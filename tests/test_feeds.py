import json
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree as ET

from hiringsignal.config import Board, RunConfig
from hiringsignal.feeds import MAX_FEED_DESCRIPTION, json_feed, rss_feed
from hiringsignal.output import export_results
from hiringsignal.providers import filter_reason, normalize_job, normalized_employment_type, request_url
from hiringsignal.runner import scrape_boards, source_failure_is_fatal


def job(**changes):
    return {"jobKey": "lever:acme:123", "title": "Data Engineer", "jobUrl": "https://jobs.lever.co/acme/123?a=1&b=2",
            "applyUrl": "https://jobs.lever.co/acme/123/apply", "company": "acme", "locations": ["London"],
            "workplaceType": "remote", "employmentType": "Full-time", "employmentTypeNormalized": "full-time",
            "publishedAt": None, "updatedAt": "2026-10-15T11:00:00Z", "observedAt": "2026-10-16T12:00:00Z",
            "descriptionText": "Build APIs", "descriptionTruncated": False, **changes}


class FeedExportTests(unittest.TestCase):
    def test_stable_ids_source_dates_and_observation_are_kept_distinct(self):
        row = job()
        feed = json_feed([row], {"observedAt": row["observedAt"], "partialResults": True})
        item = feed["items"][0]
        self.assertEqual(item["id"], row["jobKey"])
        self.assertNotIn("date_published", item)
        self.assertEqual(item["date_modified"], row["updatedAt"])
        self.assertTrue(feed["_hiringsignal"]["partialResults"])
        self.assertEqual(feed["version"], "https://jsonfeed.org/version/1.1")
        channel = ET.fromstring(rss_feed([row], {"observedAt": row["observedAt"]})).find("channel")
        self.assertIsNone(channel.find("item/pubDate"))
        self.assertEqual(channel.find("item/guid").text, row["jobKey"])
        self.assertEqual(channel.find("item/guid").attrib, {"isPermaLink": "false"})
        self.assertIn("16 Oct 2026", channel.find("lastBuildDate").text)

    def test_ashby_last_published_is_labeled_and_invalid_dates_never_exported(self):
        row = job(publishedAt="2026-10-10T10:00:00+02:00", publishedAtMeaning="last-published", updatedAt="invalid")
        item = json_feed([row], {})["items"][0]
        self.assertEqual(item["date_published"], "2026-10-10T08:00:00Z")
        self.assertNotIn("date_modified", item)
        self.assertIn("Source publication (last-published)", item["content_text"])
        root = ET.fromstring(rss_feed([row], {}))
        self.assertEqual(root.find("channel/item/pubDate").text, "Sat, 10 Oct 2026 08:00:00 GMT")

    def test_xml_controls_unsafe_links_and_source_markup_cannot_become_html(self):
        row = job(title="Role \x00\ud800 & <b>bold</b> 😀", jobUrl="javascript:alert(1)", applyUrl="data:text/html,x",
                  descriptionText='<script>alert("bad")</script> & tests')
        root = ET.fromstring(rss_feed([row], {}))
        self.assertIsNone(root.find("channel/item/link"))
        self.assertNotIn("\x00", root.find("channel/item/title").text)
        self.assertIn("😀", root.find("channel/item/title").text)
        self.assertIn("&lt;script&gt;", root.find("channel/item/description").text)
        self.assertIsNone(root.find(".//script"))
        item = json_feed([row], {})["items"][0]
        self.assertNotIn("url", item)
        self.assertNotIn("external_url", item)
        self.assertNotIn("content_html", item)

    def test_description_limits_empty_feeds_and_files_include_only_saved_rows(self):
        row = job(descriptionText="x" * (MAX_FEED_DESCRIPTION + 20))
        item = json_feed([row], {})["items"][0]
        self.assertTrue(item["_hiringsignal"]["descriptionTruncated"])
        self.assertIn("Description shortened", item["content_text"])
        self.assertNotIn("x" * (MAX_FEED_DESCRIPTION + 1), item["content_text"])
        report = {"results": [], "summary": {}, "diagnostics": [], "knownJobIds": [row["jobKey"]]}
        with tempfile.TemporaryDirectory() as directory:
            export_results(report, directory)
            self.assertEqual(json.loads((Path(directory) / "jobs.feed.json").read_text())["items"], [])
            self.assertEqual(ET.parse(Path(directory) / "jobs.rss").findall("channel/item"), [])


