# Release checklist

This is a repeatable release procedure, not a claim that every item has already passed. Record actual results, versions, date, dataset size and remaining limitations in [test-results.md](test-results.md). Preparing a source release does not publish it or establish product-market fit.

## Functionality and recovery

- [ ] Start from the README command in a clean directory with Python 3.11+ and FTS5; confirm the initial archive is empty.
- [ ] Import synthetic EML and MBOX fixtures. Check multilingual text, HTML-only mail, dates, MIME attachments and readable warnings.
- [ ] Re-import identical data and confirm exact duplicates; retain different raw bytes sharing one Message-ID.
- [ ] Search bodies and attachment names; exercise sender, inclusive date and attachment filters, paging and no-result states.
- [ ] Exercise unsupported/empty files, malformed records, oversized records, partial results and reversed date ranges.
- [ ] Cancel an import; confirm committed messages remain and re-import completes without exact duplicates. Restart during an unfinished import and check `interrupted` recovery.
- [ ] Download and reopen original EML, attachment, filtered MBOX and complete JSON receipt. Reconcile receipt outcomes with stored messages; do not interpret totals as provider completeness.
- [ ] Download a backup, restore into a new data directory, restart, search and download an attachment. Confirm restore refuses an existing archive and rejects corrupt/incompatible snapshots.
- [ ] Run archive verification and inspect SQLite, raw hash and search-index results.
- [ ] Measure a stated synthetic scale before making performance claims. Record wall time, message count, bytes, Python/SQLite versions and environment; do not call a configured maximum a tested capacity.

## Security and interface

- [ ] Run `python -m unittest discover -s tests -v` from the project root and preserve the actual outcome.
- [ ] Confirm loopback-only binding, launch-token session behavior, unauthenticated API rejection, cross-origin/Host rejection and mutation-header checks.
- [ ] Confirm mail HTML and remote image URLs remain inert; inspect network requests for unintended remote activity.
- [ ] Check desktop and narrow layouts in a real browser: keyboard navigation, import progress, results, reader, history, errors and downloads.
- [ ] Capture `docs/screenshots/desktop.png` and `docs/screenshots/mobile.png` using synthetic data only. The latter denotes a narrow viewport, not phone network support.
- [ ] Inspect screenshots for clipped controls, private paths, session tokens and sensitive content; do not publish launch URLs.

## Source and rights

- [ ] Check README links and CLI examples against current behavior; update Chinese and English limitations together.
- [ ] Keep LICENSE identical to the official text and verify its SHA-256 against [dependency-audit.md](dependency-audit.md).
- [ ] Include NOTICE, COMMERCIAL.md, CONTRIBUTING.md and SECURITY.md; preserve the source-available/noncommercial distinction.
- [ ] Confirm the actual publisher identity/contact route before offering commercial agreements. Do not fabricate either.
- [ ] Audit new code, dependencies, runtime bundles, fonts/icons and contributor rights. Do not add a permissive license badge to the project.
- [ ] Exclude live data directories, `.upload-*`, SQLite/WAL/SHM files, lock files, caches, secrets, local logs and real exported email from the release.
- [ ] Retain explicitly synthetic fixtures, source, launch scripts, tests, workflow and documentation; review the final file inventory.
- [ ] Preserve honest research caveats and competitor successes. Do not claim validated demand, revenue or enterprise/compliance readiness.

## Publication

- [ ] Verify the intended repository and publishing account against the user's authorization before any external write.
- [ ] Publish only the reviewed source package and factual release notes; disclose remaining untested platforms or scale limits.
- [ ] Confirm the resulting repository/release URL and commit or artifact identity after publication. If not published, describe it as a prepared local release.
