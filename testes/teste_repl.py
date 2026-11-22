from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from lume.cli import iniciar_repl


class TestesREPL(unittest.TestCase):
    def executar_repl(self, entradas: list[str], modo_semantico: bool | None = False) -> tuple[str, str]:
        fila = iter(entradas)
        saida = io.StringIO()
        erros = io.StringIO()
        with patch("builtins.input", side_effect=lambda _prompt="": next(fila)):
            with redirect_stdout(saida), redirect_stderr(erros):
                iniciar_repl(modo_semantico)
        return saida.getvalue(), erros.getvalue()

    def test_repl_completa_bloco_multilinha(self) -> None:
        saida, erros = self.executar_repl([
            "se verdadeiro então",
            'mostrar "ok"',
            "fim",
            "sair",
        ])
        self.assertIn("ok", saida)
        self.assertEqual(erros, "")

    def test_repl_recupera_de_erro_lexico(self) -> None:
        saida, erros = self.executar_repl([
            "mostrar @",
            'mostrar "recuperado"',
            "sair",
        ])
        self.assertIn("recuperado", saida)
        self.assertIn("caractere não reconhecido", erros)

    def test_repl_completa_bloco_semantico_de_tratamento(self) -> None:
        saida, erros = self.executar_repl([
            "tente",
            'lance "falha"',
            "capture erro",
            'mostre "capturado"',
            "fim",
            "sair",
        ], modo_semantico=True)
        self.assertIn("capturado", saida)
        self.assertEqual(erros, "")


if __name__ == "__main__":
    unittest.main()
