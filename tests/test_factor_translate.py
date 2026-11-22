"""OD-0216: the USD-to-AUD translation tool, on invented builds, rates and H.10 XML only. No network."""

import hashlib
import importlib
import json
import stat
import sys
import zipfile
from decimal import Decimal as D
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
tool = importlib.import_module("factor_translate")

COMMIT = "c" * 40
USD_ID = "equity.zzz.market_total_return"
HOME_ID = "cash.aud.zzz_reconstructed"
FCASH_ID = "cash.us.zzz_market_total_return"
TRANSLATED = "equity.zzz.aud_total_return"
ONE = D(1)

# USD per AUD. 0.50 -> 0.40 is the AUD weakening: s = 0.50/0.40 - 1 = +0.25 (inverted: -0.20).
RATES = {"2030-01-02": "0.50", "2030-01-03": "0.40", "2030-01-04": "0.50"}
# (start, end, price, income). Period 2 is a distribution period. Period 3 ends on a Sunday.
USD_ROWS = [
    ("2030-01-02", "2030-01-03", "0.01", "0"),
    ("2030-01-03", "2030-01-04", "0.02", "0.005"),
    ("2030-01-04", "2030-01-06", "-0.01", "0"),
]


@pytest.fixture(autouse=True)
def private_tmp(tmp_path):
    tmp_path.chmod(0o700)


