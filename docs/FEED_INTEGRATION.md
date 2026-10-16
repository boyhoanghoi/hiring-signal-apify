# Import saved jobs into a feed or job board

HiringSignal provides two additional exports for each run:

- `jobs.rss`: RSS 2.0 (`application/rss+xml`).
- `jobs.feed.json`: JSON Feed 1.1 (`application/feed+json`).

The local CLI writes both files beside `results.csv`. On Apify, open the run's
Output tab and choose the corresponding feed. Exports include only rows actually
saved after filters, duplicate/known-key checks and spending limits. No extra
Actor event is charged for downloading these additional formats.

## Example: full-time roles for an AI newsletter

```json
{
  "companyGroup": "ai",
  "rolePreset": "data-ai",
  "employmentTypes": ["full-time"],
  "maxJobs": 6,
  "maxJobsPerBoard": 2
}
```

The employment filter matches exact normalized explicit source labels. It never
guesses full-time status from a title or description. Missing or ambiguous labels
are `unknown`, so this example can exclude otherwise relevant jobs. Leave
`employmentTypes` empty to apply no employment restriction.

## Connect a downstream consumer

1. Run the Actor with small limits, then inspect `SUMMARY` and `DIAGNOSTICS`.
2. Download one feed file and import it into your own consumer. Only use a
   consumer that accepts the selected format; no third-party product is bundled
   or claimed to have been tested by this project.
3. Use JSON Feed `items[].id` or RSS `guid` to upsert/deduplicate. Both contain
   the original stable `jobKey`, independent of a changed title or URL.
4. If you want a subscription at one stable URL, your own workflow must publish
   the chosen export to hosting you control and update it after successful runs.
   Never embed an Apify API token into a public feed URL. An Apify run output is
   a static artifact; scheduling does not turn it into a live subscription.
5. For incremental collection, keep `KNOWN_JOB_IDS` separately and pass it to the
   next input. A feed from such a run contains only that run's saved unseen keys,
   so merge it into your own archive rather than replacing the archive blindly.

## Field meanings and limitations

- JSON Feed uses `content_text`, not HTML. RSS content is escaped for XML and
  HTML readers. Original job content is never executable markup in these feeds.
- Feed description text is limited to 2,000 description characters per job. It
  is marked shortened when the description or original normalized row was
  truncated. Dataset JSON keeps the existing 12,000-character description bound.
- Source `publishedAt` is exported as RSS `pubDate` / JSON `date_published` only
  when available. Ashby reports last publication; its meaning is labeled in
  content and JSON extension metadata. An unseen key is not proof of a new job.
- `observedAt` appears as observation metadata. It never replaces a missing
  publication date. Greenhouse modification time remains JSON `date_modified`.
- Items retain provider order, not newest-first order. Remote does not mean
  worldwide eligibility. Open the original posting before redistributing it.
- An empty feed does not imply existing jobs closed. Source failures, filters,
  caps and known IDs can all remove records from an individual export. Consult
  diagnostics and your retained state rather than deleting missing jobs.
- A run whose every attempted source fails ends with a failed status and
  `sourceFailureFatal: true`. Exports and diagnostics are still available; no
  rows are saved or job events charged. An actually empty successful source or
  no filter matches remains a successful empty result.

The formats follow the first-party [RSS 2.0 specification](https://www.rssboard.org/rss-specification)
and [JSON Feed 1.1 specification](https://www.jsonfeed.org/version/1.1/).
