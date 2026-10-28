---
id: OD-0086
title: "Owner instructs that each hio-orch session runs the bootstrap by itself and brings up hiomux, with its view in a new Warp window, unless it is already up; orch prompt and alias changed outside the repository; hiomux and PROTOCOL unchanged"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-orch-autostart.md (typed by the owner, verbatim)
  sha256: 9646f58434c19216da0fc4c291a9db90e8d45a38428932ed76425c0a89a891f3
  date: 2026-10-28
  quote: "when I run hio-orch, which starts a new orch session, I want you to bring up hiomux in a new warp terminal, if is not up already.  you also need to run your bootstrap sequence."
base_revision: 636fea073b7f2c3bc5f5a79a974f77523c71ef61
applies_to:
  - path: ~/.hio-runs/orch-prompt.md (outside the repository)
    revision: "sha256 5f75f210e0ceb3cbc6f19ce4a441883fed29281564f9e23d987ce09db1e1ee8c"
  - path: ~/.zshrc, alias hio-orch (outside the repository)
    revision: "the alias text quoted below"
related: {adrs: [], tasks: [], findings: [], ods: [OD-0072, OD-0085]}
---

# OD-0086: hio-orch starts itself

## Owner instruction

Quoted in full above: on `hio-orch`, run the bootstrap, and bring up hiomux in a new Warp window if it is not
already up.

## What changed (outside the repository; tested by Claude)

- **`~/.hio-runs/orch-prompt.md`** (was `d8c0e5c0…`, now `5f75f210…`; backup
  `~/.hio-runs/notes/orch-prompt.pre-autostart.bak`). Step 3 used to say to start the stack "only when there is
  work to delegate". It now reads PROTOCOL.md, and a new step 4 runs **only if the bootstrap and the hash checks
  (steps 1 and 2) passed**:
  - `tmux has-session -t hio` fails → `hiomux up --no-orch` (reuses an open run, else starts a new one);
  - `tmux list-clients -t hio` empty → `open "warp://launch/hio-workers"`;
  - then a short report to the owner. Nothing is delegated without an owner instruction.
- **The `hio-orch` alias** (`~/.zshrc`; backup `~/.hio-runs/notes/zshrc.pre-autostart.bak`) now passes an
  opening message, so the session starts the sequence without waiting for the owner:

  ```
  alias hio-orch='cd ~/Developer/elusivenode/hio && claude --append-system-prompt "$(cat ~/.hio-runs/orch-prompt.md)" "Start of session: run the start-of-session sequence in your system prompt."'
  ```
- **Test:** in this session, step 4 found no tmux server, ran `hiomux up --no-orch` (run
  `20261028T081310Z-d55d`), and opened the Warp view; `tmux list-clients -t hio` then showed one attached client
  on window `view`.

## Consequences

- **Every `hio-orch` session with no open run opens a new hiomux run**, even with nothing to delegate. Empty runs
  need `hiomux close` and `cleanup` as before.
- **The hiomux and PROTOCOL.md hashes are unchanged** (`e659b0bc…`, OD-0085 correction 1; `b4e81ff4…`,
  OD-0085), so the start-of-session check stays as it is.

## Not changed

No repository harness, tool, CI or authority. hiomux grants no authority; a running stack authorises no task.
