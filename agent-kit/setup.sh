#!/usr/bin/env bash
# =============================================================
# 苇舟江湖梦 · Agent Kit · 环境一键配置脚本（macOS / Linux）
# 用法:
#   bash setup.sh             # 创建 venv 并安装依赖
#   bash setup.sh --verify    # 校验环境与工程完整性
#   bash setup.sh --with-skills  # 安装依赖 + 可选安装配套 skills
# =============================================================
set -euo pipefail

# 脚本所在目录即项目根（工具包解压后运行）
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT/.venv"
PYTHON_BIN="${PYTHON:-python3}"

info()  { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
ok()    { printf "\033[1;32m[ OK ]\033[0m %s\n" "$*"; }
warn()  { printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
err()   { printf "\033[1;31m[FAIL]\033[0m %s\n" "$*" >&2; exit 1; }

verify_python() {
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    err "未找到 $PYTHON_BIN，请安装 Python 3.10+（macOS: brew install python）"
  fi
  local v
  v="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  info "检测到 Python $v"
  if [[ "$(printf '%s\n%s' '3.10' "$v" | sort -V | head -1)" != '3.10' ]]; then
    err "需要 Python >= 3.10，当前 $v"
  fi
  PYTHON_BIN="$("$PYTHON_BIN" -c 'import sys; print(sys.executable)')"
}

setup_venv() {
  if [[ -x "$VENV_DIR/bin/python" ]]; then
    info "复用已有虚拟环境: $VENV_DIR"
  else
    info "创建虚拟环境: $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  ok "虚拟环境就绪"
}

install_deps() {
  info "安装依赖（requirements.txt）…"
  "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
  if "$VENV_DIR/bin/pip" install -r "$ROOT/requirements.txt"; then
    ok "依赖安装完成"
  else
    warn "默认源安装失败（常见于镜像 403），回退官方源 pypi.org 重试…"
    "$VENV_DIR/bin/pip" install --index-url https://pypi.org/simple -r "$ROOT/requirements.txt"
    ok "依赖安装完成（官方源）"
  fi
}

verify_all() {
  info "校验 Python 依赖…"
  local missing=()
  for mod in numpy scipy jieba snownlp networkx; do
    if "$VENV_DIR/bin/python" -c "import $mod" >/dev/null 2>&1; then
      ok "  依赖 $mod ✓"
    else
      missing+=("$mod")
    fi
  done
  [[ ${#missing[@]} -gt 0 ]] && err "缺少依赖: ${missing[*]} —— 请运行 bash setup.sh"

  info "校验关键数据文件…"
  local required=(
    "数据/full_text.txt"
    "数据/chapter_data/all_tags.json"
    "数据/char_stats.json"
    "脚本/01_split_chapters.py"
    "脚本/13_build_archive.py"
    "产物/theme.css"
  )
  for f in "${required[@]}"; do
    [[ -f "$ROOT/$f" ]] && ok "  文件 $f ✓" || warn "  缺失 $f（可重跑流水线生成）"
  done

  info "校验公共辅助模块可导入…"
  (cd "$ROOT" && "$VENV_DIR/bin/python" -c "import sys; sys.path.insert(0, '脚本'); import _quant_common; print('  _quant_common ✓ ROOT =', _quant_common.ROOT)")
  ok "工程完整性校验通过"
}

install_skills() {
  if [[ -d "$ROOT/skills" ]]; then
    info "安装配套 skills → ~/.workbuddy/skills/"
    bash "$ROOT/skills/install_skills.sh" --to "$HOME/.workbuddy/skills"
  else
    warn "未找到 skills/ 目录，跳过"
  fi
}

# ---------------- main ----------------
MODE="setup"
for arg in "$@"; do
  case "$arg" in
    --verify) MODE="verify" ;;
    --with-skills) WITH_SKILLS=1 ;;
    *) warn "未知参数: $arg（忽略）" ;;
  esac
done

verify_python

case "$MODE" in
  setup)
    setup_venv
    install_deps
    if [[ "${WITH_SKILLS:-}" == "1" ]]; then install_skills; fi
    info "配置完成。验证: bash setup.sh --verify"
    info "冒烟测试: $VENV_DIR/bin/python 脚本/13_build_archive.py"
    ;;
  verify)
    setup_venv
    verify_all
    ;;
esac
