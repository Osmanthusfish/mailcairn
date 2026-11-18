# Synthetic fixtures

Every email in this directory was written for MailCairn testing. Names, shops,
bookings, invoices, attachments and correspondence are fictional. All addresses
use the reserved `example.com` domain. No private mailbox or customer data is
included, and no message loads remote content.

- `sample.mbox`: 20 everyday messages, 7 small text attachments, English and
  Chinese, a mixture of LF and CRLF, dated 31 October–9 November 2026.
- `sample.eml`: the first message, for exact-byte download checks.
- `invalid.mbox`: deliberately malformed input.
- `empty.mbox`: zero-byte input.

Regenerate deterministically from the repository root:

```sh
python -m tests.make_fixtures
```

The application starts empty. These files are only imported when a tester
explicitly selects them; screenshots using them are labelled synthetic.
