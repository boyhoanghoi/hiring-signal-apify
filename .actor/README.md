# AI & Data Jobs Finder | HiringSignal

![HiringSignal: selected employer feeds to a reviewable jobs shortlist](https://raw.githubusercontent.com/boyhoanghoi/hiring-signal-apify/main/assets/launch/jobs-finder.png)

Turn selected public employer job boards into a shortlist for your AI/Data
newsletter or niche job board. Choose a curated company group and role preset,
then download matching jobs as CSV, JSON and a Markdown newsletter draft.
Greenhouse, Lever and Ashby feeds share one normalized schema with source links.

[Step-by-step first run](https://github.com/boyhoanghoi/hiring-signal-apify/blob/main/docs/FIRST_RUN.md) ·
[Hướng dẫn tiếng Việt](https://github.com/boyhoanghoi/hiring-signal-apify/blob/main/docs/FIRST_RUN_VI.md)

## Start with six matching jobs

```json
{
  "companyGroup": "ai",
  "rolePreset": "data-ai",
  "maxJobs": 6,
  "maxJobsPerBoard": 2
}
```

Run this small input, inspect the jobs and their application requirements, then
open **Output → Newsletter jobs shortlist (Markdown)** for a draft you can edit. This input saves
at most six matching jobs and at most two per board; availability changes, so it
may return fewer or zero. Six saved rows correspond to $0.009 in `job-saved`
events at the configured price. Check Pricing and the run's platform charges.

The watchlist is a starting point, not a complete AI-company directory, a global
job search or an endorsement by listed employers. The newsletter contains only
saved rows in provider order. It is not a newest-first ranking and is not posted
anywhere automatically.

## Pick your employer watchlist

`companyGroup` accepts `none`, `ai`, `developer-tools`, `fintech` or `all`.
The built-in catalog associates selected employer display names with public ATS
board keys. Inspect the current **EMPLOYER_CATALOG** output or run the standalone
CLI's `hiringsignal catalog` command for the actual roster and preset terms.
See the [catalog notes](https://github.com/boyhoanghoi/hiring-signal-apify/blob/main/docs/CATALOG.md)
for scope and verification context.

You can also supply `boards`:

```json
{
  "companyGroup": "none",
  "rolePreset": "engineering",
  "boards": ["greenhouse:stripe", "ashby:ashby"],
  "maxJobs": 6,
  "maxJobsPerBoard": 3,
  "knownJobIds": []
}
```

When both are supplied, explicit boards run first and the company group's boards
are added without duplicates. Use `companyGroup: "none"` for only your own
boards. The combined selection must contain 1–30 unique boards. To try only the
AI preset, clear any older explicit `boards` input.

Supported board forms include `greenhouse:stripe`, `lever:leverdemo`,
`lever-eu:yourboard`, `ashby:ashby`, and HTTPS public board URLs on
`boards.greenhouse.io`, `job-boards.greenhouse.io`, `jobs.lever.co`,
`jobs.eu.lever.co` and `jobs.ashbyhq.com`. Ashby capitalization is preserved.
Arbitrary API endpoints, custom careers domains and redirects are not accepted.

HiringSignal reads official public JSON feeds. It needs no ATS API key or proxy.
It does not submit applications, read private candidate data, bypass access
restrictions or support LinkedIn, Indeed or social-media scraping.

## Refine matching jobs

`rolePreset` accepts `all`, `data-ai`, `engineering`, `product-design` or
`sales-marketing`. Presets match case-insensitive title words or phrases from
the catalog; they are practical title filters, not an AI assessment of the role.
The `all` preset adds no role restriction.

Optional `includeTitleKeywords`, `excludeTitleKeywords` and `locationKeywords`
use case-insensitive substring matching. Terms within each list are OR; different
filter lists and the role preset combine with AND. Exclusion takes priority.
All filters apply **before saving and billing**.

`remoteOnly` requires an explicit provider remote field, excluding hybrid and
unknown jobs. A remote-looking title or location is not enough. Greenhouse's
list feed generally has no explicit workplace field, so its jobs usually do not
pass this filter. **Remote does not mean eligible to work from every country.**
Check each source posting's location, work authorization and application terms.

`publishedAfter` is an inclusive ISO date or timestamp. When set, jobs with an
unknown publication date are excluded. Greenhouse `updated_at` is a modification
date and never substitutes for publication. Lever public jobs generally lack a
documented publication date. Ashby `publishedAt` means **last published**, not
necessarily first posted. `publishedAtMeaning` preserves that distinction.

Defaults `companyGroup: "none"` and `rolePreset: "all"` preserve existing manual
watchlist workflows. The displayed starter input chooses AI/Data explicitly.

## Output you can use

The dataset has one row per normalized, filtered job actually saved:

| Fields | Meaning |
| --- | --- |
| `id`, `jobKey`, `source`, `boardKey` | Source ID and stable provider/board/job identity |
| `company`, `companySource` | Employer board slug and its source |
| `companyDisplayName`, `companyDisplayNameSource` | Curated display label when known, otherwise the board slug, with provenance |
| `title`, `locations`, `department`, `team` | Published job fields when available |
| `workplaceType`, `workplaceTypeSource` | Explicit remote/hybrid/onsite value or unknown |
| `employmentType`, `descriptionText` | Published employment label and cleaned job content |
| `jobUrl`, `applyUrl` | Source job/application links when exposed |
| `publishedAt`, `publishedAtMeaning`, `updatedAt` | Publication and modification dates kept distinct |
| `salary` | Source compensation only; null when absent |
| `fieldSources`, `requestUrl`, `observedAt` | JSON field mapping, source API and observation time |

The Output tab also links spreadsheet-safe CSV, `newsletter.md`, `SUMMARY`,
`DIAGNOSTICS`, `KNOWN_JOB_IDS`, `EMPLOYER_CATALOG` and complete `OUTPUT` JSON.
The Markdown draft includes titles, employer labels, locations, workplace labels
and source application/job links. Review it before republishing.

Diagnostics report per-board fetched/filtered/invalid/saved counts, errors and
completion flags. Summary signals use **only saved rows**, not total employer
hiring. A board name in the catalog does not guarantee its feed is currently
available or contains matching roles.

## Repeat without paying for known keys

Copy the **KNOWN_JOB_IDS** JSON array into the next run's `knownJobIds`. Only
previous keys and jobs actually saved in this run enter this rolling union.
Filtered, failed or unpaid jobs are not marked seen. Keys are checked before
saving and billing.

Up to 10,000 keys are retained; the oldest are dropped and
`knownJobIdsTruncated` is true if the union grows larger. An evicted key can
appear again. This is a bounded seen-list, not an unlimited history database.
Scheduling the same input does not automatically copy state: your workflow must
save the new array and supply it in the following run.

An unknown key means **not in your supplied seen-list**, not newly published.
Previously saved jobs with changed descriptions remain skipped by key. An absent
job is never labeled closed. Capped, filtered, rate-limited or failed boards
cannot establish a full employer snapshot or hiring growth.

The standalone CLI can load a previous export directly:

```powershell
hiringsignal run --input examples/ai-data-newsletter.json --previous-ids output/known_job_ids.json --output output-next
```

The combined input seen-list must still fit the 10,000-key bound.

## Pricing and limits

The configured Actor fee is **$0.0015 per saved job ($1.50 per 1,000)**. The
Store Pricing tab controls current terms. In pay-per-event mode, `job-saved`
occurs once per successfully normalized, filtered, saved dataset row. Errors,
empty boards, filtered jobs and known keys do not generate this event. Check
displayed platform charges as well as the Actor price; infrastructure may still
be used when no row is saved. Your spending limit bounds persisted results.

Limits: 30 selected boards, 1,000 saved jobs per run, 1,000 per board, 8 MiB
decoded JSON per response, 80 HTTP attempts per run, 20 Lever pages per board,
5,000 processed source records per board and 12,000 description characters per
saved job. Transient requests receive at most one retry with paced requests and
a bounded retry wait. No JavaScript pages or private ATS endpoints are read.

Source fields may be absent or change. Salary is not estimated; currencies and
compensation intervals remain as published. Check source links and diagnostics
before making hiring or research decisions. Respect source content terms when
republishing jobs.

## Support

Open the Actor's Issues tab with the provider, public board, run ID, expected
field and observed result. Remove tokens and private data from reports.
