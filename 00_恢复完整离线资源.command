#!/bin/bash
set -u

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESOURCE_DIR="$KIT_DIR/resources"
ARCHIVE="$RESOURCE_DIR/offline-resources.zip"

if [ -f "$KIT_DIR/assets/s8/014.jpg" ] && [ -d "$KIT_DIR/materials" ]; then
  exit 0
fi

if ! ls "$RESOURCE_DIR"/offline-resources.part-* >/dev/null 2>&1; then
  osascript -e 'display alert "缺少离线资源包" message "请确认 resources 文件夹没有被移动或删除。" as critical' 2>/dev/null
  exit 1
fi

printf '正在恢复完整离线资料（首次运行约需一分钟）……\n'
cat "$RESOURCE_DIR"/offline-resources.part-* > "$ARCHIVE" || exit 1
if ! unzip -q -o "$ARCHIVE" -d "$KIT_DIR"; then
  rm -f "$ARCHIVE"
  printf '资源恢复失败。请重新下载完整仓库 ZIP 后再试。\n'
  exit 1
fi
rm -f "$ARCHIVE"
printf '恢复完成。\n'
