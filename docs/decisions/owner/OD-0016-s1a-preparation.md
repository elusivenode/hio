---
id: OD-0016
title: "Owner instruction: adopt the S1a-preparation advice (align the execution documents); draft, not grant, the S1a authorisation; push the staging branch"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/documentation-agent
owner_statement:
  source: hio/docs/history/2026-10-24-owner-s1a-preparation.md (pasted advice plus the owner's own words, verbatim)
  sha256: 96fc111d2caedfa151cd31024f7cfc3ad4bf6c758cb611f530e223341a11d3cb
  date: 2026-10-24
  quote: "once done, please push our branch to the remote"
applies_to:
  - path: hio/
    revision: 81793f7
related: {adrs: [HIO-ADR-0001, HIO-ADR-0008, HIO-ADR-0010], tasks: [T-0005, T-0007], findings: []}
---

# OD-0016: S1a preparation

## Owner action, and how it was read

The owner pasted collaborator advice and added: "once done, please push our branch to the
remote". The words don't adopt the advice explicitly. Claude reads "once done" as instructing the
advice's **executable parts within the standing limits**, and records that reading here so the
owner can correct it:

1. **Align the execution documents with HIO-ADR-0010 rev 3** (advice item 1):
   - the roadmap, the implementation plan and T-0005 describe S1a and S1b separately, and T-0002
     gates S1b only;
   - operating model §8.1: the obsolete "every proposed ADR remain proposed" status sentence
     (a status-only edit, logged in the changelog);
   - the README: the migration preserves history (§8.1), not a `git mv`.
2. **T-0007 criteria 1–2:** add the advice's point that a review run in a continuing chat is not
   the §10 fresh-session test (a later edit on the accepted card).
3. **Draft the S1a authorisation** (advice item 2) as a `draft` OD record with no authority.
   **Granting it is the owner's separate action.**
4. **Push `docs/hio-a01-baseline` to `origin`** once the above is committed.

## Scope and exclusions

- **Not done:** S1a authorisation or any S1a work; repository creation or migration; any change
  to an approval, verification or task status.
- **Not done:** confirming OD-0010's cross-lineage review mechanics. That is the owner's action,
  and it is flagged for decision.
- **Advice item 3** (T-0002/T-0003 research in parallel; the T-0004 review) is already
  authorised (OD-0009, OD-0010, OD-0013), so this record adds nothing to it.
- **No other branch is pushed.** That includes `macsmsf` `main` and `docs/hio-001-boundary-c1`.

## What this record does NOT do

- It does not authorise S1a or S1b, the hio repository, or a migration.
- It does not approve the roadmap, the implementation plan or T-0005. They stay
  recommendations or proposals.
- It does not re-approve the operating model. The §8.1 edit is status-only. The approved content
  stays at blob `e3114bd188ad` (OD-0012).
