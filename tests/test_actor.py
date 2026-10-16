import sys
import json
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from hiringsignal.actor import BILLABLE_EVENT, run_actor


class FakeManager:
    def __init__(self, remaining=2, ppe=True):
        self.remaining, self.ppe, self.count = remaining, ppe, 0
    def get_pricing_info(self):
        return SimpleNamespace(is_pay_per_event=self.ppe, per_event_prices={BILLABLE_EVENT: 0.0015})
    def compute_push_data_limit(self, count, event, *, is_default_dataset):
        return min(count, self.remaining)
    def get_charged_event_count(self, event):
        return self.count


class FakeActor:
    def __init__(self, manager):
        self.manager = manager
        self.input = {"boards": ["lever:acme"], "knownJobIds": ["lever:acme:old"]}
        self.dataset, self.writes, self.events = [], {}, []
        self.configuration = SimpleNamespace(is_at_home=False)
        self.log = SimpleNamespace(error=lambda value: None)
        self.exit_code, self.status_message = 0, ""
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass
    async def get_input(self):
        return self.input
    def get_charging_manager(self):
        return self.manager
    async def set_value(self, key, value, **kwargs):
        self.writes[key] = value
    async def push_data(self, row, charged_event_name=None):
        if charged_event_name and self.manager.remaining < 1:
            return SimpleNamespace(charged_count=0, event_charge_limit_reached=True)
        self.dataset.append(row)
        self.events.append(charged_event_name)
        if charged_event_name:
            self.manager.count += 1
            self.manager.remaining -= 1
        return SimpleNamespace(charged_count=1 if charged_event_name else 0, event_charge_limit_reached=self.manager.remaining == 0)


async def fake_scrape(config, callback):
    saved = []
    for index in range(min(3, config.max_jobs)):
        row = {"id": str(index), "jobKey": f"lever:acme:{index}", "boardKey": "lever:acme", "source": "lever",
               "title": "Engineer", "department": "Engineering", "workplaceType": "remote", "publishedAt": None, "salary": None}
        if not await callback(row):
            break
        saved.append(row)
    return {"results": saved, "diagnostics": [{"board": "lever:bad", "status": "failed"}], "summary": {"savedJobs": len(saved)}}


class BillingTests(unittest.IsolatedAsyncioTestCase):
    async def run_fake(self, actor, scrape=fake_scrape):
        with patch.dict(sys.modules, {"apify": SimpleNamespace(Actor=actor)}), patch("hiringsignal.actor.scrape_boards", new=scrape):
            await run_actor()

    async def test_last_affordable_job_is_saved_and_only_saved_ids_marked_seen(self):
        actor = FakeActor(FakeManager(remaining=1))
        await self.run_fake(actor)
        self.assertEqual(len(actor.dataset), 1)
        self.assertEqual(actor.writes["RESULTS"], actor.dataset)
        self.assertEqual(actor.writes["KNOWN_JOB_IDS"], ["lever:acme:old", "lever:acme:0"])
        self.assertEqual(actor.writes["SUMMARY"]["chargedJobs"], 1)
        self.assertTrue(actor.writes["SUMMARY"]["budgetLimitReached"])
        self.assertEqual(actor.events, [BILLABLE_EVENT])
        self.assertIn("1 saved matching jobs", actor.writes["newsletter.md"])
        self.assertEqual([item["id"] for item in json.loads(actor.writes["jobs.feed.json"])["items"]], [actor.dataset[0]["jobKey"]])
        self.assertEqual(len(actor.writes["EMPLOYER_CATALOG"]["employers"]), 14)

    async def test_zero_budget_does_not_fetch_or_charge(self):
        actor = FakeActor(FakeManager(remaining=0))
        scrape = AsyncMock()
        await self.run_fake(actor, scrape)
        scrape.assert_not_awaited()
        self.assertEqual(actor.events, [])
        self.assertEqual(actor.writes["KNOWN_JOB_IDS"], ["lever:acme:old"])
        self.assertEqual(actor.writes["RESULTS"], [])
        self.assertIn("0 saved matching jobs", actor.writes["newsletter.md"])
        self.assertEqual(json.loads(actor.writes["jobs.feed.json"])["items"], [])
        self.assertFalse(actor.writes["SUMMARY"]["sourceFailureFatal"])

    async def test_non_ppe_has_no_explicit_billing(self):
        actor = FakeActor(FakeManager(ppe=False))
        await self.run_fake(actor)
        self.assertEqual(actor.events, [None, None, None])
        self.assertEqual(actor.writes["SUMMARY"]["chargedJobs"], 0)

    async def test_invalid_input_and_missing_cloud_event_fail_without_work(self):
        for invalid in ("input", "billing"):
            actor = FakeActor(FakeManager())
            if invalid == "input":
                actor.input = {"boards": ["http://127.0.0.1/"]}
            else:
                actor.configuration.is_at_home = True
                actor.manager.get_pricing_info = lambda: SimpleNamespace(is_pay_per_event=True, per_event_prices={})
            scrape = AsyncMock()
            await self.run_fake(actor, scrape)
            scrape.assert_not_awaited()
            self.assertEqual(actor.exit_code, 1)
            self.assertEqual(actor.events, [])

    async def test_all_failed_sources_preserve_diagnostics_and_known_ids_but_fail_the_run(self):
        actor = FakeActor(FakeManager())
        async def failed(config, callback):
            return {"results": [], "diagnostics": [{"board": "lever:acme", "status": "failed", "errorCode": "timeout"}],
                    "summary": {"savedJobs": 0, "failedBoards": 1, "successfulBoards": 0}}
        await self.run_fake(actor, failed)
        self.assertEqual(actor.exit_code, 1)
        self.assertEqual(actor.events, [])
        self.assertTrue(actor.writes["SUMMARY"]["sourceFailureFatal"])
        self.assertEqual(actor.writes["KNOWN_JOB_IDS"], ["lever:acme:old"])
        self.assertEqual(actor.writes["DIAGNOSTICS"][0]["errorCode"], "timeout")
        self.assertEqual(json.loads(actor.writes["jobs.feed.json"])["items"], [])

    async def test_empty_successful_source_does_not_fail_when_another_source_is_unavailable(self):
        actor = FakeActor(FakeManager())
        async def empty(config, callback):
            return {"results": [], "diagnostics": [], "summary": {"failedBoards": 1, "successfulBoards": 1}}
        await self.run_fake(actor, empty)
        self.assertEqual(actor.exit_code, 0)
        self.assertFalse(actor.writes["SUMMARY"]["sourceFailureFatal"])


if __name__ == "__main__":
    unittest.main()
