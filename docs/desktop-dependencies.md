# Windows desktop runtime and redistribution notices

Audit date: **2026-11-09**. This covers the proposed Tkinter/PyInstaller desktop bundle. It supplements [the source audit](dependency-audit.md); the source audit's statement that Python is not bundled does not apply to a frozen desktop artifact. No new application package is required: Tkinter is supplied with the selected CPython Windows distribution, while PyInstaller is a build tool whose loader and runtime hooks enter the resulting executable.

**Current clearance: final artifact reconciliation passed for local build/review; external release remains separate.** Successfully downloading licenses alone does not establish which libraries a build includes, interpreter authenticity, or compliance of an external release. The actual artifact checks below supply the build-content evidence. Do not label the entire bundle PolyForm: MailCairn's code retains its project license; its bundled third-party components retain their own terms.

## Reproducible collection

Run against the exact interpreter and build tool installation used for packaging:

```powershell
python scripts/collect_desktop_licenses.py --python-dir PATH_TO_BUILD_PYTHON
```

If PyInstaller is imported from a separate environment, add `--pyinstaller-dir PATH_TO_ITS_SITE_PACKAGES`. The script probes Python/OpenSSL/SQLite/Expat/zlib/mpdecimal/Tcl/Tk, copies the installed Windows Python and PyInstaller terms, fetches notices from upstream version tags, and writes **text files only** to `licenses/desktop`. `manifest.json` records versions, source URL or local path, access time, exact collected-file SHA-256 and original-source SHA-256. Leading copyright comments extracted from C files are explicitly marked; other texts are copied without modification. ReST markup in Python's incorporated-software notice is intentionally retained.

Missing required sources cause a nonzero exit. OpenSSL `NOTICE` is optional only when the exact upstream path returns 404; network errors are not treated as absence. A refresh is a new audit: don't mix old notice files with a new runtime unnoticed. Keep the generated manifest with the distributed notices and reconcile it against the final bundle, not merely the build environment's installed packages.

## Components and required handling

| Component | Evidence and license | Distribution action |
| --- | --- | --- |
| CPython interpreter, stdlib, Windows extensions | Installed `LICENSE.txt`, plus exact-tag `Doc/license.rst`; PSF/historical licenses and incorporated-software notices | Ship **both** `Python-Windows-LICENSE.txt` and `Python-incorporated-software-notices.txt`. State that the interpreter is unmodified and application modules/resources have been bundled with it. Preserve the Microsoft conditions in the Windows license. |
| Tcl/Tk | Exact probed patchlevels, official `tcltk/tcl` and `tcltk/tk` tags | Include `Tcl-LICENSE.txt`, `Tk-LICENSE.txt`, Tcl regex copyright notice and LibTomMath terms. The main Tcl/Tk notice explicitly requires its verbatim inclusion in distributions. Tk's installed notice is not a substitute for Tcl's separately attributed notice. |
| OpenSSL | `ssl.OPENSSL_VERSION`; exact `openssl-VERSION` tag | Apache-2.0 license and upstream NOTICE if present. Keep OpenSSL's terms even if the application does not make outbound HTTPS calls: `hashlib` or other bundled modules can load it. |
| Expat | `pyexpat.EXPAT_VERSION`; exact upstream `COPYING` | Preserve current MIT copyright and permission notices; Python's historical Expat attribution alone may omit newer contributors. |
| zlib | Runtime-reported version; tagged upstream LICENSE | Include notice. This covers compression used by Python/Tcl as present in the actual artifact; do not infer all binaries use the same build without checking. |
| bzip2 / libffi | Installed Windows Python license contains full bzip2/libffi terms; CPython `PCbuild/python.props` pins build dependencies | Keep the complete installed license. Confirm final bundle presence of `_bz2` / `_ctypes` / `libffi` rather than omitting notices because the app has no pip dependency. |
| liblzma / XZ | Exact CPython build-properties version and upstream COPYING | XZ's COPYING differentiates components; liblzma is public domain in the selected 5.2.5 upstream distribution. Including its notice does not mean the GPL xz command-line executable is shipped. If an xz executable is added, audit its different terms. |
| mpdecimal | Runtime-reported version; exact CPython `mpdecimal.c` copyright/license header | Include the BSD notice if `_decimal` is bundled. Source excerpt is the complete initial license comment, not a rewritten summary. |
| HACL* / mimalloc / other incorporated CPython code | Exact CPython source-tag notices, full Python incorporated-software notice | Include MIT/copyright notices. The collector retains HACL's complete leading MIT block and mimalloc attribution; full mimalloc MIT wording is also in Python's incorporated notice. |
| SQLite / FTS5 | Runtime version; tagged SQLite public-domain declaration | Include declaration for transparency. SQLite deliverable code is public domain; this does not assign project-created code to the public domain. |
| PyInstaller bootloader and loader | Installed `COPYING.txt`: GPL-2.0-or-later **with bootloader exception** | The exception permits embedding/distributing the generated combination without imposing GPL on MailCairn merely because of the bootloader. It does not remove other dependencies' obligations or cover redistributing arbitrary modified PyInstaller source. Include the complete COPYING for transparency. |
| PyInstaller runtime hooks | Same COPYING identifies runtime hooks as Apache-2.0; installed hook headers | Include Apache-2.0 text and runtime-hook copyright notices. The collector records all installed runtime-hook headers conservatively; use the build log/TOC to identify the hooks actually embedded. |
| PyInstaller hooks-contrib | Installed package LICENSE distinguishes build-time GPL hooks from Apache runtime hooks | Keep LICENSE in the notice collection. Build-time hooks aren't automatically application dependencies; any embedded runtime hook needs its own retained notices. |
| Fonts | Existing Hanken Grotesk / Newsreader OFL files | Preserve current font notices with the static assets; this audit does not replace them. |
| User's browser / Windows | Used externally, not distributed by MailCairn | No browser engine, WebView2 or pywebview is assumed. Re-audit if packaging changes this. |

