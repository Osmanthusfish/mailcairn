# Dependency and license audit

Audit date: **2026-11-09**. Scope: the source release, application imports, static assets, fixtures and runtime requirements. The Windows 64-bit portable desktop candidate is covered separately by the [desktop runtime audit](desktop-dependencies.md) and [collected runtime notices](../licenses/desktop/README.txt). This is a distribution inventory, not an independent legal opinion or a vulnerability certification.

## Inventory

| Item | Origin / license | Distribution status and obligations |
| --- | --- | --- |
| MailCairn Python, HTML, CSS and JavaScript | Project-created source; [PolyForm Noncommercial 1.0.0](../LICENSE) | Included. Distribute LICENSE and the Required Notice in NOTICE. Commercial use outside the license's permitted purposes requires separate authorization. |
| Python standard-library modules | Separately installed Python for source execution; [PSF license and historical/component notices](https://docs.python.org/3/license.html) | The source release does not bundle the interpreter. Application imports use the standard library only; no pip application dependencies. The desktop candidate bundles Python 3.13.17 with full runtime notices under its separate audit. |
| SQLite / FTS5 via `sqlite3` | SQLite deliverable code is [public domain](https://www.sqlite.org/copyright.html) | Source execution uses the user's Python build with FTS5 enabled. The desktop artifact includes the selected Python runtime's SQLite; its version and notice are recorded separately. |
| Tkinter desktop entry | Python standard-library `tkinter`; Tcl/Tk under their own notices | Source desktop execution needs Python with Tkinter. The packaged candidate includes Tcl/Tk; preserve the notices in `licenses/desktop`. |
| Browser | User-installed browser under its own terms | Not redistributed. Uses platform DOM, Fetch/XHR and native file selection/download facilities. |
| Icons and decorative shapes | Inline project-created SVG/CSS | Included as source. No downloaded icon package or stock illustration. |
| Fonts | Hanken Grotesk and Newsreader, SIL Open Font License 1.1 | Two unmodified variable TTF files bundled and served locally. Full original copyright and OFL notices accompany each in `mailcairn/static/fonts/`. Their licenses remain OFL; they are not relicensed under PolyForm. System fallbacks remain available. |
| Test fixtures and screenshots | Synthetic example mail and locally captured project UI | No private/customer mail or third-party photographic assets are intended for distribution. Screenshots must be checked before each release. |
| CI runner/actions | External development services, not application dependencies | Workflow tooling is not shipped as an application runtime. Re-audit workflow references before changing or redistributing their code. |

There are **zero third-party application packages** and therefore no pip/npm transitive application dependency tree. This does not mean the entire execution environment has no dependencies: Python builds include native libraries and component notices, and browser/OS software is outside this source audit. No Python, SQLite or browser binaries are included in the source release. The separate desktop executable includes Python, SQLite, Tcl/Tk, other native components and PyInstaller runtime code; their licenses are not replaced by MailCairn's license. No browser is bundled.

The application imports modules such as `email`, `html.parser`, `sqlite3`, `http.server`, `hashlib`, `json`, `threading`, `tempfile`, `pathlib`, `argparse`, `webbrowser`, `tkinter`, and platform locking modules. The English/Simplified Chinese UI uses project-created local JavaScript and does not add a translation package or service. No CDN JavaScript, external web fonts, analytics script, AI client or cloud SDK is required. `requirements.txt` documents the application dependency boundary and contains no installable entries.

## License provenance and consistency

The LICENSE file is the unmodified [official PolyForm Noncommercial 1.0.0 text](https://polyformproject.org/licenses/noncommercial/1.0.0.txt). Its SHA-256 is:

```text
ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8
```

The public license restricts permitted purposes and is **source-available, not OSI open source**. Its explicitly defined personal and noncommercial-organization permissions must not be reduced to a blanket ban on every organizational use. LICENSE is authoritative; README, NOTICE, COMMERCIAL.md and CONTRIBUTING.md must remain consistent with it.

NOTICE identifies the original publisher without inventing a legal name. The publishing repository's owner supplies the commercial contact route; this draft does not fabricate an email address or company. The original rights holder's ability to grant separate commercial licenses covers rights it holds. Outside contributions need the rights process described in [CONTRIBUTING.md](../CONTRIBUTING.md); a public pull request alone does not establish unrestricted future relicensing rights.

## Desktop candidate and future dependency changes

The current candidate uses Python **3.13.17** and PyInstaller **6.22.0**. The [desktop audit](desktop-dependencies.md) records the actual component versions, artifact reconciliation and outstanding external-distribution conditions. Complete texts and their hashes are in [licenses/desktop](../licenses/desktop/README.txt). These notices ship with the executable alongside project and font notices. The candidate remains unsigned, Windows 64-bit only, and untested on a clean second machine; a successful component inventory does not establish those results.

For any later dependency or packaging change, record the exact package/version, direct and transitive licenses, source URL, bundled assets and notice obligations. Review compatibility with the intended source distribution and commercial licensing model before copying code or merging a contribution. Reconcile complete runtime notices against the actual new artifact; this source audit alone does not authorize a binary distribution. Recheck external sources and the installed runtime version for that release.

## Quality iteration development tools

The browser audit used **axe-core 4.14.0**, MPL-2.0, installed only in the external scratch QA directory; its package lock contains one package and no transitive packages. Neither axe source nor its binaries are copied into MailCairn or the source release. Its package includes its own third-party notices. Automated rule checks supplement manual keyboard/layout testing; they do not certify full WCAG conformance. Source: [Deque axe-core](https://github.com/dequelabs/axe-core), accessed 2026-11-09.

The shipped `scripts/check_frontend.mjs` and `scripts/check_i18n.mjs` are project-created and use only Node built-ins. Node 24 is a development/CI tool, not an application runtime requirement. CI now configures it with [actions/setup-node](https://github.com/actions/setup-node) v7 (MIT, executed externally, not redistributed), with package-manager caching disabled. This workflow change is prepared locally; no remote workflow run is claimed.

## Automatic archive iteration

The connector adds only Python standard-library `imaplib`, `ssl`, `socket`, `ctypes` and related local state helpers. Windows DPAPI uses the installed OS crypt32/kernel32 APIs; no credential SDK is bundled. The selected desktop inventory remains21native components; the application module inventory is now10. Provider help links open only on explicit clicks, with no remote runtime assets.

The external synthetic TLS test fixture used the pre-existing development environment's cryptography50.0.1 solely to generate a short-lived local self-signed certificate. Neither that package, its dependencies, the certificate nor its private key enters the project or either release artifact. Application behavior and build origin checks remain stdlib-only. No new third-party source was merged and the project license is unchanged.
