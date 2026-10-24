"""End-to-end synthetic pipeline: releases, reproducibility, status, consumers, catalogue index
(S1-A9, S1-A11, releases standard §6.1; information availability through real views)."""

import json
from datetime import UTC, date, datetime

import pytest

from hio.contracts.manifest import content_sha256
from hio.contracts.rights import RightsRefused
from hio.contracts.status import Status
from hio.contracts.temporal import KnowledgeMode
from hio.jobs import s1a
from hio.marketdata.queries import InadmissibleForPredictivePointInTime
from hio.marketdata.vintages import VintageStore
from hio.publish.release import verify_release, write_release
from hio.publish.status import RefusedUse, append_status, resolve_for_use
from hio.rights.gate import RightsGate
from hio.rights.model import ALL_PERMISSIONS, Permission, RightsRecord, Verification
from hio.rights.register import load_synthetic
from hio.storage.catalogue_index import dump, rebuild_index
from hio.storage.objectstore import IntegrityError, LocalObjectStore
from tests.helpers import FIXTURES

WORLD = FIXTURES / "s1a_world"
RIGHTS = dict(load_synthetic(FIXTURES / "rights.yaml"))
CUTOFF = datetime(2026, 1, 29, tzinfo=UTC)
CODE = {"commit": "0" * 40, "lock_sha256": "1" * 64}
DATASETS = {
    "cash.aud.overnight",
    "cash.usd.overnight",
    "fx.usd_cash_vs_aud.excess",
    "fx.usd_cash_vs_aud.decomposition",
}


def run(
    tmp_path,
    name,
    cutoff=CUTOFF,
    mode=KnowledgeMode.AS_CAPTURED_BY_HIO,
    published_at=CUTOFF,
    quality_as_of=None,
):
    world = s1a.load_world(WORLD)
    store = LocalObjectStore(tmp_path / name)
    vs = VintageStore(store, world.series)
    gate = RightsGate(RIGHTS)
    s1a.run_captures(world, vs, gate, s1a.capture_instants(date(2026, 1, 5), cutoff))
    releases = s1a.build_releases(world, vs, gate, RIGHTS, mode, cutoff, CODE, quality_as_of)
    s1a.publish_releases(vs, gate, releases, published_at)
    return world, store, vs, releases


def rows(store, release):
    return list(csv_rows(store.get(f"{release.prefix}/data.csv")))


def csv_rows(data: bytes):
    lines = data.decode().splitlines()
    header = lines[0].split(",")
    for line in lines[1:]:
        yield dict(zip(header, line.split(","), strict=True))


# --- S1-A9 and the release contents ---------------------------------------------------------------


def test_four_releases_including_the_decomposition_companion(tmp_path):
    _, store, _, releases = run(tmp_path, "a")
    assert set(releases) == DATASETS
    for r in releases.values():
        core = verify_release(store, r.core["dataset_id"], r.content_sha256)
        assert core["knowledge_mode"] == "as_captured_by_hio"
        assert core["quality_summary"]["absent_periods"] == []
    excess = {
        (r["period_start"], r["period_end"]): r for r in rows(store, releases["fx.usd_cash_vs_aud.excess"])
    }
    decomposition = rows(store, releases["fx.usd_cash_vs_aud.decomposition"])
    assert {(r["period_start"], r["period_end"]) for r in decomposition} == set(excess)


def test_ny_holiday_period_accrues_fridays_rate_and_is_knowable_on_tuesday(tmp_path):
    _, store, _, releases = run(tmp_path, "a")
    usd = {(r["period_start"], r["period_end"]): r for r in rows(store, releases["cash.usd.overnight"])}
    fri_mon = usd[("2026-01-16", "2026-01-19")]
    assert fri_mon["legs"] == "2026-01-16:4.41:3"
    assert fri_mon["knowable_at"] == "2026-01-20T13:00:00.000000Z"  # Monday is a NY holiday
    assert usd[("2026-01-19", "2026-01-20")]["legs"] == "2026-01-16:4.41:1"


# --- information availability through real views ----------------------------------------------------


