#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""聚合 6 个批次标签为统一 all_tags.json，并做一致性校验。"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "数据", "chapter_data")
BATCHES = [f"tags_batch{i}.json" for i in range(1, 7)]

# —— 受控词表（与 tag_schema.md 保持一致）——
TIME_LAYERS = {"序章/前史","初入江湖","江湖历练","庙堂初涉","乱世将起",
               "战乱爆发","大战/决战","战后格局","未明/过渡"}
CHAPTER_TYPES = {"战斗/武斗","日常/生活","谋略/权谋","情感/感情","过渡/行进",
                 "揭示/设定","会议/议事","悲剧/伤亡","喜剧/轻松","结局/收束"}
STORY_ARCS = {"主线·任琅成长","主线·任琅尚樱感情","主线·川阴王叛乱/战争",
              "支线·江湖门派","支线·宫廷权谋","支线·配角故事","多线交织","未明"}
EMOTION_LINES = {"升温/进展","波折/误会","分离/离别","平淡/日常",
                 "无显著感情戏","虐/悲情"}
POVS = {"任琅限知","尚樱限知","第三人称全知","多视角切换"}
LOC_CANON = {"京城","卫京郡","南岭关","京墨渡口","川阴城","梨花川","梨阳","望岳镇",
             "苏城","楚城","海郡","奉秋","石陵","夫文渡口","响城","海都","暮山城",
             "浣冰郡","镜湖"}

def main():
    all_objs = []
    for b in BATCHES:
        p = os.path.join(BASE, b)
        if not os.path.exists(p):
            print(f"[WARN] 缺失批次文件: {b}")
            continue
        data = json.load(open(p, encoding="utf-8"))
        all_objs.extend(data)

    # 校验章节完整性
    chs = [o.get("chapter") for o in all_objs]
    missing = set(range(1, 60)) - set(chs)
    dup = [c for c in set(chs) if chs.count(c) > 1]
    print(f"总对象数: {len(all_objs)}  章节集合大小: {len(set(chs))}")
    if missing:
        print(f"[ERROR] 缺失章节: {sorted(missing)}")
    if dup:
        print(f"[ERROR] 重复章节: {sorted(dup)}")

    # 排序
    all_objs.sort(key=lambda o: o.get("chapter", 0))

    errors = []
    for o in all_objs:
        ch = o.get("chapter")
        # 必填字段
        for fld in ["chapter","file","word_count","time_layer","main_locations",
                    "characters_present","chapter_type","story_arc","emotion_line",
                    "combat_intensity","narrative_pov","key_events","tags_free"]:
            if fld not in o:
                errors.append(f"ch{ch}: 缺字段 {fld}")
        # 枚举校验
        if o.get("time_layer") not in TIME_LAYERS:
            errors.append(f"ch{ch}: time_layer 越界 {o.get('time_layer')}")
        if o.get("story_arc") not in STORY_ARCS:
            errors.append(f"ch{ch}: story_arc 越界 {o.get('story_arc')}")
        if o.get("emotion_line") not in EMOTION_LINES:
            errors.append(f"ch{ch}: emotion_line 越界 {o.get('emotion_line')}")
        if o.get("narrative_pov") not in POVS:
            errors.append(f"ch{ch}: narrative_pov 越界 {o.get('narrative_pov')}")
        for ct in (o.get("chapter_type") or []):
            if ct not in CHAPTER_TYPES:
                errors.append(f"ch{ch}: chapter_type 越界 {ct}")
        ci = o.get("combat_intensity")
        if not (isinstance(ci, int) and 0 <= ci <= 3):
            errors.append(f"ch{ch}: combat_intensity 非法 {ci}")
        # 归一校验：不应残留 川阴王 作为人物
        for c in (o.get("characters_present") or []):
            if c in ("川阴王","王爷","反王"):
                errors.append(f"ch{ch}: 人物未归一 {c}（应→陈奉天）")
        # main_locations 数量
        if len(o.get("main_locations") or []) > 3:
            errors.append(f"ch{ch}: main_locations >3")

    out = os.path.join(BASE, "all_tags.json")
    json.dump(all_objs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"已写出 {out}")

    if errors:
        print(f"\n[校验问题 {len(errors)} 项]")
        for e in errors[:50]:
            print("  -", e)
        if len(errors) > 50:
            print(f"  ... 其余 {len(errors)-50} 项省略")
    else:
        print("\n[校验通过] 全部 59 章字段合规、枚举合法、人物已归一。")

if __name__ == "__main__":
    main()