def write_build(tmp_path, name, factor_id, rows, *, numeraire="USD", passed=True):
    directory = tmp_path / "builds" / name
    directory.mkdir(parents=True)
    lines = ["period_start,period_end,price_return,income_return,total_return,index\n"]
    level = ONE
    for start, end, pr, ir in rows:
        tr = D(pr) + D(ir)
        level *= 1 + tr
        lines.append(f"{start},{end},{pr},{ir},{tr},{level}\n")
    data = "".join(lines).encode()
    (directory / "series.csv").write_bytes(data)
    record = {
        "factor_id": factor_id,
        "series_class": "total_return",
        "numeraire": numeraire,
        "invariants": {"RA-INV-001": {"checked": len(rows), "passed": passed}},
        "series_sha256": hashlib.sha256(data).hexdigest(),
        "build_id": hashlib.sha256(name.encode()).hexdigest()[:16],
    }
    (directory / "build.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return directory


def write_h10(tmp_path, rates=RATES, name="FRB_h10_xml.zip"):
    cells = "".join(f'<k:Obs TIME_PERIOD="{d}" OBS_VALUE="{v}"/>' for d, v in rates.items())
    xml = (
        '<m xmlns:k="urn:k"><k:Series SERIES_NAME="OTHER"><k:Obs TIME_PERIOD="2030-01-02" OBS_VALUE="9"/>'
        f'</k:Series><k:Series SERIES_NAME="RXI$US_N.B.AL">{cells}</k:Series></m>'
    )
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("H10_data.xml", xml)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def spec_text(
    *,
    mode="unhedged",
    series_class="total_return",
    numeraire="AUD",
    hedging=None,
    ids=None,
):
    if hedging is None:
        hedging = "unhedged" if mode == "unhedged" else "hedged, h = 1, reset every period (RA 4.3)"
    if ids is None:
        ids = [USD_ID, "frb_h10.aud_usd.noon_new_york"] + ([HOME_ID, FCASH_ID] if mode == "hedged" else [])
    obs = "".join(f"  - series_id: {i}\n    source_id: invented.source\n" for i in ids)
    return f"""identity:
  factor_id: {TRANSLATED}
  version: 0.1.0
classification:
  series_class: {series_class}
  investability: replicable_with_basis
return_convention:
  numeraire: {numeraire}
  hedging: "{hedging}"
observations:
{obs}"""


def write_spec(tmp_path, **kwargs):
    path = tmp_path / "spec.yaml"
    path.write_text(spec_text(**kwargs))
    return path


def unhedged(tmp_path, rows=USD_ROWS, rates=RATES, out=None, **spec_kwargs):
    foreign = write_build(tmp_path, "usd", USD_ID, rows)
    h10, sha = write_h10(tmp_path, rates)
    out = out or tmp_path / "out"
    return tool.build(
        write_spec(tmp_path, **spec_kwargs), "unhedged", foreign, h10, sha, out, commit=COMMIT
    ), out


def hedged(tmp_path, usd, home, fcash, rates=RATES, out=None):
    paths = [
        write_build(tmp_path, "usd", USD_ID, usd),
        write_build(tmp_path, "home", HOME_ID, home, numeraire="AUD"),
        write_build(tmp_path, "fcash", FCASH_ID, fcash),
    ]
    h10, sha = write_h10(tmp_path, rates)
    out = out or tmp_path / "out"
    spec = write_spec(tmp_path, mode="hedged")
    record = tool.build(
        spec, "hedged", paths[0], h10, sha, out, home_cash=paths[1], foreign_cash=paths[2], commit=COMMIT
    )
    return record, out


def target(out, record):
    return out / TRANSLATED / "0.1.0" / record["build_id"]


def table(directory, name):
    lines = (directory / name).read_text().splitlines()
    head = lines[0].split(",")
    return [dict(zip(head, (c for c in line.split(",")), strict=True)) for line in lines[1:]]


def close(a, b, tol="1e-20"):
    return abs(D(a) - D(b)) <= D(tol)


# ----------------------------------------------------------------------------------------------- unhedged


def test_unhedged_three_periods_by_hand_including_a_distribution(tmp_path):
    record, out = unhedged(tmp_path)
    series = table(target(out, record), "series.csv")
    # s = 0.25, -0.2, 0 (the Sunday end uses Friday's rate)
    assert [D(r["price_return"]) for r in series] == [D("0.2625"), D("-0.184"), D("-0.01")]
    assert [D(r["income_return"]) for r in series] == [D("0"), D("0.004"), D("0")]  # 0.005 x (1 - 0.2)
    assert [D(r["total_return"]) for r in series] == [D("0.2625"), D("-0.18"), D("-0.01")]
    assert [D(r["index"]) for r in series] == [D("1.2625"), D("1.03525"), D("1.0248975")]
    for r in series:
        assert D(r["total_return"]) == D(r["price_return"]) + D(r["income_return"])
    assert [(r["period_start"], r["period_end"]) for r in series] == [(a, b) for a, b, _p, _i in USD_ROWS]


def test_unhedged_decomposition_and_cross_term(tmp_path):
    record, out = unhedged(tmp_path)
    directory = target(out, record)
    head = (directory / "decomposition.csv").read_text().splitlines()[0]
    assert head == "period_start,period_end,foreign_return,spot_return,cross_term,total_return"
    rows = table(directory, "decomposition.csv")
    assert [D(r["foreign_return"]) for r in rows] == [D("0.01"), D("0.025"), D("-0.01")]
    assert [D(r["spot_return"]) for r in rows] == [D("0.25"), D("-0.2"), D("0")]
    for r in rows:
        f, s, x, t = (D(r[k]) for k in ("foreign_return", "spot_return", "cross_term", "total_return"))
        assert x == f * s
        assert t == f + s + x
        assert 1 + t == (1 + f) * (1 + s)
    assert record["invariants"]["RA-INV-006"] == {"checked": 3, "passed": True}


def test_series_format_is_exact(tmp_path):
    record, out = unhedged(tmp_path)
    directory = target(out, record)
    data = (directory / "series.csv").read_bytes()
    assert data.startswith(b"period_start,period_end,price_return,income_return,total_return,index\n")
    assert b"\r" not in data and b"e-" not in data.lower() and b"E+" not in data
    assert hashlib.sha256(data).hexdigest() == record["series_sha256"]
    on_disk = json.loads((directory / "build.json").read_text())
    assert on_disk == record
    assert (directory / "build.json").read_text() == json.dumps(record, indent=1, sort_keys=True) + "\n"
    required = {"factor_id", "spec_version", "spec_sha256", "series_class", "numeraire", "code_commit"}
    required |= {"periods", "first", "last", "invariants", "series_sha256", "build_id", "inputs", "mode"}
    required |= {"periods_after_fx", "fx_dates", "investability"}
    assert required <= set(record)
    assert record["series_class"] == "total_return" and record["numeraire"] == "AUD"
    assert record["mode"] == "unhedged" and record["investability"] == "replicable_with_basis"
    assert (record["periods"], record["first"], record["last"]) == (3, "2030-01-02", "2030-01-06")
    assert all(v["passed"] for v in record["invariants"].values())
    assert {"RA-INV-001", "index_chain", "RA-INV-006", "RA-INV-007", "fx_dates"} <= set(record["invariants"])
    roles = {i["role"]: i for i in record["inputs"]}
    assert roles["foreign"]["factor_id"] == USD_ID and "series_sha256" in roles["foreign"]
    assert roles["h10"]["sha256"] == hashlib.sha256((tmp_path / "FRB_h10_xml.zip").read_bytes()).hexdigest()


def test_weaker_aud_gives_positive_s_and_the_inverted_formula_would_not(tmp_path):
    record, out = unhedged(tmp_path)
    first = table(target(out, record), "decomposition.csv")[0]
    q_then, q_now = D("0.50"), D("0.40")  # USD per AUD falls: AUD weakens
    s = D(first["spot_return"])
    assert s == q_then / q_now - 1 > 0
    assert (q_now / q_then - 1) < 0  # the inverted formula has the wrong sign (RA-INV-007)
    assert D(first["total_return"]) > D(first["foreign_return"])
    assert tool._spot(q_then, q_now) == s


def test_a_weekend_end_uses_the_earlier_rate_and_is_counted(tmp_path):
    record, _out = unhedged(tmp_path)
    # boundary dates 02, 03, 04 have rates; 06 (Sunday) uses 04's, two days old
    assert record["fx_dates"] == {"on_the_day": 3, "before_the_day": 1}
    assert record["periods_after_fx"] == 0


def test_periods_after_the_last_rate_are_dropped_and_counted(tmp_path):
    rows = [*USD_ROWS, ("2030-01-06", "2030-01-15", "0.01", "0"), ("2030-01-15", "2030-01-16", "0.01", "0")]
    record, out = unhedged(tmp_path, rows=rows)
    assert record["periods"] == 3 and record["periods_after_fx"] == 2
    assert record["last"] == "2030-01-06"
    assert len(table(target(out, record), "series.csv")) == 3


def test_a_stale_rate_inside_the_span_refuses(tmp_path):
    rates = {"2030-01-02": "0.5", "2030-01-03": "0.4", "2030-01-04": "0.5", "2030-01-15": "0.5"}
    rows = [("2030-01-02", "2030-01-03", "0.01", "0"), ("2030-01-03", "2030-01-12", "0.01", "0")]
    with pytest.raises(ValueError, match="days old"):
        unhedged(tmp_path, rows=rows, rates=rates)


def test_no_usable_rate_at_all_refuses(tmp_path):
    with pytest.raises(ValueError):
        unhedged(tmp_path, rows=[("2031-01-02", "2031-01-03", "0.01", "0")])


# ------------------------------------------------------------------------------------------------ hedged

CASH_H = [("2030-01-02", "2030-01-03", "0", "0.001"), ("2030-01-03", "2030-01-04", "0", "0.002")]
CASH_F = [("2030-01-02", "2030-01-03", "0", "0.0005"), ("2030-01-03", "2030-01-04", "0", "0.0005")]
USD_TWO = [("2030-01-02", "2030-01-03", "0.01", "0"), ("2030-01-03", "2030-01-04", "0.02", "0")]


def expected_hedged(big_r, rh, rf, s):
    f = (1 + D(rh)) / (1 + D(rf)) - 1
    return D(big_r) + f + D(big_r) * D(s), f


def test_hedged_two_periods_by_hand(tmp_path):
    record, out = hedged(tmp_path, USD_TWO, CASH_H, CASH_F)
    directory = target(out, record)
    series = table(directory, "series.csv")
    for row, (big_r, rh, rf, s) in zip(
        series, [("0.01", "0.001", "0.0005", "0.25"), ("0.02", "0.002", "0.0005", "-0.2")], strict=True
    ):
        total, _f = expected_hedged(big_r, rh, rf, s)
        assert close(row["total_return"], total)
        assert row["price_return"] == row["total_return"] and row["income_return"] == "0"
    level = ONE
    for row in series:
        level *= 1 + D(row["total_return"])
        assert close(row["index"], level)
    head = (directory / "decomposition.csv").read_text().splitlines()[0]
    assert head == (
        "period_start,period_end,foreign_return,spot_return,forward_premium,cross_term,hedge_payoff,total_return"
    )
    rows = table(directory, "decomposition.csv")
    for r in rows:
        big_r, s, f, x, payoff, total = (
            D(r[k])
            for k in (
                "foreign_return",
                "spot_return",
                "forward_premium",
                "cross_term",
                "hedge_payoff",
                "total_return",
            )
        )
        assert x == big_r * s and close(payoff, -(s - f))
        assert close(total, (1 + big_r) * (1 + s) - 1 - (s - f))  # RA-INV-009
    assert record["mode"] == "hedged" and record["periods"] == 2
    assert all(v["passed"] for v in record["invariants"].values())
    assert {"RA-INV-009", "alignment", "cip_forward"} <= set(record["invariants"])
    roles = [i["role"] for i in record["inputs"]]
    assert roles == ["foreign", "home_cash", "foreign_cash", "h10"]


def test_hedged_equal_cash_rates_has_zero_forward_premium(tmp_path):
    equal = [("2030-01-02", "2030-01-03", "0", "0.001"), ("2030-01-03", "2030-01-04", "0", "0.001")]
    record, out = hedged(tmp_path, USD_TWO, equal, equal)
    directory = target(out, record)
    rows = table(directory, "decomposition.csv")
    assert [D(r["forward_premium"]) for r in rows] == [0, 0]
    for series, dec in zip(table(directory, "series.csv"), rows, strict=True):
        big_r, s = D(dec["foreign_return"]), D(dec["spot_return"])
        assert D(series["total_return"]) == big_r + big_r * s


def test_hedged_with_zero_foreign_return_is_the_forward_premium(tmp_path):
    zero = [("2030-01-02", "2030-01-03", "0", "0"), ("2030-01-03", "2030-01-04", "0", "0")]
    record, out = hedged(tmp_path, zero, CASH_H, CASH_F)
    directory = target(out, record)
    for series, dec in zip(
        table(directory, "series.csv"), table(directory, "decomposition.csv"), strict=True
    ):
        assert D(series["total_return"]) == D(dec["forward_premium"])
        assert D(dec["cross_term"]) == 0
    assert close(table(directory, "series.csv")[0]["total_return"], D("1.001") / D("1.0005") - 1)


def test_hedged_compounds_each_build_between_common_dates(tmp_path):
    # the home cash build has no 03 boundary, so 03 is not common: the USD build compounds across it
    home = [("2030-01-02", "2030-01-04", "0", "0.003")]
    record, out = hedged(tmp_path, USD_TWO, home, CASH_F)
    (row,) = table(target(out, record), "decomposition.csv")
    big_r = D("1.01") * D("1.02") - 1
    assert close(row["foreign_return"], big_r)
    s = D("0.5") / D("0.5") - 1
    total, _f = expected_hedged(big_r, "0.003", D("1.0005") * D("1.0005") - 1, s)
    assert close(row["total_return"], total)
    assert record["periods"] == 1
    assert record["invariants"]["alignment"]["passed"]


def test_a_date_without_a_fresh_rate_is_not_a_common_date(tmp_path):
    rates = {"2030-01-02": "0.5", "2030-01-10": "0.5"}
    usd = [("2030-01-02", "2030-01-06", "0.01", "0"), ("2030-01-06", "2030-01-10", "0.01", "0")]
    home = [("2030-01-02", "2030-01-06", "0", "0.001"), ("2030-01-06", "2030-01-10", "0", "0.001")]
    fcash = [("2030-01-02", "2030-01-06", "0", "0.001"), ("2030-01-06", "2030-01-10", "0", "0.001")]
    record, _out = hedged(tmp_path, usd, home, fcash, rates=rates)
    assert record["periods"] == 2  # 06 has a rate 4 days old: fresh, so common
    rates2 = {"2030-01-02": "0.5", "2030-01-12": "0.5"}
    usd2 = [("2030-01-02", "2030-01-08", "0.01", "0"), ("2030-01-08", "2030-01-12", "0.01", "0")]
    cash2 = [("2030-01-02", "2030-01-08", "0", "0.001"), ("2030-01-08", "2030-01-12", "0", "0.001")]
    sub = tmp_path / "second"
    sub.mkdir()
    sub.chmod(0o700)
    record2, out2 = hedged(sub, usd2, cash2, cash2, rates=rates2)
    assert record2["periods"] == 1  # 08 is six days after the last earlier rate: not common
    assert (record2["first"], record2["last"]) == ("2030-01-02", "2030-01-12")
    assert target(out2, record2).is_dir()


def test_hedged_fixtures_of_the_standard_through_the_same_code_path():
    # (a) S0 = S_T = 1, r_h = 10%, r_f = 0, F = 1.1
    s0, s_t = D(1), D(1)
    f = tool.forward_premium(1 / s0, D("0.1"), D(0))
    forward = s0 * (1 + f)
    assert close(forward, "1.1", "1e-25")
    assert close((1 + D("0.1")) * (s_t / forward - 1), "-0.1", "1e-25")
    assert close(s_t / forward - 1, "-0.0909090909090909090909", "1e-20")
    # (b)
    s0, s_t = D("1.5385"), D("1.5000")
    r_h, r_f = D("0.036") * 30 / 365, D("0.043") * 30 / 360
    f = tool.forward_premium(1 / s0, r_h, r_f)
    forward = s0 * (1 + f)
    assert close(forward, "1.5375427458", "1e-10")
    assert close(s_t / forward - 1, "-0.024417367194", "1e-11")
    assert close((1 + r_h) * (s_t / forward - 1), "-0.024489615842", "1e-11")
    # f is the quote-level-free premium (1 + r_h)/(1 + r_f) - 1
    assert close(f, (1 + r_h) / (1 + r_f) - 1, "1e-25")


# ----------------------------------------------------------------------------------------------- refusals


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"series_class": "excess_return"}, "series_class"),
        ({"numeraire": "USD"}, "numeraire"),
        ({"hedging": "hedged, h = 1"}, "but --mode"),
        ({"hedging": "partly"}, "hedging"),
        ({"ids": ["something.else"]}, "observations"),
    ],
)
def test_unhedged_spec_refusals(tmp_path, kwargs, message):
    with pytest.raises(ValueError, match=message):
        unhedged(tmp_path, **kwargs)


