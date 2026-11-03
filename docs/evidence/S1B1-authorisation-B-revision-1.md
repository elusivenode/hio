---
id: HIO-EVIDENCE-S1B1-AUTH-B-REV1
title: "Authorisation B, revision 1 (proposed): exploratory P3 capture no longer waits for the C5 decision"
status: adopted             # OD-0139 at ecd6b81 (blob c7db575b9788); later edits record status only; authorises no capture, run or build
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-03
base_revision: 6030c17c980591bc8498d8cb77852647616ffb83
instruction: OD-0136 item 1 (draft only)
amends_if_adopted: docs/evidence/S1B1-authorisation-B-package.md (stages B-2 and B-3); docs/base-camp.md (criterion 1, proposed)
sources: [architect consultation 20261103T141451-ask-15e3, OD-0063, OD-0119, HIO-ADR-0012 §4.3.3, docs/evidence/b2/README.md]
---

# Authorisation B, revision 1 (adopted, OD-0139)

> **Adopted by OD-0139 at `ecd6b81`; the text below stands as adopted.** Nothing here authorises capture, an Azure write, a dispatch or a C5 amendment. It amends no ADR text. If the
> owner adopts it, the Authorisation B package and base-camp criterion 1 are read as changed below.

## The change, in one line

**B-3 stops waiting for a decision on C5.** Capture may start as exploratory, `schedule_only` (P3) capture once storage
integrity and access controls are shown. C5 stays unresolved and on the record, and every finality obligation stays owed.

## Why

- **The gate is stricter than its purpose.** The package says B-3 follows "B-2's outcome is decided". C5 only supports a
  claim that a value was checked after its revision window (HIO-ADR-0012 §4.3.3). No S1b-1 release makes that claim:
  each is `exploratory` and none may be labelled final (OD-0063; T-0009 A-9).
- **The B-2 result says less than it appears to.** The probe took `completed_at` after the write. The ADR defines it as the
  moment the body is fully read, and production does that (`src/hio/sources/run.py:93`, before any write). Whole-second
  `Last-Modified` remains a real question, but 50/50 does not show that production would fail.
- **OD-0063 already lets finality evaluation follow capture**, while keeping the obligation before final labels, S1b-1
  completion or G2. This is the strongest basis for the change.
- **A later C5 decision can be applied to records already written, conditionally.** `evaluate_records` reads `s` through
  `store.write_time(attempt_record_key)`, which queries provider metadata (`src/hio/marketdata/finality.py:354`,
  `src/hio/storage/blobstore.py:122`). The attempt record does not contain that witness. So later evaluation holds only while the
  original object and its provider metadata stay accessible. A copy's timestamps cannot substitute (`tools/second_copy.py` keeps
  the original metadata separately).
- **Waiting has a cost.** Unrecoverable days are lost (charter §6), though see the limit below.

**A limit on the first reason for urgency.** For these two cash series, the value of vintages is probably modest. SOFR's
documented revision is same-day and only above 1bp (`registers/sources.yaml:52`), and the data-need statement finds that
captured data is needed only for walk-forward signal claims (Year 4). The stronger reasons to start are evidence of
unattended operation and real cash rebuilds. This is judgement; the architect weights the capture clock more heavily.

## What is already shown, and what is not

| Control | State | Source |
|---|---|---|
| Evidence store: shared key off, no public access, ZRS, immutability Unlocked 3,650 days, empty | shown (read-back) | OD-0125 correction 2 |
| Fresh create; one version per key | shown (probe account) | `docs/evidence/b2/README.md` |
| Writer's overwrite and delete refused | shown, as **RBAC** refusals (probe account) | `docs/evidence/b2/README.md` |
| Immutability against a privileged actor | **not shown** (7b excluded) | same; STATUS |
| The writer identity on the evidence account itself | **not shown** by a write; first exercised by the watched B-3 dispatch | B-3 step 4 |
| C5 | **unresolved** | `docs/evidence/b2/README.md` |
| Duplicate create | returns 403, not 409 | same; T-0015 |

**A known limit in how storage errors fail (traced in code; not exercised on Azure).** An unmapped 403 raises, so nothing is
silently accepted or overwritten: integrity holds. Availability and accounting do not fully hold:
- `BlobStagedWrites.commit` checks first, then creates keys one at a time, with no rollback (`src/hio/storage/blobstore.py:145`).
  Earlier writes survive a later failure, for example receipt bytes without their attempt record.
- A storage exception escapes `run_capture` and `run_due`. It ends the remaining due slots and skips the completeness check, and
  it writes no failed run record. The process fails, so the failed-run alert still fires.
- Candidates for reaching this path: a key appearing between the check and the create, or an SDK retry after a lost response.

Mapping the 403 (T-0015 F-1) does not fix this by itself, because `put` still raises. It needs a decision: accept it during the
soak, where it would fail loudly, or raise a small task for it.

## Revised stages

### B-2

