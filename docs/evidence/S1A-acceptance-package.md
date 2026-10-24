---
id: HIO-EVIDENCE-S1A-ACCEPTANCE-PACKAGE
title: S1a final acceptance package (all acceptance evidence complete; the owner's acceptance record is the only remaining step)
status: prepared_for_owner   # NOT acceptance
owner: implementation agent (prepared); owner (decides)
created_at: 2026-10-25
authorised_by: [OD-0041]
supersedes_for_current_state: docs/evidence/S1A-acceptance-readiness.md   # kept unedited as the dated 2026-10-25 matrix
---

# S1a final acceptance package

> **Prepared for the owner's decision. S1a is not accepted.** Every S1a acceptance requirement
> now has evidence. The one remaining step is the owner's acceptance record itself.

## 1. What acceptance would apply to

**The implementation**, by git object id. It is identical at every revision listed:

| Path | Object id |
|---|---|
| `src/` | `bcce5e8d776538769e3fccef5b8c40040295bd01` |
| `tests/` | `ec9bb960fac792880f007841d753ee91877b6563` |
| `tools/` | `8157768518e980d0047357f3e47daaf51aa551c8` |
| `specs/` | `ccea37c960fb7053cf21921a0bc7b858caaeb90e` |
| `.github/` | `61ca7dd0fc8d5912b7caa9323e524f8ee4b63d92` |
| `pyproject.toml` | `9f93bcb0207f25a2c25145d0b7ad7c93b6b1b301` |
| `uv.lock` | `fbd187e03a2d3f60b61d6940acc0dd941435582f` |

| Revision | Role |
|---|---|
| `084154ccb0fd1c13150d77d02eb525007a5b161e` | reviewed head, verified by VERIFY-2026-10-24-s1a-1-11 |
| `773a557534280ca7a19ce69a16394343f73e2139` | integration of PR #2 into `main` (tree equal to `084154c`) |
| `3fd129e946498e180b9f78a13d3f745afb46c638` | S1-A16 run 1 (Claude half) |
| `df3af48ed874acf3365ecddc1861f93abc1be03e` | S1-A16 run 2 (Codex half), Y; CI `40143785814` success |

**The evidence:** the records listed in §2. They are on `main` at Y, except this package,
OD-0041 and HARNESS-…-2, which the commit adding this file adds.

## 2. Requirements and evidence

| Requirement | Status | Evidence |
|---|---|---|
| S1-A1…A15 (implementation plan) | **met for S1a**, as mapped in the [readiness matrix](S1A-acceptance-readiness.md) §4; the implementation is unchanged since. S1-A10 and A13, and the real-source parts of A3 and A12, are **S1b** | readiness §4; the 278 tests pass at Y; CI at Y |
| **S1-A16** (§10 fresh-session test) | **satisfied** (OD-0041) | [HARNESS-…-1](../../reviews/records/HARNESS-2026-10-25-s1a16-1.md), [HARNESS-…-2](../../reviews/records/HARNESS-2026-10-25-s1a16-2.md); two-revision basis, OD-0040 |
| HIO-ADR-0010 rev 3 S1a list | **met** | OBS-INV-001…007, RA §3.2 and CASH-USD-INV-3, FXC-INV-1…4, RA-INV-021, releases §6.1, the rights fail-closed fixtures, import and independence, reproducible rebuild, harness CI: mapped in the [evidence package](S1A-evidence-package.md) and the readiness §4. "Codex review at an assigned head": V11 READY at `084154c`, received (OD-0037) |
| Findings | **none open**: F1–F7 verified closed at their reviewed heads; none waived | [`reviews/README.md`](../../reviews/README.md) |
| Release reproducibility | the four `data.csv` sha256 (`9e3a03e9…`, `97faf4e8…`, `6e628493…`, `b8ea0d6f…`) reproduced at `084154c` (V11), at `3fd129e` (all four by the preparer; the excess release independently by run 1) and at Y (the preparer) | records cited |
| Decisions gated on acceptance | **made**: Q-007 ratified, Q-008 accepted for S1a only, Q-005a confirmed, Q-010 deferred to S1b design (OD-0038). Q-001, Q-002 and Q-002-R1 approved (OD-0029, OD-0030, OD-0035) | [`open-decisions.md`](../decisions/open-decisions.md) |

## 3. Remaining decisions

**Required for S1a acceptance:** only the owner's S1a acceptance record.

**Not required** (they stay open after acceptance):
- **Observations v0.3** (blob `61ddd58ed49af9fed395eaa17e61dfc7fb451fe6`): a separate approval;
  a consolidation only.
- **Run-1 stale-line candidates:**
  - the §10 prompt path `hio/AGENTS.md`, in the approved operating model;
  - `docs/decisions/README.md` saying "S1a is not authorised";
  - the S1a *Assigned reviews* row saying "findings open";
  - research brief `3fd129e` citing no OD.

  Each needs its own instruction.
- **Open questions:** Q-003 (research use of `reconstructed`); Q-004, Q-010 and the network and
  credential-control decision (S1b); Q-005b and Q-006 (consumer integration).
- **Housekeeping:**
  - Codex's received `review/s1a-1-verify-*` branches (owner or Codex to delete);
  - the T-0004 `macsmsf` merge decision, which belongs to the SMSF process and is not S1a.

## 4. Limitations accepted with S1a

These are known, and none of them blocks S1a:
- **Synthetic data only.** No real source, credential, bucket or schedule.
- **No CI egress firewall** (Q-008, S1a only). This is not proof of network isolation.
- **Hatchling** is constrained by `>=1.25` and not hash-locked.
- **Release ids depend on `code_ref`,** so they reproduce only at the same commit. The
  `data.csv` bytes reproduce at any revision with unchanged code.

## 5. What acceptance would not do

- **It would not authorise S1b.** S1b needs, per ADR-0010 rev 3:
  - T-0002 `owner_verified` rights for every S1b operation, per source;
  - publication timing, calendars and the AUD rate regime evidenced;
  - the separate network and credential-control decision (OD-0038);
  - Q-010 in S1b design;
  - its own owner authorisation.
- It would not approve observations v0.3, or change any standard or the implementation.
