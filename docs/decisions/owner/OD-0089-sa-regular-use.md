---
id: OD-0089
title: "Owner adopts ChatGPT's recommendation: the solution architect moves from pilot to bounded regular advisory use; powers, identity, standards and Codex's review path unchanged; two held-out cases to be named; review after five genuine consultations"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-adopt-sa-regular-use.md (owner's messages, verbatim; message C is ChatGPT's text)
  sha256: 4419005de0d05f778f290e685469ab2f50dbfb7ce54a16ebfbe43934312d0940
  date: 2026-10-28
  quote: "yes, adopted"
base_revision: eb5297c
applies_to:
  - path: ~/.hio-runs/PROTOCOL.md (outside the repository)
    revision: "sha256 13a45eb7bcc5adcdbb68d50365ba141bfdf9ebb0100973a3e1d4d4c795cd71c9"
  - path: ~/.hio-runs/orch-prompt.md (outside the repository)
    revision: "sha256 6a0ef5f8554996900f7e24e5557e9a9dbd7efee9f65b48b985ca5e77522006f1"
related: {adrs: [], tasks: [], findings: [], ods: [OD-0081, OD-0082, OD-0083, OD-0084, OD-0087, OD-0088]}
---

# OD-0089: the solution architect in regular use

## Basis

ChatGPT graded the OD-0087 stress test independently. By its report (section 9, verbatim in the source file):
- the six seals and the results-file hash matched;
- all twelve runs passed Score A;
- there were no critical or major failures, and five minor weaknesses;
- critical items were stable across all six pairs.

Its full grading report is **not yet recorded** in the repository; only section 9 was supplied. The owner adopted
ChatGPT's recommendation: "yes, adopted".

## What is authorised

- **Bounded regular advisory use** of the CLI solution architect.
  - Its limits are unchanged: read-only assessment, repository evidence first, explicit authority boundaries,
    and Codex's independent verification.
  - It still never approves, accepts, waives or widens scope, and never directs Codex (OD-0081).
- **Folded into the normal hiomux workflow:**
  - PROTOCOL.md gains "Regular use": consult before a substantial recommendation, report its view alongside
    Claude's, and flag the review after the fifth genuine consultation;
  - the orchestrator prompt points to it.

  The new hashes are in the front matter above. hiomux is unchanged (`4e1b3133…`, OD-0088).
- **A performance review** after five genuine advisory consultations (`ask` and `assess`; not `eval` or
  `probe`). Claude flags when it is due. Five is Claude's concrete reading of "several".

## Pending

- **The two held-out stress cases:** to be named by the owner or ChatGPT, then recorded here as a correction.
  Until then, no stress case is used for tuning.
- **ChatGPT's full grading report:** to be recorded verbatim in `docs/history/` when the owner supplies it.

## Not authorised

- any change to the identity (v0.2 stays), the context manifest, the schema or the boundary;
- new powers;
- any change to Codex's review path or to approved standards;
- final acceptance of the architect as an architectural authority. ChatGPT: "not final acceptance of an
  autonomous architectural authority".

## Corrections (append-only)
