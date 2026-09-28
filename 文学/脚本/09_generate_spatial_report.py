#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
苇舟江湖梦 - 空间地点专业分析报告生成器
基于内嵌参考图像素坐标 + 文本旅行时间标定 + 地形/战术描述
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ----------------------------------------------------------------------------
# 1. Load spatial data
# ----------------------------------------------------------------------------
data = json.load(open(os.path.join(ROOT, "数据", "spatial_data.json"), encoding="utf-8"))
nodes = data["nodes"]
key = data["key"]
mat = data["matrix"]
scale_km = data["scale_km_per_px"]

# importance / role metadata
meta = {
    "京": {"tier": "A", "role": "帝都/政治中心", "terrain": "盆地平原，宫城雄踞", "note": "全书终极战略目标；盆地粮仓角邺为其供给"},
    "川阴城": {"tier": "A", "role": "西南王都/陈奉天根据地", "terrain": "南依山脉，梨花川上游", "note": "中原第二都，王宫依山而建；陈奉天策源地"},
    "海都": {"tier": "A", "role": "东海水师/商贸港城", "terrain": "滨海，铁闸海防", "note": "许达起家之地；海运关键，受海盗袭扰"},
    "楚城": {"tier": "B", "role": "南疆商都/苏氏前线", "terrain": "前为旷野，城防坚固", "note": "赵骁屠城地；后成东区战线补给源"},
    "苏城": {"tier": "B", "role": "苏氏商帮本部", "terrain": "山谷中的城池", "note": "苏雨、苏沐文根据地；连接楚城与川阴"},
    "望岳镇": {"tier": "B", "role": "主角启程点/京西门户", "terrain": "北侧平原，近山", "note": "任琅和尚樱离开山村后首个重要城镇"},
    "奉秋": {"tier": "B", "role": "海郡北方重镇", "terrain": "丘陵环绕", "note": "许达海郡起兵后首取；马远、黄亚钊争夺"},
    "石陵": {"tier": "B", "role": "奉秋西侧据点", "terrain": "主城周围多丘陵", "note": "十日内被许达攻下；与奉秋互为犄角"},
    "卫京郡": {"tier": "A", "role": "京城北方最后一道关隘", "terrain": "峡谷关城，绝壁夹道，内外双层城墙", "note": "陈奉天北上必经之路；聂林山顶设伏点"},
    "南岭关": {"tier": "B", "role": "京城东南门户", "terrain": "山岭关隘", "note": "赵翔献城；通角邺粮仓"},
    "夫文渡口": {"tier": "B", "role": "梨花川战略渡口", "terrain": "江面开阔，南北岸对垒", "note": "许达八日埋伏、火攻张广义；冬季水缓可渡"},
    "宿冰都": {"tier": "B", "role": "东北冰雪重镇/浣冰郡入口", "terrain": "雪峰环绕，冰窟资源", "note": "朝廷疏散百姓方向；苦寒但战略后方"},
    "建武": {"tier": "C", "role": "东部沿海郡县", "terrain": "平原近海", "note": "黄九州联合防线东翼"},
    "川陵": {"tier": "C", "role": "川阴东部边城", "terrain": "梨花川西北岸平原", "note": "程廖 exile 之地；陈奉天攻势中易帜"},
    "梨阳": {"tier": "C", "role": "陈奉天故乡/旧封地", "terrain": "川阴北侧平原", "note": "被屠城；距川阴城仅约2日路程"},
    "角都": {"tier": "C", "role": "京畿粮仓", "terrain": "关内盆地", "note": "京城近郊，南岭关东折可达"},
    "昌平": {"tier": "C", "role": "京南郡县", "terrain": "平原", "note": ""},
    "武都": {"tier": "C", "role": "东部郡县", "terrain": "平原", "note": "东线被赵翔攻下"},
    "方上": {"tier": "C", "role": "东部郡县", "terrain": "平原", "note": "黄九州防线中枢"},
    "响城": {"tier": "C", "role": "夫文渡口上游小城", "terrain": "临江，东西多绝壁", "note": "冬季渡江替代点，有烽火台"},
    "清州": {"tier": "C", "role": "东部沿海州", "terrain": "平原", "note": "黄九州联合防线西翼"},
}

tier_color = {"A": "#c0392b", "B": "#2980b9", "C": "#27ae60"}
tier_r = {"A": 9, "B": 7, "C": 5}

