import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from privacy_scan import scan_text  # noqa: E402


class PrivacyScanTests(unittest.TestCase):
    def test_detects_common_identifiers(self):
        findings = scan_text(
            "fixture",
            "sample.txt",
            "連絡先 03-1234-5678\n令和7年（ワ）第123号",  # privacy-scan-allow
            [],
        )
        self.assertEqual(
            {item.code for item in findings},
            {"japanese_phone", "court_case_number"},
        )

    def test_detects_runtime_private_token_without_echoing_it(self):
        findings = scan_text("fixture", "sample.txt", "PRIVATE PARTY", ["PRIVATE PARTY"])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "private_deny_token")

    def test_synthetic_text_is_clean(self):
        self.assertEqual(
            scan_text("fixture", "sample.txt", "原告Aと架空の取引相手B", []),
            [],
        )


if __name__ == "__main__":
    unittest.main()
