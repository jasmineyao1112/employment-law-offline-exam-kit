# Singapore Employment Law Offline Exam Kit

> Search an entire employment-law course in seconds — with no Wi-Fi, server, account, or AI required.

This project turns lecture slides, bilingual revision notes, and quiz materials into a fast, browser-based reference tool for open-book study and exams. It was designed around Singapore labour and employment law, with English and Chinese search support throughout.

## What makes it useful

- **Fully offline:** open `index.html` locally and search without a network connection.
- **Fast bilingual retrieval:** search legal terms in English or Chinese and jump directly to the relevant card or slide.
- **Exam-focused content:** 1,560 searchable knowledge cards across 11 sources, including 38 quiz questions with teacher answers, legal boundaries, and follow-up practice.
- **Original-slide context:** 382 slide images help users verify wording and understand where each rule came from.
- **Practical search syntax:** supports multiple-keyword search, exact phrases, exclusions, abbreviations, prefixes, and typo tolerance.
- **Personal study tools:** bookmark cards, add notes, and export or import study data locally.
- **No tracking:** the app runs entirely in the browser and does not send study materials anywhere.

## Quick start on macOS

1. Download the repository as a ZIP and keep the full folder together.
2. Double-click `02_打开离线速查.command`.
3. Search terms such as `Q38`, `annual leave`, `vicarious liability`, `WICA`, `年假`, or `竞业限制`.

You can also open `index.html` directly in a browser. The `.command` launcher is provided for convenience.

## Rebuild the reference library

Add text-searchable PDF or Markdown files to `materials/`, then double-click `01_构建考试资料库.command`. On first use, the script creates a local Python environment and installs PyMuPDF.

Run `03_考前自检.command` after rebuilding. It checks the index structure, linked images, source count, and external HTML dependencies.

## Search examples

| Query | Result |
| --- | --- |
| `annual leave` | Cards containing both words |
| `"section 14"` | Exact phrase match |
| `dismissal -retrenchment` | Dismissal results excluding retrenchment |
| `Q01` to `Q38` | Individual quiz questions and explanations |
| `年假`, `工伤`, `竞业限制` | Chinese retrieval across bilingual notes |

## How it works

The Python indexer extracts text from PDF and Markdown sources, breaks it into searchable cards, and writes the result to `data.js`. The interface in `index.html` loads that data directly using a normal script tag, so it works under `file://` without a local server.

Search uses a lightweight client-side relevance index with phrase matching, exclusions, prefix expansion, abbreviation support, typo tolerance, and Chinese bigram matching. Slide images are stored as relative assets so the project remains portable.

```text
PDF / Markdown sources
        ↓
build_index.py
        ↓
data.js + assets/
        ↓
index.html (offline browser app)
```

## Repository structure

```text
Employment_Law_Offline_Exam_Kit/
├── index.html                 # Offline search interface
├── data.js                    # Generated searchable index
├── assets/                    # Referenced slide images
├── materials/                 # PDFs and bilingual Markdown notes
├── build_index.py             # Index builder
├── annotations.py             # Optional glossary and question annotations
├── 01_构建考试资料库.command
├── 02_打开离线速查.command
└── 03_考前自检.command
```

## Current collection

- 6 seminar slide decks
- 4 consolidated bilingual study-note sets
- 1 bilingual 38-question quiz revision reference
- 1,560 searchable cards
- 382 original slide images

The legal notes were checked through **30 September 2026**. Laws, thresholds, and policy commencement dates may change, so use the source links in the notes when relying on the material after that date.

## Exam use

Use the tool only where the applicable assessment rules permit access to local files and a browser. Secure Examplify settings may restrict other applications or local resources.

## Educational notice

This project is an educational reference and does not provide legal advice. Verify current law and the facts of a specific situation before relying on any legal proposition.

---

Designed and curated by **Jasmine Yao** for faster, calmer, and more reliable open-book revision.
