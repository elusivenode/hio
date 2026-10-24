---
id: OD-0037
title: "Owner authorisation: integrate PR #2 at reviewed head 084154c, then receive the S1a verification evidence (VERIFY-2026-10-24-s1a-1-1 to -11); not S1a acceptance"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  - source: docs/history/2026-10-25-owner-receive-verify-11-acceptance-prep.md (pasted by the owner, verbatim)
    sha256: e77de82598ca6ff97aa5b586d7396f9339aeab7be7ace4b185536fe793c6144d
    quote: "I authorise receipt of the round-11 Codex review evidence and preparation of the S1a acceptance package, subject to the existing harness-0.7 integrity checks."
  - source: docs/history/2026-10-25-owner-integrate-pr2-receive-evidence.md (pasted by the owner, verbatim)
    sha256: a0f8e0653f69ea451f2982835b03a547303f5d5b24ea1d8f57c1f43f86ccbd60
    quote: "I approve the integration-first route under the existing harness-0.7 procedure."
applies_to:
  - path: /
    revision: 084154ccb0fd1c13150d77d02eb525007a5b161e   # PR #2 head verified by VERIFY-2026-10-24-s1a-1-11
related: {adrs: [HIO-ADR-0010], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-1, F-REVIEW-2026-10-24-s1a-1-2, F-REVIEW-2026-10-24-s1a-1-3, F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-5, F-REVIEW-2026-10-24-s1a-1-6, F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0037: integrate PR #2, then receive the S1a verification evidence

## Why integration came first

Every S1a reviewer branch descends from a PR #2 head. Receipt under harness-0.7 §6.2 step 5 is a
`--no-ff` merge that keeps reviewer commit ids, so receiving any of them before PR #2 would have
merged unreviewed-for-integration implementation history into `main`. Receiving the first
instruction alone was therefore blocked. The second instruction chose to integrate PR #2 at the
reviewed head first, then receive.

## Checks performed before merging (all passed)

| Check | Result |
|---|---|
| PR #2 head | `084154ccb0fd1c13150d77d02eb525007a5b161e` (open, `Submission-Head` equal); CI push `40139197232` and PR `40139203000`, attempt 1, success |
| `main` before | `6fe35cf6f85ec421ec6f8d67acc04134f2bdbd39`, an ancestor of `084154c`, so the merge tree equals the reviewed tree |
| Reviewer branches V1–V11 | for each: the record commit, the record's SHA-256 (also equal at the branch tip), `reviewed_head` an ancestor of `084154c`, `check_review_branch.sh` exit 0, `check_review_assignment.py` exit 0. Each SHA-256 equals the value cited when the record was first relied on (OD-0024/0025/0026/0031–0036 and responses 2–11; V11 checked against the owner's instruction naming `cd94ca5`) |
| Isolated rehearsal | PR #2 merge, then V1–V11 `--no-ff`. Tree after PR #2 = `084154c`; every reviewer tip an ancestor of the result (ids kept); nothing outside `reviews/` differs from `084154c`; record bytes unchanged; `check_repo` 0; pytest 278 passed |
| Conflict | one: V1 also edited `reviews/README.md` rows that PR #2 later rewrote. Resolved by keeping the PR #2 index and applying V1's own additions (its verification row; its cells for F1, F2, F3, F5 and F6). The record files did not conflict |

## Owner action

1. **Integration:** PR #2 merged `--no-ff` at `084154c`: merge commit
   `773a557534280ca7a19ce69a16394343f73e2139`, whose tree equals `084154c`.
2. **Receipt:** V1–V11 received `--no-ff` with reviewer commit ids kept (receipt commits in
   `STATUS.md` and the review index). PR #3 (V1) is received by its branch's merge, not merged
   blindly.
3. **Records:** the review index shows F1–F7 verified closed at their reviewed revisions; STATUS
   separates technical verification, integration, receipt and acceptance; the S1-A1..A15 evidence
   matrix is prepared.

## What this record does NOT do

- It does **not** accept S1a, approve observations v0.3, authorise S1b, or change any approved
  standard or ADR. Receipt means the evidence is received, not that its conclusions are accepted
  (§6.2 step 5). Final acceptance is a separate owner record.
