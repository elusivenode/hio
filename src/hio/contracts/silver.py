"""Silver version 2 contract: tables, keys, CSV, selections and releases.

Built to `docs/decisions/silver-v2-contract.md` (proposed; OD-0233). Section numbers in the
docstrings are that document's. Everything here is pure and deterministic: no clock, no
environment, no randomness in any output byte. This module imports no other `hio` package
except `hio.contracts.canonical`.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

from hio.contracts.canonical import canonical_json, sha256_hex

SCHEMA = "hio.silver/2"
KEY_SCHEMA = "hio-dimensional-key/1"
OBSERVATION_SCHEMA = "hio-observation/1"
VINTAGE_SCHEMA = "hio-vintage/1"
SELECTION_SCHEMA = "hio-selection/1"

FILE_MODE = 0o600
DIR_MODE = 0o700

_SHA256 = re.compile(r"[0-9a-f]{64}")
_UNSIGNED = re.compile(r"[0-9]+")

# --------------------------------------------------------------------------------------
# Tables (§4)
# --------------------------------------------------------------------------------------

COMMON_FACT_COLUMNS: tuple[str, ...] = (
    "vintage_id",
    "observation_id",
    "series_id",
    "series_sk",
    "source_sk",
    "audit_sk",
    "origin_source_record_id",
    "anchor_snapshot_id",
    "first_captured_at",
)

DIMENSION_TABLES: tuple[str, ...] = (
    "dim_date",
    "dim_currency",
    "dim_source",
    "dim_instrument",
    "dim_listing",
    "dim_source_listing",
    "dim_series",
    "dim_audit",
)

# The four measurement facts: the tables that carry the nine common columns and a fingerprint.
FACT_TABLES: tuple[str, ...] = (
    "fact_listing_bar_day",
    "fact_vendor_adjusted_close_day",
    "fact_distribution_event",
    "fact_split_event",
)

_FACT_FURTHER: dict[str, tuple[str, ...]] = {
    "fact_listing_bar_day": (
        "listing_sk",
        "instrument_sk",
        "trade_date_sk",
        "trade_date",
        "quote_currency_sk",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ),
    "fact_vendor_adjusted_close_day": (
        "listing_sk",
        "instrument_sk",
        "trade_date_sk",
        "trade_date",
        "quote_currency_sk",
        "adjusted_close",
    ),
    "fact_distribution_event": (
        "instrument_sk",
        "currency_sk",
        "ex_date_sk",
        "declaration_date_sk",
        "record_date_sk",
        "payment_date_sk",
        "ex_date",
        "occurrence",
        "declaration_date",
        "record_date",
        "payment_date",
        "amount_unadjusted",
        "amount_split_adjusted",
        "currency",
        "period_label",
        "franking",
    ),
    "fact_split_event": (
        "instrument_sk",
        "effective_date_sk",
        "effective_date",
        "occurrence",
        "ratio",
        "new_units",
        "old_units",
    ),
}

# Fact table -> the measure column names of its fingerprint (§4 "Measures").
MEASURES: dict[str, tuple[str, ...]] = {
    "fact_listing_bar_day": ("open", "high", "low", "close", "volume"),
    "fact_vendor_adjusted_close_day": ("adjusted_close",),
    "fact_distribution_event": (
        "declaration_date",
        "record_date",
        "payment_date",
        "amount_unadjusted",
        "amount_split_adjusted",
        "currency",
        "period_label",
        "franking",
    ),
    "fact_split_event": ("ratio",),
}

# Fact table -> (coordinate date column, occurrence column or None). A table with no
# occurrence column sorts as occurrence 0.
_FACT_SORT_COLUMNS: dict[str, tuple[str, str | None]] = {
    "fact_listing_bar_day": ("trade_date", None),
    "fact_vendor_adjusted_close_day": ("trade_date", None),
    "fact_distribution_event": ("ex_date", "occurrence"),
    "fact_split_event": ("effective_date", "occurrence"),
}

TABLES: dict[str, tuple[str, ...]] = {
    # dimensions
    "dim_date": ("date_sk", "date", "year", "month", "day", "iso_weekday"),
    "dim_currency": ("currency_sk", "code"),
    "dim_source": ("source_sk", "source_id"),
    "dim_instrument": (
        "instrument_sk",
        "instrument_code",
        "name",
        "issuer_code",
        "vehicle_type",
        "domicile",
    ),
    "dim_listing": (
        "listing_sk",
        "instrument_code",
        "instrument_sk",
        "mic",
        "ticker",
        "valid_from",
        "quote_currency",
    ),
    "dim_source_listing": (
        "source_listing_sk",
        "source_id",
        "source_symbol",
        "vendor_code",
        "vendor_exchange",
        "name",
        "country",
        "exchange",
        "currency",
        "isin",
        "type",
    ),
    "dim_series": ("series_sk", "series_id", "source_id", "source_symbol", "quantity"),
    "dim_audit": (
        "audit_sk",
        "schema",
        "code_commit",
        "release_spec_sha256",
        "register_sha256",
        "observation_specs_sha256",
    ),
    # provenance
    "snapshot": (
        "snapshot_id",
        "name",
        "source_id",
        "capture_order",
        "first_retrieved_at",
        "last_retrieved_at",
    ),
    "snapshot_member": ("snapshot_id", "path", "file_sha256", "kind", "source_symbol", "retrieved_at"),
    "source_record": ("source_record_id", "file_sha256", "row_index", "record_sha256"),
    "source_identity_mapping": ("source_id", "source_symbol", "instrument_code", "listing_sk"),
    "bridge_vintage_support": ("vintage_id", "source_record_id", "snapshot_id"),
    # facts: the nine common columns, then the table's further columns
    **{name: (*COMMON_FACT_COLUMNS, *further) for name, further in _FACT_FURTHER.items()},
    # membership and corrections
    "fact_listing_presence": (
        "source_listing_sk",
        "snapshot_id",
        "instrument_sk",
        "listing_sk",
        "currency_sk",
    ),
    "correction_rule": (
        "correction_id",
        "observation_spec_sha256",
        "source_symbol",
        "action",
        "ex_date",
        "reason",
        "evidence",
    ),
    "fact_correction_application": (
        "application_id",
        "correction_id",
        "snapshot_id",
        "target_source_record_id",
        "target_vintage_id",
        "disposition",
    ),
}

# §4 sort keys of the non-fact tables: (column, is_numeric) pairs in significance order. A
# column is compared as text unless it is marked numeric. Fact tables are sorted separately.
_SORT_ORDER: dict[str, tuple[tuple[str, bool], ...]] = {
    "dim_date": (("date", False),),
    "dim_currency": (("code", False),),
    "dim_source": (("source_id", False),),
    "dim_instrument": (("instrument_code", False),),
    "dim_listing": (("instrument_code", False), ("mic", False), ("ticker", False), ("valid_from", False)),
    "dim_source_listing": (("source_symbol", False), ("source_listing_sk", False)),
    "dim_series": (("series_id", False),),
    "dim_audit": (("audit_sk", False),),
    "snapshot": (("capture_order", True),),
    "snapshot_member": (("snapshot_id", False), ("path", False)),
    "source_record": (("file_sha256", False), ("row_index", True)),
    "source_identity_mapping": (("source_symbol", False),),
    "bridge_vintage_support": (("vintage_id", False), ("source_record_id", False), ("snapshot_id", False)),
    "fact_listing_presence": (("snapshot_id", False), ("source_listing_sk", False)),
    "correction_rule": (("source_symbol", False), ("ex_date", False)),
    "fact_correction_application": (("correction_id", False), ("snapshot_id", False)),
}

# --------------------------------------------------------------------------------------
# Encoding (§1)
# --------------------------------------------------------------------------------------


def exact_text(value: object) -> str:
    """§1: a source field as the text of its cell.

    `None` is the empty cell; a `Decimal` is `format(value, "f")` (never an exponent, nothing
    rounded); a `str` is unchanged. Anything else (float, int, bool, ...) is refused with
    `TypeError`: source numbers must be read with `load_json_exact`. A non-finite `Decimal` is a
    `ValueError`.
    """
    if value is None:
        return ""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"non-finite decimal: {value}")
        return format(value, "f")
    if isinstance(value, str):
        return value
    raise TypeError(f"not an exact source value: {type(value).__name__}")


def load_json_exact(data: bytes) -> Any:
    """§1: parse source JSON with every number a `Decimal` (`parse_float` and `parse_int`)."""
    return json.loads(data, parse_float=Decimal, parse_int=Decimal)


def record_sha256(record: Any) -> str:
    """§1: sha256 of `json.dumps(record, sort_keys=True, default=str)` as UTF-8.

    `record` is the source record as parsed by `load_json_exact`.
    """
    return sha256_hex(json.dumps(record, sort_keys=True, default=str).encode("utf-8"))


# --------------------------------------------------------------------------------------
# Keys (§2)
# --------------------------------------------------------------------------------------


def _text_mapping(name: str, mapping: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(mapping, Mapping):
        raise TypeError(f"{name} must be a mapping")
    out: dict[str, str] = {}
    for key, value in mapping.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError(f"{name} must map str to str; got {key!r}: {value!r}")
        out[key] = value
    return out


def sk(
    dimension: str,
    durable_key: Mapping[str, str],
    version_identity: Mapping[str, str] | None = None,
) -> str:
    """§2: the surrogate key of a dimension row.

    sha256 of the canonical JSON of `{"key_schema": "hio-dimensional-key/1", "dimension": ...,
    "durable_key": ...}`; `version_identity` is part of the JSON only when it is not `None`.
    """
    body: dict[str, Any] = {
        "key_schema": KEY_SCHEMA,
        "dimension": dimension,
        "durable_key": _text_mapping("durable_key", durable_key),
    }
    if version_identity is not None:
        body["version_identity"] = _text_mapping("version_identity", version_identity)
    return sha256_hex(canonical_json(body))


def observation_id(series_id: str, coordinate: Mapping[str, str | int]) -> str:
    """§2: sha256 of the canonical JSON of `{"schema": "hio-observation/1", "series_id", "coordinate"}`.

    A coordinate value is a `str`, or an `int` for `occurrence`.
    """
    coord: dict[str, str | int] = {}
    for key, value in coordinate.items():
        if isinstance(value, bool) or not isinstance(value, str | int):
            raise TypeError(f"coordinate values must be str or int; got {key!r}: {value!r}")
        coord[key] = value
    return sha256_hex(
        canonical_json({"schema": OBSERVATION_SCHEMA, "series_id": series_id, "coordinate": coord})
    )


def value_fingerprint(measures: dict[str, str]) -> str:
    """§2: sha256 of the canonical JSON of the row's measure cells, by column name."""
    return sha256_hex(canonical_json(_text_mapping("measures", measures)))


