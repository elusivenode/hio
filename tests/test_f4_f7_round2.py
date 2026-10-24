"""Regression tests for VERIFY-2026-10-24-s1a-1-6 (OD-0031): F4/F7 round 2.

1. Completeness (OBS-INV-019, OBS-INV-018). A captured receipt repeating an existing value with
   stronger timing evidence was treated as a no-op by value equality, so an unprocessed receipt
   let a query be served, and processing it later changed the result at the same (T, Q) under the
   same evidence digest. Every captured receipt must now be accounted for by its own processing
   outcome, which keeps capture evidence, capture mode and outcome distinct.
2. Admissibility (OBS-INV-014). A Q > T market build reached the point-in-time release path and
   was published. It must be refused before anything is built or written, with no override.
"""

import json
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from hio.contracts.temporal import KnowledgeMode
from hio.jobs import s1a
from hio.marketdata.capture import SyntheticSource, capture
from hio.marketdata.queries import InadmissibleForPredictivePointInTime
from hio.marketdata.series import CaptureMode
from hio.marketdata.vintages import IncompleteProcessing, VintageStore
from hio.rights.gate import RightsGate
from hio.rights.register import load_synthetic
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import FIXTURES, SERIES, AllowAllGate, receipt_text, utc

RATE, SRC = "synthetic.rate", "synthetic.daily_source"
D1 = date(2026, 1, 12)
CLOCK = lambda: utc(2026, 1, 1)  # noqa: E731


def capture_only(vs, tmp, text, at):
    path = tmp / f"{SRC}.csv"
    path.write_text(text)
    receipt, is_new = capture(SyntheticSource(SRC, path), vs.store, AllowAllGate(), at)
    assert is_new
    return receipt


def values(view):
    return {k: v.value for k, v in view.values.items()}


# --- 1. Codex's completeness counterexample -----------------------------------------------------------

T, Q = utc(2026, 1, 13), utc(2026, 1, 15)


def codex_store(tmp_path):
    vs = VintageStore(LocalObjectStore(tmp_path / "s"), SERIES, clock=CLOCK)
    first = capture_only(
        vs, tmp_path, receipt_text("plain", [f"{RATE},2026-01-12,3.60"]), utc(2026, 1, 13, 12)
    )
    vs.ingest(first, CaptureMode.BACKFILL)  # a schedule_only vintage
    stronger = capture_only(
        vs,
        tmp_path,
        receipt_text(
            "stamped",
            [f"{RATE},2026-01-12,3.60,2026-01-12T00:00:00Z"],
            "series_id,valid_time,value,published_at",
        ),
        utc(2026, 1, 14, 12),
    )  # the same value and key, with a publisher timestamp: left unprocessed
    return vs, stronger


def test_codex_round6_an_unprocessed_same_value_receipt_with_stronger_evidence_refuses(tmp_path):
    vs, _ = codex_store(tmp_path)
    with pytest.raises(IncompleteProcessing):
        vs.as_known_by_market(RATE, T, Q)
    with pytest.raises(IncompleteProcessing):
        vs.conflicts(RATE, Q)


def test_codex_round6_fixed_t_q_and_evidence_cannot_silently_give_two_results(tmp_path):
    vs, stronger = codex_store(tmp_path)
    try:
        before = vs.as_known_by_market(RATE, T, Q)
    except IncompleteProcessing:
        before = None  # refused, not served
    vs.ingest(stronger, CaptureMode.SCHEDULED)
    after = vs.as_known_by_market(RATE, T, Q)
    assert values(after) == {D1: Decimal("3.60")}
    # Either the earlier query was refused, or it gave the same result with the same pins.
    assert before is None or (before == after and before.evidence_digest == after.evidence_digest)


def test_the_capture_mode_is_part_of_the_evidence_pin(tmp_path):
    """Receipt bytes alone do not determine the vintages; the capture mode does too, so it is
    pinned (distinct from capture evidence and from the processing outcome)."""
    vs, stronger = codex_store(tmp_path)
    vs.ingest(stronger, CaptureMode.SCHEDULED)
    digest = vs.evidence_digest(RATE, Q)
    other, stronger2 = codex_store(tmp_path / "b")
    other.ingest(stronger2, CaptureMode.BACKFILL)
    assert other.evidence_digest(RATE, Q) != digest


def test_a_forged_processing_outcome_is_detected(tmp_path):
    """The outcome is checked against the receipt's rows (identity and content) and against the
    vintages it claims; a record claiming a no-op the evidence does not support is refused."""
    vs, stronger = codex_store(tmp_path)
    vs.ingest(stronger, CaptureMode.SCHEDULED)
    (key,) = [k for k in vs.store.list("catalogue/processed/") if stronger.receipt_id in k]
    record = json.loads(vs.store.get(key))
    for row in record["rows"]:
        row["disposition"], row["vintage_seq"] = "redundant", None  # claim a no-op instead
    path = vs.store.root / key
    path.chmod(0o644)
    path.write_text(json.dumps(record))
    with pytest.raises(IncompleteProcessing):
        VintageStore(vs.store, SERIES, clock=CLOCK).as_known_by_market(RATE, T, Q)


# --- 2. Admissibility at the point-in-time release boundary ------------------------------------------


def s1a_world(tmp_path):
    world = s1a.load_world(FIXTURES / "s1a_world")
    rights = dict(load_synthetic(FIXTURES / "rights.yaml"))
    store = LocalObjectStore(tmp_path / "s")
    vs = VintageStore(store, world.series)
    gate = RightsGate(rights)
    s1a.run_captures(
        world, vs, gate, s1a.capture_instants(date(2026, 1, 5), datetime(2026, 1, 29, tzinfo=UTC))
    )
    return world, rights, store, vs, gate


CODE = {"commit": "0" * 40, "lock_sha256": "1" * 64}


def test_codex_round6_a_q_after_t_market_build_is_refused_and_nothing_is_written(tmp_path):
    world, rights, store, vs, gate = s1a_world(tmp_path)
    before = store.snapshot()
    with pytest.raises(InadmissibleForPredictivePointInTime):
        s1a.build_releases(
            world,
            vs,
            gate,
            rights,
            KnowledgeMode.AS_KNOWN_BY_MARKET,
            datetime(2026, 1, 12, tzinfo=UTC),
            CODE,
            datetime(2026, 1, 29, tzinfo=UTC),
        )
    assert store.snapshot() == before
    assert not any(k.startswith("releases/") for k in store.list())


def test_admissible_point_in_time_builds_still_publish(tmp_path):
    world, rights, _, vs, gate = s1a_world(tmp_path)
    cutoff = datetime(2026, 1, 29, tzinfo=UTC)
    for mode, q in ((KnowledgeMode.AS_CAPTURED_BY_HIO, None), (KnowledgeMode.AS_KNOWN_BY_MARKET, cutoff)):
        releases = s1a.build_releases(world, vs, gate, rights, mode, cutoff, CODE, q)
        s1a.publish_releases(vs, gate, releases, cutoff)
        assert set(releases) == {
            "cash.aud.overnight",
            "cash.usd.overnight",
            "fx.usd_cash_vs_aud.decomposition",
            "fx.usd_cash_vs_aud.excess",
        }
