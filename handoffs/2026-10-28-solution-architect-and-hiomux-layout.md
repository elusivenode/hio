---
id: HANDOFF-2026-10-28-solution-architect-and-hiomux-layout
date: 2026-10-28
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code; hiomux orchestrator, run 20261028T043057Z-e4d8; outside tmux since OD-0085)
work_status: "solution-architect pilot accepted (OD-0083), identity v0.2 approved (OD-0084); hiomux layout changed (OD-0085)"
base_revision: a83100fb17df   # main after OD-0080 and the previous handoff (handoffs/2026-10-28-t0009-acceptance-and-knowledge.md)
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/2026-10-28-solution-architect-and-hiomux-layout.md
work_commits:
  - 934aded   # main: OD-0081 and the slice-1 proposal (42b0480)
  - 8e867da   # main: slice 1 merged, OD-0082
  - e549af1   # main: OD-0083, pilot accepted, v0.2 results
  - 38c40e2   # main: identity v0.2 approved, OD-0084
work_card: none   # owner-instructed tooling work (OD-0081 to OD-0085); no task card
stream: solution-architect-and-hiomux   # proposed H4 field (harness-0.9; not yet in the template)
---

# Handoff: the solution architect, and hiomux's layout

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

**Role:** implementation agent and hiomux orchestrator. **Work status:** the pilot is accepted and identity v0.2
is approved. None of it is a harness change.

## Changed files

