# Architecture

MailCairn is a single-user Python 3.11+ application with native HTML/CSS/JavaScript and SQLite FTS5. The source needs no application-package installation or compilation. Optional IMAP connections now feed the local archive while its process runs; file import remains independent of account access. Runtime measurements and verified platforms are documented separately in [test results](test-results.md).

## Components and data flow

```text
Browser file selection
  → authenticated loopback HTTP upload
  → temporary file + whole-file SHA-256
  → bounded MBOX/EML record reader
  → MIME metadata and inert text extraction
  → SQLite transaction: raw message + FTS entry + receipt item + counters
  → search / original EML / attachment / filtered MBOX / snapshot backup
```

| Component | Responsibility |
| --- | --- |
| `app.py` | CLI configuration, OS archive lock, optional restore, interrupted-import recovery, temporary-upload cleanup, browser launch and shutdown. |
| `mailcairn/parse.py` | MBOX envelope detection, size limits, MIME traversal, metadata extraction, text-only HTML conversion and attachment decoding. |
| `mailcairn/store.py` | Schema, transactions, exact-byte deduplication, search, import receipts, export, backup and integrity verification. |
| `mailcairn/server.py` | Loopback HTTP interface, session checks, upload streaming, asynchronous import/verification jobs and downloads. |
| `mailcairn/sync.py` | Scheduled one-way ingestion, connection state, durable UID progress and coordination with the archive writer lock. |
| `mailcairn/imap_client.py` | Bounded read-only IMAP fetches; remote certificate validation and local Proton Bridge certificate pinning. |
| `mailcairn/credentials.py` | Current-user Windows DPAPI after a successful capability probe; explicitly memory-only credentials otherwise. |
| `mailcairn/static/` | Native browser UI, transfer/indexing progress, search/filter state, reader, import history and recovery guidance. |
| `mailcairn/static/startup.js` | Independent pre-business-script recovery; queues early failures until DOM readiness, exposes bilingual full-page reload, settles on ready/handled startup and preserves the unexchanged session fragment. No mail or credentials are stored here. |

## Storage and import semantics

`data/archive.sqlite3` is the default store. `messages` keeps raw RFC message bytes, SHA-256, decoded metadata/body, attachment descriptors and warnings. `mail_fts` is an external-content FTS5 index maintained on insertion. `imports` stores file-level receipt metadata; `import_items` stores every processed recognized record's ordinal, byte offset/length, outcome, reason, message row and available hash. The application identifier is `0x4D434152`, and the schema version is 1.

The uploader streams to a named `.upload-*` file in the data directory, hashes the whole file and rejects unsupported extensions, empty bodies and configured size violations. Its free-space check is an estimate, not a guarantee that a large archive will fit. One import or verification operation runs at a time. The upload must finish before indexing starts; cancellation during transfer differs from cancellation during indexing.

MBOX parsing recognizes conventional mboxo/mboxrd envelope lines and excludes those separator lines from stored message bytes. It preserves other bytes, including existing MBOX escape characters. Content-Length-based mboxcl/mboxcl2 is rejected. A damaged or ambiguous boundary can prevent correct recognition; receipt totals cannot establish the source provider's true message count.

Messages, their receipt items, FTS insertions and running counters commit atomically in bounded batches: at most 100 records, a 4 MiB raw-byte threshold or 250 ms elapsed between record boundaries. A single record can exceed the byte/time threshold within the configured per-message limit. SQLite retains FULL synchronous durability. Progress is reported only after a successful commit; an interrupted uncommitted batch is replayed on re-import. A raw-byte SHA-256 uniqueness constraint identifies exact duplicates. Message-ID is metadata, not a uniqueness key. Oversized records are counted as skipped without retaining their raw spans; malformed messages can also be skipped. Keep the source export whenever an import is partial, failed or interrupted.

