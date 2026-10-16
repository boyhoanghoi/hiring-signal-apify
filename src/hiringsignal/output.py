"""Lossless JSON and spreadsheet-safe CSV exports."""

import csv
import io
import json
import re
from pathlib import Path
from urllib.parse import quote, urlsplit

from .feeds import json_feed, rss_feed


def spreadsheet_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    value = str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")) else value


def results_csv(rows: list[dict]) -> str:
    stream = io.StringIO(newline="")
    fields = ["id", "jobKey", "source", "board", "boardKey", "company", "companySource", "companyDisplayName", "companyDisplayNameSource", "title", "locations", "department", "team",
              "workplaceType", "workplaceTypeSource", "employmentType", "employmentTypeNormalized", "descriptionText", "descriptionTruncated", "jobUrl",
              "applyUrl", "publishedAt", "publishedAtMeaning", "updatedAt", "salary", "fieldSources", "requestUrl", "observedAt"]
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: spreadsheet_cell(row.get(field)) for field in fields})
    return stream.getvalue()


def _markdown_text(value: str) -> str:
    value = " ".join(str(value).split())
    return re.sub(r"([\\`*_{}\[\]()<>#!|])", r"\\\1", value)


def newsletter_markdown(rows: list[dict], summary: dict) -> str:
    """A reviewable digest of saved rows, never a claim of newly published jobs."""
    lines = ["# Jobs shortlist", "", f"{len(rows)} saved matching jobs from selected employer boards.", "",
             "Review each employer's requirements and application link before sharing. Remote status does not imply worldwide eligibility.", ""]
    observed = summary.get("observedAt")
    if observed:
        lines.extend([f"Observed: {_markdown_text(observed)}", ""])
    if summary.get("partialResults"):
        lines.extend(["Coverage is partial. See diagnostics for caps, skipped boards or failed sources.", ""])
    if not rows:
        lines.extend(["No matching jobs were saved in this run. Check filters and diagnostics.", ""])
    for row in rows:
        title = _markdown_text(row["title"])
        url = row.get("applyUrl") or row.get("jobUrl") or ""
        # Defense in depth for standalone callers; never emit executable links.
        try:
            parsed = urlsplit(url)
            safe = parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not parsed.username and not parsed.password
        except ValueError:
            safe = False
        link = f"[{title}]({quote(url, safe=':/?=&%+@,;~.-_')})" if safe else title
        company = _markdown_text(row.get("companyDisplayName") or row.get("company") or row.get("boardKey", ""))
        locations = _markdown_text("; ".join(row.get("locations", [])) or "Location not provided")
        workplace = _markdown_text(row.get("workplaceType", "unknown"))
        lines.extend([f"- {link} — **{company}**", f"  {locations} · Workplace: {workplace}", ""])
    lines.extend(["Source: HiringSignal / public employer job feeds. Provider order; not a newest-first ranking.", ""])
    return "\n".join(lines)


def export_results(report: dict, directory: str | Path) -> None:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("results", "summary", "diagnostics"):
        (directory / f"{name}.json").write_text(json.dumps(report[name], indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    (directory / "results.csv").write_text("\ufeff" + results_csv(report["results"]), encoding="utf-8", newline="")
    (directory / "newsletter.md").write_text(newsletter_markdown(report["results"], report["summary"]), encoding="utf-8")
    (directory / "jobs.rss").write_text(rss_feed(report["results"], report["summary"]), encoding="utf-8")
    (directory / "jobs.feed.json").write_text(json.dumps(json_feed(report["results"], report["summary"]), indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    if "knownJobIds" in report:
        (directory / "known_job_ids.json").write_text(json.dumps(report["knownJobIds"], indent=2) + "\n", encoding="utf-8")


def rolling_known_ids(previous, rows: list[dict]) -> tuple[list[str], bool]:
    union = list(dict.fromkeys([*previous, *(row["jobKey"] for row in rows)]))
    return union[-10000:], len(union) > 10000
