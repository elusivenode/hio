---
id: HIO-PROPOSAL-FACTOR-FIRST
title: "Factor-first sequencing (proposed): the duration factor and an analytical layer move ahead of further storage work"
status: adopted             # OD-0139 at ecd6b81 (blob 21d7e17ffb98); later edits record status only; authorises no capture, run or build
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-03
base_revision: 6030c17c980591bc8498d8cb77852647616ffb83
instruction: OD-0136 item 2 (draft only)
amends_if_adopted: docs/base-camp.md (proposed; order and parallel work); docs/roadmap.md (proposed; weeks 9–16); docs/implementation-plan.md (proposed; S3 and S5 entry)
sources: [architect consultation 20261103T141451-ask-15e3, docs/research/data-need-statement.md, docs/research/T-0002-free-history-sources-matrix.md, docs/charter.md §6]
---

# Factor-first sequencing (adopted as the working order, OD-0139)

> **Adopted by OD-0139 at `ecd6b81` as the working order; the text below stands as adopted.** It authorises no download, build, purchase or vendor contact. It changes no approved document: the roadmap, the
> implementation plan and base camp are all themselves proposed. Each step below needs its own yes.

## The problem

HIO's goal is high-quality factors and quantitative capability on top of them. Today:

| Capability | State at the base revision |
|---|---|
| Real data captured | none; the evidence store is empty |
| Factor specs | cash AUD, cash USD, USD-cash-versus-AUD excess |
| `src/hio/library` | cash and FX construction, about 300 lines |
| `src/hio/models`, `portfolio`, `taa`, `implementation` | **do not exist** (`docs/architecture.md` §1 lists them) |
| Numerical or columnar dependencies | **none**: `pyproject.toml` has DuckDB, and no numpy, pandas or pyarrow |
| DuckDB use | the catalogue index only |
| Release payloads | canonical CSV plus JSON manifests |
| Recent delivery | T-0010 to T-0015 are mostly operational assurance, with some cash validation reporting in T-0014 |

The architect's reading is the same: "most subsequent delivery concerns operational assurance". The records do not show hours,
so no percentage is claimed. The foundation was reasonable. The problem is that assurance has kept going with nothing on top
of it to assure.

## Where factor quality comes from

Judgement, resting on the cited statement:
- **Long clean history.** Covariance, regimes and tail dependence need decades (`docs/research/data-need-statement.md` §1).
- **Correct construction.** The return standard (RA §6, RA-INV-013) and triangulation (RA §11).
- **Labelled knowability.** Risk, regime and replication uses can run on `reconstructed(T)`. Captured data is needed only for
  walk-forward claims in Year 4 (same statement). Daily capture matters for later years, and costs little to run, so it should
  run, but it is not where Year-1 quality is won.

## The proposed sequence

Tracks run in parallel, and the numbers show the order of first effort. Capture goes first because its remaining work is small
and then it mostly waits on the calendar. It stops being the main programme once it runs.

