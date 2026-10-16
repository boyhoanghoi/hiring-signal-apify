import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hiringsignal.catalog import EMPLOYERS, catalog_document, group_boards, role_matches
from hiringsignal.cli import main
from hiringsignal.config import Board, RunConfig, parse_board
from hiringsignal.output import export_results, newsletter_markdown, results_csv
from hiringsignal.providers import filter_reason, normalize_job, request_url
from hiringsignal.runner import scrape_boards


class FinderConfigTests(unittest.TestCase):
    def test_group_only_custom_union_and_backwards_compatibility(self):
        ai = RunConfig.from_dict({"companyGroup": "ai", "rolePreset": "data-ai"})
        self.assertEqual([board.key for board in ai.boards], list(group_boards("ai")))
        self.assertEqual(len(ai.boards), 4)
        union = RunConfig.from_dict({"boards": ["ashby:cursor", "https://jobs.ashbyhq.com/PostHog"], "companyGroup": "ai"})
        self.assertEqual(union.boards[:2], (Board("ashby", "cursor"), Board("ashby", "PostHog")))
        self.assertEqual(len(union.boards), 5)
        old = RunConfig.from_dict({"boards": ["lever:acme"]})
        self.assertEqual(old.company_group, "none")
        self.assertEqual(old.role_preset, "all")
        self.assertEqual(old.boards, (Board("lever", "acme"),))

    def test_invalid_or_oversized_combined_selection_fails_before_fetch(self):
        for data in ({}, {"boards": []}, {"companyGroup": "unknown"}, {"companyGroup": []},
                     {"companyGroup": "ai", "rolePreset": {}}, {"companyGroup": "ai", "rolePreset": "python"},
                     {"companyGroup": "all", "boards": [f"lever:custom{i}" for i in range(17)]}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                RunConfig.from_dict(data)

    def test_catalog_references_valid_boards_and_unique_entries(self):
        keys = [item["board"] for item in EMPLOYERS]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(keys), 14)
        for item in EMPLOYERS:
            self.assertEqual(parse_board(item["board"]), parse_board(item["publicBoardUrl"]))
            self.assertTrue(item["verifiedAt"])
        config = RunConfig.from_dict({"companyGroup": "all"})
        self.assertEqual(len(config.boards), len(keys))
        self.assertIn("ashby:PostHog", group_boards("developer-tools"))
        json.dumps(catalog_document(), allow_nan=False)

    def test_role_terms_use_word_boundaries_and_manual_filters_are_anded(self):
        for title in ("Data Engineer", "AI Engineer", "Machine Learning Scientist", "ML Infrastructure", "Analytics Lead"):
            self.assertTrue(role_matches(title, "data-ai"), title)
        for title in ("Paid Marketing", "Retail Sales", "Email Operations", "Chairperson"):
            self.assertFalse(role_matches(title, "data-ai"), title)
        self.assertTrue(role_matches("Machine   Learning Engineer", "data-ai"))
        self.assertFalse(role_matches("Engineering", "product-design"))
        self.assertTrue(role_matches("Senior Product Manager", "product-design"))
        self.assertTrue(role_matches("Account Executive", "sales-marketing"))
        config = RunConfig.from_dict({"companyGroup": "ai", "rolePreset": "data-ai", "includeTitleKeywords": ["engineer"], "locationKeywords": ["london"]})
        row = {"title": "AI Engineer", "locations": ["London"], "workplaceType": "unknown"}
        self.assertIsNone(filter_reason(row, config))
        self.assertEqual(filter_reason({**row, "title": "Data Analyst"}, config), "title_not_included")
        self.assertEqual(filter_reason({**row, "title": "Backend Engineer"}, config), "role_preset_not_matched")
        self.assertEqual(filter_reason({**row, "locations": ["New York"]}, config), "location_not_included")

    def test_curated_display_names_preserve_stable_identity_and_source(self):
        raw = {"id": "123", "title": "Data Engineer", "jobUrl": "https://jobs.ashbyhq.com/elevenlabs/123"}
        row = normalize_job(Board("ashby", "elevenlabs"), raw, "https://api.ashbyhq.com")
        self.assertEqual(row["company"], "elevenlabs")
        self.assertEqual(row["companyDisplayName"], "ElevenLabs")
        self.assertEqual(row["companyDisplayNameSource"], "curated-employer-catalog")
        self.assertEqual(row["jobKey"], "ashby:elevenlabs:123")
        self.assertEqual(row["fieldSources"]["companyDisplayName"], "catalog:ashby:elevenlabs")
        custom = normalize_job(Board("ashby", "other"), raw, "https://api.ashbyhq.com")
        self.assertEqual(custom["companyDisplayName"], "other")
        self.assertEqual(custom["companyDisplayNameSource"], "board-slug")
        self.assertEqual(list(csv.DictReader(io.StringIO(results_csv([row]))))[0]["companyDisplayName"], "ElevenLabs")


