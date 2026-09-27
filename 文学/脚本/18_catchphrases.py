# -*- coding: utf-8 -*-
"""D2 口头禅 / 标志语量化：抽取对话归属（X说/道…「quote」），按最近前置角色名归并，
识别复现整句与标志 n-gram。产出 数据/catchphrases.json。
自动词表抽取；单字名（影/空/福）用否定清单排除光影/天空等泛指错归。
"""
import os, re, json
from collections import defaultdict
from _quant_common import (ROOT, DATA, load_full_text, load_char_names,
                           is_real_mention)

QUOTE_RE = re.compile(r"[“「]([^”」]{1,60})[”」]")
TRAIL_PUNCT = "。，！？…、；：”」』 ]　"
NON_HAN = re.compile(r"[^一-鿿〇０-９]")


def find_attr_name(text_before, names):
    """返回 text_before 中最后出现的（真实）角色名；无则 None。"""
    best_name, best_pos = None, -1
    for name in names:  # 已按长度降序
        start = 0
        while True:
            i = text_before.find(name, start)
            if i == -1:
                break
            if is_real_mention(name, text_before, i):
                if i > best_pos:
                    best_pos, best_name = i, name
            start = i + 1
    return best_name


def normalize(utt):
    s = NON_HAN.sub("", utt)
    return s


def build():
    chapters = load_full_text()
    names = load_char_names()
    utt_counter = defaultdict(lambda: defaultdict(int))      # (char, norm) -> freq
    utt_chapters = defaultdict(lambda: defaultdict(set))
    utt_context = defaultdict(lambda: defaultdict(list))     # 存样本上下文
    char_ngrams = defaultdict(lambda: defaultdict(int))      # char -> ngram -> freq
    char_ngram_ch = defaultdict(lambda: defaultdict(set))
    all_ngrams = defaultdict(int)                            # ngram -> 全局 freq（集中度分母）

    for ch in chapters:
        cidx = ch["idx"]
        prev_text = ""
        for p in ch["paragraphs"]:
            # 该段全部引号
            for m in QUOTE_RE.finditer(p):
                raw = m.group(1)
                before = prev_text + p[:m.start()]
                name = find_attr_name(before, names)
                if not name:
                    continue
                norm = normalize(raw)
                if len(norm) < 2:
                    continue
                utt_counter[name][norm] += 1
                utt_chapters[name][norm].add(cidx)
                if len(utt_context[name][norm]) < 2:
                    s = max(0, m.start() - 24); e = min(len(p), m.end() + 24)
                    utt_context[name][norm].append({"chapter": cidx, "context": p[s:e]})
                # n-gram（2–4 字）累积
                for n in (2, 3, 4):
                    for i in range(len(norm) - n + 1):
                        g = norm[i:i + n]
                        if re.search(r"[一-鿿]", g):  # 仅含汉字
                            char_ngrams[name][g] += 1
                            all_ngrams[g] += 1
                            char_ngram_ch[name][g].add(cidx)
            prev_text = p

    name_set = set(names)
    # 复现整句（freq>=2，排除角色自称名）
    recurring = []
    for name, d in utt_counter.items():
        for norm, freq in d.items():
            if freq >= 2 and norm not in name_set:
                chs = sorted(utt_chapters[name][norm])
                ctx = utt_context[name][norm][0] if utt_context[name][norm] else {"chapter": chs[0], "context": ""}
                recurring.append({
                    "phrase": norm, "character": name, "freq": freq,
                    "chapters": chs, "first_chapter": chs[0],
                    "sample_context": ctx["context"],
                })
    recurring.sort(key=lambda x: -x["freq"])

    # 标志 n-gram：freq>=5 且 ≥70% 归属于该角色（真正特征短语）
    sig = []
    for name, d in char_ngrams.items():
        for g, freq in d.items():
            total = all_ngrams[g]
            if freq >= 5 and freq / total >= 0.7 and g not in name_set:
                chs = sorted(char_ngram_ch[name][g])
                ctx = ""
                sig.append({"phrase": g, "character": name, "freq": freq,
                            "share": round(freq / total, 2),
                            "chapters": chs, "first_chapter": chs[0], "sample_context": ctx})
    sig.sort(key=lambda x: (-x["freq"], -x["share"]))

    by_char = defaultdict(list)
    for r in recurring:
        by_char[r["character"]].append(r["phrase"])
    for s in sig[:200]:
        if s["character"] not in by_char or len(by_char[s["character"]]) < 8:
            by_char[s["character"]].append(s["phrase"])

    result = {
        "recurring_utterances": recurring,
        "signature_ngrams": sig,
        "by_character": {k: v for k, v in by_char.items()},
        "stats": {"characters_with_catchphrase": len([k for k in by_char if by_char[k]]),
                  "recurring_count": len(recurring), "signature_ngram_count": len(sig)},
    }
    return result


if __name__ == "__main__":
    res = build()
    out = os.path.join(DATA, "catchphrases.json")
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written", out)
    print("stats:", res["stats"])
    print("--- top 8 recurring utterances ---")
    for r in res["recurring_utterances"][:8]:
        print(" ", r["character"], "×", r["freq"], "：", r["phrase"][:30])
