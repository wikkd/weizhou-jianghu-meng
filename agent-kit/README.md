# 苇舟江湖梦 · 文本量化分析项目

《苇舟江湖梦》（作者：霜月仲明，全文约 60 章 / 23 万字）的文本计量分析工程。
本目录已完成整理：**源文件 / 数据 / 脚本 / 产物** 四类分离，所有流水线脚本现已自动定位项目根目录，可在任意工作目录下运行。

> **🛠 Agent Kit 模式**：本目录为可开箱即用的 agent 工具包。新 agent 接管前请先阅读：
> 1. `AGENTS.md` —— 新 agent 接管指引（必读）
> 2. `WORKFLOW.md` —— 团队工作流总结
> 3. `REQUIREMENTS.md` + `setup.sh` —— 环境配置（一键）
> 4. `skills/INSTALL.md` —— 配套 skills 安装说明

## 目录结构

```
苇舟江湖梦/
├── README.md                # 本说明
├── 源文件/                  # 原始素材（只读）
│   ├── 苇舟江湖梦.docx        # 小说原稿
│   ├── reference_map.jpeg     # 内嵌参考图（示意图标定）
│   └── reference_map_grid.jpeg
├── 数据/                    # 全部数据（原始文本 + 中间产物 + 衍生 JSON）
│   ├── full_text.txt         # 从 docx 提取的纯文本（含自序与参考图注）
│   ├── chap_stats.json       # 59 章字数与段落数
│   ├── char_stats.json       # 49 个规范人物统计
│   ├── series.json           # 按章时间序列
│   ├── spatial_data.json     # 示意图标定的 33 节点坐标
│   ├── time_loc.json         # 时间-地点序列
│   ├── text_coords.json      # 纯文本派生的 19 节点坐标
│   ├── chapter_data/         # 59 章文本 + 结构化标签 + 批次标注 + 索引 + schema
│   │   ├── chap_01.txt … chap_59.txt
│   │   ├── all_tags.json      # 六批标注聚合（核心）
│   │   ├── chapters_index.json
│   │   ├── tags_batch1..6.json
│   │   └── tag_schema.md
│   └── analysis/            # 量化分析中间结果
│       ├── character_network.json
│       ├── lexical_stats.json
│       ├── stylometry.json
│       ├── sentiment_series.json
│       ├── sentiment_chart.svg
│       └── stats_inference.json
├── 脚本/                    # 26 个主流水线脚本（01–26，按执行顺序编号）+ 下划线辅助脚本
│   01_split_chapters.py … 26_organize_reports.py
└── 产物/                    # 生成的报告与归档（可重新生成）
    ├── theme.css             # 统一设计语言样式表（所有报告共享，单一来源）
    ├── 设计语言规范.md        # 设计系统说明与可复用生成提示
    ├── 报告中心/             # 统一报告展示平台（导航/筛选/iframe 查看器）
    │   ├── index.html         # 平台入口（总览网格 + 分类导航 + 查看器）
    │   ├── site.css           # 外壳样式（复用 theme.css 的设计 Token）
    │   └── app.js             # 24 份报告元数据 + 分类筛选 / 搜索 / 视图切换逻辑
    ├── 苇舟江湖梦_*.html      # 各分析报告
    ├── 川阴王建都推演.html
    ├── index.html             # 旧版静态索引（已由「报告中心」替代为首选入口）
    └── 数据归档/             # SQLite 数据库 + HTML 总览索引
```

## 流水线（建议执行顺序）

