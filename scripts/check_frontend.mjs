#!/usr/bin/env node
// Dependency-free static and state-machine checks. This is not a browser,
// accessibility audit, or layout test; exercise those separately in a browser.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const html = readFileSync(resolve(root, "mailcairn/static/index.html"), "utf8");
const source = readFileSync(resolve(root, "mailcairn/static/app.js"), "utf8");
const languageSource = readFileSync(resolve(root, "mailcairn/static/i18n.js"), "utf8");
const isDirect = !!process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href;
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map((match) => match[1]);
const idSet = new Set(ids);
const dynamicIds = new Set([...source.matchAll(/\.id\s*=\s*"([^"]+)"/g)].map((match) => match[1]));
const reports = [];
function check(name, fn) {
  if (!isDirect) return Promise.resolve();
  return Promise.resolve().then(fn).then(() => { reports.push(name); console.log(`PASS ${name}`); });
}

await check("static IDs, accessibility references, and local resource boundaries", () => {
  assert.equal(ids.length, idSet.size, "Duplicate HTML IDs");
  for (const match of source.matchAll(/\$\("#([\w-]+)(?:"|[ .:[>])/g)) {
    assert.ok(idSet.has(match[1]) || dynamicIds.has(match[1]), `Missing HTML ID: ${match[1]}`);
  }
  for (const match of html.matchAll(/\b(?:for|aria-controls|aria-labelledby|aria-describedby)="([^"]+)"/g)) {
    for (const id of match[1].split(/\s+/)) assert.ok(idSet.has(id), `Broken accessible reference: ${id}`);
  }
  assert.doesNotMatch(html, /\son\w+\s*=/i, "Inline event handlers conflict with CSP");
  assert.doesNotMatch(html, /<(?:script|link|img|iframe)\b[^>]*(?:src|href)="https?:/i, "Unexpected remote resource");
  assert.doesNotMatch(source, /\b(?:innerHTML|outerHTML|insertAdjacentHTML|eval)\b/, "Mail must remain inert text");
  for (const removed of ["scene-dialog", "open-scene", "replay-scene", "stop-scene", "replay-archive-light", "preview-effects"]) {
    assert.equal(idSet.has(removed), false, `Removed demonstration control must not remain: ${removed}`);
  }
  assert.match(html, /name="viewport"/);
  assert.match(html, /<html\s+lang="[^"]+"/);
});

// This tiny DOM preserves text and listeners and supplies only the platform
// operations used by these state tests. It never parses mail as HTML.
export function harness(options = {}) {
  const nodes = new Map(), created = [], timers = new Map(), frames = new Map(), media = new Map(), observers = [], animations = [];
  let nextTimer = 0, nextFrame = 0, now = 0;
  const events = () => ({
    events: {},
    addEventListener(name, fn) { (this.events[name] ||= []).push(fn); },
    dispatchEvent(event) { for (const fn of this.events[event.type] || []) fn(event); },
  });
  const emit = (target, type, fields = {}) => target.dispatchEvent({ type, target, preventDefault() {}, ...fields });
  class Node {
    constructor(tag = "div") {
      this.tagName = tag.toUpperCase(); this.children = []; this.attributes = new Map();
      this.nodeType = tag === "#text" ? 3 : 1;
      this.dataset = {}; this.events = {}; this.value = ""; this.checked = false;
      this.hidden = false; this.disabled = false; this.open = false; this._text = "";
      this.className = "";
      const properties = new Map();
      this.style = { setProperty: (key, value) => properties.set(key, value), removeProperty: (key) => properties.delete(key), getPropertyValue: (key) => properties.get(key) || "" };
      this.bounds = { left: 0, top: 0, width: 800, height: 450 };
      this.visible = true;
      this.draws = { clears: 0, paints: 0 };
      let transform = [1, 0, 0, 1, 0, 0];
      const gradient = () => ({ addColorStop() {} });
      this.context2d = {
        clearRect: () => { this.draws.clears++; this.draws.clearTransform = [...transform]; }, fillRect: () => { this.draws.paints++; }, fill: () => { this.draws.paints++; }, stroke: () => { this.draws.paints++; },
        createLinearGradient: gradient, createRadialGradient: gradient,
        setTransform: (...values) => { transform = values; }, transform() {}, save() {}, restore() {}, beginPath() {}, closePath() {}, arc() {}, moveTo() {}, lineTo() {}, translate() {}, rotate() {}, scale() {}, quadraticCurveTo() {}, bezierCurveTo() {}, ellipse() {},
      };
      this.classList = {
        contains: (name) => this.className.split(/\s+/).includes(name),
        add: (...names) => { this.className = [...new Set([...this.className.split(/\s+/), ...names])].join(" "); },
        remove: (...names) => { this.className = this.className.split(/\s+/).filter((name) => !names.includes(name)).join(" "); },
        toggle: (name, force) => { const enabled = force ?? !this.classList.contains(name); this.classList[enabled ? "add" : "remove"](name); return enabled; },
      };
      created.push(this);
    }
    set id(value) { this._id = value; nodes.set(`#${value}`, this); }
    get id() { return this._id || ""; }
    set textContent(value) { this._text = String(value ?? ""); for (const node of this.children) if (typeof node === "object") node.parentNode = null; this.children = []; }
    get textContent() { return this._text + this.children.map((node) => node.textContent ?? String(node)).join(""); }
    get childNodes() { return this.children; }
    append(...children) { for (const node of children) { this.children.push(node); if (typeof node === "object") node.parentNode = this; } }
    prepend(...children) { this.children.unshift(...children); for (const node of children) if (typeof node === "object") node.parentNode = this; }
    replaceChildren(...children) { this.textContent = ""; this.append(...children); }
    setAttribute(key, value) {
      this.attributes.set(key, String(value));
      if (key === "class") this.className = value;
      if (key.startsWith("data-")) this.dataset[key.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = String(value);
    }
    getAttribute(key) { return this.attributes.get(key) ?? null; }
    removeAttribute(key) { this.attributes.delete(key); }
    addEventListener(name, fn) { (this.events[name] ||= []).push(fn); }
    dispatchEvent(event) { for (const fn of this.events[event.type] || []) fn(event); }
    getContext() { return this.context2d; }
    animate(keyframes, options) {
      const animation = { target: this, keyframes, options, started: now, playState: "running", onfinish: null, oncancel: null,
        cancel() { this.playState = "idle"; this.oncancel?.(); },
        finish() { if (this.playState === "running") { this.playState = "finished"; this.onfinish?.(); } },
      };
      animations.push(animation);
      return animation;
    }
    getClientRects() { return this.visible ? [this.bounds] : []; }
    getBoundingClientRect() { return { ...this.bounds, right: this.bounds.left + this.bounds.width, bottom: this.bounds.top + this.bounds.height }; }
    focus() { document.activeElement = this; }
    remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter((node) => node !== this); this.parentNode = null; nodes.delete(`#${this.id}`); }
    showModal() { this.open = true; }
    close() { if (this.open) { this.open = false; emit(this, "close"); } }
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
    querySelectorAll(selector) {
      return created.filter((node) => matchesQuery(node, selector)).filter((node) => {
        for (let parent = node.parentNode; parent; parent = parent.parentNode) if (parent === this) return true;
        return false;
      });
    }
    scrollIntoView() {}
    click() { if (!this.disabled) emit(this, "click"); }
    insertBefore(node, reference) { node.remove(); const index = reference ? this.children.indexOf(reference) : this.children.length; this.children.splice(index, 0, node); node.parentNode = this; return node; }
  }
  function matchesQuery(node, selector) {
    const attribute = selector.match(/^\[([\w-]+)\]$/);
    if (attribute) return node.attributes.has(attribute[1]);
    const className = selector.match(/^\.([\w-]+)$/);
    if (className) return node.classList.contains(className[1]);
    if (selector === "dialog" || selector === "canvas") return node.tagName === selector.toUpperCase();
    return ["#message-list .message-row", "#message-list button"].includes(selector) && node.classList.contains("message-row");
  }
  function connected(node) {
    for (let parent = node; parent; parent = parent.parentNode) if (parent === document.documentElement) return true;
    return false;
  }
  const stack = [], voidTags = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"]);
  for (const match of html.matchAll(/<(\/?)([a-z][a-z0-9]*)\b([^>]*)>|([^<]+)/g)) {
    if (match[4]) {
      if (stack.length) { const node = new Node("#text"); node.textContent = match[4]; stack.at(-1).append(node); }
      continue;
    }
    if (match[1]) {
      const index = stack.findLastIndex((node) => node.tagName === match[2].toUpperCase());
      if (index >= 0) stack.length = index;
      continue;
    }
    const node = new Node(match[2]);
    for (const attribute of match[3].matchAll(/([\w-]+)(?:="([^"]*)")?/g)) {
      node.setAttribute(attribute[1], attribute[2] ?? "");
      if (attribute[1] === "id") node.id = attribute[2];
    }
    stack.at(-1)?.append(node);
    if (!voidTags.has(match[2]) && !match[3].endsWith("/")) stack.push(node);
  }
  const document = {
    ...events(), hidden: false,
    createElement: (tag) => new Node(tag), createElementNS: (_, tag) => new Node(tag),
    createTextNode: (text) => { const node = new Node("#text"); node.textContent = text; return node; },
    getElementById: (id) => nodes.get(`#${id}`) || null,
    querySelector(selector) {
      if (selector === "dialog[open]") return [...nodes.values()].find((node) => node.open) || null;
      if (selector.startsWith("#") && !/[ >:[.]/.test(selector.slice(1))) return nodes.get(selector) || null;
      if (/^\.[\w-]+$/.test(selector)) {
        const node = created.find((item) => connected(item) && item.classList.contains(selector.slice(1)));
        if (node) return node;
      }
      if (!nodes.has(selector)) nodes.set(selector, new Node());
      return nodes.get(selector);
    },
    querySelectorAll(selector) {
      return created.filter((node) => connected(node) && matchesQuery(node, selector));
    },
  };
  document.body = created.find(node => node.tagName === "BODY") || new Node("body");
  document.documentElement = created.find(node => node.tagName === "HTML") || new Node("html");
  document.activeElement = document.body;
  const storage = new Map(Object.entries(options.storage || {}));
  const context = vm.createContext({
    console, document, URLSearchParams, Intl, AbortController, navigator: { language: options.language || "en-US" },
    localStorage: { getItem: (key) => { if (options.storageFailure) throw new Error("Storage unavailable"); return storage.get(key) ?? null; }, setItem: (key, value) => { if (options.storageFailure) throw new Error("Storage unavailable"); storage.set(key, String(value)); } },
    window: { ...events(), devicePixelRatio: 3, innerWidth: 1200, innerHeight: 800, scrollY: 0, scrollTo() {},
      matchMedia: (query) => { if (!media.has(query)) media.set(query, { ...events(), matches: false }); return media.get(query); },
      location: { hash: "", pathname: "/" } },
    performance: { now: () => now },
    IntersectionObserver: class { constructor(callback) { this.callback = callback; this.targets = []; observers.push(this); } observe(target) { this.targets.push(target); } disconnect() {} },
    location: { reload() {} }, history: { replaceState() {} },
    setTimeout: (fn, delay = 0) => { timers.set(++nextTimer, { fn, due: now + delay }); return nextTimer; }, clearTimeout: (id) => timers.delete(id),
    requestAnimationFrame: (fn) => { frames.set(++nextFrame, fn); return nextFrame; }, cancelAnimationFrame: (id) => frames.delete(id),
    fetch: async () => { throw new Error("Unexpected network call"); },
  });
  const code = source.replace(/\binitialize\(\);\s*$/, "");
  assert.notEqual(code, source, "Expected a single explicit application startup call");
  vm.runInContext(languageSource, context, { filename: "i18n.js" });
  vm.runInContext(code, context, { filename: "app.js" });
  const run = (code) => vm.runInContext(code, context);
  function advance(milliseconds = 40) {
    now += milliseconds;
    const due = [...timers.entries()].filter(([, timer]) => timer.due <= now);
    for (const [id, timer] of due) { if (timers.delete(id)) timer.fn(); }
    for (const animation of animations) if (animation.playState === "running" && now - animation.started >= animation.options.duration) animation.finish();
    const batch = [...frames.entries()];
    for (const [id, callback] of batch) { if (frames.delete(id)) callback(now); }
  }
  return { context, run, nodes, created, document, frames, timers, media, storage, observers, animations, emit, advance };
}
export const response = (body, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
export const deferred = () => { let resolve; const promise = new Promise((done) => { resolve = done; }); return { promise, resolve }; };
export const emptyStats = { messages: 0, raw_bytes: 0, attachments: 0, imports: [], active_job: null, archive_file: "synthetic archive" };

await check("API mutations use local credentials and required header", async () => {
  const h = harness();
  let observed;
  h.context.fetch = async (path, options) => { observed = { path, options }; return response({ ok: true }); };
  await h.run('api("/api/verify", { method: "POST" })');
  assert.equal(observed.path, "/api/verify");
  assert.equal(observed.options.credentials, "same-origin");
  assert.equal(observed.options.headers["X-MailCairn"], "1");
});

await check("late search responses cannot replace newer results", async () => {
  const h = harness(), first = deferred(), second = deferred();
  const queue = [first, second];
  h.context.fetch = () => queue.shift().promise;
  h.run("state.stats = { messages: 12 }");
  h.nodes.get("#search-input").value = "old";
  const oldSearch = h.run("search()");
  h.nodes.get("#search-input").value = "new";
  const newSearch = h.run("search()");
  second.resolve(response({ total: 2, messages: [], offset: 0, limit: 50 }));
  await newSearch;
  first.resolve(response({ total: 11, messages: [], offset: 0, limit: 50 }));
  await oldSearch;
  assert.equal(h.run("state.result.total"), 2);
  assert.equal(h.run("state.searchReady"), true);
  assert.match(h.nodes.get("#export-results").href, /q=new/);
});

await check("query and sender edits reject old responses throughout debounce and block stale exports", async () => {
  for (const field of ["search-input", "filter-sender"]) {
    for (const failed of [false, true]) {
      const h = harness(), old = deferred(), current = deferred(), requests = [];
      const seed = { total: 120, offset: 50, limit: 50, messages: [{ id: 7, subject: "Existing result", sender: "Synthetic", date_day: "2026-01-01" }] };
      h.context.seedResult = seed;
      h.run("bindEvents(); state.stats={messages:120}; state.result=seedResult; state.searchReady=true; renderList()");
      h.nodes.get("#global-error").hidden = true;
      h.context.fetch = path => { requests.push(path); return requests.length === 1 ? old.promise : current.promise; };
      h.nodes.get("#" + field).value = "old";
      const oldSearch = h.run("search()");
      // Simulate a real edit while the old request is pending, before any new request starts.
      h.nodes.get("#" + field).value = "新查询";
      h.emit(h.nodes.get("#" + field), "input");
      old.resolve(failed ? response({ error: "Stale failure" }, 503) : response({ total: 99, offset: 0, limit: 50, messages: [{ id: 8, subject: "Stale result", sender: "Old" }] }));
      await oldSearch;
      assert.equal(requests.length, 1);
      assert.equal(h.run("state.result.total"), 120);
      assert.match(h.nodes.get("#message-list").textContent, /Existing result/);
      assert.doesNotMatch(h.nodes.get("#message-list").textContent, /Stale result/);
      assert.equal(h.nodes.get("#global-error").hidden, true);
      assert.equal(h.run("state.searchReady"), false);
      assert.equal(h.nodes.get("#export-results").getAttribute("aria-disabled"), "true");
      assert.equal(h.nodes.get("#previous-page").disabled, true);
      assert.equal(h.nodes.get("#next-page").disabled, true);
      let prevented = false;
      h.emit(h.nodes.get("#export-results"), "click", { preventDefault() { prevented = true; } });
      assert.equal(prevented, true, "An old response must not reopen export during debounce");
      h.advance(249);
      assert.equal(requests.length, 1);
      h.advance(1);
      assert.equal(requests.length, 2);
      assert.equal(new URL(requests[1], "http://synthetic.test").searchParams.get(field === "search-input" ? "q" : "sender"), "新查询");
      current.resolve(response({ total: 1, offset: 0, limit: 50, messages: [{ id: 9, subject: "Current result", sender: "New" }] }));
      await new Promise(resolve => setImmediate(resolve));
      assert.equal(h.run("state.result.total"), 1);
      assert.match(h.nodes.get("#message-list").textContent, /Current result/);
      assert.equal(h.run("state.searchReady"), true);
      assert.equal(h.nodes.get("#export-results").getAttribute("aria-disabled"), "false");
      assert.equal(new URL(h.nodes.get("#export-results").href, "http://synthetic.test").searchParams.get(field === "search-input" ? "q" : "sender"), "新查询");
    }
  }
});

await check("invalid filters invalidate pending searches and disable export", async () => {
  const h = harness(), pending = deferred();
  h.context.fetch = () => pending.promise;
  h.run("state.stats = { messages: 1 }");
  const oldSearch = h.run("search()");
  h.nodes.get("#filter-after").value = "2026-11-10";
  h.nodes.get("#filter-before").value = "2026-11-09";
  await h.run("search()");
  pending.resolve(response({ total: 1, messages: [], offset: 0, limit: 50 }));
  await oldSearch;
  assert.equal(h.run("state.searchReady"), false);
  assert.equal(h.nodes.get("#export-results").getAttribute("aria-disabled"), "true");
  assert.match(h.nodes.get("#global-error-text").textContent, /start date/i);
});

await check("correcting invalid dates clears only search-owned errors", async () => {
  const h = harness();
  h.run("state.stats={messages:1}");
  h.nodes.get('#filter-after').value='2026-11-10';
  h.nodes.get('#filter-before').value='2026-11-09';
  await h.run('search()');
  assert.equal(h.nodes.get('#global-error').hidden,false);
  assert.equal(h.nodes.get('#export-results').getAttribute('aria-disabled'),'true');
  h.nodes.get('#filter-before').value='2026-11-11';
  h.context.fetch=async()=>response({total:0,messages:[],offset:0,limit:50});
  await h.run('search()');
  assert.equal(h.run('state.searchReady'),true);
  assert.equal(h.nodes.get('#global-error').hidden,true);
  h.run("setError('Unrelated archive failure')");
  await h.run('search()');
  assert.equal(h.nodes.get('#global-error').hidden,false);
  assert.equal(h.nodes.get('#global-error-text').textContent,'Unrelated archive failure');
});

await check("failed pagination keeps the committed page and retries its exact offset", async () => {
  const h = harness(), pending = deferred();
  h.run("bindEvents(); bindReadingRoom(); state.stats={messages:120}; state.offset=0; state.selected=1");
  h.context.fetch = async () => response({total:120,offset:0,limit:50,messages:[{id:1,subject:'Original page'}]});
  await h.run('search()');
  const list=h.nodes.get('#message-list'), reader=h.nodes.get('#reader');
  reader.textContent='Keep the current reader'; list.scrollTop=180;
  const oldPage=h.nodes.get('#page-label').textContent;
  h.context.fetch=()=>pending.promise;
  h.nodes.get('#next-page').click();
  assert.equal(h.run('state.offset'),0);
  assert.equal(list.scrollTop,180);
  pending.resolve(response({error:'Synthetic temporary failure'},503));
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.run('state.offset'),0);
  assert.equal(h.nodes.get('#page-label').textContent,oldPage);
  assert.match(list.textContent,/Original page/);
  assert.equal(reader.textContent,'Keep the current reader');
  const retry=h.nodes.get('#retry-search');
  assert.equal(retry.hidden,false);
  const next=deferred();let retriedPath, retriedRequests=0;
  h.context.fetch=path=>{retriedPath=path;retriedRequests++;return next.promise;};
  retry.focus();retry.click();
  assert.equal(retry.getAttribute('aria-disabled'),'true');
  assert.equal(retry.disabled,false,'A pending retry must retain native keyboard focus');
  retry.click();assert.equal(retriedRequests,1,'Repeated retry must not duplicate the request');
  assert.equal(new URL(retriedPath,'http://test.invalid').searchParams.get('offset'),'50');
  assert.equal(h.run('state.offset'),0);
  next.resolve(response({total:120,offset:50,limit:50,messages:[{id:2,subject:'Second page'}]}));
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.run('state.offset'),50);
  assert.equal(list.scrollTop,0);
  assert.match(list.textContent,/Second page/);
  assert.equal(retry.hidden,true);
  assert.equal(h.nodes.get('#global-error').hidden,true);
  assert.equal(Number(h.document.activeElement.dataset.messageId),2);
});

await check("editing a failed query invalidates its retry before debounce", async () => {
  const h=harness();h.run('bindEvents(); state.stats={messages:1}');
  let requests=0;h.context.fetch=async()=>{requests++;return response({error:'Synthetic failure'},503);};
  await h.run('search()');
  const retry=h.nodes.get('#retry-search');assert.equal(retry.hidden,false);
  h.nodes.get('#search-input').value='Changed query';h.emit(h.nodes.get('#search-input'),'input');
  assert.equal(retry.hidden,true);
  retry.click();assert.equal(requests,1,'Stale retry cannot submit old pagination under new filters');
});

await check("reader races preserve latest selection and mail remains literal text", async () => {
  const h = harness(), first = deferred(), second = deferred(), queue = [first, second];
  h.context.fetch = () => queue.shift().promise;
  const initialResourceNodes = h.created.filter((node) => ["IMG", "SCRIPT", "IFRAME"].includes(node.tagName)).length;
  h.run("state.result = { messages: [] }");
  const oldRead = h.run("readMessage(1)");
  const newRead = h.run("readMessage(2)");
  const dangerous = '<img src="https://tracking.invalid/pixel" onerror="alert(1)">';
  second.resolve(response({ id: 2, subject: dangerous, body: dangerous, warnings: [], attachments: [] }));
  await newRead;
  first.resolve(response({ id: 1, subject: "STALE CONTENT", body: "STALE CONTENT", warnings: [], attachments: [] }));
  await oldRead;
  assert.equal(h.run("state.selected"), 2);
  assert.ok(h.nodes.get("#reader").textContent.includes(dangerous));
  assert.ok(!h.nodes.get("#reader").textContent.includes("STALE CONTENT"));
  assert.equal(h.created.filter((node) => ["IMG", "SCRIPT", "IFRAME"].includes(node.tagName)).length, initialResourceNodes);
});

await check("rapid reader selections skip obsolete waiting requests and recover after failure", async () => {
  const h = harness(), calls = [], pending = new Map();
  h.run("state.result = { messages: [] }");
  h.context.fetch = path => {
    calls.push(path);
    const request = deferred();
    pending.set(path, request);
    return request.promise;
  };
  const reads = [1, 2, 3, 4, 5].map(id => h.run(`readMessage(${id})`));
  assert.deepEqual(calls, ["/api/messages/1", "/api/messages/2"]);
  pending.get("/api/messages/1").resolve(response({ error: "synthetic failure" }, 503));
  await settleUntil(() => calls.length === 3, "Latest selection should start after a failed request");
  assert.deepEqual(calls, ["/api/messages/1", "/api/messages/2", "/api/messages/5"]);
  pending.get("/api/messages/5").resolve(response({ id: 5, subject: "Latest selection", body: "Latest body", warnings: [], attachments: [] }));
  pending.get("/api/messages/2").resolve(response({ id: 2, subject: "Old selection", body: "Old body", warnings: [], attachments: [] }));
  await Promise.all(reads);
  assert.match(h.nodes.get("#reader").textContent, /Latest body/);
  assert.doesNotMatch(h.nodes.get("#reader").textContent, /Old body/);
  assert.equal(h.run("readerRequests.size"), 0);
});

await check("narrow reader exposes Back immediately while a message is loading", async () => {
  const h = harness(), pending = deferred();
  h.run("bindLanguage(); bindReadingRoom(); state.result = { messages: [] }");
  h.context.window.matchMedia("(max-width: 580px)").matches = true;
  h.context.fetch = () => pending.promise;
  const reading = h.run("readMessage(1)");
  const back = h.nodes.get("#reader").querySelector(".reader-back");
  assert.ok(h.document.activeElement === back, "The hidden list row must not retain keyboard focus");
  assert.match(h.nodes.get("#reader").textContent, /Opening message/);
  assert.doesNotMatch(h.nodes.get("#reader").textContent, /reading table is ready/i);
  back.click();
  pending.resolve(response({ id: 1, subject: "Late", body: "Late", warnings: [], attachments: [] }));
  await reading;
  assert.equal(h.document.querySelector(".mail-workspace").classList.contains("reading"), false);
  assert.doesNotMatch(h.nodes.get("#reader").textContent, /Late/);
});

await check("a completed narrow read preserves the user's latest focus", async () => {
  for (const keepBack of [true, false]) {
    const h = harness(), pending = deferred();
    h.run("bindLanguage(); bindReadingRoom(); state.result = { messages: [] }");
    h.context.window.matchMedia("(max-width: 580px)").matches = true;
    h.context.fetch = () => pending.promise;
    const reading = h.run("readMessage(1)");
    const other = h.nodes.get("#search-input");
    if (!keepBack) other.focus();
    pending.resolve(response({ id: 1, subject: "Sample", body: "Safe body", warnings: [], attachments: [] }));
    await reading;
    const newBack = h.nodes.get("#reader").querySelector(".reader-back");
    assert.ok(h.document.activeElement === (keepBack ? newBack : other), "The response must not override newer focus");
    assert.match(h.nodes.get("#reader").textContent, /Safe body/);
  }
});

await check("Back cancels a queued reader selection before it starts", async () => {
  const h = harness(), calls = [], first = deferred(), second = deferred();
  h.run("bindReadingRoom(); state.result = { messages: [] }");
  h.context.window.matchMedia("(max-width: 580px)").matches = true;
  h.context.fetch = path => { calls.push(path); return calls.length === 1 ? first.promise : second.promise; };
  const reads = [1, 2, 3].map(id => h.run(`readMessage(${id})`));
  h.nodes.get("#reader").querySelector(".reader-back").click();
  first.resolve(response({ id: 1, subject: "Old", body: "Old", warnings: [], attachments: [] }));
  second.resolve(response({ id: 2, subject: "Old", body: "Old", warnings: [], attachments: [] }));
  await Promise.all(reads);
  assert.deepEqual(calls, ["/api/messages/1", "/api/messages/2"]);
  assert.equal(h.document.querySelector(".mail-workspace").classList.contains("reading"), false);
  assert.equal(h.run("readerRequests.size"), 0);
});

await check("successful reading clears only its own earlier error", async () => {
  const h = harness();
  h.run("state.result = { messages: [] }");
  h.context.fetch = async () => response({ error: "synthetic read failure" }, 503);
  await h.run("readMessage(1)");
  assert.equal(h.nodes.get("#global-error").hidden, false);
  h.context.fetch = async () => response({ id: 2, subject: "Recovered", body: "Readable", warnings: [], attachments: [] });
  await h.run("readMessage(2)");
  assert.equal(h.nodes.get("#global-error").hidden, true);
  h.run('setError("A different operation failed")');
  await h.run("readMessage(2)");
  assert.equal(h.nodes.get("#global-error").hidden, false);
  assert.match(h.nodes.get("#global-error-text").textContent, /different operation/);
});

await check("reader shows meaningful labels without a redundant default", async () => {
  const h = harness();
  h.run("state.result = { messages: [] }");
  h.context.fetch = async path => response({ id: 1, subject: "Letter", body: "Body", labels: path.endsWith('/2') ? 'Family' : '', warnings: [], attachments: [] });
  await h.run("readMessage(1)");
  assert.doesNotMatch(h.nodes.get("#reader").textContent, /ARCHIVED MESSAGE/);
  assert.match(h.nodes.get("#reader").textContent, /Save original/);
  await h.run("readMessage(2)");
  assert.match(h.nodes.get("#reader").textContent, /Family/);
});

await check("keyboard navigation at list edges does not reload the same mail", async () => {
  const h = harness(), calls = [];
  h.run("bindReadingRoom(); state.searchReady = true; state.result = { messages: [{id: 1, subject: 'First'}, {id: 2, subject: 'Second'}] }; renderList()");
  h.context.fetch = async path => { calls.push(path); return response({ id: 2, subject: 'Second', body: 'Body', warnings: [], attachments: [] }); };
  const list = h.nodes.get("#message-list"), [first, second] = list.children;
  first.focus();
  h.emit(list, "keydown", {key:"ArrowUp"});
  h.emit(list, "keydown", {key:"Home"});
  assert.deepEqual(calls, []);
  h.emit(list, "keydown", {key:"ArrowDown"});
  assert.deepEqual(calls, ["/api/messages/2"]);
  assert.equal(h.document.activeElement, second);
  h.emit(list, "keydown", {key:"End"});
  h.emit(list, "keydown", {key:"ArrowDown"});
  assert.deepEqual(calls, ["/api/messages/2"]);
});

await check("cancelled verification cannot be presented as success", () => {
  const h = harness();
  h.run('renderVerification({cancelled:true, checked:1, total:2, sqlite:"ok", search_index:"ok", mismatches:[]})');
  const text = h.nodes.get("#verify-result").textContent;
  assert.match(text, /stopped/i);
  assert.doesNotMatch(text, /passed its checks/i);
});

await check("verification failure releases busy state and preserves error", async () => {
  const h = harness();
  h.context.fetch = async (path) => {
    if (path === "/api/verify") throw new Error("synthetic network failure");
    if (path === "/api/stats") return response(emptyStats);
    throw new Error(`Unexpected endpoint: ${path}`);
  };
  await h.run("startVerify()");
  assert.equal(h.run("state.busy"), false);
  assert.equal(h.run("state.job"), null);
  assert.equal(h.nodes.get("#verify-button").disabled, false);
  assert.match(h.nodes.get("#global-error-text").textContent, /Cannot reach/i);
});

await check("cancel during job creation is forwarded before polling", async () => {
  const h = harness(), started = deferred(), calls = [];
  h.context.fetch = async (path) => {
    calls.push(path);
    if (path === "/api/verify") return started.promise;
    if (path === "/api/jobs/pending/cancel") return response({ ok: true });
    if (path === "/api/jobs/pending") return response({ status: "done", result: { cancelled: true, total: 1, checked: 0, sqlite: "ok", search_index: "ok", mismatches: [] } });
    if (path === "/api/stats") return response(emptyStats);
    throw new Error(`Unexpected endpoint: ${path}`);
  };
  const job = h.run("startVerify()");
  await h.run("cancelJob()");
  started.resolve(response({ job_id: "pending" }, 202));
  await job;
  assert.ok(calls.indexOf("/api/jobs/pending/cancel") < calls.indexOf("/api/jobs/pending"));
  assert.equal(h.run("state.busy"), false);
  assert.match(h.nodes.get("#verify-result").textContent, /stopped/i);
});

await check("receipt failures prevent a green verification result", () => {
  const h = harness();
  h.run('renderVerification({cancelled:false, checked:2, total:2, sqlite:"ok", search_index:"ok", receipts:"ok", mismatches:[]})');
  assert.match(h.nodes.get("#verify-result").textContent, /passed its checks/i);
  h.run('renderVerification({cancelled:false, checked:2, total:2, sqlite:"ok", search_index:"ok", receipts:"failed", mismatches:[]})');
  assert.doesNotMatch(h.nodes.get("#verify-result").textContent, /passed its checks/i);
  assert.match(h.nodes.get("#verify-result").textContent, /receipts.*failed|records are inconsistent/i);
});

await check("corrupt preferences fall back and unrecognized values are discarded", () => {
  const h = harness();
  h.context.localStorage.getItem = () => "{broken JSON";
  assert.equal(h.run("JSON.stringify(loadPreferences())"), h.run("JSON.stringify(preferenceDefaults)"));
  h.context.localStorage.getItem = () => JSON.stringify({ theme: "dark", accent: "invalid", motion: "false", density: "compact", mail: "never persist this" });
  const clean = JSON.parse(h.run("JSON.stringify(loadPreferences())"));
  assert.equal(clean.theme, "dark");
  assert.equal(clean.accent, "cedar");
  assert.equal(clean.motion, true);
  assert.equal(clean.density, "compact");
  assert.ok(!Object.hasOwn(clean, "mail"));
});

await check("reduced motion and unavailable storage still leave preferences usable", () => {
  const h = harness();
  h.context.localStorage.setItem = () => { throw new Error("storage disabled"); };
  h.run('preferences = validatedPreferences({ theme: "dark", motion: true }); reducedMedia.matches = true; applyPreferences({save:true})');
  assert.equal(h.document.documentElement.dataset.theme, "dark");
  assert.equal(h.document.documentElement.dataset.motion, "off");
  assert.match(h.nodes.get("#preference-status").textContent, /storage unavailable/i);
  h.run("unfoldArchive(); illuminateArchive()");
  assert.equal(h.frames.size, 0, "Reduced motion must block natural entrance effects");
  assert.equal(h.timers.size, 0);
});


await check("natural archive entrance keeps one frame chain and finishes without residual work", () => {
  const h = harness(), canvas = h.nodes.get("#archive-light");
  h.run("bindReadingRoom()");
  h.run("state.stats = {messages: 0}; setView('archive')");
  assert.equal(h.frames.size, 1);
  h.advance(); h.advance();
  assert.ok(canvas.draws.paints > 0, "An enabled effect should draw");
  h.run("illuminateArchive()");
  assert.equal(h.frames.size, 1, "Repeated entrance notification must not fork the frame chain");
  for (let i = 0; i < 120; i++) h.advance(100);
  assert.equal(h.frames.size, 0, "The finite effect should release its scheduled work");
  const paints = canvas.draws.paints;
  h.advance(1000);
  assert.equal(canvas.draws.paints, paints);
});

await check("visibility, resize, dialog close and viewport exit release active effects", () => {
  for (const boundary of ["visibility", "resize", "close", "intersection"]) {
    const h = harness(), canvas = h.nodes.get("#import-light");
    h.run("bindReadingRoom()");
    const dialog = h.nodes.get("#import-dialog");
    dialog.showModal();
    h.run("appendOutcome({id: 1, status: 'complete', added: 1, duplicates: 0, skipped: 0}, 'fixture.eml')");
    h.advance();
    assert.ok(canvas.draws.paints > 0, `${boundary}: test must start a drawing effect`);
    const clears = canvas.draws.clears, paints = canvas.draws.paints;
    if (boundary === "visibility") { h.document.hidden = true; h.emit(h.document, "visibilitychange"); }
    if (boundary === "resize") h.emit(h.context.window, "resize");
    if (boundary === "close") dialog.close();
    if (boundary === "intersection") {
      const observer = h.observers.find((item) => item.targets.includes(canvas));
      assert.ok(observer, "Canvas must be observed for viewport exit");
      observer.callback([{ target: canvas, isIntersecting: false }]);
    }
    assert.equal(h.frames.size, 0, `${boundary}: frame chain must stop immediately`);
    assert.ok(canvas.draws.clears > clears, `${boundary}: last canvas frame must be cleared`);
    h.advance();
    assert.equal(canvas.draws.paints, paints, `${boundary}: stopped effect must not draw again`);
  }
});

await check("live reduced motion and cross-tab preferences stop effects without overwriting user choice", () => {
  const h = harness(), canvas = h.nodes.get("#archive-light");
  h.run("bindReadingRoom()");
  h.run("state.stats = {messages: 0}; illuminateArchive()");
  h.advance(); h.advance();
  const reduced = h.media.get("(prefers-reduced-motion: reduce)");
  reduced.matches = true;
  h.emit(reduced, "change");
  assert.equal(h.frames.size, 0);
  assert.equal(h.document.documentElement.dataset.motion, "off");
  assert.equal(h.nodes.get("#motion-preference").checked, true, "OS preference must not erase the user's chosen setting");
  const paints = canvas.draws.paints;
  h.run("playLight($('#archive-light'), 'archive')");
  h.advance();
  assert.equal(canvas.draws.paints, paints, "Reduced motion must prevent new drawing");
  reduced.matches = false;
  h.emit(reduced, "change");
  assert.equal(h.document.documentElement.dataset.motion, "on");
  assert.equal(h.frames.size, 0, "Restoring motion should not auto-replay a completed interaction");
  h.run("playLight($('#archive-light'), 'archive')");
  h.advance();
  h.storage.set("mailcairn.reading-room.v1", JSON.stringify({ motion: false }));
  h.emit(h.context.window, "storage", { key: "mailcairn.reading-room.v1" });
  assert.equal(h.document.documentElement.dataset.motion, "off");
  assert.equal(h.nodes.get("#motion-preference").checked, false);
  assert.equal(h.frames.size, 0);
  h.run("playLight($('#archive-light'), 'archive')");
  assert.equal(h.frames.size, 0, "A disabled preference must prevent new drawing");
  h.storage.clear();
  h.emit(h.context.window, "storage", { key: null });
  assert.equal(h.nodes.get("#motion-preference").checked, true, "Cross-tab clearing restores valid defaults");
});


await check("rich light is saved, finite, bounded and subordinate to reduced motion", () => {
  const h = harness(), canvas=h.nodes.get('#archive-light');
  h.run("bindReadingRoom(); preferences=validatedPreferences({atmosphere:'full'}); applyPreferences({save:true})");
  assert.equal(JSON.parse(h.storage.get('mailcairn.reading-room.v1')).atmosphere,'full');
  canvas.bounds={left:0,top:0,width:3840,height:2160};
  let arcs=0;
  canvas.context2d.arc=()=>{arcs++};
  h.run("playLight($('#archive-light'))");
  assert.ok(canvas.width*canvas.height<=1500000);
  h.advance();
  assert.equal(arcs,64,'Rich mode must remain within its per-frame particle budget');
  const paints=canvas.draws.paints;
  h.advance(5);
  assert.equal(canvas.draws.paints,paints,'Rich mode must retain draw throttling');
  for(let i=0;i<49;i++)h.advance(100);
  assert.equal(h.frames.size,0,'Rich opening must finish within five seconds');
  h.run("reducedMedia.matches=true; applyPreferences(); playLight($('#archive-light'))");
  assert.equal(h.frames.size,0);
  assert.equal(h.run('preferences.atmosphere'),'full','System reduction must preserve the saved choice');
});

await check("import feedback uses bounded drawing and releases its frame chain", () => {
  const h = harness(), canvas = h.nodes.get("#import-light"), dialog = h.nodes.get("#import-dialog");
  h.run("bindReadingRoom()");
  canvas.bounds = { left: 0, top: 0, width: 3840, height: 2160 };
  h.nodes.get("#import-dialog").showModal();
    h.run("appendOutcome({id: 1, status: 'complete', added: 1, duplicates: 0, skipped: 0}, 'fixture.eml')");
  assert.equal(dialog.open, true);
  assert.ok(canvas.width * canvas.height <= 1500000, "High-DPI canvas must respect the pixel budget");
  h.advance();
  assert.ok(canvas.draws.paints > 0);
  const painted = canvas.draws.paints;
  h.advance(5);
  assert.equal(canvas.draws.paints, painted, "Fast RAF callbacks must not force unthrottled canvas painting");
  for (let i = 0; i < 100; i++) h.advance(100);
  assert.equal(h.frames.size, 0, "Finite success feedback releases all work");
  assert.deepEqual(canvas.draws.clearTransform, [1, 0, 0, 1, 0, 0], "Stopping clears the full backing canvas");
});

await check("import feedback stops at lifecycle boundaries and respects disabled motion", () => {
  for (const boundary of ["close", "visibility", "resize", "reduced-motion", "motion-off", "view-change"]) {
    const h = harness(), canvas = h.nodes.get("#import-light");
    h.run("bindReadingRoom()");
    h.nodes.get("#import-dialog").showModal();
    h.run("appendOutcome({id: 1, status: 'complete', added: 1, duplicates: 0, skipped: 0}, 'fixture.eml')");
    h.advance();
    assert.ok(canvas.draws.paints > 0, `${boundary}: scene should begin playing`);
    if (boundary === "close") h.nodes.get("#import-dialog").close();
    if (boundary === "visibility") { h.document.hidden = true; h.emit(h.document, "visibilitychange"); }
    if (boundary === "resize") h.emit(h.context.window, "resize");
    if (boundary === "reduced-motion") { const media = h.media.get("(prefers-reduced-motion: reduce)"); media.matches = true; h.emit(media, "change"); }
    if (boundary === "motion-off") h.emit(h.nodes.get("#preferences-form"), "change", { target: { name: "motion", type: "checkbox", checked: false } });
    if (boundary === "view-change") h.run('setView("guide")');
    assert.equal(h.frames.size, 0, `${boundary}: no scheduled work should remain`);
  }
  for (const key of ["reduced-motion", "motion-off"]) {
    const h = harness();
    if (key === "reduced-motion") h.media.get("(prefers-reduced-motion: reduce)").matches = true;
    else h.storage.set("mailcairn.reading-room.v1", JSON.stringify({ motion: false }));
    h.run("bindReadingRoom()");
    h.nodes.get("#import-dialog").showModal();
    h.run("appendOutcome({id: 1, status: 'complete', added: 1, duplicates: 0, skipped: 0}, 'fixture.eml')");
    assert.equal(h.nodes.get("#import-dialog").open, true, "The receipt remains accessible without motion");
    assert.equal(h.frames.size, 0);
  }
});

await check("pointer tilt is mouse-only and resets on cancellation and reduced motion", () => {
  const h = harness();
  h.run("bindReadingRoom()");
  const paper = h.created.find((node) => node.attributes.has("data-paper-surface"));
  const move = (pointerType) => h.emit(paper, "pointermove", { pointerType, clientX: 700, clientY: 100 });
  move("touch");
  assert.equal(h.frames.size, 0);
  move("mouse");
  move("mouse");
  assert.equal(h.frames.size, 1, "Pointer bursts should share one pending update");
  h.advance();
  assert.notEqual(paper.style.getPropertyValue("--tilt-x"), "0deg");
  move("mouse");
  h.emit(paper, "pointercancel");
  assert.equal(h.frames.size, 0);
  assert.equal(paper.style.getPropertyValue("--tilt-x"), "0deg");
  assert.equal(paper.style.getPropertyValue("--pointer-x"), "50%");
  move("mouse");
  const media = h.media.get("(prefers-reduced-motion: reduce)");
  media.matches = true;
  h.emit(media, "change");
  assert.equal(h.frames.size, 0);
  assert.equal(paper.style.getPropertyValue("--tilt-y"), "0deg");
  move("mouse");
  assert.equal(h.frames.size, 0);
});


await check("an unrelated dialog close cannot stop active import feedback", () => {
  const h = harness();
  h.run("bindReadingRoom()");
  h.nodes.get("#import-dialog").showModal();
  h.run("appendOutcome({id: 1, status: 'complete', added: 1, duplicates: 0, skipped: 0}, 'fixture.eml')");
  h.advance();
  const canvas = h.nodes.get("#import-light"), painted = canvas.draws.paints;
  h.emit(h.nodes.get("#command-dialog"), "close");
  assert.equal(h.frames.size, 1, "A queued close event belongs only to the dialog being closed");
  h.advance();
  assert.ok(canvas.draws.paints > painted);
  h.nodes.get("#import-dialog").close();
  assert.equal(h.frames.size, 0);
});

await check("paper entrance restarts safely and finishes without idle work", () => {
  const h = harness();
  h.run("bindReadingRoom()");
  const paper = h.document.querySelector(".archive-object");
  h.run("unfoldArchive()");
  assert.equal(paper.classList.contains("paper-unfolding"), true);
  assert.equal(h.timers.size, 1);
  h.advance(1400);
  h.run("unfoldArchive()");
  assert.equal(h.timers.size, 1, "Repeated replay must replace the entrance timer");
  h.advance(1200);
  assert.equal(paper.classList.contains("paper-unfolding"), true, "The prior timer must not cut short a replay");
  h.advance(1500);
  assert.equal(paper.classList.contains("paper-unfolding"), false);
  assert.equal(h.timers.size, 0);
  h.advance(9000);
  assert.equal(h.frames.size, 0);
});

await check("paper entrance stops on lifecycle changes and cannot start with motion disabled", () => {
  for (const boundary of ["visibility", "resize", "view-change", "reduced-motion", "motion-off"]) {
    const h = harness();
    h.run("bindReadingRoom()");
    const paper = h.document.querySelector(".archive-object");
    h.run("unfoldArchive()");
    assert.equal(paper.classList.contains("paper-unfolding"), true);
    if (boundary === "visibility") { h.document.hidden = true; h.emit(h.document, "visibilitychange"); }
    if (boundary === "resize") h.emit(h.context.window, "resize");
    if (boundary === "view-change") h.run('setView("guide")');
    if (boundary === "reduced-motion") { const media = h.media.get("(prefers-reduced-motion: reduce)"); media.matches = true; h.emit(media, "change"); }
    if (boundary === "motion-off") h.emit(h.nodes.get("#preferences-form"), "change", { target: { name: "motion", type: "checkbox", checked: false } });
    assert.equal(paper.classList.contains("paper-unfolding"), false, `${boundary}: entrance must stop`);
    assert.equal(h.timers.has(h.run("paperUnfoldTimer")), false, `${boundary}: entrance timer must be released`);
    h.advance(1000);
    assert.equal(h.timers.size, 0, `${boundary}: finite destination transition must also finish`);
    if (["reduced-motion", "motion-off"].includes(boundary)) {
      h.run("unfoldArchive()");
      assert.equal(paper.classList.contains("paper-unfolding"), false);
      assert.equal(h.timers.size, 0);
    }
  }
});

await check("navigation marker follows active destination and changes axis at the narrow breakpoint", () => {
  const h = harness();
  h.run("bindReadingRoom()");
  const nav = h.document.querySelector(".nav-list"), marker = h.document.querySelector(".nav-marker");
  const guide = h.created.find((node) => node.dataset.view === "guide");
  nav.bounds = { left: 20, top: 30, width: 200, height: 200 };
  guide.bounds = { left: 20, top: 150, width: 190, height: 48 };
  const focused = h.document.activeElement;
  h.run('setView("guide")');
  assert.equal(guide.getAttribute("aria-current"), "page");
  assert.equal(marker.getAttribute("aria-hidden"), "true", "Marker must not create an extra accessibility stop");
  assert.equal(marker.style.getPropertyValue("transform"), "translate(0px, 132px)");
  assert.equal(marker.style.getPropertyValue("width"), "3px");
  assert.equal(marker.style.getPropertyValue("height"), "24px");
  h.media.get("(max-width: 760px)").matches = true;
  h.emit(h.context.window, "resize");
  assert.equal(marker.style.getPropertyValue("transform"), "translate(16px, 165px)");
  assert.equal(marker.style.getPropertyValue("width"), "158px");
  assert.equal(marker.style.getPropertyValue("height"), "3px");
  assert.equal(h.document.activeElement, focused, "Decorative navigation motion must not steal keyboard focus");
  assert.equal(h.frames.size, 0, "Navigation marker must not leave an idle RAF loop");
});

await check("result arrival is bounded, immediately readable, and does not resume after reduced motion", async () => {
  const h = harness();
  h.run("bindReadingRoom()");
  h.run("state.stats = { messages: 50 }");
  const messages = Array.from({ length: 50 }, (_, index) => ({
    id: index + 1, sender: `Sender ${index + 1}`, subject: `Synthetic letter ${index + 1}`,
    snippet: `Message preview ${index + 1}`, attachment_count: 0,
  }));
  h.context.fetch = async () => response({ total: 50, messages, offset: 0, limit: 50 });
  await h.run("search()");
  const rows = h.nodes.get("#message-list").children;
  assert.equal(rows.length, 50, "Entrance must not defer result creation");
  assert.equal(rows.filter((row) => row.classList.contains("result-arriving")).length, 8);
  assert.ok(rows.every((row, index) => row.textContent.includes(messages[index].subject)));
  assert.ok(rows.every((row) => row.tagName === "BUTTON" && !row.disabled), "All results must remain actionable during arrival");
  h.emit(rows[0], "animationend");
  assert.equal(rows[0].classList.contains("result-arriving"), false);
  const reduced = h.media.get("(prefers-reduced-motion: reduce)");
  reduced.matches = true;
  h.emit(reduced, "change");
  assert.ok(rows.every((row) => !row.classList.contains("result-arriving")), "Live OS setting must clear entrance state");
  reduced.matches = false;
  h.emit(reduced, "change");
  assert.ok(rows.every((row) => !row.classList.contains("result-arriving")), "Restoring motion must not replay old results");
  h.emit(h.nodes.get("#preferences-form"), "change", { target: { name: "motion", type: "checkbox", checked: false } });
  await h.run("search()");
  assert.ok(h.nodes.get("#message-list").children.every((row) => !row.classList.contains("result-arriving")));
  assert.equal(h.frames.size, 0, "Result arrival must not create an idle JS animation loop");
});

await check("background arrival animates only new rows and preserves reading context", async () => {
  const h = harness();
  h.run("bindReadingRoom(); state.stats = { messages: 3 }; state.selected = 2; state.searchReady = true");
  const old = [1, 2, 3].map(id => ({ id, sender: 'Synthetic sender', subject: `Letter ${id}`, snippet: 'Safe text' }));
  h.context.seedRows = old;
  h.run("state.result = {messages: seedRows}; renderList()");
  const list = h.nodes.get("#message-list");
  list.children[1].focus(); list.scrollTop = 120;
  h.nodes.get("#reader").textContent = "Already reading letter 2";
  const refreshed = [old[0], {id: 4, subject: 'New letter'}, old[1], {id: 5, subject: 'Another new letter'}, old[2]];
  h.context.fetch = async () => response({total: 5, messages: refreshed, offset: 0, limit: 50});
  await h.run("search(false, {preserveSelection: true})");
  const animated = list.children.filter(row => row.classList.contains("result-arriving"));
  assert.deepEqual(animated.map(row => Number(row.dataset.messageId)), [4, 5]);
  assert.deepEqual(animated.map(row => Number(row.style.getPropertyValue("--arrival-order"))), [0, 1]);
  assert.equal(Number(h.document.activeElement.dataset.messageId), 2);
  assert.equal(list.scrollTop, 120);
  assert.equal(h.nodes.get("#reader").textContent, "Already reading letter 2");
  await h.run("search(false, {preserveSelection: true})");
  assert.ok(list.children.every(row => !row.classList.contains("result-arriving")), "Unchanged sync must not replay entrance");
  await h.run("search()");
  assert.equal(list.children.filter(row => row.classList.contains("result-arriving")).length, 5, "Deliberate search retains its own arrival");
});

const liveFlights = (h) => h.document.body.children.filter((node) => node.classList.contains("message-flight"));
const runningAnimations = (h) => h.animations.filter((animation) => animation.playState === "running");
function motionBoundary(h, boundary, restore = false) {
  if (boundary === "visibility") { h.document.hidden = !restore; h.emit(h.document, "visibilitychange"); }
  if (boundary === "resize") h.emit(h.context.window, "resize");
  if (boundary === "view-change") h.run(`setView("${restore ? "archive" : "guide"}")`);
  if (boundary === "reduced-motion") { const media = h.media.get("(prefers-reduced-motion: reduce)"); media.matches = !restore; h.emit(media, "change"); }
  if (boundary === "motion-off") h.emit(h.nodes.get("#preferences-form"), "change", { target: { name: "motion", type: "checkbox", checked: restore } });
}

await check("reader flight follows selection without copying mail and stale completions cannot end its replacement", async () => {
  const h = harness(), pending = deferred();
  h.run("bindReadingRoom(); state.result = { messages: [{id: 1, subject: 'First'}, {id: 2, subject: 'Second'}] }; renderList()");
  const [firstRow, secondRow] = h.nodes.get("#message-list").children;
  firstRow.bounds = { left: 0, top: 150, width: 250, height: 60 };
  secondRow.bounds = { left: 0, top: 250, width: 250, height: 60 };
  const reader = h.nodes.get("#reader");
  reader.bounds = { left: 300, top: 100, width: 600, height: 700 };
  h.context.fetch = async (path) => path.endsWith("/2") ? pending.promise : response({ id: 1, subject: "First", body: "First literal body", attachments: [], warnings: [] });
  firstRow.focus();
  await h.run("readMessage(1)");
  const first = h.animations.find((animation) => animation.target === reader);
  assert.equal(first.keyframes[0].transformOrigin, "0px 80px", "Hinge follows the selected row midpoint");
  const firstFlight = liveFlights(h)[0], firstFlightAnimation = h.animations.find((animation) => animation.target === firstFlight);
  assert.ok(firstFlight, "A selected message should have one decorative flight");
  assert.equal(liveFlights(h).length, 1);
  assert.equal(firstFlight.getAttribute("aria-hidden"), "true");
  assert.equal(firstFlight.textContent, "", "Decorative paper must never duplicate private mail");
  assert.equal(firstFlight.tagName, "DIV");
  assert.ok(firstFlightAnimation.options.duration > 0 && firstFlightAnimation.options.duration < 1500, "Flight must have a finite interaction-sized duration");
  assert.equal(h.document.activeElement, firstRow, "Desktop reader motion must not steal row focus");
  assert.match(reader.textContent, /First literal body/);
  const next = h.run("readMessage(2, false)");
  assert.equal(first.playState, "idle", "Prior animation must cancel before the next fetch completes");
  assert.equal(firstFlightAnimation.playState, "idle");
  assert.equal(liveFlights(h).length, 0, "Changing selection must remove the old flight immediately");
  assert.equal(reader.classList.contains("reader-opening"), false);
  pending.resolve(response({ id: 2, subject: "Second", body: "Second literal body", attachments: [], warnings: [] }));
  await next;
  const second = h.animations.findLast((animation) => animation.target === reader), created = h.created.length;
  const secondFlight = liveFlights(h)[0];
  const children = [...reader.children];
  assert.equal(second.keyframes[0].transformOrigin, "0px 180px");
  assert.equal(runningAnimations(h).length, 2, "Only the new hinge and paper flight should run");
  first.onfinish();
  firstFlightAnimation.onfinish();
  assert.equal(reader.classList.contains("reader-opening"), true, "Late finish must not clear the next entrance");
  assert.deepEqual(liveFlights(h), [secondFlight], "Late flight completion must not remove its replacement");
  h.advance(1500);
  assert.equal(second.playState, "finished");
  assert.equal(reader.classList.contains("reader-opening"), false);
  assert.equal(h.run("readerOpening"), null);
  assert.equal(h.run("readerFlight"), null);
  assert.equal(liveFlights(h).length, 0);
  assert.equal(runningAnimations(h).length, 0);
  assert.equal(h.frames.size, 0);
  assert.equal(h.timers.size, 0);
  assert.deepEqual(reader.children, children, "Completion must preserve live content and controls");
  assert.equal(h.created.length, created, "Motion must not clone or rebuild mail content");
  assert.match(reader.textContent, /Second literal body/);
  assert.doesNotMatch(reader.textContent, /First literal body/);
});

await check("decorative paper travels from the selected row to the visible message body and skips missing geometry", () => {
  for (const scenario of ["visible", "source-offscreen", "source-left-offscreen", "source-right-offscreen", "body-offscreen", "body-missing"]) {
    const h = harness();
    h.run("bindReadingRoom()");
    const reader = h.nodes.get("#reader"), body = h.document.createElement("pre");
    body.className = "reader-body";
    body.bounds = { left: 380, top: scenario === "body-offscreen" ? 900 : 280, width: 500, height: 400 };
    if (scenario !== "body-missing") reader.append(body);
    const sourceLeft = scenario === "source-left-offscreen" ? -300 : scenario === "source-right-offscreen" ? 1300 : 20;
    h.run(`openReaderPage({left:${sourceLeft}, top:${scenario === "source-offscreen" ? 900 : 140}, width:250, height:60, right:${sourceLeft + 250}, bottom:${scenario === "source-offscreen" ? 960 : 200}})`);
    if (scenario === "visible") {
      const flight = liveFlights(h)[0], animation = h.animations.find((item) => item.target === flight);
      assert.equal(flight.style.left, "20px");
      assert.equal(flight.style.top, "140px");
      assert.match(animation.keyframes.at(-1).transform, /translate3d\(395px,154px,0\)/, "Landing position must follow message-body geometry below the header");
      assert.equal(animation.keyframes.at(-1).opacity, 0, "The overlay must reveal the live text by completion");
    } else assert.equal(liveFlights(h).length, 0, `${scenario}: absent viewport geometry must not create a stray paper`);
    h.advance(1500);
    assert.equal(liveFlights(h).length, 0);
    assert.equal(runningAnimations(h).length, 0);
  }
});

await check("reader page motion cancels at lifecycle boundaries without removing mail or focus", () => {
  for (const boundary of ["visibility", "resize", "view-change", "reduced-motion", "motion-off"]) {
    const h = harness();
    h.run("bindReadingRoom()");
    const reader = h.nodes.get("#reader");
    const body = h.document.createElement("pre");
    body.className = "reader-body";
    body.textContent = "Preserve the real message";
    reader.replaceChildren(body);
    reader.focus();
    h.run("openReaderPage({left:0, top:120, width:250, height:60, right:250, bottom:180})");
    const animations = runningAnimations(h);
    assert.equal(animations.length, 2);
    motionBoundary(h, boundary);
    assert.ok(animations.every((animation) => animation.playState === "idle"), `${boundary}: both animations must cancel`);
    assert.equal(h.run("readerOpening"), null);
    assert.equal(h.run("readerFlight"), null);
    assert.equal(liveFlights(h).length, 0);
    assert.equal(reader.classList.contains("reader-opening"), false);
    assert.equal(reader.textContent, "Preserve the real message");
    assert.equal(h.document.activeElement, reader);
    h.advance(1000);
    assert.equal(runningAnimations(h).length, 0);
  }
});

await check("reader remains usable with unavailable animation APIs, reduced motion or disabled motion", async () => {
  for (const boundary of ["unsupported", "reduced-motion", "motion-off"]) {
    const h = harness();
    h.run("bindReadingRoom()");
    const reader = h.nodes.get("#reader");
    if (boundary === "unsupported") reader.animate = undefined;
    else motionBoundary(h, boundary);
    h.context.fetch = async () => response({ id: 3, subject: "A still page", body: "Always readable", attachments: [], warnings: [] });
    await h.run("readMessage(3)");
    assert.match(reader.textContent, /Always readable/);
    assert.equal(h.animations.length, 0);
    assert.equal(reader.classList.contains("reader-opening"), false);
    assert.equal(h.run("readerOpening"), null);
    assert.equal(h.run("readerFlight"), null);
    assert.equal(liveFlights(h).length, 0);
  }
});

await check("a lifecycle cancellation during fetch cannot resurrect motion after the boundary is restored", async () => {
  for (const boundary of ["visibility", "resize", "view-change", "reduced-motion", "motion-off"]) {
    const h = harness(), pending = deferred();
    h.run("bindReadingRoom(); state.result = { messages: [{id: 1, subject: 'Delayed'}] }; renderList()");
    h.context.fetch = () => pending.promise;
    const reading = h.run("readMessage(1)");
    motionBoundary(h, boundary);
    motionBoundary(h, boundary, true);
    pending.resolve(response({ id: 1, subject: "Delayed", body: "Fetched mail remains available", attachments: [], warnings: [] }));
    await reading;
    assert.match(h.nodes.get("#reader").textContent, /Fetched mail remains available/);
    assert.equal(h.animations.length, 0, `${boundary}: late response must not replay a cancelled interaction`);
    assert.equal(liveFlights(h).length, 0);
    assert.equal(h.frames.size, 0);
    h.advance(1000); // A deliberate destination change may have its own finite CSS transition.
    assert.equal(h.timers.size, 0);
  }
});

await check("mobile Back cancels a pending read without later reopening it, changing focus or starting motion", async () => {
  const h = harness(), pending = deferred();
  h.run("bindReadingRoom(); state.result = { messages: [{id: 1, subject: 'Delayed'}] }; renderList()");
  h.context.window.matchMedia("(max-width: 580px)").matches = true;
  h.context.fetch = () => pending.promise;
  const reading = h.run("readMessage(1)");
  const back = h.nodes.get("#reader").querySelector(".reader-back");
  assert.ok(back, "Loading reader must already offer a way back");
  back.click();
  const focused = h.document.activeElement;
  assert.equal(h.document.querySelector(".mail-workspace").classList.contains("reading"), false);
  pending.resolve(response({ id: 1, subject: "Late response", body: "Do not reopen this mail", attachments: [], warnings: [] }));
  await reading;
  assert.equal(h.document.querySelector(".mail-workspace").classList.contains("reading"), false);
  assert.equal(h.document.activeElement, focused);
  assert.doesNotMatch(h.nodes.get("#reader").textContent, /Do not reopen this mail/);
  assert.equal(h.animations.length, 0);
  assert.equal(liveFlights(h).length, 0);
});

async function settleUntil(predicate, message) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (predicate()) return;
    await Promise.resolve();
  }
  assert.ok(predicate(), message);
}

