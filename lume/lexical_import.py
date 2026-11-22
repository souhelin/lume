"""Importadores explícitos e offline para fontes lexicais do LUME.

Os arquivos são fornecidos localmente pelo usuário. Este módulo não baixa dados.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Iterable, Iterator

from .lexicon import FonteLexical, Lexicon, normalizar_forma


@dataclass(frozen=True, slots=True)
class ResultadoImportacao:
    fonte: str
    registros_lidos: int
    registros_importados: int
    sentidos_importados: int = 0
    ignorados: int = 0


def _linhas(caminho: str | Path) -> Iterator[str]:
    with Path(caminho).open("r", encoding="utf-8-sig", newline="") as arquivo:
        for linha in arquivo:
            valor = linha.strip()
            if valor and not valor.startswith("#"):
                yield valor


def _id(fonte: str, classe: str, lema: str) -> str:
    chave = f"{fonte}\0{classe}\0{normalizar_forma(lema)}"
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()[:32]


def _registrar_fonte(
    lexicon: Lexicon, *, identificador: str, nome: str, licenca: str,
    versao: str, url: str, atribuicao: str, confirmar_direitos: bool,
) -> None:
    if not confirmar_direitos:
        raise PermissionError(
            "Importação bloqueada: revise a licença/procedência e passe "
            "confirmar_direitos=True conscientemente."
        )
    lexicon.registrar_fonte(
        FonteLexical(identificador, nome, licenca, versao, url, atribuicao),
        verificada=True,
    )


def _gravar_entradas(
    lexicon: Lexicon, fonte: str, entradas: Iterable[tuple[str, str, str, str | None]],
) -> int:
    """Grava (id, lema, classe) em lote, mantendo o banco em uma transação."""
    lote = list(entradas)
    if not lote:
        return 0
    with lexicon._lock, lexicon._db:
        registro = lexicon._db.execute(
            "SELECT verificada FROM fontes WHERE id=?", (fonte,)
        ).fetchone()
        if registro is None or not registro["verificada"]:
            raise PermissionError("fonte não verificada para importação")
        fonte_meta = lexicon._db.execute(
            "SELECT licenca, versao FROM fontes WHERE id=?", (fonte,)
        ).fetchone()
        lexicon._db.executemany(
            """
            INSERT OR IGNORE INTO entradas
                (id, lema, lema_normalizado, classe, definicao, fonte_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                (identificador, lema, normalizar_forma(lema), classe, definicao, fonte)
                for identificador, lema, classe, definicao in lote
            ),
        )
        lexicon._db.executemany(
            """
            INSERT OR IGNORE INTO formas
                (forma_normalizada, forma_original, entrada_id, tipo)
            VALUES (?, ?, ?, 'lema')
            """,
            (
                (normalizar_forma(lema), lema, identificador)
                for identificador, lema, _classe, _definicao in lote
            ),
        )
        lexicon._limpar_cache()
    return len(lote)


def importar_fserb_lexico(
    lexicon: Lexicon, arquivo_lexico: str | Path, *,
    versao: str, confirmar_direitos: bool = False,
    limite: int | None = None,
) -> ResultadoImportacao:
    """Importa o arquivo de uma palavra por linha, sem inventar classe/definição.

    O agregado upstream informa múltiplas fontes dicionarísticas. O aceite
    explícito não substitui uma auditoria jurídica dos dados de origem.
    """
    fonte = "fserb-pt-br-lexico"
    _registrar_fonte(
        lexicon, identificador=fonte, nome="fserb/pt-br — lexico",
        licenca="MIT (licença declarada no repositório; proveniência agregada pendente)",
        versao=versao, url="https://github.com/fserb/pt-br",
        atribuicao="Copyright 2021 Fernando Serboncini; preservar LICENSE upstream.",
        confirmar_direitos=confirmar_direitos,
    )
    vistos: set[str] = set()
    lote: list[tuple[str, str, str | None]] = []
    lidos = importados = ignorados = 0
    for palavra in _linhas(arquivo_lexico):
        lidos += 1
        termo = normalizar_forma(palavra)
        if termo in vistos:
            ignorados += 1
            continue
        vistos.add(termo)
        lote.append((_id(fonte, "não_classificada", palavra), palavra,
                     "não_classificada", None))
        if len(lote) >= 2000:
            importados += _gravar_entradas(lexicon, fonte, lote)
            lote.clear()
        if limite is not None and lidos >= limite:
            break
    importados += _gravar_entradas(lexicon, fonte, lote)
    return ResultadoImportacao(fonte, lidos, importados, ignorados=ignorados)


