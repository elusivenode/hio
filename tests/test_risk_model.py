"""Risk model on invented builds (OD-0215). No real data."""

from __future__ import annotations

import hashlib
import json
import math
import stat
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import risk_model as rm  # noqa: E402

TOTAL_HEADER = "period_start,period_end,price_return,income_return,total_return,index"
EXCESS_HEADER = "period_start,period_end,asset_return,cash_return,excess_return"
FIRST, LAST = date(2020, 1, 1), date(2024, 12, 15)


def _days(first: date = FIRST, last: date = LAST) -> list[date]:
    out, cursor = [first], first
    while cursor < last:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5:
            out.append(cursor)
    return out


def sine(amp: float, phase: float):
    def make(days: list[date]) -> list[Decimal]:
        return [
            Decimal(format(amp * math.sin(phase + 0.7 * k) + 0.0003, ".10f")) for k in range(len(days) - 1)
        ]

    return make


def nth_day(sign) -> object:
    """A return only on the n-th weekday (by `sign(month_index)`'s own rule) of each month, else zero."""

    def make(days: list[date]) -> list[Decimal]:
        out, seen = [], {}
        for end in days[1:]:
            key = (end.year, end.month)
            seen[key] = seen.get(key, 0) + 1
            out.append(Decimal(format(sign(end.year * 12 + end.month, seen[key]), ".10f")))
        return out

    return make


def _record(factor_id, series_class, numeraire, passed, body, count):
    return {
        "factor_id": factor_id,
        "series_class": series_class,
        "numeraire": numeraire,
        "invariants": {"RA-INV-001": {"checked": count, "passed": passed}},
        "series_sha256": hashlib.sha256(body).hexdigest(),
        "build_id": "0123456789abcdef",
    }


def _store(root: Path, factor_id: str, body: bytes, record: dict) -> Path:
    directory = root / factor_id / "v1" / "b0"
    directory.mkdir(parents=True)
    (directory / "series.csv").write_bytes(body)
    (directory / "build.json").write_text(json.dumps(record, sort_keys=True, indent=1) + "\n")
    return directory


def make_total(root, factor_id, maker, *, numeraire="USD", passed=True, last=LAST) -> Path:
    days = _days(last=last)
    rets = maker(days)
    lines, index = [TOTAL_HEADER], Decimal(1)
    for k, r in enumerate(rets):
        index *= 1 + r
        lines.append(f"{days[k]},{days[k + 1]},{r:f},0.000000,{r:f},{index:f}")
    body = ("\n".join(lines) + "\n").encode()
    return _store(
        root, factor_id, body, _record(factor_id, "total_return", numeraire, passed, body, len(rets))
    )


def make_excess(root, factor_id, asset_maker, cash_maker, *, numeraire="USD", passed=True) -> Path:
    days = _days()
    assets, cash = asset_maker(days), cash_maker(days)
    lines = [EXCESS_HEADER]
    for k, (a, c) in enumerate(zip(assets, cash, strict=True)):
        lines.append(f"{days[k]},{days[k + 1]},{a:f},{c:f},{a - c:f}")
    body = ("\n".join(lines) + "\n").encode()
    return _store(
        root, factor_id, body, _record(factor_id, "excess_return", numeraire, passed, body, len(assets))
    )


def _load(*dirs):
    return [rm.load_build(d) for d in dirs]


@pytest.fixture
def two(tmp_path):
    return (
        make_total(tmp_path / "s", "AAA", sine(0.02, 0.0)),
        make_total(tmp_path / "s", "BBB", sine(0.004, 1.3)),
    )


def test_euler_percentages_and_sanity_identity(two):
    result = rm.risk(_load(*two), {"AAA": 0.7, "BBB": 0.3}, 36)
    res = result["results"]
    assert sum(res["component_contribution"].values()) == pytest.approx(
        res["portfolio_volatility"], rel=1e-12
    )
    assert sum(res["percentage_contribution"].values()) == pytest.approx(1.0, rel=1e-12)
    sanity = res["sanity_monthly_portfolio_volatility"]
    assert sanity["monthly_portfolio_volatility"] == pytest.approx(res["portfolio_volatility"], rel=1e-12)
    assert res["portfolio_variance"] == pytest.approx(res["portfolio_volatility"] ** 2, rel=1e-12)
    assert res["diversification_ratio"] >= 1 - 1e-12


