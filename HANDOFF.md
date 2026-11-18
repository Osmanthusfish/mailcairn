# MailCairn 详细交接文档

更新：2026-11-18。本文面向没有当前聊天上下文的接手 Agent；事实与待验证判断分开记录。历史材料保留在 `HANDOFF.history.md`、`docs/handoff-history-20261113.md`。项目相对路径均相对本文件所在源码根目录，工作区路径不是写死在产品中的用户档案位置。

## 1. 当前状态：Alpha.9 发布前打磨、验收与打包已完成，等待用户验收与授权上传

**2026-11-18，已完成面向 GitHub 公开发布前的最后一轮体验打磨、门面精简、仓库瘦身与全流程验收打包（0.1.0-alpha.9）。未上传 GitHub，未经用户明确确认不上传。**

### 1.1 版本与入口状态

| 层级 | 当前真实状态 |
| --- | --- |
| 当前工作源码 | **0.1.0-alpha.9**，完成单键快捷键大小写兼容与 `,` 双语说明、使用指南第 04 步桌面“恢复备份…”双语说明、语言按钮 `nowrap` 防折行、IMAP 20s 超时、中英 README 首屏门面精简、CI 命令对齐、相对链接修复及清理 19 张无引用历史过程图（瘦身约 2.98 MiB）。 |
| 最新本地构建与候选包 | **Alpha.9**（构建目录 `../../defalt_folder/mailcairn-alpha9-build-20261118`，已完整复制到 `../deliverables/MailCairn-0.1.0-alpha.9`），已生成 Windows/源码 ZIP 与 `ALPHA9-ARTIFACTS.json`。 |
| 用户可打开的候选 | **Alpha.9**。`../Open-MailCairn-Candidate.cmd` 已切换指向 `../deliverables/MailCairn-0.1.0-alpha.9/MailCairn.exe`（保留用户候选档案 `../work/alpha-candidate-20261113`）。历史 Alpha.8 / Alpha.7 / Alpha.6 / Alpha.5 快照完整保留。 |
| 普通旧入口 | `../Open-MailCairn.cmd` 仍是旧 Alpha.4，不要声称它也已更新。 |

### 1.2 完成、未完成与可用性结论

- 已有真实产品：本机持久邮件档案，MBOX/EML 导入、搜索筛选、纯文本阅读、原文/附件下载、导入回执、导出、备份恢复、中英界面和可选只读 IMAP 同步。
- **Alpha.9 完整验证**：全量 Python **202** 项无跳过（51.035 秒，`-W error::RuntimeWarning`，含 SSL/Bridge 20s 超时断言）；前端/连接/双语/启动回归 **66 / 31 / 19 / 11**；源码边界检查 **163** 文件零问题、全仓 Markdown 内部链接 **0** 断链；构建审计（21 native / 10 app / 10 static / 21 desktop notices / 3 project notices / 19 license hashes）与实际 Alpha.9 EXE 八组合成 HTTP 冒烟通过（恢复使用源码 helper）；Ego 浏览器验证实际 Alpha.9 EXE 的 20 封 `sample.mbox` UI 导入、`Shift+H`/`Shift+G`/`Shift+I`/`,` 快捷键与双语说明、使用指南第 04 步桌面与 CLI 恢复双语说明，以及 320×568 窄屏下语言按钮 `nowrap` 单行 44px 不折行表现。
- **明确未验证/未解决事项**：Gmail 后续新信自动到达因 TLS EOF/重置仍未通过（首次 120 封通过，放宽 `NETWORK_TIMEOUT` 至 20s 仅提升慢链路容忍度，不绕过阻断 993 端口的路由）；付费 Proton Bridge 未实测，免费账号不支持该连接器；第二台干净 Windows 电脑、最新 build 原生窗口选择器恢复流程（仍为 Alpha.4 历史范围）、低性能实机、真实手机与读屏器输出均未验收；等待用户视觉与体验确认。
- README/README.zh-CN、ALPHA、RELEASE_NOTES、test-results、known-limits 与 `docs/alpha9-evidence.json` 已同步至 **0.1.0-alpha.9**；另已在 `../deliverables/GITHUB-RELEASE-AND-PROMO-ALPHA9.md` 准备好可直接复制的 GitHub Release 说明与社区自荐草稿。

### 1.3 任务、进程与额度快照

- 所有 Alpha.9 自有测试 `MailCairn.exe` 进程均已在核对路径后停止；未改动或关闭用户代理、私人邮件或候选档案。
- Ego 浏览器空间 8（Alpha.9）已在最后一步调用 `finish({ keep: [] })` 结束。Alpha.9 浏览器实验记录与本地截图位于 `../../defalt_folder/mailcairn-alpha9-browser-20261118/`。
- 当前运行环境中无 `codex_app.get_usage_limits` 接口（unavailable），无法读取五小时剩余百分比；若后续接手环境恢复该接口，需按 `AGENTS.md` 在启动新阶段前重读（≤10% 则停止）。

### 1.4 接手者最先需要知道的事

先读本文第2–5节了解产品、用户要求和代码约束，再读第8节核对版本/入口。当前已具备可供用户直接通过 `../Open-MailCairn-Candidate.cmd` 体验验收并随时建仓发布的 **0.1.0-alpha.9** 候选。不要问已答过的二机/免费Proton问题，不要改代理，不要读私人邮件找测试素材，未经用户确认不要上传GitHub。

## 2. 产品背景、证据和选题理由

最初需求是：用户从邮箱导出 MBOX/EML 后，希望长期保存、快速搜索、找回附件、了解导入是否完整并可靠备份，不愿维护 Docker、服务器或新账号。之后用户明确指出“每次手动导出再导入成本高”，因此新增可选的只读 IMAP 增量同步。它目前是个人本机邮件档案与阅读工具，不是完整邮箱服务或代发客户端。

研究入口和详细来源在 `docs/market-research.md`，原始研究截止/访问日为 2026-11-09。优先看近 3—6 个月原始讨论、评价及独立来源；没有把讨论热度当市场规模。代表记录：