def vintage_id(observation_id: str, value_fingerprint: str, anchor_snapshot_id: str) -> str:
    """§2: sha256 of the canonical JSON of `{"schema": "hio-vintage/1", "observation_id",
    "value_fingerprint", "anchor_snapshot_id"}`."""
    return sha256_hex(
        canonical_json(
            {
                "schema": VINTAGE_SCHEMA,
                "observation_id": observation_id,
                "value_fingerprint": value_fingerprint,
                "anchor_snapshot_id": anchor_snapshot_id,
            }
        )
    )


def source_record_id(file_sha256: str, row_index: int) -> str:
    """§2: sha256 of the canonical JSON of `{"file_sha256", "row_index"}`; `row_index` is the
    0-based position of the record in its file, an integer (a `bool` or a negative is refused)."""
    if isinstance(row_index, bool) or not isinstance(row_index, int) or row_index < 0:
        raise ValueError(f"row_index must be a non-negative integer: {row_index!r}")
    return sha256_hex(canonical_json({"file_sha256": file_sha256, "row_index": row_index}))


def attributes_sha256(attributes: dict[str, str]) -> str:
    """§2: sha256 of the canonical JSON of a row's other attribute cells, by column name."""
    return sha256_hex(canonical_json(_text_mapping("attributes", attributes)))


