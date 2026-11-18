/* MailCairn's interface. Mail content is always inserted as text, never HTML. */
"use strict";

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = { view: "archive", stats: null, result: null, selected: null, offset: 0, importId: "", searchSerial: 0, readerSerial: 0, receiptSerial: 0, searchReady: false, busy: false, kind: null, job: null, xhr: null, cancel: false, currentFile: null, importReview: null, limits: { upload_bytes: 20 * 1024 ** 3, message_bytes: 32 * 1024 ** 2 } };
let searchTimer, toastTimer, failedSearch = null;
let readerReturnScroll = 0;
let sessionNavigationBound = false;
state.connections = null;
state.connectionCapabilities = null;
state.statsSerial = 0;
state.archiveDirty = false;
let connectionProvider = "gmail", reconnectingAccount = null, connectionSubmitting = false;
let connectionFormSerial = 0, connectionsSerial = 0, connectionsSignature = "";
let connectionPollingStarted = false, connectionPollTimer = 0, connectionPollController = null;
const connectionActions = new Set();
const surfaceTransitions = new Map();

function settleSurface(node) {
  const transition = surfaceTransitions.get(node);
  if (!transition) return;
  clearTimeout(transition.timer);
  node.classList.remove(transition.name);
  surfaceTransitions.delete(node);
}
function animateSurface(node, name, duration) {
  if (!node) return;
  settleSurface(node);
  if (!motionAllowed() || document.hidden || node.hidden) return;
  void node.offsetWidth;
  node.classList.add(name);
  surfaceTransitions.set(node, { name, timer: setTimeout(() => settleSurface(node), duration) });
}

function el(tag, className = "", content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (typeof content === "function") uiText(node, content);
  else if (content !== undefined) node.textContent = content;
  return node;
}
function icon(name, extra = "") {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", `icon ${extra}`.trim());
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `#i-${name}`);
  svg.append(use);
  return svg;
}
function action(label, handler, className = "text-button") {
  const button = el("button", className);
  if (label) uiCopy(button, label);
  button.type = "button";
  button.addEventListener("click", handler);
  return button;
}
function download(label, href, className = "text-button") {
  const link = el("a", className);
  link.href = href;
  link.setAttribute("download", "");
  const caption = document.createTextNode("");
  uiCopy(caption, label);
  link.append(icon("download"), caption);
  return link;
}
const number = (value) => Number(value || 0).toLocaleString(uiLocale);
function bytes(value) {
  const size = Number(value || 0);
  if (size < 1024) return `${size} B`;
  const units = ["KiB", "MiB", "GiB", "TiB"];
  const exponent = Math.min(4, Math.floor(Math.log(size) / Math.log(1024)));
  const amount = size / 1024 ** exponent;
  return `${amount.toLocaleString(uiLocale, { maximumFractionDigits: amount < 10 ? 1 : 0 })} ${units[exponent - 1]}`;
}
function shortDate(value) {
  if (!value) return translate("Undated");
  const parts = value.split("-");
  if (parts.length !== 3) return value;
  return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2])).toLocaleDateString(uiLocale, { month: "short", day: "numeric", year: "numeric" });
}
function localTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? translate("Unknown date") : date.toLocaleString(uiLocale, { year: "numeric", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}
function senderName(value) {
  return String(value || translate("Unknown sender")).replace(/\s*<[^>]+>\s*$/, "").replace(/^"|"$/g, "").trim() || value || translate("Unknown sender");
}
function statusClass(status) {
  return ["failed", "interrupted"].includes(status) ? "error" : ["partial", "cancelled", "running"].includes(status) ? "warn" : "";
}
let errorOwner = null;
function setError(message, owner = null) {
  errorOwner = owner;
  uiCopy($("#global-error-text"), () => message);
  $("#global-error").hidden = false;
}
function toast(message) {
  clearTimeout(toastTimer);
  uiCopy($("#toast"), () => message);
  $("#toast").hidden = false;
  toastTimer = setTimeout(() => { $("#toast").hidden = true; }, 5000);
}
async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.method && options.method !== "GET") headers["X-MailCairn"] = "1";
  let response;
  try {
    response = await fetch(path, { ...options, headers, credentials: "same-origin" });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new Error("Cannot reach MailCairn. Open the app, then try again.");
  }
  let body;
  try { body = await response.json(); } catch { throw new Error("MailCairn returned an unexpected response. Reopen your archive from the app."); }
  if (!response.ok) {
    const error = new Error(body.error || `The operation failed (${response.status}).`);
    error.status = response.status;
    throw error;
  }
  return body;
}

let viewRevision = 0, importDialogRevision = 0, viewImportSerial = 0;
function setView(view) {
  const changed = state.view !== view;
  if (changed) viewRevision++;
  stopAllLights(); resetPaperTilt();
  state.view = view;
  const titles = {
    archive: ["", "All mail", ""],
    imports: ["", "Import history", "Your files and import receipts."],
    connections: ["", "Connected mailboxes", ""],
    guide: ["", "Getting started", "Bring your mail. Keep your originals."]
  };
  const title = titles[view] || titles.archive;
  uiCopy($("#page-eyebrow"), () => title[0]);
  uiCopy($("#page-title"), () => title[1]);
  uiCopy($("#page-subtitle"), () => title[2]);
  $$(".view").forEach((node) => { node.hidden = node.id !== `view-${view}`; });
  $$("[data-view]").forEach((button) => {
    const active = button.dataset.view === view;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current");
  });
  positionNavMarker();
  if (changed) animateSurface($(`#view-${view}`), "view-entering", 560);
  if (view === "imports") renderHistory();
  if (view === "connections") refreshConnections().catch(showConnectionsError);
  if (view === "archive" && state.archiveDirty) search(false, { preserveSelection: true });
  scheduleConnectionPoll();
  if (view === "archive" && state.stats?.messages === 0) illuminateArchive();
}

async function refreshStats({ recover = false, cancelRequested = false, quiet = false, signal } = {}) {
  const serial = ++state.statsSerial;
  const stats = await api("/api/stats", signal ? { signal } : {});
  if (signal?.aborted || serial !== state.statsSerial) return state.stats;
  const importsChanged = JSON.stringify(state.stats?.imports) !== JSON.stringify(stats.imports);
  const hadMail = (state.stats?.messages || 0) > 0;
  state.stats = stats;
  if (stats.limits) state.limits = stats.limits;
  uiCopy($("#nav-count"), () => number(stats.messages));
  uiCopy($("#summary-count"), () => number(stats.messages));
  uiCopy($("#summary-label"), () => Number(stats.messages) === 1 ? "message preserved" : "messages preserved");
  uiCopy($("#summary-range"), () => stats.first_date ? `${shortDate(stats.first_date)} — ${shortDate(stats.last_date)}` : "No dated messages");
  uiCopy($("#summary-size"), () => `${bytes(stats.raw_bytes)} of originals · ${number(stats.attachments)} ${Number(stats.attachments) === 1 ? "attachment" : "attachments"}`);
  $("#archive-path").textContent = stats.archive_file;
  $("#empty-archive").hidden = stats.messages > 0;
  $("#archive-summary").hidden = stats.messages === 0;
  $("#archive-workspace").hidden = stats.messages === 0;
  if (!hadMail && stats.messages > 0) {
    stopPaperUnfold();
    stopLight($("#archive-light"));
    animateSurface($("#archive-workspace"), "archive-arriving", 720);
  }
  uiCopy($("#drop-zone small"), () => `MBOX / EML · up to ${bytes(state.limits.upload_bytes)} per file`);
  const limitParagraph = $("#guide-limits");
  if (limitParagraph) uiCopy(limitParagraph, () => `This session allows ${bytes(state.limits.upload_bytes)} per file and ${bytes(state.limits.message_bytes)} per message. Oversized or unreadable records appear in the receipt, rather than disappearing silently.`);
  if (!quiet || importsChanged) renderHistory();
  if (recover && stats.active_job && !state.busy) {
    resumeJob(stats.active_job, { cancelRequested });
  }
  return stats;
}

