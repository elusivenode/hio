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
            **dict.fromkeys(tool.TABLES, 0),  # the silver version 2 tables: this lake has no release
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
    assert [r[0] for r in table(out, "SHOW TABLES")] == sorted([*tool.TABLES, *tool.VIEWS])
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
        *[f"{name}: 0" for name in tool.TABLES if name.startswith(("silver2_", "s2_"))],
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


# ---- silver version 2 -------------------------------------------------------------------------------------

silver2 = tool.silver2
SERIES_BAR, SERIES_DIST = "ZZZ.US.bar_day", "ZZZ.US.distribution"
SNAP_ABSENT = "ab" * 32  # a snapshot pin that no loaded bronze root holds
SOURCE_RECORDS = [silver2.source_record_id("5" * 64, i) for i in range(3)]


def fact_row(table, series_id, coordinate, cells, anchor, origin, **extra):
    """One fact row with real keys; every column not given is the empty cell."""
    measures = {c: cells.get(c, "") for c in silver2.MEASURES[table]}
    observation = silver2.observation_id(series_id, coordinate)
    row = dict.fromkeys(silver2.TABLES[table], "")
    row.update(cells)
    row.update(extra)
    row.update(
        vintage_id=silver2.vintage_id(observation, silver2.value_fingerprint(measures), anchor),
        observation_id=observation,
        series_id=series_id,
        series_sk=silver2.sk("series", {"series_id": series_id}, {"definition": "1"}),
        anchor_snapshot_id=anchor,
        origin_source_record_id=origin,
        first_captured_at="2030-03-01T00:00:00Z",
    )
    return row


def make_release(root: Path, snapshot_sha: str, *, close="102.5000", commit="f" * 40, name="Example Fund"):
    """Write one small silver version 2 release under `root`/v2; its first snapshot is `snapshot_sha`, its
    second one is not in any bronze root. Returns the facts the tests look at."""
    snaps = [snapshot_sha, SNAP_ABSENT]
    capture = dict(zip(snaps, (1, 2), strict=True))
    instrument = {"instrument_code": "example-fund"}
    inst_sk = silver2.sk(
        "instrument", instrument, {"attributes_sha256": silver2.attributes_sha256({"n": "1"})}
    )
    listing_sk = silver2.sk("listing", {**instrument, "mic": "XXXX", "ticker": "ZZZ", "valid_from": ""})
    bars = [
        fact_row(
            "fact_listing_bar_day",
            SERIES_BAR,
            {"trade_date": "2030-01-01"},
            {
                "open": "100",
                "high": "103.25",
                "low": "99.5",
                "close": close,
                "volume": "",
                "trade_date": "2030-01-01",
            },
            snapshot_sha,
            SOURCE_RECORDS[0],
            listing_sk=listing_sk,
            instrument_sk=inst_sk,
        ),
        fact_row(
            "fact_listing_bar_day",
            SERIES_BAR,
            {"trade_date": "2030-01-02"},
            {
                "open": "1",
                "high": "2",
                "low": "1",
                "close": "1.5",
                "volume": "1200",
                "trade_date": "2030-01-02",
            },
            SNAP_ABSENT,
            SOURCE_RECORDS[1],
            listing_sk=listing_sk,
            instrument_sk=inst_sk,
        ),
    ]
    distribution = fact_row(
        "fact_distribution_event",
        SERIES_DIST,
        {"ex_date": "2030-01-02", "occurrence": 0},
        {
            "ex_date": "2030-01-02",
            "occurrence": "0",
            "amount_unadjusted": "0.2500",
            "amount_split_adjusted": "0.1250",
            "currency": "USD",
            "period_label": "Quarterly",
            "franking": "",
        },
        snapshot_sha,
        SOURCE_RECORDS[2],
        instrument_sk=inst_sk,
    )
    rows = {name_: [] for name_ in silver2.TABLES}
    rows["fact_listing_bar_day"] = bars
    rows["fact_distribution_event"] = [distribution]
    rows["dim_instrument"] = [
        {
            "instrument_sk": inst_sk,
            "instrument_code": "example-fund",
            "name": name,
            "issuer_code": "example-issuer",
            "vehicle_type": "etf",
            "domicile": "US",
        }
    ]
    rows["dim_listing"] = [
        {
            "listing_sk": listing_sk,
            "instrument_code": "example-fund",
            "instrument_sk": inst_sk,
            "mic": "XXXX",
            "ticker": "ZZZ",
            "valid_from": "",
            "quote_currency": "USD",
        }
    ]
    rows["dim_series"] = [
        {
            "series_sk": bar["series_sk"],
            "series_id": bar["series_id"],
            "source_id": "some.source",
            "source_symbol": "ZZZ.US",
            "quantity": quantity,
        }
        for bar, quantity in ((bars[0], "bar_day"), (distribution, "distribution"))
    ]
    rows["source_identity_mapping"] = [
        {
            "source_id": "some.source",
            "source_symbol": "ZZZ.US",
            "instrument_code": "example-fund",
            "listing_sk": listing_sk,
        }
    ]
    rows["snapshot"] = [
        {
            "snapshot_id": snap,
            "name": f"s{order}",
            "source_id": "some.source",
            "capture_order": str(order),
            "first_retrieved_at": "2030-03-01T00:00:00Z",
            "last_retrieved_at": "2030-03-01T00:00:00Z",
        }
        for snap, order in capture.items()
    ]
    rows["source_record"] = [
        {"source_record_id": rid, "file_sha256": "5" * 64, "row_index": str(i), "record_sha256": "6" * 64}
        for i, rid in enumerate(SOURCE_RECORDS)
    ]
    data = {n: silver2.table_bytes(n, r, capture) for n, r in rows.items()}
    policy = silver2.selection_policy_bytes("compat-v1", {"ZZZ.US": snapshot_sha}, [])
    selection_rows = [
        {
            "fact_table": "fact_listing_bar_day",
            "series_id": SERIES_BAR,
            "observation_id": bar["observation_id"],
            "vintage_id": bar["vintage_id"],
            "source_record_id": bar["origin_source_record_id"],
            "row_index": str(index),
            "disposition": "selected",
            "reason": "",
        }
        for index, bar in zip((2, 10), bars, strict=True)
    ]
    selections = {silver2.selection_id(policy): (policy, silver2.selection_bytes(selection_rows))}
    core = silver2.manifest_core(
        release_spec={"name": "funds", "version": "0.1.0", "sha256": "1" * 64},
        register_sha256="2" * 64,
        observation_specs=[{"source_symbol": "ZZZ.US", "sha256": "3" * 64}],
        snapshots=[{"name": f"s{capture[s]}", "manifest_sha256": s} for s in snaps],
        code_commit=commit,
        tables=data,
        selections=selections,
    )
    directory, existed = silver2.write_release(root, core, data, selections)
    assert not existed
    return {
        "id": silver2.release_id(core),
        "dir": directory,
        "core": core,
        "selection_id": silver2.selection_id(policy),
        "bars": bars,
        "distribution": distribution,
        "listing_sk": listing_sk,
        "instrument_sk": inst_sk,
        "snapshots": snaps,
    }


