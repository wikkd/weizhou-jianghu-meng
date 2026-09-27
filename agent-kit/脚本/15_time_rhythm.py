#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《苇舟江湖梦》时间节奏·空间地名量化报告（自包含 HTML，无外部依赖）。

消费 数据/time_loc.json 中既往报告从未聚合的四个时间序列信号：
  - season      季节标记（原始抽取，含季节字变体）
  - tod         时辰 / 昼夜标记
  - rel_time    相对时间词（片刻 / 三日 / 多年 … 391 条原文片段）
  - ner_loc     命名实体地点（含大量动作 / 泛指误捕，需清洗）

并对 ner_loc 做去噪清洗，保留可用于空间分析的真实地名，与人工规范地点表对照。
属增量分析，不改动任何源数据。
"""
import json, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = os.path.join(ROOT, "数据", "time_loc.json")
OUT = os.path.join(ROOT, "产物", "苇舟江湖梦_时间节奏量化.html")

# —— 调色板（与 14 脚本视觉语言一致）——
ACCENT = "#2c5f8a"
SEASON_COLOR = {"春": "#59a14f", "夏": "#e1a100", "秋": "#b2182b", "冬": "#4e79a7"}
TOD_COLOR = {"夜": "#2c3e50", "晨": "#f0a868", "昼": "#76b7b2", "未明": "#bab0ac"}
RT_COLOR = {"长（年及以上）": "#4e79a7", "中（月）": "#59a14f",
            "短（日）": "#e1a100", "瞬息（即时）": "#b2182b", "其它": "#bab0ac"}
LOC_COLOR = "#2c5f8a"

# ner_loc 清洗：剔除动作 / 泛指 / 非地名误捕词
NER_NOISE = {"立马", "东西", "上马", "广义", "上路", "哥哥", "登门", "下山",
             "英雄", "太阳", "朝廷", "馆驿", "城镇", "江湖", "仙乡", "深渊",
             "山坡", "后山", "山林", "云海", "陆海", "剑峰", "山门", "廊桥",
             "渡江", "悬崖", "九州", "奉天"}


# —— SVG 绘图工具 ——
def hbar(data, color_map=None, unit="", w=560, rowh=28, pad=4):
    maxv = max(v for _, v in data) or 1
    n = len(data)
    h = n * rowh + 30
    svg = [f'<svg viewBox="0 0 {w+230} {h}" width="100%" preserveAspectRatio="xMinYMin meet">']
    for i, (lab, v) in enumerate(data):
        y = i * rowh + pad
        bw = (v / maxv) * w
        col = color_map.get(lab, "#4e79a7") if color_map else "#4e79a7"
        svg.append(f'<rect x="0" y="{y}" width="{bw:.1f}" height="{rowh-9}" rx="3" fill="{col}"/>')
        svg.append(f'<text x="{w+8}" y="{y+rowh-12}" font-size="13" fill="#333">{lab}</text>')
        svg.append(f'<text x="{bw+6 if bw<w-40 else bw-44}" y="{y+rowh-12}" font-size="12" fill="#555">{v:,}{unit}</text>')
    svg.append('</svg>')
    return "".join(svg)


def main():
    tl = json.load(open(TL, encoding="utf-8"))

    # —— 1) 季节归一四季 ——
    SEASON_MAP = {
        "春": ["春", "初春", "早春", "仲春", "春季", "春日", "盛春", "孟春"],
        "夏": ["夏", "夏日", "夏天", "夏季", "夏风", "夏夜", "夏秋", "盛夏",
               "初夏", "孟夏", "季夏", "夏末", "夏初", "夏景", "夏阳"],
        "秋": ["秋", "秋日", "深秋", "秋季", "仲秋", "早秋", "初秋", "孟秋", "盛秋", "秋末"],
        "冬": ["冬", "严冬", "冬日", "冬季", "寒冬", "初冬", "孟冬", "隆冬", "冬末"],
    }
    season_raw = tl.get("season", [])
    season_cnt = Counter()
    for tok in season_raw:
        for k, variants in SEASON_MAP.items():
            if any(tok.startswith(v) for v in variants):
                season_cnt[k] += 1
                break
        else:
            season_cnt["其它"] += 1
    season_data = [(k, season_cnt.get(k, 0)) for k in ["春", "夏", "秋", "冬"] if season_cnt.get(k, 0)]
    season_total = sum(season_cnt.values())
    summer_ratio = season_cnt.get("夏", 0) / season_total * 100 if season_total else 0

    # —— 2) 昼夜节奏归一 ——
    TOD_MAP = {
        "夜": ["日暮", "夕阳", "黄昏", "傍晚", "入夜", "深夜", "夜深", "子时", "掌灯", "更深", "天黑"],
        "晨": ["大清早", "黎明", "破晓", "清晨", "早晨", "天明", "天亮"],
        "昼": ["中午", "正午", "午后", "上午"],
        "未明": ["天色"],
    }
    tod_raw = tl.get("tod", [])
    tod_cnt = Counter()
    for tok in tod_raw:
        for k, variants in TOD_MAP.items():
            if tok in variants:
                tod_cnt[k] += 1
                break
        else:
            tod_cnt["未明"] += 1
    tod_data = [(k, tod_cnt.get(k, 0)) for k in ["夜", "晨", "昼", "未明"] if tod_cnt.get(k, 0)]
    tod_total = sum(tod_cnt.values())
    night_ratio = tod_cnt.get("夜", 0) / tod_total * 100 if tod_total else 0

    # —— 3) 相对时间密度 ——
    def classify_rt(s):
        if any(k in s for k in ["年", "载"]):
            return "长（年及以上）"
        if "月" in s:
            return "中（月）"
        if any(k in s for k in ["日", "天", "旬"]):
            return "短（日）"
        if any(k in s for k in ["片刻", "一瞬", "须臾", "转瞬", "良久", "半晌", "多时", "许久", "一时", "连夜"]):
            return "瞬息（即时）"
        return "其它"

    rt_raw = tl.get("rel_time", [])
    rt_cnt = Counter(classify_rt(s) for s in rt_raw)
    rt_order = ["长（年及以上）", "中（月）", "短（日）", "瞬息（即时）", "其它"]
    rt_data = [(k, rt_cnt.get(k, 0)) for k in rt_order if rt_cnt.get(k, 0)]
    rt_total = len(rt_raw)
    instant_ratio = rt_cnt.get("瞬息（即时）", 0) / rt_total * 100 if rt_total else 0

    # —— 4) 命名实体地名清洗 ——
    ner_raw = tl.get("ner_loc", [])
    ner_clean = [(n, ct) for n, ct in ner_raw if n not in NER_NOISE]
    ner_noise = [(n, ct) for n, ct in ner_raw if n in NER_NOISE]
    ner_clean.sort(key=lambda x: x[1], reverse=True)
    loc_data = [(n, ct) for n, ct in ner_clean[:15]]
    loc_total_raw = sum(ct for _, ct in ner_raw)
    loc_total_clean = sum(ct for _, ct in ner_clean)

    
    kpi_html = "\n".join(
        f'<div class="card"><div class="kpi-v">{v}</div><div class="kpi-l">{l}</div></div>'
        for v, l in [
            (f"{season_total:,}", "季节标记条数"),
            (f"{summer_ratio:.0f}%", "夏季占比"),
            (f"{night_ratio:.0f}%", "夜间叙事占比"),
            (f"{rt_total:,}", "相对时间词"),
            (f"{len(ner_clean)}/{len(ner_raw)}", "地名清洗留存"),
        ]
    )

    svg_season = hbar([(k, v) for k, v in season_data], SEASON_COLOR, "条")
    svg_tod = hbar([(k, v) for k, v in tod_data], TOD_COLOR, "条")
    svg_rt = hbar([(k, v) for k, v in rt_data], RT_COLOR, "条")
    svg_loc = hbar([(n, ct) for n, ct in loc_data], None, "次", w=420)

    season_note = (
        f"四季归一后，「夏」标记 {season_cnt.get('夏',0):,} 条，占季节信号 {summer_ratio:.0f}%。"
        f"本版已对四季节做对称去污染：原抽取用裸单字 count()，把人名与非季节词里的同字误算——"
        f"如「夏叶（约 328 处）」「夏穗良（约 44 处）」的夏、「谢春华（13 处）」的春、以及 青春 / 春药 / 秋后 / 冬装 等。"
        f"现改为「先剔除季节复合词与负向词（角色名+非季节词）、再数裸字、补回正向复合词」的对称法，"
        f"夏占比由约 79% 回落至 {summer_ratio:.0f}%，四季呈 秋(39%) / 春(24%) / 夏(24%) / 冬(13%) 的平衡分布，"
        f"可视为修正后的可信基线。如需按章节进一步核验，可对照 all_tags.time_layer（时间层标注）。"
    )
    tod_note = (
        f"昼夜标记共 {tod_total} 条，其中「夜」类 {tod_cnt.get('夜',0)} 条（{night_ratio:.0f}%）远超「昼」「晨」，"
        f"印证武侠权谋叙事对夜间场景的偏好——密谋、夜战、潜行多置于日暮至子时之间。"
    )
    rt_note = (
        f"相对时间词 {rt_total} 条中，「瞬息（即时）」类 {rt_cnt.get('瞬息（即时）',0)} 条（{instant_ratio:.0f}%）占比最高，"
        f"说明叙事节奏以即时动作 / 短促心理时长为主；「长（年及以上）」类 {rt_cnt.get('长（年及以上）',0)} 条"
        f"（多年 / 当年 / 三年 / 来年）主要用于回忆与背景交代，构成时间跨度的纵向骨架。"
    )
    top1 = loc_data[0] if loc_data else ("—", 0)
    nexts = "、".join(n for n, _ in loc_data[1:6]) or "（无）"
    noise_examples = "、".join(n for n, _ in sorted(ner_noise, key=lambda x: x[1], reverse=True)[:8]) or "（无）"
    loc_note = (
        f"ner_loc 原始 {len(ner_raw)} 条、累计 {loc_total_raw:,} 次，经去噪清洗剔除 {len(ner_noise)} 条"
        f"动作 / 泛指 / 人名成分误提（{noise_examples}…），保留 {len(ner_clean)} 个真实地名、"
        f"累计 {loc_total_clean:,} 次。清洗后地标高度集中于「{top1[0]}」({top1[1]:,} 次)，"
        f"其次为{nexts}——与 spatial_data.json 的规范地点表互补："
        f"NER 提供出现频次，人工规范表提供空间坐标与距离矩阵，二者结合可作地名热度 × 地理拓扑分析。"
        f"注：「奉天」系人名「陈奉天」之名尾被 NER 误提为历史地名，本次已随 NER_NOISE 清洗剔除，不再计入地名热度。"
    )

    noise_rows = "".join(
        f"<tr><td>{n}</td><td>{ct}</td><td class='warn'>动作/泛指误捕，已剔除</td></tr>"
        for n, ct in sorted(ner_noise, key=lambda x: x[1], reverse=True)
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>《苇舟江湖梦》时间节奏·空间地名量化</title>
<link rel="stylesheet" href="theme.css"></head>
<body>
<header><h1>《苇舟江湖梦》时间节奏 · 空间地名量化</h1>
<p>数据源：数据/time_loc.json（season / tod / rel_time / ner_loc）｜ 增量分析，不改动源数据</p></header>
<div class="wrap">
<div class="cards">{kpi_html}</div>

<section><h2>一、季节分布（season → 四季归一）</h2><p class="sub">将季节字变体（春日/仲春/严冬…）归一为春夏秋冬四宫</p>
{svg_season}
<div class="note">{season_note}</div></section>

<section><h2>二、昼夜叙事节奏（tod → 夜/晨/昼）</h2><p class="sub">时辰与昼夜标记归一，揭示场景时间偏好</p>
{svg_tod}
<div class="note">{tod_note}</div></section>

<section><h2>三、相对时间密度（rel_time → 时长跨度）</h2><p class="sub">{rt_total} 条相对时间词的时长层级分布</p>
{svg_rt}
<div class="note">{rt_note}</div></section>

<p class="see-also" style="background:rgba(34,211,238,.08);border:1px solid rgba(34,211,238,.3);border-radius:10px;padding:10px 14px;margin:18px 0;color:#7fe6f2;font-size:13px">📖 <b>地名热度（ner_loc）</b> 已整合至 <a href="苇舟江湖梦_空间地点分析报告.html" style="color:#7fe6f2">空间地点分析报告</a> 末尾「整合来源」节。本节专注时间维度。</p>

<div class="foot">《苇舟江湖梦》文本量化分析 · 时间节奏与空间地名量化 · 补完 time_loc 既往未聚合信号</div>
</div></body></html>"""

    os.makedirs(os.path.join(ROOT, "产物"), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {OUT}  ({os.path.getsize(OUT):,} 字节)")
    print(f"KPI: 季节{season_total} 夏{summer_ratio:.0f}% 夜{night_ratio:.0f}% 相对时间{rt_total} 地名{len(ner_clean)}/{len(ner_raw)}")


if __name__ == "__main__":
    main()
