"""OD-0231: the silver builder, on an invented snapshot only. No network, no real data, no git."""

import hashlib
import importlib
import json
import re
import stat
import sys
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
tool = importlib.import_module("silver_build")

COMMIT = "c" * 40
INSTRUMENT = "ZZZ.US"
SNAPSHOT = "s1"

EOD = (
    '[{"date": "2030-01-07", "close": 100.0000, "adjusted_close": 100.0000},'
    ' {"date": "2030-01-08", "close": 102.5000, "adjusted_close": null},'
    ' {"date": "2030-01-09", "close": 102.0, "adjusted_close": 102.0},'
    ' {"date": "2030-01-10", "close": 51.0, "adjusted_close": 102},'
    ' {"date": "2030-01-11", "close": 52}]'
)
DIV_NINTH = (
    '{"date": "2030-01-09", "value": 1.0, "unadjustedValue": 1.0, "currency": "USD",'
    ' "paymentDate": "2030-01-10", "recordDate": "2030-01-09", "declarationDate": "2030-01-08"}'
)
DIV_ELEVENTH = (
    '{"date": "2030-01-11", "value": 0.2500, "unadjustedValue": 0.5000, "currency": "USD",'
    ' "paymentDate": null, "recordDate": "2030-01-11", "declarationDate": null, "period": "Quarterly"}'
)
SPLITS = '[{"date": "2030-01-10", "split": "2.000000/1.000000"}]'
LISTING = '[{"Code": "ZZZ", "Currency": "USD"}, {"Code": "OTHER", "Currency": "EUR"}]'

CLOSES_CSV = (
    b"date,close,adjusted_close\n"
    b"2030-01-07,100.0000,100.0000\n"
    b"2030-01-08,102.5000,\n"
    b"2030-01-09,102.0,102.0\n"
    b"2030-01-10,51.0,102\n"
    b"2030-01-11,52,\n"
)
DISTRIBUTIONS_CSV = (
    b"ex_date,amount,split_adjusted_amount,currency,payment_date,record_date,declaration_date,period\n"
    b"2030-01-09,1.0,1.0,USD,2030-01-10,2030-01-09,2030-01-08,\n"
    b"2030-01-11,0.5000,0.2500,USD,,2030-01-11,,Quarterly\n"
)
DISTRIBUTIONS_CORRECTED_CSV = (
    b"ex_date,amount,split_adjusted_amount,currency,payment_date,record_date,declaration_date,period\n"
    b"2030-01-11,0.5000,0.2500,USD,,2030-01-11,,Quarterly\n"
)
SPLITS_CSV = b"date,ratio\n2030-01-10,2.000000/1.000000\n"


@pytest.fixture(autouse=True)
def private_tmp(tmp_path):
    tmp_path.chmod(0o700)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def spec_text(corrections="[]", currency="USD", version="0.1.0", extra=""):
    return f"""identity: {{instrument: {INSTRUMENT}, version: {version}, status: proposed}}
source: {{source_id: invented.source, quote_currency: {currency}}}
corrections: {corrections}
changelog: ["0.1.0 (invented): first"]
{extra}"""


CORRECTION = """
  - action: exclude_distribution
    ex_date: "2030-01-09"
    reason: "invented duplicate"
    evidence: notes/record.md"""


def write_spec(tmp_path, name="spec.yaml", **kwargs):
    path = tmp_path / name
    path.write_text(spec_text(**kwargs))
    return path


def make_snapshot(tmp_path, eod=EOD, dividends=None, drop=None, listing=LISTING, source_id=None):
    """The real layout: raw/<snapshot>/<SYMBOL>.<kind>.json and manifest.json. Returns (root, pin)."""
    root = tmp_path / "root"
    raw = root / "raw" / SNAPSHOT
    raw.mkdir(parents=True)
    dividends = f"[{DIV_NINTH}, {DIV_ELEVENTH}]" if dividends is None else dividends
    contents = {
        (INSTRUMENT, "eod"): eod,
        (INSTRUMENT, "div"): dividends,
        (INSTRUMENT, "splits"): SPLITS,
        ("EXCHANGE.US", "symbols"): listing,
    }
    files = []
    for (symbol, kind), text in contents.items():
        if drop == kind:
            continue
        name = f"{symbol}.{kind}.json"
        body = text.encode()
        (raw / name).write_bytes(body)
        files.append({"symbol": symbol, "kind": kind, "path": f"raw/{SNAPSHOT}/{name}", "sha256": sha(body)})
    manifest = {"snapshot": SNAPSHOT, "files": files, "stopped": None}
    if source_id is not None:
        manifest["source_id"] = source_id
    (raw / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return root, sha((raw / "manifest.json").read_bytes())


def build_in(tmp_path, root, pin, spec=None, out=None, commit=COMMIT):
    return tool.build(
        spec or write_spec(tmp_path), root, SNAPSHOT, pin, out or tmp_path / "store", commit=commit
    )


def run_build(tmp_path, **kwargs):
    root, pin = make_snapshot(tmp_path)
    return build_in(tmp_path, root, pin, **kwargs)


def set_dir(tmp_path, manifest):
    return tmp_path / "store" / INSTRUMENT / manifest["silver_id"]


def tree_digest(root):
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file()}


