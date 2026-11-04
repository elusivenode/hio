"""E-0003, on invented data only."""

import importlib.util
import json
import sys
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("e0003_aud_cash", REPO / "tools" / "e0003_aud_cash.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["e0003_aud_cash"] = tool
_spec.loader.exec_module(tool)


def f1(rows, series="FIRMMCTRI"):
    head = f"Title,Cash Rate TRI\nSeries ID,{series}\n"
    return (head + "".join(f"{d},{v}\n" for d, v in rows)).encode()


def test_the_tri_is_parsed_exactly_by_its_series_id():
    levels = tool.parse_tri(f1([("04-Jan-2011", "100.000000"), ("05-Jan-2011", "100.012345")]))
    assert levels[date(2011, 1, 5)] == D("100.012345")


def test_a_receipt_without_the_tri_stops():
    with pytest.raises(tool.ev.Stop, match="doesn't hold"):
        tool.parse_tri(f1([("04-Jan-2011", "100")], series="OTHER"))


def test_a_level_is_the_latest_on_or_before_and_too_old_stops():
    levels = {date(2011, 1, 3): D(100)}
    assert tool.level_on(levels, sorted(levels), date(2011, 1, 5)) == D(100)
    with pytest.raises(tool.ev.Stop, match="within 5 days"):
        tool.level_on(levels, sorted(levels), date(2011, 1, 9))


def test_cash_returns_are_level_ratios_by_hand():
    months = [date(2011, 1, 31), date(2011, 2, 28), date(2011, 3, 31)]
    levels = dict(zip(months, [D(100), D(101), D("102.01")], strict=True))
    assert tool.cash_returns(months, levels).tolist() == pytest.approx([0.01, 0.01])


def test_every_allocation_uses_one_window_from_the_first_tri_level():
    months = [date(2010, 12, 31), date(2011, 1, 31), date(2011, 2, 28)]
    assert tool.common_months(months, date(2011, 1, 4)) == [1, 2]


def test_translation_applies_to_usd_sleeves_and_not_to_aud_cash_by_hand():
    usd = np.array([[0.10, 0.02, 0.01]])  # panel columns below
    out = tool.matrix(usd, ("equity", "treasury", "cash"), np.array([0.05]), np.array([0.003]))
    assert out[0, 0] == pytest.approx(1.10 * 1.05 - 1)  # equity
    assert out[0, 1] == pytest.approx(1.01 * 1.05 - 1)  # bills come from the panel's cash sleeve, BIL
    assert out[0, 2] == pytest.approx(1.02 * 1.05 - 1)  # Treasuries
    assert out[0, 3] == 0.003  # AUD cash is untouched by the currency


def test_each_portfolio_holds_60_equity_and_40_in_one_sleeve():
    for name in tool.PORTFOLIOS:
        v = tool.weights_vector(name)
        assert v.sum() == pytest.approx(1.0)
        assert v[tool.SLEEVES.index("equity")] == 0.6
        assert sorted(v) == [0, 0, 0.4, 0.6]


def test_the_combined_effect_splits_into_labelled_parts_by_hand():
    out = tool.bills_against_cash(np.array([0.01]), np.array([0.05]), np.array([0.003]))
    assert out["difference"] == pytest.approx(1.01 * 1.05 - 1 - 0.003)
    assert out["rate_gap"] == pytest.approx(0.007)
    assert out["currency"] == pytest.approx(0.05)
    assert out["rate_gap"] + out["currency"] + out["cross"] == pytest.approx(out["difference"])


def month_ends(count, year=2011):
    out, month = [], 1
    for _ in range(count):
        first = date(year + month // 12, month % 12 + 1, 1)
        out.append(first - timedelta(days=1))
        year, month = first.year, first.month
    return out


def invented(count=190, seed=4, same=False):
    rng = np.random.default_rng(seed)
    months = month_ends(count)
    returns = rng.normal(0.004, [0.04, 0.03, 0.03, 0.001], size=(count - 1, 4))
    if same:
        returns[:, 1] = returns[:, 3]
    return months, returns, rng.normal(0.001, 0.0005, count - 1), rng.normal(0, 0.03, count - 1)


def test_the_effects_are_the_right_differences_on_one_window():
    months, returns, bills, s = invented()
    window = tool.evaluate(months, returns, bills, s)["windows"]["full"]
    for effect, (a, b) in tool.EFFECTS.items():
        expected = window["portfolios"][b]["volatility"] - window["portfolios"][a]["volatility"]
        assert window["effects"][effect]["volatility"] == pytest.approx(expected)
    total = window["effects"]["total"]["annualised_return"]
    parts = (
        window["effects"]["cash_rate_and_currency"]["annualised_return"]
        + window["effects"]["treasury_duration"]["annualised_return"]
    )
    assert parts == pytest.approx(total)


def test_identical_sleeves_give_no_effect_and_no_uncertainty():
    months, returns, bills, s = invented(same=True)
    results = tool.evaluate(months, returns, bills, s)
    assert results["windows"]["full"]["effects"]["cash_rate_and_currency"]["max_drawdown"] == 0
    for block in results["bootstrap"]["cash_rate_and_currency"].values():
        assert block["volatility"]["low"] == block["volatility"]["high"] == 0
    assert tool.earlier_history_indicated(results) is False
    assert tool.intervals_span_zero(results)["cash_rate_and_currency"]["volatility"] is True


def _window(size, available=True):
    if not available:
        return {"available": False}
    return {"available": True, "effects": {"cash_rate_and_currency": {"max_drawdown": size}}}


def test_the_earlier_history_rule_is_two_points_in_a_named_window():
    results = {"windows": {"full": _window(0.019), "q1_2020": _window(-0.021), "2022": _window(0, False)}}
    assert tool.earlier_history_indicated(results) is True
    results["windows"]["q1_2020"] = _window(0.019)
    assert tool.earlier_history_indicated(results) is False


def test_the_report_states_who_it_is_for_and_the_missing_2008():
    months, returns, bills, s = invented()
    text = tool.render(tool.evaluate(months, returns, bills, s))
    assert text.startswith("# E-0003: for the owner only")
    assert "2008 isn't in the sample" in text
    assert "Reserve Bank of Australia" in text


def test_the_conclusion_follows_the_tests_and_never_quotes_a_size():
    months, returns, bills, s = invented(same=True)
    results = tool.evaluate(months, returns, bills, s)
    text = "\n".join(tool.conclusion(results))
    assert "not indicated by the pre-registered test" in text
    assert "anything about 2008" in text
    months, returns, bills, s = invented()
    other = "\n".join(tool.conclusion(tool.evaluate(months, returns, bills, s)))
    assert "indicated by the pre-registered test" in other


def test_no_2008_window_exists():
    assert "2008" not in tool.WINDOWS
    assert min(s for s, _ in tool.WINDOWS.values() if s != date.min) >= date(2011, 1, 1)


def test_the_rights_allow_each_source_locally_and_no_agent_use_of_eodhd():
    gate = tool.ev.make_gate({})
    for source in (tool.RBA_SOURCE, tool.aud_tool.H10_SOURCE, tool.ev.SOURCE_ID):
        gate.authorise(tool.Operation.BUILD, [source])
    assert str(gate.records[tool.ev.SOURCE_ID].get("agent_context")) == "deny"


def test_a_tampered_receipt_stops(tmp_path):
    tmp_path.chmod(0o700)
    e2 = tmp_path / "e2"
    e2.mkdir(mode=0o700)
    root = tmp_path / "root"
    (root / "raw").mkdir(parents=True, mode=0o700)
    root.chmod(0o700)
    (root / "raw" / "rba_f1.csv").write_bytes(b"changed")
    (root / "raw" / "manifest.json").write_text(json.dumps({"receipt_id": "0" * 64}))
    with pytest.raises(tool.ev.Stop, match="don't match"):
        tool.run(root, e2, tmp_path, "s2", gate=tool.ev.make_gate({}))
