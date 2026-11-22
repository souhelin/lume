"""Interpretador da Lume, separado do analisador léxico e sintático."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

from .ambiente import Ambiente
from .erros import (
    ErroExecucao,
    SinalContinuar,
    SinalInterromper,
    SinalRetorno,
)
from .nos import (
    Binaria,
    Chamada,
    Condicional,
    Continuar,
    Definir,
    ExpressaoInstrucao,
    FuncaoDeclaracao,
    Interromper,
    Indice,
    Enquanto,
    ListaLiteral,
    Literal,
    Mostrar,
    ParaCada,
    Programa,
    Retornar,
    Unaria,
    Variavel,
)


@dataclass(slots=True)
class FuncaoNativa:
    nome: str
    minimo: int
    maximo: int | None
    executar: Callable[..., object]


@dataclass(slots=True)
class FuncaoLume:
    nome: str
    parametros: list[str]
    corpo: list[object]
    fechamento: Ambiente


class Interpretador:
    LIMITE_PASSOS = 100_000
    LIMITE_COLECAO = 100_000

    def __init__(
        self,
        saida: Callable[[str], None] | None = None,
        entrada: Callable[[str], str] | None = None,
        limite_passos: int = LIMITE_PASSOS,
    ) -> None:
        self.saida = saida or print
        self.entrada = entrada or input
        self.limite_passos = limite_passos
        self.passos = 0
        self.nivel_lacos = 0
        self.ambiente = Ambiente()
        self._registrar_biblioteca()

    def executar(self, programa: Programa) -> None:
        self.passos = 0
        try:
            self._executar_bloco(programa.declaracoes, self.ambiente)
        except SinalRetorno:
            raise ErroExecucao("'retornar' só pode ser usado dentro de uma função")
        except (SinalInterromper, SinalContinuar):
            raise ErroExecucao("comando de repetição fora de um laço")
        except RecursionError as erro:
            raise ErroExecucao("limite de chamadas de funções excedido") from erro

    def _executar_bloco(self, declaracoes: list[object], ambiente: Ambiente) -> None:
        anterior = self.ambiente
        self.ambiente = ambiente
        try:
            for declaracao in declaracoes:
                self._passo()
                self._executar_instrucao(declaracao)
        finally:
            self.ambiente = anterior

    def _passo(self) -> None:
        self.passos += 1
        if self.passos > self.limite_passos:
            raise ErroExecucao(
                f"o programa ultrapassou o limite de {self.limite_passos:,} etapas; "
                "verifique se existe uma repetição sem fim"
            )

    def _executar_instrucao(self, no: object) -> None:
        if isinstance(no, Mostrar):
            valores = [self._avaliar(item) for item in no.valores]
            self.saida(" ".join(self._formatar(valor) for valor in valores))
            return

        if isinstance(no, Definir):
            self.ambiente.definir(no.nome, self._avaliar(no.valor))
            return

        if isinstance(no, ExpressaoInstrucao):
            self._avaliar(no.expressao)
            return

        if isinstance(no, Condicional):
            caminho = no.caminho_verdadeiro if self._verdadeiro(self._avaliar(no.condicao)) else no.caminho_falso
            self._executar_bloco(caminho, self.ambiente)
            return

        if isinstance(no, Enquanto):
            self.nivel_lacos += 1
            try:
                while self._verdadeiro(self._avaliar(no.condicao)):
                    self._passo()
                    try:
                        self._executar_bloco(no.corpo, self.ambiente)
                    except SinalContinuar:
                        continue
                    except SinalInterromper:
                        break
            finally:
                self.nivel_lacos -= 1
            return

        if isinstance(no, ParaCada):
            iteravel = self._avaliar(no.iteravel)
            if not isinstance(iteravel, (list, tuple, str)):
                raise ErroExecucao("'para cada' precisa receber uma lista ou um texto")
            if len(iteravel) > self.LIMITE_COLECAO:
                raise ErroExecucao("a coleção ultrapassa o limite permitido de itens")
            self.nivel_lacos += 1
            try:
                for item in iteravel:
                    self._passo()
                    self.ambiente.definir(no.nome, item)
                    try:
                        self._executar_bloco(no.corpo, self.ambiente)
                    except SinalContinuar:
                        continue
                    except SinalInterromper:
                        break
            finally:
                self.nivel_lacos -= 1
            return

        if isinstance(no, FuncaoDeclaracao):
            self.ambiente.definir(no.nome, FuncaoLume(no.nome, no.parametros, no.corpo, self.ambiente))
            return

        if isinstance(no, Retornar):
            raise SinalRetorno(None if no.valor is None else self._avaliar(no.valor))

        if isinstance(no, Interromper):
            if self.nivel_lacos == 0:
                raise ErroExecucao("'interromper' só pode ser usado dentro de um laço")
            raise SinalInterromper()

        if isinstance(no, Continuar):
            if self.nivel_lacos == 0:
                raise ErroExecucao("'continuar' só pode ser usado dentro de um laço")
            raise SinalContinuar()

        raise ErroExecucao(f"instrução interna desconhecida: {type(no).__name__}")

    def _avaliar(self, no: object) -> object:
        if isinstance(no, Literal):
            return no.valor
        if isinstance(no, Variavel):
            return self.ambiente.obter(no.nome)
        if isinstance(no, ListaLiteral):
            if len(no.elementos) > self.LIMITE_COLECAO:
                raise ErroExecucao("a lista ultrapassa o limite permitido de itens")
            return [self._avaliar(item) for item in no.elementos]
        if isinstance(no, Unaria):
            valor = self._avaliar(no.operando)
            if no.operador == "não":
                return not self._verdadeiro(valor)
            if no.operador == "-":
                if not self._numero_valido(valor):
                    raise ErroExecucao("o sinal negativo só pode ser usado com números")
                return -valor
        if isinstance(no, Binaria):
            return self._avaliar_binaria(no)
        if isinstance(no, Chamada):
            funcao = self._avaliar(no.funcao)
            argumentos = [self._avaliar(argumento) for argumento in no.argumentos]
            return self._chamar(funcao, argumentos)
        if isinstance(no, Indice):
            colecao = self._avaliar(no.colecao)
            indice = self._avaliar(no.indice)
            if not isinstance(colecao, (list, tuple, str)):
                raise ErroExecucao("o acesso por índice exige uma lista ou um texto")
            if type(indice) is not int:
                raise ErroExecucao("o índice precisa ser um número inteiro")
            try:
                return colecao[indice]
            except IndexError as erro:
                raise ErroExecucao(f"índice {indice} fora dos limites da coleção") from erro
        raise ErroExecucao(f"expressão interna desconhecida: {type(no).__name__}")

    def _avaliar_binaria(self, no: Binaria) -> object:
        esquerda = self._avaliar(no.esquerda)
        if no.operador == "e":
            return self._verdadeiro(esquerda) and self._verdadeiro(self._avaliar(no.direita))
        if no.operador == "ou":
            return self._verdadeiro(esquerda) or self._verdadeiro(self._avaliar(no.direita))
        direita = self._avaliar(no.direita)
        op = no.operador

        if op in {"==", "!="}:
            return esquerda == direita if op == "==" else esquerda != direita
        if op in {"<", "<=", ">", ">="}:
            numeros = self._numero_valido(esquerda) and self._numero_valido(direita)
            textos = isinstance(esquerda, str) and isinstance(direita, str)
            if not (numeros or textos):
                raise ErroExecucao("a comparação exige dois números ou dois textos")
            return {"<": esquerda < direita, "<=": esquerda <= direita, ">": esquerda > direita, ">=": esquerda >= direita}[op]
        if op == "+":
            if isinstance(esquerda, str) and isinstance(direita, str):
                resultado = esquerda + direita
                if len(resultado) > self.LIMITE_COLECAO:
                    raise ErroExecucao("o texto resultante ultrapassa o limite permitido")
                return resultado
            if isinstance(esquerda, list) and isinstance(direita, list):
                resultado_lista = esquerda + direita
                if len(resultado_lista) > self.LIMITE_COLECAO:
                    raise ErroExecucao("a lista resultante ultrapassa o limite permitido")
                return resultado_lista
            if self._numero_valido(esquerda) and self._numero_valido(direita):
                resultado_numerico = esquerda + direita
                if isinstance(resultado_numerico, float) and not math.isfinite(resultado_numerico):
                    raise ErroExecucao("o resultado numérico não é finito")
                if abs(resultado_numerico) > 10**100:
                    raise ErroExecucao("o resultado ultrapassa o limite numérico permitido")
                return resultado_numerico
            raise ErroExecucao("'+' aceita dois números, dois textos ou duas listas")
        if op in {"-", "*", "/", "//", "%", "**"}:
            if not self._numero_valido(esquerda) or not self._numero_valido(direita):
                raise ErroExecucao(f"'{op}' só pode ser usado com números")
            if op == "**" and abs(direita) > 1_000:
                raise ErroExecucao("o expoente ultrapassa o limite permitido")
            try:
                resultado = {
                    "-": lambda: esquerda - direita,
                    "*": lambda: esquerda * direita,
                    "/": lambda: esquerda / direita,
                    "//": lambda: esquerda // direita,
                    "%": lambda: esquerda % direita,
                    "**": lambda: esquerda ** direita,
                }[op]()
            except ZeroDivisionError as erro:
                raise ErroExecucao("não é possível dividir por zero") from erro
            except (OverflowError, ValueError) as erro:
                raise ErroExecucao("o resultado matemático não é válido") from erro
            if isinstance(resultado, float) and not math.isfinite(resultado):
                raise ErroExecucao("o resultado numérico não é finito")
            if isinstance(resultado, (int, float)) and abs(resultado) > 10**100:
                raise ErroExecucao("o resultado ultrapassa o limite numérico permitido")
            return resultado
        raise ErroExecucao(f"operador não suportado: {op}")

    def _chamar(self, funcao: object, argumentos: list[object]) -> object:
        if isinstance(funcao, FuncaoNativa):
            if len(argumentos) < funcao.minimo or (funcao.maximo is not None and len(argumentos) > funcao.maximo):
                esperado = str(funcao.minimo) if funcao.minimo == funcao.maximo else f"entre {funcao.minimo} e {funcao.maximo or 'vários'}"
                raise ErroExecucao(f"'{funcao.nome}' espera {esperado} argumento(s); recebeu {len(argumentos)}")
            try:
                return funcao.executar(*argumentos)
            except ErroExecucao:
                raise
            except (TypeError, ValueError, OverflowError) as erro:
                raise ErroExecucao(f"não foi possível executar '{funcao.nome}': {erro}") from erro
        if isinstance(funcao, FuncaoLume):
            if len(argumentos) != len(funcao.parametros):
                raise ErroExecucao(
                    f"'{funcao.nome}' espera {len(funcao.parametros)} argumento(s); recebeu {len(argumentos)}"
                )
            local = Ambiente(funcao.fechamento)
            for nome, valor in zip(funcao.parametros, argumentos):
                local.definir(nome, valor)
            nivel_externo = self.nivel_lacos
            self.nivel_lacos = 0
            try:
                try:
                    self._executar_bloco(funcao.corpo, local)
                except SinalRetorno as retorno:
                    return retorno.valor
                return None
            finally:
                self.nivel_lacos = nivel_externo
        raise ErroExecucao("o valor informado não pode ser chamado como função")

    @staticmethod
    def _numero_valido(valor: object) -> bool:
        return type(valor) in (int, float)

    @staticmethod
    def _verdadeiro(valor: object) -> bool:
        return bool(valor)

    def _formatar(self, valor: object) -> str:
        if valor is True:
            return "verdadeiro"
        if valor is False:
            return "falso"
        if valor is None:
            return "nulo"
        if isinstance(valor, list):
            return "[" + ", ".join(self._formatar(item) for item in valor) + "]"
        return str(valor)

    def _registrar_biblioteca(self) -> None:
        def registrar(nome: str, minimo: int, maximo: int | None, funcao: Callable[..., object]) -> None:
            self.ambiente.definir(nome, FuncaoNativa(nome, minimo, maximo, funcao))

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
            if quantidade > self.LIMITE_COLECAO:
                raise ErroExecucao("o intervalo ultrapassa o limite permitido de itens")
            return list(range(inicio, parada, passo))

        registrar("comprimento", 1, 1, lambda valor: len(valor) if isinstance(valor, (str, list, tuple)) else self._erro_tipo("'comprimento' aceita texto ou lista"))
        registrar("texto", 1, 1, lambda valor: self._formatar(valor))
        registrar("numero", 1, 1, converter_numero)
        registrar("inteiro", 1, 1, lambda valor: int(converter_numero(valor)))
        registrar("decimal", 1, 1, lambda valor: float(converter_numero(valor)))
        registrar("tipo", 1, 1, self._tipo)

        def perguntar(mensagem: object = "") -> str:
            try:
                return self.entrada(self._formatar(mensagem))
            except EOFError as erro:
                raise ErroExecucao("a entrada foi encerrada antes de receber uma resposta") from erro

        registrar("perguntar", 0, 1, perguntar)
        registrar("intervalo", 2, 3, intervalo)

        def somar(valores: object) -> int | float:
            if not isinstance(valores, (list, tuple)) or not all(self._numero_valido(v) for v in valores):
                raise ErroExecucao("'somar' exige uma lista de números")
            resultado = sum(valores)
            if abs(resultado) > 10**100 or (isinstance(resultado, float) and not math.isfinite(resultado)):
                raise ErroExecucao("a soma ultrapassa o limite numérico permitido")
            return resultado

        registrar("somar", 1, 1, somar)
        registrar("minimo", 1, 1, lambda valores: min(valores) if isinstance(valores, (list, tuple)) and valores else self._erro_tipo("'minimo' exige uma lista não vazia"))
        registrar("maximo", 1, 1, lambda valores: max(valores) if isinstance(valores, (list, tuple)) and valores else self._erro_tipo("'maximo' exige uma lista não vazia"))
        registrar("arredondar", 1, 2, lambda valor, casas=0: round(valor, casas) if self._numero_valido(valor) and type(casas) is int else self._erro_tipo("'arredondar' exige um número e, opcionalmente, casas inteiras"))
        registrar("maiusculas", 1, 1, lambda valor: valor.upper() if isinstance(valor, str) else self._erro_tipo("'maiusculas' exige um texto"))
        registrar("minusculas", 1, 1, lambda valor: valor.lower() if isinstance(valor, str) else self._erro_tipo("'minusculas' exige um texto"))
        def validar_lista(valor: object, nome: str) -> list[object]:
            if not isinstance(valor, list):
                raise ErroExecucao(f"'{nome}' exige uma lista")
            return valor

        def adicionar(lista: object, valor: object) -> int:
            destino = validar_lista(lista, "adicionar")
            if len(destino) >= self.LIMITE_COLECAO:
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
            if len(destino) >= self.LIMITE_COLECAO:
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
        registrar("contem", 2, 2, lambda colecao, valor: valor in colecao if isinstance(colecao, (list, tuple, str)) else self._erro_tipo("'contem' exige uma lista ou texto"))
        registrar("ordenar", 1, 1, ordenar)
        registrar("inverter", 1, 1, lambda colecao: colecao[::-1] if isinstance(colecao, (list, tuple, str)) else self._erro_tipo("'inverter' exige uma lista ou texto"))
        registrar("juntar", 2, 2, lambda lista, separador: separador.join(lista) if isinstance(lista, (list, tuple)) and isinstance(separador, str) and all(isinstance(item, str) for item in lista) else self._erro_tipo("'juntar' exige uma lista de textos e um separador"))


    @staticmethod
    def _erro_tipo(mensagem: str) -> object:
        raise ErroExecucao(mensagem)

    @staticmethod
    def _tipo(valor: object) -> str:
        if valor is None:
            return "nulo"
        if isinstance(valor, bool):
            return "lógico"
        if type(valor) is int:
            return "inteiro"
        if type(valor) is float:
            return "decimal"
        if isinstance(valor, str):
            return "texto"
        if isinstance(valor, list):
            return "lista"
        if isinstance(valor, (FuncaoNativa, FuncaoLume)):
            return "função"
        return "desconhecido"
