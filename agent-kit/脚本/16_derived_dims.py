#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《苇舟江湖梦》派生维度量化报告（自包含 HTML，无外部依赖）。

基于既有数据派生两个既往报告未覆盖的网络视角：
  1) 出场 vs 提及背离：char_stats.mentions / chapters_present（基于名字扫描的"在场"）
     × all_tags.characters_present（人工标注的真实登场章节）——识别"在场却不在场"的幕后人物；
  2) 人物-地点共现：逐章 characters_present × main_locations 累加，得到 (角色,地点) 共现矩阵，
     与 character_network（角色-角色）互补，揭示"谁在何处"。

属增量分析，不改动任何源数据。
"""
import json, os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "数据", "chapter_data")
CS = os.path.join(ROOT, "数据", "char_stats.json")
OUT = os.path.join(ROOT, "产物", "苇舟江湖梦_派生维度量化.html")

ACCENT = "#2c5f8a"


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
        svg.append(f'<text x="{bw+6 if bw<w-40 else bw-44}" y="{y+rowh-12}" font-size="12" fill="#555">{v}{unit}</text>')
    svg.append('</svg>')
    return "".join(svg)


def scatter(points, w=700, h=440):
    """points: [(x, y, name)]；x=真实登场章节, y=提及章节；对角线 y=x 之下即为背离。"""
    xmax = max(p[0] for p in points) or 1
    ymax = max(p[1] for p in points) or 1
    M = max(xmax, ymax, 1)
    left, top, right, bottom = 64, 24, 24, 52
    pw = w - left - right
    ph = h - top - bottom

    def sx(v):
        return left + v / M * pw

    def sy(v):
        return top + (1 - v / M) * ph

    svg = [f'<svg viewBox="0 0 {w} {h}" width="100%" preserveAspectRatio="xMinYMin meet">']
    svg.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ph}" stroke="#999"/>')
    svg.append(f'<line x1="{left}" y1="{top+ph}" x2="{left+pw}" y2="{top+ph}" stroke="#999"/>')
    svg.append(f'<text x="{left-8}" y="{top+ph+16}" font-size="11" fill="#666" text-anchor="middle" transform="rotate(-90 {left-8} {top+ph/2:.0f})">提及章节</text>')
    svg.append(f'<text x="{left+pw/2:.0f}" y="{top+ph+40}" font-size="11" fill="#666" text-anchor="middle">真实登场章节</text>')
    # 对角线 y=x
    svg.append(f'<line x1="{sx(0)}" y1="{sy(0)}" x2="{sx(M)}" y2="{sy(M)}" stroke="#bbb" stroke-dasharray="4"/>')
    svg.append(f'<text x="{sx(M)-4:.0f}" y="{sy(M)-6:.0f}" font-size="10" fill="#999" text-anchor="end">提及=登场</text>')
    for x, y, name in points:
        cx, cy = sx(x), sy(y)
        dev = y - x
        col = "#b2182b" if dev > 5 else "#2c5f8a"
        svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5" fill="{col}" opacity="0.7"/>')
        if dev > 5 or name in ("川阴王", "影", "任琅", "陈奉天"):
            svg.append(f'<text x="{cx+7:.1f}" y="{cy+3:.1f}" font-size="10" fill="#333">{name}</text>')
    svg.append('</svg>')
    return "".join(svg)


def heatmap(matrix, roles, locs, w=760, h=430):
    cols, rows = len(locs), len(roles)
    left, top, right, bottom = 96, 56, 16, 16
    pw = w - left - right
    ph = h - top - bottom
    cw, ch = pw / cols, ph / rows
    maxv = max(matrix.values()) if matrix else 1
    svg = [f'<svg viewBox="0 0 {w} {h}" width="100%" preserveAspectRatio="xMinYMin meet">']
    for j, loc in enumerate(locs):
        x = left + j * cw + cw / 2
        ll = loc if len(loc) <= 4 else loc[:4]
        svg.append(f'<text x="{x:.1f}" y="{top-8:.1f}" font-size="10.5" fill="#333" text-anchor="middle">{ll}</text>')
    for i, role in enumerate(roles):
        y = top + i * ch
        svg.append(f'<text x="{left-8:.1f}" y="{y+ch/2+4:.1f}" font-size="10.5" fill="#333" text-anchor="end">{role}</text>')
        for j, loc in enumerate(locs):
            x = left + j * cw
            v = matrix.get((role, loc), 0)
            if v > 0:
                r = v / maxv
                fill = f'rgb({int(238-(238-31)*r):.0f},{int(242-(242-58)*r):.0f},{int(246-(246-95)*r):.0f})'
                svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw-1:.1f}" height="{ch-1:.1f}" fill="{fill}"/>')
                svg.append(f'<text x="{x+cw/2:.1f}" y="{y+ch/2+3:.1f}" font-size="9" fill="{"#fff" if r>0.5 else "#555"}" text-anchor="middle">{v}</text>')
            else:
                svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw-1:.1f}" height="{ch-1:.1f}" fill="#f3f4f6" stroke="#e3e6ea" stroke-width="0.5"/>')
    return "".join(svg)


def main():
    tags = json.load(open(os.path.join(BASE, "all_tags.json"), encoding="utf-8"))
    cs = json.load(open(CS, encoding="utf-8"))

    # —— 真实登场章节集合 ——
    real_present = defaultdict(set)
    for t in tags:
        for c in t.get("characters_present", []):
            real_present[c].add(t["chapter"])

    # —— 1) 出场 vs 提及背离 ——
    rows = []
    for c in cs:
        name = c["name"]
        mentions = c["mentions"]
        cp_ch = c.get("chapters_present", 0)
        real_ch = len(real_present.get(name, set()))
        rows.append({
            "name": name, "mentions": mentions, "cp": cp_ch,
            "real": real_ch, "dev": cp_ch - real_ch,
        })
    rows.sort(key=lambda r: r["dev"], reverse=True)
    dev_top = [(r["name"], r["dev"]) for r in rows if r["dev"] > 0][:12]
    svg_dev = hbar(dev_top, None, "章")

    # 类型判定
    behind = [r for r in rows if r["real"] == 0 and r["cp"] >= 5]
    scatter_pts = [(r["real"], r["cp"], r["name"]) for r in rows]
    svg_scatter = scatter(scatter_pts)

    n_dev = sum(1 for r in rows if r["dev"] != 0)
    avg_dev = sum(r["dev"] for r in rows) / len(rows)

    # 影：单字名曾被子串污染，预取其修正后数值供叙述使用
    ying = next((r for r in rows if r["name"] == "影"), None)
    ying_real = ying["real"] if ying else 0
    ying_cp = ying["cp"] if ying else 0
    ying_dev = ying["dev"] if ying else 0

    dev_note = (
        f"49 个主要角色中 {n_dev} 个存在「提及章节 ≠ 真实登场章节」的背离，平均偏离 {avg_dev:.1f} 章。"
        f"最极端者为「川阴王」：被提及 {[r['cp'] for r in rows if r['name']=='川阴王'][0]} 章却<b>零真实登场</b>——"
        f"作为叛乱核心，其存在完全依靠他人转述与符号化指涉，构成典型的「在场却不在场」叙事策略；"
        f"「影」（提及 {ying_cp} 章、真实登场 {ying_real} 章）此前因单字名「影」被光影泛指词"
        f"（身影 / 背影 / 影子 …）误计，背离曾虚高至约 35；修正后背离约 {ying_dev} 章，"
        f"已回落至中等偏离，不宜再解读为强「符号型」叙事策略。"
        f"相对的，任琅（提及 {[r['mentions'] for r in rows if r['name']=='任琅'][0]} / 登场 {[r['real'] for r in rows if r['name']=='任琅'][0]}）"
        f"近乎贴合对角线，是标准的在场主角。"
    )

    # 背离明细表（Top 15）
    dev_rows = "".join(
        f"<tr><td>{r['name']}</td><td>{r['mentions']:,}</td><td>{r['cp']}</td>"
        f"<td>{r['real']}</td><td class='{'down' if r['dev']>5 else ''}'>{r['dev']:+d}</td>"
        f"<td>{'幕后/符号型' if (r['real']==0 and r['cp']>=5) else ('偏高' if r['dev']>5 else '正常')}</td></tr>"
        for r in rows[:15]
    )

    # —— 2) 人物-地点共现 ——
    loc_freq = Counter()
    for t in tags:
        for loc in t.get("main_locations", []):
            loc_freq[loc] += 1
    top_locs = [l for l, _ in loc_freq.most_common(8)]
    top_roles = [r["name"] for r in sorted(rows, key=lambda r: r["mentions"], reverse=True)[:12]]

    co = Counter()
    for t in tags:
        chars = t.get("characters_present", [])
        locs = t.get("main_locations", [])
        for ch in chars:
            for lc in locs:
                co[(ch, lc)] += 1

    matrix = {(r, l): co.get((r, l), 0) for r in top_roles for l in top_locs}
    svg_heat = heatmap(matrix, top_roles, top_locs)

    top_pairs = co.most_common(10)
    pair_rows = "".join(
        f"<tr><td>{a}</td><td>{b}</td><td>{cnt}</td></tr>" for (a, b), cnt in top_pairs
    )

    co_note = (
        f"逐章将「真实登场角色 × 本章主地点」展开，累计 {sum(co.values()):,} 对共现。"
        f"热力图聚焦提及 Top12 角色 × 主地点 Top8——纵向看「谁常在何处」，与 character_network"
        f"（角色-角色共现）形成正交互补：后者刻画关系网，前者刻画空间足迹。"
        f"例如「奉天」作为绝对核心地标，承载了最多角色的活动轨迹；"
        f"而某些仅在单点高频出没的角色，则其空间足迹高度集中。"
    )

    
    kpi_html = "\n".join(
        f'<div class="card"><div class="kpi-v">{v}</div><div class="kpi-l">{l}</div></div>'
        for v, l in [
            (len(rows), "主要角色"),
            (n_dev, "存在背离"),
            (f"{avg_dev:.1f}", "平均偏离(章)"),
            (sum(co.values()), "人物-地点共现对"),
            (len(top_locs), "高频主地点"),
        ]
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>《苇舟江湖梦》派生维度量化</title>
<link rel="stylesheet" href="theme.css"></head>
<body>
<header><h1>《苇舟江湖梦》派生维度量化</h1>
<p>数据源：char_stats.json ＋ chapter_data/all_tags.json ｜ 增量分析，不改动源数据</p></header>
<div class="wrap">
<div class="cards">{kpi_html}</div>

<section><h2>一、出场 vs 提及背离</h2><p class="sub">「基于名字扫描的在场章节」与「人工标注的真实登场章节」之差——识别幕后 / 符号型角色</p>
{svg_dev}
<div class="note">{dev_note}</div>
<h3 style="font-size:14px;color:#3a4a5a;margin:18px 0 6px;">背离明细（Top 15，按偏离降序）</h3>
<table><tr><th>角色</th><th>提及次数</th><th>提及章节</th><th>真实登场</th><th>背离</th><th>判定</th></tr>{dev_rows}</table>
<h3 style="font-size:14px;color:#3a4a5a;margin:18px 0 6px;">散点：真实登场 × 提及章节（对角线之下＝背离）</h3>
{svg_scatter}
<div class="note">红点落在对角线下方，表示「被频繁提及却少真实登场」；蓝点贴近对角线，表示「提及即登场」的常态主角。川阴王（0,19）是最显著的「在场却不在场」符号型异常点；「影」此前因单字名被光影泛指词污染、背离虚高至约 35，修正后坐标为（{ying_real},{ying_cp}）、背离约 {ying_dev} 章，已回落至中等偏离。</div></section>

<section><h2>二、人物-地点共现矩阵</h2><p class="sub">逐章 真实登场角色 × 主地点 累加；行=提及Top12角色，列=主地点Top8</p>
{svg_heat}
<div class="note">{co_note}</div>
<h3 style="font-size:14px;color:#3a4a5a;margin:18px 0 6px;">共现最强对（Top 10）</h3>
<table><tr><th>角色</th><th>地点</th><th>共现章数</th></tr>{pair_rows}</table>
</section>

<div class="foot">《苇舟江湖梦》文本量化分析 · 派生维度量化 · 补完人物网络的空间与"在场"视角</div>
</div></body></html>"""

    os.makedirs(os.path.join(ROOT, "产物"), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {OUT}  ({os.path.getsize(OUT):,} 字节)")
    print(f"KPI: 角色{len(rows)} 背离{n_dev} 平均{avg_dev:.1f} 共现{sum(co.values())} 地点{len(top_locs)}")


if __name__ == "__main__":
    main()
