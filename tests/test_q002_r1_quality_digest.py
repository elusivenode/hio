"""Acceptance tests for OBS-AMEND-Q002-R1 revision 1 (approved, OD-0035; blob cb7a937d): the
quality_digest reproducibility pin. AT-Q2R1-1..7.

Codex's counterexample (VERIFY-2026-10-24-s1a-1-9): two valid stores with one identical receipt,
one of them with an owner QUARANTINED decision before the cutoff, gave different results under
identical evidence, resolution and algorithm pins.
"""

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from hio.contracts.canonical import canonical_json
from hio.contracts.temporal import KnowledgeMode, QualityStatus
from hio.jobs import s1a
from hio.marketdata.capture import SyntheticSource, capture
from hio.marketdata.queries import ALGORITHM_REVISION
from hio.marketdata.series import CaptureMode
from hio.marketdata.vintages import IncompleteProcessing, PinMismatch, VintageStore
from hio.rights.gate import RightsGate
from hio.rights.register import load_synthetic
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import FIXTURES, SERIES, AllowAllGate, receipt_text, utc

RATE, SRC = "synthetic.rate", "synthetic.daily_source"
D1 = date(2026, 1, 12)
T = utc(2026, 1, 15)
ROW = receipt_text(
    "q", [f"{RATE},2026-01-12,3.60,2026-01-12T00:00:00Z"], "series_id,valid_time,value,published_at"
)


def open_store(root, clock=lambda: utc(2026, 1, 1)):
    return VintageStore(LocalObjectStore(root), SERIES, clock=clock)


def one_receipt(root, clock=lambda: utc(2026, 1, 1)):
    vs = open_store(root, clock)
    path = root / f"{SRC}.csv"
    path.write_text(ROW)
    receipt, _ = capture(SyntheticSource(SRC, path), vs.store, AllowAllGate(), utc(2026, 1, 12, 1))
    vs.ingest(receipt, CaptureMode.SCHEDULED)
    return vs


def pins(view):
    return (view.evidence_digest, view.resolution_digest, view.quality_digest, view.algorithm_revision)


def empty_value(series_id):
    return hashlib.sha256(
        canonical_json({"schema": "hio-quality-digest/1", "series_id": series_id, "events": []})
    ).hexdigest()


# --- AT-Q2R1-1: Codex's two valid stores ------------------------------------------------------------


def test_at_q2r1_1_codex_two_valid_stores_have_different_quality_digests(tmp_path):
    a = one_receipt(tmp_path / "a")
    b = one_receipt(tmp_path / "b")
    b.set_quality(RATE, D1, 1, QualityStatus.QUARANTINED, "owner", "x", utc(2026, 1, 14))
    va, vb = a.as_captured_by_hio(RATE, T), b.as_captured_by_hio(RATE, T)
    assert {k: v.value for k, v in va.values.items()} == {D1: Decimal("3.60")} and vb.values == {}
    assert (va.evidence_digest, va.resolution_digest, va.algorithm_revision) == (
        vb.evidence_digest,
        vb.resolution_digest,
        vb.algorithm_revision,
    )
    assert va.quality_digest != vb.quality_digest
    assert va.algorithm_revision == ALGORITHM_REVISION == "hio-obs-select/3"


# --- AT-Q2R1-2: fixed-cutoff stability ---------------------------------------------------------------


def test_at_q2r1_2_later_decisions_leave_the_result_and_all_pins_unchanged(tmp_path):
    vs = one_receipt(tmp_path / "s")
    before = vs.as_captured_by_hio(RATE, T)
    vs.set_quality(RATE, D1, 1, QualityStatus.QUARANTINED, "owner", "later", utc(2026, 1, 16))
    vs.set_quality(RATE, D1, 1, QualityStatus.VALID, "owner", "later still", utc(2026, 1, 17))
    assert vs.as_captured_by_hio(RATE, T) == before
    assert open_store(tmp_path / "s").as_captured_by_hio(RATE, T) == before  # after reopening
    assert pins(vs.as_captured_by_hio(RATE, utc(2026, 1, 18))) != pins(before)  # in force later


