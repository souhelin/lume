"""Benchmark determinístico de consultas do LUME Lexicon."""
from __future__ import annotations
import argparse
import statistics
import tempfile
import time
from pathlib import Path

from lume import Lexicon, importar_fserb_lexico


def percentil(valores: list[float], p: float) -> float:
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, int((len(ordenados) - 1) * p))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banco", type=Path, help="banco real já importado")
    parser.add_argument("--iteracoes", type=int, default=5000)
    args = parser.parse_args()
    if args.iteracoes < 1:
        parser.error("--iteracoes precisa ser maior que zero")

    temporario = tempfile.TemporaryDirectory() if args.banco is None else None
    try:
        banco_path = args.banco
        if banco_path is None:
            root = Path(temporario.name)
            palavras = root / "fixture"
            palavras.write_text(
                "".join(f"palavra_{i:05d}\\n" for i in range(20_000)),
                encoding="utf-8",
            )
            banco_path = root / "benchmark.sqlite3"
            with Lexicon(banco_path) as banco:
                importar_fserb_lexico(
                    banco, palavras, versao="benchmark-fixture",
                    confirmar_direitos=True,
                )

        with Lexicon(banco_path) as banco:
            linhas = banco._db.execute(
                "SELECT lema FROM entradas ORDER BY id LIMIT 20000"
            ).fetchall()
            termos = [linha[0] for linha in linhas]
            if not termos:
                raise SystemExit("o banco não contém entradas para benchmark")
            amostras = []
            inicio = time.perf_counter()
            for i in range(args.iteracoes):
                termo = termos[i % len(termos)]
                t0 = time.perf_counter()
                banco.buscar(termo)
                amostras.append((time.perf_counter() - t0) * 1000)
            total = time.perf_counter() - inicio
            print(f"Entradas: {banco.estatisticas()['entradas']}")
            print(f"Consultas: {args.iteracoes}")
            print(f"Throughput: {args.iteracoes / total:.1f} consultas/s")
            print(f"Latência média: {statistics.mean(amostras):.4f} ms")
            print(f"Latência p50: {percentil(amostras, 0.50):.4f} ms")
            print(f"Latência p95: {percentil(amostras, 0.95):.4f} ms")
            print(f"Latência p99: {percentil(amostras, 0.99):.4f} ms")
            print(f"Integridade: {banco.integridade()}")
    finally:
        if temporario is not None:
            temporario.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
