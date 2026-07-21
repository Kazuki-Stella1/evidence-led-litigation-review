# Privacy and safety

This repository contains only deliberately fictional demo material. `原告A` and `取引相手B` are abstract labels, not replacements for real people.

The filing analyzer, evidence intake, diagonal map, deterministic logic checker, and proofreading exporter run locally and make no network request. Optional PDF and image extraction uses local Poppler and Tesseract programs. The anonymizer is a first pass, not a guarantee of anonymity. Removing names is insufficient when dates, relationships, medical events, quotations, or an unusual combination of facts can identify a person.

Before publishing, run:

```bash
python scripts/privacy_scan.py --history
```

Also perform a human semantic review of the current tree and every repository intended for publication. A clean automated result means only that the configured patterns were not found.

Do not commit real manifests, correction glossaries, extracted dossiers, proofreading outputs, transcripts, maps, exhibits, medical records, audio, images, addresses, account identifiers, case numbers, or unredacted court documents. Keep real workflow inputs and outputs in a private case directory outside the public repository. Never push the private working repository merely because its current files were later cleaned; publish only a separately verified clean-history release repository.