# --- AT-Q2R1-3: sensitivity to included fields only --------------------------------------------------


def _alter_event(vs, change):
    (key,) = list(vs.store.list("catalogue/quality/"))
    record = json.loads(vs.store.get(key))
    change(record)
    path = vs.store.root / key
    path.chmod(0o644)
    path.write_bytes(canonical_json(record))


@pytest.mark.parametrize(
    ("field", "value", "included"),
    [
        ("status", "valid", True),
        ("decided_at", "2026-01-14T06:00:00.000000Z", True),
        ("actor", "gate", True),
        ("evidence", "different reason", True),
        ("recorded_at", "2026-01-02T00:00:00.000000Z", False),
    ],
)
def test_at_q2r1_3_included_fields_change_the_digest_and_excluded_ones_do_not(
    tmp_path, field, value, included
):
    vs = one_receipt(tmp_path / "s")
    vs.set_quality(RATE, D1, 1, QualityStatus.QUARANTINED, "owner", "x", utc(2026, 1, 14))
    before = vs.quality_digest(RATE, T)
    _alter_event(vs, lambda r: r.__setitem__(field, value))
    after = open_store(tmp_path / "s").quality_digest(RATE, T)
    assert (after != before) is included


# --- AT-Q2R1-4: independent reconstruction -----------------------------------------------------------


def test_at_q2r1_4_a_fresh_store_with_a_faithful_copy_recorded_later_reproduces_everything(tmp_path):
    a = one_receipt(tmp_path / "a", clock=lambda: utc(2026, 1, 1))
    a.set_quality(RATE, D1, 1, QualityStatus.QUARANTINED, "owner", "x", utc(2026, 1, 14))
    b = one_receipt(tmp_path / "b", clock=lambda: utc(2026, 1, 13))  # recorded at a different time
    b.set_quality(RATE, D1, 1, QualityStatus.QUARANTINED, "owner", "x", utc(2026, 1, 14))
    assert a.as_captured_by_hio(RATE, T) == b.as_captured_by_hio(RATE, T)
    b.verify_pins(RATE, KnowledgeMode.AS_CAPTURED_BY_HIO, T, None, pins(a.as_captured_by_hio(RATE, T)))


# --- AT-Q2R1-5: the empty history ---------------------------------------------------------------------


def test_at_q2r1_5_no_decisions_give_the_documented_empty_value(tmp_path):
    vs = one_receipt(tmp_path / "s")
    assert vs.quality_digest(RATE, T) == empty_value(RATE)
    assert vs.as_captured_by_hio(RATE, T).quality_digest == empty_value(RATE)
    vs.set_quality(RATE, D1, 1, QualityStatus.QUARANTINED, "owner", "x", utc(2026, 1, 16))
    assert vs.quality_digest(RATE, T) == empty_value(RATE)  # decided after Q: still empty at Q


# --- AT-Q2R1-6: refusal on mismatched or unavailable inputs --------------------------------------------


def test_at_q2r1_6_mismatched_pins_refuse(tmp_path):
    vs = one_receipt(tmp_path / "s")
    recorded = pins(vs.as_captured_by_hio(RATE, T))
    vs.verify_pins(RATE, KnowledgeMode.AS_CAPTURED_BY_HIO, T, None, recorded)
    vs.set_quality(
        RATE, D1, 1, QualityStatus.QUARANTINED, "owner", "x", utc(2026, 1, 14)
    )  # history now differs
    with pytest.raises(PinMismatch, match="quality_digest"):
        vs.verify_pins(RATE, KnowledgeMode.AS_CAPTURED_BY_HIO, T, None, recorded)
    for i, name in enumerate(
        ("evidence_digest", "resolution_digest", "quality_digest", "algorithm_revision")
    ):
        wrong = list(pins(vs.as_captured_by_hio(RATE, T)))
        wrong[i] = "0" * 64
        with pytest.raises(PinMismatch, match=name):
            vs.verify_pins(RATE, KnowledgeMode.AS_CAPTURED_BY_HIO, T, None, tuple(wrong))


