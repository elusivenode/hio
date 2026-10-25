---
id: HANDOFF-2026-10-25-t0002-rba-nyfed-evidence
date: 2026-10-25
actor: claude/implementation-agent (Claude Opus 5.5)
work_status: authorised   # OD-0045: integration done; T-0002 research continued; nothing approved
base_revision: a37d81f3cd4fa7fb61b912c64d82e7ed7077db72
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/2026-10-25-t0002-rba-nyfed-evidence.md
work_commits: [569753a, a37d81f]
work_card: T-0002
---

# Handoff: readiness integration; T-0002 RBA and NY Fed evidence

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

## Changed files
- The integration (OD-0045): `569753a`, merged `--no-ff` as `a37d81f`; pushed under OD-0046.
- This branch:
  - added the verbatim instruction (sha256 `d55b6895…3343`), OD-0045, the evidence note
    `docs/research/T-0002-rba-nyfed-evidence-2026-10-25.md` and this handoff;
  - edited the three index READMEs, the T-0002 card (one progress line), `registers/sources.yaml`
    (dataset notes and research pointers only) and `STATUS.md`.

## Done
- Scope verified before integration; the merge tree is equal to the branch's.
- Primary-source evidence for RBA (terms, F1, F11, methodology, RITS) and NY Fed (terms, SOFR,
  SOFR Index, API). The S1b staging recommendation is in §5 of the note.

## Tests and evidence
| Claim | Method | Result |
|---|---|---|
| No permission changed | `load_genuine('registers/sources.yaml')`: every permission `unknown`, `unverified` | confirmed |
| No implementation change | `git diff --stat main -- src tests tools specs .github pyproject.toml uv.lock` | empty |
| Samples not retained | the scratchpad sample directory deleted (`rm -rf`) | deleted |
| Repository checks | `check_repo`, `ruff check`, `ruff format --check`, `pytest` | PASS (0 problems); clean; 63 files formatted; 278 passed |

## Known limitations and not verified
- The quotations are the fetch tool's short extracts and summaries. They must be checked against
  the live pages.
- The RBA RITS Sydney-only holiday statement and the LSEG licence statement come from search
  extracts only.
- Not read: the SIFMA recommendations, the RBA bank-holiday pages, the US Treasury terms, and
  the NY Fed API documentation (it did not render).

## Conflicts found between documents
- The 2026-10-18 note proposed CC BY for the RBA AUD/USD. The CSV `Source` row and the
  definitions page show WM/Reuters (third party). The old note is left unedited, and
  superseded on this point by the 2026-10-25 note.
- The readiness assessment's E1 ("RBA and NY Fed first") assumed an RBA-cleared AUD/USD. It is
  revised by the note's §5 (cash legs first), and the assessment is left unedited.

## NOT approved by this session
- Any rights value; the OD-0013 lift; the staging; an ADR-0010 revision; S1b; any contact with
  the RBA, LSEG or ASX.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `docs/t0002-rba-nyfed-evidence` @ this commit (committed under OD-0046); merged to `main` `--no-ff` |
| Pushed? PR link | `main` pushed after the merge (OD-0046); no PR |
| Received into `main`? | yes (OD-0046) |
| Next actor | **owner** |
| Prompt for the owner | "Verify or reject the per-dataset rights in the 2026-10-25 note, decide the FX source path, and decide whether to instruct an HIO-ADR-0010 rev 4 draft for staging. Prerequisite: `main` contains this handoff." |
