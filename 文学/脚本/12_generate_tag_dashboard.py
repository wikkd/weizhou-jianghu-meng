#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基于 chapter_data/all_tags.json 生成《苇舟江湖梦》章节标签量化看板 HTML（自包含，无外部依赖）。"""
import json, os
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "数据", "chapter_data")
OUT = os.path.join(ROOT, "产物", "苇舟江湖梦_章节标签量化看板.html")

# —— 调色板 ——
TL_ORDER = ["序章/前史","初入江湖","江湖历练","庙堂初涉","乱世将起",
            "战乱爆发","大战/决战","战后格局","未明/过渡"]
TL_COLOR = {
    "序章/前史":"#9e9e9e","初入江湖":"#4e79a7","江湖历练":"#59a14f","庙堂初涉":"#b07aa1",
    "乱世将起":"#e15759","战乱爆发":"#f28e2b","大战/决战":"#b2182b","战后格局":"#76b7b2",
    "未明/过渡":"#bab0ac",
}
CT_ORDER = ["战斗/武斗","谋略/权谋","情感/感情","日常/生活","揭示/设定",
            "悲剧/伤亡","过渡/行进","喜剧/轻松","会议/议事","结局/收束"]
CT_COLOR = {
    "战斗/武斗":"#e15759","谋略/权谋":"#4e79a7","情感/感情":"#e377c2","日常/生活":"#59a14f",
    "揭示/设定":"#9c755f","悲剧/伤亡":"#b2182b","过渡/行进":"#bab0ac","喜剧/轻松":"#f1c40f",
    "会议/议事":"#76b7b2","结局/收束":"#8c564b",
}
EMO_ORDER = ["平淡/日常","升温/进展","无显著感情戏","虐/悲情","波折/误会","分离/离别"]
EMO_COLOR = {
    "平淡/日常":"#4e79a7","升温/进展":"#59a14f","无显著感情戏":"#bab0ac","虐/悲情":"#b2182b",
    "波折/误会":"#f28e2b","分离/离别":"#9e9e9e",
}

def hbar(data, color_map=None, unit="章", w=520, rowh=26, pad=4):
    """水平条形图。data: [(label, value)]"""
    maxv = max(v for _, v in data) or 1
    n = len(data)
    h = n * rowh + 30
    svg = [f'<svg viewBox="0 0 {w+200} {h}" width="100%" preserveAspectRatio="xMinYMin meet">']
    # 计算标签最大宽度
    for i, (lab, v) in enumerate(data):
        y = i * rowh + pad
        bw = (v / maxv) * w
        col = color_map.get(lab, "#4e79a7") if color_map else "#4e79a7"
        svg.append(f'<rect x="0" y="{y}" width="{bw:.1f}" height="{rowh-8}" rx="3" fill="{col}"/>')
        svg.append(f'<text x="{w+8}" y="{y+rowh-12}" font-size="13" fill="#333">{lab}</text>')
        svg.append(f'<text x="{bw+6 if bw<w-30 else bw-30}" y="{y+rowh-12}" font-size="12" fill="#555">{v}{unit}</text>')
    svg.append('</svg>')
    return "".join(svg)

def vbar(data, color="#4e79a7", w=640, h=300, unit="", top=20):
    """垂直条形图。data: [(label, value)]"""
    maxv = max(v for _, v in data) or 1
    n = len(data)
    gap = 6
    bw = (w - gap * (n + 1)) / n
    svg = [f'<svg viewBox="0 0 {w} {h+40}" width="100%" preserveAspectRatio="xMinYMin meet">']
    # y 轴基线
    base = h
    for i, (lab, v) in enumerate(data[:top]):
        x = gap + i * (bw + gap)
        bh = (v / maxv) * (h - 20)
        svg.append(f'<rect x="{x:.1f}" y="{base-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2" fill="{color}"/>')
        svg.append(f'<text x="{x+bw/2:.1f}" y="{base-bh-4:.1f}" font-size="11" fill="#555" text-anchor="middle">{v}</text>')
        # x 标签（竖排或截断）
        ll = lab if len(lab) <= 5 else lab[:5]
        svg.append(f'<text x="{x+bw/2:.1f}" y="{base+14:.1f}" font-size="11" fill="#333" text-anchor="middle">{ll}</text>')
    svg.append(f'<line x1="0" y1="{base}" x2="{w}" y2="{base}" stroke="#ccc"/>')
    svg.append('</svg>')
    return "".join(svg)

