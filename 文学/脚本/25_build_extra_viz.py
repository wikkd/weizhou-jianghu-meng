# -*- coding: utf-8 -*-
"""
25_build_extra_viz.py
======================
深度叙事可视化（四维之外的再四个）：

  ① 伏笔—回收网络   —— 扫描 full_text 原文，抽伏笔/悬念连词(setup)与应验/揭晓连词(payoff)，
                       按共享角色跨章连 setup→payoff 边（ECharts graph）+ 真实例句样例面板。
  ② 时空动画地图     —— spatial_data 坐标 + 各章主地点 + time_layer，ECharts timeline 动画：
                       逐章高亮当前地点并连线迁移，事件在地图上"走"起来。
  ③ 文风漂移流图     —— stylometry 逐章 5 维文体特征，ECharts themeRiver(流图) 展示占比漂移。
  ④ 知识图谱 + MOC   —— 角色/地点/关键词/时代 分类节点 + 共现边（ECharts graph），
                       附 MOC 内容地图导航。

产物：产物/苇舟江湖梦_深度叙事可视化.html  （离线：本地 echarts.min.js + mermaid.min.js）
"""
import json, os, re
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "数据")
OUT  = os.path.join(BASE, "产物")
READER = "苇舟江湖梦_原文阅读.html"
NARR   = "苇舟江湖梦_可视化叙事系统.html"
EXT    = "苇舟江湖梦_扩展叙事可视化.html"

# ---------------------------------------------------------------- 数据加载
def load_chapters():
    with open(os.path.join(DATA, "chapter_data", "all_tags.json"), encoding="utf-8") as f:
        d = json.load(f)
    d.sort(key=lambda c: c["chapter"])
    return d

def load_parts():
    txt = open(os.path.join(DATA, "full_text.txt"), encoding="utf-8").read()
    marker = re.compile(r"^[一二三四五六七八九十百零〇\d]+[、．.]\s*$", re.M)
    return [p for p in re.split(marker, txt) if p and p.strip()]

def split_sentences(text):
    return [s.strip() for s in re.split(r"[。！？；…]", text) if len(s.strip()) >= 6]

# ---------------------------------------------------------------- ① 伏笔回收
SETUP = ["伏笔", "悬念", "埋下", "端倪", "征兆", "隐隐", "山雨欲来", "一触即发", "蓄势", "暗流",
         "冥冥", "日后", "终有一日", "迟早", "料定", "似有", "若是有", "风声", "剑拔弩张"]
PAYOFF = ["应验", "果然", "殊不知", "原来", "竟", "终究", "真相", "水落石出", "成真", "应了",
          "兑现", "恍然", "大白", "谜底", "揭晓", "端的是", "现出", "至此方知"]

def build_foreshadow(parts, names):
    # names: 角色名列表（按长度降序，len>=2）
    setup_ch, payoff_ch = {}, {}
    for k in range(1, 63):
        sents = split_sentences(parts[k]) if k < len(parts) else []
        su = [s for s in sents if any(c in s for c in SETUP)]
        pa = [s for s in sents if any(c in s for c in PAYOFF)]
        if su: setup_ch[k] = su
        if pa: payoff_ch[k] = pa
    def entities(text):
        return [n for n in names if n in text]
    pairs = []
    for a in sorted(setup_ch):
        for b in sorted(payoff_ch):
            if b <= a:
                continue
            shared = set()
            for s in setup_ch[a]:
                es = entities(s)
                for p in payoff_ch[b]:
                    ep = entities(p)
                    inter = set(es) & set(ep)
                    if inter:
                        shared |= inter
            if shared:
                pairs.append({"a": a, "b": b, "entity": "/".join(sorted(shared)[:3]),
                              "gap": b - a, "n": len(shared)})
    # 去重 (a,b) 保留最强；按 n 降序、gap 升序排序后截断
    seen = {}
    for p in pairs:
        key = (p["a"], p["b"])
        if key not in seen or p["n"] > seen[key]["n"]:
            seen[key] = p
    uniq = sorted(seen.values(), key=lambda x: (-x["n"], x["gap"]))[:70]
    # 样例：取 gap 适中且 n 较大者前 8，附例句
    samples = []
    for p in sorted(uniq, key=lambda x: (-x["n"], x["gap"]))[:8]:
        a, b = p["a"], p["b"]
        su = next((s for s in setup_ch[a] if any(n in s for n in p["entity"].split("/"))), setup_ch[a][0])
        pa = next((s for s in payoff_ch[b] if any(n in s for n in p["entity"].split("/"))), payoff_ch[b][0])
        cue_a = next((c for c in SETUP if c in su), "")
        cue_b = next((c for c in PAYOFF if c in pa), "")
        samples.append({"a": a, "b": b, "entity": p["entity"],
                        "setup": su[:60], "payoff": pa[:60], "ca": cue_a, "cb": cue_b})
    return {"edges": [{"a": p["a"], "b": p["b"], "entity": p["entity"]} for p in uniq],
            "samples": samples, "nsetup": len(setup_ch), "npayoff": len(payoff_ch)}

