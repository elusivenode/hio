# Solution architect's harness-0.9 assessment (2026-10-28, verbatim)

Advice from the HIO solution architect, relayed by the owner into the Claude Code session and
transcribed verbatim below. It was advice when received (`AGENTS.md` rule 4). The owner adopted its
disposition, qualified by Claude's response, in
`2026-10-28-owner-adopt-harness-0.9-disposition.md` (OD-0070).

---

# To Claude — HIO Harness-0.9 Architectural Assessment and Revision Instructions

**Role:** Claude — HIO implementation agent and author of the harness-0.9 proposal  
**From:** HIO solution architect — advisory assessment for owner consideration  
**Date:** 28 October 2026  
**Disposition:** ADOPT WITH CHANGES — architectural recommendation, not owner approval  
**Subject:** Harness-0.9 revision 2, authority boundaries, institutional knowledge, reviewer independence and sequencing against T-0009

## 1. Purpose of this handoff

I have reviewed the harness-0.9 architectural brief, the revision 2 proposal, its seed knowledge files, the same-vendor dry-run report, the approved harness authority model, the corrected STATUS and the T-0009 independent review.

My conclusion is that **harness-0.9 addresses a genuine architectural deficiency and should be adopted with targeted modifications**.

The proposed knowledge layer is valuable. However, its adoption must not create a second governance programme, weaken the distinction between owner authority and agent execution, compromise reviewer independence, or divert implementation capacity from achieving live point-in-time capture.

This handoff provides:

1. The architectural rationale for adopting harness-0.9.
2. Specific dispositions on H1–H9 and H11.
3. Required refinements to H5, H7 and H11.
4. The recommended sequencing of Phase A, Phase B and T-0009 remediation.
5. Treatment of the existing dry-run findings and OD-0069 correction.
6. A bounded next step and explicit stop conditions.

**This document is advice. It does not authorise a merge, implementation, standards change, review assignment, waiver or acceptance.** The owner must explicitly adopt any proposed instruction that requires authority under `AGENTS.md`.

## 2. Repository evidence and authority baseline

The assessment used these fixed revisions:

| Purpose | Repository revision |
|---|---|
| Approved harness, current STATUS and T-0009 authority records | `16ea0c6f472b61a28a9741c75635255bf173ffa6` |
| Harness-0.9 proposal, revision 2 | `f5ce1b8beaaaed59fbcbccf586892ac9ae1cf261` |
| T-0009 implementation reviewed by Codex | `ce0c3b534ac98eb89663cf15c439f5ccad93b969` |

Relevant paths:

- `AGENTS.md`
- `STATUS.md`
- `docs/harness/operating-model.md`
- `docs/decisions/harness-0.9-proposal.md`
- `MAP.md`
- `knowledge/findings.md`
- `reviews/reports/REPORT-2026-10-28-harness-0.9-fable-dryrun-1.md`
- `reviews/records/REVIEW-2026-10-25-t0009-1.md`

Treat the fixed repository revisions and approved owner decisions as authoritative. Resolve exact revisions through Git rather than reconstructing identifiers from this handoff.

The same-vendor dry run is useful diagnostic evidence, but it is **not** an independent Codex review, technical verification or approval.

I also inspected the relevant T-0009 implementation paths, including:

- `src/hio/publish/lineage.py`
- `src/hio/sources/run.py`
- `src/hio/jobs/s1b1.py`

This corroborated material aspects of the review findings, but I did not independently execute the test suite or reproduce every adversarial probe.

Do not upgrade this assessment into a claim of comprehensive technical verification.

## 3. Architectural diagnosis: what harness-0.9 should solve

The current harness is relatively strong at answering:

- Who authorised the work?
- Which revisions were reviewed?
- Which findings are open?
- Which standards apply?
- What was technically verified?
- What was accepted, approved or merged?

It is less effective at answering:

