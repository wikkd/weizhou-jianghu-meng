# -*- coding: utf-8 -*-
"""产物/theme.css 鸿蒙化（幂等，可重复执行）。

将报告族统一设计语言从「宣纸墨蓝」切换为 HarmonyOS Design：
  1. 亮/暗两套 Token 换血（#0A59F7 主色、浅灰底白卡片、暗色 #000/#1C1C1E）
  2. 注入 8 条非线性缓动曲线 + 4 级时长（与站点 assets/theme.css 同源，Open Props MIT 子集）
  3. 内嵌 HarmonyOS Sans SC Regular/Medium @font-face（fonts/ 相对路径，164 分片）
  4. 标题改 HarmonyOS Sans Medium、dm-toggle 按钮胶囊化、卡片 hover 浮起
  5. 375px 小屏补充断点
用法：python 脚本/_harmonize_report_theme.py   （deploy.sh 部署前自动调用）
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.normpath(os.path.join(ROOT, "..", "苇舟江湖梦_知识库"))
THEME = os.path.join(ROOT, "产物", "theme.css")
SITE_THEME = os.path.join(SITE, "assets", "theme.css")

MARK = "/* harmonyos-harmonized */"


def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(s)


def replace_once(s, old, new):
    if new in s and old not in s:
        return s  # 已替换过
    if old not in s:
        print("  [WARN] 未找到锚点: " + old[:60].replace("\n", "\\n"))
        return s
    return s.replace(old, new, 1)


def extract_site_fonts(site_css):
    """从站点 theme.css 提取 @font-face 全部块（含节注释）。"""
    i = site_css.find("/* ===== HarmonyOS Sans SC Regular")
    if i < 0:
        i = site_css.find("@font-face")
    blocks = []
    for m in re.finditer(r"@font-face\s*\{.*?\}", site_css[i:], re.S):
        blocks.append(m.group(0))
    return len(blocks), "\n".join(blocks)


def main():
    css = read(THEME)

    # ---------- 1. 头部 DNA 注释 ----------
    css = replace_once(
        css,
        " *  设计 DNA：宣纸底 / 墨蓝主色 / 朱砂点缀 / 衬线标题 + 无衬线正文。",
        " *  设计 DNA：HarmonyOS Design —— 鸿蒙蓝 #0A59F7 / 浅灰底白卡片 / Medium 标题。\n"
        " *  （2026-09-28 鸿蒙化：令牌/字体/动效与站点 assets/theme.css 同源）",
    )

    # ---------- 2. :root 亮色 Token 换血 ----------
    old_root_hdr = """  /* —— 既有色板 Token（不变）—— */
  --bg:#f4f1ea; --surface:#fffdf8; --surface-2:#f7f4ec;
  --ink:#1f1c17; --muted:#6b6353; --line:#ddd6c8; --line-strong:#cdc4b0;
  --primary:#2c5d8a; --primary-d:#1f3a5f; --accent:#8a3324; --gold:#b8860b;
  --band:linear-gradient(135deg,#1f3a5f 0%,#2c5d8a 100%);
  --serif:'Noto Serif SC','Songti SC','SimSun',serif;
  --sans:'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif;

  /* —— 形状 / 阴影 / 度量（新增，统一复用）—— */
  --radius:12px; --radius-sm:10px;
  --shadow:0 1px 3px rgba(31,28,23,.06);
  --shadow-card:0 2px 10px rgba(31,28,23,.06);
  --measure:74ch;                 /* 正文舒适行宽 */
}"""
    new_root = """  /* —— 鸿蒙亮色 Token（HarmonyOS Design）—— */
  --bg:#F1F3F5; --surface:#FFFFFF; --surface-2:#F7F9FA;
  --ink:#182431; --muted:#7A8A99; --line:rgba(24,36,49,.10); --line-strong:rgba(24,36,49,.16);
  --primary:#0A59F7; --primary-d:#0642B0; --accent:#E84026; --gold:#B8860B;
  --band:linear-gradient(135deg,#0642B0 0%,#0A59F7 55%,#3D7FFF 100%);
  --serif:'Noto Serif SC','Songti SC','SimSun',serif;
  --sans:'HarmonyOS Sans SC','HarmonyOS Sans','PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif;

  /* —— 形状 / 阴影 / 度量 —— */
  --radius:16px; --radius-sm:12px;
  --shadow:0 8px 24px rgba(0,0,0,.06);
  --shadow-card:0 2px 10px rgba(24,36,49,.06);
  --measure:74ch;                 /* 正文舒适行宽 */

  /* —— 动效：非线性缓动曲线（与站点 theme.css 同一令牌，Open Props MIT 精选子集）—— */
  --ease-std:cubic-bezier(.25,0,.3,1);
  --ease-out:cubic-bezier(0,0,.1,1);
  --ease-out-soft:cubic-bezier(0,0,.3,1);
  --ease-in-out:cubic-bezier(.5,0,.5,1);
  --ease-expo-out:cubic-bezier(.19,1,.22,1);
  --ease-spring:linear(0,0.009,0.035 2.1%,0.141 4.4%,0.723 12.9%,0.938 16.7%,1.017,1.077,1.121,1.149 24.3%,1.159,1.163,1.161,1.154 29.9%,1.129 32.8%,1.051 39.6%,1.017 43.1%,0.991,0.977 51%,0.974 53.8%,0.975 57.1%,0.997 69.8%,1.003 76.9%,1);
  --ease-bounce:linear(0,0.004,0.016,0.035,0.063,0.098,0.141 15.1%,0.25,0.391,0.562,0.765,1,0.892 45.2%,0.849,0.815,0.788,0.769,0.757,0.753,0.757,0.769,0.788,0.815,0.85,0.892 75.2%,1 80.2%,0.973,0.954,0.943,0.939,0.943,0.954,0.973,1);
  --ease-elastic-out:cubic-bezier(.5,1.25,.75,1.25);
  --dur-fast:120ms; --dur-base:200ms; --dur-slow:320ms; --dur-drama:480ms;
}"""
    css = replace_once(css, old_root_hdr, new_root)

    # ---------- 3. 选区 / body 过渡 ----------
    css = replace_once(css,
        "::selection{background:rgba(44,93,138,.18);}",
        "::selection{background:rgba(10,89,247,.15);}")
    css = replace_once(css,
        "body{margin:0;background:var(--bg);color:var(--ink);\n  font-family:var(--sans);font-size:15.5px;line-height:1.78;\n  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;}",
        "body{margin:0;background:var(--bg);color:var(--ink);\n  font-family:var(--sans);font-size:15.5px;line-height:1.78;\n  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;\n  transition:background-color var(--dur-slow) var(--ease-in-out),color var(--dur-slow) var(--ease-in-out);}")

    # ---------- 4. 标题：衬线 → HarmonyOS Sans Medium ----------
    css = replace_once(css,
        "h1{display:block;background:var(--band);color:#fff;font-family:var(--serif);\n  font-size:clamp(22px,3.2vw,27px);font-weight:700;line-height:1.32;letter-spacing:1.5px;",
        "h1{display:block;background:var(--band);color:#fff;font-family:var(--sans);\n  font-size:clamp(22px,3.2vw,27px);font-weight:500;line-height:1.32;letter-spacing:1px;")
    css = replace_once(css,
        "h2{font-family:var(--serif);font-size:20px;font-weight:700;color:var(--primary-d);",
        "h2{font-family:var(--sans);font-size:20px;font-weight:500;color:var(--primary-d);")
    css = replace_once(css,
        "h3{font-family:var(--serif);font-size:17px;color:var(--ink);",
        "h3{font-family:var(--sans);font-size:17px;font-weight:500;color:var(--ink);")

    # ---------- 5. 暗色 Token 换血 ----------
    css = replace_once(css,
        """body.dark{
  --bg:#0e1219; --surface:#19212c; --surface-2:#1f2832;
  --ink:#e9e4d8; --muted:#94a0ae; --line:#2b3441; --line-strong:#3a4654;
  --primary:#5a93c9; --primary-d:#3d7ab0; --accent:#d8644f; --gold:#dcae46;
  --band:linear-gradient(135deg,#11283f 0%,#1d4b73 100%);
}""",
        """body.dark{
  --bg:#000000; --surface:#1C1C1E; --surface-2:#232326;
  --ink:#F1F3F5; --muted:rgba(255,255,255,.60); --line:rgba(255,255,255,.12); --line-strong:rgba(255,255,255,.20);
  --primary:#3E70E8; --primary-d:#6B9BFF; --accent:#F09595; --gold:#EF9F27;
  --band:linear-gradient(135deg,#0A1E45 0%,#153E8F 100%);
}""")
    for old, new in [
        ("body.dark .note{background:#1c2530;", "body.dark .note{background:#1C1C1E;"),
        ("body.dark .note code{background:#28323e;}", "body.dark .note code{background:#2A2A2E;}"),
        ("body.dark code{background:#222e3a; color:#cdd6e0;}", "body.dark code{background:#2A2A2E; color:#C9CDD2;}"),
        ("body.dark table th{background:#222e3a; color:#cdd6e0;}", "body.dark table th{background:#2A2A2E; color:#C9CDD2;}"),
        ("body.dark tbody tr:nth-child(even) td{background:#161d26;}", "body.dark tbody tr:nth-child(even) td{background:#141416;}"),
        ("body.dark tr:hover td{background:#1f2a38;}", "body.dark tr:hover td{background:#26262A;}"),
        ("body.dark .warn{background:#3a1f1c; border:1px solid #7a3a32; color:#e8948a;}",
         "body.dark .warn{background:#3A1B16; border:1px solid #7A3328; color:#F09595;}"),
        ("body.dark .mapbox{background:#11161d;", "body.dark .mapbox{background:#111113;"),
        ("  body.dark{transition:none}", "  body{transition:none}\n  .card{transition:none}"),
    ]:
        css = replace_once(css, old, new)

    # ---------- 6. 追加：动效 + dm 按钮 + 375px + 字体（幂等标记） ----------
    if MARK not in css:
        n, font_blocks = extract_site_fonts(read(SITE_THEME))
        addon = "\n" + MARK + "\n"
        if n:
            addon += ("\n/* ===== HarmonyOS Sans SC 内嵌（cn-font-split 分片，"
                      "与站点 assets/fonts 同源；产物/fonts/ 本地自包含）===== */\n" + font_blocks + "\n")
        addon += """
/* ---- 动效：卡片浮起（只动 transform/box-shadow，弹性曲线） ---- */
.card{transition:transform var(--dur-base) var(--ease-spring),box-shadow var(--dur-base) var(--ease-out)}
.card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(10,89,247,.10)}

/* ---- dm-toggle 鸿蒙胶囊化（覆盖 JS 注入的旧样式） ---- */
.dm-toggle{border-radius:999px!important;font-family:var(--sans)!important;font-size:12.5px!important;font-weight:500!important;
  padding:7px 16px!important;border:1px solid var(--line)!important;background:var(--surface)!important;
  color:var(--primary)!important;box-shadow:var(--shadow)!important;
  transition:transform var(--dur-base) var(--ease-spring),background-color var(--dur-fast) var(--ease-std),color var(--dur-fast) var(--ease-std)!important}
.dm-toggle:hover{transform:translateY(-2px)!important}

/* ---- 375px 级小屏补充 ---- */
@media(max-width:400px){
  h1{font-size:18px;padding:12px 14px;letter-spacing:.5px}
  h2{font-size:17px}
  table{font-size:13px}
  .metric{min-width:112px;margin:4px;}
}
"""
        css = css + addon
        print("  [字体] 内嵌 @font-face %d 条" % n)
    else:
        print("  [跳过] 追加块已存在")

    write(THEME, css)
    print("theme.css 鸿蒙化完成：%s" % THEME)


if __name__ == "__main__":
    main()
