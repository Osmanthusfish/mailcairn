"""Bounded mbox/EML reading and inert MIME-to-text extraction.

Raw message bytes are kept separately from the derived text index. No HTML is
ever returned for rendering, and no URL in a message is fetched.
"""
from __future__ import annotations

from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import re

ENVELOPE = re.compile(rb"^From [^\r\n]+ +(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2} \d{2}:\d{2}(?::\d{2})?[^\r\n]*\d{4}[^\r\n]*\r?\n?$")
MAX_TEXT = 1_000_000
HTML_TEXT_WARNING = "HTML converted to inert text; layout and inline images omitted"


class MailFormatError(ValueError):
    pass


def records(path, name, max_bytes=32 * 1024 * 1024, cancelled=lambda: False):
    """Yield ordinal, raw offset, length, bytes-or-None. None means oversized.

    mboxo/mboxrd envelope lines are excluded; all other bytes are retained.
    Readline is capped so a malicious single line cannot consume all memory.
    """
    with open(path, "rb") as stream:
        if name.lower().endswith(".eml"):
            data = stream.read(max_bytes + 1)
            size = path.stat().st_size
            yield 1, 0, size, data if size <= max_bytes else None
            return
        first = stream.readline(1024 * 1024)
        if not first:
            raise MailFormatError("The file is empty. Select an extracted .mbox or .eml file.")
        if not ENVELOPE.fullmatch(first):
            raise MailFormatError("No standard MBOX envelope found. Unzip your export first. PST, ZIP and mboxcl files are not supported; individual messages must use .eml.")
        offset = stream.tell()
        ordinal, length = 1, 0
        buf = bytearray()
        line_start = True
        while True:
            if cancelled():
                return
            pos = stream.tell()
            line = stream.readline(1024 * 1024)
            is_boundary = line_start and bool(ENVELOPE.fullmatch(line))
            if not line or is_boundary:
                raw = bytes(buf) if length <= max_bytes else None
                if raw is not None:
                    header = re.split(rb"\r?\n\r?\n", raw, maxsplit=1)[0]
                    if re.search(rb"(?im)^Content-Length\s*:", header):
                        raise MailFormatError("Content-Length-based MBOX variants (mboxcl/mboxcl2) are not supported. Export as mboxo/mboxrd or individual EML files first.")
                yield ordinal, offset, length, raw
                if not line:
                    return
                ordinal += 1
                offset = stream.tell()
                length = 0
                buf = bytearray()
            else:
                length += len(line)
                if length <= max_bytes:
                    buf.extend(line)
                else:
                    buf.clear()
            line_start = line.endswith(b"\n")