- What did previous sessions discover?
- Which approaches failed, and why?
- Which implementation traps have already been encountered?
- What assumptions were tested and rejected?
- What knowledge should a new agent inherit without accepting another agent's conclusions uncritically?
- How does an agent find this information without reading extensive chronological history?

This distinction matters increasingly as HIO matures.

The objective should not be to preserve every agent conversation. It should be to preserve the **minimum sufficient institutional knowledge required to conduct reproducible work and make informed decisions over years**.

### Three related but distinct types of memory

**A. Governance memory**

Records owner instructions, decision authority, standards approval, technical review, integration and acceptance.

Canonical examples include owner decisions, approved standards, task authorisations and review records.

Governance memory requires strong provenance, explicit authority and revision integrity.

**B. Engineering memory**

Records technical discoveries, defect patterns, failed approaches, reproducibility lessons, operational traps and architectural reasoning.

Examples include missing-link rights failures, incorrectly attributed datasets, dropped comparison periods and release/spec identity mistakes.

Engineering knowledge should be easy to contribute and retrieve. It should not require an owner decision for every observation.

**C. Research memory**

Records investment hypotheses, data limitations, factor definitions, experiments, negative results, modelling assumptions and evidence for economic conclusions.

The canonical research records already include `registers/hypotheses.yaml` and `registers/experiments.yaml`.

Harness-0.9 should connect these memory systems without duplicating their responsibilities or creating competing authorities.

### Long-term objective

An agent starting in a fresh session, or a future model generation, should be able to:

1. Understand HIO's purpose and approved architecture.
2. Establish the current authoritative work state.
3. Identify the exact work it is authorised to perform.
4. Find relevant accumulated engineering and research knowledge.
5. Distinguish proven facts from unverified claims and historical conclusions.
6. Resume productive work with bounded context cost.
7. Know when to stop rather than infer missing authority.

That is the architectural success criterion for harness-0.9.

## 4. H1 — MAP.md

**Disposition: ADOPT, with source and maintenance discipline.**

A concise project map is useful because `STATUS.md` is not the right location for the project's enduring purpose, research pillars, architectural boundaries and long-term trajectory.

Retain:

- Purpose and research pillars.
- Year 1 trajectory as a sequencing hypothesis, not a commitment.
- Current, target and undecided architecture.
- Active research and engineering threads with navigation pointers.
- High-value settled architectural facts.
- Open strategic questions.

Do not restore operational state to MAP.

In particular, MAP should not independently maintain:

- Current task status.
- Current review findings.
- Pending remediation instructions.
- Current branch heads.
- Detailed blocker lists already maintained in STATUS.

**Source-of-truth principle:** MAP is a navigational projection of other records. It does not acquire independent authority merely because the owner approves its content.

### Maintenance concern

The revision 2 proposal requires owner approval for MAP changes.

This is appropriate for substantive changes to strategic direction or architectural assertions, but may be excessive for mechanical navigation corrections.

Please distinguish:

- Substantive architectural or strategic revisions requiring explicit owner approval.
- Mechanical link, path or source-reference corrections that do not change meaning and could be covered by bounded administrative authorisation.

Do not presume the second category is already authorised. Propose the distinction for the owner's decision.

The map should not become another expensive approval surface.

## 5. H2 — Engineering findings index

**Disposition: ADOPT.**

The proposed `knowledge/findings.md` is one of the strongest additions.

It allows the system to retain lessons such as:

- Missing or substituted provenance links changing the effective rights subject.
- The need for negative tests that grant rights to an incorrect subject while denying the true subject.
- Factor-spec identity and versioning constraints.
- Silent omission of comparison periods.
- CI trailer and shell-pipeline failure modes.
- Decisions that depend on exact publisher precision or available evidence.

These are highly reusable engineering lessons.

### Maintain evidence status

Retain the separation between Settled and Inbox.

The distinction must remain explicit:

**Settled:** an owner-accepted knowledge entry that cites evidence, not an independent standard or approval.

**Inbox:** an observation or claim that has not yet been settled.

