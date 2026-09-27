# -*- coding: utf-8 -*-
"""
24_build_extended_viz.py
========================
扩展叙事可视化构建器（在四维流程图之外的新四维）：

  ① 因果事件链图   —— 从 all_tags.json 的 key_events 抽因果连词，构建章→章因果 DAG (Mermaid)
                       + 章内子事件因果链样例面板（真正落地"因果关系"）
  ② 叙事节奏谱     —— ECharts 合成"小说心电图"：战斗强度(右轴) + 篇幅(左轴) + 悲剧章阴影
  ③ 角色六维雷达+性格谱系 —— char_traits.json 信号计数 → 6 维刻画强度向量；
                       雷达对比 top8 + 余弦相似谱系网络(聚类)
  ④ 角色登场矩阵热力图 —— chapters×characters 登场强度热力图（按首登场排序）

产物：产物/苇舟江湖梦_扩展叙事可视化.html  （离线：本地 echarts.min.js + mermaid.min.js）
"""
import json, os, re
from collections import Counter, OrderedDict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "数据")
OUT  = os.path.join(BASE, "产物")
READER = "苇舟江湖梦_原文阅读.html"
NARR   = "苇舟江湖梦_可视化叙事系统.html"

AXES = ["性情", "品性", "心气", "情义", "智愚", "胆气"]
# 纯因果连词（排除 因为/因此/因之 等复合；排除 故事/故乡/故人/故国）
CAUSAL = ["于是", "因而", "故此", "所以", "致使", "由此", "以此", "既而", "由是", "因之", "遂", "缘"]
TEMP = ["次日", "当夜", "其后", "不久", "自此", "从此", "旋", "未几", "顷之", "俄而", "继而"]

def _has_cue(text, cue):
    if cue in ("因", "故"):
        if cue == "因":
            return bool(re.search(r"(?<!为)因(?!此|而|之)", text))
        return bool(re.search(r"故(?!事|乡|人|国)", text))
    return cue in text

def load():
    with open(os.path.join(DATA, "chapter_data", "all_tags.json"), encoding="utf-8") as f:
        d = json.load(f)
    d.sort(key=lambda c: c["chapter"])
    return d

# ---------------------------------------------------------------- ① 因果（基于原文真实语料）
def _split_sentences(text):
    return [s.strip() for s in re.split(r"[。！？；…]", text) if len(s.strip()) >= 6]

def build_causal(chapters, parts):
    # parts[k] = 第 k 章原文（k=1..59）；章→章因果/时序边来自下一章原文是否含连词
    edges = []
    involved = set()
    for i in range(1, 59):
        nxt = parts[i + 1] if i + 1 < len(parts) else ""
        c_hit = next((c for c in CAUSAL if _has_cue(nxt, c)), None)
        t_hit = next((c for c in TEMP if c in nxt), None)
        if c_hit:
            edges.append((i, i + 1, c_hit, "causal")); involved.update([i, i + 1])
        elif t_hit:
            edges.append((i, i + 1, t_hit, "temp")); involved.update([i, i + 1])
    nodes = sorted(involved)
    nid = {ch: f"c{ch}" for ch in nodes}
    lines = ["flowchart TD"]
    arc_of = {c["chapter"]: c.get("story_arc", "") for c in chapters}
    for ch in nodes:
        lines.append(f'    {nid[ch]}["第{ch}章"]')
    for a, b, cue, kind in edges:
        if kind == "causal":
            lines.append(f'    {nid[a]} -->|"{cue}"| {nid[b]}')
        else:
            lines.append(f'    {nid[a]} -.->|"{cue}"| {nid[b]}')
    src = "\n".join(lines)
    # 章内真实因果子句链（取自原文，连词高亮）
    intra = []
    for k in range(1, 60):
        sents = _split_sentences(parts[k])
        pairs = []
        for j in range(len(sents) - 1):
            hit = next((cu for cu in CAUSAL if _has_cue(sents[j + 1], cu)), None)
            if hit:
                pairs.append((sents[j][:42], sents[j + 1][:42], hit))
        if pairs:
            intra.append({"ch": k, "chains": pairs})
    intra.sort(key=lambda x: -len(x["chains"]))
    return src, edges, intra[:12]

# ---------------------------------------------------------------- ② 节奏
def build_rhythm(chapters):
    chs, ci, wc, tragic = [], [], [], []
    for c in chapters:
        chs.append(c["chapter"])
        ci.append(c.get("combat_intensity", 0))
        wc.append(c.get("word_count", 0))
        tragic.append(1 if c.get("emotion_line") in ("虐/悲情", "分离/离别") or "悲剧/伤亡" in (c.get("chapter_type") or []) else 0)
    return {"chs": chs, "ci": ci, "wc": wc, "tragic": tragic}

