#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 wiki：content/ 词条源 → wiki/ 静态页（纯标准库，规格见 WIKI_SPEC.md）。

原则：
- 信息框统计单源于 knowledge_base.json，词条手写内容与统计数据不混写；
- [[词条链]] 构建期解析，未创建词条输出红链并计入死链报告；
- 每次构建全量重建 wiki/（幂等）。
"""
import json, os, re, html, shutil, urllib.parse, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT, "content")
OUT_DIR = os.path.join(ROOT, "wiki")
KB = json.load(open(os.path.join(ROOT, "knowledge_base.json"), encoding="utf-8"))
CH, CHARS = KB["chapters"], KB["characters"]
SCHEMA_VERSION = 1
NS_ORDER = ["人物", "章节", "地点", "组织", "术语", "诗词"]
BUILD_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
REPO = "https://github.com/wikkd/weizhou-jianghu-meng"

def ch_title(i):
    return CH[i]["title"] if 0 <= i < len(CH) else "?"

# ---------- frontmatter（自写极简解析：标量 / [列表] / infobox 嵌套键值） ----------
def parse_scalar(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [s.strip().strip("'\"") for s in inner.split(",") if s.strip()] if inner else []
    return v.strip("'\"")

def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    meta, cur = {}, None
    for raw in text[3:end].splitlines():
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        k, _, v = raw.strip().partition(":")
        k, v = k.strip(), v.strip()
        if indent == 0:
            meta[k] = parse_scalar(v) if v else {}
            cur = k
        elif isinstance(meta.get(cur), dict):
            meta[cur][k] = parse_scalar(v)
    return meta, text[end + 4:].lstrip("\n")

# ---------- 词条加载 ----------
entries, alias_map = {}, {}
for d in sorted(os.listdir(CONTENT_DIR)):
    dpath = os.path.join(CONTENT_DIR, d)
    if not os.path.isdir(dpath):
        continue
    for f in sorted(os.listdir(dpath)):
        if not f.endswith(".md"):
            continue
        meta, body = parse_frontmatter(open(os.path.join(dpath, f), encoding="utf-8").read())
        ns = meta.get("ns") or d
        title = meta.get("title") or f[:-3]
        e = {"ns": ns, "title": title, "aliases": meta.get("aliases") or [],
             "summary": meta.get("summary", ""), "tags": meta.get("tags") or [],
             "infobox": meta.get("infobox") or {}, "body": body, "path": f"content/{d}/{f}"}
        entries[(ns, title)] = e
        for a in e["aliases"]:
            alias_map[a] = (ns, title)

def ns_rank(ns):
    return NS_ORDER.index(ns) if ns in NS_ORDER else len(NS_ORDER)

def resolve(target):
    target = target.strip()
    if "/" in target:
        ns, t = target.split("/", 1)
        if (ns, t) in entries:
            return (ns, t)
        hit = alias_map.get(t)
        if hit and hit[0] == ns:
            return hit
        return None
    cands = sorted([k for k in entries if k[1] == target], key=lambda k: ns_rank(k[0]))
    if cands:
        return cands[0]
    return alias_map.get(target)

# ---------- 行内渲染（先转义，再替换词条链/加粗） ----------
WLR = re.compile(r"\[\[([^\[\]|]+)(?:\|([^\[\]]+))?\]\]")

def inline(s, base):
    s = html.escape(s)
    def rep(m):
        tgt, label = m.group(1).strip(), (m.group(2) or m.group(1)).strip()
        r = resolve(tgt)
        if r:
            ns, t = r
            return f'<a class="wl" href="{base}{urllib.parse.quote(ns)}/{urllib.parse.quote(t)}.html">{html.escape(label)}</a>'
        q = urllib.parse.quote(label)
        return f'<a class="wl red" href="{base}{urllib.parse.quote("待创建")}.html?t={q}" title="词条待创建">{html.escape(label)}</a>'
    s = WLR.sub(rep, s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

def render_body(body, base):
    out = []
    for para in re.split(r"\n\s*\n", body.strip()):
        lines = [l for l in para.splitlines() if l.strip()]
        if not lines:
            continue
        if lines[0].lstrip().startswith("## "):
            out.append(f"<h3>{inline(lines[0].lstrip()[3:], base)}</h3>")
            lines = lines[1:]
        if lines and all(l.lstrip().startswith("- ") for l in lines):
            out.append("<ul>" + "".join(f"<li>{inline(l.lstrip()[2:], base)}</li>" for l in lines) + "</ul>")
        elif lines:
            out.append("<p>" + "<br>".join(inline(l.strip(), base) for l in lines) + "</p>")
    return "\n".join(out)

# ---------- 信息框与出处（单源：knowledge_base.json） ----------
def chap_entry_link(title, base):
    t = title.rstrip("、")
    if ("章节", t) in entries:
        return f'<a class="chip lnk" href="{base}{urllib.parse.quote("章节")}/{urllib.parse.quote(t)}.html">{html.escape(title)}</a>'
    return f'<span class="chip gray">{html.escape(title)}</span>'

def person_chips(names, base, max_n=6):
    out = []
    for n in names:
        if ("人物", n) in entries:
            out.append(f'<a class="chip lnk" href="{base}{urllib.parse.quote("人物")}/{urllib.parse.quote(n)}.html">{html.escape(n)}</a>')
        else:
            out.append(f'<span class="chip gray">{html.escape(n)}</span>')
    return "".join(out)

def build_infobox(e, base):
    ns, title = e["ns"], e["title"]
    rows = {}
    if ns == "人物" and title in CHARS:
        p = CHARS[title]
        rows = {"角色": p["role"], "阵营": p["side"],
                "首见": ch_title(p["first_chapter"]), "末见": ch_title(p["last_chapter"]),
                "提及": f'{p["total_mentions"]} 次', "出场": f'{p["chapter_count"]} 章'}
    elif ns == "章节":
        c = next((c for c in CH if c["title"].rstrip("、") == title), None)
        if c:
            rows = {"字数": f'{c["chars"]} 字', "场景": "、".join(c["scenes"]) or "—"}
    for k, v in (e["infobox"] or {}).items():   # 手写键覆盖/追加（描述性字段）
        rows[k] = v
    trs = "".join(f'<div class="row">{html.escape(k)} <b>{inline(str(v), base)}</b></div>' for k, v in rows.items())
    avatar = html.escape(title[0]) if title else "？"
    box = f'<div class="card infobox"><div class="avatar">{avatar}</div>{trs}</div>'
    extra = ""
    if ns == "人物" and title in CHARS:
        tl = CHARS[title].get("timeline") or []
        chs = [t["ch"] for t in tl]
        chips = "".join(chap_entry_link(ch_title(i), base) for i in chs[:6])
        more = f'<span class="chip gray">+{len(chs) - 6} 章</span>' if len(chs) > 6 else ""
        extra = (f'<div class="sec-h">章节出处（自动汇聚）</div><div>{chips}{more}</div>')
    elif ns == "章节":
        c = next((c for c in CH if c["title"].rstrip("、") == title), None)
        if c:
            top = sorted(c["presence"].items(), key=lambda kv: -kv[1])
            extra = f'<div class="sec-h">出场人物（提及次数）</div><div>{person_chips([n for n, _ in top], base)}</div>'
    return box, extra

# ---------- 页面模板 ----------
THEME_INIT = ('<script>(function(){var d=document.documentElement,t=localStorage.getItem("wzjm_theme");'
              'if(!t)t=window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";'
              'd.setAttribute("data-theme",t);})();</script>')

def page_html(*, title, body_html, base, history_path=None, extra_head=""):
    hist = (f'<span>修订历史 <a href="{REPO}/commits/master/{urllib.parse.quote(history_path)}" target="_blank" rel="noopener">git log</a></span>'
            if history_path else f"<span>源 <a href='{REPO}' target='_blank' rel='noopener'>GitHub</a></span>")
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · 苇舟江湖梦 Wiki</title>
{THEME_INIT}<link rel="stylesheet" href="{base}../assets/theme.css">{extra_head}
</head>
<body>
<nav class="nav">
  <a class="lk" href="{base}../index.html">‹ 主页</a>
  <div class="brand">苇舟江湖梦 · Wiki</div>
  <span class="sp"></span>
  <form action="{base}index.html" method="get" style="margin:0"><input class="search k" name="q" placeholder="搜索词条…"></form>
  <button class="theme-btn" onclick="toggleTheme()" title="明暗切换" aria-label="切换明暗主题"><img src="{base}../assets/icons/ic_public_themes.svg" alt="" width="18" height="18"></button>
</nav>
<div class="wrap fade-in">
{body_html}
<div class="foot">{hist}<span>由 build_wiki.py 构建 · {BUILD_TIME}</span><span>schema v{SCHEMA_VERSION}</span></div>
</div>
<script>function toggleTheme(){{var d=document.documentElement,t=d.getAttribute("data-theme")==="dark"?"light":"dark";d.setAttribute("data-theme",t);localStorage.setItem("wzjm_theme",t);}}</script>
</body></html>"""

