"""The covariance and risk-contribution calculations (gold marts contract §6a, OD-0234).

Invented data only; no files, no git, no network.
"""

from __future__ import annotations

import calendar
import math
import statistics
from collections.abc import Mapping, Sequence

import numpy as np
import pytest

from hio.contracts import gold
from hio.models.risk import build_covariance, build_risk_contribution

BUILD = "a" * 64
RISK = "b" * 64
PORTFOLIO = "c" * 64


def covariance_spec(trailing: int | None = None) -> dict:
    return {
        "name": "t",
        "version": "0.1.0",
        "status": "proposed",
        "kind": "covariance",
        "panel": "t",
        "estimator": "sample",
        "ddof": 1,
        "annualisation": 12,
        "trailing_months": trailing,
        "sha256": "0" * 64,
    }


def risk_spec() -> dict:
    return {
        "name": "t",
        "version": "0.1.0",
        "status": "proposed",
        "kind": "risk_contribution",
        "portfolio": "t",
        "covariance": "t",
        "sha256": "0" * 64,
    }


def month_ends(count: int) -> list[str]:
    """`count + 1` consecutive month-end dates from 2019-12-31; a month runs from one to the next."""
    out = []
    year, month = 2019, 12
    for _ in range(count + 1):
        out.append(f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return out


def panel(returns: Mapping[str, Sequence[object]]) -> dict[str, list[dict[str, str]]]:
    count = len(next(iter(returns.values())))
    ends = month_ends(count)
    rows = []
    for code, values in returns.items():
        for index, value in enumerate(values):
            text = value if isinstance(value, str) else repr(float(value))  # type: ignore[arg-type]
            rows.append(
                {
                    "panel_build_id": "p" * 64,
                    "member_code": code,
                    "period_start": ends[index],
                    "period_end": ends[index + 1],
                    "return": text,
                    "asset_return": "",
                    "cash_return": "",
                }
            )
    return {"fact_panel_return": rows}


def allocation(weights: Mapping[str, str]) -> dict[str, list[dict[str, str]]]:
    return {
        "fact_target_allocation": [
            {"portfolio_build_id": PORTFOLIO, "member_code": code, "target_weight": weight}
            for code, weight in weights.items()
        ]
    }


def index(rows: list[dict[str, str]], *keys: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row[k] for k in keys): row for row in rows}


THREE = {
    "a": [0.01, 0.02, -0.01, 0.03, 0.00],
    "b": [0.02, -0.01, 0.01, 0.00, 0.02],
    "c": [-0.02, 0.01, 0.02, -0.01, 0.01],
}


# ---------------------------------------------------------------------------------- covariance


def test_three_members_five_months_against_statistics() -> None:
    tables = build_covariance(covariance_spec(), panel(THREE), BUILD)
    assert set(tables) == set(gold.TABLES["covariance"])
    cov = index(tables["fact_covariance"], "window_id", "member_i", "member_j")
    vol = index(tables["fact_volatility"], "window_id", "member_code")
    assert len(cov) == 9 and len(vol) == 3
    for i, xs in THREE.items():
        assert float(vol["full", i]["volatility"]) == pytest.approx(
            statistics.stdev(xs) * math.sqrt(12), abs=1e-12
        )
        for j, ys in THREE.items():
            expected = statistics.covariance(xs, ys) * 12
            row = cov["full", i, j]
            assert float(row["covariance"]) == pytest.approx(expected, abs=1e-12)
            assert float(row["correlation"]) == pytest.approx(statistics.correlation(xs, ys), abs=1e-12)
            assert row["covariance_build_id"] == BUILD


def test_hand_checked_two_members() -> None:
    # x = (1, 2, 3), y = (2, 2, 5) as monthly returns: var x = 1, var y = 3, cov = 1.5.
    tables = build_covariance(covariance_spec(), panel({"x": [1.0, 2.0, 3.0], "y": [2.0, 2.0, 5.0]}), BUILD)
    cov = index(tables["fact_covariance"], "window_id", "member_i", "member_j")
    assert float(cov["full", "x", "x"]["covariance"]) == pytest.approx(12.0, abs=1e-12)
    assert float(cov["full", "y", "y"]["covariance"]) == pytest.approx(36.0, abs=1e-12)
    assert float(cov["full", "x", "y"]["covariance"]) == pytest.approx(18.0, abs=1e-12)
    assert float(cov["full", "x", "y"]["correlation"]) == pytest.approx(18.0 / math.sqrt(12 * 36), abs=1e-12)


