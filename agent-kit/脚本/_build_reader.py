# -*- coding: utf-8 -*-
"""
构建《苇舟江湖梦》原文阅读页（产物/苇舟江湖梦_原文阅读.html）。

解析源：
  - 数据/full_text.txt          全书原文（作者/自序/简易参考图 + 59 章正文）
  - 数据/chapter_data/chapters_index.json  59 章索引（cn 中文数字 + scene_hint）

拆分规则：
  - 章首标记 = 独立成行、仅含「中文数字 + 、」、无后续内容（如「一、」「五十九、」），
    与章内条目标号（如「一、大清早……」）区分开。
  - 每章 / 序 的正文按空行切分为段落（<p>），段内换行折叠为空格，忠实保留原文。

样式：复用 产物/theme.css（设计 Token + body.dark 深色变量），另注入阅读页专属排版
      （舒适行宽、行高、居中章题、目录多列、阅读进度条、回到顶部），并内联深色切换。
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "数据", "full_text.txt")
IDX = os.path.join(ROOT, "数据", "chapter_data", "chapters_index.json")
OUT = os.path.join(ROOT, "产物", "苇舟江湖梦_原文阅读.html")
THEME_HREF = "theme.css"

CHAP_RE = re.compile(r"^[一二三四五六七八九十百]+、$")
WS_RE = re.compile(r"\s+", re.UNICODE)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def paragraphs(text):
    """源文件以「每物理行 = 一个段落」组织（章节内无空行分隔）。
    按换行切分，跳过空行；段内空白/制表符折叠为单空格，忠实保留原文。"""
    out = []
    for ln in text.split("\n"):
        b = ln.strip()
        if not b:
            continue
        b = WS_RE.sub(" ", b)
        out.append(b)
    return out


def load():
    text = io.open(SRC, encoding="utf-8").read()
    lines = text.split("\n")
    first = None
    for i, ln in enumerate(lines):
        if CHAP_RE.match(ln.strip()):
            first = i
            break
    if first is None:
        raise RuntimeError("未在 full_text.txt 中找到任何章首标记")
    fore_lines = lines[:first]
    body_lines = lines[first:]
    chapters = []  # (marker, [body_lines])
    marker = None
    buf = []
    for ln in body_lines:
        s = ln.strip()
        if CHAP_RE.match(s):
            if marker is not None:
                chapters.append((marker, buf))
            marker = s
            buf = []
        else:
            buf.append(ln)
    if marker is not None:
        chapters.append((marker, buf))
    return fore_lines, chapters


def render_foreword(fore_lines):
    text = "\n".join(fore_lines).strip()
    blocks = paragraphs(text)
    html = ['<section id="foreword" class="foreword">']
    fi = 0
    for b in blocks:
        if b.startswith("作者：") or b.startswith("作者:"):
            html.append('<p id="fore-p%d" class="byline">%s</p>' % (fi, esc(b)))
            fi += 1
        elif b.strip() == "自序":
            html.append('<h2 class="ft-title">自序</h2>')
        elif "简易参考图" in b:
            html.append('<div class="note">%s（原稿标注，未附图，此处从略。）</div>' % esc(b))
        else:
            html.append('<p id="fore-p%d">%s</p>' % (fi, esc(b)))
            fi += 1
    html.append("</section>")
    return "\n".join(html)


def render_chapters(chapters):
    idx = json.load(io.open(IDX, encoding="utf-8"))
    meta = {e["chapter"]: e for e in idx}
    html = []
    for i, (marker, body) in enumerate(chapters):
        num = i + 1
        entry = meta.get(num, {})
        cn = entry.get("cn", re.match(r"^([一二三四五六七八九十百]+)、$", marker).group(1))
        scene = entry.get("scene_hint") or ""
        title = '%s<span class="ch-scene">%s</span>' % (esc(cn) + "、", esc(scene)) if scene else (esc(cn) + "、")
        html.append('<section id="ch%d" class="chapter">' % num)
        html.append('<h2>%s</h2>' % title)
        for pi, p in enumerate(paragraphs("\n".join(body))):
            html.append('<p id="ch%d-p%d">%s</p>' % (num, pi, esc(p)))
        html.append("</section>")
    return "\n".join(html)


def render_toc(chapters):
    idx = json.load(io.open(IDX, encoding="utf-8"))
    meta = {e["chapter"]: e for e in idx}
    items = ['<li><a href="#foreword">序 · 自序</a></li>']
    for i in range(len(chapters)):
        num = i + 1
        entry = meta.get(num, {})
        cn = entry.get("cn", "第%d章" % num)
        scene = entry.get("scene_hint") or ""
        label = "第%s章" % esc(cn)
        if scene:
            label += " · %s" % esc(scene)
        items.append('<li><a href="#ch%d">%s</a></li>' % (num, label))
    return (
        '<nav class="toc" aria-label="目录">\n'
        '  <h2 class="toc-title">目录</h2>\n'
        '  <ul class="toc-list">\n    ' + "\n    ".join(items) + "\n  </ul>\n"
        "</nav>"
    )


CSS = """
/* ===== 阅读页专属排版（在 theme.css 之上微调，保留宣纸/墨蓝/朱砂 DNA） ===== */
.reader{max-width:780px;margin:0 auto;padding:0 22px 140px;}
.reader header.cover{margin:0 -22px 40px;border-radius:0;}
.reader header.cover h1{font-size:clamp(26px,4vw,34px);letter-spacing:4px;}
.reader header.cover p{color:rgba(255,255,255,.9);font-size:14px;letter-spacing:1px;}
.reader header.cover .cov-sub{opacity:.82;font-size:12.5px;margin-top:6px;}

