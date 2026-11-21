"""E-0004 step 1b: the precision check, on invented sequences only."""

import hashlib
import importlib.util
import json
import sys
import types
from datetime import date
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("e0004_precision", REPO / "tools" / "e0004_precision.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["e0004_precision"] = tool
_spec.loader.exec_module(tool)

A, N, U = "accelerating", "not", "unavailable"


# --- benefit


def test_benefit_both_negative():
    # R_T = 0.6*-0.10 + 0.4*-0.05 = -0.08; R_B = 0.6*-0.10 + 0.4*0.01 = -0.056; b = 0.056 - 0.08
    out = tool.benefit([-0.10], [-0.05], [0.01])
    assert out[0] == pytest.approx(-0.024)


def test_benefit_one_negative():
    # R_T = 0.6*0.01 + 0.4*-0.10 = -0.034 (a loss); R_B = 0.006 + 0.4*0.0 > 0 (none); b = 0 - 0.034
    out = tool.benefit([0.01], [-0.10], [0.0])
    assert out[0] == pytest.approx(-0.034)
    # the other way: the bond leg gains, the bill leg loses
    out = tool.benefit([-0.05], [0.10], [-0.10])
    # R_T = -0.03 + 0.04 = 0.01 (none); R_B = -0.03 - 0.04 = -0.07; b = 0.07
    assert out[0] == pytest.approx(0.07)


def test_benefit_no_loss():
    out = tool.benefit([0.02, 0.0], [0.01, 0.0], [0.0, 0.0])
    assert list(out) == [0.0, 0.0]


def test_benefit_refuses_unequal_lengths():
    with pytest.raises(ValueError):
        tool.benefit([0.0, 0.1], [0.0], [0.0, 0.0])


# --- delta, segments, shifted


def test_delta_excludes_unavailable_and_averages_each_state():
    b = [1.0, 3.0, 100.0, 0.5, 1.5]
    states = [A, A, U, N, N]
    assert tool.delta(b, states) == pytest.approx(2.0 - 1.0)


def test_delta_is_none_without_a_state():
    assert tool.delta([1.0, 2.0], [A, A]) is None
    assert tool.delta([1.0, 2.0], [N, U]) is None
    assert tool.delta([1.0, 2.0], [U, U]) is None


def test_segments():
    assert tool.segments([U, A, N, U, U, N, A, A, U]) == [range(1, 3), range(5, 8)]
    assert tool.segments([A, N]) == [range(0, 2)]
    assert tool.segments([U, U]) == []
    assert tool.segments([]) == []


def test_shifted_matches_np_roll_and_moves_breaks():
    states = [U, A, N, A, N]
    for k in (0, 1, 2, 4, 5, 7):
        assert tool.shifted(states, k) == list(np.roll(np.array(states, dtype=object), k))
    assert tool.shifted(states, 1) == [N, U, A, N, A]


# --- bootstrap


def reference(b, states, picks, block):
    """A plain loop of the declared procedure, from the same starting picks."""
    segs = tool.segments(states)
    available = [i for r in segs for i in r]
    m = len(available)
    out = []
    for row in picks:
        drawn = []
        for p in row:
            i = available[p]
            seg = next(r for r in segs if i in r)
            for j in range(block):
                drawn.append(seg.start + (i - seg.start + j) % len(seg))
        drawn = drawn[:m]
        a = [b[i] for i in drawn if states[i] == A]
        o = [b[i] for i in drawn if states[i] == N]
        out.append(None if not a or not o else sum(a) / len(a) - sum(o) / len(o))
    return out


def test_bootstrap_matches_a_plain_loop_with_wrapping_and_truncation():
    states = [A, N, A, U, N, A, N, N, U, U, A, N]
    b = [0.5, -1.0, 2.0, 99.0, 0.25, -0.75, 1.5, 3.0, 99.0, 99.0, -2.0, 0.125]
    block, reps, seed = 4, 200, 7
    deltas, dropped = tool.bootstrap(b, states, block=block, reps=reps, seed=seed)
    m = sum(len(r) for r in tool.segments(states))
    picks = np.random.default_rng(seed).integers(0, m, size=(reps, -(-m // block)))
    expected = reference(b, states, picks, block)
    kept = [x for x in expected if x is not None]
    assert dropped == expected.count(None)
    assert len(deltas) == len(kept) == reps - dropped
    assert np.allclose(deltas, kept)


def test_bootstrap_never_crosses_a_break():
    # Segment one is all accelerating with b = 0; segment two all "not" with b = 1.
    # Blocks of 3 cover a whole segment by wrapping, so every kept delta is exactly 0 - 1.
    states = [A, A, A, U, N, N, N]
    b = [0.0, 0.0, 0.0, 50.0, 1.0, 1.0, 1.0]
    deltas, dropped = tool.bootstrap(b, states, block=3, reps=300, seed=1)
    assert len(deltas) + dropped == 300
    assert dropped > 0  # some replications drew one segment only
    assert np.allclose(deltas, -1.0)


def test_bootstrap_wraps_inside_a_short_segment():
    states = [A, N, U, N, N, N, N, N]
    b = [1.0, 0.0, 9.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    deltas, _ = tool.bootstrap(b, states, block=6, reps=50, seed=3)
    assert len(deltas) > 0
    assert np.all(np.isfinite(deltas))


def test_bootstrap_is_deterministic_for_a_seed():
    states = [A, N] * 10
    b = list(np.linspace(-1, 1, 20))
    one = tool.bootstrap(b, states, block=3, reps=100, seed=11)
    two = tool.bootstrap(b, states, block=3, reps=100, seed=11)
    other = tool.bootstrap(b, states, block=3, reps=100, seed=12)
    assert np.array_equal(one[0], two[0]) and one[1] == two[1]
    assert not np.array_equal(one[0], other[0])


def test_bootstrap_counts_dropped_replications():
    states = [A, A, A, A, A, A, A, A, A, A, N]
    b = [0.0] * 10 + [1.0]
    deltas, dropped = tool.bootstrap(b, states, block=1, reps=500, seed=5)
    assert dropped > 0
    assert len(deltas) + dropped == 500
    allr = tool.bootstrap([0.0, 0.0], [A, A], block=2, reps=10, seed=1)
    assert len(allr[0]) == 0 and allr[1] == 10


def test_bootstrap_refuses_unequal_lengths():
    with pytest.raises(ValueError):
        tool.bootstrap([0.0], [A, N], block=2, reps=10, seed=1)


def test_interval_uses_linear_quantiles():
    lo, hi = tool.interval(list(range(101)))
    assert (lo, hi) == (pytest.approx(2.5), pytest.approx(97.5))


# --- precision


def test_precision_uses_shifts_13_to_n_minus_13_and_returns_no_delta(monkeypatch):
    n = 30
    states = [A, N] * (n // 2)
    b = list(np.linspace(-0.01, 0.01, n))
    seen = []
    real = tool.shifted

    def spy_shifted(s, k):
        seen.append(k)
        return real(s, k)

    monkeypatch.setattr(tool, "shifted", spy_shifted)
    out = tool.precision(b, states, block=3, reps=50)
    assert seen == [13, 14, 15, 16, 17]
    assert out["shifts"] == 5
    assert set(out) == {"shifts", "median_half_width", "pass", "dropped"}
    assert out["pass"] is (out["median_half_width"] <= 0.0020)


def test_precision_passes_when_b_is_constant_and_fails_when_wide():
    states = [A, N] * 20
    flat = tool.precision([0.001] * 40, states, block=4, reps=100)
    assert flat["median_half_width"] == pytest.approx(0.0, abs=1e-12)
    assert flat["pass"] is True
    noisy = list(np.random.default_rng(0).normal(0.0, 0.1, 40))
    wide = tool.precision(noisy, [A, A, N, N] * 10, block=4, reps=100)
    assert wide["pass"] is False


def test_precision_refuses_a_sample_too_short_for_any_shift():
    with pytest.raises(ValueError):
        tool.precision([0.0] * 20, [A, N] * 10, block=3, reps=10)


# --- main, with every loader replaced: nothing outside the temp dirs is read

SPY = [0.011, -0.083, 0.021, -0.0417, 0.0333, 0.0157] * 6
IEF = [0.0021, 0.0192, -0.0054, 0.0113, -0.0071, 0.0049] * 6
BIL = [0.0003, 0.0004, 0.0002, 0.0003, 0.0004, 0.0002] * 6


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

    n = len(SPY)
    months = [date(2020 + i // 12, i % 12 + 1, 1) for i in range(n + 1)]
    panel = types.SimpleNamespace(months=months)
    monkeypatch.setattr(tool.ev, "check_root", lambda *_: None)
    monkeypatch.setattr(tool.ev, "code_commit", lambda: {"commit": "abcdef0123456789"})
    monkeypatch.setattr(tool.common, "load_frozen", lambda *_: (panel, run_dir))
    monkeypatch.setattr(tool.common, "usd_columns", lambda *_: {"equity": SPY, "treasury": IEF, "bills": BIL})
    states = [U] * 12 + [A, N, N, A, A, N] * 4
    fake = types.SimpleNamespace(
        load_cpi=lambda *_: {},
        load_releases=lambda *_: [],
        states=lambda *_: states,
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


def test_main_writes_the_median_half_width_and_no_delta(tmp_path, monkeypatch, capsys):
    t0023, raw = fake_world(tmp_path, monkeypatch)
    monkeypatch.setattr(tool, "CPI_MANIFEST_SHA", hashlib.sha256(b'{"invented": 1}').hexdigest())
    code, runs = run_main(tmp_path, t0023, raw)
    assert code == 0
    (out,) = list(runs.iterdir())
    assert out.name.endswith("-abcdef01")
    written = (out / "precision.json").read_text()
    result = json.loads(written)
    assert set(result) == {"code", "shifts", "median_half_width", "pass", "dropped"}
    printed = capsys.readouterr().out
    assert json.loads(printed) == result
    # no b value, delta or mean appears anywhere in what was written or printed
    b = tool.benefit(SPY, IEF, BIL)
    for text in (written, printed, *(p.read_text() for p in out.iterdir())):
        assert "delta" not in text.lower()
        for v in set(b) - {0.0}:
            assert repr(float(v)) not in text
    assert [p.name for p in out.iterdir()] == ["precision.json"]


def test_module_does_not_import_the_state_tool_at_the_top():
    source = (REPO / "tools" / "e0004_precision.py").read_text()
    assert "\nimport e0004_state" not in source
    assert "\n    import e0004_state" in source
