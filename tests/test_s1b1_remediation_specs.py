"""Adversarial regressions for F-REVIEW-2026-10-25-t0009-4 (OD-0067): S1b-1.0 releases cite a spec
version that describes their actual inputs, calendars and in-arrears accrual, while the accepted S1a
releases keep citing 0.2.0 with byte-identical identities."""

from __future__ import annotations

import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from hio.contracts.canonical import sha256_hex
from hio.contracts.temporal import KnowledgeMode
from hio.jobs import s1a
from hio.jobs.s1b1 import S1B_SPECS
from hio.marketdata.vintages import VintageStore
from hio.rights.gate import RightsGate
from hio.rights.register import load_synthetic
from hio.storage.objectstore import LocalObjectStore
from tests.test_s1b1_releases import world  # noqa: F401  (world is a fixture)

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "synthetic"

# Content hashes of the S1a releases (code_ref fixed as below), computed at the reviewed head ce0c3b5
# and unchanged by the remediation: the whole release identity, not only data.csv.
S1A_CONTENT_SHA256 = {
    "cash.aud.overnight": "70493c9a32f25b745b2514c49531d514c0a72131173821457440b32e86aa3231",
    "cash.usd.overnight": "6d03ba315caa5afadbdcc5100b4a6d9aa0043b423213224fd1643eb253a7bdfd",
    "fx.usd_cash_vs_aud.decomposition": "5588fc4e355ccb7fd885083648bc48bc35aae038306392344499e931aff9c766",
    "fx.usd_cash_vs_aud.excess": "7e7aa4af7d043c5c2eaeaac3d7847260d096c666721def74a33da25188e1f974",
}
# sha256 of specs/factors/cash.*.overnight.yaml at ce0c3b5 (version 0.2.0), kept in archive/.
SPEC_0_2_0_SHA256 = {
    "cash.aud.overnight": "8baeb4bc0b4ae444f1cf51348059537b33b7e34e4af00508eb7666b2376abeff",
    "cash.usd.overnight": "f6a33fba7238befa258b77cdb068004b66d3b2a69bc72601e5c9c046935682b5",
}


def test_f4_s1a_release_identities_are_unchanged_and_cite_0_2_0():
    world_ = s1a.load_world(FIXTURES / "s1a_world")
    rights = dict(load_synthetic(FIXTURES / "rights.yaml"))
    cutoff = datetime(2026, 1, 29, tzinfo=UTC)
    vs = VintageStore(LocalObjectStore(Path(tempfile.mkdtemp()) / "s"), world_.series)
    gate = RightsGate(rights)
    s1a.run_captures(world_, vs, gate, s1a.capture_instants(date(2026, 1, 5), cutoff))
    built = s1a.build_releases(
        world_,
        vs,
        gate,
        rights,
        KnowledgeMode.AS_CAPTURED_BY_HIO,
        cutoff,
        {"commit": "0" * 40, "lock_sha256": "1" * 64},
    )
    assert {k: r.content_sha256 for k, r in built.items()} == S1A_CONTENT_SHA256
    assert {r.core["spec_ref"].split("@")[1] for r in built.values()} == {"0.2.0"}


@pytest.mark.parametrize("factor_id", sorted(SPEC_0_2_0_SHA256))
def test_f4_the_cited_0_2_0_spec_is_preserved_byte_for_byte(factor_id):
    path = REPO / "specs" / "factors" / "archive" / f"{factor_id}@0.2.0.yaml"
    assert sha256_hex(path.read_bytes()) == SPEC_0_2_0_SHA256[factor_id]
    assert s1a.spec_document(factor_id, "0.2.0")["identity"]["version"] == "0.2.0"


def test_f4_every_s1b_release_cites_0_3_0(world):
    for release in world[6].values():
        factor_id, version = release.core["spec_ref"].split("@")
        assert version == S1B_SPECS[factor_id] == "0.3.0"
        assert s1a.spec_document(factor_id, version)["identity"]["version"] == "0.3.0"


def test_f4_the_0_3_0_specs_describe_the_actual_inputs_calendars_and_regime(world):
    aud = s1a.spec_document("cash.aud.overnight", "0.3.0")
    usd = s1a.spec_document("cash.usd.overnight", "0.3.0")
    release_series = {
        f["dataset_id"]: {i["series_id"] for i in f["inputs"] if "series_id" in i}
        for f in (r.core for r in world[6].values())
    }
    assert {o["series_id"] for o in aud["observations"]} == release_series["cash.aud.overnight"]
    assert {o["series_id"] for o in usd["observations"]} == release_series["cash.usd.overnight"]
    assert [o["source_id"] for o in aud["observations"]] == ["rba.cash_rate"]
    assert [o["source_id"] for o in usd["observations"]] == ["nyfed.sofr"]
    for spec in (aud, usd):
        assert spec["construction"]["regime"] == "in_arrears"
        assert "schedule_only" in spec["availability"]["knowable_rule"]
    assert "RITS" in aud["construction"]["calendar"] and "RITS" in aud["construction"]["algorithm"]
    assert "NSW" in usd["construction"]["calendar"] and "SIFMA" in usd["construction"]["calendar"]


def test_f4_an_uncited_version_refuses():
    with pytest.raises(LookupError):
        s1a.spec_ref("cash.aud.overnight", "0.2.1")
    with pytest.raises(LookupError):
        s1a.spec_document("cash.usd.overnight", "9.9.9")
