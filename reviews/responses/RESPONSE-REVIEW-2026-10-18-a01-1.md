---
id: RESPONSE-REVIEW-2026-10-18-a01-1
author: claude/documentation-agent
findings: [F-REVIEW-2026-10-18-a01-1, F-REVIEW-2026-10-18-a01-2, F-REVIEW-2026-10-18-a01-3, F-REVIEW-2026-10-18-a01-4, F-REVIEW-2026-10-18-a01-5, F-REVIEW-2026-10-18-a01-6, F-REVIEW-2026-10-18-a01-7, F-REVIEW-2026-10-18-a01-8]
reviewed_head: 35c9821f805955914b05991c1c075b8cb3e082b5
fix_commits: [0e3de4b76398799692cd09f3982c12986e195e7b]
submission_head: self    # resolve with: git log -n1 --format=%H -- hio/reviews/responses/RESPONSE-REVIEW-2026-10-18-a01-1.md
task: T-0008 (authorised by OD-0005)
created_at: 2026-10-18
---

# Remediation response: REVIEW-2026-10-18-a01, findings 1–8

> Written by the author on the staging branch. **This is a claim, not a verification.** Every
> finding stays `open` until a Codex verification record closes it. Verification should be
> assigned at the **submission head** (the commit that adds this file), so the fix and this
> evidence are seen at one revision.

All fixture arithmetic below was computed with Python `decimal` at 30-digit precision, and is
quoted to 12 decimal places.

