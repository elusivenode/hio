"""OD-0065: one immutable F1 receipt serves rba.cash_rate and rba.cash_rate_tri, each keeping its own
dataset identity and rights evaluation. Shared-receipt attribution, cross-dataset rights, denied
publication, replay, fail-closed provenance, and the unchanged single-dataset behaviour."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from hio.contracts.canonical import canonical_json
from hio.contracts.layout import CAPTURES_PREFIX, LINKS_PREFIX
from hio.contracts.rights import Operation, RightsRefused
from hio.contracts.temporal import KnowledgeMode
from hio.jobs.s1a import publish_releases
from hio.jobs.s1b1 import _places, build_releases, ingest_pending, sofr_calendar, vintage_store
from hio.marketdata.capture import load_receipt_record
from hio.marketdata.vintages import ReceiptIntegrityError
from hio.publish.lineage import stored_release_sources
from hio.publish.release import write_release
from hio.rights.gate import RightsGate
from hio.rights.model import ALL_PERMISSIONS, Permission, RightsRecord, Verification
from hio.sources.datasets import PUBLICATIONS
from hio.sources.run import run_capture
from hio.sources.transport import FixtureTransport
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import AllowAllGate
from tests.test_s1b1_capture import EXEC, UA
from tests.test_s1b1_releases import (  # noqa: F401  (world is a fixture)
    AUD_DAYS,
    NSW,
    RITS,
    Calendars,
    allow,
    f1_csv,
    resp,
    world,
)

AONIA, TRI = "rba.cash_rate.aonia", "rba.cash_rate.tri"


def record(sid: str, **deny: str) -> RightsRecord:
    perms = {p: Permission.parse(deny.get(p, "allow")) for p in ALL_PERMISSIONS}
    return RightsRecord(sid, Verification.OWNER_VERIFIED, perms)


def copy_store(store, tmp_path, name, keep=lambda _key: True, replace=None):
    local = LocalObjectStore(tmp_path / name)
    for key in store.snapshot():
        if keep(key):
            local.put(key, (replace or {}).get(key, store.get(key)))
    return local


def test_one_raw_receipt_serves_both_datasets(world):
    store, *_ = world
    captures = list(store.list(CAPTURES_PREFIX + "rba.f1/"))
    assert len(captures) == len(AUD_DAYS) - 1  # a capture per day, each stored once
    assert not list(store.list(CAPTURES_PREFIX + "rba.cash_rate/"))
    assert not list(store.list(CAPTURES_PREFIX + "rba.cash_rate_tri/"))  # no per-dataset copy of the file
    links = [json.loads(store.get(k)) for k in store.list(LINKS_PREFIX)]
    assert len(links) == len(captures) and {k.split("/")[2] for k in store.list(LINKS_PREFIX)} == {"rba.f1"}
    for link in links:
        assert link["publication_id"] == "rba.f1"
        assert link["datasets"] == {"rba.cash_rate": [AONIA], "rba.cash_rate_tri": [TRI]}
    assert {link["receipt_id"] for link in links} == {
        load_receipt_record(store, k).receipt_id for k in captures
    }


def test_each_observation_keeps_its_dataset_identity_and_rights_subject(world):
    _, _, vs, cutoff, *_ = world
    aonia, tri = vs.series[AONIA], vs.series[TRI]
    assert (aonia.source_id, aonia.dataset_id) == ("rba.f1", "rba.cash_rate")
    assert (tri.source_id, tri.dataset_id) == ("rba.f1", "rba.cash_rate_tri")
    shared = {v.receipt_id for v in vs.all_vintages() if v.series_id in (AONIA, TRI)}
    assert shared  # the same stored receipts back both series
    mode = KnowledgeMode.AS_CAPTURED_BY_HIO
    assert vs.sources_of(vs.view(AONIA, mode, cutoff, None)) == {"rba.cash_rate"}
    assert vs.sources_of(vs.view(TRI, mode, cutoff, None)) == {"rba.cash_rate_tri"}
    assert {v.receipt_id for v in vs.view(AONIA, mode, cutoff, None).values.values()} <= shared


def test_release_lineage_names_only_the_datasets_a_release_uses(world, tmp_path):
    store, cals, _vs, cutoff, _rights, _code, built = world
    local = copy_store(store, tmp_path, "pub")
    publish_releases(vintage_store(local, cals), AllowAllGate(), built, cutoff)
    sources = {k: stored_release_sources(local, r.content_sha256)[2] for k, r in built.items()}
    assert sources["cash.aud.overnight"] == {"rba.cash_rate"}
    assert sources["cash.aud.overnight.vs_tri"] == {"rba.cash_rate", "rba.cash_rate_tri"}
    assert sources["cash.usd.overnight"] == {"nyfed.sofr"}
    assert sources["cash.usd.overnight.vs_sofr_index"] == {"nyfed.sofr", "nyfed.sofr_index"}


def test_single_dataset_receipts_have_no_link_and_keep_their_source(world):
    store, *_ = world
    assert all("/rba.f1/" in k for k in store.list(LINKS_PREFIX))  # only the shared file is linked
    for sid in ("nyfed.sofr", "nyfed.sofr_index"):
        assert not [k for k in store.list(LINKS_PREFIX) if f"/{sid}/" in k]
        assert list(store.list(CAPTURES_PREFIX + sid + "/"))  # captured under their own id, as in S1a


def test_capturing_the_file_needs_every_dataset_it_serves(tmp_path):
    store = LocalObjectStore(tmp_path / "s")
    url = "https://fixture.invalid/rba.f1"
    transport = FixtureTransport({url: [resp(f1_csv(AUD_DAYS[3]), url)]})
    gate = RightsGate(
        {
            "rba.cash_rate": record("rba.cash_rate"),
            "rba.cash_rate_tri": record("rba.cash_rate_tri", raw_retention="deny"),
        }
    )
    with pytest.raises(RightsRefused, match=r"rba.cash_rate_tri: raw_retention"):
        run_capture(
            PUBLICATIONS["rba.f1"],
            transport=transport,
            store=store,
            gate=gate,
            clock=iter([datetime(2026, 10, 22, tzinfo=UTC)] * 2).__next__,
            execution=EXEC,
            user_agent=UA,
            url=url,
        )
    assert transport.requests == [] and store.snapshot() == {}


def test_building_is_evaluated_per_output_on_the_datasets_it_uses(world):
    _, cals, vs, cutoff, _rights, code, _ = world
    rights = {s: allow(s) for s in ("rba.cash_rate", "nyfed.sofr", "nyfed.sofr_index")}
    rights["rba.cash_rate_tri"] = record("rba.cash_rate_tri", derivation="deny")
    gate = RightsGate(rights)
    aud = build_releases(vs, gate, rights, cals, cutoff, code, outputs=["cash.aud.overnight"])
    assert set(aud) == {"cash.aud.overnight"}  # the TRI's denial does not stop the cash leg
    with pytest.raises(RightsRefused, match=r"rba.cash_rate_tri: derivation"):
        build_releases(vs, gate, rights, cals, cutoff, code, outputs=["cash.aud.overnight.vs_tri"])


def test_denied_publication_is_per_dataset(world, tmp_path):
    store, _cals, _vs, _cutoff, _rights, _code, built = world
    rights = {s: allow(s) for s in ("rba.cash_rate", "nyfed.sofr", "nyfed.sofr_index")}
    rights["rba.cash_rate_tri"] = record("rba.cash_rate_tri", derived_storage="deny")
    gate = RightsGate(rights)
    local = copy_store(store, tmp_path, "deny")
    assert write_release(local, gate, built["cash.aud.overnight"])  # AONIA only: allowed
    with pytest.raises(RightsRefused, match=r"rba.cash_rate_tri: derived_storage"):
        write_release(local, gate, built["cash.aud.overnight.vs_tri"])
    assert not [k for k in local.list("releases/") if "vs_tri" in k]  # nothing partial
    with pytest.raises(RightsRefused):  # no consumer distribution is granted by any record here
        RightsGate({"rba.cash_rate": record("rba.cash_rate", **{"distribution.smsf_app": "deny"})}).authorise(
            Operation.PUBLISH, ["rba.cash_rate"], "smsf_app"
        )


def test_replay_from_receipts_and_links_alone_reproduces_every_release(world, tmp_path):
    store, _cals, _vs, cutoff, rights, code, built = world
    evidence = ("receipts/", CAPTURES_PREFIX, LINKS_PREFIX, "catalogue/attempts/")
    bare = copy_store(store, tmp_path, "bare", keep=lambda k: k.startswith(evidence))
    fresh_cals = Calendars(RITS, NSW, sofr_calendar(bare, cutoff))
    vs = vintage_store(bare, fresh_cals)
    assert ingest_pending(vs, cutoff) > 0  # every vintage re-derived from the stored files
    again = build_releases(vs, AllowAllGate(), rights, fresh_cals, cutoff, code)
    assert {k: r.content_sha256 for k, r in again.items()} == {k: r.content_sha256 for k, r in built.items()}


def test_a_shared_receipt_without_its_link_fails_closed(world, tmp_path):
    store, cals, _vs, cutoff, _rights, _code, built = world
    local = copy_store(store, tmp_path, "nolink", keep=lambda k: not k.startswith(LINKS_PREFIX))
    with pytest.raises(ReceiptIntegrityError, match="no provenance link"):
        vintage_store(local, cals).view(
            AONIA,
            KnowledgeMode.AS_CAPTURED_BY_HIO,
            cutoff,
            None,
        )
    gate = RightsGate(
        {s: allow(s) for s in ("rba.cash_rate", "rba.cash_rate_tri", "nyfed.sofr", "nyfed.sofr_index")}
    )
    # Without its link the receipt is attributed to the publication id, which has no rights record:
    # unknown means deny, so publishing is refused rather than guessed.
    with pytest.raises(RightsRefused, match=r"rba.f1: no rights record"):
        write_release(local, gate, built["cash.aud.overnight"])


def test_a_link_naming_the_wrong_dataset_fails_closed(world, tmp_path):
    store, cals, _vs, cutoff, *_ = world
    key = sorted(store.list(LINKS_PREFIX))[0]
    link = json.loads(store.get(key))
    link["datasets"] = {"rba.cash_rate": [TRI], "rba.cash_rate_tri": [AONIA]}  # swapped
    local = copy_store(store, tmp_path, "swap", replace={key: canonical_json(link)})
    with pytest.raises(ReceiptIntegrityError, match="is not linked to"):
        vintage_store(local, cals).view(AONIA, KnowledgeMode.AS_CAPTURED_BY_HIO, cutoff, None)


def test_decimal_places_do_not_depend_on_parsed_or_reloaded_form():
    assert _places(Decimal("100.1200")) == _places(Decimal("100.12")) == 2
    assert _places(Decimal("1.1200E+2")) == _places(Decimal("112")) == 0