@pytest.fixture
def lake2(lake):
    """The lake plus one release whose first snapshot is loaded (bronze-a) and whose second is not."""
    lake["release"] = make_release(lake["silver"], lake["snapshot_sha"])
    return lake


def build2(lake, name="catalogue.duckdb"):
    out = lake["tmp"] / name
    return tool.build(*roots(lake), out), out


def test_a_release_fills_the_new_tables(lake2):
    release = lake2["release"]
    rid = release["id"]
    report, out = build2(lake2)
    assert report["problems"] == 0 and report["result"] == "pass"
    for name in silver2.TABLES:
        assert (
            report["counts"][f"s2_{name}"] == {e["name"]: e["rows"] for e in release["core"]["tables"]}[name]
        )
    assert report["counts"]["silver2_release"] == 1
    assert report["counts"]["silver2_selection"] == 1
    assert report["counts"]["silver2_selection_row"] == 2
    assert report["counts"]["s2_fact_listing_bar_day"] == 2
    assert report["counts"]["s2_dim_listing"] == 1
    assert table(
        out,
        "SELECT release_id, release_name, release_version, code_commit, register_sha256, directory "
        "FROM silver2_release",
    ) == [(rid, "funds", "0.1.0", "f" * 40, "2" * 64, str(release["dir"]))]
    core_json = table(out, "SELECT core_json FROM silver2_release")[0][0]
    assert core_json.encode() == tool.canonical_json(release["core"])
    assert silver2.release_id(json.loads(core_json)) == rid
    assert table(out, "SELECT release_id, selection_id, name, rows FROM silver2_selection") == [
        (rid, release["selection_id"], "compat-v1", 2)
    ]
    selection = table(
        out,
        "SELECT release_id, selection_id, fact_table, series_id, row_index, disposition, reason, "
        "typeof(row_index) FROM silver2_selection_row ORDER BY row_index",
    )
    assert selection == [
        (rid, release["selection_id"], "fact_listing_bar_day", SERIES_BAR, 2, "selected", "", "BIGINT"),
        (rid, release["selection_id"], "fact_listing_bar_day", SERIES_BAR, 10, "selected", "", "BIGINT"),
    ]
    # an s2_ table: release_id first, every cell text, an empty cell stays the empty string
    assert table(
        out, "SELECT release_id, listing_sk, mic, ticker, valid_from, quote_currency FROM s2_dim_listing"
    ) == [(rid, release["listing_sk"], "XXXX", "ZZZ", "", "USD")]
    assert table(
        out,
        "SELECT close, volume, typeof(close), typeof(volume) "
        "FROM s2_fact_listing_bar_day ORDER BY trade_date",
    ) == [("102.5000", "", "VARCHAR", "VARCHAR"), ("1.5", "1200", "VARCHAR", "VARCHAR")]
    assert table(out, "SELECT snapshot_id, capture_order FROM s2_snapshot ORDER BY capture_order") == [
        (s, str(i)) for i, s in enumerate(release["snapshots"], 1)
    ]
    for name in silver2.TABLES:
        assert table(out, f"SELECT DISTINCT release_id FROM s2_{name}") in ([(rid,)], [])
    assert table(out, "SELECT * FROM problem") == []


