---
id: OD-0164
title: "Owner instructs an Azure Key Vault for the EODHD key; one small vault created in hnf-prod, the key only"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-key-vault.md (owner's message, verbatim)
  sha256: 922f6eff4ab1b9c41b5f5150c1b7549e9a50cd0d39b2057fc27e00142241d924
  date: 2026-11-04
  quote: "saved/  set up az kv for this"
base_revision: 183d6d3e3dd62393bb195a2ca4ec80fa3d67f4c0
related: {adrs: [], tasks: [T-0022], findings: [], ods: [OD-0162, OD-0163]}
---

# OD-0164: a key vault for the EODHD key

This owner instruction overrides, for this one vault, OD-0162's "no new Azure service". The work is bounded and reversible.

**Done 2026-11-04:** resource group `rg-hio-secrets` in `hnf-prod`, australiaeast, with one vault: standard SKU, RBAC authorisation, soft delete 7 days, no purge protection, so it can be removed after the evaluation. The owner's user holds Key Vault Secrets Officer at vault scope. One secret, `eodhd-api-key`, copied from the keychain by pipe and verified by hash; its value was never printed. The vault's name is held locally, in `vault-name` in the evaluation workspace. Created with `az`, not OpenTofu, because it is short-lived and shares nothing with the evidence store.

## How Claude read it

- **Dedicated, not shared.** The platform vault in `hnf-dev` wasn't used, to keep HIO's boundary. `hnf-prod` holds HIO's other resources. These were Claude's choices.
- **The vault holds a credential, not data.** `external_processing` stays denied for `eodhd.personal_evaluation`, and licensed data stays on the owner's Mac.
- **Public network access is on,** protected by RBAC, because the Mac's address isn't fixed.
- **The keychain copy is left in place** for the owner to delete. The tool reads only the vault.

## Not authorised

Any other Azure change, CI access to the key, or any use of the evidence store.

## Corrections (append-only)
