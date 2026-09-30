#!/bin/bash
set -u

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "$KIT_DIR/data.js" ]; then
  osascript -e 'display alert "尚未构建资料库" message "请先双击 01_构建考试资料库.command" as critical' 2>/dev/null
  exit 1
fi

if [ ! -d "$KIT_DIR/assets" ] || [ ! -d "$KIT_DIR/materials" ]; then
  "$KIT_DIR/00_恢复完整离线资源.command" || exit 1
fi

open "$KIT_DIR/index.html"
