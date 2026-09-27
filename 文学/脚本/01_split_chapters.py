#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 full_text.txt 按章节标记（一、二、...五十九、）切分为 59 个独立章节文本文件，
并输出章节索引 chapters_index.json，供 subagent 标注与后续量化聚合使用。"""
import re, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC = os.path.join(ROOT, "数据", "full_text.txt")
OUT_DIR = os.path.join(ROOT, "数据", "chapter_data")
CN_DIGIT = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4,
            "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
CN_UNIT = {"十": 10, "百": 100}

def cn_to_int(s: str) -> int:
    """将中文数字（支持到百位，如 五十九）转为整数。"""
    if s.isdigit():
        return int(s)
    total, cur, has_digit = 0, 0, False
    for ch in s:
        if ch in CN_DIGIT:
            cur = CN_DIGIT[ch]
            has_digit = True
        elif ch in CN_UNIT:
            unit = CN_UNIT[ch]
            if not has_digit:
                cur = 1
            total += cur * unit
            cur, has_digit = 0, False
    total += cur
    return total

MARKER = re.compile(r'^([一二三四五六七八九十百零〇\d]+)[、．.]\s*$')

def main():
    with open(SRC, encoding="utf-8") as f:
        lines = f.read().split("\n")

    markers = []  # (line_index, cn_str, int_val)
    for i, ln in enumerate(lines):
        m = MARKER.match(ln)
        if m:
            markers.append((i, m.group(1), cn_to_int(m.group(1))))

    markers.sort(key=lambda x: x[2])
    # 校验连续 1..59
    seq = [v for _, _, v in markers]
    assert seq == list(range(1, len(seq) + 1)), f"章节序号不连续: {seq}"

    os.makedirs(OUT_DIR, exist_ok=True)
    index = []
    for idx, (li, cn, val) in enumerate(markers):
        start = li + 1
        end = markers[idx + 1][0] if idx + 1 < len(markers) else len(lines)
        body = lines[start:end]
        # 去除首尾空行
        while body and body[0].strip() == "":
            body.pop(0)
        while body and body[-1].strip() == "":
            body.pop()
        text = "\n".join(body)
        fname = f"chap_{val:02d}.txt"
        with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as fo:
            fo.write(text)
        # 章节首行若为地点/场景标题（短且无标点），记录为 scene_hint
        first = body[0].strip() if body else ""
        index.append({
            "chapter": val,
            "cn": cn,
            "file": fname,
            "chars": len(text),
            "scene_hint": first if (first and len(first) <= 12) else None,
        })

    with open(os.path.join(OUT_DIR, "chapters_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"已切分 {len(markers)} 章 -> {OUT_DIR}/")
    print("总字符(章节正文):", sum(x['chars'] for x in index))

if __name__ == "__main__":
    main()
