"""API pública da linguagem de programação Lume."""

__version__ = "0.3.0"

from .erros import (ErroAmbiguidade, ErroExecucao, ErroLume, ErroLexico, ErroSemantico, ErroSintatico, Posicao)
from .interpretador import Interpretador
from .permissoes import PermissoesRede
from .formatador import formatar_fonte
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
from .desambiguacao import CandidatoSentido, DesambiguadorContextual, ResultadoToken
from .lexical_import import (
    ResultadoImportacao,
    importar_fserb_lexico,
    importar_fserb_conjugacoes,
    importar_openwordnet_tsv,
)
from .lexicon import (
    CorrespondenciaLexical,
    EntradaLexical,
    FonteLexical,
    Lexicon,
    normalizar_forma,
)
from .vocabulario import (
    DICIONARIO_PADRAO,
    DicionarioSemantico,
    EntradaSemantica,
    criar_dicionario_padrao,
)

__all__ = [
    "Interpretador",
    "Lexicon",
    "FonteLexical",
    "EntradaLexical",
    "CorrespondenciaLexical",
    "normalizar_forma",
    "DesambiguadorContextual",
    "CandidatoSentido",
    "ResultadoToken",
    "ResultadoImportacao",
    "importar_fserb_lexico",
    "importar_fserb_conjugacoes",
    "importar_openwordnet_tsv",
    "PermissoesRede",
    "formatar_fonte",
    "ErroLume",
    "ErroLexico",
    "ErroSintatico",
    "ErroExecucao",
    "Posicao",
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
