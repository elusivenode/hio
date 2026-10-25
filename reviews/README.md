---
id: HIO-REVIEWS
title: Review index (assignments, records, findings, remediation claims, verification, waivers)
status: current
owner: independent reviewer (findings and verification); owner (assignments and waivers)
last_reviewed: 2026-10-18
---

# HIO review index

A **navigation summary**: what is assigned, what has been reviewed at which revision, and what
remains open. **The individual records are the source of truth.** If this index disagrees with a
record, the record wins. Rules: [operating model §3, §6.1 and
§6.2](../docs/harness/operating-model.md#62-review-branch-and-worktree-protocol).

**Who writes what:**
- **The owner:** assignments (an *Assigned reviews* row, an owner PR comment, or a direct
  instruction later indexed here; exact SHAs and the review branch); runs or reviews the scope
  check; merges reviewer PRs (receipt only); acceptance, approval and waivers (by OD id).
- **The reviewer (Codex):** review records and verification records (`records/`), its
  handoffs (`handoffs/`), opinion or readiness reports (`reports/`), and its own index rows. Written on its review branch, in its own
  worktree, never on the staging branch.
- **The author (Claude):** remediation responses (`responses/`) and the *Remediation claim*
  cell. Never a verdict, a verification or a closure.

Commits carry `HIO-Actor` role trailers as **self-declared metadata, not proof**. Reviewer
actions are evidenced by the reviewer's own output on a scope-checked review branch (§6.1–6.2).

## Assigned reviews (owner-assigned; harness-0.7: one of three owner-authored sources, see operating model §6.2 step 1)

| Review | Repository | Base SHA | Head SHA | Task / scope | Assigned by (OD / source) | Status |
|---|---|---|---|---|---|---|
| REVIEW-2026-10-18-t0004 | `macsmsf`, branch `docs/hio-001-boundary-c1` | `1502ab8804c5968a8bf91fa36275c44e6e84f575` (`main`) | `fe3fdc78cb2d2b9f147122528cc5cf97db976397` | T-0004: the documentation-only ADR 0003 C1 boundary amendment and the HIO-001 review-record pointer. Check it is consistent with HIO-ADR-0003 (approved, OD-0008) and changes no code, schema or activation prerequisite. Review branch `review/t0004-codex`, cut from the staging commit that adds OD-0010; the target is inspected read-only (cross-lineage mechanics in OD-0010) | [OD-0010](../docs/decisions/owner/OD-0010-g1-followup-instructions.md) (owner instruction, transcribed); cross-lineage mechanics **confirmed** by [OD-0018](../docs/decisions/owner/OD-0018-t0004-mechanics-parallel-work.md). The repository and SHAs are `macsmsf`'s; the review branch is in `macsmsf` | **received** from `macsmsf@db305a3cbfe0b149b25d0cde30a3bb890e70dc39` by byte-identical cross-lineage copy ([OD-0040](../docs/decisions/owner/OD-0040-t0004-cross-lineage-receipt.md); exception to §6.2 step 5); verdict READY; **not** T-0004 acceptance or a `macsmsf` merge |
| REVIEW-2026-10-24-s1a-1 | `elusivenode/hio` | `9370256bac6ba2193b09c342170bd11ca57b70a3` | `98e6a8e08fca8b28241d9e4e7c04c181d75f1eef` | T-0005 S1a synthetic-fixture implementation (HIO-ADR-0010 rev 3, OD-0017, OD-0020). Review branch `review/s1a-1-codex` | owner direct assignment in Codex chat, 2026-10-24; indexed at receipt and the five values confirmed by the owner ([OD-0022](../docs/decisions/owner/OD-0022-receive-s1a-review.md)) | **received** at `e55cc89` (PR #1); verdict REQUEST CHANGES; findings open |
| REVIEW-2026-10-25-adr0012 | `elusivenode/hio` | `183523fd6e2cc148abfe2619426bfc38c7cf2108` | `1d68da3e90d879da6318082551bab943c60cf68b` | HIO-ADR-0012 staged S1b design; seven bounded questions; review branch `review/adr0012-codex` | owner direct instruction to Codex, 2026-10-25 (image supplied in the review conversation); OD-0048 authorisation | **submitted for receipt**; verdict REQUEST CHANGES; three findings open |

## Candidate review targets (NOT assigned; a reviewer must not treat these as its target)

| Candidate | Repository | Base SHA | Head SHA | Proposed scope | Proposed by |
|---|---|---|---|---|---|
| A01 independent review | `macsmsf`, branch `docs/hio-a01-baseline` | `1502ab8` (`macsmsf` main) | **the commit that adds the latest `hio/handoffs/*t0006-final-correction*` handoff**, resolved as `git log -n1 --format=%H -- <that file>`; the SHA is stated in the owner-facing completion report | ADRs 0001–0010; the standards (especially return accounting v0.1); the S1 draft specs; harness-0.3 (T-0006); the four `macsmsf` pointer edits in `85ef0fa` | Claude (candidate only) |
| S1a implementation review (**assigned directly; see Assigned reviews**) | `elusivenode/hio` | `9370256bac6ba2193b09c342170bd11ca57b70a3` (the revision OD-0020 reviewed) | **the commit that adds `docs/evidence/S1A-evidence-package.md`**, resolved as `git log -n1 --format=%H -- docs/evidence/S1A-evidence-package.md` | S1a under HIO-ADR-0010 rev 3 and OD-0017/OD-0020: the acceptance list, the RA §3.2 and FX fixtures, OBS-INV-001…007, the rights gate, releases §6.1, the safeguards, and the ten interpretations listed in the evidence package | Claude (candidate only) |
| HIO-ADR-0012 (staged S1b) proposal review, `REVIEW-2026-10-25-adr0012`, review branch `review/adr0012-codex` | `elusivenode/hio`, branch `docs/adr0012-staged-s1b-proposal` | `183523fd6e2cc148abfe2619426bfc38c7cf2108` (`main`) | **the PR's Submission-Head** (the commit that last touches `docs/decisions/HIO-ADR-0012-staged-s1b.md`, resolved as `git log -n1 --format=%H -- docs/decisions/HIO-ADR-0012-staged-s1b.md`); the SHA is stated in the PR description and the owner-facing completion report | the seven questions in [`HIO-ADR-0012-review-assignment-draft.md`](../docs/decisions/HIO-ADR-0012-review-assignment-draft.md), with question 5 covering publication and revision timestamp semantics: supersession accuracy, no obligation deleted, gates not weakened, return mathematics, observation and evidence integrity, rights, boundary | Claude (candidate only; OD-0047, OD-0048). The owner authorised the review in OD-0048, conditional on confirmation from Git; the binding values are in the owner's assignment (PR comment or direct instruction) |

Historical candidate: the owner subsequently assigned the A01 review directly at the fixed
head `35c9821`. The completed review is indexed below; this candidate is not a pending task.

## Reviewed revisions and review records

| Review | Subject | Base..head | Reviewer | Verdict | Record |
|---|---|---|---|---|---|
| REVIEW-2026-10-18-a01 | A01 architecture, mathematics, S1 specs and harness-0.3 | `1502ab8..35c9821` | Codex, on the owner's direct 2026-10-18 request | **REQUEST CHANGES** | [record](records/REVIEW-2026-10-18-a01.md) |
| REVIEW-2026-10-18-t0007-pilot | T-0007 review-worktree protocol and harness-0.5 corrections | `46ea6a5..b48f83c` | Codex, on the owner's direct 2026-10-18 assignment | **READY** | [record](records/REVIEW-2026-10-18-t0007-pilot.md) |
| REVIEW-2026-10-18-t0004 | T-0004 SMSF documentation amendment for HIO-001 boundary option C1 | `1502ab8..fe3fdc7` | Codex, under OD-0010 and OD-0018 | **READY** | [record](records/REVIEW-2026-10-18-t0004.md) |
| REVIEW-2026-10-24-s1a-1 | T-0005 S1a synthetic-fixture implementation | `9370256..98e6a8e` | Codex, on the owner's direct 2026-10-24 assignment | **REQUEST CHANGES** | [record](records/REVIEW-2026-10-24-s1a-1.md) |
| REVIEW-2026-10-25-adr0012 | HIO-ADR-0012 staged S1b design | `183523f..1d68da3` | Codex, on the owner's direct 2026-10-25 assignment | **REQUEST CHANGES** | [record](records/REVIEW-2026-10-25-adr0012.md) |
| HARNESS-2026-10-25-s1a16-1 | operating model §10 cold-start test, run 1 (S1-A16): fresh Claude and Codex sessions | at `3fd129e` | owner-run sessions; owner-graded (preliminary, OD-0039) | **pending**: Claude pass subject to evidence; Codex baseline ambiguous (T-0004 assignment outstanding); evidence paths: see [OD-0043](../docs/decisions/owner/OD-0043-relocate-s1a16-evidence.md) (now under `~/Documents/hio-evidence/`). | [record](records/HARNESS-2026-10-25-s1a16-1.md) |
| HARNESS-2026-10-25-s1a16-2 | operating model §10 cold-start test, run 2 (Codex-only retest) and the combined S1-A16 result | at `df3af48` (Codex); with run 1 at `3fd129e` (Claude) | owner-run fresh session; owner-graded (OD-0041) | **satisfied**: S1-A16 PASS on the two-revision basis (OD-0040); evidence paths: see [OD-0043](../docs/decisions/owner/OD-0043-relocate-s1a16-evidence.md) (now under `~/Documents/hio-evidence/`). | [record](records/HARNESS-2026-10-25-s1a16-2.md) |

Reviewer build-check addendum for `REVIEW-2026-10-24-s1a-1`:
[locked offline sync and repeated tests](reports/2026-10-24-s1a-1-build-addendum.md).

## Verification rounds

| Verification | Original review | Base..submission head | Fix commit | Reviewer outcome | Record |
|---|---|---|---|---|---|
| VERIFY-2026-10-18-a01-1 | REVIEW-2026-10-18-a01, findings 1–8 | `35c9821..0c74686` | `0e3de4b` | **Eight verified_closed** | [record](records/VERIFY-2026-10-18-a01-1.md) |
| VERIFY-2026-10-24-s1a-1-1 | REVIEW-2026-10-24-s1a-1, findings 1, 2, 3, 5, 6 | `98e6a8e..18c80f2` | `39d37da`, `6bbf562`, `3185443`, `7076452`, `1c117e6` | **Four verified_closed; F6 remediation_rejected; REQUEST CHANGES** | [record](records/VERIFY-2026-10-24-s1a-1-1.md) |
| VERIFY-2026-10-24-s1a-1-2 | REVIEW-2026-10-24-s1a-1, finding(s) 6 | `18c80f2..759ddf7` | `45dd538` | F6 remediation_rejected; REQUEST CHANGES | [record](records/VERIFY-2026-10-24-s1a-1-2.md) |
| VERIFY-2026-10-24-s1a-1-3 | REVIEW-2026-10-24-s1a-1, finding(s) 6 | `759ddf7..21c8167` | `c964461` | F6 remediation_rejected; REQUEST CHANGES | [record](records/VERIFY-2026-10-24-s1a-1-3.md) |
| VERIFY-2026-10-24-s1a-1-4 | REVIEW-2026-10-24-s1a-1, finding(s) 6 | `21c8167..4c1b565` | `5fbbd09` | F6 remediation_rejected; REQUEST CHANGES | [record](records/VERIFY-2026-10-24-s1a-1-4.md) |
| VERIFY-2026-10-24-s1a-1-5 | REVIEW-2026-10-24-s1a-1, finding(s) 6 | `4c1b565..d9fa276` | `7cf2c01` | **F6 verified_closed**; READY | [record](records/VERIFY-2026-10-24-s1a-1-5.md) |
| VERIFY-2026-10-24-s1a-1-6 | REVIEW-2026-10-24-s1a-1, finding(s) 4, 7 | `b4c398d..191ac0f` | `e3efc9f`, `eb7e92c`, `92cef1c`, `f6187f3` | F4 and F7 remediation rejected; REQUEST CHANGES | [record](records/VERIFY-2026-10-24-s1a-1-6.md) |
| VERIFY-2026-10-24-s1a-1-7 | REVIEW-2026-10-24-s1a-1, finding(s) 4, 7 | `191ac0f..f00db8c` | `36e5f13`, `c3be820` | **F4 verified**; F7 rejected; REQUEST CHANGES | [record](records/VERIFY-2026-10-24-s1a-1-7.md) |
| VERIFY-2026-10-24-s1a-1-8 | REVIEW-2026-10-24-s1a-1, finding(s) 4, 7 | `f00db8c..6720a6c` | `6ac9ef7` | F4 verification held; F7 rejected; REQUEST CHANGES | [record](records/VERIFY-2026-10-24-s1a-1-8.md) |
| VERIFY-2026-10-24-s1a-1-9 | REVIEW-2026-10-24-s1a-1, finding(s) 4, 7 | `6720a6c..0e900e8` | `7b267f5` | F4 held; F7 contract gap (Q-002-R1); REQUEST CHANGES | [record](records/VERIFY-2026-10-24-s1a-1-9.md) |
| VERIFY-2026-10-24-s1a-1-10 | REVIEW-2026-10-24-s1a-1, finding(s) 7 | `0e900e8..21e4a07` | `3016796` | F4 held; F7 rejected; REQUEST CHANGES | [record](records/VERIFY-2026-10-24-s1a-1-10.md) |
| VERIFY-2026-10-24-s1a-1-11 | REVIEW-2026-10-24-s1a-1, finding(s) 7 | `21e4a07..084154c` | `6b0c0b3` | **F7 verified_closed**; F4 held; READY | [record](records/VERIFY-2026-10-24-s1a-1-11.md) |

All S1a verification records V1–V11 were **received into `main`** on 2026-10-25 under OD-0037,
after PR #2 was integrated at the reviewed head `084154c` (merge `773a557`). Receipt is not
acceptance of S1a.

The owner assigned the A01 review directly in the Codex session. The *Assigned reviews* table
above was not updated beforehand; it is not evidence that the candidate row authorised the
review. The reviewed base/head and assignment source are in that record. The review record does
not accept or approve the A01 baseline.

The owner also assigned T0007-PILOT directly in the Codex session at the fixed base/head in its
record. Its READY opinion is not acceptance of T-0007 or approval of HIO-ADR-0008.

**Other reviewer inputs (not reviews; no findings opened):**
- A **Codex focused analysis** (`hio-harness-refinement-codex-analysis-for-chatgpt-2026-10-18.md`,
  of `23ad27f`) is cited by the owner's directive (OD-0002). It was not supplied to Claude and
  is not in the repository.
- The directive describes it as "not the independent A01 architecture, financial mathematics,
  or implementation review", granting no approval.
- If the owner wants it on record, commit it verbatim under `docs/history/`.

## Findings register

| Finding | From review | Severity | State | Remediation claim (author) | Verification (reviewer) | Waiver (owner OD) |
|---|---|---|---|---|---|---|
| F-REVIEW-2026-10-18-a01-1 | REVIEW-2026-10-18-a01 | critical | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-2 | REVIEW-2026-10-18-a01 | high | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-3 | REVIEW-2026-10-18-a01 | high | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-4 | REVIEW-2026-10-18-a01 | high | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-5 | REVIEW-2026-10-18-a01 | high | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-6 | REVIEW-2026-10-18-a01 | high | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-7 | REVIEW-2026-10-18-a01 | medium | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-18-a01-8 | REVIEW-2026-10-18-a01 | medium | **verified_closed** | remediation_claimed: fix `0e3de4b`; [response](responses/RESPONSE-REVIEW-2026-10-18-a01-1.md) | [VERIFY-2026-10-18-a01-1](records/VERIFY-2026-10-18-a01-1.md) | — |
| F-REVIEW-2026-10-24-s1a-1-1 | REVIEW-2026-10-24-s1a-1 | high | **verified_closed** | remediation_claimed: fix `39d37da`; [response](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md) | [VERIFY-2026-10-24-s1a-1-1](records/VERIFY-2026-10-24-s1a-1-1.md) at `18c80f2` | — |
| F-REVIEW-2026-10-24-s1a-1-2 | REVIEW-2026-10-24-s1a-1 | high | **verified_closed** | remediation_claimed: fix `6bbf562`; [response](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md) | [VERIFY-2026-10-24-s1a-1-1](records/VERIFY-2026-10-24-s1a-1-1.md) at `18c80f2` | — |
| F-REVIEW-2026-10-24-s1a-1-3 | REVIEW-2026-10-24-s1a-1 | high | **verified_closed** | remediation_claimed: fix `3185443`; [response](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md) | [VERIFY-2026-10-24-s1a-1-1](records/VERIFY-2026-10-24-s1a-1-1.md) at `18c80f2` | — |
| F-REVIEW-2026-10-24-s1a-1-4 | REVIEW-2026-10-24-s1a-1 | high | **verified_closed** | remediation_claimed (round 2): fixes `36e5f13`, `c3be820` (tests `b3aa3c7`); [response 7](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-7.md); round 1 (`e3efc9f`, `eb7e92c`; [response 6](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-6.md)) rejected by VERIFY-2026-10-24-s1a-1-6 at `3cb3dd0` (exception OD-0031; since received, OD-0037); Q-001 decided by OD-0029 (OBS-AMEND-Q001 revision 4) | [VERIFY-2026-10-24-s1a-1-7](records/VERIFY-2026-10-24-s1a-1-7.md) at `f00db8c`; held by -8…-11 | — |
| F-REVIEW-2026-10-24-s1a-1-5 | REVIEW-2026-10-24-s1a-1 | medium | **verified_closed** | remediation_claimed: fix `7076452`; [response](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md) | [VERIFY-2026-10-24-s1a-1-1](records/VERIFY-2026-10-24-s1a-1-1.md) at `18c80f2` | — |
| F-REVIEW-2026-10-24-s1a-1-6 | REVIEW-2026-10-24-s1a-1 | medium | **verified_closed** | remediation_claimed (round 5): fix `7cf2c01`; [response 5](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-5.md) (OD-0025). Earlier rounds rejected, records preserved and owner-disposed, since received (OD-0037): round 4 (fix `5fbbd09`, [response 4](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-4.md)) by VERIFY-2026-10-24-s1a-1-4 at `873fc69`; round 3 (fix `c964461`, [response 3](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-3.md)) by VERIFY-2026-10-24-s1a-1-3 at `ff0dd81`; round 1 (fix `1c117e6`, [response 1](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md)) by VERIFY-2026-10-24-s1a-1-1 at `0255cb2`; round 2 (fix `45dd538`, [response 2](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-2.md)) by VERIFY-2026-10-24-s1a-1-2 at `9a94c3a` | [VERIFY-2026-10-24-s1a-1-5](records/VERIFY-2026-10-24-s1a-1-5.md) at `d9fa276` | — |
| F-REVIEW-2026-10-24-s1a-1-7 | REVIEW-2026-10-24-s1a-1 | medium | **verified_closed** | remediation_claimed (round 6): fix `6b0c0b3` (tests `b996e48`); [response 11](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-11.md); round 5 (Q-002-R1 `quality_digest`, `3016796`; [response 10](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-10.md)) rejected by VERIFY-2026-10-24-s1a-1-10 at `586b35e` (exception OD-0036; since received, OD-0037); round 4 (`7b267f5`; [response 9](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-9.md)) found the contract gap in VERIFY-2026-10-24-s1a-1-9 at `63df7ff` (exception OD-0035; since received, OD-0037); round 3 (`6ac9ef7`; [response 8](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-8.md)) rejected by VERIFY-2026-10-24-s1a-1-8 at `db1722c` (exception OD-0033; since received, OD-0037); round 2 (`36e5f13`, `c3be820`; [response 7](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-7.md)) rejected by VERIFY-2026-10-24-s1a-1-7 at `35526b5` (exception OD-0032; since received, OD-0037); round 1 (`e3efc9f`, `eb7e92c`; [response 6](responses/RESPONSE-REVIEW-2026-10-24-s1a-1-6.md)) rejected by VERIFY-2026-10-24-s1a-1-6 at `3cb3dd0` (OD-0031); Q-002 decided by OD-0030 (OBS-AMEND-Q002 revision 5, Option A′) | [VERIFY-2026-10-24-s1a-1-11](records/VERIFY-2026-10-24-s1a-1-11.md) at `084154c` | — |

| F-REVIEW-2026-10-25-adr0012-1 | REVIEW-2026-10-25-adr0012 | high | **open**: approximate or deferred publication can make P earlier than this vintage's actual publication | — | — |
| F-REVIEW-2026-10-25-adr0012-2 | REVIEW-2026-10-25-adr0012 | high | **open**: a cutoff after W can label the morning vintage final before the post-window receipt | — | — |
| F-REVIEW-2026-10-25-adr0012-3 | REVIEW-2026-10-25-adr0012 | medium | **open**: the SOFR Index can be revised for an Index calculation error without a SOFR rate revision | — | — |

States: `open`, `remediation_claimed` (still open), `verified_closed`, `waived`. A waiver
preserves the finding. It is not a verification.
