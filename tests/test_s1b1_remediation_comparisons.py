"""Adversarial regressions for F-REVIEW-2026-10-25-t0009-3 (OD-0067): the index comparisons report
every eligible cash period, name the cause of each period they cannot compare, and classify against a
pre-registered rounding model whose bound is validated here independently of the code under test."""

from __future__ import annotations

import dataclasses
import random
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

import pytest

from hio.contracts.temporal import KnowledgeMode
from hio.jobs.s1b1 import (
    CASH,
    COMPARISON,
    _comparison,
    cash_series,
    rounding_bound,
    rounding_model,
)
from tests.test_s1b1_releases import (  # noqa: F401  (world is a fixture)
    rows,
    world,
)

MODE = KnowledgeMode.AS_CAPTURED_BY_HIO
D = date


def _series(world, cash_id):
    _store, cals, vs, cutoff, *_ = world
    sid, rate_key, end_key, base = CASH[cash_id]
    calendars = {"rits": cals.rits, "nsw": cals.nsw, "ny": cals.ny}
    return cash_series(vs.view(sid, MODE, cutoff, None), calendars[rate_key], calendars[end_key], base)


@pytest.mark.parametrize("out_id", sorted(COMPARISON))
def test_f3_every_eligible_cash_period_is_a_row(world, out_id):
    cash_id = COMPARISON[out_id][0]
    series = _series(world, cash_id)
    cmp = world[6][out_id]
    got = {(r["period_start"], r["period_end"]) for r in rows(cmp)}
    want = {(p.start.isoformat(), p.end.isoformat()) for p in series.periods}
    want |= {(s.isoformat(), e.isoformat()) for s, e, _ in series.gaps}
    assert got == want and len(rows(cmp)) == len(want)
    qs = cmp.core["quality_summary"]
    assert qs["periods"] == len(want)
    assert qs["periods_compared"] + qs["not_compared"] == qs["periods"]
    assert sum(qs["not_compared_by_cause"].values()) == qs["not_compared"]


def test_f3_the_first_aud_period_is_compared_not_dropped(world):
    data = rows(world[6]["cash.aud.overnight.vs_tri"])
    first = min(data, key=lambda r: r["period_start"])
    assert first["classification"] == "within_expected_bound"
    assert world[6]["cash.aud.overnight.vs_tri"].core["quality_summary"]["not_compared"] == 0


def test_f3_usd_periods_without_an_index_value_are_reported_with_their_cause(world):
    data = {r["period_start"]: r for r in rows(world[6]["cash.usd.overnight.vs_sofr_index"])}
    # Oct 12 is an NSW period end with no SOFR Index value (a derived US holiday).
    assert data["2026-10-09"]["classification"] == "not_compared"
    assert data["2026-10-09"]["cause"] == "reference_missing_at_end"
    assert data["2026-10-12"]["cause"] == "reference_missing_at_start"
    assert data["2026-10-09"]["ours"]  # our side is still shown
    qs = world[6]["cash.usd.overnight.vs_sofr_index"].core["quality_summary"]
    assert qs["not_compared_by_cause"]["reference_missing_at_end"] >= 1


def _compare(world, out_id, ref_values=None, series=None):
    _store, _cals, vs, cutoff, *_ = world
    cash_id, ref_sid, base = COMPARISON[out_id]
    view = vs.view(ref_sid, MODE, cutoff, None)
    if ref_values is not None:
        view = dataclasses.replace(view, values=ref_values(dict(view.values)))
    return _comparison(
        world[6][cash_id],
        series or _series(world, cash_id),
        view,
        out_id,
        {
            "version": "t",
            "code_ref": {"commit": "t", "lock_sha256": "0" * 64},
            "knowledge_mode": MODE.value,
            "knowledge_cutoff": None,
            "supersedes": None,
        },
        base,
        world[6][cash_id].core["rights"],
    )


def test_f3_a_reference_value_removed_mid_series_becomes_two_reported_rows(world):
    out_id = "cash.aud.overnight.vs_tri"
    gone = D(2026, 10, 22)
    cmp = _compare(world, out_id, lambda v: {d: x for d, x in v.items() if d != gone})
    by_end = {r["period_end"]: r for r in rows(cmp)}
    by_start = {r["period_start"]: r for r in rows(cmp)}
    assert by_end["2026-10-22"]["cause"] == "reference_missing_at_end"
    assert by_start["2026-10-22"]["cause"] == "reference_missing_at_start"
    assert cmp.core["quality_summary"]["not_compared_by_cause"] == {
        "reference_missing_at_end": 1,
        "reference_missing_at_start": 1,
    }


