---
id: OD-0162
title: "Owner authorises a one-month EODHD Personal plan evaluation (T-0022), the owner paying; a rights decision is still owed before any retrieval"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-eodhd-evaluation.md (the pasted brief; sections 2 to 10 condensed, as it states)
  sha256: e4e9d21921f35bc81e9d5140861ec315a9de50fd2f41fff22a7e9f3d370efa2c
  date: 2026-11-04
  quote: "I have decided to proceed with a one-month evaluation of the EODHD Personal EOD Historical All-World plan"
base_revision: 9b399221684defd643c4d68fbb42b42e80b80b4d
related: {adrs: [HIO-ADR-0011], tasks: [T-0003, T-0021, T-0022], findings: [], ods: [OD-0159, OD-0160, OD-0161]}
---

# OD-0162: the EODHD evaluation

The brief selects EODHD for one month, with the owner completing the subscription, and authorises Claude to implement and report. It supersedes, for this evaluation, E-0002's 40/60/80 design with its three allocations; and supplies the "own decision" OD-0159 reserved for a trial and Stage C. Vendor selection isn't reopened.

## How Claude read it

- **The rights gate isn't cleared by this decision.** The brief says it doesn't alter the standard and makes retrieval "subject to the applicable rights gate". `eodhd` is `unverified`, so the gate refuses. A narrow owner decision is owed before any retrieval, and Claude has asked for it.
- **Agents see no licensed values.** EODHD's terms don't address AI, so `agent_context` is unknown, and unknown means deny (rights standard §3, §4; AGENTS.md). Tools show Claude and Codex counts, hashes and pass or fail only. Reports with values are for the owner, locally.
- **USD cash** is a bill ETF, BIL, from the same source, labelled a funded bill-ETF sleeve and not RA §3.2 cash, because retained SOFR covers about six weeks. One added instrument.
- **E-0002 is pre-registered before any retrieval,** on the three allocations, with monthly rebalancing.
- **Codex** reviews code, invented fixtures and metadata. It doesn't receive licensed bytes.

## Not authorised

As brief section 10 lists. Also no second vendor, no evidence-store write, and any retention after cancellation until the owner decides.

## Corrections (append-only)

1. **2026-11-04: the Codex review the brief requires (section 9) is assigned.** Review id `REVIEW-2026-11-04-t0022-1`, at `34d2f33a6ab7327493a6e877b6720c7ac20d8a48`. Scope: `tools/eodhd_eval.py`, `tools/research_reader.py`, `src/hio/library/vehicle_return.py`, `src/hio/portfolio/fixed_allocation.py`, their tests, the rights record, E-0002's pre-registration and `docs/evidence/e0002/assessment-1.md`'s claims. **Codex receives no licensed bytes or values:** the evaluation workspace is made unreadable for the run. It reviews code, invented fixtures, counts and claims. One focused review, not a general one. It writes only under `reviews/`.
