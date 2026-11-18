# Alpha 0.1.0-alpha.9 — internal candidate

Prepared on 2026-11-18 (`0.1.0-alpha.9`). Packages are `MailCairn-0.1.0-alpha.9-windows-x64.zip` and `MailCairn-0.1.0-alpha.9-source.zip`; match them to `ALPHA9-ARTIFACTS.json` and `.sha256`. EXE SHA-256: `54181677c6dd415191c7f7bb46737d33cf17ec574094eff81c9775bc08188a35`.

Alpha.9 completes pre-publication polish: case-insensitive single-key shortcuts (`I`/`G`/`H` work under Caps Lock) with bilingual `,` Reading room help copy, desktop `Restore backup…` / `恢复备份…` guidance alongside the CLI command in Getting started Step 04, `white-space: nowrap` on `.language-option` pills, a 20-second IMAP socket timeout (`NETWORK_TIMEOUT = 20`), streamlined English/Chinese README front-door presentation, CI command parity, zero broken markdown links, and removal of 19 unreferenced historical process screenshots (~2.98 MiB).

202 Python tests (`-W error::RuntimeWarning`) and 66/31/19/11 frontend/connection/bilingual/startup checks passed; bundle audit and eight synthetic actual-EXE HTTP workflow groups passed; ego-browser against the actual Alpha.9 EXE verified uppercase/comma shortcuts, bilingual shortcut and Step 04 backup restore copy, and 320×568 single-line language pills. Exact scope is in [test results](docs/test-results.md) and [Alpha.9 evidence](docs/alpha9-evidence.json). Native pickers were not reaccepted on this build. Real Gmail automatic-arrival TLS recovery, paid Bridge, a clean second machine, low-end hardware, screen readers and owner visual approval remain outstanding.

中文：alpha.9 为发布前体验与门面打磨候选（未上传）。补齐单键快捷键大小写兼容与 `,` 阅读设置双语提示、使用指南第04步桌面“恢复备份…”说明、语言按钮 `nowrap` 防折行、IMAP 20秒超时、README首屏精简及清理19张无引用历史过程图（减重约2.98MB）。202项Python、66／31／19／11项Node回归、构建审计、实际EXE八组HTTP与Ego真机验证均通过。原生窗口重测、真实Gmail后续新信、第二台电脑与视觉认可仍待完成。

---

# Historical Alpha 0.1.0-alpha.8 — internal candidate

Prepared locally on 2026-11-17; not uploaded or finally accepted. Packages are `MailCairn-0.1.0-alpha.8-windows-x64.zip` and `MailCairn-0.1.0-alpha.8-source.zip`; match them to `ALPHA8-ARTIFACTS.json` and `.sha256`. EXE SHA-256: `9a11ab42700477f9d0f30481988b2802ec40a345fea2865ca3d64ceca7b8efba`.

Alpha.8 adds in-place bilingual retry actions with keyboard-focus preservation when message reading or import receipt loading fails, focuses the saved active theme radio when opening Reading room, and refines modal focus wrapping to handle `<summary>`, collapsed `<details>`, and `<dialog>` root focus.

202 Python tests (RuntimeWarning as error) and 65/31/18/11 frontend/connection/bilingual/startup checks passed; bundle audit and eight synthetic actual-EXE HTTP workflow groups passed; ego-browser against the actual Alpha.8 EXE verified 20-message synthetic UI import, active-theme focus on reopening Reading room, `<details>` collapsed/open Tab cycling, bilingual `.retry-reader` / `.retry-receipt` failure states, `Enter` keyboard retry recovery without focus theft, and preference key restoration. Exact scope is in [test results](docs/test-results.md) and [Alpha.8 evidence](docs/alpha8-evidence.json). Native pickers were not reaccepted on this build. Real Gmail automatic-arrival TLS recovery, paid Bridge, a clean second machine, low-end hardware, screen readers and owner visual approval remain outstanding.

