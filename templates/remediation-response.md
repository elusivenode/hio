---
id: RESPONSE-<review id>-<n>
author: claude/<role>
findings: [F-<review id>-<n>]
reviewed_head: <the head the original review examined>
fix_commits: [<full SHA>, ...]   # the commits that change the work
submission_head: self            # the commit that adds this response; resolve with: git log -n1 --format=%H -- <this file>
created_at: YYYY-MM-DD
---

# Remediation response: <findings>

> Written by the author on the staging branch. This is a claim, not a verification. The finding
> stays open until a verification record closes it. Verification is assigned against the
> **submission head**, so the reviewer sees the fix and this evidence at one revision
> (operating model §6.2, steps 6–7).

| Finding | Fix commit(s) | What changed (files) | Evidence (tests, checks) | Residual risk or disagreement |
|---|---|---|---|---|
