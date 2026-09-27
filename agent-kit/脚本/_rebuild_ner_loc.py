#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建 time_loc.json 的 ner_loc 字段（剔除人名成分误提版）。

问题：NER 地名抽取把人名「陈奉天」中的「奉天」（现实中是沈阳旧称 / 历史地名）
误提为独立地名实体（freq 268）。而全文 276 处「奉天」里 275 处是「陈奉天」的一部分，
全书并不存在独立地名「奉天」。该误提会污染地名实体热度报告与归档消费。

修复：从 ner_loc 中剔除「人名成分误提」集合（初始 {"奉天"}），保留其余真实地名。

仅覆盖 time_loc.json 的 ner_loc 字段，保留 season / tod / rel_time。覆盖前自动备份。
"""
import json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = os.path.join(ROOT, "数据", "time_loc.json")
BAK = TL + ".bak"

# 人名成分误提集合（在此扩展）：name 是某规范人名的子串、本身并非独立地名
NAME_FRAGMENT_NOISE = {"奉天"}


def main():
    tl = json.load(open(TL, encoding="utf-8"))
    ner_raw = tl.get("ner_loc", [])
    kept, removed = [], []
    for entry in ner_raw:
        name = entry[0] if isinstance(entry, list) and entry else None
        if name in NAME_FRAGMENT_NOISE:
            removed.append(entry)
        else:
            kept.append(entry)
    tl["ner_loc"] = kept

    # 覆盖前自动备份当前线上版本
    shutil.copy2(TL, BAK)

    with open(TL, "w", encoding="utf-8") as f:
        json.dump(tl, f, ensure_ascii=False, indent=2)

    print(f"ner_loc 原始 {len(ner_raw)} 条 -> 保留 {len(kept)} 条")
    print(f"剔除 {len(removed)} 条人名成分误提: {removed}")


if __name__ == "__main__":
    main()