def test_at_q2r1_6_a_quality_event_for_an_unavailable_vintage_refuses(tmp_path):
    vs = one_receipt(tmp_path / "s")
    vs.set_quality(RATE, D1, 1, QualityStatus.QUARANTINED, "owner", "x", utc(2026, 1, 14))
    _alter_event(vs, lambda r: r.__setitem__("vintage_seq", 9))  # names a vintage that does not exist
    with pytest.raises(IncompleteProcessing):
        open_store(tmp_path / "s").as_captured_by_hio(RATE, T)


# --- AT-Q2R1-7: release provenance --------------------------------------------------------------------

S1A_DATA_SHA256 = {
    "cash.aud.overnight": "9e3a03e9c5f5e6bca5bd97ffd8786451439f65ec9602a8abb2460fda172fe73c",
    "cash.usd.overnight": "97faf4e8eaba6be8b17a35d34b539ddafafe120e667ef60e78187f13acf8c6b2",
    "fx.usd_cash_vs_aud.decomposition": "6e6284932674e81cd8969f8bda3672e4a6e9ce75bbaa019ca9c6006bba125a95",
    "fx.usd_cash_vs_aud.excess": "b8ea0d6f293dbefc6e3bfd6e9da99b2751d640486b5d90bd69663e8cbeb46587",
}
CUTOFF = datetime(2026, 1, 29, tzinfo=UTC)
CODE = {"commit": "0" * 40, "lock_sha256": "1" * 64}


def s1a_store(root):
    world = s1a.load_world(FIXTURES / "s1a_world")
    rights = dict(load_synthetic(FIXTURES / "rights.yaml"))
    vs = VintageStore(LocalObjectStore(root), world.series, clock=lambda: utc(2026, 1, 1))
    gate = RightsGate(rights)
    s1a.run_captures(world, vs, gate, s1a.capture_instants(date(2026, 1, 5), CUTOFF))
    return world, rights, vs, gate


def test_at_q2r1_7_releases_carry_the_pin_and_references_and_verify(tmp_path):
    world, rights, vs, gate = s1a_store(tmp_path / "s")
    releases = s1a.build_releases(world, vs, gate, rights, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE)
    assert {
        d: hashlib.sha256(r.files["data.csv"]).hexdigest() for d, r in releases.items()
    } == S1A_DATA_SHA256
    for release in releases.values():
        views = [i for i in release.core["inputs"] if "series_id" in i]
        assert views
        for i in views:
            assert (
                i["quality_digest"] == empty_value(i["series_id"])
                and i["algorithm_revision"] == "hio-obs-select/3"
            )
            assert i["evidence_refs"] and i["quality_event_refs"] == [] and i["resolution_refs"] == []
        s1a.verify_release_inputs(vs, release.core)  # every referenced input reproduces its pins
    # A fresh store rebuilt from the same captured evidence verifies the same release inputs.
    _, _, fresh, _ = s1a_store(tmp_path / "fresh")
    for release in releases.values():
        s1a.verify_release_inputs(fresh, release.core)


def test_at_q2r1_7_an_altered_quality_history_fails_release_verification(tmp_path):
    world, rights, vs, gate = s1a_store(tmp_path / "s")
    vintage = next(v for v in vs.all_vintages() if v.series_id == s1a.CASH_RATE)
    vs.set_quality(
        s1a.CASH_RATE,
        vintage.valid_time,
        vintage.vintage_seq,
        QualityStatus.VALID,
        "owner",
        "x",
        datetime(2026, 1, 20, tzinfo=UTC),
    )
    releases = s1a.build_releases(world, vs, gate, rights, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE)
    core = releases["cash.aud.overnight"].core
    s1a.verify_release_inputs(vs, core)
    (key,) = [k for k in vs.store.list("catalogue/quality/")]
    record = json.loads(vs.store.get(key))
    record["evidence"] = "rewritten after publication"
    path = vs.store.root / key
    path.chmod(0o644)
    path.write_bytes(canonical_json(record))
    with pytest.raises(PinMismatch):
        s1a.verify_release_inputs(VintageStore(vs.store, world.series, clock=lambda: utc(2026, 1, 1)), core)
