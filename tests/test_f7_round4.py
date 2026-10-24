"""Regression tests for VERIFY-2026-10-24-s1a-1-8 (OD-0033): F7 round 4, quarantine and the
completeness trust boundary.

Completeness skipped any receipt with a quarantine marker before verifying its bytes or why it
was quarantined. (1) After a genuine quarantine, deleting the raw receipt still served the same
result and evidence digest. (2) A forged marker on a valid, unprocessed receipt served a result
instead of refusing. Every captured receipt's bytes are now verified first, and its disposition
(quarantine included) is re-derived with ingest's own rules; any marker, outcome or vintage the
evidence does not warrant refuses.
"""

import json

import pytest

from hio.contracts.canonical import canonical_json
from hio.contracts.layout import receipt_key
from hio.marketdata.capture import SyntheticSource, capture
from hio.marketdata.series import CaptureMode
from hio.marketdata.vintages import IncompleteProcessing, ReceiptIntegrityError, VintageStore
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import SERIES, AllowAllGate, receipt_text, utc

RATE, SRC = "synthetic.rate", "synthetic.daily_source"
CLOCK = lambda: utc(2026, 1, 1)  # noqa: E731
REFUSED = (IncompleteProcessing, ReceiptIntegrityError)


def open_store(root):
    return VintageStore(LocalObjectStore(root), SERIES, clock=CLOCK)


def capture_bytes(vs, root, text, at):
    path = root / f"{SRC}.csv"
    path.write_text(text)
    receipt, is_new = capture(SyntheticSource(SRC, path), vs.store, AllowAllGate(), at)
    assert is_new
    return receipt


def quarantine_key(receipt):
    return f"catalogue/quarantine/receipts/{receipt.receipt_id}.json"


def every_path_refuses(root, t, q, exc=REFUSED):
    """Query, diagnostics, resolution and the evidence pin all refuse, on the store as given and
    after reopening it, and a refusal writes nothing."""
    for vs in (open_store(root), open_store(root)):
        before = vs.store.snapshot()
        with pytest.raises(exc):
            vs.as_known_by_market(RATE, t, q)
        with pytest.raises(exc):
            vs.as_captured_by_hio(RATE, q)
        with pytest.raises(exc):
            vs.conflicts(RATE, q)
        with pytest.raises(exc):
            vs.evidence_digest(RATE, q)
        with pytest.raises(exc):
            vs.resolve_conflict(RATE, "0" * 64, "reject_all", None, "", "owner", "x", q)
        assert vs.store.snapshot() == before


T = Q = utc(2026, 1, 15)
VALID = receipt_text(
    "valid", [f"{RATE},2026-01-12,3.60,2026-01-12T00:00:00Z"], "series_id,valid_time,value,published_at"
)


def genuinely_quarantined(root):
    vs = open_store(root)
    receipt = capture_bytes(vs, root, "not a receipt\n", utc(2026, 1, 13, 12))
    assert vs.ingest(receipt, CaptureMode.SCHEDULED).receipt_quarantined
    return vs, receipt


# --- Codex counterexample 1: raw bytes missing after a genuine quarantine -------------------------


def test_codex_round8_missing_raw_bytes_after_a_genuine_quarantine_refuse(tmp_path):
    root = tmp_path / "s"
    vs, receipt = genuinely_quarantined(root)
    assert vs.as_known_by_market(RATE, T, Q).values == {}  # a genuine quarantine is still served
    path = root / receipt_key(SRC, receipt.captured_at, receipt.receipt_id)
    path.chmod(0o644)
    path.unlink()
    every_path_refuses(root, T, Q, ReceiptIntegrityError)


def test_altered_raw_bytes_of_a_quarantined_receipt_refuse(tmp_path):
    root = tmp_path / "s"
    _, receipt = genuinely_quarantined(root)
    path = root / receipt_key(SRC, receipt.captured_at, receipt.receipt_id)
    path.chmod(0o644)
    path.write_bytes(b"also not a receipt\n")
    every_path_refuses(root, T, Q, ReceiptIntegrityError)


# --- Codex counterexample 2: a forged marker on a valid, unprocessed receipt ----------------------


def test_codex_round8_a_forged_quarantine_marker_on_a_valid_receipt_refuses(tmp_path):
    root = tmp_path / "s"
    vs = open_store(root)
    receipt = capture_bytes(vs, root, VALID, utc(2026, 1, 12, 1))  # valid, left unprocessed
    vs.store.put(
        quarantine_key(receipt), canonical_json({"receipt_id": receipt.receipt_id, "reason": "malformed"})
    )
    every_path_refuses(root, utc(2026, 1, 13), utc(2026, 1, 13), IncompleteProcessing)
    with pytest.raises(IncompleteProcessing):  # and nothing later can be ingested past it
        open_store(root).ingest(
            capture_bytes(vs, root, VALID.replace("3.60", "3.61"), utc(2026, 1, 13, 1)), CaptureMode.SCHEDULED
        )


