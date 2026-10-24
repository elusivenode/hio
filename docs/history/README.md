---
id: HIO-HISTORY
title: Superseded inputs and rationale
status: historical
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-24
---

# HIO history: superseded inputs (kept verbatim for rationale)

These files are **not policy**. They record how the current baseline was reached. Where they
conflict with a canonical document, the canonical document wins (`AGENTS.md` precedence).

| File | What it is | Status | Superseded by |
|---|---|---|---|
| (not committed) the first owner brief, "Strategic Review of Investment Research and Portfolio Construction Roadmap" | supplied only as chat text on 2026-10-18. It asked for a critical review of the research direction across a factor universe, data acquisition, modelling, the SAA/TAA connection, layer separation, validation and sequencing | historical | answered by `2026-10-18-strategic-review.md`; its intent is carried into the charter |
| `2026-10-18-strategic-review.md` | Claude's first review: it treated HIO as an extension of the SMSF and its cadence | superseded | `2026-10-18-five-year-architecture-proposal.md`, then the canonical baseline |
| `2026-10-18-directive-five-year-architecture.md` | owner directive: HIO is a separate five-year system; it corrects six methodological points in the first review | historical (its decisions are in HIO-ADR-0001/0002/0007) | — |
| `2026-10-18-five-year-architecture-proposal.md` | Claude's architecture proposal; direction accepted "for further design" | superseded in part: §5.1 → HIO-ADR-0004; AD-6 → HIO-ADR-0005; §4.1 catalogue → HIO-ADR-0009; §11 slice → HIO-ADR-0010 | canonical baseline |
| `2026-10-18-directive-harness-refinement.md` | brief supplied by the owner in chat **as a file path with no accompanying words**. It describes itself as a "Proposed documentation-only assignment". Its authorship is not stated in the file | historical; T-0006's commissioning brief; recorded in OD-0001 (corrected; the ambiguity is preserved) | partly by the final-correction directive |
| `2026-10-18-directive-t0006-final-correction.md` | owner directive ("From: HIO owner, with ChatGPT acting as strategic architecture collaborator"), supplied by file path. It explicitly authorises six documentation corrections, and cites a Codex focused analysis that was not supplied | historical; recorded in OD-0002 | — |
| `2026-10-18-directive-review-worktree-protocol.md` | proposed harness amendment (it names ChatGPT among its roles), adopted by the owner's chat instruction "please implement ... I will advise Codex" | historical; recorded in OD-0003; implemented as T-0007 | — |
| `2026-10-18-codex-assessment-t0007.md` | a Codex assessment of T-0007 at `46ea6a5`, pasted by the owner without words | historical evidence; remediated within T-0007 (OD-0003); not a review record | — |
| `2026-10-18-directive-g1-approval-package.md` | owner directive ("From: HIO owner, on architectural advice from ChatGPT") authorising receipt of VERIFY-2026-10-18-a01-1 and preparation of the G1 package | historical; the package's `authorised_by` | — |
| `2026-10-18-owner-g1-decisions.md` | the owner's own G1 decisions, verbatim (sha256 `111b6fc2…c306a99e`) | **authority** for OD-0006…0009 (not superseded) | — |
| `2026-10-18-owner-g1-followup.md` | the owner's follow-up instructions, verbatim | authority for OD-0010 | — |
| `2026-10-18-owner-g1-completion.md` | the owner's approval of ADR-0010 rev 3 and harness-0.6, and the T-0002/T-0003 instructions, verbatim | authority for OD-0011…0013 | — |
| `2026-10-24-owner-stale-line-fixes.md` | the owner's instruction to fix the stale lines, verbatim, with the list it refers to | authority for OD-0014 | — |
| `2026-10-24-owner-further-stale-lines.md` | the owner's instruction to fix the further stale lines, verbatim | authority for OD-0015 | — |
| `2026-10-24-owner-s1a-preparation.md` | pasted collaborator advice on S1a preparation, plus the owner's own words, verbatim | authority for OD-0016 (the advice itself is advice; see OD-0016 for the reading) | — |
| `2026-10-24-owner-s1a-authorisation.md` | the owner's S1a authorisation, T-0004 confirmation and parallel-work instructions, verbatim | authority for OD-0017 and OD-0018 | — |
| `2026-10-24-owner-make-public.md` | the owner's instruction to make the repository public, verbatim | authority for OD-0019 | — |
| `2026-10-24-owner-s1a-proceed.md` | the owner's instruction to proceed with S1a implementation, verbatim | authority for OD-0020 | — |
| `2026-10-24-owner-approve-harness-0.7.md` | the owner's approval of harness-0.7 rev 3, verbatim | authority for OD-0021 | — |
| `2026-10-24-owner-receive-s1a-review.md` | the owner's receipt authorisation for PR #1, verbatim | authority for OD-0022 | — |
| `2026-10-24-owner-authorise-s1a-remediation.md` | the owner's authorisation of the S1a remediation slice, verbatim | authority for OD-0023 | — |
| `2026-10-24-owner-f6-remediation-before-receipt.md` | the owner's F6 remediation-before-receipt authorisation (harness-0.8 work stopped; local-first proposal requested), verbatim | authority for OD-0024 | — |
| `2026-10-24-owner-f6-round3-authorisation.md` | the owner's F6 round-3 authorisation and disposition of the two verification records, verbatim (its record hash was mistranscribed) | authority for OD-0025, with its correction | corrected in part by the next file |
| `2026-10-24-owner-f6-round3-hash-correction.md` | the owner's correction of that hash, verbatim | authority for OD-0025 | — |
| `2026-10-24-owner-q001-q002-drafting.md` | pasted by the owner without other words: solution-architecture advice (Option A for Q-001/Q-002, refined) and a drafting-only instruction, verbatim | authority for OD-0026 (the advice is advice) | — |
| `2026-10-24-owner-q001-q002-final-amendment.md` | the owner's final narrow amendment instruction for the Q-001/Q-002 drafts, verbatim | authority for OD-0027 | — |
| `2026-10-24-owner-q001-q002-revision4.md` | the owner's revision-4 instruction (Q-001 header; Q-002 processing order vs acquisition history), verbatim | authority for OD-0028 | — |
| `2026-10-24-owner-approve-q001-select-q002-a-prime.md` | the owner's approval of Q-001 revision 4 and selection of Q-002 Option A′, verbatim | authority for OD-0029 | — |
| `2026-10-24-owner-approve-q002-authorise-f4-f7.md` | the owner's approval of Q-002 revision 5 and authorisation of F4/F7 implementation, verbatim | authority for OD-0030 | — |
| `2026-10-24-owner-f4-f7-verify-6-exception.md` | the owner's remediation-before-receipt exception for VERIFY-2026-10-24-s1a-1-6, verbatim | authority for OD-0031 | — |
| `2026-10-24-owner-f7-verify-7-exception.md` | the owner's remediation-before-receipt exception for VERIFY-2026-10-24-s1a-1-7, verbatim | authority for OD-0032 | — |
| `2026-10-24-owner-f7-verify-8-exception.md` | the owner's remediation-before-receipt exception for VERIFY-2026-10-24-s1a-1-8, verbatim | authority for OD-0033 | — |
| `2026-10-24-owner-q002-quality-digest-drafting.md` | the owner's quality_digest direction and drafting instruction, verbatim | authority for OD-0034 | — |
| `2026-10-25-owner-approve-q002-r1-authorise-implementation.md` | the owner's approval of Q-002-R1, the VERIFY-…-9 exception and implementation authorisation, verbatim (its review commit was mistranscribed) | authority for OD-0035, with its correction | corrected in part by the next file |
| `2026-10-25-owner-approve-q002-r1-correction.md` | the owner's correction of that review commit, verbatim | authority for OD-0035 | — |
| `2026-10-18-directive-a01-baseline.md` | owner directive commissioning this baseline and the harness | historical (in force as the commissioning brief for A01) | — |

**Rule going forward** (operating model §0). An owner directive that changes direction is
committed here, and the decisions it makes become ADRs. Directives no longer live only in
`~/Downloads` or in chat.
