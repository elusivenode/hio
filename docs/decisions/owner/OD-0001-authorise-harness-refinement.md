---
id: OD-0001
title: Owner instruction to execute the harness refinement brief (T-0006), as recorded and later corrected
decision: authorise_work
record_status: corrected
created_at: 2026-10-18
updated_at: 2026-10-18
recorded_by: claude/documentation-agent
owner_statement:
  source: hio/docs/history/2026-10-18-directive-harness-refinement.md
  sha256: 6e2ca7f35de53d2cfeb87aef9ad489489e7d3a7330bf31d47750b0f3648feeed
  date: 2026-10-18
  quote: >-
    The owner sent the file path of this brief in the Claude Code chat, with no accompanying
    words. The brief describes itself as a "Proposed documentation-only assignment; not
    architectural or implementation approval", and says the owner "need only authorise
    documentation-only harness refinement on the staged branch".
applies_to:
  - path: hio/
    revision: 85ef0fa8821e5f538b739c5fe000f3f63d3bfac1
related: {adrs: [HIO-ADR-0008], tasks: [T-0006], findings: []}
---

# OD-0001: the T-0006 harness refinement instruction

## Owner action (as it actually happened)

On 2026-10-18 the owner supplied the brief by file path, without other words. Claude treated
that as an instruction to execute it, and carried out T-0006 (commits `72d1e56`, `23ad27f`).

**The original ambiguity is preserved here.** Whether a bare file path, attached to a brief that
calls itself "proposed", was an explicit instruction to execute was not clear at the time.

The owner's subsequent directive
(`hio/docs/history/2026-10-18-directive-t0006-final-correction.md`, recorded in OD-0002):
- directs Claude to *repair* T-0006 and this record, rather than reverting the work;
- states that the owner has **not accepted T-0006** and **not approved HIO-ADR-0008**.

This record claims nothing beyond that.

## Scope and exclusions (from the brief)

**Scope:** documentation-only edits to the HIO harness within `hio/`.

**Excluded:**
- code; infrastructure;
- `macsmsf` application changes;
- HIO-001 or HIO-S1 activation;
- roadmap changes;
- ADR status changes;
- claims of Codex endorsement.

## What this record does NOT do

- It does not accept T-0006.
- It does not approve HIO-ADR-0008 or any other ADR, standard or spec.

## Corrections (append-only)

**2026-10-18 (T-0006 final correction, under OD-0002).**
- **What the earlier version said** (at `72d1e56`/`23ad27f`): `status: proposed`;
  "Claude transcription, unconfirmed"; and that T-0006 had "no standing" until the owner
  confirmed this record.
- **Why that was inconsistent:** it treated transcription as a second permission gate, after
  the work had already been done on the owner's instruction.
- **The corrected rule** (operating model §1.1):
  - an explicit owner instruction authorises bounded, reversible work immediately;
  - recording it is an audit step;
  - acceptance and approval are separate owner actions.
- **The correction does not resolve, after the fact, whether the original bare-path message was
  explicit.** That ambiguity is recorded above. The owner's later directive is the evidence of
  the owner's position on it.
