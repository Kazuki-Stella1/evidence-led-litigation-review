import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evidence_ingest import build_index  # noqa: E402
from evidence_map import render_svg  # noqa: E402
from evidence_model import (  # noqa: E402
    EvidenceError,
    extract_evidence_ids,
    extract_source,
    require_ocr_language,
    tesseract_languages,
)
from logic_check import analyze_logic  # noqa: E402


def write_manifest(directory: Path, item: dict) -> Path:
    path = directory / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "case_id": "SYNTHETIC-TEST-001",
                "case_title": "完全架空テスト",
                "items": [item],
                "claims": [],
                "contradictions": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def complete_annotations() -> dict:
    return {
        "summary": ["架空資料の要約。"],
        "facts": ["架空の事実。"],
        "proves": ["架空の立証趣旨。"],
        "causation": ["架空の因果関係。"],
        "contradictions": ["架空の矛盾候補。"],
        "inferences": ["架空の推論。"],
        "legal_evaluation": ["架空の法的評価。"],
    }


def write_minimal_pdf(path: Path, text: str) -> None:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 18 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    payload = bytearray(b"%PDF-1.4\n%synthetic\n")
    offsets = [0]
    for number, body in enumerate(objects, 1):
        offsets.append(len(payload))
        payload.extend(f"{number} 0 obj\n".encode("ascii"))
        payload.extend(body)
        payload.extend(b"\nendobj\n")
    xref = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")  # privacy-scan-allow: required PDF xref row
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode(
            "ascii"
        )
    )
    path.write_bytes(payload)


class EvidenceCitationTests(unittest.TestCase):
    def test_extracts_both_sides_ranges_branches_and_fullwidth_digits(self):
        self.assertEqual(
            extract_evidence_ids("甲第１号証、乙2ないし乙4及び甲３－２を参照する。"),
            ["甲1", "乙2", "乙3", "乙4", "甲3の2"],
        )