function filters() {
  const params = new URLSearchParams();
  const values = { q: $("#search-input").value.trim(), sender: $("#filter-sender").value.trim(), after: $("#filter-after").value, before: $("#filter-before").value, attachments: $("#filter-attachments").checked ? "1" : "", import_id: state.importId };
  if (values.after && values.before && values.after > values.before) throw new Error("The start date must be on or before the end date.");
  Object.entries(values).forEach(([key, value]) => { if (value) params.set(key, value); });
  return params;
}
function updateFilterBadge() {
  const count = [$("#filter-sender").value, $("#filter-after").value, $("#filter-before").value, $("#filter-attachments").checked].filter(Boolean).length;
  uiCopy($("#filter-count"), () => count);
  $("#filter-count").hidden = !count;
}
async function search(reset = true, { preserveSelection = false, offset, scrollResults = false } = {}) {
  if (!state.stats || !state.stats.messages) return;
  const requestedOffset = reset ? 0 : (offset ?? state.offset);
  const serial = ++state.searchSerial;
  failedSearch = null;
  const retry = $("#retry-search");
  retry.hidden = document.activeElement !== retry;
  // Keep a keyboard user's focused retry in the tab order while it runs.
  // failedSearch is cleared above, so repeated activation cannot resubmit.
  retry.setAttribute("aria-disabled", "true");
  state.searchReady = false;
  $("#message-list").setAttribute("aria-busy", "true");
  $("#export-results").setAttribute("aria-disabled", "true");
  $("#previous-page").disabled = true;
  $("#next-page").disabled = true;
  updateFilterBadge();
  let params;
  try { params = filters(); } catch (error) { $("#message-list").setAttribute("aria-busy", "false"); setError(error.message, "search"); return; }
  $("#export-results").href = `/api/export?${params}`;
  params.set("offset", requestedOffset);
  uiCopy($("#results-label"), () => "Searching…");
  try {
    const result = await api(`/api/messages?${params}`);
    if (serial !== state.searchSerial) return;
    $("#message-list").setAttribute("aria-busy", "false");
    const previousIds = new Set((state.result?.messages || []).map(message => message.id));
    state.result = result;
    state.offset = result.offset;
    state.archiveDirty = false;
    state.searchReady = true;
    uiCopy($("#results-label"), () => `${number(result.total)} ${result.total === 1 ? "message" : "messages"}`);
    $("#previous-page").disabled = result.offset === 0;
    $("#next-page").disabled = result.offset + result.limit >= result.total;
    uiCopy($("#page-label"), () => result.total ? `${number(result.offset + 1)}–${number(Math.min(result.offset + result.limit, result.total))} of ${number(result.total)}` : "No results");
    $("#list-empty").hidden = !!result.messages.length;
    $("#message-list").hidden = !result.messages.length;
    $("#export-results").setAttribute("aria-disabled", result.total ? "false" : "true");
    const focusedMessage = preserveSelection ? document.activeElement?.dataset?.messageId : null;
    const listScroll = $("#message-list").scrollTop;
    renderList({ arrivingIds: preserveSelection ? new Set(result.messages.filter(message => !previousIds.has(message.id)).map(message => message.id)) : null });
    if (reset || scrollResults) $("#message-list").scrollTop = 0;
    if (document.activeElement === retry) {
      ($("#message-list").querySelector(".message-row") || $("#search-input")).focus({ preventScroll: true });
    }
    retry.hidden = true;
    if (errorOwner === "search") { $("#global-error").hidden = true; errorOwner = null; }
    if (preserveSelection) {
      $("#message-list").scrollTop = listScroll;
      if (focusedMessage) {
        const focusedRow = $$(".message-row").find(row => row.dataset.messageId === focusedMessage);
        (focusedRow || (state.selected ? $("#reader") : $("#search-input"))).focus({ preventScroll: true });
      }
      if (state.selected) return;
    }
    if (state.selected && result.messages.some((message) => message.id === state.selected)) return;
    state.selected = null;
    state.readerSerial++;
    $(".mail-workspace").classList.remove("reading");
    if (result.messages.length && window.matchMedia("(min-width: 581px)").matches) {
      await readMessage(result.messages[0].id, false);
    } else renderReaderPlaceholder();
  } catch (error) {
    if (serial !== state.searchSerial) return;
    $("#message-list").setAttribute("aria-busy", "false");
    uiCopy($("#results-label"), () => "Search unavailable");
    failedSearch = { serial, reset, preserveSelection, offset: requestedOffset, scrollResults };
    retry.hidden = false;
    retry.setAttribute("aria-disabled", "false");
    setError(error.message, "search");
  }
}
function renderList({ arrivingIds = null } = {}) {
  const list = $("#message-list");
  list.replaceChildren();
  pruneUIBindings();
  let arrivalOrder = 0;
  for (const message of (state.result?.messages || [])) {
    const row = el("button", `message-row${state.selected === message.id ? " selected" : ""}`);
    row.type = "button";
    // Only the first visible handful arrives in sequence; long results stay immediate.
    if (motionAllowed() && arrivalOrder < 8 && (!arrivingIds || arrivingIds.has(message.id))) {
      row.classList.add("result-arriving");
      row.style.setProperty("--arrival-order", arrivalOrder++);
      row.addEventListener("animationend", () => row.classList.remove("result-arriving"), { once: true });
    }
    row.dataset.messageId = message.id;
    row.setAttribute("aria-pressed", state.selected === message.id ? "true" : "false");
    const top = el("div", "message-row-top");
    top.append(el("span", "message-sender", () => senderName(message.sender)), el("span", "message-date", () => translate(shortDate(message.date_day))));
    const subject = el("div", "message-subject");
    subject.append(el("span", "", message.subject));
    if (message.attachment_count) {
      const clip = icon("clip");
      const label = () => clip.setAttribute("aria-label", translate(`${number(message.attachment_count)} ${Number(message.attachment_count) === 1 ? "attachment" : "attachments"}`));
      uiAttributes.push({ node: clip, render: label }); label();
      clip.removeAttribute("aria-hidden");
      subject.append(clip);
    }
    row.append(top, subject, el("div", "message-preview", () => message.snippet?.trim() || translate("No preview text")));
    row.addEventListener("click", () => readMessage(message.id, true));
    list.append(row);
  }
}
function renderReaderPlaceholder(message = "Select a message to read it here.", retry = null) {
  stopReaderOpening();
  const empty = el("div", "reader-placeholder");
  empty.append(icon("mail"), el("h3", "", () => translate(message)));
  if (typeof retry === "function") empty.append(action("Try again", retry, "button secondary small retry-reader"));
  $("#reader").replaceChildren(empty);
  pruneUIBindings();
  if ($(".mail-workspace").classList.contains("reading")) $("#reader").prepend(readerBack());
}
function readerBack() {
  return action("← Back to messages", () => {
    state.readerSerial++;
    stopReaderOpening();
    $(".mail-workspace").classList.remove("reading");
    $("#message-list button.selected")?.focus({ preventScroll: true });
    window.scrollTo({ top: readerReturnScroll, behavior: "auto" });
  }, "text-button reader-back");
}
const readerRequests = new Set();
async function fetchReaderMessage(id, serial) {
  // Keep capacity for search and downloads. After a read finishes, fetch only
  // the newest waiting selection; obsolete rows never need their own request.
  while (readerRequests.size >= 2) {
    await Promise.race([...readerRequests].map((request) => request.catch(() => undefined)));
    if (serial !== state.readerSerial) return null;
  }
  if (serial !== state.readerSerial) return null;
  const request = api(`/api/messages/${id}`);
  readerRequests.add(request);
  try { return await request; }
  finally { readerRequests.delete(request); }
}
async function readMessage(id, navigate = true) {
  const serial = ++state.readerSerial;
  const animatePage = navigate || state.selected !== null;
  const sourceRow = $$(".message-row").find((row) => Number(row.dataset.messageId) === Number(id));
  // Capture before .reading hides the list on narrow screens.
  const sourceBounds = sourceRow?.getBoundingClientRect();
  const retryFocused = document.activeElement?.classList?.contains("retry-reader") && state.view === "archive";
  state.selected = id;
  $$(".message-row").forEach((row) => { const selected = Number(row.dataset.messageId) === Number(id); row.classList.toggle("selected", selected); row.setAttribute("aria-pressed", String(selected)); });
  if (navigate) {
    if (!$(".mail-workspace").classList.contains("reading") && window.matchMedia("(max-width: 580px)").matches) readerReturnScroll = window.scrollY;
    $(".mail-workspace").classList.add("reading");
  }
  renderReaderPlaceholder("Opening message…");
  const loadingBack = $("#reader").querySelector(".reader-back");
  // On narrow screens the selected row is now hidden. Move focus to the
  // available Back control immediately, including while the request is slow.
  if (navigate && window.matchMedia("(max-width: 580px)").matches) {
    loadingBack?.focus({ preventScroll: true });
    $("#reader").scrollIntoView({ block: "start", behavior: "auto" });
  } else if (retryFocused) {
    $("#reader").focus({ preventScroll: true });
  }
  const motionEpoch = readerMotionEpoch;
  try {
    const message = await fetchReaderMessage(id, serial);
    if (serial !== state.readerSerial) return;
    if (errorOwner === "reader") {
      $("#global-error").hidden = true;
      errorOwner = null;
    }
    const reader = $("#reader");
    const restoreBackFocus = document.activeElement === loadingBack && state.view === "archive";
    const restoreReaderFocus = retryFocused && document.activeElement === reader && state.view === "archive";
    reader.replaceChildren();
    pruneUIBindings();
    const back = readerBack();
    const head = el("header", "reader-head");
    const top = el("div", "reader-topline");
    if (message.labels) top.append(el("span", "mail-label", message.labels));
    top.append(download("Save original", `/api/messages/${id}/eml`));
    head.append(top, el("h2", "", message.subject));
    const details = el("dl", "message-details");
    for (const [label, value] of [["From", () => message.sender || translate("Unknown sender")], ["To", () => message.recipients || translate("Not provided")], ["Date", () => message.date_header || translate("Not provided")]]) {
      details.append(el("dt", "", () => translate(label)), el("dd", label === "From" ? "sender-value" : "", value));
    }
    head.append(details);
    const body = el("pre", "reader-body", () => message.body || translate("This message has no readable text body. Save the original to open it in a compatible mail app."));
    reader.append(back, head, body);
    if (message.attachments?.length) {
      const attachments = el("section", "reader-attachments");
      attachments.append(el("h3", "", () => translate(`${number(message.attachments.length)} ${message.attachments.length === 1 ? "attachment" : "attachments"}`)));
      for (const attachment of message.attachments) {
        const link = el("a", "attachment-link");
        link.href = `/api/messages/${id}/attachments/${attachment.index}`;
        link.setAttribute("download", "");
        const name = el("span", "", attachment.name);
        name.append(el("small", "", () => translate(`${bytes(attachment.size)} · ${attachment.type}`)));
        link.append(icon("clip"), name, icon("download", "download-icon"));
        attachments.append(link);
      }
      reader.append(attachments);
    }
    if (message.warnings?.length) {
      const notes = el("details", "reader-notes");
      notes.append(el("summary", "", () => translate(`${number(message.warnings.length)} reading ${message.warnings.length === 1 ? "note" : "notes"}`)));
      const list = el("ul");
      for (const warning of message.warnings) list.append(el("li", "", () => translate(warning)));
      notes.append(list);
      reader.append(notes);
    }
    reader.scrollTop = 0;
    if (navigate && restoreBackFocus && $(".mail-workspace").classList.contains("reading") && window.matchMedia("(max-width: 580px)").matches) {
      back.focus({ preventScroll: true });
    } else if (restoreReaderFocus) {
      reader.focus({ preventScroll: true });
    }
    // A resize, hidden tab, view change or motion change during fetch must not
    // restart a cancelled gesture. The fetched mail itself remains immediate.
    if (animatePage && motionEpoch === readerMotionEpoch) openReaderPage(sourceBounds);
  } catch (error) {
    if (serial !== state.readerSerial) return;
    const reader = $("#reader");
    const restoreBackFocus = document.activeElement === loadingBack && state.view === "archive";
    const restoreReaderFocus = retryFocused && document.activeElement === reader && state.view === "archive";
    renderReaderPlaceholder(error.message, () => readMessage(id, navigate));
    setError(error.message, "reader");
    if (navigate && restoreBackFocus && window.matchMedia("(max-width: 580px)").matches) {
      reader.querySelector(".reader-back")?.focus({ preventScroll: true });
    } else if (restoreReaderFocus) {
      reader.querySelector(".retry-reader")?.focus({ preventScroll: true });
    }
  }
}