def test_fx_period_waits_for_the_in_arrears_usd_leg_under_market_knowledge(tmp_path):
    """Monday's Sydney fixing is public at 06:00Z; Friday's SOFR only at 13:00Z (Monday, NY).

    Changed by OBS-AMEND-Q001 and VERIFY-2026-10-24-s1a-1-6 (OD-0031). This test built
    point-in-time market releases at 12:00Z and 13:00Z with Q at the store's cutoff (HIO's later
    captures), and expected a recorded gap at 12:00Z and the period at 13:00Z. A Q > T market
    release is not admissible and is now refused before anything is built. The knowability
    placement is asserted on views (labelled, not admissible); the releases use Q = T."""
    world, _, vs, _ = run(tmp_path, "a")
    gate = RightsGate(RIGHTS)
    monday = lambda h: datetime(2026, 1, 12, h, tzinfo=UTC)  # noqa: E731
    with pytest.raises(InadmissibleForPredictivePointInTime):
        s1a.build_releases(
            world, vs, gate, RIGHTS, KnowledgeMode.AS_KNOWN_BY_MARKET, monday(13), CODE, CUTOFF
        )
    # Knowability placement, judged with HIO's later captures (views only).
    friday = date(2026, 1, 9)
    sofr_12 = vs.as_known_by_market(s1a.SOFR, monday(12), CUTOFF)
    assert friday not in sofr_12.values and not sofr_12.predictive_pit_admissible
    assert friday in vs.as_known_by_market(s1a.SOFR, monday(13), CUTOFF).values
    # The AUD leg of the Fri→Mon period needs only Friday's rate, already knowable by then.
    assert friday in vs.as_known_by_market(s1a.CASH_RATE, monday(12), CUTOFF).values
    # Admissible releases (Q = T): the period appears once HIO has captured its inputs (14:00Z).
    at = lambda h: s1a.build_releases(  # noqa: E731
        world, vs, gate, RIGHTS, KnowledgeMode.AS_KNOWN_BY_MARKET, monday(h), CODE, monday(h)
    )
    periods = lambda r: {(x["period_start"], x["period_end"]) for x in csv_rows(r.files["data.csv"])}  # noqa: E731
    assert ("2026-01-09", "2026-01-12") not in periods(at(12)["fx.usd_cash_vs_aud.excess"])
    assert ("2026-01-09", "2026-01-12") in periods(at(14)["fx.usd_cash_vs_aud.excess"])
    assert ("2026-01-09", "2026-01-12") in periods(at(14)["cash.aud.overnight"])


def test_as_known_by_market_matches_as_captured_for_on_schedule_captures(tmp_path):
    """Every vintage was captured on schedule, so both point-in-time modes hold the same values;
    the releases differ only in the mode recorded in the manifest."""
    _, _, _, captured = run(tmp_path, "c")
    _, _, _, known = run(tmp_path, "k", mode=KnowledgeMode.AS_KNOWN_BY_MARKET, quality_as_of=CUTOFF)
    for d in DATASETS:
        assert captured[d].files == known[d].files
        assert captured[d].content_sha256 != known[d].content_sha256


# --- S1-A11 and releases §6.1 ----------------------------------------------------------------------


def test_fixture_1_determinism_across_independent_stores_and_run_times(tmp_path):
    _, store_a, _, a = run(tmp_path, "a", published_at=datetime(2026, 2, 1, tzinfo=UTC))
    _, store_b, _, b = run(tmp_path, "b", published_at=datetime(2026, 3, 1, tzinfo=UTC))
    assert {d: r.content_sha256 for d, r in a.items()} == {d: r.content_sha256 for d, r in b.items()}
    s1a.write_run_record(store_a, "t", CUTOFF, CUTOFF, CODE, {}, "ok")
    s1a.write_run_record(store_b, "t", CUTOFF, CUTOFF, CODE, {}, "ok")
    runs = lambda s: [k for k in s.list("catalogue/runs/")]  # noqa: E731
    assert runs(store_a) != runs(store_b)  # only the run records differ


def test_rebuild_from_stored_receipts_reproduces_every_release(tmp_path):
    world, store, _, _ = run(tmp_path, "a")
    before = store.snapshot()
    result = s1a.rebuild_check(
        world, store, RightsGate(RIGHTS), RIGHTS, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE
    )
    assert result == dict.fromkeys(sorted(DATASETS), True)
    assert store.snapshot() == before
    # A second write of an identical release is a no-op.
    for r in s1a.build_releases(
        world,
        VintageStore(store, world.series),
        RightsGate(RIGHTS),
        RIGHTS,
        KnowledgeMode.AS_CAPTURED_BY_HIO,
        CUTOFF,
        CODE,
    ).values():
        assert write_release(store, RightsGate(RIGHTS), r) is False


def test_a_different_code_ref_or_cutoff_is_a_different_release(tmp_path):
    world, _store, vs, releases = run(tmp_path, "a")
    other = s1a.build_releases(
        world,
        vs,
        RightsGate(RIGHTS),
        RIGHTS,
        KnowledgeMode.AS_CAPTURED_BY_HIO,
        CUTOFF,
        {**CODE, "commit": "f" * 40},
    )
    assert all(other[d].content_sha256 != releases[d].content_sha256 for d in DATASETS)


