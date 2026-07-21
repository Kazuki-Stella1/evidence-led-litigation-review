# OpenAI Build Week final reporting pack

Project: **Evidence-Led Litigation Review**

Release: **v0.3.1**

Track: **Work and Productivity**

Recording target: **2:45**, never over **3:00**

Public source of truth: the clean release repository only

## 1. Final English voiceover

Use `docs/demo-script-en.md` word for word. Its seven spoken sections are the source of truth. Do not improvise legal claims, OCR accuracy, model integration, privacy guarantees, or test numbers.

Required closing:

> We did not build a machine that decides who wins. We built a workflow that makes every important claim easier to verify, challenge, and improve.

Speak calmly at approximately 125–135 words per minute. Say `Codex` and `GPT-5.6` clearly. Keep deterministic Python processing, GPT-5.6 reasoning, and human original-source review separate.

## 2. Second-by-second screen and operation plan

| Time | Screen | Exact action | Message being proved |
|---|---|---|---|
| 0:00–0:06 | `README.md` title and architecture | Start on the clean repository | Product identity and two-layer architecture |
| 0:06–0:17 | `sample/workflow/input/manifest.json` | Show fictional self/opponent items only | Mixed evidence is normalized into one local workflow |
| 0:17–0:29 | architecture and README | Hold deterministic/GPT-5.6 separation | Rules and judgment are different layers |
| 0:29–0:39 | `skills/revise-litigation-filings/SKILL.md` | Show fast cache and precise source gate | Speed never silently replaces source verification |
| 0:39–0:44 | clean terminal | Type the workflow command | Reproducibility |
| 0:44–1:02 | terminal output | Run `python scripts/run_workflow_demo.py` | Seven dossiers, seven events, logic and proofreading output |
| 1:02–1:12 | `evidence-map.html` | Scroll one fictional event, then use opponent filter | Requested rising chronology and side filtering work |
| 1:12–1:22 | `logic-review.md` | Show missing 乙3 and inferential-support findings | Opponent filing is checked by the same standard |
| 1:22–1:27 | clean terminal | Run `python scripts/run_proofreading_demo.py` | Reproducible exact-location proofreading |
| 1:27–1:44 | `proofreading-review.md` | Show PR001, PR002, and PR007 | Line/column, correction, reason, certainty, and no-guess boundary |
| 1:44–1:48 | clean terminal | Type the original demo command | Before/after gate remains reproducible |
| 1:48–1:59 | terminal output and stable report | Run `python scripts/run_demo.py` | 37/11 to 100/0, with no merits claim |
| 1:59–2:12 | skill and README contributions | Show evidence, causation, damages, opponent passes | Meaningful GPT-5.6 role |
| 2:12–2:23 | `tests/test_proofreading.py` and evidence tests | Show location, citation, OCR, map, and opponent tests | Codex-built feature coverage is concrete |
| 2:23–2:28 | `docs/build-log.md` | Hold dated entry | Work and decisions are auditable |
| 2:28–2:36 | terminal test summary | Reveal final unittest output | Automated suite passes |
| 2:36–2:45 | project title | Deliver the required close | Memorable, bounded value claim |

If the cut reaches 2:50, shorten scrolling. Do not speed up or remove the two closing sentences.

## 3. Exact recording commands

Run only inside the clean public repository.

### Pre-recording verification

```bash
python --version
python -m unittest discover -s tests -v
python scripts/privacy_scan.py --history
```

### On-camera evidence workflow

```bash
python scripts/run_workflow_demo.py
```

Expected summary:

```text
workflow: 7 item(s) | 7 event(s) | 11 logic finding(s) | 1 proofreading candidate(s)
Workflow demo verification passed.
```

### On-camera proofreading

```bash
python scripts/run_proofreading_demo.py
```

Expected summary:

```text
proofreading: 1 filing(s) | 7 candidate(s)
Proofreading demo verification passed.
```

### On-camera before/after

```bash
python scripts/run_demo.py
```

Expected summary:

```text
draft: working draft | 37/100 | 11 finding(s)
stable: stable candidate | 100/100 | 0 finding(s)
Demo verification passed.
```

### Test proof

```bash
python -m unittest discover -s tests -v
```

Use the final count recorded in `docs/release-verification.md`. Do not run commands from shell history while recording.

## 4. Safe and prohibited display list

### Safe to display

- clean public release repository root;
- `README.md`, `.codex-plugin/plugin.json`, and `assets/architecture.svg`;
- `skills/revise-litigation-filings/SKILL.md`;
- all deliberately fictional files under `sample/`, including generated text, JSON, HTML, and SVG;
- `tests/`;
- `docs/build-log.md`, `docs/evidence-workflow.md`, and `docs/release-verification.md`; and
- terminal output created by the approved commands.

