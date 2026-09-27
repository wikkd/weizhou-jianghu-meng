# -*- coding: utf-8 -*-
"""就地升级《章节标签量化看板》报告：将 6 个静态 SVG 卡片替换为 ECharts 交互式图表。
  一、章节类型分布（柱）· 二、情节演进（时间层色带+战斗强度走势，时间轴+实时流）·
  三、感情线分布（柱）· 四、地点热度 Top15（柱）· 五、人物出场热度 Top20（柱）·
  六、战斗强度分布（柱）
数据取自已验证的 chapter_data/all_tags.json（59 章逐章标注）。
"""
import os, io, json, collections
import _chartlib as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_章节标签量化看板.html")
TAGS = os.path.join(ROOT, "数据", "chapter_data", "all_tags.json")
tags = C.load_json(TAGS)
N = len(tags)

def counter(field):
    c = collections.Counter()
    for e in tags:
        v = e.get(field)
        if isinstance(v, list):
            for x in v: c[x] += 1
        elif v is not None:
            c[v] += 1
    return c

CH = [e["chapter"] for e in tags]
CI = [e["combat_intensity"] for e in tags]
TL = [e["time_layer"] for e in tags]

# ---- 图 2：情节演进（时间层色带 + 战斗强度走势） TIME-SERIES ----
# 计算时间层连续区段
seen = []
runs = []
for i, tl in enumerate(TL):
    if tl not in seen: seen.append(tl)
    li = seen.index(tl)
    if runs and runs[-1][2] == tl:
        runs[-1][1] = CH[i]
    else:
        runs.append([CH[i], CH[i], tl, li])
TIME_RUNS = [[r[0], r[1], r[3]] for r in runs]   # [start,end,layerIdx]
dash_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n"
    "  var CH=%s, CI=%s, TL=%s, RUNS=%s;\n"
    "  var areaColors=[palette[0],palette[1],palette[2],palette[3],palette[4],'#9aa7b8','#b0a08c'];\n"
    "  var markAreaData=RUNS.map(function(r){return [{xAxis:r[0]},{xAxis:r[1],itemStyle:{color:areaColors[r[2]],opacity:0.12}}];});\n"
    "  return {\n"
    "    title:{text:'情节演进：时间层色带 + 战斗强度走势',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:54,right:40,top:48,bottom:64,containLabel:true},\n"
    "    tooltip:{trigger:'axis',formatter:function(ps){var i=ps[0].dataIndex;return '第 '+CH[i]+' 章 · '+TL[i]+'<br/>战斗强度：<b>'+CI[i]+'</b>';}},\n"
    "    xAxis:{type:'category',data:CH,name:'章',nameGap:26},\n"
    "    yAxis:{type:'value',name:'战斗强度',min:0,max:3,interval:1},\n"
    "    series:[{name:'战斗强度',type:'line',step:'middle',smooth:false,data:CI,\n"
    "      lineStyle:{width:2.4,color:palette[1]},itemStyle:{color:palette[1]},\n"
    "      markArea:{silent:true,data:markAreaData},\n"
    "      markLine:{silent:true,symbol:'none',data:[{yAxis:1}],lineStyle:{type:'dotted',color:vars.muted},label:{formatter:'阈值 1',color:vars.muted}},\n"
    "      emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(CH), json.dumps(CI), json.dumps(TL), json.dumps(TIME_RUNS))

# ---- 图 1：章节类型分布（柱）----
ct_c = counter("chapter_type")
CT = [k for k, _ in ct_c.most_common()]
CTV = [ct_c[k] for k in CT]
ct_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'章节类型分布（chapter_type，多标签累计）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:54,right:30,top:48,bottom:88,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'category',data:%s,axisLabel:{color:vars.muted,interval:0,rotate:30,fontSize:11}},\n"
    "    yAxis:{type:'value',name:'出现章数'},\n"
    "    series:[{type:'bar',data:%s,barWidth:'52%%',itemStyle:{color:palette[0],borderRadius:[4,4,0,0]},\n"
    "      label:{show:true,position:'top',color:vars.muted,fontSize:10},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(CT, ensure_ascii=False), json.dumps(CTV))

# ---- 图 3：感情线分布（柱）----
emo_c = counter("emotion_line")
EMO = [k for k, _ in emo_c.most_common()]
EMOV = [emo_c[k] for k in EMO]
emo_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'感情线分布（emotion_line）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:54,right:30,top:48,bottom:64,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'category',data:%s,axisLabel:{color:vars.muted,interval:0,rotate:18,fontSize:11}},\n"
    "    yAxis:{type:'value',name:'章数'},\n"
    "    series:[{type:'bar',data:%s,barWidth:'52%%',itemStyle:{color:palette[2],borderRadius:[4,4,0,0]},\n"
    "      label:{show:true,position:'top',color:vars.muted},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(EMO, ensure_ascii=False), json.dumps(EMOV))

