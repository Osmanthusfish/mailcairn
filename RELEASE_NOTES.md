# MailCairn 0.1.0-alpha.9 — Alpha preview, 2026-11-18

Single-key navigation shortcuts (`i`, `g`, `h`) now work case-insensitively (such as under Caps Lock), and the Reading room toggle explicitly documents `,` for opening Reading room in English and Simplified Chinese. Getting started Step 04 now explains restoring backups through the Windows desktop window (`Restore backup…` / `恢复备份…`) ahead of the source CLI command. Language pills enforce `white-space: nowrap` in narrow headers and dialogs, `IMAPClient` uses a 20-second socket timeout (`NETWORK_TIMEOUT = 20`), and `LocalServer.server_bind` avoids reverse-DNS `getfqdn` stalls on macOS loopback bindings. English and Simplified Chinese READMEs were streamlined for repository visitors, development commands match CI, relative historical links were repaired, and 19 unreferenced historical screenshots (~2.98 MiB) were removed from the source package.

202 Python tests, 66/31/19/11 Node checks, bundle reconciliation, eight actual-EXE HTTP groups and ego-browser shortcut/guide/320px pill checks passed. See [dated evidence](docs/alpha9-evidence.json) and [test results](docs/test-results.md) for exact scope. Still unsigned, local and unpublished; real Gmail automatic-arrival TLS failure and other known limits remain. Checksums belong to `ALPHA9-ARTIFACTS.json` and `.sha256` beside the matching packages.

中文：alpha.9 完成公开发布前细节打磨：单键快捷键支持大小写并补齐 `,` 阅读设置双语提示，使用指南第04步增加桌面窗口“恢复备份…”操作说明，语言切换按钮加 `nowrap` 防折行，IMAP 超时放宽至20秒，精简中英 README 首屏并清理19张无引用旧截图。202项Python、66／31／19／11项Node回归、构建审计、实际EXE八组HTTP与Ego真机验收通过。仍未签名、未上传，原生恢复重测、Gmail后续新信及二机等限制保留。

---

# Historical MailCairn 0.1.0-alpha.8 — internal candidate, 2026-11-17

Message reading (`readMessage`) and import receipt loading (`showReceipt`) now present an in-place bilingual retry action (`Try again` / `重试`) on request failure, keeping keyboard focus inside the pane or receipt dialog across repeated retries without stealing focus if the user moves elsewhere. Opening Reading room now focuses the currently active theme choice rather than always focusing System, and `keepDialogFocus` includes `<summary>` elements while skipping collapsed `<details>` controls and handling `<dialog>` root Tab wrapping.

202 Python tests, 65/31/18/11 Node checks, bundle reconciliation, eight actual-EXE HTTP groups and ego-browser real-workflow retry/focus checks passed. See [dated evidence](docs/alpha8-evidence.json) and [test results](docs/test-results.md) for exact scope. Still unsigned, local and unpublished; real Gmail automatic-arrival TLS failure and other known limits remain. Checksums belong to `ALPHA8-ARTIFACTS.json` and `.sha256` beside the matching packages.

中文：alpha.8 补充读信与回执失败时的就地双语重试（`重试` / `Try again`）与键盘焦点保持、阅读设置自动聚焦当前主题及弹窗 `<summary>` / 折叠 `<details>` 焦点控制；202项Python、65／31／18／11项Node回归、构建审计、实际EXE八组HTTP与Ego真机交互验证通过。仍未签名、未发布，原生窗口重测、Gmail后续新信及第二台电脑等限制保留。

---

# Historical MailCairn 0.1.0-alpha.7 — internal candidate, 2026-11-17

Modal dialogs now wrap `Tab` and `Shift+Tab` across visible, enabled, non-inert focusable controls while preserving modified system shortcuts and native interior movement. Archive summaries, attachment counts and clip accessible labels, duplicate counts, unimported record counts and review status lines now distinguish singular and plural English copy accurately without modifying Simplified Chinese or literal message content.

202 Python tests, 62/31/17/11 Node checks, bundle reconciliation, eight actual-EXE HTTP groups and ego-browser 800×600 / 320×568 reading, keyboard loop, reload persistence and disabled-motion checks passed. See [dated evidence](docs/alpha7-evidence.json) and [test results](docs/test-results.md) for exact scope. Still unsigned, local and unpublished; real Gmail automatic-arrival TLS failure and other known limits remain. Checksums belong to `ALPHA7-ARTIFACTS.json` and `.sha256` beside the matching packages.

