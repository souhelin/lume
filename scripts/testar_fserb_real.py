"""Valida importação completa do snapshot público fserb/pt-br."""
from __future__ import annotations
import argparse
from pathlib import Path
from lume import (
    Lexicon, importar_fserb_lexico, importar_fserb_conjugacoes,
    importar_fserb_verbos, importar_fserb_icf,
)

VERSAO = "93ba2a6f3b2f85262fba72df09d448c6bb2fa50a"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("lexico", type=Path)
    p.add_argument("conjugacoes", type=Path)
    p.add_argument("verbos", type=Path)
    p.add_argument("icf", type=Path)
    a = p.parse_args()
    with Lexicon(":memory:") as lexicon:
        resultados = [
            importar_fserb_lexico(lexicon, a.lexico, versao=VERSAO, confirmar_direitos=True),
            importar_fserb_conjugacoes(lexicon, a.conjugacoes, versao=VERSAO, confirmar_direitos=True),
            importar_fserb_verbos(lexicon, a.verbos, versao=VERSAO, confirmar_direitos=True),
            importar_fserb_icf(lexicon, a.icf, versao=VERSAO, confirmar_direitos=True),
        ]
        limites = (100_000, 150_000, 3_000, 300_000)
        for resultado, minimo in zip(resultados, limites):
            if resultado.registros_importados < minimo:
                raise SystemExit(
                    f"importação incompleta de {resultado.fonte}: "
                    f"{resultado.registros_importados} < {minimo}"
                )
        stats = lexicon.estatisticas()
        if stats["frequencias"] < 300_000 or lexicon.frequencia("a") == ():
            raise SystemExit("pontuações ICF não foram carregadas corretamente")
        if not lexicon.buscar("cantar"):
            raise SystemExit("lema de verbo não encontrado")
        if lexicon.integridade() != ("ok",):
            raise SystemExit("falha de integridade SQLite")
        print("Importação fserb validada:", resultados)
        print("Estatísticas:", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
