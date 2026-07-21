# Devpost submission copy

## Submission fields

- **Track:** Work and Productivity
- **Project name:** Evidence-Led Litigation Review
- **Tagline:** Turn mixed evidence and repeated Japanese legal-drafting revisions into a verifiable Codex workflow.
- **Code repository URL:** `[REQUIRED EXTERNAL VALUE — paste the clean public repository URL]`
- **Public YouTube URL:** `[REQUIRED EXTERNAL VALUE — paste the public video URL]`
- **Primary `/feedback` Codex Session ID:** `[REQUIRED EXTERNAL VALUE — obtain from the primary build thread]`

## Inspiration

People revising the same legal filing many times can improve the prose while accidentally weakening the record: exhibit citations drift, facts blur into inference, damage periods overlap, and emotional labels displace observable conduct. We wanted the model to remember a disciplined improvement process rather than rewrite one document once.

## What it does

Evidence-Led Litigation Review is a local-first Codex plugin for Japanese litigation filings. It converts supported local PDFs, images, DOCX files, and text records into reusable evidence dossiers; draws a two-sided diagonal chronology; lists deterministic inconsistency candidates between filings, normalized claims, and exhibits; and exports a location-specific proofreading repair list. Its skill then leads Codex through seven fixed passes: record inventory, issue chain, evidence-claim matrix, causation and damages, strongest-opponent review, expression, and filing-day verification.

The basic deterministic checker reads TXT, Markdown, or DOCX without third-party packages or network calls. The expanded source workflow uses optional local Poppler and Tesseract tools for PDFs and images, and never calls a model API. It separates fast cached-text navigation from precise original-source review. It flags unresolved exhibits, unknown 甲 or 乙 citations, direct claims resting on inferential support, date and causal-order gaps, contract-duty errors, missing lawful-advocacy limits, loaded terms, overlapping damage periods, and unclear partial-claim allocation. Its proofreading stage lists registered misconversions, duplicate input, punctuation and bracket defects, and supported exhibit-number repairs with extracted-text line and character positions. It produces human-readable text and Markdown plus machine-readable JSON, CSV, and SVG.

The public repository includes only an invented commercial dispute using `原告A` and `取引相手B`. No real party, filing, medical record, address, case number, or exhibit is included.

## The two-layer design

The local tools handle repeatable extraction states and structural signals. GPT-5.6 in Codex handles the judgment that rules cannot: what an exhibit directly proves, where inference begins, how competing causal explanations affect the claim, whether loss periods overlap, what the strongest lawful response is, and which wording remains faithful to the record.

The score is drafting triage, never a win probability or legal-merits decision. The repository demo tests the deterministic layer; installing the bundled Codex plugin demonstrates the complete GPT-5.6 reasoning workflow.

## How we built it with Codex and GPT-5.6

Codex accelerated the entire repository workflow: plugin structure, Python implementation, DOCX and PDF handling, image OCR integration tests, cache design, map generation, location-specific proofreading, test design, synthetic fixtures, documentation, privacy review, release verification, and repeated repair loops.

GPT-5.6 was used in the primary Codex build thread to make the core product decisions and encode the review method. It separated direct evidence from inference, constructed the chronology-to-remedy issue chain, tested causation and alternative explanations, separated non-property damage from past and future property loss, steelmanned lawful-advocacy and proof objections, and converted those judgments into a reusable skill. It also identified that a merely anonymized public fact pattern could still be re-identifying, leading us to replace it with a deliberately unrelated fictional dispute.

## Challenges

The hardest design problem was avoiding two unsafe extremes: a generic grammar checker and a system that pretends to decide legal merit. We separated deterministic drafting checks from GPT-5.6's record-sensitive reasoning and required the model to say which files and pages it actually read.

Claims involving opposing counsel created another difficult boundary. Ordinary advocacy cannot be equated with wrongdoing. The workflow therefore tests the objectively unsupported premise, knowledge or easy verifiability, correction opportunity, conduct after correction, and the strongest lawful explanation before recommending language.

## Accomplishments

- A working installable Codex plugin and fixed-pass litigation-review skill
- Local evidence dossiers for text, DOCX, PDF, screenshots, and photographs, with an explicit original-source gate
- A filterable rising diagonal chronology for self, opponent, and neutral sources
- Two-sided 甲・乙 filing/evidence inconsistency candidates
- Line-and-column proofreading lists in Markdown, JSON, and spreadsheet-ready CSV
- Dependency-free core filing analysis and optional local Poppler/Tesseract extraction
- Machine-readable evidence citation matrix and human-readable reports
- Explicit separation of deterministic checks from GPT-5.6 reasoning
- Cross-platform one-command demo and automated tests
- Ready local-marketplace release ZIP for judge testing without rebuilding
- Current-tree and Git-history privacy scan
- Entirely fictional public sample with before/after output

## What we learned

The most useful AI behavior was not stronger rhetoric. It was disciplined separation: observable fact from inference, one medical event from another, non-property loss from property loss, past loss from future loss, and the user's theory from the strongest opposing explanation.

## What's next

- Legacy `.doc` conversion assistance
- Region-level OCR and pinpoint image coordinates
- Word redlines with reasons for each accepted or rejected revision
- A damage-calculation workbook with explicit non-overlapping periods
- Additional jurisdiction-specific rule packs

## Built with

Codex, GPT-5.6, Codex plugins and skills, Python standard library, OOXML, Poppler, Tesseract, JSON, Markdown, SVG.

## Judge path

```bash
python scripts/run_demo.py
python scripts/run_workflow_demo.py
python scripts/run_proofreading_demo.py
python -m unittest discover -s tests -v
```

Full installation and test instructions: `docs/judge-quickstart.md`.
