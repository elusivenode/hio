"""T-0010 release notices (OD-0118 decision 3): every S1b-1 release carries, inside the manifest core's
quality_summary, the notices its input datasets owe, as exact strings. The expected strings are written
out here on purpose: they are the wording the owner adopted, not a restatement of the module constants."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from hio.contracts.canonical import sha256_hex
from hio.contracts.temporal import KnowledgeMode
from hio.jobs import s1a, s1b1
from hio.marketdata.vintages import VintageStore
from hio.rights.gate import RightsGate
from hio.rights.register import load_synthetic
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import FIXTURES, AllowAllGate
from tests.test_f4_f7_acceptance import S1A_DATA_SHA256
from tests.test_s1b1_releases import build_world

RBA_SOURCE = "Source: Reserve Bank of Australia 2026"
RBA_NO_ENDORSE = (
    "The Reserve Bank of Australia does not endorse HIO or this derived series; "
    "HIO internal research use only."
)
NY_NO_ENDORSE = "The Federal Reserve Bank of New York does not endorse HIO or this derived data."
NY_DTCC = (
    "SOFR is calculated using data provided under a license granted to the New York Fed by "
    "DTCC Solutions LLC; DTCC Solutions LLC and its sources have no liability for its use."
)
NY_DERIVED_SOFR = (
    "HIO derivation cash.usd.overnight@0.3.0: not the SOFR "
    "as published by the Federal Reserve Bank of New York."
)
NY_DERIVED_INDEX = (
    "HIO derivation cash.usd.overnight@0.3.0: not the SOFR Index "
    "as published by the Federal Reserve Bank of New York."
)

EXPECTED = {
    "cash.aud.overnight": [RBA_SOURCE, RBA_NO_ENDORSE],
    "cash.aud.overnight.vs_tri": [RBA_SOURCE, RBA_NO_ENDORSE],
    "cash.usd.overnight": [NY_DERIVED_SOFR, NY_DTCC, NY_NO_ENDORSE],
    "cash.usd.overnight.vs_sofr_index": [NY_DERIVED_SOFR, NY_DERIVED_INDEX, NY_DTCC, NY_NO_ENDORSE],
}


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return build_world(LocalObjectStore(tmp_path_factory.mktemp("n") / "store"))


def test_every_release_carries_exactly_the_notices_its_inputs_owe(world):
    releases = world[6]
    assert set(releases) == set(EXPECTED)
    for dataset_id, release in releases.items():
        assert release.core["quality_summary"]["notices"] == sorted(EXPECTED[dataset_id]), dataset_id


def test_notices_are_sorted_and_free_of_duplicates(world):
    for release in world[6].values():
        notices = release.core["quality_summary"]["notices"]
        assert notices == sorted(notices) and len(notices) == len(set(notices))


def test_a_comparison_carries_the_union_of_its_inputs_notices(world):
    releases = world[6]
    for cmp_id, cash_id in (
        ("cash.aud.overnight.vs_tri", "cash.aud.overnight"),
        ("cash.usd.overnight.vs_sofr_index", "cash.usd.overnight"),
    ):
        cash = set(releases[cash_id].core["quality_summary"]["notices"])
        cmp = set(releases[cmp_id].core["quality_summary"]["notices"])
        assert cash <= cmp


def test_no_notice_for_a_publisher_the_release_does_not_use(world):
    for dataset_id in ("cash.aud.overnight", "cash.aud.overnight.vs_tri"):
        text = " ".join(world[6][dataset_id].core["quality_summary"]["notices"])
        assert "New York" not in text and "DTCC" not in text
    for dataset_id in ("cash.usd.overnight", "cash.usd.overnight.vs_sofr_index"):
        text = " ".join(world[6][dataset_id].core["quality_summary"]["notices"])
        assert "Reserve Bank of Australia" not in text


def test_the_manifest_gains_no_top_level_field_and_keeps_limitations(world):
    for release in world[6].values():
        assert "notices" not in release.core
        assert "limitations" in release.core["quality_summary"]


def test_the_rba_year_is_the_year_of_the_knowledge_cutoff(world):
    _store, _cals, vs, _cutoff, rights, code, _ = world
    cals = world[1]
    later = datetime(2027, 1, 2, tzinfo=UTC)
    rebuilt = s1b1.build_releases(vs, AllowAllGate(), rights, cals, later, code, ["cash.aud.overnight"])
    notices = rebuilt["cash.aud.overnight"].core["quality_summary"]["notices"]
    assert "Source: Reserve Bank of Australia 2027" in notices and RBA_SOURCE not in notices


def test_notices_are_inside_the_content_hash(world, monkeypatch):
    _store, cals, vs, cutoff, rights, code, releases = world
    monkeypatch.setattr(s1b1, "NYFED_NO_ENDORSEMENT_NOTICE", NY_NO_ENDORSE + " (changed)")
    monkeypatch.setattr(s1b1, "RBA_NO_ENDORSEMENT_NOTICE", RBA_NO_ENDORSE + " (changed)")
    changed = s1b1.build_releases(vs, AllowAllGate(), rights, cals, cutoff, code)
    assert set(changed) == set(releases)
    for dataset_id, release in releases.items():
        assert changed[dataset_id].content_sha256 != release.content_sha256, dataset_id
        assert changed[dataset_id].files == release.files  # only the notice moved


def test_two_builds_are_identical(world):
    _store, cals, vs, cutoff, rights, code, releases = world
    again = s1b1.build_releases(vs, AllowAllGate(), rights, cals, cutoff, code)
    for dataset_id, release in releases.items():
        assert again[dataset_id].content_sha256 == release.content_sha256
        assert again[dataset_id].core == release.core


def test_s1a_outputs_and_their_data_hashes_are_unchanged_and_carry_no_notices(tmp_path):
    synthetic = load_synthetic(FIXTURES / "rights.yaml")
    rights = dict(synthetic)
    cutoff = datetime(2026, 1, 29, tzinfo=UTC)
    world = s1a.load_world(FIXTURES / "s1a_world")
    vs = VintageStore(LocalObjectStore(tmp_path / "s"), world.series)
    gate = RightsGate(rights)
    s1a.run_captures(world, vs, gate, s1a.capture_instants(date(2026, 1, 5), cutoff))
    releases = s1a.build_releases(
        world,
        vs,
        gate,
        rights,
        KnowledgeMode.AS_CAPTURED_BY_HIO,
        cutoff,
        {"commit": "0" * 40, "lock_sha256": "1" * 64},
    )
    assert {d: sha256_hex(r.files["data.csv"]) for d, r in releases.items()} == S1A_DATA_SHA256
    assert all("notices" not in r.core["quality_summary"] for r in releases.values())
