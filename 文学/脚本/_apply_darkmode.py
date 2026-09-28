# -*- coding: utf-8 -*-
"""
为所有报告页面注入「自包含深色切换脚本」。
- 兼容 theme.css（报告页）与 site.css（报告中心外壳）两套 Token：按钮样式用双变量回退 var(--x, var(--rc-x, fallback))
- 切换时：① 切换 body.dark ② 存 localStorage ③ 广播主题
  · 若在 iframe 内（报告页）：向 parent 广播（外壳可忽略）
  · 若在顶层且有 iframe（报告中心）：向所有 iframe 广播（联动 iframe 报告）
  · 接收 parent 广播（报告页）：应用主题
用法：python3 脚本/_apply_darkmode.py
"""
import os, glob, io, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 需要注入的页面（排除已自带深色模式的 美学图谱.html）
TARGETS = [
    "产物/川阴王建都推演.html",
    "产物/苇舟江湖梦_统计推断.html",
    "产物/苇舟江湖梦_风格计量.html",
    "产物/苇舟江湖梦_词汇计量.html",
    "产物/苇舟江湖梦_情感时序.html",
    "产物/苇舟江湖梦_空间地点分析报告.html",
    "产物/苇舟江湖梦_官制考究.html",
    "产物/苇舟江湖梦_地理位置关系图.html",
    "产物/苇舟江湖梦_章节标签量化看板.html",
    "产物/苇舟江湖梦_章节结构量化.html",
    "产物/苇舟江湖梦_时间节奏量化.html",
    "产物/苇舟江湖梦_人物关系网络.html",
    "产物/数据归档/苇舟江湖梦_数据归档总览.html",
    "产物/苇舟江湖梦_派生维度量化.html",
    "产物/苇舟江湖梦_分析报告.html",
    "产物/index.html",
    "产物/报告中心/index.html",
]

DM_SCRIPT = r"""
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
    s.textContent='.dm-toggle{position:fixed;top:16px;right:16px;z-index:9999;display:inline-flex;align-items:center;gap:6px;padding:8px 15px;border-radius:20px;cursor:pointer;font-family:\'PingFang SC\',\'Microsoft YaHei\',\'Noto Sans SC\',sans-serif;font-size:13px;font-weight:600;border:1px solid var(--line,var(--rc-line,#e3ddcf));background:var(--surface,var(--rc-surface,#fffdf8));color:var(--primary-d,var(--rc-primary-d,#1f3a5f));box-shadow:0 4px 14px rgba(31,28,23,.18);transition:transform .2s ease,background-color .35s ease,color .35s ease,border-color .35s ease}.dm-toggle:hover{transform:translateY(-2px)}';
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
      window.postMessage({wzTheme:d?'dark':'light'},'*');   /* 自广播：echarts-kit 重绘 */
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

def inject(path):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        print("  [跳过·不存在] " + path); return False
    with io.open(full, "r", encoding="utf-8") as f:
        html = f.read()
    # 移除旧版注入（无自广播），保证升级到新版脚本
    html = re.sub(r"<script>\s*\(function\(\)\{\s*var KEY='wz-dark';.*?\}\)\(\);\s*</script>",
                  "", html, count=1, flags=re.S)
    if "dm-toggle" in html:
        print("  [跳过·已注入] " + path); return False
    if "</body>" not in html:
        print("  [跳过·无</body>] " + path); return False
    html = html.replace("</body>", DM_SCRIPT + "\n</body>", 1)
    with io.open(full, "w", encoding="utf-8") as f:
        f.write(html)
    print("  [已注入] " + path); return True

if __name__ == "__main__":
    ok = 0
    for t in TARGETS:
        if inject(t): ok += 1
    print("\n完成：共注入 %d 个文件。" % ok)
