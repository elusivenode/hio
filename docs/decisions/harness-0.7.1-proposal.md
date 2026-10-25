---
id: HIO-HARNESS-0.7.1-PROPOSAL
title: "Decision package: harness-0.7.1, review evidence delivered by pushed branch and byte-identical receipt (no reviewer PRs), proposed, revision 3"
status: approved_applied   # approved as applied in C1 552d4fbde6f4256bf969b908d721a765aae84e17 (operating model blob a74a41453d10) by OD-0056; this file is the preserved decision package, revision 3 at 8ed13fd. Status-only edit; text below unchanged
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-10-25
drafted_under: [OD-0049, OD-0050, OD-0052]
revision: 3   # rev 1 = 8d63b99; rev 2 = 9878dd0bad6fa61a0ef8519a6d47da7198b08526 (REVIEW-2026-10-25-harness-0.7.1, REQUEST CHANGES, four findings); rev 3 answers them
amends: docs/harness/operating-model.md §6.2 (harness-0.7), the review delivery and receipt steps only
---

# Decision package: harness-0.7.1 (review evidence delivery)

> **No effect until approved.** The approved operating model is harness-0.7
> (`docs/harness/operating-model.md`, blob `920b1bb153bf7ffaf3a8356a7486b2fa86c5be3f` on `main`).
> It is not edited by this package. If the owner approves an exact revision of this file, §4 is
> applied to §6.2 verbatim, with a changelog line. The name harness-0.8 is not used, because a
> stopped harness-0.8 proposal exists at `b86f497` (OD-0024).

## 1. The problem

Harness-0.7 §6.2 step 3 makes Codex open a PR to `main` for every review and verification
record, and step 5 receives the evidence by merging that PR `--no-ff`.

**That is extra ceremony, and it is also unsafe whenever the reviewed head is not yet in
`main`.** A review branch is cut at the assigned head (step 2), so it carries every commit of the
work under review. Merging it integrates that work.

[OBS] **PR #5** (`review/adr0012-codex` @ `1a05d8e`) shows this:
- its base is `main` (`183523f`);
- it descends from PR #4's head `1d68da3` (HIO-ADR-0012, **proposed**).

Merging PR #5 would put the unapproved ADR, its OD records and the matrix onto `main`. Codex's
own commit adds only three `reviews/` files.

## 2. Receipt mechanisms compared

| # | Mechanism | Keeps the reviewer's commit id in `main`'s history | Can integrate unaccepted work | Works for an unmerged head | Tooling | Verdict |
|---|---|---|---|---|---|---|
| M1 | Reviewer PR, merged `--no-ff` (harness-0.7 today) | yes | **yes**, whenever the head is not in `main` | **no** (unsafe) | CI gate on PRs | replace |
| M2 | Local `git merge --no-ff` of the review branch, no PR | yes | **yes**, unless `git merge-base --is-ancestor <head> main` holds | only after the work is integrated | existing | not the default: it is safe only when the head is already in `main`, and silently unsafe otherwise |
| M3 | Cherry-pick or rebase the reviewer commit onto `main` | no (a new id) | no | yes | existing | reject: it loses identity *and* invites conflict-resolution edits, with no gain over M4 |
| **M4** | **Byte-identical import:** copy the reviewer-added files from the pushed reviewer commit into a receipt commit on `main`; preserve the original commit with a tag | no, **but** the original commit stays reachable through the tag, the receipt commit names it, and every imported file has the **same git blob id** | **no**: only the named `reviews/` files are written | **yes** | existing (`check_review_branch.sh`, `check_review_assignment.py`, `git`) | **recommend** |
| M5 | Cut the review branch from `main` (records only), with the reviewed head in a separate detached worktree; then merge | yes | no | yes | **changes** `check_review_assignment.py` (the descent check), which is accepted S1a content | defer: a later option once tool changes are in scope |

