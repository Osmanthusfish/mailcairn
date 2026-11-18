/* Independent recovery for failures before the main interface can start. */
(() => {
  "use strict";
  let settled = false;
  let pending = null;
  const disabled = new Map();
  const language = () => {
    try {
      const saved = localStorage.getItem("mailcairn.language.v1");
      if (saved === "en" || saved === "zh-CN") return saved;
    } catch { /* Recovery must also work when browser storage is blocked. */ }
    return String(navigator.language || "en").toLowerCase().startsWith("zh") ? "zh-CN" : "en";
  };
  function show(slow = false) {
    if (settled) return;
    if (!slow) clearTimeout(timer);
    pending = slow && pending !== "failed" ? "slow" : "failed";
    const panel = document.getElementById("startup-recovery");
    if (!panel) return;
    slow = pending === "slow";
    const chinese = language() === "zh-CN";
    panel.lang = chinese ? "zh-CN" : "en";
    document.getElementById("startup-title").textContent = chinese
      ? (slow ? "档案还在打开中。" : "MailCairn 未能加载。")
      : (slow ? "Your archive is still opening." : "MailCairn couldn’t load.");
    document.getElementById("startup-message").textContent = chinese
      ? "可以重新加载此页，或在 MailCairn 窗口中选择“打开档案”。"
      : "Reload this page, or choose “Open archive” in the MailCairn window.";
    document.getElementById("startup-reload").textContent = chinese ? "重新加载" : "Reload page";
    document.getElementById("loading-screen").hidden = true;
    for (const button of document.querySelectorAll("[data-open-import], [data-open-connect]")) {
      if (!disabled.has(button)) disabled.set(button, button.disabled);
      button.disabled = true;
    }
    panel.hidden = false;
  }
  function failed(event) {
    const target = event.target;
    if ((target === window && /\/(?:app|i18n)\.js(?:[?#]|$)/.test(event.filename || "")) ||
        (target?.tagName === "SCRIPT" && /\/(?:app|i18n)\.js(?:[?#]|$)/.test(target.src))) show();
  }
  const timer = setTimeout(() => show(true), 12000);
  window.addEventListener("error", failed, true);
  function bindRecovery() {
    document.getElementById("startup-reload").addEventListener("click", () => location.reload());
    if (pending) show(pending === "slow");
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bindRecovery, { once: true });
  else bindRecovery();
  window.MailCairnStartup = Object.freeze({
    fail() { show(); },
    ready() {
      if (settled) return;
      settled = true;
      pending = null;
      clearTimeout(timer);
      window.removeEventListener("error", failed, true);
      const panel = document.getElementById("startup-recovery");
      const restoreFocus = !panel.hidden && panel.contains(document.activeElement);
      panel.hidden = true;
      for (const [button, wasDisabled] of disabled) button.disabled = wasDisabled;
      disabled.clear();
      if (restoreFocus) document.getElementById("main-content").focus();
    },
  });
})();
