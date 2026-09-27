# -*- coding: utf-8 -*-
"""就地升级《时间节奏量化》报告：将 4 个静态 SVG 卡片替换为 ECharts 交互式柱状图。
  一、季节分布（归一四季）· 二、昼夜叙事节奏（夜/晨/昼）·
  三、相对时间密度（rel_time 高频时长表达 Top15）· 四、地名实体热度（ner_loc Top20）
数据取自已验证的 time_loc.json。
"""
import os, io, json, collections
import _chartlib as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_时间节奏量化.html")
JSON = os.path.join(ROOT, "数据", "time_loc.json")
tl = C.load_json(JSON)

def season_bucket(s):
    if "春" in s: return "春"
    if "夏" in s: return "夏"
    if "秋" in s: return "秋"
    if "冬" in s: return "冬"
    return "其他"

def tod_bucket(t):
    if t == "天色": return "昼"
    if any(k in t for k in ["夜", "黑", "深", "暮", "昏", "晚", "子", "灯", "夕"]): return "夜"
    if any(k in t for k in ["晨", "早", "黎", "晓", "明", "清", "破晓", "亮"]): return "晨"
    if any(k in t for k in ["午", "日", "阳"]): return "昼"
    return "其他"

season_c = collections.Counter(season_bucket(s) for s in tl["season"])
SEASON = ["春", "夏", "秋", "冬"]
SEASONV = [season_c.get(k, 0) for k in SEASON]
season_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'季节分布（season → 四季归一）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:54,right:30,top:48,bottom:50,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'category',data:%s,axisLabel:{color:vars.muted,fontSize:12}},\n"
    "    yAxis:{type:'value',name:'提及次数'},\n"
    "    series:[{type:'bar',data:%s,barWidth:'46%%',itemStyle:{color:palette[3],borderRadius:[4,4,0,0]},\n"
    "      label:{show:true,position:'top',color:vars.muted},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(SEASON, ensure_ascii=False), json.dumps(SEASONV))

tod_c = collections.Counter(tod_bucket(t) for t in tl["tod"])
TOD = ["夜", "晨", "昼"]
TODV = [tod_c.get(k, 0) for k in TOD]
tod_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'昼夜叙事节奏（tod → 夜/晨/昼）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:54,right:30,top:48,bottom:50,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'category',data:%s,axisLabel:{color:vars.muted,fontSize:12}},\n"
    "    yAxis:{type:'value',name:'提及次数'},\n"
    "    series:[{type:'bar',data:%s,barWidth:'46%%',itemStyle:{color:palette[1],borderRadius:[4,4,0,0]},\n"
    "      label:{show:true,position:'top',color:vars.muted},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(TOD, ensure_ascii=False), json.dumps(TODV))

rel = collections.Counter(tl["rel_time"]).most_common(15)
RELW = [w for w, _ in rel][::-1]
RELV = [v for _, v in rel][::-1]
rel_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'相对时间密度 Top15（rel_time 时长表达）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:96,right:48,top:48,bottom:40,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'value',name:'出现次数'},\n"
    "    yAxis:{type:'category',data:%s,axisLabel:{color:vars.muted,fontSize:11}},\n"
    "    series:[{type:'bar',data:%s,barWidth:'62%%',itemStyle:{color:palette[2],borderRadius:[0,4,4,0]},\n"
    "      label:{show:true,position:'right',color:vars.muted},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(RELW, ensure_ascii=False), json.dumps(RELV))

ner = tl["ner_loc"][:20]
NERW = [w for w, _ in ner][::-1]
NERV = [v for _, v in ner][::-1]
ner_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'地名实体热度 Top20（ner_loc）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:90,right:48,top:48,bottom:40,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'value',name:'出现次数'},\n"
    "    yAxis:{type:'category',data:%s,axisLabel:{color:vars.muted,fontSize:11}},\n"
    "    series:[{type:'bar',data:%s,barWidth:'62%%',itemStyle:{color:palette[0],borderRadius:[0,4,4,0]},\n"
    "      label:{show:true,position:'right',color:vars.muted},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(NERW, ensure_ascii=False), json.dumps(NERV))

cards = [
    ("一、季节分布", "一、季节分布（交互式）", "rh_season", season_opt, 4, 360, "交互：悬停看次数 · 点击图例。"),
    ("二、昼夜叙事节奏", "二、昼夜叙事节奏（交互式）", "rh_tod", tod_opt, 3, 360, "交互：悬停看次数。"),
    ("三、相对时间密度", "三、相对时间密度（交互式）", "rh_rel", rel_opt, 15, 460, "交互：悬停看出现次数 · 拖动缩放。"),
    ("四、命名实体地名清洗与热度", "四、地名实体热度 Top20（交互式）", "rh_ner", ner_opt, 20, 480, "交互：悬停看出现次数 · 拖动缩放。"),
]
charts = [("rh_season", season_opt, "none", 4),
          ("rh_tod", tod_opt, "none", 3),
          ("rh_rel", rel_opt, "none", 15),
          ("rh_ner", ner_opt, "none", 20)]

with io.open(HTML, "r", encoding="utf-8") as f:
    html = f.read()
for old, new, cid, opt, n, h, hint in cards:
    card = C.card(new, cid, "none", n, hint, height=h)
    html = C.replace_heading_block(html, old, new, card)
html = C.inject_script(html, C.bundle(charts))

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("[完成] 时间节奏量化 → ECharts 交互式（4 柱，controls=none）")
print("  季节 %s=%s · 昼夜 %s=%s · relTop%d · nerTop%d" % (SEASON, SEASONV, TOD, TODV, len(RELW), len(NERW)))
