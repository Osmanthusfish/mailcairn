from email import policy
from email.message import EmailMessage
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mailcairn.parse import HTML_TEXT_WARNING, MailFormatError, get_attachment, parse_message, records
from mailcairn.store import Store
from tests.helpers import ENVELOPE, mbox, message


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "inbox.mbox"
        self.addCleanup(self.temp.cleanup)

    def read(self, data, **kwargs):
        self.path.write_bytes(data)
        return list(records(self.path, self.path.name, **kwargs))

    def test_standard_envelopes_and_offsets(self):
        first, second = message(), message("Second", message_id="<second@example.com>", crlf=True)
        data = mbox(first, second)
        result = self.read(data)
        self.assertEqual(len(result), 2)
        for ordinal, offset, length, raw in result:
            self.assertEqual(raw, data[offset:offset + length])
            self.assertEqual(ordinal, result.index((ordinal, offset, length, raw)) + 1)
        self.assertEqual(result[0][3], first)
        self.assertEqual(result[1][3], second)

    def test_body_from_lines_do_not_split_mail(self):
        raw = message(body="From the station, walk north.\n>From archive@example.com Mon Nov 09 09:00:00 2026\n>>From a quoted line\nEnd.")
        result = self.read(mbox(raw))
        self.assertEqual(len(result), 1)
        self.assertIn(b"From the station", result[0][3])
        self.assertIn(b">From archive@", result[0][3])

    def test_final_message_without_newline(self):
        raw = message().rstrip(b"\n")
        result = self.read(ENVELOPE + raw)
        self.assertEqual(result[0][3], raw)
        self.assertEqual(result[0][2], len(raw))

    def test_oversized_record_skips_and_continues(self):
        large = message(body="x" * 5000)
        small = message("Small", message_id="<small@example.com>")
        result = self.read(mbox(large, small), max_bytes=1000)
        self.assertIsNone(result[0][3])
        self.assertEqual(result[0][2], len(large))
        self.assertEqual(result[1][3], small)

    def test_single_oversized_line_is_bounded(self):
        # No MIME encoder: this is intentionally one very long physical line.
        large = b"Subject: large\n\n" + b"z" * 2_100_000 + b"\n"
        small = message("After giant line")
        result = self.read(mbox(large, small), max_bytes=1024)
        self.assertEqual(len(result), 2)
        self.assertIsNone(result[0][3])
        self.assertEqual(result[1][3], small)

    def test_eml_preserves_bytes_exactly(self):
        raw = message(crlf=True).rstrip(b"\r\n")
        self.path.write_bytes(raw)
        result = list(records(self.path, "mail.eml"))
        self.assertEqual(result, [(1, 0, len(raw), raw)])

    def test_empty_and_non_mailbox_rejected(self):
        for data in (b"", b"PK\x03\x04a zip file", b"not an mbox\n"):
            with self.subTest(data=data):
                with self.assertRaises(MailFormatError):
                    self.read(data)

    def test_cancel_before_reading_body(self):
        self.assertEqual(self.read(mbox(message()), cancelled=lambda: True), [])

    def test_pipermail_sender_with_spaces_and_double_space_separator(self):
        envelope = b"From maintainer at example.com  Tue Jan  1 12:34:56 2019\n"
        raw = message("Announcement")
        result = self.read(envelope + raw + envelope + raw)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][3], raw)

    def test_content_length_mbox_variant_is_explicitly_rejected(self):
        raw = b"Subject: mboxcl record\nContent-Length: 32\n\nSome content\n"
        with self.assertRaisesRegex(MailFormatError, "mboxcl"):
            self.read(ENVELOPE + raw)
        # The header is valid in standalone EML: no MBOX boundary inference.
        self.path.write_bytes(raw)
        self.assertEqual(list(records(self.path, "mail.eml"))[0][3], raw)


