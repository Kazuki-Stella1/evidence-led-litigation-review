#!/usr/bin/env python3
"""Build cached evidence text dossiers from heterogeneous local source files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_model import (
    EvidenceError,
    annotation_lines,
    extract_source,
    load_json,
    manifest_source,
    normalize_text,
    parse_event_date,
    safe_filename,
    sha256_bytes,
    sha256_file,
)


REQUIRED_ANNOTATION_KEYS = ("summary", "facts", "proves", "causation", "contradictions", "legal_evaluation")
VALID_SIDES = {"self", "opponent", "neutral"}
VALID_KINDS = {"evidence", "filing", "record", "reference"}
VALID_IMPORTANCE = {"low", "normal", "high", "critical"}


def validate_manifest(manifest: dict) -> None:
    if not manifest.get("case_id"):
        raise EvidenceError("manifest.case_id is required")
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        raise EvidenceError("manifest.items must be a non-empty array")
    seen: set[str] = set()
    for position, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise EvidenceError(f"items[{position}] must be an object")
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            raise EvidenceError(f"items[{position}].id is required")
        if item_id in seen:
            raise EvidenceError(f"duplicate item id: {item_id}")
        seen.add(item_id)
        if item.get("side", "neutral") not in VALID_SIDES:
            raise EvidenceError(f"{item_id}: side must be self, opponent, or neutral")
        if item.get("kind", "evidence") not in VALID_KINDS:
            raise EvidenceError(f"{item_id}: unsupported kind")
        if item.get("importance", "normal") not in VALID_IMPORTANCE:
            raise EvidenceError(f"{item_id}: unsupported importance")
        if not item.get("source") and not item.get("transcript"):
            raise EvidenceError(f"{item_id}: source or transcript is required")
        parse_event_date(item.get("event_date"))


def load_previous_index(out_dir: Path) -> tuple[dict, dict[str, dict]]:
    path = out_dir / "evidence-index.json"
    if not path.exists():
        return {}, {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, {}
    items = value.get("items", []) if isinstance(value, dict) else []
    return value, {str(item.get("id")): item for item in items if isinstance(item, dict)}


def read_cached_text(out_dir: Path, previous: dict) -> str | None:
    relative = previous.get("raw_text_file")
    if not relative:
        return None
    path = out_dir / relative
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def extract_item(
    manifest_path: Path,
    item: dict,
    *,
    mode: str,
    out_dir: Path,
    previous: dict | None,
    default_ocr_language: str,
) -> dict:
    item_id = str(item["id"])
    source = manifest_source(manifest_path, item)
    transcript = manifest_source(manifest_path, item, "transcript")
    source_hash = sha256_file(source) if source and source.exists() else None
    transcript_hash = sha256_file(transcript) if transcript and transcript.exists() else None
    warnings: list[str] = []
    method = ""
    page_count: int | None = None
    selected_text = ""
    source_text_hash: str | None = None
    source_was_reextracted = False
    transcript_matches_source: bool | None = None
    cached = False

    if (
        mode == "fast"
        and previous
        and previous.get("source_sha256") == source_hash
        and previous.get("transcript_sha256") == transcript_hash
    ):
        cached_text = read_cached_text(out_dir, previous)
        if cached_text is not None:
            selected_text = cached_text
            previous_method = str(previous.get("extraction_method") or "unknown")
            while previous_method.startswith("cache:"):
                previous_method = previous_method.removeprefix("cache:")
            method = f"cache:{previous_method}"
            page_count = previous.get("page_count")
            source_text_hash = previous.get("source_text_sha256")
            transcript_matches_source = previous.get("transcript_matches_source")
            warnings.extend(previous.get("extraction_warnings", []))
            cached = True

    ocr_language = str(item.get("ocr_language") or default_ocr_language)
    transcript_text = ""
    if transcript and transcript.exists():
        transcript_text = normalize_text(transcript.read_text(encoding="utf-8"))

    if not cached:
        if mode == "fast" and transcript_text:
            selected_text = transcript_text
            method = "reviewed_transcript_sidecar"
            warnings.append("Fast mode used the transcript sidecar without re-reading the original source.")
        else:
            if source and source.exists():
                try:
                    extracted = extract_source(source, ocr_language=ocr_language)
                    source_was_reextracted = True
                    selected_text = extracted.text
                    method = extracted.method
                    page_count = extracted.page_count
                    warnings.extend(extracted.warnings or [])
                    source_text_hash = sha256_bytes(selected_text.encode("utf-8"))
                    if transcript_text:
                        transcript_matches_source = normalize_text(transcript_text) == normalize_text(selected_text)
                        if not transcript_matches_source:
                            warnings.append(
                                "Reviewed transcript and current source extraction differ; inspect the original source."
                            )
                except EvidenceError as exc:
                    if transcript_text:
                        selected_text = transcript_text
                        method = "reviewed_transcript_fallback"
                        warnings.append(str(exc))
                        warnings.append("Source extraction failed; the reviewed transcript was used as a fallback.")
                    else:
                        raise
            elif transcript_text:
                selected_text = transcript_text
                method = "reviewed_transcript_source_missing"
                warnings.append("Original source was not available; precision verification is impossible.")
            else:
                raise EvidenceError(f"{item_id}: neither source nor transcript is readable")

    selected_text = normalize_text(selected_text)
    if not selected_text.strip():
        raise EvidenceError(f"{item_id}: extracted text is empty")

    source_checked = bool(item.get("source_checked", False))
    importance = item.get("importance", "normal")
    if mode == "fast":
        precision_status = "fast_cache_source_hash_matched" if cached else "fast_text_only"
    elif source_checked and source_was_reextracted and transcript_matches_source is not False:
        precision_status = "source_verified"
    elif source_was_reextracted:
        precision_status = "reextracted_pending_source_review"
    else:
        precision_status = "transcript_only_pending_source_review"

    annotations = item.get("annotations", {})
    if not isinstance(annotations, dict):
        raise EvidenceError(f"{item_id}: annotations must be an object")
    missing_annotations = [
        key for key in REQUIRED_ANNOTATION_KEYS if not annotation_lines(annotations, key)
    ]
    if missing_annotations:
        warnings.append("Annotation fields still require review: " + ", ".join(missing_annotations))
    warnings = list(dict.fromkeys(warnings))

    return {
        "id": item_id,
        "title": str(item.get("title") or item_id),
        "side": item.get("side", "neutral"),
        "kind": item.get("kind", "evidence"),
        "event_date": item.get("event_date"),
        "source_pages": item.get("source_pages", []),
        "importance": importance,
        "source_file": str(item.get("source") or ""),
        "transcript_file": str(item.get("transcript") or ""),
        "source_sha256": source_hash,
        "transcript_sha256": transcript_hash,
        "text_sha256": sha256_bytes(selected_text.encode("utf-8")),
        "source_text_sha256": source_text_hash,
        "extraction_method": method,
        "extraction_mode": mode,
        "page_count": page_count,
        "source_checked": source_checked,
        "source_was_reextracted": source_was_reextracted,
        "transcript_matches_source": transcript_matches_source,
        "precision_status": precision_status,
        "original_required_for_final": importance in {"high", "critical"},
        "annotation_status": "complete" if not missing_annotations else "incomplete",
        "missing_annotations": missing_annotations,
        "annotations": annotations,
        "extraction_warnings": warnings,
        "_selected_text": selected_text,
    }


def render_list(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- 未記載"


def dossier_text(case_id: str, record: dict) -> str:
    annotations = record["annotations"]
    sections = [
        ("内容要約", annotation_lines(annotations, "summary")),
        ("事実の詳細", annotation_lines(annotations, "facts")),
        ("立証対象・立証趣旨", annotation_lines(annotations, "proves")),
        ("因果関係", annotation_lines(annotations, "causation")),
        ("矛盾点・反対資料", annotation_lines(annotations, "contradictions")),
        ("推論", annotation_lines(annotations, "inferences")),
        ("法的評価", annotation_lines(annotations, "legal_evaluation")),
        ("原本確認メモ", annotation_lines(annotations, "verification_notes")),
    ]
    lines = [
        f"# {record['id']}｜{record['title']}",
        "",
        f"- Case ID: `{case_id}`",
        f"- Side: `{record['side']}`",
        f"- Kind: `{record['kind']}`",
        f"- 証拠・出来事の日付: `{record.get('event_date') or '未記載'}`",
        f"- 元ファイル: `{record.get('source_file') or '未記載'}`",
        f"- 元ファイルSHA-256: `{record.get('source_sha256') or '未確認'}`",
        f"- 対象頁: `{record.get('source_pages') or '未記載'}`",
        f"- 抽出方法: `{record['extraction_method']}`",
        f"- 読取モード: `{record['extraction_mode']}`",
        f"- 重要度: `{record['importance']}`",
        f"- 原本確認済み: `{str(record['source_checked']).lower()}`",
        f"- 精度状態: `{record['precision_status']}`",
        f"- 注釈状態: `{record['annotation_status']}`",
        "",
        "## 抽出・転記テキスト",
        "",
        record["_selected_text"].strip(),
        "",
    ]
    for title, values in sections:
        lines.extend([f"## {title}", "", render_list(values), ""])
    lines.extend(["## 抽出警告", "", render_list(record["extraction_warnings"]), ""])
    return "\n".join(lines).rstrip() + "\n"


def index_markdown(index: dict) -> str:
    lines = [
        "# 証拠テキスト台帳",
        "",
        f"- Case ID: `{index['case_id']}`",
        f"- Case title: {index.get('case_title') or '未記載'}",
        f"- Mode: `{index['mode']}`",
        f"- Items: {len(index['items'])}",
        "",
        "| ID | Side | Kind | 日時 | 重要度 | 抽出 | 精度状態 | テキスト |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in index["items"]:
        lines.append(
            "| {id} | {side} | {kind} | {date} | {importance} | {method} | {status} | [{file}]({file}) |".format(
                id=item["id"],
                side=item["side"],
                kind=item["kind"],
                date=item.get("event_date") or "—",
                importance=item["importance"],
                method=item["extraction_method"],
                status=item["precision_status"],
                file=item["text_file"],
            )
        )
    lines.extend(
        [
            "",
            "> 高速モードのテキストは確認用キャッシュです。重要な引用、日時、金額、署名、画像内容及び争点は原本確認へ戻してください。",
            "",
        ]
    )
    return "\n".join(lines)


def build_index(
    manifest_path: Path,
    out_dir: Path,
    *,
    mode: str = "fast",
    default_ocr_language: str = "jpn+eng",
) -> dict:
    manifest = load_json(manifest_path)
    validate_manifest(manifest)
    out_dir.mkdir(parents=True, exist_ok=True)
    text_dir = out_dir / "text"
    text_dir.mkdir(exist_ok=True)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    _, previous_items = load_previous_index(out_dir)

    records: list[dict] = []
    for position, item in enumerate(manifest["items"], 1):
        record = extract_item(
            manifest_path,
            item,
            mode=mode,
            out_dir=out_dir,
            previous=previous_items.get(str(item["id"])),
            default_ocr_language=default_ocr_language,
        )
        filename = f"{position:03d}_{safe_filename(record['id'])}.txt"
        relative = Path("text") / filename
        raw_relative = Path("raw") / filename
        (out_dir / raw_relative).write_text(record["_selected_text"], encoding="utf-8")
        (out_dir / relative).write_text(
            dossier_text(str(manifest["case_id"]), record), encoding="utf-8"
        )
        record["text_file"] = relative.as_posix()
        record["raw_text_file"] = raw_relative.as_posix()
        record.pop("_selected_text")
        records.append(record)

    index = {
        "schema_version": 1,
        "case_id": manifest["case_id"],
        "case_title": manifest.get("case_title", ""),
        "mode": mode,
        "items": records,
        "claims": manifest.get("claims", []),
        "contradictions": manifest.get("contradictions", []),
        "proofreading": manifest.get("proofreading", {}),
        "disclaimer": (
            "Extracted text is a navigation cache, not a substitute for the original source. "
            "Annotations and legal evaluations require record-sensitive human or Codex review."
        ),
    }
    (out_dir / "evidence-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "evidence-index.md").write_text(index_markdown(index), encoding="utf-8")
    return index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=("fast", "precise"), default="fast")
    parser.add_argument("--ocr-lang", default="jpn+eng")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        index = build_index(
            args.manifest,
            args.out,
            mode=args.mode,
            default_ocr_language=args.ocr_lang,
        )
    except EvidenceError as exc:
        print(f"Evidence intake failed: {exc}")
        return 2
    print(f"Indexed {len(index['items'])} item(s) in {args.mode} mode.")
    print(args.out / "evidence-index.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
