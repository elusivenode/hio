---
id: OD-0163
title: "Owner decides the EODHD evaluation is the owner's own personal research, giving a narrow rights record; authorises a zero-curve variant of the duration construction"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-eodhd-rights-variant.md (owner's message, verbatim)
  sha256: 9edc8f361821dca18d07c3cb84bb689f7fbdf2c5929ee7dc3cfd4cf0c57421d9
  date: 2026-11-04
  quote: "yes, it's my own personal research. yes to all"
base_revision: bae70d9d700501803224f131831c41503141872b
related: {adrs: [], tasks: [T-0020, T-0022], findings: [], ods: [OD-0157, OD-0160, OD-0161, OD-0162]}
---

# OD-0163: rights for the evaluation, and the zero-curve variant

## 1. EODHD: a narrow rights record

`eodhd.personal_evaluation` is `owner_verified`, on the owner's own reading of EODHD's terms, **for this evaluation only**. It rests on the owner's characterisation, not on anything from the vendor, whose position is unknown (`docs/research/T-0003-vendor-assessment-2026-11-04.md`).

| Allowed, on conditions | Denied |
|---|---|
| Retrieval with the owner's key from the owner's Mac; raw retention locally until the owner's end-of-month decision; local calculation, derivation and derived storage; results visible to the owner | Cloud or CI processing; any agent seeing values; any report to the other trustee or auditor; any SMSF use |

Post-termination rights stay `unknown`. The parent `eodhd` row stays `unverified`. It changes no standard.

## 2. Zero-curve variant

As put: a separately recorded variant valuing on the zero curve, using the retained Treasury data, with interpolation sensitivity and a comparison against flat, under a new spec version, still UNREFERENCED, with no promotion. It doesn't reverse E-0001's result, and any research reliance waits. A Codex review follows it, on an assignment the owner approves.

## How Claude read it

"yes to all" followed two open questions, so it's read as those two. **It isn't read as** the subscription having been made, or as a merge. Claude's earlier "I'd default to deleting" at cancellation stays a proposal.

## Not authorised

Everything OD-0162 and OD-0157 exclude. Accepting E-0001, the variant or any EODHD series.

## Corrections (append-only)