中文：alpha.7 补齐弹窗 `Tab` / `Shift+Tab` 首末焦点循环并修正英文单复数文案，不影响中文界面和邮件原文；202项Python、62／31／17／11项Node回归、构建审计、实际EXE八组HTTP与Ego真机窄屏阅读／偏好持久／减少动效均通过。仍未签名、未发布，原生窗口重测、Gmail后续新信及第二台电脑等限制保留。

---

# Historical MailCairn 0.1.0-alpha.6 — internal candidate, 2026-11-16/17

Failed app/translation scripts, parse/top-level errors and early binding failures now expose independent English/Chinese recovery. A slow startup receives a bounded 12-second notice that can settle naturally when initialization finishes. Confirmed failure wording does not regress to a slow-startup message. The native reload button preserves an unexchanged session fragment, works with Enter, and starts a complete page rather than rebinding a partly initialized interface.

Startup readiness clears its listeners/timer, restores only the control states it temporarily disabled, and moves focus only when hiding a focused recovery panel. No recovery copy appears in normal use. The bootstrap has no i18n/business-script dependency; its own download failure cannot be recovered by that same JavaScript layer. Disabled JavaScript receives a static bilingual notice. The original sporadic navigation cause remains unconfirmed.

The Windows bundle was rebuilt and reconciled; actual-EXE eight-group HTTP and Ego blocked-script/reload checks passed. See [dated evidence](docs/alpha6-evidence.json) for full scope. No dependency or license change; still unsigned, local and unpublished. Real Gmail automatic-arrival TLS failure and other known limits remain. Checksums belong to `ALPHA6-ARTIFACTS.json` and `.sha256` beside the matching packages.

中文：alpha.6修复启动异常时只剩转圈、没有重试入口的恢复缺口；支持双语和键盘，慢启迟到成功不会留下提示或禁用状态。实际构建已验，但未定位旧偶发根因；没有重测本版原生恢复，也没有解决独立Gmail TLS故障。旧版记录如下，不能混用其验收范围。

---

# Historical MailCairn 0.1.0-alpha.5 — internal candidate, 2026-11-16

Background file imports and recovered jobs preserve the current reader while updating real counts and newly arrived rows. If the focused message leaves the visible page, focus moves to its preserved reader. Browsing an import from history or a receipt focuses search immediately and plays the existing archive entrance; delayed results cannot reclaim focus.

MBOX export removes top-level Content-Length headers and their folded continuations from a temporary copy, so individually imported EML messages export into a file the app can read again. Message bodies, MIME-part headers, stored originals and EML downloads are retained. MBOX remains a compatibility export, not a byte-exact roundtrip.

Earlier polling, credential rollback and startup fixes are included. No dependencies or license terms changed. This is an unsigned local candidate, not published; real Gmail new-message recovery, paid Proton Bridge, second-machine compatibility and owner visual acceptance remain unresolved. Read [test results](docs/test-results.md) for executed checks and exact build identities. Current package checksums belong to `ALPHA5-ARTIFACTS.json` and `.sha256` files.

中文：alpha.5修复后台导入打断阅读、历史／明细跳转丢失焦点和含长度头的EML导出MBOX后无法重导的问题。保留邮件原件和此前启动／轮询／凭据修复，无新依赖；各项测试按实际执行记录，仍为未发布的内部候选。

---

# Historical MailCairn 0.1.0-alpha.4 — 2026-11-10

Prepared 2026-11-10. **Local desktop startup hotfix; not uploaded. Actual EXE recovery/restart and default-launch health checks passed; final ZIP CRC and member-byte checks passed; checksums are recorded in ALPHA4-ARTIFACTS.json and .sha256 files.**

Windows can reserve the desktop's previously saved loopback port. A real exclusive bind to that saved port failed with WinError 10013, while an OS-assigned loopback port bound successfully. Alpha.4 retries once on `127.0.0.1:0` for Windows 10013/10048 or `EADDRINUSE`, then persists the actual assigned port. It does not use a TCP availability probe or change OS reservations, firewall, proxy or administrative settings. Other permission failures, including generic `EACCES`, still propagate; failure cleanup is covered.

**32 targeted desktop/instance tests passed in 6.197 seconds.** Independent review found no blocker. The alpha.3 full-suite result (181 Python / 80 JavaScript), mixed-mail benchmark and package evidence below are historical, not rerun results for this hotfix. No reader optimization ships in alpha.4. [Current evidence](docs/alpha4-evidence.json).

