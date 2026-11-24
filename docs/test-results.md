# Verification report — Alpha 0.1.0-alpha.9 and historical iterations

## Alpha.9 pre-publication polish and repository cleanup — 2026-11-18

[Sanitized evidence](alpha9-evidence.json). EXE SHA-256 `54181677c6dd415191c7f7bb46737d33cf17ec574094eff81c9775bc08188a35`. Single-key shortcuts now match uppercase/lowercase letter keys (`I`/`G`/`H`) while respecting open dialogs, focused inputs and the shortcut switch; Reading room documents `,` in both languages; Getting started Step 04 documents the Windows desktop `Restore backup…` / `恢复备份…` action alongside the source CLI command; `.language-option` enforces `white-space: nowrap`; `IMAPClient` uses `NETWORK_TIMEOUT = 20`; English/Chinese READMEs were streamlined and 19 unreferenced historical screenshots were removed.

**202 Python tests passed, no skips, 51.035s** (`-W error::RuntimeWarning`), including verified 20-second IMAP socket timeout assertions on both SSL and Bridge transports. Frontend / connections / bilingual / startup checks passed **66 / 31 / 19 / 11**, `release_check.py` passed 163 source files with zero problems, and all internal markdown links resolved with zero broken links. Bundle audit passed 21 native components, 10 application modules, 10 static assets, 21 desktop notices, 3 project notices and 19 license hashes. The actual Alpha.9 EXE passed eight synthetic HTTP workflow groups (`Server: MailCairn/0.1.0-alpha.9` and visible page version); restore used the extracted-source helper.

Using ego-browser against the actual Alpha.9 EXE on an isolated synthetic archive: importing the public 20-message `sample.mbox` via UI succeeded; uppercase `Shift+H` (`#view-imports`), `Shift+G` (`#view-archive`), `Shift+I` (`#import-dialog`) and `,` (`#preferences-dialog`) worked from keyboard; English/Chinese `,` shortcut copy and Getting started Step 04 desktop + CLI restore copy matched; at a 320×568 simulated viewport (`scrollWidth` 305px), header and dialog `.language-option[data-language="zh-CN"]` computed `white-space: nowrap` at single-line 44px height. QA pixels were inspected locally, the two browser preference keys were restored, and the Ego space and owned synthetic EXEs were closed cleanly. Native pickers, second-machine compatibility, real Gmail new-message recovery and owner acceptance retain the limits below.

中文：Alpha.9 完成单键快捷键大小写兼容与 `,` 双语提示、指南第04步桌面“恢复备份…”双语说明、语言按钮 `nowrap` 防折行、IMAP 20秒超时、README首屏精简及19张无引用旧截图清理。202项Python（无跳过，51.035秒）、66／31／19／11项Node检查、163文件发布扫描、全仓Markdown链接核验、构建审计、实际EXE八组合成HTTP与Ego真机快捷键／指南文案／320px不折行验收均通过。原生窗口重测、第二台电脑、真实Gmail后续新信及用户视觉认可等限制保留。

## Alpha.8 in-place retry and modal focus refinements — 2026-11-17

[Sanitized evidence](alpha8-evidence.json). EXE SHA-256 `9a11ab42700477f9d0f30481988b2802ec40a345fea2865ca3d64ceca7b8efba`. Message reading (`readMessage`) and import receipt loading (`showReceipt`) now offer bilingual in-place retry actions (`.retry-reader` / `.retry-receipt`) on request failure, keeping keyboard focus across repeated retries and transferring focus on recovery without stealing moved focus. `openPreferences` focuses the active theme choice, and `keepDialogFocus` includes `<summary>`, skips controls inside collapsed `<details>`, and handles `<dialog>` root Tab wrapping.

**202 Python tests passed, no skips, 27.828s** (`-W error::RuntimeWarning`). Frontend / connections / bilingual / startup checks passed **65 / 31 / 18 / 11**. Bundle audit passed 21 native components, 10 application modules, 10 static assets, 21 desktop notices, 3 project notices and 19 license hashes. The actual Alpha.8 EXE passed eight synthetic HTTP workflow groups (`Server: MailCairn/0.1.0-alpha.8` and visible page version); restore used the extracted-source helper.

Using ego-browser against the actual Alpha.8 EXE at 1280×800 on a fresh synthetic archive: importing the public 20-message `sample.mbox` via UI succeeded; saving Lamplight (`dark`) and reopening Reading room focused `input[name="theme"][value="dark"]`; switching to Other email in Connect mailbox verified `#connection-advanced > summary` focus, forward/reverse Tab wrapping when collapsed, and `#connection-port` focus after expanding `<details>`; blocking only the test Page's `/api/messages/2` or `/api/messages/3` and `/api/imports/1` through CDP exposed bilingual `重试` / `Try again` buttons, and unblocking then pressing `Enter` recovered the full message body (`#reader` focused) and receipt checksum (`.receipt-actions` focused). Screenshot [alpha8-reader-retry-zh.png](screenshots/alpha8-reader-retry-zh.png) pixels were inspected; the two browser preference keys were restored, and the Ego space and owned synthetic EXEs were closed cleanly. Native pickers, second-machine compatibility, real Gmail new-message recovery and owner acceptance retain the limits below.

中文：Alpha.8 新增读信与导入回执加载失败时的就地双语重试与键盘焦点保持、阅读设置打开聚焦当前主题及弹窗 `<summary>` / 折叠 `<details>` 焦点边界控制。202项Python（无跳过，27.828秒）、65／31／18／11项Node检查、构建审计、实际EXE八组合成HTTP与Ego真机20封导入／主题聚焦／折叠面板Tab循环／单封与回执CDP拦截重试恢复均通过；已查看截图、恢复两个原始偏好键并结束空间与自有进程。原生窗口重测、第二台电脑、真实Gmail后续新信及用户视觉认可等限制保留。

## Alpha.7 modal focus wrap and bilingual singular/plural grammar — 2026-11-17

[Sanitized evidence](alpha7-evidence.json). EXE SHA-256 `7c574d2e0cf16e87880ec90ec4184b49f0fc936c2829da786d55b9e9298c3ac3`. Modal dialogs now wrap `Tab` and `Shift+Tab` across visible, enabled, non-inert controls while keeping modified shortcuts and native interior focus intact; archive summaries, attachment counts and clip accessible labels, duplicate/record counts and review lines handle 0/1/2+ English singular/plural grammar while leaving Simplified Chinese and original mail text untouched.

**202 Python tests passed, no skips, 26.656s** (`-W error::RuntimeWarning`). Frontend / connections / bilingual / startup checks passed **62 / 31 / 17 / 11**. Bundle audit passed 21 native components, 10 application modules, 10 static assets, 21 desktop notices, 3 project notices and 19 license hashes. The actual Alpha.7 EXE passed eight synthetic HTTP workflow groups (version `0.1.0-alpha.7` confirmed in `Server` header and page text); restore still used the extracted-source helper.

Using ego-browser against the actual Alpha.7 EXE with the public 20-message synthetic archive, 320×568 preferences wrapping passed (`reset-preferences` → `Tab` → `[data-language="en"]`, `Shift+Tab` → `reset-preferences`, no horizontal overflow), and opening message 1 after waiting for `.reader-body`, `.message-flight` removal, finite animations completion and `#reader` transform `none` measured 20px `.reader-body`, document width 305px at 320px viewport and untouched body text. Reloading at 800×600 retained `dark`/`large`/`compact`/`full` preferences, English/Chinese switching preserved plural grammar and message bodies, disabling Motion produced zero `.message-flight` and zero running finite animations, and the two saved browser preference keys were restored to their pre-test values. Screenshot [alpha7-reader-dark-320.png](screenshots/alpha7-reader-dark-320.png) pixels were inspected; owned synthetic EXEs and Ego task space were closed cleanly. Native pickers, second-machine compatibility, real Gmail new-message recovery and owner acceptance retain the limits below.

中文：Alpha.7 新增弹窗 `Tab` / `Shift+Tab` 首末循环与英文单复数修复。202项Python（无跳过，26.656秒）、62／31／17／11项前端／连接／双语／启动检查、构建审计与实际EXE八组合成HTTP通过；Ego真机验证实际EXE的320×568弹窗循环、大字号20px窄屏读信、刷新保留偏好、中英切换单复数与关闭动效，并已查看截图、恢复两个原始偏好键并结束空间与自有进程。原生窗口重测、第二台电脑、真实Gmail后续新信及用户视觉认可等限制保留。

## Alpha.6 startup recovery — 2026-11-16

[Sanitized evidence](alpha6-evidence.json). EXE SHA-256 `59ce87b4b7fe458ab14327e52817f23a391f2427b3187aeba745effbe2e3f332`. Independent startup recovery now runs before the business scripts, records failures before the DOM exists, and handles missing scripts, parse/top-level exceptions and early binding failures without relying on the translation module. A 12-second message describes a slow startup honestly; a definitive failure cancels that timer. Reload preserves an unexchanged session link; readiness removes startup listeners/timers and restores temporary disabled states and focus. Normal use adds no recovery copy.