function importFixture({ count = 1, failRefresh = false, status = "complete" } = {}) {
  const h = harness(), secondUpload = deferred();
  let uploads = 0, refreshes = 0, failedRefresh = false;
  const committed = [], requests = [];
  const runs = Array.from({ length: count }, (_, index) => ({ id: index + 11, name: `fixture-${index + 1}.eml`, size: 100, status, total: 1, added: 1, duplicates: 0, skipped: 0, started: "2026-11-09T12:00:00Z" }));
  h.context.files = runs.map(run => ({ name: run.name, size: run.size }));
  h.context.fakeUpload = async () => { uploads++; return uploads === 2 ? secondUpload.promise : { job_id: uploads }; };
  h.context.fetch = async path => {
    requests.push(path);
    if (path === "/api/stats") {
      refreshes++;
      if (failRefresh && committed.length && !failedRefresh) { failedRefresh = true; throw new Error("Disconnected after commit"); }
      return response({ ...emptyStats, messages: committed.length, raw_bytes: committed.length * 100, imports: runs.slice(0, committed.length) });
    }
    if (path.startsWith("/api/jobs/") && path.endsWith("/cancel")) return response({ cancelled: true });
    if (path.startsWith("/api/jobs/")) {
      const index = Number(path.split("/")[3]) - 1;
      committed.push({ id: index + 1, sender: "Synthetic sender", subject: `Saved mail ${index + 1}`, snippet: "Original literal text", attachment_count: 0 });
      return response({ status: "complete", result: runs[index] });
    }
    if (path.startsWith("/api/messages?")) return response({ messages: [...committed], total: committed.length, offset: 0, limit: 50 });
    throw new Error(`Unexpected fixture request: ${path}`);
  };
  h.run("bindLanguage(); bindEvents(); bindReadingRoom(); upload = fakeUpload");
  return { h, runs, requests, secondUpload, get uploads() { return uploads; }, get refreshes() { return refreshes; } };
}