def test_proportional_sleeves_by_hand(tmp_path):
    # identical returns: correlation 1, sigma_p = (w1 + w2) sigma = sigma, contribution_i = w_i sigma
    a = make_total(tmp_path / "s", "AAA", sine(0.01, 0.4))
    b = make_total(tmp_path / "s", "BBB", sine(0.01, 0.4))
    result = rm.risk(_load(a, b), {"AAA": 0.25, "BBB": 0.75}, 12)["results"]
    sigma = result["volatility"]["AAA"]
    assert result["correlation"]["matrix"][0][1] == pytest.approx(1.0, abs=1e-12)
    assert result["portfolio_volatility"] == pytest.approx(sigma, rel=1e-12)
    assert result["component_contribution"]["AAA"] == pytest.approx(0.25 * sigma, rel=1e-12)
    assert result["component_contribution"]["BBB"] == pytest.approx(0.75 * sigma, rel=1e-12)
    assert result["diversification_ratio"] == pytest.approx(1.0, rel=1e-12)


def test_uncorrelated_closed_form(tmp_path):
    end = date(2024, 10, 10)  # complete months Feb 2020 to Sep 2024: 56, a multiple of 4
    a = make_total(
        tmp_path / "s",
        "AAA",
        nth_day(lambda k, n: (0.04 if k % 2 == 0 else -0.04) if n == 1 else 0),
        last=end,
    )
    b = make_total(
        tmp_path / "s",
        "BBB",
        nth_day(lambda k, n: (0.01 if (k // 2) % 2 == 0 else -0.01) if n == 2 else 0),
        last=end,
    )
    builds = _load(a, b)
    ends = rm.monthly_returns(builds)[1]
    assert len(ends) % 4 == 0
    result = rm.risk(builds, {"AAA": 0.6, "BBB": 0.4}, 12)["results"]
    s1, s2, rho = (
        result["volatility"]["AAA"],
        result["volatility"]["BBB"],
        result["correlation"]["matrix"][0][1],
    )
    assert rho == pytest.approx(0.0, abs=1e-12)
    expected = 0.6**2 * s1**2 + 0.4**2 * s2**2 + 2 * 0.6 * 0.4 * rho * s1 * s2
    assert result["portfolio_variance"] == pytest.approx(expected, rel=1e-12)
    assert s1 == pytest.approx(0.04 * math.sqrt(12 * len(ends) / (len(ends) - 1)), rel=1e-9)


def test_single_sleeve_contribution_is_its_volatility(two):
    res = rm.risk(_load(two[0]), {"AAA": 1.0}, 12)["results"]
    assert res["component_contribution"]["AAA"] == pytest.approx(res["volatility"]["AAA"], rel=1e-12)
    assert res["percentage_contribution"]["AAA"] == pytest.approx(1.0, rel=1e-12)


def test_rolling_rows_and_last_window(two):
    builds = _load(*two)
    weights = {"AAA": 0.7, "BBB": 0.3}
    result = rm.risk(builds, weights, 24)
    months = result["span"]["months"]
    rows = result["rolling"]
    assert len(rows) == months - 24 + 1
    _, ends, _, matrix = rm.monthly_returns(builds)
    last = matrix[-24:]
    assert rows[-1]["month_end"] == ends[-1].isoformat()
    assert rows[-1]["vol"][0] == pytest.approx(np.std(last[:, 0], ddof=1) * math.sqrt(12), rel=1e-12)
    assert rows[-1]["corr"][0, 1] == pytest.approx(np.corrcoef(last[:, 0], last[:, 1])[0, 1], rel=1e-12)
    port = np.std(last @ np.array([0.7, 0.3]), ddof=1) * math.sqrt(12)
    assert rows[-1]["portfolio"] == pytest.approx(port, rel=1e-12)


def test_excess_accepted_with_exposures_and_is_leg_difference(tmp_path):
    cash = sine(0.0, 0.0)  # constant 0.0003 a day
    ea = make_excess(tmp_path / "s", "EA", sine(0.02, 0.0), cash)
    eb = make_excess(tmp_path / "s", "EB", sine(0.005, 1.3), cash)
    result = rm.risk(_load(ea, eb), {"EA": 2.0, "EB": -0.5}, 24)
    res = result["results"]
    assert sum(res["component_contribution"].values()) == pytest.approx(
        res["portfolio_volatility"], rel=1e-12
    )
    assert res["sanity_monthly_portfolio_volatility"] is None
    assert {i["series_class"] for i in result["inputs"]} == {"excess_return"}
    # independent check: the excess month is the asset month less the cash month, each compounded
    asset = make_total(tmp_path / "t", "EA", sine(0.02, 0.0))
    cash_only = make_total(tmp_path / "t", "CASH", cash)
    _, _, _, m_asset = rm.monthly_returns(_load(asset))
    _, _, _, m_cash = rm.monthly_returns(_load(cash_only))
    _, _, _, m_excess = rm.monthly_returns(_load(ea))
    assert m_excess[:, 0] == pytest.approx(m_asset[:, 0] - m_cash[:, 0], abs=1e-12)


def test_total_weights_must_sum_to_one(two):
    with pytest.raises(ValueError, match="sum to 1"):
        rm.risk(_load(*two), {"AAA": 0.5, "BBB": 0.4}, 12)
    with pytest.raises(ValueError, match="not in"):
        rm.risk(_load(*two), {"AAA": 1.5, "BBB": -0.5}, 12)


def test_excess_zero_exposure_refuses(tmp_path):
    cash = sine(0.0, 0.0)
    ea = make_excess(tmp_path / "s", "EA", sine(0.02, 0.0), cash)
    eb = make_excess(tmp_path / "s", "EB", sine(0.005, 1.3), cash)
    with pytest.raises(ValueError, match="zero or not finite"):
        rm.risk(_load(ea, eb), {"EA": 1.0, "EB": 0.0}, 12)
    with pytest.raises(ValueError, match="zero or not finite"):
        rm.risk(_load(ea, eb), {"EA": 1.0, "EB": float("nan")}, 12)


def test_mixed_classes_refuse(tmp_path):
    total = make_total(tmp_path / "s", "AAA", sine(0.02, 0.0))
    excess = make_excess(tmp_path / "s", "EB", sine(0.005, 1.3), sine(0.0, 0.0))
    with pytest.raises(ValueError, match="RA-INV-015"):
        rm.risk(_load(total, excess), {"AAA": 0.5, "EB": 0.5}, 12)


def test_other_refusals(tmp_path, two):
    with pytest.raises(ValueError, match="numeraire"):
        eur = make_total(tmp_path / "e", "CCC", sine(0.01, 0.2), numeraire="EUR")
        rm.risk(_load(two[0], eur), {"AAA": 0.5, "CCC": 0.5}, 12)
    failed = make_total(tmp_path / "f", "DDD", sine(0.01, 0.2), passed=False)
    with pytest.raises(ValueError, match="did not pass"):
        rm.risk(_load(two[0], failed), {"AAA": 0.5, "DDD": 0.5}, 12)
    with pytest.raises(ValueError, match="exactly the builds"):
        rm.risk(_load(*two), {"AAA": 0.5, "ZZZ": 0.5}, 12)
    with pytest.raises(ValueError, match="exactly the builds"):
        rm.risk(_load(*two), {"AAA": 1.0}, 12)
    with pytest.raises(ValueError, match="not distinct"):
        rm.risk(_load(two[0], two[0]), {"AAA": 1.0}, 12)
    with pytest.raises(ValueError, match="window"):
        rm.risk(_load(*two), {"AAA": 0.5, "BBB": 0.5}, 1)


def test_tampered_series_refuses(two):
    path = two[0] / "series.csv"
    path.write_bytes(path.read_bytes().replace(b"0.0", b"0.1", 1))
    with pytest.raises(ValueError, match="sha256"):
        rm.load_build(two[0])


def test_too_short_sample_refuses(two):
    builds = _load(*two)
    months = rm.risk(builds, {"AAA": 0.5, "BBB": 0.5}, 12)["span"]["months"]
    rm.risk(builds, {"AAA": 0.5, "BBB": 0.5}, months - 1)
    with pytest.raises(ValueError, match="window \\+ 1"):
        rm.risk(builds, {"AAA": 0.5, "BBB": 0.5}, months)


def test_out_inside_repository_refuses(two):
    with pytest.raises(ValueError, match="outside the repository"):
        rm.run(list(two), {"AAA": 0.5, "BBB": 0.5}, 12, REPO / "risk_out")
    assert not (REPO / "risk_out").exists()


def test_main_prints_no_return_and_writes_modes(two, tmp_path, capsys):
    out = tmp_path / "out"
    argv = ["--build", str(two[0]), "--build", str(two[1]), "--weight", "AAA=0.7", "--weight", "BBB=0.3"]
    assert rm.main([*argv, "--window", "24", "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    lines = printed.splitlines()
    assert lines[0].startswith("months: ") and lines[1] == "sleeves: 2"
    assert lines[-1] == "risk contributions reconcile: yes"
    assert len(lines) == 6
    counts = "\n".join(lines[:3])  # the hash lines are hex; the rest must hold no date or return
    assert "-" not in counts and "." not in counts
    assert stat.S_IMODE(out.stat().st_mode) == 0o700
    for name in ("risk.json", "rolling.csv"):
        assert stat.S_IMODE((out / name).stat().st_mode) == 0o600
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() in printed
    header = (out / "rolling.csv").read_text().splitlines()[0]
    assert header == "month_end,AAA.volatility,BBB.volatility,AAA|BBB.correlation,portfolio.volatility"
    record = json.loads((out / "risk.json").read_text())
    assert list(record) == sorted(record)
    assert int(lines[2].split(": ")[1]) == record["span"]["months"] - 24 + 1


def test_main_refuses_with_exit_two(two, tmp_path, capsys):
    argv = ["--build", str(two[0]), "--weight", "AAA=0.5", "--out", str(tmp_path / "o")]
    assert rm.main(argv) == 2
    assert capsys.readouterr().err.startswith("refused: ")
