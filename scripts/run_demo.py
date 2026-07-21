#!/usr/bin/env python3
"""Run the synthetic before/after demo on any Python-supported platform."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "scripts" / "analyze_filing.py"
EVIDENCE = ROOT / "sample" / "input" / "evidence.json"


def run_case(name: str, filing: Path, output: Path) -> dict:
    command = [
        sys.executable,
        str(ANALYZER),
        "--filing",
        str(filing),
        "--evidence",
        str(EVIDENCE),
        "--out",
        str(output),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    result = json.loads((output / "review.json").read_text(encoding="utf-8"))
    print(
        f"{name}: {result['status']} | {result['score']}/100 | "
        f"{len(result['findings'])} finding(s)"
    )
    return result


def main() -> int:
    draft = run_case(
        "draft",
        ROOT / "sample" / "input" / "complaint_draft.txt",
        ROOT / "sample" / "output" / "draft",
    )
    stable = run_case(
        "stable",
        ROOT / "sample" / "fixed" / "complaint_stable.txt",
        ROOT / "sample" / "output" / "stable",
    )

    if draft["status"] != "working draft":
        raise RuntimeError("The draft fixture no longer demonstrates critical findings.")
    if stable["score"] != 100 or stable["findings"]:
        raise RuntimeError("The stable fixture no longer demonstrates a clean report.")

    print("Demo verification passed.")
    print(f"Draft report:  {ROOT / 'sample/output/draft/review.md'}")
    print(f"Stable report: {ROOT / 'sample/output/stable/review.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
