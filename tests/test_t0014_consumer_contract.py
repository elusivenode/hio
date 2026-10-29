"""T-0014 P-4: the minimal consumer contract (base-camp criterion 6), on synthetic data only.

A pinned consumer goes through `hio.publish.status.resolve_for_use` and, at every use, gets the exact
dataset and hash pin, canonical integrity, complete lineage, and the CURRENT status and rights. These
tests are the refusals plus the success. A success returns the verified manifest core: it records no
event and never manufactures an approval. No API, mandate schema, SMSF projection or distribution
semantics is tested because none is built."""

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from hio.contracts.layout import CAPTURES_PREFIX
from hio.contracts.rights import RightsRefused
from hio.contracts.status import Status
from hio.contracts.temporal import KnowledgeMode
from hio.jobs import s1a
from hio.marketdata.vintages import VintageStore
from hio.publish.lineage import LineageError
from hio.publish.status import RefusedUse, append_status, events, resolve_for_use
from hio.rights.gate import RightsGate
from hio.rights.model import ALL_PERMISSIONS, Permission, RightsRecord, Verification
from hio.rights.register import load_synthetic
from hio.storage.objectstore import IntegrityError, LocalObjectStore
from tests.helpers import FIXTURES

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "infra" / "workflows" / "consumer-contract.yml"

RIGHTS = dict(load_synthetic(FIXTURES / "rights.yaml"))
CUTOFF = datetime(2026, 1, 29, tzinfo=UTC)
CODE = {"commit": "0" * 40, "lock_sha256": "1" * 64}
AUD = "cash.aud.overnight"
USD = "cash.usd.overnight"
CLASS = "hio_internal"


def build(tmp_path):
    world = s1a.load_world(FIXTURES / "s1a_world")
    store = LocalObjectStore(tmp_path / "store")
    vs = VintageStore(store, world.series)
    gate = RightsGate(RIGHTS)
    s1a.run_captures(world, vs, gate, s1a.capture_instants(date(2026, 1, 5), CUTOFF))
    releases = s1a.build_releases(world, vs, gate, RIGHTS, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE)
    s1a.publish_releases(vs, gate, releases, CUTOFF)
    return store, releases


def use(store, dataset_id, sha, *, required=Status.EXPLORATORY, consumer_class=CLASS, gate=None):
    return resolve_for_use(
        store,
        dataset_id,
        sha,
        required=required,
        consumer_class=consumer_class,
        gate=gate or RightsGate(RIGHTS),
    )


def rights_with(**overrides):
    """A gate over one record for the synthetic source, every permission allowed except `overrides`
    (a permission name -> its value, where None means not stated as anything: unknown)."""
    perms = {p: Permission.parse("allow") for p in ALL_PERMISSIONS}
    perms |= {k.replace("__", "."): Permission.parse(v) for k, v in overrides.items()}
    return RightsGate({"synthetic.rba": RightsRecord("synthetic.rba", Verification.OWNER_VERIFIED, perms)})


def unlink(store, key):
    path = store.root / key
    path.chmod(0o644)
    path.unlink()


def overwrite(store, key, old, new):
    path = store.root / key
    path.chmod(0o644)
    assert old in path.read_bytes()
    path.write_bytes(path.read_bytes().replace(old, new, 1))


# --- a success returns the verified core and approves nothing ----------------------------------------


def test_a_pinned_use_returns_the_verified_core_and_records_nothing(tmp_path):
    store, releases = build(tmp_path)
    r = releases[AUD]
    before = events(store, r.content_sha256)
    core = use(store, AUD, r.content_sha256)
    assert core == r.core
    assert events(store, r.content_sha256) == before
    assert all(e.status is not Status.APPROVED_FOR_CONSUMER for e in events(store, r.content_sha256))


def test_exploratory_status_never_satisfies_a_requirement_of_approval(tmp_path):
    store, releases = build(tmp_path)
    sha = releases[AUD].content_sha256
    with pytest.raises(RefusedUse, match="not approved for hio_internal"):
        use(store, AUD, sha, required=Status.APPROVED_FOR_CONSUMER)
    assert not any(e.status is Status.APPROVED_FOR_CONSUMER for e in events(store, sha))  # none written


