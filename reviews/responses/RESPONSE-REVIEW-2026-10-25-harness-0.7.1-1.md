---
id: RESPONSE-REVIEW-2026-10-25-harness-0.7.1-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-25-harness-0.7.1-1, F-REVIEW-2026-10-25-harness-0.7.1-2, F-REVIEW-2026-10-25-harness-0.7.1-3, F-REVIEW-2026-10-25-harness-0.7.1-4]
responds_to: REVIEW-2026-10-25-harness-0.7.1   # reviewer commit 9c51a6b2d05ea3751bfa8799ee756b81ca320651 (branch review/harness-0.7.1-codex, not yet received); record blob 93129fc0e9c84361c4ba8f33c6198ddfef935cce, sha256 0b36f97a3e2a7e23853ae76eb21579d4dcbfdf876701aede54526b4d3947b1cd (read with git show, hash checked; OD-0052)
previous_submission_head: 9878dd0bad6fa61a0ef8519a6d47da7198b08526
authorised_by: OD-0052
fix_commits: [3cfff1489939403fd8a08f5fa9288d7ba9c98aa0]
test_commits: []   # documentation-only; no test applies
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-25-harness-0.7.1-1.md
created_at: 2026-10-25
---

# Remediation response 1: harness-0.7.1 receipt procedure

> **Author's claim, not verification.** All four findings stay **open**. harness-0.7.1 stays
> **proposed**; harness-0.7 is unchanged and in force. Only Codex may verify closure, at a fixed
> head the owner assigns. The index rows for these findings arrive with Codex's own `README`
> edit, which has not been received, so this response adds no index row.

The fix is one commit, `3cfff14`, changing only `docs/decisions/harness-0.7.1-proposal.md`
(revision 3). The reviewed head `9878dd0` stays in ancestry.

## Closure map

| Finding | Root cause | Fix (package section) | The review's scenario, re-run on revision 3 |
|---|---|---|---|
| **F1** (high) | the assignment string was taken from the record, nothing independent fixed the expected file list, and no signal existed if an adverse record was never received. The text still called the safeguards "mechanical, not trust" | **§4 step 5.0** requires the **owner-authored assignment source**, cited by location, and the **reviewer's independent report** (tip and sha256 of every added file, from its final message). The record's own `assignment` field is never the expected source. **5.2** reconciles the file list **both ways**. The **accountability paragraph** replaces "mechanical, not trust", states what blob identity does not prove, and adds a **receipt sweep** of `refs/heads/review/*`. §3's delegation is tightened | a forged matching assignment string no longer passes: the expected values come from 5.0.1. A missing or extra file stops at 5.2. A reviewer who pushes and the receiver who stays silent is visible at the next sweep. Absent or withheld evidence is **reported**, not inferred |
| **F2** (medium) | a README patch that only adds lines passed, yet could carry a false disposition | **5.6** classifies every changed index line as **Class N** (navigation) or **Class S** (a state transition), each checked against the **imported immutable record**. It refuses duplicate ids, unsupported `verified_closed`/`waived`/`accepted`, a transition with no verifying record, and any other change | the second, false `verified_closed` row (old row kept) is refused: the finding id would appear twice. A replacement row with no verifying record is refused as an unsupported transition |
| **F3** (medium) | `T=$(git ls-remote …)` captured `<sha><tab><ref>`, and the stop condition for a moving tip was never executed | **5.1** parses `awk '{print $1}'` and requires **exactly one 40-hex id**, fetches that object, and compares it with the reviewer's reported tip. **5.9** re-runs `ls-remote` for the branch **and** the tag immediately before the merge | a force-push after the first read is caught at 5.9: the branch is not merged, the tag stays, the owner decides, and changed work needs a new assignment |
| **F4** (medium) | the tag was pushed **after** the merge, so a failed push left `main` holding a record whose promised provenance tag was missing, with no recovery | **5.4** publishes and **verifies** the annotated tag **before** the import (a tag with no receipt is harmless). **5.10** marks the receipt "received" only when remote `main`, the blobs and the remote tag all verify; until then it is **"receipt incomplete"**. **5.11** is a recovery table covering seven partial states | a rejected or interrupted tag push now happens when nothing is imported, and is retried or stopped. A deleted tag after the merge is recreated at `T` and recorded. A partial receipt is never presented as complete |

## A real defect found while testing the rules

The revision-2 rule "the staged `README` diff adds exactly the reviewer's added lines and removes
none" would have **refused a genuine verification**. VERIFY-2026-10-25-adr0012-1's index change
rewrites three existing finding rows (a state transition is a rewrite), so revision 2 could not
have received it. Class S (5.6) fixes that without letting a false closure through.

## Evidence

| Check | Result |
|---|---|
| Real index diffs checked mechanically against their records (scratch script, 2026-10-25) | VERIFY-2026-10-25-adr0012-1 (`e1f60f9`): 1 Class N row whose id, `6fbec1a..860fd78` and verdict equal the record; 3 Class S rewrites whose outcomes match the record (F1, F3 `verified_closed`, F2 `open`); no duplicate id. REVIEW-2026-10-25-harness-0.7.1 (`9c51a6b`): 1 Class N row and 4 new `open` finding rows defined in the record; none removed; no duplicate id. A synthetic duplicate-row attack is caught by the per-table and per-finding-id rule |
| Worked table | package §6, "Worked checks of the revision 3 rules against the two newest records" |
| Preserved | byte-identical import (5.5, 5.7), exact Git provenance (5.8, 5.4), the ban on importing unapproved ancestry (the receipt branch is cut from `main`; only named `reviews/` files are imported; the reviewer's commit is never merged), stop-on-mismatch (the stop-condition list, extended) |
| Delegation | still to Claude, **only** with the owner-authored assignment, the reviewer's report, a matching inventory, passing checks, Class N or S changes, a verified tag and a rechecked tip. Approval, waivers, closing findings, integration and acceptance remain the owner's (§3) |
| Unchanged | `docs/harness/operating-model.md` is blob-identical to `main`'s; `tools/`, `.github/`, `src/`, `tests/`, the standards and `registers/` are untouched |
| Repository checks | `tools/check_repo.py` PASS; `ruff` clean; `pytest` 278 passed (see the handoff) |

## Open items (none decided here)

1. **The index-semantics check (5.6) is a procedure the receiver performs**, helped by a
   scratch script. Automating it as a checker in `tools/` would change accepted S1a content and is
   **not proposed**; it needs a separate authorisation if the owner wants it.
2. **The two Codex records are not received.** Under §6.2 step 6 each must be received or have a
   disposition recorded before the next verification is assigned (OD-0052). Under this procedure
   the receipt would currently **stop at 5.0**, because the owner's assignment text and the
   reviewers' reports have not been supplied.
3. **No change to the trust model or to an approved standard** is proposed. The accountability
   paragraph states a limit of the mechanism; it does not add an authentication system.

## Not claimed

- That any finding is closed, or that harness-0.7.1 is approved or ready to adopt.
- That the receipt of any Codex record has happened or is authorised.
- That the procedure has been run end to end; it has been replayed on paper and against two real
  index diffs.
