"""Strict input validation. No arbitrary API URLs are accepted."""

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import re
from typing import Any
from urllib.parse import parse_qs, urlsplit


@dataclass(frozen=True)
class Board:
    provider: str
    slug: str
    region: str = "global"

    @property
    def key(self) -> str:
        prefix = "lever-eu" if self.provider == "lever" and self.region == "eu" else self.provider
        return f"{prefix}:{self.slug}"


def parse_board(value: Any) -> Board:
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise ValueError("Each board must be provider:slug or a supported public board URL.")
    value = value.strip()
    provider, slug, region = "", "", "global"
    if "://" not in value:
        if ":" not in value:
            raise ValueError("Include a provider prefix, for example greenhouse:stripe.")
        provider, slug = value.split(":", 1)
        provider = provider.lower()
        if provider == "lever-eu":
            provider, region = "lever", "eu"
    else:
        try:
            parsed = urlsplit(value)
            if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
                raise ValueError("Only HTTPS public board URLs without credentials are accepted.")
            host = (parsed.hostname or "").lower()
            parts = [part for part in parsed.path.split("/") if part]
            if host in {"boards.greenhouse.io", "job-boards.greenhouse.io"}:
                provider = "greenhouse"
                if parts == ["embed", "job_board"]:
                    slug = parse_qs(parsed.query).get("for", [""])[0]
                else:
                    slug = parts[0] if parts else ""
            elif host in {"jobs.lever.co", "jobs.eu.lever.co"}:
                provider, slug = "lever", parts[0] if parts else ""
                region = "eu" if host == "jobs.eu.lever.co" else "global"
            elif host == "jobs.ashbyhq.com":
                provider, slug = "ashby", parts[0] if parts else ""
            else:
                raise ValueError("URL host must be a supported public Greenhouse, Lever or Ashby board.")
        except ValueError as exc:
            raise ValueError(f"Invalid board URL: {exc}") from None
    if provider not in {"greenhouse", "lever", "ashby"} or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", slug):
        raise ValueError("Use greenhouse:slug, lever:slug, lever-eu:slug or ashby:slug; slugs may contain letters, digits, _ and -.")
    # Ashby's board names may be case-sensitive; never lowercase a supplied slug.
    return Board(provider, slug, region)


def iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or len(value) > 100:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc)
    except ValueError:
        return None


def _int(value: Any, name: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} must be an integer between {low} and {high}.")
    return value


def _words(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > 30 or any(not isinstance(v, str) or not v.strip() or len(v) > 100 for v in value):
        raise ValueError(f"{name} must be a list of at most 30 non-empty strings, each at most 100 characters.")
    return tuple(dict.fromkeys(v.strip().casefold() for v in value))


@dataclass(frozen=True)
class RunConfig:
    boards: tuple[Board, ...]
    max_jobs: int = 20
    max_jobs_per_board: int = 8
    include_title_keywords: tuple[str, ...] = ()
    exclude_title_keywords: tuple[str, ...] = ()
    location_keywords: tuple[str, ...] = ()
    remote_only: bool = False
    published_after: datetime | None = None
    timeout_seconds: int = 20
    min_delay_seconds: float = 0.5
    known_job_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Any) -> "RunConfig":
        if not isinstance(data, dict):
            raise ValueError("Input must be a JSON object.")
        known = {"boards", "maxJobs", "maxJobsPerBoard", "includeTitleKeywords", "excludeTitleKeywords", "locationKeywords", "remoteOnly", "publishedAfter", "timeoutSeconds", "minDelaySeconds", "knownJobIds"}
        unknown = [str(key) for key in data if key not in known and not str(key).startswith("__")]
        if unknown:
            raise ValueError("Unknown input field(s): " + ", ".join(sorted(unknown)))
        values = data.get("boards")
        if not isinstance(values, list) or not 1 <= len(values) <= 30:
            raise ValueError("boards must contain between 1 and 30 public employer boards.")
        boards = tuple(dict.fromkeys(parse_board(value) for value in values))
        remote = data.get("remoteOnly", False)
        if not isinstance(remote, bool):
            raise ValueError("remoteOnly must be true or false.")
        after_raw = data.get("publishedAfter")
        after = iso_datetime(after_raw) if after_raw not in (None, "") else None
        if after_raw not in (None, "") and after is None:
            raise ValueError("publishedAfter must be an ISO 8601 date or timestamp.")
        delay = data.get("minDelaySeconds", 0.5)
        if isinstance(delay, bool) or not isinstance(delay, (int, float)) or not math.isfinite(delay) or not 0.25 <= delay <= 10:
            raise ValueError("minDelaySeconds must be between 0.25 and 10.")
        prior = data.get("knownJobIds", [])
        if not isinstance(prior, list) or len(prior) > 10000 or any(not isinstance(item, str) or not item.strip() or len(item) > 400 for item in prior):
            raise ValueError("knownJobIds must be at most 10,000 stable jobKey strings, each at most 400 characters.")
        return cls(boards=boards,
            max_jobs=_int(data.get("maxJobs", 20), "maxJobs", 1, 1000),
            max_jobs_per_board=_int(data.get("maxJobsPerBoard", 8), "maxJobsPerBoard", 1, 1000),
            include_title_keywords=_words(data.get("includeTitleKeywords", []), "includeTitleKeywords"),
            exclude_title_keywords=_words(data.get("excludeTitleKeywords", []), "excludeTitleKeywords"),
            location_keywords=_words(data.get("locationKeywords", []), "locationKeywords"), remote_only=remote,
            published_after=after, timeout_seconds=_int(data.get("timeoutSeconds", 20), "timeoutSeconds", 5, 45),
            min_delay_seconds=float(delay), known_job_ids=tuple(dict.fromkeys(item.strip() for item in prior)))