A settled finding may subsequently become stale when the code, data contract or approved standard changes.

Therefore, add a lightweight applicability rule:

- Entries identify their source and relevant revision or scope where material.
- An entry contradicted by newer authoritative evidence must be corrected, superseded or flagged.
- Historical findings must not automatically govern future implementation revisions.
- The original evidence remains accessible.

Avoid introducing a heavyweight review process for every knowledge entry.

### Research-memory boundary

Preserve the proposal's boundary with `registers/experiments.yaml`.

Investment hypothesis results, quantitative experiments and negative research findings belong in research memory.

The engineering findings index may point to them, but should not independently reproduce their conclusions.

The long-term HIO research platform must preserve why an approach was rejected, including relevant assumptions and data limitations, not simply record that it failed.

### Distillation

The proposed 25-line Inbox threshold is reasonable as a housekeeping signal, not an automatic governance gate.

Retain owner authority over claims being presented as settled, but make the process proportional.

Distillation should preferably occur at existing task boundaries or when knowledge retrieval has demonstrably become impaired.

Do not generate a separate owner-review event merely because the Inbox crosses a numerical threshold.

## 6. H3 — STATUS.md

**Disposition: ADOPT the current-state-only principle; avoid unnecessary rework.**

The approved main revision `16ea0c6` already includes OD-0069's repair of the T-0009 authority and STATUS inconsistency.

This matters because revision 2 of the harness-0.9 proposal still contains a decision item requesting that repair.

**The repair is already reflected in the fixed repository evidence.**

Consequently:

1. Mark the relevant proposal action as satisfied by OD-0069.
2. Preserve its historical context.
3. Do not request the owner to authorise the same repair again.
4. Do not rewrite a correct STATUS merely to demonstrate Phase A completion.

The current-state-only model is appropriate.

STATUS should answer:

- What is underway?
- Which approved authorisations constrain it?
- What is blocked?
- What remains open?
- What must happen next?
- Which branch contains the implementation?

History belongs in its canonical logs, reviews, decisions and handoffs.

The proposed line-count and line-width enforcement should remain a separately tested Phase B tool change.

## 7. H4 — Stream handoffs and session continuity

**Disposition: ADOPT, with minimal additional ceremony.**

Retain immutable, per-session handoffs organised by stream.

The suggested paths such as `handoffs/t0009/`, `handoffs/harness/`, `handoffs/research/` and `handoffs/rights/` are reasonable.

Preserve the existing requirements for:

- Exact branch and revision.
- Work status.
- What was completed.
- What was not approved.
- Open findings and blockers.
- Next actor.
- Completion block and successor instruction.

The additions *Didn't work* and *For the index* are valuable.

### Avoid duplicate work

Do not require authors to write the same findings extensively in both the handoff and knowledge index.

A handoff can identify concise candidate index entries, preferably citing existing review or implementation evidence.

Retain task-boundary rollover as a working practice, rather than creating another approval event.

Avoid making session count or the use of `/clear` an architectural correctness gate.

## 8. H5 — Two-tier owner record model

**Disposition: DEFER.**

The revision 2 correction is directionally sound.

A verbatim owner transcript with a cryptographic hash and a repository index entry can provide adequate evidence for strictly documentation-only instructions.

However, this is not equivalent to granting authority based on an agent's commit trailer or self-declared interpretation.

Preserve:

- Exact owner wording.
- Stable repository evidence.
- Transcript hash.
- Authorisation scope.
- Relevant base revision.
- The distinction between recorded evidence and the authority conveyed by the original owner instruction.

The tier-2 category must remain narrow.

Explicitly exclude:

- Code or data changes.
- Infrastructure changes or deployment.
- Source-rights claims.
- Standards, ADR or spec approval.
- Work acceptance.
- Waivers.
- Scope changes.
- Review assignments and receipts.
- Merge or promotion authority.
- Any decision whose effect reaches beyond strictly reversible documentation work.

### Critical sequencing

Do not adopt H5 before H6.

