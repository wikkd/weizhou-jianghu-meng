# -*- coding: utf-8 -*-
"""就地升级空间类报告的两张静态 SVG 地图为 ECharts 交互式坐标散点：
  · 空间地点分析报告 · 三、相对空间位置图  ← spatial_data.json（像素坐标，y 轴翻转保持「上北」）
  · 地理位置关系图 · 一、地理位置关系图     ← text_coords.json（文本坐标嵌入，相对位置）
均支持滚轮缩放/平移、悬停看坐标、点击高亮；controls=none（地图为静态空间关系，动态重绘无意义）。

本次增强：为「地理位置关系图」叠加【地理要素标注图层】——
  山地 / 河流 / 湖泊 / 道路 四类自然与人文要素，使用 path:// SVG 图标表示，
  每项标注名称 + 关键属性，底部图例可逐类显隐（不遮挡主体地点关系）。
"""
import os, io, json
import _chartlib as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- 空间地点分析报告 ----------
SP = os.path.join(ROOT, "数据", "spatial_data.json")
sp = C.load_json(SP)
SP_NODES = [{"name": n, "value": [c[0], c[1]]} for n, c in sp["nodes"].items()]
sp_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  var DATA=%s;\n  return {\n"
    "    title:{text:'相对空间位置图（基于 spatial_data 像素坐标，上北）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:14}},\n"
    "    grid:{left:50,right:30,top:46,bottom:46,containLabel:true},\n"
    "    tooltip:{trigger:'item',formatter:function(p){return '<b>'+p.data.name+'</b><br/>坐标 ('+p.data.value[0]+', '+p.data.value[1]+')';}},\n"
    "    xAxis:{type:'value',name:'X(px)',scale:true,axisLabel:{color:vars.muted},splitLine:{lineStyle:{color:vars.line}}},\n"
    "    yAxis:{type:'value',name:'Y(px)',scale:true,inverse:true,axisLabel:{color:vars.muted},splitLine:{lineStyle:{color:vars.line}}},\n"
    "    series:[{type:'scatter',data:DATA,symbolSize:12,\n"
    "      itemStyle:{color:palette[0],opacity:0.82,borderColor:vars.surface,borderWidth:1},\n"
    "      label:{show:true,position:'right',color:vars.ink,fontSize:11},\n"
    "      emphasis:{focus:'self'}}],\n"
    "    animationDurationUpdate:420\n  };\n}"
) % (json.dumps(SP_NODES, ensure_ascii=False),)

# ---------- 地理位置关系图（优化：关系连线 + 方位罗盘 + 片区筛选 + 缩放 + 地理要素标注） ----------
TC = os.path.join(ROOT, "数据", "text_coords.json")
tc = C.load_json(TC)
SP = os.path.join(ROOT, "数据", "spatial_data.json")
sp = C.load_json(SP)
POS = tc["pos"]; SCALE = tc["scale"]; NODE_NAMES = tc["nodes"]
ALIAS = {"京": "京城"}
def _resolve(n): return ALIAS.get(n, n)
# 由 spatial_data 距离矩阵构建「两地点都存在」的关系边
_raw_edges = []; _seen = set()
ki = {k: i for i, k in enumerate(sp["key"])}
for i, a in enumerate(sp["key"]):
    for j, b in enumerate(sp["key"]):
        if i < j:
            ra, rb = _resolve(a), _resolve(b)
            if ra in POS and rb in POS:
                c = sp["matrix"][i][j]
                li = c.get("li", 0); km = c.get("km", 0); days = c.get("days", 0)
                if li > 0:
                    key = tuple(sorted([ra, rb]))
                    if key not in _seen:
                        _seen.add(key); _raw_edges.append([ra, rb, li, km, days])
# 最小生成树（连通主干） + 补 5 条最长官道
_nodes_in = set()
for e in _raw_edges: _nodes_in.update([e[0], e[1]])
_parent = {n: n for n in _nodes_in}
def _find(x):
    while _parent[x] != x:
        _parent[x] = _parent[_parent[x]]; x = _parent[x]
    return x
def _union(a, b): _parent[_find(a)] = _find(b)
_mst = []
for e in sorted(_raw_edges, key=lambda e: e[2]):
    if _find(e[0]) != _find(e[1]):
        _union(e[0], e[1]); _mst.append(e)
