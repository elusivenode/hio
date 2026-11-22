"""Lake catalogue: build and verify over invented bronze, silver and gold trees (no git, no network)."""

import hashlib
import importlib.util
import json
import re
import stat
from datetime import date
from pathlib import Path

import duckdb
import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("lake_catalogue", REPO / "tools" / "lake_catalogue.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

SERIES_ONE = (
    "period_start,period_end,total_return,price_return\n"
    "2030-01-01,2030-01-31,0.0100,-0.5000\n"
    "2030-02-01,2030-02-28,,1e-05\n"
)
SERIES_TWO = "period_start,period_end,excess\n2030-01-01,2030-01-31,0.0025\n"
SERIES_THREE = (
    "period_start,period_end,total_return\n2030-01-01,2030-01-31,0.0300\n2030-02-01,2030-02-28,0.0400\n"
)
GOLD_ONE, GOLD_TWO, GOLD_THREE, GOLD_ABSENT = ("a1" * 8, "b2" * 8, "c3" * 8, "d4" * 8)
SILVER_ID = "e5" * 8
SNAPSHOT = "snap-one"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: Path, data: bytes | str) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = data.encode() if isinstance(data, str) else data
    path.write_bytes(raw)
    return raw


def make_bronze(root: Path, snapshot: str = SNAPSHOT, *, files=None) -> str:
    """Write raw/<snapshot> with the given {name: bytes} files; returns the snapshot's manifest sha256."""
    files = files if files is not None else {"eod.json": b'[{"date": "2030-01-01"}]', "div.json": b"[]"}
    entries = []
    for name, data in sorted(files.items()):
        write(root / "raw" / snapshot / name, data)
        entries.append(
            {
                "path": f"raw/{snapshot}/{name}",
                "sha256": sha(data),
                "bytes": len(data),
                "kind": name.split(".")[0],
                "symbol": "ZZZ.US",
                "retrieved_at": "2030-03-01T00:00:00Z",
                "request": {"endpoint": "eod", "n": 1},
            }
        )
    manifest = {
        "snapshot": snapshot,
        "source_id": "some.source",
        "code_commit": "f" * 40,
        "stopped": None,
        "files": entries,
    }
    return sha(write(root / "raw" / snapshot / "manifest.json", json.dumps(manifest, indent=1)))


