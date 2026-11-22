"""Cliente HTTP opcional da Lume; nunca é inicializado com permissões implícitas."""

from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
import ssl

from .erros import ErroExecucao
from .permissoes import PermissoesRede


class _SemRedirecionamento(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ClienteRede:
    """Operações HTTP(S) limitadas por host, tempo e tamanho de resposta."""

    LIMITE_RESPOSTA = 1_048_576

    def __init__(
        self,
        permissoes: PermissoesRede,
        timeout: float = 10.0,
        limite_resposta: int = LIMITE_RESPOSTA,
    ) -> None:
        if timeout <= 0 or timeout > 60:
            raise ValueError("timeout deve estar entre 0 e 60 segundos")
        if limite_resposta < 1 or limite_resposta > self.LIMITE_RESPOSTA:
            raise ValueError("limite de resposta deve estar entre 1 byte e 1 MiB")
        self.permissoes = permissoes
        self.timeout = timeout
        self.limite_resposta = limite_resposta
        contexto = ssl.create_default_context()
        self._opener = build_opener(_SemRedirecionamento(), HTTPSHandler(context=contexto))

    def requisitar(
        self,
        url: str,
        metodo: str = "GET",
        corpo: str | bytes | None = None,
        cabecalhos: dict[str, str] | None = None,
    ) -> bytes:
        self.permissoes.autorizar_url(url)
        if not isinstance(metodo, str):
            raise ErroExecucao("o método HTTP precisa ser um texto")
        metodo = metodo.upper()
        if metodo not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"}:
            raise ErroExecucao("método HTTP não permitido")
        if corpo is not None and not isinstance(corpo, (str, bytes)):
            raise ErroExecucao("o corpo HTTP precisa ser texto ou bytes")
        if cabecalhos is not None:
            if not isinstance(cabecalhos, dict) or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in cabecalhos.items()
            ):
                raise ErroExecucao("cabeçalhos HTTP precisam ser um dicionário de textos")
        dados = corpo.encode("utf-8") if isinstance(corpo, str) else corpo
        if dados is not None and len(dados) > self.limite_resposta:
            raise ErroExecucao("o corpo da requisição ultrapassa o limite de 1 MiB")
        try:
            requisicao = Request(url, data=dados, headers=cabecalhos or {}, method=metodo)
        except (TypeError, ValueError) as erro:
            raise ErroExecucao("requisição HTTP inválida") from erro
        try:
            with self._opener.open(requisicao, timeout=self.timeout) as resposta:
                dados_resposta = resposta.read(self.limite_resposta + 1)
        except HTTPError as erro:
            raise ErroExecucao(f"requisição HTTP falhou com status {erro.code}") from erro
        except (URLError, TimeoutError, OSError, ssl.SSLError) as erro:
            raise ErroExecucao(f"não foi possível concluir a conexão: {erro}") from erro
        if len(dados_resposta) > self.limite_resposta:
            raise ErroExecucao("a resposta externa ultrapassa o limite de 1 MiB")
        return dados_resposta

    def obter_texto(self, url: str) -> str:
        try:
            return self.requisitar(url).decode("utf-8")
        except UnicodeDecodeError as erro:
            raise ErroExecucao("a resposta externa não está codificada em UTF-8") from erro
