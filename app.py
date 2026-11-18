#!/usr/bin/env python3
"""Run MailCairn with the Python standard library."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from pathlib import Path
import sys
import sqlite3
import time
import webbrowser

from mailcairn.server import LocalServer
from mailcairn import __version__
from mailcairn.store import Store, restore_backup
from mailcairn.instance import publish_instance, existing_launch, clear_instance


class ArchiveAlreadyOpen(ValueError):
    pass


def open_browser(launch):
    try:
        if webbrowser.open(launch):
            return
    except (OSError, webbrowser.Error):
        pass
    print("Browser could not open automatically. Copy the complete Open link above.", flush=True)


@contextmanager
def archive_lock(folder):
    """Hold an OS advisory lock until shutdown; stale lock files are harmless."""
    folder.mkdir(parents=True, exist_ok=True)
    lock = (folder / ".mailcairn.lock").open("a+b")
    try:
        lock.seek(0, 2)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ArchiveAlreadyOpen("This archive is already open. Close its other MailCairn process first.") from exc
        yield
    finally:
        lock.close()


def main():
    parser = argparse.ArgumentParser(description="Local mail archive with optional read-only mailbox connections.")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent / "data")
    parser.add_argument("--port", type=int, default=8765, help="Local port; 0 chooses an available port")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--open-existing", action="store_true", help="Open the verified running instance when this archive is already in use")
    parser.add_argument("--restore-backup", type=Path, help="Restore into a NEW data directory")
    parser.add_argument("--max-upload-gib", type=int, default=20)
    parser.add_argument("--max-message-mib", type=int, default=32)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535 or not 1 <= args.max_upload_gib <= 1000 or not 1 <= args.max_message_mib <= 256:
        parser.error("Port must be 0–65535, upload limit 1–1000 GiB and message limit 1–256 MiB.")
    folder = args.data_dir.resolve()
    try:
        with archive_lock(folder):
            archive = folder / "archive.sqlite3"
            if args.restore_backup:
                restore_backup(args.restore_backup, archive)
            store = Store(archive)
            store.recover_interrupted()
            # Only our named temporary uploads are removed after taking the lock.
            for abandoned in folder.glob(".upload-*"):
                if abandoned.is_file():
                    abandoned.unlink()
            server = LocalServer(("127.0.0.1", args.port), store, args.max_upload_gib * 1024 ** 3, args.max_message_mib * 1024 ** 2)
            try:
                publish_instance(folder, server)
            except OSError:
                server.server_close()
                raise
            launch = server.origin + "/#session=" + server.token
            print(f"MailCairn {__version__} - local mail archive", flush=True)
            print(f"Archive: {archive}", flush=True)
            print(f"Open: {launch}", flush=True)
            print("Keep this terminal open. Press Ctrl+C to stop. Connected mailboxes sync while the app runs; mail is never sent or deleted.", flush=True)
            try:
                if not args.no_browser:
                    open_browser(launch)
                server.serve_forever(poll_interval=0.2)
            except KeyboardInterrupt:
                print("\nStopping MailCairn…", flush=True)
                for job in server.jobs.values():
                    job["cancel"].set()
                # Let the active message transaction finish before exiting.
                server.operation.acquire(timeout=10)
            finally:
                server.server_close()
                clear_instance(folder, server)
    except ArchiveAlreadyOpen as exc:
        if args.open_existing and not args.restore_backup:
            # The first process may still be publishing its startup record.
            for attempt in range(4):
                launch = existing_launch(folder)
                if launch:
                    print("MailCairn is already running. Opening the existing archive.", flush=True)
                    print(f"Open: {launch}", flush=True)
                    if not args.no_browser:
                        open_browser(launch)
                    return 0
                if attempt < 3:
                    time.sleep(.2)
        print(f"Cannot start MailCairn: {exc}", file=sys.stderr)
        if args.open_existing and not args.restore_backup:
            print("The running instance could not be verified. If it was started with an older version, use its existing browser tab or close its terminal once and relaunch.", file=sys.stderr)
        return 1
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"Cannot start MailCairn: {exc}", file=sys.stderr)
        if "fts5" in str(exc).lower():
            print("Use Python 3.11+ with SQLite FTS5 enabled (the standard python.org builds include it).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
