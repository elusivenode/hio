---
id: OD-0078
title: "Receipt of VERIFY-2026-10-28-t0009-1-3 (READY: F-5 verified_closed at 846974b) by byte-identical import, on the owner's go-ahead, accepting the reviewer's revision-pinned assignment citation; all seven T-0009 findings now verified_closed; nothing accepted or waived"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-f5-verification-receipt.md (the owner's selections, verbatim)
  sha256: 5cd23bb0caf208bae431e8147cb87348d3a33e02a18f37b2ee1b2bef09b91c80
  date: 2026-10-28
  quote: "Yes, push and receive (Recommended)"
applies_to:
  - path: reviews/records/VERIFY-2026-10-28-t0009-1-3.md
    revision: 73fefcc8f930117c66ee34ed19b02fad80102eb2   # reviewer tip; tag reviews/VERIFY-2026-10-28-t0009-1-3
related: {adrs: [HIO-ADR-0012], tasks: [T-0009], findings: [F-REVIEW-2026-10-25-t0009-5], ods: [OD-0061, OD-0075, OD-0076, OD-0077]}
---

# OD-0078: receipt of VERIFY-2026-10-28-t0009-1-3

## Result

**VERIFY-2026-10-28-t0009-1-3: READY.** F-REVIEW-2026-10-25-t0009-5 is `verified_closed` at `846974b`. Record:
`reviews/records/VERIFY-2026-10-28-t0009-1-3.md`.

- **Pages read live.** The reviewer, with network under OD-0077, read both RBA pages once each over HTTPS. Each
  returned HTTP 200 with the same full sha256 the calendar files cite.
- **Every date checked.** It compared every closed weekday in both files with the pages: none missing, none extra.
- **Interpretations confirmed.** 27 April is open on RITS; 28 December is closed.
- **Behaviour.** It exercised all three NSW-only dates.
- **Regressions.** It confirmed that `76539b5..846974b` changes nothing the six earlier findings depend on, apart
  from the new `rba_calendar_pages` entry, which matches OD-0076.
- **Tests.** 416 passed; the S1a hashes and release identities are unchanged.

**All seven findings of `REVIEW-2026-10-25-t0009-1` are now `verified_closed`:**
- F-1, F-2, F-3, F-4, F-6 and F-7 by `VERIFY-2026-10-28-t0009-1-1` (OD-0075);
- F-5 by this record.

## Why the owner's go-ahead was needed

- **Class S transition.** F-5's row changes from `open` to `verified_closed`.
- **Report channel.** The reviewer's report reached Claude through the hiomux runner's files.
- **The assignment check failed as first run.** The record's `assignment` field reads
  `docs/decisions/owner/OD-0077-codex-reviewer-network.md on main at a8136950c71c8624e9e92e108f7b3a9b96466206`;
  Claude had supplied the bare path. That text is accurate: `a813695` is on `main` and holds OD-0077 as assigned
  (blob `a572b0f`), before correction 1 was appended. The owner chose "Accept the citation". The check was rerun
  with the pinned citation as the expected source, and passed.

## Receipt (operating model §6.2 step 5)

| Check | Result |
|---|---|
| 5.0.1 assignment | `docs/history/2026-10-28-owner-codex-network.md` (sha256 `6c2cee0f…38ed`), transcribed in OD-0077 and the *Assigned reviews* row, on `main` at `a813695` |
| 5.0.2 independent report | Codex's final message saved by hiomux (run `20261028T043057Z-e4d8`, task C3, attempt 1; `report_ok: true`; applied `gpt-6-sol`/`high`/`danger-full-access` inside hiomux's network profile), used on the owner's instruction |
| 5.0.3 second assignment searched | `git grep` of `origin/main`: only OD-0077 and its index and STATUS lines; agent exchange: none; `review/*`: no other branch for this target |
| 5.1 tip | `ls-remote`: one line, `73fefcc8f930117c66ee34ed19b02fad80102eb2`; equals `FETCH_HEAD` and the reported tip |
| 5.2 inventory | expected 2, found 2, missing 0, extra 0: `A reviews/records/VERIFY-2026-10-28-t0009-1-3.md` (sha256 `06e2b656…200d`), `A reviews/handoffs/2026-10-28-t0009-f5-verify-3-codex.md` (sha256 `372701ff…c6c4`); parent is the assigned head `846974b` |
| 5.3 | scope (`main`'s `check_review_branch.sh`) PASS; assignment PASS on rerun, as above |
| 5.4 tag | `reviews/VERIFY-2026-10-28-t0009-1-3` peels to `73fefcc…` (verified by `ls-remote`) |
| 5.5–5.8 | import on `receipt/VERIFY-2026-10-28-t0009-1-3` at `7e2b295`; no reviewer `README` diff; blobs equal; only `reviews/` staged; `check_repo` and trailers PASS; import `ef7e1be` |
| 5.9–5.10 | recheck passed; merge `72908c5` pushed; remote `main` = `72908c5`; blobs on `main` = `T`'s; tag peels to `T`. **Receipt complete** |
| 5.6 index rows (this administrative commit) | Class N: a *Verification rounds* row; the *Assigned reviews* row set to received. Class S: F-5's state cell begins `verified_closed`, traceable to the record; its id, review, severity and remediation-claim cells are unchanged |

**Receipt sweep:** 18 `review/*` branches at the start, all received or disposed of; at the end, 19, the new one
received here. `review/t0009-1-verify-2-codex` was never pushed (superseded, OD-0077).

## Notes and limits

- **Author-receiver.** Claude authored the remediation and received its verification. Not independent (accepted
  weakness, OD-0061).
- **Coverage is 2026 only**, as the record states.
- A receipt is evidence only. This record does **not** accept T-0009 or S1b, merge PR #6, waive anything, or
  authorise any live operation. T-0009 acceptance and the PR #6 merge are separate owner actions.

## Corrections (append-only)

None.
