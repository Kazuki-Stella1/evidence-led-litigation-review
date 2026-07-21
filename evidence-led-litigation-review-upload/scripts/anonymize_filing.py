#!/usr/bin/env python3
"""Create a deterministic redacted text copy of a TXT, MD, or DOCX filing."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from analyze_filing import read_filing


PHONE = re.compile(r"(?<!\d)(?:0\d{1,4}[－ー\-]\d{1,4}[－ー\-]\d{3,4}|0\d{9,10})(?!\d)")
POSTAL = re.compile(r"〒?\s*\d{3}[－ー\-]\d{4}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filing", required=True, type=Path)
    parser.add_argument("--mapping", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    if not isinstance(mapping, dict):
        raise ValueError("Mapping must be a JSON object")
    text = "\n\n".join(read_filing(args.filing))
    for source in sorted(mapping, key=len, reverse=True):
        text = text.replace(source, str(mapping[source]))
    text = PHONE.sub("[電話番号削除]", text)
    text = POSTAL.sub("[郵便番号削除]", text)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
