#!/usr/bin/env python3
"""Build a deterministic ZIP from the clean, Git-tracked release tree."""

from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def main() -> int:
    if run_git("diff", "--quiet").returncode or run_git("diff", "--cached", "--quiet").returncode:
        raise RuntimeError("Commit or revert tracked changes before building the release ZIP.")

    manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    name = manifest["name"]
    version = manifest["version"]
    archive_path = DIST / f"{name}-{version}.zip"
    marketplace_archive_path = DIST / f"{name}-marketplace-{version}.zip"
    paths = sorted(item for item in run_git("ls-files", "-z").stdout.split("\0") if item)

    DIST.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in paths:
            source = ROOT / path
            info = zipfile.ZipInfo(f"{name}/{path}", date_time=(2026, 7, 20, 0, 0, 0))
            executable = path.endswith((".py", ".sh"))
            mode = stat.S_IFREG | (0o755 if executable else 0o644)
            info.external_attr = mode << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())

    marketplace_root = f"{name}-marketplace"
    marketplace = {
        "name": f"{name}-local",
        "interface": {"displayName": "Evidence-Led Litigation Review Local"},
        "plugins": [
            {
                "name": name,
                "source": {"source": "local", "path": f"./plugins/{name}"},
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": "Productivity",
            }
        ],
    }
    with zipfile.ZipFile(
        marketplace_archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        marketplace_info = zipfile.ZipInfo(
            f"{marketplace_root}/.agents/plugins/marketplace.json",
            date_time=(2026, 7, 20, 0, 0, 0),
        )
        marketplace_info.external_attr = (stat.S_IFREG | 0o644) << 16
        marketplace_info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(
            marketplace_info,
            json.dumps(marketplace, ensure_ascii=False, indent=2).encode("utf-8") + b"\n",
        )
        for path in paths:
            source = ROOT / path
            info = zipfile.ZipInfo(
                f"{marketplace_root}/plugins/{name}/{path}",
                date_time=(2026, 7, 20, 0, 0, 0),
            )
            executable = path.endswith((".py", ".sh"))
            mode = stat.S_IFREG | (0o755 if executable else 0o644)
            info.external_attr = mode << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())

    checksum_path = DIST / "SHA256SUMS"
    checksum_lines = []
    for path in (archive_path, marketplace_archive_path):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        checksum_lines.append(f"{digest}  {path.name}")
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    print(archive_path)
    print(marketplace_archive_path)
    print(checksum_path)
    print(f"files={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
