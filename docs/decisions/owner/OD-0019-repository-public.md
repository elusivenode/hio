---
id: OD-0019
title: "Owner instruction: make the hio repository public (amends OD-0017's 'private')"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/documentation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-make-public.md (the owner's chat message, verbatim)
  sha256: e36d09f4fcf6c07dcd911db901a06a5b635004daa34bef2359194097a4e56572
  date: 2026-10-24
  quote: "needs to be public for ChatGPT can review"
applies_to:
  - path: /
    revision: f10ad70c143a84398dcd8d9140b39b292f8d59db
related: {adrs: [HIO-ADR-0005, HIO-ADR-0006], tasks: [T-0005], findings: []}
---

# OD-0019: make the repository public

## Owner action

The owner instructed that `elusivenode/hio` be made **public**, so that ChatGPT (a strategic
collaborator, `AGENTS.md` rule 4) can review it. This **amends OD-0017's destination** ("a new
private repository"). Every other OD-0017 term stands.

## Pre-change scan (Claude, 2026-10-24, all history to `f10ad70`)

- **None found:**
  - secret patterns: cloud keys, private keys, tokens, database URLs;
  - holdings tickers, dollar amounts, account numbers, BSB/TFN/ABN;
  - member data or balances;
  - licensed data: no source data has been ingested.
- **Becomes public:**
  - the commit author email;
  - the name "MacDonald Family SMSF" and the fact that HIO serves it;
  - the fund's broad objective, as described in the charter;
  - the `macsmsf` commit ids in the documents. The `macsmsf` repository itself stays private.
- The owner was told this before the change.

## Standing consequences

- **Every future commit is published.** The rights standard already forbids licensed data in a
  published artefact unless its rights record allows it. In a public repository, this applies
  to the repository itself.
- S1a stays synthetic-fixture-only, so S1a adds no source data.
- **S1b must not commit raw or derived source data here** without rights that allow public
  redistribution. Its receipts belong in the (future) bucket, not in git.
- **Secrets** were already never permitted in files (`AGENTS.md`). That rule now carries
  public exposure.

## What this record does NOT do

- It does not make `macsmsf` or any `macsmsf` branch public.
- It does not make a ChatGPT review an independent review under §6. Collaborator input stays
  advice until the owner adopts it.
- It changes no approval, acceptance or authorisation.
