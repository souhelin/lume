"""Representação intermediária semântica da Lume.

A IR não contém palavras-chave da sintaxe de origem. Ela representa operações
e expressões por identificadores estáveis, podendo receber outras front-ends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .erros import ErroSemantico, Posicao
from .nos import (
    Atribuir, AtribuirIndice, Tentar, Lancar, Importar, Binaria, Chamada, Condicional, Continuar, Definir,
    ExpressaoInstrucao, FuncaoDeclaracao, Indice, Interromper, Enquanto,
    ListaLiteral, Literal, Mostrar, ParaCada, Programa, Retornar, Unaria,
    Variavel,
)


@dataclass(frozen=True, slots=True)
class ExpressaoIR:
    operacao: str
    argumentos: tuple[Any, ...] = ()


@dataclass(frozen=True, slots=True)
class InstrucaoIR:
    operacao: str
    argumentos: tuple[Any, ...] = ()
    posicao: Posicao | None = None


@dataclass(frozen=True, slots=True)
class ProgramaIR:
    instrucoes: tuple[InstrucaoIR, ...]

    def para_dicionario(self) -> dict[str, Any]:
        return {"tipo": "programa", "instrucoes": [_serializar(i) for i in self.instrucoes]}


def _serializar(valor: Any) -> Any:
    if isinstance(valor, (ExpressaoIR, InstrucaoIR)):
        return {
            "operacao": valor.operacao,
            "argumentos": [_serializar(item) for item in valor.argumentos],
            **({"posicao": {"linha": valor.posicao.linha, "coluna": valor.posicao.coluna}} if isinstance(valor, InstrucaoIR) and valor.posicao else {}),
        }
    if isinstance(valor, ProgramaIR):
        return valor.para_dicionario()
    if isinstance(valor, tuple):
        return [_serializar(item) for item in valor]
    if isinstance(valor, list):
        return [_serializar(item) for item in valor]
    if isinstance(valor, (str, int, float, bool)) or valor is None:
        return valor
    return repr(valor)


def expressao_para_ir(no: object) -> ExpressaoIR:
    if isinstance(no, Literal):
        return ExpressaoIR("literal", (no.valor,))
    if isinstance(no, Variavel):
        return ExpressaoIR("referencia", (no.nome,))
    if isinstance(no, ListaLiteral):
        return ExpressaoIR("lista", (tuple(expressao_para_ir(item) for item in no.elementos),))
    if isinstance(no, Chamada):
        return ExpressaoIR("chamada", (
            expressao_para_ir(no.funcao),
            tuple(expressao_para_ir(item) for item in no.argumentos),
        ))
    if isinstance(no, Unaria):
        return ExpressaoIR("unaria", (no.operador, expressao_para_ir(no.operando)))
    if isinstance(no, Binaria):
        return ExpressaoIR("binaria", (
            expressao_para_ir(no.esquerda), no.operador, expressao_para_ir(no.direita)
        ))
    if isinstance(no, Indice):
        return ExpressaoIR("indice", (
            expressao_para_ir(no.colecao), expressao_para_ir(no.indice)
        ))
    raise ErroSemantico(f"expressão não suportada pela representação intermediária: {type(no).__name__}")


def instrucao_para_ir(no: object) -> InstrucaoIR:
    if isinstance(no, Mostrar):
        return InstrucaoIR("exibir", (tuple(expressao_para_ir(v) for v in no.valores),))
    if isinstance(no, Definir):
        return InstrucaoIR("declarar", (no.nome, expressao_para_ir(no.valor)))
    if isinstance(no, Atribuir):
        return InstrucaoIR("atribuir", (no.nome, expressao_para_ir(no.valor)))
    if isinstance(no, ExpressaoInstrucao):
        return InstrucaoIR("avaliar", (expressao_para_ir(no.expressao),))
    if isinstance(no, Condicional):
        return InstrucaoIR("condicional", (
            expressao_para_ir(no.condicao),
            ProgramaIR(tuple(_instrucao_com_posicao(i) for i in no.caminho_verdadeiro)),
            ProgramaIR(tuple(_instrucao_com_posicao(i) for i in no.caminho_falso)),
        ))
    if isinstance(no, Enquanto):
        return InstrucaoIR("enquanto", (
            expressao_para_ir(no.condicao),
            ProgramaIR(tuple(_instrucao_com_posicao(i) for i in no.corpo)),
        ))
    if isinstance(no, ParaCada):
        return InstrucaoIR("para_cada", (
            no.nome, expressao_para_ir(no.iteravel),
            ProgramaIR(tuple(_instrucao_com_posicao(i) for i in no.corpo)),
        ))
    if isinstance(no, FuncaoDeclaracao):
        return InstrucaoIR("declarar_funcao", (
            no.nome, tuple(no.parametros),
            ProgramaIR(tuple(_instrucao_com_posicao(i) for i in no.corpo)),
        ))
    if isinstance(no, Retornar):
        return InstrucaoIR("retornar", (
            None if no.valor is None else expressao_para_ir(no.valor),
        ))
    if isinstance(no, Importar):
        return InstrucaoIR("importar_modulo", (no.caminho,))
    if isinstance(no, AtribuirIndice):
        return InstrucaoIR("atribuir_indice", (
            expressao_para_ir(no.colecao), expressao_para_ir(no.indice),
            expressao_para_ir(no.valor),
        ))
    if isinstance(no, Tentar):
        return InstrucaoIR("tentar", (
            ProgramaIR(tuple(_instrucao_com_posicao(i) for i in no.corpo)),
            no.nome_erro,
            ProgramaIR(tuple(_instrucao_com_posicao(i) for i in no.captura)),
            ProgramaIR(tuple(_instrucao_com_posicao(i) for i in no.finalmente)),
        ))
    if isinstance(no, Lancar):
        return InstrucaoIR("lancar", (expressao_para_ir(no.valor),))
    if isinstance(no, Interromper):
        return InstrucaoIR("interromper")
    if isinstance(no, Continuar):
        return InstrucaoIR("continuar")
    raise ErroSemantico(f"instrução não suportada pela representação intermediária: {type(no).__name__}")


def _instrucao_com_posicao(no: object) -> InstrucaoIR:
    instrucao = instrucao_para_ir(no)
    return InstrucaoIR(
        instrucao.operacao, instrucao.argumentos, getattr(no, "posicao", None)
    )


def programa_para_ir(programa: Programa) -> ProgramaIR:
    return ProgramaIR(tuple(_instrucao_com_posicao(i) for i in programa.declaracoes))


def expressao_ir_para_no(expressao: ExpressaoIR) -> object:
    op, args = expressao.operacao, expressao.argumentos
    if op == "literal":
        return Literal(args[0])
    if op == "referencia":
        return Variavel(args[0])
    if op == "lista":
        return ListaLiteral([expressao_ir_para_no(item) for item in args[0]])
    if op == "chamada":
        return Chamada(
            expressao_ir_para_no(args[0]),
            [expressao_ir_para_no(item) for item in args[1]],
        )
    if op == "unaria":
        return Unaria(args[0], expressao_ir_para_no(args[1]))
    if op == "binaria":
        return Binaria(expressao_ir_para_no(args[0]), args[1], expressao_ir_para_no(args[2]))
    if op == "indice":
        return Indice(expressao_ir_para_no(args[0]), expressao_ir_para_no(args[1]))
    raise ErroSemantico(f"operação de expressão desconhecida na IR: {op}")


def _instrucao_ir_para_no_sem_posicao(instrucao: InstrucaoIR) -> object:
    op, args = instrucao.operacao, instrucao.argumentos
    if op == "exibir":
        return Mostrar([expressao_ir_para_no(v) for v in args[0]])
    if op == "declarar":
        return Definir(args[0], expressao_ir_para_no(args[1]))
    if op == "atribuir":
        return Atribuir(args[0], expressao_ir_para_no(args[1]))
    if op == "avaliar":
        return ExpressaoInstrucao(expressao_ir_para_no(args[0]))
    if op == "condicional":
        return Condicional(
            expressao_ir_para_no(args[0]),
            [instrucao_ir_para_no(i) for i in args[1].instrucoes],
            [instrucao_ir_para_no(i) for i in args[2].instrucoes],
        )
    if op == "enquanto":
        return Enquanto(
            expressao_ir_para_no(args[0]),
            [instrucao_ir_para_no(i) for i in args[1].instrucoes],
        )
    if op == "para_cada":
        return ParaCada(
            args[0], expressao_ir_para_no(args[1]),
            [instrucao_ir_para_no(i) for i in args[2].instrucoes],
        )
    if op == "declarar_funcao":
        return FuncaoDeclaracao(
            args[0], list(args[1]),
            [instrucao_ir_para_no(i) for i in args[2].instrucoes],
        )
    if op == "retornar":
        return Retornar(None if args[0] is None else expressao_ir_para_no(args[0]))
    if op == "importar_modulo":
        return Importar(args[0])
    if op == "atribuir_indice":
        return AtribuirIndice(
            expressao_ir_para_no(args[0]), expressao_ir_para_no(args[1]),
            expressao_ir_para_no(args[2]),
        )
    if op == "tentar":
        return Tentar(
            [instrucao_ir_para_no(i) for i in args[0].instrucoes],
            args[1],
            [instrucao_ir_para_no(i) for i in args[2].instrucoes],
            [instrucao_ir_para_no(i) for i in args[3].instrucoes],
        )
    if op == "lancar":
        return Lancar(expressao_ir_para_no(args[0]))
    if op == "interromper":
        return Interromper()
    if op == "continuar":
        return Continuar()
    raise ErroSemantico(f"operação de instrução desconhecida na IR: {op}")


def instrucao_ir_para_no(instrucao: InstrucaoIR) -> object:
    no = _instrucao_ir_para_no_sem_posicao(instrucao)
    if hasattr(no, "posicao"):
        no.posicao = instrucao.posicao
    return no


def programa_ir_para_ast(programa: ProgramaIR) -> Programa:
    return Programa([instrucao_ir_para_no(i) for i in programa.instrucoes])
