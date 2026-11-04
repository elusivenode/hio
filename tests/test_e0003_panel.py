"""T-0023 step 2 (OD-0177): the AUD panel rebuild, on invented data only. Nothing here reads a research store,
touches the network or runs xlrd: the extractor is injected."""

import hashlib
import importlib.util
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal as D
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from hio.storage.objectstore import LocalObjectStore

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("e0003_panel", REPO / "tools" / "e0003_panel.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["e0003_panel"] = tool
_spec.loader.exec_module(tool)

CODE = {"commit": "a" * 40, "lock_sha256": "l" * 64}
CODE2 = {"commit": "b" * 40, "lock_sha256": "l" * 64}
NOW = datetime(2026, 11, 5, 1, 2, 3, tzinfo=UTC)
NOW2 = datetime(2026, 11, 6, 4, 5, 6, tzinfo=UTC)
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
SHAPES = {"SPY": (0.31, 50), "IEF": (0.12, 37), "BIL": (0.011, 23)}  # invented price saw-teeth
XLS_BYTES = bytes.fromhex("D0CF11E0") + b" invented spreadsheet bytes"


@pytest.fixture(autouse=True)
def fast_and_private(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    for module in {id(m): m for m in (tool.ev, tool.base.ev)}.values():
        monkeypatch.setattr(module, "REPLICATIONS", 100)  # the bootstrap's size is not what these tests probe


# --- invented inputs


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def trading_days(start: date, count: int) -> list[date]:
    out, day = [], start
    while len(out) < count:
        if day.weekday() < 5:
            out.append(day)
        day += timedelta(days=1)
    return out


def calendar_days(first: date, last: date) -> list[date]:
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def symbol_rows(exchange):
    wanted = [s.rsplit(".", 1)[0] for s in tool.ev.ETFS if s.endswith(f".{exchange}")]
    return [{"Code": c, "Currency": "USD" if exchange == "US" else "AUD"} for c in wanted]


def invented_eod(days, step, wrap):
    rows = []
    for i, day in enumerate(days):
        close = round(100.0 + step * (i % wrap), 4)
        rows.append({"date": day.isoformat(), "close": close, "adjusted_close": close})
    return rows


def responder(days):
    def get(request):
        path = request.split("?")[0].split("/")
        if path[1] == "eod":
            step, wrap = SHAPES.get(path[2].split(".")[0], (0.2, 41))
            return 200, json.dumps(invented_eod(days, step, wrap)).encode()
        if path[1] == "exchange-symbol-list":
            return 200, json.dumps(symbol_rows(path[2])).encode()
        return 200, b"[]"

    return get


def f1_date(day: date) -> str:
    return f"{day.day:02d}-{MONTHS[day.month - 1]}-{day.year}"


def f1_bytes() -> bytes:
    """An invented F1: FIRMMCRID daily from the TRI's start, and the TRI as exactly that rate's accrual."""
    days = calendar_days(date(2011, 1, 4), date(2011, 7, 31))
    rates = {d: D("4") + D(i % 9) / 20 for i, d in enumerate(days)}
    levels = tool.ext.accrue(rates)
    lines = [
        "F1 INTEREST RATES AND YIELDS (invented),,",
        "Title,Interbank Overnight Cash Rate,Cash Rate Total Return Index",
        "Series ID,FIRMMCRID,FIRMMCTRI",
    ]
    lines += [f"{f1_date(d)},{rates[d]},{levels[d] * 100:.4f}" for d in days]
    return ("\n".join(lines) + "\n").encode()


def h10_zip_bytes(path: Path) -> bytes:
    days = calendar_days(date(2007, 3, 1), date(2011, 7, 31))
    cells = "".join(
        f'<k:Obs TIME_PERIOD="{d.isoformat()}" OBS_VALUE="{0.70 + 0.0001 * (i % 40):.4f}"/>'
        for i, d in enumerate(days)
    )
    xml = (
        '<m xmlns:k="urn:k"><k:Series SERIES_NAME="OTHER">'
        '<k:Obs TIME_PERIOD="2020-01-02" OBS_VALUE="9"/></k:Series>'
        f'<k:Series SERIES_NAME="RXI$US_N.B.AL">{cells}</k:Series></m>'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("H10_data.xml", xml)
    return path.read_bytes()


def history_rows() -> list[tuple[str, str]]:
    days = calendar_days(date(2007, 3, 1), date(2011, 1, 3))
    return [(d.isoformat(), f"{5.0 + (i % 11) / 20:.2f}") for i, d in enumerate(days)]


def extract_body(rows) -> str:
    return "date,rate_pct\n" + "".join(f"{d},{r}\n" for d, r in rows)


@dataclass
class Workspace:
    root: Path
    e0002: Path
    e0003: Path
    h10: Path
    history: Path
    rows: list[tuple[str, str]]
    gate: Any

    def extract(self, _path):
        return list(self.rows)


def make_private_dir(path: Path) -> Path:
    path.mkdir(parents=True, mode=0o700)
    path.chmod(0o700)
    return path


def build_workspace(base: Path) -> Workspace:
    gate = tool.ev.make_gate({})
    e0002 = make_private_dir(base / "e0002")
    days = trading_days(date(2007, 4, 2), 1100)
    tool.ev.fetch(e0002, "s2", gate=gate, commit="c" * 40, get=responder(days), pause=0)
    manifest = tool.ev.load_snapshot(e0002, "s2")
    store = LocalObjectStore(e0002 / "store")
    _, hashes = tool.build_usd_panel(e0002, manifest, store, gate=gate, code=CODE)
    tool.ev.make_private(e0002 / "store")
    (e0002 / "store").chmod(0o700)
    summary = {"snapshot": "s2", "comparison_ran": True, "releases": hashes}
    tool.ev.private_write(e0002 / "summary.json", (json.dumps(summary, indent=1) + "\n").encode())

    e0003 = make_private_dir(base / "e0003")
    raw = make_private_dir(e0003 / "raw")
    f1 = f1_bytes()
    (raw / "rba_f1.csv").write_bytes(f1)
    (raw / "manifest.json").write_text(json.dumps({"receipt_id": sha256(f1)}))

    h10 = make_private_dir(base / "h10")
    zipped = h10_zip_bytes(h10 / "FRB_h10_xml.zip")
    (h10 / "manifest.json").write_text(json.dumps({"sha256": sha256(zipped)}))

    history = make_private_dir(base / "history")
    rows = history_rows()
    body = extract_body(rows).encode()
    (history / tool.history_tool.FILE_NAME).write_bytes(XLS_BYTES)
    (history / "manifest.json").write_text(json.dumps({"sha256": sha256(XLS_BYTES)}))
    (history / "firmmcrid.csv").write_bytes(body)
    meta = {"rows": len(rows), "from_file_sha256": sha256(XLS_BYTES), "sha256": sha256(body)}
    (history / "extract-manifest.json").write_text(json.dumps(meta))
    return Workspace(make_private_dir(base / "root"), e0002, e0003, h10, history, rows, gate)


@pytest.fixture
def ws(tmp_path):
    return build_workspace(tmp_path)


def rebuild(ws: Workspace, **kwargs):
    options = {
        "gate": ws.gate,
        "code": CODE,
        "extract": ws.extract,
        "tool_versions": lambda: {"python": "invented"},
        "now": lambda: NOW,
        "frozen": None,
    }
    return tool.rebuild(ws.root, ws.e0002, ws.e0003, ws.h10, ws.history, **(options | kwargs))


def tree(*roots: Path) -> dict[str, tuple[str, int]]:
    return {
        str(p): (sha256(p.read_bytes()) if p.is_file() else "dir", p.stat().st_mode)
        for r in roots
        for p in sorted(r.rglob("*"))
    }


def runs(ws: Workspace) -> list[Path]:
    return sorted((ws.root / "runs").iterdir()) if (ws.root / "runs").exists() else []


# --- (1) end to end


def test_a_rebuild_writes_four_private_files_and_touches_no_earlier_workspace(ws):
    before = tree(ws.e0002, ws.e0003)
    out = rebuild(ws)
    run_dir = Path(out["run_dir"])
    assert run_dir == ws.root / "runs" / f"20261105T010203Z-{CODE['commit'][:8]}"
    for name in ("panel.csv", "values.json", "report.md", "run.json"):
        assert (run_dir / name).stat().st_mode & 0o777 == 0o600, name
    assert tree(ws.e0002, ws.e0003) == before
    assert out["first_month"] <= "2007-05-31" and out["last_month"] > "2011-01-04"
    assert out["months"] >= 48
    assert sha256((run_dir / "panel.csv").read_bytes()) == out["panel_sha256"]
    assert sha256((run_dir / "values.json").read_bytes()) == out["values_sha256"]
    assert sha256((run_dir / "report.md").read_bytes()) == out["report_sha256"]
    assert json.loads((run_dir / "run.json").read_text()) == json.loads(json.dumps(out))
    assert out["code"] == CODE and out["versions"] == {"python": "invented"}
    assert out["started_at"] == NOW.isoformat()


# --- (2) a second rebuild


def test_a_second_rebuild_is_a_new_run_with_the_same_panel_identity(ws):
    first = rebuild(ws)
    first_dir = Path(first["run_dir"])
    first_tree = tree(first_dir)
    second = rebuild(ws, code=CODE2, now=lambda: NOW2)
    assert second["run_dir"] != first["run_dir"] and Path(second["run_dir"]).is_dir()
    assert len(runs(ws)) == 2
    assert set(second["release_ids_this_run"]) == set(first["release_ids_this_run"])
    for sleeve, release_id in first["release_ids_this_run"].items():
        assert second["release_ids_this_run"][sleeve] != release_id
    for key in ("panel_id", "panel_sha256", "values_sha256"):
        assert second[key] == first[key]
    assert second["report_sha256"] != first["report_sha256"]  # the report names its run
    assert second["release_data_sha256"] == first["release_data_sha256"]
    assert second["code"] == CODE2 and second["started_at"] == NOW2.isoformat()
    assert tree(first_dir) == first_tree  # the earlier run isn't touched


# --- (3) what the panel id covers

BASE_INPUTS = {
    "eodhd_snapshot": {
        "name": "s2",
        "files": {"manifest.json": "a" * 64, "raw/s2/SPY.US.eod.json": "b" * 64},
    },
    "rba_f1_receipt": "c" * 64,
    "rba_f1_historical_xls": "d" * 64,
    "rba_firmmcrid_extract": "e" * 64,
    "frb_h10_zip": "f" * 64,
}
PANEL_SHA = "9" * 64


def test_the_panel_id_is_a_function_of_its_inputs_alone():
    assert tool.panel_id(BASE_INPUTS, PANEL_SHA) == tool.panel_id(
        dict(reversed(BASE_INPUTS.items())), PANEL_SHA
    )
    assert re.fullmatch(r"[0-9a-f]{64}", tool.panel_id(BASE_INPUTS, PANEL_SHA))


@pytest.mark.parametrize("key", sorted(BASE_INPUTS))
def test_the_panel_id_changes_when_any_one_input_hash_changes(key):
    changed = dict(BASE_INPUTS)
    changed[key] = {**BASE_INPUTS[key], "name": "s3"} if isinstance(BASE_INPUTS[key], dict) else "0" * 64
    assert tool.panel_id(changed, PANEL_SHA) != tool.panel_id(BASE_INPUTS, PANEL_SHA)


def test_the_panel_id_changes_when_one_snapshot_file_hash_changes():
    files = {**BASE_INPUTS["eodhd_snapshot"]["files"], "raw/s2/SPY.US.eod.json": "0" * 64}
    changed = {**BASE_INPUTS, "eodhd_snapshot": {"name": "s2", "files": files}}
    assert tool.panel_id(changed, PANEL_SHA) != tool.panel_id(BASE_INPUTS, PANEL_SHA)


@pytest.mark.parametrize("key, value", [("max_stale_days", 99), ("cash", "another"), ("spec_version", "9")])
def test_the_panel_id_changes_when_a_convention_changes(monkeypatch, key, value):
    before = tool.panel_id(BASE_INPUTS, PANEL_SHA)
    monkeypatch.setitem(tool.CONVENTIONS, key, value)
    assert tool.panel_id(BASE_INPUTS, PANEL_SHA) != before


def test_the_panel_id_changes_when_the_panel_text_changes():
    assert tool.panel_id(BASE_INPUTS, "8" * 64) != tool.panel_id(BASE_INPUTS, PANEL_SHA)


# --- (4) tampering stops before any run directory exists


def tamper_snapshot(ws):
    (ws.e0002 / "raw" / "s2" / "SPY.US.eod.json").write_bytes(b"[]")


def tamper_f1(ws):
    path = ws.e0003 / "raw" / "rba_f1.csv"
    path.write_bytes(path.read_bytes() + b"\n")


def tamper_h10(ws):
    path = ws.h10 / "FRB_h10_xml.zip"
    path.write_bytes(path.read_bytes() + b"x")


def tamper_xls(ws):
    (ws.history / tool.history_tool.FILE_NAME).write_bytes(XLS_BYTES + b"x")


@pytest.mark.parametrize(
    "tamper, why",
    [
        (tamper_snapshot, "don't match the manifest"),
        (tamper_f1, "F1 bytes don't match"),
        (tamper_h10, "H.10 archive doesn't match"),
        (tamper_xls, "retained .xls doesn't match"),
    ],
)
def test_changed_retained_bytes_stop_and_write_no_run_directory(ws, tamper, why):
    tamper(ws)
    with pytest.raises(tool.ev.Stop, match=why):
        rebuild(ws)
    assert not (ws.root / "runs").exists()
    assert list(ws.root.iterdir()) == []


@pytest.mark.parametrize("change", ["value", "dropped", "extra"])
def test_an_extractor_that_returns_other_rows_stops_and_writes_no_run_directory(ws, change):
    rows = ws.rows
    other = {
        "value": [*rows[:-1], (rows[-1][0], "9.99")],
        "dropped": rows[:-1],
        "extra": [*rows, ("2011-01-04", "4.00")],
    }[change]
    with pytest.raises(tool.ev.Stop, match=r"extracting the \.xls again"):
        rebuild(ws, extract=lambda _path: other)
    assert not (ws.root / "runs").exists()


def test_an_extract_that_names_another_xls_stops(ws):
    meta_path = ws.history / "extract-manifest.json"
    meta = json.loads(meta_path.read_text())
    meta_path.write_text(json.dumps({**meta, "from_file_sha256": "0" * 64}))
    with pytest.raises(tool.ev.Stop, match=r"names another \.xls"):
        rebuild(ws)
    assert not (ws.root / "runs").exists()


# --- (5) the checks


def test_the_checks_of_a_plain_rebuild(ws):
    checks = rebuild(ws)["checks"]
    assert checks == {
        "release_data_equals_recorded": True,
        "values_equal_recorded_v1": False,  # invented data can't equal what E-0003 V1 recorded
        "seam_check_passes": True,
        "panel_id_equals_frozen": None,
    }


def test_values_equal_recorded_is_true_only_for_the_runs_own_values_hash(ws):
    first = rebuild(ws)
    again = rebuild(ws, recorded_values=first["values_sha256"], now=lambda: NOW2)
    assert again["checks"]["values_equal_recorded_v1"] is True
    other = rebuild(ws, recorded_values="0" * 64, now=lambda: NOW2 + timedelta(seconds=1))
    assert other["checks"]["values_equal_recorded_v1"] is False
    assert other["values_sha256"] == first["values_sha256"]


def test_the_default_is_the_frozen_id_so_an_invented_panel_differs(ws):
    assert tool.FROZEN_PANEL_ID is not None
    out = tool.rebuild(
        ws.root,
        ws.e0002,
        ws.e0003,
        ws.h10,
        ws.history,
        gate=ws.gate,
        code=CODE,
        extract=ws.extract,
        tool_versions=lambda: {"python": "invented"},
        now=lambda: NOW,
    )
    assert out["checks"]["panel_id_equals_frozen"] is False


def test_panel_id_equals_frozen_is_none_true_or_false(ws):
    first = rebuild(ws)
    assert first["checks"]["panel_id_equals_frozen"] is None
    match = rebuild(ws, frozen=first["panel_id"], now=lambda: NOW2)
    assert match["checks"]["panel_id_equals_frozen"] is True
    mismatch = rebuild(ws, frozen="0" * 64, now=lambda: NOW2 + timedelta(seconds=1))
    assert mismatch["checks"]["panel_id_equals_frozen"] is False


def test_release_data_equals_recorded_is_false_when_the_recorded_store_differs(ws):
    summary = json.loads((ws.e0002 / "summary.json").read_text())
    sha = summary["releases"]["equity"]
    data = ws.e0002 / "store" / "releases" / tool.ev.SLEEVES["equity"][1] / sha / "data.csv"
    data.chmod(0o600)
    data.write_bytes(data.read_bytes() + b"2030-01-01,2030-01-02,0,0,0\n")
    out = rebuild(ws)
    assert out["checks"]["release_data_equals_recorded"] is False
    assert out["checks"]["seam_check_passes"] is True


# --- (6) main


def fake_out(**checks):
    wanted = {
        "release_data_equals_recorded": True,
        "values_equal_recorded_v1": True,
        "seam_check_passes": True,
        "panel_id_equals_frozen": None,
    } | checks
    keys = (
        *("panel_id", "panel_sha256", "values_sha256", "report_sha256", "run_dir", "code", "versions"),
        *("first_month", "last_month", "months", "seam_check", "interval_classes"),
    )
    return {**dict.fromkeys(keys, "x"), "checks": wanted}


def main_argv(ws):
    return [
        "rebuild",
        "--root",
        str(ws.root),
        "--e0002",
        str(ws.e0002),
        "--e0003",
        str(ws.e0003),
        "--h10",
        str(ws.h10),
        "--history",
        str(ws.history),
    ]


@pytest.fixture(autouse=True)
def no_git(monkeypatch):
    monkeypatch.setattr(tool.ev, "code_commit", lambda: CODE)  # the real one needs a clean git tree


def test_main_returns_3_when_a_check_is_false(ws, monkeypatch, capsys):
    monkeypatch.setattr(tool, "rebuild", lambda *_a, **_k: fake_out(panel_id_equals_frozen=False))
    assert tool.main(main_argv(ws)) == 3
    captured = capsys.readouterr()
    assert "differs: panel_id_equals_frozen" in captured.err
    assert json.loads(captured.out)["checks"]["panel_id_equals_frozen"] is False


def test_main_returns_0_when_no_check_is_false(ws, monkeypatch, capsys):
    monkeypatch.setattr(tool, "rebuild", lambda *_a, **_k: fake_out())
    assert tool.main(main_argv(ws)) == 0
    assert capsys.readouterr().err == ""


def test_main_returns_2_when_rebuild_stops_and_prints_only_the_stop(ws, monkeypatch, capsys):
    def stop(*_a, **_k):
        raise tool.ev.Stop("a retained input changed")

    monkeypatch.setattr(tool, "rebuild", stop)
    assert tool.main(main_argv(ws)) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "a retained input changed" in captured.err


def test_main_hides_the_message_of_any_other_error(ws, monkeypatch, capsys):
    def boom(*_a, **_k):
        raise ValueError("invented-value-0.123456")

    monkeypatch.setattr(tool, "rebuild", boom)
    assert tool.main(main_argv(ws)) == 2
    captured = capsys.readouterr()
    assert "ValueError" in captured.err and "0.123456" not in captured.err + captured.out


def test_main_over_a_real_rebuild_prints_hashes_and_classes_but_no_panel_value(ws, monkeypatch, capsys):
    original = tool.rebuild

    def injected(*args, **kwargs):
        return original(
            *args, **kwargs, extract=ws.extract, tool_versions=lambda: {"python": "invented"}, now=lambda: NOW
        )

    monkeypatch.setattr(tool, "rebuild", injected)
    assert tool.main(main_argv(ws)) == 3  # invented data can't equal the recorded V1 values
    captured = capsys.readouterr()
    printed = json.loads(captured.out)
    run_dir = Path(printed["run_dir"])
    assert "differs: values_equal_recorded_v1" in captured.err
    assert printed["panel_sha256"] == sha256((run_dir / "panel.csv").read_bytes())
    cells = [c for line in (run_dir / "panel.csv").read_text().splitlines()[1:] for c in line.split(",")[2:]]
    assert cells and not [c for c in cells if c in captured.out]
    values = json.loads((run_dir / "values.json").read_text())
    assert "final_wealth" not in captured.out and "windows" not in printed
    assert values["windows"]["full"]["available"] is True


# --- (7) the panel's text, the report and the output locations


def test_the_panel_text_has_the_declared_columns_and_twelve_decimals():
    built = tool.ext.Assembled(
        months=[date(2020, 1, 31), date(2020, 2, 29), date(2020, 3, 31)],
        returns=np.array([[0.1, -0.2, 0.3, 0.4], [0.0, 1 / 3, 2 / 3, 1.0]]),
        usd_bills=np.array([0.01, 0.02]),
        s=np.array([-0.05, 0.05]),
        history_rates_used=0,
        facts={},
        seam={},
    )
    lines = tool.panel_text(built).split("\n")
    assert lines[0] == "period_start,period_end,equity,bills,treasury,cash,usd_bills,fx_return"
    assert lines[0] == ",".join(tool.CONVENTIONS["panel_columns"])
    assert lines[1] == (
        "2020-01-31,2020-02-29,0.100000000000,-0.200000000000,0.300000000000,0.400000000000,"
        "0.010000000000,-0.050000000000"
    )
    assert lines[2] == (
        "2020-02-29,2020-03-31,0.000000000000,0.333333333333,0.666666666667,1.000000000000,"
        "0.020000000000,0.050000000000"
    )
    assert lines[3] == ""  # ends with one newline


def test_a_rebuilt_panel_file_holds_only_twelve_decimal_cells(ws):
    run_dir = Path(rebuild(ws)["run_dir"])
    lines = (run_dir / "panel.csv").read_text().splitlines()
    assert lines[0] == ",".join(tool.CONVENTIONS["panel_columns"])
    for line in lines[1:]:
        start, end, *cells = line.split(",")
        assert start < end and len(cells) == 6
        assert all(re.fullmatch(r"-?\d+\.\d{12}", c) for c in cells), line


def test_the_report_names_the_panel_id_and_the_run(ws):
    out = rebuild(ws)
    report = (Path(out["run_dir"]) / "report.md").read_text()
    assert f"Panel id `{out['panel_id']}`" in report
    assert f"Run `{Path(out['run_dir']).name}`" in report
    assert report.startswith("# E-0003 V1 (from May 2007)")


def test_no_output_path_lies_inside_the_repository(ws):
    out = rebuild(ws)
    for path in (ws.root, Path(out["run_dir"]), ws.e0002, ws.e0003):
        resolved = path.resolve()
        assert resolved != REPO and REPO not in resolved.parents


@pytest.mark.parametrize("place", ["root", "e0002", "e0003"])
def test_a_root_inside_the_repository_refuses_before_anything_is_written(ws, place):
    inside = REPO / "tests"
    kwargs = {"root": ws.root, "e0002": ws.e0002, "e0003": ws.e0003} | {place: inside}
    before = tree(ws.root, ws.e0002, ws.e0003)
    with pytest.raises(tool.ev.Stop, match="outside the repository"):
        tool.rebuild(
            kwargs["root"],
            kwargs["e0002"],
            kwargs["e0003"],
            ws.h10,
            ws.history,
            gate=ws.gate,
            code=CODE,
            extract=ws.extract,
            now=lambda: NOW,
        )
    if place != "root":
        assert tree(ws.root) == {k: v for k, v in before.items() if k.startswith(str(ws.root))}
    assert not (ws.root / "runs").exists()