The current record burden may be largely mechanical. Once assignment and receipt are scripted, the benefit of replacing OD files might be considerably smaller.

Changing the authority-record model before measuring that benefit would introduce policy complexity to solve a problem that automation may resolve more directly.

**Recommendation:** H5 remains a candidate policy amendment, not a Phase A commitment or prerequisite.

## 9. H6 — Scripted assignment and receipt

**Disposition: ADOPT in Phase B, subject to independent verification.**

This is likely the most valuable operational simplification in harness-0.9.

The current process appears to spend significant effort manually executing repeatable checks that are already specified in the operating model.

Converting those checks into deterministic tools is preferable to relying on repeated natural-language instructions.

Retain the proposed tools:

- `tools/hio_assign.py`
- `tools/hio_receive.py`

### Required design properties

The scripts must preserve the approved evidence-integrity requirements, including:

- Exact assignment target and head.
- Revision and branch identity.
- Scope checks.
- Bidirectional inventory reconciliation.
- Content hashes.
- Allowed review paths.
- Byte-identical receipt.
- Correct review state and index updates.
- Final verification before publication.
- Stop-on-mismatch behaviour.

The tool's exit status must not be treated as sufficient evidence unless the tool's tests and behaviour have been independently verified.

### Independent review

Codex should test both successful receipt and deliberate failure cases.

Examples include:

- Moving review branch tip.
- Incorrect assignment head.
- Additional or missing files.
- Unauthorised path changes.
- Hash mismatch.
- Duplicate or conflicting receipt.
- Incorrect review index transition.
- Stale target revision.
- Failure during a partially completed receipt.

A non-zero result must leave the workflow in a safe, reconcilable state.

No implementation should silently replace the owner acceptance or approval steps.

The scripted receipt should mechanise the existing operating model, not change the meaning of review or acceptance.

## 10. H7 — Standing administrative merge authority

**Disposition: ADOPT ONLY WITH A NARROWER AUTHORITY MODEL.**

This is the most consequential governance recommendation in the package.

The operational problem is real.

Owner instructions, task cards and authority evidence can remain on implementation branches while `main` continues to present an incomplete or misleading view of authorised work.

H7 attempts to remove this problem through standing merge approval.

I support that objective.

However, path allowlisting alone is not sufficient to ensure that a change is administrative rather than consequential.

A file beneath `docs/decisions/owner/` can contain an approval, waiver, acceptance or expanded authorisation. Its location does not make the change harmless.

### Recommended distinction

Separate:

**A. Publishing existing authority**

An agent records an explicit owner action that has already occurred.

**B. Creating consequential authority**

The owner authorises, accepts, approves, waives, changes scope or otherwise makes a consequential decision.

Standing administrative publication may support A, but cannot substitute for B.

### Conditions for a bounded standing approval

If the owner chooses H7, require:

1. A specific owner-approved standing delegation recorded in a tier-1 OD.
2. A narrow list of permitted administrative paths and operations.
3. Direct traceability from each published authority statement to an existing owner instruction.
4. No change to the meaning or scope of that instruction.
5. No independent grant of acceptance, approval or waiver by Claude.
6. Exact revision and scope checks before publication.
7. Fail-closed behaviour if evidence, scope or target revision is ambiguous.
8. No code, standards, specs or substantive review-result modifications under the delegation.
9. Revocability by the owner.
10. Independent verification of any new automation enforcing these constraints.

A proposed task card may be present on `main`, provided its status and recorded authority are unambiguous. Its presence is not authorisation.

The owner should be able to authorise an administrative workflow without having to approve every mechanical publication of records.

The key requirement is that the **delegation never allows the agent to decide that an otherwise unauthorised consequential action is permitted**.

Please refine H7 accordingly. Do not implement it without explicit owner approval.

## 11. H8 — Hooks and enforcement

**Disposition: DEFER until the primary controls are established.**

Hooks are useful for preventing accidental violations, but they are not a durable security boundary.

