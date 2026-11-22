"""Sleeve comparison on invented builds (OD-0220). No real data."""

from __future__ import annotations

import calendar
import hashlib
import json
import math
import stat
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import sleeve_comparison as sc  # noqa: E402

HEADER = "period_start,period_end,price_return,income_return,total_return,index"
DECOMP_HEADER = "period_start,period_end,foreign_return,spot_return,cross_term,total_return"
REPS = 300


def month_end(i: int) -> date:
    year, month = divmod(2020 * 12 + i, 12)
    return date(year, month + 1, calendar.monthrange(year, month + 1)[1])


def dec(x: float) -> Decimal:
    return Decimal(format(x, ".6f"))


def make_build(
    root: Path,
    factor_id: str,
    returns: list[float] | None = None,
    *,
    fx: tuple[list[float], list[float]] | None = None,
    spot_bias: float = 0.0,
    merge_at: int | None = None,
    series_class: str = "total_return",
    numeraire: str = "AUD",
    passed: bool = True,
) -> Path:
    """One monthly period per return, from the end of a month to the end of the next."""
    if fx is not None:
        foreign, spot = [dec(x) for x in fx[0]], [dec(x) for x in fx[1]]
        totals = [(1 + f) * (1 + s) - 1 for f, s in zip(foreign, spot, strict=True)]
    else:
        assert returns is not None
        totals = [dec(x) for x in returns]
    lines, index = [HEADER], Decimal(1)
    for k, r in enumerate(totals):
        index *= 1 + r
        lines.append(f"{month_end(k)},{month_end(k + 1)},{r:f},0.000000,{r:f},{index:f}")
    body = ("\n".join(lines) + "\n").encode()
    directory = root / factor_id
    directory.mkdir(parents=True)
    (directory / "series.csv").write_bytes(body)
    record = {
        "factor_id": factor_id,
        "series_class": series_class,
        "numeraire": numeraire,
        "invariants": {"RA-INV-001": {"checked": len(totals), "passed": passed}},
        "series_sha256": hashlib.sha256(body).hexdigest(),
        "build_id": "0123456789abcdef",
    }
    if fx is not None:
        rows = list(zip(foreign, spot, totals, strict=True))
        out = [DECOMP_HEADER]
        k = 0
        while k < len(rows):
            f, s, t = rows[k]
            end = k + 1
            if merge_at == k:
                f2, s2, _ = rows[k + 1]
                f, s, t, end = (
                    (1 + f) * (1 + f2) - 1,
                    (1 + s) * (1 + s2) - 1,
                    (1 + t) * (1 + rows[k + 1][2]) - 1,
                    k + 2,
                )
            out.append(f"{month_end(k)},{month_end(end)},{f:f},{s + dec(spot_bias):f},{f * s:f},{t:f}")
            k = end
        dbody = ("\n".join(out) + "\n").encode()
        (directory / "decomposition.csv").write_bytes(dbody)
        record["decomposition_sha256"] = hashlib.sha256(dbody).hexdigest()
    (directory / "build.json").write_text(json.dumps(record, sort_keys=True, indent=1) + "\n")
    return directory


def wave(n: int, amp: float, phase: float, base: float = 0.004) -> list[float]:
    return [round(amp * math.sin(phase + 0.9 * k) + base, 6) for k in range(n)]


N = 27  # periods: 26 kept months
CASH = [round(0.002 + 0.0002 * (k % 3), 6) for k in range(N)]


def load(*dirs: Path) -> list[dict]:
    return [sc.load_build(d) for d in dirs]


def run(tmp_path: Path, sleeves: list[list[float]], ids: list[str], **kw):
    root = tmp_path / "b"
    dirs = [make_build(root, i, r) for i, r in zip(ids, sleeves, strict=True)]
    cash = make_build(root, "CASHX", CASH)
    return sc.compare(load(*dirs), sc.load_build(cash), blocks=(3, 6), replications=REPS, **kw)


