"""Archived CPI releases: parser on the committed BLS snippets, fetch and compare on invented data."""

import csv
import importlib.util
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from hio.contracts.rights import Operation, RightsRefused

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "bls"
_spec = importlib.util.spec_from_file_location("bls_cpi_releases", REPO / "tools" / "bls_cpi_releases.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

CONTACT = "zz-invented-contact@example.invalid"
NOW = datetime(2026, 11, 22, 3, 0, tzinfo=UTC)
D = Decimal


def snippet(name):
    return (FIXTURES / name).read_bytes()


# ---- parser on the real snippets (levels read from the snippet text)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        # <PRE> layout: previous and reference month printed; no year-ago level
        (
            "cpi_02202009.htm.snippet",
            (date(2009, 1, 1), D("211.143"), date(2008, 1, 1), None),
        ),
        ("cpi_04152011.htm.snippet", (date(2011, 3, 1), D("223.467"), date(2010, 3, 1), None)),
        # HTML tables
        ("cpi_07162013.htm.snippet", (date(2013, 6, 1), D("233.504"), date(2012, 6, 1), D("229.478"))),
        ("cpi_05112022.htm.snippet", (date(2022, 4, 1), D("289.109"), date(2021, 4, 1), D("267.054"))),
    ],
)
def test_snippets_parse_to_the_printed_months_and_levels(name, expected):
    assert tool.parse_release(name, snippet(name)) == expected


def test_a_dash_is_none_for_that_level():
    got = tool.parse_release("cpi_11102026.htm.snippet", snippet("cpi_11102026.htm.snippet"))
    assert got == (date(2026, 10, 1), D("337.511"), date(2025, 10, 1), None)


def test_the_1967_base_row_is_not_taken_for_all_items():
    text = snippet("cpi_02202009.htm.snippet").decode()
    swapped = "\n".join(line for line in text.splitlines() if not line.startswith(" All items......"))
    with pytest.raises(ValueError, match="All items"):
        tool.parse_release("x.htm", swapped.encode())


@pytest.mark.parametrize(
    ("name", "old", "new", "match"),
    [
        ("cpi_07162013.htm.snippet", "233.504", "n/a", "not an index level"),
        ("cpi_07162013.htm.snippet", "All items", "Everything", "All items"),
        ("cpi_07162013.htm.snippet", "Jun.<br />2012</th>", "Xyz<br />2012</th>", "month label"),
        ("cpi_07162013.htm.snippet", "Jun.<br />2012</th>", "Jun.<br />2011</th>", "a year earlier"),
        ("cpi_04152011.htm.snippet", "to Mar. 2011", "ending then", "reference-month"),
        ("cpi_04152011.htm.snippet", "223.467", "garbled", "not an index level"),
    ],
)
def test_a_garbled_table_refuses(name, old, new, match):
    data = snippet(name).decode().replace(old, new, 1).encode()
    with pytest.raises(ValueError, match=match):
        tool.parse_release(name, data)


def test_text_that_is_not_a_table_refuses():
    with pytest.raises(ValueError):
        tool.parse_release("cpi_x.htm", b"<html>nothing here</html>")


# ---- the PDF path: a generated tiny PDF feeds the same text parser


def tiny_pdf(lines):
    stream = "BT /F1 8 Tf 10 780 Td 10 TL\n" + "\n".join(f"({ln}) '" for ln in lines) + "\nET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 700 800] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def test_a_pdf_is_text_extracted_then_parsed_as_text():
    pytest.importorskip("pypdf")
    lines = [
        "Unadjusted indexes percent change",
        "Relative to Feb. 2007",
        "All items....................    100.000    202.416    203.499     2.4     0.5",
    ]
    assert tool.parse_release("cpi_03162007.pdf", tiny_pdf(lines)) == (
        date(2007, 2, 1),
        D("203.499"),
        date(2006, 2, 1),
        None,
    )


def test_a_pdf_without_the_row_refuses():
    pytest.importorskip("pypdf")
    with pytest.raises(ValueError, match="All items"):
        tool.parse_release("cpi_03162007.pdf", tiny_pdf(["Nothing to see"]))


# ---- fetch on invented responses


class FakeGate:
    def __init__(self, refuse=None):
        self.refuse = refuse
        self.calls = []

    def authorise(self, operation, source_ids, _consumer_class=None):
        self.calls.append((operation, list(source_ids)))
        if operation is self.refuse:
            raise RightsRefused(operation, ["bls_cpi: invented refusal"])


DATES = [date(2006, 4, 12), date(2006, 5, 1), date(2007, 3, 16), date(2020, 1, 14), date(2026, 10, 31)]
DATES += [date(2026, 11, 10)]