# ---------------------------------------------------------------- ③ 雷达+谱系
def build_traits():
    d = json.load(open(os.path.join(DATA, "char_traits.json"), encoding="utf-8"))
    vecs = {}
    totals = {}
    dominant = {}
    for name, prof in d.items():
        v = [0] * 6
        for s in prof.get("signals", []) or []:
            if s.get("axis") in AXES:
                v[AXES.index(s["axis"])] += 1
        vecs[name] = v
        totals[name] = sum(v)
        dominant[name] = prof.get("dominant_traits", []) or []
    # top8 by total
    top = sorted([n for n in vecs if totals[n] > 0], key=lambda n: -totals[n])[:8]
    radar = {"axes": AXES, "series": [{"name": n, "value": vecs[n], "dom": dominant[n]} for n in top]}
    # 余弦相似谱系（仅对非零向量）
    nonzero = [n for n in vecs if totals[n] > 0]
    def cos(a, b):
        na = sum(x * x for x in a) ** .5; nb = sum(x * x for x in b) ** .5
        if na == 0 or nb == 0: return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        return dot / (na * nb)
    pairs = []
    for i in range(len(nonzero)):
        for j in range(i + 1, len(nonzero)):
            s = cos(vecs[nonzero[i]], vecs[nonzero[j]])
            if s >= 0.85:
                pairs.append((nonzero[i], nonzero[j], round(s, 3)))
    # 节点：所有有数据的角色，size=total
    nodes = [{"name": n, "size": totals[n]} for n in nonzero]
    return radar, {"nodes": nodes, "edges": pairs}

# ---------------------------------------------------------------- ④ 热力
def build_heat(chapters):
    # 角色首登场排序；仅保留登场≥2章的显著角色，避免标签过载
    first = {}
    cnt = Counter()
    for c in chapters:
        for ch_name in (c.get("characters_present") or []):
            if ch_name not in first:
                first[ch_name] = c["chapter"]
            cnt[ch_name] += 1
    chars = [n for n in first if cnt[n] >= 2]
    chars.sort(key=lambda n: first[n])
    chs = [c["chapter"] for c in chapters]
    present = {c["chapter"]: set(c.get("characters_present") or []) for c in chapters}
    cells = []
    for yi, ch_name in enumerate(chars):
        for xi, ch in enumerate(chs):
            if ch_name in present[ch]:
                cells.append([xi, yi, 1])
    return {"chars": chars, "chs": chs, "cells": cells, "first": first}

