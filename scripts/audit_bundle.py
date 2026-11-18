"""Reconcile an existing PyInstaller one-directory bundle; never rebuild or copy files.

Run with the selected build Python (which supplies PyInstaller):
  python scripts/audit_bundle.py --project . --build ../work/desktop-build
  Add --write-evidence to replace docs/desktop-build-evidence.json ONLY on PASS.
"""
import argparse
import ast
import datetime
import hashlib
import json
import marshal
import sys
import types
import zipfile
import re
from pathlib import Path

from PyInstaller.archive.readers import CArchiveReader


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--python-dir", type=Path, default=Path(sys.base_prefix))
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    root, build, runtime = args.project.resolve(), args.build.resolve(), args.python_dir.resolve()
    version_tree = ast.parse((root / "mailcairn/__init__.py").read_text(encoding="utf-8"))
    version = next(ast.literal_eval(node.value) for node in version_tree.body
                   if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets))
    if not isinstance(version, str) or not re.fullmatch(r"[0-9A-Za-z.-]+", version):
        parser.error("Invalid application version")
    dist = build / "dist/MailCairn"
    internal = dist / "_internal"
    exe = dist / "MailCairn.exe"
    previous_path = root / "docs/desktop-build-evidence.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {}
    analysis = ast.literal_eval((build / "work/MailCairn/Analysis-00.toc").read_text(encoding="utf-8"))
    collect = ast.literal_eval((build / "work/MailCairn/COLLECT-00.toc").read_text(encoding="utf-8"))[0]
    failures = []

    def require(condition, message):
        if not condition:
            failures.append(message)

    native = []
    entries = [entry for entry in collect if entry[2] in ("BINARY", "EXTENSION")]
    for name, source_name, kind in entries:
        source, target = Path(source_name), internal / name
        origin = "selected-python-runtime" if source.resolve().is_relative_to(runtime) else "EXTERNAL"
        matches = target.is_file() and source.is_file() and sha(target) == sha(source)
        native.append({"name": name, "source": "build-runtime/" + source.relative_to(runtime).as_posix() if origin != "EXTERNAL" else "EXTERNAL", "origin": origin,
                       "sha256": sha(target) if target.is_file() else None,
                       "source_sha256": sha(source) if source.is_file() else None,
                       "matches_source": matches})
        require(origin == "selected-python-runtime", f"Native input outside selected runtime: {source}")
        require(matches, f"Native file mismatch/missing: {name}")
    actual_native = {str(path.relative_to(internal)) for path in internal.rglob("*") if path.suffix.lower() in (".dll", ".pyd")}
    require(actual_native == {row[0] for row in entries}, "Actual DLL/pyd set differs from COLLECT TOC")
    unexpected = [row for row in analysis[14] if "site-packages" in row[1].lower()]
    require(not unexpected, f"Unexpected third-party Python application modules: {unexpected}")
    hooks = [row for row in analysis[13] if row[0].startswith("pyi_rth_")]

    archive = CArchiveReader(str(exe))
    pyz = archive.open_embedded_archive("PYZ.pyz")
    code_count = 0
    def check_filenames(code):
        nonlocal code_count
        if not isinstance(code, types.CodeType):
            return
        code_count += 1
        name = code.co_filename
        require(not (re.match(r"^[A-Za-z]:[\\/]", name) or name.startswith(("/", "\\\\"))),
                "Absolute filename embedded in Python code")
        for value in code.co_consts:
            check_filenames(value)
    for name, entry in pyz.toc.items():
        if entry[0] in (0, 1):
            check_filenames(pyz.extract(name))
    for name, entry in archive.toc.items():
        if entry[-1] in ("s", "m", "M"):
            check_filenames(marshal.loads(archive.extract(name)))
    with zipfile.ZipFile(internal / "base_library.zip") as base_library:
        for name in base_library.namelist():
            if name.endswith(".pyc"):
                check_filenames(marshal.loads(base_library.read(name)[16:]))
    code_rows = []
    application = [("app", "app.py"), ("mailcairn", "mailcairn/__init__.py"),
                   ("mailcairn.instance", "mailcairn/instance.py"), ("mailcairn.parse", "mailcairn/parse.py"),
                   ("mailcairn.server", "mailcairn/server.py"), ("mailcairn.store", "mailcairn/store.py"),
                   ("mailcairn.sync", "mailcairn/sync.py"),
                   ("mailcairn.credentials", "mailcairn/credentials.py"),
                   ("mailcairn.imap_client", "mailcairn/imap_client.py"),
                   ("desktop", "desktop.py")]
    for module, relative in application:
        source = root / relative
        embedded = marshal.loads(archive.extract(module)) if module == "desktop" else pyz.extract(module)
        matches = compile(source.read_bytes(), embedded.co_filename, "exec", dont_inherit=True, optimize=0) == embedded
        code_rows.append({"module": module, "path": relative, "source_sha256": sha(source), "compiled_code_matches": matches})
        require(matches, f"Embedded application code differs from source: {module}")

    def compare_directory(relative, key):
        source_dir, target_dir = root / relative, internal / relative
        source_files = {path.relative_to(source_dir) for path in source_dir.rglob("*") if path.is_file()}
        target_files = {path.relative_to(target_dir) for path in target_dir.rglob("*") if path.is_file()}
        require(source_files == target_files, f"File inventory mismatch: {relative}")
        result = []
        for name in sorted(source_files):
            source, target = source_dir / name, target_dir / name
            matches = target.is_file() and source.read_bytes() == target.read_bytes()
            result.append({key: str(Path(relative) / name) if key == "path" else str(name),
                           "present": target.is_file(), "matches_source": matches,
                           "sha256": sha(target) if target.is_file() else None})
            require(matches, f"Bundle file differs/missing: {relative}/{name}")
        return result

    static_rows = compare_directory("mailcairn/static", "path")
    notice_rows = compare_directory("licenses/desktop", "file")
    project_notices = []
    for name in ("LICENSE", "NOTICE", "COMMERCIAL.md"):
        target = internal / name
        matches = target.is_file() and (root / name).read_bytes() == target.read_bytes()
        project_notices.append({"file": name, "present": target.is_file(), "matches_source": matches,
                                "sha256": sha(target) if target.is_file() else None})
        require(matches, f"Project notice mismatch/missing: {name}")
    manifest = json.loads((internal / "licenses/desktop/manifest.json").read_text(encoding="utf-8"))
    manifest_valid = all((internal / "licenses/desktop" / row["file"]).is_file() and
                         sha(internal / "licenses/desktop" / row["file"]) == row["sha256"] for row in manifest["files"])
    require(manifest_valid, "Desktop license manifest hash mismatch")
    require(len(manifest["files"]) == 19, "Expected 19 collected component notices; review new inventory before release")

    if failures:
        print(json.dumps({"status": "FAIL", "artifact": str(dist), "failures": failures}, indent=2))
        return 1
    evidence = {
        "reviewed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "artifact": f"MailCairn-{version}-windows-x64", "version": version, "exe_sha256": sha(exe), "python_build": sys.version,
        "selected_runtime_versions": manifest["versions"],
        "summary": {"native_count": len(native), "external_native_count": 0,
                    "all_native_bytes_match_toc_sources": True, "unexpected_python_thirdparty_modules": 0,
                    "all_application_code_matches_current_source": True, "all_static_bytes_match_current_source": True,
                    "all_desktop_notices_match_source": True, "manifest_19_hashes_valid": True,
                    "python_code_objects_checked_for_absolute_filenames": code_count},
        "native_files": native, "unexpected_python_modules": unexpected,
        "runtime_hooks": [{"module": row[0], "source": "build-runtime/" + Path(row[1]).relative_to(runtime).as_posix()} for row in hooks],
        "application_code": code_rows, "static_resources": static_rows, "desktop_notices": notice_rows,
        "project_notices": project_notices,
        "status": "PASS: artifact native origins, current app code, static resources and licenses match reviewed inputs",
        "scope": "Static artifact/TOC/hash/code reconciliation only. Current binary UI launch, clean-machine, signing and public release require separate evidence.",
    }
    for key in ("installer", "previous_candidate"):
        if key in previous:
            evidence[key] = previous[key]
    if args.write_evidence:
        previous_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "artifact": str(dist), "exe_sha256": evidence["exe_sha256"],
                      "native": len(native), "application_modules": len(code_rows), "static": len(static_rows),
                      "desktop_notices": len(notice_rows), "project_notices": len(project_notices),
                      "manifest_hashes": len(manifest["files"]), "evidence_written": args.write_evidence}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
