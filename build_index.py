#!/usr/bin/env python3
"""
Generic offline exam-kit builder.

Scans SOURCE_DIR for *.pdf and *.md files, slices them into searchable
cards, renders one image per PDF page, copies images referenced by
Markdown, and writes data.js next to index.html.

Everything is local. No network calls. Re-run whenever the material changes:

    python3 build_index.py

Input assumptions
-----------------
PDF      : text layer present (not a scan). One page = one card.
           Bookmarks (get_toc) give the best titles.
Markdown : one card per paragraph block; heading path becomes the section.
           If the file has no headings, blocks are used as-is.

If a file is a scan (very few extracted characters per page), OCR it first
(`ocrmypdf in.pdf out.pdf`) and index the OCRed copy.
"""

import json
import os
import re
import shutil
from datetime import datetime

import fitz  # PyMuPDF

# --------------------------------------------------------------------------
# CONFIG — edit these three lines for a new subject
# --------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.environ.get("SOURCE_DIR", os.path.join(HERE, "materials"))
OUT_DIR = HERE                      # data.js + assets/ land here

# Optional: {filename: label shown in the UI}. Files not listed fall back to
# a label derived from the file name.
LABELS = {
    # "week1.pdf": "Week 1 - Introduction",
}

IMG_ZOOM = 1.6        # ~856px wide for A4 portrait
IMG_QUALITY = 62      # ~40 KB per page; 400 pages ~= 19 MB
BULLETS = "•➢▪●◦‣"
MAX_BLOCK = 900       # Markdown blocks longer than this get split further

SOURCE_EXT = (".pdf", ".md", ".markdown")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def norm(s):
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'),
                 ("\u2013", "-"), ("\u2014", "-")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def split_items(flat):
    parts = [p.strip() for p in re.split("[" + BULLETS + "]", flat)]
    return [p for p in parts if p] or ([flat] if flat else [])


def is_noise(line):
    return bool(re.match(r"^Source\s*:", line, re.I)
                or re.match(r"^\d{1,3}$", line)
                or re.match(r"^(Slide\s*\d+)$", line, re.I))


def strip_md(line):
    """Remove markdown decoration so the text reads clean in the UI."""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)          # images
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)         # links
    s = re.sub(r"`{1,3}", "", s)                           # code ticks
    s = re.sub(r"^\s{0,3}#{1,6}\s*", "", s)
    s = re.sub(r"^\s{0,3}>\s?", "", s)
    s = re.sub(r"^\s*[-*+]\s+", "", s)
    s = re.sub(r"^\s*\d+[.)]\s+", "", s)
    s = re.sub(r"(\*\*|__|\*|_)", "", s)
    return s.strip()


# --------------------------------------------------------------------------
# PDF: one card per page
# --------------------------------------------------------------------------
def extract_pdf(path, source_idx, label, out_dir):
    doc = fitz.open(path)
    toc = {}
    for _lvl, title, page in doc.get_toc():
        toc[page - 1] = title

    os.makedirs(out_dir, exist_ok=True)
    cards = []
    empty = 0

    for pno in range(len(doc)):
        page = doc[pno]
        rows = []
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for line in b.get("lines", []):
                text = "".join(s["text"] for s in line["spans"]).strip()
                if not text:
                    continue
                size = max(s["size"] for s in line["spans"])
                rows.append((line["bbox"][1], text, size))
        rows.sort(key=lambda r: r[0])

        # title: bookmark -> largest text on the page -> first bullet
        title = ""
        raw = toc.get(pno, "")
        m = re.match(r"^Slide\s*\d+\s*:\s*(.+)$", raw)
        if m:
            title = norm(m.group(1))
        if not title and raw:
            title = norm(raw)
        if not title and rows:
            top = max(rows, key=lambda r: r[2])
            if top[2] >= 19:                      # body text is usually ~17.5
                title = norm(top[1])

        body = [r for r in rows if not is_noise(norm(r[1]))]
        if title:
            body = [r for r in body if norm(r[1]) != title]

        flat = norm(" ".join(norm(r[1]) for r in body))
        if not flat:
            empty += 1
            continue
        items = split_items(flat)
        if not title and items:
            title = items[0][:55] + ("..." if len(items[0]) > 55 else "")

        img_name = "%03d.jpg" % (pno + 1)
        page.get_pixmap(matrix=fitz.Matrix(IMG_ZOOM, IMG_ZOOM)).save(
            os.path.join(out_dir, img_name), jpg_quality=IMG_QUALITY)

        cards.append({
            "s": source_idx, "p": pno + 1, "t": title, "sec": "",
            "txt": flat, "it": items,
            "img": "assets/s%d/%s" % (source_idx, img_name),
        })

    doc.close()
    if empty:
        print("     (%d blank/unreadable pages skipped — scanned? try OCR)" % empty)
    return cards