def test_fixture_2_status_does_not_change_identity(tmp_path):
    world, store, vs, releases = run(tmp_path, "a")
    r = releases["fx.usd_cash_vs_aud.excess"]
    data_before = store.get(f"{r.prefix}/data.csv")
    append_status(store, r.content_sha256, Status.VALIDATED, "owner", "fixture", CUTOFF)
    append_status(store, r.content_sha256, Status.WITHDRAWN, "owner", "fixture", CUTOFF)
    rebuilt = s1a.build_releases(
        world, vs, RightsGate(RIGHTS), RIGHTS, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE
    )
    assert rebuilt["fx.usd_cash_vs_aud.excess"].content_sha256 == r.content_sha256
    assert store.get(f"{r.prefix}/data.csv") == data_before
    assert content_sha256(json.loads(store.get(f"{r.prefix}/manifest.json"))) == r.content_sha256


def test_fixture_3_withdrawal_reaches_a_pinned_consumer(tmp_path):
    _, store, _, releases = run(tmp_path, "a")
    r = releases["cash.aud.overnight"]
    use = dict(
        required=Status.EXPLORATORY,
        consumer_class="hio_internal",
        gate=RightsGate(RIGHTS),
    )
    resolve_for_use(store, "cash.aud.overnight", r.content_sha256, **use)
    append_status(store, r.content_sha256, Status.WITHDRAWN, "owner", "fixture", CUTOFF)
    with pytest.raises(RefusedUse, match="withdrawn"):
        resolve_for_use(store, "cash.aud.overnight", r.content_sha256, **use)
    verify_release(store, "cash.aud.overnight", r.content_sha256)  # the pinned bytes still verify
    with pytest.raises(Exception, match="terminal"):
        append_status(store, r.content_sha256, Status.VALIDATED, "owner", "revive?", CUTOFF)


def test_consumers_check_level_and_current_rights_not_the_snapshot(tmp_path):
    _, store, _, releases = run(tmp_path, "a")
    r = releases["cash.aud.overnight"]
    with pytest.raises(RefusedUse, match="below validated"):
        resolve_for_use(
            store,
            "cash.aud.overnight",
            r.content_sha256,
            required=Status.VALIDATED,
            consumer_class="hio_internal",
            gate=RightsGate(RIGHTS),
        )
    perms = {p: Permission.parse("allow") for p in ALL_PERMISSIONS} | {
        "distribution.hio_internal": Permission.parse("deny")
    }
    revoked = RightsGate({"synthetic.rba": RightsRecord("synthetic.rba", Verification.OWNER_VERIFIED, perms)})
    assert r.core["rights"]["distribution.hio_internal"] == "allow"  # the build-time snapshot
    with pytest.raises(RightsRefused):
        resolve_for_use(
            store,
            "cash.aud.overnight",
            r.content_sha256,
            required=Status.EXPLORATORY,
            consumer_class="hio_internal",
            gate=revoked,
        )


def test_tampered_release_bytes_fail_verification(tmp_path):
    _, store, _, releases = run(tmp_path, "a")
    r = releases["cash.usd.overnight"]
    path = store.root / r.prefix / "data.csv"
    path.chmod(0o644)
    path.write_bytes(path.read_bytes().replace(b"4.3", b"4.4", 1))
    with pytest.raises(IntegrityError):
        verify_release(store, "cash.usd.overnight", r.content_sha256)


def test_only_the_owner_validates_approves_or_withdraws(tmp_path):
    _, store, _, releases = run(tmp_path, "a")
    sha = releases["cash.aud.overnight"].content_sha256
    for status in (Status.VALIDATED, Status.WITHDRAWN):
        with pytest.raises(PermissionError):
            append_status(store, sha, status, "claude/implementation-agent", "self-certify", CUTOFF)


# --- the catalogue index (HIO-ADR-0009) ------------------------------------------------------------


def test_catalogue_index_is_rebuildable_and_matches_the_records(tmp_path):
    _, store, vs, releases = run(tmp_path, "a")
    first, second = rebuild_index(store), rebuild_index(store)
    assert dump(first) == dump(second)
    indexed = dict(first.execute("SELECT dataset_id, content_sha256 FROM releases").fetchall())
    assert indexed == {d: r.content_sha256 for d, r in releases.items()}
    statuses = set(first.execute("SELECT status FROM effective_status").fetchall())
    assert statuses == {("exploratory",)}
    assert first.execute("SELECT count(*) FROM vintages").fetchone()[0] == len(vs.all_vintages())
