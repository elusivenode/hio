"""Silver version 2 release builder: `hio.marketdata.silver_build` and `tools/silver_release.py`.

Every input is invented: a two-snapshot bronze tree of two funds, written as literal JSON text so the
exactness of numbers is testable. Tests run no git: the commit is a parameter.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml

from hio.contracts import silver
from hio.contracts.canonical import canonical_json, sha256_hex
from hio.marketdata import silver_build as sb

REPO = Path(__file__).resolve().parent.parent
COMMIT = "a" * 40
SOURCE = "test.source"
ZZZ = "ZZZ.US"
YYY = "YYY.AU"

# --------------------------------------------------------------------------------------
# Invented bronze text
# --------------------------------------------------------------------------------------

EOD1 = """[
 {"date": "2020-01-02", "open": 10.10, "high": 10.50, "low": 10.00, "close": 10.30, "volume": 1000,
  "adjusted_close": 9.900},
 {"date": "2020-01-03", "open": 10.3, "high": 10.6, "low": 10.2, "close": 10.40, "volume": 2000,
  "adjusted_close": null},
 {"date": "2020-01-06", "open": 10.4, "high": 10.8, "low": 10.3, "close": 10.50, "volume": 3000}
]"""
EOD2 = """[
 {"date": "2020-01-02", "open": 10.10, "high": 10.50, "low": 10.00, "close": 10.30, "volume": 1000,
  "adjusted_close": 9.900},
 {"date": "2020-01-03", "open": 10.3, "high": 10.6, "low": 10.2, "close": 10.45, "volume": 2000,
  "adjusted_close": null},
 {"date": "2020-01-06", "open": 10.4, "high": 10.8, "low": 10.3, "close": 10.50, "volume": 3000},
 {"date": "2020-01-07", "open": 10.5, "high": 10.9, "low": 10.4, "close": 10.60, "volume": 4000,
  "adjusted_close": 10.10}
]"""
DIV = """[
 {"date": "2020-03-05", "unadjustedValue": 0.50, "value": 0.50, "currency": "USD",
  "declarationDate": "2020-02-20", "recordDate": "2020-03-06", "paymentDate": "2020-03-20",
  "period": "Quarterly", "franking": null},
 {"date": "2020-06-05", "unadjustedValue": 0.25, "value": 0.25, "currency": "USD",
  "declarationDate": null, "recordDate": "2020-06-06", "paymentDate": "2020-06-20", "period": null},
 {"date": "2020-06-05", "unadjustedValue": 0.75, "value": 0.75, "currency": "USD",
  "declarationDate": "2020-05-20", "recordDate": "2020-06-06", "paymentDate": "2020-06-20",
  "period": "Quarterly"},
 {"date": "2020-09-04", "unadjustedValue": 0.10, "value": 0.10, "currency": "USD",
  "declarationDate": "", "recordDate": "2020-09-07", "paymentDate": "2020-09-21",
  "period": "Quarterly"}
]"""
SPLITS = """[
 {"date": "2020-04-01", "split": "2.000000/1.000000"},
 {"date": "2020-05-01", "split": null}
]"""
YYY_EOD = """[
 {"date": "2020-01-02", "open": 20.5, "high": 21.0, "low": 20.0, "close": 20.75, "volume": 50,
  "adjusted_close": 20.70},
 {"date": "2020-01-03", "open": 20.7, "high": 21.1, "low": 20.6, "close": 20.80, "volume": 60,
  "adjusted_close": 20.75}
]"""
US_LIST1 = """[
 {"Code": "ZZZ", "Name": "Zed Fund", "Country": "USA", "Exchange": "NYSE ARCA", "Currency": "USD",
  "Isin": "US0000000001", "Type": "ETF"},
 {"Code": "OTHER", "Name": "Other", "Country": "USA", "Exchange": "NYSE ARCA", "Currency": "EUR",
  "Isin": null, "Type": "ETF"}
]"""
US_LIST2 = US_LIST1.replace("Zed Fund", "Zed Fund II")
AU_LIST1 = """[
 {"Code": "YYY", "Name": "Why Fund", "Country": "Australia", "Exchange": "AU", "Currency": "AUD",
  "Isin": null, "Type": "ETF"}
]"""
AU_LIST2 = """[
 {"Code": "OTHER", "Name": "Other", "Country": "Australia", "Exchange": "AU", "Currency": "AUD",
  "Isin": null, "Type": "ETF"}
]"""


def full_snapshot(
    name: str,
    day: str,
    *,
    zzz_eod: str = EOD1,
    zzz_div: str = DIV,
    zzz_splits: str = SPLITS,
    yyy_eod: str = YYY_EOD,
    us_list: str = US_LIST1,
    au_list: str = AU_LIST1,
) -> dict[str, Any]:
    return {
        "name": name,
        "day": day,
        "files": {
            (ZZZ, "eod"): zzz_eod,
            (ZZZ, "div"): zzz_div,
            (ZZZ, "splits"): zzz_splits,
            (YYY, "eod"): yyy_eod,
            (YYY, "div"): "[]",
            (YYY, "splits"): "[]",
            ("EXCHANGE.US", "symbols"): us_list,
            ("EXCHANGE.AU", "symbols"): au_list,
        },
    }


def default_snaps() -> list[dict[str, Any]]:
    return [
        full_snapshot("s1", "2026-01-10"),
        full_snapshot("s2", "2026-02-10", zzz_eod=EOD2, us_list=US_LIST2, au_list=AU_LIST2),
    ]


def write_bronze(root: Path, snaps: list[dict[str, Any]]) -> dict[str, str]:
    pins: dict[str, str] = {}
    for snap in snaps:
        directory = root / "raw" / snap["name"]
        directory.mkdir(parents=True)
        entries = []
        for i, ((symbol, kind), text) in enumerate(snap["files"].items()):
            data = text.encode()
            filename = f"{symbol}.{kind}.json"
            (directory / filename).write_bytes(data)
            entries.append(
                {
                    "path": f"raw/{snap['name']}/{filename}",
                    "sha256": sha256_hex(data),
                    "kind": kind,
                    "symbol": symbol,
                    "retrieved_at": f"{snap['day']}T01:00:{i:02d}+00:00",
                    "bytes": len(data),
                }
            )
        manifest = {"source_id": SOURCE, "snapshot": snap["name"], "stopped": None, "files": entries}
        data = (json.dumps(manifest, indent=1) + "\n").encode()
        (directory / "manifest.json").write_bytes(data)
        pins[snap["name"]] = sha256_hex(data)
    return pins


def default_docs(pins: dict[str, str]) -> dict[str, Any]:
    names = list(pins)
    spec = {
        "identity": {"release_name": "testfunds", "version": "0.1.0", "status": "proposed"},
        "schema": "hio.silver/2",
        "source_id": SOURCE,
        "snapshots": [{"name": n, "manifest_sha256": pins[n]} for n in names],
        "instruments": [ZZZ, YYY],
        "selections": [
            {"name": "compat-v1", "members": {ZZZ: names[-1], YYY: names[0]}},
            {"name": "older", "members": {ZZZ: names[0]}},
        ],
    }
    register = {
        "status": "proposed",
        "instruments": [
            {
                "instrument_code": "zed-fund",
                "name": "Zed Fund",
                "issuer_code": "zed-issuer",
                "vehicle_type": "etf",
                "domicile": "US",
                "listings": [{"mic": "XXXX", "ticker": "ZZZ", "quote_currency": "USD", "valid_from": None}],
                "source_mappings": [
                    {"source_id": SOURCE, "source_symbol": ZZZ, "mic": "XXXX", "ticker": "ZZZ"}
                ],
            },
            {
                "instrument_code": "why-fund",
                "name": "Why Fund",
                "issuer_code": "why-issuer",
                "vehicle_type": "etf",
                "domicile": "AU",
                "listings": [
                    {"mic": "XASX", "ticker": "YYY", "quote_currency": "AUD", "valid_from": "2019-05-01"}
                ],
                "source_mappings": [
                    {"source_id": SOURCE, "source_symbol": YYY, "mic": "XASX", "ticker": "YYY"}
                ],
            },
        ],
    }
    obs = {
        ZZZ: {
            "identity": {"instrument": ZZZ, "version": "0.1.0", "status": "proposed"},
            "source": {"source_id": SOURCE, "quote_currency": "USD"},
            "corrections": [
                {
                    "action": "exclude_distribution",
                    "ex_date": "2020-09-04",
                    "reason": "invented duplicate",
                    "evidence": "invented.md",
                }
            ],
            "changelog": ["0.1.0: invented"],
        },
        YYY: {
            "identity": {"instrument": YYY, "version": "0.1.0", "status": "proposed"},
            "source": {"source_id": SOURCE, "quote_currency": "AUD"},
            "corrections": [],
            "changelog": ["0.1.0: invented"],
        },
    }
    return {"spec": spec, "register": register, "obs": obs}


@dataclass
class World:
    root: Path
    spec: Path
    register: Path
    observations: Path
    bronze: Path
    silver: Path
    pins: dict[str, str]

    def build(self, commit: str = COMMIT) -> tuple[Path, dict[str, Any], bool]:
        return sb.build_release(
            self.spec, self.register, self.observations, self.bronze, self.silver, commit=commit
        )

    def obs_path(self, symbol: str) -> Path:
        return self.observations / f"{symbol}.yaml"


def make_world(tmp_path: Path, name: str = "w", *, snaps=None, edit=None) -> World:
    root = tmp_path / name
    root.mkdir()
    bronze = root / "bronze"
    pins = write_bronze(bronze, snaps if snaps is not None else default_snaps())
    docs = default_docs(pins)
    if edit is not None:
        edit(docs)
    observations = root / "observations"
    observations.mkdir()
    for symbol, doc in docs["obs"].items():
        (observations / f"{symbol}.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
    (root / "spec.yaml").write_text(yaml.safe_dump(docs["spec"], sort_keys=False))
    (root / "register.yaml").write_text(yaml.safe_dump(docs["register"], sort_keys=False))
    return World(
        root, root / "spec.yaml", root / "register.yaml", observations, bronze, root / "silver", pins
    )


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


@pytest.fixture
def built(world: World) -> tuple[World, Path, dict[str, Any]]:
    release_dir, core, existed = world.build()
    assert existed is False
    return world, release_dir, core


def table(release_dir: Path, name: str) -> list[dict[str, str]]:
    return silver.parse_table(name, (release_dir / "tables" / f"{name}.csv").read_bytes())


def pick(rows: list[dict[str, str]], **conditions: str) -> list[dict[str, str]]:
    return [r for r in rows if all(r[k] == v for k, v in conditions.items())]


def one(rows: list[dict[str, str]], **conditions: str) -> dict[str, str]:
    found = pick(rows, **conditions)
    assert len(found) == 1, found
    return found[0]


def tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def sk_date(day: str) -> str:
    return silver.sk("date", {"date": day})


SENTINEL = {"sentinel": "not_recorded"}

# --------------------------------------------------------------------------------------
# Tables: counts and exact rows
# --------------------------------------------------------------------------------------

EXPECTED_ROWS = {
    "dim_date": 18,
    "dim_currency": 3,
    "dim_source": 1,
    "dim_instrument": 2,
    "dim_listing": 2,
    "dim_source_listing": 3,
    "dim_series": 8,
    "dim_audit": 1,
    "snapshot": 2,
    "snapshot_member": 16,
    "source_record": 15,
    "source_identity_mapping": 2,
    "bridge_vintage_support": 34,
    "fact_listing_bar_day": 7,
    "fact_vendor_adjusted_close_day": 6,
    "fact_distribution_event": 4,
    "fact_split_event": 2,
    "fact_listing_presence": 3,
    "correction_rule": 1,
    "fact_correction_application": 2,
}


def test_every_table_is_written_with_the_expected_row_count(built) -> None:
    _, release_dir, core = built
    assert set(EXPECTED_ROWS) == set(silver.TABLES)
    assert {e["name"]: e["rows"] for e in core["tables"]} == EXPECTED_ROWS
    for name, count in EXPECTED_ROWS.items():
        assert len(table(release_dir, name)) == count, name
    assert sorted(e["rows"] for e in core["selections"]) == [12, 18]


def test_dimension_rows_are_exact(built) -> None:
    world, release_dir, _ = built
    assert table(release_dir, "dim_source") == [
        {"source_sk": silver.sk("source", {"source_id": SOURCE}), "source_id": SOURCE}
    ]
    currencies = table(release_dir, "dim_currency")
    assert sorted(r["code"] for r in currencies) == ["", "AUD", "USD"]
    assert one(currencies, code="")["currency_sk"] == silver.sk("currency", SENTINEL)
    assert one(currencies, code="USD")["currency_sk"] == silver.sk("currency", {"code": "USD"})
    dates = table(release_dir, "dim_date")
    assert one(dates, date="2020-01-02") == {
        "date_sk": sk_date("2020-01-02"),
        "date": "2020-01-02",
        "year": "2020",
        "month": "1",
        "day": "2",
        "iso_weekday": "4",
    }
    assert one(dates, date="") == {
        "date_sk": silver.sk("date", SENTINEL),
        "date": "",
        "year": "",
        "month": "",
        "day": "",
        "iso_weekday": "",
    }
    attributes = {"name": "Zed Fund", "issuer_code": "zed-issuer", "vehicle_type": "etf", "domicile": "US"}
    instrument_sk = silver.sk(
        "instrument",
        {"instrument_code": "zed-fund"},
        {"attributes_sha256": silver.attributes_sha256(attributes)},
    )
    assert one(table(release_dir, "dim_instrument"), instrument_code="zed-fund") == {
        "instrument_sk": instrument_sk,
        "instrument_code": "zed-fund",
        **attributes,
    }
    listing_sk = silver.sk(
        "listing", {"instrument_code": "why-fund", "mic": "XASX", "ticker": "YYY", "valid_from": "2019-05-01"}
    )
    assert one(table(release_dir, "dim_listing"), instrument_code="why-fund") == {
        "listing_sk": listing_sk,
        "instrument_code": "why-fund",
        "instrument_sk": one(table(release_dir, "dim_instrument"), instrument_code="why-fund")[
            "instrument_sk"
        ],
        "mic": "XASX",
        "ticker": "YYY",
        "valid_from": "2019-05-01",
        "quote_currency": "AUD",
    }
    assert one(table(release_dir, "dim_listing"), instrument_code="zed-fund")["valid_from"] == ""
    assert table(release_dir, "source_identity_mapping")[0] == {
        "source_id": SOURCE,
        "source_symbol": YYY,
        "instrument_code": "why-fund",
        "listing_sk": listing_sk,
    }
    series = one(table(release_dir, "dim_series"), series_id=f"{ZZZ}.adjusted_close_day")
    assert series == {
        "series_sk": silver.sk("series", {"series_id": f"{ZZZ}.adjusted_close_day"}, {"definition": "1"}),
        "series_id": f"{ZZZ}.adjusted_close_day",
        "source_id": SOURCE,
        "source_symbol": ZZZ,
        "quantity": "adjusted_close_day",
    }
    spec_sha = sha256_hex(world.spec.read_bytes())
    register_sha = sha256_hex(world.register.read_bytes())
    obs_hashes = sorted(sha256_hex(world.obs_path(s).read_bytes()) for s in (ZZZ, YYY))
    audit = {
        "schema": "hio.silver/2",
        "code_commit": COMMIT,
        "release_spec_sha256": spec_sha,
        "register_sha256": register_sha,
        "observation_specs_sha256": sha256_hex(canonical_json(obs_hashes)),
    }
    assert table(release_dir, "dim_audit") == [{"audit_sk": silver.sk("audit", audit), **audit}]


def test_source_listings_hold_one_row_per_attribute_set_and_presence_follows_the_lists(built) -> None:
    _, release_dir, _ = built
    listings = table(release_dir, "dim_source_listing")
    zzz = pick(listings, source_symbol=ZZZ)
    assert sorted(r["name"] for r in zzz) == ["Zed Fund", "Zed Fund II"]
    assert len({r["source_listing_sk"] for r in zzz}) == 2
    first = one(zzz, name="Zed Fund")
    assert first == {
        "source_listing_sk": first["source_listing_sk"],
        "source_id": SOURCE,
        "source_symbol": ZZZ,
        "vendor_code": "ZZZ",
        "vendor_exchange": "US",
        "name": "Zed Fund",
        "country": "USA",
        "exchange": "NYSE ARCA",
        "currency": "USD",
        "isin": "US0000000001",
        "type": "ETF",
    }
    assert one(listings, source_symbol=YYY)["isin"] == ""  # null: an empty cell
    snapshots = {r["name"]: r["snapshot_id"] for r in table(release_dir, "snapshot")}
    presence = table(release_dir, "fact_listing_presence")
    # YYY is absent from the second snapshot's list: no presence row for it there.
    assert len(pick(presence, snapshot_id=snapshots["s2"])) == 1
    assert len(pick(presence, snapshot_id=snapshots["s1"])) == 2
    row = one(presence, snapshot_id=snapshots["s2"])
    assert row["source_listing_sk"] == one(zzz, name="Zed Fund II")["source_listing_sk"]
    assert row["currency_sk"] == silver.sk("currency", {"code": "USD"})


def test_snapshot_and_member_tables(built) -> None:
    world, release_dir, _ = built
    snapshots = table(release_dir, "snapshot")
    assert [(r["name"], r["capture_order"], r["source_id"]) for r in snapshots] == [
        ("s1", "1", SOURCE),
        ("s2", "2", SOURCE),
    ]
    assert [r["snapshot_id"] for r in snapshots] == [world.pins["s1"], world.pins["s2"]]
    assert snapshots[0]["first_retrieved_at"] == "2026-01-10T01:00:00+00:00"
    assert snapshots[0]["last_retrieved_at"] == "2026-01-10T01:00:07+00:00"
    members = pick(table(release_dir, "snapshot_member"), snapshot_id=world.pins["s1"])
    assert len(members) == 8
    exchange = one(members, source_symbol="EXCHANGE.US")
    assert exchange["kind"] == "symbols"
    assert exchange["path"] == "raw/s1/EXCHANGE.US.symbols.json"
    assert exchange["file_sha256"] == sha256_hex(US_LIST1.encode())
    assert [m["path"] for m in members] == sorted(m["path"] for m in members)


def test_a_source_number_is_its_exact_text_and_nulls_are_empty_cells(built) -> None:
    _, release_dir, _ = built
    bars = table(release_dir, "fact_listing_bar_day")
    first = one(bars, series_id=f"{ZZZ}.bar_day", trade_date="2020-01-02")
    assert (first["open"], first["high"], first["low"], first["close"], first["volume"]) == (
        "10.10",
        "10.50",
        "10.00",
        "10.30",
        "1000",
    )
    assert first["trade_date_sk"] == sk_date("2020-01-02")
    assert first["quote_currency_sk"] == silver.sk("currency", {"code": "USD"})
    adjusted = table(release_dir, "fact_vendor_adjusted_close_day")
    assert (
        one(adjusted, series_id=f"{ZZZ}.adjusted_close_day", trade_date="2020-01-02")["adjusted_close"]
        == "9.900"
    )
    # null and absent adjusted closes are both empty cells, and the row still exists.
    assert (
        one(adjusted, series_id=f"{ZZZ}.adjusted_close_day", trade_date="2020-01-03")["adjusted_close"] == ""
    )
    assert (
        one(adjusted, series_id=f"{ZZZ}.adjusted_close_day", trade_date="2020-01-06")["adjusted_close"] == ""
    )
    distributions = table(release_dir, "fact_distribution_event")
    null_declaration = one(distributions, ex_date="2020-06-05", declaration_date="")
    assert null_declaration["declaration_date_sk"] == silver.sk("date", SENTINEL)
    assert null_declaration["period_label"] == ""  # absent key
    assert null_declaration["franking"] == ""
    empty_string = one(distributions, ex_date="2020-09-04")
    assert empty_string["declaration_date"] == ""
    assert empty_string["declaration_date_sk"] == silver.sk("date", SENTINEL)
    assert empty_string["record_date_sk"] == sk_date("2020-09-07")
    assert empty_string["amount_unadjusted"] == "0.10"
    assert empty_string["currency_sk"] == silver.sk("currency", {"code": "USD"})


def test_a_splits_new_and_old_units(built) -> None:
    _, release_dir, _ = built
    splits = table(release_dir, "fact_split_event")
    two_for_one = one(splits, effective_date="2020-04-01")
    assert (two_for_one["ratio"], two_for_one["new_units"], two_for_one["old_units"]) == (
        "2.000000/1.000000",
        "2.000000",
        "1.000000",
    )
    assert two_for_one["occurrence"] == "0"
    assert two_for_one["effective_date_sk"] == sk_date("2020-04-01")
    null_ratio = one(splits, effective_date="2020-05-01")
    assert (null_ratio["ratio"], null_ratio["new_units"], null_ratio["old_units"]) == ("", "", "")


# --------------------------------------------------------------------------------------
# Vintages
# --------------------------------------------------------------------------------------


def test_an_unchanged_row_in_both_snapshots_is_one_fact_row_and_two_bridge_rows(built) -> None:
    world, release_dir, _ = built
    bars = pick(
        table(release_dir, "fact_listing_bar_day"), series_id=f"{ZZZ}.bar_day", trade_date="2020-01-02"
    )
    assert len(bars) == 1
    bridge = pick(table(release_dir, "bridge_vintage_support"), vintage_id=bars[0]["vintage_id"])
    assert sorted(r["snapshot_id"] for r in bridge) == sorted(world.pins.values())
    assert len({r["source_record_id"] for r in bridge}) == 2  # two files, two records
    assert bars[0]["anchor_snapshot_id"] == world.pins["s1"]
    assert bars[0]["first_captured_at"] == "2026-01-10T01:00:00+00:00"
    # the adjusted close of the same row is a separate observation with its own single vintage.
    adjusted = pick(
        table(release_dir, "fact_vendor_adjusted_close_day"),
        series_id=f"{ZZZ}.adjusted_close_day",
        trade_date="2020-01-02",
    )
    assert len(adjusted) == 1
    assert adjusted[0]["observation_id"] != bars[0]["observation_id"]


def test_a_revised_close_gives_two_vintages_of_one_observation(built) -> None:
    world, release_dir, _ = built
    bars = pick(
        table(release_dir, "fact_listing_bar_day"), series_id=f"{ZZZ}.bar_day", trade_date="2020-01-03"
    )
    assert [(r["close"], r["anchor_snapshot_id"]) for r in bars] == [
        ("10.40", world.pins["s1"]),
        ("10.45", world.pins["s2"]),
    ]
    assert len({r["observation_id"] for r in bars}) == 1
    assert bars[0]["observation_id"] == silver.observation_id(f"{ZZZ}.bar_day", {"trade_date": "2020-01-03"})
    assert bars[0]["vintage_id"] != bars[1]["vintage_id"]
    fingerprint = silver.value_fingerprint(
        {"open": "10.3", "high": "10.6", "low": "10.2", "close": "10.45", "volume": "2000"}
    )
    assert bars[1]["vintage_id"] == silver.vintage_id(
        bars[1]["observation_id"], fingerprint, world.pins["s2"]
    )
    assert bars[1]["first_captured_at"] == "2026-02-10T01:00:00+00:00"
    # the revised row's adjusted close (null both times) did not change.
    adjusted = pick(
        table(release_dir, "fact_vendor_adjusted_close_day"),
        series_id=f"{ZZZ}.adjusted_close_day",
        trade_date="2020-01-03",
    )
    assert len(adjusted) == 1
    # a row first seen in the second snapshot is anchored there.
    new_day = one(
        table(release_dir, "fact_listing_bar_day"), series_id=f"{ZZZ}.bar_day", trade_date="2020-01-07"
    )
    assert new_day["anchor_snapshot_id"] == world.pins["s2"]


def test_a_value_that_goes_a_b_a_gives_three_vintages(tmp_path: Path) -> None:
    def eod(close: str) -> str:
        return f'[{{"date": "2020-01-02", "open": 1, "high": 2, "low": 1, "close": {close}, "volume": 5}}]'

    snaps = [
        full_snapshot("s1", "2026-01-10", zzz_eod=eod("10.30")),
        full_snapshot("s2", "2026-02-10", zzz_eod=eod("10.35")),
        full_snapshot("s3", "2026-03-10", zzz_eod=eod("10.30")),
    ]
    world = make_world(tmp_path, snaps=snaps)
    release_dir, _, _ = world.build()
    bars = pick(table(release_dir, "fact_listing_bar_day"), series_id=f"{ZZZ}.bar_day")
    assert [r["close"] for r in bars] == ["10.30", "10.35", "10.30"]
    assert len({r["vintage_id"] for r in bars}) == 3
    assert len({r["observation_id"] for r in bars}) == 1
    assert [r["anchor_snapshot_id"] for r in bars] == [world.pins[n] for n in ("s1", "s2", "s3")]
    bridge = table(release_dir, "bridge_vintage_support")
    for row in bars:
        assert len(pick(bridge, vintage_id=row["vintage_id"])) == 1


def test_a_record_absent_from_a_later_snapshot_changes_nothing(tmp_path: Path) -> None:
    short = (
        '[{"date": "2020-01-02", "open": 10.10, "high": 10.50, "low": 10.00, "close": 10.30,'
        ' "volume": 1000, "adjusted_close": 9.900}]'
    )
    snaps = [full_snapshot("s1", "2026-01-10"), full_snapshot("s2", "2026-02-10", zzz_eod=short)]
    world = make_world(tmp_path, snaps=snaps)
    release_dir, _, _ = world.build()
    bars = pick(table(release_dir, "fact_listing_bar_day"), series_id=f"{ZZZ}.bar_day")
    assert sorted(r["trade_date"] for r in bars) == ["2020-01-02", "2020-01-03", "2020-01-06"]


def test_an_instrument_need_not_have_files_in_every_snapshot(tmp_path: Path) -> None:
    second = full_snapshot("s2", "2026-02-10")
    for key in [(ZZZ, "div"), (ZZZ, "splits")]:
        del second["files"][key]

    def edit(docs: dict[str, Any]) -> None:
        docs["spec"]["selections"][0]["members"][ZZZ] = "s1"  # a selection of s2 would be refused

    world = make_world(tmp_path, snaps=[full_snapshot("s1", "2026-01-10"), second], edit=edit)
    release_dir, core, _ = world.build()
    assert len(table(release_dir, "fact_distribution_event")) == 4
    applications = table(release_dir, "fact_correction_application")
    assert [a["snapshot_id"] for a in applications] == [world.pins["s1"]]
    assert {e["name"] for e in core["selections"]} == {"compat-v1", "older"}


def test_a_selection_member_whose_snapshot_lacks_a_file_refuses(tmp_path: Path) -> None:
    second = full_snapshot("s2", "2026-02-10")
    del second["files"][(ZZZ, "splits")]
    world = make_world(tmp_path, snaps=[full_snapshot("s1", "2026-01-10"), second])
    with pytest.raises(ValueError, match="lacks its splits file"):
        world.build()


def test_the_same_file_in_two_snapshots_gives_its_source_records_once(built) -> None:
    _, release_dir, _ = built
    div_sha = sha256_hex(DIV.encode())
    records = pick(table(release_dir, "source_record"), file_sha256=div_sha)
    assert [r["row_index"] for r in records] == ["0", "1", "2", "3"]
    members = pick(table(release_dir, "snapshot_member"), file_sha256=div_sha)
    assert len(members) == 2  # held by both snapshots, listed once each
    parsed = silver.load_json_exact(DIV.encode())
    assert records[1] == {
        "source_record_id": silver.source_record_id(div_sha, 1),
        "file_sha256": div_sha,
        "row_index": "1",
        "record_sha256": silver.record_sha256(parsed[1]),
    }
    assert len(pick(table(release_dir, "source_record"), file_sha256=sha256_hex(EOD1.encode()))) == 3


def test_two_distributions_on_one_ex_date_get_occurrences_in_record_sha_order(built) -> None:
    _, release_dir, _ = built
    parsed = silver.load_json_exact(DIV.encode())
    pair = sorted((parsed[1], parsed[2]), key=silver.record_sha256)
    rows = pick(table(release_dir, "fact_distribution_event"), ex_date="2020-06-05")
    assert [(r["occurrence"], r["amount_unadjusted"]) for r in rows] == [
        ("0", format(pair[0]["unadjustedValue"], "f")),
        ("1", format(pair[1]["unadjustedValue"], "f")),
    ]
    assert rows[0]["observation_id"] == silver.observation_id(
        f"{ZZZ}.distribution", {"ex_date": "2020-06-05", "occurrence": 0}
    )
    # a unique date is occurrence 0.
    assert one(table(release_dir, "fact_distribution_event"), ex_date="2020-03-05")["occurrence"] == "0"
    # each stays one vintage across the two snapshots, with two bridge rows.
    bridge = table(release_dir, "bridge_vintage_support")
    for row in rows:
        assert len(pick(bridge, vintage_id=row["vintage_id"])) == 2


# --------------------------------------------------------------------------------------
# Corrections and selections
# --------------------------------------------------------------------------------------


def selection_of(
    release_dir: Path, core: dict[str, Any], name: str
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    entry = next(e for e in core["selections"] if e["name"] == name)
    sid = entry["selection_id"]
    policy = json.loads((release_dir / "selections" / f"{sid}.json").read_bytes())
    rows = silver.parse_selection((release_dir / "selections" / f"{sid}.csv").read_bytes())
    return policy, rows


def test_a_declared_exclusion_stays_in_the_fact_and_is_excluded_only_in_the_selection(built) -> None:
    world, release_dir, core = built
    excluded_fact = one(table(release_dir, "fact_distribution_event"), ex_date="2020-09-04")
    assert excluded_fact["amount_unadjusted"] == "0.10"  # the record stays in the fact
    ospec_sha = sha256_hex(world.obs_path(ZZZ).read_bytes())
    cid = silver.correction_id(ospec_sha, "exclude_distribution", "2020-09-04")
    rule = table(release_dir, "correction_rule")
    assert rule == [
        {
            "correction_id": cid,
            "observation_spec_sha256": ospec_sha,
            "source_symbol": ZZZ,
            "action": "exclude_distribution",
            "ex_date": "2020-09-04",
            "reason": "invented duplicate",
            "evidence": "invented.md",
        }
    ]
    applications = table(release_dir, "fact_correction_application")
    assert sorted(a["snapshot_id"] for a in applications) == sorted(world.pins.values())  # one per snapshot
    div_sha = sha256_hex(DIV.encode())
    target = silver.source_record_id(div_sha, 3)
    for application in applications:
        assert application["target_source_record_id"] == target
        assert application["correction_id"] == cid
        assert application["disposition"] == "excluded"
        assert application["application_id"] == silver.application_id(cid, application["snapshot_id"], target)
    assert {a["target_vintage_id"] for a in applications} == {excluded_fact["vintage_id"]}

    policy, rows = selection_of(release_dir, core, "compat-v1")
    assert policy["corrections"] == [cid]
    assert policy["members"] == {ZZZ: world.pins["s2"], YYY: world.pins["s1"]}
    assert len(rows) == 18
    excluded = pick(rows, disposition="excluded")
    assert excluded == [
        {
            "fact_table": "fact_distribution_event",
            "series_id": f"{ZZZ}.distribution",
            "observation_id": excluded_fact["observation_id"],
            "vintage_id": excluded_fact["vintage_id"],
            "source_record_id": target,
            "row_index": "3",
            "disposition": "excluded",
            "reason": cid,
        }
    ]
    assert {r["reason"] for r in pick(rows, disposition="selected")} == {""}
    # an eod record gives two rows, one for each of its fact tables.
    eod_sha = sha256_hex(EOD2.encode())
    eod_rows = pick(rows, source_record_id=silver.source_record_id(eod_sha, 0))
    assert sorted(r["fact_table"] for r in eod_rows) == [
        "fact_listing_bar_day",
        "fact_vendor_adjusted_close_day",
    ]


def test_a_selection_that_picks_the_older_snapshot_points_at_the_older_vintages(built) -> None:
    world, release_dir, core = built
    policy, rows = selection_of(release_dir, core, "older")
    assert policy["members"] == {ZZZ: world.pins["s1"]}
    assert len(rows) == 12
    bars = pick(
        table(release_dir, "fact_listing_bar_day"), series_id=f"{ZZZ}.bar_day", trade_date="2020-01-03"
    )
    older = next(b for b in bars if b["anchor_snapshot_id"] == world.pins["s1"])
    chosen = pick(rows, fact_table="fact_listing_bar_day", observation_id=older["observation_id"])
    assert [r["vintage_id"] for r in chosen] == [older["vintage_id"]]
    # in the newer selection the same observation points at the revised vintage.
    _, newer_rows = selection_of(release_dir, core, "compat-v1")
    revised = next(b for b in bars if b["anchor_snapshot_id"] == world.pins["s2"])
    chosen = pick(newer_rows, fact_table="fact_listing_bar_day", observation_id=older["observation_id"])
    assert [r["vintage_id"] for r in chosen] == [revised["vintage_id"]]
    # a selection's rows sort by table, series and the row index as a number.
    keys = [(r["fact_table"], r["series_id"], int(r["row_index"])) for r in newer_rows]
    assert keys == sorted(keys)


def correction_edit(ex_date: str):
    def edit(docs: dict[str, Any]) -> None:
        docs["obs"][ZZZ]["corrections"][0]["ex_date"] = ex_date

    return edit


def test_a_correction_with_no_match_in_the_selected_snapshot_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path, edit=correction_edit("2020-12-31"))
    with pytest.raises(ValueError, match="no application"):
        world.build()


def test_a_correction_found_only_in_another_snapshot_refuses_for_the_selection_that_lacks_it(
    tmp_path: Path,
) -> None:
    only_first = full_snapshot("s1", "2026-01-10")
    without = DIV.replace('"date": "2020-09-04"', '"date": "2020-09-08"')
    second = full_snapshot("s2", "2026-02-10", zzz_div=without)
    world = make_world(tmp_path, snaps=[only_first, second])
    with pytest.raises(ValueError, match="no application"):  # compat-v1 picks s2 for ZZZ
        world.build()


def test_a_correction_matching_several_records_refuses(tmp_path: Path) -> None:
    world = make_world(tmp_path, edit=correction_edit("2020-06-05"))
    with pytest.raises(ValueError, match="matches 2 distribution records"):
        world.build()


def test_a_zero_valued_record_is_not_a_correction_match(tmp_path: Path) -> None:
    zero = DIV.replace('"unadjustedValue": 0.10, "value": 0.10', '"unadjustedValue": 0, "value": 0')
    world = make_world(
        tmp_path,
        snaps=[
            full_snapshot("s1", "2026-01-10", zzz_div=zero),
            full_snapshot("s2", "2026-02-10", zzz_div=zero),
        ],
    )
    with pytest.raises(ValueError, match="no application"):
        world.build()


def test_a_correction_for_an_instrument_outside_every_selection_needs_no_application(tmp_path: Path) -> None:
    def edit(docs: dict[str, Any]) -> None:
        correction_edit("2020-12-31")(docs)
        docs["spec"]["selections"] = [{"name": "yyy-only", "members": {YYY: "s1"}}]

    world = make_world(tmp_path, edit=edit)
    release_dir, _, _ = world.build()
    assert table(release_dir, "fact_correction_application") == []
    assert len(table(release_dir, "correction_rule")) == 1
    assert world.silver in release_dir.parents


# --------------------------------------------------------------------------------------
# Determinism, idempotence, identity
# --------------------------------------------------------------------------------------


def test_the_build_is_idempotent(built) -> None:
    world, release_dir, core = built
    before = tree(world.silver)
    again_dir, again_core, existed = world.build()
    assert (again_dir, again_core, existed) == (release_dir, core, True)
    assert tree(world.silver) == before
    assert release_dir == world.silver / "v2" / silver.release_id(core)


def test_verify_release_passes_and_files_have_private_modes(built) -> None:
    _, release_dir, core = built
    assert silver.verify_release(release_dir) == core
    assert (release_dir / "manifest.json").stat().st_mode & 0o777 == 0o600
    assert release_dir.stat().st_mode & 0o777 == 0o700
    assert core["code_commit"] == COMMIT
    assert core["schema"] == "hio.silver/2"
    assert [s["name"] for s in core["snapshots"]] == ["s1", "s2"]


def test_the_bronze_tree_is_byte_identical_afterwards(world: World) -> None:
    before = tree(world.bronze)
    modes = {p: p.stat().st_mode for p in world.bronze.rglob("*")}
    world.build()
    assert tree(world.bronze) == before
    assert {p: p.stat().st_mode for p in world.bronze.rglob("*")} == modes


def test_permuting_the_instruments_and_dictionary_orders_changes_nothing_but_the_audit_key(
    tmp_path: Path,
) -> None:
    def edit(docs: dict[str, Any]) -> None:
        spec = docs["spec"]
        spec["instruments"].reverse()
        spec["selections"].reverse()
        for selection in spec["selections"]:
            selection["members"] = dict(reversed(list(selection["members"].items())))
        docs["register"]["instruments"].reverse()
        docs["obs"] = dict(reversed(list(docs["obs"].items())))

    a = make_world(tmp_path, "a")
    b = make_world(tmp_path, "b", edit=edit)
    dir_a, core_a, _ = a.build()
    dir_b, core_b, _ = b.build()
    assert a.pins == b.pins
    assert core_a["selections"] == core_b["selections"]
    assert core_a["snapshots"] == core_b["snapshots"]
    for entry in core_a["selections"]:
        for ext in ("json", "csv"):
            name = f"selections/{entry['selection_id']}.{ext}"
            assert (dir_a / name).read_bytes() == (dir_b / name).read_bytes()
    for name in silver.TABLES:
        rows_a, rows_b = table(dir_a, name), table(dir_b, name)
        if name == "dim_audit":
            assert len(rows_a) == len(rows_b) == 1
            continue
        for rows in (rows_a, rows_b):
            for row in rows:
                row.pop("audit_sk", None)
        assert rows_a == rows_b, name
    # a table that does not depend on the audit row is byte-identical.
    for name in ("snapshot", "source_record", "bridge_vintage_support", "dim_series", "correction_rule"):
        path = f"tables/{name}.csv"
        assert (dir_a / path).read_bytes() == (dir_b / path).read_bytes(), name


def test_permuting_a_manifests_file_order_keeps_every_table_the_same_size(tmp_path: Path) -> None:
    # A manifest is pinned by its bytes, so its snapshot_id changes with its file order; the rows do not.
    snaps = default_snaps()
    for snap in snaps:
        snap["files"] = dict(reversed(list(snap["files"].items())))
    a = make_world(tmp_path, "a")
    b = make_world(tmp_path, "b", snaps=snaps)
    dir_a, core_a, _ = a.build()
    dir_b, core_b, _ = b.build()
    assert [e["rows"] for e in core_a["tables"]] == [e["rows"] for e in core_b["tables"]]
    for name in ("dim_date", "dim_currency", "dim_series", "dim_instrument", "dim_listing", "source_record"):
        assert (dir_a / f"tables/{name}.csv").read_bytes() == (dir_b / f"tables/{name}.csv").read_bytes()
    closes_a = [r["close"] for r in table(dir_a, "fact_listing_bar_day")]
    assert closes_a == [r["close"] for r in table(dir_b, "fact_listing_bar_day")]


def test_the_release_id_changes_with_the_commit_an_observation_spec_and_the_register(tmp_path: Path) -> None:
    base = make_world(tmp_path, "base")
    _, core, _ = base.build()
    other_commit = make_world(tmp_path, "commit").build(commit="b" * 40)[1]
    assert silver.release_id(other_commit) != silver.release_id(core)

    changed_obs = make_world(tmp_path, "obs")
    with changed_obs.obs_path(YYY).open("a") as handle:
        handle.write("# a comment changes the bytes\n")
    core_obs = changed_obs.build()[1]
    assert silver.release_id(core_obs) != silver.release_id(core)
    assert {e["source_symbol"]: e["sha256"] for e in core_obs["observation_specs"]}[ZZZ] == {
        e["source_symbol"]: e["sha256"] for e in core["observation_specs"]
    }[ZZZ]

    changed_register = make_world(tmp_path, "register")
    with changed_register.register.open("a") as handle:
        handle.write("# a comment changes the bytes\n")
    core_register = changed_register.build()[1]
    assert core_register["register_sha256"] != core["register_sha256"]
    assert silver.release_id(core_register) != silver.release_id(core)


def test_an_existing_release_with_different_bytes_is_refused(built) -> None:
    world, release_dir, _ = built
    with (release_dir / "tables" / "dim_source.csv").open("ab") as handle:
        handle.write(b"x\n")
    with pytest.raises(ValueError, match="different bytes"):
        world.build()


# --------------------------------------------------------------------------------------
# Refusals (§6)
# --------------------------------------------------------------------------------------


def test_a_pin_that_does_not_match_its_manifest_refuses(tmp_path: Path) -> None:
    def edit(docs: dict[str, Any]) -> None:
        docs["spec"]["snapshots"][0]["manifest_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="does not match its pin"):
        make_world(tmp_path, edit=edit).build()


def test_a_file_that_does_not_match_its_manifest_entry_refuses(world: World) -> None:
    (world.bronze / "raw" / "s2" / f"{ZZZ}.eod.json").write_bytes(EOD1.encode())
    with pytest.raises(ValueError, match="does not match its manifest entry"):
        world.build()
    assert not (world.silver / "v2").exists()


def test_a_missing_bronze_file_refuses(world: World) -> None:
    (world.bronze / "raw" / "s1" / f"{YYY}.eod.json").unlink()
    with pytest.raises(ValueError, match="missing"):
        world.build()


def test_snapshots_out_of_capture_order_refuse(tmp_path: Path) -> None:
    def edit(docs: dict[str, Any]) -> None:
        docs["spec"]["snapshots"].reverse()

    with pytest.raises(ValueError, match="ascending capture order"):
        make_world(tmp_path, edit=edit).build()


def test_snapshots_with_the_same_capture_time_refuse(tmp_path: Path) -> None:
    snaps = [full_snapshot("s1", "2026-01-10"), full_snapshot("s2", "2026-01-10")]
    with pytest.raises(ValueError, match="ascending capture order"):
        make_world(tmp_path, snaps=snaps).build()


def test_an_instrument_with_no_register_mapping_refuses(tmp_path: Path) -> None:
    def edit(docs: dict[str, Any]) -> None:
        docs["register"]["instruments"][1]["source_mappings"] = []

    with pytest.raises(ValueError, match="no register mapping"):
        make_world(tmp_path, edit=edit).build()


def test_an_instrument_with_no_observation_spec_refuses(world: World) -> None:
    world.obs_path(YYY).unlink()
    with pytest.raises(ValueError, match="no observation spec"):
        world.build()


def test_an_instrument_with_no_file_in_any_snapshot_refuses(tmp_path: Path) -> None:
    snaps = default_snaps()
    for snap in snaps:
        for kind in ("eod", "div", "splits"):
            del snap["files"][(YYY, kind)]

    def edit(docs: dict[str, Any]) -> None:
        docs["spec"]["selections"] = [{"name": "zzz", "members": {ZZZ: "s1"}}]

    with pytest.raises(ValueError, match="no file in any snapshot"):
        make_world(tmp_path, snaps=snaps, edit=edit).build()


def test_an_instrument_absent_from_every_exchange_list_refuses(tmp_path: Path) -> None:
    snaps = [
        full_snapshot("s1", "2026-01-10", au_list=AU_LIST2),
        full_snapshot("s2", "2026-02-10", au_list=AU_LIST2),
    ]
    with pytest.raises(ValueError, match="not present in any snapshot's exchange list"):
        make_world(tmp_path, snaps=snaps).build()


def test_a_listing_currency_that_differs_from_the_quote_currency_refuses(tmp_path: Path) -> None:
    snaps = default_snaps()
    snaps[1]["files"][("EXCHANGE.US", "symbols")] = US_LIST2.replace('"Currency": "USD"', '"Currency": "CAD"')
    with pytest.raises(ValueError, match="listing currency differs") as info:
        make_world(tmp_path, snaps=snaps).build()
    assert "CAD" not in str(info.value)


def test_only_the_release_instruments_own_list_entry_is_checked_for_currency(world: World) -> None:
    # the list's other entry states EUR; only the entry whose Code is the instrument's is checked.
    assert world.build()[2] is False


@pytest.mark.parametrize(
    "eod, message",
    [
        (
            '[{"date": "2020-01-03", "close": 1}, {"date": "2020-01-02", "close": 1}]',
            "unique and ascending",
        ),
        ('[{"date": "2020-01-03", "close": 1}, {"date": "2020-01-03", "close": 2}]', "unique and ascending"),
        ('[{"date": "2020-01-03", "close": 0}]', "positive"),
        ('[{"date": "2020-01-03", "close": -1.5}]', "positive"),
        ('[{"date": "2020-01-03", "close": null}]', "positive"),
        ('[{"date": "2020-01-03"}]', "positive"),
        ('[{"date": "2020-1-3", "close": 1}]', "ISO date"),
        ('{"date": "2020-01-03", "close": 1}', "list of records"),
    ],
)
def test_bad_eod_files_refuse(tmp_path: Path, eod: str, message: str) -> None:
    snaps = [full_snapshot("s1", "2026-01-10"), full_snapshot("s2", "2026-02-10", zzz_eod=eod)]
    with pytest.raises(ValueError, match=message):
        make_world(tmp_path, snaps=snaps).build()


def test_a_non_selected_snapshot_is_checked_too(tmp_path: Path) -> None:
    snaps = [
        full_snapshot("s1", "2026-01-10", zzz_eod='[{"date": "2020-01-03", "close": 0}]'),
        default_snaps()[1],
    ]
    with pytest.raises(ValueError, match="positive"):
        make_world(tmp_path, snaps=snaps).build()


def test_an_output_path_inside_the_repository_refuses_and_writes_nothing(world: World) -> None:
    inside = REPO / "silver-output-that-must-not-exist"
    with pytest.raises(ValueError, match="outside the repository"):
        sb.build_release(world.spec, world.register, world.observations, world.bronze, inside, commit=COMMIT)
    assert not inside.exists()
    with pytest.raises(ValueError, match="outside the repository"):
        sb.check_output_path(REPO)


def test_other_refusals(tmp_path: Path, world: World) -> None:
    with pytest.raises(ValueError, match="commit"):
        sb.build_release(
            world.spec, world.register, world.observations, world.bronze, world.silver, commit=" "
        )

    def source(docs: dict[str, Any]) -> None:
        docs["obs"][ZZZ]["source"]["source_id"] = "another.source"

    with pytest.raises(ValueError, match="source_id differs"):
        make_world(tmp_path, "src", edit=source).build()

    def currency(docs: dict[str, Any]) -> None:
        docs["obs"][ZZZ]["source"]["quote_currency"] = "AUD"

    with pytest.raises(ValueError, match="quote currency differs"):
        make_world(tmp_path, "cur", edit=currency).build()

    def instrument(docs: dict[str, Any]) -> None:
        docs["obs"][ZZZ]["identity"]["instrument"] = YYY

    with pytest.raises(ValueError, match="another instrument"):
        make_world(tmp_path, "ins", edit=instrument).build()

    stopped = default_snaps()
    bad = make_world(tmp_path, "stopped", snaps=stopped)
    manifest_path = bad.bronze / "raw" / "s1" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["stopped"] = "HTTP 500"
    manifest_path.write_text(json.dumps(manifest))
    bad_spec = yaml.safe_load(bad.spec.read_text())
    bad_spec["snapshots"][0]["manifest_sha256"] = sha256_hex(manifest_path.read_bytes())
    bad.spec.write_text(yaml.safe_dump(bad_spec, sort_keys=False))
    with pytest.raises(ValueError, match="stopped early"):
        bad.build()


def test_a_manifest_for_another_source_refuses(world: World) -> None:
    def edit(docs: dict[str, Any]) -> None:
        docs["spec"]["source_id"] = "another.source"
        for symbol in docs["obs"]:
            docs["obs"][symbol]["source"]["source_id"] = "another.source"
        for item in docs["register"]["instruments"]:
            item["source_mappings"][0]["source_id"] = "another.source"

    other = make_world(world.root.parent, "other", edit=edit)
    with pytest.raises(ValueError, match="manifest's source_id differs"):
        other.build()


def test_a_snapshot_whose_manifest_path_leaves_the_bronze_root_refuses(world: World) -> None:
    manifest_path = world.bronze / "raw" / "s1" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][0]["path"] = "../outside.json"
    manifest_path.write_text(json.dumps(manifest))
    spec = yaml.safe_load(world.spec.read_text())
    spec["snapshots"][0]["manifest_sha256"] = sha256_hex(manifest_path.read_bytes())
    world.spec.write_text(yaml.safe_dump(spec, sort_keys=False))
    with pytest.raises(ValueError, match="inside the bronze root"):
        world.build()


# --------------------------------------------------------------------------------------
# Spec readers (§3)
# --------------------------------------------------------------------------------------


def test_read_release_spec(world: World) -> None:
    spec = sb.read_release_spec(world.spec)
    assert spec["release_name"] == "testfunds"
    assert spec["version"] == "0.1.0"
    assert spec["source_id"] == SOURCE
    assert spec["instruments"] == [ZZZ, YYY]
    assert spec["snapshots"][1] == {"name": "s2", "manifest_sha256": world.pins["s2"]}
    assert spec["selections"][1] == {"name": "older", "members": {ZZZ: "s1"}}
    assert spec["sha256"] == sha256_hex(world.spec.read_bytes())


def write_yaml(path: Path, doc: Any) -> Path:
    path.write_text(yaml.safe_dump(doc, sort_keys=False))
    return path


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.pop("schema"),
        lambda d: d.update(extra=1),
        lambda d: d.update(schema="hio.silver/1"),
        lambda d: d["identity"].pop("status"),
        lambda d: d["identity"].update(version=1.0),
        lambda d: d.update(source_id=""),
        lambda d: d.update(snapshots=[]),
        lambda d: d["snapshots"][0].update(manifest_sha256="abc"),
        lambda d: d["snapshots"][0].update(name="a/b"),
        lambda d: d["snapshots"].append(dict(d["snapshots"][0])),
        lambda d: d["snapshots"][0].update(extra=1),
        lambda d: d.update(instruments=[]),
        lambda d: d["instruments"].append(d["instruments"][0]),
        lambda d: d["instruments"].append("../x.US"),
        lambda d: d["selections"][0]["members"].update({"NOPE.US": "s1"}),
        lambda d: d["selections"][0]["members"].update({ZZZ: "nope"}),
        lambda d: d["selections"][0].update(members={}),
        lambda d: d["selections"].append(dict(d["selections"][0])),
        lambda d: d["selections"][0].pop("name"),
    ],
)
def test_a_malformed_release_spec_refuses(world: World, tmp_path: Path, mutate) -> None:
    doc = yaml.safe_load(world.spec.read_text())
    mutate(doc)
    with pytest.raises(ValueError):
        sb.read_release_spec(write_yaml(tmp_path / "bad.yaml", doc))


def test_an_unreadable_or_invalid_yaml_spec_refuses(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot be read"):
        sb.read_release_spec(tmp_path / "missing.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("a: [unclosed\n")
    with pytest.raises(ValueError, match="not valid YAML"):
        sb.read_observation_spec(bad)


def test_read_observation_spec(world: World) -> None:
    spec = sb.read_observation_spec(world.obs_path(ZZZ))
    assert spec["instrument"] == ZZZ
    assert spec["source_id"] == SOURCE
    assert spec["quote_currency"] == "USD"
    assert spec["corrections"] == [
        {
            "action": "exclude_distribution",
            "ex_date": "2020-09-04",
            "reason": "invented duplicate",
            "evidence": "invented.md",
        }
    ]
    assert spec["changelog"] == ["0.1.0: invented"]
    assert spec["sha256"] == sha256_hex(world.obs_path(ZZZ).read_bytes())


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.pop("changelog"),
        lambda d: d.update(extra=1),
        lambda d: d["identity"].pop("instrument"),
        lambda d: d["identity"].update(instrument="../x"),
        lambda d: d["source"].pop("quote_currency"),
        lambda d: d["source"].update(source_id=""),
        lambda d: d.update(changelog="one line"),
        lambda d: d.update(corrections="none"),
        lambda d: d["corrections"][0].update(action="drop_distribution"),
        lambda d: d["corrections"][0].update(ex_date="2020-9-4"),
        lambda d: d["corrections"][0].update(extra=1),
        lambda d: d["corrections"][0].pop("evidence"),
        lambda d: d["corrections"][0].update(reason=" "),
        lambda d: d["corrections"].append(dict(d["corrections"][0])),
    ],
)
def test_a_malformed_observation_spec_refuses(world: World, tmp_path: Path, mutate) -> None:
    doc = yaml.safe_load(world.obs_path(ZZZ).read_text())
    mutate(doc)
    with pytest.raises(ValueError):
        sb.read_observation_spec(write_yaml(tmp_path / "bad.yaml", copy.deepcopy(doc)))


def test_the_repositorys_own_specs_read() -> None:
    spec = sb.read_release_spec(REPO / "specs" / "silver" / "funds.yaml")
    assert len(spec["instruments"]) == 9
    assert [s["name"] for s in spec["snapshots"]] == ["s2", "s3", "s4", "s5"]
    assert len(spec["selections"][0]["members"]) == 9
    for path in sorted((REPO / "specs" / "observations").glob("*.yaml")):
        assert sb.read_observation_spec(path)["instrument"] == path.stem


# --------------------------------------------------------------------------------------
# The command
# --------------------------------------------------------------------------------------


@pytest.fixture
def tool(monkeypatch):
    spec = importlib.util.spec_from_file_location("silver_release_tool", REPO / "tools" / "silver_release.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "code_commit", lambda: COMMIT)
    return module


def build_args(world: World) -> list[str]:
    return [
        "build",
        "--spec",
        str(world.spec),
        "--register",
        str(world.register),
        "--observations",
        str(world.observations),
        "--bronze-root",
        str(world.bronze),
        "--silver-root",
        str(world.silver),
    ]


def test_the_build_command_prints_ids_and_counts_only(tool, world: World, capsys) -> None:
    assert tool.main(build_args(world)) == 0
    first = capsys.readouterr().out
    lines = first.splitlines()
    assert re.fullmatch(r"release_id: [0-9a-f]{64}", lines[0])
    release_id = lines[0].split(": ")[1]
    counts = {name: int(count) for name, count in (line.split(": ") for line in lines[1:21])}
    assert counts == EXPECTED_ROWS
    selection_lines = [line for line in lines if line.startswith("selection ")]
    assert len(selection_lines) == 2
    assert all(
        re.fullmatch(r"selection [\w-]+: [0-9a-f]{64} \(\d+ rows, \d+ excluded\)", x) for x in selection_lines
    )
    assert next(x for x in selection_lines if x.startswith("selection compat-v1")).endswith(
        "(18 rows, 1 excluded)"
    )
    assert next(x for x in selection_lines if x.startswith("selection older")).endswith(
        "(12 rows, 1 excluded)"
    )
    assert "already built" not in lines
    assert (world.silver / "v2" / release_id / "manifest.json").is_file()
    # nothing from the data: no date, no decimal.
    assert not re.search(r"\d{4}-\d{2}-\d{2}", first)
    assert not re.search(r"\d\.\d", first)
    for secret in ("Zed", "Why", "10.", "NYSE"):
        assert secret not in first

    assert tool.main(build_args(world)) == 0
    second = capsys.readouterr().out
    assert second.splitlines()[-1] == "already built"
    assert second.splitlines()[:-1] == lines


def test_the_verify_command(tool, world: World, capsys) -> None:
    release_dir, core, _ = world.build()
    release_id = silver.release_id(core)
    args = ["verify", "--silver-root", str(world.silver), "--release", release_id]
    assert tool.main(args) == 0
    assert capsys.readouterr().out == "pass\n"
    with (release_dir / "tables" / "dim_source.csv").open("ab") as handle:
        handle.write(b"x,y\n")
    assert tool.main(args) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("refused: ")
    assert tool.main(["verify", "--silver-root", str(world.silver), "--release", "../x"]) == 2
    assert capsys.readouterr().err.startswith("refused: ")
    assert tool.main(["verify", "--silver-root", str(world.silver), "--release", "f" * 64]) == 2
    assert capsys.readouterr().err.startswith("refused: ")


def test_the_build_command_refuses_without_looking_up_git_for_a_path_inside_the_repository(
    tool, world: World, monkeypatch, capsys
) -> None:
    def no_git() -> str:
        raise AssertionError("git must not be consulted")

    monkeypatch.setattr(tool, "code_commit", no_git)
    args = build_args(world)
    args[-1] = str(REPO / "silver-output-that-must-not-exist")
    assert tool.main(args) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("refused: ")
    assert not (REPO / "silver-output-that-must-not-exist").exists()


def test_a_refused_build_prints_no_data_and_writes_nothing(tool, world: World, capsys) -> None:
    (world.bronze / "raw" / "s2" / f"{ZZZ}.eod.json").write_bytes(EOD1.encode())
    assert tool.main(build_args(world)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("refused: ValueError: ")
    assert not re.search(r"\d{4}-\d{2}-\d{2}", captured.err)
    assert not (world.silver).exists()


def test_a_dirty_tree_refuses(tool, world: World, monkeypatch, capsys) -> None:
    def dirty() -> str:
        raise ValueError("the working tree has uncommitted changes")

    monkeypatch.setattr(tool, "code_commit", dirty)
    assert tool.main(build_args(world)) == 2
    assert "uncommitted" in capsys.readouterr().err


def test_a_copy_of_the_world_builds_the_same_release(tmp_path: Path, world: World) -> None:
    # the build depends on the inputs' bytes, not on where they live.
    copy_root = tmp_path / "copy"
    shutil.copytree(world.root, copy_root)
    copied = World(
        copy_root,
        copy_root / "spec.yaml",
        copy_root / "register.yaml",
        copy_root / "observations",
        copy_root / "bronze",
        copy_root / "silver",
        world.pins,
    )
    assert silver.release_id(copied.build()[1]) == silver.release_id(world.build()[1])
