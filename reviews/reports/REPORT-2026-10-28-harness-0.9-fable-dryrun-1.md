---
id: REPORT-2026-10-28-harness-0.9-fable-dryrun-1
status: unverified_dry_run
owner: owner
reviewer: claude-fable-5-1 (same-vendor sub-agent)
target: 5f55cc79348304263378eb1d919856e45bda1f4f
base: eb19ef760fe3f03d47882e4a1aa8ab46df01486e
---

<!-- Transcribed by claude/implementation-agent from the sub-agent's final message. The sub-agent
could not write files (its Write tool refused report files), so this file is the receiver's
transcription of its returned text, not a byte-identical import. Content unchanged except this
comment; the YAML front matter was returned inside a code fence and is unfenced here. -->

# Harness-0.9 proposal: perform and review (unverified dry run)

> **Standing.** I am a Claude sub-agent reviewing Claude's work. Under operating model §10 ("Dry runs") this is an **unverified dry run**: advice, not an independent review, and it satisfies no review gate.
> - Role: reviewer (dry run). Work status: `proposed` (OD-0068).
> - Nothing in the repository was modified.
> - Paths are at `5f55cc7` unless stated; "main" means `eb19ef7`.

## 1. Verdict

**Adopt with changes.** The diagnosis is right, and the knowledge layer is worth having: MAP, the findings index, rolling handoffs and rollover at task boundaries (H1, H2, H4, H10). In this dry run the proposed path answered knowledge questions the current path could not, and read about 17% fewer words.

But four items touch controls in ways the proposal says they do not:
- **H5** drops the receipt OD that OD-0061 makes mandatory, and treats a self-declared commit trailer as owner evidence.
- **H7** relies on a "documentation-only lane" that does not exist. In effect it asks for a standing merge approval.
- **H8** puts its override where the agent it constrains can reach it.
- **H11** passes Codex's knowledge through the author, and shows Codex framing the author drafted before Codex fixes its test plan.

Three further problems:
- Phase A is not documentation-only: it includes CI changes and a change to the reviewer protocol.
- The seed MAP cites records that are not on `main`.
- MAP already repeats state that belongs in STATUS.

Fix these before approval.

## 2. Part A: cold-start results

### 2.1 Files read (word counts from `wc -w`)

| Path | Proposed run | Current run | Words | Bytes |
|---|---|---|---|---|
| `AGENTS.md` | ✓ | ✓ | 942 | 6,710 |
| `MAP.md` | ✓ | – | 859 | 5,788 |
| `STATUS.md` | ✓ | ✓ | 1,416 | 12,006 |
| `handoffs/2026-10-25-b2-receipt-and-exchange.md` (the newest handoff added on main, `fcc27c4`; main has no T-0009 or stream handoff) | ✓ | – | 382 | 2,704 |
| `knowledge/findings.md` | ✓ | – | 785 | 5,500 |
| `registers/tasks/T-0005-hio-s1-walking-skeleton.md` (main has no T-0009 card; this was the nearest) | – | ✓ | 613 | 5,283 |
| `reviews/README.md` | – | ✓ | 2,309 | 22,020 |
| **Total** | | | **4,384 / 5,280** | **32.7 KB (≈8k tokens) / 46.0 KB (≈11.5k tokens)** |

- Both runs then needed `docs/decisions/owner/OD-0067-*.md` (775 words) and `docs/decisions/README.md`.
- Both runs are well inside the 25k-token bootstrap budget in §12.
- The proposed run still read the old 1,416-word STATUS, because H3 is not applied.

### 2.2 The six §10 Claude questions (proposed run; the last column shows where the current run differs)

