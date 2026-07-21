# English demo voiceover and shot list

Target duration: 2 minutes 30 seconds to 2 minutes 45 seconds.  
Hard limit: 3 minutes.

## 0:00–0:17 — The problem

**Screen:** project title, then `sample/workflow/input/manifest.json`.

**Voiceover:**

“Repeated legal revision hides work. Evidence arrives as PDFs, screenshots, photographs, and documents. Files are reopened, exhibit numbers drift, facts blur into inference, causal steps disappear, and opponent evidence is reviewed inconsistently.”

## 0:17–0:39 — Two layers and two source gates

**Screen:** architecture diagram, `README.md`, then the skill.

**Voiceover:**

“Evidence-Led Litigation Review separates two layers. Deterministic Python tools create local dossiers, maps, consistency candidates, and location-specific proofreading. GPT-5.6 in Codex distinguishes direct proof from inference, tests causation and damages, steelmans the strongest response, and explains revisions. Cached text is for speed; important details return to the source.”

## 0:39–1:02 — Run the evidence workflow

**Screen:** terminal.

```bash
python scripts/run_workflow_demo.py
```

**Voiceover:**

“The demo is a completely fictional two-sided dispute. One command creates seven dossiers, a rising chronology, logic findings, and a proofreading list covering both 甲 and 乙 exhibits. Python uses no model API. Optional PDF and image OCR remains local.”

## 1:02–1:22 — Inspect the map and opponent review

**Screen:** `sample/workflow/output/map/evidence-map.html`, then `logic-review.md`.

**Voiceover:**

“The map pairs exhibit IDs, dates, pages, and verification states with facts, proof purpose, causation, contradictions, inference, and legal evaluation. Filters isolate either side. The logic report catches a missing 乙3 and an opponent's direct claim resting only on inferential support. These are review candidates, not legal conclusions.”

## 1:22–1:44 — Inspect exact proofreading repairs

**Screen:** terminal, then `sample/proofreading/output/proofreading/proofreading-review.md`.

```bash
python scripts/run_proofreading_demo.py
```

**Voiceover:**

“The proofreading demo finds seven repair candidates with the filing, extracted-text line, character range, correction, reason, and certainty. It catches a duplicate particle, three misconversions, a missing bracket, an unknown exhibit, and an explicitly mapped 甲1-to-甲2 repair, then exports Markdown, JSON, and spreadsheet-ready CSV.”

## 1:44–1:59 — Preserve the before-and-after gate

**Screen:** terminal, then the stable report.

```bash
python scripts/run_demo.py
```

**Voiceover:**

“The original demo moves from thirty-seven with eleven warnings to one hundred with none. Neither number predicts who wins. It only shows whether that deterministic rule set still sees drafting risks.”

## 1:59–2:27 — Codex and GPT-5.6 contribution

**Screen:** `SKILL.md`, README contribution section, tests, and build log.

**Voiceover:**

“Codex accelerated the plugin structure, extraction and proofreading code, document handling, OCR tests, fictional fixtures, maps, privacy checks, documentation, repair, and release validation. GPT-5.6 shaped the reasoning workflow: direct proof versus inference, chronology through damage, separate causes and medical events, non-overlapping loss periods, strongest objections, record-faithful expression, and the judgment that anonymization alone may not prevent re-identification.”

## 2:27–2:45 — Close

**Screen:** all tests passing, repository layout, then project title.

**Voiceover:**

“The result supports faster daily review without pretending that extracted text replaces the source. We did not build a machine that decides who wins. We built a workflow that makes every important claim easier to verify, challenge, and improve.”

## Recording gate

- Keep the final cut at or below 2:50 to preserve margin.
- Show real output from both commands; do not use a mock screen.
- Open only the fictional `sample/` tree and public documentation.
- Say both “Codex” and “GPT-5.6” and keep their roles separate.
- Do not claim that OCR authenticates evidence or that the Python tools call GPT-5.6.
- Do not show private chats, files, notifications, account details, or real case material.
