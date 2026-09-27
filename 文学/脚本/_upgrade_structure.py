# -*- coding: utf-8 -*-
"""就地升级《章节结构量化》报告：将 4 个静态 SVG 卡片替换为 ECharts 交互式图表。
  二、故事线分布（柱）· 三、叙事视角分布（饼）· 四、自由标签主题词频（柱）·
  六、感情线 × 故事线 交叉分布（热力图，替代原「×算法情感」，因源数据无算法情感标签）
数据取自已验证的 chapter_data/all_tags.json。
"""
import os, io, json, collections
import _chartlib as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_章节结构量化.html")
TAGS = os.path.join(ROOT, "数据", "chapter_data", "all_tags.json")
tags = C.load_json(TAGS)

def counter(field):
    c = collections.Counter()
    for e in tags:
        v = e.get(field)
        if isinstance(v, list):
            for x in v: c[x] += 1
        elif v is not None:
            c[v] += 1
    return c

# ---- 图 1：故事线分布（柱）----
arc_c = counter("story_arc")
ARC = [k for k, _ in arc_c.most_common()]
ARC_V = [arc_c[k] for k in ARC]
arc_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'故事线分布（story_arc）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:54,right:30,top:48,bottom:64,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'category',data:%s,axisLabel:{color:vars.muted,interval:0,rotate:18,fontSize:11}},\n"
    "    yAxis:{type:'value',name:'章数'},\n"
    "    series:[{type:'bar',data:%s,barWidth:'52%%',itemStyle:{color:palette[0],borderRadius:[4,4,0,0]},\n"
    "      label:{show:true,position:'top',color:vars.muted},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(ARC, ensure_ascii=False), json.dumps(ARC_V))

# ---- 图 2：叙事视角分布（饼）----
pov_c = counter("narrative_pov")
POV = [{"name": k, "value": v} for k, v in pov_c.most_common()]
pov_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'叙事视角分布（narrative_pov）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    tooltip:{trigger:'item',formatter:'{b}: {c} 章 ({d}%%)'},\n"
    "    legend:{bottom:6,textStyle:{color:vars.muted}},\n"
    "    series:[{type:'pie',radius:['38%%','66%%'],center:['50%%','52%%'],data:%s,\n"
    "      label:{color:vars.ink},emphasis:{focus:'self'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(POV, ensure_ascii=False))

# ---- 图 3：自由标签主题词频（柱 Top20）----
tf = collections.Counter()
for e in tags:
    for t in e.get("tags_free", []):
        tf[t] += 1
TF = tf.most_common(20)
TF_W = [w for w, _ in TF][::-1]
TF_V = [v for _, v in TF][::-1]
tf_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n  return {\n"
    "    title:{text:'自由标签主题词频 Top20（tags_free）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},\n"
    "    grid:{left:96,right:48,top:48,bottom:40,containLabel:true},\n"
    "    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},\n"
    "    xAxis:{type:'value',name:'出现章数'},\n"
    "    yAxis:{type:'category',data:%s,axisLabel:{color:vars.muted,fontSize:11}},\n"
    "    series:[{type:'bar',data:%s,barWidth:'62%%',itemStyle:{color:palette[2],borderRadius:[0,4,4,0]},\n"
    "      label:{show:true,position:'right',color:vars.muted},emphasis:{focus:'series'}}],\n"
    "    animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'\n  };\n}"
) % (json.dumps(TF_W, ensure_ascii=False), json.dumps(TF_V))

# ---- 图 4：感情线 × 故事线 交叉热力图 ----
emo_c = counter("emotion_line")
EMO = [k for k, _ in emo_c.most_common()]          # 行
emoi = {e: i for i, e in enumerate(EMO)}
ARCI = {a: i for i, a in enumerate(ARC)}
cross = collections.Counter()
for e in tags:
    em = e.get("emotion_line"); ar = e.get("story_arc")
    if em in emoi and ar in ARCI:
        cross[(emoi[em], ARCI[ar])] += 1
CELLS = [[k[1], k[0], v] for k, v in cross.items()]   # [x=arcIdx, y=emoIdx, val]
mx = max([c[2] for c in CELLS], default=0)
cross_opt = (
    "function(vars){\n  var palette=WZ.buildTheme().color;\n"
    "  var EMO=%s, ARC=%s, CELLS=%s;\n  return {\n"
    "    title:{text:'感情线 × 故事线 交叉分布（按同章计次）',left:'center',top:4,textStyle:{color:vars.ink,fontSize:13.5}},\n"
    "    grid:{left:110,right:24,top:50,bottom:120,containLabel:false},\n"
    "    tooltip:{trigger:'item',position:'top',formatter:function(p){return EMO[p.data[1]]+' × '+ARC[p.data[0]]+'：'+p.data[2]+' 章';}},\n"
    "    xAxis:{type:'category',data:ARC,axisLabel:{interval:0,rotate:30,color:vars.muted,fontSize:10},splitArea:{show:true}},\n"
    "    yAxis:{type:'category',data:EMO,axisLabel:{color:vars.muted,fontSize:11},splitArea:{show:true}},\n"
    "    visualMap:{min:0,max:%d,calculable:true,orient:'horizontal',left:'center',bottom:4,\n"
    "      inRange:{color:[vars.surface,'#cfe3f2',palette[0],palette[1]]},textStyle:{color:vars.muted}},\n"
    "    series:[{type:'heatmap',data:CELLS,emphasis:{itemStyle:{shadowBlur:8,shadowColor:'rgba(0,0,0,.3)'}}}],\n"
    "    animationDurationUpdate:420\n  };\n}"
) % (json.dumps(EMO, ensure_ascii=False), json.dumps(ARC, ensure_ascii=False), json.dumps(CELLS), mx)

cards = [
    ("二、故事线分布", "二、故事线分布（交互式）", "st_arc", arc_opt, len(ARC), 380,
     "交互：悬停看章数 · 点击图例 · 拖动缩放。"),
    ("三、叙事视角分布", "三、叙事视角分布（交互式）", "st_pov", pov_opt, len(POV), 380,
     "交互：悬停看占比 · 点击扇区高亮。"),
    ("四、自由标签主题词频", "四、自由标签主题词频（交互式）", "st_tf", tf_opt, len(TF_W), 460,
     "交互：悬停看出现章数 · 拖动缩放。"),
    ("六、感情线 × 算法情感 交叉验证", "六、感情线 × 故事线 交叉分布（交互式）", "st_cross", cross_opt, len(CELLS), 480,
     "交互：悬停查看「感情线 × 故事线」同章共现次数 · 颜色越深越多。"),
]
charts = [("st_arc", arc_opt, "none", len(ARC)),
          ("st_pov", pov_opt, "none", len(POV)),
          ("st_tf", tf_opt, "none", len(TF_W)),
          ("st_cross", cross_opt, "none", len(CELLS))]

with io.open(HTML, "r", encoding="utf-8") as f:
    html = f.read()
for old, new, cid, opt, n, h, hint in cards:
    card = C.card(new, cid, "none", n, hint, height=h)
    html = C.replace_heading_block(html, old, new, card)
html = C.inject_script(html, C.bundle(charts))

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("[完成] 章节结构量化 → ECharts 交互式（柱/饼/柱/热力图，controls=none）")
print("  story_arc %d类 · narrative_pov %d类 · tags_free Top%d · 交叉格 %d（max %d）" % (len(ARC), len(POV), len(TF_W), len(CELLS), mx))
