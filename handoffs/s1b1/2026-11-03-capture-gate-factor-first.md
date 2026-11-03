---
id: HANDOFF-2026-11-03-capture-gate-factor-first
date: 2026-11-03
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code; hiomux orchestrator)
work_status: "T-0014 and T-0015 accepted; distil 2 accepted; capture gate revised and factor-first order adopted; B-2 re-run and 7b done; C5 open, no longer a gate; nothing captured"
base_revision: 3a8486aace0981ec94339a7074e74192e0761f27
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/s1b1/2026-11-03-capture-gate-factor-first.md
work_commits: [b5a2b1c, 7bcbc2a, 53bf125, aacfca2, 6030c17, 7c36e4a, b23d2ad, 7b362ee, fc77ea0, bc3a036, 098bb96, 52abaff, 58fe532, b40e139, cf312ed, dfc2e99, 35edd32, 310d7dd]
work_card: T-0014, T-0015
stream: s1b1
---

# Handoff: from storage assurance to a factor-first order

> A dated snapshot. **Not a decision.** The previous handoff in this stream is `2026-10-29-base-camp.md`.

## The turn this session took

The owner asked: "we are trying to build a high quality set of factors and quantitative capabilies on top. what such a heavy reliance on
blob?" That question reset the programme, so a fresh session should start here.

- **The answer reached.** Blob is right for evidence, and was never a research layer. The problems were that a storage timing rule (C5) had
  become a gate on capture, and that almost nothing exists above storage: no `models`, `portfolio` or `taa` packages, cash and FX only in
  `library`, no numerical dependencies, DuckDB used only for the catalogue index, and no real data anywhere.
- **What was decided (OD-0139).** B-3 no longer waits for a C5 decision. The working order is factor-first
  (`docs/decisions/factor-first-sequencing-proposal.md`). Each track still needs its own yes.
