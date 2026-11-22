"""Tests for the silver v2 contract module (docs/decisions/silver-v2-contract.md). Invented data only."""

from __future__ import annotations

import hashlib
import json
import shutil
import stat
from decimal import Decimal
from pathlib import Path

import pytest

from hio.contracts import silver

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def h(obj: object) -> str:
    """Independent canonical hash: sha256 of sorted, compact, non-ASCII-escaped JSON."""
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def row(table: str, **cells: str) -> dict[str, str]:
    out = dict.fromkeys(silver.TABLES[table], "")
    unknown = set(cells) - set(out)
    assert not unknown, unknown
    out.update(cells)
    return out


# ---------------------------------------------------------------- constants and headers


def test_schema_and_table_order() -> None:
    assert silver.SCHEMA == "hio.silver/2"
    assert list(silver.TABLES) == [
        "dim_date",
        "dim_currency",
        "dim_source",
        "dim_instrument",
        "dim_listing",
        "dim_source_listing",
        "dim_series",
        "dim_audit",
        "snapshot",
        "snapshot_member",
        "source_record",
        "source_identity_mapping",
        "bridge_vintage_support",
        "fact_listing_bar_day",
        "fact_vendor_adjusted_close_day",
        "fact_distribution_event",
        "fact_split_event",
        "fact_listing_presence",
        "correction_rule",
        "fact_correction_application",
    ]
    assert tuple(t for t in silver.TABLES if t.startswith("dim_")) == silver.DIMENSION_TABLES
    assert set(silver.FACT_TABLES) == set(silver.MEASURES)


COMMON = (
    "vintage_id,observation_id,series_id,series_sk,source_sk,audit_sk,"
    "origin_source_record_id,anchor_snapshot_id,first_captured_at"
)


@pytest.mark.parametrize(
    ("table", "header"),
    [
        (
            "fact_listing_bar_day",
            COMMON + ",listing_sk,instrument_sk,trade_date_sk,trade_date,quote_currency_sk,"
            "open,high,low,close,volume",
        ),
        (
            "fact_vendor_adjusted_close_day",
            COMMON + ",listing_sk,instrument_sk,trade_date_sk,trade_date,quote_currency_sk,adjusted_close",
        ),
        (
            "fact_distribution_event",
            COMMON + ",instrument_sk,currency_sk,ex_date_sk,declaration_date_sk,record_date_sk,"
            "payment_date_sk,ex_date,occurrence,declaration_date,record_date,payment_date,"
            "amount_unadjusted,amount_split_adjusted,currency,period_label,franking",
        ),
        (
            "fact_split_event",
            COMMON + ",instrument_sk,effective_date_sk,effective_date,occurrence,ratio,new_units,old_units",
        ),
        (
            "dim_source_listing",
            "source_listing_sk,source_id,source_symbol,vendor_code,vendor_exchange,name,country,"
            "exchange,currency,isin,type",
        ),
        ("dim_date", "date_sk,date,year,month,day,iso_weekday"),
        ("dim_currency", "currency_sk,code"),
        ("dim_source", "source_sk,source_id"),
        ("dim_instrument", "instrument_sk,instrument_code,name,issuer_code,vehicle_type,domicile"),
        ("dim_listing", "listing_sk,instrument_code,instrument_sk,mic,ticker,valid_from,quote_currency"),
        ("dim_series", "series_sk,series_id,source_id,source_symbol,quantity"),
        (
            "dim_audit",
            "audit_sk,schema,code_commit,release_spec_sha256,register_sha256,observation_specs_sha256",
        ),
        ("snapshot", "snapshot_id,name,source_id,capture_order,first_retrieved_at,last_retrieved_at"),
        ("snapshot_member", "snapshot_id,path,file_sha256,kind,source_symbol,retrieved_at"),
        ("source_record", "source_record_id,file_sha256,row_index,record_sha256"),
        ("source_identity_mapping", "source_id,source_symbol,instrument_code,listing_sk"),
        ("bridge_vintage_support", "vintage_id,source_record_id,snapshot_id"),
        ("fact_listing_presence", "source_listing_sk,snapshot_id,instrument_sk,listing_sk,currency_sk"),
        (
            "correction_rule",
            "correction_id,observation_spec_sha256,source_symbol,action,ex_date,reason,evidence",
        ),
        (
            "fact_correction_application",
            "application_id,correction_id,snapshot_id,target_source_record_id,target_vintage_id,disposition",
        ),
    ],
)
def test_headers_are_exactly_the_contract(table: str, header: str) -> None:
    assert ",".join(silver.TABLES[table]) == header
    assert silver.table_bytes(table, [], {}) == (header + "\n").encode()


def test_measures_are_columns_of_their_fact() -> None:
    assert silver.MEASURES["fact_listing_bar_day"] == ("open", "high", "low", "close", "volume")
    assert silver.MEASURES["fact_vendor_adjusted_close_day"] == ("adjusted_close",)
    assert silver.MEASURES["fact_split_event"] == ("ratio",)
    distribution = silver.TABLES["fact_distribution_event"]
    start = distribution.index("declaration_date")
    assert silver.MEASURES["fact_distribution_event"] == distribution[start:]
    for table, measures in silver.MEASURES.items():
        assert silver.TABLES[table][:9] == silver.COMMON_FACT_COLUMNS
        assert set(measures) <= set(silver.TABLES[table])


# ---------------------------------------------------------------- keys


