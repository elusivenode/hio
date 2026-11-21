"""T-0023 step 3's sleeve checks, on invented data only."""

import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal as D
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("t0023_sleeves", REPO / "tools" / "t0023_sleeves.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["t0023_sleeves"] = tool
_spec.loader.exec_module(tool)

CODE = {"commit": "c" * 40, "lock_sha256": "l" * 64}
NOW = datetime(2026, 11, 5, 1, 2, 3, tzinfo=UTC)
M = "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
PLACE = date(2000, 1, 1)


@pytest.fixture(autouse=True)
def fast_and_private(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    monkeypatch.setattr(tool.ev, "REPLICATIONS", 100)  # the bootstrap's size is not what these tests probe


# --- by-hand bars, each at the bar and just outside it


def zeros(n):
    return [D(0)] * n


def last_12(n):
    return [False] * (n - 12) + [True] * 12


def close_rows(n, outside=(), gap=D("1.02"), none=()):
    """Month ends with close 100 and NAV 100, except at `outside` (close 100 x gap) and `none` (no NAV)."""
    rows = []
    for i in range(n):
        close = D(100) * gap if i in outside else D(100)
        rows.append((PLACE, close, None if i in none else D(100)))
    return rows


@pytest.mark.parametrize(
    ("name", "bar", "at", "outside"),
    [
        ("SPY", D("0.01"), D("101"), D("101.01")),
        ("IEF", D("0.01"), D("101"), D("101.01")),
        ("BIL", D("0.0025"), D("100.25"), D("100.251")),
    ],
)
def test_the_c1_close_bar_is_at_the_bar_and_not_beyond_it(name, bar, at, outside):
    assert tool.C1_CLOSE_BAR[name] == bar
    in_2008 = last_12(100)
    for close, status in ((at, "pass"), (outside, "fail")):
        rows = close_rows(100)
        rows[-1] = (PLACE, close, D(100))  # a 2008 month, where every month must be within
        assert tool.check_c1(rows, bar, in_2008)["status"] == status


@pytest.mark.parametrize(
    ("n", "outside", "status"), [(100, 1, "pass"), (100, 2, "fail"), (233, 2, "pass"), (233, 3, "fail")]
)
def test_the_c1_share_is_99_percent_at_the_bar_and_just_outside(n, outside, status):
    result = tool.check_c1(close_rows(n, outside=range(outside)), D("0.01"), last_12(n))
    assert result["counts"]["within"] == n - outside
    assert result["status"] == status  # 99 of 100 and 231 of 233 pass; 98 of 100 and 230 of 233 don't


def test_c1_needs_every_month_of_2008_even_when_the_share_is_high():
    n = 233
    fails = tool.check_c1(close_rows(n, outside={n - 5}), D("0.01"), last_12(n))
    assert fails["counts"]["in_2008_within"] == 11 and fails["status"] == "fail"
    passes = tool.check_c1(close_rows(n, outside={3}), D("0.01"), last_12(n))
    assert passes["counts"]["in_2008_within"] == 12 and passes["status"] == "pass"


def test_c1_counts_a_month_end_without_a_nav_as_outside_the_bar():
    one = tool.check_c1(close_rows(100, none={0}), D("0.01"), last_12(100))
    assert one["counts"]["no_nav"] == 1 and one["status"] == "pass"
    assert tool.check_c1(close_rows(100, none={0, 1}), D("0.01"), last_12(100))["status"] == "fail"
    assert tool.check_c1(close_rows(100, none={99}), D("0.01"), last_12(100))["status"] == "fail"


def test_c1_with_less_than_all_of_2008_is_not_performed():
    with pytest.raises(tool.NotPerformed, match="2008"):
        tool.check_c1(close_rows(100), D("0.01"), [False] * 89 + [True] * 11)


def test_the_integer_share_has_no_rounding_at_the_bar():
    assert tool.share_ok(99, 100, tool.C1_SHARE) and not tool.share_ok(98, 100, tool.C1_SHARE)
    assert tool.share_ok(95, 100, tool.C2_SHARE) and not tool.share_ok(94, 100, tool.C2_SHARE)
    assert tool.share_ok(231, 233, tool.C1_SHARE) and not tool.share_ok(230, 233, tool.C1_SHARE)
    assert not tool.share_ok(0, 0, tool.C1_SHARE)


def signed(n, gaps):
    """Their series: zero except at the given months."""
    out = zeros(n)
    for i, g in gaps.items():
        out[i] = g
    return out


def test_the_c2_share_is_95_percent_at_the_bar_and_just_outside():
    n, bar = 100, tool.C2_MONTH_BAR["SPY"]
    out = D("0.0101")
    # Alternating signs keep the compounded gaps small, so only the monthly share can fail here.
    at_bar = {0: out, 1: -out, 2: out, 3: -out, 4: out, 5: -bar}
    beyond = {0: out, 1: -out, 2: out, 3: -out, 4: out, 5: -out}
    ok = tool.check_c2(zeros(n), signed(n, at_bar), last_12(n), bar)
    assert ok["counts"]["within"] == 95 and ok["status"] == "pass"
    bad = tool.check_c2(zeros(n), signed(n, beyond), last_12(n), bar)
    assert bad["counts"]["within"] == 94 and bad["status"] == "fail"
    assert tool.within_bar(tool.gap_2008(zeros(n), signed(n, beyond), last_12(n)), tool.C2_2008_BAR)
    assert tool.within_bar(tool.gap_annual(zeros(n), signed(n, beyond)), tool.C2_ANNUAL_BAR)


@pytest.mark.parametrize("name", ["SPY", "IEF", "BIL"])
def test_the_c2_monthly_bar_is_each_sleeves_own(name):
    bar = tool.C2_MONTH_BAR[name]
    assert bar == (D("0.0025") if name == "BIL" else D("0.01"))
    n = 240
    at = tool.check_c2(zeros(n), signed(n, {0: bar}), last_12(n), bar)
    beyond = tool.check_c2(zeros(n), signed(n, {0: bar + D("0.00001")}), last_12(n), bar)
    assert at["counts"]["within"] == n and beyond["counts"]["within"] == n - 1


def test_the_c2_2008_compounded_bar_is_one_point():
    n = 240
    mask = [12 <= i < 24 for i in range(n)]
    at = tool.check_c2(zeros(n), signed(n, {12: D("0.0100")}), mask, D("0.01"))
    beyond = tool.check_c2(zeros(n), signed(n, {12: D("0.0101")}), mask, D("0.01"))
    assert at["status"] == "pass" and beyond["status"] == "fail"
    assert tool.gap_2008(zeros(n), signed(n, {12: D("0.0100")}), mask) == D("0.01")


def test_the_c2_annual_bar_is_a_tenth_of_a_point_a_year():
    mask = [True] * 12  # twelve months, so a year is the sample and nothing is annualised away
    at = tool.check_c2(zeros(12), signed(12, {0: D("0.0010")}), mask, D("0.01"))
    beyond = tool.check_c2(zeros(12), signed(12, {0: D("0.0011")}), mask, D("0.01"))
    assert at["status"] == "pass" and beyond["status"] == "fail"
    assert tool.gap_annual(zeros(12), signed(12, {0: D("0.0010")})) == D("0.0010")


def test_c3_annual_bar_is_half_a_point_a_year_and_2008_one_point():
    mask = [True] * 12
    assert tool.check_c3(zeros(12), signed(12, {0: D("0.0050")}), mask)["status"] == "pass"
    assert tool.check_c3(zeros(12), signed(12, {0: D("0.0051")}), mask)["status"] == "fail"
    n = 240
    window = [12 <= i < 24 for i in range(n)]
    assert tool.check_c3(zeros(n), signed(n, {12: D("0.0100")}), window)["status"] == "pass"
    assert tool.check_c3(zeros(n), signed(n, {12: D("0.0101")}), window)["status"] == "fail"


def test_the_c4_correlation_bar_is_0_90():
    assert tool.corr_ok(D("0.90")) and not tool.corr_ok(D("0.8999")) and not tool.corr_ok(None)


def pattern(a, b, reps):
    """Two orthogonal, zero-mean, equal-norm series: corr(x, a x + b z) is a / sqrt(a^2 + b^2) exactly."""
    x, z = [1, -1, 1, -1] * reps, [1, 1, -1, -1] * reps
    return [D(v) / 1000 for v in x], [D(a * p + b * q) / 1000 for p, q in zip(x, z, strict=True)]


def test_c4_correlation_is_taken_in_full_and_over_2008_2009_and_both_must_pass():
    mask, first_year = [True] * 24, [True] * 12 + [False] * 12
    ours, theirs = pattern(12, 5, 6)  # 12/13 = 0.923
    assert tool.correlation(ours, theirs) == D("0.923076923077")
    assert tool.check_c4(ours, theirs, first_year, mask)["status"] == "pass"
    ours, theirs = pattern(15, 8, 6)  # 15/17 = 0.882
    assert tool.check_c4(ours, theirs, first_year, mask)["status"] == "fail"
    # Large agreeing months outside the window carry the full correlation; inside it the series are
    # orthogonal, so the window's own correlation fails the bar and the check with it.
    x, z = pattern(0, 1, 3)
    big, _ = pattern(1, 0, 3)
    outside = [v * 50 for v in big]
    ours, theirs = [*outside, *x], [*outside, *z]
    window = [False] * 12 + [True] * 12
    assert tool.corr_ok(tool.correlation(ours, theirs))
    assert not tool.corr_ok(tool.correlation(x, z))
    assert tool.check_c4(ours, theirs, window, window)["status"] == "fail"


def test_c4_2008_compounded_bar_is_four_points():
    n = 240
    rng = np.random.default_rng(5)
    base = [D(f"{x:.6f}") for x in rng.normal(0, 0.01, n)]
    ours = [D(0) if 12 <= i < 24 else v for i, v in enumerate(base)]
    mask, everything = [12 <= i < 24 for i in range(n)], [True] * n
    for gap, status in ((D("0.0400"), "pass"), (D("0.0401"), "fail")):
        theirs = list(ours)
        theirs[12] = gap
        assert tool.check_c4(ours, theirs, mask, everything)["status"] == status


def test_c4_with_no_variation_is_undefined_and_fails_and_too_few_months_isnt_performed():
    mask = [True] * 12
    result = tool.check_c4(zeros(12), [D("0.001")] * 12, mask, mask)
    assert result["status"] == "fail" and result["values"]["correlation, full"] == "undefined"
    with pytest.raises(tool.NotPerformed):
        tool.correlation(zeros(2), zeros(2))


def test_a_2008_that_isnt_fully_in_the_panel_is_not_performed_for_c2_c3_and_c4():
    short = [False] * 20 + [True] * 11 + [False] * 5
    for check in (
        lambda: tool.check_c2(zeros(36), zeros(36), short, D("0.01")),
        lambda: tool.check_c3(zeros(36), zeros(36), short),
        lambda: tool.check_c4(zeros(36), zeros(36), short, [True] * 36),
    ):
        with pytest.raises(tool.NotPerformed, match="2008"):
            check()


# --- C5: an audited fiscal year, each of the three comparisons at and beyond its bar


def fund(dists=None, periods=None, days=None):
    return tool.Fund("SPY", dists or {}, {}, periods or [], days or [], {})


def vp(a, b, r):
    return tool.VehiclePeriod(a, b, D(r), D(0), D(r))


FY = (date(2007, 10, 1), date(2008, 9, 30))
DAYS = [date(2007, 9, 28), date(2008, 3, 31), date(2008, 9, 30)]
PERIODS = [vp(DAYS[0], DAYS[1], "0.05"), vp(DAYS[1], DAYS[2], "0.04")]  # 1.05 x 1.04 = 9.2%


def fact(**kw):
    values = {
        "symbol": "SPY",
        "start": FY[0],
        "end": FY[1],
        "distributions": D("1.50"),
        "total_return_pct": D("9.20"),
        "nav_start": D("100.00"),
        "nav_end": D("110.00"),
        "filing": "N-CSR",
        "section": "Financial Highlights",
    }
    return tool.Fact(**(values | kw))


def parts(f, nav="default"):
    held = fund({date(2008, 1, 2): D("0.75"), date(2008, 7, 1): D("0.75")}, PERIODS, DAYS)
    nav = {DAYS[0]: D("100.00"), DAYS[2]: D("110.00")} if nav == "default" else nav
    return tool.check_c5_fact(f, held, nav)


def test_c5_distributions_per_share_within_one_cent():
    assert parts(fact())["distributions"]["status"] == "pass"
    assert parts(fact(distributions=D("1.49")))["distributions"]["status"] == "pass"
    assert parts(fact(distributions=D("1.51")))["distributions"]["status"] == "pass"
    assert parts(fact(distributions=D("1.4899")))["distributions"]["status"] == "fail"
    assert parts(fact(distributions=D("1.5101")))["distributions"]["status"] == "fail"


def test_c5_counts_only_distributions_inside_the_fiscal_year():
    held = fund(
        {date(2007, 9, 30): D("9"), date(2008, 1, 2): D("1.50"), date(2008, 10, 1): D("9")}, PERIODS, DAYS
    )
    assert tool.check_c5_fact(fact(), held, None)["distributions"]["status"] == "pass"


def test_c5_total_return_within_a_quarter_point_of_hios():
    assert parts(fact(total_return_pct=D("9.20")))["total_return"]["status"] == "pass"
    assert parts(fact(total_return_pct=D("9.45")))["total_return"]["status"] == "pass"
    assert parts(fact(total_return_pct=D("8.95")))["total_return"]["status"] == "pass"
    assert parts(fact(total_return_pct=D("9.4501")))["total_return"]["status"] == "fail"
    assert parts(fact(total_return_pct=D("8.9499")))["total_return"]["status"] == "fail"


def test_c5_nav_within_a_cent_at_each_end():
    assert parts(fact(nav_start=D("100.01"), nav_end=D("109.99")))["nav"]["status"] == "pass"
    assert parts(fact(nav_start=D("100.0101")))["nav"]["status"] == "fail"
    assert parts(fact(nav_end=D("110.0101")))["nav"]["status"] == "fail"


def test_c5_what_cant_be_checked_is_not_performed_and_never_passes():
    assert parts(fact(distributions=None))["distributions"]["status"].startswith("not performed")
    assert parts(fact(total_return_pct=None))["total_return"]["status"].startswith("not performed")
    assert parts(fact(nav_end=None))["nav"]["status"].startswith("not performed")
    assert parts(fact(), nav=None)["nav"]["status"].startswith("not performed")
    far = {date(2007, 1, 2): D("100"), date(2008, 9, 30): D("110")}
    assert parts(fact(), nav=far)["nav"]["status"].startswith("not performed")
    gappy = tool.check_c5_fact(fact(), fund({}, PERIODS, [date(2008, 3, 31), date(2008, 9, 30)]), None)
    assert gappy["total_return"]["status"].startswith("not performed")


def test_c5_combines_a_failure_over_an_unperformed_part_over_a_pass():
    assert tool.combine(["pass", "pass"]) == "pass"
    assert tool.combine(["pass", "not performed: x"]) == "not performed: x"
    assert tool.combine(["fail", "not performed: x", "pass"]) == "fail"


def test_c5_takes_the_fiscal_years_that_cover_2008_for_the_named_fund_only():
    assert tool.covers_2008(fact(start=date(2007, 1, 1), end=date(2008, 1, 1)))
    assert tool.covers_2008(fact(start=date(2008, 12, 31), end=date(2009, 12, 30)))
    assert not tool.covers_2008(fact(start=date(2007, 1, 1), end=date(2007, 12, 31)))
    assert not tool.covers_2008(fact(start=date(2009, 1, 1), end=date(2009, 12, 31)))
    held = fund({date(2008, 1, 2): D("1.50")}, PERIODS, DAYS)
    other = fact(symbol="BIL")
    with pytest.raises(tool.NotPerformed, match="no audited fiscal year"):
        tool.check_c5([other], held, None)
    result = tool.check_c5([other, fact()], held, {DAYS[0]: D("100"), DAYS[2]: D("110")})
    assert result["status"] == "pass" and result["counts"]["fiscal_years"] == 1
    assert result["counts"]["sub_checks"] == result["counts"]["sub_checks_passed"] == 3


# --- NAV returns and their split basis


DAY0 = date(2008, 1, 7)


def near(a, b):
    """Equal to the precision the tool computes at, which is more than a hand sum in the default context."""
    return abs(a - b) < D("1e-25")


def days_of(n):
    return [DAY0 + timedelta(days=i) for i in range(n)]


def navs(values, skip=()):
    return {
        d: D(v) for i, (d, v) in enumerate(zip(days_of(len(values)), values, strict=True)) if i not in skip
    }


def test_a_nav_that_jumps_with_a_split_has_its_factor_applied_as_vehicle_series_does():
    nav = navs(["100", "101", "102", "51.5", "52", "52.5"])
    periods, counts = tool.nav_periods(nav, {days_of(2)[1]: D("1.00")}, {days_of(4)[3]: D(2)})
    assert counts["splits_nav_unadjusted"] == 1 and "splits_nav_already_adjusted" not in counts
    assert near(periods[2].total_return, D(2) * D("51.5") / D(102) - 1)
    assert near(periods[0].income_return, D("0.01"))  # 1.00 on a NAV of 100


def test_a_nav_history_already_adjusted_for_a_split_takes_no_factor_and_puts_distributions_in_new_units():
    nav = navs(["50", "50.5", "51", "51.5", "52", "52.5"])
    periods, counts = tool.nav_periods(nav, {days_of(2)[1]: D("1.00")}, {days_of(4)[3]: D(2)})
    assert counts["splits_nav_already_adjusted"] == 1 and "splits_nav_unadjusted" not in counts
    assert near(periods[2].total_return, D("51.5") / D(51) - 1)
    assert near(periods[0].income_return, D("0.01"))  # 1.00 per old share is 0.50 per new, on a NAV of 50


def test_a_nav_jump_that_fits_neither_basis_stops():
    nav = navs(["100", "101", "102", "163.2", "164", "165"])
    with pytest.raises(tool.ev.Stop, match="neither basis"):
        tool.nav_periods(nav, {}, {days_of(4)[3]: D(2)})


def test_a_split_of_one_is_not_a_split_and_a_reverse_split_is_read_the_same_way():
    nav = navs(["100", "101", "102", "103"])
    assert tool.nav_periods(nav, {}, {days_of(4)[3]: D(1)})[1].get("splits_nav_unadjusted") is None
    reverse = navs(["10", "10.1", "10.2", "102", "103"])
    periods, counts = tool.nav_periods(reverse, {}, {days_of(5)[3]: D("0.1")})
    assert counts["splits_nav_unadjusted"] == 1
    assert near(periods[2].total_return, D("0.1") * D(102) / D("10.2") - 1)


def test_actions_land_on_the_first_nav_day_on_or_after_their_ex_date_and_are_counted():
    nav = navs(["100", "101", "102", "103", "104"], skip={2})  # no NAV on the third day
    before = DAY0 - timedelta(days=3)
    after = DAY0 + timedelta(days=9)
    dists = {days_of(3)[2]: D("1"), DAY0: D("5"), before: D("5"), after: D("5")}
    periods, counts = tool.nav_periods(nav, dists, {})
    assert counts["actions_moved_to_next_nav_day"] == 1
    assert counts["actions_before_the_first_period"] == 2  # the first day and before: no period to pay into
    assert counts["actions_after_last_nav_day"] == 1
    assert counts["distributions_applied"] == 1
    assert [p.end for p in periods] == [DAY0 + timedelta(days=n) for n in (1, 3, 4)]
    assert [p.income_return == 0 for p in periods] == [True, False, True]
    assert near(periods[1].income_return, D(1) / D(101))  # paid on the third NAV day, into 101


def test_a_nav_series_needs_two_days():
    with pytest.raises(tool.ev.Stop):
        tool.nav_periods({DAY0: D(100)}, {}, {})


def test_compounding_nav_periods_between_month_ends_and_a_gap_isnt_performed():
    d = days_of(5)
    periods = [(d[0], d[2], D("0.01")), (d[2], d[4], D("0.02"))]
    out = tool.compound_months(periods, [d[0], d[2], d[4]])
    assert list(out) == pytest.approx([0.01, 0.02])
    with pytest.raises(tool.NotPerformed, match=r"coverage|gap|period"):
        tool.compound_months(periods, [d[0], d[1], d[4]])
    with pytest.raises(tool.NotPerformed):
        tool.compound_months(periods[:1], [d[0], d[4]])


def test_the_one_month_accrual_is_simple_act_365_and_stale_data_isnt_performed():
    rates = {DAY0 + timedelta(days=i): D("3.65") for i in range(11)}  # 3.65% a year is 0.01% a day
    out = tool.par_months(rates, [DAY0, DAY0 + timedelta(days=10)])
    assert out[0] == pytest.approx(1.0001**10 - 1)
    with pytest.raises(tool.NotPerformed):
        tool.par_months(rates, [DAY0, DAY0 + timedelta(days=17)])
    with pytest.raises(tool.NotPerformed, match="no 1-month"):
        tool.par_months({}, [DAY0, DAY0 + timedelta(days=10)])


# --- reading the references


def feed(rows):
    cells = []
    for row in rows:
        body = ""
        for key, value in row.items():
            if value is None:
                body += f'<d:{key} m:null="true" />'
            else:
                body += f"<d:{key}>{value}</d:{key}>"
        cells.append(f"<entry><content><m:properties>{body}</m:properties></content></entry>")
    return (f'<feed xmlns:m="{M}" xmlns:d="urn:d">' + "".join(cells) + "</feed>").encode()


def test_par_rows_read_as_e0001_reads_them_and_absent_cells_are_absent():
    body = feed(
        [
            {"NEW_DATE": "2008-01-02T00:00:00", "BC_1MONTH": "3.10", "BC_10YEAR": "4.00"},
            {"NEW_DATE": "2008-01-03T00:00:00", "BC_1MONTH": None, "BC_10YEAR": "N/A"},
            {"NEW_DATE": "2008-01-04T00:00:00", "BC_1MONTH": "", "BC_10YEAR": "4.10"},
        ]
    )
    out = tool.parse_par(body)
    assert out["BC_1MONTH"] == {date(2008, 1, 2): D("3.10")}
    assert out["BC_10YEAR"] == {date(2008, 1, 2): D("4.00"), date(2008, 1, 4): D("4.10")}


@pytest.mark.parametrize(
    "rows",
    [
        [{"BC_1MONTH": "3.1"}],
        [{"NEW_DATE": "2008-01-02", "BC_1MONTH": "abc"}],
        [{"NEW_DATE": "2008-01-02", "BC_1MONTH": "26"}],
        [{"NEW_DATE": "2008-01-02", "BC_1MONTH": "-6"}],
        [{"NEW_DATE": "2008-01-02", "BC_1MONTH": "3.1"}, {"NEW_DATE": "2008-01-02", "BC_1MONTH": "3.2"}],
    ],
)
def test_bad_par_rows_stop(rows):
    with pytest.raises(tool.ev.Stop):
        tool.parse_par(feed(rows))


def test_an_identical_duplicate_par_row_is_one_row():
    row = {"NEW_DATE": "2008-01-02", "BC_1MONTH": "3.1"}
    assert tool.parse_par(feed([row, row]))["BC_1MONTH"] == {date(2008, 1, 2): D("3.1")}


def test_a_nav_file_is_read_or_absent_and_a_bad_one_stops(tmp_path):
    assert tool.load_nav(tmp_path / "nav-ief.csv") is None
    good = tmp_path / "nav-spy.csv"
    good.write_text("date,nav\n2008-01-02,100.5\n2008-01-03,101\n")
    assert tool.load_nav(good) == {date(2008, 1, 2): D("100.5"), date(2008, 1, 3): D(101)}
    for name, text in {
        "header": "day,nav\n2008-01-02,1\n",
        "repeat": "date,nav\n2008-01-02,1\n2008-01-02,2\n",
        "zero": "date,nav\n2008-01-02,0\n",
        "text": "date,nav\n2008-01-02,abc\n",
        "empty": "date,nav\n",
        "date": "date,nav\n02-Jan-2008,1\n",
    }.items():
        bad = tmp_path / f"bad-{name}.csv"
        bad.write_text(text)
        with pytest.raises(tool.ev.Stop):
            tool.load_nav(bad)


FACT_HEADER = ",".join(tool.FACT_COLUMNS)


def test_audited_facts_are_read_or_absent_and_blank_figures_are_unrecorded(tmp_path):
    assert tool.load_facts(tmp_path / "audited-facts.csv") is None
    path = tmp_path / "audited-facts.csv"
    path.write_text(f"{FACT_HEADER}\nSPY,2007-10-01,2008-09-30,1.5,,100.1,,N-CSR,Highlights\n")
    (only,) = tool.load_facts(path)
    assert only.distributions == D("1.5") and only.total_return_pct is None and only.nav_end is None
    assert only.filing == "N-CSR" and only.section == "Highlights"


@pytest.mark.parametrize(
    "text",
    [
        "symbol,fiscal_start\nSPY,2007-10-01\n",
        f"{FACT_HEADER}\nVTI,2007-10-01,2008-09-30,1,1,1,1,f,s\n",
        f"{FACT_HEADER}\nSPY,2008-09-30,2007-10-01,1,1,1,1,f,s\n",
        f"{FACT_HEADER}\nSPY,2007-10-01,2008-09-30,1,1,1,1,f,s\nSPY,2007-10-01,2008-09-30,1,1,1,1,f,s\n",
        f"{FACT_HEADER}\nSPY,2007-10-01,2008-09-30,x,1,1,1,f,s\n",
        f"{FACT_HEADER}\nSPY,October,2008-09-30,1,1,1,1,f,s\n",
    ],
)
def test_bad_audited_facts_stop(tmp_path, text):
    path = tmp_path / "audited-facts.csv"
    path.write_text(text)
    with pytest.raises(tool.ev.Stop):
        tool.load_facts(path)


# --- sensitivities: the bar is no change of class


def test_a_sensitivity_passes_with_no_class_change_and_fails_naming_each_change(monkeypatch):
    frozen = {"total": {"volatility": {"class": "mixed"}, "max_drawdown": {"class": "distinguished"}}}
    same = {"total": {"volatility": {"class": "mixed"}, "max_drawdown": {"class": "distinguished"}}}
    moved = {"total": {"volatility": {"class": "mixed"}, "max_drawdown": {"class": "not_distinguished"}}}
    seen = []
    monkeypatch.setattr(
        tool.common, "with_changes", lambda _panel, *, usd: seen.append(dict(usd)) or "changed"
    )
    monkeypatch.setattr(tool.common, "classes_of", lambda _panel: same)
    assert tool.sensitivity("panel", frozen, {"equity": "arr"}) == {"status": "pass", "changes": []}
    monkeypatch.setattr(tool.common, "classes_of", lambda _panel: moved)
    out = tool.sensitivity("panel", frozen, {"equity": "arr"})
    assert out == {"status": "fail", "changes": ["total.max_drawdown: distinguished -> not_distinguished"]}
    assert seen == [{"equity": "arr"}, {"equity": "arr"}]


def test_each_sensitivity_replaces_the_sleeves_the_preregistration_names(monkeypatch):
    assert {k: v[1] for k, v in tool.SENSITIVITIES.items()} == {
        "S1": {"equity": "nav_SPY"},
        "S2": {"bills": "nav_BIL"},
        "S3": {"bills": "par_BIL"},
        "S4": {"treasury": "v1_IEF"},
        "S5": {"equity": "nav_SPY", "bills": "nav_BIL"},
    }
    calls = []
    monkeypatch.setattr(tool.common, "classes_of", lambda _panel: {})
    monkeypatch.setattr(
        tool,
        "sensitivity",
        lambda _panel, _frozen, changes: calls.append(sorted(changes)) or {"status": "pass", "changes": []},
    )
    sources = {
        "nav_SPY": tool.Source(np.zeros(2)),
        "nav_BIL": tool.Source(None, "no nav-bil.csv"),
        "par_BIL": tool.Source(np.zeros(2)),
        "v1_IEF": tool.Source(np.zeros(2)),
    }
    out = tool.run_sensitivities("panel", sources)
    assert [k for k, v in out.items() if v["status"] == "pass"] == ["S1", "S3", "S4"]
    assert out["S2"]["status"] == out["S5"]["status"] == "not performed: no nav-bil.csv"
    assert calls == [["equity"], ["bills"], ["treasury"]]


# --- the run, over an invented workspace


def trading_days(start, count):
    out, day = [], start
    while len(out) < count:
        if day.weekday() < 5:
            out.append(day)
        day += timedelta(days=1)
    return out


def walk(seed, n, drift, vol, start):
    steps = 1 + drift + vol * np.random.default_rng(seed).standard_normal(n)
    return [round(float(x), 4) for x in start * np.cumprod(steps)]


def bill_closes(days):
    closes = [90.0]
    for i in range(1, len(days)):
        rate = 4.0 + 0.05 * ((i - 1) % 7)
        closes.append(round(closes[-1] * (1 + rate * (days[i] - days[i - 1]).days / 36500), 4))
    return closes


DIVIDEND_DAYS = [
    date(2007, 6, 15),
    date(2007, 12, 14),
    date(2008, 6, 13),
    date(2008, 12, 12),
    date(2009, 6, 12),
]
DIVIDENDS = {"SPY": 0.3, "IEF": 0.2, "BIL": 0.01}
OFFSET = {"SPY": D("1.0004"), "IEF": D("1.0003"), "BIL": D("1.0002")}


def dividend_rows(name):
    return [
        {
            "date": d.isoformat(),
            "value": DIVIDENDS[name],
            "unadjustedValue": DIVIDENDS[name],
            "currency": "USD",
            "declarationDate": d.isoformat(),
            "recordDate": d.isoformat(),
            "paymentDate": d.isoformat(),
        }
        for d in DIVIDEND_DAYS
    ]


def month_ends(days):
    last = {}
    for d in days:
        last[(d.year, d.month)] = d
    return sorted(last.values())[:-1]  # the last month may be partial


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def private_dir(path):
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.chmod(0o700)
    return path


@dataclass
class Workspace:
    root: Path
    e0002: Path
    e0001: Path
    gate: object
    days: list
    months: list
    closes: dict


def build_workspace(base: Path) -> Workspace:
    gate = tool.ev.make_gate({})
    days = trading_days(date(2007, 4, 2), 1100)
    closes = {
        "SPY": walk(1, len(days), 0.0003, 0.01, 100.0),
        "IEF": walk(2, len(days), 0.0001, 0.003, 100.0),
        "BIL": bill_closes(days),
    }
    eod = {
        name: [
            {"date": d.isoformat(), "close": c, "adjusted_close": c}
            for d, c in zip(days, values, strict=True)
        ]
        for name, values in closes.items()
    }

    def get(request):
        path = request.split("?")[0].split("/")
        name = path[2].split(".")[0] if len(path) > 2 else ""
        if path[1] == "eod":
            rows = eod.get(name) or [
                {"date": d.isoformat(), "close": 50.0 + i % 5, "adjusted_close": 50.0 + i % 5}
                for i, d in enumerate(days)
            ]
            return 200, json.dumps(rows).encode()
        if path[1] == "div":
            return 200, json.dumps(
                dividend_rows(name) if name in DIVIDENDS and path[2].endswith("US") else []
            ).encode()
        if path[1] == "exchange-symbol-list":
            wanted = [s.rsplit(".", 1)[0] for s in tool.ev.ETFS if s.endswith(f".{path[2]}")]
            currency = "USD" if path[2] == "US" else "AUD"
            return 200, json.dumps([{"Code": c, "Currency": currency} for c in wanted]).encode()
        return 200, b"[]"

    e0002 = private_dir(base / "e0002")
    tool.ev.fetch(e0002, "s2", gate=gate, commit="d" * 40, get=get, pause=0)
    manifest = tool.ev.load_snapshot(e0002, "s2")
    funds = tool.load_funds(e0002, manifest)
    months = month_ends(days)

    root = private_dir(base / "root")
    reference = private_dir(root / "reference")
    for name, rate_offset in OFFSET.items():
        text = "date,nav\n" + "".join(
            f"{d},{D(c) / rate_offset:.6f}\n" for d, c in zip(days, closes[name], strict=True)
        )
        (reference / f"nav-{name.lower()}.csv").write_text(text)

    monthly = {
        name: tool.common.compound_between(
            [(p.start, p.end, float(p.total_return)) for p in f.periods], months
        )
        for name, f in funds.items()
    }
    lines = ["period_start,period_end,equity,bills,treasury,cash,usd_bills,fx_return"]
    for i in range(len(months) - 1):
        cells = [
            monthly["SPY"][i],
            monthly["BIL"][i],
            monthly["IEF"][i],
            0.002 + 0.0001 * (i % 3),
            monthly["BIL"][i],
            0.0,
        ]
        lines.append(f"{months[i]},{months[i + 1]}," + ",".join(f"{c:.12f}" for c in cells))
    text = ("\n".join(lines) + "\n").encode()
    run = private_dir(root / "runs" / "20261104T000000Z-aaaaaaaa")
    (run / "panel.csv").write_bytes(text)
    record = {"panel_id": tool.panel_tool.FROZEN_PANEL_ID, "panel_sha256": sha(text)}
    (run / "run.json").write_text(json.dumps(record))

    facts = [",".join(tool.FACT_COLUMNS)]
    nav = {n: tool.load_nav(reference / f"nav-{n.lower()}.csv") for n in funds}
    for name, f in funds.items():
        for start, end in ((date(2007, 7, 1), date(2008, 6, 30)), (date(2008, 7, 1), date(2009, 6, 30))):
            first = tool.anchor(f.days, start, before=True)
            last = tool.anchor(f.days, end, before=False)
            paid = sum((a for d, a in f.dists.items() if start <= d <= end), D(0))
            hio = tool.period_return(f.periods, first, last) * 100
            nav_days = sorted(nav[name])
            n0, n1 = (
                nav[name][tool.anchor(nav_days, start, before=True)],
                nav[name][tool.anchor(nav_days, end, before=False)],
            )
            facts.append(
                f"{name},{start},{end},{paid},{hio:.2f},{n0:.2f},{n1:.2f},N-CSR,Financial Highlights"
            )
    (reference / "audited-facts.csv").write_text("\n".join(facts) + "\n")

    e0001 = private_dir(base / "e0001")
    raw = private_dir(e0001 / "raw")
    entries = []
    for year in sorted({d.year for d in days}):
        # the rate pattern runs over the whole list's index, as bill_closes uses it
        rows = [
            {"NEW_DATE": f"{d}T00:00:00", "BC_1MONTH": f"{4.0 + 0.05 * (i % 7):.2f}", "BC_10YEAR": "4.50"}
            for i, d in enumerate(days)
            if d.year == year
        ]
        body = feed(rows)
        (raw / f"{year}.xml").write_bytes(body)
        entries.append({"path": f"raw/{year}.xml", "sha256": sha(body)})
    manifest_v = {"stopped": None, "source_id": tool.e1.SOURCE_ID, "files": entries}
    (e0001 / "manifest.json").write_text(json.dumps(manifest_v))
    release = "ab" * 32
    store = private_dir(e0001 / "store-variant" / "releases" / tool.e1.DATASET_ID / release)
    ief = funds["IEF"].periods
    data = "period_start,period_end,r,flat_r,cubic_r,coupon_pct,long_gap\n" + "".join(
        f"{p.start},{p.end},{p.total_return + D('0.00005') * (i % 3 - 1)},0,0,4.5,false\n"
        for i, p in enumerate(ief)
    )
    (store / "data.csv").write_text(data)
    (store / "manifest.json").write_text(
        json.dumps({"files": [{"path": "data.csv", "sha256": sha(data.encode())}]})
    )
    (e0001 / "variant-summary.json").write_text(json.dumps({"release": release}))
    return Workspace(root, e0002, e0001, gate, days, months, closes)


def fresh(tmp_path):
    return build_workspace(tmp_path)


def run_all(ws):
    return tool.run(ws.root, ws.e0002, ws.e0001, gate=ws.gate, code=CODE, now=NOW)


def test_a_full_run_over_consistent_invented_data_passes_every_check(tmp_path):
    summary = run_all(fresh(tmp_path))
    status = {c: {s: r["status"] for s, r in rows.items()} for c, rows in summary["checks"].items()}
    assert status["C1"] == status["C2"] == status["C5"] == {"SPY": "pass", "BIL": "pass", "IEF": "pass"}
    assert status["C3"] == {"BIL": "pass"} and status["C4"] == {"IEF": "pass"}
    assert set(summary["sensitivities"]) == {"S1", "S2", "S3", "S4", "S5"}
    assert all(v["status"] in {"pass", "fail"} for v in summary["sensitivities"].values())
    assert summary["checks"]["C1"]["SPY"]["counts"]["in_2008_within"] == 12


def test_outputs_are_a_new_private_directory_with_values_only_in_the_report(tmp_path):
    ws = fresh(tmp_path)
    summary = run_all(ws)
    out = ws.root / "corroboration" / "step3" / summary["output"]
    assert summary["output"] == "20261105T010203Z-cccccccc"
    assert sorted(p.name for p in out.iterdir()) == ["report.md", "summary.json"]
    assert out.stat().st_mode & 0o077 == 0
    assert all(p.stat().st_mode & 0o077 == 0 for p in out.iterdir())
    report = (out / "report.md").read_text()
    for heading in ("## C1:", "## C2:", "## C3:", "## C4:", "## C5:", "## Sensitivities"):
        assert heading in report
    assert tool.panel_tool.FROZEN_PANEL_ID in report and "worst gap" in report
    on_disk = json.loads((out / "summary.json").read_text())
    assert on_disk == json.loads(json.dumps(summary))
    assert "values" not in json.dumps(on_disk) and "worst gap" not in json.dumps(on_disk)
    assert sha((out / "report.md").read_bytes()) == on_disk["report_sha256"]
    with pytest.raises(FileExistsError):
        run_all(ws)  # a second run in the same second would overwrite: it refuses


@pytest.mark.parametrize(
    ("gone", "unperformed", "performed"),
    [
        ("nav-ief.csv", {("C1", "IEF"), ("C2", "IEF"), ("C5", "IEF")}, {"S1", "S2", "S3", "S4", "S5"}),
        ("nav-spy.csv", {("C1", "SPY"), ("C2", "SPY"), ("C5", "SPY")}, {"S2", "S3", "S4"}),
        ("nav-bil.csv", {("C1", "BIL"), ("C2", "BIL"), ("C5", "BIL")}, {"S1", "S3", "S4"}),
    ],
)
def test_a_missing_nav_file_makes_only_what_needs_it_not_performed(tmp_path, gone, unperformed, performed):
    ws = fresh(tmp_path)
    (ws.root / "reference" / gone).unlink()
    summary = run_all(ws)
    for check, rows in summary["checks"].items():
        for sleeve, result in rows.items():
            assert result["status"].startswith("not performed") == ((check, sleeve) in unperformed)
    got = {k for k, v in summary["sensitivities"].items() if not v["status"].startswith("not performed")}
    assert got == performed


def test_a_missing_audited_facts_file_makes_c5_not_performed_and_nothing_else(tmp_path):
    ws = fresh(tmp_path)
    (ws.root / "reference" / "audited-facts.csv").unlink()
    summary = run_all(ws)
    assert {r["status"] for r in summary["checks"]["C5"].values()} == {"not performed: no audited-facts.csv"}
    assert summary["checks"]["C1"]["SPY"]["status"] == "pass"
    assert summary["inputs"]["audited_facts_sha256"] is None


def test_a_failed_bar_is_a_result_and_the_run_completes(tmp_path):
    ws = fresh(tmp_path)
    path = ws.root / "reference" / "nav-spy.csv"
    lines = path.read_text().splitlines()
    path.write_text(
        "\n".join([lines[0], *(f"{r.split(',')[0]},{D(r.split(',')[1]) / D('1.02'):.6f}" for r in lines[1:])])
        + "\n"
    )
    summary = run_all(ws)
    assert summary["checks"]["C1"]["SPY"]["status"] == "fail"  # close is 2% above NAV at every month end
    assert summary["checks"]["C1"]["BIL"]["status"] == "pass"


def test_s5_needs_only_spy_and_bil(tmp_path):
    ws = fresh(tmp_path)
    (ws.root / "reference" / "nav-ief.csv").unlink()
    assert not run_all(ws)["sensitivities"]["S5"]["status"].startswith("not performed")


def test_a_changed_retained_par_file_stops_before_anything_is_written(tmp_path):
    ws = fresh(tmp_path)
    (ws.e0001 / "raw" / "2008.xml").write_bytes(b"<feed/>")
    with pytest.raises(tool.ev.Stop, match="retained bytes"):
        run_all(ws)
    assert not (ws.root / "corroboration").exists()


def test_a_v1_data_file_that_doesnt_match_its_release_manifest_stops(tmp_path):
    ws = fresh(tmp_path)
    path = ws.e0001 / "store-variant" / "releases" / tool.e1.DATASET_ID / ("ab" * 32) / "data.csv"
    path.write_text(path.read_text() + "2099-01-01,2099-01-02,0.1,0,0,4.5,false\n")
    with pytest.raises(tool.ev.Stop, match="V1"):
        run_all(ws)


def test_no_rebuild_with_the_frozen_id_stops(tmp_path):
    ws = fresh(tmp_path)
    (ws.root / "runs" / "20261104T000000Z-aaaaaaaa" / "run.json").write_text(
        json.dumps({"panel_id": "x" * 64, "panel_sha256": "y"})
    )
    with pytest.raises(tool.ev.Stop, match="frozen panel id"):
        run_all(ws)


# --- main


def main_with(ws, monkeypatch, capsys):
    monkeypatch.setattr(tool.ev, "make_gate", lambda: ws.gate)
    monkeypatch.setattr(tool.ev, "code_commit", lambda: CODE)
    argv = ["--root", str(ws.root), "--e0002", str(ws.e0002), "--e0001", str(ws.e0001)]
    code = tool.main(argv)
    return code, capsys.readouterr()


def test_main_prints_statuses_and_counts_but_no_value_and_exits_0(tmp_path, monkeypatch, capsys):
    ws = fresh(tmp_path)
    code, seen = main_with(ws, monkeypatch, capsys)
    assert code == 0 and seen.err == ""
    printed = json.loads(seen.out)
    assert printed["checks"]["C1"] == {"SPY": "pass", "BIL": "pass", "IEF": "pass"}
    assert set(printed) == {"panel_id", "checks", "sensitivities", "class_changes", "report_sha256", "output"}
    assert "worst gap" not in seen.out
    for close in (ws.closes["SPY"][100], ws.closes["IEF"][100]):
        assert str(close) not in seen.out


def test_main_exits_0_when_a_bar_fails(tmp_path, monkeypatch, capsys):
    ws = fresh(tmp_path)
    (ws.root / "reference" / "nav-ief.csv").write_text("date,nav\n" + "".join(f"{d},1.0\n" for d in ws.days))
    code, seen = main_with(ws, monkeypatch, capsys)
    assert code == 0
    assert json.loads(seen.out)["checks"]["C1"]["IEF"] == "fail"


def test_main_exits_2_on_a_stop_and_says_why_without_a_value(tmp_path, monkeypatch, capsys):
    ws = fresh(tmp_path)
    ws.root.chmod(0o755)
    code, seen = main_with(ws, monkeypatch, capsys)
    assert code == 2 and seen.out == ""
    assert "mode 700" in seen.err


def test_main_hides_the_message_of_any_other_error(tmp_path, monkeypatch, capsys):
    ws = fresh(tmp_path)
    monkeypatch.setattr(tool, "load_nav", lambda _path: (_ for _ in ()).throw(KeyError("secret 123.45")))
    code, seen = main_with(ws, monkeypatch, capsys)
    assert code == 2 and "KeyError" in seen.err and "secret" not in seen.err


def test_the_nav_return_uses_eodhds_distributions_on_the_nav_so_income_isnt_tested(tmp_path):
    ws = fresh(tmp_path)
    funds = tool.load_funds(ws.e0002, tool.ev.load_snapshot(ws.e0002, "s2"))
    nav = tool.load_nav(ws.root / "reference" / "nav-spy.csv")
    periods, counts = tool.nav_periods(nav, funds["SPY"].dists, funds["SPY"].splits)
    assert counts["distributions_applied"] == len(DIVIDEND_DAYS)
    paying = [p for p in periods if p.income_return != 0]
    assert [p.end for p in paying] == DIVIDEND_DAYS
    assert all(near(p.income_return, D("0.3") / nav[p.start]) for p in paying)
