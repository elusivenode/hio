<!-- The owner's messages to Claude Code, 2026-11-22, verbatim. Recorded by OD-0212. The first asked for an investigation. Claude reported: no flaky test and no CI fault, and `main` had never failed; of the last 200 runs, 115 succeeded, 8 failed (5 distinct commits, each a real mistake caught before merge: one test broken by a stub this session, three lint or format failures and one front-matter failure earlier), 22 were cancelled as superseded, and 49 skipped by design; every push to a pull-request branch ran the workflow twice, cancelled runs look like failures, and nothing checked locally before a push. Claude said it would install a local pre-push gate, and asked: "Shall I open a PR with the trigger change in fix 2 for your approval? A yes authorises drafting that one workflow edit; merging it stays your separate approval." Fix 2 was: run on `pull_request`, and on `push` only for `main`, `review/**` branches and `reviews/**` tags. The second message is the answer. -->

**Owner's messages**

CI tests are repeatedly failing. Investigate

Y
