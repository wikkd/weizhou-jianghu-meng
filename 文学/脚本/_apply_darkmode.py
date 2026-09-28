# -*- coding: utf-8 -*-
"""报告页 DEV_RULES 合规后处理（幂等）：
  1. 深色切换注入（body.dark + 胶囊按钮 + 初始自广播，echarts/SVG 主题热更新）
  2. 「返回报告中心」入口（交互四件套：来路/逃生口；index 自身跳过）
  3. localStorage 键统一 wzjm_ 前缀（自动迁移旧键：wz-dark/wz-lib-*/mm-theme）
  4. 图标使用内联 SVG（禁 emoji 图标）
用法：python 脚本/_apply_darkmode.py
"""
import io, os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "产物")

MIG_MARK = 'id="wzjm-key-migration"'
KEYMAP = [("wzjm_dark", "wz-dark"), ("wzjm_lib_dark", "wz-lib-dark"),
          ("wzjm_lib_accent", "wz-lib-accent"), ("wzjm_mm_theme", "mm-theme")]
MIG_SCRIPT = ('<script ' + MIG_MARK + '>try{'
              + "".join('var n%d=localStorage.getItem("%s");if(n%d===null){var o%d=localStorage.getItem("%s");if(o%d!==null)localStorage.setItem("%s",o%d);}'
                        % (i, new, i, i, old, i, new, i)
                        for i, (new, old) in enumerate(KEYMAP))
              + '}catch(e){}</script>')