def test_f3_an_absent_cash_period_is_reported_not_dropped(world):
    out_id = "cash.aud.overnight.vs_tri"
    series = _series(world, "cash.aud.overnight")
    dropped = series.periods[3]
    holed = dataclasses.replace(
        series,
        periods=tuple(p for p in series.periods if p != dropped),
        gaps=(*series.gaps, (dropped.start, dropped.end, "synthetic gap")),
    )
    cmp = _compare(world, out_id, series=holed)
    row = next(r for r in rows(cmp) if r["period_start"] == dropped.start.isoformat())
    assert (row["classification"], row["cause"]) == ("not_compared", "cash_period_absent")


def test_f3_a_reference_with_more_places_than_declared_is_not_called_rounding(world):
    out_id = "cash.aud.overnight.vs_tri"
    target = D(2026, 10, 22)

    def finer(values):
        v = values[target]
        return {**values, target: dataclasses.replace(v, value=v.value + Decimal("0.00001"))}

    cmp = _compare(world, out_id, finer)
    affected = [r for r in rows(cmp) if target.isoformat() in (r["period_start"], r["period_end"])]
    assert affected and {r["classification"] for r in affected} == {"precision_exceeds_declared"}


def test_f3_a_disagreement_beyond_the_bound_is_classified_outside(world):
    out_id = "cash.usd.overnight.vs_sofr_index"
    target = D(2026, 10, 15)

    def off(values):
        v = values[target]
        return {**values, target: dataclasses.replace(v, value=v.value + Decimal("0.00000100"))}

    cmp = _compare(world, out_id, off)
    affected = [r for r in rows(cmp) if target.isoformat() in (r["period_start"], r["period_end"])]
    assert affected and {r["classification"] for r in affected} == {"outside_expected_bound"}
    assert all(r["cause"] == "residual not explained by publisher rounding" for r in affected)


def test_f3_the_rounding_model_is_declared_in_the_cited_spec():
    assert rounding_model("cash.aud.overnight", "rba.cash_rate.tri").reference_decimals == 4
    assert rounding_model("cash.usd.overnight", "nyfed.sofr_index").reference_decimals == 8
    with pytest.raises(LookupError):
        rounding_model("cash.usd.overnight", "rba.cash_rate.tri")


def _q(x: Decimal, places: int) -> Decimal:
    return x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)


@pytest.mark.parametrize("base,ref_dp,rate_dp,level", [(365, 4, 2, "100"), (360, 8, 2, "1.1")])
def test_f3_the_bound_covers_every_rounding_outcome_of_the_model(base, ref_dp, rate_dp, level):
    """Independent validation: draw unrounded rates and a start level, compound the publisher's
    index exactly from them and round it; compound HIO's side from the rounded rates. The observed
    difference must never exceed the bound, and the bound must not be loose by more than 3x."""
    rng = random.Random(20261028)
    worst_ratio = Decimal(0)
    with localcontext() as ctx:
        ctx.prec = 50
        for _ in range(400):
            legs_true = [
                (None, Decimal(rng.randint(0, 600_000)) / 100_000, rng.choice((1, 1, 1, 3, 4)))
                for _ in range(rng.randint(1, 3))
            ]
            start_true = Decimal(level) + Decimal(rng.randint(0, 10**9)) / 10**8
            end_true = start_true
            for _b, rate, n in legs_true:
                end_true *= 1 + rate * n / (100 * base)
            ref_s, ref_t = _q(start_true, ref_dp), _q(end_true, ref_dp)
            legs = [(b, _q(rate, rate_dp), n) for b, rate, n in legs_true]
            ours = Decimal(1)
            for _b, rate, n in legs:
                ours *= 1 + rate * n / (100 * base)
            diff = abs(ours - ref_t / ref_s)
            bound = rounding_bound(legs, base, rate_dp, ref_s, ref_t, ref_dp)
            assert diff <= bound
            worst_ratio = max(worst_ratio, diff / bound)
    assert worst_ratio > Decimal("0.33")  # the bound is attained to within a small factor


def test_f3_the_bound_is_not_the_first_order_estimate_it_replaces():
    """The replaced bound used ulp/ref_end for the start term, which understates the error when the
    index grows; the exact interval bound is never smaller than the true worst case."""
    legs = [(None, Decimal("5.00"), 1)]
    ref_s, ref_t = Decimal("1.0001"), Decimal("1.0003")
    u = Decimal("0.00005")
    exact_theirs = max(
        abs((ref_t + u) / (ref_s - u) - ref_t / ref_s), abs((ref_t - u) / (ref_s + u) - ref_t / ref_s)
    )
    assert rounding_bound(legs, 360, 2, ref_s, ref_t, 4) >= exact_theirs
    assert exact_theirs > u / ref_s + u / ref_t  # the replaced first-order form would understate it