The revision 2 proposal correctly places GitHub branch protection ahead of local hooks.

Preserve that ordering.

Distinguish:

- Server-enforced repository protections.
- CI and deterministic validation.
- Local workflow safeguards.
- Natural-language instructions to agents.

These offer different levels of assurance.

### Recommendations

Keep hooks focused on preventing common mistakes, rather than attempting to recognise all prohibited operations through command-string matching.

Do not claim that regex-based hooks guarantee the absence of network egress, unauthorised provisioning or policy violations.

Overrides must remain subject to approved authority and must not be independently created or interpreted by the constrained agent.

H8 should be implemented only where it provides measurable additional protection and does not obstruct legitimate authorised work unnecessarily.

## 12. H9 — Measurement

**Disposition: ADOPT IN SIMPLIFIED FORM.**

The key questions are:

- Does a fresh agent find relevant context without repeatedly asking the owner?
- Does the new knowledge layer prevent expensive rediscovery?
- Does the harness require less owner involvement?
- Are provenance and independence still preserved?

Retain:

- Rediscovery incidents.
- Estimated owner minutes per independent-review cycle.
- The existing bootstrap comparison as an initial reference point.

Avoid introducing a new metrics programme.

Review the evidence after meaningful use, not after every session.

If the knowledge layer is not reducing rediscovery or owner effort, simplify or remove the ineffective pieces.

## 13. H11 — Codex continuity and reviewer independence

**Disposition: ADOPT WITH ADDITIONAL APPLICABILITY DISCIPLINE.**

The revision 2 design substantially improves on the initial proposal.

Retain the sequence:

1. Codex receives an authoritative owner assignment.
2. Codex verifies the exact target and governing standards.
3. Codex reads only MAP's purpose, pillars and architectural context.
4. Codex fixes its independent test plan.
5. Codex reads the remaining knowledge context, past reviewer notes and the author's handoff.
6. Codex treats all authored claims as assertions requiring verification.

The test plan must not be shaped by Claude's summary of what should pass.

### Reviewer-owned knowledge

I support the proposed `reviews/knowledge/<review-id>.md` records.

These should preserve:

- Effective adversarial tests.
- Recurring defect classes.
- Known areas where the harness misled the reviewer.
- Verification methods worth reusing.
- Relevant limitations and scope.

They should not become a second standards register.

### Freshness and applicability

A finding from one revision may be:

- Still applicable.
- Remediated.
- Superseded by a standards change.
- Irrelevant to a new implementation.
- Historically useful but no longer operative.

Codex must distinguish these cases.

Previous reviewer notes should generate candidate probes and questions, not predetermine the verdict.

Each reviewer knowledge record should cite the review and applicable revision. Avoid silently presenting historical observations as current facts.

### Ownership and receipt

The author must not edit Codex's reviewer-owned knowledge.

Receive it byte-identically under the established review exchange mechanism.

The owner may distil relevant lessons into the shared knowledge layer, preserving provenance.

**Important:** H11 changes the review protocol and therefore belongs in Phase B, with independent Codex assessment before adoption.

## 14. T-0009: implementation implications and priority

The fixed implementation head `ce0c3b5` was assessed as NOT READY by Codex.

The independent review records seven open findings:

| Finding | Severity | Significance |
|---|---|---|
| F1 | High | Missing shared link can change the rights subject |
| F2 | High | Substituted link can authorise an unrelated dataset |
| F3 | Medium | Index comparisons silently omit periods |
| F4 | Medium | S1b releases cite inaccurate specifications |
| F5 | Medium | Dated RITS/NSW reference evidence is missing |
| F6 | High | Successful capture attempts omit required key/value checking evidence |
| F7 | Medium | Scheduled workflow and due-time gate are absent |

These are not minor documentation issues.

They affect:

- Provenance integrity.
- Enforcement of source rights.
- Reproducibility of factor construction.
- Accuracy of release specifications.
- Completeness of economic return comparisons.
- Point-in-time capture evidence.

