---
id: OD-0039
title: "Owner instruction: record S1-A16 run 1 (transcripts and preliminary assessment) and prepare the smallest correction; S1-A16 pending; not S1a acceptance"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-s1a16-assessment.md (pasted by the owner, verbatim)
  sha256: 45fb48a9ed88d85b7191318e639b5352655eebb16739536b9e842d5e28fcb82d
  date: 2026-10-25
  quote: "Overall S1-A16 remains pending. ... Prepare the smallest permissible correction"
applies_to:
  - path: /
    revision: 3fd129e946498e180b9f78a13d3f745afb46c638   # run 1 revision X
related: {adrs: [HIO-ADR-0008, HIO-ADR-0010], tasks: [T-0004, T-0005], findings: []}
---

# OD-0039: record S1-A16 run 1 and prepare the smallest correction

## Owner action

The owner ran the §10 fresh-session test at `3fd129e` and graded it preliminarily:
- Claude's answers pass, but complete execution evidence for the release reproduction is needed
  before sign-off.
- Codex's substantive answers pass.
- Codex treated the outstanding T-0004 assignment as actionable. That is a **test-baseline
  issue, not an independent-reviewer failure**.
- **S1-A16 remains pending.**

The owner authorised:
1. recording the transcripts and the assessment unaltered;
2. inspecting the T-0004 assignment without revoking or reinterpreting it;
3. recommending a no-assignment baseline that preserves the harness-0.7 assignment rules;
4. identifying the reproduction evidence;
5. preparing a Codex-only retest instruction and the harness-review record.

## Done under this record

- The transcripts are committed byte-for-byte, and the owner's statement verbatim
  (`docs/history/`).
- The run-1 harness review, `reviews/records/HARNESS-2026-10-25-s1a16-1.md` (result
  `pending`), holds:
  - the setup;
  - the transcript and session-log hashes;
  - the owner's assessment, quoted;
  - the complete Claude reproduction evidence;
  - the T-0004 inspection.
- The session logs and the Claude run's stores are preserved read-only outside the repository.
  JSON and JSON Lines are refused in this public repository. Their sha256 are in the record.

## Finding on T-0004 (inspection only)

- **Active, reviewed, not received.** The owner assignment (OD-0010, OD-0018) stands.
- Codex performed it: `review/t0004-codex` at `db305a3cbfe0b149b25d0cde30a3bb890e70dc39`, READY,
  no finding. Record sha256 `e70bd93d…0a2a`.
- That branch exists only in the owner's local `macsmsf` clone. The staging scope check passes
  (exit 0).
- It is **not obsolete**, and it is not revoked or reinterpreted here.

## The owner decisions this proposes (none is made by this record)

1. **Receive REVIEW-2026-10-18-t0004 into `elusivenode/hio` by a cross-lineage, byte-identical
   import**, as an explicit exception to §6.2 step 5's merge mechanics. OD-0018 anticipated
   "separate handling" for this.
   - A `--no-ff` merge of `db305a3` is **not possible without importing private `macsmsf`
     history into this public repository**.
   - The reviewer commit id is kept by citation and by `macsmsf`'s own ref, not by ancestry.
   - After receipt, the *Assigned reviews* row for T-0004 reads `received`, like the S1a row.
   - Receipt is not T-0004 acceptance and not a `macsmsf` merge.
2. **Accept S1-A16 evidenced across two revisions:** the Claude half at `3fd129e` (run 1) and the
   Codex half at the later revision Y that contains the receipt (run 2).

## What this record does NOT do

- It does not change harness semantics, the implementation, any verified finding, any approved
  standard, or S1a's acceptance state.
- It does not grade, pass or fail S1-A16, and does not accept S1a.
- It does not revoke, reinterpret, receive or accept the T-0004 assignment or review.
- It does not touch Codex's branches or worktrees in either repository.

## Corrections (append-only)

None.
