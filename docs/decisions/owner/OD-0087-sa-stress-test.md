---
id: OD-0087
title: "Owner adopts a six-case stress test of the solution architect (twelve runs, read-only pilot), with four corrections; ChatGPT writes the cases and sealed expected findings; Claude packages, runs and checks mechanically only; no grading, tuning or promotion by Claude"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-adopt-sa-stress-test.md (owner's messages, verbatim)
  sha256: e983fb9816128128ac4fa30c8670ec9fb19b7f79e681e10764f3e699341e619d
  date: 2026-10-28
  quote: "Claude is authorised to prepare the evaluation packages and run the twelve assessments within the existing read-only Solution Architect pilot. Claude may perform mechanical checks but must not grade architectural judgement."
base_revision: 1877f77
applies_to:
  - path: docs/agents/solution-architect/evals/ (new case files, proposed, when supplied)
    revision: "to be recorded per case in the corrections below"
related: {adrs: [], tasks: [], findings: [], ods: [OD-0081, OD-0082, OD-0083, OD-0084, OD-0085]}
---

# OD-0087: the solution-architect stress test

## Provenance

1. The owner pasted a ChatGPT draft: six adversarial cases on six dimensions (strategic reconstruction,
   economic validity, architectural proportionality, authority conflict, adversarial collaboration, practical
   prioritisation), hidden expected findings, full responses kept, critical failures listed apart from
   weaknesses, and agreement with ChatGPT not counted as correctness. Claude treated it as advice (AGENTS.md
   rule 4).
2. At the owner's invitation (message 4), Claude proposed modifications for ChatGPT: separate roles; correctness
   scored apart from similarity of approach; pre-registered, sealed grading; every case run as a package at a
   fixed cutoff; two runs per case; no tuning; stop conditions.
3. The owner adopted the plan with four corrections (message 5, verbatim in the source file).

## What is authorised

- **Prepare the evaluation packages:** case files under `docs/agents/solution-architect/evals/` (`proposed`),
  holding the case questions and evidence lists that ChatGPT supplies, and leak-checked packages built by
  `hiomux sa eval`.
- **Run twelve assessments:** six cases, two runs each, within the existing read-only pilot (`hiomux sa`,
  `gpt-6.1-sol`/`high`, identity v0.2).
- **Mechanical checks:**
  - model, effort, sandbox and CLI version;
  - `AGENTS.md` not auto-loaded;
  - the leak scan;
  - schema validity;
  - citations that resolve in the package;
  - stability between the two runs;
  - seal hashes.
- **Return** the complete responses and the mechanical evidence for independent grading.

## Rules (the owner's corrections and limits)

1. **Questions and findings are kept apart.** ChatGPT prepares the case questions and the sealed expected
   findings separately. The owner keeps the findings outside the repository. Claude receives only their
   sha256 hashes, which are recorded here before the first run.
2. **Historical cutoffs follow the evidence** legitimately available before each decision, not automatically
   the parent commit or a commit timestamp. In the tool, that is a cutoff tree plus named extra files at named
   revisions. The automatic leak scan stays a floor, not the definition.
3. **Severity is assessed by material consequence,** not only by matching the expected findings.
4. **A historical owner decision establishes authority.** It is not automatically proof of technical
   optimality.
5. **Claude does not grade architectural judgement.**
6. **No identity tuning** in this round.
7. **Unchanged:** the approved standards, Codex's review path, and the operational implementation scope.
8. **Stop and report on:** failed isolation, a failed boundary check, a model mismatch, or a seal that fails
   its integrity check.
9. **Promotion waits for independent grading.** No recommendation to promote the architect into regular use is
   made before that grading.

## Preparation done at adoption

- **Tool hashes:** hiomux `e659b0bc…` and PROTOCOL.md `b4e81ff4…`, as OD-0085 records them. `codex-cli 0.164.0`.
- **`hiomux sa probe` (run `20261028T081310Z-d55d`): ALL PASS.**
  - 15 boundary checks.
  - The model read four canaries and leaked none.
  - Settings: `gpt-6.1-sol`, `high`, `AGENTS.md` not auto-loaded.

## Awaited from the owner

- the six case questions, with each case's evidence list and cutoff;
- the six sha256 hashes of the sealed expected findings.

## Not authorised

- grading by Claude;
- identity changes;
- promoting the architect into regular use;
- any change to hiomux's code, Codex's review path or approved standards;
- any live operation.

## Corrections (append-only)
