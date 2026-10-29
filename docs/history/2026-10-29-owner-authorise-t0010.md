<!-- The owner's messages to Claude Code, 2026-10-29, verbatim, with Claude's answer and the decision put. Recorded by OD-0115. -->

**Message AJ** (after the start-of-session report)

I want to proceed with development and deployment according to our plan?  where are we at.
consultant to architect for guidance re current state vs target

**Claude's answer** (summary; full text in the session): S1a and S1b-1.0 are accepted, on fixtures only. Live capture
still needs code (a real HTTP transport, which `check_repo` forbids today; an Azure blob backend; OIDC and workflow
wiring) and the Authorisation B prerequisites H1 (rights, U1–U7), H3 (controls), H4 (storage) and H5 (Q-010). Finality
C1–C7 and the soak are owed before S1b-1 completion, but not before capture starts (OD-0063). The architect
(consultation `20261029T120200-ask-1eee`, the fifth genuine one) advised running the owner's rights reading, Claude's
non-live integration and finality work, and Claude's control and storage evidence in parallel, with harness work
yielding to the capture path. Claude agreed, adding that the repository holds only 2026 calendars.

**Claude's decision put** (as put, verbatim)

**Decision 1.** Shall I draft a T-0010 task card and build the non-live part on a branch? A yes authorises:
- the real HTTP transport, limited to the adapters, with the matching `check_repo` amendment, tested only against fakes;
- the Azure blob backend, tested against the emulator;
- OIDC and workflow wiring with the schedule left disabled;
- the C1–C7 finality checks on synthetic inputs;
- 2027 calendars;
- draft H3 and H4 evidence packs for your decision;
- hiomux Sonnet workers.

A yes does not authorise any real fetch, credential, `tofu init/plan/apply`, provisioning, enabled schedule, or Codex review (assigning a reviewer stays a separate decision).

**Decision 2.** Will you start the U1–U7 rights reading now? This one is your own work. I can give you the matrix (`docs/research/T-0002-owner-verification-matrix.md` §4) as a short checklist if that helps.

**Message AK**

decision 1: yes
decision 2: what do you need here?
