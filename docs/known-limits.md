# Known limits / 能力边界

## Alpha.9 scope — 2026-11-18

Alpha.9 adds case-insensitive single-key shortcuts (`I`/`G`/`H`) and bilingual `,` shortcut copy, desktop `Restore backup…` / `恢复备份…` guidance in Getting started Step 04, `white-space: nowrap` on `.language-option`, a 20-second IMAP socket timeout (`NETWORK_TIMEOUT = 20`), streamlined English/Chinese README front doors and removal of 19 unreferenced historical screenshots. Increasing `NETWORK_TIMEOUT` improves tolerance on high-latency links, **not** routes that block or reset port 993 TLS handshakes; real Gmail automatic new-message arrival remains unresolved. 202 Python tests, 66/31/19/11 Node checks, bundle reconciliation, eight actual-EXE HTTP groups and ego-browser checks passed on synthetic data. Native Windows file-picker acceptance remains on dated Alpha.4 scope; paid Proton Bridge, a second clean computer, physical mobile/low-end hardware, screen-reader output and owner visual acceptance remain outstanding.

中文：Alpha.9 补齐单键快捷键大小写兼容与 `,` 双语说明、指南第04步桌面“恢复备份…”说明、语言按钮 `nowrap`、IMAP 20秒超时及README与无引用旧图整理。放宽连接超时提升高延迟链路容忍度，但**不能绕过封禁或重置993端口TLS握手的网络路由**，真实Gmail后续新信自动到达仍未解决。202项Python、66／31／19／11项Node检查、构建审计、实际EXE八组HTTP与Ego真机验证通过（合成数据）。原生窗口选择器验收仍为历史Alpha.4范围，付费Bridge、第二台干净电脑、低性能实机、读屏器及用户视觉认可仍未完成。

## Alpha.8 scope — 2026-11-17

Alpha.8 adds in-place bilingual retry actions for failed message reads and import receipt loads while preserving keyboard focus (without stealing moved focus), focuses the saved theme choice on opening Reading room, and refines modal Tab wrapping around `<summary>` and collapsed `<details>`. 202 Python tests, 65/31/18/11 Node checks, bundle reconciliation, eight actual-EXE HTTP groups and ego-browser real-workflow checks passed on synthetic data. Native Windows file-picker acceptance remains on dated Alpha.4 scope; real Gmail automatic-arrival TLS failure, paid Proton Bridge, a second clean computer, physical mobile/low-end hardware, screen-reader output and owner visual acceptance remain outstanding.

中文：Alpha.8 补充读信与回执失败时的就地双语重试与键盘焦点保持（不抢占已移走的焦点）、阅读设置自动聚焦当前主题与弹窗 `<summary>` / 折叠 `<details>` 焦点控制；202项Python、65／31／18／11项Node检查、构建审计、实际EXE八组HTTP与Ego真机流程验证通过（均为合成数据）。原生窗口选择器验收仍为历史Alpha.4范围，真实Gmail后续新信TLS故障、付费Bridge、第二台干净电脑、低性能实机、读屏器及用户视觉认可仍未完成。

## Alpha.7 scope — 2026-11-17

Alpha.7 wraps modal `Tab` / `Shift+Tab` focus across visible enabled non-inert controls and aligns English singular/plural counters and accessible attachment labels while preserving Simplified Chinese and literal mail text. 202 Python tests, 62/31/17/11 Node checks, bundle reconciliation, eight actual-EXE HTTP groups and ego-browser 800×600 / 320×568 checks passed on synthetic data. Existing modals rely on natural DOM order without positive `tabindex`; any future positive `tabindex` usage must revisit focus ordering. Native Windows file-picker acceptance remains on dated Alpha.4 scope; real Gmail automatic-arrival TLS failure, paid Proton Bridge, a second clean computer, physical mobile/low-end hardware, screen-reader output and owner visual acceptance remain outstanding.

