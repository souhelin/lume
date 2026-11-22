"""Interface de linha de comando da Lume."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .erros import ErroLume
from .interpretador import Interpretador
from .parser import analisar_sintaxe
from .semantica import InterpretadorSemantico, detectar_sintaxe_semantica


def criar_parser_argumentos() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lume",
        description="Execute programas escritos na linguagem Lume.",
        epilog="Exemplo: lume exemplos/ola.lume",
    )
    parser.add_argument("arquivo", nargs="?", help="arquivo de código-fonte .lume")
    parser.add_argument("--verificar", action="store_true",
                        help="valida sintaxe e semântica sem executar o programa")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--semantico", action="store_true",
                      help="força a interpretação das instruções em português")
    modo.add_argument("--tradicional", action="store_true",
                      help="usa diretamente a gramática estruturada anterior")
    parser.add_argument("--versao", action="version", version=f"Lume {__version__}")
    return parser


def executar_arquivo(
    caminho: str,
    verificar: bool = False,
    modo_semantico: bool | None = None,
) -> int:
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

    usar_semantica = (
        detectar_sintaxe_semantica(fonte)
        if modo_semantico is None else modo_semantico
    )
    try:
        if usar_semantica:
            interpretador = InterpretadorSemantico(Interpretador(diretorio_raiz=arquivo.parent))
            if verificar:
                interpretador.verificar(fonte)
                print(f"Semântica válida: {arquivo}")
                return 0
            interpretador.executar(fonte)
            return 0

        programa = analisar_sintaxe(fonte)
        if verificar:
            print(f"Sintaxe válida: {arquivo}")
            return 0
        Interpretador(diretorio_raiz=arquivo.parent).executar(programa)
        return 0
    except ErroLume as erro:
        _mostrar_erro(arquivo, fonte, erro)
        return 1


def _mostrar_erro(arquivo: Path, fonte: str, erro: ErroLume) -> None:
    posicao = erro.posicao
    if posicao is None:
        print(f"{arquivo}: {erro}", file=sys.stderr)
        return
    print(f"{arquivo}:{posicao.linha}:{posicao.coluna}: {erro.categoria}: {erro.mensagem}",
          file=sys.stderr)
    linhas = fonte.splitlines()
    if 1 <= posicao.linha <= len(linhas):
        trecho = linhas[posicao.linha - 1]
        print(f"  {trecho}", file=sys.stderr)
        print("  " + " " * max(0, posicao.coluna - 1) + "^", file=sys.stderr)


def _bloco_incompleto(erro: ErroLume) -> bool:
    return (
        erro.categoria == "Erro de sintaxe"
        and any(marca in erro.mensagem for marca in (
            "esperava 'fim'", "esperava 'então'", "esperava 'faça'",
            "esperava uma quebra de linha",
        ))
    )


def iniciar_repl(modo_semantico: bool | None = None) -> int:
    print(f"Lume {__version__} — ambiente interativo")
    print("Digite uma instrução por linha. Use 'sair' para encerrar.")
    print("Blocos podem ocupar várias linhas e terminam com 'fim'.")
    interpretador = Interpretador()
    interpretador_semantico = InterpretadorSemantico(interpretador)

    while True:
        linhas: list[str] = []
        try:
            linha = input("lume> ")
            if linha.strip().casefold() in {"sair", "encerrar"}:
                return 0
            if not linha.strip():
                continue
            linhas.append(linha)

            while True:
                fonte = "\n".join(linhas) + "\n"
                usar_semantica = (
                    detectar_sintaxe_semantica(fonte)
                    if modo_semantico is None else modo_semantico
                )
                try:
                    if usar_semantica:
                        interpretador_semantico.verificar(fonte)
                        programa = None
                    else:
                        programa = analisar_sintaxe(fonte)
                    break
                except ErroLume as erro:
                    if not _bloco_incompleto(erro):
                        raise
                    linhas.append(input("... "))

            if usar_semantica:
                interpretador_semantico.executar(fonte)
            elif programa is not None:
                interpretador.executar(programa)
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        except ErroLume as erro:
            print(erro, file=sys.stderr)


def main(argumentos: list[str] | None = None) -> int:
    parser = criar_parser_argumentos()
    opcoes = parser.parse_args(argumentos)
    modo_semantico = True if opcoes.semantico else False if opcoes.tradicional else None
    if not opcoes.arquivo:
        if opcoes.verificar:
            parser.error("informe um arquivo para usar --verificar")
        return iniciar_repl(modo_semantico)
    return executar_arquivo(opcoes.arquivo, opcoes.verificar, modo_semantico)


if __name__ == "__main__":
    raise SystemExit(main())
