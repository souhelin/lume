from __future__ import annotations

import unittest

from lume.erros import ErroAmbiguidade, ErroSemantico
from lume.interpretador import Interpretador
from lume.semantica import (
    CompiladorSemantico,
    ContextoSemantico,
    InterpretadorSemantico,
    compilar_semantico,
)
from lume.vocabulario import criar_dicionario_padrao


class TestesDicionarioSemantico(unittest.TestCase):
    def test_dicionario_reconhece_sinonimos(self) -> None:
        dicionario = criar_dicionario_padrao()
        self.assertEqual(
            {entrada.intencao for entrada in dicionario.buscar("mostre")},
            {"exibir"},
        )
        self.assertEqual(
            {entrada.intencao for entrada in dicionario.buscar("apresente")},
            {"exibir"},
        )

    def test_dicionario_reconhece_expressao_completa(self) -> None:
        dicionario = criar_dicionario_padrao()
        encontradas = dicionario.reconhecer("adicione um valor à lista")
        self.assertTrue(any(entrada.intencao == "adicionar_elemento"
                            for _, _, entrada in encontradas))

    def test_dicionario_pode_ser_expandido(self) -> None:
        dicionario = criar_dicionario_padrao()
        dicionario.registrar(
            "revele", "Apresentar informação.", "verbo", "exibir",
            operacoes=("saída",),
        )
        self.assertEqual(dicionario.buscar("revele")[0].intencao, "exibir")

    def test_entradas_contem_relacoes_regras_e_operacoes(self) -> None:
        dicionario = criar_dicionario_padrao()
        entrada = dicionario.buscar("compare")[0]
        self.assertIn("comparação", entrada.operacoes)
        self.assertIn("operador", entrada.relacoes)
        self.assertTrue(entrada.regras)
        self.assertTrue(entrada.ambiguidades)


