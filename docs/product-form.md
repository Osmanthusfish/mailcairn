# Product form decision / 产品形态选择

Decision date: **2026-11-09**. Selected form: **a packaged local desktop archive**. A Windows portable EXE now bundles the Python/SQLite service and a native controller; reading and search remain in the local browser interface. The controller provides opening the reader, opening the archive folder and starting restore. The final artifact/notice audit and current-machine native controller QA passed: a backup selected through the Windows picker restored into a new archive; opening the archive folder reached the original vault; closing cleared service metadata; restarting reused the port and preserved English browser language and six messages. English and Chinese layouts showed no clipping. This is an unsigned portable review build, not a signed consumer installer; a second clean Windows machine has not been tested. The browser's directory-import picker remains unverified.

已选择并实现：**打包的本地桌面归档工具**。Windows 便携 EXE 捆绑 Python／SQLite 服务和原生控制窗口，阅读、搜索仍在本机浏览器进行。最终包及许可审查和本机原生界面验收通过：Windows 选择器选取备份后恢复到新档案，打开文件夹定位原始档案，关闭后清除服务元数据，重开复用端口并保留浏览器英文偏好和 6 封邮件。中英文控制窗口均无裁切。目前是未签名的便携审阅版，尚未在第二台干净 Windows 验证；浏览器目录导入选择器仍未验证。

## Evidence that changes the decision / 影响选择的证据

**Scope update:** the user explicitly requested automatic new-mail archiving without repeated exports. The desktop remains the chosen form, now with an optional read-only IMAP worker: INBOX initially and every five minutes while running, plus sync/pause/disconnect controls. File imports remain for historical migration. This decision supersedes the original manual-only workflow below; it is a user requirement, not new market validation. Gmail app-password eligibility and paid Proton Bridge constrain the implemented connectors. The user's Free Proton account is not automatically connected by this release; unofficial alternatives warrant separate validation, not a claim that upgrading is the only possible answer. See [sync research](mail-sync-research.md).

**范围更新：** 用户明确要求免重复导出的新邮件自动归档。仍选择桌面形态，新增可选只读 IMAP 后台：首次归档 INBOX，运行时每 5 分钟检查，并提供立即同步、暂停和断开；文件导入保留为历史迁移。这替代了下面原先仅手动导入的范围，是用户需求而非新的市场验证。当前连接器受 Gmail 应用密码资格及付费 Proton Bridge 条件约束；本版尚不能自动连接用户的免费 Proton 账号，非官方替代需另行验证，不能把升级付费说成唯一可能答案。

