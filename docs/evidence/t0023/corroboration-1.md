---
id: HIO-EVIDENCE-T0023-CORROBORATION-1
title: "T-0023 steps 3 to 5: corroboration of the comparison's inputs (content held locally)"
status: draft
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0178
relocated_by: OD-0210
---

# T-0023 steps 3 to 5: corroboration of the comparison's inputs (content held locally)

> **Relocated 2026-11-22 (OD-0210).** This record rests on data licensed for local research only, so its content is kept in the owner's local results store and not in this public repository. This file is a stub: it says what the record is, its standing, and where the content is. Earlier revisions of this file remain in git history (OD-0196).

| Field | Value |
|---|---|
| Record | `HIO-EVIDENCE-T0023-CORROBORATION-1` |
| What it is | What the comparison's inputs were checked against (issuer and audited figures, the RBA cash seam, FX timing), which checks passed or failed, and what remains. |
| Standing | Exploratory and unaccepted. T-0023's review findings are verified closed (OD-0193); T-0023 is not accepted. |
| Local copy | `~/.hio-research/results-store/records/HIO-EVIDENCE-T0023-CORROBORATION-1/`, one folder per archived revision of this file; the store's `manifest.json` lists each with its sha256 |
| Last revision with content | `d2dc747500b7963ea3a9b612f016ce587b2bea5c` |
| Check the store | `uv run python tools/results_store.py verify --store ~/.hio-research/results-store` |

## Public reference filings (not licensed data)

The audited fund reports the checks were read against are public SEC filings. `tools/t0023_sleeves.py` pins them (`C5_REQUIRED`), and a test requires this list to match it.

| Fund | Fiscal year | SEC accession number |
|---|---|---|
| SPY | 2007-10-01 to 2008-09-30 | `0000950135-08-007648` |
| SPY | 2008-10-01 to 2009-09-30 | `0000950123-09-066888` |
| BIL | 2007-07-01 to 2008-06-30 and 2008-07-01 to 2009-06-30 | `0000950123-09-040926` |
| IEF | 2007-03-01 to 2008-02-29 and 2008-03-01 to 2009-02-28 | `0001193125-09-101817` |

Nothing here states a result. A reader with access to the local store reads the record there; anyone else can rely only on the standing above.