中文：Alpha.7 补齐弹窗首末键盘循环与英文单复数文案，202项Python、62／31／17／11项Node检查、构建审计、实际EXE八组HTTP与Ego真机800×600／320×568检查通过（均为合成数据）。现有弹窗不使用正数 `tabindex`，如以后新增正 `tabindex` 需重估焦点排序；原生窗口选择器验收仍为历史Alpha.4范围，真实Gmail后续新信TLS故障、付费Bridge、第二台干净电脑、低性能实机、读屏器及用户视觉认可仍未完成。

## Alpha.6 startup recovery — 2026-11-16

Missing app/i18n scripts, their parse/top-level exceptions and early interface-binding failures now expose independent bilingual recovery rather than an indefinite spinner. A 12-second slow-startup message permits late success; deterministic failures retain their failure wording. Reload preserves any unexchanged session fragment. Source fault injection and actual-EXE blocked-script→keyboard-reload recovery passed; no system/proxy changes were made. **The original first-navigation cause remains unconfirmed.** This layer cannot run when startup.js itself fails to load; noscript covers disabled JavaScript, not that network failure. It is recovery guidance, not a background service restart or a fix for the separate Gmail TLS issue.

中文：Alpha.6新增启动失败／慢启动的双语提示与整页重试，已用源码故障注入和实际EXE验证；正常打开时不显示额外说明。未定位旧偶发的根因，也不能在bootstrap自身无法加载时保证恢复脚本运行；不自动重启服务，不解决独立的Gmail TLS故障。其他原生窗口、第二台电脑、实机、视觉认可和商业验证等限制继续有效。

## Alpha.5 scope — 2026-11-16

Alpha.5 preserves the currently read mail and focus across background file-import refreshes, including when its row leaves the current page. History/receipt navigation hands focus over before waiting for search, so a late response cannot take it back. Actual-EXE synthetic browser checks passed for these cases. This is not proof of live provider new-message delivery; the Gmail TLS EOF/reset limitation below remains unresolved.

MBOX export removes top-level Content-Length headers/continuations from its output copy so a converted EML can be reimported without being rejected as mboxcl. The database original and EML download remain byte-identical. Body literals and MIME part headers are not removed. Conversion can change the raw hash and create another record on reimport; deduplication remains exact-byte. Input mboxcl remains unsupported.

Alpha.5 passed 201 Python and 61/31/16 frontend/connection/bilingual checks, bundle reconciliation and eight actual-EXE HTTP groups. The HTTP restore uses a source helper. The native Windows file-picker restore described below was tested on dated Alpha.4, **not repeated on Alpha.5**. No second clean computer, paid Bridge, physical mobile/low-end device, screen-reader acceptance, independent security audit, owner visual acceptance or external user pilot has been added. Consult the matching artifact manifest for ZIP identity. A later actual-EXE UI import of the public 20-message fixture supplied stable bilingual/390px screenshots after finite animations ended; earlier mid-entrance captures remain local QA. On that visual task's first navigation the static opening screen persisted without app.js initialization until reload; the cause remains unconfirmed. Two later normal startup-link navigations passed. This observation is retained for further startup investigation, not presented as a diagnosed product or proxy defect.

中文：Alpha.5修复后台文件导入打断读信与迟到搜索抢焦点；合成实际EXE流程通过不等于真实邮箱新信自动到达通过。MBOX只在导出副本移除顶层Content-Length，原EML不变；转换后原文字节不同可能新增同义邮件，输入mboxcl仍不支持。新版201项Python及61／31／16项界面检查通过；原生选择器恢复证据仍属于旧Alpha.4。真实Gmail后续同步、付费Bridge、第二台电脑及用户视觉认可等缺口未消失。下面历史记录保留其原日期／构建范围。

2026-11-16 internal candidate update: failed mailbox reconnects now attempt to restore both prior settings and credential state, including the original remembered/session-only mode. If protected-file rollback also fails, the current session blocks that existing account until explicit reconnect and displays a warning; a failed new connection can leave an orphaned protected credential and reports that risk. This is exception recovery, not a cross-file transaction durable against crashes or power loss. The reconnect-required latch is in memory, so follow the warning and reconnect before restarting. Automatic orphan cleanup is not implemented.

