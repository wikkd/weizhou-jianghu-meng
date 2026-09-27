# -*- coding: utf-8 -*-
"""
《苇舟江湖梦》人物共现网络构建
- 读取 chapter_data/all_tags.json（人物已归一，直接采用原值）
- 按章去重两两无向共现，边权=共现章数
- 计算 degree / pagerank / betweenness / 社区
- appearances: 优先 char_stats.json 的 mentions，否则以 all_tags 出场章数计
- 输出 analysis/character_network.json 与 产物/苇舟江湖梦_人物关系网络.html
"""
import os, json, math, itertools
import networkx as nx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(ROOT, "数据", "analysis"), exist_ok=True)

# ---------- 1. 读取数据 ----------
with open(os.path.join(ROOT, "数据", "chapter_data", "all_tags.json"), encoding="utf-8") as f:
    tags = json.load(f)
with open(os.path.join(ROOT, "数据", "char_stats.json"), encoding="utf-8") as f:
    char_stats = json.load(f)

# char_stats: 规范人物的全文提及数
cs_map = {c["name"]: c for c in char_stats}

# ---------- 2. 共现统计（按章去重） ----------
pair_weight = {}          # (a,b) -> 共现章数
appear_chapters = {}      # 人物 -> 出场章数（用于扩展人物 appearances）
for ch in tags:
    chars = list(dict.fromkeys(ch.get("characters_present", [])))  # 保序去重
    chars = [c for c in chars if c]  # 去除空串
    for c in chars:
        appear_chapters[c] = appear_chapters.get(c, 0) + 1
    for a, b in itertools.combinations(sorted(set(chars)), 2):
        key = (a, b)
        pair_weight[key] = pair_weight.get(key, 0) + 1

# ---------- 3. 构建图 ----------
G = nx.Graph()
all_people = sorted(appear_chapters.keys())
G.add_nodes_from(all_people)
for (a, b), w in pair_weight.items():
    G.add_edge(a, b, weight=w)

# 节点属性：appearances
for n in G.nodes():
    if n in cs_map:
        G.nodes[n]["appearances"] = cs_map[n]["mentions"]
    else:
        G.nodes[n]["appearances"] = appear_chapters.get(n, 0)

# 中心性度量
deg = nx.degree_centrality(G)
pr = nx.pagerank(G, weight="weight")
# betweenness 对 101 节点近似：k=全部；若节点过多则采样。此处节点可控，直接全算。
btw = nx.betweenness_centrality(G, weight="weight")

# 社区划分
communities = nx.community.greedy_modularity_communities(G, weight="weight")
comm_of = {}
for i, comm in enumerate(communities):
    for n in comm:
        comm_of[n] = i

# ---------- 4. 输出 JSON ----------
nodes_out = []
for n in sorted(G.nodes(), key=lambda x: -deg.get(x, 0)):
    nodes_out.append({
        "name": n,
        "degree": round(deg.get(n, 0), 6),
        "pagerank": round(pr.get(n, 0), 6),
        "community": comm_of.get(n, -1),
        "appearances": G.nodes[n]["appearances"],
    })

edges_out = []
for a, b, w in G.edges(data=True):
    edges_out.append({
        "source": a,
        "target": b,
        "weight": w["weight"],
    })

net = {"nodes": nodes_out, "edges": edges_out}
with open(os.path.join(ROOT, "数据", "analysis", "character_network.json"), "w", encoding="utf-8") as f:
    json.dump(net, f, ensure_ascii=False, indent=2)

N = G.number_of_nodes()
M = G.number_of_edges()
K = len(communities)

# ---------- 5. 生成 SVG 网络图 + 自包含 HTML ----------
pos = nx.spring_layout(G, weight="weight", k=1.4, iterations=200, seed=42)

# 视图坐标映射（留出边距）
xs = [p[0] for p in pos.values()]
ys = [p[1] for p in pos.values()]
minx, maxx = min(xs), max(xs)
miny, maxy = min(ys), max(ys)
W, H = 1100, 820
pad = 60
def sx(x): return pad + (x - minx) / (maxx - minx) * (W - 2 * pad)
def sy(y): return pad + (y - miny) / (maxy - miny) * (H - 2 * pad)

# 颜色 ∝ 社区编号
palette = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#b07aa1",
           "#76b7b2", "#edc948", "#ff9da7", "#9c755f", "#bab0ac",
           "#86bcb6", "#d37295", "#f1ce63", "#a0cbe8", "#ffbe7d"]