| # | Track | Work | Needs from the owner | Status today |
|---|---|---|---|---|
| 1 | **Capture readiness, then background** | T-0015; R-1 and 7b; B-3 under Authorisation B revision 1; then the soak, with real cash rebuilds and dispositions (criterion 3) as receipts arrive | the gate decision; each "go"; the go-live yes | blocked on the gate |
| 2 | **Rights** | a complete dataset-by-operation decision for each source used: the H2 Treasury and H4 RBA F2 rows, every operation, recorded with attribution and conditions. V1 to V4 alone don't cover this (V4 asks whether F2's history suffices, not whether each operation is allowed). **Time-sensitive:** the Board's downloads are being retired in favour of FRED (`registers/sources.yaml:162`) | read the live clauses directly; verify or deny. The matrix came through a page-to-text tool, so it can't be the sole basis | draft rows |
| 3 | **Equity data** | T-0003: the vendor questions on licence class, derived storage and retention, in writing, before any purchase. Equity is the binding gap (data-need statement §3). Vendor lead time is a reason to start early | approve the questions and the contact | scorecard drafted |
| 4 | **One US duration experiment (S3 scope)** | one tenor, funded total return. **Spec before code** (`docs/standards/factor-specification.md`): tenor, curve type, interpolation and extrapolation, pricing approximation, coupon and day-count conventions, re-strike frequency, return class. RA-INV-013 fixtures and the decomposition residual; real inputs; a triangulation against a separately cleared reference, with an expected-difference model. Labelled `reconstructed(T)`. Excess return waits for a specified, cleared historical cash leg | track 2; the separate ordering act below | not started |
| 5 | **Minimal analytical reader** | justified by track 4's result: derived Parquet panels and DuckDB queries over stored exploratory releases (see below) | the choice below; the dependency decision | not started |
| 6 | **Risk first path** | sample covariance, then EWMA with declared frequency, decay and initialisation; a joint block bootstrap. It shows reproducible construction, alignment, uncertainty and lineage. **It claims nothing about diversification**: a few rate series share an exposure. A common numeraire and return basis are required before any portfolio reading. No optimisation or tail claims | after 4 and 5 | not started |
| 7 | **AU and breadth** | AU duration after resolving F2's benchmark-YTM approximation and whether monthly values can be valuation points; then more tenors and families | after 4 | not started |

**Paused unless a track needs it:** further storage hardening, locking the immutability policy, a hosted database, finality work
beyond recording evaluations, and running T-0014's tools before there are real receipts. The owner's C5 decision still comes,
on evidence, whenever the re-run is done.

## The analytical layer

**The input choice comes first.** `resolve_for_use` (`src/hio/publish/status.py:83`) resolves a stored release: it verifies bytes
and lineage, requires status events and checks current rights. It can't read an unreleased factor. The approved architecture also
says `models` reads released datasets (`docs/architecture.md` §1). So there are two routes:

| Route | What it means | Assessment |
|---|---|---|
| **A. Store an `exploratory` release** (recommended) | the duration series goes through the existing release machinery, in a local store, with `reconstructed(T)` in its manifest. Not in the evidence store; not approved for any consumer (OD-0038 keeps that distinct) | reuses lineage and status. It departs from base-camp criterion 7's "not released", which would need rewording to "not approved for a consumer" |
| B. Keep it unreleased | a bounded research reader over receipt, spec, code and output hashes, with its own rights checks | can't use the resolver, and can't feed `models` without an exception to the architecture |

