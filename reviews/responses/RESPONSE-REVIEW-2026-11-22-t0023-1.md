---
id: RESPONSE-REVIEW-2026-11-22-t0023-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-11-22-t0023-1-1, F-REVIEW-2026-11-22-t0023-1-2]
reviewed_head: 4b6472e54aa7a1d989ee78ee49f83d6967a27536
fix_commits: [0288120e32046359223f53b923fc8d2e90d5dd20]
submission_head: self   # the commit adding this file; resolve with: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-11-22-t0023-1.md
created_at: 2026-11-22
---

# Remediation response: REVIEW-2026-11-22-t0023-1

> Written by the author on `fix/t0023-review-1` under OD-0186 (OD-0184 A8). A claim, not a verification. Each finding stays open until a verification record closes it.

| Finding | What changed (files) | Evidence (tests, checks) | Residual risk or disagreement |
|---|---|---|---|
| F-1 (medium): C5 can pass after a fiscal year is omitted | `tools/t0023_sleeves.py`: `C5_REQUIRED` pins each fund's two fiscal years covering 2008 with the accession each is read from (as in `corroboration-1.md`). `check_c5` is performed only over exactly that set: a missing, extra, differently filed or repeated year leaves it `not performed`. | `tests/test_t0023_sleeves.py`: omission of each year (`only-first-year`, `only-second-year`), an unpinned filing, a repeated year, the default pins, and the pins checked against the corroboration file's accessions. **Real inputs:** all three funds have exactly the pinned set; dropping SPY's 2009 row on the real file gives "missing 2008-10-01 to 2009-09-30". The full sleeves run at `0288120` reproduces every reported status (C1 to C5, S1 to S5) | Agreed with the finding. The reported run had all six rows, so no reported result changes |
| F-2 (medium): downstream tools don't validate the frozen panel identity | `tools/t0023_common.py`: `verify_record` recomputes `panel_id` from the record's `inputs` and the panel bytes on disk, and requires every rebuild check (`REQUIRED_CHECKS`) to be `true`; `load_frozen` applies it and reads the pinned id at call time. `tools/t0023_seam.py`: the summary's `panel_id` is now the real id, with the run directory as `panel_run`. Test fixtures now write records that recompute (`record_for`). | `tests/test_t0023_common.py`: the paired CSV-and-hash change the review describes, changed or missing inputs, each rebuild check false, absent or null, and no fallback past a failing newest match. The test that accepted two panel texts under one id is removed. **Real inputs:** the frozen run `20261104T090417Z-1d500b75` recomputes to `1aa29918…` with all four checks true; seam, basis and episodes rerun at `0288120` with the same results (episode decision row 1) | Agreed. The id binds the code's conventions, so a convention change now needs a new frozen id, as intended |

**Also, from the review's tracing.** Codex read the six fund-years from the SEC filings. Claude compared the local `audited-facts.csv` with that table on 2026-11-22: all 24 figures (distributions, return, NAV start and end) are equal. That answers "audited figures were transcribed by the author" for these values; the EODHD-derived results stay unverifiable by an independent reader, as the review says.

Suite: 1,693 passed; `check_repo.py` PASS.