class DigestTests(unittest.TestCase):
    def test_markdown_escapes_titles_and_urls_and_never_emits_unsafe_scheme(self):
        row = {"title": "[Job](javascript:evil) <img>", "companyDisplayName": "**Company**", "locations": ["<b>Remote</b>"],
               "workplaceType": "unknown", "jobUrl": "https://example.org/job(a)?x=1&z=2", "applyUrl": None}
        digest = newsletter_markdown([row], {"partialResults": True})
        self.assertIn("%28a%29", digest)
        self.assertIn(r"\[Job\]", digest)
        self.assertNotIn("<img>", digest)
        self.assertNotIn("**Company**", digest)
        self.assertIn("Coverage is partial", digest)
        malicious = newsletter_markdown([{**row, "jobUrl": "javascript:alert(1)"}], {})
        self.assertNotIn("](javascript:", malicious)

    def test_empty_export_has_no_invented_jobs(self):
        report = {"results": [], "summary": {"savedJobs": 0}, "diagnostics": [], "knownJobIds": []}
        with tempfile.TemporaryDirectory() as directory:
            export_results(report, directory)
            digest = (Path(directory) / "newsletter.md").read_text(encoding="utf-8")
            self.assertIn("0 saved matching jobs", digest)
            self.assertIn("No matching jobs were saved", digest)
            self.assertNotIn("- [", digest)


class FinderIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_role_and_known_filters_run_before_result_callback_and_digest(self):
        board = Board("ashby", "cursor")
        def job(identity, title):
            return {"id": identity, "title": title, "jobUrl": f"https://jobs.ashbyhq.com/cursor/{identity}", "location": "London"}
        class Client:
            requests = 0
            def __init__(self, config):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def fetch_json(self, url):
                self.requests += 1
                return {"jobs": [job("old", "AI Engineer"), job("irrelevant", "Paid Marketing"), job("new", "Data Engineer")]}
        config = RunConfig.from_dict({"boards": [board.key], "rolePreset": "data-ai", "knownJobIds": ["ashby:cursor:old"]})
        accepted = []
        async def save(row):
            accepted.append(row)
            return True
        report = await scrape_boards(config, save, client_factory=Client)
        self.assertEqual([row["id"] for row in accepted], ["new"])
        self.assertEqual(report["summary"]["knownJobsSkipped"], 1)
        self.assertEqual(report["summary"]["filteredJobs"], 1)
        self.assertEqual(report["summary"]["search"]["rolePreset"], "data-ai")
        digest = newsletter_markdown(report["results"], report["summary"])
        self.assertIn("/new", digest)
        self.assertNotIn("/old", digest)
        self.assertNotIn("Paid Marketing", digest)


class FinderCliTests(unittest.TestCase):
    def test_previous_ids_are_merged_before_fetch_and_only_saved_ids_advance(self):
        seen = []
        async def scrape(config):
            seen.extend(config.known_job_ids)
            return {"results": [], "diagnostics": [], "summary": {"failedBoards": 0, "savedJobs": 0}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input.json").write_text(json.dumps({"companyGroup": "ai", "knownJobIds": ["input-key"]}))
            (root / "previous.json").write_text(json.dumps(["prior-key", "input-key"]))
            with patch("sys.argv", ["hiringsignal", "run", "--input", str(root / "input.json"), "--previous-ids", str(root / "previous.json"), "--output", str(root / "out")]), patch("hiringsignal.cli.scrape_boards", new=scrape), patch("builtins.print"):
                self.assertEqual(main(), 0)
            self.assertEqual(seen, ["input-key", "prior-key"])
            self.assertEqual(json.loads((root / "out" / "known_job_ids.json").read_text()), seen)

    def test_invalid_previous_ids_never_start_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input.json").write_text(json.dumps({"companyGroup": "ai"}))
            (root / "previous.json").write_text(json.dumps({"not": "an array"}))
            with patch("sys.argv", ["hiringsignal", "run", "--input", str(root / "input.json"), "--previous-ids", str(root / "previous.json")]), patch("hiringsignal.cli.scrape_boards") as scrape, patch("sys.stderr", new=io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    main()
            self.assertEqual(raised.exception.code, 2)
            scrape.assert_not_called()
