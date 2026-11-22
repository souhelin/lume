"""Definição dos tokens produzidos pelo analisador léxico."""

from __future__ import annotations

from dataclasses import dataclass

from .erros import Posicao


@dataclass(frozen=True, slots=True)
class Token:
    tipo: str
    valor: object
    posicao: Posicao

    def __repr__(self) -> str:
        return f"Token({self.tipo}, {self.valor!r}, {self.posicao.linha}:{self.posicao.coluna})"
