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
    reference = make_reference(tmp_path, {})
    assert ref.main(["extract", "--reference", str(reference)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("stopped: ") and "openpyxl" in err
