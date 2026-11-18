"""Real loopback HTTP workflow, access controls and recoverable failures."""
import hashlib
import http.client
import socket
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, build_opener, ProxyHandler

from mailcairn.server import LocalServer, STATIC
from mailcairn.store import Store, restore_backup
from tests.helpers import mbox, message


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "archive.sqlite3")
        self.server = LocalServer(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()
        self.client = build_opener(ProxyHandler({}))
        self.cookie = ""

    def tearDown(self):
        for job in self.server.jobs.values():
            job["cancel"].set()
        deadline = time.monotonic() + 10
        while self.server.operation.locked() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.temp.cleanup()

    def request(self, path, method="GET", body=None, headers=None):
        actual_headers = {"Origin": self.server.origin}
        if self.cookie:
            actual_headers["Cookie"] = self.cookie
        actual_headers.update(headers or {})
        request = Request(self.server.origin + path, data=body, method=method, headers=actual_headers)
        try:
            response = self.client.open(request, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.headers, response.read()

    def login(self):
        status, headers, body = self.request("/api/session", "POST", b"", {"X-MailCairn-Token": self.server.token})
        self.assertEqual(status, 200, body)
        self.cookie = headers["Set-Cookie"].split(";", 1)[0]
        return headers

    def get_json(self, path):
        status, headers, body = self.request(path)
        self.assertEqual(status, 200, body)
        return json.loads(body)

    def post(self, path, body=b"", extra=None):
        return self.request(path, "POST", body, {"X-MailCairn": "1", **(extra or {})})

    def wait_job(self, key):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            job = self.get_json("/api/jobs/" + key)
            if job["status"] != "running":
                self.assertFalse(self.server.operation.locked(), "Done must mean the operation lock has been released")
                return job
            time.sleep(0.01)
        self.fail("HTTP background job did not complete")

    def import_mail(self, raw, name="mail.eml"):
        status, _, body = self.post("/api/import?name=" + quote(name), raw)
        self.assertEqual(status, 202, body)
        return self.wait_job(json.loads(body)["job_id"])

    def test_session_required_and_cookie_is_private(self):
        self.assertEqual(self.request("/api/stats")[0], 401)
        self.assertEqual(self.request("/api/session", "POST", b"", {"X-MailCairn-Token": "wrong"})[0], 401)
        headers = self.login()
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", headers["Set-Cookie"])
        self.assertEqual(self.get_json("/api/stats")["messages"], 0)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")

    def test_host_origin_and_cross_site_are_rejected(self):
        self.login()
        for header in ({"Host": "evil.example.com"}, {"Origin": "https://evil.example.com"}, {"Sec-Fetch-Site": "cross-site"}):
            with self.subTest(header=header):
                self.assertEqual(self.request("/api/stats", headers=header)[0], 403)
        self.assertEqual(self.request("/api/import", "OPTIONS")[0], 403)
        with self.assertRaises(ValueError):
            LocalServer(("0.0.0.0", 0), self.store)

    def test_mutations_require_custom_header(self):
        self.login()
        self.assertEqual(self.request("/api/verify", "POST", b"")[0], 403)
        status, _, body = self.post("/api/verify")
        self.assertEqual(status, 202)
        self.assertEqual(self.wait_job(json.loads(body)["job_id"])["result"]["checked"], 0)

    def test_complete_import_search_download_export_backup_restore_flow(self):
        self.login()
        payload = "保修凭证\nSERIAL LANTERN-421\n".encode()
        raw = message("Coffee machine warranty", "Keep your lantern receipt safe.", attachment=("保修凭证.txt", payload), crlf=True)
        job = self.import_mail(raw)
        self.assertEqual(job["status"], "done")
        self.assertEqual(job["result"]["added"], 1)
        results = self.get_json("/api/messages?q=lantern")
        self.assertEqual(results["total"], 1)
        row = results["messages"][0]["id"]
        detail = self.get_json(f"/api/messages/{row}")
        self.assertNotIn("raw", detail)
        self.assertEqual(detail["attachments"][0]["name"], "保修凭证.txt")
        status, headers, downloaded = self.request(f"/api/messages/{row}/eml")
        self.assertEqual((status, downloaded), (200, raw))
        self.assertTrue(headers["Content-Disposition"].startswith("attachment;"))
        attachment = detail["attachments"][0]
        status, headers, downloaded = self.request(f"/api/messages/{row}/attachments/{attachment['index']}")
        self.assertEqual((status, downloaded), (200, payload))
        self.assertIn("filename*=UTF-8''", headers["Content-Disposition"])
        run = job["result"]["id"]
        report = self.get_json(f"/api/imports/{run}/receipt")
        self.assertEqual(report["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(len(report["items"]), 1)
        status, _, exported = self.request("/api/export?q=lantern")
        self.assertEqual(status, 200)
        duplicate = self.import_mail(exported, "roundtrip.mbox")
        self.assertEqual(duplicate["result"]["duplicates"], 1)
        status, _, backup = self.request("/api/backup")
        self.assertEqual(status, 200)
        backup_path = self.root / "snapshot.sqlite3"
        backup_path.write_bytes(backup)
        restored_path = self.root / "restored" / "archive.sqlite3"
        restore_backup(backup_path, restored_path)
        restored = Store(restored_path)
        self.assertEqual(restored.search({"q": "lantern"})["total"], 1)
        self.assertEqual(restored.message(row, raw=True)["raw"], raw)
        status, _, body = self.post("/api/verify")
        self.assertEqual(status, 202)
        verified = self.wait_job(json.loads(body)["job_id"])["result"]
        self.assertEqual((verified["checked"], verified["mismatches"], verified["search_index"]), (1, [], "ok"))

    def test_upload_errors_are_explicit_and_unlock_future_import(self):
        self.login()
        self.assertEqual(self.post("/api/import?name=archive.zip", b"PKfile")[0], 400)
        self.assertEqual(self.post("/api/import?name=empty.mbox", b"")[0], 400)
        self.server.max_upload = 8
        self.assertEqual(self.post("/api/import?name=too-big.eml", message())[0], 413)
        self.server.max_upload = 20 * 1024 ** 3
        failed = self.import_mail(b"not a mailbox", "broken.mbox")
        self.assertEqual(failed["result"]["status"], "failed")
        good = self.import_mail(message())
        self.assertEqual(good["result"]["added"], 1)
        self.assertEqual(list(self.root.glob(".upload-*")), [])

    def test_parallel_operations_conflict_without_silent_loss(self):
        self.login()
        self.server.operation.acquire()
        try:
            self.assertEqual(self.post("/api/import?name=mail.eml", message())[0], 409)
            self.assertEqual(self.post("/api/verify")[0], 409)
        finally:
            self.server.operation.release()
        self.assertEqual(self.import_mail(message())["result"]["added"], 1)

    def test_insufficient_space_does_not_leave_lock_or_temp_file(self):
        self.login()
        usage = type("Usage", (), {"free": 0})()
        with patch("mailcairn.server.shutil.disk_usage", return_value=usage):
            self.assertEqual(self.post("/api/import?name=mail.eml", message())[0], 507)
        self.assertFalse(self.server.operation.locked())
        self.assertEqual(list(self.root.glob(".upload-*")), [])

    def test_oversized_message_receipt_and_job_cancel_endpoint(self):
        self.login()
        self.server.max_message = 1000
        result = self.import_mail(mbox(message("Large", "x" * 5000), message("Small")), "partial.mbox")
        self.assertEqual(result["result"]["status"], "partial")
        self.assertEqual((result["result"]["added"], result["result"]["skipped"]), (1, 1))
        self.assertEqual(self.post("/api/jobs/" + result["id"] + "/cancel")[0], 200)
        self.assertEqual(self.post("/api/jobs/missing/cancel")[0], 404)

    def test_invalid_filter_and_path_traversal_do_not_disclose_files(self):
        self.login()
        self.assertEqual(self.request("/api/messages?after=tomorrow")[0], 400)
        self.assertEqual(self.request("/../app.py")[0], 404)
        self.assertEqual(self.request("/%2e%2e/app.py")[0], 404)
        self.assertEqual(self.request("/api/jobs/unknown")[0], 404)

    def test_local_typefaces_are_complete_font_responses_before_login(self):
        status, headers, body = self.request("/fonts.css")
        self.assertEqual(status, 200, body)
        self.assertEqual(headers.get_content_type(), "text/css")
        self.assertEqual(body, (STATIC / "fonts.css").read_bytes())
        for name in ("HankenGrotesk.ttf", "Newsreader.ttf"):
            with self.subTest(font=name):
                path = "/fonts/" + name
                self.assertIn(path.encode(), body)
                status, headers, font = self.request(path)
                self.assertEqual(status, 200)
                self.assertEqual(headers.get_content_type(), "font/ttf")
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(int(headers["Content-Length"]), len(font))
                self.assertEqual(font, (STATIC / "fonts" / name).read_bytes())
                self.assertEqual(font[:4], b"\x00\x01\x00\x00", "Response must be a TrueType sfnt, not an HTML fallback")
                tables = int.from_bytes(font[4:6], "big")
                self.assertGreater(tables, 0)
                self.assertGreaterEqual(len(font), 12 + tables * 16)
                for index in range(tables):
                    record = font[12 + index * 16:28 + index * 16]
                    offset = int.from_bytes(record[8:12], "big")
                    length = int.from_bytes(record[12:16], "big")
                    self.assertLessEqual(offset + length, len(font), "Every sfnt table must be complete")

    def test_language_catalogue_is_local_script_available_before_session(self):
        status, headers, body = self.request("/i18n.js")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get_content_type(), "text/javascript")
        self.assertEqual(body, (STATIC / "i18n.js").read_bytes())
        self.assertIn("全部邮件".encode(), body)
        self.assertEqual(self.request("/api/stats")[0], 401)

    def test_startup_recovery_script_is_complete_local_and_available_before_session(self):
        status, headers, body = self.request("/startup.js")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get_content_type(), "text/javascript")
        self.assertEqual(int(headers["Content-Length"]), len(body))
        self.assertEqual(body, (STATIC / "startup.js").read_bytes())
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertNotIn("unsafe-inline", headers["Content-Security-Policy"])
        self.assertEqual(self.request("/api/stats")[0], 401)
        for path in ("/startup.js/extra", "/static/startup.js", "/../startup.js"):
            with self.subTest(path=path):
                self.assertNotEqual(self.request(path)[0], 200)

    def test_font_routes_do_not_expose_directories_or_unlisted_files(self):
        self.login()
        for path in ("/fonts/", "/fonts/unknown.ttf", "/fonts/Newsreader-OFL.txt",
                     "/fonts/../app.js", "/fonts/%2e%2e/app.js",
                     "/fonts/../../server.py", "/fonts/%2e%2e/%2e%2e/server.py",
                     "/fonts/Newsreader.ttf/extra", "/fonts%2fNewsreader.ttf"):
            with self.subTest(path=path):
                status, headers, body = self.request(path)
                self.assertEqual(status, 404, body)
                self.assertEqual(headers.get_content_type(), "application/json")


    def raw_request(self, path, headers, body=b"", *, end_body=False):
        """Send exact HTTP framing that high-level clients normally normalize."""
        request = [f"POST {path} HTTP/1.1", f"Host: 127.0.0.1:{self.server.server_port}",
                   f"Origin: {self.server.origin}", f"Cookie: {self.cookie}",
                   "X-MailCairn: 1", *headers, "", ""]
        with socket.create_connection(self.server.server_address, timeout=3) as connection:
            connection.sendall("\r\n".join(request).encode("ascii") + body)
            if end_body:
                connection.shutdown(socket.SHUT_WR)
            response = http.client.HTTPResponse(connection)
            response.begin()
            return response.status, response.read()

    def test_http_framing_rejects_ambiguous_lengths_and_transfer_encoding(self):
        self.login()
        cases = [("Content-Length: 0", "Content-Length: 1"),
                 ("Content-Length: -1",), ("Content-Length: +0",),
                 ("Content-Length: 0, 0",), ("Content-Length: invalid",),
                 ("Content-Length: 0", "Transfer-Encoding: chunked")]
        for headers in cases:
            with self.subTest(headers=headers):
                status, body = self.raw_request("/api/import?name=test.eml", headers)
                self.assertEqual(status, 400, body)
        self.assertFalse(self.server.operation.locked())
        self.assertEqual(self.store.stats()["imports"], [])

    def test_large_upload_rejected_from_headers_without_reading_body(self):
        self.login()
        self.server.max_upload = 1024 * 1024
        status, body = self.raw_request("/api/import?name=large.eml", ["Content-Length: 8388608"])
        self.assertEqual(status, 413, body)
        self.assertFalse(self.server.operation.locked())
        self.assertEqual(list(self.root.glob(".upload-*")), [])
        self.assertEqual(self.store.stats()["imports"], [])
        self.assertEqual(self.get_json("/api/stats")["messages"], 0)

    def test_non_upload_endpoints_reject_nonempty_body(self):
        self.login()
        self.assertEqual(self.post("/api/verify", b"unexpected body")[0], 400)
        self.assertEqual(self.request("/api/session", "POST", b"unexpected body",
                                      {"X-MailCairn-Token": self.server.token})[0], 400)
        self.assertEqual(self.server.jobs, {})
        self.assertFalse(self.server.operation.locked())

    def test_interrupted_upload_cleans_temp_and_allows_retry(self):
        self.login()
        status, body = self.raw_request("/api/import?name=broken.eml", ["Content-Length: 4096"],
                                        b"Subject: incomplete\n\npartial", end_body=True)
        self.assertEqual(status, 400, body)
        self.assertFalse(self.server.operation.locked())
        self.assertEqual(list(self.root.glob(".upload-*")), [])
        self.assertEqual(self.store.stats()["imports"], [])
        self.assertEqual(self.import_mail(message())["result"]["added"], 1)

    def test_bounded_jobs_keep_receipts_after_ephemeral_jobs_expire(self):
        self.login()
        imported = self.import_mail(message())
        receipt_id = imported["result"]["id"]
        for _ in range(44):
            job = self.server.new_job("verify")
            self.server.update_job(job, status="done", result={})
        self.assertLessEqual(len(self.server.jobs), 40)
        self.assertEqual(self.get_json(f"/api/imports/{receipt_id}")["added"], 1)

    def test_email_html_stays_plain_json_and_downloads_are_attachments(self):
        self.login()
        raw = message('<img src=x onerror=alert(1)>', html='<script>alert(1)</script><p>Visible</p>',
                      attachment=("../evil\"name.txt", b"untrusted download"))
        self.import_mail(raw)
        detail = self.get_json("/api/messages/1")
        self.assertEqual(detail["subject"], '<img src=x onerror=alert(1)>')
        status, headers, _ = self.request("/api/messages/1/eml")
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn("object-src 'none'", headers["Content-Security-Policy"])
        self.assertTrue(headers["Content-Disposition"].startswith("attachment;"))
        index = detail["attachments"][0]["index"]
        status, headers, payload = self.request(f"/api/messages/1/attachments/{index}")
        self.assertEqual((status, payload), (200, b"untrusted download"))
        self.assertEqual(headers["Content-Type"], "application/octet-stream")
        self.assertNotIn("../", headers["Content-Disposition"])


    def test_incomplete_headers_expire_and_server_remains_available(self):
        # A deadline bounds clients that never finish sending their headers.
        with patch("mailcairn.server.HEADER_TIMEOUT", 0.15):
            with socket.create_connection(self.server.server_address, timeout=3) as connection:
                connection.sendall(b"GET / HTTP/1.1\r\nHost: ")
                try:
                    closed = connection.recv(1)
                except (ConnectionResetError, ConnectionAbortedError):
                    closed = b""
                self.assertEqual(closed, b"")
        self.assertEqual(self.request("/")[0], 200)

    def test_request_worker_limit_rejects_excess_and_recovers_slots(self):
        from mailcairn.server import Handler
        entered = threading.Condition()
        active = []
        release = threading.Event()
        finished = threading.Event()
        original = Handler.handle

        def held_handler(handler):
            with entered:
                active.append(handler)
                entered.notify_all()
            release.wait(5)
            try:
                original(handler)
            finally:
                with entered:
                    active.remove(handler)
                    if not active:
                        finished.set()

        with patch("mailcairn.server.MAX_REQUEST_THREADS", 2):
            server = LocalServer(("127.0.0.1", 0), self.store)
        serving = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        serving.start()
        clients = []
        try:
            with patch.object(Handler, "handle", held_handler):
                for _ in range(2):
                    clients.append(socket.create_connection(server.server_address, timeout=3))
                with entered:
                    self.assertTrue(entered.wait_for(lambda: len(active) == 2, timeout=3))
                with socket.create_connection(server.server_address, timeout=3) as excess:
                    try:
                        excess.sendall(b"GET / HTTP/1.0\r\n\r\n")
                        closed = excess.recv(1)
                    except (ConnectionResetError, ConnectionAbortedError):
                        closed = b""
                    self.assertEqual(closed, b"", "Excess clients must not allocate unbounded workers")
                for client in clients:
                    client.close()
                release.set()
                self.assertTrue(finished.wait(3))
            # Handler completion precedes the server's worker-finally by a few
            # instructions; wait for actual capacity instead of racing cleanup.
            self.assertTrue(server.request_slots.acquire(timeout=3))
            server.request_slots.release()
            # Both admitted workers have completed; a subsequent client works.
            with self.client.open(server.origin + "/", timeout=3) as response:
                self.assertEqual(response.status, 200)
        finally:
            release.set()
            for client in clients:
                client.close()
            server.shutdown()
            serving.join(timeout=3)
            server.server_close()

    def test_download_capacity_returns_explicit_error_and_frees_slots(self):
        self.login()
        slots = []
        try:
            while self.server.read_slots.acquire(blocking=False):
                slots.append(True)
            self.assertEqual(self.request("/api/export")[0], 503)
            self.assertEqual(self.request("/api/backup")[0], 503)
            # In-memory job polling retains capacity during export saturation.
            job = self.server.new_job("verify")
            self.server.update_job(job, status="done", result={})
            self.assertEqual(self.get_json("/api/jobs/" + job["id"])["status"], "done")
        finally:
            for _ in slots:
                self.server.read_slots.release()
        self.assertEqual(self.request("/api/export")[0], 200)


if __name__ == "__main__":
    unittest.main()
