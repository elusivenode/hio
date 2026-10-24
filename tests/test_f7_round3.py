"""Regression tests for VERIFY-2026-10-24-s1a-1-7 (OD-0032): F7 round 3.

Codex's counterexample: three receipts for one key, 3.60, then 3.61, then 3.60 (a true revert),
with the third receipt's processing outcome forged as "redundant". Verification accepted it,
because an older equal value existed, although ingest's rule requires the latest capture-order
value to match. The forged store served 3.61 and the honest store 3.60 under the same evidence
digest. Verification must now re-derive each outcome with exactly the capture-order rules ingest
uses (latest value, evidence strength, reverts) and refuse any mismatch.
"""

import json
from datetime import date
from decimal import Decimal

import pytest

from hio.contracts.canonical import canonical_json
from hio.marketdata.capture import SyntheticSource, capture
from hio.marketdata.series import CaptureMode
from hio.marketdata.vintages import IncompleteProcessing, VintageStore
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import SERIES, AllowAllGate, receipt_text, utc

RATE, SRC = "synthetic.rate", "synthetic.daily_source"
D1 = date(2026, 1, 12)
CLOCK = lambda: utc(2026, 1, 1)  # noqa: E731
HEADER = "series_id,valid_time,value,published_at"
RECEIPTS = [  # (captured at, value, published_at)
    (utc(2026, 1, 12, 1), "3.60", "2026-01-12T00:00:00Z"),
    (utc(2026, 1, 13, 1), "3.61", "2026-01-13T00:00:00Z"),
    (utc(2026, 1, 14, 1), "3.60", "2026-01-14T00:00:00Z"),
]
T = Q = utc(2026, 1, 15)


def open_store(root):
    return VintageStore(LocalObjectStore(root), SERIES, clock=CLOCK)


def capture_receipt(vs, tmp, at, value, stamp):
    path = tmp / f"{SRC}.csv"
    path.write_text(receipt_text(value, [f"{RATE},2026-01-12,{value},{stamp}"], HEADER))
    receipt, is_new = capture(SyntheticSource(SRC, path), vs.store, AllowAllGate(), at)
    assert is_new
    return receipt


def honest(root):
    vs = open_store(root)
    for at, value, stamp in RECEIPTS:
        vs.ingest(capture_receipt(vs, root, at, value, stamp), CaptureMode.SCHEDULED)
    return vs


def forged(root):
    """The first two honestly; the third's outcome written by hand as a false no-op."""
    vs = open_store(root)
    for at, value, stamp in RECEIPTS[:2]:
        vs.ingest(capture_receipt(vs, root, at, value, stamp), CaptureMode.SCHEDULED)
    at, value, stamp = RECEIPTS[2]
    third = capture_receipt(vs, root, at, value, stamp)
    key = f"catalogue/processed/{SRC}/{at:%Y%m%d-%H%M%S%f}-{third.receipt_id}.json"
    outcome = {
        "receipt_id": third.receipt_id,
        "source_id": SRC,
        "captured_at": at,
        "capture_mode": "scheduled",
        "rows": [
            {
                "series_id": RATE,
                "valid_time": "2026-01-12",
                "value": "3.6",
                "knowable_at": utc(2026, 1, 14),
                "knowable_basis": "publisher_timestamp",
                "disposition": "redundant",
                "vintage_seq": None,
            }
        ],
    }
    vs.store.put(key, canonical_json(outcome))
    return vs


def test_codex_round7_a_revert_forged_as_redundant_is_refused_by_query_and_resolution(tmp_path):
    root = tmp_path / "f"
    forged(root)
    for vs in (forged_store := open_store(root), open_store(root)):  # including after reopening
        with pytest.raises(IncompleteProcessing):
            vs.as_known_by_market(RATE, T, Q)
        with pytest.raises(IncompleteProcessing):
            vs.as_captured_by_hio(RATE, T)
        with pytest.raises(IncompleteProcessing):
            vs.conflicts(RATE, Q)
        with pytest.raises(IncompleteProcessing):
            vs.resolve_conflict(RATE, "0" * 64, "reject_all", None, "", "owner", "x", Q)
    assert forged_store is not None


def test_codex_round7_honest_capture_order_ingestion_returns_the_revert_reproducibly(tmp_path):
    a = honest(tmp_path / "a")
    view = a.as_known_by_market(RATE, T, Q)
    assert {k: v.value for k, v in view.values.items()} == {D1: Decimal("3.60")}
    assert view.values[D1].vintage_seq == 3 and view.values[D1].captured_at == utc(2026, 1, 14, 1)
    assert open_store(tmp_path / "a").as_known_by_market(RATE, T, Q) == view  # reopened: identical
    b = honest(tmp_path / "b")  # an independent replay of the same evidence
    assert b.as_known_by_market(RATE, T, Q) == view
    assert b.evidence_digest(RATE, Q) == view.evidence_digest


def test_an_honest_no_op_relabelled_as_a_vintage_is_refused(tmp_path):
    """The mirror case: an honest redundant row (the same value and evidence again) claimed as a
    new vintage, with the vintage record written to match the claim."""
    root = tmp_path / "m"
    vs = open_store(root)
    stamp = "2026-01-12T00:00:00Z"
    vs.ingest(capture_receipt(vs, root, utc(2026, 1, 12, 1), "3.60", stamp), CaptureMode.SCHEDULED)
    path = root / f"{SRC}.csv"
    path.write_text(receipt_text("again", [f"{RATE},2026-01-12,3.60,{stamp}"], HEADER))  # new bytes
    second, _ = capture(SyntheticSource(SRC, path), vs.store, AllowAllGate(), utc(2026, 1, 12, 2))
    vs.ingest(second, CaptureMode.SCHEDULED)
    (key,) = [k for k in vs.store.list("catalogue/processed/") if second.receipt_id in k]
    record = json.loads(vs.store.get(key))
    assert record["rows"][0]["disposition"] == "redundant"
    record["rows"][0]["disposition"], record["rows"][0]["vintage_seq"] = "vintage", 2
    vintage = json.loads(vs.store.get(f"catalogue/vintages/{RATE}/2026-01-12/000001.json"))
    vintage.update(vintage_seq=2, receipt_id=second.receipt_id, captured_at="2026-01-12T02:00:00.000000Z")
    target = root / key
    target.chmod(0o644)
    target.write_bytes(canonical_json(record))
    vs.store.put(f"catalogue/vintages/{RATE}/2026-01-12/000002.json", canonical_json(vintage))
    with pytest.raises(IncompleteProcessing):
        open_store(root).as_known_by_market(RATE, T, Q)
