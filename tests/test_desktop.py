"""Exercise the desktop service against real locks, HTTP requests and workers."""
import http.client
import errno
import json
import os
from pathlib import Path
import tempfile
import socket
import threading
import time
import unittest
from unittest.mock import patch
from urllib.request import ProxyHandler, Request, build_opener

from app import ArchiveAlreadyOpen, archive_lock
from desktop import DESKTOP_SETTINGS, DesktopService, default_data_dir, preferred_port, restore_archive, switch_archive
from mailcairn.instance import existing_launch
from mailcairn.server import LocalServer
from mailcairn.store import Store


class DesktopServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mailcairn-desktop-test-")
        self.addCleanup(self.temporary.cleanup)
        self.temp_root = Path(self.temporary.name).resolve()
        self.folder = self.temp_root / "archive"
        self.service = DesktopService(self.folder)

    def tearDown(self):
        self.service.stop(cancel=True)

    def request(self, path):
        server = self.service.server
        client = build_opener(ProxyHandler({}))
        request = Request(server.origin + path, headers={"Cookie": server.cookie_name + "=" + server.token})
        with client.open(request, timeout=5) as response:
            return json.load(response)

    def test_frozen_default_is_persistent_and_not_bundle_extraction(self):
        with patch("sys.frozen", True, create=True), patch("sys._MEIPASS", "C:/temporary-bundle", create=True), patch.dict(os.environ, {"LOCALAPPDATA": str(self.folder)}):
            self.assertEqual(default_data_dir(), self.folder / "MailCairn")

    def test_source_default_reuses_source_data_directory(self):
        import desktop
        with patch("sys.frozen", False, create=True):
            self.assertEqual(default_data_dir(), Path(desktop.__file__).resolve().parent / "data")

    def test_stop_and_reopen_keeps_browser_origin_with_new_session_token(self):
        self.service.start()
        origin, token = self.service.server.origin, self.service.server.token
        record = json.loads((self.folder / DESKTOP_SETTINGS).read_text(encoding="utf-8"))
        self.assertEqual(record, {"port": self.service.server.server_port})
        self.service.stop()
        reopened = DesktopService(self.folder)
        self.addCleanup(reopened.stop)
        reopened.start()
        self.assertEqual(reopened.server.origin, origin)
        self.assertNotEqual(reopened.server.token, token)
        self.assertEqual(existing_launch(self.folder), reopened.launch)

    def test_occupied_remembered_port_falls_back_without_reusing_other_listener(self):
        self.folder.mkdir(parents=True)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            occupied = listener.getsockname()[1]
            (self.folder / DESKTOP_SETTINGS).write_text(json.dumps({"port": occupied}), encoding="utf-8")
            self.service.start()
            self.assertFalse(self.service.reused)
            self.assertNotEqual(self.service.server.server_port, occupied)
            assigned = self.service.server.server_port
            self.assertEqual(preferred_port(self.folder), assigned)
        self.service.stop()
        reopened = DesktopService(self.folder)
        self.addCleanup(reopened.stop)
        reopened.start()
        self.assertEqual(reopened.server.server_port, assigned)

    def test_port_preference_rejects_malformed_and_out_of_range_values(self):
        self.folder.mkdir(parents=True)
        path = self.folder / DESKTOP_SETTINGS
        for value in ({"port": True}, {"port": "8765"}, {"port": 0}, {"port": 65536}, [], None, {"port": 2.5}):
            with self.subTest(value=value):
                path.write_text(json.dumps(value), encoding="utf-8")
                self.assertEqual(preferred_port(self.folder), 8765)
        for data in (b"not-json", b"x" * 4097, b"\xff\xff"):
            path.write_bytes(data)
            self.assertEqual(preferred_port(self.folder), 8765)

    def test_bind_permission_error_does_not_silently_choose_another_port(self):
        with patch("desktop.LocalServer", side_effect=OSError(errno.EACCES, "test denied")) as server:
            with self.assertRaises(OSError):
                self.service.start()
        self.assertEqual(server.call_count, 1)
        with archive_lock(self.folder):
            pass

    def test_windows_reserved_port_uses_os_assigned_port_and_remembers_it(self):
        denied = OSError(errno.EACCES, "Windows reserved port")
        denied.winerror = 10013
        attempts = []

        def bind(address, store):
            attempts.append(address)
            if len(attempts) == 1:
                raise denied
            return LocalServer(address, store)

        with patch("desktop.LocalServer", side_effect=bind):
            self.service.start()
        self.assertEqual(attempts, [("127.0.0.1", 8765), ("127.0.0.1", 0)])
        assigned = self.service.server.server_port
        self.assertEqual(preferred_port(self.folder), assigned)
        self.assertEqual(self.request("/api/instance")["archive"], str(self.folder / "archive.sqlite3"))
        self.service.stop()
        reopened = DesktopService(self.folder)
        self.addCleanup(reopened.stop)
        reopened.start()
        self.assertEqual(reopened.server.server_port, assigned)

    def test_windows_global_bind_denial_stops_after_one_fallback_and_releases_lock(self):
        denied = OSError(errno.EACCES, "Windows denied all local ports")
        denied.winerror = 10013
        with patch("desktop.LocalServer", side_effect=denied) as server:
            with self.assertRaises(OSError):
                self.service.start()
        self.assertEqual(server.call_args_list[0].args[0], ("127.0.0.1", 8765))
        self.assertEqual(server.call_args_list[1].args[0], ("127.0.0.1", 0))
        self.assertEqual(server.call_count, 2)
        self.assertFalse((self.folder / ".mailcairn-instance.json").exists())
        self.assertFalse((self.folder / DESKTOP_SETTINGS).exists())
        with archive_lock(self.folder):
            pass

    def test_second_listener_cannot_share_first_archives_http_port(self):
        self.service.start()
        original_port = self.service.server.server_port
        other = Store(Path(self.temporary.name) / "other" / "archive.sqlite3")
        second = None
        try:
            with self.assertRaises(OSError):
                second = LocalServer(("127.0.0.1", original_port), other)
        finally:
            if second is not None:
                second.server_close()
        self.assertEqual(self.request("/api/instance")["archive"], str(self.folder / "archive.sqlite3"))
        self.assertEqual(existing_launch(self.folder), self.service.launch)

    def test_failed_port_persistence_stops_server_and_releases_archive(self):
        with patch("desktop.remember_port", side_effect=OSError("test disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                self.service.start()
        self.assertFalse(self.service.thread.is_alive())
        self.assertFalse((self.folder / ".mailcairn-instance.json").exists())
        with archive_lock(self.folder):
            pass

    def test_server_is_authenticated_discoverable_and_lock_is_released_on_stop(self):
        launch = self.service.start()
        self.assertEqual(existing_launch(self.folder), launch)
        self.assertEqual(self.request("/api/instance")["archive"], str(self.folder / "archive.sqlite3"))
        with self.assertRaises(ArchiveAlreadyOpen), archive_lock(self.folder):
            pass
        self.service.stop()
        self.assertFalse((self.folder / ".mailcairn-instance.json").exists())
        with archive_lock(self.folder):
            pass

    def test_reused_instance_is_never_stopped_or_cleared(self):
        launch = self.service.start()
        peer = DesktopService(self.folder)
        self.assertEqual(peer.start(), launch)
        self.assertTrue(peer.reused)
        self.assertIsNone(peer.server)
        peer.stop(cancel=True)
        self.assertEqual(existing_launch(self.folder), launch)
        self.assertFalse(self.service.server.operation.locked())

    def test_unverifiable_busy_archive_is_not_opened_again(self):
        with archive_lock(self.folder), patch("desktop.time.sleep"):
            with self.assertRaisesRegex(ArchiveAlreadyOpen, "could not be verified"):
                self.service.start()
        self.assertIsNone(self.service.server)
        self.assertFalse((self.folder / "archive.sqlite3").exists())

    def test_failed_start_releases_lock_and_its_instance_record(self):
        with patch("desktop.publish_instance", side_effect=OSError("test disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                self.service.start()
        self.assertFalse((self.folder / ".mailcairn-instance.json").exists())
        with archive_lock(self.folder):
            pass

    def test_close_waits_for_worker_transaction_and_keeps_archive_locked(self):
        self.service.start()
        server = self.service.server
        entered, finish, completed = threading.Event(), threading.Event(), threading.Event()
        server.operation.acquire()
        job = server.new_job("test")

        def work(progress, cancelled):
            entered.set()
            finish.wait(5)
            # Use the real database to prove the job completed before lock release.
            with server.store.db() as connection:
                connection.execute("PRAGMA user_version=1")
            completed.set()
            return {"finished": True}

        server.start_job(job, work)
        self.assertTrue(entered.wait(2))
        stopping = threading.Thread(target=self.service.stop)
        stopping.start()
        try:
            time.sleep(.15)
            self.assertTrue(stopping.is_alive())
            self.assertFalse(job["cancel"].is_set())
            with self.assertRaises(ArchiveAlreadyOpen), archive_lock(self.folder):
                pass
        finally:
            finish.set()
            stopping.join(5)
        self.assertFalse(stopping.is_alive())
        self.assertTrue(completed.is_set())
        with archive_lock(self.folder):
            pass

    def test_cancel_close_cooperatively_cancels_job_and_waits_for_cleanup(self):
        self.service.start()
        server = self.service.server
        entered, cleanup = threading.Event(), threading.Event()
        server.operation.acquire()
        job = server.new_job("test")

        def work(progress, cancelled):
            entered.set()
            deadline = time.monotonic() + 5
            while not cancelled() and time.monotonic() < deadline:
                time.sleep(.01)
            return {"cancelled": cancelled()}

        server.start_job(job, work, cleanup=cleanup.set)
        self.assertTrue(entered.wait(2))
        self.service.stop(cancel=True)
        self.assertTrue(job["cancel"].is_set())
        self.assertTrue(cleanup.is_set())
        with archive_lock(self.folder):
            pass

    def test_close_drains_accepted_read_before_releasing_lock(self):
        self.service.start()
        entered, finish, returned = threading.Event(), threading.Event(), threading.Event()
        original = self.service.server.store.stats

        def slow_stats():
            entered.set()
            finish.wait(5)
            result = original()
            returned.set()
            return result

        self.service.server.store.stats = slow_stats
        results = []
        reading = threading.Thread(target=lambda: results.append(self.request("/api/stats")))
        reading.start()
        self.assertTrue(entered.wait(2))
        stopping = threading.Thread(target=self.service.stop)
        stopping.start()
        try:
            time.sleep(.15)
            self.assertTrue(stopping.is_alive())
            with self.assertRaises(ArchiveAlreadyOpen), archive_lock(self.folder):
                pass
        finally:
            finish.set()
            reading.join(5)
            stopping.join(5)
        self.assertTrue(returned.is_set())
        self.assertEqual(len(results), 1)
        self.assertFalse(stopping.is_alive())

    def test_close_waits_for_accepted_upload_and_its_later_import_job(self):
        self.service.start()
        server = self.service.server
        raw = (Path(__file__).parent / "fixtures" / "sample.mbox").read_bytes()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        stopping = None
        try:
            connection.putrequest("POST", "/api/import?name=sample.mbox")
            connection.putheader("Content-Length", str(len(raw)))
            connection.putheader("Cookie", server.cookie_name + "=" + server.token)
            connection.putheader("X-MailCairn", "1")
            connection.endheaders()
            connection.send(raw[:100])
            deadline = time.monotonic() + 2
            while not server.operation.locked() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(server.operation.locked())
            stopping = threading.Thread(target=self.service.stop)
            stopping.start()
            time.sleep(.15)
            self.assertTrue(stopping.is_alive())
            with self.assertRaises(ArchiveAlreadyOpen), archive_lock(self.folder):
                pass
            connection.send(raw[100:])
            response = connection.getresponse()
            self.assertEqual(response.status, 202)
            response.read()
        finally:
            connection.close()
            if stopping:
                stopping.join(5)
        self.assertFalse(stopping.is_alive())
        self.assertEqual(server.store.stats()["messages"], 20)
        self.assertFalse(list(self.folder.glob(".upload-*")))

    def create_backup(self):
        self.service.start()
        fixture = Path(__file__).parent / "fixtures" / "sample.mbox"
        self.service.server.store.import_file(fixture)
        backup = Path(self.temporary.name) / "backup.sqlite3"
        self.service.server.store.backup(backup)
        return backup

    def test_restore_backup_creates_new_archive_and_preserves_original(self):
        backup = self.create_backup()
        original = self.service
        restored = restore_archive(original, backup, Path(self.temporary.name))
        self.addCleanup(restored.stop)
        self.assertNotEqual(restored.folder, original.folder)
        self.assertTrue(restored.folder.name.startswith("MailCairn-restored-"))
        self.assertEqual(restored.server.store.stats()["messages"], 20)
        self.assertEqual(Store(original.folder / "archive.sqlite3").stats()["messages"], 20)
        self.assertIsNone(original._lock)
        self.assertEqual(existing_launch(restored.folder), restored.launch)
        # The native Open archive folder workflow can later reopen this folder.
        restored.stop()
        reopened = switch_archive(original, restored.folder)
        self.addCleanup(reopened.stop)
        self.assertEqual(reopened.server.store.stats()["messages"], 20)

    def test_invalid_backup_keeps_current_archive_open_and_removes_empty_destination(self):
        self.service.start()
        launch = self.service.launch
        backup = Path(self.temporary.name) / "invalid.sqlite3"
        backup.write_bytes(b"not a database")
        with self.assertRaises(Exception):
            restore_archive(self.service, backup, Path(self.temporary.name))
        self.assertEqual(existing_launch(self.folder), launch)
        self.assertFalse(list(Path(self.temporary.name).glob("MailCairn-restored-*")))

    def test_switch_to_missing_or_invalid_archive_keeps_current_archive_open(self):
        self.service.start()
        launch = self.service.launch
        other = Path(self.temporary.name) / "not-an-archive"
        with self.assertRaises(ValueError):
            switch_archive(self.service, other)
        self.assertFalse((other / "archive.sqlite3").exists())
        self.assertEqual(existing_launch(self.folder), launch)

    def test_switch_and_restore_are_blocked_during_work(self):
        self.service.start()
        self.service.server.operation.acquire()
        try:
            with self.assertRaisesRegex(ValueError, "Finish"):
                switch_archive(self.service, Path(self.temporary.name) / "other")
            with self.assertRaisesRegex(ValueError, "Finish"):
                restore_archive(self.service, "unused.sqlite3", Path(self.temporary.name))
        finally:
            self.service.server.operation.release()
        self.assertEqual(existing_launch(self.folder), self.service.launch)
        self.assertFalse(list(Path(self.temporary.name).glob("MailCairn-restored-*")))

    def test_restore_never_overwrites_an_existing_archive(self):
        backup = self.create_backup()
        other = Path(self.temporary.name) / "existing"
        other.mkdir()
        destination = other / "archive.sqlite3"
        destination.write_bytes(b"existing content")
        with self.assertRaises(ValueError):
            switch_archive(self.service, other, restore_from=backup)
        self.assertEqual(destination.read_bytes(), b"existing content")
        self.assertEqual(existing_launch(self.folder), self.service.launch)

    def test_switching_reused_peer_does_not_stop_its_server(self):
        backup = self.create_backup()
        peer = DesktopService(self.folder)
        peer.start()
        restored = restore_archive(peer, backup, Path(self.temporary.name))
        self.addCleanup(restored.stop)
        self.assertEqual(existing_launch(self.folder), self.service.launch)
        self.assertEqual(restored.server.store.stats()["messages"], 20)


if __name__ == "__main__":
    unittest.main()
