---
id: HANDOFF-2026-10-28-h6-1-verify-1-codex
date: 2026-10-28
actor: codex/reviewer
work_status: in_review
base_revision: ab0288fe57fb2ae9100c989142102445e5046bc5
head_revision: self
work_commits: []
stream: harness
---

# Handoff: H6 remediation verification

> Reviewer snapshot, not an owner decision. The [verification record](../records/VERIFY-2026-10-28-h6-1-1.md) is the verdict.

## Changed files and scope

Added this handoff, the verification record and the prior [test plan](../reports/2026-10-28-h6-1-verify-1-test-plan.md); added one verification-round row to `reviews/README.md`. No author work, approved document, `STATUS.md`, non-reviewer handoff or file outside `reviews/` was edited. The assigned head is `ab0288fe57fb2ae9100c989142102445e5046bc5`, the public HTTPS `phase-b/h6` tip; the assigned base is its ancestor. OD-0097 matches the owner message and the index, with no conflicting owner assignment found.

## Result

**NOT READY.** F-REVIEW-2026-10-28-h6-1-1 is technically `verified_closed` for its original unsupported-acceptance exploit. F-2, F-3 and F-4 remain `open`; their remediation claims are rejected at this head. A further medium regression overrejects valid Class N rows when their scope text contains `accepted`, `waived` or `approved`. The record gives exact reproductions and the affected lines.

## Tests and evidence

| Check | Result |
|---|---|
| Pinned Python 3.13.3, `uv sync --frozen`, full `uv run --frozen pytest -q` | **490 passed in 92.52s**. The temporary environment holds the 11 locked packages; no extra tool was installed. |
| Ruff on both changed tools and their test modules; `git diff --check` | Passed. |
| Own 11-case disposable bare-origin run, using the test module's repository fixture with independent perturbations and assertions | The valid dry run left remote refs unchanged; the nine required failure categories stopped; partial receipt recovered after a rejected `main` push. The fixture uses the real scope and assignment checks and a repository-check stub. |
| Independent direct probes against `main`'s real index and a disposable assignment index | Reproduced F-2, F-3 and the original F-4 example; confirmed F-1's original rejection and that a later seven-cell F-4 row now works. Exposed the additional overbroad Class N refusal. |
| Index import check | The single new verification-round row passed `hio_receive.check_index` when applied to `main` with the imported record. The original F-1 state row exists on `main`, not in this older author head, so it cannot be rewritten in this branch's patch. The record supplies its closure authority for the receiver's later index update. |

## Didn't work and limits

The first in-memory index-row check inserted the proposed verification row after the matching id in *Assigned reviews*, which tested the wrong table and failed. I corrected the probe to target *Verification rounds*; it passed with no file change. No real remote receipt or CI result was run. The disposable fixture's repository check is a stub; `main`'s three check tools are byte-identical in this checkout, and the receiver's calls to them were inspected.

## For the index

- F-REVIEW-2026-10-28-h6-1-1: `verified_closed` at `ab0288f` by [this verification](../records/VERIFY-2026-10-28-h6-1-1.md); technical closure only.
- F-REVIEW-2026-10-28-h6-1-2 to -4: `open` at `ab0288f`; remediation rejected by the same verification.
- Additional medium regression: `hio_receive.check_index` refuses a valid Class N scope containing the word `accepted`; see the record's regression section.

## Not approved

No H6 activation, implementation acceptance, §6.2 amendment, finding waiver, H11 change, or receipt into `main` was approved by this session. The latest handoff is not a decision.

## Completion block (operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and SHA | `review/h6-1-verify-1-codex` at `ab0288fe57fb2ae9100c989142102445e5046bc5` before the runner's reviewer commit; the runner reports the later branch tip. |
| Pushed? | No; the runner owns the commit and the owner or orchestrator pushes it. No PR. |
| Received into `main`? | No. |
| Next actor | hiomux runner, then owner or orchestrator as receiver. |
| Prompt with prerequisites | Verify the final report's four file hashes, commit exactly those bytes with `HIO-Actor: codex/reviewer`, and report the new tip. Before pushing and receipt, reconfirm OD-0097, the fixed assigned head and absence of a conflicting owner assignment; then apply §6.2 scope, assignment, inventory, tag and byte-identical receipt checks. The owner or receiver reconciles the finding-state index after receipt. Receipt is not H6 approval or activation. |
