#!/usr/bin/env bash
# 部署模型：
#   master   = 网站工程（根）+ 文学/ 工程资产（skills/脚本/数据/源文件，无产物）
#   gh-pages = master + 1 个「量化报告产物」commit（每次部署确定性重建，force-with-lease 推送）
# 日常更新：
#   1) 提交并 git push origin master
#   2) bash deploy.sh
# 产物本地来源：Desktop/image/_agentkit_stage/产物/（不可删除）
set -e
cd "$(dirname "$0")"

git push origin master

# gh-pages = master 原样 + 报告挂载；不用 rebase，容忍 master 任意重构（改名/搬迁均安全）
git checkout gh-pages
git reset --hard master

STAGE="../_agentkit_stage"
if [ -d "$STAGE/产物" ]; then
  # 深色切换后处理：生成器重写报告会冲掉注入，部署前统一补注（幂等，已注入自动跳过）
  PYBIN="${PYBIN:-python}"
  if command -v "$PYBIN" >/dev/null 2>&1; then
    "$PYBIN" "$STAGE/脚本/_harmonize_report_theme.py" || echo "WARN: 鸿蒙化(theme)失败，继续部署"
    "$PYBIN" "$STAGE/脚本/_harmonize_glass_and_pages.py" || echo "WARN: 鸿蒙化(glass/pages)失败，继续部署"
    "$PYBIN" "$STAGE/脚本/_apply_darkmode.py" || echo "WARN: 深色注入失败，继续部署（报告将缺深色切换）"
  else
    echo "WARN: 未找到 python，跳过深色注入"
  fi
  /usr/bin/rm -rf 文学/产物
  cp -r "$STAGE/产物" 文学/产物
  git add -f 文学/产物
  if ! git diff --cached --quiet; then
    git commit -m "chore(gh-pages): 挂载量化报告产物"
  fi
else
  echo "WARN: 未找到 $STAGE/产物，跳过产物挂载（线上报告不会更新）"
fi

# 报告提交每次重建都会改写哈希，部署分支仅本脚本维护，force-with-lease 安全
git push --force-with-lease origin gh-pages
git checkout master
echo "deploy done."
