"""E-0003 V1, on invented data only."""

import importlib.util
import sys
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("e0003_extended", REPO / "tools" / "e0003_extended.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["e0003_extended"] = tool
_spec.loader.exec_module(tool)


def test_accrual_is_simple_act_365_between_published_dates_by_hand():
    rates = {date(2008, 1, 1): D("3.65"), date(2008, 1, 11): D("7.30")}
    levels = tool.accrue(rates, until=date(2008, 1, 12))
    assert levels[date(2008, 1, 1)] == 1
    assert levels[date(2008, 1, 11)] == D("1.001")  # 3.65% for 10 days
    assert levels[date(2008, 1, 12)] == D("1.001") * D("1.0002")  # 7.30% for a day


def test_the_tri_continues_the_accrual_at_its_first_level():
    accrued = {date(2010, 12, 31): D(1), date(2011, 1, 4): D("1.01")}
    tri = {date(2011, 1, 4): D(100), date(2011, 1, 31): D(101)}
    joined = tool.joined_levels(accrued, tri)
    assert joined[date(2011, 1, 4)] == D("1.01")
    assert joined[date(2011, 1, 31)] == D("1.0201")
    assert joined[date(2010, 12, 31)] == 1


def test_an_accrual_that_stops_short_refuses():
    with pytest.raises(tool.ev.Stop, match="doesn't reach"):
        tool.joined_levels({date(2010, 12, 31): D(1)}, {date(2011, 1, 4): D(100)})


def daily(start, count):
    return [start + timedelta(days=i) for i in range(count)]


def test_the_seam_check_passes_when_the_index_is_the_accrual():
    days = daily(date(2011, 1, 4), 200)
    rates = dict.fromkeys(days, D("4.75"))
    tri = {d: v * 100 for d, v in tool.accrue(rates).items()}
    months = [date(2011, 1, 31), date(2011, 2, 28), date(2011, 3, 31), date(2011, 4, 29)]
    result = tool.seam_check(months, rates, tri)
    assert result["passes"] is True and result["within_1bp"] == result["months"] == 3


def test_the_seam_check_fails_when_they_diverge():
    days = daily(date(2011, 1, 4), 200)
    rates = dict.fromkeys(days, D("4.75"))
    tri = {d: v * 100 for d, v in tool.accrue(dict.fromkeys(days, D("9.5"))).items()}
    months = [date(2011, 1, 31), date(2011, 2, 28), date(2011, 3, 31)]
    assert tool.seam_check(months, rates, tri)["passes"] is False


def test_the_seam_check_with_no_overlap_is_not_a_pass():
    only = {date(2011, 1, 4): D(4)}
    assert tool.seam_check([date(2008, 1, 31)], only, {date(2011, 1, 4): D(100)})["passes"] is False


def invented():
    rng = np.random.default_rng(6)
    months = [date(2007 + (m + 4) // 12, (m + 4) % 12 + 1, 28) for m in range(233)]
    returns = rng.normal(0.004, [0.04, 0.01, 0.03, 0.002], size=(232, 4))
    return months, returns, rng.normal(0.002, 0.0005, 232), rng.normal(0, 0.03, 232)


def test_2008_is_a_named_window_and_the_report_says_so():
    months, returns, bills, s = invented()
    results = tool.base.evaluate(months, returns, bills, s, tool.WINDOWS)
    assert results["windows"]["2008"]["available"] is True
    text = tool.render(results, {"passes": True, "within_1bp": 180, "months": 189})
    assert text.startswith("# E-0003 V1 (from May 2007): for the owner only")
    assert "**2008 is in this sample:**" in text
    assert "2008 isn't in the sample" not in text
    assert "anything about 2008" not in text
    assert "About six" in text and "About five" not in text
    assert "did from May 2007," in text and "did from 2011," not in text
    assert "before 2016 have no independent check" in text
    assert "Seam check:** passed" in text
    assert "no independent check" in text


def test_a_failed_seam_check_is_stated():
    months, returns, bills, s = invented()
    results = tool.base.evaluate(months, returns, bills, s, tool.WINDOWS)
    assert "**failed**" in tool.render(results, {"passes": False, "within_1bp": 1, "months": 10})


def test_a_changed_extract_stops(tmp_path):
    (tmp_path / "firmmcrid.csv").write_text("date,rate_pct\n2008-01-01,1\n")
    (tmp_path / "extract-manifest.json").write_text('{"sha256": "0"}')
    with pytest.raises(tool.ev.Stop, match="doesn't match"):
        tool.load_history(tmp_path)
