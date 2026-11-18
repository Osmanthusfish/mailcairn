#!/usr/bin/env node
// Behavioral checks using the shared DOM shim. No real mailbox data is used.
import assert from "node:assert/strict";
import { harness, response, deferred, emptyStats } from "./check_frontend.mjs";

let passed = 0;
async function check(name, fn) { await fn(); console.log(`PASS ${name}`); passed++; }

await check("saved language wins, invalid preferences fall back, and blocked storage stays usable", () => {
  const saved = harness({ language: "zh-CN", storage: { "mailcairn.language.v1": "en" } });
  assert.equal(saved.run("uiLocale"), "en");
  const fallback = harness({ language: "zh-TW", storage: { "mailcairn.language.v1": "invalid" } });
  assert.equal(fallback.run("uiLocale"), "zh-CN");
  const blocked = harness({ language: "zh-CN", storageFailure: true });
  blocked.run("bindLanguage(); changeLanguage('en'); changeLanguage('zh-CN')");
  assert.equal(blocked.document.documentElement.lang, "zh-CN");
  assert.equal(blocked.run("translate('Import mail')"), "导入邮件");
  blocked.run("changeLanguage('unsupported')");
  assert.equal(blocked.run("uiLocale"), "zh-CN");
});

await check("static controls translate in place without losing listeners or user inputs", () => {
  const h = harness(); h.run("bindLanguage()");
  const button = h.nodes.get("#choose-files"), input = h.nodes.get("#search-input");
  assert.ok(button, "Import button must exist");
  let clicked = 0; button.addEventListener("click", () => clicked++);
  input.value = "Import mail 中文 <tag>";
  input.focus();
  h.run("changeLanguage('zh-CN')");
  assert.match(button.textContent, /选择文件/);
  assert.equal(input.getAttribute("placeholder"), "搜索邮件、联系人或附件名称…");
  assert.equal(input.value, "Import mail 中文 <tag>");
  assert.equal(h.document.activeElement, input);
  button.click(); assert.equal(clicked, 1);
  h.run("changeLanguage('en')");
  assert.match(button.textContent, /Choose files/);
  assert.equal(h.storage.get("mailcairn.language.v1"), "en");
});

await check("segmented language buttons expose selection and preserve working state", () => {
  const h = harness(); h.run("bindLanguage()");
  const choices = h.created.filter(node => node.dataset.language);
  const groups = h.created.filter(node => node.classList.contains("language-control"));
  assert.ok(groups.length >= 1);
  for (const group of groups) {
    const pair = choices.filter(node => node.parentNode === group);
    assert.deepEqual(pair.map(node => node.dataset.language).sort(), ["en", "zh-CN"], "Every language group offers exactly two choices");
  }
  const english = choices.find(node => node.dataset.language === "en");
  const chinese = choices.find(node => node.dataset.language === "zh-CN");
  assert.equal(english.tagName, "BUTTON"); assert.equal(chinese.tagName, "BUTTON");
  assert.equal(english.getAttribute("aria-pressed"), "true");
  assert.equal(chinese.getAttribute("aria-pressed"), "false");
  h.run("state.selected = 71; state.offset = 50; state.busy = true");
  h.nodes.get("#search-input").value = "Import mail";
  chinese.click();
  assert.equal(h.run("uiLocale"), "zh-CN");
  assert.equal(chinese.getAttribute("aria-pressed"), "true");
  assert.equal(english.getAttribute("aria-pressed"), "false");
  for (const choice of choices) assert.equal(choice.getAttribute("aria-pressed"), String(choice.dataset.language === "zh-CN"), "Toolbar and modal choices stay synchronized");
  assert.equal(h.run("state.selected"), 71);
  assert.equal(h.run("state.offset"), 50);
  assert.equal(h.run("state.busy"), true);
  assert.equal(h.nodes.get("#search-input").value, "Import mail");
  english.click();
  assert.equal(h.run("uiLocale"), "en");
  assert.equal(h.storage.get("mailcairn.language.v1"), "en");
  assert.equal(english.getAttribute("aria-pressed"), "true");
});

await check("cross-tab language changes update display without overwriting storage", () => {
  const h = harness(); h.run("bindLanguage()");
  h.storage.set("mailcairn.language.v1", "en");
  h.emit(h.context.window, "storage", { key: "mailcairn.language.v1", newValue: "zh-CN" });
  assert.equal(h.run("uiLocale"), "zh-CN");
  assert.equal(h.storage.get("mailcairn.language.v1"), "en");
  h.emit(h.context.window, "storage", { key: "mailcairn.language.v1", newValue: null });
  assert.equal(h.run("uiLocale"), "zh-CN");
});

