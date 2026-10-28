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

1. **2026-10-28, seals and cases received (before any run).**
   - **Owner's instruction** (pasted, in the owner's voice): "Proceed with the OD-0087 Solution Architect stress
     test using the attached six-case YAML archive and the six separately supplied SHA-256 seal hashes. Use the
     exact case cutoffs. … Do not receive or inspect the owner-only grading pack."
   - **Seal hashes of the owner-held expected findings**, as the owner supplied them. Claude has not received
     the findings files.

     | Case | sha256 of the sealed findings |
     |---|---|
     | stress-1 | `b7d793cae43ac880fab5baf38e59153692c4f011c06b311ad2303d335027df85` |
     | stress-2 | `412a9cec1f83c23924961ad130aee31c675febbf6189e00e4b1982588ceb4caa` |
     | stress-3 | `6193982e0e38581e9f4eec8cea393f5e7e533941e7b1a2bd523a0e53edf88aa3` |
     | stress-4 | `107d490e59a0d22c262184c941e6dbe4356e5a2d231c1624d0101876cc4ecc3f` |
     | stress-5 | `256eee4ef282860b662ad268ffea7bf313e9e744b43345a80bee8d99bb7c49df` |
     | stress-6 | `d2554b7f6006705ed38c9886a372eb1499ea29258b843cb8808be9bba3806cd7` |

   - **Case archive:** `~/Downloads/hio-stress-cases-for-claude.zip`, sha256
     `2f4707c4d527cc78814f44042419b28db57ab4c085b0972bae1f6986c3242fae`. It holds exactly six files. They are
     committed byte-identical under `docs/agents/solution-architect/evals/`:
     - `stress-1.yaml` `801e7140a9e80fea55f61d8f170515127ed7aa121dbf5f1a2218a198bd1d8a43`
     - `stress-2.yaml` `5412ccd125f48715c80599e0e53ed19872fa5bd156307b27fdc27fac20204032`
     - `stress-3.yaml` `ece970a548efd7cf5a07e8331b60303768bc4f4801ccba1f696f43f1379ca145`
     - `stress-4.yaml` `077e6caf2a7f2f3da87be401cc80176f64362c558911389137e8d85f87d038a1`
     - `stress-5.yaml` `633b598659d63ce35e950496aba59274eed01d93120265043028bf59f9f2b7f9`
     - `stress-6.yaml` `585a6e984b16df9aa696e07948914aed1dfec6dc3c04d239c0f58cfb0991329d`
   - **Cutoff:** every case uses `cab174713cf4980bbb009da70bd283da864d6b9a` (main with OD-0087), used exactly as
     supplied. No case names extras, forbidden phrases or allowed later ODs.

2. **2026-10-28, twelve runs complete; responses returned for independent grading.**
   - **Probe:** `hiomux sa probe` ALL PASS immediately before the runs.
   - **Runs:** `hiomux sa eval stress-1` … `stress-6`, two runs each, 18:23–18:54 AEST, run
     `20261028T081310Z-d55d`. All 12 have status `ok`: schema-valid, with no problems. Every run applied
     `gpt-6.1-sol`/`high`, `codex-cli 0.164.0`, identity v0.2 (blob as on `main`), no auto-loaded `AGENTS.md`,
     cutoff `cab1747`, and a clean leak scan. Every run had an identical context bundle (manifest blob `e8600c1f`,
     schema blob `33caa5a3`).
   - **Network:** no run executed a network command; there was no `curl`, `wget`, URL fetch, `git` remote
     command or web-search item. `origin/main` equalled the cutoff throughout.
   - **Citations:** all cited paths exist in the package, and all cited ODs are OD-0087 or earlier. The flags
     were each resolved:
     - `a82aa0d` is quoted from `AGENTS.md`; it is a pre-migration `macsmsf` id;
     - `2df83b4` is the `proposal/harness-0.9` head, cited from `STATUS.md` and committed before the cutoff;
     - `MAP.md` and `knowledge/findings.md` are correctly named as absent;
     - three hex-like strings are decimal digits.
   - **Disclosed:** the cutoff includes OD-0087 and `STATUS.md`, so the architect could know a stress test was
     under way. It had no expected findings and nothing later.
   - **Returned:** the complete responses and mechanical evidence, ungraded, on a private claude.ai page,
     https://claude.ai/artifact/QpVsm3fXGGYPKpWaAtEApV (OD-0088). The run records stay in `~/.hio-runs`, which is
     operational evidence. Claude graded nothing and recommends nothing about promotion.

3. **2026-10-28, independent grading received.**
   - **The report:** ChatGPT's full grading, supplied by the owner as
     `~/Downloads/hio-solution-architect-independent-grading-report-2026-10-28.md`. It is recorded byte-identical as
     `docs/history/2026-10-28-chatgpt-sa-grading-report.md`, sha256
     `86f013f72bf5ee21527a814db70eebd5090f8ed4eb35f54fde11ff9f6dcb0972`.
   - **Its findings:**
     - integrity: the seals and the results-file hash (`870938d1…`) matched;
     - **12/12 pass Score A, with zero critical and zero major findings**;
     - five minor findings: case 2 runs 1 and 2, case 5 run 2, case 6 runs 1 and 2;
     - critical items stable in all six pairs;
     - Score B was High except case 6 run 2 (Medium).
   - **ChatGPT's own limits:** it did not replay the CLI sessions. The mechanical record is reported by Claude, and
     ChatGPT checked the key approved sources at the cutoff itself.
   - **Claude's cross-check:** the identity blob it quotes (`25272b1a…`) matches `main` and every run record.
   - **The report is advice.** The owner's adoption is OD-0089.
