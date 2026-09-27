# Wiki 化骨架规划（只读期 · 预留扩展）

> 定稿 2026-09-27。三项决策：① 词条源 = Markdown + frontmatter ② 编辑预留 = git-based CMS（Decap 占位）③ 一期 = 骨架 + 5 个种子词条。
> 配套设计系统见 `UI_SPEC.md`（鸿蒙风格、双主题、内嵌鸿蒙 Sans）。

## 1. 定位与原则

- **Wiki 功能 = 构建期生成**：读者看到的是纯静态 HTML（GitHub Pages 直出），无后端、运行时零依赖。
- **内容与渲染分离**：词条内容活在 `content/`（git 内 Markdown），改内容 = 改 md + 重跑构建；"不开放编辑"只是不加编辑入口，数据层面天然可编辑。
- **扩展开关**：CMS / 评论 / 历史均为可插拔接口，启用时不动架构。

## 2. 命名空间与 URL

| 命名空间 | URL | 来源 |
|---|---|---|
| 人物 | `/wiki/人物/任琅.html` | 手写 md + knowledge_base.json 自动信息框 |
| 章节 | `/wiki/章节/一.html` | chapters_index + 分章 txt 自动生成正文 |
| 地点 / 组织 / 术语 | `/wiki/地点/青楼.html` 等 | 手写 md（一期仅骨架占位） |
| 诗词 | `/wiki/诗词/其一.html` | poems.json |
| 特殊页 | `/wiki/index.html`（总目录）、分类页、消歧义页、重定向页（别名自动生成） | 构建器产出 |

## 3. 词条源格式（content/）

```markdown
---
title: 任琅
ns: 人物
aliases: [任少侠]
summary: 本书主人公之一，与尚樱定情于情花节。
infobox:            # 缺省键自动从 knowledge_base.json 回填（首见/末见/提及/出场）
  身份: 少年剑客
tags: [主角, 五岳盟]
---
正文支持 Markdown 子集与词条链：[[尚樱]]、[[章节/十一|情花节福纸]]、[[妖刀]]（未创建=红链）。
```

- 目录：`content/<ns>/<title>.md`；`schema_version` 写入构建产物。
- 构建器校验：死链清单输出（红链可点→"词条待创建"页）。

## 4. 构建管线 build_wiki.py（纯标准库）

1. 扫描 `content/` 解析 frontmatter（自写解析，不引 PyYAML）
2. `[[链]]` 解析：`[[title]]` / `[[ns/title]]` / `[[ns/title|显示名]]`，别名归一
3. 生成：词条页、重定向页、分类页、总目录、消歧义页
4. 回链索引（谁引用了本词条）+ 章节出处自动汇聚（infobox 数据来自 knowledge_base.json，词条间保持单一事实源）
5. `wiki/search-index.json`（标题/摘要/正文分词碎片）
6. 输出死链报告 + 构建统计

## 5. 页面模板与现有页关系

- `assets/theme.css`：鸿蒙设计令牌（UI_SPEC 落地件，三页与 wiki 共用）。
- 词条页结构：命名空间徽标 → 大标题/别名 → 信息框（左）+ 正文（右）→ 章节出处胶囊 → 反向链接 → 页脚（修订历史链接 = 该文件 GitHub commits 页 + 构建时间 + schema 版本）。
- `index.html` 门户加"Wiki 词条"入口；`kb.html` 保留为**数据库视图**（五视图），wiki 为**叙事视图**，二期 kb 人物表点击跳词条页。

## 6. 扩展预留（只读期不启用）

| 接口 | 预留方式 | 启用动作 |
|---|---|---|
| 编辑 | `content/` 即编辑面；`admin/config.yml` 占位（Decap CMS 配置） | 部署 Decap + GitHub OAuth，网页编辑→提 PR |
| 评论 | 词条模板预留 `<div id="giscus">` 挂载点 | 填 giscus 仓库参数即可 |
| 历史 | 页脚 git commits 链接（已可用） | 无需动作 |
| 开放数据 | `knowledge_base.json` / `search-index.json` 常驻可直连 | 无需动作 |
| 版本 | 产物内嵌 `schema_version` | 升级时迁移脚本按版本判断 |

## 7. 分期路线

- **P1 ✅（2026-09-27）**：`content/` 骨架 + `build_wiki.py` + `assets/theme.css` 落地 + 5 个种子词条（任琅 / 尚樱 / 夏叶 / 章节·一 / 章节·十一）+ 总目录 + 死链机制 + 门户入口。
- **P2（当前待办）**：全量自动词条（33 人物 + 63 章节，信息框自动、正文待补）+ 分类页 + 站内搜索接线。
- **P3 ✅（2026-09-27，提前完成）**：鸿蒙双主题统一全站页（index / kb / poem_gallery / wiki / docs），含内嵌 HarmonyOS Sans SC 字体（fonts/ 分片）、官方图标库、动效令牌（MOTION_SPEC.md）。
- **P4**：按需启用 CMS / 评论。

## 8. 验收标准

- [[链]]零死链（或红链显式可见）；别名重定向可达
- 信息框数据与 kb.html 同源一致（单源校验）
- 搜索可命中词条正文关键词
- 双主题 + 移动端 375px 可用；`bash deploy.sh` 一键上线不变
