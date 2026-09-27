#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《苇舟江湖梦》知识性索引数据库 构建脚本
读取 docx -> 产出 knowledge_base.json (可查询数据库) + CSV 导出。
"""
import json, re, os
from collections import defaultdict, Counter
from docx import Document

SRC = r"F:/Users/FrostStarInquire/Downloads/苇舟江湖梦.docx"
OUTDIR = os.path.dirname(os.path.abspath(__file__))

# ---------- 人物花名册（策展，可扩展）----------
# role: 主/配/待定 ; side: 江湖/朝堂/战场/门派/亲属 ...（按出镜粗略归类，作者可改）
CHARACTERS = {
    "任琅":    {"role": "主", "side": "江湖", "note": "男主，执打刀的少年，立誓出山看世界"},
    "尚樱":    {"role": "主", "side": "江湖", "note": "女主，蓝眼少女，月下与任琅比刀"},
    "夏叶":    {"role": "配", "side": "门派", "note": "多次主动寻任琅比试"},
    "刘笑岩":  {"role": "配", "side": "门派", "note": "常与夏叶同场"},
    "陈奉天":  {"role": "配", "side": "朝堂", "note": "朝中人物，多章传唤任琅/尚樱"},
    "许达":    {"role": "配", "side": "待定", "note": ""},
    "苏雨":    {"role": "配", "side": "待定", "note": ""},
    "赵翔":    {"role": "配", "side": "待定", "note": ""},
    "刑布":    {"role": "配", "side": "战场", "note": ""},
    "马远":    {"role": "配", "side": "待定", "note": ""},
    "赵骁":    {"role": "配", "side": "战场", "note": "骑兵追击牛金"},
    "苏沐文":  {"role": "配", "side": "待定", "note": ""},
    "张潇璃":  {"role": "配", "side": "待定", "note": ""},
    "李博":    {"role": "配", "side": "待定", "note": ""},
    "聂林":    {"role": "配", "side": "待定", "note": ""},
    "尚衫虎":  {"role": "配", "side": "待定", "note": ""},
    "虞环":    {"role": "配", "side": "朝堂", "note": "尚樱曾旁听其早朝；被称'虞环姐'"},
    "王芣":    {"role": "配", "side": "待定", "note": ""},
    "刑泰":    {"role": "配", "side": "战场", "note": "兵败投降"},
    "牛银":    {"role": "配", "side": "战场", "note": ""},
    "牛金":    {"role": "配", "side": "战场", "note": "撤兵，被赵骁追击"},
    "刘基":    {"role": "待定", "side": "待定", "note": ""},
    "张洵":    {"role": "待定", "side": "待定", "note": ""},
    "张百慧":  {"role": "待定", "side": "待定", "note": ""},
    "李叔":    {"role": "待定", "side": "待定", "note": ""},
    "李月婵":  {"role": "待定", "side": "待定", "note": ""},
    "刘媛灵":  {"role": "配", "side": "江湖", "note": "早期与任琅比试的少女(蓝眼?)关联人物"},
    "张广义":  {"role": "待定", "side": "待定", "note": ""},
    "赵穗良":  {"role": "待定", "side": "待定", "note": ""},
    "陈番":    {"role": "待定", "side": "朝堂", "note": "疑为陈奉天下属"},
    "苏氏":    {"role": "待定", "side": "待定", "note": ""},
    "夏寂然":  {"role": "配", "side": "战场", "note": "令刑泰返回调集部队"},
    "任瑛":    {"role": "配", "side": "待定", "note": "尚樱曾托付府上事务"},
}

# 关系事实（已知，作者可扩）—— type: 同伴/情侣/师徒/君臣/敌/亲 ...
RELATIONS = [
    ("任琅", "尚樱", "同伴/羁绊", "开篇月下比刀，相伴出山"),
    ("夏叶", "刘笑岩", "同门/搭档", "多次同场比试任琅"),
    ("虞环", "尚樱", "引荐/朝堂", "尚樱旁听其早朝"),
    ("赵骁", "牛金", "敌/战场", "牛金撤兵，赵骁率骑兵追击"),
    ("夏寂然", "刑泰", "上下级", "令刑泰返回调集后续部队"),
    ("尚樱", "任瑛", "托付", "尚樱将府上事务托付任瑛"),
]

# 地点/场景关键词 -> 标签（多字优先，单字不与其重叠，避免"一阵/山河"误匹配）
SCENE_KW = {
    "江湖": "江湖", "早朝": "朝堂", "战场": "战场", "客栈": "客栈", "驿站": "驿站",
    "村": "村落", "庄": "庄院", "府": "府邸", "城": "城池", "宫": "宫阙",
    "山": "山野", "林": "林间", "寺": "寺观", "庙": "庙宇",
}

def split_chapters(doc):
    chapters = []
    cur = None; buff = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if p.style.name == 'Heading 2':
            if cur is not None:
                chapters.append({"title": cur, "text": "".join(buff)})
            cur = t; buff = []
        else:
            if t:
                buff.append(t)
    if cur is not None:
        chapters.append({"title": cur, "text": "".join(buff)})
    return chapters

def main():
    doc = Document(SRC)
    chapters = split_chapters(doc)
    meta = {
        "title": "苇舟江湖梦",
        "author": "霜月仲明",
        "source_file": SRC,
        "chapter_count": len([c for c in chapters if c["title"] != "自序"]),
        "has_preface": any(c["title"] == "自序" for c in chapters),
    }

    chap_list = []
    for i, c in enumerate(chapters):
        text = c["text"]
        cnt = len(text)
        opening = ""
        for para in re.split(r"[。！？\n]", text):
            para = para.strip()
            if len(para) >= 4:
                opening = para
                break
        # presence + mention counts
        present = {}
        for name in CHARACTERS:
            n = text.count(name)
            if n > 0:
                present[name] = n
        # scene tags
        tags = Counter()
        for kw, label in SCENE_KW.items():
            if kw in text:
                tags[label] += text.count(kw)
        chap_list.append({
            "idx": i,
            "title": c["title"],
            "is_preface": c["title"] == "自序",
            "chars": cnt,
            "opening": opening[:60],
            "text": text,
            "presence": present,
            "scenes": dict(tags.most_common(6)),
        })

    # character profiles (with timeline = per-chapter mention)
    char_profiles = {}
    timeline = {name: [] for name in CHARACTERS}
    for ci, c in enumerate(chap_list):
        for name, n in c["presence"].items():
            timeline[name].append({"ch": ci, "n": n})
    for name, info in CHARACTERS.items():
        mentions = sum(c["presence"].get(name, 0) for c in chap_list)
        chaps_present = [c["idx"] for c in chap_list if name in c["presence"]]
        char_profiles[name] = {
            **info,
            "total_mentions": mentions,
            "chapter_count": len(chaps_present),
            "first_chapter": chaps_present[0] if chaps_present else None,
            "last_chapter": chaps_present[-1] if chaps_present else None,
            "chapters": chaps_present,
            "timeline": timeline[name],
        }

    # relationship co-occurrence edges (derived)
    cooccur = defaultdict(int)
    for c in chap_list:
        names = list(c["presence"].keys())
        for a in range(len(names)):
            for b in range(a + 1, len(names)):
                cooccur[(names[a], names[b])] += 1
    rel_edges = []
    for (a, b), n in sorted(cooccur.items(), key=lambda x: -x[1]):
        if n >= 2:
            rel_edges.append({"a": a, "b": b, "co_chapters": n})
    # attach known relation facts
    known = {(x[0], x[1]): x for x in RELATIONS}
    for e in rel_edges:
        k = (e["a"], e["b"])
        if k in known:
            e["type"] = known[k][2]
            e["desc"] = known[k][3]
        elif (e["b"], e["a"]) in known:
            e["type"] = known[(e["b"], e["a"])][2]
            e["desc"] = known[(e["b"], e["a"])][3]

    kb = {
        "meta": meta,
        "chapters": chap_list,
        "characters": char_profiles,
        "relations_known": [{"a": x[0], "b": x[1], "type": x[2], "desc": x[3]} for x in RELATIONS],
        "relations_cooccur": rel_edges,
    }

    with open(os.path.join(OUTDIR, "knowledge_base.json"), "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

    # CSV exports
    import csv
    with open(os.path.join(OUTDIR, "characters.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["姓名", "角色", "阵营", "总提及", "出场章数", "首出场章", "末出场章", "备注"])
        for name, p in sorted(char_profiles.items(), key=lambda x: -x[1]["total_mentions"]):
            w.writerow([name, p["role"], p["side"], p["total_mentions"], p["chapter_count"],
                        p["first_chapter"], p["last_chapter"], p["note"]])
    with open(os.path.join(OUTDIR, "chapters.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["章序", "标题", "字数", "首句", "场景标签", "出场人物数"])
        for c in chap_list:
            w.writerow([c["idx"], c["title"], c["chars"], c["opening"],
                        ",".join(c["scenes"].keys()), len(c["presence"])])

    print("chapters:", len(chap_list))
    print("characters:", len(char_profiles))
    print("cooccur edges(>=2):", len(rel_edges))
    print("total mentions sum:", sum(p["total_mentions"] for p in char_profiles.values()))

if __name__ == "__main__":
    main()