function renderHistory() {
  const history = $("#import-history");
  history.replaceChildren();
  pruneUIBindings();
  const imports = state.stats?.imports || [];
  if (!imports.length) {
    const empty = el("div", "history-empty");
    empty.append(icon("import"), el("h3", "", () => translate("Your archive starts here.")), el("p", "", () => translate("Import a mail file to create your first receipt.")), action("Import mail", openImport, "button primary"));
    history.append(empty);
    return;
  }
  for (const run of imports) {
    const card = el("article", "history-card");
    const top = el("div", "history-card-top");
    const file = el("div", "history-file");
    const name = el("div");
    name.append(el("h3", "", run.name), el("p", "", () => translate(`${localTime(run.started)} · ${bytes(run.size)}`)));
    file.append(icon("archive"), name);
    top.append(file, el("span", `status-tag ${statusClass(run.status)}`, () => translate(run.status)));
    const metrics = el("div", "history-metrics");
    for (const [label, value] of [["added", run.added], ["duplicates", run.duplicates], ["not imported", run.skipped]]) {
      const metric = el("div", "history-metric");
      metric.append(el("strong", "", () => translate(number(value))), el("span", "", () => translate(label)));
      metrics.append(metric);
    }
    const actions = el("div", "history-actions");
    actions.append(action("View receipt ↗", () => showReceipt(run.id)));
    if (run.added || run.duplicates) actions.append(action("Browse mail", () => browseImport(run.id, run.name)));
    metrics.append(actions);
    card.append(top, metrics);
    if (run.note) card.append(el("p", "history-note", () => translate(run.note)));
    history.append(card);
  }
}
let browseImportSerial = 0;
async function browseImport(id, name) {
  const serial = ++browseImportSerial;
  const view = state.view, revision = viewRevision, dialogRevision = importDialogRevision, review = state.importReview, receiptSerial = state.receiptSerial;
  const importOpen = $("#import-dialog").open, receiptOpen = $("#receipt-dialog").open;
  const stillCurrent = () => serial === browseImportSerial && state.view === view && viewRevision === revision && importDialogRevision === dialogRevision && state.importReview === review &&
    state.receiptSerial === receiptSerial && $("#import-dialog").open === importOpen && $("#receipt-dialog").open === receiptOpen;
  try {
    await refreshStats();
    if (!stillCurrent()) return;
  } catch (error) {
    if (!stillCurrent()) return;
    if (importOpen && $("#import-dialog").open && state.importReview === review && !receiptOpen) {
      uiCopy($("#import-review-error"), () => error.message);
      $("#import-review-error").hidden = false;
    } else if (receiptOpen && $("#receipt-dialog").open && state.receiptSerial === receiptSerial) {
      $("#receipt-content").append(el("p", "receipt-note", () => translate(error.message)));
    }
    setError(error.message);
    return;
  }
  state.importId = String(id);
  clearSearchValues();
  uiCopy($("#source-filter-text"), () => `From import: ${name}`);
  $("#source-filter").hidden = false;
  $("#import-dialog").close();
  $("#receipt-dialog").close();
  setView("archive");
  animateSurface($("#archive-workspace"), "archive-arriving", 720);
  $("#search-input").focus({ preventScroll: true });
  await search();
}
async function showReceipt(id) {
  const serial = ++state.receiptSerial;
  const dialog = $("#receipt-dialog");
  const content = $("#receipt-content");
  const retryFocused = document.activeElement?.classList?.contains("retry-receipt") && dialog.open;
  content.replaceChildren(el("p", "dialog-description", () => translate("Loading receipt…")));
  pruneUIBindings();
  if (!dialog.open) dialog.showModal();
  if (retryFocused) {
    content.tabIndex = -1;
    content.focus({ preventScroll: true });
  }
  try {
    const run = await api(`/api/imports/${id}`);
    if (serial !== state.receiptSerial) return;
    const restoreFocus = retryFocused && document.activeElement === content && dialog.open;
    content.replaceChildren(el("p", "receipt-name", run.name));
    const meta = el("div", "receipt-meta");
    meta.append(el("span", `status-tag ${statusClass(run.status)}`, () => translate(run.status)), el("span", "", () => translate(`${localTime(run.started)} · ${bytes(run.size)}`)));
    const counts = el("div", "receipt-counts");
    for (const [label, value] of [["recognized", run.total], ["added", run.added], ["duplicates", run.duplicates], ["not imported", run.skipped]]) {
      const count = el("div");
      count.append(el("strong", "", () => translate(number(value))), el("span", "", () => translate(label)));
      counts.append(count);
    }
    content.append(meta, counts);
    if (run.note) content.append(el("p", "receipt-note", () => translate(run.note)));
    const checksum = el("div", "receipt-checksum");
    checksum.append(el("span", "", () => translate("SOURCE FILE · SHA-256")), el("code", "", run.sha256));
    const actions = el("div", "receipt-actions");
    const firstAction = download("Download full receipt", `/api/imports/${id}/receipt`, "button secondary");
    actions.append(firstAction);
    if (run.added || run.duplicates) actions.append(action("Browse imported mail", () => browseImport(run.id, run.name), "button secondary"));
    content.append(checksum, actions);
    if (run.issues?.length) {
      content.append(el("h3", "issue-heading", () => translate("Details to review")), el("p", "issue-help", () => translate("Showing up to 200 reading notes or skipped records. The full receipt includes every recognized record and its source byte offsets.")));
      const wrap = el("div", "issue-table-wrap");
      const table = el("table", "issue-table");
      const head = el("thead");
      const headings = el("tr");
      for (const label of ["Record", "Status", "What happened"]) headings.append(el("th", "", () => translate(label)));
      head.append(headings);
      const body = el("tbody");
      for (const issue of run.issues) {
        const row = el("tr");
        row.append(el("td", "", `#${issue.ordinal}`), el("td", "", () => translate(issue.status)), el("td", "", () => translate(issue.reason)));
        body.append(row);
      }
      table.append(head, body);
      wrap.append(table);
      content.append(wrap);
    }
    content.append(el("p", "dialog-description", () => translate("A receipt describes recognized records in this source file. It cannot prove a complete provider export or the authenticity of a message. Keep the original export.")));
    if (restoreFocus) firstAction.focus({ preventScroll: true });
  } catch (error) {
    if (serial === state.receiptSerial) {
      const restoreFocus = retryFocused && document.activeElement === content && dialog.open;
      const retry = action("Try again", () => showReceipt(id), "button secondary small retry-receipt");
      content.replaceChildren(el("p", "receipt-note", () => translate(error.message)), retry);
      if (restoreFocus) retry.focus({ preventScroll: true });
    }
  }
}

function openImport() {
  if (!state.busy && !state.importReview?.runs.some(run => run.added || run.duplicates)) setImportStep("choose");
  if (!$("#import-dialog").open) { importDialogRevision++; renderImportReview(); $("#import-dialog").showModal(); }
  if (!state.busy) {
    const next = $("#view-imported-mail");
    (next.hidden ? $("#choose-files") : next).focus();
  }
}
function setBusy(busy, kind = "import") {
  state.busy = busy;
  state.kind = busy ? kind : null;
  $("#stop-verify")?.remove();
  $("#task-bar").hidden = !busy;
  $("#choose-files").disabled = busy;
  $("#drop-zone").classList.toggle("busy", busy);
  $("#file-input").disabled = busy;
  $("#folder-input").disabled = busy;
  $("#choose-folder").disabled = busy;
  $("#verify-button").disabled = busy;
  $("#verify-button").classList.toggle("checking", busy && kind === "verify");
  $("#verify-button").setAttribute("aria-busy", String(busy && kind === "verify"));
  $("#cancel-import").disabled = false;
  if (busy) {
    uiCopy($("#task-bar-text"), () => kind === "verify" ? "Checking stored mail and the search index…" : "Accession in progress…");
    if (kind === "verify") {
      const stop = action("Stop check", cancelJob, "text-button");
      stop.id = "stop-verify";
      $("#task-bar").append(stop);
    }
  }
  renderImportReview();
}
function renderImportReview() {
  const review = state.importReview;
  const container = $("#import-review-actions");
  container.hidden = !review || !(review.runs.length || review.errors);
  if (!review) return;
  const added = review.runs.reduce((sum, run) => sum + Number(run.added || 0), 0);
  const duplicates = review.runs.reduce((sum, run) => sum + Number(run.duplicates || 0), 0);
  const skipped = review.runs.reduce((sum, run) => sum + Number(run.skipped || 0), 0);
  const needsReview = review.errors + review.runs.filter(run => run.status !== "complete").length;
  const summary = $("#import-review-summary");
  // One successful file already displays these counts on its receipt card.
  // Keep the summary for batches, interrupted queues and anything needing review.
  summary.hidden = !state.busy && review.runs.length === 1 && !review.errors && !review.remaining && !needsReview && !skipped;
  uiText(summary, () => translate(`${number(added)} added · ${number(duplicates)} ${duplicates === 1 ? "duplicate" : "duplicates"} · ${number(skipped)} ${skipped === 1 ? "record" : "records"} not imported · ${number(needsReview)} ${needsReview === 1 ? "file needs" : "files need"} review`) + (!state.busy && review.remaining ? " " + translate(`${number(review.remaining)} ${Number(review.remaining) === 1 ? "file was" : "files were"} not started.`) : ""));
  const eligible = review.runs.filter(run => run.added || run.duplicates);
  const button = $("#view-imported-mail");
  button.hidden = !eligible.length || state.busy;
  button.disabled = state.busy;
  uiCopy(button, () => eligible.length === 1 ? "View imported mail" : "View mail");
}
async function viewImportedMail() {
  if (state.busy) return;
  const serial = ++viewImportSerial;
  const review = state.importReview;
  const revision = viewRevision, dialogRevision = importDialogRevision;
  const eligible = review?.runs.filter(run => run.added || run.duplicates) || [];
  if (!eligible.length) return;
  const button = $("#view-imported-mail");
  button.disabled = true;
  $("#import-review-error").hidden = true;
  try {
    // Receipts prove saved records exist; refresh before navigating so a previous
    // refresh failure cannot strand the first import behind the empty state.
    await refreshStats();
    if (serial !== viewImportSerial || state.busy || state.importReview !== review || viewRevision !== revision || importDialogRevision !== dialogRevision || !$("#import-dialog").open) return;
    clearSearchValues();
    state.offset = 0;
    state.importId = eligible.length === 1 ? String(eligible[0].id) : "";
    $("#source-filter").hidden = !state.importId;
    if (state.importId) uiCopy($("#source-filter-text"), () => `From import: ${eligible[0].name}`);
    $("#import-dialog").close();
    $("#receipt-dialog").close();
    setView("archive");
    // Complete navigation before waiting for results, so a slow search cannot
    // reclaim focus or restart the entrance after the user moves elsewhere.
    animateSurface($("#archive-workspace"), "archive-arriving", 720);
    $("#search-input").focus({ preventScroll: true });
    await search();
  } catch (error) {
    if (serial !== viewImportSerial || state.importReview !== review || viewRevision !== revision || importDialogRevision !== dialogRevision || !$("#import-dialog").open) return;
    uiCopy($("#import-review-error"), () => error.message);
    $("#import-review-error").hidden = false;
    setError(error.message);
  }
  finally { if (serial === viewImportSerial && importDialogRevision === dialogRevision) button.disabled = state.busy; }
}
function importProgress(filename, stage, percent) {
  $("#import-progress").hidden = false;
  $("#import-filename").textContent = filename;
  uiCopy($("#import-stage"), () => stage);
  if (percent === null) {
    $("#import-meter").removeAttribute("value");
    uiCopy($("#import-percent"), () => "");
  } else {
    const safe = Math.max(0, Math.min(100, percent));
    $("#import-meter").value = safe;
    uiCopy($("#import-percent"), () => `${Math.round(safe)}%`);
  }
}
function upload(file) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    state.xhr = xhr;
    xhr.open("POST", `/api/import?name=${encodeURIComponent(file.name)}`);
    xhr.setRequestHeader("X-MailCairn", "1");
    xhr.setRequestHeader("Content-Type", "application/octet-stream");
    xhr.upload.addEventListener("progress", (event) => {
      setImportStep("copy");
      const percent = event.lengthComputable ? 100 * event.loaded / event.total : null;
      importProgress(file.name, "Copying to your local archive. Nothing is sent to the cloud.", percent);
      if (event.lengthComputable && event.loaded >= event.total) importProgress(file.name, "Preparing the local import…", null);
    });
    xhr.addEventListener("load", () => {
      state.xhr = null;
      let result;
      try { result = JSON.parse(xhr.responseText); } catch { reject(new Error("Unexpected response. Check Import history before trying again.")); return; }
      if (xhr.status >= 200 && xhr.status < 300) resolve(result);
      else reject(new Error(result.error || `Import failed (${xhr.status}).`));
    });
    xhr.addEventListener("error", () => { state.xhr = null; reject(new Error("The connection to MailCairn was lost. Check Import history before trying again.")); });
    xhr.addEventListener("abort", () => { state.xhr = null; reject(new Error("Upload stopped. If processing had already started, review Import history.")); });
    xhr.send(file);
  });
}
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function watchJob(id, { kind = "import", filename = "Mail import", size = 0 } = {}) {
  state.job = id;
  if (kind === "import") setImportStep("index");
  for (;;) {
    const job = await api(`/api/jobs/${id}`);
    if (job.status !== "running") {
      state.job = null;
      if (job.status === "failed") throw new Error(job.error || "The operation failed. Review Import history and try again.");
      return job.result;
    }
    const progress = job.progress || {};
    if (kind === "verify") {
      const count = progress.checked || 0;
      const total = progress.total || 0;
      uiCopy($("#task-bar-text"), () => total ? `Checking archive: ${number(count)} of ${number(total)} messages` : "Checking stored mail and the search index…");
    } else {
      const stage = `${number(progress.total)} recognized · ${number(progress.added)} added · ${number(progress.duplicates)} duplicates · ${number(progress.skipped)} not imported`;
      importProgress(filename, stage, size ? 100 * (progress.bytes_done || 0) / size : null);
      uiCopy($("#task-bar-text"), () => `Importing ${filename} · ${number(progress.added)} added`);
    }
    await pause(600);
  }
}
function appendOutcome(run, filename, error) {
  state.importReview ||= { runs: [], errors: 0 };
  if (error) state.importReview.errors++;
  else state.importReview.runs.push({ ...run, name: run.name || filename });
  const tone = error ? "error" : statusClass(run.status);
  const card = el("div", `outcome-card ${tone}`);
  card.append(el("strong", "", filename));
  if (error) card.append(el("p", "", () => translate(error)));
  else {
    card.append(el("p", "", () => translate(`${run.status === "complete" ? "Import complete" : `Import ${run.status}`} · ${number(run.added)} added · ${number(run.duplicates)} duplicates · ${number(run.skipped)} not imported`)));
    if (run.note) card.append(el("p", "", () => translate(run.note)));
    const actions = el("div", "outcome-actions");
    actions.append(action("View receipt ↗", () => showReceipt(run.id)));
    card.append(actions);
  }
  $("#import-outcomes").append(card);
  animateSurface(card, "outcome-arriving", 620);
  renderImportReview();
  if (!error && run.status === "complete" && run.added > 0) playLight($("#import-light"), "success");
}
async function startFolderImport(files) {
  if (state.busy) { toast("Wait for the current operation to finish, or stop it first."); return; }
  if (!files.length) return;
  const mail = files.filter(file => /\.(mbox|eml)$/i.test(file.name));
  const skipped = files.length - mail.length;
  uiCopy($("#folder-summary"), () => `Skipped ${number(skipped)} non-mail files (including JSON sidecars). Selected ${number(mail.length)} mail files.`);
  $("#folder-summary").hidden = false;
  if (!mail.length) { toast("No MBOX or EML files were found in this folder."); $("#folder-input").value = ""; return; }
  await startImport(mail, { folder: true });
}
async function startImport(files, { folder = false } = {}) {
  if (state.busy) { toast("Wait for the current operation to finish, or stop it first."); return; }
  if (!files.length) return;
  if (!folder) $("#folder-summary").hidden = true;
  openImport();
  setImportStep("copy");
  $("#import-outcomes").replaceChildren();
  state.importReview = { runs: [], errors: 0, remaining: files.length };
  $("#import-review-error").hidden = true;
  pruneUIBindings();
  state.cancel = false;
  setBusy(true);
  try {
    for (const [index, file] of files.entries()) {
      if (state.cancel) break;
      state.importReview.remaining = files.length - index - 1;
      $("#import-queue").hidden = files.length < 2;
      uiCopy($("#import-queue"), () => `File ${number(index + 1)} of ${number(files.length)}`);
      if (!/\.(mbox|eml)$/i.test(file.name)) { appendOutcome(null, file.name, "Choose an extracted MBOX or EML file. ZIP, PST, and other formats are not supported."); continue; }
      if (!file.size) { appendOutcome(null, file.name, "This file is empty. Choose a mail export containing messages."); continue; }
      if (file.size > state.limits.upload_bytes) { appendOutcome(null, file.name, `This file exceeds the ${bytes(state.limits.upload_bytes)} limit for this session.`); continue; }
      state.currentFile = file;
      setImportStep("copy");
      importProgress(file.name, "Preparing your local file…", 0);
      try {
        const response = await upload(file);
        if (state.cancel) await api(`/api/jobs/${response.job_id}/cancel`, { method: "POST" });
        const run = await watchJob(response.job_id, { filename: file.name, size: file.size });
        appendOutcome(run, file.name);
      } catch (error) {
        appendOutcome(null, file.name, error.message);
        // Do not flood a disconnected or busy server with the rest of a queue.
        break;
      }
      // A saved receipt remains successful if a later list refresh fails.
      // Update real archive state after each file, even while the queue runs.
      try { await refreshStats(); await search(false, { preserveSelection: true }); }
      catch (error) { setError(error.message); break; }
    }
  } finally {
    state.job = null;
    state.xhr = null;
    state.currentFile = null;
    setBusy(false);
    setImportStep("review");
    $("#import-progress").hidden = true;
    $("#file-input").value = "";
    $("#folder-input").value = "";
    try { await refreshStats({ recover: true, cancelRequested: state.cancel }); await search(false, { preserveSelection: true }); } catch (error) { setError(error.message); }
  }
}
async function cancelJob() {
  if (!state.busy) return;
  state.cancel = true;
  $("#cancel-import").disabled = true;
  if ($("#stop-verify")) $("#stop-verify").disabled = true;
  uiCopy($("#import-stage"), () => "Stopping safely… saved messages will remain in your archive.");
  if (state.xhr) state.xhr.abort();
  if (state.job) {
    try { await api(`/api/jobs/${state.job}/cancel`, { method: "POST" }); }
    catch (error) {
      setError(error.message);
      $("#cancel-import").disabled = false;
      if ($("#stop-verify")) $("#stop-verify").disabled = false;
    }
  }
}
function renderVerification(result) {
  const complete = !result.cancelled && result.checked === result.total;
  const ok = complete && result.sqlite === "ok" && result.search_index === "ok" && result.receipts === "ok" && result.mismatches?.length === 0;
  const card = el("div", `verification-card${ok ? "" : " warn"}`);
  card.append(el("h3", "", () => translate(ok ? "Your stored archive passed its checks." : result.cancelled ? "Archive check stopped." : "Your archive needs attention.")));
  card.append(el("p", "", () => translate(`${number(result.checked)} of ${number(result.total)} message hashes checked · SQLite: ${result.sqlite} · Search index: ${result.search_index} · Import receipts: ${result.receipts || "not checked"}`)));
  if (result.receipts === "failed") card.append(el("p", "", () => translate("Import receipt records are inconsistent. Keep your source exports and restore a known-good backup before relying on these counts.")));
  if (result.mismatches?.length) card.append(el("p", "", () => translate(`${number(result.mismatches.length)} messages have changed bytes. Keep the source exports and restore a known-good backup.`)));
  card.append(el("p", "", () => translate(result.scope || "Checks stored bytes and the local index only. This cannot prove your provider exported every email.")));
  if (result.verified_at) card.append(el("p", "", () => translate(`Checked ${localTime(result.verified_at)}`)));
  $("#verify-result").replaceChildren(card);
  $("#verify-result").hidden = false;
}
async function startVerify() {
  if (state.busy) return;
  state.cancel = false;
  setBusy(true, "verify");
  try {
    const response = await api("/api/verify", { method: "POST" });
    if (state.cancel) await api(`/api/jobs/${response.job_id}/cancel`, { method: "POST" });
    const result = await watchJob(response.job_id, { kind: "verify" });
    renderVerification(result);
  } catch (error) { setError(error.message); }
  finally {
    state.job = null;
    setBusy(false);
    try { await refreshStats({ recover: true, cancelRequested: state.cancel }); } catch (error) { setError(error.message); }
  }
}
async function resumeJob(job, { cancelRequested = false } = {}) {
  state.cancel = cancelRequested;
  setBusy(true, job.kind);
  try {
    state.job = job.id;
    if (cancelRequested) await cancelJob();
    const run = state.stats.imports?.find((item) => item.id === job.progress?.import_id || item.status === "running");
    const result = await watchJob(job.id, { kind: job.kind, filename: run?.name || "Existing mail import", size: run?.size || 0 });
    if (job.kind === "verify") renderVerification(result);
    else appendOutcome(result, result.name || "Mail import");
    await refreshStats();
    await search(false, { preserveSelection: true });
  } catch (error) { setError(error.message); }
  finally { state.job = null; setBusy(false); if (job.kind === "import") setImportStep("review"); $("#import-progress").hidden = true; }
}
/* Mailbox credentials exist only in the setup input and the local API request.
   Status polling never reads or stores credentials in browser storage. */