def test_trailing_windows_ids_spans_and_counts() -> None:
    returns = {"a": [0.01, 0.02, -0.01, 0.03, 0.00, 0.02], "b": [0.02, -0.01, 0.01, 0.00, 0.02, -0.02]}
    tables = build_covariance(covariance_spec(trailing=3), panel(returns), BUILD)
    ends = month_ends(6)
    windows = tables["dim_window"]
    assert [w["window_id"] for w in windows] == ["full"] + [f"trailing:{e}" for e in ends[3:]]
    full = windows[0]
    assert (full["window_kind"], full["first_period_end"], full["last_period_end"], full["n_obs"]) == (
        "full",
        ends[1],
        ends[6],
        "6",
    )
    for offset, window in enumerate(windows[1:]):
        assert window["window_kind"] == "trailing"
        assert window["n_obs"] == "3"
        assert window["first_period_end"] == ends[1 + offset]
        assert window["last_period_end"] == ends[3 + offset]
    # the first trailing window is the first three months
    cov = index(tables["fact_covariance"], "window_id", "member_i", "member_j")
    expected = statistics.covariance(returns["a"][:3], returns["b"][:3]) * 12
    assert float(cov[f"trailing:{ends[3]}", "a", "b"]["covariance"]) == pytest.approx(expected, abs=1e-12)
    assert len(tables["fact_covariance"]) == 5 * 4 and len(tables["fact_volatility"]) == 5 * 2


def test_trailing_null_gives_the_full_window_only() -> None:
    tables = build_covariance(covariance_spec(None), panel(THREE), BUILD)
    assert [w["window_id"] for w in tables["dim_window"]] == ["full"]
    assert {r["window_id"] for r in tables["fact_covariance"]} == {"full"}


def test_trailing_window_as_long_as_the_sample_less_one_is_enough() -> None:
    tables = build_covariance(covariance_spec(trailing=4), panel(THREE), BUILD)
    assert [w["window_kind"] for w in tables["dim_window"]] == ["full", "trailing", "trailing"]


def test_correlation_is_symmetric_with_a_unit_diagonal() -> None:
    tables = build_covariance(covariance_spec(trailing=3), panel(THREE), BUILD)
    cov = index(tables["fact_covariance"], "window_id", "member_i", "member_j")
    for window in {w for w, _, _ in cov}:
        for i in THREE:
            assert float(cov[window, i, i]["correlation"]) == pytest.approx(1.0, abs=1e-12)
            for j in THREE:
                assert cov[window, i, j]["correlation"] == cov[window, j, i]["correlation"]
                assert cov[window, i, j]["covariance"] == cov[window, j, i]["covariance"]
                assert -1 - 1e-12 <= float(cov[window, i, j]["correlation"]) <= 1 + 1e-12


def test_a_single_member_panel_is_one_by_one() -> None:
    tables = build_covariance(covariance_spec(), panel({"only": [0.01, 0.03, 0.02]}), BUILD)
    assert len(tables["fact_covariance"]) == 1
    assert float(tables["fact_covariance"][0]["correlation"]) == pytest.approx(1.0, abs=1e-12)


def test_outputs_are_accepted_by_table_bytes_and_are_text() -> None:
    tables = build_covariance(covariance_spec(trailing=3), panel(THREE), BUILD)
    for name, rows in tables.items():
        data = gold.table_bytes("covariance", name, rows)
        assert gold.parse_table("covariance", name, data)
        for row in rows:
            assert tuple(row) == gold.TABLES["covariance"][name]
            assert all(isinstance(cell, str) for cell in row.values())
    assert all(r["n_obs"].isdigit() for r in tables["dim_window"])
    # a float is the repr of itself
    for row in tables["fact_covariance"]:
        assert repr(float(row["covariance"])) == row["covariance"]


