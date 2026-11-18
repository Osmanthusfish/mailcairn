#!/usr/bin/env node
// Connection UI regressions share the existing DOM harness. Synthetic data only.
import assert from "node:assert/strict";
import { harness, response, deferred, emptyStats } from "./check_frontend.mjs";

let passed = 0;
async function check(name, fn) { await fn(); console.log(`PASS ${name}`); passed++; }
const mailbox = (extra = {}) => ({ id: "synthetic-account", provider: "imap", host: "imap.example.test", port: 993, username: "Import complete", folder: "INBOX", paused: false, status: "idle", added: 1, last_added: 1, last_duplicates: 0, last_sync: "2026-01-01T00:00:00Z", credentials_available: true, credentials_persistent: false, ...extra });
const mail = { id: 8, subject: "Synthetic mail", sender: "Fixture", date_day: "2026-01-01", snippet: "No personal data", attachments: 0 };
function setup({ persistent = false, accounts = [] } = {}) {
  const h = harness();
  h.run("bindLanguage(); bindEvents(); bindReadingRoom()");
  const model = { accounts, persistent, stats: { ...emptyStats }, requests: [], settingsError: "", postError: "" };
  h.context.fetch = async (path, options = {}) => {
    model.requests.push({ path, options });
    if (options.method === "POST") {
      if (model.postError) return response({ error: model.postError }, 400);
      if (path === "/api/connections") {
        const config = JSON.parse(options.body);
        model.accounts = [mailbox({ ...config, password: undefined, status: "queued", added: 0, credentials_persistent: config.remember })];
      } else if (path.endsWith("/disconnect")) model.accounts = [];
      else if (path.endsWith("/pause")) model.accounts[0] = { ...model.accounts[0], paused: true, status: "paused" };
      else if (path.endsWith("/resume")) model.accounts[0] = { ...model.accounts[0], paused: false, status: "queued" };
      return response({ ok: true });
    }
    if (path === "/api/connections") return response({ connections: model.accounts, capabilities: { persistent_credentials: model.persistent }, settings_error: model.settingsError });
    if (path === "/api/stats") return response(model.stats);
    if (path.startsWith("/api/messages?")) return response({ messages: model.stats.messages ? [mail] : [], total: model.stats.messages, offset: 0, limit: 50 });
    throw new Error(`Unexpected synthetic request: ${path}`);
  };
  const node = id => h.nodes.get("#" + id);
  // The shared shim does not reflect direct dataset writes into attributes.
  const controls = () => h.created.filter(item => {
    if (!item.dataset.connectionAction) return false;
    for (let parent = item.parentNode; parent; parent = parent.parentNode) if (parent === node("connections-list")) return true;
    return false;
  });
  const button = name => controls().find(item => item.dataset.connectionAction === name);
  return { h, model, node, button, controls };
}

await check("Gmail submission uses the preset and clears secrets without translating account data", async () => {
  const { h, model, node } = setup({ persistent: true });
  await h.run("openConnect()");
  assert.equal(node("connection-remember").checked, true);
  node("connection-username").value = "Import complete";
  node("connection-password").value = "test secret password";
  h.run("changeLanguage('zh-CN')");
  assert.equal(node("connection-password").value, "test secret password");
  assert.equal(node("connect-submit").textContent, "开始同步");
  await h.run("submitConnection({preventDefault(){}})");
  const request = model.requests.find(item => item.options.method === "POST");
  assert.deepEqual(JSON.parse(request.options.body), { provider: "gmail", host: "imap.gmail.com", port: 993, username: "Import complete", password: "testsecretpassword", remember: true, folder: "INBOX" });
  assert.equal(request.options.headers["X-MailCairn"], "1");
  assert.equal(request.options.credentials, "same-origin");
  assert.equal(node("connection-password").value, "");
  assert.match(node("connections-list").textContent, /Import complete/);
  assert.match(node("connections-list").textContent, /等待同步/);
  assert.ok(!JSON.stringify([...h.storage]).includes("secret"));
});