Build reconciliation passed **21 native components, 10 application modules, 9 static resources, 21 desktop notices and 19 hashes**. EXE SHA-256: `4d6d8654eeabeea2f4f5892288a23f1231e4890f90ca6ce4725ff804cb912e6a` (not a ZIP checksum). [Versioned build evidence](docs/desktop-build-alpha4.json). This round does not claim a new eight-group HTTP smoke run or full-suite run. The local port fix does not establish recovery of the separate Gmail TLS failure.

Target packages are `MailCairn-0.1.0-alpha.4-windows-x64.zip` and `MailCairn-0.1.0-alpha.4-source.zip`. The workspace default launcher now opens alpha.4 with the Chinese control window; the Gmail test launcher remains on alpha.1 to preserve the user's active instance. The EXE remains unsigned; second-machine acceptance and real Gmail automatic new-message recovery remain unresolved. Source remains [PolyForm Noncommercial 1.0.0](LICENSE).

中文：alpha.4 仅修复桌面保存端口被 Windows 保留／占用时的启动失败。特定绑定错误会在本机回环地址上重试一次，由系统分配并保存新端口；不探测 TCP、不修改防火墙／代理／系统保留规则、不要求管理员设置。32 项定向测试通过，普通权限错误仍上报；本轮未重跑 alpha.3 的 181 项 Python／80 项 JavaScript，也未交付阅读器优化。实际 EXE 保留端口回退、正常关闭／重启复用端口及真实默认入口健康检查通过；应用已正常启动并保持运行。最终 ZIP 核对通过，校验和见 ALPHA4-ARTIFACTS.json 和 .sha256，未上传。

---

# MailCairn 0.1.0-alpha.3

Prepared 2026-11-10. **Local candidate; not uploaded. ZIP packaging passed CRC and full-member byte checks (158 source files, 1,149 Windows-package files). Current checksums are in the delivery directory’s `ALPHA3-ARTIFACTS.json` and `.sha256` files.**

- Search now splits punctuation consistently, combines CJK substrings with accented Latin terms using AND, and finds fragments within attachment names. Search and filtered export use the same conditions. A partial attachment-name index improves the filename fallback; the archive remains schema version 1.
- Editing the query or sender immediately invalidates older responses and disables stale export/pagination during debounce.
- **181 Python tests passed (32.247 s); 80 JavaScript checks passed (41 frontend, 15 i18n, 24 connections).** On the same synthetic 1,000-message fixture with 250 × 64 KiB attachments, all 12 query cases, exact-byte samples, integrity, deduplication and cancel/resume passed. Import took 2.698 s, deduplication 0.507 s, selective query medians 4.45–4.85 ms. This 24,694,850-byte workload does not establish attachment-heavy or 20 GiB capacity.
- Real browser checks found 250 results for each formerly missing case. The downloaded filtered export reimported to the exact 250-message hash set; a 65,536-byte attachment matched. Chinese 1440px and English 390px views were inspected without horizontal overflow. Language switching preserved the query/results; reduced motion left zero running animations. A short sample observed no long tasks; this is not an FPS guarantee.
- Fresh source and the actual alpha.3 EXE each passed eight HTTP workflow groups. Restore used an extracted-source helper, not the native dialog; the source CMD launcher was not rerun. Build reconciliation passed 21 native components, 10 application modules, 9 static resources, 21 desktop notices and 19 hashes. [Evidence](docs/alpha3-evidence.json).

Target packages: `MailCairn-0.1.0-alpha.3-windows-x64.zip` and `MailCairn-0.1.0-alpha.3-source.zip`. The EXE is unsigned; clean second-machine testing remains outstanding. Real Gmail still has only the initial 120-message pass; automatic new mail failed at TLS and remains unresolved. This iteration used synthetic data, left the user's apps/proxy/network unchanged and made no new private-mail probes. Source remains under [PolyForm Noncommercial 1.0.0](LICENSE).

中文：alpha.3 修复三类可复现搜索遗漏与输入等待期间的旧结果导出问题；181 项 Python、80 项 JavaScript、合成浏览器及新源码／新 EXE 各八组 HTTP 流程通过。相同约 24.7 MB 混合样本的 12 项查询、原文字节／附件、完整性、去重和取消续导通过；这不代表大规模附件或 20 GiB 已验证。最终 ZIP 核对通过，未上传。真实 Gmail 仍为首次 120 封通过、后续自动到信未恢复；未改动用户应用或网络。