# --- the files and their exact bytes


def test_a_build_writes_the_three_files_and_the_manifest_to_the_contract(tmp_path):
    spec = write_spec(tmp_path)
    root, pin = make_snapshot(tmp_path)
    manifest, existed = build_in(tmp_path, root, pin, spec=spec)
    assert existed is False
    directory = set_dir(tmp_path, manifest)
    assert sorted(p.name for p in directory.iterdir()) == [
        "closes.csv",
        "distributions.csv",
        "manifest.json",
        "splits.csv",
    ]
    assert (directory / "closes.csv").read_bytes() == CLOSES_CSV
    assert (directory / "distributions.csv").read_bytes() == DISTRIBUTIONS_CSV
    assert (directory / "splits.csv").read_bytes() == SPLITS_CSV
    spec_sha, pin_sha = sha(spec.read_bytes()), pin
    silver_id = sha((spec_sha + pin_sha + COMMIT).encode())[:16]
    assert directory.name == silver_id
    raw = f"raw/{SNAPSHOT}/"
    expected = {
        "schema": "hio.silver/1",
        "instrument": INSTRUMENT,
        "quote_currency": "USD",
        "source_id": "invented.source",
        "observation_spec": {"version": "0.1.0", "sha256": spec_sha},
        "snapshot": SNAPSHOT,
        "snapshot_manifest_sha256": pin_sha,
        "inputs": [
            {"path": f"{raw}EXCHANGE.US.symbols.json", "sha256": sha(LISTING.encode())},
            {"path": f"{raw}ZZZ.US.div.json", "sha256": sha(f"[{DIV_NINTH}, {DIV_ELEVENTH}]".encode())},
            {"path": f"{raw}ZZZ.US.eod.json", "sha256": sha(EOD.encode())},
            {"path": f"{raw}ZZZ.US.splits.json", "sha256": sha(SPLITS.encode())},
        ],
        "corrections": [],
        "code_commit": COMMIT,
        "files": {
            "closes.csv": {"sha256": sha(CLOSES_CSV), "rows": 5},
            "distributions.csv": {"sha256": sha(DISTRIBUTIONS_CSV), "rows": 2},
            "splits.csv": {"sha256": sha(SPLITS_CSV), "rows": 1},
        },
        "first": "2030-01-07",
        "last": "2030-01-11",
        "silver_id": silver_id,
    }
    assert manifest == expected
    assert (directory / "manifest.json").read_bytes() == (
        json.dumps(expected, indent=1, sort_keys=True) + "\n"
    ).encode()


def test_inputs_are_the_four_bronze_files_sorted_by_path(tmp_path):
    manifest, _ = run_build(tmp_path)
    paths = [i["path"] for i in manifest["inputs"]]
    assert paths == sorted(paths) and len(paths) == 4


def test_exact_text_is_preserved_and_a_null_is_an_empty_cell(tmp_path):
    manifest, _ = run_build(tmp_path)
    lines = (set_dir(tmp_path, manifest) / "closes.csv").read_text().splitlines()
    assert lines[2] == "2030-01-08,102.5000,"  # trailing zeros kept, null empty
    assert lines[1] == "2030-01-07,100.0000,100.0000"
    assert lines[5] == "2030-01-11,52,"  # a missing field is an empty cell, an integer stays an integer
    text = (set_dir(tmp_path, manifest) / "distributions.csv").read_text()
    assert "0.5000,0.2500" in text


def test_the_silver_id_changes_with_the_commit(tmp_path):
    root, pin = make_snapshot(tmp_path)
    first, _ = build_in(tmp_path, root, pin)
    second, _ = build_in(tmp_path, root, pin, commit="d" * 40)
    assert first["silver_id"] != second["silver_id"]