await check("Proton and custom IMAP expose the right fields and memory-only storage is explicit", async () => {
  const { h, node } = setup();
  await h.run("openConnect()");
  assert.equal(node("connection-remember").checked, false);
  assert.equal(node("connection-remember").disabled, true);
  h.run("configureProvider('proton'); changeLanguage('zh-CN')");
  assert.equal(node("connection-host").value, "127.0.0.1");
  assert.equal(node("connection-port").value, "1143");
  assert.equal(node("connection-port").disabled, false);
  assert.equal(node("connection-host-field").hidden, true);
  assert.match(node("connection-storage-note").textContent, /重启.*密码/);
  node("connection-password").value = "temporary-password";
  h.run("configureProvider('imap')");
  assert.equal(node("connection-password").value, "");
  assert.equal(node("connection-host-field").hidden, false);
  assert.equal(node("connection-host").disabled, false);
  assert.equal(node("connection-port").value, "993");
});

await check("submission failure clears the password and leaves a localized actionable form", async () => {
  const { h, model, node } = setup();
  await h.run("openConnect()");
  node("connection-username").value = "fixture@example.test";
  node("connection-password").value = "test-password";
  model.postError = "Authentication failed. Check the username and app password.";
  h.run("changeLanguage('zh-CN')");
  await h.run("submitConnection({preventDefault(){}})");
  assert.equal(node("connection-password").value, "");
  assert.match(node("connect-error").textContent, /认证失败/);
  assert.equal(node("connect-submit").disabled, false);
  assert.equal(node("connect-dialog").open, true);
  node("connection-password").value = "next-password";
  node("connect-dialog").close();
  assert.equal(node("connection-password").value, "");
});

await check("reconnecting preserves account identity and the existing session-only preference", async () => {
  const account = mailbox({ provider: "proton", host: "127.0.0.1", port: 2143, credentials_available: false });
  const { h, model, node } = setup({ persistent: true, accounts: [account] });
  h.context.fixtureAccount = account;
  await h.run("openConnect(fixtureAccount)");
  assert.equal(node("connection-username").readOnly, true);
  assert.equal(node("connection-port").disabled, true);
  assert.equal(node("connection-remember").checked, false);
  assert.ok(h.created.filter(item => item.dataset.provider).every(item => item.disabled));
  node("connection-password").value = "replacement";
  await h.run("submitConnection({preventDefault(){}})");
  const config = JSON.parse(model.requests.find(item => item.options.method === "POST").options.body);
  assert.equal(config.username, account.username);
  assert.equal(config.port, 2143);
  assert.equal(config.host, "127.0.0.1");
  assert.equal(config.remember, false);
});

await check("late connection responses cannot replace a newer account state", async () => {
  const { h, node } = setup();
  const first = deferred(), second = deferred(); let calls = 0;
  h.context.fetch = () => (++calls === 1 ? first.promise : second.promise);
  const old = h.run("refreshConnections()"), current = h.run("refreshConnections()");
  second.resolve(response({ connections: [mailbox({ paused: true, status: "paused" })], capabilities: { persistent_credentials: true } }));
  await current;
  first.resolve(response({ connections: [], capabilities: { persistent_credentials: false } }));
  await old;
  assert.equal(h.run("state.connections.length"), 1);
  assert.equal(h.run("state.connectionCapabilities.persistent_credentials"), true);
  assert.match(node("connections-list").textContent, /Paused/);
});

await check("pause, resume and disconnect update controls and preserve archived mail", async () => {
  const { h, model, button } = setup({ accounts: [mailbox()] });
  model.stats = { ...emptyStats, messages: 7 };
  await h.run("refreshStats(); refreshConnections()");
  await button("pause").events.click[0]();
  assert.equal(button("sync").disabled, true);
  assert.ok(button("resume"));
  await button("resume").events.click[0]();
  assert.ok(button("pause"));
  await button("disconnect").events.click[0]();
  assert.equal(h.run("state.connections.length"), 0);
  assert.equal(h.run("state.stats.messages"), 7);
  assert.ok(model.requests.filter(item => item.options.method === "POST").every(item => item.options.body === undefined));
});

await check("an action in flight disables duplicate mutation requests and recovers after failure", async () => {
  const { h, button, node, controls } = setup({ accounts: [mailbox()] });
  await h.run("refreshConnections()");
  const pending = deferred(); let posts = 0;
  h.context.fetch = async (path, options = {}) => { if (options.method === "POST") { posts++; return pending.promise; } throw new Error(path); };
  const operation = button("pause").events.click[0]();
  assert.ok(controls().length > 0);
  assert.ok(controls().every(item => item.disabled));
  await h.run("runConnectionAction(state.connections[0], 'pause')");
  assert.equal(posts, 1);
  pending.resolve(response({ error: "The operation failed. Check local disk space and retry." }, 500));
  await operation;
  assert.equal(button("pause").disabled, false);
  assert.equal(node("connections-error").hidden, false);
});

