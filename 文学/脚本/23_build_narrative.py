# -*- coding: utf-8 -*-
"""
23_build_narrative.py
======================
可视化叙事系统构建器。

从 `数据/chapter_data/all_tags.json` 抽取四个叙事维度：
  D1 剧情推进脉络  story_arc      (状态转移图，节点=剧情弧，边=章节间弧切换，带频次)
  D2 角色情感曲线  emotion_line   (状态转移图，节点=情感状态，边=章节间情感切换)
  D3 场景空间切换  main_locations (主地点迁移图，节点=高频地点，边=连续章主地点迁移)
  D4 时间线演进    time_layer     (时序链，节点=时间层，边=章节间时间推移，回溯用虚线)

并构建「立体交叉引用 / Nexus」索引：
  - 每个节点携带其覆盖的全部章节（用于点击联动高亮其它维度图）
  - 识别多维度同时达峰的「枢纽章」(nexus)，点击可在四张图中同时定位

产物：
  产物/苇舟江湖梦_可视化叙事系统.html   (离线可交互单页，内嵌 Mermaid)
  数据/narrative_graphs.json           (透明数据，便于审查)
"""
import json, os, re
from collections import Counter, OrderedDict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "数据")
OUT  = os.path.join(BASE, "产物")

READER = "苇舟江湖梦_原文阅读.html"

def load():
    with open(os.path.join(DATA, "chapter_data", "all_tags.json"), encoding="utf-8") as f:
        d = json.load(f)
    d.sort(key=lambda c: c["chapter"])
    return d

def fmt_range(chs):
    """把有序章节列表压成紧凑区间字符串：1,3-7,10"""
    chs = sorted(set(chs))
    if not chs:
        return "—"
    parts, start, prev = [], chs[0], chs[0]
    for x in chs[1:]:
        if x == prev + 1:
            prev = x
        else:
            parts.append(f"{start}" if start == prev else f"{start}-{prev}")
            start = prev = x
    parts.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ",".join(parts)

def value_nodes(values):
    """按首次出现顺序去重，返回 [(value, chapters)]"""
    seen, nodes = OrderedDict(), []
    for c, v in values:
        seen.setdefault(v, []).append(c)
    for v, chs in seen.items():
        nodes.append((v, chs))
    return nodes

def trans_edges(values):
    """连续章状态切换计数：(src,dst)->[count, [target_chapters]]"""
    edges = {}
    for i in range(len(values) - 1):
        a, b = values[i][1], values[i + 1][1]
        if a == b:
            continue
        key = (a, b)
        e = edges.get(key)
        if not e:
            e = edges[key] = [0, []]
        e[0] += 1
        e[1].append(values[i + 1][0])
    return edges

def build_graph(graph_id, title, dim, values, layout, start_label, edge_kind="weight"):
    """通用构建：value 节点 + 切换边。
    edge_kind: 'weight' 普通加权边; 'time' 时序边(回溯用虚线)。"""
    nodes = value_nodes(values)               # [(value, chapters)]
    edges = trans_edges(values)
    # 分配 ascii 节点 id（同一图内值唯一）
    v2id = {v: f"{graph_id[0]}{i}" for i, (v, _) in enumerate(nodes)}
    node_defs, edge_defs = [], []
    for v, chs in nodes:
        nid = v2id[v]
        label = f'{v}<br/>‹{len(chs)}章›'
        node_defs.append(f'    {nid}["{label}"]')
    # 起始桩
    first_id = v2id[nodes[0][0]]
    node_defs.insert(0, f'    S{graph_id[0]}([{start_label}])')
    edge_defs.append(f'    S{graph_id[0]} --> {first_id}')
    canon_idx = None
    if edge_kind == "time":
        canon_idx = {v: i for i, v in enumerate(dim)}  # dim 在此作为 canonical 顺序
    for (a, b), (cnt, chs) in edges.items():
        arrow = "-->"
        lab = f'"×{cnt}"'
        if edge_kind == "time" and canon_idx:
            if canon_idx[b] < canon_idx[a]:
                arrow = "-.->"
                lab = '"回溯"'
        edge_defs.append(f'    {v2id[a]} {arrow}|{lab}| {v2id[b]}')
    src = [f"flowchart {layout}"] + node_defs + edge_defs
    src = "\n".join(src)
    # 输出结构
    out_nodes = [{"id": v2id[v], "value": v, "chapters": chs, "count": len(chs)} for v, chs in nodes]
    out_edges = []
    for (a, b), (cnt, chs) in edges.items():
        out_edges.append({"src": v2id[a], "dst": v2id[b], "value_src": a, "value_dst": b,
                          "count": cnt, "chapters": chs, "back": (edge_kind == "time" and canon_idx and canon_idx[b] < canon_idx[a])})
    return {"id": graph_id, "title": title, "dim": dim if isinstance(dim, str) else "time_layer",
            "layout": layout, "source": src,
            "nodes": out_nodes, "edges": out_edges}