| 日期 | 原始来源 | 能支持与不能支持的判断 |
| --- | --- | --- |
| 2026-08-27；后续 2026-09-20 | https://www.reddit.com/r/GMail/comments/1vzwbqc/looking_for_a_way_to_automatically_archive_all_my/ | 有独立自动归档需求；作者后来确认 OpenArchiver 已解决需求，是必须保留的反证，不能声称没有有效竞品。 |
| 2026-10-14 | https://www.reddit.com/r/Thunderbird/comments/1x5gcxd/how_do_you_usually_open_and_search_large_mbox/ | 大 MBOX 打开/检索场景；单帖证据权重低，并有推广可能，不能直接推算市场。 |
| 2026-11-01 | https://www.reddit.com/r/GMail/comments/1xl6zwm/gmail_nearly_full_of_old_mail_what_do_you/ | 邮箱容量与旧邮件处理困扰；不直接证明用户会购买独立档案应用。 |

有效竞品包括 OpenArchiver、MailStore Home、Thunderbird 与导入工具、Windows MBox Viewer、浏览器 MBOX 阅读器。原始研究也记录了通过已有工具解决问题的 Mozilla 支持案例。不存在“没搜到所以没有竞品”的结论；未做可重复的竞品性能横评。

选题推断：无账号的本机持久档案、清晰回执、原文字节保留、检索与恢复，可形成较低设置门槛的体验差异。需求存在有中等定性证据；市场未满足程度、付费意愿和长期留存仍属低置信假设。尚无外部用户试点、真实付费、获客转化或价格验证。可能获客方式是实用导出/归档指南和 GitHub；尚未发布或对外联系用户。未来可考虑个人付费打包/支持及单独商业许可；一次性工具价值可能强于订阅，仍未验证。不要因为已投入开发就放大商业结论。

## 3. 当前产品形态与用户流程

### 3.1 形态和启动

当前主形态是 **Windows 便携桌面控制窗口 + 本机浏览器界面**。控制窗口管理服务、档案与备份，浏览器负责邮件阅读、搜索、导入和连接。源码服务可在 Python 3.11+、SQLite FTS5 环境运行；Windows 包自带 Python 3.13.17/Tk 8.6.15。运行不依赖 pip、Node、Docker 或 AI 服务。没有手机客户端、跨设备同步或云端托管版本。

启动时取得当前档案的系统锁，在 127.0.0.1 绑定本机服务，再打开浏览器。短期令牌交换为 HttpOnly 会话 cookie，移除 URL fragment；不得打印令牌或复制 instance 文件进发布包。浏览器标签关闭不代表桌面控制窗口/同步已停止。重复启动同一档案会尝试复用已运行实例；如果旧候选仍在运行，可能继续打开旧界面，应让用户正常退出控制窗口后重开，不能擅自杀进程。

默认档案目录来自当前运行用户/系统目录，可选择其他档案；不是开发者用户名硬编码。源码与发布包中不能放开发机档案、凭据、会话文件或包含私人路径的截图。

### 3.2 文件导入、查看和导出

1. 用户选择已经解压的 MBOX、EML 或邮件文件夹；文件夹可递归识别邮件并报告跳过项。不直接支持 PST/OST/Maildir/ZIP/TGZ 或 mboxcl。
2. 流式上传临时文件并计算哈希，解析 MIME，生成安全纯文本及附件元数据；原文写入 SQLite，建立 FTS 索引，批次提交邮件与回执。
3. 刷新邮件数量、搜索列表、导入历史和结果回执；失败、部分成功、未开始不伪装成全部成功。相同原文字节去重；不是语义或 Message-ID 去重。
4. 用户按正文/主题/地址/附件名检索，并组合发件人、日期、附件和导入筛选；50 条分页。打开纯文本邮件、下载原 EML 与附件、导出筛选后的 MBOX 或 JSON 回执。
5. 后台导入完成不能打断正在读的旧邮件，即使旧行被挤出当前页；焦点、阅读状态和滚动应保持。浏览导入记录时立即进入档案和搜索框；迟到响应不得抢走用户随后移动的焦点。

MBOX 导出在副本中去掉顶层 Content-Length 及其折行，再做 From 行转义，以避免自己的 mboxcl 拒绝规则阻止重导。数据库原文与单封 EML 下载保持原字节；正文中的 Content-Length 和 MIME 部件头不删除。格式转换会改变字节哈希，因此同一逻辑邮件重导可能新增记录；中英 README 已说明。没有邮件真实性、来源完整性或司法取证承诺。

### 3.3 邮箱连接与自动同步

邮箱连接以非技术用户为目标，常见服务尽量预设；专业服务器/端口/TLS 参数放高级设置和使用指南。只读 IMAP INBOX，首次导入已有邮件，应用运行时约每五分钟同步；可立即同步、暂停、恢复或断开。不能发信，不修改远端已读/删除状态，不做多文件夹自动发现或云端清理。

Gmail 目前用符合 Google 条件的应用专用密码，**不是 Gmail 常规登录密码**，尚未实现 OAuth。Proton 第三方 IMAP 依赖付费 Mail Bridge 及其本机凭据；免费 Proton 网页登录不能替代 Bridge。用户测试 Proton 是免费账号且没有 Bridge，不要再次承诺可直接自动同步。

Windows 凭据采用当前用户 DPAPI；无法安全持久化时保留内存并提示限制。备份不包含连接凭据和同步配置，恢复后需要重新连接。邮件数据库和备份本身不加密，DPAPI 也不防同一 Windows 用户下的恶意程序。

### 3.4 备份、恢复、双语与偏好

通过 SQLite 一致性快照备份；恢复先校验，写入新的空目录，拒绝覆盖已有档案，再从控制窗口打开恢复档案。不要只复制活跃 SQLite 主文件而忽略事务状态。

界面支持 English/简体中文，不翻译邮件、私人文件名或原始内容。主题、强调色、字号、密度、快捷键、动效与 quiet/full 光效由用户选择；展示偏好保存在浏览器本机 origin，不随邮件备份转移，端口改变可能影响偏好读取。

## 4. 用户明确提出的体验标准和约束

