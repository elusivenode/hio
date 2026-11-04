---
id: OD-0166
title: "Owner decides the H.10 rights for the Australian dollar series, having read the live pages; frb_h10.aud_usd is owner_verified with no condition yet met"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-h10-rights.md (owner's message, verbatim)
  sha256: caa55086d05ea7e15a4fd5e17e81a3877ed3680cc5f1748de3b3154306bd17cc
  date: 2026-11-04
  quote: "yes to all, pages read"
base_revision: 05222af9318e6bd3e7ffea1fd4c39b05a69d5079
related: {adrs: [], tasks: [T-0002, T-0022], findings: [], ods: [OD-0156, OD-0165]}
---

# OD-0166: H.10 rights, AUD/USD

The owner read the live pages and answered yes to all four decisions in `docs/research/T-0002-h3-reading-pack.md`:

1. **F1:** the Board's public-domain statement reaches these rates.
2. **F2:** one one-off request for the Board's XML archive is acceptable.
3. **Retention:** raw archive "indefinite, for audit and rebuild", citing the Board with no implied endorsement. Other currencies are retained as bytes and not used.
4. **Calculate, store derived, rebuild, external processing, `hio_internal`, agent context:** allowed on the same conditions.

`frb_h10.aud_usd` is `owner_verified`. The parent `frb_h10` row stays `unverified`.

## How Claude read it

**"All" is the four decisions.** Claude said a yes here wouldn't authorise the AUD variant of E-0002, and that the download would run with that variant. So nothing is downloaded yet, and no condition is recorded as met, so the gate still refuses. Claude has asked.

## Not authorised

The download or the AUD variant, until the owner answers; other currencies' use; FRED; scheduled capture; any consumer release; quotation in documents, including this repository.

## Corrections (append-only)