# ---------------------------------------------------------------- ② 时空动画
def build_spacetime(chapters):
    sp = json.load(open(os.path.join(DATA, "spatial_data.json"), encoding="utf-8"))
    nodes = sp.get("nodes", {})
    coords = {name: v for name, v in nodes.items() if isinstance(v, list) and len(v) == 2}
    base = [{"name": n, "x": c[0], "y": c[1]} for n, c in coords.items()]
    chapters_data = []
    path = []
    for c in chapters:
        ch = c["chapter"]
        present = [l for l in (c.get("main_locations") or []) if l in coords]
        prim = (c.get("main_locations") or [None])[0]
        prim_c = coords.get(prim)
        if prim_c:
            path.append(prim_c)
        chapters_data.append({
            "ch": ch, "tl": c.get("time_layer", ""), "arc": c.get("story_arc", ""),
            "primary": prim or "—", "present": present,
            "path": [list(p) for p in path],
        })
    return {"base": base, "chapters": chapters_data, "nloc": len(base)}

# ---------------------------------------------------------------- ③ 文风漂移
def build_style():
    st = json.load(open(os.path.join(DATA, "analysis", "stylometry.json"), encoding="utf-8"))
    chs = st["chapters"]
    feats = [("句长", "avg_sent_len"), ("标点密度", "punct_density"),
             ("对话比", "dialogue_ratio"), ("段落数", "para_count"), ("段均长", "avg_para_len")]
    # 按特征 min-max 归一化到 0-1
    norm = {}
    for label, key in feats:
        vals = [c[key] for c in chs]
        lo, hi = min(vals), max(vals)
        rng = hi - lo or 1
        norm[label] = [(c[key] - lo) / rng for c in chs]
    themes = [f[0] for f in feats]
    data = []
    for i, c in enumerate(chs):
        for ti, label in enumerate(themes):
            data.append([c["chapter"], round(norm[label][i], 3), label])
    return {"themes": themes, "data": data}

