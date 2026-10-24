"""Rights gate: fail closed for every operation S1 performs, every permission state and
verification level, with refusal atomicity through the real code paths (S1-A12; rights
standard §3; OD-0020 item 3).

Synthetic rights live in tests/fixtures/synthetic/rights.yaml and in records built here. None of
them touches the genuine register, which these tests also prove unchanged and still blocking.
"""

import hashlib
import re
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from hio.contracts.rights import Operation, RightsRefused
from hio.contracts.status import Status
from hio.contracts.temporal import KnowledgeMode
from hio.jobs import s1a
from hio.marketdata.capture import SyntheticSource, capture
from hio.marketdata.vintages import VintageStore
from hio.publish.release import write_release
from hio.publish.status import append_status
from hio.rights.gate import GateContext, RightsGate, required_permissions
from hio.rights.model import ALL_PERMISSIONS, Permission, RightsRecord, Verification, propagate
from hio.rights.register import RegisterError, load_genuine, load_synthetic
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import FIXTURES

REPO = Path(__file__).resolve().parent.parent
GENUINE = REPO / "registers" / "sources.yaml"
GENUINE_SHA_AT_IMPORT = hashlib.sha256(GENUINE.read_bytes()).hexdigest()
WORLD = FIXTURES / "s1a_world"
CUTOFF = datetime(2026, 1, 29, tzinfo=UTC)
CODE = {"commit": "test", "lock_sha256": "test"}
SID = "synthetic.rba"


def record(sid=SID, verification=Verification.OWNER_VERIFIED, satisfied=None, **override) -> RightsRecord:
    perms = {p: Permission.parse("allow") for p in ALL_PERMISSIONS}
    for name, value in override.items():
        perms[name.replace("__", ".")] = Permission.parse(value)
    return RightsRecord(sid, verification, perms, satisfied or {})


def gate_with(rec: RightsRecord, external=False) -> RightsGate:
    allow = record("synthetic.nyfed")
    return RightsGate({rec.source_id: rec, allow.source_id: allow}, GateContext(on_external_host=external))


OPERATIONS = [
    Operation.FETCH,
    Operation.STORE_RAW,
    Operation.BUILD,
    Operation.STORE_DERIVED,
    Operation.REBUILD,
    Operation.PUBLISH,
]
REFUSING_STATES = ["deny", "unknown", "conditional(label modified content)"]


# --- the matrix ------------------------------------------------------------------------------------


@pytest.mark.parametrize("op", OPERATIONS)
@pytest.mark.parametrize("state", REFUSING_STATES)
def test_every_required_permission_in_a_refusing_state_refuses(op, state):
    for perm in required_permissions(op, GateContext(on_external_host=True), "hio_internal"):
        gate = gate_with(record(**{perm.replace(".", "__"): state}), external=True)
        with pytest.raises(RightsRefused, match=re.escape(perm)):
            gate.authorise(op, [SID], "hio_internal")


@pytest.mark.parametrize("op", OPERATIONS)
@pytest.mark.parametrize("verification", [Verification.UNVERIFIED, Verification.VENDOR_ASSERTED])
def test_insufficient_verification_refuses_even_when_everything_is_allowed(op, verification):
    with pytest.raises(RightsRefused, match=verification.value):
        gate_with(record(verification=verification)).authorise(op, [SID], "hio_internal")


@pytest.mark.parametrize("op", OPERATIONS)
@pytest.mark.parametrize("verification", [Verification.OWNER_VERIFIED, Verification.CONTRACT])
def test_allow_with_sufficient_verification_proceeds(op, verification):
    gate_with(record(verification=verification), external=True).authorise(op, [SID], "hio_internal")


def test_a_satisfied_condition_proceeds_and_an_unsatisfied_one_refuses():
    satisfied = record(derivation="conditional(label)", satisfied={"derivation": "evidence: label applied"})
    gate_with(satisfied).authorise(Operation.BUILD, [SID])
    with pytest.raises(RightsRefused, match="not recorded as satisfied"):
        gate_with(record(derivation="conditional(label)")).authorise(Operation.BUILD, [SID])


