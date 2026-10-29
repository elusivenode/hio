---
id: OD-0118
title: "Owner authorises T-0011 authoring (I-1 to I-6, offline validation only) with the H3 and H4 decision packs; GitHub branch protection on main and the capture Environment; S1b-1 release notices and, once implemented, recording the derivation conditions as satisfied"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-t0011-github-notices.md (owner's message AO, verbatim, with Claude's decisions put)
  sha256: b0553fe2b061cdd8b880afeb84d1f10ade462063ce59da60634da7c4c9a8d00c
  date: 2026-10-29
  quote: "yes to all"
applies_to:
  - path: registers/tasks/T-0011-s1b1-infrastructure-as-code.md
    revision: "main at c70019d"
  - path: registers/tasks/T-0010-s1b1-non-live-integration.md
    revision: "main at c70019d"
related: {adrs: [HIO-ADR-0012, HIO-ADR-0006], tasks: [T-0010, T-0011], findings: [], ods: [OD-0115, OD-0116, OD-0117]}
---

# OD-0118: T-0011 authoring, GitHub settings, release notices

## Authorised (each as put)

1. **T-0011 I-1 to I-6:** write and offline-validate the OpenTofu code (`tofu fmt`, `validate` with
   `-backend=false`), with hiomux workers; draft the H3 (controls) and H4 (storage) decision packs as `proposed`.
   T-0011 moves to `authorised` for these items.
2. **GitHub (I-7), by `gh`:** branch protection on `main` (changes only by pull request, CI must pass, no
   force-push, no deletion); a `capture` Environment limited to `main` with the owner as required reviewer. From
   then on Claude lands work on `main` by pull request.
3. **Release notices:** add the RBA attribution and no-endorsement statement and the NY Fed D, E and T notices to the
   S1b-1 releases (an extension of T-0010); once implemented and tested, record the derivation conditions of the five
   dataset records as satisfied, citing this OD and the implementing commit. **If the manifest schema cannot carry
   them without amending the releases standard, Claude stops and asks.**

## Not authorised

`tofu plan` against Azure or `apply`; provider registration; any Azure or Entra write; GitHub changes beyond item 2;
I-8 (second copy); any release labelled final; distribution beyond `hio_internal`; Authorisation B.

## Corrections (append-only)