def test_hedged_spec_with_unhedged_mode_and_the_reverse_refuse(tmp_path):
    foreign = write_build(tmp_path, "usd", USD_ID, USD_ROWS)
    h10, sha = write_h10(tmp_path)
    with pytest.raises(ValueError, match="but --mode"):
        tool.build(
            write_spec(tmp_path, mode="hedged"), "unhedged", foreign, h10, sha, tmp_path / "o", commit=COMMIT
        )
    with pytest.raises(ValueError, match="but --mode"):
        tool.build(write_spec(tmp_path), "hedged", foreign, h10, sha, tmp_path / "o", commit=COMMIT)


def test_hedged_spec_must_name_both_cash_builds(tmp_path):
    paths = [
        write_build(tmp_path, "usd", USD_ID, USD_TWO),
        write_build(tmp_path, "home", HOME_ID, CASH_H, numeraire="AUD"),
        write_build(tmp_path, "fcash", FCASH_ID, CASH_F),
    ]
    h10, sha = write_h10(tmp_path)
    spec = write_spec(tmp_path, mode="hedged", ids=[USD_ID, HOME_ID])
    with pytest.raises(ValueError, match="observations"):
        tool.build(
            spec,
            "hedged",
            paths[0],
            h10,
            sha,
            tmp_path / "o",
            home_cash=paths[1],
            foreign_cash=paths[2],
            commit=COMMIT,
        )