await check("UI-like private subject, sender, body, labels and attachment names never translate", async () => {
  const h = harness(); h.run("bindLanguage()");
  const message = { id: 7, subject: "Import mail", sender: "Unknown sender", recipients: "Not provided", date_header: "Unknown date", date_day: "2026-11-09", body: "Import mail", labels: "ARCHIVED MESSAGE", attachments: [{ index: 1, name: "Import mail", size: 10, type: "text/plain" }], warnings: [] };
  h.context.fetch = async () => response(message);
  h.context.fixture = message;
  h.run("state.result = {messages: [fixture], total: 1, offset: 0, limit: 50}; renderList()");
  await h.run("readMessage(7)");
  const reader = h.nodes.get("#reader"), body = reader.querySelector(".reader-body");
  const before = JSON.stringify(h.run("state.result"));
  h.nodes.get("#search-input").value = "Import mail";
  const chosen = h.run("state.selected");
  h.run("changeLanguage('zh-CN')");
  assert.equal(reader.children.find(node => node.tagName === "HEADER").children.find(node => node.tagName === "H2").textContent, "Import mail");
  assert.equal(body.textContent, "Import mail");
  assert.equal(reader.querySelector(".sender-value").textContent, "Unknown sender");
  assert.equal(reader.querySelector(".mail-label").textContent, "ARCHIVED MESSAGE");
  assert.match(reader.querySelector(".attachment-link").textContent, /^Import mail/);
  assert.match(reader.textContent, /保存原件/);
  assert.equal(h.run("state.selected"), chosen);
  assert.equal(JSON.stringify(h.run("state.result")), before);
  assert.equal(h.nodes.get("#search-input").value, "Import mail");
  h.run("changeLanguage('en')");
  assert.equal(body.textContent, "Import mail");
  assert.match(reader.textContent, /Save original/);
});

await check("literal markup in mail stays inert after language switching", async () => {
  const h = harness(); h.run("bindLanguage()");
  const dangerous = '<img src="https://tracking.invalid/never" onerror="alert(1)">导入邮件';
  const before = h.created.filter(node => ["IMG", "IFRAME", "SCRIPT"].includes(node.tagName)).length;
  h.context.fetch = async () => response({ id: 8, subject: dangerous, body: dangerous, attachments: [], warnings: [] });
  await h.run("readMessage(8)");
  h.run("changeLanguage('zh-CN'); changeLanguage('en')");
  assert.equal(h.nodes.get("#reader").querySelector(".reader-body").textContent, dangerous);
  assert.equal(h.created.filter(node => ["IMG", "IFRAME", "SCRIPT"].includes(node.tagName)).length, before);
});

await check("a pending search survives a language change and renders in the new locale", async () => {
  const h = harness(), pending = deferred(); h.run("bindLanguage(); state.stats = {messages: 1}");
  h.context.fetch = () => pending.promise;
  h.nodes.get("#search-input").value = "original query";
  const searching = h.run("search()");
  const serial = h.run("state.searchSerial");
  h.run("changeLanguage('zh-CN')");
  assert.equal(h.run("state.searchSerial"), serial);
  pending.resolve(response({ total: 1, messages: [{ id: 8, subject: "Import mail", sender: "Sender", snippet: "Search unavailable" }], offset: 0, limit: 50 }));
  await searching;
  assert.equal(h.nodes.get("#search-input").value, "original query");
  assert.equal(h.nodes.get("#results-label").textContent, "1 封邮件");
  assert.match(h.nodes.get("#message-list").textContent, /Import mail/);
  assert.match(h.nodes.get("#message-list").textContent, /Search unavailable/);
});

await check("known recoverable errors translate while unknown diagnostics remain visible", async () => {
  const h = harness(); h.run("bindLanguage(); setError('The start date must be on or before the end date.'); changeLanguage('zh-CN')");
  assert.equal(h.nodes.get("#global-error-text").textContent, "开始日期不能晚于结束日期。");
  h.run("setError('Synthetic diagnostic E123: untouched-token')");
  assert.match(h.nodes.get("#global-error-text").textContent, /E123: untouched-token/);
  h.context.fetch = async () => { throw new Error("offline"); };
  h.run("state.stats = {messages: 1}");
  await h.run("search()");
  assert.equal(h.run("state.searchReady"), false);
  assert.match(h.nodes.get("#global-error-text").textContent, /无法连接 MailCairn/);
});

