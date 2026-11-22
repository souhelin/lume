"""Analisador léxico da Lume. Não depende de bibliotecas externas."""

from __future__ import annotations

import unicodedata

from .erros import ErroLexico, Posicao
from .tokens import Token


class AnalisadorLexico:
    SIMPLES = {
        "(": "ABRE_PARENTESE",
        ")": "FECHA_PARENTESE",
        "[": "ABRE_COLCHETE",
        "]": "FECHA_COLCHETE",
        ",": "VIRGULA",
        "+": "MAIS",
        "-": "MENOS",
        "*": "VEZES",
        "/": "DIVIDIR",
        "%": "RESTO",
        "=": "IGUAL",
        "<": "MENOR",
        ">": "MAIOR",
    }

    DUPLOS = {
        "==": "IGUAL_IGUAL",
        "!=": "DIFERENTE",
        ">=": "MAIOR_IGUAL",
        "<=": "MENOR_IGUAL",
        "**": "POTENCIA",
        "//": "DIVISAO_INTEIRA",
    }

    def __init__(self, fonte: str) -> None:
        self.fonte = fonte
        self.indice = 0
        self.linha = 1
        self.coluna = 1
        self.tokens: list[Token] = []

    def analisar(self) -> list[Token]:
        while not self._fim():
            atual = self._atual()
            if atual in " \t\r":
                self._avancar()
            elif atual == "\n":
                posicao = self._posicao()
                self._avancar()
                self.tokens.append(Token("NOVA_LINHA", "\n", posicao))
            elif atual == "#":
                self._comentario()
            elif atual in "\"'":
                self._texto()
            elif atual.isdecimal():
                self._numero()
            elif atual.isalpha() or atual == "_":
                self._identificador()
            else:
                self._operador_ou_erro()

        self.tokens.append(Token("FIM", None, self._posicao()))
        return self.tokens

    def _fim(self) -> bool:
        return self.indice >= len(self.fonte)

    def _atual(self) -> str:
        return self.fonte[self.indice]

    def _espiar(self, distancia: int = 1) -> str:
        alvo = self.indice + distancia
        return self.fonte[alvo] if alvo < len(self.fonte) else "\0"

    def _posicao(self) -> Posicao:
        return Posicao(self.linha, self.coluna)

    def _avancar(self) -> str:
        caractere = self.fonte[self.indice]
        self.indice += 1
        if caractere == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return caractere

    def _comentario(self) -> None:
        while not self._fim() and self._atual() != "\n":
            self._avancar()

    def _texto(self) -> None:
        posicao = self._posicao()
        delimitador = self._avancar()
        partes: list[str] = []
        escapes = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}

        while not self._fim() and self._atual() != delimitador:
            caractere = self._avancar()
            if caractere == "\n":
                raise ErroLexico("texto não pode atravessar linhas; use \\n para uma quebra de linha", posicao)
            if caractere == "\\":
                if self._fim():
                    break
                escapado = self._avancar()
                if escapado not in escapes:
                    raise ErroLexico(f"sequência de escape desconhecida: \\{escapado}", self._posicao())
                partes.append(escapes[escapado])
            else:
                partes.append(caractere)

        if self._fim():
            raise ErroLexico("texto sem aspas de fechamento", posicao)
        self._avancar()
        self.tokens.append(Token("TEXTO", "".join(partes), posicao))

    def _numero(self) -> None:
        posicao = self._posicao()
        inicio = self.indice
        while not self._fim() and self._atual().isdecimal():
            self._avancar()
        decimal = False
        if not self._fim() and self._atual() == "." and self._espiar().isdecimal():
            decimal = True
            self._avancar()
            while not self._fim() and self._atual().isdecimal():
                self._avancar()
        trecho = self.fonte[inicio:self.indice]
        if len(trecho) > 100:
            raise ErroLexico("literal numérico ultrapassa o limite de 100 caracteres", posicao)
        try:
            valor: int | float = float(trecho) if decimal else int(trecho)
        except ValueError as erro:
            raise ErroLexico("literal numérico inválido", posicao) from erro
        self.tokens.append(Token("NUMERO", valor, posicao))

    def _identificador(self) -> None:
        posicao = self._posicao()
        inicio = self.indice
        while not self._fim() and (
            self._atual().isalnum()
            or self._atual() == "_"
            or unicodedata.category(self._atual()) in {"Mn", "Mc"}
        ):
            self._avancar()
        valor = unicodedata.normalize("NFC", self.fonte[inicio:self.indice]).casefold()
        self.tokens.append(Token("IDENTIFICADOR", valor, posicao))

    def _operador_ou_erro(self) -> None:
        posicao = self._posicao()
        par = self._atual() + self._espiar()
        if par in self.DUPLOS:
            self._avancar()
            self._avancar()
            self.tokens.append(Token(self.DUPLOS[par], par, posicao))
            return
        caractere = self._atual()
        if caractere in self.SIMPLES:
            self._avancar()
            self.tokens.append(Token(self.SIMPLES[caractere], caractere, posicao))
            return
        raise ErroLexico(f"caractere não reconhecido: {caractere!r}", posicao)


def analisar_lexico(fonte: str) -> list[Token]:
    return AnalisadorLexico(fonte).analisar()
