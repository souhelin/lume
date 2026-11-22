"""Armazenamento lexical local e determinístico da Lume.

O módulo não contém dados de terceiros. Os conjuntos lexicais são importados
separadamente, com proveniência e licença registradas por fonte.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import threading
import unicodedata
from collections import OrderedDict
from typing import Iterable


SCHEMA_VERSION = 1
CACHE_MAXIMO = 512


def normalizar_forma(texto: str) -> str:
    """Normaliza Unicode e caixa sem remover diacríticos."""
    if not isinstance(texto, str):
        raise TypeError("a forma lexical precisa ser texto")
    return " ".join(unicodedata.normalize("NFC", texto).casefold().split())


@dataclass(frozen=True, slots=True)
class FonteLexical:
    identificador: str
    nome: str
    licenca: str
    versao: str
    url: str
    atribuicao: str


@dataclass(frozen=True, slots=True)
class EntradaLexical:
    identificador: str
    lema: str
    classe_gramatical: str
    definicao: str | None
    fonte: str
    licenca: str
    versao_fonte: str


@dataclass(frozen=True, slots=True)
class CorrespondenciaLexical:
    entrada: EntradaLexical
    forma_encontrada: str
    tipo_forma: str


class Lexicon:
    """Banco SQLite lexical, compartilhável entre os componentes da Lume.

    O caminho deve ser fornecido pelo hospedeiro. Use `:memory:` em testes.
    O banco não baixa dados nem acessa a rede.
    """

    def __init__(self, caminho: str | Path = ":memory:") -> None:
        self.caminho = str(caminho)
        if self.caminho != ":memory:":
            Path(self.caminho).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._cache: OrderedDict[tuple[str, bool], tuple[CorrespondenciaLexical, ...]] = OrderedDict()
        self._db = sqlite3.connect(
            self.caminho, timeout=5.0, check_same_thread=False
        )
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.execute("PRAGMA foreign_keys = ON")
            self._db.execute("PRAGMA busy_timeout = 5000")
            if self.caminho != ":memory:":
                self._db.execute("PRAGMA journal_mode = WAL")
                self._db.execute("PRAGMA synchronous = NORMAL")
            self._migrar()

    def _migrar(self) -> None:
        versao = int(self._db.execute("PRAGMA user_version").fetchone()[0])
        if versao > SCHEMA_VERSION:
            raise RuntimeError(
                f"banco lexical versão {versao} não é compatível "
                f"com esta versão da Lume ({SCHEMA_VERSION})"
            )
        if versao == SCHEMA_VERSION:
            return
        with self._db:
            self._db.executescript(
                """
                CREATE TABLE IF NOT EXISTS fontes (
                    id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    licenca TEXT NOT NULL,
                    versao TEXT NOT NULL,
                    url TEXT NOT NULL,
                    atribuicao TEXT NOT NULL,
                    verificada INTEGER NOT NULL DEFAULT 0
                        CHECK (verificada IN (0, 1))
                );
                CREATE TABLE IF NOT EXISTS entradas (
                    id TEXT PRIMARY KEY,
                    lema TEXT NOT NULL,
                    lema_normalizado TEXT NOT NULL,
                    classe TEXT NOT NULL,
                    definicao TEXT,
                    fonte_id TEXT NOT NULL REFERENCES fontes(id),
                    UNIQUE (lema_normalizado, classe, fonte_id)
                );
                CREATE TABLE IF NOT EXISTS formas (
                    forma_normalizada TEXT NOT NULL,
                    forma_original TEXT NOT NULL,
                    entrada_id TEXT NOT NULL REFERENCES entradas(id)
                        ON DELETE CASCADE,
                    tipo TEXT NOT NULL,
                    PRIMARY KEY (forma_normalizada, entrada_id, tipo)
                );
                CREATE TABLE IF NOT EXISTS relacoes (
                    origem_id TEXT NOT NULL REFERENCES entradas(id)
                        ON DELETE CASCADE,
                    destino_id TEXT NOT NULL REFERENCES entradas(id)
                        ON DELETE CASCADE,
                    tipo TEXT NOT NULL,
                    fonte_id TEXT NOT NULL REFERENCES fontes(id),
                    PRIMARY KEY (origem_id, destino_id, tipo, fonte_id)
                );
                CREATE TABLE IF NOT EXISTS contextos (
                    entrada_id TEXT NOT NULL REFERENCES entradas(id)
                        ON DELETE CASCADE,
                    contexto TEXT NOT NULL,
                    fonte_id TEXT NOT NULL REFERENCES fontes(id),
                    PRIMARY KEY (entrada_id, contexto, fonte_id)
                );
                CREATE INDEX IF NOT EXISTS idx_entradas_lema
                    ON entradas(lema_normalizado);
                CREATE INDEX IF NOT EXISTS idx_formas_busca
                    ON formas(forma_normalizada);
                CREATE INDEX IF NOT EXISTS idx_relacoes_origem
                    ON relacoes(origem_id, tipo);
                CREATE INDEX IF NOT EXISTS idx_contextos_entrada
                    ON contextos(entrada_id);
                """
            )
            self._db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def fechar(self) -> None:
        with self._lock:
            self._db.close()
            self._cache.clear()

    def __enter__(self) -> "Lexicon":
        return self

    def __exit__(self, *_: object) -> None:
        self.fechar()

    def registrar_fonte(self, fonte: FonteLexical, *, verificada: bool = False) -> None:
        campos = (
            fonte.identificador, fonte.nome, fonte.licenca,
            fonte.versao, fonte.url, fonte.atribuicao,
        )
        if any(not isinstance(c, str) or not c.strip() for c in campos):
            raise ValueError("todos os metadados da fonte são obrigatórios")
        with self._lock, self._db:
            self._db.execute(
                """
                INSERT INTO fontes(id, nome, licenca, versao, url, atribuicao, verificada)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    nome=excluded.nome, licenca=excluded.licenca,
                    versao=excluded.versao, url=excluded.url,
                    atribuicao=excluded.atribuicao, verificada=excluded.verificada
                """,
                (*campos, int(verificada)),
            )
            self._limpar_cache()

    def adicionar_entrada(
        self,
        entrada: EntradaLexical,
        *,
        formas: Iterable[tuple[str, str]] = (),
        relacoes: Iterable[tuple[str, str]] = (),
        contextos: Iterable[str] = (),
    ) -> None:
        if not entrada.identificador.strip() or not entrada.lema.strip():
            raise ValueError("identificador e lema são obrigatórios")
        if not entrada.classe_gramatical.strip():
            raise ValueError("classe gramatical é obrigatória")
        with self._lock, self._db:
            fonte = self._db.execute(
                "SELECT licenca, versao, verificada FROM fontes WHERE id=?",
                (entrada.fonte,),
            ).fetchone()
            if fonte is None:
                raise ValueError("a fonte lexical precisa ser registrada antes dos dados")
            if not fonte["verificada"]:
                raise ValueError("a fonte não foi marcada como licenciada e verificada")
            if entrada.licenca != fonte["licenca"] or entrada.versao_fonte != fonte["versao"]:
                raise ValueError("licença e versão da entrada divergem dos metadados da fonte")
            self._db.execute(
                """
                INSERT INTO entradas(id, lema, lema_normalizado, classe, definicao, fonte_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    lema=excluded.lema, lema_normalizado=excluded.lema_normalizado,
                    classe=excluded.classe, definicao=excluded.definicao,
                    fonte_id=excluded.fonte_id
                """,
                (
                    entrada.identificador, entrada.lema,
                    normalizar_forma(entrada.lema), entrada.classe_gramatical,
                    entrada.definicao, entrada.fonte,
                ),
            )
            self._db.execute("DELETE FROM formas WHERE entrada_id=?", (entrada.identificador,))
            self._db.execute("DELETE FROM relacoes WHERE origem_id=?", (entrada.identificador,))
            self._db.execute("DELETE FROM contextos WHERE entrada_id=?", (entrada.identificador,))
            formas_validas = [(entrada.lema, "lema"), *list(formas)]
            for forma, tipo in formas_validas:
                if not forma.strip() or not tipo.strip():
                    raise ValueError("forma e tipo de flexão não podem ser vazios")
                self._db.execute(
                    """
                    INSERT OR IGNORE INTO formas
                    (forma_normalizada, forma_original, entrada_id, tipo)
                    VALUES (?, ?, ?, ?)
                    """,
                    (normalizar_forma(forma), forma, entrada.identificador, tipo),
                )
            for destino, tipo in relacoes:
                if not destino.strip() or not tipo.strip():
                    raise ValueError("destino e tipo de relação são obrigatórios")
                self._db.execute(
                    """
                    INSERT OR IGNORE INTO relacoes(origem_id, destino_id, tipo, fonte_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (entrada.identificador, destino, tipo, entrada.fonte),
                )
            for contexto in contextos:
                if contexto.strip():
                    self._db.execute(
                        "INSERT OR IGNORE INTO contextos VALUES (?, ?, ?)",
                        (entrada.identificador, contexto.strip(), entrada.fonte),
                    )
            self._limpar_cache()

    def _entrada_da_linha(self, row: sqlite3.Row) -> EntradaLexical:
        return EntradaLexical(
            row["id"], row["lema"], row["classe"], row["definicao"],
            row["fonte_id"], row["licenca"], row["versao"],
        )

    def buscar(
        self, texto: str, *, incluir_flexoes: bool = True
    ) -> tuple[CorrespondenciaLexical, ...]:
        normalizado = normalizar_forma(texto)
        if not normalizado:
            return ()
        chave = (normalizado, incluir_flexoes)
        with self._lock:
            if chave in self._cache:
                self._cache.move_to_end(chave)
                return self._cache[chave]
            if incluir_flexoes:
                rows = self._db.execute(
                    """
                    SELECT e.id, e.lema, e.classe, e.definicao, e.fonte_id,
                           f.licenca, f.versao, x.forma_original, x.tipo
                    FROM formas x
                    JOIN entradas e ON e.id=x.entrada_id
                    JOIN fontes f ON f.id=e.fonte_id
                    WHERE x.forma_normalizada=?
                    ORDER BY e.lema, e.classe, e.id
                    """,
                    (normalizado,),
                ).fetchall()
            else:
                rows = self._db.execute(
                    """
                    SELECT e.id, e.lema, e.classe, e.definicao, e.fonte_id,
                           f.licenca, f.versao, e.lema AS forma_original,
                           'lema' AS tipo
                    FROM entradas e JOIN fontes f ON f.id=e.fonte_id
                    WHERE e.lema_normalizado=?
                    ORDER BY e.lema, e.classe, e.id
                    """,
                    (normalizado,),
                ).fetchall()
            resultado = tuple(
                CorrespondenciaLexical(
                    self._entrada_da_linha(row),
                    row["forma_original"], row["tipo"],
                )
                for row in rows
            )
            self._cache[chave] = resultado
            if len(self._cache) > CACHE_MAXIMO:
                self._cache.popitem(last=False)
            return resultado

    def relacoes(self, identificador: str, tipo: str | None = None) -> tuple[EntradaLexical, ...]:
        consulta = """
            SELECT e.id, e.lema, e.classe, e.definicao, e.fonte_id,
                   f.licenca, f.versao
            FROM relacoes r
            JOIN entradas e ON e.id=r.destino_id
            JOIN fontes f ON f.id=e.fonte_id
            WHERE r.origem_id=?
        """
        parametros: tuple[object, ...] = (identificador,)
        if tipo is not None:
            consulta += " AND r.tipo=?"
            parametros += (tipo,)
        consulta += " ORDER BY e.lema, e.id"
        with self._lock:
            rows = self._db.execute(consulta, parametros).fetchall()
            return tuple(self._entrada_da_linha(row) for row in rows)

    def integridade(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(row[0] for row in self._db.execute("PRAGMA integrity_check"))

    def estatisticas(self) -> dict[str, int]:
        with self._lock:
            return {
                tabela: int(self._db.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0])
                for tabela in ("fontes", "entradas", "formas", "relacoes", "contextos")
            }

    def _limpar_cache(self) -> None:
        self._cache.clear()