# --------------------------------------------------------------------------
# Markdown: one card per paragraph block, headings give the section
# --------------------------------------------------------------------------
def extract_markdown(path, source_idx, label, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    raw = open(path, encoding="utf-8", errors="ignore").read()
    # drop fenced code blocks? No — many notes put formulas there. Keep them
    # but they are just text to us.
    lines = raw.split("\n")

    heads = []            # stack of (level, text)
    blocks = []           # (section_path, [raw lines])
    buf = []

    def flush():
        if not buf:
            return
        blocks.append((" > ".join(h[1] for h in heads), list(buf)))
        buf.clear()

    for ln in lines:
        if ln.strip().startswith("```"):
            buf.append(ln)
            continue
        m = re.match(r"^\s{0,3}(#{1,6})\s+(.*)$", ln)
        if m:
            flush()
            level = len(m.group(1))
            text = strip_md(m.group(2))[:80]
            while heads and heads[-1][0] >= level:
                heads.pop()
            heads.append((level, text))
            continue
        if not ln.strip():
            flush()
            continue
        buf.append(ln)
    flush()

    def grab_images(blk):
        """Copy local images referenced by a block, return their asset paths."""
        out = []
        for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", "\n".join(blk)):
            src = m.group(1).split()[0].strip("<>")
            if src.startswith(("http://", "https://", "data:")):
                continue
            src_path = os.path.join(os.path.dirname(path), src)
            if not os.path.exists(src_path):
                continue
            tgt = os.path.join(out_dir, os.path.basename(src))
            shutil.copyfile(src_path, tgt)
            rel = "assets/s%d/%s" % (source_idx, os.path.basename(src))
            if rel not in out:
                out.append(rel)
        return out

    cards = []
    pending = []          # images with no text block before them yet
    for section, blk in blocks:
        imgs = grab_images(blk)
        text_lines = [x for x in (strip_md(x) for x in blk) if x]
        if not text_lines:
            # Image-only block. Attach backwards to the card it illustrates;
            # if there is none yet, carry it forward.
            if imgs and cards:
                cards[-1]["img"] = cards[-1].get("img") or imgs[0]
                if len(imgs) > 1:
                    cards[-1]["imgs"] = (cards[-1].get("imgs") or []) + imgs
            else:
                pending.extend(imgs)
            continue
        imgs = imgs + pending
        pending = []

        flat = norm(" ".join(text_lines))
        for n, chunk in enumerate(chunk_text(flat)):
            cards.append({
                "s": source_idx, "p": None, "t": chunk[:80], "sec": section,
                "txt": chunk, "it": split_items(chunk),
                "img": imgs[0] if (imgs and n == 0) else None,
                "imgs": imgs if (len(imgs) > 1 and n == 0) else None,
            })
    if pending:           # trailing figures with no text after them
        cards.append({
            "s": source_idx, "p": None, "t": "Figures", "sec": "Figures",
            "txt": "Figures from the source notes.", "it": [],
            "img": pending[0], "imgs": pending,
        })

    return cards


def chunk_text(flat):
    """Split an over-long paragraph block at sentence boundaries."""
    if len(flat) <= MAX_BLOCK:
        return [flat]
    parts = re.split(r"(?<=[.。;!?])\s+", flat)
    out, cur = [], ""
    for p in parts:
        if cur and len(cur) + len(p) > MAX_BLOCK:
            out.append(cur.strip())
            cur = p
        else:
            cur = (cur + " " + p).strip()
    if cur:
        out.append(cur)
    return [x for x in out if x] or [flat]


# --------------------------------------------------------------------------
# quick-reference mining: money, time periods, statutory sections, case names
# --------------------------------------------------------------------------
MONEY_RE = re.compile(r"(?:S\$|SGD|\$)\s?\d[\d,]*(?:\.\d+)?\s?(?:K|k|M|m)?\b|\b\d[\d,]*\s?dollars\b")
TIME_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:day|days|week|weeks|month|months|year|years|hour|hours)\b")
SECT_RE = re.compile(r"\b(?:[Ss]ection|s\.|S\.|ss\.|art\.|Art\.)\s?\d+[A-Za-z]?(?:\(\d+\))?\b")
CASE_RE = re.compile(r"\b[A-Za-z][A-Za-z'’\-]+(?:\s+[A-Za-z'’\-.]+){0,4}\s+v\.?\s+[A-Za-z][A-Za-z'’\-]+(?:\s+[A-Za-z'’\-.]+){0,3}\b")

