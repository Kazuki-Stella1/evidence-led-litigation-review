#!/usr/bin/env python3
"""Run and verify the fully fictional filing-proofreading demo."""

from __future__ import annotations

import json
from pathlib import Path

from evidence_ingest import build_index
from proofread_filings import write_report


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sample = ROOT / "sample/proofreading"
    intake = sample / "output/intake"
    index = build_index(
        sample / "input/manifest.json",
        intake,
        mode="fast",
        default_ocr_language="eng",
    )
    report = write_report(intake / "evidence-index.json", sample / "output/proofreading")
    if len(index["items"]) != 3:
        raise RuntimeError("The proofreading fixture item count changed.")
    if report["finding_count"] != 7:
        raise RuntimeError(
            f"The proofreading fixture finding count changed: {report['finding_count']} != 7."
        )
    payload = json.loads(report["json_path"].read_text(encoding="utf-8"))
    codes = {item["code"] for item in payload["findings"]}
    for required in (
        "literal_correction",
        "duplicate_input",
        "wrong_exhibit_reference",
        "unknown_exhibit_reference",
        "unclosed_bracket",
    ):
        if required not in codes:
            raise RuntimeError(f"The proofreading fixture no longer demonstrates {required}.")
    wrong = next(item for item in payload["findings"] if item["code"] == "wrong_exhibit_reference")
    if wrong["suggestion"] != "甲2" or wrong["line"] != 4:
        raise RuntimeError("The location-specific exhibit correction changed.")
    csv_payload = report["csv_path"].read_bytes()
    if not csv_payload.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError("The proofreading CSV no longer has a UTF-8 BOM.")
    print(f"proofreading: {report['filing_count']} filing(s) | {report['finding_count']} candidate(s)")
    print("Proofreading demo verification passed.")
    print(f"Markdown: {report['markdown_path']}")
    print(f"JSON:     {report['json_path']}")
    print(f"CSV:      {report['csv_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
