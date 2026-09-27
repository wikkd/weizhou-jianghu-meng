# -*- coding: utf-8 -*-
"""重建《苇舟江湖梦》章节标签量化看板：保留原图表脚本块（含被截断的情节演进数据），
将五个分布图折叠为标签页「分布速览」，情节演进设为核心图，移除模拟实时数据流，
收紧 KPI 与层级。仅重写 DOM 结构，图表初始化逻辑逐字复用原文件。"""
import re, io, sys

SRC = "/Users/shuangyuexingxun/Desktop/苇舟江湖梦/产物/苇舟江湖梦_章节标签量化看板.html"
OUT = SRC

src = io.open(SRC, encoding="utf-8").read()

# —— 逐字抽取原文件中的关键脚本块（避免触及被截断的情节演进数据）——
embed = re.search(r"<script data-wz-embed>.*?</script>", src, re.S).group(0)
chart_block = re.search(r"<!--WZ-SCRIPT-START-->.*?<!--WZ-SCRIPT-END-->", src, re.S).group(0)
# 移除「模拟实时数据流」死代码（按钮已被移除，仅为源码整洁）
chart_block = re.sub(r"\s*\(function\(\)\{\s*var liveBtn=document\.getElementById\('db_dash-live'\).*?\}\)\(\);", "", chart_block, flags=re.S)
dark = re.search(r"<script>\s*\(function\(\)\{\s*var KEY='wz-dark'.*?</script>", src, re.S).group(0)
kw = re.search(r"<!--WZ-KEYINDEX-START-->.*?<!--WZ-KEYINDEX-END-->", src, re.S).group(0)

# —— 将「索引跳转」直接集成进图表：点击图表元素 → 打开原文阅读并高亮 / 定位 ——
# 三个目标图表当前以 WZ.chart(dom, builder, {}) 结尾；向第三个参注入 onClick。
# db_dash：折线节点 → ?loc=chN（章节定位）；db_loc/db_chp：柱条 → ?kw=<名称>（原文高亮）。
def inject_onclick(block, chart_id, handler):
    key = 'getElementById("%s")' % chart_id
    s = block.index(key)
    mark = '}, {});'
    e = block.index(mark, s)  # 该图表自身的结尾（内部不会出现 '}, {});'）
    return block[:e] + '}, {onClick:function(p,inst){%s}});' % handler + block[e + len(mark):]

chart_block = inject_onclick(chart_block, "db_dash",
    "if(p&&p.name){var ch=parseInt(p.name,10);if(!isNaN(ch)){window.open('苇舟江湖梦_原文阅读.html?loc=ch'+ch,'_blank','noopener');}}")
chart_block = inject_onclick(chart_block, "db_loc",
    "if(p&&p.name){window.open('苇舟江湖梦_原文阅读.html?kw='+encodeURIComponent(p.name),'_blank','noopener');}")
chart_block = inject_onclick(chart_block, "db_chp",
    "if(p&&p.name){window.open('苇舟江湖梦_原文阅读.html?kw='+encodeURIComponent(p.name),'_blank','noopener');}")

