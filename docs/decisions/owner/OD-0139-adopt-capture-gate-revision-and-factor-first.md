---
id: OD-0139
title: "Owner adopts Authorisation B revision 1 (B-3 no longer waits for a C5 decision) and the factor-first sequence as the working order, both at ecd6b81"
decision: approve
record_status: recorded
created_at: 2026-11-03
updated_at: 2026-11-03
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-03-owner-adopt-capture-gate-factor-first.md (owner's message, verbatim, with Claude's decisions put)
  sha256: 0fd2006a0d6df0a563fd6e91d5b6f14fe8c50a36d88a998971d73b2317e5083d
  date: 2026-11-03
  quote: "yes to both"
approves:
  - path: docs/evidence/S1B1-authorisation-B-revision-1.md
    revision: "ecd6b817ce0d3fb349dee6ed6b9fa1677d419752, blob c7db575b9788756eb5849f5252944fa10e617261"
  - path: docs/decisions/factor-first-sequencing-proposal.md
    revision: "ecd6b817ce0d3fb349dee6ed6b9fa1677d419752, blob 21d7e17ffb9881d1d4b1d45a12428d176c971c74"
base_revision: 58fe532650c2c14c216eb0f06ab8de3f7533f541
related: {adrs: [HIO-ADR-0012], tasks: [T-0015], findings: [], ods: [OD-0063, OD-0119, OD-0132, OD-0136, OD-0138]}
---

# OD-0139: capture gate revised; factor-first order adopted

1. **Authorisation B revision 1 is adopted.** B-3 no longer waits for a C5 decision. Capture may start as exploratory, `schedule_only` (P3)
   capture under the staging stated in that document. C5 stays unresolved and on record. Finality stays owed before any final claim,
   S1b-1 stage completion or G2. **This changes the gate only.** The Authorisation B package is read as amended by it.
2. **The factor-first sequence is the working order.** G2, finality and S1 obligations are unchanged. **It sets priorities only:** each
   track keeps its own authorisation.

PR #60 is merged with the head match enforced. The only edit after the merge is each document's status wording.

**Choices in revision 1 still open to the owner:** whether R-1 and 7b run before go-live or 7b is deferred; whether the storage-error limit
is accepted for the soak or fixed first.

**Documents not changed by this record.** `docs/base-camp.md` (itself still proposed and unadopted), `docs/roadmap.md` and
`docs/implementation-plan.md` are not edited. The proposal lists the changes they would take; they follow if and when the owner adopts or
amends those documents. `docs/architecture.md` (approved) and HIO-ADR-0012 are unchanged.

## Not authorised

B-3 go-live, any capture or `LIVE_AUTHORISATION`; the re-run, 7b or the destroy; any C5 amendment; any rights verification; any download,
vendor contact or purchase; the duration experiment; the analytical reader or a stack change; adopting base camp; any waiver.

## Corrections (append-only)

### Correction 1 (2026-11-03): merged

OD-0139 merged as `b40e139`; PR #60 merged as `cf312ed`, with the head match enforced and both blobs on `main` equal to those
above. This commit changes each document's status wording only, and STATUS.
