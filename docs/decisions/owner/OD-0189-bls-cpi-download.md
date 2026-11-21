---
id: OD-0189
title: "Owner authorises one bounded BLS CPI download (at most 20 requests), with the owner's email as the declared contact; nothing run"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-bls-download.md (owner's message, verbatim, with Claude's question)
  sha256: 59fa15fdc2143025e3437ddd0bf0fc54eb732dca92ba6143610799db7d86d9e6
  date: 2026-11-22
  quote: "Yes"
base_revision: c6886d9e50d034f3a21cb57fa5d736e2a078592c
related: {adrs: [], tasks: [T-0002], findings: [], ods: [OD-0179, OD-0187, OD-0188]}
---

# OD-0189: one bounded BLS CPI download

**Authorised, at most 20 requests in total, once:**
1. CPI-U `CUUR0000SA0` from 2005 on, through BLS's public API v1 (no key);
2. BLS's CPI news-release archive page (release dates since 2007);
3. up to 12 archived CPI news releases, to test whether today's NSA values equal the first-published ones.

**How:** a declared User-Agent naming the owner's email as contact, sent to BLS only. The email is passed at run time and never written to the repository, a manifest or a prompt. **Where:** `~/.hio-research/E-0004/raw/`, under a manifest with each file's sha256 and the OD-0188 notice. This satisfies `bls_cpi`'s automated-retrieval condition for this one download only.

**Built by:** a hiomux worker writes the fetch tool and its tests on invented responses; Claude runs it once on the real service.

## Not authorised

A second download; adopting E-0004 or running any part of it; ALFRED.

## Corrections (append-only)

### Correction 1 (2026-11-22): the API refused; one flat file instead

Two runs at `2be6b4f` stopped on BLS's API v1 answering HTTP 503 to the first request (22:48Z and about 22:51Z); nothing was written; **2 of the 20 requests used.** The owner then authorised ("Y", `docs/history/2026-11-22-owner-yes-bls-flat-file.md`, sha256 `7eaa6f7905e05a7f8cbee7236d8930dc844e6b13d7a2d271e32d75c5c078902e`) one GET of `https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems` in place of the API calls, with the same User-Agent, storage and limit (**18 remaining**), then the archive page and up to 12 archived releases as before. If BLS refuses again, Claude stops and reports.
