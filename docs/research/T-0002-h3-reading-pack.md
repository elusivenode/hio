---
id: HIO-RESEARCH-T0002-H3-PACK
title: "Reading pack: the owner's rights decision on H3 (Federal Reserve Board H.10 AUD/USD)"
status: draft              # for the owner's reading. Verifies nothing, and decides nothing
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-11-04
task: T-0002
instruction: OD-0165
---

# H3 reading pack

> **The decision is the owner's own reading of the live pages.** The quotes came through a page-to-text tool on 2026-11-04, so they can't be the sole basis. No data file was requested.

## Read these

| Page | What it showed through the tool |
|---|---|
| <https://www.federalreserve.gov/disclaimer.htm> (last update 2024-08-02) | "Unless otherwise indicated, information on Board's website is in the public domain" and "may be copied and distributed without permission"; "Please cite to the Board as the source of the information." Non-Board material needs the non-Board source's permission. Seals and logos are excluded. **Automated access isn't addressed** |
| <https://www.federalreserve.gov/releases/h10/hist/> (last update 2026-11-02) | Australia is listed. "noon buying rates in New York for cable transfers payable in foreign currencies"; certified by the Federal Reserve Bank of New York for customs purposes; updated Mondays at 4:15 pm |
| <https://www.federalreserve.gov/releases/h10/> | The current release. Links an XML archive, `/releases/h10/data/FRB_h10_xml.zip`. "From May 22, 2006, to January 2009, the weekly H.10 release ceased publication", with that period's data on the Data Download Program |
| <https://www.federalreserve.gov/data/data-download-fred-information.htm> | Build Your Package goes the week of 2026-11-09; "Historical data will remain available for download as XML files on statistical release pages" |

**Unlike Treasury, the Board states its position.** The case rests on a published statement with a citation condition, not only a presumption. The open points are below.

## The questions

- **F1:** does "public domain unless otherwise indicated" reach these rates, given the third-party carve-out? The rates are the Board's release, certified by the New York Fed, and no page read marks them as third-party. Claude's recommendation is yes. Unverified.
- **F2:** is one modest, one-off download acceptable, given that automated access isn't addressed? This is the same reasoning as RBA (U1) and Treasury (V2).

## The decision, one operation at a time

For `frb_h10`, the Australian dollar series only. Recommendations are from `docs/research/T-0002-free-history-sources-matrix.md`, row H3.

| Operation | Recommended | Condition |
|---|---|---|
| Retrieve, one-off | your judgement | one archive request, declared User-Agent |
| Retain raw | allow | cite the Board; no implied endorsement. **State a duration:** proposed "indefinite, for audit and rebuild". The archive covers other currencies too: they're retained as bytes and not used |
| Calculate | allow | same |
| Store derived | allow | same |
| Rebuild and reconstruct | allow | same |
| External processing | allow | same |
| `hio_internal` | allow | same |
| Agent context | allow | same |

**Not covered by a yes:** other currencies' use; FRED, whose terms bar storage (`knowledge/findings.md`), even though it republishes this series; scheduled capture; release to a consumer; quotation in documents, including this public repository; any change to EODHD's rights.

## What it would and wouldn't do

**Would:** give a declared fixing, noon New York, for an unhedged AUD translation, and the first independent check on EODHD's AUD/USD.

**Wouldn't:**
- **Timing:** noon New York isn't a US or ASX close, so daily figures carry noise (RA §4.4). Monthly should be primary.
- **Hedging:** it's spot only.
- **Point in time:** values are reconstructed(T). Weekly release means a daily value is knowable up to about a week later.

**To confirm from the file, not assumed:** the quote direction (USD per AUD is expected; RA-INV-007 governs an inversion), the start date (Claude's "about 1971" is from memory), whether the archive fills 2006 to 2009, and how holidays and missing values appear.

**No November deadline:** the Build Your Package removal doesn't remove this history, on the Board's own statement. The archive's continued availability is still worth not leaving for years, given the "eventual retirement" of the Data Download Program.
