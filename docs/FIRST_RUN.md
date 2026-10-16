# Your first AI/Data jobs shortlist

Use this guide to prepare a reviewable shortlist for a niche job board or
newsletter. HiringSignal reads selected public employer ATS feeds, filters the
jobs and exports saved rows. It does not publish your newsletter.

## 1. Try a small cloud run

Open [HiringSignal on Apify](https://apify.com/reliable_quatrain/greenhouse-lever-ashby-jobs-hiring-signal),
select JSON input and replace the input with:

```json
{
  "companyGroup": "ai",
  "rolePreset": "data-ai",
  "maxJobs": 6,
  "maxJobsPerBoard": 2,
  "knownJobIds": []
}
```

Check the Pricing tab, use a small maximum spending limit appropriate to the
platform's displayed estimate, and run. At the configured Actor price, six saved
rows generate **$0.009 of job-saved events**. This is the event fee calculation,
not a promise of six results or an all-inclusive infrastructure quote.

The chosen group is a small curated watchlist, not all AI employers. Existing
manual `boards` are added first when both inputs are present: replace the full
input as above if you want only this preset. Source availability and title
matches change, so zero or fewer than six rows can be a valid result.

## 2. Review before publishing

- **Dataset / jobs:** inspect title, employer label, locations, source job URL and
  application link. Open the source posting to verify current requirements.
- **newsletter.md:** copy a Markdown shortlist into your own newsletter editor.
  It contains only saved rows and is a draft for your review.
- **results.csv:** import the spreadsheet-safe export into your job-board process
  or spreadsheet. JSON remains available for programmatic use.
- **SUMMARY / DIAGNOSTICS:** check failed boards, caps and partial coverage. Six
  saved jobs do not establish six total vacancies at these employers.
- **EMPLOYER_CATALOG:** inspect the curated employer labels, board keys and role
  terms used by this version.
- **KNOWN_JOB_IDS:** retain this JSON array for the next run.
- **jobs.rss / jobs.feed.json:** saved-only feeds for your own job-board or
  feed-reader workflow. They are static artifacts of this run. See the
  [integration guide](FEED_INTEGRATION.md) before using incremental exports.

The draft is in provider order, not newest-first. A job not previously saved can
be an older posting. Remote status requires explicit source metadata and does
not establish worldwide eligibility. Review location and work authorization.

## 3. Prepare your next shortlist

Copy the array from the first run's `KNOWN_JOB_IDS` record into the second input.
This illustrative template needs **your actual saved keys**; the strings below
are placeholders, not board identities you should run:

```json
{
  "companyGroup": "ai",
  "rolePreset": "data-ai",
  "maxJobs": 6,
  "maxJobsPerBoard": 2,
  "knownJobIds": ["paste-the-first-saved-jobKey-here", "paste-the-next-jobKey-here"]
}
```

Replace the entire placeholder array with the real one. Previously supplied
keys are skipped before saving or billing. With small caps, a second run can
save different jobs from the same feeds even if no employer published anything
new. Previously seen keys are not revisited for edits. Never label these
results "newly posted" solely because the key was unseen.

Each run returns the rolling union of previous and saved keys. Retain up to
10,000; watch `knownJobIdsTruncated` if the history fills. Evicted keys can
reappear. A scheduled Actor with unchanged input does not update its own state:
your automation must store the returned array and pass it to the next run.

## 4. Use your own selection

Choose `companyGroup`: `none`, `ai`, `developer-tools`, `fintech` or `all`.
Choose `rolePreset`: `all`, `data-ai`, `engineering`, `product-design` or
`sales-marketing`. Presets use defined case-insensitive title words/phrases,
not an assessment of the candidate or job description.

For a manual watchlist, select `companyGroup: "none"` and supply `boards` such as
`greenhouse:stripe` or `ashby:ashby`. Adding boards to a company group produces
their deduplicated union, manual boards first; the total is bounded to 30.
Other filters combine with the role preset using AND. Keyword/location lists
use substring OR within each list, and exclusions take priority.

Start with no location or remote restriction, inspect the source fields, then
refine. `remoteOnly: true` excludes unknown and hybrid roles. Greenhouse's list
feed usually lacks explicit remote metadata. `publishedAfter` excludes jobs
whose publication date is unknown; update dates never stand in for publication.
Lever commonly has no public publication date, and Ashby's date means last
published rather than necessarily first published.

## Local Python CLI

From the repository root on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[actor]"
.\.venv\Scripts\python.exe -m hiringsignal catalog
.\.venv\Scripts\python.exe -m hiringsignal run --input examples/ai-data-newsletter.json --output output
```

Open `output/newsletter.md`, `output/results.csv`, `output/diagnostics.json` and
`output/known_job_ids.json`. For the next run:

```powershell
.\.venv\Scripts\python.exe -m hiringsignal run --input examples/ai-data-newsletter.json --previous-ids output/known_job_ids.json --output output-next
```

`--previous-ids` reads the exported JSON array and merges it with input
`knownJobIds`. The combined list must fit the same 10,000-key input bound;
the CLI does not silently discard input to bypass validation. A later run can
then read `output-next/known_job_ids.json` and write to another directory.

Installing the project also provides `hiringsignal catalog` and
`hiringsignal run ...` in the active virtual environment. Local CLI runs do not
charge Apify events; they still use your machine and the source feeds.

## Before sharing the results

Check the source posting, its current application availability, geography and
content terms. No absence implies job closure, no saved-row count measures all
employer hiring, and no output proves an endorsement. This tool does not apply
for jobs, send emails or automatically publish a newsletter. Read the
[complete product guide](../.actor/README.md) for field meanings and bounds.
