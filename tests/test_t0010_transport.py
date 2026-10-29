"""T-0010 W-1: the real HTTP transport (OD-0115), tested only against a local server on 127.0.0.1.

No test here may reach the internet: every request goes to 127.0.0.1, or is refused by policy before a
connection is attempted (the `.invalid` TLD never resolves).
"""

from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from hio.sources.http_transport import HttpTransport
from hio.sources.transport import HttpResponse, TransportError

UA = {"User-Agent": "hio-test/0 (synthetic)"}


class _Handler(BaseHTTPRequestHandler):
    server_version = "T"
    sys_version = ""

    def log_message(self, *args):  # silence
        pass

    def _send(self, status, body=b"", headers=(), length=True):
        self.send_response(status)
        for k, v in headers:
            self.send_header(k, v)
        if length:
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        srv = self.server
        srv.seen.append((self.path, dict(self.headers.items())))
        path = self.path
        if path == "/ok":
            self._send(200, b"hello", [("Content-Type", "text/plain")])
        elif path == "/order":
            self._send(
                200,
                b"x",
                [("X-B", "1"), ("X-A", "2"), ("X-B", "3"), ("X-C", "4")],
            )
        elif path in {"/404", "/500", "/429"}:
            self._send(int(path[1:]), b"nope", [("Retry-After", "7")])
        elif path.startswith("/size/"):
            self._send(200, b"z" * int(path.split("/")[2]))
        elif path.startswith("/nolength/"):
            self._send(200, b"z" * int(path.split("/")[2]), length=False)
        elif path.startswith("/redirect/"):
            n = int(path.split("/")[2])
            if n == 0:
                self._send(200, b"landed")
            else:
                self._send(302, headers=[("Location", f"/redirect/{n - 1}")])
        elif path == "/to-http":
            self._send(302, headers=[("Location", "http://example.invalid/x")])
        elif path == "/to-file":
            self._send(302, headers=[("Location", "file:///etc/passwd")])
        elif path == "/to-creds":
            self._send(302, headers=[("Location", "http://u:p@127.0.0.1:1/")])
        elif path == "/to-absolute":
            self._send(301, headers=[("Location", f"http://127.0.0.1:{srv.server_port}/ok#frag")])
        elif path == "/cross":
            self._send(302, headers=[("Location", f"http://127.0.0.1:{srv.other_port}/ok")])
        elif path == "/leave-and-return":
            self._send(302, headers=[("Location", f"http://127.0.0.1:{srv.other_port}/back")])
        elif path == "/back":
            self._send(302, headers=[("Location", f"http://127.0.0.1:{srv.other_port}/ok")])
        elif path == "/nolocation":
            self._send(302, b"moved")
        elif path == "/hang":
            srv.release.wait(10)
            self._send(200, b"late")
        elif path == "/drip":
            self.send_response(200)
            self.send_header("Content-Length", "50")
            self.end_headers()
            for _ in range(50):
                if srv.release.wait(0.1):
                    break
                self.wfile.write(b"d")
                self.wfile.flush()
        else:
            self._send(404, b"unknown")


def _serve():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    srv.daemon_threads = True
    srv.seen = []
    srv.release = threading.Event()
    srv.other_port = None
    thread = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    return srv, thread


def _stop(srv, thread):
    srv.release.set()
    srv.shutdown()
    srv.server_close()
    thread.join(5)


@pytest.fixture
def server():
    srv, thread = _serve()
    try:
        yield srv
    finally:
        _stop(srv, thread)


@pytest.fixture
def two_servers():
    """Two loopback servers on different ports: two origins, each recording the requests it receives."""
    first, t1 = _serve()
    second, t2 = _serve()
    first.other_port = second.server_port
    second.other_port = first.server_port
    try:
        yield first, second
    finally:
        _stop(first, t1)
        _stop(second, t2)


def _url(srv, path):
    return f"http://127.0.0.1:{srv.server_port}{path}"


def _loopback(**kw):
    return HttpTransport(allow_loopback_http=True, **kw)


# --- the happy path --------------------------------------------------------------------------------


def test_returns_status_headers_body_and_final_url(server):
    resp = _loopback().get(_url(server, "/ok"), UA)
    assert isinstance(resp, HttpResponse)
    assert resp.status == 200
    assert resp.body == b"hello"
    assert resp.final_url == _url(server, "/ok")
    assert ("Content-Type", "text/plain") in resp.headers
    assert isinstance(resp.headers, tuple)


