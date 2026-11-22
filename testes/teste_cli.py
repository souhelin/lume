from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


class TestesCLI(unittest.TestCase):
    def executar_cli(self, *argumentos: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "lume", *argumentos],
            cwd=RAIZ,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_versao(self) -> None:
        resultado = self.executar_cli("--versao")
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("0.1.0", resultado.stdout)

    def test_verificar_arquivo(self) -> None:
        resultado = self.executar_cli("--verificar", "exemplos/ola.lume")
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("Sintaxe válida", resultado.stdout)

    def test_executar_arquivo(self) -> None:
        resultado = self.executar_cli("exemplos/ola.lume")
        self.assertEqual(resultado.returncode, 0)
        self.assertEqual(resultado.stdout.strip(), "Olá, mundo!")

    def test_arquivo_inexistente(self) -> None:
        resultado = self.executar_cli("arquivo-que-nao-existe.lume")
        self.assertEqual(resultado.returncode, 2)
        self.assertIn("não encontrado", resultado.stderr)

    def test_executar_instrucao_semantica_em_portugues(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".lume") as arquivo:
            arquivo.write(
                "crie uma variável chamada idade com valor 18\n"
                "mostre idade\n"
            )
            arquivo.flush()
            resultado = self.executar_cli(arquivo.name)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stdout.strip(), "18")

    def test_verificar_semantica_sem_executar(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".lume") as arquivo:
            arquivo.write('mostre "válido"\n')
            arquivo.flush()
            resultado = self.executar_cli("--semantico", "--verificar", arquivo.name)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("Semântica válida", resultado.stdout)

    def test_modo_semantico_rejeita_referencia_inexistente(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".lume") as arquivo:
            arquivo.write("mostre nome_que_nao_existe\n")
            arquivo.flush()
            resultado = self.executar_cli("--semantico", "--verificar", arquivo.name)
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("não definido", resultado.stderr)


if __name__ == "__main__":
    unittest.main()