Authoritative source details: [Python licensing](https://docs.python.org/3/license.html), [Tcl 8.6.15 notice](https://raw.githubusercontent.com/tcltk/tcl/core-8-6-15/license.terms), [PyInstaller 6.22.0 COPYING](https://raw.githubusercontent.com/pyinstaller/pyinstaller/v6.22.0/COPYING.txt), and [SQLite copyright](https://www.sqlite.org/copyright.html). Exact URLs for the selected runtime belong to the generated manifest rather than hard-coded claims about a future build. Sources accessed 2026-11-09; version-tag files are tied to their tag, not an invented publication date.

## Microsoft runtime boundary

[Microsoft's redistribution documentation](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170) (updated 2026-04-15, accessed 2026-11-09) distinguishes licensed redistribution of VC runtime packages/binaries from merely using software that needs them. The installed Python Windows license **also contains explicit further-distribution conditions**, including preserving notices, avoiding misleading Microsoft branding, platform restrictions, and protecting Microsoft Distributable Code in downstream terms. Those conditions are preserved in full; a PSF source license alone is insufficient.

For this local candidate, an available option is to exclude separately collected `vcruntime*.dll` and require an already installed [official Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170). Validate that dependency on a clean Windows system before claiming a portable, prerequisite-free build. Do not ship a copied Microsoft installer or extra DLL from another installation without establishing its applicable redistribution terms. Excluding standalone VC DLLs does not remove Microsoft-linked code already inside Python extension binaries or the associated Python Windows conditions.

## Runtime provenance and release gates

The original development interpreter was Python **3.13.1**, Tcl/Tk **8.6.15**, OpenSSL **3.0.15**, SQLite **3.45.3**, Expat **2.6.4**, zlib **1.3.1**, mpdecimal **4.0.0**, with PyInstaller **6.22.0** and hooks-contrib **2026.6**. A collector probe against that interpreter succeeded in a scratch directory; those are **not automatically the final release versions**.

The [official Python 3.13.1 release page](https://www.python.org/downloads/release/python-3131/) states that its Windows signing certificates were revoked on 2025-08-28 and recommends later releases. The lead agent installed an isolated newer official interpreter. The collector has now executed against it and populated [the notice manifest](../licenses/desktop/manifest.json) with **19 texts, zero missing required sources**:

| Probed component | Selected version |
| --- | --- |
| Python | 3.13.17 |
| OpenSSL | 3.5.9 |
| SQLite | 3.50.4 |
| Expat | 2.8.5 |
| zlib | 1.3.1 |
| mpdecimal | 4.0.0 |
| Tcl / Tk | 8.6.15 / 8.6.15 |
| PyInstaller | 6.22.0 |
| hooks-contrib | 2026.9 |
| XZ source dependency, from tagged build properties | 5.2.5 |

The exact selected OpenSSL source tag returned 404 for `NOTICE`; this absence is recorded separately, not treated as a downloaded license. Before external publication:

1. Record the new installer URL, SHA-256 and successful Authenticode check; record actual runtime versions after installation. Do not silently reuse 3.13.1 binaries.
2. Regenerate this notice collection against that runtime and the exact PyInstaller installation; require zero collection errors and verify manifest hashes.
3. Reconcile PyInstaller's analysis/collection output and final native DLL list. Block if unexpected third-party application packages or unreviewed native libraries enter the artifact.
4. Include `licenses/desktop`, project LICENSE/NOTICE/COMMERCIAL and font licenses in the installed/extracted artifact, and make the notices accessible without a development checkout.
5. Confirm the Microsoft dependency strategy and downstream terms. Test startup and import/backup recovery on a clean supported Windows system; signing and clean-machine validation are separate from license collection.

**Pass conditions already established:** newer-runtime version probing and notice collection executed; 19 downloaded/copied texts retain copyright/license language and content hashes; final artifact code, static files, notice inclusion and native origins were reconciled successfully below. **Not yet cleared by this document:** downstream Microsoft terms for external distribution, clean-machine behavior, signing, or public release. This is a concrete distribution inventory and source-based review, not an independent legal opinion or vulnerability certification.

## First artifact reconciliation — 2026-11-09

The initial `desktop-build/dist/MailCairn` artifact was inspected using its actual PyInstaller Analysis/COLLECT TOCs, embedded Python archive and file hashes. The first artifact was rejected and rebuilt; historical findings are retained in [desktop-build-evidence.json](desktop-build-evidence.json):

- Its 64 native files match their recorded input bytes, but **43 API-set/UCRT DLLs came from the Codex native libheif cache**, outside the selected Python installation. The libheif library itself and Python application packages were not imported. These unexpected native origins require a sanitized build PATH and fresh collection; a Python license does not establish provenance for unrelated cached DLLs.
- Six of seven embedded application modules match compilation of current source. `mailcairn.parse` is stale relative to the current HTML-head handling fix. Rebuild after the source changes settle.
- Static assets, both font OFL notices, project LICENSE/NOTICE/COMMERCIAL, and all shipped desktop notice files match their source bytes. The 19 manifest content hashes pass.
- The embedded runtime hooks are `pyi_rth_inspect` and `pyi_rth__tkinter`. No third-party Python application module appears in the analysis. `VCRUNTIME140.dll` came from the selected official Python installation; the unexpected UCRT/API-set DLLs have a different source and are separately flagged.

This is an artifact inspection, not a launch result. Local Windows launch/import testing is upcoming; no clean-machine, MailCairn signing, or external-publication claim is made. The new Python installer's Authenticode validity was reported by the lead agent; its exact URL and locally computed SHA-256 are recorded in the JSON.

## Final artifact reconciliation — passed

The replacement **`desktop-final/dist/MailCairn`** was inspected after a build with a restricted PATH and the settled source fixes. Its executable SHA-256 is `691b73a302876dce2fc367df364a3385818ed1cca448fc79b529bf6ca5209361`.

| Check | Executed result |
| --- | --- |
| Native files versus Analysis/COLLECT input paths | **21 files, all from the selected Python installation**, and all output bytes match those inputs. No native DLL was copied from a system directory, the Codex cache or another application in this final artifact. |
| Python application dependencies | No unexpected third-party Python application modules in Analysis. The two embedded runtime hooks are PyInstaller's inspect and Tkinter hooks, covered by collected notices. |
| Current application source versus embedded executable/PYZ code | **All seven modules match** compilation of current source under the selected Python 3.13.17, including corrected `mailcairn.parse` and `desktop`. This compares code objects, not source timestamps. |
| Static resource fidelity | **All nine static files match byte-for-byte**, including both font binaries and their separate Hanken Grotesk / Newsreader OFL texts. |
| Desktop notices | **All 21 files in `licenses/desktop` match source**: 19 collected texts, manifest and README. All 19 manifest SHA-256 entries validate. |
| Project notices | LICENSE, NOTICE and COMMERCIAL.md are present under `_internal` and match source. |
| Microsoft runtime | `VCRUNTIME140.dll` comes from the selected Python installation and its installed Windows notice is included. The earlier unrelated cached API-set/UCRT files are absent. Runtime dependencies provided by the host Windows installation remain a clean-machine validation item. |

The JSON evidence contains per-native-file sources and hashes, per-module source hashes, resource/notice comparisons and the installer checksum. This pass concerns **artifact composition and provenance only**. The lead agent is separately exercising the actual executable on the current Windows machine. That is not a clean-machine test, application signing, security certification or external publication.

## 中文摘要

本次针对 Tkinter＋PyInstaller 的 Windows 打包；不增加第三方业务包，不捆绑浏览器。Python、Tcl/Tk、OpenSSL、Expat、zlib、libffi、bzip2、liblzma、SQLite、mpdecimal、HACL*、mimalloc 和打包器运行时都有各自的声明，不能只附一份 PSF 许可，也不能把整个包统一改成项目非商业许可。

脚本按实际运行时版本收集文本并记录来源、日期和 SHA-256，已针对新安装的 Python 3.13.17 成功收集 19 份文本。初版误从环境 PATH 收集了 43 个外部缓存 DLL，且解析模块落后于源码，已拒绝并重建。最终包的 21 个原生文件均来自所选 Python，7 个应用模块和全部静态资源与当前源码匹配，声明完整且哈希通过。最终包含的 VCRUNTIME140.dll 来自所选 Python，完整保留相应 Windows 许可；干净系统、签名及外部发布仍需独立完成，不能据此宣称已获完整外部分发合规认证。

## Automatic archive candidate — latest reconciliation

The2026-11-09 sync candidate uses the same reviewed interpreter and notice collection. [Current evidence](desktop-build-evidence.json) reconciles21native files, **10 application modules** (including credentials, IMAP transport and sync),9static resources,21desktop notice files,3project notices and19manifest hashes. No third-party application Python package was pulled into the bundle. The EXE's actual protected-credential and restart checks are recorded in[sync evidence](sync-evidence.json). Prior7-module checkpoints above are historical. External-distribution, signing and clean-machine limits remain unchanged.