function providerName(provider) {
  return provider === "gmail" ? "Gmail" : provider === "proton" ? "Proton Mail" : translate("Other email");
}
function configureProvider(provider, { account = null } = {}) {
  if (!["gmail", "proton", "imap"].includes(provider)) return;
  connectionProvider = provider;
  $$("[data-provider]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.provider === provider));
    button.disabled = !!account || connectionSubmitting;
  });
  for (const option of ["gmail", "proton", "imap"]) $(`#${option}-setup`).hidden = option !== provider;
  const host = $("#connection-host"), port = $("#connection-port"), username = $("#connection-username");
  host.value = account?.host || (provider === "gmail" ? "imap.gmail.com" : provider === "proton" ? "127.0.0.1" : "");
  port.value = String(account?.port || (provider === "proton" ? 1143 : 993));
  $("#connection-host-field").hidden = provider !== "imap";
  $("#connection-advanced").hidden = provider === "gmail" || !!account;
  $("#connection-advanced").open = false;
  host.disabled = provider !== "imap" || !!account;
  host.required = provider === "imap";
  port.disabled = provider === "gmail" || !!account;
  username.type = provider === "gmail" ? "email" : "text";
  username.readOnly = !!account;
  if (account) username.value = account.username;
  $("#connection-password").value = "";
  uiCopy($("#connection-username-label"), () => provider === "gmail" ? "Gmail address" : provider === "proton" ? "Bridge username" : "Username");
  uiCopy($("#connection-password-label"), () => provider === "gmail" ? "App password" : provider === "proton" ? "Bridge password" : "Password or app password");
}
function updateCredentialChoice({ reset = false } = {}) {
  const available = state.connectionCapabilities?.persistent_credentials === true;
  const choice = $("#connection-remember");
  if (reset) choice.checked = available && (!reconnectingAccount || reconnectingAccount.credentials_persistent);
  if (!available) choice.checked = false;
  choice.disabled = !available || connectionSubmitting;
  $("#connection-remember-option").hidden = !available;
  $("#connection-storage-note").hidden = available && choice.checked;
  uiCopy($("#connection-storage-note"), () => !state.connectionCapabilities ? "Preparing setup…" : "You'll need to enter your password after restarting MailCairn.");
  $("#connect-submit").disabled = !state.connectionCapabilities || connectionSubmitting;
}
async function openConnect(account = null, provider = account?.provider || "gmail") {
  if (connectionSubmitting) { toast("Adding mailbox…"); return; }
  const serial = ++connectionFormSerial;
  reconnectingAccount = account;
  $("#connect-error").hidden = true;
  uiCopy($("#connect-title"), () => account ? "Reconnect mailbox" : "Connect mailbox");
  uiCopy($("#connect-submit"), () => account ? "Reconnect" : "Start syncing");
  uiText($("#connect-status"), "");
  $("#connection-username").value = account?.username || "";
  configureProvider(provider, { account });
  updateCredentialChoice({ reset: true });
  if (!$("#connect-dialog").open) $("#connect-dialog").showModal();
  $(account ? "#connection-password" : "#connection-username").focus();
  try {
    await refreshConnections();
    if (serial === connectionFormSerial && $("#connect-dialog").open) updateCredentialChoice({ reset: true });
  } catch (error) {
    if (serial === connectionFormSerial && $("#connect-dialog").open) {
      uiCopy($("#connect-error"), () => error.message);
      $("#connect-error").hidden = false;
    }
  }
}
function setConnectionFormBusy(busy) {
  connectionSubmitting = busy;
  for (const id of ["connection-username", "connection-password"]) $("#" + id).disabled = busy;
  $("#connection-host").disabled = busy || connectionProvider !== "imap" || !!reconnectingAccount;
  $("#connection-port").disabled = busy || connectionProvider === "gmail" || !!reconnectingAccount;
  $$("[data-provider]").forEach(button => { button.disabled = busy || !!reconnectingAccount; });
  updateCredentialChoice();
  $("#connection-form").setAttribute("aria-busy", String(busy));
}
async function submitConnection(event) {
  event.preventDefault();
  if (connectionSubmitting || !state.connectionCapabilities) return;
  const username = $("#connection-username").value.trim();
  const host = $("#connection-host").value.trim();
  const port = Number($("#connection-port").value);
  let password = $("#connection-password").value;
  if (connectionProvider === "gmail") password = password.replace(/ /g, "");
  if (!username || !password || !host || !Number.isInteger(port) || port < 1 || port > 65535) {
    if (!Number.isInteger(port) || port < 1 || port > 65535) $("#connection-advanced").open = true;
    uiCopy($("#connect-error"), "Enter the mailbox details and password to continue.");
    $("#connect-error").hidden = false;
    return;
  }
  const serial = connectionFormSerial;
  const body = JSON.stringify({ provider: connectionProvider, host, port, username, password, remember: state.connectionCapabilities.persistent_credentials === true && $("#connection-remember").checked, folder: reconnectingAccount?.folder || "INBOX" });
  password = "";
  $("#connection-password").value = "";
  $("#connect-error").hidden = true;
  setConnectionFormBusy(true);
  uiCopy($("#connect-status"), "Adding mailbox…");
  let saved = false;
  try {
    await api("/api/connections", { method: "POST", headers: { "Content-Type": "application/json" }, body });
    saved = true;
    await refreshConnections();
    if (serial === connectionFormSerial && $("#connect-dialog").open) {
      $("#connect-dialog").close();
      setView("connections");
    }
    toast("Mailbox added. Check its sync status below.");
    connectionPollingStarted = true;
    scheduleConnectionPoll(1000);
  } catch (error) {
    const message = saved ? "Mailbox settings were saved, but status could not refresh. Open Mailboxes to check before adding it again." : error.message;
    if (serial === connectionFormSerial && $("#connect-dialog").open) {
      uiCopy($("#connect-error"), () => message);
      $("#connect-error").hidden = false;
    } else setError(message);
  } finally {
    $("#connection-password").value = "";
    setConnectionFormBusy(false);
    uiText($("#connect-status"), "");
  }
}
// Keep the backend's stable error strings intact; only recognized network errors
// get contextual UI copy. Unknown/provider errors must remain visible verbatim.
function connectionNetworkError(account) {
  return account.last_error === "Could not connect securely. Check the server, port and network.";
}
function connectionIncompleteResponse(account) {
  return account.last_error === "The server returned an unsupported or incomplete IMAP response.";
}
function connectionErrorCopy(account) {
  if (connectionIncompleteResponse(account)) return translate("The mailbox sent an incomplete or unsupported response. Try syncing again.");
  if (!connectionNetworkError(account)) return translate(account.last_error);
  return translate(account.provider === "gmail"
    ? "Cannot connect to Gmail right now. Your saved mail is still available."
    : "Cannot connect to this mailbox right now. Your saved mail is still available.");
}
function connectionStatus(account) {
  if (account.paused) return "Paused";
  if (account.credentials_available === false || account.status === "auth_required") return "Password needed";
  if (account.status === "error" && connectionNetworkError(account)) return "Connection unavailable";
  return ({ idle: account.last_sync ? "Up to date" : "Ready to sync", queued: "Queued", syncing: "Syncing mail…", waiting: "Waiting for the archive", error: "Needs attention" })[account.status] || "Ready to sync";
}
const connectionCards = new Map();
function renderConnections() {
  const focused = document.activeElement?.dataset;
  const focusedAction = focused?.connectionAction || focused?.connectionFocusAction;
  const focusKey = focused?.connectionId && focusedAction ? [focused.connectionId, focusedAction] : null;
  const list = $("#connections-list");
  const cards = new Map();
  const ordered = [], changes = [];
  if (!state.connections?.length || !connectionCards.size) {
    for (const entry of connectionCards.values()) settleSurface(entry.statusNode);
    connectionCards.clear();
    list.replaceChildren();
    uiText($("#connections-announcement"), "");
    pruneUIBindings();
  }
  if (state.connections === null) {
    list.append(el("p", "connections-loading", () => translate("Loading mailboxes…")));
    return;
  }
  if (!state.connections.length) {
    const empty = el("div", "history-empty connection-empty");
    const connect = action("Connect mailbox", () => openConnect(), "button primary");
    empty.append(icon("mail"), el("h3", "", () => translate("Connect your first mailbox")), el("p", "", () => translate("Mail from INBOX will be saved here automatically.")), connect);
    list.append(empty);
    if (focusKey && state.view === "connections") connect.focus({ preventScroll: true });
    return;
  }
  for (const account of state.connections) {
    const id = String(account.id);
    const accountSignature = JSON.stringify(account);
    const signature = accountSignature + connectionActions.has(id);
    const previous = connectionCards.get(id);
    if (previous?.accountSignature === accountSignature) {
      if (previous.signature !== signature) {
        for (const button of previous.node.querySelectorAll("[data-connection-action]")) {
          button.disabled = connectionActions.has(id) || (button.dataset.connectionAction === "sync" && (account.paused || ["syncing", "queued", "waiting"].includes(account.status)));
        }
        previous.signature = signature;
      }
      cards.set(id, previous.node);
      ordered.push(previous.node);
      continue;
    }
    const card = el("article", "connection-card");
    card.tabIndex = -1;
    card.dataset.connectionId = String(account.id);
    card.setAttribute("aria-label", account.username);
    cards.set(String(account.id), card);
    const top = el("div", "connection-card-top");
    const identity = el("div", "connection-identity");
    identity.append(el("h3", "", account.username), el("p", "", () => providerName(account.provider)));
    const status = el("span", `status-tag${account.status === "error" || account.status === "auth_required" ? " warn" : ""}`, () => translate(connectionStatus(account)));
    const label = connectionStatus(account);
    if (previous && previous.label !== label && state.view === "connections" && !document.hidden) {
      changes.push({ username: account.username, label });
    }
    top.append(identity, status);
    const metrics = el("div", "connection-metrics");
    const total = el("div");
    total.append(el("strong", "", () => number(account.added)), el("span", "", () => translate("Saved from this mailbox")));
    const activity = el("div", "connection-activity");
    activity.append(el("p", "", () => account.last_sync ? translate(`Last successful sync: ${localTime(account.last_sync)}`) : translate("Not synced yet")));
    // These counters reset at each attempt; they do not belong to last_sync
    // while an attempt is queued, running, interrupted or unsuccessful.
    if (account.last_sync && account.status === "idle" && !account.paused && !account.last_error && account.credentials_available === true) {
      activity.append(el("p", "", () => translate(`${number(account.last_added)} added · ${number(account.last_duplicates)} duplicates in the last successful sync`)));
    }
    metrics.append(total, activity);
    card.append(top, metrics);
    if (account.last_error) card.append(el("p", "connection-error", () => connectionErrorCopy(account)));
    if ((connectionNetworkError(account) || connectionIncompleteResponse(account)) && account.status === "error" && !account.paused && account.credentials_available === true) {
      card.append(el("p", "connection-retry", () => translate("MailCairn retries every 5 minutes while it is running.")));
    }
    const bottom = el("div", "connection-card-bottom");
    const actions = el("div", "connection-actions");
    const addAction = (name, label, handler, className = "text-button") => {
      const button = action(label, handler, className);
      button.setAttribute("data-connection-id", String(account.id));
      button.setAttribute("data-connection-action", name);
      button.disabled = connectionActions.has(String(account.id));
      actions.append(button);
      return button;
    };
    const needsPassword = account.credentials_available === false || account.status === "auth_required" || account.last_error?.startsWith("Authentication failed.");
    if (needsPassword) addAction("reconnect", "Reconnect", () => openConnect(account), "button secondary small");
    else {
      const sync = addAction("sync", "Sync now", () => runConnectionAction(account, "sync"), "button secondary small");
      sync.disabled ||= account.paused || ["syncing", "queued", "waiting"].includes(account.status);
    }
    if (!needsPassword || !account.paused) addAction(account.paused ? "resume" : "pause", account.paused ? "Resume" : "Pause", () => runConnectionAction(account, account.paused ? "resume" : "pause"));
    if (account.added > 0 || account.last_duplicates > 0) addAction("mail", "View mail", async () => {
      try {
        await refreshStats({ quiet: true });
        if (state.view !== "connections") return;
        clearSearchValues();
        state.importId = "";
        state.archiveDirty = false;
        $("#source-filter").hidden = true;
        setView("archive");
        await search();
      } catch (error) { showConnectionsError(error); }
    });
    if (account.last_receipt_id) addAction("receipt", "View receipt ↗", () => showReceipt(account.last_receipt_id));
    addAction("disconnect", "Disconnect", () => runConnectionAction(account, "disconnect"), "text-button disconnect-button");
    bottom.append(actions);
    card.append(bottom);
    if (previous) { settleSurface(previous.statusNode); previous.node.remove(); }
    connectionCards.set(id, { node: card, statusNode: status, signature, accountSignature, label });
    ordered.push(card);
    if (previous && previous.label !== label && state.view === "connections") animateSurface(status, "connection-status-changing", 520);
  }
  for (const [id, entry] of connectionCards) {
    if (!cards.has(id)) { settleSurface(entry.statusNode); entry.node.remove(); connectionCards.delete(id); }
  }
  ordered.forEach((card, index) => {
    if (list.children[index] !== card) list.insertBefore(card, list.children[index] || null);
  });
  pruneUIBindings();
  if (changes.length) uiText($("#connections-announcement"), () => changes.map(item => `${item.username}: ${translate(item.label)}`).join("; "));
  if (focusKey && state.view === "connections") {
    const replacement = { pause: "resume", resume: "pause" }[focusKey[1]];
    const candidates = [...list.querySelectorAll("[data-connection-action]")].filter(button => button.dataset.connectionId === focusKey[0] && !button.disabled);
    const target = candidates.find(button => button.dataset.connectionAction === focusKey[1])
      || candidates.find(button => button.dataset.connectionAction === replacement);
    if (target) { if (document.activeElement !== target) target.focus({ preventScroll: true }); }
    else if (cards.has(focusKey[0])) {
      const card = cards.get(focusKey[0]);
      card.dataset.connectionFocusAction = focusKey[1];
      card.focus({ preventScroll: true });
    } else $(".page-actions [data-open-connect]")?.focus({ preventScroll: true });
  }
}
function showConnectionsError(error) {
  const target = $("#connections-error");
  target.replaceChildren(el("span", "", () => translate(error.message || error)), action("Try again", () => refreshConnections().catch(showConnectionsError)));
  target.hidden = false;
}
async function refreshConnections({ signal } = {}) {
  const serial = ++connectionsSerial;
  const result = await api("/api/connections", signal ? { signal } : {});
  if (signal?.aborted || serial !== connectionsSerial) return;
  state.connections = Array.isArray(result.connections) ? result.connections : [];
  state.connectionCapabilities = result.capabilities || { persistent_credentials: false };
  uiText($("#connection-count"), () => number(state.connections.length));
  $("#connection-count").hidden = !state.connections.length;
  $("#connections-error").hidden = true;
  if (result.settings_error) showConnectionsError(result.settings_error);
  const signature = JSON.stringify(state.connections) + JSON.stringify([...connectionActions]);
  if (signature !== connectionsSignature) {
    connectionsSignature = signature;
    renderConnections();
  }
}
async function runConnectionAction(account, operation) {
  const id = String(account.id);
  if (connectionActions.has(id)) return;
  connectionActions.add(id);
  renderConnections();
  try {
    const result = await api(`/api/connections/${encodeURIComponent(id)}/${operation}`, { method: "POST" });
    const warning = result.connection?.warning;
    if (operation === "disconnect" && !warning) toast("Mailbox disconnected. Archived mail was kept.");
    if (warning) setError(warning);
    await refreshConnections();
  } catch (error) { showConnectionsError(error); }
  finally {
    connectionActions.delete(id);
    connectionsSignature = "";
    renderConnections();
    scheduleConnectionPoll(1000);
  }
}
function activeConnections() {
  return state.connections?.some(account => !account.paused && account.credentials_available !== false) || false;
}
function scheduleConnectionPoll(delay = 8000) {
  clearTimeout(connectionPollTimer);
  connectionPollTimer = 0;
  // Until discovery succeeds, an unavailable status endpoint does not mean
  // there are no mailboxes. Retry at the normal interval without idle polling
  // once an empty or inactive list is known.
  if (!connectionPollingStarted || document.hidden || (state.connections !== null && !activeConnections() && state.view !== "connections")) return;
  connectionPollTimer = setTimeout(pollConnections, delay);
}
async function pollConnections() {
  connectionPollTimer = 0;
  if (!connectionPollingStarted || document.hidden || connectionPollController) return;
  const controller = new AbortController();
  connectionPollController = controller;
  try {
    await refreshConnections({ signal: controller.signal });
    if (controller.signal.aborted || document.hidden) return;
    if (activeConnections() && !state.busy) {
      const before = state.stats;
      const stats = await refreshStats({ quiet: true, signal: controller.signal });
      if (controller.signal.aborted || !stats) return;
      const changed = before?.messages !== stats.messages || before?.raw_bytes !== stats.raw_bytes || before?.attachments !== stats.attachments;
      if (changed) {
        state.archiveDirty = true;
        if (state.view === "archive" && (!before?.messages || state.searchReady)) await search(false, { preserveSelection: true });
      }
    }
  } catch (error) {
    if (!controller.signal.aborted && state.view === "connections") showConnectionsError(error);
  } finally {
    if (connectionPollController === controller) connectionPollController = null;
    scheduleConnectionPoll();
  }
}
function stopConnectionPolling() {
  clearTimeout(connectionPollTimer);
  connectionPollTimer = 0;
  connectionPollController?.abort();
}
function bindConnections() {
  $$("[data-open-connect]").forEach(button => button.addEventListener("click", () => openConnect()));
  $$("[data-provider]").forEach(button => button.addEventListener("click", () => {
    if (!connectionSubmitting && !reconnectingAccount) configureProvider(button.dataset.provider);
  }));
  $("#connection-remember").addEventListener("change", () => updateCredentialChoice());
  $("#connection-port").addEventListener("invalid", () => { $("#connection-advanced").open = true; });
  $("#mailbox-setup-help").addEventListener("click", () => {
    $("#connect-dialog").close();
    setView("guide");
    $(`#mailbox-guide-${connectionProvider}`).open = true;
    $("#mailbox-guide-title").focus({ preventScroll: true });
    $("#mailbox-setup-guide").scrollIntoView?.({ block: "start", behavior: motionAllowed() ? "smooth" : "auto" });
  });
  $$("[data-connect-provider]").forEach(button => button.addEventListener("click", () => openConnect(null, button.dataset.connectProvider)));
  $("#connection-form").addEventListener("submit", submitConnection);
  $("#connect-dialog").addEventListener("close", () => { $("#connection-password").value = ""; connectionFormSerial++; });
  document.addEventListener("visibilitychange", () => { if (document.hidden) stopConnectionPolling(); else scheduleConnectionPoll(0); });
  window.addEventListener("pagehide", () => { connectionPollingStarted = false; stopConnectionPolling(); });
}
function clearSearchValues() {
  $("#search-input").value = "";
  $("#filter-sender").value = "";
  $("#filter-after").value = "";
  $("#filter-before").value = "";
  $("#filter-attachments").checked = false;
  updateFilterBadge();
}
function clearEverything() {
  clearSearchValues();
  state.importId = "";
  $("#source-filter").hidden = true;
  $("#global-error").hidden = true;
  search();
}