def test_external_processing_is_required_only_on_an_external_host():
    rec = record(external_processing="deny")
    gate_with(rec, external=False).authorise(Operation.BUILD, [SID])
    with pytest.raises(RightsRefused, match="external_processing"):
        gate_with(rec, external=True).authorise(Operation.BUILD, [SID])


def test_unknown_sources_and_empty_input_lists_refuse():
    with pytest.raises(RightsRefused, match="no rights record"):
        gate_with(record()).authorise(Operation.BUILD, ["synthetic.missing"])
    with pytest.raises(RightsRefused, match="no input sources"):
        gate_with(record()).authorise(Operation.BUILD, [])


def test_every_input_source_must_grant_every_permission():
    good, bad = record("synthetic.a"), record("synthetic.b", derivation="deny")
    gate = RightsGate({good.source_id: good, bad.source_id: bad})
    with pytest.raises(RightsRefused, match=re.escape("synthetic.b: derivation is deny")):
        gate.authorise(Operation.BUILD, ["synthetic.a", "synthetic.b"])


def test_publish_checks_the_consumer_class():
    with pytest.raises(RightsRefused, match=re.escape("distribution.smsf_app")):
        gate_with(record(distribution__smsf_app="deny")).authorise(Operation.PUBLISH, [SID], "smsf_app")


def test_propagation_is_most_restrictive_with_conditions_concatenated():
    a = record("synthetic.a", derivation="conditional(cite A)", derived_storage="deny")
    b = record(
        "synthetic.b", Verification.CONTRACT, derivation="conditional(cite B)", derived_storage="allow"
    )
    out = propagate([a, b])
    assert out["derivation"] == "conditional(cite A; cite B)"
    assert out["derived_storage"] == "deny"
    assert out["internal_compute"] == "allow"
    assert out["verification"] == "owner_verified"


def test_records_are_immutable():
    rec = record()
    with pytest.raises(TypeError):
        rec.permissions["derivation"] = Permission.parse("deny")


# --- atomicity through the real code paths -------------------------------------------------------------


@pytest.fixture
def world_store(tmp_path):
    """A store with captures and vintages built under fully allowed synthetic rights."""
    world = s1a.load_world(WORLD)
    rights = dict(load_synthetic(FIXTURES / "rights.yaml"))
    store = LocalObjectStore(tmp_path / "store")
    vs = VintageStore(store, world.series)
    s1a.run_captures(world, vs, RightsGate(rights), s1a.capture_instants(date(2026, 1, 5), CUTOFF))
    return world, rights, store, vs


def refusing_rights(rights, perm):
    return {**rights, SID: record(**{perm.replace(".", "__"): "deny"})}


def test_fetch_refusal_reads_and_writes_nothing(tmp_path):
    store = LocalObjectStore(tmp_path / "s")
    missing_file = SyntheticSource(SID, tmp_path / "never-read.csv")  # the gate fires before the read
    with pytest.raises(RightsRefused, match="automated_retrieval"):
        capture(missing_file, store, gate_with(record(automated_retrieval="unknown")), CUTOFF)
    with pytest.raises(RightsRefused, match="raw_retention"):
        capture(missing_file, store, gate_with(record(raw_retention="deny")), CUTOFF)
    assert store.snapshot() == {}


@pytest.mark.parametrize("perm", ["internal_compute", "derivation"])
def test_build_refusal_writes_nothing(world_store, perm):
    world, rights, store, vs = world_store
    before = store.snapshot()
    gate = RightsGate(refusing_rights(rights, perm))
    with pytest.raises(RightsRefused, match=re.escape(perm)):
        s1a.build_releases(world, vs, gate, rights, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE)
    assert store.snapshot() == before


