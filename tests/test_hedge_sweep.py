"""OD-0217: the hedge-ratio sweep, on invented builds, rates and H.10 XML only. No network, no git."""

import hashlib
import importlib.util
import json
import math
import stat
import sys
from datetime import date
from decimal import Decimal as D
from pathlib import Path

import numpy as np
import pytest

from hio.portfolio import fixed_allocation as fa

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests"))


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


tool = _import("hedge_sweep_under_test", REPO / "tools" / "hedge_sweep.py")
helpers = _import("test_factor_translate_for_hedge_sweep", REPO / "tests" / "test_factor_translate.py")
ft = tool._ft

COMP_ID = "equity.zzz.aud_companion"
Period = tool.Period

# Two boundary dates a month (the 1st and the 15th) for ten months of 2030: eight monthly returns, as the
# first and last periods are dropped.
DATES = [f"2030-{m:02d}-{d:02d}" for m in range(1, 11) for d in (1, 15)]


@pytest.fixture(autouse=True)
def private_tmp(tmp_path):
    tmp_path.chmod(0o700)


def rates_path():
    """USD per AUD: a deterministic wiggle around 0.65."""
    return {
        d: f"{0.65 + 0.04 * math.sin(i * 1.3) + 0.01 * math.cos(i * 0.7):.6f}" for i, d in enumerate(DATES)
    }


def spots(rates):
    q = [D(rates[d]) for d in DATES]
    return [q[i] / q[i + 1] - 1 for i in range(len(q) - 1)]


def rows_from(returns, dates=DATES):
    return [(dates[i], dates[i + 1], f"{r:.8f}", "0") for i, r in enumerate(returns)]


def cash_rows(rate):
    return rows_from([rate] * (len(DATES) - 1))


def make_inputs(tmp_path, asset_returns, *, rates=None, home=0.002, foreign=0.001, companion=None):
    """Write the invented builds and the H.10 archive. Returns the directories and the pin."""
    rates = rates or rates_path()
    paths = {
        "foreign": helpers.write_build(tmp_path, "usd", helpers.USD_ID, rows_from(asset_returns)),
        "home": helpers.write_build(tmp_path, "home", helpers.HOME_ID, cash_rows(home), numeraire="AUD"),
        "fcash": helpers.write_build(tmp_path, "fcash", helpers.FCASH_ID, cash_rows(foreign)),
    }
    if companion is not None:
        paths["companion"] = helpers.write_build(
            tmp_path, "comp", COMP_ID, rows_from(companion), numeraire="AUD"
        )
    h10, sha = helpers.write_h10(tmp_path, rates)
    return paths, h10, sha


def periods_for(tmp_path, asset_returns, **kwargs):
    paths, h10, sha = make_inputs(tmp_path, asset_returns, **kwargs)
    rates, _digest = ft.read_h10(h10, sha)
    legs = [
        ft.load_build(paths["foreign"], role="foreign", numeraire="USD"),
        ft.load_build(paths["home"], role="home", numeraire="AUD"),
        ft.load_build(paths["fcash"], role="fcash", numeraire="USD"),
    ]
    return tool.asset_periods(*legs, rates)


def noise(n, scale):
    return [scale * math.sin(i * 2.1 + 0.4) for i in range(n)]


def opposite_returns(factor, rates=None):
    s = spots(rates or rates_path())
    return [factor * float(x) + n for x, n in zip(s, noise(len(s), 0.002), strict=True)]


def run_tool(tmp_path, paths, h10, sha, out=None, **kwargs):
    return tool.run(
        paths["foreign"], paths["home"], paths["fcash"], h10, sha, out or tmp_path / "out", **kwargs
    )


# ---------------------------------------------------------------------------------------------- identities


HAND = [
    Period("2030-01-01", "2030-01-15", D("0.02"), D("0.25"), D("0.001")),
    Period("2030-01-15", "2030-02-01", D("-0.03"), D("-0.2"), D("-0.002")),
]


