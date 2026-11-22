"""The verified silver reader and the version 1 compatibility export (OD-0233).

Every release here is made by hand with `hio.contracts.silver` from invented data: two instruments
(`ZZZ.US`, `YYY.US`), two snapshots, one revised close, one revised adjusted close, one declared
exclusion, 11 bar rows (so that row 2 sorts before row 10). Nothing reads bronze or runs git.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import re
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from hio.contracts import silver as contract
from hio.marketdata.silver_reader import FundObservations, open_release

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "silver_compat_export", REPO / "tools" / "silver_compat_export.py"
)
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

BAR = "fact_listing_bar_day"
ADJ = "fact_vendor_adjusted_close_day"
DIST = "fact_distribution_event"
SPLIT = "fact_split_event"
ZZZ = "ZZZ.US"
YYY = "YYY.US"


def _h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _sk(label: str) -> str:
    return contract.sk("test", {"label": label})


SNAP = {"s1": _h("manifest one"), "s2": _h("manifest two")}
CAPTURE = {SNAP["s1"]: 1, SNAP["s2"]: 2}
CID = contract.correction_id(_h(f"obs{ZZZ}"), "exclude_distribution", "2024-01-09")


def _row(table: str, **cells: str) -> dict[str, str]:
    row = dict.fromkeys(contract.TABLES[table], "")
    unknown = set(cells) - set(row)
    assert not unknown, f"{table}: {sorted(unknown)}"
    row.update(cells)
    return row


def _eod(i: int, snap: str) -> dict[str, str]:
    revised = snap == "s2" and i == 1
    return {
        "date": f"2024-01-{i + 2:02d}",
        "open": "9.50",
        "high": f"{11 + i}.50",
        "low": "9.00",
        "close": "11.30" if revised else f"{10 + i}.25",
        "volume": str(1000 + i),
        "adjusted_close": "" if i == 3 else ("11.27" if revised else f"{10 + i}.20"),
    }


DIV0 = {
    "ex_date": "2024-01-05",
    "declaration_date": "2024-01-02",
    "record_date": "2024-01-08",
    "payment_date": "2024-01-15",
    "amount_unadjusted": "0.50",
    "amount_split_adjusted": "0.25",
    "currency": "USD",
    "period_label": "Q4",
    "franking": "",
}
DIV1 = {  # the declared exclusion
    "ex_date": "2024-01-09",
    "declaration_date": "",
    "record_date": "2024-01-10",
    "payment_date": "2024-01-16",
    "amount_unadjusted": "0.40",
    "amount_split_adjusted": "0.20",
    "currency": "USD",
    "period_label": "Q4 again",
    "franking": "",
}
DIV2 = {  # in the second snapshot only
    "ex_date": "2024-01-11",
    "declaration_date": "",
    "record_date": "2024-01-12",
    "payment_date": "2024-01-17",
    "amount_unadjusted": "0.30",
    "amount_split_adjusted": "0.15",
    "currency": "USD",
    "period_label": "Q1, special",
    "franking": "",
}
SPLIT0 = {
    "effective_date": "2024-01-04",
    "ratio": "2.000000/1.000000",
    "new_units": "2.000000",
    "old_units": "1.000000",
}
YYY_EOD = {
    "date": "2024-01-10",
    "open": "7.00",
    "high": "8.00",
    "low": "6.50",
    "close": "7.75",
    "volume": "55",
    "adjusted_close": "7.70",
}

CLOSES_S2 = (
    b"date,close,adjusted_close\n"
    b"2024-01-02,10.25,10.20\n"
    b"2024-01-03,11.30,11.27\n"
    b"2024-01-04,12.25,12.20\n"
    b"2024-01-05,13.25,\n"
    b"2024-01-06,14.25,14.20\n"
    b"2024-01-07,15.25,15.20\n"
    b"2024-01-08,16.25,16.20\n"
    b"2024-01-09,17.25,17.20\n"
    b"2024-01-10,18.25,18.20\n"
    b"2024-01-11,19.25,19.20\n"
    b"2024-01-12,20.25,20.20\n"
)
CLOSES_S1 = CLOSES_S2.replace(b"2024-01-03,11.30,11.27", b"2024-01-03,11.25,11.20")
DISTRIBUTIONS_HEADER = (
    "ex_date,amount,split_adjusted_amount,currency,payment_date,record_date,declaration_date,period\n"
)
DISTRIBUTIONS_S2 = (
    DISTRIBUTIONS_HEADER
    + "2024-01-05,0.50,0.25,USD,2024-01-15,2024-01-08,2024-01-02,Q4\n"
    + '2024-01-11,0.30,0.15,USD,2024-01-17,2024-01-12,,"Q1, special"\n'
).encode()
DISTRIBUTIONS_S1 = (
    DISTRIBUTIONS_HEADER + "2024-01-05,0.50,0.25,USD,2024-01-15,2024-01-08,2024-01-02,Q4\n"
).encode()
SPLITS = b"date,ratio\n2024-01-04,2.000000/1.000000\n"


@dataclass
class Parts:
    """The rows of a release before they are rendered, so a test can change them."""

    tables: dict[str, list[dict[str, str]]] = field(default_factory=lambda: {n: [] for n in contract.TABLES})
    records: dict[tuple[str, str], list[dict[str, str]]] = field(default_factory=dict)
    selections: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    newest: dict[tuple[str, str], tuple[str, str]] = field(default_factory=dict)
    seen_records: set[str] = field(default_factory=set)


def _record(parts: Parts, symbol: str, snap: str, kind: str, index: int, record: dict[str, str]) -> str:
    file_sha = _h(f"{symbol}:{kind}:{snap}")
    rid = contract.source_record_id(file_sha, index)
    if rid not in parts.seen_records:
        parts.seen_records.add(rid)
        parts.tables["source_record"].append(
            _row(
                "source_record",
                source_record_id=rid,
                file_sha256=file_sha,
                row_index=str(index),
                record_sha256=contract.record_sha256(record),
            )
        )
    return rid


def _observe(
    parts: Parts,
    symbol: str,
    snap: str,
    table: str,
    quantity: str,
    coordinate: dict[str, str | int],
    measures: dict[str, str],
    further: dict[str, str],
    rid: str,
    index: int,
) -> None:
    series = f"{symbol}.{quantity}"
    oid = contract.observation_id(series, coordinate)
    fingerprint = contract.value_fingerprint(measures)
    newest = parts.newest.get((table, oid))
    if newest is not None and newest[0] == fingerprint:
        vid = newest[1]
    else:
        vid = contract.vintage_id(oid, fingerprint, SNAP[snap])
        parts.newest[(table, oid)] = (fingerprint, vid)
        parts.tables[table].append(
            _row(
                table,
                vintage_id=vid,
                observation_id=oid,
                series_id=series,
                series_sk=_sk(series),
                source_sk=_sk("source"),
                audit_sk=_sk("audit"),
                origin_source_record_id=rid,
                anchor_snapshot_id=SNAP[snap],
                first_captured_at=f"2024-02-0{CAPTURE[SNAP[snap]]}T00:00:00Z",
                **measures,
                **further,
            )
        )
    parts.tables["bridge_vintage_support"].append(
        _row("bridge_vintage_support", vintage_id=vid, source_record_id=rid, snapshot_id=SNAP[snap])
    )
    parts.records.setdefault((symbol, snap), []).append(
        {
            "fact_table": table,
            "series_id": series,
            "observation_id": oid,
            "vintage_id": vid,
            "source_record_id": rid,
            "row_index": str(index),
            "disposition": "selected",
            "reason": "",
        }
    )


def _bar_and_adjusted(parts: Parts, symbol: str, snap: str, index: int, rec: dict[str, str]) -> None:
    rid = _record(parts, symbol, snap, "eod", index, rec)
    common = {
        "listing_sk": _sk(f"listing:{symbol}"),
        "instrument_sk": _sk(f"instrument:{symbol}"),
        "trade_date_sk": _sk(f"date:{rec['date']}"),
        "trade_date": rec["date"],
        "quote_currency_sk": _sk("currency"),
    }
    coordinate: dict[str, str | int] = {"trade_date": rec["date"]}
    bar = {k: rec[k] for k in contract.MEASURES[BAR]}
    _observe(parts, symbol, snap, BAR, "bar_day", coordinate, bar, common, rid, index)
    adjusted = {"adjusted_close": rec["adjusted_close"]}
    _observe(parts, symbol, snap, ADJ, "adjusted_close_day", coordinate, adjusted, common, rid, index)


def _distribution(parts: Parts, symbol: str, snap: str, index: int, rec: dict[str, str]) -> None:
    rid = _record(parts, symbol, snap, "div", index, rec)
    further = {
        "instrument_sk": _sk(f"instrument:{symbol}"),
        "currency_sk": _sk("currency"),
        "ex_date_sk": _sk(f"date:{rec['ex_date']}"),
        "declaration_date_sk": _sk("date:declaration"),
        "record_date_sk": _sk("date:record"),
        "payment_date_sk": _sk("date:payment"),
        "ex_date": rec["ex_date"],
        "occurrence": "0",
    }
    measures = {k: rec[k] for k in contract.MEASURES[DIST]}
    coordinate: dict[str, str | int] = {"ex_date": rec["ex_date"], "occurrence": 0}
    _observe(parts, symbol, snap, DIST, "distribution", coordinate, measures, further, rid, index)


def _split(parts: Parts, symbol: str, snap: str, index: int, rec: dict[str, str]) -> None:
    rid = _record(parts, symbol, snap, "splits", index, rec)
    further = {
        "instrument_sk": _sk(f"instrument:{symbol}"),
        "effective_date_sk": _sk(f"date:{rec['effective_date']}"),
        "effective_date": rec["effective_date"],
        "occurrence": "0",
        "new_units": rec["new_units"],
        "old_units": rec["old_units"],
    }
    coordinate: dict[str, str | int] = {"date": rec["effective_date"], "occurrence": 0}
    _observe(parts, symbol, snap, SPLIT, "split", coordinate, {"ratio": rec["ratio"]}, further, rid, index)


def _exclude(parts: Parts, symbol: str, snap: str, index: int) -> None:
    (row,) = [
        r for r in parts.records[(symbol, snap)] if r["fact_table"] == DIST and r["row_index"] == str(index)
    ]
    row["disposition"] = "excluded"
    row["reason"] = CID
    parts.tables["fact_correction_application"].append(
        _row(
            "fact_correction_application",
            application_id=contract.application_id(CID, SNAP[snap], row["source_record_id"]),
            correction_id=CID,
            snapshot_id=SNAP[snap],
            target_source_record_id=row["source_record_id"],
            target_vintage_id=row["vintage_id"],
            disposition="excluded",
        )
    )


def make_parts() -> Parts:
    parts = Parts()
    for name, order in (("s1", "1"), ("s2", "2")):
        parts.tables["snapshot"].append(
            _row(
                "snapshot",
                snapshot_id=SNAP[name],
                name=name,
                source_id="some.source",
                capture_order=order,
                first_retrieved_at=f"2024-02-0{order}T00:00:00Z",
                last_retrieved_at=f"2024-02-0{order}T00:10:00Z",
            )
        )
    for code, symbol, mic, ticker, currency in (
        ("example-fund", ZZZ, "XXXX", "ZZZ", "USD"),
        ("other-fund", YYY, "YYYY", "YYY", "EUR"),
    ):
        listing_sk = _sk(f"listing:{symbol}")
        instrument_sk = _sk(f"instrument:{symbol}")
        parts.tables["dim_instrument"].append(
            _row("dim_instrument", instrument_sk=instrument_sk, instrument_code=code, name="An invented fund")
        )
        parts.tables["dim_listing"].append(
            _row(
                "dim_listing",
                listing_sk=listing_sk,
                instrument_code=code,
                instrument_sk=instrument_sk,
                mic=mic,
                ticker=ticker,
                quote_currency=currency,
            )
        )
        parts.tables["source_identity_mapping"].append(
            _row(
                "source_identity_mapping",
                source_id="some.source",
                source_symbol=symbol,
                instrument_code=code,
                listing_sk=listing_sk,
            )
        )
    for snap in ("s1", "s2"):
        for i in range(11):
            _bar_and_adjusted(parts, ZZZ, snap, i, _eod(i, snap))
        _distribution(parts, ZZZ, snap, 0, DIV0)
        _distribution(parts, ZZZ, snap, 1, DIV1)
        if snap == "s2":
            _distribution(parts, ZZZ, snap, 2, DIV2)
        _split(parts, ZZZ, snap, 0, SPLIT0)
        _exclude(parts, ZZZ, snap, 1)
    _bar_and_adjusted(parts, YYY, "s2", 0, YYY_EOD)
    parts.tables["correction_rule"].append(
        _row(
            "correction_rule",
            correction_id=CID,
            observation_spec_sha256=_h(f"obs{ZZZ}"),
            source_symbol=ZZZ,
            action="exclude_distribution",
            ex_date="2024-01-09",
            reason="a duplicate",
            evidence="an invented note",
        )
    )
    parts.selections = [("compat-v1", {ZZZ: "s2", YYY: "s2"}), ("older", {ZZZ: "s1"})]
    return parts


def _text_ordered(rows: list[dict[str, str]]) -> bytes:
    """A selection CSV sorted with `row_index` as text: valid to the contract module's checks."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(contract.SELECTION_COLUMNS)
    for row in sorted(rows, key=lambda r: (r["fact_table"], r["series_id"], r["row_index"])):
        writer.writerow([row[c] for c in contract.SELECTION_COLUMNS])
    return buffer.getvalue().encode()