def test_store_derived_refusal_writes_nothing(world_store):
    world, rights, store, vs = world_store
    releases = s1a.build_releases(
        world, vs, RightsGate(rights), rights, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE
    )
    # The cash releases are stored first (the FX releases cite them as upstream lineage).
    for d in ("cash.aud.overnight", "cash.usd.overnight"):
        write_release(store, RightsGate(rights), releases[d])
    before = store.snapshot()
    gate = RightsGate(refusing_rights(rights, "derived_storage"))  # refuses synthetic.rba only
    # Sources come from each release's lineage (F-REVIEW-2026-10-24-s1a-1-1): every release that
    # depends on synthetic.rba is refused; the USD cash leg depends only on synthetic.nyfed.
    for d in ("cash.aud.overnight", "fx.usd_cash_vs_aud.excess", "fx.usd_cash_vs_aud.decomposition"):
        with pytest.raises(RightsRefused, match=re.escape("synthetic.rba: derived_storage")):
            write_release(store, gate, releases[d])
    assert write_release(store, gate, releases["cash.usd.overnight"]) is False  # allowed; already stored
    assert store.snapshot() == before


@pytest.mark.parametrize("perm", ["internal_compute", "derivation", "derived_storage", "raw_retention"])
def test_rebuild_refusal_writes_nothing(world_store, perm):
    world, rights, store, _ = world_store
    before = store.snapshot()
    gate = RightsGate(refusing_rights(rights, perm))
    with pytest.raises(RightsRefused, match=re.escape(perm)):
        s1a.rebuild_check(world, store, gate, rights, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE)
    assert store.snapshot() == before


def test_publish_refusal_writes_no_status_event(world_store):
    world, rights, store, vs = world_store
    gate = RightsGate(rights)
    releases = s1a.build_releases(world, vs, gate, rights, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE)
    s1a.publish_releases(vs, gate, releases, CUTOFF)
    sha = releases["cash.aud.overnight"].content_sha256
    before = store.snapshot()
    refusing = RightsGate(refusing_rights(rights, "distribution.hio_internal"))
    with pytest.raises(RightsRefused, match=re.escape("distribution.hio_internal")):
        append_status(
            store,
            sha,
            Status.APPROVED_FOR_CONSUMER,
            "owner",
            "fixture",
            CUTOFF,
            gate=refusing,
            consumer_class="hio_internal",
        )
    assert store.snapshot() == before
    append_status(
        store,
        sha,
        Status.APPROVED_FOR_CONSUMER,
        "owner",
        "fixture",
        CUTOFF,
        gate=gate,
        consumer_class="hio_internal",
    )


# --- the genuine register: read-only, still blocking -----------------------------------------------------


def test_genuine_s1_sources_are_still_refused_for_every_operation():
    gate = RightsGate(load_genuine(GENUINE))
    for sid in ("rba_statistical_tables", "nyfed_reference_rates", "us_treasury_rates", "frb_h10"):
        for op in OPERATIONS:
            with pytest.raises(RightsRefused, match="verification is unverified"):
                gate.authorise(op, [sid], "hio_internal")


def test_synthetic_and_genuine_registers_cannot_be_mixed(tmp_path):
    with pytest.raises(RegisterError, match="synthetic source"):
        bad = tmp_path / "sources.yaml"
        bad.write_text("sources:\n  - {id: synthetic.x, verification: owner_verified}\n")
        load_genuine(bad)
    fixture_dir = tmp_path / "synthetic"
    fixture_dir.mkdir()
    genuine_id = fixture_dir / "rights.yaml"
    genuine_id.write_text(
        "# SYNTHETIC\nsources:\n  - {id: rba_statistical_tables, verification: owner_verified}\n"
    )
    with pytest.raises(RegisterError, match=re.escape("must start with 'synthetic.'")):
        load_synthetic(genuine_id)
    outside = tmp_path / "rights.yaml"
    outside.write_text("# SYNTHETIC\nsources: []\n")
    with pytest.raises(RegisterError, match="'synthetic' fixtures directory"):
        load_synthetic(outside)


@pytest.mark.usefixtures("world_store")
def test_the_genuine_register_is_byte_identical_after_the_rights_tests():
    """Runs after the synthetic owner_verified fixtures have been loaded and exercised."""
    assert hashlib.sha256(GENUINE.read_bytes()).hexdigest() == GENUINE_SHA_AT_IMPORT