def test_hand_computed_three_series(tmp_path):
    n = 25  # 24 kept months
    a = [0.02 if k % 2 == 0 else -0.01 for k in range(n)]
    b = [0.01 - x for x in a]
    root = tmp_path / "b"
    da, db = make_build(root, "AAA", a), make_build(root, "BBB", b)
    dc = make_build(root, "CASHX", [0.002] * n)
    panel = sc.monthly_panel(load(da, db), sc.load_build(dc))
    assert panel["returns"].shape == (24, 3)
    assert list(panel["returns"][:4, 0]) == pytest.approx(a[:4], abs=1e-12)
    assert list(panel["returns"][:4, 1]) == pytest.approx(b[:4], abs=1e-12)

    result = sc.compare(load(da, db), sc.load_build(dc), blocks=(3,), replications=REPS)
    days = (month_end(24) - month_end(0)).days
    annual_a = ((1.02 * 0.99) ** 12) ** (365.25 / days) - 1
    annual_c = (1.002**24) ** (365.25 / days) - 1
    vol_a = 0.015 * math.sqrt(24 / 23) * math.sqrt(12)
    s = result["sleeves"]["AAA"]
    assert s["annualised_return"] == pytest.approx(annual_a, rel=1e-12)
    assert s["annualised_volatility"] == pytest.approx(vol_a, rel=1e-12)
    assert s["drawdown"]["max_drawdown"] == pytest.approx(0.01, abs=1e-9)
    assert s["best_month"]["return"] == pytest.approx(0.02, abs=1e-12)
    assert s["worst_month"]["return"] == pytest.approx(-0.01, abs=1e-12)
    assert result["cash"]["annualised_return"] == pytest.approx(annual_c, rel=1e-12)
    assert result["cash"]["annualised_volatility"] == pytest.approx(0, abs=1e-12)
    # excess: X = 0.018 or -0.012, mean 0.003
    x = s["excess_over_cash"]
    assert x["mean_annual"] == pytest.approx(0.036, abs=1e-12)
    assert x["volatility"] == pytest.approx(vol_a, rel=1e-9)
    assert x["return_difference"] == pytest.approx(annual_a - annual_c, rel=1e-12)
    # pair: B = 0.01 - A, same compounded return, difference alternates by 0.03
    (pair,) = result["pairs"]
    assert pair["correlation"] == pytest.approx(-1, abs=1e-12)
    assert pair["return_difference"] == pytest.approx(0, abs=1e-12)
    assert pair["difference_volatility"] == pytest.approx(0.03 * math.sqrt(24 / 23) * math.sqrt(12), rel=1e-9)


def test_no_chained_excess_index_written(tmp_path):
    result = run(tmp_path, [wave(N, 0.02, 0), wave(N, 0.01, 1)], ["AAA", "BBB"])
    assert not any("excess" in c or "index" in c for c in result["monthly_columns"])
    assert not any("excess" in k for row in result["monthly"] for k in row)
    assert result["monthly_columns"] == ["month_end", "AAA", "BBB", "cash"]


def test_identical_sleeves(tmp_path):
    w = wave(N, 0.02, 0.3)
    result = run(tmp_path, [w, w], ["AAA", "BBB"])
    (pair,) = result["pairs"]
    assert pair["correlation"] == pytest.approx(1, abs=1e-12)
    assert pair["return_difference"] == pytest.approx(0, abs=1e-15)
    for block in ("3", "6"):
        p = result["intervals"][block]["pairs"][0]
        for key in ("volatility_difference", "return_difference", "drawdown_difference"):
            assert p[key]["spans_zero"] is True


def test_constant_premium_does_not_span_zero(tmp_path):
    a = wave(N, 0.02, 0.3)
    result = run(tmp_path, [a, [x + 0.01 for x in a]], ["AAA", "BBB"])
    assert result["pairs"][0]["return_difference"] > 0.05
    for block in ("3", "6"):
        diff = result["intervals"][block]["pairs"][0]["return_difference"]
        assert diff["spans_zero"] is False
        assert diff["low"] > 0


def fx_lists(n: int = N) -> tuple[list[float], list[float]]:
    return wave(n, 0.02, 0.0, 0.003), wave(n, 0.01, 2.0, 0.001)


def fx_case(tmp_path: Path, **kw):
    root = tmp_path / "b"
    fxd = make_build(root, "USEQ", fx=fx_lists(), **kw)
    other = make_build(root, "AUEQ", wave(N, 0.015, 0.5))
    cash = make_build(root, "CASHX", CASH)
    return load(fxd, other), sc.load_build(cash)


