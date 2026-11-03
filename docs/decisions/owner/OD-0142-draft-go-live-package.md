---
id: OD-0142
title: "Owner instructs Claude to draft the go-live package (B-3); draft only"
decision: authorise_work
record_status: recorded
created_at: 2026-11-03
updated_at: 2026-11-03
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-03-owner-go-live-package-draft.md (owner's message, verbatim, with Claude's question put)
  sha256: 9d70fffa43287b39c1fe942cdab38fd8ff3a118c8fc1c96358c303ea5b30297a
  date: 2026-11-03
  quote: "yes, draft the go-live package"
base_revision: 387eee7ee39d91f5ab983284089a0949bda0fb9f
related: {adrs: [HIO-ADR-0012], tasks: [T-0009, T-0013], findings: [], ods: [OD-0063, OD-0116, OD-0119, OD-0139, OD-0140, OD-0141]}
---

# OD-0142: draft the go-live package

**Scope:** one document, `docs/evidence/S1B1-go-live-package.md`, marked `proposed` and sent by PR, covering the data-source URLs, the punctuality bar and
the OD-0063 staging statement. Reading publishers' documentation pages to propose the URLs is within it, as the Authorisation B package says.

## Not authorised

Go-live; setting `LIVE_AUTHORISATION`; configuring any URL in code; the workflow move; `alert_enabled`; removing the reviewer rule; any dispatch, capture, Azure write
or request to a data URL; adopting the punctuality bar or the staging statement.

## Corrections (append-only)

### Correction 1 (2026-11-03): architect consulted at an earlier revision

`hiomux sa ask` at `main` (`387eee7`) refused: "context bundle 92936 bytes exceeds the manifest budget 90000". The last session's Inbox lines and STATUS took it over. Claude consulted at
`310d7dd` with `--rev`, the last revision that fits, and told the architect why; `310d7dd..387eee7` changes only session-close documents. The manifest and hiomux are unchanged. Consultation
`20261103T165541-ask-dee0` is logged. Until the bundle shrinks or the owner changes the budget, the architect refuses at `main`.
