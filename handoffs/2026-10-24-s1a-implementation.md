---
id: HANDOFF-2026-10-24-s1a-implementation
date: 2026-10-24
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code session)
work_status: in_review (submitted; review not yet assigned)
base_revision: 9370256bac6ba2193b09c342170bd11ca57b70a3
head_revision: self       # resolve: git log -n1 --format=%H -- handoffs/2026-10-24-s1a-implementation.md
work_commits: [f71852d, cfd60ad, 583db8e, 426f5b6, 8e5fff0, af5f1ee, 0f6247d]
work_card: T-0005 (S1a)
---

# Handoff: S1a implemented and submitted for review

> A dated snapshot. **Not a decision.** The evidence is in
> [`docs/evidence/S1A-evidence-package.md`](../docs/evidence/S1A-evidence-package.md).

## Changed files

All new apart from these:
- **New code and tooling:**
  - `src/hio/` (contracts, reference, storage, marketdata, library, rights, publish, jobs);
  - `tests/` (150 tests, synthetic fixtures);
  - `tools/check_repo.py`, `tools/install-hooks.sh`;
  - `.github/workflows/ci.yml`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.python-version`.
- **New documents:**
  - `docs/engineering/repository-safeguards.md`;
  - the evidence package;
  - OD-0020 and its history file.
- **Edited:** `STATUS.md`, T-0005, `reviews/README.md` (a candidate row only), the OD and
  history indexes.
- **No approved document changed.**

## Done

S1a in OD-0020's order, in seven small commits. CI is green on GitHub at `0f6247d`.

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| All tests pass, network blocked | `uv run pytest` | 150 passed |
| Harness checks | `uv run python tools/check_repo.py` | PASS |
| CI | GitHub Actions run for `0f6247d` | harness ✓, tests ✓ |
| End to end | `python -m hio.jobs.s1a … --cutoff 2026-01-29T00:00:00Z` | 34 captures, 14 no-ops, 49 vintages, 4 releases, no absent periods |

## Found and fixed while building

- **A revert to earlier bytes was lost.** Content addressing deduplicated it. Captures are now
  per event.
- **The AUD cash series stopped one period early.** Each period needs only the rates fixed
  before its end.
- **A well-formed empty receipt was quarantined.** It is now valid: nothing has been
  released yet.
- **`ruff format` reformatted a historical Markdown handoff.** Reverted before commit; ruff is
  now limited to Python.

## Known limitations and not verified

See the evidence package, especially the ten interpretations and limitation 8 (no CI egress
firewall).

## Open findings

None recorded.

## Conflicts found between documents

None. One open standard question: OBS-INV-007 Case B `reconstructed` (interpretation 1).

## NOT approved by this session

- S1a acceptance.
- The review assignment.
- The §10 fresh-session test.
- S1b; any source permission; vendor contact; any `macsmsf` change; the T-0004 merge.

## Next authorised action

None for the author until review findings exist.

**Owner:**
- assign the Codex review, using the candidate row in `reviews/README.md`;
- run the §10 fresh-session test in a session with no prior chat history.