# ----------------------------------------------------------------------------
# 2. Helpers
# ----------------------------------------------------------------------------
def dist(a, b):
    return math.hypot(nodes[a][0]-nodes[b][0], nodes[a][1]-nodes[b][1]) * scale_km

def lookup(a, b):
    i = key.index(a)
    j = key.index(b)
    return mat[i][j]

# ----------------------------------------------------------------------------
# 3. SVG Map
# ----------------------------------------------------------------------------
# viewbox: scaled map (50% of original)
vb_w, vb_h = 3174, 2244

def px(x):
    return x

def py(y):
    return y

# river paths (approximate based on reference map)
lihua_river = [
    (40, 1080), (120, 1050), (250, 1020), (420, 1010), (600, 1030),
    (800, 1060), (1000, 1090), (1200, 1110), (1400, 1130), (1600, 1140),
    (1800, 1150), (2000, 1160), (2200, 1170), (2400, 1180), (2600, 1220),
    (2750, 1300), (2850, 1400), (2900, 1550), (2920, 1700), (2910, 1900),
    (2880, 2100), (2840, 2244)
]
mochuan_river = [
    (2300, 0), (2280, 80), (2270, 160), (2260, 240), (2240, 320),
    (2200, 400), (2150, 500), (2120, 600), (2140, 700), (2200, 800),
    (2280, 900), (2340, 1000), (2380, 1100), (2420, 1200), (2480, 1350),
    (2550, 1500), (2620, 1650), (2700, 1800), (2780, 1950), (2850, 2100),
    (2920, 2244)
]

def polyline(pts):
    return " ".join(f"{x},{y}" for x, y in pts)

# mountain zones (approximate polygons)
mountain_polys = [
    # 南山-奕剑-望岳西山地
    [(0, 300), (400, 320), (500, 500), (300, 650), (0, 600)],
    # 北梨岭
    [(1200, 1000), (1800, 1050), (1850, 1180), (1300, 1200), (1100, 1130)],
    # 南梨岭
    [(1150, 1300), (1750, 1350), (1800, 1500), (1200, 1480), (1050, 1400)],
    # 苏城南山地
    [(1050, 1550), (1350, 1600), (1400, 1900), (1100, 1850)],
    # 楚城周边山地
    [(1700, 1700), (2100, 1750), (2150, 2000), (1750, 1980)],
    # 卫京都-蒙城山地
    [(700, 150), (1100, 180), (1150, 450), (850, 500), (650, 350)],
]

# strategic routes (origin, dest, label, style)
routes = [
    ("望岳镇", "京", "任琅入京主线", "#e74c3c"),
    ("京", "卫京郡", "北道·陈奉天北上", "#8e44ad"),
    ("卫京郡", "川阴城", "川阴王主力轴", "#8e44ad"),
    ("川阴城", "苏城", "西-南商道", "#3498db"),
    ("苏城", "楚城", "南区战线", "#3498db"),
    ("楚城", "夫文渡口", "东线补给/渡江", "#16a085"),
    ("海都", "奉秋", "海郡北征", "#d35400"),
    ("奉秋", "石陵", "奉秋-石陵联动", "#d35400"),
    ("石陵", "楚城", "东线南伸", "#d35400"),
    ("南岭关", "角都", "东南粮道", "#f39c12"),
    ("京", "南岭关", "京畿东南走廊", "#f39c12"),
    ("宿冰都", "京", "东北后方通道", "#7f8c8d"),
]