| # | Answer (source at `5f55cc7` unless stated) | Current run |
|---|---|---|
| 1 | `docs/decisions/owner/OD-*.md`, indexed in `docs/decisions/owner/README.md` (`AGENTS.md` rule 2; operating model §1.1) | same |
| 2 | Approved: ADR-0001…0009 at `a82aa0d` (OD-0008); 0010 rev 3 at `760f73e` (OD-0011); 0012 rev 3 (OD-0055) (`docs/decisions/README.md` l.40–49). None is proposed; 0011 was renumbered. **MAP has no ADR line**, so STATUS was still needed | same |
| 3 | S1a is accepted (OD-0042). S1b-1.0 (T-0009) is authorised for synthetic development only, not for live operation (MAP l.40–41). **The cited OD-0062 to OD-0065 and the T-0009 card are not on main**; only OD-0067 (`authorise_work`) is | **Misleading:** `STATUS.md` l.28 says "S1b is not authorised" and never mentions T-0009. T-0009 shows up only in `reviews/README.md` l.36, 57 and 124–130 |
| 4 | Without an owner instruction: drafts and handoffs only. T-0009 remediation is authorised (OD-0067), but its scope card exists only on the `impl/t0009-*` branches. Stop and flag | same, and STATUS l.48 lists stale agent actions |
| 5 | T-0009 F-1 to F-7 are open (`reviews/README.md` l.124–130). adr0012-1 and -3 are ambiguous (§2.4). Next action: T-0009 remediation (OD-0067) | **Wrong:** STATUS l.48 gives observations v0.3 and the run-1 stale lines. The newest handoff's next action (merge OD-0060) was already superseded by OD-0061 |
| 6 | HIO never writes SMSF truth and never imports `macsmsf`; HIO-001 is SMSF-owned (`AGENTS.md` Boundaries; ADR-0002, ADR-0003; MAP l.71) | same |

### 2.3 Knowledge questions

| Q | Proposed run | Current run |
|---|---|---|
| (a) T-0009 state and next action | NOT READY; 7 findings open; remediation authorised and not started (MAP l.40, l.63; OD-0067). MAP's "plan agreed" is unsupported. Neither path shows that `impl/t0009-remediation-1` already exists (at `ce0c3b5`, with no new commits) | Partial: findings and receipt come from `reviews/README.md`; the authority only via the OD-0067 link; STATUS contradicts both |
| (b) Why S1b specs must not reuse the S1a spec files | Reached: findings l.22 (file stem must equal `factor_id`, `tools/check_repo.py:163`) and l.31 (S1a `spec_ref` and release ids; OD-0042, OD-0067). The mechanism is stated imprecisely (DRY-14) | **Not reachable.** F-4 at `reviews/README.md` l.127 only hints at it |
| (c) Is any source right verified? | No (findings l.36; MAP l.55; `registers/sources.yaml`: 5 × `verification: unverified`) | No (STATUS l.38, l.84) |
| (d) Year 1 learning; has the PIT clock started? | Reached (MAP l.30–32 and l.45–47; charter §6): the clock has not started | **Not reachable.** The charter and roadmap are not on the read path |

**Comparison.**
- The proposed run read about 17% fewer words, answered (b) and (d), and got the S1b answer right. Its weakness is citing evidence a reader on main cannot open.
- The current run gave one **wrong** answer (the next action) and one **misleading** answer (S1b authorisation).
- Neither run could establish T-0009's scope from main.

### 2.4 Where MAP, STATUS, the findings file and the OD records disagree

1. **STATUS contradicts itself** on the HIO-ADR-0012 findings:
   - l.39 says "3 findings **open**";
   - l.47 says "technically verified closed, OD-0054";
   - `reviews/README.md` l.121 and l.123 say `remediation_claimed`.

   `findings.md` l.48 notes only the index-versus-OD gap.
2. STATUS (l.28, l.46–49) says S1b is not authorised and does not mention T-0009. MAP l.40 says S1b-1.0 is authorised for development, and OD-0067 on main is `authorise_work` for T-0009.
3. STATUS's OD snapshot stops at OD-0061 (`last_reviewed: 2026-10-25`). OD-0066 and OD-0067 are on main but missing from it.
4. MAP cites OD-0062 to OD-0065, the "T-0009 card" and `infra/tofu/README.md` (l.40, 41, 55, 77, 85, 86). None of these is on main; all exist only on `impl/t0009-shared-receipt-and-storage`.
5. MAP l.63 says "plan agreed". OD-0067 records an instruction, and the work is "not yet executed". No plan is recorded anywhere.
6. MAP l.30 calls the Year 1 outcome a "goal". Charter §6 calls the trajectory "a sequencing hypothesis… not a commitment", and MAP omits "risk of hypothetical portfolios explained by factors".
7. `findings.md` l.46 cites the proposal §1 as its source, which makes the citation circular.