- 用户反感模板式字体、堆砌小字说明、普通焦点彩色边框和生硬直角按钮；希望圆润、精致且有创意的真实任务交互。键盘可见焦点仍需保留，不能以“去 AI 味”为由删除可访问性。
- 纸张模型可以有创意，但松开悬停时不得穿模，文字不能超出合理纸面；导入、列表、开信、筛选和按钮都需要完善，不能只有首页装饰好看。
- 去掉无实际任务价值的“展开书信”“点亮书房”等独立演示按钮，开场随进入自然出现；动效应服务真实动作，并尊重减少动效/隐藏页面/节能边界。
- 每个阶段主动用中文解释做了什么、证据是什么、还差什么；持续工作时不让用户超过约一分钟不清楚进度。无需写心得。README 中英双语。
- 浏览器操作只用 **ego-browser skill/CLI**，不直接用 Computer Use。原生桌面交互证据与浏览器证据必须分开。
- 不断开、切换或重配用户的代理/VPN，不关闭其他后台网络客户端，不改全局网络规则。用户还在运行其他任务；不能杀不明进程。另一套组织 VPN 客户端仅安装未连接这一澄清优先于早期口述。
- 不索取聊天中的密码，不打印应用密码、邮件内容、会话令牌、订阅配置或账号额度重置标识。只能操作明确授权测试邮箱及合成档案；现阶段无必要继续读私人邮件。
- 用户已说明暂时没有第二台 Windows 电脑，继续本机检查，不重复追问。若真正需要新增外部条件，明确说明缺什么、哪些已验证。
- 可并行研究/开发，用户要求子 Agent 使用 gpt-6-astra 高标准；启动前核对额度和现有 Agent 状态，避免重复任务、并发改同文件或把失败的复查说成已完成。

## 5. 核心源码地图与不可破坏的逻辑

| 文件 | 职责与关键约束 |
| --- | --- |
| `app.py` | CLI、档案锁、恢复中断作业、临时文件清理、服务启动。 |
| `desktop.py` | 桌面控制、原生档案/备份选择器、单实例与端口回退；仅对 WinError 10013/10048/EADDRINUSE 等预期绑定冲突回退，不能吞掉任意错误或修改 OS 网络。 |
| `mailcairn/server.py` | 仅回环服务、会话/Host/Origin 校验、安全响应头、导入作业与下载；16 个工作线程、4 个原文重读槽位。不能开放到公网或把令牌写日志。 |
| `mailcairn/store.py` | SQLite schema 1、application_id 0x4D434152；原文字节/哈希、FTS、imports/import_items、检索、导出、备份恢复。批次阈值 100 封/4MiB/0.25 秒，在记录边界提交，FULL；进度只承诺已提交数据。正常取消保留已处理，强制终止回滚未提交批次，重导靠去重，不是按字节偏移续传。 |
| `mailcairn/parse.py` | mboxo/mboxrd 信封识别、输入 mboxcl 拒绝、MIME 深度 30/部件 500 上限、安全纯文本提取。原件不应因显示而重写。 |
| `mailcairn/sync.py` | 只读 INBOX 五分钟轮询、UIDVALIDITY/UID 持久化；邮件提交成功再推进游标，游标写入失败允许安全重放，不完整非空 FETCH 保留重试。 |
| `mailcairn/imap_client.py` | 有界读取、TLS 校验/Bridge 证书固定等连接逻辑，不可为通过测试关闭验证。 |
| `mailcairn/credentials.py` | 当前用户 DPAPI/内存回退；RLock 事务快照旧加密表示和内存值，不为回滚解密旧凭据；设置写失败恢复。 |
| `mailcairn/static/app.js` | 搜索/分页/读信/作业/连接状态；最多两条并发读请求，排队只保留最新；序号和页面版本阻止迟到响应接管新操作。 |
| `mailcairn/static/style.css`、`mailcairn/static/i18n.js` | 纸面阅读、有限动效、EN/中文与展示偏好。不要增加无任务意义的循环光效或远程字体。 |
| `mailcairn/static/startup.js` | 不依赖业务脚本/i18n的独立IIFE，head同步加载；处理早期资源/语法/顶层错误，DOM未到则记录pending；12秒慢启提示，确定失败清timer；ready清监听/临时禁用，仅隐藏区含焦点时交main。自身脚本加载失败不保证恢复。 |
| `scripts/` | 前端状态回归、双语检查、源码边界扫描、Windows 构建/核对/打包/冒烟；扫描不是安全认证。 |

补充不变量：

- `search` 成功才提交 offset；失败参数单独保留供重试，保留旧列表、滚动与读信。errorOwner 只清自己的错误；后台刷新不反复播放全部旧行的入场动画。
- connectionCards 按账号 ID/签名复用节点，忙碌时更新状态/按钮，保留操作焦点；独立 announcement 仅播真正状态变化。尚未真实读屏器验收。
- 凭据事务回滚文件失败时不能假装已恢复：已有账号通过当前会话 `_credential_errors` 阻止同步并要求明确重连；新账号提示可能残留加密凭据。断开先持久化移除设置，再清凭据，清理失败仍保持断开并提示。没有跨文件崩溃原子性、持久化重连锁或自动孤立凭据清理。
- 普通文本预览不重读完整 MIME，旧 HTML 兼容分支仍可能加载原件。预览/索引 100 万字符上限在解码之后，不是内存硬上限；附件内容不检索。完整性哈希用 blobopen 每 256KiB 分块。
- 光效 quiet/full 默认柔和，丰富开场最多 64 粒子/4.8 秒，成功最多 42/1.8 秒，DPR≤2、backing pixels≤150 万、约 30 次绘制/秒；隐藏、离开视口、关闭动效或 OS 减少动效都应停止。阅读装饰约 720ms、实际入场约 700ms；真正类名 `.message-flight`，不能等待不存在的 `.paper-flight` 就宣称截图稳定。

## 6. 最近完成的工作：Alpha.5

1. 修复后台文件导入/恢复作业完成后搜索刷新把用户正在读的旧信切换为新信：`startImport` 每文件和 finally、`resumeJob` 均保留 selection。旧行离开 50 条当前页时仍保留正文/滚动；键盘焦点交到可编程聚焦的 reader，而不是丢到页面根部。
2. 从历史/回执浏览邮件时先切档案、启动已有入场并聚焦搜索，再等待搜索响应；异步结果不会抢走用户随后转移的焦点。
3. 修复含顶层 Content-Length 的 EML 导出为 MBOX 后被自身 mboxcl 输入拒绝的问题：仅修改导出副本，覆盖 LF/CRLF、重复/大小写混合头、折行、正文同名文字、后续正常头、附件及原件完整性。
4. 前端 DOM 测试增加桌面/窄屏后台读信保持与延迟响应焦点。首轮测试漏 await 初始搜索已修；后续测试 shim 错把已脱离 document 的节点当作有效节点，大对象断言又造成 OOM 表象，已修正查询语义与布尔断言。后续回归通过，不应把这段测试问题描述为产品内存泄漏。
5. 统一源码/HTML 侧栏版本 Alpha.5；中英 README、ALPHA.md、RELEASE_NOTES.md 更新新版说明并明确历史 Alpha.4；Windows 新候选和清单已生成，源码包最后更新后重包。
6. 已构建新的实际 Windows EXE、核对打包模块、执行实际服务合成冒烟、真实 Ego 浏览器导入/导出/重导及焦点测试。独立 Astra 后端复查确认 MBOX 最小修复，无新确认缺陷；前端第二次独立复查因额度失败，不得记为已完成。

