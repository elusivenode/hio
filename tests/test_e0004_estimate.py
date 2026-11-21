"""E-0004 step 2: the estimate, on invented data only."""

import hashlib
import importlib.util
import json
import sys
import types
from datetime import date
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("e0004_estimate", REPO / "tools" / "e0004_estimate.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["e0004_estimate"] = tool
_spec.loader.exec_module(tool)

import e0004_info as info  # noqa: E402
import e0004_state as state_tool  # noqa: E402

A, N, U = "accelerating", "not", "unavailable"


# --- estimate


def test_estimate_is_deterministic_and_reports_point_interval_dropped():
    states = [A, N, N, A] * 10
    b = list(np.random.default_rng(1).normal(0.0, 0.01, 40))
    one = tool.estimate(b, states, block=3, reps=200, seed=5)
    two = tool.estimate(b, states, block=3, reps=200, seed=5)
    assert one == two
    assert set(one) == {"point", "lo", "hi", "dropped"}
    assert one["lo"] <= one["hi"]
    assert one["point"] == pytest.approx(tool.prec.delta(b, states))


def test_estimate_refuses_a_missing_state():
    with pytest.raises(ValueError):
        tool.estimate([0.0, 1.0], [A, A], block=1, reps=10)


# --- reading


def test_reading_not_distinguished_when_interval_holds_zero():
    assert tool.reading(-0.01, 0.01, [0.5], 0.5) == "not distinguished"
    assert tool.reading(0.0, 0.01, [], 0.005) == "not distinguished"
    assert tool.reading(-0.01, 0.0, [], -0.005) == "not distinguished"


def test_reading_relevant_needs_beyond_threshold_and_no_fragility_problem():
    assert tool.reading(0.0021, 0.01, [0.004, 0.003], 0.005) == "relevant state-dependent difference"
    assert tool.reading(-0.01, -0.0021, [-0.004], -0.005) == "relevant state-dependent difference"
    assert tool.reading(0.0021, 0.01, [], 0.005) == "relevant state-dependent difference"


def test_reading_threshold_edges_are_not_beyond():
    uncertain = "nonzero difference of uncertain relevance"
    assert tool.reading(0.0020, 0.01, [0.004], 0.005) == uncertain
    assert tool.reading(-0.01, -0.0020, [-0.004], -0.005) == uncertain
    relevant = "relevant state-dependent difference"
    assert tool.reading(0.0020, 0.01, [0.004], 0.005, threshold=0.0019) == relevant


def test_reading_each_fragility_violation_downgrades():
    uncertain = "nonzero difference of uncertain relevance"
    assert tool.reading(0.003, 0.01, [0.004, None], 0.005) == uncertain
    assert tool.reading(0.003, 0.01, [0.004, 0.0], 0.005) == uncertain
    assert tool.reading(0.003, 0.01, [0.004, -0.001], 0.005) == uncertain
    assert tool.reading(-0.01, -0.003, [-0.004, 0.001], -0.005) == uncertain


def test_reading_small_nonzero_interval_is_uncertain():
    assert tool.reading(0.0005, 0.001, [0.001], 0.001) == "nonzero difference of uncertain relevance"


# --- persistence


def test_persistence_switches_on_the_nth_consecutive_new_period():
    raw = [A, A, N, N, A, N, N, N, A]
    assert tool.persistence(raw, 3) == [A, A, A, A, A, A, A, N, N]


def test_persistence_starts_at_the_first_available_raw_state():
    assert tool.persistence([U, N, A, A, A, A], 3) == [U, N, N, N, A, A]


def test_persistence_passes_unavailable_through_without_counting_or_breaking():
    raw = [A, N, U, N, U, N, A]
    # three "not" around the breaks switch at the third one; the breaks stay unavailable
    assert tool.persistence(raw, 3) == [A, A, U, A, U, N, N]
    # a break does not reset a pending switch, and an opposite raw state does
    assert tool.persistence([A, N, N, U, A, N, N, N], 3) == [A, A, A, U, A, A, A, N]


def test_persistence_n_one_is_identity_on_available_periods():
    raw = [A, N, U, A, N]
    assert tool.persistence(raw, 1) == raw


# --- fragility


def test_fragility_marks_only_the_cluster():
    states = [A, A, N, N, A, N]
    b = [1.0, 2.0, 0.0, 1.0, 5.0, 3.0]
    frag = tool.fragility(b, states, [[0, 1], [4]])
    assert frag[0] == pytest.approx(5.0 - 4.0 / 3)  # A: only period 4; N: 0, 1, 3
    assert frag[1] == pytest.approx(1.5 - 4.0 / 3)  # A: 0, 1; N: 2, 3, 5
    assert states == [A, A, N, N, A, N]  # the input isn't altered


def test_fragility_is_none_when_a_state_vanishes():
    assert tool.fragility([1.0, 2.0, 0.0], [A, A, N], [[0, 1]]) == [None]


def test_sensitivity_4_removes_exactly_one_period():
    states = [A, N, A, N, A]
    b = [1.0, 0.0, 3.0, 0.0, 5.0]
    marked = list(states)
    marked[2] = U
    assert sum(1 for s in marked if s != U) == len(states) - 1
    assert tool.prec.delta(b, marked) == pytest.approx(3.0 - 0.0)


# --- equal_is_accelerating, clusters


def _cpi_world():
    # the level doubles each calendar year, so every year-on-year rate is exactly 1: always a tie
    cpi = {(y, m): Decimal(100) * 2 ** (y - 2017) for y in range(2017, 2022) for m in range(1, 13)}
    releases = [date(y, m, 15) for y in range(2018, 2022) for m in range(1, 13)]
    month_ends = [date(2020 + i // 12, i % 12 + 1, 28) for i in range(13)]
    return month_ends, releases, cpi


def test_equal_is_accelerating_changes_only_ties():
    month_ends, releases, cpi = _cpi_world()
    default = state_tool.states(month_ends, releases, cpi)
    equal = state_tool.states(month_ends, releases, cpi, equal_is_accelerating=True)
    assert state_tool.states(month_ends, releases, cpi, equal_is_accelerating=False) == default
    assert set(default) == {N}
    assert set(equal) == {A}


def test_clusters_equals_the_count_function_s_clusters():
    states = [A, N, N, A, A, N, N, N, N, A, U, N, N, A]
    spy = [-0.06, 0.0, 0.0, 0.01, -0.07, 0.0, 0.0, 0.0, 0.0, -0.06, -0.06, -0.06, 0.0, -0.06]
    groups = info.clusters(states, spy)
    assert groups == [[0], [4], [9], [11, 13]]
    held = {s: sum(1 for c in groups if any(states[i] == s for i in c)) for s in (A, N)}
    counted = info.count(states, spy)
    assert counted[A]["clusters"] == held[A]
    assert counted[N]["clusters"] == held[N]
    assert info.clusters_of(states, spy) == groups


# --- main, with every loader replaced

N_PERIODS = 36
SPY = [0.011, -0.083, 0.021, -0.0417, 0.0333, 0.0157] * 6
IEF = [0.0021, 0.0192, -0.0054, 0.0113, -0.0071, 0.0049] * 6
BIL = [0.0003, 0.0004, 0.0002, 0.0003, 0.0004, 0.0002] * 6


def fake_world(tmp_path, monkeypatch, cpi_manifest=b'{"invented": 1}', eodhd_sha=None, v1_from=0):
    t0023 = tmp_path / "t0023"
    run_dir = tmp_path / "run"
    raw = tmp_path / "raw"
    for d in (t0023, run_dir, raw):
        d.mkdir()
    sha = tool.EODHD_MANIFEST_SHA if eodhd_sha is None else eodhd_sha
    record = {"inputs": {"eodhd_snapshot": {"files": {"manifest.json": sha}}}}
    (run_dir / "run.json").write_text(json.dumps(record))
    (raw / "manifest.json").write_bytes(cpi_manifest)

    months = [date(2006 + (i + 4) // 12, (i + 4) % 12 + 1, 28) for i in range(N_PERIODS + 1)]
    months[months.index(date(2008, 9, 28))] = date(2008, 9, 30)
    panel = types.SimpleNamespace(months=months)
    monkeypatch.setattr(tool.ev, "check_root", lambda *_: None)
    monkeypatch.setattr(tool.ev, "code_commit", lambda: {"commit": "abcdef0123456789"})
    monkeypatch.setattr(tool.common, "load_frozen", lambda *_: (panel, run_dir))
    monkeypatch.setattr(tool.common, "usd_columns", lambda *_: {"equity": SPY, "treasury": IEF, "bills": BIL})
    states = [A, A, A, N, N, N] * 6

    def fake_states(*_, equal_is_accelerating=False):
        return [A] * 6 + states[6:] if equal_is_accelerating else list(states)

    fake_state = types.SimpleNamespace(
        load_cpi=lambda *_: {}, load_releases=lambda *_: [], states=fake_states
    )
    monkeypatch.setitem(sys.modules, "e0004_state", fake_state)
    periods = [(months[i], months[i + 1], Decimal("0.004")) for i in range(v1_from, N_PERIODS)]
    fake_sleeves = types.SimpleNamespace(
        load_v1=lambda *_: (periods, "digest"),
        compound_months=lambda _per, ms: [0.004] * (len(ms) - 1),
    )
    monkeypatch.setitem(sys.modules, "t0023_sleeves", fake_sleeves)
    return t0023, raw


def run_main(tmp_path, t0023, raw):
    runs = tmp_path / "runs"
    argv = ["--t0023-root", str(t0023), "--cpi-raw", str(raw), "--runs", str(runs), "--e0001", str(tmp_path)]
    return tool.main(argv), runs


def pin_cpi(monkeypatch):
    monkeypatch.setattr(tool, "CPI_MANIFEST_SHA", hashlib.sha256(b'{"invented": 1}').hexdigest())


def test_main_refuses_a_wrong_cpi_manifest_hash(tmp_path, monkeypatch, capsys):
    t0023, raw = fake_world(tmp_path, monkeypatch)
    code, runs = run_main(tmp_path, t0023, raw)
    assert code == 2
    assert not runs.exists()
    assert capsys.readouterr().out == ""


def test_main_refuses_a_wrong_snapshot_manifest_hash(tmp_path, monkeypatch):
    t0023, raw = fake_world(tmp_path, monkeypatch, eodhd_sha="0" * 64)
    pin_cpi(monkeypatch)
    code, runs = run_main(tmp_path, t0023, raw)
    assert code == 2
    assert not runs.exists()


def test_main_writes_result_json_with_every_section(tmp_path, monkeypatch, capsys):
    t0023, raw = fake_world(tmp_path, monkeypatch, v1_from=6)
    pin_cpi(monkeypatch)
    monkeypatch.setattr(tool.info, "STRESS", -0.04)
    real = tool.estimate

    def small(b, s, *, block, reps=200, seed=tool.SEED):
        return real(b, s, block=block, reps=reps, seed=seed)

    monkeypatch.setattr(tool, "estimate", small)
    code, runs = run_main(tmp_path, t0023, raw)
    assert code == 0
    (out,) = list(runs.iterdir())
    result = json.loads((out / "result.json").read_text())
    assert json.loads(capsys.readouterr().out) == result
    assert set(result) >= {"primary", "blocks", "block_disagreement", "fragility", "sensitivities", "n"}
    assert set(result["blocks"]) == {"6", "24"}
    assert set(result["primary"]) >= {"point", "lo", "hi", "dropped", "reading"}
    sens = result["sensitivities"]
    assert set(sens) == {"equal_is_accelerating", "v1_ten_year", "persistence_3", "without_2008_09_30"}
    for s in sens.values():
        assert set(s) >= {"point", "lo", "hi", "reading"}
    assert sens["v1_ten_year"]["overlap_first"] == tool_month(6)
    assert "per_state_mean" not in json.dumps(result)


def tool_month(i):
    return date(2006 + (i + 4) // 12, (i + 4) % 12 + 1, 28).isoformat()