def main():
    chapters = load()
    # 原文分章（块0=自序，块1..59=第1..59章）
    txt = open(os.path.join(DATA, "full_text.txt"), encoding="utf-8").read()
    marker = re.compile(r"^[一二三四五六七八九十百零〇\d]+[、．.]\s*$", re.M)
    parts = [p for p in re.split(marker, txt) if p and p.strip()]
    causal_src, causal_edges, causal_samples = build_causal(chapters, parts)
    rhythm = build_rhythm(chapters)
    radar, cluster = build_traits()
    heat = build_heat(chapters)

    html = TEMPLATE
    html = html.replace("/*CAUSAL_SRC*/", causal_src)
    html = html.replace("/*RYTHM*/", json.dumps(rhythm, ensure_ascii=False))
    html = html.replace("/*RADAR*/", json.dumps(radar, ensure_ascii=False))
    html = html.replace("/*CLUSTER*/", json.dumps(cluster, ensure_ascii=False))
    html = html.replace("/*HEAT*/", json.dumps(heat, ensure_ascii=False))
    html = html.replace("/*CAUSAL_SAMPLES*/", json.dumps(causal_samples, ensure_ascii=False))
    html = html.replace("/*READER*/", READER)
    html = html.replace("/*NARR*/", NARR)
    html = html.replace("/*NEDGES*/", str(len(causal_edges)))
    html = html.replace("/*NSAMP*/", str(len(causal_samples)))

    out = os.path.join(OUT, "苇舟江湖梦_扩展叙事可视化.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("causal edges:", len(causal_edges), "samples:", len(causal_samples))
    print("radar top8:", [s['name'] for s in radar['series']])
    print("cluster edges:", len(cluster['edges']), "nodes:", len(cluster['nodes']))
    print("heat cells:", len(heat['cells']), "chars:", len(heat['chars']))
    print("written:", out)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>苇舟江湖梦 · 扩展叙事可视化</title>
<style>
:root{--bg:#0a0f1c;--panel:rgba(20,32,54,.62);--brd:rgba(90,150,230,.22);--txt:#e8eefc;--muted:#9fb2d4;
  --blue:#3b82f6;--cyan:#22d3ee;--violet:#a78bfa;--amber:#f59e0b;--red:#ef4444;--green:#34d399;}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 700px at 80% -10%,rgba(59,130,246,.18),transparent 60%),
  radial-gradient(900px 600px at 0% 110%,rgba(167,139,250,.14),transparent 55%),var(--bg);
  color:var(--txt);font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",system-ui,sans-serif;line-height:1.6}
.wrap{max-width:1240px;margin:0 auto;padding:28px 22px 80px}
header h1{margin:0;font-size:28px;letter-spacing:2px;background:linear-gradient(90deg,var(--cyan),var(--blue),var(--violet));
  -webkit-background-clip:text;background-clip:text;color:transparent}
header p{margin:6px 0 0;color:var(--muted);font-size:14px}
.nav{margin:10px 0 4px}
.nav a{color:var(--cyan);text-decoration:none;font-size:13px;border:1px solid var(--brd);padding:4px 10px;border-radius:8px}
.nav a:hover{background:rgba(34,211,238,.12)}
section{background:var(--panel);border:1px solid var(--brd);border-radius:16px;padding:18px;margin-top:20px;
  backdrop-filter:blur(14px);box-shadow:0 10px 40px rgba(0,0,0,.35)}
section h2{margin:0 0 4px;font-size:20px;display:flex;align-items:center;gap:8px}
section h2 .dot{width:12px;height:12px;border-radius:3px}
.sub{color:var(--muted);font-size:13px;margin-bottom:12px}
.chart{width:100%;height:460px}
.flow-host{overflow:auto;max-height:560px;border-radius:10px;background:rgba(6,11,22,.45);border:1px solid rgba(90,150,230,.12);padding:6px}
pre.mermaid{background:transparent;margin:0}
.samples{margin-top:14px;display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:800px){.samples{grid-template-columns:1fr}}
.scard{background:rgba(6,11,22,.4);border:1px solid rgba(90,150,230,.12);border-radius:10px;padding:10px 12px;font-size:12.5px}
.scard b{color:var(--amber)}
.scard .ev{color:var(--txt)} .scard .cue{color:var(--red);font-weight:700}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:900px){.two{grid-template-columns:1fr}}
.nx-hl{outline:3px solid var(--amber)!important;outline-offset:2px;filter:drop-shadow(0 0 8px var(--amber))}
.hint{color:var(--muted);font-size:12px;margin-top:8px}
a.rdr{color:var(--cyan);text-decoration:none}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>苇舟江湖梦 · 扩展叙事可视化</h1>
  <p>在四维状态转移流程图之外，用因果链、节奏谱、性格雷达/谱系、登场矩阵进一步把小说的「隐性结构」显性化。全部离线可用。</p>
  <div class="nav"><a href="/*NARR*/">← 返回四维叙事系统</a></div>
</header>

<section>
  <h2><span class="dot" style="background:var(--red)"></span>① 因果事件链图</h2>
  <div class="sub">从各章关键事件抽取因果连词（于是/因而/所以/遂/由此/缘…），仅当「下一章事件由前文导出」时连边——高亮全书<b>因果密集段</b>。共 /*NEDGES*/ 条因果边；点击节点跳转原文。</div>
  <div class="flow-host" id="host_causal"><pre class="mermaid">
/*CAUSAL_SRC*/</pre></div>
  <div class="samples" id="samples"></div>
  <div class="hint">章内子事件因果链样例（/*NSAMP*/ 章）：连词以<span style="color:var(--red);font-weight:700">红</span>标出，可见一步推一步的因果脉络。</div>
</section>

<section>
  <h2><span class="dot" style="background:var(--amber)"></span>② 叙事节奏谱 · 小说心电图</h2>
  <div class="sub">左轴＝篇幅(字数)，右轴＝战斗强度(0–3)，红色阴影＝悲情/伤亡章。看全书的张弛与留白。</div>
  <div class="chart" id="rhythm"></div>
</section>

<section>
  <h2><span class="dot" style="background:var(--violet)"></span>③ 角色六维性格雷达 + 性格谱系</h2>
  <div class="sub">六维＝各性格轴被「刻画证据」的强度计数（非极性评分）。左：刻画最密的角色对比；右：余弦相似谱系网络（连边＝性格刻画模式相近），节点越大刻画越丰。</div>
  <div class="two">
    <div class="chart" id="radar"></div>
    <div class="chart" id="cluster"></div>
  </div>
</section>

<section>
  <h2><span class="dot" style="background:var(--cyan)"></span>④ 角色登场矩阵热力图</h2>
  <div class="sub">纵轴＝角色（按首登场排序），横轴＝章节(1–59)。亮点＝该章登场。竖向光带即人物弧光；群像章（多角色同亮）与独奏章一目了然。点击格子跳转原文。</div>
  <div class="chart" id="heat" style="height:720px"></div>
</section>

</div>

<script src="echarts.min.js"></script>
<script src="mermaid.min.js"></script>
<script>
const READER="/*READER*/";
const RHYTHM=/*RYTHM*/;
const RADAR=/*RADAR*/;
const CLUSTER=/*CLUSTER*/;
const HEAT=/*HEAT*/;
const SAMPLES=/*CAUSAL_SAMPLES*/;

/* 暗色玻璃主题 */
const AX='#33415c', TXT='#cdd9f0', MUT='#9fb2d0';
const PAL=['#3b82f6','#22d3ee','#a78bfa','#f59e0b','#34d399','#ef4444','#60a5fa','#f472b6'];
function tip(){return {trigger:'axis',backgroundColor:'rgba(10,15,28,.92)',borderColor:'#33415c',textStyle:{color:TXT}};}

/* ① Mermaid */
mermaid.initialize({startOnLoad:false,securityLevel:'loose',theme:'base',
  themeVariables:{background:'transparent',primaryColor:'rgba(40,20,30,.85)',primaryTextColor:'#ffe1e1',
    primaryBorderColor:'#ef4444',lineColor:'#f59e0b',fontSize:'13px'},
  flowchart:{curve:'basis',htmlLabels:true,nodeSpacing:30,rankSpacing:42}});

/* ② 节奏谱 */
(function(){
  const el=document.getElementById('rhythm');
  const ch=echarts.init(el,null,{renderer:'canvas'});
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:tip(),
    legend:{data:['篇幅(字)','战斗强度'],textStyle:{color:TXT},top:0},
    grid:{left:58,right:54,top:40,bottom:60},
    xAxis:{type:'category',data:RHYTHM.chs,axisLine:{lineStyle:{color:AX}},axisLabel:{color:MUT,interval:4}},
    yAxis:[
      {type:'value',name:'字数',axisLine:{lineStyle:{color:AX}},splitLine:{lineStyle:{color:'rgba(90,150,230,.08)'}},axisLabel:{color:MUT}},
      {type:'value',name:'战力',min:0,max:3,axisLine:{lineStyle:{color:AX}},splitLine:{show:false},axisLabel:{color:MUT}}
    ],
    series:[
      {name:'篇幅(字)',type:'line',smooth:true,data:RHYTHM.wc,showSymbol:false,lineStyle:{color:'#22d3ee',width:2},
        areaStyle:{color:'rgba(34,211,238,.12)'},
        markArea:{silent:true,itemStyle:{color:'rgba(239,68,68,.10)'},
          data:RHYTHM.tragic.map((t,i)=> t?[{xAxis:i},{xAxis:i}]:null).filter(Boolean)}},
      {name:'战斗强度',type:'bar',yAxisIndex:1,data:RHYTHM.ci,barWidth:'55%',
        itemStyle:{color:function(p){return ['#34d399','#a3e635','#f59e0b','#ef4444'][p.value]||'#ef4444';}}}
    ]
  });
  ch.on('click',p=>{ if(p.dataIndex!=null) window.open(READER+'?loc=ch'+RHYTHM.chs[p.dataIndex],'_blank','noopener'); });
  window.addEventListener('resize',()=>ch.resize());
})();

