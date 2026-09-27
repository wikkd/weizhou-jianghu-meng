# 苇舟江湖梦站点 · UI 设计规格（HarmonyOS 风格）

> 定稿于 2026-09-27。三项决策：① 明暗双主题（跟随系统 + 手动切换）② 内嵌 HarmonyOS Sans SC ③ 三页一并改造。

## 1. 设计原则（鸿蒙映射到 Web）

| 鸿蒙设计语言 | 本站落地 |
|---|---|
| 克制纯净、大留白 | 取消蓝绿渐变横幅，改浅灰底 `#F1F3F5` + 白卡片 |
| 服务卡片 | 统计/入口/诗词全部卡片化，圆角 16-24 |
| 大标题层次 | 页面顶部大标题（24/500），滚动后导航收缩为小标题 |
| 胶囊组件 | 按钮、Tab 分段器、标签全用全圆胶囊 |
| 半模态 sheet | 人物/章节详情改底部滑出面板（替代右侧抽屉） |
| 明暗双主题 | CSS 变量双套 + 手动切换按钮，默认跟随系统 |
| 弹簧动效 | 过渡统一 250-300ms ease-out，卡片悬浮上移 4px |

## 2. 设计令牌

### 色彩（CSS 变量，`:root` / `[data-theme=dark]` 双套）

| 变量 | 浅色 | 深色 |
|---|---|---|
| `--bg` | #F1F3F5 | #000000 |
| `--card` | #FFFFFF | #1C1C1E |
| `--ink`（主文字） | #182431 | #F1F3F5 |
| `--muted`（次文字） | #7A8A99 | #99FFFFFF |
| `--line`（分割线） | rgba(24,36,49,.10) | rgba(255,255,255,.12) |
| `--brand`（鸿蒙蓝） | #0A59F7 | #3E70E8 |
| `--brand-soft`（蓝底浅） | #E6F1FB | rgba(62,112,232,.18) |
| `--accent`（配角绿） | #0F6E56 | #5DCAA5 |
| `--accent-soft` | #E1F5EE | rgba(93,202,165,.16) |
| `--gold`（诗题金） | #B8860B | #EF9F27 |

主题切换：`<html data-theme="light|dark">`，默认 JS 读 `prefers-color-scheme`，右上角胶囊按钮手动切换并 `localStorage` 记忆。

### 字体

```css
@font-face { font-family:"HarmonyOS Sans SC"; src:url("fonts/…woff2") format("woff2");
             font-weight:400; font-display:swap; unicode-range:… }
/* Medium 500 / Bold 700 同理 */
```

- 来源：npm `harmonyos-sans-sc-webfont-splitted`（cn-font-split 按 unicode-range 拆 woff2，浏览器按需加载分片）。
- 字体栈：`"HarmonyOS Sans SC","Noto Sans CJK SC","Microsoft YaHei",system-ui,sans-serif`。
- 诗词正文保留衬线：`"Noto Serif CJK SC","Songti SC",serif`。
- 仓库仅收 2 个权重：Regular 400 + Medium 500（Bold 场景用 500 代替，减体积）。

### 字阶 / 圆角 / 间距 / 动效

| 令牌 | 值 |
|---|---|
| 大标题 24/500 · 标题 20/500 · 小标题 15/500 · 正文 14/400 · 辅助 12/400 | 仅 400/500 两档字重 |
| 圆角 | 卡片 16（服务卡 24 视觉外圈）、输入框 12、胶囊 999 |
| 间距 | 8pt 栅格：8 / 12 / 16 / 24 / 32 |
| 描边阴影 | 0.5px `--line` 为主；悬浮阴影 `0 8px 24px rgba(0,0,0,.06)`（深色模式禁用阴影，改亮描边） |
| 动效 | `transition: .25s ease-out`；sheet `transform .3s cubic-bezier(.2,.8,.2,1)` |

## 3. 组件改造清单

| 现状 | 改为 |
|---|---|
| 蓝绿渐变 header | 白色玻璃导航（`backdrop-filter:blur`）+ 大标题区 |
| 方角 Tab（`.tab`） | 胶囊分段器，active=鸿蒙蓝实底白字 |
| 人物/章节右侧抽屉（`.drawer`） | 底部半模态 sheet：拖拽条 + 圆角 18 顶边 + 遮罩，点遮罩/下滑关闭 |
| `.chip` 方角 | 全圆胶囊（主=蓝系 / 配=绿系 / 待定=灰系） |
| `.stat` 蓝底 | 白卡片，数字 22/500 主文字色，标签 12 灰 |
| 桌面表格 | 宽屏保留表格；<880px 折成人物/章节卡片列表（头像字圆 + 名称 + 胶囊 + ›） |
| SVG 共现网络 | 节点色 `--brand`、边 `#9BB6E8→`深色模式用 50% 白蓝；标签跟随 `--ink` |
| 检索输入框 | 圆角 12、聚焦描边 `--brand` |
| 热力格 | 未出场 `--line` 色，出现档位用蓝系 4 档（#EDEFF3 基线/浅/中/深蓝） |

## 4. 三页改版要点

### index.html（入口主页）
- 玻璃导航：品牌圆点 + 关于/知识库/诗图/仓库（仓库=蓝底胶囊）。
- Hero 左文右图：大标题、作者行、蓝字名句、双胶囊 CTA；右侧 2×2 统计白卡。
- 三处入口服务卡片（SVG 线性图标 36px 圆角底 + 标题 + 描述 + "打开 →"）。
- 诗词撷英：4 列小卡（人物蓝字 / 章回·诗体 11px 灰 / 首句衬线省略）。
- 页脚灰色小字 + 版权声明。

### kb.html（知识库）
- 顶部胶囊"‹ 主页" + 标题 + 右侧数据规模灰字。
- 胶囊分段器五视图；概览统计改白卡网格。
- 人物/章节详情：底部半模态 sheet（时间线热力格 + 高频共现胶囊可点）。
- 检索视图：大圆角输入框 + 命中结果列表卡片化。
- 深色模式下 SVG 网络/热力档位同步换色。

### poems/poem_gallery.html（诗图）
- 顶部导航与另两页统一（返回胶囊"‹ 主页"）。
- 诗卡：图区黑底改深灰 `#141414`（深色模式 `#000`）、圆角 24；诗题区白卡。
- 诗体标签胶囊化；`loading="lazy"` 保留，加骨架底色防跳动。
- 双主题下 meta 文字用 `--muted`。

## 5. 实施清单与验收

- [ ] 引入 fonts/（harmonyos-sans-sc-webfont-splitted 的 Regular+Medium woff2 与 CSS，去 CDN 依赖改本地引用）
- [ ] 三页公共 CSS 抽为 `assets/theme.css`（令牌 + 组件基类），三页 `<link>` 复用（仍是本地文件，保持离线可用）
- [ ] 主题切换按钮 + localStorage + prefers-color-scheme
- [ ] kb.html：抽屉→sheet、Tab→胶囊、表格响应式
- [ ] index.html / poem_gallery 按第 4 节重排
- [ ] 验收：深浅两套主题全页过一遍无对比度问题（正文 ≥ 4.5:1）；移动端 375px 宽不横向滚动；构建脚本可一键重出三页
