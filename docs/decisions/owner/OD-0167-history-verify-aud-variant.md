---
id: OD-0167
title: "Owner leaves the disclosed bound in branch history, assigns one narrow Codex verification of T-0022's five fixes, and authorises the AUD variant of E-0002 on H.10"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-yes-history-verify-aud.md (owner's message, verbatim)
  sha256: e59c84a0dc2e6c44708812b6c59427b7f8fb87009fafaa1f0c078f7b2d89055b
  date: 2026-11-04
  quote: "yes to all"
base_revision: eaeee62cdda7599111d04bc3c2df8cbc0108bd8e
related: {adrs: [], tasks: [T-0022], findings: [F-REVIEW-2026-11-04-t0022-1-1, F-REVIEW-2026-11-04-t0022-1-2, F-REVIEW-2026-11-04-t0022-1-3, F-REVIEW-2026-11-04-t0022-1-4, F-REVIEW-2026-11-04-t0022-1-5], ods: [OD-0162, OD-0166]}
---

# OD-0167: history, verification, AUD variant

1. **The bound stays in the branch's earlier commits** (OD-0162 correction 3). Nothing is rewritten.
2. **Verification `VERIFY-2026-11-04-t0022-1-1` is assigned.** Its assigned head is the commit that adds this record: `git log -n1 --format=%H -- docs/decisions/owner/OD-0167-history-verify-aud-variant.md`. Scope: the remediation claims for F-REVIEW-2026-11-04-t0022-1-1 to 5 only, as implemented in `tools/eodhd_eval.py`, its tests, and `docs/evidence/e0002/assessment-1.md`. The review record is on this branch, imported byte-identically. Codex receives no licensed bytes or values, and the workspace is unreadable for the run. It writes only under `reviews/`.
3. **The AUD variant of E-0002 is authorised:** the one-off H.10 archive request, retained outside the repository; your three allocations translated to AUD, unhedged under RA §4.1, on H.10's noon New York rate; local and FX contributions; a comparison of EODHD's AUD/USD with H.10 as counts and pass or fail; a recorded variant; results in the owner's local report only.

## A receipt deviation, disclosed

The review's record and handoff are imported byte-identically. **Its test plan isn't:** Codex's file had no front matter, which \`check_repo\` requires, so the receiver added a front matter block and changed nothing else. Reviewer's file sha256 \`fa0830fca05243a7fa84cf5e254e9f41a8c690cbeff7877d9b801ffc97a08008\`, on \`review/REVIEW-2026-11-04-t0022-1-codex\`; imported file sha256 \`ff81b859bcee3f0c23bdf0f342986cbc23cf911ecac0e71b5af3c3b0fdd040d3\`. The verdict and findings aren't touched. Not yet an owner-approved exception; Claude has told the owner.

## Not authorised

Accepting T-0022, any finding's closure before verification, hedged returns, FRED, other currencies, and anything else OD-0162 and OD-0166 exclude.

## Corrections (append-only)
