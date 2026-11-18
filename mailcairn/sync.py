"""One-way, incremental IMAP ingestion under the archive's writer lock."""
from __future__ import annotations

from datetime import datetime, timezone
import imaplib
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
import time

from .credentials import ACCOUNT_ID, CredentialError, CredentialRollbackError, CredentialStore, atomic_json
from .imap_client import ERRORS, IMAPClient, SyncError

SYNC_FILE = ".mailcairn-sync.json"
BATCH_MESSAGES = 100
UID_WINDOW = 1000
MAX_ACCOUNTS = 3
CONFIG_KEYS = {"provider", "username", "password", "host", "port", "folder", "remember"}
PUBLIC_KEYS = ("id", "provider", "username", "host", "port", "folder", "paused", "status",
               "last_sync", "last_error", "added", "last_added", "last_duplicates",
               "last_receipt_id", "uidvalidity", "last_uid")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_config(config):
    if not isinstance(config, dict) or set(config) - CONFIG_KEYS:
        raise ValueError("Unsupported connection setting.")
    provider = config.get("provider")
    if provider not in ("gmail", "proton", "imap"):
        raise ValueError("Choose Gmail, Proton Bridge or IMAP.")
    username = config.get("username")
    password = config.get("password")
    folder = config.get("folder", "INBOX")
    if not isinstance(username, str) or not 1 <= len(username.strip()) <= 320 or re.search(r"[\x00-\x1f\x7f]", username):
        raise ValueError("Enter a valid IMAP username.")
    if not isinstance(password, str) or not 1 <= len(password) <= 4096 or re.search(r"[\x00\r\n]", password):
        raise ValueError("Enter an app password or Bridge password.")
    if not isinstance(folder, str) or not 1 <= len(folder) <= 200 or re.search(r"[^\x20-\x7e]", folder):
        raise ValueError("Enter an ASCII IMAP folder name, such as INBOX.")
    fixed_host = {"gmail": "imap.gmail.com", "proton": "127.0.0.1"}.get(provider)
    host = config.get("host", fixed_host)
    if not isinstance(host, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9.-]{0,252}", host):
        raise ValueError("Enter an IMAP server hostname without a URL or path.")
    host = host.lower()
    if fixed_host and host != fixed_host:
        raise ValueError("This provider requires its preset server address.")
    port = config.get("port", 1143 if provider == "proton" else 993)
    if type(port) is not int or not 1 <= port <= 65535 or (provider == "gmail" and port != 993):
        raise ValueError("Enter a valid IMAP port; Gmail requires port 993.")
    remember = config.get("remember", True)
    if type(remember) is not bool:
        raise ValueError("Remember password must be true or false.")
    return {"provider": provider, "username": username.strip(), "host": host, "port": port,
            "folder": folder, "remember": remember}, password.replace(" ", "") if provider == "gmail" else password