function bindSessionNavigation() {
  if (sessionNavigationBound) return;
  sessionNavigationBound = true;
  window.addEventListener("hashchange", () => {
    const token = new URLSearchParams(window.location.hash.slice(1)).get("session");
    // Launch tokens are 32 random bytes encoded as URL-safe base64. A fresh
    // launch URL in an existing tab changes only its hash, so rerun startup.
    if (/^[A-Za-z0-9_-]{43}$/.test(token || "")) location.reload();
  });
}
function bindEvents() {
  bindSessionNavigation();
  bindConnections();
  $("#view-imported-mail").addEventListener("click", viewImportedMail);
  $$("[data-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
  $(".brand").addEventListener("click", (event) => { event.preventDefault(); setView("archive"); });
  $$("[data-open-import]").forEach((button) => button.addEventListener("click", openImport));
  $$("[data-close-dialog]").forEach((button) => button.addEventListener("click", () => document.getElementById(button.dataset.closeDialog).close()));
  $("#dismiss-error").addEventListener("click", () => { $("#global-error").hidden = true; });
  $("#choose-files").addEventListener("click", () => $("#file-input").click());
  $("#file-input").addEventListener("change", (event) => startImport([...event.target.files]));
  const folderInput = $("#folder-input");
  $("#choose-folder").hidden = !("webkitdirectory" in folderInput);
  $("#folder-help").hidden = !("webkitdirectory" in folderInput);
  $("#choose-folder").addEventListener("click", () => folderInput.click());
  folderInput.addEventListener("change", (event) => startFolderImport([...event.target.files]));
  const drop = $("#drop-zone");
  for (const type of ["dragenter", "dragover"]) drop.addEventListener(type, (event) => { event.preventDefault(); if (!state.busy) drop.classList.add("dragover"); });
  for (const type of ["dragleave", "drop"]) drop.addEventListener(type, (event) => { event.preventDefault(); drop.classList.remove("dragover"); });
  drop.addEventListener("drop", (event) => { if (!state.busy) startImport([...event.dataTransfer.files]); });
  // Prevent a dropped file outside the target from replacing the app page.
  window.addEventListener("dragover", (event) => { if ([...event.dataTransfer.types].includes("Files")) event.preventDefault(); });
  window.addEventListener("drop", (event) => { if ([...event.dataTransfer.types].includes("Files")) event.preventDefault(); });
  $("#cancel-import").addEventListener("click", cancelJob);
  $("#show-task").addEventListener("click", () => {
    if (state.kind === "verify") {
      setView("imports");
    } else openImport();
  });
  $("#verify-button").addEventListener("click", startVerify);
  $("#filter-toggle").addEventListener("click", () => {
    const expanded = $("#filter-panel").hidden;
    $("#filter-panel").hidden = !expanded;
    $("#filter-toggle").setAttribute("aria-expanded", String(expanded));
    if (expanded) {
      animateSurface($("#filter-panel"), "filters-opening", 420);
      $("#filter-sender").focus();
    } else settleSurface($("#filter-panel"));
  });
  $("#search-form").addEventListener("submit", (event) => { event.preventDefault(); clearTimeout(searchTimer); search(); });
  $("#retry-search").addEventListener("click", () => {
    if (!failedSearch || failedSearch.serial !== state.searchSerial) return;
    const attempt = failedSearch;
    search(attempt.reset, attempt);
  });
  for (const id of ["search-input", "filter-sender"]) document.getElementById(id).addEventListener("input", () => {
    // Invalidate at the edit, not when the debounce expires: an older response
    // must not enable exporting its results under the newly entered query.
    state.searchSerial++;
    failedSearch = null;
    $("#retry-search").hidden = true;
    state.searchReady = false;
    $("#export-results").setAttribute("aria-disabled", "true");
    $("#previous-page").disabled = true;
    $("#next-page").disabled = true;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => search(), 250);
  });
  for (const id of ["filter-after", "filter-before", "filter-attachments"]) document.getElementById(id).addEventListener("change", () => search());
  $("#clear-filters").addEventListener("click", () => {
    for (const id of ["filter-sender", "filter-after", "filter-before"]) document.getElementById(id).value = "";
    $("#filter-attachments").checked = false;
    $("#global-error").hidden = true;
    search();
  });
  $("#clear-source").addEventListener("click", () => { state.importId = ""; $("#source-filter").hidden = true; search(); });
  $("#reset-search").addEventListener("click", clearEverything);
  $("#previous-page").addEventListener("click", () => search(false, { offset: Math.max(0, state.offset - 50), scrollResults: true }));
  $("#next-page").addEventListener("click", () => search(false, { offset: state.offset + 50, scrollResults: true }));
  $("#export-results").addEventListener("click", (event) => {
    if (!state.searchReady) { event.preventDefault(); toast("Wait for a successful search before exporting results."); }
    else if (!state.result?.total) { event.preventDefault(); toast("There are no matching messages to export."); }
    else toast("Preparing your MBOX download. Large exports may take a moment.");
  });
  $$("a[href='/api/backup']").forEach((link) => link.addEventListener("click", () => toast("Preparing a consistent archive backup. Large archives may take a moment.")));
  window.addEventListener("keydown", (event) => {
    if (preferences.shortcuts && event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName) && !document.querySelector("dialog[open]") && state.stats?.messages) {
      event.preventDefault(); setView("archive"); $("#search-input").focus();
    }
  });
  window.addEventListener("beforeunload", (event) => { if (state.xhr) { event.preventDefault(); event.returnValue = ""; } });
}