**The trade-off.**
- **M1 and M2** keep the reviewer's commit in `main`'s ancestry. For any review of unmerged
  work, they cannot avoid integrating that work.
- **M4** gives up only ancestry, and keeps three stronger properties:
  - identical bytes (blob id and sha256), checked mechanically;
  - the reviewer's exact commit, preserved and named;
  - a guarantee that nothing outside `reviews/` reaches `main`.

  Precedent: OD-0040 received the T-0004 review this way, as a one-off exception.

### Two different things "preservation" can mean

The choice between M1/M2 and M4 is a choice between two properties that are often confused.

| Property | What it proves | M1/M2 (merge) | M4 (import + tag) |
|---|---|---|---|
| **Byte-identical record preservation** | the record on `main` is the file the reviewer committed: same git blob id, same sha256 | yes | **yes**, checked mechanically before the commit and recorded in its message |
| **Reviewer commit identity** (the exact commit, its message, author and timestamps, retrievable) | which commit the reviewer produced | yes | **yes**: the commit is named in the receipt trailers, kept by an **annotated tag** and by the pushed branch |
| **Commit ancestry in `main`** (the reviewer's commit is an ancestor of `main`) | that everything the reviewer's branch contains has been integrated | yes | **no, deliberately** |

**Ancestry is not evidence integrity, and it can be a liability.** A review branch is cut at the
reviewed head, so its ancestry is the work under review. For an unmerged head, ancestry in `main`
*is* integration of unaccepted work. M4 gives up only that property, and keeps the other two.

**What M4 loses, stated plainly:**
- `git log` on `main` does not show the reviewer's commit. It is found through the receipt
  message, the tag, or the review index.
- The tag and branch are refs, not history. They are protected only by convention (no
  force-push or deletion by the receiver) until branch and tag protection exist (§6.2, "Hosted
  evolution"). The blob ids on `main` remain verifiable against them at any time.
- Commit authorship is not authentication either way. The reviewer's commits carry the owner's
  Git identity, so reviewer provenance rests on the assignment, the record and the pushed branch.
- The reviewer-PR CI scope run was triggered independently of the receiver. Without a PR it is
  dormant, and the same check is run by the receiver from `main`'s copy and recorded in the
  receipt. That is a procedural loss, not an integrity gain (REVIEW-2026-10-25-harness-0.7.1, area 7).

## 3. The recommended procedure (summary)

1. **Claude** uses PRs for implementation, standards and architecture proposals (author PR,
   `Submission-Head`). Documentation-only records may integrate by a local `--no-ff` merge on
   the owner's instruction, as today.
2. **Codex** reviews in an isolated worktree, on `review/<id>-codex` cut at the assigned head,
   and commits records there. It may add files under `reviews/records/`, `reviews/handoffs/` and
   `reviews/reports/`, and its own rows in `reviews/README.md`, as today. **It pushes the branch
   and opens no PR.**
3. **Routine receipt is delegated to Claude** (or the owner), after the checks. It needs **no
   per-receipt owner approval** only when **all** of these hold:
   - the receiver holds the **owner-authored assignment source**, cited by location, and the
     **reviewer's independent report** (§4, step 5.0). If either is absent it reports that and
     stops. It does not substitute the record's own statements;
   - the two-way file inventory matches and the scope and assignment checks pass (5.2, 5.3);
   - every index change falls within Class N or Class S (5.6);
   - the provenance tag is published and verified at the reviewer's commit **before** the merge,
     and the branch tip is rechecked immediately before it (5.4, 5.9);
   - the completion check passes (5.10). Until it does, the status stays "receipt incomplete".

   Receipt is evidence delivery, not acceptance. **Anything else needs the owner:** absent or
   withheld evidence, an assignment discrepancy, a failed check, an unexpected or missing file, an
   index change outside Class N or S, a reviewer branch that moved, a waiver, closing or disposing
   of a finding, integrating the work, or accepting it.
4. **Unchanged:**
   - records are immutable;
   - only Codex verifies technical closure;
   - waivers, standards, scope changes, integration of the work, and acceptance remain owner
     actions (§1.1).

## 4. Exact amendment text (applied to §6.2 on approval)

**Replace step 3's last two sentences** with:

> The reviewer **pushes the review branch** and does **not** open a pull request. An unpushed
> review branch has not been submitted. The reviewer's **final message** is its independent
> report: it states the pushed branch, the branch **tip SHA**, the reviewed head, and the
> **sha256 of every file the reviewer added**. The handoff cannot carry its own commit id, so the
> final message is the source the receiver reconciles against.

**Replace step 4's first sentence** with:

> **Scope check** (the receiver, before receipt). Run **`main`'s copy** of
> `tools/check_review_branch.sh <assigned head> review/<id>-codex` against the pushed branch.

The rest of step 4 is unchanged. Its final paragraph's CI sentences then describe a dormant
control: the `pull_request_target` workflow stays in place, but no longer runs, because there
are no reviewer PRs. Removing it is a separate change to accepted `.github/` content.

**Replace step 5** with:

> 5. **Receipt by byte-identical import** (Claude or the owner; routine, not acceptance). Run it in
> a scratch clone, never in a reviewer's worktree. Every step is idempotent and re-checks the state
> it depends on. Stop and report on any failure.
>
> **5.0 Inputs the receiver must hold first.** If any is absent or withheld, the receiver
> **reports it as absent** and stops. It never substitutes the record's own statements.
> 1. The **owner-authored assignment source**, cited by location: a file in `docs/history/` holding
>    the owner's assignment text verbatim, an *Assigned reviews* row committed by the owner, or an
>    owner PR comment. The expected review id, repository, full base and head SHAs, scope, branch
>    and any delivery exception are taken **from it**. The record's `assignment` field and the
>    reviewer's branch are **never** the expected source.
> 2. The **reviewer's independent report** (step 3): the branch tip SHA and the sha256 of every
>    file the reviewer added, from the reviewer's own final message and relayed by the owner. It
>    must come from somewhere other than the branch.
> 3. A statement that the receiver looked for a **second owner-authored assignment** for the same
>    target (step 1, conflicting channels), naming where it looked.
>
> **5.1 Resolve the tip.**
> - `T=$(git ls-remote origin refs/heads/review/<id>-codex | awk '{print $1}')`. `T` must be
>   exactly one 40-character lowercase hex id. Stop on no line, on several lines, or on any other
>   shape.
> - `git fetch origin refs/heads/review/<id>-codex`, then `git rev-parse FETCH_HEAD` must equal `T`.
> - `T` must equal the tip in the reviewer's report (5.0.2). If not, the branch moved after the
>   report or the report is wrong: stop. The owner decides. Changed work needs a new assignment at
>   a newly stated head.
>
> **5.2 Inventory, reconciled both ways.** List `git diff --name-status <head> T`. Allowed: `A`
> under `reviews/records/`, `reviews/handoffs/` or `reviews/reports/`, and `M reviews/README.md`.
> Anything else: stop. Then reconcile with the reviewer's report: every reported file exists at `T`
> with the reported sha256, **and** no file exists at `T` that was not reported. Record the
> inventory (expected, found, missing, extra) in the receipt's OD. A missing or extra file is a
> stop, never a note.
>
> **5.3 Checks.** Scope: `main`'s copy of `tools/check_review_branch.sh <head> T`. Assignment:
> `tools/check_review_assignment.py` with the values from 5.0.1. Both must pass.
>
> **5.4 Publish and verify the provenance tag first.**
> - Create the annotated tag `reviews/<id>` at `T`, push it, and verify that
>   `git ls-remote origin 'refs/tags/reviews/<id>^{}'` returns exactly `T`.
> - If the tag already exists, it must peel to `T`; otherwise stop. A tag is never moved or deleted.
> - Nothing has been imported yet, so a tag without a receipt is harmless and recoverable.
>
> **5.5 Import.** On `receipt/<id>` cut at the current `main`: `git checkout T -- <each added
> file>`. For `reviews/README.md`, apply `git diff <head> T -- reviews/README.md`. Stop if it does not
> apply cleanly.
>
> **5.6 Index-row semantics.** The staged `reviews/README.md` may differ from `main`'s only by lines
> of these two classes. Each is checked against the **imported immutable records**: the receiver
> reads the record, not the row.
> - **Class N (navigation).** A new row for the imported record itself (assigned-review or
>   received-review row), whose id, base, head, record path and verdict equal the record's front
>   matter, and whose assignment cell matches 5.0.1. Or a new finding row for a finding that the
>   imported **review** record defines: the same id and severity, and the state `open`.
> - **Class S (state transition).** The rewrite of an existing finding row. It is allowed only when
>   the imported record is a **verification** (`VERIFY-*`) of that finding at its reviewed head,
>   and states that finding's outcome. The row's id, review, severity and remediation-claim cells
>   are unchanged. The state cell begins with the state word the record states (`verified_closed`,
>   `remediation_rejected` or `open`), and any further text is traceable to the record.
>
> **Refuse and stop** on any of these:
> - a duplicate id: a first-column id appearing twice in one table, or a finding id appearing twice
>   anywhere in the file;
> - `verified_closed`, `waived` or `accepted` that no imported record supports. A waiver exists
>   only as an owner OD, which the receiver may cite and never creates;
> - a state transition with no verifying record;
> - a removed or changed line that is not the superseded version of a Class S row;
> - any other change.
>
> Where the reviewer's own `README` diff fails this check, the receiver does not apply it, and
> reports the discrepancy to the owner.
>
> **5.7 Verify.** Each imported file's blob id (`git rev-parse :<path>`) equals
> `git rev-parse T:<path>`; nothing outside `reviews/` is staged; `tools/check_repo.py` passes; and
> 5.6 passes.
>
> **5.8 Commit the pure import**, with the trailers:
> - `Review-Id`, `Review-Branch`, `Review-Commit: <T>`, `Reviewed-Base`, `Reviewed-Head`;
> - `Assignment-Source`: the location in 5.0.1, never the record's field;
> - `Reviewer-Report`: how it was supplied;
> - one `Record: <path> blob <id> sha256 <hex>` per imported file;
> - `Inventory: complete` and `Receipt-Checks`.
>
> Keep it pure: no status cell, `STATUS.md` or OD change in this commit.
>
> **5.9 Final remote recheck, then merge and publish.** Immediately before merging, re-run the
> `ls-remote` of 5.1 and of the tag. The branch tip must still equal `T` and the reported tip, and
> the tag must still peel to `T`. If the branch moved, **do not merge**: leave the tag, report, and
> let the owner decide. Otherwise merge `--no-ff` into `main` as `Merge receipt/<id>: receive <id>
> evidence (receipt only)`, and push `main`.
>
> **5.10 Complete only when verified.** After the push, verify that remote `main` equals the local
> merge, that the blobs on `main` equal `T`'s, and that the remote tag peels to `T`. Only then write
> "received" in the index and report completion. Until then the status word is **"receipt
> incomplete"**, and the receiver reports it to the owner by name. A partial receipt is never
> presented as complete.
>
> **5.11 Recovery from a partial operation.** Restart at 5.1 each time. The steps check state before
> acting.
>
> | State found | Action |
> |---|---|
> | checks failed, nothing pushed | stop and report; nothing has changed |
> | tag pushed, no import | harmless. Resume at 5.5 with the same `T`, or abandon with a note in the OD. Never delete or move the tag |
> | tag push failed or rejected | nothing else was done; retry. If the tag exists at a different commit, stop: a mismatch for the owner |
> | import committed, not merged | re-verify 5.9, then merge; or discard `receipt/<id>` (disposable: the reviewer's evidence is untouched) |
> | merged locally, push of `main` failed | re-verify 5.9, then push. The status stays "receipt incomplete" |
> | `main` pushed, tag missing (an outside action removed it) | recreate the exact tag at `T`, verify, and record in the OD that the receipt was incomplete until then |
> | reviewer branch moved or deleted after the tag | `T` stays pinned by the tag and by the blobs on `main`; report it and take no other action |
>
> **Accountability, not mechanism.** The author of the work may be the receiver (Claude receives
> Codex's review of Claude's proposal). **Blob identity detects substitution when the comparison
> runs.** It does not authenticate the reviewer, discover conflicting owner instructions, or make
> the receiver import an adverse record. So **timely receipt and completeness depend on procedural
> accountability**, which these rules make visible to the owner:
> - the owner holds the reviewer's report (5.0.2) and can compare it with the receipt;
> - a **receipt sweep**: at the start and end of every session that touches reviews, and in every
>   completion report, the receiver lists `git ls-remote origin 'refs/heads/review/*'` and reports
>   every branch whose tip is not recorded as received or dispositioned, so that silence is
>   visible;
> - the receiver reports adverse verdicts and open findings first, with the record path, and never
>   describes findings as resolved;
> - absent or withheld evidence is reported, not inferred.
>
> These do not make an author-receiver independent. Where the owner wants independence, the owner
> or a different agent performs the receipt.
>
> **A receipt means the evidence has been received.** It does not mean that the conclusions are
> accepted, that defects are fixed, that an ADR is approved, that a slice is authorised, or that the
> work under review is integrated or accepted. Those remain separate owner actions (§1.1).
>
> **Stop conditions:**
> - the tip changed (5.1 or 5.9);
> - a 5.0 input is absent;
> - a scope or assignment check failed;
> - an inventory mismatch, a missing or extra file, or any file outside the allowed set;
> - a `README` hunk that does not apply or fails 5.6;
> - any blob id differs;
> - `check_repo` failed;
> - the reviewed head differs from the assignment;
> - a tag that exists at a different commit.

**Step 6, first sentence:** replace "on a branch from the receipt commit, submitted as an author
PR per step 0" with:

> on the work's own author branch, submitted at a new fixed `Submission-Head` per step 0, which
> Claude states in the author PR or a comment on it. Claude starts only from a prompt naming the
> receipt commit, reads the record from `main`, and stops if that commit is not in `main` or if
> the record's blob differs from the tag `reviews/<id>`.

The rest of step 6, including the remediation-before-receipt exception, is unchanged.

**Step 7:** "Steps 3–5 apply again" stays, and now means push-only, then receipt by import.

**The PR sentence in the §6.2 preamble.** Replace "merging a reviewer PR is receipt, never
acceptance" with:

> receipt (step 5) is evidence delivery, never acceptance. Reviewers do not open PRs.

## 5. What does not change

- **The assignment.** One owner-authored source; full base and head SHAs; a fixed head, never
  rebased (step 1).
- **Isolated worktrees**, and the reviewer's write scope (steps 2–3).
- **Scope and assignment checks** (steps 4 and 4a), using the existing tools. No change to
  `tools/` or `.github/`.
- **Immutability.** Records are never edited; corrections go through new records or ODs.
  Finding states change only through Codex's verification records, or an owner waiver.
- **Owner approval** remains required for standards, scope changes, waivers, integration of the
  work under review, and acceptance.

## 6. Migration: PR #5 (REVIEW-2026-10-25-adr0012)

> **Executed on 2026-10-25 under OD-0050**, as a one-off exception to harness-0.7 step 5: import
> commit `eadda1e5da5df2d5141d7951abed14df40f70782`, receipt merge `6fbec1aa064551d7aa505cf3008a677acfd68e73`,
> annotated tag `reviews/REVIEW-2026-10-25-adr0012` → `1a05d8e6e0dd453c91cc37aba16c921cd6c97238`,
> PR #5 closed unmerged. Both files on `main` are blob-identical to the reviewer's. The reviewer's
> commit is not an ancestor of `main`, and HIO-ADR-0012 is not in `main`. The proposal text below
> is kept as written; the lessons from the execution are folded into §3 and §4.

**State, checked from Git on 2026-10-25:**

| Item | Value |
|---|---|
| Branch tip | `1a05d8e6e0dd453c91cc37aba16c921cd6c97238` |
| Descends from | the assigned head `1d68da3…` |
| Scope check | **PASS** (`tools/check_review_branch.sh`): one commit; `A` record, `A` handoff, `M reviews/README.md` |
| Assignment check | **PASS** (`tools/check_review_assignment.py`, in a scratch clone): id, base `183523f…`, head `1d68da3…`, branch, and scope terms. The `assignment` string was supplied **from the record**; the owner must confirm it is the source they gave Codex |
| Record | `reviews/records/REVIEW-2026-10-25-adr0012.md`: blob `f3f104da15295b3d6bfb3fe2cbb082cf481354bc`, sha256 `3b12c9fee25b85b609f0195e777c308d55e57d70010b9bddd28691c2bbfe10f2`. Verdict **REQUEST CHANGES**; findings 1 and 2 high, 3 medium, all open |
| Handoff | `reviews/handoffs/2026-10-25-adr0012-codex.md`: blob `196de9c7dd411fe4336254d17d031fee504f7477`, sha256 `5bfd10a95ef9d20c37a9f69d276e3bf004e1842eda3ca1851707451c0350fe2f` |
| Dry run of the M4 import onto `main`, in a scratch clone | both blobs identical; the `README` patch applies (offset −1); exactly Codex's added rows, nothing removed; nothing outside `reviews/`; `check_repo` PASS. Nothing committed |

**Proposed treatment.** This needs no new review, because the evidence is unchanged and only its
delivery differs.
1. **Do not merge PR #5.** That would integrate PR #4's proposed HIO-ADR-0012.
2. **Receive REVIEW-2026-10-25-adr0012 by the M4 import** (§4, step 5), as a one-off exception
   to harness-0.7 step 5. This is the same kind of exception as OD-0040. The receipt commit cites
   `1a05d8e` and the two blob ids above.
3. **Push the tag `reviews/REVIEW-2026-10-25-adr0012` → `1a05d8e`.** Then close PR #5 unmerged,
   with a comment naming the receipt commit. The branch is kept until the owner or Codex deletes
   it.
4. **No effect on HIO-ADR-0012.**
   - It stays **proposed**, and PR #4 stays open.
   - The three findings stay **open**.
   - Remediation follows on PR #4's branch at a new `Submission-Head`, and is verified by Codex.

### Worked checks of the revision 3 rules against the two newest records

A mechanical comparison on 2026-10-25 of Codex's real index diffs with the records they came with.

| Record (reviewer commit) | Index diff | Under revision 2 | Under revision 3 |
|---|---|---|---|
| VERIFY-2026-10-25-adr0012-1 (`e1f60f9`) | 1 new row for the record (id, `6fbec1a..860fd78` and verdict equal its front matter), plus 3 **rewritten** finding rows: F1 and F3 `verified_closed` at `860fd78`, F2 `open`. Each row's id, review and severity are unchanged. No duplicate id results | **refused**: the rule "adds only lines, removes none" rejects any state transition | row 1 is Class N; the three rewrites are Class S, each stating the outcome the record states. Passes 5.6. The receipt would still **stop at 5.0**: the owner's assignment text and the reviewer's report have not been supplied |
| REVIEW-2026-10-25-harness-0.7.1 (`9c51a6b`) | 1 new row for the record, plus 4 new finding rows (ids and severities high, medium, medium, medium all defined in the record; state `open`). No removals. No duplicates | passes | all Class N. The assignment cell asserts a "push-only exception" that only the record asserts, so 5.0.1 requires an owner-authored source for it |
| The attack in finding 2: a second, false `verified_closed` row for an open finding, with the old row kept | a duplicate finding id | passes (only adds a line) | **refused**: the finding id would appear twice. A row that replaced the old one without a verifying record is refused as an unsupported transition |
| The PR #5 precedent (OD-0050) | the receipt took the assignment string from the record | n/a | would have been reported as "assignment source absent" and stopped, as OD-0050 itself records. It proceeded as a specific, owner-authorised one-off |

## 7. Independent check before approval

- **The owner's condition:** this package is independently checked at an exact revision before
  approval. The proposed check is a Codex review of this file only, against harness-0.7 §6.2 and
  OD-0040.
- **Delivery as a pilot:** the owner may ask Codex to push only (no PR), and have the review
  received by the §4 procedure as a second one-off exception. That exercises the procedure before
  it is adopted. The PR #5 receipt (OD-0050) was the first, manual exercise.
- **The draft assignment** is [`harness-0.7.1-review-assignment-draft.md`](harness-0.7.1-review-assignment-draft.md).
  It is a draft, not an assignment.
- **Revision 2 was reviewed** by Codex (REVIEW-2026-10-25-harness-0.7.1, reviewer commit
  `9c51a6b2d05ea3751bfa8799ee756b81ca320651`, REQUEST CHANGES, four findings; **not yet received**).
  Revision 3 answers those four findings and reopens nothing else.

## 8. Owner decisions

1. **Done (OD-0050):** the PR #5 receipt, the tag and the closing of PR #5.
2. **Owed before the next verification is assigned (harness-0.7 §6.2 step 6):** the receipt, or a
   recorded disposition, of REVIEW-2026-10-25-harness-0.7.1 and of VERIFY-2026-10-25-adr0012-1.
   Neither can be merged without integrating unapproved work, and a receipt by import needs its
   own one-off authorisation until this amendment is approved (OD-0052).
3. **Next, and smallest:** assign the scoped verification of this revision (OD-0052, Package B2).
4. **Later:** approve or reject harness-0.7.1 at the revision that was checked.

## Changelog

- 2026-10-25, revision 1 (OD-0049): created.
- 2026-10-25, revision 2 (OD-0050): adds "Two different things 'preservation' can mean" (§2); the
  explicit delegation conditions of routine receipt (§3); the annotated tag, the pure import
  commit and the receiver-independence safeguard (§4 step 5); records the executed PR #5 receipt
  (§6); updates the owner decisions (§8); adds the draft review assignment. The mechanism and the
  exact replacement text of steps 3, 4, 6 and the preamble are otherwise unchanged.
- 2026-10-25, revision 3 (OD-0052): answers REVIEW-2026-10-25-harness-0.7.1 (four findings):
  - F1: step 5.0 requires the owner-authored assignment source and the reviewer's independent
    report; step 5.2 reconciles the file inventory both ways; the accountability paragraph
    replaces "mechanical, not trust" and adds the receipt sweep; delegation in §3 is tightened;
  - F2: step 5.6 validates added and rewritten index rows against the imported records (Class N
    and Class S), and refuses duplicate ids and unsupported dispositions;
  - F3: step 5.1 parses the SHA from `ls-remote` and validates it, and step 5.9 rechecks the tip
    immediately before the merge;
  - F4: step 5.4 publishes and verifies the provenance tag before the import, step 5.10 marks the
    receipt complete only when verified, and step 5.11 gives the recovery path;
  - also: step 3 makes the reviewer's final message the independent report, step 6 states the new
    `Submission-Head`, and §2 and §6 record the dormant CI control and the worked checks.

  Byte-identical import, exact Git provenance, the ban on importing unapproved ancestry and
  stop-on-mismatch are unchanged. `tools/` and `.github/` are not changed.