此前重要修复也已包含：初始连接发现失败按 8 秒恢复、区分未知状态和已知空账号；页面隐藏暂停/可见恢复；分页失败保留旧页并可重试；邮箱卡片复用；凭据/配置失败回滚与双语警告；桌面绑定权限/端口回退；真实 Tk 测试资源清理防跨线程析构警告。不要重复应用旧补丁。

## Alpha.6节点（2026-11-16/17，最新已打包候选）

- 新增独立启动恢复层并把三个早期绑定放入try。中文/英文按已有保存项优先、存储不可用按浏览器语言；正常启动默认隐藏，不增加常驻解释文字。错误使用固定文案，不把原异常/令牌写DOM；重试仅location.reload，session交换前不清片段。bootstrap本身下载失败无法靠同一脚本自救；noscript仅覆盖JS关闭。
- 独立Astra确认第一版确定失败会被12秒timer改成慢启文案；已修正并加回归。另把bootstrap改为head同步安装错误监听，DOM尚未到时保存pending。ready/handled后移除timer/listener，恢复原禁用值；仅当焦点还在隐藏面板内时交main，避免抢焦点。
- 完整Python202项无跳过/RuntimeWarning错误，38.168秒，在startup改动后/版本元数据升号前；HTTP定向22项通过。Node前端61、连接31、双语16、新startup11通过。新检查已接CI/README；CI未在远端实际执行。
- 源码Ego注入缺失app/i18n、语法/顶层/绑定失败都显示恢复，Enter重载成功；12秒慢启后释放响应，按钮/焦点恢复。首轮注入在取消header timer前阻塞，10秒由测试服务断开，已修fixture并在同空间通过；不能算产品慢启失败。
- Alpha.6实际构建审计通过21native/10app/10static/21桌面声明/3项目声明/19许可哈希；EXE SHA256 `59ce87b4b7fe458ab14327e52817f23a391f2427b3187aeba745effbe2e3f332`。实际EXE八组合成HTTP通过；恢复仍是source helper，不是原生窗口。本版正常启动与Ego仅对自己的Page临时CDP阻止app.js→立即恢复提示→清除阻止→Enter重载2封邮件、导入按钮恢复、session清理均通过，没有系统代理修改。
- 原始报告/脚本/截图在 `../../defalt_folder/mailcairn-startup-20261116/`（fault-cases.json、slow-recovery.json、actual-exe-recovery.json）；EXE冒烟 `../../defalt_folder/mailcairn-alpha6-smoke-report-20261116.json`。公开脱敏证据 `docs/alpha6-evidence.json`；恢复截图像素已查看并入docs/screenshots。Ego空间7结束、exec1394退出、路径核对自有EXE34588已停，无需恢复运行任务。
- 原首导航原因仍未知。源码21次静态读取完整；16个request_slots饱和会关闭新请求，但无当时饱和证据。此版本解决失败恢复缺口，不声称定位该偶发或解决Gmail TLS。

## Alpha.9节点（2026-11-18，公开发布前体验打磨、门面整理、瘦身与打包）

已改内容：

1. `mailcairn/static/app.js`、`index.html`、`i18n.js`：单键快捷键匹配大小写字母键（`I`/`G`/`H` 在 Caps Lock 下同样生效），并在阅读设置弹窗补齐 `,`（打开阅读设置）的中英说明；使用指南第 04 步补充桌面控制窗口“恢复备份… / Restore backup…”操作说明（保留源码 CLI 命令）。
2. `mailcairn/static/style.css`：`.language-option` 增加 `white-space: nowrap` 防止高缩放或窄弹窗下折行。
3. `mailcairn/imap_client.py` 与 `tests/test_sync.py`：`NETWORK_TIMEOUT` 从 10s 放宽至 20s 并补充 SSL/Bridge 单元测试断言。
4. `README.md`、`README.zh-CN.md`、`docs/handoff-history-20261113.md` 与 `docs/screenshots/`：将 `HANDOFF.md` 链接移至文末开发章节，精简首屏内部候选流水账，补齐开发检查命令与 CI 对齐，修复两处历史相对链接，清理 `docs/screenshots/` 中 19 张完全无引用的早期过程图（减少约 2.98 MiB，源码包文件数由 181 精简至 163）。

完整验收结果：

- 自动化与审计：全量 Python **202** 项无跳过（51.035s，`-W error::RuntimeWarning`）；前端 **66** / 连接 **31** / 双语 **19** / 启动 **11** 通过；源码边界扫描 163 文件零问题、全仓 Markdown 链接 0 断链；Windows 构建审计通过；实际 Alpha.9 EXE 8 组合成 HTTP 冒烟通过（`../../defalt_folder/mailcairn-alpha9-smoke-report-20261118.json`）。
- Ego 真实浏览器（实际 Alpha.9 EXE）：20 封 `sample.mbox` 导入、`Shift+H`/`Shift+G`/`Shift+I`/`,` 快捷键及双语提示、指南第 04 步双语桌面+CLI 恢复说明、320×568 下语言按钮 `nowrap` 单行 44px 不折行均通过，已查看本地截图、恢复原浏览器偏好键并结束空间 8 与测试 EXE。
- 已生成 `docs/alpha9-evidence.json`、打包 `../deliverables/MailCairn-0.1.0-alpha.9`、Windows/源码 ZIP 与 `ALPHA9-ARTIFACTS.json`，切换 `../Open-MailCairn-Candidate.cmd` 指向 Alpha.9，并在 `../deliverables/GITHUB-RELEASE-AND-PROMO-ALPHA9.md` 整理好 GitHub Release 与社区自荐文案。

## Alpha.8节点（2026-11-17，已完成真实流程完善、验收、文档与本地打包）

背景：在真实阅读、回执查看与设置弹窗流程中发现四处交互可靠性可完善点：读信或加载回执因瞬时繁忙/网络失败时缺乏就地重试按钮、打开阅读设置始终把焦点落回 `system` 而非当前保存的主题、弹窗焦点循环未显式处理 `<summary>` 与折叠 `<details>` 边界。

已改源码：

