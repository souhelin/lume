from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

from lume import (
    EntradaLexical, FonteLexical, Interpretador, InterpretadorSemantico,
    Lexicon, DesambiguadorContextual, importar_fserb_lexico,
    importar_fserb_conjugacoes, importar_openwordnet_tsv,
)


class TestesImportacaoEDesambiguacao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "lexicon.sqlite3"
        self.lexicon = Lexicon(self.db_path)
        self.addCleanup(self.lexicon.fechar)

    def test_importa_fserb_lexico_sem_inventar_classe(self):
        arquivo = self.root / "lexico"
        arquivo.write_text("casa\nárvore\ncasa\n", encoding="utf-8")
        resultado = importar_fserb_lexico(
            self.lexicon, arquivo, versao="fixture-1", confirmar_direitos=True
        )
        self.assertEqual(resultado.registros_lidos, 3)
        self.assertEqual(resultado.registros_importados, 2)
        self.assertEqual(self.lexicon.buscar("árvore")[0].entrada.classe_gramatical,
                         "não_classificada")

    def test_importa_conjugacoes_sem_fingir_que_conhece_o_lema(self):
        arquivo = self.root / "conjugacoes"
        arquivo.write_text("canto\ncantamos\ncantarei\n", encoding="utf-8")
        resultado = importar_fserb_conjugacoes(
            self.lexicon, arquivo, versao="fixture-1", confirmar_direitos=True
        )
        self.assertEqual(resultado.registros_importados, 3)
        self.assertEqual(
            self.lexicon.buscar("cantamos")[0].entrada.classe_gramatical,
            "forma_verbal_sem_lema",
        )

    def test_openwordnet_preserva_multiplos_synsets_para_mesma_palavra(self):
        arquivo = self.root / "wn-data-por.tab"
        arquivo.write_text(
            "# OpenWN-PT\\tpor\\turl\\n"
            "00000001-n\\tlemma\\tbanco\\n"
            "00000001-n\\tlemma\\tinstituição financeira\\n"
            "00000002-n\\tlemma\\tbanco\\n"
            "00000002-n\\tlemma\\tassento\\n",
            encoding="utf-8",
        )
        resultado = importar_openwordnet_tsv(
            self.lexicon, arquivo, versao="fixture-1", confirmar_direitos=True
        )
        self.assertEqual(resultado.sentidos_importados, 2)
        correspondencias = self.lexicon.buscar("banco")
        self.assertEqual(len(correspondencias), 1)
        sentidos = self.lexicon.sentidos(correspondencias[0].entrada.identificador)
        self.assertEqual(len(sentidos), 2)

    def test_desambiguacao_usa_pista_sintatica_e_preserva_duvida(self):
        fonte = FonteLexical(
            "local", "Fonte local", "MIT", "1", "https://example.org", "Crédito"
        )
        self.lexicon.registrar_fonte(fonte, verificada=True)
        self.lexicon.adicionar_entrada(EntradaLexical(
            "canto-n", "canto", "substantivo", None, "local", "MIT", "1"
        ))
        self.lexicon.adicionar_entrada(EntradaLexical(
            "canto-v", "canto", "verbo", None, "local", "MIT", "1"
        ))
        desambiguador = DesambiguadorContextual(self.lexicon)
        resultado = desambiguador.analisar("o canto")[0]
        self.assertFalse(resultado.ambiguo)
        self.assertEqual(resultado.selecionado.correspondencia.entrada.classe_gramatical,
                         "substantivo")
        sem_pista = desambiguador.analisar("canto")[0]
        self.assertTrue(sem_pista.ambiguo)
        self.assertIsNone(sem_pista.selecionado)

    def test_integracao_com_interpretador_semantico(self):
        fonte = FonteLexical(
            "integracao", "Fonte", "MIT", "1", "https://example.org", "Crédito"
        )
        self.lexicon.registrar_fonte(fonte, verificada=True)
        self.lexicon.adicionar_entrada(EntradaLexical(
            "rio", "rio", "substantivo", None, "integracao", "MIT", "1"
        ))
        interpretador = Interpretador(lexicon=self.lexicon)
        fachada = InterpretadorSemantico(interpretador)
        self.assertEqual(len(fachada.analisar_lexico("o rio")), 1)

    def test_migracao_de_esquema_v1_para_v2(self):
        self.lexicon.fechar()
        conexao = sqlite3.connect(self.db_path)
        conexao.execute("PRAGMA user_version = 1")
        conexao.close()
        migrado = Lexicon(self.db_path)
        try:
            self.assertEqual(
                migrado._db.execute("PRAGMA user_version").fetchone()[0], 2
            )
            self.assertEqual(migrado.estatisticas()["sentidos"], 0)
        finally:
            migrado.fechar()


