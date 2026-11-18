"""Original, synthetic email fixtures. No user or customer data."""
from email import policy
from email.message import EmailMessage

ENVELOPE = b"From archive@example.com Mon Nov 09 09:00:00 2026\n"


def message(subject="Autumn train receipt", body="Your booking reference is LANTERN-421.", *,
            sender="Harbor Rail <tickets@example.com>", recipient="Alex Morgan <alex@example.com>",
            date="Mon, 09 Nov 2026 09:00:00 +0800", message_id="<sample-001@example.com>",
            attachment=None, html=None, crlf=False):
    msg = EmailMessage(policy=policy.SMTP if crlf else policy.default)
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Message-ID"] = message_id
    if date is not None:
        msg["Date"] = date
    msg["X-Gmail-Labels"] = "Archive,Personal"
    msg.set_content(body)
    if html is not None:
        msg.add_alternative(html, subtype="html")
        msg.set_boundary("alternative-fixture-boundary")
    if attachment is not None:
        filename, data = attachment
        msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=filename)
        msg.set_boundary("mixed-fixture-boundary")
    return msg.as_bytes()


def mbox(*messages):
    return b"".join(ENVELOPE + raw + (b"" if raw.endswith(b"\n") else b"\n") for raw in messages)
