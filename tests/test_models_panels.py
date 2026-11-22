"""The monthly panel calculation (gold marts contract §5; OD-0233). Invented data only."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal
from itertools import pairwise
from typing import Any

import pytest

from hio.contracts.gold import TABLES, FactorSeries, table_bytes
from hio.models.panels import build_panel
from hio.portfolio.fixed_allocation import Interval, align, period_returns, sleeve_levels

PANEL_ID = "p" * 64
D = Decimal


def make_series(
    factor_id: str,
    periods: list[tuple[str, str, tuple[str, ...]]],
    *,
    series_class: str = "total_return",
    numeraire: str = "USD",
    build_id: str | None = None,
) -> FactorSeries:
    """A verified-looking series built in memory: `periods` is `(start, end, legs...)`, the legs
    being `total_return`, or `asset_return, cash_return, excess_return`."""
    names = (
        ("total_return",)
        if series_class == "total_return"
        else ("asset_return", "cash_return", "excess_return")
    )
    columns = ("period_start", "period_end", *names)
    rows = [dict(zip(columns, (start, end, *legs), strict=True)) for start, end, legs in periods]
    digest = factor_id.encode().hex().ljust(64, "0")[:64]
    return FactorSeries(
        factor_id=factor_id,
        spec_version="0.1.0",
        build_id=build_id or digest[:16],
        series_sha256=digest,
        series_class=series_class,
        numeraire=numeraire,
        record={},
        columns=columns,
        rows=rows,
    )


def total(factor_id: str, periods: list[tuple[str, str, str]], **kw: Any) -> FactorSeries:
    return make_series(factor_id, [(a, b, (r,)) for a, b, r in periods], **kw)


def spec_for(**members: str) -> dict[str, Any]:
    return {
        "name": "example",
        "version": "0.1.0",
        "status": "proposed",
        "kind": "panel",
        "frequency": "monthly",
        "alignment": "common_boundaries",
        "incomplete_periods": "exclude",
        "members": members,
        "sha256": "0" * 64,
    }


# A: has 2026-02-03 which B lacks.  B: has 2026-03-16 which A lacks.
A_PERIODS = [
    ("2026-01-29", "2026-01-30", "0.01"),
    ("2026-01-30", "2026-02-02", "0.02"),
    ("2026-02-02", "2026-02-03", "0.03"),
    ("2026-02-03", "2026-02-13", "-0.01"),
    ("2026-02-13", "2026-02-27", "0.005"),
    ("2026-02-27", "2026-03-02", "0.004"),
    ("2026-03-02", "2026-03-31", "0.015"),
    ("2026-03-31", "2026-04-01", "-0.02"),
    ("2026-04-01", "2026-04-02", "0.002"),
]
B_PERIODS = [
    ("2026-01-29", "2026-01-30", "0.002"),
    ("2026-01-30", "2026-02-02", "-0.004"),
    ("2026-02-02", "2026-02-13", "0.01"),
    ("2026-02-13", "2026-02-27", "0.006"),
    ("2026-02-27", "2026-03-02", "-0.003"),
    ("2026-03-02", "2026-03-16", "0.007"),
    ("2026-03-16", "2026-03-31", "0.008"),
    ("2026-03-31", "2026-04-01", "0.001"),
    ("2026-04-01", "2026-04-02", "0.002"),
]


def by_member(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    for row in sorted(rows, key=lambda r: (r["member_code"], r["period_end"])):
        out.setdefault(row["member_code"], []).append(row)
    return out


def two_member_panel() -> dict[str, list[dict[str, str]]]:
    members = {"a": total("fa", A_PERIODS), "b": total("fb", B_PERIODS)}
    return build_panel(spec_for(a="fa", b="fb"), members, PANEL_ID)


def test_hand_calculated_two_members_on_unequal_calendars() -> None:
    tables = two_member_panel()
    returns = by_member(tables["fact_panel_return"])
    # Common boundaries: 01-29, 01-30, 02-02, 02-13, 02-27, 03-02, 03-31, 04-01, 04-02.
    # Marks: 01-30, 02-27, 03-31 (the next common boundary is in another month). Two months.
    a_feb = D("1.02") * D("1.03") * D("0.99") * D("1.005") - 1
    a_mar = D("1.004") * D("1.015") - 1
    b_feb = D("0.996") * D("1.01") * D("1.006") - 1
    b_mar = D("0.997") * D("1.007") * D("1.008") - 1
    assert [(r["period_start"], r["period_end"]) for r in returns["a"]] == [
        ("2026-01-30", "2026-02-27"),
        ("2026-02-27", "2026-03-31"),
    ]
    assert [D(r["return"]) for r in returns["a"]] == [a_feb, a_mar]
    assert [D(r["return"]) for r in returns["b"]] == [b_feb, b_mar]
    assert [(r["period_start"], r["period_end"]) for r in returns["b"]] == [
        ("2026-01-30", "2026-02-27"),
        ("2026-02-27", "2026-03-31"),
    ]


def test_part_months_before_the_first_mark_and_after_the_last_are_excluded() -> None:
    returns = by_member(two_member_panel()["fact_panel_return"])
    for rows in returns.values():
        assert len(rows) == 2
        assert rows[0]["period_start"] == "2026-01-30"  # not 01-29: January is a part month
        assert rows[-1]["period_end"] == "2026-03-31"  # not 04-02: April is a part month
    # The excluded days do not move any included return: change them and nothing included moves.
    changed_a = [(*p[:2], "0.5") if p[0] in ("2026-01-29", "2026-04-01") else p for p in A_PERIODS]
    other = build_panel(
        spec_for(a="fa", b="fb"),
        {"a": total("fa", changed_a), "b": total("fb", B_PERIODS)},
        PANEL_ID,
    )
    assert other["fact_panel_return"] == two_member_panel()["fact_panel_return"]


def test_total_return_leg_cells_are_empty_and_text() -> None:
    for row in two_member_panel()["fact_panel_return"]:
        assert row["asset_return"] == "" and row["cash_return"] == ""
        assert row["panel_build_id"] == PANEL_ID
        assert all(isinstance(cell, str) for cell in row.values())


def test_coverage_counts() -> None:
    coverage = {r["member_code"]: r for r in two_member_panel()["fact_panel_coverage"]}
    for code in ("a", "b"):
        row = coverage[code]
        assert row["panel_build_id"] == PANEL_ID
        assert row["first_boundary"] == "2026-01-29"
        assert row["last_boundary"] == "2026-04-02"
        assert row["boundaries"] == "10"  # 9 common plus one of its own
        assert row["omitted_boundaries"] == "1"
        assert row["common_first"] == "2026-01-29"
        assert row["common_last"] == "2026-04-02"
        assert row["months"] == "2"


def test_coverage_first_and_last_boundary_are_the_members_own() -> None:
    late = total("fb", B_PERIODS[1:])  # starts 01-30
    tables = build_panel(spec_for(a="fa", b="fb"), {"a": total("fa", A_PERIODS), "b": late}, PANEL_ID)
    coverage = {r["member_code"]: r for r in tables["fact_panel_coverage"]}
    assert coverage["a"]["first_boundary"] == "2026-01-29"
    assert coverage["a"]["omitted_boundaries"] == "2"  # 02-03 and 01-29
    assert coverage["b"]["first_boundary"] == "2026-01-30"
    assert coverage["b"]["omitted_boundaries"] == "1"  # 03-16
    assert coverage["b"]["common_first"] == "2026-01-30"
    assert coverage["b"]["months"] == "2"


def test_bridge_rows() -> None:
    bridge = two_member_panel()["bridge_panel_member"]
    members = {"a": total("fa", A_PERIODS), "b": total("fb", B_PERIODS)}
    assert [r["member_code"] for r in bridge] == ["a", "b"]
    for order, row in enumerate(bridge):
        series = members[row["member_code"]]
        assert row == {
            "panel_build_id": PANEL_ID,
            "member_code": row["member_code"],
            "column_order": str(order),
            "factor_id": series.factor_id,
            "spec_version": "0.1.0",
            "input_build_id": series.build_id,
            "input_series_sha256": series.series_sha256,
            "series_class": "total_return",
            "numeraire": "USD",
        }


def test_column_order_follows_sorted_member_code_not_spec_order() -> None:
    members = {"zed": total("f1", A_PERIODS), "alpha": total("f2", B_PERIODS)}
    bridge = build_panel(spec_for(zed="f1", alpha="f2"), members, PANEL_ID)["bridge_panel_member"]
    assert {r["member_code"]: r["column_order"] for r in bridge} == {"alpha": "0", "zed": "1"}


EXCESS_DATES = ["2026-01-30", "2026-02-10", "2026-02-27", "2026-03-02"]


def excess_member(factor_id: str, assets: list[str], cashes: list[str]) -> FactorSeries:
    periods = []
    for (start, end), asset, cash in zip(pairwise(EXCESS_DATES), assets, cashes, strict=True):
        periods.append((start, end, (asset, cash, str(D(asset) - D(cash)))))
    return make_series(factor_id, periods, series_class="excess")


def test_excess_legs_are_compounded_separately_not_daily_excess() -> None:
    member = excess_member("fx", ["0.10", "0.10", "0.001"], ["0.01", "0.01", "0.001"])
    other = excess_member("fy", ["0.02", "0.03", "0"], ["0.001", "0.002", "0"])
    tables = build_panel(spec_for(x="fx", y="fy"), {"x": member, "y": other}, PANEL_ID)
    rows = by_member(tables["fact_panel_return"])
    # One month, 01-30 -> 02-27: the legs compound over the month first, then are differenced.
    asset = D("1.10") * D("1.10") - 1  # 0.21
    cash = D("1.01") * D("1.01") - 1  # 0.0201
    assert len(rows["x"]) == 1
    row = rows["x"][0]
    assert D(row["asset_return"]) == asset
    assert D(row["cash_return"]) == cash
    assert D(row["return"]) == asset - cash == D("0.1899")
    # Compounding the daily excess (0.09 twice) gives something else.
    daily_excess_compounded = D("1.09") * D("1.09") - 1
    assert daily_excess_compounded == D("0.1881")
    assert D(row["return"]) != daily_excess_compounded
    y = rows["y"][0]
    assert D(y["return"]) == (D("1.02") * D("1.03") - 1) - (D("1.001") * D("1.002") - 1)
    assert {r["series_class"] for r in tables["bridge_panel_member"]} == {"excess"}


def test_decimals_are_exact_and_in_context_precision() -> None:
    # 1 + 1e-20 compounded: a float would lose it; the text keeps every digit.
    periods = [
        ("2026-01-30", "2026-02-02", "0.00000000000000000001"),
        ("2026-02-02", "2026-02-27", "0.00000000000000000001"),
        ("2026-02-27", "2026-03-02", "0"),
    ]
    tables = build_panel(spec_for(a="fa"), {"a": total("fa", periods)}, PANEL_ID)
    assert tables["fact_panel_return"][0]["return"] == "0.0000000000000000000200000000000000000001"


def test_refuses_members_with_different_numeraires() -> None:
    members = {"a": total("fa", A_PERIODS), "b": total("fb", B_PERIODS, numeraire="AUD")}
    with pytest.raises(ValueError, match="numeraire"):
        build_panel(spec_for(a="fa", b="fb"), members, PANEL_ID)


def test_refuses_members_with_different_series_classes() -> None:
    excess = excess_member("fb", ["0.01", "0.01", "0.01"], ["0", "0", "0"])
    members = {"a": total("fa", A_PERIODS), "b": excess}
    with pytest.raises(ValueError, match="series_class"):
        build_panel(spec_for(a="fa", b="fb"), members, PANEL_ID)


def test_refuses_a_gap() -> None:
    gap = [p for p in A_PERIODS if p[0] != "2026-02-13"]  # 02-03 -> 02-13 then 02-27 -> ...
    members = {"a": total("fa", gap), "b": total("fb", B_PERIODS)}
    with pytest.raises(ValueError, match="do not join"):
        build_panel(spec_for(a="fa", b="fb"), members, PANEL_ID)


def test_refuses_an_overlap() -> None:
    overlap = [*A_PERIODS[:2], ("2026-02-01", "2026-02-03", "0.01"), *A_PERIODS[3:]]
    members = {"a": total("fa", overlap)}
    with pytest.raises(ValueError, match=r"not strictly increasing|do not join"):
        build_panel(spec_for(a="fa"), members, PANEL_ID)


def test_refuses_a_non_increasing_period() -> None:
    backwards = [*A_PERIODS[:3], ("2026-02-03", "2026-02-03", "0.01"), *A_PERIODS[4:]]
    with pytest.raises(ValueError, match="ends on or before its start"):
        build_panel(spec_for(a="fa"), {"a": total("fa", backwards)}, PANEL_ID)
    reversed_ = list(reversed(A_PERIODS))
    with pytest.raises(ValueError, match=r"ends on or before|strictly increasing"):
        build_panel(spec_for(a="fa"), {"a": total("fa", reversed_)}, PANEL_ID)


def test_refuses_periods_out_of_order() -> None:
    shuffled = [A_PERIODS[1], A_PERIODS[0], *A_PERIODS[2:]]
    with pytest.raises(ValueError, match="strictly increasing"):
        build_panel(spec_for(a="fa"), {"a": total("fa", shuffled)}, PANEL_ID)


def test_refuses_fewer_than_two_common_boundaries() -> None:
    a = total("fa", [("2026-01-30", "2026-02-27", "0.01")])
    b = total("fb", [("2026-03-02", "2026-03-31", "0.01")])
    with pytest.raises(ValueError, match="fewer than two common boundaries"):
        build_panel(spec_for(a="fa", b="fb"), {"a": a, "b": b}, PANEL_ID)
    c = total("fc", [("2026-02-27", "2026-03-31", "0.01")])  # shares exactly one date with a
    with pytest.raises(ValueError, match="fewer than two common boundaries"):
        build_panel(spec_for(a="fa", c="fc"), {"a": a, "c": c}, PANEL_ID)


def test_refuses_fewer_than_two_marks() -> None:
    # Boundaries 01-30, 02-02, 02-27: only 01-30 is a mark (02-27 is last, so never one).
    one_mark = total("fa", [("2026-01-30", "2026-02-02", "0.01"), ("2026-02-02", "2026-02-27", "0.01")])
    with pytest.raises(ValueError, match="fewer than two marks"):
        build_panel(spec_for(a="fa"), {"a": one_mark}, PANEL_ID)
    within_one_month = total(
        "fa", [("2026-02-02", "2026-02-10", "0.01"), ("2026-02-10", "2026-02-27", "0.01")]
    )
    with pytest.raises(ValueError, match="fewer than two marks"):
        build_panel(spec_for(a="fa"), {"a": within_one_month}, PANEL_ID)
    # The last common boundary is never a mark: 01-30 is the only mark here.
    ends_at_month_start = total(
        "fa", [("2026-01-30", "2026-02-02", "0.01"), ("2026-02-02", "2026-02-10", "0.01")]
    )
    with pytest.raises(ValueError, match="fewer than two marks"):
        build_panel(spec_for(a="fa"), {"a": ends_at_month_start}, PANEL_ID)


def test_refuses_members_keys_that_differ_from_the_spec() -> None:
    spec = spec_for(a="fa", b="fb")
    a, b = total("fa", A_PERIODS), total("fb", B_PERIODS)
    with pytest.raises(ValueError, match="differ from the spec"):
        build_panel(spec, {"a": a}, PANEL_ID)
    with pytest.raises(ValueError, match="differ from the spec"):
        build_panel(spec, {"a": a, "b": b, "c": b}, PANEL_ID)
    with pytest.raises(ValueError, match="differ from the spec"):
        build_panel(spec, {"a": a, "x": b}, PANEL_ID)


def test_refuses_a_member_whose_factor_id_differs_from_the_spec() -> None:
    with pytest.raises(ValueError, match="factor_id"):
        build_panel(
            spec_for(a="fa", b="fb"), {"a": total("fa", A_PERIODS), "b": total("other", B_PERIODS)}, PANEL_ID
        )


@pytest.mark.parametrize("bad", ["", "abc", "nan", "inf", "1_0", " 0.1"])
def test_refuses_a_return_that_is_not_a_finite_decimal(bad: str) -> None:
    periods = [(*A_PERIODS[0][:2], bad), *A_PERIODS[1:]]
    with pytest.raises(ValueError, match=r"decimal|finite"):
        build_panel(spec_for(a="fa"), {"a": total("fa", periods)}, PANEL_ID)


def test_refuses_an_empty_series_and_a_non_iso_date() -> None:
    with pytest.raises(ValueError, match="no periods"):
        build_panel(spec_for(a="fa"), {"a": total("fa", [])}, PANEL_ID)
    with pytest.raises(ValueError, match="ISO date"):
        build_panel(spec_for(a="fa"), {"a": total("fa", [("20260130", "2026-02-27", "0.01")])}, PANEL_ID)


def test_is_pure_and_repeatable_and_leaves_inputs_alone() -> None:
    members = {"a": total("fa", A_PERIODS), "b": total("fb", B_PERIODS)}
    before = [list(s.rows) for s in members.values()]
    first = build_panel(spec_for(a="fa", b="fb"), members, PANEL_ID)
    second = build_panel(spec_for(a="fa", b="fb"), members, PANEL_ID)
    assert first == second
    assert [list(s.rows) for s in members.values()] == before


def test_output_is_accepted_by_table_bytes() -> None:
    tables = two_member_panel()
    assert set(tables) == set(TABLES["panel"])
    for name, rows in tables.items():
        data = table_bytes("panel", name, rows)
        assert data.startswith(",".join(TABLES["panel"][name]).encode())
        assert data.count(b"\n") == len(rows) + 1
    # Row order does not matter to the bytes.
    shuffled = {name: list(reversed(rows)) for name, rows in tables.items()}
    for name in tables:
        assert table_bytes("panel", name, shuffled[name]) == table_bytes("panel", name, tables[name])


def test_excess_output_is_accepted_by_table_bytes() -> None:
    member = excess_member("fx", ["0.10", "0.10", "0.001"], ["0.01", "0.01", "0.001"])
    tables = build_panel(spec_for(x="fx"), {"x": member}, PANEL_ID)
    for name, rows in tables.items():
        table_bytes("panel", name, rows)


# ----------------------------------------------------------------------------------------
# Cross-check against today's floating-point alignment
# ----------------------------------------------------------------------------------------


def business_days(start: date, count: int) -> list[date]:
    days: list[date] = []
    cursor = start
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


def random_member(rng: random.Random, factor_id: str, days: list[date]) -> FactorSeries:
    kept = [d for i, d in enumerate(days) if i in (0, len(days) - 1) or rng.random() < 0.8]
    periods = []
    for start, end in pairwise(kept):
        span = len([d for d in days if start < d <= end])
        scale = D(rng.randint(-250, 250) * span).scaleb(-4)
        periods.append((start.isoformat(), end.isoformat(), format(scale, "f")))
    return total(factor_id, periods)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_matches_fixed_allocation_to_1e_12(seed: int) -> None:
    rng = random.Random(seed)
    days = business_days(date(2026, 1, 5), 150)
    members = {code: random_member(rng, f"f_{code}", days) for code in ("eq", "bd", "gd")}
    spec = spec_for(**{code: f"f_{code}" for code in members})
    tables = build_panel(spec, members, PANEL_ID)

    series = {
        code: [
            Interval(
                date.fromisoformat(r["period_start"]),
                date.fromisoformat(r["period_end"]),
                D(r["total_return"]),
            )
            for r in s.rows
        ]
        for code, s in members.items()
    }
    panel = align(series)
    expected = period_returns(panel.dates, sleeve_levels(panel), "monthly")
    rows = by_member(tables["fact_panel_return"])
    assert expected.shape[0] >= 3
    for column, code in enumerate(panel.sleeves):
        mine = [float(r["return"]) for r in rows[code]]
        assert len(mine) == expected.shape[0]
        assert max(abs(a - b) for a, b in zip(mine, expected[:, column], strict=True)) < 1e-12
    coverage = {r["member_code"]: r for r in tables["fact_panel_coverage"]}
    for code in panel.sleeves:
        assert int(coverage[code]["omitted_boundaries"]) == panel.omitted_dates[code]
        assert coverage[code]["common_first"] == panel.dates[0].isoformat()
        assert coverage[code]["common_last"] == panel.dates[-1].isoformat()
        assert int(coverage[code]["months"]) == expected.shape[0]
