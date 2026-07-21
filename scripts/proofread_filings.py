#!/usr/bin/env python3
"""Create deterministic, location-specific proofreading reports for filings.

The checker works on the local extracted-text index.  It reports literal legal
misconversions, duplicate input, bracket/punctuation defects, unknown exhibits,
and claim-to-exhibit citation drift.  It does not call a model API and does not
pretend to find every contextual Japanese-language error.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from evidence_model import (
    EXHIBIT_RE,
    EvidenceError,
    exhibit_id,
    load_json,
    normalize_exhibit_text,
    sha256_bytes,
)
from logic_check import claim_evidence_entries, list_strings


BUILTIN_LITERAL_RULES = (
    {
        "wrong": "証拠説書",
        "correct": "証拠説明書",
        "category": "誤変換",
        "reason": "訴訟書面の文書名としては「証拠説明書」が通常の表記です。",
    },
    {
        "wrong": "生合成",
        "correct": "整合性",
        "category": "誤変換",
        "reason": "文書と証拠の一致を表す語は「整合性」です。",
    },
    {
        "wrong": "損害倍賞",
        "correct": "損害賠償",
        "category": "誤変換",
        "reason": "法律用語は「損害賠償」です。",
    },
    {
        "wrong": "逸出利益",
        "correct": "逸失利益",
        "category": "誤変換",
        "reason": "損害項目の法律用語は「逸失利益」です。",
    },
    {
        "wrong": "休業障害",
        "correct": "休業損害",
        "category": "誤変換",
        "reason": "休業による過去の減収を表す損害項目は「休業損害」です。",
    },
    {
        "wrong": "因果間係",
        "correct": "因果関係",
        "category": "誤変換",
        "reason": "法律上の因果のつながりを表す語は「因果関係」です。",
    },
    {
        "wrong": "号証番後",
        "correct": "号証番号",
        "category": "誤変換",
        "reason": "証拠の番号を表す語は「号証番号」です。",
    },
)

PARTICLE_REPEAT_RE = re.compile(
    r"(?P<token>ならびに|並びに|および|または|及び|又は|は|が|を|に|へ|と|で|も|の)(?P=token)"
)
PUNCTUATION_REPEAT_RE = re.compile(r"(?P<token>[。、，．！？])(?P=token)+")
UNIT_REPEAT_RE = re.compile(r"(?P<token>号証|年|月|日|第)(?P=token)")
OPEN_TO_CLOSE = {"(": ")", "（": "）", "[": "]", "［": "］", "{": "}", "｛": "｝", "「": "」", "『": "』", "【": "】"}
CLOSE_TO_OPEN = {close: open_ for open_, close in OPEN_TO_CLOSE.items()}
VALID_SEVERITIES = {"critical", "material", "review", "info"}
VALID_CERTAINTIES = {"confirmed", "high", "review"}


@dataclass
class ProofreadingFinding:
    severity: str
    certainty: str
    code: str
    category: str
    side: str
    filing_id: str
    source_file: str
    extraction_method: str
    line: int
    column_start: int
    column_end: int
    observed: str
    suggestion: str | None
    reason: str
    line_text: str
    claim_id: str | None = None
    evidence_ids: list[str] | None = None
    location_basis: str = "extracted_text"
    finding_id: str | None = None


def item_text(index_path: Path, item: dict) -> str:
    relative = item.get("raw_text_file") or item.get("text_file")
    if not relative:
        return ""
    try:
        return (index_path.parent / str(relative)).read_text(encoding="utf-8")
    except OSError:
        return ""


def normalized_rule(rule: object, *, origin: str) -> dict:
    if not isinstance(rule, dict):
        raise EvidenceError(f"{origin}: each proofreading rule must be an object")
    wrong = str(rule.get("wrong") or "")
    correct = str(rule.get("correct") or "")
    if not wrong or not correct:
        raise EvidenceError(f"{origin}: proofreading rules require wrong and correct text")
    if wrong == correct:
        raise EvidenceError(f"{origin}: wrong and correct text must differ")
    if "\n" in wrong or "\r" in wrong:
        raise EvidenceError(f"{origin}: wrong text must fit on one extracted-text line")
    filing_ids = rule.get("filing_ids", [])
    if isinstance(filing_ids, str):
        filing_ids = [filing_ids]
    if not isinstance(filing_ids, list):
        raise EvidenceError(f"{origin}: filing_ids must be an array")
    severity = str(rule.get("severity") or "review")
    certainty = str(rule.get("certainty") or "high")
    if severity not in VALID_SEVERITIES:
        raise EvidenceError(f"{origin}: unsupported severity: {severity}")
    if certainty not in VALID_CERTAINTIES:
        raise EvidenceError(f"{origin}: unsupported certainty: {certainty}")
    return {
        "wrong": wrong,
        "correct": correct,
        "category": str(rule.get("category") or "表記"),
        "reason": str(rule.get("reason") or "登録された校正規則と一致しました。"),
        "severity": severity,
        "certainty": certainty,
        "filing_ids": [str(value) for value in filing_ids],
    }


def rules_from_config(config: object, *, origin: str) -> tuple[list[dict], set[str]]:
    if config in (None, {}):
        return [], set()
    if not isinstance(config, dict):
        raise EvidenceError(f"{origin}: proofreading configuration must be an object")
    values = config.get("rules", [])
    if not isinstance(values, list):
        raise EvidenceError(f"{origin}: rules must be an array")
    ignore = config.get("ignore_text", [])
    if isinstance(ignore, str):
        ignore = [ignore]
    if not isinstance(ignore, list):
        raise EvidenceError(f"{origin}: ignore_text must be an array")
    return [normalized_rule(value, origin=origin) for value in values], {str(value) for value in ignore}


def load_rules(index: dict, rules_path: Path | None) -> tuple[list[dict], set[str]]:
    builtins = [normalized_rule(rule, origin="built-in") for rule in BUILTIN_LITERAL_RULES]
    manifest_rules, ignored = rules_from_config(index.get("proofreading"), origin="evidence index")
    external_rules: list[dict] = []
    if rules_path:
        external_config = load_json(rules_path)
        external_rules, external_ignored = rules_from_config(external_config, origin=str(rules_path))
        ignored.update(external_ignored)
    return builtins + manifest_rules + external_rules, ignored


def add_literal_findings(
    findings: list[ProofreadingFinding],
    *,
    filing: dict,
    lines: list[str],
    rules: list[dict],
    ignored: set[str],
) -> None:
    filing_id = str(filing["id"])
    common = {
        "side": str(filing.get("side") or "neutral"),
        "filing_id": filing_id,
        "source_file": str(filing.get("source_file") or ""),
        "extraction_method": str(filing.get("extraction_method") or "unknown"),
    }
    for rule in rules:
        if rule["filing_ids"] and filing_id not in rule["filing_ids"]:
            continue
        wrong = rule["wrong"]
        if wrong in ignored:
            continue
        for line_number, line_text in enumerate(lines, 1):
            start = 0
            while True:
                offset = line_text.find(wrong, start)
                if offset < 0:
                    break
                findings.append(
                    ProofreadingFinding(
                        severity=rule["severity"],
                        certainty=rule["certainty"],
                        code="literal_correction",
                        category=rule["category"],
                        line=line_number,
                        column_start=offset + 1,
                        column_end=offset + len(wrong),
                        observed=wrong,
                        suggestion=rule["correct"],
                        reason=rule["reason"],
                        line_text=line_text,
                        **common,
                    )
                )
                start = offset + len(wrong)


def add_pattern_findings(
    findings: list[ProofreadingFinding],
    *,
    filing: dict,
    lines: list[str],
    ignored: set[str],
) -> None:
    common = {
        "side": str(filing.get("side") or "neutral"),
        "filing_id": str(filing["id"]),
        "source_file": str(filing.get("source_file") or ""),
        "extraction_method": str(filing.get("extraction_method") or "unknown"),
    }
    patterns = (
        (PARTICLE_REPEAT_RE, "duplicate_input", "重複入力", "review", "high", "同じ助詞又は接続語が連続しています。"),
        (PUNCTUATION_REPEAT_RE, "duplicate_punctuation", "句読点", "review", "high", "同じ句読点が連続しています。"),
        (UNIT_REPEAT_RE, "duplicate_unit", "重複入力", "review", "high", "年・月・日・第・号証の単位が重複しています。"),
    )
    for line_number, line_text in enumerate(lines, 1):
        for pattern, code, category, severity, certainty, reason in patterns:
            for match in pattern.finditer(line_text):
                observed = match.group(0)
                if observed in ignored:
                    continue
                token = match.group("token")
                findings.append(
                    ProofreadingFinding(
                        severity=severity,
                        certainty=certainty,
                        code=code,
                        category=category,
                        line=line_number,
                        column_start=match.start() + 1,
                        column_end=match.end(),
                        observed=observed,
                        suggestion=token,
                        reason=reason,
                        line_text=line_text,
                        **common,
                    )
                )


def add_bracket_findings(
    findings: list[ProofreadingFinding], *, filing: dict, lines: list[str]
) -> None:
    stack: list[tuple[str, int, int, str]] = []
    common = {
        "side": str(filing.get("side") or "neutral"),
        "filing_id": str(filing["id"]),
        "source_file": str(filing.get("source_file") or ""),
        "extraction_method": str(filing.get("extraction_method") or "unknown"),
    }
    for line_number, line_text in enumerate(lines, 1):
        for column, character in enumerate(line_text, 1):
            if character in OPEN_TO_CLOSE:
                stack.append((character, line_number, column, line_text))
            elif character in CLOSE_TO_OPEN:
                expected_open = CLOSE_TO_OPEN[character]
                if stack and stack[-1][0] == expected_open:
                    stack.pop()
                else:
                    findings.append(
                        ProofreadingFinding(
                            severity="review",
                            certainty="confirmed",
                            code="unmatched_closing_bracket",
                            category="括弧",
                            line=line_number,
                            column_start=column,
                            column_end=column,
                            observed=character,
                            suggestion=None,
                            reason=f"対応する開き括弧「{expected_open}」がありません。括弧の種類と位置を確認してください。",
                            line_text=line_text,
                            **common,
                        )
                    )
    for character, line_number, column, line_text in stack:
        close = OPEN_TO_CLOSE[character]
        findings.append(
            ProofreadingFinding(
                severity="review",
                certainty="confirmed",
                code="unclosed_bracket",
                category="括弧",
                line=line_number,
                column_start=column,
                column_end=column,
                observed=character,
                suggestion=f"対応位置に{close}を追加",
                reason=f"開き括弧「{character}」に対応する閉じ括弧「{close}」がありません。",
                line_text=line_text,
                **common,
            )
        )


def citation_matches(line_text: str) -> list[tuple[str, int, int, str]]:
    normalized = normalize_exhibit_text(line_text)
    result: list[tuple[str, int, int, str]] = []
    for match in EXHIBIT_RE.finditer(normalized):
        normalized_id = exhibit_id(match.group("prefix"), match.group("base"), match.group("branch"))
        result.append((normalized_id, match.start(), match.end(), line_text[match.start() : match.end()]))
    return result


def strict_claims_for_line(claims: list[dict], filing_id: str, line_text: str) -> list[dict]:
    matches: list[dict] = []
    for claim in claims:
        if not isinstance(claim, dict) or str(claim.get("filing_id") or "") != filing_id:
            continue
        if claim.get("citation_check") != "same_line":
            continue
        terms = list_strings(claim.get("match_terms"))
        statement = str(claim.get("statement") or "").strip()
        if terms and all(term in line_text for term in terms):
            matches.append(claim)
        elif statement and statement in line_text:
            matches.append(claim)
    return matches


def expected_ids(claim: dict) -> list[str]:
    return [entry["id"] for entry in claim_evidence_entries(claim)]


def add_exhibit_findings(
    findings: list[ProofreadingFinding],
    *,
    filing: dict,
    lines: list[str],
    claims: list[dict],
    known_evidence_ids: set[str],
) -> None:
    filing_id = str(filing["id"])
    common = {
        "side": str(filing.get("side") or "neutral"),
        "filing_id": filing_id,
        "source_file": str(filing.get("source_file") or ""),
        "extraction_method": str(filing.get("extraction_method") or "unknown"),
    }
    for line_number, line_text in enumerate(lines, 1):
        citations = citation_matches(line_text)
        strict_claims = strict_claims_for_line(claims, filing_id, line_text)
        expected_for_line = list(dict.fromkeys(eid for claim in strict_claims for eid in expected_ids(claim)))
        claim_ids = [str(claim.get("id")) for claim in strict_claims if claim.get("id")]

        for actual_id, start, end, observed in citations:
            if actual_id in known_evidence_ids:
                continue
            suggestion = None
            if len(expected_for_line) == 1 and expected_for_line[0] in known_evidence_ids:
                suggestion = expected_for_line[0]
            findings.append(
                ProofreadingFinding(
                    severity="material",
                    certainty="confirmed",
                    code="unknown_exhibit_reference",
                    category="号証",
                    line=line_number,
                    column_start=start + 1,
                    column_end=end,
                    observed=observed,
                    suggestion=suggestion,
                    reason=(
                        f"{actual_id}は証拠台帳にありません。"
                        + (f"この行に対応付けられた号証は{suggestion}です。" if suggestion else "正しい号証は台帳と原本で確認してください。")
                    ),
                    line_text=line_text,
                    claim_id=claim_ids[0] if len(claim_ids) == 1 else None,
                    evidence_ids=[actual_id] + ([suggestion] if suggestion else []),
                    **common,
                )
            )

        for claim in strict_claims:
            expected = expected_ids(claim)
            if not expected:
                continue
            actual = [value[0] for value in citations]
            missing = [value for value in expected if value not in actual]
            if not missing:
                continue
            claim_id = str(claim.get("id") or "") or None
            wrong_known = [value for value in actual if value in known_evidence_ids and value not in expected]
            if len(expected) == 1 and len(wrong_known) == 1:
                wrong_id = wrong_known[0]
                match = next(value for value in citations if value[0] == wrong_id)
                findings.append(
                    ProofreadingFinding(
                        severity="material",
                        certainty="high",
                        code="wrong_exhibit_reference",
                        category="号証",
                        line=line_number,
                        column_start=match[1] + 1,
                        column_end=match[2],
                        observed=match[3],
                        suggestion=expected[0],
                        reason=f"主張{claim_id or ''}の明示的な対応号証は{expected[0]}ですが、この行は{wrong_id}を引用しています。",
                        line_text=line_text,
                        claim_id=claim_id,
                        evidence_ids=[wrong_id, expected[0]],
                        **common,
                    )
                )
            elif wrong_known:
                first = next(value for value in citations if value[0] == wrong_known[0])
                findings.append(
                    ProofreadingFinding(
                        severity="material",
                        certainty="high",
                        code="mapped_exhibit_missing_on_line",
                        category="号証",
                        line=line_number,
                        column_start=first[1] + 1,
                        column_end=max(value[2] for value in citations),
                        observed="、".join(actual),
                        suggestion="、".join(missing),
                        reason=f"主張{claim_id or ''}の同一行対応号証{', '.join(missing)}が記載されていません。",
                        line_text=line_text,
                        claim_id=claim_id,
                        evidence_ids=list(dict.fromkeys(actual + expected)),
                        **common,
                    )
                )
            elif not actual:
                findings.append(
                    ProofreadingFinding(
                        severity="material",
                        certainty="high",
                        code="missing_exhibit_reference",
                        category="号証",
                        line=line_number,
                        column_start=len(line_text) + 1,
                        column_end=len(line_text) + 1,
                        observed="[号証記載なし]",
                        suggestion="、".join(expected),
                        reason=f"主張{claim_id or ''}には同一行での号証確認が指定されています。",
                        line_text=line_text,
                        claim_id=claim_id,
                        evidence_ids=expected,
                        **common,
                    )
                )


def deduplicate_and_number(findings: list[ProofreadingFinding]) -> list[ProofreadingFinding]:
    severity_order = {"critical": 0, "material": 1, "review": 2, "info": 3}
    unique: dict[tuple, ProofreadingFinding] = {}
    for finding in findings:
        key = (
            finding.filing_id,
            finding.line,
            finding.column_start,
            finding.code,
            finding.observed,
            finding.suggestion,
            finding.claim_id,
        )
        unique.setdefault(key, finding)
    ordered = sorted(
        unique.values(),
        key=lambda item: (
            item.filing_id,
            item.line,
            item.column_start,
            severity_order.get(item.severity, 9),
            item.code,
        ),
    )
    for number, finding in enumerate(ordered, 1):
        finding.finding_id = f"PR{number:03d}"
    return ordered


def analyze_proofreading(index_path: Path, *, rules_path: Path | None = None) -> dict:
    index = load_json(index_path)
    items = index.get("items", [])
    if not isinstance(items, list):
        raise EvidenceError("evidence-index items must be an array")
    claims = index.get("claims", [])
    if not isinstance(claims, list):
        raise EvidenceError("evidence-index claims must be an array")
    rules, ignored = load_rules(index, rules_path)
    filings = [item for item in items if isinstance(item, dict) and item.get("kind") == "filing" and item.get("id")]
    known_evidence_ids = {
        str(item.get("id"))
        for item in items
        if isinstance(item, dict) and item.get("kind") != "filing" and item.get("id")
    }
    findings: list[ProofreadingFinding] = []
    filing_hashes: dict[str, str] = {}
    for filing in filings:
        text = item_text(index_path, filing)
        filing_id = str(filing["id"])
        filing_hashes[filing_id] = sha256_bytes(text.encode("utf-8"))
        lines = text.splitlines()
        add_literal_findings(findings, filing=filing, lines=lines, rules=rules, ignored=ignored)
        add_pattern_findings(findings, filing=filing, lines=lines, ignored=ignored)
        add_bracket_findings(findings, filing=filing, lines=lines)
        add_exhibit_findings(
            findings,
            filing=filing,
            lines=lines,
            claims=claims,
            known_evidence_ids=known_evidence_ids,
        )
    ordered = deduplicate_and_number(findings)
    severity_counts = Counter(item.severity for item in ordered)
    category_counts = Counter(item.category for item in ordered)
    side_counts = Counter(item.side for item in ordered)
    return {
        "schema_version": 1,
        "case_id": index.get("case_id"),
        "filing_count": len(filings),
        "finding_count": len(ordered),
        "severity_counts": dict(sorted(severity_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "side_counts": dict(sorted(side_counts.items())),
        "filing_text_sha256": filing_hashes,
        "findings": [asdict(item) for item in ordered],
        "disclaimer": (
            "This deterministic report lists configured and structural proofreading candidates. "
            "Line and column numbers refer to extracted text, which may differ from Word/PDF visual lines. "
            "It does not find every typo, decide legal correctness, or replace original-source review."
        ),
    }


def markdown_escape(value: object) -> str:
    return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ")


def inline_code(value: object) -> str:
    text = str(value if value is not None else "—").replace("`", "ˋ").replace("\n", " ")
    return f"`{text}`"


def render_markdown(report: dict) -> str:
    lines = [
        "# 訴訟書面 校正候補一覧",
        "",
        f"- Case ID: `{report.get('case_id') or '未記載'}`",
        f"- 対象書面数: {report['filing_count']}",
        f"- 校正候補数: {report['finding_count']}",
        f"- 重大度別: `{json.dumps(report['severity_counts'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "> 行番号・文字位置は抽出テキスト基準です。DOCX・PDFの画面上の行や頁とは一致しない場合があります。最終修正前に原本と証拠台帳を確認してください。",
        "",
        "| ID | 重大度 | 確度 | 書面 | 場所 | 種別 | 該当 | 修正候補 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in report["findings"]:
        location = f"{item['line']}行 {item['column_start']}–{item['column_end']}字"
        lines.append(
            "| {id} | {severity} | {certainty} | {filing} | {location} | {category} | {observed} | {suggestion} |".format(
                id=markdown_escape(item["finding_id"]),
                severity=markdown_escape(item["severity"]),
                certainty=markdown_escape(item["certainty"]),
                filing=markdown_escape(item["filing_id"]),
                location=markdown_escape(location),
                category=markdown_escape(item["category"]),
                observed=markdown_escape(item["observed"]),
                suggestion=markdown_escape(item.get("suggestion")),
            )
        )
    if not report["findings"]:
        lines.append("| — | — | — | — | — | — | 校正候補なし | — |")
    lines.extend(["", "## 修正指示", ""])
    for item in report["findings"]:
        lines.extend(
            [
                f"### {item['finding_id']}｜{item['filing_id']}｜抽出テキスト{item['line']}行",
                "",
                f"- 元ファイル: {inline_code(item.get('source_file') or '未記載')}",
                f"- 位置: `{item['line']}行 {item['column_start']}–{item['column_end']}字`",
                f"- 該当行: {inline_code(item['line_text'])}",
                f"- 検出箇所: {inline_code(item['observed'])}",
                f"- 修正候補: {inline_code(item.get('suggestion') or '台帳・原本を確認')}",
                f"- 理由: {item['reason']}",
                f"- 確度: `{item['certainty']}`",
                f"- 関連主張: `{item.get('claim_id') or 'なし'}`",
                f"- 関連号証: `{', '.join(item.get('evidence_ids') or []) or 'なし'}`",
                "",
            ]
        )
    lines.extend(
        [
            "## 判定範囲",
            "",
            "- `confirmed`: 台帳不存在、括弧不整合等、入力上の状態を機械的に確認できるもの。",
            "- `high`: 登録辞書、重複規則又は明示された同一行の主張・号証対応に基づく強い候補。",
            "- この一覧は全ての誤字、文脈上の誤変換、法的正確性又は号証内容の正しさを保証しません。",
            "- 修正候補が一意でない号証は推測せず、台帳・証拠説明書・原本確認へ戻します。",
            "",
        ]
    )
    return "\n".join(lines)


CSV_FIELDS = (
    "finding_id",
    "severity",
    "certainty",
    "category",
    "side",
    "filing_id",
    "source_file",
    "line",
    "column_start",
    "column_end",
    "observed",
    "suggestion",
    "reason",
    "claim_id",
    "evidence_ids",
    "line_text",
)


def render_csv(report: dict) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for finding in report["findings"]:
        row = dict(finding)
        row["evidence_ids"] = ",".join(finding.get("evidence_ids") or [])
        writer.writerow(row)
    return stream.getvalue()


def write_report(index_path: Path, out_dir: Path, *, rules_path: Path | None = None) -> dict:
    report = analyze_proofreading(index_path, rules_path=rules_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "proofreading-review.json"
    markdown_path = out_dir / "proofreading-review.md"
    csv_path = out_dir / "proofreading-review.csv"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    csv_path.write_text(render_csv(report), encoding="utf-8-sig")
    report["json_path"] = json_path
    report["markdown_path"] = markdown_path
    report["csv_path"] = csv_path
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True, help="intake/evidence-index.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rules", type=Path, help="optional local JSON correction glossary")
    parser.add_argument("--strict", action="store_true", help="return 1 when material/critical findings remain")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = write_report(args.index, args.out, rules_path=args.rules)
    except EvidenceError as exc:
        print(f"Proofreading failed: {exc}")
        return 2
    print(
        f"Proofreading passed: {report['filing_count']} filing(s), "
        f"{report['finding_count']} candidate(s)."
    )
    print(report["markdown_path"])
    print(report["csv_path"])
    if args.strict and any(item["severity"] in {"critical", "material"} for item in report["findings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
