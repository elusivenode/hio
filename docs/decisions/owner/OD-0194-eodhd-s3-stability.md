---
id: OD-0194
title: "Owner authorises one EODHD snapshot s3 for SPY, IEF and BIL (at most 12 requests) and its stability comparison with s2, under rules declared first"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-eodhd-s3.md (owner's message, verbatim, with Claude's question)
  sha256: 569100af4eae0a7dd32ae5145dd851a272ce4993fc9dc1574b13ee0f989b172e
  date: 2026-11-22
  quote: "y"
base_revision: 692fa8a4514417d1fbff1cd50b11bfb19d8d39b3
related: {adrs: [], tasks: [T-0003, T-0022], findings: [], ods: [OD-0162, OD-0163, OD-0164, OD-0176]}
---

# OD-0194: EODHD snapshot s3 and stability

**Authorised:** one snapshot `s3` with `tools/eodhd_eval.py` for **SPY.US, IEF.US and BIL.US only**: their eod, div and splits endpoints and the US exchange symbol list (10 requests; at most 12), with the owner's key from the HIO key vault, on the owner's Mac, kept in `~/.hio-research/E-0002-eodhd/raw/s3`. Then the comparison with `s2` under `docs/evidence/e0002/stability-1.md`, whose rules are committed before `s3` is taken. A hiomux worker adds the fund filter and the comparison tool on invented data; Claude runs both once.

Rights: `eodhd.personal_evaluation` (OD-0163, OD-0176). No value goes in the repository.

## Not authorised

Any other fund or endpoint; a second snapshot; the T-0003 decision; any factor build.

## Corrections (append-only)
