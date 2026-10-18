---
id: HANDOFF-2026-10-18-harness-refinement
date: 2026-10-18
actor: claude/documentation-agent (Claude Opus 5.5, Claude Code session)
work_status: proposed     # T-0006 is submitted_for_review; its authorisation OD-0001 is unconfirmed
base_revision: 85ef0fa8821e5f538b739c5fe000f3f63d3bfac1
head_revision: self       # resolve: git log -n1 --format=%H -- hio/handoffs/2026-10-18-harness-refinement.md
work_commits: [72d1e56a6f2c349cdfaf645e3d2092a662d1365a]
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
| YAML and front matter parse; relative links resolve; STATUS ≤150 lines | the documentation check recorded under *Cold-start dry-run results* | `OK`; STATUS 73 lines |
| No ADR status changed | `git diff 85ef0fa -- hio/docs/decisions/HIO-ADR-*` shows no `status:` line change | see the commit message |
| No file outside `hio/` changed | `git diff --stat 85ef0fa -- . ':!hio'` | empty |
| Cold-start tests | two isolated, read-only Claude sub-agents with the §10 prompts @ 72d1e56 (**unverified dry run**: not independent, not Codex) | both answered every question correctly, with no false approval or authorisation claims; 5 distinct issues raised (one by both runs); dispositions below |

## Cold-start dry-run results (@ 72d1e56; unverified dry run)

- **Claude role:** 6/6 correct.
  - It found no approved OD, all ADRs proposed, S1 not authorised, no open findings.
  - Its next action was "owner confirms OD-0001; owner requests the review".
  - It read about 10–12k tokens.
  - **Gap:** no committed file names the head commit.
- **Reviewer role:** 7/7 correct.
  - It fixed the target from git **before** reading the handoff, and treated the handoff as
    unverified.
  - It read about 28–32k tokens: over the 25k target, under the 40k cap.
  - **Gaps raised:**
    - (a) the review request pointed at the author's handoff for its head;
    - (b) 85ef0fa has no `HIO-Actor` trailer;
    - (c) the "links resolve" check was not reproducible;
    - (d) the `docs/implementation-plan.md` edit needed checking against the "no roadmap
      changes" exclusion.
- **Dispositions:**
  - the head gap and (a): `head_revision: self` convention; review targets are SHAs fixed at
    go-ahead (operating model §3, §6.1; handoff template; review index);
  - (b): the trailer convention is stated to start at 72d1e56;
  - (c): the check procedure is recorded below;
  - (d): the edit is one sentence changing "approved task card" to "authorised task card (an OD
    record)". It is a harness-vocabulary change, not a roadmap or slice-content change. **Owner
    to confirm this reading.**

**Reproducible documentation check** (run from the repository root with any Python 3 with
PyYAML):

```python
import re, pathlib, yaml
root = pathlib.Path("hio"); bad = []
slug = lambda h: re.sub(r"[^\w\- ]", "", h.strip().lower()).replace(" ", "-")
for p in root.rglob("*.yaml"):
    yaml.safe_load(p.read_text())
for p in root.rglob("*.md"):
    t = p.read_text()
    if "history" in p.parts and p.name != "README.md":
        continue
    for m in re.finditer(r"\]\(([^)#\s]*)(?:#([^)\s]+))?\)", t):
        tgt, anc = m.group(1), m.group(2)
        if tgt.startswith("http"):
            continue
        f = (p.parent / tgt).resolve() if tgt else p.resolve()
        if not f.exists():
            bad.append(f"{p}->{tgt}"); continue
        if anc and f.suffix == ".md" and anc not in [slug(re.sub(r"^#+\s*", "", l)) for l in f.read_text().splitlines() if l.startswith("#")]:
            bad.append(f"{p}->{tgt}#{anc}")
print(bad or "OK", len((root / "STATUS.md").read_text().splitlines()))
```

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