## 3. Findings (most severe first)

**DRY-1 (high). H5's tier 2 conflicts with OD-0061 and with the evidence rule for owner confirmation.**
- Evidence:
  - Tier 2 includes "routine receipt under OD-0061" (l.158). OD-0061 ("Mandatory with every delegated receipt") requires "The receipt recorded in an OD", and that OD holds the table of checks 5.0 to 5.10.
  - A routine receipt has no owner words to put in an `Owner-Instruction:` trailer.
  - The operating model calls trailers "self-declared metadata… never proof" (l.364, l.376). Owner confirmation is a verbatim `docs/history/` file with its sha256, cited by an OD (l.367).
  - "Git keeps the quote immutable" (l.162) is equally true of a history file. What tier 2 actually loses is the verbatim context and the sha256 anchor.
  - A trailer on an unmerged or rebased branch is invisible to main.
  - "Documentation-only authorisations" could swallow review assignments, which §6.2 step 5.0.1 requires as a history file or an owner-committed row.
  - The proposal contradicts itself: l.153 and §9.2 say rule 2 is amended; l.160 says it is unchanged.
- Fix:
  - Exclude receipts and assignments from tier 2.
  - Make the tier-2 evidence a short verbatim history file, with its sha256 in the index row. The trailer is optional and extra.
  - List the OD-0061 amendment in §9.
  - Resolve the rule 2 contradiction.

**DRY-2 (high). H7 invents a merge authority.**
- Evidence:
  - H7 merges "through the existing documentation-only lane" (l.178). A grep of the operating model, `AGENTS.md` and all OD records finds no such lane.
  - §1.1 (l.88) and `AGENTS.md` rule 3 make approving a merge a separate, explicit owner action tied to a revision.
  - H7 is therefore a standing approval for a whole class of merges, while §3 claims the authority model does not change. Today these merges are ad hoc (OD-0067: "fix it now. get main sorted").
  - Risk: `proposed` cards (the T-0009 card says `status: proposed`) would sit on main next to authorised ones.
- Fix:
  - Make H7 an explicit tier-1 standing approval for a narrow class: OD files, history files and task cards only, with no code and no `reviews/` state.
  - List it in §9.
  - Require each card's status and authorising OD in its front matter.
  - STATUS names the code branch of each authorised item.

**DRY-3 (medium). The agent H8 constrains can reach its override.**
- Evidence:
  - The hooks live in `.claude/settings.json`, which the agent can edit, and which can also set `env`.
  - The env-var override is not checked against any OD (l.191).
  - A local hook cannot tell a "push to main outside the receipt tool" from an owner's push.
  - A regex for "network fetches from publishers" is bypassed by any Python client.
- Fix:
  - Put GitHub branch protection on `main` first.
  - Deny edits to `.claude/**` in PreToolUse.
  - Use overrides kept by the owner outside the repository, each naming an OD and an expiry.
  - Call the hooks defence in depth, not a control.

**DRY-4 (medium). H11 lets the author shape the reviewer's context and knowledge.**
- Evidence:
  - MAP and the Settled lines are drafted by Claude. The owner approves them from Claude's proposed placements (l.127–129).
  - MAP carries in-scope judgements ("plan agreed", "7 findings open") that Codex would read before its test plan. That inverts §2.2, under which author narrative is read last.
  - The receiver, often the author (OD-0067 "author-receiver"), copies Codex's *For the index* lines, and Claude then proposes where they go.
- Fix:
  - Before its test plan, Codex reads only MAP's purpose and architecture sections; the rest it reads afterwards.
  - Give Codex its own `reviews/knowledge/reviewer-notes.md`, written on its review branch and received byte-identically. The author does not edit it; the owner distils from it directly.
  - Require a real Codex review of H11 (§9.5 excludes it).

**DRY-5 (medium). Phase A is not documentation-only.**
- Evidence:
  - The line caps in H1 (120) and H3 (150 → 60) change `tools/check_repo.py` and CI.
  - H11 and the new bootstrap change the reviewer protocol.
  - OD-0068 excludes all of these.