/* ③ 雷达 */
(function(){
  const el=document.getElementById('radar');
  const ch=echarts.init(el,null,{renderer:'canvas'});
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:{backgroundColor:'rgba(10,15,28,.92)',borderColor:'#33415c',textStyle:{color:TXT}},
    legend:{data:RADAR.series.map(s=>s.name),textStyle:{color:TXT},top:0,type:'scroll'},
    radar:{indicator:RADAR.axes.map(a=>({name:a,max:Math.max(3,...RADAR.series.map(s=>s.value[RADAR.axes.indexOf(a)]))})),
      axisName:{color:TXT},splitLine:{lineStyle:{color:'rgba(90,150,230,.18)'}},
      splitArea:{areaStyle:{color:['rgba(34,211,238,.04)','rgba(59,130,246,.04)']}},
      axisLine:{lineStyle:{color:'rgba(90,150,230,.25)'}}},
    series:[{type:'radar',data:RADAR.series.map((s,i)=>({name:s.name,value:s.value,
      lineStyle:{color:PAL[i%PAL.length],width:2},itemStyle:{color:PAL[i%PAL.length]},
      areaStyle:{opacity:0.08}}))}]
  });
  window.addEventListener('resize',()=>ch.resize());
})();

/* ③ 谱系网络 */
(function(){
  const el=document.getElementById('cluster');
  const ch=echarts.init(el,null,{renderer:'canvas'});
  const nodes=CLUSTER.nodes.map((n,i)=>({id:n.name,name:n.name,value:n.size,
    symbolSize:10+Math.sqrt(n.size)*6,
    itemStyle:{color:PAL[i%PAL.length]},
    label:{show:true,color:TXT,fontSize:11}}));
  const links=CLUSTER.edges.map(e=>({source:e[0],target:e[1],value:e[2],
    lineStyle:{color:'rgba(167,139,250,.45)',width:1+e[2]*2}}));
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:{backgroundColor:'rgba(10,15,28,.92)',borderColor:'#33415c',textStyle:{color:TXT},
      formatter:p=> p.dataType==='edge'? (p.data.source+' ↔ '+p.data.target+'  相似 '+p.data.value):(p.data.name+'  刻画证据 '+p.data.value+' 条')},
    series:[{type:'graph',layout:'force',roam:true,
      force:{repulsion:160,edgeLength:[40,120],gravity:0.08},
      data:nodes,links:links,
      lineStyle:{opacity:0.6},emphasis:{focus:'adjacency'}}]
  });
  window.addEventListener('resize',()=>ch.resize());
})();

