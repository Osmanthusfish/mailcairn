"""Build the local Windows desktop folder; does not publish or create an installer."""
import argparse
from pathlib import Path
import subprocess
import sys
import os


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "work" / "mailcairn-desktop-build")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("Build Windows packages on Windows.")
    output = args.output.resolve()
    if output == ROOT or output.is_relative_to(ROOT):
        parser.error("Keep binaries and build state outside the source directory.")
    output.mkdir(parents=True, exist_ok=True)
    arguments = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                 "--onedir", "--windowed", "--name", "MailCairn",
                 "--distpath", str(output / "dist"), "--workpath", str(output / "work"),
                 "--specpath", str(output), "--paths", str(ROOT),
                 "--add-data", str(ROOT / "mailcairn" / "static") + ";mailcairn/static"]
    for name in ("LICENSE", "NOTICE", "COMMERCIAL.md"):
        arguments.extend(["--add-data", str(ROOT / name) + ";."])
    notices = ROOT / "licenses" / "desktop"
    if not (notices / "manifest.json").is_file():
        parser.error("Collect exact build-runtime licenses before packaging.")
    import json
    import hashlib
    from importlib.metadata import version
    manifest = json.loads((notices / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("errors") or manifest["versions"]["python"] != sys.version.split()[0]:
        parser.error("Runtime notice collection is incomplete or belongs to another Python version.")
    for package, key in (("pyinstaller", "pyinstaller"), ("pyinstaller-hooks-contrib", "pyinstaller_hooks_contrib")):
        if version(package) != manifest["versions"].get(key):
            parser.error("Build-tool version differs from the collected notices: " + package)
    for item in manifest["files"]:
        if hashlib.sha256((notices / item["file"]).read_bytes()).hexdigest() != item["sha256"]:
            parser.error("Runtime notice hash mismatch: " + item["file"])
    arguments.extend(["--add-data", str(notices) + ";licenses/desktop"])
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.is_file():
        arguments.extend(["--add-data", str(python_license) + ";licenses/Python"])
    arguments.append(str(ROOT / "desktop.py"))
    environment = os.environ.copy()
    windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    environment["PATH"] = os.pathsep.join(map(str, [Path(sys.base_prefix), Path(sys.base_prefix) / "DLLs", windows / "System32", windows]))
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    subprocess.run(arguments, cwd=ROOT, env=environment, check=True)
    print(output / "dist" / "MailCairn" / "MailCairn.exe")


if __name__ == "__main__":
    main()