async function initialize() {
  let interfaceBound = false;
  try {
    bindLanguage();
    bindEvents();
    bindReadingRoom();
    interfaceBound = true;
    const hash = new URLSearchParams(window.location.hash.slice(1));
    const token = hash.get("session");
    if (token) {
      await api("/api/session", { method: "POST", headers: { "X-MailCairn-Token": token } });
      history.replaceState(null, "", window.location.pathname);
    }
    await refreshStats({ recover: true });
    $("#loading-screen").hidden = true;
    setView("archive");
    if (state.stats.messages) await search();
    window.MailCairnStartup?.ready();
    connectionPollingStarted = true;
    refreshConnections().then(() => scheduleConnectionPoll(1000)).catch(error => {
      showConnectionsError(error);
      scheduleConnectionPoll();
    });
  } catch (error) {
    if (!interfaceBound && window.MailCairnStartup) {
      window.MailCairnStartup.fail();
      return;
    }
    $("#loading-screen").hidden = true;
    const box = el("section", "reconnect-box");
    box.append(el("h2", "", () => translate(error.status === 401 ? "Open your local archive." : "Let’s reconnect your archive.")), el("p", "", () => translate(error.message)), el("p", "", () => translate("Choose “Open archive” in the MailCairn window, or use the link from your usual startup command.")), action("Try again", () => location.reload(), "button secondary"));
    $("#main-content").insertBefore(box, $(".main-footer"));
    window.MailCairnStartup?.ready();
    $$("[data-open-import]").forEach((button) => { button.disabled = true; });
    $$("[data-open-connect]").forEach((button) => { button.disabled = true; });
  }
}

