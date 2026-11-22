"""OD-0213: the factor build tool, on an invented snapshot only. No network, no real data."""

import hashlib
import importlib
import json
import re
import stat
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal as D
from itertools import pairwise
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
tool = importlib.import_module("factor_build")

COMMIT = "c" * 40
FACTOR = "equity.us.zzz.market_total_return"
SNAPSHOT = "s1"
DAYS = ["2030-01-07", "2030-01-08", "2030-01-09", "2030-01-10", "2030-01-11"]
CLOSES = [100.0, 102.0, 102.0, 51.0, 52.0]
TOL = D("1e-12")


@pytest.fixture(autouse=True)
def private_tmp(tmp_path):
    tmp_path.chmod(0o700)


def spec_text(series_class="total_return", second_symbol="ZZZ", numeraire="USD", extra=""):
    return f"""identity:
  factor_id: {FACTOR}
  version: 0.1.0
classification:
  series_class: {series_class}
return_convention:
  numeraire: {numeraire}
observations:
  - series_id: ZZZ.US.close_unadjusted
    source_id: invented.source
  - series_id: {second_symbol}.US.distributions_and_splits
    source_id: invented.source
{extra}"""


def write_spec(tmp_path, name="spec.yaml", **kwargs):
    path = tmp_path / name
    path.write_text(spec_text(**kwargs))
    return path


def dividend_record(day=DAYS[2], amount=1.0):
    return {
        "date": day,
        "value": amount,
        "unadjustedValue": amount,
        "currency": "USD",
        "paymentDate": DAYS[3],
        "recordDate": day,
        "declarationDate": DAYS[1],
    }


def make_snapshot(tmp_path, closes=CLOSES, drop=None, dividends=None):
    """The real layout: raw/<snapshot>/<SYMBOL>.<kind>.json and manifest.json. Returns (root, pin)."""
    root = tmp_path / "root"
    raw = root / "raw" / SNAPSHOT
    raw.mkdir(parents=True)
    dividends = [dividend_record()] if dividends is None else dividends
    contents = {
        ("ZZZ.US", "eod"): [
            {"date": d, "close": c, "adjusted_close": c} for d, c in zip(DAYS, closes, strict=True)
        ],
        ("ZZZ.US", "div"): dividends,
        ("ZZZ.US", "splits"): [{"date": DAYS[3], "split": "2.000000/1.000000"}],
        ("EXCHANGE.US", "symbols"): [{"Code": "ZZZ", "Currency": "USD"}],
    }
    files = []
    for (symbol, kind), rows in contents.items():
        if drop == kind and symbol == "ZZZ.US":
            continue
        name = f"{symbol}.{kind}.json"
        body = json.dumps(rows).encode()
        (raw / name).write_bytes(body)
        files.append(
            {
                "symbol": symbol,
                "kind": kind,
                "path": f"raw/{SNAPSHOT}/{name}",
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        )
    manifest = json.dumps({"snapshot": SNAPSHOT, "files": files, "stopped": None}, indent=1, sort_keys=True)
    (raw / "manifest.json").write_text(manifest + "\n")
    return root, hashlib.sha256((raw / "manifest.json").read_bytes()).hexdigest()


def run_build(tmp_path, **kwargs):
    root, pin = make_snapshot(tmp_path)
    return build_in(tmp_path, root, pin, **kwargs)


def build_in(tmp_path, root, pin, spec=None, out=None):
    return tool.build(
        spec or write_spec(tmp_path), root, SNAPSHOT, pin, out or tmp_path / "store", commit=COMMIT
    )


def build_dir(tmp_path, record):
    return tmp_path / "store" / FACTOR / "0.1.0" / record["build_id"]


def rows_of(directory):
    lines = (directory / "series.csv").read_text().splitlines()
    assert lines[0] == "period_start,period_end,price_return,income_return,total_return,index"
    return [line.split(",") for line in lines[1:]]


# --- the build and its files


def test_a_build_with_a_distribution_and_a_split_writes_both_files_in_the_format(tmp_path):
    record = run_build(tmp_path)
    directory = build_dir(tmp_path, record)
    series = (directory / "series.csv").read_bytes()
    text = series.decode()
    assert "\r" not in text and text.endswith("\n")
    assert hashlib.sha256(series).hexdigest() == record["series_sha256"]
    build_bytes = (directory / "build.json").read_bytes()
    assert build_bytes == (json.dumps(record, indent=1, sort_keys=True) + "\n").encode()
    assert sorted(record) == sorted(
        [
            "factor_id",
            "spec_version",
            "spec_sha256",
            "series_class",
            "numeraire",
            "source_id",
            "symbol",
            "snapshot",
            "snapshot_manifest_sha256",
            "inputs",
            "code_commit",
            "periods",
            "first",
            "last",
            "qualified",
            "invariants",
            "source_corrections",
            "distribution_screen",
            "series_sha256",
            "build_id",
        ]
    )
    assert record["factor_id"] == FACTOR and record["spec_version"] == "0.1.0"
    assert record["series_class"] == "total_return" and record["numeraire"] == "USD"
    assert record["source_id"] == "invented.source" and record["symbol"] == "ZZZ.US"
    assert record["snapshot"] == SNAPSHOT and record["code_commit"] == COMMIT
    assert record["periods"] == 4 and record["first"] == DAYS[0] and record["last"] == DAYS[-1]
    assert record["qualified"]["Q1"] and record["qualified"]["Q2"] and "Q3" in record["qualified"]
    assert [i["path"] for i in record["inputs"]] == sorted(i["path"] for i in record["inputs"])
    assert len(record["inputs"]) == 4
    expected_id = hashlib.sha256(
        (record["spec_sha256"] + record["snapshot_manifest_sha256"] + COMMIT).encode()
    ).hexdigest()[:16]
    assert record["build_id"] == expected_id
    for name in ("RA-INV-001", "index_chain", "RA-INV-020"):
        assert record["invariants"][name]["passed"] is True
    for row in rows_of(directory):
        assert all(re.fullmatch(r"-?\d+(\.\d+)?", cell) for cell in row[2:])


def test_the_returns_match_a_hand_computation_and_the_index_chains(tmp_path):
    record = run_build(tmp_path)
    rows = rows_of(build_dir(tmp_path, record))
    expected = [
        (D("0.02"), D(0)),
        (D(0), D(1) / D(102)),
        (D(0), D(0)),  # the split day: 2 * 51 / 102 - 1
        (D(1) / D(51), D(0)),
    ]
    assert len(rows) == 4
    level = D(1)
    for row, (price, income) in zip(rows, expected, strict=True):
        got_price, got_income, got_total, got_index = (D(cell) for cell in row[2:])
        assert abs(got_price - price) <= TOL and abs(got_income - income) <= TOL
        assert abs(got_total - (price + income)) <= TOL
        level *= 1 + (price + income)
        assert abs(got_index - level) <= TOL
    assert [r[0] for r in rows] == DAYS[:-1] and [r[1] for r in rows] == DAYS[1:]
    assert record["invariants"]["RA-INV-020"] == {"checked": 1, "passed": True}


def test_a_split_day_has_no_income_and_a_continuous_price_return(tmp_path):
    record = run_build(tmp_path)
    split_row = rows_of(build_dir(tmp_path, record))[2]
    assert split_row[1] == DAYS[3]
    assert D(split_row[3]) == 0
    assert abs(D(split_row[2])) <= TOL  # 2 new units at 51 against 1 old unit at 102


def test_a_second_build_is_already_built_with_identical_bytes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tool._base, "code_commit", lambda: {"commit": COMMIT})
    root, pin = make_snapshot(tmp_path)
    spec = write_spec(tmp_path)
    args = ["--spec", str(spec), "--root", str(root), "--snapshot", SNAPSHOT]
    args += ["--manifest-sha256", pin, "--out", str(tmp_path / "store")]
    assert tool.main(args) == 0
    assert "already built" not in capsys.readouterr().out
    record = build_in(tmp_path, root, pin)
    directory = build_dir(tmp_path, record)
    before = [(directory / n).read_bytes() for n in ("series.csv", "build.json")]
    assert tool.main(args) == 0
    assert "already built" in capsys.readouterr().out
    assert [(directory / n).read_bytes() for n in ("series.csv", "build.json")] == before


