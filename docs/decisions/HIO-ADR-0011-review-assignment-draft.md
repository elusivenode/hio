---
id: HIO-ADR-0011-REVIEW-ASSIGNMENT-DRAFT
title: "Draft Codex review assignment for HIO-ADR-0011 (staged S1b), for the owner to issue or amend"
status: draft   # NOT an assignment. Only an owner-authored source assigns a review (operating model §6.2 step 1)
owner: owner (assigns); drafted by claude/implementation-agent
created_at: 2026-10-25
drafted_under: OD-0047
---

# Draft review assignment: HIO-ADR-0011

> **Not an assignment.** A reviewer must not treat this file as its target. It is the text the
> owner may adopt, in one owner-authored source: an *Assigned reviews* row, an owner PR comment,
> or a direct instruction (operating model §6.2 step 1). Its exact head is resolved below, not
> written here, because a file cannot contain its own commit id.

## Proposed assignment values

| Field | Proposed value |
|---|---|
| Review id | `REVIEW-2026-10-25-adr0011` |
| Repository | `elusivenode/hio` |
| Base SHA | `183523fd6e2cc148abfe2619426bfc38c7cf2108` (`main`, pushed) |
| Head SHA | the commit that adds this file and `docs/decisions/HIO-ADR-0011-staged-s1b.md`, resolved with `git log -n1 --format=%H -- docs/decisions/HIO-ADR-0011-staged-s1b.md`, on branch `docs/adr0011-staged-s1b-proposal`. The full SHA is given in the owner-facing completion report |
| Review branch | `review/adr0011-codex`, cut at the head |
| Reviewer | Codex, independent reviewer (declared role) |
| Writes allowed | `.md` files under `reviews/` only (operating model §6.2 step 3) |

## Scope (bounded)

**In scope (read-only):**
- `docs/decisions/HIO-ADR-0011-staged-s1b.md`, the subject;
- `docs/research/T-0002-owner-verification-matrix.md`, and the 2026-10-25 evidence note,
  including its append-only correction, only as far as the ADR relies on them.

**Reference (approved):**
- HIO-ADR-0010 rev 3 (blob `8ade1962cf28`);
- the return accounting standard v0.2;
- the observations standard v0.2, with Q-001 r4, Q-002 r5 and Q-002-R1 r1;
- the rights standard v0.2;
- the releases standard;
- HIO-ADR-0002;
- implementation plan §S1 (S1-A1…A16, G2 evidence).

**Questions the review must answer, each with file and line references:**

1. **Supersession accuracy.** Is every revision 3 S1b provision listed in §2? Is each quotation
   exact in the approved blob `8ade1962cf28` (`hio` commit `5ea6287`)? Does the ADR supersede anything beyond S10-B2, S10-B5 and the conditional
   wording of S10-B8(ii)? Is the S1a column and history (OD-0042) untouched?
2. **No obligation deleted.** Does §5 map every S1-A1…A16 obligation, every S10-B2 inclusion and
   every G2 evidence item? Is each "Supersession proposed" limited as stated? Are S1-A10a–c still
   owed, or reported blocked?
3. **Gates not weakened.** Does each stage gate in §4.2 contain every revision 3 S10-B5
   condition for its datasets?
4. **Return mathematics unchanged.** Is the §4.1 benchmark definition consistent with RA §2,
   §3.2 and §10 (`total_return`, `replicable_with_basis`)? Is the RITS calendar patch an RA
   §3.2 step 2 alignment, not a change? Is the §4.4 "no label shift" claim correct for the TRI
   and the SOFR Index, as their documentation describes them?
5. **Observation and evidence integrity.**
   - Do the §4.3 window rules use only existing mechanisms (OBS-INV-001…007, `knowable_basis`,
     quality gates)?
   - Is `knowable_at` = W for a final-capture revision conservative, never earlier than the
     truth?
   - Do rule 3 (quarantining an out-of-window change) and §4.7 (an ingest check) only add
     fail-closed behaviour?
   - Is Q-010's existing suppression unchanged?
6. **Rights model.** Does §4.5 keep every permission unverified? Is §4.6's `unknown` versus
   `deny` distinction consistent with rights standard §1 and §3?
7. **Boundary.** Does anything create a dependency on `macsmsf`, or a distribution class beyond
   `hio_internal`?

**Out of scope:**
- verifying any right or publisher clause against live pages (owner);
- the FX-source choice;
- the equity ADR numbering;
- S1b implementation;
- any change to `src/`, `tests/`, `specs/` or `registers/`.

**Verdicts:**
- `READY`, `READY WITH CONDITIONS` or `REQUEST CHANGES`;
- findings recorded as `F-REVIEW-2026-10-25-adr0011-N`, each with a failure scenario.
