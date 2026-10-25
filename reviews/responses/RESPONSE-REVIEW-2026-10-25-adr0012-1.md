---
id: RESPONSE-REVIEW-2026-10-25-adr0012-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-25-adr0012-1, F-REVIEW-2026-10-25-adr0012-2, F-REVIEW-2026-10-25-adr0012-3]
responds_to: REVIEW-2026-10-25-adr0012   # reviewer commit 1a05d8e6e0dd453c91cc37aba16c921cd6c97238 (tag reviews/REVIEW-2026-10-25-adr0012); record blob f3f104da15295b3d6bfb3fe2cbb082cf481354bc, sha256 3b12c9fee25b85b609f0195e777c308d55e57d70010b9bddd28691c2bbfe10f2; received by OD-0050 at 6fbec1a
previous_submission_head: 1d68da3e90d879da6318082551bab943c60cf68b
authorised_by: OD-0051
fix_commits: [bc939f778066d96ebafc2364640f9ebf0457d09e]
test_commits: []   # documentation-only; no test applies
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-25-adr0012-1.md
created_at: 2026-10-25
---

# Remediation response 1: HIO-ADR-0012 timing, finality and Index revisions

> **Author's claim, not verification.** All three findings stay **open**. HIO-ADR-0012 stays
> **proposed**. Only Codex may verify closure, at a fixed head the owner assigns.

The branch merged `main` at the receipt (`6fbec1a`) before the fix, as harness-0.7 §6.2 step 6
requires. The reviewed head `1d68da3` stays in its ancestry. The fix is one commit,
`bc939f7`, changing only `docs/decisions/HIO-ADR-0012-staged-s1b.md` (revision 2).

## Closure map

| Finding | Root cause | Fix (ADR section) | The review's own scenario, re-run on the new text |
|---|---|---|---|
| **F1** (high) | revision 1 set `knowable_at` = the documented publication time P for any first capture within grace, so a deferred publication was given an earlier time than the vintage's | **§4.3.1** P1/P2/P3. The schedule (renamed P_doc/W_doc) only schedules captures and sets the finality window. A vintage is placed by an **evidenced instant** (`publisher_timestamp`), else the **first capture that contains it** (`captured_on_schedule`, `knowable_at` = `captured_at`), else the **fail-closed** `schedule_only`. P1 needs the source's timestamp semantics evidenced first | RBA defers to 09:35, first capture 09:45: **09:45** (P2) or the recorded 09:35 header instant (P1), never 09:20. SOFR Index published 08:20, captured 08:30: **08:30**, never 08:00 |
| **F2** (high) | "final" was decided by `knowledge_cutoff` after W alone; no evidence required that the post-window value was held | **§4.3.3–§4.3.4**. A vintage is final at cutoff C only if a **verified** record exists with W_doc ≤ `attempted_at` ≤ C, covering the key, matching the value, with no later vintage. A failed, missing or parse-failed check, or an attempt alone, never counts. Release finality needs every input final; the evidence ids are release inputs | revision at 15:50, W 16:00, final check 16:30, build at 16:10: no verified record in [16:00, 16:10], so **not final**. After a 16:30 `verified_changed`, a build with cutoff ≥ 16:30 is final |
| **F3** (medium) | the SOFR Index was grouped under SOFR's 1 bp revision rule | **§4.3.5**. Separate rules and **independent per-dataset checks**; a post-window check is required for each dataset, whether or not its sibling changed or `revisionIndicator` shows a revision. `cash.usd` finality depends on SOFR only; the Index triangulation needs both | SOFR unchanged, Index corrected at 14:30: the 15:00 Index check records `verified_changed` (a new Index vintage) while the SOFR check is `verified_unchanged`. `cash.usd` stays final, and the triangulation is final only after the Index check |

## Evidence

| Check | Result |
|---|---|
| Sections of the ADR that changed | **§4.2** (two gate cells), **§4.3** (rewritten), **§4.7** (one sentence), and consequential lines in §3, §5, §6, §8, the front matter and the changelog. §1, §2, §4.1, §4.4, §4.5, §4.6, §7 and *Approval* are **byte-identical** to the reviewed head (compared section by section) |
| The §2 supersession table | unchanged: S10-B2 and S10-B5 superseded, S10-B8(ii) in wording only if the FX source changes. S1a column untouched |
| §5 obligation mapping | every row kept. One row added (capture-attempt records and finality evidence, **new, additive**) and the S1-A14 row's wording extended. No row deleted or weakened |
| Accepted S1a content | `git diff --stat 084154c HEAD -- src tests tools specs .github pyproject.toml uv.lock` is empty. The four S1a `data.csv` hashes cannot move |
| Approved standards, HIO-ADR-0010, harness-0.7, `registers/` | unchanged (`git diff --stat main HEAD` over those paths is empty). Every source permission is still `unverified`/`unknown` |
| The S1a code the fix relies on | `src/hio/marketdata/knowability.py:51-52`: a scheduled capture that sees a **revised** value already gets `captured_on_schedule` with `knowable_at` = the capture instant. `knowability.py:60`: a late or unscheduled capture gets `schedule_only`. `src/hio/marketdata/capture.py:98-99`: an identical consecutive re-fetch **writes nothing**, which is why finality needs the additive attempt record (F2) |
| Repository checks | `tools/check_repo.py` PASS; `ruff` clean; `pytest` 278 passed (see the handoff) |

## Escalations (not decided by this response)

1. **Q-013 (observation semantics).**
   - The approved observations standard §3 defines `captured_on_schedule` as "the documented
     release time preceding that capture". It does not state the capture-instant reading that
     accepted S1a code already applies to a revision. Using it for a **first** capture is a
     clarification of approved semantics, and needs an opt-in change to accepted S1a placement
     behaviour.
   - The ADR does not depend on it: **P3 is the fail-closed fallback** (`schedule_only`, no
     `as_known_by_market` claim).
2. **Release manifest schema.** If finality evidence ids cannot be release inputs without
   amending the releases standard, that is an escalation (ADR §4.3.4).
3. **Header semantics and the Index revision rule are not evidenced here.**
   - For the NY Fed API no header was examined. The review record's account of the Index
     correction rule was **not independently re-read**; this response does not claim to have
     verified the NY Fed's page.
   - Both are S1b-1 gate items (d, d2), and examining them needs an owner-approved fetch.

## Not claimed

- That any finding is closed or verified. Only Codex can verify.
- That the ADR is approved, that any source right is verified, or that S1b is authorised.
- That the additive attempt records have been implemented. They are specified, not built.