def test_a_build_directory_with_different_bytes_refuses(tmp_path):
    record = run_build(tmp_path)
    directory = build_dir(tmp_path, record)
    directory.joinpath("series.csv").chmod(0o600)
    directory.joinpath("series.csv").write_bytes(b"changed\n")
    root, pin = tmp_path / "root", record["snapshot_manifest_sha256"]
    with pytest.raises(ValueError, match="different bytes"):
        build_in(tmp_path, root, pin)


# --- refusals


def test_a_wrong_pin_refuses(tmp_path):
    root, _pin = make_snapshot(tmp_path)
    with pytest.raises(ValueError, match="pin"):
        build_in(tmp_path, root, "0" * 64)
    assert not (tmp_path / "store").exists()


def test_altered_retained_bytes_refuse(tmp_path):
    root, pin = make_snapshot(tmp_path)
    (root / "raw" / SNAPSHOT / "ZZZ.US.eod.json").write_bytes(b"[]")
    with pytest.raises(ValueError, match="retained bytes"):
        build_in(tmp_path, root, pin)


def test_an_excess_return_spec_refuses(tmp_path):
    root, pin = make_snapshot(tmp_path)
    with pytest.raises(ValueError, match="total_return"):
        build_in(tmp_path, root, pin, spec=write_spec(tmp_path, series_class="excess_return"))


def test_observations_with_two_symbols_refuse(tmp_path):
    root, pin = make_snapshot(tmp_path)
    with pytest.raises(ValueError, match="prefix"):
        build_in(tmp_path, root, pin, spec=write_spec(tmp_path, second_symbol="YYY"))


def test_a_wrong_numeraire_refuses(tmp_path):
    root, pin = make_snapshot(tmp_path)
    with pytest.raises(ValueError, match="did not qualify"):
        build_in(tmp_path, root, pin, spec=write_spec(tmp_path, numeraire="AUD"))


@pytest.mark.parametrize("kind", ["eod", "div", "splits"])
def test_a_missing_symbol_file_refuses(tmp_path, kind):
    root, pin = make_snapshot(tmp_path, drop=kind)
    with pytest.raises(ValueError, match=f"no {kind} file"):
        build_in(tmp_path, root, pin)


def test_a_non_positive_close_refuses(tmp_path):
    root, pin = make_snapshot(tmp_path, closes=[100.0, 0.0, 102.0, 51.0, 52.0])
    with pytest.raises(ValueError, match="Q1"):
        build_in(tmp_path, root, pin)


def test_an_out_inside_the_repository_refuses(tmp_path):
    root, pin = make_snapshot(tmp_path)
    target = REPO / "factor-build-refused-out"
    with pytest.raises(ValueError, match="outside the repository"):
        build_in(tmp_path, root, pin, out=target)
    assert not target.exists()