| Choice | Proposal | Why |
|---|---|---|
| Authority | **Derived and disposable**, like the catalogue index. Rebuilt from pinned releases; never a system of record | keeps one authority (HIO-ADR-0009's reasoning) |
| Format | Parquet panels written by DuckDB. Release identity stays hashed over the canonical CSV, so **no manifest or standard changes** | columnar and portable |
| Cache key | release hash and cutoff, **plus** transformation version, frequency, alignment and missing-data policy, return convention, and code and lock identity | the hash and cutoff alone don't identify a derived panel |
| Interface | a small reader for named pinned releases. It calls the resolver, then **separately enforces the requested knowledge mode and cutoff**, because the resolver only returns those declarations. It rechecks rights and status on cache use | research does not bypass the checks |
| Values | canonical decimals are preserved up to the numerical boundary | no silent float drift in stored values |
| Location | local or CI first. Files in blob only if a real need appears | no new infrastructure |
| Numerics | numpy under the hash-locked `uv.lock`, as **its own owner decision** (a stack change under OD-0038). New builds change `code_ref`, so they need not reproduce old release hashes; existing releases are not rewritten | needed for covariance and bootstrap; none exists today |
| Rules | import rules unchanged. `taa` reads PIT views only. Research outputs are not artefacts until re-run as pinned jobs (`docs/architecture.md` §3) | no new exception |

The hosted-database triggers in `docs/architecture.md` §5 stay as they are. Nothing measured fires them today.

## What this does to the existing documents

| Document | Change if adopted |
|---|---|
| `docs/base-camp.md` §"Order and parallel work" | rights and the duration experiment (criteria 8 and 7) start alongside capture readiness, not after the soak. Criterion 7 rewords "not released" under route A. Add an analytical-reader criterion. Criterion 1 splits, as in Authorisation B revision 1. Base camp still isn't adopted by this |
| `docs/roadmap.md` | a bounded US duration experiment runs before G2. S2 and S3 **promotion** stays behind G2. S5 may start on what exists, as "first path", not as D1 itself. Dates need redoing and are not restated here |
| `docs/implementation-plan.md` | S3's row gains "a bounded experiment may precede S1 completion; promotion needs S1". S5 gains the analytical reader as an explicit prerequisite |
| `docs/architecture.md` (**approved**) | **no change proposed.** §2 already says DuckDB is derived. Listing the reader would be a later edit needing its own approval |
| G2, S1b-1 completion, finality, HIO-ADR-0012, HIO-ADR-0010 | **unchanged**. Nothing here is promotion, and early research discharges no S1 obligation |

**Is this allowed under approved documents?** The S2/S3-after-G2 ordering is in the proposed roadmap and plan. Approved HIO-ADR-0010
excludes bonds from S1b's scope, and doesn't forbid separately authorised research. But OD-0132 reserves changing the ordering for
criterion 7 to a separate owner act, and its authorised build covers criteria 3–6 and 9 only. So this needs an explicit yes, and
it is **not already authorised**.

## Where this departs from the current plan, and the risks

| Risk | Mitigation |
|---|---|
| A research-only factor gets used as if validated | `reconstructed(T)` and `exploratory` labels; not released; RA §12's anti-masquerade gate applies at promotion; Codex reviews construction |
| Work starts on rights that are later denied | track 1 comes first; no download before verification. US first because Treasury is presumed public domain, though unverified (V3) |
| AU duration history is short (F2 daily from 2013-05-20); F2.1 and H.15 monthly values may be averages, which cannot price a return | check before building on them (V4; data-need statement §1, §2). Declare a daily-only span if so |
| The factor set outruns operational evidence | capture still runs, and promotion still needs it. G2 is untouched |
| The owner's time (R-09), and the December–January holiday | one track at a time gets the owner's attention. The rights reading is the one near-term owner task that can't be delegated |
| Governance cost per task stays high | **an open question, not a proposal.** This session's receipts and records took many steps for one accepted task. The owner may want to consider, later, whether research-only work can carry lighter review than capture and release work |

## Where the architect and Claude differ

Two consultations informed this draft (`20261103T141451-ask-15e3`, `20261103T142328-ask-3901`). The second challenged an earlier
version and changed it: capture readiness moved first, the experiment narrowed to one US tenor, the rights track widened, the
reader's input became an explicit choice, and the claims about C5 and the 403 were qualified.

- **Agree:** keep Azure; decouple capture from a C5 decision; capture readiness first; then a bounded US experiment and a minimal
  reader, then covariance as a demonstration.
- **Remaining difference, of emphasis:** the architect weights the capture clock more heavily. Claude expects cash vintages to add
  little and sees the main value of early capture as evidence of operation and real cash rebuilds. The order is the same either way.
- **Claude's own order also has this risk:** the first real receipts may change the reader's design. That is a reason to keep the
  reader minimal.

## The owner decisions this draft awaits

Each is separate:

1. "Adopt `docs/decisions/factor-first-sequencing-proposal.md` at `<revision>` as the working order, leaving G2, finality and S1
   obligations unchanged?" A yes sets priorities. Each track still needs its own authorisation.
2. **If 1 is yes,** a complete rights decision on the H2 and H4 rows. That is the owner's own reading of the live clauses.
3. **If 1 is yes and rights clear,** "Authorise a bounded pre-G2 experiment: one US tenor, funded total return, stored as a local
   `exploratory` release (route A), with a one-off download of the cleared source, the spec first, and review by Codex?" A yes
   approves it for no consumer and discharges no S1 obligation.
4. **After 3 has a result,** "Authorise a card for the minimal analytical reader, including the numpy decision?" A yes authorises a
   non-live build only.
