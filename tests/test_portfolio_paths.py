"""Tests for the portfolio-path calculation (gold marts contract §6). Invented data only."""

from __future__ import annotations

from decimal import Decimal

import pytest

from hio.contracts.gold import CTX, TABLES, parse_table, table_bytes
from hio.portfolio.paths import build_portfolio_path

PANEL_ID = "p" * 64
PORTFOLIO_ID = "q" * 64
MONTH_ENDS = ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30"]


def panel_tables(
    returns: dict[str, list[str]],
    *,
    series_class: str = "total_return",
    ends: list[str] | None = None,
) -> dict[str, list[dict[str, str]]]:
    """A panel's three tables, as parsed rows, for members given as code -> monthly returns."""
    ends = ends or MONTH_ENDS
    bridge = []
    facts = []
    coverage = []
    for order, code in enumerate(sorted(returns)):
        bridge.append(
            {
                "panel_build_id": PANEL_ID,
                "member_code": code,
                "column_order": str(order),
                "factor_id": f"factor.{code}",
                "spec_version": "0.1.0",
                "input_build_id": "a" * 16,
                "input_series_sha256": "b" * 64,
                "series_class": series_class,
                "numeraire": "AUD",
            }
        )
        for start, end, value in zip(ends[:-1], ends[1:], returns[code], strict=True):
            facts.append(
                {
                    "panel_build_id": PANEL_ID,
                    "member_code": code,
                    "period_start": start,
                    "period_end": end,
                    "return": value,
                    "asset_return": "",
                    "cash_return": "",
                }
            )
        coverage.append(
            {
                "panel_build_id": PANEL_ID,
                "member_code": code,
                "first_boundary": ends[0],
                "last_boundary": ends[-1],
                "boundaries": str(len(ends)),
                "omitted_boundaries": "0",
                "common_first": ends[0],
                "common_last": ends[-1],
                "months": str(len(returns[code])),
            }
        )
    return {"bridge_panel_member": bridge, "fact_panel_return": facts, "fact_panel_coverage": coverage}


def spec(weights: dict[str, str]) -> dict[str, object]:
    return {
        "name": "example",
        "version": "0.1.0",
        "status": "proposed",
        "kind": "portfolio_path",
        "panel": "example",
        "rebalance": "month_end",
        "weights": weights,
    }


EQUITY = ["0.10", "-0.05", "0.02"]
BONDS = ["0.01", "0.02", "-0.01"]


def two_member_result() -> dict[str, list[dict[str, str]]]:
    return build_portfolio_path(
        spec({"equity": "0.60", "bonds": "0.40"}),
        panel_tables({"equity": EQUITY, "bonds": BONDS}),
        PORTFOLIO_ID,
    )


def by_end(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["period_end"]: row for row in rows}


def test_hand_calculated_three_month_two_member_example() -> None:
    result = two_member_result()
    # Month 1: 0.6 * 0.10 + 0.4 * 0.01 = 0.064; wealth 1.064.
    # Month 2: 0.6 * -0.05 + 0.4 * 0.02 = -0.022; wealth 1.064 * 0.978 = 1.040592.
    # Month 3: 0.6 * 0.02 + 0.4 * -0.01 = 0.008; wealth 1.040592 * 1.008 = 1.048916736.
    expected_returns = [Decimal("0.064"), Decimal("-0.022"), Decimal("0.008")]
    expected_wealth = [Decimal("1.064"), Decimal("1.040592"), Decimal("1.048916736")]
    path = by_end(result["fact_portfolio_return"])
    assert list(path) == MONTH_ENDS[1:]
    for end, ret, wealth in zip(MONTH_ENDS[1:], expected_returns, expected_wealth, strict=True):
        assert Decimal(path[end]["portfolio_return"]) == ret
        assert Decimal(path[end]["wealth_index"]) == wealth
        assert path[end]["portfolio_build_id"] == PORTFOLIO_ID
    assert path["2026-02-28"]["period_start"] == "2026-01-31"
    assert path["2026-04-30"]["period_start"] == "2026-03-31"

    contributions = {(r["member_code"], r["period_end"]): r for r in result["fact_return_contribution"]}
    assert len(contributions) == 6
    expected = {
        ("equity", "2026-02-28"): ("0.60", "0.10", "0.0600"),
        ("equity", "2026-03-31"): ("0.60", "-0.05", "-0.0300"),
        ("equity", "2026-04-30"): ("0.60", "0.02", "0.0120"),
        ("bonds", "2026-02-28"): ("0.40", "0.01", "0.0040"),
        ("bonds", "2026-03-31"): ("0.40", "0.02", "0.0080"),
        ("bonds", "2026-04-30"): ("0.40", "-0.01", "-0.0040"),
    }
    for key, (weight, member_return, contribution) in expected.items():
        row = contributions[key]
        assert Decimal(row["start_weight"]) == Decimal(weight)
        assert Decimal(row["member_return"]) == Decimal(member_return)
        assert Decimal(row["contribution"]) == Decimal(contribution)

    allocation = {r["member_code"]: r["target_weight"] for r in result["fact_target_allocation"]}
    assert allocation == {"bonds": "0.40", "equity": "0.60"}


