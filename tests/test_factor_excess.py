"""OD-0215: the excess-return build tool, on invented total-return builds only. No network, no real data."""

import hashlib
import importlib
import json
import stat
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
tool = importlib.import_module("factor_excess")

COMMIT = "c" * 40
EXCESS = "equity.zzz.vs_cash.excess"
ASSET = "equity.zzz.market_total_return"
CASH = "cash.zzz.market_total_return"

# asset boundaries: 02, 03, 04, 05, 08; cash boundaries: 02, 04, 05, 06, 08. Common: 02, 04, 05, 08.
ASSET_PERIODS = [
    ("2030-01-02", "2030-01-03", "0.01"),
    ("2030-01-03", "2030-01-04", "0.02"),
    ("2030-01-04", "2030-01-05", "-0.01"),
    ("2030-01-05", "2030-01-08", "0.03"),
]
CASH_PERIODS = [
    ("2030-01-02", "2030-01-04", "0.001"),
    ("2030-01-04", "2030-01-05", "0.0005"),
    ("2030-01-05", "2030-01-06", "0.0004"),
    ("2030-01-06", "2030-01-08", "0.0003"),
]


@pytest.fixture(autouse=True)
def private_tmp(tmp_path):
    tmp_path.chmod(0o700)


def spec_text(series_class="excess_return", numeraire="USD", cash=CASH, ids=(ASSET, CASH)):
    obs = "".join(f"  - series_id: {i}\n    source_id: invented.source\n" for i in ids)
    return f"""identity:
  factor_id: {EXCESS}
  version: 0.1.0
classification:
  series_class: {series_class}
return_convention:
  numeraire: {numeraire}
  cash_leg: {cash}
observations:
{obs}"""


def write_spec(tmp_path, **kwargs):
    path = tmp_path / "spec.yaml"
    path.write_text(spec_text(**kwargs))
    return path


