"""Biblioteca padrão nativa da Lume."""

from __future__ import annotations

import math
from typing import Callable

from .erros import ErroExecucao


def registrar_biblioteca(interpretador: object) -> None:
    from .interpretador import FuncaoNativa

    def registrar(nome: str, minimo: int, maximo: int | None, funcao: Callable[..., object]) -> None:
        interpretador.ambiente.definir(nome, FuncaoNativa(nome, minimo, maximo, funcao))

    def converter_numero(valor: object) -> int | float:
        if type(valor) in (int, float):
            return valor
        if not isinstance(valor, str):
            raise ErroExecucao("a conversão para número exige um texto ou número")
        try:
            convertido = valor.strip().replace(",", ".")
            numero = float(convertido)
            if not math.isfinite(numero):
                raise ErroExecucao("o número precisa ser finito")
            return int(numero) if numero.is_integer() else numero
        except ValueError as erro:
            raise ErroExecucao(f"'{valor}' não representa um número válido") from erro

    def intervalo(inicio: object, fim: object, passo: object = 1) -> list[int]:
        if type(inicio) is not int or type(fim) is not int or type(passo) is not int:
            raise ErroExecucao("'intervalo' exige números inteiros")
        if passo == 0:
            raise ErroExecucao("o passo de 'intervalo' não pode ser zero")
        parada = fim + (1 if passo > 0 else -1)
        quantidade = len(range(inicio, parada, passo))
        if quantidade > interpretador.LIMITE_COLECAO:
            raise ErroExecucao("o intervalo ultrapassa o limite permitido de itens")
        return list(range(inicio, parada, passo))

    registrar("comprimento", 1, 1, lambda valor: len(valor) if isinstance(valor, (str, list, tuple)) else interpretador._erro_tipo("'comprimento' aceita texto ou lista"))
    registrar("texto", 1, 1, lambda valor: interpretador._formatar(valor))
    registrar("numero", 1, 1, converter_numero)
    registrar("inteiro", 1, 1, lambda valor: int(converter_numero(valor)))
    registrar("decimal", 1, 1, lambda valor: float(converter_numero(valor)))
    registrar("tipo", 1, 1, interpretador._tipo)

    def exigir_lexicon() -> object:
        lexicon = getattr(interpretador, "lexicon", None)
        if lexicon is None:
            raise ErroExecucao(
                "o Lexicon não está carregado; injete Lexicon no Interpretador "
                "ou execute a CLI com --lexicon CAMINHO"
            )
        return lexicon

    def consultar_lexico(termo: object) -> list[str]:
        if not isinstance(termo, str):
            raise ErroExecucao("'consultar_lexico' exige um texto")
        lexicon = exigir_lexicon()
        correspondencias = lexicon.buscar(termo)
        resultados: list[str] = []
        for item in correspondencias:
            entrada = item.entrada
            definicao = entrada.definicao or "definição não disponível"
            resultados.append(
                f"{entrada.lema} ({entrada.classe_gramatical}): {definicao} "
                f"[fonte: {entrada.fonte}; licença: {entrada.licenca}; "
                f"versão: {entrada.versao_fonte}]"
            )
        return resultados

    def analisar_lexico(texto: object) -> list[str]:
        if not isinstance(texto, str):
            raise ErroExecucao("'analisar_lexico' exige um texto")
        from .desambiguacao import DesambiguadorContextual
        resultados = DesambiguadorContextual(exigir_lexicon()).analisar(texto)
        saida: list[str] = []
        for resultado in resultados:
            if resultado.selecionado is None:
                candidatos = "; ".join(
                    f"{item.correspondencia.entrada.lema} "
                    f"({item.correspondencia.entrada.classe_gramatical}, "
                    f"sentido={item.identificador_sentido or 'sem synset'}, "
                    f"pontuação={item.pontuacao:g})"
                    for item in resultado.candidatos
                )
                saida.append(f"{resultado.token}: ambíguo — {candidatos}")
            else:
                item = resultado.selecionado
                entrada = item.correspondencia.entrada
                definicao = item.definicao or entrada.definicao or "definição não disponível"
                saida.append(
                    f"{resultado.token}: {entrada.lema} "
                    f"({entrada.classe_gramatical}) — {definicao}"
                )
        return saida

    registrar("consultar_lexico", 1, 1, consultar_lexico)
    registrar("analisar_lexico", 1, 1, analisar_lexico)

    def perguntar(mensagem: object = "") -> str:
        try:
            return interpretador.entrada(interpretador._formatar(mensagem))
        except EOFError as erro:
            raise ErroExecucao("a entrada foi encerrada antes de receber uma resposta") from erro

    registrar("perguntar", 0, 1, perguntar)
    registrar("intervalo", 2, 3, intervalo)

    def somar(valores: object) -> int | float:
        if not isinstance(valores, (list, tuple)) or not all(interpretador._numero_valido(v) for v in valores):
            raise ErroExecucao("'somar' exige uma lista de números")
        resultado = sum(valores)
        if abs(resultado) > 10**100 or (isinstance(resultado, float) and not math.isfinite(resultado)):
            raise ErroExecucao("a soma ultrapassa o limite numérico permitido")
        return resultado

    registrar("somar", 1, 1, somar)
    registrar("minimo", 1, 1, lambda valores: min(valores) if isinstance(valores, (list, tuple)) and valores else interpretador._erro_tipo("'minimo' exige uma lista não vazia"))
    registrar("maximo", 1, 1, lambda valores: max(valores) if isinstance(valores, (list, tuple)) and valores else interpretador._erro_tipo("'maximo' exige uma lista não vazia"))
    registrar("arredondar", 1, 2, lambda valor, casas=0: round(valor, casas) if interpretador._numero_valido(valor) and type(casas) is int else interpretador._erro_tipo("'arredondar' exige um número e, opcionalmente, casas inteiras"))
    registrar("maiusculas", 1, 1, lambda valor: valor.upper() if isinstance(valor, str) else interpretador._erro_tipo("'maiusculas' exige um texto"))
    registrar("minusculas", 1, 1, lambda valor: valor.lower() if isinstance(valor, str) else interpretador._erro_tipo("'minusculas' exige um texto"))
    def validar_lista(valor: object, nome: str) -> list[object]:
        if not isinstance(valor, list):
            raise ErroExecucao(f"'{nome}' exige uma lista")
        return valor

    def adicionar(lista: object, valor: object) -> int:
        destino = validar_lista(lista, "adicionar")
        if len(destino) >= interpretador.LIMITE_COLECAO:
            raise ErroExecucao("a lista atingiu o limite permitido de itens")
        destino.append(valor)
        return len(destino)

    def remover(lista: object, indice: object) -> object:
        destino = validar_lista(lista, "remover")
        if type(indice) is not int:
            raise ErroExecucao("o índice de 'remover' precisa ser inteiro")
        try:
            return destino.pop(indice)
        except IndexError as erro:
            raise ErroExecucao(f"índice {indice} fora dos limites da lista") from erro

    def inserir(lista: object, indice: object, valor: object) -> int:
        destino = validar_lista(lista, "inserir")
        if type(indice) is not int:
            raise ErroExecucao("o índice de 'inserir' precisa ser inteiro")
        if len(destino) >= interpretador.LIMITE_COLECAO:
            raise ErroExecucao("a lista atingiu o limite permitido de itens")
        if indice < -len(destino) or indice > len(destino):
            raise ErroExecucao(f"índice {indice} fora dos limites da lista")
        destino.insert(indice, valor)
        return len(destino)

    def ordenar(lista: object) -> list[object]:
        origem = validar_lista(lista, "ordenar")
        try:
            return sorted(origem)
        except TypeError as erro:
            raise ErroExecucao("não é possível ordenar valores de tipos incompatíveis") from erro

    registrar("adicionar", 2, 2, adicionar)
    registrar("inserir", 3, 3, inserir)
    registrar("remover", 2, 2, remover)
    registrar("contem", 2, 2, lambda colecao, valor: valor in colecao if isinstance(colecao, (list, tuple, str)) else interpretador._erro_tipo("'contem' exige uma lista ou texto"))
    registrar("ordenar", 1, 1, ordenar)
    registrar("inverter", 1, 1, lambda colecao: colecao[::-1] if isinstance(colecao, (list, tuple, str)) else interpretador._erro_tipo("'inverter' exige uma lista ou texto"))
    registrar("ler_arquivo", 1, 1, interpretador._ler_arquivo)
    registrar("escrever_arquivo", 2, 2, lambda caminho, texto: interpretador._escrever_arquivo(caminho, texto))
    registrar("anexar_arquivo", 2, 2, lambda caminho, texto: interpretador._escrever_arquivo(caminho, texto, anexar=True))
    registrar("existe_arquivo", 1, 1, lambda caminho: interpretador._resolver_caminho(caminho).is_file())
    registrar("juntar", 2, 2, lambda lista, separador: separador.join(lista) if isinstance(lista, (list, tuple)) and isinstance(separador, str) and all(isinstance(item, str) for item in lista) else interpretador._erro_tipo("'juntar' exige uma lista de textos e um separador"))
    # As funções só alcançam a rede quando o programa as chama e o host está autorizado.
    registrar("http_obter", 1, 1, interpretador._http_obter)
    registrar("http_enviar", 2, 2, interpretador._http_enviar)
    registrar("baixar", 2, 2, interpretador._baixar_arquivo)