await check("mailbox actions keep focus through busy state and respect a user's move", async () => {
  for (const move of [false, true]) {
    const { h, model, button, node } = setup({accounts:[mailbox()]});
    h.run("state.view = 'connections'");
    await h.run("refreshConnections()");
    button('pause').focus();
    const pending = deferred(), originalFetch = h.context.fetch;
    h.context.fetch = (path, options = {}) => options.method === 'POST' ? pending.promise : originalFetch(path, options);
    const operation = button('pause').events.click[0]();
    assert.ok(h.document.activeElement.classList.contains('connection-card'), 'Busy action has a focusable card fallback');
    const other = node('search-input');
    if(move) other.focus();
    model.accounts = [mailbox({paused:true,status:'paused'})];
    pending.resolve(response({ok:true}));
    await operation;
    assert.ok(h.document.activeElement === (move ? other : button('resume')), 'Completion respects current focus and renamed action');
  }
});

await check("disconnect cleanup warning survives account refresh and translates", async () => {
  const {h, model, button, node} = setup({accounts:[mailbox()]});
  await h.run('refreshConnections()');
  const originalFetch = h.context.fetch;
  h.context.fetch = (path, options = {}) => {
    if(options.method === 'POST') {
      model.accounts=[];
      return Promise.resolve(response({ok:true,connection:{removed:true,warning:'Mailbox disconnected. Its saved password may remain on this computer because local cleanup failed.'}}));
    }
    return originalFetch(path, options);
  };
  await button('disconnect').events.click[0]();
  assert.equal(h.run('state.connections.length'),0);
  assert.equal(node('global-error').hidden,false);
  assert.match(node('global-error-text').textContent,/local cleanup failed/);
  h.run("changeLanguage('zh-CN')");
  assert.match(node('global-error-text').textContent,/邮箱已断开.*本地清理失败/);
});

await check("one mailbox update leaves other cards and focus intact and announces only status changes", async () => {
  const first=mailbox({id:'first',username:'Import complete'}), second=mailbox({id:'second',username:'Second synthetic'});
  const {h,model,node,controls}=setup({accounts:[first,second]});
  h.run("state.view='connections'");await h.run('refreshConnections()');
  const otherCard=node('connections-list').children[1];
  const otherButton=controls().find(button=>button.dataset.connectionId==='second'&&button.dataset.connectionAction==='pause');
  otherButton.focus();
  model.accounts=[{...first,added:2},second];await h.run('refreshConnections()');
  assert.ok(node('connections-list').children[1]===otherCard,'Unchanged mailbox must retain its DOM');
  assert.ok(h.document.activeElement===otherButton,'Updating a different mailbox preserves the focused node');
  assert.equal(node('connections-announcement').textContent,'','Counts alone must not announce the whole card');
  model.accounts=[{...first,status:'syncing'},second];await h.run('refreshConnections()');
  assert.match(node('connections-announcement').textContent,/Import complete: Syncing mail/);
  assert.ok(node('connections-list').children[0].querySelector('.status-tag').classList.contains('connection-status-changing'));
  h.run("changeLanguage('zh-CN')");
  assert.match(node('connections-announcement').textContent,/Import complete: 正在同步邮件/,'Opaque account names stay literal');
  model.accounts=[{...first,status:'idle'},second];await h.run('refreshConnections()');
  assert.match(node('connections-announcement').textContent,/Import complete: 已同步/);
  h.run("state.view='guide'");
  model.accounts=[{...first,status:'error'},second];await h.run('refreshConnections()');
  assert.doesNotMatch(node('connections-announcement').textContent,/需要处理/,'Hidden mailbox view must not announce polling');
});