中文：alpha.8 为本地内部候选，未上传、未完成最终用户验收。新增读信与回执失败的就地双语重试及键盘焦点保持、阅读设置打开聚焦当前主题单选框及弹窗 `<summary>` / 折叠 `<details>` 焦点边界处理。202项Python、65／31／18／11项Node检查、构建审计、实际EXE八组合成HTTP及Ego真机验证均通过。原生选择器重测、真实Gmail新信自动到达、第二台电脑与视觉认可仍待完成。

---

# Historical Alpha 0.1.0-alpha.7 — internal candidate

Prepared locally on 2026-11-17; not uploaded or finally accepted. Packages are `MailCairn-0.1.0-alpha.7-windows-x64.zip` and `MailCairn-0.1.0-alpha.7-source.zip`; match them to `ALPHA7-ARTIFACTS.json` and `.sha256`. EXE SHA-256: `7c574d2e0cf16e87880ec90ec4184b49f0fc936c2829da786d55b9e9298c3ac3`.

Alpha.7 wraps modal dialog `Tab` / `Shift+Tab` navigation between visible, enabled, non-inert controls and aligns English singular/plural copy for archive summaries, attachment counts/labels, duplicates, records and import reviews while preserving Simplified Chinese and untouched mail text.

202 Python tests (RuntimeWarning as error) and 62/31/17/11 frontend/connection/bilingual/startup checks passed; bundle audit and eight synthetic actual-EXE HTTP workflow groups passed; ego-browser verified 800×600 settings persistence, 320×568 dialog Tab/Shift+Tab wrapping, 20px narrow reading without horizontal overflow, reload persistence, disabled motion and restoration of the two saved browser preference keys. Exact scope is in [test results](docs/test-results.md) and [Alpha.7 evidence](docs/alpha7-evidence.json). Native pickers were not reaccepted on this build. Real Gmail automatic-arrival TLS recovery, paid Bridge, a clean second machine, low-end hardware, screen readers and owner visual approval remain outstanding.

中文：alpha.7 为本地内部候选，未上传、未完成最终用户验收。新增弹窗首末键盘循环及英文单复数修复；202项Python、62／31／17／11项前端／连接／双语／启动检查、构建审计、实际EXE八组合成HTTP及Ego真机800×600与320×568键盘／大字号阅读／偏好持久化／减少动效均已通过。原生选择器重测、真实Gmail新信自动到达、第二台电脑与视觉认可仍待完成。

---

# Historical Alpha 0.1.0-alpha.6 — internal candidate

Prepared locally across 2026-11-16/17; not uploaded or finally accepted. Packages are `MailCairn-0.1.0-alpha.6-windows-x64.zip` and `MailCairn-0.1.0-alpha.6-source.zip`; match them to `ALPHA6-ARTIFACTS.json` and `.sha256`. EXE SHA-256: `59ce87b4b7fe458ab14327e52817f23a391f2427b3187aeba745effbe2e3f332`.

Alpha.6 adds independent recovery when business scripts fail or startup is slow. Enter can reload without losing an unexchanged session link; a late success restores temporary controls/focus. Normal use has no extra recovery copy. The original first-navigation cause remains unconfirmed; failure of the recovery script itself is outside that layer's coverage.

202 Python checks and 61/31/16/11 frontend/connection/bilingual/startup checks passed; the actual EXE passed eight synthetic HTTP groups and a real Ego blocked-script→keyboard-reload test. Exact scope, including the pre-version-metadata full-suite timing, is in [test results](docs/test-results.md) and [Alpha.6 evidence](docs/alpha6-evidence.json). Native pickers were not reaccepted on this build. Real Gmail automatic-arrival TLS recovery, paid Bridge, a clean second machine, low-end hardware, screen readers and owner visual approval remain outstanding.

中文：alpha.6为内部候选，新增启动加载失败／慢启动的独立双语提示和整页重试；实际EXE与Ego恢复流程已验。原偶发原因仍未确认，原生窗口重测、真实Gmail后续新信、第二台电脑与视觉认可等缺口保留；不上传、不宣称最终交付。

---

# Historical Alpha 0.1.0-alpha.5 — internal candidate

Prepared locally on 2026-11-16; not uploaded and not finally accepted. Package names are `MailCairn-0.1.0-alpha.5-windows-x64.zip` and `MailCairn-0.1.0-alpha.5-source.zip`. Use the accompanying `ALPHA5-ARTIFACTS.json` and `.sha256` files for artifact identity. Source and actual-EXE evidence must be read with their stated build scope in [test results](docs/test-results.md).