**202 Python tests passed, no skips, 38.168s**, RuntimeWarning treated as errors, after the startup changes and before the release-version metadata bump. Targeted HTTP passed 22; frontend / connections / bilingual / new independent startup checks passed **61 / 31 / 16 / 11**. The bundle audit passed 21 native components, 10 application modules, **10 static assets**, 21 desktop notices, 3 project notices and 19 license hashes. The actual Alpha.6 EXE passed eight synthetic HTTP groups, including complete startup.js bytes; restore still used a source helper.

Using ego-browser and a synthetic source server, missing app/i18n, syntax, top-level and binding errors displayed a usable English/Chinese recovery panel. Enter reloaded the complete page and recovered. A held stats response produced the slow-startup message, then late success restored controls and moved focus out of the hidden recovery panel. The first delay injection had paused before the header timer was cancelled and was closed at 10s; the fixture was corrected and the intended case passed in the same space. This was not a diagnosed product timeout defect.

Separately, **the actual Alpha.6 EXE** displayed two imported synthetic messages with recovery hidden. Blocking only that test Page's app.js through CDP immediately exposed recovery with the unexchanged fragment retained. The block list was cleared, Enter reloaded, both messages returned, import was enabled and the exchanged fragment was removed. The screenshot was viewed; no system/proxy setting was changed. Ego space 7 was finished, source fixture shut down and only the path-verified owned EXE stopped.

The original first-navigation cause remains unconfirmed. A separate source review found 21 concurrent static requests byte-identical; saturation of all 16 request workers can close new connections, but no evidence shows it happened then. The new recovery layer does not guarantee its own operation if startup.js cannot load. Native pickers, second-machine compatibility, real Gmail new-message recovery and owner acceptance retain the limits below.

中文：Alpha.6增加独立启动恢复层，202项Python、61／31／16／11项前端／连接／双语／启动检查、构建核对及实际EXE八组流程通过。真实Ego验证主脚本／翻译缺失、语法／顶层／绑定失败、键盘重试和慢启迟到恢复；实际EXE阻止自身主脚本后可明确提示并在解除阻止后恢复。原始偶发原因仍未知，不能宣称已定位；bootstrap自身加载失败、原生恢复重测、二机及真实Gmail后续新信等限制仍保留。

## Alpha.5 actual build — 2026-11-16

[Sanitized evidence](alpha5-evidence.json). The actual Alpha.5 EXE SHA-256 is `32a5d73df73efd2f9d2361fbb1d325fd7811a32e19d49b30065e28044895bd67`. **201 Python tests passed, none skipped**, in 25.768s with RuntimeWarning treated as an error; Store/parse targeted checks passed 55. Frontend / connections / bilingual checks passed **61 / 31 / 16**. Bundle reconciliation passed 21 native components, 10 application modules, 9 static assets, 21 desktop notices, 3 project notices and 19 license hashes. Eight actual-EXE synthetic HTTP workflow groups passed; their restore path used an extracted source helper, not native desktop file pickers.

In the actual EXE with ego-browser, a background file import inserted a new row and displaced the currently read old row from a full 50-result page. The old body remained open, desktop scroll stayed 180→180 and focus transferred to the reader. At a simulated 390px viewport (375px document), reading state, body and the Back button's focus remained intact. History and receipt keyboard navigation focused search immediately; an intentionally delayed search response did not steal focus after the user moved to the filter button.

The real UI imported three synthetic EML files, downloaded a filtered MBOX and reimported that artifact. It contained three records: reimport added one converted message and deduplicated two unchanged messages. Top-level Content-Length headers and continuations were removed only from the export copy; body text and original EML bytes remained intact. The original EML download matched the input exactly. Final isolated archive checks passed for 58 messages, stored raw hashes, SQLite, FTS and receipts. Focused Python coverage also exercises LF/CRLF, repeated mixed-case length headers, folded continuations, body literals, following headers and attachments.

The initial regression harness missed an awaited search and queried detached nodes as though connected; both test defects were corrected before the passing run. A large object assertion caused an OOM during test diagnosis; this is not evidence of a product memory leak. Browser gates were bounded and used only synthetic messages. The browser task and owned test services were closed. Earlier Alpha.5 screenshots were captured during reader entrance and are local QA, not stable publication screenshots.

A subsequent isolated actual-EXE visual check imported the public 20-message fixture through the UI. Stable [screenshots and scope](screenshots/README.md) now cover the Chinese empty archive, English/Chinese desktop reader and simulated 390px reader. Captures waited for the real `.message-flight` and finite animations to finish (reader transform `none`); pixels were inspected. Opening from the narrow list placed the reader at the viewport top without horizontal overflow. Two ordinary startup-link navigations then initialized successfully, displayed 20 messages and removed the session fragment. The first navigation of this visual task had stayed at the static opening state without app.js initialization until a same-page reload; its cause is unconfirmed and has not been attributed to the product or network. The later successful checks do not explain that observation. Ego space 6 was finished and only its path-verified synthetic EXE was stopped; no user process, private mail or network settings were changed.

**Scope:** the native Windows picker/restore acceptance in the next section used the dated Alpha.4 build. It has not been repeated on Alpha.5. Real Gmail new-message recovery, paid Proton Bridge, a clean second computer, physical mobile/low-end hardware, screen-reader output and owner visual acceptance remain unverified. Packaging and launch-entry switching must be checked against the eventual Alpha.5 artifact manifest; a passing build is not publication or owner approval.

中文：Alpha.5实际EXE已通过201项Python（无跳过）、61／31／16项前端／连接／双语、构建核对及八组合成HTTP流程。真实Ego浏览器验证后台导入不切换正在阅读的旧信、保留滚动与焦点；历史／回执的迟到搜索不抢焦点。实际导入三封、导出MBOX再导入，新增一封转换记录、去重两封，原EML字节不变；最终58封合成邮件完整性通过。新版原生恢复选择器、第二台电脑、真实新信自动到达及用户视觉认可仍未完成。下方均为各自日期／构建的历史证据。

## Internal candidate and local acceptance — 2026-11-16

The 11/16 internal build passed bundle reconciliation (21 native components /10 app modules /9 static resources /21 desktop notices /3 project notices /19 license hashes) and eight synthetic actual-EXE HTTP workflow groups. EXE SHA-256 `88791ba28fce389f4b4f1cc4364108b07ef86da725516d97eaf6ace16f05978d`; still internally labelled alpha.4, distinguished by build date/hash. The 11/13v3 build and ZIP remain historical snapshots. No GitHub upload or final owner acceptance has occurred.

[Sanitized evidence](candidate-20261116-evidence.json). **200 Python tests passed, none skipped**, in 25.097s with RuntimeWarning promoted to errors; targeted credential/sync/HTTP/desktop checks passed57. Frontend / connections / bilingual DOM checks passed **59 / 31 / 16**. New regressions cover remembered↔session-only credential rollback, opaque unreadable prior values, failed writes, rollback failure blocking sync until reconnect, and the distinct new-account cleanup warning. A bounded independent review also checked lock ordering and verified a concurrent credential update survives rollback. All credentials and mail were synthetic.

An isolated real browser confirmed the initial mailbox-discovery request could fail, then recover automatically at the normal polling interval and populate one synthetic message without a manual poll/sync action. An actual import followed by a two-second search delay retained focus on the user's filter button after the response. The existing-account rollback warning translated in place between English and Chinese and exposed reconnect; a same-invocation390px viewport check measured document width375px with no horizontal overflow. The first test fixture incorrectly reused the fake manager's call-log property as a counter; that fixture was corrected and rerun in the same browser task.

Four new checks use real Tk widgets/workers and archives with substituted file pickers/browser launch: restore success, cancellation, corrupt backup and busy-state blocking. An initial full-suite run emitted a Tcl finalization warning; joining owned desktop workers, clearing mock/widget references and collecting Tcl cycles on the creating thread removed it in the rerun. Cross-file crash atomicity for credentials/settings, restart-persistent reconnect-required state and automatic orphan-credential cleanup remain unsupported.

Separately, the **same actual 11/16 EXE** completed native Windows acceptance in the normal user session: select a synthetic backup, select a fresh destination, restore and reach Ready, open the original empty archive, reopen the restored archive, cancel another restore without changing archives, then quit using the desktop button. Post-close read-only checks found zero original messages and one message in both backup and restored copy; SQLite integrity was `ok`, original mail bytes matched `sample.eml`, stored hashes matched raw bytes and the backup, and the restored FTS contained one row. The sandbox desktop was initially inaccessible; launching the test in the normal user session resolved targetability. A file-picker automation input error was corrected by clicking existing folders. No system/network permissions were changed. Native screenshots showing personal Explorer sidebar entries were excluded from public artifacts.

