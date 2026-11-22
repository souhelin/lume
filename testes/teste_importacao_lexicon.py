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
    importar_fserb_conjugacoes, importar_fserb_verbos, importar_fserb_icf,
    importar_openwordnet_tsv, importar_openwordnet_ttl,
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

    def test_importa_lista_de_verbos_e_pontuacao_icf(self):
        verbos = self.root / "verbos"
        icf = self.root / "icf"
        verbos.write_text("cantar\nser\n", encoding="utf-8")
        icf.write_text("cantar,5.23\nser,3.10\n", encoding="utf-8")
        importar_fserb_verbos(
            self.lexicon, verbos, versao="fixture-1", confirmar_direitos=True
        )
        resultado = importar_fserb_icf(
            self.lexicon, icf, versao="fixture-1", confirmar_direitos=True
        )
        self.assertEqual(resultado.registros_importados, 2)
        self.assertEqual(self.lexicon.buscar("cantar")[0].entrada.classe_gramatical, "verbo")
        self.assertEqual(self.lexicon.frequencia("cantar"), (5.23,))

    def test_openwordnet_preserva_multiplos_synsets_para_mesma_palavra(self):
        arquivo = self.root / "wn-data-por.tab"
        arquivo.write_text(
            "# OpenWN-PT\tpor\turl\n"
            "00000001-n\tlemma\tbanco\n"
            "00000001-n\tlemma\tinstituição financeira\n"
            "00000002-n\tlemma\tbanco\n"
            "00000002-n\tlemma\tassento\n",
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

    @unittest.skipUnless(importlib.util.find_spec("rdflib"), "extra rdf não instalado")
    def test_importa_turtle_com_glossas_e_relacoes(self):
        palavras = self.root / "words.ttl"
        synsets = self.root / "synsets.ttl"
        sentidos = self.root / "wordsenses.ttl"
        relacoes = self.root / "relations.ttl"
        prefixos = (
            "@prefix own-pt: <https://w3id.org/own/own-pt/instances/> .\n"
            "@prefix owns: <https://w3id.org/own/schema/> .\n"
        )
        palavras.write_text(
            prefixos +
            'own-pt:word-casa-n a owns:Word ; owns:lemma "casa"@pt ; owns:pos "n" .\n'
            'own-pt:word-lar-n a owns:Word ; owns:lemma "lar"@pt ; owns:pos "n" .\n'
            'own-pt:wordsense-0001-n-1 owns:word own-pt:word-casa-n .\n'
            'own-pt:wordsense-0002-n-1 owns:word own-pt:word-lar-n .\n',
            encoding="utf-8",
        )
        synsets.write_text(
            prefixos +
            'own-pt:synset-0001-n a owns:NounSynset ; owns:synsetId "0001-n" ; owns:gloss "moradia"@pt ; owns:example "Uma casa oferece abrigo"@pt .\n'
            'own-pt:synset-0002-n a owns:NounSynset ; owns:synsetId "0002-n" ; owns:gloss "habitação"@pt .\n',
            encoding="utf-8",
        )
        sentidos.write_text(
            prefixos +
            'own-pt:synset-0001-n owns:containsWordSense own-pt:wordsense-0001-n-1 .\n'
            'own-pt:synset-0002-n owns:containsWordSense own-pt:wordsense-0002-n-1 .\n',
            encoding="utf-8",
        )
        relacoes.write_text(
            prefixos +
            'own-pt:synset-0001-n owns:similarTo own-pt:synset-0002-n .\n',
            encoding="utf-8",
        )
        resultado = importar_openwordnet_ttl(
            self.lexicon, palavras, synsets, sentidos, relacoes,
            versao="fixture-ttl-1", confirmar_direitos=True,
        )
        casa = self.lexicon.buscar("casa")[0].entrada
        self.assertEqual(len(self.lexicon.sentidos(casa.identificador)), 1)
        self.assertIn("moradia", self.lexicon.sentidos(casa.identificador)[0]["definicao"])
        self.assertIn("Uma casa oferece abrigo", self.lexicon.contextos_do_sentido("0001-n"))
        self.assertGreater(resultado.relacoes_importadas, 0)
        self.assertEqual(self.lexicon.estatisticas()["relacoes"], 1)

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

    def test_desambiguacao_escolhe_sense_por_glossa_e_membros(self):
        fonte = FonteLexical(
            "wordnet-wsd", "WordNet local", "CC BY 4.0", "1",
            "https://example.org", "Atribuição",
        )
        self.lexicon.registrar_fonte(fonte, verificada=True)
        termos = ("banco", "dinheiro", "conta", "assento", "cadeira")
        for termo in termos:
            self.lexicon.adicionar_entrada(EntradaLexical(
                f"entrada-{termo}", termo, "substantivo", None,
                "wordnet-wsd", "CC BY 4.0", "1",
            ))
        self.lexicon.registrar_sentido(
            "banco-financeiro", "wordnet-wsd", "substantivo",
            "instituição financeira que guarda dinheiro e administra contas",
            ("entrada-banco", "entrada-dinheiro", "entrada-conta"),
        )
        self.lexicon.registrar_sentido(
            "banco-assento", "wordnet-wsd", "substantivo",
            "móvel ou assento usado para sentar, como uma cadeira",
            ("entrada-banco", "entrada-assento", "entrada-cadeira"),
        )
        desambiguador = DesambiguadorContextual(self.lexicon)
        isolado = desambiguador.analisar("banco")[0]
        self.assertTrue(isolado.ambiguo)
        self.assertEqual(len(isolado.candidatos), 2)
        contextual = desambiguador.analisar("banco e dinheiro")[0]
        self.assertFalse(contextual.ambiguo)
        self.assertEqual(contextual.selecionado.identificador_sentido, "banco-financeiro")

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

    def test_atualizacao_preserva_relacoes_e_contextos_de_outras_fontes(self):
        for identificador in ("fonte-a", "fonte-b"):
            self.lexicon.registrar_fonte(
                FonteLexical(
                    identificador, identificador, "MIT", "1",
                    "https://example.org", "Crédito",
                ),
                verificada=True,
            )
        self.lexicon.adicionar_entrada(EntradaLexical(
            "entrada-a", "casa", "substantivo", None,
            "fonte-a", "MIT", "1",
        ), contextos=("moradia",))
        self.lexicon.adicionar_entrada(EntradaLexical(
            "entrada-b", "lar", "substantivo", None,
            "fonte-a", "MIT", "1",
        ))
        self.lexicon.adicionar_relacao(
            "entrada-a", "entrada-b", "sinonimo", "fonte-b"
        )
        self.lexicon.adicionar_contexto(
            "entrada-a", "habitação", "fonte-b"
        )

        self.lexicon.adicionar_entrada(EntradaLexical(
            "entrada-a", "casa", "substantivo", "local de moradia",
            "fonte-a", "MIT", "1",
        ), contextos=("residência",))

        self.assertEqual(
            self.lexicon.contextos("entrada-a"),
            ("habitação", "residência"),
        )
        self.assertEqual(
            tuple(item.identificador for item in self.lexicon.relacoes("entrada-a")),
            ("entrada-b",),
        )

    def test_migracao_de_esquema_v1_para_v6(self):
        self.lexicon.fechar()
        self.db_path.unlink(missing_ok=True)
        conexao = sqlite3.connect(self.db_path)
        conexao.executescript(
            """
            PRAGMA foreign_keys=ON;
            CREATE TABLE fontes (
                id TEXT PRIMARY KEY, nome TEXT NOT NULL, licenca TEXT NOT NULL,
                versao TEXT NOT NULL, url TEXT NOT NULL, atribuicao TEXT NOT NULL,
                verificada INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE entradas (
                id TEXT PRIMARY KEY, lema TEXT NOT NULL, lema_normalizado TEXT NOT NULL,
                classe TEXT NOT NULL, definicao TEXT,
                fonte_id TEXT NOT NULL REFERENCES fontes(id),
                UNIQUE (lema_normalizado, classe, fonte_id)
            );
            CREATE TABLE formas (
                forma_normalizada TEXT NOT NULL, forma_original TEXT NOT NULL,
                entrada_id TEXT NOT NULL REFERENCES entradas(id) ON DELETE CASCADE,
                tipo TEXT NOT NULL,
                PRIMARY KEY (forma_normalizada, entrada_id, tipo)
            );
            CREATE TABLE relacoes (
                origem_id TEXT NOT NULL REFERENCES entradas(id) ON DELETE CASCADE,
                destino_id TEXT NOT NULL REFERENCES entradas(id) ON DELETE CASCADE,
                tipo TEXT NOT NULL, fonte_id TEXT NOT NULL REFERENCES fontes(id),
                PRIMARY KEY (origem_id, destino_id, tipo, fonte_id)
            );
            CREATE TABLE contextos (
                entrada_id TEXT NOT NULL REFERENCES entradas(id) ON DELETE CASCADE,
                contexto TEXT NOT NULL, fonte_id TEXT NOT NULL REFERENCES fontes(id),
                PRIMARY KEY (entrada_id, contexto, fonte_id)
            );
            INSERT INTO fontes VALUES
                ('fonte-v1', 'Fonte antiga', 'MIT', '1', 'https://example.org', 'Crédito', 1);
            INSERT INTO entradas VALUES
                ('casa-v1', 'casa', 'casa', 'substantivo', NULL, 'fonte-v1');
            INSERT INTO entradas VALUES
                ('lar-v1', 'lar', 'lar', 'substantivo', NULL, 'fonte-v1');
            INSERT INTO formas VALUES ('casa', 'casa', 'casa-v1', 'lema');
            INSERT INTO relacoes VALUES ('casa-v1', 'lar-v1', 'sinonimo', 'fonte-v1');
            INSERT INTO contextos VALUES ('casa-v1', 'moradia', 'fonte-v1');
            PRAGMA user_version=1;
            """
        )
        conexao.close()
        migrado = Lexicon(self.db_path)
        try:
            self.assertEqual(
                migrado._db.execute("PRAGMA user_version").fetchone()[0], 6
            )
            entrada = migrado.buscar("casa")[0].entrada
            self.assertEqual(entrada.licenca, "MIT")
            self.assertEqual(entrada.versao_fonte, "1")
            self.assertEqual(migrado.contextos("casa-v1"), ("moradia",))
            self.assertEqual(migrado.relacoes("casa-v1")[0].lema, "lar")
            self.assertEqual(migrado.estatisticas()["sentidos"], 0)
        finally:
            migrado.fechar()


class TesteGrandeBaseLexical(unittest.TestCase):
    def test_importacao_em_lote_de_dez_mil_entradas(self):
        with tempfile.TemporaryDirectory() as pasta:
            root = Path(pasta)
            arquivo = root / "lexico"
            arquivo.write_text(
                "".join(f"termo_{i:05d}\n" for i in range(10_000)),
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
            operacoes = [
                {
                    "op": "upsert", "source": "fonte-v2", "id": "nova",
                    "lemma": "nova", "pos": "substantivo",
                },
                {
                    "op": "upsert", "source": "fonte-v2", "id": "outra",
                    "lemma": "outra", "pos": "substantivo",
                },
                {
                    "op": "upsert_sense", "source": "fonte-v2", "id": "sense-1",
                    "pos": "substantivo", "definition": "sentido de teste",
                    "members": ["nova", "outra"],
                },
                {
                    "op": "upsert_relation", "source": "fonte-v2",
                    "origin": "nova", "destination": "outra", "type": "sinonimo",
                },
                {
                    "op": "upsert_frequency", "source": "fonte-v2",
                    "form": "nova", "value": 2.5,
                },
            ]
            delta = ("".join(json.dumps(item) + "\n" for item in operacoes)).encode()
            manifesto = {
                "schema_version": 6, "delta_sha256": hashlib.sha256(delta).hexdigest(),
                "source": fonte,
            }
            chave = Ed25519PrivateKey.generate()
            pacote = self._pacote(root, chave, delta, manifesto)
            publica = chave.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            resultado = aplicar_pacote_assinado(db, pacote, publica)
            self.assertEqual(resultado.operacoes, 5)
            self.assertTrue(Path(resultado.backup).is_file())
            with Lexicon(db) as atualizado:
                self.assertEqual(len(atualizado.buscar("nova")), 1)
                entrada_nova = atualizado.buscar("nova")[0].entrada
                self.assertEqual(len(atualizado.sentidos(entrada_nova.identificador)), 1)
                self.assertEqual(atualizado.relacoes(entrada_nova.identificador), (atualizado.buscar("outra")[0].entrada,))
                self.assertEqual(atualizado.frequencia("nova"), (2.5,))

    def test_atualizacao_preserva_versao_historica_da_entrada(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        from lume.lexical_update import aplicar_pacote_assinado

        with tempfile.TemporaryDirectory() as pasta:
            root = Path(pasta)
            db = root / "lexicon.sqlite3"
            with Lexicon(db) as lexicon:
                lexicon.registrar_fonte(
                    FonteLexical("fonte", "Fonte", "MIT", "1", "https://example.org", "Crédito"),
                    verificada=True,
                )
                lexicon.adicionar_entrada(EntradaLexical(
                    "antiga", "antiga", "substantivo", None, "fonte", "MIT", "1"
                ))
            fonte = {
                "id": "fonte", "name": "Fonte", "license": "MIT",
                "version": "2", "url": "https://example.org", "attribution": "Crédito",
            }
            delta = (json.dumps({
                "op": "upsert", "source": "fonte", "id": "nova",
                "lemma": "nova", "pos": "substantivo",
            }) + "\n").encode()
            manifesto = {
                "schema_version": 6, "delta_sha256": hashlib.sha256(delta).hexdigest(),
                "source": fonte,
            }
            chave = Ed25519PrivateKey.generate()
            pacote = self._pacote(root, chave, delta, manifesto)
            publica = chave.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            aplicar_pacote_assinado(db, pacote, publica)
            with Lexicon(db) as atualizado:
                antiga = atualizado.buscar("antiga")[0].entrada
                nova = atualizado.buscar("nova")[0].entrada
                self.assertEqual(antiga.versao_fonte, "1")
                self.assertEqual(nova.versao_fonte, "2")

    def test_delta_invalido_faz_rollback_sem_alterar_banco(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        from lume.lexical_update import aplicar_pacote_assinado

        with tempfile.TemporaryDirectory() as pasta:
            root = Path(pasta)
            db = root / "lexicon.sqlite3"
            with Lexicon(db) as lexicon:
                lexicon.registrar_fonte(
                    FonteLexical("base", "Base", "MIT", "1", "https://example.org", "Crédito"),
                    verificada=True,
                )
                lexicon.adicionar_entrada(EntradaLexical(
                    "fixa", "fixa", "substantivo", None, "base", "MIT", "1"
                ))
            fonte = {
                "id": "base", "name": "Base", "license": "MIT",
                "version": "2", "url": "https://example.org", "attribution": "Crédito",
            }
            delta = (json.dumps({
                "op": "operacao_inexistente", "source": "base",
            }) + "\n").encode()
            manifesto = {
                "schema_version": 6, "delta_sha256": hashlib.sha256(delta).hexdigest(),
                "source": fonte,
            }
            chave = Ed25519PrivateKey.generate()
            pacote = self._pacote(root, chave, delta, manifesto)
            publica = chave.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            with self.assertRaisesRegex(ValueError, "operação desconhecida"):
                aplicar_pacote_assinado(db, pacote, publica)
            with Lexicon(db) as original:
                self.assertEqual(original.buscar("fixa")[0].entrada.versao_fonte, "1")
                self.assertFalse(db.with_suffix(".sqlite3.bak").exists())

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
                "schema_version": 6, "delta_sha256": hashlib.sha256(delta).hexdigest(),
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
