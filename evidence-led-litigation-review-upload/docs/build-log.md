# Build log

All public plugin code and submission materials were created during the OpenAI Build Week submission period. The underlying drafting problem existed before Build Week; the public software artifact did not.

## Dated repository work

| Recorded timestamp | Commit or verification | Codex contribution | Key human/product decision |
|---|---|---|---|
| 2026-07-19T10:03:35+07:00 | Private working commit `382eb88`—not for publication | Scaffolded the plugin, implemented the analyzer and anonymizer, created fixtures and tests | Use a reusable fixed-pass workflow and a dependency-free local checker |
| 2026-07-19T10:15:57+07:00 | Private working commit `0998d26`—not for publication | Improved documentation, validation coverage, deterministic demo output, and release notes | Treat checker output as drafting triage, never a merits decision |
| 2026-07-19 | Private completion snapshot `3474418`—not for publication | Audited official requirements, added explicit Codex/GPT-5.6 roles, cross-platform demo, privacy/history scan, judge path, English demo copy, and deterministic packaging | Replace facts resembling any private workflow with a deliberately fictional public case |
| 2026-07-18T23:05:06-06:00 (2026-07-19 JST) | Clean public commits `9357e2e`, `a92942b`, `77eb87f`, and `2602b1a` | Imported only the fully fictional release tree, separated working code from submission material, and recorded release QA | Publish a fresh auditable history instead of the private development history |
| 2026-07-19 | Final reporting pass; inspect the newest public commit | Added the timed demo runbook, safe-screen boundary, consistency audit, hard-question rehearsal, short pitches, and external publication gate | Finish communication and verification without expanding product scope |
| 2026-07-20 | Feature commit `0f1e83f` on `feature/evidence-workflow` | Implemented local evidence extraction, hash-aware dossiers, fast/precise gates, diagonal mapping, two-sided logic candidates, fictional fixtures, integration tests, and v0.3 documentation | Use cached text for routine speed, require original-source review for important details, and apply the same evidence standard to opponent filings |
| 2026-07-20 | Feature commit `02b5f8d` on `feature/evidence-workflow` | Added deterministic line-and-column proofreading, private correction rules, exhibit-repair logic, Markdown/JSON/CSV exports, a seven-candidate fictional demo, tests, and v0.3.1 submission documentation | Propose a corrected exhibit only when the index and an explicit same-line claim mapping identify it; otherwise require source review instead of guessing |

## Where GPT-5.6 was used

GPT-5.6 was the reasoning layer in the primary Codex build thread. It was used to:

- distinguish deterministic structural checks from evidence and legal judgment;
- turn a repeated filing-review process into seven ordered passes;
- reason through direct proof versus inference and disputed facts;
- separate causation, non-property damage, past loss, and future loss;
- steelman lawful-advocacy, knowledge, causation, mitigation, and amount objections;
- review public-sample privacy at the level of fact patterns, not only names;
- separate source extraction from authentication and fast navigation from precise source review;
- structure a two-sided chronology around facts, proof purpose, causation, contradiction, inference, and legal evaluation;
- align the README, demo narration, tests, and Devpost description;
- separate repeatable typo/notation detection from contextual Japanese-language judgment; and
- require evidence-index support before presenting an exhibit number as a correction.

The repository does not imply that a Python score came from GPT-5.6. The Python analyzer is deterministic; GPT-5.6 is invoked through the Codex skill for record-sensitive reasoning.

## Reproducible verification commands

```bash
python -m unittest discover -s tests -v
python scripts/run_demo.py
python scripts/run_workflow_demo.py
python scripts/run_proofreading_demo.py
python scripts/privacy_scan.py --history
python /path/to/plugin-creator/scripts/validate_plugin.py .
python /path/to/skill-creator/scripts/quick_validate.py skills/revise-litigation-filings
python scripts/build_release.py
```

Exact final test outputs are recorded in `docs/release-verification.md`; generated archive hashes are written to `dist/SHA256SUMS`.