# ---------------------------------------------------------------- ④ 知识图谱
def build_kg(chapters, parts):
    char_stats = json.load(open(os.path.join(DATA, "char_stats.json"), encoding="utf-8"))
    sp = json.load(open(os.path.join(DATA, "spatial_data.json"), encoding="utf-8"))
    lex = json.load(open(os.path.join(DATA, "analysis", "lexical_stats.json"), encoding="utf-8"))
    char_names = [c["name"] for c in char_stats] if isinstance(char_stats, list) else list(char_stats.keys())
    loc_names = [n for n, v in sp.get("nodes", {}).items() if isinstance(v, list) and len(v) == 2]
    top_words = [w["word"] for w in lex.get("top_words", []) if len(w["word"]) >= 2][:30]
    eras = ["初入江湖", "江湖历练", "庙堂初涉", "乱世将起", "战乱爆发", "大战/决战", "战后格局"]

    # 角色出现章节计数 + 共现
    char_ch = defaultdict(set)
    char_loc = defaultdict(Counter)
    char_era = defaultdict(Counter)
    pair = Counter()
    for c in chapters:
        ch = c["chapter"]
        chars = c.get("characters_present") or []
        locs = c.get("main_locations") or []
        tl = c.get("time_layer", "")
        for n in chars:
            char_ch[n].add(ch)
            char_era[n][tl] += 1
            for l in locs:
                if l in loc_names:
                    char_loc[n][l] += 1
        for i in range(len(chars)):
            for j in range(i + 1, len(chars)):
                a, b = chars[i], chars[j]
                if a != b:
                    pair[(a, b)] += 1

    # 关键词→时代（扫全文按章计数）
    kw_era = {}
    for w in top_words:
        if w in char_names:
            continue
        cnt = Counter()
        for k in range(1, 63):
            if k >= len(parts):
                break
            n = parts[k].count(w)
            if n:
                cnt[chapters[k - 1]["time_layer"]] += n
        if cnt:
            kw_era[w] = cnt.most_common(1)[0][0]

    cats = ["角色", "地点", "关键词", "时代"]
    nodes, links = [], []
    nid = {}
    def add(name, cat, size, color):
        nid[name] = len(nodes)
        nodes.append({"name": name, "category": cat, "symbolSize": size,
                      "itemStyle": {"color": color}, "label": {"show": cat != 1 or size > 16}})
    C = ["#3b82f6", "#22d3ee", "#a78bfa", "#f59e0b"]
    for n in char_names:
        add(n, 0, 10 + min(40, len(char_ch.get(n, [])) * 2), C[0])
    for n in loc_names:
        add(n, 1, 12, C[1])
    for w in top_words:
        if w not in char_names:
            add(w, 2, 10, C[2])
    for e in eras:
        add(e, 3, 26, C[3])
    # 边
    for (a, b), cnt in pair.items():
        if cnt >= 6 and a in nid and b in nid:
            links.append({"source": nid[a], "target": nid[b], "value": cnt,
                          "lineStyle": {"color": "rgba(59,130,246,.28)", "width": min(4, cnt / 4)}})
    for n, lc in char_loc.items():
        for l, cnt in lc.items():
            if cnt >= 4 and n in nid and l in nid:
                links.append({"source": nid[n], "target": nid[l], "value": cnt,
                              "lineStyle": {"color": "rgba(34,211,238,.25)", "width": 1}})
    for w, e in kw_era.items():
        if w in nid and e in nid:
            links.append({"source": nid[w], "target": nid[e], "value": 1,
                          "lineStyle": {"color": "rgba(167,139,250,.3)", "width": 1}})
    # 时代—角色 top3
    for e in eras:
        topc = sorted(char_era.items(), key=lambda x: -x[1].get(e, 0))[:3]
        for n, _ in topc:
            if n in nid and e in nid:
                links.append({"source": nid[n], "target": nid[e], "value": 1,
                              "lineStyle": {"color": "rgba(245,158,11,.3)", "width": 1}})
    return {"categories": cats, "nodes": nodes, "links": links,
            "nchar": len(char_names), "nloc": len(loc_names), "nkw": len(top_words)}

def main():
    chapters = load_chapters()
    parts = load_parts()
    cs = json.load(open(os.path.join(DATA, "char_stats.json"), encoding="utf-8"))
    cs_names = {c["name"] for c in cs} if isinstance(cs, list) else set(cs.keys())
    names = sorted({n for n in
                    (cs_names
                     | set().union(*[set(c.get("characters_present") or []) for c in chapters]))
                    if len(n) >= 2}, key=lambda x: -len(x))
    fores = build_foreshadow(parts, names)
    space = build_spacetime(chapters)
    style = build_style()
    kg = build_kg(chapters, parts)

    html = TEMPLATE
    for tok, val in [("/*FORES*/", json.dumps(fores, ensure_ascii=False)),
                     ("/*FORES_EDGES*/", str(len(fores["edges"]))),
                     ("/*FORES_NSETUP*/", str(fores["nsetup"])),
                     ("/*FORES_NPAYOFF*/", str(fores["npayoff"])),
                     ("/*SPACE*/", json.dumps(space, ensure_ascii=False)),
                     ("/*STYLE*/", json.dumps(style, ensure_ascii=False)),
                     ("/*KG*/", json.dumps(kg, ensure_ascii=False)),
                     ("/*READER*/", READER), ("/*NARR*/", NARR), ("/*EXT*/", EXT)]:
        html = html.replace(tok, val)
    out = os.path.join(OUT, "苇舟江湖梦_深度叙事可视化.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("foresight edges:", len(fores["edges"]), "samples:", len(fores["samples"]),
          "setup章:", fores["nsetup"], "payoff章:", fores["npayoff"])
    print("spacetime locs:", space["nloc"], "chapters:", len(space["chapters"]))
    print("style themes:", style["themes"], "river pts:", len(style["data"]))
    print("KG nodes:", len(kg["nodes"]), "links:", len(kg["links"]),
          f"(char {kg['nchar']}/loc {kg['nloc']}/kw {kg['nkw']})")
    print("written:", out)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>苇舟江湖梦 · 深度叙事可视化</title>
