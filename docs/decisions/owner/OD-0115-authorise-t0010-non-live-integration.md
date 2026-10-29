---
id: OD-0115
title: "Owner authorises T-0010: the non-live S1b-1 integration (real HTTP transport confined to the adapters, Azure blob backend against the emulator, OIDC and workflow wiring with the schedule disabled, C1–C7 finality on synthetic inputs, 2027 calendars, draft H3 and H4 evidence packs) with hiomux Sonnet workers; nothing live"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-authorise-t0010.md (owner's messages AJ and AK, verbatim, with Claude's decision put)
  sha256: fcadd51ed3c417bb8df7507629a041150f048c27e0e4d413dbaa649ca97052c1
  date: 2026-10-29
  quote: "decision 1: yes"
applies_to:
  - path: registers/tasks/T-0010-s1b1-non-live-integration.md
    revision: "base a56462cb60a002324f90097da28168396c8ae918"
related: {adrs: [HIO-ADR-0012], tasks: [T-0009, T-0010, T-0002], findings: [], ods: [OD-0062, OD-0063, OD-0076, OD-0079, OD-0089, OD-0114]}
---

# OD-0115: T-0010 authorised (non-live S1b-1 integration)

## The instruction

Message AJ asked to proceed "with development and deployment according to our plan" and to consult the architect.
Claude answered that deployment cannot proceed yet (H1, H3, H4 and Authorisation B are each a separate owner act) and
put Decision 1, which the owner answered "decision 1: yes" (message AK). Base: `a56462c`.

## Authorised (bounded, reversible; on a branch)

1. Draft the T-0010 card (`registers/tasks/T-0010-s1b1-non-live-integration.md`).
2. A real HTTP transport, **confined to the adapters**, with the matching `tools/check_repo.py` amendment; tested
   only against fakes or local servers.
3. An Azure blob backend behind the existing store interface, tested against a local emulator.
4. OIDC and capture-workflow wiring, with **the schedule disabled**.
5. The C1–C7 checks and finality logic (HIO-ADR-0012 §4.3.3–4.3.4), on synthetic inputs.
6. 2027 calendars, by a manual documentation read within D7's verified use (OD-0076: retain and cite, manual read
   only), if the RBA has published them.
7. Draft H3 (controls; OD-0038 successor) and H4 (storage) evidence packs, as `proposed`, for the owner's decision.
8. hiomux Claude Sonnet workers, under PROTOCOL.md, each task `check`ed before integration.

## Not authorised

Any real data fetch or request to a data source; any credential, federated identity or secret; `tofu init`,
`validate`, `plan` or `apply`; provisioning; an enabled schedule; a Codex review assignment (a separate owner act);
merging T-0010 work to `main` as accepted (acceptance is a separate act); marking any right verified; Authorisation B.

## Also recorded

- The architect consultation `20261029T120200-ask-1eee` is the **fifth genuine consultation** (OD-0089): the
  performance review is now due. Advice only.
- Decision 2 (the owner's U1–U7 rights reading) is not decided here; the owner asked what is needed.

## Corrections (append-only)
