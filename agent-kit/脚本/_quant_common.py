# -*- coding: utf-8 -*-
"""量化扩展公共模块：全文分章、实体名表、语境窗口工具。
被 17_character_traits / 18_catchphrases / 19_combat_actions / 20_geo_descriptions 复用。
所有路径以本文件所在目录（脚本/）的父目录为项目根。
"""
import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "数据")

CH_MARK = re.compile(r"^[一二三四五六七八九十百零〇\d]+[、．.]\s*$")


def _proj(*p):
    return os.path.join(ROOT, *p)


def load_full_text():
    """返回 chapters: [{idx(1-based), title, paragraphs:[str]}]；按独立章标记行切分。"""
    path = os.path.join(DATA, "full_text.txt")
    raw = open(path, encoding="utf-8").read().split("\n")
    chapters = []
    cur = None
    for line in raw:
        if CH_MARK.match(line.strip()):
            if cur is not None:
                chapters.append(cur)
            cur = {"idx": len(chapters) + 1, "title": line.strip(), "paragraphs": []}
        else:
            if cur is not None:
                s = line.strip()
                if s:
                    cur["paragraphs"].append(s)
    if cur is not None:
        chapters.append(cur)
    return chapters


def load_char_names():
    cs = json.load(open(os.path.join(DATA, "char_stats.json"), encoding="utf-8"))
    names = [c["name"] for c in cs]
    # 长名优先，避免「空」匹配进「空间」等长串；单字名排最后
    return sorted(names, key=lambda n: (-len(n), n))


def load_loc_names():
    sp = json.load(open(os.path.join(DATA, "spatial_data.json"), encoding="utf-8"))
    names = list(sp.get("nodes", {}).keys())
    return sorted(names, key=lambda n: (-len(n), n))


def load_all_tags():
    return json.load(open(os.path.join(DATA, "chapter_data", "all_tags.json"), encoding="utf-8"))


def char_paragraphs(chapters, name):
    """yield (chapter_idx, paragraph) 所有含该角色名的段落（段落级语境窗口）。"""
    for ch in chapters:
        for p in ch["paragraphs"]:
            if name in p:
                yield ch["idx"], p


def char_chapter_set(chapters, name):
    return sorted({ci for ci, _ in char_paragraphs(chapters, name)})


# —— 单字名否定清单（沿用 _rebuild_char_mentions 机制，防止光影/天空等泛指污染）——
NEG_BOUNDARY = {
    "影": ["身影", "背影", "人影", "阴影", "影子", "暗影", "疏影", "倒影", "影影绰绰", "魅影"],
    "空": ["天空", "虚空", "空旷", "空荡", "腾空", "凌空", "半空", "长空", "晴空", "空中", "空寂", "空山"],
    "福": ["福气", "福分", "洪福", "造福", "享福", "福泽", "眼福"],
}


def is_real_mention(name, text, pos):
    """name 在 text 的 pos 处是否真实提及（排除单字名泛指复合词）。"""
    if name not in NEG_BOUNDARY:
        return True
    neg = NEG_BOUNDARY[name]
    for w in neg:
        i = text.find(w)
        while i != -1:
            if i <= pos <= i + len(w) - 1:
                return False
            i = text.find(w, i + 1)
    return True


def count_real(text, name):
    """单字名安全计数（仅「影/空/福」启用否定；其余直接 count）。"""
    if name not in NEG_BOUNDARY:
        return text.count(name)
    total = 0
    start = 0
    while True:
        i = text.find(name, start)
        if i == -1:
            break
        if is_real_mention(name, text, i):
            total += 1
        start = i + 1
    return total


if __name__ == "__main__":
    ch = load_full_text()
    print("chapters:", len(ch), "names:", len(load_char_names()), "locs:", len(load_loc_names()))
