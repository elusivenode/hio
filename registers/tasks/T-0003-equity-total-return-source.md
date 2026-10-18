---
id: T-0003
title: Decide the equity total-return source for S2
status: in_progress
owner: owner
assignee_role: architecture agent (research) + owner (procurement decision)
created: 2026-10-18
authorised_by: OD-0009   # research task; execution not yet started
base_revision: f7a9ec90bb2f0cbd58272c5bd0f0da07948a4ecb
links: {adrs: [HIO-ADR-0005, HIO-ADR-0007, HIO-ADR-0010], depends_on: [], blocks: [S2]}
---

# T-0003: decide the equity total-return source

## Objective
Select a source, and the matching construction, for an investable US large-cap equity total
return in USD (S&P 500 or a declared alternative). It is then translated to AUD by the S1 FX
construction.

## Options to evaluate (from HIO-ADR-0010)
1. S&P DJI index TR and net TR licence.
2. A licensed EOD vendor: prices, dividends and splits for a US-listed S&P 500 ETF, giving a
   market-price TR.
3. Issuer NAV and distribution history, giving a NAV TR.
4. Kenneth French US market return, as a `reference_academic` triangulation only (it is not the
   S&P 500).
5. Wait for futures: ES rolled excess + collateral.

## Evaluation scorecard (per option)
- Return construction validity: which `series_class`, and what is missing.
- Rights:
  - raw and derived storage;
  - post-termination retention;
  - quotation in a trustee pack;
  - agent context.
- History depth; timeliness; corporate-action and dividend completeness; revision behaviour.
- Cost: quote versus estimate, kept separate.
- Exit: bulk export.

## Acceptance tests
| ID | Test | Evidence |
|---|---|---|
| Q1 | the scorecard is completed for options 1–3, with sources cited | a research note in `docs/` or the task |
| Q2 | at least one written vendor response or published terms excerpt per paid option | evidence links |
| Q3 | the owner records the decision as an ADR (HIO-ADR-0011) | ADR |

## Non-goals
- signing a contract;
- writing code.

## Progress (2026-10-18, begun on OD-0010)

Scorecard drafted at `docs/research/T-0003-equity-total-return-sources.md` (Q1). **Q2 is outstanding:** no vendor response, because contacting vendors needs owner approval. Q3 (ADR-0011) follows.

- 2026-10-18: draft vendor questions prepared for owner review (`docs/research/T-0003-vendor-questions-draft.md`). **Not sent** (OD-0013).
