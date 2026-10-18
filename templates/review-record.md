---
id: REVIEW-<yyyy-mm-dd>-<subject>
subject: <task, ADR, spec or release id>
reviewer: codex/reviewer      # or a human reviewer; never the author
reviewed_base: <git sha>
reviewed_head: <git sha>      # the exact revision examined; must equal the owner's assignment
assignment: <reviews/README.md 'Assigned reviews' row, or the owner assignment source>
review_branch: review/<id>-codex   # created at reviewed_head in a separate worktree (operating model §6.2)
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
verdict: <READY | READY WITH CONDITIONS | NOT READY>   # a readiness opinion; never an approval
---

# Review: <subject>

> Immutable once committed. Verification happens in separate verification records. The reviewer
> writes this file. The author never edits it. When the reviewer cannot commit directly, the
> owner commits the reviewer's output verbatim, with its sha256 (operating model §6.1).
> `HIO-Actor` trailers are metadata, not proof.

## Scope and inputs
What was reviewed (diff range, specs, releases) and what was out of scope. Which governing
documents were treated as **approved** (with OD ids), and which as proposed context.

## Independent method
The test plan, written **before** reading the author's report. Commands run, reproductions,
triangulation checks.

## Author claims checked
| Claim (from the author's handoff or report) | Checked how | Result |
|---|---|---|

## Findings
| ID | Severity | Finding | Evidence (paths, commands) | Required to close |
|---|---|---|---|---|
| F-<review id>-1 | | | | |

Finding states are tracked in `reviews/README.md`: `open → remediation_claimed →
verified_closed`, or `open → waived` (owner OD only).

## Verification
Not in this file. See the verification records (`templates/verification-record.md`) that
reference these finding ids.

## Verdict and conditions

## Owner disposition
_Pending._ (OD-NNNN for acceptance or waivers.)
