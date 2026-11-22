---
id: VERIFY-2026-11-22-e0004-1-3-TEST-PLAN
status: in_review
owner: codex/reviewer
---

# Test plan: VERIFY-2026-11-22-e0004-1-3

Fixed before reading Response 3 or any author handoff. Authority: OD-0208 and its Assigned reviews row on public `main`; base `3528e8e537a7505d4de3af469f9de0a4dcba4183`, head `2f1251b3252955aa609a4618e159b254a7083a1e`, branch `review/e0004-1-verify-3-codex`. The checkout matches. Work is in review. OD-0206 sets the owner's line; OD-0196 excludes history. The F-2 finding and the previous verification are governing review records.

1. **F-2, all current files:** Inventory the tracked tree at the head, search it for EODHD-related figures and other suspect numerical claims, and trace each suspect to its source or computation without reading licensed input. Apply OD-0206: EODHD-derived counts, measures and bounds must be absent; qualitative readings, stated dates of disagreement and fund-availability sample length may remain. Distinguish RBA, BLS, H.10 archive, SEC, synthetic, design thresholds and public-page figures from EODHD-derived numbers. Do not copy suspected values into review output.
2. **Owner observation:** If a retained qualitative reading may itself be a restricted derived value, record that as a separate observation for the owner. Do not conflate it with whether the explicit OD-0206 numerical line was met.
3. **Regression:** Compare the base and head, especially the seven files named in OD-0206, for any changed result, verdict or acceptance statement. Use focused checks if a changed file has executable behavior; do not rerun the licensed-input experiment.
4. **Record and handoff:** State the technical outcome for F-2 at this head, limits, any observations and the regression conclusion. Write only under `reviews/`, leave files uncommitted for hiomux, and report sha256 for each added file.

No reads under `~/.hio-research/`, no EODHD bytes or values, no Azure, no vendor URL or licensed-input rerun. Public reads only. Git history is outside the F-2 existence question; the base-to-head diff is used only for regression and provenance. The author response is an unverified claim until independently checked.
