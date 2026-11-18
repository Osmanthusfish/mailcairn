"""Discover an already-running archive without starting another writer."""
from __future__ import annotations

import http.client
import json
import os
from pathlib import Path
import re
import tempfile

INSTANCE_FILE = ".mailcairn-instance.json"


def publish_instance(folder, server):
    """Publish only while holding the archive lock. The token is local secret state."""
    folder = Path(folder)
    descriptor, temporary = tempfile.mkstemp(prefix=".mailcairn-instance-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"port": server.server_port, "token": server.token}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, folder / INSTANCE_FILE)
    finally:
        Path(temporary).unlink(missing_ok=True)


def read_instance(folder):
    path = Path(folder) / INSTANCE_FILE
    if path.is_symlink():
        return None
    try:
        with path.open("rb") as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            return None
        value = json.loads(raw)
        if not isinstance(value, dict):
            return None
        port, token = value.get("port"), value.get("token")
        if type(port) is not int or not 1 <= port <= 65535:
            return None
        if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
            return None
        return port, token
    except (OSError, ValueError, UnicodeError):
        return None


def existing_launch(folder):
    """Verify the live session and exact archive; never follow a supplied URL."""
    info = read_instance(folder)
    if info is None:
        return None
    port, token = info
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=.8)
    try:
        connection.request("GET", "/api/instance", headers={"Cookie": f"mailcairn_{port}={token}"})
        response = connection.getresponse()
        if response.status != 200:
            return None
        raw = response.read(4097)
        if len(raw) > 4096:
            return None
        value = json.loads(raw)
        expected = str((Path(folder) / "archive.sqlite3").resolve())
        if not isinstance(value, dict) or value.get("archive") != expected:
            return None
        return f"http://127.0.0.1:{port}/#session={token}"
    except (OSError, http.client.HTTPException, ValueError, UnicodeError):
        return None
    finally:
        connection.close()


def clear_instance(folder, server):
    """Do not remove a record that somebody replaced during shutdown."""
    if read_instance(folder) == (server.server_port, server.token):
        try:
            (Path(folder) / INSTANCE_FILE).unlink(missing_ok=True)
        except OSError:
            # A stale record is harmless: reuse always verifies the live session.
            pass
