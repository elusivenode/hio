---
id: HIO-EVIDENCE-B3-CASH-REBUILD-1
title: "First cash rebuild from live receipts (exploratory; base-camp criterion 3 not established)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0147
---

# First cash rebuild from live receipts

> **Exploratory.** One local rebuild, for a stated window. No rate or index value is recorded here. It writes nothing to the evidence store, releases nothing and approves nothing, and it does not establish base-camp criterion 3.

**Method.** The 14 objects in the evidence store were read with the owner's reader identity and copied to a local scratch store. `hio.jobs.s1b1` then built the releases and `hio.jobs.s1b1_cash_evidence` the report, under the genuine rights gate, at `ac36cbf`, with knowledge cutoff `2026-11-03T23:30:00Z` and P3 labels. The scratch store is not retained, but the receipts remain in the evidence store.

| Output | Rows | Release id (content-addressed) |
|---|---|---|
| `cash.aud.overnight` | 214 | `rel-421322ebb24f…` |
| `cash.aud.overnight.vs_tri` | 214 | `rel-797d1c06a5a0…` |
| `cash.usd.overnight` | 30 | `rel-4891173163f6…` |
| `cash.usd.overnight.vs_sofr_index` | 30 | `rel-a997b8d9b03f…` |

## Results

| Currency | Window | Agrees within bound | Differs: precision | Date alignment | Missing comparison | Unexplained residual |
|---|---|---|---|---|---|---|
| AUD | 2026-01-02 to 2026-11-04 | 0 | **214** | 0 | 0 | 0 |
| USD | 2026-09-21 to 2026-11-03 | 27 | 0 | 0 | **3** | 0 |

No comparison row lacks a cash period, in either currency.

## Dispositions (proposed; each is the owner's to accept)

- **AUD, all 214 `differs: precision`: the spec's declared TRI precision is wrong.** `cash.aud.overnight` 0.3.0 declares `reference_decimals: 4`, marked `[EXT, unverified]` "to confirm at the first authorised structure check". The live TRI has up to **6** decimals (188 of 214 rows in the window have 6; the rest have fewer, consistent with trailing zeros). The classifier therefore correctly declined to apply a bound. The per-period differences are all below 1e-8, far inside the rate-rounding term alone (half a rate ulp over one day at ACT/365 is about 1.4e-7), and their sum over the window is below 1e-7. So there is **no sign of a construction or date-alignment problem**, but the classes stay as reported until a spec version declares 6 decimals. That change belongs with the approval package (T-0014, execution checklist 4).
- **USD, 3 `missing comparison`.** `2026-09-21` to `09-22`: the receipt's SOFR Index window starts one day after its SOFR window, so there is no index level at the start. `10-09` to `10-12` and `10-12` to `10-13`: 2026-10-12 is a US holiday with no index level, but an NSW business day that ends a period. All three are explained by coverage and calendars, and aren't data problems.
- **USD coverage is thin.** `last/30` gives about six weeks, so this exercises the pipeline more than it tests the index relationship. It grows with each capture.

## Gaps this exposed

1. **The build path can't ingest the real F1 receipt as it stands.** F1 runs back to 2011, and `ingest_pending` refuses at the first date outside the 2026 calendar (`CalendarCoverageError`). This rebuild applied the 2026 window in its own driver, outside the repository, keeping rows dated on or after 2026-01-02, so nothing was weakened. A repeatable build needs a stated window or historical calendars, which is a task to raise. **Capture is unaffected.**
2. **An AUD series before 2026 needs cited RITS calendars for those years.** No conclusion here reaches before 2026.
3. **The expert-judgement flags were read but aren't an input to these rows.** The file holds 466 flags, 7 of them in the window, all type A.
