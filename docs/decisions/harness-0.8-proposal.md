---
id: HIO-HARNESS-0.8-PROPOSAL
title: "Decision package: harness-0.8 (one implementation PR per work item; review evidence lane on main), proposed, draft 1"
status: proposed   # no effect; the approved operating model is harness-0.7 (OD-0021, 9b58811)
owner: owner (decides); drafted by claude/implementation-agent
last_reviewed: 2026-10-24
source: "request pasted by the owner on 2026-10-24 without words of their own (docs/history/2026-10-24-advice-workflow-simplification.md, sha256 264f1c8efb53acc4d403b89c81aa7233423df84b6b5bd6e093d04fbe7d7dea5e); read as advice to draft, which any agent may do (AGENTS.md)"
---

# Decision package: harness-0.8

> **Draft only. No effect until the owner approves an exact revision in an OD.** The approved
> operating model is harness-0.7 (OD-0021, `9b58811`). No approved file is edited by this
> branch. PR #2 and PR #3 are untouched; no finding state, verdict or record is changed.
> No OD is recorded for the request, because the request was pasted without the owner's own
> words and nothing was decided.

## 1. Evidence (checked 2026-10-24, `origin/main` = `6fe35cf`)

| Fact | Evidence |
|---|---|
| PR #2 (author): `remediation/s1a-1` → `main`, head `18c80f2…`, 8 commits, 24 files | `gh pr view 2`; `git diff --stat main origin/remediation/s1a-1` |
| PR #3 (reviewer): `review/s1a-1-verify-1-codex` → `main`, head `0255cb2…`; GitHub shows **25 files** | `gh pr view 3 --json files` |
| PR #3 adds **one commit**, `0255cb2` (parent `18c80f2`, trailer `HIO-Actor: codex/reviewer`), changing **two files**, both under `reviews/` | `git log 18c80f2..0255cb2`; `git diff --stat 18c80f2 0255cb2` |
| The record `reviews/records/VERIFY-2026-10-24-s1a-1-1.md` at `0255cb2`: blob `fc199a36d80770503fa725e1c80d567a250faeeb`, sha256 `03dbf7197f9a0ee99902698aa265b86ad8ef4ba24f44a06dcc9fdff13fc55e5e` | `git rev-parse 0255cb2:<path>`; `git show … \| shasum -a 256` |
| Its verdict: REQUEST CHANGES; F1, F2, F3, F5 `verified_closed`; F6 `remediation_rejected`; F4, F7 out of scope (Q-001, Q-002) | the record |
| PR #3 checks green: `scope` run 40071335398; `harness`/`tests` runs 40071323253, 40071335270 | `gh pr view 3 --json statusCheckRollup` |
| PR #1's reviewed head `98e6a8e` was already a first-parent commit of `main` when it was reviewed | `git merge-base --is-ancestor 98e6a8e 3ebeb21` (exit 0); `git log --first-parent main` |
| Every PR is opened by the same GitHub account (`elusivenode`); every commit uses the owner's git identity | `gh pr list --json author`; operating model §6.1 |
| `main` has no branch protection | `gh api …/branches/main/protection` (exit 1, not found) |
| GitHub keeps `refs/pull/3/head` → `0255cb2` | `git ls-remote origin 'refs/pull/*'` |

## 2. Cause of the overlapping PRs

**The overlap is required by harness-0.7, not a reviewer error.** Four rules combine:

1. §6.2 step 0: the author PR stays open and unmerged until the owner says otherwise.
2. §6.2 steps 2 and 7: the reviewer cuts its branch **at the submission head**.
3. Both checks require that ancestry:
   - `tools/check_review_branch.sh` fails if the branch does not descend from the assigned head;
   - so does `tools/check_review_assignment.py` (line 60).
4. §6.2 step 3: the reviewer PR targets **`main`**.

For S1a's first review the head (`98e6a8e`) was already in `main`, so the reviewer PR's diff
against `main` was the record only. Remediation is the first round whose head is **not** in
`main`. Rules 1–4 then force a reviewer PR that is stacked on the author PR.