def test_approval_is_scoped_to_the_consumer_class_it_names(tmp_path):
    store, releases = build(tmp_path)
    sha = releases[AUD].content_sha256
    gate = RightsGate(RIGHTS)
    append_status(
        store,
        sha,
        Status.APPROVED_FOR_CONSUMER,
        "owner",
        "synthetic",
        CUTOFF,
        gate=gate,
        consumer_class=CLASS,
    )
    use(store, AUD, sha, required=Status.APPROVED_FOR_CONSUMER)
    with pytest.raises(RefusedUse, match="not approved for smsf_app"):
        use(store, AUD, sha, required=Status.APPROVED_FOR_CONSUMER, consumer_class="smsf_app")


# --- the exact pin ------------------------------------------------------------------------------------


def test_a_hash_that_belongs_to_another_dataset_is_refused(tmp_path):
    store, releases = build(tmp_path)
    with pytest.raises(RefusedUse, match="belongs to"):
        use(store, USD, releases[AUD].content_sha256)


def test_an_unknown_hash_is_refused(tmp_path):
    store, _ = build(tmp_path)
    with pytest.raises(LineageError, match="found 0"):
        use(store, AUD, "f" * 64)


# --- canonical integrity ------------------------------------------------------------------------------


def test_tampered_payload_bytes_are_refused(tmp_path):
    store, releases = build(tmp_path)
    r = releases[USD]
    overwrite(store, f"{r.prefix}/data.csv", b"4.3", b"4.4")
    with pytest.raises((LineageError, IntegrityError)):
        use(store, USD, r.content_sha256)


def test_a_tampered_manifest_is_refused(tmp_path):
    store, releases = build(tmp_path)
    r = releases[AUD]
    key = f"{r.prefix}/manifest.json"
    overwrite(store, key, b"cash.aud.overnight", b"cash.aud.overnighT")
    with pytest.raises((LineageError, IntegrityError)):
        use(store, AUD, r.content_sha256)


def test_a_missing_payload_is_refused(tmp_path):
    store, releases = build(tmp_path)
    r = releases[AUD]
    unlink(store, f"{r.prefix}/data.csv")
    with pytest.raises((LineageError, IntegrityError, OSError)):
        use(store, AUD, r.content_sha256)


# --- complete lineage ---------------------------------------------------------------------------------


def test_a_missing_capture_record_breaks_lineage_and_is_refused(tmp_path):
    store, releases = build(tmp_path)
    r = releases[AUD]
    for key in store.list(CAPTURES_PREFIX):
        unlink(store, key)
    with pytest.raises(LineageError, match="no capture record"):
        use(store, AUD, r.content_sha256)


def test_a_corrupt_receipt_breaks_lineage_and_is_refused(tmp_path):
    store, releases = build(tmp_path)
    r = releases[AUD]
    receipt_id = next(item["receipts"][0] for item in r.core["inputs"] if "receipts" in item)
    unlink(store, next(k for k in store.list("receipts/") if k.endswith(receipt_id)))
    with pytest.raises(LineageError):
        use(store, AUD, r.content_sha256)


def test_a_missing_upstream_release_breaks_lineage_and_is_refused(tmp_path):
    store, releases = build(tmp_path)
    excess = releases["fx.usd_cash_vs_aud.excess"]
    assert any("upstream" in item for item in excess.core["inputs"])  # the premise of this case
    unlink(store, f"{releases[AUD].prefix}/manifest.json")
    with pytest.raises(LineageError):
        use(store, "fx.usd_cash_vs_aud.excess", excess.content_sha256)


# --- current status on every use ----------------------------------------------------------------------


def test_a_release_with_no_status_is_refused(tmp_path):
    store, releases = build(tmp_path)
    sha = releases[AUD].content_sha256
    for key in store.list(f"catalogue/status/{sha}/"):
        unlink(store, key)
    with pytest.raises(RefusedUse, match="no status"):
        use(store, AUD, sha)


def test_withdrawal_after_a_successful_use_is_refused_on_the_next(tmp_path):
    store, releases = build(tmp_path)
    sha = releases[AUD].content_sha256
    use(store, AUD, sha)
    append_status(store, sha, Status.WITHDRAWN, "owner", "synthetic", CUTOFF)
    with pytest.raises(RefusedUse, match="withdrawn globally"):
        use(store, AUD, sha)


