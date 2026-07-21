---
name: revise-litigation-filings
description: Create local evidence dossiers and maps, then repeatedly improve Japanese complaints, briefs, evidence explanations, petitions, and other litigation filings by checking source evidence, organizing issues, testing causation and anticipated defenses, and revising expression without overstating the record. Use for PDF or image evidence intake, 証拠マッピング, 訴状, 準備書面, 主張書面, 証拠説明書, 上申書, 申立書, or a final filing review.
---

# Evidence-led review of Japanese litigation filings

## Start with the record

1. Identify the filing type, court or recipient, procedural stage, requested relief, source version, and available exhibits.
2. State which files and pages were actually read. Treat missing, illegible, truncated, or image-only material as unverified.
3. Preserve the user's theory and objective while separating facts, reasonable inferences, disputed allegations, and legal evaluation.
4. Verify current statutes, court rules, fees, and precedent from primary sources when accuracy matters.

## Run the local checker first

When the record contains mixed PDF, DOCX, screenshot, photograph, or text sources, first create the local evidence cache described in `docs/evidence-workflow.md`:

```bash
python scripts/evidence_workflow.py --manifest <manifest.json> --out <output-dir> --mode fast --ocr-lang jpn+eng
```

- Use the generated dossier for routine navigation and comparison.
- For every high or critical source, return to the original and run the precise path before relying on an exact quotation, date, amount, signature, page, or image detail.
- Treat `reviewed_transcript_*` and `fast_text_only` as navigation states, not original verification.
- Never infer that an unread image or unavailable OCR language was successfully reviewed.
- Keep private manifests, original sources, and generated dossiers outside a public repository.

The same manifest covers both sides: mark each item and normalized claim as `self`, `opponent`, or `neutral`. Review 甲 and 乙 citations with the same source and inference standards.

The complete workflow also writes a location-specific proofreading list. To rerun only that stage:

```bash
python scripts/proofread_filings.py --index <output-dir>/intake/evidence-index.json --out <output-dir>/proofreading
```

- Treat its line and column numbers as extracted-text locations. They may not equal visible Word or PDF lines.
- Apply literal corrections and duplicate-input warnings only after checking the sentence.
- Give a corrected exhibit number only when the evidence index and an explicitly configured `citation_check: same_line` mapping support it.
- If the report says the correct exhibit is indeterminate, return to the evidence index, evidence explanation, and original; do not guess.
- Use an optional private JSON glossary for case-specific names and recurring conversions. Never add real-case terms to the public repository.

For the smaller text, Markdown, or DOCX filing-only check, run:

```bash
python scripts/analyze_filing.py --filing <path> --evidence <evidence-index.json> --out <output-dir>
```

Use its report as triage, not as a substitute for reading the filing or exhibits. Resolve critical placeholders and exhibit mismatches before prose editing.

## Keep the two layers separate

- The local Python checker is deterministic. It identifies repeatable structural signals and produces the same report for the same input.
- GPT-5.6 in Codex is the reasoning layer. It reads the available record, distinguishes direct proof from inference, tests causation and damages, steelmans the strongest response, and explains proposed wording.
- Never present the checker's readiness score as a probability of success or a legal-merits conclusion.
- Never claim that GPT-5.6 reviewed a file or page that was not actually available and readable in the current task.

## Review in fixed passes

### Pass 1: Evidence inventory

- Start from the cached dossier for speed, but open the source whenever the item's precision state or importance requires it.
- Record dates, actors, acts or omissions, quotations, amounts, exhibit numbers, and page locations.
- Check both directions: every essential allegation needs support, and every material exhibit needs a stated purpose.
- An evidence explanation should say what the exhibit directly shows. Do not use it mainly to announce legal conclusions.

### Pass 2: Issue chain

Reduce each theory to:

`chronology -> knowable circumstances -> legal standard -> act or omission -> breach -> causation -> damage or remedy`

Separate primary, alternative, and fallback theories. Keep core facts in the complaint, evidentiary descriptions in the evidence explanation, and developed rebuttal in later briefs.

### Pass 3: Evidence-claim matrix

Create one row per material proposition using `references/review-templates.md`. Test exhibit numbering globally and flag citations that prove a weaker or different fact.

Use the diagonal map as navigation, not as proof. Its left side records facts, causation, contradictions, proof purpose, inference, and legal evaluation; its right side records exhibit ID, date, page, and verification state.

### Pass 4: Causation and damages

- Separate occurrence, amount, foreseeability, mitigation, and proof.
- Separate non-property damage from property damage when both are claimed.
- Within property damage, separate the periods used for past loss and future lost earnings.
- If only part of a larger loss is claimed, identify the allocation and reserved balance expressly.
- For separate medical events, state the date, cause, diagnosis, and treatment period of each; do not merge distinct episodes, diagnoses, admissions, or intervening events.

### Pass 5: Opponent review

Test jurisdiction, standing, limitation, absence of duty, lawful litigation activity, lack of knowledge, weak causation, intervening cause, mitigation, and proof of amount where relevant.

Run the deterministic logic report for both sides. A candidate can identify missing citations, unknown exhibits, reversed dates, or a direct claim resting on inferential support; it cannot establish that every semantic contradiction was found.

For a claim against opposing counsel:

- Do not treat the counsel's contractual duty to the client as a direct contractual duty to the adverse party.
- Use professional rules and the standard of ordinary counsel as evidence relevant to negligence or wrongfulness under tort law.
- Address the strict standard protecting access to courts and ordinary advocacy. Identify the objectively false or groundless premise, knowledge or easy verifiability, the correction opportunity, and conduct after correction.
- Distinguish ordinary denial, settlement refusal, or unsuccessful advocacy from independently wrongful conduct.

### Pass 6: Expression

- Replace motive labels and repeated accusations with observable acts, exact quotations, and expressly identified inferences.
- Keep emotional intensity as the reason for seeking relief, while making the filed text calm and recordable.
- Use short paragraphs with one function each and consistent names for actors.
- Run the deterministic proofreading list before and after semantic revision. Resolve each location-specific typo, conversion, bracket, punctuation, and exhibit candidate, or record why it was not changed.

### Pass 7: Stable version and filing-day gate

1. Read the cause-of-action narrative straight through.
2. Recalculate every amount and date.
3. Confirm all exhibit references against the evidence explanation.
4. Resolve the strongest anticipated defenses.
5. Remove placeholders, duplication, inconsistent names, and obsolete sections.
6. Export the final proofreading list and confirm that every material candidate is resolved or explained.
7. Render the document and inspect every page.
8. Preserve a stable completed version separately from the filing-day checked version.

## Deliverables

Lead with the overall assessment and the highest-impact defect. Then provide the evidence gaps, legal and structural issues, exact revisions, unresolved facts, and completion status. Never describe a draft with unresolved critical evidence or calculation questions as filing-ready.