def write(root: Path, parts: Parts, *, text_order: bool = False) -> tuple[Path, str]:
    tables = {name: contract.table_bytes(name, rows, CAPTURE) for name, rows in parts.tables.items()}
    selections = {}
    for name, members in parts.selections:
        rows = [r for symbol, snap in members.items() for r in parts.records.get((symbol, snap), [])]
        corrections = {r["reason"] for r in rows if r["disposition"] == "excluded"}
        policy = contract.selection_policy_bytes(name, {s: SNAP[n] for s, n in members.items()}, corrections)
        data = _text_ordered(rows) if text_order else contract.selection_bytes(rows)
        selections[contract.selection_id(policy)] = (policy, data)
    core = contract.manifest_core(
        release_spec={"name": "funds", "version": "0.1.0", "sha256": _h("release spec")},
        register_sha256=_h("register"),
        observation_specs=[{"source_symbol": s, "sha256": _h(f"obs{s}")} for s in (ZZZ, YYY)],
        snapshots=[{"name": n, "manifest_sha256": SNAP[n]} for n in ("s1", "s2")],
        code_commit="0123abc",
        tables=tables,
        selections=selections,
    )
    directory, existed = contract.write_release(root, core, tables, selections)
    assert not existed
    return directory, contract.release_id(core)