def test_input_order_does_not_change_the_result() -> None:
    forward = panel(THREE)
    reverse = {"fact_panel_return": list(reversed(forward["fact_panel_return"]))}
    assert build_covariance(covariance_spec(trailing=3), forward, BUILD) == build_covariance(
        covariance_spec(trailing=3), reverse, BUILD
    )


def test_covariance_refusals() -> None:
    with pytest.raises(ValueError, match="fewer than 2"):
        build_covariance(covariance_spec(), panel({"a": [0.01], "b": [0.02]}), BUILD)
    with pytest.raises(ValueError, match="fewer than trailing_months"):
        build_covariance(covariance_spec(trailing=5), panel(THREE), BUILD)  # 5 months, needs 6
    with pytest.raises(ValueError, match="constant"):
        build_covariance(covariance_spec(), panel({"a": [0.01, 0.02, 0.03], "b": [0.0, 0.0, 0.0]}), BUILD)
    with pytest.raises(ValueError, match="constant"):
        build_covariance(covariance_spec(), panel({"a": [0.01, 0.02, 0.03], "b": [0.1, 0.1, 0.1]}), BUILD)
    for bad in ("nan", "inf", "-inf", "", "abc", "1_0", " 0.1"):
        with pytest.raises(ValueError, match="not"):
            build_covariance(
                covariance_spec(), panel({"a": [0.01, 0.02, 0.03], "b": [0.01, bad, 0.02]}), BUILD
            )
    with pytest.raises(ValueError, match="no members"):
        build_covariance(covariance_spec(), {"fact_panel_return": []}, BUILD)
    with pytest.raises(ValueError, match="no table"):
        build_covariance(covariance_spec(), {}, BUILD)
    with pytest.raises(ValueError, match="ISO date"):
        rows = panel(THREE)
        rows["fact_panel_return"][0]["period_end"] = "2020-1-31"
        build_covariance(covariance_spec(), rows, BUILD)


def test_a_window_whose_trailing_member_is_constant_is_refused() -> None:
    # constant over the last three months only: the full window is fine, a trailing one is not
    returns = {"a": [0.01, 0.02, -0.01, 0.03, 0.02, 0.01], "b": [0.02, -0.01, 0.01, 0.01, 0.01, 0.01]}
    build_covariance(covariance_spec(), panel(returns), BUILD)
    with pytest.raises(ValueError, match="constant"):
        build_covariance(covariance_spec(trailing=3), panel(returns), BUILD)


def test_mismatched_months_are_refused() -> None:
    short = panel(THREE)
    short["fact_panel_return"] = [
        r
        for r in short["fact_panel_return"]
        if not (r["member_code"] == "c" and r["period_end"].endswith("-03-31"))
    ]
    with pytest.raises(ValueError, match="different months"):
        build_covariance(covariance_spec(), short, BUILD)
    moved = panel(THREE)
    for r in moved["fact_panel_return"]:
        if r["member_code"] == "b" and r["period_start"] == month_ends(5)[0]:
            r["period_start"] = "2019-12-30"
    with pytest.raises(ValueError, match="different months"):
        build_covariance(covariance_spec(), moved, BUILD)
    duplicate = panel(THREE)
    duplicate["fact_panel_return"].append(dict(duplicate["fact_panel_return"][0]))
    with pytest.raises(ValueError, match="more than one return"):
        build_covariance(covariance_spec(), duplicate, BUILD)


def test_covariance_spec_refusals() -> None:
    bad = {**covariance_spec(), "kind": "panel"}
    with pytest.raises(ValueError, match="not a covariance spec"):
        build_covariance(bad, panel(THREE), BUILD)
    with pytest.raises(ValueError, match="ddof 1"):
        build_covariance({**covariance_spec(), "ddof": 0}, panel(THREE), BUILD)
    with pytest.raises(ValueError, match="at least 2"):
        build_covariance(covariance_spec(trailing=1), panel(THREE), BUILD)
    with pytest.raises(ValueError, match="covariance_build_id"):
        build_covariance(covariance_spec(), panel(THREE), "")


