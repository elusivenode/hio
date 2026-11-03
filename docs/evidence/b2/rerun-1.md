---
id: HIO-EVIDENCE-B2-RERUN-1
title: "B-2 re-run and step 7b: retained report and first reading"
status: draft            # evidence plus Claude's first reading; the interpretation is for the owner
owner: HIO architecture lead (owner); prepared by claude/implementation-agent
created_at: 2026-11-03
instruction: OD-0140 (R-1, R-2, 7b), with its correction 1
---

# B-2 re-run and step 7b

**Run:** GitHub Actions run `41590213489`, workflow `storage-probe`, dispatched at `main` `35edd32` with `repeats=50`, approved by the owner
in the `capture` Environment. It finished `failure` because the C5 rule as written fails, which is the expected reading below. The report
is kept verbatim at the end of this file, sha256 `0a514b60d73bde761ec76361be23b21862df638188c3592a2bbb259f48f00ad8`, as downloaded from the run artifact. It ends with a newline.

## The re-run

| Check | Result |
|---|---|
| Create a fresh key | pass |
| Conditional create of the same key | pass: **`BlobExists`**, so the T-0015 mapping works against Azure |
| Overwrite by the writer | refused, 403 `UnauthorizedBlobOverwrite` (an RBAC refusal) |
| Delete by the writer | refused, 403 `AuthorizationPermissionMismatch` (an RBAC refusal) |
| One version per key | pass |
| C5 as written, `completed_at ≤ s ≤ completed_at + δ` | **45 of 50 violations.** `s − completed_at` is −847 to +59 ms, median −394 ms |
| Candidate, `floor_s(completed_at) ≤ s ≤ completed_at + δ` | **0 of 50 violations** |
| Errors; missing headers | 0; 0 |

**Derived from the report by Claude (not fields in it), over all 50 records:**

| Measure | Result |
|---|---|
| `s` equals `x-ms-version-id` floored to the second | 50 of 50 |
| `completed_at ≤ x-ms-version-id` | 50 of 50; the difference is 67.6 to 76.2 ms, median 68.4 ms |
| `x-ms-version-id` before `post_put` | 50 of 50; by 82.6 to 100.2 ms |
| PUT duration | 151 to 170 ms |

## First reading (Claude; not a decision)

- **`Last-Modified` flooring explains the failure.** With `completed_at` taken before the write, as HIO-ADR-0012 defines it, the write landed
  after it every time. This run's `completed_at` is a surrogate taken immediately before the PUT, not a real publisher body read.
- **There may be two ways to resolve C5:** loosen the rule to the floored candidate, or keep the rule and take the witness from
  `x-ms-version-id`. The second satisfied the unamended inequality 50 of 50. **Not established:** whether Azure guarantees that a version id
  means write time. Each is an HIO-ADR-0012 change and an owner decision. Per OD-0139, it no longer gates B-3.
- **`Date` is unexplained.** The bounds (−889 to −649 ms) assume `Date` was generated between `pre_put` and `post_put`, yet `Date` ran up to
  about a second behind the version id. They may reflect how `Date` is produced, not clock skew.
- **One region, one runner, one 15-second burst.** This is not a distribution over time.

## Step 7b (2026-11-03, on `probe/20261103T063128Z-36b82702/1`, retained version `2026-11-03T06:31:31.0458245Z`)

The role was `Storage Blob Data Owner` on container `probe` only, because `Storage Blob Data Contributor`, as the plan named, has no
`blobs/deleteBlobVersion/action`. Its refusal would have proved nothing about immutability. The account's policy read back as enabled,
Unlocked, one day.

| Step | Result |
|---|---|
| Owner granted the role with their own login | done; read back as `Storage Blob Data Owner` |
| Delete the retained version (SDK `delete_blob(version_id=…)`) | **refused: HTTP 409 `BlobImmutableDueToPolicy`**, "This operation is not permitted as the blob is immutable due to a policy." |
| Upload different bytes to the same key | **succeeded**, creating a new current version `2026-11-03T06:36:50.1931024Z` (43 bytes) |
| Versions afterwards | the retained version (30 bytes) is still present, and no longer current |
| Retained version's bytes, before and after | identical, sha256 `6273378d3c72aad4e6ddca46d277a2b932157e533cbfc33531261c7d593a3889` |
| Role removed | done; 0 assignments at that scope on read-back, 2026-11-03T06:37:31Z |

**Reading.** Within its retention period, a retained version is protected against a principal holding delete rights, under an **Unlocked**
policy. Three limits:
- **An overwrite does not fail for a privileged actor.** It adds a new current version, so anything reading "current" sees the new bytes. The
  write-once claim rests on RBAC for the writer, and on version ids plus byte comparison.
- **Not tested:** removing or shortening an Unlocked policy, deleting the account or resource group, or a period longer than one day. An
  Unlocked policy can be changed by someone with management rights, and locking it is a later owner decision (OD-0119).
- **Probe account only.** The evidence account has the same design, but was not touched.

**Earliest destroy:** 2026-11-04T06:36:50Z, 24 hours after the last write. It needs its own "go".

## The report (verbatim)

