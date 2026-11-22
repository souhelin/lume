"""Ambientes léxicos usados para armazenar variáveis e funções."""

from __future__ import annotations

from .erros import ErroExecucao


class Ambiente:
    def __init__(self, anterior: "Ambiente | None" = None) -> None:
        self.valores: dict[str, object] = {}
        self.anterior = anterior

    def definir(self, nome: str, valor: object) -> None:
        self.valores[nome] = valor

    def obter(self, nome: str) -> object:
        if nome in self.valores:
            return self.valores[nome]
        if self.anterior is not None:
            return self.anterior.obter(nome)
        raise ErroExecucao(f"nome não definido: '{nome}'")

    def atribuir(self, nome: str, valor: object) -> None:
        if nome in self.valores:
            self.valores[nome] = valor
            return
        if self.anterior is not None:
            self.anterior.atribuir(nome, valor)
            return
        raise ErroExecucao(f"não é possível alterar '{nome}': nome não definido")