# ------------------------------------------------------------------------------ risk contribution


def two_member_covariance() -> dict[str, list[dict[str, str]]]:
    """S = [[0.04, 0.01], [0.01, 0.09]] with volatilities 0.2 and 0.3, one window."""
    rows = [
        ("x", "x", "0.04"),
        ("x", "y", "0.01"),
        ("y", "x", "0.01"),
        ("y", "y", "0.09"),
    ]
    return {
        "dim_window": [
            {
                "covariance_build_id": BUILD,
                "window_id": "full",
                "window_kind": "full",
                "first_period_end": "2020-01-31",
                "last_period_end": "2020-05-31",
                "n_obs": "5",
            }
        ],
        "fact_covariance": [
            {
                "covariance_build_id": BUILD,
                "window_id": "full",
                "member_i": i,
                "member_j": j,
                "covariance": c,
                "correlation": "0.5",
            }
            for i, j, c in rows
        ],
        "fact_volatility": [
            {"covariance_build_id": BUILD, "window_id": "full", "member_code": "x", "volatility": "0.2"},
            {"covariance_build_id": BUILD, "window_id": "full", "member_code": "y", "volatility": "0.3"},
        ],
    }


def test_two_members_by_hand() -> None:
    tables = build_risk_contribution(
        risk_spec(), two_member_covariance(), allocation({"x": "0.6", "y": "0.4"}), RISK
    )
    # Sw = (0.028, 0.042); w'Sw = 0.0336; component = w * Sw / sigma = 0.0168 / sigma for both
    sigma = math.sqrt(0.0336)
    (risk,) = tables["fact_portfolio_risk"]
    assert risk["risk_build_id"] == RISK and risk["window_id"] == "full"
    assert float(risk["portfolio_variance"]) == pytest.approx(0.0336, abs=1e-15)
    assert float(risk["portfolio_volatility"]) == pytest.approx(sigma, abs=1e-15)
    assert float(risk["diversification_ratio"]) == pytest.approx((0.6 * 0.2 + 0.4 * 0.3) / sigma, abs=1e-12)
    assert float(risk["euler_relative_gap"]) < 1e-12
    by_member = index(tables["fact_risk_contribution"], "window_id", "member_code")
    x, y = by_member["full", "x"], by_member["full", "y"]
    assert float(x["weight"]) == 0.6 and float(y["weight"]) == 0.4
    assert float(x["marginal_contribution"]) == pytest.approx(0.028 / sigma, abs=1e-12)
    assert float(y["marginal_contribution"]) == pytest.approx(0.042 / sigma, abs=1e-12)
    assert float(x["component_contribution"]) == pytest.approx(0.0168 / sigma, abs=1e-12)
    assert float(y["component_contribution"]) == pytest.approx(0.0168 / sigma, abs=1e-12)
    assert float(x["percentage_contribution"]) == pytest.approx(0.5, abs=1e-12)
    assert float(y["percentage_contribution"]) == pytest.approx(0.5, abs=1e-12)
    for name, rows in tables.items():
        assert gold.parse_table("risk_contribution", name, gold.table_bytes("risk_contribution", name, rows))


def test_contributions_sum_to_volatility_in_every_window() -> None:
    cov = build_covariance(covariance_spec(trailing=3), panel(THREE), BUILD)
    weights = {"a": "0.5", "b": "0.3", "c": "0.2"}
    tables = build_risk_contribution(risk_spec(), cov, allocation(weights), RISK)
    assert len(tables["fact_portfolio_risk"]) == len(cov["dim_window"]) == 4
    contributions = index(tables["fact_risk_contribution"], "window_id", "member_code")
    for risk in tables["fact_portfolio_risk"]:
        window = risk["window_id"]
        sigma = float(risk["portfolio_volatility"])
        assert sigma > 0
        assert sum(
            float(contributions[window, m]["component_contribution"]) for m in weights
        ) == pytest.approx(sigma, abs=1e-12)
        assert sum(
            float(contributions[window, m]["percentage_contribution"]) for m in weights
        ) == pytest.approx(1.0, abs=1e-12)
        assert float(risk["euler_relative_gap"]) <= 1e-9


