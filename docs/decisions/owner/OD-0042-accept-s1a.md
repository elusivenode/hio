---
id: OD-0042
title: "Owner acceptance: HIO S1a (synthetic-fixture foundation, HIO-ADR-0010 rev 3; OD-0017, OD-0020) accepted as complete; S1b not authorised"
decision: accept_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-accept-s1a.md (pasted by the owner, verbatim)
  sha256: f412d702663f0bdfb86948d94ce524c16408161830f07e58dc2a4cd4ffcff048
  date: 2026-10-25
  quote: "I accept HIO S1a, the synthetic-fixture research foundation authorised by OD-0017 and OD-0020 under HIO-ADR-0010 revision 3, as complete, subject to the final evidence-integrity checks below."
applies_to:
  - path: src/, tests/, tools/, specs/, .github/, pyproject.toml, uv.lock
    revision: 084154ccb0fd1c13150d77d02eb525007a5b161e   # independently reviewed head (VERIFY-2026-10-24-s1a-1-11)
  - path: /
    revision: 773a557534280ca7a19ce69a16394343f73e2139   # integration of PR #2 into main; tree equal to 084154c
  - path: docs/evidence/S1A-acceptance-package.md
    revision: edc80d33a0588a9c5dcc6d4cd15d47204ed167ad   # blob 4a61682dac9d2e91c004ec4892b6ea21a9b9e172; integrated by 8140edb
related: {adrs: [HIO-ADR-0010], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-1, F-REVIEW-2026-10-24-s1a-1-2, F-REVIEW-2026-10-24-s1a-1-3, F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-5, F-REVIEW-2026-10-24-s1a-1-6, F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0042: S1a accepted

## Owner action

**S1a is accepted as complete:** the synthetic-fixture research foundation authorised by OD-0017
and OD-0020 under HIO-ADR-0010 revision 3. The acceptance applies to:

- **the implementation** at the independently reviewed head
  `084154ccb0fd1c13150d77d02eb525007a5b161e`, integrated by merge
  `773a557534280ca7a19ce69a16394343f73e2139`. Its object ids:

  | Path | Object id |
  |---|---|
  | `src/` | `bcce5e8d776538769e3fccef5b8c40040295bd01` |
  | `tests/` | `ec9bb960fac792880f007841d753ee91877b6563` |
  | `tools/` | `8157768518e980d0047357f3e47daaf51aa551c8` |
  | `specs/` | `ccea37c960fb7053cf21921a0bc7b858caaeb90e` |
  | `.github/` | `61ca7dd0fc8d5912b7caa9323e524f8ee4b63d92` |
  | `pyproject.toml` | `9f93bcb0207f25a2c25145d0b7ad7c93b6b1b301` |
  | `uv.lock` | `fbd187e03a2d3f60b61d6940acc0dd941435582f` |

- **the evidence** in [`docs/evidence/S1A-acceptance-package.md`](../../evidence/S1A-acceptance-package.md)
  at `edc80d33a0588a9c5dcc6d4cd15d47204ed167ad`: blob `4a61682dac9d2e91c004ec4892b6ea21a9b9e172`,
  sha256 `b2237d348942012ed3b00aa4704007db77ef5092e326168d7e83a781bcda34fe`. It was integrated
  into `main` by `8140edbc4a4794f328147ecee75224a2c792e28b`.

**Limitations acknowledged with the acceptance** (package §4):
- synthetic-only data;
- Q-008's S1a-specific network-control decision: no CI egress firewall, which is not proof of
  isolation;
- Hatchling's packaging lock limitation (`>=1.25`, not hash-locked);
- release identities that depend on the revision.

## Final evidence-integrity checks (all passed, 2026-10-25)

| Owner check | Result |
|---|---|
| 1. Identifiers resolved from Git | `084154ccb0fd1c13150d77d02eb525007a5b161e`; `773a557534280ca7a19ce69a16394343f73e2139` (parents `6fe35cf…`, `084154c…`; tree equal to `084154c`); branch `edc80d33a0588a9c5dcc6d4cd15d47204ed167ad` |
| 2. `main` unchanged | `main` = `origin/main` = `df3af48ed874acf3365ecddc1861f93abc1be03e` before integration; an ancestor of the branch |
| 3. Branch and evidence match the handoff | branch head `edc80d3…`, the commit that last touched the handoff, package, OD-0041 and HARNESS-…-2. Evidence sha256 on the branch: transcripts `51b513a0…`, `6f989c20…`, `a3f818e5…`; T-0004 record `e70bd93d…`. All 12 preserved evidence files re-checked (`shasum -c` 12 OK) |
| 4. OD-0041 and the S1-A16 PASS record | OD-0041 `record_status: recorded`; HARNESS-2026-10-25-s1a16-2 `result: satisfied`, its checks complete; HARNESS-…-1 kept as `pending` (immutable) |
| 5. No implementation, test, specification, approved-standard or CI change | `git diff --quiet 084154c edc80d3 -- src tests tools specs .github pyproject.toml uv.lock docs/standards docs/harness AGENTS.md docs/decisions/HIO-ADR-*` exit 0; object ids above equal at both; approved contract blobs `419992f2…`, `d0a25b3b…`, `cb7a937d…` unchanged |
| 6. No unresolved S1a requirement | all 15 indexed findings are `verified_closed` and none is waived; S1-A1…A15 met for S1a (S1-A10, S1-A13 and the real-source parts of S1-A3 and S1-A12 are S1b); S1-A16 satisfied; the HIO-ADR-0010 rev 3 S1a list is met; the decisions gated on acceptance are made (OD-0038) |

## What this record does NOT do

- It does **not** authorise S1b. S1b still needs:
  - T-0002 `owner_verified` rights per source;
  - evidence of publication timing, calendars and the AUD rate regime;
  - a separate network and credential-control decision (OD-0038);
  - Q-010 in S1b design;
  - its own authorisation (HIO-ADR-0010 rev 3).
- It does **not** approve observations v0.3 (blob `61ddd58e`), and it does not alter any standard,
  ADR, harness rule or the implementation.
- It does **not** accept or merge T-0004, and it does not resolve Q-003, Q-004, Q-005b, Q-006 or
  Q-010.
- It does **not** decide the run-1 stale-line candidates.

## Corrections (append-only)

None.
