# HiringSignal Jobs Finder: release verification

Verified **16 October 2026 (Asia/Saigon)**.

- [Public Actor](https://apify.com/reliable_quatrain/greenhouse-lever-ashby-jobs-hiring-signal): **AI & Tech Jobs Finder | Greenhouse, Lever & Ashby**.
- [GitHub source](https://github.com/boyhoanghoi/hiring-signal-apify).
- Actor ID `2VTBeCh22BK3amvDJ`; latest cloud build **0.2.1**, ID `12ABV9NASLbyM7UCQ`, succeeded. Python package version is `0.2.0`; cloud build patch numbering is independent.
- **32 Python unit/integration tests passed**, including group union, role-word boundaries, source names, Markdown escaping, explicit seen-list handoff and billing limits.
- Official Apify CLI validated input, dataset and output schemas.
- Existing single `job-saved` event remains **USD 0.0015 per saved matching job**. No price change was submitted.
- Anonymous Actor metadata confirmed public visibility and the latest build. Store returned HTTP 200 and contains the new product image and `companyGroup` input. The GitHub-hosted image returned HTTP 200.

## Useful workflow now available

The same Actor now includes 14 curated employers across AI, developer tools and
fintech; role-title presets; sourced employer display labels; saved-row-only
`newsletter.md`; `EMPLOYER_CATALOG`; and local `--previous-ids` loading. Existing
manual-board input remains supported. See [CATALOG.md](CATALOG.md) for exact scope
and verification date, and [FIRST_RUN_VI.md](FIRST_RUN_VI.md) for a small trial.

## Cloud integration checks

Both tests combined the AI group with explicit Figma and Palantir boards,
`rolePreset=data-ai`, a five-job global limit and one saved job per board. Each
run used a USD 0.01 maximum charge limit. Output is deliberately capped.

| Check | Run ID | Observed result |
| --- | --- | --- |
| First run | `r1sLWBIM3vUDAWwWi` | Succeeded; 5 rows, 5 `job-saved` events, all 3 providers, no failed boards |
| Seen-list repeat | `zFYEcQgQpsChXmak1` | Succeeded; 5 previous keys skipped; 5 different rows and events; no overlap in saved job keys |

Both runs returned the 14-entry catalog, correct search context, display-name
provenance and a Markdown digest containing exactly the five saved jobs. Final
run event counts were fetched after completion and compared with the dataset
and `SUMMARY` counts.

Observed platform usage for these owner tests: USD 0.000654895523723629 and
0.0006694522769335244. The build used USD 0.004297777777777778. These are sample
infrastructure measurements, not revenue or a prediction of every run's cost.

Local starter smoke saved six matching jobs; its repeat skipped the six prior
keys and saved six different jobs. Some boards were capped/skipped as expected;
the summary and newsletter explicitly report partial coverage.

## Launch materials

- [First-run guide](FIRST_RUN.md) and [Vietnamese guide](FIRST_RUN_VI.md).
- [English/Vietnamese post drafts](LAUNCH_POSTS.md) and [customer validation plan](ACQUISITION_PLAN_VI.md).
- Product image: `assets/launch/jobs-finder.png`; editable SVG and reproduction
  script are in the repository. The image is visible in the Store README.
- Actor icon: `assets/brand/icon-512.png` is ready for upload under
  [Publishing / Display information](https://console.apify.com/actors/2VTBeCh22BK3amvDJ/publication).
  The separate top-level Actor icon has not been uploaded by this release.

Owner tests are not customer revenue. No first customer or payout is claimed.
Post drafts have not been published and no promotional messages have been sent.
Cloud schedules still need explicit `KNOWN_JOB_IDS` handoff; missing jobs never
become closure claims. LinkedIn, Indeed and social-media sources are not
implemented in this Actor.

## Previous release

Build `0.1.1` / `T72cZc6bICBXkA1sD` was checked with runs
`6fbnLvEU9xgDEu26A` and `r1SzqsTWEOhdCIhpb`. They verified the three-provider
reader and repeat-key billing behavior. Current release evidence supersedes
those checks for the new Jobs Finder workflow.
