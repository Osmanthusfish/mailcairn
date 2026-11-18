# Provider exports → MailCairn / 从邮箱导出到 MailCairn

Reviewed **2026-11-09**. This guide separates provider documentation from MailCairn behavior. **With the owner's authorization, one ordinary Proton welcome message was exported through the signed-in web UI (More → Export), imported and found by search. Its downloaded original matched the source EML byte-for-byte; all ten decoded inline attachment payloads matched, and backup/restore passed.** Its unread state was restored; no mail was sent or deleted. Gmail and Proton bulk export remain documentation-only; neither one real message nor synthetic fixtures establish provider completeness. See [executed checks](test-results.md).

核查日期：**2026-11-09**。本指南区分官方文档、当前软件行为和未验证事项。**经用户授权，已从 Proton 测试邮箱网页导出一封普通欢迎邮件，导入后可搜索；下载原件与源 EML 字节一致，10 个解码后的内嵌附件内容一致，备份恢复通过。** 已恢复该邮件未读状态，没有发送或删除邮件。Gmail 及 Proton 全量导出仍仅作文档核查；单封实测和合成样本不能证明整个邮箱导出完整。实测记录见[验证报告](test-results.md)。

## New mail without repeated exports / 新邮件免重复导出

Use **Connect mailbox**, then **Mailboxes** for connection status and **Sync now / Pause / Resume / Disconnect**. The current UI archives **INBOX every five minutes while MailCairn runs**; keep the native controller (or source server) open. It reads without changing source flags or deleting mail, and retains archived copies after source deletion. Closing the reader tab alone does not stop the worker; quitting the application does. Mail removed from INBOX before a check can be missed. Initial connection also reads mail already in INBOX.

使用**连接邮箱**，在**邮箱连接**查看状态并**立即同步／暂停／继续同步／断开连接**。当前界面在应用运行时**每 5 分钟归档 INBOX 收件箱**，首次也读取已有收件箱邮件；须保持原生控制窗口或源码服务运行。不会更改已读标记或删除源邮件，已归档副本不随源端删除。只关闭阅读网页不会停止后台，退出应用会停止；检查前已移出收件箱的邮件可能遗漏。