await check("language switching preserves live import state, filename and eventual receipt", async () => {
  const h = harness(), pending = deferred(); h.run("bindLanguage()");
  h.context.pendingUpload = pending.promise;
  h.context.fakeStats = emptyStats;
  h.run("upload = async () => pendingUpload; watchJob = async () => ({id: 1, status: 'complete', added: 1, duplicates: 0, skipped: 0}); refreshStats = async () => { state.stats = fakeStats; }; search = async () => {};");
  h.context.files = [{ name: "Import mail.eml", size: 25 }];
  const importing = h.run("startImport(files)");
  assert.equal(h.run("state.busy"), true);
  const file = h.run("state.currentFile");
  h.run("changeLanguage('zh-CN')");
  assert.equal(h.run("state.currentFile"), file);
  assert.equal(h.run("state.busy"), true);
  assert.equal(h.nodes.get("#import-filename").textContent, "Import mail.eml");
  assert.match(h.nodes.get("#import-stage").textContent, /正在准备本地文件/);
  pending.resolve({ job_id: "synthetic" }); await importing;
  assert.equal(h.run("state.busy"), false);
  assert.match(h.nodes.get("#import-outcomes").textContent, /Import mail.eml/);
  assert.match(h.nodes.get("#import-outcomes").textContent, /新增 1/);
  h.run("changeLanguage('en')");
  assert.match(h.nodes.get("#import-outcomes").textContent, /1 added/);
});

await check("folder import selects nested mail, counts sidecars and preserves summary across languages", async () => {
  const h = harness(); h.run("bindLanguage()");
  assert.equal(h.run("typeof startFolderImport"), "function", "Folder workflow must be present");
  h.context.files = [
    {name: "a.EML", size: 20, webkitRelativePath: "export/sub/a.EML"},
    {name: "b.mbox", size: 20, webkitRelativePath: "export/b.mbox"},
    {name: "a.json", size: 20, webkitRelativePath: "export/sub/a.json"},
    {name: "note.txt", size: 20, webkitRelativePath: "export/note.txt"}
  ];
  h.run("startImport = async files => { globalThis.acceptedFiles = files; }");
  await h.run("startFolderImport(files)");
  assert.deepEqual(Array.from(h.context.acceptedFiles, file => file.name), ["a.EML", "b.mbox"]);
  const summary = h.nodes.get("#folder-summary"); assert.ok(summary, "Folder summary must remain inspectable");
  assert.match(summary.textContent, /2 non-mail files/);
  h.run("changeLanguage('zh-CN')");
  assert.match(summary.textContent, /跳过 2/); assert.match(summary.textContent, /选择 2/);
  h.run("changeLanguage('en')");
  assert.match(summary.textContent, /Selected 2 mail files/);
  h.context.files = [{name: "only.json", size: 1}];
  h.context.acceptedFiles = null;
  await h.run("startFolderImport(files)");
  assert.equal(h.context.acceptedFiles, null, "Metadata-only folders must not start an upload");
  assert.match(h.nodes.get("#global-error-text").textContent + summary.textContent + h.nodes.get("#toast").textContent, /No MBOX or EML/);
});

await check("folder summary survives actual batch cleanup and rejected empty mail remains visible", async () => {
  const h = harness(); h.run("bindLanguage(); refreshStats = async () => {}; search = async () => {};");
  h.context.files = [{name: "empty.eml", size: 0}, {name: "metadata.json", size: 10}];
  await h.run("startFolderImport(files)");
  const summary = h.nodes.get("#folder-summary");
  assert.equal(summary.hidden, false);
  assert.match(summary.textContent, /Skipped 1 non-mail files/);
  assert.match(h.nodes.get("#import-outcomes").textContent, /empty.eml/);
  assert.match(h.nodes.get("#import-outcomes").textContent, /This file is empty/);
  assert.equal(h.run("state.busy"), false);
  h.run("changeLanguage('zh-CN')");
  assert.match(summary.textContent, /跳过 1/);
  assert.match(h.nodes.get("#import-outcomes").textContent, /此文件为空/);
  await h.run("startImport([{name: 'other.eml', size: 0}])");
  assert.equal(summary.hidden, true, "A new ordinary file import should hide the old folder summary");
});