class MimeTests(unittest.TestCase):
    @staticmethod
    def html_message(html):
        return b"Subject: Synthetic HTML layout\nContent-Type: text/html; charset=utf-8\n\n" + html.encode("utf-8")

    def test_multipart_alternative_prefers_plain_text(self):
        parsed = parse_message(message(body="The plain version.", html="<p>Different HTML version.</p>"))
        self.assertIn("The plain version", parsed["body"])
        self.assertNotIn("Different HTML", parsed["body"])

    def test_html_is_inert_text_and_excludes_active_content(self):
        raw = b"From: notice@example.com\nSubject: HTML notice\nContent-Type: text/html; charset=utf-8\n\n<head><style>secret-style</style></head><script>alert('secret-script')</script><p>Visible receipt &amp; total</p><img src='https://tracking.example.com/pixel'><a href='javascript:alert(1)'>Read me</a>"
        parsed = parse_message(raw)
        self.assertIn("Visible receipt & total", parsed["body"])
        self.assertIn("Read me", parsed["body"])
        for hidden in ("secret-style", "secret-script", "tracking.example", "javascript:", "<p>"):
            self.assertNotIn(hidden, parsed["body"])
        self.assertTrue(any("HTML converted" in warning for warning in parsed["warnings"]))

    def test_html_layout_indentation_does_not_become_blank_pages(self):
        html = "<html><body>\n" + "  <table>\n <tbody>\n <tr>\n <td>\n" * 55
        html += "<h1>Archive notice</h1>\n<p>Hello <b>reader</b>.</p>\n<p>Keep this receipt.</p>"
        html += "\n </td>\n </tr>\n </tbody>\n </table>" * 55 + "</body></html>"
        body = parse_message(self.html_message(html))["body"]
        self.assertEqual(body, "Archive notice\n\nHello reader.\n\nKeep this receipt.")

    def test_optional_head_end_does_not_hide_visible_body(self):
        for body in ("<body><p>Visible mail</p></body>", "<p>Visible mail</p>", "Visible mail"):
            with self.subTest(body=body):
                html = '<html><head><meta charset="UTF-8">' + body + '</html>'
                self.assertEqual(parse_message(self.html_message(html))["body"], "Visible mail")

    def test_optional_head_end_retains_metadata_and_active_content_suppression(self):
        html = "<html><head><title>Hidden title</title><style>body:before {content:'Hidden style'}</style><script>document.write('<body>Hidden script')</script><meta charset='UTF-8'><body><h1>Visible heading</h1><p>Visible mail</p><style>Hidden later style</style><script>Hidden later script</script></body></html>"
        self.assertEqual(parse_message(self.html_message(html))["body"], "Visible heading\n\nVisible mail")

    def test_html_inline_words_cells_lists_and_explicit_breaks_stay_separate(self):
        html = "<div>Hello\n  <strong>careful</strong> reader.</div><table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td></tr></table><ul><li>One</li><li>Two</li></ul><p>Line<br>next<br><br>paragraph</p>"
        body = parse_message(self.html_message(html))["body"]
        self.assertEqual(body, "Hello careful reader.\nA B\nC D\nOne\nTwo\n\nLine\nnext\n\nparagraph")

    def test_html_preformatted_spacing_and_blank_lines_are_preserved(self):
        pre = "  column\tvalue\n\n\n    indented\n  end  "
        html = "<p>Before</p><pre>" + pre + "</pre><p>After</p>"
        body = parse_message(self.html_message(html))["body"]
        self.assertEqual(body, "Before\n\n" + pre + "\n\nAfter")
        self.assertEqual(parse_message(self.html_message("<pre>" + pre + "</pre>"))["body"], pre)

    def test_plain_text_spacing_is_unchanged_even_with_html_alternative(self):
        body = "  opening\n\n\n\n\tcolumn    value\n  closing  \n"
        mail = EmailMessage()
        mail["Subject"] = "Synthetic whitespace"
        mail.set_content(body)
        mail.add_alternative("<p>Different version</p>", subtype="html")
        parsed = parse_message(mail.as_bytes())
        self.assertEqual(parsed["body"], body)
        self.assertNotIn(HTML_TEXT_WARNING, parsed["warnings"])

    def test_unknown_charset_is_reported(self):
        raw = b"Subject: Odd charset\nContent-Type: text/plain; charset=x-not-real\n\nhello\xc3\xa9"
        parsed = parse_message(raw)
        self.assertEqual(parsed["body"], "helloé")
        self.assertTrue(any("Unknown charset" in warning for warning in parsed["warnings"]))

    def test_unicode_headers_filename_and_attachment_bytes(self):
        payload = "保修凭证\n有效期至 2028 年\n".encode()
        raw = message("咖啡机保修确认", sender="林晓 <lin@example.com>", attachment=("保修凭证.txt", payload), crlf=True)
        parsed = parse_message(raw)
        self.assertEqual(parsed["subject"], "咖啡机保修确认")
        self.assertIn("林晓", parsed["sender"])
        self.assertEqual(parsed["attachments"][0]["name"], "保修凭证.txt")
        self.assertEqual(get_attachment(raw, parsed["attachments"][0]["index"]), payload)

    def test_attached_message_download(self):
        outer = EmailMessage()
        outer["From"] = "alex@example.com"
        outer["Subject"] = "Forwarded booking"
        outer.set_content("The original booking is attached.")
        inner = EmailMessage()
        inner["From"] = "tickets@example.com"
        inner["Subject"] = "Original booking"
        inner.set_content("Private reference in attached mail.")
        outer.add_attachment(inner)
        raw = outer.as_bytes()
        parsed = parse_message(raw)
        self.assertEqual(len(parsed["attachments"]), 1)
        attachment = parsed["attachments"][0]
        self.assertEqual(attachment["type"], "message/rfc822")
        self.assertNotIn("Private reference", parsed["body"])
        saved = get_attachment(raw, attachment["index"])
        self.assertIn(b"Subject: Original booking", saved)

    def test_invalid_attachment_index_is_rejected(self):
        raw = message()
        for index in (-1, 0, 20):
            with self.subTest(index=index):
                with self.assertRaises(MailFormatError):
                    get_attachment(raw, index)

    def test_missing_and_naive_dates(self):
        missing = parse_message(message(date=None))
        self.assertEqual(missing["date_day"], "")
        self.assertTrue(any("Missing or invalid" in warning for warning in missing["warnings"]))
        naive = parse_message(message(date="Mon, 09 Nov 2026 09:00:00 -0000"))
        self.assertEqual(naive["date_day"], "2026-11-09")
        self.assertTrue(any("no timezone" in warning for warning in naive["warnings"]))

    def test_invalid_message_has_no_silent_success(self):
        with self.assertRaises(MailFormatError):
            parse_message(b"this is not an email\njust text")

    def test_deep_mime_is_rejected(self):
        outer = EmailMessage()
        outer["Subject"] = "Nesting limit"
        child = outer
        for _ in range(32):
            child.make_mixed()
            inner = EmailMessage()
            child.attach(inner)
            child = inner
        child.set_content("too deep")
        with self.assertRaises(MailFormatError):
            parse_message(outer.as_bytes())

    def test_decode_defects_are_reported(self):
        raw = b"Subject: Damaged content\nContent-Type: text/plain\nContent-Transfer-Encoding: base64\n\nSGVsbG8@\n"
        parsed = parse_message(raw)
        self.assertTrue(any("Base64" in warning for warning in parsed["warnings"]), parsed["warnings"])


class StoredHtmlPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.store = Store(self.folder / "archive.sqlite3")
        self.raw = MimeTests.html_message("\n  <p>Readable <b>message</b>.</p>\n <pre>  a\n\n\n  b</pre>")
        self.path = self.folder / "synthetic.eml"
        self.path.write_bytes(self.raw)
        self.legacy = "legacytoken\n" + "\n" * 300 + "  a\n\n\n  b"
        parsed = parse_message(self.raw)
        parsed["body"] = self.legacy
        # Simulate an archive imported by the previous parser, including its FTS.
        with patch("mailcairn.store.parse_message", return_value=parsed):
            self.store.import_file(self.path)

    def test_existing_html_reader_is_rederived_without_rewriting_source_or_index(self):
        preview = self.store.message(1)
        self.assertEqual(preview["body"], "Readable message.\n\n  a\n\n\n  b")
        self.assertIn(HTML_TEXT_WARNING, preview["warnings"])
        original = self.store.message(1, raw=True)
        self.assertEqual(original["raw"], self.raw)
        self.assertEqual(original["body"], self.legacy)
        self.assertEqual(self.store.search({"q": "legacytoken"})["total"], 1)

    def test_older_message_remains_readable_if_rederivation_fails(self):
        with patch("mailcairn.store.parse_message", side_effect=ValueError("synthetic parser failure")):
            self.assertEqual(self.store.message(1)["body"], self.legacy)

    def test_raw_download_does_not_reparse_message(self):
        with patch("mailcairn.store.parse_message", side_effect=AssertionError("must not parse")):
            self.assertEqual(self.store.message(1, raw=True)["raw"], self.raw)

    def test_plain_reader_uses_saved_text_without_reparsing(self):
        raw = message(body="  original\n\n\n\n  spacing")
        self.path.write_bytes(raw)
        self.store.import_file(self.path)
        with patch("mailcairn.store.parse_message", side_effect=AssertionError("must not parse")):
            self.assertEqual(self.store.message(2)["body"], parse_message(raw)["body"])


if __name__ == "__main__":
    unittest.main()
