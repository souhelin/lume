"""Dicionário semântico extensível da Lume.

O dicionário descreve o vocabulário aceito; não executa código nem usa IA.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


def normalizar_termo(texto: str) -> str:
    """Normaliza Unicode, caixa e espaços sem remover acentos significativos."""
    return " ".join(unicodedata.normalize("NFC", texto).casefold().split())


@dataclass(frozen=True, slots=True)
class EntradaSemantica:
    expressao: str
    significado: str
    categoria: str
    intencao: str
    operacoes: tuple[str, ...] = ()
    relacoes: tuple[str, ...] = ()
    regras: tuple[str, ...] = ()
    ambiguidades: tuple[str, ...] = ()


class DicionarioSemantico:
    """Registro de termos e expressões associados a intenções da linguagem."""

    def __init__(self) -> None:
        self._entradas: dict[str, list[EntradaSemantica]] = {}

    def registrar(
        self,
        expressao: str,
        significado: str,
        categoria: str,
        intencao: str,
        operacoes: tuple[str, ...] = (),
        relacoes: tuple[str, ...] = (),
        regras: tuple[str, ...] = (),
        ambiguidades: tuple[str, ...] = (),
    ) -> EntradaSemantica:
        termo = normalizar_termo(expressao)
        if not termo:
            raise ValueError("a expressão do dicionário não pode ser vazia")
        if not intencao.strip():
            raise ValueError("a intenção semântica não pode ser vazia")
        entrada = EntradaSemantica(
            termo, significado, categoria, intencao,
            tuple(operacoes), tuple(relacoes), tuple(regras), tuple(ambiguidades)
        )
        existentes = self._entradas.setdefault(termo, [])
        if entrada not in existentes:
            existentes.append(entrada)
        return entrada

    def buscar(self, expressao: str) -> tuple[EntradaSemantica, ...]:
        return tuple(self._entradas.get(normalizar_termo(expressao), ()))

    def termos_para(self, intencao: str) -> tuple[str, ...]:
        return tuple(sorted(
            termo
            for termo, entradas in self._entradas.items()
            if any(entrada.intencao == intencao for entrada in entradas)
        ))

    def reconhecer(self, texto: str) -> list[tuple[int, int, EntradaSemantica]]:
        """Localiza termos conhecidos, priorizando expressões mais longas."""
        fonte = normalizar_termo(texto)
        encontrados: list[tuple[int, int, EntradaSemantica]] = []
        ocupados: list[tuple[int, int]] = []
        termos = sorted(self._entradas, key=len, reverse=True)
        for termo in termos:
            padrao = re.compile(r"(?<!\w)" + re.escape(termo) + r"(?!\w)")
            for ocorrencia in padrao.finditer(fonte):
                inicio, fim = ocorrencia.span()
                if any(inicio < fim_existente and fim > inicio_existente
                       for inicio_existente, fim_existente in ocupados):
                    continue
                for entrada in self._entradas[termo]:
                    encontrados.append((inicio, fim, entrada))
                ocupados.append((inicio, fim))
        encontrados.sort(key=lambda item: (item[0], item[1]))
        return encontrados

    def todas(self) -> tuple[EntradaSemantica, ...]:
        return tuple(
            entrada
            for termo in sorted(self._entradas)
            for entrada in self._entradas[termo]
        )


def criar_dicionario_padrao() -> DicionarioSemantico:
    dicionario = DicionarioSemantico()

    def grupo(
        termos: tuple[str, ...],
        significado: str,
        intencao: str,
        operacoes: tuple[str, ...],
        regras: tuple[str, ...] = (),
        relacoes: tuple[str, ...] = (),
        ambiguidades: tuple[str, ...] = (),
    ) -> None:
        for termo in termos:
            dicionario.registrar(
                termo, significado, "verbo", intencao,
                operacoes=operacoes, relacoes=relacoes,
                regras=regras, ambiguidades=ambiguidades,
            )

    grupo(
        ("crie", "criar", "cria", "declare", "declarar", "declara"),
        "Criar uma variável e associar um valor inicial.",
        "declarar_variavel", ("declarar", "avaliar_valor"),
        ("o nome deve ser um identificador válido", "o valor é avaliado antes da declaração"),
        ("variável", "nome", "valor"),
        ("criar e atribuir são operações distintas",)
    )
    grupo(
        ("mostre", "mostrar", "mostra", "exiba", "exibir", "exibe",
         "apresente", "apresentar", "apresenta"),
        "Apresentar um ou mais valores ao usuário.",
        "exibir", ("avaliar", "saída"),
        ("a expressão precisa estar completa",),
        ("valor", "variável", "texto"),
        ("não confundir exibição com declaração ou atribuição",)
    )
    grupo(
        ("atribua", "atribuir", "atribui", "atualize", "atualizar", "atualiza"),
        "Associar um novo valor a uma variável já existente.",
        "atribuir", ("avaliar_valor", "atualizar"),
        ("o destino deve existir no contexto",),
        ("variável", "valor", "contexto"),
        ("o pronome depende de uma referência anterior inequívoca",)
    )
    grupo(("some", "somar", "soma"), "Calcular a soma de dois valores.",
          "somar", ("adição",), ("os dois operandos devem ser compatíveis",), ("número", "valor"))
    grupo(("subtraia", "subtrair", "subtrai"), "Subtrair um valor de outro.",
          "subtrair", ("subtração",), relacoes=("número", "valor", "ordem dos operandos"))
    grupo(("multiplique", "multiplicar", "multiplica"), "Multiplicar dois valores.",
          "multiplicar", ("multiplicação",), relacoes=("número", "valor"))
    grupo(("divida", "dividir", "divide"), "Dividir um valor por outro.",
          "dividir", ("divisão",), ("o divisor não pode ser zero",), ("número", "valor", "divisor"))
    grupo(("compare", "comparar", "compara"), "Comparar dois valores.",
          "comparar", ("comparação",),
          ("o operador de comparação precisa ser informado",),
          ("valor", "operador", "maior que", "menor que"),
          ("duas expressões sem operador não definem uma comparação",))
    grupo(("repita", "repetir", "repete"), "Executar um bloco repetidamente.",
          "repetir", ("laço",), ("a quantidade de repetições deve ser explícita",),
          ("quantidade", "bloco", "fim"))
    grupo(("adicione", "adicionar", "adiciona"), "Adicionar um elemento a uma lista.",
          "adicionar_elemento", ("adicionar",), relacoes=("lista", "elemento", "valor"))
    grupo(("remova", "remover", "remove"), "Remover um elemento de uma lista.",
          "remover_elemento", ("remover",), relacoes=("lista", "elemento", "índice"))
    grupo(("retorne", "retornar", "devolva", "devolver"), "Devolver um valor de uma função.",
          "retornar", ("retorno",), relacoes=("função", "valor", "resultado"))
    grupo(("defina", "definir"), "Definir uma estrutura nomeada.",
          "definir", ("declarar",))

    substantivos = (
        ("variável", "Um nome associado a um valor.", "substantivo", "variavel", ("valor", "nome", "atribuição")),
        ("variavel", "Um nome associado a um valor.", "substantivo", "variavel", ("valor", "nome", "atribuição")),
        ("valor", "Conteúdo associado a uma expressão ou variável.", "substantivo", "valor", ("variável", "expressão", "operação")),
        ("número", "Valor numérico inteiro ou decimal.", "substantivo", "numero", ("valor", "adição", "comparação")),
        ("numero", "Valor numérico inteiro ou decimal.", "substantivo", "numero", ("valor", "adição", "comparação")),
        ("lista", "Coleção ordenada de elementos.", "substantivo", "lista", ("elemento", "índice", "adicionar", "remover")),
        ("nome", "Identificador de uma entidade.", "substantivo", "identificador", ("variável", "função", "referência")),
        ("função", "Estrutura nomeada que recebe parâmetros e pode retornar um valor.", "substantivo", "funcao", ("parâmetro", "retorno", "chamada")),
        ("parâmetro", "Nome que recebe um argumento em uma função.", "substantivo", "parametro", ("função", "argumento")),
        ("índice", "Posição numérica de um item em uma coleção.", "substantivo", "indice", ("lista", "elemento", "acesso")),
        ("coleção", "Conjunto ordenado de elementos.", "substantivo", "colecao", ("lista", "elemento", "índice")),
        ("vezes", "Unidade de quantidade de repetições.", "marcador", "quantidade", ("repetição", "bloco")),
        ("chamada", "Indica o nome de uma entidade.", "marcador", "nomeacao", ("função", "variável")),
    )
    for termo, significado, categoria, intencao, relacoes in substantivos:
        dicionario.registrar(
            termo, significado, categoria, intencao, relacoes=relacoes
        )

    comparadores = (
        ("maior que", "Relação de ordem crescente.", ">"),
        ("menor que", "Relação de ordem decrescente.", "<"),
        ("maior ou igual a", "Relação de ordem com igualdade.", ">="),
        ("menor ou igual a", "Relação de ordem com igualdade.", "<="),
        ("igual a", "Relação de igualdade.", "=="),
        ("diferente de", "Relação de diferença.", "!="),
    )
    for expressao, significado, operador in comparadores:
        dicionario.registrar(
            expressao, significado, "operador", "comparacao",
            operacoes=(operador,), relacoes=("comparar", "valor", "operando"),
            regras=("exige duas expressões",),
        )

    return dicionario


DICIONARIO_PADRAO = criar_dicionario_padrao()