1. `mailcairn/static/app.js`：`renderReaderPlaceholder(message, retry)` 与 `readMessage(id, navigate)` 增加失败就地重试按钮（`.retry-reader`）；按重试后临时把焦点停在 `#reader`（或窄屏保留 `.reader-back`），再次失败保留聚焦新 `.retry-reader`，成功则交回 `#reader`，且用户移走焦点时不抢回。
2. `mailcairn/static/app.js`：`showReceipt(id)` 增加失败就地重试按钮（`.retry-receipt`），加载中暂留焦点于 `#receipt-content`（`tabIndex=-1`），成功聚焦 `.receipt-actions` 首项、再失败回聚焦 `.retry-receipt`，不抢用户移走后的焦点。
3. `mailcairn/static/app.js`：`openPreferences()` 在 `showModal()` 后聚焦当前保存主题单选框；`keepDialogFocus(event)` 纳入 `summary`、过滤闭合 `<details>` 内部控件并支持焦点在 `<dialog>` 根元素时的 Tab / Shift+Tab 边界循环。
4. `mailcairn/static/style.css`：为 `.retry-reader` / `.retry-receipt` 增加 `margin-top: 12px` 与 `#receipt-content:focus { outline: none }`；`mailcairn/__init__.py` 与 `index.html` 升至 `0.1.0-alpha.8`。
5. `scripts/check_frontend.mjs` 与 `scripts/check_i18n.mjs` 新增 3 项前端与 1 项双语回归测试（65 / 18 通过）。

完整验收结果：

- 自动化与审计：全量 Python **202** 项无跳过（27.828s，`-W error::RuntimeWarning`）；前端 **65** / 连接 **31** / 双语 **18** / 启动 **11** 通过；源码发布边界扫描 181 文件通过；Windows 构建审计 21 native / 10 app / 10 static / 21 桌面声明 / 3 项目声明 / 19 许可哈希通过；实际 Alpha.8 EXE 8 组合成 HTTP 冒烟通过（`../../defalt_folder/mailcairn-alpha8-smoke-report-20261117.json`）。
- Ego 真实浏览器（针对实际 Alpha.8 EXE 与 `../../defalt_folder/mailcairn-alpha8-browser-20261117/archive` 隔离档案）：
  - 通过 UI 导入 `tests/fixtures/sample.mbox`（20 封）；验证打开阅读设置自动聚焦已保存 `dark` 主题；验证连接弹窗其他邮箱下 `<details>` 折叠/展开与 Tab 循环；CDP 单页拦截 `/api/messages/*` 与 `/api/imports/1` 触发双语 `.retry-reader` / `.retry-receipt`，解除拦截后按 `Enter` 恢复正文（`#reader` 保持焦点）与回执（`.receipt-actions` 获得焦点）；恢复两个偏好键、查看 `alpha8-reader-retry-zh.png` 像素并结束空间 4 与测试 EXE。
- 文档与打包：已生成 `docs/alpha8-evidence.json` 与 `docs/screenshots/alpha8-reader-retry-zh.png`，更新中英 README、`ALPHA.md`、`RELEASE_NOTES.md`、`docs/test-results.md`、`docs/known-limits.md`；已打包 `../deliverables/MailCairn-0.1.0-alpha.8`、Windows/源码 ZIP 与 `ALPHA8-ARTIFACTS.json`，并切换 `../Open-MailCairn-Candidate.cmd` 指向 Alpha.8。

## Alpha.7节点（2026-11-17，已完成全流程验收、文档与本地打包）

背景：实际Alpha.6在800×600设置面板下，大字号20px、深色、紧凑、丰富效果和偏好保存通过；320×568中从最后的“重置”按Tab会进入浏览器工具栏。通过Ego读取[W3C APG modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)（访问2026-11-17）确认首末焦点应在弹窗内循环；这是交互差距，不是已确认安全漏洞，也不代表已获无障碍认证。

已改源码：

1. `mailcairn/static/app.js` 新增 `keepDialogFocus(event)`，在已有dialog绑定循环中监听keydown。只处理不带Ctrl/Meta/Alt的Tab；收集button、链接、input、select、textarea、tabindex节点，过滤负tabindex、`:disabled`、hidden/inert祖先、无可见矩形和CSS visibility:hidden。末项Tab到首项、首项Shift+Tab到末项；内部移动和系统快捷键仍交浏览器。现有弹窗没有需另外处理的正tabindex排序；未来增加时须重新评估。
2. `index.html` 给归档摘要后缀加 `#summary-label`；`app.js` 按原始数量区分 message/messages、attachment/attachments及附件aria-label、duplicate/duplicates、record/records、file needs/files need、file was/files were。`i18n.js` 对单复数完整匹配并保留中文，不翻译邮件正文。
3. `scripts/check_frontend.mjs` 增加边界/隐藏禁用/inert/负tabindex/不可见/修饰键/关闭弹窗回归；仅在测试上下文补getComputedStyle模拟。`check_i18n.mjs` 增加0/1/2与EN→中文→EN验证，含可访问名称及原文不被改写。旧测试中错误的“1 files were”预期已修正。
4. `mailcairn/__init__.py` 与HTML侧栏升到0.1.0-alpha.7。没有新增运行依赖、没有Python业务逻辑改动。

完整验收结果（2026-11-17 恢复后执行）：

- 自动化与审计：全量 Python **202** 项无跳过通过（26.656s，`-W error::RuntimeWarning`）；前端 **62** / 连接 **31** / 双语 **17** / 启动 **11** 通过；源码发布边界扫描 179 文件通过；Windows 构建审计 21 native / 10 app / 10 static / 21 桌面声明 / 3 项目声明 / 19 许可哈希通过；实际 Alpha.7 EXE 8 组合成 HTTP 冒烟通过（`../../defalt_folder/mailcairn-alpha7-smoke-report-20261117.json`，恢复使用源码 helper）。
- Ego 真实浏览器（针对实际 Alpha.7 EXE 与 `../../defalt_folder/mailcairn-preferences-20261117/archive` 20封公开合成档案）：
  - `round7.mjs`（320×568 窄屏）：`reset-preferences` 按 `Tab` 焦点落入 `#preferences-dialog` 内 `[data-language="en"]`（`document.hasFocus()=true`），`Shift+Tab` 回到 `reset-preferences`；Escape 关闭并点击第一封信，先等待 `.reader-body`，再等待 `.message-flight` 消失、有限动画完成且 `#reader` `transform === 'none'`，测得 `.reader-body` 字号 `20px`、`docWidth` 305 <= 320、正文 `LANTERN-421` 完整保留；保存 `narrow-keyboard.json` 与 `reader-dark-320.png` 并查看像素（已脱敏合入 `docs/screenshots/alpha7-reader-dark-320.png`）。
  - `round8.mjs`（800×600）：刷新后保持 `dark`/`large`/`compact`/`full` 偏好，EN↔中文切换保持摘要单复数和原文不变；关闭 Motion 后打开第二封信零 `.message-flight` 与零运行中有限动画；按 `original-preferences.json` 精确恢复两个浏览器偏好键（`restoredMatchesOriginal: true`）。
  - 已通过 `round9-finish.mjs` 结束空间 3 并停止测试 EXE。
