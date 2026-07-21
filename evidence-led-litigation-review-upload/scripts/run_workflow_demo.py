#!/usr/bin/env python3
"""Run the fully fictional evidence workflow demo."""

from __future__ import annotations

import json
from pathlib import Path

from evidence_workflow import run_workflow


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    result = run_workflow(
        ROOT / "sample/workflow/input/manifest.json",
        ROOT / "sample/workflow/output",
        mode="fast",
        ocr_language="eng",
    )
    if result["items"] != 7:
        raise RuntimeError("The workflow fixture item count changed.")
    if result["events"] != 7:
        raise RuntimeError("The workflow fixture event count changed.")
    if result["logic_findings"] != 11:
        raise RuntimeError("The workflow fixture logic finding count changed.")
    if result["opponent_findings"] == 0:
        raise RuntimeError("The workflow fixture no longer tests opponent-side review.")
    if result["proofreading_findings"] != 1:
        raise RuntimeError("The workflow fixture no longer tests location-specific proofreading.")
    logic = json.loads(result["logic"].with_suffix(".json").read_text(encoding="utf-8"))
    codes = {item["code"] for item in logic["findings"] if item["side"] == "opponent"}
    for required in ("filing_cites_unknown_evidence", "direct_claim_uses_inferential_support"):
        if required not in codes:
            raise RuntimeError(f"The workflow fixture no longer demonstrates {required}.")
    map_html = result["map"].read_text(encoding="utf-8")
    if 'data-side="self"' not in map_html or 'data-side="opponent"' not in map_html:
        raise RuntimeError("The diagonal map no longer contains both sides.")
    print(
        f"workflow: {result['items']} item(s) | {result['events']} event(s) | "
        f"{result['logic_findings']} logic finding(s) | "
        f"{result['proofreading_findings']} proofreading candidate(s)"
    )
    print("Workflow demo verification passed.")
    print(f"Evidence index: {result['index']}")
    print(f"Diagonal map:  {result['map']}")
    print(f"Logic review:  {result['logic']}")
    print(f"Proofreading:  {result['proofreading']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
