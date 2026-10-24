"""Cash and FX constructions against every RA §3.2 and FX fixture: numbers AND information
availability (S1-A7, S1-A8; OD-0020 item 2)."""

from datetime import date
from decimal import Decimal, localcontext

import pytest

from hio.contracts.temporal import KnowableBasis
from hio.library.cash import ACT_360, ACT_365F, MissingRate, RateFixing, chain_index, overnight_period
from hio.library.fx import FxQuote, compound, fx_period, joint_calendar, spot_return
from hio.library.fx_forward import (
    cip_forward,
    forward_excess_per_capital,
    forward_return_per_notional,
    funded_cash_excess,
    notional_to_capital,
)
from hio.library.numeric import CTX
from tests.helpers import CALENDARS, utc

NY, SYD = CALENDARS["synthetic.xnys"], CALENDARS["synthetic.xsyd"]
COS = KnowableBasis.CAPTURED_ON_SCHEDULE
D = Decimal


@pytest.fixture(autouse=True)
def _library_precision():
    """Test-side arithmetic uses the library's 50-digit context, so comparisons are like for like."""
    with localcontext(CTX):
        yield


def q12(x: Decimal) -> Decimal:
    return x.quantize(D("1e-12"))


def sofr(d: date, rate: str, published=None) -> tuple[date, RateFixing]:
    """SOFR for d is published the next NY business day, about 08:00 ET (13:00Z in January)."""
    pub = published or NY.add_business_days(d, 1)
    return d, RateFixing(d, D(rate), utc(pub.year, pub.month, pub.day, 13), COS)


def rba(d: date, rate: str) -> tuple[date, RateFixing]:
    """The RBA cash rate for d is published before 09:20 Sydney on the next business day."""
    pub = SYD.add_business_days(d, 1)
    return d, RateFixing(d, D(rate), utc(pub.year, pub.month, pub.day - 1, 22, 20), COS)


FRI, SAT, MON, TUE = date(2026, 1, 9), date(2026, 1, 10), date(2026, 1, 12), date(2026, 1, 13)


# --- RA §3.2 fixtures: numbers -------------------------------------------------------------------


def test_usd_fri_to_mon():
    p = overnight_period(FRI, MON, dict([sofr(FRI, "4.30")]), NY, ACT_360)
    assert q12(p.r) == D("0.000358333333")
    assert p.legs == ((FRI, D("4.30"), 3),)


def test_usd_fri_to_tue_with_monday_holiday():
    fri, tue = date(2026, 1, 16), date(2026, 1, 20)  # Monday 2026-01-19 is a synthetic NY holiday
    p = overnight_period(fri, tue, dict([sofr(fri, "4.30")]), NY, ACT_360)
    assert q12(p.r) == D("0.000477777778")
    assert p.legs == ((fri, D("4.30"), 4),)


def test_usd_thu_to_mon():
    thu, fri, mon = date(2026, 1, 22), date(2026, 1, 23), date(2026, 1, 26)
    p = overnight_period(thu, mon, dict([sofr(thu, "4.30"), sofr(fri, "4.40")]), NY, ACT_360)
    assert q12(p.r) == D("0.000486154907")
    assert p.legs == ((thu, D("4.30"), 1), (fri, D("4.40"), 3))


def test_usd_look_ahead_trap_monday_sofr_is_not_used():
    """CASH-USD-INV-3: Monday's SOFR is in the view and already published; it is still unused."""
    with_monday = dict([sofr(FRI, "4.30"), sofr(MON, "9.99", published=MON)])
    p = overnight_period(FRI, MON, with_monday, NY, ACT_360)
    assert q12(p.r) == D("0.000358333333")
    assert p == overnight_period(FRI, MON, dict([sofr(FRI, "4.30")]), NY, ACT_360)


def test_aud_fri_to_mon_and_one_ordinary_day():
    assert q12(overnight_period(FRI, MON, dict([rba(FRI, "3.60")]), SYD, ACT_365F).r) == D("0.000295890411")
    assert q12(overnight_period(MON, TUE, dict([rba(MON, "3.60")]), SYD, ACT_365F).r) == D("0.000098630137")


def test_weekend_is_not_compounded_daily():
    p = overnight_period(FRI, MON, dict([sofr(FRI, "4.30")]), NY, ACT_360)
    assert q12(p.r) != D("0.000358376136")  # the daily-compounding convention, which is not used


# --- RA §3.2: information availability ----------------------------------------------------------------


def test_usd_period_is_knowable_when_fridays_sofr_is_published():
    """CASH-USD-INV-4: Fri→Mon is knowable at Friday's SOFR publication (Monday morning NY)."""
    p = overnight_period(FRI, MON, dict([sofr(FRI, "4.30")]), NY, ACT_360)
    assert p.knowable_at == utc(2026, 1, 12, 13)


def test_period_is_absent_when_a_needed_rate_is_not_in_the_view():
    with pytest.raises(MissingRate) as exc:
        overnight_period(FRI, MON, {}, NY, ACT_360)
    assert exc.value.business_day == FRI


def test_period_knowable_at_is_the_latest_input_and_weakest_basis_is_reported():
    thu, fri, mon = date(2026, 1, 22), date(2026, 1, 23), date(2026, 1, 26)
    weak = RateFixing(fri, D("4.40"), utc(2026, 1, 26, 13), KnowableBasis.SCHEDULE_ONLY)
    p = overnight_period(thu, mon, {thu: sofr(thu, "4.30")[1], fri: weak}, NY, ACT_360)
    assert p.knowable_at == utc(2026, 1, 26, 13)
    assert p.weakest_basis is KnowableBasis.SCHEDULE_ONLY


