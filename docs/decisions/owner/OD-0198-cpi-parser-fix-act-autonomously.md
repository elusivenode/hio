---
id: OD-0198
title: "Owner authorises merging PR #124 and the CPI release parser fix, and tells Claude to act autonomously within authorised work, consulting the architect when required"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-act-autonomously.md (owner's message, verbatim, with Claude's question)
  sha256: 4c7d59112b72156b3d30cf3eb6f14a4c6d969346dae19f93282df694c5b7dd70
  date: 2026-11-22
  quote: "y. act autonomously. consult the architect when required"
base_revision: cf146106b460619ee21f6e8f6eb467893ad6b3de
related: {adrs: [], tasks: [], findings: [F-REVIEW-2026-11-22-e0004-1-1], ods: [OD-0184, OD-0197]}
---

# OD-0198: parser fix; act autonomously

**Authorised:** merging PR #124 (OD-0184 A1) and fixing the CPI release parser on the real layouts it refused. The download and comparison remain OD-0197's, once.

**"Act autonomously":** Claude reads this as: carry already-authorised work through without asking at each step, and report afterwards. It widens no scope. Accepting, approving and waiving stay with the owner; OD-0197's stop on any difference stands; new downloads, reruns and design changes still need their own yes.

## How it was done

- **Claude made the fix itself, not a worker.** The question said "with a worker". The diagnosis needed the retained real pages, and once made, the fix was about thirty lines.
- **Cause:** the parser read the first "All items" row in a page. In the real releases that row belongs to the summary table before Table 1 (Table A, or the text table in the body) and holds percent changes. The committed snippets had been cut to Table 1 alone, so the tests passed. The parser now reads only the table headed "Table 1."; the snippets are re-cut to keep the summary row, and tests refuse it.
- **Also fixed, found on the real files:** the PDF text has a space before the leader dots; the flat-file reader stopped on the October 2025 row, whose value is "-".
- **Fetch made resumable:** a refused request used to leave a directory the tool would not reuse, with the cap partly spent. It now keeps `progress.json`, resumes from it and counts earlier requests against the same cap; it pauses one second between requests.
- **Check on real inputs:** all 11 retained releases (2002 to 2026; three PDF, two `<PRE>`, six HTML) parse, and every printed level equals the flat file.

## Not authorised

A rerun of E-0004; any design change; any download beyond OD-0197's; any acceptance, approval or waiver.

## Corrections (append-only)