def test_header_order_and_duplicates_are_preserved(server):
    resp = _loopback().get(_url(server, "/order"), UA)
    custom = [(k, v) for k, v in resp.headers if k.startswith("X-")]
    assert custom == [("X-B", "1"), ("X-A", "2"), ("X-B", "3"), ("X-C", "4")]


def test_request_is_a_get_with_the_callers_user_agent_and_nothing_ambient(server):
    _loopback().get(_url(server, "/ok?q=1"), {**UA, "Accept": "text/csv"})
    path, seen = server.seen[0]
    assert path == "/ok?q=1"
    assert seen["User-Agent"] == UA["User-Agent"]
    assert seen["Accept"] == "text/csv"
    assert seen["Accept-Encoding"] == "identity"
    assert seen["Host"] == f"127.0.0.1:{server.server_port}"
    lowered = {k.lower() for k in seen}
    assert not lowered & {"cookie", "authorization", "proxy-authorization"}


def test_proxy_environment_is_ignored(server, monkeypatch):
    for name in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "NO_PROXY"):
        monkeypatch.setenv(name, "http://127.0.0.1:9")
    assert _loopback().get(_url(server, "/ok"), UA).status == 200


# --- error statuses are responses -------------------------------------------------------------------


@pytest.mark.parametrize("status", [404, 429, 500])
def test_error_status_is_returned_not_raised(server, status):
    resp = _loopback().get(_url(server, f"/{status}"), UA)
    assert resp.status == status
    assert resp.body == b"nope"
    assert ("Retry-After", "7") in resp.headers


# --- size cap ---------------------------------------------------------------------------------------


def test_body_at_the_limit_is_returned(server):
    resp = _loopback(max_body_bytes=1000).get(_url(server, "/size/1000"), UA)
    assert len(resp.body) == 1000


def test_body_over_the_limit_is_refused_with_content_length(server):
    with pytest.raises(TransportError, match="exceeds"):
        _loopback(max_body_bytes=1000).get(_url(server, "/size/1001"), UA)


def test_body_over_the_limit_is_refused_without_content_length(server):
    with pytest.raises(TransportError, match="exceeds"):
        _loopback(max_body_bytes=1000).get(_url(server, "/nolength/200000"), UA)
    assert len(_loopback(max_body_bytes=300000).get(_url(server, "/nolength/200000"), UA).body) == 200000


# --- timeouts ---------------------------------------------------------------------------------------


def test_read_timeout_raises_transport_error(server):
    started = time.monotonic()
    with pytest.raises(TransportError, match="Timeout"):
        _loopback(timeout=0.3).get(_url(server, "/hang"), UA)
    assert time.monotonic() - started < 5


def test_overall_deadline_stops_a_slow_drip(server):
    started = time.monotonic()
    with pytest.raises(TransportError, match="deadline"):
        _loopback(timeout=2.0, deadline=0.5).get(_url(server, "/drip"), UA)
    assert time.monotonic() - started < 3


def test_connection_refused_is_a_transport_error(server):
    url = _url(server, "/ok")
    server.shutdown()
    server.server_close()
    with pytest.raises(TransportError):
        _loopback(timeout=1).get(url, UA)


def test_tls_against_a_plain_server_is_a_transport_error(server):
    with pytest.raises(TransportError):
        HttpTransport(timeout=2).get(f"https://127.0.0.1:{server.server_port}/ok", UA)


def test_certificate_verification_is_on():
    import ssl

    ctx = HttpTransport()._context
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


# --- redirects --------------------------------------------------------------------------------------


def test_redirects_are_followed_up_to_the_limit_and_final_url_reported(server):
    resp = _loopback(max_redirects=3).get(_url(server, "/redirect/3"), UA)
    assert resp.status == 200
    assert resp.body == b"landed"
    assert resp.final_url == _url(server, "/redirect/0")
    assert [p for p, _ in server.seen] == ["/redirect/3", "/redirect/2", "/redirect/1", "/redirect/0"]


def test_more_redirects_than_the_limit_is_refused(server):
    with pytest.raises(TransportError, match="redirects"):
        _loopback(max_redirects=3).get(_url(server, "/redirect/4"), UA)


