# Connect a mailbox / 连接邮箱

Updated **2026-11-09**. These instructions accompany **Getting started → Connect a mailbox** inside MailCairn, also reached through **How to connect your mailbox** in the connection form. Provider conditions were checked against the official links below; real Gmail or Proton automatic synchronization has not been tested with an external account. See [executed checks](test-results.md).

提供商资料核查于 **2026-11-09**，对应应用内**使用指南 → 连接邮箱**，也可从连接表单的设置帮助入口打开。之后真实 Gmail 首次归档了 120 封，但新邮件自动轮询遇到尚未解决的 TLS 连接故障；付费 Proton Bridge 自动同步未实测。详见注明日期的[测试记录](test-results.md)。

## Before you start / 开始之前

Choose **Connect mailbox** and your provider. MailCairn first saves mail already in your **Inbox**, then checks for new mail about **every five minutes while the application runs**. Keep its desktop control window open. Closing only the reading tab is fine; quitting MailCairn or turning off the computer stops checks. Sent mail and other folders are not included. A message moved or deleted before the next check can be missed.

点击**连接邮箱**并选择服务商。MailCairn 先保存**收件箱**已有邮件，之后在**应用运行时约每 5 分钟**检查新邮件。保持桌面控制窗口打开；可以关闭阅读网页，但退出应用或关机会停止检查。不包含已发送或其他文件夹，检查前移走或删除的邮件可能遗漏。

MailCairn does not send mail, mark source messages as read, move them or delete them. Once saved, a local copy remains even if the source later deletes it.

MailCairn 不发信，不把源邮件标为已读，也不移动或删除源邮件；保存后的本地副本不会随源端删除。

## Gmail

