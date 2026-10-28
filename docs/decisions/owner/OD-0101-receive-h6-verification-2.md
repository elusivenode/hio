---
id: OD-0101
title: "Receipt of VERIFY-2026-10-28-h6-1-2 (NOT READY: F-2 open; F-3, F-4 verified_closed) without its index diff (patch context predated main), with the reviewer's row and F-3, F-4 reconciled administratively; nothing accepted"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-receive-h6-verify-2.md (owner's messages, verbatim, with Claude's questions)
  sha256: 3bd79fd40d943d5cc1abd94a11f4ba4e25894686e80b2c800275bd9d0e0a6530
  date: 2026-10-28
  quote: "yes"
applies_to:
  - path: review/h6-1-verify-2-codex
    revision: 9006d1fd9cc9ae56bb36206a26001cc303ec195e   # T
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [F-REVIEW-2026-10-28-h6-1-2, F-REVIEW-2026-10-28-h6-1-3, F-REVIEW-2026-10-28-h6-1-4], ods: [OD-0099, OD-0100]}
---

# OD-0101: the second H6 verification received

## The receipt

| Step | Result |
|---|---|
| 5.0 inputs | **Assignment:** OD-0099. **Reviewer's report:** hiomux `result.json` for task CV2. **Second assignment:** none |
| 5.1 tip | `ls-remote` = fetch = reported tip = `9006d1fd9cc9ae56bb36206a26001cc303ec195e` |
| 5.2 inventory | `A` record, `A` report, `A` handoff, `M reviews/README.md`; each matches its reported sha256 |
| 5.3 checks | `main`'s `check_review_branch.sh` PASS; `check_review_assignment.py` (OD-0099 values) PASS |
| 5.4 tag | `reviews/VERIFY-2026-10-28-h6-1-2` at T; pushed; resolves to T |
| 5.5 README | **The patch did not apply to `main`** (§5.5: stop). Its single added line is navigation, but its context predates `main`'s VERIFY-2026-10-28-h6-1-1 row. On the owner's second go-ahead, the three record files were imported **without the index diff** (`Index-Diff: not applied` trailer) |
| 5.7–5.9 | Blobs equal T; `check_repo` PASS; trailers PASS; remote recheck ok; import merged as `296f47f` |

**The reviewer's row, verbatim:**

```
| VERIFY-2026-10-28-h6-1-2 | REVIEW-2026-10-28-h6-1, findings 2–4 and F-1-fix regression | `ab0288f..5b9e49c` | `fb9b456`, `e4fff98` | F-2 open; F-3 and F-4 verified_closed; NOT READY | [record](records/VERIFY-2026-10-28-h6-1-2.md) |
```

**Administrative edit (this OD's commit; §6.2 5.6 option B practice, OD-0100 draft):**
- **Navigation row:** Codex's row added exactly as written, placed after the VERIFY-2026-10-28-h6-1-1 row.
- **F-3 and F-4:** `open` → `verified_closed`, citing this record. Its outcome table states `**verified_closed.**` for
  both at `5b9e49c`.
- **Unchanged:** every other cell.

## The evidence received (adverse first)

**Verdict NOT READY** at `5b9e49c`:

| Finding | Outcome |
|---|---|
| F-2 (high) | **open**: `**verified_closed.** was NOT reached; …` still publishes a false closure (option B addresses it, OD-0100) |
| F-3 | **verified_closed** |
| F-4 | **verified_closed** |
| F-1-fix regression | **fixed**; F-1 itself stays `verified_closed` |

The 501-test baseline and CI's lint commands passed, and 12 scoped receipt checks passed.

## Also pushed

`01b9f09`: OD-0099 correction 1 and OD-0100.

## Not done

Nothing is accepted, waived or activated. F-2 is being addressed by option B (OD-0100).

## Corrections (append-only)

1. **2026-10-28, formatting fix (Claude's error, disclosed).**
   - **What failed:** as first committed (`118d4dc`, merged and pushed as `704d2b5`), the verbatim quote of the reviewer's
     row sat in an inline code span. The row's own backticks broke the span, so its relative link to the record file was
     live and unresolved from this folder. `check_repo` failed.
   - **Why it went out:** the failure was hidden by piping the check through `tail` (Settled finding: "Never pipe a
     gate").
   - **The fix:** the quote is now a fenced code block. Its text is unchanged.