def line_chart(ys, w=900, h=220, ymax=3, color="#e15759", ylabel="战斗强度"):
    """折线图，x 为 1..len(ys)。"""
    n = len(ys)
    padl, padr, padt, padb = 40, 20, 20, 28
    iw = w - padl - padr
    ih = h - padt - padb
    def X(i): return padl + (i / (n - 1)) * iw
    def Y(v): return padt + (1 - v / ymax) * ih
    svg = [f'<svg viewBox="0 0 {w} {h}" width="100%" preserveAspectRatio="xMinYMin meet">']
    # 网格 + y 刻度
    for g in range(ymax + 1):
        yy = Y(g)
        svg.append(f'<line x1="{padl}" y1="{yy:.1f}" x2="{w-padr}" y2="{yy:.1f}" stroke="#eee"/>')
        svg.append(f'<text x="{padl-6}" y="{yy+4:.1f}" font-size="11" fill="#888" text-anchor="end">{g}</text>')
    pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(ys))
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>')
    for i, v in enumerate(ys):
        svg.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="2.5" fill="{color}"/>')
    # x 刻度（每 10 章）
    for i in range(0, n, 10):
        svg.append(f'<text x="{X(i):.1f}" y="{h-8}" font-size="10" fill="#888" text-anchor="middle">{i+1}</text>')
    svg.append(f'<text x="10" y="{padt-6}" font-size="11" fill="#666">{ylabel}</text>')
    svg.append('</svg>')
    return "".join(svg)

def strip_chart(tls, color_map, w=900, h=70):
    """每章一个色块，按 time_layer 着色。"""
    n = len(tls)
    padl = 40
    iw = w - padl - 20
    bw = iw / n
    svg = [f'<svg viewBox="0 0 {w} {h}" width="100%" preserveAspectRatio="xMinYMin meet">']
    for i, tl in enumerate(tls):
        x = padl + i * bw
        col = color_map.get(tl, "#ddd")
        svg.append(f'<rect x="{x:.1f}" y="14" width="{bw+0.5:.1f}" height="34" fill="{col}"><title>第{i+1}章：{tl}</title></rect>')
    for i in range(0, n, 10):
        svg.append(f'<text x="{padl+i*bw:.1f}" y="64" font-size="10" fill="#888" text-anchor="middle">{i+1}</text>')
    svg.append('</svg>')
    return "".join(svg)