def main():
    data = load()
    n = len(data)
    pairs = lambda key: [(c["chapter"], c.get(key)) for c in data]
    canon_time = ["初入江湖", "江湖历练", "庙堂初涉", "乱世将起", "战乱爆发", "大战/决战", "战后格局"]

    # ---- D1 剧情推进 ----
    g1 = build_graph("g1", "剧情推进脉络", "story_arc", pairs("story_arc"), "TD", "开篇")

    # ---- D2 情感曲线 ----
    g2 = build_graph("g2", "角色情感曲线", "emotion_line", pairs("emotion_line"), "LR", "序章")

    # ---- D3 场景空间切换（主地点迁移）----
    # 主地点 = main_locations[0]
    prim = [(c["chapter"], (c.get("main_locations") or [None])[0]) for c in data]
    # 全局地点频次 -> top14
    freq = Counter()
    for c in data:
        for l in (c.get("main_locations") or []):
            if l:
                freq[l] += 1
    top_loc = [l for l, _ in freq.most_common(14)]
    if "望岳镇" in freq and "望岳镇" not in top_loc:
        top_loc.append("望岳镇")
    top_set = set(top_loc)
    # 迁移边只在 top 集合内
    edges3 = {}
    for i in range(n - 1):
        a = prim[i][1]; b = prim[i + 1][1]
        if not a or not b or a == b:
            continue
        if a not in top_set or b not in top_set:
            continue
        key = (a, b)
        e = edges3.get(key)
        if not e:
            e = edges3[key] = [0, []]
        e[0] += 1; e[1].append(prim[i + 1][0])
    # 节点：top 地点，章节=该地点出现在 main_locations 的章
    loc_chapters = {}
    for c in data:
        for l in (c.get("main_locations") or []):
            if l:
                loc_chapters.setdefault(l, []).append(c["chapter"])
    nodes3 = [(l, loc_chapters[l]) for l in top_loc if l in loc_chapters]
    v2id3 = {v: f"l{i}" for i, (v, _) in enumerate(nodes3)}
    node_defs3, edge_defs3 = [], []
    for v, chs in nodes3:
        node_defs3.append(f'    {v2id3[v]}["{v}<br/>‹{len(chs)}章›"]')
    node_defs3.insert(0, '    Sl([启程·望岳镇])')
    edge_defs3.append(f'    Sl --> {v2id3[nodes3[0][0]]}')
    for (a, b), (cnt, chs) in edges3.items():
        edge_defs3.append(f'    {v2id3[a]} -->|"×{cnt}"| {v2id3[b]}')
    src3 = "\n".join(["flowchart LR"] + node_defs3 + edge_defs3)
    g3 = {"id": "g3", "title": "场景空间切换", "dim": "main_locations", "layout": "LR",
          "source": src3,
          "nodes": [{"id": v2id3[v], "value": v, "chapters": chs, "count": len(chs)} for v, chs in nodes3],
          "edges": [{"src": v2id3[a], "dst": v2id3[b], "value_src": a, "value_dst": b,
                     "count": cnt, "chapters": chs, "back": False} for (a, b), (cnt, chs) in edges3.items()]}

    # ---- D4 时间线演进 ----
    g4 = build_graph("g4", "时间线演进", canon_time, pairs("time_layer"), "LR", "纪元之初", edge_kind="time")

    graphs = [g1, g2, g3, g4]

    # ---- Nexus 枢纽章：多维度同时达峰 ----
    nexus = []
    for c in data:
        ci = c.get("combat_intensity", 0)
        em = c.get("emotion_line", "")
        arc = c.get("story_arc", "")
        tl = c.get("time_layer", "")
        ctype = c.get("chapter_type", []) or []
        flags = {
            "ci3": ci == 3,
            "tragic": em in ("虐/悲情", "分离/离别"),
            "war": arc == "主线·川阴王叛乱/战争",
            "wartime": tl in ("战乱爆发", "大战/决战"),
            "casualty": "悲剧/伤亡" in ctype,
        }
        score = sum(flags.values())
        if score >= 3:
            nexus.append({
                "ch": c["chapter"], "arc": arc, "emo": em, "loc": (c.get("main_locations") or [None])[0],
                "tl": tl, "ci": ci, "flags": flags, "score": score,
                "key": c.get("key_events", ""),
                "chars": c.get("characters_present", [])[:6],
            })
    nexus.sort(key=lambda x: (-x["score"], x["ch"]))

    # ---- 维度值 -> 节点 id 反查（用于 nexus 定位）----
    dim_value_to_node = {}
    for g in graphs:
        m = {}
        for nd in g["nodes"]:
            m[nd["value"]] = nd["id"]
        dim_value_to_node[g["id"]] = m

    bundle = {
        "graphs": graphs,
        "nexus": nexus,
        "dim_value_to_node": dim_value_to_node,
        "reader": READER,
        "meta": {"chapters": n, "nexus_count": len(nexus)},
    }
    with open(os.path.join(DATA, "narrative_graphs.json"), "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=1)

    # ---- 写出 HTML ----
    html = render_html(bundle)
    with open(os.path.join(OUT, "苇舟江湖梦_可视化叙事系统.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # 统计输出
    print("graphs:", [(g['id'], len(g['nodes']), len(g['edges'])) for g in graphs])
    print("nexus chapters:", len(nexus), [x['ch'] for x in nexus])
    print("top locations:", top_loc)
    print("written:", os.path.join(OUT, "苇舟江湖梦_可视化叙事系统.html"))

def render_html(bundle):
    g = bundle["graphs"]
    sources = "\n\n".join(f'<div class="flow-host" id="host_{x["id"]}"><pre class="mermaid">\n{x["source"]}\n</pre></div>' for x in g)
    graphs_json = json.dumps(bundle["graphs"], ensure_ascii=False)
    nexus_json = json.dumps(bundle["nexus"], ensure_ascii=False)
    dv_json = json.dumps(bundle["dim_value_to_node"], ensure_ascii=False)
    reader = bundle["reader"]

    nexus_rows = []
    for x in bundle["nexus"]:
        chips = []
        for k, label in [("ci3", "战力峰值"), ("tragic", "悲情"), ("war", "叛乱主线"), ("wartime", "战乱"), ("casualty", "伤亡")]:
            if x["flags"][k]:
                chips.append(f'<span class="chip chip-on">{label}</span>')
        key = x["key"]
        if len(key) > 46:
            key = key[:46] + "…"
        nexus_rows.append(f'''<tr data-ch="{x['ch']}">
          <td class="cch">ch{x['ch']}</td>
          <td>{x['tl']}</td>
          <td>{x['arc']}</td>
          <td>{x['emo']}</td>
          <td>{x['loc'] or '—'}</td>
          <td class="ci{x['ci']}">L{x['ci']}</td>
          <td class="chips">{"".join(chips)}</td>
          <td class="key" title="{x['key']}">{key}</td>
          <td><button class="locate" data-ch="{x['ch']}">◎ 立体定位</button>
              <a class="rdr" href="{reader}?loc=ch{x['ch']}" target="_blank" rel="noopener">读原文</a></td>
        </tr>''')
    nexus_table = "\n".join(nexus_rows)

    captions = {
        "g1": "节点＝剧情弧（主线/支线）；连线＝相邻章节间的弧线切换，标注<b>×切换次数</b>。纵向展开叙事主脉的更迭与交织。",
        "g2": "节点＝情感状态；连线＝相邻章节间的情感迁移，标注切换次数。横向铺开角色情绪起伏的波动节律。",
        "g3": "节点＝高频场景地点（‹出现章数›）；连线＝连续章节间的<b>主地点迁移</b>，标注迁移次数。呈现空间行程与枢纽。",
        "g4": "节点＝时间层（按史序排列）；实线＝时间推进，<b>虚线＝时间回溯</b>（非线性叙事）。构成全书时间脊柱。",
    }
    cap_html = "".join(f'<p class="cap" data-for="{x["id"]}">{captions[x["id"]]}</p>' for x in g)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>苇舟江湖梦 · 可视化叙事系统</title>
<style>
:root{{
  --bg:#0a0f1c; --bg2:#0e1626; --panel:rgba(20,32,54,.62); --panel-brd:rgba(90,150,230,.22);
  --txt:#e8eefc; --muted:#9fb2d4; --blue:#3b82f6; --cyan:#22d3ee; --violet:#a78bfa;
  --amber:#f59e0b; --red:#ef4444; --green:#34d399; --glass:blur(14px);
}}
*{{box-sizing:border-box}}
body{{margin:0;background:radial-gradient(1200px 700px at 80% -10%,rgba(59,130,246,.18),transparent 60%),
  radial-gradient(900px 600px at 0% 110%,rgba(167,139,250,.14),transparent 55%),var(--bg);
  color:var(--txt);font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",system-ui,sans-serif;line-height:1.6;}}
.wrap{{max-width:1280px;margin:0 auto;padding:28px 22px 80px}}
header h1{{margin:0;font-size:30px;letter-spacing:2px;
  background:linear-gradient(90deg,var(--cyan),var(--blue),var(--violet));-webkit-background-clip:text;background-clip:text;color:transparent}}
header p{{margin:6px 0 0;color:var(--muted);font-size:14px}}
.legend{{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 6px}}
.legend span{{font-size:13px;padding:5px 12px;border-radius:20px;border:1px solid var(--panel-brd);
  background:var(--panel);backdrop-filter:var(--glass)}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px;vertical-align:middle}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:14px}}
@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
.card{{background:var(--panel);border:1px solid var(--panel-brd);border-radius:16px;
  padding:16px 16px 8px;backdrop-filter:var(--glass);box-shadow:0 10px 40px rgba(0,0,0,.35)}}
.card h2{{margin:0 0 4px;font-size:18px;display:flex;align-items:center;gap:8px}}
.card h2 .dot{{width:12px;height:12px;border-radius:3px}}
.card .cap{{margin:2px 0 10px;font-size:12.5px;color:var(--muted)}}
.flow-host{{overflow:auto;max-height:520px;border-radius:10px;background:rgba(6,11,22,.45);
  border:1px solid rgba(90,150,230,.12);padding:6px}}
.cap[data-for]{{display:none}}
.cap.show{{display:block}}
pre.mermaid{{background:transparent;margin:0}}
/* (placeholder removed) */
/* mermaid node highlight */
.nx-hl{{outline:3px solid var(--amber)!important;outline-offset:2px;filter:drop-shadow(0 0 8px var(--amber))}}
.nx-hl-weak{{outline:2px dashed rgba(245,158,11,.6)!important;outline-offset:2px}}
/* nexus */
.nexus{{margin-top:26px;background:var(--panel);border:1px solid var(--panel-brd);border-radius:16px;
  padding:18px;backdrop-filter:var(--glass)}}
.nexus h2{{margin:0 0 4px;font-size:20px}}
.nexus .sub{{color:var(--muted);font-size:13px;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{padding:7px 8px;text-align:left;border-bottom:1px solid rgba(90,150,230,.12)}}
th{{color:var(--cyan);font-weight:600;font-size:12px;letter-spacing:.5px}}
tr:hover td{{background:rgba(59,130,246,.08)}}
.cch{{color:var(--violet);font-weight:700}}
.ci3{{color:var(--red);font-weight:700}} .ci2{{color:var(--amber)}} .ci1{{color:var(--green)}} .ci0{{color:var(--muted)}}
.chips .chip{{font-size:11px;padding:2px 7px;border-radius:10px;margin-right:3px}}
.chip-on{{background:rgba(239,68,68,.18);color:#ffb4b4;border:1px solid rgba(239,68,68,.4)}}
.key{{color:var(--muted);max-width:340px}}
button.locate{{background:linear-gradient(90deg,var(--blue),var(--violet));color:#fff;border:0;
  border-radius:8px;padding:5px 10px;cursor:pointer;font-size:12px}}
button.locate:hover{{filter:brightness(1.12)}}
a.rdr{{margin-left:6px;color:var(--cyan);text-decoration:none;font-size:12px}}
a.rdr:hover{{text-decoration:underline}}
/* side info */
#info{{position:fixed;right:18px;bottom:18px;width:300px;background:var(--panel);border:1px solid var(--panel-brd);
  border-radius:14px;padding:14px;backdrop-filter:var(--glass);box-shadow:0 12px 40px rgba(0,0,0,.5);
  font-size:13px;display:none;z-index:50}}
#info h3{{margin:0 0 6px;font-size:15px;color:var(--cyan)}}
#info .row{{color:var(--muted);margin:3px 0}}
#info .chaps{{color:var(--txt);word-break:break-all;font-size:12px}}
#info a{{color:var(--violet)}}
#info .clo{{float:right;cursor:pointer;color:var(--muted)}}
.hint{{font-size:12px;color:var(--muted);margin:8px 0 0}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>苇舟江湖梦 · 可视化叙事系统</h1>
  <p>以流程图呈现「剧情推进 · 情感变化 · 地点转移 · 时间流逝」四维度的状态变迁与转换关系；点击任意节点可在其余三张图中联动高亮其共现章节，点击枢纽章可在四图同步定位——立体交织故事结构与节奏。</p>
</header>

<div class="legend">
  <span><i style="background:var(--blue)"></i>剧情推进脉络（D1）</span>
  <span><i style="background:var(--cyan)"></i>角色情感曲线（D2）</span>
  <span><i style="background:var(--violet)"></i>场景空间切换（D3）</span>
  <span><i style="background:var(--amber)"></i>时间线演进（D4）</span>
</div>

<div class="grid">
  <div class="card">
    <h2><span class="dot" style="background:var(--blue)"></span>① 剧情推进脉络</h2>
    <div class="cap" data-for="g1"></div>
    <div class="flow-host" id="host_g1"></div>
  </div>
  <div class="card">
    <h2><span class="dot" style="background:var(--cyan)"></span>② 角色情感曲线</h2>
    <div class="cap" data-for="g2"></div>
    <div class="flow-host" id="host_g2"></div>
  </div>
  <div class="card">
    <h2><span class="dot" style="background:var(--violet)"></span>③ 场景空间切换</h2>
    <div class="cap" data-for="g3"></div>
    <div class="flow-host" id="host_g3"></div>
  </div>
  <div class="card">
    <h2><span class="dot" style="background:var(--amber)"></span>④ 时间线演进</h2>
    <div class="cap" data-for="g4"></div>
    <div class="flow-host" id="host_g4"></div>
  </div>
</div>
<div class="hint">提示：点击任一流程图节点 → 右侧信息卡显示其覆盖章节，并在其余三张图中高亮<b>共现章节</b>；点击枢纽章「◎ 立体定位」→ 四图同时聚焦该章所在节点。<span id="capToggle" style="cursor:pointer;color:var(--cyan)"> ［显示/隐藏全部维度说明］</span></div>

<div class="nexus">
  <h2>立体交叉引用 · 枢纽章 Nexus</h2>
  <div class="sub">以下章节在多维度同时达峰（战力峰值 / 悲情 / 叛乱主线 / 战乱 / 伤亡 中 ≥3 项叠加），是全书的戏剧枢纽。点击「◎ 立体定位」在四张流程图中同步锚定该章的剧情弧、情感、地点与时间节点。</div>
  <table>
    <thead><tr><th>章</th><th>时间层</th><th>剧情弧</th><th>情感</th><th>主地点</th><th>战力</th><th>叠加维度</th><th>关键事件</th><th>操作</th></tr></thead>
    <tbody>
{nexus_table}
    </tbody>
  </table>
</div>
</div>

<div id="info">
  <span class="clo" onclick="closeInfo()">✕</span>
  <h3 id="infoTitle">节点详情</h3>
  <div id="infoBody"></div>
  <a id="infoReader" href="#" target="_blank" rel="noopener">打开原文阅读器 →</a>
</div>

<script src="mermaid.min.js"></script>
<script>
const GRAPHS = {graphs_json};
const NEXUS = {nexus_json};
const DV2N = {dv_json};
const READER = "{reader}";
const capMap = {json.dumps(captions, ensure_ascii=False)};

/* 初始化 Mermaid（离线，base 主题 + 科技蓝变量） */
mermaid.initialize({{
  startOnLoad:false, securityLevel:'loose', theme:'base',
  themeVariables:{{
    background:'transparent', primaryColor:'rgba(30,48,80,.85)', primaryTextColor:'#e8eefc',
    primaryBorderColor:'#3b82f6', lineColor:'#5a96e6', secondaryColor:'rgba(34,211,238,.18)',
    tertiaryColor:'rgba(167,139,250,.18)', fontFamily:'"PingFang SC","Microsoft YaHei",sans-serif',
    fontSize:'14px'
  }},
  flowchart:{{ curve:'basis', htmlLabels:true, nodeSpacing:38, rankSpacing:46 }}
}});

/* 注入 mermaid 源 */
GRAPHS.forEach(g=>{{
  const host=document.getElementById('host_'+g.id);
  const pre=document.createElement('pre');
  pre.className='mermaid'; pre.textContent=g.source;
  host.appendChild(pre);
}});

/* 节点文本 -> nid 反查表（渲染后建立） */
const labelToNid = {{}};
function buildLabelIndex(){{
  GRAPHS.forEach(g=>{{
    labelToNid[g.id] = {{}};
    const svg=document.querySelector('#host_'+g.id+' svg');
    if(!svg) return;
    svg.querySelectorAll('g.node').forEach(node=>{{
      const t=node.querySelector('.nodeLabel');
      const txt=(t?t.textContent:'').replace(/\\s+/g,'');
      for(const nd of g.nodes){{
        if(txt.includes(nd.value.replace(/\\s+/g,''))){{
          node.dataset.nid=nd.id;
          labelToNid[g.id][nd.id]=node;
          break;
        }}
      }}
    }});
  }});
}}

function clearHighlight(){{
  document.querySelectorAll('.nx-hl,.nx-hl-weak').forEach(e=>e.classList.remove('nx-hl','nx-hl-weak'));
}}

/* 点击节点：联动高亮共现章节 */
function selectNode(gid, nid){{
  const g=GRAPHS.find(x=>x.id===gid);
  const nd=g.nodes.find(x=>x.id===nid);
  if(!nd) return;
  clearHighlight();
  const chSet=new Set(nd.chapters);
  // 本图高亮
  const self=labelToNid[gid] && labelToNid[gid][nid];
  if(self) self.classList.add('nx-hl');
  // 其它图：按章节交集高亮
  let maxOv=0;
  const ov={{}};
  GRAPHS.forEach(og=>{{
    if(og.id===gid) return;
    og.nodes.forEach(on=>{{
      const inter=on.chapters.filter(c=>chSet.has(c)).length;
      if(inter>0){{ ov[og.id]=ov[og.id]||{{}}; ov[og.id][on.id]=inter; maxOv=Math.max(maxOv,inter); }}
    }});
  }});
  GRAPHS.forEach(og=>{{
    if(og.id===gid) return;
    Object.entries(ov[og.id]||{{}}).forEach(([id,c])=>{{
      const el=labelToNid[og.id] && labelToNid[og.id][id];
      if(el) el.classList.add(c>=Math.max(2,Math.ceil(maxOv*0.6))?'nx-hl':'nx-hl-weak');
    }});
  }});
  showInfo(g.title, nd.value, nd.chapters, nd.count, '维度节点');
}}

/* nexus 立体定位 */
function locateNexus(ch){{
  clearHighlight();
  const x=NEXUS.find(n=>n.ch===ch);
  if(!x) return;
  const map={{g1:x.arc, g2:x.emo, g3:x.loc, g4:x.tl}};
  Object.entries(map).forEach(([gid,val])=>{{
    const nid=DV2N[gid] && DV2N[gid][val];
    if(!nid) return;
    const el=labelToNid[gid] && labelToNid[gid][nid];
    if(el){{ el.classList.add('nx-hl'); el.scrollIntoView({{block:'center',behavior:'smooth'}}); }}
  }});
  const chips=Object.entries(x.flags).filter(([k,v])=>v).map(([k])=>k).join('、');
  showInfo('枢纽章 ch'+ch, x.arc+' / '+x.emo, [ch], 1,
    '时间层：'+x.tl+' ｜ 主地点：'+(x.loc||'—')+' ｜ 战力：L'+x.ci+' ｜ 叠加：'+chips, x.key);
}}

/* 信息卡 */
function showInfo(title, value, chapters, count, dimLabel, key){{
  const box=document.getElementById('info');
  document.getElementById('infoTitle').textContent=title;
  let html=`<div class="row">维度值：<b style="color:var(--txt)">${{value}}</b></div>`;
  html+=`<div class="row">${{dimLabel}} ｜ 覆盖 <b style="color:var(--cyan)">${{count}}</b> 章</div>`;
  html+=`<div class="row">章节：</div><div class="chaps">${{fmtRange(chapters)}}</div>`;
  if(key) html+=`<div class="row" style="margin-top:6px">关键：${{key}}</div>`;
  document.getElementById('infoBody').innerHTML=html;
  const first=chapters&&chapters.length?chapters[0]:1;
  document.getElementById('infoReader').href=READER+'?loc=ch'+first;
  box.style.display='block';
}}
function closeInfo(){{ document.getElementById('info').style.display='none'; }}
function fmtRange(chs){{
  chs=[...new Set(chs)].sort((a,b)=>a-b); if(!chs.length) return '—';
  let parts=[],s=chs[0],p=chs[0];
  for(const x of chs.slice(1)){{ if(x===p+1){{p=x;}} else {{parts.push(s===p?s:s+'-'+p);s=p=x;}} }}
  parts.push(s===p?s:s+'-'+p); return parts.join(',');
}}

/* 事件委托：节点点击 */
GRAPHS.forEach(g=>{{
  const host=document.getElementById('host_'+g.id);
  host.addEventListener('click', e=>{{
    const node=e.target.closest('g.node');
    if(node && node.dataset.nid) selectNode(g.id, node.dataset.nid);
  }});
}});
document.querySelectorAll('button.locate').forEach(b=>{{
  b.addEventListener('click', ()=>locateNexus(parseInt(b.dataset.ch,10)));
}});

/* 维度说明显隐 */
let capsShown=false;
document.getElementById('capToggle').addEventListener('click', ()=>{{
  capsShown=!capsShown;
  document.querySelectorAll('.cap[data-for]').forEach(c=>c.classList.toggle('show',capsShown));
}});

/* 渲染 */
(async function(){{
  try{{ await mermaid.run(); }}catch(e){{ console.error('mermaid run failed', e); }}
  buildLabelIndex();
  // 兜底补全：若某图索引缺失再补一次
  setTimeout(buildLabelIndex, 400);
}})();
</script>
<script>
/* 把维度说明文本填入对应卡片 */
(function(){{
  GRAPHS.forEach(g=>{{
    const cap=document.querySelector('.cap[data-for="'+g.id+'"]');
    if(cap) cap.innerHTML=capMap[g.id];
  }});
}})();
</script>
</body>
</html>'''


if __name__ == "__main__":
    main()