def test_every_s2_table_has_release_id_then_the_columns_all_text(lake2):
    _, out = build2(lake2)
    for name, columns in silver2.TABLES.items():
        described = table(
            out,
            f"SELECT column_name, data_type FROM information_schema.columns "
            f"WHERE table_name = 's2_{name}' ORDER BY ordinal_position",
        )
        assert described == [("release_id", "VARCHAR"), *[(c, "VARCHAR") for c in columns]]


def test_two_releases_stay_separate_by_release_id(lake2):
    first = lake2["release"]
    second = make_release(
        lake2["silver"], lake2["snapshot_sha"], close="999.0000", commit="e" * 40, name="Other"
    )
    assert second["id"] != first["id"]
    report, out = build2(lake2)
    assert report["counts"]["silver2_release"] == 2
    assert report["counts"]["s2_fact_listing_bar_day"] == 4
    assert report["counts"]["s2_dim_listing"] == 2
    for release, close, name in ((first, "102.5000", "Example Fund"), (second, "999.0000", "Other")):
        rid = release["id"]
        assert table(
            out, f"SELECT close FROM s2_fact_listing_bar_day WHERE release_id = '{rid}' ORDER BY trade_date"
        ) == [(close,), ("1.5",)]
        assert table(out, f"SELECT name FROM s2_dim_instrument WHERE release_id = '{rid}'") == [(name,)]
    # the same dimension keys occur in both releases: a view joins within one release_id, no cross product
    assert table(out, "SELECT count(*) FROM s2_bar") == [(4,)]
    assert sorted(
        table(out, "SELECT release_id, close, name FROM s2_bar WHERE trade_date = '2030-01-01'")
    ) == sorted([(first["id"], "102.5000", "Example Fund"), (second["id"], "999.0000", "Other")])


def test_views_hold_numbers_beside_the_text(lake2):
    release = lake2["release"]
    _, out = build2(lake2)
    bars = table(
        out,
        "SELECT release_id, trade_date, close, close_value, typeof(close_value), open_value, high_value, "
        "low_value, volume, volume_value, instrument_code, mic, ticker, valid_from, quote_currency, name, "
        "issuer_code, vehicle_type, domicile FROM s2_bar ORDER BY trade_date",
    )
    rid = release["id"]
    assert bars == [
        (
            rid,
            "2030-01-01",
            "102.5000",
            102.5,
            "DOUBLE",
            100.0,
            103.25,
            99.5,
            "",
            None,
            "example-fund",
            "XXXX",
            "ZZZ",
            "",
            "USD",
            "Example Fund",
            "example-issuer",
            "etf",
            "US",
        ),
        (
            rid,
            "2030-01-02",
            "1.5",
            1.5,
            "DOUBLE",
            1.0,
            2.0,
            1.0,
            "1200",
            1200.0,
            "example-fund",
            "XXXX",
            "ZZZ",
            "",
            "USD",
            "Example Fund",
            "example-issuer",
            "etf",
            "US",
        ),
    ]
    assert table(
        out,
        "SELECT release_id, ex_date, occurrence, amount_unadjusted, amount_unadjusted_value, "
        "amount_split_adjusted, amount_split_adjusted_value, franking, franking_value, currency, "
        "period_label, instrument_code, mic, ticker, quote_currency, name FROM s2_distribution",
    ) == [
        (
            rid,
            "2030-01-02",
            "0",
            "0.2500",
            0.25,
            "0.1250",
            0.125,
            "",
            None,
            "USD",
            "Quarterly",
            "example-fund",
            "XXXX",
            "ZZZ",
            "USD",
            "Example Fund",
        )
    ]
    # every column of the fact is still there, unchanged
    columns = {r[0] for r in table(out, "DESCRIBE s2_bar")}
    assert set(silver2.TABLES["fact_listing_bar_day"]) <= columns


