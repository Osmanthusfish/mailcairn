"""A small, console-free desktop entry for the local browser application.

The controller owns the archive lock only when it starts the service itself.
Tkinter is imported by the window entry point, keeping lifecycle tests headless.
"""
from __future__ import annotations

import argparse
import errno
import json
import locale
import os
from pathlib import Path
import queue
import sys
import tempfile
import threading
import time
import webbrowser

from app import ArchiveAlreadyOpen, archive_lock
from mailcairn.instance import clear_instance, existing_launch, publish_instance
from mailcairn.server import LocalServer, MAX_REQUEST_THREADS
from mailcairn.store import Store, restore_backup

DESKTOP_SETTINGS = ".mailcairn-desktop.json"


def preferred_port(folder):
    """Read a nonsecret port preference while the caller holds the archive lock."""
    path = Path(folder) / DESKTOP_SETTINGS
    if path.is_symlink():
        return 8765
    try:
        with path.open("rb") as stream:
            data = stream.read(4097)
        if len(data) > 4096:
            return 8765
        value = json.loads(data)
        port = value.get("port") if isinstance(value, dict) else None
        return port if type(port) is int and 1 <= port <= 65535 else 8765
    except (OSError, ValueError, UnicodeError):
        return 8765


def remember_port(folder, port):
    """Atomically retain the browser origin, without any session token."""
    descriptor, temporary = tempfile.mkstemp(prefix=".mailcairn-desktop-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"port": port}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, Path(folder) / DESKTOP_SETTINGS)
    finally:
        Path(temporary).unlink(missing_ok=True)


def unavailable_port_error(error):
    # Windows can reserve a previously usable port without a live listener.
    # Ask the OS for one allowed loopback port; if that also fails, propagate
    # the error. This never changes exclusions, firewall rules or listeners.
    return error.errno == errno.EADDRINUSE or getattr(error, "winerror", None) in (10048, 10013)


def default_data_dir():
    if getattr(sys, "frozen", False):
        # Never put persistent mail inside a bundle or its extraction directory.
        base = os.environ.get("LOCALAPPDATA")
        return (Path(base) if base else Path.home() / "AppData" / "Local") / "MailCairn"
    return Path(__file__).resolve().parent / "data"


class DesktopService:
    """Own a service or reuse a verified peer; never stop somebody else's server."""

    def __init__(self, folder, restore_from=None, require_existing=False):
        self.folder = Path(folder).resolve()
        self.server = None
        self.thread = None
        self.launch = None
        self.reused = False
        self._lock = None
        self._started = False
        self.restore_from = Path(restore_from).resolve() if restore_from else None
        self.require_existing = require_existing

    def start(self):
        if self._started:
            raise RuntimeError("Desktop service has already started.")
        self._started = True
        lock = archive_lock(self.folder)
        try:
            lock.__enter__()
        except ArchiveAlreadyOpen:
            if self.restore_from is not None:
                raise
            for attempt in range(4):
                self.launch = existing_launch(self.folder)
                if self.launch:
                    self.reused = True
                    return self.launch
                if attempt < 3:
                    time.sleep(.2)
            raise ArchiveAlreadyOpen(
                "This archive is in use, but its running instance could not be verified. "
                "Use its existing browser window, or close the original MailCairn window and retry."
            ) from None
        self._lock = lock
        try:
            archive = self.folder / "archive.sqlite3"
            if self.require_existing and not archive.is_file():
                raise ValueError("Choose a folder containing archive.sqlite3. / 请选择包含 archive.sqlite3 的文件夹。")
            if self.restore_from is not None:
                restore_backup(self.restore_from, archive)
            store = Store(archive)
            store.recover_interrupted()
            for abandoned in self.folder.glob(".upload-*"):
                if abandoned.is_file():
                    abandoned.unlink()
            port = preferred_port(self.folder)
            try:
                self.server = LocalServer(("127.0.0.1", port), store)
            except OSError as exc:
                # A busy or Windows-reserved port cannot be used for this
                # archive. Only discovery after lock contention permits reuse;
                # otherwise let the OS select a port for our own server.
                if not unavailable_port_error(exc):
                    raise
                self.server = LocalServer(("127.0.0.1", 0), store)
            publish_instance(self.folder, self.server)
            self.launch = self.server.origin + "/#session=" + self.server.token
            self.thread = threading.Thread(target=self.server.serve_forever,
                                           kwargs={"poll_interval": .1},
                                           name="mailcairn-desktop-server", daemon=True)
            self.thread.start()
            remember_port(self.folder, self.server.server_port)
            return self.launch
        except BaseException:
            if self.server is not None:
                if self.thread is not None and self.thread.is_alive():
                    self.server.shutdown()
                    self.thread.join()
                self.server.server_close()
                clear_instance(self.folder, self.server)
            self._release_lock()
            raise

    def busy(self):
        return bool(self.server and self.server.operation.locked())

    def _cancel_jobs(self):
        with self.server.job_lock:
            for job in self.server.jobs.values():
                if job["status"] == "running":
                    job["cancel"].set()

    def stop(self, cancel=False):
        if self.reused or self.server is None or self._lock is None:
            return
        server = self.server
        # First stop accepting requests. Then drain already accepted requests,
        # including uploads and backup downloads, before releasing the OS lock.
        server.shutdown()
        self.thread.join()
        for _ in range(MAX_REQUEST_THREADS):
            while not server.request_slots.acquire(timeout=.1):
                if cancel:
                    self._cancel_jobs()
        # An accepted upload can create a job during the drain. Keep forwarding
        # cancellation until its final database transaction and cleanup finish.
        while not server.operation.acquire(timeout=.1):
            if cancel:
                self._cancel_jobs()
        try:
            server.server_close()
            clear_instance(self.folder, server)
        finally:
            server.operation.release()
            for _ in range(MAX_REQUEST_THREADS):
                server.request_slots.release()
            self._release_lock()

    def _release_lock(self):
        if self._lock is not None:
            self._lock.__exit__(None, None, None)
            self._lock = None


def switch_archive(current, folder, restore_from=None):
    """Prepare the next archive before retiring the owned service, without data loss."""
    if current.busy():
        raise ValueError("Finish the current import, sync or verification before switching archives. / 请先完成当前导入、同步或核验，再切换档案。")
    folder = Path(folder).resolve()
    if restore_from is None and folder == current.folder and current.launch:
        return current
    candidate = DesktopService(folder, restore_from=restore_from, require_existing=restore_from is None)
    candidate.start()
    try:
        current.stop()  # Reused peers are deliberately left untouched.
    except BaseException:
        candidate.stop()
        raise
    return candidate


def restore_archive(current, backup, parent):
    """Create a distinct destination; existing archives are never overwritten."""
    if current.busy():
        raise ValueError("Finish the current import, sync or verification before restoring. / 请先完成当前导入、同步或核验，再恢复备份。")
    parent = Path(parent).resolve()
    folder = Path(tempfile.mkdtemp(prefix="MailCairn-restored-" + time.strftime("%Y%m%d-") , dir=parent))
    try:
        return switch_archive(current, folder, restore_from=backup)
    except BaseException:
        # Remove only an empty destination created by this call. If restoration
        # succeeded but startup failed, retain the restored archive for recovery.
        if not (folder / "archive.sqlite3").exists():
            try:
                (folder / ".mailcairn.lock").unlink(missing_ok=True)
                folder.rmdir()
            except OSError:
                pass
        raise


COPY = {
    "en": {
        "subtitle": "Your mail, on this computer.",
        "starting": "Opening your archive…",
        "ready": "Your archive is ready.",
        "reused": "Your archive is already running in another MailCairn window.",
        "hint": "Keep this window open to use your archive and sync connected mailboxes.",
        "reused_hint": "Closing this window leaves the existing archive running.",
        "folder": "Archive folder", "open": "Open archive", "copy": "Copy launch link",
        "copied": "Launch link copied. Paste it into your browser.",
        "close": "Close MailCairn", "language": "Language / 语言",
        "stopping": "Finishing current work and closing safely…",
        "waiting": "Waiting for current work to finish. Keep this window open.",
        "busy_title": "Work is still running",
        "busy": "An import, sync, upload or verification is still running.\n\nYes: wait for current work, then close.\nNo: stop work safely, then close.\nCancel: keep MailCairn open.\n\nA file already copying must finish or time out before closing. Closing stops automatic sync.",
        "error_title": "Could not open MailCairn", "failed": "Archive could not open.",
        "browser_error": "The browser could not open. Use Copy launch link and paste it into your browser.",
        "stop_error": "Could not finish closing. Your archive remains locked. Retry closing this window.",
        "choose_archive": "Open archive folder…", "restore": "Restore backup…",
        "choose_archive_title": "Choose a folder containing archive.sqlite3",
        "choose_backup_title": "Choose a MailCairn backup",
        "restore_parent_title": "Choose where to create a NEW restored archive folder",
        "switching": "Opening the selected archive. Please wait…",
        "restoring": "Verifying and restoring into a new folder. Please wait…",
        "switch_error": "Could not switch archives",
        "switch_busy": "Finish or stop the current import, sync or verification in the browser before switching archives.",
        "archive_help": "To reopen a restored archive later, choose the folder shown here. Your original archive stays in its current folder.",
    },
    "zh-CN": {
        "subtitle": "邮件留在自己的电脑上。",
        "starting": "正在打开档案…", "ready": "档案已就绪。",
        "reused": "档案已在另一个 MailCairn 窗口中运行。",
        "hint": "使用档案及自动同步邮箱时，请保持此窗口打开。",
        "reused_hint": "关闭此窗口不会停止已有档案服务。",
        "folder": "档案文件夹", "open": "打开档案", "copy": "复制打开链接",
        "copied": "已复制打开链接，可粘贴到浏览器。",
        "close": "关闭 MailCairn", "language": "语言 / Language",
        "stopping": "正在完成当前工作并安全关闭…",
        "waiting": "等待当前工作完成，请保持此窗口打开。",
        "busy_title": "仍有任务正在运行",
        "busy": "导入、同步、文件复制或完整性核验仍在进行。\n\n是：等待当前工作后关闭。\n否：安全停止工作，然后关闭。\n取消：保持 MailCairn 打开。\n\n已经开始的文件复制需要完成或超时后才能关闭。关闭后将停止自动同步。",
        "error_title": "无法打开 MailCairn", "failed": "未能打开档案。",
        "browser_error": "无法自动打开浏览器。请复制打开链接并粘贴到浏览器。",
        "stop_error": "未能完成关闭，档案仍保持锁定。请再次尝试关闭此窗口。",
        "choose_archive": "打开档案文件夹…", "restore": "恢复备份…",
        "choose_archive_title": "选择包含 archive.sqlite3 的档案文件夹",
        "choose_backup_title": "选择 MailCairn 备份文件",
        "restore_parent_title": "选择存放位置，将在其中新建恢复档案文件夹",
        "switching": "正在打开选中的档案，请稍候…",
        "restoring": "正在验证备份并恢复到新文件夹，请稍候…",
        "switch_error": "无法切换档案",
        "switch_busy": "请先在浏览器中完成或停止当前导入、同步或核验，再切换档案。",
        "archive_help": "以后重新打开恢复的档案时，选择这里显示的文件夹。原档案仍保留在原文件夹中。",
    },
}


class DesktopWindow:
    def __init__(self, root, service, language, auto_open=True):
        import tkinter as tk
        from tkinter import ttk
        self.root, self.service = root, service
        self.language = language
        self.auto_open = auto_open
        self.events = queue.Queue()
        self.state = "starting"
        self.status_key = "starting"
        self.close_after_start = False
        root.title("MailCairn")
        root.geometry("620x510")
        root.minsize(560, 490)
        root.configure(background="#f5f2e9")
        root.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style(root)
        style.configure("Desk.TFrame", background="#f5f2e9")
        style.configure("Desk.TLabel", background="#f5f2e9", foreground="#344b3c", font=("Segoe UI", 11))
        style.configure("Title.Desk.TLabel", font=("Georgia", 28))
        style.configure("TButton", font=("Segoe UI", 10), padding=(14, 9))
        frame = ttk.Frame(root, style="Desk.TFrame", padding=28)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        heading = ttk.Frame(frame, style="Desk.TFrame")
        heading.grid(row=0, column=0, sticky="ew")
        ttk.Label(heading, text="MailCairn", style="Title.Desk.TLabel").pack(side="left")
        self.locale = ttk.Combobox(heading, values=("English", "简体中文"), state="readonly", width=10)
        self.locale.set("简体中文" if language == "zh-CN" else "English")
        self.locale.pack(side="right", pady=6)
        self.locale.bind("<<ComboboxSelected>>", self.change_language)
        self.subtitle = ttk.Label(frame, style="Desk.TLabel")
        self.subtitle.grid(row=1, column=0, sticky="w", pady=(6, 24))
        self.status = ttk.Label(frame, style="Desk.TLabel", wraplength=510)
        self.status.grid(row=2, column=0, sticky="ew")
        self.hint = ttk.Label(frame, style="Desk.TLabel", wraplength=510)
        self.hint.grid(row=3, column=0, sticky="ew", pady=(8, 18))
        self.folder_label = ttk.Label(frame, style="Desk.TLabel")
        self.folder_label.grid(row=4, column=0, sticky="w")
        self.path = tk.StringVar(value=str(service.folder))
        ttk.Entry(frame, textvariable=self.path, state="readonly").grid(row=5, column=0, sticky="ew", pady=(5, 22))
        buttons = ttk.Frame(frame, style="Desk.TFrame")
        buttons.grid(row=6, column=0, sticky="ew")
        self.open_button = ttk.Button(buttons, command=self.open_browser, state="disabled")
        self.open_button.pack(side="left")
        self.copy_button = ttk.Button(buttons, command=self.copy_link, state="disabled")
        self.copy_button.pack(side="left", padx=8)
        self.close_button = ttk.Button(buttons, command=self.close)
        self.close_button.pack(side="right")
        archive_buttons = ttk.Frame(frame, style="Desk.TFrame")
        archive_buttons.grid(row=7, column=0, sticky="ew", pady=(18, 8))
        self.choose_archive_button = ttk.Button(archive_buttons, command=self.choose_archive, state="disabled")
        self.choose_archive_button.pack(side="left")
        self.restore_button = ttk.Button(archive_buttons, command=self.restore, state="disabled")
        self.restore_button.pack(side="left", padx=8)
        self.archive_help = ttk.Label(frame, style="Desk.TLabel", wraplength=550)
        self.archive_help.grid(row=8, column=0, sticky="ew")
        root.bind("<Configure>", self.resize)
        self.render()
        self._work("started", service.start)
        root.after(100, self.poll)

    def text(self, key):
        return COPY[self.language][key]

    def render(self):
        for widget, key in ((self.subtitle, "subtitle"), (self.status, self.status_key),
                            (self.hint, "reused_hint" if self.service.reused else "hint"),
                            (self.folder_label, "folder"), (self.open_button, "open"),
                            (self.copy_button, "copy"), (self.close_button, "close"),
                            (self.choose_archive_button, "choose_archive"), (self.restore_button, "restore"),
                            (self.archive_help, "archive_help")):
            widget.configure(text=self.text(key))

    def resize(self, event):
        if event.widget is self.root:
            width = max(360, event.width - 60)
            self.hint.configure(wraplength=width)
            self.status.configure(wraplength=width)
            self.archive_help.configure(wraplength=width)

    def change_language(self, _event=None):
        self.language = "zh-CN" if self.locale.get() == "简体中文" else "en"
        self.render()

    def _work(self, name, operation):
        def run():
            try:
                self.events.put((name, operation(), None))
            except Exception as exc:
                self.events.put((name, None, exc))
        threading.Thread(target=run, name="mailcairn-desktop-" + name, daemon=False).start()

    def poll(self):
        from tkinter import messagebox
        try:
            while True:
                name, _result, error = self.events.get_nowait()
                if name == "started":
                    self.choose_archive_button.configure(state="normal")
                    self.restore_button.configure(state="normal")
                    if error:
                        self.state, self.status_key = "failed", "failed"
                        self.render()
                        messagebox.showerror(self.text("error_title"), str(error), parent=self.root)
                    else:
                        self.state = "ready"
                        self.status_key = "reused" if self.service.reused else "ready"
                        self.open_button.configure(state="normal")
                        self.copy_button.configure(state="normal")
                        self.render()
                        if self.auto_open and not self.close_after_start:
                            self.open_browser()
                    if self.close_after_start:
                        self.close()
                elif name == "switched":
                    self.choose_archive_button.configure(state="normal")
                    self.restore_button.configure(state="normal")
                    self.close_button.configure(state="normal")
                    if error:
                        self.state = self.switch_previous_state
                        self.status_key = "failed" if self.state == "failed" else ("reused" if self.service.reused else "ready")
                        messagebox.showerror(self.text("switch_error"), str(error), parent=self.root)
                    else:
                        self.service = _result
                        self.path.set(str(self.service.folder))
                        self.state = "ready"
                        self.status_key = "reused" if self.service.reused else "ready"
                    self.open_button.configure(state="normal" if self.state == "ready" else "disabled")
                    self.copy_button.configure(state="normal" if self.state == "ready" else "disabled")
                    self.render()
                    if self.close_after_start:
                        self.close()
                    elif not error:
                        self.open_browser()
                elif name == "stopped":
                    if not error:
                        self.root.destroy()
                        return
                    self.state, self.status_key = "ready", "stop_error"
                    self.close_button.configure(state="normal")
                    self.render()
                elif name == "browser" and error:
                    self.status_key = "browser_error"
                    self.render()
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def open_browser(self):
        def launch():
            if not webbrowser.open(self.service.launch):
                raise OSError("Browser could not open")
        self._work("browser", launch)

    def copy_link(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.service.launch)
        self.status_key = "copied"
        self.render()

    def can_switch(self):
        from tkinter import messagebox
        if self.state not in ("ready", "failed"):
            return False
        if self.service.busy():
            messagebox.showinfo(self.text("busy_title"), self.text("switch_busy"), parent=self.root)
            return False
        return True

    def choose_archive(self):
        from tkinter import filedialog
        if not self.can_switch():
            return
        folder = filedialog.askdirectory(title=self.text("choose_archive_title"), mustexist=True, parent=self.root)
        if folder:
            self.begin_switch(lambda: switch_archive(self.service, folder), "switching")

    def restore(self):
        from tkinter import filedialog
        if not self.can_switch():
            return
        backup = filedialog.askopenfilename(title=self.text("choose_backup_title"),
                                            filetypes=(("MailCairn / SQLite", "*.sqlite3 *.sqlite *.db"), ("All files / 所有文件", "*.*")),
                                            parent=self.root)
        if not backup:
            return
        parent = filedialog.askdirectory(title=self.text("restore_parent_title"), mustexist=True, parent=self.root)
        if parent:
            self.begin_switch(lambda: restore_archive(self.service, backup, parent), "restoring")

    def begin_switch(self, operation, status):
        if not self.can_switch():
            return
        self.switch_previous_state = self.state
        self.state, self.status_key = "switching", status
        for button in (self.open_button, self.copy_button, self.close_button, self.choose_archive_button, self.restore_button):
            button.configure(state="disabled")
        self.render()
        self._work("switched", operation)

    def close(self):
        from tkinter import messagebox
        if self.state in ("starting", "switching"):
            self.close_after_start = True
            return
        if self.state == "stopping":
            return
        if self.state == "failed" or self.service.reused:
            self.root.destroy()
            return
        cancel = False
        if self.service.busy():
            answer = messagebox.askyesnocancel(self.text("busy_title"), self.text("busy"), parent=self.root)
            if answer is None:
                return
            cancel = not answer
        self.state = "stopping"
        self.status_key = "stopping" if cancel else "waiting"
        for button in (self.open_button, self.copy_button, self.close_button, self.choose_archive_button, self.restore_button):
            button.configure(state="disabled")
        self.render()
        self._work("stopped", lambda: self.service.stop(cancel=cancel))


def main(argv=None):
    parser = argparse.ArgumentParser(description="MailCairn desktop entry")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--language", choices=COPY)
    parser.add_argument("--no-browser", action="store_true", help="Open the desktop window without automatically opening a browser")
    args = parser.parse_args(argv)
    import tkinter as tk
    language = args.language
    if not language:
        language = "zh-CN" if (locale.getlocale()[0] or "").lower().startswith("zh") else "en"
    root = tk.Tk()
    DesktopWindow(root, DesktopService(args.data_dir or default_data_dir()), language, auto_open=not args.no_browser)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
