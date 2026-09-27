# REQUIREMENTS.md · 环境配置说明

## 1. 运行时要求

| 组件 | 版本 | 说明 |
|---|---|---|
| Python | ≥ 3.10（推荐 3.12+） | 全部脚本基于标准库 + 4 个第三方包 |
| 浏览器（可选） | 任意现代浏览器 | 仅用于打开 HTML 报告；无头 Chrome 用于渲染验证 |
| 操作系统 | macOS / Linux / Windows | setup.sh（macOS/Linux）与 setup.ps1（Windows）均已提供 |
| 磁盘 | ≥ 200 MB | 产物含离线 JS bundle（echarts/mermaid）与 SQLite 库 |

## 2. Python 依赖（requirements.txt）

| 包 | 用途 | 使用脚本 |
|---|---|---|
| numpy | 数值计算 | 03_run_stats.py |
| scipy | 非参统计检验 | 03_run_stats.py |
| jieba | 中文分词 / 词频 / TTR | 05_lexical_analysis.py |
| snownlp | 情感极性分析 | 06_run_sentiment.py |
| networkx | 人物共现网络 / 社区发现 | 07_build_network.py |
| python-docx（可选） | docx 读取/重建（文档同步工作流） | 手动任务 |
| Pillow（可选） | docx 内嵌图片重编码 | 手动任务 |

> 26 个主脚本中仅 03/05/06/07 依赖第三方库，其余仅标准库。

## 3. 一键配置（推荐）

```bash
# macOS / Linux
bash setup.sh                # 创建 .venv 并安装全部依赖
bash setup.sh --verify       # 校验环境 + 工程完整性

# Windows（PowerShell）
.\setup.ps1
.\setup.ps1 -Verify
```

脚本行为：
1. 检测 Python 3.10+（未找到则报错并给出安装指引）。
2. 在项目根创建 `.venv` 虚拟环境（已存在则复用）。
3. 用 `.venv` 的 pip 安装 `requirements.txt`。
4. `--verify`：逐项校验依赖可导入、关键数据文件存在、`_quant_common` 可导入。

## 4. 手动配置（不使用脚本时）

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 5. 环境变量

本项目**无需任何环境变量**。所有路径由脚本通过 `__file__` 自动推导项目根目录，在任意工作目录下运行均可：

```bash
python 脚本/13_build_archive.py    # 任意 cwd 均可
```

## 6. 运行验证（冒烟测试）

```bash
# 1) 重建数据归档（覆盖全部数据资产 → SQLite）
.venv/bin/python 脚本/13_build_archive.py

# 2) 打开报告中心（00_总览导航 = 原报告中心入口）
open 产物/00_总览导航/index.html      # macOS
# Windows: start 产物\00_总览导航\index.html
```

预期：`产物/数据归档/苇舟江湖梦_数据归档.db` 生成/更新，报告中心浏览器可打开、图表正常渲染。

## 7. 离线资源说明

- `产物/echarts.min.js`、`产物/mermaid.min.js` 为本地离线 bundle，供 23–25 可视化页使用（**无 CDN 依赖，断网可打开**）。
- 其余报告图表均为内联 SVG，无任何外部依赖。

## 8. 常见问题

| 问题 | 解法 |
|---|---|
| `ModuleNotFoundError: jieba` | 确认使用 `.venv/bin/python` 而非系统 python |
| 报告图表空白 | 检查是否用了 CDN 图表（应改内联 SVG，见 WORKFLOW.md §8）；离线 bundle 是否与 HTML 同目录 |
| Python 版本过旧 | 安装 Python 3.10+（macOS: `brew install python`；Windows: python.org 安装包勾选 Add to PATH） |
| 中文乱码 | 终端设置 UTF-8；文件均为 UTF-8 编码 |
