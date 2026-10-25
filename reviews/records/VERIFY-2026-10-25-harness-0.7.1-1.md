---
id: VERIFY-2026-10-25-harness-0.7.1-1
reviewer: codex/reviewer
review: REVIEW-2026-10-25-harness-0.7.1
assignment: owner direct instruction to Codex, 2026-10-25, VERIFY-2026-10-25-harness-0.7.1-1, base 6fbec1aa064551d7aa505cf3008a677acfd68e73, head 8ed13fdef8537b846afb7e60b14807417b2f3c0d, verbatim in docs/history/2026-10-25-owner-review-disposition-assignments.md at commit db4cc82cf04a87a74e678c8b778db190a87305cc
reviewed_base: 6fbec1aa064551d7aa505cf3008a677acfd68e73
reviewed_head: 8ed13fdef8537b846afb7e60b14807417b2f3c0d
base_revision: 9878dd0bad6fa61a0ef8519a6d47da7198b08526
submission_head: 8ed13fdef8537b846afb7e60b14807417b2f3c0d
fix_commits: [3cfff1489939403fd8a08f5fa9288d7ba9c98aa0]
review_branch: review/harness-0.7.1-verify-1-codex
created_at: 2026-10-25
verdict: READY WITH CONDITIONS
---

# Verification: harness-0.7.1 revision 3

## Assignment and method

The owner-authored assignment is in `docs/history/2026-10-25-owner-review-disposition-assignments.md` at `db4cc82cf04a87a74e678c8b778db190a87305cc`, transcribed in OD-0053. It assigns this exact base, head, previous head, branch and four-finding scope. The remote `docs/harness-0.7.1-review-receipt` tip is `8ed13fdef8537b846afb7e60b14807417b2f3c0d`, which descends from both base `6fbec1aa064551d7aa505cf3008a677acfd68e73` and previous reviewed head `9878dd0bad6fa61a0ef8519a6d47da7198b08526`. I used a separate worktree at the fixed head. The earlier review is unreceived; OD-0053 permits reliance on its exact pushed evidence for this cycle only.

I checked the proposed step 5 against approved harness-0.7 and the original four counterexamples before reading the response. I also compared the real index diffs from reviewer commits `e1f60f9…` and `9c51a6b…` with their immutable records, then tested the changed-ref and partial-receipt paths. This is verification of proposed procedure text, not an end-to-end production receipt or adoption of the amendment.

## Per-finding outcomes

| Original finding | Independent check | Outcome |
|---|---|---|
| **F-REVIEW-2026-10-25-harness-0.7.1-1** | Revised step 5.0 requires the owner-authored assignment source, including any delivery exception, and the reviewer's final report from outside the branch, with every added file's SHA-256 (`docs/decisions/harness-0.7.1-proposal.md:137-148`). The record's own assignment field is expressly excluded as the expected value. Step 5.2 reconciles the reported and Git file lists in both directions (`:159-164`). A missing adverse record or report therefore stops rather than producing a complete receipt. The receipt sweep and accountability text (`:242-257`) expose silence while admitting that an author-receiver can still withhold action. This is a stated procedural trust limit, not an identity guarantee. The real PR #5 receipt would stop under 5.0 because its original assignment/report were unavailable, as OD-0050 records and the proposal's worked table acknowledges (`:342-356`). | **verified_closed** as a procedure correction. It does not authenticate Git users or retroactively cure earlier evidence limitations. |
| **F-REVIEW-2026-10-25-harness-0.7.1-2** | Step 5.6 allows only Class N navigation additions or Class S state rewrites supported by the imported immutable record, and refuses duplicate finding IDs or unsupported disposition (`:179-202`). I compared the actual `e1f60f9` README diff: one verification row and three rewritten F1/F2/F3 rows; its record states F1/F3 `verified_closed` and F2 open, with IDs, severity and remediation-claim cells preserved. The actual `9c51a6b` diff has one review row and four newly open findings defined in that record. Revision 2's add-only rule would reject the first; revision 3 admits it. A duplicate `verified_closed` row fails the duplicate-ID rule, while replacement without a verification record fails Class S. `tools/check_repo.py` has no review-index semantics checker; 5.6 is a receiver-performed control and is described as such. | **verified_closed** as a procedure correction. The semantic check is manual until separately authorised tooling exists. |
| **F-REVIEW-2026-10-25-harness-0.7.1-3** | Step 5.1 parses the remote line to one 40-hex T, fetches it, and compares it with the independently reported reviewer tip (`:150-157`). Step 5.9 rechecks the remote branch and peeled tag immediately before merge (`:217-221`). A force-push between 5.1 and 5.9 leaves the tag at old T but stops the merge for owner disposition; a changed report or assignment stops earlier. A race after the final check cannot be eliminated by a text procedure, but all imported files and the tag remain pinned to T. | **verified_closed** for the stated moving-ref control. |
| **F-REVIEW-2026-10-25-harness-0.7.1-4** | Step 5.4 publishes and checks the annotated tag before any import (`:169-173`). A failed tag push leaves `main` untouched. Steps 5.9-5.10 require remote branch, tag, main and imported blobs to match before reporting receipt (`:217-227`), and 5.11 gives recovery for tag-only, import-only, local-merge-only and failed-main-push states (`:229-240`). I checked the specified peeled-ref form against existing tag `reviews/REVIEW-2026-10-25-adr0012`; it returns reviewer commit `1a05d8e6e0dd453c91cc37aba16c921cd6c97238`. | **verified_closed** for tag ordering and partial-receipt recovery. |

## Integrity limits and remaining gates

The revised procedure keeps byte-identical import and a receipt branch cut from current `main`; it never merges the reviewer commit or the unapproved work in that commit's ancestry (`docs/decisions/harness-0.7.1-proposal.md:35-67,175-215`). `git diff 9878dd0..8ed13fd -- src tests tools specs registers docs/standards docs/harness` is empty. The Git blob and SHA-256 checks prove equality with a named reviewer commit; they do not authenticate the person controlling the shared Git account. The independently relayed final report and owner assignment are procedural evidence, and routine receipt still depends on a receiver actually acting. Revision 3 now states those limits without claiming cryptographic authentication (`:242-257`). No new governance or authentication system is required by the approved harness for this bounded correction.

The earlier two reviewer records and this verification are still unreceived. An actual receipt under the proposed procedure would stop at 5.0 wherever the original owner assignment or independent reviewer report is missing; OD-0053 explicitly preserves those absences. Revision 3 is proposed and cannot be used as authority until the owner approves its exact revision. The current push-only delivery for this verification is a separate owner exception, not adoption of revision 3.

## Verdict

**READY WITH CONDITIONS** for this bounded verification: all four findings are independently verified closed as design corrections at the fixed head. The conditions are owner receipt/disposition of the evidence, an approval decision on the exact proposed amendment, and separate validation when the procedure is first used. This record neither adopts harness-0.7.1 nor approves ADR-0012, waives findings, verifies rights or authorises S1b.
