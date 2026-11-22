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


SCHEMA_VERSION = 6
CACHE_MAXIMO = 512


def normalizar_forma(texto: str) -> str:
    """Normaliza Unicode e caixa sem remover diacríticos."""
    if not isinstance(texto, str):
        raise TypeError("a forma lexical precisa ser texto")
    caixa_normalizada = unicodedata.normalize("NFC", texto).casefold()
    return " ".join(unicodedata.normalize("NFC", caixa_normalizada).split())


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
        if versao == 5:
            with self._db:
                self._migrar_contextos_sentido()
                self._db.execute("PRAGMA user_version = 6")
            return
        if versao == 4:
            with self._db:
                self._migrar_procedencia_relacoes()
                self._migrar_contextos_sentido()
                self._db.execute("PRAGMA user_version = 6")
            return
        if versao == 3:
            with self._db:
                self._db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS frequencias (
                        forma_normalizada TEXT NOT NULL,
                        forma_original TEXT NOT NULL,
                        valor REAL NOT NULL,
                        fonte_id TEXT NOT NULL REFERENCES fontes(id),
                        versao_fonte TEXT NOT NULL,
                        PRIMARY KEY (forma_normalizada, fonte_id)
                    );
                    CREATE INDEX IF NOT EXISTS idx_frequencias_forma
                        ON frequencias(forma_normalizada);
                    """
                )
                self._migrar_procedencia_relacoes()
                self._migrar_contextos_sentido()
                self._db.execute("PRAGMA user_version = 6")
            return
        if versao in (1, 2):
            with self._db:
                if versao == 1:
                    self._db.executescript(
                        """
                        CREATE TABLE IF NOT EXISTS sentidos (
                            id TEXT PRIMARY KEY,
                            fonte_id TEXT NOT NULL REFERENCES fontes(id),
                            classe TEXT NOT NULL,
                            definicao TEXT
                        );
                        CREATE TABLE IF NOT EXISTS sentido_entradas (
                            sentido_id TEXT NOT NULL REFERENCES sentidos(id) ON DELETE CASCADE,
                            entrada_id TEXT NOT NULL REFERENCES entradas(id) ON DELETE CASCADE,
                            ordem INTEGER NOT NULL DEFAULT 0,
                            PRIMARY KEY (sentido_id, entrada_id)
                        );
                        CREATE INDEX IF NOT EXISTS idx_sentido_entradas_entrada
                            ON sentido_entradas(entrada_id);
                        """
                    )
                colunas_entradas = {
                    row["name"] for row in self._db.execute("PRAGMA table_info(entradas)")
                }
                if "licenca" not in colunas_entradas:
                    self._db.execute("ALTER TABLE entradas ADD COLUMN licenca TEXT NOT NULL DEFAULT ''")
                if "versao_fonte" not in colunas_entradas:
                    self._db.execute("ALTER TABLE entradas ADD COLUMN versao_fonte TEXT NOT NULL DEFAULT ''")
                self._db.execute(
                    """
                    UPDATE entradas
                    SET licenca=(SELECT licenca FROM fontes WHERE id=entradas.fonte_id),
                        versao_fonte=(SELECT versao FROM fontes WHERE id=entradas.fonte_id)
                    WHERE licenca='' OR versao_fonte=''
                    """
                )
                colunas_sentidos = {
                    row["name"] for row in self._db.execute("PRAGMA table_info(sentidos)")
                }
                if "licenca" not in colunas_sentidos:
                    self._db.execute("ALTER TABLE sentidos ADD COLUMN licenca TEXT NOT NULL DEFAULT ''")
                if "versao_fonte" not in colunas_sentidos:
                    self._db.execute("ALTER TABLE sentidos ADD COLUMN versao_fonte TEXT NOT NULL DEFAULT ''")
                self._db.execute(
                    """
                    UPDATE sentidos
                    SET licenca=(SELECT licenca FROM fontes WHERE id=sentidos.fonte_id),
                        versao_fonte=(SELECT versao FROM fontes WHERE id=sentidos.fonte_id)
                    WHERE licenca='' OR versao_fonte=''
                    """
                )
                self._db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS frequencias (
                        forma_normalizada TEXT NOT NULL,
                        forma_original TEXT NOT NULL,
                        valor REAL NOT NULL,
                        fonte_id TEXT NOT NULL REFERENCES fontes(id),
                        versao_fonte TEXT NOT NULL,
                        PRIMARY KEY (forma_normalizada, fonte_id)
                    )
                    """
                )
                self._db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_frequencias_forma ON frequencias(forma_normalizada)"
                )
                self._migrar_procedencia_relacoes()
                self._migrar_contextos_sentido()
                self._db.execute("PRAGMA user_version = 6")
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
                    licenca TEXT NOT NULL,
                    versao_fonte TEXT NOT NULL,
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
                    licenca TEXT NOT NULL,
                    versao_fonte TEXT NOT NULL,
                    PRIMARY KEY (origem_id, destino_id, tipo, fonte_id)
                );
                CREATE TABLE IF NOT EXISTS contextos (
                    entrada_id TEXT NOT NULL REFERENCES entradas(id)
                        ON DELETE CASCADE,
                    contexto TEXT NOT NULL,
                    fonte_id TEXT NOT NULL REFERENCES fontes(id),
                    licenca TEXT NOT NULL,
                    versao_fonte TEXT NOT NULL,
                    PRIMARY KEY (entrada_id, contexto, fonte_id)
                );
                CREATE TABLE IF NOT EXISTS frequencias (
                    forma_normalizada TEXT NOT NULL,
                    forma_original TEXT NOT NULL,
                    valor REAL NOT NULL,
                    fonte_id TEXT NOT NULL REFERENCES fontes(id),
                    versao_fonte TEXT NOT NULL,
                    PRIMARY KEY (forma_normalizada, fonte_id)
                );
                CREATE INDEX IF NOT EXISTS idx_frequencias_forma
                    ON frequencias(forma_normalizada);
                CREATE TABLE IF NOT EXISTS sentidos (
                    id TEXT PRIMARY KEY,
                    fonte_id TEXT NOT NULL REFERENCES fontes(id),
                    classe TEXT NOT NULL,
                    definicao TEXT,
                    licenca TEXT NOT NULL,
                    versao_fonte TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sentido_entradas (
                    sentido_id TEXT NOT NULL REFERENCES sentidos(id) ON DELETE CASCADE,
                    entrada_id TEXT NOT NULL REFERENCES entradas(id) ON DELETE CASCADE,
                    ordem INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (sentido_id, entrada_id)
                );
                CREATE TABLE IF NOT EXISTS sentido_contextos (
                    sentido_id TEXT NOT NULL REFERENCES sentidos(id) ON DELETE CASCADE,
                    contexto TEXT NOT NULL,
                    fonte_id TEXT NOT NULL REFERENCES fontes(id),
                    licenca TEXT NOT NULL,
                    versao_fonte TEXT NOT NULL,
                    PRIMARY KEY (sentido_id, contexto, fonte_id)
                );
                CREATE INDEX IF NOT EXISTS idx_sentido_entradas_entrada
                    ON sentido_entradas(entrada_id);
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

    def _migrar_procedencia_relacoes(self) -> None:
        """Acrescenta versão/licença aos vínculos semânticos já existentes."""
        for tabela in ("relacoes", "contextos"):
            colunas = {
                row["name"] for row in self._db.execute(f"PRAGMA table_info({tabela})")
            }
            if "licenca" not in colunas:
                self._db.execute(
                    f"ALTER TABLE {tabela} ADD COLUMN licenca TEXT NOT NULL DEFAULT ''"
                )
            if "versao_fonte" not in colunas:
                self._db.execute(
                    f"ALTER TABLE {tabela} ADD COLUMN versao_fonte TEXT NOT NULL DEFAULT ''"
                )
            self._db.execute(
                f"""
                UPDATE {tabela}
                SET licenca=(SELECT licenca FROM fontes WHERE id={tabela}.fonte_id),
                    versao_fonte=(SELECT versao FROM fontes WHERE id={tabela}.fonte_id)
                WHERE licenca='' OR versao_fonte=''
                """
            )

    def _migrar_contextos_sentido(self) -> None:
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS sentido_contextos (
                sentido_id TEXT NOT NULL REFERENCES sentidos(id) ON DELETE CASCADE,
                contexto TEXT NOT NULL,
                fonte_id TEXT NOT NULL REFERENCES fontes(id),
                licenca TEXT NOT NULL,
                versao_fonte TEXT NOT NULL,
                PRIMARY KEY (sentido_id, contexto, fonte_id)
            )
            """
        )

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
                INSERT INTO entradas(
                    id, lema, lema_normalizado, classe, definicao, fonte_id,
                    licenca, versao_fonte
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    lema=excluded.lema, lema_normalizado=excluded.lema_normalizado,
                    classe=excluded.classe, definicao=excluded.definicao,
                    fonte_id=excluded.fonte_id, licenca=excluded.licenca,
                    versao_fonte=excluded.versao_fonte
                """,
                (
                    entrada.identificador, entrada.lema,
                    normalizar_forma(entrada.lema), entrada.classe_gramatical,
                    entrada.definicao, entrada.fonte, entrada.licenca,
                    entrada.versao_fonte,
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
                    INSERT INTO relacoes
                        (origem_id, destino_id, tipo, fonte_id, licenca, versao_fonte)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(origem_id, destino_id, tipo, fonte_id) DO UPDATE SET
                        licenca=excluded.licenca, versao_fonte=excluded.versao_fonte
                    """,
                    (
                        entrada.identificador, destino, tipo, entrada.fonte,
                        entrada.licenca, entrada.versao_fonte,
                    ),
                )
            for contexto in contextos:
                if contexto.strip():
                    self._db.execute(
                        """
                        INSERT INTO contextos
                            (entrada_id, contexto, fonte_id, licenca, versao_fonte)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(entrada_id, contexto, fonte_id) DO UPDATE SET
                            licenca=excluded.licenca, versao_fonte=excluded.versao_fonte
                        """,
                        (
                            entrada.identificador, contexto.strip(), entrada.fonte,
                            entrada.licenca, entrada.versao_fonte,
                        ),
                    )
            self._limpar_cache()

    def adicionar_relacao(
        self, origem_id: str, destino_id: str, tipo: str, fonte_id: str
    ) -> None:
        """Registra uma relação tipada entre duas entradas já existentes."""
        if not tipo.strip():
            raise ValueError("o tipo da relação não pode ser vazio")
        with self._lock, self._db:
            fonte = self._db.execute(
                "SELECT verificada, licenca, versao FROM fontes WHERE id=?", (fonte_id,)
            ).fetchone()
            if fonte is None or not fonte["verificada"]:
                raise ValueError("a fonte da relação precisa estar verificada")
            ids = self._db.execute(
                "SELECT id FROM entradas WHERE id IN (?, ?)",
                (origem_id, destino_id),
            ).fetchall()
            if len({row["id"] for row in ids}) != 2:
                raise ValueError("as duas entradas da relação precisam existir")
            self._db.execute(
                """
                INSERT INTO relacoes
                    (origem_id, destino_id, tipo, fonte_id, licenca, versao_fonte)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(origem_id, destino_id, tipo, fonte_id) DO UPDATE SET
                    licenca=excluded.licenca, versao_fonte=excluded.versao_fonte
                """,
                (
                    origem_id, destino_id, tipo, fonte_id,
                    fonte["licenca"], fonte["versao"],
                ),
            )

    def registrar_sentido(
        self, identificador: str, fonte_id: str, classe: str,
        definicao: str | None, entradas: Iterable[str],
        contextos: Iterable[str] = (),
    ) -> None:
        """Registra um sentido/synset e associa suas entradas lexicais."""
        if not identificador.strip() or not classe.strip():
            raise ValueError("identificador e classe do sentido são obrigatórios")
        membros = tuple(dict.fromkeys(entradas))
        if not membros:
            raise ValueError("um sentido precisa conter ao menos uma entrada")
        with self._lock, self._db:
            fonte = self._db.execute(
                "SELECT verificada FROM fontes WHERE id=?", (fonte_id,)
            ).fetchone()
            if fonte is None or not fonte["verificada"]:
                raise ValueError("a fonte do sentido precisa estar verificada")
            existentes = {
                row["id"] for row in self._db.execute(
                    "SELECT id FROM entradas WHERE id IN (" +
                    ",".join("?" for _ in membros) + ")", membros
                )
            }
            if existentes != set(membros):
                raise ValueError("todas as entradas do sentido precisam existir")
            self._db.execute(
                """
                INSERT INTO sentidos(id, fonte_id, classe, definicao, licenca, versao_fonte)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    fonte_id=excluded.fonte_id, classe=excluded.classe,
                    definicao=excluded.definicao, licenca=excluded.licenca,
                    versao_fonte=excluded.versao_fonte
                """,
                (
                    identificador, fonte_id, classe, definicao,
                    self._db.execute(
                        "SELECT licenca FROM fontes WHERE id=?", (fonte_id,)
                    ).fetchone()[0],
                    self._db.execute(
                        "SELECT versao FROM fontes WHERE id=?", (fonte_id,)
                    ).fetchone()[0],
                ),
            )
            self._db.execute(
                "DELETE FROM sentido_entradas WHERE sentido_id=?", (identificador,)
            )
            self._db.executemany(
                "INSERT INTO sentido_entradas(sentido_id, entrada_id, ordem) VALUES (?, ?, ?)",
                ((identificador, membro, i) for i, membro in enumerate(membros)),
            )
            self._db.execute(
                "DELETE FROM sentido_contextos WHERE sentido_id=?", (identificador,)
            )
            fonte_meta = self._db.execute(
                "SELECT licenca, versao FROM fontes WHERE id=?", (fonte_id,)
            ).fetchone()
            self._db.executemany(
                """
                INSERT INTO sentido_contextos
                    (sentido_id, contexto, fonte_id, licenca, versao_fonte)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    (
                        identificador, contexto.strip(), fonte_id,
                        fonte_meta["licenca"], fonte_meta["versao"],
                    )
                    for contexto in contextos if contexto.strip()
                ),
            )

    def sentidos(self, identificador_entrada: str) -> tuple[dict[str, str | None], ...]:
        """Retorna os sentidos ligados a uma entrada, com procedência."""
        with self._lock:
            rows = self._db.execute(
                """
                SELECT s.id, s.classe, s.definicao, s.fonte_id, s.licenca, s.versao_fonte
                FROM sentido_entradas se
                JOIN sentidos s ON s.id=se.sentido_id
                WHERE se.entrada_id=?
                ORDER BY s.id
                """,
                (identificador_entrada,),
            ).fetchall()
            return tuple(dict(row) for row in rows)

    def contextos_do_sentido(self, identificador_sentido: str) -> tuple[str, ...]:
        """Retorna exemplos/contextos vinculados a um synset específico."""
        with self._lock:
            rows = self._db.execute(
                """
                SELECT contexto FROM sentido_contextos
                WHERE sentido_id=? ORDER BY contexto
                """,
                (identificador_sentido,),
            ).fetchall()
            return tuple(row["contexto"] for row in rows)

    def termos_do_sentido(self, identificador_sentido: str) -> tuple[str, ...]:
        """Retorna os lemas associados a um synset, sem duplicatas."""
        with self._lock:
            rows = self._db.execute(
                """
                SELECT e.lema
                FROM sentido_entradas se
                JOIN entradas e ON e.id=se.entrada_id
                WHERE se.sentido_id=?
                ORDER BY se.ordem, e.lema
                """,
                (identificador_sentido,),
            ).fetchall()
            return tuple(row["lema"] for row in rows)

    def contextos(self, identificador: str) -> tuple[str, ...]:
        with self._lock:
            rows = self._db.execute(
                "SELECT contexto FROM contextos WHERE entrada_id=? ORDER BY contexto",
                (identificador,),
            ).fetchall()
            return tuple(row["contexto"] for row in rows)

    def _entrada_da_linha(self, row: sqlite3.Row) -> EntradaLexical:
        return EntradaLexical(
            row["id"], row["lema"], row["classe"], row["definicao"],
            row["fonte_id"], row["licenca"], row["versao_fonte"],
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
                           e.licenca, e.versao_fonte, x.forma_original, x.tipo
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
                           e.licenca, e.versao_fonte, e.lema AS forma_original,
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
                   e.licenca, e.versao_fonte
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

    def frequencia(self, texto: str, fonte_id: str | None = None) -> tuple[float, ...]:
        """Retorna pontuações de frequência registradas para a forma consultada."""
        normalizado = normalizar_forma(texto)
        with self._lock:
            if fonte_id is None:
                rows = self._db.execute(
                    "SELECT valor FROM frequencias WHERE forma_normalizada=? ORDER BY fonte_id",
                    (normalizado,),
                ).fetchall()
            else:
                rows = self._db.execute(
                    "SELECT valor FROM frequencias WHERE forma_normalizada=? AND fonte_id=?",
                    (normalizado, fonte_id),
                ).fetchall()
            return tuple(float(row["valor"]) for row in rows)

    def integridade(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(row[0] for row in self._db.execute("PRAGMA integrity_check"))

    def estatisticas(self) -> dict[str, int]:
        with self._lock:
            return {
                tabela: int(self._db.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0])
                for tabela in ("fontes", "entradas", "formas", "relacoes", "contextos", "sentidos", "sentido_entradas", "sentido_contextos", "frequencias")
            }

    def _limpar_cache(self) -> None:
        self._cache.clear()
