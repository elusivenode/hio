---
id: OD-0053
title: "Owner disposition, without merge receipt, of VERIFY-2026-10-25-adr0012-1 (e1f60f9) and REVIEW-2026-10-25-harness-0.7.1 (9c51a6b); fixed-head assignments A2 and B2 with a push-only, no-reviewer-PR exception"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-review-disposition-assignments.md (pasted by the owner, verbatim; commit db4cc82cf04a87a74e678c8b778db190a87305cc)
  sha256: 0fd90258c5eb772d9245161db6c0192ef4b738e27545c72a2be11f29af4e2195
  date: 2026-10-25
  quote: "The disposition authorises reliance on the verified immutable evidence for the next bounded verification cycle; it does not waive defects or retrospectively approve an incomplete exception."
applies_to:
  - path: reviews/records/VERIFY-2026-10-25-adr0012-1.md
    revision: e1f60f9e04034c5b9cb21ac8b3c77b93afc516ce   # not merged, not received
  - path: reviews/records/REVIEW-2026-10-25-harness-0.7.1.md
    revision: 9c51a6b2d05ea3751bfa8799ee756b81ca320651   # not merged, not received
related: {adrs: [HIO-ADR-0012, HIO-ADR-0008], tasks: [T-0005], findings: [F-REVIEW-2026-10-25-adr0012-1, F-REVIEW-2026-10-25-adr0012-2, F-REVIEW-2026-10-25-adr0012-3, F-REVIEW-2026-10-25-harness-0.7.1-1, F-REVIEW-2026-10-25-harness-0.7.1-2, F-REVIEW-2026-10-25-harness-0.7.1-3, F-REVIEW-2026-10-25-harness-0.7.1-4]}
---

# OD-0053: disposition of two Codex records; assignments A2 and B2

> **These two records are not merged and not received.** They remain on Codex's pushed branches.
> This record is a **disposition under harness-0.7 §6.2 step 6**, not a receipt.

## Owner action (the verbatim text is in the history file, commit `db4cc82cf04a87a74e678c8b778db190a87305cc`)

1. A **specific owner disposition, without merge receipt**, of `VERIFY-2026-10-25-adr0012-1`
   (reviewer commit `e1f60f9`) and `REVIEW-2026-10-25-harness-0.7.1` (`9c51a6b`).
2. Resolve the complete ids and sha256 values from Git. Confirm each record's assignment, reviewed
   head, reviewer-only scope and inventory against the available owner instructions and independent
   Codex reports. **Preserve any absence as an explicit evidence limitation. Do not reconstruct
   missing owner instructions from reviewer assertions. Stop on an actual discrepancy.**
3. Preserve all open findings and both **REQUEST CHANGES** verdicts. The disposition authorises
   **reliance on the verified immutable evidence for the next bounded verification cycle**. It does
   **not** waive defects or retrospectively approve an incomplete exception.
4. Fixed-head assignments **A2** and **B2**, with the same limited **push-only, no-reviewer-PR**
   exception to harness-0.7. Codex uses separate isolated worktrees, commits and pushes its
   records, and does not merge evidence into `main`.

**Prohibited:** approving ADR-0012 or harness-0.7.1; changing source-rights states; altering
accepted S1a; authorising S1b.

## Identifiers resolved from Git (fresh fetch, 2026-10-25T06:58Z)