await check("busy-only mailbox changes reuse cards and reduced motion stops the local state cue", async () => {
  const {h,model,node}=setup({accounts:[mailbox()]});h.run("state.view='connections'");
  await h.run('refreshConnections()');
  const card=node('connections-list').children[0];
  h.run("connectionActions.add('synthetic-account'); renderConnections()");
  assert.ok(node('connections-list').children[0]===card);
  h.run("connectionActions.clear(); renderConnections()");
  assert.ok(node('connections-list').children[0]===card);
  model.accounts=[mailbox({status:'syncing'})];await h.run('refreshConnections()');
  const status=node('connections-list').children[0].querySelector('.status-tag');
  assert.ok(status.classList.contains('connection-status-changing'));
  const media=h.media.get('(prefers-reduced-motion: reduce)');media.matches=true;h.emit(media,'change');
  assert.equal(status.classList.contains('connection-status-changing'),false);
});

await check("authentication and missing-password states offer reconnect instead of futile sync", async () => {
  const { h, model, button, node } = setup({ accounts: [mailbox({ status: "error", last_error: "Authentication failed. Check the username and app password." })] });
  await h.run("refreshConnections()");
  assert.ok(button("reconnect")); assert.equal(button("sync"), undefined);
  h.run("changeLanguage('zh-CN')");
  assert.match(node("connections-list").textContent, /认证失败/);
  model.accounts = [mailbox({ credentials_available: false, status: "auth_required" })];
  await h.run("refreshConnections()");
  assert.ok(button("reconnect"));
  assert.match(node("connections-list").textContent, /需要密码/);
});

const networkError = "Could not connect securely. Check the server, port and network.";
await check("Gmail network errors keep the successful timestamp and saved total without misattributing failed counters", async () => {
  const account = mailbox({ provider: "gmail", status: "error", added: 120, last_added: 0, last_duplicates: 0, last_error: networkError });
  const { h, node, button } = setup({ accounts: [account] });
  await h.run("refreshConnections()");
  for (const language of ["en", "zh-CN", "en"]) {
    h.run(`changeLanguage('${language}')`);
    const text = node("connections-list").textContent;
    const chinese = language === "zh-CN";
    assert.match(text, chinese ? /暂时无法连接 Gmail/ : /Cannot connect to Gmail right now/);
    assert.match(text, chinese ? /上次成功同步：/ : /Last successful sync:/);
    assert.ok(text.includes(h.run("localTime(state.connections[0].last_sync)")));
    assert.match(text, /120/);
    assert.match(text, chinese ? /每 5 分钟重试/ : /retries every 5 minutes/);
    assert.doesNotMatch(text, /duplicates|重复|Last checked|上次检查|server, port|服务器、端口/);
    assert.doesNotMatch(text, /app password|应用专用密码/);
    assert.ok(button("sync")); assert.equal(button("sync").disabled, false);
    assert.equal(button("reconnect"), undefined);
    assert.ok(button("mail"));
  }
});

await check("attempt counts appear only with a completed idle sync, never with failed or in-progress attempts", async () => {
  const { h, model, node } = setup();
  for (const status of ["idle", "queued", "syncing", "waiting", "error", "paused", "auth_required"]) {
    model.accounts = [mailbox({ status, paused: status === "paused", last_added: 17, last_duplicates: 4 })];
    await h.run("refreshConnections()");
    for (const language of ["en", "zh-CN"]) {
      h.run(`changeLanguage('${language}')`);
      const text = node("connections-list").textContent;
      assert.match(text, language === "en" ? /Last successful sync:/ : /上次成功同步：/);
      if (status === "idle") assert.match(text, language === "en" ? /17 added · 4 duplicates in the last successful sync/ : /上次成功同步：新增 17 · 重复 4/);
      else assert.doesNotMatch(text, /duplicates|重复/);
    }
  }
  for (const extra of [{ last_sync: "" }, { last_error: networkError }, { credentials_available: false }, { paused: true }]) {
    model.accounts = [mailbox({ ...extra })]; await h.run("refreshConnections()");
    assert.doesNotMatch(node("connections-list").textContent, /duplicates|重复/);
  }
  model.accounts = [mailbox({ last_sync: "", status: "error", last_error: networkError })];
  await h.run("refreshConnections()");
  assert.match(node("connections-list").textContent, /尚未完成同步/);
  assert.doesNotMatch(node("connections-list").textContent, /上次成功同步：/);
});

