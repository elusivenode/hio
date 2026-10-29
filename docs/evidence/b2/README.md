---
id: HIO-EVIDENCE-B2-RESULT
title: "B-2 storage probe: retained report and first reading"
status: draft            # evidence plus Claude's first reading; the interpretation is for the owner
owner: HIO architecture lead (owner); prepared by claude/implementation-agent
created_at: 2026-10-29
instruction: OD-0132 item 1 (B-2 per docs/evidence/S1B1-B2-probe-plan.md, steps 1-8 without 7b)
---

# B-2 result

**Run:** GitHub Actions run `40853094503`, workflow `storage-probe`, dispatched at `main` `651eb95` with `repeats=50`,
approved by the owner in the `capture` Environment. It finished `failure` at 2026-10-29T10:21:04Z. The report is
kept verbatim in the fenced block at the end of this file (the repository allows no data files outside
`tests/fixtures/synthetic/`), sha256 `a3ece08a4c5b39b3dff5594b5aeb987e1cfb4915ef1e5256855312e0185ae39a`, as
downloaded from the run artifact. The block's content, from the line after its opening fence up to its
closing fence, is the file byte for byte (it ends with a newline); its sha256 was checked on commit. The artifact itself expires after 30 days.

| Check | Result |
|---|---|
| Create a fresh key | pass |
| Conditional create of the same key | **not as specified**: HTTP 403 `UnauthorizedBlobOverwrite`, not 409 `BlobAlreadyExists`. Nothing was overwritten, but `AzureBlobBackend` maps only 409/412 to `BlobExists` |
| Overwrite by the writer | refused, 403 `UnauthorizedBlobOverwrite` (an RBAC refusal) |
| Delete by the writer | refused, 403 `AuthorizationPermissionMismatch` (an RBAC refusal) |
| One version per key | pass |
| C5 timing, `completed_at ≤ s ≤ completed_at + δ` | **50 of 50 violations**. `s − completed_at` ranges from −1294 to −302 ms (median −828 ms); 17 are below −1000 ms. `s` is always a whole second |

**Not tested:** immutability against a privileged actor (step 7b was excluded).

**First reading (Claude; for the architect and the owner, not a decision).** `Last-Modified` is the server's write
instant floored to the second, and the server write precedes the client's `completed_at` by the response latency. So
C5's lower bound cannot hold on Azure as written. The plan's "≤ −1000 ms: stop; investigate" row is engaged. Floor
plus latency may explain it, but that is unconfirmed. Any C5 change is an owner decision (an HIO-ADR-0012 amendment).
B-3 waits for it.

## The report (verbatim)