def test_the_three_identities_on_hand_computed_periods():
    # period 1: R(0) = 1.02 x 1.25 - 1 = 0.275; R(1) = 0.02 + 0.001 + 0.02 x 0.25 = 0.026
    r0 = tool.hedged_returns(HAND, D(0))
    r1 = tool.hedged_returns(HAND, D(1))
    assert r0[0] == D("0.275") and r1[0] == D("0.026")
    # period 2: R(0) = 0.97 x 0.8 - 1 = -0.224; R(1) = -0.03 - 0.002 + 0.006 = -0.026
    assert r0[1] == D("-0.224") and r1[1] == D("-0.026")
    # R(0.5) = 0.275 - 0.5 (0.25 - 0.001) = 0.1505, and it is also R(0) - 0.5 (R(0) - R(1))
    (half, _) = tool.hedged_returns(HAND, D("0.5"))
    assert half == D("0.1505") == r0[0] - D("0.5") * (r0[0] - r1[0])
    counts = tool.check_identities(HAND, [D(0), D("0.5"), D(2)])
    assert counts == {"periods": 2, "unhedged": 2, "fully_hedged": 2, "linearity": 6}


def test_a_broken_identity_refuses():
    broken = [Period("2030-01-01", "2030-01-15", D("0.02"), D("0.25"), D("0.001"))]
    original = tool._hedged

    def bad(p, h):
        return original(p, h) + (D("1e-6") if h == 1 else 0)

    tool._hedged = bad
    try:
        with pytest.raises(ValueError, match="R_f"):
            tool.check_identities(broken, [D("0.5")])
    finally:
        tool._hedged = original


def test_equal_cash_rates_give_zero_forward_premium_and_fully_hedged_is_rf_plus_rf_s(tmp_path):
    periods = periods_for(tmp_path, opposite_returns(-0.5), home=0.001, foreign=0.001)
    assert all(p.forward_premium == 0 for p in periods)
    for p, r1 in zip(periods, tool.hedged_returns(periods, D(1)), strict=True):
        assert abs(r1 - (p.foreign_return + p.foreign_return * p.spot)) < D("1e-25")


def test_periods_carry_the_quote_convention_and_the_cip_premium(tmp_path):
    rates = rates_path()
    periods = periods_for(tmp_path, opposite_returns(-0.5), rates=rates)
    q = [D(rates[d]) for d in DATES]
    assert len(periods) == len(DATES) - 1
    for i, p in enumerate(periods):
        assert abs(p.spot - (q[i] / q[i + 1] - 1)) < D("1e-20")  # RA-INV-007: q_a / q_b - 1
        assert abs(p.forward_premium - (D("1.002") / D("1.001") - 1)) < D("1e-20")


# ------------------------------------------------------------------------------------- statistics, h*


def test_opposite_moves_make_the_unhedged_series_calmer_and_h_star_low(tmp_path):
    periods = periods_for(tmp_path, opposite_returns(-0.9))
    result = tool.sweep(periods, [D(0), D(1)])
    by = {e["hedge_ratio"]: e["asset"] for e in result["by_ratio"]}
    assert by["0"]["annualised_volatility"] < by["1"]["annualised_volatility"]
    assert result["h_star"]["value"] < 0.5
    assert result["correlation"]["value"] < 1  # a number, described and not asserted further
    assert result["h_star"]["label"] == "in-sample, descriptive: not a recommendation"


def test_moves_together_give_h_star_near_or_above_one(tmp_path):
    periods = periods_for(tmp_path, opposite_returns(0.9))
    result = tool.sweep(periods, [D(0), D(1)])
    by = {e["hedge_ratio"]: e["asset"] for e in result["by_ratio"]}
    assert by["1"]["annualised_volatility"] < by["0"]["annualised_volatility"]
    assert result["h_star"]["value"] > 0.8


def test_h_star_volatility_is_not_above_any_grid_ratio_by_more_than_the_tolerance(tmp_path):
    for factor in (-0.9, 0.9, 0.3):
        sub = tmp_path / str(factor)
        sub.mkdir()
        sub.chmod(0o700)
        periods = periods_for(sub, opposite_returns(factor))
        grid = [D(x) for x in ("-0.5", "0", "0.25", "0.5", "0.75", "1", "1.5")]
        result = tool.sweep(periods, grid)
        star = result["h_star"]
        for entry in result["by_ratio"]:
            assert star["volatility"] <= entry["asset"]["annualised_volatility"] + 1e-9
        assert star["no_grid_ratio_lower_by_more_than_1e-9"] is True
        assert star["gap_to_lowest_grid"] <= 1e-9
        assert star["statistics"]["annualised_volatility"] == star["volatility"]