# --- idempotence


def test_building_again_is_already_built_and_changes_nothing(tmp_path):
    root, pin = make_snapshot(tmp_path)
    manifest, existed = build_in(tmp_path, root, pin)
    before = tree_digest(tmp_path / "store")
    again, existed_again = build_in(tmp_path, root, pin)
    assert (existed, existed_again) == (False, True)
    assert again == manifest
    assert tree_digest(tmp_path / "store") == before


def test_an_existing_set_with_different_bytes_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path)
    manifest, _ = build_in(tmp_path, root, pin)
    target = set_dir(tmp_path, manifest) / "closes.csv"
    target.write_bytes(target.read_bytes() + b"x")
    with pytest.raises(ValueError, match="different bytes"):
        build_in(tmp_path, root, pin)


def test_an_existing_set_with_an_extra_file_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path)
    manifest, _ = build_in(tmp_path, root, pin)
    (set_dir(tmp_path, manifest) / "extra.txt").write_bytes(b"")
    with pytest.raises(ValueError, match="different bytes"):
        build_in(tmp_path, root, pin)


def test_a_failed_build_leaves_no_partial_directory(tmp_path):
    root, pin = make_snapshot(tmp_path, eod=EOD.replace("102.0,", "0,"))
    with pytest.raises(ValueError):
        build_in(tmp_path, root, pin)
    assert not (tmp_path / "store").exists() or not any((tmp_path / "store").rglob("*"))


# --- corrections


def test_a_correction_removes_exactly_one_row_and_changes_the_silver_id(tmp_path):
    root, pin = make_snapshot(tmp_path)
    plain, _ = build_in(tmp_path, root, pin)
    corrected, _ = build_in(tmp_path, root, pin, spec=write_spec(tmp_path, "c.yaml", corrections=CORRECTION))
    assert corrected["silver_id"] != plain["silver_id"]
    assert plain["files"]["distributions.csv"]["rows"] == 2
    assert corrected["files"]["distributions.csv"]["rows"] == 1
    directory = set_dir(tmp_path, corrected)
    assert (directory / "distributions.csv").read_bytes() == DISTRIBUTIONS_CORRECTED_CSV
    assert (directory / "closes.csv").read_bytes() == CLOSES_CSV
    record = json.loads(DIV_NINTH, parse_float=Decimal)
    digest = sha(json.dumps(record, sort_keys=True, default=str).encode())
    assert corrected["corrections"] == [
        {"action": "exclude_distribution", "ex_date": "2030-01-09", "record_sha256": digest}
    ]


def test_a_correction_that_matches_no_record_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path, dividends=f"[{DIV_ELEVENTH}]")
    with pytest.raises(ValueError, match="not 0"):
        build_in(tmp_path, root, pin, spec=write_spec(tmp_path, corrections=CORRECTION))


def test_a_correction_that_matches_several_records_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path, dividends=f"[{DIV_NINTH}, {DIV_NINTH}, {DIV_ELEVENTH}]")
    with pytest.raises(ValueError, match="not 2"):
        build_in(tmp_path, root, pin, spec=write_spec(tmp_path, corrections=CORRECTION))


def test_a_zero_amount_record_is_not_a_match(tmp_path):
    zero = DIV_NINTH.replace('"unadjustedValue": 1.0', '"unadjustedValue": 0')
    root, pin = make_snapshot(tmp_path, dividends=f"[{zero}, {DIV_NINTH}]")
    manifest, _ = build_in(tmp_path, root, pin, spec=write_spec(tmp_path, corrections=CORRECTION))
    assert manifest["files"]["distributions.csv"]["rows"] == 1  # the zero-amount record is kept


# --- refusals


def test_a_quote_currency_that_differs_from_the_listing_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path)
    with pytest.raises(ValueError, match="quote currency"):
        build_in(tmp_path, root, pin, spec=write_spec(tmp_path, currency="EUR"))