A separate [forced-process-termination experiment](crash-recovery-20261116-evidence.json) imported 250 synthetic text emails using the source Store API with unchanged production batch thresholds. A runtime parser gate at message 125 observed 124 rows in the importing transaction but only 100 rows and receipt items from an independent connection. The parent killed only its owned subprocess. Reopening preserved the committed 100, rolled back 24 uncommitted rows and recovered the receipt as `interrupted`. Reimport added 150 and deduplicated 100, ending with exactly the 250 original hash values, valid stored raw hashes, SQLite/index/receipt checks and 250 unique-token queries returning one result each. This is a source-level process crash test, not packaged-EXE termination, physical power loss or cross-file credential durability.

The isolated synthetic services and native test process were stopped. A clean second Windows computer is currently unavailable, per the owner; that check remains pending. This local acceptance does not establish real Gmail new-message recovery, paid Proton Bridge, physical power-loss safety, browser directory-picker transport, low-end hardware, screen-reader output or owner visual acceptance.

中文：11/16实际候选已构建，200项Python（无跳过）、59／31／16项前端／连接／双语、包核对及实际EXE八组合成HTTP流程通过。另已实际点击Windows原生选择器完成备份恢复、切回原档案、重新打开恢复档案、取消恢复和关闭。原档案0封、备份／恢复各1封合成邮件；原文、哈希、索引和SQLite完整性核对通过。独立强制终止实验保留100封已提交记录、回滚24封未提交记录；重导250封新增150、去重100，原文／索引／回执均通过。测试环境没有真实账号，未修改用户邮件或网络。用户目前没有第二台电脑，其兼容性和真实新信自动到达等缺口继续保留，不影响本机检查，也不据此宣称发布验收完成。

Local packaging: 167 source files passed the release boundary check. The Windows candidate ZIP contains 984 files; CRC and every member's bytes matched the candidate folder. Scoped filename and UTF-8/UTF-16 checks found no prohibited private artifacts or tested username/workspace bytes. These are finite checks, not comprehensive privacy/security certification. The source ZIP is regenerated from the final checked source and likewise reopened for CRC and full-member equality. Final ZIP checksums are recorded beside the artifacts in `CANDIDATE-20261116-ARTIFACTS.json` and `.sha256` files; EXE identity remains the hash above.

## Internal candidate — 2026-11-13

**Current v3 candidate:** [sanitized evidence](candidate-20261113-evidence.json). Python **191 total / 189 passed / 2 skipped** in 34.230s; frontend / connection / bilingual DOM checks **58 / 30 / 15 passed**. Package reconciliation passed and the actual EXE passed eight synthetic HTTP workflow groups. EXE SHA-256: `28b812608f31301f65dc2c1c96e9e5b1176b1f5a1f9f791dc34baaf305b36152`. This includes the stable mailbox-card update, search-owned date-validation recovery and saved Subtle/Rich light choice. Rich opening is bounded to 64 particles / 4.8s, success feedback to 42 / 1.8s; default remains Subtle. No replay/demo control was added.

An isolated real browser verified persisted bilingual light settings, finite completion, zero canvas drawing under OS reduced motion, actual synthetic EML import/count update and recovery after correcting invalid dates. One instrumented local sample recorded a 2.9ms maximum RAF callback and no >50ms long tasks; this is not total frame cost or low-end performance evidence. An initial cross-round viewport override did not persist (1180px), so it is excluded from narrow evidence. A separate **actual packaged EXE** browser test applied and measured the override in the same invocation: viewport390px, preferences client/scroll width320px, document scroll width375px, no horizontal overflow. Screenshots were inspected; native-window restoration, physical devices and owner visual acceptance remain pending. All isolated test services and browser tasks were stopped; the existing user launcher/private archive were left alone.

中文：最新v3候选已重新构建，包核对及实际EXE八组合成流程通过；191项Python中189通过、2跳过，前端／连接／双语检查58／30／15项通过。真实浏览器验证光效保存、双语、自然结束、减少动态效果优先、合成邮件实际导入及日期错误恢复；打包版390px设置无横向溢出。原生恢复仍由源码辅助流程替代验证，不能视为原生窗口通过；另一台电脑、真实新信自动到达及用户视觉验收仍未完成。下文为历史节点，不能覆盖本段最新范围。

Latest source after v2: **56 frontend, 30 connection and 15 bilingual DOM checks passed**. Mailbox rendering now reuses unchanged cards by account ID/signature and updates busy buttons without replacing cards. Changed status labels receive one bounded local transition; count-only changes do not replay it. A dedicated status region replaces whole-list live announcements. An isolated real browser with two synthetic accounts confirmed the other card and focused button retained identity during the first mailbox's syncing→idle change; only the changed badge animated. A subsequent count update preserved the announcement and other focus with no badge animation. The shared DOM shim's `insertBefore` now honors its reference argument, enabling meaningful order/reuse tests. Release scanning passed 161 files. This update is not in v2, was not tested with a real screen reader/provider or low-end device, and does not prove actual spoken output.

中文：v2 后续源码通过 56／30／15 项前端／连接／双语检查及161文件发布扫描。真实浏览器两个合成账号验证局部状态变化不会替换另一卡片或其焦点，只有变化状态标签播放一次动效；仅数量变化不重播、不改写状态摘要。整列表 live 区域已替换为独立状态摘要。尚未打入 v2，未做真实读屏器播报／服务商／低性能实机验证。

Latest v2 build: EXE SHA-256 `389c267c93ce0e3ef5d0f6954caa59b75a63631937e06eae31a956b00f3fd4ac` (still internally labelled alpha.4). It includes the pagination recovery, background-arrival, settings/recovery, filter, mailbox-focus and disconnect-cleanup changes described below. Bundle reconciliation passed 21 native components, 10 application modules, 9 static resources and the reviewed notices/hashes. The actual EXE passed eight synthetic HTTP workflow groups; restore used the source helper, not the native dialog. The isolated test process was stopped and the user's default launcher was not changed.

Pagination recovery: **56 frontend, 28 connection and 15 bilingual DOM checks passed**. A real browser using 60 synthetic messages verified a failed page request retained the displayed 1–50 range, reader and list scrollTop 180; keyboard retry reached range 51–60 with ten rows, scrollTop 0 and focus on the first new row. Search-owned errors cleared after success. Both a synthetic service error and target-page offline emulation were exercised. Native disabling of the focused retry initially lost focus; replacing it with guarded aria-disabled state fixed the issue and the browser test was rerun. The last full Python run remains 191 tests / 189 passed / 2 skipped, performed before this frontend-only pagination update.

中文：最新 v2 内部候选已包含下文近期修复，包核对及实际 EXE 八组合成 HTTP 流程通过；恢复仍由源码辅助服务验证，原生窗口和第二台电脑未通过，用户入口未替换。分页恢复后前端／连接／双语检查 56／28／15 项通过，真实浏览器验证失败保留旧页、滚动与读信，键盘重试到正确页并恢复焦点。最新全量 Python 仍为此次前端改动前的 191 项（189 通过、2 跳过）。下文“未打包”描述保留其当时历史范围，不适用于 v2。

Latest source-only filter/action update: **191 Python tests ran in 36.361 seconds: 189 passed, 2 skipped**; **54 frontend, 28 connection and 15 bilingual DOM checks passed**. Disconnect persistence now precedes credential deletion; synthetic regressions cover settings failure and credential cleanup failure before/after deletion. A cleanup warning is preserved as `connection.warning` in the HTTP envelope and displayed as a persistent bilingual UI error. No real credential files were touched. There is no cross-file transaction or automatic orphan-credential cleanup.

An isolated real browser with a synthetic manager verified filter opening animation, immediate sender-input focus, rapid closing with no pending surface transition, attachment-checkbox keyboard toggling/underlined focus, mailbox busy-card focus, pause→resume focus restoration, no focus theft after moving to navigation, and bilingual disconnect-cleanup warnings. An initial browser run exposed the HTTP-envelope mismatch missed by the first DOM fixture; both implementation and fixture were corrected, and browser verification reran successfully. This is not a real provider, screen-reader or low-end-device test; these changes are not in the candidate EXE below.

中文：最新源码全量 Python 191 项中通过 189 项、跳过 2 项（36.361 秒），前端／连接／双语 DOM 检查 54／28／15 项通过。真实合成浏览器验证筛选动效与键盘焦点、邮箱忙碌／完成焦点及中英文凭据清理警告。接口封装不一致曾被浏览器验收发现，已修正并复核。未操作真实凭据；不保证跨文件原子性或自动清理残留凭据，尚未纳入下方候选。

Later source-only settings/recovery update: desktop-compatible English/Chinese recovery instructions replace terminal-only guidance; settings group headings are 13px instead of 11px. 21 HTTP tests, 53 frontend DOM checks and 15 bilingual DOM checks passed. In a real isolated browser, six palette combinations (two themes × three accents) yielded a minimum computed text contrast of 5.53:1 across six sampled text roles. Large type, compact spacing and disabled motion survived reload; body text measured 20px. At a 390px simulated viewport, the settings dialog had no internal horizontal overflow and headings measured 13px. A one-second simulated network latency confirmed immediate Back focus and no focus theft after moving focus to navigation before the message completed. Invalid-session recovery was checked in both languages. These are bounded synthetic checks, not a complete accessibility, phone or low-end performance audit. This update is not in the EXE described below.

