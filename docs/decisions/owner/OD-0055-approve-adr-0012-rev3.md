---
id: OD-0055
title: "Owner approval of HIO-ADR-0012 revision 3 (staged S1b) at d0965cc; supersedes only the specified S1b provisions of HIO-ADR-0010 rev 3; S1a acceptance unchanged; no gate resolved"
decision: approve
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-adr0012-harness-0.7.1-approval.md (pasted by the owner, verbatim; Decision 1)
  sha256: 53b1b54d14a59f9bcab28dfea7698fb24e1c0fe6a76c95cb963a44487b1ac90d
  date: 2026-10-25
  quote: "I approve HIO-ADR-0012 revision 3 at commit `d0965ccfd37a0ddefdbb5ff08a11674c3267792a`, file blob `eb110ee394afa5b3a8abe612cf2e22196acbf51c`."
applies_to:
  - path: docs/decisions/HIO-ADR-0012-staged-s1b.md
    revision: d0965ccfd37a0ddefdbb5ff08a11674c3267792a   # blob eb110ee394afa5b3a8abe612cf2e22196acbf51c
related: {adrs: [HIO-ADR-0012, HIO-ADR-0010], tasks: [T-0005], findings: [F-REVIEW-2026-10-25-adr0012-1, F-REVIEW-2026-10-25-adr0012-2, F-REVIEW-2026-10-25-adr0012-3]}
---

# OD-0055: approve HIO-ADR-0012 revision 3

## Owner action

Decision 1 of the owner's instruction (verbatim in the history file above): approve HIO-ADR-0012
revision 3 at `d0965ccfd37a0ddefdbb5ff08a11674c3267792a`, file blob
`eb110ee394afa5b3a8abe612cf2e22196acbf51c`. The approval supersedes only the specified S1b
provisions of HIO-ADR-0010 revision 3. S1a acceptance is unchanged. It does not resolve Q-013, the
release-manifest schema, publisher header semantics, source permissions, infrastructure controls
or S1b authorisation.

## Verification from Git before recording (2026-10-25; the owner's stop-on-mismatch condition)

| Check | Result |
|---|---|
| `d0965cc` is the tip of `docs/adr0012-staged-s1b-proposal` | yes |
| Blob of `docs/decisions/HIO-ADR-0012-staged-s1b.md` at `d0965cc` | `eb110ee394afa5b3a8abe612cf2e22196acbf51c`, equal to the owner's blob |
| Ancestry | `main` (`6fbec1a`) is the merge base; 7 proposal commits: `bd0b8fd`, `1d68da3`, `a3976bf`, `bc939f7`, `860fd78`, `cef81f0`, `d0965cc` |
| Paths changed by the branch against `main` | only `STATUS.md`, `docs/decisions/**`, `docs/history/**`, `docs/research/**`, `handoffs/**`, `reviews/README.md`, `reviews/responses/**`. **No** `src/`, `tests/`, `specs/`, `tools/`, `.github/`, standard, operating-model or HIO-ADR-0010 file |
| HIO-ADR-0010 rev 3 | unedited on the branch (the ADR's own banner and this diff agree) |

## Scope and exclusions

- Effect (ADR-0012 §2): supersedes **only** HIO-ADR-0010 rev 3's S10-B2 and S10-B5, and the wording
  of S10-B8(ii) if the FX source is not RBA F11. Every revision 3 S1b obligation is kept and
  re-mapped (§5); the §3 invariants are unchanged.
- Adopts the technical verification of F-REVIEW-2026-10-25-adr0012-1, -2 and -3 recorded in
  OD-0054, with their conditions preserved. That is technical verification, not a waiver.
- Status-only edits follow: the ADR's `status`, `approved_by` and *Approval*; the decisions
  register row; a status note on HIO-ADR-0010; `STATUS.md`.

## What this record does NOT do

- It does **not** decide Q-013 (the ADR stands without it and falls back to `schedule_only`), the
  release-manifest schema, publisher header semantics (a dataset has no finality until evidenced),
  any source right (all `unverified`), network or credential controls (OD-0038), or the FX source.
- It does **not** authorise S1b-1 or S1b-2, alter accepted S1a, or change the return mathematics.
- It does **not** receive any Codex record; `e1f60f9` and `dac54f5` stay unreceived until OD-0057
  and the supervised receipt.

## Corrections (append-only)

None.