2026-11-16内部候选更新：邮箱重连失败时，会尝试恢复原配置及凭据，包括记住密码／仅本次使用模式。如果凭据文件的回滚也失败，当前会话会阻止该已有账号继续同步，提示重新连接；新账号添加失败时可能残留加密凭据，会明确告知。此恢复不能保证两个文件在崩溃／断电时保持原子一致；要求重连的状态仅保存在内存中，请按提示在重启前完成重连。尚无自动孤立凭据清理。

Updated 2026-11-10 for alpha.4. This is a local review candidate; user acceptance and publication remain pending. These are intentional scope limits and unverified areas, not a claim that all possible bugs have been found.

The 11/16 actual candidate now passed native Windows backup/destination selection, restore into a new folder, switching to the original archive, reopening the restored archive, cancellation and desktop shutdown. Read-only checks confirmed the original remained empty and the restored synthetic message matched the fixture bytes/hash with a valid index and SQLite integrity. This supersedes the incomplete 11/12 native interaction for the new build; it does not verify a second computer or the browser's directory-import picker.

11/16实际候选已通过Windows原生选择器恢复、切回原档案、重新打开恢复档案、取消恢复和关闭。只读核对原档案仍为空，恢复的合成邮件原文字节／哈希、索引和SQLite完整性正常，取代11/12未完成的原生验收状态。用户暂时没有第二台电脑，继续本机检查；另一台电脑和浏览器目录导入选择器仍未验证。

Alpha.4 is a bounded desktop startup hotfix: a saved port rejected as reserved/in use is retried once on an OS-assigned loopback port, which is then remembered. Generic permission errors still fail visibly. It changes no firewall, proxy, OS reservation or administrative setting. The 32 targeted desktop/instance tests passed; actual EXE reserved-port recovery/restart and the real default-launch health checks passed. Final ZIP CRC and member-byte checks passed; checksums are recorded in ALPHA4-ARTIFACTS.json and .sha256 files. Earlier full-suite, benchmark and native-window evidence below retains its stated version/scope.

中文：alpha.4 只对明确的本机端口保留／占用错误回退一次并保存系统分配端口，普通权限错误仍上报；不改防火墙、代理或系统规则。32 项定向测试通过，实际 EXE 回退／重启及默认入口健康检查通过，最终 ZIP 核对通过，校验和见 ALPHA4-ARTIFACTS.json 和 .sha256；下方既有证据不等于本轮全量重测。

## 当前能力和限制

