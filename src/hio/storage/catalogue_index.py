"""The catalogue index: a DuckDB database derived from the object store's records
(architecture §2; HIO-ADR-0009). Disposable and rebuildable: the records are the system of
record, and rebuilding from the same records gives the same index."""

from __future__ import annotations

import json

import duckdb

from hio.storage.objectstore import LocalObjectStore

SCHEMA = """
CREATE TABLE releases (content_sha256 VARCHAR PRIMARY KEY, dataset_id VARCHAR, spec_ref VARCHAR,
    knowledge_mode VARCHAR, knowledge_cutoff VARCHAR, weakest_knowable_basis VARCHAR, periods INTEGER);
CREATE TABLE status_events (content_sha256 VARCHAR, seq INTEGER, status VARCHAR, consumer_class VARCHAR,
    actor VARCHAR, event_at VARCHAR, PRIMARY KEY (content_sha256, seq));
CREATE TABLE captures (source_id VARCHAR, receipt_id VARCHAR, captured_at VARCHAR);
CREATE TABLE vintages (series_id VARCHAR, valid_time DATE, vintage_seq INTEGER, value VARCHAR,
    knowable_at VARCHAR, knowable_basis VARCHAR, captured_at VARCHAR, quality_status VARCHAR,
    PRIMARY KEY (series_id, valid_time, vintage_seq));
CREATE VIEW effective_status AS
    SELECT content_sha256, arg_max(status, seq) AS status, max(seq) AS seq FROM status_events GROUP BY 1;
"""


def rebuild_index(store: LocalObjectStore, path: str = ":memory:") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(path)
    con.execute(SCHEMA)
    for key in store.list("releases/"):
        if key.endswith("/manifest.json"):
            c = json.loads(store.get(key))
            con.execute(
                "INSERT INTO releases VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    key.split("/")[2],
                    c["dataset_id"],
                    c["spec_ref"],
                    c["knowledge_mode"],
                    c["knowledge_cutoff"],
                    c["weakest_knowable_basis"],
                    c["quality_summary"]["periods"],
                ],
            )
    for key in store.list("catalogue/status/"):
        e = json.loads(store.get(key))
        con.execute(
            "INSERT INTO status_events VALUES (?, ?, ?, ?, ?, ?)",
            [e["content_sha256"], e["seq"], e["status"], e["consumer_class"], e["actor"], e["at"]],
        )
    for key in store.list("catalogue/captures/"):
        r = json.loads(store.get(key))
        con.execute(
            "INSERT INTO captures VALUES (?, ?, ?)", [r["source_id"], r["receipt_id"], r["captured_at"]]
        )
    for key in store.list("catalogue/vintages/"):
        v = json.loads(store.get(key))
        con.execute(
            "INSERT INTO vintages VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                v["series_id"],
                v["valid_time"],
                v["vintage_seq"],
                v["value"],
                v["knowable_at"],
                v["knowable_basis"],
                v["captured_at"],
                v["quality_status"],
            ],
        )
    return con


def dump(con: duckdb.DuckDBPyConnection) -> dict[str, list[tuple]]:
    """Every table's rows in a canonical order, for comparing two rebuilds."""
    out = {}
    for table in ("releases", "status_events", "captures", "vintages"):
        out[table] = con.execute(f"SELECT * FROM {table} ORDER BY ALL").fetchall()
    return out