await check("receipt language changes preserve checksum, download links and action listeners", async () => {
  const h = harness(); h.run("bindLanguage()");
  const receipt = { id: 19, name: "Import complete", size: 1234, started: "2026-11-09T04:00:00Z", status: "complete", total: 2, added: 1, duplicates: 1, skipped: 0, sha256: "a1".repeat(32), issues: [{ ordinal: 2, status: "duplicate", reason: "" }] };
  h.context.fetch = async () => response(receipt);
  await h.run("showReceipt(19)");
  const content = h.nodes.get("#receipt-content");
  const checksum = content.querySelector(".receipt-checksum");
  const code = checksum.children.find(node => node.tagName === "CODE");
  const actions = content.querySelector(".receipt-actions"), [download, browse] = actions.children;
  const originalChildren = [...checksum.children];
  h.run("browseImport = (id, name) => { globalThis.browsed = {id, name}; }");
  for (const locale of ["zh-CN", "en", "zh-CN"]) {
    h.run(`changeLanguage('${locale}')`);
    assert.deepEqual(checksum.children, originalChildren, "Relabeling must retain the checksum element");
    assert.equal(code.textContent, receipt.sha256);
    assert.equal(content.querySelector(".receipt-name").textContent, receipt.name, "Filename matching UI copy is private data");
    assert.equal(download.href, "/api/imports/19/receipt");
    assert.equal(download.getAttribute("download"), "");
    assert.ok(download.children.some(node => node.tagName === "SVG"), "Download icon must survive language updates");
    assert.match(download.textContent, locale === "en" ? /Download full receipt/ : /下载完整回执/);
  }
  browse.click();
  assert.equal(h.context.browsed.id, receipt.id);
  assert.equal(h.context.browsed.name, receipt.name);
});

await check("command rows retain children and commands work after switching languages", () => {
  const h = harness(); h.run("bindLanguage(); state.stats = {messages: 2}; renderCommands()");
  const list = h.nodes.get("#command-results"), first = list.children[0];
  const children = [...first.children];
  const icon = children.find(node => node.tagName === "SVG");
  const copy = children.find(node => node.tagName === "SPAN");
  for (const locale of ["zh-CN", "en"]) {
    h.run(`changeLanguage('${locale}')`);
    assert.deepEqual(first.children, children, "An empty action label must not erase row children");
    assert.equal(first.children.find(node => node.tagName === "SVG"), icon);
    assert.equal(copy.children.length, 2, "Command title and detail must both remain");
    assert.match(copy.textContent, locale === "en" ? /All mail/ : /全部邮件/);
    assert.equal(first.children.find(node => node.tagName === "KBD").textContent, "G");
  }
  const search = h.nodes.get("#command-search");
  search.value = "备份档案";
  h.nodes.get("#command-dialog").showModal();
  h.run("changeLanguage('zh-CN')");
  assert.equal(search.value, "备份档案");
  assert.equal(list.children.length, 1);
  const backup = list.children[0];
  assert.match(backup.textContent, /备份档案/);
  assert.ok(backup.children.some(node => node.tagName === "SVG"));
  let downloaded = 0;
  h.document.querySelector(".backup-link").addEventListener("click", () => downloaded++);
  backup.click();
  assert.equal(downloaded, 1, "Translated command must retain its actual action");
  assert.equal(h.nodes.get("#command-dialog").open, false);
});

await check("filename and filter text resembling translation templates stays exact", async () => {
  const h = harness(); h.run("bindLanguage()");
  const names = ["Import complete", "From import: All mail", "Importing private · 99 added", "The operation failed (404).eml"];
  const runs = names.map((name, index) => ({ id: index + 1, name, size: 40, started: "2026-11-09T01:00:00Z", status: "complete", added: 1, duplicates: 0, skipped: 0 }));
  h.context.runs = runs;
  h.run("state.stats = {messages: 4, imports: runs}; renderHistory(); for (const run of runs) appendOutcome(run, run.name); search = async () => {}; refreshStats = async () => {};");
  const historyNames = h.nodes.get("#import-history").children.map(card => card.children[0].children[0].children[1].children[0]);
  const outcomeNames = h.nodes.get("#import-outcomes").children.map(card => card.children[0]);
  await h.run("browseImport(runs[1].id, runs[1].name)");
  const inputValues = new Map([["#search-input", "From import: Import complete"], ["#filter-sender", "Unknown sender"], ["#filter-after", "2026-01-01"], ["#filter-before", "2026-11-09"]]);
  for (const [id, value] of inputValues) h.nodes.get(id).value = value;
  h.nodes.get("#filter-attachments").checked = true;
  h.run("importProgress(runs[2].name, 'Preparing your local file…', 37)");
  const filterBefore = h.run("filters().toString()"), importId = h.run("state.importId");
  for (const locale of ["zh-CN", "en"]) {
    h.run(`changeLanguage('${locale}')`);
    assert.deepEqual(historyNames.map(node => node.textContent), names);
    assert.deepEqual(outcomeNames.map(node => node.textContent), names);
    assert.equal(h.nodes.get("#import-filename").textContent, names[2]);
    assert.equal(h.nodes.get("#source-filter-text").textContent, (locale === "en" ? "From import: " : "来自导入：") + names[1]);
    for (const [id, value] of inputValues) assert.equal(h.nodes.get(id).value, value);
    assert.equal(h.run("filters().toString()"), filterBefore);
    assert.equal(h.run("state.importId"), importId);
  }
});