- 文档与打包：已更新 `docs/alpha7-evidence.json`、中英 README、`ALPHA.md`、`RELEASE_NOTES.md`、`docs/test-results.md`、`docs/known-limits.md`；已打包 `../deliverables/MailCairn-0.1.0-alpha.7`、`MailCairn-0.1.0-alpha.7-windows-x64.zip`、`MailCairn-0.1.0-alpha.7-source.zip` 与 `ALPHA7-ARTIFACTS.json`，并切换 `../Open-MailCairn-Candidate.cmd` 指向 Alpha.7。保留 Alpha.6 与 Alpha.5 历史快照。

## 7. 测试证据与它们的实际覆盖范围

### 7.1 Alpha.5 已执行

- 全量 Python：**201 项通过，0 跳过，25.768 秒**，RuntimeWarning 作为错误。Store/parse 定向 55 项通过。
- Node 回归：前端 **61**、连接 **31**、双语 **16** 项通过。前端使用 `--max-old-space-size=256`；修正 shim 后通过。
- Windows 构建核对：21 原生组件、10 应用模块、9 静态资源、21 桌面声明、3 项目声明、19 许可哈希，源码和静态资源与当前构建一致。
- **实际 Alpha.5 EXE 的 8 组合成 HTTP 流程通过**；报告 `../../defalt_folder/mailcairn-alpha5-smoke-20261116.json`。其中恢复使用源码辅助服务，不是本次 EXE 原生选择器验收。
- Ego 真实浏览器：在桌面中筛选满 50 条旧记录后导入，新行进入且旧行被挤出页，原正文保持、滚动 180→180、焦点交 reader；窄屏 390px/文档 375px 保留正文、读信状态和返回按钮焦点。窄屏模拟不等于物理手机。
- 历史及回执用键盘 Enter 浏览：立刻聚焦 search-input；刻意延迟搜索并将焦点移动到 filter-toggle，响应后仍保持该焦点。
- 实际 UI 导入 3 封 EML、筛选导出 MBOX、下载并重新导入：3 条记录中新增 1/去重 2；顶层 Content-Length 被移除、正文同名文字保留。下载原 EML 与输入逐字节相等，SHA256 `b31a879dac38df39f02da774abad371c997b4b1da2d770bcd0bd511ee7821f0a`。
- 隔离档案最终 58 封合成邮件，原文哈希、SQLite、FTS 和回执核对通过。证据目录 `../../defalt_folder/mailcairn-interaction-20261116b/`，包括 `before-fix.json`、`after-fix-desktop.json`、`after-fix-narrow.json`、`history-focus.json`、`receipt-focus.json`、`export-roundtrip.json`。
- 此前截图部分处于读信入场中途：等待误用了不存在的 `.paper-flight`，仅作本地 QA。后续已用实际 EXE 在新合成档案通过界面导入公开 sample.mbox 的 20 封，等 `.message-flight` 消失、有限动画结束且 reader transform 为 none 后采集中英桌面/390px截图，像素已查看，见 `docs/screenshots/alpha5-*` 和同目录 README。窄屏从列表开信定位 reader 顶部，文档375px无横向溢出；不代表实机手机/用户认可。
- 后续原始截图/测量在 `../../defalt_folder/mailcairn-alpha5-visual-20261116/`（stable-desktop.json、stable-narrow.json、narrow-open-position.json、reopen-check.json）。首个导航曾停留静态 opening，app.js 未初始化；同页 reload 后恢复，原因未确认。随后两次正常启动链接均显示20封、完成初始化且清除session片段。不能用成功复查解释未知原因或归咎代理。Ego空间6已finish，仅停止核对路径的自有EXE43936。

浏览器实验用合成邮件和有界响应门控，给完成导入前保留阅读时间。首轮门控只释放一次导致后续 poll 继续等待，已在同一空间修正；窄屏操作曾误点隐藏行，改用可见返回按钮。一次 reload 卡住后只取消自有 CLI 并在同一页面用已文档化导航恢复。TaskSpace 5 已 finish，无待恢复页面；不能通过新建空间绕过页面错误。

### 7.2 旧构建或其他范围证据，不能冒充 Alpha.5 全覆盖

- 11/16 Alpha.4 实际 EXE 原生 Windows 验收：备份文件/目标目录选择器→恢复新目录就绪→打开原空档案→重新打开恢复档案→取消恢复→界面退出。只读核对原档案 0 封，备份/恢复各 1 封，SQLite/哈希/FTS 通过。隔离目录 `../work/native-check-20261116`。**Alpha.5 尚未重复完整原生选择器流程。**
- 4 项自动 Tk 测试使用真实控件/后台线程，但替代文件选择器和浏览器启动，覆盖成功、取消、坏备份、忙碌；不能与上项混为一谈。
- 真实自有子进程强制终止实验：250 封唯一合成邮件，生产批次阈值不变；parse 第 125 封门控，导入连接见 124 封但外部只见 100；终止自有子进程后保留 100/回滚 24。中断回执恢复后重导新增 150/去重 100，250 原文哈希和唯一词查询、SQLite/FTS/回执通过。`docs/crash-recovery-20261116-evidence.json`，原始实验 `../../defalt_folder/mailcairn-crash-check-20261116/`。不是实际 EXE 终止、物理断电或凭据跨文件原子性实验。
- 经授权真实 Proton 单封网页导出 EML→导入/检索/原文与 10 个内联附件字节/备份恢复通过；HTML 转成约 37 行可读文本。不是完整原始 HTML、全邮箱批量导出或 Bridge 实测。
- Gmail 首次真实同步导入 120 封通过。用户发送测试信后云端 121 封，但后续 TLS EOF/连接重置，应用仍 120 且保留旧 UID。**新信自动到达尚未通过**，详见 `docs/gmail-live-evidence.json`。代理始终运行、未切换；不能擅自断定密码或 VPN 是根因，更不能通过改全局代理“修好”。
- 历史合成规模测试含 1 万封文本/约 98MiB，另有千封多语言与 250 个 64KiB 附件（输入 24,694,850 字节、2.698 秒/12 查询通过）。不是 20GiB、总 RSS 保证或所有 HTML 性能证明。

