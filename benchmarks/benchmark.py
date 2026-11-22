"""Microbenchmarks reproduzíveis da Lume; não são uma barreira de CI."""

from __future__ import annotations

import platform
import statistics
import time
from collections.abc import Callable

from lume import CompiladorSemantico, Interpretador, InterpretadorSemantico, analisar_sintaxe
from lume.lexer import analisar_lexico


FONTE_TRADICIONAL = """definir total como 0
para cada numero em intervalo(1, 100) faça
    total = total + numero
fim
mostrar total
"""

FONTE_SEMANTICA = """crie uma variável chamada total com valor 0
repita 100 vezes
    atribua total + 1 a ela
fim da repetição
mostre total
"""


def medir(funcao: Callable[[], object], repeticoes: int = 100) -> float:
    for _ in range(5):
        funcao()
    amostras: list[float] = []
    for _ in range(5):
        inicio = time.perf_counter()
        for _ in range(repeticoes):
            funcao()
        amostras.append((time.perf_counter() - inicio) / repeticoes)
    return statistics.median(amostras)


def main() -> None:
    arvore = analisar_sintaxe(FONTE_TRADICIONAL)
    semantico = CompiladorSemantico()
    print(f"Lume benchmark — Python {platform.python_version()} — {platform.platform()}")
    print("Mediana de 5 amostras; cada amostra executa 100 repetições.")
    medidas = (
        ("Análise léxica", lambda: analisar_lexico(FONTE_TRADICIONAL)),
        ("Análise sintática", lambda: analisar_sintaxe(FONTE_TRADICIONAL)),
        ("Compilação semântica", lambda: semantico.compilar(FONTE_SEMANTICA)),
        ("Execução tradicional", lambda: Interpretador(saida=lambda _texto: None).executar(arvore)),
        ("Execução semântica", lambda: InterpretadorSemantico(
            Interpretador(saida=lambda _texto: None)
        ).executar(FONTE_SEMANTICA)),
    )
    for nome, funcao in medidas:
        segundos = medir(funcao)
        print(f"{nome:24} {segundos * 1_000_000:10.1f} µs/op")


if __name__ == "__main__":
    main()
