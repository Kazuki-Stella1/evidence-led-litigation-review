# Work created during Build Week

## Pre-existing material

- The general problem: repeated revision of Japanese litigation filings can create exhibit drift, unclear inference, overlapping loss periods, and unstable wording.
- A private, non-public working method for reviewing legal documents.

No private filing, exhibit, medical record, image, audio, party identity, or pre-existing private source file is included in this repository.

## New public artifact created during the submission period

- `.codex-plugin/plugin.json` and the installable `revise-litigation-filings` skill
- deterministic TXT, Markdown, and DOCX analyzer
- JSON evidence-index comparison and evidence citation matrix
- deterministic first-pass anonymizer
- cross-platform one-command demo
- public-release current-tree and Git-history scanner
- deterministic plugin and marketplace release ZIP builder
- deliberately fictional before/after case and evidence index
- deliberately fictional two-sided mixed-evidence workflow fixture
- deterministic extracted-text line-and-column proofreading and exhibit-repair reports
- deliberately fictional proofreading fixture with Markdown, JSON, and CSV outputs
- automated standard-library test suite
- architecture, privacy, judge, demo, Devpost, and release documentation

## Meaningful extensions in the completion pass

- made Codex and GPT-5.6 roles explicit and testable;
- separated deterministic output from model judgment in the skill and README;
- replaced a fact pattern that was too close to a private workflow with an unrelated fictional commercial dispute;
- added a portable judge path for macOS, Linux, and Windows;
- added a ready local-marketplace package so the plugin can be tested without rebuilding;
- added privacy scanning for current files and all reachable Git history;
- added an English voiceover script and exact external-submission placeholders;
- added reproducible release verification and archive hashing;
- added cached evidence dossiers, an original-source verification gate, a diagonal chronology, and two-sided filing/evidence logic candidates;
- added local PDF and image extraction paths with explicit OCR-language and transcript-fallback states; and
- added integration tests covering text, DOCX, PDF, image OCR, cache reuse, mapping, and opponent evidence;
- added literal and private correction rules, duplicate-input, punctuation, bracket, unknown-exhibit, and explicitly mapped exhibit-drift checks; and
- added tests covering exact positions, no-guess exhibit handling, private rule files, and all three proofreading export formats.

Commit timestamps and descriptions are retained in Git and summarized in `docs/build-log.md`.
