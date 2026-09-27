# -*- coding: utf-8 -*-
"""就地升级《风格计量》报告：静态 SVG → ECharts 交互式动态折线。
逐章 平均句长 / 标点密度 / 对话占比 三线对照；时间轴播放 + 实时数据流。
"""
import os, io, json
import _chartlib as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_风格计量.html")
JSON = os.path.join(ROOT, "数据", "analysis", "stylometry.json")

d = C.load_json(JSON)
ch = d["chapters"]
CH = [c["chapter"] for c in ch]
SENT = [round(c["avg_sent_len"], 3) for c in ch]
PUNC = [round(c["punct_density"], 4) for c in ch]
DIAL = [round(c["dialogue_ratio"], 4) for c in ch]
N = len(CH)

option_js = (
    "function(vars){\n"
    "  var palette = WZ.buildTheme().color;\n"
    "  var CH = %s;\n"
    "  var SENT = %s;\n"
    "  var PUNC = %s;\n"
    "  var DIAL = %s;\n"
    "  return {\n"
    "    legend:{data:['平均句长','标点密度','对话占比'],top:6,icon:'roundRect'},\n"
    "    grid:{left:52,right:58,top:44,bottom:64,containLabel:true},\n"
    "    tooltip:{trigger:'axis'},\n"
    "    xAxis:{type:'category',data:CH,name:'章',nameGap:28},\n"
    "    yAxis:[{type:'value',name:'平均句长',position:'left'},{type:'value',name:'比率',min:0,max:1,position:'right'}],\n"
    "    series:[\n"
    "      {name:'平均句长',type:'line',smooth:true,yAxisIndex:0,data:SENT,lineStyle:{width:2.4},itemStyle:{color:palette[0]},emphasis:{focus:'series'}},\n"
    "      {name:'标点密度',type:'line',smooth:true,yAxisIndex:1,data:PUNC,lineStyle:{width:2},itemStyle:{color:palette[1]},emphasis:{focus:'series'}},\n"
    "      {name:'对话占比',type:'line',smooth:true,yAxisIndex:1,data:DIAL,lineStyle:{width:2},itemStyle:{color:palette[2]},emphasis:{focus:'series'}}\n"
    "    ],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n"
    "  };\n"
    "}"
) % (json.dumps(CH), json.dumps(SENT), json.dumps(PUNC), json.dumps(DIAL))

title = "文体指纹与节奏（交互式动态图表）"
hint = "交互：悬停看逐章数值 · 拖动缩放 · 点击图例筛选 · 「播放时间轴」逐章演进（决战章对话骤降、叙述加快）· 「模拟实时数据流」演示平滑重绘。"
card = C.card(title, "sty", "both", N, hint, height=460)
script = C.init("sty", option_js, "both", N)

with io.open(HTML, "r", encoding="utf-8") as f:
    html = f.read()
html = C.replace_svg_cards(html, [card])
html = C.inject_script(html, script)
with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("[完成] 风格计量 → ECharts 交互式（%d 章，三线对照）" % N)
