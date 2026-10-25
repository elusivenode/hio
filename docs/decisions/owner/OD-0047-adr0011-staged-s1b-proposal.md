---
id: OD-0047
title: "Owner direction: push the integrated T-0002 evidence; commit the staged-S1b proposal as a new HIO-ADR-0011 (proposed, not policy), with provision-level supersession, a complete obligation mapping and a draft Codex review assignment"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-adr0011-staged-s1b.md (pasted by the owner, verbatim)
  sha256: d81158a0b379f6ba588cf2a22d4cbd9f12d843bb2fbd301aee003abeb2be7cdd
  date: 2026-10-25
  quote: "Commit the proposed scope revision as a new **HIO-ADR-0011 — Staged S1b live-observation implementation**, rather than substantively replacing the approved HIO-ADR-0010 revision 3."
applies_to:
  - path: /
    revision: 183523fd6e2cc148abfe2619426bfc38c7cf2108   # main, verified and pushed under this record
  - path: docs/decisions/HIO-ADR-0012-staged-s1b.md   # path corrected by OD-0048 (renumbered; first committed as HIO-ADR-0011-staged-s1b.md)
    revision: bd0b8fd56bf6b849fe67abf04493e9e1693eb296   # the commit that first added it, as HIO-ADR-0011, on docs/adr0011-staged-s1b-proposal
related: {adrs: [HIO-ADR-0010, HIO-ADR-0011, HIO-ADR-0005, HIO-ADR-0007, HIO-ADR-0004, HIO-ADR-0002], tasks: [T-0002, T-0005], findings: []}
---

# OD-0047: HIO-ADR-0011 (staged S1b) proposed

## Owner action (summary; the verbatim text is in the history file)

1. **Verify and push** the integrated T-0002 evidence; every permission stays unverified.
2. **Commit the staged-S1b scope as a new HIO-ADR-0011**, not a substantive replacement of
   HIO-ADR-0010 rev 3.
3. **Record exactly** which revision 3 S1b provisions would be superseded, preserving the S1a
   history and acceptance.
4. **Preserve** the return mathematics, the observation invariants, release integrity and the
   boundary.
5. **Treat RBA retrieval and the SOFR permissions** as recommended interpretations, pending
   per-dataset, per-operation verification.
6. **Keep WM/Reuters and ASX unavailable**, distinguishing absent from denied.
7. **Define the cash factors** as funding or cash benchmarks.
8. **Map every** original S1b obligation.
9. **Preserve Q-010's fail-closed behaviour**, and specify the publication and revision
   windows.
10. **Prepare a bounded Codex review assignment** for the owner's consideration.

**Prohibited:**
- approving the ADR;
- verifying any right;
- starting S1b;
- fetching market data;
- contacting providers;
- creating credentials;
- deploying infrastructure.

**Stop condition:** any change to the return mathematics or the evidence-integrity contract.

## Execution

**Step 1.**
- `main` = `183523f`, with parents `a37d81f` and `b35c75c`; its tree is equal to `b35c75c`'s.
- `origin/main` (`a37d81f`) was an ancestor.
- Protected paths were unchanged against `origin/main`.
- A clean worktree ran `check_repo` PASS and `pytest` 278 passed. Every genuine rights record
  loads as `unverified`, with no permission other than `unknown`.
- Pushed: `a37d81f..183523f`.

**Steps 2–10.**
- `HIO-ADR-0011` (now [`HIO-ADR-0012`](../HIO-ADR-0012-staged-s1b.md); see Corrections), `status: proposed`;
- the draft review assignment (now [here](../HIO-ADR-0012-review-assignment-draft.md)), `status: draft`
  (not an assignment);
- the [verification matrix](../../research/T-0002-owner-verification-matrix.md) relabelled as
  recommended interpretations, with third-party series `unknown` (unavailable), not `deny`.

The HIO-ADR-0010 file is untouched.

**No stop condition reached.**
- §4.1 keeps the RA classification (`total_return`, `replicable_with_basis`) and adds wording
  only.
- §4.3 and §4.7 use existing mechanisms, and add only fail-closed checks.

**Conflict flagged.** "HIO-ADR-0011" is already used, in non-approved planning documents, for
the equity total-return decision:
- the T-0003 card, acceptance Q3;
- roadmap G3;
- implementation plan S2;
- the G1 decision package;
- the immutable REVIEW-2026-10-18-a01.

None was edited. The owner's explicit numbering was followed, and the equity ADR needs a new
number by owner decision.

## What this record does NOT do

- It does **not** approve HIO-ADR-0011, supersede any HIO-ADR-0010 provision, or assign a
  review.
- It does **not** verify any right, lift OD-0013, or authorise S1b-1 or S1b-2.
- It does **not** decide Q-004, Q-010, the FX source or the equity ADR's number.

## Corrections (append-only)

- 2026-10-25 (OD-0048): **the owner selected HIO-ADR-0012** for this proposal, and retains
  HIO-ADR-0011 for the equity total-return source decision under T-0003.
  - The files were renamed to `HIO-ADR-0012-staged-s1b.md` and
    `HIO-ADR-0012-review-assignment-draft.md`, and the branch to
    `docs/adr0012-staged-s1b-proposal`.
  - The links and the `applies_to` path above were corrected, as the owner instructed ("any new
    links introduced by this proposal").
  - The "Conflict flagged" paragraph is **resolved** by that selection. The historical equity
    references are unedited and keep their meaning.
  - No substantive change to the proposal.