---

# MailCairn 0.1.0-alpha.2

Prepared 2026-11-10. **Local alpha candidate; not uploaded.** This update addresses connection-status accuracy and recovery regressions; it does not establish recovery of the user's real Gmail connection.

## Changes

- The mailbox timestamp now says **Last successful sync**. Attempt counters are shown only for a completed idle sync, so a failed, paused or in-progress attempt is not presented as the result of an older successful sync.
- Recognized network errors use short English/Chinese guidance, with Gmail-specific wording. Automatic-retry copy appears only for an unpaused network-error state with available credentials. Authentication still offers Reconnect; certificate changes and unknown errors remain visible.
- Restart queues saved unpaused connections and preserves paused connections; regression coverage checks persisted credentials, cursor and recovery after a partial failure.
- Getting started explains that a working Gmail website does not prove the mail connection is reachable. Saved mail and file import remain usable while other apps keep running. Retrying does not guarantee recovery.

## Validation and packages

The final 177 Python tests passed in 35.829 seconds; 79 JavaScript checks passed: 40 frontend, 15 i18n and 24 connection checks. Synthetic browser failure/pause/authentication and narrow-layout checks passed. Reconnecting through the actual UI increased saved mail from one to two, cleared error/retry copy and allowed opening the second message. Freshly extracted source code and the actual new EXE each passed eight HTTP workflow groups; see [dated test results](docs/test-results.md). The alpha.1 results below are historical and must not be attributed to alpha.2.

Build reconciliation passed: 21 native components, 10 application modules, 9 static resources, 21 desktop notice files and 19 notice hashes. Restore smoke checks used an extracted-source helper, not a native dialog; the source CMD launcher was not rerun this round. Both ZIPs passed CRC and full-member byte checks: 150 source files and 1,141 Windows-package files. Source matched the checked source; tested code and runtime were unchanged. A scoped username/workspace-byte scan of 1,141 files found no matches; no instance state or prohibited private-artifact types were found. Current ZIP hashes are recorded in the delivery directory’s `ALPHA-ARTIFACTS.json` and `.sha256` files. [Alpha.2 evidence](docs/alpha2-evidence.json).

Prepared artifacts are `MailCairn-0.1.0-alpha.2-windows-x64.zip` and `MailCairn-0.1.0-alpha.2-source.zip`. The Windows executable remains unsigned; a clean second Windows computer remains untested. Quit the old app normally before opening a new executable; refreshing an old browser tab does not upgrade its backend. Keep a separate backup.

Real Gmail initially archived 120 messages successfully. Later automatic new-message retrieval failed at TLS and remains unresolved. This iteration made no additional real-network or private-mail probes and changed no proxy, VPN or credentials. The user needs other jobs to continue; an unrelated enterprise VPN adapter was not connected. Paid Proton Bridge, real credential revocation and broader provider compatibility remain unverified.

## 中文版本说明

**0.1.0-alpha.2 是本地候选版，未上传。** 本轮修正连接状态的表达：时间明确标为“上次成功同步”，失败、暂停和进行中的尝试不再显示成旧成功同步的数量。网络故障提供简短中英说明，仅在未暂停、密码可用且处于网络错误状态时提示自动重试；认证失败保留重新连接，证书变化和未知错误继续明确显示。

最终 177 项 Python（35.829 秒）、79 项 JavaScript 检查通过；未暂停连接的重启排队和暂停状态保留已修正。合成浏览器故障／暂停／认证及窄屏检查通过；实际界面重连后归档从一封增至两封，错误和重试提示消失，第二封可打开阅读。新解压源码及实际新 EXE 各八组 HTTP 流程通过；构建及两个 ZIP 的 CRC／全部成员字节核对通过；源码 150 文件、Windows 包 1,141 文件，指定用户名／工作区字节扫描 1,141 文件无命中，未发现实例状态或禁止的私人产物类型。ZIP 校验和以交付目录 `ALPHA-ARTIFACTS.json` 和 `.sha256` 为准。恢复使用源码辅助程序，本轮未重测原生恢复弹窗或源码 CMD。真实 Gmail 首次 120 封归档通过，但后续 TLS 故障及新信自动到信仍未解决。本轮未新增真实网络或私人邮箱探测，未改代理、VPN 或密码；另一套未连接的机构 VPN 客户端未启用。可继续查看档案或导入文件，无需中断其他任务。自动重试不等于已恢复。

