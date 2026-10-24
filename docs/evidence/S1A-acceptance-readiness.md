---
id: HIO-EVIDENCE-S1A-READINESS
title: S1a acceptance readiness (requirement-to-evidence matrix after integration and receipt)
status: prepared_for_owner   # NOT acceptance; the owner decides S1a acceptance in its own record
owner: implementation agent (prepared); owner (decides)
created_at: 2026-10-25
authorised_by: [OD-0037]
evaluated_tree: 084154ccb0fd1c13150d77d02eb525007a5b161e   # src/ and tests/ on main equal this reviewed head
---

# S1a acceptance readiness

> **Prepared for the owner's decision. Not acceptance.** The author's original claims are in the
> [S1a evidence package](S1A-evidence-package.md) (version 1, as reviewed). This document maps
> each requirement to the evidence on integrated `main`, and separates what Codex verified from
> what is still outstanding.

## 1. Five states, kept separate

| State | Meaning | S1a status (2026-10-25) |
|---|---|---|
| Technical verification | Codex's verdict at an exact head | **F1–F7 verified closed** at their reviewed heads (§3) |
| Review receipt | reviewer evidence merged into `main` (§6.2 step 5) | **done**: V1–V11 received (OD-0037) |
| Integration | the implementation merged into `main` | **done**: PR #2 at reviewed head `084154c`, merge `773a557` (tree equal) |
| Standards approval | owner approval of a standard revision | Q-001 r4, Q-002 r5, Q-002-R1 r1 **approved**; observations v0.3 consolidation **pending** |
| Final owner acceptance | an owner record accepting S1a | **not given** |

## 2. Integration and receipt commits

| Step | Commit on `main` |
|---|---|
| Integration of PR #2 (reviewed head `084154c`) | `773a557534280ca7a19ce69a16394343f73e2139` |
| OD-0037 recorded | `a5f9b1d0bc64fa117979a58111c7ea1a10f344c1` |
| V1 receipt (PR #3; index conflict resolved, records unchanged) | `3015c5babc951be6f12c47eaa335ec8150c8a8c3` |
| V2 … V5 receipts | `709225b`, `9663382`, `8515728`, `5be5071` |
| V6 … V11 receipts | `d9d3cc6`, `ba55c69`, `406dc1e`, `f2c335b`, `6ad7326`, `95c2e82a4e72cb74083f3e758573c1b652391a62` |

Every reviewer commit id is kept (each branch tip is an ancestor of `main`). Each record's bytes
equal the SHA-256 first relied on. Nothing outside `reviews/` and the owner-decision trail differs
from `084154c`.

## 3. Findings: independent verification

| Finding | Verified by | At head |
|---|---|---|
| F1, F2, F3, F5 | VERIFY-2026-10-24-s1a-1-1 | `18c80f2` |
| F6 | VERIFY-2026-10-24-s1a-1-5 (rounds 1–4 rejected by -1…-4) | `d9fa276` |
| F4 | VERIFY-2026-10-24-s1a-1-7; held by -8…-11 | `f00db8c` |
| F7 | VERIFY-2026-10-24-s1a-1-11 (rounds 1–5 rejected or gapped by -6…-10) | `084154c` |

V11 also reports the full suite and F1–F6 regressions passing at `084154c`, and the four release
`data.csv` hashes and release ids reproduced independently.

## 4. S1-A1…A15 (implementation plan; S1a stage mapping)

Test counts are from running each group on integrated `main` on 2026-10-25 (all passed). The full
suite is 278 passed; CI at `084154c`: push `40139197232`, PR `40139203000`, attempt 1, success.

| Test | Requirement (short) | Evidence on `main` | Status |
|---|---|---|---|
| S1-A1 | no `macsmsf` import, dependency, credential or network route | `test_independence.py`, `test_harness_guards.py` (4); `tools/check_repo.py imports`; socket block in `tests/conftest.py` | **met for S1a, with a limitation**: no CI egress firewall (Q-008) |
| S1-A2 | import rules enforced; a deliberate violation fails | `test_independence.py::test_deliberate_violations_fail` (1) | met |
| S1-A3 | write-once receipts; hash verified on read; second write refused | `test_objectstore.py` (12); F6 rounds (`test_remediation_s1a_1_f6_round2…5.py`), verified by V5 | met (local filesystem). Bucket versioning is S1b |
| S1-A4 | OBS-INV-001: identical re-fetch no vintage; change makes vintage 2 | `test_observations.py::test_obs_inv_001_*`, `test_objectstore.py::test_duplicate_receipt_is_a_no_op` (2) | met |
| S1-A5 | OBS-INV-002/003 properties; OBS-INV-007 | `test_query_properties.py`, OBS-INV-007 cases A and B, plus the Q-001/Q-002/Q-002-R1 acceptance tests (`test_f4_f7_acceptance.py`, `test_q002_r1_quality_digest.py`) (42); F4/F7 verified by V7/V11 | met |
| S1-A6 | OBS-INV-005: no `valid_time` from a UTC instant (test + lint) | `test_contracts.py::test_obs_inv_005_*`, `test_independence.py::test_repository_passes_the_import_and_valid_time_rules` (2); `check_repo.py valid_time` | met |
| S1-A7 | cash legs, RA §3.2 fixtures, CASH-USD-INV-3 look-ahead trap, period `knowable_at` | `test_constructions.py` usd/aud/weekend/knowable (9); `test_pipeline.py::test_ny_holiday_*` (1) | met |
| S1-A8 | FXC-INV-1/2/4; RA-INV-007 rising and falling `q`; RA-INV-016 | `test_constructions.py` fxc/ra_inv/worked-example/fx_excess (7) | met |
| S1-A9 | decomposition release alongside the excess release | `test_pipeline.py::test_four_releases_including_the_decomposition_companion` (1) | met |
| S1-A10 | triangulation reports | — | **S1b** |
| S1-A11 | clean rebuild reproduces `content_sha256`; releases §6.1 fixtures | `test_pipeline.py` fixtures 1–3 and rebuild; `test_contracts.py::test_manifest_core_refuses_self_reference`; F5 rebuild tests (8); CI clean checkout; V11 independent rebuild | met |
| S1-A12 | fail-closed rights fixtures for every operation | `test_rights.py` (61): six operations × refusing states × permissions; atomic refusals; genuine register byte-identical and still refusing | met (fixtures). Real sources are S1b |
| S1-A13 | soak | — | **S1b** |
| S1-A14 | malformed receipt quarantined; staleness detected | `test_observations.py` malformed/staleness/jump (3+); `test_f7_round4.py` quarantine integrity (12 in group) | met |
| S1-A15 | harness CI checks pass; handoff written | `check_repo.py` PASS; `test_review_gate.py` (28); CI green; handoffs for every round | met |
| **S1-A16** | §10 fresh-agent test, reproducing a release hash | — | **not run** (owner action, §6) |

ADR-0010 rev 3's own S1a list (it governs if the two differ) maps onto the same evidence, as the
evidence package's table shows, plus "Codex review at an assigned head": **met** (V11 READY at
`084154c`, received).