| 范围 | 已做到 | 边界、代价或未验证项 |
| --- | --- | --- |
| 工作流 | 每份导入完成后用实际档案数据刷新数量和列表；紧凑完成区保留成功／部分／失败结果与未启动文件数，可继续查看邮件、回执、原文和附件，或备份恢复 | 单份“查看已导入邮件”按该导入筛选，多文件“查看邮件”显示全部档案；队列不会自动掩盖错误或关闭结果。个人单机，不发信、不清理云端邮件、不支持多人或跨设备共享。 |
| 自动归档 | 可选只读 IMAP 连接，界面归档 INBOX；首次读取已有邮件，应用运行时每 5 分钟检查，支持立即同步／暂停／继续／断开；本地已存邮件不随源端删除 | Gmail 需符合条件的应用密码，本版无 OAuth；官方 Proton 路径需付费 Bridge，免费账号尚未支持自动接入。非官方 Hydroxide 存在但未验证／集成，不能推断免费接入不可能。后台支持每连接一个 ASCII 文件夹，界面不提供多文件夹；退出、关机或检查前已移走的邮件无法保证捕获。真实 Gmail 首次 120 封归档通过；后续自动新信在 TLS 阶段失败，恢复仍未验证。付费 Proton Bridge 未实测。 |
| 同步进度与凭据 | 按 UIDVALIDITY／UID 追踪；先归档后更新进度，重试按原文字节去重；Windows DPAPI 能力检测通过时可加密记住密码，否则仅内存 | 超限／解析失败停在该项前重试，不自动跳过；每封抓取生成一份导入回执，大量小邮件吞吐尚未量测。账号配置、进度和凭据不在 SQLite 备份中；恢复后重连。断开保留邮件，内存凭据退出即失效。 |
| 输入 | 常见 mboxo／mboxrd 和单独 EML；文件夹流程选择子目录中的邮件并统计跳过项 | 不支持 PST、OST、Maildir、ZIP／TGZ 直接导入、mboxcl；须先解压。不读取 Proton JSON 元数据或重建目录。合成 FileList＋真实 HTTP 已测 6 EML 导入、6 JSON 跳过，原生浏览器文件夹选择器传递尚未验证。损坏或模糊边界不能证明提供商的原始邮件总数。 |
| 去重 | 原文字节 SHA-256 完全相同才去重 | 同一逻辑邮件若由不同导出工具改写头部、空白或转义，可能保留多份；相同 Message-ID 不会被强行合并。 |
| 阅读与搜索 | 主题、地址、正文、附件名；筛选、分页、纯文本阅读 | 不保留HTML排版／内嵌图片，不搜索附件内部；最多预览和索引 1,000,000 个解码正文字符，完整原文保留；此上限在解码后应用，不是解析内存上限。标点分词后各词 AND，Latin 走词匹配并支持附件名片段，CJK 走子串；非 Gmail 语法，大档案 CJK 仍可能较慢。 |
| 容量 | 历史实测 10,000 封约 98 MiB 纯文本；alpha.3 实测 1,000 封多语言邮件、250 个 64 KiB 附件，共 24,694,850 字节，导入 2.698 秒 | 默认20 GiB／文件、32 MiB／邮件只是可调限制，不是已测上限；本次约 24.7 MB 混合样本不代表大规模附件、20 GiB 或大规模 CJK 容量。文件导入超限邮件跳过并写明细；同步超限邮件停止进度并报错，此文件导入基准不能代表网络同步吞吐。 |
| 资源 | 16个请求worker、4个重读／下载槽，上传和请求头有界 | 繁忙时可能503或连接被关闭；导出和备份需要临时磁盘空间。大邮件MIME解码仍有CPU／内存代价，不能把导入基准内存推广到所有负载。 |
| 数据可靠性 | 批事务、FULL同步、崩溃回滚未提交批次、可重导、原子备份／恢复、哈希／索引／明细核验；11/16源码强制终止实验保留100封已提交、回滚24封未提交，重导后250封原文／索引／回执通过 | 正常取消会保存当前批次已处理记录；强制终止须重导未提交记录。进程实验不是实际EXE终止或物理断电测试；摘要核验不能证明来源真实性或提供商完整导出。 |
| 恢复 | 验证后创建新档案，拒绝覆盖已有目标；真实 Proton 单封样本备份恢复通过；本机 Windows 原生选择器选取备份并恢复到新档案通过 | 目标文件系统须支持硬链接，例如NTFS；不支持FAT／exFAT目标。已测错误注入，未在真实FAT／exFAT盘运行。 |
| 隐私 | HTTP 仅监听127.0.0.1，无遥测／远程字体／邮件资源加载；可选连接会访问配置的邮件端点，Proton Bridge 自行联网 | 数据库、临时文件、备份和附件均无应用级加密；凭据侧文件和配置须保密，DPAPI 不防同用户恶意程序。下载附件后由打开它的应用负责安全。不能公开暴露服务端口。 |
| 视觉与个性化 | EN／中文直接切换按钮；档案阅读室风格、明暗／系统主题、3墨色、字号、密度、快捷键和动态效果开关 | 切换语言保留筛选、导入与阅读状态，不翻译邮件原文；日期按当前界面语言显示。偏好保存在当前浏览器与同一端口的origin，不跨设备同步，换端口可能显示默认偏好。 |
| 字体 | 本地 Hanken Grotesk 操作／正文与 Newsreader 标题字体，独立 OFL 许可 | 两个未裁剪字体共584,556字节；中文界面和邮件字形使用系统回退，并非统一中文字体设计。 |
| 动效与渲染 | 空档案打开时信封展开一次；页面导航、导入阶段和真实结果短暂过渡；720ms装饰纸张飞入和700ms实际阅读面板翻开；可选柔和／丰富光效，默认柔和；减少动态效果优先，后台停止 | 无信封重播、独立光影场景或预览按钮。不支持Web Animations API时阅读面板静态显示。丰富开场最多64粒子／4.8秒、成功反馈42粒子／1.8秒；DPR≤2且画布≤150万像素，设计绘制上限约30次／秒。未测低端设备／其他浏览器引擎，不承诺通用帧率；视觉效果仍需用户确认。 |
| 窄屏和无障碍 | 本轮320／390px无横向溢出并检查动画关键阶段，点选邮件定位到阅读区并支持返回；大字号、命令／列表键盘操作；所测axe场景无违规 | 只是窗口布局模拟，未测真实手机触控或读屏器，也不是WCAG认证；另一台手机不能连接此loopback服务。 |
| 安装与平台 | Windows 便携 EXE 捆绑 Python3.13.17／SQLite／Tk8.6.15；原生控制窗口管理服务，浏览器负责阅读；alpha.3 构建核对及新源码／EXE 冒烟通过，最终 ZIP 核对通过；历史本机原生恢复、打开档案、关闭重开和双语布局验收通过 | 未签名，未在第二台干净 Windows 验证。源码路径仍需 Python3.11+／SQLite FTS5，无pip安装或前端构建；其他系统无打包版，macOS/Linux CI已配置但未执行。 |
| 市场与商业 | 真实来源、竞品对照、聚焦个人文件归档 | 无真实用户试点、留存或付费验证；不能宣称市场成立。源码可见且非商业许可，不是允许任意商用的OSI开源软件。 |