def test_zero_redirects_returns_nothing_followed(server):
    with pytest.raises(TransportError, match="redirects"):
        _loopback(max_redirects=0).get(_url(server, "/redirect/1"), UA)


def test_absolute_redirect_drops_the_fragment(server):
    resp = _loopback().get(_url(server, "/to-absolute"), UA)
    assert resp.final_url == _url(server, "/ok")


def test_redirect_without_location_is_returned_as_a_response(server):
    resp = _loopback().get(_url(server, "/nolocation"), UA)
    assert resp.status == 302
    assert resp.body == b"moved"


@pytest.mark.parametrize("path", ["/to-http", "/to-file", "/to-creds"])
def test_redirect_to_a_refused_target_is_a_transport_error(server, path):
    with pytest.raises(TransportError):
        _loopback().get(_url(server, path), UA)
    assert [p for p, _ in server.seen] == [path]  # the second request was never sent


# --- redirects stay on the original origin (OD-0121) -----------------------------------------------


def test_cross_origin_redirect_is_refused_and_the_other_origin_sees_nothing(two_servers):
    first, second = two_servers
    with pytest.raises(TransportError, match="cross-origin") as info:
        _loopback().get(_url(first, "/cross"), UA)
    assert f"127.0.0.1:{first.server_port}" in str(info.value)
    assert f"127.0.0.1:{second.server_port}" in str(info.value)
    assert [p for p, _ in first.seen] == ["/cross"]
    assert second.seen == []


def test_same_origin_redirect_is_still_followed_with_another_origin_present(two_servers):
    first, second = two_servers
    resp = _loopback().get(_url(first, "/redirect/2"), UA)
    assert resp.status == 200
    assert resp.final_url == _url(first, "/redirect/0")
    assert second.seen == []


def test_a_chain_that_leaves_and_returns_is_refused_at_the_first_cross_origin_hop(two_servers):
    first, second = two_servers
    with pytest.raises(TransportError, match="cross-origin"):
        _loopback().get(_url(first, "/leave-and-return"), UA)
    assert [p for p, _ in first.seen] == ["/leave-and-return"]
    assert second.seen == []


@pytest.mark.parametrize(
    ("url", "origin"),
    [
        ("HTTPS://Example.COM/x", "https://example.com:443"),
        ("https://example.com:443/x", "https://example.com:443"),
        ("https://example.com:8443/x", "https://example.com:8443"),
        ("https://example.com/x#frag", "https://example.com:443"),
    ],
)
def test_origin_is_scheme_lowercase_host_and_effective_port(url, origin):
    assert HttpTransport()._origin(url) == origin


# --- policy refusals (no connection is attempted) ---------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://example.invalid/data.csv",
        "http://localhost/x",
        "http://127.0.0.2/x",
        "ftp://example.invalid/x",
        "file:///etc/passwd",
        "//example.invalid/x",
        "example.invalid/x",
        "https:///nohost",
        "https://user:pw@example.invalid/x",
        "https://example.invalid:notaport/x",
    ],
)
def test_other_urls_are_refused_even_with_the_loopback_opt_in(url):
    with pytest.raises(TransportError):
        _loopback().get(url, UA)


def test_loopback_http_is_refused_without_the_opt_in(server):
    with pytest.raises(TransportError, match="only https"):
        HttpTransport().get(_url(server, "/ok"), UA)
    assert server.seen == []


def test_a_user_agent_is_required():
    for headers in ({}, {"Accept": "x"}, {"User-Agent": "  "}):
        with pytest.raises(TransportError, match="User-Agent"):
            _loopback().get("http://127.0.0.1:9/", headers)


@pytest.mark.parametrize("name", ["Authorization", "cookie", "Proxy-Authorization"])
def test_credential_headers_are_refused(server, name):
    with pytest.raises(TransportError, match="credential"):
        _loopback().get(_url(server, "/ok"), {**UA, name: "x"})
    assert server.seen == []


def test_constructor_rejects_nonsense_limits():
    for kw in ({"timeout": 0}, {"deadline": 0}, {"max_body_bytes": 0}, {"max_redirects": -1}):
        with pytest.raises(ValueError):
            HttpTransport(**kw)