await check("first imported mail appears before a multi-file queue finishes without a page reload", async () => {
  const fixture = importFixture({ count: 2 }), { h } = fixture;
  await h.run("refreshStats()");
  assert.equal(h.nodes.get("#empty-archive").hidden, false);
  const importing = h.run("startImport(files)");
  await settleUntil(() => fixture.uploads === 2, "Second upload should start after the first receipt");
  assert.equal(h.run("state.busy"), true);
  assert.equal(h.nodes.get("#empty-archive").hidden, true);
  assert.equal(h.nodes.get("#archive-workspace").hidden, false);
  assert.equal(h.nodes.get("#nav-count").textContent, "1");
  assert.match(h.nodes.get("#message-list").textContent, /Saved mail 1/);
  assert.equal(h.run("state.result.total"), 1);
  assert.equal(h.nodes.get("#view-imported-mail").disabled, true, "Review cannot interrupt an unfinished queue");
  fixture.secondUpload.resolve({ job_id: 2 }); await importing;
  assert.equal(h.run("state.busy"), false);
  assert.equal(h.run("state.result.total"), 2);
  assert.match(h.nodes.get("#message-list").textContent, /Saved mail 2/);
  assert.equal(h.nodes.get("#nav-count").textContent, "2");
  assert.equal(h.nodes.get("#view-imported-mail").hidden, false);
  assert.match(h.nodes.get("#view-imported-mail").textContent, /View mail/);
});