def importar_fserb_conjugacoes(
    lexicon: Lexicon, arquivo_conjugacoes: str | Path, *,
    versao: str, confirmar_direitos: bool = False,
    limite: int | None = None,
) -> ResultadoImportacao:
    """Importa formas verbais como formas não analisadas, sem atribuir lema falso.

    O arquivo é uma lista simples; não contém vínculo forma→infinitivo.
    """
    fonte = "fserb-pt-br-conjugacoes"
    _registrar_fonte(
        lexicon, identificador=fonte, nome="fserb/pt-br — conjugações",
        licenca="MIT (licença declarada no repositório; proveniência agregada pendente)",
        versao=versao, url="https://github.com/fserb/pt-br",
        atribuicao="Copyright 2021 Fernando Serboncini; preservar LICENSE upstream.",
        confirmar_direitos=confirmar_direitos,
    )
    vistos: set[str] = set()
    lote: list[tuple[str, str, str | None]] = []
    lidos = importados = ignorados = 0
    for forma in _linhas(arquivo_conjugacoes):
        lidos += 1
        termo = normalizar_forma(forma)
        if termo in vistos:
            ignorados += 1
            continue
        vistos.add(termo)
        lote.append((_id(fonte, "forma_verbal_sem_lema", forma), forma,
                     "forma_verbal_sem_lema", None))
        if len(lote) >= 2000:
            importados += _gravar_entradas(lexicon, fonte, lote)
            lote.clear()
        if limite is not None and lidos >= limite:
            break
    importados += _gravar_entradas(lexicon, fonte, lote)
    return ResultadoImportacao(fonte, lidos, importados, ignorados=ignorados)


def importar_openwordnet_tsv(
    lexicon: Lexicon, arquivo_tsv: str | Path, *,
    versao: str, confirmar_direitos: bool = False,
    limite: int | None = None,
) -> ResultadoImportacao:
    """Importa exportação OMW TSV: synset_id<TAB>tipo<TAB>lema.

    Cada synset vira um sentido; termos iguais podem pertencer a vários
    sentidos sem serem confundidos. O arquivo não contém glossas neste formato.
    """
    fonte = "openwordnet-pt-omw"
    _registrar_fonte(
        lexicon, identificador=fonte, nome="OpenWordNet-PT (exportação OMW)",
        licenca="CC BY-SA 3.0 (licença do export OMW por)",
        versao=versao, url="https://github.com/omwn/omw-data/tree/main/wns/por",
        atribuicao=(
            "OpenWordNet-PT; atribuição aos autores do recurso. "
            "Distribuir os dados derivados sob CC BY-SA 3.0 e preservar avisos upstream."
        ),
        confirmar_direitos=confirmar_direitos,
    )
    pos_map = {
        "n": "substantivo", "v": "verbo", "a": "adjetivo",
        "s": "adjetivo", "r": "adverbio",
    }
    membros_por_sentido: dict[str, list[str]] = {}
    entradas: dict[str, tuple[str, str, str | None]] = {}
    lidos = ignorados = 0
    with Path(arquivo_tsv).open("r", encoding="utf-8-sig", newline="") as arquivo:
        for linha in arquivo:
            valor = linha.rstrip("\r\n")
            if not valor or valor.startswith("#"):
                continue
            partes = valor.split("\t")
            if len(partes) != 3:
                ignorados += 1
                continue
            synset, tipo, lema = partes
            if tipo != "lemma" or not synset or not lema.strip():
                ignorados += 1
                continue
            lidos += 1
            codigo_pos = synset.rsplit("-", 1)[-1][:1]
            classe = pos_map.get(codigo_pos)
            if classe is None:
                ignorados += 1
                continue
            identificador = _id(fonte, classe, lema)
            entradas[identificador] = (identificador, lema, classe, None)
            membros_por_sentido.setdefault(synset, [])
            if identificador not in membros_por_sentido[synset]:
                membros_por_sentido[synset].append(identificador)
            if limite is not None and lidos >= limite:
                break

    _gravar_entradas(lexicon, fonte, entradas.values())
    with lexicon._lock, lexicon._db:
        lexicon._db.executemany(
            """
            INSERT INTO sentidos(id, fonte_id, classe, definicao)
            VALUES (?, ?, ?, NULL)
            ON CONFLICT(id) DO UPDATE SET fonte_id=excluded.fonte_id, classe=excluded.classe
            """,
            (
                (synset, fonte, pos_map.get(synset.rsplit("-", 1)[-1][:1], "desconhecida"))
                for synset in membros_por_sentido
            ),
        )
        lexicon._db.executemany(
            """
            INSERT OR IGNORE INTO sentido_entradas(sentido_id, entrada_id, ordem)
            VALUES (?, ?, ?)
            """,
            (
                (synset, entrada_id, ordem)
                for synset, ids in membros_por_sentido.items()
                for ordem, entrada_id in enumerate(ids)
            ),
        )
        lexicon._limpar_cache()
    return ResultadoImportacao(
        fonte, lidos, len(entradas), sentidos_importados=len(membros_por_sentido),
        ignorados=ignorados,
    )
