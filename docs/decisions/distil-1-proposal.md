---
id: HIO-DISTIL-1
title: "Findings distil 1: a disposition for each of the 57 Inbox lines"
status: accepted   # OD-0093 at 8393552 (drafted under OD-0092)
owner: owner (accepts); drafted by claude/implementation-agent
last_reviewed: 2026-10-28
---

# Findings distil 1

The first distil under harness-0.9a (operating model §4.1; OD-0091, OD-0092). The Inbox at `624db08` held 57 lines:
42 seed lines and 15 added under OD-0092. **Every line leaves the Inbox.**

| Outcome | Lines | Count |
|---|---|---|
| Settled as written, or lightly shortened | the rest | 33 |
| Settled with a substantive update | 01, 08, 16, 19, 20, 28 | 6 (counted in the 46) |
| Merged into one Settled line | 03+22, 06+53, 07+21, 17+35, 29+30, 39+54, 47+48 | 7 merges (14 lines → 7) |
| Dropped from the index | 10, 11, 34, 56 | 4 |

The proposed Settled section therefore has **46 lines**.

## How the lines were checked

Claude re-read each line's cited source at `624db08`. Where a citation's line numbers had drifted, the Settled text
cites the function or section instead (01, 02). Lines whose source is a session observation ("reproducible") were
reproduced in the 2026-10-28 sessions. Settled lines describe; they never govern (operating model §4.1).

## Dispositions

Line numbers follow the Inbox order at `624db08`. **S** settled, **S\*** settled with a substantive update, **M**
merged, **D** dropped.

| # | Area | Disposition | Note |
|---|---|---|---|
| 01 | repo | S\* | Adds the `specs/factors/archive/<id>@<version>.yaml` rule, added to the check after the seed (T-0009 F-4); cites the check by name, not line |
| 02 | repo | S | Verified `check_public` (~l.268–271) |
| 03 | repo | M with 22 | One line, tagged `[rediscovery]` (recurred 2026-10-28) |
| 04 | repo | S | |
| 05 | repo | S | Verified: all four `uses:` pinned by SHA |
| 06 | repo | M with 53 | Tagged `[rediscovery]`: four failed pushes (OD-0092 correction 1) |
| 07 | repo | M with 21 | Tagged `[rediscovery]` |
| 08 | releases | S\* | Updated: S1a now pins its spec versions (`S1A_SPECS`), so the risk is now named generally |
| 09 | releases | S | Verified `_places` |
| 10 | releases | D | Superseded: the fixed publication mapping (F-1 `verified_closed`, OD-0075). The history stays in the OD |
| 11 | rights | D | Current state, not knowledge: it belongs in `registers/sources.yaml` and STATUS (OD-0076) |
| 12 | rights | S | |
| 13 | sources | S | |
| 14 | review | S | |
| 15 | review | S | Shortened (the counts stay in the finding record) |
| 16 | review | S\* | Adds the lesson "write the negative cases first" |
| 17 | harness | M with 35 | One cost line, citing OD-0066/67 and OD-0074 to OD-0079 |
| 18 | harness | S | Shortened; cites OD-0069 |
| 19 | harness | S\* | Re-verified: still true at `624db08`; "Applies to" updated |
| 20 | harness | S\* | Adds Fable (OD-0090) as an example |
| 21 | repo | M into 07 | |
| 22 | repo | M into 03 | |
| 23 | repo | S | |
| 24 | repo | S | Verified the tool exists |
| 25 | repo | S | |
| 26 | repo | S | |
| 27 | repo | S | |
| 28 | rights | S\* | Kept as the reusable pattern only; the D7 state stays in the register |
| 29 | data | M with 30 | One calendar line, "Applies to: the 2026 calendars" |
| 30 | data | M into 29 | |
| 31 | tools | S | |
| 32 | review | S | |
| 33 | review | S | Keeps the remedy (state the exact string); the owner-decision alternative is in OD-0078 |
| 34 | review | D | A candidate owner decision, not knowledge; STATUS lists it (OD-0061 and hiomux reports) |
| 35 | review | M into 17 | |
| 36 | hiomux | S | |
| 37 | hiomux | S | |
| 38 | hiomux | S | |
| 39 | hiomux | M with 54 | The unexplained change stays open (OD-0077 finding 1); the session-start hash check now exists |
| 40 | hiomux | S | |
| 41 | process | S | |
| 42 | process | S | |
| 43 | hiomux | S | |
| 44 | hiomux | S | |
| 45 | review | S | |
| 46 | process | S | |
| 47 | ops | M with 48 | |
| 48 | ops | M into 47 | |
| 49 | review | S | |
| 50 | review | S | |
| 51 | review | S | |
| 52 | repo | S | |
| 53 | repo | M into 06 | |
| 54 | hiomux | M into 39 | |
| 55 | hiomux | S | |
| 56 | hiomux | D | A pending action (the manifest fix, OD-0092), not knowledge; it becomes false once applied |
| 57 | ops | S | |

## What acceptance means

**The owner accepts the Settled section of `knowledge/findings.md` at this branch's head** (or asks for changes).
Accepted lines take precedence rank 5: navigational, and the cited source wins. Acceptance does not approve anything
the lines describe. After acceptance, Claude merges the branch, empties nothing else, and new candidates append to
the Inbox as before.