中文：后续源码将恢复说明改成桌面窗口入口与通常启动链接，设置分组标题改为 13px；21 项 HTTP、53 项前端与 15 项双语检查通过。真实浏览器六组配色、六类文字抽样最低对比度 5.53:1；大字号／紧凑／关闭动效刷新后保留。390px 模拟视口无设置框横向溢出；模拟 1 秒延迟时，加载中返回按钮可聚焦，移开焦点后成功响应不抢回；中英会话失效说明通过。尚未打入下方候选，不代表完整无障碍或低性能实机验收。

Later source-only interaction update: **53 frontend, 26 connection, 15 bilingual DOM checks passed**. Background refresh now animates only newly visible IDs; explicit searches retain bounded entrance choreography. An isolated real desktop browser with synthetic mail checked growth from two to three messages: only the new ID received entrance animation, selected mail and keyboard focus stayed on the prior ID, reader content stayed identical, unchanged refresh replayed no entrance, and there was no page horizontal overflow. This used a diagnostic invocation of the background-refresh branch, not live provider polling. The browser task was finished and the synthetic service was signaled to stop. This update postdates the EXE hash below and is not in that binary; no narrow viewport or low-end hardware claim follows.

中文：后续源码更新通过 53／26／15 项前端／连接／双语 DOM 检查。真实桌面浏览器以合成数据验证后台刷新只让新邮件入场，旧选中项、焦点及阅读内容保持，重复刷新无重播，页面无横向溢出。使用诊断调用触发后台刷新分支，不代表真实邮箱轮询验收；此改动晚于下方 EXE 构建，尚未进入该包。

Current source regression: **189 Python tests ran in 38.330 seconds: 187 passed, 2 skipped**. JavaScript DOM-shim checks: **52 frontend, 26 connection, 15 bilingual**. These cover bounded interaction and synthetic failure cases; they are not a layout, screen-reader or real-provider audit. Source-release scanning passed 161 files.

The rebuilt internal Windows EXE retains the alpha.4 version label and has SHA-256 `6243f0cdca6cd01f9cf4d05ed9d3909a15d2b13b604c22111ccd99ba60dd4b6f`. Bundle reconciliation passed 21 native components, 10 application modules, 9 static resources, 21 desktop notices, 3 project notices and 19 license-manifest hashes. The actual EXE passed eight synthetic HTTP workflow groups, including import, search, raw mail, attachments, duplicate/export handling, invalid inputs, integrity and backup/readback. Restore/readback used a source helper, not the native Restore dialog. The default user launcher was not replaced.

Native window acceptance remains incomplete: the isolated process and API were available, but Windows automation returned no targetable candidate window. The identified synthetic test process was stopped. No personal archive, provider connection, proxy or VPN was changed. Real Gmail automatic new-mail delivery, paid Proton Bridge, a second clean Windows machine, signing and owner visual acceptance remain unverified.

中文：本轮全量 Python 189 项中通过 187 项、跳过 2 项；前端／邮箱连接／双语 DOM 检查 52／26／15 项通过，发布扫描 161 文件通过。重新构建的内部候选通过包内容及许可核对，实际 EXE 八组合成 HTTP 流程通过。恢复回读由源码辅助服务完成；原生窗口因自动化未发现可操作窗口而未完成验收。最新窄屏异步焦点保护有 DOM 测试，尚无新增真实浏览器复核。用户启动入口未替换，真实 Gmail 新信自动同步等边界维持未通过状态。

## Alpha 0.1.0-alpha.4 — Windows reserved-port startup, 2026-11-10

A real exclusive bind to the saved desktop loopback port failed with **WinError 10013**; Windows listed that port inside a reserved range. An exclusive bind using an OS-assigned loopback port succeeded. This is a local startup diagnosis, not a Gmail/proxy connectivity test; public evidence omits the user's exact saved port and reserved range.

The desktop retries once on `127.0.0.1:0` only for Windows 10013/10048 or `EADDRINUSE`, then persists the server's actual assigned port. It does not first probe TCP availability or change reservations, firewall, proxy, administrative rights or other network settings. Generic `EACCES` and unrelated failures still propagate. Cleanup after retry failure is covered.

**32 targeted desktop/instance tests passed in 6.197 seconds.** Independent review found no blocker. No new full-suite or JavaScript execution is claimed for this bounded hotfix; the 181 Python / 80 JavaScript alpha.3 results and mixed benchmarks below retain their historical scope. No reader optimization ships. The actual EXE started successfully with a reserved saved port, selected an OS-assigned port, then reused that same port after a normal close and restart. [Alpha.4 evidence](alpha4-evidence.json).

Build reconciliation passed **21 native components, 10 application modules, 9 static resources, 21 desktop notices and 19 hashes**. EXE SHA-256: `4d6d8654eeabeea2f4f5892288a23f1231e4890f90ca6ce4725ff804cb912e6a` (not a ZIP checksum). [Versioned build evidence](desktop-build-alpha4.json). This round does not claim a new eight-group HTTP smoke run or full-suite run. The local port fix does not establish recovery of the separate Gmail TLS failure.

The actual workspace `Open-MailCairn.cmd` now points to alpha.4 and was invoked successfully with the Chinese controller. HTTP/API/instance checks returned 200, identified server version alpha.4 and the correct default archive, and confirmed that the persisted port matched the running listener. No message contents were read. The user app remains running. The Gmail test launcher remains alpha.1; the user's active Gmail instance is preserved. No proxy/firewall/OS reservation changes or private-mail probes were performed. Final ZIP CRC and member-byte checks passed; checksums are recorded in ALPHA4-ARTIFACTS.json and .sha256 files; unsigned/second-machine/provider limitations remain.

中文：真实本机保存端口绑定遇到 Windows 10013，系统分配端口绑定成功。桌面仅对明确的端口绑定冲突／保留错误重试一次并保存分配结果；不修改系统网络规则。32 项定向测试通过；实际 EXE 回退／重启及默认入口健康检查通过，最终 ZIP 核对通过，校验和见 ALPHA4-ARTIFACTS.json 和 .sha256，本轮未重新执行旧版全量测试，也未加入阅读器优化。私人 Gmail 入口及活动实例保持原状。

## Alpha 0.1.0-alpha.3 — mixed-mail search and input races, 2026-11-10

**181 Python tests passed in 32.247 seconds; 80 JavaScript checks passed (41 frontend, 15 i18n, 24 connections).** The fixed cases are punctuation-separated CJK terms, mixed CJK/accented Latin terms and attachment-name fragments. Terms retain AND semantics in both search and filtered export. A partial attachment-name index keeps the fallback restricted to messages with attachments; schema version remains 1. Query/sender edits immediately invalidate older responses during the 250 ms debounce window; stale success/error responses cannot replace results or re-enable export/pagination.

The [frozen alpha.2 baseline](benchmark-mixed-baseline.json) reproduced three failures; the [alpha.3 final run](benchmark-mixed-final.json) passed all 12 query cases using identical fixture and benchmark-script hashes. The synthetic fixture has **1,000 messages (250 each English/Chinese/Japanese/Korean), 250 attachments of 65,536 bytes, and 24,694,850 source bytes**. Import took **2.697697 s**, duplicate import **0.507256 s**, full verification **0.257568 s**. Selective search medians were **4.45–4.85 ms**; common Latin 28.18 ms, CJK 24.54–25.01 ms, mixed 18.90 ms and filename fragment 9.42 ms. Exact-fidelity samples and full integrity passed. Cancellation committed 300 messages; resuming added the remaining 700. These are cached local measurements for this bounded workload, not network-sync throughput, attachment-heavy/20 GiB capacity or universal latency guarantees. The 1,000,000-character preview cap is applied after decoding and is not a parser-memory bound.

Actual browser checks returned 250 results for each formerly missing query. Downloading the filtered `保修，CAFÉ` export and reimporting it produced the exact original 250-message hash set. The downloaded attachment matched all 65,536 bytes. Chinese 1440px search and English 390px reader screenshots were inspected; no horizontal overflow, language switching preserved query/results, Back returned to 250 results and reduced motion left zero running animations. The short interaction sample reported no long tasks; no sustained-FPS or low-end-device claim follows. [Structured evidence and screenshots](alpha3-evidence.json).

Freshly extracted source and the actual alpha.3 EXE each passed eight HTTP workflow groups. Restore used an extracted-source helper, not the native Restore dialog; the source CMD launcher was not rerun. Build audit passed **21 native components, 10 application modules, 9 static resources, 21 desktop notice files and 19 hashes**. EXE SHA-256: `60114895ca3ac83120d12d88e5d2ced32979769aeb677aba2657744f573976ef`. This is not a ZIP checksum. [Versioned build evidence](desktop-build-alpha3.json). Final alpha.3 packaging is recorded below; alpha.2 package/privacy counts remain historical.

