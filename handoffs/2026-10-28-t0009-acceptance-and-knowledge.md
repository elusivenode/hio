---
id: HANDOFF-2026-10-28-t0009-acceptance-and-knowledge
date: 2026-10-28
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code; hiomux orchestrator, run 20261028T043057Z-e4d8)
work_status: "T-0009 S1b-1.0 accepted (OD-0079); harness-0.9 revision 4 proposed (OD-0080), not approved"
base_revision: 300703724b1dc5f0db3cbc9a26c8262cea11fce7   # session start (docs/od0072-hiomux-pilot); main was 950cce7
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/2026-10-28-t0009-acceptance-and-knowledge.md
work_commits:
  - c77334d   # main: OD-0072 to OD-0074 merged (assignment of VERIFY-…-1)
  - 5330307   # main: receipt of VERIFY-2026-10-28-t0009-1-1
  - 4f7943f   # impl/t0009-remediation-1: F-5 completed with the real 2026 RITS and NSW calendars (D7)
  - 846974b   # impl/t0009-remediation-1: response 2, the accepted head
  - 72908c5   # main: receipt of VERIFY-2026-10-28-t0009-1-3
  - 7eba3f9   # main: PR #6 integrated
  - e16a47f   # main: OD-0079, T-0009 accepted
  - 2df83b4   # proposal/harness-0.9: revision 4
work_card: T-0009
stream: t0009-and-harness   # proposed H4 field (harness-0.9; not yet in the template)
---

# Handoff: T-0009 from submission to acceptance; Codex reviewer network; session knowledge distilled

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

**Role:** implementation agent and hiomux orchestrator.
**Work status:** T-0009 S1b-1.0 **accepted** (OD-0079); harness-0.9 revision 4 **proposed**.

## Changed files

| Area | Change |
|---|---|
| `main`, records | OD-0074 to OD-0080 with verbatim `docs/history/` files; index rows in `docs/decisions/owner/README.md` and `reviews/README.md`; `STATUS.md`; the T-0009 card status; this handoff |
| `main`, reviewer evidence | `reviews/records/VERIFY-2026-10-28-t0009-1-1.md` and `-3.md`, and their handoffs, imported byte-identically (tags `reviews/VERIFY-2026-10-28-t0009-1-1`, `-3`) |
| `main`, via PR #6 | T-0009 code, tests, specs, `infra/` and the remediation. This session added `src/hio/reference/calendars/{rits,nsw}-2026.yaml`, the `registers/sources.yaml` entry `rba_calendar_pages` and `tests/test_s1b1_reference_calendars.py` |
| `proposal/harness-0.9` | revision 4: proposal §14 and §12, `MAP.md`, `knowledge/findings.md` |
| Outside the repository | `~/.hio-runs/bin/hiomux` (networked Codex reviewer; sha256 `436833b7…`) and `PROTOCOL.md` (`c8bac354…`). Backups are in `~/.hio-runs/notes/*.pre-network.bak` |

## Done

1. **PR #6 submitted.** Pushed `impl/t0009-remediation-1` and opened PR #6 (OD-0074).
2. **First verification.** Codex returned `VERIFY-2026-10-28-t0009-1-1`, NOT READY: six findings
   `verified_closed`, F-5 open. Received under OD-0075.
3. **D7 explained and approved.** The owner approved D7 as one yes/no (OD-0076).
4. **F-5 completed.** Two RBA pages read once with `curl`, a dated extract committed, 8 tests added;
   416 tests pass.
5. **Offline verification superseded.** `VERIFY-…-2` said READY but could not see the pages. Not received
   (OD-0077).
6. **Network for the Codex reviewer.** Added on the owner's instruction (OD-0077), and tested adversarially.
7. **Second verification.** `VERIFY-2026-10-28-t0009-1-3` was READY: the reviewer read the pages live and they
   hash-matched. Received under OD-0078.
8. **Accepted and merged.** T-0009 accepted at `846974b`; PR #6 integrated as `7eba3f9` (OD-0079).
9. **Distil.** This session distilled into harness-0.9 revision 4 and this handoff (OD-0080).

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| Integrated head | `uv run --no-sync pytest -q`; `ruff check`; `ruff format --check`; `check_repo.py`; trailers, at `7eba3f9` | 416 passed; clean; clean; PASS; PASS |
| Code at integration equals the accepted head | `git diff 846974b 7eba3f9 -- src tests tools specs infra registers pyproject.toml uv.lock .github` | empty |
| Calendar data | Codex's live read (VERIFY-…-3) | both page sha256 equal to the recorded ones; every date matches |
| Codex network profile | probes, and a real `codex exec` (OD-0077 table) | network reads work; credentials, SSH, keychain, push, config and `.git` writes are blocked |
| CI | `gh run list` | `main` runs green through `520a799`. `e16a47f` was still running at last check; PR #6 checks passed |