def test_every_cell_is_text() -> None:
    for rows in two_member_result().values():
        for row in rows:
            assert all(isinstance(cell, str) for cell in row.values())


def test_contributions_sum_to_the_portfolio_return_each_month() -> None:
    result = build_portfolio_path(
        spec({"a": "0.3333333333", "b": "0.3333333333", "c": "0.3333333334"}),
        panel_tables(
            {
                "a": ["0.0123456789", "-0.0345678901", "0.0555555555"],
                "b": ["-0.0087654321", "0.0200000001", "0.0100000003"],
                "c": ["0.0311111111", "0.0044444444", "-0.0222222222"],
            }
        ),
        PORTFOLIO_ID,
    )
    for end, row in by_end(result["fact_portfolio_return"]).items():
        total = Decimal(0)
        for part in result["fact_return_contribution"]:
            if part["period_end"] == end:
                total = CTX.add(total, Decimal(part["contribution"]))
        assert abs(total - Decimal(row["portfolio_return"])) <= Decimal("1e-30")


def test_zero_weight_member_contributes_nothing() -> None:
    result = build_portfolio_path(
        spec({"equity": "1", "bonds": "0"}),
        panel_tables({"equity": EQUITY, "bonds": BONDS}),
        PORTFOLIO_ID,
    )
    path = by_end(result["fact_portfolio_return"])
    assert [Decimal(path[e]["portfolio_return"]) for e in MONTH_ENDS[1:]] == [Decimal(r) for r in EQUITY]
    zero = [r for r in result["fact_return_contribution"] if r["member_code"] == "bonds"]
    assert len(zero) == 3
    assert all(Decimal(r["contribution"]) == 0 for r in zero)


def test_single_member_at_weight_one_reproduces_the_member() -> None:
    result = build_portfolio_path(spec({"equity": "1"}), panel_tables({"equity": EQUITY}), PORTFOLIO_ID)
    path = by_end(result["fact_portfolio_return"])
    wealth = Decimal(1)
    for end, value in zip(MONTH_ENDS[1:], EQUITY, strict=True):
        wealth = CTX.multiply(wealth, CTX.add(Decimal(1), Decimal(value)))
        assert Decimal(path[end]["portfolio_return"]) == Decimal(value)
        assert Decimal(path[end]["wealth_index"]) == wealth
    assert Decimal(path["2026-04-30"]["wealth_index"]) == Decimal("1.1") * Decimal("0.95") * Decimal("1.02")


def test_arithmetic_is_fifty_digits_not_float() -> None:
    result = build_portfolio_path(
        spec({"x": "1"}),
        panel_tables({"x": ["0.1234567890123456789012345678901234567890", "0", "0"]}),
        PORTFOLIO_ID,
    )
    path = by_end(result["fact_portfolio_return"])
    assert path["2026-02-28"]["portfolio_return"] == "0.1234567890123456789012345678901234567890"
    assert path["2026-02-28"]["wealth_index"] == "1.1234567890123456789012345678901234567890"


def test_output_is_accepted_by_table_bytes() -> None:
    result = two_member_result()
    for name, rows in result.items():
        data = table_bytes("portfolio_path", name, rows)
        parsed = parse_table("portfolio_path", name, data)
        assert len(parsed) == len(rows)
        assert set(parsed[0]) == set(TABLES["portfolio_path"][name])
    # Input order does not matter.
    reversed_tables = {
        k: list(reversed(v)) for k, v in panel_tables({"equity": EQUITY, "bonds": BONDS}).items()
    }
    again = build_portfolio_path(spec({"equity": "0.60", "bonds": "0.40"}), reversed_tables, PORTFOLIO_ID)
    for name in result:
        assert table_bytes("portfolio_path", name, again[name]) == table_bytes(
            "portfolio_path", name, result[name]
        )


def test_the_inputs_are_not_changed() -> None:
    tables = panel_tables({"equity": EQUITY, "bonds": BONDS})
    before = {k: [dict(r) for r in v] for k, v in tables.items()}
    weights = {"equity": "0.60", "bonds": "0.40"}
    build_portfolio_path(spec(weights), tables, PORTFOLIO_ID)
    assert tables == before
    assert weights == {"equity": "0.60", "bonds": "0.40"}


# --------------------------------------------------------------------------------------
# Refusals
# --------------------------------------------------------------------------------------


def refuse(weights: dict[str, object], tables: dict[str, list[dict[str, str]]] | None = None) -> None:
    tables = tables or panel_tables({"equity": EQUITY, "bonds": BONDS})
    with pytest.raises(ValueError):
        build_portfolio_path(spec(weights), tables, PORTFOLIO_ID)  # type: ignore[arg-type]


