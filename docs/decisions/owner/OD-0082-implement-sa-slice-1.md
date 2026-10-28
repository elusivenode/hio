---
id: OD-0082
title: "Owner authorises solution-architect slice 1 as proposed at 42b0480 (accepting HTTPS for the architect's commands and its reading its own login); implemented and tested: boundary probe ALL PASS, three leak-free cases run twice, all acceptance criteria met; acceptance of the pilot is a separate owner act"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-sa-slice-1.md (typed by the owner, verbatim)
  sha256: 93935993a04867fbc9c325c2c755919542bc9300cd9b8490a94676782ef8804e
  date: 2026-10-28
  quote: "yes, implement slice 1 as proposed at 42b0480"
applies_to:
  - path: docs/decisions/sa-slice-1-proposal.md
    revision: 42b0480   # the authorised proposal (blob 8a5cea15)
  - path: docs/agents/solution-architect/ (on branch impl/sa-slice-1)
    revision: self
  - path: ~/.hio-runs/bin/hiomux (outside the repository)
    revision: "sha256 b5e341bba090fa3b78edcbd57edac3babebc17825cb917d243becc93c1c84208"
  - path: ~/.hio-runs/PROTOCOL.md (outside the repository)
    revision: "sha256 13e60010fc2a0c8e08b7905ba36d0bfad54a99351c99eaf38493ff83ff1bc8af"
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], ods: [OD-0072, OD-0073, OD-0077, OD-0081]}
---

# OD-0082: solution-architect slice 1

## Owner action (verbatim in the source file)

"yes, implement slice 1 as proposed at 42b0480". By the question it answered, this also accepts gap G-a: HTTPS is
open for the architect's commands, and it can read its own login. It also requires stopping if the architect's
reads of the home folder and the reviewer's transcripts could not be blocked. They could be (§Results).

The owner then logged the architect's own Codex home in through the browser. Device-code sign-in was off for the
account, and Claude advised against enabling it.

## What was built

| Proposal item | Delivered |
|---|---|
| S1 identity v0.1 | `docs/agents/solution-architect/identity.md`, passed as `developer_instructions` and versioned by blob |
| S2 manifest v0.1 | `context-manifest.yaml`: nine existing records, 90 kB budget; MAP and findings read from `proposal/harness-0.9`, marked proposed. Live bundle 75 kB |
| S3 schema | `assessment.schema.yaml`. **Deviation:** YAML, not `.json`, because `check_repo.py` admits `.json` only as synthetic fixtures. hiomux converts it for `--output-schema` |
| S4 hiomux `sa` mode | `hiomux sa pane`, `sa ask`, `sa assess`, `sa eval`, `sa probe`. Each session gets a fresh full clone at the revision; the CLI is pinned; the run fails closed on any mismatch |
| S5 consultation log | `<run>/sa/consultations.jsonl` (11 entries in this run) |
| S6 three cases | `evals/case-{1,2,3}.yaml` with separate rubrics. Packages are built by `git archive` plus named extras, and scanned for later commits, later ODs and forbidden phrases |
| P3 separate CODEX_HOME | `~/.hio-runs/sa-codex-home`, with its own login |
| P4 home-folder read block | the profile denies reading file contents anywhere in the home folder except the session directory and SA_HOME (metadata still resolves) |
| P5 pins | `codex-cli 0.164.0`, `gpt-6.1-sol`, `high` |

**Found and fixed during implementation:**
- `hashlib` was not imported.
- The leak scan's definition of "later" had to be by commit time: old review commits imported byte-identically
  are cited legitimately.
- Interactive Codex needs a memories database. It is now writable in SA_HOME and wiped before every session.
- Codex 0.164 decides folder trust from `config.toml`, so hiomux writes that file with one trusted checkout; the
  architect cannot write it.
- `sa pane` recreates the `workers` window if it is missing.

## Results against the acceptance criteria (§4 of the proposal)

1. **Boundary probe: ALL PASS** (`sa probe`).
   - **Blocked:** reads of MACSMSF, `~/.ssh`, the `gh` config, the keychain (exit 44), `~/.claude`, the reviewer's
     `~/.codex/sessions`, other runs, `~/Documents` and Claude's scratch space; writes to the checkout, both
     `config.toml` files and anything else; SSH.
   - **Allowed:** reads of its own checkout, writes to its own `out/`.
   - **Model reads of four canaries:** no leak.
   - A local check also showed that your main `~/.codex/auth.json` and your shell history are unreadable.
2. **Settings:** every run showed `gpt-6.1-sol`/`high`/`danger-full-access` with no auto-loaded `AGENTS.md`,
   including the interactive pane.
3. **Formal output:** all six evaluation answers are schema-valid.
4. **Cases:** three cases, two runs each, every package leak-free. Pre-scores 14, 13 and 14 out of 14; one
   substantive divergence, in case 2
   (`docs/agents/solution-architect/evals/results-2026-10-28.md`).
5. **Logging:** every call is logged, and the consultations are summarised to the owner in Claude's report.
6. **Reversible:** delete the `sa` section of hiomux and `docs/agents/solution-architect/`; no harness, Codex
   review path or task record depends on them.

**No stop condition fired.**

## Not approved

- **Acceptance of the pilot** and any wider use: separate owner acts.
- **The case-2 divergence:** the owner may want the identity to weigh independent authentication of external
  data more heavily; that would be identity v0.2, an owner decision.
- **Harness-0.9 Phase A** is unchanged (not approved). The architect reads MAP and findings from the proposal
  branch as proposed material.

## Corrections (append-only)

None.