def test_lineage_both_ways_with_present_and_absent_parents(lake2):
    release = lake2["release"]
    rid = release["id"]
    gold = lake2["gold"]
    make_gold(gold, "a9" * 8, SERIES_THREE, factor_id="ZZZ_S2", silver={"release_id": rid})
    make_gold(gold, "b9" * 8, SERIES_THREE, factor_id="ZZZ_S3", silver={"release_id": "7" * 64})
    _, out = build2(lake2)
    rows = set(
        table(
            out,
            "SELECT child_kind, child_id, parent_kind, parent_id, role, parent_present FROM lineage "
            "WHERE child_kind = 'silver2' OR parent_kind = 'silver2'",
        )
    )
    assert rows == {
        # a release -> each of its snapshots: the first is in a loaded bronze root, the second is not
        ("silver2", rid, "bronze", lake2["snapshot_sha"], "bronze", True),
        ("silver2", rid, "bronze", SNAP_ABSENT, "bronze", False),
        # a gold build -> a release: one loaded, one not
        ("gold", "a9" * 8, "silver2", rid, "silver2", True),
        ("gold", "b9" * 8, "silver2", "7" * 64, "silver2", False),
    }
    # a gold build that names neither a silver set nor a release is still a problem
    make_gold(gold, "c9" * 8, SERIES_THREE, factor_id="ZZZ_S4", silver={})
    _, out = build2(lake2, "again.duckdb")
    assert problems(out) == [("gold", "c9" * 8, "silver.silver_id is not a non-empty string")]


def test_a_tampered_release_is_reported_and_excluded_while_the_rest_loads(lake2):
    good = lake2["release"]
    bad = make_release(lake2["silver"], lake2["snapshot_sha"], close="999.0000", commit="e" * 40)
    gold = lake2["gold"]
    make_gold(gold, "a9" * 8, SERIES_THREE, factor_id="ZZZ_S2", silver={"release_id": bad["id"]})
    (bad["dir"] / "tables" / "dim_listing.csv").write_bytes(b"tampered\n")
    report, out = build2(lake2)
    assert report["result"] == "fail" and report["problems"] == 1
    [(layer, ident, message)] = problems(out)
    assert (layer, ident) == ("silver2", bad["id"])
    assert "dim_listing" in message
    assert table(out, "SELECT release_id FROM silver2_release") == [(good["id"],)]
    assert table(out, "SELECT DISTINCT release_id FROM silver2_selection_row") == [(good["id"],)]
    for name in silver2.TABLES:
        assert table(out, f"SELECT count(*) FROM s2_{name} WHERE release_id = '{bad['id']}'") == [(0,)]
    assert table(out, f"SELECT count(*) FROM lineage WHERE child_id = '{bad['id']}'") == [(0,)]
    # the version 1 sets and the gold builds are unaffected, and the good release's lineage is intact
    assert report["counts"]["silver_set"] == 1 and report["counts"]["gold_build"] == 4
    assert table(out, "SELECT parent_present FROM lineage WHERE parent_id = '" + bad["id"] + "'") == [
        (False,)
    ]


def test_a_release_in_the_wrong_directory_or_missing_a_file_is_a_problem(lake2):
    release = lake2["release"]
    other = make_release(lake2["silver"], lake2["snapshot_sha"], commit="d" * 40)
    (other["dir"] / "selections" / f"{other['selection_id']}.csv").unlink()
    moved = release["dir"].with_name("0" * 64)
    release["dir"].rename(moved)
    report, out = build2(lake2)
    assert report["counts"]["silver2_release"] == 0 and report["problems"] == 2
    assert [(layer, ident) for layer, ident, _ in problems(out)] == sorted(
        [("silver2", "0" * 64), ("silver2", other["id"])]
    )
    assert all(r[0] == 0 for r in table(out, "SELECT count(*) FROM s2_fact_listing_bar_day"))


def test_version_1_sets_and_v2_side_by_side_and_v2_is_not_an_instrument(lake2):
    report, out = build2(lake2)
    assert report["problems"] == 0
    assert report["counts"]["silver_set"] == 1 and report["counts"]["silver2_release"] == 1
    assert table(out, "SELECT DISTINCT instrument FROM silver_set") == [("ZZZ.US",)]
    assert (lake2["silver"] / "v2").is_dir()
    # a stray file beside the releases is ignored; a stray directory is a problem, not an instrument
    (lake2["silver"] / "v2" / "notes.txt").write_text("x")
    assert tool.verify(*roots(lake2))["problems"] == 0
    (lake2["silver"] / "v2" / "stray").mkdir()
    assert tool.verify(*roots(lake2))["problems"] == 1


def test_no_v2_directory_at_all(lake):
    assert not (lake["silver"] / "v2").exists()
    report, out = build2(lake)
    assert report["problems"] == 0
    for name in tool.TABLES:
        if name.startswith(("silver2_", "s2_")):
            assert report["counts"][name] == 0
            assert table(out, f"SELECT count(*) FROM {name}") == [(0,)]
    assert table(out, "SELECT count(*) FROM s2_bar") == [(0,)]
    assert table(out, "SELECT count(*) FROM s2_distribution") == [(0,)]