This version preserves reading context during background imports, focuses the destination before a delayed history/receipt search, and removes top-level Content-Length metadata only from MBOX export copies. It also includes the earlier polling and credential recovery work. SQLite originals and original EML downloads are unchanged.

中文：当前为alpha.5内部候选，未上传、未完成最终验收。后台导入保留读信，历史／明细跳转先交接焦点，MBOX兼容转换保留数据库与EML原件。真实Gmail自动新信、付费Proton Bridge、第二台Windows、低性能实机、读屏器及用户视觉验收仍待完成；各项证据须按构建版本读取，不能继承旧版本未重测的验收结论。

---

# Historical Alpha 0.1.0-alpha.4 — 2026-11-10

**Local desktop startup hotfix; not uploaded. Actual EXE recovery/restart and default-launch health checks passed; final ZIP CRC and member-byte checks passed; checksums are recorded in ALPHA4-ARTIFACTS.json and .sha256 files.** Target ZIPs: `MailCairn-0.1.0-alpha.4-windows-x64.zip` and `MailCairn-0.1.0-alpha.4-source.zip`.

Alpha.4 recovers when Windows reserves or occupies the saved desktop loopback port: on Windows 10013/10048 or `EADDRINUSE`, retry once using `127.0.0.1:0` and persist the assigned port. Generic `EACCES` still fails visibly. No TCP availability probe, firewall/proxy change, OS reservation edit or administrative setting is required.

**32 targeted desktop/instance tests passed in 6.197 s; independent review found no blocker.** No full-suite rerun or reader optimization is claimed. [Alpha.4 evidence](docs/alpha4-evidence.json). Earlier alpha.3 counts, benchmark results and package scans below remain historical.

Build reconciliation passed **21 native components, 10 application modules, 9 static resources, 21 desktop notices and 19 hashes**. EXE SHA-256: `4d6d8654eeabeea2f4f5892288a23f1231e4890f90ca6ce4725ff804cb912e6a` (not a ZIP checksum). [Versioned build evidence](docs/desktop-build-alpha4.json). This round does not claim a new eight-group HTTP smoke run or full-suite run. The local port fix does not establish recovery of the separate Gmail TLS failure.

The workspace default launcher now opens alpha.4 with the Chinese controller; the Gmail test launcher remains alpha.1 to preserve the active user process. The unsigned/second-machine limits and unresolved real Gmail automatic-arrival TLS failure remain. Licensing stays source-available [PolyForm Noncommercial 1.0.0](LICENSE).

中文：本轮只修复保存端口遭 Windows 保留／占用时的桌面启动失败，一次回环端口回退后记住系统分配结果；不改代理、防火墙或系统规则。32 项定向测试通过；实际 EXE 回退、重启和默认入口健康检查通过；最终 ZIP 核对通过，校验和见 ALPHA4-ARTIFACTS.json 和 .sha256。未重跑历史全量回归、未交付阅读器优化，真实 Gmail 活动实例保持原状。

---

# Historical alpha.3 baseline — 2026-11-10