已准备的包名均为 alpha.2；Windows 仍未签名，第二台干净电脑和付费 Proton Bridge 等验收仍待完成。许可仍为 [PolyForm Noncommercial 1.0.0](LICENSE)。

---

# MailCairn 0.1.0-alpha.1

Prepared 2026-11-09. **Local alpha candidate; not uploaded.** See [ALPHA.md](ALPHA.md) for release gates and verification boundaries.

## Included

- Persistent MBOX/EML archiving, exact-byte deduplication, search, plain-text reading, original mail and attachment downloads, receipts and backup/restore.
- Optional read-only INBOX archiving while the app runs, with five-minute checks, visible errors, pause/resume and disconnect without deleting archived mail.
- English and Simplified Chinese throughout the browser interface and Windows control window. Private message content remains unchanged.
- Simplified mailbox setup: Gmail address/app password, paid Proton Bridge credentials, required incoming server for other providers, optional advanced port settings and in-app instructions.
- Finite navigation/import/reading motion with reduced-motion support. Confirmed import outcomes update the real archive and remain available for review.

## Packages

- `MailCairn-0.1.0-alpha.1-windows-x64.zip`: extract the entire folder and run `MailCairn.exe`; bundled Python 3.13.17, unsigned.
- `MailCairn-0.1.0-alpha.1-source.zip`: extract, install Python 3.11+ with SQLite FTS5, and run `python app.py` from that folder. No third-party application packages or frontend build required.

Use a separate backup before evaluating a new version. Quit the previous MailCairn normally before starting the new executable. Do not delete lock files or overwrite an active archive. Restores use a new directory.

Local validation completed: 175 Python tests, 75 JavaScript checks and eight HTTP workflow groups each against freshly extracted source-package code and the new EXE. The actual extracted-source CMD launcher also passed from another working directory. Build and scoped privacy checks passed. Restore used an extracted-source helper, not the native dialog. These are same-machine results. Details: [test evidence](docs/test-results.md).

## Known limits

Real Gmail/paid Proton Bridge compatibility and a clean second Windows machine remain unverified. The connector has no Google OAuth, no Proton Free automatic connection, no multi-folder/Sent coverage and no always-running system service. The archive is unencrypted; connection settings/passwords are not included in its SQLite backup. See [known limits](docs/known-limits.md) and dated [test results](docs/test-results.md).

MBOX export escapes body lines beginning `From ` to `>From `; re-import may produce a different hash and another copy. Original EML and SQLite backup/restore preserve stored message bytes.

## 中文版本说明

本次是 **0.1.0-alpha.1 本地 Alpha 候选版，尚未上传**。提供 MBOX／EML 本地归档、去重、搜索、纯文本阅读、原文和附件下载、回执及备份恢复；可在应用运行期间每五分钟只读归档收件箱。支持完整中英界面、简化的邮箱设置和应用内说明，保留减少动态效果与真实导入进度。

Windows ZIP 需完整解压，双击 `MailCairn.exe`，无需另装 Python；源码 ZIP 需 Python 3.11+，在解压目录运行 `python app.py`。使用新版前正常退出旧版并保留独立备份，不覆盖活动档案。

175 项 Python、75 项 JavaScript、新解压源码及新 EXE 各八组 HTTP 流程通过；解压源码的实际 CMD 启动也从其他工作目录通过检查；构建与指定隐私扫描通过。恢复使用源码辅助程序，并非原生弹窗；这些结果均来自同一测试机器。

真实 Gmail／付费 Proton Bridge 与第二台干净 Windows 电脑仍待验证；未签名，不支持 Google OAuth、免费 Proton 自动接入、其他文件夹／已发送或系统常驻服务。邮件档案未加密，备份不含连接设置与密码。详见 [Alpha 清单](ALPHA.md)。

MBOX 导出会转义正文行首 `From `，再次导入可能产生不同哈希和重复副本；需要保留已存字节时，使用原始 EML 或 SQLite 备份／恢复。

MailCairn remains **source-available under PolyForm Noncommercial 1.0.0**. See [LICENSE](LICENSE), [NOTICE](NOTICE) and [COMMERCIAL.md](COMMERCIAL.md); publishing source does not grant unrestricted commercial rights.
