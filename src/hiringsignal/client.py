"""Bounded HTTPS JSON GET transport restricted to official public ATS APIs."""

import asyncio
import json
import time
from urllib.parse import urlsplit

import aiohttp

from .providers import API_HOSTS


MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_REQUESTS = 80


class FeedError(Exception):
    def __init__(self, status: str, message: str, http_status: int | None = None):
        super().__init__(message)
        self.status = status
        self.http_status = http_status


def validate_api_url(url: str) -> str:
    try:
        parsed = urlsplit(url)
        allowed_path = {
            "boards-api.greenhouse.io": "/v1/boards/",
            "api.lever.co": "/v0/postings/",
            "api.eu.lever.co": "/v0/postings/",
            "api.ashbyhq.com": "/posting-api/job-board/",
        }
        if parsed.scheme != "https" or parsed.hostname not in API_HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError()
        if not parsed.path.startswith(allowed_path[parsed.hostname]) or parsed.fragment:
            raise ValueError()
    except (ValueError, TypeError):
        raise FeedError("unsafe_url", "Only generated official ATS API endpoints may be requested.") from None
    return url


class FeedClient:
    def __init__(self, config):
        self.config = config
        self.requests = 0
        self.last_request: dict[str, float] = {}
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            headers={"User-Agent": "HiringSignal/0.1 (public ATS job feed reader)", "Accept": "application/json"},
            connector=aiohttp.TCPConnector(limit=3), trust_env=False,
        )
        return self

    async def __aexit__(self, *args):
        await self.session.close()

    async def fetch_json(self, url: str):
        validate_api_url(url)
        host = urlsplit(url).hostname
        for attempt in range(2):
            if self.requests >= MAX_REQUESTS:
                raise FeedError("request_limit", "Run reached the hard limit of 80 HTTP attempts.")
            wait = self.config.min_delay_seconds - (time.monotonic() - self.last_request.get(host, 0))
            if wait > 0:
                await asyncio.sleep(wait)
            self.last_request[host] = time.monotonic()
            self.requests += 1
            retry_wait = 0.0
            try:
                async with self.session.get(url, allow_redirects=False) as response:
                    status = response.status
                    if 300 <= status < 400:
                        raise FeedError("redirect_rejected", "The API redirected; redirects are never followed.", status)
                    if status == 429 or status in {500, 502, 503, 504}:
                        retry_after = response.headers.get("Retry-After", "1")
                        try:
                            retry_wait = max(1, float(retry_after))
                        except ValueError:
                            retry_wait = 2
                        if attempt or retry_wait > 15:
                            raise FeedError("rate_limited" if status == 429 else "provider_unavailable", "Provider requested a retry or is temporarily unavailable; retry bound reached.", status)
                    elif status >= 400:
                        raise FeedError("board_not_found" if status == 404 else "http_error", f"Provider returned HTTP {status}.", status)
                    else:
                        chunks, size = [], 0
                        async for chunk in response.content.iter_chunked(65536):
                            size += len(chunk)
                            if size > MAX_RESPONSE_BYTES:
                                raise FeedError("response_too_large", "Provider JSON exceeds the 8 MiB decoded response limit.")
                            chunks.append(chunk)
                        try:
                            return json.loads(b"".join(chunks))
                        except (ValueError, UnicodeError, RecursionError):
                            raise FeedError("invalid_json", "Provider did not return valid bounded JSON.") from None
            except asyncio.TimeoutError:
                if attempt:
                    raise FeedError("timeout", "Provider request timed out twice.") from None
                retry_wait = 1
            except (aiohttp.ClientError, OSError) as exc:
                if attempt:
                    raise FeedError("network_error", f"Provider connection failed ({type(exc).__name__}).") from None
                retry_wait = 1
            await asyncio.sleep(retry_wait)
        raise FeedError("provider_unavailable", "Provider retry limit reached.")
