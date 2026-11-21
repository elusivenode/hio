---
id: HIO-RESEARCH-T0002-CPI-PACK
title: "Reading pack: the owner's rights decision on BLS CPI-U (bls_cpi), for E-0004's inflation state"
status: draft              # for the owner's reading. Verifies nothing, and decides nothing
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-11-22
task: T-0002
instruction: OD-0181 (item 4); the owner's "yes, proceed" to the rights reading, 2026-11-22
---

# CPI reading pack

> **For the owner to read against the live pages.** The quotes below were read on 2026-11-22 and are exact. They don't replace your own reading. `bls_cpi` stays `unverified` (deny) until you decide.

## The two pages

**1. [BLS Copyright Information](https://www.bls.gov/opub/copyright-information.htm)** (no date shown):
- "everything that we publish, both in hard copy and electronically, is in the public domain", "except for previously copyrighted photographs and illustrations."
- "You are free to use our public domain material without specific permission"; "we do ask that you cite the Bureau of Labor Statistics as the source."
- "Unauthorized use of the BLS emblem is prohibited."

**2. [BLS Terms of Service](https://www.bls.gov/developers/termsOfService.htm)** ("Last Modified Date: August 30, 2023"):
- "Data accessed through BLS.gov do not, and should not, include controls over its end use."
- "Users of the public API should cite the date that data were accessed or retrieved using the API."
- "Users must clearly state that" "BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov."
- "Users may not modify or falsely represent content accessed through BLS.gov and still cite the source as BLS.gov."
- "Use of the APIs may be subject to certain limitations on access, calls, or use"; the page gives no numbers.
- The BLS.gov logo may not be used on products that aren't BLS-sponsored.

Neither page mentions CPI specifically, retention or redistribution. Public domain answers those, but you decide whether to rely on it, as you did for Treasury (OD-0156) and the Federal Reserve Board (OD-0166).

## Proposed rights for `bls_cpi`

**One notice for every use:** "Source: U.S. Bureau of Labor Statistics, CPI-U (CUUR0000SA0), retrieved <date>. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov." No BLS emblem or logo. Derived series are labelled as HIO's, not as BLS content.

| Operation | Proposed |
|---|---|
| automated_retrieval | conditional: one bounded download (the CUUR0000SA0 series and BLS's release-date records), declared User-Agent, **after its own yes** |
| raw_retention | conditional (the notice), **indefinite**, for audit and rebuild |
| internal_compute, derivation, derived_storage | conditional (the notice) |
| distribution: hio_internal | conditional (the notice) |
| agent_context | conditional (the notice). Public data, so Claude may read the values |
| external_processing | conditional (the notice). Codex may read it in a review |
| quotation_in_documents | conditional (the notice). Public domain, so CPI values may appear in repository documents |
| distribution: smsf_app, smsf_trustee_pack, smsf_auditor, third_party | unknown (deny) until a consumer is approved |
| post_termination_raw, post_termination_derived, audit_retention | unknown |

## What you decide, and what a yes authorises

**Verify `bls_cpi` with these rights?** A yes records it `owner_verified` in an OD, on the public-domain presumption and the two pages, with the notice above. It authorises no download; that is the next, separate yes.

ALFRED (`alfred_fred.cpi_release_dates`) stays unverified: BLS's own release records are enough, and ALFRED's tags vary by series.
