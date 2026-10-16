"""Provider field mappings; absence stays unknown, with no guessed dates/pay."""

from datetime import datetime, timezone
from html import unescape
import math
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup

from .config import Board, RunConfig, iso_datetime
from .catalog import employer_for, role_matches


MAX_DESCRIPTION = 12000
API_HOSTS = frozenset({"boards-api.greenhouse.io", "api.lever.co", "api.eu.lever.co", "api.ashbyhq.com"})


def normalized_employment_type(value: str) -> str:
    """Map only unambiguous, explicit source labels; never inspect job prose."""
    key = re.sub(r"[\s_-]+", "", value.casefold())
    return {
        "fulltime": "full-time", "parttime": "part-time",
        "contract": "contract", "contractor": "contract",
        "temporary": "temporary", "temp": "temporary",
        "internship": "internship", "intern": "internship",
        "freelance": "freelance", "freelancer": "freelance",
        "apprenticeship": "apprenticeship", "apprentice": "apprenticeship",
    }.get(key, "unknown")


def request_url(board: Board, offset: int = 0) -> str:
    if board.provider == "greenhouse":
        return f"https://boards-api.greenhouse.io/v1/boards/{board.slug}/jobs?content=true"
    if board.provider == "lever":
        host = "api.eu.lever.co" if board.region == "eu" else "api.lever.co"
        return f"https://{host}/v0/postings/{board.slug}?mode=json&skip={offset}&limit=100"
    if board.provider == "ashby":
        return f"https://api.ashbyhq.com/posting-api/job-board/{board.slug}?includeCompensation=true"
    raise ValueError("Unknown provider.")


def safe_public_link(raw: Any) -> str | None:
    if not isinstance(raw, str) or len(raw) > 2048 or any(c.isspace() or ord(c) < 32 for c in raw):
        return None
    try:
        p = urlsplit(raw)
        if p.scheme not in {"http", "https"} or not p.hostname or p.username or p.password:
            return None
        if p.port not in (None, 80, 443):
            return None
        return urlunsplit((p.scheme, p.netloc, p.path, p.query, ""))
    except ValueError:
        return None


def text(value: Any, maximum: int = 500) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()[:maximum]


def description(value: Any) -> tuple[str, bool]:
    if not isinstance(value, str):
        return "", False
    # Greenhouse can HTML-entity encode the full description more than once.
    value = unescape(unescape(value[:200000]))
    soup = BeautifulSoup(value, "html.parser")
    for node in soup.find_all(["script", "style", "noscript"]):
        node.decompose()
    plain = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    return plain[:MAX_DESCRIPTION], len(plain) > MAX_DESCRIPTION


def _date(raw: Any) -> str | None:
    parsed = iso_datetime(raw)
    return parsed.isoformat().replace("+00:00", "Z") if parsed else None


def _number(value: Any) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return value