def test_currency_identity_and_variance_split(tmp_path):
    sleeves, cash = fx_case(tmp_path)
    result = sc.compare(sleeves, cash, ["USEQ"], blocks=(3,), replications=REPS)
    foreign, spot = fx_lists()
    rows = result["monthly"]
    for k, row in enumerate(rows):
        total = (1 + foreign[k]) * (1 + spot[k]) - 1
        assert row["USEQ"] == pytest.approx(total, abs=1e-12)
        assert row["USEQ.foreign"] == pytest.approx(foreign[k], abs=1e-12)
        assert row["USEQ.spot"] == pytest.approx(spot[k], abs=1e-12)
        assert row["USEQ.cross"] == pytest.approx(foreign[k] * spot[k], abs=1e-12)
    split = result["fx_split"]["USEQ"]
    assert sum(split["variance_split"].values()) == pytest.approx(1, abs=1e-12)
    assert split["max_identity_gap"] < 1e-9
    assert set(split["spot_correlation_with"]) == {"AUEQ"}
    assert result["monthly_columns"][-3:] == ["USEQ.foreign", "USEQ.spot", "USEQ.cross"]


def test_constant_spot_gives_foreign_only(tmp_path):
    root = tmp_path / "b"
    foreign, _ = fx_lists()
    fxd = make_build(root, "USEQ", fx=(foreign, [0.0] * N))
    other = make_build(root, "AUEQ", wave(N, 0.015, 0.5))
    cash = make_build(root, "CASHX", CASH)
    result = sc.compare(load(fxd, other), sc.load_build(cash), ["USEQ"], blocks=(3,), replications=REPS)
    split = result["fx_split"]["USEQ"]
    assert split["variance_split"]["spot"] == 0
    assert split["variance_split"]["covariance"] == 0
    assert split["variance_split"]["foreign"] == pytest.approx(1, abs=1e-12)
    assert abs(split["variance_split"]["remainder"]) < 1e-12
    assert split["correlation_foreign_spot"] is None
    for row in result["monthly"]:
        assert row["USEQ.spot"] == 0
        assert row["USEQ.foreign"] == pytest.approx(row["USEQ"], abs=1e-15)


def test_decomposition_disagreeing_with_series_refuses(tmp_path):
    sleeves, cash = fx_case(tmp_path, spot_bias=0.002)
    with pytest.raises(ValueError, match="differ from the series"):
        sc.compare(sleeves, cash, ["USEQ"], blocks=(3,), replications=REPS)


def test_missing_decomposition_boundary_refuses(tmp_path):
    sleeves, cash = fx_case(tmp_path, merge_at=5)
    with pytest.raises(ValueError, match="not a decomposition boundary"):
        sc.compare(sleeves, cash, ["USEQ"], blocks=(3,), replications=REPS)


def test_tampered_decomposition_refuses(tmp_path):
    sleeves, cash = fx_case(tmp_path)
    path = sleeves[0]["directory"] / "decomposition.csv"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match=r"decomposition\.csv .* sha256"):
        sc.compare(sleeves, cash, ["USEQ"], blocks=(3,), replications=REPS)


def test_split_of_unknown_or_missing_decomposition_refuses(tmp_path):
    sleeves, cash = fx_case(tmp_path)
    with pytest.raises(ValueError, match="not one of the given sleeves"):
        sc.compare(sleeves, cash, ["NOPE"], blocks=(3,), replications=REPS)
    with pytest.raises(ValueError, match=r"no decomposition\.csv"):
        sc.compare(sleeves, cash, ["AUEQ"], blocks=(3,), replications=REPS)


def test_seed_changes_intervals_not_estimates(tmp_path):
    sleeves = [wave(N, 0.02, 0), wave(N, 0.01, 1)]
    one = run(tmp_path, sleeves, ["AAA", "BBB"], seed=1)
    again = run(tmp_path / "again", sleeves, ["AAA", "BBB"], seed=1)
    two = run(tmp_path / "two", sleeves, ["AAA", "BBB"], seed=2)
    assert json.dumps(one, sort_keys=True) == json.dumps(again, sort_keys=True)
    assert one["sleeves"] == two["sleeves"] and one["pairs"] == two["pairs"]
    a, b = one["intervals"]["3"]["sleeves"]["AAA"], two["intervals"]["3"]["sleeves"]["AAA"]
    assert a["volatility"]["estimate"] == b["volatility"]["estimate"]
    assert a["volatility"]["low"] != b["volatility"]["low"]


