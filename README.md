# 苇舟江湖梦 · 知识索引与诗图工程

线上：https://wikkd.github.io/weizhou-jianghu-meng/ ｜ 仓库：github.com/wikkd/weizhou-jianghu-meng

## 项目双域结构（2026-09-27 分离定稿）

```
├── 网站工程（仓库根）
│   ├── 页面：index.html / kb.html / poems/ / wiki/ / docs/
│   ├── 数据：knowledge_base.json / chapters.csv / characters.csv / poems.json
│   ├── 构建：build_kb.py / build_html.py / build_home.py / build_poem_gallery.py
│   │         / build_wiki.py / build_docs.py
│   ├── 资产：assets/（theme.css 设计令牌 + 动效令牌、icons/ 官方图标、fonts/ 内嵌鸿蒙字体、favicon.svg）
│   ├── 治理：README.md / CHARTER.md / DEV_RULES.md / MOTION_SPEC.md / UI_SPEC.md / WIKI_SPEC.md
│   │         （均已站点化为 docs/ 页面，md 为单一事实源）
│   └── 运维：deploy.sh / .gitignore
└── 文学/（原 agent-kit，内部结构保持产线原样）
    ├── 源文件/ ：苇舟江湖梦.docx、参考地图
    ├── 数据/   ：full_text.txt、60 章分章 txt、章节标签、分析 JSON
    ├── 脚本/   ：01–26 主线分析脚本 + 辅助脚本（ROOT 约定：数据/产物/源文件必须与本目录同级）
    ├── skills/ ：8 个分析 skill
    ├── 根文档  ：README / AGENTS / PROMPT / WORKFLOW / REQUIREMENTS / setup.*
    └── 产物/   ：量化报告（仅 gh-pages 存在，master 上被 .gitignore 屏蔽）
```

> ⚠️ `文学/脚本/` 内 46 个脚本按 `ROOT=脚本上级目录` 取数，`数据/`、`产物/`、`源文件/` 必须与 `脚本/` 保持同父级，拆散会断产线。

## 文档与资产分类

### A. 线上站点页面（gh-pages 可访问）
| 路径 | 内容 |
|---|---|
| `index.html` | 项目入口主页（鸿蒙双主题，导航/搜索/统计/Wiki 结构总览） |
| `kb.html` | 知识性索引数据库（人物/章节/关系/检索五视图） |
| `wiki/` | Wiki 词条（总目录 + 人物/章节等命名空间词条，构建期生成） |
| `docs/` | 工程文档站点化版本（6 份治理文档，构建期生成） |
| `poems/poem_gallery.html` | 9 首角色诗图对照画廊 |
| `文学/产物/00_总览导航/index.html` | 量化报告总览（仅 gh-pages 存在） |

### B. 网站工程（仓库根）
| 文件 | 职责 |
|---|---|
| `build_kb.py` | docx → knowledge_base.json + CSV（解析层） |
| `build_html.py` / `build_home.py` / `build_poem_gallery.py` | 生成 kb.html / index.html / 诗图画廊 |
| `build_wiki.py` | content/*.md → wiki/ 静态词条（纯标准库，规格见 WIKI_SPEC.md） |
| `build_docs.py` | 治理 md → docs/ 文档页（纯标准库 Markdown 子集渲染器） |
| `deploy.sh` | 一键部署：gh-pages 确定性重建 = master + 报告挂载 |
| `CHARTER.md` / `DEV_RULES.md` / `MOTION_SPEC.md` | 治理三层：章程 → 守则 → 动效细则 |
| `UI_SPEC.md` / `WIKI_SPEC.md` | 设计系统 / Wiki 架构规格 |
| `README.md` | 本文件 |

### C. 站点数据层（仓库根）
`knowledge_base.json`（63 章/33 人/234 边）· `chapters.csv` · `characters.csv` · `poems.json`

### D. 文学工程资产（文学/，8 月产线并入）
| 子目录/文件 | 内容 |
|---|---|
| `skills/` | 8 个 skill（darwin / generate-chart / data-analysis-plus / html-report-keyword-index / mermaid-diagram / browser-use / deep-research / kimi-websearch） |
| `脚本/` | 01–26 主线分析脚本 + `_upgrade/_rebuild/_chartlib` 等辅助 |
| `数据/` | full_text.txt、60 章分章 txt、章节标签、词汇/情感/风格/网络/地理分析 JSON |
| `源文件/` | 苇舟江湖梦.docx、参考地图 jpeg |
| 根文档 | README / AGENTS / PROMPT / WORKFLOW / REQUIREMENTS / setup.sh·ps1 / requirements.txt |

### E. 量化报告产物（文学/产物/，仅 gh-pages；本地来源 `_agentkit_stage/产物/`）
| 分类 | 报告 |
|---|---|
| 00 总览导航 | 报告归纳整理、分析报告、原文阅读、图书馆、组件库、美学图谱、关键词索引 |
| 01 文本语言 | 词汇计量、风格计量 |
| 02 叙事情感 | 可视化叙事系统、情感时序、扩展/深度叙事、时间节奏、派生维度、章节标签看板、章节结构 |
| 03 人物社会 | 人物关系网络、韩德人物考究、角色性格、对打动作、口头禅、统计推断 |
| 04 空间地理 | 地理描述量化、地理位置关系图、空间地点分析 |
| 05 制度家族 | 官制考究、黄家概况、川阴王建都推演 |
| 数据归档 | 数据归档 db + 总览页 |
| 支撑资源 | 设计语言规范、量化扩展审查报告、拓扑图谱与关联结构 |

### F. 工作记忆（本地，不入库）
`.workbuddy/memory/`：当日工作日志 + 项目长期备注（MEMORY.md）

## 部署模型

- **master** = 网站工程（根）+ `文学/` 工程资产（`.gitignore` 屏蔽 `文学/产物/`）
- **gh-pages** = master 原样 + 1 个「量化报告产物」commit（每次部署确定性重建，force-with-lease 推送）
- 日常更新：提交 master → `bash deploy.sh`（产物来源 `Desktop/image/_agentkit_stage/产物/`，该目录不可删）