## 8. 源码、构建、启动入口和发布包的精确状态

| 项目 | 当前状态 |
| --- | --- |
| 源码 | 当前项目根；`mailcairn/__init__.py` 与HTML侧栏 **0.1.0-alpha.9**。之前检查无 `.git`，不要假设已有远端/分支；源码有data等本机目录，发布须走排除/扫描，不能整目录上传。 |
| 最新已打包候选 EXE（Alpha.9） | `../../defalt_folder/mailcairn-alpha9-build-20261118-v2/dist/MailCairn/MailCairn.exe`，2,269,311字节，SHA256 `54181677c6dd415191c7f7bb46737d33cf17ec574094eff81c9775bc08188a35`；完整onedir目录已复制到 `../deliverables/MailCairn-0.1.0-alpha.9`，不能只复制EXE。 |
| 候选入口 | `../Open-MailCairn-Candidate.cmd` 现指 `../deliverables/MailCairn-0.1.0-alpha.9/MailCairn.exe`。档案沿用 `../work/alpha-candidate-20261113`，不可覆盖或删除用户测试数据。普通入口 `../Open-MailCairn.cmd` 仍旧版。 |
| Alpha.9 Windows ZIP | `../deliverables/MailCairn-0.1.0-alpha.9-windows-x64.zip`，984文件、13,063,389字节，SHA256 `988e0bcbeceeffd9aa6af6ee107e7c2b42edd8a8d8997ae1e3b65268ea83e8c1`；已包含 `LocalServer.server_bind` 免反向 DNS 阻塞修复与公开联系邮箱 `yuyuio123@protonmail.com`，重跑 `audit_bundle.py --write-evidence` 与实际 EXE 8 组 HTTP 冒烟通过。 |
| Alpha.9 源码/清单 | `../deliverables/MailCairn-0.1.0-alpha.9-source.zip`（163文件，具体字节/SHA256见外部 `ALPHA9-ARTIFACTS.json` 与 `.sha256`）。 |
| Alpha.8 历史候选 | `../deliverables/MailCairn-0.1.0-alpha.8`（EXE SHA256 `9a11ab42700477f9d0f30481988b2802ec40a345fea2865ca3d64ceca7b8efba`）、Windows ZIP（984文件、13,062,102字节、SHA256 `73ae27f841feb17f4ccf3fe459976e68ebcf8416fc45923ef752e40035d6bcaf`）、源码 ZIP（181文件、6,158,450字节、SHA256 `ff891312c875567a10a326f5673b3aaa3955c56cf236f775387a2762ee1b3acc`）及 `ALPHA8-ARTIFACTS.json` 保留历史快照。 |
| Alpha.7 历史候选 | `../deliverables/MailCairn-0.1.0-alpha.7`（EXE SHA256 `7c574d2e0cf16e87880ec90ec4184b49f0fc936c2829da786d55b9e9298c3ac3`）、Windows ZIP（984文件、13,063,111字节、SHA256 `d4821225bbeb22a5eb2579304fcc10a471d40d31a9e693a6b68cd399a743c014`）、源码 ZIP（179文件、6,056,599字节、SHA256 `997425f631f135c54a4856d81726730fd20073494e28c50a53a5b4009dc2f533`）及 `ALPHA7-ARTIFACTS.json` 保留历史快照。 |
| Alpha.6 历史候选 | `../deliverables/MailCairn-0.1.0-alpha.6`、Windows ZIP（SHA256 `89176417896c5f9690930cc326bf289e7211eb58d7b01fbbd442aea3c0b6ec33`）、源码 ZIP（177文件、6,019,868字节、SHA256 `45caafe046380d93b738e212d1f1e68f026d73d09486ad83f28ea8df62553e41`）及 `ALPHA6-ARTIFACTS.json` 保留历史快照。 |
| 旧 11/16 EXE | SHA256 `88791ba28fce389f4b4f1cc4364108b07ef86da725516d97eaf6ace16f05978d`，有旧构建原生验收。普通入口也未切换。 |
| 旧源码 ZIP | `../deliverables/MailCairn-source-candidate-20261116.zip`，167 文件，5,389,393 字节，SHA256 `2e1e0dc6d303ca51080d6dd07e3c74fb89cf2562bc7653a3df6aa3b7008bd926`。**不含后续 Alpha.5 源码及本文**。 |
| 旧 Windows ZIP | `../deliverables/MailCairn-windows-candidate-20261116.zip`，984 文件，13,061,697 字节，SHA256 `e7754c2e67980375d9c535d7884e01ee5d0f00705152e59c3679241032e9b534`。已做 CRC/逐成员字节比对，仍属旧版本。 |
| 旧清单 | `../deliverables/CANDIDATE-20261116-ARTIFACTS.json`，只描述上述旧包。 |
| Alpha.5 Windows 包 | `../deliverables/MailCairn-0.1.0-alpha.5-windows-x64.zip`，983文件，13,060,517字节，SHA256 `87d7a893dab73214228e16f47ef8768e3cb9454400c054da876faaf7a9ffec23`；CRC/全部成员字节与审计构建一致，有限文件名及用户名/工作区字节扫描通过。 |
| 历史Alpha.5 源码/清单 | `../deliverables/MailCairn-0.1.0-alpha.5-source.zip`，173文件、5,958,341字节、SHA256 `d1ed4725bc9a10666495f45463c101c9f098fd47c1dcd0bb08659e2e5c663172`；对应ALPHA5-ARTIFACTS.json，不含Alpha.6，保留快照不重包。 |
| 公开证据文档 | 新增 `docs/alpha9-evidence.json`，test-results/known-limits/中英README/ALPHA/RELEASE_NOTES 已更新至 Alpha.9，保留 21 张有效引用截图。 |

先前包含 Alpha.5 证据/文档/打包安排的大补丁被自动审批以工作区额度原因拒绝，没有执行；**本轮已逐项正常写入/核对**，不能把旧拒绝当作现在仍未完成。详细交接写入曾因普通 shell 对项目目录无写权限失败，后经正常 require_escalated 审批写入成功；没有绕过沙箱。

## 9. 运行环境和复现方式