await check("background import completion keeps the current reader when new mail displaces it from the page", async () => {
  for (const narrow of [false, true]) {
    const h = harness(), uploadPending = deferred();
    const old = Array.from({ length: 50 }, (_, i) => ({ id: i + 1, subject: `Old letter ${i + 1}`, sender: "Fixture" }));
    const run = { id: 11, name: "incoming.eml", size: 100, status: "complete", total: 1, added: 1, duplicates: 0, skipped: 0 };
    let committed = false;
    h.context.window.matchMedia("(max-width: 580px)").matches = narrow;
    h.context.window.matchMedia("(min-width: 581px)").matches = !narrow;
    h.context.fakeUpload = () => uploadPending.promise;
    h.context.fetch = async path => {
      if (path === "/api/stats") return response({ ...emptyStats, messages: committed ? 51 : 50, imports: committed ? [run] : [] });
      if (path.startsWith("/api/jobs/")) { committed = true; return response({ status: "complete", result: run }); }
      if (path.startsWith("/api/messages?")) return response({ total: committed ? 51 : 50, offset: 0, limit: 50, messages: committed ? [{ id: 51, subject: "Incoming", sender: "Fixture" }, ...old.slice(0, 49)] : old });
      const match = path.match(/^\/api\/messages\/(\d+)$/);
      if (match) return response({ id: Number(match[1]), subject: `Letter ${match[1]}`, body: `Body ${match[1]}`, attachments: [], warnings: [] });
      throw new Error(`Unexpected request: ${path}`);
    };
    h.run("bindLanguage(); bindEvents(); bindReadingRoom(); upload = fakeUpload");
    await h.run("refreshStats()");
    await h.run("search()");
    const importing = h.run("startImport([{name:'incoming.eml',size:100}])");
    h.nodes.get("#import-dialog").close();
    await h.run("readMessage(50)");
    h.nodes.get("#message-list").querySelectorAll(".message-row")[49].focus();
    const reader = h.nodes.get("#reader");
    reader.scrollTop = 127;
    const wasReading = h.document.querySelector(".mail-workspace").classList.contains("reading");
    uploadPending.resolve({ job_id: 1 }); await importing;
    assert.equal(h.run("state.selected"), 50, `${narrow ? "Narrow" : "Desktop"}: keep the current mail`);
    assert.match(reader.textContent, /Body 50/);
    assert.equal(reader.scrollTop, 127);
    assert.equal(h.document.activeElement === reader, true, "If the focused row leaves the page, keep focus with the preserved reader");
    assert.equal(h.document.querySelector(".mail-workspace").classList.contains("reading"), wasReading);
    assert.equal(h.run("state.result.total"), 51);
    assert.match(h.nodes.get("#message-list").textContent, /Incoming/);
    assert.equal(h.nodes.get("#message-list").querySelectorAll(".result-arriving").length, 0, "Final unchanged refresh must not replay old rows");
  }
});

