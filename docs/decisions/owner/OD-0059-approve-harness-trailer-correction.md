---
id: OD-0059
title: "Owner approval of the bounded harness-0.7.1 trailer and CI-reporting correction (steps 5.7, 5.8, 5.10); regression test passed; published history and both CI runs preserved; routine delegated receipt still NOT enabled"
decision: approve
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-approve-trailer-correction.md (pasted by the owner, verbatim)
  sha256: 004daa75a966fbaeaa3a7ab52f72829e057825aae1ef848a5c335b5e775b9123
  date: 2026-10-25
  quote: "I approve the narrowly scoped correction proposed in `docs/decisions/harness-0.7.1-trailer-correction-proposal.md`, subject to exact-revision and diff verification."
applies_to:
  - path: docs/decisions/harness-0.7.1-trailer-correction-proposal.md
    revision: dfb0a20   # revision 1, blob b8d2fac0dc18a223a209f5fbc68f5c5e46e94c3a, on main since merge 09c86f7
  - path: docs/harness/operating-model.md
    revision: "§6.2 steps 5.7, 5.8 and 5.10 only; the integrating commit is on the merge that records this OD"
related: {adrs: [], tasks: [], findings: []}
---

# OD-0059: approve the trailer and CI-reporting correction

## Owner action

Approve the correction proposed at revision 1 (blob `b8d2fac0dc18…`, commit `dfb0a20`, verified on
`main` at `09c86f7`) with the owner's seven points (verbatim in the history file). Point 3 **adds** to
the proposal: the proposal left CI status as an open question for 5.10; the owner makes it a
**mandatory reported result**, distinguishing evidence-integrity checks from CI integration checks.

## The exact approved amendment (operating model §6.2 step 5; no other text changed)

| Step | Added text |
|---|---|
| 5.7 | "Once the 5.8 commit exists and before the 5.9 recheck, run `uv run python tools/check_repo.py trailers origin/main HEAD`: it must pass. (The local hook does not check trailers; CI does. If it fails, stop and fix the **unpublished** import commit.)" |
| 5.8 | trailer bullet "`HIO-Actor: <role> (evidence receipt, OD-NNNN)`, as CI requires on every non-merge commit (`tools/check_repo.py trailers`); and `Co-Authored-By` when the receiver is an agent"; and after "Keep it pure…": the 5.9 merge commit and any later administrative commit carry the same trailer (merge commits are exempt in CI, but carry it for consistency) |
| 5.10 | a new paragraph "Report CI as a separate, mandatory result": after the push, report the CI conclusion (run id and head SHA) in a section separate from the evidence-integrity result. Evidence-integrity checks (5.1 to 5.10) decide whether the receipt is complete; CI integration checks are reported alongside. A CI failure does not by itself change a verified receipt, and a green run does not substitute for the integrity checks. A failed run is never rewritten away; a later green run is a separate run, never a repair |
| front matter | a `changelog` line only ("harness-0.7.1 correction 1"). `status`, `version` and `approved_by` are unchanged |

Diff verification: the change to `docs/harness/operating-model.md` is 18 insertions and 3 deletions in
five hunks (the changelog, 5.7, 5.8 twice, 5.10); steps 1 to 4a, 5.0 to 5.6, 5.9, 5.11, 6 to 9 and
every other section are byte-identical. No tool, workflow or hook changed. The proposal file gets a
status-only edit (`approved_applied`).

## Test evidence (bounded scratch-clone regression, nothing published)

Transcript: `trailer-regression.txt` in the session scratchpad (reproduced here), base `origin/main` `09c86f7`,
using the existing `tools/check_repo.py trailers`:

| Case | Result |
|---|---|
| 1. import-style commit **without** `HIO-Actor` | **rejected**: `no HIO-Actor trailer`, exit 1 |
| 2. the same commit **with** `HIO-Actor: claude/implementation-agent (evidence receipt, OD-0059)` | **accepted**, exit 0 |
| 3. `HIO-Actor:` with no value | rejected, exit 1 (the rule needs `\S` after the colon) |
| 4. real range `618059f..347da95` (the first receipt) | rejected on `3131e70`, exit 1: the historical failure reproduced |
| 4b. real range `347da95..09c86f7` (the follow-up) | accepted, exit 0 |

Scratch branches were deleted. The test shows the check rejects a missing trailer and accepts the correct
one. It does **not** exercise a full receipt under the corrected text.

## Preserved history

- The original failed CI run `40175402830` on `347da95`, and the successful later run `40175824947` on `09c86f7`,
  are both preserved and reported as separate runs. The second does not repair the first.
- No commit was amended, rebased, replaced or force-pushed.

## Recommendation on lifting the suspension of routine delegated receipt (not a decision)

**Recommend: do not lift it yet; lift it in one bounded step after one clean corrected receipt.**

1. What is established: the evidence-receipt mechanics worked on a live receipt (tag first, import, tree identity,
   blobs, remote verification), and the one defect found is corrected and regression-tested.
2. What is not established: **no receipt has yet run end to end under the corrected text**, so the
   owner's OD-0056 condition (a supervised first use recorded as passed) is not yet met. A regression test of
   one rule is not a first use.
3. Proposed path: the next owner-assigned receipt (B2, when the owner assigns it) is run supervised under
   the corrected text; it passes if the integrity checks pass, the trailer check passes before merge, and CI on
   the push is green, reported separately. The owner then records that in an OD.
4. Proposed scope of any later delegation: only a receipt of a verification or review record that (a) has an
   owner-authored assignment source, (b) has the reviewer's independent report, and (c) needs no `reviews/README.md`
   change or only Class N rows. Anything involving a Class S transition, an index conflict, a missing 5.0 input or any stop
   condition keeps the owner's go-ahead. The receipt sweep and the CI report stay mandatory.
5. Two known weaknesses stay open and are the owner's to accept: the semantic index check (5.6) is manual, and the
   assignment check's expected string for A2 and B2 came from the receiver's own OD-0053 text.

Routine delegated receipt is **not enabled** by this record.

## What this record does NOT do

- It does not declare the first-use validation passed, enable routine delegated receipt, receive B2, approve any
  source right, modify accepted S1a, authorise S1b, or reopen the harness review.
- It changes no unrelated operating procedure, tool, workflow or hook.

## Corrections (append-only)

None.
