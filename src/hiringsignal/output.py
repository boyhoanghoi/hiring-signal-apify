"""Lossless JSON and spreadsheet-safe CSV exports."""

import csv
import io
import json
from pathlib import Path


def spreadsheet_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    value = str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")) else value


def results_csv(rows: list[dict]) -> str:
    stream = io.StringIO(newline="")
    fields = ["id", "jobKey", "source", "board", "boardKey", "company", "companySource", "title", "locations", "department", "team",
              "workplaceType", "workplaceTypeSource", "employmentType", "descriptionText", "descriptionTruncated", "jobUrl",
              "applyUrl", "publishedAt", "publishedAtMeaning", "updatedAt", "salary", "fieldSources", "requestUrl", "observedAt"]
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: spreadsheet_cell(row.get(field)) for field in fields})
    return stream.getvalue()


def export_results(report: dict, directory: str | Path) -> None:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("results", "summary", "diagnostics"):
        (directory / f"{name}.json").write_text(json.dumps(report[name], indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    (directory / "results.csv").write_text("\ufeff" + results_csv(report["results"]), encoding="utf-8", newline="")
    if "knownJobIds" in report:
        (directory / "known_job_ids.json").write_text(json.dumps(report["knownJobIds"], indent=2) + "\n", encoding="utf-8")


def rolling_known_ids(previous, rows: list[dict]) -> tuple[list[str], bool]:
    union = list(dict.fromkeys([*previous, *(row["jobKey"] for row in rows)]))
    return union[-10000:], len(union) > 10000
