---
id: VERIFY-<yyyy-mm-dd>-<review id>-<n>
reviewer: codex/reviewer
review: <REVIEW id whose findings are being verified>
assignment: <owner assignment of the remediation head>
base_revision: <reviewed head of the original review>
remediation_head: <full SHA the owner assigned for verification>
review_branch: review/<id>-verify-<n>
created_at: YYYY-MM-DD
---

# Verification: <review id>, round <n>

> Written by the reviewer in its own worktree (operating model §6.2). Immutable once committed.

| Finding | Remediation response | Remediation SHA | Independent check (commands, evidence) | Outcome (`verified_closed` / back to `open`, with reason) |
|---|---|---|---|---|

## Notes