# ---- 图 4：地点热度 Top15 ----
loc_c = collections.Counter()
for e in tags:
    for l in e.get("main_locations", []):
        loc_c[l] += 1
LOC = loc_c.most_common(15)
LOCW = [w for w, _ in LOC][::-1]
LOCV = [v for _, v in LOC][::-1]
loc_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'地点热度 Top15（main_locations 出现章数）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:90,right:48,top:48,bottom:40,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'value',name:'出现章数'},\n"
    "    yAxis:{type:'category',data:%s,axisLabel:{color:vars.muted,fontSize:11}},\n"
    "    series:[{type:'bar',data:%s,barWidth:'62%%',itemStyle:{color:palette[0],borderRadius:[0,4,4,0]},\n"
    "      label:{show:true,position:'right',color:vars.muted},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(LOCW, ensure_ascii=False), json.dumps(LOCV))

# ---- 图 5：人物出场热度 Top20 ----
ch_c = collections.Counter()
for e in tags:
    for c in e.get("characters_present", []):
        ch_c[c] += 1
CHP = ch_c.most_common(20)
CHPW = [w for w, _ in CHP][::-1]
CHPV = [v for _, v in CHP][::-1]
chp_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'人物出场热度 Top20（characters_present 出现章数）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:90,right:48,top:48,bottom:40,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'value',name:'出场章数'},\n"
    "    yAxis:{type:'category',data:%s,axisLabel:{color:vars.muted,fontSize:11}},\n"
    "    series:[{type:'bar',data:%s,barWidth:'62%%',itemStyle:{color:palette[1],borderRadius:[0,4,4,0]},\n"
    "      label:{show:true,position:'right',color:vars.muted},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(CHPW, ensure_ascii=False), json.dumps(CHPV))

# ---- 图 6：战斗强度分布（柱）----
ci_c = collections.Counter(CI)
CIL = [0, 1, 2, 3]
CIV = [ci_c.get(k, 0) for k in CIL]
civ_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'战斗强度分布（combat_intensity 0–3）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:54,right:30,top:48,bottom:50,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'category',data:['0 无战事','1 轻微','2 中等','3 激烈'],axisLabel:{color:vars.muted}},\n"
    "    yAxis:{type:'value',name:'章数'},\n"
    "    series:[{type:'bar',data:%s,barWidth:'46%%',itemStyle:{color:palette[1],borderRadius:[4,4,0,0]},\n"
    "      label:{show:true,position:'top',color:vars.muted},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(CIV))

cards = [
    ("一、章节类型分布", "一、章节类型分布（交互式）", "db_ct", ct_opt, len(CT), 380, "交互：悬停看章数 · 拖动缩放。"),
    ("二、情节演进", "二、情节演进（交互式动态）", "db_dash", dash_opt, N, 440,
     "交互/动态：悬停看章+时间层+战斗强度 · 拖动缩放 · 「播放时间轴」逐章推进（色带即时间层）· 「模拟实时数据流」演示平滑重绘。"),
    ("三、感情线分布", "三、感情线分布（交互式）", "db_emo", emo_opt, len(EMO), 380, "交互：悬停看章数 · 拖动缩放。"),
    ("四、地点热度", "四、地点热度 Top15（交互式）", "db_loc", loc_opt, len(LOCW), 460, "交互：悬停看出现章数 · 拖动缩放。"),
    ("五、人物出场热度", "五、人物出场热度 Top20（交互式）", "db_chp", chp_opt, len(CHPW), 480, "交互：悬停看出场章数 · 拖动缩放。"),
    ("六、战斗强度分布", "六、战斗强度分布（交互式）", "db_civ", civ_opt, 4, 360, "交互：悬停看章数。"),
]
charts = [("db_ct", ct_opt, "none", len(CT)),
          ("db_dash", dash_opt, "both", N),
          ("db_emo", emo_opt, "none", len(EMO)),
          ("db_loc", loc_opt, "none", len(LOCW)),
          ("db_chp", chp_opt, "none", len(CHPW)),
          ("db_civ", civ_opt, "none", 4)]

with io.open(HTML, "r", encoding="utf-8") as f:
    html = f.read()
for old, new, cid, opt, n, h, hint in cards:
    card = C.card(new, cid, ("both" if cid == "db_dash" else "none"), n, hint, height=h)
    html = C.replace_heading_block(html, old, new, card)
html = C.inject_script(html, C.bundle(charts))

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("[完成] 章节标签量化看板 → ECharts 交互式（6 图，db_dash 为时间轴+实时流）")
print("  章节类型 %d类 · 感情线 %d类 · 地点Top%d · 人物Top%d · 时间层色带 %d 段" % (len(CT), len(EMO), len(LOCW), len(CHPW), len(TIME_RUNS)))