| | VERIFY-2026-10-25-adr0012-1 | REVIEW-2026-10-25-harness-0.7.1 |
|---|---|---|
| Reviewer commit (the owner named the abbreviation) | `e1f60f9e04034c5b9cb21ac8b3c77b93afc516ce` | `9c51a6b2d05ea3751bfa8799ee756b81ca320651` |
| Pushed branch whose tip it is | `review/adr0012-verify-1-codex` | `review/harness-0.7.1-codex` |
| Record | `reviews/records/VERIFY-2026-10-25-adr0012-1.md`: blob `6e3848559a0f227224ff44ce91652a65c43ad512`, sha256 `4692c99f021f2ca9a1b965d33e0459495b93479f8ea35553490fa8023375d048` | `reviews/records/REVIEW-2026-10-25-harness-0.7.1.md`: blob `93129fc0e9c84361c4ba8f33c6198ddfef935cce`, sha256 `0b36f97a3e2a7e23853ae76eb21579d4dcbfdf876701aede54526b4d3947b1cd` |
| Handoff | blob `8d6760951b2663f3336f17171ed21e34b92b4e6d`, sha256 `1d6ff8ce454878b32c8886b2e0fd3b9f83bc5f8c92d080bf092777888cf16d72` | blob `c351c42b3f894ab02a6a50461f6648f976296b27`, sha256 `f1f41b84239470b05eb6f61eed1dcd63b38627d72ae9429656351b6ed917218b` |
| Reviewed head (the record's `reviewed_head`) | `860fd7879c6c663980bc4bf037a8c29e8c7df769` | `9878dd0bad6fa61a0ef8519a6d47da7198b08526` |
| Reviewed base | `6fbec1aa064551d7aa505cf3008a677acfd68e73` | `6fbec1aa064551d7aa505cf3008a677acfd68e73` |
| Verdict (preserved) | **REQUEST CHANGES** | **REQUEST CHANGES** |
| Findings (preserved) | F1 and F3 `verified_closed` by Codex as proposed design corrections; **F2 open** | **four findings, all open** |

The hashes equal the ones computed on the previous fetch for OD-0052.

## What was confirmed, and against what

| Item | Confirmed? | Basis |
|---|---|---|
| Reviewer commit identity | **Yes** | the owner named `e1f60f9` and `9c51a6b`. Both resolve uniquely and equal the live tips of the two pushed branches (`git ls-remote`) |
| Reviewed head | **Yes** | in the owner's A2 and B2 text, "previous reviewed head" is `860fd78` and `9878dd0`. Each equals the corresponding record's `reviewed_head` (full ids compared, non-empty). Each record's commit is a direct child of that head |
| Reviewed base | **Yes** | the owner's base `6fbec1a` equals each record's `reviewed_base` and the current `main` |
| Reviewer-only scope | **Yes** | `tools/check_review_branch.sh` from `main` passes for both: one commit each, no merge commits, adding one record and one handoff and modifying `reviews/README.md` |
| File inventory | **From Git only** | three files per commit, as above |
| **Original assignment text** | **No: absent** | see the limitations |
| **Independent Codex report (completion report: tip SHA and file hashes)** | **No: absent** | see the limitations |
| `tools/check_review_assignment.py` | **Not run, on purpose** | the only expected-source string available is the record's own `assignment` field. Using it would be circular (REVIEW-2026-10-25-harness-0.7.1-1) |

**No actual discrepancy was found.** Every value that an owner-authored statement and a Git fact
can both speak to matches.

## Evidence limitations (explicit; nothing reconstructed)

1. **The owner's original assignment text for either review was not supplied to the receiver.**
   The owner's instruction above supplies reviewer commits, reviewed heads and the base, which are
   confirmed. It does **not** supply the assignment's scope text, the review branch names, or the
   delivery terms of the first two reviews. Those are **not** reconstructed from the records'
   `assignment` fields or from Claude's earlier packages (OD-0051), which are reviewer and author
   statements.
2. **No independent file inventory exists.** Each Codex handoff says that the branch tip and the
   record sha256 are in "the reviewer's completion report". **That report has not been supplied.**
   The tips and hashes above are computed from Git alone. The handoffs sit in the same commit as
   the records, so they are not independent of the branch.
3. **The earlier push-only exception rests on Codex's own statements.** Both handoffs say the
   reviews were delivered "under the owner's specific harness-0.7 §6.2 step 3 exception". No
   owner-authored source for that exception is in the repository. The owner's present instruction
   authorises "the same limited push-only, no-reviewer-PR exception" for A2 and B2 only, and says
   the disposition does not "retrospectively approve an incomplete exception". This record does
   not either.
4. **Blob identity is not authentication.** Matching blobs prove content equality with a named
   commit. They do not authenticate who operated the Git account, or prove completeness.

## Disposition

Under harness-0.7, the owner **disposes of the two records without merge receipt**, as follows.

- **What it is.** The records are verified, immutable evidence at the commits above, held on the
  pushed branches. They are **not merged and not received**. No file is imported, no tag is
  created and `main` is not changed by this record.
- **What it authorises.** **Reliance on that verified evidence for the next bounded verification
  cycle only**, which is assignments A2 and B2 below. Claude may read the records with
  `git show <commit>:<path>` and cite their commits and hashes.
- **What it preserves.** Both **REQUEST CHANGES** verdicts. Every open finding stays open: ADR-0012
  F2, and harness-0.7.1 findings 1 to 4. F1 and F3 of ADR-0012 are Codex's verification, which is
  **not** an owner acceptance, and **nothing is waived**.
- **What it does not do.** It does not approve ADR-0012 or harness-0.7.1, receive either record,
  retrospectively approve any incomplete exception (including the push-only delivery of the two
  records, and the OD-0052 reading of §6.2 step 6), or change the review index on `main`. It
  lapses after the A2 and B2 cycle unless the owner renews it.

## Verified assignment records

Every value was re-read from the pushed refs at **2026-10-25T06:58Z**, and must be re-read again
at the moment the assignment is made available to Codex (stop if any differs).

### A2: ADR-0012 F2 verification

| Field | Value (owner's abbreviation, resolved from Git) | Verified |
|---|---|---|
| ID | `VERIFY-2026-10-25-adr0012-2` | no such record or branch exists yet |
| Base | `6fbec1aa064551d7aa505cf3008a677acfd68e73` | equals `main` on the remote |
| Reviewed head | `d0965ccfd37a0ddefdbb5ff08a11674c3267792a` | equals the tip of `docs/adr0012-staged-s1b-proposal` (PR #4, open); descends from `main` |
| Previous reviewed head | `860fd7879c6c663980bc4bf037a8c29e8c7df769` | is an ancestor of the new head; equals VERIFY-2026-10-25-adr0012-1's reviewed head |
| Review branch | `review/adr0012-verify-2-codex` | does not exist on the remote |
| Delivery | push-only, no reviewer PR | owner-authorised in the history file |

### B2: harness-0.7.1 verification

| Field | Value (owner's abbreviation, resolved from Git) | Verified |
|---|---|---|
| ID | `VERIFY-2026-10-25-harness-0.7.1-1` | no such record or branch exists yet |
| Base | `6fbec1aa064551d7aa505cf3008a677acfd68e73` | equals `main` on the remote |
| Reviewed head | `8ed13fdef8537b846afb7e60b14807417b2f3c0d` | equals the tip of `docs/harness-0.7.1-review-receipt`; descends from `main`; no PR |
| Previous reviewed head | `9878dd0bad6fa61a0ef8519a6d47da7198b08526` | is an ancestor of the new head; equals REVIEW-2026-10-25-harness-0.7.1's reviewed head |
| Review branch | `review/harness-0.7.1-verify-1-codex` | does not exist on the remote |
| Delivery | push-only, no reviewer PR | owner-authorised in the history file |

### Copy-ready assignment text for Codex

The **owner-authored source** is the history file at commit `db4cc82cf04a87a74e678c8b778db190a87305cc` on the pushed branch
`docs/od0053-disposition-assignments`. The expected values below are taken from it.

> **Assignment A2.** Review id `VERIFY-2026-10-25-adr0012-2`. Repository `elusivenode/hio`. Base
> `6fbec1aa064551d7aa505cf3008a677acfd68e73`. Reviewed head `d0965ccfd37a0ddefdbb5ff08a11674c3267792a`.
> Previous reviewed head `860fd7879c6c663980bc4bf037a8c29e8c7df769`. Review branch
> `review/adr0012-verify-2-codex`. **Scope:** independently test the remaining F2 finality-evidence
> defect, including forged, missing, failed, delayed, stale and inconsistent capture-completion
> evidence. Examine the seven checks and the boundary between replayable records and trusted adapter
> assertions. Confirm F1 and F3 are not regressed, and that Q-013 and the release-manifest questions
> are not silently resolved.
>
> **Assignment B2.** Review id `VERIFY-2026-10-25-harness-0.7.1-1`. Repository `elusivenode/hio`.
> Base `6fbec1aa064551d7aa505cf3008a677acfd68e73`. Reviewed head
> `8ed13fdef8537b846afb7e60b14807417b2f3c0d`. Previous reviewed head
> `9878dd0bad6fa61a0ef8519a6d47da7198b08526`. Review branch `review/harness-0.7.1-verify-1-codex`.
> **Scope:** independently verify the four findings, testing owner-assignment provenance, complete
> reviewer inventory, finding-index semantics, remote-tip checks, tag publication and recovery. Test
> against the actual previous review-index changes as well as adversarial examples.
>
> **For both:** push-only, no reviewer PR (a limited exception to harness-0.7 step 3). Use a
> separate isolated worktree for each. Write only `.md` files under `reviews/`. Commit and push the
> records. Do not merge evidence into `main`. Stop if the branch tip of the reviewed head differs
> from the value above.

**Suggested strings for the record's `assignment` field** (they contain the commit of the
owner-authored source, so a later receiver can compare them with something that is not the record):

- A2: `owner direct instruction to Codex, 2026-10-25, VERIFY-2026-10-25-adr0012-2, base 6fbec1aa064551d7aa505cf3008a677acfd68e73, head d0965ccfd37a0ddefdbb5ff08a11674c3267792a, verbatim in docs/history/2026-10-25-owner-review-disposition-assignments.md at commit db4cc82cf04a87a74e678c8b778db190a87305cc`
- B2: `owner direct instruction to Codex, 2026-10-25, VERIFY-2026-10-25-harness-0.7.1-1, base 6fbec1aa064551d7aa505cf3008a677acfd68e73, head 8ed13fdef8537b846afb7e60b14807417b2f3c0d, verbatim in docs/history/2026-10-25-owner-review-disposition-assignments.md at commit db4cc82cf04a87a74e678c8b778db190a87305cc`

**Suggested addition, not in the owner's text** (the owner may include it): in its final message,
each reviewer states its branch tip SHA and the sha256 of every file it added. That is the
independent report that a later receipt needs, and its absence is the limitation recorded above.

## Remaining decisions for the owner

1. **Receipt of the records.** Neither record is received, and the A2 and B2 records will also be
   unreceived. A byte-identical import needs its own one-off authorisation until harness-0.7.1 is
   approved, and VERIFY-2026-10-25-adr0012-1's index change **rewrites three finding rows**, which
   the approved harness-0.7 does not address and harness-0.7.1 revision 2 would refuse.
2. **Supply, if they exist,** the original assignment texts and Codex's completion reports, so
   that the limitations above can be closed by evidence instead of staying open.
3. **Relay the assignments to Codex** (the copy-ready text), or tell me where to place it. Nothing
   has been sent to Codex from here.
4. **Whether to merge the branch** `docs/od0053-disposition-assignments` (records only) into
   `main`. The assigned heads do not depend on it.
5. **Unchanged and open:** approval of ADR-0012 and harness-0.7.1, Q-013, the release-manifest
   question, and S1b.

## What this record does NOT do

- It does **not** merge or receive either record, create a tag, or change `main`.
- It does **not** approve ADR-0012 or harness-0.7.1, close or waive any finding, verify any source
  right, alter accepted S1a, or authorise S1b.
- It does **not** contact Codex.

## Corrections (append-only)

None.
