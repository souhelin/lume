"""Nós da árvore de sintaxe abstrata da Lume."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Programa:
    declaracoes: list[object]


@dataclass(slots=True)
class Literal:
    valor: object


@dataclass(slots=True)
class Variavel:
    nome: str


@dataclass(slots=True)
class ListaLiteral:
    elementos: list[object]


@dataclass(slots=True)
class Chamada:
    funcao: object
    argumentos: list[object]


@dataclass(slots=True)
class Unaria:
    operador: str
    operando: object


@dataclass(slots=True)
class Binaria:
    esquerda: object
    operador: str
    direita: object


@dataclass(slots=True)
class Mostrar:
    valores: list[object]


@dataclass(slots=True)
class Definir:
    nome: str
    valor: object


@dataclass(slots=True)
class ExpressaoInstrucao:
    expressao: object


@dataclass(slots=True)
class Condicional:
    condicao: object
    caminho_verdadeiro: list[object]
    caminho_falso: list[object]


@dataclass(slots=True)
class Enquanto:
    condicao: object
    corpo: list[object]


@dataclass(slots=True)
class ParaCada:
    nome: str
    iteravel: object
    corpo: list[object]


@dataclass(slots=True)
class FuncaoDeclaracao:
    nome: str
    parametros: list[str]
    corpo: list[object]


@dataclass(slots=True)
class Retornar:
    valor: object | None


@dataclass(slots=True)
class Interromper:
    pass


@dataclass(slots=True)
class Continuar:
    pass


@dataclass(slots=True)
class Indice:
    colecao: object
    indice: object


@dataclass(slots=True)
class Atribuir:
    nome: str
    valor: object


@dataclass(slots=True)
class AtribuirIndice:
    colecao: object
    indice: object
    valor: object


@dataclass(slots=True)
class Tentar:
    corpo: list[object]
    nome_erro: str | None
    captura: list[object]
    finalmente: list[object]


@dataclass(slots=True)
class Lancar:
    valor: object