def test_a_v2_root_that_is_a_file_has_no_releases(lake):
    (lake["silver"] / "v2").write_text("not a directory")
    assert tool.verify(*roots(lake))["problems"] == 0


def test_cli_prints_the_release_counts_and_no_data(lake2, capsys):
    out = lake2["tmp"] / "catalogue.duckdb"
    assert tool.main(cli_args(lake2, "build", "--out", str(out))) == 0
    built = capsys.readouterr()
    assert tool.main(cli_args(lake2, "verify")) == 0
    verified = capsys.readouterr()
    assert built.out == verified.out
    lines = built.out.splitlines()
    assert "silver2_release: 1" in lines and "silver2_selection_row: 2" in lines
    assert "s2_fact_listing_bar_day: 2" in lines and "s2_dim_date: 0" in lines
    assert lines[-3:] == ["problem: 0", "problems: 0", "pass"]
    for stream in (built.out, built.err, verified.out, verified.err):
        assert not DATE_OR_DECIMAL.search(stream)
        assert lake2["release"]["id"] not in stream


# ---- gold marts -------------------------------------------------------------------------------------------

gold_marts = tool.gold_marts
KIND_TABLES = [(kind, name) for kind, tables in gold_marts.TABLES.items() for name in tables]


def factor_parent(role, build_id, factor_id, series_sha=None):
    return {
        "role": role,
        "kind": "factor_series",
        "id": build_id,
        "payload_sha256": series_sha or sha(build_id.encode()),
        "factor_id": factor_id,
        "spec_version": "0.1.0",
    }


def panel_recipe(name, members, parents):
    return gold_marts.recipe(
        "panel",
        {"name": name, "version": "0.1.0", "sha256": sha(name.encode())},
        {
            "frequency": "monthly",
            "alignment": "common_boundaries",
            "incomplete_periods": "exclude",
            "members": members,
        },
        parents,
        "f" * 40,
    )


def write_panel(root: Path, name, members, parents, returns):
    """members: {code: factor_id}; returns: {code: [(start, end, return, asset, cash)]}. Returns (id, dir)."""
    recipe = panel_recipe(name, members, parents)
    bid = gold_marts.build_id(recipe)
    rows = {
        "bridge_panel_member": [
            {
                "panel_build_id": bid,
                "member_code": code,
                "column_order": str(i),
                "factor_id": factor_id,
                "spec_version": "0.1.0",
                "input_build_id": parents[i]["id"],
                "input_series_sha256": parents[i]["payload_sha256"],
                "series_class": "total_return",
                "numeraire": "USD",
            }
            for i, (code, factor_id) in enumerate(sorted(members.items()))
        ],
        "fact_panel_return": [
            {
                "panel_build_id": bid,
                "member_code": code,
                "period_start": start,
                "period_end": end,
                "return": ret,
                "asset_return": asset,
                "cash_return": cash,
            }
            for code, entries in returns.items()
            for start, end, ret, asset, cash in entries
        ],
        "fact_panel_coverage": [
            {
                "panel_build_id": bid,
                "member_code": code,
                "first_boundary": "2030-01-31",
                "last_boundary": "2030-03-31",
                "boundaries": "3",
                "omitted_boundaries": "0",
                "common_first": "2030-01-31",
                "common_last": "2030-03-31",
                "months": str(len(entries)),
            }
            for code, entries in returns.items()
        ],
    }
    tables = {n: gold_marts.table_bytes("panel", n, r) for n, r in rows.items()}
    directory, existed = gold_marts.write_bundle(root, recipe, tables)
    assert not existed
    return bid, directory


def write_portfolio(root: Path, panel_id, weights, months):
    """months: [(start, end, return, wealth, {code: (start_weight, member_return, contribution)})]"""
    recipe = gold_marts.recipe(
        "portfolio_path",
        {"name": "pf", "version": "0.1.0", "sha256": sha(b"pf")},
        {"panel": "twin", "rebalance": "month_end", "weights": weights},
        [
            {
                "role": "panel",
                "kind": "panel",
                "id": panel_id,
                "payload_sha256": sha(b"payload-" + panel_id.encode()),
            }
        ],
        "e" * 40,
    )
    bid = gold_marts.build_id(recipe)
    rows = {
        "fact_target_allocation": [
            {"portfolio_build_id": bid, "member_code": c, "target_weight": w} for c, w in weights.items()
        ],
        "fact_portfolio_return": [
            {
                "portfolio_build_id": bid,
                "period_start": s,
                "period_end": e,
                "portfolio_return": r,
                "wealth_index": w,
            }
            for s, e, r, w, _ in months
        ],
        "fact_return_contribution": [
            {
                "portfolio_build_id": bid,
                "member_code": code,
                "period_start": s,
                "period_end": e,
                "start_weight": sw,
                "member_return": mr,
                "contribution": ct,
            }
            for s, e, _, _, per in months
            for code, (sw, mr, ct) in per.items()
        ],
    }
    tables = {n: gold_marts.table_bytes("portfolio_path", n, r) for n, r in rows.items()}
    directory, _ = gold_marts.write_bundle(root, recipe, tables)
    return bid, directory


