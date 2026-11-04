---
id: HANDOFF-2026-11-04-go-live-and-first-factor-code
date: 2026-11-04
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code; hiomux orchestrator)
work_status: "capture live, soak pending; T-0016 to T-0019 accepted; cash rebuild repeatable, dispositions unaccepted; US duration spec proposed, calculation on invented inputs only; nothing released, no finality claim"
base_revision: 387eee7ee39d91f5ab983284089a0949bda0fb9f
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/s1b1/2026-11-04-go-live-and-first-factor-code.md
work_commits: [5c68d6c, 6eb5c13, a4ba84b, 0a2c0a1, 6ee8922, 1bfd06f, ac36cbf, a881882, cbd6c8c, 6e2e60d, ba9946d, 9482189, 29dab6f, 6a73b79, 9ea3c0f]
work_card: T-0016, T-0017, T-0018, T-0019
stream: s1b1
---

# Handoff: capture went live; the first factor's code exists

> A dated snapshot. **Not a decision.** The previous handoff in this stream is `2026-11-03-capture-gate-factor-first.md`.

## Start here

- **HIO is capturing real data.** Four files on schedule since 2026-11-04 Sydney (OD-0143). Nobody needs to approve runs.
- **The soak** runs 2026-11-05 09:45 to 2026-11-19 09:45 Sydney: 80 slots, at most 4 misses (`docs/evidence/b3/soak-1.md`). The period and bar were declared first. **Don't dispatch during it** without recording why.
- **The factor programme is blocked on one owner act:** the Treasury (H2) rights reading (`docs/research/T-0002-h2-reading-pack.md`). A comparison reference is also open.
- **Read the runs, not the red.** Runs fail by design on any missed slot. Startup failures ended about 2026-11-04T16:30Z, so a failure after that is real. Read it with `gh run view <id> --log`.

## Done

| Step | Result | Record |
|---|---|---|
| Go-live package | four URLs, punctuality bar, staging statement, order of steps; adopted at `3cee431` | OD-0142, OD-0143; `docs/evidence/S1B1-go-live-package.md` |
| T-0016 go-live PR | Codex READY; merged as `0a2c0a1` | OD-0144 |
| First live run `41733292506` | three files captured; the expert-judgement parser failed closed | `docs/evidence/b3/first-run.md` |
| T-0017 parser fix | Codex READY; re-run `41737776204` captured it, 466 flags | OD-0145, OD-0146 |
| Alert, reviewer rule, first unattended run | targeted apply; rule removed; run `41741724257` ran alone | OD-0146 correction 1 |
| I-5 | real scheduled failure email received; deliberate test dropped | OD-0149 |
| First cash rebuild | AUD 214 `differs: precision`, USD 27 agree and 3 missing; no unexplained residual | OD-0147; `docs/evidence/b3/cash-rebuild-1.md` |
| T-0018 repeatable rebuild | `tools/cash_rebuild.py`; rerun byte-identical; **no Codex review** | OD-0148 |
| US duration spec 0.1.2, T-0019 calculation | Codex NOT READY (three findings), then READY; all `verified_closed` | OD-0150 to OD-0153 |
| Drafts | vendor questions revised (not sent); planning patch to the proposed documents; H2 pack; plan differences | OD-0147, OD-0150 |
| Architect | two consultations: `…165541-ask-dee0` changed the go-live order, `…093209-ask-a45b` set the work order | OD-0142, OD-0147 |

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| `main` green | full suite on the T-0019 head; CI on each merge | 1148 passed |
| The live receipts read back | owner's reader identity; hashes and parse | `docs/evidence/b3/first-run.md` |
| The rebuild repeats | tool at `a881882` against the first driver | four `data.csv` byte-identical |
| CMT reproduces the standard | RA-INV-013 fixtures; RA §14.6 | pass; about -0.397% |
| Receipts complete | §6.2 5.0–5.10, four receipts | PASS; see the ODs |

## Known limitations and not verified

- **Unattended reliability is unproven** until the soak ends. Then the dead-man exercise (its method comes to the owner first), the CI-run audit, and replay on live receipts.
- **Pricing-basis error in the CMT is unmeasured.** The experiment must report a zero-curve repricing sensitivity. It isn't built.
- **The cash results are thin in USD** (about six weeks; `last/30`), and AUD is 2026 only. Cash dispositions and the spec's `reference_decimals` (4 declared, 6 live) await the owner. Criterion 3 isn't established.
- **Calendars end 2026-12-31:** runs fail from then without the 2027 files (recheck by 2026-12-01). Hard date.
- **Two plan differences remain** (`docs/evidence/b3/plan-differences.md`), so state and code disagree. Their cause isn't established.
- **T-0018 had no independent review**, by the owner's acceptance.
- **`az` now has the `log-analytics` preview extension** on the owner's Mac.
- **The H2 quotes** came through a page-to-text tool.

