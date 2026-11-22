"""CLI para importar arquivos lexicais locais no banco SQLite do LUME."""
from __future__ import annotations
import argparse
from pathlib import Path
from lume import Lexicon, importar_fserb_lexico, importar_fserb_conjugacoes, importar_openwordnet_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banco", required=True, type=Path)
    parser.add_argument("--versao-fserb", default="master")
    parser.add_argument("--versao-openwordnet", default="omw-data:main")
    parser.add_argument("--fserb-lexico", type=Path)
    parser.add_argument("--fserb-conjugacoes", type=Path)
    parser.add_argument("--openwordnet-tsv", type=Path)
    parser.add_argument(
        "--confirmar-direitos", action="store_true",
        help="confirma que você revisou licença, atribuição e direitos dos arquivos informados",
    )
    args = parser.parse_args()
    if not any((args.fserb_lexico, args.fserb_conjugacoes, args.openwordnet_tsv)):
        parser.error("informe ao menos uma fonte local")
    with Lexicon(args.banco) as lexicon:
        if args.fserb_lexico:
            print(importar_fserb_lexico(
                lexicon, args.fserb_lexico, versao=args.versao_fserb,
                confirmar_direitos=args.confirmar_direitos,
            ))
        if args.fserb_conjugacoes:
            print(importar_fserb_conjugacoes(
                lexicon, args.fserb_conjugacoes, versao=args.versao_fserb,
                confirmar_direitos=args.confirmar_direitos,
            ))
        if args.openwordnet_tsv:
            print(importar_openwordnet_tsv(
                lexicon, args.openwordnet_tsv, versao=args.versao_openwordnet,
                confirmar_direitos=args.confirmar_direitos,
            ))
        print("Estatísticas:", lexicon.estatisticas())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
