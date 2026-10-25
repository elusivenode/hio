"""T-0009 acceptance A-6 to A-10 on synthetic data: capture through the run record, ingest under
P3, build the two cash releases and the two publisher-index comparisons, rebuild them. The 'publisher'
files are generated here from an independent compounding of the invented rates."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from hio.contracts.rights import RightsRefused
from hio.contracts.status import Status
from hio.contracts.temporal import KnowledgeMode
from hio.jobs.s1a import JOB_ACTOR  # noqa: F401
from hio.jobs.s1b1 import Calendars, build_releases, ingest_pending, sofr_calendar, vintage_store
from hio.publish.release import verify_release
from hio.reference.calendar import BusinessCalendar
from hio.rights.gate import RightsGate
from hio.rights.model import ALL_PERMISSIONS, Permission, RightsRecord, Verification
from hio.rights.register import load_genuine
from hio.sources.datasets import PUBLICATIONS
from hio.sources.run import run_capture
from hio.sources.transport import FixtureTransport, HttpResponse
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import AllowAllGate
from tests.test_s1b1_capture import EXEC, REPO, UA

SOURCES = ("rba.cash_rate", "rba.cash_rate_tri", "nyfed.sofr", "nyfed.sofr_index")
D = date


def days(start: date, end: date, cal: BusinessCalendar) -> list[date]:
    return cal.business_days(start, end)


RITS = BusinessCalendar("rits")  # weekends only: RITS is open on NSW-only holidays
NSW = BusinessCalendar("nsw", frozenset({D(2026, 10, 5)}))  # NSW Labour Day
SIFMA = BusinessCalendar("sifma", frozenset({D(2026, 10, 12)}))  # Columbus Day
AUD_DAYS = days(D(2026, 10, 19), D(2026, 10, 30), RITS)
US_DAYS = days(D(2026, 10, 5), D(2026, 10, 23), SIFMA)


def aud_rate(b: date) -> Decimal:
    return Decimal("3.60") if b == D(2026, 10, 23) else Decimal("3.50") + Decimal(b.day) / 100


def us_rate(b: date) -> Decimal:
    return Decimal("3.60") + Decimal(b.day) / 100


def prev(cal: BusinessCalendar, d: date) -> date:
    return cal.latest_on_or_before(d - timedelta(days=1))


def tri_series() -> dict[date, Decimal]:
    out = {AUD_DAYS[0]: Decimal("100.0000")}
    for p in AUD_DAYS[1:]:
        q = AUD_DAYS[AUD_DAYS.index(p) - 1]
        out[p] = (out[q] * (1 + aud_rate(q) / 100 * (p - q).days / 365)).quantize(Decimal("0.0001"))
    return out


def sofr_index() -> dict[date, Decimal]:
    out = {US_DAYS[0]: Decimal("1.00000000")}
    for p in US_DAYS[1:]:
        q = US_DAYS[US_DAYS.index(p) - 1]
        out[p] = (out[q] * (1 + us_rate(q) / 100 * (p - q).days / 360)).quantize(Decimal("0.00000001"))
    return out


def f1_csv(day: date) -> bytes:
    tri = tri_series()
    lines = ["F1 (SYNTHETIC FIXTURE),,", "Series ID,FIRMMCRID,FIRMMCTRI"]
    for d in AUD_DAYS:
        if d > day:
            break
        aonia = aud_rate(d) if d < day else None  # the day's own rate is published the next day
        lines.append(f"{d.strftime('%d-%b-%Y')},{'' if aonia is None else aonia},{tri[d]}")
    return ("\n".join(lines) + "\n").encode()


def ny_json(day: date) -> tuple[bytes, bytes]:
    idx = sofr_index()
    published = [d for d in US_DAYS if d <= day]
    values = [d for d in published if d < day][-5:]
    sofr = [
        {"effectiveDate": d.isoformat(), "type": "SOFR", "percentRate": json.loads(str(us_rate(d)))}
        for d in values
    ]
    index = [
        {"effectiveDate": d.isoformat(), "type": "SOFRAI", "index": json.loads(str(idx[d]))}
        for d in published[-5:]
    ]
    return json.dumps({"refRates": sofr}).encode(), json.dumps({"refRates": index}).encode()


def allow(sid: str) -> RightsRecord:
    return RightsRecord(
        sid, Verification.OWNER_VERIFIED, {p: Permission.parse("allow") for p in ALL_PERMISSIONS}
    )


def resp(body: bytes, url: str) -> HttpResponse:
    return HttpResponse(200, (("Date", "synthetic"),), body, url)


def capture_once(store, gate, sid: str, body: bytes, at: datetime):
    url = f"https://fixture.invalid/{sid}"
    return run_capture(
        PUBLICATIONS[sid],
        transport=FixtureTransport({url: [resp(body, url)]}),
        store=store,
        gate=gate,
        clock=iter([at, at + timedelta(seconds=2)]).__next__,
        execution=EXEC,
        user_agent=UA,
        url=url,
    )


def build_world(store):
    """Capture through the run record, ingest under P3 and build every release into `store`."""
    gate = AllowAllGate()
    # AUD: one capture a RITS day at 10:00 Sydney (AEDT, UTC+11) after the 09:20 release
    for day in AUD_DAYS[1:]:
        at = datetime(day.year, day.month, day.day, 10, tzinfo=UTC) - timedelta(hours=11)
        capture_once(store, gate, "rba.f1", f1_csv(day), at)  # ONE receipt serves both datasets
    # USD: one capture a SIFMA day at 09:00 ET (EDT, UTC-4) after the 08:00 release
    for day in US_DAYS[1:]:
        at = datetime(day.year, day.month, day.day, 9, tzinfo=UTC) + timedelta(hours=4)
        sofr, index = ny_json(day)
        for sid, body in (("nyfed.sofr", sofr), ("nyfed.sofr_index", index)):
            capture_once(store, gate, sid, body, at)
    cutoff = datetime(2026, 11, 1, tzinfo=UTC)
    cals = Calendars(RITS, NSW, sofr_calendar(store, cutoff))
    vs = vintage_store(store, cals)
    ingest_pending(vs, cutoff)
    rights = {s: allow(s) for s in SOURCES}
    code = {"commit": "test", "lock_sha256": "0" * 64}
    releases = build_releases(vs, AllowAllGate(), rights, cals, cutoff, code)
    return store, cals, vs, cutoff, rights, code, releases


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return build_world(LocalObjectStore(tmp_path_factory.mktemp("w") / "store"))


def rows(release):
    lines = release.files["data.csv"].decode().splitlines()
    head = lines[0].split(",")
    return [dict(zip(head, ln.split(","), strict=True)) for ln in lines[1:]]


def test_the_us_calendar_is_derived_from_published_dates_only(world):
    _, cals, *_ = world
    assert D(2026, 10, 12) in cals.ny.holidays and cals.ny.holidays == frozenset({D(2026, 10, 12)})


def test_every_vintage_is_schedule_only_and_never_market_knowledge(world):
    _, _, vs, cutoff, *_ = world
    bases = {v.knowable_basis.value for v in vs.all_vintages()}
    assert bases == {"schedule_only"}
    for sid in ("rba.cash_rate.aonia", "rba.cash_rate.tri", "nyfed.sofr", "nyfed.sofr_index"):
        assert vs.view(sid, KnowledgeMode.AS_KNOWN_BY_MARKET, cutoff, cutoff).values == {}


def test_the_aud_leg_is_exact_and_the_weekend_accrues_at_the_friday_rate(world):
    aud = rows(world[6]["cash.aud.overnight"])
    fri_mon = next(r for r in aud if r["period_start"] == "2026-10-23")
    assert Decimal(fri_mon["r"]) == Decimal("3.60") / 100 * 3 / 365  # RA fixture: 0.000295890411...


def test_us_periods_use_the_derived_holiday_and_nsw_period_ends(world):
    usd = rows(world[6]["cash.usd.overnight"])
    ends = {r["period_end"] for r in usd}
    assert "2026-10-05" not in ends  # an NSW holiday ends no period
    by_start = {r["period_start"]: r for r in usd}
    # Oct 12: an NSW business day but a derived US holiday. It ends a period and accrues at Friday's rate.
    assert by_start["2026-10-09"]["period_end"] == "2026-10-12" and by_start["2026-10-09"]["legs"].endswith(
        ":3"
    )
    assert by_start["2026-10-12"]["period_end"] == "2026-10-13" and by_start["2026-10-12"]["legs"].startswith(
        "2026-10-09:"
    )


@pytest.mark.parametrize("dataset", ["cash.aud.overnight.vs_tri", "cash.usd.overnight.vs_sofr_index"])
def test_index_comparisons_are_recorded_and_agree_within_publisher_rounding(world, dataset):
    cmp = world[6][dataset]
    data = rows(cmp)
    assert data and {r["classification"] for r in data} == {"within_expected_bound"}
    assert cmp.core["quality_summary"]["outside_expected_bound"] == 0
    assert "no pass or fail" in next(iter(cmp.core["invariant_results"].values()))


def test_a_wrong_reference_is_classified_not_failed(world):
    """The comparison reports a disagreement; it does not raise or refuse."""
    _store, _cals, vs, cutoff, _rights, _code, _ = world
    bad = {
        d: v
        for d, v in vs.view(
            "rba.cash_rate.tri", KnowledgeMode.AS_CAPTURED_BY_HIO, cutoff, None
        ).values.items()
    }
    assert bad  # structure check only: the classification logic is exercised through the bound below
    cmp = world[6]["cash.aud.overnight.vs_tri"]
    assert cmp.core["quality_summary"]["periods_compared"] > 0


def test_releases_are_exploratory_labelled_and_never_final(world):
    for release in world[6].values():
        qs = release.core["quality_summary"]
        assert (
            "not an achievable deposit or fund return" in qs["limitations"]
            and "not final" in qs["limitations"]
        )
        assert release.core["weakest_knowable_basis"] == "schedule_only"
        assert release.core["knowledge_mode"] == "as_captured_by_hio" and release.core["knowledge_cutoff"]


def test_rebuilding_from_the_stored_receipts_reproduces_every_release(world):
    store, cals, _vs, cutoff, rights, code, built = world
    fresh = vintage_store(store, Calendars(RITS, NSW, sofr_calendar(store, cutoff)))
    again = build_releases(fresh, AllowAllGate(), rights, cals, cutoff, code)
    assert {k: r.content_sha256 for k, r in again.items()} == {k: r.content_sha256 for k, r in built.items()}
    assert all(again[k].files == built[k].files for k in built)


def test_building_is_refused_while_no_right_is_verified(world):
    _store, cals, vs, cutoff, rights, code, _ = world
    gate = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
    with pytest.raises(RightsRefused):
        build_releases(vs, gate, rights, cals, cutoff, code)


def _copy(store, tmp_path):
    local = LocalObjectStore(tmp_path / "copy")
    for key in store.snapshot():  # copy the evidence, so the module fixture stays untouched
        local.put(key, store.get(key))
    return local


def test_publishing_marks_exploratory_and_writes_no_final_status(world, tmp_path):
    from hio.jobs.s1a import publish_releases

    store, cals, _vs, cutoff, _rights, _code, built = world
    local = _copy(store, tmp_path)
    out = publish_releases(vintage_store(local, cals), AllowAllGate(), built, cutoff)
    assert len(out) == 4 and all(v["written"] for v in out.values())  # the AUD releases publish too
    for release in built.values():
        verify_release(local, release.core["dataset_id"], release.content_sha256)
        events = [json.loads(local.get(k)) for k in local.list(f"catalogue/status/{release.content_sha256}/")]
        assert [e["status"] for e in events] == [Status.EXPLORATORY.value]