## Didn't work

- **My go-live order was wrong twice before review:** the alert came after the rule was removed, and the failure email came too late. The architect caught both.
- **A parser built on a deleted sample** failed on the live file. The package had named the risk.
- **Unguarded command chains:** one pushed a tag before a check passed, and another committed past a failed `check_repo`. Gating with `|| exit 1` then stopped a bad receipt at 5.7.
- **A loose tolerance hid a factor-of-100 convexity bug** until another test failed.
- **The classifier refuses PR merges by Claude** ("Merge Without Review") from #74 on. The owner ran each merge with `!`, which took many turns.
- **Index rows inserted by sed** silently missed when the anchor row wasn't on that branch.

## For the index

- `[capture] The completeness check has no start date, so slots before go-live count as missed until due + 27h: expect red runs at any fresh start, and compute the list first. Source: src/hio/sources/schedule.py:130; docs/evidence/b3/first-run.md.`
- `[capture] Moving the workflow with LIVE_AUTHORISATION set arms cron on merge; the capture reviewer rule is the only hold. Source: docs/evidence/S1B1-go-live-package.md.`
- `[capture] Under AEDT and EST, 22:45 to 23:00 UTC is the only overlap of the RBA first and NY final slots, so one run can test all four files. Approval time, not dispatch time, decides which slots run. Source: OD-0143; run 41733292506.`
- `[sources] The RBA expert-judgement CSV opens with prose holding both "date" and "type" in one cell; its header is Date, Expert Judgement type, Series title, Details. Source: T-0017; src/hio/sources/datasets.py.`
- `[sources] Publication URLs: F1 serves two datasets, so five datasets are four URLs. NY Fed sofrai is under /api/rates/secured/{ratetype}/last/{n}. Source: docs/evidence/S1B1-go-live-package.md.`
- `[sources] The live FIRMMCTRI has up to 6 decimals; cash.aud.overnight 0.3.0 declares 4, so every AUD period classifies differs: precision. Source: docs/evidence/b3/cash-rebuild-1.md.`
- `[build] The F1 file runs back to 2011, past the cited calendars: ingest refuses unless vintage_store(earliest=...) states a window. Source: T-0018; tools/cash_rebuild.py.`
- `[alert] A failed capture still writes an attempt record, so a failed run does not fire the dead-man; infra/tofu/README.md says the same test proves both, which monitoring.tf contradicts. Source: docs/evidence/b3/soak-1.md; architect 20261103T165541-ask-dee0.`
- `[ci] GitHub's scheduled firings ran about a minute to five minutes late on the first day; a scheduled run waiting on a reviewer holds its old code and can be cancelled. Source: runs 41734200727, 41741724257.`
- `[infra] tofu inputs can be read from state without printing them, but a full plan after B-1 shows drift, so use a targeted plan and show the owner. Source: OD-0146 correction 1.`
- `[factors] In CMT, the decomposition residual tests the Taylor terms only: both sides use the same flat yield, so it cannot measure pricing-basis error. Source: F-REVIEW-2026-11-04-t0019-1-2.`
- `[factors] A maturity-anchored schedule breaks on a leap-day strike; the spec anchors coupons to the strike with the day clamped. Source: F-REVIEW-2026-11-04-t0019-1-1.`
- `[rights] The Federal Reserve Board's change removes Build Your Package in the week of 2026-11-09, but historical XML stays on release pages: not a November deadline for losing history. Source: federalreserve.gov/data/data-download-fred-information.htm, read 2026-11-04.`
- `[rights] No Treasury page read grants or restricts reuse: H2 rests on the 17 U.S.C. §105 presumption. Source: docs/research/T-0002-h2-reading-pack.md.`
- `[process] A worker-free receipt from a scratch clone needs a local branch for check_review_assignment, which must run in a worktree at T. Source: OD-0144.`
- `[process] A verification record linking to the response file fails check_repo at 5.7 until the work is merged, so merge the work first when the record links to it. Source: OD-0153.`
- `[process] A records PR that adds an OD index row conflicts with an open PR adding a row at the same place: run git merge-tree first. Source: OD-0151.`
- `[process] The classifier refuses gh pr merge from Claude as "Merge Without Review": give the owner the command with --match-head-commit; base branch policy also blocks it until CI ends. Source: PRs #74 to #88.`
- `[hiomux] sa ask refuses at main when the bundle exceeds 90,000 bytes; --rev <older> works if the question supplies newer state. Distil 3 doesn't shrink it. Source: OD-0142 correction 1.`
- `[review] Codex has now found a real defect or spec overclaim that a passing suite missed in T-0013, T-0014, T-0015 and T-0019, and was READY first time on T-0016 and T-0017, both small. Source: OD-0144, OD-0146, OD-0152.`

