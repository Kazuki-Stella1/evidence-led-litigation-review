#!/usr/bin/env python3
"""List deterministic consistency gaps between filings, claims, and evidence."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from evidence_model import (
    EvidenceError,
    annotation_lines,
    extract_evidence_ids,
    load_json,
    parse_event_date,
)


@dataclass
class Finding:
    severity: str
    code: str
    side: str
    message: str
    claim_id: str | None = None
    filing_id: str | None = None
    evidence_ids: list[str] | None = None
    repair: str | None = None


def item_text(index_path: Path, item: dict) -> str:
    relative = item.get("raw_text_file") or item.get("text_file")
    if not relative:
        return ""
    path = index_path.parent / str(relative)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def claim_evidence_entries(claim: dict) -> list[dict]:
    values = claim.get("evidence", [])
    if isinstance(values, str):
        values = [values]
    result: list[dict] = []
    for value in values if isinstance(values, list) else []:
        if isinstance(value, str):
            result.append({"id": value, "support": "unspecified"})
        elif isinstance(value, dict) and value.get("id"):
            result.append({"id": str(value["id"]), "support": value.get("support", "unspecified")})
    return result


def list_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def evidence_annotation_text(item: dict) -> str:
    annotations = item.get("annotations", {})
    values: list[str] = []
    for key in ("summary", "facts", "proves", "causation", "contradictions", "inferences"):
        values.extend(annotation_lines(annotations, key))
    return "\n".join(values)


def analyze_logic(index_path: Path) -> dict:
    index = load_json(index_path)
    items = index.get("items", [])
    if not isinstance(items, list):
        raise EvidenceError("evidence-index items must be an array")
    item_by_id = {str(item.get("id")): item for item in items if isinstance(item, dict) and item.get("id")}
    filings = {item_id: item for item_id, item in item_by_id.items() if item.get("kind") == "filing"}
    filing_text = {item_id: item_text(index_path, item) for item_id, item in filings.items()}
    filing_citations = {item_id: set(extract_evidence_ids(text)) for item_id, text in filing_text.items()}
    claims = index.get("claims", [])
    if not isinstance(claims, list):
        raise EvidenceError("evidence-index claims must be an array")
    claim_by_id = {
        str(claim.get("id")): claim
        for claim in claims
        if isinstance(claim, dict) and claim.get("id")
    }
    findings: list[Finding] = []
    used_evidence: set[str] = set()

    for item_id, item in item_by_id.items():
        side = item.get("side", "neutral")
        if item.get("annotation_status") == "incomplete" and item.get("kind") != "filing":
            findings.append(
                Finding(
                    "review",
                    "annotation_incomplete",
                    side,
                    f"{item_id}の証拠注釈が未完成です: {', '.join(item.get('missing_annotations', []))}",
                    evidence_ids=[item_id],
                    repair="抽出テキスト又は原本で確認できる範囲だけを記載し、未確認欄は未確認のまま明示してください。",
                )
            )
        if item.get("importance") in {"high", "critical"} and item.get("precision_status") != "source_verified":
            findings.append(
                Finding(
                    "material" if item.get("importance") == "critical" else "review",
                    "important_source_unverified",
                    side,
                    f"{item_id}の重要度は{item.get('importance')}ですが、原本の精密確認が完了していません。",
                    evidence_ids=[item_id],
                    repair="最終利用前に原本を開き、引用、日付、金額、頁を確認してからsource_checkedを記録してください。",
                )
            )
        if not item_text(index_path, item).strip():
            findings.append(
                Finding(
                    "critical",
                    "missing_extracted_text",
                    side,
                    f"{item_id}に読取り可能なキャッシュテキストがありません。",
                    evidence_ids=[item_id],
                    repair="対応する抽出方法又は原本確認済みの転記を用いて取込みを再実行してください。",
                )
            )
        for warning in item.get("extraction_warnings", []):
            if "differ" in warning or "failed" in warning or "impossible" in warning:
                findings.append(
                    Finding(
                        "material",
                        "source_extraction_warning",
                        side,
                        f"{item_id}: {warning}",
                        evidence_ids=[item_id],
                        repair="このテキストを根拠として利用する前に、抽出警告を原本と照合して解消してください。",
                    )
                )

    for filing_id, citations in filing_citations.items():
        filing = filings[filing_id]
        for evidence_id in sorted(citations):
            used_evidence.add(evidence_id)
            if evidence_id not in item_by_id:
                findings.append(
                    Finding(
                        "critical",
                        "filing_cites_unknown_evidence",
                        filing.get("side", "neutral"),
                        f"{filing_id}は{evidence_id}を引用していますが、証拠台帳に存在しません。",
                        filing_id=filing_id,
                        evidence_ids=[evidence_id],
                        repair="正確な号証を台帳へ追加するか、書面の引用番号を修正してください。",
                    )
                )

    for claim_id, claim in claim_by_id.items():
        side = claim.get("side", "neutral")
        filing_id = str(claim.get("filing_id") or "")
        statement = str(claim.get("statement") or "").strip()
        proof_type = claim.get("proof_type", "inference")
        entries = claim_evidence_entries(claim)
        evidence_ids = [entry["id"] for entry in entries]
        used_evidence.update(evidence_ids)

        if not statement:
            findings.append(
                Finding(
                    "material",
                    "claim_statement_missing",
                    side,
                    f"{claim_id}に正規化された主張命題がありません。",
                    claim_id=claim_id,
                    filing_id=filing_id or None,
                    repair="証拠連鎖を検証する前に、一つの主張を一つの命題として記載してください。",
                )
            )
        if not filing_id or filing_id not in filings:
            findings.append(
                Finding(
                    "critical",
                    "claim_filing_missing",
                    side,
                    f"{claim_id}が存在しない書面を指定しています: {filing_id or '[未指定]'}。",
                    claim_id=claim_id,
                    filing_id=filing_id or None,
                    evidence_ids=evidence_ids,
                    repair="この命題が記載された自分側又は相手方の書面を正確に指定してください。",
                )
            )
            text = ""
        else:
            text = filing_text[filing_id]
            filing_side = filings[filing_id].get("side", "neutral")
            if side != filing_side:
                findings.append(
                    Finding(
                        "material",
                        "claim_side_mismatch",
                        side,
                        f"{claim_id}のsideは{side}ですが、{filing_id}のsideは{filing_side}です。",
                        claim_id=claim_id,
                        filing_id=filing_id,
                        evidence_ids=evidence_ids,
                        repair="sideを修正するか、主張を本来の書面へ割り当ててください。",
                    )
                )

        if proof_type in {"direct", "fact", "causation"} and not entries:
            findings.append(
                Finding(
                    "critical",
                    "material_claim_without_evidence",
                    side,
                    f"{claim_id}は{proof_type}に分類されていますが、対応証拠がありません。",
                    claim_id=claim_id,
                    filing_id=filing_id or None,
                    repair="直接証拠を対応付けるか、命題を争いあり・未確認・推論へ再分類してください。",
                )
            )

        match_terms = list_strings(claim.get("match_terms"))
        if filing_id in filings and match_terms and not all(term in text for term in match_terms):
            missing = [term for term in match_terms if term not in text]
            findings.append(
                Finding(
                    "material",
                    "claim_text_not_found",
                    side,
                    f"{claim_id}を{filing_id}内で特定できません。未検出語: {', '.join(missing)}",
                    claim_id=claim_id,
                    filing_id=filing_id,
                    evidence_ids=evidence_ids,
                    repair="検索語を更新するか、この命題がある正しい書面版を指定してください。",
                )
            )

        known_entries: list[tuple[dict, dict]] = []
        for entry in entries:
            evidence_id = entry["id"]
            evidence = item_by_id.get(evidence_id)
            if not evidence:
                findings.append(
                    Finding(
                        "critical",
                        "claim_maps_unknown_evidence",
                        side,
                        f"{claim_id}が存在しない証拠{evidence_id}へ対応付けられています。",
                        claim_id=claim_id,
                        filing_id=filing_id or None,
                        evidence_ids=[evidence_id],
                        repair="号証IDを修正するか、不足する原資料を取り込んでください。",
                    )
                )
                continue
            known_entries.append((entry, evidence))
            if filing_id in filings and evidence_id not in filing_citations[filing_id]:
                findings.append(
                    Finding(
                        "material",
                        "mapped_evidence_not_cited",
                        side,
                        f"{claim_id}は{evidence_id}へ対応付けられていますが、{filing_id}は同号証を引用していません。",
                        claim_id=claim_id,
                        filing_id=filing_id,
                        evidence_ids=[evidence_id],
                        repair="対応箇所へ号証・頁を引用するか、近接する引用がこの命題を含む理由を明示してください。",
                    )
                )
            if proof_type == "direct" and entry.get("support") not in {"direct", "unspecified"}:
                findings.append(
                    Finding(
                        "material",
                        "direct_claim_uses_inferential_support",
                        side,
                        f"{claim_id}は直接立証に分類されていますが、{evidence_id}の支え方は{entry.get('support')}です。",
                        claim_id=claim_id,
                        filing_id=filing_id or None,
                        evidence_ids=[evidence_id],
                        repair="号証が直接示す内容と、そこから先の推論を分けてください。",
                    )
                )

        proof_terms = list_strings(claim.get("proof_terms"))
        if proof_terms and known_entries:
            annotation_text = "\n".join(evidence_annotation_text(evidence) for _, evidence in known_entries)
            missing = [term for term in proof_terms if term not in annotation_text]
            if missing:
                findings.append(
                    Finding(
                        "material",
                        "proof_purpose_mismatch",
                        side,
                        f"{claim_id}が求める立証語が対応証拠の注釈にありません: {', '.join(missing)}",
                        claim_id=claim_id,
                        filing_id=filing_id or None,
                        evidence_ids=evidence_ids,
                        repair="主張を限定し、立証趣旨を修正し、又は不足命題を直接支える資料へ対応付けてください。",
                    )
                )

        if claim.get("date_must_match_evidence") and claim.get("event_date") and known_entries:
            expected = str(claim["event_date"])
            actual = {str(evidence.get("event_date")) for _, evidence in known_entries if evidence.get("event_date")}
            if actual and expected not in actual:
                findings.append(
                    Finding(
                        "material",
                        "claim_evidence_date_mismatch",
                        side,
                        f"{claim_id}の日付{expected}が、対応証拠の日付{', '.join(sorted(actual))}と一致しません。",
                        claim_id=claim_id,
                        filing_id=filing_id or None,
                        evidence_ids=evidence_ids,
                        repair="原本の日付を確認し、出来事の日付、作成日、後日の通知日を分けてください。",
                    )
                )

        claim_date = parse_event_date(claim.get("event_date"))
        for cause_id in list_strings(claim.get("causes")):
            cause = claim_by_id.get(cause_id)
            if not cause:
                findings.append(
                    Finding(
                        "critical",
                        "causal_link_unknown_claim",
                        side,
                        f"{claim_id}が存在しない原因命題{cause_id}を指定しています。",
                        claim_id=claim_id,
                        filing_id=filing_id or None,
                        evidence_ids=evidence_ids,
                        repair="不足命題を作成するか、裏付けのない因果リンクを削除してください。",
                    )
                )
                continue
            cause_date = parse_event_date(cause.get("event_date"))
            if claim_date and cause_date and cause_date > claim_date:
                findings.append(
                    Finding(
                        "critical",
                        "causal_order_reversed",
                        side,
                        f"原因とされた{cause_id}（{cause_date}）が、結果とされた{claim_id}（{claim_date}）より後です。",
                        claim_id=claim_id,
                        filing_id=filing_id or None,
                        evidence_ids=evidence_ids,
                        repair="日付を修正するか、時間順序が逆転した因果主張を削除してください。",
                    )
                )

    contradictions = index.get("contradictions", [])
    addressed = {
        contradiction_id
        for claim in claim_by_id.values()
        for contradiction_id in list_strings(claim.get("addresses_contradictions"))
    }
    for contradiction in contradictions if isinstance(contradictions, list) else []:
        if not isinstance(contradiction, dict) or not contradiction.get("id"):
            continue
        contradiction_id = str(contradiction["id"])
        applies_to = list_strings(contradiction.get("applies_to"))
        if applies_to and contradiction_id not in addressed:
            side = contradiction.get("side", "neutral")
            findings.append(
                Finding(
                    "material",
                    "contradiction_unaddressed",
                    side,
                    f"{contradiction_id}がいずれの対応主張でも処理されていません: {contradiction.get('text', '')}",
                    claim_id=applies_to[0] if len(applies_to) == 1 else None,
                    evidence_ids=list_strings(contradiction.get("evidence")),
                    repair="相反する説明、反対資料による応答、又は未解決である旨を明示してください。",
                )
            )

    for item_id, item in item_by_id.items():
        if item.get("kind") == "evidence" and item_id not in used_evidence:
            findings.append(
                Finding(
                    "review",
                    "evidence_not_mapped_to_claim",
                    item.get("side", "neutral"),
                    f"{item_id}は台帳にありますが、正規化された主張又は書面引用へ対応付けられていません。",
                    evidence_ids=[item_id],
                    repair="立証趣旨を特定するか、対象外である旨を記録してください。",
                )
            )

    order = {"critical": 0, "material": 1, "review": 2}
    findings.sort(key=lambda item: (order.get(item.severity, 9), item.side, item.code, item.claim_id or ""))
    counts = {
        severity: sum(1 for item in findings if item.severity == severity)
        for severity in ("critical", "material", "review")
    }
    side_counts = {
        side: sum(1 for item in findings if item.side == side)
        for side in ("self", "opponent", "neutral")
    }
    return {
        "case_id": index.get("case_id"),
        "scope": "self_and_opponent",
        "finding_count": len(findings),
        "severity_counts": counts,
        "side_counts": side_counts,
        "findings": [asdict(item) for item in findings],
        "disclaimer": (
            "これは決定的な不整合候補の一覧です。意味上の網羅性、証拠の真正、法的当否又は因果関係を"
            "立証するものではありません。GPT-5.6/Codexによる検討と、人による原本確認が必要です。"
        ),
    }


def markdown_report(result: dict) -> str:
    counts = result["severity_counts"]
    lines = [
        "# 書面・証拠 論理検証レポート",
        "",
        f"- Case ID: `{result.get('case_id')}`",
        "- Scope: 自分側及び相手方",
        f"- Findings: **{result['finding_count']}**",
        f"- Critical: **{counts['critical']}** / Material: **{counts['material']}** / Review: **{counts['review']}**",
        f"- Self: **{result['side_counts']['self']}** / Opponent: **{result['side_counts']['opponent']}** / Neutral: **{result['side_counts']['neutral']}**",
        "",
        "> この一覧は決定的な不整合候補であり、法的結論、証拠の真正、因果関係又は網羅性を自動判定しません。",
        "",
    ]
    for side, label in (("self", "自分側"), ("opponent", "相手方"), ("neutral", "中立・その他")):
        side_findings = [item for item in result["findings"] if item["side"] == side]
        if not side_findings:
            continue
        lines.extend([f"## {label}", ""])
        for number, item in enumerate(side_findings, 1):
            title = f"{number}. {item['severity'].upper()} — `{item['code']}`"
            lines.extend([f"### {title}", "", item["message"], ""])
            metadata = []
            if item.get("claim_id"):
                metadata.append(f"主張: `{item['claim_id']}`")
            if item.get("filing_id"):
                metadata.append(f"書面: `{item['filing_id']}`")
            if item.get("evidence_ids"):
                metadata.append("証拠: " + ", ".join(f"`{value}`" for value in item["evidence_ids"]))
            if metadata:
                lines.extend([" / ".join(metadata), ""])
            if item.get("repair"):
                lines.extend([f"**確認・修正:** {item['repair']}", ""])
    lines.extend(["---", "", result["disclaimer"], ""])
    return "\n".join(lines)


def write_report(index_path: Path, out_dir: Path) -> dict:
    result = analyze_logic(index_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "logic-review.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "logic-review.md").write_text(markdown_report(result), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = write_report(args.index, args.out)
    except EvidenceError as exc:
        print(f"Logic check failed: {exc}")
        return 2
    print(
        f"Logic review: {result['finding_count']} finding(s) "
        f"[self={result['side_counts']['self']}, opponent={result['side_counts']['opponent']}]"
    )
    print(args.out / "logic-review.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