def test_a_long_only_portfolio_is_less_risky_than_its_parts() -> None:
    cov = build_covariance(covariance_spec(), panel(THREE), BUILD)
    tables = build_risk_contribution(risk_spec(), cov, allocation({"a": "0.4", "b": "0.3", "c": "0.3"}), RISK)
    assert float(tables["fact_portfolio_risk"][0]["diversification_ratio"]) >= 1.0


def test_a_short_weight_uses_the_absolute_weight_in_the_ratio() -> None:
    tables = build_risk_contribution(
        risk_spec(), two_member_covariance(), allocation({"x": "1.5", "y": "-0.5"}), RISK
    )
    s = np.array([[0.04, 0.01], [0.01, 0.09]])
    w = np.array([1.5, -0.5])
    sigma = math.sqrt(w @ s @ w)
    assert float(tables["fact_portfolio_risk"][0]["diversification_ratio"]) == pytest.approx(
        (1.5 * 0.2 + 0.5 * 0.3) / sigma, abs=1e-12
    )


def test_risk_refusals() -> None:
    cov = two_member_covariance()
    with pytest.raises(ValueError, match="no covariance for \\['z'\\]"):
        build_risk_contribution(risk_spec(), cov, allocation({"x": "0.5", "y": "0.3", "z": "0.2"}), RISK)
    with pytest.raises(ValueError, match="no weight for \\['y'\\]"):
        build_risk_contribution(risk_spec(), cov, allocation({"x": "1"}), RISK)
    with pytest.raises(ValueError, match="not positive"):
        build_risk_contribution(risk_spec(), cov, allocation({"x": "0", "y": "0"}), RISK)
    with pytest.raises(ValueError, match="not finite"):
        build_risk_contribution(risk_spec(), cov, allocation({"x": "nan", "y": "0.5"}), RISK)
    with pytest.raises(ValueError, match="more than one weight"):
        both = allocation({"x": "0.5", "y": "0.5"})
        both["fact_target_allocation"].append(dict(both["fact_target_allocation"][0]))
        build_risk_contribution(risk_spec(), cov, both, RISK)
    with pytest.raises(ValueError, match="not a risk-contribution spec"):
        build_risk_contribution(covariance_spec(), cov, allocation({"x": "0.5", "y": "0.5"}), RISK)
    with pytest.raises(ValueError, match="no table"):
        build_risk_contribution(risk_spec(), cov, {}, RISK)
    with pytest.raises(ValueError, match="no table"):
        build_risk_contribution(risk_spec(), {}, allocation({"x": "1"}), RISK)
    with pytest.raises(ValueError, match="risk_build_id"):
        build_risk_contribution(risk_spec(), cov, allocation({"x": "0.5", "y": "0.5"}), "")


def test_covariance_tables_that_do_not_hold_every_pair_are_refused() -> None:
    cov = two_member_covariance()
    cov["fact_covariance"] = cov["fact_covariance"][:3]
    with pytest.raises(ValueError, match="every ordered pair"):
        build_risk_contribution(risk_spec(), cov, allocation({"x": "0.5", "y": "0.5"}), RISK)
    cov = two_member_covariance()
    cov["fact_volatility"] = cov["fact_volatility"][:1]
    with pytest.raises(ValueError, match="every ordered pair"):
        build_risk_contribution(risk_spec(), cov, allocation({"x": "1"}), RISK)