def test_unknown_member_is_refused() -> None:
    refuse({"equity": "0.5", "bonds": "0.3", "gold": "0.2"})


def test_missing_member_is_refused() -> None:
    refuse({"equity": "1"})


def test_negative_weight_is_refused() -> None:
    refuse({"equity": "1.5", "bonds": "-0.5"})
    refuse({"equity": "1", "bonds": "-0"})


def test_weights_not_summing_to_one_are_refused() -> None:
    refuse({"equity": "0.6", "bonds": "0.5"})
    refuse({"equity": "0.6", "bonds": "0.3999999999999999999999999999999999"})


def test_weight_that_is_not_a_decimal_string_is_refused() -> None:
    refuse({"equity": 0.6, "bonds": "0.4"})
    refuse({"equity": "sixty", "bonds": "0.4"})
    refuse({"equity": "NaN", "bonds": "0.4"})
    refuse({"equity": " 0.6", "bonds": "0.4"})


def test_empty_or_missing_weights_are_refused() -> None:
    refuse({})
    with pytest.raises(ValueError):
        build_portfolio_path({"name": "x"}, panel_tables({"equity": EQUITY}), PORTFOLIO_ID)


def test_an_excess_panel_is_refused() -> None:
    refuse(
        {"equity": "0.6", "bonds": "0.4"},
        panel_tables({"equity": EQUITY, "bonds": BONDS}, series_class="excess"),
    )


def test_mismatched_months_are_refused() -> None:
    tables = panel_tables({"equity": EQUITY, "bonds": BONDS})
    for row in tables["fact_panel_return"]:
        if row["member_code"] == "bonds" and row["period_end"] == "2026-03-31":
            row["period_end"] = "2026-03-30"
            break
    refuse({"equity": "0.6", "bonds": "0.4"}, tables)


def test_members_with_different_month_counts_are_refused() -> None:
    tables = panel_tables({"equity": EQUITY, "bonds": BONDS})
    tables["fact_panel_return"] = [
        r
        for r in tables["fact_panel_return"]
        if not (r["member_code"] == "bonds" and r["period_end"] == "2026-04-30")
    ]
    for row in tables["fact_panel_coverage"]:
        if row["member_code"] == "bonds":
            row["months"] = "2"
    refuse({"equity": "0.6", "bonds": "0.4"}, tables)


def test_no_months_are_refused() -> None:
    tables = panel_tables({"equity": EQUITY, "bonds": BONDS})
    tables["fact_panel_return"] = []
    for row in tables["fact_panel_coverage"]:
        row["months"] = "0"
    refuse({"equity": "0.6", "bonds": "0.4"}, tables)


def test_months_that_do_not_join_are_refused() -> None:
    tables = panel_tables({"equity": EQUITY})
    tables["fact_panel_return"][1]["period_start"] = "2026-02-27"
    refuse({"equity": "1"}, tables)


def test_a_return_row_for_a_non_member_is_refused() -> None:
    tables = panel_tables({"equity": EQUITY})
    stray = dict(tables["fact_panel_return"][0])
    stray["member_code"] = "ghost"
    tables["fact_panel_return"].append(stray)
    refuse({"equity": "1"}, tables)


def test_a_return_that_is_not_a_decimal_is_refused() -> None:
    for bad in ("", "abc", "NaN", "Infinity"):
        tables = panel_tables({"equity": EQUITY})
        tables["fact_panel_return"][0]["return"] = bad
        refuse({"equity": "1"}, tables)


def test_coverage_that_disagrees_with_the_returns_is_refused() -> None:
    tables = panel_tables({"equity": EQUITY})
    tables["fact_panel_coverage"][0]["months"] = "5"
    refuse({"equity": "1"}, tables)


def test_missing_panel_table_is_refused() -> None:
    tables = panel_tables({"equity": EQUITY})
    del tables["fact_panel_coverage"]
    refuse({"equity": "1"}, tables)


def test_tables_of_different_panels_are_refused() -> None:
    tables = panel_tables({"equity": EQUITY})
    tables["fact_panel_coverage"][0]["panel_build_id"] = "z" * 64
    refuse({"equity": "1"}, tables)


def test_a_member_with_no_return_rows_is_refused() -> None:
    tables = panel_tables({"equity": EQUITY, "bonds": BONDS})
    tables["fact_panel_return"] = [r for r in tables["fact_panel_return"] if r["member_code"] != "bonds"]
    refuse({"equity": "0.6", "bonds": "0.4"}, tables)


def test_empty_portfolio_build_id_is_refused() -> None:
    with pytest.raises(ValueError):
        build_portfolio_path(spec({"equity": "1"}), panel_tables({"equity": EQUITY}), "")