def test_cash_builds_are_required_for_hedged_and_refused_for_unhedged(tmp_path):
    foreign = write_build(tmp_path, "usd", USD_ID, USD_ROWS)
    h10, sha = write_h10(tmp_path)
    with pytest.raises(ValueError, match="needs"):
        tool.build(
            write_spec(tmp_path, mode="hedged"), "hedged", foreign, h10, sha, tmp_path / "o", commit=COMMIT
        )
    with pytest.raises(ValueError, match="no cash"):
        tool.build(
            write_spec(tmp_path),
            "unhedged",
            foreign,
            h10,
            sha,
            tmp_path / "o",
            home_cash=foreign,
            commit=COMMIT,
        )


@pytest.mark.parametrize("which", ["usd", "home", "fcash"])
def test_wrong_numeraires_refuse(tmp_path, which):
    numeraires = {"usd": "USD", "home": "AUD", "fcash": "USD"}
    numeraires[which] = "AUD" if numeraires[which] == "USD" else "USD"
    paths = [
        write_build(tmp_path, "usd", USD_ID, USD_TWO, numeraire=numeraires["usd"]),
        write_build(tmp_path, "home", HOME_ID, CASH_H, numeraire=numeraires["home"]),
        write_build(tmp_path, "fcash", FCASH_ID, CASH_F, numeraire=numeraires["fcash"]),
    ]
    h10, sha = write_h10(tmp_path)
    with pytest.raises(ValueError, match="numeraire"):
        tool.build(
            write_spec(tmp_path, mode="hedged"),
            "hedged",
            paths[0],
            h10,
            sha,
            tmp_path / "o",
            home_cash=paths[1],
            foreign_cash=paths[2],
            commit=COMMIT,
        )