DM_SCRIPT = r"""
<script>
(function(){
  var KEY='wzjm_dark';
  function apply(d){ document.body.classList.toggle('dark', d); }
  var SUN='<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  var MOON='<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
  function sync(){
    var b=document.querySelector('.dm-toggle');
    if(b){ var d=document.body.classList.contains('dark'); b.innerHTML = d ? SUN+'<span>浅色</span>' : MOON+'<span>深色</span>'; }
  }
  function buildBtn(){
    var s=document.createElement('style');
    s.textContent='.dm-cluster{position:fixed;top:16px;right:16px;z-index:9999;display:flex;gap:8px}'
    +'.dm-toggle,.dm-back{display:inline-flex;align-items:center;gap:6px;padding:8px 15px;border-radius:999px;cursor:pointer;'
    +"font-family:'HarmonyOS Sans SC','PingFang SC','Microsoft YaHei',sans-serif;font-size:12.5px;font-weight:500;"
    +'border:1px solid var(--line,var(--rc-line,#dfe3e8));background:var(--surface,var(--rc-surface,#fff));'
    +'color:var(--primary,var(--rc-primary,#0A59F7));box-shadow:0 4px 14px rgba(24,36,49,.14);'
    +'transition:transform .2s cubic-bezier(.25,0,.3,1),background-color .3s,color .3s,border-color .3s}'
    +'.dm-toggle:hover,.dm-back:hover{transform:translateY(-2px)}'
    +'.dm-back{text-decoration:none}';
    document.head.appendChild(s);
    var c=document.createElement('div');c.className='dm-cluster';
    var backHref='__BACK__';
    if(backHref){
      var a=document.createElement('a');a.className='dm-back';a.href=backHref;
      a.setAttribute('aria-label','返回报告中心');a.textContent='报告中心';
      c.appendChild(a);
    }
    var b=document.createElement('button');b.className='dm-toggle';
    b.setAttribute('aria-label','切换深色模式');
    b.addEventListener('click', function(){
      var d=!document.body.classList.contains('dark');
      apply(d);
      try{ localStorage.setItem(KEY, d?'1':'0'); }catch(e){}
      sync(); broadcast(d);
    });
    c.appendChild(b);
    document.body.appendChild(c);
  }
  function broadcast(d){
    try{
      window.postMessage({wzTheme:d?'dark':'light'},'*');   /* 自广播：图表主题热更新 */
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
  setTimeout(function(){ broadcast(document.body.classList.contains('dark')); },0);
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

DM_MARKER_RE = re.compile(r"<script>\s*\(function\(\)\{\s*var KEY='wz(?:jm)?_dark';.*?\}\)\(\);\s*</script>", re.S)


def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(s)


def back_href(rel):
    """返回分析中心：index.html 自身不注入；子目录 → ../index.html；根 → index.html。"""
    if rel.replace("\\", "/") == "index.html":
        return None  # 自身即中心
    d = os.path.dirname(rel)
    return ("../index.html" if d else "index.html")


def normalize_keys(html):
    """localStorage 键统一 wzjm_ 前缀：head 首位插迁移脚本 + 字面量替换。"""
    changed = False
    if MIG_MARK not in html:
        m = re.search(r"<head[^>]*>", html, re.I)
        if m:
            html = html[:m.end()] + "\n" + MIG_SCRIPT + html[m.end():]
            changed = True
    for new, old in KEYMAP:
        for q in ("'", '"'):
            if q + old + q in html:
                html = html.replace(q + old + q, q + new + q)
                changed = True
    return html, changed


BACK_ONLY = r"""
<script data-wzjm-backonly>
(function(){
  var backHref='__BACK__';
  if(!backHref) return;
  function build(){
    if(document.querySelector('.dm-back')) return;
    var s=document.createElement('style');
    s.textContent='.dm-back{position:fixed;top:16px;right:16px;z-index:9999;display:inline-flex;align-items:center;gap:6px;padding:8px 15px;border-radius:999px;cursor:pointer;font-size:13px;font-weight:600;text-decoration:none;border:1px solid rgba(127,127,127,.35);background:rgba(127,127,127,.12);color:inherit;box-shadow:0 4px 14px rgba(0,0,0,.15);transition:transform .2s ease}.dm-back:hover{transform:translateY(-2px)}';
    document.head.appendChild(s);
    var a=document.createElement('a');a.className='dm-back';a.href=backHref;
    a.innerHTML='<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M15 18l-6-6 6-6"/></svg><span>分析中心</span>';
    document.body.appendChild(a);
  }
  if(document.body){build();}else{document.addEventListener('DOMContentLoaded',build);}
})();
</script>
"""
BACK_MARK_RE = re.compile(r'<script data-wzjm-backonly>[\s\S]*?</script>')


def inject_back_only(rel):
    full = os.path.join(BASE, rel)
    if not os.path.exists(full):
        return
    html = read(full)
    if "</body>" not in html:
        return
    html = BACK_MARK_RE.sub("", html, count=1)
    href = back_href(rel)
    if not href:
        return
    html = html.replace("</body>", BACK_ONLY.replace("__BACK__", href, 1) + "\n</body>", 1)
    write(full, html)
    print("  [返回钮] " + rel)


def inject_dm(rel):
    full = os.path.join(BASE, rel)
    if not os.path.exists(full):
        print("  [跳过·不存在] " + rel); return
    html = read(full)
    if "</body>" not in html:
        print("  [跳过·无</body>] " + rel); return
    # 移除旧版注入块（标记正则保证唯一），无条件重建最新版
    html = DM_MARKER_RE.sub("", html, count=1)
    html = html.replace("</body>", DM_SCRIPT.replace("__BACK__",
                        back_href(rel) or "", 1) + "\n</body>", 1)
    write(full, html)
    print("  [已注入] " + rel)


def rel_pages():
    out = []
    for p in glob.glob(os.path.join(BASE, "*.html")) + glob.glob(os.path.join(BASE, "*", "*.html")):
        out.append(os.path.relpath(p, BASE).replace("\\", "/"))
    return sorted(out)


TARGETS = [
    "苇舟江湖梦_统计推断.html",
    "苇舟江湖梦_风格计量.html",
    "苇舟江湖梦_词汇计量.html",
    "苇舟江湖梦_情感时序.html",
    "苇舟江湖梦_空间地点分析报告.html",
    "苇舟江湖梦_官制考究.html",
    "苇舟江湖梦_地理位置关系图.html",
    "苇舟江湖梦_章节标签量化看板.html",
    "苇舟江湖梦_章节结构量化.html",
    "苇舟江湖梦_时间节奏量化.html",
    "苇舟江湖梦_人物关系网络.html",
    "苇舟江湖梦_派生维度量化.html",
    "苇舟江湖梦_分析报告.html",
    "苇舟江湖梦_可视化叙事系统.html",
    "苇舟江湖梦_扩展叙事可视化.html",
    "苇舟江湖梦_深度叙事可视化.html",
    "苇舟江湖梦_报告归纳整理.html",
    "苇舟江湖梦_原文阅读.html",
    "数据归档/苇舟江湖梦_数据归档总览.html",
    "05_制度家族/川阴王建都推演.html",
    "05_制度家族/黄家概况.html",
    "00_总览导航/苇舟江湖梦_关键词索引.html",
    "00_总览导航/苇舟江湖梦_分析报告.html",
    "00_总览导航/苇舟江湖梦_原文阅读.html",
    "00_总览导航/苇舟江湖梦_图书馆.html",
    "00_总览导航/苇舟江湖梦_报告归纳整理.html",
    "00_总览导航/苇舟江湖梦_组件库.html",
    "index.html",
]


def main():
    # 1) 全页存储键规范化（含未注入页：美学图谱/图书馆/子目录研究页等）
    n_ok = 0
    pages = rel_pages()
    for rel in pages:
        full = os.path.join(BASE, rel)
        html = read(full)
        html2, changed = normalize_keys(html)
        if changed:
            write(full, html2); n_ok += 1
    print("[键规范化] 处理 %d 页（迁移 snippet + 字面量替换）" % n_ok)
    # 2) 深色切换 + 返回入口：全量注入（自带主题系统的外壳页跳过，防双按钮）
    for rel in pages:
        if rel.replace("\\", "/") in SKIP_DM:
            inject_back_only(rel)   # 自带主题系统：只补返回钮，防双主题按钮
            continue
        inject_dm(rel)
    print("\n完成。")


# 自带完整主题系统的页面（键规范化仍生效，DM 注入跳过）
SKIP_DM = {
    "index.html",          # 分析中心（自带主题钮，即中心本身）
    "library.html",        # 数字图书馆外壳（自带主题系统 + 顶栏已有返回链接）
    "美学图谱.html",        # 自带 mm 主题系统（back-only 补返回钮）
}


if __name__ == "__main__":
    main()
