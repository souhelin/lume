"""Analisador sintático: transforma tokens em uma árvore de sintaxe abstrata."""

from __future__ import annotations

from .erros import ErroSintatico
from .lexer import analisar_lexico
from .nos import (
    Atribuir,
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
from .tokens import Token


class AnalisadorSintatico:
    PRECEDENCIA = {"ou": 1, "e": 2, "comparacao": 3, "+": 4, "-": 4, "*": 5, "/": 5, "//": 5, "%": 5, "**": 6}

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.indice = 0

    def analisar(self) -> Programa:
        declaracoes = self._bloco({"FIM"})
        self._consumir_tipo("FIM", "fim do programa")
        return Programa(declaracoes)

    def _bloco(self, terminadores: set[str]) -> list[object]:
        declaracoes: list[object] = []
        self._pular_linhas()
        while not self._eh_terminador(terminadores) and self._atual().tipo != "FIM":
            antes = self.indice
            declaracoes.append(self._instrucao())
            if self.indice == antes:
                raise ErroSintatico("não foi possível avançar durante a análise", self._atual().posicao)
            if self._atual().tipo not in terminadores and self._atual().tipo != "FIM" and self._atual().tipo != "NOVA_LINHA":
                raise ErroSintatico("esperava uma quebra de linha entre instruções", self._atual().posicao)
            self._pular_linhas()
        return declaracoes

    def _instrucao(self) -> object:
        token = self._atual()
        if token.tipo != "IDENTIFICADOR":
            raise ErroSintatico("esperava uma instrução em português", token.posicao)
        palavra = str(token.valor)

        if self._espiar_token(1).tipo == "IGUAL":
            self._avancar()
            self._avancar()
            return Atribuir(palavra, self._expressao())

        if palavra in {"mostrar", "exibir"}:
            self._avancar()
            valores: list[object] = []
            if self._atual().tipo not in {"NOVA_LINHA", "FIM"}:
                valores.append(self._expressao())
                while self._corresponde("VIRGULA"):
                    valores.append(self._expressao())
            return Mostrar(valores)
        if palavra == "definir":
            return self._definir()
        if palavra == "se":
            return self._condicional()
        if palavra == "enquanto":
            return self._enquanto()
        if palavra == "para":
            return self._para_cada()
        if palavra == "função":
            return self._funcao()
        if palavra == "retornar":
            self._avancar()
            valor = None if self._atual().tipo in {"NOVA_LINHA", "FIM"} else self._expressao()
            return Retornar(valor)
        if palavra == "interromper":
            self._avancar()
            return Interromper()
        if palavra == "continuar":
            self._avancar()
            return Continuar()

        expressao = self._expressao()
        return ExpressaoInstrucao(expressao)

    def _definir(self) -> Definir:
        self._consumir_palavra("definir", "esperava 'definir'")
        nome = self._consumir_tipo("IDENTIFICADOR", "esperava o nome da variável")
        if self._corresponde_palavra("como"):
            pass
        elif self._corresponde("IGUAL"):
            pass
        else:
            raise ErroSintatico("use 'como' ou '=' para atribuir um valor", self._atual().posicao)
        return Definir(str(nome.valor), self._expressao())

    def _condicional(self) -> Condicional:
        self._consumir_palavra("se", "esperava 'se'")
        condicao = self._expressao()
        self._consumir_palavra("então", "esperava 'então' depois da condição")
        self._nova_linha_obrigatoria()
        verdadeiro = self._bloco({"senão", "FIM"})
        falso: list[object] = []

        if self._atual().tipo == "IDENTIFICADOR" and self._atual().valor == "senão":
            self._avancar()
            if self._atual().tipo == "IDENTIFICADOR" and self._atual().valor == "se":
                falso.append(self._condicional())
                return Condicional(condicao, verdadeiro, falso)
            self._nova_linha_obrigatoria()
            falso = self._bloco({"FIM"})

        self._consumir_palavra("fim", "esperava 'fim' para encerrar o bloco 'se'")
        return Condicional(condicao, verdadeiro, falso)

    def _enquanto(self) -> Enquanto:
        self._consumir_palavra("enquanto", "esperava 'enquanto'")
        condicao = self._expressao()
        self._consumir_palavra("faça", "esperava 'faça' depois da condição")
        self._nova_linha_obrigatoria()
        corpo = self._bloco({"FIM"})
        self._consumir_palavra("fim", "esperava 'fim' para encerrar o laço")
        return Enquanto(condicao, corpo)

    def _para_cada(self) -> ParaCada:
        self._consumir_palavra("para", "esperava 'para'")
        self._consumir_palavra("cada", "esperava 'cada' depois de 'para'")
        nome = self._consumir_tipo("IDENTIFICADOR", "esperava o nome do item")
        self._consumir_palavra("em", "esperava 'em' antes da coleção")
        iteravel = self._expressao()
        self._consumir_palavra("faça", "esperava 'faça' depois da coleção")
        self._nova_linha_obrigatoria()
        corpo = self._bloco({"FIM"})
        self._consumir_palavra("fim", "esperava 'fim' para encerrar o laço")
        return ParaCada(str(nome.valor), iteravel, corpo)

    def _funcao(self) -> FuncaoDeclaracao:
        self._consumir_palavra("função", "esperava 'função'")
        nome = self._consumir_tipo("IDENTIFICADOR", "esperava o nome da função")
        self._consumir_tipo("ABRE_PARENTESE", "esperava '(' depois do nome da função")
        parametros: list[str] = []
        if self._atual().tipo != "FECHA_PARENTESE":
            while True:
                parametro = self._consumir_tipo("IDENTIFICADOR", "esperava o nome de um parâmetro")
                if parametro.valor in parametros:
                    raise ErroSintatico(f"parâmetro repetido: {parametro.valor}", parametro.posicao)
                parametros.append(str(parametro.valor))
                if not self._corresponde("VIRGULA"):
                    break
        self._consumir_tipo("FECHA_PARENTESE", "esperava ')' depois dos parâmetros")
        self._consumir_palavra("faça", "esperava 'faça' antes do corpo da função")
        self._nova_linha_obrigatoria()
        corpo = self._bloco({"FIM"})
        self._consumir_palavra("fim", "esperava 'fim' para encerrar a função")
        return FuncaoDeclaracao(str(nome.valor), parametros, corpo)

    def _expressao(self, precedencia_minima: int = 1) -> object:
        esquerda = self._unaria()
        esquerda = self._posfixa(esquerda)

        while True:
            operador_info = self._operador_binario()
            if operador_info is None:
                break
            operador, precedencia, quantidade = operador_info
            if precedencia < precedencia_minima:
                break
            for _ in range(quantidade):
                self._avancar()
            direita = self._expressao(precedencia + (0 if operador == "**" else 1))
            esquerda = Binaria(esquerda, operador, direita)
        return esquerda

    def _unaria(self) -> object:
        if self._corresponde("MENOS"):
            return Unaria("-", self._expressao(6))
        if self._atual().tipo == "IDENTIFICADOR" and self._atual().valor == "não":
            self._avancar()
            return Unaria("não", self._expressao(3))
        return self._primaria()

    def _primaria(self) -> object:
        token = self._atual()
        if self._corresponde("NUMERO"):
            return Literal(token.valor)
        if self._corresponde("TEXTO"):
            return Literal(token.valor)
        if token.tipo == "IDENTIFICADOR":
            self._avancar()
            palavra = str(token.valor)
            if palavra in {"verdadeiro", "falso", "nulo"}:
                return Literal({"verdadeiro": True, "falso": False, "nulo": None}[palavra])
            return Variavel(palavra)
        if self._corresponde("ABRE_PARENTESE"):
            expressao = self._expressao()
            self._consumir_tipo("FECHA_PARENTESE", "esperava ')' depois da expressão")
            return expressao
        if self._corresponde("ABRE_COLCHETE"):
            elementos: list[object] = []
            if self._atual().tipo != "FECHA_COLCHETE":
                while True:
                    elementos.append(self._expressao())
                    if not self._corresponde("VIRGULA"):
                        break
            self._consumir_tipo("FECHA_COLCHETE", "esperava ']' depois dos elementos")
            return ListaLiteral(elementos)
        raise ErroSintatico("esperava um valor, variável ou expressão", token.posicao)

    def _posfixa(self, expressao: object) -> object:
        while True:
            if self._corresponde("ABRE_PARENTESE"):
                argumentos: list[object] = []
                if self._atual().tipo != "FECHA_PARENTESE":
                    while True:
                        argumentos.append(self._expressao())
                        if not self._corresponde("VIRGULA"):
                            break
                self._consumir_tipo("FECHA_PARENTESE", "esperava ')' depois dos argumentos")
                expressao = Chamada(expressao, argumentos)
                continue
            if self._corresponde("ABRE_COLCHETE"):
                indice = self._expressao()
                self._consumir_tipo("FECHA_COLCHETE", "esperava ']' depois do índice")
                expressao = Indice(expressao, indice)
                continue
            break
        return expressao

    def _operador_binario(self) -> tuple[str, int, int] | None:
        token = self._atual()
        simbolos = {
            "MAIS": ("+", 4), "MENOS": ("-", 4), "VEZES": ("*", 5),
            "DIVIDIR": ("/", 5), "DIVISAO_INTEIRA": ("//", 5), "RESTO": ("%", 5),
            "POTENCIA": ("**", 6), "IGUAL_IGUAL": ("==", 3),
            "DIFERENTE": ("!=", 3), "MENOR": ("<", 3), "MENOR_IGUAL": ("<=", 3),
            "MAIOR": (">", 3), "MAIOR_IGUAL": (">=", 3),
        }
        if token.tipo in simbolos:
            operador, prec = simbolos[token.tipo]
            return operador, prec, 1
        if token.tipo != "IDENTIFICADOR":
            return None
        palavra = str(token.valor)
        if palavra in {"e", "ou"}:
            return palavra, self.PRECEDENCIA[palavra], 1
        if palavra in {"igual", "diferente"}:
            seguinte = self._espiar_token(1)
            conectivo = "a" if palavra == "igual" else "de"
            quantidade = 2 if seguinte.tipo == "IDENTIFICADOR" and seguinte.valor == conectivo else 1
            return ("==" if palavra == "igual" else "!="), 3, quantidade
        if palavra in {"maior", "menor"}:
            segundo = self._espiar_token(1)
            terceiro = self._espiar_token(2)
            quarto = self._espiar_token(3)
            base = ">" if palavra == "maior" else "<"
            if segundo.tipo == "IDENTIFICADOR" and segundo.valor == "ou" and terceiro.tipo == "IDENTIFICADOR" and terceiro.valor == "igual":
                quantidade = 3
                if quarto.tipo == "IDENTIFICADOR" and quarto.valor in {"a", "que"}:
                    quantidade = 4
                return base + "=", 3, quantidade
            quantidade = 1
            if segundo.tipo == "IDENTIFICADOR" and segundo.valor == "que":
                quantidade = 2
            return base, 3, quantidade
        return None

    def _eh_terminador(self, terminadores: set[str]) -> bool:
        token = self._atual()
        return token.tipo in terminadores or (
            token.tipo == "IDENTIFICADOR"
            and (token.valor in terminadores or ("FIM" in terminadores and token.valor == "fim"))
        )

    def _atual(self) -> Token:
        return self.tokens[self.indice]

    def _espiar_token(self, distancia: int) -> Token:
        alvo = min(self.indice + distancia, len(self.tokens) - 1)
        return self.tokens[alvo]

    def _avancar(self) -> Token:
        token = self._atual()
        if token.tipo != "FIM":
            self.indice += 1
        return token

    def _corresponde(self, tipo: str) -> bool:
        if self._atual().tipo == tipo:
            self._avancar()
            return True
        return False

    def _corresponde_palavra(self, palavra: str) -> bool:
        if self._atual().tipo == "IDENTIFICADOR" and self._atual().valor == palavra:
            self._avancar()
            return True
        return False

    def _consumir_tipo(self, tipo: str, mensagem: str) -> Token:
        if self._atual().tipo == tipo:
            return self._avancar()
        raise ErroSintatico(mensagem, self._atual().posicao)

    def _consumir_palavra(self, palavra: str, mensagem: str) -> Token:
        if self._atual().tipo == "IDENTIFICADOR" and self._atual().valor == palavra:
            return self._avancar()
        raise ErroSintatico(mensagem, self._atual().posicao)

    def _pular_linhas(self) -> None:
        while self._corresponde("NOVA_LINHA"):
            pass

    def _nova_linha_obrigatoria(self) -> None:
        if self._atual().tipo == "NOVA_LINHA":
            self._pular_linhas()
            return
        raise ErroSintatico("esperava uma quebra de linha depois desta instrução", self._atual().posicao)


def analisar_sintaxe(fonte: str) -> Programa:
    return AnalisadorSintatico(analisar_lexico(fonte)).analisar()