# Only surface a number when the sentence around it states a rule. Without
# this filter hypotheticals ("I sell you my car for $50K") pollute the table.
KEY_HINTS = re.compile(
    r"limit|ceiling|cap\b|capped|threshold|minimum|maximum|up to|not exceeding|exceed|"
    r"entitle|entitled|eligib|qualify|qualifying|shall|must|require|required|"
    r"salary|wages|pay\b|paid|payment|levy|penalty|fine|compensation|"
    r"claim|contribution|rate|notice|leave|per month|per year|per annum|"
    r"covered|coverage|apply|applies|section|act\b|under the|of service",
    re.I)
NOISE_HINTS = re.compile(r"\bI (offer|ask|sell|approach)\b|\beg:\s*I\b|my car", re.I)


def sentences(text):
    return [p.strip() for p in re.split(r"(?<=[.;])\s+|\s*•\s*", text) if p.strip()]


def keep_ctx(sent):
    return not NOISE_HINTS.search(sent) and bool(KEY_HINTS.search(sent))


def mine(cards):
    money, timeq, sects, cases = [], [], [], []
    seen = set()

    def add(bucket, tag, value, ctx, ci):
        key = (tag, value.lower(), ci)
        if key in seen:
            return
        seen.add(key)
        bucket.append({"v": value.strip(), "c": ctx[:260], "i": ci})

    for ci, c in enumerate(cards):
        for sent in sentences(c.get("txt", "")):
            if keep_ctx(sent):
                for m in MONEY_RE.findall(sent):
                    add(money, "m", m, sent, ci)
                for m in TIME_RE.findall(sent):
                    add(timeq, "t", m, sent, ci)
            for m in SECT_RE.findall(sent):
                add(sects, "s", m, sent, ci)
            for m in CASE_RE.findall(sent):
                if len(m) > 10 and " v " in m:
                    add(cases, "c", m, sent, ci)

    uniq, names = [], set()
    for c in cases:
        k = re.sub(r"[^a-z]", "", c["v"].lower())
        if k not in names:
            names.add(k)
            uniq.append(c)
    return money, timeq, sects, uniq


# Long Form (ABBR) and ABBR (Long Form). Note the space in the char class —
# "Industrial Arbitration Court (IAC)" is several words, not one.
ABBR_RE = re.compile(r"\b([A-Za-z][A-Za-z\s\-]{1,40}[A-Za-z])\s*[（(]\s*([A-Z]{2,7})\s*[)）]")
ABBR_RE2 = re.compile(r"\b([A-Z]{2,7})\s*[（(]\s*([A-Za-z][A-Za-z\s\-]{3,45})\s*[)）]")


