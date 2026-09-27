# -*- coding: utf-8 -*-
"""就地升级《派生维度量化》报告：将 2 个静态 SVG 卡片替换为 ECharts 交互式图表。
  1) 出场章数 vs 总提及：背离扫描（散点，悬停看人物）
  2) 人物-地点共现矩阵（Top12×Top12 热力图）
数据取自已验证的 char_stats.json 与 chapter_data/all_tags.json。
"""
import os, io, json, collections
import _chartlib as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_派生维度量化.html")
CS = os.path.join(ROOT, "数据", "char_stats.json")
TAGS = os.path.join(ROOT, "数据", "chapter_data", "all_tags.json")

cs = C.load_json(CS)
tags = C.load_json(TAGS)

# ---- 图 1：背离散点 ----
cs_sorted = sorted(cs, key=lambda c: c["mentions"], reverse=True)
NAMES = [c["name"] for c in cs_sorted]
CHP = [c["chapters_present"] for c in cs_sorted]
MENT = [c["mentions"] for c in cs_sorted]
RATIO = [round(c["mentions"] / max(1, c["chapters_present"]), 1) for c in cs_sorted]

SC_DATA = [{"name": n, "value": [chp, ment], "ratio": r}
            for n, chp, ment, r in zip(NAMES, CHP, MENT, RATIO)]
sc_opt = (
    "function(vars){\n"
    "  var palette=WZ.buildTheme().color;\n"
    "  var data=%s;\n"
    "  return {\n"
    "    title:{text:'出场章数 vs 总提及：背离扫描',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:64,right:40,top:48,bottom:56,containLabel:true},\n"
    "    tooltip:{trigger:'item',formatter:function(p){var d=p.data; return '<b>'+d.name+'</b><br/>出场章数：'+d.value[0]+'<br/>总提及：'+d.value[1]+'<br/>提及/章：'+d.ratio.toFixed(1);}},\n"
    "    xAxis:{type:'value',name:'出场章数',min:0,max:60},\n"
    "    yAxis:{type:'value',name:'总提及次数',min:0},\n"
    "    series:[{type:'scatter',data:data,\n"
    "      symbolSize:function(v){return Math.max(9, Math.sqrt(v[1])*1.15);},\n"
    "      itemStyle:{color:palette[0],opacity:0.72,borderColor:palette[1],borderWidth:0.6},\n"
    "      emphasis:{focus:'self',label:{show:true,formatter:'{b}',position:'top',color:vars.ink,fontWeight:'bold'}}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n"
    "  };\n"
    "}"
) % (json.dumps(SC_DATA, ensure_ascii=False),)

# ---- 图 2：人物-地点共现热力图 ----
TOPK = 12
top_chars = [c["name"] for c in cs_sorted[:TOPK]]
loc_counter = collections.Counter()
for e in tags:
    for loc in e.get("main_locations", []):
        loc_counter[loc] += 1
top_locs = [loc for loc, _ in loc_counter.most_common(TOPK)]
# 共现计次：同一章内 人物∈top_chars 且 地点∈top_locs
ci = {n: i for i, n in enumerate(top_chars)}
li = {n: i for i, n in enumerate(top_locs)}
cells = []
mx = 0
for e in tags:
    chars = set(e.get("characters_present", [])) & set(top_chars)
    locs = set(e.get("main_locations", [])) & set(top_locs)
    for ch in chars:
        for lo in locs:
            v = 1
            xi, yi = li[lo], ci[ch]
            # 累加（同一章一对只计 1 次，但可能多章重复 → 计章数）
            cells.append([xi, yi, v])
# 合并重复 (xi,yi)
agg = collections.Counter((c[0], c[1]) for c in cells)
CELLS = [[k[0], k[1], agg[k]] for k in agg]
mx = max([c[2] for c in CELLS], default=0)

heat_opt = (
    "function(vars){\n"
    "  var palette=WZ.buildTheme().color;\n"
    "  var CH=%s, LO=%s, CELLS=%s;\n"
    "  return {\n"
    "    title:{text:'人物-地点共现矩阵（Top12 人物 × Top12 地点，按同章共现章数）',left:'center',top:4,textStyle:{color:vars.ink,fontSize:13.5}},\n"
    "    grid:{left:92,right:24,top:50,bottom:118,containLabel:false},\n"
    "    tooltip:{trigger:'item',position:'top',formatter:function(p){return CH[p.data[1]]+' @ '+LO[p.data[0]]+'：'+p.data[2]+' 章';}},\n"
    "    xAxis:{type:'category',data:LO,axisLabel:{interval:0,rotate:55,color:vars.muted,fontSize:11},splitArea:{show:true}},\n"
    "    yAxis:{type:'category',data:CH,axisLabel:{color:vars.muted,fontSize:11},splitArea:{show:true}},\n"
    "    visualMap:{min:0,max:%d,calculable:true,orient:'horizontal',left:'center',bottom:4,\n"
    "      inRange:{color:[vars.surface,'#cfe3f2',palette[0],palette[1]]},textStyle:{color:vars.muted}},\n"
    "    series:[{name:'共现',type:'heatmap',data:CELLS,\n"
    "      label:{show:false},emphasis:{itemStyle:{shadowBlur:8,shadowColor:'rgba(0,0,0,.3)'}}}],\n"
    "    animationDurationUpdate:420\n"
    "  };\n"
    "}"
) % (json.dumps(top_chars, ensure_ascii=False), json.dumps(top_locs, ensure_ascii=False),
     json.dumps(CELLS), mx)

hint_sc = "交互：悬停查看人物「出场章数 / 总提及 / 提及每章」· 框选缩放 · 右上角图例。右上远离原点的点＝高提及却少出场（浓墨重彩型）。"
hint_heat = "交互：悬停查看「人物 @ 地点」的同章共现次数 · 颜色越深共现越多 · 拖动缩放。"

card_sc = C.card("一、出场 vs 提及背离（交互式）", "dv_sc", "none", len(NAMES), hint_sc, height=460)
card_heat = C.card("二、人物-地点共现矩阵（交互式）", "dv_heat", "none", len(CELLS), hint_heat, height=520)

with io.open(HTML, "r", encoding="utf-8") as f:
    html = f.read()
html = C.replace_heading_block(html, "一、出场 vs 提及背离", "一、出场 vs 提及背离（交互式）", card_sc)
html = C.replace_heading_block(html, "二、人物-地点共现矩阵", "二、人物-地点共现矩阵（交互式）", card_heat)
script = C.bundle([
    ("dv_sc", sc_opt, "none", len(NAMES)),
    ("dv_heat", heat_opt, "none", len(CELLS)),
])
html = C.inject_script(html, script)
with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("[完成] 派生维度量化 → ECharts 交互式（散点 + 热力图，均为交互型 controls=none）")
print("  散点人物数:%d · 热力图 Top%d×Top%d，最大同章共现 %d" % (len(NAMES), TOPK, TOPK, mx))
