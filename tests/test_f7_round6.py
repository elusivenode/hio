"""Regression tests for VERIFY-2026-10-24-s1a-1-10 (OD-0036): loaded quality events obey the
Q-001 decision clock.

Codex: a stored event's recorded_at was changed to a time after its decided_at (a decision
"made" two days before it was recorded). On reopening, the store applied it, and verify_pins
reported all four pins equal, because quality_digest excludes recorded_at precisely on the
assumption that the no-backdating rule holds. Every loaded event is now validated with the same
rule as set_quality: recorded_at <= decided_at, and decided_at after the vintage's capture. An
invalid stored event refuses before it can reach a view, digest, pin check or release.
"""

import json
from datetime import date

import pytest

from hio.contracts.canonical import canonical_json
from hio.contracts.temporal import KnowledgeMode, QualityStatus
from hio.marketdata.capture import SyntheticSource, capture
from hio.marketdata.series import CaptureMode
from hio.marketdata.vintages import DecisionRefused, VintageStore
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import SERIES, AllowAllGate, receipt_text, utc

RATE, SRC = "synthetic.rate", "synthetic.daily_source"
D1 = date(2026, 1, 12)
T = utc(2026, 1, 15)
ROW = receipt_text(
    "q", [f"{RATE},2026-01-12,3.60,2026-01-12T00:00:00Z"], "series_id,valid_time,value,published_at"
)


def store_with_decision(root, clock=lambda: utc(2026, 1, 1)):
    vs = VintageStore(LocalObjectStore(root), SERIES, clock=clock)
    path = root / f"{SRC}.csv"
    path.write_text(ROW)
    receipt, _ = capture(SyntheticSource(SRC, path), vs.store, AllowAllGate(), utc(2026, 1, 12, 1))
    vs.ingest(receipt, CaptureMode.SCHEDULED)
    vs.set_quality(RATE, D1, 1, QualityStatus.QUARANTINED, "owner", "x", utc(2026, 1, 14))
    return vs


def alter_event(vs, **fields):
    (key,) = list(vs.store.list("catalogue/quality/"))
    record = json.loads(vs.store.get(key))
    for k, v in fields.items():
        if v is None:
            record.pop(k)
        else:
            record[k] = v
    path = vs.store.root / key
    path.chmod(0o644)
    path.write_bytes(canonical_json(record))


def pins(view):
    return (view.evidence_digest, view.resolution_digest, view.quality_digest, view.algorithm_revision)


@pytest.mark.parametrize(
    "fields",
    [
        {"recorded_at": "2026-01-16T00:00:00.000000Z"},  # Codex: recorded after it was decided
        {"decided_at": "2026-01-12T01:00:00.000000Z"},  # decided at the vintage's capture
        {
            "decided_at": "2026-01-12T00:30:00.000000Z",
            "recorded_at": "2026-01-12T00:00:00.000000Z",
        },  # before it
        {"recorded_at": None},  # no recording time at all
    ],
    ids=["recorded-after-decided", "decided-at-capture", "decided-before-capture", "recorded-at-missing"],
)
def test_an_invalid_stored_quality_event_refuses_on_reopen(tmp_path, fields):
    root = tmp_path / "s"
    vs = store_with_decision(root)
    recorded = pins(vs.as_captured_by_hio(RATE, T))
    alter_event(vs, **fields)
    # No path can use the store: views, digests, pin verification and releases all start from it.
    with pytest.raises(DecisionRefused):
        VintageStore(LocalObjectStore(root), SERIES, clock=lambda: utc(2026, 1, 1))
    with pytest.raises(DecisionRefused):
        VintageStore(LocalObjectStore(root), SERIES).verify_pins(
            RATE, KnowledgeMode.AS_CAPTURED_BY_HIO, T, None, recorded
        )


def test_faithful_copies_with_valid_differing_recorded_at_keep_identical_digests(tmp_path):
    a = store_with_decision(tmp_path / "a", clock=lambda: utc(2026, 1, 1))
    b = store_with_decision(tmp_path / "b", clock=lambda: utc(2026, 1, 13, 12))  # also valid
    va, vb = a.as_captured_by_hio(RATE, T), b.as_captured_by_hio(RATE, T)
    assert va == vb and pins(va) == pins(vb)
    # Reopened, and with a valid recorded_at change in place: still identical.
    alter_event(a, recorded_at="2026-01-13T23:00:00.000000Z")
    reopened = VintageStore(LocalObjectStore(tmp_path / "a"), SERIES, clock=lambda: utc(2026, 1, 1))
    assert reopened.as_captured_by_hio(RATE, T) == va
    reopened.verify_pins(RATE, KnowledgeMode.AS_CAPTURED_BY_HIO, T, None, pins(vb))
