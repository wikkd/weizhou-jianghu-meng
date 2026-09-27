#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取 knowledge_base.json，生成零依赖单文件 index.html（JSON 内联，可离线打开）。"""
import json, os

OUTDIR = os.path.dirname(os.path.abspath(__file__))
kb = json.load(open(os.path.join(OUTDIR, "knowledge_base.json"), encoding="utf-8"))
KB_JSON = json.dumps(kb, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>苇舟江湖梦 · 知识性索引数据库</title>
<style>
:root{
  --bg:#f5f8fc; --panel:#ffffff; --ink:#1f2a37; --muted:#6b7a90;
  --line:#e2e9f3; --blue:#2f6fed; --blue2:#e8f0fe; --accent:#0f9d8b;
  --warn:#e0823d; --pink:#d6467e; --gold:#caa24a;
  --shadow:0 1px 3px rgba(31,42,55,.08),0 6px 20px rgba(31,42,55,.06);
}
*{box-sizing:border-box}
body{margin:0;font-family:"Noto Sans CJK SC","Microsoft YaHei",system-ui,-apple-system,sans-serif;
  background:var(--bg);color:var(--ink);font-size:14px;line-height:1.6}
header{background:linear-gradient(120deg,#2f6fed,#0f9d8b);color:#fff;padding:18px 24px;box-shadow:var(--shadow)}
header h1{margin:0;font-size:20px;letter-spacing:1px}
header .sub{opacity:.9;font-size:12px;margin-top:2px}
.wrap{max-width:1180px;margin:0 auto;padding:18px 20px 60px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:16px 0}
.tab{padding:8px 16px;border:1px solid var(--line);background:var(--panel);border-radius:10px;cursor:pointer;color:var(--muted);font-weight:600}
.tab.active{background:var(--blue);color:#fff;border-color:var(--blue)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow);margin-bottom:16px}
.grid{display:grid;gap:14px}
.g4{grid-template-columns:repeat(4,1fr)}
.g3{grid-template-columns:repeat(3,1fr)}
.g2{grid-template-columns:repeat(2,1fr)}
@media(max-width:820px){.g4,.g3,.g2{grid-template-columns:1fr 1fr}}
.stat{background:var(--blue2);border-radius:12px;padding:14px}
.stat .n{font-size:26px;font-weight:800;color:var(--blue)}
.stat .l{color:var(--muted);font-size:12px}
h2{font-size:16px;margin:0 0 12px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--muted);font-weight:700;cursor:pointer;user-select:none;position:relative}
tbody tr:hover{background:#f0f6ff}
.chip{display:inline-block;padding:2px 9px;border-radius:20px;font-size:12px;margin:2px;background:var(--blue2);color:var(--blue);border:1px solid #cfe0fb}
.chip.主{background:#fff0f5;color:var(--pink);border-color:#f6c9dc}
.chip.配{background:#eafaf6;color:var(--accent);border-color:#bfe9df}
.chip.待定{background:#f1f3f7;color:var(--muted);border-color:var(--line)}
.tag{display:inline-block;padding:1px 8px;border-radius:6px;font-size:11px;background:#eef2f8;color:var(--muted);margin:1px}
.search{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:10px;font-size:14px;outline:none}
.search:focus{border-color:var(--blue)}
.row{cursor:pointer}
.detail{background:#fafcff;border:1px dashed var(--line);border-radius:10px;padding:12px;margin-top:8px}
.heat{display:flex;flex-wrap:wrap;gap:3px;margin-top:8px}
.cell{width:20px;height:20px;border-radius:3px;font-size:9px;display:flex;align-items:center;justify-content:center;color:#fff;cursor:default}
.muted{color:var(--muted)}
.small{font-size:12px}
svg text{font-family:inherit}
.drawer{position:fixed;top:0;right:0;height:100%;width:420px;max-width:92vw;background:#fff;box-shadow:-8px 0 30px rgba(0,0,0,.15);transform:translateX(100%);transition:.25s;z-index:50;overflow:auto;padding:18px}
.drawer.open{transform:translateX(0)}
.mask{position:fixed;inset:0;background:rgba(20,30,45,.25);display:none;z-index:40}
.mask.open{display:block}
.close{float:right;cursor:pointer;color:var(--muted);font-size:20px;border:none;background:none}
.legend{font-size:11px;color:var(--muted);margin-top:6px}
a.k{color:var(--blue);cursor:pointer;text-decoration:underline}
</style>
</head>
<body>
<header>
  <h1>苇舟江湖梦 · 知识性索引数据库</h1>
  <div class="sub" id="hdrsub"></div>
</header>
<div class="wrap">
  <div class="tabs">
    <div class="tab active" data-v="overview">概览</div>
    <div class="tab" data-v="chars">人物</div>
    <div class="tab" data-v="chapters">章节</div>
    <div class="tab" data-v="rel">关系</div>
    <div class="tab" data-v="search">检索</div>
  </div>
  <div id="view"></div>
</div>
<div class="mask" id="mask"></div>
<div class="drawer" id="drawer"><button class="close" onclick="closeDrawer()">×</button><div id="drawerBody"></div></div>

<script id="kbdata" type="application/json">__KB_JSON__</script>
<script>
const KB = JSON.parse(document.getElementById('kbdata').textContent);
const C = KB.characters, CH = KB.chapters, RL = KB.relations_known, RC = KB.relations_cooccur;
const view = document.getElementById('view');
document.getElementById('hdrsub').textContent =
  '作者：'+KB.meta.author+' ｜ '+KB.meta.chapter_count+'章（含自序）｜ 约'+(CH.reduce((a,c)=>a+c.chars,0)/10000).toFixed(1)+'万字 ｜ 人物'+Object.keys(C).length+'名';

function el(html){const d=document.createElement('div');d.innerHTML=html;return d.firstElementChild;}
function chrName(i){return CH[i]?CH[i].title:('?');}

/* ---------- 概览 ---------- */
function vOverview(){
  const top = Object.entries(C).sort((a,b)=>b[1].total_mentions-a[1].total_mentions).slice(0,10);
  const maxM = top[0][1].total_mentions;
  let bars = top.map(([n,p])=>{
    const w=(p.total_mentions/maxM*100).toFixed(1);
    return `<div style="display:flex;align-items:center;gap:8px;margin:5px 0">
      <div style="width:64px;text-align:right" class="small">${n}</div>
      <div style="flex:1;background:#eef2f8;border-radius:6px;height:18px;overflow:hidden">
        <div style="width:${w}%;height:100%;background:linear-gradient(90deg,#2f6fed,#0f9d8b)"></div></div>
      <div style="width:54px" class="small">${p.total_mentions}</div></div>`;
  }).join('');
  // chapter length sparkline (svg)
  const lens = CH.map(c=>c.chars);
  const W=1100,H=120,max=Math.max(...lens);
  const pts = CH.map((c,i)=>[ (i/(CH.length-1))*W, H-(c.chars/max)*H ]);
  const path = pts.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  const svg = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="background:#fafcff;border-radius:8px">
    <path d="${path}" fill="none" stroke="#2f6fed" stroke-width="2"/>
    ${pts.map((p,i)=> i%6===0?`<circle cx="${p[0]}" cy="${p[1]}" r="2.5" fill="#0f9d8b"/>`:'').join('')}
    </svg>`;
  view.innerHTML = `
  <div class="grid g4">
    <div class="stat"><div class="n">${KB.meta.chapter_count}</div><div class="l">章节（含自序）</div></div>
    <div class="stat"><div class="n">${Object.keys(C).length}</div><div class="l">已索引人物</div></div>
    <div class="stat"><div class="n">${(CH.reduce((a,c)=>a+c.chars,0)/10000).toFixed(1)}万</div><div class="l">正文字数</div></div>
    <div class="stat"><div class="n">${RC.length}</div><div class="l">共现关系边</div></div>
  </div>
  <div class="card"><h2>人物提及 TOP10</h2>${bars}</div>
  <div class="card"><h2>章节字数分布</h2>${svg}
    <div class="legend">每点≈6章，纵轴为字数；高耸处为关键大章（如二十、三十四、三十七、四十四章）。</div></div>`;
}

/* ---------- 人物 ---------- */
let sortKey='total_mentions', sortAsc=false;
function vChars(){
  const rows = Object.entries(C).sort((a,b)=>{
    let x=a[1][sortKey], y=b[1][sortKey];
    if(typeof x==='string'){return sortAsc?x.localeCompare(y):y.localeCompare(x);}
    return sortAsc? x-y : y-x;
  });
  let tr = rows.map(([n,p])=>`<tr class="row" onclick="openChar('${n}')">
    <td><b>${n}</b></td><td><span class="chip ${p.role}">${p.role}</span></td>
    <td>${p.side}</td><td>${p.total_mentions}</td><td>${p.chapter_count}</td>
    <td>${chrName(p.first_chapter)}</td><td>${chrName(p.last_chapter)}</td></tr>`).join('');
  view.innerHTML = `<div class="card"><h2>人物花名册（点击查看出场时间线）</h2>
   <table><thead><tr>
     <th data-k="name">姓名</th><th data-k="role">角色</th><th data-k="side">阵营</th>
     <th data-k="total_mentions">提及</th><th data-k="chapter_count">出场章</th>
     <th data-k="first_chapter">首出场</th><th data-k="last_chapter">末出场</th></tr></thead>
   <tbody>${tr}</tbody></table></div>`;
  view.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{
    const k=th.dataset.k; if(k==='name'||k==='role'||k==='side'){sortKey=k;}
    else sortKey=k; sortAsc=!sortAsc; vChars();
  });
}

function openChar(name){
  const p=C[name];
  const nch=CH.length;
  const cells = CH.map((c,i)=>{
    const n=p.timeline.find(t=>t.ch===i);
    if(!n) return `<div class="cell" style="background:#eef2f8;color:#c2ccda" title="${c.title}：未出场">·</div>`;
    const v=Math.min(1, Math.log(n.n+1)/Math.log(40));
    const bg=`rgb(${Math.round(47+v*180)},${Math.round(111+v*60)},${Math.round(237-v*150)})`;
    return `<div class="cell" style="background:${bg}" title="${c.title}：提及${n.n}次">${i}</div>`;
  }).join('');
  // co-occur
  const co = RC.filter(e=>e.a===name||e.b===name).sort((a,b)=>b.co_chapters-a.co_chapters).slice(0,8)
    .map(e=>{const o=e.a===name?e.b:e.a;return `<span class="chip 配" onclick="openChar('${o}')">${o} · ${e.co_chapters}章${e.type?' · '+e.type:''}</span>`;}).join('');
  document.getElementById('drawerBody').innerHTML = `
    <h2>${name} <span class="chip ${p.role}">${p.role}</span></h2>
    <div class="small muted">阵营：${p.side} ｜ 总提及 ${p.total_mentions} ｜ 出场 ${p.chapter_count} 章</div>
    <div class="small muted">首出场 ${chrName(p.first_chapter)} ｜ 末出场 ${chrName(p.last_chapter)}</div>
    <div class="detail small">${p.note||'（备注待补）'}</div>
    <h2 style="margin-top:14px;font-size:14px">出场时间线（每格=1章，颜色深=提及多）</h2>
    <div class="heat">${cells}</div>
    <div class="legend">序号为章序（0=自序）；浅灰·=该章未出场。</div>
    <h2 style="margin-top:14px;font-size:14px">高频共现人物</h2>
    <div>${co||'<span class="muted small">无</span>'}</div>`;
  document.getElementById('drawer').classList.add('open');
  document.getElementById('mask').classList.add('open');
}

/* ---------- 章节 ---------- */
function vChapters(){
  const rows = CH.map(c=>`<tr class="row" onclick="openCh(${c.idx})">
    <td>${c.title}</td><td>${c.chars}</td>
    <td>${Object.keys(c.scenes).map(s=>'<span class="tag">'+s+'</span>').join('')||'<span class="muted">—</span>'}</td>
    <td>${Object.keys(c.presence).length}</td>
    <td class="small muted">${c.opening}</td></tr>`).join('');
  view.innerHTML = `<div class="card"><h2>章节索引（点击查看首段与出场人物）</h2>
   <table><thead><tr><th>标题</th><th>字数</th><th>场景</th><th>出场人物</th><th>首句</th></tr></thead>
   <tbody>${rows}</tbody></table></div>`;
}
function openCh(i){
  const c=CH[i];
  const chips=Object.entries(c.presence).sort((a,b)=>b[1]-a[1])
    .map(([n,m])=>`<span class="chip ${C[n]?C[n].role:'配'}" onclick="openChar('${n}')">${n} ${m}</span>`).join('');
  const tags=Object.keys(c.scenes).map(s=>'<span class="tag">'+s+'</span>').join('');
  document.getElementById('drawerBody').innerHTML = `
    <h2>${c.title} <span class="muted small">· ${c.chars}字</span></h2>
    <div>${tags||'<span class="muted">无场景标签</span>'}</div>
    <div class="detail"><b>首段：</b><br>${c.opening}……</div>
    <h2 style="margin-top:14px;font-size:14px">出场人物（数字=提及次数）</h2>
    <div>${chips}</div>`;
  document.getElementById('drawer').classList.add('open');
  document.getElementById('mask').classList.add('open');
}

/* ---------- 关系 ---------- */
function vRel(){
  const known = RL.map(r=>`<tr><td><b>${r.a}</b> ↔ <b>${r.b}</b></td><td><span class="chip 主">${r.type}</span></td><td class="small">${r.desc}</td></tr>`).join('');
  // graph: top 14 by mentions
  const top = Object.entries(C).sort((a,b)=>b[1].total_mentions-a[1].total_mentions).slice(0,14).map(x=>x[0]);
  const idx = Object.fromEntries(top.map((n,i)=>[n,i]));
  const W=520,H=520,cx=W/2,cy=H/2,R=200;
  const pos = top.map((n,i)=>{const a=i/top.length*2*Math.PI - Math.PI/2;return [cx+R*Math.cos(a), cy+R*Math.sin(a)];});
  const edgeSet = RC.filter(e=>idx[e.a]!==undefined&&idx[e.b]!==undefined).sort((a,b)=>b.co_chapters-a.co_chapters).slice(0,30);
  const maxE = edgeSet[0]?edgeSet[0].co_chapters:1;
  const edges = edgeSet.map(e=>{
    const a=pos[idx[e.a]],b=pos[idx[e.b]];const w=(e.co_chapters/maxE*5+0.6).toFixed(2);
    return `<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" stroke="#9bb6e8" stroke-width="${w}" opacity=".55"/>`;
  }).join('');
  const nodes = pos.map((p,i)=>`<circle cx="${p[0]}" cy="${p[1]}" r="${10+ (C[top[i]].total_mentions/Math.max(...top.map(n=>C[n].total_mentions))*12).toFixed(1)}" fill="#2f6fed"/>
     <text x="${p[0]}" y="${p[1]+4}" text-anchor="middle" fill="#fff" font-size="11">${top[i]}</text>`).join('');
  // top co-occur pairs table
  const pairs = RC.slice(0,20).map(e=>`<tr><td><a class="k" onclick="openChar('${e.a}')">${e.a}</a> ↔ <a class="k" onclick="openChar('${e.b}')">${e.b}</a></td><td>${e.co_chapters}章</td><td>${e.type||''}</td></tr>`).join('');
  view.innerHTML = `
   <div class="card"><h2>已知关系事实（作者标注）</h2>
     <table><thead><tr><th>人物</th><th>关系</th><th>说明</th></tr></thead><tbody>${known}</tbody></table></div>
   <div class="grid g2">
     <div class="card"><h2>人物共现网络（TOP14）</h2>
       <svg viewBox="0 0 ${W} ${H}" width="100%">${edges}${nodes}</svg>
       <div class="legend">节点大小=提及量；连线粗细=共同出场章数。</div></div>
     <div class="card"><h2>高频共现对 TOP20</h2>
       <table><thead><tr><th>人物对</th><th>共现</th><th>关系</th></tr></thead><tbody>${pairs}</tbody></table></div>
   </div>`;
}

/* ---------- 检索 ---------- */
function vSearch(){
  view.innerHTML = `<div class="card">
    <h2>全文检索</h2>
    <input class="search" id="q" placeholder="输入人物名 / 关键词（如 任琅、江湖、早朝、比试）…" oninput="doSearch(this.value)">
    <div id="sres" class="small muted" style="margin-top:10px">输入后显示结果。</div></div>`;
}
function doSearch(q){
  q=q.trim(); if(!q){document.getElementById('sres').innerHTML='';return;}
  // character match
  let html='';
  const cmatches = Object.keys(C).filter(n=>n.includes(q));
  if(cmatches.length){
    html += '<div class="small" style="margin:8px 0">命中人物：'+cmatches.map(n=>`<span class="chip ${C[n].role}" onclick="openChar('${n}')">${n}</span>`).join('')+'</div>';
  }
  const hits = CH.map(c=>({c,n:c.text.split(q).length-1})).filter(x=>x.n>0);
  if(hits.length){
    html += '<div style="margin-top:6px"><b>命中章节 '+hits.length+' 章（含'+hits.reduce((a,x)=>a+x.n,0)+'处）：</b></div>';
    html += hits.slice(0,60).map(x=>`<div class="row" style="padding:6px 8px;border-bottom:1px solid var(--line)" onclick="openCh(${x.c.idx})">
       <b>${x.c.title}</b> <span class="muted small">· ${x.n}处 · ${x.c.chars}字</span></div>`).join('');
  } else if(!cmatches.length){
    html='<div class="muted">未命中。</div>';
  }
  document.getElementById('sres').innerHTML=html;
}

/* ---------- 路由 ---------- */
const views={overview:vOverview,chars:vChars,chapters:vChapters,rel:vRel,search:vSearch};
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  t.classList.add('active'); views[t.dataset.v]();
});
function closeDrawer(){document.getElementById('drawer').classList.remove('open');document.getElementById('mask').classList.remove('open');}
document.getElementById('mask').onclick=closeDrawer;
vOverview();
</script>
</body>
</html>"""

out = HTML.replace("__KB_JSON__", KB_JSON)
with open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(out)
print("index.html bytes:", len(out))