**Ancestry versus authorship.**
- GitHub diffs PR #3 against `main`, so it lists PR #2's 24 files plus the record.
- The reviewer authored exactly `18c80f2..0255cb2`: one commit, two `.md` files under
  `reviews/`.
- The CI scope gate checks that range (Reviewed-Head..PR head), which is why it passed
  correctly.
- The extra 23 files in PR #3's view are inherited ancestry, not reviewer changes.

**What goes wrong if the harness is followed literally.**
- **Receipt becomes integration.** Step 5 says "merge the reviewer PR". Merging PR #3 would
  bring all of PR #2's unaccepted implementation into `main`. GitHub would also normally mark
  PR #2 as merged, because its head would then be in `main`.
- **Step 6 pushes towards a competing PR.** It says remediation goes "on a branch from the
  receipt commit". For F6 that means a new author branch and a second implementation PR,
  alongside PR #2.

## 3. Proposed future workflow (harness-0.8)

Two lanes, with the owner's authority at the edges:

| Lane | Carries | Branch and PR | Merged by |
|---|---|---|---|
| **Implementation** | code, tests, author records (OD transcriptions, remediation responses, handoffs) | **one** author PR per work item, for its whole life; new commits are appended; never rebased or force-pushed | owner, at **integration** (once) |
| **Evidence** | reviewer records and the reviewer's index rows | one short reviewer PR per review round, **cut from `main`**, touching only `reviews/` | owner, at **receipt** (each round) |

**One round:**
1. **Submission (author).** Append commits to the work item's PR and end with a submission
   commit. Update the PR description's `Submission-Head:` and post a PR comment naming it.
2. **Review (reviewer).** Check that the head named in the assignment rule is the current
   author PR head; if not, stop. Then:
   - test in a **detached worktree at that head**;
   - write the record in a **separate worktree on `review/<id>-codex` cut from `main`**;
   - put the reviewed head in the record's front matter. Ancestry no longer carries it; the
     record is the pin.
   - Push, and open the evidence PR to `main` stating `Reviewed-Head:` and
     `Author-PR: #<n>`.
   - Optionally, post a GitHub **comment-type** PR review on the author PR, with `commit_id`
     set to the reviewed head. It gives the verdict summary and the record's path and sha256.
     This is the collaboration surface only.
3. **Receipt (owner).** Check that steps 4 and 4a pass, then merge the evidence PR `--no-ff`.
   The merge receives the evidence only; no implementation code reaches `main`.
4. **Next round.** The author remediates on the same PR, as in round step 1. A verification
   is pinned to the new head. Its scope is:
   - the rejected or open findings;
   - a regression check of the already verified findings over the delta range
     (previous head..new head).
5. **Integration (owner, once per work item).** Before the final review round, the author
   merges `main` into the author branch (a merge commit, never a rebase), so the final
   reviewed head integrates without conflicts. The owner then merges the author PR `--no-ff`
   under an OD (see §5).

## 4. Where review records live, and their provenance

**Recommended: Git is the evidence store, on `main`, through the evidence lane.**
- Records stay immutable `.md` files in `reviews/records/`.
- The scope gate still enforces their immutability from first commit.
- Provenance is unchanged from §6.1:
  - the `HIO-Actor` trailer, which is declared, not proof;
  - the commit id;
  - the reviewed head in front matter;
  - the receipt merge commit;
  - the OD citing it.

**GitHub PR reviews are the surface, not the store.** Reasons:
- a submitted review body can be edited or dismissed;
- it is not in Git, so it cannot be checked offline;
- every actor uses one account, so a review "approval" authenticates nothing. GitHub does not
  even let a PR's author approve it.

The reviewer may cite the record's sha256 in its PR review, so a later edit is detectable.
Authenticated reviewer accounts remain the deferred evolution named in §6.1.

