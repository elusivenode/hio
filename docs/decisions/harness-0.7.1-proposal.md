---
id: HIO-HARNESS-0.7.1-PROPOSAL
title: "Decision package: harness-0.7.1, review evidence delivered by pushed branch and byte-identical receipt (no reviewer PRs), proposed, revision 1"
status: proposed   # NO EFFECT until the owner approves an exact revision. harness-0.7 (OD-0021, 9b58811, blob 90e2565fe814) stays in force
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-10-25
drafted_under: OD-0049
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

## 3. The recommended procedure (summary)

1. **Claude** uses PRs for implementation, standards and architecture proposals (author PR,
   `Submission-Head`). Documentation-only records may integrate by a local `--no-ff` merge on
   the owner's instruction, as today.
2. **Codex** reviews in an isolated worktree, on `review/<id>-codex` cut at the assigned head,
   and commits records there. It may add files under `reviews/records/`, `reviews/handoffs/` and
   `reviews/reports/`, and its own rows in `reviews/README.md`, as today. **It pushes the branch
   and opens no PR.**
3. **Receipt** (Claude or the owner) is the M4 import, run as scripted Git commands. It stops on
   any mismatch. It needs **no separate owner approval** when an owner-authored assignment exists
   and every check passes, because receipt is evidence delivery, not acceptance.
4. **Unchanged:**
   - records are immutable;
   - only Codex verifies technical closure;
   - waivers, standards, scope changes, integration of the work, and acceptance remain owner
     actions (§1.1).

## 4. Exact amendment text (applied to §6.2 on approval)

**Replace step 3's last two sentences** with:

> The reviewer **pushes the review branch** and does **not** open a pull request. An unpushed
> review branch has not been submitted. The reviewer reports the pushed branch and its tip SHA,
> and the reviewed head, in its handoff and final message.

**Replace step 4's first sentence** with:

> **Scope check** (the receiver, before receipt). Run **`main`'s copy** of
> `tools/check_review_branch.sh <assigned head> review/<id>-codex` against the pushed branch.

The rest of step 4 is unchanged. Its final paragraph's CI sentences then describe a dormant
control: the `pull_request_target` workflow stays in place, but no longer runs, because there
are no reviewer PRs. Removing it is a separate change to accepted `.github/` content.

**Replace step 5** with:

> 5. **Receipt by byte-identical import** (Claude or the owner; routine, not acceptance). Run it
>    in a scratch clone, never in a reviewer's worktree. Stop and report on any failure.
>    1. `T=$(git ls-remote origin refs/heads/review/<id>-codex)`. Stop if it is missing.
>       `git fetch origin review/<id>-codex:review/<id>-codex`, then confirm the local tip
>       equals T.
>    2. **Scope:** step 4. **Assignment:** step 4a, with the values from the owner-authored
>       assignment source.
>    3. List `git diff --name-status <head> T -- reviews/`. Stop on anything other than:
>       - `A` under `reviews/records/`, `reviews/handoffs/` or `reviews/reports/`;
>       - `M reviews/README.md`.
>    4. From a branch `receipt/<id>` cut at the current `main`:
>       - `git checkout T -- <each added file>`;
>       - for `reviews/README.md`, `git diff <head> T -- reviews/README.md | git apply`. Stop
>         if it does not apply cleanly.
>    5. **Verify:**
>       - each imported file's blob id (`git rev-parse :<path>`) equals `git rev-parse T:<path>`;
>       - the staged `README` diff adds exactly the reviewer's added lines and removes none;
>       - nothing outside `reviews/` is staged;
>       - `tools/check_repo.py` passes.
>    6. Commit with the trailers:
>       - `Review-Id`, `Review-Branch`, `Review-Commit: <T>`, `Reviewed-Base`,
>         `Reviewed-Head`;
>       - `Assignment-Source`;
>       - one `Record: <path> blob <id> sha256 <hex>` per imported file;
>       - `Receipt-Checks: scope PASS; assignment PASS; blob identity PASS`.
>
>       Then merge `--no-ff` into `main` as `Merge receipt/<id>: receive <id> evidence (receipt
>       only)`.
>    7. **Preserve provenance:** push the tag `reviews/<id>` pointing to T, so the reviewer's
>       commit stays reachable. The review branch may then be deleted by the owner or the
>       reviewer.
>    8. Update the review index row ("received at `<receipt merge>` from `<T>`, tag
>       `reviews/<id>`") and `STATUS.md`.
>
>    **A receipt means the evidence has been received.** It does not mean that the conclusions
>    are accepted, that defects are fixed, that an ADR is approved, that a slice is authorised, or
>    that the work under review is integrated or accepted. Those remain separate owner actions
>    (§1.1).
>
>    **Stop conditions:**
>    - the tip changed during receipt;
>    - a scope or assignment check failed;
>    - a file is outside the allowed set;
>    - a `README` hunk does not apply;
>    - any blob id differs;
>    - `check_repo` failed;
>    - the reviewed head differs from the assignment.

**Step 6, first sentence:** replace "on a branch from the receipt commit, submitted as an author
PR per step 0" with:

> on the work's own author branch, submitted at a new fixed `Submission-Head` per step 0. Claude
> starts only from a prompt naming the receipt commit, reads the record from `main`, and stops if
> that commit is not in `main` or if the record's blob differs from the tag `reviews/<id>`.

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

## 7. Independent check before approval

- **The owner's condition:** this package is independently checked at an exact revision before
  approval. The proposed check is a Codex review of this file only, against harness-0.7 §6.2 and
  OD-0040.
- **Delivery as a pilot:** the owner may ask Codex to push only (no PR), and have the review
  received by the §4 procedure as a second one-off exception. That exercises the procedure before
  it is adopted.

## 8. Owner decisions

1. **Smallest, and now:** authorise receipt of REVIEW-2026-10-25-adr0012 by byte-identical import,
   tag `reviews/REVIEW-2026-10-25-adr0012` → `1a05d8e`, and closing PR #5 unmerged. This is a
   one-off exception to harness-0.7 step 5. With it, confirm the record's `assignment` string.
2. **Later:** assign the independent check of this package at its exact revision, then approve
   or reject harness-0.7.1.