await check("history and receipt browsing focus the destination immediately without late search focus theft", async () => {
  for (const receipt of [false, true]) {
    const { h, runs } = importFixture();
    await h.run("refreshStats()");
    await h.run("startImport(files)");
    h.nodes.get("#import-dialog").close();
    h.run("setView('imports')");
    if (receipt) h.nodes.get("#receipt-dialog").showModal();
    const pending = deferred(), previousFetch = h.context.fetch;
    let searching = false;
    h.context.fetch = path => path.startsWith("/api/messages?") ? (searching = true, pending.promise) : previousFetch(path);
    const browsing = h.run(`browseImport(${runs[0].id}, '${runs[0].name}')`);
    await settleUntil(() => searching, "Browse must start the destination search");
    assert.equal(h.run("state.view"), "archive");
    assert.equal(h.nodes.get("#receipt-dialog").open, false);
    assert.equal(h.document.activeElement, h.nodes.get("#search-input"));
    h.nodes.get("#filter-toggle").focus();
    pending.resolve(response({ total: 1, offset: 0, limit: 50, messages: [{ id: 1, subject: "Saved mail", sender: "Fixture" }] }));
    await browsing;
    assert.equal(h.document.activeElement, h.nodes.get("#filter-toggle"), "A late result must not reclaim focus");
  }
});