# ---------- 回链收集 ----------
links_to = {}   # (ns,title) -> set of source (ns,title)
red_links = []  # (source, target label)

def collect_links(e):
    base = "../"   # 词条页位于 wiki/<ns>/ 下
    src = (e["ns"], e["title"])
    for m in WLR.finditer(e["body"]):
        tgt, label = m.group(1).strip(), (m.group(2) or m.group(1)).strip()
        r = resolve(tgt)
        if r and r != src:
            links_to.setdefault(r, set()).add(src)
        elif not r:
            red_links.append((f"{src[0]}/{src[1]}", label))

for e in entries.values():
    collect_links(e)

# ---------- 生成词条页 / 重定向页 ----------
if os.path.isdir(OUT_DIR):
    shutil.rmtree(OUT_DIR)
os.makedirs(OUT_DIR)

made, redirects = 0, 0
for (ns, title), e in entries.items():
    base = "../"
    box, extra = build_infobox(e, base)
    body = render_body(e["body"], base)
    alias_str = "、".join(e["aliases"]) if e["aliases"] else "—"
    tag_html = "".join(f'<span class="chip gray">{html.escape(t)}</span>' for t in e["tags"])
    backlinks = sorted(links_to.get((ns, title), []))
    bl_html = "".join(f'<a class="chip green lnk" href="{base}{urllib.parse.quote(sns)}/{urllib.parse.quote(st)}.html">{html.escape(st)}</a>'
                      for sns, st in backlinks) or '<span class="chip gray">暂无</span>'
    content = f"""
<div class="crumb"><span class="ns">命名空间：{html.escape(ns)}</span><span class="alias">别名：{html.escape(alias_str)}</span></div>
<h1 class="title">{html.escape(title)}</h1>
{tag_html}
<div class="entry-grid">
  <div>{box}</div>
  <div class="card body">
    {body}
    {extra}
    <div class="sec-h">反向链接（谁引用了本词条）</div>
    <div>{bl_html}</div>
  </div>
</div>"""
    hist = f'content/{urllib.parse.quote(ns)}/{urllib.parse.quote(title)}.md'
    page = page_html(title=f"{title} · {ns}", body_html=content, base=base, history_path=e["path"])
    out_ns = os.path.join(OUT_DIR, ns)
    os.makedirs(out_ns, exist_ok=True)
    with open(os.path.join(out_ns, f"{title}.html"), "w", encoding="utf-8") as f:
        f.write(page)
    made += 1
    for a in e["aliases"]:
        url = f"{urllib.parse.quote(ns)}/{urllib.parse.quote(title)}.html"
        redir = (f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
                 f'<meta http-equiv="refresh" content="0; url={url}">'
                 f'<link rel="canonical" href="{url}"></head><body>'
                 f'「{html.escape(a)}」是「<a href="{url}">{html.escape(title)}</a>」的别名，正在跳转…</body></html>')
        with open(os.path.join(out_ns, f"{a}.html"), "w", encoding="utf-8") as f:
            f.write(redir)
        redirects += 1

