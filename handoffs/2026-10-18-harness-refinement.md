---
id: HANDOFF-2026-10-18-harness-refinement
date: 2026-10-18
actor: claude/documentation-agent (Claude Opus 5.5, Claude Code session)
work_status: proposed     # T-0006 is submitted_for_review; its authorisation OD-0001 is unconfirmed
base_revision: 85ef0fa8821e5f538b739c5fe000f3f63d3bfac1
head_revision: "the commit on docs/hio-a01-baseline whose message begins 'Refine the HIO harness'; see git log"
work_card: T-0006
---

# Handoff: harness refinement (harness-0.1 → harness-0.2)

> A dated snapshot. Not a decision.

## Changed files (all under `hio/`)

**New:**
- `docs/decisions/owner/{README.md, OD-0001-authorise-harness-refinement.md}`;
- `reviews/README.md`, `reviews/records/README.md`;
- `templates/owner-decision.md`;
- `registers/tasks/T-0006-harness-refinement.md`;
- `docs/history/2026-10-18-directive-harness-refinement.md` (the brief, verbatim);
- this handoff.

**Edited:**
- `AGENTS.md`;
- `STATUS.md`;
- `README.md`;
- `docs/harness/operating-model.md`;
- `docs/harness/worked-example.md`;
- `docs/decisions/{README.md, template.md, HIO-ADR-0008-…}` (content only; **status unchanged**);
- `docs/charter.md` (one anchor);
- `docs/implementation-plan.md` (one wording line);
- `docs/history/README.md`;
- `templates/{task-card.md, handoff.md, review-record.md}`;
- `registers/tasks/T-0001…T-0005` (`approved:` → `authorised_by:` / `base_revision:`);
- `.claude/skills/hio-session/SKILL.md`.

**No file outside `hio/` changed.**

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| The base matches the owner's stated baseline | `git rev-parse HEAD` before editing | `85ef0fa8821e5f538b739c5fe000f3f63d3bfac1` |
| YAML and front matter parse; relative links resolve; STATUS ≤150 lines | a one-off check script (not committed) | see the commit message |
| No ADR status changed | `git diff 85ef0fa -- hio/docs/decisions/HIO-ADR-*` shows no `status:` line change | see the commit message |
| No file outside `hio/` changed | `git diff --stat 85ef0fa -- . ':!hio'` | empty |
| Cold-start tests | Claude sub-agent dry runs (**not** independent; **not** Codex) | recorded below once run |

## Known limitations and not verified

- `HIO-Actor` trailer checks are a convention. Nothing enforces them until S1 CI exists.
- **The cold-start tests have not been run with genuinely independent sessions.** Any Claude
  sub-agent run is an *unverified dry run*. The real Codex run is pending.

## Open findings

None recorded. No independent review has taken place.

## Assumptions made

- The owner's chat instruction (supplying the brief) is treated as the request to execute
  T-0006. It is transcribed as OD-0001, which stays `proposed` until the owner confirms it.

## Conflicts found between documents

- harness-0.1 used `approved` for task cards and approvals recorded inside ADRs. harness-0.2
  replaces these with `authorised` and OD records. All references were updated. Historical
  files in `docs/history/` are left verbatim.

## NOT approved by this session

- **Nothing.** OD-0001 is unconfirmed.
- T-0006 is not accepted.
- No ADR, standard or spec is approved.
- HIO-S1 is not authorised.
- Codex has not reviewed or endorsed anything.

## Next authorised action

**None is authorised.** The decisions needed:
1. The owner confirms or rejects OD-0001.
2. The owner requests the Codex A01 review (proposal in `reviews/README.md`, under *Pending
   review requests*).
