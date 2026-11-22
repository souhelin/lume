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
    identificador_sentido: str | None = None
    definicao: str | None = None
    lemas_relacionados: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResultadoToken:
    token: str
    candidatos: tuple[CandidatoSentido, ...]
    selecionado: CandidatoSentido | None
    ambiguo: bool


class DesambiguadorContextual:
    """Pontua sentidos/synsets; não força uma leitura sem evidência suficiente."""

    ARTIGOS = {"o", "a", "os", "as", "um", "uma", "uns", "umas"}
    PREPOSICOES = {"de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas"}
    STOPWORDS = {
        "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da",
        "dos", "das", "em", "no", "na", "nos", "nas", "e", "ou", "com",
        "para", "por", "que", "se", "ao", "aos", "à", "às", "ser", "ter",
    }

    def __init__(self, lexicon: Lexicon, *, margem_minima: float = 1.5) -> None:
        if margem_minima < 0:
            raise ValueError("a margem mínima não pode ser negativa")
        self.lexicon = lexicon
        self.margem_minima = margem_minima

    @staticmethod
    def _tokens(texto: str) -> list[str]:
        return [
            normalizar_forma(match.group(0))
            for match in re.finditer(r"[^\W_]+", texto, re.UNICODE)
        ]

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

    def _pontuar(
        self,
        correspondencia: CorrespondenciaLexical,
        grupo: list[CorrespondenciaLexical],
        tokens: list[str],
        indice: int,
        *,
        identificador_sentido: str | None,
        definicao: str | None,
        lemas_relacionados: tuple[str, ...],
        fontes: tuple[str, ...],
    ) -> CandidatoSentido:
        classe = normalizar_forma(correspondencia.entrada.classe_gramatical)
        esperada = self._classe_esperada(tokens, indice)
        pontos = 0.0
        evidencias: list[str] = []
        if esperada and classe == esperada:
            pontos += 3.0
            evidencias.append(f"pista sintática local: {esperada}")
        elif esperada and classe not in {"não_classificada", "forma_verbal_sem_lema"}:
            pontos -= 1.0
            evidencias.append(f"classe não corresponde à pista {esperada}")

        janela = set(
            tokens[max(0, indice - 3):indice]
            + tokens[indice + 1:indice + 4]
        ) - self.STOPWORDS
        contextos = {
            token_contexto
            for origem in grupo
            for contexto in self.lexicon.contextos(origem.entrada.identificador)
            for token_contexto in self._tokens(contexto)
        }
        sobreposicao_contexto = contextos & janela
        if sobreposicao_contexto:
            pontos += min(2.0, 0.75 * len(sobreposicao_contexto))
            evidencias.append(
                "contexto lexical registrado: " + ", ".join(sorted(sobreposicao_contexto))
            )

        glossario = set(self._tokens(definicao or "")) - self.STOPWORDS
        sobreposicao_glossa = glossario & janela
        if sobreposicao_glossa:
            pontos += min(4.0, 2.0 * len(sobreposicao_glossa))
            evidencias.append(
                "termos da glossa presentes no contexto: "
                + ", ".join(sorted(sobreposicao_glossa))
            )

        relacionados = {
            token_relacionado
            for lema in lemas_relacionados
            for token_relacionado in self._tokens(lema)
        } - {normalizar_forma(correspondencia.entrada.lema)}
        sobreposicao_synset = relacionados & janela
        if sobreposicao_synset:
            pontos += min(3.0, 1.5 * len(sobreposicao_synset))
            evidencias.append(
                "membros do synset presentes no contexto: "
                + ", ".join(sorted(sobreposicao_synset))
            )

        return CandidatoSentido(
            correspondencia=correspondencia,
            pontuacao=pontos,
            evidencias=tuple(evidencias),
            fontes=fontes,
            identificador_sentido=identificador_sentido,
            definicao=definicao,
            lemas_relacionados=lemas_relacionados,
        )

    def analisar(self, texto: str) -> tuple[ResultadoToken, ...]:
        tokens = self._tokens(texto)
        resultados: list[ResultadoToken] = []
        for indice, token in enumerate(tokens):
            correspondencias = self.lexicon.buscar(token)
            if not correspondencias:
                continue

            grupos: dict[tuple[str, str], list[CorrespondenciaLexical]] = {}
            for correspondencia in correspondencias:
                chave = (
                    normalizar_forma(correspondencia.entrada.lema),
                    normalizar_forma(correspondencia.entrada.classe_gramatical),
                )
                grupos.setdefault(chave, []).append(correspondencia)

            candidatos: list[CandidatoSentido] = []
            for grupo in grupos.values():
                grupo.sort(key=lambda item: (item.entrada.fonte, item.entrada.identificador))
                representante = grupo[0]
                sentidos: dict[tuple[str, str], dict[str, str | None]] = {}
                correspondencia_por_fonte: dict[str, CorrespondenciaLexical] = {}
                for origem in grupo:
                    for sentido in self.lexicon.sentidos(origem.entrada.identificador):
                        chave_sentido = (str(sentido["fonte_id"]), str(sentido["id"]))
                        sentidos[chave_sentido] = sentido
                        correspondencia_por_fonte.setdefault(str(sentido["fonte_id"]), origem)

                if sentidos:
                    for chave_sentido, sentido in sorted(sentidos.items()):
                        fonte_sentido, identificador = chave_sentido
                        correspondencia = correspondencia_por_fonte.get(
                            fonte_sentido, representante
                        )
                        lemas = self.lexicon.termos_do_sentido(identificador)
                        fontes = tuple(sorted({fonte_sentido}))
                        candidatos.append(
                            self._pontuar(
                                correspondencia, grupo, tokens, indice,
                                identificador_sentido=identificador,
                                definicao=sentido.get("definicao"),
                                lemas_relacionados=lemas,
                                fontes=fontes,
                            )
                        )
                else:
                    fontes = tuple(sorted({origem.entrada.fonte for origem in grupo}))
                    candidatos.append(
                        self._pontuar(
                            representante, grupo, tokens, indice,
                            identificador_sentido=None,
                            definicao=representante.entrada.definicao,
                            lemas_relacionados=(),
                            fontes=fontes,
                        )
                    )

            candidatos.sort(
                key=lambda item: (
                    -item.pontuacao,
                    item.correspondencia.entrada.lema,
                    item.identificador_sentido or "",
                    item.fontes,
                )
            )
            selecionado = None
            ambiguo = len(candidatos) > 1
            if len(candidatos) == 1:
                selecionado = candidatos[0]
                ambiguo = False
            elif candidatos and (
                candidatos[0].pontuacao - candidatos[1].pontuacao >= self.margem_minima
            ):
                selecionado = candidatos[0]
                ambiguo = False
            resultados.append(ResultadoToken(token, tuple(candidatos), selecionado, ambiguo))
        return tuple(resultados)
