# Development and Apify deployment

## Source API contracts

The implementation reads the official public feed endpoints only:

- [Greenhouse Job Board API](https://developers.greenhouse.io/job-board.html):
  `/v1/boards/{slug}/jobs?content=true`. The list includes job content and
  metadata. Its modification timestamp is not treated as a posting date.
- [Lever Postings API](https://github.com/lever/postings-api): JSON pages under
  `/v0/postings/{slug}`, using skip/limit. Global and EU instances are supported.
- [Ashby public job posting API](https://developers.ashbyhq.com/docs/public-job-posting-api):
  `/posting-api/job-board/{slug}?includeCompensation=true`. Unlisted jobs are
  excluded; explicit remote, publication and compensation fields are preserved.

These are public employer postings, not private recruiting/candidate APIs. The
Actor sends GET requests only. Output URLs are source data and are not crawled.
Transport allows the four official API hosts and refuses every redirect.

## Limits and diagnostics

Boards run sequentially, retaining bounded JSON and normalized results in memory.
Each API request has a timeout, at most one transient retry, an 8 MiB decoded-body
limit and paced provider access. Provider errors become board diagnostics. The
run saves at most 1,000 descriptions of at most 12,000 characters, fitting a
512 MB default deployment; malformed records are counted and skipped.

`coverageComplete` means all exposed feed records were evaluated without invalid
records or a cap/error. It does not mean all employer jobs exist in these feeds.
Filtering can yield no saved records after a successful complete read. Saved-job
signals never represent a full employer hiring count unless you independently
establish complete coverage and account for filters. Closed jobs are not inferred.

## Deploy

Authenticate from your own terminal using the Apify CLI, then run `apify push`
from the repository root. Actor metadata points to the root Dockerfile and the
Store-specific README. Set the cloud default run timeout to **300 seconds** and
memory to **512 MB**. Metadata bounds memory to 256–1,024 MB. No account token
belongs in source control or input.

Test a small public board input, invalid board input, failed provider response,
zero matches, known-ID skip and a tiny spending cap. Inspect dataset rows,
`results.csv`, `SUMMARY`, `DIAGNOSTICS` and `KNOWN_JOB_IDS` before public launch.

## Active monetization

Pay-per-event is active on the public Actor with event key `job-saved` at
**$0.0015 per saved job ($1.50 per 1,000)**. The configuration was accepted by
Apify and verified through paid-mode cloud runs. This is not evidence of a
paying customer. Keep synthetic dataset/start fees at zero to avoid an
undisclosed duplicate charge. The published Pricing tab is authoritative.

In pay-per-event runs, the Python SDK's `Actor.push_data(row,
charged_event_name='job-saved')` persists the affordable row before recording the
explicit charge, under the SDK's charging lock. The Actor preflights the combined
event/dataset budget, reduces its job cap and honors the final affordable row.
Failures, invalid rows, filters, duplicates and known jobs do not reach this call.
Only successfully saved rows enter CSV, JSON and next-run known keys.

The SDK integration follows the official
[pay-per-event guide](https://docs.apify.com/sdk/python/docs/concepts/pay-per-event).
Local simulation may use `ACTOR_TEST_PAY_PER_EVENT=true`; without platform pricing,
the SDK's simulated event price is $1, not the active $0.0015. Never set the test
flag in a cloud production run. Publication and seller eligibility are platform
account operations, separate from building this source package.

## Reusing known IDs

The stable key includes provider, board and source ID. Ashby IDs may be read from
the source's public job URL when no explicit ID is supplied; the mapping says so.
Keys from successfully saved rows are merged with prior input keys in order,
retaining the most recent 10,000. The summary marks truncation. Keep a separate
durable database if you require an unlimited historical seen-list. A known-ID
skip says only that your input contained a key, never that a job is closed.
