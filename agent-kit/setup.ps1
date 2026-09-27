# =============================================================
# 苇舟江湖梦 · Agent Kit · 环境一键配置脚本（Windows / PowerShell）
# 用法:
#   .\setup.ps1              # 创建 venv 并安装依赖
#   .\setup.ps1 -Verify      # 校验环境与工程完整性
# =============================================================
param(
    [switch]$Verify,
    [switch]$WithSkills
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$VenvDir = Join-Path $Root ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

function Info  { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Ok    { Write-Host "[ OK ] $args" -ForegroundColor Green }
function Warn  { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Fail  { Write-Host "[FAIL] $args" -ForegroundColor Red; exit 1 }

# ---------- Python 检测 ----------
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Fail "未找到 python，请安装 Python 3.10+（python.org，勾选 Add to PATH）" }
$ver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Info "检测到 Python $ver"
if ([version]$ver -lt [version]"3.10") { Fail "需要 Python >= 3.10，当前 $ver" }

# ---------- venv ----------
if (-not (Test-Path $VenvPython)) {
    Info "创建虚拟环境: $VenvDir"
    & python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { Fail "venv 创建失败" }
}
Ok "虚拟环境就绪"

# ---------- 安装依赖 ----------
Info "安装依赖（requirements.txt）…"
& $VenvPython -m pip install --upgrade pip | Out-Null
& $VenvPython -m pip install -r (Join-Path $Root "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    Warn "默认源安装失败（常见于镜像 403），回退官方源 pypi.org 重试…"
    & $VenvPython -m pip install --index-url https://pypi.org/simple -r (Join-Path $Root "requirements.txt")
    if ($LASTEXITCODE -ne 0) { Fail "依赖安装失败" }
}
Ok "依赖安装完成"

# ---------- 校验 ----------
if ($Verify) {
    Info "校验 Python 依赖…"
    $missing = @()
    foreach ($mod in @("numpy","scipy","jieba","snownlp","networkx")) {
        & $VenvPython -c "import $mod" 2>$null
        if ($LASTEXITCODE -eq 0) { Ok "  依赖 $mod ✓" } else { $missing += $mod }
    }
    if ($missing.Count -gt 0) { Fail "缺少依赖: $($missing -join ', ') —— 请重新运行 setup.ps1" }

    Info "校验关键数据文件…"
    $required = @(
        "数据\full_text.txt",
        "数据\chapter_data\all_tags.json",
        "数据\char_stats.json",
        "脚本\01_split_chapters.py",
        "脚本\13_build_archive.py",
        "产物\theme.css"
    )
    foreach ($f in $required) {
        if (Test-Path (Join-Path $Root $f)) { Ok "  文件 $f ✓" } else { Warn "  缺失 $f（可重跑流水线生成）" }
    }
    Ok "工程完整性校验通过"
}

# ---------- skills ----------
if ($WithSkills) {
    $skillInstaller = Join-Path $Root "skills\install_skills.sh"
    if (Test-Path $skillInstaller) {
        Info "skills 安装请参考 skills\INSTALL.md（本机可运行 WSL/bash 执行 install_skills.sh）"
    }
}

Info "配置完成。验证: .\setup.ps1 -Verify"
Info "冒烟测试: & .\.venv\Scripts\python.exe 脚本\13_build_archive.py"
