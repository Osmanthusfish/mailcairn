"""Create a clean, deterministic source release; never include local archives."""
import argparse
import hashlib
import os
from pathlib import Path
import tempfile
import zipfile

try:
    from .release_check import ROOT, check, is_link, source_files
except ImportError:  # Direct script launch.
    from release_check import ROOT, check, is_link, source_files


def create_release(output, root=ROOT):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError("Write the ZIP outside the source tree")
    # Validate the exact bytes that will be packaged, not a second later read.
    content = {rel: path.read_bytes() for path, rel in source_files(root) if not is_link(path)}
    result = check(root, content=content)
    if not result["passed"]:
        raise ValueError("Release checks failed: " + str(result["problems"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".mailcairn-release-", suffix=".tmp", dir=output.parent)
    os.close(descriptor)
    staged = Path(temporary)
    try:
        with zipfile.ZipFile(staged, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for rel, data in sorted(content.items()):
                info = zipfile.ZipInfo("mailcairn/" + rel.as_posix(), date_time=(2026, 11, 9, 0, 0, 0))
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100755 if rel.suffix == ".sh" else 0o100644) << 16
                archive.writestr(info, data)
        with zipfile.ZipFile(staged) as archive:
            if archive.testzip() is not None or len(archive.infolist()) != len(content):
                raise ValueError("Source ZIP verification failed")
            for rel, data in content.items():
                if archive.read("mailcairn/" + rel.as_posix()) != data:
                    raise ValueError("Source ZIP content differs from checked source")
        digest = hashlib.sha256(staged.read_bytes()).hexdigest()
        os.replace(staged, output)
    finally:
        staged.unlink(missing_ok=True)
    output.with_suffix(output.suffix + ".sha256").write_text(digest + "  " + output.name + "\n", encoding="ascii")
    return {"output": output.name, "bytes": output.stat().st_size, "sha256": digest, "files": len(content)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="ZIP destination outside this source directory")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error("Write the ZIP outside the source tree")
    try:
        result = create_release(output)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print(f"Created {result['output']}: {result['bytes']:,} bytes; SHA-256 {result['sha256']}")


if __name__ == "__main__":
    main()
