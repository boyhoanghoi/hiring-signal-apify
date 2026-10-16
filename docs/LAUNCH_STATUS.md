# HiringSignal feed release verification

Verified **16 October 2026 (Asia/Saigon)**.

- [Public Actor](https://apify.com/reliable_quatrain/greenhouse-lever-ashby-jobs-hiring-signal): **AI & Tech Jobs Finder | Greenhouse, Lever & Ashby**.
- [GitHub source](https://github.com/boyhoanghoi/hiring-signal-apify).
- Actor `2VTBeCh22BK3amvDJ`; latest build **0.3.1**, ID `dtYBVUZGuucG79BNh`, succeeded.
- Runtime source commit: `8c1fbd4d34c72d39085f69ebab16178696591fe6`. Python package version `0.3.0`; cloud build patch numbering is independent.
- **42 Python unit/integration tests passed**. Official Apify CLI validated all three input, dataset and output schemas. `git diff --check` passed before release.
- Anonymous Actor metadata confirmed public visibility, latest build and the existing single `job-saved` event at **USD 0.0015 per saved matching job**. No pricing change was submitted.
- Public Store returned HTTP 200 and includes the RSS/JSON Feed documentation and employment-type input.

## Useful workflows

The Actor retains 14 curated employers, role-title presets, explicit known-key
handoff, CSV and saved-row-only newsletter Markdown. This release adds:

- `jobs.rss` (RSS 2.0) and `jobs.feed.json` (JSON Feed 1.1), containing exactly
  the saved results. Their stable identifiers are the original job keys.
- Optional `employmentTypes` filtering from explicit source labels, with
  `employmentTypeNormalized` and source provenance. Missing/ambiguous labels
  remain `unknown`.
- A failed run status when every attempted employer feed fails and no jobs
  are saved, with diagnostics and empty exports retained. A successful empty
  source or no filter matches remains a successful result.

See [FEED_INTEGRATION.md](FEED_INTEGRATION.md) and the
[Vietnamese guide](FEED_INTEGRATION_VI.md) for downstream integration, static
feed hosting and explicit state handoff. Source dates are never replaced by
observation dates. A run output is a static export; feed hosting and repeated
`KNOWN_JOB_IDS` handoff remain the consumer's responsibility.

## Cloud integration checks

Each owner test used a USD 0.01 maximum charge limit.

| Check | Run ID | Observed result |
| --- | --- | --- |
| Three-provider starter | `IdkxRscuI7UbdMpwJ` | Succeeded; 3 rows, 3 events, all 3 providers, no failed boards |
| Exact full-time filter | `sa97cpPa3Kz7jZgDA` | Succeeded; 1 Ashby full-time row, 1 event, no failed boards |

Both tests verified exact correspondence between dataset keys, RSS GUIDs,
JSON Feed item IDs and `KNOWN_JOB_IDS`; saved-only item counts; normalized
employment fields; source-date semantics; and the `application/rss+xml` /
`application/feed+json` response types. Final event counts matched saved rows
and `SUMMARY`. The starter retained `unknown` for two providers' missing
employment labels rather than guessing full-time status.

Observed platform usage: USD 0.0007170008822745748 and
0.0004285010489821435. Build usage: USD 0.003974666666666667. These are sample
infrastructure measurements from owner tests, not revenue or a fixed run cost.

## Launch materials and scope

- [First-run guide](FIRST_RUN.md), [Vietnamese guide](FIRST_RUN_VI.md),
  [catalog](CATALOG.md) and [full-time feed input](../examples/full-time-ai-feed.json).
- [Post drafts](LAUNCH_POSTS.md) and [customer validation plan](ACQUISITION_PLAN_VI.md).
- Store README product image: `assets/launch/jobs-finder.png`.
- Separate Actor icon: `assets/brand/icon-512.png` is ready for manual upload;
  this release does not claim that it has been uploaded.

Owner tests are not customer revenue. No first customer or payout is claimed.
No promotional messages or posts have been sent. Missing jobs never become
closure claims. LinkedIn, Indeed and social-media sources are not implemented.

## Previous release evidence

Build `0.2.1` / `12ABV9NASLbyM7UCQ` used runtime source
`da79a811edb204ac27e5112b03638b4696e1d7c7`. Its runs
`r1sLWBIM3vUDAWwWi` and `zFYEcQgQpsChXmak1` each saved five jobs; the repeat
skipped the prior five keys with no overlap. The current 42-test suite retains
coverage of the known-key and billing behavior. Machine-readable previous
release and current cloud evidence are in [launch.json](launch.json).
