"""T-0023 (OD-0178): the public reference tool, on invented data only. openpyxl isn't a HIO dependency, so
`extract` is tested only for its ImportError becoming exit 2."""

import hashlib
import json
import stat
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import eodhd_eval as ev  # noqa: E402
import t0023_reference as ref  # noqa: E402

HEADER = ("Date", "NAV")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- nav_rows


def test_nav_rows_skips_a_preamble_and_a_blank_trailing_row_and_sorts_oldest_first():
    rows = [
        ("Fund Name", "Invented ETF"),
        (None, None),
        HEADER,
        ("03-Feb-2020", 101.5),
        ("02-Jan-2020", 100),
        ("15-Jan-2020", 100.25),
        (None, None),
    ]
    assert ref.nav_rows(rows) == [("2020-01-02", "100"), ("2020-01-15", "100.25"), ("2020-02-03", "101.5")]


def test_nav_rows_stops_on_a_missing_header():
    with pytest.raises(ev.Stop, match="no Date and NAV header"):
        ref.nav_rows([("Fund", "x"), ("02-Jan-2020", 100.0)])


def test_nav_rows_stops_on_a_repeated_date():
    with pytest.raises(ev.Stop, match="a repeated NAV row"):
        ref.nav_rows([HEADER, ("02-Jan-2020", 100.0), ("02-Jan-2020", 100.5)])


@pytest.mark.parametrize("bad", [0, 0.0, -1.5, "100.0", "n/a"])
def test_nav_rows_stops_on_a_non_positive_or_non_numeric_nav(bad):
    with pytest.raises(ev.Stop, match="an impossible NAV"):
        ref.nav_rows([HEADER, ("02-Jan-2020", bad)])


def test_nav_rows_stops_on_a_missing_nav():
    with pytest.raises(ev.Stop, match="an impossible NAV"):
        ref.nav_rows([HEADER, ("02-Jan-2020", None)])


def test_nav_rows_stops_when_there_are_no_rows():
    with pytest.raises(ev.Stop, match="no NAV rows"):
        ref.nav_rows([HEADER, (None, None)])


# --- nav_text


def test_nav_text_exact_bytes():
    assert ref.nav_text([("2020-01-02", "100"), ("2020-01-15", "100.25")]) == (
        "date,nav\n2020-01-02,100\n2020-01-15,100.25\n"
    )
    assert ref.nav_text([]) == "date,nav\n"


# --- record


def make_reference(tmp_path: Path, files: dict[str, bytes]) -> Path:
    reference = tmp_path / "reference"
    (reference / "raw").mkdir(parents=True, mode=0o700)
    for name, data in files.items():
        (reference / "raw" / name).write_bytes(data)
    return reference


def test_record_hashes_each_file_against_its_declaration(tmp_path):
    reference = make_reference(tmp_path, {"b.xlsx": b"bee", "a.csv": b"ay"})
    sources = {
        "a.csv": {"url": "https://invented.example/a"},
        "b.xlsx": {"url": "https://invented.example/b"},
    }
    now = datetime(2026, 11, 5, 1, 2, 3, tzinfo=UTC)
    out = ref.record(reference, sources, now)
    assert out == {
        "recorded_at": "2026-11-05T01:02:03+00:00",
        "files": {
            "a.csv": {"url": "https://invented.example/a", "sha256": sha256(b"ay")},
            "b.xlsx": {"url": "https://invented.example/b", "sha256": sha256(b"bee")},
        },
    }
    assert list(out["files"]) == ["a.csv", "b.xlsx"]  # type: ignore[arg-type]


def test_record_stops_on_an_undeclared_file(tmp_path):
    reference = make_reference(tmp_path, {"a.csv": b"ay", "stray.bin": b"x"})
    with pytest.raises(ev.Stop, match=r"not declared: stray\.bin"):
        ref.record(reference, {"a.csv": {"url": "u"}})


# --- main


def test_main_record_writes_a_private_manifest(tmp_path, capsys):
    reference = make_reference(tmp_path, {"a.csv": b"ay"})
    (reference / "sources.json").write_text(json.dumps({"a.csv": {"url": "https://invented.example/a"}}))
    assert ref.main(["record", "--reference", str(reference)]) == 0
    assert json.loads(capsys.readouterr().out) == {"files": 1}
    manifest = reference / "manifest.json"
    assert json.loads(manifest.read_text())["files"]["a.csv"]["sha256"] == sha256(b"ay")
    assert stat.S_IMODE(manifest.stat().st_mode) == 0o600


def test_main_returns_2_on_a_stop(tmp_path, capsys):
    reference = make_reference(tmp_path, {"stray.bin": b"x"})
    (reference / "sources.json").write_text("{}")
    assert ref.main(["record", "--reference", str(reference)]) == 2
    assert "stopped: Stop: not declared: stray.bin" in capsys.readouterr().err
    assert not (reference / "manifest.json").exists()


