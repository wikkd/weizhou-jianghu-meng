#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建 time_loc.json 的 season 字段（对称去污染版）。

问题：季节标记若用裸单字 count()，会把人名/非季节词里的同字误算：
  - 夏 ← 夏叶(328) / 夏穗良(44) 等人名
  - 春 ← 谢春华(13，角色名) + 青春/春药/春色 等非季节词
  - 秋 ← 秋后/秋雨/春秋 等；冬 ← 冬装/过冬 等

修复（四季节对称）：对每个季节字 ch，
  1) 从正文同时剔除「正向季节复合词」与「负向词（角色名+非季节词）」；
  2) 统计剩余裸字 ch（真正的单字季节标记）；
  3) 再把正向复合词按出现次数补回。
这样：角色名/非季节词完全排除，正向复合词只计一次，裸字也只计一次（无双重计数）。

仅覆盖 time_loc.json 的 season 字段，保留 tod / rel_time / ner_loc。覆盖前自动备份。
"""
import json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "数据", "full_text.txt")
TL = os.path.join(ROOT, "数据", "time_loc.json")

# 四季节：正向复合词（真实季节义） + 负向词（角色名 / 非季节义）
SEASON = {
    "春": {
        "pos": ["春日", "仲春", "早春", "初春", "孟春", "春季", "盛春"],
        "neg": ["春华", "青春", "春药", "春色", "春宫", "春梦", "春情", "春心",
                "春意", "春画", "春宵", "春笋", "怀春", "妙手回春", "春游",
                "春装", "春寒", "春雷", "春潮", "阳春", "春暖", "春华秋实"],
    },
    "夏": {
        "pos": ["夏日", "夏天", "夏季", "夏风", "夏夜", "夏秋", "盛夏",
                "初夏", "孟夏", "季夏", "夏末", "夏初", "夏景", "夏阳"],
        "neg": ["夏叶", "夏穗良"],
    },
    "秋": {
        "pos": ["秋日", "仲秋", "早秋", "初秋", "孟秋", "秋季", "深秋", "盛秋", "秋末"],
        "neg": ["秋后", "秋雨", "秋霜", "秋凉", "秋千", "秋波", "秋水", "秋毫",
                "秋老虎", "秋膘", "春秋", "多事之秋", "暗送秋波", "秋实", "秋景气"],
    },
    "冬": {
        "pos": ["冬日", "严冬", "初冬", "孟冬", "冬季", "寒冬", "隆冬", "冬末"],
        "neg": ["冬装", "冬泳", "过冬", "冬眠", "冬笋", "冬菇", "冬枣", "冬麦"],
    },
}


def strip(text, words):
    t = text
    for w in words:
        if w in t:
            t = t.replace(w, "　" * len(w))
    return t


def season_tokens(ch, pos, neg, text):
    clean = strip(text, pos + neg)          # 剔除正向复合词 + 负向词
    bare = clean.count(ch)                   # 剩余裸字 = 真季节单字
    toks = [ch] * bare
    for v in pos:
        toks.extend([v] * text.count(v))     # 正向复合词按实出现补回
    return toks


def main():
    ft = open(SRC, encoding="utf-8").read()
    tl = json.load(open(TL, encoding="utf-8"))
    old = tl.get("season", [])

    tokens = []
    report = []
    for ch, cfg in SEASON.items():
        tk = season_tokens(ch, cfg["pos"], cfg["neg"], ft)
        tokens.extend(tk)
        # 负向词实际命中（用于报告）
        neg_hit = {w: ft.count(w) for w in cfg["neg"] if ft.count(w) > 0}
        report.append((ch, tk.count(ch), sum(neg_hit.values()), neg_hit))

    tl["season"] = tokens
    bak = TL + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(TL, bak)
    with open(TL, "w", encoding="utf-8") as f:
        json.dump(tl, f, ensure_ascii=False, indent=2)

    print(f"season 标记数: {len(old)} -> {len(tokens)}")
    for ch, n_ch, neg_n, neg_hit in report:
        print(f"  {ch}: 净标记 {n_ch}  剔除负向词 {neg_n} 处 {neg_hit if neg_hit else ''}")
    print(f"备份: {bak}")


if __name__ == "__main__":
    main()
