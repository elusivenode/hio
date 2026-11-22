---
id: VERIFY-2026-11-22-e0004-1-1-TEST-PLAN
status: in_review
owner: codex/reviewer
---

# E-0004 verification test plan

Fixed before reading the author's response or handoff. Assignment: OD-0202 and its Assigned reviews row on `main` at `1cad8c0`, base `6720c5c34a130db8ae0a6196fa530e10f3888e91`, head `f349efeaaf1cd3540e8b206d5f79e511ee1f2410`. Review branch `review/e0004-1-verify-1-codex`. Role: independent reviewer; status: in_review. Governing records: the original review and findings, OD-0190's adopted preregistration at `067bd7b`, OD-0196, OD-0197, OD-0200, OD-0201, the return-accounting standard, and source rights in `registers/sources.yaml`.

1. **F-1 provenance and completeness.** Enumerate the CPI reference months actually read by the state code for the 233 run periods, including year-ago lookbacks. Check every such month has a retained first-release page in the allowed BLS-only directories; validate manifests and hashes, release dates, parser output, flat-file comparisons, and the claimed four disagreements. Spot-check parser handling against retained page text, with no new download unless a public BLS page is needed.
2. **F-1 state equivalence.** Recompute the primary and equality-as-accelerating states from first-release levels using the committed tools and an independent comparison where useful. Compare both date by date to the run's allowed `states.csv`, accounting for unavailable periods, and assess whether the tests would catch a wrong level, missing page, date mismatch, or state mismatch. Confirm the addenda state the deviation and limits accurately, preserve the text adopted at `067bd7b`, and do not claim a rerun. Decide whether this evidence closes, narrows, or leaves open F-1 under the adopted input rule and OD-0201.
3. **F-2 current publication.** Inspect current files at the assigned head, including E-0004 reports, preregistration, owner decisions and review navigation, for measurements calculated from EODHD returns. Trace any borderline measurements to tool inputs and the rights record. Exclude git history per OD-0196; do not access EODHD data or vendor sites.
4. **Regression.** Compare E-0004 tools, tests and records at the assigned base and head for changes affecting the original review's conclusions. Run the relevant synthetic tests and direct checks for the two new CPI tools. Inspect the tests for failure sensitivity, not just green status. No portfolio estimation or licensed input read.
5. **Evidence and limits.** Record exact commands, paths, counts and any counterexample in a verification record. Use only the five allowed BLS-derived local locations, and write generated data to a reviewer temporary directory. Write only Markdown under `reviews/`; do not commit or push in this sandbox. State the unverified aspects and what is not approved in the reviewer handoff.