/* 序 */
.foreword{margin:8px 0 8px;}
.reader .byline{text-align:center;color:var(--accent);font-size:14px;margin:0 0 22px;letter-spacing:1px;}
.reader .ft-title{text-align:center;color:var(--primary-d);border-left:none;padding:0;
  font-size:21px;letter-spacing:3px;margin:0 0 22px;}

/* 目录 */
.toc{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:20px 22px;margin:0 0 18px;box-shadow:var(--shadow-card);}
.toc-title{margin:0 0 14px;font-size:18px;color:var(--primary-d);border-left:none;
  padding:0;text-align:center;letter-spacing:3px;}
.toc-list{list-style:none;margin:0;padding:0;column-count:2;column-gap:22px;}
.toc-list li{margin:0 0 9px;break-inside:avoid;}
.toc-list a{display:block;font-size:13.5px;color:var(--ink);padding:3px 8px;
  border-radius:6px;transition:background-color .2s ease,color .2s ease;}
.toc-list a:hover{background:var(--surface-2);color:var(--primary);text-decoration:none;}
@media(max-width:560px){.toc-list{column-count:1;}}

/* 章 */
.chapter{margin:0;}
.reader .chapter h2{font-family:var(--serif);text-align:center;color:var(--primary-d);
  font-size:23px;font-weight:700;letter-spacing:2px;margin:56px 0 28px;padding:0;
  border-left:none;line-height:1.5;}
.reader .chapter h2 .ch-scene{display:block;font-size:14px;font-weight:400;
  color:var(--muted);letter-spacing:1px;margin-top:6px;}
.reader .chapter p{font-size:17px;line-height:2.0;margin:0 0 1.2em;color:var(--ink);
  text-align:justify;text-justify:inter-ideograph;letter-spacing:.02em;
  text-indent:2em;}
.reader .chapter p:first-of-type{text-indent:2em;}
.reader .chapter section:last-child p:last-child{margin-bottom:0;}
.chapter, .foreword, #foreword{scroll-margin-top:24px;}
.chapter p, .foreword p{scroll-margin-top:18px;}

/* 关键词高亮（来自报告/索引页 ?kw= 跳转） */
mark.kw-hl{background:linear-gradient(transparent 60%, rgba(214,160,60,.55) 0);
  color:inherit;padding:0 1px;border-radius:2px;scroll-margin-top:18px;}
mark.kw-hl.active{background:linear-gradient(transparent 50%, rgba(196,58,38,.72) 0);
  box-shadow:0 0 0 2px rgba(196,58,38,.28);}

/* 高亮悬浮条 */
#kwbar{position:fixed;left:50%;transform:translateX(-50%);bottom:18px;z-index:9997;
  display:none;align-items:center;gap:10px;max-width:92vw;padding:9px 14px;border-radius:24px;
  border:1px solid var(--line);background:var(--surface);color:var(--ink);
  box-shadow:0 8px 24px rgba(31,28,23,.22);font-size:13px;}
#kwbar.show{display:flex;}
#kwbar b{color:var(--primary);}
#kwbar button{font:inherit;cursor:pointer;border:1px solid var(--line);
  background:var(--surface-2,var(--surface));color:var(--ink);border-radius:16px;
  padding:5px 11px;transition:background-color .2s,color .2s,border-color .2s;}
#kwbar button:hover{background:var(--primary);color:#fff;border-color:var(--primary);}
#kwbar .kw-close{border-color:var(--accent);color:var(--accent);}
#kwbar .kw-close:hover{background:var(--accent);color:#fff;border-color:var(--accent);}
@media(max-width:560px){#kwbar{flex-wrap:wrap;bottom:10px;font-size:12px;gap:6px;
  justify-content:center;}}
