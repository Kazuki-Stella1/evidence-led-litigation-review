#!/usr/bin/env python3
"""Run evidence intake, mapping, logic review, and filing proofreading."""

from __future__ import annotations

import argparse
from pathlib import Path

from evidence_ingest import build_index
from evidence_map import build_map
from evidence_model import EvidenceError
from logic_check import write_report as write_logic_report
from proofread_filings import write_report as write_proofreading_report


def run_workflow(
    manifest: Path,
    out: Path,
    *,
    mode: str = "fast",
    ocr_language: str = "jpn+eng",
    proofreading_rules: Path | None = None,
) -> dict:
    intake_dir = out / "intake"
    map_dir = out / "map"
    logic_dir = out / "logic"
    proofreading_dir = out / "proofreading"
    index = build_index(
        manifest,
        intake_dir,
        mode=mode,
        default_ocr_language=ocr_language,
    )
    map_result = build_map(
        intake_dir / "evidence-index.json",
        map_dir / "evidence-map.html",
        map_dir / "evidence-map.svg",
    )
    logic = write_logic_report(intake_dir / "evidence-index.json", logic_dir)
    proofreading = write_proofreading_report(
        intake_dir / "evidence-index.json",
        proofreading_dir,
        rules_path=proofreading_rules,
    )
    return {
        "mode": mode,
        "items": len(index["items"]),
        "events": map_result["events"],
        "logic_findings": logic["finding_count"],
        "self_findings": logic["side_counts"]["self"],
        "opponent_findings": logic["side_counts"]["opponent"],
        "proofreading_findings": proofreading["finding_count"],
        "index": intake_dir / "evidence-index.md",
        "map": map_dir / "evidence-map.html",
        "logic": logic_dir / "logic-review.md",
        "proofreading": proofreading_dir / "proofreading-review.md",
        "proofreading_csv": proofreading_dir / "proofreading-review.csv",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=("fast", "precise"), default="fast")
    parser.add_argument("--ocr-lang", default="jpn+eng")
    parser.add_argument("--proofreading-rules", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = run_workflow(
            args.manifest,
            args.out,
            mode=args.mode,
            ocr_language=args.ocr_lang,
            proofreading_rules=args.proofreading_rules,
        )
    except EvidenceError as exc:
        print(f"Evidence workflow failed: {exc}")
        return 2
    print(
        f"Evidence workflow passed: {result['items']} item(s), {result['events']} dated event(s), "
        f"{result['logic_findings']} logic finding(s) "
        f"[self={result['self_findings']}, opponent={result['opponent_findings']}]; "
        f"{result['proofreading_findings']} proofreading candidate(s)."
    )
    print(f"Index: {result['index']}")
    print(f"Map:   {result['map']}")
    print(f"Logic: {result['logic']}")
    print(f"Proof: {result['proofreading']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
