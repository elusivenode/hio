"""OD-0213: the factor build tool, on an invented snapshot only. No network, no real data."""

import hashlib
import importlib
import json
import re
import stat
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

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


def spec_text(series_class="total_return", second_symbol="ZZZ", numeraire="USD"):
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
"""


def write_spec(tmp_path, **kwargs):
    path = tmp_path / "spec.yaml"
    path.write_text(spec_text(**kwargs))
    return path


def make_snapshot(tmp_path, closes=CLOSES, drop=None):
    """The real layout: raw/<snapshot>/<SYMBOL>.<kind>.json and manifest.json. Returns (root, pin)."""
    root = tmp_path / "root"
    raw = root / "raw" / SNAPSHOT
    raw.mkdir(parents=True)
    dividend = {
        "date": DAYS[2],
        "value": 1.0,
        "unadjustedValue": 1.0,
        "currency": "USD",
        "paymentDate": DAYS[3],
        "recordDate": DAYS[2],
        "declarationDate": DAYS[1],
    }
    contents = {
        ("ZZZ.US", "eod"): [
            {"date": d, "close": c, "adjusted_close": c} for d, c in zip(DAYS, closes, strict=True)
        ],
        ("ZZZ.US", "div"): [dividend],
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