源码是当前 `mailcairn` 根目录；已知 Python 相对位置：`../work/bilingual-20261109/build-python/python.exe`（3.13.17），Node 24.22.1。接手后根据当前工作目录解析绝对路径，不依赖开发机盘符或 `python` 命令一定指向该环境。

在项目目录，用已知 Python 路径替换下列 `python`：

```text
python -W error::RuntimeWarning -m unittest discover -s tests -q
python -m unittest tests.test_store tests.test_parse -q
node --max-old-space-size=256 scripts/check_frontend.mjs
node scripts/check_connections.mjs
node scripts/check_i18n.mjs
node scripts/check_startup.mjs
python scripts/release_check.py
python scripts/build_windows.py --output <源码外的新构建目录>
python scripts/audit_bundle.py --project . --build <构建目录>
python scripts/package_release.py <源码外的源码ZIP路径>
```

不要把尖括号示意参数原样运行。构建/包必须在源码目录之外。源码业务或静态资源变更后重建 EXE、重核对，不能沿用旧哈希。源码文档变更后重打源码 ZIP。Windows ZIP 需要核对全目录成员、CRC、哈希和必要许可，而非仅测试可解压。

恢复后若验收Alpha.7，实际 EXE 冒烟应使用新的合成 data-dir、`--no-browser`、`--language zh-CN`，从 instance 文件传 token 而不打印。冒烟工具要求新的空工作目录，可传 `--source-dir`、`--work-dir`、`--report`、`--expected-version 0.1.0-alpha.7`、`--origin`、`--token-file`；运行前读脚本帮助确认具体参数，不复制旧端口。恢复中的源码 helper 与实际 EXE 原生恢复要分开报告。

浏览器必须从当前技能目录读取 `ego-browser/SKILL.md`（本机位于当前用户的 `.agents/skills` 下），并运行 `ego-browser skill` 获取当前 API。测试用完整 UTF-8 `.mjs` 写至允许目录，通过 CLI 导入；每轮遵守当前 Skill 的 TaskSpace 复用/结束规则。TaskSpace 8在暂停前尚未记录结束，恢复时先查询它是否存在并按规则复用；只有确认旧任务已结束且技能允许时才能建新任务，不能用新空间恢复出错页面。截图需在同一有效视口设置下确认尺寸、实际动画结束和页面状态，再保存；不要等待错误类名。

当前沙箱普通 shell 可读项目，但写入本项目父目录可能 Access denied；允许写工作区包含相对项目根的 `../../defalt_folder` 等，以接手环境权限为准。使用正常 `require_escalated` 自动审批完成用户授权项目写入，禁止借其他工具绕过拒绝。Ego bootstrap 在普通沙箱不可连接时也需要正常审批的同一用户环境。不要借此修改系统权限/网络。

## 10. 已知限制与未完成验收

1. 真 Gmail 新信自动到达仍被连接 EOF/重置阻塞；付费 Proton Bridge 未实测，免费账号不支持该路径。无 OAuth、多文件夹发现、SMTP、跨设备同步。
2. Alpha.5/6/7均没有第二台干净Windows验收，原生选择器全流程只在旧Alpha.4做过；尚无正式签名、低性能实机、真实手机/其他浏览器引擎或读屏器验证。
3. 没有第三方安全审计、物理断电实验、跨文件凭据崩溃事务保证；本机访问控制不是防同用户恶意软件边界。邮件与备份不加密。
4. 不支持上述邮箱容器/压缩格式和 Proton JSON 完整层级；展示纯文本，不还原完整 HTML，附件仅按名字检索。日期按原 Date 的日历日期筛选，不作跨时区统一语义保证。
5. 恢复依赖 NTFS 硬链接能力，FAT/exFAT 实机未验收；不能把本机测试扩大为所有文件系统支持。
6. 字节去重不是逻辑邮件去重；MBOX 转换可能新增同义记录。没有服务商导出完整性或原信真实性认证。
7. 用户尚未认可最新动效效果；Alpha.5前缀新截图是稳定终态，旧中途截图不作新版验收。首次静态 opening 未初始化现象原因未确认，后续两次启动通过，需继续调查。尚无外部真实用户试用/留存/商业验证，不能承诺市场成熟度。

## 11. 发布权利和隐私边界

项目采用 **PolyForm Noncommercial 1.0.0**，公开源码但不允许未经授权商业使用，作者保留未来盈利/单独商业授权权利。必须称 source-available/非商业许可公开源码，不能误称 OSI 开源或允许商用的开源。未填写的真实作者商业联系信息不能编造；贡献策略须保证未来商业许可所需权利。

本地 Hanken Grotesk、Newsreader 字体为 OFL；Windows Python/Tk 等随包许可由构建审计核对。没有新增运行依赖。未来新增依赖需重新检查兼容性与再分发要求，不能凭“免费”推断可商业授权。

发布前扫描源码/ZIP/截图，不含密码、邮箱档案、SQLite/WAL、会话令牌、instance 文件、开发机个人用户名路径或含私人侧栏截图。内部证据路径只是定位线索，不复制原始私人报告到公开包。有限规则扫描不等于完整隐私或安全认证。

## 12. 后续待办与交接要点（等待用户验收后决定）

1. 当前 Alpha.9 的体验打磨、门面整理、全流程验收、本地打包和候选入口切换已全部完成，用户可直接通过 `../Open-MailCairn-Candidate.cmd` 打开最新 **0.1.0-alpha.9** 候选，或使用 `../deliverables/GITHUB-RELEASE-AND-PROMO-ALPHA9.md` 中的文案准备公开发布。
2. 未完成并需用户或后续阶段关注的项目边界：
   - 真 Gmail 后续新信自动到达 TLS EOF/重置问题；
   - 付费 Proton Mail Bridge 实测；
   - 第二台干净 Windows 电脑与当前最新 build 的原生 Windows 文件选择器恢复全流程重测；
   - 低性能实机、真实手机触控、真实读屏器播报及用户最终视觉体验确认；
   - 已按作者确认在 `COMMERCIAL.md`、`SECURITY.md` 与 `NOTICE` 写入公开联系邮箱 `yuyuio123@protonmail.com`（贡献权利策略已在 `CONTRIBUTING.md` 明确，PolyForm Noncommercial 1.0.0 许可保持不变），本地干净发布仓已就绪，等待用户执行最终一步建仓/推送确认。

## 13. 给接手Agent的简短开场提示

可直接参考第 1 节与第 8 节向用户汇报当前最新候选 `0.1.0-alpha.9` 的已验证与未验证范围；未经用户确认不得上传 GitHub。
