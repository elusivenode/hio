---
id: HIO-RESEARCH-T0002-H2-PACK
title: "Reading pack: the owner's rights decision on H2 (US Treasury par yield curve)"
status: draft              # for the owner's reading. Verifies nothing, and decides nothing
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-11-04
task: T-0002
instruction: OD-0150
---

# H2 reading pack

> **The decision is the owner's own reading of the live pages.** The quotes below came through a page-to-text tool on 2026-11-04, so they can't be the sole basis. No data file was requested.

## Read these

| Page | What it showed through the tool |
|---|---|
| <https://home.treasury.gov/subfooter/site-policies-and-notices> | **No clause on copyright, public domain, reuse, automated access or attribution** |
| <https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics> | The rates are "based on" "closing market bid prices on the most recently auctioned Treasury securities"; inputs are "indicative quotations obtained by the Federal Reserve Bank of New York" at "approximately 3:30 PM". No terms stated |
| <https://www.law.cornell.edu/uscode/text/17/105> | 17 U.S.C. §105, the basis of the public-domain presumption: copyright isn't available for works of the US Government. **Not read here**, cited from the existing matrix |

**So the case rests on a presumption, not a licence.** No Treasury page grants or restricts anything that was found.

## The two questions (from the matrix)

- **V2:** is one modest, one-off download of public-domain history acceptable on your reading, given that the terms are silent on automated access? The same reasoning served for the RBA (U1).
- **V3:** does the NY Fed's role as collector of the input quotes change Treasury's public-domain presumption? Claude's recommendation is no, because Treasury publishes the curve as its own work. That is unverified.

## The decision, one operation at a time

For `us_treasury_rates`, par yield curve only. Recommendations are from `docs/research/T-0002-free-history-sources-matrix.md`.

| Operation | Recommended | Condition |
|---|---|---|
| Retrieve, one-off | your judgement | modest, declared User-Agent |
| Retain raw | allow | cite Treasury; no implied endorsement. **You must also state a duration:** proposed "indefinite, for audit and rebuild", as for the five capture datasets (`docs/research/T-0002-owner-verification-matrix.md`) |
| Calculate | allow | same |
| Store derived | allow | same |
| Rebuild and reconstruct | allow | same |
| External processing | allow | same |
| `hio_internal` | allow | same |
| Agent context | allow | same |

**Not covered by a yes on H2:** Board H.15 (a separate row); bill rates, unless you include them; scheduled capture of this curve; any release to a consumer; the comparison reference, which is still open in the spec and may need a licence.

**Without a cleared reference, the experiment can't complete its triangulation.** It could still run and be reported as unreferenced. That is a choice for the experiment's own yes.
