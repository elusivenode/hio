"""T-0010 W-2: GitHub-OIDC federated authentication, tested with an injected environment and an injected
fetch. No credential is acquired, no network is touched, the real environment is never read.

Azure immutability enforcement and the C5 suitability of whole-second Last-Modified are UNVERIFIED
pending H4 (OD-0117); nothing here claims either.
"""

from __future__ import annotations

import ast
import http.client
import json
from pathlib import Path
from typing import ClassVar
from urllib.parse import parse_qs, urlsplit

import pytest
from azure.identity import ClientAssertionCredential

from hio.storage import azure_auth
from hio.storage.azure_auth import AUDIENCE, GitHubOidcAssertion, OidcError, github_oidc_credential

JWT = "jwt-SENTINEL-9Zq"  # fake identity token; short on purpose so it is never mistaken for a secret
REQ = "req-SENTINEL-4Kd"  # fake request token
URL = "https://actions.example.invalid/idtoken?api-version=2.0&x=1"
TENANT = "tenant-for-tests"
CLIENT = "client-for-tests"


def env(**override):
    base = {azure_auth.URL_VARIABLE: URL, azure_auth.REQUEST_TOKEN_VARIABLE: REQ}
    base.update(override)
    return {k: v for k, v in base.items() if v is not None}


class Fetch:
    def __init__(self, body: bytes | None = None, error: BaseException | None = None) -> None:
        self.body = json.dumps({"value": JWT}).encode() if body is None else body
        self.error = error
        self.calls: list[tuple[str, str, float, float]] = []

    def __call__(self, url, request_token, timeout, deadline):
        self.calls.append((url, request_token, timeout, deadline))
        if self.error:
            raise self.error
        return self.body


def test_the_assertion_callback_returns_the_github_token_for_the_azure_audience():
    fetch = Fetch()
    assertion = GitHubOidcAssertion(env(), fetch=fetch)
    assert assertion() == JWT
    ((url, request_token, timeout, deadline),) = fetch.calls
    query = parse_qs(urlsplit(url).query)
    assert query["audience"] == [AUDIENCE] == ["api://AzureADTokenExchange"]
    assert query["api-version"] == ["2.0"] and query["x"] == ["1"]  # the Actions-provided query is kept
    assert urlsplit(url).netloc == "actions.example.invalid"
    assert request_token == REQ
    assert 0 < timeout <= 60 and 0 < deadline <= 120  # bounded


def test_an_existing_audience_in_the_request_url_is_replaced_not_duplicated():
    fetch = Fetch()
    GitHubOidcAssertion(env(**{azure_auth.URL_VARIABLE: URL + "&audience=evil"}), fetch=fetch)()
    assert parse_qs(urlsplit(fetch.calls[0][0]).query)["audience"] == [AUDIENCE]


def test_every_call_fetches_a_fresh_token():
    fetch = Fetch()
    assertion = GitHubOidcAssertion(env(), fetch=fetch)
    assertion()
    assertion()
    assert len(fetch.calls) == 2


@pytest.mark.parametrize("missing", [azure_auth.URL_VARIABLE, azure_auth.REQUEST_TOKEN_VARIABLE])
@pytest.mark.parametrize("value", [None, ""])
def test_missing_or_empty_oidc_environment_is_refused_at_construction(missing, value):
    fetch = Fetch()
    with pytest.raises(OidcError, match="id-token: write"):
        GitHubOidcAssertion(env(**{missing: value}), fetch=fetch)
    assert fetch.calls == []  # nothing was requested


def test_a_variable_removed_after_construction_is_refused_at_call_time():
    environ = env()
    assertion = GitHubOidcAssertion(environ, fetch=Fetch())
    del environ[azure_auth.REQUEST_TOKEN_VARIABLE]
    with pytest.raises(OidcError):
        assertion()


@pytest.mark.parametrize(
    "body", [b"not json", b"[]", b"{}", b'{"value": ""}', b'{"value": 7}', b'{"value": null}', b""]
)
def test_a_malformed_github_response_is_refused(body):
    with pytest.raises(OidcError):
        GitHubOidcAssertion(env(), fetch=Fetch(body=body))()


def test_no_token_appears_in_repr_str_or_exceptions():
    assertion = GitHubOidcAssertion(env(), fetch=Fetch())
    for shown in (repr(assertion), str(assertion)):
        assert REQ not in shown and JWT not in shown and "actions.example" not in shown
    failures = [
        lambda: GitHubOidcAssertion(env(**{azure_auth.REQUEST_TOKEN_VARIABLE: None}), fetch=Fetch()),
        lambda: GitHubOidcAssertion(env(), fetch=Fetch(body=b'{"value": 5}'))(),
        lambda: GitHubOidcAssertion(env(), fetch=Fetch(body=JWT.encode()))(),
        lambda: GitHubOidcAssertion(env(), fetch=azure_auth.fetch_https)(),
    ]
    for failure in failures:
        with pytest.raises(OidcError) as raised:
            failure()
        text = f"{raised.value!s} {raised.value!r} {raised.value.__cause__!r} {raised.value.__context__!r}"
        assert REQ not in text and JWT not in text and "actions.example" not in text
        assert raised.value.__suppress_context__ or raised.value.__context__ is None


def test_the_credential_is_a_client_assertion_credential_wired_to_the_callback():
    assertion = GitHubOidcAssertion(env(), fetch=Fetch())
    credential = github_oidc_credential(TENANT, CLIENT, env(), assertion=assertion)
    assert type(credential) is ClientAssertionCredential  # not DefaultAzureCredential, not a chain
    assert JWT not in repr(credential) and REQ not in repr(credential)
    credential.close()


