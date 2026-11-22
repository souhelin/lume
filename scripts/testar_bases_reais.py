"""Teste de integração com os quatro arquivos Turtle oficiais OpenWordNet-PT."""
from __future__ import annotations
import argparse
from pathlib import Path
from lume import Lexicon, importar_openwordnet_ttl


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("palavras", type=Path)
    p.add_argument("synsets", type=Path)
    p.add_argument("palavras_sentido", type=Path)
    p.add_argument("relacoes", type=Path)
    p.add_argument("--min-entradas", type=int, default=5_000)
    p.add_argument("--min-sentidos", type=int, default=5_000)
    a = p.parse_args()
    with Lexicon(":memory:") as lexicon:
        resultado = importar_openwordnet_ttl(
            lexicon, a.palavras, a.synsets, a.palavras_sentido, a.relacoes,
            versao="own-pt:master", confirmar_direitos=True,
        )
        stats = lexicon.estatisticas()
        if resultado.registros_importados < a.min_entradas:
            raise SystemExit(f"base lexical pequena: {resultado.registros_importados}")
        if resultado.sentidos_importados < a.min_sentidos:
            raise SystemExit(f"base de sentidos pequena: {resultado.sentidos_importados}")
        if stats["relacoes"] == 0:
            raise SystemExit("nenhuma relação semântica foi importada")
        if lexicon.integridade() != ("ok",):
            raise SystemExit("falha de integridade SQLite")
        respirar = lexicon.buscar("respirar")
        if not respirar:
            raise SystemExit("consulta real 'respirar' não retornou resultado")
        glossas = [
            sentido for correspondencia in respirar
            for sentido in lexicon.sentidos(correspondencia.entrada.identificador)
            if sentido.get("definicao")
        ]
        if not glossas:
            raise SystemExit("nenhuma glossa foi associada ao lema 'respirar'")
        print("Base real OpenWordNet-PT validada:", resultado)
        print("Estatísticas:", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