| 序号 | 脚本 | 作用 | 输入 → 输出 | 依赖 |
|------|------|------|-------------|------|
| 01 | `01_split_chapters.py` | 按章节标记切分全文 | `数据/full_text.txt` → `数据/chapter_data/chap_*.txt` + `chapters_index.json` | 仅标准库 |
| 02 | `02_aggregate_tags.py` | 聚合 6 批标注并校验 | `数据/chapter_data/tags_batch*.json` → `all_tags.json` | 仅标准库 |
| 03 | `03_run_stats.py` | 叙事假设非参检验 | `chapter_data/all_tags.json` → `数据/analysis/stats_inference.json` + `产物/…统计推断.html` | numpy, scipy |
| 04 | `04_run_stylometry.py` | 文体指纹（句长/标点/对话） | `chapter_data/` → `数据/analysis/stylometry.json` + `产物/…风格计量.html` | 仅标准库 |
| 05 | `05_lexical_analysis.py` | 词频 / TTR / 用语漂移 | `数据/full_text.txt` → `数据/analysis/lexical_stats.json` + `产物/…词汇计量.html` | jieba |
| 06 | `06_run_sentiment.py` | 逐章情感极性 | `chapter_data/` → `数据/analysis/sentiment_series.json` + `产物/…情感时序.html` | snownlp |
| 07 | `07_build_network.py` | 人物共现网络 | `chapter_data/` + `char_stats.json` → `数据/analysis/character_network.json` + `产物/…人物关系网络.html` | networkx |
| 08 | `08_generate_report.py` | 全文本量化分析报告 | `char_stats/chap_stats/series` → `产物/苇舟江湖梦_分析报告.html` | 仅标准库 |
| 09 | `09_generate_spatial_report.py` | 空间地点分析报告 | `spatial_data.json` → `产物/…空间地点分析报告.html` | 仅标准库 |
| 10 | `10_generate_guanzhi.py` | 官制考究 | （内嵌术语表）→ `产物/…官制考究.html` | 仅标准库 |
| 11 | `11_generate_text_map.py` | 纯文本地理关系图 | `text_coords.json` → `产物/…地理位置关系图.html` | 仅标准库 |
| 12 | `12_generate_tag_dashboard.py` | 章节标签量化看板 | `chapter_data/` → `产物/…章节标签量化看板.html` | 仅标准库 |
| 13 | `13_build_archive.py` | 汇总建库 + 总览索引 | 全部数据资产 → `产物/数据归档/*.db` + `总览.html` | 仅标准库 |
| 14 | `14_chapter_structure.py` | 章节结构深度量化（补盲区） | `chapter_data/all_tags.json` + `analysis/sentiment_series.json` → `产物/…章节结构量化.html` | 仅标准库 |
| 15 | `15_time_rhythm.py` | 时间节奏与空间地名量化（补盲区） | `数据/time_loc.json` → `产物/…时间节奏量化.html` | 仅标准库 |
| 16 | `16_derived_dims.py` | 派生维度量化（补盲区） | `char_stats.json` + `chapter_data/all_tags.json` → `产物/…派生维度量化.html` | 仅标准库 |

> 说明：步骤 02 的 `all_tags.json` 与 `tags_batch*.json` 为人工/subagent 标注产物，非脚本自动生成；其余数据均由流水线产出。

## 量化扩展（角色性格 / 口头禅 / 对打动作 / 地理描述）

在 01–16 受控词表体系之上，系统化扩展四类可量化维度。设计蓝图见 `产物/量化扩展_拓扑图谱与关联结构.md`，审查报告见 `产物/量化扩展_审查报告.md`。

| 步骤 | 脚本 | 维度 | 输入 → 输出 |
|---|---|---|---|
| 17 | `17_character_traits.py` | D1 角色性格特征 | `char_stats.json` + `full_text.txt` → `数据/char_traits.json`（49 角色六轴性格档案 + 原文证据） |
| 18 | `18_catchphrases.py` | D2 口头禅/标志语 | `chapter_data/all_tags.json` + `full_text.txt` → `数据/catchphrases.json`（对话归属 + 复现/特征 n-gram） |
| 19 | `19_combat_actions.py` | D3 精彩对打动作（含 D5 兵器/功法） | `all_tags.json`(战斗章) + `full_text.txt` → `数据/combat_actions.json`（动作词表/逐章/招式序列） |
| 20 | `20_geo_descriptions.py` | D4 地点地理描述 | `spatial_data.json` + `geo_features.json` + `full_text.txt` → `数据/geo_profile.json`（地形归类/要素/描述抽样） |
| 21 | `21_build_quant_reports.py` | 四份独立报告 | 上述 JSON → `产物/苇舟江湖梦_{角色性格,口头禅,对打动作,地理描述}量化.html` |
| 22 | `22_review_quant.py` | Phase 3 完整审查 | 全量 JSON → 一致性/覆盖/准确性断言 + `产物/量化扩展_审查报告.md` |

