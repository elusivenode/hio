"""GitHub-OIDC federated authentication to Azure (T-0010 W-2; OD-0117 decision 4). Not wired to any job.

STATUS: UNVERIFIED against a real tenant. Azure immutability enforcement and the C5 suitability of
whole-second `Last-Modified` stay UNVERIFIED pending H4 (OD-0117); nothing here establishes either.

A GitHub Actions job asks GitHub for an OIDC identity token for the audience
`api://AzureADTokenExchange`, using the job's `ACTIONS_ID_TOKEN_REQUEST_URL` and
`ACTIONS_ID_TOKEN_REQUEST_TOKEN`; `azure.identity.ClientAssertionCredential` exchanges that token for
an Azure access token through a federated credential. There is no secret to store.

Rules this module keeps:

- The tenant id and client id are constructor parameters. The caller reads them from the environment;
  no identifier is a literal here.
- No `DefaultAzureCredential` and no credential chain: exactly one credential type, and nothing falls
  back to another when it fails.
- The request token and the identity token are never put in a repr, a log or an exception message.
  Errors carry a fixed description (and at most an exception type name), and are raised `from None`.
- The GitHub request is https only, follows no redirect, has a connect/read timeout and an overall
  deadline, and reads a bounded body.
- The environment mapping and the HTTP fetch are injectable, so tests use neither the real environment
  nor a network. The only network import is `http.client`, allowed in this file by `tools/check_repo.py`.
"""

from __future__ import annotations

import http.client
import json
import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit

from azure.identity import ClientAssertionCredential

AUDIENCE = "api://AzureADTokenExchange"
URL_VARIABLE = "ACTIONS_ID_TOKEN_REQUEST_URL"
REQUEST_TOKEN_VARIABLE = "ACTIONS_ID_TOKEN_REQUEST_TOKEN"
TIMEOUT_SECONDS = 10.0
DEADLINE_SECONDS = 30.0
MAX_BODY_BYTES = 64 * 1024

# fetch(url, request_token, timeout, deadline) -> response body bytes
Fetch = Callable[[str, str, float, float], bytes]


class OidcError(Exception):
    """The GitHub OIDC identity token could not be obtained. The message never contains a token or a URL."""


def fetch_https(url: str, request_token: str, timeout: float, deadline: float) -> bytes:
    """GET `url` with a bearer request token; https only, no redirects, bounded time and size."""
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        raise OidcError("the OIDC request URL must be https")
    target = parts.path or "/"
    if parts.query:
        target += "?" + parts.query
    started = time.monotonic()
    try:
        conn = http.client.HTTPSConnection(parts.hostname, parts.port, timeout=timeout)
        try:
            conn.request(
                "GET",
                target,
                headers={"Authorization": f"bearer {request_token}", "Accept": "application/json"},
            )
            response = conn.getresponse()
            if response.status != 200:
                raise OidcError(f"GitHub answered the OIDC request with HTTP {response.status}")
            body = bytearray()
            while chunk := response.read(8192):
                body += chunk
                if len(body) > MAX_BODY_BYTES:
                    raise OidcError("the OIDC response exceeds the size limit")
                if time.monotonic() - started > deadline:
                    raise OidcError("the OIDC request exceeded its deadline")
            return bytes(body)
        finally:
            conn.close()
    except OidcError:
        raise
    except (OSError, http.client.HTTPException) as error:
        raise OidcError(f"the OIDC request failed ({type(error).__name__})") from None


class GitHubOidcAssertion:
    """A callable that returns a fresh GitHub Actions OIDC identity token (the client assertion)."""

    def __init__(
        self,
        environ: Mapping[str, str],
        *,
        audience: str = AUDIENCE,
        fetch: Fetch = fetch_https,
        timeout: float = TIMEOUT_SECONDS,
        deadline: float = DEADLINE_SECONDS,
    ) -> None:
        if timeout <= 0 or deadline <= 0:
            raise ValueError("timeout and deadline must be positive")
        self._environ = environ
        self._audience = audience
        self._fetch = fetch
        self._timeout = timeout
        self._deadline = deadline
        self._request()  # refuse at construction when the job has no OIDC permission

    def __repr__(self) -> str:
        return "GitHubOidcAssertion()"

    def _request(self) -> tuple[str, str]:
        url = self._environ.get(URL_VARIABLE)
        request_token = self._environ.get(REQUEST_TOKEN_VARIABLE)
        if not url or not request_token:
            raise OidcError(
                f"{URL_VARIABLE} and {REQUEST_TOKEN_VARIABLE} are required "
                "(the job needs the `id-token: write` permission)"
            )
        parts = urlsplit(url)
        query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "audience"]
        query.append(("audience", self._audience))
        return parts._replace(query=urlencode(query)).geturl(), request_token

    def __call__(self) -> str:
        url, request_token = self._request()
        body = self._fetch(url, request_token, self._timeout, self._deadline)
        try:
            token = json.loads(body).get("value")
        except (ValueError, AttributeError):
            raise OidcError("the OIDC response is not the expected JSON") from None
        if not isinstance(token, str) or not token:
            raise OidcError("the OIDC response carries no identity token")
        return token


def github_oidc_credential(
    tenant_id: str,
    client_id: str,
    environ: Mapping[str, str],
    *,
    assertion: Callable[[], str] | None = None,
    credential_factory: Callable[..., Any] = ClientAssertionCredential,
) -> Any:
    """The one credential HIO uses: a `ClientAssertionCredential` whose assertion is the GitHub OIDC
    token. `tenant_id` and `client_id` come from the caller's environment; empty values are refused.
    Constructing it makes no network request."""
    if not tenant_id or not client_id:
        raise ValueError("tenant_id and client_id are required")
    return credential_factory(tenant_id, client_id, assertion or GitHubOidcAssertion(environ))
