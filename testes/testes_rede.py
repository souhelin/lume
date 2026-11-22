"""Testes para permissões e conectividade opcional."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from lume.erros import ErroExecucao
from lume.permissoes import PermissoesRede
from lume.rede import ClienteRede


class TestesPermissoesRede(unittest.TestCase):
    def test_rede_negada_por_padrao(self):
        permissoes = PermissoesRede()
        with self.assertRaisesRegex(ErroExecucao, "bloqueado"):
            permissoes.autorizar_url("https://exemplo.com/dados")

    def test_autorizacao_exata_de_host(self):
        permissoes = PermissoesRede(["exemplo.com"])
        self.assertEqual(permissoes.autorizar_url("https://exemplo.com/a"), "exemplo.com")
        with self.assertRaises(ErroExecucao):
            permissoes.autorizar_url("https://sub.exemplo.com/a")

    def test_rejeita_esquema_e_credenciais(self):
        permissoes = PermissoesRede(["exemplo.com"])
        for url in ("file:///etc/passwd", "ftp://exemplo.com/a", "https://usuario@exemplo.com"):
            with self.subTest(url=url), self.assertRaises(ErroExecucao):
                permissoes.autorizar_url(url)

    def test_revogar_permissao(self):
        permissoes = PermissoesRede(["exemplo.com"])
        permissoes.revogar_host("exemplo.com")
        with self.assertRaises(ErroExecucao):
            permissoes.autorizar_url("https://exemplo.com")

    def test_requisicao_nao_inicia_sem_permissao(self):
        cliente = ClienteRede(PermissoesRede())
        with patch.object(cliente, "_opener") as opener:
            with self.assertRaises(ErroExecucao):
                cliente.requisitar("https://exemplo.com")
            opener.open.assert_not_called()

    def test_limites_de_configuracao(self):
        with self.assertRaises(ValueError):
            ClienteRede(PermissoesRede(), timeout=100)


if __name__ == "__main__":
    unittest.main()
