"""Importadores explícitos e offline para fontes lexicais do LUME.

Os arquivos são fornecidos localmente pelo usuário. Este módulo não baixa dados.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Iterable, Iterator

from .lexicon import FonteLexical, Lexicon, normalizar_forma


@dataclass(frozen=True, slots=True)
class ResultadoImportacao:
    fonte: str
    registros_lidos: int
    registros_importados: int
    sentidos_importados: int = 0
    ignorados: int = 0
    relacoes_importadas: int = 0


def _linhas(caminho: str | Path) -> Iterator[str]:
    with Path(caminho).open("r", encoding="utf-8-sig", newline="") as arquivo:
        for linha in arquivo:
            valor = linha.strip()
            if valor and not valor.startswith("#"):
                yield valor


def _id(fonte: str, classe: str, lema: str) -> str:
    chave = f"{fonte}\0{classe}\0{normalizar_forma(lema)}"
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()[:32]


def _registrar_fonte(
    lexicon: Lexicon, *, identificador: str, nome: str, licenca: str,
    versao: str, url: str, atribuicao: str, confirmar_direitos: bool,
) -> None:
    if not confirmar_direitos:
        raise PermissionError(
            "Importação bloqueada: revise a licença/procedência e passe "
            "confirmar_direitos=True conscientemente."
        )
    lexicon.registrar_fonte(
        FonteLexical(identificador, nome, licenca, versao, url, atribuicao),
        verificada=True,
    )


def _gravar_entradas(
    lexicon: Lexicon, fonte: str, entradas: Iterable[tuple[str, str, str, str | None]],
) -> int:
    """Grava (id, lema, classe) em lote, mantendo o banco em uma transação."""
    lote = list(entradas)
    if not lote:
        return 0
    with lexicon._lock, lexicon._db:
        registro = lexicon._db.execute(
            "SELECT verificada FROM fontes WHERE id=?", (fonte,)
        ).fetchone()
        if registro is None or not registro["verificada"]:
            raise PermissionError("fonte não verificada para importação")
        fonte_meta = lexicon._db.execute(
            "SELECT licenca, versao FROM fontes WHERE id=?", (fonte,)
        ).fetchone()
        lexicon._db.executemany(
            """
            INSERT INTO entradas
                (id, lema, lema_normalizado, classe, definicao, fonte_id, licenca, versao_fonte)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                lema=excluded.lema, lema_normalizado=excluded.lema_normalizado,
                classe=excluded.classe, definicao=excluded.definicao,
                fonte_id=excluded.fonte_id, licenca=excluded.licenca,
                versao_fonte=excluded.versao_fonte
            """,
            (
                (
                    identificador, lema, normalizar_forma(lema), classe,
                    definicao, fonte, fonte_meta["licenca"], fonte_meta["versao"]
                )
                for identificador, lema, classe, definicao in lote
            ),
        )
        lexicon._db.executemany(
            """
            INSERT OR IGNORE INTO formas
                (forma_normalizada, forma_original, entrada_id, tipo)
            VALUES (?, ?, ?, 'lema')
            """,
            (
                (normalizar_forma(lema), lema, identificador)
                for identificador, lema, _classe, _definicao in lote
            ),
        )
        lexicon._limpar_cache()
    return len(lote)


def importar_fserb_lexico(
    lexicon: Lexicon, arquivo_lexico: str | Path, *,
    versao: str, confirmar_direitos: bool = False,
    limite: int | None = None,
) -> ResultadoImportacao:
    """Importa o arquivo de uma palavra por linha, sem inventar classe/definição.

    O agregado upstream informa múltiplas fontes dicionarísticas. O aceite
    explícito não substitui uma auditoria jurídica dos dados de origem.
    """
    fonte = "fserb-pt-br-lexico"
    _registrar_fonte(
        lexicon, identificador=fonte, nome="fserb/pt-br — lexico",
        licenca="MIT (licença declarada no repositório; proveniência agregada pendente)",
        versao=versao, url="https://github.com/fserb/pt-br",
        atribuicao="Copyright 2021 Fernando Serboncini; preservar LICENSE upstream.",
        confirmar_direitos=confirmar_direitos,
    )
    vistos: set[str] = set()
    lote: list[tuple[str, str, str | None]] = []
    lidos = importados = ignorados = 0
    for palavra in _linhas(arquivo_lexico):
        lidos += 1
        termo = normalizar_forma(palavra)
        if termo in vistos:
            ignorados += 1
            continue
        vistos.add(termo)
        lote.append((_id(fonte, "não_classificada", palavra), palavra,
                     "não_classificada", None))
        if len(lote) >= 2000:
            importados += _gravar_entradas(lexicon, fonte, lote)
            lote.clear()
        if limite is not None and lidos >= limite:
            break
    importados += _gravar_entradas(lexicon, fonte, lote)
    return ResultadoImportacao(fonte, lidos, importados, ignorados=ignorados)


def importar_fserb_conjugacoes(
    lexicon: Lexicon, arquivo_conjugacoes: str | Path, *,
    versao: str, confirmar_direitos: bool = False,
    limite: int | None = None,
) -> ResultadoImportacao:
    """Importa formas verbais como formas não analisadas, sem atribuir lema falso.

    O arquivo é uma lista simples; não contém vínculo forma→infinitivo.
    """
    fonte = "fserb-pt-br-conjugacoes"
    _registrar_fonte(
        lexicon, identificador=fonte, nome="fserb/pt-br — conjugações",
        licenca="MIT (licença declarada no repositório; proveniência agregada pendente)",
        versao=versao, url="https://github.com/fserb/pt-br",
        atribuicao="Copyright 2021 Fernando Serboncini; preservar LICENSE upstream.",
        confirmar_direitos=confirmar_direitos,
    )
    vistos: set[str] = set()
    lote: list[tuple[str, str, str | None]] = []
    lidos = importados = ignorados = 0
    for forma in _linhas(arquivo_conjugacoes):
        lidos += 1
        termo = normalizar_forma(forma)
        if termo in vistos:
            ignorados += 1
            continue
        vistos.add(termo)
        lote.append((_id(fonte, "forma_verbal_sem_lema", forma), forma,
                     "forma_verbal_sem_lema", None))
        if len(lote) >= 2000:
            importados += _gravar_entradas(lexicon, fonte, lote)
            lote.clear()
        if limite is not None and lidos >= limite:
            break
    importados += _gravar_entradas(lexicon, fonte, lote)
    return ResultadoImportacao(fonte, lidos, importados, ignorados=ignorados)


def importar_openwordnet_tsv(
    lexicon: Lexicon, arquivo_tsv: str | Path, *,
    versao: str, confirmar_direitos: bool = False,
    limite: int | None = None,
) -> ResultadoImportacao:
    """Importa exportação OMW TSV: synset_id<TAB>tipo<TAB>lema.

    Cada synset vira um sentido; termos iguais podem pertencer a vários
    sentidos sem serem confundidos. O arquivo não contém glossas neste formato.
    """
    fonte = "openwordnet-pt-omw"
    _registrar_fonte(
        lexicon, identificador=fonte, nome="OpenWordNet-PT (exportação OMW)",
        licenca="CC BY-SA 3.0 (licença do export OMW por)",
        versao=versao, url="https://github.com/omwn/omw-data/tree/main/wns/por",
        atribuicao=(
            "OpenWordNet-PT; atribuição aos autores do recurso. "
            "Distribuir os dados derivados sob CC BY-SA 3.0 e preservar avisos upstream."
        ),
        confirmar_direitos=confirmar_direitos,
    )
    pos_map = {
        "n": "substantivo", "v": "verbo", "a": "adjetivo",
        "s": "adjetivo", "r": "adverbio",
    }
    membros_por_sentido: dict[str, list[str]] = {}
    entradas: dict[str, tuple[str, str, str, str | None]] = {}
    lidos = ignorados = 0
    with Path(arquivo_tsv).open("r", encoding="utf-8-sig", newline="") as arquivo:
        for linha in arquivo:
            valor = linha.rstrip("\r\n")
            if not valor or valor.startswith("#"):
                continue
            partes = valor.split("\t")
            if len(partes) != 3:
                ignorados += 1
                continue
            synset, tipo, lema = partes
            if tipo != "lemma" or not synset or not lema.strip():
                ignorados += 1
                continue
            lidos += 1
            codigo_pos = synset.rsplit("-", 1)[-1][:1]
            classe = pos_map.get(codigo_pos)
            if classe is None:
                ignorados += 1
                continue
            identificador = _id(fonte, classe, lema)
            entradas[identificador] = (identificador, lema, classe, None)
            membros_por_sentido.setdefault(synset, [])
            if identificador not in membros_por_sentido[synset]:
                membros_por_sentido[synset].append(identificador)
            if limite is not None and lidos >= limite:
                break

    _gravar_entradas(lexicon, fonte, entradas.values())
    with lexicon._lock, lexicon._db:
        lexicon._db.executemany(
            """
            INSERT INTO sentidos(id, fonte_id, classe, definicao, licenca, versao_fonte)
            VALUES (?, ?, ?, NULL, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                fonte_id=excluded.fonte_id, classe=excluded.classe,
                licenca=excluded.licenca, versao_fonte=excluded.versao_fonte
            """,
            (
                (
                    synset, fonte,
                    pos_map.get(synset.rsplit("-", 1)[-1][:1], "desconhecida"),
                    lexicon._db.execute(
                        "SELECT licenca FROM fontes WHERE id=?", (fonte,)
                    ).fetchone()[0],
                    lexicon._db.execute(
                        "SELECT versao FROM fontes WHERE id=?", (fonte,)
                    ).fetchone()[0],
                )
                for synset in membros_por_sentido
            ),
        )
        for synset in membros_por_sentido:
            lexicon._db.execute(
                "DELETE FROM sentido_entradas WHERE sentido_id=?", (synset,)
            )
        lexicon._db.executemany(
            """
            INSERT OR IGNORE INTO sentido_entradas(sentido_id, entrada_id, ordem)
            VALUES (?, ?, ?)
            """,
            (
                (synset, entrada_id, ordem)
                for synset, ids in membros_por_sentido.items()
                for ordem, entrada_id in enumerate(ids)
            ),
        )
        lexicon._limpar_cache()
    return ResultadoImportacao(
        fonte, lidos, len(entradas), sentidos_importados=len(membros_por_sentido),
        ignorados=ignorados,
    )


def _local_name(valor: object) -> str:
    texto = str(valor)
    return texto.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def importar_openwordnet_ttl(
    lexicon: Lexicon, arquivo_palavras: str | Path,
    arquivo_synsets: str | Path, arquivo_palavras_sentido: str | Path,
    arquivo_relacoes: str | Path, *, versao: str,
    arquivo_morfosemantico: str | Path | None = None,
    arquivo_same_as: str | Path | None = None,
    confirmar_direitos: bool = False,
) -> ResultadoImportacao:
    """Importa OpenWordNet-PT Turtle: lemas, glossas, sentidos e relações.

    Requer rdflib (pip install lume-lang[rdf]). Todos os arquivos são locais.
    """
    try:
        from rdflib import Graph
    except ImportError as erro:
        raise RuntimeError(
            "importação Turtle requer o extra opcional: pip install lume-lang[rdf]"
        ) from erro

    fonte = "openwordnet-pt"
    _registrar_fonte(
        lexicon, identificador=fonte, nome="OpenWordNet-PT (dados Turtle oficiais)",
        licenca="CC BY 4.0",
        versao=versao, url="https://github.com/own-pt/openWordnet-PT",
        atribuicao=(
            "OpenWordNet-PT; atribuir aos autores conforme README upstream; "
            "indicar modificações e manter referência à CC BY 4.0."
        ),
        confirmar_direitos=confirmar_direitos,
    )
    pos_map = {
        "n": "substantivo", "v": "verbo", "a": "adjetivo",
        "s": "adjetivo", "r": "adverbio",
    }

    grafo = Graph()
    grafo.parse(str(arquivo_palavras), format="turtle")
    dados_palavras: dict[object, dict[str, str]] = {}
    palavra_do_sentido: dict[object, object] = {}
    for sujeito, predicado, objeto in grafo:
        nome = _local_name(predicado)
        if nome == "lemma":
            dados_palavras.setdefault(sujeito, {})["lema"] = str(objeto)
        elif nome == "pos":
            dados_palavras.setdefault(sujeito, {})["pos"] = str(objeto)
        elif nome == "word":
            palavra_do_sentido[sujeito] = objeto
    del grafo

    id_por_uri: dict[object, str] = {}
    lote: list[tuple[str, str, str, str | None]] = []
    for uri, dados in dados_palavras.items():
        lema = dados.get("lema", "").strip()
        classe = pos_map.get(dados.get("pos", ""))
        if not lema or not classe:
            continue
        identificador = _id(fonte, classe, lema)
        id_por_uri[uri] = identificador
        lote.append((identificador, lema, classe, None))
    _gravar_entradas(lexicon, fonte, lote)

    grafo = Graph()
    grafo.parse(str(arquivo_synsets), format="turtle")
    metadados_sentidos: dict[object, dict[str, str]] = {}
    for sujeito, predicado, objeto in grafo:
        nome = _local_name(predicado)
        if nome == "synsetId":
            metadados_sentidos.setdefault(sujeito, {})["id"] = str(objeto)
        elif nome == "gloss":
            item = metadados_sentidos.setdefault(sujeito, {})
            gloss = str(objeto).strip()
            if gloss:
                item["gloss"] = (item.get("gloss", "") + ("; " if item.get("gloss") else "") + gloss)
        elif nome == "type":
            tipo = _local_name(objeto)
            classe = {
                "NounSynset": "substantivo", "VerbSynset": "verbo",
                "AdjectiveSynset": "adjetivo", "AdjectiveSatelliteSynset": "adjetivo",
                "AdverbSynset": "adverbio",
            }.get(tipo)
            if classe:
                metadados_sentidos.setdefault(sujeito, {})["classe"] = classe
    del grafo

    grafo = Graph()
    grafo.parse(str(arquivo_palavras_sentido), format="turtle")
    membros_uri: dict[object, list[object]] = {}
    for sujeito, predicado, objeto in grafo:
        if _local_name(predicado) == "containsWordSense":
            membros_uri.setdefault(sujeito, []).append(objeto)
    del grafo

    id_sentido_por_uri: dict[object, str] = {}
    membros_por_sentido: dict[str, list[str]] = {}
    glossas_por_sentido: dict[str, str | None] = {}
    classes_por_sentido: dict[str, str] = {}
    for uri, dados in metadados_sentidos.items():
        identificador = dados.get("id") or _local_name(uri).removeprefix("synset-")
        classe = dados.get("classe") or pos_map.get(
            identificador.rsplit("-", 1)[-1], "desconhecida"
        )
        id_sentido_por_uri[uri] = identificador
        classes_por_sentido[identificador] = classe
        glossas_por_sentido[identificador] = dados.get("gloss")
        membros: list[str] = []
        for uri_sense in membros_uri.get(uri, ()):
            uri_palavra = palavra_do_sentido.get(uri_sense)
            entrada_id = id_por_uri.get(uri_palavra)
            if entrada_id and entrada_id not in membros:
                membros.append(entrada_id)
        if membros:
            membros_por_sentido[identificador] = membros

    with lexicon._lock, lexicon._db:
        fonte_meta = lexicon._db.execute(
            "SELECT licenca, versao FROM fontes WHERE id=?", (fonte,)
        ).fetchone()
        lexicon._db.executemany(
            """
            INSERT INTO sentidos(id, fonte_id, classe, definicao, licenca, versao_fonte)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                fonte_id=excluded.fonte_id, classe=excluded.classe,
                definicao=excluded.definicao, licenca=excluded.licenca,
                versao_fonte=excluded.versao_fonte
            """,
            (
                (
                    identificador, fonte, classes_por_sentido[identificador],
                    glossas_por_sentido.get(identificador),
                    fonte_meta["licenca"], fonte_meta["versao"],
                )
                for identificador in membros_por_sentido
            ),
        )
        for identificador in membros_por_sentido:
            lexicon._db.execute(
                "DELETE FROM sentido_entradas WHERE sentido_id=?", (identificador,)
            )
        lexicon._db.executemany(
            """
            INSERT OR IGNORE INTO sentido_entradas(sentido_id, entrada_id, ordem)
            VALUES (?, ?, ?)
            """,
            (
                (identificador, entrada_id, ordem)
                for identificador, membros in membros_por_sentido.items()
                for ordem, entrada_id in enumerate(membros)
            ),
        )
        lexicon._limpar_cache()

    membros_por_uri = {
        uri: membros_por_sentido.get(identificador, [])
        for uri, identificador in id_sentido_por_uri.items()
    }
    for uri, membros in membros_uri.items():
        if uri not in membros_por_uri:
            continue
        for uri_sense in membros:
            uri_palavra = palavra_do_sentido.get(uri_sense)
            entrada_id = id_por_uri.get(uri_palavra)
            if entrada_id and entrada_id not in membros_por_uri[uri]:
                membros_por_uri[uri].append(entrada_id)

    relacoes_lote: list[tuple[str, str, str, str, str, str]] = []
    total_relacoes = 0
    arquivos_relacionais = (arquivo_relacoes, arquivo_morfosemantico, arquivo_same_as)
    for arquivo_relacional in arquivos_relacionais:
        if arquivo_relacional is None:
            continue
        grafo = Graph()
        grafo.parse(str(arquivo_relacional), format="turtle")
        for sujeito, predicado, objeto in grafo:
            tipo = _local_name(predicado)
            if tipo in {"type", "label"}:
                continue
            origem = membros_por_uri.get(sujeito)
            destino = membros_por_uri.get(objeto)
            if origem is None:
                uri_palavra = palavra_do_sentido.get(sujeito)
                entrada_id = id_por_uri.get(uri_palavra)
                origem = [entrada_id] if entrada_id else []
            if destino is None:
                uri_palavra = palavra_do_sentido.get(objeto)
                entrada_id = id_por_uri.get(uri_palavra)
                destino = [entrada_id] if entrada_id else []
            for origem_id in origem:
                for destino_id in destino:
                    if origem_id and destino_id and origem_id != destino_id:
                        relacoes_lote.append((
                            origem_id, destino_id, tipo, fonte,
                            fonte_meta["licenca"], fonte_meta["versao"],
                        ))
            if len(relacoes_lote) >= 5000:
                with lexicon._lock, lexicon._db:
                    lexicon._db.executemany(
                        """
                        INSERT INTO relacoes
                            (origem_id, destino_id, tipo, fonte_id, licenca, versao_fonte)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(origem_id, destino_id, tipo, fonte_id) DO UPDATE SET
                            licenca=excluded.licenca, versao_fonte=excluded.versao_fonte
                        """,
                        relacoes_lote,
                    )
                total_relacoes += len(relacoes_lote)
                relacoes_lote.clear()
        del grafo
    if relacoes_lote:
        with lexicon._lock, lexicon._db:
            lexicon._db.executemany(
                """
                INSERT INTO relacoes
                    (origem_id, destino_id, tipo, fonte_id, licenca, versao_fonte)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(origem_id, destino_id, tipo, fonte_id) DO UPDATE SET
                    licenca=excluded.licenca, versao_fonte=excluded.versao_fonte
                """,
                relacoes_lote,
            )
        total_relacoes += len(relacoes_lote)
    del grafo
    with lexicon._lock:
        lexicon._limpar_cache()
    return ResultadoImportacao(
        fonte, len(dados_palavras), len(lote),
        sentidos_importados=len(membros_por_sentido), relacoes_importadas=total_relacoes,
    )


def importar_fserb_verbos(
    lexicon: Lexicon, arquivo_verbos: str | Path, *,
    versao: str, confirmar_direitos: bool = False,
    limite: int | None = None,
) -> ResultadoImportacao:
    """Importa a lista de verbos como lemas verbais, sem inferir conjugações."""
    fonte = "fserb-pt-br-verbos"
    _registrar_fonte(
        lexicon, identificador=fonte, nome="fserb/pt-br — listas/verbos",
        licenca="MIT (licença declarada no repositório; procedência agregada pendente)",
        versao=versao, url="https://github.com/fserb/pt-br",
        atribuicao="Copyright 2021 Fernando Serboncini; preservar LICENSE upstream.",
        confirmar_direitos=confirmar_direitos,
    )
    vistos: set[str] = set()
    lote: list[tuple[str, str, str, str | None]] = []
    lidos = importados = ignorados = 0
    for verbo in _linhas(arquivo_verbos):
        lidos += 1
        termo = normalizar_forma(verbo)
        if termo in vistos:
            ignorados += 1
            continue
        vistos.add(termo)
        lote.append((_id(fonte, "verbo", verbo), verbo, "verbo", None))
        if len(lote) >= 2000:
            importados += _gravar_entradas(lexicon, fonte, lote)
            lote.clear()
        if limite is not None and lidos >= limite:
            break
    importados += _gravar_entradas(lexicon, fonte, lote)
    return ResultadoImportacao(fonte, lidos, importados, ignorados=ignorados)


def importar_fserb_icf(
    lexicon: Lexicon, arquivo_icf: str | Path, *,
    versao: str, confirmar_direitos: bool = False,
    limite: int | None = None,
) -> ResultadoImportacao:
    """Importa pares palavra,pontuação ICF em lotes, sem guardá-los na RAM."""
    import math

    fonte = "fserb-pt-br-icf"
    _registrar_fonte(
        lexicon, identificador=fonte, nome="fserb/pt-br — icf",
        licenca="MIT (licença declarada no repositório; procedência agregada pendente)",
        versao=versao, url="https://github.com/fserb/pt-br",
        atribuicao="Copyright 2021 Fernando Serboncini; preservar LICENSE upstream.",
        confirmar_direitos=confirmar_direitos,
    )
    lidos = importados = ignorados = 0
    lote: list[tuple[str, str, float, str, str]] = []
    with lexicon._lock, lexicon._db:
        fonte_meta = lexicon._db.execute(
            "SELECT verificada, versao FROM fontes WHERE id=?", (fonte,)
        ).fetchone()
        if fonte_meta is None or not fonte_meta["verificada"]:
            raise PermissionError("fonte ICF não verificada para importação")
        with Path(arquivo_icf).open("r", encoding="utf-8-sig", newline="") as arquivo:
            for linha in arquivo:
                valor = linha.strip()
                if not valor:
                    continue
                lidos += 1
                try:
                    palavra, pontuacao_texto = valor.rsplit(",", 1)
                    pontuacao = float(pontuacao_texto)
                    if not palavra.strip() or not math.isfinite(pontuacao) or pontuacao < 0:
                        raise ValueError
                except ValueError:
                    ignorados += 1
                    continue
                lote.append((
                    normalizar_forma(palavra), palavra, pontuacao,
                    fonte, fonte_meta["versao"],
                ))
                if len(lote) >= 5000:
                    lexicon._db.executemany(
                        """
                        INSERT INTO frequencias
                            (forma_normalizada, forma_original, valor, fonte_id, versao_fonte)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(forma_normalizada, fonte_id) DO UPDATE SET
                            forma_original=excluded.forma_original, valor=excluded.valor,
                            versao_fonte=excluded.versao_fonte
                        """,
                        lote,
                    )
                    importados += len(lote)
                    lote.clear()
                if limite is not None and lidos >= limite:
                    break
        if lote:
            lexicon._db.executemany(
                """
                INSERT INTO frequencias
                    (forma_normalizada, forma_original, valor, fonte_id, versao_fonte)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(forma_normalizada, fonte_id) DO UPDATE SET
                    forma_original=excluded.forma_original, valor=excluded.valor,
                    versao_fonte=excluded.versao_fonte
                """,
                lote,
            )
            importados += len(lote)
    return ResultadoImportacao(fonte, lidos, importados, ignorados=ignorados)