await check("diagnostic templates translate their explanation without interpreting opaque details", () => {
  const h = harness(); h.run("bindLanguage()");
  const detail = 'E123: C:\\Synthetic\\Import complete.eml <raw-token> "From import: secret"';
  h.context.detail = detail;
  h.run("setError('Cannot parse message: ' + detail); changeLanguage('zh-CN')");
  assert.equal(h.nodes.get("#global-error-text").textContent, "无法解析邮件：" + detail);
  h.run("changeLanguage('en')");
  assert.equal(h.nodes.get("#global-error-text").textContent, "Cannot parse message: " + detail);
  h.run("setError(detail); changeLanguage('zh-CN')");
  assert.equal(h.nodes.get("#global-error-text").textContent, detail);
  for (const opaque of ["Import complete", "From import: private", "Missing or invalid date; date filters exclude this message"]) {
    h.context.opaque = opaque;
    h.run("setError('Cannot parse message: ' + opaque)");
    assert.equal(h.nodes.get("#global-error-text").textContent, "无法解析邮件：" + opaque, "Opaque exception detail must not be treated as a second UI message");
  }
  const mixed = "E123 opaque token: Missing or invalid date; date filters exclude this message";
  h.context.mixed = mixed;
  h.run("setError(mixed)");
  assert.equal(h.nodes.get("#global-error-text").textContent, mixed, "Known phrases embedded in unknown diagnostics must stay verbatim");
  h.run("setError('Cannot parse message: No recognizable email headers; the original span was not imported.')");
  assert.equal(h.nodes.get("#global-error-text").textContent, "无法解析邮件：未识别出邮件头，原始数据片段未导入。");
  const warnings = "Unknown charset; decoded with UTF-8 replacement; Missing or invalid date; date filters exclude this message; InvalidBase64PaddingDefect";
  h.context.warnings = warnings;
  const localized = h.run("translate(warnings)");
  assert.match(localized, /字符集未知/);
  assert.match(localized, /日期缺失或无效/);
  assert.match(localized, /Base64 填充无效/);
  assert.equal(h.run("translate(warnings + '; Opaque warning token')"), warnings + "; Opaque warning token", "Unknown composite diagnostics must remain intact");
});

await check("credential rollback failures retain actionable bilingual warnings", () => {
  const h=harness(); h.run('bindLanguage()');
  for (const [english,chinese] of [
    ['Connection settings could not be saved and the previous saved password could not be restored. The saved password may have changed. Reconnect this account before restarting the app.','连接设置未能保存，原先保存的密码也未能恢复。本机保存的密码可能已改变，请在重启应用前重新连接此邮箱。'],
    ['The connection was not added because settings could not be saved. Its saved password may remain on this computer because local cleanup failed. Check disk space and permissions before trying again.','连接设置未能保存，邮箱未添加成功。由于本机清理失败，密码可能仍保存在此电脑上。请检查磁盘空间和文件权限后再试。']
  ]) {
    h.context.failure=english;
    h.run("setError(failure); changeLanguage('zh-CN')");
    assert.equal(h.nodes.get('#global-error-text').textContent,chinese);
    h.run("changeLanguage('en')");
    assert.equal(h.nodes.get('#global-error-text').textContent,english);
  }
});