_top = sorted(_raw_edges, key=lambda e: -e[2])[:5]
_mstk = set(tuple(sorted([e[0], e[1]])) for e in _mst)
_all_edges = _mst + [e for e in _top if tuple(sorted([e[0], e[1]])) not in _mstk]
_deg = {n: 0 for n in NODE_NAMES}
for e in _all_edges: _deg[e[0]] += 1; _deg[e[1]] += 1
_jx, _jy = POS["京城"]
def _region(n):
    if n == "京城": return "京畿"
    dx = POS[n][0] - _jx; dy = POS[n][1] - _jy
    if dx >= 0 and dy >= 0: return "东北"
    if dx >= 0 and dy < 0: return "东南"
    if dx < 0 and dy < 0: return "西南"
    return "西北"
REGIONS = ["京畿", "东北", "东南", "西南", "西北"]
graph_nodes = []
for n in NODE_NAMES:
    x = round(POS[n][0] * SCALE, 1); y = round(POS[n][1] * SCALE, 1)
    graph_nodes.append({"name": n, "value": [x, y], "region": _region(n), "deg": _deg[n]})
graph_edges = [{"source": e[0], "target": e[1], "li": e[2], "km": e[3], "days": round(e[4], 1)} for e in _all_edges]
TC_NODES = graph_nodes

# ===== 地理要素标注数据 =====
GF = os.path.join(ROOT, "数据", "geo_features.json")
gf = C.load_json(GF)
FTYPES = gf["meta"]["types"]                       # ['山地','河流','湖泊','道路']
FCOLORS = {t: gf["type_style"][t]["color"] for t in FTYPES}
ICONS = {
    "山地": "path://M2,20 L8,9 L12,15 L16,6 L22,20 Z",
    "河流": "path://M12,3 C12,3 5,12 5,16 A7,7 0 0 0 19,16 C19,12 12,3 12,3 Z",
    "湖泊": "path://M3,14 C3,11 7,9.5 12,9.5 C17,9.5 21,11 21,14 C21,17 17,18.5 12,18.5 C7,18.5 3,17 3,14 Z",
    "道路": "path://M6,3 L6,21 L8,21 L8,13 L19,17 L19,5 L8,9 L8,3 Z",
}
feat_data = []
for f in gf["features"]:
    a = POS[f["anchor"]]
    fx = round((a[0] + f["dx"]) * SCALE, 1)
    fy = round((a[1] + f["dy"]) * SCALE, 1)
    feat_data.append({"name": f["name"], "type": f["type"], "x": fx, "y": fy, "attr": f["attr"]})
FEAT_JSON = json.dumps(feat_data, ensure_ascii=False)
FTYPES_JSON = json.dumps(FTYPES, ensure_ascii=False)
FCOLORS_JSON = json.dumps(FCOLORS, ensure_ascii=False)
ICONS_JSON = json.dumps(ICONS, ensure_ascii=False)