def test_a_failed_invariant_refuses():
    class Period:
        def __init__(self, total, price, income, start="2030-01-07", end="2030-01-08"):
            self.total_return, self.price_return, self.income_return = D(total), D(price), D(income)
            self.start, self.end = start, end

    broken = [Period("0.02", "0.01", "0.0")]
    result = tool.check_invariants(broken, tool.index_levels(broken), set(), set())
    assert result["RA-INV-001"]["passed"] is False
    split = [Period("0.01", "0", "0.01")]
    day = split[0].end
    result = tool.check_invariants(split, tool.index_levels(split), {day}, set())
    assert result["RA-INV-020"] == {"checked": 1, "passed": False}
    gap = [Period("0.01", "0.01", "0", "1", "2"), Period("0.01", "0.01", "0", "3", "4")]
    assert tool.check_invariants(gap, tool.index_levels(gap), set(), set())["index_chain"]["passed"] is False
    wrong_level = tool.check_invariants(gap[:1], [D("5")], set(), set())
    assert wrong_level["index_chain"]["passed"] is False


# --- the command line


def test_the_command_prints_no_return_or_date_and_refuses_with_exit_2(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tool._base, "code_commit", lambda: {"commit": COMMIT})
    root, pin = make_snapshot(tmp_path)
    args = ["--spec", str(write_spec(tmp_path)), "--root", str(root), "--snapshot", SNAPSHOT]
    args += ["--manifest-sha256", pin, "--out", str(tmp_path / "store")]
    assert tool.main(args) == 0
    out = capsys.readouterr().out
    assert FACTOR in out and "series_sha256" in out and "RA-INV-020: pass" in out
    assert "periods: 4" in out
    assert not re.search(r"\d{4}-\d{2}-\d{2}", out)
    assert not re.search(r"\d\.\d", out)
    bad = [*args[:-4], "--manifest-sha256", "0" * 64, "--out", str(tmp_path / "store")]
    assert tool.main(bad) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("refused:") and captured.out == ""
    assert tool.main([*args[:-1], str(REPO / "no-such-out")]) == 2
    assert capsys.readouterr().err.startswith("refused:")


def test_file_and_directory_modes(tmp_path):
    record = run_build(tmp_path)
    directory = build_dir(tmp_path, record)
    for name in ("series.csv", "build.json"):
        assert stat.S_IMODE((directory / name).stat().st_mode) == 0o600
    for level in (tmp_path / "store", tmp_path / "store" / FACTOR, directory.parent, directory):
        assert stat.S_IMODE(level.stat().st_mode) == 0o700


# --- the distribution screen (OD-0228), on invented periods


@dataclass
class Period:
    start: date
    end: date
    price_return: D
    income_return: D


START = date(2030, 1, 1)


def distribution_periods(yields, prices=None):
    """Consecutive periods that each pay a distribution; the price falls by the yield unless given."""
    prices = prices or [-D(y) for y in yields]
    return [
        Period(START + timedelta(days=i), START + timedelta(days=i + 1), D(price), D(y))
        for i, (y, price) in enumerate(zip(yields, prices, strict=True))
    ]


def daily_periods(count=40):
    return [
        Period(START + timedelta(days=i), START + timedelta(days=i + 1), D(0), D(0)) for i in range(count)
    ]


def day_of(index):
    """The `end` day of the index-th period built by `distribution_periods` or `daily_periods`."""
    return (START + timedelta(days=index + 1)).isoformat()


def screen_of(yields, prices=None, dividends=()):
    return tool.screen_distributions(distribution_periods(yields, prices), list(dividends))


def flagged_days(result):
    return {f["day"]: f["rules"] for f in result["flagged"]}


def test_a_clean_series_flags_nothing():
    result = screen_of(["0.01"] * 9)
    assert result["distribution_days"] == 9
    assert result["D1"] == {"checked": 9, "flagged": 0}
    assert result["D2"] == {"checked": 9, "flagged": 0}
    assert result["D3"] == {"checked": 0, "flagged": 0}
    assert result["flagged"] == [] and result["flagged_days"] == 0 and result["flagged_d1_and_d2"] == 0


def test_the_screen_records_its_thresholds_as_strings():
    thresholds = screen_of(["0.01"])["thresholds"]
    assert thresholds["D1_min_yield"] == "0.005" and thresholds["D2_min_yield"] == "0.02"
    assert thresholds["D1_multiple_of_neighbour_median"] == "3" and thresholds["D3_max_days_apart"] == "10"
    assert all(isinstance(v, str) for v in thresholds.values())


def test_days_without_income_are_not_distribution_days():
    periods = daily_periods(12)
    assert tool.screen_distributions(periods, [])["distribution_days"] == 0


def test_d1_flags_a_yield_above_three_times_its_neighbours_median():
    result = screen_of(["0.01"] * 4 + ["0.04"] + ["0.01"] * 4)
    assert result["D1"] == {"checked": 9, "flagged": 1}
    assert flagged_days(result) == {day_of(4): ["D1"]}


def test_d1_does_not_flag_a_yield_of_exactly_three_times_the_median():
    result = screen_of(["0.01"] * 4 + ["0.03"] + ["0.01"] * 4)
    assert result["D1"] == {"checked": 9, "flagged": 0}


def test_d1_needs_a_yield_of_at_least_half_a_percent():
    low = screen_of(["0.001"] * 4 + ["0.0049"] + ["0.001"] * 4)  # above 3 x the median but under 0.5%
    assert low["D1"]["flagged"] == 0
    at = screen_of(["0.001"] * 4 + ["0.005"] + ["0.001"] * 4)
    assert flagged_days(at) == {day_of(4): ["D1"]}