<style>
:root{--bg:#0a0f1c;--panel:rgba(20,32,54,.62);--brd:rgba(90,150,230,.22);--txt:#e8eefc;--muted:#9fb2d4;
  --blue:#3b82f6;--cyan:#22d3ee;--violet:#a78bfa;--amber:#f59e0b;--red:#ef4444;--green:#34d399;}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 700px at 80% -10%,rgba(167,139,250,.16),transparent 60%),
  radial-gradient(900px 600px at 0% 110%,rgba(34,211,238,.12),transparent 55%),var(--bg);
  color:var(--txt);font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",system-ui,sans-serif;line-height:1.6}
.wrap{max-width:1240px;margin:0 auto;padding:28px 22px 80px}
header h1{margin:0;font-size:28px;letter-spacing:2px;background:linear-gradient(90deg,var(--violet),var(--cyan),var(--blue));
  -webkit-background-clip:text;background-clip:text;color:transparent}
header p{margin:6px 0 0;color:var(--muted);font-size:14px}
.nav{margin:10px 0 4px}.nav a{color:var(--cyan);text-decoration:none;font-size:13px;border:1px solid var(--brd);padding:4px 10px;border-radius:8px;margin-right:6px}
.nav a:hover{background:rgba(34,211,238,.12)}
section{background:var(--panel);border:1px solid var(--brd);border-radius:16px;padding:18px;margin-top:20px;
  backdrop-filter:blur(14px);box-shadow:0 10px 40px rgba(0,0,0,.35)}
section h2{margin:0 0 4px;font-size:20px;display:flex;align-items:center;gap:8px}
section h2 .dot{width:12px;height:12px;border-radius:3px}
.sub{color:var(--muted);font-size:13px;margin-bottom:12px}
.chart{width:100%;height:520px}
.samples{margin-top:14px;display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:800px){.samples{grid-template-columns:1fr}}
.scard{background:rgba(6,11,22,.4);border:1px solid rgba(90,150,230,.12);border-radius:10px;padding:10px 12px;font-size:12.5px}
.scard .hd{color:var(--amber);font-weight:700;margin-bottom:4px}
.scard .ev{color:var(--txt);margin:2px 0}.scard .cue{color:var(--red);font-weight:700}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:900px){.two{grid-template-columns:1fr}}
.moc{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:14px}
.moc .grp{background:rgba(6,11,22,.4);border:1px solid rgba(90,150,230,.12);border-radius:10px;padding:8px 12px}
.moc .grp h4{margin:0 0 6px;font-size:13px;color:var(--cyan)}
.moc .grp span{display:inline-block;font-size:12px;color:var(--muted);margin:2px 6px 2px 0}
.hint{color:var(--muted);font-size:12px;margin-top:8px}
a.rdr{color:var(--cyan);text-decoration:none}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>苇舟江湖梦 · 深度叙事可视化</h1>
  <p>在四维流程图与扩展四图之外，再用伏笔回收、时空动画、文风漂移、知识图谱把小说的「隐性纵深」挖到底。全部离线可用。</p>
  <div class="nav">
    <a href="/*NARR*/">← 四维叙事系统</a>
    <a href="/*EXT*/">← 扩展叙事可视化</a>
  </div>
</header>

<section>
  <h2><span class="dot" style="background:var(--amber)"></span>① 伏笔—回收网络</h2>
  <div class="sub">扫描全文，抽「伏笔/悬念」类连词标记 setup 章、『应验/揭晓』类连词标记 payoff 章；仅当两章共享同一角色时连 setup→payoff 边（共 /*FORES_EDGES*/ 条边，涉及 setup 章 /*FORES_NSETUP*/、payoff 章 /*FORES_NPAYOFF*/）。文学因果为推断，例句见下。</div>
  <div class="chart" id="fores"></div>
  <div class="samples" id="samples"></div>
  <div class="hint">伏笔→回收 真实例句（连词红标）：可见悬念如何在后文兑现。</div>
</section>