def make_silver(
    root: Path, snapshot_sha: str, silver_id: str = SILVER_ID, instrument: str = "ZZZ.US"
) -> Path:
    directory = root / instrument / silver_id
    csv_files = {
        "closes.csv": "date,close,adjusted_close\n2030-01-01,102.5000,\n2030-01-02,103.0000,51.5000\n",
        "distributions.csv": (
            "ex_date,amount,split_adjusted_amount,currency,payment_date,record_date,declaration_date,period\n"
            "2030-01-02,0.2500,0.1250,USD,,,,Quarterly\n"
        ),
        "splits.csv": "date,ratio\n2030-01-02,2.000000/1.000000\n",
    }
    files = {}
    for name, text in csv_files.items():
        raw = write(directory / name, text)
        files[name] = {"sha256": sha(raw), "rows": text.count("\n") - 1}
    manifest = {
        "schema": "hio.silver/1",
        "instrument": instrument,
        "quote_currency": "USD",
        "source_id": "some.source",
        "observation_spec": {"version": "0.1.0", "sha256": "9" * 64},
        "snapshot": SNAPSHOT,
        "snapshot_manifest_sha256": snapshot_sha,
        "inputs": [],
        "corrections": [
            {"action": "exclude_distribution", "ex_date": "2030-01-09", "record_sha256": "8" * 64}
        ],
        "code_commit": "f" * 40,
        "files": files,
        "first": "2030-01-01",
        "last": "2030-01-02",
        "silver_id": silver_id,
    }
    write(directory / "manifest.json", json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return directory


def make_gold(
    root: Path, build_id: str, series: str, factor_id: str = "ZZZ_TR", version: str = "0.1.0", **extra
):
    rows = [line for line in series.splitlines()[1:] if line]
    record = {
        "factor_id": factor_id,
        "spec_version": version,
        "build_id": build_id,
        "series_class": "total_return",
        "numeraire": "USD",
        "spec_sha256": "7" * 64,
        "code_commit": "f" * 40,
        "periods": len(rows),
        "first": "2030-01-01",
        "last": "2030-02-28",
        "series_sha256": sha(series.encode()),
        **extra,
    }
    directory = root / factor_id / version / build_id
    write(directory / "series.csv", series)
    write(directory / "build.json", json.dumps(record, indent=1, sort_keys=True) + "\n")
    return directory


@pytest.fixture
def lake(tmp_path):
    """Bronze (two roots), silver and gold trees: every lineage case, one parent absent."""
    bronze_a, bronze_b = tmp_path / "bronze-a", tmp_path / "bronze-b"
    snapshot_sha = make_bronze(bronze_a)
    other_sha = make_bronze(bronze_b, "snap-two", files={"eod.json": b"[]"})
    silver = tmp_path / "silver"
    make_silver(silver, snapshot_sha)
    gold = tmp_path / "gold"
    make_gold(
        gold,
        GOLD_ONE,
        SERIES_ONE,
        input_layer="silver",
        silver={"silver_id": SILVER_ID, "manifest_sha256": "1" * 64},
        snapshot_manifest_sha256=snapshot_sha,
        inputs=[{"path": "ZZZ.US/x/closes.csv", "sha256": "2" * 64}],
    )
    make_gold(
        gold,
        GOLD_TWO,
        SERIES_TWO,
        factor_id="ZZZ_EX",
        asset_leg={"build_id": GOLD_ONE, "factor_id": "ZZZ_TR", "series_sha256": "3" * 64},
        cash_leg={"build_id": GOLD_ABSENT, "factor_id": "CASH", "series_sha256": "4" * 64},
        inputs=[
            {"role": "companion", "build_id": GOLD_THREE, "factor_id": "ZZZ_B", "series_sha256": "5" * 64},
            {"build_id": GOLD_ONE, "factor_id": "ZZZ_TR", "series_sha256": "3" * 64},
        ],
    )
    make_gold(gold, GOLD_THREE, SERIES_THREE, factor_id="ZZZ_B", snapshot_manifest_sha256=snapshot_sha)
    return {
        "bronze": [bronze_a, bronze_b],
        "silver": silver,
        "gold": gold,
        "snapshot_sha": snapshot_sha,
        "other_sha": other_sha,
        "tmp": tmp_path,
    }


def roots(lake):
    return lake["bronze"], lake["silver"], lake["gold"]


def table(path: Path, query: str):
    con = duckdb.connect(str(path), read_only=True)
    try:
        return con.execute(query).fetchall()
    finally:
        con.close()


def contents(path: Path) -> dict:
    names = [r[0] for r in table(path, "SHOW TABLES")]
    return {n: sorted(map(repr, table(path, f"SELECT * FROM {n}"))) for n in names}


def test_counts_and_exact_rows(lake):
    out = lake["tmp"] / "out" / "catalogue.duckdb"
    report = tool.build(*roots(lake), out)
    assert report == {
        "counts": {
            "bronze_snapshot": 2,
            "bronze_file": 3,
            "silver_set": 1,
            "silver_file": 3,
            "gold_build": 3,
            "gold_series": 4 + 1 + 2,
            "lineage": 8,
            "problem": 0,
        },
        "problems": 0,
        "result": "pass",
    }
    snap = table(out, "SELECT * FROM bronze_snapshot WHERE snapshot = 'snap-one'")
    assert snap == [
        (
            lake["snapshot_sha"],
            "snap-one",
            "some.source",
            "f" * 40,
            None,
            str(lake["bronze"][0] / "raw" / "snap-one"),
        )
    ]
    assert table(
        out,
        "SELECT path, sha256, bytes, kind, symbol, retrieved_at, request "
        "FROM bronze_file WHERE path LIKE '%div.json'",
    ) == [
        (
            "raw/snap-one/div.json",
            sha(b"[]"),
            2,
            "div",
            "ZZZ.US",
            "2030-03-01T00:00:00Z",
            '{"endpoint": "eod", "n": 1}',
        )
    ]
    assert table(
        out,
        "SELECT silver_id, instrument, quote_currency, source_id, observation_spec_version, snapshot, "
        "corrections, first, last FROM silver_set",
    ) == [(SILVER_ID, "ZZZ.US", "USD", "some.source", "0.1.0", "snap-one", 1, "2030-01-01", "2030-01-02")]
    assert table(out, "SELECT name, row_count FROM silver_file ORDER BY name") == [
        ("closes.csv", 2),
        ("distributions.csv", 1),
        ("splits.csv", 1),
    ]
    build = table(
        out,
        "SELECT build_id, factor_id, spec_version, series_class, numeraire, periods, first, last, "
        f"input_layer FROM gold_build WHERE build_id = '{GOLD_ONE}'",
    )
    assert build == [
        (GOLD_ONE, "ZZZ_TR", "0.1.0", "total_return", "USD", 2, "2030-01-01", "2030-02-28", "silver")
    ]
    assert table(out, f"SELECT input_layer FROM gold_build WHERE build_id = '{GOLD_TWO}'") == [(None,)]
    record_json = table(out, f"SELECT record_json FROM gold_build WHERE build_id = '{GOLD_ONE}'")[0][0]
    assert json.loads(record_json)["silver"]["silver_id"] == SILVER_ID
    assert record_json == (lake["gold"] / "ZZZ_TR" / "0.1.0" / GOLD_ONE / "build.json").read_text()
    assert table(out, "SELECT * FROM problem") == []


def test_value_text_exact_and_value_numeric(lake):
    out = lake["tmp"] / "catalogue.duckdb"
    tool.build(*roots(lake), out)
    rows = table(
        out,
        "SELECT period_start, period_end, measure, value_text, value FROM gold_series "
        f"WHERE build_id = '{GOLD_ONE}' ORDER BY period_start, measure",
    )
    assert rows == [
        (date(2030, 1, 1), date(2030, 1, 31), "price_return", "-0.5000", -0.5),
        (date(2030, 1, 1), date(2030, 1, 31), "total_return", "0.0100", 0.01),
        (date(2030, 2, 1), date(2030, 2, 28), "price_return", "1e-05", 1e-05),
        (date(2030, 2, 1), date(2030, 2, 28), "total_return", "", None),
    ]
    assert table(out, f"SELECT DISTINCT factor_id FROM gold_series WHERE build_id = '{GOLD_ONE}'") == [
        ("ZZZ_TR",)
    ]


def test_every_lineage_case_and_parent_present(lake):
    out = lake["tmp"] / "catalogue.duckdb"
    tool.build(*roots(lake), out)
    rows = set(
        table(out, "SELECT child_kind, child_id, parent_kind, parent_id, role, parent_present FROM lineage")
    )
    assert rows == {
        # silver set -> its bronze snapshot (present)
        ("silver", SILVER_ID, "bronze", lake["snapshot_sha"], "bronze", True),
        # gold from silver: the silver parent only (not also the bronze one), plus a file input
        ("gold", GOLD_ONE, "silver", SILVER_ID, "silver", True),
        ("gold", GOLD_ONE, "file", "2" * 64, "input", None),
        # gold with legs and inputs: present, absent, roled input, default-role input
        ("gold", GOLD_TWO, "gold", GOLD_ONE, "asset_leg", True),
        ("gold", GOLD_TWO, "gold", GOLD_ABSENT, "cash_leg", False),
        ("gold", GOLD_TWO, "gold", GOLD_THREE, "companion", True),
        ("gold", GOLD_TWO, "gold", GOLD_ONE, "input", True),
        # gold straight from bronze
        ("gold", GOLD_THREE, "bronze", lake["snapshot_sha"], "bronze", True),
    }
    assert len(rows) == 8


def test_parent_absent_when_not_loaded(lake):
    out = lake["tmp"] / "catalogue.duckdb"
    report = tool.build([], lake["silver"], lake["gold"], out)
    assert report["counts"]["bronze_snapshot"] == 0
    flags = table(out, "SELECT parent_present FROM lineage WHERE parent_kind = 'bronze'")
    assert flags == [(False,), (False,)]


def test_a_tampered_silver_set_is_an_absent_parent(lake):
    out = lake["tmp"] / "catalogue.duckdb"
    tool.build(lake["bronze"], lake["silver"], lake["gold"], out)
    (lake["silver"] / "ZZZ.US" / SILVER_ID / "closes.csv").write_bytes(b"tampered\n")
    report = tool.build(lake["bronze"], lake["silver"], lake["gold"], out)
    assert report["counts"]["silver_set"] == 0
    flags = table(
        out, f"SELECT parent_present FROM lineage WHERE parent_kind = 'silver' AND parent_id = '{SILVER_ID}'"
    )
    assert flags == [(False,)]


def test_same_snapshot_in_two_roots_loads_once(lake):
    twin = lake["tmp"] / "bronze-twin"
    make_bronze(twin)
    report = tool.verify([*lake["bronze"], twin], lake["silver"], lake["gold"])
    assert report["counts"]["bronze_snapshot"] == 2
    assert report["problems"] == 0


def problems(out: Path) -> list[tuple]:
    return table(out, "SELECT layer, id, problem FROM problem ORDER BY layer, id")


def test_tampered_bronze_file_is_reported_and_excluded(lake):
    (lake["bronze"][0] / "raw" / "snap-one" / "eod.json").write_bytes(b"[]")
    out = lake["tmp"] / "catalogue.duckdb"
    report = tool.build(*roots(lake), out)
    assert report["result"] == "fail" and report["problems"] == 1
    assert problems(out) == [
        ("bronze", "snap-one", "file raw/snap-one/eod.json: sha256 differs from the manifest")
    ]
    assert table(out, "SELECT snapshot FROM bronze_snapshot") == [("snap-two",)]
    assert table(out, "SELECT DISTINCT snapshot_manifest_sha256 FROM bronze_file") == [(lake["other_sha"],)]
    assert table(out, "SELECT count(*) FROM gold_build") == [(3,)]


def test_missing_bronze_file(lake):
    (lake["bronze"][0] / "raw" / "snap-one" / "div.json").unlink()
    report = tool.verify(*roots(lake))
    assert report["problems"] == 1 and report["counts"]["bronze_snapshot"] == 1


def test_bronze_directory_name_and_unsafe_path(lake):
    (lake["bronze"][0] / "raw" / "snap-one").rename(lake["bronze"][0] / "raw" / "renamed")
    out = lake["tmp"] / "catalogue.duckdb"
    tool.build(*roots(lake), out)
    assert problems(out) == [("bronze", "renamed", "directory name disagrees with the manifest's snapshot")]
    other = lake["tmp"] / "bronze-c"
    manifest = {
        "snapshot": "s",
        "source_id": "x",
        "code_commit": "c",
        "stopped": None,
        "files": [{"path": "../x", "sha256": "0" * 64}],
    }
    write(other / "raw" / "s" / "manifest.json", json.dumps(manifest))
    report = tool.verify([other], None, None)
    assert report["problems"] == 1 and report["counts"]["bronze_snapshot"] == 0


def test_unparseable_json_in_each_layer(lake):
    write(lake["bronze"][1] / "raw" / "snap-two" / "manifest.json", "{not json")
    write(lake["silver"] / "ZZZ.US" / SILVER_ID / "manifest.json", "[1, 2]")
    write(lake["gold"] / "ZZZ_B" / "0.1.0" / GOLD_THREE / "build.json", b"\xff\xfe")
    out = lake["tmp"] / "catalogue.duckdb"
    report = tool.build(*roots(lake), out)
    assert problems(out) == [
        ("bronze", "snap-two", "manifest.json is not parseable JSON"),
        ("gold", GOLD_THREE, "build.json is not parseable JSON"),
        ("silver", SILVER_ID, "manifest.json is not a JSON object"),
    ]
    assert report["counts"]["gold_build"] == 2 and report["counts"]["silver_set"] == 0
    assert report["counts"]["bronze_snapshot"] == 1


def test_silver_problems(lake):
    silver = lake["silver"]
    (silver / "ZZZ.US" / SILVER_ID / "splits.csv").unlink()
    assert tool.verify(*roots(lake))["problems"] == 1
    make_silver(silver, lake["snapshot_sha"])
    (silver / "ZZZ.US").rename(silver / "OTHER.US")
    out = lake["tmp"] / "catalogue.duckdb"
    tool.build(*roots(lake), out)
    assert problems(out) == [
        ("silver", SILVER_ID, "instrument directory disagrees with the manifest's instrument")
    ]
    (silver / "OTHER.US" / SILVER_ID).rename(silver / "OTHER.US" / ("0" * 16))
    tool.build(*roots(lake), out)
    assert problems(out) == [("silver", "0" * 16, "directory name disagrees with the manifest's silver_id")]


def test_gold_problems_tampered_missing_directory_and_row_count(lake):
    gold = lake["gold"]
    (gold / "ZZZ_TR" / "0.1.0" / GOLD_ONE / "series.csv").write_text(SERIES_ONE.replace("0.0100", "0.0101"))
    (gold / "ZZZ_EX" / "0.1.0" / GOLD_TWO / "series.csv").unlink()
    wrong_dir = make_gold(gold, "9f" * 8, SERIES_THREE, factor_id="ZZZ_B", version="0.2.0")
    wrong_dir.rename(gold / "ZZZ_B" / "0.2.0" / ("9e" * 8))
    short = make_gold(gold, "7a" * 8, SERIES_THREE, factor_id="ZZZ_S")
    record = json.loads((short / "build.json").read_text())
    record["periods"] = 5
    (short / "build.json").write_text(json.dumps(record))
    out = lake["tmp"] / "catalogue.duckdb"
    report = tool.build(*roots(lake), out)
    assert report["problems"] == 4 and report["result"] == "fail"
    assert problems(out) == [
        ("gold", "7a" * 8, "series.csv row count disagrees with periods"),
        ("gold", "9e" * 8, "directory name disagrees with the record's build_id"),
        ("gold", GOLD_ONE, "series.csv sha256 differs from the record"),
        ("gold", GOLD_TWO, "series.csv missing"),
    ]
    assert table(out, "SELECT build_id FROM gold_build") == [(GOLD_THREE,)]
    assert {r[0] for r in table(out, "SELECT DISTINCT build_id FROM gold_series")} == {GOLD_THREE}
    # a lineage row exists only for the good bundles
    assert {r[0] for r in table(out, "SELECT DISTINCT child_id FROM lineage WHERE child_kind = 'gold'")} == {
        GOLD_THREE
    }


def test_gold_directory_disagreements_on_factor_and_version(lake):
    gold = lake["gold"]
    (gold / "ZZZ_B").rename(gold / "ZZZ_RENAMED")
    (gold / "ZZZ_EX" / "0.1.0").rename(gold / "ZZZ_EX" / "9.9.9")
    out = lake["tmp"] / "catalogue.duckdb"
    tool.build(*roots(lake), out)
    assert problems(out) == [
        ("gold", GOLD_TWO, "directory name disagrees with the record's spec_version"),
        ("gold", GOLD_THREE, "directory name disagrees with the record's factor_id"),
    ]


def test_gold_missing_fields_and_bad_series_header(lake):
    gold = lake["gold"]
    directory = gold / "ZZZ_TR" / "0.1.0" / GOLD_ONE
    record = json.loads((directory / "build.json").read_text())
    del record["numeraire"]
    (directory / "build.json").write_text(json.dumps(record))
    bad = make_gold(gold, "6b" * 8, "start,end,x\n2030-01-01,2030-01-31,1\n", factor_id="ZZZ_H")
    assert bad.is_dir()
    out = lake["tmp"] / "catalogue.duckdb"
    tool.build(*roots(lake), out)
    assert problems(out) == [
        ("gold", "6b" * 8, "series.csv does not start with period_start,period_end"),
        ("gold", GOLD_ONE, "record lacks numeraire"),
    ]


def test_absent_and_empty_roots(tmp_path):
    out = tmp_path / "catalogue.duckdb"
    (tmp_path / "empty").mkdir()
    report = tool.build(
        [tmp_path / "nowhere", tmp_path / "empty"], tmp_path / "no-silver", tmp_path / "empty", out
    )
    assert report["result"] == "pass" and report["problems"] == 0
    assert set(report["counts"].values()) == {0}
    assert [r[0] for r in table(out, "SHOW TABLES")] == sorted(tool.TABLES)
    assert tool.verify([], None, None)["result"] == "pass"


def test_root_that_is_a_file_is_refused(tmp_path):
    (tmp_path / "f").write_text("x")
    with pytest.raises(ValueError, match="not a directory"):
        tool.verify([], tmp_path / "f", None)


def test_rebuild_after_delete_gives_the_same_contents(lake):
    out = lake["tmp"] / "catalogue.duckdb"
    tool.build(*roots(lake), out)
    first = contents(out)
    out.unlink()
    tool.build(*roots(lake), out)
    assert contents(out) == first
    assert first["gold_series"]


def test_build_replaces_and_leaves_no_temporary_file(lake):
    out = lake["tmp"] / "catalogue.duckdb"
    out.write_bytes(b"not a database")
    tool.build(*roots(lake), out)
    assert table(out, "SELECT count(*) FROM gold_build") == [(3,)]
    assert sorted(p.name for p in lake["tmp"].iterdir() if p.name.startswith("catalogue")) == [
        "catalogue.duckdb"
    ]
    assert stat.S_IMODE(out.stat().st_mode) == 0o600


def test_new_output_directories_are_private(lake):
    out = lake["tmp"] / "new" / "deeper" / "catalogue.duckdb"
    tool.build(*roots(lake), out)
    for directory in (out.parent, out.parent.parent):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700


def test_out_inside_the_repository_is_refused(lake):
    target = REPO / "tests" / "never-written.duckdb"
    with pytest.raises(ValueError, match="outside the repository"):
        tool.build(*roots(lake), target)
    assert not target.exists()
    assert (
        tool.main(
            [
                "build",
                "--silver-root",
                str(lake["silver"]),
                "--gold-root",
                str(lake["gold"]),
                "--out",
                str(target),
            ]
        )
        == 2
    )
    assert not target.exists()


def test_out_that_is_a_directory_is_refused(lake):
    with pytest.raises(ValueError, match="directory"):
        tool.build(*roots(lake), lake["tmp"])


def test_verify_writes_nothing_and_leaves_the_tree_unchanged(lake):
    before = sorted(p.relative_to(lake["tmp"]).as_posix() for p in lake["tmp"].rglob("*"))
    assert tool.verify(*roots(lake))["result"] == "pass"
    assert sorted(p.relative_to(lake["tmp"]).as_posix() for p in lake["tmp"].rglob("*")) == before


def test_first_and_last_columns_are_queryable_unquoted(lake):
    out = lake["tmp"] / "catalogue.duckdb"
    tool.build(*roots(lake), out)
    assert table(out, "SELECT min(first), max(last) FROM gold_build") == [("2030-01-01", "2030-02-28")]


def cli_args(lake, command, *extra):
    args = [command]
    for root in lake["bronze"]:
        args += ["--bronze-root", str(root)]
    return [*args, "--silver-root", str(lake["silver"]), "--gold-root", str(lake["gold"]), *extra]


DATE_OR_DECIMAL = re.compile(r"\d{4}-\d{2}-\d{2}|\d+\.\d+")


def test_cli_build_and_verify_print_counts_only(lake, capsys):
    out = lake["tmp"] / "catalogue.duckdb"
    assert tool.main(cli_args(lake, "build", "--out", str(out))) == 0
    built = capsys.readouterr()
    assert tool.main(cli_args(lake, "verify")) == 0
    verified = capsys.readouterr()
    assert built.out == verified.out
    assert built.out.splitlines() == [
        "bronze_snapshot: 2",
        "bronze_file: 3",
        "silver_set: 1",
        "silver_file: 3",
        "gold_build: 3",
        "gold_series: 7",
        "lineage: 8",
        "problem: 0",
        "problems: 0",
        "pass",
    ]
    for stream in (built.out, built.err, verified.out, verified.err):
        assert not DATE_OR_DECIMAL.search(stream)


def test_cli_fails_with_one_when_there_is_a_problem_but_still_writes(lake, capsys):
    (lake["gold"] / "ZZZ_TR" / "0.1.0" / GOLD_ONE / "series.csv").write_text("period_start,period_end\n")
    out = lake["tmp"] / "catalogue.duckdb"
    assert tool.main(cli_args(lake, "build", "--out", str(out))) == 1
    text = capsys.readouterr()
    assert text.out.splitlines()[-2:] == ["problems: 1", "fail"]
    assert not DATE_OR_DECIMAL.search(text.out + text.err)
    assert table(out, "SELECT count(*) FROM gold_build") == [(2,)]
    assert tool.main(cli_args(lake, "verify")) == 1


def test_cli_refusals(lake, capsys):
    assert tool.main(cli_args(lake, "build")) == 2
    assert "refused: --out is required with build" in capsys.readouterr().err
    assert tool.main(cli_args(lake, "verify", "--out", str(lake["tmp"] / "x.duckdb"))) == 2
    assert "refused: --out is not valid with verify" in capsys.readouterr().err


def test_cli_absent_roots(tmp_path, capsys):
    argv = ["verify", "--silver-root", str(tmp_path / "s"), "--gold-root", str(tmp_path / "g")]
    assert tool.main(argv) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "pass"
