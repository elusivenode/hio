"""Portfolio analytics on invented builds (OD-0213). No real data."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import stat
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import portfolio_analytics as pa  # noqa: E402

HEADER = "period_start,period_end,price_return,income_return,total_return,index"


def _days(first: date, count: int, skip: int = 0) -> list[date]:
    out = [first]
    cursor = first
    while len(out) < count + 1:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5:
            out.append(cursor)
    return out[skip:]


def _returns(n: int, amp: float, phase: float) -> list[Decimal]:
    return [Decimal(format(amp * math.sin(phase + 0.7 * k) + 0.0003, ".10f")) for k in range(n)]


def make_build(
    root: Path,
    factor_id: str,
    *,
    amp: float = 0.01,
    phase: float = 0.0,
    first: date = date(2020, 1, 1),
    count: int = 650,
    skip: int = 0,
    series_class: str = "total_return",
    numeraire: str = "USD",
    passed: bool = True,
) -> Path:
    days = _days(first, count)
    rets = _returns(count, amp, phase)
    lines, index = [HEADER], Decimal(1)
    for k, r in enumerate(rets):
        index *= 1 + r
        lines.append(f"{days[k]},{days[k + 1]},{r:f},0.000000,{r:f},{index:f}")
    if skip:
        lines = [lines[0], *lines[1 + skip :]]
    body = ("\n".join(lines) + "\n").encode()
    directory = root / factor_id / "v1" / "b0"
    directory.mkdir(parents=True)
    (directory / "series.csv").write_bytes(body)
    record = {
        "factor_id": factor_id,
        "series_class": series_class,
        "numeraire": numeraire,
        "invariants": {"RA-INV-001": {"checked": count, "passed": passed}},
        "series_sha256": hashlib.sha256(body).hexdigest(),
        "build_id": "0123456789abcdef",
    }
    (directory / "build.json").write_text(json.dumps(record, sort_keys=True, indent=1) + "\n")
    return directory


def _load(*dirs: Path) -> list[dict]:
    return [pa.load_build(d) for d in dirs]


@pytest.fixture
def two(tmp_path: Path) -> tuple[Path, Path]:
    return (
        make_build(tmp_path / "s", "AAA", amp=0.02, phase=0.0),
        make_build(tmp_path / "s", "BBB", amp=0.004, phase=1.3),
    )


def test_one_sleeve_equals_sleeve(two):
    result = pa.analyse(_load(two[0]), {"AAA": 1.0})
    p, s = result["portfolio"], result["sleeves"]["AAA"]
    for key in ("annualised_return", "annualised_volatility"):
        assert p[key] == pytest.approx(s[key], rel=1e-12)
    assert p["drawdown"]["max_drawdown"] == pytest.approx(s["drawdown"]["max_drawdown"], rel=1e-12)
    assert p["worst_month"]["month_end"] == s["worst_month"]["month_end"]
    assert p["compounding_residual"] == pytest.approx(s["sum_of_contributions"] - p["compounded_return"])


def test_sixty_forty_month_return(two):
    result = pa.analyse(_load(*two), {"AAA": 0.6, "BBB": 0.4})
    row = result["monthly"][5]
    expected = 0.6 * row["AAA.return"] + 0.4 * row["BBB.return"]
    assert row["portfolio_return"] == pytest.approx(expected, abs=1e-12)
    assert row["AAA.contribution"] == pytest.approx(0.6 * row["AAA.return"], abs=1e-15)


def test_contributions_sum_every_month(two):
    result = pa.analyse(_load(*two), {"AAA": 0.3, "BBB": 0.7})
    assert result["span"]["months"] == len(result["monthly"]) > 20
    for row in result["monthly"]:
        total = row["AAA.contribution"] + row["BBB.contribution"]
        assert total == pytest.approx(row["portfolio_return"], abs=1e-12)


def test_compounding_residual_reported_not_forced(tmp_path):
    a = make_build(tmp_path / "s", "AAA", amp=0.04)
    b = make_build(tmp_path / "s", "BBB", amp=0.03, phase=2.0)
    result = pa.analyse(_load(a, b), {"AAA": 0.5, "BBB": 0.5})
    p = result["portfolio"]
    assert abs(p["compounding_residual"]) > 1e-6
    assert p["compounding_residual"] == pytest.approx(p["sum_of_contributions"] - p["compounded_return"])


def test_correlation_matrix_and_drawdown_fields(two):
    result = pa.analyse(_load(*two), {"AAA": 0.5, "BBB": 0.5})
    matrix = result["correlation"]["matrix"]
    assert result["correlation"]["order"] == ["AAA", "BBB"]
    assert matrix[0][0] == pytest.approx(1) and matrix[0][1] == pytest.approx(matrix[1][0])
    assert set(result["portfolio"]["drawdown"]) >= {"peak", "trough", "recovery", "max_drawdown"}


def test_excess_return_refused(tmp_path, two):
    ex = make_build(tmp_path / "x", "EXC", series_class="excess_return")
    with pytest.raises(ValueError, match="RA-INV-015"):
        pa.analyse(_load(two[0], ex), {"AAA": 0.5, "EXC": 0.5})


def test_mixed_numeraire_refused(tmp_path, two):
    aud = make_build(tmp_path / "x", "CCC", numeraire="AUD")
    with pytest.raises(ValueError, match="numeraire"):
        pa.analyse(_load(two[0], aud), {"AAA": 0.5, "CCC": 0.5})


def test_tampered_series_refused(two):
    with (two[0] / "series.csv").open("ab") as handle:
        handle.write(b"x")
    with pytest.raises(ValueError, match="sha256"):
        pa.load_build(two[0])


@pytest.mark.parametrize(
    "weights",
    [{"AAA": 0.5, "BBB": 0.4}, {"AAA": 1.0}, {"AAA": 0.5, "BBB": 0.3, "ZZZ": 0.2}, {"AAA": 1.5, "BBB": -0.5}],
)
def test_bad_weights_refused(two, weights):
    with pytest.raises(ValueError):
        pa.analyse(_load(*two), weights)


def test_duplicate_factor_refused(two):
    builds = _load(two[0], two[0])
    with pytest.raises(ValueError, match="distinct"):
        pa.analyse(builds, {"AAA": 1.0})


def test_failed_invariant_refused(tmp_path):
    bad = make_build(tmp_path / "s", "BAD", passed=False)
    with pytest.raises(ValueError, match="invariant"):
        pa.analyse(_load(bad), {"BAD": 1.0})


def test_different_ranges_use_common_dates_only(tmp_path):
    a = make_build(tmp_path / "s", "AAA", count=650)
    b = make_build(tmp_path / "s", "BBB", count=650, skip=100, phase=1.0)
    result = pa.analyse(_load(a, b), {"AAA": 0.5, "BBB": 0.5})
    days = _days(date(2020, 1, 1), 650)
    assert result["span"]["common_first"] == days[100].isoformat()
    assert result["span"]["common_last"] == days[-1].isoformat()
    assert result["omitted_dates"] == {"AAA": 100, "BBB": 0}


def test_gap_inside_a_sleeve_is_not_filled(tmp_path):
    a = make_build(tmp_path / "s", "AAA")
    lines = (a / "series.csv").read_text().splitlines()
    del lines[50]
    body = ("\n".join(lines) + "\n").encode()
    (a / "series.csv").write_bytes(body)
    record = json.loads((a / "build.json").read_text())
    record["series_sha256"] = hashlib.sha256(body).hexdigest()
    (a / "build.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="join"):
        pa.analyse(_load(a), {"AAA": 1.0})


def test_main_outputs_modes_and_no_returns(tmp_path, two, capsys):
    out = tmp_path / "out"
    args = ["--build", str(two[0]), "--build", str(two[1]), "--weight", "AAA=0.6", "--weight", "BBB=0.4"]
    code = pa.main([*args, "--out", str(out)])
    printed = capsys.readouterr().out
    assert code == 0
    lines = printed.splitlines()
    assert len(lines) == 5 and lines[-1] == "contributions reconcile: yes"
    assert "sleeves: 2" in lines
    for name in ("analytics.json", "monthly.csv"):
        data = (out / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() in printed
        assert stat.S_IMODE((out / name).stat().st_mode) == 0o600
    assert stat.S_IMODE(out.stat().st_mode) == 0o700
    analytics = json.loads((out / "analytics.json").read_text())
    assert [i["factor_id"] for i in analytics["inputs"]] == ["AAA", "BBB"]
    assert "monthly" not in analytics
    rows = list(csv.reader((out / "monthly.csv").open()))
    assert rows[0] == [
        "month_end",
        "portfolio_return",
        "AAA.return",
        "AAA.contribution",
        "BBB.return",
        "BBB.contribution",
        "drawdown",
    ]
    assert printed.count("-") == 0  # no dates, no negative returns


def test_main_is_deterministic(tmp_path, two):
    args = ["--build", str(two[0]), "--build", str(two[1]), "--weight", "AAA=0.6", "--weight", "BBB=0.4"]
    pa.main([*args, "--out", str(tmp_path / "o1")])
    pa.main([*args, "--out", str(tmp_path / "o2")])
    for name in ("analytics.json", "monthly.csv"):
        assert (tmp_path / "o1" / name).read_bytes() == (tmp_path / "o2" / name).read_bytes()


def test_out_inside_repository_refused(two, capsys):
    inside = REPO / "portfolio_analytics_test_out"
    code = pa.main(["--build", str(two[0]), "--weight", "AAA=1", "--out", str(inside)])
    assert code == 2
    assert "refused" in capsys.readouterr().err
    assert not inside.exists()


def test_main_refusal_exit_code(two, capsys, tmp_path):
    code = pa.main(["--build", str(two[0]), "--weight", "AAA=0.5", "--out", str(tmp_path / "o")])
    assert code == 2
    assert capsys.readouterr().err.startswith("refused:")