**Keeping reviewed heads reachable.** A record on `main` may cite a head that is only on an
unmerged branch. Three things keep it reachable:
- the no-force-push rule;
- GitHub's retained `refs/pull/<n>/head`;
- a lightweight tag `reviewed/<review id>` on each reviewed head. The owner pushes it at
  receipt; it is a ref, not content.

## 5. Authority and acceptance boundaries

The routine burden drops from about four owner actions per round to about one: receipt.
Scope, policy, integration and acceptance stay owner-only.

| Action | Who | How often | Instrument |
|---|---|---|---|
| Authorise a work item: scope, findings, author PR, branch | owner | once per work item | OD |
| **Standing review assignment.** Review series id, reviewer, scope, base. Rule: "each round's head is the author PR head at the moment the reviewer starts, which must equal the latest `Submission-Head`". It lasts until the series ends or the owner revokes it. | owner | once per work item | the same or a separate OD; indexed in *Assigned reviews* |
| Start a review round inside a standing assignment | reviewer | each round | none; the record pins the head |
| Receive review evidence (merge an evidence PR) | owner, after steps 4 and 4a | each round | the merge commit, indexed; one OD line per receipt, or a batch at integration |
| Remediate findings inside the authorised scope, including a rejected remediation, after the rejecting record is received | author | each round | none beyond the work-item OD; stop if the record is not in `main` |
| Remediate anything new (scope change, policy questions, new findings outside scope) | owner decides first | as needed | OD |
| **Integrate** the author PR | owner | once | OD, after a checklist: the latest received verification is pinned to the current author PR head; no in-scope finding is open unless waived; CI is green at that head |
| **Accept** the work item | owner | once | separate OD. Integration is not acceptance |
| Waive a finding; decide a policy question (Q-…) | owner (+ solution architect for Q-001/Q-002) | as needed | OD |

Unchanged: the author never edits a verdict or closes a finding, and the reviewer never edits
the author PR. Collaborator text is advice until the owner adopts it, and any conflict means
stop and report.

## 6. F6 on PR #2, without a competing PR