def test_a_tampered_input_refuses(tmp_path):
    foreign = write_build(tmp_path, "usd", USD_ID, USD_ROWS)
    with (foreign / "series.csv").open("a") as handle:
        handle.write("2030-01-06,2030-01-07,0,0,0,1\n")
    h10, sha = write_h10(tmp_path)
    with pytest.raises(ValueError, match="does not hash"):
        tool.build(write_spec(tmp_path), "unhedged", foreign, h10, sha, tmp_path / "o", commit=COMMIT)


def test_a_failed_invariant_in_an_input_refuses(tmp_path):
    foreign = write_build(tmp_path, "usd", USD_ID, USD_ROWS, passed=False)
    h10, sha = write_h10(tmp_path)
    with pytest.raises(ValueError, match="invariant"):
        tool.build(write_spec(tmp_path), "unhedged", foreign, h10, sha, tmp_path / "o", commit=COMMIT)


def test_a_wrong_pin_and_a_tampered_h10_refuse(tmp_path):
    foreign = write_build(tmp_path, "usd", USD_ID, USD_ROWS)
    h10, sha = write_h10(tmp_path)
    with pytest.raises(ValueError, match="pin"):
        tool.build(write_spec(tmp_path), "unhedged", foreign, h10, "0" * 64, tmp_path / "o", commit=COMMIT)
    h10.write_bytes(h10.read_bytes() + b"x")
    with pytest.raises(ValueError, match="pin"):
        tool.build(write_spec(tmp_path), "unhedged", foreign, h10, sha, tmp_path / "o", commit=COMMIT)


