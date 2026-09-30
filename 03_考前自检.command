#!/bin/bash
set -u

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT_DIR" || exit 1

python3 - "$KIT_DIR" <<'PY'
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
errors = []
warnings = []

for name in ("index.html", "data.js", "build_index.py"):
    if not (root / name).is_file():
        errors.append(f"缺少 {name}")

cards = []
sources = []
if (root / "data.js").is_file():
    raw = (root / "data.js").read_text(encoding="utf-8")
    prefix = "window.EXAM_DATA = "
    if not raw.startswith(prefix) or not raw.rstrip().endswith(";"):
        errors.append("data.js 格式不正确")
    else:
        try:
            data = json.loads(raw[len(prefix):].rstrip()[:-1])
            cards = data.get("cards", [])
            sources = data.get("meta", {}).get("sources", [])
        except Exception as exc:
            errors.append(f"data.js 无法解析：{exc}")

missing = []
for card in cards:
    for key in ("img",):
        rel = card.get(key)
        if rel and not (root / rel).is_file():
            missing.append(rel)
    for rel in card.get("imgs") or []:
        if rel and not (root / rel).is_file():
            missing.append(rel)
if missing:
    errors.append(f"缺少 {len(missing)} 张引用图片（例如 {missing[0]}）")

html = (root / "index.html").read_text(encoding="utf-8") if (root / "index.html").is_file() else ""
remote = re.findall(r'''(?:src|href)=["']https?://[^"']+''', html, re.I)
if remote:
    errors.append(f"HTML 含 {len(remote)} 个外部资源引用")
if '<script src="data.js"></script>' not in html:
    errors.append("index.html 未加载 data.js")
if not cards:
    warnings.append("索引中没有卡片：请确认 materials 内已有可读取的 PDF/Markdown，并重新构建")

asset_count = sum(1 for p in (root / "assets").rglob("*") if p.is_file()) if (root / "assets").exists() else 0
print("离线考试资料库自检")
print("=" * 24)
print(f"sources: {len(sources)}")
print(f"cards: {len(cards)}")
print(f"assets: {asset_count}")
print(f"missing images: {len(missing)}")
print(f"external HTML references: {len(remote)}")

for warning in warnings:
    print(f"警告：{warning}")
for error in errors:
    print(f"错误：{error}")

if errors:
    print("\n结论：未通过，请先修正错误。")
    raise SystemExit(1)
print("\n结论：通过。仍请在正式考试相同设置的 mock exam 中实际打开测试。")
PY

STATUS=$?
printf '\n按 Enter 键关闭此窗口。'
read -r _
exit "$STATUS"