/* Browser-only preferences never contain mail, file paths, or account data. */
const preferenceKey = "mailcairn.reading-room.v1";
const preferenceDefaults = Object.freeze({ theme: "system", accent: "cedar", type: "standard", density: "comfortable", motion: true, atmosphere: "quiet", shortcuts: true });
const preferenceValues = { theme: ["system", "light", "dark"], accent: ["cedar", "blue", "umber"], type: ["small", "standard", "large"], density: ["comfortable", "compact"], atmosphere: ["quiet", "full"] };
const darkMedia = window.matchMedia("(prefers-color-scheme: dark)");
const reducedMedia = window.matchMedia("(prefers-reduced-motion: reduce)");
let preferences = { ...preferenceDefaults };
let preferencesWritable = true;
function validatedPreferences(value) {
  const clean = { ...preferenceDefaults };
  if (!value || typeof value !== "object" || Array.isArray(value)) return clean;
  for (const [key, choices] of Object.entries(preferenceValues)) if (choices.includes(value[key])) clean[key] = value[key];
  if (typeof value.motion === "boolean") clean.motion = value.motion;
  if (typeof value.shortcuts === "boolean") clean.shortcuts = value.shortcuts;
  return clean;
}
function loadPreferences() {
  try { return validatedPreferences(JSON.parse(localStorage.getItem(preferenceKey))); }
  catch { return { ...preferenceDefaults }; }
}
const motionAllowed = () => preferences.motion && !reducedMedia.matches;
function applyPreferences({ save = false } = {}) {
  const root = document.documentElement;
  const theme = preferences.theme === "system" ? (darkMedia.matches ? "dark" : "light") : preferences.theme;
  const paletteChanged = root.dataset.theme !== theme || root.dataset.accent !== preferences.accent;
  // Commit foreground and background together. Hover transitions resume after
  // this style flush; no frame is painted with a partially changed palette.
  if (paletteChanged) root.classList.add("palette-changing");
  root.dataset.theme = theme;
  for (const key of ["accent", "type", "density", "atmosphere"]) root.dataset[key] = preferences[key];
  if (paletteChanged) {
    void root.offsetWidth;
    root.classList.remove("palette-changing");
  }
  root.dataset.motion = motionAllowed() ? "on" : "off";
  document.querySelector('meta[name="theme-color"]').content = root.dataset.theme === "dark" ? "#191c1a" : "#eae7df";
  if (!motionAllowed()) {
    stopAllLights(); resetPaperTilt();
    $$(".result-arriving").forEach((row) => row.classList.remove("result-arriving"));
  }
  for (const [key, value] of Object.entries(preferences)) {
    if (key === "motion") $("#motion-preference").checked = value;
    else if (key === "shortcuts") $("#shortcut-preference").checked = value;
    else {
      const input = $(`#preferences-form input[name="${key}"][value="${value}"]`);
      if (input) input.checked = true;
    }
  }
  if (save) {
    try { localStorage.setItem(preferenceKey, JSON.stringify(preferences)); preferencesWritable = true; }
    catch { preferencesWritable = false; }
  }
  uiCopy($("#preference-status"), () => preferencesWritable ? "Saved only in this browser" : "Applied for this visit · storage unavailable");
}
function openPreferences() {
  const dialog = $("#preferences-dialog");
  if (!dialog.open) dialog.showModal();
  ($(`#preferences-form input[name="theme"][value="${preferences.theme}"]`) || $("#preferences-form input[name=\"theme\"]"))?.focus();
}
function keepDialogFocus(event) {
  if (event.key !== "Tab" || event.ctrlKey || event.metaKey || event.altKey) return;
  const dialog = event.currentTarget;
  if (!dialog.open) return;
  const controls = [...dialog.querySelectorAll('button, a[href], input:not([type="hidden"]), select, textarea, summary, [tabindex]')].filter(node => {
    if (node.tabIndex < 0 || node.matches(":disabled") || node.closest("[hidden], [inert]")) return false;
    if (node.tagName) {
      const detailsCheck = node.tagName === "SUMMARY" && node.parentElement?.tagName === "DETAILS"
        ? node.parentElement.parentElement?.closest("details:not([open])")
        : node.closest("details:not([open])");
      if (detailsCheck) return false;
    }
    return node.getClientRects().length && getComputedStyle(node).visibility === "visible";
  });
  const first = controls[0], last = controls.at(-1);
  const destination = !first ? dialog :
    document.activeElement === dialog ? (event.shiftKey ? last : first) :
    event.shiftKey && document.activeElement === first ? last :
    !event.shiftKey && document.activeElement === last ? first : null;
  if (destination) { event.preventDefault(); destination.focus(); }
}
function setImportStep(step) {
  const dialog = $("#import-dialog");
  if (dialog.dataset.importPhase !== step) {
    dialog.dataset.importPhase = step;
    animateSurface(dialog, "import-stage-changing", 500);
  }
  let passed = true;
  $$("[data-import-step]").forEach((node) => {
    if (node.dataset.importStep === step) { node.setAttribute("aria-current", "step"); passed = false; }
    else node.removeAttribute("aria-current");
    node.classList.toggle("step-done", passed);
  });
}

/* Bounded light studies: 110 motes maximum, 1.5M backing pixels, 30fps.
   Mail text is never a canvas surface. No idle animation or automatic replay. */
const lightRuns = new Map();
let archiveIlluminated = false;
function stopLight(canvas) {
  const run = lightRuns.get(canvas);
  if (run) cancelAnimationFrame(run.frame);
  lightRuns.delete(canvas);
  const ctx = canvas?.getContext("2d");
  if (ctx) {
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.restore();
  }
}
function stopAllLights() {
  for (const canvas of [...lightRuns.keys()]) stopLight(canvas);
  stopPaperUnfold();
  stopReaderOpening();
  for (const node of [...surfaceTransitions.keys()]) settleSurface(node);
}
function playLight(canvas, kind = "archive") {
  if (!canvas || !motionAllowed() || document.hidden || !canvas.getClientRects().length) return;
  stopLight(canvas);
  const bounds = canvas.getBoundingClientRect();
  if (!bounds.width || !bounds.height || bounds.bottom <= 0 || bounds.top >= window.innerHeight || bounds.right <= 0 || bounds.left >= window.innerWidth) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const width = bounds.width, height = bounds.height;
  const dpr = Math.min(window.devicePixelRatio || 1, 2, Math.sqrt(1500000 / (width * height)));
  canvas.width = Math.floor(width * dpr); canvas.height = Math.floor(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const full = preferences.atmosphere === "full";
  const duration = kind === "success" ? 1800 : full ? 4800 : 4200;
  const colors = { cedar: [232, 209, 146], blue: [164, 208, 238], umber: [244, 183, 122] };
  const rgb = colors[preferences.accent].join(",");
  const dark = document.documentElement.dataset.theme === "dark";
  const count = kind === "success" ? (full ? 42 : 28) : full ? 64 : 24;
  const particles = Array.from({ length: count }, (_, index) => ({
    x: Math.random() * width, y: Math.random() * height,
    layer: index % 5, radius: .45 + (index % 5) * .55,
    speed: 3 + (index % 5) * 3, phase: Math.random() * Math.PI * 2,
    drift: 2 + Math.random() * 9
  }));
  const run = { frame: 0, started: performance.now(), lastDraw: -100 };
  lightRuns.set(canvas, run);
  function draw(now) {
    const elapsed = now - run.started;
    if (elapsed >= duration || document.hidden || !motionAllowed()) { stopLight(canvas); return; }
    run.frame = requestAnimationFrame(draw);
    if (now - run.lastDraw < 32) return;
    run.lastDraw = now;
    const t = elapsed / duration, seconds = elapsed / 1000;
    const fade = Math.min(1, t * 5) * Math.min(1, (1 - t) * 4);
    ctx.clearRect(0, 0, width, height);
    // Several independent window shafts, with feathered edges and a warm source.
    const source = width * (.58 + Math.sin(t * Math.PI) * .07);
    if (full) {
      const halo = ctx.createRadialGradient(source, -height * .08, 0, source, 0, width * .68);
      halo.addColorStop(0, `rgba(${rgb},${fade * (dark ? .48 : .26)})`);
      halo.addColorStop(.24, `rgba(${rgb},${fade * .12})`);
      halo.addColorStop(1, `rgba(${rgb},0)`);
      ctx.fillStyle = halo; ctx.fillRect(0, 0, width, height);
    }
    const beams = full ? 5 : 1;
    for (let beam = 0; beam < beams; beam++) {
      ctx.save();
      const center = source + (beam - 2) * width * .095;
      const spread = width * (full ? .028 + (beam % 2) * .022 : .16);
      ctx.transform(1, 0, -.58 + beam * .035, 1, height * .22, 0);
      const shaft = ctx.createLinearGradient(center - spread * 2, 0, center + spread * 2, 0);
      shaft.addColorStop(0, `rgba(${rgb},0)`);
      shaft.addColorStop(.42, `rgba(${rgb},${fade * (full ? .18 : .09)})`);
      shaft.addColorStop(.5, `rgba(${rgb},${fade * (full ? .32 : .13)})`);
      shaft.addColorStop(.63, `rgba(${rgb},${fade * .07})`);
      shaft.addColorStop(1, `rgba(${rgb},0)`);
      ctx.fillStyle = shaft; ctx.fillRect(center - spread * 2, 0, spread * 4, height);
      ctx.restore();
    }
    // Distant dust stays small; near motes have soft bokeh and a bright core.
    for (const particle of particles) {
      const x = particle.x + Math.sin(seconds * .45 + particle.phase) * (4 + particle.layer * 4) - particle.drift * seconds;
      const y = particle.y - particle.speed * seconds;
      const glow = .45 + .55 * Math.pow(Math.sin(seconds * .7 + particle.phase), 2);
      const alpha = fade * glow * (dark ? .85 : .62);
      if (full && particle.layer >= 3) {
        const radius = particle.radius * (particle.layer === 4 ? 5 : 3);
        const halo = ctx.createRadialGradient(x, y, 0, x, y, radius);
        halo.addColorStop(0, `rgba(${rgb},${alpha * .38})`);
        halo.addColorStop(1, `rgba(${rgb},0)`);
        ctx.fillStyle = halo; ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2);
      }
      ctx.beginPath(); ctx.fillStyle = `rgba(${rgb},${alpha})`;
      ctx.arc(x, y, particle.radius, 0, Math.PI * 2); ctx.fill();
    }
  }
  run.frame = requestAnimationFrame(draw);
}
function illuminateArchive() {
  if (archiveIlluminated || state.stats?.messages !== 0) return;
  archiveIlluminated = true;
  if (!motionAllowed() || document.hidden) return;
  requestAnimationFrame(() => {
    if (state.view !== "archive" || !motionAllowed() || document.hidden) return;
    unfoldArchive();
    playLight($("#archive-light"));
  });
}
let paperUnfoldTimer = 0;
function stopPaperUnfold() {
  clearTimeout(paperUnfoldTimer);
  $(".archive-object")?.classList.remove("paper-unfolding");
}
function unfoldArchive() {
  stopPaperUnfold();
  const paper = $(".archive-object");
  if (!paper || !motionAllowed() || document.hidden || state.view !== "archive") return;
  // Restart the physical fan, including when replay is pressed during its entrance.
  void paper.offsetWidth;
  paper.classList.add("paper-unfolding");
  paperUnfoldTimer = setTimeout(stopPaperUnfold, 2500);
}
function positionNavMarker() {
  const nav = $(".nav-list"), marker = $(".nav-marker");
  const active = $$("[data-view]").find((item) => item.classList.contains("active"));
  if (!nav || !marker || !active) return;
  const parent = nav.getBoundingClientRect(), target = active.getBoundingClientRect();
  const horizontal = window.matchMedia("(max-width: 760px)").matches;
  const axis = horizontal ? "horizontal" : "vertical";
  const changedAxis = marker.dataset.axis !== axis;
  if (changedAxis) marker.style.setProperty("transition", "none");
  marker.style.setProperty("width", horizontal ? `${Math.max(12, target.width - 32)}px` : "3px");
  marker.style.setProperty("height", horizontal ? "3px" : `${Math.max(12, target.height - 24)}px`);
  marker.style.setProperty("transform", `translate(${target.left - parent.left + (horizontal ? 16 : 0)}px, ${target.top - parent.top + (horizontal ? target.height - 3 : 12)}px)`);
  if (changedAxis) {
    void marker.offsetWidth;
    marker.style.removeProperty("transition");
  }
  marker.dataset.axis = axis;
}
let readerOpening = null;
let readerFlight = null;
let readerMotionEpoch = 0;
function stopReaderOpening() {
  readerMotionEpoch++;
  const opening = readerOpening;
  readerOpening = null;
  opening?.cancel();
  const flight = readerFlight;
  readerFlight = null;
  flight?.animation.cancel();
  flight?.node.remove();
  $("#reader")?.classList.remove("reader-opening");
}
function flyMessagePaper(sourceBounds, reader) {
  if (!sourceBounds?.width || !sourceBounds.height || sourceBounds.bottom <= 0 || sourceBounds.top >= window.innerHeight || sourceBounds.right <= 0 || sourceBounds.left >= window.innerWidth) return;
  const bodyBounds = reader.querySelector(".reader-body")?.getBoundingClientRect();
  // Land in the text area's paper, below the original/download controls.
  if (!bodyBounds?.width || bodyBounds.top >= window.innerHeight || bodyBounds.bottom <= 0) return;
  const width = Math.min(sourceBounds.width, 330), height = Math.min(sourceBounds.height, 124);
  const left = sourceBounds.left + (sourceBounds.width - width) / 2;
  const top = Math.max(0, sourceBounds.top);
  const targetLeft = bodyBounds.left + Math.min(35, bodyBounds.width * .08);
  const targetTop = Math.max(0, bodyBounds.top) + 14;
  const dx = targetLeft - left, dy = targetTop - top;
  const scaleX = Math.min(bodyBounds.width - 30, 360) / width;
  const scaleY = Math.min(190, Math.max(height, bodyBounds.height * .45)) / height;
  // One blank decorative sheet. Never clone a row or any private mail text.
  const node = el("div", "message-flight");
  node.setAttribute("aria-hidden", "true");
  node.append(el("span", "message-flight-fold"), el("span", "message-flight-seal"));
  Object.assign(node.style, { left: `${left}px`, top: `${top}px`, width: `${width}px`, height: `${height}px`, transformOrigin: "0 0" });
  document.body.append(node);
  if (!node.animate) { node.remove(); return; }
  const animation = node.animate([
    { transform: "perspective(1000px) translate3d(0,0,0) rotateY(0deg) rotateZ(0deg) scale(1)", opacity: .72 },
    { transform: `perspective(1000px) translate3d(${dx * .14}px,${Math.max(dy * .18, -32) - 22}px,80px) rotateY(-24deg) rotateZ(-8deg) scale(.94)`, opacity: .86, offset: .22 },
    { transform: `perspective(1000px) translate3d(${dx * .78}px,${dy}px,30px) rotateY(16deg) rotateZ(4deg) scale(${scaleX * .92},${scaleY * .88})`, opacity: .34, offset: .65 },
    { transform: `perspective(1000px) translate3d(${dx}px,${dy}px,0) rotateY(0deg) rotateZ(0deg) scale(${scaleX},${scaleY})`, opacity: 0 }
  ], { duration: 720, easing: "cubic-bezier(.2,.68,.2,1)", fill: "forwards" });
  const flight = { node, animation };
  readerFlight = flight;
  const finish = () => {
    node.remove();
    if (readerFlight === flight) readerFlight = null;
  };
  animation.onfinish = finish;
  animation.oncancel = finish;
}
function openReaderPage(sourceBounds) {
  stopReaderOpening();
  const reader = $("#reader");
  if (!motionAllowed() || document.hidden || state.view !== "archive" || !reader?.animate || !reader.getClientRects().length) return;
  const bounds = reader.getBoundingClientRect();
  const mobile = window.matchMedia("(max-width: 580px)").matches;
  const sourceY = sourceBounds ? sourceBounds.top + sourceBounds.height / 2 : bounds.top + 90;
  const originY = Math.max(30, Math.min(bounds.height - 30, sourceY - bounds.top));
  const origin = mobile ? "50% 0px" : `0px ${originY}px`;
  flyMessagePaper(sourceBounds, reader);
  reader.classList.add("reader-opening");
  // Open the actual sheet around the selected row's height. No mail is cloned,
  // delayed, or made unfocusable; a new selection cancels this immediately.
  const opening = reader.animate([
    { transform: mobile ? "perspective(1200px) translateY(38px) rotateX(-24deg)" : "perspective(1400px) translateX(-28px) rotateY(-34deg)", transformOrigin: origin },
    { transform: mobile ? "perspective(1200px) translateY(-3px) rotateX(2deg)" : "perspective(1400px) translateX(3px) rotateY(3deg)", transformOrigin: origin, offset: .76 },
    { transform: "perspective(1400px) translate(0) rotateY(0) rotateX(0)", transformOrigin: origin }
  ], { duration: 700, easing: "cubic-bezier(.18,.75,.2,1)" });
  readerOpening = opening;
  opening.onfinish = () => {
    if (readerOpening === opening) {
      readerOpening = null;
      reader.classList.remove("reader-opening");
    }
  };
}
let tiltFrame = 0;
function resetPaperTilt() {
  cancelAnimationFrame(tiltFrame);
  for (const object of $$("[data-paper-surface]")) {
    object.style.setProperty("--tilt-x", "0deg"); object.style.setProperty("--tilt-y", "0deg");
    object.style.setProperty("--pointer-x", "50%"); object.style.setProperty("--pointer-y", "30%");
  }
}

