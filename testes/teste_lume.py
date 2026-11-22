from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from lume.erros import ErroExecucao, ErroLexico, ErroSintatico
from lume.interpretador import Interpretador
from lume.lexer import analisar_lexico
from lume.parser import analisar_sintaxe


class TestesLume(unittest.TestCase):
    def executar(self, fonte: str, entradas: list[str] | None = None) -> list[str]:
        saidas: list[str] = []
        fila = iter(entradas or [])
        interpretador = Interpretador(saida=saidas.append, entrada=lambda _mensagem: next(fila))
        interpretador.executar(analisar_sintaxe(fonte))
        return saidas

    def test_ola_mundo(self) -> None:
        self.assertEqual(self.executar('mostrar "Olá, mundo!"'), ["Olá, mundo!"])

    def test_alias_exibir(self) -> None:
        self.assertEqual(self.executar('exibir "Olá"'), ["Olá"])

    def test_identificadores_com_acentos_e_sem_distincao_de_caixa(self) -> None:
        self.assertEqual(self.executar('DEFINIR ação como "feito"\nmostrar AÇÃO'), ["feito"])

    def test_variaveis_e_operacoes(self) -> None:
        fonte = "definir resultado como (2 + 3) * 4\nmostrar resultado"
        self.assertEqual(self.executar(fonte), ["20"])

    def test_precedencia_e_potencia(self) -> None:
        self.assertEqual(self.executar("mostrar 2 + 3 * 4\nmostrar 2 ** 3 ** 2"), ["14", "512"])

    def test_precedencia_de_negacao_e_sinal(self) -> None:
        self.assertEqual(self.executar("mostrar -2 ** 2\nmostrar não 2 maior que 1"), ["-4", "falso"])

    def test_comparacao_em_portugues(self) -> None:
        self.assertEqual(self.executar("mostrar 5 maior que 3\nmostrar 5 menor ou igual a 5"), ["verdadeiro", "verdadeiro"])

    def test_comparacao_entre_inteiro_e_decimal(self) -> None:
        self.assertEqual(self.executar("mostrar 2 < 2.5\nmostrar 3.0 == 3"), ["verdadeiro", "verdadeiro"])

    def test_condicional_e_senao(self) -> None:
        fonte = 'definir valor como 4\nse valor maior que 3 então\n mostrar "sim"\nsenão\n mostrar "não"\nfim'
        self.assertEqual(self.executar(fonte), ["sim"])

    def test_condicional_senao_se(self) -> None:
        fonte = 'definir valor como 2\nse valor igual a 1 então\n mostrar "um"\nsenão se valor igual a 2 então\n mostrar "dois"\nsenão\n mostrar "outro"\nfim'
        self.assertEqual(self.executar(fonte), ["dois"])

    def test_enquanto(self) -> None:
        fonte = "definir contador como 0\nenquanto contador menor que 3 faça\n definir contador como contador + 1\nfim\nmostrar contador"
        self.assertEqual(self.executar(fonte), ["3"])

    def test_para_cada_e_intervalo_inclusivo(self) -> None:
        fonte = "definir total como 0\npara cada numero em intervalo(1, 4) faça\n definir total como total + numero\nfim\nmostrar total"
        self.assertEqual(self.executar(fonte), ["10"])

    def test_funcao_com_retorno(self) -> None:
        fonte = "função dobro(numero) faça\n retornar numero * 2\nfim\nmostrar dobro(8)"
        self.assertEqual(self.executar(fonte), ["16"])

    def test_funcao_recursiva(self) -> None:
        fonte = "função fatorial(n) faça\n se n menor ou igual a 1 então\n  retornar 1\n fim\n retornar n * fatorial(n - 1)\nfim\nmostrar fatorial(5)"
        self.assertEqual(self.executar(fonte), ["120"])

    def test_listas(self) -> None:
        fonte = 'definir itens como ["a", "b"]\nmostrar itens\nmostrar comprimento(itens)'
        self.assertEqual(self.executar(fonte), ["[a, b]", "2"])

    def test_operadores_logicos_com_curto_circuito(self) -> None:
        self.assertEqual(self.executar("mostrar falso e (1 / 0 maior que 2)\nmostrar verdadeiro ou falso"), ["falso", "verdadeiro"])

    def test_entrada_de_dados(self) -> None:
        self.assertEqual(self.executar('definir nome como perguntar("Nome: ")\nmostrar "Olá", nome', ["Lia"]), ["Olá Lia"])

    def test_biblioteca_de_tipos(self) -> None:
        self.assertEqual(self.executar('mostrar tipo(10)\nmostrar numero("2,5")\nmostrar maiusculas("lume")'), ["inteiro", "2.5", "LUME"])

    def test_divisao_por_zero(self) -> None:
        with self.assertRaisesRegex(ErroExecucao, "dividir por zero"):
            self.executar("mostrar 10 / 0")

    def test_nome_nao_definido(self) -> None:
        with self.assertRaisesRegex(ErroExecucao, "não definido"):
            self.executar("mostrar desconhecido")

    def test_quantidade_de_argumentos(self) -> None:
        with self.assertRaisesRegex(ErroExecucao, "espera 1 argumento"):
            self.executar("mostrar comprimento()")

    def test_limite_de_execucao(self) -> None:
        interpretador = Interpretador(saida=lambda _texto: None, limite_passos=20)
        with self.assertRaisesRegex(ErroExecucao, "limite"):
            interpretador.executar(analisar_sintaxe("enquanto verdadeiro faça\n mostrar 1\nfim"))

    def test_interromper(self) -> None:
        fonte = "definir n como 0\nenquanto verdadeiro faça\n definir n como n + 1\n interromper\nfim\nmostrar n"
        self.assertEqual(self.executar(fonte), ["1"])

    def test_continuar(self) -> None:
        fonte = "definir total como 0\npara cada n em intervalo(1, 4) faça\n se n igual a 2 então\n  continuar\n fim\n definir total como total + n\nfim\nmostrar total"
        self.assertEqual(self.executar(fonte), ["8"])

    def test_controle_de_laco_nao_escapa_de_funcao(self) -> None:
        fonte = "função parar() faça\n interromper\nfim\nenquanto verdadeiro faça\n parar()\nfim"
        with self.assertRaisesRegex(ErroExecucao, "só pode ser usado dentro de um laço"):
            self.executar(fonte)

    def test_variavel_local_nao_altera_fechamento(self) -> None:
        fonte = 'definir nome como "global"\nfunção trocar() faça\n definir nome como "local"\n mostrar nome\nfim\ntrocar()\nmostrar nome'
        self.assertEqual(self.executar(fonte), ["local", "global"])

    def test_numero_nao_finito_e_rejeitado(self) -> None:
        with self.assertRaisesRegex(ErroExecucao, "finito"):
            self.executar('mostrar numero("NaN")')

    def test_caractere_invalido(self) -> None:
        with self.assertRaises(ErroLexico):
            analisar_lexico("mostrar @")

    def test_texto_sem_fechamento(self) -> None:
        with self.assertRaises(ErroLexico):
            analisar_lexico('mostrar "aberto')

    def test_bloco_sem_fim(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar_sintaxe("se verdadeiro então\n mostrar 1\n")

    def test_retornar_fora_de_funcao(self) -> None:
        with self.assertRaisesRegex(ErroExecucao, "só pode ser usado"):
            self.executar("retornar 1")

    def test_virgulas_no_mostrar(self) -> None:
        self.assertEqual(self.executar('mostrar "a", 2, verdadeiro'), ["a 2 verdadeiro"])


    def test_acesso_por_indice_em_lista_e_texto(self) -> None:
        fonte = 'definir itens como ["a", "b", "c"]\nmostrar itens[0]\nmostrar itens[-1]\nmostrar "Lume"[1]'
        self.assertEqual(self.executar(fonte), ["a", "c", "u"])

    def test_indice_fora_dos_limites(self) -> None:
        with self.assertRaisesRegex(ErroExecucao, "fora dos limites"):
            self.executar("mostrar [1, 2][4]")

    def test_indice_precisa_ser_inteiro(self) -> None:
        with self.assertRaisesRegex(ErroExecucao, "inteiro"):
            self.executar('mostrar ["a"][0.5]')

    def test_funcoes_de_mutacao_de_lista(self) -> None:
        fonte = 'definir itens como ["b", "c"]\nadicionar(itens, "d")\ninserir(itens, 0, "a")\nmostrar itens\nmostrar remover(itens, -1)\nmostrar itens'
        self.assertEqual(self.executar(fonte), ["[a, b, c, d]", "d", "[a, b, c]"])

    def test_funcoes_de_colecao(self) -> None:
        fonte = 'mostrar contem(["a", "b"], "b")\nmostrar ordenar([3, 1, 2])\nmostrar inverter("lume")\nmostrar juntar(["a", "b"], "-")'
        self.assertEqual(self.executar(fonte), ["verdadeiro", "[1, 2, 3]", "emul", "a-b"])

    def test_adicionar_respeita_limite_de_lista(self) -> None:
        interpretador = Interpretador(saida=lambda _texto: None)
        interpretador.LIMITE_COLECAO = 1
        with self.assertRaisesRegex(ErroExecucao, "limite"):
            interpretador.executar(analisar_sintaxe('definir itens como [1]\nadicionar(itens, 2)'))

    def test_atribuicao_atualiza_variavel_existente(self) -> None:
        fonte = "definir contador como 1\ncontador = contador + 1\nmostrar contador"
        self.assertEqual(self.executar(fonte), ["2"])

    def test_atribuicao_dentro_de_condicional_e_laco(self) -> None:
        fonte = "definir total como 0\nse verdadeiro então\n total = 5\nfim\npara cada n em intervalo(1, 2) faça\n total = total + n\nfim\nmostrar total"
        self.assertEqual(self.executar(fonte), ["8"])

    def test_atribuicao_dentro_de_funcao_altera_variavel_externa(self) -> None:
        fonte = "definir valor como 1\nfunção atualizar() faça\n valor = 9\nfim\natualizar()\nmostrar valor"
        self.assertEqual(self.executar(fonte), ["9"])

    def test_atribuicao_de_nome_inexistente_falha(self) -> None:
        with self.assertRaisesRegex(ErroExecucao, "nome não definido"):
            self.executar("novo = 3")

    def test_atribuicao_por_indice(self) -> None:
        fonte = "definir itens como [1, 2, 3]\nitens[1] = 9\nmostrar itens"
        self.assertEqual(self.executar(fonte), ["[1, 9, 3]"])

    def test_atribuicao_por_indice_invalido(self) -> None:
        with self.assertRaisesRegex(ErroExecucao, "fora dos limites"):
            self.executar("definir itens como [1]\nitens[4] = 9")

    def test_atribuicao_por_indice_em_texto_e_rejeitada(self) -> None:
        with self.assertRaisesRegex(ErroExecucao, "só é permitida em listas"):
            self.executar('definir texto como "lume"\ntexto[0] = "L"')

    def test_tratamento_estruturado_de_erro(self) -> None:
        fonte = 'tente\n lance "falha controlada"\ncapture erro\n mostrar erro\nfim'
        self.assertEqual(self.executar(fonte), ["Erro de execução: falha controlada"])

    def test_finalmente_e_executado_apos_erro(self) -> None:
        fonte = 'tente\n lance "falha"\nfinalmente\n mostrar "finalizado"\nfim'
        with self.assertRaisesRegex(ErroExecucao, "falha"):
            self.executar(fonte)

    def test_finalmente_e_executado_apos_captura(self) -> None:
        fonte = 'tente\n lance "falha"\ncapture erro\n mostrar "capturado"\nfinalmente\n mostrar "finalizado"\nfim'
        self.assertEqual(self.executar(fonte), ["capturado", "finalizado"])

    def test_importa_modulo_local(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            Path(diretorio, "apoio.lume").write_text(
                'definir taxa como 7\n', encoding="utf-8"
            )
            saidas: list[str] = []
            interpretador = Interpretador(saida=saidas.append, diretorio_raiz=diretorio)
            interpretador.executar(analisar_sintaxe(
                'importar "apoio.lume"\nmostrar taxa'
            ))
            self.assertEqual(saidas, ["7"])

    def test_importacao_detecta_ciclo(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            Path(diretorio, "a.lume").write_text('importar "b.lume"\n', encoding="utf-8")
            Path(diretorio, "b.lume").write_text('importar "a.lume"\n', encoding="utf-8")
            interpretador = Interpretador(saida=lambda _texto: None, diretorio_raiz=diretorio)
            with self.assertRaisesRegex(ErroExecucao, "ciclo de importação"):
                interpretador.executar(analisar_sintaxe('importar "a.lume"'))

    def test_importacao_rejeita_travessia_de_diretorio(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            interpretador = Interpretador(saida=lambda _texto: None, diretorio_raiz=diretorio)
            with self.assertRaisesRegex(ErroExecucao, "dentro do diretório"):
                interpretador.executar(analisar_sintaxe('importar "../fora.lume"'))

    def test_biblioteca_de_arquivos_limitada_ao_projeto(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            saidas: list[str] = []
            interpretador = Interpretador(saida=saidas.append, diretorio_raiz=diretorio)
            interpretador.executar(analisar_sintaxe(
                'escrever_arquivo("dados.txt", "Olá")\n'
                'mostrar ler_arquivo("dados.txt")\n'
                'anexar_arquivo("dados.txt", "!")\n'
                'mostrar existe_arquivo("dados.txt")\n'
                'mostrar ler_arquivo("dados.txt")'
            ))
            self.assertEqual(saidas, ["Olá", "verdadeiro", "Olá!"])

    def test_escrita_rejeita_travessia_de_diretorio(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            interpretador = Interpretador(saida=lambda _texto: None, diretorio_raiz=diretorio)
            with self.assertRaisesRegex(ErroExecucao, "dentro do diretório"):
                interpretador.executar(analisar_sintaxe(
                    'escrever_arquivo("../fora.txt", "proibido")'
                ))

if __name__ == "__main__":
    unittest.main()