- **Gmail:** an eligible account's app password, with 2-Step Verification; normal passwords and Google OAuth sign-in are not supported by this release. [Google's requirements](https://support.google.com/accounts/answer/185833). / 需符合条件账号的应用密码及两步验证，本版没有 Google OAuth 登录。
- **Proton:** the official connector requires a paid plan and running local Bridge, using **Bridge credentials**, not your Proton account password or existing web session. **It does not currently connect a Free account automatically.** Unofficial alternatives such as Hydroxide exist but have not been validated or integrated; see [sync research](mail-sync-research.md). / 官方连接器需付费套餐和运行中的 Bridge，填写其专用凭据；**当前不能自动连接免费账号**。非官方 Hydroxide 等路径存在，但尚未验证与集成，不能说免费接入绝无可能。
- **Other IMAP:** use the provider's TLS host, port and supported credential; the UI targets INBOX. / 其他 IMAP 使用提供商的 TLS 主机、端口及允许的凭据，界面只连接 INBOX。

Windows can remember credentials when its current-user DPAPI capability check passes; otherwise credentials remain in memory. SQLite backups exclude connection configuration, sync progress and credentials: reconnect after restoring. No real Gmail or Proton sync account has been tested in the research described here. The export workflows below remain useful for history outside INBOX, unsupported accounts and recovery; the earlier real Proton test was a **manual export**, not automatic synchronization.

Windows 当前用户 DPAPI 能力检测通过时可记住凭据，否则仅保存在进程内存。SQLite 备份不含账号配置、同步进度或凭据，恢复后需重新连接。本指南最初研究未实测自动同步；后续真实 Gmail 首次归档了 120 封，新邮件轮询遇到未解决的 TLS 连接故障，详见[测试记录](test-results.md)。此前真实 Proton 实测是**手动导出**，不能当成同步验收。以下导出流程仍用于收件箱之外的历史、未支持账号和恢复。

## Manual export routes / 手动导出路径

| Source / 来源 | Route and output / 路径与产物 | Availability / 条件 |
| --- | --- | --- |
| Gmail, bulk / 批量 | Takeout → ZIP/TGZ → extracted MBOX / 解压后的 MBOX | Personal-account instructions do not require a paid plan; organization policies may restrict export. / 个人账号官方步骤未要求付费，组织账号可能受管理员限制。 [Google](https://support.google.com/mail/answer/10016932?hl=en) · [Takeout](https://support.google.com/accounts/answer/3024190?hl=en) |
| Gmail, one message / 单封 | Open message → More → Download message → `.eml` / 打开邮件 → 更多 → 下载邮件 | Desktop web / 电脑网页。 [Google](https://support.google.com/mail/answer/9261412?hl=en) |
| Proton, bulk / 批量 | Proton Mail Export Tool → `.eml` + `.json` directory / 邮件与元数据目录 | Free and paid accounts; Windows, macOS, Linux. / 免费和付费账号均可使用，电脑端工具。 [Proton](https://proton.me/support/proton-mail-export-tool) |
| Proton, one message / 单封 | Web message → More → Export → `.eml` / 网页邮件 → 更多 → 导出 | All accounts / 所有账号。 [Proton instructions](https://proton.me/support/export-import-emails) · [format confirmation](https://proton.me/business/blog/how-to-attach-email-to-email) |
| Proton via existing mail client / 已使用客户端 | Bridge + Thunderbird → select messages → Save as → EML / 选中邮件后另存为 EML | Bridge requires a paid Proton plan. / Bridge 需付费套餐。 [Availability](https://proton.me/support/export-import-emails) · [steps](https://proton.me/support/import-export-mbox-eml-using-proton-mail-bridge) |

**Format provenance:** Google's public help verifies the export process and metadata; the explicit Takeout MBOX format and Mail-selection screenshots are additionally documented in the [University of Alberta IT guide, pp. 2, 5–9](https://www.ualberta.ca/en/information-services-and-technology/media-library/create-an-email-archive-using-google-takeout.pdf). That is an institutional primary guide, not a Google-authored page or a newly captured account session. No fixed export filename or exact folder layout is guaranteed here.

**格式证据：** Google 帮助页说明导出流程和元数据；MBOX 格式及 Mail 选择界面另由上述大学 IT 官方指南佐证。该指南不是 Google 撰写，也不是本次登录截图；此处不承诺固定文件名或目录结构。

## Gmail: export and locate the input / 导出并找到输入文件

1. Open [Google Takeout](https://takeout.google.com/) yourself. Deselect other products, select **Mail**, and inspect **All Mail data included**; choose all mail or the desired labels. / 自行打开 Takeout，取消其他产品，只选 **Mail**，检查包含范围，选择全部邮件或需要的标签。
2. Continue; choose an emailed download link, one export, **ZIP**, and a practical archive-part size. Request the export, then download **every part**. TGZ is another supported container. / 继续，选择邮件下载链接、一次导出、ZIP 和分卷大小；导出完成后下载**全部分卷**，也可选择 TGZ。
3. Extract locally. Find the `.mbox` files inside the extracted Mail data; select those in MailCairn. Do not select `archive_browser.html`, settings JSON, or the ZIP itself. / 在电脑解压，从邮件数据中找到 `.mbox` 并导入；不要选择说明 HTML、设置 JSON 或 ZIP 本身。

The workflow follows [Google's download guide](https://support.google.com/accounts/answer/3024190?hl=en) and the [institutional walkthrough](https://www.ualberta.ca/en/information-services-and-technology/media-library/create-an-email-archive-using-google-takeout.pdf). Takeout has no direct date-range export; request-time changes may be absent. Downloading does not delete cloud mail. / 流程依据上述文档；Takeout 没有直接按日期范围导出的选项，导出期间的更改可能未包含；下载不会删除云端邮件。

## Proton: free bulk export / 免费批量导出

Use the current **Proton Mail Export Tool** linked from [Proton's guide](https://proton.me/support/proton-mail-export-tool), not an old Import-Export installer. Minimums listed there: Windows 10; macOS 10.15 Intel / 11 Apple Silicon; Ubuntu 20.04 LTS. / 使用当前官方 Export Tool，不依赖旧版 Import-Export 下载地址；最低系统版本如上。

1. Extract the downloaded tool; launch `proton-mail-export-cli` (Linux: `./proton-mail-export-cli`). / 解压工具并启动。
2. Authenticate inside Proton's tool, including 2FA/mailbox password when requested; choose **B / Backup** and an output directory. Never enter these Proton account credentials into MailCairn; its optional Bridge connector uses a different Bridge password. / 在 Proton 工具内登录并选择备份和目录；不要把 Proton 账号密码填入 MailCairn，可选连接器使用的是另一套 Bridge 专用密码。
3. Wait for completion. Keep **both EML and JSON**; import the EML files into MailCairn. The documented mail output is a directory, not an MBOX or a promised ZIP. / 等待完成，保留 EML 和 JSON；向 MailCairn 导入 EML，官方说明的产物是目录。

The tool exports decrypted mail and metadata, needs free disk space and a stable connection, and cannot pause/resume. Its documented workflow exports all mail; selective folder/date export is not documented. / 工具导出解密后的邮件和元数据，需要空间和稳定连接，不支持暂停续传；官方流程为全量，未说明按文件夹或日期筛选。 [Official tool guide](https://proton.me/support/proton-mail-export-tool)

## What survives import / 导入后保留什么

| Item / 项目 | Provider evidence and MailCairn boundary / 提供商证据与当前边界 |
| --- | --- |
| Headers, body, attachments / 头部、正文、附件 | Google lists these as export contents; encrypted Gmail messages stay encrypted. Proton's EML export preserves message attachments, but external links are not embedded files. MailCairn stores the supplied message bytes and reads MIME attachments; it does not decrypt encrypted mail or fetch linked files. / Google 明确包含这些内容，但加密邮件仍加密；Proton EML 保留邮件附件。外链不是已嵌入附件，MailCairn 不下载外链或解密邮件。 [Google](https://support.google.com/mail/answer/10016932?hl=en) · [Proton](https://proton.me/business/blog/how-to-attach-email-to-email) |
| Gmail labels / 标签 | Google documents `X-Gmail-Labels`. MailCairn retains and displays its text; it does not rebuild a folder tree or provide label filtering. / 保留并显示该头部文本，不重建目录树，也没有标签筛选。 [Google](https://support.google.com/accounts/answer/3024190?hl=en) · [parser](../mailcairn/parse.py) |
| Proton folders, labels, status / 目录、标签、状态 | Proton documents JSON metadata but not its full schema on the support page. MailCairn currently does not ingest JSON or reconstruct Proton hierarchy/read state. Preserve the original EML+JSON set for provider restoration. / 官方说明有 JSON 元数据，帮助页未详述其结构；当前不导入 JSON，不还原 Proton 目录／已读状态。务必保留完整导出目录。 [Proton](https://proton.me/support/export-import-emails) |
| Source hierarchy / 来源层级 | Import filenames are recorded in receipts; ordinary file selection does not reconstruct provider folders. One Gmail message can have multiple labels: do not equate labels, files, conversations and unique-message counts. / 明细记录文件名，普通文件选择不还原来源目录；不要把标签数、文件数、会话数当成唯一邮件数。 |
| Byte identity / 字节一致性 | Exact-byte deduplication can retain logically identical mail if exports rewrite headers or escaping. An import receipt counts recognized records, not everything originally present at the provider. / 不同导出改写字节时可能保留逻辑重复；导入明细不能证明提供商导出完整。 |

## Finish the local journey / 完成本地归档

Start MailCairn using the [README](../README.md). In **Import mail**, choose extracted `.mbox` / `.eml` files or use **Choose folder** for an export directory and its subfolders. The folder workflow selects mail files and reports how many other files, including Proton JSON sidecars, were skipped; it does not import their metadata. Retain originals. Thousands of files still produce per-file receipts and have not been benchmarked as a real Proton export. ZIP/TGZ, PST/OST, Maildir, and JSON are not accepted inputs. Renaming an extension does not convert a file.

按 [中文 README](../README.zh-CN.md) 启动，在**导入邮件**中选择解压后的 MBOX／EML，或用**选择文件夹**处理导出目录及子目录。文件夹流程选择邮件文件，并报告跳过的其他文件数量（包括 Proton JSON）；不会导入其中元数据。请保留原始目录。数千文件仍产生逐文件明细，尚未用真实 Proton 全量导出测性能。不能直接导入 ZIP／TGZ、PST／OST、Maildir 或 JSON；改扩展名不等于转换格式。

After import, inspect the receipt and every skipped/error outcome. Search a known older message and a recent one, check Chinese/non-ASCII text, open an attachment, and compare important examples with the source. Re-importing the same bytes should add no duplicates. Back up from the app, restore into a **new** data directory, and repeat retrieval before treating the archive as usable. The executed single-message Proton journey provides one concrete check; these acceptance steps still apply to your own complete export.

导入后检查明细和跳过／失败项；找回一封旧邮件和一封近期邮件，核对中文、附件及重要样本。同字节重导应不再新增。使用应用备份并恢复到**新目录**，再次检索确认。已完成的 Proton 单封流程是一项具体实测，你自己的完整导出仍须完成上述验收。

The real Proton sample exposed a legacy HTML preview defect. After the inert-text parser fix, its preview contains **37 readable lines**, while the original and attachment bytes remain unchanged. This checks that one message's text is usable; it does not promise original HTML layout or inline-image rendering. A separate synthetic folder batch passed the browser FileList-to-HTTP workflow: **six EML files imported, six JSON sidecars skipped and counted**. The operating system's native browser directory-picker transport was not verified; no real Proton bulk CLI export was used.

这封真实 Proton 样本发现了旧式 HTML 预览缺陷；修复静态文本解析后形成 **37 行可读文本**，原件和附件字节不变。这不代表还原 HTML 排版或展示内嵌图片。另有合成文件夹批次通过浏览器 FileList 到真实 HTTP 的流程：**导入 6 个 EML，跳过并统计 6 个 JSON**；尚未验证操作系统原生浏览器文件夹选择器的传递过程，也未执行真实 Proton 批量 CLI 导出。

A Windows portable EXE now supplies a native controller for the local service, opening the browser reader, opening the archive folder and starting restore. Its final artifact/notice audit passed. On the current Windows machine, the native backup picker restored into a new archive, opening the archive folder selected the original vault, and closing the controller removed service metadata. Restarting the same EXE and archive reused the port and preserved English browser language and six messages. English and Chinese controller layouts were inspected without clipping. It is unsigned and has not been checked on a second clean Windows machine. These native controller checks do not verify the browser's directory-import picker. / 当前已提供 Windows 便携 EXE，以原生控制窗口管理本机服务、打开浏览器阅读界面、打开档案文件夹和发起恢复，最终包及许可审查通过。本机 Windows 实测已通过：原生备份文件选择器恢复到新档案，打开档案文件夹定位到原始档案，关闭控制窗口后服务元数据清除；同一 EXE 重开同一档案复用端口，保留浏览器英文偏好和 6 封邮件。中英文控制窗口均检查无裁切。构建未签名，未在第二台干净 Windows 验证；以上不代表验证了浏览器的目录导入选择器。

Current defaults are 20 GiB per file and 32 MiB per message, **not tested performance guarantees**. A MIME-encoded message can exceed its decoded attachment size. Oversized records are skipped with receipts. Allow disk space for originals, extraction, temporary upload, SQLite/index and backup; use [measured results](test-results.md) and [known limits](known-limits.md), not a blanket capacity promise. Exported Proton mail, MailCairn's database and backups are not protected by Proton's online encryption once stored locally; MailCairn adds no application-level encryption.

默认每文件 20 GiB、每邮件 32 MiB 是限制而非性能保证；MIME 编码后的整封邮件可能大于附件本身。超限会记录为跳过。原始压缩包、解压、临时上传、数据库／索引和备份均需磁盘空间。Proton 导出后的本地明文，以及 MailCairn 数据库与备份，没有 MailCairn 提供的应用级加密。

## Source dates and verification boundary / 日期与验证边界

All linked sources were accessed **2026-11-09**. Google/Proton support pages and the university PDF did not expose a reliable publication/update date in retrieved text; dates are **unknown**, not inferred from crawl timestamps. Proton's attachment article is dated **2026-07-31**. Provider menu names can change. OS minimums above belong to Proton's tool; they do not establish MailCairn OS certification. The authorized single-message Proton web export does not validate the bulk tool binary, bulk-export duration, provider JSON schema, full account hierarchy, or attachment completeness across an account.

链接访问日期均为 **2026-11-09**。支持页及大学 PDF 的可靠发布／更新日期未显示，记为未知；不把抓取日期当发布日期。Proton 附件文章日期为 **2026-07-31**。已完成的 Proton 单封网页导出不代表验证了批量工具、批量耗时、JSON 结构、完整账号层级或整个账号附件完整性。