### Never display

- the private working repository or its earlier history;
- any real complaint, brief, evidence explanation, exhibit, medical record, image, audio, amount, distinctive date sequence, court name, case number, address, phone number, or party name;
- private manifests, original-source directories, transcripts, generated real-case dossiers, or maps;
- upload folders, scratch-parent directories, file pickers, private chats, `/feedback` payloads, or diagnostic logs;
- account email addresses, browser bookmarks, notifications, other tabs, clipboard history, or terminal history; and
- any screen that has not passed the privacy gate.

Use a clean recording copy with a neutral terminal prompt. Disable notifications and close unrelated windows.

## 5. Cross-surface consistency

Detailed evidence is in `docs/devpost-consistency-audit.md`. The approved claims are:

- one local deterministic layer for extraction state and structural candidates;
- one GPT-5.6-in-Codex reasoning layer;
- no claim that the Python tools call a model API;
- fast text navigation plus a separate original-source gate;
- local TXT, structured text, DOCX, PDF, and common-image paths, with optional Poppler/Tesseract requirements stated;
- a rising diagonal self/opponent chronology, two-sided 甲・乙 checks, and extracted-text line/column proofreading;
- 37/100 with eleven findings and 100/100 with zero findings in the original deterministic fixture;
- fully fictional public data only; and
- no legal-merits, authenticity, completeness, OCR-certainty, or win-probability claim.

## 6. Ten hard judge questions and answers

### 1. Isn't this just a regex checker?

**Answer:** Regex is used where deterministic notation and literal checks are appropriate, such as 甲・乙 citations, repeated input, and registered misconversions. The product also performs source hashing and cache invalidation, DOCX/PDF/image extraction, explicit precision states, a two-sided chronology, claim-to-evidence comparison, date and causal-order checks, line-and-column repair export, and a Codex skill. GPT-5.6 handles the semantic work that rules should not pretend to decide: direct proof versus inference, competing causes, contextual wording, damage periods, and strongest objections.

### 2. Where does GPT-5.6 make a meaningful contribution?

**Answer:** GPT-5.6 is the reasoning layer used through the Codex skill. It evaluates what a source directly shows, where an inference begins, which causal step is unsupported, whether separate causes or medical events were collapsed, whether damage periods overlap, and what the strongest lawful response would be. It explains why wording should be narrowed or supported. It is not called by the Python tools.

### 3. How do you reduce legal hallucinations?

**Answer:** The skill first states which sources and pages were actually readable. Propositions are separated into direct support, inference, dispute, and unverified material. Missing OCR language data fails explicitly. Important details return to the original. Current law must be checked against authoritative primary sources, the score is never legal merit, and a human retains filing responsibility.

### 4. Why focus on Japanese litigation filings?

**Answer:** Japanese practice has recurring structures such as 甲・乙号証 notation, evidence explanations, and distinct damages terminology. A focused implementation is more useful than a generic writing assistant. The workflow can travel, but another jurisdiction needs its own terminology, procedural checks, and primary-law validation.

### 5. Does the project upload real evidence to an external service?

**Answer:** The deterministic source and filing tools make no network request and need no API key. GPT-5.6 operates only when a user separately invokes the Codex skill and provides material in that chosen environment. Users must follow applicable privacy policy. The public repository and demo contain only an unrelated fictional dispute.

### 6. What do 37 and 100 mean?

**Answer:** They are deterministic drafting-readiness scores from the original filing checker. Thirty-seven means weighted structural warnings remain in the fictional draft. One hundred means that rule set found none in the stable fixture. Neither is a win probability, evidence-sufficiency judgment, or filing approval. The newer logic report uses finding counts and severity rather than converting them into a merits-like score.

### 7. What value does this provide to lawyers or self-represented litigants?

**Answer:** Routine review starts from a searchable dossier instead of repeatedly opening every source. Important details still return to the original. The map makes chronology and opposing material visible, while logic and proofreading reports identify repeatable gaps and exact repair locations before semantic review. This reduces revision drift and leaves a traceable list; it supports rather than replaces professional judgment.

### 8. Can it extend to other countries or document formats?

**Answer:** The evidence cache, chronology, claim mapping, causation review, opponent review, and filing gate are portable. Today it supports common text formats, DOCX, text PDFs, scanned PDFs, and common images when local tools are available. Other countries require separate notation, rule packs, and authoritative-law validation. Legacy `.doc` is not ingested directly.

### 9. What is lost without Codex?

**Answer:** The local intake, map, and deterministic reports still work. What is lost is reusable multi-file reasoning: distinguishing direct proof from inference, integrating chronology through damage, separating causes, steelmanning the response, and explaining revisions. Codex turns outputs into a disciplined review loop.