def make_svg():
    svg = [f'<svg viewBox="0 0 {vb_w} {vb_h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;background:#e8e0c5">']
    # defs
    svg.append('''<defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#555"/></marker>
    </defs>''')
    # sea
    svg.append('<path d="M3174,0 L2700,0 Q2600,400 2700,900 Q2850,1600 3174,2244 Z" fill="#4a90d9" opacity="0.35"/>')
    # plains base
    svg.append('<rect width="3174" height="2244" fill="#e8e0c5"/>')
    svg.append('<path d="M3174,0 L2700,0 Q2600,400 2700,900 Q2850,1600 3174,2244 Z" fill="#6baed6" opacity="0.35"/>')
    # mountains
    for poly in mountain_polys:
        svg.append(f'<polygon points="{polyline(poly)}" fill="#7f8c5a" opacity="0.35" stroke="none"/>')
    # rivers
    svg.append(f'<polyline points="{polyline(lihua_river)}" fill="none" stroke="#5dade2" stroke-width="14" stroke-linecap="round"/>')
    svg.append(f'<polyline points="{polyline(mochuan_river)}" fill="none" stroke="#5dade2" stroke-width="14" stroke-linecap="round"/>')
    # distance rings from 京 (200km, 400km)
    for r_km in [200, 400]:
        r_px = r_km / scale_km
        svg.append(f'<circle cx="{nodes["京"][0]}" cy="{nodes["京"][1]}" r="{r_px:.1f}" fill="none" stroke="#c0392b" stroke-width="2" stroke-dasharray="8,8" opacity="0.4"/>')
        svg.append(f'<text x="{nodes["京"][0]+r_px+10:.1f}" y="{nodes["京"][1]:.1f}" font-size="28" fill="#c0392b" opacity="0.6">{r_km}km</text>')
    # routes
    for a, b, label, color in routes:
        x1, y1 = nodes[a]
        x2, y2 = nodes[b]
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="4" stroke-dasharray="12,8" opacity="0.75" marker-end="url(#arrow)"/>')
    # nodes
    for name, (x, y) in nodes.items():
        if name not in meta:
            continue
        m = meta[name]
        r = tier_r[m["tier"]]
        color = tier_color[m["tier"]]
        svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="#fff" stroke-width="3"/>')
        # label with background
        svg.append(f'<text x="{x}" y="{y-r-8}" text-anchor="middle" font-size="30" font-weight="bold" fill="#2c3e50" stroke="#fff" stroke-width="4" paint-order="stroke">{name}</text>')
    # legend
    legend_x, legend_y = 40, 2100
    svg.append(f'<rect x="{legend_x-20}" y="{legend_y-50}" width="420" height="160" fill="#fff" opacity="0.85" rx="15"/>')
    items = [("A 级：核心都市/战略枢纽", "#c0392b"), ("B 级：郡县重镇/战线节点", "#2980b9"), ("C 级：一般城邑/辅助据点", "#27ae60")]
    for i, (txt, c) in enumerate(items):
        yy = legend_y + i * 45
        svg.append(f'<circle cx="{legend_x}" cy="{yy}" r="10" fill="{c}"/>')
        svg.append(f'<text x="{legend_x+25}" y="{yy+8}" font-size="28" fill="#2c3e50">{txt}</text>')
    # title on map
    svg.append('<text x="1587" y="60" text-anchor="middle" font-size="48" font-weight="bold" fill="#2c3e50" stroke="#fff" stroke-width="5" paint-order="stroke">《苇舟江湖梦》相对空间位置与战略走廊</text>')
    svg.append('</svg>')
    return "\n".join(svg)

# ----------------------------------------------------------------------------
# 4. HTML Report
# ----------------------------------------------------------------------------
html = []
html.append('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>《苇舟江湖梦》空间地点分析报告</title>')
html.append('''<link rel="stylesheet" href="theme.css"></head><body>''')

html.append('<h1>《苇舟江湖梦》空间地点专业分析报告</h1>')
html.append('<p><b>分析对象：</b>霜月仲明《苇舟江湖梦》全本 62 章；<b>数据来源：</b>小说内嵌参考图（reference_map.jpeg）像素坐标 + 文本旅行时间/方向/地形/战术描述。</p>')

html.append('<div style="display:flex;flex-wrap:wrap;justify-content:center">')
html.append('<div class="metric"><b>32</b>空间节点</div>')
html.append('<div class="metric"><b>228</b>km/标准行军日<br><span class="small">基准：望岳镇→京≈13日</span></div>')
html.append('<div class="metric"><b>35</b>里/日<br><span class="small">混合行军速度假设</span></div>')
html.append('<div class="metric"><b>0.41</b>里/px<br><span class="small">地图像素比例尺</span></div>')
html.append('</div>')

