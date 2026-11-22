"""Aplicação de deltas lexicais autenticados com staging e rollback.

A verificação Ed25519 é opcional e falha fechada se cryptography não estiver
instalado. A atualização nunca baixa pacotes: recebe um arquivo local assinado.
"""
from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import zipfile

from .lexicon import EntradaLexical, FonteLexical, Lexicon, SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ResultadoAtualizacao:
    fonte: str
    operacoes: int
    entradas: int
    backup: str


def _verificar_assinatura(manifesto: bytes, assinatura: bytes, chave: bytes) -> None:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as erro:
        raise RuntimeError(
            "verificação Ed25519 requer o extra opcional: pip install lume-lang[updates]"
        ) from erro
    try:
        Ed25519PublicKey.from_public_bytes(chave).verify(assinatura, manifesto)
    except Exception as erro:
        raise ValueError("assinatura Ed25519 inválida") from erro


def aplicar_pacote_assinado(
    banco: str | Path, pacote: str | Path, chave_publica_ed25519: bytes,
) -> ResultadoAtualizacao:
    """Verifica e aplica um delta JSONL sem tocar no banco ativo antes da validação."""
    caminho = Path(banco).resolve()
    arquivo_pacote = Path(pacote)
    if not caminho.is_file():
        raise FileNotFoundError(f"banco lexical não encontrado: {caminho}")
    if len(chave_publica_ed25519) != 32:
        raise ValueError("chave pública Ed25519 precisa ter exatamente 32 bytes")

    with zipfile.ZipFile(arquivo_pacote, "r") as pacote_zip:
        nomes = set(pacote_zip.namelist())
        if nomes != {"manifest.json", "manifest.sig", "delta.jsonl"}:
            raise ValueError("pacote contém arquivos ausentes ou inesperados")
        manifesto_bytes = pacote_zip.read("manifest.json")
        assinatura_texto = pacote_zip.read("manifest.sig").strip()
        delta = pacote_zip.read("delta.jsonl")
    try:
        assinatura = base64.b64decode(assinatura_texto, validate=True)
        manifesto = json.loads(manifesto_bytes.decode("utf-8"))
    except Exception as erro:
        raise ValueError("manifesto ou assinatura malformados") from erro
    _verificar_assinatura(manifesto_bytes, assinatura, chave_publica_ed25519)

    if manifesto.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("versão de esquema do pacote incompatível")
    if hashlib.sha256(delta).hexdigest() != manifesto.get("delta_sha256"):
        raise ValueError("hash do delta não corresponde ao manifesto")
    fonte = manifesto.get("source")
    obrigatorios = ("id", "name", "license", "version", "url", "attribution")
    if not isinstance(fonte, dict) or any(
        not isinstance(fonte.get(chave), str) or not fonte[chave].strip()
        for chave in obrigatorios
    ):
        raise ValueError("metadados da fonte incompletos")

    caminho.parent.mkdir(parents=True, exist_ok=True)
    fd, nome_stage = tempfile.mkstemp(
        prefix=f".{caminho.name}.stage-", suffix=".sqlite3", dir=caminho.parent
    )
    os.close(fd)
    stage = Path(nome_stage)
    backup = caminho.with_suffix(caminho.suffix + ".bak")
    anterior_backup = caminho.with_suffix(caminho.suffix + ".bak.previous")
    try:
        with sqlite3.connect(caminho) as origem, sqlite3.connect(stage) as destino:
            origem.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            origem.backup(destino)

        lexicon = Lexicon(stage)
        try:
            lexicon.registrar_fonte(
                FonteLexical(
                    fonte["id"], fonte["name"], fonte["license"],
                    fonte["version"], fonte["url"], fonte["attribution"],
                ),
                verificada=True,
            )
            operacoes = 0
            for numero, linha in enumerate(delta.decode("utf-8").splitlines(), start=1):
                if not linha.strip():
                    continue
                try:
                    item = json.loads(linha)
                except json.JSONDecodeError as erro:
                    raise ValueError(f"delta inválido na linha {numero}") from erro
                if item.get("source") != fonte["id"]:
                    raise ValueError(f"fonte divergente na linha {numero}")
                acao = item.get("op")
                if acao == "upsert":
                    entrada = EntradaLexical(
                        str(item["id"]), str(item["lemma"]),
                        str(item["pos"]), item.get("definition"),
                        fonte["id"], fonte["license"], fonte["version"],
                    )
                    lexicon.adicionar_entrada(
                        entrada,
                        formas=tuple(tuple(x) for x in item.get("forms", ())),
                        contextos=tuple(item.get("contexts", ())),
                    )
                elif acao == "delete":
                    with lexicon._lock, lexicon._db:
                        lexicon._db.execute(
                            "DELETE FROM entradas WHERE id=? AND fonte_id=?",
                            (str(item["id"]), fonte["id"]),
                        )
                        lexicon._limpar_cache()
                else:
                    raise ValueError(f"operação desconhecida na linha {numero}")
                operacoes += 1
            if lexicon.integridade() != ("ok",):
                raise ValueError("integridade SQLite falhou no banco temporário")
            with lexicon._lock:
                if lexicon._db.execute("PRAGMA foreign_key_check").fetchone():
                    raise ValueError("integridade referencial falhou no banco temporário")
            entradas = lexicon.estatisticas()["entradas"]
        finally:
            lexicon.fechar()

        with sqlite3.connect(stage) as conexao:
            conexao.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conexao.execute("PRAGMA journal_mode=DELETE")

        if backup.exists():
            shutil.copy2(backup, anterior_backup)
        os.replace(caminho, backup)
        try:
            os.replace(stage, caminho)
        except Exception:
            os.replace(backup, caminho)
            raise
        return ResultadoAtualizacao(fonte["id"], operacoes, entradas, str(backup))
    except Exception:
        if stage.exists():
            stage.unlink()
        for sufixo in ("-wal", "-shm"):
            lateral = Path(str(stage) + sufixo)
            if lateral.exists():
                lateral.unlink()
        raise