@media print{#kwbar{display:none!important;}}

/* 阅读进度条 */
#progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:9998;
  background:linear-gradient(90deg,var(--accent),var(--gold));
  transition:width .08s linear;}
/* 回到顶部 */
#toTop{position:fixed;right:18px;bottom:22px;z-index:9998;width:44px;height:44px;
  border-radius:50%;border:1px solid var(--line);background:var(--surface);
  color:var(--primary-d);font-size:18px;cursor:pointer;display:flex;
  align-items:center;justify-content:center;box-shadow:0 4px 14px rgba(31,28,23,.18);
  opacity:0;pointer-events:none;transition:opacity .3s ease,transform .2s ease;}
#toTop:hover{transform:translateY(-2px);}

/* 页脚 */
.reader .reader-foot{text-align:center;color:var(--muted);font-size:12px;margin-top:60px;
  padding-top:22px;border-top:1px solid var(--line);}

@media(max-width:480px){
  .reader{padding:0 16px 120px;}
  .reader .chapter p{font-size:16px;}
  .reader .chapter h2{font-size:20px;}
}
@media print{
  #progress,#toTop,.dm-toggle{display:none!important;}
  .toc{break-inside:avoid;}
}
"""


DARK_TOGGLE = """
<script>
(function(){
  var KEY='wz-dark';
  function apply(d){ document.body.classList.toggle('dark', d); }
  function sync(){
    var b=document.querySelector('.dm-toggle');
    if(b){ var d=document.body.classList.contains('dark'); b.textContent = d ? '☀ 浅色' : '🌙 深色'; }
  }
  function buildBtn(){
    var s=document.createElement('style');
    s.textContent='.dm-toggle{position:fixed;top:16px;right:16px;z-index:9999;display:inline-flex;align-items:center;gap:6px;padding:8px 15px;border-radius:20px;cursor:pointer;font-family:\\'PingFang SC\\',\\'Microsoft YaHei\\',\\'Noto Sans SC\\',sans-serif;font-size:13px;font-weight:600;border:1px solid var(--line,var(--rc-line,#e3ddcf));background:var(--surface,var(--rc-surface,#fffdf8));color:var(--primary-d,var(--rc-primary-d,#1f3a5f));box-shadow:0 4px 14px rgba(31,28,23,.18);transition:transform .2s ease,background-color .35s ease,color .35s ease,border-color .35s ease}.dm-toggle:hover{transform:translateY(-2px)}';
    document.head.appendChild(s);
    var b=document.createElement('button');
    b.className='dm-toggle';
    b.setAttribute('aria-label','切换深色模式');
    b.addEventListener('click', function(){
      var d=!document.body.classList.contains('dark');
      apply(d);
      try{ localStorage.setItem(KEY, d?'1':'0'); }catch(e){}
      sync();
      broadcast(d);
    });
    document.body.appendChild(b);
  }
  function broadcast(d){
    try{
      if(window.parent!==window){ window.parent.postMessage({wzTheme:d?'dark':'light'},'*'); }
      else{ var fs=document.querySelectorAll('iframe'); for(var i=0;i<fs.length;i++){ try{ fs[i].contentWindow.postMessage({wzTheme:d?'dark':'light'},'*'); }catch(e){} } }
    }catch(e){}
  }
  var saved=null;
  try{ saved=localStorage.getItem(KEY); }catch(e){}
  var prefers = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  apply(saved ? saved==='1' : !!prefers);
  buildBtn();
  sync();
  window.addEventListener('message', function(e){
    if(e.data && e.data.wzTheme){
      var d = e.data.wzTheme==='dark';
      apply(d);
      try{ localStorage.setItem(KEY, d?'1':'0'); }catch(err){}
      sync();
    }
  });
})();
</script>
"""

READER_JS = """
<script>
(function(){
  var bar=document.getElementById('progress');
  var top=document.getElementById('toTop');
  function upd(){
    var h=document.documentElement;
    var st=h.scrollTop||document.body.scrollTop;
    var sh=(h.scrollHeight-h.clientHeight)||1;
    if(bar) bar.style.width=(st/sh*100)+'%';
    if(top){ var show=st>600; top.style.opacity=show?'1':'0'; top.style.pointerEvents=show?'auto':'none'; }
  }
  window.addEventListener('scroll',upd,{passive:true});
  window.addEventListener('resize',upd);
  if(top) top.addEventListener('click',function(){ window.scrollTo({top:0,behavior:'smooth'}); });
  upd();
})();
</script>
"""

KW_JS = """
<script>
/* 关键词索引深链：?kw=关键词 高亮全文并滚动到首条；?loc=chN-pM 直接定位段落。
   来自「关键词索引」页或各报告内嵌索引挂件。 */
