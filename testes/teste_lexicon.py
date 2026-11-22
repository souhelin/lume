from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lume import EntradaLexical, FonteLexical, Interpretador, Lexicon, normalizar_forma


class TestesLexicon(unittest.TestCase):
    def criar_banco(self, caminho: str = ":memory:") -> Lexicon:
        banco = Lexicon(caminho)
        banco.registrar_fonte(
            FonteLexical(
                "teste", "Fonte de teste", "MIT", "1.0",
                "https://example.org/dados", "Atribuição de teste",
            ),
            verificada=True,
        )
        return banco

    def entrada(
        self, identificador: str, lema: str, classe: str = "substantivo",
        definicao: str | None = None,
    ) -> EntradaLexical:
        return EntradaLexical(
            identificador, lema, classe, definicao, "teste", "MIT", "1.0"
        )

    def test_normalizacao_unicode_e_acentos(self):
        self.assertEqual(normalizar_forma("  ÁRVORE  "), "árvore")
        self.assertNotEqual(normalizar_forma("avó"), normalizar_forma("avo"))

    def test_busca_por_lema(self):
        banco = self.criar_banco()
        try:
            banco.adicionar_entrada(self.entrada("arvore-n", "árvore"))
            resultados = banco.buscar("ÁRVORE", incluir_flexoes=False)
            self.assertEqual(len(resultados), 1)
            self.assertEqual(resultados[0].entrada.lema, "árvore")
        finally:
            banco.fechar()

    def test_busca_por_flexao(self):
        banco = self.criar_banco()
        try:
            banco.adicionar_entrada(
                self.entrada("cantar-v", "cantar", "verbo"),
                formas=(("canto", "presente_1s"), ("cantávamos", "imperfeito_1p")),
            )
            resultado = banco.buscar("CANTÁVAMOS")
            self.assertEqual(len(resultado), 1)
            self.assertEqual(resultado[0].entrada.lema, "cantar")
            self.assertEqual(resultado[0].tipo_forma, "imperfeito_1p")
        finally:
            banco.fechar()

    def test_preserva_ambiguidades_e_classes(self):
        banco = self.criar_banco()
        try:
            banco.adicionar_entrada(self.entrada("canto-n", "canto", "substantivo"))
            banco.adicionar_entrada(self.entrada("cantar-v", "cantar", "verbo"),
                                    formas=(("canto", "presente_1s"),))
            resultados = banco.buscar("canto")
            self.assertEqual(len(resultados), 2)
            self.assertEqual({r.entrada.classe_gramatical for r in resultados},
                             {"substantivo", "verbo"})
        finally:
            banco.fechar()

    def test_fonte_precisa_estar_verificada(self):
        banco = Lexicon()
        try:
            banco.registrar_fonte(FonteLexical(
                "nao-verificada", "Fonte", "MIT", "1", "https://example.org", "Crédito"
            ))
            entrada = EntradaLexical("x", "exemplo", "substantivo", None,
                                     "nao-verificada", "MIT", "1")
            with self.assertRaisesRegex(ValueError, "não foi marcada"):
                banco.adicionar_entrada(entrada)
        finally:
            banco.fechar()

    def test_exige_procedencia_e_licenca_consistentes(self):
        banco = self.criar_banco()
        try:
            entrada = EntradaLexical("x", "exemplo", "substantivo", None,
                                     "teste", "CC-BY-4.0", "1.0")
            with self.assertRaisesRegex(ValueError, "divergem"):
                banco.adicionar_entrada(entrada)
        finally:
            banco.fechar()

    def test_nao_inventa_palavra_desconhecida(self):
        banco = self.criar_banco()
        try:
            self.assertEqual(banco.buscar("palavra-inexistente"), ())
        finally:
            banco.fechar()

    def test_relacoes_semanticas(self):
        banco = self.criar_banco()
        try:
            banco.adicionar_entrada(self.entrada("feliz", "feliz", definicao="Estado de alegria."))
            banco.adicionar_entrada(self.entrada("contente", "contente"))
            banco.adicionar_relacao("feliz", "contente", "sinonimo", "teste")
            self.assertEqual(banco.relacoes("feliz", "sinonimo")[0].lema, "contente")
        finally:
            banco.fechar()

    def test_persistencia_e_integridade_sqlite(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = str(Path(pasta) / "lexicon.sqlite3")
            banco = self.criar_banco(caminho)
            banco.adicionar_entrada(self.entrada("casa", "casa"))
            self.assertEqual(banco.integridade(), ("ok",))
            banco.fechar()

            reaberto = Lexicon(caminho)
            try:
                self.assertEqual(reaberto.buscar("casa")[0].entrada.lema, "casa")
                self.assertEqual(reaberto.estatisticas()["entradas"], 1)
            finally:
                reaberto.fechar()

    def test_interpretador_consulta_a_instancia_compartilhada(self):
        banco = self.criar_banco()
        try:
            banco.adicionar_entrada(self.entrada("rio", "rio"))
            interpretador = Interpretador(lexicon=banco)
            self.assertEqual(
                interpretador.consultar_lexico("RIO")[0].entrada.identificador,
                "rio",
            )
        finally:
            banco.fechar()

    def test_interpretador_sem_lexicon_nao_inventa_resultados(self):
        interpretador = Interpretador()
        self.assertEqual(interpretador.consultar_lexico("palavra"), ())

    def test_entrada_sem_fonte_e_rejeitada(self):
        banco = Lexicon()
        try:
            with self.assertRaisesRegex(ValueError, "fonte lexical"):
                banco.adicionar_entrada(EntradaLexical(
                    "x", "exemplo", "substantivo", None, "ausente", "MIT", "1"
                ))
        finally:
            banco.fechar()


if __name__ == "__main__":
    unittest.main()
