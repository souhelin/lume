"""Interpretador da Lume, separado do analisador léxico e sintático."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Callable

from .ambiente import Ambiente
from .erros import (
    ErroExecucao,
    ErroLume,
    SinalContinuar,
    SinalInterromper,
    SinalRetorno,
)
from .nos import (
    Atribuir,
    AtribuirIndice,
    Importar,
    Tentar,
    Lancar,
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
        diretorio_raiz: str | Path | None = None,
    ) -> None:
        self.saida = saida or print
        self.entrada = entrada or input
        self.limite_passos = limite_passos
        self.diretorio_raiz = Path(diretorio_raiz or Path.cwd()).resolve()
        self._modulos_carregados: set[Path] = set()
        self._modulos_em_carga: set[Path] = set()
        self.passos = 0
        self.nivel_lacos = 0
        self.ambiente = Ambiente()
        from .biblioteca import registrar_biblioteca
        registrar_biblioteca(self)

    def executar(self, programa: Programa) -> None:
        self.passos = 0
        self._executar_programa(programa)

    def _executar_programa(self, programa: Programa) -> None:
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
                try:
                    self._executar_instrucao(declaracao)
                except ErroLume as erro:
                    if erro.posicao is None:
                        erro.posicao = getattr(declaracao, "posicao", None)
                    raise
        finally:
            self.ambiente = anterior

    def _resolver_caminho(self, caminho: object) -> Path:
        if not isinstance(caminho, str) or not caminho.strip():
            raise ErroExecucao("o caminho precisa ser um texto não vazio")
        relativo = Path(caminho)
        if relativo.is_absolute():
            raise ErroExecucao("caminhos absolutos não são permitidos")
        destino = (self.diretorio_raiz / relativo).resolve()
        try:
            destino.relative_to(self.diretorio_raiz)
        except ValueError as erro:
            raise ErroExecucao("o caminho precisa permanecer dentro do diretório do projeto") from erro
        return destino

    def _executar_modulo(self, caminho: str) -> None:
        arquivo = self._resolver_caminho(caminho)
        if arquivo.suffix.casefold() != ".lume":
            raise ErroExecucao("módulos precisam usar a extensão .lume")
        if arquivo in self._modulos_carregados:
            return
        if arquivo in self._modulos_em_carga:
            raise ErroExecucao(f"ciclo de importação detectado no módulo '{caminho}'")
        try:
            dados = arquivo.read_bytes()
        except FileNotFoundError as erro:
            raise ErroExecucao(f"módulo não encontrado: '{caminho}'") from erro
        except OSError as erro:
            raise ErroExecucao(f"não foi possível ler o módulo '{caminho}': {erro}") from erro
        if len(dados) > 1_048_576:
            raise ErroExecucao("o módulo ultrapassa o limite de 1 MiB")
        try:
            fonte = dados.decode("utf-8")
        except UnicodeDecodeError as erro:
            raise ErroExecucao(f"o módulo '{caminho}' não está codificado em UTF-8") from erro
        self._modulos_em_carga.add(arquivo)
        try:
            from .semantica import InterpretadorSemantico, detectar_sintaxe_semantica
            if detectar_sintaxe_semantica(fonte):
                from .representacao import programa_ir_para_ast
                semantico = InterpretadorSemantico(self)
                resultado = semantico.verificar(fonte)
                self._executar_programa(programa_ir_para_ast(resultado.programa))
                semantico.compilador.confirmar(resultado)
            else:
                from .parser import analisar_sintaxe
                self._executar_programa(analisar_sintaxe(fonte))
            self._modulos_carregados.add(arquivo)
        finally:
            self._modulos_em_carga.discard(arquivo)

    def _ler_arquivo(self, caminho: object) -> str:
        arquivo = self._resolver_caminho(caminho)
        try:
            dados = arquivo.read_bytes()
        except OSError as erro:
            raise ErroExecucao(f"não foi possível ler o arquivo: {erro}") from erro
        if len(dados) > 1_048_576:
            raise ErroExecucao("o arquivo ultrapassa o limite de leitura de 1 MiB")
        try:
            return dados.decode("utf-8")
        except UnicodeDecodeError as erro:
            raise ErroExecucao("o arquivo não está codificado em UTF-8") from erro

    def _escrever_arquivo(self, caminho: object, conteudo: object, anexar: bool = False) -> None:
        arquivo = self._resolver_caminho(caminho)
        if not isinstance(conteudo, str):
            raise ErroExecucao("o conteúdo do arquivo precisa ser um texto")
        dados = conteudo.encode("utf-8")
        if len(dados) > 1_048_576:
            raise ErroExecucao("o conteúdo ultrapassa o limite de escrita de 1 MiB")
        if anexar and arquivo.exists():
            try:
                if arquivo.stat().st_size + len(dados) > 1_048_576:
                    raise ErroExecucao("o arquivo ultrapassaria o limite de 1 MiB")
            except OSError as erro:
                raise ErroExecucao(f"não foi possível consultar o arquivo: {erro}") from erro
        try:
            modo = "ab" if anexar else "wb"
            with arquivo.open(modo) as destino:
                destino.write(dados)
        except OSError as erro:
            raise ErroExecucao(f"não foi possível escrever o arquivo: {erro}") from erro

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

        if isinstance(no, Atribuir):
            valor = self._avaliar(no.valor)
            self.ambiente.atribuir(no.nome, valor)
            return

        if isinstance(no, Importar):
            self._executar_modulo(no.caminho)
            return

        if isinstance(no, AtribuirIndice):
            colecao = self._avaliar(no.colecao)
            indice = self._avaliar(no.indice)
            valor = self._avaliar(no.valor)
            if not isinstance(colecao, list):
                raise ErroExecucao("atribuição por índice só é permitida em listas")
            if type(indice) is not int:
                raise ErroExecucao("o índice de atribuição precisa ser inteiro")
            try:
                colecao[indice] = valor
            except IndexError as erro:
                raise ErroExecucao(f"índice {indice} fora dos limites da lista") from erro
            return

        if isinstance(no, Tentar):
            try:
                self._executar_bloco(no.corpo, self.ambiente)
            except ErroExecucao as erro:
                if not no.captura:
                    raise
                local = Ambiente(self.ambiente)
                if no.nome_erro:
                    local.definir(no.nome_erro, str(erro))
                self._executar_bloco(no.captura, local)
            finally:
                if no.finalmente:
                    self._executar_bloco(no.finalmente, self.ambiente)
            return

        if isinstance(no, Lancar):
            valor = self._avaliar(no.valor)
            raise ErroExecucao(self._formatar(valor))

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
