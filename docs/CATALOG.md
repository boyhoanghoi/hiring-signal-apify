# Curated employer catalog

Verified against bounded official public JSON feeds on **16 October 2026**. This is a small editorial watchlist for newsletter and job-board workflows, not a global search index. Names identify public boards; none are customer or endorsement claims.

| Employer | Board key | Collection | Verification |
| --- | --- | --- | --- |
| [ElevenLabs](https://jobs.ashbyhq.com/elevenlabs) | `ashby:elevenlabs` | ai | 2026-10-16 |
| [Perplexity](https://jobs.ashbyhq.com/perplexity) | `ashby:perplexity` | ai | 2026-10-16 |
| [Cursor](https://jobs.ashbyhq.com/cursor) | `ashby:cursor` | ai, developer-tools | 2026-10-16 |
| [Palantir](https://jobs.lever.co/palantir) | `lever:palantir` | ai | 2026-10-16 |
| [Figma](https://job-boards.greenhouse.io/figma) | `greenhouse:figma` | developer-tools | 2026-10-16 |
| [Vercel](https://job-boards.greenhouse.io/vercel) | `greenhouse:vercel` | developer-tools | 2026-10-16 |
| [Linear](https://jobs.ashbyhq.com/linear) | `ashby:linear` | developer-tools | 2026-10-16 |
| [Notion](https://jobs.ashbyhq.com/notion) | `ashby:notion` | developer-tools | 2026-10-16 |
| [Supabase](https://jobs.ashbyhq.com/supabase) | `ashby:supabase` | developer-tools | 2026-10-16 |
| [Ashby](https://jobs.ashbyhq.com/ashby) | `ashby:ashby` | developer-tools | 2026-10-16 |
| [PostHog](https://jobs.ashbyhq.com/PostHog) | `ashby:PostHog` | developer-tools | 2026-10-16 |
| [Stripe](https://job-boards.greenhouse.io/stripe) | `greenhouse:stripe` | fintech | 2026-10-16 |
| [Coinbase](https://job-boards.greenhouse.io/coinbase) | `greenhouse:coinbase` | fintech | 2026-10-16 |
| [Plaid](https://jobs.ashbyhq.com/plaid) | `ashby:plaid` | fintech | 2026-10-16 |

14 unique employers: AI (4), developer tools (8), fintech (3). Cursor is in two collections. Custom `boards` come first, followed by the selected `companyGroup`; overlaps are removed by exact provider/board identity. `all` chooses these 14 entries. Ashby board capitalization is preserved.

Availability and job counts can change. A feed was reachable on the verification date; this is not a guarantee that every run succeeds. A failed or oversized board is reported in `DIAGNOSTICS`, and `SUMMARY.search.resolvedBoards` records exactly which boards were selected.

Some large employer feeds exceed the 8 MiB decoded response bound. Those candidates were excluded from these watchlists; the reader reports a bounded failure instead of silently fetching an unbounded response. Lever verification sampled its first page, not a total count.

## Exact title-preset terms

These are case-insensitive whole words or phrases, including flexible whitespace within a phrase. They are convenience filters, not inferred skills or occupation classifications. Custom title inclusion/exclusion, location, explicit remote and date filters also apply. All filters run before persistence and billing.

- `all`: all titles.
- `data-ai`: data, machine learning, ml, ai, artificial intelligence, analytics, scientist.
- `engineering`: engineer, engineering, developer, devops, sre, architect.
- `product-design`: product manager, product management, designer, design, ux, ui.
- `sales-marketing`: sales, marketing, account executive, business development, growth, demand generation.

Inspect the machine-readable registry without network requests:

```powershell
.\.venv\Scripts\python.exe -m hiringsignal catalog
```

The cloud Output tab exposes the same registry under `EMPLOYER_CATALOG`. Display names use `companyDisplayNameSource=curated-employer-catalog`; unrecognized custom boards keep their slug. The existing `company` and stable `jobKey` fields retain their original meanings.
