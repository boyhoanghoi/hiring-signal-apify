"""Apify billing occurs only when a normalized, filtered job is persisted."""

import asyncio
from dataclasses import replace

from .config import RunConfig
from .output import results_csv, rolling_known_ids
from .runner import scrape_boards, saved_signals


BILLABLE_EVENT = "job-saved"


async def run_actor() -> None:
    from apify import Actor

    async with Actor:
        try:
            config = RunConfig.from_dict(await Actor.get_input() or {})
        except ValueError as exc:
            message = f"Invalid input: {exc}"
            Actor.log.error(message)
            await Actor.set_value("OUTPUT", {"error": message, "results": []})
            Actor.exit_code, Actor.status_message = 1, message
            return
        manager = Actor.get_charging_manager()
        pricing = manager.get_pricing_info()
        ppe = pricing.is_pay_per_event
        if ppe and Actor.configuration.is_at_home and BILLABLE_EVENT not in pricing.per_event_prices:
            message = f"Missing pay-per-event configuration for {BILLABLE_EVENT}."
            Actor.log.error(message)
            await Actor.set_value("OUTPUT", {"error": message, "results": []})
            Actor.exit_code, Actor.status_message = 1, message
            return
        saved = []
        budget_reached = False
        if ppe:
            available = manager.compute_push_data_limit(config.max_jobs, BILLABLE_EVENT, is_default_dataset=True)
            budget_reached = available == 0
            if available:
                config = replace(config, max_jobs=min(config.max_jobs, available))

        async def save(row: dict) -> bool:
            nonlocal budget_reached
            if ppe and manager.compute_push_data_limit(1, BILLABLE_EVENT, is_default_dataset=True) < 1:
                budget_reached = True
                return False
            if ppe:
                charge = await Actor.push_data(row, charged_event_name=BILLABLE_EVENT)
                if charge.charged_count:
                    saved.append(row)
                budget_reached = charge.event_charge_limit_reached or charge.charged_count == 0
                return charge.charged_count > 0
            await Actor.push_data(row)
            saved.append(row)
            return True

        if budget_reached:
            report = {"results": [], "diagnostics": [{"board": board.key, "status": "skipped", "feedComplete": False, "coverageComplete": False, "stopReason": "spending_limit"} for board in config.boards],
                "summary": {"inputBoards": len(config.boards), "savedJobs": 0, "requests": 0, "coverageComplete": False, "partialResults": True}}
        else:
            report = await scrape_boards(config, save)
        report["results"] = saved
        known, known_truncated = rolling_known_ids(config.known_job_ids, saved)
        report["knownJobIds"] = known
        summary = report["summary"]
        summary.update({"savedJobs": len(saved), "signals": saved_signals(saved), "countsScope": "saved-results-only",
            "budgetLimitReached": budget_reached, "billingEvent": BILLABLE_EVENT if ppe else None,
            "chargedJobs": manager.get_charged_event_count(BILLABLE_EVENT) if ppe else 0,
            "knownJobIdsTruncated": known_truncated, "closureInferenceSupported": False})
        await Actor.set_value("RESULTS", saved)
        await Actor.set_value("SUMMARY", summary)
        await Actor.set_value("DIAGNOSTICS", report["diagnostics"])
        await Actor.set_value("KNOWN_JOB_IDS", known)
        await Actor.set_value("results.csv", results_csv(saved), content_type="text/csv; charset=utf-8")
        await Actor.set_value("OUTPUT", report)
        Actor.status_message = f"Saved {len(saved)} matching jobs. " + ("Spending limit reached." if budget_reached else "See diagnostics for board coverage.")


def main():
    asyncio.run(run_actor())


if __name__ == "__main__":
    main()