class SyncManager:
    def __init__(self, store, operation_lock, max_message=32 * 1024 * 1024,
                 credential_store=None, client_factory=None, interval=300):
        self.store = store
        self.operation = operation_lock
        self.max_message = max_message
        self.folder = Path(store.path).parent
        self.path = self.folder / SYNC_FILE
        self.credentials = credential_store or CredentialStore(self.folder)
        self.client_factory = client_factory or IMAPClient
        self.interval = max(.05, float(interval))
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = None
        self._active = None
        self._client = None
        self._accounts = {}
        self._requested = set()
        self._credential_errors = {}
        self._next_due = {}
        self._load_error = False
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            if self.path.is_symlink() or self.path.stat().st_size > 100_000:
                raise ValueError
            state = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(state, dict) or state.get("version") != 1 or not isinstance(state.get("accounts"), list) or len(state["accounts"]) > MAX_ACCOUNTS:
                raise ValueError
            accounts = {}
            for saved in state["accounts"]:
                if not isinstance(saved, dict) or not ACCOUNT_ID.fullmatch(saved.get("id", "")):
                    raise ValueError
                if saved["id"] in accounts or type(saved.get("paused", False)) is not bool:
                    raise ValueError
                # Validate persisted endpoint data as strictly as API input.
                config = {key: saved[key] for key in ("provider", "username", "host", "port", "folder", "remember")}
                clean, _ = validate_config({**config, "password": "validation-only"})
                account = self._new_account(saved["id"], clean)
                for key in ("last_uid", "uidvalidity", "added", "last_added", "last_duplicates", "last_receipt_id"):
                    value = saved.get(key, 0)
                    if type(value) is not int or value < 0 or (key in ("last_uid", "uidvalidity") and value > 4_294_967_295):
                        raise ValueError
                    account[key] = value
                account["paused"] = saved.get("paused") is True
                last_sync = saved.get("last_sync", "")
                account["last_sync"] = last_sync if isinstance(last_sync, str) and len(last_sync) <= 40 else ""
                pin = saved.get("certificate_pin", "")
                if not isinstance(pin, str) or (pin and not re.fullmatch(r"[a-f0-9]{64}", pin)):
                    raise ValueError
                account["certificate_pin"] = pin
                # Saved counters may describe an interrupted partial cycle.
                # Only a new completed poll can establish an idle/success state.
                account["status"] = "paused" if account["paused"] else "queued"
                accounts[account["id"]] = account
            self._accounts = accounts
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            self._load_error = True

    @staticmethod
    def _new_account(account_id, clean):
        return {**clean, "id": account_id, "paused": False, "status": "queued", "last_sync": "",
                "last_error": "", "added": 0, "last_added": 0, "last_duplicates": 0,
                "last_receipt_id": 0, "uidvalidity": 0, "last_uid": 0, "certificate_pin": ""}

    def _persist(self):
        try:
            atomic_json(self.path, {"version": 1, "accounts": list(self._accounts.values())})
        except OSError:
            raise SyncError("settings") from None

    def _public(self, account):
        result = {key: account[key] for key in PUBLIC_KEYS}
        result["credentials_persistent"] = self.credentials.remembered(account["id"])
        result["credentials_available"] = self.credentials.available(account["id"])
        if not result["credentials_available"] and not account["paused"]:
            result["status"] = "auth_required"
            result["last_error"] = ERRORS["credentials"]
        if account["id"] in self._credential_errors:
            result["status"] = "auth_required"
            result["last_error"] = self._credential_errors[account["id"]]
        return result

    def status(self):
        with self._lock:
            return {"accounts": [self._public(account) for account in self._accounts.values()],
                    "credentials_persistent": self.credentials.persistent,
                    "settings_error": ERRORS["settings"] if self._load_error else "",
                    "interval_seconds": self.interval}

    def add(self, config):
        clean, password = validate_config(config)
        with self._lock:
            if self._load_error:
                raise ValueError("Connection settings could not be loaded. Keep the state file and restore it before adding accounts.")
            keys = ("provider", "host", "port", "username", "folder")
            match = next((account for account in self._accounts.values()
                          if all(account[key] == clean[key] for key in keys)), None)
            if match is None and len(self._accounts) >= MAX_ACCOUNTS:
                raise ValueError("Up to three connections are supported. Remove a connection before adding another.")
            account_id = match["id"] if match else secrets.token_hex(12)
            account = dict(match) if match else self._new_account(account_id, clean)
            account.update(clean)
            account.update(paused=False, status="queued", last_error="")
            try:
                with self.credentials.transaction():
                    self.credentials.set(account_id, password, remember=clean["remember"])
                    self._accounts[account_id] = account
                    self._persist()
            except Exception as exc:
                if match is None:
                    self._accounts.pop(account_id, None)
                    if isinstance(exc, CredentialRollbackError):
                        raise CredentialError("The connection was not added because settings could not be saved. Its saved password may remain on this computer because local cleanup failed. Check disk space and permissions before trying again.") from None
                else:
                    self._accounts[account_id] = match
                    if isinstance(exc, CredentialRollbackError):
                        self._credential_errors[account_id] = str(exc)
                        self._requested.discard(account_id)
                raise
            self._credential_errors.pop(account_id, None)
            self._requested.add(account_id)
            self._wake.set()
            return self._public(account)

    def _get(self, account_id):
        account = self._accounts.get(account_id)
        if account is None:
            raise KeyError("Connection not found.")
        return account

    def sync_now(self, account_id):
        with self._lock:
            account = self._get(account_id)
            if account_id in self._credential_errors:
                raise CredentialRollbackError()
            if account["paused"]:
                raise ValueError("Resume the connection before syncing.")
            self._requested.add(account_id)
            if self._active != account_id:
                account["status"] = "queued"
            self._wake.set()
            return self._public(account)

    def pause(self, account_id):
        return self._pause(account_id, True)

    def resume(self, account_id):
        return self._pause(account_id, False)

    def _pause(self, account_id, paused):
        with self._lock:
            account = self._get(account_id)
            old = dict(account)
            account.update(paused=paused, status="paused" if paused else "queued")
            try:
                self._persist()
            except Exception:
                self._accounts[account_id] = old
                raise
            client = self._client if self._active == account_id and paused else None
            if not paused:
                self._requested.add(account_id)
            self._wake.set()
            result = self._public(account)
        if client is not None:
            client.abort()
        return result

    def remove(self, account_id):
        with self._lock:
            old = self._get(account_id)
            self._accounts.pop(account_id)
            try:
                self._persist()
            except Exception:
                self._accounts[account_id] = old
                raise
            self._requested.discard(account_id)
            self._credential_errors.pop(account_id, None)
            client = self._client if self._active == account_id else None
            self._wake.set()
            warning = None
            try:
                self.credentials.delete(account_id)
            except Exception:
                # Settings and credentials are separate durable files. Once
                # disconnect is committed, never resurrect an account whose
                # password cleanup may already have succeeded before raising.
                warning = "Mailbox disconnected. Its saved password may remain on this computer because local cleanup failed."
        if client is not None:
            client.abort()
        result = {"removed": True, "id": account_id}
        if warning:
            result["warning"] = warning
        return result

    def start(self):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._schedule, daemon=True, name="mailcairn-sync")
            self._thread.start()

    def stop(self):
        self._stop.set()
        self._wake.set()
        with self._lock:
            client, thread = self._client, self._thread
        if client is not None:
            client.abort()
        # Multiple shutdown callers may safely join the same worker. Never
        # release the archive OS lock while a sync commit is still running.
        if thread is not None and thread is not threading.current_thread():
            thread.join()

    def _schedule(self):
        while not self._stop.is_set():
            with self._lock:
                current = time.monotonic()
                account_id = next((key for key, account in self._accounts.items()
                                   if not account["paused"] and key not in self._credential_errors and
                                   (key in self._requested or self._next_due.get(key, 0) <= current)), None)
                if account_id:
                    self._requested.discard(account_id)
            if account_id is None:
                self._wake.wait(min(self.interval, 1))
                self._wake.clear()
                continue
            self._cycle(account_id)

    def _cancelled(self, account_id):
        with self._lock:
            account = self._accounts.get(account_id)
            return self._stop.is_set() or account is None or account["paused"] or account_id in self._credential_errors

    def _checkpoint(self, account_id, **fields):
        with self._lock:
            if account_id not in self._accounts:
                raise SyncError("unknown")
            old = dict(self._accounts[account_id])
            self._accounts[account_id].update(fields)
            try:
                self._persist()
            except Exception:
                self._accounts[account_id] = old
                raise

    def _save_message(self, raw, provider, uid, account_id):
        if len(raw) > self.max_message:
            raise SyncError("size")
        descriptor, temporary = tempfile.mkstemp(prefix=".upload-sync-", suffix=".eml", dir=self.folder)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw)
            receipt = self.store.import_file(Path(temporary), name=f"IMAP-{provider}-UID-{uid}.eml",
                                             cancelled=lambda: self._cancelled(account_id), max_bytes=self.max_message)
        except OSError:
            raise SyncError("unknown") from None
        finally:
            Path(temporary).unlink(missing_ok=True)
        if receipt["added"] + receipt["duplicates"] != 1 or receipt["skipped"] or receipt["status"] not in ("complete", "cancelled"):
            raise SyncError("message")
        return receipt

    def _cycle(self, account_id):
        if not self.operation.acquire(blocking=False):
            with self._lock:
                if account_id in self._accounts:
                    self._accounts[account_id]["status"] = "waiting"
                    self._next_due[account_id] = time.monotonic() + 1
            return
        client = None
        backlog = False
        error = None
        try:
            with self._lock:
                if self._cancelled(account_id):
                    return
                account = dict(self._get(account_id))
                self._active = account_id
                self._accounts[account_id].update(status="syncing", last_error="", last_added=0, last_duplicates=0)
            try:
                password = self.credentials.get(account_id)
            except CredentialError:
                password = None
            if not password:
                raise SyncError("credentials")
            client = self.client_factory(account, password,
                                         lambda pin: self._checkpoint(account_id, certificate_pin=pin), self.max_message)
            with self._lock:
                self._client = client
            if self._cancelled(account_id):
                return
            client.connect()
            if self._cancelled(account_id):
                return
            validity, next_uid = client.select(account["folder"])
            if validity != account["uidvalidity"]:
                self._checkpoint(account_id, uidvalidity=validity, last_uid=0)
                account["last_uid"] = 0
            last = account["last_uid"]
            high = min(last + UID_WINDOW, next_uid - 1)
            if high > last:
                candidates = client.search(last + 1, high)
                candidates = sorted({uid for uid in candidates if last < uid <= high})
                for uid in candidates[:BATCH_MESSAGES]:
                    if self._cancelled(account_id):
                        return
                    raw = client.fetch(uid)
                    if self._cancelled(account_id):
                        return
                    if raw is not None:
                        receipt = self._save_message(raw, account["provider"], uid, account_id)
                        with self._lock:
                            saved = dict(self._get(account_id))
                        # The cursor is advanced ONLY after SQLite's durable
                        # receipt reports added/duplicate. Failed saves retry.
                        self._checkpoint(account_id, last_uid=uid,
                                         added=saved["added"] + receipt["added"],
                                         last_added=saved["last_added"] + receipt["added"],
                                         last_duplicates=saved["last_duplicates"] + receipt["duplicates"],
                                         last_receipt_id=receipt["id"])
                    else:
                        self._checkpoint(account_id, last_uid=uid)
                    last = uid
                if len(candidates) <= BATCH_MESSAGES:
                    # Empty UID gaps were explicitly searched; no stored or
                    # unprocessed message is skipped by advancing across them.
                    last = high
                    self._checkpoint(account_id, last_uid=last)
                backlog = last < next_uid - 1
            if not self._cancelled(account_id):
                self._checkpoint(account_id, last_sync=utc_now())
        except SyncError as exc:
            error = exc.code
        except (OSError, imaplib.IMAP4.error):
            error = "network"
        except Exception:
            error = "unknown"
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
            with self._lock:
                self._client = None
                self._active = None
                account = self._accounts.get(account_id)
                if account is not None:
                    if account["paused"]:
                        account["status"] = "paused"
                    elif self._stop.is_set():
                        account["status"] = "idle"
                    elif error:
                        account["status"] = "auth_required" if error in ("auth", "credentials") else "error"
                        account["last_error"] = ERRORS.get(error, ERRORS["unknown"])
                    else:
                        account["status"] = "queued" if backlog else "idle"
                self._next_due[account_id] = time.monotonic() + (.05 if backlog and not error else self.interval)
            self.operation.release()
