"""Real loopback connection API boundaries; synthetic manager, no mail network."""
import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from mailcairn.server import LocalServer
from mailcairn.store import Store


PASSWORD = "SYNTHETIC-SECRET-do-not-echo-704"


class FakeSyncManager:
    """Implements the public manager contract without credentials or networking."""

    def __init__(self):
        self.calls = []
        self.accounts = []
        self.secrets = {}
        self.credentials_persistent = True
        self.settings_error = ""
        self.failure = None

    def start(self):
        pass

    def stop(self):
        pass

    def _call(self, method, value=None):
        self.calls.append((method, copy.deepcopy(value)))
        if self.failure:
            raise self.failure

    def status(self):
        self._call("status")
        return {"accounts": copy.deepcopy(self.accounts), "credentials_persistent": self.credentials_persistent,
                "settings_error": self.settings_error}

    def add(self, config):
        self._call("add", config)
        account = {key: config[key] for key in ("provider", "host", "port", "username", "folder")}
        account.update(id="fixture-1", paused=False, status="ready")
        self.accounts = [account]
        self.secrets[account["id"]] = config["password"]
        return copy.deepcopy(account)

    def _action(self, method, key):
        self._call(method, key)
        account = next((item for item in self.accounts if item["id"] == key), None)
        if account is None:
            raise KeyError(key)
        if method == "pause":
            account["paused"] = True
        elif method == "resume":
            account["paused"] = False
        elif method == "sync_now":
            account["status"] = "queued"
        elif method == "remove":
            self.accounts.remove(account)
            self.secrets.pop(key, None)
        return copy.deepcopy(account)

    def sync_now(self, key):
        return self._action("sync_now", key)

    def pause(self, key):
        return self._action("pause", key)

    def resume(self, key):
        return self._action("resume", key)

    def remove(self, key):
        return self._action("remove", key)


class SyncHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "archive.sqlite3")
        self.manager = FakeSyncManager()
        with patch("mailcairn.server.SyncManager", return_value=self.manager):
            self.server = LocalServer(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()
        self.cookie = ""
        self.config = {"provider": "imap", "host": "imap.example.invalid", "port": 993,
                       "username": "synthetic@example.invalid", "password": PASSWORD,
                       "remember": True, "folder": "INBOX"}

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.temp.cleanup()

    def request(self, path="/api/connections", method="GET", body=None, headers=None):
        merged = {"Origin": self.server.origin}
        if self.cookie:
            merged["Cookie"] = self.cookie
        merged.update(headers or {})
        client = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            client.request(method, path, body=body, headers=merged)
            reply = client.getresponse()
            return reply.status, dict(reply.getheaders()), reply.read()
        finally:
            client.close()

    def login(self):
        status, headers, body = self.request("/api/session", "POST", b"", {"X-MailCairn-Token": self.server.token})
        self.assertEqual(status, 200, body)
        self.cookie = headers["Set-Cookie"].split(";", 1)[0]

    def post(self, path="/api/connections", body=None, headers=None):
        payload = json.dumps(self.config).encode() if body is None else body
        return self.request(path, "POST", payload, {"X-MailCairn": "1", "Content-Type": "application/json", **(headers or {})})

    def add(self):
        status, _, body = self.post()
        self.assertEqual(status, 201, body)
        return json.loads(body)["connection"]

    def assert_safe(self, headers, body):
        self.assertNotIn(PASSWORD.encode(), body)
        self.assertNotIn(PASSWORD, json.dumps(headers))
        self.assertNotIn(b'"password"', body)
        self.assertEqual(headers.get("Cache-Control"), "no-store")

    def test_connection_endpoints_require_session_before_manager_access(self):
        for path, method, body in [("/api/connections", "GET", None),
                                   ("/api/connections", "POST", json.dumps(self.config).encode()),
                                   ("/api/connections/fixture-1/sync", "POST", b"")]:
            with self.subTest(path=path, method=method):
                status, _, _ = self.request(path, method, body, {"X-MailCairn": "1", "Content-Type": "application/json"})
                self.assertEqual(status, 401)
        self.assertEqual(self.manager.calls, [])

    def test_connection_mutations_require_csrf_header_and_trusted_origin(self):
        self.login()
        for headers in ({"X-MailCairn": ""}, {"Origin": "https://attacker.invalid"},
                        {"Host": "attacker.invalid"}, {"Sec-Fetch-Site": "cross-site"}):
            with self.subTest(headers=headers):
                status, _, _ = self.post(headers=headers)
                self.assertEqual(status, 403)
        for action in ("sync", "pause", "resume", "disconnect"):
            status, _, _ = self.request(f"/api/connections/fixture-1/{action}", "POST", b"")
            self.assertEqual(status, 403)
        self.assertEqual(self.manager.calls, [])

    def test_connection_list_and_add_expose_only_public_configuration(self):
        self.login()
        created = self.add()
        self.assertEqual(created["username"], self.config["username"])
        self.assertEqual(self.manager.calls[-1], ("add", self.config))
        self.assertEqual(self.manager.secrets["fixture-1"], PASSWORD)
        status, headers, body = self.request()
        self.assertEqual(status, 200)
        self.assert_safe(headers, body)
        data = json.loads(body)
        self.assertEqual(data["connections"], [created])
        self.assertEqual(data["capabilities"], {"persistent_credentials": True, "interval_seconds": 300})
        self.manager.credentials_persistent = False
        self.assertFalse(json.loads(self.request()[2])["capabilities"]["persistent_credentials"])
        self.assertNotIn(PASSWORD.encode(), self.store.path.read_bytes(), "HTTP settings must not spill into the mail archive")

    def test_add_reply_and_action_replies_never_echo_password(self):
        self.login()
        status, headers, body = self.post()
        self.assertEqual(status, 201)
        self.assert_safe(headers, body)
        for action, method in (("sync", "sync_now"), ("pause", "pause"), ("resume", "resume"), ("disconnect", "remove")):
            with self.subTest(action=action):
                status, headers, body = self.post(f"/api/connections/fixture-1/{action}", b"")
                self.assertEqual(status, 200, body)
                self.assertTrue(json.loads(body)["ok"])
                self.assertEqual(self.manager.calls[-1], (method, "fixture-1"))
                self.assert_safe(headers, body)
        self.assertEqual(json.loads(self.request()[2])["connections"], [])

    def test_corrupt_connection_settings_are_visible_without_exposing_credentials(self):
        self.login()
        self.manager.settings_error = "Connection settings could not be saved. Check disk space and folder permissions."
        self.manager.credentials_persistent = False
        status, headers, body = self.request()
        self.assertEqual(status, 200)
        self.assert_safe(headers, body)
        payload = json.loads(body)
        self.assertEqual(payload["settings_error"], self.manager.settings_error)
        self.assertEqual(payload["connections"], [])
        self.assertFalse(payload["capabilities"]["persistent_credentials"])
        self.manager.settings_error = ""
        self.assertEqual(json.loads(self.request()[2])["settings_error"], "")

    def test_json_body_size_boundary_and_content_type(self):
        self.login()
        encoded = json.dumps(self.config).encode()
        for body, content_type, expected in ((b"", "application/json", 400),
                                              (encoded + b" " * (16385 - len(encoded)), "application/json", 413),
                                              (encoded, "text/plain", 415),
                                              (encoded, "application/x-www-form-urlencoded", 415)):
            with self.subTest(expected=expected, content_type=content_type):
                status, headers, response = self.post(body=body, headers={"Content-Type": content_type})
                self.assertEqual(status, expected, response)
                self.assert_safe(headers, response)
        self.assertEqual(self.manager.calls, [])
        status, _, body = self.post(body=encoded + b" " * (16384 - len(encoded)), headers={"Content-Type": "application/json; charset=utf-8"})
        self.assertEqual(status, 201, body)
        self.assertEqual(len(self.manager.calls), 1)

    def test_malformed_non_object_duplicate_and_invalid_utf8_json_are_rejected(self):
        self.login()
        for body in (b'{"password":', b"[]", b"null", b'"string"', b"42", b"true",
                     b'{"provider":"imap","provider":"gmail"}', b'{"password":"\xff"}'):
            with self.subTest(body=body):
                status, headers, response = self.post(body=body)
                self.assertEqual(status, 400, response)
                self.assert_safe(headers, response)
                self.assertEqual(json.loads(response)["error"], "Mailbox connection settings are not valid JSON.")
        self.assertEqual(self.manager.calls, [])

    def test_action_routes_validate_identifier_action_and_empty_body(self):
        self.login()
        for path in ("/api/connections/missing/unknown", "/api/connections/missing/sync/extra",
                     "/api/connections/bad%2Fid/sync", "/api/connections/" + "a" * 65 + "/sync"):
            with self.subTest(path=path):
                self.assertEqual(self.post(path, b"")[0], 404)
        self.assertEqual(self.manager.calls, [])
        self.assertEqual(self.post("/api/connections/missing/sync", b"{}")[0], 400)
        self.assertEqual(self.manager.calls, [])
        status, _, body = self.post("/api/connections/missing/sync", b"")
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body)["error"], "Mailbox connection not found.")

    def test_manager_validation_error_is_recoverable(self):
        self.login()
        self.manager.failure = ValueError("Choose INBOX for this connector.")
        status, _, body = self.post()
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"], "Choose INBOX for this connector.")
        self.manager.failure = None
        self.add()
        self.manager.failure = ValueError("Connection is paused.")
        self.assertEqual(self.post("/api/connections/fixture-1/sync", b"")[0], 400)
        self.manager.failure = None
        self.assertEqual(self.post("/api/connections/fixture-1/sync", b"")[0], 200)

    def test_unexpected_manager_failures_are_generic_and_do_not_leak_secrets(self):
        self.login()
        self.manager.failure = RuntimeError("Remote IMAP error: " + PASSWORD)
        for path, method, body in (("/api/connections", "GET", None),
                                   ("/api/connections", "POST", json.dumps(self.config).encode()),
                                   ("/api/connections/fixture-1/sync", "POST", b"")):
            with self.subTest(path=path, method=method):
                status, headers, response = self.request(path, method, body, {"X-MailCairn": "1", "Content-Type": "application/json"})
                self.assertEqual(status, 500)
                self.assert_safe(headers, response)
                self.assertNotIn(b"Remote IMAP", response)
        self.manager.failure = None
        self.assertEqual(self.request()[0], 200, "A failed request must not strand the server")

    def test_connection_get_rejects_body_and_cross_origin_access(self):
        self.login()
        self.assertEqual(self.request(body=b"{}")[0], 400)
        self.assertEqual(self.request(headers={"Origin": "https://attacker.invalid"})[0], 403)
        self.assertEqual(self.request(method="OPTIONS")[0], 403)
        self.assertEqual(self.manager.calls, [])


if __name__ == "__main__":
    unittest.main()