Normal cancellation stops at a record boundary after committing already processed records in the current batch. A database failure or abrupt process termination rolls back the uncommitted batch; all earlier committed batches remain. On restart, unfinished imports become `interrupted`; users re-import the original file and exact duplicates are skipped. This is safe replay, not a saved byte-position resume. The OS advisory lock prevents simultaneous processes using the same archive. SQLite uses WAL, so a live directory may also contain `-wal` and `-shm` files.

## Optional mailbox ingestion

The initial interface configures INBOX, with a five-minute schedule while the server remains running and explicit sync/pause/resume/disconnect controls. Gmail uses an eligible app password; generic IMAP uses the provider's supported credential; Proton uses paid local Bridge credentials. This version implements neither Gmail OAuth nor Proton Free automatic access. Mailbox credentials are separate from the browser session token and are never inferred from existing browser sign-in.

The scheduler shares the import/verification writer lock. A cycle selects read-only, searches bounded UID ranges and fetches original bytes without setting `\\Seen`. Progress is keyed by connection and UIDVALIDITY; a validity change starts a safe rescan. Each fetched message goes through the existing EML parser/store and receives a receipt. Cursor state advances only after durable added/duplicate confirmation; a subsequent state-write failure replays the record safely. Failed/oversized records stop before the failing UID. Source deletions do not remove archived messages. There is no SMTP sender or source mutation operation.

The UI supplies INBOX; the backend supports one configured ASCII folder per connection, not discovery or simultaneous multi-folder synchronization. `.mailcairn-sync.json` stores connection configuration and progress; `.mailcairn-credentials.json` stores remembered Windows DPAPI blobs, never plaintext passwords. Platforms or execution contexts without working DPAPI keep secrets in memory. These sidecars are not part of SQLite backup/restore. Mail remains unencrypted in the archive. The HTTP API returns public connection fields and fixed operational explanations, not credentials or raw IMAP responses. Connection POST bodies are bounded to 16 KiB and require session/origin/mutation-header checks. See [security](../SECURITY.md) and [provider research](mail-sync-research.md).

## Search and reading

FTS5 `unicode61` indexes subject, sender, recipients, decoded body and attachment filenames. Ordinary search splits at most 30 word tokens and combines them with AND; it does not expose arbitrary FTS or Gmail query syntax. Queries containing CJK characters use literal substring checks instead, which can be slower. Search returns 50 rows per page, newest first. Sender, inclusive date range, attachment presence and import-origin filters compose with text search.

The date filter uses the calendar date from the original Date header, without converting that date to the local timezone. A missing timezone uses UTC for sort order and emits a warning; invalid/missing dates are excluded by date filters. At most 1,000,000 decoded body characters are retained for preview/indexing. Raw mail remains intact; attachment contents are not full-text indexed.

MIME traversal is bounded to 30 levels and 500 parts. Plain-text alternatives are preferred. HTML is converted to text; mail-controlled values enter the UI as text rather than executable HTML. Attachments are decoded from stored raw MIME on demand, then downloaded rather than rendered in the reader. Attached messages can be downloaded as EML; reserialization of such MIME attachments is distinct from downloading the byte-exact top-level original EML.

## Reading room and browser state

The bilingual UI exposes direct EN/中文 buttons and reading preferences for appearance, accent, type size, density, shortcuts and motion. Explicit UI bindings update operation labels and counts in place; mail text and filenames are never translated. Preferences remain browser-local. Reduced motion overrides application motion, including Canvas and paper tilt.

Preferences use the versioned local-storage key `mailcairn.reading-room.v1`, scoped to the browser origin. They contain presentation choices, not mail or file paths, and are not part of the SQLite archive or backup. A whitelist validates enum values and boolean switches. Missing, malformed or inaccessible stored preferences fall back to defaults. Failed writes leave changes active for the current visit and display a storage-unavailable notice. Storage events synchronize preferences across tabs of the same origin.

Ctrl/⌘ K opens the Commands dialog. Its arrow keys move between available commands; Enter invokes the selected command. With focus on a message row, ↑/↓ and Home/End navigate and read messages within the current results page. The single-key-shortcuts preference controls `/`, `i`, `g`, `h`, `,` and `?`; it does not disable Ctrl/⌘ K or focused-list navigation. Single-key actions are suppressed in text fields and open dialogs. These controls use native buttons and dialogs rather than an application-wide synthetic keyboard mode.

