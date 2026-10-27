---
id: HIO-FINDINGS-INDEX
title: Findings index (findings, dead ends and settled assessments, one line each)
status: proposed   # seed draft for harness-0.9 H2 (OD-0068); no authority. Every line cites its source; the source wins
owner: owner (approves Settled lines at distil); any agent appends to the Inbox
last_reviewed: 2026-10-28
---

# Findings index

> **Navigation only.** Before deriving something non-trivial, `grep` this file and say what you
> found. **Settled** lines were accepted by the owner at a distil. **Inbox** lines are claims, not
> facts. Format: `- [area] the finding. Source: <path, commit, test or record>.`

## Settled

_(None yet. The seed lines below are all Inbox candidates for the first distil.)_

## Inbox

### Repository and CI mechanics
- [repo] A factor spec file must be named `<factor_id>.yaml`: `tools/check_repo.py` compares the file stem with `identity.factor_id`, so S1b specs need distinct factor ids. Source: `tools/check_repo.py` (yaml check); handover 2026-10-25 §0.
- [repo] Data files (`.csv .json .jsonl .xml .txt .tsv`) must live under `tests/fixtures/synthetic/` with `SYNTHETIC` on line 1; the repository is public. Source: `tools/check_repo.py` `check_public`; OD-0019.
- [repo] `uv run python tools/check_repo.py | tail` does not stop a chained `git commit` when the check fails; test the exit code of `check_repo.py` itself. Cost one commit with a front-matter error. Source: handover 2026-10-25 §7.
- [repo] YAML front-matter values containing `: ` must be quoted or the front-matter check fails. Source: handover 2026-10-25 §7.
- [repo] CI pins every GitHub Action by commit SHA; copy the pins from `.github/workflows/ci.yml` for any new workflow. Source: `.github/workflows/ci.yml`.
- [repo] CI requires an `HIO-Actor:` trailer on every non-merge commit; the local hook does not check it. Run `uv run python tools/check_repo.py trailers origin/main HEAD` before pushing. Source: OD-0058 (the CI failure), OD-0059.
- [repo] In zsh, `git show $REF:path` breaks when the path starts with `r` (`$REF:r` is a history modifier); quote the argument. Source: session 2026-10-28.

### Releases and specs
- [releases] Changing an S1a spec (`cash.aud.overnight.yaml`, `cash.usd.overnight.yaml`) changes S1a `spec_ref` strings and therefore the S1a release ids accepted with S1a (OD-0042); OD-0067 requires the S1a hashes preserved. Add new specs rather than editing these. Source: handover 2026-10-25 §0; OD-0042; OD-0067.
- [releases] Decimal places must be counted from the canonical string, not from a parsed `Decimal`: a parsed-then-reloaded value lost trailing zeros (`_places()` bug, fixed). Source: T-0009 handover; `98205d5`.
- [releases] One shared RBA F1 receipt serves `rba.cash_rate` and `rba.cash_rate_tri`; the receipt belongs to publication `rba.f1` and each series carries its own `dataset_id`. A receipt with no link must not fall back to its publication id as the rights subject. Source: OD-0065; `F-REVIEW-2026-10-25-t0009-1`.

### Rights and sources
- [rights] Every source permission is `unverified`; the genuine rights register refuses every operation. A design direction (OD-0064, F1 file retention) is not a rights verification. Source: OD-0013; OD-0064.
- [rights] A link record supplied by the caller is not trustworthy evidence of which dataset a series belongs to: a substituted link authorised an unrelated dataset. Pin the series-to-dataset mapping in code. Source: `F-REVIEW-2026-10-25-t0009-2`.
- [sources] The US observation calendar can be derived from verified NY Fed publication dates, which avoids a SIFMA dependency. Source: T-0009 card §2 item 7.

### Review practice (useful to Codex and Claude)
- [review] Codex's probes that found F-1 and F-2 were "allow the publication id, deny the true dataset" and "substitute a single-owner link with the true dataset denied". Use both as standing adversarial tests for any rights-subject change. Source: `REVIEW-2026-10-25-t0009-1`.
- [review] Silent `continue` on a missing input in a comparison loop dropped periods without trace (AUD 9 periods gave 8 rows; USD 13 gave 10). Every omission should be counted and given a reason. Source: `F-REVIEW-2026-10-25-t0009-3`.
- [review] Passing synthetic tests show only the tested paths; reviews have repeatedly found defects in untested negative cases (missing key, missing link, substituted link). Source: `REVIEW-2026-10-25-t0009-1` verdict.

### Harness
- [harness] A receipt of two review files took a full session by hand (OD-0066, OD-0067; five commits and merges); every step is mechanical. Source: harness-0.9 proposal §1.
- [harness] Authority records left on an unmerged implementation branch make `main` contradict itself: `STATUS.md` on `main` does not know T-0009 exists. Source: OD-0062 to OD-0065 on `impl/t0009-shared-receipt-and-storage`; `STATUS.md` at `eb19ef7`.
- [harness] The finding state of `F-REVIEW-2026-10-25-adr0012-1` and `-3` reads `remediation_claimed` in `reviews/README.md` but "technically verified closed" in OD-0054, because `VERIFY-2026-10-25-adr0012-1` was disposed unreceived (OD-0057). Read OD-0054 before relying on the index row. Source: OD-0053, OD-0054, OD-0057.
- [harness] A same-vendor sub-agent standing in for Codex is an unverified dry run; it never satisfies an independent-review gate. Source: operating model §10.
- [tooling] Bash calls in Claude Code occasionally fail with "classifier gave no verdict"; retry the exact call once. Source: handover 2026-10-25 §7.
