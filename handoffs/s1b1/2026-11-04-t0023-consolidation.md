---
id: HANDOFF-2026-11-04-t0023-consolidation
date: 2026-11-04
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code; hiomux orchestrator)
work_status: "T-0023 steps 1 to 7 done, unreviewed and unaccepted; recommendation proposed"
base_revision: db9d7aedb457931a0f264f65c82ad4fdc6b00f4b
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/s1b1/2026-11-04-t0023-consolidation.md
work_card: T-0023
stream: s1b1
---

# Handoff: T-0023, the AUD comparison made challengeable

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the review index. It holds no licensed-derived value.

## Changed files
`git diff --stat db9d7ae..HEAD`: `tools/e0003_panel.py`, `tools/t0023_*.py`, their tests, `docs/evidence/t0023/`, OD-0177 to OD-0180. Licensed workspaces stay in `~/.hio-research/T-0023/`.

## Done
- **Steps 1 and 2 (OD-0177):** per-block interval classes; panel `1aa29918…` rebuilds from retained bytes, values byte-identical to E-0003 V1's record.
- **Steps 3 to 5 (OD-0178, OD-0179):** corroboration, the cash seam, what remains. Bars declared first.
- **Steps 6 and 7 (OD-0180):** three episodes; rule gives row 1; recommendation proposed, after the architect (`docs/history/2026-11-04-architect-t0023-step7.md`).
- **Workers W1 to W7 (Sonnet):** tools and tests, each through `hiomux check`, about 6.84 USD. W2 to W6 tools needed fixes only real data showed.

## Tests and evidence
| Claim | Method | Result |
|---|---|---|
| Repository and suite | `tools/check_repo.py`; `uv run pytest -q` | see the PR for this head |
| Rebuild | two commits | same panel id and values hash |
| Tests catch a broken tool | 13 mutations of `tools/e0003_panel.py` only | 13 of 13 |
| Results | `docs/evidence/t0023/` | recorded without licensed values |

## Known limitations and not verified
- **Codex hasn't reviewed anything here.** One author, one machine.
- **IEF has no NAV check,** and C1 for BIL, C4 for IEF and C5's return bar for SPY failed. See `corroboration-1.md`.
- **Audited figures were transcribed by the author;** accession numbers are recorded for tracing.
- **Two full test runs stalled at 99% CPU,** no stack captured, not reproduced, not explained.
- **`tools/t0023_spy_diagnostic.py` was declared after the failure it explains.**
- **The mutation check covered only the panel tool.**

## Didn't work
- **`cmd | tail && git commit` and `set -e` in this shell:** both let failed checks through, twice. Use `|| exit 1` on each step, with no pipe on the gated command.
- **Curl to iShares' download link:** returns the product page, and a site-entry workaround was refused as bot-check circumvention. It needs the owner's browser.

## For the index
- `[research] Workers' invented-data tests missed three real-data shapes (a links column, H.10's last date, BIL's reverse split); run a tool on real inputs before trusting a pass. Source: docs/evidence/t0023/corroboration-1.md.`
- `[research] Two translated USD portfolios' compounded difference keeps its sign in AUD: W_T_AUD - W_B_AUD = W_FX (W_T_USD - W_B_USD). FX or AUD cash sensitivities can't challenge it. Source: tools/t0023_episodes.py.`
- `[sources] SEC www.sec.gov refuses a client with no declared contact, though data.sec.gov answered; audited fund highlights give NAV, distributions and return per fiscal year, public. Source: OD-0179.`
- `[data] EODHD's distributions for SPY, BIL and IEF match six audited fund-years covering 2008. Source: docs/evidence/t0023/corroboration-1.md.`
- `[data] Reinvesting on the payment date doesn't explain HIO's SPY gap to the issuer. Source: tools/t0023_basis.py.`
- `[build] Reloading a tool module under its own name in a test makes two copies of its exception across a full run; import it once. Source: tests/test_t0022_eodhd_eval.py.`

## Open findings (from `reviews/README.md`)
None from this work: no review was run. F-1 (BGBL) stays open.

## Assumptions made
- "Publicly readable" in T-0023 covers one recorded read of issuer files, whose rights row stays unverified; they stay local.

## Conflicts found between documents
- `preregistration-1.md`'s independence table said the audited reports weren't obtained; amendment 2 records that they were.

## NOT approved by this session
No experiment result, data series, source or factor is accepted. The recommendation is proposed. No experiment is authorised, no CPI source is authorised, no Codex review is assigned, and PR #104 isn't merged. Nothing is approved for a consumer or the SMSF.

## Next authorised action
None. The owner decides on the recommendation, the merge and any review.

## Completion block (harness-0.7, operating model §6.2 step 9)
| Field | Value |
|---|---|
| Branch and full SHA | `feat/t0023-consolidation`; `git log -n1 --format=%H -- handoffs/s1b1/2026-11-04-t0023-consolidation.md` |
| Pushed? PR link | yes, https://github.com/elusivenode/hio/pull/104 |
| Received into `main`? | not received; the owner runs the merge |
| Next actor | owner |
| Prompt for the next actor | See below |

**Prompt for the next orchestrator.** Run the start-of-session sequence. Read `docs/evidence/t0023/recommendation-1.md`, then act only on the owner's answer. IEF's NAV file, if the owner downloads it, goes in `~/.hio-research/T-0023/reference/raw/`: add it to `sources.json`, extract it to `nav-ief.csv` (the reader takes State Street's layout, so iShares' needs its own), then rerun `tools/t0023_sleeves.py`.

**Keep in mind:** the soak starts 22:45Z on 2026-11-04 and ends 2026-11-19. Recheck 2027 calendars by 2026-12-01.
