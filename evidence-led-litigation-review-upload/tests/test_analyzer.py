import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_filing import analyze, extract_exhibits, load_evidence, read_filing  # noqa: E402


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.evidence = load_evidence(ROOT / "sample/input/evidence.json")

    def test_draft_finds_core_problems(self):
        paragraphs = read_filing(ROOT / "sample/input/complaint_draft.txt")
        result = analyze(paragraphs, self.evidence)
        codes = {finding["code"] for finding in result["findings"]}
        self.assertEqual(result["status"], "working draft")
        self.assertIn("unresolved_exhibit", codes)
        self.assertIn("contract_duty_to_adverse_party", codes)
        self.assertIn("duplicate_damage_phrase", codes)
        self.assertIn("damage_period_overlap", codes)

    def test_stable_sample_has_no_critical_findings(self):
        paragraphs = read_filing(ROOT / "sample/fixed/complaint_stable.txt")
        result = analyze(paragraphs, self.evidence)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["score"], 100)

    def test_json_shape_is_serializable(self):
        result = analyze(["請求の趣旨", "請求の原因", "損害及び因果関係（甲1）"], self.evidence)
        json.dumps(result, ensure_ascii=False)

    def test_exhibit_range_is_expanded(self):
        self.assertEqual(
            extract_exhibits("支払及び住所関係（甲8ないし甲11）"),
            ["甲8", "甲9", "甲10", "甲11"],
        )

    def test_docx_is_read_without_third_party_packages(self):
        document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>請求の原因</w:t></w:r></w:p></w:body>
</w:document>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", document_xml)
            self.assertEqual(read_filing(path), ["請求の原因"])

    def test_partial_claim_without_allocation_is_flagged(self):
        result = analyze([
            "請求の趣旨",
            "請求の原因",
            "損害及び因果関係",
            "損害の一部として請求する。",
        ], [])
        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("partial_claim_allocation", codes)


if __name__ == "__main__":
    unittest.main()