def raw_dir(tmp_path, dates=DATES):
    raw = tmp_path / "raw"
    raw.mkdir()
    with (raw / "release-dates.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["date", "url"])
        for d in dates:
            ext = "pdf" if d.year < 2008 else "htm"
            writer.writerow([d.isoformat(), f"https://example.invalid/cpi_{d:%m%d%Y}.{ext}"])
    return raw


class Net:
    def __init__(self, status=200, echo=False):
        self.status, self.echo = status, echo
        self.gets, self.agents = [], []

    def get(self, url, agent):
        self.gets.append(url)
        self.agents.append(agent)
        body = b"invented " + url.encode()
        if self.echo:
            body += CONTACT.encode()
        return self.status, (body if self.status == 200 else b"")


def run(tmp_path, net=None, gate=None, **kwargs):
    net = net or Net()
    out = tmp_path / "out"
    manifest = tool.fetch(
        kwargs.pop("raw", None) or raw_dir(tmp_path),
        out,
        contact=CONTACT,
        gate=gate or FakeGate(),
        commit="c",
        get=net.get,
        now=NOW,
        **kwargs,
    )
    return manifest, net, out


def test_the_default_span_selects_2006_05_01_to_2026_10_31_inclusive(tmp_path):
    manifest, net, out = run(tmp_path)
    assert [Path(u).name for u in net.gets] == [
        "cpi_05012006.pdf",
        "cpi_03162007.pdf",
        "cpi_01142020.htm",
        "cpi_10312026.htm",
    ]
    assert manifest["requests"] == 4
    assert sorted(p.name for p in out.iterdir()) == sorted(
        [*(f["name"] for f in manifest["files"]), "manifest.json"]
    )


def test_start_and_end_narrow_the_selection(tmp_path):
    manifest, _net, _out = run(tmp_path, start=date(2007, 1, 1), end=date(2020, 1, 14))
    assert [f["name"] for f in manifest["files"]] == ["cpi_03162007.pdf", "cpi_01142020.htm"]


def test_bodies_are_saved_verbatim_and_hashed(tmp_path):
    import hashlib

    manifest, _net, out = run(tmp_path)
    for entry in manifest["files"]:
        body = (out / entry["name"]).read_bytes()
        assert entry["bytes"] == len(body)
        assert entry["sha256"] == hashlib.sha256(body).hexdigest()
    assert (out / manifest["files"][0]["name"]).read_bytes().startswith(b"invented https://example.invalid/")


def test_the_cap_refuses_on_the_request_past_it(tmp_path):
    net = Net()
    with pytest.raises(ValueError, match="more than 3 requests"):
        run(tmp_path, net=net, cap=3)
    assert len(net.gets) == 3


def test_the_default_cap_is_250():
    assert tool.DEFAULT_CAP == 250


def test_a_bad_status_refuses(tmp_path):
    with pytest.raises(ValueError, match="HTTP 503"):
        run(tmp_path, net=Net(status=503))


def test_both_operations_are_authorised_for_bls_cpi_before_any_request(tmp_path):
    gate = FakeGate()
    run(tmp_path, gate=gate)
    assert gate.calls == [(Operation.FETCH, ["bls_cpi"]), (Operation.STORE_RAW, ["bls_cpi"])]


@pytest.mark.parametrize("operation", [Operation.FETCH, Operation.STORE_RAW])
def test_a_gate_refusal_stops_before_any_request(tmp_path, operation):
    with pytest.raises(RightsRefused):
        tool.fetch(
            raw_dir(tmp_path),
            tmp_path / "out",
            contact=CONTACT,
            gate=FakeGate(refuse=operation),
            commit="c",
            get=pytest.fail,
        )


@pytest.mark.parametrize("contact", ["", "  ", "a\nb"])
def test_a_bad_contact_refuses_before_any_request(tmp_path, contact):
    with pytest.raises(ValueError, match="contact"):
        tool.fetch(
            raw_dir(tmp_path), tmp_path / "out", contact=contact, gate=FakeGate(), commit="c", get=pytest.fail
        )


def test_a_used_or_in_repository_output_refuses(tmp_path):
    used = tmp_path / "out"
    used.mkdir()
    (used / "x").write_text("x")
    with pytest.raises(ValueError, match="absent or empty"):
        tool.fetch(raw_dir(tmp_path), used, contact=CONTACT, gate=FakeGate(), commit="c", get=pytest.fail)
    sub = tmp_path / "sub"
    sub.mkdir()
    with pytest.raises(ValueError, match="outside the repository"):
        tool.fetch(
            raw_dir(sub),
            REPO / "out-never-written",
            contact=CONTACT,
            gate=FakeGate(),
            commit="c",
            get=pytest.fail,
        )


def test_the_contact_is_in_the_user_agent_only_never_in_a_file(tmp_path):
    manifest, net, out = run(tmp_path)
    assert all(CONTACT in agent for agent in net.agents)
    assert "<owner contact>" in manifest["user_agent"]
    for path in out.iterdir():
        assert CONTACT.encode() not in path.read_bytes()


def test_a_response_echoing_the_contact_is_refused_and_not_written(tmp_path):
    with pytest.raises(ValueError) as err:
        run(tmp_path, net=Net(echo=True))
    assert CONTACT not in str(err.value)
    out = tmp_path / "out"
    for path in out.iterdir():
        assert CONTACT.encode() not in path.read_bytes()
    assert not (out / "manifest.json").exists()


def test_no_dates_in_span_refuses(tmp_path):
    with pytest.raises(ValueError, match="no release dates"):
        run(tmp_path, raw=raw_dir(tmp_path, [date(1999, 1, 1)]))


# ---- compare


def parsed_set():
    return {
        "cpi_a.htm": (date(2013, 6, 1), D("233.504"), date(2012, 6, 1), D("229.478")),
        "cpi_b.htm": (date(2013, 7, 1), D("233.596"), date(2012, 7, 1), None),
    }


FLAT = {
    date(2013, 6, 1): D("233.504"),
    date(2012, 6, 1): D("229.478"),
    date(2013, 7, 1): D("233.596"),
}


def test_compare_all_equal_compares_decimals_exactly_not_textually():
    parsed = parsed_set()
    parsed["cpi_a.htm"] = (date(2013, 6, 1), D("233.5040"), date(2012, 6, 1), D("229.478"))
    got = tool.compare(FLAT, parsed)
    assert got["reading"] == "all equal"
    assert (got["observations_equal"], got["observations_different"], got["observations_not_printed"]) == (
        3,
        0,
        1,
    )
    assert got["months"] == 4
    assert got["differences"] == []


def test_compare_lists_the_differing_months():
    flat = {**FLAT, date(2013, 6, 1): D("233.505")}
    got = tool.compare(flat, parsed_set())
    assert got["reading"] == "differences found"
    assert got["observations_different"] == 1
    assert got["differing_months"] == ["2013-06"]
    assert got["differences"] == [
        {
            "release": "cpi_a.htm",
            "role": "current",
            "month": "2013-06",
            "printed": "233.504",
            "flat": "233.505",
        }
    ]


def test_a_printed_month_missing_from_the_flat_file_is_a_difference():
    flat = {k: v for k, v in FLAT.items() if k != date(2012, 6, 1)}
    got = tool.compare(flat, parsed_set())
    assert got["reading"] == "differences found"
    assert got["differences"][0]["flat"] is None


def test_read_flat_keeps_monthly_all_items_rows_only(tmp_path):
    path = tmp_path / "flat.txt"
    path.write_text(
        "series_id        \tyear\tperiod\t       value\tfootnote_codes\n"
        "CUSR0000SA0      \t2013\tM06\t       999.0\t\n"
        "CUUR0000SA0      \t2013\tM06\t       233.504\t\n"
        "CUUR0000SA0      \t2013\tM13\t       230.0\t\n"
    )
    assert tool.read_flat(path) == {date(2013, 6, 1): D("233.504")}


def test_main_compare_writes_local_files_and_prints_counts_only(tmp_path, capsys):
    raw = tmp_path / "raw"
    rel = tmp_path / "rel"
    raw.mkdir()
    rel.mkdir()
    (raw / tool.FLAT_NAME).write_text(
        "series_id\tyear\tperiod\tvalue\tfootnote_codes\n"
        "CUUR0000SA0\t2013\tM06\t233.504\t\n"
        "CUUR0000SA0\t2012\tM06\t229.479\t\n"
    )
    (rel / "cpi_07162013.htm").write_bytes(snippet("cpi_07162013.htm.snippet"))
    assert tool.main(["compare", "--raw", str(raw), "--releases", str(rel)]) == 0
    out = capsys.readouterr().out
    assert "reading: differences found" in out
    assert "233.504" not in out
    result = json.loads((rel / "comparison.json").read_text())
    assert result["differing_months"] == ["2012-06"]
    rows = list(csv.reader((rel / "differences.csv").open()))
    assert rows[0] == ["release", "role", "month", "printed", "flat"]
    assert rows[1] == ["cpi_07162013.htm", "year_ago", "2012-06", "229.478", "229.479"]


def test_main_compare_refuses_when_a_release_cannot_be_parsed(tmp_path, capsys):
    raw = tmp_path / "raw"
    rel = tmp_path / "rel"
    raw.mkdir()
    rel.mkdir()
    (raw / tool.FLAT_NAME).write_text(
        "series_id\tyear\tperiod\tvalue\tfootnote_codes\nCUUR0000SA0\t2013\tM06\t1.0\t\n"
    )
    (rel / "cpi_01012013.htm").write_bytes(b"<html>nothing</html>")
    assert tool.main(["compare", "--raw", str(raw), "--releases", str(rel)]) == 2
    assert "could not be parsed" in capsys.readouterr().err
    assert not (rel / "comparison.json").exists()