class EmploymentTypeTests(unittest.TestCase):
    def test_explicit_labels_only_and_ambiguous_source_labels_stay_unknown(self):
        for raw, expected in (("FullTime", "full-time"), ("Full-time", "full-time"), ("Part time", "part-time"),
                              ("Contractor", "contract"), ("Intern", "internship"), ("Temporary", "temporary"),
                              ("Apprenticeship", "apprenticeship"), ("Freelance", "freelance"),
                              ("Full-time or part-time", "unknown"), ("", "unknown")):
            self.assertEqual(normalized_employment_type(raw), expected)
        board = Board("lever", "acme")
        raw = {"id": "123", "text": "Full-time developer", "hostedUrl": "https://jobs.lever.co/acme/123",
               "categories": {"commitment": "Part-time"}}
        row = normalize_job(board, raw, request_url(board))
        self.assertEqual(row["employmentType"], "Part-time")
        self.assertEqual(row["employmentTypeNormalized"], "part-time")
        self.assertEqual(row["fieldSources"]["employmentTypeNormalized"], "categories.commitment:exact-label-map")
        greenhouse = normalize_job(Board("greenhouse", "acme"), {"id": "123", "title": "Full-time intern", "absolute_url": "https://example.org/job"}, "https://boards-api.greenhouse.io")
        self.assertEqual(greenhouse["employmentTypeNormalized"], "unknown")

    def test_validated_or_matching_and_unmatched_types_do_not_pass(self):
        config = RunConfig.from_dict({"boards": ["lever:acme"], "employmentTypes": ["internship", "part-time"]})
        self.assertIsNone(filter_reason(job(employmentTypeNormalized="part-time"), config))
        self.assertEqual(filter_reason(job(), config), "employment_type_not_included")
        self.assertEqual(filter_reason(job(employmentTypeNormalized="unknown"), config), "employment_type_not_included")
        for value in ("full-time", ["FullTime"], [None], ["full-time"] * 9):
            with self.assertRaises(ValueError):
                RunConfig.from_dict({"boards": ["lever:acme"], "employmentTypes": value})

    def test_source_failure_fatal_only_without_a_successful_source_or_saved_rows(self):
        for saved, successful, failed, expected in (([], 0, 1, True), ([], 1, 1, False), ([], 1, 0, False), ([job()], 0, 1, False), ([], 0, 0, False)):
            self.assertEqual(source_failure_is_fatal({"results": saved, "summary": {"successfulBoards": successful, "failedBoards": failed}}), expected)


class EmploymentFilterIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_filtered_employment_and_known_jobs_never_reach_save_callback(self):
        class Client:
            requests = 0
            def __init__(self, config): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            async def fetch_json(self, url):
                self.requests += 1
                return [{"id": identity, "text": "Engineer", "hostedUrl": f"https://jobs.lever.co/acme/{identity}",
                         "categories": {"commitment": commitment}}
                        for identity, commitment in (("old", "Full-time"), ("wrong", "Part-time"), ("unknown", ""), ("new", "FullTime"))]
        config = RunConfig.from_dict({"boards": ["lever:acme"], "knownJobIds": ["lever:acme:old"], "employmentTypes": ["full-time"]})
        accepted = []
        async def save(row):
            accepted.append(row)
            return True
        report = await scrape_boards(config, save, client_factory=Client)
        self.assertEqual([row["id"] for row in accepted], ["new"])
        self.assertEqual(report["summary"]["knownJobsSkipped"], 1)
        self.assertEqual(report["diagnostics"][0]["filterReasons"], {"employment_type_not_included": 2})
        self.assertEqual(report["summary"]["signals"]["jobsByEmploymentType"], {"full-time": 1})