1. In your Google account, enable **2-Step Verification** if needed. Open Google's [App passwords](https://myaccount.google.com/apppasswords) page and create an app password for MailCairn. This is a separate password Google generates for an application. [Google's instructions](https://support.google.com/accounts/answer/185833).
2. In MailCairn, choose **Gmail**. Enter your complete Gmail address and the generated **App password**. Do not enter your usual Google password. Gmail's server settings are filled in for you.
3. Choose whether to remember the password on this computer, then start the connection. Open **Mailboxes** to check its result.

1. 在 Google 账号中开启**两步验证**，打开 [应用专用密码](https://myaccount.google.com/apppasswords) 页面，为 MailCairn 创建一个密码。这是 Google 为应用另外生成的密码，详见[官方说明](https://support.google.com/accounts/answer/185833)。
2. 在 MailCairn 选择 **Gmail**，填写完整邮箱地址和生成的**应用专用密码**，不要填平常登录 Google 的密码。服务器参数已自动设置。
3. 选择是否在本机记住密码，开始连接，然后在**邮箱连接**查看结果。

**Cannot find App passwords?** Some work/school accounts, accounts using only security keys for verification, or Advanced Protection accounts cannot create them. Follow Google's account-specific guidance; this release has no **Sign in with Google** alternative. An existing browser login does not connect MailCairn. File import remains available, but it does not automatically collect new mail.

**找不到应用专用密码？** 某些工作／学校账号、仅使用安全密钥验证的账号或高级保护账号无法创建。请按 Google 对该账号的说明处理；本版没有“使用 Google 登录”的替代入口，已经登录浏览器也不代表已连接 MailCairn。仍可导入文件，但该流程不会自动收取新邮件。

## Proton Mail

**This connection requires a paid Proton Mail plan and Proton Mail Bridge. A Free account cannot use this connector.** Free accounts can use Proton's export tool for manual import; this is not automatic synchronization. Unofficial alternatives exist, but are not integrated or verified here; see [research and alternatives](mail-sync-research.md).

**此连接方式需要付费 Proton Mail 套餐及 Proton Mail Bridge，免费账号无法使用本连接器。** 免费账号仍可使用官方导出工具后手动导入，但这不是自动同步。非官方替代方案存在，本版尚未集成或验证，见[研究与替代方案](mail-sync-research.md)。

1. Install [Proton Mail Bridge](https://proton.me/mail/bridge) on this computer. Sign into your Proton account **inside Bridge**, then open its mailbox/client settings. [Official setup guide](https://proton.me/support/protonmail-bridge-clients-windows-thunderbird).
2. In MailCairn choose **Proton Mail**. Copy the **username and password displayed by Bridge** into the matching fields. Do not use your normal Proton password or a browser session.
3. MailCairn uses the local computer automatically. Its default incoming-mail port is **1143**. If Bridge shows a different **IMAP port**, enter that number in the advanced settings. Use Bridge's **STARTTLS** incoming-mail configuration; an SMTP port is for sending and will not work here.
4. Start the connection and keep **both Bridge and MailCairn running**. Check **Mailboxes** for a successful check or an error.

1. 在本机安装 [Proton Mail Bridge](https://proton.me/mail/bridge)，**在 Bridge 内**登录 Proton，打开其邮箱／邮件客户端设置。参见[官方设置指南](https://proton.me/support/protonmail-bridge-clients-windows-thunderbird)。
2. 在 MailCairn 选择 **Proton Mail**，把 **Bridge 显示的用户名与密码**复制到对应字段；不要填 Proton 常用密码，也不能复用网页登录。
3. 本机地址已自动设置，默认收信端口为 **1143**。若 Bridge 的 **IMAP 端口**不同，在高级设置填入该数字。使用 Bridge 的 **STARTTLS** 收信配置；SMTP 是发信端口，不能用于这里。
4. 开始连接，并保持 **Bridge 和 MailCairn 都在运行**，在**邮箱连接**查看成功检查或错误结果。

## Other email providers / 其他邮箱

Choose **Other email** and find your provider's **incoming-mail settings for IMAP with SSL/TLS**. Copy them from the provider's help page; they cannot reliably be guessed from your email address. A provider that only permits its own sign-in flow may not work with this connector.

选择**其他邮箱**，从提供商帮助页查找 **IMAP 收信设置，安全方式为 SSL/TLS**，不要根据邮箱地址猜服务器。若提供商只允许它自己的授权登录流程，本连接器可能不适用。

| Field / 字段 | What to enter / 填写什么 |
| --- | --- |
| Incoming mail server / 收信服务器 | The provider's hostname, for example `imap.example.com`; no `https://` or web page path. / 提供商给出的主机名，不加 `https://` 或网页路径。 |
| Username / 用户名 | Usually your full email address; follow the provider's instructions if different. / 通常是完整邮箱地址，以提供商说明为准。 |
| Password or app password / 密码或应用专用密码 | The credential the provider allows for mail clients; this may be a separate app password. / 提供商允许邮件客户端使用的密码，可能需要另建应用专用密码。 |
| Port, under advanced settings / 高级设置中的端口 | Leave **993** unless the provider specifies another **SSL/TLS** incoming-mail port. Plaintext or STARTTLS-only servers are not supported by this Other email option. / 默认保留 **993**；只有官方指定其他 **SSL/TLS** 收信端口时才改。此选项不支持明文或仅 STARTTLS 的服务器。 |

## Check the result / 确认连接结果

Open **Mailboxes**. A newly added account may still be waiting to connect; adding it is not proof that its password worked. Wait for the first completed check and inspect its saved-mail count or error. An empty Inbox can successfully save zero messages. Use **Sync now** after a new message arrives; open the mail list to read what was saved. Initial catch-up can take longer for a large Inbox.

打开**邮箱连接**。新添加的账号可能还在等待连接，添加成功不代表密码已验证。等待首次检查完成，查看保存数量或错误；空收件箱成功检查后也可能是零封。新邮件到达后可点**立即同步**，再到邮件列表阅读。首次收件箱较大时可能需要更久。

- **Password rejected:** check that you used the right kind of password. For Gmail, create a replacement app password if revoked; for Proton, copy the current Bridge password. Use **Reconnect** to enter it again. / **密码被拒绝：** 检查密码类型；Gmail 应用密码被撤销时重新生成，Proton 复制当前 Bridge 密码，再用**重新连接**填写。
- **Cannot reach the mailbox:** check internet access; for Proton, also check that Bridge is running and its incoming port matches. / **无法连接：** 检查网络；Proton 还需确认 Bridge 已运行、收信端口一致。
- **A message cannot be saved:** read the connection error. A message above the size limit or a parsing failure stops progress before that item; it is not silently skipped. / **邮件无法保存：** 查看连接错误；超限或无法解析的邮件会停止该处进度，不会静默跳过。
- **Pause / Resume / Disconnect:** pause stops checks, resume restarts them, and disconnect removes the connection without deleting archived mail. / **暂停／继续同步／断开连接：** 暂停停止检查，继续恢复；断开移除连接，保留已归档邮件。

## Passwords and backups / 密码与备份

**Remember on this computer** is available when Windows account protection works. Otherwise the password lasts only until MailCairn exits; reconnect after restarting. A disabled remember option is not a mailbox error. Password protection does not encrypt the mail archive or protect it from software running as your Windows user.

Windows 账号保护可用时，可选择**在此电脑记住**。否则密码只保留到 MailCairn 退出，重启后需重新连接；记住选项不可用不代表邮箱出错。密码保护不等于邮件档案加密，也不能防止以同一 Windows 用户运行的软件读取数据。

**Back up archive** saves mail, attachments and archive records. It does **not** include connected-account settings, passwords or sync progress. Restore into a new archive, then reconnect the mailbox. Treat archive files and backups as private mail; keep a separate copy on a protected drive. For manual exports, see the [provider import guide](provider-import-guide.md).

**备份档案**保存邮件、附件和归档记录，**不包含**已连接账号的设置、密码或同步进度。恢复到新档案后重新连接邮箱。档案和备份包含私人邮件，请在受保护的另一块存储上另存副本。手动导出流程见[提供商导入指南](provider-import-guide.md)。
