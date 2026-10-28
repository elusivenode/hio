"""Adversarial regressions for F-REVIEW-2026-10-25-t0009-6 (OD-0067): a verified capture-run record
names every key it checked with a digest of the value, for a changed and an unchanged response; a
response that drops an expected key fails as `key_missing` and writes nothing else. No finality is
claimed: these are the recorded facts C3 will later replay (OD-0063 staging)."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from hio.contracts.canonical import canonical_json, decimal_str
from hio.contracts.layout import CAPTURES_PREFIX, LINKS_PREFIX
from hio.marketdata.capture import load_receipt_record, receipt_bytes
from hio.marketdata.runrecord import IntegrityError, RunRecord, load_run_record, value_digest
from hio.sources.datasets import PUBLICATIONS
from hio.sources.run import checked_keys
from hio.sources.transport import FixtureTransport, HttpResponse
from hio.storage.objectstore import LocalObjectStore
from tests.test_s1b1_capture import (  # noqa: F401  (store is a fixture)
    FILES,
    HEADERS,
    URL,
    attempts,
    clock,
    go,
    resp,
    store,
    t,
)

AONIA, TRI = "rba.cash_rate.aonia", "rba.cash_rate.tri"


def body(text: str, sid: str = "rba.f1") -> HttpResponse:
    return HttpResponse(200, HEADERS, text.encode(), URL.format(sid))


F1_HEAD = "F1 (SYNTHETIC FIXTURE),,\nSeries ID,FIRMMCRID,FIRMMCTRI\n"


def replay(store, record: RunRecord) -> list[tuple[str, str, str]]:
    """C3's arithmetic, independently: parse the stored bytes and digest each value."""
    key = next(k for k in store.list(CAPTURES_PREFIX) if k.endswith(f"-{record.receipt_id}.json"))
    parsed = PUBLICATIONS[record.source_id].parse(receipt_bytes(store, load_receipt_record(store, key)))
    out = {(r.series_id, r.valid_time.isoformat(), value_digest(decimal_str(r.value))) for r in parsed.rows}
    out |= {
        ("rba.expert_judgement.fallback_type", f.valid_time.isoformat(), value_digest(f.kind))
        for f in parsed.flags
    }
    return sorted(out)


@pytest.mark.parametrize("sid", sorted(PUBLICATIONS))
def test_f6_a_changed_capture_records_every_key_with_a_replayable_digest(sid, store):
    result = go(sid, FixtureTransport({URL.format(sid): [resp(FILES[sid])]}), store, clock(t(1), t(2)))
    rec = load_run_record(store, result.record.key)
    assert rec.outcome == "verified_changed" and rec.keys_checked
    assert list(rec.keys_checked) == replay(store, rec)
    assert json.loads(store.get(result.record.key))["keys_checked"] == [list(k) for k in rec.keys_checked]


def test_f6_an_unchanged_response_records_the_same_keys_against_the_held_receipt(store):
    url = URL.format("rba.f1")
    transport = FixtureTransport({url: [resp(FILES["rba.f1"]), resp(FILES["rba.f1"])]})
    first = go("rba.f1", transport, store, clock(t(1), t(2)))
    second = go("rba.f1", transport, store, clock(t(3), t(4)))
    assert second.record.outcome == "verified_unchanged" and not second.is_new
    assert second.record.receipt_id == first.record.receipt_id
    assert second.record.keys_checked == first.record.keys_checked
    assert list(second.record.keys_checked) == replay(store, second.record)
    keys = {(k[0], k[1]) for k in second.record.keys_checked}
    assert (AONIA, "2026-10-22") in keys and (TRI, "2026-10-23") in keys
    assert (AONIA, "2026-10-23") not in keys  # an empty cell is not yet published: not a checked key