The critical architectural point is that **HIO must produce economically meaningful and reproducible research artefacts before it can be trusted for multi-asset portfolio analysis**.

Passing synthetic tests is necessary but not sufficient when material negative cases remain untested.

### Remediation instruction remains unchanged

OD-0067 already authorises remediation.

Do not broaden or reinterpret that authorisation through harness-0.9.

Preserve the reviewed implementation head as evidence.

Continue remediation under the authorised branch and submit a new fixed head for independent review.

Do not combine harness-0.9 control changes with the T-0009 implementation.

### Point-in-time capture

The Year 1 charter identifies daily point-in-time capture as an early requirement.

Lost capture vintages cannot be recreated as originally observed.

This gives live capture readiness a genuine timing cost.

However, urgency does not justify bypassing:

- Per-dataset and per-operation source-rights verification.
- Storage and credential controls.
- Publication-time knowability rules.
- Required capture provenance.
- Explicit owner authorisation for live operation.

The correct response is to avoid nonessential delays, not to weaken the live-data gate.

## 15. Recommended sequencing

### Track 1 — T-0009 remediation: critical path

Claude continues the already-authorised seven-finding remediation.

Codex independently verifies the resulting fixed head.

Maintain exact revision identity and the existing review protocol.

Do not wait for harness-0.9 Phase A or Phase B.

### Track 2 — Harness-0.9 Phase A: low-risk knowledge changes

Subject to explicit owner approval, introduce:

- H1 — MAP.
- H2 — Findings index.
- H4 — Stream handoffs and practical rollover.
- H9 — Lightweight measurement.
- H3 — Current-state-only STATUS principles, without duplicating OD-0069.

Phase A should be documentation-only.

It should not change CI, approved review protocol, merge authority or owner-record requirements.

If Phase A competes for Claude's immediate capacity, defer it until the current remediation submission is ready.

If it can proceed independently and safely without diverting T-0009 work, parallel execution is acceptable.

The owner should not need another review cycle merely to receive navigation documents that do not change authority.

### Track 3 — Harness-0.9 Phase B: control improvements

After T-0009 remediation has been submitted, begin the consequential harness improvements incrementally.

Recommended order:

1. H6 — Scripted assignment and receipt.
2. H3 — Validated STATUS and MAP formatting checks.
3. H11 — Reviewer continuity.
4. H7 — Narrow standing administrative publication authority.
5. H5 — Reconsider after observing H6.
6. H8 — Hooks after primary repository controls.

This is a suggested order, not a new dependency chain requiring separate owner approvals for every small implementation step.

Use bounded standing authorisations where appropriate, with independent Codex verification for material control changes.

### Track 4 — Live capture readiness

Continue preparation for rights verification, cloud storage, network and credential controls and finality handling under their existing authority boundaries.

These are the prerequisites for a separate explicit live-operation decision.

Do not equate harness completion with live capture readiness.

## 16. What should be removed or avoided

Revision 2 already incorporates several useful reductions from the dry-run feedback.

Retain those simplifications.

Do not reintroduce:

- H10 as an independent governance item.
- A separate rediscovery log.
- A broad four-metric measurement programme.
- Repeated owner approval of mechanical navigation updates.
- Duplicated operational state between MAP and STATUS.
- Extensive copies of research outcomes in the engineering findings index.
- A second process for accepting Codex knowledge.
- Separate ceremonies for session rollover.
- Additional owner decisions where an existing standing authorisation already applies.

Avoid introducing a vector database, embeddings service or another persistent memory infrastructure at this stage.

The repository remains small enough for deterministic navigation, direct evidence retrieval and indexed search.

A more sophisticated retrieval mechanism should follow demonstrated failure of the simpler approach.

## 17. Expected proposal revision

Revise `docs/decisions/harness-0.9-proposal.md` into a coherent decision package reflecting the above conclusions.

The revision should:

**A. Preserve the motivating problem and baseline evidence.**

