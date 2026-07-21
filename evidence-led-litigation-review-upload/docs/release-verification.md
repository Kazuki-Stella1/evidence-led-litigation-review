# Release verification

Verification date: 2026-07-20 JST

Release: `evidence-led-litigation-review` 0.3.1

Verified environment: Linux, CPython 3.12.13

Optional local extraction tools exercised in this environment: Tesseract 5.3.4 with English language data, `pdftotext` 24.02.0, `pdftoppm` 26.05.0, and ImageMagick 6.9.12-98. Japanese Tesseract language data was not installed; the missing-language failure and transcript fallback were tested explicitly.

## Automated results

| Check | Result |
|---|---|
| Python compilation | Passed |
| Unit and integration tests | 23 tests passed |
| Plain text and hash-aware cache reuse | Passed |
| DOCX OOXML extraction | Passed |
| Text-layer PDF extraction | Passed |
| Scanned-PDF OCR fallback | Passed with a fictional English image PDF |
| Common-image OCR | Passed with a fictional English PNG |
| Missing Japanese OCR language handling | Passed; explicit error, no false read claim |
| Reviewed transcript fallback state | Passed; not marked source-verified |
| Diagonal self/opponent SVG generation | Passed structurally and by rendered visual inspection |
| Opponent 乙 citation and inference-gap detection | Passed |
| Location-specific proofreading | Passed; extracted-text line and character range verified |
| Literal/private correction rules | Passed; manifest and external private rule paths verified |
| Exhibit repair boundary | Passed; supported 甲1→甲2 correction and unknown-number no-guess behavior verified |
| Proofreading exports | Passed; Markdown, JSON, and UTF-8 BOM CSV generated |
| Synthetic filing demo | `working draft`, 37/100, 11 findings; `stable candidate`, 100/100, 0 findings |
| Synthetic evidence-workflow demo | 7 items, 7 events, 11 logic findings, 1 proofreading candidate; self and opponent paths verified |
| Synthetic proofreading demo | 1 filing, 7 candidates; exact locations and exports verified |
| Plugin manifest validation | Passed |
| Skill validation | Passed |
| Current-tree privacy scan | Passed |
| All-reachable-Git-history privacy scan | Passed |
| Runtime deny-token scan for known private-case terms | Passed |
| Git whitespace check | Passed |

## Visual inspection

The generated chronology SVG was exported to a 1680×2860 PNG with Inkscape and a temporary Japanese QA font. The rising diagonal, month labels, left evidence-analysis cards, right source cards, side colors, spacing, and card boundaries were visually inspected. The updated architecture SVG was separately rendered at 1200 pixels wide and visually inspected after the proofreading labels were added. The temporary fonts and PNGs are QA artifacts under `/tmp`; they are not part of the public repository or release.

The HTML filter is also covered structurally by the generated `data-side` attributes and fictional demo self-check. A browser remains the intended interactive viewing surface.

## Manual semantic privacy review

- All public samples are invented commercial disputes using abstract labels such as `原告A` and `取引相手B`.
- Dates, amounts, transactions, medical examples, evidence titles, filings, chats, and outputs are fictional.
- No real filing, exhibit, image, audio, address, case number, full name, medical record, transcript, or private manifest is included.
- Known private-case names and identifiers were supplied as runtime deny tokens and were absent.
- The clean public history remains separate from the private development repository.

## Reproduction

```bash
python -m compileall -q scripts tests
python -m unittest discover -s tests -v
python scripts/run_demo.py
python scripts/run_workflow_demo.py
python scripts/run_proofreading_demo.py
python scripts/privacy_scan.py --history
python /path/to/plugin-creator/scripts/validate_plugin.py .
python /path/to/skill-creator/scripts/quick_validate.py skills/revise-litigation-filings
python scripts/build_release.py
```

`scripts/build_release.py` requires a clean commit and writes the plugin ZIP, ready local-marketplace ZIP, and `dist/SHA256SUMS`. Exact final archive hashes are reported with the final commit-to-ZIP handoff; `dist/` is intentionally excluded from Git.

## External submission values not represented by local tests

- public or judge-shared repository URL;
- public YouTube demo URL; and
- `/feedback` Session ID from the primary Codex build thread.
