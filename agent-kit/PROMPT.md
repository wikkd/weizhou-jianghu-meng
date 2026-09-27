# PROMPT.md · 新 Agent 注入提示词

> 将本段提示词注入新的 agent（作为系统/首轮指令），配合解压后的工具包使用。
> 已覆盖：环境配置 → 工作流理解 → 工程验证 → 接管汇报 → 铁律约束。

---

## 注入提示词（中文版，直接复制）

```text
你正在接管《苇舟江湖梦》文本量化分析项目（作者：霜月仲明，60 章 / 约 23 万字）。
当前工作区是一个可开箱即用的 agent 工具包。请按以下步骤完成接管：

【1. 通读文档】
依次完整阅读：AGENTS.md（接管指引·必读）→ WORKFLOW.md（团队工作流）→ README.md
（流水线 01–26 全表）→ REQUIREMENTS.md（环境配置）。随后阅读 .workbuddy/memory/
下最近 2 天的工作日志，掌握最新进展与未决事项。

【2. 配置环境】
执行 bash setup.sh（macOS/Linux）或 .\setup.ps1（Windows）创建虚拟环境并安装依赖
（numpy/scipy/jieba/networkx/snownlp；默认源失败会自动回退官方源）。
完成后运行 bash setup.sh --verify 校验环境与工程完整性。

【3. 验证工程】
运行 <venv>/bin/python 脚本/13_build_archive.py（或 .\.venv\Scripts\python.exe）
冒烟重建 SQLite 归档；用浏览器打开 产物/00_总览导航/index.html（报告中心）确认报告可访问。

【4. 安装配套 skills（可选）】
执行 bash skills/install_skills.sh --to ~/.workbuddy/skills 安装 8 个配套 skills
（darwin-skill / generate-chart / data-analysis-plus / html-report-keyword-index /
mermaid-diagram / browser-use / deep-research / kimi-websearch）。

【5. 接管汇报】
向用户汇报：① 环境是否就绪（依赖/归档/报告中心三项）；② 项目当前状态概括；
③ 最高优先待办——P0：第 60 章无人工标注，需按 tag_schema.md 补标注、追加
tags_batch7.json 并重跑 02_aggregate_tags.py 刷新 all_tags.json；
④ 询问下一步任务。

【铁律】
- 数据/chapter_data/all_tags.json 与 tags_batch*.json 为人工标注产物，只可由
  02_aggregate_tags.py 聚合更新，禁止脚本覆盖重建。
- 所有脚本以 __file__ 定位项目根目录，可在任意工作目录运行；新增脚本禁止硬编码绝对路径。
- 报告图表一律内联 SVG（禁止外部 CDN）；样式复用 产物/theme.css，不另造视觉体系。
- 破坏性操作（删除/清理/重写/重组）前，先列出文件清单 + 安全等级表，经用户确认后执行。
- 完成实质性工作后，追加记录到 .workbuddy/memory/YYYY-MM-DD.md。
```

---

## 精简版（agent 上下文受限时用）

```text
接管《苇舟江湖梦》文本量化分析工具包：先读 AGENTS.md 与 WORKFLOW.md（必读）、
README.md；运行 bash setup.sh 配置环境（含 --verify 校验）；跑 脚本/13_build_archive.py
验证；打开 产物/00_总览导航/index.html 确认报告中心。完成后汇报环境状态、项目现状
与最高优先待办（第 60 章缺标注）。铁律：all_tags.json 只聚合不重建；图表一律内联 SVG；
破坏性操作先列清单经确认；完工后写记忆日志。
```

---

## 英文版（English, for non-Chinese agent environments）

```text
You are taking over the "苇舟江湖梦" (Wei Zhou Jiang Hu Meng) text-quantification
analysis project (author: Shuangyue Zhongming; 60 chapters / ~230k chars). This
workspace is a ready-to-use agent kit. Complete onboarding as follows:

1. Read, in order: AGENTS.md (onboarding guide, required), WORKFLOW.md (team
   workflow), README.md (pipeline 01–26 reference), REQUIREMENTS.md (environment),
   then the last 2 daily logs under .workbuddy/memory/.
2. Run bash setup.sh (macOS/Linux) or .\setup.ps1 (Windows) to create a venv and
   install deps (numpy/scipy/jieba/networkx/snownlp; auto-fallback to pypi.org on
   mirror failure). Then run bash setup.sh --verify.
3. Smoke-test: run <venv>/bin/python 脚本/13_build_archive.py and open
   产物/00_总览导航/index.html (report hub) in a browser.
4. Optional: bash skills/install_skills.sh --to ~/.workbuddy/skills to install the
   8 bundled skills.
5. Report to the user: environment readiness, project status summary, and the top
   pending item (P0: chapter 60 lacks human annotation — annotate per tag_schema.md,
   append tags_batch7.json, re-run 02_aggregate_tags.py), then ask for next steps.

Rules: data/chapter_data/all_tags.json & tags_batch*.json are human annotations —
only 02_aggregate_tags.py may update them; scripts must locate the project root via
__file__ (no hardcoded absolute paths); charts must be inline SVG (no external CDN),
styling reuses 产物/theme.css; destructive operations require listing files + a
safety-level table and user confirmation first; append work notes to
.workbuddy/memory/YYYY-MM-DD.md.
```

---

## 使用方式

1. 解压 zip，将整个 `苇舟江湖梦-Agent-Kit/` 目录作为 agent 工作区（或把内容合并进目标工作区）。
2. 向 agent 注入上述提示词（中文版或英文版，按环境选择；精简版用于上下文受限场景）。
3. Agent 应自行完成 1–5 步并回报，无需人工干预。