tc_opt = (
    """function(vars){
  var palette=WZ.buildTheme().color;
  var NODES=%s;
  var EDGES=%s;
  var REGIONS=%s;
  var FEATURES=%s;
  var FTYPES=%s;
  var FCOLORS=%s;
  var ICONS=%s;
  var categories=REGIONS.map(function(r,i){return {name:r, itemStyle:{color:palette[i%%palette.length]}};});
  var nodes=NODES.map(function(d){
    var isCap=d.name==='京城';
    return {name:d.name, value:d.value, category:REGIONS.indexOf(d.region), deg:d.deg,
      symbolSize: isCap?22:(10+d.deg*3),
      itemStyle: isCap?{color:'#c8a24a',borderColor:vars.ink,borderWidth:1.6}:{},
      label:{show:true,position:'right',color:vars.ink,fontSize:isCap?12:11,fontWeight:isCap?'bold':'normal'}};
  });
  var edges=EDGES.map(function(e){
    var w=e.li>500?3:(e.li>200?2:1.2);
    return {source:e.source,target:e.target,li:e.li,km:e.km,days:e.days,
      lineStyle:{width:w,opacity:0.42,curveness:0.12,color:vars.line}};
  });
  var featSeries=FTYPES.map(function(t){
    var data=FEATURES.filter(function(f){return f.type===t;}).map(function(f){
      return {name:f.name, value:[f.x,f.y], ftype:f.type, attr:f.attr,
        symbol:ICONS[t], symbolSize:16,
        itemStyle:{color:FCOLORS[t], opacity:0.92, borderColor:'#fff', borderWidth:1.4},
        label:{show:true, position:'top', distance:6, color:vars.ink, fontSize:10.5, fontWeight:'bold'}};
    });
    return {name:t, type:'scatter', coordinateSystem:'cartesian2d', data:data, z:2,
      legendHoverLink:true,
      emphasis:{scale:1.35, itemStyle:{borderColor:vars.ink, borderWidth:2}},
      labelLayout:{hideOverlap:true}};
  });
  return {
    title:{text:'地理位置关系图（关系连线 + 片区分布 + 地理要素标注）',
      subtext:'上北下南 · 左西右东 · 坐标为文本相对位置（非绝对地理投影）',
      left:'center',top:6,textStyle:{color:vars.ink,fontSize:14},subtextStyle:{color:vars.muted,fontSize:11}},
    tooltip:{trigger:'item',formatter:function(p){
      if(p.seriesName && FTYPES.indexOf(p.seriesName)>=0){
        var f=p.data; var h='<b>'+f.name+'</b> <span style=\\"color:'+FCOLORS[f.ftype]+'\\">●</span> '+f.ftype+'<br/>';
        for(var k in f.attr){ h+= k+'：'+f.attr[k]+'<br/>'; }
        return h;
      }
      if(p.dataType==='edge'){return p.data.source+' — '+p.data.target+'<br/>'+p.data.li+' 里 / '+p.data.km+' km / '+p.data.days+' 天';}
      var d=p.data; var reg=REGIONS[d.category];
      return '<b>'+d.name+'</b>'+(d.name==='京城'?'（京城）':'')+'<br/>片区：'+reg+'<br/>相对坐标 ('+d.value[0]+', '+d.value[1]+')<br/>关系连线：'+d.deg+' 条';
    }},
    legend:[
      {data:REGIONS,top:36,left:'center',itemWidth:12,itemHeight:12,textStyle:{color:vars.muted,fontSize:11}},
      {data:FTYPES,bottom:8,left:'center',itemWidth:18,itemHeight:14,itemGap:16,
        textStyle:{color:vars.muted,fontSize:11},selectedMode:true}
    ],
    grid:{left:54,right:34,top:70,bottom:66,containLabel:true},
    xAxis:{type:'value',name:'相对经度 X',scale:true,axisLabel:{color:vars.muted},splitLine:{lineStyle:{color:vars.line}}},
    yAxis:{type:'value',name:'相对纬度 Y',scale:true,axisLabel:{color:vars.muted},splitLine:{lineStyle:{color:vars.line}}},
    dataZoom:[{type:'inside',xAxisIndex:0,filterMode:'none',moveOnMouseMove:true,moveOnMouseWheel:false},
              {type:'inside',yAxisIndex:0,filterMode:'none',moveOnMouseMove:true,moveOnMouseWheel:false}],
    graphic:[{type:'group',right:26,top:78,children:[
      {type:'circle',shape:{cx:0,cy:0,r:20},style:{fill:'rgba(127,127,127,0.04)',stroke:vars.line,lineWidth:1}},
      {type:'path',shape:{path:'M0,-15 L6,9 L0,3 L-6,9 Z'},style:{fill:vars.accent}},
      {type:'text',style:{text:'北',x:-7,y:-30,fill:vars.muted,font:'bold 12px sans-serif'}},
      {type:'text',style:{text:'南',x:-7,y:24,fill:vars.muted,font:'12px sans-serif'}},
      {type:'text',style:{text:'东',x:24,y:-4,fill:vars.muted,font:'12px sans-serif'}},
      {type:'text',style:{text:'西',x:-30,y:-4,fill:vars.muted,font:'12px sans-serif'}}
    ]}],
    series: featSeries.concat([{type:'graph',coordinateSystem:'cartesian2d',roam:false, z:4,
      data:nodes, links:edges, categories:categories,
      labelLayout:{hideOverlap:true},
      edgeLabel:{show:false},
      emphasis:{focus:'adjacency',edgeLabel:{show:true,formatter:function(p){return p.data.li+' 里';},color:vars.ink,fontWeight:'bold'}},
      lineStyle:{opacity:0.42},
      animationDurationUpdate:480,animationEasingUpdate:'cubicInOut'}])
  };
}"""
) % (json.dumps(graph_nodes, ensure_ascii=False),
     json.dumps(graph_edges, ensure_ascii=False),
     json.dumps(REGIONS, ensure_ascii=False),
     FEAT_JSON, FTYPES_JSON, FCOLORS_JSON, ICONS_JSON)