def test_a_listing_that_does_not_settle_the_currency_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path, listing='[{"Code": "OTHER", "Currency": "EUR"}]')
    with pytest.raises(ValueError, match="quote currency"):
        build_in(tmp_path, root, pin)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('"2030-01-08", "close": 102.5000', '"2030-01-07", "close": 102.5000', "unique and ascending"),
        ('"2030-01-09", "close": 102.0', '"2030-01-06", "close": 102.0', "unique and ascending"),
        ("102.0,", "0,", "positive"),
        ("102.0,", "-1.5,", "positive"),
        ("102.0,", "null,", "positive"),
        ('"close": 52', '"close": "52"', "positive"),
        ('"2030-01-11"', '"11/01/2030"', "ISO date"),
    ],
)
def test_bad_closes_are_refused(tmp_path, old, new, message):
    root, pin = make_snapshot(tmp_path, eod=EOD.replace(old, new))
    with pytest.raises(ValueError, match=message):
        build_in(tmp_path, root, pin)


def test_no_closes_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path, eod="[]")
    with pytest.raises(ValueError, match="no rows"):
        build_in(tmp_path, root, pin)


@pytest.mark.parametrize("kind", ["eod", "div", "splits", "symbols"])
def test_a_missing_kind_or_listing_is_refused(tmp_path, kind):
    root, pin = make_snapshot(tmp_path, drop=kind)
    with pytest.raises(ValueError, match=f"no {kind}" if kind != "symbols" else "exchange symbol list"):
        build_in(tmp_path, root, pin)


def test_a_pin_that_does_not_match_is_refused(tmp_path):
    root, _pin = make_snapshot(tmp_path)
    with pytest.raises(ValueError, match="does not match the pin"):
        build_in(tmp_path, root, "0" * 64)


def test_a_tampered_snapshot_file_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path)
    (root / "raw" / SNAPSHOT / "ZZZ.US.eod.json").write_bytes(b"[]")
    with pytest.raises(ValueError, match="retained bytes"):
        build_in(tmp_path, root, pin)


def test_a_snapshot_source_id_that_differs_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path, source_id="other.source")
    with pytest.raises(ValueError, match="source_id"):
        build_in(tmp_path, root, pin)
    root2 = tmp_path / "again"
    root2.mkdir()
    root2, pin2 = make_snapshot(root2, source_id="invented.source")
    assert build_in(tmp_path, root2, pin2)[1] is False


def test_an_empty_commit_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path)
    with pytest.raises(ValueError, match="commit"):
        build_in(tmp_path, root, pin, commit=" ")


def test_a_snapshot_with_a_bad_name_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path)
    with pytest.raises(ValueError):
        tool.build(write_spec(tmp_path), root, "../s1", pin, tmp_path / "store", commit=COMMIT)


# --- the observation spec


def read(tmp_path, text):
    path = tmp_path / "spec.yaml"
    path.write_text(text)
    return tool.read_observation_spec(path)


def test_a_valid_spec_is_read_with_its_hash(tmp_path):
    spec = write_spec(tmp_path, corrections=CORRECTION)
    fields = tool.read_observation_spec(spec)
    assert fields["instrument"] == INSTRUMENT
    assert (fields["version"], fields["status"]) == ("0.1.0", "proposed")
    assert (fields["source_id"], fields["quote_currency"]) == ("invented.source", "USD")
    assert fields["corrections"][0]["ex_date"] == "2030-01-09"
    assert fields["sha256"] == sha(spec.read_bytes())
    assert read(tmp_path, spec_text())["corrections"] == []


@pytest.mark.parametrize(
    "text",
    [
        spec_text(extra="extra: 1\n"),
        spec_text().replace("changelog", "notes"),
        spec_text(version="1.0"),  # a YAML float, not a string
        spec_text().replace("status: proposed", "status: 3"),
        spec_text().replace(", status: proposed", ""),
        spec_text().replace("quote_currency: USD", "quote_currency: USD, extra: 1"),
        spec_text().replace("instrument: ZZZ.US", "instrument: ZZZ"),
        spec_text().replace("instrument: ZZZ.US", "instrument: ../ZZZ.US"),
        spec_text().replace('["0.1.0 (invented): first"]', "first"),
        spec_text(corrections="notalist"),
        spec_text(corrections="[1]"),
        "- a list\n",
        "key: [unclosed\n",
    ],
)
def test_a_malformed_spec_is_refused(tmp_path, text):
    with pytest.raises(ValueError):
        read(tmp_path, text)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda c: c.replace("exclude_distribution", "delete"),
        lambda c: c.replace('"2030-01-09"', "2030-01-09"),  # unquoted: a YAML date, not a string
        lambda c: c.replace('"2030-01-09"', '"2030-13-09"'),
        lambda c: c.replace('"invented duplicate"', '""'),
        lambda c: c.replace("notes/record.md", '""'),
        lambda c: c + "\n    series_id: ZZZ.US.close",
        lambda c: c.replace("    evidence: notes/record.md", ""),
    ],
)
def test_a_malformed_correction_is_refused(tmp_path, mutate):
    with pytest.raises(ValueError):
        read(tmp_path, spec_text(corrections=mutate(CORRECTION)))


