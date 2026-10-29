"""The real HTTP transport (OD-0115, T-0010 W-1; HIO-ADR-0012). The only module in `src/` allowed to
import a network client (`tools/check_repo.py`, `imports`). It satisfies `Transport` and nothing else
in the repository wires it up yet.

Design choices, each deliberate:

- HTTPS only, with certificate and host-name verification from `ssl.create_default_context()`. The one
  exception is an explicit constructor opt-in (`allow_loopback_http=True`) for plain `http://127.0.0.1`,
  which exists for tests that run a local server. No other host is ever contacted over plain HTTP.
- GET only. The caller supplies `User-Agent` (required); there is no default identity.
- Built on `http.client`, not `urllib.request`: nothing reads `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` or
  `.netrc`, there is no cookie jar, no authentication handler and no automatic redirect handling. A
  caller header that carries credentials (`Authorization`, `Cookie`, `Proxy-Authorization`) is refused,
  as is a URL with embedded user information.
- `Accept-Encoding: identity` unless the caller says otherwise, so the body is the bytes the server sent
  and no decompression happens inside the transport.
- Redirects (301, 302, 303, 307, 308 with a `Location`) are followed by hand, at most `max_redirects`
  times, only to https (or loopback http under the opt-in). The caller's headers are re-sent unchanged.
  `final_url` is the URL that produced the returned response.
- A body larger than `max_body_bytes` is refused with `TransportError`; it is never truncated.
- `timeout` bounds the connect and each socket read; `deadline` bounds the whole call, redirects
  included, so a server that drips bytes cannot hold the caller indefinitely.
- An HTTP error status is a response, not an exception: `run.py` classifies it. `TransportError` is for
  connection, timeout, TLS, protocol, policy and size failures only.
"""

from __future__ import annotations

import http.client
import ssl
import time
from collections.abc import Mapping
from urllib.parse import urldefrag, urljoin, urlsplit

from hio.sources.transport import HttpResponse, TransportError

LOOPBACK_HOST = "127.0.0.1"
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
FORBIDDEN_REQUEST_HEADERS = frozenset({"authorization", "cookie", "proxy-authorization"})
_CHUNK = 64 * 1024


class HttpTransport:
    def __init__(
        self,
        *,
        timeout: float = 30.0,
        deadline: float = 120.0,
        max_body_bytes: int = 32 * 1024 * 1024,
        max_redirects: int = 3,
        allow_loopback_http: bool = False,
    ) -> None:
        if timeout <= 0 or deadline <= 0 or max_body_bytes <= 0 or max_redirects < 0:
            raise ValueError("timeout, deadline and max_body_bytes must be positive; max_redirects >= 0")
        self.timeout = timeout
        self.deadline = deadline
        self.max_body_bytes = max_body_bytes
        self.max_redirects = max_redirects
        self.allow_loopback_http = allow_loopback_http
        self._context = ssl.create_default_context()  # verifies certificates and host names

    def get(self, url: str, headers: Mapping[str, str]) -> HttpResponse:
        request_headers = self._request_headers(headers)
        expires = time.monotonic() + self.deadline
        current = url
        for hop in range(self.max_redirects + 1):
            response = self._fetch_once(current, request_headers, expires)
            location = _header(response.headers, "location")
            if response.status in REDIRECT_STATUSES and location is not None:
                if hop == self.max_redirects:
                    raise TransportError(f"more than {self.max_redirects} redirects from {url}")
                current = urljoin(current, location)
                continue
            return response
        raise AssertionError("unreachable")  # pragma: no cover

    def _request_headers(self, headers: Mapping[str, str]) -> dict[str, str]:
        out = dict(headers)
        names = {k.lower() for k in out}
        if "user-agent" not in names or not out[next(k for k in out if k.lower() == "user-agent")].strip():
            raise TransportError("a non-empty User-Agent header is required")
        bad = sorted(names & FORBIDDEN_REQUEST_HEADERS)
        if bad:
            raise TransportError(f"credential-bearing request headers are refused: {bad}")
        if "accept-encoding" not in names:
            out["Accept-Encoding"] = "identity"
        out["Connection"] = "close"
        return out

    def _check_url(self, url: str) -> tuple[str, str, int | None, str]:
        """Return (scheme, host, port, request target) or raise TransportError."""
        try:
            parts = urlsplit(urldefrag(url).url)
            port = parts.port
        except ValueError as exc:
            raise TransportError(f"invalid URL {url!r}: {exc}") from exc
        host = parts.hostname
        if not host:
            raise TransportError(f"URL has no host: {url!r}")
        if parts.username is not None or parts.password is not None:
            raise TransportError("URLs with embedded credentials are refused")
        loopback_http = parts.scheme == "http" and self.allow_loopback_http and host == LOOPBACK_HOST
        if parts.scheme != "https" and not loopback_http:
            raise TransportError(
                f"refused: only https is allowed, got {parts.scheme or 'no scheme'}://{host}"
            )
        target = parts.path or "/"
        if parts.query:
            target += "?" + parts.query
        return parts.scheme, host, port, target

    def _fetch_once(self, url: str, headers: dict[str, str], expires: float) -> HttpResponse:
        scheme, host, port, target = self._check_url(url)
        final_url = urldefrag(url).url
        remaining = expires - time.monotonic()
        if remaining <= 0:
            raise TransportError(f"deadline of {self.deadline}s exceeded for {url}")
        timeout = min(self.timeout, remaining)
        if scheme == "https":
            conn: http.client.HTTPConnection = http.client.HTTPSConnection(
                host, port, timeout=timeout, context=self._context
            )
        else:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)
        try:
            conn.request("GET", target, headers=headers)
            resp = conn.getresponse()
            declared = resp.getheader("Content-Length")
            if declared is not None and declared.strip().isdigit() and int(declared) > self.max_body_bytes:
                raise TransportError(f"body of {declared} bytes exceeds the {self.max_body_bytes} byte limit")
            chunks: list[bytes] = []
            total = 0
            while True:
                if time.monotonic() > expires:
                    raise TransportError(f"deadline of {self.deadline}s exceeded reading {url}")
                chunk = resp.read1(_CHUNK)  # one socket read at a time, so the deadline is re-checked
                if not chunk:
                    break
                total += len(chunk)
                if total > self.max_body_bytes:
                    raise TransportError(f"body exceeds the {self.max_body_bytes} byte limit")
                chunks.append(chunk)
            return HttpResponse(
                status=resp.status,
                headers=tuple((k, v) for k, v in resp.getheaders()),
                body=b"".join(chunks),
                final_url=final_url,
            )
        except TransportError:
            raise
        except (OSError, http.client.HTTPException, ValueError) as exc:  # incl. TimeoutError, SSLError
            raise TransportError(f"{type(exc).__name__} fetching {url}: {exc}") from exc
        finally:
            conn.close()


def _header(headers: tuple[tuple[str, str], ...], name: str) -> str | None:
    for key, value in headers:
        if key.lower() == name:
            return value
    return None
