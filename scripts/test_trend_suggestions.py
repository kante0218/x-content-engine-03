"""Offline regression checks: python scripts/test_trend_suggestions.py."""
import datetime as dt
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import trend_suggestions as t


class TrendSuggestionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = patch.object(t, "STATE", Path(self.tmp.name))
        self.state.start()
        self.addCleanup(self.state.stop)
        self.env = patch.dict(os.environ, {"X_BEARER_TOKEN": "test", "GEMINI_API_KEY": "test", "LINE_CHANNEL_ACCESS_TOKEN": "test",
                                          "LINE_TO": "U" + "0" * 32}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.drafts = {"emiri": {"trend": "コーヒー", "short": "コーヒー派？", "long": "朝の飲みものを選ぶ時間って、ちょっとした気分転換になりそう。" * 3}}

    def test_parse_and_validation(self):
        self.assertEqual(t.parse_trends({"data": [{"trend_name": "コーヒー", "tweet_count": 5}]}), ["コーヒー"])
        self.assertEqual(t.parse_suggestions(json.dumps(self.drafts), ["コーヒー"], ["emiri"]), self.drafts)
        for payload in ({}, {"data": []}, {"data": [{"trend_name": ""}]}):
            with self.assertRaises(ValueError):
                t.parse_trends(payload)
        for raw in ("oops", json.dumps(self.drafts).replace("emiri", "wakana"), "{}"):
            with self.assertRaises(ValueError):
                t.parse_suggestions(raw, ["コーヒー"], ["emiri"])
        with self.assertRaises(ValueError):
            t.parse_suggestions(json.dumps(self.drafts), ["別の話題"], ["emiri"])
        self.drafts["emiri"]["short"] = "長" * 36
        with self.assertRaises(ValueError):
            t.parse_suggestions(json.dumps(self.drafts), ["コーヒー"], ["emiri"])

    def test_x_only_get_and_no_fallback(self):
        response = io.BytesIO(b'{"data":[{"trend_name":"Coffee"}]}')
        with patch.object(t.urllib.request, "urlopen", return_value=response) as call:
            self.assertEqual(t.fetch_trends(), ["Coffee"])
        req = call.call_args.args[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(req.full_url, "https://api.x.com/2/trends/by/woeid/23424856?max_trends=20")
        error = urllib.error.HTTPError(req.full_url, 402, "Payment Required", {}, None)
        with patch.object(t.urllib.request, "urlopen", side_effect=error), patch.object(t, "generate") as generate:
            with self.assertRaises(urllib.error.HTTPError):
                t.run(["emiri"])
            generate.assert_not_called()

    def test_dry_run_and_send_guard(self):
        with patch.object(t, "fetch_trends", return_value=["コーヒー"]), patch.object(t, "generate", return_value=self.drafts), patch.object(t, "push") as push:
            t.run(["emiri"])
            push.assert_not_called()
        self.assertTrue((t.STATE / "preview-emiri.json").exists())
        self.assertFalse((t.STATE / "delivery-emiri.json").exists())
        os.environ.pop("LINE_TO")
        with patch.object(t, "fetch_trends") as fetch, self.assertRaises(ValueError):
            t.run(["emiri"], send=True)
        fetch.assert_not_called()

    def test_missing_generation_key_before_paid_fetch(self):
        os.environ.pop("GEMINI_API_KEY")
        with patch.object(t, "fetch_trends") as fetch, self.assertRaisesRegex(ValueError, "GEMINI_API_KEY"):
            t.run(["emiri"])
        fetch.assert_not_called()

    def test_timeout_retry_same_body_and_dedup(self):
        with patch.object(t, "fetch_trends", return_value=["コーヒー"]), patch.object(t, "generate", return_value=self.drafts), patch.object(t, "push", side_effect=TimeoutError):
            with self.assertRaises(TimeoutError):
                t.run(["emiri"], send=True)
        before = json.loads((t.STATE / "delivery-emiri.json").read_text())
        self.assertEqual(before["status"], "pending")
        with patch.object(t, "fetch_trends") as fetch, patch.object(t, "push") as push:
            t.run(["emiri"], send=True)
            self.assertEqual(push.call_args.args[0]["retry_key"], before["retry_key"])
            self.assertEqual(push.call_args.args[0]["text"], before["text"])
            t.run(["emiri"], send=True)
            self.assertEqual(push.call_count, 1)
            fetch.assert_not_called()

    def test_push_retry_acceptance_expiry_and_recipient(self):
        record = {"to": os.environ["LINE_TO"], "created_at": dt.datetime.now(t.JST).isoformat(),
                  "text": "案", "retry_key": "11111111-1111-4111-8111-111111111111"}
        error = urllib.error.HTTPError("https://api.line.me/v2/bot/message/push", 409, "Conflict",
                                       {"x-line-accepted-request-id": "accepted"}, None)
        with patch.object(t.urllib.request, "urlopen", side_effect=error) as call:
            t.push(record, "test", record["to"])
        request = call.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("X-line-retry-key"), record["retry_key"])
        with patch.object(t.urllib.request, "urlopen") as call:
            with self.assertRaises(ValueError):
                t.push(record, "test", "U" + "1" * 32)
            record["created_at"] = (dt.datetime.now(t.JST) - dt.timedelta(hours=24)).isoformat()
            with self.assertRaises(ValueError):
                t.push(record, "test", record["to"])
            call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
