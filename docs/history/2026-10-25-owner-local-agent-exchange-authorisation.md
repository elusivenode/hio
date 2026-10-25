<!-- Pasted into the Claude Code chat by the owner, 2026-10-25, verbatim (the pasted block only; the
owner's preceding chat sentences are not reproduced). Recorded by OD-0060. -->

**To Claude — establish direct local agent handoffs**

Claude and Codex operate on the same host with access to the HIO repository. I authorise a minimal local-first handoff mechanism to eliminate manual owner relay of routine completion reports.

Use `~/.local/share/hio/agent-exchange/` as a shared exchange directory outside the repository.

Implement only the following:

- Separate `claude/` and `codex/` subdirectories.
- One uniquely named, immutable completion report per task or review.
- Atomic publication through a temporary file followed by rename.
- Reports contain repository, assignment/review id, exact submitted/reviewed head, reviewer commit, complete added-file inventory with SHA-256, verdict and next actor.
- Both agents can read the directory. Each writes only to its own designated subdirectory.
- Use a consistent documented filename convention and simple JSON or Markdown.
- Never store credentials, source-data payloads or private SMSF information there.

For the current B2 receipt, Codex should publish its existing final report directly to the exchange directory. Claude should read it and independently check the Git evidence.

Do not replace authoritative Git records with exchange files, grant new review assignments, relax stop-on-mismatch or change approved standards.

Keep this a local operational convention. Do not initiate a broader harness revision or another review cycle.

Report the shared path and demonstrate one successful Codex-to-Claude handoff.
