---
id: HIO-FINDINGS-INDEX
title: Findings index (findings, dead ends and settled assessments, one line each)
status: proposed   # seed for harness-0.9 H2 (OD-0068, OD-0070), revision 3 (Appendix A2); no authority. Every line cites its source; the source wins
owner: owner (approves Settled lines at distil); any agent appends to the Inbox
last_reviewed: 2026-10-28
---

# Findings index

> **Navigation only.** Before deriving something non-trivial, `grep` this file and say what you
> found. **Settled** lines (rank 5) were accepted by the owner at a distil. **Inbox** lines
> (rank 6) are claims, not facts. Each line cites repository evidence or a reproducible fact;
> "(branch …)" marks evidence not yet on `main`. Experiment results belong in
> `registers/experiments.yaml`, not here (point to them; never restate them). Tag a line
> `[rediscovery]` when re-deriving it cost real time. A line contradicted by newer evidence is
> marked `superseded by …` or `flagged: …`, never deleted; lines describe and never govern a later
> implementation revision (operating model §4.1, proposed).
>
> Format: `- [area] the finding. Source: <path:line, commit, test, record or "reproducible">. Applies to: <revision or component, where material>.`

## Settled

_(None yet. Every line below is an Inbox candidate for the first distil.)_

## Inbox

### Repository and CI mechanics
- [repo] A factor spec file must be named `<factor_id>.yaml`: the YAML check compares the file stem with `identity.factor_id`. New S1b specs need distinct factor ids. Source: `tools/check_repo.py:163`.
- [repo] Data files (`.csv .json .jsonl .xml .txt .tsv`) must live under `tests/fixtures/synthetic/` with `SYNTHETIC` on line 1; the repository is public. Source: `tools/check_repo.py` `check_public` (l.243–260); OD-0019.
- [repo] `check_repo.py | tail` returns `tail`'s exit status, so a chained `&& git commit` runs even when the check fails. Test the exit code of `check_repo.py` itself (or use `set -o pipefail`). Source: reproducible (shell pipeline semantics).
- [repo] YAML front-matter values containing `: ` must be quoted, or the front matter does not parse as a mapping and the front-matter check fails. Source: reproducible; `tools/check_repo.py` `check_frontmatter`.
- [repo] CI pins every GitHub Action by commit SHA; copy the pins from the existing workflow for any new one. Source: `.github/workflows/ci.yml`.
- [repo] CI requires an `HIO-Actor:` trailer on every non-merge commit, and the local hook does not check it. Run `uv run python tools/check_repo.py trailers origin/main HEAD` before pushing. Source: OD-0058 (the CI failure); OD-0059; operating model §6.2 step 5.7.
- [repo] [rediscovery] In zsh, `git show $REF:path` breaks when `path` starts with `r`, because `$REF:r` is a history modifier. Quote the argument: `git show "$REF:path"`. Source: reproducible.

### Releases and specs
- [releases] `spec_ref` is `factor_id@identity.version`. Editing an S1a spec either bumps its version (changing S1a release ids, whose outputs OD-0067 requires preserved) or silently changes a spec at an unchanged version. S1b releases need their own accurately versioned specs. Source: `src/hio/jobs/s1a.py:192-194`; `F-REVIEW-2026-10-25-t0009-4`; OD-0067.
- [releases] Count decimal places from the canonical string, not from a parsed `Decimal`: a parsed-then-reloaded value can lose trailing zeros. Source: `src/hio/jobs/s1b1.py:140` `_places` (branch `impl/t0009-shared-receipt-and-storage`, not on `main`).
- [releases] One shared RBA F1 receipt serves `rba.cash_rate` and `rba.cash_rate_tri`. The receipt belongs to publication `rba.f1`, and each series carries its own `dataset_id`. A shared receipt with no link must not fall back to its publication id as the rights subject. Source: OD-0065; `F-REVIEW-2026-10-25-t0009-1`. Applies to: T-0009 at `ce0c3b5` (F-1 open).

### Rights and sources
- [rights] Every source permission is `unverified`; the genuine rights register refuses every operation. A design direction such as OD-0064 (F1 file retention) is not a rights verification. Source: `registers/sources.yaml`; OD-0013; OD-0064. Applies to: all sources as of `16ea0c6`.
- [rights] A caller-supplied link record is not trustworthy evidence of which dataset a series belongs to: a substituted link authorised an unrelated dataset. Pin the series-to-dataset mapping in code. Source: `F-REVIEW-2026-10-25-t0009-2`.
- [sources] The US observation calendar can be derived from verified NY Fed publication dates, which avoids a SIFMA dependency. Source: `registers/tasks/T-0009-s1b1-cash-capture-and-research.md` §2 item 7 (a design intent, not yet verified).

### Review practice (useful to Codex and Claude)
- [review] Two probes found the T-0009 high findings: allow the publication id but deny the true dataset; substitute a single-owner link with the true dataset denied. Reuse both as standing adversarial tests for any change to the rights subject. Source: `reviews/records/REVIEW-2026-10-25-t0009-1.md` F-1, F-2.
- [review] A silent `continue` on a missing input in a comparison loop dropped periods without trace (AUD: 9 periods, 8 rows; USD: 13 periods, 10 rows). Count every omission and give its reason. Source: `F-REVIEW-2026-10-25-t0009-3`.
- [review] In REVIEW-2026-10-25-t0009-1, passing synthetic tests covered the happy paths; all three high findings were untested negative cases (missing link, substituted link, missing key). Source: `reviews/records/REVIEW-2026-10-25-t0009-1.md` verdict.

### Harness
- [harness] Assigning and receiving one review (`REVIEW-2026-10-25-t0009-1`) took two ODs, two transcripts, a tag, a receipt branch, index rows and five commits and merges, every step mechanical. Source: OD-0066; OD-0067; commits `c0588d9`..`eb19ef7`.
- [harness] Authority records left on an unmerged implementation branch make `main` contradict itself: at `eb19ef7`, `STATUS.md` did not mention T-0009 while OD-0067 authorised its remediation. Resolved for T-0009 by OD-0069 (merge `16ea0c6`); the failure mode remains possible (harness-0.9 H7). Source: `STATUS.md` and OD-0067 at `eb19ef7`; OD-0069.
- [harness] The HIO-ADR-0012 findings read three ways on `main` at `eb19ef7`: "3 findings open" (`STATUS.md` l.39), "technically verified closed" (`STATUS.md` l.47; OD-0054), and `remediation_claimed` for -1 and -3 (`reviews/README.md`), because `VERIFY-2026-10-25-adr0012-1` was disposed unreceived. Read OD-0054 before relying on any of them. Source: OD-0053; OD-0054; OD-0057. Applies to: `main` at `16ea0c6` (`STATUS.md` now states the discrepancy).
- [harness] A same-vendor sub-agent standing in for Codex is an unverified dry run, and never satisfies an independent-review gate. Sub-agents return text and cannot write report files; the receiver transcribes. Source: operating model §10; `reviews/reports/REPORT-2026-10-28-harness-0.9-fable-dryrun-1.md`.
