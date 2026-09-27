#!/usr/bin/env bash
# =============================================================
# 苇舟江湖梦 · Agent Kit · skills 一键安装脚本
# 用法:
#   bash install_skills.sh --to <目标目录> [--force]
#   默认目标: ~/.workbuddy/skills
# 行为: 复制 skills/0X-* 到目标目录；同名已存在则跳过（--force 强制覆盖）
# =============================================================
set -euo pipefail

# 本脚本所在目录 = skills/ 目录
SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HOME}/.workbuddy/skills"
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to) DEST="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    *) echo "[WARN] 未知参数: $1（忽略）"; shift ;;
  esac
done

[[ -d "$DEST" ]] || mkdir -p "$DEST"

echo "[INFO] 安装目标: $DEST"
installed=0; skipped=0
for src in "$SKILLS_DIR"/0*-*/; do
  [[ -d "$src" ]] || continue
  name="$(basename "$src")"
  # 去掉 0X- 前缀作为实际 skill 名
  real="${name#0?-}"
  target="$DEST/$real"
  if [[ -d "$target" && "$FORCE" == "0" ]]; then
    echo "[SKIP] $real 已存在（--force 可覆盖）"
    skipped=$((skipped+1))
    continue
  fi
  if [[ -d "$target" ]]; then
    rm -rf "$target"
  fi
  cp -R "$src" "$target"
  echo "[ OK ] 安装 $real → $target"
  installed=$((installed+1))
done

echo "[INFO] 完成：安装 $installed 个，跳过 $skipped 个"
if [[ $installed -eq 0 && $skipped -eq 0 ]]; then
  echo "[WARN] skills/ 下未发现 0X-* skill 目录"
fi
exit 0