def test_d1_median_of_an_even_count_is_the_mean_of_the_middle_two():
    # the last day's four neighbours are 0.01, 0.01, 0.02, 0.02: median 0.015, so the line is 0.045
    assert screen_of(["0.01", "0.01", "0.02", "0.02", "0.046"])["D1"]["flagged"] == 1
    assert screen_of(["0.01", "0.01", "0.02", "0.02", "0.045"])["D1"]["flagged"] == 0


def test_d1_is_not_evaluated_with_fewer_than_four_neighbours():
    short = screen_of(["0.01", "0.01", "0.01", "0.5"])  # each day has three neighbours
    assert short["D1"] == {"checked": 0, "flagged": 0}
    five = screen_of(["0.01"] * 4 + ["0.5"])  # each day has four
    assert five["D1"] == {"checked": 5, "flagged": 1}
    assert flagged_days(five) == {day_of(4): ["D1"]}


def test_d1_uses_only_the_nearest_four_on_each_side():
    # the days five and six places away are huge; they would lift a wider median above the 0.04 line
    yields = ["0.5", "0.5", "0.5", "0.5", "0.5", "0.01", "0.01", "0.01", "0.01", "0.04", "0.01"]
    yields += ["0.01", "0.01", "0.01", "0.5", "0.5", "0.5", "0.5", "0.5"]
    result = screen_of(yields)
    assert flagged_days(result)[day_of(9)] == ["D1"]


def test_d2_flags_a_large_yield_without_a_price_fall_of_half_the_yield():
    assert flagged_days(screen_of(["0.02"], ["0.0"])) == {day_of(0): ["D2"]}
    assert flagged_days(screen_of(["0.02"], ["-0.0099"])) == {day_of(0): ["D2"]}
    assert screen_of(["0.02"], ["0.0"])["D2"] == {"checked": 1, "flagged": 1}


def test_d2_does_not_flag_a_price_fall_of_exactly_half_the_yield():
    assert screen_of(["0.02"], ["-0.01"])["D2"] == {"checked": 1, "flagged": 0}
    assert screen_of(["0.04"], ["-0.03"])["D2"]["flagged"] == 0


def test_d2_needs_a_yield_of_at_least_two_percent():
    assert screen_of(["0.0199"], ["0.0"])["D2"] == {"checked": 1, "flagged": 0}
    assert screen_of(["0.02"], ["0.0"])["D2"]["flagged"] == 1


def test_a_day_flagged_by_d1_and_d2_together_is_counted_once():
    prices = ["-0.01"] * 4 + ["0.0"]
    result = screen_of(["0.01"] * 4 + ["0.05"], prices)
    assert flagged_days(result) == {day_of(4): ["D1", "D2"]}
    assert result["flagged_days"] == 1 and result["flagged_d1_and_d2"] == 1
    assert result["D1"]["flagged"] == 1 and result["D2"]["flagged"] == 1


def record(day, amount="1.0"):
    return {"date": day, "unadjustedValue": amount}


def test_d3_flags_both_records_of_a_pair_ten_days_apart():
    records = [record("2030-01-05", "0.7"), record("2030-01-15", "0.7")]
    result = tool.screen_distributions(daily_periods(), records)
    assert result["D3"] == {"checked": 2, "flagged": 2}
    assert flagged_days(result) == {"2030-01-05": ["D3"], "2030-01-15": ["D3"]}
    assert result["flagged_days"] == 2 and result["flagged_d1_and_d2"] == 0


def test_d3_does_not_flag_a_pair_eleven_days_apart_or_on_one_date_or_with_different_amounts():
    far = [record("2030-01-05", "0.7"), record("2030-01-16", "0.7")]
    assert tool.screen_distributions(daily_periods(), far)["D3"] == {"checked": 2, "flagged": 0}
    same_day = [record("2030-01-05", "0.7"), record("2030-01-05", "0.7")]
    assert tool.screen_distributions(daily_periods(), same_day)["D3"]["flagged"] == 0
    different = [record("2030-01-05", "0.7"), record("2030-01-06", "0.71")]
    assert tool.screen_distributions(daily_periods(), different)["D3"]["flagged"] == 0


def test_d3_looks_only_at_positive_amounts():
    records = [record("2030-01-05", "0"), record("2030-01-06", "0"), {"date": "2030-01-07"}]
    records += [{"date": "2030-01-08", "unadjustedValue": None}, record("2030-01-09", "0.5")]
    result = tool.screen_distributions(daily_periods(), records)
    assert result["D3"] == {"checked": 1, "flagged": 0}


def test_a_d3_record_on_an_unobserved_day_lands_on_the_next_observed_day():
    weekdays = [date(2030, 1, 7), date(2030, 1, 8), date(2030, 1, 9), date(2030, 1, 10), date(2030, 1, 14)]
    periods = [Period(a, b, D(0), D(0)) for a, b in pairwise(weekdays)]
    records = [record("2030-01-10", "0.5"), record("2030-01-12", "0.5")]  # the 12th is a Saturday
    result = tool.screen_distributions(periods, records)
    assert flagged_days(result) == {"2030-01-10": ["D3"], "2030-01-14": ["D3"]}


