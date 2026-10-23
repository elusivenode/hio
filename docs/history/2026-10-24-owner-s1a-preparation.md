<!-- The owner's message in the Claude Code chat, 2026-10-24, verbatim. It consists of a pasted
block of collaborator advice (author not stated; it is advice, AGENTS.md rule 4) followed by the
owner's own words. The authority for OD-0016. The owner's own words are the last line; Claude
reads "once done" as adopting the advice's executable parts within the standing limits (see
OD-0016 for the reading and what it excludes). -->

## Pasted advice (verbatim)

The main sequencing issue is now clear: S1a can proceed independently of T-0002, but the roadmap, implementation plan and T-0005 card still describe a combined S1. The migration checklist also has an obsolete sentence about ADRs remaining proposed. I’d put those corrections ahead of the repository move, while keeping rights research active for S1b.
Yes: S1a is the right next implementation slice. At the clean 81793f7 head, G1 is complete, all eight A01 findings are closed, and S1a still needs its own owner authorization. No HIO repository or implementation exists. T-0002 rights remain unverified, which blocks live S1b but does not block synthetic S1a. These states are recorded in STATUS (hio/STATUS.md) and ADR-0010 (hio/docs/decisions/HIO-ADR-0010-first-slice-scope.md).

I would authorize S1a through a bounded decision record, with this order of work:

1. Make the execution documents agree before migration. The roadmap (hio/docs/roadmap.md), implementation plan (hio/docs/implementation-plan.md) and T-0005 card (hio/registers/tasks/T-0005-hio-s1-walking-skeleton.md) still describe a combined S1 or make T-0002 appear to block fixture work. Correct the obsolete “every proposed ADR remain proposed” sentence in §8.1 (hio/docs/harness/operating-model.md) before using its migration checklist. The HIO README (hio/README.md) also calls the move a git mv, while §8.1 requires preserved history. These are migration-preparation issues, not reasons to wait for source rights.
2. Set the S1a boundary in the authorization: source commit, destination and owner of the private hio repository, pinned development stack, history and approval-continuity checks, synthetic acceptance fixtures, and a fixed-head Codex review. Keep network fetches, real data, credentials, buckets and scheduling outside S1a. Verify the split history and approved document hashes locally before publishing the new repository. GitHub supports pushing an existing local repository into a private repository; Actions permissions should be kept to the access CI needs. GitHub import guidance (https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github), Actions permissions (https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
3. Run the parallel work now. Continue T-0002 evidence gathering early: unresolved retrieval rights and timing could delay S1b even if S1a finishes quickly. Continue T-0003 research within its current no-contact limit. T-0004 is independent of S1a and can be reviewed in parallel.

I would not count a T-0004 review in this continuing chat as the fresh-session harness test. §10 (hio/docs/harness/operating-model.md) requires a session with no prior chat history and a neutral prompt. The cross-lineage review-branch procedure in OD-0010 also still asks for owner confirmation before a reviewer commits its record.

## The owner's own words (verbatim)

once done, please push our branch to the remote
