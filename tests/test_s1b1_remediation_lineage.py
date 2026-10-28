"""Adversarial regressions for F-REVIEW-2026-10-25-t0009-1 and -2 (OD-0067): the rights subject of a
shared F1 receipt comes from the fixed publication mapping, never from links found in the store. Each
probe allows the subject the attack would substitute and denies (or leaves unknown) the true one, so a
pass cannot come from an incidental unknown-right refusal."""

from __future__ import annotations

import dataclasses
import json
from datetime import timedelta

import pytest

from hio.contracts.canonical import canonical_json
from hio.contracts.layout import LINKS_PREFIX, link_record_key
from hio.contracts.observation import parse_instant
from hio.contracts.publications import SHARED_PUBLICATIONS, link_datasets
from hio.contracts.temporal import KnowledgeMode
from hio.jobs.s1b1 import vintage_store
from hio.marketdata.vintages import ReceiptIntegrityError
from hio.publish.lineage import LineageError, release_sources
from hio.publish.release import write_release
from hio.rights.gate import RightsGate
from hio.sources.datasets import DATASETS, PUBLICATIONS, Publication
from tests.test_s1b1_releases import (  # noqa: F401  (world is a fixture)
    allow,
    world,
)
from tests.test_s1b1_shared_receipt import copy_store

AONIA, TRI = "rba.cash_rate.aonia", "rba.cash_rate.tri"
MODE = KnowledgeMode.AS_CAPTURED_BY_HIO


def _links(store):
    return sorted(store.list(LINKS_PREFIX))


def _assert_refused_and_nothing_written(local, gate, release):
    with pytest.raises(LineageError):
        release_sources(local, release.core)
    with pytest.raises(LineageError):
        write_release(local, gate, release)
    assert not list(local.list(f"releases/{release.core['dataset_id']}/"))


# --- F-1: a missing link must refuse whatever the rights register holds ---------------------------


def test_f1_missing_links_refuse_even_when_the_publication_id_is_allowed(world, tmp_path):
    store, *_rest, built = world
    local = copy_store(store, tmp_path, "nolinks", keep=lambda k: not k.startswith(LINKS_PREFIX))
    gate = RightsGate({"rba.f1": allow("rba.f1")})  # the substitute is allowed; rba.cash_rate is unknown
    _assert_refused_and_nothing_written(local, gate, built["cash.aud.overnight"])


def test_f1_one_missing_link_among_many_refuses(world, tmp_path):
    store, *_rest, built = world
    dropped = _links(store)[-1]
    local = copy_store(store, tmp_path, "onelink", keep=lambda k: k != dropped)
    gate = RightsGate({s: allow(s) for s in ("rba.f1", "rba.cash_rate")})
    _assert_refused_and_nothing_written(local, gate, built["cash.aud.overnight"])


def test_f1_a_series_definition_without_its_dataset_id_refuses_in_the_vintage_view(world):
    store, cals, _vs, cutoff, *_ = world
    vs = vintage_store(store, cals)
    vs.series[AONIA] = dataclasses.replace(vs.series[AONIA], dataset_id=None)
    with pytest.raises(ReceiptIntegrityError, match=r"assigns it to rba\.cash_rate"):
        vs.sources_of(vs.view(AONIA, MODE, cutoff, None))


# --- F-2: a substituted, duplicated or inconsistent link must refuse ------------------------------


def _rewrite_links(store, tmp_path, name, mutate):
    replace = {}
    for key in _links(store):
        link = json.loads(store.get(key))
        mutate(link)
        replace[key] = canonical_json(link)
    return copy_store(store, tmp_path, name, replace=replace)


def test_f2_a_substituted_single_owner_link_cannot_authorise_an_unrelated_dataset(world, tmp_path):
    store, *_rest, built = world

    def substitute(link):
        link["datasets"] = {"wrong.dataset": [AONIA], "rba.cash_rate_tri": [TRI]}

    local = _rewrite_links(store, tmp_path, "subst", substitute)
    gate = RightsGate({"wrong.dataset": allow("wrong.dataset")})  # the true dataset is unknown: denied
    _assert_refused_and_nothing_written(local, gate, built["cash.aud.overnight"])


