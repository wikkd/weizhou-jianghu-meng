# MOTION_SPEC.md — 动效与交互细则

> DEV_RULES.md 守则一/守则二的**动效深化**，对所有页面新增/改动的交互动效强制生效。
> 令牌落地件：`assets/theme.css`（`--ease-*` / `--dur-*`），全站引用，禁止页面内自造曲线。
> 曲线令牌取自 [Open Props](https://github.com/argyleink/open-props)（MIT）精选子集，注释已署名。

---

## 1. 组件库选型结论（2026-09-27 调研）

| 候选 | 许可 | 结论 | 理由 |
|---|---|---|---|
| [Open Props](https://github.com/argyleink/open-props) | MIT | **采用（曲线令牌子集内联）** | 缓动值就是 `cubic-bezier`/`linear()` 常量，直接并入 theme.css，零依赖不破坏 |
| [harmony-style](https://gitee.com/hongweifei/harmony-style)（Gitee） | ISC | **仅作规范参考，不引入** | 自带 `--color-brand` 变量体系与本站 theme.css 冲突；深色模式走 `prefers-color-scheme` 与本站 `data-theme` 手动切换冲突 |
| IBest-UI / ArkUI ace_engine | — | 排除 | ArkTS 原生库，不适用于 Web 静态页 |

> 若未来 harmony-style 支持外部主题挂载，可再评估整库引入；当前沿用 theme.css 单一令牌源。

## 2. 曲线令牌（非线性优先）

**总原则：所有过渡/动画一律使用下列非线性曲线；`linear`、`ease`、`ease-in/out` 等原生关键字禁止使用**（`linear()` 弹性曲线与 `steps()` 除外）。

| 令牌 | 值 | 用途 |
|---|---|---|
| `--ease-std` | `cubic-bezier(.25,0,.3,1)` | **默认**。悬停、取色、下划线等标准过渡 |
| `--ease-out` | `cubic-bezier(0,0,.1,1)` | 进入/展开：卡片上浮、面板滑入 |
| `--ease-out-soft` | `cubic-bezier(0,0,.3,1)` | 进入·柔和版（长列表避免过冲） |
| `--ease-in-out` | `cubic-bezier(.5,0,.5,1)` | 位移往返、主题切换颜色过渡 |
| `--ease-expo-out` | `cubic-bezier(.19,1,.22,1)` | sheet/抽屉等大面板滑入（强减速） |
| `--ease-spring` | `linear(...)`（Open Props spring-3） | 弹性强调：按压回弹、弹出层；旧浏览器自动降级为 `ease` |
| `--ease-bounce` | `linear(...)`（Open Props bounce-2） | 完成态反馈：打勾、落位、"已复制" |
| `--ease-elastic-out` | `cubic-bezier(.5,1.25,.75,1.25)` | 微反馈：chip 放大、小位移过冲 |

## 3. 时长刻度

| 令牌 | 值 | 用途 |
|---|---|---|
| `--dur-fast` | 120ms | 微反馈：hover、chip、链接下划线 |
| `--dur-base` | 200ms | 标准过渡：按钮、卡片、tab、焦点环 |
| `--dur-slow` | 320ms | 大位移：抽屉、sheet、主题切换、页面入场 |
| `--dur-drama` | 480ms | 强调：搜索命中闪烁、页首横幅 |

> 配对惯例：位移/尺寸变化用「慢曲线快时长」之外，**out 系曲线配 fast/base，spring/bounce 配 base 及以上**——弹性曲线太短会抖。

## 4. 交互触发动效映射表（新增交互照此选型）

| 交互 | 属性 | 曲线 | 时长 | 备注 |
|---|---|---|---|---|
| 链接/导航 hover | `background` `color` | `--ease-std` | fast | 词条蓝链 `.wl` 另加下划线实线化 |
| 卡片 hover | `transform:translateY(-2px)` + `box-shadow` | `--ease-out` | base | 只上浮不加缩放 |
| 按钮 hover / 按压 | `translateY` / `scale(.96)` | `--ease-spring` | base | 按压回弹是鸿蒙手感核心 |
| chip 类小件 hover | `scale(1.06)` / 按压 `scale(.94)` | `--ease-elastic-out` | fast | 仅可点的 `.lnk` chip |
| 主题切换按钮 | `rotate(15deg)` + 按压缩放 | `--ease-spring` | base | 旋转+回弹 |
| 主题切换全局 | `background` `color` | `--ease-in-out` | slow | body 已有 0.25s 过渡，页面无需另写 |
| 抽屉/半模态 sheet | `transform:translateX/Y` | `--ease-expo-out` | slow | 遮罩淡入用 `--ease-std` |
| tab/分段器切换 | 内容淡入 | `--ease-out-soft` | base | 参考 `.fade-in` |
| 页面载入 | `opacity` + `translateY(8px)`（`.fade-in`） | `--ease-out` | slow | 列表容器加 stagger：`animation-delay:calc(var(--i)*40ms)` |
| 搜索命中 | 命中卡淡入 | `--ease-out-soft` | base | 空态提示不动画（反馈靠文案） |
| 完成提示（复制/保存成功） | 打勾 `scale` 0→1 | `--ease-bounce` | base | 一次性，不循环 |
| 红链 hover | 虚线→实线 | `--ease-std` | fast | 语义：可创建的词条 |

## 5. 硬性红线

1. **只动合成层属性**：`transform`、`opacity`、`filter`。禁止动画 `width/height/top/left/margin`（引发布局抖动）。
2. **`prefers-reduced-motion: reduce` 必须降级**：theme.css 已全站兜底，页面私有动画无需重复写，但新增**循环动画**时自查降级效果。
3. **禁止无限循环装饰动画**（呼吸、漂浮、渐变流光）。唯一例外：加载指示器（`.loading` 类）。
4. **入场动画必须渐进增强**：`animation ... backwards` + 内容默认可见，禁 JS 阻塞注入类名才显示的写法。
5. **stagger 上限**：`animation-delay` 步进 ≤40ms、总数 ≤12 项，超出部分直接显示。
6. **曲线禁令**：页面内出现 `transition: all`、`ease`、`linear`（非 spring/bounce 场景）即为违规。

## 6. 验收清单（每页动效过一遍）

- [ ] 全部过渡引用 `--ease-*`/`--dur-*`，无自造 bezier、无 `transition: all`
- [ ] 按钮/卡片/chip 三类手感齐全（hover、按压、回弹）
- [ ] 系统开启「减少动效」后页面静态可用
- [ ] 动画只涉及 transform/opacity/filter
- [ ] 无循环装饰动画；加载态除外
- [ ] 入场动画不阻塞内容可见（禁 JS 时页面完整）
