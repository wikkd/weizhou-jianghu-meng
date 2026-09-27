# -*- coding: utf-8 -*-
"""就地升级《情感时序》报告：将静态 SVG 折线图替换为 ECharts 交互式动态图表。
- 交互：悬停 tooltip、dataZoom 缩放、图例筛选、点击数据点查看章节详情
- 动态：时间轴播放器（59 章逐章平滑演进）+ 实时数据流模拟（外部事件触发平滑重绘）
- 自动随深色模式 (body.dark) 换肤（依赖 echarts-kit.js 的 MutationObserver）
仅改写产物 HTML，不触碰任何源数据文件；数据取自已验证的 sentiment_series.json。
"""
import os, re, io, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_情感时序.html")
JSON = os.path.join(ROOT, "数据", "analysis", "sentiment_series.json")

with io.open(JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

CH = [c["chapter"] for c in data["chapters"]]
S = [c["sentiment"] for c in data["chapters"]]
C = [c["combat_intensity"] for c in data["chapters"]]
MEAN = data["mean"]
PEARSON = data["corr"]["pearson"]["r"]
N = len(CH)

# ---- 新的交互式图表卡片（替换原 SVG 卡片；用注释锚点保证可重复升级）----
NEW_CARD = (
    '<!--WZ-CHART-BLOCK-START-->\n'
    '<h2>情感时序 vs 战斗强度（交互式动态图表）</h2>\n'
    '<div class="card wz-chart-card">\n'
    '  <div class="wz-controls">\n'
    '    <div class="wz-ctrl-group">\n'
    '      <button id="wz-play" class="wz-btn" type="button" aria-label="播放时间轴">▶ 播放时间轴</button>\n'
    '      <input id="wz-seek" class="wz-seek" type="range" min="1" max="%d" value="%d" aria-label="时间轴进度">\n'
    '      <span id="wz-frame" class="wz-frame">第 %d / %d 章</span>\n'
    '    </div>\n'
    '    <div class="wz-ctrl-group">\n'
    '      <button id="wz-live" class="wz-btn" type="button" aria-label="模拟实时数据流">⦿ 模拟实时数据流</button>\n'
    '      <span id="wz-live-dot" class="wz-dot" aria-hidden="true"></span>\n'
    '    </div>\n'
    '  </div>\n'
    '  <div id="wz-chart" data-wz-chart style="width:100%%;height:440px"></div>\n'
    '  <div id="wz-detail" class="wz-detail" hidden></div>\n'
    '  <p class="wz-hint">交互：悬停查看逐章数值 · 拖动滑块缩放(dataZoom) · 点击图例筛选序列 · 点击数据点查看章节详情 · '
    '「播放时间轴」逐章演进 · 「模拟实时数据流」演示外部事件触发的平滑重绘。</p>\n'
    '</div>\n'
    '<!--WZ-CHART-BLOCK-END-->\n'
) % (N, N, N, N)

# ---- 内嵌初始化脚本 ----
INIT = """<!--WZ-SCRIPT-START-->
<script src="echarts-kit.js"></script>
<script>
WZ.ready(function(){
  var CH = %s;
  var S = %s;
  var C = %s;
  var MEAN = %s;
  var PEARSON = %s;
  var N = CH.length;

  function hexToRgba(hex,a){hex=hex.replace('#','');if(hex.length===3){hex=hex.split('').map(function(x){return x+x;}).join('');}var r=parseInt(hex.substr(0,2),16),g=parseInt(hex.substr(2,2),16),b=parseInt(hex.substr(4,2),16);return 'rgba('+r+','+g+','+b+','+a+')';}
  function emotion(s){return s>0.62?'偏正面':(s<0.40?'偏负面':'中性');}
  function combatLabel(c){return ['无战事','轻微冲突','中等交战','激烈大战'][c]||'—';}
  function strength(r){var a=Math.abs(r);return a<0.1?'可忽略':a<0.3?'弱':a<0.5?'中等':a<0.7?'较强':'强';}

  var chart = WZ.chart(document.getElementById('wz-chart'), function(vars){
    var palette = WZ.buildTheme().color;
    var blue = palette[0], red = palette[1];
    return {
      legend:{data:['情感 polarity','战斗强度'],top:6,icon:'roundRect'},
      grid:{left:50,right:50,top:42,bottom:72,containLabel:true},
      xAxis:{type:'category',boundaryGap:false,data:CH.map(function(c){return ('0'+c).slice(-2);}),name:'章',nameGap:30},
      yAxis:[
        {type:'value',name:'情感 polarity',min:0,max:1,position:'left',splitNumber:5},
        {type:'value',name:'战斗强度',min:0,max:3,position:'right',interval:1,splitNumber:3}
      ],
      series:[
        {name:'情感 polarity',type:'line',smooth:true,yAxisIndex:0,showSymbol:false,data:S,
          lineStyle:{width:2.4,color:blue},itemStyle:{color:blue},
          areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:hexToRgba(blue,0.20)},{offset:1,color:hexToRgba(blue,0)}])},
          markLine:{silent:true,symbol:'none',data:[{yAxis:MEAN}],lineStyle:{type:'dashed',color:vars.muted},label:{formatter:'均值 '+MEAN.toFixed(3),color:vars.muted,position:'insideEndTop'}},
          emphasis:{focus:'series'}},
        {name:'战斗强度',type:'line',yAxisIndex:1,step:'middle',showSymbol:true,symbolSize:5,data:C,
          lineStyle:{width:2,type:'dashed',color:red},itemStyle:{color:red},emphasis:{focus:'series'}}
      ],
      animationDuration:600,animationDurationUpdate:420,animationEasingUpdate:'cubicInOut'
    };
  }, {
    onClick:function(p){ if(p.componentType==='series' && p.dataIndex!=null){ showDetail(p.dataIndex); } }
  });

  function showDetail(i){
    var d=document.getElementById('wz-detail');
    d.hidden=false;
    d.innerHTML='<b>第 '+CH[i]+' 章</b> · 情感 polarity <b>'+S[i].toFixed(4)+'</b>（'+emotion(S[i])+'）'
      +' · 战斗强度 <b>'+C[i]+'</b>（'+combatLabel(C[i])+'）'
      +'<br><span class="wz-hint">Pearson r = '+PEARSON.toFixed(4)+'（'+strength(PEARSON)+'负相关）｜点击图例可筛选序列，拖动滑块缩放，悬停查看任意章。</span>';
  }

  // ---- 时间轴播放器：逐章平滑演进 ----
  var playBtn=document.getElementById('wz-play');
  var seekEl=document.getElementById('wz-seek');
  var frameEl=document.getElementById('wz-frame');
  var player = WZ.timelinePlayer(chart, {
    max:N, step:200, stride:1,
    onFrame:function(t){
      chart.setOption({
        xAxis:{data:CH.slice(0,t).map(function(c){return ('0'+c).slice(-2);})},
        series:[{data:S.slice(0,t)},{data:C.slice(0,t)}]
      });
      seekEl.value=t;
      frameEl.textContent='第 '+t+' / '+N+' 章';
      if(t>=N){ playBtn.classList.remove('active'); playBtn.textContent='▶ 重播时间轴'; }
    }
  });
  playBtn.addEventListener('click',function(){
    if(player.isPlaying()){ player.pause(); playBtn.classList.remove('active'); playBtn.textContent='▶ 播放时间轴'; }
    else { player.play(); playBtn.classList.add('active'); playBtn.textContent='⏸ 暂停'; }
  });
  seekEl.addEventListener('input',function(e){
    player.pause(); playBtn.classList.remove('active'); playBtn.textContent='▶ 播放时间轴';
    player.seek(parseInt(e.target.value,10));
  });

  // ---- 实时数据流模拟：外部事件触发平滑重绘 ----
  var liveBtn=document.getElementById('wz-live');
  var dot=document.getElementById('wz-live-dot');
  var live = WZ.liveStream({
    interval:1400,
    onState:function(on){ liveBtn.classList.toggle('active',on); liveBtn.classList.toggle('wz-live',on); dot.classList.toggle('live',on); liveBtn.textContent = on?'■ 停止实时流':'⦿ 模拟实时数据流'; },
    onTick:function(){
      var K=8;
      for(var i=N-K;i<N;i++){
        S[i]=Math.max(0.12,Math.min(0.92, S[i]+(Math.random()-0.5)*0.06));
        C[i]=Math.max(0,Math.min(3, Math.round(C[i]+(Math.random()-0.5)*1.2)));
      }
      chart.setOption({series:[{data:S},{data:C}]}, {lazyUpdate:true});
    }
  });
  liveBtn.addEventListener('click',function(){ live.toggle(); });
});
</script>
<!--WZ-SCRIPT-END-->
""" % (
    json.dumps(CH, ensure_ascii=False),
    json.dumps(S, ensure_ascii=False),
    json.dumps(C, ensure_ascii=False),
    repr(MEAN),
    repr(PEARSON),
)

with io.open(HTML, "r", encoding="utf-8") as f:
    html = f.read()

# 1) 移除旧注入脚本（无论是否带锚点），保证可重复升级
html = re.sub(r'<script src="echarts-kit\.js"></script>\s*<script>\s*WZ\.ready[\s\S]*?</script>\s*', "", html)

# 2) 替换图表卡片：优先匹配原 SVG；否则按 <h2> 标题块匹配（兼容首次/已升级）
svg_pat = re.compile(r'<div class="card">\s*<svg xmlns="http://www\.w3\.org/2000/svg" viewBox="0 0 1000 520".*?</svg>\s*</div>', re.DOTALL)
h2_pat = re.compile(r'<h2>情感时序 vs 战斗强度（交互式动态图表）</h2>[\s\S]*?(?=<h2>)')
if svg_pat.search(html):
    html = svg_pat.sub(NEW_CARD, html, count=1)
elif h2_pat.search(html):
    html = h2_pat.sub(NEW_CARD, html, count=1)
else:
    print("[错误] 未找到原 SVG 图表卡片，也未找到已升级标题块，请检查产物 HTML 结构。")
    raise SystemExit(1)

# 3) 在 </body> 前注入脚本（保留已存在的 dm-toggle 脚本）
html = html.replace("</body>", INIT + "\n</body>", 1)

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("[完成] 已就地升级《情感时序》为 ECharts 交互式动态图表（可重复运行）。")
print("  数据：%d 章 · 均值 %.4f · Pearson r %.4f" % (N, MEAN, PEARSON))
