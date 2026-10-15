# HiringSignal

<img src="assets/brand/icon-512.png" width="72" height="72" alt="HiringSignal icon">

[Run on Apify Store](https://apify.com/reliable_quatrain/greenhouse-lever-ashby-jobs-hiring-signal) · [Vietnamese workflow guide](docs/WORKFLOW_COOKBOOK_VI.md) · [Launch verification](docs/LAUNCH_STATUS.md)

Public Greenhouse, Lever and Ashby employer jobs, normalized into one dataset.
The standalone Python CLI and Apify Actor share the same validation, mappings,
filters and export code. See the [Store product guide](.actor/README.md) for exact
field meanings, limits and coverage caveats.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[actor]"
.\.venv\Scripts\python.exe -m hiringsignal run --input examples/input.json --output output
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Local runs do not publish the Actor or charge Apify events. Output includes
`results.json`, `results.csv`, `summary.json`, `diagnostics.json` and
`known_job_ids.json`. JSON preserves observations; CSV escapes formula-like
cells. Pass saved `jobKey` values back as `knownJobIds` to skip prior results.

The configured Actor fee is $0.0015 per saved job ($1.50 per 1,000). The Store
Pricing tab controls the current price. Usage is not evidence of earned revenue.

Deployment and official API references are in [docs/README.md](docs/README.md).
The source is MIT licensed; employer job content remains subject to its owners'
terms and applicable use requirements.