MONTHS = [("2030-01-01", "2030-01-31"), ("2030-02-01", "2030-02-28")]


@pytest.fixture
def marts(lake):
    """Two panels side by side (one parent factor build present, one absent) and a portfolio on the first."""
    root = lake["tmp"] / "marts"
    members = {"alpha": "ZZZ_TR", "beta": "ZZZ_X"}
    parents = [
        factor_parent("m0_alpha", GOLD_ONE, "ZZZ_TR"),
        factor_parent("m1_beta", GOLD_ABSENT, "ZZZ_X"),
    ]
    lake["root"] = root
    lake["panel_a"], lake["panel_a_dir"] = write_panel(
        root,
        "twin",
        members,
        parents,
        {
            "alpha": [(*MONTHS[0], "0.0100", "", ""), (*MONTHS[1], "-0.0200", "", "")],
            "beta": [(*MONTHS[0], "0.0300", "0.0310", "0.0010"), (*MONTHS[1], "", "", "")],
        },
    )
    lake["panel_b"], lake["panel_b_dir"] = write_panel(
        root,
        "solo",
        {"gamma": "ZZZ_B"},
        [factor_parent("m0_gamma", GOLD_THREE, "ZZZ_B")],
        {"gamma": [(*MONTHS[0], "0.0300", "", ""), (*MONTHS[1], "0.0400", "", "")]},
    )
    lake["portfolio"], lake["portfolio_dir"] = write_portfolio(
        root,
        lake["panel_a"],
        {"alpha": "0.6", "beta": "0.4"},
        [
            (
                *MONTHS[0],
                "0.0180",
                "1.0180",
                {"alpha": ("0.6", "0.0100", "0.0060"), "beta": ("0.4", "0.0300", "0.0120")},
            ),
        ],
    )
    return lake


def build_marts(lake, name="catalogue.duckdb"):
    out = lake["tmp"] / name
    return tool.build(*roots(lake), out, mart_root=lake["root"]), out


def test_gold_bundle_rows_and_the_g_tables(marts):
    report, out = build_marts(marts)
    assert report["problems"] == 0 and report["result"] == "pass"
    counts = report["counts"]
    assert counts["gold_bundle"] == 3
    assert counts["g_bridge_panel_member"] == 3  # two panels: two members and one
    assert counts["g_fact_panel_return"] == 6
    assert counts["g_fact_panel_coverage"] == 3
    assert counts["g_fact_target_allocation"] == 2
    assert counts["g_fact_portfolio_return"] == 1
    assert counts["g_fact_return_contribution"] == 2
    assert counts["lineage"] == 8 + 2 + 1 + 1  # the lake's, panel a's two parents, panel b's, the portfolio's
    recipe = gold_marts.recipe(
        "panel",
        {"name": "twin", "version": "0.1.0", "sha256": sha(b"twin")},
        {
            "frequency": "monthly",
            "alignment": "common_boundaries",
            "incomplete_periods": "exclude",
            "members": {"alpha": "ZZZ_TR", "beta": "ZZZ_X"},
        },
        [factor_parent("m0_alpha", GOLD_ONE, "ZZZ_TR"), factor_parent("m1_beta", GOLD_ABSENT, "ZZZ_X")],
        "f" * 40,
    )
    manifest = json.loads((marts["panel_a_dir"] / "manifest.json").read_text())
    assert table(
        out,
        "SELECT kind, build_id, spec_name, spec_version, spec_sha256, code_commit, numeric_policy, "
        f"payload_sha256, directory, recipe_json FROM gold_bundle WHERE build_id = '{marts['panel_a']}'",
    ) == [
        (
            "panel",
            marts["panel_a"],
            "twin",
            "0.1.0",
            sha(b"twin"),
            "f" * 40,
            "decimal-50/1",
            manifest["payload_sha256"],
            str(marts["panel_a_dir"]),
            tool.canonical_json(recipe).decode(),
        )
    ]
    assert marts["panel_a"] == gold_marts.build_id(recipe)
    assert table(out, "SELECT kind, spec_name FROM gold_bundle ORDER BY spec_name") == [
        ("portfolio_path", "pf"),
        ("panel", "solo"),
        ("panel", "twin"),
    ]
    # every g_ table: the table's columns, all text, in the contract's order
    for kind, name in KIND_TABLES:
        described = table(out, f"DESCRIBE g_{name}")
        assert [(r[0], r[1]) for r in described] == [(c, "VARCHAR") for c in gold_marts.TABLES[kind][name]]
    assert table(
        out,
        'SELECT member_code, period_end, "return", asset_return, cash_return FROM g_fact_panel_return '
        f"WHERE panel_build_id = '{marts['panel_a']}' ORDER BY member_code, period_end",
    ) == [
        ("alpha", "2030-01-31", "0.0100", "", ""),
        ("alpha", "2030-02-28", "-0.0200", "", ""),
        ("beta", "2030-01-31", "0.0300", "0.0310", "0.0010"),
        ("beta", "2030-02-28", "", "", ""),
    ]
    assert table(
        out,
        "SELECT member_code, factor_id, input_build_id FROM g_bridge_panel_member "
        f"WHERE panel_build_id = '{marts['panel_a']}' ORDER BY member_code",
    ) == [("alpha", "ZZZ_TR", GOLD_ONE), ("beta", "ZZZ_X", GOLD_ABSENT)]
    assert table(
        out, "SELECT portfolio_return, wealth_index, typeof(wealth_index) FROM g_fact_portfolio_return"
    ) == [("0.0180", "1.0180", "VARCHAR")]
    assert table(out, "SELECT member_code, contribution FROM g_fact_return_contribution ORDER BY 1") == [
        ("alpha", "0.0060"),
        ("beta", "0.0120"),
    ]