def test_sk_without_and_with_version_identity() -> None:
    plain = h(
        {"key_schema": "hio-dimensional-key/1", "dimension": "date", "durable_key": {"date": "2024-01-02"}}
    )
    assert silver.sk("date", {"date": "2024-01-02"}) == plain
    assert silver.sk("date", {"date": "2024-01-02"}, None) == plain
    with_version = h(
        {
            "key_schema": "hio-dimensional-key/1",
            "dimension": "instrument",
            "durable_key": {"instrument_code": "x"},
            "version_identity": {"attributes_sha256": SHA_A},
        }
    )
    assert silver.sk("instrument", {"instrument_code": "x"}, {"attributes_sha256": SHA_A}) == with_version
    assert plain != with_version


def test_sk_sentinel_and_empty_version_identity() -> None:
    assert silver.sk("date", {"sentinel": "not_recorded"}) == h(
        {
            "key_schema": "hio-dimensional-key/1",
            "dimension": "date",
            "durable_key": {"sentinel": "not_recorded"},
        }
    )
    # An empty version identity is not None: it is written.
    assert silver.sk("x", {"a": "b"}, {}) != silver.sk("x", {"a": "b"})


def test_sk_refuses_non_text_values() -> None:
    with pytest.raises(TypeError):
        silver.sk("date", {"date": 1})  # type: ignore[dict-item]


def test_observation_id_integer_occurrence() -> None:
    expected = h(
        {
            "schema": "hio-observation/1",
            "series_id": "ZZZ.US.distribution",
            "coordinate": {"ex_date": "2024-03-01", "occurrence": 0},
        }
    )
    assert (
        silver.observation_id("ZZZ.US.distribution", {"ex_date": "2024-03-01", "occurrence": 0}) == expected
    )
    as_text = silver.observation_id("ZZZ.US.distribution", {"ex_date": "2024-03-01", "occurrence": "0"})
    assert as_text != expected
    with pytest.raises(TypeError):
        silver.observation_id("s", {"occurrence": True})


def test_observation_id_date_coordinate() -> None:
    expected = h(
        {
            "schema": "hio-observation/1",
            "series_id": "ZZZ.US.bar_day",
            "coordinate": {"trade_date": "2024-01-02"},
        }
    )
    assert silver.observation_id("ZZZ.US.bar_day", {"trade_date": "2024-01-02"}) == expected


def test_value_fingerprint_and_attributes() -> None:
    measures = {"open": "1.0", "close": "1.5000", "volume": "12345678901234567890"}
    assert silver.value_fingerprint(measures) == h(measures)
    assert silver.attributes_sha256({"name": "Fund, Inc.", "isin": ""}) == h(
        {"name": "Fund, Inc.", "isin": ""}
    )
    # Order of keys does not matter; text does.
    assert silver.value_fingerprint({"a": "1", "b": "2"}) == silver.value_fingerprint({"b": "2", "a": "1"})
    assert silver.value_fingerprint({"a": "1.0"}) != silver.value_fingerprint({"a": "1"})
    with pytest.raises(TypeError):
        silver.value_fingerprint({"a": Decimal("1")})  # type: ignore[dict-item]


def test_vintage_and_source_record_ids() -> None:
    assert silver.vintage_id(SHA_A, SHA_B, SHA_C) == h(
        {
            "schema": "hio-vintage/1",
            "observation_id": SHA_A,
            "value_fingerprint": SHA_B,
            "anchor_snapshot_id": SHA_C,
        }
    )
    assert silver.source_record_id(SHA_A, 0) == h({"file_sha256": SHA_A, "row_index": 0})
    assert silver.source_record_id(SHA_A, 12) == h({"file_sha256": SHA_A, "row_index": 12})
    for bad in (-1, True, "1", 1.0):
        with pytest.raises(ValueError, match="row_index"):
            silver.source_record_id(SHA_A, bad)  # type: ignore[arg-type]


def test_correction_and_application_ids() -> None:
    cid = silver.correction_id(SHA_A, "exclude", "2024-03-01")
    assert cid == h({"observation_spec_sha256": SHA_A, "action": "exclude", "ex_date": "2024-03-01"})
    assert silver.application_id(cid, SHA_B, SHA_C) == h(
        {"correction_id": cid, "snapshot_id": SHA_B, "target_source_record_id": SHA_C}
    )


# ---------------------------------------------------------------- exact text and source JSON


def test_exact_text() -> None:
    assert silver.exact_text(None) == ""
    assert silver.exact_text(Decimal("102.5000")) == "102.5000"
    assert silver.exact_text(Decimal("0.00")) == "0.00"
    assert silver.exact_text("keep me") == "keep me"
    assert silver.exact_text("") == ""
    assert silver.exact_text(Decimal("1E+3")) == "1000"
    assert silver.exact_text(Decimal("1E-7")) == "0.0000001"
    for bad in (1, 1.5, True, b"x", [], {}):
        with pytest.raises(TypeError):
            silver.exact_text(bad)
    with pytest.raises(ValueError, match="non-finite"):
        silver.exact_text(Decimal("NaN"))


def test_load_json_exact_keeps_numbers_as_written() -> None:
    parsed = silver.load_json_exact(
        b'{"close": 102.5000, "volume": 12345678901234567890123, "n": null, "s": "x"}'
    )
    assert parsed["close"] == Decimal("102.5000")
    assert silver.exact_text(parsed["close"]) == "102.5000"
    # A large integer volume is written with no exponent and nothing lost.
    assert silver.exact_text(parsed["volume"]) == "12345678901234567890123"
    assert silver.exact_text(parsed["n"]) == ""
    big = silver.load_json_exact(b'{"volume": 1.2345E+9}')
    assert silver.exact_text(big["volume"]) == "1234500000"