/* ④ 热力图 */
(function(){
  const el=document.getElementById('heat');
  const ch=echarts.init(el,null,{renderer:'canvas'});
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:{position:'top',backgroundColor:'rgba(10,15,28,.92)',borderColor:'#33415c',textStyle:{color:TXT},
      formatter:p=> HEAT.chars[p.data[1]]+' · 第'+HEAT.chs[p.data[0]]+'章（登场）'},
    grid:{left:96,right:20,top:10,bottom:50},
    xAxis:{type:'category',data:HEAT.chs,axisLine:{lineStyle:{color:AX}},axisLabel:{color:MUT,interval:4},splitArea:{show:false}},
    yAxis:{type:'category',data:HEAT.chars,axisLine:{lineStyle:{color:AX}},axisLabel:{color:MUT,fontSize:10}},
    visualMap:{min:0,max:1,calculable:true,show:false,inRange:{color:['#0a0f1c','#3b82f6','#22d3ee','#a78bfa']}},
    series:[{type:'heatmap',data:HEAT.cells,progressive:2000,
      itemStyle:{borderColor:'rgba(10,15,28,.6)',borderWidth:0.5},
      emphasis:{itemStyle:{color:'#f59e0b'}}}]
  });
  ch.on('click',p=>{ if(p.data) window.open(READER+'?loc=ch'+HEAT.chs[p.data[0]],'_blank','noopener'); });
  window.addEventListener('resize',()=>ch.resize());
})();

/* ① 样例面板 */
(function(){
  const box=document.getElementById('samples');
  box.innerHTML=SAMPLES.map(s=>{
    const items=s.chains.map(c=>{
      const a=c[0],b=c[1],cue=c[2];
      const bb=b.replace(cue,'<span class="cue">'+cue+'</span>');
      return '<div class="ev">'+a+'</div><div class="ev">→ '+bb+'</div>';
    }).join('');
    return '<div class="scard"><b>第'+s.ch+'章</b>'+items+'</div>';
  }).join('');
})();

/* 渲染因果图 + 节点跳转 */
(async function(){
  try{ await mermaid.run(); }catch(e){ console.error(e); }
  const host=document.getElementById('host_causal');
  host.addEventListener('click',e=>{
    const g=e.target.closest('g.node');
    if(!g) return;
    const t=g.querySelector('.nodeLabel'); const txt=t?t.textContent:'';
    const m=txt.match(/第(\d+)章/); if(m) window.open(READER+'?loc=ch'+m[1],'_blank','noopener');
  });
})();
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