# --- related bypasses ---------------------------------------------------------------------------


def test_a_quarantine_marker_with_the_wrong_reason_refuses(tmp_path):
    root = tmp_path / "s"
    _, receipt = genuinely_quarantined(root)
    path = root / quarantine_key(receipt)
    path.chmod(0o644)
    path.write_bytes(canonical_json({"receipt_id": receipt.receipt_id, "reason": "a different reason"}))
    every_path_refuses(root, T, Q, IncompleteProcessing)


def test_a_marker_beside_a_processing_outcome_refuses(tmp_path):
    """A valid receipt, honestly processed, then also marked quarantined: contradictory state."""
    root = tmp_path / "s"
    vs = open_store(root)
    receipt = capture_bytes(vs, root, VALID, utc(2026, 1, 12, 1))
    vs.ingest(receipt, CaptureMode.SCHEDULED)
    vs.store.put(quarantine_key(receipt), canonical_json({"receipt_id": receipt.receipt_id, "reason": "x"}))
    every_path_refuses(root, T, Q, IncompleteProcessing)


def test_a_deleted_marker_for_a_genuinely_malformed_receipt_refuses(tmp_path):
    root = tmp_path / "s"
    _, receipt = genuinely_quarantined(root)
    path = root / quarantine_key(receipt)
    path.chmod(0o644)
    path.unlink()
    every_path_refuses(root, T, Q, IncompleteProcessing)


def test_a_forged_outcome_for_a_malformed_receipt_refuses(tmp_path):
    """Instead of quarantine, a processing outcome claiming the malformed receipt was processed."""
    root = tmp_path / "s"
    vs = open_store(root)
    receipt = capture_bytes(vs, root, "not a receipt\n", utc(2026, 1, 13, 12))
    key = f"catalogue/processed/{SRC}/{receipt.captured_at:%Y%m%d-%H%M%S%f}-{receipt.receipt_id}.json"
    outcome = {
        "receipt_id": receipt.receipt_id,
        "source_id": SRC,
        "captured_at": receipt.captured_at,
        "capture_mode": "scheduled",
        "rows": [],
    }
    vs.store.put(key, canonical_json(outcome))
    every_path_refuses(root, T, Q, IncompleteProcessing)


# --- valid quarantine behaviour is preserved, and pins are stable ---------------------------------


def test_genuine_quarantine_is_served_with_stable_pins_across_reopen_and_replay(tmp_path):
    a, _ = genuinely_quarantined(tmp_path / "a")
    a.ingest(
        capture_bytes(
            a,
            tmp_path / "a",
            VALID.replace("2026-01-12T00:00:00Z", "2026-01-14T00:00:00Z"),
            utc(2026, 1, 14, 1),
        ),
        CaptureMode.SCHEDULED,
    )
    view = a.as_known_by_market(RATE, T, Q)
    assert [str(v.value) for v in view.values.values()] == ["3.60"]
    assert open_store(tmp_path / "a").as_known_by_market(RATE, T, Q) == view
    b, _ = genuinely_quarantined(tmp_path / "b")
    b.ingest(
        capture_bytes(
            b,
            tmp_path / "b",
            VALID.replace("2026-01-12T00:00:00Z", "2026-01-14T00:00:00Z"),
            utc(2026, 1, 14, 1),
        ),
        CaptureMode.SCHEDULED,
    )
    assert b.as_known_by_market(RATE, T, Q) == view
    record = json.loads(a.store.get(next(k for k in a.store.list("catalogue/quarantine/receipts/"))))
    assert record["reason"]  # the marker records why, and the reason is re-derived on every check


def test_a_held_vintage_without_a_verified_capture_event_refuses(tmp_path):
    """Removing a processed receipt's capture record drops it from E(Q); its vintage must not stay
    held (it could still create or outrank a conflict)."""
    from hio.contracts.layout import capture_record_key

    root = tmp_path / "s"
    vs = open_store(root)
    receipt = capture_bytes(vs, root, VALID, utc(2026, 1, 12, 1))
    vs.ingest(receipt, CaptureMode.SCHEDULED)
    path = root / capture_record_key(SRC, receipt.captured_at, receipt.receipt_id)
    path.chmod(0o644)
    path.unlink()
    every_path_refuses(root, T, Q, IncompleteProcessing)