def test_cash_index_ratio_equals_period_return():
    """CASH-AUD-INV-1 / CASH-USD-INV-1 and RA-INV-003 (the index is the product of 1 + r)."""
    returns = [(MON, D("0.000295890411")), (TUE, D("0.000098630137"))]
    index = chain_index(returns)
    assert index[-1][1] == D(100) * (1 + returns[0][1]) * (1 + returns[1][1])


# --- FX: numbers ---------------------------------------------------------------------------------------


def fx_inputs(q_fri: str, q_mon: str):
    quotes = {
        FRI: FxQuote(FRI, D(q_fri), utc(2026, 1, 9, 5), COS),  # 16:00 Sydney fixing
        MON: FxQuote(MON, D(q_mon), utc(2026, 1, 12, 5), COS),
    }
    return quotes, dict([sofr(FRI, "4.30")]), dict([rba(FRI, "3.60")])


def test_fxc_inv_4_fri_to_mon_fixture():
    quotes, usd, aud = fx_inputs("0.6633", "0.66")  # q_{t−1}/q_t = 1.005, so s = +0.5%
    p = fx_period(FRI, MON, quotes, usd, NY, aud, SYD)
    assert p.s == D("0.005")
    assert q12(p.R) == D("0.005360125000")
    assert q12(p.X) == D("0.005064234589")
    assert q12(p.carry) == D("0.000062442922")
    assert q12(p.cross) == D("0.000001791667")
    assert abs(p.X - (p.s + p.carry + p.cross)) < D("1e-30")  # FXC-INV-1
    assert abs(p.R - (p.r_aud + p.X)) < D("1e-30")  # FXC-INV-2


@pytest.mark.parametrize(
    ("q_prev", "q_now", "sign"),
    [("0.66", "0.65", 1), ("0.65", "0.66", -1)],  # q falls: the AUD weakens, USD gains
)
def test_ra_inv_007_quote_inversion_for_falling_and_rising_q(q_prev, q_now, sign):
    s = spot_return(D(q_prev), D(q_now))
    assert s == D(q_prev) / D(q_now) - 1
    assert (s > 0) == (sign > 0)
    assert s != D(q_now) / D(q_prev) - 1


def test_ra_inv_006_translation_identity():
    quotes, usd, aud = fx_inputs("0.6700", "0.6612")
    p = fx_period(FRI, MON, quotes, usd, NY, aud, SYD)
    assert abs((1 + p.R) - (1 + p.r_usd) * (1 + p.s)) < D("1e-30")


def test_worked_example_14_2_one_day():
    """RA §14.2: one day, s = +0.5%, USD 4.30% ACT/360, AUD 3.60% ACT/365F."""
    quotes = {
        MON: FxQuote(MON, D("0.6633"), utc(2026, 1, 12, 5), COS),
        TUE: FxQuote(TUE, D("0.66"), utc(2026, 1, 13, 5), COS),
    }
    p = fx_period(MON, TUE, quotes, dict([sofr(MON, "4.30")]), NY, dict([rba(MON, "3.60")]), SYD)
    assert p.R.quantize(D("1e-9")) == D("0.005120042")
    assert p.X.quantize(D("1e-9")) == D("0.005021412")


# --- FX: information availability ------------------------------------------------------------------


def test_fx_excess_is_knowable_only_after_the_in_arrears_usd_leg():
    """The USD leg is in arrears, so X_t is knowable after the Sydney fixing: at Friday's SOFR
    publication on Monday in New York, not at Monday's 16:00 Sydney fixing."""
    quotes, usd, aud = fx_inputs("0.6633", "0.66")
    p = fx_period(FRI, MON, quotes, usd, NY, aud, SYD)
    assert p.knowable_at == utc(2026, 1, 12, 13)
    assert p.knowable_at > quotes[MON].knowable_at


def test_joint_calendar_is_sydney_business_days_with_a_fixing():
    quotes = {d: FxQuote(d, D("0.66"), utc(2026, 1, 30), COS) for d in [FRI, SAT, MON, date(2026, 1, 26)]}
    assert joint_calendar(quotes, SYD) == [FRI, MON]  # Saturday and the Sydney holiday drop out


# --- RA-INV-016: cumulative relationships ------------------------------------------------------------


def test_worked_example_14_5_cumulative_gap_is_a_compounding_fact():
    c, x1, x2 = D("0.0002"), D("0.01"), D("-0.005")
    tr = compound([c + x1, c + x2])
    assert tr == D("0.005351040")
    gap = tr - (compound([c, c]) + compound([x1, x2]))
    assert gap == c * (x1 + x2)  # 0.000001 = 0.000100%: not an error


# --- RA-INV-021: cash versus forward on the same capital ----------------------------------------


@pytest.mark.parametrize(
    ("s0", "s_t", "r_h", "r_f", "f", "cash", "per_notional"),
    [
        (D(1), D(1), D("0.10"), D(0), D("1.1"), D("-0.100000000000"), D("-0.090909090909")),
        (
            D("1.5385"),
            D("1.5000"),
            D("0.036") * 30 / 365,
            D("0.043") * 30 / 360,
            D("1.5375427458"),
            D("-0.024489615842"),
            D("-0.024417367194"),
        ),
    ],
)
def test_ra_inv_021_fixtures(s0, s_t, r_h, r_f, f, cash, per_notional):
    forward = cip_forward(s0, r_h, r_f)
    assert forward.quantize(D("1e-10")) == f
    assert q12(funded_cash_excess(s0, s_t, r_h, r_f)) == cash
    assert q12(forward_excess_per_capital(s0, s_t, forward, r_f)) == cash  # identical under CIP
    assert q12(forward_return_per_notional(s_t, forward)) == per_notional
    assert q12(notional_to_capital(forward_return_per_notional(s_t, forward), r_h)) == cash