def test_main_extract_returns_2_when_openpyxl_is_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "openpyxl", None)  # makes `import openpyxl` raise ImportError
    reference = make_reference(tmp_path, {"navhist-spy.xlsx": b"x"})
    assert ref.main(["extract", "--reference", str(reference)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("stopped: ") and "openpyxl" in err


# --- ishares_rows

NS = 'xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"'
IHEAD = ["As Of", "NAV per Share", "Ex-Dividends", "Shares Outstanding"]


def cell(text, extra=""):
    return f'<ss:Cell{extra}><ss:Data ss:Type="String">{text}</ss:Data></ss:Cell>'


def row(*texts):
    return "<ss:Row>" + "".join(cell(t) if t is not None else "<ss:Cell/>" for t in texts) + "</ss:Row>"


def workbook(rows, name="Historical", extra_sheet=""):
    return (
        f'<?xml version="1.0"?><ss:Workbook {NS}>{extra_sheet}'
        f'<ss:Worksheet ss:Name="{name}"><ss:Table>{"".join(rows)}</ss:Table></ss:Worksheet></ss:Workbook>'
    ).encode()


GOOD = [
    row(*IHEAD),
    row("Nov 20, 2026", "91.585712", "0.00", "1,000"),
    row(None, None),
    row("Nov 02, 2026", "90.10", "0.12", "1,000"),
    row("Nov 10, 2026", "90.5", "0.00", "1,000"),
]


def test_ishares_rows_sorts_oldest_first_and_keeps_nav_strings():
    assert ref.ishares_rows(workbook(GOOD)) == [
        ("2026-11-02", "90.10"),
        ("2026-11-10", "90.5"),
        ("2026-11-20", "91.585712"),
    ]


@pytest.mark.parametrize(
    ("rows", "match"),
    [
        ([row("Date", "NAV")], "header"),
        ([], "header"),
        ([row(*IHEAD)], "no NAV rows"),
        ([row(*IHEAD), row("2026-11-20", "91.5")], "no readable date"),
        ([row(*IHEAD), row("Nov 20, 2026", "0")], "impossible NAV"),
        ([row(*IHEAD), row("Nov 20, 2026", "-1.5")], "impossible NAV"),
        ([row(*IHEAD), row("Nov 20, 2026", "n/a")], "impossible NAV"),
        ([row(*IHEAD), row("Nov 20, 2026", "NaN")], "impossible NAV"),
        ([row(*IHEAD), row("Nov 20, 2026", "Infinity")], "impossible NAV"),
        ([row(*IHEAD), row("Nov 20, 2026", None)], "impossible NAV"),
        ([row(*IHEAD), row("Nov 20, 2026", "91.5"), row("Nov 20, 2026", "91.6")], "a repeated NAV row"),
        (
            [row(*IHEAD), "<ss:Row>" + cell("Nov 20, 2026") + cell("91.5", ' ss:Index="3"') + "</ss:Row>"],
            "Index",
        ),
    ],
)
def test_ishares_rows_refusals(rows, match):
    with pytest.raises(ev.Stop, match=match):
        ref.ishares_rows(workbook(rows))


def test_ishares_rows_stops_without_a_historical_sheet():
    with pytest.raises(ev.Stop, match="Historical"):
        ref.ishares_rows(workbook(GOOD, name="Holdings"))


def test_ishares_rows_stops_on_a_repeated_historical_sheet():
    sheet = f'<ss:Worksheet ss:Name="Historical"><ss:Table>{"".join(GOOD)}</ss:Table></ss:Worksheet>'
    with pytest.raises(ev.Stop, match="Historical"):
        ref.ishares_rows(workbook(GOOD, extra_sheet=sheet))


def test_ishares_rows_stops_on_malformed_xml_and_a_dtd():
    with pytest.raises(ev.Stop, match="unreadable"):
        ref.ishares_rows(b"<ss:Workbook")
    with pytest.raises(ev.Stop, match="DTD"):
        ref.ishares_rows(b'<!DOCTYPE x [<!ENTITY a "b">]>' + workbook(GOOD))


def test_extract_writes_nav_ief_privately_without_openpyxl(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "openpyxl", None)
    name = "iShares-7-10-Year-Treasury-Bond-ETF_fund.xls"
    reference = make_reference(tmp_path, {name: workbook(GOOD)})
    assert ref.extract(reference) == {"nav-ief.csv": 3}
    target = reference / "nav-ief.csv"
    assert target.read_text() == "date,nav\n2026-11-02,90.10\n2026-11-10,90.5\n2026-11-20,91.585712\n"
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert not (reference / "nav-spy.csv").exists()
