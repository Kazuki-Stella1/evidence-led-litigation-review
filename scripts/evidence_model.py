#!/usr/bin/env python3
"""Shared evidence extraction and normalization helpers.

The module is deliberately local-first.  It never calls a model API.  Text and
DOCX are handled with the Python standard library.  PDF text extraction uses
Poppler when available, and image/scanned-PDF OCR uses Tesseract when available.
Codex-reviewed transcripts can be supplied as sidecars when local OCR is not
available or is not reliable enough for the source language.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.etree import ElementTree


TEXT_SUFFIXES = {".txt", ".md", ".csv", ".tsv", ".json"}
IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}

FULLWIDTH_TRANSLATION = str.maketrans(
    "０１２３４５６７８９－−―",
    "0123456789---",  # privacy-scan-allow: digit translation table
)
EXHIBIT_RE = re.compile(
    r"(?P<prefix>[甲乙])\s*(?:第\s*)?(?P<base>\d+)"
    r"(?:\s*(?:の|-)\s*(?P<branch>\d+))?\s*(?:号証(?:拠)?)?"
)
EXHIBIT_RANGE_RE = re.compile(
    r"(?P<prefix>[甲乙])\s*(?:第\s*)?(?P<start>\d+)\s*(?:号証(?:拠)?)?"
    r"\s*(?:ないし|乃至|から|～|〜|~)\s*"
    r"(?P<end_prefix>[甲乙])?\s*(?:第\s*)?(?P<end>\d+)\s*(?:号証(?:拠)?)?"
)


class EvidenceError(RuntimeError):
    """Raised when a source cannot be extracted without overstating coverage."""


@dataclass
class ExtractedText:
    text: str
    method: str
    page_count: int | None = None
    warnings: list[str] | None = None

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "method": self.method,
            "page_count": self.page_count,
            "warnings": list(self.warnings or []),
        }


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u3000", " ")
    lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in text.splitlines()]
    compact: list[str] = []
    blank = False
    for line in lines:
        if line:
            compact.append(line)
            blank = False
        elif compact and not blank:
            compact.append("")
            blank = True
    return "\n".join(compact).strip() + ("\n" if compact else "")


def safe_filename(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "_", value.strip())
    value = re.sub(r"\s+", "_", value)
    return value[:100] or "evidence"


def normalize_exhibit_text(text: str) -> str:
    """Normalize digits/dashes without changing substantive filing text."""

    return text.translate(FULLWIDTH_TRANSLATION)


def exhibit_id(prefix: str, base: str | int, branch: str | int | None = None) -> str:
    normalized = f"{prefix}{int(base)}"
    return normalized + (f"の{int(branch)}" if branch is not None else "")


def extract_evidence_ids(text: str) -> list[str]:
    """Extract both plaintiff-side 甲 and opponent-side 乙 exhibit citations.

    Supported forms include ``甲1``, ``乙第2号証``, ``甲3の2`` and
    ``乙1ないし乙4``.  The result is ordered by first appearance and de-duplicated.
    """

    normalized = normalize_exhibit_text(text)
    located: list[tuple[int, str]] = []
    for match in EXHIBIT_RANGE_RE.finditer(normalized):
        prefix = match.group("prefix")
        end_prefix = match.group("end_prefix") or prefix
        start = int(match.group("start"))
        end = int(match.group("end"))
        if prefix == end_prefix and start <= end and end - start <= 100:
            located.extend((match.start(), exhibit_id(prefix, number)) for number in range(start, end + 1))
    for match in EXHIBIT_RE.finditer(normalized):
        located.append(
            (
                match.start(),
                exhibit_id(match.group("prefix"), match.group("base"), match.group("branch")),
            )
        )
    located.sort(key=lambda value: value[0])
    return list(dict.fromkeys(value for _, value in located))


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        try:
            payload = archive.read("word/document.xml")
        except KeyError as exc:
            raise EvidenceError(f"DOCX lacks word/document.xml: {path}") from exc
    root = ElementTree.fromstring(payload)
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for paragraph in root.iter(namespace + "p"):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == namespace + "t" and node.text:
                parts.append(node.text)
            elif node.tag == namespace + "tab":
                parts.append("\t")
            elif node.tag in {namespace + "br", namespace + "cr"}:
                parts.append("\n")
        value = "".join(parts).strip()
        if value:
            paragraphs.append(value)
    return normalize_text("\n\n".join(paragraphs))


def run_checked(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def tesseract_languages() -> set[str]:
    executable = shutil.which("tesseract")
    if not executable:
        return set()
    result = run_checked([executable, "--list-langs"])
    if result.returncode:
        return set()
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not line.startswith("List of available languages")
    }


def require_ocr_language(requested: str) -> None:
    available = tesseract_languages()
    missing = [item for item in requested.split("+") if item and item not in available]
    if missing:
        raise EvidenceError(
            "Missing Tesseract language data: "
            + ", ".join(missing)
            + ". Supply a reviewed transcript sidecar or install the language data."
        )


def ocr_image(path: Path, language: str) -> ExtractedText:
    executable = shutil.which("tesseract")
    if not executable:
        raise EvidenceError("Tesseract is not installed; supply a reviewed transcript sidecar.")
    require_ocr_language(language)
    result = run_checked([executable, str(path), "stdout", "-l", language, "--psm", "6"])
    if result.returncode:
        raise EvidenceError(f"Tesseract failed for {path.name}: {result.stderr.strip()}")
    text = normalize_text(result.stdout)
    if not text.strip():
        raise EvidenceError(f"Tesseract returned no text for {path.name}")
    return ExtractedText(text=text, method=f"tesseract:{language}", page_count=1, warnings=[])


def pdf_page_count(path: Path) -> int | None:
    executable = shutil.which("pdfinfo")
    if not executable:
        return None
    result = run_checked([executable, str(path)])
    if result.returncode:
        return None
    match = re.search(r"^Pages:\s*(\d+)\s*$", result.stdout, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def ocr_scanned_pdf(path: Path, language: str) -> ExtractedText:
    converter = shutil.which("pdftoppm")
    if not converter:
        raise EvidenceError("pdftoppm is not installed; supply a reviewed transcript sidecar.")
    require_ocr_language(language)
    pages: list[str] = []
    warnings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="evidence-pdf-") as directory:
        prefix = Path(directory) / "page"
        result = run_checked([converter, "-png", "-r", "220", str(path), str(prefix)])
        if result.returncode:
            raise EvidenceError(f"pdftoppm failed for {path.name}: {result.stderr.strip()}")
        images = sorted(Path(directory).glob("page-*.png"))
        if not images:
            raise EvidenceError(f"No PDF pages were rendered for {path.name}")
        for number, image in enumerate(images, 1):
            extracted = ocr_image(image, language)
            pages.append(f"[Page {number}]\n{extracted.text.strip()}")
            warnings.extend(extracted.warnings or [])
    return ExtractedText(
        text=normalize_text("\n\n".join(pages)),
        method=f"pdftoppm+tesseract:{language}",
        page_count=len(pages),
        warnings=warnings,
    )


def extract_pdf(path: Path, language: str) -> ExtractedText:
    executable = shutil.which("pdftotext")
    warnings: list[str] = []
    if executable:
        result = run_checked([executable, "-layout", str(path), "-"])
        text = normalize_text(result.stdout) if not result.returncode else ""
        if len(re.sub(r"\s+", "", text)) >= 20:
            return ExtractedText(
                text=text,
                method="pdftotext:layout",
                page_count=pdf_page_count(path),
                warnings=warnings,
            )
        warnings.append("PDF text layer was empty or too short; OCR fallback was used.")
    extracted = ocr_scanned_pdf(path, language)
    extracted.warnings = warnings + list(extracted.warnings or [])
    return extracted


def extract_source(path: Path, *, ocr_language: str = "jpn+eng") -> ExtractedText:
    if not path.exists():
        raise EvidenceError(f"Source file does not exist: {path}")
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8-sig")
        return ExtractedText(normalize_text(text), f"plain:{suffix.lstrip('.')}", 1, [])
    if suffix == ".docx":
        return ExtractedText(read_docx(path), "ooxml:docx", None, [])
    if suffix == ".pdf":
        return extract_pdf(path, ocr_language)
    if suffix in IMAGE_SUFFIXES:
        return ocr_image(path, ocr_language)
    raise EvidenceError(
        f"Unsupported source type {suffix or '[none]'} for {path.name}; "
        "use a reviewed UTF-8 transcript sidecar."
    )


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"Could not read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"JSON root must be an object: {path}")
    return value


def parse_event_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        if re.fullmatch(r"\d{4}-\d{2}", value):
            return date.fromisoformat(value + "-01")
        return date.fromisoformat(value)
    except ValueError as exc:
        raise EvidenceError(f"Invalid event_date {value!r}; use YYYY-MM or YYYY-MM-DD") from exc


def annotation_lines(annotations: dict, key: str) -> list[str]:
    value = annotations.get(key, [])
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                result.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("text") or item.get("description")
                if isinstance(text, str) and text.strip():
                    result.append(text.strip())
        return result
    return []


def manifest_source(manifest_path: Path, item: dict, field: str = "source") -> Path | None:
    value = item.get(field)
    if not value:
        return None
    path = Path(str(value))
    return path if path.is_absolute() else manifest_path.parent / path
