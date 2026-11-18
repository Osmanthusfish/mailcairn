"""Check the deliverable boundary and obvious accidental private artifacts.

Run from any directory. This is a focused release check, not a security audit.
"""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import os
import re
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__", ".venv", "data", "work", ".pytest_cache", ".mypy_cache"}
ROOT_FILES = {".gitignore", ".gitattributes", "AGENTS.md", "app.py", "desktop.py", "LICENSE", "NOTICE",
              "COMMERCIAL.md", "CONTRIBUTING.md", "DESIGN.md", "HANDOFF.md", "HANDOFF.history.md",
              "README.md", "README.zh-CN.md", "SECURITY.md", "ALPHA.md", "RELEASE_NOTES.md",
              "requirements.txt", "Start-MailCairn.cmd", "Start-MailCairn-Desktop.cmd", "start-mailcairn.sh"}
TEXT_SUFFIXES = {".py", ".js", ".mjs", ".html", ".css", ".md", ".json", ".yml", ".yaml", ".txt", ".cmd", ".sh", ".svg"}
# Only reviewed, deterministically generated mail may cross the source boundary.
SYNTHETIC_MAIL = {
    "tests/fixtures/empty.mbox": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "tests/fixtures/invalid.mbox": "7ed3dfeac05dea94fec835ea02b19e1d1b0166ec2ddc51b36c38d849b5d1b2b3",
    "tests/fixtures/sample.eml": "c1fc79cf59215b73d04bac7261ef21714d036f6f9443921fed5f3f3f96030260",
    "tests/fixtures/sample.mbox": "5b1c2db3578cd76265618e61c564c70402ef764227e3164dbe599966b1a570ac",
}
REQUIRED = ["app.py", "README.md", "README.zh-CN.md", "AGENTS.md", "LICENSE", "NOTICE", "COMMERCIAL.md", "SECURITY.md", "CONTRIBUTING.md", "mailcairn/static/index.html", "mailcairn/static/app.js", "mailcairn/static/style.css", "docs/market-research.md", "docs/dependency-audit.md", ".github/workflows/test.yml", "HANDOFF.md", "docs/test-results.md"]


class StaticLinks(HTMLParser):
    """Provider help opens only on a click; remote application resources do not."""
    HELP = {"https://myaccount.google.com/apppasswords", "https://support.google.com/accounts/answer/185833", "https://proton.me/mail/bridge"}

    def __init__(self):
        super().__init__()
        self.problems = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        for key in ("src", "href"):
            value = attrs.get(key) or ""
            if not value.lower().startswith(("http:", "https:", "//")):
                continue
            if (tag == "a" and key == "href" and value in self.HELP
                    and attrs.get("target") == "_blank"
                    and {"noopener", "noreferrer"} <= set((attrs.get("rel") or "").split())):
                continue
            self.problems.append("Unexpected external static reference")


def is_link(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def source_files(root=None):
    """The checker and packager share exactly the same exclusions."""
    root = Path(root or ROOT)
    for base, directories, names in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in SKIP and not is_link(Path(base) / name))
        for name in sorted(names):
            path = Path(base) / name
            if (path.suffix.lower() in {".zip", ".log", ".tmp", ".pyc", ".pyo"}
                    or name.endswith("~") or name in {".DS_Store", "Thumbs.db", ".coverage"}):
                continue
            yield path, path.relative_to(root)


def allowed_source_path(rel):
    name, suffix = rel.as_posix(), rel.suffix.lower()
    if len(rel.parts) == 1:
        return name in ROOT_FILES
    if rel.parts[0] == "docs":
        return suffix in {".md", ".json"} or (rel.parts[:2] == ("docs", "screenshots") and suffix == ".png")
    if rel.parts[0] == "licenses":
        return suffix in {".txt", ".md", ".json"}
    if rel.parts[0] == "scripts":
        return suffix in {".py", ".mjs"}
    if rel.parts[0] == "tests":
        return suffix == ".py" or name == "tests/fixtures/README.md" or name in SYNTHETIC_MAIL
    if rel.parts[0] == ".github":
        return suffix in {".yml", ".yaml", ".md"}
    if rel.parts[0] == "mailcairn":
        return suffix == ".py" or (rel.parts[:2] == ("mailcairn", "static") and suffix in {".html", ".js", ".css", ".ttf", ".txt", ".svg"})
    return False


def machine_paths(text):
    """Reject absolute machine locations, allowing explicit neutral examples."""
    normalized = re.sub(r"\\+", "/", text)
    windows = re.findall(r"(?<![A-Za-z0-9])[A-Za-z]:/[^\s\"'`<>),;]+", normalized)
    allowed = re.compile(r"^[A-Za-z]:/(?:MyMail|Synthetic|temporary-bundle|Windows)(?:/|$)", re.I)
    if any(not allowed.match(value) for value in windows):
        return True
    if (re.search(r"(?<![\\:A-Za-z0-9])\\{2,}[A-Za-z0-9_.-]+\\+[A-Za-z0-9]", text)
            or re.search(r"(?<![A-Za-z0-9:/])//[A-Za-z0-9_.-]+/[A-Za-z0-9]", text)):
        return True  # UNC share, including JSON-escaped Windows forms.
    # Home directories and temporary work areas commonly reveal account names.
    return bool(re.search(r"(?<![A-Za-z0-9:])/(?:Users|home|tmp|private/tmp|var/folders)/[^\s\"'`<>]+", normalized))


