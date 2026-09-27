# -*- coding: utf-8 -*-
"""_chartlib.py — 《苇舟江湖梦》图表就地升级共享库。
把报告的静态 SVG 图表替换为 ECharts 交互式动态图表（依赖 产物/echarts-kit.js）。
提供：
  · card(title, chart_id, controls, n, hint, height)  —— 生成交互式卡片 HTML（含控制条）
  · init(chart_id, option_js, controls, n, anchor)    —— 生成 <script> 注入块
  · generic_extra(chart_id, controls, n)              —— 通用时间轴/实时流接线 JS
  · replace_svg_cards(html, cards)                    —— 按序替换报告内的 SVG 卡片
  · inject_script(html, script)                       —— 在 </body> 前注入脚本
控件 id 以 chart_id 为命名空间，支持同一报告多图表互不冲突。
"""
import re

SVG_CARD = re.compile(r'<div class="card[^"]*">\s*<svg\b.*?</svg>\s*</div>', re.DOTALL)
SVG_ANY = re.compile(r'<svg\b.*?</svg>', re.DOTALL)


def controls_html(prefix, kind, n):
    if not kind or kind == "none":
        return ""
    parts = ['<div class="wz-controls">']
    if kind in ("timeline", "both"):
        parts.append(
            '<div class="wz-ctrl-group">'
            '<button id="%s-play" class="wz-btn" type="button">▶ 播放时间轴</button>'
            '<input id="%s-seek" class="wz-seek" type="range" min="1" max="%d" value="%d">'
            '<span id="%s-frame" class="wz-frame">第 %d / %d</span></div>' % (prefix, prefix, n, n, prefix, n, n))
    if kind in ("live", "both"):
        parts.append(
            '<div class="wz-ctrl-group">'
            '<button id="%s-live" class="wz-btn" type="button">⦿ 模拟实时数据流</button>'
            '<span id="%s-dot" class="wz-dot"></span></div>' % (prefix, prefix))
    parts.append('</div>')
    return "".join(parts)


def card(title, chart_id, controls, n, hint=None, height=440):
    c = controls_html(chart_id, controls, n) if controls else ""
    h = ('<p class="wz-hint">%s</p>' % hint) if hint else ""
    return (
        '<!--WZ-CHART-BLOCK-START-->\n'
        '<h2>%s</h2>\n'
        '<div class="card wz-chart-card">\n'
        '%s'
        '<div id="%s" data-wz-chart style="width:100%%;height:%dpx"></div>\n'
        '%s'
        '</div>\n'
        '<!--WZ-CHART-BLOCK-END-->\n'
    ) % (title, c, chart_id, height, h)


def generic_extra(chart_id, controls, n):
    if not controls or controls == "none":
        return ""
    js = []
    if controls in ("timeline", "both"):
        js.append("""
  (function(){
    var playBtn=document.getElementById('%s-play'); var seekEl=document.getElementById('%s-seek'); var frameEl=document.getElementById('%s-frame');
    if(!playBtn) return;
    var player = WZ.timelinePlayer(chart, { max:%d, step:200,
      onFrame:function(t){
        var opt=chart.getOption();
        var xo=opt.xAxis; var xArr=Array.isArray(xo)?xo:[xo];
        var xs=(((xArr[0]||{}).data)||[]).slice(0,t);
        var ss=opt.series.map(function(s){ return {data:(s.data||[]).slice(0,t)}; });
        chart.setOption({xAxis:{data:xs}, series:ss});
        seekEl.value=t; frameEl.textContent='第 '+t+' / %d';
        if(t>=%d){ playBtn.classList.remove('active'); playBtn.textContent='▶ 重播时间轴'; }
      }});
    playBtn.addEventListener('click',function(){
      if(player.isPlaying()){ player.pause(); playBtn.classList.remove('active'); playBtn.textContent='▶ 播放时间轴'; }
      else { player.play(); playBtn.classList.add('active'); playBtn.textContent='⏸ 暂停'; }
    });
    seekEl.addEventListener('input',function(e){ player.pause(); playBtn.classList.remove('active'); playBtn.textContent='▶ 播放时间轴'; player.seek(parseInt(e.target.value,10)); });
  })();""" % (chart_id, chart_id, chart_id, n, n, n))
    if controls in ("live", "both"):
        js.append("""
  (function(){
    var liveBtn=document.getElementById('%s-live'); var dot=document.getElementById('%s-dot');
    if(!liveBtn) return;
    var live = WZ.liveStream({ interval:1400,
      onState:function(on){ liveBtn.classList.toggle('active',on); liveBtn.classList.toggle('wz-live',on); dot.classList.toggle('live',on); liveBtn.textContent= on?'■ 停止实时流':'⦿ 模拟实时数据流'; },
      onTick:function(){
        var opt=chart.getOption();
        var ss=opt.series.map(function(s){
          if(s.type==='pie'||s.type==='graph'||s.type==='tree'||s.type==='sankey') return {};
          var d=s.data||[]; if(!d.length||typeof d[0]!=='number') return {};
          var K=Math.min(8,d.length);
          for(var i=d.length-K;i<d.length;i++){ d[i]=Math.max(0, d[i]+(Math.random()-0.5)*Math.abs(d[i]+1e-6)*0.12); }
          return {data:d};
        });
        chart.setOption({series:ss});
      }
    });
    liveBtn.addEventListener('click',function(){ live.toggle(); });
  })();""" % (chart_id, chart_id))
    return "\n".join(js)