- Fix: move the caps to Phase B, or name them as a tested tool change, and classify H11 as a control change.

**DRY-6 (medium). The seed MAP cannot be verified from main.**
- Evidence:
  - The off-main citations and "plan agreed" (§2.4 items 4 and 5).
  - l.72 and l.76 have no source; the source for l.76 is HIO-ADR-0012 l.160–165. Yet MAP l.12 claims "every line points to its source".
- Fix:
  - Mark off-main citations "(branch …, not on main)".
  - Add the two missing sources.
  - Change "plan agreed" to "owner instruction (OD-0067); no plan recorded".

**DRY-7 (medium). MAP already duplicates STATUS: the §8 drift risk has happened in the seed.**
- Evidence: "Where we are" (l.36–43) and the thread "State" column (l.61–67) restate operational state. Two of those cells are already wrong (DRY-6).
- Fix: MAP keeps purpose, pillars, architecture, and each thread's purpose with a pointer. State lives only in STATUS.

**DRY-8 (medium). The precedence rank is wrong.**
- Evidence:
  - MAP at "rank 3" (l.110) ranks a navigation summary above task cards (rank 4) and STATUS (rank 5).
  - §3 confirms only ranks 1, 2 and 5 as unchanged.
- Fix: MAP and the Settled lines go at rank 5 and the Inbox at rank 6, and the proposal says ranks 3, 4 and 6 are unchanged.

**DRY-9 (medium). H3 caps the wrong dimension.**
- Evidence: STATUS has 93 lines, and its longest line is 2,729 characters (both confirmed). The problem is line width, not line count. A 60-line cap still allows cells of 3,000 characters.
- Fix: add a line-width cap (for example 200 characters) and ban OD lists inside table cells.

**DRY-10 (medium). The findings index cites sources outside the repository.**
- Evidence:
  - "handover 2026-10-25 §0/§7", a file in `~/Downloads`, on l.22, 24, 25, 31 and 50.
  - "session 2026-10-28" on l.28.
  - The owner cannot check either at a distil.
- Fix: cite repository evidence instead, such as `tools/check_repo.py:163`, `src/hio/jobs/s1a.py:192-194` and OD-0058. Alternatively, import the relevant passages into `docs/history/` after a rights and secrets check.

**DRY-11 (medium). The owner decisions in §9 are incomplete.** Missing:
- the standing merge approval (DRY-2);
- the OD-0061 amendment (DRY-1);
- the Phase A CI changes (DRY-5);
- the reviewer-protocol change (DRY-4);
- who runs the distil, and how many owner minutes it costs;
- the boundary between the findings index and `registers/experiments.yaml`, which already has a "negative findings" field (§4). Without it, dead ends get two homes.

**DRY-12 (low). Some §1 numbers are off by one or mix bases.**

| Claim | Measured |
|---|---|
| OD records / history files / review records: 64 / 70 / 23 | 63 / 69 / 22. Each count included a `README.md`; the 22 include 2 HARNESS records |
| 47 handoffs | correct |
| 208 commits on main | correct (168 non-merge) |
| 186 non-merge commits across refs, 37 touching code | correct |
| ≈28,500 docs lines vs ≈11,700 code lines | correct across all refs (28,573 / 11,695). On main they are 26,784 / 9,230 |
| Docs lines as overhead | Overstated: the docs total includes substantive work (standards 2,600, evidence 1,003, research 870 lines) |
| 8,440 words / 3,012 words | correct |
| 4 hypotheses / 0 experiments | correct |
| 21 seed lines | correct |

Fix: correct the counts, state the base of each, and separate governance records from substantive documents.

**DRY-13 (low). Some claims are overstated.**
- "A grep finds none": `git grep` does find lessons, for example OD-0058 ("nothing local would have caught it") and `handoffs/2026-10-18-t0007-…` ("caught only indirectly").
- "Nobody has caught it in a false approval claim" has no support.
- `findings.md` l.43 says "repeatedly" but cites a single review.
- Fix: say "lessons are scattered; there is no class or index for them".