await check("0/1/2 archive counts, attachment names and partial-import outcomes retain grammar and bilingual identity", async () => {
  for(const n of [0,1,2]){
    const h=harness();h.run('bindLanguage()');
    h.context.fetch=async()=>response({...emptyStats,messages:n,attachments:n,raw_bytes:128});
    await h.run('refreshStats()');
    h.context.sampleCount=n;
    h.run('state.result={messages:[{id:1,sender:"Example",subject:"Literal 1 attachments",attachment_count:sampleCount}]}; renderList(); state.importReview={runs:[{added:1,duplicates:sampleCount,skipped:sampleCount,status:"complete"}],errors:sampleCount,remaining:sampleCount}; renderImportReview()');
    const label=h.nodes.get('#summary-label'),size=h.nodes.get('#summary-size'),review=h.nodes.get('#import-review-summary');
    const englishLabel=n===1?'message preserved':'messages preserved';
    assert.equal(label.textContent,englishLabel);assert.match(size.textContent,new RegExp(n+' attachment'+(n===1?'':'s')+'$'));
    assert.match(review.textContent,new RegExp(n+' '+(n===1?'file needs':'files need')+' review'));
    if(n===1){assert.match(review.textContent,/1 duplicate · 1 record not imported/);assert.match(review.textContent,/1 file was not started\./);}
    const clips=h.created.filter(node=>node.getAttribute('aria-label')===n+' '+(n===1?'attachment':'attachments'));
    if(n)assert.equal(clips.length,1);
    h.run("changeLanguage('zh-CN')");assert.equal(label.textContent,'封邮件已保存');assert.match(size.textContent,new RegExp(n+' 个附件$'));assert.match(review.textContent,new RegExp('待检查文件 '+n));if(n)assert.equal(clips[0].getAttribute('aria-label'),n+' 个附件');
    h.run("changeLanguage('en')");assert.equal(label.textContent,englishLabel);if(n)assert.equal(clips[0].getAttribute('aria-label'),n+' '+(n===1?'attachment':'attachments'));
    assert.match(h.nodes.get('#message-list').textContent,/Literal 1 attachments/);
  }
});

await check("in-place reader and receipt retry controls translate across languages", async () => {
  const h = harness();
  h.run("bindLanguage(); bindReadingRoom(); state.result = { messages: [] }");
  h.context.fetch = async () => response({ error: "synthetic unavailable" }, 503);
  await h.run("readMessage(1)");
  await h.run("showReceipt(1)");
  const readerRetry = h.nodes.get("#reader").querySelector(".retry-reader");
  const receiptRetry = h.nodes.get("#receipt-content").querySelector(".retry-receipt");
  assert.equal(readerRetry.textContent, "Try again");
  assert.equal(receiptRetry.textContent, "Try again");
  h.run("changeLanguage('zh-CN')");
  assert.equal(readerRetry.textContent, "重试");
  assert.equal(receiptRetry.textContent, "重试");
  h.run("changeLanguage('en')");
  assert.equal(readerRetry.textContent, "Try again");
  assert.equal(receiptRetry.textContent, "Try again");
});

await check("desktop backup restore guidance and reading-room comma shortcut copy translate cleanly", () => {
  const h = harness();
  h.run("bindLanguage()");
  const guide = h.nodes.get("#view-guide");
  const prefs = h.nodes.get("#preferences-dialog");
  assert.match(guide.textContent, /In the desktop window, choose “Restore backup…”/);
  assert.match(guide.textContent, /python app\.py --data-dir restored --restore-backup archive\.sqlite3/);
  assert.match(prefs.textContent, /Use , for reading room and \? for commands\./);
  h.run("changeLanguage('zh-CN')");
  assert.match(guide.textContent, /在桌面控制窗口点击“恢复备份…”即可校验并在新文件夹中打开副本；源码运行可使用：/);
  assert.match(guide.textContent, /python app\.py --data-dir restored --restore-backup archive\.sqlite3/);
  assert.match(prefs.textContent, /按 \/ 搜索、I 导入、G 查看邮件、H 查看记录；/);
  assert.match(prefs.textContent, /按 , 打开阅读设置、\? 打开命令。Ctrl \/ ⌘ K 始终可用。/);
  h.run("changeLanguage('en')");
  assert.match(guide.textContent, /In the desktop window, choose “Restore backup…”/);
  assert.match(prefs.textContent, /Use , for reading room and \? for commands\./);
});

console.log(`\n${passed} i18n/folder checks passed. Node ${process.version}; DOM shim and synthetic data, not physical browser or mailbox verification.`);
