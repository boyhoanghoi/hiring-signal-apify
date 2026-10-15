import argparse
import asyncio
import json
from pathlib import Path

from .config import RunConfig
from .output import export_results, rolling_known_ids
from .runner import scrape_boards


def main() -> int:
    parser = argparse.ArgumentParser(description="HiringSignal: public Greenhouse, Lever and Ashby job feeds.")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Fetch, filter and export public job postings.")
    run.add_argument("--input", required=True, type=Path)
    run.add_argument("--output", default=Path("output"), type=Path)
    args = parser.parse_args()
    try:
        config = RunConfig.from_dict(json.loads(args.input.read_text(encoding="utf-8-sig")))
        report = asyncio.run(scrape_boards(config))
        report["knownJobIds"], report["summary"]["knownJobIdsTruncated"] = rolling_known_ids(config.known_job_ids, report["results"])
        export_results(report, args.output)
    except (OSError, ValueError, RecursionError) as exc:
        parser.exit(2, f"HiringSignal: {exc}\n")
    except KeyboardInterrupt:
        parser.exit(130, "HiringSignal: interrupted.\n")
    print(f"Saved {len(report['results'])} jobs to {args.output.resolve()}; {report['summary']['failedBoards']} failed boards.")
    return 1 if report["summary"]["failedBoards"] and not report["results"] else 0
