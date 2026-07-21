# Fictional evidence-workflow fixture

Every person, entity, transaction, date, amount, filing, exhibit, statement, and output in this directory is deliberately fictional. The fixture was created only to demonstrate two-sided evidence intake, mapping, and deterministic consistency candidates. It is unrelated to any real dispute.

Run from the repository root:

```bash
python scripts/run_workflow_demo.py
```

The script reads `input/manifest.json` and regenerates `output/`.

The fixture intentionally contains two opponent-side review candidates:

- the fictional opponent filing cites `乙3`, which is absent from the evidence index; and
- a direct claim that payment was never received relies on `乙1`, whose fictional wording only says that one employee had not yet confirmed it on screen.

High and critical items remain marked as requiring original-source review in fast mode. That behavior is intentional even though the fixture sources are plain text.
