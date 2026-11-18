"""Incremental ingestion and protocol restrictions with synthetic IMAP mail."""
import imaplib
import json
from pathlib import Path
import ssl
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

from mailcairn.credentials import CredentialError, CredentialRollbackError, CredentialStore
from mailcairn.imap_client import ERRORS, IMAPClient, SyncError, _BoundedRead
from mailcairn.store import Store
from mailcairn.sync import SYNC_FILE, SyncManager, validate_config
from tests.helpers import message

PASSWORD = "synthetic-password-must-not-appear"


class Mailbox:
    def __init__(self):
        self.messages = {1: message("One", body="Synthetic one", crlf=True)}
        self.validity = 1
        self.fail_uid = None
        self.clients = []
        self.entered = threading.Event()
        self.block = False
        self.released = threading.Event()

    def factory(self, account, password, on_pin, max_message):
        mailbox = self

        class Client:
            def __init__(self):
                self.closed = False
                self.calls = []

            def connect(self):
                mailbox.entered.set()
                if mailbox.block:
                    mailbox.released.wait(3)

            def select(self, folder):
                self.calls.append(("select", folder))
                return mailbox.validity, max(mailbox.messages, default=0) + 1

            def search(self, low, high):
                self.calls.append(("search", low, high))
                return [uid for uid in mailbox.messages if low <= uid <= high]

            def fetch(self, uid):
                self.calls.append(("fetch", uid))
                if uid == mailbox.fail_uid:
                    raise RuntimeError(PASSWORD)
                return mailbox.messages.get(uid)

            def abort(self):
                mailbox.released.set()

            def close(self):
                self.closed = True

        client = Client()
        self.clients.append(client)
        return client


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.store = Store(self.folder / "archive.sqlite3")
        self.operation = threading.Lock()
        self.mailbox = Mailbox()
        self.credentials = CredentialStore(self.folder, persistent=False)
        self.manager = SyncManager(self.store, self.operation, credential_store=self.credentials,
                                   client_factory=self.mailbox.factory, interval=.1)
        self.addCleanup(self.manager.stop)
        self.config = {"provider": "proton", "username": "synthetic-user", "password": PASSWORD, "remember": False}
        self.account = self.manager.add(self.config)

    def state(self):
        return self.manager.status()["accounts"][0]

    def cycle(self):
        self.manager._cycle(self.account["id"])

    def test_incremental_new_uid_archives_exact_bytes_without_reimport(self):
        self.cycle()
        original = self.mailbox.messages[1]
        self.assertEqual(self.store.message(1, raw=True)["raw"], original)
        self.mailbox.messages[2] = message("Two", body="Synthetic two")
        self.cycle()
        self.assertEqual(self.store.stats()["messages"], 2)
        self.assertEqual(self.state()["last_uid"], 2)
        self.assertEqual(self.state()["last_added"], 1)
        self.assertEqual([call for call in self.mailbox.clients[-1].calls if call[0] == "fetch"], [("fetch", 2)])
        self.assertEqual(self.store.verify()["receipts"], "ok")

    def test_same_bytes_new_uid_count_as_duplicate(self):
        self.cycle()
        self.mailbox.messages[2] = self.mailbox.messages[1]
        self.cycle()
        self.assertEqual(self.store.stats()["messages"], 1)
        self.assertEqual(self.state()["last_duplicates"], 1)
        self.assertEqual(self.state()["added"], 1)
        self.assertEqual(self.state()["last_uid"], 2)

    def test_uidvalidity_reset_rescans_without_losing_new_lower_uid(self):
        self.mailbox.messages = {90: message("Old", body="Old synthetic")}
        self.cycle()
        self.mailbox.validity = 2
        self.mailbox.messages = {1: message("New", body="New synthetic")}
        self.cycle()
        self.assertEqual(self.state()["uidvalidity"], 2)
        self.assertEqual(self.state()["last_uid"], 1)
        self.assertEqual(self.store.stats()["messages"], 2)

    def test_failed_message_keeps_cursor_before_failure_and_errors_are_redacted(self):
        self.mailbox.messages[2] = message("Two")
        self.mailbox.fail_uid = 2
        self.cycle()
        self.assertEqual(self.state()["last_uid"], 1)
        self.assertEqual(self.store.stats()["messages"], 1)
        self.assertEqual(self.state()["status"], "error")
        self.assertNotIn(PASSWORD, json.dumps(self.manager.status()))
        self.assertNotIn(PASSWORD, (self.folder / SYNC_FILE).read_text(encoding="utf-8"))
        self.mailbox.fail_uid = None
        self.cycle()
        self.assertEqual(self.state()["last_uid"], 2)
        self.assertEqual(self.store.stats()["messages"], 2)

    def test_oversized_or_unparseable_message_never_advances_cursor(self):
        for raw in (b"x" * 101, b"not email"):
            with self.subTest(size=len(raw)):
                self.manager.max_message = 100
                self.mailbox.messages = {1: raw}
                self.cycle()
                self.assertEqual(self.state()["last_uid"], 0)
                self.assertEqual(self.store.stats()["messages"], 0)
                self.assertEqual(self.state()["status"], "error")

    def test_cursor_persistence_failure_retries_as_duplicate(self):
        original = self.manager._persist

        def fail_cursor():
            if self.manager._accounts[self.account["id"]]["last_uid"]:
                raise SyncError("settings")
            original()

        with patch.object(self.manager, "_persist", side_effect=fail_cursor):
            self.cycle()
        self.assertEqual(self.store.stats()["messages"], 1)
        self.assertEqual(self.state()["last_uid"], 0)
        self.cycle()
        self.assertEqual(self.store.stats()["messages"], 1)
        self.assertEqual(self.state()["last_duplicates"], 1)
        self.assertEqual(self.state()["last_uid"], 1)

    def test_reconnect_keeps_id_and_cursor_and_copies_input(self):
        self.cycle()
        config = dict(self.config, password="synthetic-new-password")
        account = self.manager.add(config)
        config.clear()
        self.assertEqual(account["id"], self.account["id"])
        self.assertEqual(account["last_uid"], 1)
        self.assertEqual(self.credentials.get(account["id"]), "synthetic-new-password")
        self.assertNotIn("password", json.dumps(self.manager.status()).lower())

    def test_incomplete_body_response_keeps_cursor_and_retries_message(self):
        broken = TransportTests().connection(self.mailbox.messages[1])
        original_uid = broken.uid
        def incomplete(command, *args):
            if command == "FETCH" and "BODY.PEEK" in args[-1]:
                return "OK", [b"1 (UID 1 BODY[]<0>)"]
            return original_uid(command, *args)
        broken.uid = incomplete
        working = TransportTests().connection(self.mailbox.messages[1])
        self.manager.client_factory = IMAPClient
        with patch("mailcairn.imap_client._IMAP", side_effect=[broken, working]):
            self.cycle()
            self.assertEqual(self.state()["status"], "error")
            self.assertEqual(self.state()["last_uid"], 0)
            self.assertEqual(self.store.stats()["messages"], 0)
            self.cycle()
        self.assertEqual(self.state()["last_uid"], 1)
        self.assertEqual(self.store.message(1, raw=True)["raw"], self.mailbox.messages[1])

    def test_memory_only_restart_requires_credentials_but_keeps_cursor(self):
        self.cycle()
        reopened = SyncManager(self.store, self.operation, credential_store=CredentialStore(self.folder, persistent=False))
        self.addCleanup(reopened.stop)
        state = reopened.status()["accounts"][0]
        self.assertEqual(state["last_uid"], 1)
        self.assertEqual(state["status"], "auth_required")

    def test_restart_queues_partial_failed_sync_with_remembered_credentials(self):
        # Exercise persisted credentials using only a synthetic protection stub.
        remembered = CredentialStore(self.folder, persistent=True)
        self.manager.credentials = remembered
        with patch("mailcairn.credentials._dpapi", return_value=b"synthetic-protected-secret"):
            self.manager.add({**self.config, "remember": True})
        self.cycle()
        last_success = self.state()["last_sync"]
        self.mailbox.messages[2] = message("Partial progress")
        self.mailbox.messages[3] = message("Retry after restart")
        self.mailbox.fail_uid = 3
        self.cycle()
        self.assertEqual(self.state()["status"], "error")
        self.assertEqual(self.state()["last_uid"], 2)
        self.assertEqual(self.state()["last_added"], 1)
        self.assertEqual(self.store.stats()["messages"], 2)
        self.manager.stop()

        restored_credentials = CredentialStore(self.folder, persistent=True)
        reopened = SyncManager(self.store, self.operation, credential_store=restored_credentials,
                               client_factory=self.mailbox.factory)
        self.addCleanup(reopened.stop)
        with patch("mailcairn.credentials._dpapi", return_value=PASSWORD.encode()):
            state = reopened.status()["accounts"][0]
        self.assertTrue(state["credentials_persistent"])
        self.assertTrue(state["credentials_available"])
        self.assertEqual(state["status"], "queued")
        self.assertEqual(state["last_uid"], 2)
        self.assertEqual(state["last_added"], 1)
        self.assertEqual(state["last_sync"], last_success)

        self.mailbox.fail_uid = None
        reopened._cycle(self.account["id"])
        self.assertEqual(reopened.status()["accounts"][0]["status"], "idle")
        self.assertEqual(self.store.stats()["messages"], 3)
        self.assertEqual([call for call in self.mailbox.clients[-1].calls if call[0] == "fetch"],
                         [("fetch", 3)])
        self.assertFalse(self.operation.locked())

        reopened.pause(self.account["id"])
        paused = SyncManager(self.store, self.operation, credential_store=restored_credentials)
        self.addCleanup(paused.stop)
        self.assertEqual(paused.status()["accounts"][0]["status"], "paused")

    def test_shared_operation_lock_defers_without_network(self):
        self.operation.acquire()
        try:
            self.cycle()
            self.assertEqual(self.state()["status"], "waiting")
            self.assertFalse(self.mailbox.clients)
        finally:
            self.operation.release()

    def test_pause_resume_remove_preserve_archived_messages(self):
        self.cycle()
        self.manager.pause(self.account["id"])
        self.assertEqual(self.state()["status"], "paused")
        self.manager.resume(self.account["id"])
        self.assertEqual(self.state()["status"], "queued")
        self.manager.remove(self.account["id"])
        self.assertEqual(self.manager.status()["accounts"], [])
        self.assertIsNone(self.credentials.get(self.account["id"]))
        self.assertEqual(self.store.stats()["messages"], 1)

    def test_failed_disconnect_settings_save_keeps_account_and_password(self):
        account_id = self.account["id"]
        with patch.object(self.manager, "_persist", side_effect=OSError("synthetic write failure")), patch.object(self.credentials, "delete") as delete:
            with self.assertRaises(OSError):
                self.manager.remove(account_id)
        delete.assert_not_called()
        self.assertEqual(self.state()["id"], account_id)
        self.assertEqual(self.credentials.get(account_id), PASSWORD)
        saved = json.loads((self.folder / SYNC_FILE).read_text(encoding="utf-8"))
        self.assertEqual(saved["accounts"][0]["id"], account_id)

    def test_disconnect_cleanup_failure_reports_committed_state_without_restoring_account(self):
        account_id = self.account["id"]
        for after_delete in (False, True):
            with self.subTest(after_delete=after_delete):
                if after_delete:
                    self.account = self.manager.add(self.config)
                    account_id = self.account["id"]
                original = self.credentials.delete
                def fail_cleanup(key):
                    if after_delete:
                        original(key)
                    raise OSError(PASSWORD)
                client = Mock()
                self.manager._active, self.manager._client = account_id, client
                with patch.object(self.credentials, "delete", side_effect=fail_cleanup):
                    result = self.manager.remove(account_id)
                self.assertTrue(result["removed"])
                self.assertIn("local cleanup failed", result["warning"])
                self.assertNotIn(PASSWORD, json.dumps(result))
                self.assertEqual(self.manager.status()["accounts"], [])
                saved = json.loads((self.folder / SYNC_FILE).read_text(encoding="utf-8"))
                self.assertEqual(saved["accounts"], [])
                self.assertEqual(self.credentials.get(account_id), None if after_delete else PASSWORD)
                client.abort.assert_called_once()

    def test_bounded_batch_and_uid_search_window(self):
        self.mailbox.messages = {uid: message(f"Synthetic {uid}") for uid in range(1, 106)}
        self.cycle()
        self.assertEqual(self.state()["last_uid"], 100)
        self.assertEqual(self.state()["status"], "queued")
        self.assertEqual(self.store.stats()["messages"], 100)
        self.cycle()
        self.assertEqual(self.store.stats()["messages"], 105)
        self.assertEqual(self.state()["last_uid"], 105)
        self.assertTrue(all(call[2] - call[1] < 1000 for client in self.mailbox.clients
                            for call in client.calls if call[0] == "search"))

    def test_scheduler_imports_then_stop_interrupts_active_client_and_releases_lock(self):
        self.mailbox.block = True
        self.manager.start()
        self.assertTrue(self.mailbox.entered.wait(2))
        stopped = [threading.Thread(target=self.manager.stop) for _ in range(2)]
        for thread in stopped:
            thread.start()
        for thread in stopped:
            thread.join(2)
            self.assertFalse(thread.is_alive())
        self.assertFalse(self.operation.locked())
        self.assertTrue(self.mailbox.clients[0].closed)
        self.assertEqual(self.store.stats()["messages"], 0)

    def test_scheduler_discovers_new_mail_without_another_manual_request(self):
        self.manager.start()
        deadline = time.monotonic() + 3
        while self.store.stats()["messages"] < 1 and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertEqual(self.store.stats()["messages"], 1)
        self.mailbox.messages[2] = message("Arrived later", body="Another synthetic message")
        deadline = time.monotonic() + 3
        while self.store.stats()["messages"] < 2 and time.monotonic() < deadline:
            time.sleep(.01)
        self.manager.stop()
        self.assertEqual(self.store.stats()["messages"], 2)
        self.assertFalse(self.operation.locked())

    def test_scheduler_recovers_after_ssl_eof_without_manual_request(self):
        self.cycle()
        previous = self.state()
        self.mailbox.messages[2] = message("Arrived during outage", body="Synthetic recovery")
        original_factory = self.manager.client_factory
        attempts = []

        def factory(*args):
            client = original_factory(*args)
            attempts.append(client)
            if len(attempts) == 1:
                def fail():
                    raise ssl.SSLEOFError(8, PASSWORD)
                client.connect = fail
            return client

        failed = threading.Event()
        recovered = threading.Event()
        observation = {}
        original_cycle = self.manager._cycle

        def observe_cycle(account_id):
            original_cycle(account_id)
            if not failed.is_set():
                observation.update(state=self.state(), messages=self.store.stats()["messages"],
                                   locked=self.operation.locked(), closed=attempts[0].closed)
                failed.set()
            elif self.state()["last_uid"] == 2:
                recovered.set()

        self.manager.client_factory = factory
        self.manager._cycle = observe_cycle
        # Both attempts are due polls, with no queued/manual sync request.
        self.manager._requested.clear()
        self.manager._next_due[self.account["id"]] = 0
        self.manager.start()
        try:
            self.assertTrue(failed.wait(3), "The scheduled failure did not finish")
            self.assertTrue(recovered.wait(3), "The scheduler did not recover automatically")
        finally:
            self.manager.stop()
        self.assertEqual(observation["state"]["status"], "error")
        self.assertEqual(observation["state"]["last_error"], ERRORS["network"])
        self.assertEqual(observation["state"]["last_uid"], previous["last_uid"])
        self.assertEqual(observation["state"]["last_sync"], previous["last_sync"])
        self.assertEqual(observation["messages"], 1)
        self.assertFalse(observation["locked"])
        self.assertTrue(observation["closed"])
        self.assertEqual(self.store.stats()["messages"], 2)
        self.assertEqual(self.state()["last_uid"], 2)
        self.assertEqual(self.state()["added"], 2)
        self.assertEqual(self.state()["last_error"], "")
        self.assertEqual([call for client in attempts for call in client.calls
                          if call[0] == "fetch"], [("fetch", 2)])
        self.assertTrue(all(client.closed for client in attempts))
        self.assertFalse(self.operation.locked())

    def test_certificate_verification_error_reaches_sync_status_without_credentials(self):
        account = self.manager.add({"provider": "gmail", "username": "synthetic@example.invalid",
                                    "password": PASSWORD, "remember": False})
        self.manager.client_factory = IMAPClient
        with patch("mailcairn.imap_client._IMAPSSL", side_effect=ssl.SSLCertVerificationError(PASSWORD)):
            self.manager._cycle(account["id"])
        status = next(item for item in self.manager.status()["accounts"] if item["id"] == account["id"])
        self.assertEqual(status["status"], "error")
        self.assertEqual(status["last_error"], ERRORS["tls_certificate"])
        self.assertEqual(status["last_uid"], 0)
        self.assertNotIn(PASSWORD, json.dumps(status))
        self.assertFalse(self.operation.locked())
        self.manager.client_factory = self.mailbox.factory
        self.manager._cycle(account["id"])
        recovered = next(item for item in self.manager.status()["accounts"] if item["id"] == account["id"])
        self.assertEqual(recovered["status"], "idle")
        self.assertEqual(recovered["last_error"], "")
        self.assertEqual(recovered["last_uid"], 1)
        self.assertEqual(self.store.stats()["messages"], 1)

    def test_uid_range_quirk_cannot_fetch_already_processed_uid(self):
        self.cycle()
        self.mailbox.messages[2] = message("New UID")
        original = self.manager.client_factory
        def factory(*args):
            client = original(*args)
            client.search = lambda low, high: [1, 2, 999999]
            return client
        self.manager.client_factory = factory
        self.cycle()
        self.assertEqual([call for call in self.mailbox.clients[-1].calls if call[0] == "fetch"], [("fetch", 2)])

    def test_corrupt_settings_fail_closed_without_overwrite(self):
        path = self.folder / SYNC_FILE
        path.write_text("[]", encoding="utf-8")
        broken = SyncManager(self.store, self.operation, credential_store=self.credentials)
        self.addCleanup(broken.stop)
        with self.assertRaises(ValueError):
            broken.add(self.config)
        self.assertEqual(path.read_text(encoding="utf-8"), "[]")

    def test_malformed_persisted_account_state_never_starts_network(self):
        path = self.folder / SYNC_FILE
        valid = json.loads(path.read_text(encoding="utf-8"))
        duplicate = {"version": 1, "accounts": valid["accounts"] * 2}
        invalid_pause = json.loads(json.dumps(valid))
        invalid_pause["accounts"][0]["paused"] = "false"
        for contents in (json.dumps(duplicate), json.dumps(invalid_pause), "[" * 2000 + "]" * 2000):
            with self.subTest(kind=contents[:30]):
                path.write_text(contents, encoding="utf-8")
                manager = SyncManager(self.store, self.operation, credential_store=self.credentials)
                self.addCleanup(manager.stop)
                self.assertTrue(manager.status()["settings_error"])
                self.assertEqual(manager.status()["accounts"], [])
                self.assertIsNone(manager._thread)

    def test_settings_validation_rejects_unknown_insecure_or_injected_values(self):
        for fields in ({"tls": "none"}, {"host": "remote.invalid"}, {"port": True},
                       {"username": "user\r\nLOGOUT"}, {"password": "secret\nSTORE"}):
            with self.subTest(fields=list(fields)):
                with self.assertRaises(ValueError):
                    validate_config({**self.config, **fields})


    def test_failed_reconnect_restores_credentials_and_settings_in_both_modes(self):
        for original_remember in (True, False):
            with self.subTest(original_remember=original_remember):
                self.manager.credentials = CredentialStore(self.folder, persistent=True)
                credentials = self.manager.credentials
                with patch("mailcairn.credentials._dpapi", side_effect=lambda data, decrypt=False: data):
                    self.manager.add({**self.config, "remember": original_remember})
                    before_settings = self.manager.path.read_bytes()
                    before_state = self.state()
                    with patch.object(self.manager, "_persist", side_effect=SyncError("settings")):
                        with self.assertRaises(SyncError):
                            self.manager.add({**self.config, "password": "synthetic-replacement",
                                              "remember": not original_remember})
                    self.assertEqual(self.manager.path.read_bytes(), before_settings)
                    self.assertEqual(self.state(), before_state)
                    self.assertEqual(credentials.get(self.account["id"]), PASSWORD)
                    reopened = CredentialStore(self.folder, persistent=True)
                    self.assertEqual(reopened.get(self.account["id"]), PASSWORD if original_remember else None)
                    self.assertEqual(credentials.remembered(self.account["id"]), original_remember)
                self.cycle()
                self.assertEqual(self.state()["status"], "idle")

    def test_failed_credential_rollback_requires_explicit_reconnect(self):
        import mailcairn.credentials as credential_module
        self.manager.credentials = CredentialStore(self.folder, persistent=True)
        credentials = self.manager.credentials
        with patch("mailcairn.credentials._dpapi", side_effect=lambda data, decrypt=False: data):
            self.manager.add({**self.config, "remember": True})
            before_settings = self.manager.path.read_bytes()
            original_atomic = credential_module.atomic_json
            writes = []

            def fail_rollback(path, value):
                writes.append(True)
                if len(writes) == 2:
                    raise OSError(PASSWORD)
                return original_atomic(path, value)

            with patch.object(self.manager, "_persist", side_effect=SyncError("settings")), patch.object(credential_module, "atomic_json", side_effect=fail_rollback):
                with self.assertRaises(CredentialRollbackError) as failed:
                    self.manager.add({**self.config, "password": "synthetic-replacement", "remember": False})
            self.assertNotIn(PASSWORD, str(failed.exception))
            self.assertEqual(self.manager.path.read_bytes(), before_settings)
            self.assertEqual(credentials.get(self.account["id"]), PASSWORD)
            self.assertFalse(credentials.remembered(self.account["id"]))
            self.assertIsNone(CredentialStore(self.folder, persistent=True).get(self.account["id"]))
            for action in (self.manager.pause, self.manager.resume):
                action(self.account["id"])
                self.assertEqual(self.state()["status"], "auth_required")
                self.assertIn("Reconnect this account before restarting", self.state()["last_error"])
            with self.assertRaises(CredentialRollbackError):
                self.manager.sync_now(self.account["id"])
            self.cycle()
            self.assertFalse(self.mailbox.clients)
            self.assertNotIn(PASSWORD, json.dumps(self.manager.status()))
            self.manager.start()
            self.assertFalse(self.mailbox.entered.wait(.2), "Background scheduling must wait for reconnect")
            self.manager.stop()
            self.manager.add({**self.config, "remember": True})
            self.assertEqual(self.state()["status"], "queued")
            self.manager._stop.clear()
            self.cycle()
            self.assertEqual(self.state()["status"], "idle")
            self.assertEqual(self.store.stats()["messages"], 1)

    def test_failed_new_account_rollback_discloses_possible_saved_password(self):
        import mailcairn.credentials as credential_module
        self.manager.credentials = CredentialStore(self.folder, persistent=True)
        before_settings = self.manager.path.read_bytes()
        original_atomic = credential_module.atomic_json
        writes = []

        def fail_rollback(path, value):
            writes.append(True)
            if len(writes) == 2:
                raise OSError(PASSWORD)
            return original_atomic(path, value)

        with patch("mailcairn.credentials._dpapi", return_value=b"synthetic-protected"), patch.object(self.manager, "_persist", side_effect=SyncError("settings")), patch.object(credential_module, "atomic_json", side_effect=fail_rollback):
            with self.assertRaises(CredentialError) as failed:
                self.manager.add({**self.config, "username": "synthetic-second-user", "remember": True})
        self.assertIn("connection was not added", str(failed.exception))
        self.assertIn("saved password may remain", str(failed.exception))
        self.assertNotIn(PASSWORD, str(failed.exception))
        self.assertEqual(self.manager.path.read_bytes(), before_settings)
        self.assertEqual(len(self.manager.status()["accounts"]), 1)
        self.assertEqual(len(json.loads(self.manager.credentials.path.read_text())["secrets"]), 1)


