#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性后处理：将 产物/ 下所有 HTML 报告的内联 <style>...</style> 替换为
<link rel="stylesheet" href="theme.css">，统一页面风格。

- 直接位于 产物/ 的文件 → href="theme.css"
- 位于子目录（如 产物/数据归档/）的文件 → href="../theme.css"
- 仅替换 <style> 标签块，正文/图表的内联 style="..." 属性不受影响。
- 幂等：已无 <style> 的文件跳过。
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根
PROD = os.path.join(ROOT, "产物")
THEME = "theme.css"

style_re = re.compile(r"<style>.*?</style>", re.DOTALL | re.IGNORECASE)
link_tmpl = '<link rel="stylesheet" href="{}">'

def rel_for(path):
    # 若文件不在 产物/ 直接子级，则用 ../ 回退到 产物/
    if os.path.dirname(path) == PROD:
        return THEME
    return "../" + THEME

def main():
    htmls = []
    for dp, _, fns in os.walk(PROD):
        for fn in fns:
            if fn.lower().endswith(".html"):
                htmls.append(os.path.join(dp, fn))
    htmls.sort()
    changed = skipped = 0
    for p in htmls:
        with open(p, encoding="utf-8") as f:
            s = f.read()
        if not style_re.search(s):
            # 检查是否已有链接，避免误判
            if "theme.css" in s:
                print(f"[跳过-已链接] {os.path.relpath(p, ROOT)}")
                skipped += 1
            else:
                print(f"[警告-无style无link] {os.path.relpath(p, ROOT)}")
            continue
        new_s = style_re.sub(link_tmpl.format(rel_for(p)), s)
        with open(p, "w", encoding="utf-8") as f:
            f.write(new_s)
        print(f"[已替换] {os.path.relpath(p, ROOT)}  ({s.count('<style>')} 处 style)")
        changed += 1
    print(f"\n完成：替换 {changed} 个，跳过/已链接 {skipped} 个，共扫描 {len(htmls)} 个 HTML。")

if __name__ == "__main__":
    main()