def test_f6_digests_do_not_depend_on_the_published_trailing_zeros():
    a = checked_keys(PUBLICATIONS["rba.f1"].parse((F1_HEAD + "21-Oct-2026,3.60,100.50\n").encode()))
    b = checked_keys(PUBLICATIONS["rba.f1"].parse((F1_HEAD + "21-Oct-2026,3.6,100.5\n").encode()))
    assert a == b and a[0][2] == value_digest("3.6")
    c = checked_keys(PUBLICATIONS["rba.f1"].parse((F1_HEAD + "21-Oct-2026,3.61,100.5\n").encode()))
    assert c != a  # a different value is a different digest


def test_f6_a_response_dropping_a_held_key_fails_as_key_missing_and_writes_nothing_else(store):
    url = URL.format("rba.f1")
    full = F1_HEAD + "21-Oct-2026,3.60,100.50\n22-Oct-2026,3.61,100.60\n23-Oct-2026,3.62,100.70\n"
    holed = F1_HEAD + "21-Oct-2026,3.60,100.50\n22-Oct-2026,,100.60\n23-Oct-2026,3.62,100.70\n"
    transport = FixtureTransport({url: [body(full), body(holed)]})
    go("rba.f1", transport, store, clock(t(1), t(2)))
    before = {k for k in store.snapshot() if not k.startswith("catalogue/attempts/")}
    result = go("rba.f1", transport, store, clock(t(3), t(4)))
    assert result.record.outcome == "failed" and result.record.error_class == "key_missing"
    assert result.receipt is None and result.record.keys_checked is None
    assert {k for k in store.snapshot() if not k.startswith("catalogue/attempts/")} == before
    assert len(attempts(store)) == 2
    assert load_run_record(store, result.record.key).error_class == "key_missing"


def test_f6_a_response_without_any_key_of_a_served_series_fails_as_key_missing(store):
    url = URL.format("rba.f1")
    no_tri = F1_HEAD + "21-Oct-2026,3.60,\n22-Oct-2026,3.61,\n"
    result = go("rba.f1", FixtureTransport({url: [body(no_tri)]}), store, clock(t(1), t(2)))
    assert result.record.error_class == "key_missing"
    assert not list(store.list(CAPTURES_PREFIX)) and not list(store.list(LINKS_PREFIX))


def test_f6_a_key_rolled_off_the_start_of_a_window_is_not_missing(store):
    url = URL.format("nyfed.sofr")
    v1 = (
        '{"refRates":[{"effectiveDate":"2026-10-21","type":"SOFR","percentRate":3.65},'
        '{"effectiveDate":"2026-10-22","type":"SOFR","percentRate":3.66}]}'
    )
    v2 = (
        '{"refRates":[{"effectiveDate":"2026-10-22","type":"SOFR","percentRate":3.66},'
        '{"effectiveDate":"2026-10-23","type":"SOFR","percentRate":3.67}]}'
    )
    transport = FixtureTransport({url: [body(v1, "nyfed.sofr"), body(v2, "nyfed.sofr")]})
    go("nyfed.sofr", transport, store, clock(t(1), t(2)))
    result = go("nyfed.sofr", transport, store, clock(t(3), t(4)))
    assert result.record.outcome == "verified_changed"


def test_f6_record_shape_is_enforced_and_tampering_with_keys_is_detected(store, tmp_path):
    result = go(
        "rba.f1", FixtureTransport({URL.format("rba.f1"): [resp(FILES["rba.f1"])]}), store, clock(t(1), t(2))
    )
    rec = result.record
    with pytest.raises(ValueError, match="records the keys it checked"):
        replace(rec, keys_checked=None)
    with pytest.raises(ValueError, match="claims no checked keys"):
        replace(rec, outcome="failed", error_class="parse", receipt_id=None)
    with pytest.raises(ValueError, match="sorted"):
        replace(rec, keys_checked=list(reversed(rec.keys_checked)))
    tampered = json.loads(store.get(rec.key))
    tampered["keys_checked"] = tampered["keys_checked"][1:]  # quietly drop one checked key
    forged = LocalObjectStore(tmp_path / "forged")  # the real store is write-once: forge a copy
    forged.put(rec.key, canonical_json(tampered))
    with pytest.raises(IntegrityError):
        load_run_record(forged, rec.key)
