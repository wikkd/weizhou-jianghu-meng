# -*- coding: utf-8 -*-
"""D3 精彩对打动作量化：在 combat_intensity>=2 的战斗章中，按 6 类动作词表抽取，
生成动作词表（含归属角色/章节/证据）+ 逐章动作 + 招式序列 bigram。含 D5 兵器/功法（technique 类）。
产出 数据/combat_actions.json。
"""
import os, json
from collections import defaultdict
from _quant_common import (ROOT, DATA, load_full_text, load_all_tags,
                           char_paragraphs)

ACTION_LEX = {
    "兵器": ["劈", "砍", "斩", "刺", "挑", "撩", "格", "挡", "架", "削", "点", "崩", "截", "缠", "封", "剁", "挥", "抡", "扫"],
    "身法": ["纵", "跃", "闪", "避", "旋", "翻", "掠", "腾", "窜", "疾走", "落", "掠", "斜刺", "错步"],
    "内力": ["运功", "吐纳", "内力", "真气", "罡气", "气劲", "内劲", "震", "涌", "灌", "爆", "气流"],
    "招式": ["剑气", "掌风", "拳影", "腿影", "指风", "刀芒", "剑芒", "残影", "虚影", "剑光", "刀光", "掌影", "鞭影"],
    "防守": ["卸", "化", "引", "借力", "闪避", "格挡", "封挡", "腾挪", "化解", "避让"],
    "伤效": ["血溅", "断臂", "洞穿", "震退", "击飞", "封喉", "贯胸", "吐血", "重伤", "倒地", "喷血", "裂"],
}


def build():
    chapters = load_full_text()
    tags = load_all_tags()
    combat = [t for t in tags if t.get("combat_intensity", 0) >= 2]
    combat_idx = {t["chapter"] for t in combat}
    # 章节 -> 出场角色
    ch_chars = {t["chapter"]: t.get("characters_present", []) for t in combat}

    # 全局词表计数 + 证据 + 归属角色/章节
    vocab_freq = defaultdict(int)
    vocab_ch = defaultdict(set)
    vocab_chars = defaultdict(set)
    vocab_ctx = {}
    by_chapter = defaultdict(list)
    seq = defaultdict(int)

    # 逐战斗章段落扫描
    for ch in chapters:
        if ch["idx"] not in combat_idx:
            continue
        present = ch_chars.get(ch["idx"], [])
        for p in ch["paragraphs"]:
            para_actions = []
            for cat, words in ACTION_LEX.items():
                for w in words:
                    c = p.count(w)
                    if c == 0:
                        continue
                    vocab_freq[w] += c
                    vocab_ch[w].add(ch["idx"])
                    by_chapter[ch["idx"]].append(w)
                    para_actions.append(w)
                    # 归属：本段出现过的出场角色
                    for nm in present:
                        if nm in p:
                            vocab_chars[w].add(nm)
                    if w not in vocab_ctx:
                        i = p.find(w)
                        s = max(0, i - 20); e = min(len(p), i + len(w) + 20)
                        vocab_ctx[w] = {"chapter": ch["idx"], "context": p[s:e]}
            # 序列 bigram（段落内动作出现序）
            for a, b in zip(para_actions, para_actions[1:]):
                if a != b:
                    seq[a + "→" + b] += 1

    vocab = []
    for w, f in vocab_freq.items():
        # 反查类别
        cat = next((k for k, ws in ACTION_LEX.items() if w in ws), "其它")
        vocab.append({
            "action": w, "category": cat, "freq": f,
            "chapters": sorted(vocab_ch[w]),
            "characters": sorted(vocab_chars[w]),
            "sample_context": vocab_ctx.get(w, {}).get("context", ""),
        })
    vocab.sort(key=lambda x: -x["freq"])

    sequences = [{"bigram": k, "freq": v} for k, v in
                 sorted(seq.items(), key=lambda x: -x[1]) if v >= 2][:40]

    result = {
        "vocab": vocab,
        "by_chapter": {str(k): v for k, v in sorted(by_chapter.items())},
        "sequences": sequences,
        "stats": {
            "combat_chapters": len(combat_idx),
            "distinct_actions": len(vocab),
            "total_action_hits": sum(vocab_freq.values()),
            "categories": {k: sum(1 for v in vocab if v["category"] == k) for k in ACTION_LEX},
        },
    }
    return result


if __name__ == "__main__":
    res = build()
    out = os.path.join(DATA, "combat_actions.json")
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written", out, "| combat chapters:", res["stats"]["combat_chapters"],
          "| distinct actions:", res["stats"]["distinct_actions"])
    print("category counts:", res["stats"]["categories"])
    print("--- top 12 actions ---")
    for v in res["vocab"][:12]:
        print(" ", v["category"], v["action"], "×", v["freq"], "| chars", len(v["characters"]), "| ch", len(v["chapters"]))
    print("--- top 8 sequences ---")
    for s in res["sequences"][:8]:
        print(" ", s["bigram"], "×", s["freq"])
