"""E-0002's AUD variant, on invented XML, rates and returns only."""

import importlib.util
import sys
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("e0002_aud", REPO / "tools" / "e0002_aud.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["e0002_aud"] = tool
_spec.loader.exec_module(tool)


def xml(*obs, series="RXI$US_N.B.AL"):
    cells = "".join(obs)
    return (
        '<m xmlns:k="urn:k"><k:Series SERIES_NAME="OTHER">'
        '<k:Obs TIME_PERIOD="2020-01-02" OBS_VALUE="9"/></k:Series>'
        f'<k:Series SERIES_NAME="{series}">{cells}</k:Series></m>'
    ).encode()


def obs(day, value, status=None):
    extra = f' OBS_STATUS="{status}"' if status else ""
    return f'<k:Obs TIME_PERIOD="{day}" OBS_VALUE="{value}"{extra}/>'


def test_only_the_australian_series_is_read_and_exactly():
    rates, absent = tool.parse_h10(xml(obs("2020-01-02", "0.7011")))
    assert rates == {date(2020, 1, 2): D("0.7011")} and absent == 0


@pytest.mark.parametrize("cell", [obs("2020-01-02", "ND"), obs("2020-01-02", "", "ND")])
def test_a_no_data_row_is_counted_and_not_a_rate(cell):
    rates, absent = tool.parse_h10(xml(cell, obs("2020-01-03", "0.7")))
    assert list(rates) == [date(2020, 1, 3)] and absent == 1


@pytest.mark.parametrize(
    "cells, why",
    [
        ((obs("2020-01-02", "abc"),), "non-numeric"),
        ((obs("2020-01-02", "0"),), "impossible"),
        ((obs("2020-01-02", "0.7"), obs("2020-01-02", "0.8")), "conflicting"),
    ],
)
def test_bad_rows_stop(cells, why):
    with pytest.raises(tool.ev.Stop, match=why):
        tool.parse_h10(xml(*cells))


def test_a_missing_series_stops():
    with pytest.raises(tool.ev.Stop, match="no RXI"):
        tool.parse_h10(xml(obs("2020-01-02", "0.7"), series="ELSE"))


def test_the_rate_is_the_latest_on_or_before_and_too_old_stops():
    rates = {date(2020, 1, 2): D("0.7")}
    assert tool.rate_on(rates, sorted(rates), date(2020, 1, 4)) == (D("0.7"), 2)
    with pytest.raises(tool.ev.Stop, match="days old"):
        tool.rate_on(rates, sorted(rates), date(2020, 1, 8))
    with pytest.raises(tool.ev.Stop, match="on or before"):
        tool.rate_on(rates, sorted(rates), date(2020, 1, 1))


def test_a_falling_aud_is_a_gain_for_an_aud_holder_of_usd_by_hand():
    # USD per AUD falls from 0.80 to 0.72: s = 0.80 / 0.72 - 1 = 11.11%, so 10% in USD is 22.22% in AUD.
    months = [date(2020, 1, 31), date(2020, 2, 28)]
    rates = {months[0]: D("0.80"), months[1]: D("0.72")}
    aud, s, facts = tool.translate(months, np.array([[0.10]]), rates)
    assert s[0] == pytest.approx(0.8 / 0.72 - 1)
    assert aud[0, 0] == pytest.approx(1.1 * (0.8 / 0.72) - 1)
    assert facts == {"months": 1, "rates_not_on_the_day": 0, "oldest_rate_days": 0}


def test_attribution_adds_up_by_construction_and_by_hand():
    t = tool.attribution(np.array([0.10]), np.array([0.05]))
    assert t["asset_usd"] == pytest.approx(0.10) and t["currency"] == pytest.approx(0.05)
    assert t["cross"] == pytest.approx(0.005)
    assert t["asset_usd"] + t["currency"] + t["cross"] == pytest.approx(t["total_aud"])


def month_ends(count):
    out, year, month = [], 2006, 1
    for _ in range(count):
        next_first = date(year + month // 12, month % 12 + 1, 1)
        out.append(next_first - timedelta(days=1))
        year, month = next_first.year, next_first.month
    return out


def test_a_full_comparison_runs_and_the_report_says_who_it_is_for():
    months = month_ends(240)
    rng = np.random.default_rng(1)
    usd = rng.normal(0.004, 0.02, size=(239, 3))
    s = rng.normal(0, 0.03, 239)
    aud = (1 + usd) * (1 + s[:, None]) - 1
    results = tool.compare_aud(("cash", "equity", "treasury"), months, usd, aud, s)
    assert results["windows"]["2008"]["available"] is True
    assert set(results["bootstrap_treasury_minus_cash"]) == {"12", "6", "24"}
    assert tool.render(results).startswith("# E-0002 AUD variant: for the owner and HIO's agents")


def test_with_no_currency_move_aud_and_usd_paths_are_equal():
    months = month_ends(240)
    usd = np.random.default_rng(2).normal(0.004, 0.02, size=(239, 3))
    s = np.zeros(239)
    full = tool.compare_aud(("cash", "equity", "treasury"), months, usd, usd, s)["windows"]["full"]
    for d in full["allocations"].values():
        assert d["aud"]["final_wealth"] == pytest.approx(d["usd"]["final_wealth"])
        assert d["attribution"]["currency"] == 0


def test_fx_sources_are_compared_as_counts_only():
    start = date(2020, 1, 1)
    rates = {date(2020, 1, 6): D("0.70"), date(2020, 1, 7): D("0.70")}
    rows = [
        {"date": "2019-12-31", "close": D("9")},
        {"date": "2020-01-04", "close": D("0.70")},
        {"date": "2020-01-06", "close": D("0.70")},
        {"date": "2020-01-07", "close": D("0.80")},
    ]
    out = tool.compare_fx_sources(rows, rates, start)
    assert out["common_dates"] == 2 and out["within_0.01"] == 1 and out["weekend_rows"] == 1
    assert out["within_1pct_on_95pct"] is False
    assert "close" not in out


def _usd(vol, dd, wealth):
    return {"volatility_monthly": vol, "max_drawdown": dd, "final_wealth": wealth}


def _aud(vol, dd, wealth):
    return {"usd": {"volatility": vol, "max_drawdown": dd, "final_wealth": wealth}}


def test_the_reports_reconcile_and_a_difference_is_caught():
    usd = {"windows": {"q1_2020": {"available": True, "allocations": {"a": _usd(0.2, 0.3, 0.9)}}}}
    good = {"windows": {"q1_2020": {"available": True, "allocations": {"a": _aud(0.2, 0.2, 0.9)}}}}
    assert all(tool.reconcile_reports(usd, good)["q1_2020"].values())
    bad = {"windows": {"q1_2020": {"available": True, "allocations": {"a": _aud(0.25, 0.4, 0.8)}}}}
    row = tool.reconcile_reports(usd, bad)["q1_2020"]
    assert row["availability_matches"] is True
    assert not any(v for k, v in row.items() if k != "availability_matches")


def test_an_availability_mismatch_fails_and_is_never_omitted():
    usd = {"windows": {"q1_2020": {"available": True, "allocations": {"a": _usd(0.2, 0.3, 0.9)}}}}
    aud = {"windows": {"q1_2020": {"available": False}}}
    row = tool.reconcile_reports(usd, aud)["q1_2020"]
    assert row["availability_matches"] is False and row["monthly_volatility_equal"] is None


def test_a_window_only_one_report_has_fails():
    usd = {"windows": {}}
    aud = {"windows": {"2008": {"available": True, "allocations": {}}}}
    assert tool.reconcile_reports(usd, aud)["2008"]["availability_matches"] is False


def test_wealth_not_compared_is_none_and_not_a_pass():
    usd = {"windows": {"full": {"available": True, "allocations": {"a": _usd(0.2, 0.3, 0.9)}}}}
    aud = {"windows": {"full": {"available": True, "allocations": {"a": _aud(0.2, 0.2, 1.5)}}}}
    assert tool.reconcile_reports(usd, aud)["full"]["wealth_equal"] is None


def test_no_common_dates_is_not_a_pass():
    assert tool.compare_fx_sources([], {}, date(2020, 1, 1))["within_1pct_on_95pct"] is False
