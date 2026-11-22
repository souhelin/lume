"""Formatador determinístico da fonte Lume."""

from __future__ import annotations

import re


_ABERTURAS = (
    re.compile(r"^se\s+.+\s+ent[aã]o$", re.IGNORECASE),
    re.compile(r"^enquanto\s+.+\s+fa[çc]a$", re.IGNORECASE),
    re.compile(r"^para\s+cada\s+.+\s+fa[çc]a$", re.IGNORECASE),
    re.compile(r"^função\s+.+\s+fa[çc]a$", re.IGNORECASE),
    re.compile(r"^tente$", re.IGNORECASE),
)
_FECHAMENTOS = re.compile(
    r"^(?:fim(?:\s+da\s+(?:repetiç[aã]o|funç[aã]o))?|"
    r"sen[aã]o(?:\s+se\s+.+\s+ent[aã]o)?|caso\s+contr[aá]rio|capture(?:\s+\w+)?|finalmente)$",
    re.IGNORECASE,
)
_RAMO = re.compile(r"^(?:sen[aã]o(?:\s+se\s+.+\s+ent[aã]o)?|caso\s+contr[aá]rio|capture(?:\s+\w+)?|finalmente)$", re.IGNORECASE)


def formatar_fonte(fonte: str) -> str:
    """Normaliza recuo e espaços externos sem reescrever expressões ou textos."""
    nivel = 0
    linhas_formatadas: list[str] = []
    for original in fonte.splitlines():
        texto = original.strip()
        if not texto:
            if linhas_formatadas and linhas_formatadas[-1] != "":
                linhas_formatadas.append("")
            continue
        if _FECHAMENTOS.fullmatch(texto):
            nivel = max(0, nivel - 1)
        linhas_formatadas.append("    " * nivel + texto)
        if _RAMO.fullmatch(texto):
            nivel += 1
        elif any(padrao.fullmatch(texto) for padrao in _ABERTURAS):
            nivel += 1
    while linhas_formatadas and not linhas_formatadas[-1]:
        linhas_formatadas.pop()
    resultado = "\n".join(linhas_formatadas)
    return resultado + ("\n" if fonte.endswith(("\n", "\r")) else "")