def test_ratios_outside_zero_one_are_allowed_and_labelled(tmp_path):
    periods = periods_for(tmp_path, opposite_returns(-0.5))
    result = tool.sweep(periods, [D("-0.25"), D("0.5"), D("1.25")])
    labels = {e["hedge_ratio"]: e["label"] for e in result["by_ratio"]}
    assert labels["0.5"] == "within [0, 1]"
    assert labels["-0.25"].startswith("outside [0, 1]") and labels["1.25"].startswith("outside [0, 1]")


def test_ratios_zero_and_one_reproduce_the_factor_translate_series_statistics(tmp_path):
    asset = opposite_returns(-0.6)
    paths, h10, sha = make_inputs(tmp_path, asset)
    spec_u = helpers.write_spec(tmp_path, mode="unhedged")
    spec_path = tmp_path / "spec_unhedged.yaml"
    spec_path.write_bytes(spec_u.read_bytes())
    unhedged = ft.build(spec_path, "unhedged", paths["foreign"], h10, sha, tmp_path / "tr", commit="c" * 40)
    hedged_spec = helpers.write_spec(tmp_path, mode="hedged")
    hedged = ft.build(
        hedged_spec,
        "hedged",
        paths["foreign"],
        h10,
        sha,
        tmp_path / "tr",
        home_cash=paths["home"],
        foreign_cash=paths["fcash"],
        commit="c" * 40,
    )
    result = run_tool(tmp_path, paths, h10, sha, ratios="0,1")
    assert result["ratios"] == 2
    record = json.loads((tmp_path / "out" / "sweep.json").read_text())
    by = {e["hedge_ratio"]: e["asset"] for e in record["by_ratio"]}
    for ratio, built in (("0", unhedged), ("1", hedged)):
        directory = tmp_path / "tr" / helpers.TRANSLATED / "0.1.0" / built["build_id"]
        loaded = ft.load_build(directory, role="translated", numeraire="AUD")
        intervals = [
            fa.Interval(date.fromisoformat(r[0]), date.fromisoformat(r[1]), r[4]) for r in loaded["rows"]
        ]
        panel = fa.align({ASSET: intervals})
        stats, _ = tool._describe(panel, {ASSET: 1.0})
        for key in ("annualised_return", "annualised_volatility", "max_drawdown", "worst_month_return"):
            assert abs(stats[key] - by[ratio][key]) <= 1e-9, (ratio, key)
        for key in ("drawdown_peak", "drawdown_trough", "worst_month"):
            assert stats[key] == by[ratio][key]


ASSET = tool.ASSET


def test_a_portfolio_month_is_the_weighted_sum_of_the_asset_and_companion_months(tmp_path):
    asset = opposite_returns(-0.4)
    companion = [0.004 * math.cos(i) + 0.003 for i in range(len(DATES) - 1)]
    periods = periods_for(tmp_path, asset)
    comp_intervals = [
        fa.Interval(date.fromisoformat(a), date.fromisoformat(b), D(r))
        for (a, b, r, _i) in rows_from(companion)
    ]
    comp = {COMP_ID: (0.4, comp_intervals)}
    h = D("0.5")
    panel = tool._panel(periods, h, comp)
    _stats, monthly = tool._describe(panel, tool._weights(0.6, comp))
    # month k runs between the 15th of month k+1 and the 15th of month k+2 (the first month is dropped):
    # take the second returned month, which spans periods 3 (15 Feb to 1 Mar) and 4 (1 Mar to 15 Mar)
    ra = tool.hedged_returns(periods, h)
    rc = [D(r) for (_a, _b, r, _i) in rows_from(companion)]
    m_a = (1 + ra[3]) * (1 + ra[4]) - 1
    m_c = (1 + rc[3]) * (1 + rc[4]) - 1
    assert abs(float(D("0.6") * m_a + D("0.4") * m_c) - monthly[1]) < 1e-12


