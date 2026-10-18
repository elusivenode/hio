---
id: T-0003
title: Decide the equity total-return source for S2
status: proposed
owner: owner
assignee_role: architecture agent (research) + owner (procurement decision)
created: 2026-10-18
approved: null
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
