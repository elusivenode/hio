---
id: HIO-H6-OPTION-B
title: "Proposed amendment: receipt takes navigation rows only; finding states are reconciled separately (H6 option B)"
status: proposed   # drafted under OD-0100; needs owner approval at an exact revision; no effect until then
owner: owner (approves); drafted by claude/implementation-agent
last_reviewed: 2026-10-28
---

# Amendment proposal: H6 option B

**Why.**
- **F-REVIEW-2026-10-28-h6-1-2:** across two rounds of fixes, a receiver deciding finding states from a record's
  prose produced false closures. Free text can always contradict a token.
- **The missing-row problem:** reviewers' branches often lack `main`'s finding rows, so they cannot write the change
  (OD-0098).
- **The architect's advice** (consultation `20261028T211545-ask-2e83`, OD-0100): take state interpretation out of
  receipt.
- **Current practice already matches:** OD-0061 already requires the owner's go-ahead for any Class S row.

**Effect.**
- Receipt brings in evidence and navigation rows only.
- Finding states change in a separate administrative edit that the owner authorises. It transcribes the received
  record's outcome and accepts nothing.
- Existing records and rows are unchanged.

## A. Operating model §6.2 step 5.6 (replace the whole step)

Old text: from `**5.6 Index-row semantics.**` up to, but not including, `**5.7 Verify.**`.

New text:

```
   **5.6 Index-row semantics (navigation only).** The staged `reviews/README.md` may differ from
   `main`'s only by **added** lines of Class N, each checked against the **imported immutable
   records**: the receiver reads the record, not the row.
   - **Class N (navigation).** A new row for the imported record itself (assigned-review or
     received-review row), whose id, base, head, record path and verdict equal the record's front
     matter, and whose assignment cell matches 5.0.1. Or a new finding row for a finding that the
     imported **review** record defines: the same id and severity, and the state `open`.

   Receipt never changes the state of an existing finding. A finding's state changes only by 5.12.

   **Refuse and stop** on any of these:
   - a duplicate id: a first-column id appearing twice in one table, or a finding id appearing twice
     anywhere in the file;
   - a state cell of `verified_closed`, `remediation_rejected`, `waived` or `accepted` in any added row.
     A waiver or acceptance exists only as an owner OD, which the receiver may cite and never creates;
   - any removed or changed line;
   - any other change.

   **When the reviewer's `README` diff is refused**, the receiver does not apply any part of it. With
   the owner's go-ahead for that receipt, it may still receive the record files (5.5, 5.7 to 5.10)
   **without the index diff**. The import commit then carries `Index-Diff: refused (<reason>)`, and the
   receipt's OD lists the refused lines verbatim. The navigation rows and any state changes follow by
   5.12. A partial receipt is never presented as including the index.
```

## B. Operating model §6.2: new step 5.12 (insert after step 5.11's table, before `**Accountability, not mechanism.**`)

```
   **5.12 Index reconciliation (owner-authorised, after receipt).** Finding states in
   `reviews/README.md` change only by an administrative edit the owner authorises in an OD, after the
   verification record that supports them has been received (5.10).
   - **Each change names:**
     - the finding;
     - the received record and its reviewed head;
     - the outcome as the record states it;
     - the row's state before and after.
   - **Only the state cell (and its citation) changes;** every other cell is preserved. Navigation rows
     a refused index diff would have added (5.6) may be added in the same edit, checked as Class N.
   - **Several changes may be batched** in one OD.
   - **What it is:** a transcription of the reviewer's technical outcome. It does **not** accept the
     work, approve its activation or grant a waiver.
   - **The receipt summary (5.10)** lists, as "index reconciliation pending", every outcome an imported
     verification record states that the index does not yet show. That disagreement is visible until
     5.12 resolves it.
```

## C. Operating model §6.2 step 5.0, or OD-0061 (no text change needed)

OD-0061's routine delegated receipt already covers Class N only. Under this amendment, every receipt's index change
is Class N, and every finding-state change is an owner OD (5.12).

## D. H6 design wording (`docs/decisions/harness-0.9-proposal.md` §6.1, `hio_receive.py` bullet)

Replace `implements §6.2 steps 5.1 to 5.10 without changing their meaning;` with:

```
implements §6.2 steps 5.1 to 5.10 as amended by option B (5.6 navigation only; a refused index diff
received only with `--without-index` and the owner's go-ahead), and reports "index reconciliation
pending" for 5.12; it never changes a finding's state;
```

## E. Harness version

When approved and applied: `harness-0.9b`, with this changelog line:

```
"harness-0.9b (YYYY-MM-DD, APPROVED by OD-NNNN at <commit>; docs/decisions/h6-option-b-amendment.md): §6.2 step 5.6 takes Class N index changes only; a refused index diff may be received without the index on the owner's go-ahead; new step 5.12, owner-authorised finding reconciliation. Codex's bootstrap and review protocol otherwise unchanged. No CI or hook changed"
```

## Not in this amendment

- Activation of H6, which still needs its Codex verification and the owner's approval.
- Any change to existing records or rows.
- OD-0061's scope.
