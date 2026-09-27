# -*- coding: utf-8 -*-
"""就地升级《人物关系网络》报告：将 1 个静态 SVG 网络图替换为 ECharts 力导向交互网络图。
展示出场频次 Top55 的核心人物共现网络（按社区着色），支持拖动/缩放/高亮邻接。
数据取自已验证的 character_network.json。
"""
import os, io, json, math
import _chartlib as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_人物关系网络.html")
JSON = os.path.join(ROOT, "数据", "analysis", "character_network.json")
cn = C.load_json(JSON)

TOPN = 55
nodes_sorted = sorted(cn["nodes"], key=lambda n: n["appearances"], reverse=True)
top_names = set(n["name"] for n in nodes_sorted[:TOPN])
NODES = []
for n in nodes_sorted[:TOPN]:
    ap = n["appearances"]
    NODES.append({"name": n["name"], "size": round(10 + math.sqrt(ap) * 0.85),
                  "val": ap, "comm": int(n["community"])})
LINKS = []
for e in cn["edges"]:
    if e["source"] in top_names and e["target"] in top_names:
        LINKS.append([e["source"], e["target"], e["weight"]])

# 计算每节点直接共现度（用于点击详情）
deg_map = {}
for l in LINKS:
    deg_map[l[0]] = deg_map.get(l[0], 0) + 1
    deg_map[l[1]] = deg_map.get(l[1], 0) + 1
for n in NODES:
    n["deg"] = deg_map.get(n["name"], 0)

opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n"
    "  var NODES=%s, LINKS=%s;\n  return {\n"
    "    title:{text:'人物共现网络（核心 Top%d，按社区着色）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    tooltip:{trigger:'item',formatter:function(p){ if(p.dataType==='edge') return p.data.source+' — '+p.data.target+'：共现 '+p.data.value; return '<b>'+p.data.name+'</b><br/>出场：'+p.data.value; }},\n"
    "    legend:{show:false},\n"
    "    series:[{type:'graph',layout:'force',roam:true,draggable:true,\n"
    "      data:NODES.map(function(n){return {name:n.name,symbolSize:n.size,value:n.val,community:n.comm,deg:n.deg,\n"
    "        itemStyle:{color:palette[n.comm%%palette.length],borderColor:vars.surface,borderWidth:1},\n"
    "        label:{show:true,color:vars.ink,fontSize:10,position:'right'}}; }),\n"
    "      links:LINKS.map(function(l){return {source:l[0],target:l[1],value:l[2],\n"
    "        lineStyle:{width:Math.min(5,l[2]/12),opacity:0.28,color:vars.lineStrong}}; }),\n"
    "      emphasis:{focus:'adjacency'},\n"
    "      force:{repulsion:160,edgeLength:[40,120],gravity:0.06},\n"
    "      lineStyle:{color:vars.lineStrong,opacity:0.28}}],\n"
    "    animationDurationUpdate:420\n  };\n}"
) % (json.dumps(NODES, ensure_ascii=False), json.dumps(LINKS, ensure_ascii=False), TOPN)

hint = "交互：拖动节点重排 · 滚轮缩放/平移 · 悬停看出场与共现 · 点击节点高亮其邻接关系并查看详情。"
card = C.card("二、人物共现网络图（交互式）", "net", "none", len(NODES), hint, height=560)
# 点击详情面板（置于卡片内，随图表换肤）
card = card.replace("</div>\n<!--WZ-CHART-BLOCK-END-->",
                    '  <div id="net_detail" class="wz-detail" hidden></div>\n</div>\n<!--WZ-CHART-BLOCK-END-->')
NET_ONCLICK = (
    "var det=document.getElementById('net_detail'); if(!det) return; "
    "if(p.dataType==='node'){ det.hidden=false; det.innerHTML='<b>'+p.data.name+'</b>（社区 '+p.data.community+'）<br/>出场 '+p.data.value+' 次 · 直接共现 '+p.data.deg+' 条'; chart.dispatchAction({type:'focusNodeAdjacency',seriesIndex:0,dataIndex:p.dataIndex}); } "
    "else if(p.dataType==='edge'){ det.hidden=false; det.innerHTML='<b>'+p.data.source+' — '+p.data.target+'</b><br/>共现强度 '+p.data.value; } "
    "else { det.hidden=true; }"
)
with io.open(HTML, "r", encoding="utf-8") as f:
    html = f.read()
html = C.replace_heading_block(html, "二、人物共现网络图", "二、人物共现网络图（交互式）", card)
html = C.inject_script(html, C.bundle([("net", opt, "none", len(NODES))], onclick={"net": NET_ONCLICK}))
with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("[完成] 人物关系网络 → ECharts 力导向交互网络（核心 Top%d，边 %d）" % (TOPN, len(LINKS)))