# ---- 写入 空间地点分析报告 ----
H1 = os.path.join(ROOT, "产物", "苇舟江湖梦_空间地点分析报告.html")
hint1 = "交互：滚轮缩放/平移 · 悬停看坐标 · 点击地点高亮并查看坐标。y 轴已翻转以保持「上北下南」。"
card1 = C.card("三、相对空间位置图（交互式）", "sp_map", "none", len(SP_NODES), hint1, height=520)
card1 = card1.replace("</div>\n<!--WZ-CHART-BLOCK-END-->",
                       '  <div id="sp_map_detail" class="wz-detail" hidden></div>\n</div>\n<!--WZ-CHART-BLOCK-END-->')
SP_ONCLICK = (
    "var det=document.getElementById('sp_map_detail'); if(!det) return; "
    "if(p.data && p.data.name){ det.hidden=false; det.innerHTML='<b>'+p.data.name+'</b><br/>坐标 ('+p.data.value[0]+', '+p.data.value[1]+')'; } "
    "else { det.hidden=true; }"
)
with io.open(H1, "r", encoding="utf-8") as f:
    h1 = f.read()
h1 = C.replace_heading_block(h1, "三、相对空间位置图", "三、相对空间位置图（交互式）", card1)
h1 = C.inject_script(h1, C.bundle([("sp_map", sp_opt, "none", len(SP_NODES))], onclick={"sp_map": SP_ONCLICK}))
with io.open(H1, "w", encoding="utf-8") as f:
    f.write(h1)

# ---- 写入 地理位置关系图 ----
H2 = os.path.join(ROOT, "产物", "苇舟江湖梦_地理位置关系图.html")
hint2 = ("交互：滚轮/双指缩放 · 拖动平移 · 悬停看详情 · 点击节点/要素高亮并查看属性 · "
         "顶部图例筛选片区、底部图例显隐地理要素（⛰山地 ⌁河流 ◍湖泊 ⌁道路）。"
         "上北下南、左西右东；连线为关系主干（非几何距离），要素为叙事相对位置标注。")
card2 = C.card("一、地理位置关系图（交互式）", "tc_map", "none", len(TC_NODES), hint2, height=580)
card2 = card2.replace("</div>\n<!--WZ-CHART-BLOCK-END-->",
                       '  <div id="tc_map_detail" class="wz-detail" hidden></div>\n</div>\n<!--WZ-CHART-BLOCK-END-->')
TC_ONCLICK = (
    "var REGIONS=['京畿','东北','东南','西南','西北']; "
    "var FTYPES=['山地','河流','湖泊','道路']; "
    "var FCOLORS=%s; "
    "var det=document.getElementById('tc_map_detail'); if(!det) return; "
    "if(p.seriesName && FTYPES.indexOf(p.seriesName)>=0){ "
    "  var f=p.data; var html='<b>'+f.name+'</b> · '+f.ftype+'<br/>'; "
    "  for(var k in f.attr){ html+=k+'：'+f.attr[k]+'<br/>'; } "
    "  det.hidden=false; det.innerHTML=html; return; "
    "}"
    "if(p.data && p.data.name){ "
    "  var reg=REGIONS[p.data.category]; "
    "  var deg=(p.data.deg!=null)?p.data.deg:0; "
    "  det.hidden=false; "
    "  det.innerHTML='<b>'+p.data.name+'</b>'+(p.data.name==='京城'?'（京城）':'')"
    "+'<br/>片区：'+reg+'<br/>关系连线：'+deg+' 条<br/>相对坐标 ('+p.data.value[0]+', '+p.data.value[1]+')'; "
    "} else { det.hidden=true; }"
) % (FCOLORS_JSON,)
with io.open(H2, "r", encoding="utf-8") as f:
    h2 = f.read()
h2 = C.replace_heading_block(h2, "一、地理位置关系图", "一、地理位置关系图（交互式）", card2)
h2 = C.inject_script(h2, C.bundle([("tc_map", tc_opt, "none", len(TC_NODES))], onclick={"tc_map": TC_ONCLICK}))
with io.open(H2, "w", encoding="utf-8") as f:
    f.write(h2)

print("[完成] 空间类报告 → ECharts 交互式坐标散点（含地理要素标注图层）")
print("  空间地点分析报告(spatial_data) 节点 %d" % len(SP_NODES))
print("  地理位置关系图(text_coords) 节点 %d · 地理要素 %d（山地/河流/湖泊/道路）" % (len(TC_NODES), len(feat_data)))
