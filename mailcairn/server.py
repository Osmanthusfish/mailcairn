"""Loopback-only HTTP interface. No third-party runtime dependencies."""
from __future__ import annotations

import hashlib
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import shutil
import socket
import socketserver
import sys
import tempfile
import threading
import time
import re
from urllib.parse import parse_qs, quote, urlsplit

from .parse import get_attachment
from . import __version__
from .sync import SyncManager

STATIC = Path(__file__).with_name("static")
MAX_REQUEST_THREADS = 16
HEADER_TIMEOUT = 10
UPLOAD_TIMEOUT = 30
UPLOAD_MIN_BYTES_PER_SECOND = 1024


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    # Windows SO_REUSEADDR can let unrelated listeners share one port. Keep
    # Unix restart behavior, but require exclusive ownership of Windows origins.
    allow_reuse_address = sys.platform != "win32"

    def server_bind(self):
        if sys.platform == "win32":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        socketserver.TCPServer.server_bind(self)
        self.server_name = "127.0.0.1"
        self.server_port = self.server_address[1]

    def __init__(self, address, store, max_upload=20 * 1024 ** 3, max_message=32 * 1024 ** 2):
        if address[0] != "127.0.0.1":
            raise ValueError("MailCairn can only bind to 127.0.0.1.")
        self.store = store
        self.max_upload = max_upload
        self.max_message = max_message
        self.token = secrets.token_urlsafe(32)
        self.jobs = {}
        self.job_lock = threading.Lock()
        self.operation = threading.Lock()
        self.request_slots = threading.BoundedSemaphore(MAX_REQUEST_THREADS)
        self.read_slots = threading.BoundedSemaphore(4)
        super().__init__(address, Handler)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        self.cookie_name = f"mailcairn_{self.server_port}"
        try:
            self.sync_manager = SyncManager(store, self.operation, max_message=max_message)
        except BaseException:
            super().server_close()
            raise

    def serve_forever(self, poll_interval=0.5):
        self.sync_manager.start()
        try:
            return super().serve_forever(poll_interval=poll_interval)
        finally:
            self.sync_manager.stop()

    def shutdown(self):
        # Stop network readers before any caller drains the shared operation
        # lock or releases exclusive ownership of the archive directory.
        self.sync_manager.stop()
        return super().shutdown()

    def server_close(self):
        if getattr(self, "sync_manager", None) is not None:
            self.sync_manager.stop()
        return super().server_close()

    def process_request(self, request, client_address):
        if not self.request_slots.acquire(blocking=False):
            # Never allocate another worker just to reject an overloaded socket.
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.request_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.request_slots.release()

    def new_job(self, kind):
        key = secrets.token_hex(12)
        job = {"id": key, "kind": kind, "status": "running", "progress": {}, "result": None, "cancel": threading.Event()}
        with self.job_lock:
            # Completed jobs are ephemeral; import receipts remain in SQLite.
            if len(self.jobs) >= 40:
                old = next((k for k, v in self.jobs.items() if v["status"] != "running"), None)
                if old:
                    del self.jobs[old]
            self.jobs[key] = job
        return job

    def start_job(self, job, target, cleanup=lambda: None):
        def run():
            fields = {}
            try:
                result = target(lambda info: self.update_job(job, progress=info), job["cancel"].is_set)
                fields = {"result": result, "status": "done"}
            except Exception as exc:
                fields = {"status": "failed", "error": str(exc)[:500]}
            finally:
                try:
                    cleanup()
                except OSError:
                    # A leftover temp file is removed after the next startup's
                    # archive lock; cleanup cannot permanently hold the job lock.
                    pass
                finally:
                    self.operation.release()
            self.update_job(job, **fields)
        threading.Thread(target=run, daemon=True, name="mailcairn-" + job["kind"]).start()

    def update_job(self, job, **fields):
        with self.job_lock:
            job.update(fields)


