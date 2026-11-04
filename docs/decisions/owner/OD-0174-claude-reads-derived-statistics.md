---
id: OD-0174
title: "Owner allows Claude to read EODHD-derived statistics in the personal evaluation; raw prices, Codex and the architect are unchanged"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-agent-context-derived.md (owner's message, verbatim)
  sha256: 94bc32c1ac101574b7c0da7f977afc72326df8cb022d0a60d00fdf4ea4493c97
  date: 2026-11-04
  quote: "yes"
base_revision: 59429c541390d8df7a9e0900e0ad9d7be33658e2
related: {adrs: [], tasks: [T-0022], findings: [], ods: [OD-0162, OD-0163, OD-0170]}
---

# OD-0174: Claude may read derived statistics

On the owner's own reading of EODHD's terms, which don't mention AI, `agent_context` on `eodhd.personal_evaluation` becomes conditional: **derived statistics only**, such as volatility, drawdown and bootstrap intervals, read by Claude to interpret the owner's reports with the owner. It changes OD-0163's denial, and OD-0170's instruction not to send such values to agents, to that extent.

**Unchanged:** raw prices and distributions stay out of agent context. Codex and the architect receive no such values. `quotation_in_documents` stays denied, so no value goes in the repository. No SMSF use or report to others.

## Corrections (append-only)