def test_withdrawal_for_one_class_leaves_others_usable_and_refuses_that_one(tmp_path):
    store, releases = build(tmp_path)
    sha = releases[AUD].content_sha256
    append_status(store, sha, Status.WITHDRAWN, "owner", "synthetic", CUTOFF, consumer_class="smsf_app")
    use(store, AUD, sha)
    with pytest.raises(RefusedUse, match="withdrawn for smsf_app"):
        use(store, AUD, sha, consumer_class="smsf_app")


def test_a_status_below_the_requirement_is_refused(tmp_path):
    store, releases = build(tmp_path)
    with pytest.raises(RefusedUse, match="below validated"):
        use(store, AUD, releases[AUD].content_sha256, required=Status.VALIDATED)


# --- current rights on every use ----------------------------------------------------------------------


def test_revoked_permission_is_refused_though_the_manifest_snapshot_allows(tmp_path):
    store, releases = build(tmp_path)
    r = releases[AUD]
    assert r.core["rights"]["distribution.hio_internal"] == "allow"
    use(store, AUD, r.content_sha256)
    with pytest.raises(RightsRefused, match="deny"):
        use(store, AUD, r.content_sha256, gate=rights_with(distribution__hio_internal="deny"))


def test_an_unstated_permission_is_unknown_and_means_deny(tmp_path):
    store, releases = build(tmp_path)
    perms = {
        p: Permission.parse(None) if p == "distribution.hio_internal" else Permission.parse("allow")
        for p in ALL_PERMISSIONS
    }
    gate = RightsGate({"synthetic.rba": RightsRecord("synthetic.rba", Verification.OWNER_VERIFIED, perms)})
    with pytest.raises(RightsRefused, match="unknown"):
        use(store, AUD, releases[AUD].content_sha256, gate=gate)


def test_a_conditional_permission_that_is_not_recorded_as_satisfied_is_refused(tmp_path):
    store, releases = build(tmp_path)
    gate = rights_with(distribution__hio_internal="conditional(owner confirms)")
    with pytest.raises(RightsRefused, match="not recorded as satisfied"):
        use(store, AUD, releases[AUD].content_sha256, gate=gate)


def test_a_source_with_no_rights_record_is_refused(tmp_path):
    store, releases = build(tmp_path)
    with pytest.raises(RightsRefused, match="no rights record"):
        use(store, AUD, releases[AUD].content_sha256, gate=RightsGate({}))


def test_insufficient_verification_is_refused_even_when_every_permission_allows(tmp_path):
    store, releases = build(tmp_path)
    perms = {p: Permission.parse("allow") for p in ALL_PERMISSIONS}
    gate = RightsGate({"synthetic.rba": RightsRecord("synthetic.rba", Verification.VENDOR_ASSERTED, perms)})
    with pytest.raises(RightsRefused, match="verification is vendor_asserted"):
        use(store, AUD, releases[AUD].content_sha256, gate=gate)


def test_rights_are_checked_for_the_consumer_class_asked_for(tmp_path):
    store, releases = build(tmp_path)
    sha = releases[AUD].content_sha256
    gate = rights_with(distribution__smsf_app="deny")
    use(store, AUD, sha, gate=gate)
    with pytest.raises(RightsRefused, match=r"distribution\.smsf_app"):
        use(store, AUD, sha, gate=gate, consumer_class="smsf_app")


# --- the inactive CI job template ---------------------------------------------------------------------


def template_text():
    return TEMPLATE.read_text()


def test_the_template_lives_outside_the_workflows_directory_and_nothing_runs_it():
    assert TEMPLATE.is_file()
    assert not (REPO / ".github" / "workflows" / TEMPLATE.name).exists()
    assert "NOT ENABLED" in template_text().splitlines()[0]


def test_the_template_is_manual_only_read_only_and_holds_no_secret():
    text = template_text()
    lines = [ln.strip() for ln in text.splitlines() if not ln.strip().startswith("#")]
    assert "workflow_dispatch:" in lines
    assert "schedule:" not in lines
    assert "push:" not in lines
    assert "pull_request:" not in lines
    assert "secrets." not in text
    assert "id-token: write" not in text
    assert "contents: read" in lines
    assert "vars." in text  # the pin and the access settings come from Environment variables, never literals