Canvas effects are finite, local and event-triggered at natural empty-archive entrance and successful import. Standalone decorative scenes and their replay/preview controls have been removed. Per-run particle and backing-store budgets remain bounded; visibility, viewport, preference and lifecycle changes stop obsolete work. Real navigation, import receipts and reader surfaces use cancellable CSS/Web Animations feedback without delaying access to mail. Counts and lists refresh after each committed file, and review navigation awaits a fresh archive state and guards against closed dialogs/new batches. There is no permanent animation loop, media download or rendering dependency.

## Backup, export and verification

The backup endpoint uses SQLite's backup API to create a consistent snapshot, then downloads it. Copying only a live database file can omit WAL changes. Restore is available through CLI startup or the native desktop controller, always into a new archive path. It stages a consistent snapshot in the destination directory and checks application/schema identifiers, SQLite integrity, raw-message hashes, FTS consistency and receipt counts/references before publishing it. Publication uses an atomic, no-overwrite hard link; a concurrently created target is preserved and validation failure leaves no partial archive. The destination filesystem must support hard links (for example NTFS on Windows); FAT/exFAT targets are not supported by this restore path. The source backup is unchanged.

Verification checks SQLite integrity, stored raw-message hashes, FTS consistency against external content, and receipt counts/references. Receipt JSON counters and items are read from one SQLite snapshot even while ingestion continues. It reports cancellation and mismatch IDs. It is not proof of provider export completeness, authorship or authenticity. Filtered MBOX export emits envelope separators and escapes unquoted `From ` lines; use original EML download when exact stored bytes matter. The JSON receipt download includes all record items; the interactive issue summary is capped at 200 entries.

## Local security boundary

The server only binds `127.0.0.1`. A random session token in the launch URL fragment is exchanged for an HttpOnly, SameSite=Strict cookie. Requests require an exact loopback Host match and validate Origin when supplied and reject cross-site fetch metadata; state-changing requests also require a custom header. The browser removes the launch fragment after exchanging it. Response headers restrict content loading and framing. Private request URLs are not logged to the console. HTTP work is bounded to 16 request workers and four simultaneous archive reads/downloads; overload can close a socket or return 503. Job polling remains outside the heavy-read limit. Request headers have a 10-second absolute deadline. Uploads use a 30-second socket timeout and, after a 30-second grace period, a 1 KiB/s minimum average rate. Duplicate Content-Length and Transfer-Encoding framing are rejected. These are local resource safeguards, not a public-server deployment guarantee.

This boundary protects a local session from common browser-origin mistakes; it does not isolate the archive from malware, another process with filesystem access, or someone who obtains the session token. The app does not encrypt archives, temporary files or downloads. See [SECURITY.md](../SECURITY.md) for the complete threat model.

The service is not intended for public deployment, multi-user access, LAN sharing, two-way mailbox synchronization or forensic custody. Its optional one-way polling runs only while the local process is open. A responsive layout is a narrow-window feature; a separate phone cannot access this loopback server.

## Typography and physical interactions

Local variable TTF fonts are served from an exact two-file allowlist with `font/ttf`; font notices remain OFL. No remote font requests are made. A finite CSS paper fan and bounded result entrances complement a 700ms Web Animations API reader hinge and one 720ms textless decorative sheet transfer. It animates the real reader, never a cloned mail body. Rapid selection cancels the previous animation; lifecycle and reduced-motion changes stop it. Unsupported WAAPI leaves a fully functional static reader. Result text remains opaque throughout animation.

The envelope has four CSS 3D sheets, a folding flap and seal; its 2400ms sequence is cleaned up at2500ms. Cancellation generations prevent a late network response from resurrecting cancelled motion. Back while loading invalidates the reader request. Decorative transfer nodes are ARIA-hidden, pointer-transparent, removed on completion/cancellation and never contain private mail text.
