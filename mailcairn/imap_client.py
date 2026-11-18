"""Bounded, read-only IMAP transport. Never changes flags or expunges mail."""
from __future__ import annotations

import hashlib
import hmac
import imaplib
import re
import socket
import ssl
import threading

NETWORK_TIMEOUT = 20

ERRORS = {
    "auth": "Authentication failed. Check the username and app password.",
    "credentials": "Credentials are needed. Reconnect this account.",
    "network": "Could not connect securely. Check the server, port and network.",
    "tls_certificate": "The mail server's security certificate could not be verified. Check the server address and your device's date and time.",
    "certificate": "The Proton Bridge certificate changed. Remove and reconnect this account after checking Bridge.",
    "size": "A message exceeds the archive size limit. Sync stopped before that message.",
    "message": "A message could not be archived. Sync stopped before that message.",
    "settings": "Connection settings could not be saved. Check disk space and permissions.",
    "protocol": "The server returned an unsupported or incomplete IMAP response.",
    "unknown": "Sync failed. Check the connection and available disk space, then retry.",
}


class SyncError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(ERRORS.get(code, ERRORS["unknown"]))


class _BoundedRead:
    def read(self, size):
        if size > self.max_literal:
            raise SyncError("size")
        return super().read(size)


class _IMAP(_BoundedRead, imaplib.IMAP4):
    def __init__(self, *args, max_literal, **kwargs):
        self.max_literal = max_literal
        super().__init__(*args, **kwargs)


class _IMAPSSL(_BoundedRead, imaplib.IMAP4_SSL):
    def __init__(self, *args, max_literal, **kwargs):
        self.max_literal = max_literal
        super().__init__(*args, **kwargs)


def _number(response):
    data = response[1]
    if not data or not isinstance(data[0], bytes) or not re.fullmatch(rb"[0-9]+", data[0]):
        raise SyncError("protocol")
    value = int(data[0])
    if not 1 <= value <= 4_294_967_295:
        raise SyncError("protocol")
    return value


class IMAPClient:
    def __init__(self, account, password, on_pin, max_message):
        self.account = account
        self.password = password
        self.on_pin = on_pin
        self.max_message = max_message
        self.connection = None
        self._aborted = threading.Event()

    def _check_active(self):
        if self._aborted.is_set():
            raise SyncError("network")

    def connect(self):
        account = self.account
        try:
            self._check_active()
            if account["provider"] == "proton":
                if account["host"] != "127.0.0.1":
                    raise SyncError("network")
                self.connection = _IMAP("127.0.0.1", account["port"], timeout=NETWORK_TIMEOUT, max_literal=self.max_message + 1)
                self.connection.debug = 0
                self._check_active()
                # Bridge's self-signed certificate is scoped to a literal local
                # address. Pin it BEFORE transmitting any authentication data.
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                self.connection.starttls(ssl_context=context)
                self._check_active()
                certificate = self.connection.sock.getpeercert(binary_form=True)
                if not certificate:
                    raise SyncError("network")
                fingerprint = hashlib.sha256(certificate).hexdigest()
                known = account.get("certificate_pin")
                if known and not hmac.compare_digest(known, fingerprint):
                    raise SyncError("certificate")
                if not known:
                    self.on_pin(fingerprint)
            else:
                context = ssl.create_default_context()
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                self.connection = _IMAPSSL(account["host"], account["port"], ssl_context=context,
                                           timeout=NETWORK_TIMEOUT, max_literal=self.max_message + 1)
                self.connection.debug = 0
            self._check_active()
            try:
                status, _ = self.connection.login(account["username"], self.password)
                if status != "OK":
                    raise SyncError("auth")
            except imaplib.IMAP4.abort:
                # abort inherits error, but a dropped connection is not a
                # rejection of the supplied credentials.
                raise SyncError("network") from None
            except imaplib.IMAP4.error:
                raise SyncError("auth") from None
        except SyncError:
            raise
        except ssl.SSLCertVerificationError:
            raise SyncError("tls_certificate") from None
        except (OSError, ssl.SSLError, imaplib.IMAP4.error):
            raise SyncError("network") from None
        finally:
            self.password = None

    def select(self, folder):
        quoted = '"' + folder.replace("\\", "\\\\").replace('"', '\\"') + '"'
        status, _ = self.connection.select(quoted, readonly=True)
        if status != "OK":
            raise SyncError("protocol")
        return _number(self.connection.response("UIDVALIDITY")), _number(self.connection.response("UIDNEXT"))

    def search(self, low, high):
        status, response = self.connection.uid("SEARCH", None, "UID", f"{low}:{high}")
        if status != "OK" or not response or not isinstance(response[0], bytes):
            raise SyncError("protocol")
        if len(response[0]) > 16_000:
            raise SyncError("protocol")
        words = response[0].split()
        if any(not word.isdigit() for word in words) or len(words) > high - low + 1:
            raise SyncError("protocol")
        # IMAP reverses ranges such as n:* when n exceeds the highest UID.
        # Every response is explicitly filtered to the bounded requested window.
        return sorted({int(word) for word in words if low <= int(word) <= high})

    def fetch(self, uid):
        status, response = self.connection.uid("FETCH", str(uid), "(UID RFC822.SIZE)")
        if status != "OK":
            raise SyncError("protocol")
        metadata = b" ".join(part for part in response if isinstance(part, bytes))
        if not metadata.strip():
            return None  # Expunged by another client between SEARCH and FETCH.
        size = re.search(rb"\bRFC822\.SIZE ([0-9]+)\b", metadata, re.I)
        found_uid = re.search(rb"\bUID ([0-9]+)\b", metadata, re.I)
        if not size or not found_uid or int(found_uid[1]) != uid:
            raise SyncError("protocol")
        length = int(size[1])
        if length > self.max_message:
            raise SyncError("size")
        status, response = self.connection.uid("FETCH", str(uid), f"(UID BODY.PEEK[]<0.{self.max_message + 1}>)")
        if status != "OK":
            raise SyncError("protocol")
        literals = [part for part in response if isinstance(part, tuple)]
        if not literals:
            # An empty FETCH can mean the message was expunged between the
            # size and body requests. A nonempty response without its literal
            # is incomplete: do not treat it as an expunge and skip the UID.
            if any(part is not None and (not isinstance(part, bytes) or part.strip()) for part in response):
                raise SyncError("protocol")
            return None
        if len(literals) != 1:
            raise SyncError("protocol")
        meta, raw = literals[0]
        found_uid = re.search(rb"\bUID ([0-9]+)\b", meta, re.I)
        if not found_uid or int(found_uid[1]) != uid or not isinstance(raw, bytes) or len(raw) != length:
            raise SyncError("protocol")
        if len(raw) > self.max_message:
            raise SyncError("size")
        return raw

    def abort(self):
        self._aborted.set()
        connection = self.connection
        if connection is not None:
            sock = getattr(connection, "sock", None)
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

    def close(self):
        # LOGOUT never changes message flags. Do not call IMAP CLOSE, which can
        # expunge messages when used after a writable SELECT elsewhere.
        if self.connection is not None:
            try:
                self.connection.logout()
            except Exception:
                try:
                    self.connection.shutdown()
                except Exception:
                    pass