function commandItems() {
  return [
    { title: "All mail", detail: "Return to the catalogue", icon: "archive", key: "G", run: () => setView("archive") },
    { title: "Connect mailbox", detail: "Archive your INBOX automatically", icon: "mail", disabled: !state.stats, run: () => openConnect() },
    { title: "Connected mailboxes", detail: "Manage automatic archiving", icon: "mail", run: () => setView("connections") },
    { title: "Search the collection", detail: state.stats?.messages ? "Words, people, dates, attachment names" : "Import mail to begin searching", icon: "search", key: "/", disabled: !state.stats?.messages, run: () => { setView("archive"); $("#search-input").focus(); } },
    { title: "Import mail", detail: "Add MBOX or EML files", icon: "import", key: "I", disabled: !state.stats, run: openImport },
    { title: "Import history", detail: "Review receipts and source files", icon: "book", key: "H", run: () => setView("imports") },
    { title: "Check archive integrity", detail: state.busy ? "Available after the current operation" : "Check message bytes and the search index", icon: "shield", disabled: !state.stats || state.busy, run: () => { setView("imports"); startVerify(); } },
    { title: "Back up archive", detail: "Download a consistent copy of the archive", icon: "download", disabled: !state.stats, run: () => $(".backup-link").click() },
    { title: "Reading room", detail: "Light, ink, typography, spacing, and motion", icon: "filter", key: ",", run: openPreferences },
    { title: "Getting started", detail: "Export formats, backups, and clear limits", icon: "info", run: () => setView("guide") }
  ];
}
let visibleCommands = [], commandIndex = 0;
function markCommand(index, { scroll = false } = {}) {
  commandIndex = Math.max(0, Math.min(index, visibleCommands.length - 1));
  $$(".command-row").forEach((row, i) => row.classList.toggle("active", i === commandIndex));
  if (scroll) $$(".command-row")[commandIndex]?.scrollIntoView({ block: "nearest" });
}
function executeCommand(index) {
  const command = visibleCommands[index];
  if (!command || command.disabled) return;
  $("#command-dialog").close();
  command.run();
}
function renderCommands() {
  const query = $("#command-search").value.trim().toLowerCase();
  visibleCommands = commandItems().filter((item) => `${item.title} ${item.detail} ${translate(item.title)} ${translate(item.detail)}`.toLowerCase().includes(query));
  const list = $("#command-results"); list.replaceChildren();
  visibleCommands.forEach((item, index) => {
    const row = action("", () => executeCommand(index), "command-row");
    row.disabled = !!item.disabled;
    const copy = el("span"); copy.append(el("strong", "", () => translate(item.title)), el("small", "", () => translate(item.detail)));
    row.append(icon(item.icon), copy);
    if (item.key) row.append(el("kbd", "", item.key));
    row.addEventListener("focus", () => markCommand(index));
    list.append(row);
  });
  if (!visibleCommands.length) list.append(el("p", "command-empty", () => translate("No command found. Try “import”, “backup”, or “reading”.")));
  markCommand(Math.max(0, visibleCommands.findIndex((item) => !item.disabled)));
}
function openCommands() {
  if ($("dialog[open]")) return;
  $("#command-search").value = "";
  renderCommands();
  $("#command-dialog").showModal();
  $("#command-search").focus();
}
function nextCommand(direction) {
  if (!visibleCommands.length) return;
  for (let step = 1; step <= visibleCommands.length; step++) {
    const index = (commandIndex + direction * step + visibleCommands.length) % visibleCommands.length;
    if (!visibleCommands[index].disabled) { markCommand(index, { scroll: true }); return; }
  }
}
function bindReadingRoom() {
  preferences = loadPreferences();
  applyPreferences();
  const marker = el("span", "nav-marker");
  marker.setAttribute("aria-hidden", "true");
  $(".nav-list").append(marker);
  positionNavMarker();
  // Font swaps can change navigation geometry without a viewport resize.
  document.fonts?.ready.then(positionNavMarker);
  // Observe post-layout dimensions too: mobile viewport changes may settle
  // after the window resize event, especially with device emulation/zoom.
  if (typeof ResizeObserver !== "undefined") {
    const navGeometry = new ResizeObserver(positionNavMarker);
    navGeometry.observe($(".nav-list"));
  }
  $("#open-preferences").addEventListener("click", openPreferences);
  $("#open-commands").addEventListener("click", openCommands);
  $("#footer-commands").addEventListener("click", openCommands);
  $("#preferences-form").addEventListener("submit", (event) => event.preventDefault());
  $("#preferences-form").addEventListener("change", (event) => {
    const input = event.target;
    if (!input.name) return;
    preferences = validatedPreferences({ ...preferences, [input.name]: input.type === "checkbox" ? input.checked : input.value });
    stopAllLights();
    applyPreferences({ save: true });
  });
  $("#reset-preferences").addEventListener("click", () => { preferences = { ...preferenceDefaults }; stopAllLights(); applyPreferences({ save: true }); toast("Reading room preferences reset."); });
  darkMedia.addEventListener("change", () => applyPreferences());
  reducedMedia.addEventListener("change", () => applyPreferences());
  window.addEventListener("storage", (event) => { if (event.key === preferenceKey || event.key === null) { preferences = loadPreferences(); stopAllLights(); applyPreferences(); } });
  document.addEventListener("visibilitychange", () => { document.documentElement.dataset.effectsPaused = String(document.hidden); if (document.hidden) { stopAllLights(); resetPaperTilt(); } });
  window.addEventListener("resize", () => { stopAllLights(); resetPaperTilt(); positionNavMarker(); });
  for (const dialog of $$("dialog")) {
    dialog.addEventListener("keydown", keepDialogFocus);
    dialog.addEventListener("close", () => {
      for (const canvas of dialog.querySelectorAll("canvas")) stopLight(canvas);
      resetPaperTilt();
    });
  }
  const visibility = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (!entry.isIntersecting) stopLight(entry.target);
  }));
  for (const canvas of $$("canvas")) visibility.observe(canvas);
  for (const object of $$("[data-paper-surface]")) {
    object.addEventListener("pointermove", (event) => {
      if (event.pointerType !== "mouse" || !motionAllowed() || document.hidden) return;
      const bounds = object.getBoundingClientRect();
      const x = (event.clientX - bounds.left) / bounds.width - .5;
      const y = (event.clientY - bounds.top) / bounds.height - .5;
      cancelAnimationFrame(tiltFrame);
      tiltFrame = requestAnimationFrame(() => {
        object.style.setProperty("--tilt-x", `${-y * 9}deg`); object.style.setProperty("--tilt-y", `${x * 13}deg`);
        object.style.setProperty("--pointer-x", `${(x + .5) * 100}%`); object.style.setProperty("--pointer-y", `${(y + .5) * 100}%`);
      });
    });
    object.addEventListener("pointerleave", resetPaperTilt);
    object.addEventListener("pointercancel", resetPaperTilt);
  }
  $("#command-search").addEventListener("input", renderCommands);
  $("#command-dialog").addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault(); nextCommand(event.key === "ArrowDown" ? 1 : -1);
      // Real buttons provide focus and accessible names; no synthetic listbox.
      $$(".command-row")[commandIndex]?.focus();
    } else if (event.key === "Enter" && event.target === $("#command-search")) { event.preventDefault(); executeCommand(commandIndex); }
  });
  $("#message-list").addEventListener("keydown", (event) => {
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key) || !state.searchReady) return;
    const rows = $$(".message-row");
    const current = rows.indexOf(document.activeElement);
    if (current < 0) return;
    event.preventDefault();
    const next = event.key === "Home" ? 0 : event.key === "End" ? rows.length - 1 : Math.max(0, Math.min(rows.length - 1, current + (event.key === "ArrowDown" ? 1 : -1)));
    if (next === current) return;
    rows[next]?.focus();
    if (rows[next]) readMessage(Number(rows[next].dataset.messageId), false);
  });
  window.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      if ($("#command-dialog").open) $("#command-dialog").close(); else openCommands();
      return;
    }
    if (!preferences.shortcuts || event.ctrlKey || event.metaKey || event.altKey || event.isComposing || $("dialog[open]") || document.activeElement.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) return;
    const shortcuts = { "?": openCommands, ",": openPreferences, "g": () => setView("archive"), "h": () => setView("imports"), "i": () => { if (state.stats) openImport(); } };
    const key = String(event.key || "");
    const shortcut = shortcuts[key] || shortcuts[key.toLowerCase()];
    if (shortcut) { event.preventDefault(); shortcut(); }
  });
}

initialize();
