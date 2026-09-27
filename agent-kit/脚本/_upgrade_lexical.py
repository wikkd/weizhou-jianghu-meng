# -*- coding: utf-8 -*-
"""就地升级《词汇计量》报告：将 2 个静态 SVG 卡片替换为 ECharts 交互式动态图表。
  1) 59 章 TTR 折线图（交互：悬停/缩放/筛选；动态：时间轴播放 + 实时数据流）
  2) 全本 Top20 关键词（交互：悬停/缩放/点击；横向柱状）
数据取自已验证的 lexical_stats.json；仅改写产物 HTML，不触碰源数据。
"""
import os, io, json
import _chartlib as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_词汇计量.html")
JSON = os.path.join(ROOT, "数据", "analysis", "lexical_stats.json")

d = C.load_json(JSON)
ttr = d["ttr"]                                   # [{chapter, ttr}]
top = d["top_words"][:20]                         # [{word, freq}]
CH = [c["chapter"] for c in ttr]
YS = [round(c["ttr"], 4) for c in ttr]
MEAN = round(float(d["meta"]["ttr_mean"]), 4)
WORDS = [w["word"] for w in top][::-1]            # 反转使最大值在顶部
FREQS = [w["freq"] for w in top][::-1]
N = len(CH)

# ---- 图 1：59 章 TTR 折线（时间轴 + 实时流）----
ttr_opt = (
    "function(vars){\n"
    "  var palette = WZ.buildTheme().color;\n"
    "  return {\n"
    "    title:{text:'59 章类符/形符比 (TTR)',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:56,right:56,top:48,bottom:64,containLabel:true},\n"
    "    tooltip:{trigger:'axis',valueFormatter:function(v){return (v==null)?'-':(+v).toFixed(4);}},\n"
    "    xAxis:{type:'category',data:%s,name:'章',nameGap:26},\n"
    "    yAxis:{type:'value',name:'TTR',min:0.55,max:0.90,splitNumber:7},\n"
    "    series:[{name:'TTR',type:'line',smooth:true,showSymbol:false,data:%s,\n"
    "      lineStyle:{width:2.4,color:palette[0]},itemStyle:{color:palette[0]},\n"
    "      areaStyle:{color:'rgba(44,93,138,0.08)'},\n"
    "      markLine:{silent:true,symbol:'none',data:[{yAxis:%s}],lineStyle:{type:'dashed',color:vars.muted},\n"
    "        label:{formatter:'均值 %s',color:vars.muted,position:'insideEndTop'}},\n"
    "      emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n"
    "  };\n"
    "}"
) % (json.dumps(CH, ensure_ascii=False), json.dumps(YS), repr(MEAN), repr(MEAN))

# ---- 图 2：Top20 关键词（横向柱状，交互为主）----
bar_opt = (
    "function(vars){\n"
    "  var palette = WZ.buildTheme().color;\n"
    "  return {\n"
    "    title:{text:'全本 Top20 关键词（实词词频）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:80,right:64,top:48,bottom:48,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'value',name:'词频'},\n"
    "    yAxis:{type:'category',data:%s,axisLabel:{color:vars.muted}},\n"
    "    series:[{name:'词频',type:'bar',data:%s,barWidth:'62%%',\n"
    "      itemStyle:{color:palette[0],borderRadius:[0,4,4,0]},\n"
    "      label:{show:true,position:'right',color:vars.muted,formatter:function(p){return p.value;}},\n"
    "      emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n"
    "  };\n"
    "}"
) % (json.dumps(WORDS, ensure_ascii=False), json.dumps(FREQS))

hint_ttr = "交互：悬停看逐章数值 · 拖动缩放(dataZoom) · 点击图例筛选 · 「播放时间轴」逐章演进 · 「模拟实时数据流」演示平滑重绘。"
hint_bar = "交互：悬停查看词频 · 拖动缩放 · 点击图例 · 点击柱体高亮该词在全本的分布。"

card_ttr = C.card("59 章 TTR 折线图（交互式动态图表）", "lex_ttr", "both", N, hint_ttr, height=420)
card_bar = C.card("全本 Top20 关键词（交互式）", "lex_bar", "none", 20, hint_bar, height=520)

with io.open(HTML, "r", encoding="utf-8") as f:
    html = f.read()

html = C.replace_heading_block(html, "59 章 TTR 折线图", "59 章 TTR 折线图（交互式动态图表）", card_ttr)
html = C.replace_heading_block(html, "全本 Top20 关键词", "全本 Top20 关键词（交互式）", card_bar)

script = C.bundle([
    ("lex_ttr", ttr_opt, "both", N),
    ("lex_bar", bar_opt, "none", 20),
])
html = C.inject_script(html, script)

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("[完成] 词汇计量 → ECharts 交互式（TTR 折线 controls=both；Top20 柱状 controls=none）")
print("  数据：%d 章 TTR · 均值 %.4f · Top20 词频 %s" % (N, MEAN, FREQS[:3]))