def test_windows_with_different_members_are_refused() -> None:
    cov = two_member_covariance()
    cov["dim_window"].append(
        {**cov["dim_window"][0], "window_id": "trailing:2020-05-31", "window_kind": "trailing"}
    )
    cov["fact_volatility"].append(
        {
            "covariance_build_id": BUILD,
            "window_id": "trailing:2020-05-31",
            "member_code": "x",
            "volatility": "0.2",
        }
    )
    cov["fact_covariance"].append(
        {
            "covariance_build_id": BUILD,
            "window_id": "trailing:2020-05-31",
            "member_i": "x",
            "member_j": "x",
            "covariance": "0.04",
            "correlation": "1.0",
        }
    )
    with pytest.raises(ValueError, match="different members"):
        build_risk_contribution(risk_spec(), cov, allocation({"x": "0.5", "y": "0.5"}), RISK)


# ------------------------------------------------------------------- independent numpy cross-check


def test_both_functions_agree_with_independent_numpy_formulas() -> None:
    rng = np.random.default_rng(20261122)
    codes = ["bonds", "credit", "equity", "gold"]
    data = rng.normal(0.004, 0.03, size=(20, 4)) + np.array([0.0, 0.01, 0.0, 0.0]) * rng.normal(size=(20, 1))
    trailing = 6
    cov_tables = build_covariance(
        covariance_spec(trailing=trailing),
        panel({code: data[:, k].tolist() for k, code in enumerate(codes)}),
        BUILD,
    )
    ends = month_ends(20)[1:]
    windows = {"full": data} | {
        f"trailing:{ends[t]}": data[t - trailing + 1 : t + 1] for t in range(trailing - 1, 20)
    }
    assert [w["window_id"] for w in cov_tables["dim_window"]] == ["full"] + [
        f"trailing:{e}" for e in ends[trailing - 1 :]
    ]
    cov_rows = index(cov_tables["fact_covariance"], "window_id", "member_i", "member_j")
    vol_rows = index(cov_tables["fact_volatility"], "window_id", "member_code")

    weights = np.array([0.45, 0.15, 0.3, 0.1])
    risk_tables = build_risk_contribution(
        risk_spec(),
        cov_tables,
        allocation({code: repr(float(weights[k])) for k, code in enumerate(codes)}),
        RISK,
    )
    risk_rows = index(risk_tables["fact_portfolio_risk"], "window_id")
    contribution_rows = index(risk_tables["fact_risk_contribution"], "window_id", "member_code")
    assert len(risk_rows) == len(windows)

    for window_id, block in windows.items():
        centred = block - block.mean(axis=0)
        s = centred.T @ centred / (len(block) - 1) * 12
        vol = np.sqrt(np.diagonal(s))
        for i, ci in enumerate(codes):
            assert float(vol_rows[window_id, ci]["volatility"]) == pytest.approx(vol[i], rel=1e-12, abs=1e-14)
            for j, cj in enumerate(codes):
                row = cov_rows[window_id, ci, cj]
                assert float(row["covariance"]) == pytest.approx(s[i, j], rel=1e-12, abs=1e-14)
                assert float(row["correlation"]) == pytest.approx(
                    s[i, j] / (vol[i] * vol[j]), rel=1e-12, abs=1e-14
                )

        variance = float(np.einsum("i,ij,j->", weights, s, weights))
        sigma = math.sqrt(variance)
        sw = np.array([sum(s[i, j] * weights[j] for j in range(4)) for i in range(4)])
        risk = risk_rows[(window_id,)]
        assert float(risk["portfolio_variance"]) == pytest.approx(variance, rel=1e-12)
        assert float(risk["portfolio_volatility"]) == pytest.approx(sigma, rel=1e-12)
        assert float(risk["diversification_ratio"]) == pytest.approx(
            sum(abs(weights[i]) * vol[i] for i in range(4)) / sigma, rel=1e-12
        )
        for i, code in enumerate(codes):
            row = contribution_rows[window_id, code]
            assert float(row["weight"]) == weights[i]
            assert float(row["marginal_contribution"]) == pytest.approx(sw[i] / sigma, rel=1e-12, abs=1e-14)
            assert float(row["component_contribution"]) == pytest.approx(
                weights[i] * sw[i] / sigma, rel=1e-12, abs=1e-14
            )
            assert float(row["percentage_contribution"]) == pytest.approx(
                weights[i] * sw[i] / variance, rel=1e-12, abs=1e-14
            )
