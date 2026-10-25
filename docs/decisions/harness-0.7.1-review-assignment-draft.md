---
id: HIO-HARNESS-0.7.1-REVIEW-ASSIGNMENT-DRAFT
title: "Draft Codex review assignment for the harness-0.7.1 package, for the owner to issue or amend"
status: draft   # NOT an assignment. Only an owner-authored source assigns a review (operating model §6.2 step 1)
owner: owner (assigns); drafted by claude/implementation-agent
created_at: 2026-10-25
drafted_under: OD-0050
---

# Draft review assignment: harness-0.7.1

> **Not an assignment.** A reviewer must not treat this file as its target. The owner may adopt
> it in one owner-authored source (an *Assigned reviews* row, an owner PR comment, or a direct
> instruction). The head cannot be written here, because a file cannot contain its own commit id.

## Proposed assignment values

| Field | Proposed value |
|---|---|
| Review id | `REVIEW-2026-10-25-harness-0.7.1` |
| Repository | `elusivenode/hio` |
| Base SHA | `6fbec1aa064551d7aa505cf3008a677acfd68e73` (`main`, pushed) |
| Head SHA | the tip of branch `docs/harness-0.7.1-review-receipt` when the owner assigns it, resolved with `git rev-parse docs/harness-0.7.1-review-receipt` and stated in the owner's assignment. It is fixed, and never rebased or force-pushed during the review |
| Review branch | `review/harness-0.7.1-codex`, cut at the head |
| Reviewer | Codex, independent reviewer |
| Delivery | **push the review branch; open no PR** — only if the owner authorises this as a pilot exception to harness-0.7 step 3. Otherwise harness-0.7 applies |
| Writes allowed | `.md` files under `reviews/` only |

## Scope

**Subject (read-only):** `docs/decisions/harness-0.7.1-proposal.md` (§3 and §4 hold the exact
replacement text).

**Reference (approved):**
- `docs/harness/operating-model.md` §6.2 and §1.1, harness-0.7;
- `tools/check_review_branch.sh` and `tools/check_review_assignment.py`;
- OD-0021, OD-0040 (the T-0004 byte-identical cross-lineage receipt);
- OD-0050 (the PR #5 receipt, the first manual run of the procedure).

**Questions** (answer each with file and line references; build counterexamples, do not just read):

1. **Integrity preserved.** Does every guarantee of harness-0.7 §6.2 survive: the single
   owner-authored assignment, the fixed head, reviewer-only scope, record immutability,
   assignment verification, and stop-on-mismatch?
2. **No unaccepted integration.** Can the §4 receipt procedure put any commit, or any file
   outside `reviews/`, onto `main`? Try adversarial branches: a middle commit that touches
   another path and is reverted; a `README` hunk that removes or rewrites a row; a symlink or
   executable; a rename; a branch tip that moves between fetch and import; a tag that already
   exists or is moved.
3. **Byte preservation versus ancestry.** Does the package state accurately what blob identity
   and the annotated tag prove, and what is lost by not having the reviewer's commit as an
   ancestor of `main`? Is anything claimed that the mechanism does not give?
4. **Delegated receipt.** Do the delegation conditions in §3 leave any owner-only action
   (acceptance, waiver, closing a finding, integrating the work, a scope change) implicit or
   reachable by the receiver? Is "receipt is not acceptance" preserved?
5. **Receiver independence.** Where the receiver is the author of the work under review, do the
   safeguards (blob identity, the reachable branch and tag, the reviewer-stated tip and sha256)
   make a silent alteration or omission detectable? What residual risk remains?
6. **Consistency.** Does the amendment conflict with other operating-model text (§3 records, §6.1
   provenance, step 6 including the remediation-before-receipt exception, step 7 verification,
   the dormant `pull_request_target` workflow, `tools/check_review_assignment.py`'s descent
   check)? Is the replacement text complete and exact?
7. **Execution against the PR #5 receipt.** Compare OD-0050 and the receipt commit `eadda1e`
   with §4: does the recorded execution match the procedure, and what should the procedure
   change in the light of it?

**Out of scope:** approving harness-0.7.1; changing `tools/` or `.github/`; HIO-ADR-0012 and its
findings; any rights value.

**Output:** a verdict (`READY`, `READY WITH CONDITIONS` or `REQUEST CHANGES`), findings as
`F-REVIEW-2026-10-25-harness-0.7.1-N` with failure scenarios, and — in the final message — the
branch tip SHA and the sha256 of each file added, so that the receiver can compare them with its
own verification (§4, receiver independence).
