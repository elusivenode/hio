"""The one-off BLS CPI fetch, on invented responses only (no network)."""

import hashlib
import importlib.util
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from hio.contracts.rights import Operation, RightsRefused

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("bls_cpi_fetch", REPO / "tools" / "bls_cpi_fetch.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

CONTACT = "zz-invented-contact@example.invalid"
NOW = datetime(2026, 11, 22, 3, 0, tzinfo=UTC)
OK = json.dumps({"status": "REQUEST_SUCCEEDED", "Results": {"series": []}}).encode()
# 14 distinct dates; the first also has a pdf link.
ARCHIVE_DATES = [date(2024, m, 10) for m in range(1, 13)] + [date(2025, 1, 15), date(2025, 2, 12)]


def archive_page(dates=ARCHIVE_DATES, extra=""):
    links = [f'<a href="/news.release/archives/cpi_{d:%m%d%Y}.htm">x</a>' for d in dates]
    links.append(f'<a href="/news.release/archives/cpi_{dates[0]:%m%d%Y}.pdf">pdf</a>')
    return ("<html>" + "".join(links) + extra + "</html>").encode()


class FakeGate:
    def __init__(self, refuse=None):
        self.refuse = refuse
        self.calls = []

    def authorise(self, operation, source_ids, _consumer_class=None):
        self.calls.append((operation, list(source_ids)))
        if operation is self.refuse:
            raise RightsRefused(operation, ["bls_cpi: invented refusal"])


class Net:
    def __init__(self, page=None, post_answer=(200, OK), get_status=200):
        self.page = archive_page() if page is None else page
        self.post_answer = post_answer
        self.get_status = get_status
        self.posts = []
        self.gets = []
        self.agents = []

    def post(self, url, payload, agent):
        self.posts.append((url, json.loads(payload)))
        self.agents.append(agent)
        return self.post_answer

    def get(self, url, agent):
        self.gets.append(url)
        self.agents.append(agent)
        if self.get_status != 200:
            return self.get_status, b""
        if url == tool.ARCHIVE_URL:
            return 200, self.page
        return 200, b"invented release " + url.encode()


def run(tmp_path, net=None, gate=None, **kwargs):
    net = net or Net()
    kwargs.setdefault("now", NOW)
    manifest = tool.fetch(
        tmp_path / "out",
        gate=gate or FakeGate(),
        commit="c",
        contact=CONTACT,
        get=net.get,
        post=net.post,
        **kwargs,
    )
    return manifest, net


def test_the_ten_year_split():
    assert tool.year_spans(2026) == [(2005, 2014), (2015, 2024), (2025, 2026)]
    assert tool.year_spans(2024) == [(2005, 2014), (2015, 2024)]
    assert tool.year_spans(2025) == [(2005, 2014), (2015, 2024), (2025, 2025)]
    assert tool.year_spans(2005) == [(2005, 2005)]
    with pytest.raises(ValueError):
        tool.year_spans(2004)


def test_requests_are_the_split_then_the_archive_then_the_releases(tmp_path):
    manifest, net = run(tmp_path, releases=4)
    assert [p[0] for p in net.posts] == [tool.API_URL] * 3
    assert net.posts[0][1] == {"seriesid": ["CUUR0000SA0"], "startyear": "2005", "endyear": "2014"}
    assert net.posts[2][1] == {"seriesid": ["CUUR0000SA0"], "startyear": "2025", "endyear": "2026"}
    assert net.gets[0] == tool.ARCHIVE_URL
    assert len(net.gets) == 1 + 4
    assert manifest["requests"] == 3 + 1 + 4
    out = tmp_path / "out"
    assert (out / "cpi_series_2005_2014.json").read_bytes() == OK
    assert (out / "cpi_release_archive.htm").read_bytes() == archive_page()


def test_every_request_carries_the_user_agent_with_the_contact(tmp_path):
    _manifest, net = run(tmp_path, releases=2)
    expected = f"HIO-research/0.1 (one-off CPI download for non-commercial research; contact: {CONTACT})"
    assert net.agents and set(net.agents) == {expected}


def test_the_default_is_twelve_releases_and_sixteen_requests(tmp_path):
    manifest, net = run(tmp_path)
    assert manifest["requests"] == 16
    assert len(net.gets) == 13


def test_refusal_past_the_request_limit(tmp_path):
    net = Net()
    with pytest.raises(ValueError, match="more than 20 requests"):
        run(tmp_path, net, now=datetime(2100, 1, 1, tzinfo=UTC))
    assert len(net.posts) + len(net.gets) == 20
    assert not (tmp_path / "out").exists()


def test_a_smaller_limit_refuses_on_the_request_past_it(tmp_path):
    net = Net()
    with pytest.raises(ValueError, match="more than 4 requests"):
        run(tmp_path, net, max_requests=4)
    assert len(net.posts) + len(net.gets) == 4


def test_releases_outside_one_to_twelve_refuse_before_any_request(tmp_path):
    for n in (0, 13, -1):
        with pytest.raises(ValueError, match="between 1 and 12"):
            run(tmp_path, Net(post_answer=pytest.fail), releases=n)


@pytest.mark.parametrize(
    "answer",
    [
        (200, json.dumps({"status": "REQUEST_NOT_PROCESSED"}).encode()),
        (200, json.dumps({"message": ["no status"]}).encode()),
        (200, b"<html>not json</html>"),
        (200, b"[1, 2]"),
    ],
)
def test_a_non_success_api_status_refuses_and_writes_nothing(tmp_path, answer):
    net = Net(post_answer=answer)
    with pytest.raises(ValueError, match="API answer"):
        run(tmp_path, net)
    assert net.gets == []
    assert not (tmp_path / "out").exists()


def test_an_api_http_error_refuses(tmp_path):
    with pytest.raises(ValueError, match="HTTP 500"):
        run(tmp_path, Net(post_answer=(500, b"")))
    assert not (tmp_path / "out").exists()


def test_a_get_http_error_refuses(tmp_path):
    with pytest.raises(ValueError, match="HTTP 403"):
        run(tmp_path, Net(get_status=403))
    assert not (tmp_path / "out").exists()


def test_archive_links_pdf_and_htm_duplicates_and_bad_dates():
    page = (
        '<a href="/news.release/archives/cpi_01152025.htm">a</a>'
        '<a href="/news.release/archives/cpi_01152025.pdf">a</a>'
        '<a href="/news.release/archives/cpi_01152025.htm">a again</a>'
        '<a href="/news.release/archives/cpi_12112024.pdf">pdf only</a>'
        '<a href="/news.release/archives/cpi_13112024.htm">month 13</a>'
        '<a href="/news.release/archives/cpi_02302024.htm">30 February</a>'
        '<a href="/news.release/archives/cpi_0115.htm">short</a>'
        '<a href="/news.release/archives/ppi_01152025.htm">other series</a>'
    )
    assert tool.parse_release_links(page) == [
        (date(2024, 12, 11), f"{tool.SITE}/news.release/archives/cpi_12112024.pdf"),
        (date(2025, 1, 15), f"{tool.SITE}/news.release/archives/cpi_01152025.htm"),
    ]
    assert tool.parse_release_links("<html>nothing</html>") == []


def test_a_page_with_no_release_dates_refuses(tmp_path):
    with pytest.raises(ValueError, match="no release dates"):
        run(tmp_path, Net(page=b"<html>none</html>"))
    assert not (tmp_path / "out").exists()


def test_release_dates_csv_is_sorted_and_deduplicated(tmp_path):
    shuffled = list(reversed(ARCHIVE_DATES))
    manifest, _net = run(tmp_path, Net(page=archive_page(shuffled)), releases=2)
    lines = (tmp_path / "out" / "release-dates.csv").read_text().splitlines()
    assert lines[0] == "date,url"
    assert len(lines) == 1 + len(ARCHIVE_DATES)
    assert lines[1].startswith("2024-01-10,https://www.bls.gov/news.release/archives/cpi_01102024.htm")
    assert [line.split(",")[0] for line in lines[1:]] == sorted(d.isoformat() for d in ARCHIVE_DATES)
    assert manifest["release_dates_parsed"] == len(ARCHIVE_DATES)


def test_even_spacing_includes_first_and_last():
    items = list(range(14))
    assert tool.choose_evenly(items, 12) == [0, 1, 2, 4, 5, 6, 7, 8, 9, 11, 12, 13]
    assert tool.choose_evenly(items, 2) == [0, 13]
    assert tool.choose_evenly(items, 3) == [0, 6, 13]
    assert tool.choose_evenly(items, 1) == [13]
    assert tool.choose_evenly(list(range(5)), 12) == [0, 1, 2, 3, 4]
    assert tool.choose_evenly([], 3) == []
    chosen = tool.choose_evenly(list(range(200)), 12)
    assert chosen[0] == 0 and chosen[-1] == 199 and chosen == sorted(set(chosen)) and len(chosen) == 12


def test_the_fetched_releases_are_the_evenly_spaced_ones(tmp_path):
    _manifest, net = run(tmp_path, releases=3)
    urls = [f"{tool.SITE}/news.release/archives/cpi_{ARCHIVE_DATES[i]:%m%d%Y}.htm" for i in (0, 6, 13)]
    assert net.gets[1:] == urls
    for url in urls:
        assert (tmp_path / "out" / Path(url).name).read_bytes() == b"invented release " + url.encode()


def test_a_used_output_refuses_so_a_rerun_cannot_download_again(tmp_path):
    run(tmp_path, releases=1)
    with pytest.raises(ValueError, match="absent or empty"):
        run(tmp_path, Net(post_answer=pytest.fail))


def test_an_empty_existing_output_is_accepted(tmp_path):
    (tmp_path / "out").mkdir()
    manifest, _net = run(tmp_path, releases=1)
    assert manifest["requests"] == 5


def test_inside_the_repository_refuses():
    with pytest.raises(ValueError, match="outside the repository"):
        tool.fetch(
            REPO / "data" / "bls",
            gate=FakeGate(),
            commit="c",
            contact=CONTACT,
            get=pytest.fail,
            post=pytest.fail,
        )


@pytest.mark.parametrize("contact", ["", "   ", "a\nb", "a\r\nX-Evil: 1"])
def test_a_bad_contact_refuses_before_any_request(tmp_path, contact):
    with pytest.raises(ValueError, match="--contact"):
        tool.fetch(
            tmp_path / "out", gate=FakeGate(), commit="c", contact=contact, get=pytest.fail, post=pytest.fail
        )


@pytest.mark.parametrize("operation", [Operation.FETCH, Operation.STORE_RAW])
def test_a_gate_refusal_stops_before_any_request(tmp_path, operation):
    gate = FakeGate(refuse=operation)
    with pytest.raises(RightsRefused):
        tool.fetch(
            tmp_path / "out", gate=gate, commit="c", contact=CONTACT, get=pytest.fail, post=pytest.fail
        )
    assert not (tmp_path / "out").exists()
    assert gate.calls[0] == (Operation.FETCH, ["bls_cpi"])


def test_both_operations_are_authorised_for_bls_cpi(tmp_path):
    gate = FakeGate()
    run(tmp_path, gate=gate, releases=1)
    assert gate.calls == [(Operation.FETCH, ["bls_cpi"]), (Operation.STORE_RAW, ["bls_cpi"])]


def test_the_contact_is_in_no_file_and_not_in_stdout(tmp_path, capsys, monkeypatch):
    manifest, _net = run(tmp_path, releases=3)
    needle = CONTACT.encode()
    files = sorted((tmp_path / "out").iterdir())
    assert files
    assert all(needle not in f.read_bytes() for f in files)
    assert manifest["user_agent"] == (
        "HIO-research/0.1 (one-off CPI download for non-commercial research; contact: <owner contact>)"
    )

    net = Net()
    real_fetch = tool.fetch
    monkeypatch.setattr(tool, "code_commit", lambda: "c")
    monkeypatch.setattr(tool, "load_genuine", lambda _p: {})
    monkeypatch.setattr(tool, "RightsGate", lambda _r: FakeGate())
    monkeypatch.setattr(
        tool, "fetch", lambda output, **kw: real_fetch(output, get=net.get, post=net.post, now=NOW, **kw)
    )
    code = tool.main(["--output", str(tmp_path / "second"), "--contact", CONTACT, "--releases", "2"])
    captured = capsys.readouterr()
    assert code == 0
    assert CONTACT not in captured.out and CONTACT not in captured.err
    assert "requests 6" in captured.out
    assert all(needle not in f.read_bytes() for f in (tmp_path / "second").iterdir())


def test_a_response_that_echoes_the_contact_is_refused_and_nothing_is_written(tmp_path):
    echo = json.dumps({"status": "REQUEST_SUCCEEDED", "echo": CONTACT}).encode()
    with pytest.raises(ValueError, match="contact string") as info:
        run(tmp_path, Net(post_answer=(200, echo)))
    assert CONTACT not in str(info.value)
    assert not (tmp_path / "out").exists()


def test_refusal_messages_never_contain_the_contact(tmp_path):
    with pytest.raises(ValueError) as info:
        run(tmp_path, Net(get_status=404))
    assert CONTACT not in str(info.value)


def test_the_manifest_hashes_match_the_files(tmp_path):
    manifest, _net = run(tmp_path, releases=5)
    out = tmp_path / "out"
    on_disk = json.loads((out / "manifest.json").read_text())
    assert on_disk == manifest
    assert on_disk["source_id"] == "bls_cpi"
    assert on_disk["code_commit"] == "c"
    assert on_disk["retrieved_at"] == NOW.isoformat()
    assert on_disk["notice"] == (
        "Source: U.S. Bureau of Labor Statistics, CPI-U (CUUR0000SA0), retrieved 2026-11-22. BLS.gov cannot "
        "vouch for the data or analyses derived from these data after the data have been retrieved from "
        "BLS.gov."
    )
    names = {entry["name"] for entry in on_disk["files"]}
    assert names == {p.name for p in out.iterdir()} - {"manifest.json"}
    assert len(on_disk["files"]) == 3 + 1 + 5 + 1
    for entry in on_disk["files"]:
        body = (out / entry["name"]).read_bytes()
        assert entry["bytes"] == len(body)
        assert entry["sha256"] == hashlib.sha256(body).hexdigest()
        assert entry["url"]