def _refuses(tmp_path, match, *, a=None, b=None, cash_kw=None, ids=("AAA", "BBB"), n=N, **kw):
    root = tmp_path / "b"
    first = make_build(root, ids[0], wave(n, 0.02, 0), **(a or {}))
    second = make_build(tmp_path / "b2", ids[1], wave(n, 0.01, 1), **(b or {}))
    cash = make_build(root, "CASHX", CASH[:n] if n <= N else CASH, **(cash_kw or {}))
    with pytest.raises(ValueError, match=match):
        sc.compare(load(first, second), sc.load_build(cash), blocks=kw.get("blocks", (3,)), replications=50)


def test_refusals(tmp_path):
    _refuses(tmp_path / "1", "numeraire", b={"numeraire": "USD"})
    _refuses(tmp_path / "2", "numeraire", cash_kw={"numeraire": "USD"})
    _refuses(tmp_path / "3", "RA-INV-015", b={"series_class": "excess_return"})
    _refuses(tmp_path / "4", "invariant", a={"passed": False})
    _refuses(tmp_path / "5", "not distinct", ids=("AAA", "AAA"))
    _refuses(tmp_path / "6", "at least 24", n=20)
    _refuses(tmp_path / "7", "doesn't fit", blocks=(40,))
    _refuses(tmp_path / "8", "doesn't fit", blocks=(0,))


def test_tampered_series_refuses(tmp_path):
    root = tmp_path / "b"
    d = make_build(root, "AAA", wave(N, 0.02, 0))
    path = d / "series.csv"
    path.write_bytes(path.read_bytes().replace(b"0.000000", b"0.000001", 1))
    with pytest.raises(ValueError, match="sha256"):
        sc.load_build(d)


def _args(tmp_path: Path, out: Path, extra: list[str] | None = None):
    root = tmp_path / "b"
    fxd = make_build(root, "USEQ", fx=fx_lists())
    other = make_build(root, "AUEQ", wave(N, 0.015, 0.5))
    cash = make_build(root, "CASHX", CASH)
    return [
        "--sleeve", str(fxd), "--sleeve", str(other), "--cash", str(cash),
        "--fx-split", "USEQ", "--blocks", "3,6", "--replications", "100",
        "--out", str(out), *(extra or []),
    ]  # fmt: skip


def test_out_inside_repository_refuses(tmp_path, capsys):
    target = REPO / "zz_sleeve_comparison_test_out"
    code = sc.main(_args(tmp_path, target))
    assert code == 2
    assert "outside the repository" in capsys.readouterr().err
    assert not target.exists()


def test_command_output_modes_and_determinism(tmp_path, capsys):
    out1, out2 = tmp_path / "o" / "one", tmp_path / "two"
    assert sc.main(_args(tmp_path, out1)) == 0
    stdout = capsys.readouterr().out
    first = {p.name: p.read_bytes() for p in out1.iterdir()}
    assert sc.main(_args(tmp_path / "again", out2)) == 0
    capsys.readouterr()
    assert {p.name: p.read_bytes() for p in out2.iterdir()} == first

    sha = {name: hashlib.sha256(data).hexdigest() for name, data in first.items()}
    assert stdout == (
        "months: 26\n"
        "sleeves: 2\n"
        "split sleeves: 1\n"
        f"comparison.json sha256: {sha['comparison.json']}\n"
        f"monthly.csv sha256: {sha['monthly.csv']}\n"
        "identities hold: yes\n"
    )
    assert stat.S_IMODE(out1.stat().st_mode) == 0o700
    for name in first:
        assert stat.S_IMODE((out1 / name).stat().st_mode) == 0o600
    record = json.loads(first["comparison.json"])
    assert record["span"]["months"] == 26
    assert list(record) == sorted(record)
    header = first["monthly.csv"].decode().splitlines()[0]
    assert header == "month_end,USEQ,AUEQ,cash,USEQ.foreign,USEQ.spot,USEQ.cross"