await check("automatic retry copy requires a network error, available credentials and an unpaused error state", async () => {
  const { h, model, node, button } = setup();
  for (const extra of [
    { paused: true, status: "paused" }, { paused: true },
    { credentials_available: false }, { credentials_available: undefined },
    { status: "auth_required" }, { status: "queued" }, { status: "syncing" }, { status: "waiting" },
    { last_error: "Authentication failed. Check the username and app password." },
    { last_error: "The Proton Bridge certificate changed. Remove and reconnect this account after checking Bridge." }
  ]) {
    model.accounts = [mailbox({ status: "error", last_error: networkError, ...extra })];
    await h.run("refreshConnections()");
    for (const language of ["en", "zh-CN"]) {
      h.run(`changeLanguage('${language}')`);
      assert.doesNotMatch(node("connections-list").textContent, /retries every|每 5 分钟重试/);
    }
    if (extra.paused) assert.equal(button("sync").disabled, true);
    if (extra.credentials_available === false || extra.status === "auth_required" || extra.last_error?.startsWith("Authentication failed.")) {
      assert.ok(button("reconnect")); assert.equal(button("sync"), undefined);
    }
  }
});

await check("certificate and unknown errors stay visible in both languages without being softened into network recovery", async () => {
  const { h, model, node } = setup();
  const certificate = "The Proton Bridge certificate changed. Remove and reconnect this account after checking Bridge.";
  const unknown = "Unrecognized provider response <b>literal detail</b> — 120";
  for (const error of [certificate, unknown]) {
    model.accounts = [mailbox({ provider: "proton", status: "error", last_error: error })];
    await h.run("refreshConnections()");
    for (const language of ["en", "zh-CN", "en"]) {
      h.run(`changeLanguage('${language}')`);
      const text = node("connections-list").textContent;
      assert.match(text, language === "zh-CN" ? /需要处理/ : /Needs attention/);
      if (error === unknown || language === "en") assert.ok(text.includes(error));
      else assert.match(text, /证书已更改/);
      assert.doesNotMatch(text, /Connection unavailable|暂时无法连接|retries every|每 5 分钟重试/);
    }
  }
});

await check("TLS certificate verification errors remain distinct and translated", async () => {
  const { h, model, node } = setup();
  const error = "The mail server's security certificate could not be verified. Check the server address and your device's date and time.";
  model.accounts = [mailbox({ provider: "gmail", status: "error", last_error: error })];
  await h.run("refreshConnections()");
  for (const language of ["en", "zh-CN"]) {
    h.run(`changeLanguage('${language}')`);
    const text = node("connections-list").textContent;
    assert.match(text, language === "en" ? /security certificate could not be verified/ : /无法验证邮件服务器的安全证书/);
    assert.doesNotMatch(text, /Connection unavailable|暂时无法连接/);
  }
});

await check("incomplete responses explain retry without blaming the password", async () => {
  const { h, model, node, button } = setup();
  const error = "The server returned an unsupported or incomplete IMAP response.";
  model.accounts = [mailbox({ status: "error", last_error: error })];
  await h.run("refreshConnections()");
  for (const language of ["en", "zh-CN"]) {
    h.run(`changeLanguage('${language}')`);
    const text = node("connections-list").textContent;
    assert.match(text, language === "en" ? /incomplete or unsupported response/ : /邮箱返回的数据不完整或暂不受支持/);
    assert.match(text, language === "en" ? /retries every 5 minutes/ : /每 5 分钟重试/);
    assert.doesNotMatch(text, /IMAP|app password|应用专用密码/);
    assert.ok(button("sync"));
    assert.equal(button("sync").disabled, false);
    assert.equal(button("reconnect"), undefined);
  }
  model.accounts = [mailbox({ status: "paused", paused: true, last_error: error })];
  await h.run("refreshConnections()");
  assert.doesNotMatch(node("connections-list").textContent, /retries every|每 5 分钟重试/);
});

await check("unchanged polling leaves results intact and new mail preserves the selected reader and filters", async () => {
  const { h, model, node } = setup({ accounts: [mailbox()] });
  model.stats = { ...emptyStats, messages: 1 };
  await h.run("refreshStats()");
  h.run("state.view='archive';state.searchReady=true;state.selected=8;connectionPollingStarted=true");
  node("reader").textContent = "Reader stays exact";
  node("search-input").value = "mail";
  node("filter-sender").value = "Fixture";
  await h.run("pollConnections()");
  assert.equal(model.requests.filter(item => item.path.startsWith("/api/messages?")).length, 0);
  model.stats = { ...model.stats, messages: 2 };
  await h.run("pollConnections()");
  const searches = model.requests.filter(item => item.path.startsWith("/api/messages?"));
  assert.equal(searches.length, 1);
  assert.match(searches[0].path, /q=mail&sender=Fixture/);
  assert.equal(h.run("state.selected"), 8);
  assert.equal(node("reader").textContent, "Reader stays exact");
  assert.equal(node("search-input").value, "mail");
});

