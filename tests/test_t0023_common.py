"""T-0023 (OD-0178): the shared frozen-panel helpers, on invented data only. Nothing here reads a research
store, touches the network or runs a tool against real data."""

import hashlib
import json
import stat
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import e0003_aud_cash as base  # noqa: E402
import e0003_extended as ext  # noqa: E402
import e0003_panel as panel_tool  # noqa: E402
import eodhd_eval as ev  # noqa: E402
import t0023_common as common  # noqa: E402

MONTHS = [date(2020, 1, 31), date(2020, 2, 29), date(2020, 3, 31), date(2020, 4, 30)]
RETURNS = np.array(
    [
        [0.0123456789, 0.0011, 0.0045, 0.0030],
        [-0.0456789012, 0.0012, 0.0100, 0.0031],
        [0.0300000000, 0.0010, -0.0070, 0.0029],
    ]
)
BILLS = np.array([0.0011, 0.0012, 0.0010])
S = np.array([0.0200, -0.0150, 0.0050])
RETURNS[:, 1] = (1 + BILLS) * (1 + S) - 1  # the AUD bills column is always the USD bills with RA 4.1 applied


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def frozen() -> common.FrozenPanel:
    return common.FrozenPanel(list(MONTHS), RETURNS.copy(), BILLS.copy(), S.copy())


def invented_text() -> str:
    built = ext.Assembled(list(MONTHS), RETURNS.copy(), BILLS.copy(), S.copy(), 0, {}, {})
    return panel_tool.panel_text(built)


def make_run(root: Path, name: str, panel_id: str, text: str, recorded_sha: str | None = None) -> Path:
    run = root / "runs" / name
    run.mkdir(parents=True)
    data = text.encode()
    (run / "panel.csv").write_bytes(data)
    record = {"panel_id": panel_id, "panel_sha256": recorded_sha or hashlib.sha256(data).hexdigest()}
    (run / "run.json").write_text(json.dumps(record))
    return run


# --- parse_panel


def test_parse_panel_round_trips_panel_text():
    parsed = common.parse_panel(invented_text())
    assert parsed.months == MONTHS
    np.testing.assert_allclose(parsed.returns, RETURNS, rtol=0, atol=1e-12)
    np.testing.assert_allclose(parsed.usd_bills, BILLS, rtol=0, atol=1e-12)
    np.testing.assert_allclose(parsed.s, S, rtol=0, atol=1e-12)
    assert parsed.returns.shape == (3, len(base.SLEEVES))


@pytest.mark.parametrize("text", ["", ",".join(panel_tool.CONVENTIONS["panel_columns"]) + "\n"])
def test_parse_panel_stops_on_an_empty_panel(text):
    with pytest.raises(ev.Stop, match="empty"):
        common.parse_panel(text)


# --- load_frozen


def test_load_frozen_picks_the_newest_matching_run(tmp_path):
    older = invented_text()
    newer_built = ext.Assembled(MONTHS[:3], RETURNS[:2].copy(), BILLS[:2].copy(), S[:2].copy(), 0, {}, {})
    make_run(tmp_path, "20261101T000000Z", "id-a", older)
    newest = make_run(tmp_path, "20261103T000000Z", "id-a", panel_tool.panel_text(newer_built))
    make_run(tmp_path, "20261104T000000Z", "id-other", older)
    panel, run_dir = common.load_frozen(tmp_path, "id-a")
    assert run_dir == newest
    assert panel.months == MONTHS[:3]


def test_load_frozen_skips_other_ids_and_directories_without_a_record(tmp_path):
    wanted = make_run(tmp_path, "20261101T000000Z", "id-a", invented_text())
    make_run(tmp_path, "20261102T000000Z", "id-other", invented_text())
    (tmp_path / "runs" / "20261103T000000Z").mkdir()
    _, run_dir = common.load_frozen(tmp_path, "id-a")
    assert run_dir == wanted


def test_load_frozen_stops_when_no_run_holds_the_id(tmp_path):
    make_run(tmp_path, "20261101T000000Z", "id-other", invented_text())
    with pytest.raises(ev.Stop, match="no rebuild"):
        common.load_frozen(tmp_path, "id-a")


def test_load_frozen_stops_without_any_runs(tmp_path):
    with pytest.raises(ev.Stop, match="no rebuild"):
        common.load_frozen(tmp_path, "id-a")


