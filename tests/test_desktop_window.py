"""Real Tk widgets/workers with synthetic archives and substituted file pickers.

This checks the desktop controller boundary, not native file-dialog automation.
"""
from pathlib import Path
import gc
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from desktop import DesktopService, DesktopWindow
from mailcairn.store import Store


class DesktopWindowTests(unittest.TestCase):
    def setUp(self):
        try:
            import tkinter as tk
            self.root = tk.Tk()
        except Exception as error:
            self.skipTest("Tk desktop unavailable: " + type(error).__name__)
        self.root.withdraw()
        self.temporary = tempfile.TemporaryDirectory(prefix="mailcairn-window-test-")
        self.base = Path(self.temporary.name).resolve()
        for name, target, options in (
            ('errors', 'tkinter.messagebox.showerror', {}),
            ('info', 'tkinter.messagebox.showinfo', {}),
            ('browser', 'desktop.webbrowser.open', {'return_value': True}),
        ):
            patcher = patch(target, **options)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        self.existing_threads = set(threading.enumerate())
        self.window = DesktopWindow(self.root, DesktopService(self.base / "current"), "zh-CN", auto_open=False)
        self.wait_ready()

    def tearDown(self):
        if hasattr(self, "window"):
            self.window.service.stop(cancel=True)
            for worker in threading.enumerate():
                if worker not in self.existing_threads and worker.name.startswith('mailcairn-desktop-'):
                    worker.join(timeout=5)
                    self.assertFalse(worker.is_alive(), 'Desktop test worker did not stop')
        if hasattr(self, "root"):
            try:
                for callback in self.root.tk.call("after", "info"):
                    self.root.after_cancel(callback)
                self.root.destroy()
            except Exception:
                pass
        if hasattr(self, "temporary"):
            self.temporary.cleanup()
        # Error-dialog mocks retain their parent widgets. Release every test
        # reference and collect Tk cycles on the creating thread, before another
        # test's worker can trigger garbage collection of a Tcl interpreter.
        for name in ('errors', 'info', 'browser'):
            if hasattr(self, name):
                getattr(self, name).reset_mock()
        self.window = self.root = None
        gc.collect()

    def wait_ready(self):
        deadline = time.monotonic() + 10
        while self.window.state in ("starting", "switching") and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.01)
        self.assertEqual(self.window.state, "ready")

    def backup(self):
        seed = Store(self.base / "seed" / "archive.sqlite3")
        seed.import_file(Path(__file__).parent / "fixtures" / "sample.eml")
        target = self.base / "backup.sqlite3"
        seed.backup(target)
        return target

    def test_restore_button_switches_to_copy_and_preserves_original(self):
        backup = self.backup()
        original = self.window.service
        source_bytes = backup.read_bytes()
        with patch("tkinter.filedialog.askopenfilename", return_value=str(backup)), patch("tkinter.filedialog.askdirectory", return_value=str(self.base)):
            self.window.restore_button.invoke()
        self.assertEqual(self.window.state, "switching")
        self.assertTrue(self.window.restore_button.instate(["disabled"]))
        self.assertTrue(self.window.choose_archive_button.instate(["disabled"]))
        self.wait_ready()
        self.assertIsNot(self.window.service, original)
        self.assertEqual(self.window.service.server.store.stats()["messages"], 1)
        self.assertEqual(Store(original.folder / "archive.sqlite3").stats()["messages"], 0)
        self.assertEqual(backup.read_bytes(), source_bytes)
        self.assertEqual(self.window.path.get(), str(self.window.service.folder))
        self.assertFalse(self.window.open_button.instate(["disabled"]))
        self.errors.assert_not_called()

    def test_cancelled_file_selection_preserves_service_without_parent_picker(self):
        original = self.window.service
        with patch("tkinter.filedialog.askopenfilename", return_value=""), patch("tkinter.filedialog.askdirectory") as directory:
            self.window.restore_button.invoke()
        directory.assert_not_called()
        self.assertIs(self.window.service, original)
        self.assertEqual(self.window.state, "ready")

    def test_invalid_backup_keeps_live_service_and_restores_buttons(self):
        backup = self.base / "corrupt.sqlite3"
        backup.write_bytes(b"not a database")
        original = self.window.service
        with patch("tkinter.filedialog.askopenfilename", return_value=str(backup)), patch("tkinter.filedialog.askdirectory", return_value=str(self.base)):
            self.window.restore_button.invoke()
        self.wait_ready()
        self.assertIs(self.window.service, original)
        self.assertEqual(self.window.path.get(), str(original.folder))
        self.assertEqual(original.server.store.stats()["messages"], 0)
        self.assertFalse(self.window.restore_button.instate(["disabled"]))
        self.assertFalse(self.window.open_button.instate(["disabled"]))
        self.errors.assert_called_once()
        self.assertFalse(list(self.base.glob("MailCairn-restored-*")))

    def test_busy_archive_blocks_restore_before_file_picker(self):
        self.window.service.server.operation.acquire()
        try:
            with patch("tkinter.filedialog.askopenfilename") as picker:
                self.window.restore_button.invoke()
            picker.assert_not_called()
            self.info.assert_called_once()
            self.assertEqual(self.window.state, "ready")
        finally:
            self.window.service.server.operation.release()