- **Owner preference seen again.** Controls should match the risk of the step. The owner questioned the state backup ("does this really
  matter?"), and they were right: I had made it a precondition for a step it did not affect.

## Changed files

`main` `3a8486a..`, all by pull request (#55 to #70, and #43, #53):
- **Owner records:** OD-0135 to OD-0141, with `docs/history/` transcripts.
- **Merged work:** T-0014 (`aacfca2`); T-0015 (`52abaff`).
- **Adopted documents:** `docs/evidence/S1B1-authorisation-B-revision-1.md`; `docs/decisions/factor-first-sequencing-proposal.md`.
- **Evidence:** `docs/evidence/b2/rerun-1.md` (the re-run report verbatim, and 7b).
- **Review receipts:** VERIFY-…-t0014-1-1, REVIEW-…-t0015-1, VERIFY-…-t0015-1-1, each with §5.12 rows.
- **Knowledge:** distil 2 (39 lines, `MAP.md` rows).

## Done

- **Session start:** both hashes matched (hiomux `54fe4e86`, PROTOCOL `13a45eb7`). hiomux was down; run `20261103T013031Z-6675` opened.
- **T-0014** received and accepted (OD-0135). Machinery only: no base-camp criterion is established.
- **T-0015:** Codex found a real defect (an inconclusive properties result treated as proof of existence). Fixed (`cf50736`), verified READY,
  accepted (OD-0137, OD-0138). So Codex has now found a real defect in three tasks running.
- **Two architect consultations** (`…141451-ask-15e3`, `…142328-ask-3901`). The second changed the drafts: capture readiness first, one US
  tenor, a wider rights track, and an explicit input choice for the reader. It also corrected two of my claims.
- **B-2 re-run** (run `41590213489`, OD-0140): `BlobExists` works live; C5 as written 45/50 violations; floored candidate 0/50.
- **7b:** a privileged delete of a retained version is refused, 409 `BlobImmutableDueToPolicy`; an overwrite adds a new version; bytes intact.

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| T-0014 with `main` | scratch-clone merge; pytest, ruff, `check_repo` | 1053 passed; clean |
| T-0015 with `main` | scratch-clone merge; pytest, ruff, `check_repo` | 1108 passed; clean |
| The T-0015 regression test catches the defect | the new cases run on the pre-fix code | 7 failed, then all passed after the fix |
| `main` green | CI at `58fe532`, `310d7dd` | success |
| Receipts complete | §6.2 5.0–5.10, three receipts | PASS; all three without the index diff, on the owner's go-ahead |
| Re-run | report sha256 `0a514b60…`, retained verbatim | as above |
| 7b | `docs/evidence/b2/rerun-1.md` | as above |

## Known limitations and not verified

- **C5 is undecided.** Candidates: the floored rule, or `x-ms-version-id` as the witness. Whether Azure guarantees a version id means write time
  is unverified. The re-run used a surrogate for `completed_at`, not a real publisher read, in one 15-second burst.
- **The `Date` header** ran up to about a second behind the version id. Unexplained.
- **Immutability:** tested on the probe account, one-day Unlocked policy. Changing an Unlocked policy, deleting the account and the evidence account
  itself are all untested.
- **Storage-error limit, accepted for the soak (OD-0140):** partial writes and no failed run record on a storage exception. Traced in code, not
  exercised on Azure.
- **Base camp, the roadmap and the implementation plan** are still proposed, and don't yet reflect the adopted order.
- **`~/.hio-state/`** is still a single copy. The owner regards rebuilding it as easy.
- **One CI attempt failed** at the `uv` install step on PR #65, with no cause in the log (OD-0138 correction 1).

## Didn't work

- **My 7b plan had two errors:** a role that can't delete versions, and a CLI option that doesn't exist. Either would have looked like a refusal.
  Reading the exit code and the reason caught the second.
- **`check | head -1`** gave a false failure on a passing check (SIGPIPE). The same family as last session's `| tail`.
- **Long compound commands** chaining commit, push and merge were refused by the classifier once; the same work passed as separate steps after the
  owner's explicit yes. **Role grants are refused outright** ("Permission Grant"): the owner runs them with `!`.
- **My first answer on the 403** overstated it, and my correction understated it. Reading `BlobStagedWrites.commit` settled it, after the architect
  pushed.
- **zsh:** `$T:path` applies a history modifier, and `=====` at the start of a word is an equals expansion.

## For the index

- `[infra] Azure's x-ms-version-id carries sub-second time: s equalled its floor and completed_at <= version id in 50 of 50, by 67.6 to 76.2 ms. Whether Azure guarantees this meaning is unverified. Source: docs/evidence/b2/rerun-1.md.`
- `[infra] With completed_at taken before the write, C5's existing rule failed 45 of 50 and floor_s(completed_at) <= s held 50 of 50: whole-second Last-Modified explains the failure. Source: docs/evidence/b2/rerun-1.md.`
- `[infra] Azure's response Date header ran up to about a second behind x-ms-version-id, so offset bounds built from Date may not measure clock skew. Unexplained. Source: docs/evidence/b2/rerun-1.md.`
- `[infra] Storage Blob Data Contributor has no blobs/deleteBlobVersion/action, so its refusal of a version delete proves nothing about immutability; test with Storage Blob Data Owner. Source: OD-0140 correction 1.`
- `[infra] az storage blob delete has no --version-id; use the SDK's delete_blob(version_id=...). Source: OD-0140 correction 1.`
- `[infra] Under version-level immutability, deleting a retained version gives 409 BlobImmutableDueToPolicy; an overwrite by a principal with write rights succeeds and adds a new current version. Source: docs/evidence/b2/rerun-1.md.`
- `[storage] BlobStagedWrites.commit creates keys one at a time with no rollback, and a storage exception escapes run_capture and run_due with no failed run record; the process fails, so the alert fires. Accepted for the soak. Source: src/hio/storage/blobstore.py:145; OD-0140.`
- `[publish] resolve_for_use resolves stored releases only and returns knowability declarations without enforcing them; a reader must enforce the knowledge mode and cutoff itself. Source: src/hio/publish/status.py:83; architect consultation 20261103T142328-ask-3901.`
- `[process] A refusal test counts only if the refusal's reason is read: exit code 2 from a CLI argument error looked like a refusal. Source: OD-0140 correction 1.`
- `[process] Match a precondition to the risk of its step: the state backup gated a probe that never touched state. Source: OD-0140 correction 1.`
- `[process] A pipe to head kills the check with SIGPIPE and gives a false failure: send a check's output to a file and read its exit code. Source: OD-0137 correction 1.`
- `[process] The auto-mode classifier refuses Azure role grants ("Permission Grant"): give the owner the command to run with !, printing no ids. Source: OD-0140 correction 1.`
- `[repo] In zsh, $T:path applies a history modifier (:r strips an extension): write ${T}:path. A word starting with = is an equals expansion. Source: reproducible.`
- `[ci] A newer merge to main cancels the running main CI, so read the tip's run; a cancelled run on an earlier merge is not a failure. Source: runs on 098bb96, 52abaff and 58fe532.`
- `[review] A reviewer's README diff failed to apply in all three receipts this session; ask for the go-ahead to receive without it in the receipt question. Source: OD-0135 correction 1; OD-0137; OD-0138.`
- `[hiomux] A Codex reviewer's clone has no origin remote: tell it to read the OD and index row from local main at a cited commit. Source: REVIEW-2026-11-03-t0015-1.`
- `[review] In three tasks running (T-0013, T-0014, T-0015) Codex found a real defect that a passing full suite did not cover. Source: OD-0133, OD-0134, OD-0135.`

## Open findings (from `reviews/README.md`)

- F-VERIFY-2026-10-28-h6-1-6-1 (high, H6 parked). HIO-ADR-0012 F-1 and F-3 still `remediation_claimed` (OD-0054).
- All T-0014 and T-0015 findings are `verified_closed`. No finding is waived.

**Receipt sweep:** every `review/*` branch from this session is received. Earlier branches stand as STATUS records them. `review/t0009-1-verify-2-codex`
is local only, by design (OD-0077).

## Assumptions made

- **"Rebuilding state … isn't that difficult. we can back up state if you really want."** Read as dropping the backup for R-1 and 7b, and as making it
  optional at go-live too, though revision 1 lists it as required. Confirm at the go-live yes.
- **Consultation count:** 12 genuine (`ask` and `assess`) across runs, counted from the logs.

## Conflicts found between documents

- **Revision 1 lists the backup as required for B-3;** the owner's words make it optional (above).
- **Base-camp criterion 7 says "not released";** the adopted order recommends a local `exploratory` release (route A). Base camp is unadopted, so
  this waits for that decision.
- **The re-run plan** still names the Contributor role and the CLI option. It stays as it stands; `docs/evidence/b2/rerun-1.md` records what ran.

## NOT approved by this session

- **Go-live and any capture;** `LIVE_AUTHORISATION`; the five URLs; the punctuality bar. The go-live package draft was put to the owner and **not answered**.
- **Any C5 amendment; the destroy;** adopting base camp; changes to the roadmap or plan.
- **Any rights verification;** the duration experiment; the analytical reader; numpy; any download, vendor contact or purchase.
- **Distil 3** is proposed only.

Owner acts this session: OD-0135 to OD-0141 as recorded, including accepting T-0014, T-0015 and distil 2, and adopting the two documents.

## Next authorised action

**Nothing new is authorised for Claude.** The owner decides, in the adopted order:
1. **The go-live package draft** (five URLs, punctuality bar, staging statement): a draft-only yes, put and unanswered.
2. **Destroy `rg-hio-probe`:** from 2026-11-04T06:36:50Z, on a "go".
3. **Rights on the H2 and H4 rows:** the owner's own reading of the live clauses. Blocks the duration experiment.
4. **T-0003 vendor questions**, and whether to adopt or amend base camp, the roadmap and the plan.
5. **The C5 choice:** consult the architect first.
6. **Distil 3** (PR, proposed), the overdue architect performance review, and the held-out cases.

**Hard date:** 2027 RITS and NSW calendars before 2027-01-01; recheck by 2026-12-01.

## Completion block

| Field | Value |
|---|---|
| Branch and full SHA | `main` at the commit adding this file; `proposal/distil-3` (proposed, unmerged) |
| Pushed? PR link | yes, by PR |
| Received into `main`? | VERIFY-…-t0014-1-1 (`53bf125`), REVIEW-…-t0015-1 (`7b362ee`), VERIFY-…-t0015-1-1 (`098bb96`) |
| Next actor | owner |
| Prompt for the next actor | "Run `hio-orch`. Check hiomux `54fe4e86…`, PROTOCOL `13a45eb7…`. Stop if `main` lacks OD-0141 or this handoff. Read this handoff, then `docs/decisions/factor-first-sequencing-proposal.md` and `docs/evidence/S1B1-authorisation-B-revision-1.md`: they set the working order. The probe account `rg-hio-probe` is held, and may be destroyed from 2026-11-04T06:36:50Z on a go. Nothing has been captured. Then put the owner's next decisions, starting with the go-live package draft." |
