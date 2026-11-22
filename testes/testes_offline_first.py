"""Regressões da execução offline e da conectividade opcional."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lume import Interpretador, InterpretadorSemantico, analisar_sintaxe
from lume.erros import ErroExecucao


class TestesOfflineFirst(unittest.TestCase):
    def test_programa_tradicional_executa_sem_rede(self):
        saida = []
        interpretador = Interpretador(saida=saida.append)
        interpretador.executar(analisar_sintaxe("definir resultado como (20 + 22)\nmostrar resultado\n"))
        self.assertEqual(saida, ["42"])
        self.assertIsNone(interpretador._cliente_rede)

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
