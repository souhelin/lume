"""Front-end semântico determinístico para instruções em português."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata
from typing import Any

from .erros import ErroAmbiguidade, ErroExecucao, ErroLume, ErroSemantico, Posicao
from .lexer import analisar_lexico
from .nos import (
    Atribuir, AtribuirIndice, Tentar, Lancar, Importar, Binaria, Chamada, Condicional, Continuar, Definir,
    ExpressaoInstrucao, FuncaoDeclaracao, Indice, Interromper, Enquanto,
    ListaLiteral, Literal, Mostrar, ParaCada, Programa, Retornar, Unaria,
    Variavel,
)
from .parser import analisar_sintaxe
from .representacao import (
    ExpressaoIR, InstrucaoIR, ProgramaIR, expressao_ir_para_no,
    programa_ir_para_ast, programa_para_ir,
)
from .vocabulario import DICIONARIO_PADRAO, DicionarioSemantico, normalizar_termo


IDENTIFICADOR = r"[^\W\d]\w*|_[\w]+"
FUNCOES_NATIVAS: dict[str, tuple[int, int | None]] = {
    "comprimento": (1, 1), "texto": (1, 1), "numero": (1, 1),
    "inteiro": (1, 1), "decimal": (1, 1), "tipo": (1, 1),
    "perguntar": (0, 1), "intervalo": (2, 3), "somar": (1, 1),
    "minimo": (1, 1), "maximo": (1, 1), "arredondar": (1, 2),
    "maiusculas": (1, 1), "minusculas": (1, 1), "adicionar": (2, 2),
    "inserir": (3, 3), "remover": (2, 2), "contem": (2, 2),
    "ler_arquivo": (1, 1), "escrever_arquivo": (2, 2),
    "anexar_arquivo": (2, 2), "existe_arquivo": (1, 1),
    "ordenar": (1, 1), "inverter": (1, 1), "juntar": (2, 2),
}
TIPOS_RETORNO_NATIVAS: dict[str, type | None] = {
    "comprimento": int, "texto": str, "tipo": str, "perguntar": str,
    "inteiro": int, "decimal": float, "contem": bool,
    "adicionar": int, "inserir": int, "ordenar": list, "juntar": str,
    "intervalo": list, "minimo": None, "maximo": None,
    "ler_arquivo": str, "escrever_arquivo": type(None),
    "anexar_arquivo": type(None), "existe_arquivo": bool,
}


@dataclass(slots=True)
class ContextoSemantico:
    variaveis: set[str] = field(default_factory=set)
    funcoes: dict[str, int] = field(default_factory=dict)
    tipos: dict[str, type | None] = field(default_factory=dict)
    ultima_variavel: str | None = None

    def copiar(self) -> "ContextoSemantico":
        return ContextoSemantico(
            set(self.variaveis), dict(self.funcoes), dict(self.tipos),
            self.ultima_variavel
        )


@dataclass(frozen=True, slots=True)
class ResultadoCompilacao:
    programa: ProgramaIR
    fonte_normalizada: str
    contexto_resultante: ContextoSemantico


def detectar_sintaxe_semantica(fonte: str) -> bool:
    """Detecta formas naturais novas sem alterar programas tradicionais."""
    inicios = (
        "crie", "criar", "cria", "declare", "declarar", "declara",
        "mostre", "mostra", "exiba", "exibe", "apresente", "apresenta",
        "defina", "atribua", "atribui", "atualize", "atualiza", "some", "somar",
        "subtraia", "subtrai", "multiplique", "multiplica", "divida",
        "divide", "compare", "compara", "repita", "repete", "adicione",
        "adiciona", "remova", "remove", "retorne", "devolva", "tente", "lance",
    )
    for linha in fonte.splitlines():
        texto = normalizar_termo(linha).lstrip()
        if any(re.match(r"^" + re.escape(verbo) + r"(?:\s|$)", texto) for verbo in inicios):
            return True
        if re.search(r"\b(?:for|é|seja)\s+(?:maior|menor|igual|diferente)\b", texto):
            return True
        if re.fullmatch(
            r"(?:caso\s+contr[aá]rio|fim\s+da\s+(?:repeti[cç][aã]o|fun[cç][aã]o))",
            texto
        ):
            return True
    return False


class TradutorSemantico:
    """Reconhece modelos explícitos e converte-os para a gramática canônica."""

    def __init__(self, dicionario: DicionarioSemantico | None = None) -> None:
        self.dicionario = dicionario or DICIONARIO_PADRAO
        self._contador_repeticoes = 0
        self._variaveis_declaradas_na_fonte: set[str] = set()

    def _termos(self, intencao: str) -> str:
        termos = self.dicionario.termos_para(intencao)
        if not termos:
            return r"(?!)"
        termos = sorted(termos, key=len, reverse=True)
        return r"(?:" + "|".join(re.escape(t) for t in termos) + r")"

    @staticmethod
    def _limpar_expressao(expressao: str) -> str:
        """Remove artigos e descritores apenas quando não apagam identificadores."""
        texto = expressao.strip()
        texto = re.sub(
            r"^(?:o\s+)?nome\s+da\s+vari[aá]vel\s+", "", texto,
            flags=re.IGNORECASE
        )
        texto = re.sub(
            r"^(?:a\s+)?vari[aá]vel\s+", "", texto, flags=re.IGNORECASE
        )
        texto = re.sub(
            r"^(?:o\s+)?valor\s+de\s+", "", texto, flags=re.IGNORECASE
        )
        texto = re.sub(
            r"^(?:o\s+)?n[uú]mero\s+de\s+", "", texto, flags=re.IGNORECASE
        )
        texto = re.sub(
            r"^(?:(?:o|um|uma)\s+)?valor\s+(?=[+-]?\d|['\"\[]|verdadeiro\b|falso\b|nulo\b)",
            "", texto, flags=re.IGNORECASE
        )
        texto = re.sub(
            r"^(?:(?:o|um|uma)\s+)?n[uú]mero\s+(?=[+-]?\d)",
            "", texto, flags=re.IGNORECASE
        )
        texto = re.sub(
            r"^(?:o|a|os|as|um|uma)\s+"
            r"(?=(?:nome|valor|n[uú]mero|vari[aá]vel|lista|índice|"
            r"[úu]ltimo|primeiro|resultado|texto|conte[uú]do)\b)",
            "", texto, flags=re.IGNORECASE
        )
        texto = re.sub(
            r"\b(?:for|é|seja)\s+(?=(?:maior|menor|igual|diferente)\b)",
            "", texto, flags=re.IGNORECASE
        )
        texto = re.sub(
            r"\b(?:da|do)\s+vari[aá]vel\s+", "", texto, flags=re.IGNORECASE
        )
        return texto.strip()

    @staticmethod
    def _normalizar_pontuacao_final(linha: str) -> str:
        """Aceita pontuação terminal fora de textos entre aspas."""
        sem_espacos = linha.rstrip()
        if not sem_espacos:
            return linha
        aspas: str | None = None
        escapado = False
        for caractere in sem_espacos:
            if aspas is not None:
                if escapado:
                    escapado = False
                elif caractere == "\\":
                    escapado = True
                elif caractere == aspas:
                    aspas = None
            elif caractere in {"'", '"'}:
                aspas = caractere
            elif caractere == "#":
                break
        if aspas is None:
            final = sem_espacos
            while final and final[-1] in ".;!?":
                final = final[:-1].rstrip()
            return final + linha[len(sem_espacos):]
        return linha

    def traduzir(self, fonte: str, contexto: ContextoSemantico) -> str:
        fonte = "\n".join(
            self._normalizar_pontuacao_final(linha)
            for linha in fonte.splitlines()
        )
        self._variaveis_declaradas_na_fonte = set()
        analisar_lexico(fonte)
        saida: list[str] = []
        for numero_linha, original in enumerate(fonte.splitlines(), start=1):
            linha = original.strip()
            if not linha or linha.startswith("#"):
                saida.append(original)
                continue
            try:
                traduzida = self._traduzir_linha(linha, contexto)
            except ErroAmbiguidade as erro:
                raise ErroAmbiguidade(
                    f"linha {numero_linha}: {erro.mensagem}"
                ) from erro
            except ErroSemantico as erro:
                raise ErroSemantico(
                    f"linha {numero_linha}: {erro.mensagem}"
                ) from erro
            saida.append(traduzida)
            self._atualizar_referencias_legadas(linha, contexto)
        return "\n".join(saida)

    def _atualizar_referencias_legadas(self, linha: str, contexto: ContextoSemantico) -> None:
        definir = re.match(rf"^definir\s+({IDENTIFICADOR})\b", linha, re.IGNORECASE)
        if definir:
            nome = definir.group(1).casefold()
            contexto.ultima_variavel = nome
            self._variaveis_declaradas_na_fonte.add(nome)

    def _traduzir_linha(self, linha: str, contexto: ContextoSemantico) -> str:
        texto = " ".join(unicodedata.normalize("NFC", linha).split())
        # Declaração tradicional da versão anterior, preservada sem reinterpretação.
        if re.match(r"^definir\s+\w+\s+(?:como|=)", texto, re.IGNORECASE):
            return linha

        reconhecidos_inicio = [
            entrada for inicio, _fim, entrada in self.dicionario.reconhecer(texto)
            if inicio == 0 and entrada.categoria == "verbo"
        ]
        intencoes_inicio = {entrada.intencao for entrada in reconhecidos_inicio}
        if len(intencoes_inicio) > 1:
            raise ErroAmbiguidade(
                f"a palavra inicial '{texto.split()[0]}' possui mais de uma intenção registrada"
            )

        # Fechamentos naturais de blocos.
        if re.fullmatch(r"fim\s+da\s+(?:repeti[cç][aã]o|fun[cç][aã]o)", texto, re.IGNORECASE):
            return "fim"
        if re.fullmatch(r"(?:caso\s+contr[aá]rio|do\s+contr[aá]rio)", texto, re.IGNORECASE):
            return "senão"
        if re.fullmatch(r"(?:pare|interrompa)\s+(?:a\s+)?repeti[cç][aã]o", texto, re.IGNORECASE):
            return "interromper"
        if re.fullmatch(r"(?:avance|continue)\s+(?:para\s+a\s+)?pr[oó]xima\s+(?:itera[cç][aã]o|repeti[cç][aã]o)", texto, re.IGNORECASE):
            return "continuar"

        # Definição de função declarada em linguagem natural.
        verbo_definir = "(?:" + self._termos("definir") + "|" + self._termos("declarar_variavel") + ")"
        padrao_funcao = re.fullmatch(
            rf"{verbo_definir}\s+(?:(?:uma|a)\s+)?função\s+(?:chamada\s+)?(?P<nome>{IDENTIFICADOR})"
            rf"(?:\s+com\s+par[aâ]metros?\s+(?P<parametros>.+))?",
            texto, re.IGNORECASE
        )
        if padrao_funcao:
            nome = padrao_funcao.group("nome")
            parametros = padrao_funcao.group("parametros") or ""
            parametros = self._limpar_expressao(parametros)
            parametros = re.sub(r"\s+e\s+", ", ", parametros)
            return f"função {nome}({parametros}) faça"

        # Declaração de variável: as duas formulações documentadas são equivalentes.
        verbos_criar = self._termos("declarar_variavel")
        padrao_declarar = re.fullmatch(
            rf"{verbos_criar}\s+(?:uma\s+)?vari[aá]vel\s+"
            rf"(?:chamada\s+)?(?P<nome>{IDENTIFICADOR})\s+"
            rf"(?:com\s+(?:o\s+)?valor|e\s+atribua\s+a\s+ela\s+"
            rf"(?:o\s+)?(?:valor|n[uú]mero))\s+(?P<valor>.+)",
            texto, re.IGNORECASE
        )
        if padrao_declarar:
            nome = padrao_declarar.group("nome").casefold()
            valor = self._limpar_expressao(padrao_declarar.group("valor"))
            self._variaveis_declaradas_na_fonte.add(nome)
            contexto.ultima_variavel = nome
            return f"definir {nome} como {valor}"

        # Atualização com alvo explícito ou referência pronominal.
        verbos_atribuir = self._termos("atribuir")
        padrao_atualizar = re.fullmatch(
            rf"{verbos_atribuir}\s+(?:a\s+)?vari[aá]vel\s+(?P<nome>{IDENTIFICADOR})"
            rf"\s+com\s+(?:o\s+)?valor\s+(?P<valor>.+)",
            texto, re.IGNORECASE
        )
        if padrao_atualizar:
            nome = padrao_atualizar.group("nome").casefold()
            valor = self._limpar_expressao(padrao_atualizar.group("valor"))
            contexto.ultima_variavel = nome
            return f"{nome} = {valor}"

        padrao_atribuir = re.fullmatch(
            rf"{verbos_atribuir}\s+(?P<valor>.+?)\s+(?:a|à|para)\s+"
            rf"(?:(?:vari[aá]vel)\s+)?(?P<nome>{IDENTIFICADOR}|ela|ele)",
            texto, re.IGNORECASE
        )
        if padrao_atribuir:
            nome = padrao_atribuir.group("nome").casefold()
            if nome in {"ela", "ele"}:
                nome = contexto.ultima_variavel or ""
                if not nome:
                    raise ErroSemantico(
                        "a referência 'ela/ele' não tem uma variável anterior; "
                        "informe explicitamente o nome do destino"
                    )
            valor = self._limpar_expressao(padrao_atribuir.group("valor"))
            contexto.ultima_variavel = nome
            return f"{nome} = {valor}"

        # Saída: mostre, exiba e apresente são equivalentes.
        verbos_exibir = self._termos("exibir")
        padrao_exibir = re.fullmatch(rf"{verbos_exibir}\s+(?P<valor>.+)", texto, re.IGNORECASE)
        if padrao_exibir:
            valor = self._limpar_expressao(padrao_exibir.group("valor"))
            return f"mostrar {valor}"

        # Operações matemáticas expressas por verbos.
        for intencao, separador, operador, inversa in (
            ("somar", " e ", "+", False),
            ("multiplicar", " por ", "*", False),
            ("subtrair", " de ", "-", True),
            ("dividir", " por ", "/", False),
        ):
            verbos = self._termos(intencao)
            correspondencia = re.fullmatch(rf"{verbos}\s+(?P<operandos>.+)", texto, re.IGNORECASE)
            if not correspondencia:
                continue
            operandos = correspondencia.group("operandos")
            destino = re.fullmatch(
                rf"(?P<expr>.+?)\s+e\s+(?:guarde|armazene)\s+em\s+(?P<nome>{IDENTIFICADOR})",
                operandos, re.IGNORECASE
            )
            nome_destino = destino.group("nome").casefold() if destino else None
            if destino:
                operandos = destino.group("expr")
            partes = re.fullmatch(rf"(?P<a>.+?){re.escape(separador)}(?P<b>.+)", operandos)
            if not partes:
                raise ErroSemantico(
                    f"instrução de {intencao} incompleta; informe os dois operandos "
                    f"separados por '{separador.strip()}'"
                )
            a = self._limpar_expressao(partes.group("a"))
            b = self._limpar_expressao(partes.group("b"))
            expressao = f"({b} {operador} {a})" if inversa else f"({a} {operador} {b})"
            if nome_destino:
                if (nome_destino in contexto.variaveis
                        or nome_destino in self._variaveis_declaradas_na_fonte):
                    contexto.ultima_variavel = nome_destino
                    return f"{nome_destino} = {expressao}"
                self._variaveis_declaradas_na_fonte.add(nome_destino)
                contexto.ultima_variavel = nome_destino
                return f"definir {nome_destino} como {expressao}"
            return f"mostrar {expressao}"

        # Comparação requer que o operador esteja escrito.
        verbo_comparar = self._termos("comparar")
        comparar = re.fullmatch(rf"{verbo_comparar}\s+(?P<resto>.+)", texto, re.IGNORECASE)
        if comparar:
            resto = comparar.group("resto")
            operacoes = (
                ("maior ou igual a", ">="), ("menor ou igual a", "<="),
                ("maior que", ">"), ("menor que", "<"),
                ("igual a", "=="), ("diferente de", "!="),
            )
            # Forma explícita: compare A com B usando maior que.
            forma_com = re.fullmatch(
                r"(?P<a>.+?)\s+com\s+(?P<b>.+?)\s+usando\s+"
                r"(?P<op>maior\s+ou\s+igual\s+a|menor\s+ou\s+igual\s+a|"
                r"maior\s+que|menor\s+que|igual\s+a|diferente\s+de)",
                resto, re.IGNORECASE
            )
            if forma_com:
                a = self._limpar_expressao(forma_com.group("a"))
                b = self._limpar_expressao(forma_com.group("b"))
                operador_texto = " ".join(forma_com.group("op").casefold().split())
                simbolo = dict(operacoes)[operador_texto]
                return f"mostrar ({a} {simbolo} {b})"
            for frase, simbolo in operacoes:
                partes = re.fullmatch(
                    rf"(?P<a>.+?)\s+{re.escape(frase)}\s+(?P<b>.+)",
                    resto, re.IGNORECASE
                )
                if partes:
                    a = self._limpar_expressao(partes.group("a"))
                    b = self._limpar_expressao(partes.group("b"))
                    return f"mostrar ({a} {simbolo} {b})"
            raise ErroAmbiguidade(
                "comparação ambígua: informe o operador, por exemplo "
                "'compare idade maior que 17' ou 'compare idade com 17 usando igual a'"
            )

        # Operações sobre coleções com verbo e destino explícitos.
        verbo_adicionar = self._termos("adicionar_elemento")
        adicionar = re.fullmatch(
            rf"{verbo_adicionar}\s+(?P<valor>.+?)\s+(?:à|a|na|em)\s+"
            rf"(?:lista\s+)?(?P<nome>{IDENTIFICADOR})",
            texto, re.IGNORECASE
        )
        if adicionar:
            nome = adicionar.group("nome").casefold()
            valor = self._limpar_expressao(adicionar.group("valor"))
            return f"adicionar({nome}, {valor})"

        verbo_remover = self._termos("remover_elemento")
        remover_ultimo = re.fullmatch(
            rf"{verbo_remover}\s+(?:o\s+)?(?:[úu]ltimo)\s+item\s+da\s+"
            rf"(?:lista\s+)?(?P<nome>{IDENTIFICADOR})",
            texto, re.IGNORECASE
        )
        if remover_ultimo:
            return f"remover({remover_ultimo.group('nome').casefold()}, -1)"
        remover_indice = re.fullmatch(
            rf"{verbo_remover}\s+(?:o\s+)?(?:[íi]ndice)\s+(?P<indice>.+?)\s+da\s+"
            rf"(?:lista\s+)?(?P<nome>{IDENTIFICADOR})",
            texto, re.IGNORECASE
        )
        if remover_indice:
            indice = self._limpar_expressao(remover_indice.group("indice"))
            nome = remover_indice.group("nome").casefold()
            return f"remover({nome}, {indice})"

        # Repetição contada. O contador é interno e não colide com nomes do usuário.
        verbo_repetir = self._termos("repetir")
        repetir = re.fullmatch(rf"{verbo_repetir}\s+(.+?)\s+vezes", texto, re.IGNORECASE)
        if repetir:
            quantidade = self._limpar_expressao(repetir.group(1))
            nome_contador = f"__lume_repeticao_{self._contador_repeticoes}"
            self._contador_repeticoes += 1
            return f"para cada {nome_contador} em intervalo(1, {quantidade}) faça"

        # Condições e laços tradicionais podem usar relações em linguagem mais natural.
        condicao = re.fullmatch(r"se\s+(.+?)\s+ent[aã]o", texto, re.IGNORECASE)
        if condicao:
            return f"se {self._limpar_expressao(condicao.group(1))} então"
        enquanto = re.fullmatch(r"enquanto\s+(.+?)\s+fa[çc]a", texto, re.IGNORECASE)
        if enquanto:
            return f"enquanto {self._limpar_expressao(enquanto.group(1))} faça"

        # Retorno escrito em português comum.
        verbos_retornar = self._termos("retornar")
        retornar = re.fullmatch(rf"{verbos_retornar}\s+(.+)", texto, re.IGNORECASE)
        if retornar:
            return f"retornar {self._limpar_expressao(retornar.group(1))}"

        # Se uma expressão começa com verbo conhecido mas não segue regra, não se
        # tenta adivinhar a intenção.
        reconhecidos = [
            entrada for inicio, _fim, entrada in self.dicionario.reconhecer(texto)
            if inicio == 0 and entrada.categoria == "verbo"
        ]
        intencoes = {entrada.intencao for entrada in reconhecidos}
        if len(intencoes) > 1:
            raise ErroAmbiguidade(
                f"a expressão inicial '{texto.split()[0]}' possui mais de uma intenção; "
                "reescreva a instrução de forma explícita"
            )
        if intencoes:
            verbo = texto.split()[0]
            raise ErroSemantico(
                f"instrução iniciada por '{verbo}' incompleta ou fora da gramática conhecida; "
                "consulte o dicionário semântico e os exemplos"
            )

        # Se duas palavras começam a linha e a primeira não é um comando legado,
        # não transforme silenciosamente a frase desconhecida em expressão.
        primeiro = re.match(r"^([^\W\d]\w*)\s+(?=[^\W\d_])", texto, re.UNICODE)
        comandos_legados = {
            "mostrar", "exibir", "definir", "se", "senão", "enquanto",
            "para", "função", "retornar", "interromper", "continuar", "fim",
            "tente", "capture", "finalmente", "lance", "importar",
        }
        if primeiro and primeiro.group(1).casefold() not in comandos_legados:
            palavra = primeiro.group(1)
            raise ErroSemantico(
                f"palavra de instrução desconhecida: '{palavra}'; "
                "consulte o dicionário semântico ou use uma instrução reconhecida"
            )

        # Linhas da sintaxe estruturada anterior são preservadas sem alterações.
        return linha


class _Validador:
    def __init__(self, contexto: ContextoSemantico) -> None:
        self.contexto = contexto.copiar()
        self.funcoes = dict(FUNCOES_NATIVAS)
        self.funcoes.update({nome: (qtd, qtd) for nome, qtd in self.contexto.funcoes.items()})

    def validar(self, programa: ProgramaIR) -> ContextoSemantico:
        self._bloco(programa.instrucoes, self.contexto, em_funcao=False, nivel_lacos=0)
        return self.contexto

    def _bloco(
        self,
        instrucoes: tuple[InstrucaoIR, ...],
        contexto: ContextoSemantico,
        em_funcao: bool,
        nivel_lacos: int,
    ) -> None:
        for instrucao in instrucoes:
            try:
                self._validar_bloco((instrucao,), contexto, em_funcao, nivel_lacos)
            except ErroSemantico as erro:
                if erro.posicao is None:
                    erro.posicao = instrucao.posicao
                raise

    def _validar_bloco(
        self,
        instrucoes: tuple[InstrucaoIR, ...],
        contexto: ContextoSemantico,
        em_funcao: bool,
        nivel_lacos: int,
    ) -> None:
        for instrucao in instrucoes:
            op, args = instrucao.operacao, instrucao.argumentos
            if op == "importar_modulo":
                continue
            elif op == "declarar":
                nome, valor = args
                tipo = self._expressao(valor, contexto)
                contexto.variaveis.add(nome)
                contexto.tipos[nome] = tipo
                contexto.ultima_variavel = nome
            elif op == "atribuir":
                nome, valor = args
                if nome not in contexto.variaveis and nome not in contexto.funcoes:
                    raise ErroSemantico(
                        f"variável '{nome}' não foi declarada; declare-a antes de atribuir um valor"
                    )
                contexto.tipos[nome] = self._expressao(valor, contexto)
                contexto.ultima_variavel = nome
            elif op == "atribuir_indice":
                colecao = self._expressao(args[0], contexto)
                indice = self._expressao(args[1], contexto)
                self._expressao(args[2], contexto)
                if colecao is not None and colecao is not list:
                    raise ErroSemantico("atribuição por índice exige uma lista")
                if indice is not None and indice is not int:
                    raise ErroSemantico("o índice de atribuição precisa ser inteiro")
            elif op == "tentar":
                base = contexto.copiar()
                self._bloco(args[0].instrucoes, base, em_funcao, nivel_lacos)
                captura = contexto.copiar()
                if args[1]:
                    captura.variaveis.add(args[1])
                    captura.tipos[args[1]] = str
                self._bloco(args[2].instrucoes, captura, em_funcao, nivel_lacos)
                self._bloco(args[3].instrucoes, contexto.copiar(), em_funcao, nivel_lacos)
            elif op == "lancar":
                tipo = self._expressao(args[0], contexto)
                if tipo is not None and tipo is not str:
                    raise ErroSemantico("'lance' exige uma mensagem em texto")
            elif op == "exibir":
                for valor in args[0]:
                    self._expressao(valor, contexto)
            elif op == "avaliar":
                self._expressao(args[0], contexto)
            elif op == "condicional":
                self._expressao(args[0], contexto)
                base = contexto.copiar()
                ramo_verdadeiro = base.copiar()
                ramo_falso = base.copiar()
                self._bloco(args[1].instrucoes, ramo_verdadeiro, em_funcao, nivel_lacos)
                self._bloco(args[2].instrucoes, ramo_falso, em_funcao, nivel_lacos)
                # Um nome novo só é garantido após o condicional quando existe
                # nos dois caminhos possíveis.
                comuns = ramo_verdadeiro.variaveis & ramo_falso.variaveis
                for nome in comuns - base.variaveis:
                    contexto.variaveis.add(nome)
                    if ramo_verdadeiro.tipos.get(nome) == ramo_falso.tipos.get(nome):
                        contexto.tipos[nome] = ramo_verdadeiro.tipos.get(nome)
                    else:
                        contexto.tipos[nome] = None
            elif op == "enquanto":
                self._expressao(args[0], contexto)
                self._bloco(args[1].instrucoes, contexto.copiar(), em_funcao, nivel_lacos + 1)
            elif op == "para_cada":
                nome, iteravel, corpo = args
                tipo = self._expressao(iteravel, contexto)
                if tipo not in (None, list, str, tuple):
                    raise ErroSemantico("'para cada' exige uma lista ou um texto")
                local = contexto.copiar()
                local.variaveis.add(nome)
                local.tipos[nome] = None
                self._bloco(corpo.instrucoes, local, em_funcao, nivel_lacos + 1)
            elif op == "declarar_funcao":
                nome, parametros, corpo = args
                contexto.funcoes[nome] = len(parametros)
                self.funcoes[nome] = (len(parametros), len(parametros))
                local = contexto.copiar()
                local.variaveis.update(parametros)
                for parametro in parametros:
                    local.tipos[parametro] = None
                self._bloco(corpo.instrucoes, local, em_funcao=True, nivel_lacos=0)
            elif op == "retornar":
                if not em_funcao:
                    raise ErroSemantico("'retornar' só pode ser usado dentro de uma função")
                if args[0] is not None:
                    self._expressao(args[0], contexto)
            elif op == "interromper":
                if nivel_lacos == 0:
                    raise ErroSemantico("'interromper' só pode ser usado dentro de uma repetição")
            elif op == "continuar":
                if nivel_lacos == 0:
                    raise ErroSemantico("'continuar' só pode ser usado dentro de uma repetição")
            else:
                raise ErroSemantico(f"operação intermediária desconhecida: {op}")

    def _expressao(self, expressao: ExpressaoIR, contexto: ContextoSemantico) -> type | None:
        op, args = expressao.operacao, expressao.argumentos
        if op == "literal":
            valor = args[0]
            return type(valor) if valor is not None else type(None)
        if op == "referencia":
            nome = args[0]
            if nome not in contexto.variaveis and nome not in contexto.funcoes and nome not in FUNCOES_NATIVAS:
                raise ErroSemantico(
                    f"nome '{nome}' não definido; declare a variável antes de usá-la"
                )
            return contexto.tipos.get(nome)
        if op == "lista":
            for item in args[0]:
                self._expressao(item, contexto)
            return list
        if op == "unaria":
            operador, operando = args
            tipo = self._expressao(operando, contexto)
            if operador == "-" and tipo is not None and tipo not in (int, float):
                raise ErroSemantico("o sinal negativo exige um valor numérico")
            return bool if operador == "não" else tipo
        if op == "binaria":
            esquerda = self._expressao(args[0], contexto)
            direita = self._expressao(args[2], contexto)
            operador = args[1]
            numericos = (int, float)
            if operador in {"-", "*", "/", "//", "%", "**"}:
                if esquerda is not None and esquerda not in numericos:
                    raise ErroSemantico(f"o operador '{operador}' exige valores numéricos")
                if direita is not None and direita not in numericos:
                    raise ErroSemantico(f"o operador '{operador}' exige valores numéricos")
                return float if operador == "/" or float in (esquerda, direita) else int
            if operador == "+" and esquerda is not None and direita is not None:
                compatíveis = (
                    esquerda in numericos and direita in numericos
                ) or (esquerda is str and direita is str) or (esquerda is list and direita is list)
                if not compatíveis:
                    raise ErroSemantico("'+' exige dois números, dois textos ou duas listas")
                return float if float in (esquerda, direita) else esquerda
            if operador in {"<", "<=", ">", ">="} and esquerda is not None and direita is not None:
                compatíveis = (
                    esquerda in numericos and direita in numericos
                ) or (esquerda is str and direita is str)
                if not compatíveis:
                    raise ErroSemantico("a comparação ordenada exige dois números ou dois textos")
                return bool
            if operador in {"==", "!=", "<", "<=", ">", ">="}:
                return bool
            if operador in {"e", "ou"}:
                return bool
            return None
        if op == "indice":
            colecao = self._expressao(args[0], contexto)
            indice = self._expressao(args[1], contexto)
            if indice is not None and indice is not int:
                raise ErroSemantico("o índice de uma coleção precisa ser inteiro")
            if colecao is not None and colecao not in (list, tuple, str):
                raise ErroSemantico("o acesso por índice exige uma lista ou um texto")
            return None
        if op == "chamada":
            funcao, argumentos = args
            nome = funcao.argumentos[0] if funcao.operacao == "referencia" else None
            if nome is not None:
                aridade = self.funcoes.get(nome)
                if aridade is None and nome not in contexto.variaveis:
                    raise ErroSemantico(
                        f"função '{nome}' não definida; verifique o nome ou declare a função"
                    )
                if aridade is not None and not (aridade[0] <= len(argumentos)
                                                and (aridade[1] is None or len(argumentos) <= aridade[1])):
                    esperado = str(aridade[0]) if aridade[0] == aridade[1] else f"entre {aridade[0]} e {aridade[1] or 'vários'}"
                    raise ErroSemantico(
                        f"'{nome}' espera {esperado} argumento(s); recebeu {len(argumentos)}"
                    )
            else:
                self._expressao(funcao, contexto)
            for argumento in argumentos:
                self._expressao(argumento, contexto)
            return TIPOS_RETORNO_NATIVAS.get(nome) if nome else None
        raise ErroSemantico(f"expressão intermediária desconhecida: {op}")


class CompiladorSemantico:
    """Compila texto natural determinístico em IR validada."""

    def __init__(
        self,
        dicionario: DicionarioSemantico | None = None,
        contexto: ContextoSemantico | None = None,
    ) -> None:
        self.dicionario = dicionario or DICIONARIO_PADRAO
        self.contexto = contexto or ContextoSemantico()
        self.tradutor = TradutorSemantico(self.dicionario)

    def compilar(self, fonte: str) -> ResultadoCompilacao:
        contexto_traducao = self.contexto.copiar()
        fonte_normalizada = self.tradutor.traduzir(fonte, contexto_traducao)
        arvore = analisar_sintaxe(fonte_normalizada)
        representacao = programa_para_ir(arvore)
        validador = _Validador(contexto_traducao)
        contexto_resultante = validador.validar(representacao)
        return ResultadoCompilacao(representacao, fonte_normalizada, contexto_resultante)

    def confirmar(self, resultado: ResultadoCompilacao) -> None:
        self.contexto = resultado.contexto_resultante.copiar()


class InterpretadorSemantico:
    """Fachada de execução com contexto semântico persistente."""

    def __init__(self, interpretador: Any | None = None,
                 dicionario: DicionarioSemantico | None = None) -> None:
        if interpretador is None:
            from .interpretador import Interpretador
            interpretador = Interpretador()
        self.interpretador = interpretador
        self.compilador = CompiladorSemantico(dicionario=dicionario)

    def _sincronizar_contexto(self) -> None:
        """Reconcilia nomes com o ambiente real, inclusive após comandos tradicionais."""
        ambiente = getattr(self.interpretador, "ambiente", None)
        valores = getattr(ambiente, "valores", {})
        for nome, valor in valores.items():
            nome = str(nome).casefold()
            if nome in FUNCOES_NATIVAS:
                continue
            if hasattr(valor, "parametros"):
                self.compilador.contexto.funcoes[nome] = len(valor.parametros)
            else:
                self.compilador.contexto.variaveis.add(nome)
                self.compilador.contexto.tipos[nome] = type(valor)

    @staticmethod
    def _tem_importacao_aninhada(instrucao: object) -> bool:
        if isinstance(instrucao, Condicional):
            blocos = (instrucao.caminho_verdadeiro, instrucao.caminho_falso)
        elif isinstance(instrucao, (Enquanto, FuncaoDeclaracao)):
            blocos = (instrucao.corpo,)
        elif isinstance(instrucao, ParaCada):
            blocos = (instrucao.corpo,)
        elif isinstance(instrucao, Tentar):
            blocos = (instrucao.corpo, instrucao.captura, instrucao.finalmente)
        else:
            return False
        for bloco in blocos:
            for item in bloco:
                if isinstance(item, Importar) or InterpretadorSemantico._tem_importacao_aninhada(item):
                    return True
        return False

    def _validar_importacoes(
        self,
        programa: Programa,
        contexto: ContextoSemantico,
        carregando: set[object],
        carregados: set[object],
    ) -> ContextoSemantico:
        importacoes: list[Importar] = []
        iniciou_codigo = False
        for instrucao in programa.declaracoes:
            if isinstance(instrucao, Importar):
                if iniciou_codigo:
                    raise ErroSemantico(
                        "as importações devem aparecer no início do arquivo, antes das demais instruções",
                        getattr(instrucao, "posicao", None),
                    )
                importacoes.append(instrucao)
            else:
                iniciou_codigo = True
                if self._tem_importacao_aninhada(instrucao):
                    raise ErroSemantico(
                        "importe módulos no início do arquivo, fora de condições, laços ou funções",
                        getattr(instrucao, "posicao", None),
                    )
        resultado = contexto.copiar()
        for importacao in importacoes:
            resultado = self._validar_modulo(
                importacao.caminho, resultado, carregando, carregados
            )
        return resultado

    def _validar_modulo(
        self,
        caminho: str,
        contexto: ContextoSemantico,
        carregando: set[object],
        carregados: set[object],
    ) -> ContextoSemantico:
        try:
            arquivo = self.interpretador._resolver_caminho(caminho)
            if arquivo.suffix.casefold() != ".lume":
                raise ErroSemantico("módulos precisam usar a extensão .lume")
            if arquivo in carregados:
                return contexto
            if arquivo in carregando:
                raise ErroSemantico(f"ciclo de importação detectado no módulo '{caminho}'")
            if not arquivo.is_file():
                raise ErroSemantico(f"módulo não encontrado: '{caminho}'")
            fonte = self.interpretador._ler_arquivo(caminho)
        except ErroExecucao as erro:
            raise ErroSemantico(erro.mensagem, erro.posicao) from erro

        carregando.add(arquivo)
        try:
            try:
                contexto_modulo = contexto.copiar()
                tradutor = TradutorSemantico(self.compilador.dicionario)
                fonte_normalizada = tradutor.traduzir(fonte, contexto_modulo)
                arvore = analisar_sintaxe(fonte_normalizada)
                contexto_modulo = self._validar_importacoes(
                    arvore, contexto_modulo, carregando, carregados
                )
                representacao = programa_para_ir(arvore)
                contexto_resultante = _Validador(contexto_modulo).validar(representacao)
                carregados.add(arquivo)
                return contexto_resultante
            except ErroLume as erro:
                local = f"no módulo '{caminho}'"
                if erro.posicao is not None:
                    local += f" na linha {erro.posicao.linha}, coluna {erro.posicao.coluna}"
                raise ErroSemantico(f"{local}: {erro.mensagem}") from erro
        finally:
            carregando.discard(arquivo)

    def verificar(self, fonte: str) -> ResultadoCompilacao:
        self._sincronizar_contexto()
        contexto = self.compilador.contexto.copiar()
        carregando: set[object] = set()
        carregados: set[object] = set()

        # Pré-carrega símbolos dos imports iniciais para que o tradutor semântico
        # também consiga resolver referências contextuais a variáveis dos módulos.
        for linha in fonte.splitlines():
            texto = linha.strip()
            if not texto or texto.startswith("#"):
                continue
            importacao = re.fullmatch(r"""importar\s+["']([^"']+)["']""", texto, re.IGNORECASE)
            if not importacao:
                break
            contexto = self._validar_modulo(
                importacao.group(1), contexto, carregando, carregados
            )

        tradutor = TradutorSemantico(self.compilador.dicionario)
        fonte_normalizada = tradutor.traduzir(fonte, contexto)
        arvore = analisar_sintaxe(fonte_normalizada)
        contexto = self._validar_importacoes(arvore, contexto, carregando, carregados)
        representacao = programa_para_ir(arvore)
        contexto_resultante = _Validador(contexto).validar(representacao)
        return ResultadoCompilacao(representacao, fonte_normalizada, contexto_resultante)

    def executar(self, fonte: str) -> ProgramaIR:
        resultado = self.verificar(fonte)
        self.interpretador.executar(programa_ir_para_ast(resultado.programa))
        self.compilador.confirmar(resultado)
        return resultado.programa


def compilar_semantico(
    fonte: str,
    dicionario: DicionarioSemantico | None = None,
    contexto: ContextoSemantico | None = None,
) -> ResultadoCompilacao:
    return CompiladorSemantico(dicionario, contexto).compilar(fonte)
