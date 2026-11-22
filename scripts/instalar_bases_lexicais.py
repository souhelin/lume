"""Baixa snapshots fixados e monta uma base SQLite lexical offline do LUME.

A rede é usada somente quando este script é executado explicitamente.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import tempfile
from urllib.parse import quote
from urllib.request import Request, urlopen

from lume import (
    Lexicon, importar_fserb_lexico, importar_fserb_conjugacoes,
    importar_fserb_verbos, importar_fserb_icf, importar_openwordnet_ttl,
)

FSERB_COMMIT = "93ba2a6f3b2f85262fba72df09d448c6bb2fa50a"
OWN_COMMIT = "264016d5899e6969f6f7cb4f1d75fa06037c1fd7"

ARQUIVOS = {
    "fserb": {
        "lexico": ("https://raw.githubusercontent.com/fserb/pt-br/" + FSERB_COMMIT + "/lexico",
                   "ff0500fea0a7daa840507acec49ab1a78e40183b"),
        "conjugacoes": ("https://raw.githubusercontent.com/fserb/pt-br/" + FSERB_COMMIT + "/" + quote("conjugações"),
                        "eb52f972b8c7c9135c8879f772526b25b4994579"),
        "verbos": ("https://raw.githubusercontent.com/fserb/pt-br/" + FSERB_COMMIT + "/listas/verbos",
                   "0af1ddde21fd6db329ab62b1eeec8dad31c49f17"),
        "icf": ("https://raw.githubusercontent.com/fserb/pt-br/" + FSERB_COMMIT + "/icf",
                "044c008b07b84d9d89cd8d508148557fdd23d352"),
    },
    "openwordnet": {
        "palavras": ("https://raw.githubusercontent.com/own-pt/openWordnet-PT/" + OWN_COMMIT + "/data/own-pt-words.ttl",
                     "9ff02b4ab8f3d99ca33be2eee16af3e5dcb5ad37"),
        "synsets": ("https://raw.githubusercontent.com/own-pt/openWordnet-PT/" + OWN_COMMIT + "/data/own-pt-synsets.ttl",
                    "331b7bb345bb6ae7d23cac47e7a23eba1f052d04"),
        "palavras_sentido": ("https://raw.githubusercontent.com/own-pt/openWordnet-PT/" + OWN_COMMIT + "/data/own-pt-wordsenses.ttl",
                             "2c6113248c2853f201a673e6f3d7577175739ae6"),
        "relacoes": ("https://raw.githubusercontent.com/own-pt/openWordnet-PT/" + OWN_COMMIT + "/data/own-pt-relations.ttl",
                     "8f69dea317898666cd11db9059254a56375b0ff3"),
        "morfosemantico": ("https://raw.githubusercontent.com/own-pt/openWordnet-PT/" + OWN_COMMIT + "/data/own-pt-morphosemantic-links.ttl",
                           "df66d5ec53d48142293f8a10337a23e265c92006"),
        "same_as": ("https://raw.githubusercontent.com/own-pt/openWordnet-PT/" + OWN_COMMIT + "/data/own-pt-same-as.ttl",
                    "b895b3b4351c116579f708c4e8349a28a8999982"),
    },
}


def baixar_verificado(url: str, sha_esperado: str, destino: Path) -> None:
    requisicao = Request(url, headers={"User-Agent": "LUME-Lexicon-Installer/1.0"})
    with urlopen(requisicao, timeout=90) as resposta:
        conteudo = resposta.read()
    git_blob = hashlib.sha1(
        f"blob {len(conteudo)}\0".encode("ascii") + conteudo
    ).hexdigest()
    if git_blob != sha_esperado:
        raise ValueError(
            f"checksum Git incorreto para {destino.name}: {git_blob}"
        )
    destino.write_bytes(conteudo)
    print(f"Verificado: {destino.name} ({len(conteudo):,} bytes)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino", type=Path, default=Path("dados/lexicon.sqlite3"),
        help="caminho do banco SQLite que será criado",
    )
    parser.add_argument(
        "--confirmar-direitos", action="store_true",
        help="confirma que você revisou as licenças e a procedência dos dois conjuntos",
    )
    args = parser.parse_args()
    if not args.confirmar_direitos:
        parser.error(
            "revise DATA_SOURCES.md e LICENSES.md; depois execute com --confirmar-direitos"
        )
    if args.destino.exists():
        parser.error(f"o destino já existe; escolha outro caminho: {args.destino}")

    args.destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="lume-lexicon-") as pasta:
            raiz = Path(pasta)
            arquivos: dict[str, Path] = {}
            for grupo, itens in ARQUIVOS.items():
                for nome, (url, sha) in itens.items():
                    caminho = raiz / f"{grupo}-{nome}.ttl"
                    baixar_verificado(url, sha, caminho)
                    arquivos[f"{grupo}_{nome}"] = caminho

            with Lexicon(args.destino) as lexicon:
                resultados = [
                    importar_fserb_lexico(
                        lexicon, arquivos["fserb_lexico"], versao=FSERB_COMMIT,
                        confirmar_direitos=True,
                    ),
                    importar_fserb_conjugacoes(
                        lexicon, arquivos["fserb_conjugacoes"], versao=FSERB_COMMIT,
                        confirmar_direitos=True,
                    ),
                    importar_fserb_verbos(
                        lexicon, arquivos["fserb_verbos"], versao=FSERB_COMMIT,
                        confirmar_direitos=True,
                    ),
                    importar_fserb_icf(
                        lexicon, arquivos["fserb_icf"], versao=FSERB_COMMIT,
                        confirmar_direitos=True,
                    ),
                    importar_openwordnet_ttl(
                        lexicon,
                        arquivos["openwordnet_palavras"],
                        arquivos["openwordnet_synsets"],
                        arquivos["openwordnet_palavras_sentido"],
                        arquivos["openwordnet_relacoes"],
                        versao=OWN_COMMIT,
                        arquivo_morfosemantico=arquivos["openwordnet_morfosemantico"],
                        arquivo_same_as=arquivos["openwordnet_same_as"],
                        confirmar_direitos=True,
                    ),
                ]
                if lexicon.integridade() != ("ok",):
                    raise RuntimeError("a integridade do banco lexical falhou")
                estatisticas = lexicon.estatisticas()

        aviso = args.destino.with_suffix(args.destino.suffix + ".licenses.txt")
        aviso.write_text(
            "LUME Lexicon — avisos dos dados incorporados\n\n"
            f"fserb/pt-br commit: {FSERB_COMMIT}\n"
            "Licença declarada: MIT; o agregado informa múltiplas fontes dicionarísticas.\n"
            "A procedência de terceiros deve ser revisada antes de redistribuir o agregado.\n"
            "https://github.com/fserb/pt-br\n\n"
            f"OpenWordNet-PT commit: {OWN_COMMIT}\n"
            "Licença declarada: CC BY 4.0; manter atribuição e indicar modificações.\n"
            "https://github.com/own-pt/openWordnet-PT\n\n"
            "A licença do código LUME não substitui as licenças dos dados.\n"
            "Consulte LICENSES.md e DATA_SOURCES.md no repositório.\n",
            encoding="utf-8",
        )
        print("Banco lexical criado:", args.destino)
        print("Avisos de licença:", aviso)
        print("Resultados:", resultados)
        print("Estatísticas:", estatisticas)
        return 0
    except Exception:
        for caminho in (
            args.destino, Path(str(args.destino) + "-wal"),
            Path(str(args.destino) + "-shm"),
        ):
            if caminho.exists():
                caminho.unlink()
        raise


if __name__ == "__main__":
    raise SystemExit(main())