class InertText(HTMLParser):
    """Extract readable flow text without retaining HTML source indentation.

    Separators are pending until visible text arrives, so nested layout tables
    cannot manufacture hundreds of empty lines. Preformatted data is retained
    verbatim; this normalization is never applied to a text/plain MIME part.
    """
    PARAGRAPHS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"}
    BLOCKS = {"div", "tr", "li", "table", "section", "article", "header", "footer",
              "ul", "ol", "dl", "dt", "dd", "address", "hr"}
    HIDDEN = {"script", "style", "title"}
    HEAD_ELEMENTS = {"base", "basefont", "bgsound", "link", "meta", "title",
                     "script", "style", "noscript", "noframes", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.hidden = 0
        self.in_head = False
        self.preformatted = 0
        self.pending_break = 0
        self.pending_space = False

    def boundary(self, lines):
        self.pending_break = max(self.pending_break, lines)
        self.pending_space = False

    def append_text(self, text):
        if self.output:
            previous = self.output[-1]
            if self.pending_break:
                trailing = 2 if previous.endswith("\n\n") else int(previous.endswith("\n"))
                separator = "\n" * max(0, self.pending_break - trailing)
                if separator:
                    self.output.append(separator)
            elif self.pending_space and not previous.endswith((" ", "\n", "\r", "\t")):
                self.output.append(" ")
        self.pending_break = 0
        self.pending_space = False
        self.output.append(text)

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head = True
            return
        if tag in self.HIDDEN:
            self.hidden += 1
        if self.hidden:
            return
        # </head> and even <body> are optional in HTML. End the metadata
        # section when body content begins, without ending script/style hiding.
        if self.in_head and tag not in self.HEAD_ELEMENTS and tag != "html":
            self.in_head = False
        if self.in_head:
            return
        if tag == "pre":
            self.boundary(2)
            self.preformatted += 1
        elif tag == "br":
            if self.preformatted:
                self.append_text("\n")
            else:
                # Two explicit breaks retain a paragraph; layout nesting only
                # requests a separator and does not accumulate empty lines.
                self.boundary(min(2, self.pending_break + 1))
        elif not self.preformatted:
            if tag in self.PARAGRAPHS:
                self.boundary(2)
            elif tag in self.BLOCKS:
                self.boundary(1)
            elif tag in ("td", "th"):
                self.pending_space = True

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False
            return
        if tag in self.HIDDEN:
            self.hidden = max(0, self.hidden - 1)
            return
        if self.hidden or self.in_head:
            return
        if tag == "pre":
            self.preformatted = max(0, self.preformatted - 1)
            self.boundary(2)
        elif not self.preformatted:
            if tag in self.PARAGRAPHS:
                self.boundary(2)
            elif tag in self.BLOCKS:
                self.boundary(1)
            elif tag in ("td", "th"):
                self.pending_space = True

    def handle_data(self, data):
        if self.hidden or not data:
            return
        if self.in_head:
            if not data.strip():
                return
            self.in_head = False
        if self.preformatted:
            self.append_text(data)
            return
        text = re.sub(r"[ \t\r\n\f]+", " ", data)
        if text.startswith(" "):
            self.pending_space = True
        content = text.strip(" ")
        if content:
            self.append_text(content)
        if text.endswith(" "):
            self.pending_space = True


def flatten(msg):
    pending = [(msg, 0)]
    parts = []
    while pending:
        part, depth = pending.pop()
        if depth > 30 or len(parts) >= 500:
            raise MailFormatError("MIME nesting or part count exceeds the safety limit (30 levels / 500 parts).")
        parts.append(part)
        # An attached message is one downloadable attachment, not body text.
        if part.is_multipart() and part.get_content_type() != "message/rfc822" and not part.get_filename():
            pending.extend((child, depth + 1) for child in reversed(part.get_payload()))
    return parts


def attachment_bytes(part):
    payload = part.get_payload(decode=True)
    if payload is not None:
        return payload
    if isinstance(part.get_payload(), list):
        return b"\r\n".join(child.as_bytes(policy=policy.SMTP) for child in part.get_payload())
    return str(part.get_payload()).encode("utf-8", "replace")


def parse_message(raw):
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    if not any(msg.get(h) for h in ("From", "To", "Subject", "Date", "Message-ID")):
        raise MailFormatError("No recognizable email headers; the original span was not imported.")
    warnings = []
    plain, rich, attachments = [], [], []
    for index, part in enumerate(flatten(msg)):
        filename = part.get_filename()
        if filename or part.get_content_disposition() == "attachment" or part.get_content_type() == "message/rfc822":
            attachments.append({"index": index, "name": str(filename or ("attached-message.eml" if part.get_content_type() == "message/rfc822" else f"attachment-{index}")), "type": part.get_content_type(), "size": len(attachment_bytes(part))})
        elif part.get_content_type() in ("text/plain", "text/html"):
            data = part.get_payload(decode=True) or b""
            try:
                text = data.decode(part.get_content_charset() or "utf-8", "replace")
            except LookupError:
                text = data.decode("utf-8", "replace")
                warnings.append("Unknown charset; decoded with UTF-8 replacement")
            if part.get_content_type() == "text/plain":
                plain.append(text)
            else:
                parser = InertText()
                parser.feed(text)
                parser.close()
                rich.append("".join(parser.output))
        # Transfer-decoding (not just parsing) can append defects, e.g. malformed
        # base64 padding. Capture these after consuming the payload.
        warnings.extend(type(d).__name__ for d in part.defects)
    body = "\n\n".join(plain or rich).replace("\x00", "")
    if not plain and rich:
        warnings.append(HTML_TEXT_WARNING)
    if len(body) > MAX_TEXT:
        warnings.append("Search/preview text limited to 1,000,000 characters; full original retained")
        body = body[:MAX_TEXT]
    date_header = str(msg.get("Date", ""))
    date_iso = ""
    timestamp = 0
    try:
        dt = parsedate_to_datetime(date_header)
        if dt is not None:
            date_iso = dt.date().isoformat()
            # A missing timezone must not silently inherit the machine's zone.
            if dt.tzinfo is None:
                from datetime import timezone
                dt = dt.replace(tzinfo=timezone.utc)
                warnings.append("Date has no timezone; UTC used for sort order")
            timestamp = int(dt.timestamp())
    except (ValueError, TypeError, OverflowError, OSError):
        pass
    if not date_iso:
        warnings.append("Missing or invalid date; date filters exclude this message")
    return {
        "subject": str(msg.get("Subject", "")) or "(No subject)",
        "sender": str(msg.get("From", "")),
        "recipients": ", ".join(str(v) for h in ("To", "Cc", "Bcc") for v in msg.get_all(h, [])),
        "date_header": date_header, "date_day": date_iso, "sent_at": timestamp,
        "message_id": str(msg.get("Message-ID", "")),
        "labels": str(msg.get("X-Gmail-Labels", "")), "body": body,
        "attachment_names": "\n".join(a["name"] for a in attachments),
        "attachments": attachments, "warnings": sorted(set(warnings)),
    }


def get_attachment(raw, index):
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    parts = flatten(msg)
    if index < 0 or index >= len(parts):
        raise MailFormatError("Attachment not found.")
    part = parts[index]
    if not (part.get_filename() or part.get_content_disposition() == "attachment" or part.get_content_type() == "message/rfc822"):
        raise MailFormatError("Not an attachment.")
    return attachment_bytes(part)