## Open findings (from `reviews/README.md`)

- F-VERIFY-2026-10-28-h6-1-6-1 (high, H6 parked). HIO-ADR-0012 F-1 and F-3 still `remediation_claimed` (OD-0054). All T-0016 to T-0019 findings are `verified_closed` or none opened. No finding is waived.

**Receipt sweep:** this session's review branches are received. `review/t0009-1-verify-2-codex` is local only, by design (OD-0077).

## Assumptions made

- **"approved" (OD-0148) and "you are authorised to proceed" (OD-0150)** were read narrowly, and said so at the time. Neither was taken as a rights decision, a dispositions acceptance or the probe destroy. Neither was corrected.
- **Running the merge of #81 was taken as the yes** to accepting T-0018 without Codex, since Claude had said so. Not contradicted.
- **Local cash values:** copies were deleted after use, and only counts, classes and ids are in the repository.

## Conflicts found between documents

- **`MAP.md`** still says C5 blocks B-3 go-live, and its Current column predates capture. Substantive map changes need the owner; left, for the next distil.
- **`infra/tofu/README.md`** says the I-5 test also proves the Azure alert, and asks for a run failed "on purpose". OD-0149 and `monitoring.tf` differ. Left.
- **The factor-first document** calls the Board retirement time-sensitive more firmly than the Board's notice supports. Adopted text stands; the correction is above.
- **The Authorisation B package** lists the rule removal before the dispatch. The adopted go-live package supersedes that order.

## NOT approved by this session

- **Any finality claim, C5 amendment or final label;** S1b-1 completion; G2.
- **H2 or any other rights decision.** The Treasury source stays `unverified`.
- **The cash dispositions, or any cash spec change.**
- **Spec `rates.us.cmt_10y.total_return`:** proposed only. The duration experiment; any real yield; any download.
- **Base camp, the roadmap and the plan,** though patched: still proposed.
- **Sending vendor questions; any purchase.**
- **The probe destroy, the dead-man exercise, distil 3.**

Owner acts this session: OD-0142 to OD-0154 as recorded.

## Next authorised action

**Nothing new is authorised for Claude.** The owner decides:
1. **H2 Treasury rights**, with a retention duration, V2 and V3. Unlocks real duration work, with the experiment's own yes.
2. **The vendor questions:** send or not. Also a route to the comparison reference.
3. **Destroy `rg-hio-probe`:** allowed since 2026-11-04T06:36:50Z, on a "go".
4. **The architect:** its context budget (it refuses at `main`) and the overdue performance review (14 consultations; due after 5). Held-out cases.
5. **Whenever suits:** the cash dispositions; the C5 choice; distil 3; adopting the planning documents.

**Hard dates:** the soak ends 2026-11-19; 2027 calendars rechecked by 2026-12-01 and loaded before 2027-01-01; second copy (S-7) within the first capture month.

## Completion block

| Field | Value |
|---|---|
| Branch and full SHA | `records/od-0154` at the commit adding this file; `proposal/distil-3` (proposed, unmerged) |
| Pushed? PR link | yes, by PR |
| Received into `main`? | REVIEW-…-t0016-1 (`a4ba84b`), REVIEW-…-t0017-1 (`1bfd06f`), REVIEW-…-t0019-1 (`ba9946d`), VERIFY-…-t0019-1-1 (`6a73b79`) |
| Next actor | owner |
| Prompt for the next actor | "Run `hio-orch`. Check hiomux `54fe4e86…`, PROTOCOL `13a45eb7…`. Stop if `main` lacks OD-0154 or this handoff. Read this handoff and `docs/evidence/b3/soak-1.md`. Capture is live, so check recent `s1b1-capture` runs first, and don't dispatch during the soak without recording why. The architect refuses at `main`; use `--rev` until its budget is fixed. Then put the owner's next decisions, starting with H2." |
