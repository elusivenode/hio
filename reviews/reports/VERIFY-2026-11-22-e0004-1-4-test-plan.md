---
id: VERIFY-2026-11-22-e0004-1-4-TEST-PLAN
status: in_review
owner: codex/reviewer
---

# Test plan: VERIFY-2026-11-22-e0004-1-4

Fixed before reading Response 4 or the author handoff. Authority: OD-0211 and its Assigned reviews row on public `main`; base `2f1251b3252955aa609a4618e159b254a7083a1e`, head `144d39a51ebd17ddf61a0cf329816aae2706ba28`, branch `review/e0004-1-verify-4-codex`. Checkout and assignment match. The work is in review. OD-0210 governs the relocation; the F-2 record, OD-0196 and the earlier verification define the context. The EODHD rights row limits data use.

1. **Relocated records:** Read each of the ten named current evidence files and check that it contains only identity, record kind, standing, local-content pointer and public reference identifiers, with no EODHD-dependent result, reading, sign, count or measure. Check every named repeated summary for remaining EODHD-dependent result statements.
2. **Results-store tool:** Inspect `tools/results_store.py` and its synthetic tests. Run focused tests without accessing the local store or licensed inputs. Check manifest and catalogue integrity, missing and extra files, path safety, and whether the tests support Response 4's tool claims. The actual local store and byte-for-byte copy claim are unavailable for independent verification.
3. **Remaining current disclosures:** Enumerate tracked files outside the relocated set and search for EODHD-dependent result-bearing content, including prose without numerals. Record each by file and line without reproducing a value. Distinguish deliberately untouched owner decisions, history, review records and public preregistrations from other locations. Identify which residuals matter to the owner. Exclude git history from the existence question.
4. **Regression and verdict:** Compare base and head for changes in acceptance, verdict or finding state, check links and repository checks, and apply OD-0210's explicit boundary to give an independent technical judgement on F-2. Record limits and handoff under `reviews/`; leave files uncommitted for the runner.

No private research path, EODHD bytes or values, Azure, vendor URL, licensed-input rerun, or external transmission. No package or tool is planned for installation.