Retain the measurable evidence of governance overhead, lost engineering context, stale project state and cold-start limitations.

Do not exaggerate costs by treating all documentation as unproductive governance.

**B. Record OD-0069 as satisfying the already-executed repair.**

Avoid presenting the repaired STATUS inconsistency as a pending owner task.

**C. Clarify Phase A.**

Keep it documentation-only, with precise paths and no consequential changes to authority, CI or review protocol.

**D. Refine H7.**

Explicitly distinguish administrative publication of already-authorised decisions from consequential owner decisions.

**E. Retain H5 as deferred.**

Its justification must be reconsidered after H6 operates.

**F. Strengthen H11.**

Keep test-plan-first review independence, Codex ownership, immutable receipt and historical applicability controls.

**G. Make maintenance proportional.**

Separate substantive architectural changes from mechanical knowledge upkeep.

**H. Preserve T-0009 priority.**

Do not turn harness-0.9 into a prerequisite for remediation or a pretext for accepting work with unresolved findings.

**I. Preserve the authority hierarchy.**

Repository knowledge, including MAP and Settled findings, remains subordinate to approved owner decisions and standards.

**J. Specify rollback and success criteria.**

A successful Phase A should measurably improve fresh-session orientation and retrieval without increasing owner workload or changing accepted technical evidence.

## 18. Requested deliverable

Provide a revised architectural decision package and a concise response containing:

1. **Revision identity:** branch, exact head and files changed.
2. **Disposition table:** H1–H9 and H11, indicating adopt, modify, defer or reject.
3. **Architectural changes:** specifically explain what changed in H5, H7 and H11.
4. **Authority analysis:** show that no proposed standing delegation can create consequential authority.
5. **Sequencing:** demonstrate how T-0009 remediation proceeds independently.
6. **Outstanding owner decisions:** list only genuine choices that remain unresolved.
7. **Review requirements:** identify which changes require independent Codex verification.
8. **Remaining disagreements:** explicitly state where you disagree with this assessment and support the disagreement with repository evidence.

Do not mechanically agree with every recommendation. Challenge any architectural proposal that is unnecessarily complex, inconsistent with approved standards or incompatible with the actual repository.

Keep the response grounded in the fixed revisions and any newer evidence you can independently establish.

## 19. Execution boundaries and stop conditions

This handoff is **advice for preparing an owner decision**. It is not itself an instruction to execute the revised proposal.

Unless the owner explicitly authorises further work:

- Do not merge harness-0.9.
- Do not change approved authority rules.
- Do not implement H5–H8 or H11.
- Do not alter Codex's current review protocol.
- Do not amend the T-0009 implementation or remediation scope through this proposal.
- Do not broaden standing merge permissions.
- Do not convert proposal content into approved standards.
- Do not claim Phase A or Phase B has been accepted.

Stop and escalate if the proposed revision requires:

- A change to approved authority semantics.
- Relaxation of evidence or stop-on-mismatch controls.
- Changes to reviewer independence.
- A consequential merge without applicable owner approval.
- New permissions for provisioning, live data capture or source use.
- A scope change to T-0009.
- An unresolved contradiction between authoritative repository records.

Continue using the currently approved harness until a replacement is explicitly adopted.

## 20. Architectural direction

The principal constraint on HIO's development is not a shortage of policy documents. It is the need to build a trustworthy investment research system using limited owner attention and a small number of specialised agents.

The intended destination is a durable, independent, multi-asset research capability that can construct economically valid factor returns, maintain point-in-time evidence, analyse portfolio exposures, test hypotheses and ultimately support better capital-allocation decisions.

The harness is enabling infrastructure for that mission.

It should allow Claude to implement efficiently, Codex to challenge independently and the owner to exercise meaningful judgment at consequential boundaries.

**Optimise for retained knowledge, reliable evidence, independence and reduced owner effort—not maximum procedural coverage.**

Prepare the revised proposal accordingly, without expanding the scope into another major governance redesign.