**DRY-14 (low). `findings.md` l.31 states the mechanism imprecisely.**
- Evidence: `spec_ref = factor_id@identity.version` (`src/hio/jobs/s1a.py:192-194`). Editing a spec changes `spec_ref` only through a version bump, and an edit without a bump is a silent spec change. The real reason is F-4.
- Fix: reword the line and cite both the code and F-4.

**DRY-15 (low). H4's rolling files are mutable and will conflict between `impl/*` branches and main.**
- Evidence: they also lose the append-only property handoffs have now.
- Fix: write one file per session under `handoffs/<stream>/`, or edit rolling files only on main.

**DRY-16 (low). H9 has no baseline and relies on agents reporting their own rediscoveries.**
- Evidence: agents rarely notice when they rediscover something, and owner minutes per review cycle are not measured today.
- Fix: take a baseline now (this report's bootstrap figures are a start), and let the owner and Codex log incidents. Replace `rediscovery.md` with a `[rediscovery]` tag in the inbox.

**DRY-17 (low). A local path is now in a public repository.**
- Evidence: the history file commits `/Users/elusivenode/Downloads/...`, which contains the username (l.11).
- Fix: the file must stay verbatim, so this is for the owner's awareness only.

**Checked and correct:**
- the history file's sha256 (`fcdbf8d…`) matches OD-0068;
- the commit's 8 files are within OD-0068's scope;
- the F-1 to F-3 lines match the review record (l.39–45);
- `check_public` and the trailer check match `tools/check_repo.py` (l.242–260, l.364).

## 4. Recommended changes to the proposal

1. **H5:** exclude receipts and review assignments from tier 2. Make the tier-2 evidence a short history file with its sha256 in the index row, and the trailer optional and extra. Fix the rule 2 contradiction.
2. **H7:** make it an explicit, narrow, tier-1 standing merge approval, listed in §9.
3. **H8:**
   - branch protection on `main` first;
   - deny edits to `.claude/**`;
   - overrides kept by the owner, naming an OD, with an expiry;
   - call it defence in depth.
4. **H11:**
   - Codex reads only MAP's purpose and architecture before its test plan;
   - a Codex-owned `reviews/knowledge/` file, received byte-identically;
   - a real Codex review of H11.
5. Move the CI caps out of Phase A, or name them as tool changes.
6. Strip operational state from MAP; fix its off-main and missing citations and "plan agreed".
7. Put MAP and the Settled lines at precedence rank 5, and the Inbox at rank 6.
8. Add a line-width cap to H3.
9. Re-source the findings lines to repository evidence, and reword l.31.
10. Complete §9, and correct the §1 numbers and the overstated claims.
11. Use per-session files under `handoffs/<stream>/`. Fold H9 into the inbox and take a baseline now.
12. **Sequencing.** What should come first is one bounded owner instruction to bring OD-0062 to OD-0065 and the T-0009 card to main and rewrite STATUS. That fixes today's contradiction without waiting for harness-0.9. Then:
    1. H1 and H2, corrected;
    2. H3 and H4;
    3. H6 before H5, because mechanising receipt may remove most of the record cost that motivates tier 2;
    4. H8 last.

    None of this should delay T-0009 remediation; the PIT capture clock (MAP l.45–47) is the real constraint.
13. **Cut as ceremony:**
    - H10 as a separate item (it is one practice line in H4);
    - `knowledge/rediscovery.md` (use a tag instead);
    - the four-metric H9 review (keep rediscovery incidents and owner minutes);
    - the *Surprised by* heading (fold it into *For the index*).

## 5. What I did not check

- I ran no tests, `check_repo.py`, CI or hooks, and did not test whether Claude Code hooks can enforce H8 as described.
- I did not read the `~/Downloads` source or the 2026-10-25 handover, so claims cited to them are unverified.
- I read the operating model only in part: §1, §1.1, §2.2, §4, §6.2 step 5.0, and §10 to §12. I did not read every OD from OD-0053 to OD-0061.
- There was no Codex cold start. Independence is untested, and the §10 Codex run is still pending.
- Token figures are estimated as bytes ÷ 4.
- As a same-vendor reviewer I may share the author's blind spots.