class TransportTests(unittest.TestCase):
    def connection(self, raw=b"Subject: synthetic\r\n\r\nbody"):
        class Connection:
            def __init__(self):
                self.calls = []
                self.sock = self
                self.debug = 0
            def starttls(self, ssl_context):
                self.calls.append("STARTTLS")
                return "OK", []
            def getpeercert(self, binary_form):
                return b"synthetic certificate"
            def login(self, username, password):
                self.calls.append("LOGIN")
                return "OK", []
            def select(self, folder, readonly):
                self.calls.append(("EXAMINE", folder, readonly))
                return "OK", [b"1"]
            def response(self, field):
                return field, [b"1" if field == "UIDVALIDITY" else b"2"]
            def uid(self, command, *args):
                self.calls.append((command, args))
                if command == "SEARCH":
                    return "OK", [b"1"]
                if "RFC822.SIZE" in args[-1]:
                    return "OK", [f"1 (UID 1 RFC822.SIZE {len(raw)})".encode()]
                return "OK", [(b"1 (UID 1 BODY[]<0> {" + str(len(raw)).encode() + b"}", raw), b")"]
            def logout(self):
                self.calls.append("LOGOUT")
            def shutdown(self, *args):
                self.calls.append("shutdown")
        return Connection()

    def test_tls_verified_remote_readonly_peek_and_no_mutating_commands(self):
        connection = self.connection()
        account = {"provider": "imap", "host": "example.invalid", "port": 993, "username": "synthetic"}
        with patch("mailcairn.imap_client._IMAPSSL", return_value=connection) as factory:
            client = IMAPClient(account, PASSWORD, lambda pin: None, 1024)
            client.connect()
            context = factory.call_args.kwargs["ssl_context"]
            self.assertEqual(factory.call_args.kwargs["timeout"], 20)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)
            self.assertEqual(client.select("INBOX"), (1, 2))
            self.assertEqual(client.search(1, 1), [1])
            self.assertIn(b"Subject: synthetic", client.fetch(1))
            client.close()
        self.assertIn(("EXAMINE", '"INBOX"', True), connection.calls)
        commands = repr(connection.calls)
        self.assertIn("BODY.PEEK[]", commands)
        for forbidden in ("STORE", "EXPUNGE", "APPEND", "CLOSE"):
            self.assertNotIn(forbidden, commands)

    def test_missing_body_literal_is_only_an_expunge_when_response_is_empty(self):
        for response, expunged in (([None], True), ([b""], True),
                                   ([b"1 (UID 1 BODY[]<0>)"], False), ([b")"], False)):
            with self.subTest(response=response):
                connection = self.connection()
                original_uid = connection.uid
                def fetch(command, *args):
                    if command == "FETCH" and "BODY.PEEK" in args[-1]:
                        return "OK", response
                    return original_uid(command, *args)
                connection.uid = fetch
                client = IMAPClient({"provider": "imap", "host": "example.invalid", "port": 993,
                                     "username": "synthetic"}, PASSWORD, lambda pin: None, 1024)
                client.connection = connection
                if expunged:
                    self.assertIsNone(client.fetch(1))
                else:
                    with self.assertRaises(SyncError) as raised:
                        client.fetch(1)
                    self.assertEqual(raised.exception.code, "protocol")

    def test_bridge_pin_is_recorded_before_auth_and_change_blocks_login(self):
        account = {"provider": "proton", "host": "127.0.0.1", "port": 1143, "username": "synthetic"}
        connection = self.connection()
        pins = []
        def pin(value):
            self.assertNotIn("LOGIN", connection.calls)
            pins.append(value)
        with patch("mailcairn.imap_client._IMAP", return_value=connection) as factory:
            client = IMAPClient(account, PASSWORD, pin, 1024)
            client.connect()
            self.assertEqual(factory.call_args.kwargs["timeout"], 20)
        self.assertEqual(len(pins[0]), 64)
        changed = self.connection()
        with patch("mailcairn.imap_client._IMAP", return_value=changed):
            with self.assertRaisesRegex(SyncError, "certificate changed"):
                IMAPClient({**account, "certificate_pin": "0" * 64}, PASSWORD, pin, 1024).connect()
        self.assertNotIn("LOGIN", changed.calls)

    def test_login_failure_classification_redaction_and_cleanup(self):
        cases = ((imaplib.IMAP4.abort(PASSWORD), "network"),
                 (imaplib.IMAP4.error(PASSWORD), "auth"),
                 (None, "auth"))
        for failure, expected in cases:
            with self.subTest(failure=type(failure).__name__):
                connection = self.connection()
                def login(*args):
                    if failure is not None:
                        raise failure
                    return "NO", [PASSWORD.encode()]
                connection.login = login
                if isinstance(failure, imaplib.IMAP4.abort):
                    def logout():
                        connection.calls.append("LOGOUT")
                        raise imaplib.IMAP4.abort(PASSWORD)
                    connection.logout = logout
                client = IMAPClient({"provider": "gmail", "host": "imap.gmail.com", "port": 993,
                                     "username": "synthetic"}, PASSWORD, lambda pin: None, 1024)
                with patch("mailcairn.imap_client._IMAPSSL", return_value=connection):
                    try:
                        with self.assertRaises(SyncError) as raised:
                            client.connect()
                    finally:
                        client.close()
                self.assertEqual(raised.exception.code, expected)
                self.assertEqual(str(raised.exception), ERRORS[expected])
                self.assertNotIn(PASSWORD, str(raised.exception))
                self.assertIsNone(client.password)
                self.assertIn("LOGOUT", connection.calls)
                if isinstance(failure, imaplib.IMAP4.abort):
                    self.assertIn("shutdown", connection.calls)

    def test_tls_certificate_verification_failure_is_distinct_and_redacted(self):
        client = IMAPClient({"provider": "gmail", "host": "imap.gmail.com", "port": 993,
                             "username": "synthetic"}, PASSWORD, lambda pin: None, 1024)
        with patch("mailcairn.imap_client._IMAPSSL", side_effect=ssl.SSLCertVerificationError(PASSWORD)):
            with self.assertRaises(SyncError) as raised:
                client.connect()
        self.assertEqual(raised.exception.code, "tls_certificate")
        self.assertEqual(str(raised.exception), ERRORS["tls_certificate"])
        self.assertNotIn(PASSWORD, str(raised.exception))
        self.assertIsNone(client.password)

    def test_oversized_literal_rejected_before_allocation(self):
        class Reader(_BoundedRead):
            max_literal = 10
        with self.assertRaisesRegex(SyncError, "size limit"):
            Reader().read(11)

    def test_cancelled_connection_never_sends_credentials(self):
        account = {"provider": "imap", "host": "example.invalid", "port": 993, "username": "synthetic"}
        connection = self.connection()
        client = IMAPClient(account, PASSWORD, lambda pin: None, 1024)
        with patch("mailcairn.imap_client._IMAPSSL", side_effect=lambda *a, **k: (client.abort(), connection)[1]):
            with self.assertRaises(SyncError):
                client.connect()
        self.assertNotIn("LOGIN", connection.calls)


if __name__ == "__main__":
    unittest.main()
