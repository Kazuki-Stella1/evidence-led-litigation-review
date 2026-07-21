# Evidence source workflow

## Purpose and boundary

This workflow reduces repeated opening of PDFs, screenshots, photographs, DOCX files, and text records. It creates a searchable local dossier for everyday review, then requires a separate return to the original for accuracy-critical use.

`source → local text extraction or reviewed transcript → evidence dossier → diagonal chronology → logic candidates + location-specific proofreading → Codex and human review`

The Python tools are local and deterministic. They do not call an OpenAI API. Extraction is not authentication, an annotation is not proof, and a consistency report is not a legal conclusion.

## Supported sources

| Source | Local path | Optional tool |
|---|---|---|
| TXT, Markdown, CSV, TSV, JSON | direct UTF-8 read | none |
| DOCX | direct OOXML read | none |
| text-layer PDF | `pdftotext -layout` | Poppler |
| scanned PDF | page rendering, then OCR | `pdftoppm`, Tesseract, language data |
| PNG, JPEG, TIFF, WebP, BMP, GIF | OCR | Tesseract and language data |
| unsupported or unreliable source | reviewed UTF-8 transcript sidecar | original still required for final verification |

For Japanese OCR, install the Tesseract `jpn` language data and request `jpn+eng`. If the requested language is missing, intake fails explicitly unless a reviewed transcript sidecar is available. It does not silently pretend that Japanese text was read.

## Two review modes

| Mode | Use | Behavior | Permitted conclusion |
|---|---|---|---|
| `fast` | ordinary navigation and repeated comparison | reuses text when source and transcript SHA-256 values match | cached text is available; original may still be required |
| `precise` | important quotation, date, amount, page, signature, image, or dispute | re-extracts the current original and compares a transcript when supplied | `source_verified` only when re-extraction occurred and the manifest records a completed source check |

The program cannot independently know that a human opened the correct page. `source_checked: true` is a review record supplied by the operator, not an automated authenticity finding.

## Manifest

Use one item for every filing, evidence source, record, or reference. The public fixture at `sample/workflow/input/manifest.json` is complete and entirely fictional.

```json
{
  "case_id": "PRIVATE-LOCAL-ID",
  "case_title": "local-only title",
  "items": [
    {
      "id": "甲1",
      "title": "source title",
      "side": "self",
      "kind": "evidence",
      "source": "sources/exhibit-1.pdf",
      "transcript": "transcripts/exhibit-1.txt",
      "event_date": "2026-01-10",
      "source_pages": [2],
      "importance": "high",
      "source_checked": false,
      "annotations": {
        "summary": ["content summary"],
        "facts": ["what is directly shown"],
        "proves": ["proof purpose"],
        "causation": ["limited causal relevance"],
        "contradictions": ["conflicting source or assertion"],
        "inferences": ["step beyond direct proof"],
        "legal_evaluation": ["separate legal evaluation"],
        "verification_notes": ["page and original-check notes"]
      }
    }
  ],
  "claims": [],
  "contradictions": [],
  "proofreading": {
    "rules": [
      {
        "wrong": "case-specific mistype",
        "correct": "approved spelling",
        "reason": "private case glossary",
        "filing_ids": ["訴状案"]
      }
    ],
    "ignore_text": []
  }
}
```

Allowed sides are `self`, `opponent`, and `neutral`. Allowed importance levels are `low`, `normal`, `high`, and `critical`. Dates use `YYYY-MM` or `YYYY-MM-DD` and should represent the event being mapped, not an automatically inferred document date.

Set `citation_check: "same_line"` on a normalized claim only when its mapped exhibits must appear on the same extracted-text line. That explicit instruction lets the proofreader propose a replacement exhibit number. Without a unique supported mapping, it reports the citation for source review and does not guess. Keep real names and case-specific correction rules in a private manifest or private `--rules` file.

## Commands

Run the complete fictional demo:

```bash
python scripts/run_workflow_demo.py
python scripts/run_proofreading_demo.py
```

Run intake, map, logic review, and proofreading together:

```bash
python scripts/evidence_workflow.py \
  --manifest <manifest.json> \
  --out <output-directory> \
  --mode fast \
  --ocr-lang jpn+eng
```

Run only the proofreading stage or add a private glossary:

```bash
python scripts/proofread_filings.py \
  --index <output-directory>/intake/evidence-index.json \
  --out <output-directory>/proofreading \
  --rules <private-rules.json>
```

Re-run high and critical material after source review:

```bash
python scripts/evidence_workflow.py \
  --manifest <manifest.json> \
  --out <output-directory> \
  --mode precise \
  --ocr-lang jpn+eng
```

## Outputs

- `intake/evidence-index.json`: machine-readable source hashes, methods, precision state, annotations, claims, and contradictions.
- `intake/evidence-index.md`: compact table for ordinary navigation.
- `intake/text/*.txt`: one human-readable dossier per source.
- `intake/raw/*.txt`: extracted text cache used for hashing and later analysis.
- `map/evidence-map.html`: filterable map for all, self, opponent, or neutral sources.
- `map/evidence-map.svg`: portable static map.
- `logic/logic-review.json` and `.md`: deterministic inconsistency candidates grouped by side.
- `proofreading/proofreading-review.md`: readable repair list with document, extracted-text line, character range, observed text, correction candidate, reason, certainty, claim, and exhibit.
- `proofreading/proofreading-review.json`: machine-readable version of the same findings with input text hashes.
- `proofreading/proofreading-review.csv`: UTF-8 BOM list intended for spreadsheet handoff.

The rising diagonal is divided by year and month. Left cards contain facts, proof purpose, causation, contradictions, inference, and legal evaluation. Right cards contain side, exhibit or filing ID, event date, source title, pages, and precision state.

## Deterministic logic candidates

The checker covers both 甲 and 乙 exhibits, including full-width digits, branches, and ranges. It can list:

- filing citations absent from the index;
- claims mapped to missing evidence;
- mapped evidence not cited by the filing;
- direct claims resting on inferential support;
- expected proof-purpose terms missing from evidence annotations;
- explicit event-date mismatches and reversed causal ordering;
- unresolved contradiction records;
- important sources that have not passed the precise source gate; and
- evidence that is indexed but not mapped.

It cannot find every semantic inconsistency, authenticate a source, decide admissibility or sufficiency, or establish causation. GPT-5.6 in Codex and a human reviewer use the candidate list to inspect the actual record and decide what should be narrowed, supported, disputed, or rewritten.

## Deterministic proofreading candidates

The proofreading stage covers built-in high-confidence legal misconversions, a private literal correction glossary, duplicate particles or punctuation, repeated date/number units, unmatched brackets, citations absent from the evidence index, and exhibit drift where a claim explicitly requires its mapped exhibit on the same line.

`confirmed` means an input state such as an unclosed bracket or an index-absent exhibit was mechanically observed. `high` means a strong rule-based candidate. Neither label establishes the legal correctness of the sentence. The checker cannot find every contextual conversion error or grammatical defect, and extracted-text line numbers may differ from Word/PDF display lines.

## Privacy rule

Real manifests, originals, transcripts, dossiers, correction glossaries, and outputs belong in a private case directory. Do not copy them into this public repository. The tracked `sample/workflow/` and `sample/proofreading/` trees contain only deliberately fictional commercial examples. Redaction alone is not treated as sufficient where a distinctive fact pattern could permit re-identification.
