"""Permissões explícitas para recursos de rede da Lume."""

from __future__ import annotations

from urllib.parse import urlsplit

from .erros import ErroExecucao


class PermissoesRede:
    """Lista de permissões por host; negar é o comportamento padrão."""

    def __init__(self, hosts_permitidos: tuple[str, ...] | list[str] = ()) -> None:
        self._hosts = frozenset(self._normalizar_host(host) for host in hosts_permitidos)

    @staticmethod
    def _normalizar_host(host: str) -> str:
        if not isinstance(host, str):
            raise ValueError("hosts autorizados precisam ser textos")
        valor = host.strip().rstrip(".").casefold()
        if not valor or any(caractere.isspace() or caractere in "/:@?#" for caractere in valor):
            raise ValueError(f"host inválido na lista de permissões: {host!r}")
        return valor

    @property
    def hosts_permitidos(self) -> frozenset[str]:
        return self._hosts

    def permitir_host(self, host: str) -> None:
        self._hosts = self._hosts | {self._normalizar_host(host)}

    def revogar_host(self, host: str) -> None:
        self._hosts = self._hosts - {self._normalizar_host(host)}

    def autorizar_url(self, url: str) -> str:
        try:
            partes = urlsplit(url)
            host = (partes.hostname or "").rstrip(".").casefold()
            partes.port  # valida a porta, quando presente
        except (TypeError, ValueError) as erro:
            raise ErroExecucao("endereço de rede inválido") from erro
        if partes.scheme.casefold() not in {"http", "https"}:
            raise ErroExecucao("somente endereços HTTP e HTTPS são permitidos")
        if not host or partes.username is not None or partes.password is not None:
            raise ErroExecucao("o endereço precisa conter um host válido e não pode incluir credenciais")
        if host not in self._hosts:
            raise ErroExecucao(
                f"acesso externo bloqueado para '{host}'; autorize explicitamente esse host "
                "na configuração do interpretador ou com --permitir-rede"
            )
        return host
