"""Launch the shipped CLI in real processes, including archive lock contention."""
from contextlib import redirect_stdout
from pathlib import Path
import io
import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

import app
from mailcairn.instance import publish_instance
from mailcairn.server import LocalServer
from mailcairn.store import Store


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mailcairn-cli-test-")
        self.addCleanup(self.temp.cleanup)
        self.temp_path = Path(self.temp.name).resolve()
        self.args = [sys.executable, "-u", str(ROOT / "app.py"),
                     "--data-dir", str(self.temp_path), "--port", "0", "--no-browser"]

    def launch(self, extra_args=()):
        process = subprocess.Popen([*self.args, *extra_args], cwd=ROOT, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True,
                                   encoding="utf-8", errors="replace")
        lines = queue.Queue()

        def read_output():
            for line in process.stdout:
                lines.put(line)
            lines.put(None)

        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()

        def stop():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
            reader.join(timeout=5)
            process.stdout.close()

        self.addCleanup(stop)
        deadline = time.monotonic() + 15
        output = []
        while time.monotonic() < deadline:
            try:
                line = lines.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if line is None:
                break
            output.append(line)
            if line.startswith("Open: "):
                return process, line[len("Open: "):].strip(), stop
        self.fail("CLI failed to announce a URL within 15 seconds: " + "".join(output))

    def test_cli_serves_loopback_page_with_session_url(self):
        process, launch_url, _ = self.launch()
        parsed = urlsplit(launch_url)
        self.assertEqual(parsed.scheme, "http")
        self.assertEqual(parsed.hostname, "127.0.0.1")
        self.assertGreater(parsed.port, 0)
        self.assertTrue(parsed.fragment.startswith("session="))
        self.assertGreater(len(parsed.fragment.removeprefix("session=")), 20)
        client = build_opener(ProxyHandler({}))
        with client.open(launch_url.split("#", 1)[0], timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"MailCairn", response.read())
        self.assertIsNone(process.poll())
        self.assertTrue((self.temp_path / "archive.sqlite3").is_file())

    def test_browser_failure_keeps_server_running_and_shutdown_cleans_instance(self):
        folder = self.temp_path
        metadata = folder / ".mailcairn-instance.json"
        for failure in (False, OSError("browser unavailable"), app.webbrowser.Error("no browser")):
            with self.subTest(failure=repr(failure)):
                served = []

                def finish_serving(server, **kwargs):
                    served.append(server)
                    record = json.loads(metadata.read_text(encoding="utf-8"))
                    self.assertEqual(record["port"], server.server_port)
                    self.assertEqual(record["token"], server.token)
                    self.assertGreaterEqual(server.socket.fileno(), 0)

                output = io.StringIO()
                browser_options = ({"side_effect": failure} if isinstance(failure, Exception)
                                   else {"return_value": failure})
                with patch.object(sys, "argv", [str(ROOT / "app.py"), "--data-dir",
                                               str(folder), "--port", "0"]), \
                        patch.object(app.webbrowser, "open", **browser_options) as browser, \
                        patch.object(LocalServer, "serve_forever", autospec=True,
                                     side_effect=finish_serving) as serve, \
                        redirect_stdout(output):
                    self.assertEqual(app.main(), 0)
                serve.assert_called_once()
                self.assertEqual(len(served), 1)
                server = served[0]
                launch = server.origin + "/#session=" + server.token
                browser.assert_called_once_with(launch)
                self.assertIn("Open: " + launch, output.getvalue())
                self.assertIn("Copy the complete Open link above", output.getvalue())
                self.assertFalse(metadata.exists())
                self.assertEqual(server.socket.fileno(), -1)
                with app.archive_lock(folder):
                    pass

    def test_second_process_is_rejected_and_lock_releases_on_exit(self):
        first, _, stop_first = self.launch()
        second = subprocess.run(self.args, cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=15)
        self.assertEqual(second.returncode, 1, second.stdout + second.stderr)
        self.assertIn("This archive is already open", second.stderr)
        self.assertNotIn("Traceback", second.stderr)
        self.assertIsNone(first.poll())
        stop_first()
        # The stale lock file must not prevent reopening after abrupt termination.
        reopened, launch_url, _ = self.launch()
        self.assertIsNone(reopened.poll())
        self.assertTrue(launch_url.startswith("http://127.0.0.1:"))

    def test_open_existing_reuses_running_process_and_session(self):
        first, launch_url, _ = self.launch()
        second = subprocess.run([*self.args, "--open-existing"], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=15)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertIn("Open: " + launch_url, second.stdout)
        self.assertEqual(second.stderr, "")
        self.assertIsNone(first.poll())
        client = build_opener(ProxyHandler({}))
        with client.open(launch_url.split("#", 1)[0], timeout=5) as response:
            self.assertEqual(response.status, 200)

    def test_open_existing_never_bypasses_restore_lock(self):
        first, launch_url, _ = self.launch()
        second = subprocess.run([*self.args, "--open-existing", "--restore-backup",
                                 str(self.temp_path / "missing-backup.zip")],
                                cwd=ROOT, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=15)
        self.assertEqual(second.returncode, 1, second.stdout + second.stderr)
        self.assertIn("This archive is already open", second.stderr)
        self.assertNotIn(launch_url, second.stdout + second.stderr)
        self.assertIsNone(first.poll())

    def test_open_existing_replaces_stale_metadata_after_lock_release(self):
        first, old_url, stop_first = self.launch()
        stop_first()
        self.assertIsNotNone(first.poll())
        reopened, new_url, _ = self.launch(["--open-existing"])
        self.assertIsNone(reopened.poll())
        self.assertNotEqual(new_url, old_url)
        metadata = json.loads((self.temp_path / ".mailcairn-instance.json").read_text())
        self.assertEqual(metadata["port"], urlsplit(new_url).port)
        self.assertEqual(metadata["token"], urlsplit(new_url).fragment.removeprefix("session="))

    def test_invalid_instance_metadata_does_not_open_or_print_untrusted_target(self):
        first, _, _ = self.launch()
        target = "https://untrusted.invalid/private"
        token = "untrusted-token-do-not-print"
        (self.temp_path / ".mailcairn-instance.json").write_text(
            json.dumps({"port": target, "token": token, "url": target}), encoding="utf-8")
        second = subprocess.run([*self.args, "--open-existing"], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=15)
        output = second.stdout + second.stderr
        self.assertEqual(second.returncode, 1, output)
        self.assertIn("This archive is already open", output)
        self.assertNotIn(target, output)
        self.assertNotIn(token, output)
        self.assertNotIn("Traceback", output)
        self.assertIsNone(first.poll())

    def test_open_existing_checks_archive_lock_before_reusing_metadata(self):
        # Even a reachable authenticated instance record is only a hint. A new
        # process that can acquire the archive lock must create its own session.
        folder = self.temp_path
        server = LocalServer(("127.0.0.1", 0), Store(folder / "archive.sqlite3"))
        thread = threading.Thread(target=server.serve_forever,
                                  kwargs={"poll_interval": 0.02}, daemon=True)
        thread.start()
        try:
            publish_instance(folder, server)
            process, launch_url, stop = self.launch(["--open-existing"])
            self.assertIsNone(process.poll())
            self.assertNotEqual(launch_url, server.origin + "/#session=" + server.token)
            stop()
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


if __name__ == "__main__":
    unittest.main()
