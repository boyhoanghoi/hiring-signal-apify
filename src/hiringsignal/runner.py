"""Filter before storing; report feed coverage separately from saved-job counts."""

from collections import Counter
from datetime import datetime, timezone
import time
from typing import Awaitable, Callable

from .client import FeedClient, FeedError
from .config import RunConfig
from .providers import filter_reason, normalize_job, request_url
from .catalog import search_context


MAX_PAGES_PER_BOARD = 20
MAX_FETCHED_PER_BOARD = 5000


def saved_signals(rows: list[dict]) -> dict:
    return {
        "scope": "saved-results-only",
        "jobsByBoard": dict(Counter(row["boardKey"] for row in rows)),
        "jobsBySource": dict(Counter(row["source"] for row in rows)),
        "jobsByDepartment": dict(Counter(row["department"] or "unknown" for row in rows)),
        "jobsByWorkplaceType": dict(Counter(row["workplaceType"] for row in rows)),
        "jobsByEmploymentType": dict(Counter(row.get("employmentTypeNormalized", "unknown") for row in rows)),
        "jobsWithPublishedDate": sum(row["publishedAt"] is not None for row in rows),
        "jobsWithSalary": sum(row["salary"] is not None for row in rows),
    }


def source_failure_is_fatal(report: dict) -> bool:
    """Empty successful feeds/filters are valid; no usable source is a failure."""
    summary = report["summary"]
    return not report["results"] and summary.get("failedBoards", 0) > 0 and summary.get("successfulBoards", 0) == 0


async def scrape_boards(config: RunConfig, on_result: Callable[[dict], Awaitable[bool]] | None = None, *, client_factory=FeedClient) -> dict:
    started = time.monotonic()
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    rows, boards, seen = [], [], set()
    known = set(config.known_job_ids)
    stop_all = False
    async with client_factory(config) as client:
        for board in config.boards:
            state = {"board": board.key, "status": "skipped" if stop_all else "success", "feedComplete": False,
                "coverageComplete": False, "fetchedJobs": 0, "normalizedJobs": 0, "invalidJobs": 0,
                "filteredJobs": 0, "duplicateJobs": 0, "knownJobsSkipped": 0, "savedJobs": 0, "requests": 0,
                "stopReason": "global_or_spending_limit" if stop_all else None, "filterReasons": {}}
            boards.append(state)
            if stop_all:
                continue
            before_requests = client.requests
            offset = 0
            try:
                for page_number in range(MAX_PAGES_PER_BOARD):
                    url = request_url(board, offset)
                    payload = await client.fetch_json(url)
                    jobs = payload if board.provider == "lever" else payload.get("jobs") if isinstance(payload, dict) else None
                    if not isinstance(jobs, list):
                        raise FeedError("unexpected_schema", "Expected the provider's public jobs array.")
                    if board.provider == "greenhouse":
                        total = payload.get("meta", {}).get("total") if isinstance(payload.get("meta"), dict) else None
                        terminal = not isinstance(total, int) or total <= len(jobs)
                    else:
                        terminal = board.provider != "lever" or len(jobs) < 100
                    state["fetchedJobs"] += len(jobs)
                    remaining = max(0, MAX_FETCHED_PER_BOARD - (state["fetchedJobs"] - len(jobs)))
                    bounded_jobs = jobs[:remaining]
                    hard_cap = len(jobs) > len(bounded_jobs)
                    stop_board = False
                    for index, raw in enumerate(bounded_jobs):
                        if isinstance(raw, dict) and raw.get("isListed") is False:
                            state["filteredJobs"] += 1
                            state["filterReasons"]["unlisted"] = state["filterReasons"].get("unlisted", 0) + 1
                            continue
                        try:
                            row = normalize_job(board, raw, url, observed_at)
                        except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
                            row = None
                        if row is None:
                            state["invalidJobs"] += 1
                            continue
                        state["normalizedJobs"] += 1
                        if row["jobKey"] in known:
                            state["knownJobsSkipped"] += 1
                            continue
                        key = (board.key, row["id"])
                        if key in seen:
                            state["duplicateJobs"] += 1
                            continue
                        seen.add(key)
                        reason = filter_reason(row, config)
                        if reason:
                            state["filteredJobs"] += 1
                            state["filterReasons"][reason] = state["filterReasons"].get(reason, 0) + 1
                            continue
                        if on_result is not None and not await on_result(row):
                            stop_all = stop_board = True
                            state["stopReason"] = "spending_or_result_callback_limit"
                            break
                        rows.append(row)
                        state["savedJobs"] += 1
                        more = index < len(bounded_jobs) - 1 or not terminal or hard_cap
                        if len(rows) >= config.max_jobs:
                            stop_all = stop_board = True
                            state["stopReason"] = "global_job_limit" if more else None
                            state["feedComplete"] = not more
                            break
                        if state["savedJobs"] >= config.max_jobs_per_board:
                            stop_board = True
                            state["stopReason"] = "per_board_job_limit" if more else None
                            state["feedComplete"] = not more
                            break
                    if stop_board:
                        break
                    if hard_cap or state["fetchedJobs"] >= MAX_FETCHED_PER_BOARD and not terminal:
                        state["stopReason"] = "hard_record_limit"
                        break
                    if terminal:
                        state["feedComplete"] = True
                        break
                    if board.provider != "lever":
                        state["stopReason"] = "provider_total_exceeds_returned_records"
                        break
                    offset += len(jobs)
                else:
                    state["stopReason"] = "hard_page_limit"
            except FeedError as exc:
                state.update({"status": "failed", "error": str(exc), "errorCode": exc.status, "httpStatus": exc.http_status,
                              "stopReason": "provider_error"})
                if exc.status == "request_limit":
                    stop_all = True
            if state["status"] == "success" and state["invalidJobs"] > 0 and state["normalizedJobs"] == 0:
                state.update({"status": "failed", "error": "No returned listed job could be normalized. Source schema may have changed.",
                    "errorCode": "all_records_invalid", "stopReason": "provider_schema_error", "feedComplete": False})
            state["requests"] = client.requests - before_requests
            state["coverageComplete"] = state["feedComplete"] and state["invalidJobs"] == 0 and state["status"] == "success"
        request_count = client.requests
    complete = all(board["coverageComplete"] for board in boards)
    return {"results": rows, "diagnostics": boards, "summary": {
        "search": search_context(config),
        "inputBoards": len(config.boards), "successfulBoards": sum(board["status"] == "success" for board in boards),
        "failedBoards": sum(board["status"] == "failed" for board in boards),
        "skippedBoards": sum(board["status"] == "skipped" for board in boards),
        "fetchedJobs": sum(board["fetchedJobs"] for board in boards), "savedJobs": len(rows),
        "filteredJobs": sum(board["filteredJobs"] for board in boards),
        "invalidJobs": sum(board["invalidJobs"] for board in boards),
        "duplicateJobs": sum(board["duplicateJobs"] for board in boards),
        "knownJobsSkipped": sum(board["knownJobsSkipped"] for board in boards),
        "coverageComplete": complete, "partialResults": not complete,
        "countsScope": "saved-results-only", "closureInferenceSupported": False,
        "requests": request_count, "durationSeconds": round(time.monotonic() - started, 3),
        "signals": saved_signals(rows), "observedAt": observed_at}}