def test_record_sha256() -> None:
    record = silver.load_json_exact(b'{"b": 2, "a": 1.50, "c": null}')
    expected = hashlib.sha256(
        json.dumps({"b": Decimal("2"), "a": Decimal("1.50"), "c": None}, sort_keys=True, default=str).encode()
    ).hexdigest()
    assert silver.record_sha256(record) == expected
    assert expected == hashlib.sha256(b'{"a": "1.50", "b": "2", "c": null}').hexdigest()
    assert silver.record_sha256({"a": 1}) != silver.record_sha256({"a": "1"})


# ---------------------------------------------------------------- CSV and sorting


def test_csv_quoting_of_comma_and_quote_round_trip() -> None:
    rows = [
        row("dim_instrument", instrument_sk="s1", instrument_code="b", name='The "Big, Bold" Fund'),
        row("dim_instrument", instrument_sk="s2", instrument_code="a", name="Line\nbreak"),
    ]
    data = silver.table_bytes("dim_instrument", rows)
    text = data.decode()
    assert text.startswith("instrument_sk,instrument_code,name,issuer_code,vehicle_type,domicile\n")
    assert '"The ""Big, Bold"" Fund"' in text
    assert "\r" not in text
    parsed = silver.parse_table("dim_instrument", data)
    assert parsed == [rows[1], rows[0]]  # sorted by instrument_code
    assert silver.table_bytes("dim_instrument", parsed) == data


def test_round_trip_non_ascii_and_empty_cells() -> None:
    rows = [row("dim_currency", currency_sk="k", code=""), row("dim_currency", currency_sk="j", code="AUD")]
    data = silver.table_bytes("dim_currency", rows)
    assert data == b"currency_sk,code\nk,\nj,AUD\n"
    assert silver.parse_table("dim_currency", data) == rows
    accented = [row("dim_source", source_sk="x", source_id="café.source")]
    assert silver.parse_table("dim_source", silver.table_bytes("dim_source", accented)) == accented


def test_table_bytes_refuses_bad_rows() -> None:
    good = row("dim_currency", currency_sk="k", code="AUD")
    with pytest.raises(ValueError, match="columns"):
        silver.table_bytes("dim_currency", [{"currency_sk": "k"}])
    with pytest.raises(ValueError, match="columns"):
        silver.table_bytes("dim_currency", [{**good, "extra": "x"}])
    with pytest.raises(ValueError, match="not text"):
        silver.table_bytes("dim_currency", [{**good, "code": 1}])  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="not text"):
        silver.table_bytes("dim_currency", [{**good, "code": None}])  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="unknown silver table"):
        silver.table_bytes("dim_nothing", [])


def test_parse_table_refuses_wrong_header_and_ragged_rows() -> None:
    with pytest.raises(ValueError, match="header"):
        silver.parse_table("dim_currency", b"currency_sk,Code\nk,AUD\n")
    with pytest.raises(ValueError, match="header"):
        silver.parse_table("dim_currency", b"")
    with pytest.raises(ValueError, match="header"):
        silver.parse_table("dim_currency", b"code,currency_sk\n")
    with pytest.raises(ValueError, match="cells"):
        silver.parse_table("dim_currency", b"currency_sk,code\nk\n")
    with pytest.raises(ValueError, match="UTF-8"):
        silver.parse_table("dim_currency", b"currency_sk,code\n\xff,x\n")


def test_sort_dimension_rows_as_text() -> None:
    rows = [
        row("dim_date", date_sk="3", date="2024-01-10"),
        row("dim_date", date_sk="1", date=""),
        row("dim_date", date_sk="2", date="2024-01-02"),
    ]
    assert [r["date"] for r in silver.sort_rows("dim_date", rows)] == ["", "2024-01-02", "2024-01-10"]
    listings = [
        row("dim_listing", listing_sk="1", instrument_code="b", mic="XNYS", ticker="Z", valid_from=""),
        row(
            "dim_listing",
            listing_sk="2",
            instrument_code="a",
            mic="XNYS",
            ticker="Z",
            valid_from="2020-01-01",
        ),
        row("dim_listing", listing_sk="3", instrument_code="a", mic="XNYS", ticker="Z", valid_from=""),
        row(
            "dim_listing",
            listing_sk="4",
            instrument_code="a",
            mic="ARCX",
            ticker="Z",
            valid_from="2021-01-01",
        ),
    ]
    assert [r["listing_sk"] for r in silver.sort_rows("dim_listing", listings)] == ["4", "3", "2", "1"]
    source_listings = [
        row("dim_source_listing", source_listing_sk="2", source_symbol="B.US"),
        row("dim_source_listing", source_listing_sk="9", source_symbol="A.US"),
        row("dim_source_listing", source_listing_sk="1", source_symbol="A.US"),
    ]
    got = silver.sort_rows("dim_source_listing", source_listings)
    assert [(r["source_symbol"], r["source_listing_sk"]) for r in got] == [
        ("A.US", "1"),
        ("A.US", "9"),
        ("B.US", "2"),
    ]


def test_sort_result_does_not_depend_on_input_order() -> None:
    rows = [row("dim_currency", currency_sk=str(i), code="X") for i in range(5)]
    assert silver.sort_rows("dim_currency", rows) == silver.sort_rows("dim_currency", rows[::-1])


