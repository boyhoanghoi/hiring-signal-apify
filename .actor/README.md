# Greenhouse, Lever & Ashby Jobs Scraper | HiringSignal

Build one clean jobs dataset from public employer boards across three ATS
providers. Filter before saving, keep source links and JSON-field provenance,
and pass saved job keys into the next run to avoid paying for repeats.

## Useful workflows

- Recruitment teams: collect matching roles from an existing employer watchlist.
- Niche job boards: export titles, locations, descriptions and application links.
- Research teams: count saved roles by employer, department and explicit workplace
  type, with coverage flags before drawing conclusions.
- Automation builders: schedule through Apify and feed `KNOWN_JOB_IDS` into a
  later run's `knownJobIds` input to collect jobs you have not saved before.

HiringSignal uses public, official JSON feeds. It needs no ATS API key or proxy.
It does not search the entire internet, submit applications, find candidates or
bypass access restrictions. You supply the employer boards.

## Start with a small run

```json
{
  "boards": ["greenhouse:stripe", "lever:leverdemo", "ashby:ashby"],
  "maxJobs": 20,
  "maxJobsPerBoard": 8,
  "includeTitleKeywords": [],
  "excludeTitleKeywords": [],
  "locationKeywords": [],
  "remoteOnly": false,
  "knownJobIds": []
}
```

These public boards are examples, not customers or endorsements; availability
and posting counts change. The sample saves up to 20 jobs and is deliberately
partial. Increase the caps only after inspecting results and the Pricing tab.

Supported inputs include `greenhouse:stripe`, `lever:leverdemo`, `ashby:Ashby`,
`lever-eu:yourboard`, and HTTPS URLs on `boards.greenhouse.io`,
`job-boards.greenhouse.io`, `jobs.lever.co`, `jobs.eu.lever.co` and
`jobs.ashbyhq.com`. Ashby capitalization is preserved. Arbitrary API endpoints,
custom careers domains and redirects are not accepted.

## Filters

Title inclusion, title exclusion and location lists use case-insensitive substring
matching. Terms within a list are OR; different filter lists are combined with
AND. Exclusion takes priority. Filters apply **before saving and billing**.

`remoteOnly` requires an explicit provider remote field, and excludes hybrid and
unknown jobs. A remote-looking location or title is not enough. Greenhouse's
list endpoint generally has no explicit workplace field, so its jobs usually do
not pass this filter.

`publishedAfter` is an inclusive ISO date or timestamp. When it is set, jobs with
unknown publication dates are excluded. Greenhouse `updated_at` is a modification
date and is never substituted for publication. Lever public jobs generally lack
a documented publication date. Ashby `publishedAt` means **last published**, not
necessarily first posted. The separate `publishedAtMeaning` field explains this.

## Output

The default dataset has one row per normalized job that passes your filters and
is actually saved:

| Fields | Meaning |
| --- | --- |
| `id`, `jobKey`, `source`, `boardKey` | Source ID and stable provider/board/job identity |
| `company`, `companySource` | Employer **board slug**, not an invented legal/display name |
| `title`, `locations`, `department`, `team` | Published job fields when available |
| `workplaceType`, `workplaceTypeSource` | Explicit remote/hybrid/onsite value or unknown |
| `employmentType`, `descriptionText` | Published employment label and cleaned job content |
| `jobUrl`, `applyUrl` | Source job/application links when exposed |
| `publishedAt`, `publishedAtMeaning`, `updatedAt` | Publication and modification dates kept distinct |
| `salary` | Source compensation only; null when not exposed |
| `fieldSources`, `requestUrl`, `observedAt` | JSON field mapping, API source and observation time |

The Output tab also links spreadsheet-safe CSV, `SUMMARY`, `DIAGNOSTICS`,
`KNOWN_JOB_IDS` and the complete `OUTPUT` JSON. Diagnostics include per-board
fetched/filtered/invalid/saved counts, errors and completion flags. Signals in
the summary are calculated **only from saved rows**, not total employer hiring.

## Repeat runs without false closure claims

Copy `KNOWN_JOB_IDS` to the next run's `knownJobIds`. Only previous keys and jobs
actually saved in this run enter this rolling union. Filtered, failed or unpaid
jobs are not marked seen. Up to 10,000 keys are retained; the oldest are dropped
and `knownJobIdsTruncated` is true if the rolling union grows larger. An evicted
key can appear again in a future run. This is a bounded seen-list, not a durable
unlimited database or an automatic scheduler.

An absent job is **never** labeled closed. A capped, filtered, rate-limited or
failed board is not a complete employer snapshot. Even a fully read feed is an
observation at one time; this Actor does not infer openings, closures or growth
from missing records.

## Pricing and limits

The Actor fee is **$0.0015 per saved job ($1.50 per 1,000)**; check the Pricing
tab for current terms. In pay-per-event mode the event is `job-saved`,
once per successful, normalized, filtered dataset row. Errors, empty boards,
filtered jobs and previously known jobs do not generate job-saved events. Your
spending limit bounds persisted results; the final affordable job is retained.

Limits are 30 boards, 1,000 saved jobs per run, 1,000 saved jobs per board,
8 MiB decoded JSON per response, 80 HTTP attempts per run, 20 Lever pages per
board, 5,000 processed source records per board and 12,000 description characters
per saved job. A transient request is retried at most once, with paced requests
and a bounded retry wait. No JavaScript, private ATS data or applications are read.

Source fields may be absent or change. Salary is not estimated. Currencies and
compensation intervals remain as published. Review source links and coverage
diagnostics before using the data in a hiring or research decision.

## Support

Open the Actor's Issues tab with the provider, public board, run ID, expected
field and observed result. Remove tokens and private data from reports.
