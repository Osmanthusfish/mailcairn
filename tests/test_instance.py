"""Verify local instance discovery against a live, authenticated HTTP server."""
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

from mailcairn.instance import clear_instance, existing_launch, publish_instance
from mailcairn.server import LocalServer
from mailcairn.store import Store


class InstanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mailcairn-instance-test-")
        self.root = Path(self.temp.name)
        self.metadata = self.root / ".mailcairn-instance.json"
        self.store = Store(self.root / "archive.sqlite3")
        self.server = LocalServer(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()
        self.client = build_opener(ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.temp.cleanup()

    def test_published_metadata_discovers_authenticated_exact_archive(self):
        publish_instance(self.root, self.server)
        metadata = json.loads(self.metadata.read_text(encoding="utf-8"))
        self.assertEqual(metadata["port"], self.server.server_port)
        self.assertEqual(metadata["token"], self.server.token)
        self.assertEqual(existing_launch(self.root),
                         self.server.origin + "/#session=" + self.server.token)
        if os.name != "nt":
            self.assertEqual(self.metadata.stat().st_mode & 0o777, 0o600)

    def test_instance_endpoint_requires_session_cookie(self):
        with self.assertRaises(HTTPError) as caught:
            self.client.open(self.server.origin + "/api/instance", timeout=5)
        self.assertEqual(caught.exception.code, 401)
        caught.exception.close()
        request = Request(self.server.origin + "/api/instance", headers={
            "Cookie": self.server.cookie_name + "=" + self.server.token})
        with self.client.open(request, timeout=5) as response:
            self.assertEqual(json.load(response), {"archive": str(self.store.path.resolve())})

    def test_cleanup_removes_only_this_instances_record(self):
        publish_instance(self.root, self.server)
        clear_instance(self.root, self.server)
        self.assertFalse(self.metadata.exists())
        replacement = {"port": self.server.server_port, "token": "x" * 43}
        self.metadata.write_text(json.dumps(replacement), encoding="utf-8")
        clear_instance(self.root, self.server)
        self.assertEqual(json.loads(self.metadata.read_text()), replacement)

    def test_discovery_works_while_archive_read_slots_are_busy(self):
        publish_instance(self.root, self.server)
        acquired = 0
        try:
            while self.server.read_slots.acquire(blocking=False):
                acquired += 1
            self.assertEqual(existing_launch(self.root),
                             self.server.origin + "/#session=" + self.server.token)
        finally:
            for _ in range(acquired):
                self.server.read_slots.release()

    def test_discovery_rejects_valid_session_for_different_archive(self):
        other = self.root / "other"
        other.mkdir()
        publish_instance(other, self.server)
        self.assertIsNone(existing_launch(other))

    def test_discovery_rejects_wrong_session(self):
        self.metadata.write_text(json.dumps({"port": self.server.server_port,
                                             "token": "x" * 43}), encoding="utf-8")
        self.assertIsNone(existing_launch(self.root))

    def test_missing_and_malformed_metadata_are_ignored(self):
        self.assertIsNone(existing_launch(self.root))
        for content in ("", "{", "null", "[]", "{}", "x" * 10000):
            with self.subTest(content=content[:20]):
                self.metadata.write_text(content, encoding="utf-8")
                self.assertIsNone(existing_launch(self.root))

    def test_invalid_ports_and_tokens_are_ignored(self):
        cases = [
            {"port": "https://untrusted.invalid/", "token": self.server.token},
            {"port": 0, "token": self.server.token},
            {"port": 65536, "token": self.server.token},
            {"port": True, "token": self.server.token},
            {"port": self.server.server_port, "token": None},
            {"port": self.server.server_port, "token": "bad\r\nInjected: yes"},
        ]
        for metadata in cases:
            with self.subTest(metadata=metadata):
                self.metadata.write_text(json.dumps(metadata), encoding="utf-8")
                self.assertIsNone(existing_launch(self.root))


if __name__ == "__main__":
    unittest.main()
