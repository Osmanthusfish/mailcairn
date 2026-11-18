#!/usr/bin/env python3
"""Bounded synthetic English/CJK and attachment benchmark, with no network access.

Default: 1,000 messages, about 2 KiB text each and 64 KiB binary attachments
on every fourth message. Temporary fixtures are removed unless --keep-work
names a new directory outside the source tree. Reports contain no local paths.
"""
import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
import hashlib
import json
from pathlib import Path
import platform
import sqlite3
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]

LANGUAGES = (
    ("en", "Synthetic garden journal and family travel records."),
    ("zh", "合成档案记录：花园散步与家庭旅行。 保修 发票 café"),
    ("ja", "合成メール記録：庭の散歩と家族旅行。"),
    ("ko", "합성메일기록 정원 산책과 가족 여행."),
)
ENVELOPE = b"From synthetic@example.com Mon Nov 09 09:00:00 2026\n"


def payload(index, size):
    block = hashlib.sha256(f"synthetic-attachment-{index}".encode()).digest()
    return (block * ((size + len(block) - 1) // len(block)))[:size]


def fixture(index, args):
    language, text = LANGUAGES[index % len(LANGUAGES)]
    message = EmailMessage(policy=policy.default)
    message["From"] = f"Synthetic Sender {index % 17} <sender{index % 17}@example.com>"
    message["To"] = "Synthetic Reader <reader@example.com>"
    message["Subject"] = f"Synthetic {language} journal {index}"
    message["Message-ID"] = f"<mixed-benchmark-{index}@example.com>"
    message["Date"] = "Mon, 09 Nov 2026 09:00:00 +0800"
    line = text + "\n"
    repetitions = max(1, (args.body_bytes + len(line.encode()) - 1) // len(line.encode()))
    message.set_content(f"commonbeacon selective{index}end\n" + line * repetitions)
    if index % args.attachment_every == 0:
        message.add_attachment(payload(index, args.attachment_bytes), maintype="application",
                               subtype="octet-stream", filename=f"synthetic-附件记录-{index}.bin")
        message.set_boundary(f"mailcairn-synthetic-mixed-{index}")
    return message.as_bytes()


def timed(call):
    started = time.perf_counter()
    result = call()
    return result, round(time.perf_counter() - started, 6)


def receipt_summary(receipt):
    return {key: receipt[key] for key in ("status", "total", "added", "duplicates", "skipped", "warning_count")}


def verify_summary(store):
    result, seconds = timed(store.verify)
    return {"seconds": seconds, **{key: result[key] for key in
            ("checked", "mismatches", "sqlite", "search_index", "receipts")}}


def benchmark(root, args):
    failures = []

    def require(condition, name):
        if not condition:
            failures.append(name)

    source = root / "synthetic-mixed.mbox"
    source_hash = hashlib.sha256()
    source_bytes = 0
    started = time.perf_counter()
    with source.open("xb") as stream:
        for index in range(args.messages):
            raw = fixture(index, args)
            chunk = ENVELOPE + raw
            source_bytes += len(chunk)
            if source_bytes > args.max_source_mib * 1024 ** 2:
                raise ValueError("source_size_limit")
            stream.write(chunk)
            source_hash.update(chunk)
    generation_seconds = round(time.perf_counter() - started, 6)
    store = Store(root / "archive.sqlite3")
    imported, import_seconds = timed(lambda: store.import_file(source))
    require((imported["status"], imported["total"], imported["added"], imported["duplicates"], imported["skipped"])
            == ("complete", args.messages, args.messages, 0, 0), "complete_initial_import")
    attachment_count = (args.messages - 1) // args.attachment_every + 1
    require(store.stats()["attachments"] == attachment_count, "attachment_inventory")

    cases = [("selective_first", "selective0end", 1),
             ("selective_middle", f"selective{args.messages // 2}end", 1),
             ("selective_last", f"selective{args.messages - 1}end", 1),
             ("common_english", "commonbeacon", args.messages)]
    for offset, (language, term) in enumerate((("zh", "花园散步"), ("ja", "庭の散歩"), ("ko", "정원")), start=1):
        expected = len(range(offset, args.messages, 4))
        cases.append(("cjk_" + language, term, expected))
    cases.append(("absent", "absentbeaconneverpresent", 0))
    cases.extend((
        ("cjk_punctuation", "保修，发票", len(range(1, args.messages, 4))),
        ("mixed_cjk_accent_case", "CAFE 花园", len(range(1, args.messages, 4))),
        ("attachment_cjk_filename_fragment", "件记", attachment_count),
        ("attachment_latin_filename_fragment", "etic", attachment_count),
    ))
    searches = []
    for name, query, expected in cases:
        observations = []
        matches = []
        page_sizes = []
        for repeat in range(args.query_repeats):
            result, seconds = timed(lambda: store.search({"q": query}))
            observations.append(seconds)
            matches.append(result["total"])
            page_sizes.append(len(result["messages"]))
        require(all(count == expected for count in matches), "query_matches_" + name)
        require(all(count == min(expected, 50) for count in page_sizes), "query_page_" + name)
        searches.append({"name": name, "query": query, "expected_matches": expected,
                         "matches": matches, "page_sizes": page_sizes, "seconds": observations,
                         "first_seconds": observations[0], "median_seconds": statistics.median(observations),
                         "max_seconds": max(observations)})

    sample_indices = sorted({0, args.messages // 2, args.messages - 1,
                             ((args.messages - 1) // args.attachment_every) * args.attachment_every})
    fidelity = []
    for index in sample_indices:
        result = store.search({"q": f"selective{index}end"})
        if result["total"] != 1:
            require(False, "fidelity_lookup")
            continue
        saved = store.message(result["messages"][0]["id"], raw=True)
        raw_equal = saved["raw"] == fixture(index, args)
        require(raw_equal, "raw_fidelity")
        row = {"index": index, "raw_bytes": len(saved["raw"]), "raw_equal": raw_equal,
               "raw_sha256": hashlib.sha256(saved["raw"]).hexdigest()}
        if index % args.attachment_every == 0:
            require(len(saved["attachments"]) == 1, "sample_attachment_count")
            if saved["attachments"]:
                data = get_attachment(saved["raw"], saved["attachments"][0]["index"])
                row.update(attachment_bytes=len(data), attachment_equal=data == payload(index, args.attachment_bytes),
                           attachment_sha256=hashlib.sha256(data).hexdigest())
                require(row["attachment_equal"], "attachment_fidelity")
        fidelity.append(row)

    duplicated, duplicate_seconds = timed(lambda: store.import_file(source))
    require((duplicated["status"], duplicated["total"], duplicated["added"], duplicated["duplicates"], duplicated["skipped"])
            == ("complete", args.messages, 0, args.messages, 0), "duplicate_import")
    verification = verify_summary(store)
    require(verification["checked"] == args.messages and not verification["mismatches"] and
            all(verification[key] == "ok" for key in ("sqlite", "search_index", "receipts")), "integrity")
    cancellation = {"executed": False}
    if args.cancel_after:
        recovery_store = Store(root / "cancel-resume.sqlite3")
        observed = {"stop": False, "committed": 0}

        def progress(info):
            observed["committed"] = info["added"]
            if info["total"] >= args.cancel_after:
                observed["stop"] = True

        cancelled, cancel_seconds = timed(lambda: recovery_store.import_file(
            source, progress=progress, cancelled=lambda: observed["stop"]))
        durable_count = recovery_store.search({})["total"]
        cancelled_verification = verify_summary(recovery_store)
        # Reopen the archive before reimporting the full original file.
        recovery_store = Store(root / "cancel-resume.sqlite3")
        resumed, resume_seconds = timed(lambda: recovery_store.import_file(source))
        resumed_verification = verify_summary(recovery_store)
        require(cancelled["status"] == "cancelled" and 0 < durable_count < args.messages,
                "cancelled_mid_import")
        require(durable_count == cancelled["added"] == observed["committed"], "cancel_durable_count")
        require((resumed["status"], resumed["added"], resumed["duplicates"], resumed["skipped"])
                == ("complete", args.messages - durable_count, durable_count, 0), "resume_counts")
        for label, check, expected in (("cancel", cancelled_verification, durable_count),
                                       ("resume", resumed_verification, args.messages)):
            require(check["checked"] == expected and not check["mismatches"] and
                    all(check[key] == "ok" for key in ("sqlite", "search_index", "receipts")), label + "_integrity")
        cancellation = {"executed": True, "requested_after": args.cancel_after,
                        "durable_messages": durable_count, "cancel_seconds": cancel_seconds,
                        "cancel_receipt": receipt_summary(cancelled), "cancel_verification": cancelled_verification,
                        "resume_seconds": resume_seconds, "resume_receipt": receipt_summary(resumed),
                        "resume_verification": resumed_verification}

    peak, method = peak_memory()
    return {"status": "passed" if not failures else "failed", "failures": failures,
            "measured_at": datetime.now(timezone.utc).isoformat(), "app_version": __version__,
            "source_sha256": {name: hashlib.sha256((args.source_dir / name).read_bytes()).hexdigest()
                              for name in ("mailcairn/store.py", "mailcairn/parse.py", "mailcairn/__init__.py")},
            "benchmark_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "environment": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
                            "platform": platform.system(), "platform_release": platform.release(),
                            "architecture": platform.machine()},
            "fixture": {"synthetic_only": True, "messages": args.messages,
                        "languages": {language: len(range(offset, args.messages, 4))
                                      for offset, (language, text) in enumerate(LANGUAGES)},
                        "minimum_body_bytes_requested": args.body_bytes,
                        "attachment_every": args.attachment_every, "attachment_count": attachment_count,
                        "attachment_bytes_each": args.attachment_bytes, "source_bytes": source_bytes,
                        "source_sha256": source_hash.hexdigest(), "generation_seconds": generation_seconds,
                        "kept_for_follow_up": args.keep_work is not None},
            "import": {"seconds": import_seconds, "messages_per_second": round(args.messages / import_seconds, 2),
                       "receipt": receipt_summary(imported)},
            "searches": searches, "fidelity_samples": fidelity,
            "duplicate_import": {"seconds": duplicate_seconds, "receipt": receipt_summary(duplicated)},
            "verification": verification, "cancellation_resume": cancellation,
            "archive_bytes_after_duplicate_import": store.path.stat().st_size,
            "peak_memory_bytes": peak, "peak_memory_method": method,
            "limits": ["One synthetic local run; not real-provider, large-capacity, HTTP or browser evidence.",
                       "CJK queries use the application's literal-substring fallback, not FTS segmentation.",
                       "Queries follow import and repeat in one process; OS/database caches are not flushed.",
                       "Attachments are deterministic repetitive binary data; no attachment-text indexing is tested.",
                       "Raw and attachment byte comparisons are sampled; integrity hashes cover every stored message.",
                       "Peak memory covers fixture generation and all benchmark phases, not import alone.",
                       "Cancellation waits for a committed progress boundary, not an exact requested ordinal."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--messages", type=int, default=1000)
    parser.add_argument("--body-bytes", type=int, default=2048)
    parser.add_argument("--attachment-bytes", type=int, default=65536)
    parser.add_argument("--attachment-every", type=int, default=4)
    parser.add_argument("--query-repeats", type=int, default=5)
    parser.add_argument("--max-source-mib", type=int, default=100)
    parser.add_argument("--cancel-after", type=int, default=0, help="Optional committed-count threshold; 0 disables")
    parser.add_argument("--output", type=Path, required=True, help="New metrics JSON outside the source tree")
    parser.add_argument("--source-dir", type=Path, default=ROOT, help="Application source to benchmark; supports frozen release comparisons")
    parser.add_argument("--keep-work", type=Path, help="New directory outside source; preserves synthetic mail and archives")
    args = parser.parse_args()
    args.source_dir = args.source_dir.resolve()
    if not (args.source_dir / "mailcairn/store.py").is_file():
        parser.error("Source directory must contain mailcairn/store.py")
    sys.path.insert(0, str(args.source_dir))
    global Store, get_attachment, __version__, peak_memory
    from mailcairn import __version__
    from mailcairn.parse import get_attachment
    from mailcairn.store import Store
    from scripts.benchmark import peak_memory
    if not (4 <= args.messages <= 100000 and 128 <= args.body_bytes <= 1000000
            and 1 <= args.attachment_bytes <= 8000000 and 1 <= args.attachment_every <= args.messages
            and 1 <= args.query_repeats <= 100 and 1 <= args.max_source_mib <= 1024
            and (args.cancel_after == 0 or 0 < args.cancel_after < args.messages)):
        parser.error("Invalid bounded workload settings; see --help")
    args.output = args.output.resolve()
    if args.output.exists() or args.output.is_relative_to(ROOT):
        parser.error("Report must be a new file outside the source tree")
    if args.keep_work:
        args.keep_work = args.keep_work.resolve()
        if args.keep_work.exists() or args.keep_work.is_relative_to(ROOT):
            parser.error("Work directory must be new and outside the source tree")
        args.keep_work.mkdir(parents=True)
    context = nullcontext(args.keep_work) if args.keep_work else tempfile.TemporaryDirectory(prefix="mailcairn-mixed-")
    with context as location:
        result = benchmark(Path(location), args)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(rendered + "\n")
    # Console encodings such as Windows GBK may not represent every CJK script.
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
