"""Teste de integração com uma exportação real OpenWordNet-PT/OMW."""
from __future__ import annotations
import argparse
from pathlib import Path
from lume import Lexicon, importar_openwordnet_tsv


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("arquivo", type=Path)
    p.add_argument("--min-entradas", type=int, default=10_000)
    p.add_argument("--min-sentidos", type=int, default=1_000)
    a = p.parse_args()
    with Lexicon(":memory:") as lexicon:
        resultado = importar_openwordnet_tsv(
            lexicon, a.arquivo, versao="omw-data:main",
            confirmar_direitos=True,
        )
        stats = lexicon.estatisticas()
        if resultado.registros_importados < a.min_entradas:
            raise SystemExit(
                f"base real menor que o esperado: {resultado.registros_importados}"
            )
        if resultado.sentidos_importados < a.min_sentidos:
            raise SystemExit(
                f"número de sentidos menor que o esperado: {resultado.sentidos_importados}"
            )
        if lexicon.integridade() != ("ok",):
            raise SystemExit("falha de integridade SQLite")
        if not lexicon.buscar("pessoa"):
            raise SystemExit("consulta real 'pessoa' não retornou resultado")
        print("Base real validada:", resultado)
        print("Estatísticas:", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
