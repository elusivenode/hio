---
id: OD-0057
title: "Owner disposition D0: Codex records e1f60f9 and 9c51a6b preserved as explicitly disposed but unreceived; integration, verification and the supervised first receipt (A2, dac54f5) authorised up to the owner's go-ahead"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-adr0012-harness-0.7.1-approval.md (pasted by the owner, verbatim; Decision 3 and Execution)
  sha256: 53b1b54d14a59f9bcab28dfea7698fb24e1c0fe6a76c95cb963a44487b1ac90d
  date: 2026-10-25
  quote: "Preserve the earlier Codex records `e1f60f9` and `9c51a6b` as explicitly disposed but unreceived, with their provenance limitations recorded. Do not infer missing assignment or independent inventory evidence."
applies_to:
  - path: reviews/records/VERIFY-2026-10-25-adr0012-1.md
    revision: e1f60f9e04034c5b9cb21ac8b3c77b93afc516ce   # branch review/adr0012-verify-1-codex; disposed, unreceived
  - path: reviews/records/REVIEW-2026-10-25-harness-0.7.1.md
    revision: 9c51a6b2d05ea3751bfa8799ee756b81ca320651   # branch review/harness-0.7.1-codex; disposed, unreceived
related: {adrs: [HIO-ADR-0012], tasks: [], findings: [F-REVIEW-2026-10-25-adr0012-1, F-REVIEW-2026-10-25-adr0012-2, F-REVIEW-2026-10-25-adr0012-3, F-REVIEW-2026-10-25-harness-0.7.1-1, F-REVIEW-2026-10-25-harness-0.7.1-2, F-REVIEW-2026-10-25-harness-0.7.1-3, F-REVIEW-2026-10-25-harness-0.7.1-4]}
---

# OD-0057: disposition D0 and the controlled receipt sequence

## Owner action

**Decision 3.** Preserve the earlier Codex records `e1f60f9` and `9c51a6b` as **explicitly disposed
but unreceived**, with their provenance limitations recorded. Do not infer missing assignment or
independent inventory evidence. Preserve all findings and their independently verified technical
dispositions.

**Execution** (verbatim in the history file): verify from Git, record the decisions separately,
make status-only approval edits, integrate the **author** branches by controlled `--no-ff` merges
without merging any reviewer branch, verify that nothing but authorised documentation and harness
changes differs, prepare the first harness-0.7.1 receipt using A2 (`dac54f5`), obtain Codex's
independent full evidence inventory (**not** Git-computed hashes in its place), run the prescribed
dry run in isolation, present its checks, transcript and discrepancies **before** pushing to
`main`, and **stop for the owner's explicit go-ahead**.

## Disposition D0 as adopted

| Record (reviewer commit) | Disposition | Limitation, recorded and not cured |
|---|---|---|
| VERIFY-2026-10-25-adr0012-1 (`e1f60f9`) | **disposed, unreceived.** Pinned on a provenance tag; no import. Not retrospectively approved as a delivery route | no owner-authored assignment source (OD-0053 limitation); no reviewer completion report with sha256 values; its index diff does not apply to `main` or PR #4's head |
| REVIEW-2026-10-25-harness-0.7.1 (`9c51a6b`) | **disposed, unreceived.** Same treatment | no owner-authored assignment source (OD-0053 limitation); no reviewer completion report with sha256 values |

- This adopts the package's D0 option 3(a). The one-off, disposition-bound import (option 3(b)) is
  **not** adopted.
- **Findings are preserved with their independently verified technical dispositions** (OD-0054):
  adr0012-1 and -3 closed at `860fd78`, adr0012-2 at `d0965cc`, harness-0.7.1-1…-4 at `8ed13fd`,
  conditions intact. Nothing is waived.
- **Consequence to carry forward:** the index cannot yet show the chain through `9c51a6b` and
  `e1f60f9` by import. Any index row that depends on them is a matter for the owner; the receiver
  must **not** manufacture an input to fill it. If receipt of A2 or B2 needs rows these records
  would define, the run **stops** and reports (stop condition, harness-0.7.1 §6.2).
- **Not retrospectively approved:** the push-only delivery of the first two reviews, or OD-0052's
  reading of §6.2 step 6.

## First receipt: A2 and the independent inventory

The operating model requires the reviewer's own final-message report (branch, tip SHA, reviewed
head, sha256 of each added file). **That report for A2 has not been supplied.** The owner has
supplied the branch name, the commit prefix `dac54f5` and the verdict; the full SHA and hashes
were computed from Git (OD-0054). Per the owner's instruction these are **not** substituted for the
report: the receipt waits for Codex's inventory. No review is initiated for it.

## What this record does NOT do

- It does not approve source rights, authorise S1b, modify accepted S1a, resolve Q-013 or change
  the release-manifest schema.
- It does not receive, import or merge any record, and does not push to `main`.
- It does not enable routine delegated receipt (OD-0056).

## Corrections (append-only)

None.
