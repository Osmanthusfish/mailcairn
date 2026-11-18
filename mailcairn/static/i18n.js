/* Only interface copy enters this catalogue. Private mail is always literal text. */
"use strict";
const uiCatalogue = {
  "In the desktop window, choose “Restore backup…” to verify and open a copy in a new folder. From source, run:": "在桌面控制窗口点击“恢复备份…”即可校验并在新文件夹中打开副本；源码运行可使用：",
  "Use / to search, I to import, G for mail, H for history.": "按 / 搜索、I 导入、G 查看邮件、H 查看记录；",
  "Use , for reading room and ? for commands. Ctrl / ⌘ K always opens commands.": "按 , 打开阅读设置、? 打开命令。Ctrl / ⌘ K 始终可用。",
  "message preserved": "封邮件已保存",
  "Connection settings could not be saved and the previous saved password could not be restored. The saved password may have changed. Reconnect this account before restarting the app.": "连接设置未能保存，原先保存的密码也未能恢复。本机保存的密码可能已改变，请在重启应用前重新连接此邮箱。",
  "The connection was not added because settings could not be saved. Its saved password may remain on this computer because local cleanup failed. Check disk space and permissions before trying again.": "连接设置未能保存，邮箱未添加成功。由于本机清理失败，密码可能仍保存在此电脑上。请检查磁盘空间和文件权限后再试。",
  "Subtle": "柔和",
  "Rich": "丰富",
  "Connection unavailable": "暂时无法连接",
  "Cannot connect to Gmail right now. Your saved mail is still available.": "暂时无法连接 Gmail，已归档邮件仍可查看。",
  "Cannot connect to this mailbox right now. Your saved mail is still available.": "暂时无法连接此邮箱，已归档邮件仍可查看。",
  "MailCairn retries every 5 minutes while it is running.": "MailCairn 运行期间会每 5 分钟重试。",
  "After a connection error, automatic retries continue while MailCairn is running, the mailbox is not paused, and its password is available. A retry may still fail until the connection is available again.": "发生连接错误后，MailCairn 运行期间会在邮箱未暂停且密码可用时自动重试。连接恢复之前，重试仍可能失败。",
  "If Gmail opens in your browser but syncing fails, your network may allow the website but block mail connections. A connection error alone does not mean the app password is wrong. You can leave other apps running and import a Google Takeout export instead.": "如果浏览器可以打开 Gmail，但邮件同步失败，可能是网络允许访问网页，却无法连接邮件服务。连接错误本身不代表应用专用密码有误。你可以保持其他应用运行，改为导入 Google Takeout 导出的邮件。",
  "Other email": "其他邮箱", "Incoming mail server": "收信服务器", "Advanced settings": "高级设置", "Change this only if your provider or Bridge shows a different port.": "仅当服务商或 Bridge 显示不同端口时修改。", "How to connect your mailbox": "如何连接邮箱", "Preparing setup…": "正在准备…", "You'll need to enter your password after restarting MailCairn.": "重启 MailCairn 后需要重新输入密码。", "Syncing mail…": "正在同步邮件…",
  "Use a Google app password, not your usual Google password.": "请使用 Google 应用专用密码，不是平时登录 Google 的密码。", "Requires a paid Proton plan and Bridge running on this computer. Use the username and password from Bridge.": "需订阅付费 Proton 套餐，并在本机运行 Bridge。请填写 Bridge 中的用户名和密码。", "Use the incoming-mail settings from your email provider.": "请填写邮箱服务商提供的收信设置。", "Inbox only. Keep MailCairn running to receive new mail.": "仅归档收件箱。请保持 MailCairn 运行，以获取新邮件。", "Inbox only. Checks for new mail every 5 minutes while MailCairn is running.": "仅归档收件箱，MailCairn 运行期间每 5 分钟检查新邮件。",
  "Connect a mailbox": "连接邮箱", "Choose your email provider below for step-by-step instructions.": "选择你的邮箱服务商，按步骤完成连接。",
  "In your Google Account, turn on 2-Step Verification.": "在 Google 账号中开启两步验证。", "Create a Google app password for MailCairn. This is a separate password for this app, not your usual Google password.": "为 MailCairn 创建 Google 应用专用密码。这是专门供应用使用的独立密码，不是平时登录 Google 的密码。", "Choose Gmail in MailCairn, enter your full Gmail address and the app password, then choose Start syncing.": "在 MailCairn 中选择 Gmail，填写完整 Gmail 地址和应用专用密码，然后点击“开始同步”。",
  "App passwords may be unavailable for work or school accounts, Advanced Protection, or some security-key-only setups. If Google does not offer one, import a Google Takeout export instead.": "工作或学校账号、已加入高级保护计划的账号，以及部分仅使用安全密钥的账号可能无法创建应用专用密码。如果 Google 不提供此选项，可改用 Google Takeout 导出后导入邮件。", "Google's app-password instructions ↗": "Google 应用专用密码说明 ↗", "Connect Gmail": "连接 Gmail",
  "Automatic sync requires a paid Proton Mail plan and Proton Mail Bridge installed on this computer. Proton Free does not support this connection.": "自动同步需要付费 Proton Mail 套餐，并在本机安装 Proton Mail Bridge。Proton Free 不支持此连接方式。", "Open Bridge and sign in to Proton there. Keep Bridge running while MailCairn syncs.": "打开 Bridge 并在其中登录 Proton。MailCairn 同步期间需保持 Bridge 运行。", "Copy the username and password shown in Bridge's mailbox settings into MailCairn. Your usual Proton account password will not work here.": "将 Bridge 邮箱设置中显示的用户名和密码复制到 MailCairn。这里不能使用平时登录 Proton 账号的密码。",
  "The default Bridge port is 1143. If Bridge shows a different IMAP port, open Advanced settings in MailCairn and enter that number. The local Bridge connection uses STARTTLS; MailCairn remembers its certificate and stops if it changes.": "Bridge 默认端口为 1143。如果 Bridge 显示不同的 IMAP 端口，请打开 MailCairn 中的“高级设置”并填写该端口号。本机 Bridge 连接使用 STARTTLS；MailCairn 会记住其证书，并在证书变化时停止连接。", "Without a paid plan, use Proton Mail Export Tool to export EML files, then import the folder into MailCairn. File import does not require Bridge.": "没有付费套餐时，可用 Proton Mail Export Tool 导出 EML 文件，再将文件夹导入 MailCairn。文件导入不需要 Bridge。", "Connect Proton Mail": "连接 Proton Mail",
  "Other email providers": "其他邮箱服务商", "Find your provider's incoming-mail settings for IMAP. You need the incoming server address, your username (often your full email address), and a password. Some providers require a separate app password or enabling IMAP first.": "查找邮箱服务商提供的 IMAP 收信设置。你需要收信服务器地址、用户名（通常是完整邮箱地址）和密码。部分服务商要求使用单独的应用专用密码，或先开启 IMAP。", "Enter those details under Other email. The default port is 993, using an encrypted SSL/TLS connection. Only change the port in Advanced settings if your provider specifies another SSL/TLS port. Unencrypted connections and remote STARTTLS-only servers are not supported.": "选择“其他邮箱”并填写这些信息。默认使用 993 端口和加密的 SSL/TLS 连接。只有服务商指定其他 SSL/TLS 端口时，才需在“高级设置”中修改。不支持未加密连接，也不支持仅提供 STARTTLS 的远程服务器。", "MailCairn cannot connect to a provider that requires OAuth sign-in only. You can still import its exported mail files.": "MailCairn 无法连接仅支持 OAuth 登录的邮箱服务商，但仍可导入其导出的邮件文件。", "Connect other email": "连接其他邮箱",
  "What happens after connecting": "连接之后", "The first sync saves existing mail from your inbox (INBOX). MailCairn then checks for new mail every 5 minutes while it is running. Other folders and Sent are not included.": "首次同步会保存收件箱（INBOX）中已有的邮件。此后，MailCairn 在运行期间每 5 分钟检查新邮件，不包含其他文件夹和已发送邮件。", "Closing the browser tab does not stop sync; quitting MailCairn does. Mail moved out of the inbox or deleted before the next check can be missed.": "关闭浏览器标签页不会停止同步，退出 MailCairn 才会停止。在下次检查前移出收件箱或删除的邮件可能无法归档。",
  "Adding a mailbox saves its settings; it does not confirm that sign-in worked. Open Mailboxes to check the status, last successful sync time and saved count. Choose View mail to read the archive. Sync now checks immediately; Pause stops future checks. Disconnect removes the connection but keeps archived mail.": "添加邮箱只是保存连接设置，不代表已成功登录。请打开“邮箱连接”查看状态、上次成功同步时间和归档数量。点击“查看邮件”阅读档案；“立即同步”会马上检查；“暂停”会停止后续检查；“断开连接”会移除连接，但保留已归档邮件。", "MailCairn only reads and copies mail. It does not send mail, mark it as read, or delete it from your provider.": "MailCairn 只读取和复制邮件，不发送邮件、不标记已读，也不删除服务商中的邮件。",
  "On Windows, when Remember on this computer is available, it protects the password with your Windows account using DPAPI. Otherwise, or when you turn this option off, the password stays only in memory. You must reconnect with your password after restarting MailCairn.": "在 Windows 上，“在这台电脑上记住密码”可用时，会通过 Windows 账户的 DPAPI 机制保护密码。其他情况下，或关闭此选项后，密码仅保留在内存中，重启 MailCairn 后需重新输入密码连接。", "Mailbox settings and passwords are stored separately from the mail database and are not included in Back up archive. The mail archive itself is not encrypted; protect the computer and your backup copies.": "邮箱设置和密码与邮件数据库分开保存，不包含在“备份档案”生成的备份中。邮件档案本身未加密，请保护电脑和备份副本。",
  "Archives INBOX only, then checks every 5 minutes while MailCairn runs. Other folders and Sent are not included. Cloud mail is never deleted or marked as read.": "仅归档收件箱（INBOX），运行期间每 5 分钟检查新邮件。不包含其他文件夹和已发送邮件，不会删除云端邮件或标记已读。",
  "Mail and receipts are stored in the database below. Use the backup button while the app is running. Mailbox settings and passwords are stored separately and are not included in this backup.": "邮件和回执保存在下方数据库中。应用运行时请使用备份按钮。邮箱设置和密码单独保存，不包含在这份备份中。",
  "Mailbox connection settings must be a JSON object under 16 KiB.": "邮箱连接设置必须是小于 16 KiB 的 JSON 对象。", "Mailbox connection settings require application/json.": "邮箱连接设置需使用 application/json 格式。", "Incomplete mailbox connection settings.": "邮箱连接设置接收不完整。", "Mailbox connection request timed out.": "邮箱连接请求超时，请重试。", "Mailbox connection settings are not valid JSON.": "邮箱连接设置的 JSON 格式无效。", "Could not save the mailbox connection. Check local storage and try again.": "无法保存邮箱连接，请检查本地存储后重试。",
  "Connect mailbox": "连接邮箱", "Mailboxes": "邮箱连接", "Connected mailboxes": "已连接邮箱", "Import file": "导入文件", "Import a file": "导入文件",
  "Keep your mail close. Find it whenever you need.": "把邮件留在身边，需要时随手可查。", "One-way archiving · Your cloud mail stays untouched": "单向归档 · 不改动云端邮件",
  "INBOX first, then new mail every 5 minutes while MailCairn runs.": "先归档收件箱；MailCairn 运行期间，每 5 分钟检查新邮件。",
  "MailCairn copies mail into this archive. It does not mark messages as read or delete anything from your mailbox. Only INBOX is synced; other folders and Sent are not included.": "MailCairn 将邮件复制到本地档案，不标记已读，也不删除邮箱中的内容。仅同步收件箱（INBOX），不包含其他文件夹和已发送邮件。",
  "Import existing exports or connect a mailbox for one-way local archiving. Your source files and cloud mail stay untouched.": "导入已有导出文件，或连接邮箱进行单向本地归档。原始文件和云端邮件都不会被改动。",
  "Close mailbox setup": "关闭邮箱设置", "Email provider": "邮箱服务商", "Other IMAP": "其他 IMAP",
  "Use your Gmail address and a Google app password, not your regular Google password.": "填写 Gmail 地址和 Google 应用专用密码，请勿填写 Google 账号的常用密码。",
  "Create an app password ↗": "创建应用专用密码 ↗", "Requires 2-Step Verification. Some work, school or protected accounts do not offer app passwords.": "需开启两步验证。部分工作、学校或受保护的账号不提供应用专用密码。",
  "Run Proton Mail Bridge on this computer. A paid Proton Mail plan is required.": "需在这台电脑上运行 Proton Mail Bridge，并订阅付费 Proton Mail 套餐。", "Set up Proton Mail Bridge ↗": "设置 Proton Mail Bridge ↗",
  "Use the username and password shown in Bridge, not your Proton account password. Bridge must stay running.": "使用 Bridge 中显示的用户名和密码，不是 Proton 账号密码。Bridge 需保持运行。",
  "Use your provider's IMAP server and an app password when required. The connection uses verified TLS.": "填写服务商提供的 IMAP 服务器地址，按要求使用应用专用密码。连接使用经过证书验证的 TLS。",
  "IMAP server": "IMAP 服务器", "Port": "端口", "Gmail address": "Gmail 地址", "App password": "应用专用密码", "Bridge username": "Bridge 用户名", "Bridge password": "Bridge 密码", "Username": "用户名", "Password or app password": "密码或应用专用密码",
  "Local Bridge · 127.0.0.1 · STARTTLS": "本机 Bridge · 127.0.0.1 · STARTTLS", "Encrypted connection · SSL/TLS": "加密连接 · SSL/TLS",
  "Remember on this computer": "在这台电脑上记住密码", "Checking credential storage…": "正在检查密码保存方式…", "Password saved with Windows account protection on this computer.": "密码通过此电脑的 Windows 账户保护机制保存。", "This session only. Enter the password again after restarting MailCairn.": "密码仅保留在本次运行的内存中，重启 MailCairn 后需重新输入。",
  "Archives INBOX, then checks for new mail every 5 minutes while this app runs. Other folders are not included.": "归档收件箱（INBOX），然后在应用运行期间每 5 分钟检查新邮件。不包含其他文件夹。",
  "Start syncing": "开始同步", "Reconnect mailbox": "重新连接邮箱", "Save password and sync": "保存密码并同步", "Enter the mailbox details and password to continue.": "请填写邮箱连接信息和密码。", "Adding mailbox…": "正在保存邮箱连接…",
  "Mailbox added. Check its sync status below.": "邮箱连接已保存，请在下方查看同步状态。", "Mailbox settings were saved, but status could not refresh. Open Mailboxes to check before adding it again.": "邮箱设置已保存，但状态刷新失败。请先打开“邮箱连接”检查，再尝试添加。",
  "Paused": "已暂停", "Password needed": "需要密码", "Up to date": "已同步", "Queued": "等待同步", "Syncing INBOX…": "正在同步收件箱…", "Waiting for the archive": "等待档案空闲", "Needs attention": "需要处理", "Ready to sync": "准备同步",
  "Loading mailboxes…": "正在加载邮箱连接…", "Connect your first mailbox": "连接你的第一个邮箱", "Mail from INBOX will be saved here automatically.": "收件箱中的邮件会自动保存到本地档案。", "Saved from this mailbox": "从此邮箱新增归档", "Not synced yet": "尚未完成同步",
  "Password protected by Windows": "密码由 Windows 保护", "Password kept for this session": "密码仅保留在本次运行中", "Reconnect to provide your password": "重新连接以提供密码", "Reconnect": "重新连接", "Sync now": "立即同步", "Pause": "暂停", "Resume": "继续同步", "Disconnect": "断开连接", "Mailbox disconnected. Archived mail was kept.": "已断开邮箱连接，已归档邮件已保留。",
  "Manage automatic archiving": "管理自动归档", "Archive your INBOX automatically": "自动归档收件箱",
  "Authentication failed. Check the username and app password.": "认证失败，请检查用户名和应用专用密码。", "Credentials are needed. Reconnect this account.": "需要提供密码，请重新连接此邮箱。", "Could not connect securely. Check the server, port and network.": "无法建立安全连接，请检查服务器、端口和网络。", "The mail server's security certificate could not be verified. Check the server address and your device's date and time.": "无法验证邮件服务器的安全证书。请检查服务器地址和设备的日期、时间。",
  "The Proton Bridge certificate changed. Remove and reconnect this account after checking Bridge.": "Proton Bridge 证书已更改。请先确认 Bridge 状态，再断开并重新连接此邮箱。",
  "A message exceeds the archive size limit. Sync stopped before that message.": "一封邮件超过档案大小上限，同步已停在该邮件之前。", "A message could not be archived. Sync stopped before that message.": "一封邮件无法归档，同步已停在该邮件之前。",
  "Connection settings could not be saved. Check disk space and permissions.": "无法保存连接设置，请检查磁盘空间和访问权限。", "The server returned an unsupported or incomplete IMAP response.": "服务器返回了不支持或不完整的 IMAP 响应。", "The mailbox sent an incomplete or unsupported response. Try syncing again.": "邮箱返回的数据不完整或暂不受支持，请稍后重试同步。", "Sync failed. Check the connection and available disk space, then retry.": "同步失败，请检查连接和可用磁盘空间后重试。",
  "Unsupported connection setting.": "不支持此连接设置。", "Choose Gmail, Proton Bridge or IMAP.": "请选择 Gmail、Proton Bridge 或 IMAP。", "Enter a valid IMAP username.": "请输入有效的 IMAP 用户名。", "Enter an app password or Bridge password.": "请输入应用专用密码或 Bridge 密码。", "Enter an ASCII IMAP folder name, such as INBOX.": "请输入 ASCII 字符组成的 IMAP 文件夹名，例如 INBOX。", "Enter an IMAP server hostname without a URL or path.": "请输入 IMAP 服务器主机名，不要包含网址前缀或路径。", "This provider requires its preset server address.": "此服务商需使用预设的服务器地址。", "Enter a valid IMAP port; Gmail requires port 993.": "请输入有效的 IMAP 端口；Gmail 需使用 993。", "Remember password must be true or false.": "记住密码的设置必须为是或否。",
  "Connection settings could not be loaded. Keep the state file and restore it before adding accounts.": "无法读取连接设置。请保留并恢复状态文件，再添加邮箱。", "Up to three connections are supported. Remove a connection before adding another.": "最多支持三个邮箱连接，请先断开一个再添加。", "Connection not found.": "未找到邮箱连接。", "Resume the connection before syncing.": "请先恢复连接，再开始同步。",
  "Motion": "动态效果", "View imported mail": "查看已导入邮件", "View mail": "查看邮件",
  "MailCairn — your personal email archive": "MailCairn — 你的个人邮件档案",
  "Your email archive, safely on your own computer. Search, preserve, and find what matters.": "将邮件档案保存在自己的电脑上，随时搜索、查阅和备份。",
  "Language": "语言", "Skip to archive": "跳到邮件档案", "Main navigation": "主导航", "MailCairn home": "MailCairn 首页",
  "All mail": "全部邮件", "Import history": "导入记录", "Getting started": "使用指南", "Commands": "快捷命令", "Commands (Ctrl / ⌘ K)": "快捷命令（Ctrl / ⌘ K）", "Reading room": "阅读设置", "Back up archive": "备份档案", "Light the room": "点亮书房", "Import mail": "导入邮件", "Dismiss error": "关闭错误提示", "Working on your archive…": "正在处理档案…", "View progress": "查看进度", "Opening your archive…": "正在打开档案…", "Email archive": "邮件档案", "messages preserved": "封邮件已保存",
  "Your letters,": "往来书信，", "within reach.": "随手可及。", "Import your old emails. Find them again.": "导入旧邮件，重拾每一段往来。", "Import your first file": "导入第一份邮件", "MBOX or EML files": "支持 MBOX 或 EML 文件", "Correspondence": "往来书信", "Unfold the letters": "展开书信", "Search archived mail": "搜索归档邮件", "Search mail, people, or attachment names…": "搜索邮件、联系人或附件名称…", "Filters": "筛选", "Export results": "导出结果", "From": "发件人", "To": "收件人", "Date": "日期", "Name or email": "姓名或邮箱", "On or after": "开始日期（含）", "On or before": "结束日期（含）", "Has attachments": "包含附件", "Clear filters": "清除筛选", "All search words must match. Searches include body text and attachment names, not file contents.": "所有搜索词都须匹配。搜索范围包含正文和附件名称，不包含附件内容。", "Show all mail": "显示全部邮件", "Messages": "邮件列表", "Your mail": "你的邮件", "Use ↑ / ↓ inside the message list": "在邮件列表中使用 ↑ / ↓ 切换", "Newest first": "最新在前", "No matching mail": "没有匹配的邮件", "Try fewer words or a wider date range.": "试试减少关键词，或扩大日期范围。", "Clear search and filters": "清除搜索和筛选", "Previous page": "上一页", "Next page": "下一页", "Selected email": "所选邮件", "Select a message": "选择一封邮件",
  "Added, duplicate, and skipped messages from each import.": "查看每次导入中新增、重复和未导入的邮件。", "Check archive integrity": "检查档案完整性", "A completed import accounts for recognized records in that file. It cannot prove your provider exported every email. Keep your original export and a separate backup.": "导入完成表示已处理该文件中识别出的记录，不能证明邮件服务商导出了所有邮件。请保留原始导出文件和独立备份。", "Bring your mail along.": "把邮件留在身边。", "MailCairn reads exports you already have. It never signs in to your mailbox, syncs deletions, or changes your original files.": "MailCairn 读取你已有的导出文件，不登录邮箱、不同步删除操作，也不改动原始文件。", "Export from your mail app": "从邮箱导出邮件", "For Gmail, use Google Takeout, select Mail, download the export, and unzip it. Locate the": "Gmail 用户可在 Google Takeout 中选择邮件，下载并解压导出包，然后找到", "file. Thunderbird can also export MBOX using ImportExportTools NG.": "文件。Thunderbird 也可通过 ImportExportTools NG 导出 MBOX。", "Individual messages saved as": "也支持保存为", "work too. ZIP, PST, OST, and mboxcl are not supported.": "的单封邮件。不支持 ZIP、PST、OST 和 mboxcl。", "Import and review the receipt": "导入并查看回执", "Select one or more files. MailCairn preserves message bytes and builds a search index. Import the same file again safely: byte-identical messages are stored once.": "选择一个或多个文件。MailCairn 保存邮件原始字节并建立搜索索引。可以放心重复导入：字节完全相同的邮件只保存一次。", "The default limits are": "默认上限为", "20 GiB per file": "每个文件 20 GiB", "and": "，以及", "32 MiB per message": "每封邮件 32 MiB", ". Oversized or unreadable records appear in the receipt, rather than disappearing silently.": "。超限或无法读取的记录会列在回执中，不会无提示地忽略。", "Find what you need": "找到需要的邮件", "Search subject lines, senders, recipients, body text, and attachment names. Use dates or “Has attachments” to narrow the results. Words are matched together; CJK text uses substring search.": "可搜索主题、发件人、收件人、正文和附件名称。用日期或“包含附件”缩小范围。多个词须同时匹配；中文、日文和韩文按子字符串匹配。", "Emails are displayed as plain text. Remote images, tracking pixels, scripts, and HTML layouts are not loaded. Download the original EML when you need it.": "邮件以纯文本显示，不加载远程图片、追踪像素、脚本或 HTML 排版。需要时可下载原始 EML 文件。", "Make a separate backup": "另存一份备份", "Use": "点击", "to save a consistent SQLite copy containing your mail, attachments, index, and import receipts. Keep a copy on another drive.": "，保存包含邮件、附件、索引和导入回执的一致 SQLite 副本。请在另一块磁盘上保留一份。", "Restore into a new folder with:": "使用以下命令恢复到新文件夹：", "See the included README for details.": "详情见随附的 README。", "Local, with clear limits": "本地保存，了解边界", "The archive is not encrypted. Anyone who can access your files may read it. Use your operating system’s disk encryption and protect your backups. “Check archive integrity” checks stored bytes and the search index; it does not certify a complete provider export.": "档案未加密，能访问文件的人可能读取其中内容。请启用操作系统的磁盘加密并保护备份。“检查档案完整性”检查已存字节和搜索索引，不能证明服务商导出完整。", "Your archive file": "档案文件位置", "Everything is stored in the local database below. Use the backup button while the app is running, rather than copying an active database by hand.": "所有数据保存在下方的本地数据库中。应用运行时请使用备份按钮，避免直接复制正在使用的数据库。", "Opening archive…": "正在打开档案…", "On this computer": "保存在本机", "Keyboard commands": "键盘快捷键",
  "Import your archive": "导入邮件档案", "Close import dialog": "关闭导入窗口", "Import stages": "导入步骤", "01 Choose": "01 选择", "02 Copy": "02 复制", "03 Catalogue": "03 建索引", "04 Review": "04 查看", "Choose extracted MBOX files or individual EML messages. Your files stay on this computer.": "选择解压后的 MBOX 文件或单封 EML 邮件。文件始终留在本机。", "Drop your mail files here": "将邮件文件拖到这里", "or choose them from your computer": "或从电脑中选择文件", "Choose files": "选择文件", "Choose folder": "选择文件夹", "Import progress": "导入进度", "Stop import": "停止导入", "Originals stay untouched. Exact duplicates are kept only once.": "原文件保持不变，完全相同的邮件仅保留一份。", "Import details": "导入详情", "Close receipt dialog": "关闭回执窗口", "Close light scene": "关闭光影场景", "Words travel.": "文字辗转，", "Here, they stay.": "在此安放。", "Some words": "有些文字", "are worth": "值得", "keeping.": "珍藏。", "LOCAL ARCHIVE": "本地档案", "Scene intensity": "光影强度", "Quiet desk": "静谧书桌", "Full scene": "完整光影", "Stop": "停止", "Replay light": "重播光影", "Your reading room": "你的阅读设置", "Close reading preferences": "关闭阅读设置", "Light": "明暗模式", "System": "跟随系统", "Daylight": "日光", "Lamplight": "灯下", "Accent color": "主题色", "Cedar": "雪松绿", "Blue": "墨蓝", "Umber": "赭褐", "Reading type size": "阅读字号", "Small": "小", "Standard": "标准", "Large": "大", "Message spacing": "邮件间距", "Comfortable": "舒适", "Compact": "紧凑", "Single-key shortcuts": "单键快捷操作", "Use / to search, I to import, G for mail, H for history,": "按 / 搜索、I 导入、G 查看邮件、H 查看记录，", "and ? for commands. Ctrl / ⌘ K always opens commands.": "按 ? 打开命令。Ctrl / ⌘ K 始终可用。", "Motion & light": "动效与光影", "Follows your system’s reduced-motion setting.": "遵循系统的减少动态效果设置。", "Light effects": "光影效果", "Short, local effects only": "仅播放短暂的局部效果", "Preview light ↗": "预览光影 ↗", "Some words are": "有些文字，", "worth keeping.": "值得珍藏。", "Reset to defaults": "恢复默认设置", "Saved only in this browser": "仅保存在此浏览器", "Go to…": "前往…", "Close commands": "关闭命令窗口", "Find a command": "查找命令", "Search commands…": "搜索命令…", "Move": "移动", "Open": "打开", "Close": "关闭",
  "Undated": "无日期", "Unknown date": "日期未知", "Unknown sender": "未知发件人", "No dated messages": "没有包含日期的邮件", "Searching…": "正在搜索…", "No results": "没有结果", "Search unavailable": "暂时无法搜索", "No preview text": "没有预览文本", "Select a message to read it here.": "选择一封邮件，在此阅读。", "The reading table is ready.": "邮件在此等候。", "← Back to messages": "← 返回邮件列表", "Opening message…": "正在打开邮件…", "ARCHIVED MESSAGE": "已归档邮件", "Save original": "保存原件", "Not provided": "未提供", "This message has no readable text body. Save the original to open it in a compatible mail app.": "这封邮件没有可读的文本正文。请保存原件，用兼容的邮件应用打开。", "Plain-text view · Remote images and scripts never loaded": "纯文本视图 · 不加载远程图片或脚本", "Your archive starts here.": "从这里开始归档。", "Import a mail file to create your first receipt.": "导入邮件文件，生成第一份回执。", "View receipt ↗": "查看回执 ↗", "Browse mail": "浏览邮件", "Loading receipt…": "正在加载回执…", "SOURCE FILE · SHA-256": "源文件 · SHA-256", "Download full receipt": "下载完整回执", "Browse imported mail": "浏览已导入邮件", "Details to review": "需要查看的详情", "Showing up to 200 reading notes or skipped records. The full receipt includes every recognized record and its source byte offsets.": "最多显示 200 条阅读提示或跳过记录。完整回执包含每条识别记录及其在源文件中的字节偏移量。", "Record": "记录", "Status": "状态", "What happened": "说明", "A receipt describes recognized records in this source file. It cannot prove a complete provider export or the authenticity of a message. Keep the original export.": "回执仅描述该源文件中识别出的记录，不能证明服务商导出完整，也不能证明邮件真实性。请保留原始导出文件。", "Checking stored mail and the search index…": "正在检查邮件和搜索索引…", "Accession in progress…": "正在导入档案…", "Stop check": "停止检查", "Copying to your local archive. Nothing is sent to the cloud.": "正在复制到本地档案，不会上传到云端。", "Preparing the local import…": "正在准备本地导入…", "Mail import": "邮件导入", "Existing mail import": "进行中的邮件导入", "Import complete": "导入完成", "Preparing your local file…": "正在准备本地文件…", "Stopping safely… saved messages will remain in your archive.": "正在安全停止…已保存的邮件会保留在档案中。", "Your stored archive passed its checks.": "已存档案通过检查。", "Archive check stopped.": "档案检查已停止。", "Your archive needs attention.": "档案存在需要处理的问题。", "Import receipt records are inconsistent. Keep your source exports and restore a known-good backup before relying on these counts.": "导入回执记录不一致。请保留源文件，并恢复可靠备份后再使用这些统计数据。", "Checks stored bytes and the local index only. This cannot prove your provider exported every email.": "仅检查已存字节和本地索引，不能证明服务商导出了所有邮件。", "Open your local archive.": "打开你的本地档案。", "Let’s reconnect your archive.": "重新连接邮件档案。", "Start MailCairn with python app.py, then open the complete launch URL printed in the terminal. Each app restart creates a new local session.": "运行 python app.py 启动 MailCairn，然后打开终端输出的完整启动链接。每次重启应用都会创建新的本地会话。", "Try again": "重试", "Applied for this visit · storage unavailable": "本次访问已生效 · 无法保存设置", "System reduced motion is on": "系统已开启减少动态效果", "Motion is off": "动效已关闭", "System reduced motion is on. Enjoy the still room.": "系统已开启减少动态效果，书房保持静止。", "Motion is off. Enjoy the still room.": "动效已关闭，书房保持静止。", "Playing an eight-second light study. Stop or replay anytime.": "正在播放 8 秒光影，可随时停止或重播。", "Playing a quiet four-second light study.": "正在播放 4 秒静谧光影。", "The room is still. Replay the light whenever you like.": "书房静止，随时可以重播光影。",
  "Return to the catalogue": "回到邮件目录", "Search the collection": "搜索邮件档案", "Words, people, dates, attachment names": "关键词、联系人、日期、附件名称", "Import mail to begin searching": "导入邮件后即可搜索", "Add MBOX or EML files": "添加 MBOX 或 EML 文件", "Review receipts and source files": "查看回执和源文件", "Available after the current operation": "当前操作完成后可用", "Check message bytes and the search index": "检查邮件字节和搜索索引", "Download a consistent copy of the archive": "下载档案的一致副本", "Open an interactive light study": "打开交互式光影场景", "Light, ink, typography, spacing, and motion": "明暗、色彩、字号、间距和动效", "Export formats, backups, and clear limits": "导出格式、备份和功能边界", "No command found. Try “import”, “backup”, or “reading”.": "没有找到命令。试试“导入”“备份”或“阅读”。", "Your files and import receipts.": "你的文件和导入回执。", "Bring your mail. Keep your originals.": "带来邮件，保留原件。",
  "complete": "已完成", "partial": "部分完成", "cancelled": "已停止", "running": "进行中", "failed": "失败", "interrupted": "已中断", "added": "新增", "duplicates": "重复", "duplicate": "重复", "not imported": "未导入", "skipped": "已跳过", "recognized": "已识别", "ok": "通过", "not checked": "未检查",
  "Cannot reach MailCairn. Make sure the app is still running in your terminal, then refresh this page.": "无法连接 MailCairn。请确认应用仍在终端中运行，然后刷新页面。", "MailCairn returned an unexpected response. Restart the app and open its launch URL.": "MailCairn 返回了异常响应。请重启应用并打开启动链接。", "The start date must be on or before the end date.": "开始日期不能晚于结束日期。", "Start date must be on or before end date.": "开始日期不能晚于结束日期。", "Unexpected response. Check Import history before trying again.": "收到异常响应。请先查看导入记录，再重试。", "The connection to MailCairn was lost. Check Import history before trying again.": "与 MailCairn 的连接已断开。请先查看导入记录，再重试。", "Upload stopped. If processing had already started, review Import history.": "文件复制已停止。如果处理已经开始，请查看导入记录。", "The operation failed. Review Import history and try again.": "操作失败。请查看导入记录后重试。", "Wait for the current operation to finish, or stop it first.": "请等待当前操作完成，或先停止当前操作。", "Choose an extracted MBOX or EML file. ZIP, PST, and other formats are not supported.": "请选择解压后的 MBOX 或 EML 文件。不支持 ZIP、PST 等其他格式。", "This file is empty. Choose a mail export containing messages.": "此文件为空。请选择包含邮件的导出文件。", "Wait for a successful search before exporting results.": "请等待搜索成功后再导出结果。", "There are no matching messages to export.": "没有可导出的匹配邮件。", "Preparing your MBOX download. Large exports may take a moment.": "正在准备 MBOX 下载，大量邮件可能需要一些时间。", "Preparing a consistent archive backup. Large archives may take a moment.": "正在准备档案的一致备份，较大的档案可能需要一些时间。", "Reading room preferences reset.": "阅读设置已恢复默认。", "Motion is off in your reading room or system preferences.": "阅读设置或系统设置中已关闭动效。",
  "The file is empty. Select an extracted .mbox or .eml file.": "文件为空。请选择解压后的 .mbox 或 .eml 文件。", "No standard MBOX envelope found. Unzip your export first. PST, ZIP and mboxcl files are not supported; individual messages must use .eml.": "未找到标准 MBOX 记录分隔行。请先解压导出文件。不支持 PST、ZIP 和 mboxcl；单封邮件须使用 .eml。", "Content-Length-based MBOX variants (mboxcl/mboxcl2) are not supported. Export as mboxo/mboxrd or individual EML files first.": "不支持基于 Content-Length 的 MBOX 变体（mboxcl/mboxcl2）。请先导出为 mboxo/mboxrd 或单封 EML。", "MIME nesting or part count exceeds the safety limit (30 levels / 500 parts).": "MIME 嵌套层数或分段数量超过安全上限（30 层 / 500 段）。", "No recognizable email headers; the original span was not imported.": "未识别出邮件头，原始数据片段未导入。", "Unknown charset; decoded with UTF-8 replacement": "字符集未知；已用 UTF-8 解码并替换无效字符", "HTML converted to inert text; layout and inline images omitted": "HTML 已转换为静态文本；省略了排版和内嵌图片", "Search/preview text limited to 1,000,000 characters; full original retained": "搜索和预览文本限制为 1,000,000 个字符；完整原件已保留", "Date has no timezone; UTC used for sort order": "日期未包含时区；按 UTC 排序", "Missing or invalid date; date filters exclude this message": "日期缺失或无效；日期筛选会排除此邮件", "Attachment not found.": "附件不存在。", "Not an attachment.": "这不是附件。", "Choose an extracted .mbox or .eml file.": "请选择解压后的 .mbox 或 .eml 文件。", "Stopped at a message boundary. Saved messages remain searchable. Re-import to continue.": "已在邮件边界处停止。已保存的邮件仍可搜索，重新导入即可继续。", "Some messages were not stored. Keep the source file and review the receipt.": "部分邮件未保存。请保留源文件并查看回执。", "Message not found.": "邮件不存在。", "Import receipt not found.": "导入回执不存在。", "Stored message bytes, local search index and import-receipt consistency only. This cannot prove the original export contains every email in your account.": "仅检查已存邮件字节、本地搜索索引和导入回执的一致性，不能证明原始导出包含账户中的所有邮件。",
  "Proton Mail: use the Proton Mail Export Tool to export EML files, then choose the exported folder here. JSON sidecar files are skipped. A paid Bridge subscription is not required for this workflow.": "Proton Mail 用户可用 Proton Mail Export Tool 导出 EML 文件，然后在此选择导出的文件夹。JSON 辅助文件会跳过，此流程不需要付费 Bridge 订阅。",
  "Choose a folder containing EML or MBOX files. Subfolders are included; other files are skipped and counted.": "可选择包含 EML 或 MBOX 的文件夹，包含其子文件夹；其他文件会跳过并报告数量。", "No MBOX or EML files were found in this folder.": "此文件夹中没有找到 MBOX 或 EML 文件。",
  "Cannot reach MailCairn. Open the app, then try again.": "无法连接 MailCairn。请打开应用后重试。",
  "MailCairn returned an unexpected response. Reopen your archive from the app.": "MailCairn 返回了异常响应。请从应用中重新打开档案。",
  "Choose “Open archive” in the MailCairn window, or use the link from your usual startup command.": "请在 MailCairn 窗口点击“打开档案”，或使用启动程序时显示的链接。",
  "Open your archive from MailCairn or its startup link.": "请从 MailCairn 窗口或启动链接打开档案。",
  "Open your archive from MailCairn or its startup link to continue.": "请从 MailCairn 窗口或启动链接重新打开档案后继续。",
  "This session has expired. Reopen your archive from MailCairn or its startup link.": "当前会话已失效。请从 MailCairn 窗口或启动链接重新打开档案。",
  "Mailbox disconnected. Its saved password may remain on this computer because local cleanup failed.": "邮箱已断开。由于本地清理失败，保存的密码可能仍留在这台电脑上。",
  "Use the local launch URL shown in the terminal.": "请使用终端显示的本地启动链接。",
  "Open the launch URL from the terminal to unlock this local session.": "请打开终端中的启动链接，解锁本地会话。",
  "Invalid session. Use the launch URL from the terminal.": "会话无效，请使用终端中的启动链接。",
  "Cross-origin access is not allowed.": "不允许跨源访问。", "Cross-site access is not allowed.": "不允许跨站访问。", "Cross-origin requests are not supported.": "不支持跨源请求。",
  "GET requests must not contain a body.": "GET 请求不能包含请求正文。", "Request URL is too long.": "请求链接过长。", "File not found.": "文件不存在。", "Not found.": "未找到请求的内容。",
  "This job is no longer active. Check Import history for saved receipts.": "此任务已结束，请在导入记录中查看已保存的回执。", "The archive is busy. Retry shortly.": "档案正在处理中，请稍后重试。",
  "The archive operation failed. Check available disk space and restart the app if necessary.": "档案操作失败。请检查可用磁盘空间，必要时重启应用。", "The operation failed. Check local disk space and retry.": "操作失败。请检查本地磁盘空间后重试。",
  "This action requires an empty request body.": "此操作要求请求正文为空。", "Missing local request header.": "缺少本地请求标头。",
  "An import or verification is already running. Let it finish or cancel it first.": "已有导入或检查任务正在运行，请等待完成或先停止它。", "An import or verification is already running.": "已有导入或检查任务正在运行。", "Job not found.": "任务不存在。",
  "Choose an extracted .mbox or .eml file. ZIP and PST are not supported.": "请选择解压后的 .mbox 或 .eml 文件，不支持 ZIP 和 PST。", "Chunked transfer is not supported. Select a local file.": "不支持分块传输，请选择本地文件。", "Transfer-Encoding is not supported. Select a local file.": "不支持 Transfer-Encoding，请选择本地文件。", "Invalid Content-Length header.": "Content-Length 标头无效。",
  "The selected file is empty.": "所选文件为空。", "Not enough free space for the upload and archive. Free disk space and try again.": "磁盘空间不足以复制文件并建立档案，请清理空间后重试。", "Upload interrupted; no import was started.": "文件复制中断，尚未开始导入。", "Upload is too slow; no import was started. Please retry.": "文件复制过慢，尚未开始导入，请重试。",
  "The app stopped during import. Saved messages are safe; import the file again to finish.": "应用在导入过程中停止。已保存的邮件不受影响；再次导入文件即可完成。", "Message size limit must be positive.": "邮件大小上限必须大于零。",
  "InvalidBase64PaddingDefect": "Base64 填充无效（InvalidBase64PaddingDefect）",
  "InvalidBase64CharactersDefect": "Base64 含无效字符（InvalidBase64CharactersDefect）",
  "InvalidBase64LengthDefect": "Base64 长度无效（InvalidBase64LengthDefect）",
  "MissingHeaderBodySeparatorDefect": "邮件头与正文之间缺少分隔行（MissingHeaderBodySeparatorDefect）",
  "StartBoundaryNotFoundDefect": "未找到 MIME 起始边界（StartBoundaryNotFoundDefect）",
  "CloseBoundaryNotFoundDefect": "未找到 MIME 结束边界（CloseBoundaryNotFoundDefect）",
  "NoBoundaryInMultipartDefect": "多部分邮件缺少 MIME 边界（NoBoundaryInMultipartDefect）",
  "MultipartInvariantViolationDefect": "多部分邮件结构不一致（MultipartInvariantViolationDefect）",
  "InvalidMultipartContentTransferEncodingDefect": "多部分邮件的传输编码无效（InvalidMultipartContentTransferEncodingDefect）",
  "UndecodableBytesDefect": "存在无法解码的字节（UndecodableBytesDefect）",
  "NonPrintableDefect": "邮件头含不可打印字符（NonPrintableDefect）",
  "InvalidDateDefect": "邮件头日期无效（InvalidDateDefect）",
  "InvalidHeaderDefect": "邮件头格式无效（InvalidHeaderDefect）",
  "HeaderMissingRequiredValue": "邮件头缺少必填值（HeaderMissingRequiredValue）",
  "ObsoleteHeaderDefect": "邮件头使用旧格式（ObsoleteHeaderDefect）",
  "NonASCIILocalPartDefect": "邮箱本地部分含非 ASCII 字符（NonASCIILocalPartDefect）"
};
let uiLocale = "en";
const languageKey = "mailcairn.language.v1";
const browserLocale = () => typeof navigator !== "undefined" && /^zh\b/i.test(navigator.language || "") ? "zh-CN" : "en";
try { const saved = localStorage.getItem(languageKey); uiLocale = ["en", "zh-CN"].includes(saved) ? saved : browserLocale(); } catch { uiLocale = browserLocale(); }
const uiBindings = new Map();
// These are parser-owned diagnostics, not general UI copy. Exception details
// and strings quoted inside an unknown diagnostic must remain verbatim.
const parserErrors = new Set([
  "MIME nesting or part count exceeds the safety limit (30 levels / 500 parts).",
  "No recognizable email headers; the original span was not imported."
]);
const parserWarnings = [
  "Unknown charset; decoded with UTF-8 replacement",
  "HTML converted to inert text; layout and inline images omitted",
  "Search/preview text limited to 1,000,000 characters; full original retained",
  "Date has no timezone; UTC used for sort order",
  "Missing or invalid date; date filters exclude this message",
  ...Object.keys(uiCatalogue).filter(key => key.endsWith("Defect") || key === "HeaderMissingRequiredValue")
].sort((a, b) => b.length - a.length);
function translateWarningSequence(source) {
  let remaining = source;
  const translated = [];
  while (remaining) {
    const known = parserWarnings.find(warning => remaining === warning || remaining.startsWith(warning + "; "));
    if (!known) return source;
    translated.push(uiCatalogue[known]);
    remaining = remaining.slice(known.length);
    if (remaining) remaining = remaining.slice(2);
  }
  return translated.join("；");
}
function translate(value) {
  const source = String(value ?? "");
  if (uiLocale === "en") return source;
  if (Object.hasOwn(uiCatalogue, source)) return uiCatalogue[source];
  const rules = [
    [/^Last successful sync: ([\s\S]*)$/, (_, date) => `上次成功同步：${date}`],
    [/^(.+) added · (.+) duplicates in the last successful sync$/, (_, added, duplicates) => `上次成功同步：新增 ${added} · 重复 ${duplicates}`],
    [/^File (.+) of (.+)$/, (_, index, total) => `第 ${index} / ${total} 个文件`],
    [/^(.+) files? (?:was|were) not started\.$/, (_, count) => `${count} 个文件尚未开始导入。`],
    [/^(.+) added · (.+) duplicates? · (.+) records? not imported · (.+) files? needs? review$/, (_, added, duplicates, skipped, errors) => `新增 ${added} · 重复 ${duplicates} · 未导入记录 ${skipped} · 待检查文件 ${errors}`],
    [/^(\d[\d,]*) messages?$/, (_, n) => `${n} 封邮件`],
    [/^(\d[\d,]*) attachments?$/, (_, n) => `${n} 个附件`],
    [/^(\d[\d,]*) reading notes?$/, (_, n) => `${n} 条阅读提示`],
    [/^(.+)–(.+) of (.+)$/, (_, a, b, n) => `第 ${a}–${b} 封，共 ${n} 封`],
    [/^(.+) of originals · (.+) attachments?$/, (_, size, n) => `原件 ${size} · ${n} 个附件`],
    [/^MBOX \/ EML · up to (.+) per file$/, (_, size) => `MBOX / EML · 每个文件上限 ${size}`],
    [/^This session allows (.+) per file and (.+) per message\. Oversized or unreadable records appear in the receipt, rather than disappearing silently\.$/, (_, file, mail) => `本次会话的上限为每个文件 ${file}、每封邮件 ${mail}。超限或无法读取的记录会列在回执中，不会无提示地忽略。`],
    [/^From import: ([\s\S]*)$/, (_, name) => `来自导入：${name}`],
    [/^Checking archive: (.+) of (.+) messages$/, (_, n, total) => `正在检查档案：${n} / ${total} 封邮件`],
    [/^(.+) recognized · (.+) added · (.+) duplicates · (.+) not imported$/, (_, total, added, duplicates, skipped) => `已识别 ${total} · 新增 ${added} · 重复 ${duplicates} · 未导入 ${skipped}`],
    [/^Importing ([\s\S]*) · (.+) added$/, (_, name, n) => `正在导入 ${name} · 新增 ${n}`],
    [/^Import (\w+) · (.+) added · (.+) duplicates · (.+) not imported$/, (_, status, added, duplicates, skipped) => `导入${translate(status)} · 新增 ${added} · 重复 ${duplicates} · 未导入 ${skipped}`],
    [/^This file exceeds the (.+) limit for this session\.$/, (_, n) => `此文件超过本次会话的 ${n} 上限。`],
    [/^(.+) of (.+) message hashes checked · SQLite: (.+) · Search index: (.+) · Import receipts: (.+)$/, (_, n, total, sql, search, receipts) => `已校验 ${n} / ${total} 封邮件的哈希 · SQLite：${translate(sql)} · 搜索索引：${translate(search)} · 导入回执：${translate(receipts)}`],
    [/^(.+) messages have changed bytes\. Keep the source exports and restore a known-good backup\.$/, (_, n) => `${n} 封邮件的字节发生变化。请保留源文件并恢复可靠的备份。`],
    [/^Checked (.+)$/, (_, date) => `检查时间：${date}`],
    [/^The operation failed \((\d+)\)\.$/, (_, n) => `操作失败（${n}）。`],
    [/^Import failed \((\d+)\)\.$/, (_, n) => `导入失败（${n}）。`],
    [/^File exceeds the configured (\d+) GiB upload limit\.$/, (_, n) => `文件超过设置的 ${n} GiB 复制上限。`],
    [/^Message exceeds (\d+) byte limit; raw span not stored\.$/, (_, n) => `邮件超过 ${n} 字节上限；原始片段未保存。`],
    [/^Cannot parse message: ([\s\S]*)$/, (_, detail) => `无法解析邮件：${parserErrors.has(detail) ? uiCatalogue[detail] : detail}`],
    [/^Skipped (.+) non-mail files \(including JSON sidecars\)\. Selected (.+) mail files\.$/, (_, skipped, selected) => `已跳过 ${skipped} 个非邮件文件（含 JSON 辅助文件），已选择 ${selected} 个邮件文件。`]
  ];
  for (const [pattern, render] of rules) if (pattern.test(source)) return source.replace(pattern, render);
  // Only a complete sequence of known parser warnings is localized. Searching
  // inside arbitrary text could rewrite filenames or quoted diagnostic tokens.
  return translateWarningSequence(source);
}
function uiText(node, value) {
  if (!node) return node;
  const render = typeof value === "function" ? value : () => value;
  uiBindings.set(node, render);
  const text = String(render() ?? "");
  if (node.textContent !== text) node.textContent = text;
  return node;
}
function uiCopy(node, value) { return uiText(node, () => translate(typeof value === "function" ? value() : value)); }
const uiAttributes = [];
function pruneUIBindings() {
  for (const node of uiBindings.keys()) if (node.isConnected === false) uiBindings.delete(node);
  for (let index = uiAttributes.length - 1; index >= 0; index--) if (uiAttributes[index].node.isConnected === false) uiAttributes.splice(index, 1);
}
function bindStaticCopy() {
  // Called once, before mail is fetched. Keep markup, icons and controls intact.
  const visit = (node) => {
    if (node.nodeType === 3) {
      const original = node.textContent, key = original.trim();
      if (Object.hasOwn(uiCatalogue, key) || /^0 messages$/.test(key) || /^MBOX \/ EML ·/.test(key)) uiText(node, () => original.replace(key, translate(key)));
      return;
    }
    if (["SCRIPT", "STYLE"].includes(node.tagName)) return;
    for (const attr of ["aria-label", "title", "placeholder"]) {
      const source = node.getAttribute?.(attr);
      if (source && Object.hasOwn(uiCatalogue, source)) {
        const render = () => node.setAttribute(attr, translate(source));
        uiAttributes.push({ node, render }); render();
      }
    }
    for (const child of [...(node.childNodes || [])]) visit(child);
  };
  visit(document.documentElement);
  const meta = document.querySelector('meta[name="description"]');
  if (meta) { const source = meta.content; uiAttributes.push({ node: meta, render: () => { meta.content = translate(source); } }); }
}
function changeLanguage(locale, save = true) {
  if (!["en", "zh-CN"].includes(locale)) return;
  uiLocale = locale;
  document.documentElement.lang = locale;
  if (save) { try { localStorage.setItem(languageKey, locale); } catch { /* Current visit remains usable. */ } }
  pruneUIBindings();
  for (const [node, render] of uiBindings) {
    if (node.isConnected === false) { uiBindings.delete(node); continue; }
    const text = String(render() ?? "");
    if (node.textContent !== text) node.textContent = text;
  }
  for (const binding of uiAttributes) if (binding.node.isConnected !== false) binding.render();
  document.querySelectorAll("[data-language]").forEach(button => { button.setAttribute("aria-pressed", String(button.dataset.language === locale)); });
  if (typeof renderCommands === "function" && document.querySelector("#command-dialog")?.open) renderCommands();
  if (typeof positionNavMarker === "function") positionNavMarker();
}
function bindLanguage() {
  bindStaticCopy();
  document.querySelectorAll("[data-language]").forEach(button => button.addEventListener("click", () => changeLanguage(button.dataset.language)));
  window.addEventListener("storage", event => { if (event.key === languageKey && ["en", "zh-CN"].includes(event.newValue)) changeLanguage(event.newValue, false); });
  changeLanguage(uiLocale, false);
}