class TesteGrandeBaseLexical(unittest.TestCase):
    def test_importacao_em_lote_de_dez_mil_entradas(self):
        with tempfile.TemporaryDirectory() as pasta:
            root = Path(pasta)
            arquivo = root / "lexico"
            arquivo.write_text(
                "".join(f"termo_{i:05d}\\n" for i in range(10_000)),
                encoding="utf-8",
            )
            with Lexicon(root / "base.sqlite3") as lexicon:
                resultado = importar_fserb_lexico(
                    lexicon, arquivo, versao="stress-1", confirmar_direitos=True
                )
                self.assertEqual(resultado.registros_importados, 10_000)
                self.assertEqual(len(lexicon.buscar("termo_09999")), 1)
                self.assertEqual(lexicon.integridade(), ("ok",))


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "extra updates não instalado")
class TestesAtualizacaoAssinada(unittest.TestCase):
    def _pacote(self, pasta: Path, chave, delta: bytes, manifesto: dict, *,
                corromper_assinatura: bool = False) -> Path:
        from cryptography.hazmat.primitives import serialization
        manifesto_bytes = json.dumps(
            manifesto, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        assinatura = chave.sign(manifesto_bytes)
        if corromper_assinatura:
            assinatura = b"X" * len(assinatura)
        pacote = pasta / "update.zip"
        with zipfile.ZipFile(pacote, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("manifest.json", manifesto_bytes)
            z.writestr("manifest.sig", base64.b64encode(assinatura))
            z.writestr("delta.jsonl", delta)
        return pacote

    def test_atualizacao_incremental_assinada_e_backup(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        from lume.lexical_update import aplicar_pacote_assinado

        with tempfile.TemporaryDirectory() as pasta:
            root = Path(pasta)
            db = root / "lexicon.sqlite3"
            with Lexicon(db) as lexicon:
                lexicon.registrar_fonte(
                    FonteLexical("base", "Base", "MIT", "1", "https://x", "Crédito"),
                    verificada=True,
                )
                lexicon.adicionar_entrada(EntradaLexical(
                    "antiga", "antiga", "adjetivo", None, "base", "MIT", "1"
                ))
            fonte = {
                "id": "fonte-v2", "name": "Fonte", "license": "MIT",
                "version": "2", "url": "https://example.org",
                "attribution": "Crédito",
            }
            delta = (
                json.dumps({
                    "op": "upsert", "source": "fonte-v2", "id": "nova",
                    "lemma": "nova", "pos": "adjetivo", "license": "MIT",
                    "version": "2",
                }) + "\\n"
            ).encode()
            manifesto = {
                "schema_version": 2, "delta_sha256": hashlib.sha256(delta).hexdigest(),
                "source": fonte,
            }
            chave = Ed25519PrivateKey.generate()
            pacote = self._pacote(root, chave, delta, manifesto)
            publica = chave.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            resultado = aplicar_pacote_assinado(db, pacote, publica)
            self.assertEqual(resultado.operacoes, 1)
            self.assertTrue(Path(resultado.backup).is_file())
            with Lexicon(db) as atualizado:
                self.assertEqual(len(atualizado.buscar("nova")), 1)

    def test_assinatura_invalida_nao_altera_banco_ativo(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        from lume.lexical_update import aplicar_pacote_assinado

        with tempfile.TemporaryDirectory() as pasta:
            root = Path(pasta)
            db = root / "lexicon.sqlite3"
            with Lexicon(db) as lexicon:
                lexicon.registrar_fonte(
                    FonteLexical("base", "Base", "MIT", "1", "https://x", "Crédito"),
                    verificada=True,
                )
                lexicon.adicionar_entrada(EntradaLexical(
                    "fixa", "fixa", "substantivo", None, "base", "MIT", "1"
                ))
            chave = Ed25519PrivateKey.generate()
            delta = b""
            fonte = {
                "id": "fonte-v2", "name": "Fonte", "license": "MIT",
                "version": "2", "url": "https://example.org", "attribution": "Crédito",
            }
            manifesto = {
                "schema_version": 2, "delta_sha256": hashlib.sha256(delta).hexdigest(),
                "source": fonte,
            }
            pacote = self._pacote(root, chave, delta, manifesto, corromper_assinatura=True)
            publica = chave.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            with self.assertRaisesRegex(ValueError, "assinatura"):
                aplicar_pacote_assinado(db, pacote, publica)
            with Lexicon(db) as original:
                self.assertEqual(len(original.buscar("fixa")), 1)


if __name__ == "__main__":
    unittest.main()
