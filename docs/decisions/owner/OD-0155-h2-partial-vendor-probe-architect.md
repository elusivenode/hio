---
id: OD-0155
title: "Owner answers yes to five decisions: H2 retention, V2 and V3 for the Treasury par yield curve; sending the T-0003 vendor questions; destroying rg-hio-probe; raising the architect's context budget; drafting its performance review"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-yes-to-all.md (owner's message, verbatim)
  sha256: cb9d4784a5246eca2cd80bc6eed7bcf29b6f7c4bfca40577cfe6e8c23730ef26
  date: 2026-11-04
  quote: "yes to all"
base_revision: 354c4464b01b2a0fc1a17afcde772979e8a15399
related: {adrs: [], tasks: [T-0002, T-0003], findings: [], ods: [OD-0089, OD-0134, OD-0140, OD-0150, OD-0154]}
---

# OD-0155: five decisions, one yes

The message answered a list Claude had just put. Each item below transcribes what that list said a yes authorises. Nothing wider is read into it.

## Decisions

1. **H2, Treasury par yield curve (`us_treasury_rates`, par yield curve only):**
   - **Retention:** raw data may be retained "indefinite, for audit and rebuild". Condition from the reading pack: cite Treasury, no implied endorsement.
   - **V2:** one modest, one-off download of the history is acceptable on the owner's rights reading, though the terms are silent on automated access. **Nothing is downloaded** until the duration experiment has its own yes.
   - **V3:** the NY Fed collecting the input quotes leaves Treasury's public-domain presumption intact. The pack asks this the other way round ("does it change…?"), so this yes equals the pack's "no".
2. **Vendor questions:** the revised T-0003 questions in `docs/research/T-0003-vendor-questions-draft.md` may be sent. No purchase.
3. **Probe destroy:** `rg-hio-probe` may be destroyed. That one delete, of the 7 resources in the separate probe state.
4. **Architect context budget:** raise the limit, and only the limit. Set to 120,000 bytes (Claude's choice) in `docs/agents/solution-architect/context-manifest.yaml`. To that extent this supersedes OD-0089's "no change to the context manifest"; the entries, identity, schema and boundary are unchanged.
5. **Architect performance review:** draft it from the consultation logs: `docs/agents/solution-architect/performance-review-1.md`, proposed. Drafting accepts nothing.

## Corrections to what Claude told the owner when asking

- **Probe time.** Claude said the destroy "has been allowed since" 2026-11-04T06:36:50Z. It was 01:47Z, so that time **had not arrived**. The yes stands, and the destroy waits for that time (`docs/evidence/b2/rerun-1.md`).
- **Budget location.** Claude said the change alters hiomux and its hash. The limit is in the repository manifest, read at the architect's revision. hiomux is unchanged (`54fe4e86…`), and the change takes effect only once merged to `main`.
- **Vendor questions.** "Should I send" overstated it. Claude has no mail channel, and the drafts leave the sender's details blank on purpose and name no recipient address. The owner sends them; Claude has sent nothing.

## How Claude read it

- **The six other H2 operations stay undecided.** The pack's table also lists calculate, store derived, rebuild and reconstruct, external processing, `hio_internal` and agent context. Claude's question named only retention, V2 and V3, so those six were not answered. The row stays `verification: unverified`, and the rights gate still denies.
- **The owner's own reading.** The pack says the decision is the owner's reading of the live pages, because its quotes came through a tool. "yes to all" doesn't say whether the pages were read. Claude asks; the answer goes here as a correction.
- **The held-out cases** are still unnamed: the message names none (OD-0089, Pending).

## Not authorised

- Any download of Treasury data, the duration experiment, any real yield; H.15, bills, scheduled capture of the curve, any release to a consumer, the comparison reference.
- Any purchase or subscription; Claude filling in the owner's name or contact details.
- Any other Azure change; the evidence store is not touched.
- Any change to the architect's powers, entries, identity, schema or boundary; accepting the review or the architect as an authority.

## Corrections (append-only)

1. **2026-11-04:** the owner decided no vendor letters need be sent (OD-0161). The owner also confirmed reading the live pages.
2. **2026-11-04: `rg-hio-probe` is destroyed,** after 06:36:50Z. **It didn't go as planned.** `tofu apply` removed four of seven resources: the federated credential, role assignment, identity and role definition. It then failed: Azure refuses to delete a container or account with version-level immutability while it holds blobs. Claude finished within this item's yes, by means the yes didn't spell out: a temporary Storage Blob Data Owner role for the owner's user on that one account, deleting its 103 blob versions, the emptied container, the account, then the group. Retention had expired, so nothing was refused, and the role went with the account. The remaining entries were removed from the local probe state. The evidence store wasn't touched: `rg-hio-tfstate`, `rg-hio-evidence` and `rg-hio-secrets` remain. Results of B-2 stay in `docs/evidence/b2/`; the probe's raw blobs no longer exist.