def test_two_corrections_with_one_ex_date_are_refused(tmp_path):
    with pytest.raises(ValueError, match="share an ex_date"):
        read(tmp_path, spec_text(corrections=CORRECTION + CORRECTION))


# --- the snapshot, the output and the modes


def test_the_snapshot_is_byte_identical_afterwards(tmp_path):
    root, pin = make_snapshot(tmp_path)
    before = tree_digest(root)
    build_in(tmp_path, root, pin, spec=write_spec(tmp_path, corrections=CORRECTION))
    assert tree_digest(root) == before


def test_modes_are_private(tmp_path):
    manifest, _ = run_build(tmp_path)
    directory = set_dir(tmp_path, manifest)
    for folder in (tmp_path / "store", directory.parent, directory):
        assert stat.S_IMODE(folder.stat().st_mode) == 0o700
    for path in directory.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert not any(p.name.startswith(".tmp-") for p in directory.parent.iterdir())


def test_an_out_path_inside_the_repository_is_refused(tmp_path):
    root, pin = make_snapshot(tmp_path)
    target = REPO / "silver-never-written"
    with pytest.raises(ValueError, match="outside the repository"):
        build_in(tmp_path, root, pin, out=target)
    assert not target.exists()
    with pytest.raises(ValueError, match="outside the repository"):
        build_in(tmp_path, root, pin, out=REPO)


# --- the command


def cli(tmp_path, monkeypatch, *, out=None, pin=None, spec=None):
    monkeypatch.setattr(tool._base, "code_commit", lambda: {"commit": COMMIT})
    root, real_pin = (
        make_snapshot(tmp_path) if not (tmp_path / "root").exists() else (tmp_path / "root", None)
    )
    pin = pin or real_pin or sha((tmp_path / "root" / "raw" / SNAPSHOT / "manifest.json").read_bytes())
    return [
        "--spec",
        str(spec or write_spec(tmp_path, corrections=CORRECTION)),
        "--root",
        str(root),
        "--snapshot",
        SNAPSHOT,
        "--manifest-sha256",
        pin,
        "--out",
        str(out or tmp_path / "store"),
    ]


def test_the_command_prints_counts_ids_and_hashes_only(tmp_path, monkeypatch, capsys):
    argv = cli(tmp_path, monkeypatch)
    assert tool.main(argv) == 0
    output = capsys.readouterr().out
    lines = output.splitlines()
    assert lines[0] == f"instrument: {INSTRUMENT}"
    assert re.fullmatch(r"silver_id: [0-9a-f]{16}", lines[1])
    assert lines[2:5] == ["closes.csv: 5 rows", "distributions.csv: 1 rows", "splits.csv: 1 rows"]
    assert lines[5] == "corrections: 1 applied"
    assert f"closes.csv sha256: {sha(CLOSES_CSV)}" in lines
    assert f"distributions.csv sha256: {sha(DISTRIBUTIONS_CORRECTED_CSV)}" in lines
    assert f"splits.csv sha256: {sha(SPLITS_CSV)}" in lines
    assert any(line.startswith("manifest.json sha256: ") for line in lines)
    assert "already built" not in output
    assert not re.search(r"\d{4}-\d{2}-\d{2}", output)  # no date
    assert not re.search(r"\d\.\d", output)  # no decimal
    assert tool.main(argv) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "already built"


def test_the_command_refuses_with_exit_2(tmp_path, monkeypatch, capsys):
    argv = cli(tmp_path, monkeypatch, pin="0" * 64)
    assert tool.main(argv) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("refused: ValueError: ")


def test_the_command_refuses_an_out_path_inside_the_repository_before_any_lookup(
    tmp_path, monkeypatch, capsys
):
    argv = cli(tmp_path, monkeypatch, out=REPO / "silver-never-written")

    def forbidden():
        raise AssertionError("git was consulted")

    monkeypatch.setattr(tool._base, "code_commit", forbidden)
    assert tool.main(argv) == 2
    assert "outside the repository" in capsys.readouterr().err
    assert not (REPO / "silver-never-written").exists()
