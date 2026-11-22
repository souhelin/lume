from __future__ import annotations

import unittest

from lume.formatador import formatar_fonte


class TestesFormatador(unittest.TestCase):
    def test_normaliza_recuo_de_blocos(self) -> None:
        fonte = 'se verdadeiro então\nmostrar "sim"\nsenão\nmostrar "não"\nfim\n'
        esperado = 'se verdadeiro então\n    mostrar "sim"\nsenão\n    mostrar "não"\nfim\n'
        self.assertEqual(formatar_fonte(fonte), esperado)

    def test_normaliza_ramo_senao_se(self) -> None:
        fonte = 'se verdadeiro então\nmostrar "a"\nsenão se falso então\nmostrar "b"\nfim\n'
        esperado = 'se verdadeiro então\n    mostrar "a"\nsenão se falso então\n    mostrar "b"\nfim\n'
        self.assertEqual(formatar_fonte(fonte), esperado)

    def test_nao_altera_textos_entre_aspas(self) -> None:
        fonte = 'mostrar "  texto   preservado  "\n'
        self.assertEqual(formatar_fonte(fonte), fonte)

    def test_remove_espacos_externos_e_linhas_vazias_excedentes(self) -> None:
        fonte = '  mostrar "a"   \n\n\n  mostrar "b"  \n'
        self.assertEqual(formatar_fonte(fonte), 'mostrar "a"\n\nmostrar "b"\n')


if __name__ == "__main__":
    unittest.main()
