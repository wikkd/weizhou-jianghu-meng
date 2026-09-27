# 苇舟江湖梦 · 知识索引与诗图工程

线上：https://wikkd.github.io/weizhou-jianghu-meng/ ｜ 仓库：github.com/wikkd/weizhou-jianghu-meng

## 文档与资产分类

### A. 线上站点页面（gh-pages 可访问）
| 路径 | 内容 |
|---|---|
| `index.html` | 项目入口主页（导航/统计/诗词撷英） |
| `kb.html` | 知识性索引数据库（人物/章节/关系/检索五视图） |
| `poems/poem_gallery.html` | 9 首角色诗图对照画廊 |
| `agent-kit/产物/00_总览导航/index.html` | 量化报告总览（仅 gh-pages 存在） |

### B. 站点构建工程（master）
| 文件 | 职责 |
|---|---|
| `build_kb.py` | docx → knowledge_base.json + CSV（解析层） |
| `build_html.py` / `build_home.py` / `build_poem_gallery.py` | 生成 kb.html / index.html / 诗图画廊 |
| `deploy.sh` | 一键部署：gh-pages rebase master + 重挂报告产物 |
| `UI_SPEC.md` | 鸿蒙风格 UI 设计规格（双主题/字体/三页改造） |
| `README.md` | 本文件 |

### C. 站点数据层（master）
`knowledge_base.json`（63 章/33 人/234 边）· `chapters.csv` · `characters.csv` · `poems.json`

### D. Agent-Kit 工程资产（agent-kit/，8 月产线并入）
| 子目录/文件 | 内容 |
|---|---|
| `skills/` | 8 个 skill（darwin / generate-chart / data-analysis-plus / html-report-keyword-index / mermaid-diagram / browser-use / deep-research / kimi-websearch） |
| `脚本/` | 01–26 主线分析脚本 + `_upgrade/_rebuild/_chartlib` 等辅助 |
| `数据/` | full_text.txt、60 章分章 txt、章节标签、词汇/情感/风格/网络/地理分析 JSON |
| `源文件/` | 苇舟江湖梦.docx、参考地图 jpeg |
| 根文档 | README / AGENTS / PROMPT / WORKFLOW / REQUIREMENTS / setup.sh·ps1 / requirements.txt |

### E. 量化报告产物（agent-kit/产物/，仅 gh-pages；本地来源 `_agentkit_stage/产物/`）
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

- **master** = 站点 + agent-kit 工程资产（`.gitignore` 屏蔽 `agent-kit/产物/`）
- **gh-pages** = master + 1 个「量化报告产物」commit
- 日常更新：提交 master → `bash deploy.sh`（产物来源 `Desktop/image/_agentkit_stage/产物/`，该目录不可删）