Final alpha.3 packaging contained 158 source files and 1,149 Windows-package files. Both ZIPs passed CRC and full-member byte checks; tested code/runtime were unchanged. Scoped username/workspace-byte scans found no matches, and no prohibited private-artifact types were found. Current ZIP checksums are recorded in `ALPHA3-ARTIFACTS.json` and `.sha256` in the delivery directory. These finite checks do not establish comprehensive privacy/security certification.

Only synthetic QA processes were closed. The real user app, private Gmail archive, proxy and network settings were untouched; no new external-network/private-mail probe occurred. Real Gmail initial 120-message import remains a partial pass, with automatic new-message TLS failure unresolved. Signing, second-machine testing and paid Proton Bridge remain outstanding. No upload occurred.

中文：本轮 181 项 Python（32.247 秒）、80 项 JavaScript 通过；相同 1,000 封／250 个 64 KiB 附件样本由旧版三项查询失败变为 12 项全部通过。实际浏览器三类查询均为 250 条；筛选导出重导后原文哈希集合完全一致，附件字节一致。窄屏／语言／减少动态效果检查及新源码／新 EXE 各八组 HTTP 流程通过。最终 ZIP 核对通过；24,694,850 字节样本不代表 20 GiB 或大规模附件容量。真实 Gmail 自动新信仍未恢复，本轮未改用户应用或网络。下方版本计数均为历史记录。

## Alpha 0.1.0-alpha.2 — connection recovery UI, 2026-11-10

**79 JavaScript checks passed: 40 frontend, 15 i18n/folder and 24 connection checks.** Node 24.22.1, synthetic DOM fixtures only. New cases exercise English/Chinese network guidance, successful-time preservation after failure, saved totals, suppression of failed/in-progress counters, retry-copy eligibility, authentication controls, certificate warnings and verbatim unknown diagnostics. These DOM checks do not establish browser layout or real-provider recovery.

The final post-fix Python run passed **177 tests in 35.829 seconds**. An earlier interim run passed 176 tests in 47.930 seconds. The restart regression covers unpaused saved connections returning as queued, paused state preservation, persisted credentials, cursor and recovery after a partial failure. The desktop executable was rebuilt successfully. Build reconciliation, source/EXE smoke checks and final ZIP checks passed as detailed below; current ZIP checksums are recorded in the delivery manifest and `.sha256` files. Alpha.1 package counts, hashes and workflow results below retain their historical scope.

The product now calls `last_sync` **Last successful sync**, matching the backend's meaning. It does not combine a previous successful timestamp with counters reset by a failed attempt. Network-error guidance does not ask Gmail users to edit preset server/port settings or infer a bad password. Retry copy requires an unpaused network-error state with credentials available; it does not promise that the connection will recover. Authentication, certificate and unknown errors remain distinct.

Synthetic browser checks observed one saved message and the retained successful time after a network failure, no misleading failed-zero counts, no retry copy while paused, and Password needed / Reconnect without network-retry text after an authentication failure. Chinese 1440px and English 390px views had no horizontal overflow. Reconnecting through the actual UI increased saved mail from one to two, returned Up to date and cleared error/retry text. View mail opened the archive and the second message was opened successfully; the synthetic browser workspace was finished.

Freshly extracted source code and the **actual rebuilt EXE each passed eight HTTP workflow groups**: authentication/empty state; request guards; version/assets; import/search/read/raw/attachment/receipt; duplicate/export handling; invalid-input recovery; integrity; and restore/readback. Restore used an extracted-source helper, **not a native restore-dialog test**. The source CMD launcher was not rerun this round; its earlier evidence stays under alpha.1.

Build reconciliation passed **21 native components, 10 application modules, 9 static resources, 21 desktop notice files and 19 notice hashes**. The EXE SHA-256 is `48946dbf878d66927705bc51c81530dc5855e1cbb25c234023d96c39c1f29e4e`. This is not a ZIP checksum. Final packaging passed with **150 source files and 1,141 Windows-package files**. Both ZIPs were reopened: all CRC checks and full-member byte comparisons passed. Packaged source matched the checked source; tested code and runtime were unchanged. A scoped scan of 1,141 files found no tested username/workspace bytes; no instance state or prohibited private-artifact types were found. These finite checks do not certify comprehensive privacy or security. Current ZIP hashes are in the delivery directory’s `ALPHA-ARTIFACTS.json` and `.sha256` files. [Structured alpha.2 evidence](alpha2-evidence.json). Workspace default and Gmail scripts deliberately remain on alpha.1 to preserve the user's active process; the alpha.2 EXE is available directly.

Both isolated synthetic test processes were closed after verification; the user’s real app was left untouched. No additional real Gmail, proxy, VPN or other network probing was performed for this iteration. The earlier real Gmail result remains a partial pass: 120 initially archived messages; subsequent automatic new-message retrieval unresolved at TLS. The user's proxy remains unchanged and an unrelated enterprise VPN adapter was not connected. Other tasks must keep running. Paid Proton Bridge, credential revocation, a clean second Windows machine and signing remain outstanding.

中文：Alpha.2 最终 177 项 Python（35.829 秒）、79 项 JavaScript 检查通过；此前 176 项、47.930 秒是中间记录。合成浏览器故障／暂停／认证和窄屏检查通过；实际界面重连后归档从一封增至两封，已同步状态恢复，错误与重试提示消失，并成功打开第二封。新源码／新 EXE 各八组 HTTP 流程及构建核对通过；最终源码 150 文件、Windows 包 1,141 文件，两个 ZIP 重开后的 CRC 及全部成员字节核对通过，已测代码和运行时未变化。指定用户名／工作区字节扫描 1,141 文件无命中，未发现实例状态或禁止的私人产物类型。当前校验和见交付清单及 `.sha256`。界面使用“上次成功同步”，避免把失败尝试的数量配到旧成功时间上；自动重试提示有状态条件，不承诺恢复。本轮没有新增真实网络或私人邮件探测，真实 Gmail 自动新信仍未通过。下方旧版计数、哈希和流程仅描述其当时版本。

## Real Gmail acceptance — 2026-11-10

**Partial pass; new-message automatic arrival has not passed.** The authorized Gmail test account connected and archived 120 INBOX messages. The live UI displayed 120 and replaced its empty state. All 120 original hashes, SQLite integrity, search index and import receipts passed. A separate read-only connection unlocked the saved Windows credential and observed TLS 1.3; this is not a full application-restart test.

The user sent one test message. A read-only provider snapshot counted 121 INBOX messages, but subsequent application polling reported a connection error and retained 120 local messages and its prior UID cursor. No manual sync was triggered by the agent. Direct no-credential probes on Python 3.13.17/OpenSSL 3.5.9 and Python 3.13.1/OpenSSL 3.0.15 failed before authentication with SSL EOF/reset. In a paired check, Gmail web HTTPS (443) succeeded while IMAP TLS (993) failed. The user reports the proxy remained running and unchanged. The precise route/provider failure is **unresolved**; do not label this a password error or prove a proxy misconfiguration from these observations.

22 sync unit tests and an additional synthetic scheduled SSL-EOF recovery test passed. These explain the expected retry/cursor behavior but do not substitute for real Gmail recovery. Rule-hit evidence or a later user-authorized route comparison, actual app restart, credential revocation, paid Proton Bridge and a second clean Windows computer remain pending. The user declined node changes; no proxy or VPN was disconnected. Explicit local HTTP and SOCKS tunnels also failed at TLS. An unrelated enterprise VPN adapter is installed but not connected, per the corrected user statement; no causation is established. No TLS verification, network setting or mailbox credential was changed. No private message content, account address, token or real-mail screenshot is included. [Aggregate evidence](gmail-live-evidence.json).

中文：真实 Gmail 首次连接、120 封收件箱归档、实际界面更新及完整性检查通过。新测试信已到 Gmail（121 封），但应用后续收信连接在登录前的 TLS 握手阶段失败，本地仍为 120 封；**自动到信验收未通过**。网页 HTTPS 正常不代表收信连接正常；代理一直运行是用户确认的事实，具体链路原因尚未定位。保留原档案和连接游标；用户不希望换节点或中断其他任务，停止额外探测。未修改代理、密码或 TLS 校验。

The following sections retain their dated historical scope.

Executed 2026-11-09. **Local review candidate; owner acceptance and GitHub publication are pending.** Measurements apply to the stated machine, workload and browser, not general production certification.

## Alpha 0.1.0-alpha.1 — local release checks

**175 Python tests passed in 32.624 seconds, including 12 release-boundary tests. All 75 JavaScript checks passed: 40 frontend, 15 i18n/folder and 20 connection checks.** This was the completed alpha.1 full regression run; it does not verify alpha.2. The counts in later sections remain historical checkpoints.

Freshly extracted source-package code and the new Windows EXE each passed **eight HTTP workflow groups**, using two explicitly synthetic messages and a 303-byte attachment. The groups cover authentication/empty-archive handling; host/origin/mutation guards; version and bundled assets; MBOX import/search/body/raw/attachment/receipt; duplicate and export-escaping behavior; invalid-file recovery; integrity; and no-overwrite restore with HTTP readback. Both instances exposed version `0.1.0-alpha.1`.