- 方法学：**自动词表抽取 + 可人审证据**（全量覆盖、精度靠抽样兜底）；单字名（影/空/福）启用否定清单排除光影/天空等泛指污染。
- 四份报告已注册进 `产物/报告中心/app.js`（分类：人物维度·语言计量·章节标注·时空地理）。
- 审查结论：一致性 / 覆盖完整性 / 准确性（证据溯源抽样）三项均 PASS；准确性为溯源核验，precision 仍需人工抽看 top 证据。

## 流水线扩展（23–26 · 叙事可视化 + 报告治理）

| 序号 | 脚本 | 作用 | 输入 → 输出 |
|---|---|---|---|
| 23 | `23_build_narrative.py` | 四维状态转移流程图（剧情/情感/空间/时间）+ Nexus 立体交叉引用 | `chapter_data/all_tags.json` → `产物/苇舟江湖梦_可视化叙事系统.html` + `数据/narrative_graphs.json` |
| 24 | `24_build_extended_viz.py` | 扩展叙事可视化（因果事件链/节奏谱/角色六维雷达/登场矩阵热力图） | `full_text.txt` + `all_tags.json` + `char_traits.json` → `产物/苇舟江湖梦_扩展叙事可视化.html` |
| 25 | `25_build_extra_viz.py` | 深度叙事可视化（伏笔回收/时空动画/文风漂移/知识图谱+MOC） | `full_text.txt` + `spatial_data.json` + `stylometry.json` → `产物/苇舟江湖梦_深度叙事可视化.html` |
| 26 | `26_organize_reports.py` | 报告归纳整理（只读盘点：主题分组/重复组/安全等级动作清单） | 扫描 `产物/` → `产物/苇舟江湖梦_报告归纳整理.html` |

> 23–25 离线依赖本地 `产物/echarts.min.js` + `产物/mermaid.min.js`（无 CDN）；26 为治理脚本，只读不删改文件。

## 可视化叙事系统（流程图 + 扩展可视化）

- **四维状态转移流程图**（剧情推进 / 情感曲线 / 空间切换 / 时间线）+ 9 章 Nexus 枢纽交叉引用：`产物/苇舟江湖梦_可视化叙事系统.html`（构建器 `脚本/23_build_narrative.py`，透明数据 `数据/narrative_graphs.json`）。支持点击节点跨图联动高亮、Nexus「◎ 立体定位」四图同步锚定。
- **扩展叙事可视化**（因果事件链 / 叙事节奏谱 / 角色六维雷达+性格谱系 / 角色登场矩阵热力图）：`产物/苇舟江湖梦_扩展叙事可视化.html`（构建器 `脚本/24_build_extended_viz.py`）。因果链回溯至 `数据/full_text.txt` 原文抽取真实因果连词；离线依赖本地 `产物/echarts.min.js` + `产物/mermaid.min.js`。
- **深度叙事可视化**（伏笔—回收网络 / 时空动画地图 / 文风漂移流图 / 知识图谱+MOC）：`产物/苇舟江湖梦_深度叙事可视化.html`（构建器 `脚本/25_build_extra_viz.py`）。伏笔连词（埋下/端倪/山雨欲来…）标 setup 章、应验连词（应验/果然/水落石出…）标 payoff 章，按共享角色跨章连边（46 条推断边 + 8 组真实例句）；时空地图用 spatial_data 坐标 + ECharts timeline 逐章动画迁移；文风用 stylometry 5 维归一化 themeRiver 流图；知识图谱聚合 角色49/地点33/关键词30/时代7 = 97 节点、95 边，附 MOC 内容地图。
- 三页互链成体系；Mermaid/ECharts 均本地 bundle，可完全离线打开。

