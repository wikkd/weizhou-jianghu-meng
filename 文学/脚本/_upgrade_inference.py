# -*- coding: utf-8 -*-
"""为《统计推断》报告新增一张 ECharts 交互式显著性柱状图（原报告仅有表格，无 SVG 图）。
展示 5 项假设检验的 p 值，按是否显著着色（红=显著），并标注 0.05 显著性阈值；
悬停可看方法、统计量、效应量与解读。controls=none（静态比较，动态重绘无意义）。
数据取自已验证的 stats_inference.json。
"""
import os, io, json, re
import _chartlib as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_统计推断.html")
JSON = os.path.join(ROOT, "数据", "analysis", "stats_inference.json")
data = C.load_json(JSON)

def clean(label):
    return re.sub(r"^[a-z]_", "", label)

TESTS = []
for t in data:
    TESTS.append({
        "label": clean(t["test"]),
        "p": round(float(t["p"]), 4),
        "sig": bool(t["significant"]),
        "method": t.get("method", ""),
        "stat": t.get("stat"),
        "effect": t.get("effect", ""),
        "interp": t.get("interpretation", ""),
    })

opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n"
    "  var TESTS=%s;\n  return {\n"
    "    title:{text:'假设检验 p 值（红=显著，阈值 0.05）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:170,right:60,top:48,bottom:46,containLabel:true},\n"
    "    tooltip:{trigger:'item',formatter:function(p){var t=TESTS[p.dataIndex];return '<b>'+t.label+'</b><br/>方法：'+t.method+'<br/>统计量：'+t.stat+'<br/>p='+t.p+(t.sig?'（显著）':'（不显著）')+'<br/>效应：'+t.effect+'<br/><span style=\"color:'+vars.muted+'\">'+t.interp+'</span>';}},\n"
    "    xAxis:{type:'value',name:'p 值',max:0.30,axisLabel:{color:vars.muted}},\n"
    "    yAxis:{type:'category',data:TESTS.map(function(t){return t.label;}),axisLabel:{color:vars.muted,fontSize:11}},\n"
    "    series:[{type:'bar',data:TESTS.map(function(t){return {value:t.p,itemStyle:{color:t.sig?palette[1]:vars.muted,borderRadius:[0,4,4,0]}};}),\n"
    "      barWidth:'56%%',label:{show:true,position:'right',color:vars.ink,formatter:function(p){return p.value;}},\n"
    "      markLine:{silent:true,symbol:'none',data:[{xAxis:0.05}],lineStyle:{type:'dashed',color:vars.accent},label:{formatter:'α=0.05',color:vars.accent,position:'insideEndTop'}},\n"
    "      emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(TESTS, ensure_ascii=False),)

hint = "交互：悬停查看方法/统计量/p 值/效应量与解读 · 拖动缩放 · 红色＝通过 0.05 显著性，灰色＝未通过。"
card = C.card("结果可视化（交互式）", "inf", "none", len(TESTS), hint, height=360)

with io.open(HTML, "r", encoding="utf-8") as f:
    html = f.read()

# 在「二、通俗解读」之前插入新图表卡片（原表格保留不动）
anchor = "<h2>二、通俗解读"
idx = html.find(anchor)
if idx == -1:
    print("[错误] 未找到插入锚点「二、通俗解读」"); raise SystemExit(1)
html = html[:idx] + card + "\n" + html[idx:]

html = C.inject_script(html, C.bundle([("inf", opt, "none", len(TESTS))]))
with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("[完成] 统计推断 → 新增 ECharts 交互式显著性柱状图（%d 项检验）" % len(TESTS))
print("  显著:", sum(1 for t in TESTS if t["sig"]), " · 不显著:", sum(1 for t in TESTS if not t["sig"]))