await check("a refresh failure never rewrites a committed file as a failed import", async () => {
  const { h } = importFixture({ failRefresh: true });
  await h.run("refreshStats();");
  await h.run("startImport(files)");
  const outcomes = h.nodes.get("#import-outcomes").children;
  assert.equal(outcomes.length, 1, "A saved file gets one receipt, even if its first stats refresh fails");
  assert.match(outcomes[0].textContent, /Import complete/);
  assert.equal(outcomes[0].classList.contains("error"), false);
  assert.equal(h.run("state.stats.messages"), 1, "Final refresh recovers the saved archive");
  assert.match(h.nodes.get("#message-list").textContent, /Saved mail 1/);
});

await check("import review offers one clear browse action and retains the receipt", async () => {
  const { h } = importFixture();
  await h.run("refreshStats();"); await h.run("startImport(files)");
  assert.match(h.nodes.get("#import-outcomes").textContent, /View receipt/);
  assert.doesNotMatch(h.nodes.get("#import-outcomes").textContent, /Browse mail/);
  assert.equal(h.nodes.get("#view-imported-mail").hidden, false);
  assert.equal(h.nodes.get("#import-review-summary").hidden, true, "One successful file already shows its counts on the card");
});

await check("browsing a receipt retries a failed archive refresh without losing the receipt", async () => {
  const { h, runs } = importFixture();
  await h.run("refreshStats();"); await h.run("startImport(files)");
  h.nodes.get("#receipt-dialog").showModal();
  const fetch = h.context.fetch;
  h.context.fetch = async () => { throw new Error("Connection lost"); };
  await h.run(`browseImport(${runs[0].id}, '${runs[0].name}')`);
  assert.equal(h.nodes.get("#receipt-dialog").open, true);
  assert.match(h.nodes.get("#receipt-content").textContent, /Cannot reach MailCairn/);
  h.context.fetch = fetch;
  await h.run(`browseImport(${runs[0].id}, '${runs[0].name}')`);
  assert.equal(h.nodes.get("#receipt-dialog").open, false);
  assert.equal(Number(h.run("state.importId")), runs[0].id);
  assert.equal(h.run("state.result.total"), 1);
});

await check("View imported mail clears stale filters and opens the confirmed single receipt", async () => {
  const { h, requests, runs } = importFixture();
  await h.run("refreshStats();"); await h.run("startImport(files)");
  for (const selector of ["#search-input", "#filter-sender", "#filter-after", "#filter-before"]) h.nodes.get(selector).value = "stale";
  h.nodes.get("#filter-attachments").checked = true;
  h.run("state.importId = '999'; state.offset = 50");
  assert.equal(h.nodes.get("#import-dialog").open, true);
  h.nodes.get("#view-imported-mail").click();
  await settleUntil(() => !h.nodes.get("#import-dialog").open && h.run("state.searchReady"), "Review action must finish navigation and search");
  for (const selector of ["#search-input", "#filter-sender", "#filter-after", "#filter-before"]) assert.equal(h.nodes.get(selector).value, "");
  assert.equal(h.nodes.get("#filter-attachments").checked, false);
  assert.equal(Number(h.run("state.importId")), runs[0].id);
  assert.equal(h.run("state.offset"), 0);
  assert.equal(h.run("state.view"), "archive");
  const params = new URLSearchParams(requests.filter(path => path.startsWith("/api/messages?")).at(-1).split("?")[1]);
  assert.equal(params.get("import_id"), String(runs[0].id));
  for (const key of ["q", "sender", "after", "before", "attachments"]) assert.equal(params.has(key), false);
  assert.match(h.nodes.get("#message-list").textContent, /Saved mail 1/);
});

await check("a delayed imported-mail search preserves subsequent focus and navigation", async () => {
  for (const destination of ["filter", "guide", "preferences"]) {
    const { h } = importFixture();
    await h.run("refreshStats()"); await h.run("startImport(files)");
    const previousFetch = h.context.fetch, pending = deferred();
    let requested = false;
    h.context.fetch = path => {
      if (path.startsWith("/api/messages?")) { requested = true; return pending.promise; }
      return previousFetch(path);
    };
    const reviewing = h.run("viewImportedMail()");
    await settleUntil(() => requested, "Navigation must start the imported-mail search");
    assert.equal(h.nodes.get("#import-dialog").open, false);
    assert.equal(h.document.activeElement, h.nodes.get("#search-input"), "Initial navigation focuses search immediately");
    if (destination === "guide") h.run("setView('guide')");
    if (destination === "preferences") h.run("openPreferences()");
    const focused = h.nodes.get(destination === "guide" ? "#mailbox-guide-title" : destination === "preferences" ? "#reset-preferences" : "#filter-toggle");
    focused.focus();
    h.advance(1000); // The original navigation entrance finishes while loading.
    pending.resolve(response({ total: 1, offset: 0, limit: 50, messages: [{ id: 1, subject: "Synthetic", sender: "Fixture" }] }));
    await reviewing;
    assert.equal(h.document.activeElement, focused, `${destination}: late results must preserve the user's focus`);
    assert.equal(h.run("state.view"), destination === "guide" ? "guide" : "archive");
    if (destination === "preferences") assert.equal(h.nodes.get("#preferences-dialog").open, true);
    assert.equal(h.nodes.get("#archive-workspace").classList.contains("archive-arriving"), false, "Results cannot restart the navigation entrance");
  }
});