def test_two_panels_side_by_side_stay_separate_by_build_id(marts):
    _, out = build_marts(marts)
    assert table(
        out, "SELECT panel_build_id, count(*) FROM g_fact_panel_return GROUP BY 1 ORDER BY 2 DESC"
    ) == [(marts["panel_a"], 4), (marts["panel_b"], 2)]
    assert table(
        out,
        "SELECT p.spec_name, count(*) FROM g_fact_panel_coverage c "
        "JOIN gold_bundle p ON p.build_id = c.panel_build_id GROUP BY 1 ORDER BY 1",
    ) == [("solo", 1), ("twin", 2)]


def test_the_views_hold_numbers_beside_the_text_and_the_factor_id(marts):
    _, out = build_marts(marts)
    rows = table(
        out,
        'SELECT panel_build_id, member_code, period_end, "return", return_value, asset_return, '
        "asset_return_value, cash_return_value, factor_id, typeof(return_value) "
        "FROM g_panel_return ORDER BY panel_build_id, member_code, period_end",
    )
    assert len(rows) == 6 == table(out, "SELECT count(*) FROM g_fact_panel_return")[0][0]
    by_key = {(r[0], r[1], r[2]): r for r in rows}
    beta = by_key[(marts["panel_a"], "beta", "2030-01-31")]
    assert beta[3:] == ("0.0300", 0.03, "0.0310", 0.031, 0.001, "ZZZ_X", "DOUBLE")
    alpha = by_key[(marts["panel_a"], "alpha", "2030-02-28")]
    assert alpha[3:9] == ("-0.0200", -0.02, "", None, None, "ZZZ_TR")
    assert by_key[(marts["panel_a"], "beta", "2030-02-28")][4] is None  # empty text: NULL, not an error
    assert by_key[(marts["panel_b"], "gamma", "2030-02-28")][8] == "ZZZ_B"
    # the same member code in two panels takes each panel's own factor id
    assert table(out, "SELECT sum(return_value) FROM g_panel_return WHERE factor_id = 'ZZZ_TR'") == [
        (pytest.approx(-0.01),)
    ]
    assert table(
        out,
        "SELECT portfolio_return, portfolio_return_value, wealth_index, wealth_index_value, "
        "typeof(wealth_index_value) FROM g_portfolio_return",
    ) == [("0.0180", 0.018, "1.0180", 1.018, "DOUBLE")]


def test_lineage_to_present_and_absent_factor_builds_and_from_a_portfolio_to_its_panel(marts):
    _, out = build_marts(marts)
    rows = table(
        out,
        "SELECT child_id, parent_kind, parent_id, role, parent_present FROM lineage "
        "WHERE child_kind = 'mart' ORDER BY child_id, role",
    )
    assert sorted(rows) == sorted(
        [
            (marts["panel_a"], "gold", GOLD_ONE, "m0_alpha", True),
            (marts["panel_a"], "gold", GOLD_ABSENT, "m1_beta", False),
            (marts["panel_b"], "gold", GOLD_THREE, "m0_gamma", True),
            (marts["portfolio"], "mart", marts["panel_a"], "panel", True),
        ]
    )


def test_a_portfolio_whose_panel_is_not_loaded_has_an_absent_mart_parent(marts):
    other = "9" * 64
    write_portfolio(marts["root"], other, {"alpha": "1"}, [])
    _, out = build_marts(marts)
    assert table(
        out, f"SELECT parent_kind, parent_id, parent_present FROM lineage WHERE parent_id = '{other}'"
    ) == [("mart", other, False)]


