---
id: HANDOFF-2026-10-25-adr0012-f2-remediation
date: 2026-10-25
actor: claude/implementation-agent (Claude Sonnet 5.5)
work_status: in_review   # ADR-0012 proposed, revision 3; F2 round-2 correction claimed; nothing approved
base_revision: 860fd7879c6c663980bc4bf037a8c29e8c7df769
head_revision: self       # = the PR #4 submission head; resolve with: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-25-adr0012-2.md
work_commits: [cef81f07164c0902c6255897112903a1751ac84f]
work_card: T-0005
---

# Handoff: ADR-0012 F2 correction (revision 3)

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

## Done
- Resolved and verified `VERIFY-2026-10-25-adr0012-1` from Codex's pushed branch (commit
  `e1f60f9`, record sha256 `4692c99f…d048`); read it with `git show` only. It is **not imported
  and not received**; `reviews/records/` is unchanged (OD-0052).
- Corrected **F2 only** in ADR §4.3.3–§4.3.4 (fix `cef81f0`): completion evidence bound to a CI
  execution and a response envelope, seven completion checks, the replayable / witnessed / trusted
  split, an explicit statement that self-recorded events do not prove network activity, the
  unchanged-response case, and fail-closed refusal of missing, failed, delayed, inconsistent and
  unverified evidence.
- Response 2 replays the verifier's counterexample and twelve neighbouring cases.

## Tests and evidence
| Claim | Method | Result |
|---|---|---|
| F1 and F3 text not reopened | section-by-section compare with `860fd78` | §4.3.1, §4.3.2, §4.3.5 and the rest outside §4.3.3, §4.3.4, §4.2, §8 identical |
| Accepted S1a, standards, harness-0.7, `registers/` unchanged | `git diff --stat` | empty |
| Repository checks | `check_repo`, `ruff check`, `ruff format --check`, `pytest` | PASS (0 problems); clean; 63 files formatted; 278 passed |

## Known limitations and not verified
- Specified, not built. The `Date`, `Age` and write-time behaviour of any S1b source or store is
  not evidenced, and examining it needs an owner-approved fetch.
- One case in the replay table is **accepted at build time and is the stated trust limit**: a
  trusted adapter that lies consistently across the envelope, the write time and an invented run
  id. Only an audit of the CI run history, or a later genuine fetch, exposes it.

## Escalated, not decided
- Q-013 and the release-manifest schema question: unchanged, as directed.
- Any stronger mechanism (signatures, hash chain, third-party attestation) is a trust-model
  change. It is not proposed.

## Receipt owed (harness-0.7 §6.2 step 6)
The Codex records are **not received**. Before the owner assigns the F2 verification, each must be
received, or its disposition recorded. See OD-0052.

## NOT approved by this session
- HIO-ADR-0012; any finding closure; any right; S1b; PR #4's merge; Q-013.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `docs/adr0012-staged-s1b-proposal` @ the submission head (stated in the report) |
| Pushed? PR link | pushed; PR #4 (https://github.com/elusivenode/hio/pull/4), with the new `Submission-Head` in a comment |
| Received into `main`? | no |
| Next actor | **owner**, to settle the receipt of the two Codex records and confirm Package A2 |
| Prompt for Codex | per the owner's issued assignment. Prerequisite: the branch tip equals the head named in the assignment; stop otherwise |