The [provider journey](provider-import-guide.md) begins before the import screen. Gmail bulk export involves requesting, waiting, downloading and extracting files. Proton's free bulk route already requires a Windows/macOS/Linux CLI and produces many EML files plus metadata. Google's own [Takeout guide](https://support.google.com/accounts/answer/3024190?hl=en) recommends viewing exports on a desktop computer. These documented steps favor a desktop workflow, but do not prove that users prefer MailCairn or will pay for it.

[提供商流程](provider-import-guide.md)发生在导入页之前：Gmail 要申请、等待、下载与解压；Proton 免费全量导出已要求电脑命令行工具，并产生多份 EML 与元数据。Google 官方也建议电脑查看导出。这支持电脑优先的工作流判断，不等于验证了用户愿意采用或付费。

The [market review](market-research.md) provides moderate evidence for independent historical-mail retrieval and low confidence in an underserved paying segment. The clearest Gmail requester later succeeded with OpenArchiver. MailStore Home, Thunderbird and browser-local viewers are credible alternatives. Choosing desktop is an engineering/product inference from the selected manual-export journey, not a new market validation result.

现有[市场研究](market-research.md)对历史邮件检索需求有中等信心，对付费缺口仍信心低。典型 Gmail 发帖者后来通过 OpenArchiver 解决了问题；MailStore Home、Thunderbird 和本地浏览器工具都值得公平比较。本建议是基于所选流程的产品推断。

## Compare the forms / 形态比较

| Form / 形态 | Fit for this journey / 适配情况 | Cost or unresolved problem / 代价与问题 | Decision / 选择 |
| --- | --- | --- | --- |
| Source-run local service + browser / 源码启动本机服务＋浏览器 | Persistent SQLite, receipts and recovery; files already on the computer. / 持久索引、明细和恢复，数据已在电脑。 | This route requires Python and a running terminal; exports still need extraction. / 此路径需 Python 和持续运行的终端，导出仍需解压。 | Retained for developers and source users. / 保留给开发者和源码用户。 |
| Packaged desktop / 打包桌面应用 | Implemented Windows EXE bundles runtime and native process/archive controller; browser handles reading. / 已实现 Windows EXE，捆绑运行时和原生控制窗口，浏览器负责阅读。 | Unsigned; clean-machine, upgrade and other-platform validation remain. / 未签名，干净系统、升级和其他平台仍待验证。 | Current selected review build; artifact audit passed. / 当前选定审阅版，包内容审查通过。 |
| Pure browser-local / 纯浏览器本地处理 | No Python install; useful for a quick preview and could support streaming large files. / 无需 Python，适合快速预览，也可实现大文件流式处理。 | Persistent storage, reopening, backups and browser compatibility need a new implementation. Quota/eviction behavior is engine-specific. / 持久化、重开、备份与兼容需另做，配额／驱逐依赖浏览器。 | Credible alternative, not ruled out; do not rewrite now merely for the website label. / 是可信替代，不为“网页产品”名义立即重写。 |
| Hosted upload web app / 托管上传网站 | Easier installation and possible multi-device access. / 免本机安装，可实现多设备访问。 | Uploading raw mail creates sensitive server storage, authentication, deletion, recovery and operating-cost responsibilities; large uploads add another transfer. / 原始邮件上云引入敏感存储、身份、删除、恢复和运营责任，并增加一次大文件传输。 | Poor fit for the present local/private positioning; would be a separate product decision. / 与当前定位不符，需另作产品决策。 |
| Native mobile app / 原生手机应用 | Could help occasional reading if a deliberate secure transfer/sync feature exists. / 若有明确安全传输机制，可方便偶尔阅读。 | Export sourcing remains desktop-oriented; bulk files, attachments and long imports introduce additional mobile work. No physical-phone workflow has been tested. / 导出仍偏电脑，大文件与长导入需额外设计；未做真机流程测试。 | Defer; narrow desktop layout is not mobile access. / 暂缓，窄屏适配不等于手机可访问。 |

Browser-local is technically viable. [WebKit's storage policy](https://webkit.org/blog/14403/updates-to-storage-policy/) documents quotas, best-effort eviction and a persistence request API. This supports explicitly testing persistence and backup behavior; it does **not** support claiming that every browser archive loses data or cannot handle gigabytes. The article is dated **2023-08-10**, accessed **2026-11-09**; it is platform documentation, not a benchmark of MailCairn or its competitors.

纯浏览器方案技术上可行。[WebKit 文档](https://webkit.org/blog/14403/updates-to-storage-policy/)说明配额、默认尽力存储和申请持久化 API，因此需实测持久化与备份；不能据此声称所有浏览器归档都会丢失或不能处理 GB 文件。文档发布于 **2023-08-10**，访问于 **2026-11-09**，不属于性能对比。

## Concrete next release / 下一版具体范围

1. **Finish desktop release validation:** the Windows portable runtime/controller is implemented, its contents audited, and current-machine native restore, folder-opening, close/restart and bilingual layout checks passed. Next verify a second clean machine, shutdown during work and upgrades without archive replacement. Signing/distribution remains release work, not a claim already completed.
2. **Complete the input journey:** the current iteration adds bilingual provider instructions and a folder picker with skipped-sidecar counts. Next, add discovery/count preview before importing and one batch receipt. Add bounded ZIP extraction only with path checks, size limits and explicit handling of ignored metadata; retain the original export. TGZ can remain a clearly documented manual step until implemented and tested.
3. **Make metadata fidelity explicit:** display Gmail labels without implying a folder tree. Before importing Proton JSON, obtain a consented or official representative schema and write compatibility fixtures; preserve unmatched sidecars and report unrecognized fields. Do not reconstruct labels from guesses.
4. **Prove retrieval and recovery:** observe a first-time user importing an authorized export, explaining skipped records, finding known mail/attachments and restoring a backup. Record task outcomes and timings without collecting message content. Add mixed attachments, realistic EML file counts and larger exports to performance tests before advertising capacity.

当前已加入 Windows 便携 EXE、双语导出说明、文件夹选择和跳过辅助文件统计，本机控制窗口恢复、打开文件夹、关闭重开和双语布局验收通过。下一步完成第二台干净系统与升级验证；增加导入前计数确认和统一批次明细；有边界地支持 ZIP；明确标签与元数据保真度，拿到可信 JSON 结构后再兼容；继续真实用户验收与大规模附件／多文件测试。合成文件夹已通过 FileList＋真实 HTTP 导入 6 个 EML、跳过 6 个 JSON；原生浏览器目录选择器传递尚未验证。

The current defaults and synthetic benchmark are documented in [known limits](known-limits.md). A configured 20 GiB allowance is not evidence that a typical 20 GiB Takeout or tens of thousands of Proton files are pleasant or reliable to import. The owner-authorized **single-message Proton web export → import → search → original/attachment recovery → backup/restore passed**. Original EML bytes and ten inline attachment payloads match; a legacy HTML parsing fix produces a 37-line readable preview. Gmail and Proton bulk CLI exports remain documentation-verified, not executed. This technical check is not a first-time-user study or proof of market demand.

当前配置和合成基准见[能力边界](known-limits.md)。20 GiB 配置上限不能证明同规模真实 Takeout 或数万 Proton 文件的使用体验。**授权的 Proton 单封网页导出、导入、搜索、原件／附件取回、备份恢复已通过**：原始 EML 和 10 个内嵌附件字节一致，修复旧式 HTML 后预览为 37 行。Gmail 和 Proton 批量 CLI 仍未执行。这是技术验证，不是首次用户研究或市场需求证明。

## Product validation and commercial scope / 验证与商业范围

The original repeat-use hypothesis was periodic import and occasional retrieval. The explicit automatic-ingestion requirement now adds recurring background checks while the application runs; successful retrieval, retained source bytes and recovery still matter more than daily clicks. A packaged edition or support/commercial license remains an unvalidated revenue hypothesis. Compare working alternatives fairly and validate whether the supported connection routes meet the actual user's account conditions before claiming the task solved. Preserve the source-available noncommercial license and separate commercial rights; packaging does not change them.

原假设是周期性导入、偶尔检索；现在按明确要求加入应用运行期间的自动检查，找回原件和恢复成功仍比日活更重要。打包版、支持或商业许可收入仍是假设，没有已验证价格或付费意愿。应公平比较已有方案，并确认接入路径符合实际用户账号条件后再宣称解决需求；打包不改变非商业源码许可及单独商业授权边界。