def test_a_tampered_bundle_is_reported_and_excluded(marts):
    path = marts["panel_b_dir"] / "tables" / "fact_panel_return.csv"
    path.write_text(path.read_text().replace("0.0400", "0.0401"))
    report, out = build_marts(marts)
    assert report["problems"] == 1 and report["result"] == "fail"
    assert table(out, "SELECT layer, id, path, problem FROM problem") == [
        (
            "mart",
            marts["panel_b"],
            str(marts["panel_b_dir"]),
            "table fact_panel_return: file sha256 differs from the manifest",
        )
    ]
    assert table(out, "SELECT count(*) FROM gold_bundle") == [(2,)]
    assert table(out, f"SELECT count(*) FROM lineage WHERE child_id = '{marts['panel_b']}'") == [(0,)]
    for name in ("bridge_panel_member", "fact_panel_return", "fact_panel_coverage"):
        assert table(out, f"SELECT count(*) FROM g_{name} WHERE panel_build_id = '{marts['panel_b']}'") == [
            (0,)
        ]
    assert table(out, "SELECT count(*) FROM g_fact_panel_return") == [(4,)]
    assert tool.main(cli_args(marts, "verify", "--mart-root", str(marts["root"]))) == 1


def test_other_bundle_problems_are_reported_once_each(marts):
    (marts["panel_b_dir"] / "stray.txt").write_text("x")
    wrong = marts["root"] / "portfolio_path" / marts["panel_a"]
    wrong.mkdir()
    (wrong / "manifest.json").write_text("{}")
    junk = marts["root"] / "junk" / ("1" * 64)
    junk.mkdir(parents=True)
    report = tool.verify(*roots(marts), mart_root=marts["root"])
    assert report["problems"] == 3
    _, out = build_marts(marts)
    assert sorted(r[0] for r in table(out, "SELECT layer FROM problem")) == ["mart"] * 3
    assert table(out, "SELECT count(*) FROM gold_bundle") == [(2,)]


def test_no_mart_root_given_leaves_the_mart_tables_empty(lake):
    out = lake["tmp"] / "catalogue.duckdb"
    report = tool.build(*roots(lake), out)
    assert report["problems"] == 0
    for name in tool.MART_TABLES:
        assert report["counts"][name] == 0
        assert table(out, f"SELECT count(*) FROM {name}") == [(0,)]
    for view in ("g_panel_return", "g_portfolio_return"):
        assert table(out, f"SELECT count(*) FROM {view}") == [(0,)]
    assert table(out, "SELECT count(*) FROM lineage WHERE child_kind = 'mart'") == [(0,)]


def test_an_absent_or_empty_mart_root_is_fine_and_a_file_is_refused(lake):
    assert tool.verify(*roots(lake), mart_root=lake["tmp"] / "nowhere")["result"] == "pass"
    (lake["tmp"] / "empty-marts").mkdir()
    assert tool.verify(*roots(lake), mart_root=lake["tmp"] / "empty-marts")["result"] == "pass"
    (lake["tmp"] / "afile").write_text("x")
    with pytest.raises(ValueError, match="mart root is not a directory"):
        tool.verify(*roots(lake), mart_root=lake["tmp"] / "afile")


def test_the_new_tables_and_views_are_in_every_catalogue(marts):
    _, out = build_marts(marts)
    assert [r[0] for r in table(out, "SHOW TABLES")] == sorted([*tool.TABLES, *tool.VIEWS])
    assert {"gold_bundle", "g_panel_return", "g_portfolio_return"} <= {
        r[0] for r in table(out, "SHOW TABLES")
    }


def test_rebuilding_with_marts_gives_the_same_contents(marts):
    _, out = build_marts(marts)
    first = contents(out)
    out.unlink()
    build_marts(marts)
    assert contents(out) == first
    assert first["g_fact_panel_return"]


def test_cli_prints_the_mart_counts_only_with_a_mart_root_and_no_data(marts, capsys):
    out = marts["tmp"] / "catalogue.duckdb"
    extra = ("--mart-root", str(marts["root"]))
    assert tool.main(cli_args(marts, "build", "--out", str(out), *extra)) == 0
    built = capsys.readouterr()
    assert tool.main(cli_args(marts, "verify", *extra)) == 0
    verified = capsys.readouterr()
    assert built.out == verified.out
    lines = built.out.splitlines()
    assert (
        "gold_bundle: 3" in lines
        and "g_fact_panel_return: 6" in lines
        and "g_fact_portfolio_return: 1" in lines
    )
    assert lines[-3:] == ["problem: 0", "problems: 0", "pass"]
    for stream in (built.out, built.err, verified.out, verified.err):
        assert not DATE_OR_DECIMAL.search(stream)
        assert marts["panel_a"] not in stream
    assert tool.main(cli_args(marts, "verify")) == 0
    assert "gold_bundle" not in capsys.readouterr().out
