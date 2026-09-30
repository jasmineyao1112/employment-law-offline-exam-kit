#!/bin/bash
set -u

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT_DIR" || exit 1

finish() {
  printf '\n按 Enter 键关闭此窗口。'
  read -r _
}
trap finish EXIT

if ! command -v python3 >/dev/null 2>&1; then
  printf '未找到 Python 3。请先从 https://www.python.org/downloads/macos/ 安装 Python 3。\n'
  exit 1
fi

PYTHON_BIN="python3"
if ! "$PYTHON_BIN" -c 'import fitz' >/dev/null 2>&1; then
  if [ ! -x "$KIT_DIR/.venv/bin/python" ]; then
    printf '正在创建本地 Python 环境……\n'
    "$PYTHON_BIN" -m venv "$KIT_DIR/.venv" || exit 1
  fi
  PYTHON_BIN="$KIT_DIR/.venv/bin/python"
  if ! "$PYTHON_BIN" -c 'import fitz' >/dev/null 2>&1; then
    printf '首次安装 PyMuPDF（此步骤需要网络，考试当天不需要）……\n'
    if ! "$PYTHON_BIN" -m pip install --disable-pip-version-check -r "$KIT_DIR/requirements.txt"; then
      printf '\nPyMuPDF 安装失败，但已经生成的 index.html 和 data.js 不受影响。\n'
      printf '如果 02 可以打开、03 自检通过，考试当天仍可正常使用现有资料库。\n'
      exit 1
    fi
  fi
fi

printf '正在读取 materials 并构建离线索引……\n\n'
SOURCE_DIR="$KIT_DIR/materials" "$PYTHON_BIN" "$KIT_DIR/build_index.py" || exit 1

printf '\n构建完成。正在打开离线页面……\n'
open "$KIT_DIR/index.html"