## 报告体系与入口

产物目录当前有 25 份内容报告 + 3 个入口（**已收敛**）：

| 入口 | 数量 | 形态 | 路径 |
|---|---|---|---|
| 报告中心 | 24 | 分类筛选 + iframe 看板 | `产物/00_总览导航/index.html`（目录重组后原报告中心所在） |
| 图书馆 | 21 | SPA + tags 检索 | `产物/苇舟江湖梦_图书馆.html` |
| 顶层索引 | 3 入口+5 直达 | 简化为总入口（不再列 12 张卡片） | `产物/index.html` |

- **分类已扩展**：报告中心新增「叙事可视化 ✦」（含 4 维流程图 / 扩展 / 深度 三页），另含「报告归纳整理」治理页。
- **报告归纳整理**：25 份报告 × 3 入口 × 6 重复组的只读方案 + 4 等级动作清单：`产物/苇舟江湖梦_报告归纳整理.html`（构建器 `脚本/26_organize_reports.py`）。
- **已执行的整理动作**（按安全等级）：
  - L1 清理：`.bak` 归档 + `echarts-kit.js` 离线回退（14 份旧报告离线可用）。
  - L2 入口收敛：4 份未注册报告补登记 + 顶层索引改总入口。
  - L3-2 分析报告降级为导读（08 生成器加 8 节跳转链接 + 顶部 banner）。
  - **L3-1 空间 4→1+1**（09 加整合来源节 / 11 加 banner / 15 删 § 4）。
  - **L3-3 口头禅并入词汇：决定保持独立** —— 词汇计量聚焦词频/TTR/前后期漂移，口头禅量化聚焦角色标志语（对话归属 + 特征 n-gram），维度边界清晰，合并反而模糊报告定位；两页已在报告中心同归「语言计量」分类。
- **遗留建议**：量化扩展审查的 precision 仍需人工抽看 top 证据（见 `产物/量化扩展_审查报告.md`）。

## 运行方式

所有脚本均以 `__file__` 推导项目根目录，**无需在特定目录下执行**：

```bash
python 脚本/13_build_archive.py
```

需要第三方库的步骤（03/05/06/07）请先安装：`pip install numpy scipy jieba snownlp networkx`。

## 产物说明

- **统一报告展示平台（首选入口）**：`产物/00_总览导航/index.html`（目录重组后原「报告中心」所在）。将分散的 23 份报告整合到同一平台——左侧栏提供分类导航（总体概览 / 人物维度 / 章节标注 / 时空地理 / 语言计量 / 考据专题 / 叙事可视化）与关键词搜索；主区「总览网格」支持卡片式集中浏览与分类筛选，点击即在 iframe 查看器中打开原报告（保留各自 `theme.css` 渲染）。视觉风格、交互动效与操作逻辑全局一致，且界面响应式（窄屏侧栏转为抽屉）。
- `产物/*.html`：各维度分析报告，样式统一由 `产物/theme.css` 驱动（共享样式表，非内联），SVG 图表内联，可直接浏览器打开。设计规范见 `产物/设计语言规范.md`。
- `产物/数据归档/苇舟江湖梦_数据归档.db`：SQLite 关系库，可用 SQL 查询章节/人物/地点/分析模块。
- `产物/数据归档/苇舟江湖梦_数据归档总览.html`：统一浏览索引，链接至各报告与数据库表。
- `产物/index.html`：旧版静态索引，仅作兼容保留。
