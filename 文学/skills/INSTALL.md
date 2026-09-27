# skills/INSTALL.md · Skill 安装说明

本工具包随附 8 个与本项目工作流直接相关的 skills（已打包，位于 `skills/` 下）。
安装后 agent 可调用它们完成对应任务；**不安装也能运行全部流水线**（skills 是增强，非必需）。

## 1. 随附 skills 一览

| 目录 | Skill | 在本项目中的用途 | 来源 |
|---|---|---|---|
| `01-darwin-skill` | darwin-skill | 报告/技能迭代的"评估→改进→实测→保留"棘轮纪律 | 开源（GitHub: alchaincyf/darwin-skill） |
| `02-generate-chart` | 数据可视化 | 生成交互式 HTML 仪表板/图表 | skillhub |
| `03-data-analysis-plus` | 数据分析大师 | 数据采集、整合、解读方法论 | skillhub |
| `04-html-report-keyword-index` | 关键词索引 | 构建"关键词→原文"交叉索引（对应产物/关键词索引.json） | 自建 |
| `05-mermaid-diagram` | Mermaid 图 | 流程图/时序图/架构图（报告内嵌图谱） | skillhub |
| `06-browser-use` | 浏览器自动化 | 无头浏览器渲染验证、报告截图实测 | 自建/通用 |
| `07-deep-research` | 深度调研 | 考据类任务（人物调查、官制考究等） | 自建 |
| `08-kimi-websearch` | Kimi 联网搜索 | 补充实时信息检索 | skillhub |

> 各 skill 目录内 `SKILL.md` 为入口，附带的 `_skillhub_meta.json` / `README*` 为元数据与说明，可一并保留。

## 2. 安装方式

### 方式 A：一键脚本（推荐，macOS / Linux）

```bash
bash skills/install_skills.sh --to ~/.workbuddy/skills
```

- 默认目标：用户级 `~/.workbuddy/skills`（跨项目可用）。
- 也可装到项目级：`--to .workbuddy/skills`（仅本项目可用）。
- 若目标已存在同名 skill，会**跳过并警告**（不覆盖你的现有配置）；如需强制覆盖加 `--force`。

### 方式 B：手动复制

把需要的 `skills/0X-*` 目录复制到目标 skills 目录（保持目录内的 `SKILL.md` 相对结构）：

```bash
mkdir -p ~/.workbuddy/skills/01-darwin-skill
cp -R skills/01-darwin-skill/* ~/.workbuddy/skills/01-darwin-skill/
# ……其余同理
```

### 方式 C：Windows

推荐在 WSL / Git Bash 中执行 `bash skills/install_skills.sh`；或手动复制目录到
`C:\Users\<用户名>\.workbuddy\skills\`。

## 3. 可选扩展 skills（未打包，按需自行安装）

以下 skills 与本项目弱相关，需要时再装：

- `write` / `humanizer`：报告文案润色、去除 AI 腔。
- `html-deploy`：将单页 HTML 发布为公开链接。
- `interactive-architecture-diagram`（ContextWeave）：架构图/流程图生成。
- `markitdown-skill` / `pdf-image-text-extractor`：docx/PDF/图片转 Markdown 文本。
- `memory-manager-v2`：工作记忆压缩管理。

## 4. 卸载

删除对应目录即可，例如：`rm -rf ~/.workbuddy/skills/02-generate-chart`（个人目录操作请谨慎，建议先移入废纸篓）。

## 5. 注意事项

- **许可证**：随附 skills 均来自开源或 skillhub 公开来源，保留原 `_skillhub_meta.json` 与 README 即可合规复用；商用前请复核各来源许可。
- **敏感信息**：skills 目录内不含任何密钥/凭据；连接器类能力（kdocs 文档同步等）不在本工具包内，需接收方自行配置授权。