The first source instance used an extracted-source HTTP helper. A separate run then started the actual extracted `Start-MailCairn.cmd` from another working directory and passed all eight workflow groups; its HTTP header, page/sidebar and startup log showed `0.1.0-alpha.1`. Restore for these workflows used the source helper, **not the native Restore dialog**. The Windows workflow used the actual new EXE on the existing test machine, not a clean second computer.

The MBOX smoke case confirmed an important boundary: exported body lines beginning `From ` are quoted as `>From `. Re-import can therefore change raw hashes and add a second copy of the same logical message. MBOX is not guaranteed to preserve raw bytes across export/re-import. Original EML downloads and SQLite backup/restore preserve stored message bytes.

Build reconciliation passed **21 native components, 10 application modules, 9 static resources and 19 notice hashes**. The executable SHA-256 is `748c6a266d9484c43661cca46bdaaf122fda2c4d0f664d7c7c7a4735807effc2`; it is not the ZIP checksum. Final documentation packaging can change ZIP hashes without changing this EXE.

The source release-boundary check passed across **143 files**. Privacy checks examined **983 binary-package files and 154 ZIP members** for the tested OS-username/workspace-root bytes, with no matches. **10,034 Python code objects** contained no absolute filenames. All **26 included screenshots** were visually reviewed as synthetic. These finite checks do not establish that every possible sensitive-data pattern has been detected, and are not an independent security audit.

No real Gmail or paid Proton Bridge sync is claimed. A Gmail test account is available, but local credential input and actual connection are still pending. Clean-machine Windows acceptance, provider policy/revocation testing, signing and broader accessibility testing remain outstanding. No GitHub upload occurred. See the [Alpha checklist](../ALPHA.md) and [handoff](../HANDOFF.md) for current remaining work.

中文：本轮 175 项 Python（含 12 项发布检查）、75 项 JavaScript 通过；新解压源码和新 EXE 各八组 HTTP 流程通过；另从其他工作目录实际运行解压源码 CMD，也通过八组流程且版本一致。恢复使用解压源码辅助程序，未新测原生恢复弹窗。构建及指定发布边界／隐私扫描通过。MBOX 转义可能导致重导入重复，保留字节请用 EML 或数据库备份。真实 Gmail／付费 Proton Bridge、第二台干净 Windows 与公开上传仍未完成。

## Plain setup and paper hover-return — latest UI iteration

2026-11-09: **40 frontend +15 i18n +20 connection checks passed**. Backend code did not change;163 Python passes below remain the previous iteration's baseline. The simplified form was exercised against a real synthetic local STARTTLS server: optional custom Bridge port worked, hidden invalid-port validation revealed its field, count changed0→1 and the reader showed the saved message. In-app help opened the chosen provider, cleared the password and offered a correct route back. Gmail hides server/port; custom providers still require their actual incoming server. No provider compatibility is inferred from this fixture.

Nine settled axe scenes covered English/Chinese setup, the new guide, dark mode and320/390/1440px windows:0violations and no horizontal page overflow. Screenshots were visually inspected. A test initially clicked a setup action inside a closed guide section; opening that section fixed the test, with no product change. A minimized Ego window was restored within the same workspace before finishing captures.

Paper geometry was calculated from actual CSS across1001 hover/return samples and all6 sheet pairs. The rear-to-next plane clearance changes from−4.667px with the legacy tilt to+4.328px after the correction; the smallest other pair remains+3.846px. All entrance endpoints match rest transforms. Actual browser hover-exit frames at0/100/250/400/550/700ms were inspected, plus rapid re-entry, reduced motion and320px layout. The model-plane check is not a claim that every entrance trajectory or browser engine has been proven.

Windows scripts now prefer the nearby packaged review app for an ordinary double-click. The default script actually launched it and its authenticated sync API returned200. Both scripts preserve visible errors/nonzero exits with invalid explicit source arguments from another working directory. A root Open-MailCairn.cmd provides a single local entry. No old personal process or archive was terminated; only this iteration's isolated test processes were cleaned up. [Evidence](usability-evidence.json), [bilingual setup instructions](mailbox-setup-guide.md).

## Automatic INBOX archive — latest candidate, 2026-11-09

**163 Python tests passed in27.883s;40 existing frontend,15 i18n and16 new persisted connection-UI checks passed.** Normal Windows profile tests exercised real DPAPI protection/decryption; restricted-profile capability failure explicitly falls back to memory-only credentials. Remote CI has not run. Commands: `python -B -m unittest discover -s tests -q`, `node scripts/check_frontend.mjs`, `node scripts/check_i18n.mjs`, `node scripts/check_connections.mjs`.

Actual Chromium UI connected through the real Python IMAP transport to an explicitly synthetic local STARTTLS server. First sync changed0→1 and showed readable mail. A second server message arrived with no Sync now click: the next EXAMINE was **300.364seconds** later with the default300-second setting; count/list became2 and the selected first reader stayed open. No polling interval was shortened for this test. Wire records contain EXAMINE and BODY.PEEK only, no writable SELECT/STORE/CLOSE/EXPUNGE; every LOGIN followed TLS.

Additional real UI/wire checks passed: a new UID containing existing raw bytes counted as a duplicate; removing source UID1 retained its archive; pause disabled manual sync, resume collected the next message; disconnect removed the account but retained3messages; an invalid password produced a localized error and reconnect recovered without duplicate archive growth. Downloaded original bytes matched exactly; a downloaded SQLite backup restored3messages, passed integrity checks, and contained no connection/credential sidecars. Synthetic passwords were absent from archive/config/credential files on disk. Core tests cover UIDVALIDITY resets, failed-item cursor retry, bounded literals, certificate pinning before LOGIN, malformed persisted state, shared writer exclusion and shutdown/cancellation.

The actual packaged EXE connected to the same synthetic server and protected its password using DPAPI. After controlled termination of only the test process, a new server message was added. Relaunch retrieved it without another password prompt, retained the port and advanced UID4→5 with count3→4. A real browser issue was found: reusing a tab with a new `#session=` link did not reload initialization. A bounded hashchange handler now exchanges the new launch token; the final packaged existing-tab flow passed and two regressions cover it. This is not a new claim of native close-dialog testing: normal close is covered by lifecycle regression and earlier native-window evidence.

Nine settled axe checks across source/final package had0violations and no horizontal page overflow at observed320/390/1077/1440CSS-pixel widths. They include bilingual setup, connections and dark mode; the final320px IMAP form has a full-width164px host input instead of the initial cramped column. Screenshots were visually inspected. This is not physical-phone, screen-reader or WCAG certification. Synthetic test only: **no real Gmail or paid Proton Bridge account was authenticated**; the user's free Proton account remains unsupported by this official route.

Final artifact reconciliation passed21native components,10application modules,9static resources,21desktop notice files,3project notices and19manifest hashes. No new third-party application dependency was added. The user's existing running bundle and personal archive were left untouched. Unsigned/clean-machine/provider-compatibility limits remain. [Machine-readable evidence](sync-evidence.json), [research and competitors](mail-sync-research.md), [known limits](known-limits.md).

中文：默认5分钟自动到信、重复／删除留存、暂停／继续、断开、认证失败重连、原文／备份恢复及打包版凭据保存和重启续传已实测。测试服务器和邮件均为合成，不能冒充真实 Gmail／Proton 兼容性验收。免费 Proton 仍不能通过本版官方 Bridge 连接器自动接入。

## Useful interactions and truthful import states — 2026-11-09, review 2

**40 frontend behavior checks +15 i18n/folder checks passed. 21 HTTP tests passed (3.871s); JS syntax passed.** This is a frontend iteration; the previous123-test Python full-suite run remains the preceding baseline, not a new execution claim.

Real Chromium checks used synthetic mail only. A new empty archive changed from0to1 after oneEML: initial guidance disappeared, count/list/body updated before the completed action became available. Repeat import left the count at1. ZIP rejection left it unchanged and offered no nonexistent mail target. DamagedMBOX plus a6-message MBOX produced5added,1duplicate,1file needing review; history contained the actual runs. Each committed file refreshes the list while later queue items continue. Tests cover refresh failures, partial/cancelled batches, deferred job creation, modal closing and new-import races; none may rewrite a committed import as failed or navigate using stale review state.

Removed standalone replay/light-scene/preview controls. Natural opening remains; actual navigation animates, real reader content receives a700ms sheet opening with aligned crease/header/body treatment, and import outcomes transition into compact review. Browser observation confirmed both flight and reader animations while actual text was already available; rapid selection left the last selected message and zero residual flights. Reduced motion stopped both while retaining the body. Mouse focus has no enclosing outline; keyboard focus remains marked.

Seven settled axe scenes passed with0violations: English reader/history1440, Chinese dark preferences1440, Chinese dark reader1440/390, Chinese dark preferences320, Chinese import-choice320. All had no page horizontal overflow. Initial file-input label findings were fixed and rechecked. This is not screen-reader, physical-phone or WCAG certification. A test-script attempt to click an already-hidden mobile list was corrected to inspect the active reading state; it was not recorded as a product defect.

