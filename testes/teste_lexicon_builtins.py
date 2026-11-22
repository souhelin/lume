from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lume import EntradaLexical, ErroExecucao, FonteLexical, Interpretador, Lexicon


class TestesFuncoesLexicaisNativas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lexicon = Lexicon(Path(self.tmp.name) / "lexicon.sqlite3")
        self.addCleanup(self.lexicon.fechar)
        self.lexicon.registrar_fonte(
            FonteLexical(
                "teste", "Fonte de teste", "MIT", "1",
                "https://example.org", "Crédito",
            ),
            verificada=True,
        )
        self.lexicon.adicionar_entrada(EntradaLexical(
            "casa", "casa", "substantivo", "local de moradia",
            "teste", "MIT", "1",
        ))

    def test_consultar_lexico_disponivel_dentro_da_linguagem(self):
        interpretador = Interpretador(lexicon=self.lexicon)
        funcao = interpretador.ambiente.valores["consultar_lexico"]
        resultado = funcao.executar("casa")
        self.assertEqual(len(resultado), 1)
        self.assertIn("local de moradia", resultado[0])
        self.assertIn("fonte: teste", resultado[0])

    def test_analisar_lexico_disponivel_dentro_da_linguagem(self):
        interpretador = Interpretador(lexicon=self.lexicon)
        funcao = interpretador.ambiente.valores["analisar_lexico"]
        resultado = funcao.executar("a casa")
        self.assertEqual(len(resultado), 1)
        self.assertIn("casa", resultado[0])
        self.assertIn("local de moradia", resultado[0])

    def test_funcoes_lexicais_exigem_banco_carregado(self):
        interpretador = Interpretador()
        funcao = interpretador.ambiente.valores["consultar_lexico"]
        with self.assertRaisesRegex(ErroExecucao, "Lexicon não está carregado"):
            funcao.executar("casa")

    def test_funcoes_lexicais_validam_argumento(self):
        interpretador = Interpretador(lexicon=self.lexicon)
        funcao = interpretador.ambiente.valores["consultar_lexico"]
        with self.assertRaisesRegex(ErroExecucao, "exige um texto"):
            funcao.executar(123)


if __name__ == "__main__":
    unittest.main()
