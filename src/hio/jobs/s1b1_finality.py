"""S1b-1 external finality evaluation of a built release (T-0014 P-2; base-camp criterion 4).

Given a release already in the store, this job reconstructs the exact vintages that contributed to it,
evaluates C1-C7 and finality for each at the release's knowledge cutoff (`hio.marketdata.finality`,
unchanged), and writes one canonical content-addressed record under `catalogue/finality/<release_id>/`
(`hio.marketdata.finality_record`). It never rewrites a manifest, signs anything, labels a release final
or changes a lifecycle status: a record is evidence for a caller that wants to make a final claim, and
the absence of a passing record means there is no claim (`require_final_claim`).

No fetch happens here. The inputs are the release, the vintage store and the attempt records the capture
job retained. A comparison release is evaluated together with the cash release it names as an input
(`upstream`), because it is final only if everything it was computed from is.

W_doc, the documented window close of a key, comes from ADR-0012 §4.3: 16:00 Sydney on the release day
for the RBA series, 14:30 New York on the release day for the NY Fed series (`documented_window_close`).
It is a function argument so a spec-declared window can replace it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from hio.contracts.observation import Vintage, parse_instant
from hio.contracts.temporal import KnowledgeMode
from hio.jobs.s1a import verify_release_inputs
from hio.marketdata.finality import (
    DEFAULT_DELTA,
    DEFAULT_EPSILON,
    FinalityPolicy,
    RecordEvaluation,
    evaluate_records,
    release_finality,
    vintage_finality,
)
from hio.marketdata.finality_record import (
    ReleaseRef,
    VintageEvaluation,
    build_record,
    evaluation_sha256,
    finality_key,
    write_record,
)
from hio.marketdata.series import SeriesDef
from hio.marketdata.vintages import VintageStore
from hio.publish.release import verify_release
from hio.sources.datasets import PUBLICATIONS
from hio.sources.run import checked_keys

SYD, NY = "Australia/Sydney", "America/New_York"
WINDOW_CLOSE = {SYD: time(16, 0), NY: time(14, 30)}  # HIO-ADR-0012 §4.3, documented window close W_doc
EVALUATOR_NAME = "hio.jobs.s1b1_finality/1"


@dataclass(frozen=True)
class Contributing:
    """A vintage that contributed to a release, the publication it was captured from and its W_doc."""

    vintage: Vintage
    source_id: str
    w_doc: datetime | None


@dataclass(frozen=True)
class Evaluated:
    key: str  # where the record was written
    body: dict[str, Any]

    @property
    def final(self) -> bool:
        return self.body["aggregate"]["final"] is True


def documented_window_close(series: SeriesDef, valid_time: date) -> datetime | None:
    """W_doc(k) as a UTC instant: the documented close time on the key's release day, in the series'
    timezone. None when the series has no schedule or a timezone with no documented close (the checks that
    need W_doc then fail closed)."""
    schedule = series.schedule
    close = WINDOW_CLOSE.get(schedule.tz) if schedule is not None else None
    if schedule is None or close is None:
        return None
    zone = ZoneInfo(schedule.tz)
    release_day = schedule.calendar.add_business_days(
        valid_time, schedule.lag_business_days
    )  # a date, not an instant
    return datetime.combine(release_day, close, tzinfo=zone).astimezone(UTC)


def publication_policies(
    ci_platform: str,
    code_ref: Mapping[str, str] | str,
    *,
    delta=DEFAULT_DELTA,
    epsilon=DEFAULT_EPSILON,
) -> dict[str, FinalityPolicy]:
    """One policy per publication: the series schema (C3) is that publication's own parser, the same one
    the capture run used to write `keys_checked`."""

    def keys_of(spec):
        return lambda body: checked_keys(spec.parse(body))

    return {
        pid: FinalityPolicy(ci_platform, code_ref, keys_of(spec), delta, epsilon)
        for pid, spec in sorted(PUBLICATIONS.items())
    }


def evaluate_vintages(
    store,
    contributing: Iterable[Contributing],
    held: Iterable[Vintage],
    cutoff: datetime,
    policies: Mapping[str, FinalityPolicy],
) -> list[VintageEvaluation]:
    """Finality of each distinct contributing vintage at `cutoff`, with the attempt records evaluated for
    its key (those covering it, every failed run, and every unreadable record). `held` are all the
    vintages HIO holds; C3 compares each record's digests with the one held when the run completed."""
    held_by_series: dict[str, list[Vintage]] = {}
    for v in held:
        held_by_series.setdefault(v.series_id, []).append(v)
    distinct = {(c.vintage.series_id, c.vintage.valid_time, c.vintage.vintage_seq): c for c in contributing}
    cache: dict[tuple[str, str, datetime | None], list[RecordEvaluation]] = {}
    out = []
    for ident in sorted(distinct):
        c = distinct[ident]
        v = c.vintage
        if c.source_id not in policies:
            raise ValueError(f"no finality policy for publication {c.source_id}")
        policy, series_held = policies[c.source_id], held_by_series.get(v.series_id, [])
        verdict = vintage_finality(store, c.source_id, v, series_held, cutoff, w_doc=c.w_doc, policy=policy)
        cache_key = (c.source_id, v.series_id, c.w_doc)
        if cache_key not in cache:
            cache[cache_key] = evaluate_records(
                store, c.source_id, policy, w_doc=c.w_doc, vintages=series_held
            )
        key = (v.series_id, v.valid_time.isoformat())
        attempts = tuple(
            e
            for e in cache[cache_key]
            if e.record is None or e.record.outcome == "failed" or key in e.digests()
        )
        out.append(VintageEvaluation(v, c.source_id, c.w_doc, verdict, attempts))
    return out