class TestesInterpretacaoSemantica(unittest.TestCase):
    def criar_interpretador(self) -> tuple[InterpretadorSemantico, list[str]]:
        saidas: list[str] = []
        base = Interpretador(saida=saidas.append, entrada=lambda _mensagem: "")
        return InterpretadorSemantico(base), saidas

    def test_exemplo_principal_cria_e_mostra_variavel(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "crie uma variável chamada idade com valor 18\n"
            "mostre idade"
        )
        self.assertEqual(saidas, ["18"])

    def test_formulacoes_equivalentes_produzem_mesma_operacao(self) -> None:
        resultados = []
        for declaracao in (
            "crie uma variável chamada idade com valor 18",
            "declare uma variável idade e atribua a ela o número 18",
        ):
            interpretador, saidas = self.criar_interpretador()
            interpretador.executar(declaracao + "\nmostre idade")
            resultados.append(saidas)
        self.assertEqual(resultados, [["18"], ["18"]])

    def test_sinonimos_de_saida_sao_equivalentes(self) -> None:
        saidas = []
        for verbo in ("mostre", "exiba", "apresente"):
            interpretador, destino = self.criar_interpretador()
            interpretador.executar(f'{verbo} "Lume"')
            saidas.append(destino)
        self.assertEqual(saidas, [["Lume"], ["Lume"], ["Lume"]])

    def test_preserva_caixa_em_textos(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar('mostre "Lume Português"')
        self.assertEqual(saidas, ["Lume Português"])

    def test_aceita_pontuacao_terminal_fora_de_textos(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar('mostre "Lume Português".')
        self.assertEqual(saidas, ["Lume Português"])

    def test_mistura_comandos_legados_e_instrucoes_naturais(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            'definir nome como "Lume"\n'
            "mostre nome"
        )
        self.assertEqual(saidas, ["Lume"])

    def test_operacoes_matematicas_em_portugues(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "some 2 e 3\n"
            "subtraia 5 de 10\n"
            "multiplique 3 por 4\n"
            "divida 20 por 5"
        )
        self.assertEqual(saidas, ["5", "5", "12", "4.0"])

    def test_operacao_matematica_pode_guardar_resultado(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "some 2 e 3 e guarde em total\n"
            "mostre total"
        )
        self.assertEqual(saidas, ["5"])

    def test_comparacao_explicitamente_estruturada(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "crie uma variável chamada idade com valor 18\n"
            "compare idade maior que 17\n"
            "compare idade com 18 usando igual a"
        )
        self.assertEqual(saidas, ["verdadeiro", "verdadeiro"])

    def test_comparacao_sem_operador_e_ambigua(self) -> None:
        compilador = CompiladorSemantico(contexto=ContextoSemantico(
            variaveis={"idade"}, tipos={"idade": int}
        ))
        with self.assertRaises(ErroAmbiguidade):
            compilador.compilar("compare idade com 18")

    def test_atribuicao_contextual_com_pronome(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "crie uma variável chamada idade com valor 18\n"
            "atribua o valor 19 a ela\n"
            "atribua o valor 20 à variável idade\n"
            "mostre idade"
        )
        self.assertEqual(saidas, ["20"])

    def test_repeticao_contada(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "crie uma variável chamada contador com valor 0\n"
            "repita 3 vezes\n"
            "  atribua contador + 1 a ela\n"
            "fim da repetição\n"
            "mostre contador"
        )
        self.assertEqual(saidas, ["3"])

    def test_condicional_com_conectivo_natural(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "crie uma variável chamada idade com valor 18\n"
            "se idade for maior que 17 então\n"
            '  apresente "maior"\n'
            "caso contrário\n"
            '  apresente "menor"\n'
            "fim"
        )
        self.assertEqual(saidas, ["maior"])

    def test_funcao_definida_em_portugues(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "defina uma função chamada dobro com parâmetros numero\n"
            "  retorne numero * 2\n"
            "fim da função\n"
            "mostre dobro(5)"
        )
        self.assertEqual(saidas, ["10"])

    def test_lista_pode_ser_manipulada_em_portugues(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "crie uma variável chamada itens com valor [1, 2]\n"
            "adicione 3 à lista itens\n"
            "remova o último item da lista itens\n"
            "mostre itens"
        )
        self.assertEqual(saidas, ["[1, 2]"])

    def test_vocabulario_customizado_e_usado_pelo_compilador(self) -> None:
        dicionario = criar_dicionario_padrao()
        dicionario.registrar("revele", "Exibir informação.", "verbo", "exibir")
        saidas: list[str] = []
        interpretador = InterpretadorSemantico(
            Interpretador(saida=saidas.append), dicionario
        )
        interpretador.executar('revele "extensível"')
        self.assertEqual(saidas, ["extensível"])

    def test_nome_desconhecido_e_detectado_antes_da_execucao(self) -> None:
        compilador = CompiladorSemantico()
        with self.assertRaisesRegex(ErroSemantico, "não definido"):
            compilador.compilar("mostre variavel_inexistente")

    def test_referencia_a_declaracao_futura_e_rejeitada(self) -> None:
        compilador = CompiladorSemantico()
        with self.assertRaisesRegex(ErroSemantico, "não definido"):
            compilador.compilar(
                "mostre idade\n"
                "crie uma variável chamada idade com valor 18"
            )

    def test_operacao_pode_atualizar_variavel_legada(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "definir total como 1\n"
            "some 2 e 3 e guarde em total\n"
            "mostre total"
        )
        self.assertEqual(saidas, ["5"])

    def test_ir_e_validador_suportam_atribuicao_por_indice(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            "crie uma variável chamada itens com valor [1, 2]\n"
            "itens[0] = 8\n"
            "mostre itens"
        )
        self.assertEqual(saidas, ["[8, 2]"])

    def test_ir_e_validador_suportam_tratamento_de_erros(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar(
            'tente\n lance "erro esperado"\ncapture falha\n'
            'mostre "capturado"\nfinalmente\nmostre "finalizado"\nfim'
        )
        self.assertEqual(saidas, ["capturado", "finalizado"])

    def test_atribuicao_a_nome_inexistente_e_rejeitada(self) -> None:
        compilador = CompiladorSemantico()
        with self.assertRaisesRegex(ErroSemantico, "não foi declarada"):
            compilador.compilar("atribua 4 à variável ausente")

    def test_operacao_com_tipos_incompativeis_e_rejeitada(self) -> None:
        compilador = CompiladorSemantico()
        with self.assertRaisesRegex(ErroSemantico, "dois números"):
            compilador.compilar(
                'crie uma variável chamada nome com valor "Lume"\n'
                "some nome e 1"
            )

    def test_chamada_nativa_com_arity_incorreta_e_rejeitada(self) -> None:
        compilador = CompiladorSemantico()
        with self.assertRaisesRegex(ErroSemantico, "espera 1 argumento"):
            compilador.compilar("mostre comprimento()")

    def test_instrucao_incompleta_nao_e_adivinhada(self) -> None:
        compilador = CompiladorSemantico()
        with self.assertRaisesRegex(ErroSemantico, "incompleta"):
            compilador.compilar("crie uma variável idade")

    def test_palavra_de_comando_desconhecida_e_identificada(self) -> None:
        compilador = CompiladorSemantico()
        with self.assertRaisesRegex(ErroSemantico, "palavra de instrução desconhecida"):
            compilador.compilar("mostraa idade")

    def test_termo_com_duas_intencoes_gera_ambiguidade(self) -> None:
        dicionario = criar_dicionario_padrao()
        dicionario.registrar("mostre", "Comparar.", "verbo", "comparar")
        compilador = CompiladorSemantico(dicionario)
        with self.assertRaises(ErroAmbiguidade):
            compilador.compilar('mostre "texto"')

    def test_ir_usa_operacoes_independentes_da_frase(self) -> None:
        resultado = compilar_semantico(
            'crie uma variável chamada nome com valor "Lume"\nmostre nome'
        )
        self.assertEqual(
            [instrucao.operacao for instrucao in resultado.programa.instrucoes],
            ["declarar", "exibir"],
        )
        serializado = resultado.programa.para_dicionario()
        self.assertEqual(serializado["tipo"], "programa")
        self.assertEqual(serializado["instrucoes"][1]["operacao"], "exibir")

    def test_estado_de_contexto_e_preservado_entre_chamadas(self) -> None:
        interpretador, saidas = self.criar_interpretador()
        interpretador.executar("crie uma variável chamada contador com valor 1")
        interpretador.executar("atribua 2 a ela")
        interpretador.executar("mostre contador")
        self.assertEqual(saidas, ["2"])


if __name__ == "__main__":
    unittest.main()