await check("first synced mail updates actual counts and empty state before archive navigation", async () => {
  const { h, model, node } = setup({ accounts: [mailbox()] });
  await h.run("refreshStats()");
  h.run("state.view='connections';connectionPollingStarted=true");
  assert.equal(node("empty-archive").hidden, false);
  model.stats = { ...emptyStats, messages: 1 };
  await h.run("pollConnections()");
  assert.equal(node("empty-archive").hidden, true);
  assert.equal(node("summary-count").textContent, "1");
  assert.equal(h.run("state.archiveDirty"), true);
  assert.equal(model.requests.filter(item => item.path.startsWith("/api/messages?")).length, 0);
  h.run("setView('archive')");
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.run("state.result.total"), 1);
  assert.equal(h.run("state.archiveDirty"), false);
});

await check("hidden pages abort in-flight polling and page exit prevents rescheduling", async () => {
  const { h, node } = setup({ accounts: [mailbox()] });
  await h.run("refreshConnections()");
  h.run("connectionPollingStarted=true");
  const pending = deferred(); let signal;
  h.context.fetch = (path, options) => { signal = options.signal; return pending.promise; };
  const poll = h.run("pollConnections()");
  h.document.hidden = true; h.emit(h.document, "visibilitychange");
  assert.equal(signal.aborted, true);
  pending.resolve(response({ connections: [], capabilities: { persistent_credentials: false } }));
  await poll;
  assert.equal(h.run("state.connections.length"), 1, "Aborted response must not clear current accounts");
  assert.equal(h.run("connectionPollTimer"), 0);
  assert.equal(node("connections-error").hidden, true);
  h.document.hidden = false; h.emit(h.document, "visibilitychange");
  assert.ok(h.run("connectionPollTimer") > 0);
  h.emit(h.context.window, "pagehide");
  assert.equal(h.run("connectionPollingStarted"), false);
  assert.equal(h.run("connectionPollTimer"), 0);
});

await check("View mail refreshes first-sync stats and clears stale filters before displaying real mail", async () => {
  const { h, model, node, button } = setup({ accounts: [mailbox()] });
  await h.run("refreshConnections()");
  h.run("state.view='connections';state.stats={messages:0};state.selected=8;state.importId='old-source'");
  node("search-input").value = "old query"; node("filter-sender").value = "old sender";
  node("filter-after").value = "2024-01-01"; node("filter-before").value = "2024-12-31"; node("filter-attachments").checked = true;
  model.stats = { ...emptyStats, messages: 1 };
  await button("mail").events.click[0]();
  assert.equal(h.run("state.view"), "archive");
  assert.equal(h.run("state.result.total"), 1);
  assert.equal(h.run("state.importId"), "");
  for (const id of ["search-input", "filter-sender", "filter-after", "filter-before"]) assert.equal(node(id).value, "");
  assert.equal(node("filter-attachments").checked, false);
});

await check("a delayed View mail response cannot redirect after navigating elsewhere", async () => {
  const { h, button } = setup({ accounts: [mailbox()] });
  await h.run("refreshConnections()"); h.run("state.view='connections'");
  const pending = deferred();
  h.context.fetch = path => { assert.equal(path, "/api/stats"); return pending.promise; };
  const action = button("mail").events.click[0]();
  h.run("setView('guide')");
  pending.resolve(response({ ...emptyStats, messages: 1 })); await action;
  assert.equal(h.run("state.view"), "guide");
});

await check("corrupt connection settings show a localized warning without hiding saved accounts", async () => {
  const { h, model, node } = setup({ accounts: [mailbox()] });
  model.settingsError = "Connection settings could not be saved. Check disk space and permissions.";
  h.run("changeLanguage('zh-CN')");
  await h.run("refreshConnections()");
  assert.equal(node("connections-error").hidden, false);
  assert.match(node("connections-error").textContent, /无法保存连接设置/);
  assert.match(node("connections-list").textContent, /Import complete/);
});

