# -*- coding: utf-8 -*-
"""
汇编液态玻璃设计系统：将 产物/glass/*.css 细粒度组件 partial 按顺序拼接为
单一权威样式表 产物/glass.css。

设计：源文件是真正独立、可复用的组件模块；产物 glass.css 是供 17 份报告
<link> 的打包结果。修改任一组件只需编辑对应 partial 后重跑本脚本。
"""
import io, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC  = os.path.join(ROOT, "产物", "glass")
OUT  = os.path.join(ROOT, "产物", "glass.css")

# 拼接顺序：令牌 → 基础 → 布局 → 表面 → 控件 → 导航 → 数据 → 反馈 → 浮层
#           → 旧主题兼容（覆盖基础/布局中的标题等）→ 动效 → 打印
PARTIALS = [
    "tokens.css",    # 设计令牌（含 body.dark 冷调覆盖）
    "base.css",      # reset / 渐变背景 / 排版 / 焦点
    "layout.css",    # 容器 / 栅格 / 间距 / 响应式
    "surface.css",   # .glass 玻璃材质 / panel / hero / divider
    "button.css",    # .btn 多形态 / icon-btn / 涟漪
    "form.css",      # 输入 / 搜索 / 开关 / 滑块
    "chip.css",      # chip / badge / avatar
    "navigation.css",# topbar / nav / tabs / segmented / toolbar
    "data.css",      # statcard / table / list / timeline
    "feedback.css",  # alert / progress / tooltip / toast / skeleton
    "overlay.css",   # modal / drawer / popover / accordion
    "legacy.css",    # 旧 theme.css 选择器玻璃化（兼容 17 份报告）
    "motion.css",    # 关键帧 / 过渡 / 降级
    "print.css",     # 打印
]

def main():
    if not os.path.isdir(SRC):
        raise SystemExit("未找到目录: " + SRC)
    missing = [p for p in PARTIALS if not os.path.isfile(os.path.join(SRC, p))]
    if missing:
        raise SystemExit("缺少 partial: " + ", ".join(missing))

    out = io.StringIO()
    out.write("/* ============================================================\n")
    out.write(" *  苇舟江湖梦 · Glass Design System（液态玻璃设计系统）\n")
    out.write(" *  由 脚本/_build_glass.py 自动汇编自 产物/glass/*.css（细粒度组件）\n")
    out.write(" *  单一权威样式表：供 产物/ 下所有 HTML 报告共用。\n")
    out.write(" *  视觉语言：Apple 经典冷调液态玻璃（blur + 半透明 + 高光 + 折射）\n")
    out.write(" * ============================================================ */\n\n")

    banner = "/* ===== %s ===== */\n"
    for name in PARTIALS:
        p = os.path.join(SRC, name)
        txt = io.open(p, encoding="utf-8").read().strip()
        out.write(banner % name)
        out.write(txt)
        out.write("\n\n")

    css = out.getvalue()
    io.open(OUT, "w", encoding="utf-8").write(css)

    # 统计
    size = len(css.encode("utf-8"))
    braces = css.count("{") - css.count("}")
    rules = len(re.findall(r"\{[^}]*\}", css))
    print("已生成:", OUT)
    print("  组成部分:", len(PARTIALS), "个细粒度组件 partial")
    print("  体积: %.1f KB" % (size / 1024))
    print("  规则数(约):", rules)
    print("  花括号平衡:", "OK" if braces == 0 else ("不平衡! %+d" % braces))

if __name__ == "__main__":
    main()
