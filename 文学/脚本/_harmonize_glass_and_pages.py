# -*- coding: utf-8 -*-
"""glass.css 鸿蒙化 + 独立模板页接入 + echarts 字体栈（幂等）。

范围：
  1. 产物/glass.css：Apple 冷调 → HarmonyOS 色板（亮/暗）、HarmonyOS Sans 字体栈、
     动效曲线对齐站点令牌（--ease 家族）、底色渐变换鸿蒙浅灰
  2. 5 个真独立内联模板页：注入 theme.css 链接 + HarmonyOS 字体强制块
     （可视化叙事系统 / 扩展叙事 / 深度叙事 / 报告归纳整理×2）
  3. echarts-kit.js 图表字体栈加 HarmonyOS Sans SC
用法：python 脚本/_harmonize_glass_and_pages.py   （deploy.sh 部署前自动调用）
"""
import io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, "产物", *a)
MARK = "/* harmonyos-glass-harmonized */"
FONT_FORCE = ("<style id=\"wz-harmony-font\">"
              "body,h1,h2,h3,h4,button,input,select,textarea"
              "{font-family:'HarmonyOS Sans SC','HarmonyOS Sans','PingFang SC',"
              "'Microsoft YaHei','Noto Sans SC',sans-serif!important}</style>")


def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(s)


def sub_once(css, old, new, label):
    if new in css and old not in css:
        return css
    if old not in css:
        print("  [WARN glass] 未找到: " + label)
        return css
    return css.replace(old, new, 1)


def harmonize_glass():
    css = read(P("glass.css"))
    # —— 亮色品牌/中性 ——
    css = sub_once(css, "--primary:#0a84ff;", "--primary:#0A59F7;", "primary")
    css = sub_once(css, "--primary-d:#0066d6;", "--primary-d:#0642B0;", "primary-d")
    css = sub_once(css, "--primary-l:#5ac8fa;", "--primary-l:#3D7FFF;", "primary-l")
    css = sub_once(css, "--accent:#ff453a;", "--accent:#E84026;", "accent")
    css = sub_once(css, "--ink:#0f1620;", "--ink:#182431;", "ink")
    css = sub_once(css, "--muted:#5d6675;", "--muted:#7A8A99;", "muted")
    css = sub_once(css, "--line:rgba(18,30,50,.12);", "--line:rgba(24,36,49,.10);", "line")
    css = sub_once(css, "--line-strong:rgba(18,30,50,.22);", "--line-strong:rgba(24,36,49,.16);", "line-strong")
    css = sub_once(css,
        "--band:linear-gradient(135deg,#0a84ff 0%,#5e5ce6 100%);",
        "--band:linear-gradient(135deg,#0642B0 0%,#0A59F7 55%,#3D7FFF 100%);", "band")
    css = sub_once(css, "--bg:#e9eef7;", "--bg:#F1F3F5;", "glass-bg")
    css = sub_once(css,
        "--sans:'PingFang SC','Microsoft YaHei','Noto Sans SC',system-ui,-apple-system,'Segoe UI',sans-serif;",
        "--sans:'HarmonyOS Sans SC','HarmonyOS Sans','PingFang SC','Microsoft YaHei','Noto Sans SC',system-ui,sans-serif;",
        "sans")
    css = sub_once(css, "--serif:'PingFang SC','Noto Sans SC',system-ui,sans-serif;",
        "--serif:'HarmonyOS Sans SC','PingFang SC','Noto Sans SC',system-ui,sans-serif;", "serif")
    css = sub_once(css, "--ease:cubic-bezier(.32,.72,0,1);",
        "--ease:cubic-bezier(.25,0,.3,1);\n  --ease-spring:linear(0,0.009,0.035 2.1%,0.141 4.4%,0.723 12.9%,0.938 16.7%,1.017,1.077,1.121,1.149 24.3%,1.159,1.163,1.161,1.154 29.9%,1.129 32.8%,1.051 39.6%,1.017 43.1%,0.991,0.977 51%,0.974 53.8%,0.975 57.1%,0.997 69.8%,1.003 76.9%,1);\n  --ease-expo-out:cubic-bezier(.19,1,.22,1);", "ease")
    # 底色渐变（亮）→ 鸿蒙浅灰
    css = sub_once(css,
        "linear-gradient(160deg,#eaf0f9 0%,#e6ebf5 50%,#eef1f8 100%);",
        "linear-gradient(160deg,#F1F3F5 0%,#ECF0F4 50%,#F4F6F8 100%);", "bg-gradient-light")
    css = sub_once(css, "rgba(10,132,255,.14), transparent 55%)", "rgba(10,89,247,.12), transparent 55%)", "radial-blue")
    # —— 暗色 ——
    css = sub_once(css,
        "body.dark{\n  --primary:#0a84ff; --primary-d:#409cff; --primary-l:#64d2ff;\n  --accent:#ff6961; --accent-d:#ff453a;",
        "body.dark{\n  --primary:#3E70E8; --primary-d:#6B9BFF; --primary-l:#8AB4FF;\n  --accent:#F09595; --accent-d:#E07B6A;", "dark-brand")
    css = sub_once(css, "  --ink:#eef2f8;", "  --ink:#F1F3F5;", "dark-ink")
    css = sub_once(css, "  --bg:#0a0d13;", "  --bg:#000000;", "dark-bg")
    css = sub_once(css, "  --surface-solid:#161a22;", "  --surface-solid:#1C1C1E;", "dark-surface-solid")
    css = sub_once(css, "  --glass-tint:22,26,34;", "  --glass-tint:28,28,30;", "dark-glass-tint")
    css = sub_once(css,
        "  --band:linear-gradient(135deg,#0a84ff 0%,#5e5ce6 100%);\n  --shadow:0 8px 26px",
        "  --band:linear-gradient(135deg,#2E5BD0 0%,#6C9BFF 100%);\n  --shadow:0 8px 26px", "dark-band")
    if MARK not in css:
        css += ("\n" + MARK + "\n/* 鸿蒙化追加：标题 Medium 已由令牌字体栈生效；"
                "若下方无规则则为占位，保持文件结构稳定 */\n")
    write(P("glass.css"), css)
    print("glass.css 鸿蒙化完成")