class EvidenceIntakeTests(unittest.TestCase):
    def test_fast_cache_and_precise_original_gate(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            (directory / "source.txt").write_text("Synthetic source text\n", encoding="utf-8")
            manifest = write_manifest(
                directory,
                {
                    "id": "甲1",
                    "title": "架空資料",
                    "side": "self",
                    "kind": "evidence",
                    "source": "source.txt",
                    "event_date": "2026-01-10",
                    "source_pages": [1],
                    "importance": "critical",
                    "source_checked": True,
                    "annotations": complete_annotations(),
                },
            )
            out = directory / "out"
            first = build_index(manifest, out, mode="fast", default_ocr_language="eng")
            self.assertEqual(first["items"][0]["precision_status"], "fast_text_only")
            second = build_index(manifest, out, mode="fast", default_ocr_language="eng")
            self.assertEqual(second["items"][0]["extraction_method"], "cache:plain:txt")
            third = build_index(manifest, out, mode="fast", default_ocr_language="eng")
            self.assertEqual(third["items"][0]["extraction_method"], "cache:plain:txt")
            warnings = third["items"][0]["extraction_warnings"]
            self.assertEqual(len(warnings), len(set(warnings)))
            precise = build_index(manifest, out, mode="precise", default_ocr_language="eng")
            self.assertEqual(precise["items"][0]["precision_status"], "source_verified")
            dossier = (out / precise["items"][0]["text_file"]).read_text(encoding="utf-8")
            for heading in ("事実の詳細", "立証対象・立証趣旨", "因果関係", "法的評価"):
                self.assertIn(heading, dossier)

    def test_reviewed_transcript_is_explicit_fallback_not_source_verification(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            (directory / "source.bin").write_bytes(b"unsupported")
            (directory / "source.transcript.txt").write_text("Reviewed fictional transcript", encoding="utf-8")
            manifest = write_manifest(
                directory,
                {
                    "id": "乙1",
                    "title": "架空画像転記",
                    "side": "opponent",
                    "kind": "evidence",
                    "source": "source.bin",
                    "transcript": "source.transcript.txt",
                    "event_date": "2026-02-01",
                    "importance": "high",
                    "source_checked": False,
                    "annotations": complete_annotations(),
                },
            )
            index = build_index(manifest, directory / "out", mode="precise", default_ocr_language="eng")
            item = index["items"][0]
            self.assertEqual(item["extraction_method"], "reviewed_transcript_fallback")
            self.assertEqual(item["precision_status"], "transcript_only_pending_source_review")
            self.assertFalse(item["source_was_reextracted"])

    def test_docx_text_is_extracted_locally(self):
        document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>Synthetic DOCX evidence</w:t></w:r></w:p></w:body>
</w:document>"""
        with tempfile.TemporaryDirectory() as raw_directory:
            path = Path(raw_directory) / "source.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", document_xml)
            result = extract_source(path)
            self.assertEqual(result.method, "ooxml:docx")
            self.assertIn("Synthetic DOCX evidence", result.text)

    @unittest.skipUnless(shutil.which("pdftotext"), "Poppler pdftotext unavailable")
    def test_text_pdf_is_extracted_locally(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            path = Path(raw_directory) / "synthetic.pdf"
            write_minimal_pdf(path, "SYNTHETIC PDF EVIDENCE 2026")
            result = extract_source(path, ocr_language="eng")
            self.assertEqual(result.method, "pdftotext:layout")
            self.assertIn("SYNTHETIC PDF EVIDENCE 2026", result.text)

    def test_missing_ocr_language_fails_without_claiming_source_was_read(self):
        with mock.patch("evidence_model.tesseract_languages", return_value={"eng"}):
            with self.assertRaisesRegex(EvidenceError, "Missing Tesseract language data: jpn"):
                require_ocr_language("jpn+eng")

    @unittest.skipUnless(shutil.which("convert") and shutil.which("tesseract"), "local OCR tools unavailable")
    def test_fictional_image_is_ocr_read_in_english(self):
        if "eng" not in tesseract_languages():
            self.skipTest("English Tesseract language data unavailable")
        with tempfile.TemporaryDirectory() as raw_directory:
            path = Path(raw_directory) / "fictional.png"
            subprocess.run(
                [
                    shutil.which("convert"),
                    "-size",
                    "1400x240",
                    "xc:white",
                    "-fill",
                    "black",
                    "-font",
                    "DejaVu-Sans",
                    "-pointsize",
                    "64",
                    "-gravity",
                    "center",
                    "-annotate",
                    "+0+0",
                    "SYNTHETIC EVIDENCE 2026",
                    str(path),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            result = extract_source(path, ocr_language="eng")
            self.assertEqual(result.method, "tesseract:eng")
            self.assertIn("SYNTHETIC", result.text.upper())

    @unittest.skipUnless(
        shutil.which("convert")
        and shutil.which("pdftoppm")
        and shutil.which("tesseract"),
        "local scanned-PDF tools unavailable",
    )
    def test_fictional_scanned_pdf_uses_ocr_fallback(self):
        if "eng" not in tesseract_languages():
            self.skipTest("English Tesseract language data unavailable")
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            image = directory / "scan.png"
            pdf = directory / "scan.pdf"
            subprocess.run(
                [
                    shutil.which("convert"),
                    "-size",
                    "1400x240",
                    "xc:white",
                    "-fill",
                    "black",
                    "-font",
                    "DejaVu-Sans",
                    "-pointsize",
                    "64",
                    "-gravity",
                    "center",
                    "-annotate",
                    "+0+0",
                    "SYNTHETIC SCANNED PDF 2026",
                    str(image),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            subprocess.run(
                [shutil.which("convert"), str(image), str(pdf)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            result = extract_source(pdf, ocr_language="eng")
            self.assertEqual(result.method, "pdftoppm+tesseract:eng")
            self.assertIn("SYNTHETIC SCANNED PDF", result.text.upper())
            self.assertTrue(any("OCR fallback" in warning for warning in result.warnings or []))


class EvidenceMapAndLogicTests(unittest.TestCase):
    def test_diagonal_map_contains_both_sides_and_portable_svg_text(self):
        index = {
            "case_id": "SYNTHETIC-MAP-001",
            "case_title": "完全架空マップ",
            "items": [
                {
                    "id": "甲1",
                    "title": "架空の自分側証拠",
                    "side": "self",
                    "event_date": "2026-01-10",
                    "source_pages": [1],
                    "precision_status": "source_verified",
                    "annotations": complete_annotations(),
                },
                {
                    "id": "乙1",
                    "title": "架空の相手方証拠",
                    "side": "opponent",
                    "event_date": "2026-02-15",
                    "source_pages": [2],
                    "precision_status": "fast_text_only",
                    "annotations": complete_annotations(),
                },
            ],
        }
        svg = render_svg(index)
        self.assertIn('data-side="self"', svg)
        self.assertIn('data-side="opponent"', svg)
        self.assertIn("2026年01月", svg)
        self.assertIn("立証趣旨", svg)
        self.assertIn("因果関係", svg)
        self.assertNotIn("foreignObject", svg)

    def test_fixture_detects_unknown_opponent_exhibit_and_inference_gap(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            out = Path(raw_directory) / "intake"
            build_index(
                ROOT / "sample/workflow/input/manifest.json",
                out,
                mode="fast",
                default_ocr_language="eng",
            )
            result = analyze_logic(out / "evidence-index.json")
            codes = {(item["side"], item["code"]) for item in result["findings"]}
            self.assertIn(("opponent", "filing_cites_unknown_evidence"), codes)
            self.assertIn(("opponent", "claim_maps_unknown_evidence"), codes)
            self.assertIn(("opponent", "direct_claim_uses_inferential_support"), codes)
            self.assertNotIn(
                ("opponent", "mapped_evidence_not_cited"),
                {
                    (item["side"], item["code"])
                    for item in result["findings"]
                    if item.get("evidence_ids") == ["乙1"]
                },
            )


if __name__ == "__main__":
    unittest.main()