def test_load_frozen_stops_on_a_tampered_panel(tmp_path):
    run = make_run(tmp_path, "20261101T000000Z", "id-a", invented_text())
    (run / "panel.csv").write_bytes((run / "panel.csv").read_bytes().replace(b"0.0123", b"0.0124"))
    with pytest.raises(ev.Stop, match="doesn't match its record"):
        common.load_frozen(tmp_path, "id-a")


def test_load_frozen_does_not_fall_back_when_the_newest_match_is_tampered(tmp_path):
    make_run(tmp_path, "20261101T000000Z", "id-a", invented_text())
    make_run(tmp_path, "20261102T000000Z", "id-a", invented_text(), recorded_sha="0" * 64)
    with pytest.raises(ev.Stop, match="20261102T000000Z"):
        common.load_frozen(tmp_path, "id-a")


# --- usd_columns, with_changes


def test_usd_columns_undoes_ra_4_1_by_hand():
    cols = common.usd_columns(frozen())
    equity = [(1 + 0.0123456789) / 1.02 - 1, (1 - 0.0456789012) / 0.985 - 1, 1.03 / 1.005 - 1]
    treasury = [1.0045 / 1.02 - 1, 1.0100 / 0.985 - 1, 0.993 / 1.005 - 1]
    np.testing.assert_allclose(cols["equity"], equity, rtol=0, atol=1e-15)
    np.testing.assert_allclose(cols["treasury"], treasury, rtol=0, atol=1e-15)
    np.testing.assert_array_equal(cols["bills"], BILLS)
    assert set(cols) == {"equity", "bills", "treasury"}


def test_with_changes_with_no_change_reproduces_the_panel():
    original = frozen()
    again = common.with_changes(original)
    np.testing.assert_allclose(again.returns, original.returns, rtol=0, atol=1e-12)
    np.testing.assert_array_equal(again.usd_bills, original.usd_bills)
    np.testing.assert_array_equal(again.s, original.s)
    assert again.months == original.months


def test_with_changes_changes_only_what_it_names():
    original = frozen()
    new_treasury = np.array([0.01, 0.02, 0.03])
    changed = common.with_changes(original, usd={"treasury": new_treasury})
    i = {name: base.SLEEVES.index(name) for name in base.SLEEVES}
    np.testing.assert_allclose(
        changed.returns[:, i["treasury"]], (1 + new_treasury) * (1 + S) - 1, atol=1e-15
    )
    for other in ("equity", "bills", "cash"):
        np.testing.assert_allclose(changed.returns[:, i[other]], RETURNS[:, i[other]], rtol=0, atol=1e-12)
    np.testing.assert_array_equal(changed.s, S)
    np.testing.assert_array_equal(changed.usd_bills, BILLS)


def test_with_changes_cash_replaces_only_the_aud_cash_column():
    new_cash = np.array([0.004, 0.005, 0.006])
    changed = common.with_changes(frozen(), cash=new_cash)
    np.testing.assert_array_equal(changed.returns[:, base.SLEEVES.index("cash")], new_cash)
    for name in ("equity", "bills", "treasury"):
        j = base.SLEEVES.index(name)
        np.testing.assert_allclose(changed.returns[:, j], RETURNS[:, j], rtol=0, atol=1e-12)


def test_with_changes_fx_reapplies_ra_4_1_to_the_usd_sleeves():
    new_s = np.array([0.0, 0.01, -0.02])
    original = frozen()
    usd = common.usd_columns(original)
    changed = common.with_changes(original, s=new_s)
    np.testing.assert_array_equal(changed.s, new_s)
    np.testing.assert_allclose(changed.returns[:, 0], (1 + usd["equity"]) * (1 + new_s) - 1, atol=1e-15)
    np.testing.assert_allclose(changed.returns[:, 1], (1 + BILLS) * (1 + new_s) - 1, atol=1e-15)
    np.testing.assert_allclose(changed.returns[:, 3], RETURNS[:, 3], rtol=0, atol=1e-15)
    np.testing.assert_array_equal(changed.usd_bills, BILLS)


@pytest.mark.parametrize(
    ("kwargs", "name"),
    [
        ({"usd": {"equity": np.zeros(2)}}, "equity"),
        ({"cash": np.zeros(4)}, "cash"),
        ({"s": np.zeros(2)}, "fx"),
    ],
)
def test_with_changes_stops_on_a_wrong_length(kwargs, name):
    with pytest.raises(ev.Stop, match=f"{name} doesn't cover"):
        common.with_changes(frozen(), **kwargs)