def test_the_credential_factory_receives_tenant_client_and_the_assertion():
    seen = []
    assertion = GitHubOidcAssertion(env(), fetch=Fetch())

    def factory(*args, **kwargs):
        seen.append((args, kwargs))
        return object()

    github_oidc_credential(TENANT, CLIENT, env(), assertion=assertion, credential_factory=factory)
    assert seen == [((TENANT, CLIENT, assertion), {})]


def test_the_default_assertion_is_built_from_the_environment_and_refused_without_it():
    seen = []

    def factory(_tenant, _client, func):
        seen.append(func)
        return object()

    github_oidc_credential(TENANT, CLIENT, env(), credential_factory=factory)
    assert isinstance(seen[0], GitHubOidcAssertion)
    with pytest.raises(OidcError):
        github_oidc_credential(TENANT, CLIENT, {}, credential_factory=factory)


@pytest.mark.parametrize("tenant,client", [("", CLIENT), (TENANT, ""), ("", "")])
def test_empty_tenant_or_client_is_refused(tenant, client):
    with pytest.raises(ValueError):
        github_oidc_credential(tenant, client, env(), assertion=lambda: JWT)


def test_no_fallback_credential_exists_in_the_module():
    tree = ast.parse(Path(azure_auth.__file__).read_text())
    imported = {
        (node.module, alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if node.module and node.module.startswith("azure")
    }
    assert imported == {("azure.identity", "ClientAssertionCredential")}  # the only Azure import, no chain
    assert not [n for n in vars(azure_auth) if "Default" in n or "Chained" in n]


def test_a_failed_assertion_does_not_fall_back_to_anything_else():
    fetch = Fetch(error=OidcError("injected"))
    assertion = GitHubOidcAssertion(env(), fetch=fetch)
    with pytest.raises(OidcError, match="injected"):
        assertion()
    assert len(fetch.calls) == 1  # no retry loop, no second source


# --- the default fetch: https only, bounded, no leakage (stdlib client replaced by a fake) --------------


class FakeResponse:
    def __init__(self, status=200, body=b"", chunk=8192):
        self.status, self._body, self._chunk = status, body, chunk

    def read(self, n):
        out, self._body = self._body[: min(n, self._chunk)], self._body[min(n, self._chunk) :]
        return out


class FakeConnection:
    instances: ClassVar[list[FakeConnection]] = []

    def __init__(self, host, port=None, timeout=None, response=None, error=None):
        self.host, self.port, self.timeout = host, port, timeout
        self.requests, self.closed = [], False
        self._response, self._error = response, error
        FakeConnection.instances.append(self)

    def request(self, method, target, headers=None):
        if self._error:
            raise self._error
        self.requests.append((method, target, headers))

    def getresponse(self):
        return self._response

    def close(self):
        self.closed = True


@pytest.fixture
def conn(monkeypatch):
    FakeConnection.instances = []
    config = {"response": FakeResponse(body=b'{"value": "x"}'), "error": None}
    monkeypatch.setattr(
        azure_auth.http.client,
        "HTTPSConnection",
        lambda host, port=None, timeout=None: FakeConnection(host, port, timeout, **config),
    )
    return config


@pytest.mark.usefixtures("conn")
def test_the_default_fetch_sends_a_bearer_get_over_https_with_a_timeout():
    body = azure_auth.fetch_https(URL + "&audience=a", REQ, 7.0, 20.0)
    assert body == b'{"value": "x"}'
    (c,) = FakeConnection.instances
    assert c.host == "actions.example.invalid" and c.timeout == 7.0 and c.closed
    ((method, target, headers),) = c.requests
    assert method == "GET" and target == "/idtoken?api-version=2.0&x=1&audience=a"
    assert headers["Authorization"] == f"bearer {REQ}"


@pytest.mark.usefixtures("conn")
@pytest.mark.parametrize(
    "url", ["http://actions.example.invalid/t", "ftp://x/t", "/relative", "https:///nohost"]
)
def test_the_default_fetch_refuses_non_https_urls_without_connecting(url):
    with pytest.raises(OidcError, match="https"):
        azure_auth.fetch_https(url, REQ, 5.0, 10.0)
    assert FakeConnection.instances == []


def test_the_default_fetch_does_not_follow_redirects(conn):
    conn["response"] = FakeResponse(status=302)
    with pytest.raises(OidcError, match="HTTP 302"):
        azure_auth.fetch_https(URL, REQ, 5.0, 10.0)
    assert len(FakeConnection.instances) == 1 and FakeConnection.instances[0].closed


def test_the_default_fetch_bounds_the_body(conn):
    conn["response"] = FakeResponse(body=b"x" * (azure_auth.MAX_BODY_BYTES + 1))
    with pytest.raises(OidcError, match="size"):
        azure_auth.fetch_https(URL, REQ, 5.0, 10.0)


def test_the_default_fetch_enforces_an_overall_deadline(conn, monkeypatch):
    conn["response"] = FakeResponse(body=b"x" * 100, chunk=10)
    ticks = iter(range(0, 1000, 5))
    monkeypatch.setattr(azure_auth.time, "monotonic", lambda: next(ticks))
    with pytest.raises(OidcError, match="deadline"):
        azure_auth.fetch_https(URL, REQ, 5.0, 12.0)


@pytest.mark.parametrize(
    "error", [TimeoutError("slow"), ConnectionResetError("x"), http.client.BadStatusLine("x")]
)
def test_the_default_fetch_turns_transport_failures_into_a_token_free_error(conn, error):
    conn["error"] = error
    with pytest.raises(OidcError) as raised:
        azure_auth.fetch_https(URL, REQ, 5.0, 10.0)
    assert REQ not in str(raised.value) and "actions.example" not in str(raised.value)
    assert raised.value.__cause__ is None and raised.value.__suppress_context__
    assert type(error).__name__ in str(raised.value)