def test_an_h10_file_that_is_not_the_archive_refuses(tmp_path):
    foreign = write_build(tmp_path, "usd", USD_ID, USD_ROWS)
    bogus = tmp_path / "bogus.zip"
    bogus.write_bytes(b"not a zip")
    with pytest.raises(ValueError, match="zip"):
        tool.build(
            write_spec(tmp_path),
            "unhedged",
            foreign,
            bogus,
            hashlib.sha256(b"not a zip").hexdigest(),
            tmp_path / "o",
            commit=COMMIT,
        )


def test_out_inside_the_repository_refuses(tmp_path):
    inside = REPO / "zz_translate_out_must_not_exist"
    with pytest.raises(ValueError, match="outside the repository"):
        unhedged(tmp_path, out=inside)
    assert not inside.exists()


# ------------------------------------------------------------------------- determinism, modes, command


def test_a_second_build_is_identical_and_already_built(tmp_path):
    record, out = unhedged(tmp_path)
    directory = target(out, record)
    before = {n: (directory / n).read_bytes() for n in ("series.csv", "decomposition.csv", "build.json")}
    _record, existed = tool._build(
        tmp_path / "spec.yaml",
        "unhedged",
        tmp_path / "builds" / "usd",
        tmp_path / "FRB_h10_xml.zip",
        record["inputs"][-1]["sha256"],
        out,
        None,
        None,
        COMMIT,
    )
    assert existed
    assert before == {n: (directory / n).read_bytes() for n in before}
    expected = hashlib.sha256(
        (
            record["spec_sha256"]
            + record["inputs"][0]["series_sha256"]
            + record["inputs"][-1]["sha256"]
            + "unhedged"
            + COMMIT
        ).encode()
    ).hexdigest()[:16]
    assert record["build_id"] == expected