def png_problems(data):
    """Inspect structure and metadata without decoding or altering screenshot pixels."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ["Invalid PNG screenshot"]
    offset, saw_header, saw_end = 8, False, False
    problems = []
    while offset + 12 <= len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + size
        if end > len(data):
            return problems + ["Truncated PNG screenshot"]
        payload = data[offset + 8:offset + 8 + size]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            problems.append("Invalid PNG checksum")
        if not saw_header and kind != b"IHDR":
            problems.append("Invalid PNG header order")
        saw_header = True
        if kind in {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME", b"iCCP"}:
            problems.append("Screenshot contains unreviewed metadata: " + kind.decode("ascii"))
        offset = end
        if kind == b"IEND":
            saw_end = True
            if size or offset != len(data):
                problems.append("Unexpected data after PNG image")
            break
    if not saw_end:
        problems.append("Incomplete PNG screenshot")
    return problems


def check(root=None, content=None):
    root = Path(root or ROOT)
    if content is None:
        content = {rel: path.read_bytes() for path, rel in source_files(root) if not is_link(path)}
    problems = ["Missing required file: " + name for name in REQUIRED if Path(name) not in content]
    count = 0
    for base, directories, names in os.walk(root, followlinks=False):
        directories[:] = [name for name in directories if name not in SKIP]
        for name in directories + names:
            candidate = Path(base) / name
            if is_link(candidate):
                problems.append("Symlink or junction not allowed in source release: " + str(candidate.relative_to(root)))
        directories[:] = [name for name in directories if not is_link(Path(base) / name)]
    for rel, data in sorted(content.items()):
        path = root / rel
        count += 1
        if not allowed_source_path(rel):
            problems.append("Unreviewed source path: " + str(rel))
        if (re.search(r"\.(?:db|db3|sqlite|sqlite3)(?:-wal|-shm|-journal)?$", path.name, re.I)
                or path.suffix.lower() in (".pem", ".key", ".p12", ".pfx", ".keystore")
                or (path.name.startswith(".env") and path.name != ".env.example")
                or path.name.startswith(".upload-") or path.name == ".mailcairn.lock"
                or path.name == ".mailcairn-instance.json"
                or path.name == ".mailcairn-desktop.json"
                or path.name.startswith((".mailcairn-sync", ".mailcairn-credentials"))
                or (path.name.startswith((".mailcairn-instance-", ".mailcairn-desktop-")) and path.suffix == ".tmp")):
            problems.append("Private/runtime artifact: " + str(rel))
        if path.suffix.lower() in (".mbox", ".eml"):
            if SYNTHETIC_MAIL.get(rel.as_posix()) != hashlib.sha256(data).hexdigest():
                problems.append("Unreviewed or changed mail fixture: " + str(rel))
        if path.suffix.lower() == ".png":
            problems.extend(problem + " in " + str(rel) for problem in png_problems(data))
        if path.suffix.lower() in TEXT_SUFFIXES or len(rel.parts) == 1:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                problems.append("Non-UTF-8 source text: " + str(rel))
                continue
            upstream_notice = ((rel.parts[0] == "licenses" and path.suffix == ".txt")
                               or (rel.parts[:3] == ("mailcairn", "static", "fonts") and path.name.endswith("-OFL.txt")))
            if not upstream_notice and machine_paths(text):
                problems.append("Machine-specific absolute path in " + str(rel))
            username = os.environ.get("USERNAME") or os.environ.get("USER") or ""
            if (not upstream_notice and len(username) > 3 and username.lower() not in {"root", "user", "runner", "admin", "administrator"}
                    and re.search(r"(?<![\w-])" + re.escape(username) + r"(?![\w-])", text, re.I)):
                problems.append("Local account name in " + str(rel))
            if re.search(r"(?:sk-[A-Za-z0-9_-]{30,}|ghp_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)", text):
                problems.append("Possible credential in " + str(rel))
            if rel.parts[:2] == ("mailcairn", "static"):
                if path.suffix.lower() == ".html":
                    parser = StaticLinks()
                    parser.feed(text)
                    problems.extend(problem + " in " + str(rel) for problem in parser.problems)
                elif re.search(r'''(?:src|href)=["']https?://''', text):
                    problems.append("Remote static resource/link in " + str(rel))
    if Path("LICENSE") in content:
        digest = hashlib.sha256(content[Path("LICENSE")]).hexdigest()
        if digest != "ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8":
            problems.append("LICENSE differs from the verified official PolyForm text")
    return {"files_checked": count, "problems": problems, "passed": not problems}


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)