def test_the_sweep_runs_with_a_companion_and_writes_both_scopes(tmp_path):
    paths, h10, sha = make_inputs(tmp_path, opposite_returns(-0.4), companion=[0.003] * (len(DATES) - 1))
    summary = run_tool(
        tmp_path, paths, h10, sha, asset_weight="0.6", companions=[(paths["companion"], "0.4")]
    )
    assert summary["companions"] is True and summary["months"] == 8
    record = json.loads((tmp_path / "out" / "sweep.json").read_text())
    assert all("portfolio" in e and "asset" in e for e in record["by_ratio"])
    assert record["weights"][ASSET] == 0.6 and record["identities"]["periods"] == len(DATES) - 1
    lines = (tmp_path / "out" / "sweep.csv").read_text().splitlines()
    assert lines[0] == (
        "hedge_ratio,scope,annualised_return,annualised_volatility,max_drawdown,drawdown_peak,"
        "drawdown_trough,worst_month,worst_month_return"
    )
    assert len(lines) == 1 + 2 * 5
    assert {line.split(",")[1] for line in lines[1:]} == {"asset", "portfolio"}
    roles = [i["role"] for i in record["inputs"]]
    assert roles == ["foreign", "home_cash", "foreign_cash", "companion", "h10"]


# ---------------------------------------------------------------------------------------------- refusals


def test_weights_not_summing_to_one_refuse(tmp_path):
    paths, h10, sha = make_inputs(tmp_path, opposite_returns(-0.4), companion=[0.003] * (len(DATES) - 1))
    with pytest.raises(ValueError, match="sum to 1"):
        run_tool(tmp_path, paths, h10, sha, asset_weight="0.6", companions=[(paths["companion"], "0.3")])
    with pytest.raises(ValueError, match="sum to 1"):
        run_tool(tmp_path, paths, h10, sha, asset_weight="0.5")
    with pytest.raises(ValueError, match="in \\(0, 1\\]"):
        run_tool(tmp_path, paths, h10, sha, asset_weight="1.5", companions=[(paths["companion"], "-0.5")])


def test_a_usd_companion_refuses(tmp_path):
    paths, h10, sha = make_inputs(tmp_path, opposite_returns(-0.4))
    usd = helpers.write_build(tmp_path, "usdcomp", COMP_ID, cash_rows(0.003), numeraire="USD")
    with pytest.raises(ValueError, match="numeraire"):
        run_tool(tmp_path, paths, h10, sha, asset_weight="0.5", companions=[(usd, "0.5")])


def test_an_excess_return_companion_refuses(tmp_path):
    paths, h10, sha = make_inputs(tmp_path, opposite_returns(-0.4), companion=[0.003] * (len(DATES) - 1))
    record_path = paths["companion"] / "build.json"
    record = json.loads(record_path.read_text())
    record["series_class"] = "excess_return"
    record_path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="total_return"):
        run_tool(tmp_path, paths, h10, sha, asset_weight="0.5", companions=[(paths["companion"], "0.5")])


def test_the_foreign_build_must_be_usd_and_the_home_cash_aud(tmp_path):
    paths, h10, sha = make_inputs(tmp_path, opposite_returns(-0.4))
    paths["foreign"] = helpers.write_build(
        tmp_path, "audasset", helpers.USD_ID, rows_from(opposite_returns(-0.4)), numeraire="AUD"
    )
    with pytest.raises(ValueError, match="numeraire"):
        run_tool(tmp_path, paths, h10, sha)


def test_a_tampered_input_and_a_failed_invariant_refuse(tmp_path):
    paths, h10, sha = make_inputs(tmp_path, opposite_returns(-0.4))
    with (paths["fcash"] / "series.csv").open("a") as handle:
        handle.write("2030-10-15,2030-10-16,0,0,0,1\n")
    with pytest.raises(ValueError, match="does not hash"):
        run_tool(tmp_path, paths, h10, sha)
    sub = tmp_path / "second"
    sub.mkdir()
    sub.chmod(0o700)
    paths2, h10b, shab = make_inputs(sub, opposite_returns(-0.4))
    record_path = paths2["home"] / "build.json"
    record = json.loads(record_path.read_text())
    record["invariants"]["RA-INV-001"]["passed"] = False
    record_path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="invariant"):
        run_tool(sub, paths2, h10b, shab)