def test_modes_are_private(tmp_path):
    record, out = unhedged(tmp_path)
    directory = target(out, record)
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    for parent in (directory.parent, directory.parent.parent):
        assert stat.S_IMODE(parent.stat().st_mode) == 0o700
    for name in ("series.csv", "decomposition.csv", "build.json"):
        assert stat.S_IMODE((directory / name).stat().st_mode) == 0o600


def run_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tool._fb._base, "code_commit", lambda: {"commit": COMMIT})
    foreign = write_build(tmp_path, "usd", USD_ID, USD_ROWS)
    h10, sha = write_h10(tmp_path)
    args = [
        "--spec",
        str(write_spec(tmp_path)),
        "--mode",
        "unhedged",
        "--foreign",
        str(foreign),
        "--h10",
        str(h10),
        "--h10-sha256",
        sha,
        "--out",
        str(tmp_path / "out"),
    ]
    code = tool.main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_command_prints_no_return_rate_or_date(tmp_path, monkeypatch, capsys):
    code, out, err = run_cli(tmp_path, monkeypatch, capsys)
    assert code == 0 and err == ""
    for secret in ("2030", "0.25", "0.2625", "0.0025", "1.2625", "0.50", "0.40", "0.01"):
        assert secret not in out
    assert "build_id:" in out and "series_sha256:" in out and "RA-INV-006: pass (3 checked)" in out


def test_command_second_run_says_already_built_and_refusals_exit_two(tmp_path, monkeypatch, capsys):
    run_cli(tmp_path, monkeypatch, capsys)
    h10, sha = (
        tmp_path / "FRB_h10_xml.zip",
        hashlib.sha256((tmp_path / "FRB_h10_xml.zip").read_bytes()).hexdigest(),
    )
    args = [
        "--spec",
        str(tmp_path / "spec.yaml"),
        "--mode",
        "unhedged",
        "--foreign",
        str(tmp_path / "builds" / "usd"),
        "--h10",
        str(h10),
        "--h10-sha256",
        sha,
        "--out",
        str(tmp_path / "out"),
    ]
    assert tool.main(args) == 0
    assert "already built" in capsys.readouterr().out
    args[args.index("--h10-sha256") + 1] = "0" * 64
    assert tool.main(args) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("refused: ValueError")
    args[args.index("--out") + 1] = str(REPO / "zz_translate_out_must_not_exist")
    args[args.index("--h10-sha256") + 1] = sha
    assert tool.main(args) == 2
    assert capsys.readouterr().err.startswith("refused:")
    args[args.index("--foreign") + 1] = str(tmp_path / "missing")
    assert tool.main(args) == 2  # an OSError refuses too
