import argparse
import asyncio
import json
from pathlib import Path

from .config import RunConfig
from .output import export_results, rolling_known_ids
from .runner import scrape_boards, source_failure_is_fatal
from .catalog import catalog_document


def main() -> int:
    parser = argparse.ArgumentParser(description="HiringSignal: public Greenhouse, Lever and Ashby job feeds.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("catalog", help="Print the curated employers and exact role-preset title terms.")
    run = commands.add_parser("run", help="Fetch, filter and export public job postings.")
    run.add_argument("--input", required=True, type=Path)
    run.add_argument("--output", default=Path("output"), type=Path)
    run.add_argument("--previous-ids", type=Path, help="Read known_job_ids.json from an earlier run; merge with input knownJobIds.")
    args = parser.parse_args()
    if args.command == "catalog":
        print(json.dumps(catalog_document(), indent=2, ensure_ascii=False))
        return 0
    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        if args.previous_ids:
            # Validate each list before merging; do not let the CLI bypass limits.
            prior = json.loads(args.previous_ids.read_text(encoding="utf-8-sig"))
            current = RunConfig.from_dict(data)
            previous = RunConfig.from_dict({**data, "knownJobIds": prior})
            data["knownJobIds"] = list(dict.fromkeys([*current.known_job_ids, *previous.known_job_ids]))
        config = RunConfig.from_dict(data)
        report = asyncio.run(scrape_boards(config))
        report["summary"]["sourceFailureFatal"] = source_failure_is_fatal(report)
        report["knownJobIds"], report["summary"]["knownJobIdsTruncated"] = rolling_known_ids(config.known_job_ids, report["results"])
        export_results(report, args.output)
    except (OSError, ValueError, RecursionError) as exc:
        parser.exit(2, f"HiringSignal: {exc}\n")
    except KeyboardInterrupt:
        parser.exit(130, "HiringSignal: interrupted.\n")
    print(f"Saved {len(report['results'])} jobs to {args.output.resolve()}; {report['summary']['failedBoards']} failed boards.")
    return 1 if report["summary"]["sourceFailureFatal"] else 0