```json
{
  "run_id": "20261103T063128Z-36b82702",
  "started_at": "2026-11-03T06:31:28.975341+00:00",
  "account_host": "hioprobehoue.blob.core.windows.net",
  "passed": false,
  "results": [
    {
      "check": "create_fresh_key",
      "passed": true,
      "detail": "created probe/20261103T063128Z-36b82702/1 as version 2026-11-03T06:31:31.0458245Z"
    },
    {
      "check": "create_again_raises_blob_exists",
      "passed": true,
      "detail": "BlobExists for probe/20261103T063128Z-36b82702/1"
    },
    {
      "check": "overwrite_refused",
      "passed": true,
      "detail": "overwrite of probe/20261103T063128Z-36b82702/1 refused: HttpResponseError HTTP 403 UnauthorizedBlobOverwrite"
    },
    {
      "check": "delete_refused",
      "passed": true,
      "detail": "delete of probe/20261103T063128Z-36b82702/1 refused: HttpResponseError HTTP 403 AuthorizationPermissionMismatch"
    },
    {
      "check": "exactly_one_version",
      "passed": true,
      "detail": "one version of probe/20261103T063128Z-36b82702/1: 2026-11-03T06:31:31.0458245Z"
    },
    {
      "check": "c5_timing",
      "passed": false,
      "detail": {
        "repeats": 50,
        "delta_seconds": 600.0,
        "tolerance": "none",
        "violations": 45,
        "errors": 0,
        "min_diff_ms": -846.98,
        "max_diff_ms": 59.216,
        "rules": {
          "existing": {
            "rule": "completed_at <= s <= completed_at + delta",
            "violations": 45
          },
          "candidate": {
            "rule": "floor_s(completed_at) <= s <= completed_at + delta",
            "violations": 0
          },
          "tolerance": "none"
        },
        "offset_bounds_ms": {
          "observations_with_bracket": 50,
          "lower_max": -889.245,
          "upper_min": -649.464
        },
        "clock_sync": {
          "available": true,
          "NTP": "yes",
          "NTPSynchronized": "yes",
          "TimeUSec": "Tue 2026-11-03 06:31:47 UTC",
          "Timezone": "Etc/UTC"
        },
        "observations": [
          {
            "key": "probe/20261103T063128Z-36b82702/2",
            "completed_at": "2026-11-03T06:31:32.019393+00:00",
            "s": "2026-11-03T06:31:32.000000+00:00",
            "diff_ms": -19.393,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/3",
            "completed_at": "2026-11-03T06:31:32.323038+00:00",
            "s": "2026-11-03T06:31:32.000000+00:00",
            "diff_ms": -323.038,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/4",
            "completed_at": "2026-11-03T06:31:32.623192+00:00",
            "s": "2026-11-03T06:31:32.000000+00:00",
            "diff_ms": -623.192,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/5",
            "completed_at": "2026-11-03T06:31:32.940784+00:00",
            "s": "2026-11-03T06:31:33.000000+00:00",
            "diff_ms": 59.216,
            "within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/6",
            "completed_at": "2026-11-03T06:31:33.241009+00:00",
            "s": "2026-11-03T06:31:33.000000+00:00",
            "diff_ms": -241.009,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/7",
            "completed_at": "2026-11-03T06:31:33.542429+00:00",
            "s": "2026-11-03T06:31:33.000000+00:00",
            "diff_ms": -542.429,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/8",
            "completed_at": "2026-11-03T06:31:33.842224+00:00",
            "s": "2026-11-03T06:31:33.000000+00:00",
            "diff_ms": -842.224,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/9",
            "completed_at": "2026-11-03T06:31:34.142944+00:00",
            "s": "2026-11-03T06:31:34.000000+00:00",
            "diff_ms": -142.944,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/10",
            "completed_at": "2026-11-03T06:31:34.446039+00:00",
            "s": "2026-11-03T06:31:34.000000+00:00",
            "diff_ms": -446.039,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/11",
            "completed_at": "2026-11-03T06:31:34.745076+00:00",
            "s": "2026-11-03T06:31:34.000000+00:00",
            "diff_ms": -745.076,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/12",
            "completed_at": "2026-11-03T06:31:35.045918+00:00",
            "s": "2026-11-03T06:31:35.000000+00:00",
            "diff_ms": -45.918,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/13",
            "completed_at": "2026-11-03T06:31:35.349916+00:00",
            "s": "2026-11-03T06:31:35.000000+00:00",
            "diff_ms": -349.916,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/14",
            "completed_at": "2026-11-03T06:31:35.649045+00:00",
            "s": "2026-11-03T06:31:35.000000+00:00",
            "diff_ms": -649.045,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/15",
            "completed_at": "2026-11-03T06:31:35.948819+00:00",
            "s": "2026-11-03T06:31:36.000000+00:00",
            "diff_ms": 51.181,
            "within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/16",
            "completed_at": "2026-11-03T06:31:36.247638+00:00",
            "s": "2026-11-03T06:31:36.000000+00:00",
            "diff_ms": -247.638,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/17",
            "completed_at": "2026-11-03T06:31:36.547115+00:00",
            "s": "2026-11-03T06:31:36.000000+00:00",
            "diff_ms": -547.115,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/18",
            "completed_at": "2026-11-03T06:31:36.846980+00:00",
            "s": "2026-11-03T06:31:36.000000+00:00",
            "diff_ms": -846.98,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/19",
            "completed_at": "2026-11-03T06:31:37.146159+00:00",
            "s": "2026-11-03T06:31:37.000000+00:00",
            "diff_ms": -146.159,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/20",
            "completed_at": "2026-11-03T06:31:37.446419+00:00",
            "s": "2026-11-03T06:31:37.000000+00:00",
            "diff_ms": -446.419,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/21",
            "completed_at": "2026-11-03T06:31:37.747328+00:00",
            "s": "2026-11-03T06:31:37.000000+00:00",
            "diff_ms": -747.328,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/22",
            "completed_at": "2026-11-03T06:31:38.046895+00:00",
            "s": "2026-11-03T06:31:38.000000+00:00",
            "diff_ms": -46.895,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/23",
            "completed_at": "2026-11-03T06:31:38.345231+00:00",
            "s": "2026-11-03T06:31:38.000000+00:00",
            "diff_ms": -345.231,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/24",
            "completed_at": "2026-11-03T06:31:38.645359+00:00",
            "s": "2026-11-03T06:31:38.000000+00:00",
            "diff_ms": -645.359,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/25",
            "completed_at": "2026-11-03T06:31:38.944017+00:00",
            "s": "2026-11-03T06:31:39.000000+00:00",
            "diff_ms": 55.983,
            "within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/26",
            "completed_at": "2026-11-03T06:31:39.242748+00:00",
            "s": "2026-11-03T06:31:39.000000+00:00",
            "diff_ms": -242.748,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/27",
            "completed_at": "2026-11-03T06:31:39.542143+00:00",
            "s": "2026-11-03T06:31:39.000000+00:00",
            "diff_ms": -542.143,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/28",
            "completed_at": "2026-11-03T06:31:39.840932+00:00",
            "s": "2026-11-03T06:31:39.000000+00:00",
            "diff_ms": -840.932,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/29",
            "completed_at": "2026-11-03T06:31:40.140237+00:00",
            "s": "2026-11-03T06:31:40.000000+00:00",
            "diff_ms": -140.237,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/30",
            "completed_at": "2026-11-03T06:31:40.438653+00:00",
            "s": "2026-11-03T06:31:40.000000+00:00",
            "diff_ms": -438.653,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/31",
            "completed_at": "2026-11-03T06:31:40.737635+00:00",
            "s": "2026-11-03T06:31:40.000000+00:00",
            "diff_ms": -737.635,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/32",
            "completed_at": "2026-11-03T06:31:41.036680+00:00",
            "s": "2026-11-03T06:31:41.000000+00:00",
            "diff_ms": -36.68,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/33",
            "completed_at": "2026-11-03T06:31:41.335367+00:00",
            "s": "2026-11-03T06:31:41.000000+00:00",
            "diff_ms": -335.367,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/34",
            "completed_at": "2026-11-03T06:31:41.649463+00:00",
            "s": "2026-11-03T06:31:41.000000+00:00",
            "diff_ms": -649.463,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/35",
            "completed_at": "2026-11-03T06:31:41.948381+00:00",
            "s": "2026-11-03T06:31:42.000000+00:00",
            "diff_ms": 51.619,
            "within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/36",
            "completed_at": "2026-11-03T06:31:42.246769+00:00",
            "s": "2026-11-03T06:31:42.000000+00:00",
            "diff_ms": -246.769,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/37",
            "completed_at": "2026-11-03T06:31:42.545517+00:00",
            "s": "2026-11-03T06:31:42.000000+00:00",
            "diff_ms": -545.517,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/38",
            "completed_at": "2026-11-03T06:31:42.844547+00:00",
            "s": "2026-11-03T06:31:42.000000+00:00",
            "diff_ms": -844.547,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/39",
            "completed_at": "2026-11-03T06:31:43.143056+00:00",
            "s": "2026-11-03T06:31:43.000000+00:00",
            "diff_ms": -143.056,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/40",
            "completed_at": "2026-11-03T06:31:43.441818+00:00",
            "s": "2026-11-03T06:31:43.000000+00:00",
            "diff_ms": -441.818,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/41",
            "completed_at": "2026-11-03T06:31:43.740923+00:00",
            "s": "2026-11-03T06:31:43.000000+00:00",
            "diff_ms": -740.923,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/42",
            "completed_at": "2026-11-03T06:31:44.047487+00:00",
            "s": "2026-11-03T06:31:44.000000+00:00",
            "diff_ms": -47.487,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/43",
            "completed_at": "2026-11-03T06:31:44.347108+00:00",
            "s": "2026-11-03T06:31:44.000000+00:00",
            "diff_ms": -347.108,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/44",
            "completed_at": "2026-11-03T06:31:44.645798+00:00",
            "s": "2026-11-03T06:31:44.000000+00:00",
            "diff_ms": -645.798,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/45",
            "completed_at": "2026-11-03T06:31:44.944757+00:00",
            "s": "2026-11-03T06:31:45.000000+00:00",
            "diff_ms": 55.243,
            "within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/46",
            "completed_at": "2026-11-03T06:31:45.244370+00:00",
            "s": "2026-11-03T06:31:45.000000+00:00",
            "diff_ms": -244.37,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/47",
            "completed_at": "2026-11-03T06:31:45.544138+00:00",
            "s": "2026-11-03T06:31:45.000000+00:00",
            "diff_ms": -544.138,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/48",
            "completed_at": "2026-11-03T06:31:45.844484+00:00",
            "s": "2026-11-03T06:31:45.000000+00:00",
            "diff_ms": -844.484,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/49",
            "completed_at": "2026-11-03T06:31:46.144229+00:00",
            "s": "2026-11-03T06:31:46.000000+00:00",
            "diff_ms": -144.229,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/50",
            "completed_at": "2026-11-03T06:31:46.443484+00:00",
            "s": "2026-11-03T06:31:46.000000+00:00",
            "diff_ms": -443.484,
            "within": false
          },
          {
            "key": "probe/20261103T063128Z-36b82702/51",
            "completed_at": "2026-11-03T06:31:46.742878+00:00",
            "s": "2026-11-03T06:31:46.000000+00:00",
            "diff_ms": -742.878,
            "within": false
          }
        ],
        "timing_records": [
          {
            "key": "probe/20261103T063128Z-36b82702/2",
            "completed_at_surrogate": "2026-11-03T06:31:32.019393+00:00",
            "pre_put": "2026-11-03T06:31:32.019396+00:00",
            "post_put": "2026-11-03T06:31:32.171589+00:00",
            "post_metadata": "2026-11-03T06:31:32.322956+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 152.19546200000167,
              "post_put_to_post_metadata": 151.36703600000345,
              "surrogate_to_post_metadata": 303.5631730000006
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:31 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:32 GMT",
              "x-ms-version-id": "2026-11-03T06:31:32.0878021Z",
              "x-ms-request-id": "edb05e79-b01e-00e6-7a5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1171.589,
              "upper": -19.396
            },
            "floor_s_completed_at": "2026-11-03T06:31:32.000000+00:00",
            "s": "2026-11-03T06:31:32.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/3",
            "completed_at_surrogate": "2026-11-03T06:31:32.323038+00:00",
            "pre_put": "2026-11-03T06:31:32.323040+00:00",
            "post_put": "2026-11-03T06:31:32.475159+00:00",
            "post_metadata": "2026-11-03T06:31:32.623114+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 152.12180700000033,
              "post_put_to_post_metadata": 147.95589100000228,
              "surrogate_to_post_metadata": 300.0783399999989
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:31 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:32 GMT",
              "x-ms-version-id": "2026-11-03T06:31:32.3906329Z",
              "x-ms-request-id": "edb05f23-b01e-00e6-0e5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1475.159,
              "upper": -323.04
            },
            "floor_s_completed_at": "2026-11-03T06:31:32.000000+00:00",
            "s": "2026-11-03T06:31:32.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/4",
            "completed_at_surrogate": "2026-11-03T06:31:32.623192+00:00",
            "pre_put": "2026-11-03T06:31:32.623193+00:00",
            "post_put": "2026-11-03T06:31:32.792677+00:00",
            "post_metadata": "2026-11-03T06:31:32.940723+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 169.48640100000034,
              "post_put_to_post_metadata": 148.04620799999668,
              "surrogate_to_post_metadata": 317.5332719999986
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:31 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:32 GMT",
              "x-ms-version-id": "2026-11-03T06:31:32.6924927Z",
              "x-ms-request-id": "edb05ff1-b01e-00e6-495c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1792.677,
              "upper": -623.193
            },
            "floor_s_completed_at": "2026-11-03T06:31:32.000000+00:00",
            "s": "2026-11-03T06:31:32.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/5",
            "completed_at_surrogate": "2026-11-03T06:31:32.940784+00:00",
            "pre_put": "2026-11-03T06:31:32.940784+00:00",
            "post_put": "2026-11-03T06:31:33.092540+00:00",
            "post_metadata": "2026-11-03T06:31:33.240937+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.75888699999973,
              "post_put_to_post_metadata": 148.3971779999962,
              "surrogate_to_post_metadata": 300.15650699999696
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:32 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:33 GMT",
              "x-ms-version-id": "2026-11-03T06:31:33.0093199Z",
              "x-ms-request-id": "edb060b1-b01e-00e6-715c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1092.54,
              "upper": 59.216
            },
            "floor_s_completed_at": "2026-11-03T06:31:32.000000+00:00",
            "s": "2026-11-03T06:31:33.000000+00:00",
            "existing_rule_within": true,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/6",
            "completed_at_surrogate": "2026-11-03T06:31:33.241009+00:00",
            "pre_put": "2026-11-03T06:31:33.241010+00:00",
            "post_put": "2026-11-03T06:31:33.394200+00:00",
            "post_metadata": "2026-11-03T06:31:33.542357+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 153.1929759999997,
              "post_put_to_post_metadata": 148.15605799999787,
              "surrogate_to_post_metadata": 301.3495490000011
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:32 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:33 GMT",
              "x-ms-version-id": "2026-11-03T06:31:33.3091474Z",
              "x-ms-request-id": "edb06189-b01e-00e6-305c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1394.2,
              "upper": -241.01
            },
            "floor_s_completed_at": "2026-11-03T06:31:33.000000+00:00",
            "s": "2026-11-03T06:31:33.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/7",
            "completed_at_surrogate": "2026-11-03T06:31:33.542429+00:00",
            "pre_put": "2026-11-03T06:31:33.542430+00:00",
            "post_put": "2026-11-03T06:31:33.694206+00:00",
            "post_metadata": "2026-11-03T06:31:33.842152+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.77936899999622,
              "post_put_to_post_metadata": 147.9464080000028,
              "surrogate_to_post_metadata": 299.7263119999971
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:32 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:33 GMT",
              "x-ms-version-id": "2026-11-03T06:31:33.6105792Z",
              "x-ms-request-id": "edb06274-b01e-00e6-7c5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1694.206,
              "upper": -542.43
            },
            "floor_s_completed_at": "2026-11-03T06:31:33.000000+00:00",
            "s": "2026-11-03T06:31:33.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/8",
            "completed_at_surrogate": "2026-11-03T06:31:33.842224+00:00",
            "pre_put": "2026-11-03T06:31:33.842225+00:00",
            "post_put": "2026-11-03T06:31:33.994204+00:00",
            "post_metadata": "2026-11-03T06:31:34.142875+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.9821859999979,
              "post_put_to_post_metadata": 148.6705069999985,
              "surrogate_to_post_metadata": 300.65348400000147
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:33 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:33 GMT",
              "x-ms-version-id": "2026-11-03T06:31:33.9106462Z",
              "x-ms-request-id": "edb06356-b01e-00e6-425c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -994.204,
              "upper": 157.775
            },
            "floor_s_completed_at": "2026-11-03T06:31:33.000000+00:00",
            "s": "2026-11-03T06:31:33.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/9",
            "completed_at_surrogate": "2026-11-03T06:31:34.142944+00:00",
            "pre_put": "2026-11-03T06:31:34.142945+00:00",
            "post_put": "2026-11-03T06:31:34.294461+00:00",
            "post_metadata": "2026-11-03T06:31:34.445981+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.5190430000004,
              "post_put_to_post_metadata": 151.5195410000061,
              "surrogate_to_post_metadata": 303.0391230000049
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:33 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:34 GMT",
              "x-ms-version-id": "2026-11-03T06:31:34.2114780Z",
              "x-ms-request-id": "edb0643a-b01e-00e6-115c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1294.461,
              "upper": -142.945
            },
            "floor_s_completed_at": "2026-11-03T06:31:34.000000+00:00",
            "s": "2026-11-03T06:31:34.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/10",
            "completed_at_surrogate": "2026-11-03T06:31:34.446039+00:00",
            "pre_put": "2026-11-03T06:31:34.446039+00:00",
            "post_put": "2026-11-03T06:31:34.597747+00:00",
            "post_metadata": "2026-11-03T06:31:34.745017+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.71065500000225,
              "post_put_to_post_metadata": 147.26958899999687,
              "surrogate_to_post_metadata": 298.9806999999942
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:33 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:34 GMT",
              "x-ms-version-id": "2026-11-03T06:31:34.5143080Z",
              "x-ms-request-id": "edb06507-b01e-00e6-4c5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1597.747,
              "upper": -446.039
            },
            "floor_s_completed_at": "2026-11-03T06:31:34.000000+00:00",
            "s": "2026-11-03T06:31:34.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/11",
            "completed_at_surrogate": "2026-11-03T06:31:34.745076+00:00",
            "pre_put": "2026-11-03T06:31:34.745077+00:00",
            "post_put": "2026-11-03T06:31:34.898564+00:00",
            "post_metadata": "2026-11-03T06:31:35.045859+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 153.49006799999643,
              "post_put_to_post_metadata": 147.29499100000254,
              "surrogate_to_post_metadata": 300.78566800000317
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:34 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:34 GMT",
              "x-ms-version-id": "2026-11-03T06:31:34.8131406Z",
              "x-ms-request-id": "edb065d4-b01e-00e6-065c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -898.564,
              "upper": 254.923
            },
            "floor_s_completed_at": "2026-11-03T06:31:34.000000+00:00",
            "s": "2026-11-03T06:31:34.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/12",
            "completed_at_surrogate": "2026-11-03T06:31:35.045918+00:00",
            "pre_put": "2026-11-03T06:31:35.045918+00:00",
            "post_put": "2026-11-03T06:31:35.202506+00:00",
            "post_metadata": "2026-11-03T06:31:35.349855+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 156.58992699999885,
              "post_put_to_post_metadata": 147.34849900000313,
              "surrogate_to_post_metadata": 303.9389589999999
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:34 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:35 GMT",
              "x-ms-version-id": "2026-11-03T06:31:35.1145474Z",
              "x-ms-request-id": "edb066a6-b01e-00e6-375c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1202.506,
              "upper": -45.918
            },
            "floor_s_completed_at": "2026-11-03T06:31:35.000000+00:00",
            "s": "2026-11-03T06:31:35.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/13",
            "completed_at_surrogate": "2026-11-03T06:31:35.349916+00:00",
            "pre_put": "2026-11-03T06:31:35.349916+00:00",
            "post_put": "2026-11-03T06:31:35.501340+00:00",
            "post_metadata": "2026-11-03T06:31:35.648976+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.42674199999817,
              "post_put_to_post_metadata": 147.63517699999795,
              "surrogate_to_post_metadata": 299.06251699999586
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:34 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:35 GMT",
              "x-ms-version-id": "2026-11-03T06:31:35.4180085Z",
              "x-ms-request-id": "edb0674f-b01e-00e6-4c5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1501.34,
              "upper": -349.916
            },
            "floor_s_completed_at": "2026-11-03T06:31:35.000000+00:00",
            "s": "2026-11-03T06:31:35.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/14",
            "completed_at_surrogate": "2026-11-03T06:31:35.649045+00:00",
            "pre_put": "2026-11-03T06:31:35.649046+00:00",
            "post_put": "2026-11-03T06:31:35.801368+00:00",
            "post_metadata": "2026-11-03T06:31:35.948756+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 152.32483200000502,
              "post_put_to_post_metadata": 147.38778699999955,
              "surrogate_to_post_metadata": 299.713220000001
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:34 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:35 GMT",
              "x-ms-version-id": "2026-11-03T06:31:35.7168362Z",
              "x-ms-request-id": "edb067ea-b01e-00e6-4c5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1801.368,
              "upper": -649.046
            },
            "floor_s_completed_at": "2026-11-03T06:31:35.000000+00:00",
            "s": "2026-11-03T06:31:35.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/15",
            "completed_at_surrogate": "2026-11-03T06:31:35.948819+00:00",
            "pre_put": "2026-11-03T06:31:35.948820+00:00",
            "post_put": "2026-11-03T06:31:36.100197+00:00",
            "post_metadata": "2026-11-03T06:31:36.247569+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.37921800000242,
              "post_put_to_post_metadata": 147.3724230000002,
              "surrogate_to_post_metadata": 298.7521820000012
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:35 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:36 GMT",
              "x-ms-version-id": "2026-11-03T06:31:36.0166683Z",
              "x-ms-request-id": "edb068b2-b01e-00e6-7e5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1100.197,
              "upper": 51.18
            },
            "floor_s_completed_at": "2026-11-03T06:31:35.000000+00:00",
            "s": "2026-11-03T06:31:36.000000+00:00",
            "existing_rule_within": true,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/16",
            "completed_at_surrogate": "2026-11-03T06:31:36.247638+00:00",
            "pre_put": "2026-11-03T06:31:36.247639+00:00",
            "post_put": "2026-11-03T06:31:36.399746+00:00",
            "post_metadata": "2026-11-03T06:31:36.547044+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 152.10942999999588,
              "post_put_to_post_metadata": 147.29842500000245,
              "surrogate_to_post_metadata": 299.4084299999997
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:35 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:36 GMT",
              "x-ms-version-id": "2026-11-03T06:31:36.3165007Z",
              "x-ms-request-id": "edb0697e-b01e-00e6-2d5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1399.746,
              "upper": -247.639
            },
            "floor_s_completed_at": "2026-11-03T06:31:36.000000+00:00",
            "s": "2026-11-03T06:31:36.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/17",
            "completed_at_surrogate": "2026-11-03T06:31:36.547115+00:00",
            "pre_put": "2026-11-03T06:31:36.547115+00:00",
            "post_put": "2026-11-03T06:31:36.699424+00:00",
            "post_metadata": "2026-11-03T06:31:36.846920+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 152.31057300000117,
              "post_put_to_post_metadata": 147.49644799999828,
              "surrogate_to_post_metadata": 299.8075710000023
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:35 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:36 GMT",
              "x-ms-version-id": "2026-11-03T06:31:36.6156039Z",
              "x-ms-request-id": "edb06a71-b01e-00e6-765c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1699.424,
              "upper": -547.115
            },
            "floor_s_completed_at": "2026-11-03T06:31:36.000000+00:00",
            "s": "2026-11-03T06:31:36.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/18",
            "completed_at_surrogate": "2026-11-03T06:31:36.846980+00:00",
            "pre_put": "2026-11-03T06:31:36.846981+00:00",
            "post_put": "2026-11-03T06:31:36.998502+00:00",
            "post_metadata": "2026-11-03T06:31:37.146088+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.5239940000015,
              "post_put_to_post_metadata": 147.5852599999996,
              "surrogate_to_post_metadata": 299.1097429999954
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:36 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:36 GMT",
              "x-ms-version-id": "2026-11-03T06:31:36.9154358Z",
              "x-ms-request-id": "edb06b52-b01e-00e6-425c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -998.502,
              "upper": 153.019
            },
            "floor_s_completed_at": "2026-11-03T06:31:36.000000+00:00",
            "s": "2026-11-03T06:31:36.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/19",
            "completed_at_surrogate": "2026-11-03T06:31:37.146159+00:00",
            "pre_put": "2026-11-03T06:31:37.146160+00:00",
            "post_put": "2026-11-03T06:31:37.298627+00:00",
            "post_metadata": "2026-11-03T06:31:37.446347+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 152.46860599999934,
              "post_put_to_post_metadata": 147.72101000000504,
              "surrogate_to_post_metadata": 300.1902540000003
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:36 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:37 GMT",
              "x-ms-version-id": "2026-11-03T06:31:37.2147780Z",
              "x-ms-request-id": "edb06c3d-b01e-00e6-145c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1298.627,
              "upper": -146.16
            },
            "floor_s_completed_at": "2026-11-03T06:31:37.000000+00:00",
            "s": "2026-11-03T06:31:37.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/20",
            "completed_at_surrogate": "2026-11-03T06:31:37.446419+00:00",
            "pre_put": "2026-11-03T06:31:37.446420+00:00",
            "post_put": "2026-11-03T06:31:37.597777+00:00",
            "post_metadata": "2026-11-03T06:31:37.747233+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.35940900000122,
              "post_put_to_post_metadata": 149.45685800000064,
              "surrogate_to_post_metadata": 300.8167919999991
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:36 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:37 GMT",
              "x-ms-version-id": "2026-11-03T06:31:37.5146117Z",
              "x-ms-request-id": "edb06cee-b01e-00e6-385c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1597.777,
              "upper": -446.42
            },
            "floor_s_completed_at": "2026-11-03T06:31:37.000000+00:00",
            "s": "2026-11-03T06:31:37.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/21",
            "completed_at_surrogate": "2026-11-03T06:31:37.747328+00:00",
            "pre_put": "2026-11-03T06:31:37.747329+00:00",
            "post_put": "2026-11-03T06:31:37.899564+00:00",
            "post_metadata": "2026-11-03T06:31:38.046841+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 152.23816299999982,
              "post_put_to_post_metadata": 147.27644999999967,
              "surrogate_to_post_metadata": 299.5153079999966
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:37 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:37 GMT",
              "x-ms-version-id": "2026-11-03T06:31:37.8160202Z",
              "x-ms-request-id": "edb06da1-b01e-00e6-515c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -899.564,
              "upper": 252.671
            },
            "floor_s_completed_at": "2026-11-03T06:31:37.000000+00:00",
            "s": "2026-11-03T06:31:37.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/22",
            "completed_at_surrogate": "2026-11-03T06:31:38.046895+00:00",
            "pre_put": "2026-11-03T06:31:38.046896+00:00",
            "post_put": "2026-11-03T06:31:38.198232+00:00",
            "post_metadata": "2026-11-03T06:31:38.345169+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.3387299999991,
              "post_put_to_post_metadata": 146.93713300000155,
              "surrogate_to_post_metadata": 298.27630700000185
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:37 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:38 GMT",
              "x-ms-version-id": "2026-11-03T06:31:38.1153700Z",
              "x-ms-request-id": "edb06e8f-b01e-00e6-1b5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1198.232,
              "upper": -46.896
            },
            "floor_s_completed_at": "2026-11-03T06:31:38.000000+00:00",
            "s": "2026-11-03T06:31:38.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/23",
            "completed_at_surrogate": "2026-11-03T06:31:38.345231+00:00",
            "pre_put": "2026-11-03T06:31:38.345232+00:00",
            "post_put": "2026-11-03T06:31:38.497040+00:00",
            "post_metadata": "2026-11-03T06:31:38.645303+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.810820999998,
              "post_put_to_post_metadata": 148.26353699999828,
              "surrogate_to_post_metadata": 300.07476800000177
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:37 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:38 GMT",
              "x-ms-version-id": "2026-11-03T06:31:38.4132020Z",
              "x-ms-request-id": "edb06fa1-b01e-00e6-1f5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1497.04,
              "upper": -345.232
            },
            "floor_s_completed_at": "2026-11-03T06:31:38.000000+00:00",
            "s": "2026-11-03T06:31:38.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/24",
            "completed_at_surrogate": "2026-11-03T06:31:38.645359+00:00",
            "pre_put": "2026-11-03T06:31:38.645359+00:00",
            "post_put": "2026-11-03T06:31:38.796681+00:00",
            "post_metadata": "2026-11-03T06:31:38.943956+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.32405699999651,
              "post_put_to_post_metadata": 147.2747860000041,
              "surrogate_to_post_metadata": 298.599320000001
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:37 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:38 GMT",
              "x-ms-version-id": "2026-11-03T06:31:38.7140344Z",
              "x-ms-request-id": "edb07058-b01e-00e6-415c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1796.681,
              "upper": -645.359
            },
            "floor_s_completed_at": "2026-11-03T06:31:38.000000+00:00",
            "s": "2026-11-03T06:31:38.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/25",
            "completed_at_surrogate": "2026-11-03T06:31:38.944017+00:00",
            "pre_put": "2026-11-03T06:31:38.944018+00:00",
            "post_put": "2026-11-03T06:31:39.095479+00:00",
            "post_metadata": "2026-11-03T06:31:39.242685+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.4636189999976,
              "post_put_to_post_metadata": 147.20593300000218,
              "surrogate_to_post_metadata": 298.670051000002
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:38 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:39 GMT",
              "x-ms-version-id": "2026-11-03T06:31:39.0128677Z",
              "x-ms-request-id": "edb0710c-b01e-00e6-625c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1095.479,
              "upper": 55.982
            },
            "floor_s_completed_at": "2026-11-03T06:31:38.000000+00:00",
            "s": "2026-11-03T06:31:39.000000+00:00",
            "existing_rule_within": true,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/26",
            "completed_at_surrogate": "2026-11-03T06:31:39.242748+00:00",
            "pre_put": "2026-11-03T06:31:39.242749+00:00",
            "post_put": "2026-11-03T06:31:39.394633+00:00",
            "post_metadata": "2026-11-03T06:31:39.542080+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.8872050000013,
              "post_put_to_post_metadata": 147.44614499999642,
              "surrogate_to_post_metadata": 299.33382799999464
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:38 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:39 GMT",
              "x-ms-version-id": "2026-11-03T06:31:39.3114468Z",
              "x-ms-request-id": "edb07208-b01e-00e6-3c5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1394.633,
              "upper": -242.749
            },
            "floor_s_completed_at": "2026-11-03T06:31:39.000000+00:00",
            "s": "2026-11-03T06:31:39.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/27",
            "completed_at_surrogate": "2026-11-03T06:31:39.542143+00:00",
            "pre_put": "2026-11-03T06:31:39.542144+00:00",
            "post_put": "2026-11-03T06:31:39.693591+00:00",
            "post_metadata": "2026-11-03T06:31:39.840880+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.4497739999996,
              "post_put_to_post_metadata": 147.2883610000011,
              "surrogate_to_post_metadata": 298.7386520000044
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:38 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:39 GMT",
              "x-ms-version-id": "2026-11-03T06:31:39.6102798Z",
              "x-ms-request-id": "edb07340-b01e-00e6-555c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1693.591,
              "upper": -542.144
            },
            "floor_s_completed_at": "2026-11-03T06:31:39.000000+00:00",
            "s": "2026-11-03T06:31:39.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/28",
            "completed_at_surrogate": "2026-11-03T06:31:39.840932+00:00",
            "pre_put": "2026-11-03T06:31:39.840933+00:00",
            "post_put": "2026-11-03T06:31:39.992626+00:00",
            "post_metadata": "2026-11-03T06:31:40.140176+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.69561300000112,
              "post_put_to_post_metadata": 147.5498929999972,
              "surrogate_to_post_metadata": 299.2460859999966
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:39 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:39 GMT",
              "x-ms-version-id": "2026-11-03T06:31:39.9091115Z",
              "x-ms-request-id": "edb0741c-b01e-00e6-1f5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -992.626,
              "upper": 159.067
            },
            "floor_s_completed_at": "2026-11-03T06:31:39.000000+00:00",
            "s": "2026-11-03T06:31:39.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/29",
            "completed_at_surrogate": "2026-11-03T06:31:40.140237+00:00",
            "pre_put": "2026-11-03T06:31:40.140238+00:00",
            "post_put": "2026-11-03T06:31:40.291310+00:00",
            "post_metadata": "2026-11-03T06:31:40.438579+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.07423499999584,
              "post_put_to_post_metadata": 147.2700090000032,
              "surrogate_to_post_metadata": 298.3447209999994
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:39 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:40 GMT",
              "x-ms-version-id": "2026-11-03T06:31:40.2079445Z",
              "x-ms-request-id": "edb074d2-b01e-00e6-3b5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1291.31,
              "upper": -140.238
            },
            "floor_s_completed_at": "2026-11-03T06:31:40.000000+00:00",
            "s": "2026-11-03T06:31:40.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/30",
            "completed_at_surrogate": "2026-11-03T06:31:40.438653+00:00",
            "pre_put": "2026-11-03T06:31:40.438654+00:00",
            "post_put": "2026-11-03T06:31:40.590084+00:00",
            "post_metadata": "2026-11-03T06:31:40.737572+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.43313499999778,
              "post_put_to_post_metadata": 147.48743700000233,
              "surrogate_to_post_metadata": 298.9211200000028
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:39 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:40 GMT",
              "x-ms-version-id": "2026-11-03T06:31:40.5070697Z",
              "x-ms-request-id": "edb075a6-b01e-00e6-6d5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1590.084,
              "upper": -438.654
            },
            "floor_s_completed_at": "2026-11-03T06:31:40.000000+00:00",
            "s": "2026-11-03T06:31:40.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/31",
            "completed_at_surrogate": "2026-11-03T06:31:40.737635+00:00",
            "pre_put": "2026-11-03T06:31:40.737636+00:00",
            "post_put": "2026-11-03T06:31:40.889245+00:00",
            "post_metadata": "2026-11-03T06:31:41.036618+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.61141800000166,
              "post_put_to_post_metadata": 147.37334499999832,
              "surrogate_to_post_metadata": 298.985272000003
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:40 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:40 GMT",
              "x-ms-version-id": "2026-11-03T06:31:40.8059025Z",
              "x-ms-request-id": "edb07672-b01e-00e6-175c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -889.245,
              "upper": 262.364
            },
            "floor_s_completed_at": "2026-11-03T06:31:40.000000+00:00",
            "s": "2026-11-03T06:31:40.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/32",
            "completed_at_surrogate": "2026-11-03T06:31:41.036680+00:00",
            "pre_put": "2026-11-03T06:31:41.036681+00:00",
            "post_put": "2026-11-03T06:31:41.187856+00:00",
            "post_metadata": "2026-11-03T06:31:41.335296+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.17741800000317,
              "post_put_to_post_metadata": 147.44077200000305,
              "surrogate_to_post_metadata": 298.61878400000563
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:40 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:41 GMT",
              "x-ms-version-id": "2026-11-03T06:31:41.1047343Z",
              "x-ms-request-id": "edb07728-b01e-00e6-255c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1187.856,
              "upper": -36.681
            },
            "floor_s_completed_at": "2026-11-03T06:31:41.000000+00:00",
            "s": "2026-11-03T06:31:41.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/33",
            "completed_at_surrogate": "2026-11-03T06:31:41.335367+00:00",
            "pre_put": "2026-11-03T06:31:41.335367+00:00",
            "post_put": "2026-11-03T06:31:41.502020+00:00",
            "post_metadata": "2026-11-03T06:31:41.649400+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 166.6549549999985,
              "post_put_to_post_metadata": 147.37989500000026,
              "surrogate_to_post_metadata": 314.03553799999884
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:40 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:41 GMT",
              "x-ms-version-id": "2026-11-03T06:31:41.4035728Z",
              "x-ms-request-id": "edb077f6-b01e-00e6-365c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1502.02,
              "upper": -335.367
            },
            "floor_s_completed_at": "2026-11-03T06:31:41.000000+00:00",
            "s": "2026-11-03T06:31:41.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/34",
            "completed_at_surrogate": "2026-11-03T06:31:41.649463+00:00",
            "pre_put": "2026-11-03T06:31:41.649464+00:00",
            "post_put": "2026-11-03T06:31:41.801030+00:00",
            "post_metadata": "2026-11-03T06:31:41.948318+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.56914300000324,
              "post_put_to_post_metadata": 147.28806000000105,
              "surrogate_to_post_metadata": 298.8576199999997
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:40 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:41 GMT",
              "x-ms-version-id": "2026-11-03T06:31:41.7174273Z",
              "x-ms-request-id": "edb078d5-b01e-00e6-5e5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1801.03,
              "upper": -649.464
            },
            "floor_s_completed_at": "2026-11-03T06:31:41.000000+00:00",
            "s": "2026-11-03T06:31:41.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/35",
            "completed_at_surrogate": "2026-11-03T06:31:41.948381+00:00",
            "pre_put": "2026-11-03T06:31:41.948382+00:00",
            "post_put": "2026-11-03T06:31:42.099480+00:00",
            "post_metadata": "2026-11-03T06:31:42.246694+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.10006399999776,
              "post_put_to_post_metadata": 147.213880999999,
              "surrogate_to_post_metadata": 298.31443799999846
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:41 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:42 GMT",
              "x-ms-version-id": "2026-11-03T06:31:42.0160063Z",
              "x-ms-request-id": "edb079dd-b01e-00e6-2d5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1099.48,
              "upper": 51.618
            },
            "floor_s_completed_at": "2026-11-03T06:31:41.000000+00:00",
            "s": "2026-11-03T06:31:42.000000+00:00",
            "existing_rule_within": true,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/36",
            "completed_at_surrogate": "2026-11-03T06:31:42.246769+00:00",
            "pre_put": "2026-11-03T06:31:42.246769+00:00",
            "post_put": "2026-11-03T06:31:42.398291+00:00",
            "post_metadata": "2026-11-03T06:31:42.545463+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.52561700000433,
              "post_put_to_post_metadata": 147.16940599999617,
              "surrogate_to_post_metadata": 298.6957489999966
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:41 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:42 GMT",
              "x-ms-version-id": "2026-11-03T06:31:42.3148394Z",
              "x-ms-request-id": "edb07abb-b01e-00e6-4b5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1398.291,
              "upper": -246.769
            },
            "floor_s_completed_at": "2026-11-03T06:31:42.000000+00:00",
            "s": "2026-11-03T06:31:42.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/37",
            "completed_at_surrogate": "2026-11-03T06:31:42.545517+00:00",
            "pre_put": "2026-11-03T06:31:42.545518+00:00",
            "post_put": "2026-11-03T06:31:42.697197+00:00",
            "post_metadata": "2026-11-03T06:31:42.844486+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.68230100000102,
              "post_put_to_post_metadata": 147.28793699999443,
              "surrogate_to_post_metadata": 298.970709999999
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:41 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:42 GMT",
              "x-ms-version-id": "2026-11-03T06:31:42.6136714Z",
              "x-ms-request-id": "edb07bb6-b01e-00e6-1d5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1697.197,
              "upper": -545.518
            },
            "floor_s_completed_at": "2026-11-03T06:31:42.000000+00:00",
            "s": "2026-11-03T06:31:42.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/38",
            "completed_at_surrogate": "2026-11-03T06:31:42.844547+00:00",
            "pre_put": "2026-11-03T06:31:42.844548+00:00",
            "post_put": "2026-11-03T06:31:42.995553+00:00",
            "post_metadata": "2026-11-03T06:31:43.142997+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.0078849999985,
              "post_put_to_post_metadata": 147.4437940000044,
              "surrogate_to_post_metadata": 298.452374
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:42 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:42 GMT",
              "x-ms-version-id": "2026-11-03T06:31:42.9125038Z",
              "x-ms-request-id": "edb07cce-b01e-00e6-785c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -995.553,
              "upper": 155.452
            },
            "floor_s_completed_at": "2026-11-03T06:31:42.000000+00:00",
            "s": "2026-11-03T06:31:42.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/39",
            "completed_at_surrogate": "2026-11-03T06:31:43.143056+00:00",
            "pre_put": "2026-11-03T06:31:43.143057+00:00",
            "post_put": "2026-11-03T06:31:43.294438+00:00",
            "post_metadata": "2026-11-03T06:31:43.441755+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.38405199999738,
              "post_put_to_post_metadata": 147.31726699999825,
              "surrogate_to_post_metadata": 298.70183699999586
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:42 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:43 GMT",
              "x-ms-version-id": "2026-11-03T06:31:43.2114663Z",
              "x-ms-request-id": "edb07dc1-b01e-00e6-305c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1294.438,
              "upper": -143.057
            },
            "floor_s_completed_at": "2026-11-03T06:31:43.000000+00:00",
            "s": "2026-11-03T06:31:43.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/40",
            "completed_at_surrogate": "2026-11-03T06:31:43.441818+00:00",
            "pre_put": "2026-11-03T06:31:43.441819+00:00",
            "post_put": "2026-11-03T06:31:43.593017+00:00",
            "post_metadata": "2026-11-03T06:31:43.740862+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.20096700000119,
              "post_put_to_post_metadata": 147.84468999999945,
              "surrogate_to_post_metadata": 299.0461639999964
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:42 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:43 GMT",
              "x-ms-version-id": "2026-11-03T06:31:43.5102988Z",
              "x-ms-request-id": "edb07e66-b01e-00e6-315c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1593.017,
              "upper": -441.819
            },
            "floor_s_completed_at": "2026-11-03T06:31:43.000000+00:00",
            "s": "2026-11-03T06:31:43.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/41",
            "completed_at_surrogate": "2026-11-03T06:31:43.740923+00:00",
            "pre_put": "2026-11-03T06:31:43.740924+00:00",
            "post_put": "2026-11-03T06:31:43.900243+00:00",
            "post_metadata": "2026-11-03T06:31:44.047413+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 159.32166999999708,
              "post_put_to_post_metadata": 147.16978799999936,
              "surrogate_to_post_metadata": 306.49213199999537
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:43 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:43 GMT",
              "x-ms-version-id": "2026-11-03T06:31:43.8171271Z",
              "x-ms-request-id": "edb07f08-b01e-00e6-2a5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -900.243,
              "upper": 259.076
            },
            "floor_s_completed_at": "2026-11-03T06:31:43.000000+00:00",
            "s": "2026-11-03T06:31:43.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/42",
            "completed_at_surrogate": "2026-11-03T06:31:44.047487+00:00",
            "pre_put": "2026-11-03T06:31:44.047487+00:00",
            "post_put": "2026-11-03T06:31:44.199192+00:00",
            "post_metadata": "2026-11-03T06:31:44.347044+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.7081930000046,
              "post_put_to_post_metadata": 147.85133299999842,
              "surrogate_to_post_metadata": 299.56019400000145
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:43 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:44 GMT",
              "x-ms-version-id": "2026-11-03T06:31:44.1159588Z",
              "x-ms-request-id": "edb07feb-b01e-00e6-485c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1199.192,
              "upper": -47.487
            },
            "floor_s_completed_at": "2026-11-03T06:31:44.000000+00:00",
            "s": "2026-11-03T06:31:44.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/43",
            "completed_at_surrogate": "2026-11-03T06:31:44.347108+00:00",
            "pre_put": "2026-11-03T06:31:44.347109+00:00",
            "post_put": "2026-11-03T06:31:44.498612+00:00",
            "post_metadata": "2026-11-03T06:31:44.645735+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.50553099999797,
              "post_put_to_post_metadata": 147.12370700000577,
              "surrogate_to_post_metadata": 298.6296900000056
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:43 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:44 GMT",
              "x-ms-version-id": "2026-11-03T06:31:44.4153744Z",
              "x-ms-request-id": "edb080a4-b01e-00e6-5b5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1498.612,
              "upper": -347.109
            },
            "floor_s_completed_at": "2026-11-03T06:31:44.000000+00:00",
            "s": "2026-11-03T06:31:44.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/44",
            "completed_at_surrogate": "2026-11-03T06:31:44.645798+00:00",
            "pre_put": "2026-11-03T06:31:44.645799+00:00",
            "post_put": "2026-11-03T06:31:44.797489+00:00",
            "post_metadata": "2026-11-03T06:31:44.944695+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.69236799999908,
              "post_put_to_post_metadata": 147.205606,
              "surrogate_to_post_metadata": 298.898549999997
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:43 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:44 GMT",
              "x-ms-version-id": "2026-11-03T06:31:44.7143585Z",
              "x-ms-request-id": "edb08186-b01e-00e6-7f5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1797.489,
              "upper": -645.799
            },
            "floor_s_completed_at": "2026-11-03T06:31:44.000000+00:00",
            "s": "2026-11-03T06:31:44.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/45",
            "completed_at_surrogate": "2026-11-03T06:31:44.944757+00:00",
            "pre_put": "2026-11-03T06:31:44.944758+00:00",
            "post_put": "2026-11-03T06:31:45.096452+00:00",
            "post_metadata": "2026-11-03T06:31:45.244313+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.69588399999867,
              "post_put_to_post_metadata": 147.86195500000332,
              "surrogate_to_post_metadata": 299.5583289999999
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:44 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:45 GMT",
              "x-ms-version-id": "2026-11-03T06:31:45.0131906Z",
              "x-ms-request-id": "edb0822a-b01e-00e6-0b5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1096.452,
              "upper": 55.242
            },
            "floor_s_completed_at": "2026-11-03T06:31:44.000000+00:00",
            "s": "2026-11-03T06:31:45.000000+00:00",
            "existing_rule_within": true,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/46",
            "completed_at_surrogate": "2026-11-03T06:31:45.244370+00:00",
            "pre_put": "2026-11-03T06:31:45.244371+00:00",
            "post_put": "2026-11-03T06:31:45.396413+00:00",
            "post_metadata": "2026-11-03T06:31:45.544074+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 152.04498899999663,
              "post_put_to_post_metadata": 147.66144699999728,
              "surrogate_to_post_metadata": 299.70686499999744
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:44 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:45 GMT",
              "x-ms-version-id": "2026-11-03T06:31:45.3130228Z",
              "x-ms-request-id": "edb0829e-b01e-00e6-645c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1396.413,
              "upper": -244.371
            },
            "floor_s_completed_at": "2026-11-03T06:31:45.000000+00:00",
            "s": "2026-11-03T06:31:45.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/47",
            "completed_at_surrogate": "2026-11-03T06:31:45.544138+00:00",
            "pre_put": "2026-11-03T06:31:45.544139+00:00",
            "post_put": "2026-11-03T06:31:45.696983+00:00",
            "post_metadata": "2026-11-03T06:31:45.844414+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 152.84704500000146,
              "post_put_to_post_metadata": 147.43131600000225,
              "surrogate_to_post_metadata": 300.27890099999865
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:44 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:45 GMT",
              "x-ms-version-id": "2026-11-03T06:31:45.6128549Z",
              "x-ms-request-id": "edb0837a-b01e-00e6-6a5c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1696.983,
              "upper": -544.139
            },
            "floor_s_completed_at": "2026-11-03T06:31:45.000000+00:00",
            "s": "2026-11-03T06:31:45.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/48",
            "completed_at_surrogate": "2026-11-03T06:31:45.844484+00:00",
            "pre_put": "2026-11-03T06:31:45.844485+00:00",
            "post_put": "2026-11-03T06:31:45.996590+00:00",
            "post_metadata": "2026-11-03T06:31:46.144159+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 152.10853499999644,
              "post_put_to_post_metadata": 147.56777099999852,
              "surrogate_to_post_metadata": 299.6769649999962
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:45 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:45 GMT",
              "x-ms-version-id": "2026-11-03T06:31:45.9129570Z",
              "x-ms-request-id": "edb0846c-b01e-00e6-165c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -996.59,
              "upper": 155.515
            },
            "floor_s_completed_at": "2026-11-03T06:31:45.000000+00:00",
            "s": "2026-11-03T06:31:45.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/49",
            "completed_at_surrogate": "2026-11-03T06:31:46.144229+00:00",
            "pre_put": "2026-11-03T06:31:46.144230+00:00",
            "post_put": "2026-11-03T06:31:46.295961+00:00",
            "post_metadata": "2026-11-03T06:31:46.443411+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.7335959999997,
              "post_put_to_post_metadata": 147.45005900000052,
              "surrogate_to_post_metadata": 299.18428900000293
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:45 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:46 GMT",
              "x-ms-version-id": "2026-11-03T06:31:46.2127888Z",
              "x-ms-request-id": "edb08522-b01e-00e6-195c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1295.961,
              "upper": -144.23
            },
            "floor_s_completed_at": "2026-11-03T06:31:46.000000+00:00",
            "s": "2026-11-03T06:31:46.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/50",
            "completed_at_surrogate": "2026-11-03T06:31:46.443484+00:00",
            "pre_put": "2026-11-03T06:31:46.443485+00:00",
            "post_put": "2026-11-03T06:31:46.595403+00:00",
            "post_metadata": "2026-11-03T06:31:46.742818+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.92079600000596,
              "post_put_to_post_metadata": 147.41488199999964,
              "surrogate_to_post_metadata": 299.33636200000535
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:45 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:46 GMT",
              "x-ms-version-id": "2026-11-03T06:31:46.5126200Z",
              "x-ms-request-id": "edb085b8-b01e-00e6-025c-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -1595.403,
              "upper": -443.485
            },
            "floor_s_completed_at": "2026-11-03T06:31:46.000000+00:00",
            "s": "2026-11-03T06:31:46.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          },
          {
            "key": "probe/20261103T063128Z-36b82702/51",
            "completed_at_surrogate": "2026-11-03T06:31:46.742878+00:00",
            "pre_put": "2026-11-03T06:31:46.742879+00:00",
            "post_put": "2026-11-03T06:31:46.894489+00:00",
            "post_metadata": "2026-11-03T06:31:47.042141+00:00",
            "durations_ms": {
              "pre_put_to_post_put": 151.6137170000036,
              "post_put_to_post_metadata": 147.65223199999866,
              "surrogate_to_post_metadata": 299.266455999998
            },
            "headers_captured": true,
            "response_hook_calls": 1,
            "headers": {
              "Date": "Tue, 03 Nov 2026 06:31:46 GMT",
              "Last-Modified": "Tue, 03 Nov 2026 06:31:46 GMT",
              "x-ms-version-id": "2026-11-03T06:31:46.8114519Z",
              "x-ms-request-id": "edb086a6-b01e-00e6-245d-6b4a7a000000"
            },
            "missing_headers": [],
            "offset_bracket_ms": {
              "lower": -894.489,
              "upper": 257.121
            },
            "floor_s_completed_at": "2026-11-03T06:31:46.000000+00:00",
            "s": "2026-11-03T06:31:46.000000+00:00",
            "existing_rule_within": false,
            "candidate_rule_within": true
          }
        ]
      }
    }
  ]
}
```