经用户授权，真实 Proton 单封网页 EML 导出 → 导入 1 封 → 搜索 → 取回原件／附件 → 备份恢复已通过；原始 EML 字节和 10 个解码后的内嵌附件内容一致。样本暴露的旧式 HTML 预览问题修复后得到 37 行可读文本，不代表恢复原始 HTML 排版。Gmail 真实导出和 Proton 批量 CLI 尚未执行；单封样本不能证明全邮箱完整性，也不是用户试点。

本轮发现的可复现问题（窄屏图标名称、阅读定位、主题切换瞬间低对比度、逐封导入开销、明细快照与恢复校验、旧式 HTML 预览等）已修复并做对应复测。用户对风格、交互和动效效果的接受程度仍需实际体验确认。源码清洁检查不是完整密钥审计；真实符号链接案例因本机创建权限限制未能执行。

## English summary

断开邮箱的账号设置与凭据属于两个文件，无法保证跨文件原子提交。11/16内部候选先保存账号移除结果；若此步失败，账号和凭据保留。之后清理凭据失败时，账号保持断开并显示警告，密码可能仍留在本机；当前没有自动清理重试，也不提供物理安全擦除保证。

Connection settings and credentials are separate files, without a cross-file atomic transaction. The 11/16 internal candidate commits account removal first; a failure at that stage preserves the account and credentials. If later credential cleanup fails, the account remains disconnected and the UI warns that its password may remain locally. Automatic cleanup retry and physical secure erasure are not provided.

MailCairn is a personal local archive with loopback-only HTTP and optional outbound IMAP ingestion. Its UI reads INBOX initially and every five minutes while running; the backend supports one configured ASCII folder per connection, without multi-folder discovery. It does not send mail, change source flags, follow source deletions, share accounts across devices, encrypt stored mail, index attachment contents, ingest PST/OST/Maildir/ZIP or render full HTML. Exact-byte deduplication can retain logically similar messages from differing exports. Preview/search text is capped; original bytes remain intact. Ambiguous MBOX boundaries and hash verification cannot establish provider completeness or authenticity.