MINOR = {"of", "for", "and", "the", "to", "in", "on", "at", "by", "de", "&"}


def tidy_full(s):
    return re.sub(r"^(?:the|a|an)\s+", "", s.strip(), flags=re.I).strip()


def plausible_full(s):
    """Reject multi-word junk that a space-tolerant regex will otherwise
    pick up across sentence boundaries ('... s can be both a criminal (WSHA)')."""
    words = s.split()
    if not 2 <= len(words) <= 6:
        return False
    caps = sum(1 for w in words if w[:1].isupper() or w.lower() in MINOR)
    return caps >= len(words) - 1

# Hand-checked aliases: typing the short form finds the long form and back.
# Keep this small — every alias is also a possible source of noise.
SEED_SYNONYMS = {
    # "ea": ["employment act"], "employment act": ["ea"],
    # "sacked": ["dismissal", "termination"],
    # "redundancy": ["retrenchment"], "retrenchment": ["redundancy"],
}


def mine_abbrevs(cards):
    found = {}
    for c in cards:
        for sent in sentences(c.get("txt", "")):
            for full, ab in ABBR_RE.findall(sent):
                full = tidy_full(full)
                if plausible_full(full) and full[:1].isupper() \
                        and not re.search(r"\b(see|slide|next)\b", full, re.I):
                    found.setdefault(ab.lower(), set()).add(full.lower())
            for ab, full in ABBR_RE2.findall(sent):
                full = tidy_full(full)
                if plausible_full(full) \
                        and not re.search(r"\b(see|slide|next)\b", full, re.I):
                    found.setdefault(ab.lower(), set()).add(full.lower())
    return {k: sorted(v) for k, v in found.items()}


# --------------------------------------------------------------------------
def discover():
    """Sorted list of (path, ext) for every source file in SOURCE_DIR."""
    out = []
    for root, _dirs, files in os.walk(SOURCE_DIR):
        for fn in sorted(files):
            if fn.lower().endswith(SOURCE_EXT) and not fn.startswith((".", "_")):
                out.append(os.path.join(root, fn))
    return sorted(out)


def label_for(path):
    fn = os.path.basename(path)
    if fn in LABELS:
        return LABELS[fn]
    return re.sub(r"\.(pdf|md|markdown)$", "", fn, flags=re.I).replace("_", " ").strip()


