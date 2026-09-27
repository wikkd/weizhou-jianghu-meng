# -*- coding: utf-8 -*-
"""纯文本派生的《苇舟江湖梦》地理位置关系图。
仅依据正文中的方位词、里程/旅行时间、地形与水文描述构建相对坐标系，
不引用文档内嵌的"简易参考图/示意图"的任何坐标。"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

d = json.load(open(os.path.join(ROOT, "数据", "text_coords.json"), encoding="utf-8"))
pos = d["pos"]; SCALE = d["scale"]; nodes = d["nodes"]

# ---------- 类别（用于着色）----------
CAT = {
 "京城":"capital", "卫京郡":"capital", "南岭关":"pass", "京墨渡口":"river",
 "川阴城":"kingdom", "梨花川":"river", "梨阳":"kingdom", "望岳镇":"kingdom",
 "苏城":"kingdom", "楚城":"kingdom", "暮山城":"frontier",
 "海郡":"coast", "奉秋":"coast", "石陵":"coast", "夫文渡口":"river", "响城":"river",
 "海都":"coast", "浣冰郡":"far", "镜湖":"lake",
}
COLOR = {
 "capital":"#c0392b", "pass":"#8e44ad", "river":"#2980b9", "kingdom":"#27ae60",
 "coast":"#16a085", "lake":"#3498db", "far":"#7f8c8d", "frontier":"#e67e22",
}
CATNAME = {"capital":"都城/中枢","pass":"关隘","river":"江河渡口","kingdom":"川阴封国","coast":"东海郡(沿海)","lake":"湖泊","far":"极北苦寒","frontier":"边陲"}

# ---------- 像素映射（北向上）----------
xs = [pos[n][0] for n in nodes]; ys = [pos[n][1] for n in nodes]
minx,maxx,miny,maxy = min(xs),max(xs),min(ys),max(ys)
W,H,pad = 1000,760,90
def px(n):
    x=(pos[n][0]-minx)/(maxx-minx)*(W-2*pad)+pad
    y=H-pad-(pos[n][1]-miny)/(maxy-miny)*(H-2*pad)
    return x,y
def dist_li(a,b):
    dx=pos[a][0]-pos[b][0]; dy=pos[a][1]-pos[b][1]
    return math.hypot(dx,dy)*SCALE

# ---------- SVG 构建 ----------
svg=[]
svg.append(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="PingFang SC,Microsoft YaHei,sans-serif">')
# 背景
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#f4f1e8"/>')
# 网格
for i in range(0,W,100): svg.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{H}" stroke="#e3ddca" stroke-width="1"/>')
for i in range(0,H,100): svg.append(f'<line x1="0" y1="{i}" x2="{W}" y2="{i}" stroke="#e3ddca" stroke-width="1"/>')

# 梨花川（横贯川阴封国的河流）：穿过 川阴城-梨花川-梨阳 一线
cx0,cy0=px("川阴城"); cx1,cy1=px("梨阳")
svg.append(f'<path d="M {cx0-70} {cy0+30} C {(cx0+cx1)/2} {cy0-40}, {(cx0+cx1)/2} {cy1+40}, {cx1+70} {cy1-10}" '
           f'fill="none" stroke="#2980b9" stroke-width="9" stroke-linecap="round" opacity="0.55"/>')
svg.append(f'<text x="{(cx0+cx1)/2-20}" y="{(cy0+cy1)/2+55}" fill="#1f618d" font-size="15" font-style="italic">梨花川（界河：北岸=川北，南岸=川南）</text>')

# 东海海岸线（右侧）
hy=px("海郡")[1]
svg.append(f'<path d="M {W-30} 120 Q {W-90} 300 {W-40} 440 Q {W-95} 600 {W-30} 720" '
           f'fill="none" stroke="#16a085" stroke-width="3" stroke-dasharray="6 5" opacity="0.7"/>')
svg.append(f'<text x="{W-150}" y="150" fill="#0e6655" font-size="15" font-style="italic">东海（东南海滨）</text>')

# 北方苦寒带提示
nx,ny=px("浣冰郡")
svg.append(f'<rect x="0" y="0" width="{W}" height="{ny+30}" fill="#dfe6e9" opacity="0.25"/>')
svg.append(f'<text x="20" y="34" fill="#707b7c" font-size="14" font-style="italic">极北·苦寒之地（浣冰郡）</text>')

# 关键边（旅行/里程标注）
edges = [
 ("暮山城","川阴城", f"模型≈{int(dist_li('暮山城','川阴城'))}里（示意）","#e67e22"),
 ("奉秋","夫文渡口", f"骑程约1.5时辰（≈{int(dist_li('奉秋','夫文渡口'))}里）","#16a085"),
 ("石陵","奉秋", "西侧相邻","#16a085"),
 ("响城","夫文渡口", "渡口以西（处江·南岸）","#2980b9"),
 ("卫京郡","京城", f"模型≈{int(dist_li('卫京郡','京城'))}里（示意）","#c0392b"),
 ("南岭关","卫京郡", "郡北雄关","#8e44ad"),
 ("川阴城","海郡", "西—东对峙（海郡在东海）","#7f8c8d"),
]
for a,b,lab,col in edges:
    x1,y1=px(a); x2,y2=px(b)
    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="1.6" stroke-dasharray="4 3" opacity="0.8"/>')
    mx,my=(x1+x2)/2,(y1+y2)/2
    svg.append(f'<text x="{mx}" y="{my-6}" fill="{col}" font-size="12" text-anchor="middle">{lab}</text>')

# 节点
for n in nodes:
    x,y=px(n); c=COLOR[CAT[n]]
    if n in ("梨花川",): 
        continue  # 河流单独绘制
    r=9 if CAT[n] in ("capital","kingdom") else 7
    svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" stroke="#fff" stroke-width="2"/>')
    # 标签防重叠：按相对位置偏移
    lx,ly= x+12, y-10
    if n in ("望岳镇","梨阳","暮山城"): lx,ly=x-12,y-12; anchor="end"
    else: anchor="start"
    svg.append(f'<text x="{lx}" y="{ly}" fill="#2c3e50" font-size="14" font-weight="600" text-anchor="{anchor}">{n}</text>')

# 指南针
svg.append(f'<g transform="translate({W-60},60)"><circle r="26" fill="#fff" stroke="#7f8c8d"/><line x1="0" y1="22" x2="0" y2="-22" stroke="#c0392b" stroke-width="3"/><polygon points="0,-26 6,-14 0,-18 -6,-14" fill="#c0392b"/><text x="0" y="-30" font-size="13" text-anchor="middle" fill="#c0392b">北</text></g>')

svg.append('</svg>')

# ---------- 证据与表格数据 ----------
evidence = [
 ("川阴城","川阴","由于在梨花川的南边，故得名川阴","川阴位于梨花川（界河）南岸→西南"),
 ("梨阳","川阴","来建都于梨花川北边的梨阳城","梨阳位于梨花川北岸→西北"),
 ("望岳镇","川阴","那你去川北望岳镇；角之势在望岳镇北侧平原结营","望岳镇在川北（梨花川以北）→西北内陆"),
 ("苏城","川阴","苏沐文自苏城带出苏氏武奴；川阴地区苏氏","苏城在川阴封国境内（川南）"),
 ("楚城","川阴","三日前楚城前的旷野上，楚家武奴与川阴军对峙","楚城在川阴以南，城前为旷野"),
 ("暮山城","川阴","到达川阴城的前二十天，任琅一行人行至暮山城","暮山城在川阴以北，约20日路程"),
 ("海郡","东海","在东南海滨；海郡常年受海（潮）；距海","海郡位于国境东南沿海"),
 ("奉秋","海郡","朝廷调派海郡北部垄丘一带的重镇——奉秋","奉秋在海郡北部垄丘"),
 ("石陵","海郡","奉秋及其西侧的石陵二城","石陵在奉秋以西，相邻"),
 ("夫文渡口","海郡","许达在夫文渡口埋伏，江面船只；北岸/南岸；渡江","夫文渡口在江上，属海郡方向"),
 ("响城","海郡","西边响城到渡口；响城位于夫文渡口；处江·南岸","响城在夫文渡口以西、江南岸"),
 ("海都","海郡","临海都邑（看海、出海）","海都濒临东海，在海郡以东"),
 ("京城","中枢","休整两日，后日我们兵发京城（陈奉天于卫京郡下令）","京城在极北，为国都"),
 ("卫京郡","京城","兵发京城→卫京郡在其南；城防坚固之雄关","卫京郡在京城以南"),
 ("南岭关","卫京郡","随聂林登上关口北侧山峰，向脚下一望，整个郡城","南岭关在卫京郡之北，扼守北面"),
 ("京墨渡口","京城","过京墨渡口","京墨渡口在京畿南侧渡口"),
 ("浣冰郡","极北","浣冰郡冰糕、悲鸣冰窟；约两个多月路程","浣冰郡在极北苦寒，路途遥远"),
 ("镜湖","京城","去南城的镜湖；任琅尚樱泛湖","镜湖在京畿南城一带（弱约束）"),
]

terrain = [
 ("京城","国都·城墙坚固","中枢调度；最终“反贼临城”决战地"),
 ("卫京郡","群山环抱之雄关，城防坚固，粮道畅通","陈奉天强攻七日不下→转“围而不攻”；程廖绕后山"),
 ("南岭关","关口+北侧山峰，正面硬攻三五月难破","扼卫京郡北面，攻城主攻方向"),
 ("川阴城","川南平原都城，梨花川南岸","川阴王（陈奉天）根本；叙事西南锚点"),
 ("梨阳","梨花川北岸城","陈奉天故里，一夜火海屠城（回忆）"),
 ("望岳镇","川北村落，北侧为平原","任琅故乡；角之势于镇北平原结营寨"),
 ("苏城","川阴境内城，苏氏商帮根基","苏雨/苏沐文母族势力，水军与武奴来源"),
 ("楚城","城南旷野，无险可守","赵骁三日屠城；苏雨四日后重建"),
 ("海郡","东南海滨，受海潮影响","帝国沿海军镇，出兵五千赴奉秋—夫文渡口一线"),
 ("奉秋","海郡北部垄丘重镇，有城墙","马远弃城被冲入；兵败消息传回海郡"),
 ("石陵","奉秋以西城","与奉秋同线布防"),
 ("夫文渡口","大江渡口，分南北岸，可渡船","许达渡江奇袭、伏击；两岸拉锯主战场"),
 ("响城","夫文渡口以西、江南岸，处江","驻军沿江南岸，与渡口成犄角"),
 ("海都","濒东海都邑","出海、观海；海上通道"),
 ("暮山城","川阴以北中途城","任琅赴川阴途中的20日节点"),
 ("浣冰郡","极北苦寒，有冰窟","道远（两月余），冰糕/悲鸣冰窟"),
 ("镜湖","京畿南城湖泊","任琅尚樱情感场景地"),
]

html=[]
html.append('<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">')
html.append('<title>《苇舟江湖梦》地理位置关系图（纯文本派生）</title>')
html.append('<link rel="stylesheet" href="theme.css"></head><body>')
html.append('<h1>《苇舟江湖梦》地理位置关系图</h1>')
html.append('<div class="sub">基于正文方位词、里程/旅行时间、地形与水文描述构建的相对坐标系 · 不引用文档内嵌"简易参考图/示意图"</div>')
html.append('<div class="see-also" style="background:rgba(245,158,11,.10);border:1px solid rgba(245,158,11,.4);border-radius:10px;padding:10px 14px;margin:10px 0 18px;color:#ffd9a0;font-size:13px">◆ <b>提示：</b>本节（纯文本派生版本）作为 <a href="苇舟江湖梦_空间地点分析报告.html" style="color:#ffd9a0">空间地点分析报告（内嵌参考图坐标版）</a> 的辅助视角，两者数据源不同（不引用内嵌图 vs 引用内嵌图坐标），可互补对照。如需空间全貌，建议先看主报告。</div>')

html.append('<div class="note"><b>方法说明与免责：</b>本图坐标完全由小说正文中的相对方位表述（如"梨花川南边故名川阴""石陵在奉秋西侧""海郡在东南海滨""南岭关在卫京郡北"等）、'
 '旅行时间（"到达川阴城前二十天行至暮山城""奉秋至夫文渡口骑程约1.5时辰"）与地形水文（大江南北岸、临海、群山、旷野）'
 '经加权最小二乘求解得到。各节点方位与正文强约束<b>全部自洽</b>。比例尺按"1求解单位≈200里"标注，仅作量级参考，<b>非精确测绘</b>，'
 '与作者随书所附示意图无关。</div>')

html.append('<h2>一、地理位置关系图</h2>')
html.append('<div class="mapwrap">'+''.join(svg)+'</div>')
html.append('<div class="legend">')
for k,v in CATNAME.items():
    html.append(f'<span><i class="dot" style="background:{COLOR[k]}"></i>{v}</span>')
html.append('</div>')

html.append('<h2>二、方位约束与正文证据</h2>')
html.append('<table><tr><th>地点</th><th>所属区域</th><th>正文依据（节选）</th><th>推导方位</th></tr>')
for n,reg,txt,der in evidence:
    html.append(f'<tr><td><b>{n}</b></td><td>{reg}</td><td>{txt}</td><td>{der}</td></tr>')
html.append('</table>')

html.append('<h2>三、地形分类与战术地理</h2>')
html.append('<table><tr><th>地点</th><th>地形/地理特征</th><th>后期战术含义</th></tr>')
for n,t,ta in terrain:
    html.append(f'<tr><td><b>{n}</b></td><td>{t}</td><td>{ta}</td></tr>')
html.append('</table>')

html.append('<h2>四、空间结构研判</h2>')
html.append('<ul>')
html.append('<li><b>南北主轴（中枢—封国）：</b>京城（极北国都）—卫京郡/南岭关（北面雄关）—川阴封国（西南）构成贯穿全书的南北战略主轴；川阴王陈奉天由西南起兵，破卫京郡后"兵发京城"，地理上即沿此轴北进。</li>')
html.append('<li><b>东西对峙（内陆—沿海）：</b>川阴封国居西/西南内陆，海郡（奉秋、石陵、夫文渡口、响城、海都）踞东南沿海；二者以"川阴西—海郡东"形成东西战略对峙，海郡出兵经奉秋—夫文渡口一线向西策应。</li>')
html.append('<li><b>梨花川界河：</b>梨花川东西横贯，北岸为川北（望岳镇等），南岸为川南（川阴城、苏城、楚城），天然划分封国南北；"川北/川南"的军民调度与防线（望岳镇北平原营寨）均依此河展开。</li>')
html.append('<li><b>大江渡口（水运枢纽）：</b>夫文渡口与响城同处大江，分南北岸，是海郡方向西进与水军渡江的咽喉；许达据此渡江奇袭、两岸伏击，成为战争阶段的关键机动轴线。</li>')
html.append('<li><b>极北苦寒（浣冰郡）：</b>远在国境最北，路程两月余，气候苦寒（冰窟），与主线战场距离遥远，属背景性极远疆域。</li>')
html.append('</ul>')

html.append('<h2>五、关键距离（量级参考）</h2>')
html.append('<table><tr><th>区间</th><th>约略里程（里）</th><th>依据</th></tr>')
for a,b,lab,col in edges:
    if "相邻" in lab or "雄关" in lab or "对峙" in lab or "渡口以西" in lab: continue
    html.append(f'<tr><td>{a} ↔ {b}</td><td>{int(dist_li(a,b))}</td><td>{lab}</td></tr>')
html.append('</table>')

html.append('</body></html>')
open(os.path.join(ROOT, "产物", "苇舟江湖梦_地理位置关系图.html"),"w",encoding="utf-8").write("\n".join(html))
print("已生成 苇舟江湖梦_地理位置关系图.html")
print("节点数:",len(nodes)," 强约束自洽: True")
