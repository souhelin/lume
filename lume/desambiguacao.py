"""Desambiguação lexical contextual, conservadora e determinística."""
from __future__ import annotations

from dataclasses import dataclass
import re
from .lexicon import CorrespondenciaLexical, Lexicon, normalizar_forma


@dataclass(frozen=True, slots=True)
class CandidatoSentido:
    correspondencia: CorrespondenciaLexical
    pontuacao: float
    evidencias: tuple[str, ...]
    fontes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResultadoToken:
    token: str
    candidatos: tuple[CandidatoSentido, ...]
    selecionado: CandidatoSentido | None
    ambiguo: bool


class DesambiguadorContextual:
    """Pontua sentidos com pistas locais; nunca inventa uma escolha sem evidência."""

    ARTIGOS = {"o", "a", "os", "as", "um", "uma", "uns", "umas"}
    PREPOSICOES = {"de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas"}

    def __init__(self, lexicon: Lexicon, *, margem_minima: float = 1.5) -> None:
        if margem_minima < 0:
            raise ValueError("a margem mínima não pode ser negativa")
        self.lexicon = lexicon
        self.margem_minima = margem_minima

    @staticmethod
    def _classe_esperada(tokens: list[str], indice: int) -> str | None:
        anterior = tokens[indice - 1] if indice else ""
        if anterior in DesambiguadorContextual.ARTIGOS:
            return "substantivo"
        if anterior in {"muito", "muita", "muitos", "muitas"}:
            return "adjetivo"
        if anterior in {"não", "nunca", "sempre", "já"}:
            return "verbo"
        if anterior in DesambiguadorContextual.PREPOSICOES:
            return "substantivo"
        return None

    def analisar(self, texto: str) -> tuple[ResultadoToken, ...]:
        tokens = [normalizar_forma(m.group(0)) for m in re.finditer(r"[^\W_]+", texto, re.UNICODE)]
        resultados: list[ResultadoToken] = []
        for indice, token in enumerate(tokens):
            correspondencias = self.lexicon.buscar(token)
            if not correspondencias:
                continue
            esperada = self._classe_esperada(tokens, indice)
            grupos: dict[tuple[str, str], list[CorrespondenciaLexical]] = {}
            for correspondencia in correspondencias:
                chave_grupo = (
                    normalizar_forma(correspondencia.entrada.lema),
                    normalizar_forma(correspondencia.entrada.classe_gramatical),
                )
                grupos.setdefault(chave_grupo, []).append(correspondencia)
            candidatos: list[CandidatoSentido] = []
            for grupo in grupos.values():
                grupo.sort(key=lambda c: (c.entrada.fonte, c.entrada.identificador))
                correspondencia = grupo[0]
                classe = normalizar_forma(correspondencia.entrada.classe_gramatical)
                pontos = 0.0
                evidencias: list[str] = []
                if esperada and classe == esperada:
                    pontos += 3.0
                    evidencias.append(f"pista sintática local: {esperada}")
                elif esperada and classe != "não_classificada":
                    pontos -= 1.0
                    evidencias.append(f"classe não corresponde à pista {esperada}")
                contextos = {
                    normalizar_forma(contexto)
                    for origem in grupo
                    for contexto in self.lexicon.contextos(origem.entrada.identificador)
                }
                janela = set(tokens[max(0, indice - 3):indice] + tokens[indice + 1:indice + 4])
                sobreposicao = contextos & janela
                if sobreposicao:
                    pontos += min(2.0, 0.75 * len(sobreposicao))
                    evidencias.append("contexto lexical compartilhado: " + ", ".join(sorted(sobreposicao)))
                fontes = tuple(sorted({origem.entrada.fonte for origem in grupo}))
                candidatos.append(
                    CandidatoSentido(correspondencia, pontos, tuple(evidencias), fontes)
                )
            candidatos.sort(
                key=lambda c: (
                    -c.pontuacao,
                    c.correspondencia.entrada.lema,
                    c.correspondencia.entrada.identificador,
                )
            )
            selecionado = None
            ambiguo = len(candidatos) > 1
            if len(candidatos) == 1:
                selecionado = candidatos[0]
                ambiguo = False
            elif candidatos and candidatos[0].pontuacao - candidatos[1].pontuacao >= self.margem_minima:
                selecionado = candidatos[0]
                ambiguo = False
            resultados.append(ResultadoToken(token, tuple(candidatos), selecionado, ambiguo))
        return tuple(resultados)
