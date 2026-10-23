---
id: HIO-MIGRATION-MAP
title: Migration map (macsmsf/hio → hio)
status: current
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-24
authorised_by: OD-0017
---

# Migration map: `macsmsf/hio/` → `hio`

Operating model §8.1. **Migration changes no approval, acceptance, finding or review state.**

## Provenance

| Field | Value |
|---|---|
| Source repository | `elusivenode/MACSMSF` (`macsmsf`), private. This repository was created private and made public on 2026-10-24 (OD-0019) |
| Source branch | `docs/hio-a01-baseline` (left **unmerged** in `macsmsf`, per OD-0017) |
| Source commit | `dc4fd0241fe039fd2e8361cb82604a59a0458413` |
| Method | `git subtree split --prefix=hio dc4fd02`, run in a scratch clone (the `macsmsf` repository was not modified) |
| Split head (this repository) | `e32d282ee4c6f8195096c0aa62c25c0a59cf334f` |
| Root tree | `bbf3ee871d8bbb138803366e157f11a6daf5cacc`: **identical** to `macsmsf` `dc4fd02:hio` |
| Date | 2026-10-24 |

## Path map

Every path `hio/<p>` in `macsmsf` maps to `<p>` here. No file was renamed, added or removed by
the split, so the trees are identical. Files added after the split (this file,
`tools/verify_migration.py`, and later commits) are new.

**Not migrated (they stay in `macsmsf`):**
- the four `macsmsf` pointer edits (`85ef0fa`);
- the T-0004 amendment branch `docs/hio-001-boundary-c1` (`fe3fdc7`);
- the history of `macsmsf` commits that did not touch `hio/`.

## Commit references

Commit ids inside the migrated documents refer to **`macsmsf` history** and are kept verbatim
(§8.1 item 4). Read them as `macsmsf@<sha>`. Each one that touched `hio/` maps to a split
commit here. Commit ids that did not touch `hio/` (for example merge commits such as
`a82aa0d`, and `fe3fdc7`) exist only in `macsmsf`.

| `macsmsf` commit | `hio` commit | Subject |
|---|---|---|
| `macsmsf@85ef0fa` | `11006cc` | Stage the HIO A01 architecture, standards and harness baseline (docs only) |
| `macsmsf@72d1e56` | `77d1e80` | Refine the HIO harness: owner decision records, finding lifecycle, review index (harness-0.2) |
| `macsmsf@23ad27f` | `2317025` | Record the HIO cold-start dry-run results and close the gaps they raised |
| `macsmsf@35c9821` | `216a7f2` | Correct the HIO harness: separate instruct/accept/approve/waive; trailers as metadata (harness-0.3) |
| `macsmsf@bada952` | `71606c6` | Record independent HIO A01 architecture and math review |
| `macsmsf@46ea6a5` | `4e602bd` | Add the HIO review branch and worktree protocol (harness-0.4) |
| `macsmsf@b48f83c` | `858e949` | Harden the HIO review-branch gate and remove reviewer handoff conflicts (harness-0.5) |
| `macsmsf@e36dd08` | `8146be9` | Record independent T-0007 pilot review |
| `macsmsf@ad0f116` | `119725f` | Update HIO STATUS after receipt of the T0007-PILOT review |
| `macsmsf@cb29d80` | `1e2a8a0` | Correct the HIO STATUS T-0007 label to harness-0.5; note review branch cleanup |
| `macsmsf@e99fae1` | `2576e11` | Record owner acceptance of T-0007 at b48f83c (OD-0004) |
| `macsmsf@0e3de4b` | `5f07e22` | Correct the A01 baseline for REVIEW-2026-10-18-a01 findings 1-8 (fix commit) |
| `macsmsf@0c74686` | `461c419` | Submit T-0008 remediation response for REVIEW-2026-10-18-a01 (submission head) |
| `macsmsf@bb4aa72` | `2d8d374` | Verify A01 remediation findings 1-8 at submission head |
| `macsmsf@5b4c50e` | `21a8c1c` | Report A01 independent verification and gate readiness |
| `macsmsf@f7a9ec9` | `d990854` | Add the A01 G1 owner decision package and refresh navigation |
| `macsmsf@f2275e2` | `174e53f` | Record the owner's G1 decisions (OD-0006..0009); revise ADR-0010; reviews/reports path |
| `macsmsf@760f73e` | `5ea6287` | Correct the ADR-0010 S1a gate (rev 3); present pending decisions; assign the T-0004 review |
| `macsmsf@8e11581` | `b5e0231` | Record T-0002 and T-0003 research findings (documentation only, no data operations) |
| `macsmsf@4a994d3` | `29a414c` | Record G1 completion (OD-0011), harness-0.6 approval (OD-0012) and T-0002/T-0003 instructions (OD-0013) |
| `macsmsf@73512cf` | `3bb4086` | Fix stale lines: STATUS OD row, T-0002/T-0003 front matter, T-0007 line 60 (OD-0014) |
| `macsmsf@81793f7` | `6961a34` | Fix further stale lines in the accepted T-0006 and T-0007 cards (OD-0015) |
| `macsmsf@dc4fd02` | `e32d282` | Align S1 execution documents to the S1a/S1b split; draft the S1a authorisation (OD-0016) |

## Verification before the first push (`tools/verify_migration.py`)

| # | Check (§8.1) | Result |
|---|---|---|
| 1 | Provenance: every split commit matches one source commit on author, date and message | 23 of 23 mapped |
| 2 | Content: split tree equals `dc4fd02:hio` | identical (`bbf3ee87…`) |
| 3 | Ids and states: front-matter `id`, `status`, `record_status`, `decision`, `accepted_by`, `approved_by` on both sides | 89 documents; 0 differences |
| 4 | Approved content: every OD `applies_to` target at its revision equals the mapped split commit's content (includes approved blobs `8ade1962`, `e3114bd1`, `4000ab18`, `7172659c`) | 15 of 15 equal |
| 5 | Links: relative Markdown links resolve inside the repository | 175 links; 0 unresolved |
| — | Negative test: one broken link committed on a throwaway branch | checks 1, 2 and 5 failed as expected; branch deleted |

Rerun: `python3 -I tools/verify_migration.py <macsmsf clone> dc4fd0241fe039fd2e8361cb82604a59a0458413 e32d282 <out.json>`
(it needs a clone that holds both histories).