def test_sort_source_record_row_index_is_numeric() -> None:
    rows = [
        row("source_record", file_sha256=SHA_B, row_index="0"),
        row("source_record", file_sha256=SHA_A, row_index="10"),
        row("source_record", file_sha256=SHA_A, row_index="2"),
        row("source_record", file_sha256=SHA_A, row_index="1"),
    ]
    got = silver.sort_rows("source_record", rows)
    assert [(r["file_sha256"][0], r["row_index"]) for r in got] == [
        ("a", "1"),
        ("a", "2"),
        ("a", "10"),
        ("b", "0"),
    ]
    with pytest.raises(ValueError, match="row_index"):
        silver.sort_rows("source_record", [row("source_record", row_index="x")])


def test_sort_other_provenance_and_correction_tables() -> None:
    members = [
        row("snapshot_member", snapshot_id="s2", path="a"),
        row("snapshot_member", snapshot_id="s1", path="b"),
        row("snapshot_member", snapshot_id="s1", path="a"),
    ]
    got = silver.sort_rows("snapshot_member", members)
    assert [(r["snapshot_id"], r["path"]) for r in got] == [("s1", "a"), ("s1", "b"), ("s2", "a")]
    bridge = [
        row("bridge_vintage_support", vintage_id="v", source_record_id="r2", snapshot_id="a"),
        row("bridge_vintage_support", vintage_id="v", source_record_id="r1", snapshot_id="z"),
        row("bridge_vintage_support", vintage_id="v", source_record_id="r1", snapshot_id="b"),
    ]
    got = silver.sort_rows("bridge_vintage_support", bridge)
    assert [(r["source_record_id"], r["snapshot_id"]) for r in got] == [("r1", "b"), ("r1", "z"), ("r2", "a")]
    rules = [
        row("correction_rule", source_symbol="B.US", ex_date="2024-01-01"),
        row("correction_rule", source_symbol="A.US", ex_date="2024-05-01"),
        row("correction_rule", source_symbol="A.US", ex_date="2024-02-01"),
    ]
    got = silver.sort_rows("correction_rule", rules)
    assert [(r["source_symbol"], r["ex_date"]) for r in got] == [
        ("A.US", "2024-02-01"),
        ("A.US", "2024-05-01"),
        ("B.US", "2024-01-01"),
    ]
    apps = [
        row("fact_correction_application", correction_id="c2", snapshot_id="a"),
        row("fact_correction_application", correction_id="c1", snapshot_id="z"),
        row("fact_correction_application", correction_id="c1", snapshot_id="b"),
    ]
    got = silver.sort_rows("fact_correction_application", apps)
    assert [(r["correction_id"], r["snapshot_id"]) for r in got] == [("c1", "b"), ("c1", "z"), ("c2", "a")]
    presence = [
        row("fact_listing_presence", snapshot_id="s2", source_listing_sk="a"),
        row("fact_listing_presence", snapshot_id="s1", source_listing_sk="z"),
        row("fact_listing_presence", snapshot_id="s1", source_listing_sk="b"),
    ]
    got = silver.sort_rows("fact_listing_presence", presence)
    assert [(r["snapshot_id"], r["source_listing_sk"]) for r in got] == [
        ("s1", "b"),
        ("s1", "z"),
        ("s2", "a"),
    ]


def test_sort_snapshot_by_capture_order_text() -> None:
    # The contract says "as text" for snapshot; capture_order is not marked "as a number".
    rows = [
        row("snapshot", snapshot_id="x", capture_order="2"),
        row("snapshot", snapshot_id="y", capture_order="10"),
        row("snapshot", snapshot_id="z", capture_order="1"),
    ]
    assert [r["capture_order"] for r in silver.sort_rows("snapshot", rows)] == ["1", "10", "2"]


def test_sort_fact_rows_series_date_occurrence_then_capture_order() -> None:
    rows = [
        row(
            "fact_distribution_event",
            vintage_id="v1",
            series_id="B.US.distribution",
            anchor_snapshot_id="s1",
            ex_date="2024-01-01",
            occurrence="0",
        ),
        row(
            "fact_distribution_event",
            vintage_id="v2",
            series_id="A.US.distribution",
            anchor_snapshot_id="s1",
            ex_date="2024-02-01",
            occurrence="10",
        ),
        row(
            "fact_distribution_event",
            vintage_id="v3",
            series_id="A.US.distribution",
            anchor_snapshot_id="s1",
            ex_date="2024-02-01",
            occurrence="2",
        ),
        # Same observation, two vintages: capture order, not the snapshot id's text, decides.
        row(
            "fact_distribution_event",
            vintage_id="v4",
            series_id="A.US.distribution",
            anchor_snapshot_id="zzz-first",
            ex_date="2024-01-15",
            occurrence="0",
        ),
        row(
            "fact_distribution_event",
            vintage_id="v5",
            series_id="A.US.distribution",
            anchor_snapshot_id="aaa-second",
            ex_date="2024-01-15",
            occurrence="0",
        ),
    ]
    order = {"zzz-first": 1, "aaa-second": 2, "s1": 3}
    got = silver.sort_rows("fact_distribution_event", rows, order)
    assert [r["vintage_id"] for r in got] == ["v4", "v5", "v3", "v2", "v1"]
    data = silver.table_bytes("fact_distribution_event", rows, order)
    assert [r["vintage_id"] for r in silver.parse_table("fact_distribution_event", data)] == [
        "v4",
        "v5",
        "v3",
        "v2",
        "v1",
    ]


