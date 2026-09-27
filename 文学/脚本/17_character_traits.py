# -*- coding: utf-8 -*-
"""D1 角色性格特征量化：6 轴受控词表扫描各角色语境段落，落主导极 + 可人审证据。
产出 数据/char_traits.json（name -> 性格档案）。自动词表抽取，精度靠 Phase 3 抽样兜底。
"""
import os, json
from _quant_common import (ROOT, DATA, load_full_text, load_char_names,
                           char_paragraphs)

# 6 轴 × 两极其受控词表（2 字为主，降假阳）
TRAIT_AXES = {
    "性情": {"沉稳": ["沉稳", "从容", "镇定", "淡然", "冷静", "沉静", "安然", "稳重", "处变不惊", "不惊"],
            "急躁": ["急躁", "焦躁", "暴躁", "浮躁", "火冒", "性急", "急切", "按捺不住"]},
    "品性": {"仁厚": ["仁厚", "悲悯", "侠义", "宽厚", "仁慈", "善良", "慈悲", "仗义", "心善"],
            "狠辣": ["狠辣", "阴毒", "残忍", "冷酷", "刻薄", "毒辣", "暴虐", "无情", "阴狠"]},
    "心气": {"谦和": ["谦和", "谦逊", "低调", "内敛", "温润", "谦卑", "不骄"],
            "孤傲": ["孤傲", "睥睨", "清高", "张扬", "狂妄", "倨傲", "傲然", "恃才", "目空一切"]},
    "情义": {"重情": ["重情", "义气", "护短", "忠勇", "舍身", "情义", "赴义", "肝胆相照"],
            "凉薄": ["薄情", "背叛", "翻脸", "冷血", "背信", "负义", "弃义", "绝情"]},
    "智愚": {"机变": ["机变", "机敏", "通透", "沉吟", "审时", "谋略", "睿智", "算无遗策", "审时度势"],
            "鲁莽": ["鲁莽", "莽撞", "执拗", "昏聩", "不计后果", "冒进", "躁进", "横冲直撞"]},
    "胆气": {"无畏": ["无畏", "悍然", "赴死", "凛然", "胆气", "英勇", "慨然", "不退", "视死如归"],
            "怯懦": ["畏缩", "惊惧", "怯懦", "颤栗", "退缩", "胆寒", "惶恐", "瑟缩"]},
}


def evidence(paras_with_ch, words, limit=3):
    out = []
    seen = set()
    for ci, p in paras_with_ch:
        for w in words:
            if w in p:
                # 截取含该词的片段
                i = p.find(w)
                s = max(0, i - 18); e = min(len(p), i + len(w) + 18)
                snip = p[s:e]
                key = (ci, snip)
                if key not in seen:
                    seen.add(key)
                    out.append({"chapter": ci, "word": w, "snippet": snip})
                break
        if len(out) >= limit:
            break
    return out


def build():
    chapters = load_full_text()
    names = load_char_names()
    result = {}
    for name in names:
        paras = list(char_paragraphs(chapters, name))
        axes_out = {}
        signals = []
        margins = []
        for axis, poles in TRAIT_AXES.items():
            pole_keys = list(poles.keys())
            pa_words, pb_words = poles[pole_keys[0]], poles[pole_keys[1]]
            a = sum(p.count(w) for _, p in paras for w in pa_words)
            b = sum(p.count(w) for _, p in paras for w in pb_words)
            if a == 0 and b == 0:
                axes_out[axis] = None
                continue
            win_pole = list(poles.keys())[0] if a >= b else list(poles.keys())[1]
            win_words = pa_words if a >= b else pb_words
            axes_out[axis] = win_pole
            margins.append((axis, abs(a - b), win_pole))
            signals.append({
                "axis": axis, "pole": win_pole,
                "score_a": a, "score_b": b,
                "evidence": evidence(paras, win_words, 3),
            })
        margins.sort(key=lambda x: -x[1])
        dominant = [m[2] for m in margins[:3] if m[1] > 0]
        result[name] = {
            "name": name,
            "paragraphs": len(paras),
            "chapters_present": sorted({ci for ci, _ in paras}),
            "trait_axes": axes_out,
            "dominant_traits": dominant,
            "signals": signals,
            "confidence": round(len([m for m in margins if m[1] > 0]) / len(TRAIT_AXES), 2),
        }
    return result


if __name__ == "__main__":
    res = build()
    out = os.path.join(DATA, "char_traits.json")
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 简要统计
    n_sig = sum(1 for v in res.values() if v["dominant_traits"])
    print("written", out, len(res), "characters; with>=1 dominant trait:", n_sig)
