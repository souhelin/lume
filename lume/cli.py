"""Interface de linha de comando da Lume."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .erros import ErroLume
from .interpretador import Interpretador
from .parser import analisar_sintaxe


def criar_parser_argumentos() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lume",
        description="Execute programas escritos na linguagem Lume.",
        epilog="Exemplo: lume exemplos/ola.lume",
    )
    parser.add_argument("arquivo", nargs="?", help="arquivo de código-fonte .lume")
    parser.add_argument("--verificar", action="store_true", help="verifica a sintaxe sem executar o programa")
    parser.add_argument("--versao", action="version", version=f"Lume {__version__}")
    return parser


def executar_arquivo(caminho: str, verificar: bool = False) -> int:
    arquivo = Path(caminho)
    try:
        fonte = arquivo.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado: {arquivo}", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print(f"Erro: o arquivo '{arquivo}' não está codificado em UTF-8.", file=sys.stderr)
        return 2
    except OSError as erro:
        print(f"Erro ao ler '{arquivo}': {erro}", file=sys.stderr)
        return 2

    try:
        programa = analisar_sintaxe(fonte)
        if verificar:
            print(f"Sintaxe válida: {arquivo}")
            return 0
        Interpretador().executar(programa)
        return 0
    except ErroLume as erro:
        _mostrar_erro(arquivo, fonte, erro)
        return 1


def _mostrar_erro(arquivo: Path, fonte: str, erro: ErroLume) -> None:
    posicao = erro.posicao
    if posicao is None:
        print(f"{arquivo}: {erro}", file=sys.stderr)
        return
    print(f"{arquivo}:{posicao.linha}:{posicao.coluna}: {erro.categoria}: {erro.mensagem}", file=sys.stderr)
    linhas = fonte.splitlines()
    if 1 <= posicao.linha <= len(linhas):
        trecho = linhas[posicao.linha - 1]
        print(f"  {trecho}", file=sys.stderr)
        print("  " + " " * max(0, posicao.coluna - 1) + "^", file=sys.stderr)


def iniciar_repl() -> int:
    print(f"Lume {__version__} — ambiente interativo")
    print("Digite uma instrução por linha. Use 'sair' para encerrar.")
    interpretador = Interpretador()
    while True:
        try:
            linha = input("lume> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if linha.strip().casefold() in {"sair", "encerrar"}:
            return 0
        if not linha.strip():
            continue
        try:
            programa = analisar_sintaxe(linha + "\n")
            # O estado das variáveis é preservado durante a sessão.
            interpretador.executar(programa)
        except ErroLume as erro:
            print(erro, file=sys.stderr)


def main(argumentos: list[str] | None = None) -> int:
    parser = criar_parser_argumentos()
    opcoes = parser.parse_args(argumentos)
    if not opcoes.arquivo:
        if opcoes.verificar:
            parser.error("informe um arquivo para usar --verificar")
        return iniciar_repl()
    return executar_arquivo(opcoes.arquivo, opcoes.verificar)


if __name__ == "__main__":
    raise SystemExit(main())
