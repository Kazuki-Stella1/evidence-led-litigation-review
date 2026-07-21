#!/usr/bin/env python3
"""Deterministic triage for Japanese litigation filings.

The analyzer is local and dependency-free. It accepts TXT, MD, or DOCX,
compares exhibit citations with a JSON evidence index, and writes JSON and
Markdown reports. It does not decide legal merit.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

EXHIBIT_RE = re.compile(r"甲\s*(\d+)(?:\s*(?:の|－|-)\s*(\d+))?")
EXHIBIT_RANGE_RE = re.compile(r"甲\s*(\d+)\s*ないし\s*甲?\s*(\d+)")
DATE_RE = re.compile(
    r"(?:令和\s*[1-9]\d*年\s*\d{1,2}月\s*\d{1,2}日|20\d{2}年\s*\d{1,2}月\s*\d{1,2}日)"
)
PLACEHOLDER_PATTERNS = [
    ("unresolved_exhibit", re.compile(r"甲\s*[○〇]\s*(?:号証(?:拠)?)?")),
    ("generic_exhibit", re.compile(r"(?<![\d○〇])甲号証(?:拠)?(?!写し)")),
    ("todo_marker", re.compile(r"\b(?:TODO|TBD|FIXME)\b|要確認|未確定", re.IGNORECASE)),
    ("blank_marker", re.compile(r"\[\s*記入\s*\]|＜\s*記入\s*＞")),
]

EXPRESSION_TERMS = {
    "詐欺": "行為、発言、資料、時系列を先に示し、故意の欺罔という推論を分けてください。",
    "共犯": "刑事法上の評価語を避け、客観的な関連共同の事実を書いてください。",
    "未必の故意": "認識した具体的危険と、認容を推認させる事実を示してください。",
    "明らかに": "何が、どの証拠との比較で明らかなのかを特定してください。",
    "復讐": "請求原因には不要です。責任確認と法的救済の目的に置き換えてください。",
    "保険": "損害額は保険上限ではなく、損害の発生と算定から構成してください。",
}

MATERIAL_TERMS = (
    "虚偽", "支払", "診断", "入院", "療養", "退職", "休業損害",
    "逸失利益", "因果関係", "共同不法行為", "名誉", "医療記録",
)


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    paragraph: int | None = None
    excerpt: str | None = None
    repair: str | None = None


def read_docx(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", NS):
        text = "".join(
            (node.text or "") for node in paragraph.findall(".//w:t", NS)
        ).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def read_filing(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx(path)
    if suffix in {".txt", ".md"}:
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    raise ValueError("Supported filing formats are .txt, .md, and .docx")


def normalize_exhibit_id(raw: str) -> str:
    match = EXHIBIT_RE.search(raw.replace(" ", ""))
    if not match:
        return raw.strip()
    base, branch = match.groups()
    return f"甲{int(base)}" + (f"の{int(branch)}" if branch else "")


def base_id(exhibit_id: str) -> str:
    match = re.match(r"甲(\d+)", exhibit_id)
    return f"甲{int(match.group(1))}" if match else exhibit_id


def extract_exhibits(text: str) -> list[str]:
    refs: list[str] = []
    for match in EXHIBIT_RANGE_RE.finditer(text):
        start, end = int(match.group(1)), int(match.group(2))
        if start <= end and end - start <= 100:
            refs.extend(f"甲{number}" for number in range(start, end + 1))
    for match in EXHIBIT_RE.finditer(text):
        ref = f"甲{int(match.group(1))}" + (
            f"の{int(match.group(2))}" if match.group(2) else ""
        )
        refs.append(ref)
    return list(dict.fromkeys(refs))


def load_evidence(path: Path | None) -> list[dict]:
    if path is None:
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("evidence", raw) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise ValueError("Evidence JSON must be a list or an object with an 'evidence' list")
    normalized = []
    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            raise ValueError("Every evidence item must be an object containing 'id'")
        copy = dict(item)
        copy["id"] = normalize_exhibit_id(str(copy["id"]))
        normalized.append(copy)
    return normalized


def short(text: str, limit: int = 110) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def analyze(paragraphs: list[str], evidence: list[dict]) -> dict:
    text = "\n".join(paragraphs)
    findings: list[Finding] = []

    for code, pattern in PLACEHOLDER_PATTERNS:
        for index, paragraph in enumerate(paragraphs, 1):
            if pattern.search(paragraph):
                findings.append(Finding(
                    "critical", code, "提出前に解消すべき未確定表記があります。",
                    index, short(paragraph),
                    "正確な号証、日付、金額又は文言へ置換してください。",
                ))

    cited: list[str] = []
    citation_paragraphs: dict[str, list[int]] = {}
    for index, paragraph in enumerate(paragraphs, 1):
        for exhibit_id in extract_exhibits(paragraph):
            cited.append(exhibit_id)
            citation_paragraphs.setdefault(exhibit_id, []).append(index)

    known_ids = {item["id"] for item in evidence}
    known_bases = {base_id(item["id"]) for item in evidence}
    for exhibit_id in sorted(
        set(cited), key=lambda value: (int(re.search(r"\d+", value).group()), value)
    ):
        if evidence and exhibit_id not in known_ids and base_id(exhibit_id) not in known_bases:
            findings.append(Finding(
                "critical", "unknown_exhibit",
                f"本文の{exhibit_id}が証拠索引にありません。",
                citation_paragraphs[exhibit_id][0],
                repair="号証番号又は証拠索引を修正してください。",
            ))

    cited_bases = {base_id(item) for item in cited}
    unused = [item["id"] for item in evidence if base_id(item["id"]) not in cited_bases]
    if unused:
        findings.append(Finding(
            "review", "unused_evidence",
            "本文から参照されない証拠があります: " + "、".join(unused),
            repair="重要証拠なら本文に対応付け、不要なら提出範囲を再検討してください。",
        ))

    for section in ("請求の趣旨", "請求の原因", "損害", "因果関係"):
        if section not in text:
            findings.append(Finding(
                "material", "missing_section",
                f"「{section}」に相当する記載を確認できません。",
                repair="見出し又は明確な記載を追加してください。",
            ))

    if "415条" in text and ("弁護士" in text or "代理人" in text):
        findings.append(Finding(
            "material", "contract_duty_to_adverse_party",
            "相手方代理人に対する請求で民法415条が現れます。直接の契約関係を再確認してください。",
            repair="契約関係がなければ709・710・719条を基礎とし、職業規範は過失・違法性の評価資料として整理します。",
        ))

    if "弁護士" in text and "代理人" in text and "著しく相当性を欠" not in text:
        findings.append(Finding(
            "material", "litigation_activity_standard_missing",
            "相手方代理人の訴訟活動を問題としていますが、通常の訴訟活動との境界基準が明示されていません。",
            repair="客観的に根拠を欠く前提、認識又は容易な確認可能性、訂正機会、訂正後の継続を具体化してください。",
        ))

    for term, repair in EXPRESSION_TERMS.items():
        expression_text = text.replace("詐欺的取引", "") if term == "詐欺" else text
        count = expression_text.count(term)
        if count:
            severity = "material" if term in {"詐欺", "共犯", "未必の故意", "保険"} else "review"
            findings.append(Finding(
                severity, "loaded_expression", f"評価語「{term}」が{count}回あります。",
                repair=repair,
            ))

    if "精神的苦痛及び逸失利益、休業損害、精神的苦痛" in text:
        findings.append(Finding(
            "critical", "duplicate_damage_phrase",
            "精神的苦痛が同一列挙内で重複しています。",
            repair="非財産的損害、休業損害、逸失利益に区分してください。",
        ))

    if "休業損害" in text and "逸失利益" in text:
        if "期間" not in text or ("重複" not in text and "別個" not in text):
            findings.append(Finding(
                "material", "damage_period_overlap",
                "休業損害と逸失利益の算定期間が重複しないことを確認できません。",
                repair="各損害の始期・終期、基礎収入、控除額及び算式を表で分離してください。",
            ))

    if "一部" in text and "請求" in text and "内金" not in text and "内訳" not in text:
        findings.append(Finding(
            "material", "partial_claim_allocation",
            "一部請求の可能性がありますが、損害項目への配分が明示されていません。",
            repair="請求額を損害項目別に配分し、留保する残額を明記してください。",
        ))

    unsupported_material = []
    for index, paragraph in enumerate(paragraphs, 1):
        nearby = "\n".join(paragraphs[max(0, index - 2): min(len(paragraphs), index + 1)])
        legal_evaluation = any(
            term in paragraph for term in ("最高裁", "民法", "弁護士法", "職務基本規程")
        )
        claim_line = paragraph.startswith("1　被告は、原告に対し")
        if (
            any(term in paragraph for term in MATERIAL_TERMS)
            and not extract_exhibits(nearby)
            and not legal_evaluation
            and not claim_line
        ):
            if len(paragraph) > 45 and not paragraph.startswith(("第", "請求の趣旨")):
                unsupported_material.append((index, short(paragraph)))
    for index, excerpt in unsupported_material[:12]:
        findings.append(Finding(
            "review", "material_paragraph_without_citation",
            "重要事実を含む段落に号証引用がありません。",
            index, excerpt,
            "近接段落の引用で足りるか確認し、必要ならピンポイントの号証・頁を付してください。",
        ))

    severity_weight = {"critical": 12, "material": 6, "review": 1}
    score = max(0, 100 - sum(severity_weight[item.severity] for item in findings))
    if any(item.severity == "critical" for item in findings):
        status = "working draft"
    elif score >= 85:
        status = "stable candidate"
    else:
        status = "needs revision"

    evidence_matrix = []
    for index, paragraph in enumerate(paragraphs, 1):
        refs = extract_exhibits(paragraph)
        if refs:
            evidence_matrix.append({
                "paragraph": index,
                "excerpt": short(paragraph, 150),
                "exhibits": refs,
                "indexed": (
                    all(base_id(ref) in known_bases for ref in refs) if evidence else None
                ),
            })

    damage_terms = ("非財産的損害", "精神的苦痛", "休業損害", "逸失利益", "一部請求")
    return {
        "status": status,
        "score": score,
        "paragraph_count": len(paragraphs),
        "dates": [match.group(0).replace(" ", "") for match in DATE_RE.finditer(text)],
        "cited_exhibits": sorted(
            set(cited), key=lambda value: (int(re.search(r"\d+", value).group()), value)
        ),
        "unused_evidence": unused,
        "damage_term_counts": dict(Counter({term: text.count(term) for term in damage_terms})),
        "findings": [asdict(item) for item in findings],
        "evidence_matrix": evidence_matrix,
        "disclaimer": "This deterministic report is drafting triage, not a legal merits decision or legal advice.",
    }


def markdown_report(result: dict, filing: Path) -> str:
    severity_label = {"critical": "Critical", "material": "Material", "review": "Review"}
    lines = [
        "# Filing review report", "",
        f"- Filing: `{filing.name}`",
        f"- Status: **{result['status']}**",
        f"- Readiness score: **{result['score']}/100**",
        f"- Paragraphs: {result['paragraph_count']}",
        f"- Exhibits cited: {', '.join(result['cited_exhibits']) or 'none'}",
        "", "## Findings", "",
    ]
    if not result["findings"]:
        lines.append("No deterministic warnings were found. Manual legal and evidentiary review is still required.")
    for number, finding in enumerate(result["findings"], 1):
        location = f" paragraph {finding['paragraph']}" if finding.get("paragraph") else ""
        lines.extend([
            f"### {number}. {severity_label[finding['severity']]} — {finding['code']}{location}",
            "", finding["message"], "",
        ])
        if finding.get("excerpt"):
            lines.extend([f"> {finding['excerpt']}", ""])
        if finding.get("repair"):
            lines.extend([f"Repair: {finding['repair']}", ""])

    lines.extend([
        "## Evidence citation matrix", "",
        "| Paragraph | Exhibits | Excerpt |", "|---:|---|---|",
    ])
    for row in result["evidence_matrix"]:
        excerpt = row["excerpt"].replace("|", "\\|")
        lines.append(f"| {row['paragraph']} | {', '.join(row['exhibits'])} | {excerpt} |")
    lines.extend(["", "---", "", result["disclaimer"], ""])
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filing", required=True, type=Path, help="TXT, MD, or DOCX filing")
    parser.add_argument("--evidence", type=Path, help="JSON evidence index")
    parser.add_argument("--out", required=True, type=Path, help="Output directory")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when critical findings exist")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    paragraphs = read_filing(args.filing)
    evidence = load_evidence(args.evidence)
    result = analyze(paragraphs, evidence)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "review.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.out / "review.md").write_text(markdown_report(result, args.filing), encoding="utf-8")
    print(f"{result['status']} — {result['score']}/100")
    print(args.out / "review.md")
    if args.strict and any(item["severity"] == "critical" for item in result["findings"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