| Step | Before | Proposed |
|---|---|---|
| First run | retained | unchanged; the failed evidence stays on record as it stands |
| R-1 re-run and 7b | prerequisites for the C5 decision, which gates B-3 | **run first, in one sitting, but B-3 does not wait on a C5 decision from them.** Each still needs its own "go". The account is held and the cost is cents, so this closes the evidence gap cheaply rather than leaving it open-ended |
| C5 decision | before B-3 | **after real evidence**, before any final claim. It stays an ADR-0012 change and an owner decision |
| Destroy | after the re-run and 7b | unchanged; at least 24 hours after the last write |

**7b needs a fresh write.** The first run's objects had a one-day retention period, now passed, so a delete of those objects
would prove nothing.

### B-3 prerequisites

| # | Prerequisite | Proposed state |
|---|---|---|
| 1 | The five URLs approved | **required**, unchanged |
| 2 | `LIVE_AUTHORISATION`, the workflow move, `alert_enabled = true`, the `capture` reviewer rule removed (C-4) | **required**, unchanged |
| 3 | `~/.hio-state/` backed up | **required** (unconfirmed today) |
| 4 | The punctuality bar agreed before the soak (base-camp criterion 2) | **required** |
| 5 | The owner's explicit statement of the staging below | **new, required** |
| 6 | T-0015 merged, after its finding is fixed and verified | **required.** R-1 needs the instrumented probe on `main`, and the review is nearly finished. Acceptance stays a separate owner act |
| 7 | R-1 and 7b run | **recommended before go-live; the owner's explicit choice.** Deferring 7b is a separate evidence-limit decision. If deferred, it runs within the first month, alongside the second copy (S-7) |
| 8 | C5 decided | **removed as a gate** |
| 9 | The storage-error limit above | **an owner decision:** accept it for the soak, or raise a small task first |
| 10 | 2027 calendars | **a hard date, not a B-3 gate**: capture loses RITS days without them from 2027-01-01 (recheck by 2026-12-01) |

**An adverse 7b** (a retained version deleted or altered by a privileged actor) goes to the owner before go-live. The exploratory
label makes no claim that depends on it, but the owner decides.

**Likely order:** T-0015 fixed, verified and accepted; R-1 and 7b; then the go-live yes.

### The staging the B-3 yes would state

OD-0063 is written "for S1b-1.0 only", so it does not clearly reach live capture. The B-3 yes should say so explicitly:

> Live S1b-1 capture runs under the OD-0063 staging until finality is met: every vintage is `schedule_only`; every release is
> `exploratory`, states its knowledge cutoff and is never labelled final; C5 is unresolved. C1–C7 evaluations, when recorded, are
> reported as they fall, and a failure is never overridden. Nothing here discharges a finality obligation.

## What does not change

- HIO-ADR-0012's text, C1–C7, δ and ε. **No C5 amendment.**
- Finality is owed before any final label, S1b-1 stage completion or G2 (OD-0063).
- The soak and its CI-run audit (S1-A13), S1b-2, the triangulations and all G2 evidence.
- Rights: only the five owner-verified datasets, for `hio_internal`. S-7 within the first month of capture.

## Base-camp criterion 1 (proposed document; wording if adopted)

Split it, so that evidence stays honest and capture is not blocked:
- **1a Storage integrity and access:** the B-1 read-back, the B-2 RBAC refusals and one-version result, and the first
  production write. Needed before go-live.
- **1b C5 decided:** on real evidence, by an owner decision. Needed before any final claim, and still before base camp is
  declared met.

## Risks accepted if adopted

| Risk | Consequence | Mitigation |
|---|---|---|
| C5 is later decided in a form the early records cannot meet | those vintages stay non-final; the values stay usable as `exploratory` | attempt records and original provider metadata stay in place; a failure is reported, never rounded away |
| Provider metadata for early objects stops being available | C5 for those records can no longer be evaluated | the original store is retained; `tools/second_copy.py` keeps original metadata, with its provenance limit stated |
| A storage error interrupts a run, with partial durable state | a slot lacks its attempt record, and the remaining due slots don't run that time | the run fails loudly; the completeness check flags the gap on the next run; see the limit above |
| Privileged immutability proves weaker than assumed | early objects had less protection than designed | 7b before go-live, or within the first month if deferred; second copy (S-7); no final claims meanwhile |
| Objects written now are retained for 3,650 days under the account default | a mistaken write cannot simply be removed (Unlocked allows a policy change, at the owner's hand) | the one watched dispatch before the schedule |
| "Exploratory" drifts into being treated as validated | a research result rests on unproven evidence | the labels are enforced in code (T-0009 A-9); the release status is checked on use (T-0014 P-4) |

## What would change this recommendation

- A consumer needing a final or `as_known_by_market` claim sooner.
- Evidence that the retained records could not support a later C5 evaluation.
- An adverse 7b, before go-live.

## The owner decision this draft awaits

"Adopt `docs/evidence/S1B1-authorisation-B-revision-1.md` at `<revision>`, so that B-3 no longer waits for a C5 decision?" A yes
changes the gate only. It does not authorise go-live, which keeps its own yes on its URLs and revision.
