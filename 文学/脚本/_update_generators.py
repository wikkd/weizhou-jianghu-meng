#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性脚本：将各报告生成器脚本中的内联 style 块替换为 theme.css 链接，
使下次重跑报告仍保持统一风格。
- 13_build_archive.py 输出位于 产物/数据归档/，故链接用 ../theme.css
- 其余生成器输出位于 产物/，链接用 theme.css
- 顺手删除 14/15/16 中因替换而闲置的 css 变量（原三引号赋值块）
幂等：已无 style 则跳过。
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "脚本")

TARGETS = [
    "03_run_stats.py", "04_run_stylometry.py", "05_lexical_analysis.py",
    "06_run_sentiment.py", "07_build_network.py", "08_generate_report.py",
    "09_generate_spatial_report.py", "10_generate_guanzhi.py",
    "11_generate_text_map.py", "12_generate_tag_dashboard.py",
    "13_build_archive.py", "14_chapter_structure.py",
    "15_time_rhythm.py", "16_derived_dims.py",
]
SUBDIR = {"13_build_archive.py"}  # 输出在 产物/数据归档/

style_re = re.compile(r"<style>.*?</style>", re.DOTALL | re.IGNORECASE)
cssvar_re = re.compile(r'css\s*=\s"""[\s\S]*?"""\n?', re.IGNORECASE)

def main():
    for name in TARGETS:
        p = os.path.join(SCRIPTS, name)
        if not os.path.exists(p):
            print("[缺失] " + name)
            continue
        with open(p, encoding="utf-8") as f:
            s = f.read()
        if not style_re.search(s):
            print("[跳过-已链接] " + name)
            continue
        rel = "../theme.css" if name in SUBDIR else "theme.css"
        s = style_re.sub('<link rel="stylesheet" href="' + rel + '">', s, count=1)
        s2 = cssvar_re.sub("", s)
        if s2 != s:
            print("[替换+清冗余css] " + name)
        else:
            print("[替换] " + name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(s2)
    print("\n完成。")

if __name__ == "__main__":
    main()
