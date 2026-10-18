---
id: OD-0008
title: Owner G1 decisions on the A01 baseline at a82aa0d (items 1–11 and 13–20 approved; item 12 returned)
decision: approve
record_status: recorded
created_at: 2026-10-18
updated_at: 2026-10-18
recorded_by: claude/documentation-agent
owner_statement:
  source: hio/docs/history/2026-10-18-owner-g1-decisions.md (the owner's chat message, verbatim)
  sha256: 111b6fc200c46c70a2f5f20b8120a3c52b1cc54ceb0b2c18ef05ff7ec306a99e
  date: 2026-10-18
  quote: "For G1, I approve the package’s recommended items 1–11 and 13–20 at the pinned a82aa0d revision, subject to recording each decision against its exact file revision. I choose option C1 for the HIO-001 boundary and confirm that the proposed SMSF projection remains fund-level, with no member data. I return item 12, ADR-0010, for revision to separate synthetic-fixture S1a from live-data S1b. G1 remains open until I review and approve that revised ADR. The factor specs remain drafts; the roadmap and implementation plan remain recommendations."
applies_to:
  - path: "(each file in the table below)"
    revision: a82aa0dbddcbf63bb3432a3ddcf5df48300ff2b1
related: {adrs: [HIO-ADR-0001, HIO-ADR-0002, HIO-ADR-0003, HIO-ADR-0004, HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0007, HIO-ADR-0008, HIO-ADR-0009, HIO-ADR-0010], tasks: [T-0001], findings: []}
---

# OD-0008: G1 decisions at `a82aa0d`

Item numbers follow `hio/docs/decisions/G1-decision-package.md` §1. Each decision applies to the
file **as it was at commit `a82aa0d`** (the blob hash below), and to no other content.

| Item | File | Blob at `a82aa0d` | Decision | Notes |
|---|---|---|---|---|
| 1 | `hio/docs/charter.md` | `740d88c5e0980edbf67790ba316e23f0dc5e120d` | approve |  |
| 2 | `hio/docs/architecture.md` | `9e384d1c9de2eb2ce5c25ffd56766366525996a8` | approve |  |
| 3 | `hio/docs/decisions/HIO-ADR-0001-separate-system-modular-monolith.md` | `8a2c015a2422c19e0a1df8442faff8b534e2443d` | approve |  |
| 4 | `hio/docs/decisions/HIO-ADR-0002-systems-of-record-and-smsf-boundary.md` | `d27994cd36634bea2cdd51a264b2e237081c00d0` | approve | the SMSF projection is confirmed fund-level, with no member data |
| 5 | `hio/docs/decisions/HIO-ADR-0003-instrument-identity-boundary.md` | `79b3e40fe1a72677f346a321782c7aedf1523076` | approve | **option C1** chosen |
| 6 | `hio/docs/decisions/HIO-ADR-0004-temporal-semantics.md` | `bd86ec3938c8ffd2b443fab0f1406266144c117f` | approve |  |
| 7 | `hio/docs/decisions/HIO-ADR-0005-rights-model.md` | `2e223877d9b72bb4d40e20d774bb2a0c7a274751` | approve |  |
| 8 | `hio/docs/decisions/HIO-ADR-0006-releases-artefacts-publication.md` | `595e6b4f829c13ad856f786c7ed68da87cc2aca3` | approve |  |
| 9 | `hio/docs/decisions/HIO-ADR-0007-return-accounting-standard.md` | `e97a365995758dd500daddc4732a6d6c8e2c4b9c` | approve |  |
| 10 | `hio/docs/decisions/HIO-ADR-0008-canonical-knowledge-and-harness.md` | `fffb4be305565625b3eed7b66f4f6ad8767aa421` | approve |  |
| 11 | `hio/docs/decisions/HIO-ADR-0009-catalogue-from-manifests.md` | `1ec9ed0e95ff09ce1deb408ad0f7c660327ee796` | approve |  |
| 12 | `hio/docs/decisions/HIO-ADR-0010-first-slice-scope.md` | `fe651aca746db7bda754cffed648eb8fc72478fa` | **returned for revision** | separate synthetic-fixture S1a from live-data S1b; G1 stays open until the revised ADR is approved |
| 13 | `hio/docs/standards/observations-and-point-in-time.md` | `bd9eff0893eaad82793f81c64c22f9153407f7f8` | approve |  |
| 14 | `hio/docs/standards/return-accounting-and-factor-construction.md` | `651c3abe12598ec9b2adacefd786ee14a501a3d4` | approve |  |
| 15 | `hio/docs/standards/datasets-releases-and-artefacts.md` | `8539be643e9d03c2c6f5b2b3abf4d99a0a748ca1` | approve |  |
| 16 | `hio/docs/standards/rights-and-licensing.md` | `1d7296db6670cd36e9acabdec7cc38ff888fc325` | approve |  |
| 17 | `hio/docs/standards/reference-identity.md` | `7796e7b3833171879e6b11cabb4f9e4935a44cce` | approve |  |
| 18 | `hio/docs/standards/factor-specification.md` | `6d380434c3208b35e8ea3f5d07b5da04fe5bdd29` | approve |  |
| 19 | `hio/docs/harness/operating-model.md` | `7172659cf4baf0001704e5207787dbfeb62122b5` | approve |  |
| 20 | `hio/AGENTS.md` | `4000ab1895ee84c2972df997e1076abd94fdabf2` | approve |  |

**Not approved:**
- item 21, the factor specs: they remain drafts;
- item 22, the roadmap and implementation plan: they remain recommendations.

## Post-approval edits

Recording these decisions changes only status metadata in the approved files: `status:` lines,
*Approval* sections, changelog lines, and statements that described the protocol as
provisional. Those edits are listed in the recording commit.

**Content changes are not covered by this approval.** One is directed separately by the owner:
`reviews/reports/` added to operating model §6.2 (OD-0009). Each such change is identified
against the approved blob.

## G1 status

**G1 is open.** It completes when the owner approves the revised HIO-ADR-0010.