def test_f2_a_link_that_swaps_the_two_real_datasets_refuses(world, tmp_path):
    store, *_rest, built = world

    def swap(link):
        link["datasets"] = {"rba.cash_rate": [TRI], "rba.cash_rate_tri": [AONIA]}

    local = _rewrite_links(store, tmp_path, "swap", swap)
    gate = RightsGate({"rba.cash_rate_tri": allow("rba.cash_rate_tri")})
    _assert_refused_and_nothing_written(local, gate, built["cash.aud.overnight"])


def test_f2_a_link_with_an_extra_dataset_refuses(world, tmp_path):
    store, *_rest, built = world

    def extra(link):
        link["datasets"]["third.dataset"] = ["something.else"]

    local = _rewrite_links(store, tmp_path, "extra", extra)
    gate = RightsGate({s: allow(s) for s in ("rba.cash_rate", "third.dataset")})
    _assert_refused_and_nothing_written(local, gate, built["cash.aud.overnight"])


def test_f2_a_duplicate_link_for_the_same_receipt_refuses(world, tmp_path):
    store, *_rest, built = world
    key = _links(store)[0]
    link = json.loads(store.get(key))
    later = parse_instant(link["captured_at"]) + timedelta(seconds=1)
    dup = link_record_key("rba.f1", later, link["receipt_id"])
    local = copy_store(store, tmp_path, "dup")
    local.put(dup, canonical_json({**link, "captured_at": later}))
    gate = RightsGate({s: allow(s) for s in ("rba.cash_rate", "rba.cash_rate_tri")})
    _assert_refused_and_nothing_written(local, gate, built["cash.aud.overnight"])


def test_f2_a_link_with_an_inconsistent_capture_instant_refuses(world, tmp_path):
    store, *_rest, built = world

    def shift(link):
        link["captured_at"] = "2000-01-01T00:00:00.000000Z"

    local = _rewrite_links(store, tmp_path, "instant", shift)
    gate = RightsGate({s: allow(s) for s in ("rba.cash_rate", "rba.cash_rate_tri")})
    _assert_refused_and_nothing_written(local, gate, built["cash.aud.overnight"])


def test_f2_a_link_on_a_single_dataset_receipt_refuses(world, tmp_path):
    store, *_rest, built = world
    sofr_capture = sorted(store.list("catalogue/captures/nyfed.sofr/"))[0]
    rec = json.loads(store.get(sofr_capture))
    at = parse_instant(rec["captured_at"])
    forged = {
        "publication_id": "nyfed.sofr",
        "receipt_id": rec["receipt_id"],
        "captured_at": at,
        "datasets": {"wrong.dataset": ["nyfed.sofr"]},
    }
    local = copy_store(store, tmp_path, "single")
    local.put(link_record_key("nyfed.sofr", at, rec["receipt_id"]), canonical_json(forged))
    gate = RightsGate({s: allow(s) for s in ("nyfed.sofr", "wrong.dataset")})
    release = built["cash.usd.overnight"]
    assert rec["receipt_id"] in {r for i in release.core["inputs"] for r in i.get("receipts", [])}
    _assert_refused_and_nothing_written(local, gate, release)


def test_f2_a_series_definition_naming_the_wrong_dataset_refuses_in_the_vintage_view(world):
    store, cals, _vs, cutoff, *_ = world
    vs = vintage_store(store, cals)
    vs.series[AONIA] = dataclasses.replace(vs.series[AONIA], dataset_id="rba.cash_rate_tri")
    with pytest.raises(ReceiptIntegrityError, match=r"assigns it to rba\.cash_rate"):
        vs.sources_of(vs.view(AONIA, MODE, cutoff, None))


def test_f2_an_adapter_that_drifts_from_the_fixed_mapping_refuses_at_construction():
    with pytest.raises(ValueError, match="fixed publication mapping"):
        Publication("rba.f1", (DATASETS["rba.cash_rate"],), PUBLICATIONS["rba.f1"].parse)
    with pytest.raises(ValueError, match="fixed publication mapping"):
        Publication(
            "nyfed.sofr", (DATASETS["nyfed.sofr"], DATASETS["nyfed.sofr_index"]), DATASETS["nyfed.sofr"].parse
        )


def test_the_fixed_mapping_is_immutable_and_matches_the_adapters():
    with pytest.raises(TypeError):
        SHARED_PUBLICATIONS["rba.f1"]["rba.cash_rate"] = ("x",)  # type: ignore[index]
    for pid, pub in PUBLICATIONS.items():
        assert pub.shared == (pid in SHARED_PUBLICATIONS)
        if pub.shared:
            assert pub.link() == link_datasets(pid)