html.append('<h2>一、空间分析方法论</h2>')
html.append('<ol>')
html.append('<li><b>底图：</b>从 docx 中提取作者手绘《简易参考图》，尺寸 3174×2244 px，包含主要都市、山脉、河流、关隘。</li>')
html.append('<li><b>坐标采集：</b>在带网格底图上读取各节点像素坐标，以 京 为地理中心，建立相对坐标系。</li>')
html.append('<li><b>比例尺标定：</b>以文本强锚点「任琅一行从望岳镇到京城，十几天后抵达」为基准，取 13 日；按古代混合行军速度 35 里/日（≈17.5 km/日）折算，得 455 里≈228 km 对应图上 1122 px，故比例尺 ≈0.203 km/px。</li>')
html.append('<li><b>地形修正：</b>山河、峡谷、雪原、沼泽等地形对实际通行速度的影响，在「战术地理」章节单独标注；距离矩阵给出的是直线/标准道路行军日，复杂地形需乘以 1.3–2.0 的通行系数。</li>')
html.append('</ol>')
html.append('<div class="note"><b>重要说明：</b>本分析为「相对空间关系」而非绝对经纬度。所有距离、方位均以内嵌图为框架、以文本旅行时间为约束，用于理解叙事中的行军节奏、战略纵深与地形价值。</div>')

html.append('<h2>二、宏观空间格局</h2>')
html.append('<p>小说地理呈现<b>“一核两翼、三河两山”</b>格局：</p>')
html.append('<ul>')
html.append('<li><b>一核：</b>京（帝都）位于北部中央盆地，是全书政治终点与最终战场。</li>')
html.append('<li><b>西翼：</b>川阴城—梨阳—望岳镇一线，为任琅成长与陈奉天势力根源；梨花川上游流经。</li>')
html.append('<li><b>东翼：</b>海都—奉秋—石陵—楚城—苏城沿海/沿河走廊，为许达、苏雨、马远、赵骁角逐的东区战线。</li>')
html.append('<li><b>北翼：</b>卫京郡—宿冰都（浣冰郡）构成京城北方屏障与后方。</li>')
html.append('<li><b>两山：</b>北梨岭、南梨岭横亘中部，成为东西翼天然分隔；卫京郡北侧山谷、南岭关则是京城南北两大门户。</li>')
html.append('<li><b>三河：</b>梨花川（东西横贯）、墨川（东北纵向入海）提供水运通道与渡江战场；清水渡口、大支渡口、京墨渡口为关键节点。</li>')
html.append('</ul>')

html.append('<h2>三、相对空间位置图</h2>')
html.append('<div class="mapbox">')
html.append(make_svg())
html.append('</div>')
html.append('<div class="note">图例：红色虚线圈为以京为中心的 200 km、400 km 战略纵深环；彩色虚线为书中主要行军/补给走廊；绿色阴影为山脉，蓝色为河流，右侧蓝色为海域。</div>')

html.append('<h2>四、节点地形与战略角色</h2>')
html.append('<table><tr><th>节点</th><th>等级</th><th>战略角色</th><th>地形特征</th><th>文本依据摘要</th></tr>')
for name, m in meta.items():
    html.append(f'<tr><td><b>{name}</b></td><td>{m["tier"]}</td><td>{m["role"]}</td><td>{m["terrain"]}</td><td>{m["note"]}</td></tr>')
html.append('</table>')

html.append('<h2>五、核心距离矩阵（km / 标准行军日）</h2>')
html.append('<p>下表为 21 个关键节点间的直线距离与按 35 里/日估算的标准行军日。山地、渡河、围城等场景实际耗时需增加 30%–100%。</p>')
html.append('<div style="overflow-x:auto"><table><tr><th></th>')
for b in key: html.append(f'<th>{b}</th>')
html.append('</tr>')
for i, a in enumerate(key):
    html.append(f'<tr><th>{a}</th>')
    for j, b in enumerate(key):
        m = mat[i][j]
        html.append(f'<td>{m["km"]}<br><span class="small">{m["days"]}日</span></td>')
    html.append('</tr>')
html.append('</table></div>')

