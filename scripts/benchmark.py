#!/usr/bin/env python3
"""Reproducible synthetic benchmark; never reads private mail.

Default: 10,000 messages with about 10 KB of text each. The reported process
peak is a Windows peak working set or Unix ru_maxrss, not Python heap size.
All generated mail and databases live in a disposable temporary directory.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mailcairn.store import Store


def peak_memory():
    if os.name == "nt":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return counters.PeakWorkingSetSize, "Windows peak process working set"
    else:
        try:
            import resource
            peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            return peak if sys.platform == "darwin" else peak * 1024, "Unix process ru_maxrss"
        except (ImportError, AttributeError):
            pass
    return None, "Unavailable on this platform"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--messages", type=int, default=10_000)
    parser.add_argument("--body-bytes", type=int, default=10_000)
    parser.add_argument("--output", type=Path, help="Write metrics JSON (contains no mail or local usernames)")
    args = parser.parse_args()
    if not 1 <= args.messages <= 1_000_000 or not 100 <= args.body_bytes <= 4_000_000:
        parser.error("messages must be 1–1,000,000; body-bytes must be 100–4,000,000")
    with tempfile.TemporaryDirectory(prefix="mailcairn-benchmark-") as temp:
        root = Path(temp)
        source = root / "synthetic.mbox"
        line = b"This synthetic archive entry records a local journey, a garden visit, and a family lunch.\n"
        padding = (line * (args.body_bytes // len(line) + 1))[:args.body_bytes]
        with source.open("wb") as output:
            for index in range(args.messages):
                output.write(b"From archive@example.com Mon Nov 09 09:00:00 2026\n")
                output.write((f"From: Sender {index % 100} <sender{index % 100}@example.com>\nTo: reader@example.com\nSubject: Synthetic archive message {index}\nDate: Mon, 09 Nov 2026 09:00:00 +0800\nMessage-ID: <benchmark-{index}@example.com>\nContent-Type: text/plain; charset=utf-8\n\nUnique lookup marker beacon{index}end.\n").encode())
                output.write(padding + b"\n")
        store = Store(root / "archive.sqlite3")
        started = time.perf_counter()
        receipt = store.import_file(source)
        import_seconds = time.perf_counter() - started
        queries = []
        for index in (0, args.messages // 2, args.messages - 1):
            start = time.perf_counter()
            result = store.search({"q": f"beacon{index}end"})
            queries.append({"seconds": time.perf_counter() - start, "matches": result["total"]})
        verify_started = time.perf_counter()
        verification = store.verify()
        verify_seconds = time.perf_counter() - verify_started
        peak, method = peak_memory()
        metrics = {
            "fixture": "Synthetic text-only emails; no attachments; not a real mailbox benchmark",
            "python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
            "platform": platform.system(), "platform_release": platform.release(), "architecture": platform.machine(),
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "messages_requested": args.messages, "body_bytes_requested": args.body_bytes,
            "source_bytes": source.stat().st_size, "archive_bytes": store.path.stat().st_size,
            "import_status": receipt["status"], "total": receipt["total"],
            "added": receipt["added"], "duplicates": receipt["duplicates"], "skipped": receipt["skipped"],
            "import_seconds": round(import_seconds, 3),
            "messages_per_second": round(args.messages / import_seconds, 2),
            "searches": queries, "verification_seconds": round(verify_seconds, 3),
            "verification": {k: verification[k] for k in ("checked", "mismatches", "sqlite", "search_index", "receipts")},
            "peak_memory_bytes": peak, "peak_memory_method": method,
            "limits": "Synthetic text only; does not establish 20 GiB performance or attachment-heavy archive performance.",
        }
        rendered = json.dumps(metrics, ensure_ascii=False, indent=2)
        print(rendered)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        if (receipt["status"] != "complete" or receipt["added"] != args.messages
                or receipt["total"] != args.messages or receipt["duplicates"] != 0
                or receipt["skipped"] != 0 or any(q["matches"] != 1 for q in queries)
                or verification["checked"] != args.messages or verification["mismatches"]
                or verification["sqlite"] != "ok" or verification["search_index"] != "ok"
                or verification["receipts"] != "ok"):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