def main():
    tags = json.load(open(os.path.join(BASE, "all_tags.json"), encoding="utf-8"))
    idx = {x["chapter"]: x for x in json.load(open(os.path.join(BASE, "chapters_index.json"), encoding="utf-8"))}
    tags.sort(key=lambda o: o["chapter"])
    N = len(tags)

    # 聚合
    ct = Counter(); emo = Counter(); tl = Counter(); loc = Counter(); char = Counter(); ci = Counter()
    for o in tags:
        for t in o["chapter_type"]: ct[t] += 1
        emo[o["emotion_line"]] += 1
        tl[o["time_layer"]] += 1
        for l in o["main_locations"]: loc[l] += 1
        for c in o["characters_present"]: char[c] += 1
        ci[o["combat_intensity"]] += 1

    total_chars = sum(idx[c]["chars"] for c in idx)
    combat_chapters = ct["战斗/武斗"]
    kpi = [
        ("总章节", f"{N} 章"),
        ("总字数", f"{total_chars:,} 字"),
        ("战斗章占比", f"{combat_chapters}/{N} ({combat_chapters*100//N}%)"),
        ("标注人物", f"{len(char)} 种"),
        ("标注地点", f"{len(loc)} 种"),
        ("高强度战斗(3级)", f"{ci[3]} 章"),
    ]

    tl_by_chapter = [o["time_layer"] for o in tags]
    ci_by_chapter = [o["combat_intensity"] for o in tags]

    ct_data = [(k, ct.get(k, 0)) for k in CT_ORDER if ct.get(k, 0) > 0]
    emo_data = [(k, emo.get(k, 0)) for k in EMO_ORDER if emo.get(k, 0) > 0]
    tl_data = [(k, tl.get(k, 0)) for k in TL_ORDER if tl.get(k, 0) > 0]
    loc_data = loc.most_common(15)
    char_data = char.most_common(20)
    ci_data = [(str(k), ci.get(k, 0)) for k in [0, 1, 2, 3]]

    # 图例（时间层）
    tl_legend = "".join(
        f'<span class="lg"><i style="background:{TL_COLOR[k]}"></i>{k}</span>'
        for k in TL_ORDER if tl.get(k, 0) > 0
    )

    svg_ct = hbar(ct_data, CT_COLOR, "章")
    svg_emo = hbar(emo_data, EMO_COLOR, "章")
    svg_tl = hbar(tl_data, TL_COLOR, "章")
    svg_loc = vbar(loc_data, "#59a14f", top=15)
    svg_char = vbar(char_data, "#4e79a7", top=20)
    svg_ci = vbar(ci_data, "#e15759", top=4)
    svg_strip = strip_chart(tl_by_chapter, TL_COLOR)
    svg_line = line_chart(ci_by_chapter, ymax=3)

    kpi_html = "".join(
        f'<div class="card"><div class="kpi-v">{v}</div><div class="kpi-l">{l}</div></div>'
        for l, v in kpi
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>《苇舟江湖梦》章节标签量化看板</title>
<link rel="stylesheet" href="theme.css"></head>
<body>
<header><h1>《苇舟江湖梦》章节标签量化看板</h1>
<p>数据源：chapter_data/all_tags.json（62 章受控词表标注，subagent 并行标注 + 聚合校验）｜ 生成自全文本分章结构化标签</p></header>
<div class="wrap">
<div class="cards">{kpi_html}</div>

<section><h2>一、章节类型分布</h2><p class="sub">多标签统计：单章可同时标注多个类型（如"战斗+谋略"）</p>
<div class="grid2"><div>{svg_ct}</div><div>{svg_tl}</div></div></section>

<section><h2>二、情节演进：时间层色带 + 战斗强度走势</h2>
<p class="sub">上：每章按时间层着色（见下方图例）；下：战斗强度（0–3）随章节折线</p>
<div class="legend">{tl_legend}</div>
{svg_strip}
<div style="margin-top:8px">{svg_line}</div></section>

<section><h2>三、感情线分布</h2><p class="sub">单标签：每章情感基调归类</p>
{svg_emo}</section>

<section><h2>四、地点热度 Top15</h2><p class="sub">按出现为"主地点"的章节数计（含扩展地名）</p>
{svg_loc}</section>

<section><h2>五、人物出场热度 Top20</h2><p class="sub">按被列为"出场人物"的章节数计（川阴王已归一为陈奉天；含扩展人物）</p>
{svg_char}</section>

<section><h2>六、战斗强度分布</h2><p class="sub">0 无 / 1 低 / 2 中 / 3 高（决战级）</p>
{svg_ci}</section>

<div class="foot">《苇舟江湖梦》文本量化分析 · 章节标签看板 · 受控词表驱动，可对接共现网络与地理热力图</div>
</div></body></html>"""

    os.makedirs(os.path.join(ROOT, "产物"), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {OUT}  ({os.path.getsize(OUT):,} 字节)")
    print(f"KPI: 章节{N} 字数{total_chars:,} 战斗章{combat_chapters} 人物{len(char)} 地点{len(loc)} 高强战斗{ci[3]}")

if __name__ == "__main__":
    main()