**Local evaluation candidate; not uploaded. ZIP packaging passed CRC and full-member byte checks (158 source files, 1,149 Windows-package files). Current checksums are in the delivery directory’s `ALPHA3-ARTIFACTS.json` and `.sha256` files.** Start with [English instructions](README.md#start-the-alpha) or [中文说明](README.zh-CN.md#启动-alpha-版). Target files are `MailCairn-0.1.0-alpha.3-windows-x64.zip` and `MailCairn-0.1.0-alpha.3-source.zip`.

## Current evidence — 2026-11-10

- Fixed punctuation-separated CJK, mixed accented Latin/CJK and attachment-name fragment searches. All terms use AND in search and filtered export. A partial attachment-name index retains schema version 1. Query/sender edits now reject old responses immediately during debounce.
- **181 Python tests passed in 32.247 s; 80 JavaScript checks passed** (41 frontend, 15 i18n, 24 connections).
- The same 1,000-message, 250 × 64 KiB attachment fixture reproduced three alpha.2 failures and passed all 12 cases on alpha.3. Input: 24,694,850 bytes. Import: 2.698 s; deduplication: 0.507 s; selective query medians: 4.45–4.85 ms. Fidelity, integrity and cancel/resume passed. [Baseline](docs/benchmark-mixed-baseline.json), [final](docs/benchmark-mixed-final.json).
- Browser checks confirmed each fixed case at 250 results, exact filtered-export hash-set readback and a byte-identical 65,536-byte attachment. Chinese 1440px and English 390px views had no horizontal overflow; language switching and mobile Back preserved the result context. Reduced motion left zero running animations. A short sample without long tasks is not an FPS guarantee.
- Fresh source and the actual new EXE each passed eight HTTP workflow groups. Restore used the source helper, not the native dialog; source CMD was not rerun. Build reconciliation passed 21 native components, 10 application modules, 9 static files, 21 desktop notices and 19 hashes. EXE SHA-256: `60114895ca3ac83120d12d88e5d2ced32979769aeb677aba2657744f573976ef` (not a ZIP checksum). [Alpha.3 evidence](docs/alpha3-evidence.json), [build audit](docs/desktop-build-alpha3.json).

Final packages contain 158 source files and 1,149 Windows-package files. CRC and all-member byte checks passed; scoped username/workspace-byte scans found no matches and no prohibited private-artifact types were found. Tested code and runtime were unchanged. These finite checks are not a comprehensive privacy or security audit.

## Remaining boundaries

Real Gmail initially archived 120 messages, but automatic new-message retrieval later failed at TLS and remains unresolved. This iteration used synthetic data and left user apps, the private archive, proxy and network untouched. An unrelated enterprise VPN adapter was not connected; no cause is inferred from its presence. Paid Proton Bridge and real credential revocation remain unverified.

The Windows EXE is unsigned and has not been accepted on a clean second computer. The approximately 24.7 MB mixed workload does not establish 20 GiB or attachment-heavy capacity. Preview text is capped after decoding; this does not bound parser memory. Broader accessibility, user acceptance, other platforms and independent security review remain outstanding. Current workspace default/Gmail scripts retain alpha.1 to avoid switching the user's process; alpha.3 is opened through its own executable. Do not open the same archive concurrently.

INBOX polling requires a running app; it is not an always-running service. Google OAuth, Proton Free automatic sync and multi-folder coverage are absent. The archive is unencrypted; SQLite backups exclude connection settings and credentials. Keep originals and a separate backup. MBOX export may escape body `From ` lines; use original EML or database backup for byte-preserving roundtrips. Licensing remains [PolyForm Noncommercial 1.0.0](LICENSE), source-available rather than OSI open source. No upload is authorized by local preparation.

## Historical alpha.2 baseline

Alpha.2 passed 177 Python tests (35.829 s), 79 JavaScript checks and source/EXE eight-group smoke checks. Its packages contained 150 source files and 1,141 Windows-package files; CRC/full-member checks and a scoped username/workspace-byte scan passed. These counts do not validate alpha.3 packaging. Alpha.2 fixed connection-state wording and restart scheduling, not the three search cases found later. [Historical evidence](docs/alpha2-evidence.json) and [dated report](docs/test-results.md) preserve its full scope and earlier records.

## 中文说明

Alpha.3 修复三类搜索遗漏与输入等待期间旧结果可导出的问题；181 项 Python、80 项 JavaScript、混合样本 12 项查询、真实浏览器操作和新源码／新 EXE 各八组 HTTP 流程通过。筛选导出重导后的 250 封原文哈希及附件字节一致。最终 ZIP 核对通过，未上传；旧版打包／扫描计数仅为历史证据。

真实 Gmail 仍只有首次 120 封通过，后续 TLS 故障及自动新信未解决；本轮未改动用户应用、代理或网络。Windows 未签名，第二台干净电脑、付费 Proton Bridge 和更大规模负载仍待验证。约 24.7 MB 混合基准不是 20 GiB 承诺，正文预览上限不是解析内存上限。保留邮件原件和独立备份，商业使用须符合许可或另行授权。