def test_sort_fact_tables_without_occurrence_use_the_coordinate_date() -> None:
    bars = [
        row(
            "fact_listing_bar_day",
            vintage_id="v1",
            series_id="A",
            anchor_snapshot_id="s2",
            trade_date="2024-01-02",
        ),
        row(
            "fact_listing_bar_day",
            vintage_id="v2",
            series_id="A",
            anchor_snapshot_id="s1",
            trade_date="2024-01-02",
        ),
        row(
            "fact_listing_bar_day",
            vintage_id="v3",
            series_id="A",
            anchor_snapshot_id="s1",
            trade_date="2024-01-01",
        ),
    ]
    got = silver.sort_rows("fact_listing_bar_day", bars, {"s1": 1, "s2": 2})
    assert [r["vintage_id"] for r in got] == ["v3", "v2", "v1"]
    splits = [
        row(
            "fact_split_event",
            vintage_id="v1",
            series_id="A",
            anchor_snapshot_id="s1",
            effective_date="2024-05-01",
            occurrence="1",
        ),
        row(
            "fact_split_event",
            vintage_id="v2",
            series_id="A",
            anchor_snapshot_id="s1",
            effective_date="2024-05-01",
            occurrence="0",
        ),
    ]
    got = silver.sort_rows("fact_split_event", splits, {"s1": 1})
    assert [r["vintage_id"] for r in got] == ["v2", "v1"]
    adjusted = [
        row(
            "fact_vendor_adjusted_close_day",
            vintage_id="v1",
            series_id="A",
            anchor_snapshot_id="s1",
            trade_date="2024-02-01",
        ),
        row(
            "fact_vendor_adjusted_close_day",
            vintage_id="v2",
            series_id="A",
            anchor_snapshot_id="s1",
            trade_date="2024-01-01",
        ),
    ]
    got = silver.sort_rows("fact_vendor_adjusted_close_day", adjusted, {"s1": 1})
    assert [r["vintage_id"] for r in got] == ["v2", "v1"]


def test_fact_sort_needs_capture_order() -> None:
    fact = row("fact_split_event", anchor_snapshot_id="s1", occurrence="0")
    with pytest.raises(ValueError, match="capture_order"):
        silver.sort_rows("fact_split_event", [fact])
    with pytest.raises(ValueError, match="no capture_order for snapshot"):
        silver.sort_rows("fact_split_event", [fact], {"other": 1})
    with pytest.raises(ValueError, match="occurrence"):
        silver.sort_rows("fact_split_event", [{**fact, "occurrence": "x"}], {"s1": 1})


# ---------------------------------------------------------------- selections


