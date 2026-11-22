from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lume.cli import criar_parser_argumentos, executar_arquivo
from lume import FonteLexical, Lexicon


class TesteCLIComLexicon(unittest.TestCase):
    def test_parser_aceita_caminho_do_banco_lexical(self):
        opcoes = criar_parser_argumentos().parse_args([
            "--lexicon", "dados/lexicon.sqlite3", "programa.lume",
        ])
        self.assertEqual(opcoes.lexicon, "dados/lexicon.sqlite3")
        self.assertEqual(opcoes.arquivo, "programa.lume")

    def test_execucao_semantica_injeta_banco_lexical(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            banco = raiz / "lexicon.sqlite3"
            fonte = raiz / "programa.lume"
            fonte.write_text("mostre \\"ok\\"\\n", encoding="utf-8")
            with Lexicon(banco) as lexicon:
                lexicon.registrar_fonte(
                    FonteLexical(
                        "teste", "Fonte de teste", "MIT", "1",
                        "https://example.org", "Crédito",
                    ),
                    verificada=True,
                )

            with patch("lume.cli.InterpretadorSemantico") as fachada:
                fachada.return_value.verificar.return_value = None
                codigo = executar_arquivo(
                    str(fonte), verificar=True, modo_semantico=True,
                    caminho_lexico=banco,
                )
                self.assertEqual(codigo, 0)
                interpretador_recebido = fachada.call_args.args[0]
                self.assertIsNotNone(interpretador_recebido.lexicon)
                self.assertEqual(interpretador_recebido.lexicon.caminho, str(banco))
                self.assertEqual(interpretador_recebido.lexicon.integridade(), ("ok",))
                interpretador_recebido.lexicon.fechar()

    def test_caminho_lexical_inexistente_retorna_erro_controlado(self):
        with tempfile.TemporaryDirectory() as pasta:
            fonte = Path(pasta) / "programa.lume"
            fonte.write_text('mostre "ok"\\n', encoding="utf-8")
            codigo = executar_arquivo(
                str(fonte), verificar=True, modo_semantico=True,
                caminho_lexico=Path(pasta) / "nao-existe" / "lexicon.sqlite3",
            )
            self.assertEqual(codigo, 2)


if __name__ == "__main__":
    unittest.main()