```json
{
  "run_id": "20261029T102027Z-4deccf3f",
  "started_at": "2026-10-29T10:20:27.217668+00:00",
  "account_host": "hioprobehoue.blob.core.windows.net",
  "passed": false,
  "results": [
    {
      "check": "create_fresh_key",
      "passed": true,
      "detail": "created probe/20261029T102027Z-4deccf3f/1 as version 2026-10-29T10:20:28.8588576Z"
    },
    {
      "check": "create_again_raises_blob_exists",
      "passed": false,
      "detail": "unexpected HttpResponseError HTTP 403 UnauthorizedBlobOverwrite"
    },
    {
      "check": "overwrite_refused",
      "passed": true,
      "detail": "overwrite of probe/20261029T102027Z-4deccf3f/1 refused: HttpResponseError HTTP 403 UnauthorizedBlobOverwrite"
    },
    {
      "check": "delete_refused",
      "passed": true,
      "detail": "delete of probe/20261029T102027Z-4deccf3f/1 refused: HttpResponseError HTTP 403 AuthorizationPermissionMismatch"
    },
    {
      "check": "exactly_one_version",
      "passed": true,
      "detail": "one version of probe/20261029T102027Z-4deccf3f/1: 2026-10-29T10:20:28.8588576Z"
    },
    {
      "check": "c5_timing",
      "passed": false,
      "detail": {
        "repeats": 50,
        "delta_seconds": 600.0,
        "tolerance": "none",
        "violations": 50,
        "errors": 0,
        "min_diff_ms": -1294.274,
        "max_diff_ms": -302.031,
        "observations": [
          {
            "key": "probe/20261029T102027Z-4deccf3f/2",
            "completed_at": "2026-10-29T10:20:30.375415+00:00",
            "s": "2026-10-29T10:20:30.000000+00:00",
            "diff_ms": -375.415,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/3",
            "completed_at": "2026-10-29T10:20:30.980521+00:00",
            "s": "2026-10-29T10:20:30.000000+00:00",
            "diff_ms": -980.521,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/4",
            "completed_at": "2026-10-29T10:20:31.587679+00:00",
            "s": "2026-10-29T10:20:31.000000+00:00",
            "diff_ms": -587.679,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/5",
            "completed_at": "2026-10-29T10:20:32.192084+00:00",
            "s": "2026-10-29T10:20:31.000000+00:00",
            "diff_ms": -1192.084,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/6",
            "completed_at": "2026-10-29T10:20:32.801990+00:00",
            "s": "2026-10-29T10:20:32.000000+00:00",
            "diff_ms": -801.99,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/7",
            "completed_at": "2026-10-29T10:20:33.408099+00:00",
            "s": "2026-10-29T10:20:33.000000+00:00",
            "diff_ms": -408.099,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/8",
            "completed_at": "2026-10-29T10:20:34.011736+00:00",
            "s": "2026-10-29T10:20:33.000000+00:00",
            "diff_ms": -1011.736,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/9",
            "completed_at": "2026-10-29T10:20:34.618617+00:00",
            "s": "2026-10-29T10:20:34.000000+00:00",
            "diff_ms": -618.617,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/10",
            "completed_at": "2026-10-29T10:20:35.224470+00:00",
            "s": "2026-10-29T10:20:34.000000+00:00",
            "diff_ms": -1224.47,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/11",
            "completed_at": "2026-10-29T10:20:35.827642+00:00",
            "s": "2026-10-29T10:20:35.000000+00:00",
            "diff_ms": -827.642,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/12",
            "completed_at": "2026-10-29T10:20:36.438407+00:00",
            "s": "2026-10-29T10:20:36.000000+00:00",
            "diff_ms": -438.407,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/13",
            "completed_at": "2026-10-29T10:20:37.063323+00:00",
            "s": "2026-10-29T10:20:36.000000+00:00",
            "diff_ms": -1063.323,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/14",
            "completed_at": "2026-10-29T10:20:37.668845+00:00",
            "s": "2026-10-29T10:20:37.000000+00:00",
            "diff_ms": -668.845,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/15",
            "completed_at": "2026-10-29T10:20:38.276956+00:00",
            "s": "2026-10-29T10:20:37.000000+00:00",
            "diff_ms": -1276.956,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/16",
            "completed_at": "2026-10-29T10:20:38.886032+00:00",
            "s": "2026-10-29T10:20:38.000000+00:00",
            "diff_ms": -886.032,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/17",
            "completed_at": "2026-10-29T10:20:39.490274+00:00",
            "s": "2026-10-29T10:20:39.000000+00:00",
            "diff_ms": -490.274,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/18",
            "completed_at": "2026-10-29T10:20:40.095274+00:00",
            "s": "2026-10-29T10:20:39.000000+00:00",
            "diff_ms": -1095.274,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/19",
            "completed_at": "2026-10-29T10:20:40.698685+00:00",
            "s": "2026-10-29T10:20:40.000000+00:00",
            "diff_ms": -698.685,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/20",
            "completed_at": "2026-10-29T10:20:41.302031+00:00",
            "s": "2026-10-29T10:20:41.000000+00:00",
            "diff_ms": -302.031,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/21",
            "completed_at": "2026-10-29T10:20:41.906553+00:00",
            "s": "2026-10-29T10:20:41.000000+00:00",
            "diff_ms": -906.553,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/22",
            "completed_at": "2026-10-29T10:20:42.510889+00:00",
            "s": "2026-10-29T10:20:42.000000+00:00",
            "diff_ms": -510.889,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/23",
            "completed_at": "2026-10-29T10:20:43.115092+00:00",
            "s": "2026-10-29T10:20:42.000000+00:00",
            "diff_ms": -1115.092,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/24",
            "completed_at": "2026-10-29T10:20:43.718381+00:00",
            "s": "2026-10-29T10:20:43.000000+00:00",
            "diff_ms": -718.381,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/25",
            "completed_at": "2026-10-29T10:20:44.322562+00:00",
            "s": "2026-10-29T10:20:44.000000+00:00",
            "diff_ms": -322.562,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/26",
            "completed_at": "2026-10-29T10:20:44.935020+00:00",
            "s": "2026-10-29T10:20:44.000000+00:00",
            "diff_ms": -935.02,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/27",
            "completed_at": "2026-10-29T10:20:45.539012+00:00",
            "s": "2026-10-29T10:20:45.000000+00:00",
            "diff_ms": -539.012,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/28",
            "completed_at": "2026-10-29T10:20:46.165906+00:00",
            "s": "2026-10-29T10:20:45.000000+00:00",
            "diff_ms": -1165.906,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/29",
            "completed_at": "2026-10-29T10:20:46.792849+00:00",
            "s": "2026-10-29T10:20:46.000000+00:00",
            "diff_ms": -792.849,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/30",
            "completed_at": "2026-10-29T10:20:47.397855+00:00",
            "s": "2026-10-29T10:20:47.000000+00:00",
            "diff_ms": -397.855,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/31",
            "completed_at": "2026-10-29T10:20:48.002531+00:00",
            "s": "2026-10-29T10:20:47.000000+00:00",
            "diff_ms": -1002.531,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/32",
            "completed_at": "2026-10-29T10:20:48.613430+00:00",
            "s": "2026-10-29T10:20:48.000000+00:00",
            "diff_ms": -613.43,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/33",
            "completed_at": "2026-10-29T10:20:49.217882+00:00",
            "s": "2026-10-29T10:20:48.000000+00:00",
            "diff_ms": -1217.882,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/34",
            "completed_at": "2026-10-29T10:20:49.828820+00:00",
            "s": "2026-10-29T10:20:49.000000+00:00",
            "diff_ms": -828.82,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/35",
            "completed_at": "2026-10-29T10:20:50.437442+00:00",
            "s": "2026-10-29T10:20:50.000000+00:00",
            "diff_ms": -437.442,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/36",
            "completed_at": "2026-10-29T10:20:51.041022+00:00",
            "s": "2026-10-29T10:20:50.000000+00:00",
            "diff_ms": -1041.022,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/37",
            "completed_at": "2026-10-29T10:20:51.649748+00:00",
            "s": "2026-10-29T10:20:51.000000+00:00",
            "diff_ms": -649.748,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/38",
            "completed_at": "2026-10-29T10:20:52.253111+00:00",
            "s": "2026-10-29T10:20:51.000000+00:00",
            "diff_ms": -1253.111,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/39",
            "completed_at": "2026-10-29T10:20:52.858801+00:00",
            "s": "2026-10-29T10:20:52.000000+00:00",
            "diff_ms": -858.801,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/40",
            "completed_at": "2026-10-29T10:20:53.461793+00:00",
            "s": "2026-10-29T10:20:53.000000+00:00",
            "diff_ms": -461.793,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/41",
            "completed_at": "2026-10-29T10:20:54.066285+00:00",
            "s": "2026-10-29T10:20:53.000000+00:00",
            "diff_ms": -1066.285,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/42",
            "completed_at": "2026-10-29T10:20:54.670743+00:00",
            "s": "2026-10-29T10:20:54.000000+00:00",
            "diff_ms": -670.743,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/43",
            "completed_at": "2026-10-29T10:20:55.273195+00:00",
            "s": "2026-10-29T10:20:54.000000+00:00",
            "diff_ms": -1273.195,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/44",
            "completed_at": "2026-10-29T10:20:55.877819+00:00",
            "s": "2026-10-29T10:20:55.000000+00:00",
            "diff_ms": -877.819,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/45",
            "completed_at": "2026-10-29T10:20:56.480581+00:00",
            "s": "2026-10-29T10:20:56.000000+00:00",
            "diff_ms": -480.581,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/46",
            "completed_at": "2026-10-29T10:20:57.086812+00:00",
            "s": "2026-10-29T10:20:56.000000+00:00",
            "diff_ms": -1086.812,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/47",
            "completed_at": "2026-10-29T10:20:57.690404+00:00",
            "s": "2026-10-29T10:20:57.000000+00:00",
            "diff_ms": -690.404,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/48",
            "completed_at": "2026-10-29T10:20:58.294274+00:00",
            "s": "2026-10-29T10:20:57.000000+00:00",
            "diff_ms": -1294.274,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/49",
            "completed_at": "2026-10-29T10:20:58.902745+00:00",
            "s": "2026-10-29T10:20:58.000000+00:00",
            "diff_ms": -902.745,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/50",
            "completed_at": "2026-10-29T10:20:59.506592+00:00",
            "s": "2026-10-29T10:20:59.000000+00:00",
            "diff_ms": -506.592,
            "within": false
          },
          {
            "key": "probe/20261029T102027Z-4deccf3f/51",
            "completed_at": "2026-10-29T10:21:00.110425+00:00",
            "s": "2026-10-29T10:20:59.000000+00:00",
            "diff_ms": -1110.425,
            "within": false
          }
        ]
      }
    }
  ]
}
```