def _release_cores(store, dataset_id: str, sha: str) -> list[tuple[str, str, dict[str, Any]]]:
    """The release and, transitively, every release named as an `upstream` input, each verified byte for
    byte. A missing or altered release raises: no evaluation is written for inputs that cannot be read."""
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    pending = [(dataset_id, sha)]
    while pending:
        ds, h = pending.pop()
        if (ds, h) in seen:
            continue
        seen[(ds, h)] = verify_release(store, ds, h)
        pending.extend(
            (i["upstream"]["dataset_id"], i["upstream"]["content_sha256"])
            for i in seen[(ds, h)]["inputs"]
            if "upstream" in i
        )
    return [(ds, h, core) for (ds, h), core in sorted(seen.items())]


def evaluate_release(
    store,
    vs: VintageStore,
    dataset_id: str,
    content_sha256: str,
    *,
    policies: Mapping[str, FinalityPolicy],
    evaluator: Mapping[str, str],
    window_close: Callable[[SeriesDef, date], datetime | None] = documented_window_close,
    write: bool = True,
) -> Evaluated:
    """Evaluate the release `releases/<dataset_id>/<content_sha256>` and write its record (unless
    `write` is False, which returns the body and the key it would have). Raises if the release, its
    upstream releases or its pinned view inputs cannot be reconstructed exactly."""
    cores = _release_cores(store, dataset_id, content_sha256)
    top = next(core for ds, h, core in cores if (ds, h) == (dataset_id, content_sha256))
    cutoff = parse_instant(top["knowledge_cutoff"])
    contributing: list[Contributing] = []
    for _, _, core in cores:
        verify_release_inputs(vs, core)  # the recorded pins equal the store's, or this raises
        for record in core["inputs"]:
            if "series_id" not in record:
                continue
            mode = KnowledgeMode(record["knowledge_mode"])
            view_cutoff = parse_instant(record["knowledge_cutoff"]) if record["knowledge_cutoff"] else None
            q = parse_instant(record["quality_as_of"]) if record["quality_as_of"] else None
            view = vs.view(record["series_id"], mode, view_cutoff, q)
            series = vs.series[record["series_id"]]
            contributing.extend(
                Contributing(v, series.source_id, window_close(series, v.valid_time))
                for v in view.values.values()
            )
    evaluations = evaluate_vintages(store, contributing, vs.all_vintages(), cutoff, policies)
    verdict = release_finality([e.verdict for e in evaluations], cutoff)
    ref = ReleaseRef(f"rel-{content_sha256}", content_sha256, dataset_id, cutoff, top["spec_ref"])
    used = {e.source_id for e in evaluations}
    body = build_record(
        ref,
        evaluator={"evaluator": EVALUATOR_NAME, **evaluator},
        policies={s: p for s, p in policies.items() if s in used},
        spec_refs=[core["spec_ref"] for _, _, core in cores],
        upstream=[
            {"dataset_id": ds, "content_sha256": h}
            for ds, h, _ in cores
            if (ds, h) != (dataset_id, content_sha256)
        ],
        evaluations=evaluations,
        verdict=verdict,
    )  # fmt: skip
    key = write_record(store, body) if write else finality_key(ref.release_id, evaluation_sha256(body))
    return Evaluated(key, body)