def normalize_job(board: Board, raw: Any, url: str, observed_at: str | None = None) -> dict | None:
    if not isinstance(raw, dict) or raw.get("isListed") is False:
        return None
    sources: dict[str, str] = {"company": "input.boardSlug", "board": "input.boardSlug"}
    source_id = raw.get("id")
    if isinstance(source_id, bool) or not isinstance(source_id, (str, int)):
        source_id = None
    source_id = str(source_id).strip()[:200] if source_id is not None else ""
    job_url = safe_public_link(raw.get({"greenhouse": "absolute_url", "lever": "hostedUrl", "ashby": "jobUrl"}[board.provider]))
    if not source_id and board.provider == "ashby" and job_url:
        parts = urlsplit(job_url)
        segments = [part for part in parts.path.split("/") if part]
        if parts.hostname == "jobs.ashbyhq.com" and len(segments) >= 2 and segments[0] == board.slug:
            source_id = segments[1][:200]
            sources["id"] = "jobUrl:path[1]"
    else:
        sources["id"] = "id"
    title_field = "text" if board.provider == "lever" else "title"
    title = text(raw.get(title_field))
    if not source_id or not title or not job_url:
        return None
    sources.update({"title": title_field, "jobUrl": {"greenhouse": "absolute_url", "lever": "hostedUrl", "ashby": "jobUrl"}[board.provider]})
    row = {"id": source_id, "jobKey": f"{board.key}:{source_id}", "source": board.provider, "board": board.slug, "boardKey": board.key,
        "company": board.slug, "companySource": "board-slug", "title": title, "locations": [],
        "department": "", "team": "", "workplaceType": "unknown", "workplaceTypeSource": None,
        "employmentType": "", "descriptionText": "", "descriptionTruncated": False,
        "jobUrl": job_url, "applyUrl": None, "publishedAt": None, "publishedAtMeaning": None,
        "updatedAt": None, "salary": None, "fieldSources": sources, "requestUrl": url,
        "observedAt": observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    employer = employer_for(board.key)
    row["companyDisplayName"] = employer["name"] if employer else board.slug
    row["companyDisplayNameSource"] = "curated-employer-catalog" if employer else "board-slug"
    sources["companyDisplayName"] = f"catalog:{board.key}" if employer else "input.boardSlug"
    if board.provider == "greenhouse":
        location = raw.get("location", {})
        if isinstance(location, dict) and text(location.get("name")):
            row["locations"] = [text(location["name"])]
            sources["locations"] = "location.name"
        departments = raw.get("departments", [])
        if isinstance(departments, list):
            row["department"] = "; ".join(dict.fromkeys(text(item.get("name")) for item in departments[:30] if isinstance(item, dict) and text(item.get("name"))))
            if row["department"]:
                sources["department"] = "departments[].name"
        desc = raw.get("content", "")
        sources["descriptionText"] = "content:HTML-to-text"
        row["updatedAt"] = _date(raw.get("updated_at"))
        if row["updatedAt"]:
            sources["updatedAt"] = "updated_at"
        row["publishedAt"] = _date(raw.get("first_published"))
        if row["publishedAt"]:
            sources["publishedAt"] = "first_published"
            row["publishedAtMeaning"] = "first-published"
        # List endpoint has no documented remote/employment/pay field. Do not
        # infer these from a location name or a salary-looking description.
    elif board.provider == "lever":
        categories = raw.get("categories")
        categories = categories if isinstance(categories, dict) else {}
        locations = categories.get("allLocations", [])
        locations = locations if isinstance(locations, list) else []
        row["locations"] = list(dict.fromkeys(text(item) for item in [categories.get("location"), *locations[:50]] if text(item)))[:50]
        sources["locations"] = "categories.location/categories.allLocations"
        for key, source in [("department", "department"), ("team", "team"), ("employmentType", "commitment")]:
            row[key] = text(categories.get(source))
            if row[key]:
                sources[key] = "categories." + source
        desc = raw.get("descriptionPlain") or raw.get("description", "")
        sources["descriptionText"] = "descriptionPlain" if raw.get("descriptionPlain") else "description:HTML-to-text"
        parts = [desc] if isinstance(desc, str) else []
        for item in raw.get("lists", [])[:30] if isinstance(raw.get("lists"), list) else []:
            if isinstance(item, dict):
                parts.extend([text(item.get("text")), item.get("content", "")])
        parts.append(raw.get("additionalPlain") or raw.get("additional", ""))
        desc = " ".join(part for part in parts if isinstance(part, str))
        if len(parts) > 1:
            sources["descriptionText"] += "/lists[]/additionalPlain-or-additional"
        salary = raw.get("salaryRange")
        if isinstance(salary, dict) and any(_number(salary.get(key)) is not None for key in ("min", "max")):
            row["salary"] = {"min": _number(salary.get("min")), "max": _number(salary.get("max")), "currency": text(salary.get("currency"), 10) or None, "interval": text(salary.get("interval"), 100) or None}
            sources["salary"] = "salaryRange"
        # Lever's public postings fields do not promise a publication date.
    else:
        row["locations"] = [text(raw.get("location"))] if text(raw.get("location")) else []
        for extra in raw.get("secondaryLocations", [])[:50] if isinstance(raw.get("secondaryLocations"), list) else []:
            if isinstance(extra, dict) and text(extra.get("location")) and text(extra["location"]) not in row["locations"]:
                row["locations"].append(text(extra["location"]))
        sources["locations"] = "location/secondaryLocations[].location"
        for key in ("department", "team", "employmentType"):
            row[key] = text(raw.get(key))
            if row[key]:
                sources[key] = key
        desc = raw.get("descriptionPlain") or raw.get("descriptionHtml", "")
        sources["descriptionText"] = "descriptionPlain" if raw.get("descriptionPlain") else "descriptionHtml:HTML-to-text"
        row["publishedAt"] = _date(raw.get("publishedAt"))
        if row["publishedAt"]:
            sources["publishedAt"] = "publishedAt"
            row["publishedAtMeaning"] = "last-published"
        compensation = raw.get("compensation")
        if isinstance(compensation, dict):
            components = compensation.get("summaryComponents", [])
            salaries = []
            for component in components[:30] if isinstance(components, list) else []:
                if isinstance(component, dict) and component.get("compensationType") == "Salary":
                    salaries.append({"min": _number(component.get("minValue")), "max": _number(component.get("maxValue")), "currency": text(component.get("currencyCode"), 10) or None, "interval": text(component.get("interval"), 100) or None})
            summary = text(compensation.get("scrapeableCompensationSalarySummary"), 1000)
            if salaries or summary:
                row["salary"] = {"ranges": salaries, "summary": summary or None}
                sources["salary"] = "compensation.summaryComponents[compensationType=Salary]/scrapeableCompensationSalarySummary"
    explicit_workplace = text(raw.get("workplaceType"), 30).lower().replace("-", "").replace(" ", "")
    if explicit_workplace in {"remote", "hybrid", "onsite"}:
        row["workplaceType"] = explicit_workplace
        row["workplaceTypeSource"] = "workplaceType"
    elif board.provider == "ashby" and raw.get("isRemote") is True:
        row["workplaceType"], row["workplaceTypeSource"] = "remote", "isRemote=true"
    if row["workplaceTypeSource"]:
        sources["workplaceType"] = row["workplaceTypeSource"]
    row["descriptionText"], row["descriptionTruncated"] = description(desc)
    row["employmentTypeNormalized"] = normalized_employment_type(row["employmentType"])
    if "employmentType" in sources:
        sources["employmentTypeNormalized"] = sources["employmentType"] + ":exact-label-map"
    if board.provider != "greenhouse":
        row["applyUrl"] = safe_public_link(raw.get("applyUrl"))
        if row["applyUrl"]:
            sources["applyUrl"] = "applyUrl"
    return row


def filter_reason(row: dict, config: RunConfig) -> str | None:
    title = row["title"].casefold()
    if not role_matches(row["title"], config.role_preset):
        return "role_preset_not_matched"
    if config.include_title_keywords and not any(word in title for word in config.include_title_keywords):
        return "title_not_included"
    if any(word in title for word in config.exclude_title_keywords):
        return "title_excluded"
    if config.location_keywords and not any(word in location.casefold() for word in config.location_keywords for location in row["locations"]):
        return "location_not_included"
    if config.remote_only and row["workplaceType"] != "remote":
        return "not_explicitly_remote"
    if config.employment_types and row.get("employmentTypeNormalized", "unknown") not in config.employment_types:
        return "employment_type_not_included"
    if config.published_after:
        parsed = iso_datetime(row.get("publishedAt"))
        if parsed is None:
            return "publication_date_unknown"
        if parsed < config.published_after:
            return "published_before_cutoff"
    return None