await check("provider defaults keep ports behind Advanced settings and preserve a custom Bridge port", async () => {
  const { h, model, node } = setup();
  await h.run("openConnect()");
  assert.equal(node("connection-advanced").hidden, true);
  assert.equal(node("connection-host-field").hidden, true);
  assert.equal(node("connection-server"), undefined, "Setup must not display a redundant server/protocol summary");
  h.run("configureProvider('proton')");
  assert.equal(node("connection-advanced").hidden, false);
  assert.equal(node("connection-advanced").open, false);
  assert.equal(node("connection-port").value, "1143");
  node("connection-advanced").open = true;
  node("connection-port").value = "2143";
  node("connection-username").value = "bridge-user";
  node("connection-password").value = "bridge-generated-password";
  await h.run("submitConnection({preventDefault(){}})");
  const config = JSON.parse(model.requests.find(item => item.options.method === "POST").options.body);
  assert.equal(config.port, 2143);
  assert.equal(config.host, "127.0.0.1");
  assert.equal(config.provider, "proton");
});

await check("custom email still requires its server and invalid advanced input becomes reachable", async () => {
  const { h, model, node } = setup();
  await h.run("openConnect(null, 'imap')");
  assert.equal(node("connection-host-field").hidden, false);
  assert.equal(node("connection-host").required, true);
  assert.equal(node("connection-advanced").open, false);
  assert.equal(node("connection-port").value, "993");
  node("connection-username").value = "mail-user";
  node("connection-password").value = "app-password";
  await h.run("submitConnection({preventDefault(){}})");
  assert.equal(model.requests.filter(item => item.options.method === "POST").length, 0);
  assert.equal(node("connect-error").hidden, false);
  h.emit(node("connection-port"), "invalid");
  assert.equal(node("connection-advanced").open, true, "Native validation must expose its editable field");
  node("connection-host").value = "imap.example.test";
  await h.run("submitConnection({preventDefault(){}})");
  const config = JSON.parse(model.requests.find(item => item.options.method === "POST").options.body);
  assert.equal(config.host, "imap.example.test");
  assert.equal(config.port, 993);
});

await check("setup help opens selected bilingual instructions inside Getting started and clears the secret", async () => {
  const { h, node } = setup();
  await h.run("openConnect(null, 'proton')");
  node("connection-password").value = "do-not-carry-to-guide";
  h.run("changeLanguage('zh-CN')");
  node("mailbox-setup-help").events.click[0]();
  assert.equal(node("connect-dialog").open, false);
  assert.equal(node("connection-password").value, "");
  assert.equal(h.run("state.view"), "guide");
  assert.equal(node("mailbox-guide-proton").open, true);
  assert.equal(h.document.activeElement, node("mailbox-guide-title"));
  assert.match(node("mailbox-guide-proton").textContent, /付费.*Proton/);
  assert.match(node("mailbox-guide-gmail").textContent, /两步验证/);
  assert.match(node("mailbox-guide-imap").textContent, /收信服务器/);
  assert.match(node("mailbox-guide-sync").textContent, /内存/);
  assert.match(node("mailbox-guide-sync").textContent, /每 5 分钟/);
  const connectOther = h.created.find(item => item.dataset.connectProvider === "imap");
  await connectOther.events.click[0]();
  assert.equal(node("connect-dialog").open, true);
  assert.equal(h.run("connectionProvider"), "imap");
  assert.equal(node("connection-host-field").hidden, false);
});

await check("cards omit connection internals while session-only setup still explains the restart consequence", async () => {
  const { h, model, node } = setup({ persistent: true, accounts: [mailbox({ credentials_persistent: true })] });
  await h.run("refreshConnections(); openConnect()");
  const cardText = node("connections-list").textContent;
  assert.ok(!cardText.includes("imap.example.test"));
  assert.ok(!cardText.includes(":993"));
  assert.ok(!cardText.includes("Password protected by Windows"));
  assert.equal(node("connection-remember-option").hidden, false);
  assert.equal(node("connection-storage-note").hidden, true);
  node("connection-remember").checked = false;
  h.emit(node("connection-remember"), "change");
  assert.equal(node("connection-storage-note").hidden, false);
  assert.match(node("connection-storage-note").textContent, /after restarting/);
  model.persistent = false;
  await h.run("openConnect()");
  assert.equal(node("connection-remember-option").hidden, true);
  assert.equal(node("connection-remember").checked, false);
  assert.equal(node("connection-storage-note").hidden, false);
});