### 10. What was the most important design decision?

**Answer:** There were two linked decisions: separate deterministic processing from model judgment, and separate fast cached text from original-source verification. Those boundaries make each layer testable and stop a convenient extract, OCR result, or structural score from masquerading as evidence authenticity or legal merit. The privacy decision follows the same principle: only unrelated fictional data belongs in public.

## 7. Thirty-second, sixty-second, and three-minute explanations

### 30 seconds

> Evidence-Led Litigation Review is a local-first Codex plugin for Japanese legal work. It converts supported evidence into cached dossiers, draws a two-sided chronology, and lists filing-to-evidence inconsistencies plus exact proofreading locations. Important details return to the original. GPT-5.6 in Codex then separates direct proof from inference, tests causation and the strongest response, and explains revisions. It does not decide who wins; it makes claims easier to verify, challenge, and improve.

### 60 seconds

> Repeated legal drafting hides evidence work: people reopen the same PDFs and screenshots, citations drift, facts blur into inference, and opponent material is reviewed inconsistently. Evidence-Led Litigation Review creates a local dossier for each source, records hashes and verification state, draws a rising self/opponent chronology, and lists deterministic gaps plus location-specific proofreading across filings and 甲・乙 evidence. Fast cached text supports navigation; important details return to the original. GPT-5.6 in Codex is the separate reasoning layer for direct proof, competing causes, damage periods, strongest objections, and record-faithful wording. The public demos are completely fictional. The system does not authenticate evidence, decide legal merit, or predict success.

### Three minutes

Use `docs/demo-script-en.md` word for word with the shot plan above.

## 8. Pre-recording checklist

- [ ] Recording copy came from the clean v0.3.1 release ZIP or matching commit.
- [ ] No parent directory, private filename, real manifest, transcript, dossier, or map is visible.
- [ ] Notifications, email, messaging, cloud-sync popups, bookmarks, and history are hidden.
- [ ] Terminal prompt does not expose a personal name, email, or private path.
- [ ] `python scripts/run_workflow_demo.py` produces 7 items, 7 events, 11 logic findings, 1 proofreading candidate, and passes.
- [ ] `python scripts/run_proofreading_demo.py` produces 7 location-specific candidates and passes.
- [ ] `python scripts/run_demo.py` produces 37/11 and 100/0 and passes.
- [ ] The final unit count matches `docs/release-verification.md` and ends in `OK`.
- [ ] The narration separates Python, GPT-5.6, and human source review.
- [ ] No statement implies OCR certainty, legal merit, authenticity, or complete inconsistency detection.
- [ ] Final cut is 2:50 or shorter and uploaded duration is 3:00 or shorter.
- [ ] English audio is used, or the English translation is attached.
- [ ] Final frame includes the project name and required closing.

## 9. GitHub, YouTube, and Devpost order

1. Run `/feedback` in the primary Codex build thread and save the Session ID privately.
2. Confirm the intended GitHub account, repository name, and visibility.
3. Publish only the clean release repository matching the final ZIP checksum.
4. Verify README rendering, license, fictional sample, clone, demos, and tests from a clean copy.
5. Insert the verified repository URL into the Devpost draft.
6. Record the video from that verified copy.
7. Confirm YouTube account, title, and Public visibility, then upload.
8. Verify duration, audio, resolution, and public access from a signed-out browser.
9. Paste repository URL, YouTube URL, and `/feedback` Session ID into Devpost.
10. Select Work and Productivity, review every field, submit, and verify the entry separately.

Do not perform GitHub publication, YouTube upload, or Devpost submission until the external targets below are explicitly confirmed.

## 10. Final GO / NO-GO decision

### Local v0.3.1 package

Use `docs/release-verification.md` as the controlling local GO record. The unchanged v0.2 public candidate remains the fallback until v0.3.1 passes the complete release gate.

### External publication and submission: HOLD — conditional GO

| External field | Required value |
|---|---|
| GitHub account | Not yet confirmed |
| Repository name | Recommended: `evidence-led-litigation-review`; not yet confirmed |
| Repository visibility | Public recommended for simpler judging; not yet confirmed |
| YouTube account | Not yet confirmed |
| Video title | Recommended: `Evidence-Led Litigation Review — OpenAI Build Week Demo`; not yet confirmed |
| YouTube visibility | Must be Public; not yet confirmed |
| Devpost target | OpenAI Build Week / Work and Productivity; final project record not yet confirmed |
| Repository and YouTube URLs | Not yet created or confirmed |
| `/feedback` Session ID | Not yet supplied |

Once these values are confirmed and the local v0.3.1 gate is GO, publish in GitHub → YouTube → Devpost order.
