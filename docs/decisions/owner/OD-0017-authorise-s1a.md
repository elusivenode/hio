---
id: OD-0017
title: "Owner authorisation of S1a (synthetic-fixture foundation) under HIO-ADR-0010 rev 3: create the private hio repository and migrate the verified history"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/documentation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-s1a-authorisation.md (the owner's chat message, verbatim)
  sha256: 829b9fd2769c03ce82035e07dadb4242c8ba074ea78ab5d2ac1a3519b7839e8a
  date: 2026-10-24
  quote: "I authorise S1a under HIO-ADR-0010 revision 3, using the approved boundaries and acceptance requirements. [...] This is authorisation to perform S1a work, not acceptance of S1a or authorisation of S1b."
applies_to:
  - path: hio/      # macsmsf path; migrated to this repository's root
    revision: dc4fd0241fe039fd2e8361cb82604a59a0458413   # macsmsf@dc4fd02, the migration source
related: {adrs: [HIO-ADR-0001, HIO-ADR-0008, HIO-ADR-0009, HIO-ADR-0010], tasks: [T-0005], findings: []}
---

# OD-0017: authorise S1a

## Owner action

The owner authorised **S1a** under HIO-ADR-0010 revision 3 (approved, OD-0011), "using the
approved boundaries and acceptance requirements". This record transcribes the parameters the
owner set; the owner's message is the authority.

| Item | Owner's setting |
|---|---|
| Migration source | `macsmsf@dc4fd0241fe039fd2e8361cb82604a59a0458413` |
| Destination | a new private repository, `elusivenode/hio`. Claude may create it and migrate the verified history |
| `macsmsf` side | `docs/hio-a01-baseline` stays **unmerged**. Any pointer change to `macsmsf/main` needs a **separate reviewed change** |
| Migration method | history-preserving subtree split, with local provenance, identity, content-hash and link verification **before the first push**. Stop and report any discrepancy before pushing |
| Stack | Python 3.13, `uv`, `pytest`, `hypothesis`, `ruff`, DuckDB |
| CI | GitHub Actions only: minimum permissions, no secrets, no scheduled workflows |
| Boundary | **strictly synthetic-fixture-only.** No source-data network fetch, live data, credentials, buckets, scheduled capture or SMSF integration |
| Review | submit the implementation and evidence at a fixed revision for independent Codex review |

## What this record does NOT do

- It does **not** accept S1a. Acceptance is a separate owner action after the Codex review.
- It does **not** authorise S1b, a bucket, credentials, scheduled capture or any live data
  operation.
- It does not authorise a `macsmsf` pointer change or merge.
- It changes no approval. Migration preserves approval state (operating model §8.1 item 5).

## Corrections (append-only)

- 2026-10-24: this id was first used for a **draft** prepared under OD-0016 (`macsmsf@dc4fd02`,
  file `OD-0017-authorise-s1a-DRAFT.md`, with no authority). The owner's message completed its
  **[owner]** fields. The draft's proposed order of work and stop conditions are kept below as
  Claude's working plan; they are not owner words.

## Working plan (Claude's, from the draft; not owner words)

1. Split and verify locally, then push. Done: see `MIGRATION-MAP.md`.
2. Harness CI checks (operating model §8).
3. Contracts, then the observation/vintage/knowability model, then the three constructions,
   then the gates. Each is tested against the ADR-0010 S1a acceptance list.
4. Codex review at an owner-assigned fixed head; then the §10 fresh-session test (S1-A16).

**Stop conditions:**
- the implementation plan's stop conditions;
- any need for network data, or for `macsmsf` code or data;
- any change to an approved document's content.
