import unittest
from unittest.mock import patch

from hiringsignal.client import FeedClient, FeedError, MAX_REQUESTS
from hiringsignal.config import RunConfig


class FakeContent:
    def __init__(self, data):
        self.data = data
    async def iter_chunked(self, size):
        yield self.data


class FakeResponse:
    def __init__(self, status=200, headers=None, data=b"[]"):
        self.status, self.headers, self.content = status, headers or {}, FakeContent(data)
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class TransportTests(unittest.IsolatedAsyncioTestCase):
    def client(self, response):
        client = FeedClient(RunConfig.from_dict({"boards": ["lever:acme"]}))
        client.session = FakeSession(response)
        return client

    async def test_redirect_is_rejected_without_following(self):
        client = self.client(FakeResponse(302, {"Location": "http://127.0.0.1"}))
        with self.assertRaises(FeedError) as caught:
            await client.fetch_json("https://api.lever.co/v0/postings/acme?mode=json")
        self.assertEqual(caught.exception.status, "redirect_rejected")
        self.assertEqual(len(client.session.calls), 1)
        self.assertFalse(client.session.calls[0][1]["allow_redirects"])

    async def test_long_retry_after_is_not_ignored_or_retried_early(self):
        client = self.client(FakeResponse(429, {"Retry-After": "60"}))
        with self.assertRaises(FeedError) as caught:
            await client.fetch_json("https://api.lever.co/v0/postings/acme")
        self.assertEqual(caught.exception.status, "rate_limited")
        self.assertEqual(client.requests, 1)

    async def test_body_and_json_and_attempt_limits(self):
        for response, code in [(FakeResponse(data=b"not JSON"), "invalid_json"), (FakeResponse(data=b"[123456789]"), "response_too_large")]:
            client = self.client(response)
            with patch("hiringsignal.client.MAX_RESPONSE_BYTES", 10), self.assertRaises(FeedError) as caught:
                await client.fetch_json("https://api.lever.co/v0/postings/acme")
            self.assertEqual(caught.exception.status, code)
        client = self.client(FakeResponse())
        client.requests = MAX_REQUESTS
        with self.assertRaises(FeedError) as caught:
            await client.fetch_json("https://api.lever.co/v0/postings/acme")
        self.assertEqual(caught.exception.status, "request_limit")
        self.assertEqual(client.session.calls, [])


if __name__ == "__main__":
    unittest.main()
