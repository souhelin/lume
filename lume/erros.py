"""Erros da linguagem Lume."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Posicao:
    linha: int
    coluna: int


class ErroLume(Exception):
    """Erro conhecido da linguagem, com posição opcional no código-fonte."""

    categoria = "Erro"

    def __init__(self, mensagem: str, posicao: Posicao | None = None) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.posicao = posicao

    def __str__(self) -> str:
        if self.posicao:
            return f"{self.categoria} na linha {self.posicao.linha}, coluna {self.posicao.coluna}: {self.mensagem}"
        return f"{self.categoria}: {self.mensagem}"


class ErroLexico(ErroLume):
    categoria = "Erro léxico"


class ErroSintatico(ErroLume):
    categoria = "Erro de sintaxe"


class ErroExecucao(ErroLume):
    categoria = "Erro de execução"


class SinalRetorno(Exception):
    """Controle interno usado para encerrar a execução de uma função."""

    def __init__(self, valor: object) -> None:
        self.valor = valor


class SinalInterromper(Exception):
    """Controle interno usado pelo comando 'interromper'."""


class SinalContinuar(Exception):
    """Controle interno usado pelo comando 'continuar'."""