def correction_id(observation_spec_sha256: str, action: str, ex_date: str) -> str:
    """§4: sha256 of the canonical JSON of `{"observation_spec_sha256", "action", "ex_date"}`."""
    return sha256_hex(
        canonical_json(
            {"observation_spec_sha256": observation_spec_sha256, "action": action, "ex_date": ex_date}
        )
    )


def application_id(correction_id: str, snapshot_id: str, target_source_record_id: str) -> str:
    """§4: sha256 of the canonical JSON of `{"correction_id", "snapshot_id",
    "target_source_record_id"}`."""
    return sha256_hex(
        canonical_json(
            {
                "correction_id": correction_id,
                "snapshot_id": snapshot_id,
                "target_source_record_id": target_source_record_id,
            }
        )
    )


# --------------------------------------------------------------------------------------
# CSV tables (§1, §4)
# --------------------------------------------------------------------------------------


def _columns(table: str) -> tuple[str, ...]:
    try:
        return TABLES[table]
    except KeyError:
        raise ValueError(f"unknown silver table: {table!r}") from None


def _unsigned(table: str, column: str, cell: str) -> int:
    if not _UNSIGNED.fullmatch(cell):
        raise ValueError(f"{table}.{column} must be an unsigned integer to sort: {cell!r}")
    return int(cell)


