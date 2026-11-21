---
id: REVIEW-2026-11-22-e0004-1-TEST-PLAN
status: in_review
owner: codex/reviewer
---

# E-0004 independent review test plan

Fixed before reading any author handoff or response. Assignment: public `main` OD-0192 and its Assigned reviews row, base `c6886d9e50d034f3a21cb57fa5d736e2a078592c`, head `6720c5c34a130db8ae0a6196fa530e10f3888e91`. Governing design: OD-0190 adoption of `docs/evidence/e0004/preregistration-1.md` at `067bd7b`, with OD-0191 and correction 1's pre-run readings. Reviewer role: independent Codex; work status: assigned for review, not accepted.

1. Establish the immutable sequence: compare the adopted blob, the current text, OD-0190 and OD-0191, source and corroboration records, and commit order. Check for any post-result design or input change that could steer the finding.
2. Inspect BLS reader and CPI state: series, first-release index levels, release-date evidence, cutoff at the preceding month's final trading close, unrounded ratio, 12-month as-of comparison, carry-forward, equality, unavailable breaks, and synthetic tests of these boundaries.
3. Inspect information screen: sample inclusion, SPY-only return use, state months and runs, stress threshold, cluster gap and state allocation, concentration, all four stop bars in both states, and tests that would fail for wrong counts or leakage from outcome data.
4. Inspect precision check: all circular shifts 13 through n−13, state breaks moving with state, no actual-alignment delta reported, step-2-compatible 12-month block bootstrap and seed, median half-width threshold 0.20 points, and tests that discriminate errors.
5. Inspect estimate: full-sample portfolio returns and downside-benefit signs, jointly resampled state and returns, segment boundaries and non-wrapping circular blocks, 10,000 draws with PCG64 and linear quantiles, dropped-replicate rule, 6/24-month intervals, leave-one-stress-cluster-out fragility, decision-rule precedence, and all four specified sensitivities including OD-0191's September 2008 and third-month readings.
6. Inspect iShares NAV reader and corroboration: parsing, date/return basis, C1/C2 bars and evidence, using public issuer material only where rights allow. Check each assigned evidence file's claims against code, tests, preregistration, and records; identify supported, narrowed, or overstated claims.
7. Run the relevant synthetic test suite and targeted independent invented-data probes as needed. No licensed bytes or values, no `~/.hio-research/`, no Azure, no vendor URL. The real-input run cannot be reproduced here; mark any resulting numerical claim as record-supported at most, not independently replicated.