html.append('<h2>六、文本旅行时间锚点</h2>')
html.append('<table><tr><th>路线</th><th>文本描述</th><th>推算距离</th><th>与模型偏差</th><th>说明</th></tr>')
anchors = [
    ("望岳镇→京", "任琅一行人到达京城是十几天后的事", "≈228 km / 13 日", "基准锚点", "混合商旅速度"),
    ("暮山城→川阴城", "到达川阴城的前二十天，行至暮山城", "≈350 km / 20 日", "模型：京→川阴≈370 km/21 日", "暮山城可视作京畿西道节点"),
    ("当前位置→浣冰郡", "浣冰郡也不算近，大概得有两个多月", "—", "图上宿冰都距京仅 260 km", "宿冰都或为浣冰郡南境入口，郡治距图框外；冬季慢行、绕路"),
    ("奕剑峰→山下镇", "约莫两个时辰的路", "≈7–10 km", "山径慢行", "符合"),
    ("某地→村口", "又走了不到两个时辰，抵达村口", "≈7–10 km", "山径/马行", "符合"),
    ("许达营→奉秋", "近一个半时辰狂奔到达奉秋", "≈15–20 km", "骑兵追击", "急行军"),
    ("黄亚钊营↔马远营", "相距十五里", "≈7.5 km", "营地间距", "符合"),
    ("苏雨营↔许达营", "相距十五里", "≈7.5 km", "江岸对峙", "符合"),
    ("陈奉天攻卫京郡", "没个三五月休想破城", "—", "卫京郡地形险峻", "防御价值极高"),
]
for route, text, est, dev, note in anchors:
    html.append(f'<tr><td>{route}</td><td>{text}</td><td>{est}</td><td>{dev}</td><td>{note}</td></tr>')
html.append('</table>')

html.append('<h2>七、战术地理研判</h2>')
html.append('<h3>7.1 京城防御：两关一谷</h3>')
html.append('<ul>')
html.append('<li><b>卫京郡（北大门）：</b>距京约 140 km / 8 日，处于「必经谷道，两侧绝壁」。陈奉天正面强攻七日无果，聂林于北侧山峰俯瞰全军；程廖试图绕山偷袭后方。该谷道是全书最关键的防御咽喉。</li>')
html.append('<li><b>南岭关（东南门）：</b>距京仅 81 km / 4.6 日，是京畿东南最后一道山隘；通关后东折可达角都粮仓，再北便是京城平原。</li>')
html.append('<li><b>京城本身：</b>内外城结构（据卫京郡推断），盆地粮仓支撑长期围困；最终皇帝疏散百姓往东北浣冰郡，说明京城依赖东北后方通道。</li>')
html.append('</ul>')

html.append('<h3>7.2 东区战线：海都—奉秋—石陵—楚城—苏城走廊</h3>')
html.append('<ul>')
html.append('<li><b>海都：</b>东海水师基地，铁闸海防；许达以此为根据地北征。海都→奉秋约 120 km / 7 日，是张广义受命平叛的进军距离。</li>')
html.append('<li><b>奉秋—石陵：</b>相距仅 53 km / 3 日，互为犄角；石陵周围多丘陵，利于设伏与阻击。</li>')
html.append('<li><b>楚城—夫文渡口：</b>楚城距渡口约 166 km / 9.5 日，是东区战线向中部渡河延伸的必经之路。冬季水缓，响城东西绝壁使夫文渡口成为渡江焦点。</li>')
html.append('<li><b>苏城—楚城：</b>仅 144 km / 8.2 日，苏氏商帮可快速支援楚城，亦可通过楚城获得川阴铁骑援助。</li>')
html.append('</ul>')

html.append('<h3>7.3 西翼与川阴势力</h3>')
html.append('<ul>')
html.append('<li><b>川阴城—梨阳：</b>仅 33 km / 1.9 日，陈奉天故乡梨阳被屠后，他迅速以川阴城为新核心；两者同处梨花川上游平原，便于控制。</li>')
html.append('<li><b>川阴城→苏城：</b>255 km / 14.6 日，是陈奉天结盟苏氏、建立南区战线的通道。</li>')
html.append('<li><b>川阴城→京：</b>370 km / 21 日，陈奉天北上直取帝都的主轴；途中需穿越或绕过卫京郡。</li>')
html.append('<li><b>望岳镇：</b>位于京西 228 km，是任琅和尚樱走出山林后的第一个社会化节点；其北侧平原便于结营扎寨。</li>')
html.append('</ul>')

html.append('<h3>7.4 东北后方与浣冰郡</h3>')
html.append('<ul>')
html.append('<li><b>宿冰都/浣冰郡：</b>位于东北沿海，雪峰环绕、冰窟资源独特；皇帝将京城百姓迁往「东北浣冰郡一带」，显示其为王朝战略后方与避难所。</li>')
html.append('<li><b>墨川—京墨渡口：</b>纵向河流将东北与京城连接，水运可加速兵员、粮草调动。</li>')
html.append('</ul>')

