# Devpost consistency audit

Audit date: 2026-07-20 JST
Compared surfaces: `README.md`, `SUBMISSION.md`, English and Japanese demo scripts, plugin manifest, skill, fictional fixtures, generated reports, and automated tests.

## Result

**PASS for local v0.3.1 content after the release gate recorded in `docs/release-verification.md`.** External repository, YouTube, and `/feedback` values remain intentionally blank.

| Claim | README and Devpost | Demo | Implementation or output | Result |
|---|---|---|---|---|
| Project and track | Evidence-Led Litigation Review / Work and Productivity | Same | Manifest category is Productivity | Pass |
| Architecture | Deterministic local tools + GPT-5.6 in Codex | Same | Python tools and bundled skill are separate | Pass |
| Model boundary | Python makes no model API call | Same | No OpenAI or network client in evidence or filing tools | Pass |
| Fast/precise boundary | Cached navigation plus original-source gate | Same | Source hash, extraction mode, precision state, and `source_checked` are separate fields | Pass |
| Inputs | text, DOCX, PDF, common images; optional local tools stated | Same | Dispatcher and tests cover text, DOCX, PDF, and image OCR | Pass |
| Evidence outputs | dossiers, index, diagonal HTML/SVG map | Same | Fictional demo regenerates all outputs | Pass |
| Two-sided review | self/opponent/neutral and 甲・乙 | Same | Missing fictional 乙3 and inferential 乙1 support are detected | Pass |
| Proofreading | extracted-text line/column, correction, reason, certainty | Same | Seven-candidate fictional demo and Markdown/JSON/CSV outputs match | Pass |
| Filing before/after | 37/11 and 100/0 | Same | `scripts/run_demo.py` output matches | Pass |
| Score boundary | readiness triage only | Same | Disclaimers deny merit or win probability | Pass |
| Tests | complete automated suite | final count shown | Count and environment are recorded in release verification | Pass |
| Privacy | unrelated fictional public sample | same safe-screen rule | Current tree/history scanner and manual semantic review | Pass |
| Codex contribution | implementation, tests, fixtures, docs, repair, release | same | Build log and commits support the claim | Pass |
| GPT-5.6 contribution | direct proof/inference, causation, damage, opponent, expression | same | Skill encodes fixed record-sensitive passes | Pass |
| Judge path | three commands, no build or API key for fictional demos | commands shown | All three demos run from repository source | Pass |

## Wording controls

Approved:

- “local-first” for the deterministic source and filing tools;
- “GPT-5.6 in Codex is the reasoning layer”;
- “fast cached-text navigation” and “precise original-source gate”;
- “deterministic inconsistency candidates”;
- “location-specific proofreading candidates,” not complete language correction;
- “drafting-readiness score,” never win probability;
- “fully fictional public sample”; and
- “supports professional judgment; does not replace it.”

Do not say:

- the entire GPT-5.6 workflow is local;
- the Python tools call GPT-5.6 or an OpenAI API;
- OCR, transcript matching, a hash, or `source_checked` authenticates evidence;
- the logic report finds every semantic inconsistency;
- 100/100 means filing-ready, legally correct, or likely to win;
- the anonymizer guarantees anonymity; or
- a real lawsuit, medical event, amount, image, or distinctive chronology appears in the public demo.

## Remaining external consistency gate

After publication, verify the actual:

1. repository URL and commit;
2. release ZIP checksum;
3. public YouTube URL, duration, audio, and visibility;
4. `/feedback` Session ID; and
5. Devpost entry URL and selected Work and Productivity track.