def test_a_d3_record_after_the_last_close_is_ignored():
    records = [record("2030-02-05", "0.5"), record("2030-02-09", "0.5"), record("2030-02-10", "0.5")]
    periods = daily_periods(40)  # the last close is 2030-02-10
    assert tool.screen_distributions(periods, records)["D3"]["flagged"] == 3
    after = [record("2030-02-10", "0.5"), record("2030-02-14", "0.5")]
    result = tool.screen_distributions(periods, after)
    assert result["D3"] == {"checked": 2, "flagged": 1}
    assert flagged_days(result) == {"2030-02-10": ["D3"]}
    assert tool.screen_distributions(periods, [record("2030-02-20", "0.5")])["flagged"] == []


def test_flagged_days_are_sorted_and_each_lists_its_rules_sorted():
    prices = ["-0.01"] * 4 + ["0.0"]
    periods = distribution_periods(["0.01"] * 4 + ["0.05"], prices)
    records = [record(day_of(4), "0.5"), record(day_of(2), "0.5")]
    result = tool.screen_distributions(periods, records)
    assert [f["day"] for f in result["flagged"]] == sorted(f["day"] for f in result["flagged"])
    assert result["flagged"][-1] == {"day": day_of(4), "rules": ["D1", "D2", "D3"]}


# --- the screen in the build and on the command line


def flagged_dividends():
    # two equal records a day apart; each yields about 3%, on a price that did not fall: D2 and D3 flag
    return [dividend_record(DAYS[1], 3.0), dividend_record(DAYS[2], 3.0)]


def test_a_build_with_a_flagged_series_succeeds_and_records_the_screen(tmp_path):
    root, pin = make_snapshot(tmp_path, dividends=flagged_dividends())
    record = build_in(tmp_path, root, pin)
    screen = record["distribution_screen"]
    assert screen["D2"] == {"checked": 2, "flagged": 2} and screen["D3"] == {"checked": 2, "flagged": 2}
    assert screen["D1"] == {"checked": 0, "flagged": 0}
    assert flagged_days(screen) == {DAYS[1]: ["D2", "D3"], DAYS[2]: ["D2", "D3"]}
    assert screen["flagged_days"] == 2 and screen["flagged_d1_and_d2"] == 0
    stored = json.loads((build_dir(tmp_path, record) / "build.json").read_text())
    assert stored["distribution_screen"] == screen
    assert all(result["passed"] for result in record["invariants"].values())


def test_the_ordinary_build_records_a_screen_that_flags_nothing(tmp_path):
    screen = run_build(tmp_path)["distribution_screen"]
    assert screen["distribution_days"] == 1 and screen["flagged"] == []
    assert screen["D3"] == {"checked": 1, "flagged": 0}


def cli_args(tmp_path, *extra, out=True):
    root, pin = make_snapshot(tmp_path, dividends=flagged_dividends())
    args = ["--spec", str(write_spec(tmp_path)), "--root", str(root), "--snapshot", SNAPSHOT]
    args += ["--manifest-sha256", pin]
    if out:
        args += ["--out", str(tmp_path / "store")]
    return [*args, *extra]


def forbid_git(monkeypatch):
    def refuse():
        raise AssertionError("code_commit must not be called")

    monkeypatch.setattr(tool._base, "code_commit", refuse)


def test_the_command_prints_the_screen_counts_and_no_date_or_value(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tool._base, "code_commit", lambda: {"commit": COMMIT})
    assert tool.main(cli_args(tmp_path)) == 0
    lines = capsys.readouterr().out.splitlines()
    screen = [line for line in lines if line.startswith(("D1:", "D2:", "D3:", "distribution_screen:"))]
    assert screen == [
        "D1: 0 flagged (0 checked)",
        "D2: 2 flagged (2 checked)",
        "D3: 2 flagged (2 checked)",
        "distribution_screen: 2 day(s) flagged, 0 by D1 and D2",
    ]
    last_invariant = max(i for i, line in enumerate(lines) if line.startswith("RA-INV-020"))
    assert lines.index(screen[0]) == last_invariant + 1
    text = "\n".join(lines)
    assert not re.search(r"\d{4}-\d{2}-\d{2}", text) and not re.search(r"\d\.\d", text)


