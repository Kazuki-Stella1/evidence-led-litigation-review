# Judge quickstart

## Fastest path: test the working project without rebuilding

Prerequisite: CPython 3.10 or newer.

From the repository root:

```bash
python scripts/run_demo.py
python scripts/run_workflow_demo.py
python scripts/run_proofreading_demo.py
python -m unittest discover -s tests -v
```

No package installation, API key, test account, compiler, container, database, or network connection is required for the three included fictional demos. The first command processes the fictional draft and stable filing. The second creates fictional evidence dossiers, a diagonal map, a two-sided logic report, and a proofreading report under `sample/workflow/output/`. The third demonstrates seven exact-location repair candidates.

Expected demo result:

```text
draft: working draft | 37/100 | 11 finding(s)
stable: stable candidate | 100/100 | 0 finding(s)
Demo verification passed.
workflow: 7 item(s) | 7 event(s) | 11 logic finding(s) | 1 proofreading candidate(s)
Workflow demo verification passed.
proofreading: 1 filing(s) | 7 candidate(s)
Proofreading demo verification passed.
```

Inspect:

- `sample/output/draft/review.md`
- `sample/output/stable/review.md`
- `sample/output/draft/review.json`
- `sample/output/stable/review.json`
- `sample/workflow/output/intake/evidence-index.md`
- `sample/workflow/output/map/evidence-map.html`
- `sample/workflow/output/logic/logic-review.md`
- `sample/workflow/output/proofreading/proofreading-review.md`
- `sample/proofreading/output/proofreading/proofreading-review.md`
- `sample/proofreading/output/proofreading/proofreading-review.csv`

## Supported platforms

| Platform | Status | Command |
|---|---|---|
| Linux | Release-tested with CPython 3.12 | `python scripts/run_demo.py`, `python scripts/run_workflow_demo.py`, and `python scripts/run_proofreading_demo.py` |
| macOS | Designed for CPython 3.10+; standard-library fictional demos | `python3 scripts/run_proofreading_demo.py` |
| Windows | Designed for CPython 3.10+; standard-library fictional demos | `py scripts\run_proofreading_demo.py` |

The POSIX `scripts/run_demo.sh` wrapper is optional. The Python demos are the portable path. Real PDF/image intake additionally requires locally installed Poppler and/or Tesseract; Japanese OCR requires Tesseract `jpn` language data. A reviewed UTF-8 transcript sidecar is the explicit fallback when local extraction is unavailable.

## Test the plugin in Codex with GPT-5.6

The release process produces `evidence-led-litigation-review-marketplace-0.3.1.zip`. It is a ready local marketplace; judges do not rebuild the plugin.

1. Unzip the marketplace archive.
2. Add its absolute root path to Codex:

   ```bash
   codex plugin marketplace add /absolute/path/evidence-led-litigation-review-marketplace
   ```

3. Install the ready plugin:

   ```bash
   codex plugin add evidence-led-litigation-review@evidence-led-litigation-review-local
   ```

4. Restart or refresh the ChatGPT desktop app, select GPT-5.6 in Codex, and start a new thread.
5. Attach `sample/input/complaint_draft.txt` and `sample/input/evidence.json`, then use:

   > この架空の訴状と証拠索引を読み、ローカルチェッカーを入口に、証拠、論点、因果関係・損害、最強反論、表現、提出前確認の順でレビューしてください。直接立証・推論・争いあり・未立証を分けてください。

Expected behavior: Codex uses the deterministic report as triage, then applies the skill's evidence-led passes. It should not call the 37/100 number a chance of winning, and it should distinguish what each fictional exhibit directly proves from later inference.

## Architecture boundary

- The Python source and filing tools are deterministic and do not call an OpenAI API.
- GPT-5.6 is the reasoning layer inside the Codex plugin workflow.
- The repository-only demos prove local extraction, mapping, logic, and location-specific proofreading; the installed-plugin prompt demonstrates the complete two-layer experience.

## Privacy verification

Before any public release:

```bash
python scripts/privacy_scan.py --history
```

Private party names may be checked without storing them:

```bash
python scripts/privacy_scan.py --history --deny "PRIVATE_TOKEN"
```

The repository's included case is deliberately fictional. Automated scanning is not a substitute for manual semantic review.
