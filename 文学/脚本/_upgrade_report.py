# -*- coding: utf-8 -*-
"""就地升级《分析报告》报告：将 4 个静态 SVG 卡片替换为 ECharts 交互式图表。
  一、文本概况与结构（逐章字数，时间轴+实时流）· 二、人物图谱（网络图）·
  三、时间轴与叙事时序（逐章时序密度，时间轴+实时流）· 四、空间谱系（坐标散点）
数据取自已验证的 series.json 与 text_coords.json。
"""
import os, io, json, math
import _chartlib as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_分析报告.html")
SRC = os.path.join(ROOT, "数据", "series.json")
TC = os.path.join(ROOT, "数据", "text_coords.json")
s = C.load_json(SRC)
tc = C.load_json(TC)
N = s["N"]

CH = list(range(1, N + 1))
CHAR1 = s["chap_chars"]
TIME3 = s["per_chap_time"]

# ---- 图 1：逐章字数（时间轴）----
c1_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'文本概况：逐章字数',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:60,right:40,top:48,bottom:64,containLabel:true},\n"
    "    tooltip:{trigger:'axis',valueFormatter:function(v){return (v==null)?'-':v+' 字';}},\n"
    "    xAxis:{type:'category',data:%s,name:'章',nameGap:26},\n"
    "    yAxis:{type:'value',name:'字数'},\n"
    "    series:[{name:'字数',type:'line',smooth:true,data:%s,showSymbol:false,\n"
    "      lineStyle:{width:2.2,color:palette[0]},itemStyle:{color:palette[0]},\n"
    "      areaStyle:{color:'rgba(44,93,138,0.08)'},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(CH), json.dumps(CHAR1))

# ---- 图 3：逐章时序密度（时间轴）----
c3_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'时间轴与叙事时序：逐章时序密度',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:54,right:40,top:48,bottom:64,containLabel:true},\n"
    "    tooltip:{trigger:'axis',valueFormatter:function(v){return (v==null)?'-':v;}},\n"
    "    xAxis:{type:'category',data:%s,name:'章',nameGap:26},\n"
    "    yAxis:{type:'value',name:'时序密度'},\n"
    "    series:[{name:'时序密度',type:'bar',data:%s,barWidth:'58%%',itemStyle:{color:palette[2],borderRadius:[3,3,0,0]},\n"
    "      emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(CH), json.dumps(TIME3))

# ---- 图 2：人物图谱（网络图）----
TOPN = 15
top_set = set(s["top_chars"][:TOPN])
# 总提及
tot = {c: sum(v) for c, v in s["per_chap_char"].items()}
GRAPH_NODES = []
for c in s["top_chars"][:TOPN]:
    val = tot.get(c, 0)
    GRAPH_NODES.append({"name": c, "size": round(14 + math.sqrt(val) * 0.85), "val": val})
GRAPH_EDGES = []
for e in s["edges"]:
    if e["a"] in top_set and e["b"] in top_set:
        GRAPH_EDGES.append([e["a"], e["b"], e["w"]])
# 计算每节点直接关系数（点击详情用）
deg_map = {}
for l in GRAPH_EDGES:
    deg_map[l[0]] = deg_map.get(l[0], 0) + 1
    deg_map[l[1]] = deg_map.get(l[1], 0) + 1
for n in GRAPH_NODES:
    n["deg"] = deg_map.get(n["name"], 0)
g_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n"
    "  var NODES=%s, LINKS=%s;\n  return {\n"
    "    title:{text:'人物图谱（Top%d 角色关系网络）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    tooltip:{trigger:'item',formatter:function(p){ if(p.dataType==='edge') return p.data.source+' — '+p.data.target+'：共现 '+p.data.value; return '<b>'+p.data.name+'</b><br/>总提及：'+p.data.value; }},\n"
    "    series:[{type:'graph',layout:'force',roam:true,draggable:true,\n"
    "      data:NODES.map(function(n){return {name:n.name,symbolSize:n.size,value:n.val,deg:n.deg,\n"
    "        itemStyle:{color:palette[0],borderColor:palette[1],borderWidth:1},\n"
    "        label:{show:true,color:vars.ink,fontSize:11}}; }),\n"
    "      links:LINKS.map(function(l){return {source:l[0],target:l[1],value:l[2],\n"
    "        lineStyle:{width:Math.min(6,l[2]/18),opacity:0.32,color:vars.lineStrong}}; }),\n"
    "      emphasis:{focus:'adjacency'},\n"
    "      force:{repulsion:200,edgeLength:[50,140],gravity:0.08},\n"
    "      lineStyle:{color:vars.lineStrong,opacity:0.32}}],\n"
    "    animationDurationUpdate:420\n  };\n}"
) % (json.dumps(GRAPH_NODES, ensure_ascii=False), json.dumps(GRAPH_EDGES, ensure_ascii=False), TOPN)