# --- class_changes


def entry(kind: str) -> dict[str, str]:
    return {"class": kind}


def test_class_changes_lists_exactly_the_changed_pairs():
    a = {
        "total": {"volatility": entry("mixed"), "annualised_return": entry("distinguished")},
        "treasury_duration": {"volatility": entry("not_distinguished"), "annualised_return": entry("mixed")},
    }
    b = {
        "total": {"volatility": entry("mixed"), "annualised_return": entry("not_distinguished")},
        "treasury_duration": {"volatility": entry("distinguished"), "annualised_return": entry("mixed")},
    }
    assert common.class_changes(a, b) == [
        "total.annualised_return: distinguished -> not_distinguished",
        "treasury_duration.volatility: not_distinguished -> distinguished",
    ]


def test_class_changes_is_empty_when_nothing_changes():
    a = {"total": {"volatility": entry("mixed")}}
    assert common.class_changes(a, {"total": {"volatility": entry("mixed")}}) == []


# --- compound_between

M3 = [date(2020, 1, 31), date(2020, 2, 29), date(2020, 3, 31)]


def test_compound_between_by_hand():
    periods = [
        (date(2020, 2, 10), date(2020, 2, 29), 0.02),  # given out of order
        (date(2020, 1, 31), date(2020, 2, 10), 0.01),
        (date(2020, 2, 29), date(2020, 3, 31), 0.03),
    ]
    out = common.compound_between(periods, M3)
    np.testing.assert_allclose(out, [1.01 * 1.02 - 1, 0.03], rtol=0, atol=1e-15)


def test_compound_between_stops_on_a_gap():
    periods = [
        (date(2020, 1, 31), date(2020, 2, 10), 0.01),
        (date(2020, 2, 12), date(2020, 2, 29), 0.02),
        (date(2020, 2, 29), date(2020, 3, 31), 0.03),
    ]
    with pytest.raises(ev.Stop, match="a gap in coverage at 2020-02-10"):
        common.compound_between(periods, M3)


def test_compound_between_stops_when_coverage_stops_short():
    periods = [(date(2020, 1, 31), date(2020, 2, 20), 0.01)]
    with pytest.raises(ev.Stop, match="stops short of 2020-02-29"):
        common.compound_between(periods, M3)


def test_compound_between_stops_when_the_start_is_missing():
    periods = [(date(2020, 2, 5), date(2020, 2, 29), 0.01), (date(2020, 2, 29), date(2020, 3, 31), 0.03)]
    with pytest.raises(ev.Stop, match="no period starts by 2020-01-31"):
        common.compound_between(periods, M3)


def test_compound_between_stops_when_every_period_ended_before_the_start():
    periods = [(date(2020, 1, 1), date(2020, 1, 31), 0.01)]
    with pytest.raises(ev.Stop, match="no period starts by"):
        common.compound_between(periods, M3)


# --- new_output, write_outputs


def test_new_output_is_private_and_named_by_step_time_and_commit(tmp_path):
    tmp_path.chmod(0o700)
    now = datetime(2026, 11, 5, 1, 2, 3, tzinfo=UTC)
    out = common.new_output(tmp_path, "step4", "abcdef0123456789", now)
    assert out == tmp_path / "corroboration" / "step4" / "20261105T010203Z-abcdef01"
    assert out.is_dir()
    assert mode(out) == 0o700


def test_new_output_refuses_an_existing_directory(tmp_path):
    tmp_path.chmod(0o700)
    now = datetime(2026, 11, 5, 1, 2, 3, tzinfo=UTC)
    out = common.new_output(tmp_path, "step4", "abcdef0123456789", now)
    (out / "keep.txt").write_text("kept")
    with pytest.raises(FileExistsError):
        common.new_output(tmp_path, "step4", "abcdef0123456789", now)
    assert (out / "keep.txt").read_text() == "kept"


def test_write_outputs_files_are_private(tmp_path):
    tmp_path.chmod(0o700)
    out = common.new_output(tmp_path, "step4", "abcdef0123456789")
    common.write_outputs(out, "# report\n", {"b": 2, "a": 1})
    assert (out / "report.md").read_text() == "# report\n"
    assert (out / "summary.json").read_text() == '{\n "a": 1,\n "b": 2\n}\n'
    assert mode(out / "report.md") == 0o600
    assert mode(out / "summary.json") == 0o600
