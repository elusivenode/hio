"""T-0021: fixed-allocation calculations, against hand-worked numbers. Every figure is invented."""

from datetime import date, timedelta
from decimal import Decimal as D
from itertools import pairwise

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from hio.portfolio.fixed_allocation import (
    AlignmentError,
    Interval,
    align,
    annualised_return,
    annualised_volatility,
    covariance,
    drawdown,
    paired_block_bootstrap,
    period_ends,
    period_returns,
    reconcile,
    sleeve_levels,
    wealth_path,
    window,
)


def d(day: int, month: int = 1) -> date:
    return date(2026, month, day)


def chain(*rows: tuple[date, date, str]) -> list[Interval]:
    return [Interval(a, b, D(r)) for a, b, r in rows]


# --- alignment


def test_a_sleeve_is_compounded_across_a_date_another_sleeve_lacks():
    panel = align(
        {
            "a": chain((d(5), d(6), "0.1"), (d(6), d(7), "0.1")),
            "b": chain((d(5), d(7), "0.5")),
        }
    )
    assert panel.dates == (d(5), d(7))
    assert panel.returns[0, 0] == pytest.approx(0.21, abs=1e-15)
    assert panel.returns[0, 1] == 0.5
    assert panel.omitted_dates == {"a": 1, "b": 0}


def test_dates_outside_the_common_span_are_counted_not_used():
    panel = align(
        {
            "a": chain((d(5), d(6), "0.1"), (d(6), d(7), "0.2")),
            "b": chain((d(6), d(7), "0.3")),
        }
    )
    assert panel.dates == (d(6), d(7))
    assert panel.returns.tolist() == [[0.2, 0.3]]
    assert panel.omitted_dates == {"a": 1, "b": 0}


def test_a_gap_inside_a_sleeve_refuses_and_is_never_filled():
    with pytest.raises(AlignmentError, match="don't join"):
        align({"a": chain((d(5), d(6), "0.1"), (d(7), d(8), "0.1"))})


def test_too_few_common_dates_refuse():
    with pytest.raises(AlignmentError, match="fewer than two"):
        align({"a": chain((d(5), d(6), "0.1")), "b": chain((d(7), d(8), "0.1"))})


def test_a_backward_period_refuses():
    with pytest.raises(AlignmentError, match="ends on or before"):
        align({"a": chain((d(6), d(5), "0.1"))})


# --- wealth, by hand


def jan_feb_panel():
    # Two sleeves over 30 Jan, 2 Feb, 3 Feb. Month end is 30 Jan, which is the first date.
    return align(
        {
            "a": chain((date(2026, 1, 29), d(30), "0.10"), (d(30), d(2, 2), "0.10"), (d(2, 2), d(3, 2), "0")),
            "b": chain((date(2026, 1, 29), d(30), "0"), (d(30), d(2, 2), "0"), (d(2, 2), d(3, 2), "0")),
        }
    )


def test_wealth_by_hand_with_a_month_end_rebalance():
    panel = jan_feb_panel()
    path = wealth_path(panel, {"a": 0.5, "b": 0.5})
    # 29 Jan: 0.5, 0.5. 30 Jan is month end: 0.55 + 0.5 = 1.05, reset to 0.525 each.
    # 2 Feb: 0.5775 + 0.525 = 1.1025.  3 Feb: unchanged.
    assert path.wealth.tolist() == pytest.approx([1.0, 1.05, 1.1025, 1.1025], abs=1e-15)
    assert path.holdings[1].tolist() == pytest.approx([0.525, 0.525], abs=1e-15)
    assert reconcile(panel, {"a": 0.5, "b": 0.5}, path) <= 1e-12


def test_without_a_rebalance_a_position_drifts():
    panel = align(
        {
            "a": chain((d(5), d(6), "0.10"), (d(6), d(7), "0.10")),
            "b": chain((d(5), d(6), "0"), (d(6), d(7), "0")),
        }
    )
    path = wealth_path(panel, {"a": 0.5, "b": 0.5})
    assert path.wealth[-1] == pytest.approx(0.5 * 1.21 + 0.5, abs=1e-15)


def test_full_weight_is_the_sleeve_itself():
    panel = jan_feb_panel()
    path = wealth_path(panel, {"a": 1.0, "b": 0.0})
    assert path.wealth[-1] == pytest.approx(1.21, abs=1e-15)


@pytest.mark.parametrize(
    "weights", [{"a": 0.5}, {"a": 0.5, "b": 0.6}, {"a": 1.5, "b": -0.5}, {"a": 0.5, "c": 0.5}]
)
def test_bad_weights_refuse(weights):
    with pytest.raises(ValueError):
        wealth_path(jan_feb_panel(), weights)


