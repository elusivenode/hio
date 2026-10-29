"""T-0014 P-2: the external finality evaluation record (base-camp criterion 4) on synthetic inputs.

Layer one evaluates a synthetic vintage against attempt records in the in-memory blob fake, whose
provider-assigned write times let C5 pass, and writes the record. Layer two runs `evaluate_release` over
releases built from the synthetic capture world, whose local store cannot supply a write time, so the
evaluation is honestly not final. A passing record labels nothing and changes no status; a missing or
failing one is no final claim. No network, no real data."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

import pytest

from hio.contracts.canonical import canonical_json, instant_str, sha256_hex
from hio.contracts.layout import attempt_record_key
from hio.jobs.s1b1 import AONIA, SOFR_INDEX, TRI, series_defs
from hio.jobs.s1b1_finality import (
    Contributing,
    documented_window_close,
    evaluate_release,
    evaluate_vintages,
    publication_policies,
)
from hio.marketdata.finality import CATEGORIES, CHECK_NAMES, FinalityPolicy, release_finality
from hio.marketdata.finality_record import (
    FINALITY_PREFIX,
    FORMAT,
    FinalityRecordError,
    NoFinalClaim,
    ReleaseRef,
    build_record,
    evaluation_sha256,
    finality_key,
    load_record,
    record_shas,
    require_final_claim,
    verified_records,
    write_record,
)
from hio.marketdata.runrecord import Execution
from hio.publish.release import make_release, write_release
from hio.storage.blobstore import BlobObjectStore
from hio.storage.fakeblob import FakeBlobBackend
from hio.storage.objectstore import IntegrityError, LocalObjectStore
from tests.helpers import AllowAllGate
from tests.test_s1b1_releases import build_world
from tests.test_t0010_finality import SHA, SID, SRC, VALID, Env, T, W, body_of, ci, parse_keys, vintage

POLICY = FinalityPolicy("github_actions", {"commit": SHA, "lock_sha256": "0" * 64}, parse_keys)
EVALUATOR = {"commit": "e" * 40, "lock_sha256": "1" * 64}
CUTOFF = T(6, 0)


@pytest.fixture
def env(tmp_path) -> Env:
    backend = FakeBlobBackend(immutable=True)
    e = Env(BlobObjectStore(backend), backend)
    backend._clock = lambda: e.now
    e.tmp_path = tmp_path  # for the scenario that needs a store with no provider write time
    return e


def synthetic_release(cutoff: datetime = CUTOFF):
    return make_release(
        {
            "dataset_id": "synthetic.cash",
            "version": "t",
            "spec_ref": "synthetic.cash@1",
            "code_ref": {"commit": "test"},
            "inputs": [{"series_id": SID}],
            "knowledge_mode": "as_captured_by_hio",
            "knowledge_cutoff": instant_str(cutoff),
            "weakest_knowable_basis": None,
            "rights": {},
            "invariant_results": {},
            "quality_summary": {},
            "supersedes": None,
        },
        {"data.csv": b"a,b\n"},
    )


def ref_of(release) -> ReleaseRef:
    c = release.core
    return ReleaseRef(
        release.release_id, release.content_sha256, c["dataset_id"], T(6, 0), c["spec_ref"]
    )  # fmt: skip


def evaluate(env: Env, v, *, held=None, cutoff: datetime = CUTOFF, w_doc=W, policy: FinalityPolicy = POLICY):
    """Evaluate one contributing vintage of the synthetic release and build (not write) its record."""
    release = synthetic_release(cutoff)
    evs = evaluate_vintages(
        env.store, [Contributing(v, SRC, w_doc)], [v] if held is None else held, cutoff, {SRC: policy}
    )
    verdict = release_finality([e.verdict for e in evs], cutoff)
    body = build_record(
        ref_of(release),
        evaluator=EVALUATOR,
        policies={SRC: policy},
        spec_refs=["synthetic.cash@1"],
        upstream=[],
        evaluations=evs,
        verdict=verdict,
    )
    return release, body


def attempts_of(body):
    return [a for v in body["vintages"] for a in v["attempts"]]


def failed_reasons(body, check: str) -> set[tuple[str, str]]:
    return {
        (r["code"], r["category"])
        for a in attempts_of(body)
        for c in a["checks"]
        if c["name"] == check
        for r in c["reasons"]
    }


# --- round trip and content address ---------------------------------------------------------------------


def test_a_passing_evaluation_round_trips_at_its_content_address(env):
    rec, v1 = env.good()
    release, body = evaluate(env, v1)
    before = env.store.snapshot()
    key = write_record(env.store, body)
    sha = evaluation_sha256(body)
    assert key == f"{FINALITY_PREFIX}{release.release_id}/{sha}.json" == finality_key(release.release_id, sha)
    assert sha256_hex(env.store.get(key)) == sha
    assert set(env.store.snapshot()) - set(before) == {key} and not set(before) - set(env.store.snapshot())

    loaded = load_record(env.store, release.release_id, sha)
    assert loaded.key == key and loaded.final
    assert loaded.body == json.loads(canonical_json(body))  # what was built is what comes back
    assert record_shas(env.store, release.release_id) == [sha]
    assert require_final_claim(env.store, release.release_id).evaluation_sha256 == sha

    assert body["format"] == FORMAT
    assert body["release"] == {
        "release_id": release.release_id,
        "content_sha256": release.content_sha256,
        "dataset_id": "synthetic.cash",
        "knowledge_cutoff": CUTOFF,
        "spec_ref": "synthetic.cash@1",
    }
    assert body["evaluator"] == EVALUATOR and body["spec_refs"] == ["synthetic.cash@1"]
    assert body["policy"]["sources"][SRC]["pinned_commit"] == SHA
    assert body["policy"]["sources"][SRC]["delta_seconds"] == 600.0
    (vin,) = body["vintages"]
    assert (vin["series_id"], vin["valid_time"], vin["vintage_seq"]) == (SID, VALID, 1)
    assert vin["source_id"] == SRC and vin["w_doc"] == W and vin["verdict"]["final"] is True
    assert vin["verdict"]["evidence"] == [rec.key] and body["attempt_record_ids"] == [rec.key]
    assert body["witnesses"] == [
        {"attempt_record": rec.key, "receipt_id": rec.receipt_id, "provider_write_time": T(5, 30, 10)}
    ]
    (attempt,) = vin["attempts"]
    assert attempt["passed"] and [c["name"] for c in attempt["checks"]] == list(CHECK_NAMES)
    assert body["aggregate"]["final"] is True and body["aggregate"]["category"] is None
    assert body["aggregate"]["evidence"] == [rec.key]
    assert body["checks"]["C5"] == {"records_evaluated": 1, "records_failed": 0, "categories": []}
    assert "no lifecycle status" in body["status_effect"]
    assert "signature" not in body


def test_the_record_is_deterministic_and_rewriting_it_is_a_no_op(env):
    _, v1 = env.good()
    _, a = evaluate(env, v1)
    _, b = evaluate(env, v1)
    assert canonical_json(a) == canonical_json(b) and evaluation_sha256(a) == evaluation_sha256(b)
    assert write_record(env.store, a) == write_record(env.store, b)
    assert len(list(env.store.list(FINALITY_PREFIX))) == 1


def test_a_different_evaluation_is_a_different_address(env):
    _, v1 = env.good()
    _, a = evaluate(env, v1)
    _, later = evaluate(env, v1, cutoff=T(7, 0))  # another cutoff is another release and another evaluation
    assert evaluation_sha256(a) != evaluation_sha256(later)


def test_a_record_changed_in_place_fails_the_content_address_on_read():
    backend = FakeBlobBackend(immutable=False)
    env = Env(BlobObjectStore(backend), backend)
    _, v1 = env.good()
    release, body = evaluate(env, v1)
    key = write_record(env.store, body)
    sha = evaluation_sha256(body)
    forged = json.loads(env.store.get(key))
    forged["aggregate"]["final"] = False
    backend.overwrite(key, canonical_json(forged))
    with pytest.raises(IntegrityError, match="overwritten"):  # the store itself sees two versions
        load_record(env.store, release.release_id, sha)
    assert verified_records(env.store, release.release_id) == []
    with pytest.raises(NoFinalClaim):
        require_final_claim(env.store, release.release_id)


def test_bytes_that_do_not_hash_to_their_address_fail_the_content_address_on_read(env):
    _, v1 = env.good()
    release, body = evaluate(env, v1)
    sha = evaluation_sha256(body)
    forged = json.loads(canonical_json(body))
    forged["aggregate"]["final"] = False  # a canonical, well-formed record: only its address is wrong
    env.store.put(finality_key(release.release_id, sha), canonical_json(forged))
    with pytest.raises(FinalityRecordError, match="content address"):
        load_record(env.store, release.release_id, sha)
    assert verified_records(env.store, release.release_id) == []


def test_a_record_under_another_name_or_another_release_is_refused(env):
    _, v1 = env.good()
    release, body = evaluate(env, v1)
    data = canonical_json(body)
    other = f"rel-{'9' * 64}"

    def put_at(release_id: str, sha: str, payload: bytes) -> None:
        env.store.put(finality_key(release_id, sha), payload)

    put_at(release.release_id, "a" * 64, data)  # right release, wrong address
    put_at(other, sha256_hex(data), data)  # right address, filed under another release
    spaced = json.dumps(body, sort_keys=True, default=str, indent=1).encode()
    put_at(release.release_id, sha256_hex(spaced), spaced)  # hashes to its name, but is not canonical
    for release_id, sha in (
        (release.release_id, "a" * 64),
        (other, sha256_hex(data)),
        (release.release_id, sha256_hex(spaced)),
    ):
        with pytest.raises(FinalityRecordError):
            load_record(env.store, release_id, sha)
    assert verified_records(env.store, release.release_id) == []
    with pytest.raises(NoFinalClaim):
        require_final_claim(env.store, release.release_id)


# --- a missing or failing evaluation is no final claim --------------------------------------------------


def test_a_missing_record_blocks_a_final_claim(env):
    release = synthetic_release()
    assert record_shas(env.store, release.release_id) == []
    with pytest.raises(NoFinalClaim, match="no passing external finality evaluation"):
        require_final_claim(env.store, release.release_id)


def test_a_failing_record_is_stored_but_supports_no_final_claim(env):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), execution=Execution("other"))
    release, body = evaluate(env, vintage(1, "3.60", T(5, 30, 8)))
    assert body["aggregate"]["final"] is False
    write_record(env.store, body)
    (loaded,) = verified_records(env.store, release.release_id)
    assert not loaded.final
    with pytest.raises(NoFinalClaim):
        require_final_claim(env.store, release.release_id)


def test_a_passing_record_changes_no_manifest_or_status(env):
    """The record is a new object beside the release. The release's manifest and files are untouched,
    and nothing is written that names a status."""
    release = synthetic_release()
    prefix = release.prefix
    env.store.put(f"{prefix}/manifest.json", canonical_json(release.core))
    env.store.put(f"{prefix}/data.csv", release.files["data.csv"])
    _, v1 = env.good()
    before = env.store.snapshot()
    _, body = evaluate(env, v1)
    key = write_record(env.store, body)
    after = env.store.snapshot()
    assert {k: h for k, h in after.items() if k != key} == before
    assert env.store.get(f"{prefix}/manifest.json") == canonical_json(release.core)
    assert b"finality" not in env.store.get(f"{prefix}/manifest.json")
    assert require_final_claim(env.store, release.release_id).final
    assert not any(k.startswith("catalogue/status") for k in after)


def test_a_release_with_no_contributing_vintage_is_not_final():
    body = build_record(
        ref_of(synthetic_release()),
        evaluator=EVALUATOR,
        policies={},
        spec_refs=[],
        upstream=[],
        evaluations=[],
        verdict=release_finality([], CUTOFF),
    )
    assert body["aggregate"]["final"] is False and body["aggregate"]["category"] == "missing"


def test_a_vintage_with_no_policy_for_its_publication_raises(env):
    _, v1 = env.good()
    with pytest.raises(ValueError, match="no finality policy"):
        evaluate_vintages(env.store, [Contributing(v1, SRC, W)], [v1], CUTOFF, {})


# --- every check C1-C7 and every refusal category -------------------------------------------------------


def _c1_unreadable(env: Env):
    rec = env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10))
    # a record filed under a key whose hash is not its own: a second store holds only the forgery
    forged = Env(BlobObjectStore(FakeBlobBackend()))
    forged.store.put(rec.key.replace(rec.record_sha256, "0" * 64), rec.canonical())
    forged.now = env.now
    return forged, POLICY


def _c2_no_capture(env: Env):
    rec = env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10))
    bare = Env(BlobObjectStore(FakeBlobBackend(clock=lambda: T(5, 30, 10))))
    bare.store.put(rec.key, rec.canonical())  # the attempt record only: no capture, no bytes
    return bare, POLICY


def _c3_digest(env: Env):
    wrong = [(SID, VALID.isoformat(), "sha256:" + "0" * 64)]
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), keys=wrong)
    return env, POLICY


def _c3_parse(env: Env):
    env.good()

    def refuses(_: bytes):
        raise ValueError("schema")

    return env, FinalityPolicy("github_actions", SHA, refuses)


def _c4_stale(env: Env):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), date_header=T(5, 10))
    return env, POLICY


def _c5_late(env: Env):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 41))
    return env, POLICY


def _c5_no_write_time(env: Env):
    local = Env(LocalObjectStore(env.tmp_path / "store"))
    local.good()
    return local, POLICY


def _c6_other(env: Env):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), execution=Execution("other"))
    return env, POLICY


def _c6_wrong_sha(env: Env):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), execution=ci(sha="f" * 40))
    return env, POLICY


def _c7_twice(env: Env):
    same = ci("5555")
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), execution=same)
    env.attempt(
        body_of("3.60"), T(5, 40), T(5, 40, 8), T(5, 40, 10), outcome="verified_unchanged", execution=same
    )
    return env, POLICY


FAILURES = [
    # (scenario, the check that fails, its reason code, the reason's category, the release's category or None)
    (_c1_unreadable, "C1", "record_unreadable", "inconsistent", "missing"),
    (_c2_no_capture, "C2", "no_capture_record", "missing", "missing"),
    (_c3_digest, "C3", "digest_not_reproduced", "inconsistent", "inconsistent"),
    (_c3_parse, "C3", "parse_failed", "failed", "failed"),
    (_c4_stale, "C4", "date_too_old", "delayed", "delayed"),
    (_c5_late, "C5", "written_too_late", "inconsistent", "inconsistent"),
    (_c5_no_write_time, "C5", "no_provider_write_time", "unverified", "unverified"),
    (_c6_other, "C6", "platform_other", "unverified", "unverified"),
    (_c6_wrong_sha, "C6", "sha_not_code_ref", "inconsistent", "inconsistent"),
    (_c7_twice, "C7", "execution_claimed_twice", "inconsistent", "inconsistent"),
]


@pytest.mark.parametrize(
    ("scenario", "check", "code", "category", "release_category"),
    FAILURES,
    ids=[f"{f[1]}-{f[2]}" for f in FAILURES],
)
def test_every_failed_check_is_recorded_with_its_reason_and_the_release_is_not_final(
    env, scenario, check, code, category, release_category
):
    arranged, policy = scenario(env)
    release, body = evaluate(arranged, vintage(1, "3.60", T(5, 30, 8)), policy=policy)
    assert (code, category) in failed_reasons(body, check)
    assert body["checks"][check]["records_failed"] >= 1
    assert category in body["checks"][check]["categories"]
    assert body["aggregate"]["final"] is False and body["aggregate"]["category"] == release_category
    assert [a for a in attempts_of(body) if not a["passed"]]
    write_record(arranged.store, body)
    with pytest.raises(NoFinalClaim):
        require_final_claim(arranged.store, release.release_id)


def test_the_scenarios_cover_every_check_and_every_refusal_category():
    assert {f[1] for f in FAILURES} == set(CHECK_NAMES)
    assert {f[3] for f in FAILURES} == set(CATEGORIES)


def test_a_failed_run_is_recorded_as_a_failed_attempt(env):
    """A run that failed is attempt evidence: it is listed with its failing checks, not dropped."""
    from hio.marketdata.runrecord import RunRecord

    failed = RunRecord(
        source_id=SRC,
        execution=ci("7001"),
        request={"method": "GET", "url": "https://synthetic.invalid/rate.csv"},
        status=503,
        headers=[],
        response_sha256=None,
        response_bytes=None,
        attempted_at=T(5, 30),
        completed_at=T(5, 30, 3),
        outcome="failed",
        error_class="http_status",
    )
    env.now = T(5, 30, 5)
    env.store.put(failed.key, failed.canonical())
    assert failed.key == attempt_record_key(SRC, T(5, 30), failed.record_sha256)
    _, body = evaluate(env, vintage(1, "3.60", T(5, 30, 8)))
    (vin,) = body["vintages"]
    assert vin["verdict"]["final"] is False and vin["verdict"]["category"] == "failed"
    (attempt,) = vin["attempts"]
    assert attempt["outcome"] == "failed" and {"C2", "C3", "C4"} <= set(attempt["failed_checks"])
    assert failed_reasons(body, "C2") == {("failed_record", "failed")}
    assert body["aggregate"]["category"] == "failed" and body["attempt_record_ids"] == [failed.key]


# --- the window close and the policies --------------------------------------------------------------------


def test_the_documented_window_close_is_the_publishers_local_close_on_the_release_day(world):
    series = series_defs(world["cals"])
    # AONIA for Monday 26 Oct is released on Tuesday 27 Oct; the window closes 16:00 Sydney (AEDT, +11)
    assert documented_window_close(series[AONIA], date(2026, 10, 26)) == datetime(
        2026, 10, 27, 5, 0, tzinfo=UTC
    )
    assert documented_window_close(series[TRI], date(2026, 10, 27)) == datetime(
        2026, 10, 27, 5, 0, tzinfo=UTC
    )
    # the SOFR Index is dated by its publication day; the window closes 14:30 New York (EDT, -4)
    assert documented_window_close(series[SOFR_INDEX], date(2026, 10, 12)) == datetime(
        2026, 10, 12, 18, 30, tzinfo=UTC
    )
    import dataclasses

    unscheduled = dataclasses.replace(series[AONIA], schedule=None)
    assert documented_window_close(unscheduled, date(2026, 10, 26)) is None


def test_publication_policies_parse_each_publication_with_its_own_schema():
    policies = publication_policies("github_actions", {"commit": SHA})
    assert set(policies) >= {"rba.f1", "nyfed.sofr", "nyfed.sofr_index"}
    assert policies["rba.f1"].delta == timedelta(minutes=10) and policies["rba.f1"].pinned_commit == SHA
    with pytest.raises(Exception, match=r"."):  # a body that is not that publication's file is refused
        list(policies["nyfed.sofr"].parse_keys(b"not json"))


# --- layer two: evaluate_release over releases built from the synthetic capture world ---------------------


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    store, cals, vs, cutoff, _rights, _code, releases = build_world(
        LocalObjectStore(tmp_path_factory.mktemp("w") / "store")
    )
    for release in releases.values():
        write_release(store, AllowAllGate(), release)
    return {"store": store, "cals": cals, "vs": vs, "cutoff": cutoff, "releases": releases}


def test_evaluate_release_records_the_comparison_with_its_upstream_cash_release(world):
    store, vs, releases = world["store"], world["vs"], world["releases"]
    comparison = releases["cash.aud.overnight.vs_tri"]
    cash = releases["cash.aud.overnight"]
    manifests = {k: store.get(k) for k in store.snapshot() if k.endswith("manifest.json")}
    before = store.snapshot()
    policies = publication_policies("github_actions", {"commit": SHA})

    evaluated = evaluate_release(
        store,
        vs,
        "cash.aud.overnight.vs_tri",
        comparison.content_sha256,
        policies=policies,
        evaluator=EVALUATOR,
    )
    after = store.snapshot()
    assert set(after) - set(before) == {evaluated.key} and not set(before) - set(after)
    assert {k: store.get(k) for k in after if k.endswith("manifest.json")} == manifests  # byte-unchanged

    body = load_record(store, comparison.release_id, evaluation_sha256(evaluated.body)).body
    assert body["release"]["content_sha256"] == comparison.content_sha256
    assert body["release"]["knowledge_cutoff"] == instant_str(world["cutoff"])
    assert body["upstream_releases"] == [
        {"dataset_id": "cash.aud.overnight", "content_sha256": cash.content_sha256}
    ]
    assert body["spec_refs"] == sorted({comparison.core["spec_ref"], cash.core["spec_ref"]})
    assert {v["series_id"] for v in body["vintages"]} == {
        TRI,
        AONIA,
    }  # the cash release's and the reference's
    assert {v["source_id"] for v in body["vintages"]} == {"rba.f1"}
    assert all(v["w_doc"] is not None for v in body["vintages"])
    # a plain local store has no provider write time and the synthetic runs are not CI-witnessed:
    # the evaluation is recorded and is not final (fail closed)
    assert body["aggregate"]["final"] is False and body["aggregate"]["category"] == "unverified"
    assert body["checks"]["C5"]["records_failed"] >= 1 and body["checks"]["C6"]["records_failed"] >= 1
    assert evaluated.final is False
    with pytest.raises(NoFinalClaim):
        require_final_claim(store, comparison.release_id)

    again = evaluate_release(
        store,
        vs,
        "cash.aud.overnight.vs_tri",
        comparison.content_sha256,
        policies=policies,
        evaluator=EVALUATOR,
    )
    assert again.key == evaluated.key and store.snapshot() == after  # deterministic, idempotent


def test_evaluate_release_can_report_without_writing(world):
    store, vs, releases = world["store"], world["vs"], world["releases"]
    usd = releases["cash.usd.overnight"]
    before = store.snapshot()
    evaluated = evaluate_release(
        store,
        vs,
        "cash.usd.overnight",
        usd.content_sha256,
        policies=publication_policies("github_actions", {"commit": SHA}),
        evaluator=EVALUATOR,
        write=False,
    )
    assert store.snapshot() == before and evaluated.key.startswith(f"{FINALITY_PREFIX}{usd.release_id}/")
    assert {v["series_id"] for v in evaluated.body["vintages"]} == {"nyfed.sofr"}
    assert evaluated.body["upstream_releases"] == []


def test_evaluate_release_refuses_a_release_that_is_not_in_the_store(world):
    store, vs = world["store"], world["vs"]
    with pytest.raises(Exception):  # noqa: B017 - the store reports the absent manifest
        evaluate_release(
            store, vs, "cash.aud.overnight", "0" * 64, policies={}, evaluator=EVALUATOR
        )  # fmt: skip
    assert not any(k.startswith(f"{FINALITY_PREFIX}rel-{'0' * 64}") for k in store.snapshot())