@pytest.fixture
def built(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "silver"
    _directory, rid = write(root, make_parts())
    return root, rid


@pytest.fixture
def release(built):
    root, rid = built
    return open_release(root, rid)


def _sel(release, name: str) -> str:
    return release.selection_id(name)


# -- the release ---------------------------------------------------------------------------


def test_open_release_identity(built):
    root, rid = built
    release = open_release(root, rid)
    manifest = (root / "v2" / rid / "manifest.json").read_bytes()
    assert release.release_id == rid
    assert release.core == contract.verify_release(root / "v2" / rid)
    assert release.manifest_sha256 == hashlib.sha256(manifest).hexdigest()
    names = sorted(name for _sid, name in release.selections())
    assert names == ["compat-v1", "older"]
    with pytest.raises(AttributeError):
        release.release_id = "x"  # frozen


def test_table_is_parsed_once_and_cached(release):
    first = release.table("snapshot")
    assert [r["name"] for r in first] == ["s1", "s2"]
    assert release.table("snapshot") is first
    with pytest.raises(ValueError, match="unknown silver table"):
        release.table("nope")


def test_selection_lookup_by_name_and_id(release):
    sid = _sel(release, "compat-v1")
    assert release.selection_id(sid) == sid
    rows = release.selection_rows(sid)
    assert {r["fact_table"] for r in rows} == {BAR, ADJ, DIST, SPLIT}
    assert sum(r["disposition"] == "excluded" for r in rows) == 1
    with pytest.raises(ValueError, match="unknown selection"):
        release.selection_rows("0" * 64)


# -- the export ------------------------------------------------------------------------------


def test_compat_files_exact_bytes(release):
    files = release.compat_files(_sel(release, "compat-v1"), ZZZ)
    assert set(files) == {"closes.csv", "distributions.csv", "splits.csv"}
    assert files["closes.csv"] == CLOSES_S2
    assert files["distributions.csv"] == DISTRIBUTIONS_S2
    assert files["splits.csv"] == SPLITS


def test_compat_files_for_the_second_instrument(release):
    files = release.compat_files(_sel(release, "compat-v1"), YYY)
    assert files["closes.csv"] == b"date,close,adjusted_close\n2024-01-10,7.75,7.70\n"
    assert files["distributions.csv"] == DISTRIBUTIONS_HEADER.encode()
    assert files["splits.csv"] == b"date,ratio\n"


def test_fund_observations_fields(release):
    observed = release.fund_observations(_sel(release, "compat-v1"), ZZZ)
    assert isinstance(observed, FundObservations)
    assert observed.source_id == "some.source"
    assert observed.quote_currency == "USD"
    assert observed.snapshot_id == SNAP["s2"]
    assert observed.snapshot_name == "s2"
    assert observed.closes[1] == {"date": "2024-01-03", "close": "11.30", "adjusted_close": "11.27"}
    assert observed.splits == [{"date": "2024-01-04", "ratio": "2.000000/1.000000"}]
    assert observed.distributions[0] == {
        "ex_date": "2024-01-05",
        "amount": "0.50",
        "split_adjusted_amount": "0.25",
        "currency": "USD",
        "payment_date": "2024-01-15",
        "record_date": "2024-01-08",
        "declaration_date": "2024-01-02",
        "period": "Q4",
    }
    other = release.fund_observations(_sel(release, "compat-v1"), YYY)
    assert other.quote_currency == "EUR"
    with pytest.raises(AttributeError):
        observed.quote_currency = "AUD"  # frozen


def test_adjusted_close_joined_by_source_record_id_including_an_empty_one(release):
    observed = release.fund_observations(_sel(release, "compat-v1"), ZZZ)
    assert observed.closes[3] == {"date": "2024-01-05", "close": "13.25", "adjusted_close": ""}
    assert observed.closes[0]["adjusted_close"] == "10.20"


def test_rows_are_in_numeric_row_index_order(tmp_path):
    root = tmp_path / "silver"
    _directory, rid = write(root, make_parts(), text_order=True)
    release = open_release(root, rid)
    sid = _sel(release, "compat-v1")
    bar_indexes = [r["row_index"] for r in release.selection_rows(sid) if r["series_id"] == f"{ZZZ}.bar_day"]
    assert bar_indexes[:4] == ["0", "1", "10", "2"]  # the file is in text order, so the reader must sort
    files = release.compat_files(sid, ZZZ)
    assert files["closes.csv"] == CLOSES_S2
    assert files["distributions.csv"] == DISTRIBUTIONS_S2


def test_excluded_distribution_is_left_out_and_reported(release):
    observed = release.fund_observations(_sel(release, "compat-v1"), ZZZ)
    assert [d["ex_date"] for d in observed.distributions] == ["2024-01-05", "2024-01-11"]
    assert observed.corrections == [
        {
            "action": "exclude_distribution",
            "ex_date": "2024-01-09",
            "record_sha256": contract.record_sha256(DIV1),
        }
    ]
    # the excluded record stays in the fact table: only the selection leaves it out
    assert len([r for r in release.table(DIST) if r["ex_date"] == "2024-01-09"]) == 1
    assert release.fund_observations(_sel(release, "compat-v1"), YYY).corrections == []


def test_a_selection_of_the_older_snapshot_returns_the_older_vintage(release):
    sid = _sel(release, "older")
    observed = release.fund_observations(sid, ZZZ)
    assert observed.snapshot_name == "s1"
    assert observed.snapshot_id == SNAP["s1"]
    assert observed.closes[1] == {"date": "2024-01-03", "close": "11.25", "adjusted_close": "11.20"}
    files = release.compat_files(sid, ZZZ)
    assert files["closes.csv"] == CLOSES_S1
    assert files["distributions.csv"] == DISTRIBUTIONS_S1
    assert len(observed.corrections) == 1
    # the two vintages of the revised close are both in the fact table
    revised = [
        r
        for r in release.table(BAR)
        if r["trade_date"] == "2024-01-03" and r["series_id"] == f"{ZZZ}.bar_day"
    ]
    assert sorted(r["close"] for r in revised) == ["11.25", "11.30"]


# -- refusals ----------------------------------------------------------------------------------


def test_a_tampered_table_is_refused(built):
    root, rid = built
    path = root / "v2" / rid / "tables" / f"{BAR}.csv"
    path.write_bytes(path.read_bytes().replace(b"11.30", b"11.31"))
    with pytest.raises(ValueError, match="sha256"):
        open_release(root, rid)


def test_a_table_changed_after_opening_is_refused(built):
    root, rid = built
    release = open_release(root, rid)
    path = root / "v2" / rid / "tables" / f"{DIST}.csv"
    path.write_bytes(path.read_bytes().replace(b"0.50", b"0.51"))
    with pytest.raises(ValueError, match="sha256"):
        release.table(DIST)


def test_a_missing_selection_file_is_refused(built):
    root, rid = built
    release = open_release(root, rid)
    sid = _sel(release, "older")
    (root / "v2" / rid / "selections" / f"{sid}.csv").unlink()
    with pytest.raises(ValueError, match="missing file"):
        open_release(root, rid)


def test_a_wrong_release_id_is_refused(built):
    root, rid = built
    with pytest.raises(ValueError, match="not a release directory"):
        open_release(root, "0" * 64)
    with pytest.raises(ValueError, match="sha256"):
        open_release(root, "../" + rid)
    with pytest.raises(ValueError, match="sha256"):
        open_release(root, rid.upper())
    shutil.copytree(root / "v2" / rid, root / "v2" / ("1" * 64))
    with pytest.raises(ValueError, match="directory name"):
        open_release(root, "1" * 64)


def test_unknown_selection_ambiguous_name_and_non_member_are_refused(tmp_path, release):
    with pytest.raises(ValueError, match="unknown selection"):
        release.selection_id("no-such-selection")
    with pytest.raises(ValueError, match="unknown selection"):
        release.fund_observations("0" * 64, ZZZ)
    with pytest.raises(ValueError, match="not a member"):
        release.fund_observations(_sel(release, "older"), YYY)
    with pytest.raises(ValueError, match="not a member"):
        release.fund_observations(_sel(release, "compat-v1"), "QQQ.US")

    parts = make_parts()
    parts.selections = [("twin", {ZZZ: "s1"}), ("twin", {ZZZ: "s2"})]
    _directory, rid = write(tmp_path / "twins", parts)
    twins = open_release(tmp_path / "twins", rid)
    with pytest.raises(ValueError, match="ambiguous"):
        twins.selection_id("twin")
    for sid, _name in twins.selections():  # an id is never ambiguous
        assert twins.selection_id(sid) == sid


def test_a_selected_vintage_missing_from_its_fact_is_refused(tmp_path):
    parts = make_parts()
    parts.tables[BAR] = [
        r
        for r in parts.tables[BAR]
        if not (r["trade_date"] == "2024-01-03" and r["anchor_snapshot_id"] == SNAP["s2"])
    ]
    _directory, rid = write(tmp_path / "silver", parts)
    release = open_release(tmp_path / "silver", rid)
    with pytest.raises(ValueError, match="vintage_id"):
        release.fund_observations(_sel(release, "compat-v1"), ZZZ)
    older = release.fund_observations(_sel(release, "older"), ZZZ)  # the other snapshot is unaffected
    assert older.closes[1]["close"] == "11.25"


def test_an_exclusion_without_an_application_is_refused(tmp_path):
    parts = make_parts()
    parts.tables["fact_correction_application"] = []
    _directory, rid = write(tmp_path / "silver", parts)
    release = open_release(tmp_path / "silver", rid)
    with pytest.raises(ValueError, match="correction application"):
        release.fund_observations(_sel(release, "compat-v1"), ZZZ)


def test_a_bar_without_its_adjusted_close_row_is_refused(tmp_path):
    parts = make_parts()
    parts.records[(ZZZ, "s2")] = [
        r for r in parts.records[(ZZZ, "s2")] if not (r["fact_table"] == ADJ and r["row_index"] == "0")
    ]
    _directory, rid = write(tmp_path / "silver", parts)
    release = open_release(tmp_path / "silver", rid)
    with pytest.raises(ValueError, match="adjusted-close"):
        release.fund_observations(_sel(release, "compat-v1"), ZZZ)


# -- the tool ------------------------------------------------------------------------------------

DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
DECIMAL = re.compile(r"\d+\.\d+")


def run(capsys, root: Path, rid: str, *extra: str, selection: str = "compat-v1", symbol: str = ZZZ):
    code = tool.main(
        [
            "--silver-root",
            str(root),
            "--release",
            rid,
            "--selection",
            selection,
            "--source-symbol",
            symbol,
            *extra,
        ]
    )
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _assert_no_data(*texts: str) -> None:
    for text in texts:
        assert not DATE.search(text)
        assert not DECIMAL.search(text)
        for word in ("USD", "EUR", "Q4"):
            assert word not in text


def test_out_writes_the_three_files_with_private_modes(built, tmp_path, capsys):
    root, rid = built
    out = tmp_path / "export"
    code, stdout, stderr = run(capsys, root, rid, "--out", str(out))
    assert (code, stderr) == (0, "")
    assert stat.S_IMODE(out.stat().st_mode) == 0o700
    expected = {"closes.csv": CLOSES_S2, "distributions.csv": DISTRIBUTIONS_S2, "splits.csv": SPLITS}
    for name, data in expected.items():
        path = out / name
        assert path.read_bytes() == data
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert f"{name}: sha256 {hashlib.sha256(data).hexdigest()} rows {data.count(b'\n') - 1}" in stdout
    assert sorted(p.name for p in out.iterdir()) == sorted(expected)
    _assert_no_data(stdout, stderr)


def test_out_refuses_an_existing_directory_and_one_inside_the_repository(built, tmp_path, capsys):
    root, rid = built
    existing = tmp_path / "there"
    existing.mkdir()
    code, stdout, stderr = run(capsys, root, rid, "--out", str(existing))
    assert (code, stdout) == (2, "")
    assert stderr.startswith("refused:")
    assert list(existing.iterdir()) == []
    inside = REPO / "silver-compat-export-test-output"
    code, stdout, stderr = run(capsys, root, rid, "--out", str(inside))
    assert (code, stdout) == (2, "")
    assert "outside the repository" in stderr
    assert not inside.exists()
    _assert_no_data(stderr)


def test_compare_identical_and_differing(built, tmp_path, capsys):
    root, rid = built
    out = tmp_path / "export"
    assert run(capsys, root, rid, "--out", str(out))[0] == 0
    code, stdout, stderr = run(capsys, root, rid, "--compare", str(out))
    assert (code, stderr) == (0, "")
    for name in ("closes.csv", "distributions.csv", "splits.csv"):
        assert f"{name}: identical" in stdout
        assert f"{name}: sha256 " in stdout
    (out / "distributions.csv").write_bytes(b"changed\n")
    (out / "splits.csv").unlink()
    code, stdout, stderr = run(capsys, root, rid, "--compare", str(out))
    assert (code, stderr) == (1, "")
    assert "closes.csv: identical" in stdout
    assert "distributions.csv: differs" in stdout
    assert "splits.csv: differs" in stdout
    _assert_no_data(stdout, stderr)


def test_compare_with_the_other_snapshots_files_differs(built, tmp_path, capsys):
    root, rid = built
    older = tmp_path / "older"
    assert run(capsys, root, rid, "--out", str(older), selection="older")[0] == 0
    code, stdout, _stderr = run(capsys, root, rid, "--compare", str(older))
    assert code == 1
    assert "closes.csv: differs" in stdout
    assert "distributions.csv: differs" in stdout
    assert "splits.csv: identical" in stdout


def test_the_tool_refuses_what_the_reader_refuses(built, tmp_path, capsys):
    root, rid = built
    out = tmp_path / "export"
    for symbol, selection, release_id in (
        ("QQQ.US", "compat-v1", rid),
        (YYY, "older", rid),
        (ZZZ, "no-such-selection", rid),
        (ZZZ, "compat-v1", "0" * 64),
    ):
        code, stdout, stderr = run(
            capsys, root, release_id, "--out", str(out), selection=selection, symbol=symbol
        )
        assert (code, stdout) == (2, "")
        assert stderr.startswith("refused:")
        _assert_no_data(stderr)
    assert not out.exists()


def test_the_selection_may_be_given_by_id(built, tmp_path, capsys):
    root, rid = built
    sid = open_release(root, rid).selection_id("compat-v1")
    code, stdout, _stderr = run(capsys, root, rid, "--out", str(tmp_path / "by-id"), selection=sid)
    assert code == 0
    assert f"selection_id: {sid}" in stdout
    assert (tmp_path / "by-id" / "closes.csv").read_bytes() == CLOSES_S2


def test_out_and_compare_are_exclusive_and_one_is_required(built, tmp_path):
    root, rid = built
    base = ["--silver-root", str(root), "--release", rid, "--selection", "compat-v1", "--source-symbol", ZZZ]
    with pytest.raises(SystemExit):
        tool.main(base)
    with pytest.raises(SystemExit):
        tool.main([*base, "--out", str(tmp_path / "a"), "--compare", str(tmp_path / "b")])
