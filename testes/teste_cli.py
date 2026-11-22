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

    def arquivo_temporario(self, diretorio: str, nome: str, fonte: str) -> Path:
        caminho = Path(diretorio, nome)
        caminho.write_text(fonte, encoding="utf-8")
        return caminho

    def test_versao(self) -> None:
        resultado = self.executar_cli("--versao")
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("0.3.0", resultado.stdout)

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
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo = self.arquivo_temporario(
                diretorio, "principal.lume",
                "crie uma variável chamada idade com valor 18\nmostre idade\n",
            )
            resultado = self.executar_cli(str(arquivo))
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stdout.strip(), "18")

    def test_verificar_semantica_sem_executar(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo = self.arquivo_temporario(diretorio, "principal.lume", 'mostre "válido"\n')
            resultado = self.executar_cli("--semantico", "--verificar", str(arquivo))
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("Semântica válida", resultado.stdout)

    def test_modo_semantico_rejeita_referencia_inexistente(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo = self.arquivo_temporario(
                diretorio, "principal.lume", "mostre nome_que_nao_existe\n"
            )
            resultado = self.executar_cli("--semantico", "--verificar", str(arquivo))
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("não definido", resultado.stderr)

    def test_cli_importa_modulo_relativo_ao_programa(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            raiz = Path(diretorio)
            (raiz / "apoio.lume").write_text(
                'definir mensagem como "módulo"\n', encoding="utf-8"
            )
            principal = raiz / "principal.lume"
            principal.write_text(
                'importar "apoio.lume"\nmostrar mensagem\n', encoding="utf-8"
            )
            resultado = self.executar_cli(str(principal))
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stdout.strip(), "módulo")

    def test_cli_mostra_posicao_de_erro_de_execucao(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo = self.arquivo_temporario(
                diretorio, "principal.lume", 'mostrar "ok"\nmostrar 10 / 0\n'
            )
            resultado = self.executar_cli(str(arquivo))
        self.assertEqual(resultado.returncode, 1)
        self.assertIn(":2:1: Erro de execução:", resultado.stderr)
        self.assertIn("^", resultado.stderr)

    def test_cli_formata_arquivo_sem_gravar(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo = self.arquivo_temporario(
                diretorio, "principal.lume", 'se verdadeiro então\nmostrar "sim"\nfim\n'
            )
            resultado = self.executar_cli("--formatar", str(arquivo))
            original = arquivo.read_text(encoding="utf-8")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn('    mostrar "sim"', resultado.stdout)
        self.assertNotIn('    mostrar "sim"', original)

    def test_cli_formata_e_grava_arquivo(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo = self.arquivo_temporario(
                diretorio, "principal.lume", 'se verdadeiro então\nmostrar "sim"\nfim\n'
            )
            resultado = self.executar_cli("--formatar", "--gravar", str(arquivo))
            gravado = arquivo.read_text(encoding="utf-8")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn('    mostrar "sim"', gravado)


if __name__ == "__main__":
    unittest.main()