def comm_color(c):
    return palette[c % len(palette)]

# 节点半径 ∝ degree（sqrt 缩放避免过大）
max_deg = max(deg.values())
def radius(n):
    d = deg.get(n, 0)
    return 6 + 26 * math.sqrt(d / max_deg) if max_deg > 0 else 6

# 边宽 ∝ 权重
max_w = max(w["weight"] for _, _, w in G.edges(data=True))
def edge_width(w):
    return 0.6 + 4.0 * (w / max_w)

# Top20 节点
top20 = sorted(G.nodes(), key=lambda x: -deg.get(x, 0))[:20]

svg_parts = []
svg_parts.append(f'<svg id="net" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="人物共现网络图">')
# 边
for a, b, w in G.edges(data=True):
    x1, y1 = sx(pos[a][0]), sy(pos[a][1])
    x2, y2 = sx(pos[b][0]), sy(pos[b][1])
    svg_parts.append(
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="#999" stroke-opacity="0.28" stroke-width="{edge_width(w["weight"]):.2f}"/>'
    )
# 节点
for n in G.nodes():
    cx, cy = sx(pos[n][0]), sy(pos[n][1])
    r = radius(n)
    col = comm_color(comm_of.get(n, 0))
    svg_parts.append(
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{col}" '
        f'fill-opacity="0.82" stroke="#333" stroke-width="0.6">'
        f'<title>{n}｜社区{comm_of.get(n,0)}｜度中心性{deg.get(n,0):.3f}｜提及{G.nodes[n]["appearances"]}</title></circle>'
    )
# 标注 Top20
for n in top20:
    cx, cy = sx(pos[n][0]), sy(pos[n][1])
    r = radius(n)
    svg_parts.append(
        f'<text x="{cx:.1f}" y="{cy - r - 4:.1f}" text-anchor="middle" '
        f'font-size="13" font-weight="600" fill="#1a1a1a" '
        f'style="paint-order:stroke;stroke:#fff;stroke-width:3px;">{n}</text>'
    )
svg_parts.append('</svg>')
svg_content = "\n".join(svg_parts)

# Top15 中心性表
top15 = sorted(G.nodes(), key=lambda x: -deg.get(x, 0))[:15]
rows = []
for i, n in enumerate(top15, 1):
    rows.append(
        f"<tr><td>{i}</td><td class='nm'>{n}</td>"
        f"<td>{deg.get(n,0):.4f}</td>"
        f"<td>{pr.get(n,0):.4f}</td>"
        f"<td>{btw.get(n,0):.4f}</td>"
        f"<td>{G.degree(n)}</td>"
        f"<td>{G.nodes[n]['appearances']}</td>"
        f"<td>社区{comm_of.get(n,0)}</td></tr>"
    )
table_rows = "\n".join(rows)

# 社区说明（依据真实聚类：按共同出场场景而非阵营划分）
comm_desc = {
    0: "陈奉天领衔的权力博弈群（含皇帝、影、铁面人、聂林、张潇璃等中后期人物），是跨时间的最大聚类，内部以反王—朝堂—后期新角色混居。",
    1: "任琅主线成长群：任琅、尚樱为绝对核心，福、夏叶、刘笑岩、刘媛灵等长期同伴高频共现，是网络的枢纽社区。",
    2: "许达—苏雨支线江湖群：许达、苏雨、苏沐文、赵翔、马远等偏支线群侠，共现结构相对独立。",
    3: "陆氏局部小群：陆天、陆海、周舫、孟柯四人构成的后期小规模子图，对外连接稀疏。",
}
comm_rows = []
for i, comm in enumerate(communities):
    members = sorted(comm, key=lambda x: -deg.get(x, 0))
    desc = comm_desc.get(i, "由若干关联人物组成的局部聚类，内部共现紧密、对外连接稀疏。")
    comm_rows.append(
        f"<tr><td>社区{i}</td><td>{len(comm)}</td>"
        f"<td class='nm'>{'、'.join(members[:12])}{'…' if len(members) > 12 else ''}</td>"
        f"<td>{desc}</td></tr>"
    )
comm_table = "\n".join(comm_rows)

# 弱连接统计（仅 1 章共现且两端度很低）
weak = []
for a, b, w in G.edges(data=True):
    if w["weight"] == 1 and G.degree(a) <= 2 and G.degree(b) <= 2:
        weak.append(f"{a}—{b}")