# ---- 图 4：空间谱系（坐标散点）----
SCALE = tc["scale"]
POS = tc["pos"]
TC_NODES = tc["nodes"]
TC_DATA = [{"name": n, "value": [round(POS[n][0] * SCALE, 1), round(POS[n][1] * SCALE, 1)]} for n in TC_NODES]
tc_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  var DATA=%s;\n  return {\n"
    "    title:{text:'空间谱系（基于文本坐标嵌入的相对位置）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:40,right:40,top:48,bottom:40,containLabel:true},\n"
    "    tooltip:{trigger:'item',formatter:function(p){return '<b>'+p.data.name+'</b><br/>相对坐标 ('+p.data.value[0]+', '+p.data.value[1]+')';}},\n"
    "    xAxis:{type:'value',name:'X',scale:true,axisLabel:{color:vars.muted},splitLine:{lineStyle:{color:vars.line}}},\n"
    "    yAxis:{type:'value',name:'Y',scale:true,axisLabel:{color:vars.muted},splitLine:{lineStyle:{color:vars.line}}},\n"
    "    series:[{type:'scatter',data:DATA,symbolSize:13,\n"
    "      itemStyle:{color:palette[1],opacity:0.82,borderColor:vars.surface,borderWidth:1},\n"
    "      label:{show:true,position:'right',color:vars.ink,fontSize:11},\n"
    "      emphasis:{focus:'self'}}],\n"
    "    animationDurationUpdate:420\n  };\n}"
) % (json.dumps(TC_DATA, ensure_ascii=False),)

cards = [
    ("一、文本概况与结构", "一、文本概况与结构（交互式动态）", "rp_chars", c1_opt, N, 420,
     "交互/动态：悬停看逐章字数 · 拖动缩放 · 「播放时间轴」逐章推进 · 「模拟实时数据流」演示平滑重绘。"),
    ("二、人物图谱", "二、人物图谱（交互式网络）", "rp_graph", g_opt, len(GRAPH_NODES), 480,
     "交互：拖动节点 · 滚轮缩放/平移 · 悬停看总提及与共现 · 点击节点高亮邻接并查看详情。"),
    ("三、时间轴与叙事时序", "三、时间轴与叙事时序（交互式动态）", "rp_time", c3_opt, N, 420,
     "交互/动态：悬停看逐章时序密度 · 拖动缩放 · 「播放时间轴」逐章推进 · 「模拟实时数据流」。"),
    ("四、空间谱系", "四、空间谱系（交互式坐标）", "rp_space", tc_opt, len(TC_DATA), 460,
     "交互：滚轮缩放/拖动平移 · 悬停看相对坐标 · 点击地点高亮并查看坐标。"),
]
charts = [("rp_chars", c1_opt, "both", N),
          ("rp_graph", g_opt, "none", len(GRAPH_NODES)),
          ("rp_time", c3_opt, "both", N),
          ("rp_space", tc_opt, "none", len(TC_DATA))]

# 点击回调：网络图（节点详情 + 邻接高亮）、空间散点（坐标详情）
GRAPH_ONCLICK = (
    "var det=document.getElementById('rp_graph_detail'); if(!det) return; "
    "if(p.dataType==='node'){ det.hidden=false; det.innerHTML='<b>'+p.data.name+'</b><br/>总提及 '+p.data.value+' · 直接关系 '+p.data.deg+' 条'; chart.dispatchAction({type:'focusNodeAdjacency',seriesIndex:0,dataIndex:p.dataIndex}); } "
    "else if(p.dataType==='edge'){ det.hidden=false; det.innerHTML='<b>'+p.data.source+' — '+p.data.target+'</b><br/>共现 '+p.data.value; } "
    "else { det.hidden=true; }"
)
SPACE_ONCLICK = (
    "var det=document.getElementById('rp_space_detail'); if(!det) return; "
    "if(p.data && p.data.name){ det.hidden=false; det.innerHTML='<b>'+p.data.name+'</b><br/>相对坐标 ('+p.data.value[0]+', '+p.data.value[1]+')'; } "
    "else { det.hidden=true; }"
)

with io.open(HTML, "r", encoding="utf-8") as f:
    html = f.read()
for old, new, cid, opt, n, h, hint in cards:
    card = C.card(new, cid, ("both" if cid in ("rp_chars", "rp_time") else "none"), n, hint, height=h)
    if cid == "rp_graph":
        card = card.replace("</div>\n<!--WZ-CHART-BLOCK-END-->",
                            '  <div id="rp_graph_detail" class="wz-detail" hidden></div>\n</div>\n<!--WZ-CHART-BLOCK-END-->')
    if cid == "rp_space":
        card = card.replace("</div>\n<!--WZ-CHART-BLOCK-END-->",
                            '  <div id="rp_space_detail" class="wz-detail" hidden></div>\n</div>\n<!--WZ-CHART-BLOCK-END-->')
    html = C.replace_heading_block(html, old, new, card)
html = C.inject_script(html, C.bundle(charts, onclick={"rp_graph": GRAPH_ONCLICK, "rp_space": SPACE_ONCLICK}))

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("[完成] 分析报告 → ECharts 交互式（字数/时序 时间轴+实时流；人物网络图；空间坐标散点）")
print("  字数/时序 各 %d 章 · 网络图节点 %d / 边 %d · 空间节点 %d" % (N, len(GRAPH_NODES), len(GRAPH_EDGES), len(TC_DATA)))
