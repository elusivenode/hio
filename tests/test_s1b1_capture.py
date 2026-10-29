"""T-0009 acceptance A-2, A-5, A-6 (capture side) on synthetic fixtures only: the five adapters and
the capture-run record. No network: the transport is scripted, and the rights gate is exercised both
with the genuine register (everything refused) and with a permissive test double."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from hio.contracts.layout import ATTEMPTS_PREFIX, CAPTURES_PREFIX
from hio.contracts.rights import Operation, RightsRefused
from hio.marketdata.capture import latest_capture, load_receipt_record, receipt_bytes
from hio.marketdata.runrecord import Execution, IntegrityError, envelope_headers, load_run_record
from hio.rights.gate import GateContext, RightsGate
from hio.rights.register import load_genuine
from hio.sources.datasets import DATASETS, PUBLICATIONS, MalformedPayload
from hio.sources.run import run_capture
from hio.sources.transport import FixtureTransport, HttpResponse, TransportError
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import AllowAllGate

REPO = Path(__file__).resolve().parent.parent
FX = Path(__file__).parent / "fixtures" / "synthetic" / "s1b1"
URL = "https://fixture.invalid/{}"
UA = "hio-test (synthetic)"
EXEC = Execution("github_actions", "123", "1", "capture", "a" * 40)

FILES = {
    "rba.f1": "rba_f1_v1.csv",  # one published file serving rba.cash_rate and rba.cash_rate_tri
    "rba.expert_judgement": "rba_expert_judgement.csv",
    "nyfed.sofr": "nyfed_sofr_v1.json",
    "nyfed.sofr_index": "nyfed_sofr_index_v1.json",
}
HEADERS = (
    ("Date", "Fri, 23 Oct 2026 22:59:30 GMT"),
    ("Age", "0"),
    ("Last-Modified", "Thu, 22 Oct 2026 21:59:28 GMT"),
    ("ETag", '"abc"'),
    ("Content-Type", "text/csv"),
    ("Set-Cookie", "session=SECRETVALUE"),
)


def resp(name: str, status: int = 200, url: str = "x") -> HttpResponse:
    return HttpResponse(status, HEADERS, (FX / name).read_bytes(), URL.format(url))


def clock(*steps: datetime):
    it = iter(steps)
    return lambda: next(it)


def t(h: int, m: int = 0, s: int = 0, day: int = 23) -> datetime:
    return datetime(2026, 10, day, h, m, s, tzinfo=UTC)


@pytest.fixture
def store(tmp_path):
    return LocalObjectStore(tmp_path / "store")


def go(sid, transport, store, clk, gate=None, **kw):
    return run_capture(
        PUBLICATIONS[sid],
        transport=transport,
        store=store,
        gate=gate or AllowAllGate(),
        clock=clk,
        execution=EXEC,
        user_agent=UA,
        url=URL.format(sid),
        **kw,
    )


def attempts(store):
    return list(store.list(ATTEMPTS_PREFIX))


@pytest.mark.parametrize("sid", sorted(PUBLICATIONS))
def test_genuine_register_clears_capture_and_internal_research_only(sid):
    """A-2 after OD-0116 correction 1 and OD-0118: the five datasets are owner_verified for capture and,
    since every release carries its notices, for building and hio_internal use; any consumer class
    beyond hio_internal stays refused."""
    gate = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"), GateContext(on_external_host=True))
    subjects = [d.source_id for d in PUBLICATIONS[sid].datasets]
    for op in (Operation.FETCH, Operation.STORE_RAW, Operation.BUILD, Operation.STORE_DERIVED):
        gate.authorise(op, subjects)
    gate.authorise(Operation.PUBLISH, subjects, consumer_class="hio_internal")
    with pytest.raises(RightsRefused):
        gate.authorise(Operation.PUBLISH, subjects, consumer_class="smsf_app")


@pytest.mark.parametrize("sid", ["rba_statistical_tables", "nyfed_reference_rates", "rba.cash_rate_target"])
def test_genuine_register_still_refuses_unverified_sources(sid):
    """A-2: a source or dataset without an owner_verified record (parents, D4) is refused."""
    gate = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
    with pytest.raises(RightsRefused):
        gate.authorise(Operation.FETCH, [sid])


def test_gate_runs_before_the_request(store):
    transport = FixtureTransport({URL.format("nyfed.sofr"): [resp("nyfed_sofr_v1.json")]})

    class Checking(AllowAllGate):
        def authorise(self, operation, source_ids, consumer_class=None):
            assert transport.requests == []
            super().authorise(operation, source_ids, consumer_class)

    gate = Checking()
    go("nyfed.sofr", transport, store, clock(t(1), t(2)), gate=gate)
    assert [o for o, _ in gate.calls] == [Operation.FETCH, Operation.STORE_RAW]


@pytest.mark.parametrize("sid", sorted(PUBLICATIONS))
def test_a_new_capture_keeps_the_receipt_and_the_provenance(sid, store):
    transport = FixtureTransport({URL.format(sid): [resp(FILES[sid], url=sid)]})
    res = go(sid, transport, store, clock(t(1, 0, 0), t(1, 0, 3)), slot="first", slot_due_at=t(0, 45))
    assert res.is_new and res.record.outcome == "verified_changed"
    rec = load_run_record(store, res.record.key)  # hash recomputed against the key on read
    assert rec == res.record
    assert rec.attempted_at == t(1, 0, 0) and rec.completed_at == t(1, 0, 3)
    assert rec.request == {
        "method": "GET",
        "url": URL.format(sid),
        "final_url": URL.format(sid),
        "user_agent": UA,
    }
    assert rec.execution == EXEC and rec.slot == "first" and rec.slot_due_at == t(0, 45)
    assert [h[0] for h in rec.headers] == [h[0] for h in HEADERS]  # every header, in order
    assert dict(map(tuple, rec.headers))["Date"] == "Fri, 23 Oct 2026 22:59:30 GMT"
    assert dict(map(tuple, rec.headers))["Set-Cookie"] == "[withheld]"
    receipt = latest_capture(store, sid)
    assert receipt.receipt_id == rec.receipt_id == rec.response_sha256 and receipt.captured_at == t(1, 0, 3)
    assert receipt_bytes(store, receipt) == (FX / FILES[sid]).read_bytes()  # exact bytes, hash verified
    assert rec.response_bytes == receipt.byte_length
    assert len(attempts(store)) == 1 and len(list(store.list(CAPTURES_PREFIX))) == 1


def test_a_run_record_assigns_no_publication_time(store):
    transport = FixtureTransport({URL.format("nyfed.sofr"): [resp("nyfed_sofr_v1.json")]})
    res = go("nyfed.sofr", transport, store, clock(t(1), t(2)))
    assert not {"knowable_at", "knowable_basis", "published_at"} & set(res.record.as_record())


def test_an_identical_refetch_writes_no_receipt_and_one_run_record(store):
    sid = "nyfed.sofr"
    transport = FixtureTransport({URL.format(sid): [resp("nyfed_sofr_v1.json"), resp("nyfed_sofr_v1.json")]})
    first = go(sid, transport, store, clock(t(1), t(2)))
    receipts_before = {k for k in store.snapshot() if not k.startswith(ATTEMPTS_PREFIX)}
    second = go(sid, transport, store, clock(t(3), t(4)))
    assert not second.is_new and second.record.outcome == "verified_unchanged"
    assert second.record.receipt_id == first.record.receipt_id
    assert {k for k in store.snapshot() if not k.startswith(ATTEMPTS_PREFIX)} == receipts_before
    assert len(attempts(store)) == 2  # the evidence that the check happened and found no change


def test_a_changed_payload_is_a_new_receipt(store):
    sid = "nyfed.sofr"
    transport = FixtureTransport({URL.format(sid): [resp("nyfed_sofr_v1.json"), resp("nyfed_sofr_v2.json")]})
    go(sid, transport, store, clock(t(1), t(2)))
    second = go(sid, transport, store, clock(t(3), t(4)))
    assert second.is_new and second.record.outcome == "verified_changed"
    assert len(list(store.list(CAPTURES_PREFIX))) == 2


def test_failures_write_one_failed_record_and_nothing_else(store):
    sid = "nyfed.sofr"
    bad = HttpResponse(200, HEADERS, b"not json", URL.format(sid))
    wrong = HttpResponse(
        200,
        HEADERS,
        b'{"refRates": [{"effectiveDate": "2026-10-22", "type": "EFFR", "percentRate": 3.6}]}',
        URL.format(sid),
    )
    down = HttpResponse(503, HEADERS, b"unavailable", URL.format(sid))
    cases = [(TransportError("timeout"), "network"), (down, "http_status"), (bad, "parse"), (wrong, "schema")]
    for n, (item, klass) in enumerate(cases):
        s = LocalObjectStore(store.root.parent / f"s{n}")
        res = go(sid, FixtureTransport({URL.format(sid): [item]}), s, clock(t(1), t(2)))
        assert res.record.outcome == "failed" and res.record.error_class == klass and res.receipt is None
        assert len(attempts(s)) == 1 and len(s.snapshot()) == 1  # no receipt, no capture record, no bytes
        assert load_run_record(s, res.record.key) == res.record
    assert res.record.status == 200 and res.record.response_sha256 is None


def test_a_clock_that_runs_backwards_fails_closed(store):
    sid = "nyfed.sofr"
    transport = FixtureTransport({URL.format(sid): [resp("nyfed_sofr_v1.json"), resp("nyfed_sofr_v2.json")]})
    go(sid, transport, store, clock(t(5), t(6)))
    res = go(sid, transport, store, clock(t(1), t(2)))
    assert res.record.outcome == "failed" and res.record.error_class == "clock_order"
    assert len(list(store.list(CAPTURES_PREFIX))) == 1


def test_a_record_that_does_not_match_its_key_is_refused(store):
    transport = FixtureTransport({URL.format("nyfed.sofr"): [resp("nyfed_sofr_v1.json")]})
    res = go("nyfed.sofr", transport, store, clock(t(1), t(2)))
    wrong = res.record.key.replace(res.record.record_sha256[:8], "0" * 8)
    store.put(wrong, res.record.canonical())
    with pytest.raises(IntegrityError):
        load_run_record(store, wrong)


def test_replay_reparses_every_capture_from_the_store_alone(store):
    sid = "rba.f1"
    transport = FixtureTransport({URL.format(sid): [resp("rba_f1_v1.csv"), resp("rba_f1_v2.csv")]})
    go(sid, transport, store, clock(t(1), t(2)))
    go(sid, transport, store, clock(t(3), t(4)))
    parsed = [
        PUBLICATIONS[sid].parse(receipt_bytes(store, load_receipt_record(store, k)))
        for k in store.list(CAPTURES_PREFIX)
    ]
    assert [len(p.rows) for p in parsed] == [5, 6]  # AONIA and TRI rows from the one file
    aonia = [r.value for r in parsed[1].rows if r.series_id == "rba.cash_rate.aonia"]
    assert aonia == [Decimal("3.60"), Decimal("3.61"), Decimal("3.62")]


def test_capture_is_deterministic_across_fresh_stores(tmp_path):
    def build(name):
        s = LocalObjectStore(tmp_path / name)
        sid = "nyfed.sofr_index"
        go(sid, FixtureTransport({URL.format(sid): [resp("nyfed_sofr_index_v1.json")]}), s, clock(t(1), t(2)))
        return s.snapshot()

    assert build("a") == build("b")


def test_parsers_are_exact_and_keep_only_the_wanted_series():
    f1 = (FX / "rba_f1_v1.csv").read_bytes()
    aonia = DATASETS["rba.cash_rate"].parse(f1)
    tri = DATASETS["rba.cash_rate_tri"].parse(f1)
    assert [(r.series_id, str(r.valid_time), r.value) for r in aonia.rows] == [
        ("rba.cash_rate.aonia", "2026-10-21", Decimal("3.60")),
        ("rba.cash_rate.aonia", "2026-10-22", Decimal("3.61")),
    ]  # the empty 23-Oct cell is not yet published; the ASX and target columns are ignored
    assert [r.value for r in tri.rows] == [Decimal("100.50"), Decimal("100.60"), Decimal("100.70")]
    flags = DATASETS["rba.expert_judgement"].parse((FX / "rba_expert_judgement.csv").read_bytes())
    assert [(str(f.valid_time), f.kind) for f in flags.flags] == [("2026-07-31", "A"), ("2026-10-02", "A")]
    sofr = DATASETS["nyfed.sofr"].parse((FX / "nyfed_sofr_v1.json").read_bytes())
    assert [r.value for r in sofr.rows] == [Decimal("3.65"), Decimal("3.66")]  # Decimal, never float
    idx = DATASETS["nyfed.sofr_index"].parse((FX / "nyfed_sofr_index_v1.json").read_bytes())
    assert idx.rows[0].value == Decimal("1.12345678")


@pytest.mark.parametrize(
    "sid,payload,klass",
    [
        ("rba.cash_rate", b"Title,x\n", "schema"),
        ("rba.cash_rate", b"Series ID,FIRMMCTRI\n21-Oct-2026,1\n", "schema"),
        ("rba.cash_rate", b"Series ID,FIRMMCRID\n21-Oct-2026,abc\n", "parse"),
        ("rba.cash_rate", b"Series ID,FIRMMCRID\n21-Oct-2026,1\n21-Oct-2026,2\n", "parse"),
        ("rba.expert_judgement", b"Date,Type\n31-Jul-2026,Z\n", "schema"),
        ("nyfed.sofr", b'{"refRates": []}', "schema"),
        (
            "nyfed.sofr",
            b'{"refRates": [{"effectiveDate": "2026-10-22", "type": "SOFR", "percentRate": "3.6"}]}',
            "schema",
        ),
    ],
)
def test_malformed_payloads_fail_closed(sid, payload, klass):
    with pytest.raises(MalformedPayload) as e:
        DATASETS[sid].parse(payload)
    assert e.value.error_class == klass


def test_execution_is_copied_from_the_ci_environment_or_marked_other():
    env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_RUN_ID": "9",
        "GITHUB_RUN_ATTEMPT": "2",
        "GITHUB_JOB": "capture",
        "GITHUB_SHA": "b" * 40,
    }
    assert Execution.from_environ(env) == Execution("github_actions", "9", "2", "capture", "b" * 40)
    assert Execution.from_environ({}) == Execution("other")
    assert envelope_headers([("Set-Cookie", "x"), ("Date", "d")]) == [
        ["Set-Cookie", "[withheld]"],
        ["Date", "d"],
    ]


def test_a_url_is_required():
    with pytest.raises(ValueError):
        run_capture(
            PUBLICATIONS["nyfed.sofr"],
            transport=FixtureTransport({}),
            store=None,
            gate=AllowAllGate(),
            clock=clock(t(1)),
            execution=EXEC,
            user_agent=UA,
        )


def test_timestamps_are_utc_and_ordered():
    assert timedelta(0) <= t(2) - t(1)