1. **Prerequisite (owner).** Make VERIFY-2026-10-24-s1a-1-1 relied-on evidence, by one of:
   - **(a)** receiving it through the evidence lane (§7, step 4);
   - **(b)** now, under harness-0.7's own *remediation-before-receipt* exception (§6.2
     step 6). An OD names the review id, commit `0255cb2` and the record's sha256 (§1), and
     says the remediation goes on `remediation/s1a-1` (PR #2). That needs no harness change.
2. **Author, on `remediation/s1a-1`, appending only:**
   - read the record with `git show 0255cb2:<path>` and check its sha256;
   - write a regression test for Codex's counterexample: an `os.chmod` failure after
     `os.link`, with `catalogue/` pre-existing, leaves `catalogue/b` visible. Run it against
     the unfixed code and save the failing output, with its exact exit code;
   - commit the fix;
   - add a new response `reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-2.md` for F6
     only. Response 1 is not edited.
   - commit the new submission head, update `Submission-Head:` in PR #2, and add a PR comment.
3. **Reverification.** VERIFY-2026-10-24-s1a-1-2 is pinned to the new head, with base
   `18c80f2`. Its scope is F6, plus a regression check of F1, F2, F3 and F5 over
   `18c80f2..<new head>`.
   - Under harness-0.8, it uses the evidence lane.
   - Under harness-0.7, its reviewer PR would stack on PR #2 again. So this round should wait
     for harness-0.8, or use the interim in §8 alternative B.

## 7. Transition sequence for PR #2 and PR #3

Each step is reversible and names its actor. Nothing is merged or closed until the step says so.

| # | Actor | Step | Check |
|---|---|---|---|
| 0 | owner | Leave PR #3 **unmerged**. Optionally mark it draft or add a "do not merge: receipt would integrate PR #2" comment | PR #3 state OPEN |
| 1 | owner | Decide this package (§9) | OD |
| 2 | owner | Push tag `reviewed/VERIFY-2026-10-24-s1a-1-1` → `0255cb2`. That is the durable anchor for the original reviewer commit | `git rev-parse reviewed/VERIFY-2026-10-24-s1a-1-1` = `0255cb2…` |
| 3 | Claude, then owner | Draft harness-0.8 as exact new revisions on this branch: the operating model §6.2 and §6.1 text, `check_review_branch.sh`, `review_gate.py` and `check_review_assignment.py` (§8). The owner approves it at an exact SHA and integrates it (OD-0021 pattern), with a new adoption condition: a deliberate failing case on the first evidence PR | OD; CI runs |
| 4 | reviewer (Codex), on assignment | **Re-home the record.** Cut `review/s1a-1-verify-1-codex-rehome` from `main`. Add `reviews/records/VERIFY-2026-10-24-s1a-1-1.md` **byte-identical** to `0255cb2` (`git show 0255cb2:<path> > <path>`). Add index rows adapted to `main`'s index; they're navigation only. Open the evidence PR with `Reviewed-Head: 18c80f2…` and `Rehomed-From: 0255cb2…` | `git rev-parse HEAD:<path>` = `fc199a36…` and sha256 = `03dbf719…`; the gate passes under the 0.8 policy taken from `main` |
| 5 | owner | Run steps 4 and 4a (assignment values from the original assignment source). Merge the re-home PR `--no-ff`. Record receipt in an OD citing both `0255cb2` and the receipt commit | OD |
| 6 | owner | Close PR #3 **unmerged**, with a comment linking the receipt commit and the tag. Delete the branch once step 5 is done (the tag and `refs/pull/3/head` keep `0255cb2`) | PR #3 CLOSED, not merged; tag present |
| 7 | Claude | F6 on PR #2 (§6), under the work-item OD | the pre-fix failing output is saved |
| 8 | reviewer | VERIFY-…-2 through the evidence lane | the gate and 4a pass |
| 9 | owner | Q-001 and Q-002 decisions; their implementation and verification (§8.1); the §10 fresh-session test; then integration (OD) and acceptance (separate OD) | ODs |

Steps 2 and 7 do not depend on harness-0.8: with option 1(b) in §6, F6 work can start
straight after step 1. Steps 4–6 and 8 need harness-0.8 in `main`, because the gate takes
its policy from the base commit.

## 8. Smallest harness amendment

| Change | Where | Why it is the minimum |
|---|---|---|
| A verification branch is cut from `main`; the reviewed head is pinned by the record's front matter and the PR's `Reviewed-Head`; testing is in a detached worktree at that head | operating model §6.2 steps 2, 3 and 7 | removes the stacking |
| The scope range becomes `merge-base(base, PR head)..PR head`. Replace the descent check with: "Reviewed-Head exists and is reachable from the named author PR's `refs/pull/<n>/head`" | `check_review_branch.sh`, `review_gate.py` (CI), `check_review_assignment.py` | the existing checks require the ancestry that causes the problem. Every other gate rule is unchanged |
| Remediation of an open author PR appends to that PR. "A branch from the receipt commit" applies only after integration | §6.2 step 6 | stops competing implementation PRs |
| Standing review assignment per work item (§5), and receipt explicitly separated from integration | §6.2 steps 1 and 5, §1.1 | removes routine per-round owner prompts |
| Index navigation cells are written on the evidence lane or in post-receipt status commits; the author PR adds response files only | §6.1 | avoids conflicting edits to `reviews/README.md` on the two lanes |
| A transition clause for PR #3 (§7, steps 2–6), marked as a one-off, like the A01 transition note | §6.2 | bounded; not a precedent |

### 8.1 Q-001 and Q-002 stay owner architecture decisions

Nothing here changes them.
- They stay in the open-decisions queue as owner + solution-architect decisions.
- The drafts in `d1edf1e` stay `proposed`.
- Findings 4 and 7 stay open. No standing authority covers them.

The owner decides each in its own OD. Only the decided option is then implemented, with
regression tests built from Codex's counterexamples. **Recommended:** implement on PR #2 (the
same S1a work item, since both block S1a acceptance), verified in a later round.

