---
id: OD-0052
title: "Owner instruction: bounded remediation of VERIFY-2026-10-25-adr0012-1 (F2 only) and REVIEW-2026-10-25-harness-0.7.1 (four findings), under the remediation-before-receipt exception; both records preserved unchanged; receipt still outstanding"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-adr0012-f2-harness-0.7.1-corrections.md (pasted by the owner, verbatim)
  sha256: 1b08e9b5544da9a81cd4a6860d0715c0f803b2aa3649b7bebb5f6c163bd83232
  date: 2026-10-25
  quote: "Preserve the records unchanged. Complete the harness-0.7 receipt or explicitly authorised evidence-disposition prerequisites before remediation. Stop if verification fails or an exception beyond existing authority is needed."
applies_to:
  - path: reviews/records/VERIFY-2026-10-25-adr0012-1.md
    revision: e1f60f9e04034c5b9cb21ac8b3c77b93afc516ce   # Codex branch review/adr0012-verify-1-codex; blob 6e3848559a0f227224ff44ce91652a65c43ad512
  - path: reviews/records/REVIEW-2026-10-25-harness-0.7.1.md
    revision: 9c51a6b2d05ea3751bfa8799ee756b81ca320651   # Codex branch review/harness-0.7.1-codex; blob 93129fc0e9c84361c4ba8f33c6198ddfef935cce
related: {adrs: [HIO-ADR-0012, HIO-ADR-0008], tasks: [T-0005], findings: [F-REVIEW-2026-10-25-adr0012-2, F-REVIEW-2026-10-25-harness-0.7.1-1, F-REVIEW-2026-10-25-harness-0.7.1-2, F-REVIEW-2026-10-25-harness-0.7.1-3, F-REVIEW-2026-10-25-harness-0.7.1-4]}
---

# OD-0052: ADR-0012 F2 and harness-0.7.1 bounded corrections

## Owner action (summary; the verbatim text is in the history file)

1. **Resolve and verify** both records directly from the pushed Codex branches: the reviewer
   commits, complete record sha256 values, original assignments, reviewer-only scope, submitted
   heads. **Preserve the records unchanged.**
2. **Complete the harness-0.7 receipt, or the explicitly authorised evidence-disposition
   prerequisites, before remediation.** Stop if verification fails or an exception beyond existing
   authority is needed.
3. **A. ADR-0012, F2 only.** Define the minimum credible provenance for a successful post-window
   capture. F1 and F3 are not reopened. Q-013 and the release-manifest question stay unresolved.
4. **B. Harness-0.7.1, four findings.** Revise the proposal: the actual owner assignment and an
   independent evidence inventory; index-row semantics checked against the immutable records;
   remote SHA parsing and a final tip recheck; provenance tags published and verified before
   receipt, with a recovery path.
5. Submit both new fixed heads for scoped Codex verification, with proposed assignments.

**Prohibited:** approving ADR-0012 or harness-0.7.1; verifying any source right; changing
accepted S1a; merging PR #4; authorising S1b. **Escalate only** genuine changes to approved
standards, scope or the trust model.

## Evidence resolved from Git (all verified 2026-10-25)

Both branches were fetched from `origin` into a scratch clone. Each is **one commit, directly on
the assigned head**. `git ls-remote` re-read both tips at verification.