def write_leg(
    tmp_path,
    name,
    factor_id,
    periods,
    *,
    series_class="total_return",
    numeraire="USD",
    passed=True,
    build_id=None,
):
    directory = tmp_path / "legs" / name
    directory.mkdir(parents=True)
    lines = ["period_start,period_end,price_return,income_return,total_return,index\n"]
    level = D(1)
    for start, end, tr in periods:
        level *= 1 + D(tr)
        lines.append(f"{start},{end},{tr},0,{tr},{level}\n")
    data = "".join(lines).encode()
    (directory / "series.csv").write_bytes(data)
    record = {
        "factor_id": factor_id,
        "series_class": series_class,
        "numeraire": numeraire,
        "invariants": {"RA-INV-001": {"checked": len(periods), "passed": passed}},
        "series_sha256": hashlib.sha256(data).hexdigest(),
        "build_id": build_id or hashlib.sha256(name.encode()).hexdigest()[:16],
    }
    (directory / "build.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return directory


def legs(tmp_path, asset_opts=None, cash_opts=None):
    return (
        write_leg(tmp_path, "asset", ASSET, ASSET_PERIODS, **(asset_opts or {})),
        write_leg(tmp_path, "cash", CASH, CASH_PERIODS, **(cash_opts or {})),
    )


def run(tmp_path, spec=None, asset=None, cash=None, out=None, asset_opts=None, cash_opts=None):
    if asset is None or cash is None:
        asset, cash = legs(tmp_path, asset_opts, cash_opts)
    spec = spec or write_spec(tmp_path)
    return tool.build(spec, asset, cash, out or tmp_path / "store", commit=COMMIT)


def build_dir(tmp_path, record):
    return tmp_path / "store" / EXCESS / "0.1.0" / record["build_id"]


def rows_of(directory):
    lines = (directory / "series.csv").read_text().splitlines()
    return [line.split(",") for line in lines[1:]]


# --- the series


def test_excess_matches_a_hand_computation_with_compounded_legs(tmp_path):
    record = run(tmp_path)
    rows = rows_of(build_dir(tmp_path, record))
    assert (build_dir(tmp_path, record) / "series.csv").read_text().splitlines()[0] == (
        "period_start,period_end,asset_return,cash_return,excess_return"
    )
    assert [r[:2] for r in rows] == [
        ["2030-01-02", "2030-01-04"],
        ["2030-01-04", "2030-01-05"],
        ["2030-01-05", "2030-01-08"],
    ]
    # period 1 compounds two asset periods; period 3 compounds two cash periods
    assert [D(r[2]) for r in rows] == [D("0.0302"), D("-0.01"), D("0.03")]
    assert [D(r[3]) for r in rows] == [D("0.001"), D("0.0005"), D("0.00070012")]
    assert [D(r[4]) for r in rows] == [D("0.0292"), D("-0.0105"), D("0.02929988")]
    assert record["periods"] == 3
    assert (record["first"], record["last"]) == ("2030-01-02", "2030-01-08")


def test_ra_inv_005_holds_and_all_invariants_pass(tmp_path):
    record = run(tmp_path)
    for r in rows_of(build_dir(tmp_path, record)):
        assert abs(D(r[3]) + D(r[4]) - D(r[2])) <= D("1e-12")
    assert set(record["invariants"]) == {"RA-INV-004", "RA-INV-005", "alignment"}
    assert all(v["passed"] and v["checked"] == 3 for v in record["invariants"].values())


def test_the_alignment_product_equals_each_legs_index_ratio(tmp_path):
    record = run(tmp_path)
    rows = rows_of(build_dir(tmp_path, record))
    asset, cash = D(1), D(1)
    for r in rows:
        asset *= 1 + D(r[2])
        cash *= 1 + D(r[3])
    assert abs(asset - D("1.01") * D("1.02") * D("0.99") * D("1.03")) <= D("1e-12")
    assert abs(cash - D("1.001") * D("1.0005") * D("1.0004") * D("1.0003")) <= D("1e-12")


def test_omitted_dates_are_counted_per_leg(tmp_path):
    record = run(tmp_path)
    assert record["omitted_dates"] == {"asset": 1, "cash": 1}


def test_the_record_names_both_legs_and_the_format(tmp_path):
    record = run(tmp_path)
    on_disk = json.loads((build_dir(tmp_path, record) / "build.json").read_text())
    assert on_disk == record
    assert record["series_class"] == "excess_return"
    assert record["asset_leg"]["factor_id"] == ASSET
    assert record["cash_leg"]["factor_id"] == CASH
    assert set(record["asset_leg"]) == {"factor_id", "build_id", "series_sha256"}
    assert record["code_commit"] == COMMIT
    text = (build_dir(tmp_path, record) / "build.json").read_text()
    assert text.endswith("\n") and "\r" not in text


def test_build_id_is_the_documented_hash(tmp_path):
    record = run(tmp_path)
    expected = hashlib.sha256(
        (
            tool._sha(write_spec(tmp_path).read_bytes())
            + record["asset_leg"]["series_sha256"]
            + record["cash_leg"]["series_sha256"]
            + COMMIT
        ).encode()
    ).hexdigest()[:16]
    assert record["build_id"] == expected


# --- determinism and modes


def test_a_second_build_is_already_built(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tool._fb._base, "code_commit", lambda: {"commit": COMMIT})
    asset, cash = legs(tmp_path)
    spec = write_spec(tmp_path)
    args = ["--spec", str(spec), "--asset", str(asset), "--cash", str(cash), "--out", str(tmp_path / "store")]
    assert tool.main(args) == 0
    assert "already built" not in capsys.readouterr().out
    record = tool.build(spec, asset, cash, tmp_path / "store", commit=COMMIT)
    directory = build_dir(tmp_path, record)
    before = [(directory / n).read_bytes() for n in ("series.csv", "build.json")]
    assert tool.main(args) == 0
    assert "already built" in capsys.readouterr().out
    assert [(directory / n).read_bytes() for n in ("series.csv", "build.json")] == before


def test_a_build_directory_with_different_bytes_refuses(tmp_path):
    asset, cash = legs(tmp_path)
    record = run(tmp_path, asset=asset, cash=cash)
    target = build_dir(tmp_path, record) / "series.csv"
    target.write_bytes(b"changed\n")
    with pytest.raises(ValueError, match="different bytes"):
        run(tmp_path, asset=asset, cash=cash)


def test_file_and_directory_modes(tmp_path):
    record = run(tmp_path)
    directory = build_dir(tmp_path, record)
    for name in ("series.csv", "build.json"):
        assert stat.S_IMODE((directory / name).stat().st_mode) == 0o600
    for d in (directory, directory.parent, directory.parent.parent, tmp_path / "store"):
        assert stat.S_IMODE(d.stat().st_mode) == 0o700


def test_the_command_prints_no_return_or_date(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tool._fb._base, "code_commit", lambda: {"commit": COMMIT})
    asset, cash = legs(tmp_path)
    args = ["--spec", str(write_spec(tmp_path)), "--asset", str(asset), "--cash", str(cash)]
    assert tool.main([*args, "--out", str(tmp_path / "store")]) == 0
    out = capsys.readouterr().out
    assert EXCESS in out and "RA-INV-005: pass" in out and "series_sha256:" in out
    for secret in ("2030", "0.0292", "0.0302", "0.02929988", "0.0105"):
        assert secret not in out


# --- refusals


def test_a_tampered_leg_series_refuses(tmp_path):
    asset, cash = legs(tmp_path)
    with (asset / "series.csv").open("a") as handle:
        handle.write("x\n")
    with pytest.raises(ValueError, match="hash"):
        run(tmp_path, asset=asset, cash=cash)


def test_an_excess_return_build_as_a_leg_refuses(tmp_path):
    with pytest.raises(ValueError, match="total_return"):
        run(tmp_path, asset_opts={"series_class": "excess_return"})


def test_a_leg_with_a_failed_invariant_refuses(tmp_path):
    with pytest.raises(ValueError, match="invariant"):
        run(tmp_path, cash_opts={"passed": False})


def test_a_leg_with_the_wrong_factor_id_refuses(tmp_path):
    asset = write_leg(tmp_path, "asset", "equity.other.market_total_return", ASSET_PERIODS)
    cash = write_leg(tmp_path, "cash", CASH, CASH_PERIODS)
    with pytest.raises(ValueError, match="factor_id"):
        run(tmp_path, asset=asset, cash=cash)


def test_legs_with_different_numeraires_refuse(tmp_path):
    with pytest.raises(ValueError, match="numeraire"):
        run(tmp_path, cash_opts={"numeraire": "AUD"})


def test_a_spec_numeraire_that_differs_from_the_legs_refuses(tmp_path):
    with pytest.raises(ValueError, match="numeraire"):
        run(tmp_path, spec=write_spec(tmp_path, numeraire="AUD"))


def test_the_same_build_for_both_legs_refuses(tmp_path):
    asset, _cash = legs(tmp_path)
    with pytest.raises(ValueError, match="same build"):
        run(tmp_path, asset=asset, cash=asset)


def test_fewer_than_two_common_dates_refuses(tmp_path):
    asset = write_leg(tmp_path, "asset", ASSET, [("2030-01-02", "2030-01-03", "0.01")])
    cash = write_leg(tmp_path, "cash", CASH, [("2030-01-03", "2030-01-04", "0.001")])
    with pytest.raises(ValueError, match="two common dates"):
        run(tmp_path, asset=asset, cash=cash)


def test_a_spec_that_is_not_an_excess_return_refuses(tmp_path):
    with pytest.raises(ValueError, match="excess_return"):
        run(tmp_path, spec=write_spec(tmp_path, series_class="total_return"))


def test_a_spec_with_other_than_two_observations_refuses(tmp_path):
    with pytest.raises(ValueError, match="exactly two"):
        run(tmp_path, spec=write_spec(tmp_path, ids=(ASSET, CASH, "x.y")))


def test_a_cash_leg_outside_the_observations_refuses(tmp_path):
    with pytest.raises(ValueError, match="cash leg"):
        run(tmp_path, spec=write_spec(tmp_path, cash="cash.other"))


def test_out_inside_the_repository_refuses(tmp_path):
    with pytest.raises(ValueError, match="outside the repository"):
        run(tmp_path, out=REPO / "store_should_not_exist")
    assert not (REPO / "store_should_not_exist").exists()


def test_main_refuses_with_exit_2(tmp_path, capsys):
    asset, cash = legs(tmp_path)
    args = ["--spec", str(write_spec(tmp_path)), "--asset", str(asset), "--cash", str(cash)]
    assert tool.main([*args, "--out", str(REPO / "store_should_not_exist")]) == 2
    assert "refused:" in capsys.readouterr().err
