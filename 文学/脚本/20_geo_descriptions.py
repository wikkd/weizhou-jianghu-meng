# -*- coding: utf-8 -*-
"""D4 地点地理描述量化：对每个 spatial 地点名，抓其语境段落中含地形/气候/地标关键词的描述句，
归类地形类型，聚合 geo_features.json 的 17 项要素与相对坐标。产出 数据/geo_profile.json。
"""
import os, re, json
from collections import defaultdict, Counter
from _quant_common import (ROOT, DATA, load_full_text, load_loc_names, load_all_tags)

# 地形归类词表
TERRAIN = {
    "山岳型": ["山", "峰", "岭", "崖", "谷", "岩", "峭", "巍峨", "险峻", "崇山", "群山"],
    "水滨型": ["江", "河", "湖", "渡", "溪", "潭", "海", "波", "舟", "水滨", "码头"],
    "城郭型": ["城", "郡", "关", "镇", "墙", "街", "市", "郭", "府", "衙门"],
    "关隘型": ["关", "隘", "口", "塞", "卡"],
    "平原型": ["原", "野", "田", "旷", "平川", "麦田", "平原"],
}
CLIMATE = ["风寒", "湿润", "严寒", "酷热", "多雨", "风沙", "晴朗", "阴冷", "料峭", "萧瑟"]
SENT_SPLIT = re.compile(r"[。！？]")
# 地名本身含地形提示字（未明时回退）
NAME_TERR = [("山岳型", ["山", "岭", "峰", "崖", "谷"]), ("水滨型", ["湖", "河", "江", "渡", "海", "溪", "潭"]),
             ("城郭型", ["城", "郡", "镇", "市", "府"]), ("关隘型", ["关", "隘", "塞"]), ("平原型", ["原", "野", "田"])]
def classify(excerpts):
    cnt = Counter()
    for ex in excerpts:
        for t, words in TERRAIN.items():
            if any(w in ex for w in words):
                cnt[t] += 1
    if not cnt:
        return "未明"
    return cnt.most_common(1)[0][0]


def classify_by_name(loc):
    for t, chars in NAME_TERR:
        if any(c in loc for c in chars):
            return t
    return "未明"


def build():
    chapters = load_full_text()
    tags = load_all_tags()
    sp = json.load(open(os.path.join(DATA, "spatial_data.json"), encoding="utf-8"))
    gf = json.load(open(os.path.join(DATA, "geo_features.json"), encoding="utf-8"))
    features = gf.get("features", [])
    nodes = sp.get("nodes", {})

    # 地点集合 = spatial 节点 ∪ 全本 main_locations（覆盖完整性；坐标/要素仅 spatial 有）
    narrative_locs = set()
    for t in tags:
        for ml in t.get("main_locations", []):
            narrative_locs.add(ml)
    locs = sorted(set(load_loc_names()) | narrative_locs, key=lambda n: (-len(n), n))

    result = {}
    for loc in locs:
        paras = []
        excerpts = []
        climate_hits = Counter()
        for ch in chapters:
            for p in ch["paragraphs"]:
                if loc not in p:
                    continue
                paras.append((ch["idx"], p))
                # 描述句：含地名且含地形/气候关键词
                for sent in SENT_SPLIT.split(p):
                    if loc in sent and any(w in sent for w in sum(TERRAIN.values(), []) + CLIMATE):
                        excerpts.append({"chapter": ch["idx"], "text": sent.strip()})
                for cw in CLIMATE:
                    if cw in p:
                        climate_hits[cw] += 1
        terrain = classify([e["text"] for e in excerpts])
        if terrain == "未明":
            terrain = classify_by_name(loc)
        # 聚合要素
        feats = []
        for f in features:
            if f.get("anchor") == loc or f.get("name") == loc or f.get("attr", {}).get("关联地标") == loc:
                feats.append({"name": f["name"], "type": f["type"], "attr": f.get("attr", {})})
        # 相对坐标
        coord = nodes.get(loc)
        pos = None
        if isinstance(coord, dict) and ("x" in coord or "px" in coord or "cx" in coord):
            pos = {k: coord[k] for k in ("x", "y", "px", "py", "cx", "cy") if k in coord}
        result[loc] = {
            "location": loc,
            "paragraphs": len(paras),
            "terrain_type": terrain,
            "climate_hints": [c for c, _ in climate_hits.most_common(4)],
            "features": feats,
            "excerpts": excerpts[:6],
            "relative_pos": pos,
        }
    return result


if __name__ == "__main__":
    res = build()
    out = os.path.join(DATA, "geo_profile.json")
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    terr = Counter(v["terrain_type"] for v in res.values())
    with_feat = sum(1 for v in res.values() if v["features"])
    with_exc = sum(1 for v in res.values() if v["excerpts"])
    print("written", out, "| locations:", len(res))
    print("terrain dist:", dict(terr))
    print("with features:", with_feat, "| with excerpts:", with_exc)
    for loc in ["卫京郡", "镜湖", "南岭关", "望岳镇"]:
        v = res.get(loc, {})
        print(" ", loc, "->", v.get("terrain_type"), "| feats", len(v.get("features", [])),
              "| excerpts", len(v.get("excerpts", [])), "| cli", v.get("climate_hints"))