# ---------- 待创建（红链落点） ----------
stub = page_html(title="词条待创建", base="", body_html="""
<div class="card" style="margin-top:30px;text-align:center;padding:46px 20px">
  <div style="font-size:34px">🚧</div>
  <h2 style="font-size:18px;font-weight:500;margin:10px 0 6px">该词条尚未创建</h2>
  <p id="t" style="color:var(--muted);margin:0">正在读取词条名…</p>
  <p style="margin-top:16px"><a class="btn primary" href="index.html">返回总目录</a></p>
</div>""", extra_head="") + """
<script>var q=new URLSearchParams(location.search).get("t");if(q)document.getElementById("t").textContent="「"+q+"」还没有词条。可在 content/ 对应命名空间目录新建该词条后重新构建。";</script>"""
with open(os.path.join(OUT_DIR, "待创建.html"), "w", encoding="utf-8") as f:
    f.write(stub)

# ---------- 总目录 + 搜索索引 ----------
def esc(s): return html.escape(s)
sec_html, search_index = [], []
for ns in NS_ORDER:
    items = sorted([e for (n, _), e in entries.items() if n == ns], key=lambda e: e["title"])
    if not items:
        continue
    cards = "".join(
        f'<a class="entry-card" href="{urllib.parse.quote(e["ns"])}/{urllib.parse.quote(e["title"])}.html">'
        f'<div class="t">{esc(e["title"])}{" <span class=\"chip gray\">别名 " + esc("、".join(e["aliases"])) + "</span>" if e["aliases"] else ""}</div>'
        f'<div class="s">{esc(e["summary"])}</div></a>' for e in items)
    sec_html.append(f'<div class="ns-sec stagger" id="ns-{esc(ns)}" data-ns="{esc(ns)}"><h2>{esc(ns)} <span class="chip gray">{len(items)}</span></h2>{cards}</div>')
    for e in items:
        plain = re.sub(r"\[\[([^\[\]|]+)(?:\|([^\[\]]+))?\]\]", r"\1", e["body"])
        search_index.append({"ns": e["ns"], "title": e["title"], "aliases": e["aliases"],
                             "summary": e["summary"],
                             "text": re.sub(r"\s+", "", plain)[:180],
                             "path": f'{urllib.parse.quote(e["ns"])}/{urllib.parse.quote(e["title"])}.html'})
