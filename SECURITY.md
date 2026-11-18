# Security and privacy

MailCairn is a local, single-user archive application. Its security boundary assumes you trust the operating system, Python installation, browser and other local software running as you. It is not a hardened multi-user server or an encrypted vault.

Source launches use your installed Python; the Windows 64-bit portable desktop candidate includes Python 3.13.17 and native runtime components. The candidate is unsigned and has not been validated on a clean second machine. Its component inventory and separate notices are documented in the [desktop runtime audit](docs/desktop-dependencies.md) and [runtime notice directory](licenses/desktop/README.txt). An inventory/license check is not a security certification.

## Data flow

The browser transfers selected files to a Python HTTP server bound only to `127.0.0.1`. The server writes a temporary local upload, parses it and stores original messages plus derived search data in SQLite. Optional mailbox connections add outbound IMAP: Gmail/ordinary IMAP use TLS with normal certificate validation; Proton connects to its local Bridge using STARTTLS and a certificate fingerprint pinned before authentication. The Bridge itself contacts Proton. MailCairn has no telemetry endpoint, remote font or CDN. Email HTML becomes plain text; message scripts, remote images and tracking pixels are not fetched.

Mailbox connection passwords pass through the authenticated loopback POST endpoint, not a URL. Windows can remember them encrypted with the current user's DPAPI when a round-trip capability probe succeeds; other platforms and restricted Windows contexts retain them only in process memory. `.mailcairn-credentials.json` contains protected credential blobs, and `.mailcairn-sync.json` contains account configuration and progress. Keep both private: configuration includes addresses and hostnames, while DPAPI does not protect credentials from malware running as the same OS user. No password, token or raw server authentication response should appear in connection API output or logs. Neither sidecar is included in the SQLite backup; reconnect after restoring into a new directory.

Bridge certificate pinning trusts the first certificate presented on literal loopback, then rejects changes; it is not public-CA authentication of the first connection. A malicious local process remains outside the security boundary. Certificate validation stays enabled for remote Gmail and generic IMAP endpoints.

The initial UI connects INBOX and checks every five minutes while the local application runs. It uses read-only mailbox selection and non-marking message fetches, with no source deletion, flag update or SMTP send. Disconnect removes connection state/credentials while retaining archived messages. Quitting stops network readers before releasing the archive lock. This is not continuous coverage while the computer sleeps or the application is closed. Proton Free/browser sessions do not substitute for paid Bridge access; Gmail OAuth is not implemented in this connector.

Reading attachments is deliberately a download operation. Once you open a file in another application, that application's behavior and network access apply. An archived email can contain a malicious attachment even when MailCairn itself only presents inert text.

English/Simplified Chinese switching is local interface rendering, not a translation service. It does not send mail to a model or external API and does not translate original message content, filenames or opaque technical details. Language and reading preferences contain no mail and are stored in the browser, separately from archive backups. The desktop entry keeps only a preferred local port in `.mailcairn-desktop.json`; changing ports can change the browser preference store.

## Local access controls

Each process generates a temporary launch token. The launch URL carries it in its fragment, and the UI exchanges it for an HttpOnly, SameSite=Strict cookie. APIs require the session; mutating requests also require a local request header. The server checks Host/Origin, rejects cross-site access, does not enable CORS, uses a restrictive content security policy and serves only an explicit static-file allowlist. Request URLs and search queries are not logged to the terminal.

While running, the archive directory contains `.mailcairn-instance.json` with its local port and session token. Keep this file and any `.mailcairn-instance-*.tmp` files private; they are excluded from source releases. On Windows they inherit the directory's permissions. The launcher only consults this record after archive-lock contention, then verifies the authenticated archive identity directly over loopback without proxies or redirects. A stale record alone never grants access or prevents normal startup. Graceful shutdown removes the current process's record; the next startup replaces an abandoned record.

Do not expose the port through a reverse proxy, tunnel, LAN bind or public hosting service. Do not publish the launch link. These controls reduce browser-origin risks; they do not protect against a malicious local process or compromised browser extension with sufficient privileges.

## Storage and recovery

- The SQLite archive, upload temporary files, backup snapshots, exports and downloaded attachments are **unencrypted**. Use OS disk encryption, private directory permissions and protected backups.
- The original input file is not modified. A temporary upload is removed after processing, with leftover named uploads cleaned up on the next normal startup after the archive lock is acquired. Secure erasure of storage sectors is not guaranteed.
- Deleting a browser tab or ending a session does not remove the persistent archive. The app stores messages, derived body text, addresses, attachment names and original import filenames. Some error text may reflect source metadata.
- Use the backup download for a consistent snapshot. A raw copy of a live SQLite file without its WAL may be incomplete. Restore stages and validates SQLite integrity, raw hashes, FTS and import receipts before atomic publication into a new archive path. It refuses an existing target, including one created during validation. The destination filesystem must support hard links; unsupported filesystems fail without publishing a partial archive.
- The backup includes stored mail and receipts, not mailbox connection settings, sync cursors or credentials. Copying an entire data directory is different: it can include private sidecars and session metadata. Do not publish it or treat it as a sanitized source bundle.
- The integrity operation separately checks raw-message hashes, SQLite integrity, the search index and receipt counts/references. A matching SHA-256 only establishes correspondence with the stored digest. It does not establish source authenticity, legal provenance or completeness against the remote mailbox.

The desktop **Restore backup…** action creates a distinct destination folder; **Open archive folder…** opens an existing archive. The current owned service is retired only after the replacement starts successfully. Desktop shutdown waits for accepted requests and current database work before releasing the archive lock; a window reusing another instance does not stop that instance when closed.

## Input limits

The default upload limit is 20 GiB and the default single-message limit is 32 MiB. MIME traversal is bounded to 30 levels and 500 parts, and search/preview text is limited to 1,000,000 characters per message. Oversized messages and parsing failures are recorded in import receipts. A malformed MBOX that has ambiguous envelope boundaries cannot be repaired reliably by a generic parser; keep the source export.

The HTTP service caps request workers at 16 and simultaneous archive reads/downloads at four. Headers have a 10-second absolute deadline; uploads have a 30-second socket timeout and a minimum average transfer rate after a grace period. Ambiguous request-body framing is rejected. These limits reduce resource abuse but do not make a local Python server suitable for internet exposure.

Connection creation requires an authenticated session, the local mutation header, `application/json` and a body no larger than 16 KiB. Duplicate JSON keys, malformed UTF-8 and non-object JSON are rejected. IMAP reads have timeouts, bounded UID windows and message-size limits. Oversized or failed sync messages stop cursor advancement before that item; a successful archive commit can be retried after a state-file failure, with exact-byte deduplication preserving already saved mail.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature on the original publishing repository if it is enabled, or email **yuyuio123@protonmail.com**. Public reports should contain only a high-level description until a private channel is established. Do not attach real mail, real backups, credentials or launch tokens.

The release has automated and browser validation documented in [test results](docs/test-results.md), but has not undergone an independent security audit. There is no promised security-support SLA.
