"""Linguagem de programação Lume."""

__version__ = "0.1.0"

from .interpretador import Interpretador
from .parser import analisar_sintaxe

__all__ = ["Interpretador", "analisar_sintaxe", "__version__"]