def main():
    assets = os.path.join(OUT_DIR, "assets")
    if os.path.isdir(assets):
        shutil.rmtree(assets)
    os.makedirs(assets)

    sources, all_cards = [], []
    for path in discover():
        # Keep card source ids aligned with data.meta.sources even when an
        # unreadable file is skipped.
        idx = len(sources)
        label = label_for(path)
        print("reading %s" % os.path.basename(path))
        if path.lower().endswith(".pdf"):
            cards = extract_pdf(path, idx, label, os.path.join(assets, "s%d" % idx))
            kind = "pdf"
        else:
            cards = extract_markdown(path, idx, label, os.path.join(assets, "s%d" % idx))
            kind = "md"
        if not cards:
            print("     !! extracted nothing — check the file")
            continue
        sources.append({"label": label, "file": os.path.basename(path),
                        "kind": kind, "n": len(cards)})
        all_cards.extend(cards)

    for i, c in enumerate(all_cards):
        c["id"] = i

    money, timeq, sects, cases = mine(all_cards)
    abbrevs = mine_abbrevs(all_cards)

    syn = {k: list(v) for k, v in SEED_SYNONYMS.items()}
    for ab, fulls in abbrevs.items():
        cur = syn.setdefault(ab, [])
        for f in fulls:
            if f not in cur:
                cur.append(f)
            syn.setdefault(f, []).append(ab)

    data = {
        "meta": {"built": datetime.now().strftime("%Y-%m-%d %H:%M"), "sources": sources},
        "cards": all_cards,
        "quick": {"money": money, "time": timeq, "sect": sects},
        "cases": cases,
        "abbrev": abbrevs,
        "syn": syn,
    }

    # ----------------------------------------------------------------------
    # Optional annotation layer: annotations.py next to this script adds
    # GLOSSARY (term -> plain-language note), SEMINAR_CN (per-source intro),
    # QUESTIONS (practice Q&A). Kept in a separate file so re-running this
    # script never overwrites hand-written content.
    # ----------------------------------------------------------------------
    try:
        import annotations
    except ImportError:
        annotations = None
    if annotations:
        apply_annotations(data, annotations)

    out = os.path.join(OUT_DIR, "data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.EXAM_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    assets_bytes = sum(os.path.getsize(os.path.join(r, fn))
                       for r, _d, fs in os.walk(assets) for fn in fs)
    print("\ncards: %d  (%s)" % (len(all_cards),
                                 ", ".join("%s=%d" % (s["label"][:18], s["n"]) for s in sources)))
    print("  money %d | time %d | sections %d | cases %d | abbrevs %d"
          % (len(money), len(timeq), len(sects), len(cases), len(abbrevs)))
    print("  data.js %.1f MB | assets %.1f MB"
          % (os.path.getsize(out) / 1e6, assets_bytes / 1e6))


def apply_annotations(data, ann):
    cards = data["cards"]

    def rx(pat):
        return re.compile(r"(?<![a-z])(?:%s)(?![a-z])" % pat, re.I)

    # entries are (regex, note) or (regex, note, seminar) — both accepted
    compiled = []
    terms = []
    for entry in getattr(ann, "GLOSSARY", []):
        source_idx = entry[2] if len(entry) > 2 else -1
        compiled.append((rx(entry[0]), entry[1], source_idx))
        terms.append({"e": clean_label(entry[0]), "c": entry[1], "s": source_idx})
    hits = 0
    for c in cards:
        hay = (c.get("t", "") or "") + " " + (c.get("txt", "") or "")
        got = []
        weighted = []
        for pat, cn, source_idx in compiled:
            if source_idx not in (-1, c.get("s")) or not pat.search(hay):
                continue
            got.append(cn)
            # (Chinese note, source index, English term matched in title)
            weighted.append([cn, source_idx, bool(pat.search(c.get("t", "") or ""))])
        if got:
            c["cn"] = got
            c["cnt"] = " ".join(got)
            c["cnh"] = weighted
            hits += 1
    data["cn"] = terms
    data["sem_cn"] = getattr(ann, "SEMINAR_CN", {})

    idx = {}
    for c in cards:
        idx.setdefault(c["s"], {})[c["p"]] = c["id"]
    quiz, broken = [], 0
    for q in getattr(ann, "QUESTIONS", []):
        refs = [idx.get(s, {}).get(p) for s, p in q.get("refs", [])]
        good = [r for r in refs if r is not None]
        broken += len(refs) - len(good)
        quiz.append({k: v for k, v in q.items() if k != "refs"})
        quiz[-1]["id"] = len(quiz) - 1
        quiz[-1]["refs"] = good
    if broken:
        print("     !! %d question refs did not resolve to a card — check "
              "source index / page numbers" % broken)
    data["quiz"] = quiz
    print("  annotations: %d/%d cards annotated, %d terms, %d questions"
          % (hits, len(cards), len(terms), len(quiz)))


def clean_label(pattern):
    """Turn a glossary regex back into a readable English label."""
    head = pattern.split("|")[0]
    head = re.sub(r"\(\?[^)]*\)", "", head)
    head = head.split("(")[0]
    head = head.replace("\\", "").strip()
    return head or pattern


if __name__ == "__main__":
    main()
