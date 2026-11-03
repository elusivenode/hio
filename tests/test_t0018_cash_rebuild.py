"""T-0018 (OD-0148): a repeatable cash rebuild for a stated window, from a file older than the calendars."""

from __future__ import annotations

import importlib.util
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from hio.jobs.s1b1 import Calendars, build_releases, ingest_pending, sofr_calendar, vintage_store
from hio.reference.calendar import CalendarCoverageError
from hio.storage.blobstore import BlobObjectStore
from hio.storage.fakeblob import FakeBlobBackend
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import AllowAllGate
from tests.test_s1b1_releases import (
    AUD_DAYS,
    NSW,
    RITS,
    SOURCES,
    US_DAYS,
    allow,
    capture_once,
    f1_csv,
    ny_json,
)

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("cash_rebuild", REPO / "tools" / "cash_rebuild.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

CUTOFF = datetime(2026, 11, 1, tzinfo=UTC)
START = date(2026, 1, 2)
CODE = {"commit": "test", "lock_sha256": "0" * 64}
CAL = REPO / "src" / "hio" / "reference" / "calendars"


def with_old_history(body: bytes) -> bytes:
    """The fixture F1 plus one row dated outside any cited calendar, as the live file has."""
    lines = body.decode().splitlines()
    head = next(i for i, ln in enumerate(lines) if ln.lower().startswith("series id"))
    row = lines[-1].split(",")
    row[0] = "04-Jan-2011"
    return "\n".join([*lines[: head + 1], ",".join(row), *lines[head + 1 :]]).encode() + b"\n"


def capture_all(store) -> None:
    for day in AUD_DAYS[1:]:
        at = datetime(day.year, day.month, day.day, 10, tzinfo=UTC) - timedelta(hours=11)
        capture_once(store, AllowAllGate(), "rba.f1", with_old_history(f1_csv(day)), at)
    for day in US_DAYS[1:]:
        at = datetime(day.year, day.month, day.day, 9, tzinfo=UTC) + timedelta(hours=4)
        sofr, index = ny_json(day)
        capture_once(store, AllowAllGate(), "nyfed.sofr", sofr, at)
        capture_once(store, AllowAllGate(), "nyfed.sofr_index", index, at)


@pytest.fixture(scope="module")
def backend():
    fake = FakeBlobBackend()
    capture_all(BlobObjectStore(fake))
    return fake


def args(output: Path) -> list[str]:
    return [
        "--output", str(output),
        "--cutoff", "2026-11-01T00:00:00Z",
        "--history-from", START.isoformat(),
        "--rits-calendar", str(CAL / "rits-2026.yaml"),
        "--nsw-calendar", str(CAL / "nsw-2026.yaml"),
    ]  # fmt: skip


def run(backend, output: Path) -> int:
    return tool.main(args(output), environ={}, backend_builder=lambda _e: backend, code=lambda: CODE)


def test_without_a_window_the_old_rows_refuse(backend, tmp_path):
    local = LocalObjectStore(tmp_path / "s")
    source = BlobObjectStore(backend)
    for key in source.list(""):
        local.put(key, source.get(key))
    cals = Calendars(RITS, NSW, sofr_calendar(local, CUTOFF))
    with pytest.raises(CalendarCoverageError):
        ingest_pending(vintage_store(local, cals), CUTOFF)


def test_a_window_builds_and_every_manifest_states_it(backend, tmp_path):
    out = tmp_path / "out"
    assert run(backend, out) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["history_from"] == START.isoformat() and len(summary["outputs"]) == 4
    assert (out / "report.json").exists() and (out / "report.md").exists()
    for dataset_id in summary["outputs"]:
        assert (out / "releases" / dataset_id / "data.csv").exists()


def test_the_window_only_removes_the_old_rows(backend, tmp_path):
    """The same rows as a build whose file never held the old row, and a manifest that says so."""
    plain = LocalObjectStore(tmp_path / "plain")
    for day in AUD_DAYS[1:]:
        at = datetime(day.year, day.month, day.day, 10, tzinfo=UTC) - timedelta(hours=11)
        capture_once(plain, AllowAllGate(), "rba.f1", f1_csv(day), at)
    for day in US_DAYS[1:]:
        at = datetime(day.year, day.month, day.day, 9, tzinfo=UTC) + timedelta(hours=4)
        sofr, index = ny_json(day)
        capture_once(plain, AllowAllGate(), "nyfed.sofr", sofr, at)
        capture_once(plain, AllowAllGate(), "nyfed.sofr_index", index, at)
    rights = {s: allow(s) for s in SOURCES}
    cals = Calendars(RITS, NSW, sofr_calendar(plain, CUTOFF))
    vs = vintage_store(plain, cals)
    ingest_pending(vs, CUTOFF)
    baseline = build_releases(vs, AllowAllGate(), rights, cals, CUTOFF, CODE)
    assert all("history_from" not in r.core["quality_summary"] for r in baseline.values())

    windowed = LocalObjectStore(tmp_path / "windowed")
    source = BlobObjectStore(backend)
    for key in source.list(""):
        windowed.put(key, source.get(key))
    cals = Calendars(RITS, NSW, sofr_calendar(windowed, CUTOFF))
    vs = vintage_store(windowed, cals, earliest=START)
    ingest_pending(vs, CUTOFF)
    built = build_releases(vs, AllowAllGate(), rights, cals, CUTOFF, CODE, history_from=START)
    for dataset_id, release in built.items():
        assert release.files["data.csv"] == baseline[dataset_id].files["data.csv"]
        assert release.core["quality_summary"]["history_from"] == START.isoformat()


def test_the_evidence_store_is_only_read(backend, tmp_path):
    before = BlobObjectStore(backend).snapshot()
    assert run(backend, tmp_path / "out") == 0
    assert BlobObjectStore(backend).snapshot() == before


@pytest.mark.parametrize("where", ["inside", "not_empty"])
def test_an_unsafe_output_refuses_before_any_read(where, tmp_path, capsys):
    if where == "inside":
        output = REPO / "tests" / "not-to-be-created"
    else:
        output = tmp_path / "used"
        output.mkdir()
        (output / "x").write_text("x")

    def boom(_e):
        raise AssertionError("read the store")

    assert tool.main(args(output), environ={}, backend_builder=boom, code=lambda: CODE) == 2
    assert "--output" in capsys.readouterr().err
    assert where != "inside" or not output.exists()


def test_a_dirty_tree_refuses(backend, tmp_path, monkeypatch, capsys):
    class Result:
        stdout = " M src/hio/x.py\n"

    monkeypatch.setattr(tool.subprocess, "run", lambda *_a, **_k: Result())
    rc = tool.main(args(tmp_path / "out"), environ={}, backend_builder=lambda _e: backend)
    assert rc == 2 and "uncommitted" in capsys.readouterr().err


def test_a_provider_error_is_named_by_type_alone(tmp_path, capsys):
    class Broken(FakeBlobBackend):
        def keys(self, _prefix):
            raise OSError("secret provider text")

    rc = tool.main(args(tmp_path / "out"), environ={}, backend_builder=lambda _e: Broken(), code=lambda: CODE)
    err = capsys.readouterr().err
    assert rc == 2 and "OSError" in err and "secret" not in err
