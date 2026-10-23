---
id: OD-0017
title: "DRAFT: authorise S1a (synthetic-fixture foundation) under HIO-ADR-0010 rev 3"
decision: authorise_work
record_status: draft      # NO AUTHORITY. Becomes `recorded` only on the owner's own words, quoted verbatim below
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/documentation-agent (drafted under OD-0016)
owner_statement:          # empty until the owner speaks
  source: null
  sha256: null
  date: null
  quote: null
applies_to:
  - path: hio/
    revision: "<the staging commit the owner names as the migration source>"
related: {adrs: [HIO-ADR-0001, HIO-ADR-0008, HIO-ADR-0009, HIO-ADR-0010], tasks: [T-0005], findings: []}
---

# OD-0017 (DRAFT): authorise S1a

> **Draft for the owner's decision. It authorises nothing.** Fields marked **[owner]** are
> proposals for the owner to confirm or change. HIO-ADR-0010 rev 3 (approved, OD-0011) governs
> wherever this draft differs from it.

## 1. What would be authorised

S1a as defined in HIO-ADR-0010 rev 3: make every A01 contract executable on **synthetic
sources and fixtures only**. Its scope:
- the `hio` repository and the history-preserving migration;
- CI;
- the contracts;
- a local-filesystem object-store adapter;
- the observation, vintage and knowability model with its three query modes;
- the manifest-derived catalogue;
- the three S1 constructions (`cash.aud.overnight`, `cash.usd.overnight`,
  `fx.usd_cash_vs_aud.excess`);
- the rights and publication gates, exercised on fixtures.

## 2. Boundary

| Item | Proposal |
|---|---|
| Migration source | `macsmsf` branch `docs/hio-a01-baseline` at **[owner: name the exact commit]** |
| Destination | a new **private** GitHub repository, **[owner: e.g. `elusivenode/hio`]**, owned by the owner. The owner creates it, or authorises Claude to create it with `gh` |
| Migration method | `git subtree split --prefix=hio` (or equivalent) into a local repository. **Verify locally before the first push** (§3 below). Then push into the empty private repository |
| `macsmsf` side | **[owner: choose]** (a) leave `docs/hio-a01-baseline` unmerged and add a pointer file to `macsmsf` `main` in a separate commit after migration (operating model §8.1 item 6; recommended); or (b) merge the staging branch first |
| Development stack | **[owner: confirm]** Python 3.13, `uv` with a committed lockfile, `pytest` + `hypothesis`, `ruff`; DuckDB for the local index (implementation plan). No dependency on `macsmsf` |
| CI | GitHub Actions. The workflow sets `permissions: contents: read` by default and widens only per job where needed. No secrets. Network limited to package installation. **No scheduled workflows** |
| Excluded | any network fetch of a data source; real data; credentials; buckets; schedules; S1b; any `macsmsf` change beyond the post-migration pointer |

## 3. Order of work and checks

1. **Split and verify locally:**
   - history preserved;
   - `MIGRATION-MAP.md` (old → new paths, plus the source commit);
   - id and state continuity: every ADR, OD, task, finding and review id, and its status, is
     identical on both sides;
   - approved-document content hashes match the approved blobs in the OD records;
   - links resolve.

   **Stop and report on any difference** (§8.1 item 7).
2. **Push to the private repository**, and record the migration evidence.
3. **Harness CI checks** (operating model §8).
4. **Contracts**, then the **observation/vintage/knowability model**, then the **constructions**,
   then the **gates**. Each is tested against the ADR-0010 S1a acceptance list (OBS-INV-001…007;
   RA §3.2 fixtures and CASH-USD-INV-3; FXC-INV-1…4; RA-INV-021; releases §6.1; rights
   fail-closed fixtures; import and independence checks; reproducible rebuild).
5. **Codex review** at an owner-assigned fixed head, using the review index, before acceptance.
6. **§10 fresh-session test** in sessions with no prior chat history (S1-A16).

## 4. Stop conditions

These are the implementation plan's stop conditions, plus:
- any need for network data;
- any need for `macsmsf` code or data;
- any change to an approved document's content.

## 5. What this record would NOT do

- It would not authorise S1b, a bucket, credentials, scheduled capture or any live data
  operation.
- It would not accept S1a. Acceptance is a separate owner action after review.
- It would not change any approval. Migration preserves approval state (§8.1 item 5).