| Where | Change |
|---|---|
| `docs/agents/solution-architect/` | identity v0.2 (approved, OD-0084); context manifest and assessment schema (proposed); three regression cases with rubrics; results file |
| `docs/decisions/` | `sa-slice-1-proposal.md`; OD-0081 to OD-0085 with verbatim `docs/history/` files; index rows; `STATUS.md` |
| Outside the repository | `~/.hio-runs/bin/hiomux` (`sa` mode, workers-only session, `view` window, feeds), `PROTOCOL.md`, `~/.hio-runs/sa-codex-home` (the architect's own login), `~/.warp/launch_configurations/hio-workers.yaml`. Hashes are in OD-0085 |

## Done

1. **Assessed the ChatGPT architect spec.**
   - Recommended a Codex CLI architect instead of a Responses API service.
   - The owner adopted the revised direction with seven boundaries (OD-0081).
2. **Verified the ground before proposing.**
   - Harness authority: no amendment needed.
   - The `gpt-6.1-sol`/`high` model.
   - Codex's own read-only sandbox reads the whole disk, and Codex loads `AGENTS.md` by itself.
3. **Slice 1, built and tested (OD-0082).** The boundary probe passed in full, including reads of MACSMSF,
   credentials, the keychain and the reviewer's transcripts. The three leak-free cases were run twice each.
4. **Pilot accepted; identity v0.2 drafted and approved (OD-0083, OD-0084).** v0.2 adds "Independence of
   evidence": case 2 now defers closure until independent support, and cases 1 and 3 are unchanged.
5. **Layout (OD-0085).**
   - The orchestrator runs outside tmux.
   - The owner watches a two-pane, read-only `view` window in a separate Warp window: the architect feed and the
     workers-and-Codex feed.

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| Architect boundary | `hiomux sa probe`: local checks, then model reads of canaries | ALL PASS |
| Settings applied | session records, every call | `gpt-6.1-sol`/`high`/`danger-full-access`; no auto-loaded `AGENTS.md` |
| Regression | `hiomux sa eval case-1..3`, twice each, on v0.1 and v0.2 | citations valid; pre-scores and divergences in `evals/results-2026-10-28.md` |
| Feeds | a dummy worker; one real `sa ask` | tagged lines in `workers.log`; the consultation in `architect.log` |
| Repository checks | `check_repo.py`; trailers, each commit | PASS |

## Known limitations and not verified

- **v0.2's evidence** includes the case it was tuned on; a held-out external-data case is still needed.
- **The architect pre-scores are Claude's.** Claude wrote the identity and the rubrics.
- **The architect's commands have HTTPS**, and it can read its own login (accepted, OD-0082).
- **The hiomux changes** were tested by Claude only, with no independent review. The change to hiomux before
  OD-0077 remains unexplained.
- **Codex runs are not priced:** `cost_usd` is null, so they don't count against the run budget.
- **The memories wipe** is skipped while any architect process runs. That is safe, but memories can then persist
  until the next idle start.

## Didn't work

*Proposed H4 section.*

- **Codex's read-only sandbox** as the architect's boundary: it reads the whole disk.
- **A `--shared` clone** under the profile: its objects can't be resolved.
- **A hand-written write allowlist:** Codex's app server failed. Deriving it from hiomux's tested list worked.
- **`-c projects…trust_level`:** Codex 0.164 still prompted. hiomux writes the trust entry to the architect's
  `config.toml` instead.
- **A leak scan defined by reachability:** it flagged old review commits that were imported, not merged. "Later"
  must mean later by commit time.
- **Concurrent memories wipes:** they crashed two runs. Now skipped while an architect runs.
- **Codex device-code login:** disabled on the account. The browser login works.
- **tmux keys inside Warp:** Warp intercepts them. An orchestrator inside tmux trapped the owner. The orchestrator
  now runs outside tmux, with a separate view window.
- **Warp's new window:** it stacks exactly on top of the current one, which looks like an override with a
  transparent theme. Move it with System Events.

## For the index

*Proposed H4 section. Candidate Inbox lines: they need a distil, and are not yet in `knowledge/findings.md`.*

- [hiomux] Codex 0.164 read-only sandbox reads the whole disk; it auto-loads `AGENTS.md` (`project_doc_max_bytes=0` stops it); folder trust is read from `config.toml` before `-c`. Source: OD-0081, OD-0082.
- [hiomux] An architect profile must deny file-read-data on `$HOME` except its session and `CODEX_HOME`, and use a full (not `--shared`) clone. Source: OD-0082.
- [review] A leak-free historical eval needs `git archive` at the cutoff plus named extras, and "later" defined by commit time, not reachability. Source: OD-0082.
- [process] Tuning an identity on an eval case spends that case; keep held-out cases. Source: OD-0083, OD-0084.
- [ops] The owner uses Warp: no tmux prefix keys; the orchestrator outside tmux; the view via `open "warp://launch/hio-workers"`. Source: OD-0085.

## Assumptions made

- **Inert proposed documents went to `main`.** The pilot files were merged as such so `hiomux sa` reads `main`;
  acceptance came after (OD-0083).
- **Only the status line changed after approval.** `identity.md`'s status line was edited after v0.2 was approved
  (OD-0084 records both blobs).
- **The interactive architect pane was retired,** following "this session is the only one I will issue command
  to".

## Conflicts found between documents

None new. OD-0077's finding 1 (the unexplained hiomux change) remains.

## NOT approved by this session

- Harness-0.9 (any phase).
- The context manifest, the schema and the cases (all proposed).
- Any architect authority: it is advice only.
- Any change to Codex's review path.
- Any live operation, and any source right beyond D7.

## Next authorised action

None beyond orchestration on the owner's instruction. Owner decisions available:
1. a held-out external-data case for the architect;
2. harness-0.9 Phase A at `2df83b4`, then the first distil (now 42 Inbox lines, plus the five above);
3. the unexplained hiomux change (OD-0077, finding 1);
4. closing the hiomux run, and its cleanup;
5. the Authorisation B prerequisites.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `main` at the commit adding this handoff |
| Pushed? PR link | yes; no PR (documentation records). hiomux run `20261028T043057Z-e4d8` closed and cleaned up (OD-0085 correction 1) |
| Received into `main`? | not applicable: no review evidence this stream. Local-only `review/t0009-1-verify-2-codex` (`a6f7f31`) is superseded and deliberately unpushed (OD-0077) |
| Next actor | owner |
| Prompt for the next actor | "Read `AGENTS.md`, `STATUS.md` and this handoff. Stop if `main` lacks OD-0085. Run outside tmux. Before any hiomux use, check `bin/hiomux` against sha256 `e659b0bc…` (OD-0085 correction 1) and `PROTOCOL.md` against `b4e81ff4…` (OD-0085); a mismatch is a stop. Consult the architect only via `hiomux sa ask`, and summarise each consultation to the owner." |