<section>
  <h2><span class="dot" style="background:var(--cyan)"></span>② 时空动画地图</h2>
  <div class="sub">基于 33 个带坐标地点 + 各章主地点 + 时间层。点击时间轴「播放」，看事件如何在江湖版图上迁移行进（连线＝主地点迁移路径）。</div>
  <div class="chart" id="space" style="height:560px"></div>
</section>

<section>
  <h2><span class="dot" style="background:var(--green)"></span>③ 文风漂移流图</h2>
  <div class="sub">逐章 5 维文体特征（句长/标点密度/对话比/段落数/段均长，已归一化）的 themeRiver 流图——看笔法重心随章窗漂移。</div>
  <div class="chart" id="style" style="height:460px"></div>
</section>

<section>
  <h2><span class="dot" style="background:var(--violet)"></span>④ 知识图谱 + MOC（第二大脑）</h2>
  <div class="sub">聚合 角色/地点/关键词/时代 为分类节点，按共现（角色同场≥6章、角色—地点≥4章、关键词—时代、时代—角色 top3）连边。拖拽漫游，点击类别筛选。</div>
  <div class="moc" id="moc"></div>
  <div class="chart" id="kg" style="height:680px"></div>
</section>

</div>

<script src="echarts.min.js"></script>
<script>
const READER="/*READER*/";
const FORES=/*FORES*/;
const SPACE=/*SPACE*/;
const STYLE=/*STYLE*/;
const KG=/*KG*/;

const AX='#33415c',TXT='#cdd9f0',MUT='#9fb2d0';
const PAL=['#3b82f6','#22d3ee','#a78bfa','#f59e0b','#34d399','#ef4444'];
function tip(){return {trigger:'item',backgroundColor:'rgba(10,15,28,.92)',borderColor:'#33415c',textStyle:{color:TXT}};}

/* ① 伏笔回收 */
(function(){
  const el=document.getElementById('fores');
  const ch=echarts.init(el,null,{renderer:'canvas'});
  const nodesMap={};
  FORES.edges.forEach(e=>{nodesMap[e.a]=1;nodesMap[e.b]=1;});
  const nodes=Object.keys(nodesMap).map(n=>({name:'第'+n+'章',id:n,symbolSize:16,
    itemStyle:{color:'#f59e0b'},label:{show:true,color:TXT,fontSize:11}}));
  const links=FORES.edges.map(e=>({source:e.a,target:e.b,label:{show:true,formatter:e.entity,color:'#ffd9a0',fontSize:10},
    lineStyle:{color:'#f59e0b',width:1.4,curveness:0.2},value:e.entity}));
  ch.setOption({backgroundColor:'transparent',tooltip:tip(),
    series:[{type:'graph',layout:'force',roam:true,force:{repulsion:180,edgeLength:[60,160],gravity:0.06},
      data:nodes,links:links,lineStyle:{opacity:0.7},emphasis:{focus:'adjacency'},
      label:{show:true}}]});
  ch.on('click',p=>{ if(p.data&&p.data.id) window.open(READER+'?loc=ch'+p.data.id,'_blank','noopener'); });
  window.addEventListener('resize',()=>ch.resize());
})();

/* ① 样例 */
(function(){
  document.getElementById('samples').innerHTML=FORES.samples.map(s=>{
    const sa=s.setup.replace(s.ca,'<span class="cue">'+s.ca+'</span>');
    const sb=s.payoff.replace(s.cb,'<span class="cue">'+s.cb+'</span>');
    return '<div class="scard"><div class="hd">第'+s.a+'章 → 第'+s.b+'章 ｜ '+s.entity+'</div>'+
      '<div class="ev">伏：'+sa+'</div><div class="ev">收：'+sb+'</div></div>';
  }).join('');
})();