PAGES = [
    ("苇舟江湖梦_可视化叙事系统.html", "theme.css"),
    ("苇舟江湖梦_扩展叙事可视化.html", "theme.css"),
    ("苇舟江湖梦_深度叙事可视化.html", "theme.css"),
    ("苇舟江湖梦_报告归纳整理.html", "theme.css"),
    ("00_总览导航/苇舟江湖梦_报告归纳整理.html", "../theme.css"),
]


def inject_pages():
    for rel, href in PAGES:
        p = P(rel)
        if not os.path.exists(p):
            print("  [跳过·不存在] " + rel)
            continue
        html = read(p)
        changed = False
        if "theme.css" not in html:
            m = re.search(r"<style", html)
            link = '<link rel="stylesheet" href="%s">\n' % href
            if m:
                html = html[:m.start()] + link + html[m.start():]
            else:
                html = html.replace("</head>", link + "</head>", 1)
            changed = True
        if "wz-harmony-font" not in html:
            if "</head>" in html:
                html = html.replace("</head>", FONT_FORCE + "\n</head>", 1)
                changed = True
        if changed:
            write(p, html)
            print("  [已接入] " + rel)
        else:
            print("  [跳过·已接入] " + rel)


def fix_echarts_font():
    p = P("echarts-kit.js")
    js = read(p)
    old = 'fontFamily: "PingFang SC, Microsoft YaHei, Noto Sans SC, system-ui, sans-serif"'
    new = ('fontFamily: \'"HarmonyOS Sans SC","HarmonyOS Sans","PingFang SC",'
           '"Microsoft YaHei","Noto Sans SC",system-ui,sans-serif\'')
    if new in js:
        print("echarts-kit 字体栈已是鸿蒙")
        return
    if old in js:
        js = js.replace(old, new, 1)
        write(p, js)
        print("echarts-kit 字体栈已更新")
    else:
        print("  [WARN echarts] 未找到字体栈锚点")


if __name__ == "__main__":
    harmonize_glass()
    inject_pages()
    fix_echarts_font()