await check("a new launch session fragment reloads an existing tab once and ordinary anchors do not", () => {
  const h = harness(); let reloads = 0;
  h.context.location.reload = () => { reloads++; };
  h.run("bindSessionNavigation(); bindSessionNavigation(); bindSessionNavigation()");
  for (const hash of ["#archive", "#session=", "#session=invalid", "#not-session=" + "a".repeat(43)]) {
    h.context.window.location.hash = hash; h.emit(h.context.window, "hashchange");
  }
  assert.equal(reloads, 0);
  h.context.window.location.hash = "#session=" + "a".repeat(41) + "_-";
  h.emit(h.context.window, "hashchange");
  assert.equal(reloads, 1, "Repeated binding must not duplicate a session reload");
  h.context.window.location.hash = "#archive";
  h.emit(h.context.window, "hashchange");
  assert.equal(reloads, 1);
});

await check("failed startup discovery retries at a bounded interval, pauses when hidden, and stops for inactive accounts", async () => {
  for (const accounts of [[], [mailbox({ paused: true })], [mailbox()]]) {
    const h = harness();
    let statusRequests = 0, unavailable = true;
    h.context.fetch = async path => {
      if (path === "/api/stats") return response(emptyStats);
      if (path === "/api/connections") {
        statusRequests++;
        if (unavailable) throw new Error("Synthetic temporary status failure");
        return response({ connections: accounts, capabilities: { persistent_credentials: false } });
      }
      throw new Error(path);
    };
    await h.run("initialize()");
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(statusRequests, 1);
    assert.equal(h.run("state.connections"), null, "Failed discovery must remain unknown");
    assert.ok(h.run("connectionPollTimer") > 0, "Failure must schedule recovery without another user action");
    h.advance(7999);
    assert.equal(statusRequests, 1, "Discovery failures cannot spin immediately");
    h.document.hidden = true; h.emit(h.document, "visibilitychange");
    assert.equal(h.run("connectionPollTimer"), 0);
    h.advance(60000);
    assert.equal(statusRequests, 1, "Hidden pages must not retry discovery");
    h.document.hidden = false; h.emit(h.document, "visibilitychange");
    h.advance(0);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(statusRequests, 2, "Returning to the page retries unknown accounts");
    h.advance(7999);
    assert.equal(statusRequests, 2, "Repeated failure still observes the retry interval");
    unavailable = false;
    h.advance(1);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(statusRequests, 3);
    assert.equal(h.run("state.connections.length"), accounts.length);
    const active = accounts.some(account => !account.paused);
    assert.equal(h.run("connectionPollTimer > 0"), active, "Only known active accounts keep archive polling alive");
    if (!active) {
      h.advance(60000);
      assert.equal(statusRequests, 3, "Known empty or paused lists must not keep polling in the archive");
    }
  }
});

await check("startup exchanges the new launch token before loading data and removes it from the URL", async () => {
  const h = harness(), requests = [], replacements = [];
  const token = "b".repeat(43);
  h.context.window.location.hash = "#session=" + token;
  h.context.history.replaceState = (...args) => { replacements.push(args); h.context.window.location.hash = ""; };
  h.context.fetch = async (path, options = {}) => {
    requests.push({ path, options });
    if (path === "/api/session") return response({ ok: true });
    if (path === "/api/stats") return response(emptyStats);
    if (path === "/api/connections") return response({ connections: [], capabilities: { persistent_credentials: false } });
    throw new Error(path);
  };
  await h.run("initialize()");
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(requests[0].path, "/api/session");
  assert.equal(requests[0].options.method, "POST");
  assert.equal(requests[0].options.headers["X-MailCairn-Token"], token);
  assert.equal(requests[1].path, "/api/stats");
  assert.deepEqual(replacements, [[null, "", "/"]]);
  assert.equal(h.context.window.location.hash, "");
  assert.ok(requests.every(item => !item.path.includes(token)));
  assert.equal(h.nodes.get("#loading-screen").hidden, true);
});

console.log(`\n${passed} connection UI checks passed. Node ${process.version}; shared DOM shim and synthetic data, not a live mailbox or browser audit.`);
