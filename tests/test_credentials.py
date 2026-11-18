"""Synthetic credential protection tests; never use a user's real password."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from mailcairn.credentials import CredentialStore

ACCOUNT = "a" * 24
PASSWORD = "synthetic-app-password-DO-NOT-USE"


class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_memory_only_never_writes_password_and_requires_reentry(self):
        store = CredentialStore(self.folder, persistent=False)
        store.set(ACCOUNT, PASSWORD, remember=True)
        self.assertEqual(store.get(ACCOUNT), PASSWORD)
        self.assertFalse(store.remembered(ACCOUNT))
        self.assertFalse(store.path.exists())
        self.assertIsNone(CredentialStore(self.folder, persistent=False).get(ACCOUNT))

    @unittest.skipUnless(sys.platform == "win32", "Windows DPAPI")
    def test_dpapi_round_trip_does_not_store_plaintext(self):
        store = CredentialStore(self.folder)
        if not store.persistent:
            self.skipTest("Current logon profile cannot use DPAPI; normal-profile coverage is required separately")
        store.set(ACCOUNT, PASSWORD, remember=True)
        contents = store.path.read_text(encoding="utf-8")
        self.assertNotIn(PASSWORD, contents)
        self.assertEqual(set(json.loads(contents)), {"version", "secrets"})
        reopened = CredentialStore(self.folder)
        self.assertEqual(reopened.get(ACCOUNT), PASSWORD)
        self.assertTrue(reopened.remembered(ACCOUNT))

    @unittest.skipUnless(sys.platform == "win32", "Windows DPAPI")
    def test_remember_false_removes_persisted_secret(self):
        store = CredentialStore(self.folder)
        if not store.persistent:
            self.skipTest("Current logon profile cannot use DPAPI; normal-profile coverage is required separately")
        store.set(ACCOUNT, PASSWORD, remember=True)
        store.set(ACCOUNT, "synthetic-session-only", remember=False)
        self.assertEqual(store.get(ACCOUNT), "synthetic-session-only")
        self.assertFalse(store.remembered(ACCOUNT))
        self.assertIsNone(CredentialStore(self.folder).get(ACCOUNT))
        self.assertNotIn("synthetic-session-only", store.path.read_text(encoding="utf-8"))

    def test_delete_only_removes_credentials(self):
        archive = self.folder / "archive.sqlite3"
        archive.write_bytes(b"synthetic archive sentinel")
        store = CredentialStore(self.folder, persistent=False)
        store.set(ACCOUNT, PASSWORD)
        store.delete(ACCOUNT)
        self.assertIsNone(store.get(ACCOUNT))
        self.assertEqual(archive.read_bytes(), b"synthetic archive sentinel")

    @unittest.skipUnless(sys.platform == "win32", "Windows DPAPI")
    def test_corrupt_protected_value_requires_reconnect_without_disclosing_value(self):
        store = CredentialStore(self.folder)
        store.path.write_text(json.dumps({"version": 1, "secrets": {ACCOUNT: "not-encrypted"}}), encoding="utf-8")
        reopened = CredentialStore(self.folder)
        self.assertFalse(reopened.available(ACCOUNT))

    def test_invalid_ids_and_passwords_rejected(self):
        store = CredentialStore(self.folder, persistent=False)
        for account, password in (("../outside", PASSWORD), (ACCOUNT, ""), (ACCOUNT, "a" * 4097)):
            with self.assertRaises(ValueError):
                store.set(account, password)

    def test_unavailable_dpapi_explicitly_uses_memory_only(self):
        with patch("mailcairn.credentials.dpapi_available", return_value=False):
            store = CredentialStore(self.folder)
        self.assertFalse(store.persistent)
        store.set(ACCOUNT, PASSWORD)
        self.assertEqual(store.get(ACCOUNT), PASSWORD)
        self.assertFalse(store.path.exists())


    def test_transaction_restores_unreadable_protected_secret_without_decryption(self):
        store = CredentialStore(self.folder, persistent=True)
        store.path.write_text(json.dumps({"version": 1, "secrets": {ACCOUNT: "opaque-prior-value"}}), encoding="utf-8")
        store = CredentialStore(self.folder, persistent=True)
        before = json.loads(store.path.read_text(encoding="utf-8"))
        with patch("mailcairn.credentials._dpapi", side_effect=AssertionError("Do not decrypt snapshots")):
            with self.assertRaisesRegex(OSError, "synthetic settings failure"):
                with store.transaction():
                    store.set(ACCOUNT, PASSWORD, remember=False)
                    raise OSError("synthetic settings failure")
        self.assertEqual(json.loads(store.path.read_text(encoding="utf-8")), before)
        self.assertNotIn(ACCOUNT, store._memory)
        self.assertTrue(store.remembered(ACCOUNT))

    def test_failed_credential_write_preserves_existing_disk_and_memory(self):
        store = CredentialStore(self.folder, persistent=True)
        with patch("mailcairn.credentials._dpapi", return_value=b"synthetic-protected"):
            store.set(ACCOUNT, PASSWORD)
        before = store.path.read_bytes()
        with patch("mailcairn.credentials.atomic_json", side_effect=OSError("synthetic write failure")):
            with self.assertRaises(OSError):
                with store.transaction():
                    store.set(ACCOUNT, "synthetic-new-session-password", remember=False)
        self.assertEqual(store.path.read_bytes(), before)
        self.assertEqual(store.get(ACCOUNT), PASSWORD)
        self.assertTrue(store.remembered(ACCOUNT))


if __name__ == "__main__":
    unittest.main()