| | VERIFY-2026-10-25-adr0012-1 | REVIEW-2026-10-25-harness-0.7.1 |
|---|---|---|
| Branch | `review/adr0012-verify-1-codex` | `review/harness-0.7.1-codex` |
| Reviewer commit (the tip) | `e1f60f9e04034c5b9cb21ac8b3c77b93afc516ce` | `9c51a6b2d05ea3751bfa8799ee756b81ca320651` |
| Parent = the assigned head | `860fd7879c6c663980bc4bf037a8c29e8c7df769` (PR #4's submission head) | `9878dd0bad6fa61a0ef8519a6d47da7198b08526` (the pushed harness head) |
| Record | `reviews/records/VERIFY-2026-10-25-adr0012-1.md`: blob `6e3848559a0f227224ff44ce91652a65c43ad512`, sha256 `4692c99f021f2ca9a1b965d33e0459495b93479f8ea35553490fa8023375d048`, 6667 bytes | `reviews/records/REVIEW-2026-10-25-harness-0.7.1.md`: blob `93129fc0e9c84361c4ba8f33c6198ddfef935cce`, sha256 `0b36f97a3e2a7e23853ae76eb21579d4dcbfdf876701aede54526b4d3947b1cd`, 11025 bytes |
| Handoff | `reviews/handoffs/2026-10-25-adr0012-verify-1-codex.md`: blob `8d6760951b2663f3336f17171ed21e34b92b4e6d`, sha256 `1d6ff8ce454878b32c8886b2e0fd3b9f83bc5f8c92d080bf092777888cf16d72` | `reviews/handoffs/2026-10-25-harness-0.7.1-codex.md`: blob `c351c42b3f894ab02a6a50461f6648f976296b27`, sha256 `f1f41b84239470b05eb6f61eed1dcd63b38627d72ae9429656351b6ed917218b` |
| Files changed vs the assigned head | `A` record, `A` handoff, `M reviews/README.md` | `A` record, `A` handoff, `M reviews/README.md` |
| `tools/check_review_branch.sh` (the copy on `main`) | PASS | PASS |
| Record's `assignment`, `reviewed_base`, `reviewed_head`, `review_branch` | agree with the values in OD-0051 Package A | agree with the values in OD-0051 Package B |
| Verdict | **REQUEST CHANGES**: F1 and F3 **verified closed**; F2 **open** | **REQUEST CHANGES**: four findings open |

## What could not be verified: absent evidence, reported

- **The owner's actual assignment text for either review was not supplied to the receiver.** The
  only assignment evidence available is each record's own `assignment` field, which cites "owner
  direct instruction to Codex, 2026-10-25", and the packages I proposed in OD-0051. The values
  agree, but **that comparison uses the reviewer's own statement and my own proposal, not the
  owner-authored source.** The harness record states that the owner assigned its review "with a
  push-only exception"; that exception exists only in Codex's record, not in an OD.
- **The reviewers' independent reports (final messages with tip SHA and file hashes) were not
  supplied.** The tips and hashes above were computed from Git alone.
- This is the gap that `F-REVIEW-2026-10-25-harness-0.7.1-1` describes. It is reported here, not
  papered over.

## Why the receipt is not performed now, and what is used instead

- **A harness-0.7 receipt cannot be completed.** Step 5 merges a reviewer PR. Each branch descends
  from an **unmerged proposal** (PR #4's ADR-0012; the harness proposal), so a merge would
  integrate unapproved work, which the owner's instruction also forbids. Codex opened no PR.
- **A byte-identical import would be a new exception.** OD-0050 authorised the import for
  REVIEW-2026-10-25-adr0012 only, as a specific one-off. The harness-0.7.1 procedure that would
  govern these imports is the proposal under review, with four open findings. One concrete
  consequence: **VERIFY-2026-10-25-adr0012-1's index change removes and rewrites three existing
  finding rows** (their state cells), which the revision-2 rule "adds only lines, removes none"
  would refuse.
- **So the existing, approved route is used:** the harness-0.7 §6.2 step 6 *remediation before
  receipt* exception. The owner's instruction is explicit and names both review ids; the commits
  and sha256 values above were resolved and verified from Git, as the instruction asked. Claude
  reads each record **only** with `git show <commit>:<path>`, has checked the hashes before relying
  on it, and cites commit and hashes in each remediation response. Nothing is imported into
  `main` and nothing in `reviews/records/` changes.
- **Still owed, by the owner, before the next verification is assigned:** each record must be
  **received, or its disposition recorded** (§6.2 step 6). The options are in the report.
- **One caution on this reading.** Step 6 says the exception "never applies by inference". The
  instruction did not itself list the commit and hashes; the owner asked me to resolve and verify
  them. I treat that as explicit. **If the owner disagrees, the remediation heads stay unassigned
  and nothing else has changed.**

## Assignment packages (for owner confirmation; neither is an assignment until the owner issues it)

The heads are the commits that add each remediation response. They are stated in the owner-facing
report and in the PR comment, because a file cannot contain its own commit id.

### Package A2: scoped verification of ADR-0012, F2 only

| Field | Value |
|---|---|
| Verification id | `VERIFY-2026-10-25-adr0012-2` |
| Repository | `elusivenode/hio` |
| Base SHA | `6fbec1aa064551d7aa505cf3008a677acfd68e73` (`main`) |
| Head SHA | the PR #4 head that adds `reviews/responses/RESPONSE-REVIEW-2026-10-25-adr0012-2.md` (stated in the report) |
| Previous verified head | `860fd7879c6c663980bc4bf037a8c29e8c7df769` |
| Review branch | `review/adr0012-verify-2-codex` |
| Delivery | as the owner decides (push-only pilot, or harness-0.7) |
| Scope | **F-REVIEW-2026-10-25-adr0012-2 only.** Replay the forged `verified_unchanged` counterexample and the missing, failed, delayed, inconsistent and unverified cases against §4.3.3–§4.3.4. Check C1–C7 for gaps (a forgery that passes all seven; a check that is too weak or incoherent, for example the use of `Date` with caches or the provider write time). Check that the trust statement is honest and that no second bookkeeping system is introduced. **Regression check only** for F1 and F3: the diff against `860fd78` outside §4.3.3, §4.3.4 and the listed consequential lines must be empty. Out of scope: Q-013, the manifest question, rights |

### Package B2: scoped verification of harness-0.7.1, four findings

| Field | Value |
|---|---|
| Verification id | `VERIFY-2026-10-25-harness-0.7.1-1` |
| Repository | `elusivenode/hio` |
| Base SHA | `6fbec1aa064551d7aa505cf3008a677acfd68e73` (`main`) |
| Head SHA | the head of `docs/harness-0.7.1-review-receipt` that adds `reviews/responses/RESPONSE-REVIEW-2026-10-25-harness-0.7.1-1.md` (stated in the report) |
| Previous reviewed head | `9878dd0bad6fa61a0ef8519a6d47da7198b08526` |
| Review branch | `review/harness-0.7.1-verify-1-codex` |
| Delivery | as the owner decides |
| Scope | **F-REVIEW-2026-10-25-harness-0.7.1-1 to -4.** For each, write the failure scenario yourself and run it against the revised §4 step 5. Test the new index-row semantics against **real diffs**: VERIFY-2026-10-25-adr0012-1's rewrite of three finding rows, and the harness record's added rows. Check that byte-identical import, exact Git provenance, the ban on importing unapproved ancestry and stop-on-mismatch are preserved, and that delegation to Claude stays inside verified assignment and scope. Out of scope: approving the amendment, `tools/` and `.github/` changes |

## What this record does NOT do

- It does **not** receive either record, merge any branch, or change `reviews/records/`.
- It does **not** approve ADR-0012 or harness-0.7.1, close or waive any finding, verify any right,
  change accepted S1a, merge PR #4 or authorise S1b.
- It does **not** decide Q-013 or the release-manifest question.

## Corrections (append-only)

None.