Gmail requires an eligible app password; OAuth is not implemented. The official Proton connector needs paid Bridge. Free Proton automation is not supported in this release; unofficial Hydroxide is a documented investigation candidate, not a tested integration or proof that free access is impossible. Real Gmail initially archived 120 messages successfully; later automatic new-message retrieval failed at TLS and remains unresolved. Paid Proton Bridge is unverified. Alpha.3 made no new private-mail/network probes and left the user’s apps and proxy unchanged. Mail removed from the selected folder before a poll can be missed; quitting stops the worker. A failed/oversized sync message stops cursor advancement before that item. Each fetched message creates a receipt, so the file-import benchmark does not establish sync throughput. Remembered credentials require working current-user Windows DPAPI; other contexts use memory only. SQLite backups exclude connection configuration, progress and credentials; reconnect after restore.

Historical measurement covered 10,000 text-only messages / 98.31 MiB. Alpha.3 also tested 1,000 multilingual messages with 250 × 64 KiB attachments, totaling 24,694,850 input bytes; all 12 query cases and integrity/fidelity checks passed. Neither workload establishes 20 GiB or attachment-heavy capacity. The decoded preview cap is not a parser-memory bound; MIME decoding still incurs workload-dependent memory and CPU costs. Batch thresholds apply at record boundaries. Restore requires a hard-link-capable destination filesystem and refuses existing targets. Request/read limits can reject overload; downloads need temporary disk space.

Direct **EN / 中文** buttons switch the interface while preserving filters, import/reading state and original mail text. Each completed import file refreshes real archive counts and the mail list. The compact review retains partial/error outcomes and reports unstarted files; its single-import action filters to that receipt, while the multi-file action opens all mail. A completed receipt is not relabeled as a failed import merely because a later display refresh fails.

The two local OFL variable fonts total 584,556 bytes, with system fallback for Chinese glyphs. Preferences belong to one browser origin. Opening an empty archive plays its envelope entrance once for the page; navigation, import stages and confirmed results receive finite transitions. Reading retains a cancellable 720ms decorative transfer and 700ms live-panel opening. There are no replay, separate scene or light-preview controls. Subtle light is the default; optional Rich opening is limited to 64 particles / 4.8s and success feedback to 42 particles / 1.8s, with a resolution scale of 2, 1.5 million backing pixels per canvas and a designed drawing cap around 30 times/second. Reduced motion and visibility changes stop effects. Without Web Animations API the reader remains static and functional; no general frame-rate or low-end-GPU guarantee is made. Simulated 320px and 390px layouts and sampled animation phases were checked; this does not establish physical-phone behavior or WCAG conformance.

One authorized real Proton web EML export passed import, search, byte-identical original recovery, ten identical decoded inline attachment payloads and backup/restore. Its legacy HTML preview defect was fixed to produce 37 readable lines. Gmail account exports and the Proton bulk CLI remain untested. A synthetic folder batch passed FileList-to-real-HTTP import of six EML files with six JSON sidecars skipped and counted; the native browser directory-picker transport was not verified. JSON metadata and provider hierarchy are not imported.

Windows/Python3.13 and one Chromium browser were exercised. The current Windows portable EXE bundles Python3.13.17 and Tk8.6.15, with a native service controller and browser reader; its [artifact and notice audit](desktop-dependencies.md) passed. Packaged mode needs no separate Python installation; the source route does. Current-machine native QA passed: selecting a backup through the Windows picker restored into a new archive, opening the archive folder reached the original vault, closing cleared service metadata, and restarting reused the port while preserving English browser language and six messages. English and Chinese controller layouts showed no clipping. These checks do not verify the browser directory-import picker. The build is unsigned and has not been checked on a second clean Windows machine. Other OS/browser engines, screen readers, physical power loss, larger mixed archives, external security review and real-user commercial/retention evidence remain unverified. The application license is source-available PolyForm Noncommercial 1.0.0, not unrestricted commercial-use open source; bundled dependencies retain their own licenses. See [test results](test-results.md), [security model](../SECURITY.md), [research](market-research.md), and [LICENSE](../LICENSE).