await check("review keeps receipts visible when refresh fails and a later retry succeeds", async () => {
  const { h } = importFixture();
  await h.run("refreshStats();"); await h.run("startImport(files)");
  const fetch = h.context.fetch;
  h.context.fetch = async () => { throw new Error("Connection lost"); };
  await h.run("viewImportedMail()");
  assert.equal(h.nodes.get("#import-dialog").open, true);
  assert.match(h.nodes.get("#import-outcomes").textContent, /Import complete/);
  const inlineError = h.nodes.get("#import-review-error");
  assert.equal(inlineError.hidden, false, "Refresh failure must be visible inside the modal");
  assert.equal(inlineError.getAttribute("role"), "alert");
  assert.match(inlineError.textContent, /Cannot reach MailCairn/);
  assert.ok(h.nodes.get("#import-dialog").querySelectorAll("[role]").includes(inlineError));
  h.run("changeLanguage('zh-CN')");
  assert.match(inlineError.textContent, /无法连接/);
  assert.equal(h.nodes.get("#view-imported-mail").disabled, false, "Retry must remain available");
  h.context.fetch = fetch;
  await h.run("viewImportedMail()");
  assert.equal(inlineError.hidden, true, "A successful retry clears the inline failure");
  assert.equal(h.nodes.get("#import-dialog").open, false);
  assert.equal(h.run("state.result.total"), 1);
});

await check("a delayed review refresh cannot navigate after its dialog closes", async () => {
  const { h, requests } = importFixture();
  await h.run("refreshStats()"); await h.run("startImport(files)");
  const stats = JSON.parse(h.run("JSON.stringify(state.stats)")), pending = deferred();
  const previousFetch = h.context.fetch;
  h.context.fetch = path => path === "/api/stats" ? pending.promise : previousFetch(path);
  h.nodes.get("#search-input").value = "Keep my query";
  h.run("state.importId = 'older'; state.offset = 50");
  const reviewing = h.run("viewImportedMail()");
  h.nodes.get("#import-dialog").close();
  h.run("setView('guide')");
  const focus = h.nodes.get("#search-input"); focus.focus();
  const searchesBefore = requests.filter(path => path.startsWith("/api/messages?")).length;
  pending.resolve(response(stats)); await reviewing;
  assert.equal(h.run("state.view"), "guide");
  assert.equal(h.nodes.get("#import-dialog").open, false);
  assert.equal(h.nodes.get("#search-input").value, "Keep my query");
  assert.equal(h.run("state.importId"), "older");
  assert.equal(h.run("state.offset"), 50);
  assert.equal(h.document.activeElement, focus);
  assert.equal(requests.filter(path => path.startsWith("/api/messages?")).length, searchesBefore);
});

await check("a reopened import review ignores an older failed refresh and allows retry", async () => {
  const { h } = importFixture();
  await h.run("refreshStats();"); await h.run("startImport(files)");
  const pending = deferred(), fetch = h.context.fetch;
  h.context.fetch = path => path === "/api/stats" ? pending.promise : fetch(path);
  const old = h.run("viewImportedMail()");
  h.nodes.get("#import-dialog").close();
  h.run("openImport()");
  assert.equal(h.nodes.get("#view-imported-mail").disabled, false);
  pending.resolve(response({ error: "Old connection failure" }, 503)); await old;
  assert.equal(h.nodes.get("#import-dialog").open, true);
  assert.equal(h.nodes.get("#import-review-error").hidden, true);
  assert.equal(h.nodes.get("#view-imported-mail").disabled, false);
  h.context.fetch = fetch;
  await h.run("viewImportedMail()");
  assert.equal(h.nodes.get("#import-dialog").open, false);
  assert.equal(h.run("state.result.total"), 1);
});

await check("a delayed history action cannot navigate after leaving and returning to the same view", async () => {
  const { h, runs } = importFixture();
  await h.run("refreshStats();"); await h.run("startImport(files)");
  h.nodes.get("#import-dialog").close();
  h.run("setView('imports')");
  const pending = deferred(), fetch = h.context.fetch;
  h.context.fetch = path => path === "/api/stats" ? pending.promise : fetch(path);
  const old = h.run(`browseImport(${runs[0].id}, '${runs[0].name}')`);
  h.run("setView('guide'); setView('imports')");
  pending.resolve(response({ ...emptyStats, messages: 1, imports: runs })); await old;
  assert.equal(h.run("state.view"), "imports");
  assert.equal(h.run("state.importId"), "");
});

await check("a delayed review refresh cannot close or navigate a newer import batch", async () => {
  const fixture = importFixture({ count: 2 }), { h, requests } = fixture;
  await h.run("refreshStats()"); await h.run("startImport([files[0]])");
  const stats = JSON.parse(h.run("JSON.stringify(state.stats)")), pending = deferred();
  const previousFetch = h.context.fetch;
  let deferredStats = false;
  h.context.fetch = path => {
    if (path === "/api/stats" && !deferredStats) { deferredStats = true; return pending.promise; }
    return previousFetch(path);
  };
  h.run("setView('guide'); state.importId = 'older'; state.offset = 50");
  h.nodes.get("#search-input").value = "Keep my newer context";
  const reviewing = h.run("viewImportedMail()");
  const newImport = h.run("startImport([files[1]])");
  await settleUntil(() => fixture.uploads === 2, "A new upload must be active before old refresh resolves");
  const review = h.run("state.importReview"), focus = h.document.activeElement;
  const searchesBefore = requests.filter(path => path.startsWith("/api/messages?")).length;
  pending.resolve(response(stats)); await reviewing;
  assert.equal(h.run("state.importReview"), review);
  assert.equal(h.run("state.busy"), true);
  assert.equal(h.run("state.view"), "guide");
  assert.equal(h.nodes.get("#import-dialog").open, true);
  assert.equal(h.nodes.get("#view-imported-mail").disabled, true);
  assert.equal(h.nodes.get("#search-input").value, "Keep my newer context");
  assert.equal(h.run("state.importId"), "older");
  assert.equal(h.run("state.offset"), 50);
  assert.equal(h.document.activeElement, focus);
  assert.equal(requests.filter(path => path.startsWith("/api/messages?")).length, searchesBefore);
  fixture.secondUpload.resolve({ job_id: 2 }); await newImport;
  assert.equal(h.run("state.busy"), false);
  assert.match(h.nodes.get("#import-outcomes").textContent, /fixture-2.eml/);
  assert.doesNotMatch(h.nodes.get("#import-outcomes").textContent, /fixture-1.eml/);
});

await check("multi-file review opens all mail and language switching keeps receipt totals intact", async () => {
  const fixture = importFixture({ count: 2 }), { h, requests } = fixture;
  await h.run("refreshStats()");
  const importing = h.run("startImport(files)");
  await settleUntil(() => fixture.uploads === 2, "Queue must reach second upload");
  h.run("changeLanguage('zh-CN')");
  assert.match(h.nodes.get("#import-queue").textContent, /2/);
  assert.match(h.nodes.get("#import-outcomes").textContent, /fixture-1.eml/);
  assert.equal(h.run("state.busy"), true);
  fixture.secondUpload.resolve({ job_id: 2 }); await importing;
  assert.equal(h.nodes.get("#import-review-summary").hidden, false, "A batch needs an aggregate summary");
  assert.match(h.nodes.get("#import-review-summary").textContent, /新增 2/);
  assert.match(h.nodes.get("#view-imported-mail").textContent, /查看邮件/);
  h.run("changeLanguage('en'); state.importId = '999'");
  assert.match(h.nodes.get("#import-review-summary").textContent, /2 added/);
  await h.run("viewImportedMail()");
  assert.equal(h.run("state.importId"), "");
  assert.equal(h.nodes.get("#source-filter").hidden, true);
  assert.equal(h.run("state.result.total"), 2);
  const lastSearch = requests.filter(path => path.startsWith("/api/messages?")).at(-1);
  assert.equal(new URLSearchParams(lastSearch.split("?")[1]).has("import_id"), false);
});

await check("interrupted queues report unstarted files while preserving completed receipts", async () => {
  const { h } = importFixture({ count: 3, failRefresh: true });
  await h.run("refreshStats()"); await h.run("startImport(files)");
  assert.equal(h.run("state.importReview.runs.length"), 1);
  assert.equal(h.run("state.importReview.remaining"), 2);
  assert.equal(h.nodes.get("#import-review-summary").hidden, false, "Interrupted files must remain visible");
  assert.match(h.nodes.get("#import-review-summary").textContent, /2 files were not started/);
  assert.equal(h.nodes.get("#view-imported-mail").hidden, false);
  assert.equal(h.run("state.stats.messages"), 1);
});

await check("Stop prevents the next upload and forwards cancellation if job creation was already in flight", async () => {
  const fixture = importFixture({ count: 3 }), { h, requests } = fixture;
  await h.run("refreshStats()"); const importing = h.run("startImport(files)");
  await settleUntil(() => fixture.uploads === 2, "Second upload must be pending before Stop");
  await h.run("cancelJob()");
  assert.equal(h.run("state.cancel"), true);
  fixture.secondUpload.resolve({ job_id: 2 }); await importing;
  assert.ok(requests.includes("/api/jobs/2/cancel"), "Late-created job must receive the stop request");
  assert.equal(fixture.uploads, 2, "Third file must never upload");
  assert.equal(h.run("state.importReview.remaining"), 1);
  assert.match(h.nodes.get("#import-review-summary").textContent, /1 file was not started/);
  assert.equal(h.run("state.stats.messages"), 2, "Already committed records survive a late cancellation");
  assert.equal(h.run("state.busy"), false);
  assert.equal(h.nodes.get("#view-imported-mail").disabled, false);
});

await check("zero-message outcomes keep their receipt without offering an empty mail destination", () => {
  const h = harness(); h.run("bindLanguage(); bindReadingRoom()");
  h.run("appendOutcome({id: 8, status: 'partial', added: 0, duplicates: 0, skipped: 2}, 'unreadable.eml')");
  const actions = h.nodes.get("#import-outcomes").querySelector(".outcome-actions");
  assert.equal(actions.children.length, 1);
  assert.match(actions.textContent, /View receipt/);
  assert.doesNotMatch(actions.textContent, /Browse mail/);
  assert.equal(h.nodes.get("#view-imported-mail").hidden, true);
  assert.equal(h.nodes.get("#import-review-summary").hidden, false, "Unimported records must remain visible");
  assert.match(h.nodes.get("#import-review-summary").textContent, /2 records not imported/);
});

await check("filter reveal stays immediately usable and settles on rapid close and reduced motion", () => {
  const h = harness(); h.run("bindEvents(); bindReadingRoom()");
  const panel = h.nodes.get("#filter-panel"), toggle = h.nodes.get("#filter-toggle"), sender = h.nodes.get("#filter-sender");
  panel.hidden = true; sender.value = "Keep my filter";
  toggle.click();
  assert.equal(panel.hidden, false);
  assert.equal(toggle.getAttribute("aria-expanded"), "true");
  assert.ok(panel.classList.contains("filters-opening"));
  assert.ok(h.document.activeElement === sender);
  assert.equal(sender.value, "Keep my filter");
  toggle.click();
  assert.equal(panel.hidden, true);
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(panel.classList.contains("filters-opening"), false);
  assert.equal(h.run("surfaceTransitions.size"), 0);
  const reduced = h.media.get("(prefers-reduced-motion: reduce)");
  reduced.matches = true; h.emit(reduced, "change");
  toggle.click();
  assert.equal(panel.hidden, false);
  assert.ok(h.document.activeElement === sender);
  assert.equal(panel.classList.contains("filters-opening"), false);
  assert.equal(h.run("surfaceTransitions.size"), 0);
});