weak_count = len(weak)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>苇舟江湖梦 · 人物关系网络</title>
<link rel="stylesheet" href="theme.css">
</head>
<body>
<header>
  <h1>《苇舟江湖梦》人物关系网络</h1>
  <p>基于 {len(tags)} 章已标注 data 构建 · 共现按章去重 · 边权=共现章数</p>
</header>
<main>

<section>
  <h2>一、网络概览</h2>
  <div class="stat">节点（人物）<b>{N}</b></div>
  <div class="stat">边（共现对）<b>{M}</b></div>
  <div class="stat">社区数<b>{K}</b></div>
  <div class="stat">弱连接（仅1章且两端度≤2）<b>{weak_count}</b></div>
</section>

<section>
  <h2>二、人物共现网络图</h2>
  <div class="svgwrap">{svg_content}</div>
  <div class="legend">
    <span><i class="dot" style="background:{palette[0]}"></i>社区0</span>
    <span><i class="dot" style="background:{palette[1]}"></i>社区1</span>
    <span><i class="dot" style="background:{palette[2]}"></i>社区2</span>
    <span><i class="dot" style="background:{palette[3]}"></i>社区3</span>
    <span><i class="dot" style="background:{palette[4]}"></i>社区4</span>
    <span><i class="dot" style="background:{palette[5]}"></i>社区5</span>
  </div>
  <p class="note">节点半径∝度中心性（sqrt 缩放）；颜色∝社区编号；边宽∝共现章数；悬停节点可见详情。Top20 节点已标注名称。</p>
</section>

<section>
  <h2>三、Top15 节点中心性</h2>
  <table>
    <thead><tr><th>排名</th><th>人物</th><th>度中心性</th><th>PageRank</th><th>中介中心性</th><th>度数</th><th>全文提及</th><th>社区</th></tr></thead>
    <tbody>{table_rows}</tbody>
  </table>
  <p class="note">全文提及：规范人物取自 <code>char_stats.json</code> 的 mentions；扩展人物以 <code>all_tags</code> 出场章数计。</p>
</section>

<section>
  <h2>四、社区划分说明</h2>
  <table>
    <thead><tr><th>社区</th><th>人数</th><th>成员（前列）</th><th>解读</th></tr></thead>
    <tbody>{comm_table}</tbody>
  </table>
  <p class="note">采用 <code>greedy_modularity_communities</code>（基于模块度贪心合并）划分。</p>
</section>

<section>
  <h2>五、方法注记</h2>
  <ul class="note">
    <li><b>共现定义：</b>对每一章，取章内 <code>characters_present</code> 中两两不同人物的无序组合记一次共现；同一章内不重复计数，跨章累加得到边权（共现章数）。</li>
    <li><b>人物归一：</b>原始数据已将 川阴王/王爷/反王 等并入 <code>陈奉天</code>，本分析直接采用原值，不做二次拆分或重命名。</li>
    <li><b>弱连接阈值：</b>本报告将「仅共同出场 1 章且两端节点度数均≤2」的边标记为弱连接（共 {weak_count} 条），刻画偶发、边缘的互动，予以保留以维持网络完整性。</li>
    <li><b>中心性：</b>度中心性按 <code>degree_centrality</code> 标准化；PageRank 以边权为转移概率；中介中心性按 <code>betweenness_centrality</code> 计算（权重参与）。</li>
    <li><b>布局：</b>采用 <code>spring_layout</code>（力导向，seed=42）生成二维坐标，迭代 200 次。</li>
    <li><b>数据来源：</b><code>chapter_data/all_tags.json</code>、<code>char_stats.json</code>；仅读取分析，未修改任何源文件。</li>
  </ul>
</section>

</main>
</body>
</html>
"""

out_html = os.path.join(ROOT, "产物", "苇舟江湖梦_人物关系网络.html")
with open(out_html, "w", encoding="utf-8") as f:
    f.write(html)

# 校验两个文件写入成功
for p in [os.path.join(ROOT, "数据", "analysis", "character_network.json"), out_html]:
    if not os.path.exists(p):
        raise SystemExit(f"OUTPUT MISSING: {p}")
    print("OK:", p, os.path.getsize(p), "bytes")

print(f"NETWORK DONE: nodes={N} edges={M} communities={K}")