(function(){
  function param(n){var m=new RegExp('[?&]'+n+'=([^&]*)').exec(location.search);
    return m?decodeURIComponent(m[1].replace(/\\+/g,' ')):null;}
  function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  var kw=param('kw'); if(!kw) return;
  var loc=param('loc');
  var paras=Array.prototype.slice.call(document.querySelectorAll('.chapter p, .foreword p'));
  var kwEsc=kw.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&');
  var re=new RegExp(kwEsc,'g');
  var markCount=0;
  paras.forEach(function(p){
    var txt=p.textContent;
    if(txt.indexOf(kw)===-1) return;
    var out='',last=0,m; re.lastIndex=0;
    while((m=re.exec(txt))!==null){
      out+=esc(txt.slice(last,m.index));
      out+='<mark class="kw-hl">'+esc(m[0])+'</mark>';
      last=m.index+m[0].length;
      if(m.index===re.lastIndex) re.lastIndex++;
      markCount++;
    }
    out+=esc(txt.slice(last));
    p.innerHTML=out;
  });
  var marks=Array.prototype.slice.call(document.querySelectorAll('mark.kw-hl'));
  if(!marks.length) return;
  var bar=document.createElement('div'); bar.id='kwbar';
  bar.innerHTML='<span>关键词「<b>'+esc(kw)+'</b>」命中 <b class="kw-n">'+marks.length
    +'</b> 处</span>'
    +'<button class="kw-prev" type="button">↑ 上一条</button>'
    +'<button class="kw-next" type="button">↓ 下一条</button>'
    +'<button class="kw-close" type="button">✕ 取消高亮</button>';
  document.body.appendChild(bar);
  var cur=-1;
  function goto(i){
    if(!marks.length) return;
    if(cur>=0 && marks[cur]) marks[cur].classList.remove('active');
    cur=(i+marks.length)%marks.length;
    var el=marks[cur]; el.classList.add('active');
    el.scrollIntoView({behavior:'smooth',block:'center'});
  }
  bar.querySelector('.kw-next').addEventListener('click',function(){goto(cur+1);});
  bar.querySelector('.kw-prev').addEventListener('click',function(){goto(cur-1);});
  bar.querySelector('.kw-close').addEventListener('click',function(){
    marks.forEach(function(m){ var t=document.createTextNode(m.textContent); m.parentNode.replaceChild(t,m); });
    bar.classList.remove('show');
    try{ history.replaceState(null,'',location.pathname+location.hash); }catch(e){}
  });
  bar.classList.add('show');
  if(loc){
    var target=document.getElementById(loc);
    if(target){ target.scrollIntoView({behavior:'smooth',block:'start'});
      var inLoc=target.querySelector('mark.kw-hl');
      if(inLoc){ cur=marks.indexOf(inLoc); inLoc.classList.add('active'); }
      return;
    }
  }
  goto(0);
})();
</script>
"""


def build():
    fore_lines, chapters = load()
    title = "苇舟江湖梦"
    author = "霜月仲明"
    html = []
    html.append("<!DOCTYPE html>")
    html.append('<html lang="zh-CN">')
    html.append("<head>")
    html.append('  <meta charset="utf-8">')
    html.append('  <meta name="viewport" content="width=device-width, initial-scale=1">')
    html.append("  <title>%s · 原文阅读</title>" % title)
    html.append('  <link rel="stylesheet" href="%s">' % THEME_HREF)
    html.append("  <style>%s</style>" % CSS)
    html.append("</head>")
    html.append("<body>")
    html.append('<div id="progress"></div>')
    html.append('<main class="reader">')
    # 封面页眉
    html.append('  <header class="cover">')
    html.append("    <h1>%s</h1>" % title)
    html.append('    <p>%s · 著</p>' % author)
    html.append('    <p class="cov-sub">长篇武侠 · 原文阅读（未删节）</p>')
    html.append("  </header>")
    # 目录
    html.append(render_toc(chapters))
    # 序
    html.append(render_foreword(fore_lines))
    # 各章
    html.append(render_chapters(chapters))
    # 页脚
    html.append('  <div class="reader-foot">%s · 原文整理自 full_text.txt · 共 %d 章</div>' % (title, len(chapters)))
    html.append("</main>")
    html.append('<button id="toTop" aria-label="回到顶部" title="回到顶部">↑</button>')
    html.append(DARK_TOGGLE)
    html.append(READER_JS)
    html.append(KW_JS)
    html.append("</body>")
    html.append("</html>")
    out = "\n".join(html)
    io.open(OUT, "w", encoding="utf-8").write(out)
    return OUT, len(chapters)


if __name__ == "__main__":
    out, n = build()
    print("已生成:", out)
    print("章节数:", n)
