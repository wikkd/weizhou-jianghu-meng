#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建工程文档区 docs/：仓库内 Markdown 治理文档 → 鸿蒙风格静态页（纯标准库）。

- 单一事实源：docs 页面由仓库根的 *.md 生成，文档改 md 即改站，不手改 HTML；
- 渲染子集：标题/表格/列表/引用/围栏代码/行内代码/加粗/链接/分隔线（覆盖本仓文档全部用法）；
- 样式：复用 assets/theme.css 令牌与动效（DEV_RULES/MOTION_SPEC 强制项）。
"""
import html as H
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
os.makedirs(OUT, exist_ok=True)

REPO = "https://github.com/wikkd/weizhou-jianghu-meng"
THEME_INIT = ('<script>(function(){var d=document.documentElement,t=localStorage.getItem("wzjm_theme");'
              'if(!t)t=window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";'
              'd.setAttribute("data-theme",t);})();</script>')

def md_last_updated(md_name: str) -> str:
    """md 最后提交日期（git log 单源；失败回退文件 mtime）"""
    try:
        d = subprocess.run(["git", "log", "-1", "--format=%cs", "--", md_name],
                           cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
        if d:
            return d
    except Exception:
        pass
    import datetime
    return datetime.date.fromtimestamp(os.path.getmtime(os.path.join(ROOT, md_name))).isoformat()

DOCS = [
    ("README.md",      "readme",      "项目总览",   "双域结构、六类资产分类与部署模型"),
    ("CHARTER.md",     "charter",     "开发章程",   "流程 / DoD 门禁 / 安全红线"),
    ("DEV_RULES.md",   "dev-rules",   "开发守则",   "鸿蒙 UI / 交互逻辑 / 本地生图 / 动效令牌化"),
    ("MOTION_SPEC.md", "motion-spec", "动效细则",   "曲线与时长令牌、交互映射、红线"),
    ("UI_SPEC.md",     "ui-spec",     "设计系统",   "设计令牌 / 组件 / 页面验收"),
    ("WIKI_SPEC.md",   "wiki-spec",   "Wiki 架构",  "命名空间 / 构建管线 / 分期规划"),
]
UPDATED = {md: md_last_updated(md) for md, *_ in DOCS}

# ---------- Markdown 子集渲染 ----------
def inline(s: str) -> str:
    s = H.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s

def render(md: str):
    """返回 (title, toc[(id,text)], body_html)"""
    lines = md.splitlines()
    out, toc = [], []
    i, n, h2n, title = 0, len(lines), 0, ""
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            lvl, text = len(m.group(1)), m.group(2).strip()
            if lvl == 1 and not title:
                title = re.sub(r"[#*`]", "", text)
                i += 1
                continue
            if lvl == 2:
                h2n += 1
                hid = f"sec-{h2n}"
                toc.append((hid, re.sub(r"[#*`]", "", text)))
                out.append(f'<h2 id="{hid}">{inline(text)}</h2>')
            else:
                out.append(f"<h3>{inline(text)}</h3>")
            i += 1
            continue
        if s.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre>" + H.escape("\n".join(buf)) + "</pre>")
            continue
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            if len(rows) >= 2 and all(re.fullmatch(r":?-{2,}:?", c) for c in rows[1]):
                head, body = rows[0], rows[2:]
            else:
                head, body = None, rows
            t = ["<table>"]
            if head:
                t.append("<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead>")
            t.append("<tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + "<br>".join(inline(b) for b in buf if b) + "</blockquote>")
            continue
        if re.fullmatch(r"-{3,}", s):
            out.append("<hr>")
            i += 1
            continue
        if re.match(r"[-*]\s+", s):
            items = []
            while i < n and re.match(r"[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"[-*]\s+", "", lines[i].strip(), count=1))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(it)}</li>" for it in items) + "</ul>")
            continue
        if re.match(r"\d+\.\s+", s):
            items = []
            while i < n and re.match(r"\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"\d+\.\s+", "", lines[i].strip(), count=1))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(it)}</li>" for it in items) + "</ol>")
            continue
        # 普通段落：连续非空行合并
        buf = [s]
        i += 1
        while i < n and lines[i].strip() and not re.match(r"^(#|\||>|```|[-*]\s|\d+\.\s|-{3,})", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>" + "<br>".join(inline(b) for b in buf) + "</p>")
    return title or "文档", toc, "\n".join(out)

PAGE = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ · 苇舟江湖梦 · 工程文档</title>
__THEME_INIT__
<link rel="icon" type="image/svg+xml" href="__BASE__assets/favicon.svg">
<link rel="stylesheet" href="__BASE__assets/theme.css">
<style>
/* 文档页专属：只取 theme.css 令牌 */
.doc{max-width:860px}
.doc h1{font-size:24px;font-weight:700;letter-spacing:1px;margin:18px 0 6px}
.doc .src{color:var(--muted);font-size:12px;margin-bottom:18px}
.doc h2{font-size:17px;font-weight:500;margin:26px 0 10px;padding-left:10px;border-left:3px solid var(--brand)}
.doc h3{font-size:14.5px;font-weight:500;margin:18px 0 8px}
.doc p{margin:0 0 10px;font-size:13.5px;color:var(--ink)}
.doc ul,.doc ol{margin:0 0 12px;padding-left:22px;font-size:13.5px}
.doc li{margin:3px 0}
.doc blockquote{margin:0 0 14px;padding:8px 14px;border-left:3px solid var(--brand);
  background:var(--brand-soft);border-radius:0 var(--radius-sm) var(--radius-sm) 0;
  color:var(--muted);font-size:13px}
.doc code{background:var(--field);border-radius:6px;padding:1px 6px;font-size:12.5px;color:var(--brand)}
.doc pre{background:var(--field);border:1px solid var(--line);border-radius:var(--radius-sm);
  padding:12px 14px;overflow:auto;margin:0 0 14px}
.doc pre code{background:none;padding:0;color:var(--ink);font-size:12px;line-height:1.6}
.doc table{width:100%;border-collapse:collapse;font-size:13px;margin:0 0 14px}
.doc th,.doc td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
.doc th{color:var(--muted);font-weight:500;background:var(--field)}
.doc hr{border:none;border-top:1px solid var(--line);margin:18px 0}
.toc{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 20px}
.toc a{font-size:12px;padding:4px 14px;border-radius:999px;background:var(--card);
  border:1px solid var(--line);color:var(--muted);
  transition:color var(--dur-fast) var(--ease-std),border-color var(--dur-fast) var(--ease-std),transform var(--dur-fast) var(--ease-elastic-out)}
.toc a:hover{color:var(--brand);border-color:var(--brand);transform:scale(1.05)}
/* 上一篇/下一篇 */
.pager{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:34px 0 10px}
.pager a{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:12px 16px;
  transition:border-color var(--dur-fast) var(--ease-std),transform var(--dur-base) var(--ease-out)}
.pager a:hover{border-color:var(--brand);transform:translateY(-2px)}
.pager a.next{text-align:right}
.pager .dir{font-size:11px;color:var(--muted)}
.pager .pt{font-size:13.5px;font-weight:500;color:var(--brand);margin-top:2px}
/* 返回顶部：无 JS 时锚点跳转仍可用 */
.totop{position:fixed;right:22px;bottom:26px;z-index:30;width:40px;height:40px;border-radius:50%;
  background:var(--card);border:1px solid var(--line);box-shadow:var(--shadow);
  display:flex;align-items:center;justify-content:center;opacity:0;visibility:hidden;
  transition:opacity var(--dur-base) var(--ease-std),visibility var(--dur-base) var(--ease-std),transform var(--dur-base) var(--ease-spring)}
.totop.show{opacity:1;visibility:visible}
.totop:hover{transform:translateY(-3px);border-color:var(--brand)}
[data-theme="dark"] .totop img{filter:invert(1)}
@media(max-width:760px){.nav{flex-wrap:wrap}.pager{grid-template-columns:1fr}}
</style>
</head>
<body>
<nav class="nav">
  <a class="brand" href="__BASE__index.html">苇舟江湖梦</a>
  <span class="sp"></span>
  <a class="lk on" href="__BASE__docs/index.html">文档</a>
  <a class="lk" href="__BASE__wiki/index.html">总目录</a>
  <a class="lk" href="__BASE__kb.html">知识库</a>
  <a class="lk" href="__BASE__poems/poem_gallery.html">诗图</a>
  <a class="lk" href="__BASE__文学/产物/00_总览导航/index.html">量化报告</a>
  <a class="lk" href="__REPO__" target="_blank" rel="noopener">仓库</a>
  <button class="theme-btn" id="themeBtn" type="button" aria-label="切换明暗主题">
    <img src="__BASE__assets/icons/ic_public_themes.svg" alt="" width="18" height="18">
  </button>
</nav>
<div class="wrap doc fade-in" id="top">
<h1>__TITLE__</h1>
<div class="src">源文件 <a href="__REPO__/blob/master/__MD__" target="_blank" rel="noopener">__MD__</a> ｜ 更新于 __UPDATED__ ｜ 由 build_docs.py 构建，改动请编辑源 md</div>
<div class="toc">__TOC__</div>
__BODY__
__PAGER__
</div>
<a class="totop" id="totop" href="#top" aria-label="返回顶部">
  <img src="../assets/icons/ic_public_backtotop.svg" alt="" width="18" height="18">
</a>
<script>
document.getElementById('themeBtn').addEventListener('click',function(){
  var d=document.documentElement,t=d.getAttribute('data-theme')==='dark'?'light':'dark';
  d.setAttribute('data-theme',t);
  try{localStorage.setItem('wzjm_theme',t);}catch(e){}
  this.setAttribute('aria-label',t==='dark'?'切换到浅色主题':'切换到深色主题');
});
/* 返回顶部：滚动显隐 + 平滑滚动（渐进增强，无 JS 时锚点跳转可用） */
(function(){
  var btn=document.getElementById('totop');
  addEventListener('scroll',function(){btn.classList.toggle('show',scrollY>400)},{passive:true});
  btn.addEventListener('click',function(e){e.preventDefault();scrollTo({top:0,behavior:'smooth'})});
})();
</script>
</body></html>"""

