---
id: OD-0109
title: "Owner authorises the narrowed H6 recovery approach (draft clarification, worker fix, response 6), the receipt of VERIFY-2026-10-28-h6-1-5, and a Codex correction of its test plan's missing front matter before receipt; nothing approved or activated"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-narrow-recovery-and-correction.md (owner's messages AA and AB, verbatim, with Claude's decisions)
  sha256: ed8b54b0d1235c4540e0cd5ab3dd7b02112b64488e7290c6f0fc1259877618dd
  date: 2026-10-29
  quote: "yes to all (AA); yes (AB)"
applies_to:
  - path: review/h6-1-verify-5-codex
    revision: 409cc71ad87be7c6f67b05020407c19c5c8cb1cc   # T, tagged, not received
  - path: phase-b/h6
    revision: 5e1582934e1ef88198ff59ffd7b8c947c1ba693b   # base of the narrowed fix
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [F-VERIFY-2026-10-28-h6-1-4-1, F-VERIFY-2026-10-28-h6-1-5-1], ods: [OD-0092, OD-0104, OD-0107, OD-0108]}
---

# OD-0109: narrowed H6 recovery; verification 5 corrected before receipt

## Basis

Verifications 3, 4 and 5 each closed one finding and opened another in the same place: a rerun when an import of T
already exists on local `main`. The architect (consultation `20261029T103714-ask-15f7`, summarised to the owner;
advice only) advised narrowing: publish only a receipt built in the same invocation from a freshly fetched remote
`main`, and stop on a pre-existing unpublished import or merge. §6.2 can stay unchanged; the H6 design wording should
state the limit, which needs the owner's adoption at an exact revision.

## Authorised (message AA)

1. **The narrowed approach:**
   - the design clarification drafted on `proposal/harness-0.9` (`6d3fe3c`, local; **proposed, not adopted**);
   - one Sonnet worker (hiomux task W3) on `phase-b/h6` from `5e15829`, limited to `tools/hio_receive.py` and
     `tests/test_hio_receive.py`;
   - Claude's check and integration, and response 6.
2. **Receipt of VERIFY-2026-10-28-h6-1-5.** It stopped at 5.7 (below).

## The stop (5.7) and the correction (message AB)

| Step | Result |
|---|---|
| 5.1 | `ls-remote` = fetch = reported tip = `409cc71ad87be7c6f67b05020407c19c5c8cb1cc` |
| 5.2 | three added files (record, report, handoff), each matching its reported sha256; README unchanged |
| 5.3 | `check_review_branch.sh` PASS; `check_review_assignment.py` PASS ("…OD-0108-assign-h6-verification-5.md on main") |
| 5.4 | tag `reviews/VERIFY-2026-10-28-h6-1-5` pushed; peels to `409cc71` |
| 5.7 | **`tools/check_repo.py` FAIL:** `reviews/reports/2026-10-29-h6-1-verify-5-test-plan.md: no front matter`. Stopped. A local merge made before the failure was seen was reset; nothing reached `main` |

**The correction assignment (this OD is its owner-authored source).** One Codex run under OD-0108's assignment, on
`review/h6-1-verify-5-codex` from `409cc71`:
- add YAML front matter to `reviews/reports/2026-10-29-h6-1-verify-5-test-plan.md` only, with exactly
  `id: VERIFY-2026-10-28-h6-1-5-TEST-PLAN` and `status: fixed_before_author_response`, as the earlier test plans have;
- change nothing else: the record, the handoff and the report's body are byte-unchanged;
- report each file's sha256 as usual.

**Receipt of the corrected tip:** by §6.2 step 5, under a new tag `reviews/VERIFY-2026-10-28-h6-1-5-c1`. The tag
`reviews/VERIFY-2026-10-28-h6-1-5` stays at `409cc71` (never moved or deleted): **pinned, not received**. The receipt,
its §5.12 reconciliation and the push of `main` are recorded in a following OD.

## Not authorised

Adopting the design clarification; pushing `phase-b/h6` or `proposal/harness-0.9`; verification 6; H6 approval or
activation.

## Corrections (append-only)