html.append('<h2>八、关键发现</h2>')
html.append('<ol>')
html.append('<li><b>空间叙事的双轴结构：</b>全书军事行动围绕「西轴（川阴城→京）」与「东轴（海都→楚城/夫文渡口）」展开，两轴在京城交汇，形成东西夹击之势。</li>')
html.append('<li><b>京城的致命纵深：</b>京城距南岭关仅约 80 km（4–5 日），距卫京郡约 140 km（8 日），战略纵深偏薄；一旦两关失守，京城无险可守，只能依赖疏散。</li>')
html.append('<li><b>梨花川的切割作用：</b>东西横贯的梨花川将地图分为南北两半，夫文渡口、大支渡口成为东线兵力北渡的必争之地；冬季水缓时渡口价值倍增。</li>')
html.append('<li><b>北梨岭—南梨岭的屏障效应：</b>两岭横亘中部，使川阴势力难以直接东进，也迫使陈奉天选择「北上取京」而非「东出争海」。</li>')
html.append('<li><b>海都的侧翼价值：</b>海都距京约 350 km（20 日），看似遥远，但海运可压缩后勤时间；许达若能控制夫文渡口并建立水军，可从东侧威胁京城侧背。</li>')
html.append('<li><b>地形与行军节奏高度吻合：</b>小说中「十几日到京」「前二十天到暮山城」「两个时辰到山下镇」「十五里对峙」等描述，与基于参考图测算的相对距离基本一致，说明作者在空间设定上具有内在一致性。</li>')
html.append('</ol>')

html.append('<h2>九、局限与使用建议</h2>')
html.append('<ul>')
html.append('<li>内嵌图为示意性手绘，节点坐标存在 ±20–40 km 的判读误差。</li>')
html.append('<li>「标准行军日」假设为每日 35 里平坦道路；实际小说中的急行、追兵、风雪、围城会显著改变耗时。</li>')
html.append('<li>部分节点（如仙境、千佛谷、堕凤谷）不在参考图中，未纳入本空间模型；它们属于秘境/超自然空间，应单独分析。</li>')
html.append('<li>建议结合本报告与前期人物/事件量化报告，进一步分析「空间距离如何影响救援、情报传递与战争动员节奏」。</li>')
html.append('</ul>')

html.append('<p style="margin-top:40px;color:#7f8c8d;font-size:13px;text-align:center">报告生成时间：2026-08-17 · 分析文件：苇舟江湖梦.docx</p>')

# 整合来源（L3-1 空间 4→1+1）：标注本报告与 11/15 的关系
html.append('<h2>十、整合来源</h2>')
html.append('<p class="see-also" style="background:rgba(34,211,238,.08);border:1px solid rgba(34,211,238,.3);border-radius:10px;padding:10px 14px;margin:6px 0;color:#d7e2f7;font-size:13px"><b>本报告为空间地理的权威主版本。</b>相关视角与子集：</p>')
html.append('<ul>')
html.append('<li>📐 <b>纯文本派生版（互补视角）</b>：<a href="苇舟江湖梦_地理位置关系图.html">苇舟江湖梦_地理位置关系图.html</a> — 仅依据方位词/里程/水文，不引用内嵌参考图，§ 1 SVG 地图 + § 2 方位约束表 + § 5 关键距离与本报告互为参照。</li>')
html.append('<li>📊 <b>地点语境档案（量化补充）</b>：<a href="苇舟江湖梦_地理描述量化.html">苇舟江湖梦_地理描述量化.html</a> — 54 个地点的地形类型 + 17 项地理要素 + 抽样描述句。</li>')
html.append('<li>🕒 <b>地名热度（原 15 § 4，已并入本体系）</b>：清洗后地名 Top 15 详见 <a href="苇舟江湖梦_时间节奏量化.html">苇舟江湖梦_时间节奏量化.html</a> 历史版本（15 § 4 现已跳转至此体系）。</li>')
html.append('</ul>')

html.append('</body></html>')

open(os.path.join(ROOT, "产物", "苇舟江湖梦_空间地点分析报告.html"), "w", encoding="utf-8").write("\n".join(html))
print("Report saved: 苇舟江湖梦_空间地点分析报告.html")