NEW_HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>《苇舟江湖梦》章节标签量化看板</title>
<link rel="stylesheet" href="glass.css">
<style>
  /* 看板紧凑化：区块层级 + 分布标签页 */
  .dash-intro{color:var(--muted);font-size:13.5px;line-height:1.72;margin:-4px 0 18px;max-width:86ch}
  .dash-block{margin-top:34px}
  .dash-block h2{font-size:19px;font-weight:800;margin:0 0 6px;display:flex;align-items:center;gap:10px}
  .dash-block h2::before{content:"";width:5px;height:20px;border-radius:20px;background:var(--band)}
  .cards{margin:14px 0 6px}
  .dist-tabs{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 18px}
  .dist-tab{font-family:inherit;font-size:13px;font-weight:600;padding:8px 16px;border-radius:var(--radius-pill);
    cursor:pointer;border:1px solid var(--glass-border);background:var(--glass-bg-soft);color:var(--muted);
    transition:background var(--dur) var(--ease),color var(--dur) var(--ease),border-color var(--dur) var(--ease),box-shadow var(--dur) var(--ease)}
  .dist-tab:hover{color:var(--ink);border-color:var(--primary)}
  .dist-tab.is-active{background:var(--primary);border-color:var(--primary);color:#fff;box-shadow:0 4px 14px rgba(10,132,255,.25)}
  .dist-pane{display:none}
  .dist-pane.is-active{display:block;animation:glass-fade-up .42s var(--ease) both}
  /* 可点击跳转图表的指针提示 */
  .chart-clickable{cursor:pointer}
</style>
</head>
<body>
"""

HEADER = (
    '<header>\n'
    '<h1>《苇舟江湖梦》章节标签量化看板</h1>\n'
    '<p>59 章受控词表标注 · 章节类型、情节演进、感情线与人物 / 地点热度的聚合视图。数据源自全文本分章结构化标签。</p>\n'
    '</header>\n'
)

KPI = (
    '<div class="cards">'
    '<div class="card"><div class="kpi-v">59 章</div><div class="kpi-l">总章节</div></div>'
    '<div class="card"><div class="kpi-v">184,624 字</div><div class="kpi-l">总字数</div></div>'
    '<div class="card"><div class="kpi-v">39 / 59</div><div class="kpi-l">战斗章占比 66%</div></div>'
    '<div class="card"><div class="kpi-v">101 种</div><div class="kpi-l">标注人物</div></div>'
    '<div class="card"><div class="kpi-v">32 种</div><div class="kpi-l">标注地点</div></div>'
    '<div class="card"><div class="kpi-v">11 章</div><div class="kpi-l">高强度战斗(3级)</div></div>'
    '</div>\n'
)

SECTION1 = (
    '<section class="dash-block">\n'
    '<h2>一、情节演进 · 时间层与战斗强度</h2>\n'
    '<p class="dash-intro">沿 59 章推进，色带标示七个叙事时间层（初入江湖 → 大战 / 决战），折线为逐章战斗强度。'
    '点击「播放时间轴」逐章回放情节推进；拖动滑块可定位到任意章。</p>\n'
    '<div class="card wz-chart-card">\n'
    '<div class="wz-controls"><div class="wz-ctrl-group">\n'
    '<button id="db_dash-play" class="wz-btn" type="button">&#9654; 播放时间轴</button>\n'
    '<input id="db_dash-seek" class="wz-seek" type="range" min="1" max="59" value="59">\n'
    '<span id="db_dash-frame" class="wz-frame">第 59 / 59</span>\n'
    '</div></div>\n'
    '<div id="db_dash" data-wz-chart class="chart-clickable" style="width:100%;height:440px"></div>\n'
    '<p class="wz-hint">悬停查看章 · 时间层 · 战斗强度；拖动缩放；播放时间轴逐章推进；'
    '<b>点击折线节点跳转对应章节原文</b>。</p>\n'
    '</div>\n'
    '</section>\n'
)

SECTION2 = (
    '<section class="dash-block">\n'
    '<h2>二、分布速览</h2>\n'
    '<p class="dash-intro">五类受控标签的聚合分布，切换标签页查看：章节类型、感情线、战斗强度为全本占比；'
    '地点与人物为出现章数 Top 排行。</p>\n'
    '<div class="dist-tabs" id="distTabs">\n'
    '<button class="dist-tab is-active" data-dist="ct">章节类型</button>\n'
    '<button class="dist-tab" data-dist="emo">感情线</button>\n'
    '<button class="dist-tab" data-dist="civ">战斗强度</button>\n'
    '<button class="dist-tab" data-dist="loc">地点 Top15</button>\n'
    '<button class="dist-tab" data-dist="chp">人物 Top20</button>\n'
    '</div>\n'
    '<div class="dist-pane is-active" data-dist="ct" data-chart="db_ct"><div class="card wz-chart-card">'
    '<div id="db_ct" data-wz-chart style="width:100%;height:380px"></div>'
    '<p class="wz-hint">悬停查看章数。</p></div></div>\n'
    '<div class="dist-pane" data-dist="emo" data-chart="db_emo"><div class="card wz-chart-card">'
    '<div id="db_emo" data-wz-chart style="width:100%;height:380px"></div>'
    '<p class="wz-hint">悬停查看章数。</p></div></div>\n'
    '<div class="dist-pane" data-dist="civ" data-chart="db_civ"><div class="card wz-chart-card">'
    '<div id="db_civ" data-wz-chart style="width:100%;height:360px"></div>'
    '<p class="wz-hint">悬停查看章数。</p></div></div>\n'
    '<div class="dist-pane" data-dist="loc" data-chart="db_loc"><div class="card wz-chart-card">'
    '<div id="db_loc" data-wz-chart class="chart-clickable" style="width:100%;height:460px"></div>'
    '<p class="wz-hint">悬停查看出现章数；<b>点击柱条跳转原文并高亮该地点</b>。</p></div></div>\n'
    '<div class="dist-pane" data-dist="chp" data-chart="db_chp"><div class="card wz-chart-card">'
    '<div id="db_chp" data-wz-chart class="chart-clickable" style="width:100%;height:480px"></div>'
    '<p class="wz-hint">悬停查看出场章数；<b>点击柱条跳转原文并高亮该人物</b>。</p></div></div>\n'
    '</section>\n'
)

TAB_SCRIPT = (
    '<script>\n'
    '(function(){\n'
    '  var tabs = document.getElementById("distTabs");\n'
    '  if(!tabs) return;\n'
    '  var panes = document.querySelectorAll(".dist-pane");\n'
    '  function show(key){\n'
    '    Array.prototype.forEach.call(tabs.querySelectorAll(".dist-tab"), function(t){\n'
    '      t.classList.toggle("is-active", t.getAttribute("data-dist") === key);\n'
    '    });\n'
    '    Array.prototype.forEach.call(panes, function(p){\n'
    '      var on = p.getAttribute("data-dist") === key;\n'
    '      p.classList.toggle("is-active", on);\n'
    '      if(on){\n'
    '        var cid = p.getAttribute("data-chart");\n'
    '        requestAnimationFrame(function(){\n'
    '          var inst = window.WZ && WZ.getInstance && WZ.getInstance(cid);\n'
    '          if(inst){ try{ inst.resize(); }catch(e){} }\n'
    '        });\n'
    '      }\n'
    '    });\n'
    '  }\n'
    '  tabs.addEventListener("click", function(e){\n'
    '    var b = e.target.closest && e.target.closest(".dist-tab");\n'
    '    if(b) show(b.getAttribute("data-dist"));\n'
    '  });\n'
    '})();\n'
    '</script>\n'
)

out = (
    NEW_HEAD
    + embed + "\n"
    + HEADER
    + '<div class="wrap">\n'
    + KPI
    + SECTION1
    + SECTION2
    + '</div>\n'
    + chart_block + "\n"
    + TAB_SCRIPT
    + dark + "\n"
    + kw + "\n"
    + '</body>\n</html>\n'
)

io.open(OUT, "w", encoding="utf-8").write(out)
print("written", len(out), "bytes")