## 5. Open decisions: recommendations

| Question | Gated by the register as | Recommendation | Blocks S1a acceptance? |
|---|---|---|---|
| **Q-007** ratify `pyyaml` (runtime) and `hatchling` (build backend) | S1a acceptance | **Ratify.** `pyyaml` is required to read the YAML specs and registers the approved factor-specification standard defines; `hatchling` is build-only. Both are locked in `uv.lock` | **yes**, as registered; a one-line decision |
| **Q-008** accept the S1a network control level (no CI egress firewall) | S1a acceptance | **Accept for S1a only.** S1a is synthetic: `src/` may import no network client, tests refuse every non-loopback socket, CI holds no secrets. Require an egress control decision as part of the S1b authorisation, when real fetches begin | **yes**, as registered |
| **Q-005a** does exploratory internal use need an owner event? | S1a consumer API semantics | **Confirm current behaviour:** the job marks releases `exploratory` with no owner event; publishing to `hio_internal` needs the owner's `approved_for_consumer` event. S1a has no consumer beyond HIO | **not strictly**: no S1a test depends on it, but confirming it at acceptance avoids carrying ambiguity into S1b |
| **Archive receipt on the capture clock** (response 6): one archive receipt carrying a key's revision history makes a same-instant conflict, so `as_captured_by_hio` suppresses the key | not registered | **Defer to S1b design** and register it as an open question there. It affects no S1a fixture or release, it fails closed, and it arises only with real vintage archives | **no** |

## 6. Observations v0.3: the exact revision for separate approval

`docs/standards/drafts/observations-and-point-in-time-v0.3-candidate.md`, committed at `dc0ac10`,
blob **`61ddd58ed49af9fed395eaa17e61dfc7fb451fe6`** (unchanged on `main`). It consolidates the
approved v0.2 with Q-001 r4 (`419992f2`), Q-002 r5 (`d0a25b3b`) and Q-002-R1 r1 (`cb7a937d`),
editorially. The approved amendments already govern S1a, so v0.3 approval is a consolidation step,
**not** an S1a acceptance prerequisite.

## 7. The §10 fresh-session test (S1-A16): instructions for the owner

1. **Fix the revision.** Use `main` at the commit that adds this file (`git log -n1 --format=%H --
   docs/evidence/S1A-acceptance-readiness.md`), or a later one you name. Record it as X.
2. **Two genuinely fresh sessions**, no prior chat history, repository access at X only, no
   summary or coaching:
   - a **Claude** session with the §10 Claude prompt (six questions), plus the slice add-on:
     reproduce a named release hash (for example, run the `hio.jobs.s1a` command from the evidence
     package twice into empty stores and compare the four release ids);
   - a **Codex** session with the §10 Codex prompt (seven questions), in the *before assignment*
     state: Q2 must be "No review target has been assigned."
3. **Grade** against §10's pass criteria: no false approval or authorisation claim (S1a is
   **not** accepted; S1b is **not** authorised), no missed open finding (S1a findings are all
   verified closed; Q-003…Q-008 remain open), the correct next action, a path and commit for every
   answer, no reliance on chat memory.
4. **Record** the result in `reviews/records/` as a harness review. A failure yields the smallest
   instruction fix in the harness changelog. A Claude sub-agent standing in for Codex is an
   "unverified dry run" and does not satisfy the test.

## 8. Remaining for acceptance

- **Owner decisions:** Q-007; Q-008; (recommended) Q-005a; the S1a acceptance record itself.
- **Unmet acceptance test:** S1-A16 (§10), run and graded by the owner.
- **Not required for S1a:** observations v0.3 approval; the archive question (S1b); S1-A10, A13
  and the real-source parts of A3/A12 (S1b).
