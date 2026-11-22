"""The reconstructed AUD cash build (OD-0216), on invented data only."""

import hashlib
import importlib.util
import json
import stat
import sys
from datetime import date
from decimal import Decimal as D
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SPEC = REPO / "specs" / "factors" / "cash.aud.overnight_reconstructed.yaml"
COMMIT = "c" * 40
_spec = importlib.util.spec_from_file_location("factor_cash_aud", REPO / "tools" / "factor_cash_aud.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["factor_cash_aud"] = tool
_spec.loader.exec_module(tool)

HEADER = "period_start,period_end,price_return,income_return,total_return,index\n"
# Thursday, Friday, then Monday: the Friday rate covers the weekend (3 days). Then 8 days to the TRI start.
RATES = [("2010-12-23", "3.65"), ("2010-12-24", "7.30"), ("2010-12-27", "3.65")]
TRI = [("04-Jan-2011", "100.000000"), ("05-Jan-2011", "100.010000"), ("06-Jan-2011", "100.030000")]
TOL = D("1e-20")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f1(rows, series="FIRMMCTRI"):
    head = f"Title,Cash Rate TRI\nSeries ID,{series}\n"
    return (head + "".join(f"{d},{v}\n" for d, v in rows)).encode()


def make_inputs(root: Path, rates=RATES, tri=TRI):
    history, receipt = root / "history", root / "f1"
    (receipt / "raw").mkdir(parents=True)
    history.mkdir()
    rate_body = ("date,rate_pct\n" + "".join(f"{d},{v}\n" for d, v in rates)).encode()
    (history / "firmmcrid.csv").write_bytes(rate_body)
    (history / "extract-manifest.json").write_text(json.dumps({"sha256": sha(rate_body)}))
    tri_body = f1(tri)
    (receipt / "raw" / "rba_f1.csv").write_bytes(tri_body)
    (receipt / "raw" / "manifest.json").write_text(json.dumps({"receipt_id": sha(tri_body)}))
    return history, receipt, sha(rate_body), sha(tri_body)


def run_build(tmp_path, *, spec=SPEC, rates=RATES, tri=TRI, **overrides):
    history, receipt, h_sha, f_sha = make_inputs(tmp_path / "in", rates, tri)
    args = {
        "spec_path": spec,
        "history": history,
        "f1": receipt,
        "history_sha256": h_sha,
        "f1_sha256": f_sha,
        "out": tmp_path / "out",
    }
    args.update(overrides)
    return tool.build(**args, commit=COMMIT), args


def rows_of(tmp_path, record):
    target = tmp_path / "out" / record["factor_id"] / record["spec_version"] / record["build_id"]
    lines = (target / "series.csv").read_text().splitlines()
    return target, [r.split(",") for r in lines[1:]]


def test_the_accrual_is_act_365_to_the_next_published_date_including_a_weekend(tmp_path):
    record, _ = run_build(tmp_path)
    _, rows = rows_of(tmp_path, record)
    pre = rows[:3]
    assert [(r[0], r[1]) for r in pre] == [
        ("2010-12-23", "2010-12-24"),
        ("2010-12-24", "2010-12-27"),
        ("2010-12-27", "2011-01-04"),
    ]
    # 3.65% x 1 day; 7.30% x 3 days (Fri to Mon); 3.65% x 8 days, each over 365
    expected = [D("0.0001"), D("0.0006"), D("0.0008")]
    for row, want in zip(pre, expected, strict=True):
        assert abs(D(row[4]) - want) < TOL


def test_the_join_continues_the_accrual_and_every_post_seam_return_is_the_tri_ratio(tmp_path):
    record, _ = run_build(tmp_path)
    _, rows = rows_of(tmp_path, record)
    accrued = D("1.0001") * D("1.0006") * D("1.0008")
    index_at_seam = D(rows[2][5])
    assert abs(index_at_seam - accrued) < TOL  # the first level is 1, so the index is the accrual level
    post = rows[3:]
    assert [(r[0], r[1]) for r in post] == [("2011-01-04", "2011-01-05"), ("2011-01-05", "2011-01-06")]
    assert abs(D(post[0][4]) - D("0.0001")) < TOL
    assert abs(D(post[1][4]) - (D("100.03") / D("100.01") - 1)) < TOL
    assert abs(D(post[1][5]) - accrued * D("100.03") / D("100")) < TOL
    assert record["seam_date"] == "2011-01-04"
    assert (record["periods_before_seam"], record["periods_from_seam"], record["periods"]) == (3, 2, 5)


def test_the_format_is_exact_and_price_return_is_zero_everywhere(tmp_path):
    record, args = run_build(tmp_path)
    target, rows = rows_of(tmp_path, record)
    raw = (target / "series.csv").read_bytes()
    assert raw.decode().startswith(HEADER)
    assert b"\r" not in raw and raw.endswith(b"\n")
    level = D(1)
    for _s, _e, pr, ir, tr, index in rows:
        assert pr == "0"
        assert D(tr) == D(ir)
        level *= 1 + D(tr)
        assert abs(D(index) - level) < TOL
    build_json = (target / "build.json").read_bytes()
    assert build_json.endswith(b"\n")
    assert build_json.decode() == json.dumps(json.loads(build_json), indent=1, sort_keys=True) + "\n"
    data = json.loads(build_json)
    required = {
        *("factor_id", "spec_version", "spec_sha256", "series_class", "numeraire", "code_commit"),
        *("periods", "first", "last", "invariants", "series_sha256", "build_id", "inputs"),
        *("seam_date", "periods_before_seam", "periods_from_seam"),
    }
    assert required <= set(data)
    assert data["series_class"] == "total_return" and data["numeraire"] == "AUD"
    assert data["factor_id"] == "cash.aud.overnight_reconstructed"
    assert data["source_ids"] == ["rba.cash_rate", "rba.f1_historical"]
    assert data["series_sha256"] == sha(raw)
    assert {i["path"]: i["sha256"] for i in data["inputs"]} == {
        "firmmcrid.csv": args["history_sha256"],
        "raw/rba_f1.csv": args["f1_sha256"],
    }
    assert (data["first"], data["last"]) == ("2010-12-23", "2011-01-06")
    assert all(data["invariants"][n]["passed"] for n in tool.INVARIANTS)
    expected_id = sha((sha(SPEC.read_bytes()) + args["history_sha256"] + args["f1_sha256"] + COMMIT).encode())
    assert data["build_id"] == expected_id[:16]


def test_a_second_build_is_byte_identical_and_already_built(tmp_path):
    record, args = run_build(tmp_path)
    target, _ = rows_of(tmp_path, record)
    before = {p.name: p.read_bytes() for p in target.iterdir()}
    again, existed = tool._build(
        args["spec_path"],
        args["history"],
        args["f1"],
        args["history_sha256"],
        args["f1_sha256"],
        args["out"],
        COMMIT,
    )
    assert existed and again == record
    assert {p.name: p.read_bytes() for p in target.iterdir()} == before


def test_a_different_code_commit_gives_a_different_build_id(tmp_path):
    record, args = run_build(tmp_path)
    other = tool.build(**args, commit="d" * 40)
    assert other["build_id"] != record["build_id"]


def test_a_negative_published_rate_is_counted_not_refused(tmp_path):
    rates = [("2010-12-23", "-1.00"), ("2010-12-24", "3.65"), ("2010-12-27", "3.65")]
    record, _ = run_build(tmp_path, rates=rates)
    assert record["invariants"]["non_negative_before_seam"]["negative"] == 1
    assert record["invariants"]["non_negative_before_seam"]["passed"] is True


def test_invariants_are_recomputed_and_a_tampered_series_fails_them():
    levels = {date(2010, 12, 23): D(1), date(2010, 12, 24): D("1.0001"), date(2010, 12, 25): D("1.010101")}
    tri = {date(2010, 12, 24): D(100), date(2010, 12, 25): D(101)}
    good = tool.render_series(tool.periods_of(levels))
    assert all(r["passed"] for r in tool.check_invariants(good, levels, tri).values())
    lines = good.decode().splitlines(keepends=True)
    cells = lines[2].rstrip("\n").split(",")
    cells[2] = "0.5"  # price_return no longer zero: total != price + income
    bad_ra1 = (lines[0] + lines[1] + ",".join(cells) + "\n").encode()
    assert not tool.check_invariants(bad_ra1, levels, tri)["RA-INV-001"]["passed"]
    cells = lines[2].rstrip("\n").split(",")
    cells[5] = "9"  # index off the chain
    bad_chain = (lines[0] + lines[1] + ",".join(cells) + "\n").encode()
    assert not tool.check_invariants(bad_chain, levels, tri)["index_chain"]["passed"]
    cells = lines[2].rstrip("\n").split(",")
    cells[3] = cells[4] = "0.02"  # the TRI period no longer equals the index's own ratio
    bad_seam = (lines[0] + lines[1] + ",".join(cells) + "\n").encode()
    assert not tool.check_invariants(bad_seam, levels, tri)["seam"]["passed"]
    assert not tool.check_invariants(bad_seam, levels, tri)["level_ratio"]["passed"]


def test_a_pin_that_does_not_match_refuses(tmp_path):
    with pytest.raises(ValueError, match="historical rate file does not match its pin"):
        run_build(tmp_path, history_sha256="0" * 64)
    with pytest.raises(ValueError, match="F1 receipt file does not match its pin"):
        run_build(tmp_path / "second", f1_sha256="0" * 64)


def test_a_manifest_that_does_not_match_its_file_refuses(tmp_path):
    history, receipt, h_sha, f_sha = make_inputs(tmp_path / "in")
    (receipt / "raw" / "manifest.json").write_text(json.dumps({"receipt_id": "0" * 64}))
    with pytest.raises(ValueError, match="does not match its manifest"):
        tool.build(SPEC, history, receipt, h_sha, f_sha, tmp_path / "out", commit=COMMIT)
    (receipt / "raw" / "manifest.json").write_text(json.dumps({"receipt_id": f_sha}))
    (history / "extract-manifest.json").write_text(json.dumps({"sha256": "0" * 64}))
    with pytest.raises(ValueError, match="manifest"):
        tool.build(SPEC, history, receipt, h_sha, f_sha, tmp_path / "out", commit=COMMIT)


@pytest.mark.parametrize(
    ("old", "new", "match"),
    [
        ("series_class: total_return", "series_class: excess_return", "series_class must be total_return"),
        ("numeraire: AUD", "numeraire: USD", "numeraire must be AUD"),
    ],
)
def test_a_spec_outside_scope_refuses(tmp_path, old, new, match):
    spec = tmp_path / "spec.yaml"
    spec.write_text(SPEC.read_text().replace(old, new))
    with pytest.raises(ValueError, match=match):
        run_build(tmp_path, spec=spec)


def test_fewer_than_two_levels_refuses(tmp_path, monkeypatch):
    monkeypatch.setattr(tool._ext, "joined_levels", lambda _a, _t: {date(2011, 1, 4): D(1)})
    with pytest.raises(ValueError, match="fewer than two levels"):
        run_build(tmp_path)


def test_a_non_positive_level_refuses(tmp_path):
    rates = [("2010-12-23", "-40000"), ("2010-12-24", "3.65"), ("2010-12-27", "3.65")]
    with pytest.raises(ValueError, match="not positive"):
        run_build(tmp_path, rates=rates)


def test_dates_that_are_not_strictly_increasing_refuse(tmp_path, monkeypatch):
    unordered = {date(2011, 1, 5): D(100), date(2011, 1, 4): D(101), date(2011, 1, 6): D(102)}
    monkeypatch.setattr(tool._cash, "parse_tri", lambda _body: unordered)
    with pytest.raises(ValueError, match="strictly increasing"):
        run_build(tmp_path)


def test_a_failed_invariant_refuses(tmp_path, monkeypatch):
    failing = {"seam": {"checked": 1, "passed": False}}
    monkeypatch.setattr(tool, "check_invariants", lambda *_a: failing)
    with pytest.raises(ValueError, match="invariants failed: seam"):
        run_build(tmp_path)


def test_no_rate_before_the_first_index_level_refuses(tmp_path):
    with pytest.raises(ValueError, match="no historical rate before"):
        run_build(tmp_path, rates=[("2011-01-04", "3.65")])


def test_out_inside_the_repository_refuses(tmp_path):
    with pytest.raises(ValueError, match="outside the repository"):
        run_build(tmp_path, out=REPO / "not-created-by-the-test")
    assert not (REPO / "not-created-by-the-test").exists()


def test_files_are_0600_and_directories_0700(tmp_path):
    record, _ = run_build(tmp_path)
    target, _ = rows_of(tmp_path, record)
    for path in (target / "series.csv", target / "build.json"):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    directory = target
    while directory != tmp_path / "out":
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        directory = directory.parent


def cli(tmp_path, capsys, monkeypatch, **overrides):
    monkeypatch.setattr(tool._fb._base, "code_commit", lambda: {"commit": COMMIT})
    history, receipt, h_sha, f_sha = make_inputs(tmp_path / "in")
    argv = [
        "--spec",
        str(SPEC),
        "--history",
        str(history),
        "--f1",
        str(receipt),
        "--history-sha256",
        overrides.get("h", h_sha),
        "--f1-sha256",
        f_sha,
        "--out",
        str(overrides.get("out", tmp_path / "out")),
    ]
    code = tool.main(argv)
    return code, capsys.readouterr()


def test_the_command_prints_no_rate_return_or_date_and_says_already_built(tmp_path, capsys, monkeypatch):
    code, out = cli(tmp_path, capsys, monkeypatch)
    assert code == 0
    for forbidden in ("2010", "2011", "3.65", "7.30", "100.0", "0.0001", "0.0006", "0.0008"):
        assert forbidden not in out.out + out.err
    assert "factor_id: cash.aud.overnight_reconstructed" in out.out
    assert "RA-INV-001: pass" in out.out and "already built" not in out.out
    again = tool.main(
        [
            "--spec",
            str(SPEC),
            "--history",
            str(tmp_path / "in" / "history"),
            "--f1",
            str(tmp_path / "in" / "f1"),
            "--history-sha256",
            sha((tmp_path / "in" / "history" / "firmmcrid.csv").read_bytes()),
            "--f1-sha256",
            sha((tmp_path / "in" / "f1" / "raw" / "rba_f1.csv").read_bytes()),
            "--out",
            str(tmp_path / "out"),
        ]
    )
    assert again == 0
    assert "already built" in capsys.readouterr().out


def test_the_command_refuses_with_exit_2(tmp_path, capsys, monkeypatch):
    code, out = cli(tmp_path, capsys, monkeypatch, h="0" * 64)
    assert code == 2
    assert out.err.startswith("refused: ValueError:")
    code, out = cli(tmp_path / "b", capsys, monkeypatch, out=REPO / "not-created-by-the-test")
    assert code == 2 and "refused" in out.err
