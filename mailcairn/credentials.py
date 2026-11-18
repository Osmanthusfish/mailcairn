"""Per-user Windows DPAPI credentials; explicitly memory-only elsewhere."""
from __future__ import annotations

import base64
from contextlib import contextmanager
import ctypes
from functools import lru_cache
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import threading

CREDENTIALS_FILE = ".mailcairn-credentials.json"
ACCOUNT_ID = re.compile(r"^[a-f0-9]{24}$")


class CredentialError(ValueError):
    pass


class CredentialRollbackError(CredentialError):
    """A failed settings update could not restore the previous protected file."""

    def __init__(self):
        super().__init__("Connection settings could not be saved and the previous saved password could not be restored. The saved password may have changed. Reconnect this account before restarting the app.")


def atomic_json(path, value):
    """Replace only this local state file; incomplete writes never become state."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.stem + "-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _dpapi(data, decrypt=False):
    if sys.platform != "win32":
        raise CredentialError("Persistent credentials require Windows DPAPI.")
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source = Blob(len(data), buffer)
    target = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p if decrypt else wintypes.LPCWSTR,
                         ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                         wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    # UI_FORBIDDEN, with per-user protection. Never use LOCAL_MACHINE scope.
    if not function(ctypes.byref(source), None if decrypt else "MailCairn", None,
                    None, None, 1, ctypes.byref(target)):
        raise CredentialError("Saved credentials could not be protected or unlocked. Reconnect this account.")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(target.data)


@lru_cache(maxsize=1)
def dpapi_available():
    if sys.platform != "win32":
        return False
    try:
        probe = b"MailCairn synthetic capability probe"
        return _dpapi(_dpapi(probe), decrypt=True) == probe
    except (CredentialError, OSError, AttributeError):
        return False


class CredentialStore:
    def __init__(self, folder, persistent=None):
        self.path = Path(folder) / CREDENTIALS_FILE
        self.persistent = dpapi_available() if persistent is None else bool(persistent)
        self._memory = {}
        self._encrypted = {}
        self._lock = threading.RLock()
        if self.path.exists():
            try:
                if self.path.is_symlink() or self.path.stat().st_size > 100_000:
                    raise ValueError
                state = json.loads(self.path.read_text(encoding="utf-8"))
                values = state["secrets"]
                if state.get("version") != 1 or not isinstance(values, dict) or len(values) > 10:
                    raise ValueError
                for key, value in values.items():
                    if not ACCOUNT_ID.fullmatch(key) or not isinstance(value, str) or len(value) > 32_000:
                        raise ValueError
                self._encrypted = values
            except (OSError, ValueError, TypeError, KeyError, RecursionError):
                # Existing archives remain usable; accounts explicitly need
                # re-authentication rather than silently writing plaintext.
                self._encrypted = {}

    @contextmanager
    def transaction(self):
        """Restore opaque prior state on failure, without decrypting secrets.

        This is exception recovery across two local files, not crash atomicity.
        Keep the lock so rollback cannot erase a concurrent credential update.
        """
        with self._lock:
            encrypted, memory = dict(self._encrypted), dict(self._memory)
            try:
                yield
            except Exception:
                self._memory = memory
                if self._encrypted != encrypted:
                    try:
                        atomic_json(self.path, {"version": 1, "secrets": encrypted})
                    except Exception:
                        # The disk still has the published new representation.
                        # Preserve old session state but surface restart risk.
                        raise CredentialRollbackError() from None
                self._encrypted = encrypted
                raise

    def set(self, account_id, password, remember=True):
        if not ACCOUNT_ID.fullmatch(account_id) or not isinstance(password, str) or not 1 <= len(password) <= 4096:
            raise CredentialError("A valid account and password are required.")
        with self._lock:
            values = dict(self._encrypted)
            if self.persistent and remember:
                values[account_id] = base64.b64encode(_dpapi(password.encode("utf-8"))).decode("ascii")
            else:
                values.pop(account_id, None)
            if values != self._encrypted:
                atomic_json(self.path, {"version": 1, "secrets": values})
            self._encrypted = values
            self._memory[account_id] = password

    def get(self, account_id):
        with self._lock:
            if account_id in self._memory:
                return self._memory[account_id]
            if not self.persistent:
                return None
            value = self._encrypted.get(account_id)
            if value is None:
                return None
            try:
                password = _dpapi(base64.b64decode(value, validate=True), decrypt=True).decode("utf-8")
            except (CredentialError, ValueError, UnicodeError):
                raise CredentialError("Saved credentials could not be unlocked. Reconnect this account.") from None
            self._memory[account_id] = password
            return password

    def available(self, account_id):
        try:
            return bool(self.get(account_id))
        except CredentialError:
            return False

    def remembered(self, account_id):
        with self._lock:
            return self.persistent and account_id in self._encrypted

    def delete(self, account_id):
        with self._lock:
            values = dict(self._encrypted)
            values.pop(account_id, None)
            if values != self._encrypted:
                atomic_json(self.path, {"version": 1, "secrets": values})
            self._encrypted = values
            self._memory.pop(account_id, None)
