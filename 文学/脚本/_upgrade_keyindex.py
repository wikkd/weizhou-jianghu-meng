# -*- coding: utf-8 -*-
"""
将「关键词原文索引」挂件注入 产物/ 下各报告页（幂等）。

注入内容（锚点 <!--WZ-KEYINDEX-START/END--> 包裹，已注入则跳过）：
  <div id="wz-kwindex"></div>            —— 挂件渲染容器
  <script src="keyword-index-widget.js"></script>  —— 自包含挂件（内嵌数据）

挂件点击任一关键词 → 新标签页打开《原文阅读》并高亮该词全部位置。

不注入：原文阅读页、关键词索引专页、theme.css / echarts-kit.js / 挂件本身。
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "产物")

# 需注入的报告页（排除 reader / 索引专页 / 非 html 资源）
TARGETS = [
    "苇舟江湖梦_人物关系网络.html",
    "苇舟江湖梦_分析报告.html",
    "苇舟江湖梦_地理位置关系图.html",
    "苇舟江湖梦_官制考究.html",
    "苇舟江湖梦_情感时序.html",
    "苇舟江湖梦_时间节奏量化.html",
    "苇舟江湖梦_派生维度量化.html",
    "苇舟江湖梦_空间地点分析报告.html",
    "苇舟江湖梦_章节标签量化看板.html",
    "苇舟江湖梦_章节结构量化.html",
    "苇舟江湖梦_统计推断.html",
    "苇舟江湖梦_词汇计量.html",
    "苇舟江湖梦_风格计量.html",
    "川阴王建都推演.html",
]

BLOCK = (
    "<!--WZ-KEYINDEX-START-->\n"
    '<div id="wz-kwindex"></div>\n'
    '<script src="keyword-index-widget.js"></script>\n'
    "<!--WZ-KEYINDEX-END-->\n"
)


def inject(name):
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        print("跳过（不存在）:", name)
        return
    txt = io.open(path, encoding="utf-8").read()
    if "WZ-KEYINDEX-START" in txt:
        print("已注入，跳过:", name)
        return
    if "</body>" not in txt:
        print("无 </body>，跳过:", name)
        return
    head, sep, tail = txt.rpartition("</body>")
    out = head + sep + BLOCK + tail
    io.open(path, "w", encoding="utf-8").write(out)
    print("已注入:", name)


def main():
    for t in TARGETS:
        inject(t)


if __name__ == "__main__":
    main()