class Handler(BaseHTTPRequestHandler):
    server_version = f"MailCairn/{__version__}"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(HEADER_TIMEOUT)
        # Socket timeouts alone do not stop a client trickling one header byte
        # at a time. This deadline covers the request line and complete headers.
        self.header_timer = threading.Timer(HEADER_TIMEOUT, self.expire_headers)
        self.header_timer.daemon = True
        self.header_timer.start()

    def expire_headers(self):
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def finish(self):
        self.header_timer.cancel()
        super().finish()

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except OSError:
            # Header deadlines and disappearing local clients are normal socket
            # termination, including Windows WSAESHUTDOWN during parse_headers.
            # Endpoint storage errors are handled inside do_GET/do_POST.
            self.close_connection = True

    def request_body_size(self):
        self.header_timer.cancel()
        lengths = self.headers.get_all("Content-Length", [])
        if self.headers.get_all("Transfer-Encoding"):
            raise ValueError("Transfer-Encoding is not supported. Select a local file.")
        if len(lengths) > 1 or (lengths and not re.fullmatch(r"[0-9]{1,20}", lengths[0].strip())):
            raise ValueError("Invalid Content-Length header.")
        self._body_remaining = int(lengths[0]) if lengths else 0
        return self._body_remaining

    def log_message(self, fmt, *args):
        # URLs may contain private search terms. Never write them to console.
        pass

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        super().end_headers()

    def json(self, value, status=200, cookie=False):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", f"{self.server.cookie_name}={self.server.token}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        self.wfile.write(body)

    def error(self, status, message):
        # On Windows, closing a socket with an unread request body can reset it
        # before the client receives our error. Drain only small bounded bodies;
        # never read an unbounded rejected upload into memory.
        remaining = getattr(self, "_body_remaining", 0)
        if 0 < remaining <= 65536:
            try:
                self.connection.settimeout(1)
                self.rfile.read(remaining)
            except (OSError, TimeoutError):
                pass
            self._body_remaining = 0
        self.close_connection = True
        self.json({"error": message}, status)
        # Send a FIN after the complete response before discarding a rejected
        # large body. This avoids losing the response to a Windows socket reset.
        self.wfile.flush()
        try:
            self.connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass

    def trusted_request(self):
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self.error(403, "Open your archive from MailCairn or its startup link.")
            return False
        origin = self.headers.get("Origin")
        if origin and origin != self.server.origin:
            self.error(403, "Cross-origin access is not allowed.")
            return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self.error(403, "Cross-site access is not allowed.")
            return False
        return True

    def authenticated(self):
        try:
            cookies = SimpleCookie(self.headers.get("Cookie", ""))
            val = cookies.get(self.server.cookie_name)
            valid = val is not None and secrets.compare_digest(val.value, self.server.token)
        except Exception:
            valid = False
        if not valid:
            self.error(401, "Open your archive from MailCairn or its startup link to continue.")
        return valid

    def do_OPTIONS(self):
        self.header_timer.cancel()
        self.error(403, "Cross-origin requests are not supported.")

    def do_GET(self):
        reading = False
        try:
            if self.request_body_size():
                return self.error(400, "GET requests must not contain a body.")
            if len(self.path) > 8192:
                return self.error(414, "Request URL is too long.")
            if not self.trusted_request():
                return
            url = urlsplit(self.path)
            path = url.path
            if path in ("/", "/index.html", "/startup.js", "/app.js", "/i18n.js", "/style.css", "/fonts.css", "/favicon.svg", "/fonts/HankenGrotesk.ttf", "/fonts/Newsreader.ttf"):
                file = STATIC / ("index.html" if path == "/" else path[1:])
                if not file.is_file():
                    return self.error(404, "File not found.")
                types = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".ttf": "font/ttf"}
                with file.open("rb") as stream:
                    return self.file(stream, types[file.suffix])
            if not self.authenticated():
                return
            if path == "/api/instance":
                # Launcher discovery stays available during import and downloads.
                return self.json({"archive": str(self.server.store.path.resolve())})
            if path == "/api/connections":
                summary = self.server.sync_manager.status()
                return self.json({"connections": summary["accounts"], "settings_error": summary.get("settings_error", ""), "capabilities": {
                    "persistent_credentials": summary["credentials_persistent"],
                    "interval_seconds": 300,
                }})
            parts = path.strip("/").split("/")
            if len(parts) == 3 and parts[:2] == ["api", "jobs"]:
                with self.server.job_lock:
                    job = self.server.jobs.get(parts[2])
                    result = {k: v for k, v in job.items() if k != "cancel"} if job else None
                if result is None:
                    return self.error(404, "This job is no longer active. Check Import history for saved receipts.")
                return self.json(result)
            if not self.server.read_slots.acquire(blocking=False):
                return self.error(503, "The archive is busy. Retry shortly.")
            reading = True
            filters = {k: v[-1] for k, v in parse_qs(url.query, max_num_fields=30).items()}
            parts = path.strip("/").split("/")
            if path == "/api/stats":
                stats = self.server.store.stats()
                with self.server.job_lock:
                    running = next((j for j in self.server.jobs.values() if j["status"] == "running"), None)
                    stats["active_job"] = {k: v for k, v in running.items() if k != "cancel"} if running else None
                stats["limits"] = {"upload_bytes": self.server.max_upload, "message_bytes": self.server.max_message}
                return self.json(stats)
            if path == "/api/messages":
                return self.json(self.server.store.search(filters))
            if len(parts) >= 3 and parts[:2] == ["api", "messages"]:
                row_id = int(parts[2])
                if len(parts) == 3:
                    return self.json(self.server.store.message(row_id))
                msg = self.server.store.message(row_id, raw=True)
                import io
                if len(parts) == 4 and parts[3] == "eml":
                    return self.file(io.BytesIO(msg["raw"]), "message/rfc822", f"message-{row_id}.eml")
                if len(parts) == 5 and parts[3] == "attachments":
                    index = int(parts[4])
                    attachment = next((a for a in msg["attachments"] if a["index"] == index), None)
                    if attachment is None:
                        return self.error(404, "Attachment not found.")
                    return self.file(io.BytesIO(get_attachment(msg["raw"], index)), "application/octet-stream", attachment["name"])
            if len(parts) >= 3 and parts[:2] == ["api", "imports"]:
                run = int(parts[2])
                if len(parts) == 3:
                    return self.json(self.server.store.receipt(run))
                if len(parts) == 4 and parts[3] == "receipt":
                    with tempfile.TemporaryFile() as tmp:
                        self.server.store.export_receipt(run, tmp)
                        return self.file(tmp, "application/json", f"mailcairn-import-{run}.json")
            if path == "/api/export":
                with tempfile.TemporaryFile() as tmp:
                    self.server.store.export_mbox(filters, tmp)
                    return self.file(tmp, "application/mbox", "mailcairn-export.mbox")
            if path == "/api/backup":
                # NamedTemporaryFile cannot be reopened by SQLite on Windows.
                with tempfile.TemporaryDirectory(prefix="mailcairn-backup-") as folder:
                    target = Path(folder) / "backup.sqlite3"
                    self.server.store.backup(target)
                    with target.open("rb") as tmp:
                        return self.file(tmp, "application/octet-stream", "mailcairn-backup.sqlite3")
            return self.error(404, "Not found.")
        except (ValueError, KeyError) as exc:
            self.error(400, str(exc).strip("'"))
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            return
        except Exception:
            self.error(500, "The archive operation failed. Check available disk space and restart the app if necessary.")
        finally:
            if reading:
                self.server.read_slots.release()

    def do_POST(self):
        try:
            size = self.request_body_size()
            if len(self.path) > 8192:
                return self.error(414, "Request URL is too long.")
            if urlsplit(self.path).path not in ("/api/import", "/api/connections") and size:
                return self.error(400, "This action requires an empty request body.")
            if not self.trusted_request():
                return
            url = urlsplit(self.path)
            if url.path == "/api/session":
                supplied = self.headers.get("X-MailCairn-Token", "")
                if secrets.compare_digest(supplied, self.server.token):
                    return self.json({"ok": True}, cookie=True)
                return self.error(401, "This session has expired. Reopen your archive from MailCairn or its startup link.")
            if not self.authenticated():
                return
            if self.headers.get("X-MailCairn") != "1":
                return self.error(403, "Missing local request header.")
            if url.path == "/api/connections":
                return self.create_connection(size)
            parts = url.path.strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["api", "connections"]:
                methods = {"sync": "sync_now", "pause": "pause", "resume": "resume", "disconnect": "remove"}
                method = methods.get(parts[3])
                if not method or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", parts[2]):
                    return self.error(404, "Connection action not found.")
                try:
                    result = getattr(self.server.sync_manager, method)(parts[2])
                except KeyError:
                    return self.error(404, "Mailbox connection not found.")
                except ValueError as exc:
                    # Manager messages are fixed safe explanations, never IMAP
                    # server responses or submitted account/password strings.
                    return self.error(400, str(exc))
                return self.json({"ok": True, "connection": result})
            if url.path == "/api/import":
                return self.upload(url.query)
            if url.path == "/api/verify":
                if not self.server.operation.acquire(blocking=False):
                    return self.error(409, "An import or verification is already running. Let it finish or cancel it first.")
                job = self.server.new_job("verify")
                self.server.start_job(job, self.server.store.verify)
                return self.json({"job_id": job["id"]}, 202)
            parts = url.path.strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["api", "jobs"] and parts[3] == "cancel":
                with self.server.job_lock:
                    job = self.server.jobs.get(parts[2])
                    if job:
                        job["cancel"].set()
                if job is None:
                    return self.error(404, "Job not found.")
                return self.json({"ok": True})
            return self.error(404, "Not found.")
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            return
        except (ValueError, KeyError) as exc:
            self.error(400, str(exc).strip("'"))
        except Exception:
            self.error(500, "The operation failed. Check local disk space and retry.")

    def create_connection(self, size):
        if not 0 < size <= 16384:
            return self.error(413 if size > 16384 else 400, "Mailbox connection settings must be a JSON object under 16 KiB.")
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            return self.error(415, "Mailbox connection settings require application/json.")
        self.connection.settimeout(5)
        remaining, chunks = size, []
        started = time.monotonic()
        while remaining:
            chunk = self.rfile.read1(min(remaining, 16384))
            if not chunk:
                return self.error(400, "Incomplete mailbox connection settings.")
            chunks.append(chunk)
            remaining -= len(chunk)
            self._body_remaining = remaining
            if time.monotonic() - started > 5:
                return self.error(408, "Mailbox connection request timed out.")
        try:
            def unique_fields(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError("Duplicate field")
                    result[key] = value
                return result
            config = json.loads(b"".join(chunks).decode("utf-8"), object_pairs_hook=unique_fields)
            if not isinstance(config, dict):
                raise ValueError("Expected object")
        except (ValueError, UnicodeError):
            return self.error(400, "Mailbox connection settings are not valid JSON.")
        try:
            result = self.server.sync_manager.add(config)
        except ValueError as exc:
            return self.error(400, str(exc))
        except Exception:
            return self.error(500, "Could not save the mailbox connection. Check local storage and try again.")
        finally:
            # Do not retain submitted credentials in the HTTP handler.
            config.clear()
            chunks.clear()
        return self.json({"connection": result}, 201)

    def upload(self, query):
        name = parse_qs(query, max_num_fields=30).get("name", [""])[-1].replace("\\", "/").rsplit("/", 1)[-1][:250]
        if not name.lower().endswith((".mbox", ".eml")):
            return self.error(400, "Choose an extracted .mbox or .eml file. ZIP and PST are not supported.")
        size = int(self.headers.get("Content-Length", "0"))
        if self.headers.get("Transfer-Encoding"):
            return self.error(400, "Chunked transfer is not supported. Select a local file.")
        if size <= 0:
            return self.error(400, "The selected file is empty.")
        if size > self.server.max_upload:
            return self.error(413, f"File exceeds the configured {self.server.max_upload // (1024 ** 3)} GiB upload limit.")
        free = shutil.disk_usage(self.server.store.path.parent).free
        if free < size * 2 + 128 * 1024 ** 2:
            return self.error(507, "Not enough free space for the upload and archive. Free disk space and try again.")
        if not self.server.operation.acquire(blocking=False):
            return self.error(409, "An import or verification is already running.")
        handed_off = False
        path = None
        try:
            digest = hashlib.sha256()
            with tempfile.NamedTemporaryFile(dir=self.server.store.path.parent, prefix=".upload-", delete=False) as tmp:
                path = Path(tmp.name)
                remaining = size
                self.connection.settimeout(UPLOAD_TIMEOUT)
                started = time.monotonic()
                while remaining:
                    chunk = self.rfile.read1(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ValueError("Upload interrupted; no import was started.")
                    tmp.write(chunk)
                    digest.update(chunk)
                    remaining -= len(chunk)
                    self._body_remaining = remaining
                    elapsed = time.monotonic() - started
                    if elapsed > UPLOAD_TIMEOUT and (size - remaining) / elapsed < UPLOAD_MIN_BYTES_PER_SECOND:
                        raise ValueError("Upload is too slow; no import was started. Please retry.")
            job = self.server.new_job("import")
            self.server.start_job(job, lambda progress, cancelled: self.server.store.import_file(path, name=name, digest=digest.hexdigest(), progress=progress, cancelled=cancelled, max_bytes=self.server.max_message), cleanup=path.unlink)
            handed_off = True
            return self.json({"job_id": job["id"]}, 202)
        finally:
            if not handed_off:
                try:
                    if path:
                        path.unlink(missing_ok=True)
                finally:
                    self.server.operation.release()

    def file(self, stream, mime, name=None):
        stream.seek(0, 2)
        length = stream.tell()
        stream.seek(0)
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(length))
        if name:
            clean = name.replace("\\", "/").rsplit("/", 1)[-1]
            clean = "".join(ch for ch in clean if ord(ch) >= 32 and ch not in '\"')[:180] or "download"
            self.send_header("Content-Disposition", "attachment; filename=\"download\"; filename*=UTF-8''" + quote(clean, safe=""))
        self.end_headers()
        shutil.copyfileobj(stream, self.wfile, length=1024 * 1024)