| Finding | Fix commit | What changed (files) | Evidence (fixtures, checks) | Residual risk or disagreement |
|---|---|---|---|---|
| **-1** Critical: a backfilled revision masquerades as knowable | `0e3de4b` | `docs/standards/observations-and-point-in-time.md` v0.2 §3, §4, §4.1, §7; `docs/decisions/HIO-ADR-0004-*` (text only); `registers/hypotheses.yaml` basis names; plan S1-A5 | Knowability is now a property of a vintage. `schedule_only` and `rule_inferred` cannot satisfy `as_known_by_market`, which returns **absent** instead. New `reconstructed(T)` mode, always labelled. §4.1 fixture (original 100, revision 110, current-only backfill 110): Case A gives `as_known_by_market(2021-01-01)` absent and `reconstructed` 110; Case B, with publisher vintages, gives 100 at 2021-01-01 and 110 at 2025-07-01. OBS-INV-003 is strengthened; OBS-INV-007 added | `archived_receipt` evidence quality (archive integrity, dating) is defined only in outline. The first source to use it needs a concrete rule |
| **-2** High: the USD cash rule conflicts with its fixing convention | `0e3de4b` | `docs/standards/return-accounting-and-factor-construction.md` v0.2 §3.2, §9; `specs/factors/cash.usd.overnight.yaml` v0.2.0; `cash.aud.overnight.yaml` v0.2.0; `fx.usd_cash_vs_aud.excess.yaml` v0.2.0; plan S1-A7 | The rate is selected by **applicability**: the overnight starting on the latest business day `b ≤ d`, in window `t−1 ≤ d < t`. Selection never uses knowability. Ex-ante and in-arrears regimes are distinguished; SOFR is in arrears, labelled `replicable_with_basis`. Period `knowable_at` = the publication of the last rate used. **Fri→Mon:** NY Fri, Sat, Sun at Fri SOFR; **Monday's SOFR is not used** (CASH-USD-INV-3). FX weekend fixture (FXC-INV-4): `s = 0.005`, `R = 0.005360125000`, `X = 0.005064234589` = spot + carry `0.000062442922` + cross `0.000001791667` | The NY-date-to-Sydney-window alignment is a declared approximation (about a half-day offset). AUD regime (ex-ante or in arrears) awaits T-0002 publication timing |
| **-3** High: release identity versus status | `0e3de4b` | `docs/standards/datasets-releases-and-artefacts.md` v0.2 §1–§7, §6.1; `docs/decisions/HIO-ADR-0006-*` (text only); ADR-0002 term rename; plan S1-A11 | The hash domain is the canonical manifest core (or the artefact envelope). `created_at`, run ids and status are excluded and stored separately. Status is append-only events with sequential `seq`; `withdrawn` is terminal. Consumers resolve the effective status and current rights at use. §6.1 fixtures: determinism; status events do not change identity; withdrawal refused by a pinned consumer while its bytes verify; self-reference impossible | The canonical Parquet-versus-CSV hashing choice is still deferred to S1, as before; it is now inside a defined hash domain |
| **-4** High: CMT drops a coupon | `0e3de4b` | RA v0.2 §6 step 3; RA-INV-013 | `R_t = (P^{dirty}_t + C_{(t−1,t]})/P^{dirty}_{t−1} − 1`; coupon cash is held to the period end, then reinvested at the re-strike. Coupon date `102 → 100 + 2` gives **0** (omitting the coupon would give `−0.019607843137`); non-coupon date `101.00 → 101.05` gives **0.000495049505** | S3 work; interest on intra-period coupon cash is ignored by convention, which is immaterial for daily re-strikes |
| **-5** High: rights gates miss operations | `0e3de4b` | `docs/standards/rights-and-licensing.md` v0.2 §1, §3, §5; `docs/decisions/HIO-ADR-0005-*` (text only); `registers/sources.yaml` (`automated_retrieval`); spec `rights_required`; plan S1-A12 and dependency 4; T-0002 R5 | New `automated_retrieval` permission. An operation-to-permission matrix covers fetch, store raw, build, store derived, rebuild, publish, agent, terminate and audit, with `external_processing` where CI or cloud is involved. Fail closed: unknown, deny, an unsatisfied conditional or unverified evidence all refuse. S1 requires one fail-closed fixture per operation it performs. T-0002 must verify before **any** live operation | Enforcement for agents remains procedural until a licensed source arrives (unchanged; already declared) |
| **-6** High: bill rates called returns | `0e3de4b` | both cash specs v0.2.0 `triangulation`; plan inputs table and S1-A10 | Restated as **rate** triangulations (`state_indicator`), not return agreement: (1) contemporaneous levels after the declared conversion (T-bill money-market yield `y = d/(1 − d·n/360)`; `d = 4.20%`, `n = 91` gives `4.2450684770%`); (2) horizon-aligned: the bill yield at `t` against realised compounded overnight over `[t, t+n)`. Expected differences pre-registered | A bill total-return factor is not built. If wanted later, it is its own spec |
| **-7** Medium: false compounding bound | `0e3de4b` | RA v0.2 §3.2 (exact convention); `cash.usd.overnight.yaml` CASH-USD-INV-2 replaced | The bound is removed. Exact `Π(1 + rate_b n_b / 360) − 1` (in-arrears convention, simple within weekends). Fixtures: 3-day `0.000358333333`; 4-day holiday `0.000477777778`; Thu→Mon `0.000486154907`. Daily compounding within a weekend (`0.000358376136`, a gap of `4.280263e-8`) is documented as a different, unused convention | The convention follows the standard ARRC/ISDA-style in-arrears approach [EXT]; confirm against the NY Fed methodology in T-0002 |
| **-8** Medium: forward and cash denominators | `0e3de4b` | RA v0.2 §4.2; RA-INV-021; FX spec forward-triangulation `normalisation` | Both constructions use the same capital `K`. Under CIP, both equal `(1 + r^h)(S_T/F − 1)`; `S_T/F − 1` is per unit of forward notional. Fixture (a): `S_0 = S_T = 1`, `r^h = 10%`, `r^f = 0`: cash −10%, `S_T/F − 1` = −9.090909%, normalised −10%. Fixture (b): `F = 1.5375427458`: cash `−0.024489615842` = normalised; `S_T/F − 1` = `−0.024417367194` | None identified |

## Not changed

- The review record, finding text and finding states.
- Any ADR `status:` (all still `proposed`).
- T-0006.
- HIO-001.
- `macsmsf`.

## Request

The owner assigns a Codex verification at this file's submission head, with base `35c9821`
(the reviewed head) or `e99fae1` (T-0008's base), as the owner prefers, under operating model
§6.2.