def sort_rows(
    table: str,
    rows: Iterable[Mapping[str, str]],
    capture_order: Mapping[str, int] | None = None,
) -> list[dict[str, str]]:
    """§4: the rows in the table's sort order, as new dicts.

    Columns are compared as text, except `snapshot.capture_order`, `source_record.row_index` and
    a fact's `occurrence` (numbers). Fact rows sort by `series_id`, the coordinate date,
    `occurrence` (0 for a table without one), then the `capture_order` of the row's
    `anchor_snapshot_id`; `capture_order` (snapshot id -> position) is required for fact tables
    and a missing snapshot is refused.
    Ties are broken by the whole row in column order, so the result never depends on input order.
    """
    columns = _columns(table)
    listed = [dict(row) for row in rows]
    if table in _FACT_SORT_COLUMNS:
        if capture_order is None:
            raise ValueError(f"{table}: sorting a fact table needs capture_order")
        date_column, occurrence_column = _FACT_SORT_COLUMNS[table]

        def fact_key(row: dict[str, str]) -> tuple[Any, ...]:
            anchor = row["anchor_snapshot_id"]
            if anchor not in capture_order:
                raise ValueError(f"{table}: no capture_order for snapshot {anchor!r}")
            occurrence = _unsigned(table, "occurrence", row[occurrence_column]) if occurrence_column else 0
            return (
                row["series_id"],
                row[date_column],
                occurrence,
                capture_order[anchor],
                tuple(row[c] for c in columns),
            )

        return sorted(listed, key=fact_key)
    order = _SORT_ORDER[table]

    def key(row: dict[str, str]) -> tuple[Any, ...]:
        primary = tuple(_unsigned(table, c, row[c]) if numeric else row[c] for c, numeric in order)
        return (*primary, tuple(row[c] for c in columns))

    return sorted(listed, key=key)


def header_line(columns: Sequence[str]) -> bytes:
    """The header row of a table as bytes, with its line end."""
    return (",".join(columns) + "\n").encode("utf-8")


