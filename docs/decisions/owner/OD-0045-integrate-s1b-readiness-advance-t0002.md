---
id: OD-0045
title: "Owner instruction: integrate the S1b readiness assessment (--no-ff, status kept as prepared); continue T-0002 for RBA and NY Fed with limited manual inspection; prepare a staging recommendation"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-integrate-s1b-readiness-t0002.md (pasted by the owner, verbatim)
  sha256: d55b6895cc65e7144f210023f830b7f2f305475ad712fdd12a86341281793343
  date: 2026-10-25
  quote: "I authorise limited manual inspection of publicly accessible primary-source documentation and sample data only where the applicable rights permit it."
applies_to:
  - path: /
    revision: 1f5e5e29960ecb0bd07fa82f68e312b4cc80664b   # main before integration
  - path: docs/evidence/S1B-readiness-assessment.md
    revision: 569753a   # integrated by merge a37d81f
related: {adrs: [HIO-ADR-0005, HIO-ADR-0010], tasks: [T-0002, T-0005], findings: []}
---

# OD-0045: integrate the readiness assessment; continue T-0002

## Owner action

1. **Commit and integrate** the S1b readiness assessment, after verifying its scope against
   `main`. Use a `--no-ff` merge, and keep the report's status as proposed.
2. **Continue T-0002**, in this priority order:
   - the RBA cash rate and AUD/USD, as distinct datasets;
   - NY Fed SOFR and the SOFR Index;
   - primary-source evidence of the permitted operations;
   - timing, calendars, revisions and the AUD cash-rate regime.
3. **Limited manual inspection** of public primary-source documentation and sample data,
   **only where the rights permit**. Record access dates, URLs, terms and uncertainties. No
   automated ingestion, and no retention where rights are unknown.
4. **An evidence-based staging recommendation**, covering HIO-ADR-0010 rev 3 and the three
   approved triangulations.

**Prohibited by the instruction:**
- implementing S1b;
- creating credentials or infrastructure;
- scheduling capture;
- contacting vendors;
- treating any permission as verified without owner review.

## Execution

**Integration.**
- Scope check: `main` = `origin/main` = `1f5e5e2`; the branch differed only in documentation;
  `git diff --quiet` over `src tests tools specs .github pyproject.toml uv.lock docs/standards
  docs/harness AGENTS.md docs/decisions/HIO-ADR-* reviews registers` exited 0; no existing OD
  changed.
- Commit `569753a`, merged `--no-ff` as `a37d81f`, with a tree equal to the branch's. The
  report keeps `status: prepared_for_owner`.
- Not pushed under this record. `main` at `a37d81f` was pushed later, under OD-0046, after it was re-verified unchanged.

**T-0002.** The evidence is in
[`docs/research/T-0002-rba-nyfed-evidence-2026-10-25.md`](../../research/T-0002-rba-nyfed-evidence-2026-10-25.md).
- The manual samples were held only in the session scratchpad and **deleted** the same session.
- No value is recorded in the repository.
- `registers/sources.yaml` gains evidence pointers and dataset notes only. Every permission
  stays `unknown`, and `verification: unverified`.

## What this record does NOT do

- It does **not** verify any permission, lift OD-0013, or authorise S1b or any stage of it.
- It does **not** approve the staging recommendation or amend HIO-ADR-0010.
- It does **not** authorise contacting the RBA, LSEG, ASX or any other party.

## Corrections (append-only)

None.