def test_a_wrong_pin_refuses(tmp_path):
    paths, h10, _sha = make_inputs(tmp_path, opposite_returns(-0.4))
    with pytest.raises(ValueError, match="pin"):
        run_tool(tmp_path, paths, h10, "0" * 64)


def test_out_inside_the_repository_refuses(tmp_path):
    paths, h10, sha = make_inputs(tmp_path, opposite_returns(-0.4))
    inside = REPO / "zz_sweep_out_must_not_exist"
    with pytest.raises(ValueError, match="outside the repository"):
        run_tool(tmp_path, paths, h10, sha, out=inside)
    assert not inside.exists()


@pytest.mark.parametrize("ratios", ["0,nan", "0,inf", "0,x", "0.5,0.5", ""])
def test_bad_ratios_refuse(tmp_path, ratios):
    paths, h10, sha = make_inputs(tmp_path, opposite_returns(-0.4))
    with pytest.raises(ValueError, match="hedge ratio"):
        run_tool(tmp_path, paths, h10, sha, ratios=ratios)


# ---------------------------------------------------------------------------------- command and modes


def cli_args(tmp_path, paths, h10, sha):
    return [
        "--foreign",
        str(paths["foreign"]),
        "--home-cash",
        str(paths["home"]),
        "--foreign-cash",
        str(paths["fcash"]),
        "--h10",
        str(h10),
        "--h10-sha256",
        sha,
        "--out",
        str(tmp_path / "out"),
    ]


def test_command_prints_counts_and_hashes_but_no_number_from_the_data(tmp_path, capsys):
    paths, h10, sha = make_inputs(tmp_path, opposite_returns(-0.4))
    assert tool.main(cli_args(tmp_path, paths, h10, sha)) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    lines = captured.out.splitlines()
    assert lines[0] == "months: 8" and lines[1] == "ratios: 5" and lines[2] == "companions: no"
    assert (
        lines[3]
        == f"sweep.json sha256: {hashlib.sha256((tmp_path / 'out' / 'sweep.json').read_bytes()).hexdigest()}"
    )
    assert (
        lines[4]
        == f"sweep.csv sha256: {hashlib.sha256((tmp_path / 'out' / 'sweep.csv').read_bytes()).hexdigest()}"
    )
    assert lines[5] == "identities hold: yes" and len(lines) == 6
    record = json.loads((tmp_path / "out" / "sweep.json").read_text())
    star = record["h_star"]["value"]
    # the two hash lines are hex digests: a data-like substring can occur in one by chance, so look elsewhere
    text = "\n".join(line for line in lines if "sha256" not in line)
    for secret in ("2030", repr(star)[:6], repr(record["by_ratio"][0]["asset"]["annualised_return"])[:6]):
        assert secret not in text


def test_command_refusal_exits_two(tmp_path, capsys):
    paths, h10, _sha = make_inputs(tmp_path, opposite_returns(-0.4))
    assert tool.main(cli_args(tmp_path, paths, h10, "0" * 64)) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("refused: ValueError")


def test_modes_are_private_and_the_output_is_deterministic(tmp_path):
    paths, h10, sha = make_inputs(tmp_path, opposite_returns(-0.4))
    first = run_tool(tmp_path, paths, h10, sha, out=tmp_path / "a" / "b")
    second = run_tool(tmp_path, paths, h10, sha, out=tmp_path / "c")
    assert (first["sweep_json_sha256"], first["sweep_csv_sha256"]) == (
        second["sweep_json_sha256"],
        second["sweep_csv_sha256"],
    )
    for directory in (tmp_path / "a" / "b", tmp_path / "c"):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        for name in ("sweep.json", "sweep.csv"):
            assert stat.S_IMODE((directory / name).stat().st_mode) == 0o600
    assert stat.S_IMODE((tmp_path / "a").stat().st_mode) == 0o700
    text = (tmp_path / "c" / "sweep.json").read_text()
    assert json.dumps(json.loads(text), sort_keys=True, indent=1) + "\n" == text
    assert np.isfinite(json.loads(text)["h_star"]["value"])
