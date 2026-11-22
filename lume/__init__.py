"""API pública da linguagem de programação Lume."""

__version__ = "0.1.0"

from .erros import ErroAmbiguidade, ErroSemantico
from .interpretador import Interpretador
from .parser import analisar_sintaxe
from .representacao import ExpressaoIR, InstrucaoIR, ProgramaIR
from .semantica import (
    CompiladorSemantico,
    ContextoSemantico,
    InterpretadorSemantico,
    ResultadoCompilacao,
    compilar_semantico,
    detectar_sintaxe_semantica,
)
from .vocabulario import (
    DICIONARIO_PADRAO,
    DicionarioSemantico,
    EntradaSemantica,
    criar_dicionario_padrao,
)

__all__ = [
    "Interpretador",
    "ErroSemantico",
    "ErroAmbiguidade",
    "analisar_sintaxe",
    "CompiladorSemantico",
    "ContextoSemantico",
    "InterpretadorSemantico",
    "ResultadoCompilacao",
    "compilar_semantico",
    "detectar_sintaxe_semantica",
    "DICIONARIO_PADRAO",
    "DicionarioSemantico",
    "EntradaSemantica",
    "criar_dicionario_padrao",
    "ExpressaoIR",
    "InstrucaoIR",
    "ProgramaIR",
    "__version__",
]
