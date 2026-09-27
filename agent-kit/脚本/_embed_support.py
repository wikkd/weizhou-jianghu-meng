#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 产物/ 下各报告注入"嵌入态"支持（幂等）。

当报告以 `?embed=1` 载入图书馆 iframe 时：
  - 给 <body> 加 `embed` 类，由 glass.css 的 embed 规则隐藏独立浮层控件；
  - 监听父窗口 postMessage，同步深色主题与主题色（wzTheme / wzAccent）。

已含标记的文件跳过，可反复运行。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # 产物/
OUT_DIR = os.path.join(ROOT, "产物") if os.path.isdir(os.path.join(ROOT, "产物")) else ROOT

MARK = "data-wz-embed"
SNIPPET = (
    '<script ' + MARK + '>'
    'try{if(location.search.indexOf("embed")>=0){'
    'document.body.classList.add("embed");'
    'document.addEventListener("message",function(e){'
    'if(!e.data)return;'
    'if(e.data.wzTheme){document.body.classList.toggle("dark",e.data.wzTheme==="dark");}'
    'if(e.data.wzAccent){var r=document.documentElement.style;'
    'r.setProperty("--primary",e.data.wzAccent);}'
    '});}}catch(e){}</script>'
)

BODY_RE = re.compile(r"<body[^>]*>", re.IGNORECASE)


def inject(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    if MARK in html:
        return "skip"
    m = BODY_RE.search(html)
    if not m:
        return "nobody"
    # 在 <body ...> 之后插入（尽早生效，避免闪烁）
    html = html[: m.end()] + "\n" + SNIPPET + html[m.end():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return "ok"


def main():
    if not os.path.isdir(OUT_DIR):
        print("未找到产物目录:", OUT_DIR)
        sys.exit(1)
    files = sorted(
        f for f in os.listdir(OUT_DIR)
        if f.endswith(".html") and f != "苇舟江湖梦_图书馆.html"
    )
    ok = skip = nobody = 0
    for fn in files:
        res = inject(os.path.join(OUT_DIR, fn))
        if res == "ok":
            ok += 1
            print("  + 注入", fn)
        elif res == "skip":
            skip += 1
        else:
            nobody += 1
            print("  ! 无 <body>", fn)
    print("\n完成：新增 %d · 已存在 %d · 异常 %d" % (ok, skip, nobody))


if __name__ == "__main__":
    main()
