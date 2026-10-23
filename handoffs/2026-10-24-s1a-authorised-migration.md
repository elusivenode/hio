---
id: HANDOFF-2026-10-24-s1a-authorised-migration
date: 2026-10-24
actor: claude/documentation-agent (Claude Opus 5.5, Claude Code session)
work_status: authorised (OD-0017 S1a; OD-0018)
base_revision: e32d282ee4c6f8195096c0aa62c25c0a59cf334f   # = macsmsf@dc4fd02, the migration source
head_revision: self       # resolve: git log -n1 --format=%H -- handoffs/2026-10-24-s1a-authorised-migration.md
work_commits: [517c1c4, 1c01327, 39da54e]
work_card: T-0005 (S1a), T-0004 (mechanics), roadmap
---

# Handoff: S1a authorised; HIO migrated to `elusivenode/hio`

> A dated snapshot. **Not a decision.**

## Done

- **Migration (OD-0017):**
  - `macsmsf@dc4fd02` was split with `git subtree split --prefix=hio`, in a scratch clone;
    `macsmsf` itself was untouched;
  - the result became the local repository `elusivenode/hio`;
  - all five checks passed **before the first push** (see `MIGRATION-MAP.md` and below).
- **Records:**
  - the owner's message archived verbatim;
  - **OD-0017 recorded** (the earlier draft is noted under Corrections);
  - **OD-0018 recorded**;
  - T-0005 set to `authorised` for S1a only;
  - STATUS rewritten;
  - the OD, history and review indexes updated (the T-0004 mechanics confirmation is
    transcribed).
- **Adapted to the new root (post-migration commits, not part of the verified split):**
  - the README, CLAUDE.md, the skills, and the operating model §8.1 status sentence
    (status only);
  - `tools/check_review_branch.sh` now detects the `hio/` prefix from the assigned head.
- **Roadmap (OD-0018):**
  - G1 evidence and week anchors corrected;
  - S2/S3 moved behind G2;
  - D1 and the second of S2/S3 now end after week 13;
  - the futures procurement task flagged as not raised.
- **ETF diagnostic card (OD-0018):** proposed, SMSF-owned. It is in `macsmsf` on branch
  `docs/etf-diagnostic-card` (`560cfd6`), unmerged and **not authorised**.

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| Provenance | `tools/verify_migration.py`, check 1 | 23/23 commits mapped |
| Identity | split tree vs `macsmsf dc4fd02:hio` | identical, `bbf3ee87` |
| Ids and states | front matter on both sides | 89 documents; 0 differences |
| Approved content | 15 OD `applies_to` targets at their revisions | 15/15 equal |
| Links | relative Markdown links | 175; 0 unresolved |
| The checks can fail | a broken copy on a throwaway branch | checks 1, 2 and 5 failed |
| Review-branch script | a synthetic pass and fail here; the historical branches `b48f83c..e36dd08` and `0c74686..5b4c50e` in `macsmsf` | pass / fail / pass / pass |

## Known limitations and not verified

- **Approved documents still write paths as `hio/<p>`.** They were preserved, not edited. The
  path map and the README explain the convention.
- **T-0004 receipt.** The review branch is in `macsmsf`, cut from `macsmsf@760f73e`, so receiving
  Codex's record into this repository needs a decided procedure.
- **No S1a code exists yet.** Next comes harness CI, then the contracts.
- **The `macsmsf` staging branch** is frozen at `dc4fd02`. Its STATUS still describes the
  pre-migration state, by design: it is the source snapshot.

## Open findings

None recorded.

## NOT approved by this session

- S1a is authorised, **not accepted**.
- S1b is not authorised.
- No merge: neither T-0004 nor the staging branch, and no `macsmsf` pointer.
- No source permission is verified. No vendor contact.
- The ETF workstream is not authorised.
- The roadmap remains a recommendation.

## Next authorised action

S1a under OD-0017, in this order:
1. the harness CI checks (operating model §8);
2. the `uv` project skeleton with the pinned stack;
3. the contracts;
4. the observation model;
5. the constructions;
6. the gates.

All on fixtures only. Then submit at a fixed revision for Codex review.
