#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量重建 char_stats.json 的 mentions / chapters_present / first / last。
从新版 full_text + 切分后的 chap_*.txt 重算 49 位规范人物的全文提及、在场章数、首/末出场。
- 单字名「影」沿用否定清单（剔除光影泛指词）避免子串污染；其余多字名直接计数。
- 覆盖前自动备份 char_stats.json -> .bak。
用法：python 脚本/_rebuild_char_stats.py
"""
import json, os, glob, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "数据", "full_text.txt")
CS = os.path.join(ROOT, "数据", "char_stats.json")
CHAP_DIR = os.path.join(ROOT, "数据", "chapter_data")

# 仅「影」为单字名，沿用光影泛指词否定清单
SHADOW = {
    "身影", "背影", "人影", "踪影", "阴影", "黑影", "影子", "的影", "无影", "见影",
    "暗影", "幻影", "倒影", "残影", "魅影", "疏影", "掠影", "泡影", "影影", "虚影", "憧影",
    "倩影", "侧影", "形影", "魔影", "淡影", "孤影", "月影", "云影", "树影", "花影", "灯影",
    "窗影", "墙影", "壁影", "波影", "雪影", "风影", "寒影", "清影", "幽影", "杯影", "镜影",
    "顾影", "望影", "随影", "逐影", "捕影", "吊影", "畏影",
}


def clean(text):
    t = text
    for w in SHADOW:
        if w in t:
            t = t.replace(w, "　" * len(w))
    return t


def main():
    ft = open(SRC, encoding="utf-8").read()
    cs = json.load(open(CS, encoding="utf-8"))

    # 全本「影」净文本
    clean_global = clean(ft)

    # 章节文件按编号排序
    chap_files = sorted(glob.glob(os.path.join(CHAP_DIR, "chap_*.txt")))
    chap_idx = []
    for f in chap_files:
        base = os.path.basename(f)
        try:
            num = int(base[5:7]) if base[5:7].isdigit() else int(base[5:6])
        except Exception:
            continue
        chap_idx.append((num, f))

    for e in cs:
        name = e["name"]
        if name == "影":
            mentions = clean_global.count("影")
            present = []
            for num, f in chap_idx:
                t = clean(open(f, encoding="utf-8").read())
                if t.count("影") > 0:
                    present.append(num)
        else:
            mentions = ft.count(name)
            present = []
            for num, f in chap_idx:
                if name in open(f, encoding="utf-8").read():
                    present.append(num)
        e["mentions"] = mentions
        e["chapters_present"] = len(present)
        e["first"] = min(present) if present else None
        e["last"] = max(present) if present else None

    bak = CS + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(CS, bak)
    with open(CS, "w", encoding="utf-8") as f:
        json.dump(cs, f, ensure_ascii=False, indent=2)

    print(f"已重建 {len(cs)} 位人物计数 -> {CS}")
    print("新 mentions 合计:", sum(e["mentions"] for e in cs))
    # 抽样展示几人
    for nm in ("任琅", "陈奉天", "影", "尚樱"):
        e = next(x for x in cs if x["name"] == nm)
        print(f"  {nm}: mentions={e['mentions']} chapters_present={e['chapters_present']} first/last={e['first']}/{e['last']}")


if __name__ == "__main__":
    main()
