<!-- The owner's message to Claude Code, 2026-10-29, verbatim, with the decisions Claude put. Recorded by OD-0125. -->

**Claude's decisions put** (as put, verbatim)

1. **Receive it?** A yes authorises the receipt by PR, with the same steps as before, and the §5.12 update setting t0011 F-2 to `verified_closed`. All five findings from the two reviews would then be closed.

2. **Accept T-0011 at `c69df9e`?** This applies once decision 1's receipt is complete. A yes records your acceptance of T-0011 at `c69df9e982a81e87a8fdb208ba4c66771b9664d5` and merges PR #8 (`infra/t0011`) into `main`. Nothing is applied in Azure.

3. **Then B-1, the infrastructure?** This applies after decision 2. A yes authorises me, in this terminal with your `az` login and `--subscription hnf-prod` on every command, to:
   - register `Microsoft.Insights`, `Microsoft.OperationalInsights` and `Microsoft.AlertsManagement`;
   - run the state bootstrap: `init`, then `plan`, which I show you; then `apply` only after your "go", with the state kept outside the repository;
   - run the evidence store the same way, with its own plan and its own "go";
   - set the four `capture` Environment variables.

   You type the values that must never be committed: the GitHub numeric ids for the OIDC subject, your object id, your alert email and the state directory. A yes does **not** authorise any data capture, B-2, B-3, setting `LIVE_AUTHORISATION` or moving the workflow. Until anything is written to the store, everything B-1 creates can be removed with `tofu destroy`.

**Message AY**

Yes to all