def test_a_broken_path_fails_reconciliation():
    panel = jan_feb_panel()
    path = wealth_path(panel, {"a": 0.5, "b": 0.5})
    path.wealth[-1] *= 1.001
    with pytest.raises(ArithmeticError, match="reconcile"):
        reconcile(panel, {"a": 0.5, "b": 0.5}, path)


def long_panel(months: int = 40, seed: int = 7):
    """Invented daily returns across many months."""
    rng = np.random.default_rng(seed)
    start = date(2020, 1, 1)
    days = [start + timedelta(days=i) for i in range(months * 30)]
    series = {}
    for name, scale in (("eq", 0.01), ("dur", 0.004), ("bill", 0.0001)):
        draws = rng.normal(0.0002, scale, len(days) - 1)
        series[name] = [
            Interval(a, b, D(str(round(float(r), 10))))
            for a, b, r in zip(days[:-1], days[1:], draws, strict=True)
        ]
    return align(series)


def test_monthly_portfolio_returns_equal_the_weighted_sleeves_when_rebalanced():
    panel = long_panel()
    weights = {"bill": 0.4, "dur": 0.0, "eq": 0.6}
    path = wealth_path(panel, weights)
    from_wealth = period_returns(panel.dates, path.wealth, "monthly")
    sleeves = period_returns(panel.dates, sleeve_levels(panel), "monthly")
    vector = np.array([weights[s] for s in panel.sleeves])
    assert from_wealth == pytest.approx(sleeves @ vector, abs=1e-13)


@given(
    st.lists(st.floats(min_value=-0.2, max_value=0.2), min_size=2, max_size=60),
    st.floats(min_value=0, max_value=1),
)
def test_wealth_always_reconciles(returns, weight):
    start = date(2026, 1, 1)
    days = [start + timedelta(days=9 * i) for i in range(len(returns) + 1)]
    a = [Interval(x, y, D(str(r))) for x, y, r in zip(days[:-1], days[1:], returns, strict=True)]
    b = [Interval(x, y, D(0)) for x, y in pairwise(days)]
    panel = align({"a": a, "b": b})
    weights = {"a": weight, "b": 1 - weight}
    assert reconcile(panel, weights, wealth_path(panel, weights)) <= 1e-12


# --- periods and windows


def test_period_ends_drop_the_final_partial_period():
    dates = [date(2026, 1, 30), date(2026, 2, 2), date(2026, 2, 27), date(2026, 3, 2), date(2026, 3, 3)]
    assert period_ends(dates, "monthly") == [0, 2]


def test_a_closed_span_keeps_its_last_complete_month():
    dates = [date(2019, 12, 31), date(2020, 1, 31), date(2020, 2, 28), date(2020, 3, 31)]
    levels = np.array([1.0, 1.1, 1.1, 0.77])
    assert period_ends(dates, "monthly") == [0, 1, 2]
    assert period_ends(dates, "monthly", include_final=True) == [0, 1, 2, 3]
    returned = period_returns(dates, levels, "monthly", include_final=True)
    assert returned.tolist() == pytest.approx([0.1, 0.0, -0.3])
    assert period_returns(dates, levels, "monthly").tolist() == pytest.approx([0.1, 0.0])


def test_weekly_ends_cross_a_year_end_by_iso_week():
    dates = [date(2025, 12, 29), date(2026, 1, 2), date(2026, 1, 5)]
    assert period_ends(dates, "weekly") == [1]


def test_period_returns_are_between_period_ends():
    dates = [date(2026, 1, 30), date(2026, 2, 27), date(2026, 3, 31), date(2026, 4, 1)]
    returned = period_returns(dates, np.array([1.0, 1.1, 1.21, 2.0]), "monthly")
    assert returned.tolist() == pytest.approx([0.1, 0.1])


def test_a_window_restarts_wealth_and_keeps_one_contiguous_span():
    panel = long_panel(months=6)
    part = window(panel, panel.dates[10], panel.dates[20])
    assert part.dates == panel.dates[10:21]
    assert part.returns.shape[0] == 10
    assert wealth_path(part, {"bill": 1.0, "dur": 0.0, "eq": 0.0}).wealth[0] == 1.0


def test_an_empty_window_refuses():
    panel = long_panel(months=6)
    with pytest.raises(AlignmentError):
        window(panel, date(1999, 1, 1), date(1999, 2, 1))


# --- statistics


