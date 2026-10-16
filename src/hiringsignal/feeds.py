"""Static RSS 2.0 and JSON Feed 1.1 exports of persisted jobs only."""

from email.utils import format_datetime
from html import escape
import re
from xml.etree import ElementTree as ET

from .config import iso_datetime
from .providers import safe_public_link


HOME_URL = "https://apify.com/reliable_quatrain/greenhouse-lever-ashby-jobs-hiring-signal"
FEED_DESCRIPTION = "Saved matching jobs from selected employer feeds. Provider order, not newest-first. Remote status does not imply worldwide eligibility."
MAX_FEED_DESCRIPTION = 2000


def _content(row: dict) -> tuple[str, bool]:
    description = row.get("descriptionText", "")
    truncated = len(description) > MAX_FEED_DESCRIPTION or bool(row.get("descriptionTruncated"))
    lines = [row.get("companyDisplayName") or row.get("company") or row.get("boardKey", ""),
             "Locations: " + ("; ".join(row.get("locations", [])) or "not provided"),
             "Workplace: " + row.get("workplaceType", "unknown"),
             "Employment: " + (row.get("employmentType") or "not provided")]
    if row.get("publishedAt"):
        lines.append(f"Source publication ({row.get('publishedAtMeaning') or 'unspecified meaning'}): {row['publishedAt']}")
    if row.get("observedAt"):
        lines.append("Observed: " + row["observedAt"])
    if description:
        lines.extend(["", description[:MAX_FEED_DESCRIPTION]])
    if truncated:
        lines.append("[Description shortened; open the original posting for complete requirements.]")
    return "\n".join(lines), truncated


def json_feed(rows: list[dict], summary: dict) -> dict:
    items = []
    for row in rows:
        content, truncated = _content(row)
        item = {"id": row["jobKey"], "title": row["title"], "content_text": content,
                "_hiringsignal": {"observedAt": row.get("observedAt"),
                    "publishedAtMeaning": row.get("publishedAtMeaning"), "descriptionTruncated": truncated,
                    "boardKey": row.get("boardKey"), "employmentTypeNormalized": row.get("employmentTypeNormalized", "unknown")}}
        url = safe_public_link(row.get("jobUrl"))
        if url:
            item["url"] = url
        apply_url = safe_public_link(row.get("applyUrl"))
        if apply_url and apply_url != url:
            item["external_url"] = apply_url
        for source, target in (("publishedAt", "date_published"), ("updatedAt", "date_modified")):
            timestamp = iso_datetime(row.get(source))
            if timestamp:
                item[target] = timestamp.isoformat().replace("+00:00", "Z")
        items.append(item)
    return {"version": "https://jsonfeed.org/version/1.1", "title": "HiringSignal jobs shortlist",
            "home_page_url": HOME_URL, "description": FEED_DESCRIPTION, "items": items,
            "_hiringsignal": {"scope": "saved-results-only", "partialResults": bool(summary.get("partialResults")),
                "observedAt": summary.get("observedAt"), "staticRunExport": True}}


def _xml_text(value: str) -> str:
    # JSON sources can legally include controls which XML 1.0 cannot represent.
    return re.sub(r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]", "", str(value))


def rss_feed(rows: list[dict], summary: dict) -> str:
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    for key, value in (("title", "HiringSignal jobs shortlist"), ("link", HOME_URL), ("description", FEED_DESCRIPTION)):
        ET.SubElement(channel, key).text = value
    observed = iso_datetime(summary.get("observedAt"))
    if observed:
        ET.SubElement(channel, "lastBuildDate").text = format_datetime(observed, usegmt=True)
    for row in rows:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = _xml_text(row["title"])
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = _xml_text(row["jobKey"])
        url = safe_public_link(row.get("jobUrl"))
        if url:
            ET.SubElement(item, "link").text = _xml_text(url)
        content, _ = _content(row)
        # RSS descriptions may be interpreted as HTML after XML decoding. Escape
        # source text once for HTML as well, so source markup remains inert.
        ET.SubElement(item, "description").text = escape(_xml_text(content))
        published = iso_datetime(row.get("publishedAt"))
        if published:
            ET.SubElement(item, "pubDate").text = format_datetime(published, usegmt=True)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8") + "\n"