New packaged EXE actually imported6synthetic messages and rendered updated language controls and reader; removed demo controls absent. Artifact reconciliation passed21native components,7application modules,9static resources,21desktop notice files,3project notices and19manifest hashes. The user's earlier running executable and archive were preserved; its static resources are updated without process termination. Signed/clean-machine release validation remains pending. [Evidence](interaction-evidence.json).

中文：首封导入状态更新、重复／错误结果、实际导航与阅读动效、语言按钮及焦点检查通过。当前为本地候选迭代，不代表用户已满意，也未上传GitHub。

## Bilingual UI, provider roundtrip and Windows desktop — 2026-11-09

**Current result: 123 Python tests passed (18.227s), 28 frontend behavior checks and 14 i18n/folder checks passed.** Python 3.13.17 and Node 24.22.1; JavaScript syntax checks passed. Counts below this section are historical checkpoints.

- Real authorized Proton web account: exported one ordinary message as EML, imported it, searched it, downloaded identical original bytes and all10 embedded attachment payloads, downloaded a backup, restored to a new archive and verified search/original bytes. No message sent or deleted; original unread state restored. Personal mail and screenshots are not included in source or release. This is not a bulk-export completeness test.
- Gmail Takeout and Proton bulk Export Tool: current official routes checked; no actual Gmail export or Proton bulk CLI run. Explicit synthetic6-message MBOX and nestedEML inputs exercise Chinese search, duplicate imports, ZIP rejection, malformedMBOX, empty results and integrity checks.
- Folder import:6EML accepted,6JSON skipped via browser-injected synthetic FileList with real fixture bytes/relative paths and real HTTP ingestion. Ego's directory injection returned no files; native browser directory-picker transport remains unverified. Ordinary file inputs were exercised.
- Both UI languages:1440/390/320px home layout, reader, dark theme, preferences, dates/counts, known errors and accessible names; private text resembling UI labels remains byte-for-byte untouched.8 settled axe scenes had0 violations. An early320px preferences capture was taken mid-animation and failed contrast; the settled recheck passed. This is not WCAG certification or a real screen-reader test.
- Paper titles remain within clipped paper surfaces; full scene title/footer fit; dark paper keeps dark ink. The user's final judgment of the motion remains pending.
- Real Proton HTML initially generated709lines (689blank); corrected conversion yielded37readable lines. Regression tests cover nested layout tables, preservedpre whitespace, optionalhead closing and plain-text preservation. Legacy HTML preview is rederived at read time; raw mail, stored body and FTS index are not rewritten.
- Packaged Windows64 executable imported6synthetic messages and downloaded a backup. Actual native Windows file dialogs selected that backup, restored it into a new folder, then reopened the original archive. Both archives contain the same6raw messages as the backup, SQLite integrity isok. Close button removed instance metadata; reopening acquired the archive successfully, reused the same port and retained the browser'sEnglish choice. English and Chinese controller layouts inspected at150%DPI.
- Runtime bundle:Python3.13.17, signed official installer provenance,21native components confined to selected runtime,7application code objects and9static files match source. Notice reconciliation is recorded in[desktop build evidence](desktop-build-evidence.json). Executable is unsigned and has not been tested on a second clean machine.

中文结论：双语、真实Proton单封导入取回／备份恢复、Windows窗口恢复／切换／重启已完成。Gmail实账号导出、Proton批量导出、浏览器原生目录选择器和第二台干净机器尚未实测。交付为可试用的本地候选版，未获用户最终视觉确认、未上传GitHub。

## Reopening a running archive — 2026-11-09

**90 Python tests passed in 16.348 seconds**, using `python -B -m unittest discover -s tests -v`. Real subprocess checks cover second-launch reuse of the same session, continued service by the original process, strict restore locking, lock release after exit, stale metadata replacement and rejection of untrusted targets. Live HTTP tests cover authentication, exact archive identity, occupied read slots and metadata cleanup ownership. A browser-failure main-flow test covers `False`, `OSError` and `webbrowser.Error`, verifies entry into the serving loop and subsequent socket, metadata and lock cleanup. Browser failure itself is simulated; actual browser UI opening was not retested in this backend fix.

Both launchers now opt into verified reuse with `--open-existing`; ordinary CLI startup remains exclusive. A currently running older version cannot be discovered through the new metadata protocol: use its existing browser session or stop it once and relaunch after imports finish. The user's running process and archive were left intact.

Release-boundary check passed across **78 files**. Two focused temporary-directory probes confirmed rejection of the new instance JSON and temporary record patterns in custom archive directories. Independent implementation review completed; no new dependency or frontend change was introduced.

## Envelope and paper-transfer motion — 2026-11-09

The owner requested stronger motion after the typography revision. A 2400ms
envelope sequence now releases the seal, opens its flap and lifts four sheets
through different depths; cleanup occurs at 2500ms. Message selection combines
a 720ms textless decorative flight with a 700ms opening of the actual reader.
Both work with the existing Quiet light preference; no intensity switch is needed.

**28 frontend behavior checks and syntax checks passed.** New checks cover flight
geometry, offscreen-origin rejection, textless/ARIA-hidden decoration, stale
callbacks, cancellation across pending responses, and Back before fetch completion.
Backend and dependencies were unchanged; the preceding 76 Python tests were not
rerun without a relevant change.

Real browser checks: first-open/replay, 20-message archive selection, rapid
selection, LANTERN search, narrow reader/back focus, OS reduced motion, and zero
remaining flight nodes after completion. Sampled light/dark reader axe checks
reported zero violations. Independent screenshot review found no material
clipping, covered controls or unreadable primary text in the supplied captures.

Fixed-viewport phase sampling every100ms from0 to2400ms bounded all paper/seal
horizontal extents to725.4–1396.0px at1440px,19.8–352.3px at390px and23.9–283.9px
at320px. This caught and fixed a scale/translation anchoring error and an
intercepting decorative layer. Full-page screenshots change viewport height and
trigger lifecycle cancellation, so final phase images use direct fixed-viewport
CDP capture. Phase screenshots are explicitly paused samples, not FPS evidence.
Separate real-time samples recorded14 hero and11 reader snapshots (6 included
the flight), no >50ms long tasks and zero remaining animations at completion.
These small automated samples do not establish low-end GPU or sustained-frame-rate
performance. The user's desired visual impact remains unconfirmed.

Current evidence: [spectacle-evidence.json](spectacle-evidence.json).
Screenshots: `envelope-desktop.png`, `envelope-390.png`, `envelope-320.png`,
`reader-flight.png`. Older sections below are historical iterations.

## Typography and integrated interaction revision — 2026-11-09

The owner rejected the earlier typography, repeated microcopy, square controls,
box input focus and disconnected effects. This revision bundles Hanken Grotesk
and Newsreader locally, removes ornamental labels and repeated slogans, rounds
controls, uses persistent underline input focus, unfolds the paper fan, moves the
navigation marker and opens the real reader surface around the selected row.

- **76 Python tests passed in 9.453 seconds**. New HTTP checks verify exact font
  bytes, TTF table bounds, MIME/nosniff headers and blocked unlisted/traversal paths.
- **25 frontend behavior checks and JavaScript syntax passed**. New coverage
  verifies bounded entrance/replay, nav positioning, reduced motion, WAAPI
  cancellation during rapid selection, stale completion callbacks, unchanged
  message content/focus and unsupported-animation fallback.
- Actual browser: 20 synthetic messages imported; reimport produced 0 added /
  20 duplicates; invalid MBOX displayed a recoverable failure; LANTERN body search
  returned one message. Both bundled fonts reported loaded.
- Actual pointer tilt changed the paper to 1.8deg / 3.9deg. The real reader used
  a 420ms perspective opening; no running animation remained after completion.
  OS reduced motion stopped the fan and reported zero running animations.
- Final sampled light reader, dark reader, dark preferences and narrow layout
  axe WCAG 2 A/AA + 2.1 AA checks reported zero violations. An earlier audit caught
  selected-row contrast and transient opacity fade; both were fixed. Search
  input outline is now none with a separate persistent bottom-line indicator;
  forced-color keyboard buttons retained a visible 2px system-color outline.
- 390px layouts have no horizontal document overflow. Actual narrow message
  selection places the reader at the viewport top and the body around y=346px;
  Back restores list scroll/focus. A reviewer initially flagged a screenshot of
  a resized desktop selection; corrected real-interaction evidence resolved it.

Screenshots: `editorial-home.png`, `editorial-home-narrow.png`, `desktop.png`,
`dark.png`, `mobile.png` under `docs/screenshots`. Current hashes and sampled
browser records: [editorial-evidence.json](editorial-evidence.json).
The independent visual review found no remaining issue in its reviewed fix;
it is not evidence of subjective owner acceptance, universal FPS, low-end GPU
performance or complete WCAG conformance. The older sections below are historical.

## Stronger-light iteration — 2026-11-09

