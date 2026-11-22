"""Regressões da execução offline e da conectividade opcional."""

from __future__ import annotations

import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

from lume import Interpretador, InterpretadorSemantico, analisar_sintaxe
from lume.erros import ErroExecucao


class TestesOfflineFirst(unittest.TestCase):
    def test_importacao_e_inicio_nao_carregam_cliente_de_rede(self):
        codigo = "import sys; import lume; lume.Interpretador(); assert \"lume.rede\" not in sys.modules"
        resultado = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)

    def test_programa_tradicional_executa_sem_rede(self):
        saida = []
        interpretador = Interpretador(saida=saida.append)
        fonte = (
            "definir resultado como 0\n"
            "para cada numero em intervalo(1, 3) faça\n"
            "    resultado = resultado + numero\n"
            "fim\n"
            "se resultado == 6 então\n"
            "    mostrar resultado\n"
            "senão\n"
            "    mostrar 0\n"
            "fim\n"
        )
        interpretador.executar(analisar_sintaxe(fonte))
        self.assertEqual(saida, ["6"])
        self.assertIsNone(interpretador._cliente_rede)

    def test_validador_semantico_reconhece_funcoes_online_sem_executa_las(self):
        semantico = InterpretadorSemantico(Interpretador())
        resultado = semantico.verificar('mostrar http_obter("https://api.exemplo.com/status")\n')
        self.assertIsNotNone(resultado)

    def test_programa_semantico_executa_sem_rede(self):
        saida = []
        interpretador = Interpretador(saida=saida.append)
        semantico = InterpretadorSemantico(interpretador)
        semantico.executar("crie uma variável chamada idade com valor 18\nmostre idade\n")
        self.assertEqual(saida, ["18"])
        self.assertIsNone(interpretador._cliente_rede)

    def test_operacoes_locais_de_arquivo_continuam_disponiveis(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = []
            interpretador = Interpretador(saida=saida.append, diretorio_raiz=pasta)
            interpretador.executar(analisar_sintaxe(
                'escrever_arquivo("local.txt", "conteudo")\nmostrar ler_arquivo("local.txt")\n'
            ))
            self.assertEqual(saida, ["conteudo"])
            self.assertEqual((Path(pasta) / "local.txt").read_text(encoding="utf-8"), "conteudo")

    def test_rede_bloqueada_por_padrao_sem_iniciar_cliente(self):
        interpretador = Interpretador()
        with self.assertRaisesRegex(ErroExecucao, "bloqueado"):
            interpretador._http_obter("https://exemplo.com")
        self.assertIsNone(interpretador._cliente_rede)

    def test_chamada_de_rede_na_linguagem_e_bloqueada_sem_permissao(self):
        interpretador = Interpretador()
        programa = analisar_sintaxe('mostrar http_obter("https://exemplo.com")\n')
        with self.assertRaisesRegex(ErroExecucao, "bloqueado"):
            interpretador.executar(programa)
        self.assertIsNone(interpretador._cliente_rede)

    def test_permissao_nao_autoriza_outro_host(self):
        interpretador = Interpretador(hosts_rede_permitidos=["exemplo.com"])
        with self.assertRaisesRegex(ErroExecucao, "bloqueado"):
            interpretador._http_obter("https://outro.exemplo")
        self.assertIsNone(interpretador._cliente_rede)

    def test_permissoes_podem_ser_revogadas(self):
        interpretador = Interpretador(hosts_rede_permitidos=["exemplo.com"])
        interpretador.permissoes_rede.revogar_host("exemplo.com")
        with self.assertRaises(ErroExecucao):
            interpretador._http_obter("https://exemplo.com")
        self.assertIsNone(interpretador._cliente_rede)


if __name__ == "__main__":
    unittest.main()