## 9. Alternatives and tradeoffs

| Option | What happens | Gain | Cost |
|---|---|---|---|
| **A. Evidence lane on `main` (recommended)** | as above | receipt never integrates code; evidence reaches `main` whatever happens to the work item; the CI gate keeps running (it triggers on PRs to `main`); records never sit inside the author's branch | three small tool changes and a new adoption test; one re-home commit for PR #3 (byte-identical, provable by blob id) |
| **B. Retarget PR #3's base to `remediation/s1a-1`** (zero tool change; usable as an interim) | PR #3's diff becomes just the two reviewer files. Receipt merges it into the author branch; records reach `main` only at integration | the original commit `0255cb2` itself becomes an ancestor, so it is preserved SHA-for-SHA; one PR carries code plus evidence | the CI gate does not run (the workflow is limited to base `main`); the author branch then contains reviewer commits; evidence is stranded if the work item is abandoned (tag mitigates); the author PR head moves to a receipt merge |
| **C. Records committed straight onto the author branch** | the reviewer pushes to the author PR | one PR | the reviewer edits the work under review; the head moves mid-series; separation of duties is lost. **Rejected** |
| **D. GitHub PR reviews as the record** | no record files | least friction | mutable, not in Git, single account, not reproducible. **Rejected as a store**; kept as a surface |
| **E. Keep harness-0.7 as is** | merge PR #3 as receipt | no change | integrates unaccepted code through a "receipt", marks PR #2 merged, forces a new implementation PR for F6. **Not recommended** |

## 10. Risks and rollback

| Risk | Mitigation |
|---|---|
| PR #3 merged by mistake before the transition | step 0 (draft or comment); no branch protection exists, so this relies on care |
| The re-homed copy differs from the original | the blob id and sha256 must equal `fc199a36…` and `03dbf719…`; 4a reruns with the original assignment values |
| A standing assignment lets the author steer the target | the head must equal the current author PR head when the reviewer starts; the head is never force-pushed; the owner can revoke; the reviewer pins and checks it |
| A reviewed head on an abandoned branch becomes unreachable | the tag `reviewed/<id>`, `refs/pull/<n>/head`, no force-push |
| The new gate is weaker than the old one | the range rule and all content rules are unchanged; only the ancestry anchor moves; a deliberate failing case is a new adoption condition |
| A single account and self-declared trailers | unchanged from harness-0.7 (§6.1); PR reviews are not treated as authentication |
| The S1a verification history spans two models | the transition clause names exactly which rounds used which model |

**Rollback.**
- harness-0.8 would be a new approved revision. Reverting is an OD superseding it with
  harness-0.7, whose approved blobs remain.
- Transition steps 0–2 change no content.
- Records that have been received are never deleted.
- PR #3 can be reopened while its branch exists, so the branch should be kept until step 5's
  receipt is recorded.

## 11. Owner decisions required

1. **Direction:** adopt option A (recommended), or B as an interim, or E.
2. **Authorise drafting** harness-0.8 as exact revisions on `proposal/harness-0.8` (§8).
   Approval would be a later, separate OD at an exact SHA.
3. **Standing review assignment** per work item (recommended) or per round. Separately, decide
   whether receipt stays owner-only (recommended) or is delegated.
4. **F6 now:** whether to issue a harness-0.7 *remediation-before-receipt* OD (§6, 1(b))
   naming `0255cb2` and sha256 `03dbf719…`, with the work going on PR #2.
5. **PR #3 transition:** approve §7 steps 0–6, including the tag and the eventual close
   without merging.
6. **Q-001 and Q-002:** confirm they stay separate owner + solution-architect decisions, and
   say whether a decided option is implemented on PR #2 (recommended) or as its own work item.
7. **Integration checklist** (§5) as the precondition for merging PR #2. Acceptance stays a
   separate OD, after the §10 fresh-session test.