await check("view and receipt transitions settle on reduced motion without losing their content", () => {
  const h = harness(); h.run("bindLanguage(); bindReadingRoom(); setView('guide')");
  h.run("appendOutcome({id: 1, status: 'complete', added: 1, duplicates: 0, skipped: 0}, 'Original filename.eml')");
  assert.ok(h.run("surfaceTransitions.size") >= 1);
  const reduced = h.media.get("(prefers-reduced-motion: reduce)");
  reduced.matches = true; h.emit(reduced, "change");
  assert.equal(h.run("surfaceTransitions.size"), 0);
  assert.equal(h.timers.size, 0); assert.equal(h.frames.size, 0);
  assert.match(h.nodes.get("#import-outcomes").textContent, /Original filename.eml/);
  reduced.matches = false; h.emit(reduced, "change");
  assert.equal(h.run("surfaceTransitions.size"), 0, "Preference restoration must not replay settled surfaces");
});

await check("rejected inputs keep a useful review and cannot navigate to nonexistent imported mail", async () => {
  const { h } = importFixture(); await h.run("refreshStats()");
  await h.run("startImport([{name:'empty.eml', size:0}, {name:'wrong.zip', size:100}])");
  assert.equal(h.nodes.get("#import-outcomes").children.length, 2);
  assert.equal(h.nodes.get("#view-imported-mail").hidden, true);
  assert.equal(h.nodes.get("#import-dialog").open, true);
  assert.equal(h.run("state.stats.messages"), 0);
});

await check("modal Tab boundaries wrap visible enabled controls while interior navigation and browser shortcuts stay native", () => {
  const h=harness(),dialog=h.nodes.get('#preferences-dialog');dialog.open=true;
  const control=(id,{disabled=false,hidden=false,inert=false,tabIndex=0,visibility='visible'}={})=>({id,tabIndex,visibility,matches:()=>disabled,closest:()=>inert?{}:null,getClientRects:()=>hidden?[]:[{}],focus(){h.document.activeElement=this;}});
  const first=control('first'),middle=control('middle'),last=control('last');
  dialog.querySelectorAll=()=>[control('disabled',{disabled:true}),control('hidden',{hidden:true}),first,control('negative',{tabIndex:-1}),middle,last,control('inert',{inert:true}),control('invisible',{visibility:'hidden'})];
  h.context.getComputedStyle=node=>({visibility:node.visibility});
  h.context.testDialog=dialog;
  const key=(target,fields={})=>{let prevented=false;h.document.activeElement=target;h.context.testEvent={key:'Tab',currentTarget:dialog,preventDefault(){prevented=true;},...fields};h.run('keepDialogFocus(testEvent)');return prevented;};
  assert.equal(key(last),true);assert.equal(h.document.activeElement,first);
  assert.equal(key(first,{shiftKey:true}),true);assert.equal(h.document.activeElement,last);
  assert.equal(key(middle),false);assert.equal(h.document.activeElement,middle);
  for(const modifier of ['ctrlKey','metaKey','altKey'])assert.equal(key(last,{[modifier]:true}),false);
  assert.equal(key(last,{key:'Escape'}),false);
  dialog.open=false;assert.equal(key(last),false);
});

await check("reader failures offer in-place retry that restores body and preserves focus without stealing moved focus", async () => {
  const h = harness();
  h.run("bindLanguage(); bindReadingRoom(); state.result = { messages: [] }");
  h.context.fetch = async () => response({ error: "synthetic read busy" }, 503);
  await h.run("readMessage(1)");
  let retry = h.nodes.get("#reader").querySelector(".retry-reader");
  assert.ok(retry, "Failed reader must offer an in-place retry button");
  retry.focus();
  retry.click();
  await settleUntil(() => {
    const next = h.nodes.get("#reader").querySelector(".retry-reader");
    return next && next !== retry;
  }, "Second failure replaces retry button");
  retry = h.nodes.get("#reader").querySelector(".retry-reader");
  assert.equal(h.document.activeElement, retry, "Repeated reader retry failure keeps focus on retry button");
  const pending = deferred();
  h.context.fetch = () => pending.promise;
  retry.click();
  assert.equal(h.document.activeElement, h.nodes.get("#reader"), "Pending retry parks focus on reader");
  pending.resolve(response({ id: 1, subject: "Recovered", body: "Retried body", warnings: [], attachments: [] }));
  await settleUntil(() => h.nodes.get("#reader").textContent.includes("Retried body"), "Reader should recover body");
  assert.equal(h.document.activeElement, h.nodes.get("#reader"), "Successful retry keeps focus on reader");

  h.context.fetch = async () => response({ error: "synthetic read busy" }, 503);
  await h.run("readMessage(1)");
  retry = h.nodes.get("#reader").querySelector(".retry-reader");
  retry.focus();
  const slow = deferred();
  h.context.fetch = () => slow.promise;
  retry.click();
  const searchInput = h.nodes.get("#search-input");
  searchInput.focus();
  slow.resolve(response({ id: 1, subject: "Late", body: "Late body", warnings: [], attachments: [] }));
  await settleUntil(() => h.nodes.get("#reader").textContent.includes("Late body"), "Late retry renders body");
  assert.equal(h.document.activeElement, searchInput, "Moved focus must not be stolen by completed retry");
});

await check("receipt failures offer in-place retry that restores details and preserves moved focus", async () => {
  const h = harness();
  h.run("bindLanguage(); bindReadingRoom()");
  h.context.fetch = async () => response({ error: "receipt unavailable" }, 503);
  await h.run("showReceipt(9)");
  let retry = h.nodes.get("#receipt-content").querySelector(".retry-receipt");
  assert.ok(retry, "Failed receipt load must offer in-place retry");
  retry.focus();
  retry.click();
  await settleUntil(() => {
    const next = h.nodes.get("#receipt-content").querySelector(".retry-receipt");
    return next && next !== retry;
  }, "Second failure replaces receipt retry");
  retry = h.nodes.get("#receipt-content").querySelector(".retry-receipt");
  assert.equal(h.document.activeElement, retry, "Repeated receipt failure keeps focus on retry button");
  const pending = deferred();
  h.context.fetch = () => pending.promise;
  retry.click();
  assert.equal(h.document.activeElement, h.nodes.get("#receipt-content"), "Pending receipt retry keeps focus inside receipt content");
  pending.resolve(response({ id: 9, name: "inbox.mbox", status: "complete", started: "2026-11-17T00:00:00Z", size: 128, total: 1, added: 1, duplicates: 0, skipped: 0, sha256: "abc", issues: [] }));
  await settleUntil(() => h.nodes.get("#receipt-content").textContent.includes("inbox.mbox"), "Receipt content should load");
  assert.ok(h.document.activeElement?.classList?.contains("button"), "Successful retry moves focus to receipt action");

  h.context.fetch = async () => response({ error: "receipt unavailable" }, 503);
  await h.run("showReceipt(9)");
  retry = h.nodes.get("#receipt-content").querySelector(".retry-receipt");
  retry.focus();
  const slow = deferred();
  h.context.fetch = () => slow.promise;
  retry.click();
  const closeButton = h.nodes.get("#receipt-dialog").querySelector("[data-close-dialog]") || h.nodes.get("#search-input");
  closeButton.focus();
  slow.resolve(response({ id: 9, name: "late.mbox", status: "complete", started: "2026-11-17T00:00:00Z", size: 128, total: 1, added: 0, duplicates: 1, skipped: 0, sha256: "abc", issues: [] }));
  await settleUntil(() => h.nodes.get("#receipt-content").textContent.includes("late.mbox"), "Late receipt renders");
  assert.equal(h.document.activeElement, closeButton, "Moved focus must not be stolen by late receipt retry");
});

await check("preferences dialog focuses current theme and keepDialogFocus filters closed details while wrapping dialog root", () => {
  const h = harness({ storage: { "mailcairn.reading-room.v1": JSON.stringify({ theme: "dark" }) } });
  h.run("bindReadingRoom(); openPreferences()");
  const darkRadio = h.context.document.querySelector('#preferences-form input[name="theme"][value="dark"]');
  assert.equal(h.document.activeElement, darkRadio, "Opening preferences focuses the active theme choice");

  const dialog = h.nodes.get("#connect-dialog");
  dialog.open = true;
  const closedDetails = { tagName: "DETAILS", attributes: new Map(), closest(sel) { return sel === "details:not([open])" && !this.attributes.has("open") ? this : null; } };
  const openDetails = { tagName: "DETAILS", attributes: new Map([["open", ""]]), closest(sel) { return sel === "details:not([open])" && !this.attributes.has("open") ? this : null; } };
  const makeNode = (id, tagName, parentElement = null) => ({
    id, tagName, parentElement, tabIndex: 0,
    matches: () => false,
    closest(sel) {
      if (sel === "[hidden], [inert]") return null;
      if (sel === "details:not([open])") {
        if (this.tagName === "DETAILS" && !this.attributes?.has("open")) return this;
        return this.parentElement?.closest?.(sel) || null;
      }
      return null;
    },
    getClientRects: () => [{}],
    focus() { h.document.activeElement = this; },
  });
  const first = makeNode("first", "BUTTON");
  const closedSummary = makeNode("summary-closed", "SUMMARY", closedDetails);
  const closedInput = makeNode("port-closed", "INPUT", closedDetails);
  const openInput = makeNode("port-open", "INPUT", openDetails);
  dialog.querySelectorAll = () => [first, closedSummary, closedInput, openInput];
  h.context.getComputedStyle = () => ({ visibility: "visible" });
  h.context.testDialog = dialog;
  const key = (target, fields = {}) => {
    let prevented = false;
    h.document.activeElement = target;
    h.context.testEvent = { key: "Tab", currentTarget: dialog, preventDefault() { prevented = true; }, ...fields };
    h.run("keepDialogFocus(testEvent)");
    return prevented;
  };
  assert.equal(key(dialog), true); assert.equal(h.document.activeElement, first);
  assert.equal(key(dialog, { shiftKey: true }), true); assert.equal(h.document.activeElement, openInput);
  assert.equal(key(closedSummary, { shiftKey: false }), false);
  closedDetails.attributes.set("open", "");
  assert.equal(key(openInput), true); assert.equal(h.document.activeElement, first);
  closedDetails.attributes.delete("open");
  dialog.querySelectorAll = () => [first, closedSummary, closedInput];
  assert.equal(key(closedSummary), true); assert.equal(h.document.activeElement, first);
});

await check("single-key shortcuts support uppercase and lowercase keys while respecting dialogs, inputs and preference toggle", () => {
  const h = harness();
  h.run("bindEvents(); bindReadingRoom(); state.stats = { messages: 3 }");
  const sendKey = (key, fields = {}) => {
    let prevented = false;
    h.emit(h.context.window, "keydown", { key, ctrlKey: false, metaKey: false, altKey: false, isComposing: false, preventDefault() { prevented = true; }, ...fields });
    return prevented;
  };
  assert.equal(sendKey("H"), true);
  assert.equal(h.run("state.view"), "imports");
  assert.equal(sendKey("G"), true);
  assert.equal(h.run("state.view"), "archive");
  assert.equal(sendKey("I"), true);
  assert.equal(h.nodes.get("#import-dialog").open, true);
  assert.equal(sendKey("H"), false, "Open modal must block single-key shortcuts");
  h.nodes.get("#import-dialog").close();

  assert.equal(sendKey(","), true);
  assert.equal(h.nodes.get("#preferences-dialog").open, true);
  h.nodes.get("#preferences-dialog").close();

  assert.equal(sendKey("?"), true);
  assert.equal(h.nodes.get("#command-dialog").open, true);
  h.nodes.get("#command-dialog").close();

  h.nodes.get("#search-input").focus();
  assert.equal(sendKey("H"), false, "Focused text input must not trigger single-key shortcuts");
  h.document.body.focus();

  h.emit(h.nodes.get("#preferences-form"), "change", { target: { name: "shortcuts", type: "checkbox", checked: false } });
  assert.equal(sendKey("H"), false);
  assert.equal(sendKey("h"), false);
  assert.equal(sendKey(","), false);
});

if (isDirect) console.log(`\n${reports.length} frontend checks passed. Node ${process.version}; DOM shim only, not a browser/layout/accessibility audit.`);
