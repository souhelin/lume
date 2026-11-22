"""CLI para importar arquivos lexicais locais no banco SQLite do LUME."""
from __future__ import annotations
import argparse
from pathlib import Path
from lume import (
    Lexicon, importar_fserb_lexico, importar_fserb_conjugacoes,
    importar_fserb_verbos, importar_fserb_icf,
    importar_openwordnet_tsv, importar_openwordnet_ttl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banco", required=True, type=Path)
    parser.add_argument("--versao-fserb", default="master")
    parser.add_argument("--versao-openwordnet", default="omw-data:main")
    parser.add_argument("--fserb-lexico", type=Path)
    parser.add_argument("--fserb-conjugacoes", type=Path)
    parser.add_argument("--fserb-verbos", type=Path)
    parser.add_argument("--fserb-icf", type=Path)
    parser.add_argument("--openwordnet-tsv", type=Path)
    parser.add_argument("--openwordnet-palavras", type=Path)
    parser.add_argument("--openwordnet-synsets", type=Path)
    parser.add_argument("--openwordnet-palavras-sentido", type=Path)
    parser.add_argument("--openwordnet-relacoes", type=Path)
    parser.add_argument("--versao-openwordnet-ttl", default="master")
    parser.add_argument(
        "--confirmar-direitos", action="store_true",
        help="confirma que você revisou licença, atribuição e direitos dos arquivos informados",
    )
    args = parser.parse_args()
    if not any((args.fserb_lexico, args.fserb_conjugacoes, args.fserb_verbos, args.fserb_icf, args.openwordnet_tsv,
                args.openwordnet_palavras, args.openwordnet_synsets,
                args.openwordnet_palavras_sentido, args.openwordnet_relacoes)):
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
        if args.fserb_verbos:
            print(importar_fserb_verbos(
                lexicon, args.fserb_verbos, versao=args.versao_fserb,
                confirmar_direitos=args.confirmar_direitos,
            ))
        if args.fserb_icf:
            print(importar_fserb_icf(
                lexicon, args.fserb_icf, versao=args.versao_fserb,
                confirmar_direitos=args.confirmar_direitos,
            ))
        if args.openwordnet_tsv:
            print(importar_openwordnet_tsv(
                lexicon, args.openwordnet_tsv, versao=args.versao_openwordnet,
                confirmar_direitos=args.confirmar_direitos,
            ))
        ttl = (args.openwordnet_palavras, args.openwordnet_synsets,
               args.openwordnet_palavras_sentido, args.openwordnet_relacoes)
        if any(ttl):
            if not all(ttl):
                parser.error("informe os quatro arquivos Turtle do OpenWordNet")
            print(importar_openwordnet_ttl(
                lexicon, *ttl, versao=args.versao_openwordnet_ttl,
                confirmar_direitos=args.confirmar_direitos,
            ))
        print("Estatísticas:", lexicon.estatisticas())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
