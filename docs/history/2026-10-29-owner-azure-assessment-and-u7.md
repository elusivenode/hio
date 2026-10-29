<!-- The owner's messages to Claude Code, 2026-10-29, verbatim, with the decisions Claude put. Recorded by OD-0117 and OD-0116 correction 1. -->

**Message AM**

what is the Azure SDK question.  we have a lot of terraform IAC work to do.  you have yet to assess infra in the sub we a targeting via az

**Claude's decisions put** (as put, verbatim)

1. **Read-only `az` assessment of `hnf-prod`?** A yes authorises me to use your existing `az` login for read-only commands only. That means listing or showing:
   - the account and subscription, resource groups, resources and storage accounts;
   - role assignments, policy assignments, locks, resource providers and diagnostic settings;
   - existing Entra apps and their federated credentials.

   The raw output stays in my scratchpad and is never committed. The repository is public, so only a summary with no ids, tenant details or names beyond `hnf-prod` goes into it. A yes does not authorise any create, update, delete or login change, or any `tofu` command against Azure.

2. **`tofu init -backend=false` and `tofu validate`?** These download the azurerm provider from the OpenTofu registry and check the definitions offline. A yes authorises those two commands and committing `.terraform.lock.hcl` with its provider hashes. It does not authorise `plan`, `apply`, a state backend or any Azure call.

3. **A new task card for the IaC (T-0011)?** A yes authorises me to draft T-0011 from what the assessment and validation find, covering remote state, the evidence store, identities, Environment protection, alerting and the second copy. Applying it stays Authorisation B.

4. **Azure SDKs (option A)**, as asked before. A yes authorises adding the two libraries, hash-locked, with imports allowed only in the backend modules, and a worker task to build and test the backend against fakes.

5. **U7, as asked before.** Have you read the live RBA and NY Fed terms yourself, and do they support the answers you adopted? Until you say yes, the rights gate keeps refusing D1, D2, D3, D8 and D9.

**Message AN**

yes to all.