def test_volatility_by_hand():
    # sample sd of 0.01, -0.01 is sqrt(2) * 0.01; times sqrt(12)
    assert annualised_volatility(np.array([0.01, -0.01]), "monthly") == pytest.approx(
        0.01 * np.sqrt(2) * np.sqrt(12)
    )


def test_annualised_return_by_hand():
    panel = align({"a": chain((date(2025, 1, 1), date(2026, 1, 1), "0.1"))})
    path = wealth_path(panel, {"a": 1.0})
    assert annualised_return(path) == pytest.approx(1.1 ** (365.25 / 365) - 1)


def test_covariance_and_correlation_by_hand():
    returns = np.array([[0.01, 0.02], [-0.01, -0.02], [0.03, 0.06]])
    cov, corr = covariance(returns)
    assert cov[0, 1] == pytest.approx(2 * cov[0, 0])
    assert corr[0, 1] == pytest.approx(1.0)


DATES = [date(2026, 1, 1) + timedelta(days=10 * i) for i in range(6)]


def test_a_recovered_drawdown_by_hand():
    result = drawdown(DATES, np.array([1.0, 1.2, 0.9, 1.0, 1.2, 1.3]))
    assert result.max_drawdown == pytest.approx(0.25)
    assert (result.peak, result.trough, result.recovery) == (DATES[1], DATES[2], DATES[4])
    assert result.longest_underwater_days == 30
    assert result.underwater_fraction == pytest.approx(30 / 50)


def test_an_unrecovered_drawdown_has_no_recovery_and_runs_to_the_end():
    result = drawdown(DATES, np.array([1.0, 1.2, 0.9, 1.0, 1.1, 1.1]))
    assert result.recovery is None
    assert result.longest_underwater_days == 40
    assert result.underwater_fraction == pytest.approx(40 / 50)


def test_no_drawdown():
    result = drawdown(DATES, np.array([1.0, 1.1, 1.2, 1.3, 1.4, 1.5]))
    assert result.max_drawdown == 0
    assert result.recovery is None
    assert (result.longest_underwater_days, result.underwater_fraction) == (0, 0)


# --- bootstrap


def monthly_sample(months: int = 120, seed: int = 3):
    rng = np.random.default_rng(seed)
    return rng.normal([0.006, 0.003, 0.002], [0.04, 0.015, 0.001], size=(months, 3))


A = np.array([0.6, 0.0, 0.4])
B = np.array([0.6, 0.4, 0.0])


def test_a_fixed_seed_repeats_and_another_seed_differs():
    monthly = monthly_sample()
    first = paired_block_bootstrap(monthly, A, B, block_months=12, replications=300, seed=11)
    again = paired_block_bootstrap(monthly, A, B, block_months=12, replications=300, seed=11)
    other = paired_block_bootstrap(monthly, A, B, block_months=12, replications=300, seed=12)
    assert first == again
    assert first != other


def test_identical_portfolios_differ_by_exactly_zero_because_the_blocks_are_shared():
    result = paired_block_bootstrap(monthly_sample(), A, A, block_months=6, replications=100, seed=1)
    for interval in (result.volatility, result.annualised_return, result.max_drawdown):
        assert (interval.estimate, interval.low, interval.high) == (0, 0, 0)


def test_the_estimate_is_the_observed_paired_difference():
    monthly = monthly_sample()
    result = paired_block_bootstrap(monthly, A, B, block_months=12, replications=50, seed=1)
    expected = np.std(monthly @ B, ddof=1) * np.sqrt(12) - np.std(monthly @ A, ddof=1) * np.sqrt(12)
    assert result.volatility.estimate == pytest.approx(expected)


def test_blocks_keep_the_sleeves_of_a_month_together():
    # b equals a sleeve-for-sleeve only if rows move jointly; here two columns are perfect opposites.
    months = 60
    base = np.random.default_rng(5).normal(0, 0.02, months)
    monthly = np.column_stack((base, -base, np.zeros(months)))
    half = np.array([0.5, 0.5, 0.0])
    result = paired_block_bootstrap(
        monthly, half, np.array([0, 0, 1.0]), block_months=6, replications=50, seed=2
    )
    assert result.volatility.low == pytest.approx(0, abs=1e-15)
    assert result.volatility.high == pytest.approx(0, abs=1e-15)


@pytest.mark.parametrize("block", [0, 121])
def test_a_block_that_does_not_fit_refuses(block):
    with pytest.raises(ValueError):
        paired_block_bootstrap(monthly_sample(), A, B, block_months=block, replications=10, seed=1)