def init(chart_id, option_js, controls, n, anchor="WZ", onclick=None):
    extra = generic_extra(chart_id, controls, n) if controls and controls != "none" else ""
    click = ("  chart.on('click', function(p){ %s });\n" % onclick) if onclick else ""
    return (
        '<!--%s-SCRIPT-START-->\n'
        '<script src="echarts-kit.js"></script>\n'
        '<script>\n'
        'WZ.ready(function(){\n'
        '  var chart = WZ.chart(document.getElementById("%s"), %s, {});\n'
        '%s\n%s'
        '});\n'
        '</script>\n'
        '<!--%s-SCRIPT-END-->\n'
    ) % (anchor, chart_id, option_js, extra, click, anchor)


def replace_svg_cards(html, cards):
    it = iter(cards)
    def sub(m):
        try:
            return next(it)
        except StopIteration:
            return m.group(0)
    return SVG_CARD.sub(sub, html, count=len(cards))


def replace_heading_block(html, old_title, new_title, new_html):
    """按 <h2> 标题块就地替换图表区域（兼容首次升级与重复升级）。
    以标题「前缀」匹配（报告 h2 常带括号后缀），优先 old_title，其次 new_title，
    最后回退到 SVG 卡片匹配。new_html 自身应包含 <h2> 标题。"""
    for t in (old_title, new_title):
        pat = re.compile(re.escape("<h2>") + re.escape(t) +
                         r"[\s\S]*?(?=<h2>|</body>)", re.DOTALL)
        if pat.search(html):
            return pat.sub(new_html, html, count=1)
    return replace_svg_cards(html, [new_html])


def bundle(charts, anchor="WZ", onclick=None):
    """charts: list of (chart_id, option_js, controls, n)。
    生成「单个 echarts-kit.js 加载 + 单个 <script> 含多个 WZ.ready 闭包」，
    每个图表自带控件接线（时间轴/实时流），避免重复加载与实例引用错乱。
    onclick: 可选 dict {chart_id: JS片段}，在该图表的 WZ.ready 闭包内
      chart.on('click', function(p){ <JS片段> }) 接线（p 为点击参数，chart 为实例）。"""
    onclick = onclick or {}
    blocks = []
    for (cid, opt, ctl, n) in charts:
        extra = generic_extra(cid, ctl, n) if ctl and ctl != "none" else ""
        click = ("  chart.on('click', function(p){ %s });\n" % onclick[cid]) if cid in onclick else ""
        blocks.append(
            "WZ.ready(function(){\n"
            "  var chart = WZ.chart(document.getElementById(\"%s\"), %s, {});\n"
            "%s\n%s"
            "});" % (cid, opt, extra, click))
    body = "\n\n".join(blocks)
    return (
        "<!--%s-SCRIPT-START-->\n"
        '<script src="echarts-kit.js"></script>\n'
        "<script>\n%s\n</script>\n"
        "<!--%s-SCRIPT-END-->\n"
    ) % (anchor, body, anchor)


def inject_script(html, script):
    # 先移除旧的同锚点脚本（幂等），再注入
    anchor = "WZ-SCRIPT-START"
    html = re.sub(r'<!--%s-->[\s\S]*?<!--WZ-SCRIPT-END-->\s*' % anchor, "", html)
    return html.replace("</body>", script + "\n</body>", 1)


def load_json(path):
    import json, io
    with io.open(path, "r", encoding="utf-8") as f:
        return json.load(f)
