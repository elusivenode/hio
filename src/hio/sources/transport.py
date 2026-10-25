"""The injected transport. S1b-1.0 has only a scripted fixture transport: no real network client
exists in `src/` (check_repo forbids one), and a real one needs its own authorisation (T-0009 §8)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: tuple[tuple[str, str], ...]  # as received, in order
    body: bytes
    final_url: str


class TransportError(Exception):
    """The request did not produce a response (connection, timeout, TLS, protocol)."""


class Transport(Protocol):
    def get(self, url: str, headers: Mapping[str, str]) -> HttpResponse: ...


class FixtureTransport:
    """Serves scripted responses per URL, in order. A URL with nothing left, or never scripted,
    raises TransportError. Used only with synthetic fixtures."""

    def __init__(self, script: Mapping[str, Sequence[HttpResponse | TransportError]]) -> None:
        self._script = {u: list(r) for u, r in script.items()}
        self.requests: list[tuple[str, dict[str, str]]] = []

    def get(self, url: str, headers: Mapping[str, str]) -> HttpResponse:
        self.requests.append((url, dict(headers)))
        queue = self._script.get(url)
        if not queue:
            raise TransportError(f"no scripted response for {url}")
        item = queue.pop(0)
        if isinstance(item, TransportError):
            raise item
        return item
