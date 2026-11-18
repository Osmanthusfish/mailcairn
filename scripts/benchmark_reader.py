"""Measure saved plain-text preview reads; synthetic data, no network access."""
import argparse
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
import tracemalloc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--attachment-mib', type=int, default=8)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    if not 1 <= args.attachment_mib <= 16 or not 1 <= args.repeats <= 30:
        parser.error('Attachment must be 1–16 MiB and repetitions 1–30.')
    if args.output.exists() or args.output.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        parser.error('Report must be a new file outside the project source.')
    sys.path.insert(0, str(source))
    from mailcairn.store import Store
    from mailcairn.parse import get_attachment
    from mailcairn import __version__
    code_hash = hashlib.sha256((source / 'mailcairn/store.py').read_bytes()).hexdigest()
    attachment = bytes(range(256)) * (args.attachment_mib * 1024 ** 2 // 256)
    mail = EmailMessage(policy=policy.default)
    mail['From'] = 'Synthetic <sender@example.invalid>'
    mail['To'] = 'reader@example.invalid'
    mail['Subject'] = 'Synthetic large attachment preview'
    mail['Date'] = 'Mon, 09 Nov 2026 09:00:00 +0800'
    mail['Message-ID'] = '<reader-benchmark@example.invalid>'
    mail.set_content('A short saved body.\n保留附件原文，阅读正文不必载入附件。\n')
    mail.add_attachment(attachment, maintype='application', subtype='octet-stream', filename='synthetic-large.bin')
    mail.set_boundary('mailcairn-reader-benchmark')
    raw = mail.as_bytes()
    with tempfile.TemporaryDirectory(prefix='mailcairn-reader-') as folder:
        folder = Path(folder)
        path = folder / 'synthetic.eml'
        path.write_bytes(raw)
        store = Store(folder / 'archive.sqlite3')
        receipt = store.import_file(path)
        assert receipt['added'] == 1 and receipt['skipped'] == 0
        expected = store.message(1, raw=True)
        assert expected.pop('raw') == raw
        samples = []
        for _ in range(args.repeats):
            tracemalloc.start()
            start = time.perf_counter()
            result = store.message(1)
            elapsed = time.perf_counter() - start
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            assert result == expected
            samples.append({'seconds': round(elapsed, 6), 'python_peak_bytes': peak})
        saved = store.message(1, raw=True)
        assert saved['raw'] == raw
        assert get_attachment(saved['raw'], saved['attachments'][0]['index']) == attachment
    assert hashlib.sha256((source / 'mailcairn/store.py').read_bytes()).hexdigest() == code_hash
    report = {'status': 'passed', 'version': __version__, 'store_sha256': code_hash,
        'benchmark_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version,
        'fixture': {'synthetic_only': True, 'raw_bytes': len(raw), 'raw_sha256': hashlib.sha256(raw).hexdigest(), 'attachment_bytes': len(attachment)},
        'samples': samples, 'median_seconds': statistics.median(s['seconds'] for s in samples),
        'max_python_peak_bytes': max(s['python_peak_bytes'] for s in samples),
        'metadata_body_raw_attachment_exact': True,
        'limits': ['Saved plain-text preview only; HTML compatibility rederivation still loads original MIME.',
            'Import and fixture creation excluded; cached local reads, not browser or network timing.',
            'tracemalloc measures Python allocations, not SQLite native memory or total process RSS.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
