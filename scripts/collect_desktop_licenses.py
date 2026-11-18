"""Collect exact upstream/runtime notice texts; no packages or binaries downloaded.

Run against the SAME Python installation and PyInstaller distribution used to
build. This creates a provenance manifest, not an assertion of legal clearance.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PROBE = r'''
import json, sys, ssl, sqlite3, pyexpat, zlib, decimal, tkinter
t = tkinter.Tk()
t.withdraw()
print(json.dumps(dict(python=sys.version.split()[0], openssl=ssl.OPENSSL_VERSION.split()[1], sqlite=sqlite3.sqlite_version, expat=pyexpat.EXPAT_VERSION.removeprefix('expat_'), zlib=zlib.ZLIB_RUNTIME_VERSION, mpdecimal=decimal.__libmpdec_version__, tcl=t.tk.eval('info patchlevel'), tk=t.tk.eval('package provide Tk'))))
t.destroy()
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-dir', required=True, type=Path)
    parser.add_argument('--pyinstaller-dir', type=Path, help='site-packages containing the exact build PyInstaller dist-info; defaults to target Python site-packages')
    parser.add_argument('--output', type=Path, default=ROOT / 'licenses' / 'desktop')
    args = parser.parse_args()
    runtime = args.python_dir.resolve()
    versions = json.loads(subprocess.check_output([str(runtime / 'python.exe'), '-I', '-c', PROBE], text=True))
    packages = (args.pyinstaller_dir or runtime / 'Lib' / 'site-packages').resolve()
    copies = [(runtime / 'LICENSE.txt', 'Python-Windows-LICENSE.txt')]
    for package, filename, output in [('pyinstaller', 'COPYING.txt', 'PyInstaller-COPYING.txt'), ('pyinstaller_hooks_contrib', 'LICENSE', 'PyInstaller-hooks-contrib-LICENSE.txt')]:
        matches = list(packages.glob(f'{package}-*.dist-info'))
        if len(matches) != 1:
            raise SystemExit(f'Expected one exact {package} dist-info in {packages}; got {len(matches)}')
        versions[package] = matches[0].name.removeprefix(package + '-').removesuffix('.dist-info')
        candidates = [matches[0] / 'licenses' / filename, matches[0] / filename]
        copies.append((next(p for p in candidates if p.is_file()), output))
    cpython = f'https://raw.githubusercontent.com/python/cpython/v{versions["python"]}/'
    urls = [
        ('Python-incorporated-software-notices.txt', cpython + 'Doc/license.rst', False),
        ('Python-build-version-provenance.txt', cpython + 'PCbuild/python.props', False),
        ('Tcl-LICENSE.txt', f'https://raw.githubusercontent.com/tcltk/tcl/core-{versions["tcl"].replace(".", "-")}/license.terms', False),
        ('Tcl-regex-source-notice.txt', f'https://raw.githubusercontent.com/tcltk/tcl/core-{versions["tcl"].replace(".", "-")}/generic/regcomp.c', False),
        ('Tcl-LibTomMath-LICENSE.txt', f'https://raw.githubusercontent.com/tcltk/tcl/core-{versions["tcl"].replace(".", "-")}/libtommath/LICENSE', False),
        ('Tk-LICENSE.txt', f'https://raw.githubusercontent.com/tcltk/tk/core-{versions["tk"].replace(".", "-")}/license.terms', False),
        ('OpenSSL-LICENSE.txt', f'https://raw.githubusercontent.com/openssl/openssl/openssl-{versions["openssl"]}/LICENSE.txt', False),
        ('OpenSSL-NOTICE.txt', f'https://raw.githubusercontent.com/openssl/openssl/openssl-{versions["openssl"]}/NOTICE', True),
        ('Expat-COPYING.txt', f'https://raw.githubusercontent.com/libexpat/libexpat/R_{versions["expat"].replace(".", "_")}/expat/COPYING', False),
        ('zlib-LICENSE.txt', f'https://raw.githubusercontent.com/madler/zlib/v{versions["zlib"]}/LICENSE', False),
        ('mpdecimal-source-notice.txt', cpython + 'Modules/_decimal/libmpdec/mpdecimal.c', False),
        ('HACL-source-notice.txt', cpython + 'Modules/_hacl/Hacl_Hash_SHA2.c', False),
        ('mimalloc-source-notice.txt', cpython + 'Objects/mimalloc/alloc.c', False),
        ('Apache-2.0.txt', 'https://www.apache.org/licenses/LICENSE-2.0.txt', False),
        ('SQLite-public-domain.txt', 'https://raw.githubusercontent.com/sqlite/sqlite/version-' + versions['sqlite'] + '/LICENSE.md', False),
    ]
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    prior_manifest = out / 'manifest.json'
    if prior_manifest.is_file():
        prior_versions = json.loads(prior_manifest.read_text(encoding='utf-8')).get('versions', {})
        if any(prior_versions.get(key) != value for key, value in versions.items()):
            raise SystemExit('Output contains notices for a different runtime/build tool. Choose a fresh output directory and replace the reviewed collection explicitly.')
    accessed = datetime.now(timezone.utc).isoformat(timespec='seconds')
    entries, missing, errors = [], [], []

    def retain(filename, data, source):
        source_sha256 = hashlib.sha256(data).hexdigest()
        transform = 'none'
        if filename.endswith('-source-notice.txt'):
            match = re.match(rb'\s*(/\*.*?\*/)', data, re.DOTALL)
            if not match or b'Copyright' not in match[1]:
                raise ValueError(f'Expected complete leading license comment in {source}')
            data = match[1] + b'\n'
            transform = 'exact leading copyright/license comment, code omitted; full MIT text for mimalloc also in Python-incorporated-software-notices.txt'
        data.decode('utf-8-sig')  # reject non-text or accidental binary responses
        if not data or len(data) > 2_000_000 or data.lstrip().lower().startswith((b'<!doctype html', b'<html')):
            raise ValueError(f'Not a bounded plain-text notice: {source}')
        target = out / filename
        # Fail before replacing a symlink or outside path.
        if target.is_symlink() or target.resolve().parent != out:
            raise ValueError(f'Unsafe output: {target}')
        target.write_bytes(data)
        entries.append(dict(file=filename, source=source, accessed_utc=accessed, sha256=hashlib.sha256(data).hexdigest(), source_sha256=source_sha256, transformation=transform, bytes=len(data)))

    def fetch(item):
        name, url, optional = item
        for attempt in range(3):
            try:
                with urlopen(Request(url, headers={'User-Agent': 'MailCairn-license-collector/1'}), timeout=25) as result:
                    return name, result.read(2_000_001), url, None
            except HTTPError as error:
                return name, None, url, ('absent' if optional and error.code == 404 else str(error))
            except Exception as error:
                if attempt == 2: return name, None, url, str(error)

    for path, name in copies:
        retain(name, path.read_bytes(), "build-runtime/" + path.relative_to(runtime).as_posix())
    with ThreadPoolExecutor(max_workers=6) as pool:
        for name, data, url, error in pool.map(fetch, urls):
            if error == 'absent':
                missing.append(dict(file=name, source=url, status='upstream-404-not-present', accessed_utc=accessed))
                if (out / name).exists(): errors.append(dict(file=name, source=url, error='Stale optional notice exists although upstream now returns 404; review before distribution'))
            elif error: errors.append(dict(file=name, source=url, error=error))
            else: retain(name, data, url)
    props = out / 'Python-build-version-provenance.txt'
    if props.exists():
        matched = re.search(r'ExternalsDir\)xz-([\d.]+)', props.read_text(encoding='utf-8'))
        if matched:
            versions['xz'] = matched[1]
            name, data, url, error = fetch(('XZ-COPYING.txt', f'https://raw.githubusercontent.com/tukaani-project/xz/v{matched[1]}/COPYING', False))
            if error: errors.append(dict(file=name, source=url, error=error))
            else: retain(name, data, url)
    hooks = packages / 'PyInstaller' / 'hooks' / 'rthooks'
    notices = []
    for hook in sorted(hooks.glob('*.py')):
        lines = hook.read_text(encoding='utf-8').splitlines()
        header = []
        for line in lines:
            if line.startswith('#') or not line.strip(): header.append(line)
            else: break
        notices.append(f'File: PyInstaller/hooks/rthooks/{hook.name}\n' + '\n'.join(header).strip() + '\n')
    retain('PyInstaller-runtime-hook-notices.txt', ('\n'.join(notices)).encode('utf-8'), 'build-runtime/' + hooks.relative_to(runtime).as_posix())
    manifest = dict(versions=versions, generated_utc=accessed, files=sorted(entries, key=lambda item:item['file']), absent_optional=missing, errors=errors, clearance='NOTICE COLLECTION ONLY; reconcile final bundle and Microsoft terms before publication')
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(versions=versions, files=len(entries), errors=errors, output=str(out)), ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