/* ② 时空动画 */
(function(){
  const el=document.getElementById('space');
  const ch=echarts.init(el,null,{renderer:'canvas'});
  const cmap={}; SPACE.base.forEach(n=>cmap[n.name]={x:n.x,y:n.y});
  const opts=SPACE.chapters.map(cd=>{
    const data=SPACE.base.map(n=>{
      const on=cd.present.includes(n.name);
      const isP=(n.name===cd.primary);
      return {name:n.name,value:[n.x,n.y],
        symbolSize:isP?26:(on?16:9),
        itemStyle:{color:isP?'#f59e0b':(on?'#22d3ee':'rgba(120,140,180,.5)'),
          borderColor:'#0a0f1c',borderWidth:1},
        label:{show:isP||on,color:TXT,fontSize:isP?12:10,position:'right'}};
    });
    const links=[];
    for(let i=1;i<cd.path.length;i++) links.push({coords:[cd.path[i-1],cd.path[i]],
      lineStyle:{color:'#a78bfa',width:2,opacity:0.7,curveness:0.15}});
    return {title:{text:'第'+cd.ch+'章 · '+cd.tl+' · '+cd.primary,left:'center',top:6,textStyle:{color:TXT,fontSize:14}},
      series:[{type:'scatter',data:data,emphasis:{scale:1.3}},
        {type:'lines',coordinateSystem:'cartesian2d',polyline:false,data:links,zlevel:1}]};
  });
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:{trigger:'item',backgroundColor:'rgba(10,15,28,.92)',borderColor:'#33415c',textStyle:{color:TXT},
      formatter:p=> p.data&&p.data.name? (p.data.name+(cmap[p.data.name]?'（坐标 '+cmap[p.data.name].x+','+cmap[p.data.name].y+'）':'')):''},
    grid:{left:20,right:20,top:40,bottom:20},
    xAxis:{type:'value',min:0,max:3000,show:false},
    yAxis:{type:'value',min:0,max:2000,show:false},
    timeline:{axisType:'category',data:SPACE.chapters.map(c=>'第'+c.ch+'章'),
      autoPlay:true,playInterval:900,loop:true,left:30,right:30,bottom:6,
      label:{color:MUT},lineStyle:{color:'#33415c'},itemStyle:{color:'#3b82f6'},
      checkpointStyle:{color:'#f59e0b'},controlStyle:{color:'#cdd9f0'}},
    options:opts
  });
  window.addEventListener('resize',()=>ch.resize());
})();

/* ③ 文风漂移 */
(function(){
  const el=document.getElementById('style');
  const ch=echarts.init(el,null,{renderer:'canvas'});
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:{trigger:'item',backgroundColor:'rgba(10,15,28,.92)',borderColor:'#33415c',textStyle:{color:TXT}},
    legend:{data:STYLE.themes,textStyle:{color:TXT},top:0},
    singleAxis:{type:'category',data:STYLE.data.filter((_,i)=>i%STYLE.themes.length===0).map(d=>d[0]),
      top:30,bottom:30,axisLabel:{color:MUT,interval:5},axisLine:{lineStyle:{color:AX}},
      axisTick:{lineStyle:{color:AX}}},
    series:[{type:'themeRiver',emphasis:{focus:'series'},
      data:STYLE.data,label:{show:false},
      color:['#3b82f6','#22d3ee','#a78bfa','#f59e0b','#34d399']}]
  });
  window.addEventListener('resize',()=>ch.resize());
})();

/* ④ 知识图谱 */
(function(){
  const el=document.getElementById('kg');
  const ch=echarts.init(el,null,{renderer:'canvas'});
  ch.setOption({
    backgroundColor:'transparent',
    tooltip:{...tip(),formatter:p=> p.dataType==='edge'? (p.data.source+' — '+p.data.target):(p.data.name+'（'+(KG.categories[p.data.category]||'')+'）')},
    legend:{data:KG.categories,textStyle:{color:TXT},top:0},
    series:[{type:'graph',layout:'force',roam:true,
      categories:KG.categories.map((c,i)=>({name:c,itemStyle:{color:PAL[i]}})),
      data:KG.nodes,links:KG.links,
      force:{repulsion:120,edgeLength:[40,110],gravity:0.05},
      lineStyle:{opacity:0.5},emphasis:{focus:'adjacency'},
      label:{show:true,color:TXT,fontSize:10}}]
  });
  // MOC
  const counts={角色:KG.nchar,地点:KG.nloc,关键词:KG.nkw,时代:7};
  document.getElementById('moc').innerHTML=KG.categories.map((c,i)=>{
    return '<div class="grp"><h4 style="color:'+PAL[i]+'">'+c+' · '+counts[c]+'</h4>'+
      '<span>点击下方图谱中对应颜色节点查看</span></div>';
  }).join('');
  window.addEventListener('resize',()=>ch.resize());
})();
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