def tree(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*"))


def test_screen_only_needs_no_out_writes_nothing_and_never_asks_git(tmp_path, monkeypatch, capsys):
    forbid_git(monkeypatch)
    args = cli_args(tmp_path, "--screen-only", out=False)
    where = tmp_path / "cwd"
    where.mkdir()
    monkeypatch.chdir(where)
    before = tree(tmp_path)
    assert tool.main(args) == 0
    assert tree(tmp_path) == before
    assert not (tmp_path / "store").exists()
    out = capsys.readouterr().out
    assert f"factor_id: {FACTOR}" in out and "periods: 4" in out
    assert "D3: 2 flagged (2 checked)" in out
    assert "distribution_screen: 2 day(s) flagged, 0 by D1 and D2" in out
    assert "build_id" not in out and "series_sha256" not in out
    assert not re.search(r"\d{4}-\d{2}-\d{2}", out) and not re.search(r"\d\.\d", out)


def test_screen_only_verifies_the_pin_and_the_snapshot(tmp_path, monkeypatch, capsys):
    forbid_git(monkeypatch)
    args = cli_args(tmp_path, "--screen-only", out=False)
    wrong_pin = list(args)
    wrong_pin[wrong_pin.index("--manifest-sha256") + 1] = "0" * 64
    assert tool.main(wrong_pin) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("refused:") and captured.out == ""
    root = Path(args[args.index("--root") + 1])
    (root / "raw" / SNAPSHOT / "ZZZ.US.eod.json").write_bytes(b"[]")
    assert tool.main(args) == 2
    assert capsys.readouterr().err.startswith("refused:")


def test_a_build_needs_out_and_screen_only_refuses_it(tmp_path, capsys):
    args = cli_args(tmp_path, out=False)
    assert tool.main(args) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("refused:") and captured.out == ""
    assert tool.main([*args, "--screen-only", "--out", str(tmp_path / "store")]) == 2
    assert capsys.readouterr().err.startswith("refused:")
    assert not (tmp_path / "store").exists()


def test_screen_report_writes_a_private_json_file(tmp_path, monkeypatch):
    forbid_git(monkeypatch)
    report = tmp_path / "report.json"
    assert tool.main(cli_args(tmp_path, "--screen-only", "--screen-report", str(report), out=False)) == 0
    assert stat.S_IMODE(report.stat().st_mode) == 0o600
    data = report.read_bytes()
    body = json.loads(data)
    assert data == (json.dumps(body, indent=1, sort_keys=True) + "\n").encode()
    assert body["factor_id"] == FACTOR and body["symbol"] == "ZZZ.US" and body["snapshot"] == SNAPSHOT
    root = tmp_path / "root" / "raw" / SNAPSHOT / "manifest.json"
    assert body["snapshot_manifest_sha256"] == hashlib.sha256(root.read_bytes()).hexdigest()
    assert body["D3"] == {"checked": 2, "flagged": 2} and body["flagged_days"] == 2
    assert [f["day"] for f in body["flagged"]] == [DAYS[1], DAYS[2]]
    assert "thresholds" in body


def test_screen_report_refuses_a_path_inside_the_repository(tmp_path, capsys):
    target = REPO / "screen-report-refused.json"
    assert tool.main(cli_args(tmp_path, "--screen-only", "--screen-report", str(target), out=False)) == 2
    assert capsys.readouterr().err.startswith("refused:")
    assert not target.exists()


def test_screen_report_refuses_an_existing_file_and_leaves_it_alone(tmp_path, capsys):
    report = tmp_path / "report.json"
    report.write_text("keep\n")
    assert tool.main(cli_args(tmp_path, "--screen-only", "--screen-report", str(report), out=False)) == 2
    assert capsys.readouterr().err.startswith("refused:")
    assert report.read_text() == "keep\n"


def test_screen_report_without_screen_only_is_refused(tmp_path, capsys):
    report = tmp_path / "report.json"
    assert tool.main(cli_args(tmp_path, "--screen-report", str(report))) == 2
    assert capsys.readouterr().err.startswith("refused:")
    assert not report.exists() and not (tmp_path / "store").exists()


# --- a distribution exclusion declared in the spec (OD-0230), on invented data


def correction(**overrides):
    base = {
        "action": "exclude_distribution",
        "series_id": "ZZZ.US.distributions_and_splits",
        "ex_date": DAYS[1],
        "reason": "invented: the vendor lists one distribution twice",
        "evidence": "invented/evidence.md",
    }
    return {**base, **overrides}


def corrections_text(corrections):
    return yaml.safe_dump({"construction": {"source_corrections": corrections}}, sort_keys=False)


def corrected_spec(tmp_path, corrections=None, name="spec.yaml"):
    corrections = [correction()] if corrections is None else corrections
    return write_spec(tmp_path, name=name, extra=corrections_text(corrections))


def duplicated_dividends():
    """The ordinary distribution on DAYS[2] and an equal duplicate a day earlier, listed first."""
    return [dividend_record(DAYS[1], 1.0), dividend_record(DAYS[2], 1.0)]


def duplicate_snapshot(tmp_path):
    return make_snapshot(tmp_path, dividends=duplicated_dividends())


def snapshot_bytes(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def series_of(out, record):
    return (out / FACTOR / "0.1.0" / record["build_id"] / "series.csv").read_bytes()


def record_hash(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def as_read(record):
    """The record as the tool reads it from a file: numbers parsed to `Decimal`, which hash as strings."""
    return json.loads(json.dumps(record), parse_float=D, parse_int=D)


def read_hash(record):
    return record_hash(as_read(record))


def test_a_spec_without_corrections_reads_an_empty_list_and_builds_the_same_series(tmp_path):
    plain = tool.read_spec(write_spec(tmp_path))
    assert plain["source_corrections"] == []
    root, pin = make_snapshot(tmp_path)
    base = build_in(tmp_path, root, pin, out=tmp_path / "base")
    assert base["source_corrections"] == []
    for n, extra in enumerate(
        ("construction:\n  calendar: invented\n", "construction:\n  source_corrections: []\n")
    ):
        spec = write_spec(tmp_path, name=f"other{n}.yaml", extra=extra)
        assert tool.read_spec(spec)["source_corrections"] == []
        other = build_in(tmp_path, root, pin, spec=spec, out=tmp_path / f"block{n}")
        assert other["source_corrections"] == []
        assert series_of(tmp_path / f"block{n}", other) == series_of(tmp_path / "base", base)
        assert other["series_sha256"] == base["series_sha256"]


def test_an_excluded_duplicate_builds_the_same_series_as_a_snapshot_without_it(tmp_path):
    clean_root, clean_pin = make_snapshot(tmp_path / "clean")
    clean = build_in(tmp_path, clean_root, clean_pin, out=tmp_path / "clean_store")
    root, pin = duplicate_snapshot(tmp_path / "dup")
    uncorrected = build_in(tmp_path, root, pin, out=tmp_path / "raw_store")
    assert uncorrected["distribution_screen"]["D3"] == {"checked": 2, "flagged": 2}
    fixed = build_in(tmp_path, root, pin, spec=corrected_spec(tmp_path), out=tmp_path / "fixed_store")
    assert series_of(tmp_path / "fixed_store", fixed) == series_of(tmp_path / "clean_store", clean)
    assert fixed["series_sha256"] == clean["series_sha256"]
    assert fixed["distribution_screen"]["D3"] == {"checked": 1, "flagged": 0}
    assert fixed["distribution_screen"]["flagged"] == []
    assert fixed["distribution_screen"]["distribution_days"] == 1
    assert fixed["periods"] == clean["periods"]
    assert all(result["passed"] for result in fixed["invariants"].values())


def test_the_build_record_lists_the_applied_correction_with_the_record_hash(tmp_path):
    root, pin = duplicate_snapshot(tmp_path)
    record = build_in(tmp_path, root, pin, spec=corrected_spec(tmp_path))
    expected = [
        {
            "action": "exclude_distribution",
            "ex_date": DAYS[1],
            "record_sha256": read_hash(dividend_record(DAYS[1], 1.0)),
        }
    ]
    assert record["source_corrections"] == expected
    assert expected[0]["record_sha256"] != record_hash(dividend_record(DAYS[1], 1.0))  # numbers hash as read
    stored = json.loads((build_dir(tmp_path, record) / "build.json").read_text())
    assert stored["source_corrections"] == expected


def test_apply_corrections_removes_one_record_and_keeps_the_rest_in_order_and_bytes():
    records = [dividend_record(DAYS[0], 0.5), dividend_record(DAYS[1], 1.0), dividend_record(DAYS[2], 1.0)]
    before = json.dumps(records)
    kept, applied = tool.apply_corrections(records, [correction()])
    assert kept == [records[0], records[2]] and kept[0] is records[0] and kept[1] is records[2]
    assert json.dumps(records) == before  # the input is not changed
    assert applied == [
        {"action": "exclude_distribution", "ex_date": DAYS[1], "record_sha256": record_hash(records[1])}
    ]
    assert tool.apply_corrections(records, []) == (records, [])


def test_apply_corrections_hashes_the_record_with_sorted_keys_and_str_for_other_types():
    odd = {"unadjustedValue": "1.5", "date": DAYS[1], "when": date(2030, 1, 8)}
    _kept, applied = tool.apply_corrections([odd], [correction()])
    expected = hashlib.sha256(
        b'{"date": "2030-01-08", "unadjustedValue": "1.5", "when": "2030-01-08"}'
    ).hexdigest()
    assert applied[0]["record_sha256"] == expected


def test_apply_corrections_applies_each_correction_to_its_own_date():
    records = [dividend_record(d, 1.0) for d in DAYS[:3]]
    kept, applied = tool.apply_corrections(
        records, [correction(ex_date=DAYS[0]), correction(ex_date=DAYS[2])]
    )
    assert kept == [records[1]] and [a["ex_date"] for a in applied] == [DAYS[0], DAYS[2]]


def test_a_correction_with_no_matching_record_refuses_and_names_the_count_only():
    with pytest.raises(ValueError, match="not 0") as raised:
        tool.apply_corrections([dividend_record(DAYS[2], 1.0)], [correction()])
    assert DAYS[1] not in str(raised.value) and "1.0" not in str(raised.value)


def test_two_matching_records_on_the_date_refuse():
    records = [dividend_record(DAYS[1], 1.0), dividend_record(DAYS[1], 2.0)]
    with pytest.raises(ValueError, match="not 2") as raised:
        tool.apply_corrections(records, [correction()])
    assert DAYS[1] not in str(raised.value) and "2.0" not in str(raised.value)


@pytest.mark.parametrize("empty", [{"unadjustedValue": 0}, {"unadjustedValue": None}, {}])
def test_a_record_with_a_zero_or_missing_amount_is_not_a_match(empty):
    unmatched = {"date": DAYS[1], **empty}
    with pytest.raises(ValueError, match="not 0"):
        tool.apply_corrections([unmatched], [correction()])
    kept, applied = tool.apply_corrections([unmatched, dividend_record(DAYS[1], 1.0)], [correction()])
    assert kept == [unmatched] and len(applied) == 1


def test_a_build_refuses_when_a_correction_matches_nothing_or_twice(tmp_path):
    root, pin = make_snapshot(tmp_path)  # one distribution, on DAYS[2]
    with pytest.raises(ValueError, match="not 0"):
        build_in(tmp_path, root, pin, spec=corrected_spec(tmp_path))
    twice_root, twice_pin = make_snapshot(
        tmp_path / "twice", dividends=[dividend_record(DAYS[1], 1.0), dividend_record(DAYS[1], 1.0)]
    )
    with pytest.raises(ValueError, match="not 2"):
        build_in(tmp_path, twice_root, twice_pin, spec=corrected_spec(tmp_path))
    assert not (tmp_path / "store").exists()


MALFORMED = {
    "unknown action": [correction(action="include_distribution")],
    "extra key": [{**correction(), "note": "x"}],
    "missing key": [{k: v for k, v in correction().items() if k != "evidence"}],
    "bad date": [correction(ex_date="2030-13-40")],
    "compact date": [correction(ex_date="20300108")],
    "date not a string": [correction(ex_date=date(2030, 1, 8))],
    "empty reason": [correction(reason="")],
    "blank reason": [correction(reason="  ")],
    "empty evidence": [correction(evidence="")],
    "reason not a string": [correction(reason=5)],
    "wrong symbol prefix": [correction(series_id="YYY.US.distributions_and_splits")],
    "symbol prefix without its dot": [correction(series_id="ZZZ.USX.distributions_and_splits")],
    "duplicate ex_date": [correction(), correction(reason="a second reason")],
    "not a list": {"ex_date": DAYS[1]},
    "a string": "exclude the duplicate",
    "a list of non-mappings": ["exclude_distribution"],
}


@pytest.mark.parametrize("case", list(MALFORMED))
def test_each_malformed_correction_refuses(tmp_path, case):
    spec = corrected_spec(tmp_path, MALFORMED[case])
    with pytest.raises(ValueError):
        tool.read_spec(spec)
    root, pin = duplicate_snapshot(tmp_path)
    with pytest.raises(ValueError):
        build_in(tmp_path, root, pin, spec=spec)
    assert not (tmp_path / "store").exists()


def test_a_construction_that_is_not_a_mapping_refuses(tmp_path):
    with pytest.raises(ValueError, match="construction"):
        tool.read_spec(write_spec(tmp_path, extra="construction: [a]\n"))


def test_two_distinct_corrections_are_read_in_order(tmp_path):
    corrections = [correction(), correction(ex_date=DAYS[2])]
    assert tool.read_spec(corrected_spec(tmp_path, corrections))["source_corrections"] == corrections


def test_the_snapshot_files_are_byte_identical_after_a_corrected_build(tmp_path):
    root, pin = duplicate_snapshot(tmp_path)
    before = snapshot_bytes(root)
    build_in(tmp_path, root, pin, spec=corrected_spec(tmp_path))
    assert snapshot_bytes(root) == before
    assert json.loads(before[f"raw/{SNAPSHOT}/ZZZ.US.div.json"]) == duplicated_dividends()


def test_screen_only_applies_the_correction(tmp_path, monkeypatch, capsys):
    forbid_git(monkeypatch)
    root, pin = duplicate_snapshot(tmp_path)
    spec = corrected_spec(tmp_path)
    args = ["--spec", str(spec), "--root", str(root), "--snapshot", SNAPSHOT]
    args += ["--manifest-sha256", pin, "--screen-only"]
    result = tool.screen_only(spec, root, SNAPSHOT, pin)
    assert result["source_corrections"][0]["ex_date"] == DAYS[1]
    assert result["distribution_screen"]["D3"] == {"checked": 1, "flagged": 0}
    assert result["distribution_screen"]["distribution_days"] == 1
    report = tmp_path / "report.json"
    assert tool.main([*args, "--screen-report", str(report)]) == 0
    body = json.loads(report.read_bytes())
    assert body["source_corrections"] == result["source_corrections"]
    assert body["D3"] == {"checked": 1, "flagged": 0} and body["flagged"] == []
    out = capsys.readouterr().out
    assert "D3: 0 flagged (1 checked)" in out


def test_a_screen_only_result_without_corrections_carries_an_empty_list(tmp_path):
    root, pin = make_snapshot(tmp_path)
    assert tool.screen_only(write_spec(tmp_path), root, SNAPSHOT, pin)["source_corrections"] == []


@pytest.mark.parametrize("screen_only", [False, True])
def test_the_command_prints_the_correction_count_after_periods_and_no_date_or_value(
    tmp_path, monkeypatch, capsys, screen_only
):
    monkeypatch.setattr(tool._base, "code_commit", lambda: {"commit": COMMIT})
    root, pin = duplicate_snapshot(tmp_path)
    args = ["--spec", str(corrected_spec(tmp_path)), "--root", str(root), "--snapshot", SNAPSHOT]
    args += ["--manifest-sha256", pin]
    args += ["--screen-only"] if screen_only else ["--out", str(tmp_path / "store")]
    assert tool.main(args) == 0
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert lines[lines.index("source_corrections: 1 applied") - 1].startswith("periods: ")
    assert not re.search(r"\d{4}-\d{2}-\d{2}", out) and not re.search(r"\d\.\d", out)
    assert read_hash(dividend_record(DAYS[1], 1.0)) not in out


def test_the_command_counts_zero_corrections_for_a_plain_spec(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tool._base, "code_commit", lambda: {"commit": COMMIT})
    assert tool.main(cli_args(tmp_path)) == 0
    assert "source_corrections: 0 applied" in capsys.readouterr().out.splitlines()


def test_a_refused_correction_prints_no_date_or_amount(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tool._base, "code_commit", lambda: {"commit": COMMIT})
    root, pin = make_snapshot(tmp_path)  # no distribution on the correction's date
    args = ["--spec", str(corrected_spec(tmp_path)), "--root", str(root), "--snapshot", SNAPSHOT]
    args += ["--manifest-sha256", pin, "--out", str(tmp_path / "store")]
    assert tool.main(args) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("refused: ValueError")
    assert not re.search(r"\d{4}-\d{2}-\d{2}", captured.err) and not re.search(r"\d\.\d", captured.err)


def test_two_specs_differing_only_in_corrections_give_different_build_ids(tmp_path):
    root, pin = duplicate_snapshot(tmp_path)
    one = build_in(tmp_path, root, pin, spec=corrected_spec(tmp_path, [correction()], name="one.yaml"))
    other = [correction(reason="invented: a different reason")]
    two = build_in(tmp_path, root, pin, spec=corrected_spec(tmp_path, other, name="two.yaml"))
    assert one["spec_sha256"] != two["spec_sha256"] and one["build_id"] != two["build_id"]
    assert one["series_sha256"] == two["series_sha256"]