## Known limitations and not verified

- **Calendars:** they cover 2026 only (recheck by 2027-01-31). RITS Advice 02/2026 was never read.
- **hiomux:** its changes are tested by Claude only, with no independent verification. Its unexplained change
  before this session (OD-0077 finding 1) is **open**.
- **Precision:** the declared rounding precisions are unverified assumptions (accepted with the work).
- **Independence:** remediation and receipts were both done by Claude (author-receiver, OD-0061).

## Open findings (from `reviews/README.md`)

None for T-0009: all seven are `verified_closed`. Other reviews are unchanged.

## Didn't work

*Proposed H4 section.*

- **WebFetch for source facts.** It returns a model's summary, so I used `curl` with a hash.
- **Denying the macOS security services to block the keychain.** It broke Codex's TLS. Denying reads of the
  keychain files works instead.
- **Codex's own `workspace-write` network switch inside a hiomux profile.** macOS cannot nest the sandboxes.
- **An offline reviewer for external data.** It cannot verify against bytes it doesn't have.
- **`git merge -F -`.** It doesn't read stdin.
- **`check | tail`.** The gate passed falsely again. zsh `$T:r` broke `git show` again.

## For the index

*Proposed H4 section.* The 22 lines are already in the Inbox at `proposal/harness-0.9` `2df83b4`
(`knowledge/findings.md`, under "From the 2026-10-28 … session"). A first distil is due: 42 lines.

## Assumptions made

- **Integration route.** PR #6 was integrated by merging the exact head into `main`, not by merging `main` into the
  head, so the accepted revision stays exact.
- **The "proceed" assignment.** OD-0076 rests on "proceed" adopting a plan stated in the question it answered.
- **The F-5 re-verification.** It rests on "fix network situation first" (OD-0077). Both are recorded as such.
- **OD-0080's scope.** It is read as authorising drafting within harness-0.9, not a new mechanism.

## Conflicts found between documents

- **OD-0073's hiomux hash** did not match the tool at session start. Reported (OD-0077 finding 1), not resolved.
- **PROTOCOL's "no reads of GitHub credentials"** was untrue for Claude workers. The owner accepted the residual,
  and PROTOCOL was corrected (OD-0077 correction 1).

## NOT approved by this session

Agents approved nothing. The owner's acts are recorded in OD-0074 to OD-0080. Not approved by anyone:
- harness-0.9 (any phase);
- any Settled finding;
- source rights other than D7;
- Authorisation B or any live operation;
- the finality staging;
- the draft 0.3.0 specs;
- the `check_repo.py` proposals.

## Next authorised action

None is authorised beyond closing the hiomux run when the owner says so. Owner decisions available:
1. **Harness-0.9 Phase A:** approve its Appendix A at `2df83b4` and apply it now (proposal §12, items 1 and 2).
   Then hold the first distil.
2. **Phase B:** authorise it, including §14 G2 and G3 (hiomux into the repository; a tool hash check) and G1
   (Codex access, H11).
3. **OD-0061:** whether to extend it to hiomux-delivered reports (§14 G5).
4. **hiomux's unrecorded change:** what happened (OD-0077 finding 1).
5. **Authorisation B prerequisites:** T-0002 rights, controls, storage.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `main` at the commit adding this handoff; `proposal/harness-0.9` at `2df83b427896cf5ce413e8cee76f809a267687f6` |
| Pushed? PR link | yes, both. PR #6 merged (`7eba3f9`) |
| Received into `main`? | VERIFY-…-1 (`5330307`) and VERIFY-…-3 (`72908c5`) received; VERIFY-…-2 not received (superseded) |
| Next actor | owner |
| Prompt for the next actor | "Read `AGENTS.md`, `STATUS.md` and this handoff. Stop if `main` does not contain `7eba3f9` or OD-0080. Then, only on an owner instruction: (a) apply harness-0.9 Phase A from `proposal/harness-0.9` at `2df83b4` verbatim (stop if Appendix A differs from what the owner approved), or (b) start the Authorisation B prerequisites. hiomux: read `~/.hio-runs/PROTOCOL.md` first, and check `bin/hiomux` against sha256 `436833b7…` (OD-0077) before delegating." |