with open(os.path.join(OUT_DIR, "search-index.json"), "w", encoding="utf-8") as f:
    json.dump({"schema_version": SCHEMA_VERSION, "built": BUILD_TIME, "entries": search_index}, f, ensure_ascii=False)

n_total = len(entries)
all_cards = "".join(f'<a class="chip lnk" href="{s["path"]}">{esc(s["title"])}</a>' for s in search_index)
index_body = f"""
<div class="crumb"><span class="ns">Wiki 总目录</span><span class="alias">共 {n_total} 词条 · 构建于 {BUILD_TIME}</span></div>
<h1 class="title">苇舟江湖梦 · 百科词条</h1>
<div class="card" style="margin-bottom:8px">
  <input class="search" id="q" placeholder="过滤词条（标题 / 别名 / 摘要 / 正文片段）…">
  <div id="hit" style="margin-top:10px;font-size:12.5px;color:var(--muted)"></div>
</div>
<div id="sections">{''.join(sec_html)}</div>"""
index_page = page_html(title="总目录", body_html=index_body, base="",
                       history_path=None, extra_head="") + """
<script>
var IDX=null;
fetch("search-index.json").then(r=>r.json()).then(d=>{IDX=d.entries;apply();});
function norm(s){return (s||"").replace(/\\s+/g,"");}
function apply(){
  var q=norm(new URLSearchParams(location.search).get("q")||document.getElementById("q").value);
  document.querySelectorAll(".ns-sec").forEach(function(sec){sec.style.display="";});
  if(!IDX)return;
  var hits=IDX.filter(function(e){return !q||(e.title+" "+(e.aliases||[]).join(" ")+" "+e.summary+" "+(e.text||"")).indexOf(q)>=0;});
  document.getElementById("hit").textContent=q?("命中 "+hits.length+" 词条："+(hits.map(function(h){return h.title;}).join("、")||"无")):"";
  if(q){
    document.querySelectorAll(".ns-sec").forEach(function(sec){
      var ns=sec.getAttribute("data-ns");var any=hits.some(function(h){return h.ns===ns;});
      sec.style.display=any?"":"none";
      sec.querySelectorAll(".entry-card").forEach(function(c){
        var href=decodeURIComponent(c.getAttribute("href"));
        c.style.display=hits.some(function(h){return href.indexOf(h.path)===0;})?"":"none";
      });
    });
  }
}
document.getElementById("q").addEventListener("input",function(){history.replaceState(null,"","index.html");apply();});
apply();
</script>"""
with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_page)

# ---------- 报告 ----------
print(f"wiki 构建完成：词条 {made}，重定向 {redirects}，红链 {len(red_links)}")
for src, label in red_links:
    print(f"  红链：[[{label}]] ← {src}")
