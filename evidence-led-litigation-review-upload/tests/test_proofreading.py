import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evidence_ingest import build_index  # noqa: E402
from proofread_filings import analyze_proofreading, write_report  # noqa: E402


class ProofreadingFixtureTests(unittest.TestCase):
    def test_fictional_fixture_reports_exact_locations_and_exhibit_repair(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            out = Path(raw_directory) / "intake"
            build_index(
                ROOT / "sample/proofreading/input/manifest.json",
                out,
                mode="fast",
                default_ocr_language="eng",
            )
            report = analyze_proofreading(out / "evidence-index.json")
            self.assertEqual(report["finding_count"], 7)
            by_code = {}
            for finding in report["findings"]:
                by_code.setdefault(finding["code"], []).append(finding)
            self.assertEqual(by_code["duplicate_input"][0]["line"], 3)
            self.assertEqual(by_code["duplicate_input"][0]["column_start"], 28)
            wrong = by_code["wrong_exhibit_reference"][0]
            self.assertEqual((wrong["observed"], wrong["suggestion"]), ("甲1", "甲2"))
            self.assertEqual((wrong["line"], wrong["column_start"], wrong["column_end"]), (4, 26, 27))
            unknown = by_code["unknown_exhibit_reference"][0]
            self.assertIsNone(unknown["suggestion"])
            self.assertIn("台帳と原本", unknown["reason"])

    def test_markdown_json_and_excel_friendly_csv_are_written(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            intake = directory / "intake"
            build_index(
                ROOT / "sample/proofreading/input/manifest.json",
                intake,
                mode="fast",
                default_ocr_language="eng",
            )
            report = write_report(intake / "evidence-index.json", directory / "report")
            self.assertIn("3行 28–29字", report["markdown_path"].read_text(encoding="utf-8"))
            self.assertEqual(
                json.loads(report["json_path"].read_text(encoding="utf-8"))["finding_count"],
                7,
            )
            self.assertTrue(report["csv_path"].read_bytes().startswith(b"\xef\xbb\xbf"))


class ProofreadingRuleTests(unittest.TestCase):
    def test_manifest_correction_glossary_is_scoped_and_reusable(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            (directory / "filing.txt").write_text("架空の固有誤変換を確認する。\n", encoding="utf-8")
            manifest = {
                "case_id": "SYNTHETIC-RULE-001",
                "items": [
                    {
                        "id": "準備書面案",
                        "side": "self",
                        "kind": "filing",
                        "source": "filing.txt",
                        "importance": "normal",
                        "source_checked": True,
                        "annotations": {},
                    }
                ],
                "claims": [],
                "contradictions": [],
                "proofreading": {
                    "rules": [
                        {
                            "wrong": "固有誤変換",
                            "correct": "固有の正表記",
                            "reason": "完全架空の事件別用語集。",
                            "filing_ids": ["準備書面案"],
                        }
                    ]
                },
            }
            manifest_path = directory / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            out = directory / "intake"
            build_index(manifest_path, out, mode="fast", default_ocr_language="eng")
            report = analyze_proofreading(out / "evidence-index.json")
            self.assertEqual(report["finding_count"], 1)
            self.assertEqual(report["findings"][0]["suggestion"], "固有の正表記")

    def test_external_rule_file_can_be_applied_without_changing_manifest(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            (directory / "filing.txt").write_text("完全架空の外部誤記。\n", encoding="utf-8")
            manifest = {
                "case_id": "SYNTHETIC-RULE-002",
                "items": [
                    {
                        "id": "訴状案",
                        "side": "self",
                        "kind": "filing",
                        "source": "filing.txt",
                        "importance": "normal",
                        "source_checked": True,
                        "annotations": {},
                    }
                ],
                "claims": [],
                "contradictions": [],
            }
            manifest_path = directory / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            rules_path = directory / "rules.json"
            rules_path.write_text(
                json.dumps(
                    {"rules": [{"wrong": "外部誤記", "correct": "外部正表記"}]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            out = directory / "intake"
            build_index(manifest_path, out, mode="fast", default_ocr_language="eng")
            report = analyze_proofreading(out / "evidence-index.json", rules_path=rules_path)
            self.assertEqual(report["finding_count"], 1)
            self.assertEqual(report["findings"][0]["suggestion"], "外部正表記")


if __name__ == "__main__":
    unittest.main()
