#!/usr/bin/env bash
# 部署流程说明：
#   master   = 站点 + agent-kit 工程资产（skills/脚本/数据/源文件，无产物）
#   gh-pages = master + 1 个「量化报告产物」commit（产物不进 master，见 .gitignore）
# 日常更新：
#   1) 提交并 git push origin master
#   2) bash deploy.sh   # gh-pages rebase 到新 master，重挂产物，推送上线
set -e
cd "$(dirname "$0")"

git push origin master

git checkout gh-pages
git rebase master

STAGE="../_agentkit_stage"
if [ -d "$STAGE/产物" ]; then
  /usr/bin/rm -rf agent-kit/产物
  cp -r "$STAGE/产物" agent-kit/产物
  git add -f agent-kit/产物
  if ! git diff --cached --quiet; then
    git commit -m "chore(gh-pages): 挂载量化报告产物"
  fi
else
  echo "WARN: 未找到 $STAGE/产物，跳过产物挂载（线上报告不会更新）"
fi

git push origin gh-pages
git checkout master
echo "deploy done."
