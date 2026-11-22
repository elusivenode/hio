---
id: OD-0218
title: "Owner authorises drafting, as proposed and without implementation, one factor-programme task card and a one-page sequence, based on ChatGPT's architecture guidance with Claude's named changes"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-factor-programme-draft.md (owner's messages, verbatim, with Claude's question)
  sha256: 74ccc4396f145b23b784418c141e02b06a2b0cc00b433982eb79702c27704d98
  date: 2026-11-22
  quote: "Y"
base_revision: 6d7535a290107a899436bfa912996c7644555abc
related: {adrs: [], tasks: [T-0024], findings: [], ods: [OD-0139, OD-0184, OD-0199, OD-0210, OD-0213, OD-0217]}
---

# OD-0218: draft the factor-programme card and sequence

## Owner action

The owner asked Claude for a brief to ChatGPT on HIO's state, progress and near-term plans, then supplied ChatGPT's reply by file path. Claude summarised it, named five changes and asked one question. The owner answered "Y".

**Authorised:**

1. **One task card,** `registers/tasks/T-0024-factor-programme.md`, at `status: proposed`.
2. **A one-page sequence,** `docs/decisions/factor-programme-sequence-proposal.md`, at `status: proposed`.
3. **This record,** one solution-architect consultation on the sequencing, and a pull request.

**Also recorded:** the brief to ChatGPT was drafted by Claude and sent by the owner. It held no value from a licensed series.

## The advice, and its standing

ChatGPT's reply is kept verbatim as `docs/history/2026-11-22-chatgpt-factor-programme-guidance.md` (sha256 `f43eddc783b1de70c6e7beba8f7146d798faa0f532acecfa23ddf758d99b615d`). It is collaborator advice (AGENTS.md rule 4). The owner adopted it only as the basis for these two drafts, with the changes Claude named in its question. Nothing else in it is adopted: not its sequence, its tiers, its milestones or its notes for Codex.

## What this record does NOT do

It authorises no code, data fetch, source permission, purchase, backup, spec adoption, review assignment or build. It does not authorise the card: T-0024 stays `proposed` until the owner authorises it. It accepts nothing and approves nothing.

## Corrections (append-only)
