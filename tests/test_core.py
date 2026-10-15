import csv
from dataclasses import replace
import io
import json
from pathlib import Path
import unittest

from hiringsignal.client import FeedError, validate_api_url
from hiringsignal.config import Board, RunConfig, parse_board
from hiringsignal.output import results_csv, rolling_known_ids
from hiringsignal.providers import MAX_DESCRIPTION, filter_reason, normalize_job, request_url
from hiringsignal.runner import scrape_boards


FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / (name + ".json")).read_text())


def normalized(provider, index=0):
    data = fixture(provider)
    raw = data[index] if provider == "lever" else data["jobs"][index]
    board = Board(provider, "Acme" if provider == "ashby" else "acme")
    return normalize_job(board, raw, request_url(board), "2026-10-15T00:00:00Z")


class ConfigurationTests(unittest.TestCase):
    def test_board_urls_and_case_retained(self):
        self.assertEqual(parse_board("https://jobs.ashbyhq.com/Acme/123"), Board("ashby", "Acme"))
        self.assertEqual(parse_board("https://jobs.eu.lever.co/acme"), Board("lever", "acme", "eu"))
        self.assertEqual(parse_board("https://boards.greenhouse.io/embed/job_board?for=acme"), Board("greenhouse", "acme"))
        self.assertEqual(parse_board("https://job-boards.greenhouse.io/acme/jobs/123"), Board("greenhouse", "acme"))
        config = RunConfig.from_dict({"boards": ["ashby:Acme", "https://jobs.ashbyhq.com/Acme"]})
        self.assertEqual(len(config.boards), 1)

    def test_untrusted_urls_and_invalid_inputs(self):
        invalid_boards = ["http://jobs.lever.co/acme", "https://api.lever.co/v0/postings/acme", "https://jobs.ashbyhq.com.evil.net/acme", "https://u:p@jobs.lever.co/acme", "https://127.0.0.1/", "ashby:../x", "greenhouse:a/b", "lever:bad?x=1"]
        for value in invalid_boards:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_board(value)
        for options in [{"maxJobs": True}, {"maxJobs": 1001}, {"maxJobsPerBoard": 0}, {"includeTitleKeywords": "python"}, {"remoteOnly": "false"}, {"publishedAfter": "yesterday"}, {"timeoutSeconds": 1}, {"knownJobIds": [None]}, {"maxJob": 1}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                RunConfig.from_dict({"boards": ["lever:acme"], **options})

    def test_api_host_allowlist_and_redirect_surface(self):
        self.assertIn("api.lever.co", validate_api_url(request_url(Board("lever", "acme"))))
        for value in ["https://127.0.0.1/v0/postings/acme", "http://api.lever.co/v0/postings/acme", "https://api.lever.co.evil.net/v0/postings/acme", "https://api.lever.co/other", "https://user@api.lever.co/v0/postings/acme"]:
            with self.subTest(url=value), self.assertRaises(FeedError):
                validate_api_url(value)


class MappingTests(unittest.TestCase):
    def test_greenhouse_updated_is_not_published_or_remote(self):
        row = normalized("greenhouse")
        self.assertIsNone(row["publishedAt"])
        self.assertEqual(row["updatedAt"], "2026-10-14T12:00:00Z")
        self.assertEqual(row["workplaceType"], "unknown")
        self.assertEqual(row["descriptionText"], "Build APIs & services.")
        self.assertEqual(row["company"], "acme")
        self.assertEqual(row["fieldSources"]["company"], "input.boardSlug")
        self.assertEqual(row["jobKey"], "greenhouse:acme:101")
        self.assertIsNone(row["salary"])

    def test_lever_fields_salary_and_no_undocumented_date(self):
        row = normalized("lever")
        self.assertEqual(row["locations"], ["Berlin", "Remote, Europe"])
        self.assertEqual(row["workplaceType"], "remote")
        self.assertEqual(row["employmentType"], "Full-time")
        self.assertIn("Requirements Python Apply today", row["descriptionText"])
        self.assertEqual(row["salary"]["min"], 90000)
        self.assertIsNone(normalized("lever", 1)["publishedAt"])
        self.assertIsNone(normalized("lever", 1)["applyUrl"])

    def test_ashby_last_published_case_id_and_explicit_workplace_priority(self):
        row = normalized("ashby")
        self.assertEqual(row["id"], "ashby-1")
        self.assertEqual(row["fieldSources"]["id"], "jobUrl:path[1]")
        self.assertEqual(row["workplaceType"], "hybrid")
        self.assertEqual(row["publishedAtMeaning"], "last-published")
        self.assertEqual(row["salary"]["ranges"][0]["currency"], "USD")
        self.assertEqual(row["company"], "Acme")
        self.assertIsNone(normalized("ashby", 1))

    def test_filters_unknown_dates_and_remote_are_explicit(self):
        base = RunConfig.from_dict({"boards": ["lever:acme"]})
        self.assertIsNone(filter_reason(normalized("lever"), replace(base, include_title_keywords=("python",), exclude_title_keywords=("junior",), location_keywords=("europe",), remote_only=True)))
        self.assertEqual(filter_reason(normalized("greenhouse"), replace(base, remote_only=True)), "not_explicitly_remote")
        dated = RunConfig.from_dict({"boards": ["ashby:Acme"], "publishedAfter": "2026-10-10"})
        self.assertIsNone(filter_reason(normalized("ashby"), dated))
        self.assertEqual(filter_reason(normalized("greenhouse"), dated), "publication_date_unknown")
        self.assertEqual(filter_reason(normalized("greenhouse", 1), dated), "published_before_cutoff")

    def test_malformed_fields_and_description_bound_nonmutation(self):
        raw = fixture("lever")[0]
        original = json.dumps(raw, sort_keys=True)
        self.assertIsNone(normalize_job(Board("lever", "acme"), {"id": True, "text": "Role", "hostedUrl": "https://jobs.lever.co/acme/a"}, "https://api.lever.co"))
        normalize_job(Board("lever", "acme"), raw, "https://api.lever.co")
        self.assertEqual(json.dumps(raw, sort_keys=True), original)
        raw["descriptionPlain"] = "x" * (MAX_DESCRIPTION + 100)
        row = normalize_job(Board("lever", "acme"), raw, "https://api.lever.co")
        self.assertEqual(len(row["descriptionText"]), MAX_DESCRIPTION)
        self.assertTrue(row["descriptionTruncated"])

    def test_csv_escaping_and_known_ids_union_only_saved(self):
        row = normalized("lever")
        row["title"] = "=MALICIOUS()"
        exported = list(csv.DictReader(io.StringIO(results_csv([row]))))[0]
        self.assertEqual(exported["title"], "'=MALICIOUS()")
        self.assertEqual(row["title"], "=MALICIOUS()")
        known, truncated = rolling_known_ids(["old:board:id", row["jobKey"]], [row])
        self.assertEqual(known, ["old:board:id", row["jobKey"]])
        self.assertFalse(truncated)


class FakeClient:
    responses = {}
    def __init__(self, config):
        self.requests = 0
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass
    async def fetch_json(self, url):
        self.requests += 1
        value = self.responses[url]
        if isinstance(value, Exception):
            raise value
        return value


class RunnerTests(unittest.IsolatedAsyncioTestCase):
    def config(self, **changes):
        return RunConfig.from_dict({"boards": ["greenhouse:acme", "lever:acme", "ashby:Acme"], "maxJobs": 100, "maxJobsPerBoard": 100, **changes})

    def setUp(self):
        FakeClient.responses = {request_url(Board("greenhouse", "acme")): fixture("greenhouse"), request_url(Board("lever", "acme")): fixture("lever"), request_url(Board("ashby", "Acme")): fixture("ashby")}

    async def test_caps_summary_saved_only_and_skipped_board_partial(self):
        report = await scrape_boards(self.config(maxJobs=2, maxJobsPerBoard=1), client_factory=FakeClient)
        self.assertEqual(len(report["results"]), 2)
        self.assertTrue(report["summary"]["partialResults"])
        self.assertEqual(report["summary"]["signals"]["jobsByBoard"], {"greenhouse:acme": 1, "lever:acme": 1})
        self.assertEqual(report["diagnostics"][2]["status"], "skipped")
        self.assertFalse(report["summary"]["closureInferenceSupported"])

    async def test_dedup_known_filters_and_empty_board_not_results(self):
        source = FakeClient.responses[request_url(Board("lever", "acme"))]
        source.append(source[0].copy())
        config = self.config(boards=["lever:acme"], knownJobIds=["lever:acme:lever-2"], includeTitleKeywords=["Python"])
        report = await scrape_boards(config, client_factory=FakeClient)
        self.assertEqual(len(report["results"]), 1)
        self.assertEqual(report["summary"]["duplicateJobs"], 1)
        self.assertEqual(report["summary"]["knownJobsSkipped"], 1)
        self.assertEqual(report["summary"]["savedJobs"], 1)
        FakeClient.responses[request_url(Board("lever", "acme"))] = []
        report = await scrape_boards(config, client_factory=FakeClient)
        self.assertEqual(report["results"], [])
        self.assertTrue(report["summary"]["coverageComplete"])

    async def test_callback_false_stops_before_recording_job(self):
        seen = []
        async def callback(row):
            if seen:
                return False
            seen.append(row)
            return True
        report = await scrape_boards(self.config(), callback, client_factory=FakeClient)
        self.assertEqual(report["results"], seen)
        self.assertEqual(report["summary"]["savedJobs"], 1)
        self.assertEqual(report["summary"]["requests"], 1)

    async def test_provider_failure_and_malformed_records_are_diagnostics(self):
        FakeClient.responses[request_url(Board("greenhouse", "acme"))] = FeedError("timeout", "Timed out")
        FakeClient.responses[request_url(Board("lever", "acme"))] = [None, {"id": "bad", "categories": []}]
        report = await scrape_boards(self.config(), client_factory=FakeClient)
        self.assertEqual(report["summary"]["failedBoards"], 1)
        self.assertGreaterEqual(report["summary"]["invalidJobs"], 2)
        self.assertEqual(report["summary"]["savedJobs"], 1)
        self.assertFalse(report["summary"]["coverageComplete"])

    async def test_lever_pagination_and_complete_feed(self):
        board = Board("lever", "acme")
        template = fixture("lever")[0]
        FakeClient.responses[request_url(board)] = [{**template, "id": str(i), "hostedUrl": f"https://jobs.lever.co/acme/{i}"} for i in range(100)]
        FakeClient.responses[request_url(board, 100)] = [{**template, "id": "100", "hostedUrl": "https://jobs.lever.co/acme/100"}]
        report = await scrape_boards(self.config(boards=["lever:acme"], maxJobs=200, maxJobsPerBoard=200), client_factory=FakeClient)
        self.assertEqual(len(report["results"]), 101)
        self.assertEqual(report["summary"]["requests"], 2)
        self.assertTrue(report["summary"]["coverageComplete"])

    async def test_unexpected_provider_shape_is_not_empty_success(self):
        FakeClient.responses[request_url(Board("greenhouse", "acme"))] = {"error": "not jobs"}
        report = await scrape_boards(self.config(boards=["greenhouse:acme"]), client_factory=FakeClient)
        self.assertEqual(report["results"], [])
        self.assertEqual(report["diagnostics"][0]["errorCode"], "unexpected_schema")
        self.assertFalse(report["summary"]["coverageComplete"])


if __name__ == "__main__":
    unittest.main()