def _render(label: str, columns: Sequence[str], rows: Iterable[Mapping[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(columns)
    wanted = set(columns)
    for number, row in enumerate(rows):
        if set(row) != wanted:
            raise ValueError(f"{label} row {number}: columns {sorted(row)} differ from {sorted(wanted)}")
        for column in columns:
            if not isinstance(row[column], str):
                raise ValueError(f"{label} row {number}: {column} is not text: {row[column]!r}")
        writer.writerow([row[column] for column in columns])
    return buffer.getvalue().encode("utf-8")


def _parse(label: str, columns: Sequence[str], data: bytes) -> list[dict[str, str]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label}: not UTF-8: {exc}") from exc
    try:
        parsed = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except csv.Error as exc:
        raise ValueError(f"{label}: malformed CSV: {exc}") from exc
    if not parsed or parsed[0] != list(columns):
        raise ValueError(f"{label}: header is not {','.join(columns)}")
    out: list[dict[str, str]] = []
    for number, cells in enumerate(parsed[1:]):
        if len(cells) != len(columns):
            raise ValueError(f"{label} row {number}: {len(cells)} cells, expected {len(columns)}")
        out.append(dict(zip(columns, cells, strict=True)))
    return out


def table_bytes(
    table: str,
    rows: Iterable[Mapping[str, str]],
    capture_order: Mapping[str, int] | None = None,
) -> bytes:
    """§1 and §4: the table's CSV file.

    Every row must have exactly the table's columns and only `str` cells (else `ValueError`).
    Rows are sorted by `sort_rows` (fact tables need `capture_order`) and written as UTF-8 with
    `lineterminator="\\n"`, minimal quoting and the header first.
    """
    columns = _columns(table)
    listed = list(rows)
    _render(table, columns, listed)  # validates before sorting, so a bad row is named as such
    return _render(table, columns, sort_rows(table, listed, capture_order))


def parse_table(table: str, data: bytes) -> list[dict[str, str]]:
    """The rows of a table's CSV bytes, in file order; refuses a wrong header or ragged row.

    `table_bytes(table, parse_table(table, data), ...)` reproduces `data` when `data` was
    written by `table_bytes`.
    """
    return _parse(table, _columns(table), data)


# --------------------------------------------------------------------------------------
# Selections (§5)
# --------------------------------------------------------------------------------------

SELECTION_COLUMNS: tuple[str, ...] = (
    "fact_table",
    "series_id",
    "observation_id",
    "vintage_id",
    "source_record_id",
    "row_index",
    "disposition",
    "reason",
)


def selection_policy_bytes(name: str, members: Mapping[str, str], corrections: Iterable[str]) -> bytes:
    """§5: the canonical JSON of `{"schema": "hio-selection/1", "name", "members":
    {source_symbol: snapshot_id}, "corrections": [sorted correction ids]}`."""
    return canonical_json(
        {
            "schema": SELECTION_SCHEMA,
            "name": name,
            "members": _text_mapping("members", members),
            "corrections": sorted(corrections),
        }
    )


def selection_id(policy_bytes: bytes) -> str:
    """§5: the sha256 of the selection policy's bytes."""
    return sha256_hex(policy_bytes)


def selection_bytes(rows: Iterable[Mapping[str, str]]) -> bytes:
    """§5: the selection CSV (`SELECTION_COLUMNS`), sorted by `fact_table`, `series_id`, then
    `row_index` as a number (ties by the whole row)."""
    listed = [dict(row) for row in rows]
    _render("selection", SELECTION_COLUMNS, listed)

    def key(row: dict[str, str]) -> tuple[Any, ...]:
        return (
            row["fact_table"],
            row["series_id"],
            _unsigned("selection", "row_index", row["row_index"]),
            tuple(row[c] for c in SELECTION_COLUMNS),
        )

    return _render("selection", SELECTION_COLUMNS, sorted(listed, key=key))


def parse_selection(data: bytes) -> list[dict[str, str]]:
    """The rows of a selection CSV in file order; refuses a wrong header or ragged row."""
    return _parse("selection", SELECTION_COLUMNS, data)


# --------------------------------------------------------------------------------------
# Release manifest (§6)
# --------------------------------------------------------------------------------------

_CORE_KEYS = frozenset(
    {
        "schema",
        "release_spec",
        "register_sha256",
        "observation_specs",
        "snapshots",
        "code_commit",
        "tables",
        "selections",
    }
)
_TABLE_ENTRY_KEYS = frozenset({"name", "header_sha256", "file_sha256", "rows"})
_SELECTION_ENTRY_KEYS = frozenset({"selection_id", "name", "policy_sha256", "file_sha256", "rows"})


def _need_sha(label: str, value: object) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{label} is not a lower-case sha256: {value!r}")
    return value


def _need_keys(label: str, value: object, keys: Iterable[str]) -> Mapping[str, Any]:
    wanted = set(keys)
    if not isinstance(value, Mapping) or set(value) != wanted:
        raise ValueError(f"{label} must have exactly the keys {sorted(wanted)}")
    return value


def _selection_policy(label: str, policy_bytes: bytes) -> dict[str, Any]:
    try:
        policy = json.loads(policy_bytes)
    except ValueError as exc:
        raise ValueError(f"{label}: policy is not JSON: {exc}") from exc
    _need_keys(f"{label} policy", policy, ("schema", "name", "members", "corrections"))
    if policy["schema"] != SELECTION_SCHEMA:
        raise ValueError(f"{label}: policy schema is not {SELECTION_SCHEMA}")
    if not isinstance(policy["name"], str):
        raise ValueError(f"{label}: policy name is not text")
    return policy


def _table_entries(tables: Mapping[str, bytes]) -> list[dict[str, Any]]:
    unknown = sorted(set(tables) - set(TABLES))
    missing = sorted(set(TABLES) - set(tables))
    if unknown:
        raise ValueError(f"unknown tables: {unknown}")
    if missing:
        raise ValueError(f"missing tables: {missing}")
    entries = []
    for name in sorted(tables):
        data = tables[name]
        rows = parse_table(name, data)  # refuses a wrong header
        entries.append(
            {
                "name": name,
                "header_sha256": sha256_hex(header_line(TABLES[name])[:-1]),
                "file_sha256": sha256_hex(data),
                "rows": len(rows),
            }
        )
    return entries


def _selection_entries(selections: Mapping[str, tuple[bytes, bytes]]) -> list[dict[str, Any]]:
    entries = []
    for key in sorted(selections):
        policy_bytes, csv_bytes = selections[key]
        sid = selection_id(policy_bytes)
        if key != sid:
            raise ValueError(f"selection key {key} is not the selection_id {sid} of its policy bytes")
        policy = _selection_policy(f"selection {sid}", policy_bytes)
        entries.append(
            {
                "selection_id": sid,
                "name": policy["name"],
                "policy_sha256": sha256_hex(policy_bytes),
                "file_sha256": sha256_hex(csv_bytes),
                "rows": len(parse_selection(csv_bytes)),
            }
        )
    return entries


def manifest_core(
    *,
    release_spec: Mapping[str, str],
    register_sha256: str,
    observation_specs: Iterable[Mapping[str, str]],
    snapshots: Sequence[Mapping[str, str]],
    code_commit: str,
    tables: Mapping[str, bytes],
    selections: Mapping[str, tuple[bytes, bytes]],
) -> dict[str, Any]:
    """§6: the manifest core from explicit arguments.

    `release_spec` is `{name, version, sha256}`; `observation_specs` are `{source_symbol,
    sha256}` (sorted here by `source_symbol`); `snapshots` are `{name, manifest_sha256}` and
    keep the capture order given. `tables` maps every table name in `TABLES` (no more, no
    fewer) to its file bytes; `header_sha256`, `file_sha256` and `rows` are computed from them.
    `selections` maps each `selection_id` to `(policy_bytes, csv_bytes)`; the id is checked
    against the policy bytes and `name`, `policy_sha256`, `file_sha256` and `rows` are computed.
    Hash arguments must be lower-case sha256 hex. The core holds no time, path or run id.
    """
    spec = _need_keys("release_spec", release_spec, ("name", "version", "sha256"))
    _need_sha("release_spec.sha256", spec["sha256"])
    _need_sha("register_sha256", register_sha256)
    specs = []
    for item in observation_specs:
        entry = _need_keys("observation_specs entry", item, ("source_symbol", "sha256"))
        _need_sha(f"observation spec {entry['source_symbol']} sha256", entry["sha256"])
        specs.append({"source_symbol": entry["source_symbol"], "sha256": entry["sha256"]})
    snaps = []
    for item in snapshots:
        entry = _need_keys("snapshots entry", item, ("name", "manifest_sha256"))
        _need_sha(f"snapshot {entry['name']} manifest_sha256", entry["manifest_sha256"])
        snaps.append({"name": entry["name"], "manifest_sha256": entry["manifest_sha256"]})
    core: dict[str, Any] = {
        "schema": SCHEMA,
        "release_spec": {"name": spec["name"], "version": spec["version"], "sha256": spec["sha256"]},
        "register_sha256": register_sha256,
        "observation_specs": sorted(specs, key=lambda e: e["source_symbol"]),
        "snapshots": snaps,
        "code_commit": code_commit,
        "tables": _table_entries(tables),
        "selections": _selection_entries(selections),
    }
    _validate_core(core)
    return core


def _validate_core(core: object) -> dict[str, Any]:
    """Refuse (`ValueError`) a core that is not of the §6 shape."""
    _need_keys("core", core, _CORE_KEYS)
    assert isinstance(core, Mapping)
    if core["schema"] != SCHEMA:
        raise ValueError(f"core schema is not {SCHEMA}: {core['schema']!r}")
    spec = _need_keys("core.release_spec", core["release_spec"], ("name", "version", "sha256"))
    _need_sha("core.release_spec.sha256", spec["sha256"])
    _need_sha("core.register_sha256", core["register_sha256"])
    if not isinstance(core["code_commit"], str):
        raise ValueError("core.code_commit is not text")
    for entry in core["observation_specs"]:
        _need_keys("core.observation_specs entry", entry, ("source_symbol", "sha256"))
        _need_sha("core.observation_specs sha256", entry["sha256"])
    symbols = [e["source_symbol"] for e in core["observation_specs"]]
    if symbols != sorted(symbols):
        raise ValueError("core.observation_specs is not sorted by source_symbol")
    for entry in core["snapshots"]:
        _need_keys("core.snapshots entry", entry, ("name", "manifest_sha256"))
        _need_sha("core.snapshots manifest_sha256", entry["manifest_sha256"])
    names = []
    for entry in core["tables"]:
        _need_keys("core.tables entry", entry, _TABLE_ENTRY_KEYS)
        _need_sha(f"core.tables {entry['name']} header_sha256", entry["header_sha256"])
        _need_sha(f"core.tables {entry['name']} file_sha256", entry["file_sha256"])
        rows = entry["rows"]
        if isinstance(rows, bool) or not isinstance(rows, int) or rows < 0:
            raise ValueError(f"core.tables {entry['name']} rows is not a count: {rows!r}")
        names.append(entry["name"])
    if sorted(names) != sorted(TABLES) or names != sorted(names):
        raise ValueError("core.tables must list every table exactly once, sorted by name")
    ids = []
    for entry in core["selections"]:
        _need_keys("core.selections entry", entry, _SELECTION_ENTRY_KEYS)
        for field in ("selection_id", "policy_sha256", "file_sha256"):
            _need_sha(f"core.selections {field}", entry[field])
        rows = entry["rows"]
        if isinstance(rows, bool) or not isinstance(rows, int) or rows < 0:
            raise ValueError(f"core.selections {entry['selection_id']} rows is not a count: {rows!r}")
        ids.append(entry["selection_id"])
    if ids != sorted(set(ids)):
        raise ValueError("core.selections must be sorted by selection_id with no repeats")
    return dict(core)


def release_id(core: Mapping[str, Any]) -> str:
    """§6: the sha256 of the canonical JSON of the manifest core."""
    return sha256_hex(canonical_json(core))


def manifest_bytes(core: Mapping[str, Any]) -> bytes:
    """§6: `manifest.json`: `{"core": core, "release_id": release_id(core)}` written with
    indent 1, sorted keys and a trailing newline."""
    body = {"core": core, "release_id": release_id(core)}
    return (json.dumps(body, indent=1, sort_keys=True) + "\n").encode("utf-8")


# --------------------------------------------------------------------------------------
# Release directory (§6)
# --------------------------------------------------------------------------------------


def _release_files(
    core: Mapping[str, Any],
    tables: Mapping[str, bytes],
    selections: Mapping[str, tuple[bytes, bytes]],
) -> dict[str, bytes]:
    files = {"manifest.json": manifest_bytes(core)}
    for name, data in tables.items():
        files[f"tables/{name}.csv"] = data
    for sid, (policy_bytes, csv_bytes) in selections.items():
        files[f"selections/{sid}.json"] = policy_bytes
        files[f"selections/{sid}.csv"] = csv_bytes
    return files


def _check_content(core: Mapping[str, Any], files: Mapping[str, bytes]) -> None:
    """Refuse (`ValueError`, naming the first problem) a release whose files do not match its core.

    `files` maps each path relative to the release directory to its bytes.
    """
    expected = {"manifest.json"}
    expected |= {f"tables/{e['name']}.csv" for e in core["tables"]}
    for entry in core["selections"]:
        expected |= {f"selections/{entry['selection_id']}.json", f"selections/{entry['selection_id']}.csv"}
    for path in sorted(expected - set(files)):
        raise ValueError(f"missing file: {path}")
    for path in sorted(set(files) - expected):
        raise ValueError(f"unexpected file: {path}")
    for entry in core["tables"]:
        name = entry["name"]
        data = files[f"tables/{name}.csv"]
        if sha256_hex(data) != entry["file_sha256"]:
            raise ValueError(f"table {name}: file sha256 differs from the manifest")
        if not data.startswith(header_line(TABLES[name])):
            raise ValueError(f"table {name}: header is not {','.join(TABLES[name])}")
        if sha256_hex(header_line(TABLES[name])[:-1]) != entry["header_sha256"]:
            raise ValueError(f"table {name}: header sha256 differs from the manifest")
        rows = len(parse_table(name, data))
        if rows != entry["rows"]:
            raise ValueError(f"table {name}: {rows} rows, the manifest says {entry['rows']}")
    for entry in core["selections"]:
        sid = entry["selection_id"]
        policy_bytes = files[f"selections/{sid}.json"]
        csv_bytes = files[f"selections/{sid}.csv"]
        if selection_id(policy_bytes) != sid:
            raise ValueError(f"selection {sid}: policy bytes hash to {selection_id(policy_bytes)}")
        if sha256_hex(policy_bytes) != entry["policy_sha256"]:
            raise ValueError(f"selection {sid}: policy sha256 differs from the manifest")
        policy = _selection_policy(f"selection {sid}", policy_bytes)
        if policy["name"] != entry["name"]:
            raise ValueError(f"selection {sid}: policy name {policy['name']!r} differs from the manifest")
        if sha256_hex(csv_bytes) != entry["file_sha256"]:
            raise ValueError(f"selection {sid}: file sha256 differs from the manifest")
        rows = len(parse_selection(csv_bytes))
        if rows != entry["rows"]:
            raise ValueError(f"selection {sid}: {rows} rows, the manifest says {entry['rows']}")


def _read_release(release_dir: Path) -> dict[str, bytes]:
    if release_dir.is_symlink() or not release_dir.is_dir():
        raise ValueError(f"not a release directory: {release_dir}")
    files: dict[str, bytes] = {}
    for path in sorted(release_dir.rglob("*")):
        relative = path.relative_to(release_dir).as_posix()
        if path.is_symlink():
            raise ValueError(f"unexpected symbolic link: {relative}")
        if path.is_dir():
            if relative not in {"tables", "selections"}:
                raise ValueError(f"unexpected directory: {relative}")
            continue
        if not path.is_file():
            raise ValueError(f"unexpected entry: {relative}")
        files[relative] = path.read_bytes()
    return files


def verify_release(release_dir: Path) -> dict[str, Any]:
    """§6 and §7: check a release directory and return its manifest core.

    Checks, refusing with `ValueError` naming the first problem: `manifest.json` is of the
    §6 shape; the recomputed `release_id` equals the stored one and the directory's name;
    exactly the manifest's tables and selections are present (no missing and no extra file);
    each file's sha256; each table's header and row count; each selection's `selection_id`
    against its policy bytes, and its row count.
    """
    files = _read_release(release_dir)
    if "manifest.json" not in files:
        raise ValueError("missing file: manifest.json")
    try:
        manifest = json.loads(files["manifest.json"])
    except ValueError as exc:
        raise ValueError(f"manifest.json is not JSON: {exc}") from exc
    _need_keys("manifest", manifest, ("core", "release_id"))
    core = _validate_core(manifest["core"])
    recomputed = release_id(core)
    if manifest["release_id"] != recomputed:
        raise ValueError(f"release_id {manifest['release_id']!r} does not match the core ({recomputed})")
    if release_dir.name != recomputed:
        raise ValueError(f"directory name {release_dir.name!r} is not the release_id {recomputed}")
    if files["manifest.json"] != manifest_bytes(core):
        raise ValueError("manifest.json is not in the canonical rendering")
    _check_content(core, files)
    return core


def _same_release(target: Path, files: Mapping[str, bytes]) -> bool:
    try:
        existing = _read_release(target)
    except ValueError:
        return False
    return existing == dict(files)


def write_release(
    silver_root: Path,
    core: Mapping[str, Any],
    tables: Mapping[str, bytes],
    selections: Mapping[str, tuple[bytes, bytes]],
) -> tuple[Path, bool]:
    """§6: write `<silver_root>/v2/<release_id>/` and return `(directory, already_there)`.

    `selections` maps `selection_id` to `(policy_bytes, csv_bytes)`. The files must agree with
    `core` (checked as `verify_release` would, before anything is written). The release is built
    in a temporary sibling directory and renamed into place; files are mode 0600 and
    directories 0700. If the directory already exists with identical bytes the result is
    `(directory, True)` and nothing is changed; if it exists with different bytes the write is
    refused with `ValueError`. Nothing is overwritten. This does not check where `silver_root`
    is: callers do.
    """
    core = _validate_core(core)
    for name, data in tables.items():
        if not isinstance(data, bytes):
            raise ValueError(f"table {name}: bytes expected")
    files = _release_files(core, tables, selections)
    _check_content(core, files)
    rid = release_id(core)
    version_dir = silver_root / "v2"
    target = version_dir / rid
    if target.exists() or target.is_symlink():
        if _same_release(target, files):
            return target, True
        raise ValueError(f"release {rid} already exists with different bytes: {target}")
    silver_root.mkdir(mode=DIR_MODE, parents=True, exist_ok=True)
    version_dir.mkdir(mode=DIR_MODE, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix=".tmp-", dir=version_dir))
    try:
        os.chmod(scratch, DIR_MODE)
        for sub in ("tables", "selections"):
            (scratch / sub).mkdir(mode=DIR_MODE)
            os.chmod(scratch / sub, DIR_MODE)
        for relative, data in files.items():
            descriptor = os.open(scratch / relative, os.O_WRONLY | os.O_CREAT | os.O_EXCL, FILE_MODE)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
            os.chmod(scratch / relative, FILE_MODE)
        try:
            scratch.rename(target)
        except OSError:
            # Another writer got there first (or the name is taken): accept only identical bytes.
            if target.exists() and _same_release(target, files):
                return target, True
            raise ValueError(f"release {rid} already exists with different bytes: {target}") from None
    finally:
        if scratch.exists():
            shutil.rmtree(scratch)
    return target, False
