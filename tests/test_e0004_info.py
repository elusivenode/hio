"""E-0004 step 1: the information count, on invented sequences only."""

import hashlib
import importlib.util
import json
import sys
import types
from datetime import date
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("e0004_info", REPO / "tools" / "e0004_info.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["e0004_info"] = tool
_spec.loader.exec_module(tool)

A, N, U = "accelerating", "not", "unavailable"
CALM, BAD = 0.01, -0.06


def spy_with(n, stress):
    return [BAD if i in stress else CALM for i in range(n)]


def test_runs_are_broken_by_unavailable_and_by_state_change():
    states = [A, A, N, N, A, U, A, A, N, U, N]
    out = tool.count(states, [CALM] * len(states))
    assert out["accelerating"]["runs"] == 3  # [0,1], [4], [6,7]
    assert out["not"]["runs"] == 3  # [2,3], [8], [10]
    assert out["accelerating"]["months"] == 5
    assert out["not"]["months"] == 4
    assert out["unavailable"] == 2


def test_stress_threshold_is_inclusive_and_unavailable_is_excluded():
    states = [A, A, A, U]
    spy = [-0.05, -0.0499, -0.2, -0.3]
    out = tool.count(states, spy)
    assert out["accelerating"]["stress_months"] == 2
    assert out["accelerating"]["clusters"] == 1  # periods 0 and 2 are one apart
    assert out["not"]["stress_months"] == 0


def test_clusters_join_at_a_gap_of_two_and_split_at_three():
    states = [A] * 8
    joined = tool.count(states, spy_with(8, {0, 3}))  # periods 1 and 2 lie between
    split = tool.count(states, spy_with(8, {0, 4}))  # periods 1, 2 and 3 lie between
    assert joined["accelerating"]["clusters"] == 1
    assert split["accelerating"]["clusters"] == 2


def test_a_chain_of_stress_months_is_one_cluster():
    out = tool.count([A] * 10, spy_with(10, {0, 3, 6, 9}))
    assert out["accelerating"]["clusters"] == 1
    assert out["accelerating"]["concentration"] == 1.0


def test_a_break_splits_a_cluster():
    states = [A, U, A, A]
    out = tool.count(states, spy_with(4, {0, 2}))
    assert out["accelerating"]["clusters"] == 2
    assert out["accelerating"]["concentration"] == 0.5


def test_a_cluster_straddling_both_states_counts_for_both():
    states = [A, A, N, N]
    out = tool.count(states, spy_with(4, {1, 2}))
    assert out["accelerating"]["clusters"] == 1
    assert out["not"]["clusters"] == 1
    assert out["accelerating"]["concentration"] == 1.0
    assert out["not"]["concentration"] == 1.0


def test_concentration_is_the_largest_clusters_share_of_the_states_stress_months():
    # in A: cluster {0, 2} holds 2 of 4 stress months, then singletons at 8 and 12
    states = [A] * 14
    out = tool.count(states, spy_with(14, {0, 2, 8, 12}))
    assert out["accelerating"]["stress_months"] == 4
    assert out["accelerating"]["clusters"] == 3
    assert out["accelerating"]["concentration"] == 0.5


def test_concentration_is_zero_without_stress():
    out = tool.count([A, N], [CALM, CALM])
    assert out["accelerating"]["concentration"] == 0
    assert out["not"]["clusters"] == 0


def test_length_mismatch_refuses():
    with pytest.raises(ValueError):
        tool.count([A, N], [CALM])


# a passing baseline: runs of three alternate, twelve months a state, stress every fourth period
BASE_STATES = ([A] * 3 + [N] * 3) * 4
BASE_SPY = spy_with(24, set(range(0, 24, 4)))


@pytest.fixture
def lowered(monkeypatch):
    monkeypatch.setattr(tool, "MIN_MONTHS", 12)
    monkeypatch.setattr(tool, "MIN_RUNS", 4)
    monkeypatch.setattr(tool, "MIN_CLUSTERS", 2)
    monkeypatch.setattr(tool, "MAX_CONCENTRATION", 0.5)


@pytest.mark.usefixtures("lowered")
def test_baseline_passes_with_lowered_screen():
    out = tool.count(BASE_STATES, BASE_SPY)
    assert out["accelerating"]["clusters"] == 4
    assert out["not"]["clusters"] == 2
    assert out["not"]["concentration"] == 0.5
    assert out["screen"] == {"pass": True, "failed": []}


@pytest.mark.parametrize(
    ("name", "value", "failed"),
    [
        ("MIN_MONTHS", 13, ["accelerating: months", "not: months"]),
        ("MIN_RUNS", 5, ["accelerating: runs", "not: runs"]),
        ("MIN_CLUSTERS", 3, ["not: clusters"]),
        ("MAX_CONCENTRATION", 0.4, ["not: concentration"]),
    ],
)
@pytest.mark.usefixtures("lowered")
def test_each_screen_condition_fails_alone(monkeypatch, name, value, failed):
    monkeypatch.setattr(tool, name, value)
    out = tool.count(BASE_STATES, BASE_SPY)
    assert out["screen"]["pass"] is False
    assert out["screen"]["failed"] == failed


def test_real_screen_values():
    assert (tool.MIN_MONTHS, tool.MIN_RUNS, tool.MIN_CLUSTERS, tool.MAX_CONCENTRATION) == (48, 4, 3, 0.5)
    assert tool.count(BASE_STATES, BASE_SPY)["screen"]["pass"] is False


def test_states_csv_has_no_returns():
    text = tool.states_csv([date(2020, 1, 31), date(2020, 2, 29), date(2020, 3, 31)], [A, U])
    assert text == (
        "period_start,period_end,state\n2020-01-31,2020-02-29,accelerating\n2020-02-29,2020-03-31,unavailable\n"
    )


# --- main, with every loader replaced: nothing outside the temp dirs is read


def fake_world(tmp_path, monkeypatch, cpi_manifest=b'{"invented": 1}', eodhd_sha=None):
    t0023 = tmp_path / "t0023"
    run_dir = tmp_path / "run"
    raw = tmp_path / "raw"
    for d in (t0023, run_dir, raw):
        d.mkdir()
    sha = tool.EODHD_MANIFEST_SHA if eodhd_sha is None else eodhd_sha
    record = {"inputs": {"eodhd_snapshot": {"files": {"manifest.json": sha}}}}
    (run_dir / "run.json").write_text(json.dumps(record))
    (raw / "manifest.json").write_bytes(cpi_manifest)

    months = [date(2020, 1, 31), date(2020, 2, 29), date(2020, 3, 31), date(2020, 4, 30)]
    panel = types.SimpleNamespace(months=months)
    monkeypatch.setattr(tool.ev, "check_root", lambda *_: None)
    monkeypatch.setattr(tool.ev, "code_commit", lambda: {"commit": "abcdef0123456789"})
    monkeypatch.setattr(tool.common, "load_frozen", lambda *_: (panel, run_dir))
    monkeypatch.setattr(tool.common, "usd_columns", lambda *_: {"equity": [0.01, -0.07, 0.02]})
    fake = types.SimpleNamespace(
        load_cpi=lambda *_: {},
        load_releases=lambda *_: [],
        states=lambda *_: [U, A, N],
    )
    monkeypatch.setitem(sys.modules, "e0004_state", fake)
    return t0023, raw


def run_main(tmp_path, t0023, raw):
    runs = tmp_path / "runs"
    argv = ["--t0023-root", str(t0023), "--cpi-raw", str(raw), "--runs", str(runs)]
    return tool.main(argv), runs


def test_main_refuses_a_wrong_cpi_manifest_hash(tmp_path, monkeypatch, capsys):
    t0023, raw = fake_world(tmp_path, monkeypatch)
    code, runs = run_main(tmp_path, t0023, raw)
    assert code == 2
    assert not runs.exists()
    assert capsys.readouterr().out == ""


def test_main_refuses_a_wrong_snapshot_manifest_hash(tmp_path, monkeypatch):
    t0023, raw = fake_world(tmp_path, monkeypatch, eodhd_sha="0" * 64)
    monkeypatch.setattr(tool, "CPI_MANIFEST_SHA", hashlib.sha256(b'{"invented": 1}').hexdigest())
    code, runs = run_main(tmp_path, t0023, raw)
    assert code == 2
    assert not runs.exists()


def test_main_refuses_a_missing_cpi_manifest(tmp_path, monkeypatch):
    t0023, raw = fake_world(tmp_path, monkeypatch)
    (raw / "manifest.json").unlink()
    code, _ = run_main(tmp_path, t0023, raw)
    assert code == 2


def test_main_writes_counts_and_states_and_prints_counts_only(tmp_path, monkeypatch, capsys):
    t0023, raw = fake_world(tmp_path, monkeypatch)
    monkeypatch.setattr(tool, "CPI_MANIFEST_SHA", hashlib.sha256(b'{"invented": 1}').hexdigest())
    code, runs = run_main(tmp_path, t0023, raw)
    assert code == 0  # the screen fails on this tiny sample, and that is a result
    (out,) = list(runs.iterdir())
    assert out.name.endswith("-abcdef01")
    counts = json.loads((out / "counts.json").read_text())
    assert counts["unavailable"] == 1
    assert counts["screen"]["pass"] is False
    assert counts["accelerating"]["stress_months"] == 1
    states = (out / "states.csv").read_text()
    assert states.splitlines()[0] == "period_start,period_end,state"
    assert "0.07" not in states
    printed = capsys.readouterr().out
    assert json.loads(printed) == counts
    assert "0.07" not in printed


def test_module_does_not_import_the_state_tool_at_the_top():
    source = (REPO / "tools" / "e0004_info.py").read_text()
    assert "\nimport e0004_state" not in source
    assert "\n    import e0004_state" in source
