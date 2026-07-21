#!/usr/bin/env python3
"""Fail on common identifiers or risky binary evidence in a public release.

The scanner is intentionally conservative and must be supplemented by a human
semantic review. Exact private names can be supplied at runtime with repeated
``--deny`` arguments; those values are never written to the repository.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RISKY_EXTENSIONS = {
    ".doc", ".docx", ".heic", ".jpeg", ".jpg", ".m4a", ".mov", ".mp3",
    ".mp4", ".pdf", ".png", ".tif", ".tiff", ".wav",
}
PATTERNS = {
    "japanese_phone": re.compile(
        r"(?<!\d)(?:0\d{1,4}[－ー\-]\d{1,4}[－ー\-]\d{3,4}|0\d{9,10})(?!\d)"
    ),
    "postal_code": re.compile(r"(?<!\d)〒?\s*\d{3}[－ー\-]\d{4}(?!\d)"),
    "court_case_number": re.compile(
        r"(?:令和|平成|昭和)\s*\d+\s*年\s*[（(][^）)\n]{1,12}[）)]\s*第\s*\d+\s*号"
    ),
}


@dataclass(frozen=True)
class Finding:
    source: str
    path: str
    code: str
    line: int | None = None


def git(*args: str, input_text: str | None = None) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_text,
        text=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def scan_text(source: str, path: str, text: str, denied: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if "privacy-scan-allow" in line:
            continue
        for code, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append(Finding(source, path, code, line_number))
        if any(token and token in line for token in denied):
            findings.append(Finding(source, path, "private_deny_token", line_number))
    return findings


def scan_blob(source: str, path: str, payload: bytes, denied: list[str]) -> list[Finding]:
    if Path(path).suffix.lower() in RISKY_EXTENSIONS:
        return [Finding(source, path, "risky_binary_extension")]
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return [Finding(source, path, "non_utf8_or_binary_file")]
    return scan_text(source, path, text, denied)


def scan_current(denied: list[str]) -> tuple[list[Finding], int]:
    paths = [
        item
        for item in git("ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0")
        if item
    ]
    findings: list[Finding] = []
    for path in paths:
        findings.extend(scan_blob("worktree", path, (ROOT / path).read_bytes(), denied))
    return findings, len(paths)


def scan_history(denied: list[str]) -> tuple[list[Finding], int]:
    commits = [item for item in git("rev-list", "--all").splitlines() if item]
    findings: list[Finding] = []
    inspected = 0
    seen: set[tuple[str, str]] = set()
    for commit in commits:
        paths = [
            item
            for item in git("ls-tree", "-r", "--name-only", "-z", commit).split("\0")
            if item
        ]
        for path in paths:
            object_id = git("rev-parse", f"{commit}:{path}").strip()
            key = (object_id, path)
            if key in seen:
                continue
            seen.add(key)
            payload = subprocess.run(
                ["git", "cat-file", "blob", object_id],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout
            inspected += 1
            findings.extend(scan_blob(commit[:12], path, payload, denied))
    return findings, inspected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--history",
        action="store_true",
        help="also inspect every unique file version reachable from Git history",
    )
    parser.add_argument(
        "--deny",
        action="append",
        default=[],
        metavar="PRIVATE_TOKEN",
        help="fail if an exact private token occurs; repeat as needed",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings, current_count = scan_current(args.deny)
    history_count = 0
    if args.history:
        history_findings, history_count = scan_history(args.deny)
        findings.extend(history_findings)

    print(f"Scanned {current_count} tracked worktree files.")
    if args.history:
        print(f"Scanned {history_count} unique historical file versions.")
    if findings:
        for item in findings:
            location = f":{item.line}" if item.line else ""
            print(f"FAIL {item.source} {item.path}{location} [{item.code}]")
        print("Public-release privacy scan failed.")
        return 1
    print("Public-release privacy scan passed; manual semantic review is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