# ---------- 单文档页 ----------
for idx, (md_name, slug, zh, desc) in enumerate(DOCS):
    md = open(os.path.join(ROOT, md_name), encoding="utf-8").read()
    title, toc, body = render(md)
    toc_html = "".join(f'<a href="#{hid}">{H.escape(txt)}</a>' for hid, txt in toc)
    # 上一篇/下一篇
    prev_doc = DOCS[idx - 1] if idx > 0 else None
    next_doc = DOCS[idx + 1] if idx < len(DOCS) - 1 else None
    pager_html = '<div class="pager">'
    pager_html += (f'<a href="{prev_doc[1]}.html"><div class="dir">← 上一篇</div>'
                   f'<div class="pt">{prev_doc[2]}</div></a>' if prev_doc else '<span></span>')
    pager_html += (f'<a class="next" href="{next_doc[1]}.html"><div class="dir">下一篇 →</div>'
                   f'<div class="pt">{next_doc[2]}</div></a>' if next_doc else '<span></span>')
    pager_html += '</div>'
    page = (PAGE.replace("__TITLE__", H.escape(zh))
                .replace("__MD__", md_name)
                .replace("__UPDATED__", UPDATED[md_name])
                .replace("__THEME_INIT__", THEME_INIT)
                .replace("__BASE__", "../")
                .replace("__REPO__", REPO)
                .replace("__TOC__", toc_html)
                .replace("__PAGER__", pager_html)
                .replace("__BODY__", body))
    with open(os.path.join(OUT, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(page)

# ---------- 文档目录页 ----------
cards = "\n".join(f"""
    <a class="dcard" href="{slug}.html">
      <div class="t">{zh}</div>
      <div class="s">{desc}</div>
      <div class="meta">更新于 {UPDATED[md]} · 源 {md}</div>
      <div class="go">阅读 →</div>
    </a>""" for md, slug, zh, desc in DOCS)

INDEX = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>工程文档 · 苇舟江湖梦</title>
__THEME_INIT__
<link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">
<link rel="stylesheet" href="../assets/theme.css">
<style>
.dgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:16px}
@media(max-width:820px){.dgrid{grid-template-columns:1fr 1fr}}
@media(max-width:600px){.dgrid{grid-template-columns:1fr}}
.dcard{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px;
  box-shadow:var(--shadow);display:flex;flex-direction:column;
  transition:transform var(--dur-base) var(--ease-out),border-color var(--dur-fast) var(--ease-std),box-shadow var(--dur-base) var(--ease-out)}
.dcard:hover{transform:translateY(-3px);border-color:var(--brand);box-shadow:0 8px 20px rgba(0,0,0,.08)}
.dcard .t{font-size:15px;font-weight:500;margin-bottom:6px}
.dcard .s{color:var(--muted);font-size:12.5px;flex:1}
.dcard .meta{margin-top:10px;font-size:11px;color:var(--muted);opacity:.8}
.dcard .go{margin-top:6px;font-size:12.5px;color:var(--brand);font-weight:500}
@media(max-width:760px){.nav{flex-wrap:wrap}}
</style>
</head>
<body>
<nav class="nav">
  <a class="brand" href="../index.html">苇舟江湖梦</a>
  <span class="sp"></span>
  <a class="lk on" href="../docs/index.html">文档</a>
  <a class="lk" href="../wiki/index.html">总目录</a>
  <a class="lk" href="../kb.html">知识库</a>
  <a class="lk" href="../poems/poem_gallery.html">诗图</a>
  <a class="lk" href="../文学/产物/00_总览导航/index.html">量化报告</a>
  <a class="lk" href="__REPO__" target="_blank" rel="noopener">仓库</a>
  <button class="theme-btn" id="themeBtn" type="button" aria-label="切换明暗主题">
    <img src="../assets/icons/ic_public_themes.svg" alt="" width="18" height="18">
  </button>
</nav>
<div class="wrap fade-in">
  <h1 style="font-size:22px;font-weight:700;margin:18px 0 4px">工程文档</h1>
  <p style="color:var(--muted);font-size:13px;margin:0">治理与规格文档的站点化版本，与仓库 md 单一事实源同步。</p>
  <div class="dgrid stagger">
__CARDS__
  </div>
</div>
<script>
document.getElementById('themeBtn').addEventListener('click',function(){
  var d=document.documentElement,t=d.getAttribute('data-theme')==='dark'?'light':'dark';
  d.setAttribute('data-theme',t);
  try{localStorage.setItem('wzjm_theme',t);}catch(e){}
});
</script>
</body></html>"""

idx = INDEX.replace("__THEME_INIT__", THEME_INIT).replace("__REPO__", REPO).replace("__CARDS__", cards)
with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
    f.write(idx)

print("docs 构建完成：", ", ".join(f"{slug}.html" for _, slug, _, _ in DOCS), "+ index.html")