def test_selection_policy_and_id() -> None:
    policy = silver.selection_policy_bytes("compat-v1", {"B.US": SHA_B, "A.US": SHA_A}, ["z", "m", "a"])
    expected = json.dumps(
        {
            "schema": "hio-selection/1",
            "name": "compat-v1",
            "members": {"A.US": SHA_A, "B.US": SHA_B},
            "corrections": ["a", "m", "z"],
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    assert policy == expected
    assert silver.selection_id(policy) == hashlib.sha256(expected).hexdigest()
    assert silver.selection_policy_bytes("n", {}, iter([])) == (
        b'{"corrections":[],"members":{},"name":"n","schema":"hio-selection/1"}'
    )


def test_selection_columns_and_sort() -> None:
    assert silver.SELECTION_COLUMNS == (
        "fact_table",
        "series_id",
        "observation_id",
        "vintage_id",
        "source_record_id",
        "row_index",
        "disposition",
        "reason",
    )

    def sel(
        fact_table: str, series_id: str, row_index: str, disposition: str = "selected", reason: str = ""
    ) -> dict[str, str]:
        return {
            "fact_table": fact_table,
            "series_id": series_id,
            "observation_id": "o",
            "vintage_id": "v",
            "source_record_id": "r",
            "row_index": row_index,
            "disposition": disposition,
            "reason": reason,
        }

    rows = [
        sel("fact_vendor_adjusted_close_day", "A.US.adjusted_close_day", "1"),
        sel("fact_listing_bar_day", "B.US.bar_day", "0"),
        sel("fact_listing_bar_day", "A.US.bar_day", "10"),
        sel("fact_listing_bar_day", "A.US.bar_day", "2"),
        sel("fact_distribution_event", "A.US.distribution", "0", "excluded", SHA_A),
    ]
    data = silver.selection_bytes(rows)
    assert data.decode().splitlines()[0] == (
        "fact_table,series_id,observation_id,vintage_id,source_record_id,row_index,disposition,reason"
    )
    got = silver.parse_selection(data)
    assert [(r["fact_table"], r["series_id"], r["row_index"]) for r in got] == [
        ("fact_distribution_event", "A.US.distribution", "0"),
        ("fact_listing_bar_day", "A.US.bar_day", "2"),
        ("fact_listing_bar_day", "A.US.bar_day", "10"),
        ("fact_listing_bar_day", "B.US.bar_day", "0"),
        ("fact_vendor_adjusted_close_day", "A.US.adjusted_close_day", "1"),
    ]
    assert got[0]["reason"] == SHA_A
    assert silver.selection_bytes(got) == data
    with pytest.raises(ValueError, match="columns"):
        silver.selection_bytes([{"fact_table": "x"}])
    with pytest.raises(ValueError, match="header"):
        silver.parse_selection(b"fact_table\n")


# ---------------------------------------------------------------- release


def _tables() -> dict[str, bytes]:
    tables = {name: silver.table_bytes(name, [], {}) for name in silver.TABLES}
    tables["dim_source"] = silver.table_bytes(
        "dim_source",
        [
            row(
                "dim_source",
                source_sk=silver.sk("source", {"source_id": "some.source"}),
                source_id="some.source",
            ),
        ],
    )
    tables["dim_instrument"] = silver.table_bytes(
        "dim_instrument",
        [row("dim_instrument", instrument_sk="k1", instrument_code="example-fund", name='Example, "Fund"')],
    )
    return tables


def _selections() -> dict[str, tuple[bytes, bytes]]:
    policy = silver.selection_policy_bytes("compat-v1", {"ZZZ.US": SHA_A}, [])
    data = silver.selection_bytes(
        [
            {
                "fact_table": "fact_listing_bar_day",
                "series_id": "ZZZ.US.bar_day",
                "observation_id": "o",
                "vintage_id": "v",
                "source_record_id": "r",
                "row_index": "0",
                "disposition": "selected",
                "reason": "",
            }
        ]
    )
    return {silver.selection_id(policy): (policy, data)}


def _core(tables: dict[str, bytes], selections: dict[str, tuple[bytes, bytes]]) -> dict:
    return silver.manifest_core(
        release_spec={"name": "funds", "version": "0.1.0", "sha256": SHA_A},
        register_sha256=SHA_B,
        observation_specs=[
            {"source_symbol": "ZZZ.US", "sha256": SHA_C},
            {"source_symbol": "AAA.US", "sha256": SHA_A},
        ],
        snapshots=[{"name": "s1", "manifest_sha256": SHA_A}, {"name": "s0", "manifest_sha256": SHA_B}],
        code_commit="0" * 40,
        tables=tables,
        selections=selections,
    )


@pytest.fixture
def built(tmp_path: Path) -> tuple[Path, dict, dict[str, bytes], dict[str, tuple[bytes, bytes]]]:
    tables, selections = _tables(), _selections()
    core = _core(tables, selections)
    release_dir, existed = silver.write_release(tmp_path / "silver", core, tables, selections)
    assert existed is False
    return release_dir, core, tables, selections


def _materialise(parent: Path, core: dict, files: dict[str, bytes]) -> Path:
    """Write a release directory exactly as given, with no checks: for building bad releases."""
    target = parent / silver.release_id(core)
    for relative, data in {**files, "manifest.json": silver.manifest_bytes(core)}.items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return target


def _files(tables: dict[str, bytes], selections: dict[str, tuple[bytes, bytes]]) -> dict[str, bytes]:
    files = {f"tables/{name}.csv": data for name, data in tables.items()}
    for sid, (policy, data) in selections.items():
        files[f"selections/{sid}.json"] = policy
        files[f"selections/{sid}.csv"] = data
    return files


def test_manifest_core_shape_and_hashes() -> None:
    tables, selections = _tables(), _selections()
    core = _core(tables, selections)
    assert set(core) == {
        "schema",
        "release_spec",
        "register_sha256",
        "observation_specs",
        "snapshots",
        "code_commit",
        "tables",
        "selections",
    }
    assert core["schema"] == "hio.silver/2"
    assert core["release_spec"] == {"name": "funds", "version": "0.1.0", "sha256": SHA_A}
    assert [e["source_symbol"] for e in core["observation_specs"]] == ["AAA.US", "ZZZ.US"]
    assert [e["name"] for e in core["snapshots"]] == ["s1", "s0"]  # capture order kept
    names = [e["name"] for e in core["tables"]]
    assert names == sorted(silver.TABLES)
    entry = next(e for e in core["tables"] if e["name"] == "dim_instrument")
    assert entry["file_sha256"] == hashlib.sha256(tables["dim_instrument"]).hexdigest()
    assert (
        entry["header_sha256"]
        == hashlib.sha256(b"instrument_sk,instrument_code,name,issuer_code,vehicle_type,domicile").hexdigest()
    )
    assert entry["rows"] == 1
    assert next(e for e in core["tables"] if e["name"] == "dim_date")["rows"] == 0
    (sid, (policy, data)) = next(iter(selections.items()))
    assert core["selections"] == [
        {
            "selection_id": sid,
            "name": "compat-v1",
            "policy_sha256": hashlib.sha256(policy).hexdigest(),
            "file_sha256": hashlib.sha256(data).hexdigest(),
            "rows": 1,
        }
    ]
    assert silver.release_id(core) == h(core)


def test_manifest_core_refusals() -> None:
    tables, selections = _tables(), _selections()
    with pytest.raises(ValueError, match="missing tables"):
        _core({k: v for k, v in tables.items() if k != "dim_date"}, selections)
    with pytest.raises(ValueError, match="unknown tables"):
        _core({**tables, "dim_extra": b""}, selections)
    with pytest.raises(ValueError, match="header"):
        _core({**tables, "dim_date": b"date_sk,date\n"}, selections)
    (sid, pair) = next(iter(selections.items()))
    with pytest.raises(ValueError, match="selection_id"):
        _core(tables, {SHA_C: pair})
    assert sid != SHA_C
    with pytest.raises(ValueError, match="sha256"):
        silver.manifest_core(
            release_spec={"name": "f", "version": "1", "sha256": "short"},
            register_sha256=SHA_B,
            observation_specs=[],
            snapshots=[],
            code_commit="c",
            tables=tables,
            selections={},
        )


def test_manifest_bytes_rendering_and_determinism() -> None:
    tables, selections = _tables(), _selections()
    core = _core(tables, selections)
    data = silver.manifest_bytes(core)
    assert data.endswith(b"}\n")
    assert data == silver.manifest_bytes(_core(tables, selections))
    assert data.startswith(b'{\n "core": {\n  "code_commit"')
    parsed = json.loads(data)
    assert parsed == {"core": core, "release_id": silver.release_id(core)}
    assert data == (json.dumps(parsed, indent=1, sort_keys=True) + "\n").encode()


def test_write_verify_and_write_again(built, tmp_path: Path) -> None:
    release_dir, core, tables, selections = built
    root = tmp_path / "silver"
    assert release_dir == root / "v2" / silver.release_id(core)
    assert sorted(p.name for p in (root / "v2").iterdir()) == [silver.release_id(core)]  # no scratch left
    assert silver.verify_release(release_dir) == core
    assert (release_dir / "manifest.json").read_bytes() == silver.manifest_bytes(core)
    for name, data in tables.items():
        assert (release_dir / "tables" / f"{name}.csv").read_bytes() == data
    for sid, (policy, data) in selections.items():
        assert (release_dir / "selections" / f"{sid}.json").read_bytes() == policy
        assert (release_dir / "selections" / f"{sid}.csv").read_bytes() == data
    again, existed = silver.write_release(root, core, tables, selections)
    assert (again, existed) == (release_dir, True)
    assert silver.verify_release(release_dir) == core


def test_same_inputs_give_the_same_bytes_in_two_roots(tmp_path: Path) -> None:
    tables, selections = _tables(), _selections()
    core = _core(tables, selections)
    one, _ = silver.write_release(tmp_path / "one", core, tables, selections)
    two, _ = silver.write_release(tmp_path / "two", core, tables, selections)
    assert one.name == two.name
    for path in sorted(one.rglob("*")):
        if path.is_file():
            assert path.read_bytes() == (two / path.relative_to(one)).read_bytes()


def test_write_refuses_existing_release_with_different_bytes(built, tmp_path: Path) -> None:
    release_dir, core, tables, selections = built
    (release_dir / "tables" / "dim_source.csv").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="different bytes"):
        silver.write_release(tmp_path / "silver", core, tables, selections)
    # The tampered file is left as it was: nothing is overwritten.
    assert (release_dir / "tables" / "dim_source.csv").read_bytes() == b"tampered"
    assert sorted(p.name for p in (tmp_path / "silver" / "v2").iterdir()) == [release_dir.name]


def test_write_refuses_extra_file_in_existing_release(built, tmp_path: Path) -> None:
    release_dir, core, tables, selections = built
    (release_dir / "tables" / "extra.csv").write_bytes(b"x")
    with pytest.raises(ValueError, match="different bytes"):
        silver.write_release(tmp_path / "silver", core, tables, selections)


def test_write_refuses_files_that_disagree_with_the_core(tmp_path: Path) -> None:
    tables, selections = _tables(), _selections()
    core = _core(tables, selections)
    other = {**tables, "dim_source": silver.table_bytes("dim_source", [])}
    with pytest.raises(ValueError, match="file sha256 differs"):
        silver.write_release(tmp_path / "silver", core, other, selections)
    assert not (tmp_path / "silver").exists()
    with pytest.raises(ValueError, match="missing file"):
        silver.write_release(
            tmp_path / "silver", core, {k: v for k, v in tables.items() if k != "snapshot"}, selections
        )


def test_modes(built) -> None:
    release_dir, *_ = built
    assert stat.S_IMODE(release_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(release_dir.parent.stat().st_mode) == 0o700
    for path in release_dir.rglob("*"):
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == (0o700 if path.is_dir() else 0o600), path


def test_verify_refuses_tampered_table(built) -> None:
    release_dir, *_ = built
    path = release_dir / "tables" / "dim_instrument.csv"
    path.write_bytes(path.read_bytes() + b"more\n")
    with pytest.raises(ValueError, match=r"table dim_instrument: file sha256 differs"):
        silver.verify_release(release_dir)


def test_verify_refuses_missing_table(built) -> None:
    release_dir, *_ = built
    (release_dir / "tables" / "dim_date.csv").unlink()
    with pytest.raises(ValueError, match=r"missing file: tables/dim_date.csv"):
        silver.verify_release(release_dir)


def test_verify_refuses_missing_selection_and_manifest(built) -> None:
    release_dir, core, *_ = built
    sid = core["selections"][0]["selection_id"]
    (release_dir / "selections" / f"{sid}.csv").unlink()
    with pytest.raises(ValueError, match=r"missing file: selections/"):
        silver.verify_release(release_dir)
    (release_dir / "manifest.json").unlink()
    with pytest.raises(ValueError, match=r"missing file: manifest.json"):
        silver.verify_release(release_dir)


def test_verify_refuses_extra_file_and_directory(built) -> None:
    release_dir, *_ = built
    (release_dir / "tables" / "dim_extra.csv").write_bytes(b"x")
    with pytest.raises(ValueError, match=r"unexpected file: tables/dim_extra.csv"):
        silver.verify_release(release_dir)
    (release_dir / "tables" / "dim_extra.csv").unlink()
    (release_dir / "notes.txt").write_bytes(b"x")
    with pytest.raises(ValueError, match=r"unexpected file: notes.txt"):
        silver.verify_release(release_dir)
    (release_dir / "notes.txt").unlink()
    (release_dir / "other").mkdir()
    with pytest.raises(ValueError, match=r"unexpected directory: other"):
        silver.verify_release(release_dir)


def test_verify_refuses_wrong_directory_name(built) -> None:
    release_dir, *_ = built
    renamed = release_dir.parent / "not-the-release-id"
    shutil.move(release_dir, renamed)
    with pytest.raises(ValueError, match="directory name"):
        silver.verify_release(renamed)


def test_verify_refuses_core_that_does_not_match_its_release_id(built) -> None:
    release_dir, *_ = built
    manifest = json.loads((release_dir / "manifest.json").read_text())
    manifest["core"]["code_commit"] = "1" * 40
    (release_dir / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="does not match the core"):
        silver.verify_release(release_dir)


def test_verify_refuses_wrong_row_count(built, tmp_path: Path) -> None:
    _, core, tables, selections = built
    bad = json.loads(json.dumps(core))
    next(e for e in bad["tables"] if e["name"] == "dim_instrument")["rows"] = 2
    target = _materialise(tmp_path / "bad-rows", bad, _files(tables, selections))
    with pytest.raises(ValueError, match=r"table dim_instrument: 1 rows, the manifest says 2"):
        silver.verify_release(target)


def test_verify_refuses_wrong_selection_row_count(built, tmp_path: Path) -> None:
    _, core, tables, selections = built
    bad = json.loads(json.dumps(core))
    bad["selections"][0]["rows"] = 7
    target = _materialise(tmp_path / "bad-sel-rows", bad, _files(tables, selections))
    with pytest.raises(ValueError, match=r"selection .*: 1 rows, the manifest says 7"):
        silver.verify_release(target)


def test_verify_refuses_wrong_header(built, tmp_path: Path) -> None:
    _, core, tables, selections = built
    wrong = b"currency_sk,Code\n"
    files = _files(tables, selections)
    files["tables/dim_currency.csv"] = wrong
    bad = json.loads(json.dumps(core))
    next(e for e in bad["tables"] if e["name"] == "dim_currency")["file_sha256"] = hashlib.sha256(
        wrong
    ).hexdigest()
    target = _materialise(tmp_path / "bad-header", bad, files)
    with pytest.raises(ValueError, match=r"table dim_currency: header is not currency_sk,code"):
        silver.verify_release(target)


def test_verify_refuses_wrong_header_sha_in_manifest(built, tmp_path: Path) -> None:
    _, core, tables, selections = built
    bad = json.loads(json.dumps(core))
    next(e for e in bad["tables"] if e["name"] == "dim_currency")["header_sha256"] = SHA_C
    target = _materialise(tmp_path / "bad-header-sha", bad, _files(tables, selections))
    with pytest.raises(ValueError, match=r"table dim_currency: header sha256 differs"):
        silver.verify_release(target)


def test_verify_refuses_selection_id_mismatch(built, tmp_path: Path) -> None:
    _, core, tables, selections = built
    fake = "f" * 64
    (sid, (policy, data)) = next(iter(selections.items()))
    bad = json.loads(json.dumps(core))
    bad["selections"][0]["selection_id"] = fake
    files = _files(tables, {})
    files[f"selections/{fake}.json"] = policy
    files[f"selections/{fake}.csv"] = data
    target = _materialise(tmp_path / "bad-sel-id", bad, files)
    with pytest.raises(ValueError, match=rf"selection {fake}: policy bytes hash to {sid}"):
        silver.verify_release(target)


def test_verify_refuses_selection_name_and_policy_hash_mismatch(built, tmp_path: Path) -> None:
    _, core, tables, selections = built
    files = _files(tables, selections)
    bad = json.loads(json.dumps(core))
    bad["selections"][0]["policy_sha256"] = SHA_C
    with pytest.raises(ValueError, match="policy sha256 differs"):
        silver.verify_release(_materialise(tmp_path / "a", bad, files))
    bad = json.loads(json.dumps(core))
    bad["selections"][0]["name"] = "other"
    with pytest.raises(ValueError, match="policy name"):
        silver.verify_release(_materialise(tmp_path / "b", bad, files))
    bad = json.loads(json.dumps(core))
    bad["selections"][0]["file_sha256"] = SHA_C
    with pytest.raises(ValueError, match="file sha256 differs"):
        silver.verify_release(_materialise(tmp_path / "c", bad, files))


def test_verify_refuses_malformed_manifest(built) -> None:
    release_dir, *_ = built
    (release_dir / "manifest.json").write_bytes(b"not json")
    with pytest.raises(ValueError, match="not JSON"):
        silver.verify_release(release_dir)
    (release_dir / "manifest.json").write_bytes(b'{"core": {}, "release_id": "x"}')
    with pytest.raises(ValueError, match="exactly the keys"):
        silver.verify_release(release_dir)
    with pytest.raises(ValueError, match="not a release directory"):
        silver.verify_release(release_dir / "nowhere")


def test_verify_refuses_manifest_that_is_not_canonical_text(built) -> None:
    release_dir, core, *_ = built
    compact = json.dumps({"core": core, "release_id": silver.release_id(core)}, sort_keys=True)
    (release_dir / "manifest.json").write_text(compact)
    with pytest.raises(ValueError, match="canonical rendering"):
        silver.verify_release(release_dir)


def test_release_without_selections(tmp_path: Path) -> None:
    tables = _tables()
    core = _core(tables, {})
    release_dir, existed = silver.write_release(tmp_path / "silver", core, tables, {})
    assert existed is False
    assert silver.verify_release(release_dir)["selections"] == []
