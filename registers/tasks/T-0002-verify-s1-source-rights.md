---
id: T-0002
title: Verify rights, coverage and publication timing for the S1 sources
status: in_progress
owner: owner
assignee_role: architecture agent (research) + owner (verification)
created: 2026-10-18
authorised_by: OD-0009   # research task; begun under OD-0010; held by OD-0013 (stale comment corrected, OD-0014)
base_revision: f7a9ec90bb2f0cbd58272c5bd0f0da07948a4ecb
links: {adrs: [HIO-ADR-0004, HIO-ADR-0005], standards: [rights-and-licensing, observations-and-point-in-time], depends_on: [], blocks: [T-0005 publication criteria]}
---

# T-0002: verify the S1 source rights, coverage and timing

## Objective
Turn the S1 source hypotheses into verified records:
- RBA statistical tables;
- NY Fed SOFR;
- US Treasury bill rates;
- Federal Reserve Board H.10.

Specifically: terms of use, by every rights dimension; history start; publication schedule and
timezone (to fill `knowable_basis`); access method (keyless or not); and known revision
behaviour.

## Approved scope
- reading each publisher's terms and documentation;
- recording findings in `registers/sources.yaml` with evidence (URL, retrieval date, section);
- the owner then sets `verification: owner_verified`.

## Non-goals
- writing fetch code;
- downloading datasets beyond a single manual sample to confirm the format.

## Environment and rights constraints
Read-only web access to public terms pages. **An agent may propose `allow`; only the owner sets
`owner_verified`.**

## Acceptance tests
| ID | Test | Evidence |
|---|---|---|
| R1 | every rights dimension for the 4 sources is `allow`, `deny` or `conditional`, with evidence; none is `unknown` | sources.yaml diff |
| R5 | the permissions each S1 operation requires (rights standard §3: fetch, store raw, build, store derived, rebuild, publish) are verified **before live capture**, not only before publication; `automated_retrieval` is included | sources.yaml; a mapping table |
| R2 | the publication timing per series is stated, and how vintage evidence will be obtained (`captured_on_schedule` for captured vintages; whether any `publisher_timestamp`, `publisher_vintage` or `archived_receipt` evidence exists for history) | sources.yaml; spec patch PRs |
| R3 | `agent_context` and `external_processing` (CI runners) are explicitly resolved | sources.yaml |
| R4 | the spec `availability` fields are updated by versioned patch | spec changelogs |

## Open issues
If any source forbids storage or derivation, S1 is re-scoped (stop condition in the
implementation plan).

## Progress (2026-10-18, begun on OD-0010)

Findings drafted at `docs/research/T-0002-source-rights-and-timing.md`. **R1–R5 need owner verification**; `automated_retrieval` is unresolved for RBA, Treasury and H.10; the BAB source is undetermined.

- 2026-10-18: **OD-0013:** every source permission stays `unverified` and blocked until the outstanding terms, source, timing and calendar questions have evidence.
- 2026-10-25: **OD-0045:** primary-source evidence for RBA and NY Fed recorded at `docs/research/T-0002-rba-nyfed-evidence-2026-10-25.md`, from manual inspection only (samples deleted). Findings: RBA F11 AUD/USD is the WM/Reuters fix (third party) and the F1 BAB is ASX (third party); the RBA FX "4.00 pm (Sydney)" is local time; RITS and NSW calendars differ. Every permission stays `unverified`.
