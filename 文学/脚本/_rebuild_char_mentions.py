#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建 char_stats.json 中单字角色「影」的 mentions / chapters_present / first / last，
修正单字子串统计把光影泛指词（身影/背影/人影/阴影/影子…）误计入角色提及的污染。

问题：原 char_stats（更早会话产物，仓库无生成脚本）对单字名「影」用 full_text.count("影") 统计，
      使 210 次「影」中约 120 次为光影泛指词（占 57%），并令 chapters_present=46 虚高、
      与真实登场(all_tags)的「背离」被放大为 35（实为污染所致）。

修复：以「影象词否定清单」从文本中删除这些泛指词后，再统计「影」的净出现，
      从而重算 mentions / chapters_present / first / last。其余 48 个多字名不受影响。

仅覆盖 char_stats.json 的「影」条目，保留其它条目与字段；覆盖前自动备份为 .bak。
"""
import json, os, re, shutil, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "数据", "full_text.txt")
CS = os.path.join(ROOT, "数据", "char_stats.json")
CHAP_DIR = os.path.join(ROOT, "数据", "chapter_data")
TARGET = "影"

# 光影 / 身形泛指词（非特指名为「影」的角色）；含「影子」(7处，疑角色昵称，暂按泛指剔除并标注)
SHADOW = {
    "身影", "背影", "人影", "踪影", "阴影", "黑影", "影子", "的影", "无影", "见影",
    "暗影", "幻影", "倒影", "残影", "魅影", "疏影", "掠影", "泡影", "影影", "虚影", "憧影",
    "倩影", "侧影", "形影", "魔影", "淡影", "孤影", "月影", "云影", "树影", "花影", "灯影",
    "窗影", "墙影", "壁影", "波影", "雪影", "风影", "寒影", "清影", "幽影", "杯影", "镜影",
    "顾影", "望影", "随影", "逐影", "捕影", "吊影", "畏影",
}


def clean(text):
    """剔除所有光影泛指词（保留长度，避免改变其它字符位置）。"""
    t = text
    for w in SHADOW:
        if w in t:
            t = t.replace(w, "　" * len(w))
    return t


def main():
    ft = open(SRC, encoding="utf-8").read()
    cs = json.load(open(CS, encoding="utf-8"))

    # 定位「影」条目
    idx = next(i for i, e in enumerate(cs) if e.get("name") == TARGET)
    old = dict(cs[idx])

    # 净提及：剔除泛指词后统计「影」
    clean_ft = clean(ft)
    new_mentions = clean_ft.count(TARGET)

    # 逐章净在场（仅当章内出现非泛指词的「影」才算在场）
    chaps = sorted(glob.glob(os.path.join(CHAP_DIR, "chap_*.txt")))
    present = []
    for i, f in enumerate(chaps):
        t = clean(open(f, encoding="utf-8").read())
        if t.count(TARGET) > 0:
            present.append(i)
    new_cp = len(present)
    new_first = min(present) if present else None
    new_last = max(present) if present else None

    cs[idx]["mentions"] = new_mentions
    cs[idx]["chapters_present"] = new_cp
    cs[idx]["first"] = new_first
    cs[idx]["last"] = new_last

    # 备份后覆盖
    bak = CS + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(CS, bak)
    with open(CS, "w", encoding="utf-8") as f:
        json.dump(cs, f, ensure_ascii=False, indent=2)

    print(f"角色「{TARGET}」修正:")
    print(f"  mentions        : {old['mentions']} -> {new_mentions}")
    print(f"  chapters_present: {old['chapters_present']} -> {new_cp}")
    print(f"  first/last      : {old['first']}/{old['last']} -> {new_first}/{new_last}")
    print(f"  剔除光影泛指词约 {ft.count(TARGET)-new_mentions} 处（占原 {ft.count(TARGET)} 的 "
          f"{(ft.count(TARGET)-new_mentions)/ft.count(TARGET)*100:.0f}%）")
    print(f"备份: {bak}")


if __name__ == "__main__":
    main()