After the owner requested stronger visual effects, the frontend gained a persistent Light the room entry, five light shafts, source glow, layered particles and pointer-responsive paper depth. Full scene uses up to 110 particles for a target of eight seconds; Quiet uses 24 for 4.2 seconds. Canvas backing pixels are capped at 1.5 million per effect.

The revised Node suite passed **18/18 checks**, including command-dialog close races, identity-transform clearing, pixel budgets, replay cancellation and lifecycle stops. Python business code was unchanged in this round; its earlier 74-test evidence below was not unnecessarily rerun. Actual browser checks passed scene opening from a populated 20-message archive, Commands → scene, Stop, OS reduced-motion, 390px no-overflow layout, zero reported axe violations and working message search after closing the scene. Final desktop and narrow screenshots were inspected.

At emulated DPR 2 the canvas used 1,497,852 backing pixels. A browser sample recorded no long tasks over 50ms, 26 draw/clear calls and completion after 8.958 seconds. The automation scheduling does **not** establish stable 30/60 FPS or low-end-device performance; the eight-second target is checked on the next scheduled frame. There is no new claim of user acceptance or publication.

## Prior integrated baseline: automated checks

Windows 11 AMD64; Python 3.13.1; SQLite 3.45.3 with FTS5; Node 24.22.1. The final integrated source passed:

| Command | Observed result |
| --- | --- |
| `python -m unittest discover -s tests -v` | 74 tests, 8.526 seconds, no failures/errors |
| `node --check mailcairn/static/app.js` | Passed |
| `node scripts/check_frontend.mjs` | 11 checks passed |
| `python scripts/release_check.py` | Passed; final documentation inventory checked separately |

The Python suite covers parsing/MIME, Unicode, exact deduplication, search/filtering, raw and attachment exports, receipts, cancellation/replay, backup/restore, corruption, access controls, real CLI locking and bounded HTTP concurrency. The 24 new cases include:

- Real subprocess termination after two committed records and during the next uncommitted batch: only the committed messages, FTS entries and receipt counters survive; replay finishes the complete 240-record fixture.
- Injected receipt insertion failure rolls back the matching message and FTS change; progress callbacks see only committed data through independent connections.
- Deep MIME and a parser failure between valid records are isolated rather than aborting later messages.
- Concurrent writes cannot split receipt counters/items or search totals/page rows into different snapshots.
- Restore rejects stale FTS and inconsistent receipts, handles publication failure, refuses a target created during validation, and reports unsupported hard links without leaving a partial target.
- Invalid/duplicate HTTP lengths, Transfer-Encoding, interrupted uploads, header deadlines, request-worker overload and heavy-read limits; job polling remains available while heavy downloads occupy their slots.

The Node checks run the real frontend code with a small DOM shim and controlled asynchronous responses. They cover search/reader races, cancellation, unavailable or corrupted preference storage, invalid filters, literal-text rendering and failed receipt verification. **They do not emulate browser layout or establish accessibility.** GitHub CI uses Windows, Linux and macOS with Python 3.11 and 3.13, plus Node 24. All six jobs passed for the [published Alpha.9 tag](https://github.com/Osmanthusfish/mailcairn/actions/runs/44240859265).

## Real browser checks

Executed in Ego Lite Chromium against the running loopback service, with synthetic mail:

- Empty archive → actual 20-message MBOX upload → seven attachments → searchable persisted collection.
- Body search `LANTERN` → one result; nonexistent text → empty state; reversed dates → error and disabled filtered export.
- Original EML bytes matched the stored original; attachment bytes matched MIME decoding; reopened filtered MBOX contained exactly one expected record; downloaded receipt contained 20 items matching its counters.
- Browser-downloaded SQLite snapshot restored to a new directory. All 20 hashes, SQLite, FTS and receipts passed; the documented CLI restore launched as an independent application and browser search worked.
- Reimport → zero additions and 20 duplicates; malformed MBOX → explicit failed receipt with the reason and no message loss.
- UI integrity check → 20/20 hashes, SQLite, index and receipt checks passed.
- Synthetic HTML email with a script, remote image and malicious subject markup → literal subject and inert body; no executable reader nodes, no script flag, no external resource request.
- Theme, accent, type size and density persisted across reload. Corrupted preference JSON recovered to defaults without blocking mail; a simulated storage exception still applied settings for the visit and displayed the limitation.
- Ctrl/Command-K command selection opened Reading room; list arrow keys moved selection and retained keyboard focus.
- At 390px, opening a message positioned the reader at the viewport top; Back restored the selected row focus and prior page position. At 320px, the layout and 18px reading type had no horizontal document overflow.

One cross-context restore probe could reopen its SQLite file inside the Windows sandbox but not from an elevated process. Repeating the documented restore and startup entirely in one permission context succeeded. This is recorded as a test-environment boundary; it is not evidence that mixed sandbox ACLs are supported.

## Accessibility and motion

Development-only **axe-core 4.14.0** tested WCAG 2 A/AA and 2.1 AA rule tags in the empty state, preferences, reader and narrow layout. Final stable reader checks passed with **zero reported violations in all six light/dark × cedar/blue/umber combinations**; the six preference combinations also had zero. These results do not certify WCAG conformance or replace assistive-technology/user testing.

The first narrow audit found two icon-only buttons without accessible names; stable labels and 44px targets were added and the audit rerun successfully. Theme-switch sampling exposed temporary foreground/background mismatches; synchronized palette updates fixed them. Reader motion now keeps text fully opaque throughout its 200ms displacement.

Actual Canvas pixels were sampled during the light scene. The full-scene run stopped at about **6.535 seconds**, with zero active loops afterward. This automation sample recorded 91 clear/draw calls; it is **not** a 30/60 FPS performance guarantee. Implementation ceilings are 42 particles per effect, DPR 2 and a nominal 30 draw/s cap. OS reduced-motion stopped a running scene immediately and disabled preview. Switching to a background tab produced a real visibility event with zero remaining loops; returning did not restart it.

A separate 7.703-second full-scene observation recorded no browser long tasks over 50ms; this is one local automation sample, not a device-wide responsiveness guarantee. System light/dark following and disabling single-key shortcuts while retaining Ctrl-K were also exercised.

The screenshot set uses synthetic fixtures only. Desktop light/dark and narrow reading layouts were visually inspected. Actual touch hardware, screen readers, other browser engines and low-end-GPU frame pacing remain untested.

## Same-input performance comparison

Reproduce the generator using `python scripts/benchmark.py --help`. Workload: 10,000 synthetic text-only messages, approximately 10 KB body text each, **no attachments**. Both runs used 103,084,670 source bytes (98.31 MiB) and produced a 230,932,480-byte SQLite archive.

| Measurement | Earlier baseline | Quality iteration |
| --- | ---: | ---: |
| Import time | 131.031 s | 15.607 s |
| Throughput | 76.32 messages/s | 640.74 messages/s |
| Added / skipped | 10,000 / 0 | 10,000 / 0 |
| Three marker searches | 3.364–5.768 ms | 3.747–5.686 ms |
| Integrity check | 1.103 s | 1.118 s |
| Peak process working set | 29.05 MiB | 29.605 MiB |

Import was approximately **8.40× faster** on this workload. SQLite, 10,000 raw hashes, FTS and receipt consistency all passed. Raw results: [baseline](benchmark-result.json), [quality iteration](benchmark-polish.json). The 20 GiB configuration limit is not a tested-capacity claim. Attachment-heavy archives, CJK search at scale, 20 GiB ingestion and other platforms were not benchmarked.

## Source boundary checks

The clean-source scanner rejects runtime databases and sidecars, local environment files, private-key/certificate containers, temporary uploads and obvious credentials. A separate temporary-root probe passed 21 positive/negative cases, including `.mjs` credential scanning and exact synthetic-fixture boundaries. Three real symlink cases were **skipped** because Windows refused symlink creation (error 1314); do not count them as passing. The scanner is a focused release guard, not a comprehensive secret/security audit.

The product still has zero third-party application packages. The optional browser-audit package is outside the project and is not distributed. See [dependency audit](dependency-audit.md).

## Historical compatibility evidence

Before this iteration, the [Python announcement list January 2019 archive](https://mail.python.org/pipermail/python-announce-list/2019-January.txt) was compared with Python's independent `mailbox.mbox` reader: 22/22 messages, zero skips, hashes/SQLite/FTS passed. Downloaded 2026-11-09; 54,640 bytes; SHA-256 `98fa7903f2311d53e18123560e35db096d882173986f3eabe9217269ed825e57`. It exposed an envelope-spacing issue now covered by a regression test. This older corpus is format evidence, not market research, and is not distributed.

The original project migration preserved all 60 moved-file hashes and passed the then-current 50 tests. That historical result does not substitute for the integrated checks above.

## Remaining validation

Owner visual/interaction acceptance, real-user pilots, remote CI, macOS/Linux execution, real mobile hardware, screen-reader evaluation, low-end-rendering measurements, attachment-heavy scale tests, power-loss/storage-failure testing and an independent security audit have not been completed. See the full [known limits](known-limits.md). No GitHub repository or release was published during this iteration.
