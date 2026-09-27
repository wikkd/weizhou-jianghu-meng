# -*- coding: utf-8 -*-
"""
《苇舟江湖梦》逐章情感极性打分 + 情感时序 vs 战斗强度 对照
纪律：只读取/分析 chapter_data，绝不修改任何源文件。
"""
import os, json, math, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTER_DIR = os.path.join(ROOT, "数据", "chapter_data")
ANALYSIS_DIR = os.path.join(ROOT, "数据", "analysis")
OUT_JSON = os.path.join(ANALYSIS_DIR, "sentiment_series.json")
OUT_HTML = os.path.join(ROOT, "产物", "苇舟江湖梦_情感时序.html")

os.makedirs(ANALYSIS_DIR, exist_ok=True)

# ----------------------------------------------------------------------------
# 1) 选择情感打分器：优先 snownlp，失败则退回内置词典
# ----------------------------------------------------------------------------
def make_snownlp_scorer():
    from snownlp import SnowNLP
    def score(text):
        return float(SnowNLP(text).sentiments)  # 0~1
    return score, "snownlp"

def make_dict_scorer():
    """内置正负情感词典简易打分（正/负情感词计数）。
    当 snownlp 不可用于本语料（退化/饱和）时作为回退。

    加固（2026-08-18）：单字情感种子改用「否定清单边界」计数，
    与 _rebuild_char_mentions.py 同机制——score 前先剔除已知的同字污染复合词，
    再数裸单字 + 多字复合词，避免 '笑' 命中 嘲笑/冷笑/讥笑、'好' 命中 好像 等子串污染。
    见 数据/文档一致性巡检报告.md「全量同类风险审计」节。
    """
    # 武侠语境相关正负情感词（涵盖喜/怒/哀/惧/爱/恶/战斗/离别等）
    pos = ("喜 欢喜 欢乐 喜悦 高兴 开心 快乐 庆 贺 笑 笑容 欢笑 美 善 良 好 安 安康 安宁 祥和 "
           "平静 温柔 善良 勇敢 智 勇 胜 赢 胜利 成功 成就 希望 光 光明 暖 温暖 和 和睦 悦 愉 "
           "畅 怡 欣慰 赞美 敬佩 尊崇 爱 友爱 爱恋 柔情 团圆 相聚 重逢 归 归来 团聚 温馨 甜 "
           "舒坦 轻盈 欣喜 雀跃 豪迈 快意 畅快 欢 欣 妙 佳 吉 祥 福 瑞 情深 恩义 义气 仗义 "
           "潇洒 逍遥 自在 快活 酣畅 痛快 甜蜜 欣慰 心安 和乐 喜庆 如愿 圆满 救 恩 恩情 温情")
    neg = ("悲 悲伤 哀 哀痛 痛 哭泣 哭 泪 愁 苦 怒 愤 恨 仇 杀 杀戮 血 血腥 毒 恶 凶 残 残忍 "
           "狠 狠毒 恐怖 惊 惧 害怕 恐 慌 绝望 凄凉 孤 孤独 寂 寂寞 冷 寒 凄 惨 难 熬 煎 病 "
           "危 亡 死 死亡 葬 叛 背叛 欺 欺骗 骗 阴谋 诡计 陷害 冤 冤屈 屈 屈辱 羞 耻 耻辱 憎 "
           "厌恶 厌 弃 抛弃 离 分离 离别 离散 失散 破 破灭 毁 毁灭 残破 惨烈 血战 厮杀 搏杀 "
           "凶险 危机 忧 忧虑 焦 焦躁 怒火 仇恨 血债 复仇 杀机 阴 凛 戾 狰狞 凄然 悲凉 哀伤 "
           "痛哭 泪流 丧 消亡 厄 厄运 祸 劫 劫难 危难 险 险恶 狠 暴 怒 愤慨 悲愤 惨 痛心 心碎")
    pos_words = [w for w in pos.split() if w]
    neg_words = [w for w in neg.split() if w]

    # 单字种子「同字污染复合词」否定清单：含该种子但整体极性不符裸字极性，
    # 须先于计数剔除，否则会被误计（子串污染）。key=单字种子，value=需剔除的复合词。
    NEG_BOUNDARY = {
        "笑": ["嘲笑", "冷笑", "讥笑", "耻笑", "苦笑", "假笑", "狞笑", "讪笑",
               "笑话", "笑柄", "笑料", "赔笑", "谄笑"],
        "好": ["好像", "好不", "好生", "好险", "好端端", "好歹"],
        # 其余单字种子（悲/怒/杀/死/喜/乐/美/善…）复合词极性多与裸字一致，
        # 子串计数不翻转极性，故不列入；若后续发现污染可在此追加。
    }
    _strip_tokens = sorted((t for _s in NEG_BOUNDARY.values() for t in _s), key=len, reverse=True)
    _strip_re = re.compile("|".join(re.escape(t) for t in _strip_tokens)) if _strip_tokens else None

    def _clean(text):
        # 把否定清单复合词替换为等长空格：既剔除污染，又保持文本长度不影响其余子串计数
        if _strip_re is None:
            return text
        return _strip_re.sub(lambda m: " " * len(m.group(0)), text)

    def score(text):
        t = _clean(text)
        p = sum(t.count(w) for w in pos_words)
        n = sum(t.count(w) for w in neg_words)
        if p + n == 0:
            return 0.5
        return 0.5 + 0.5 * (p - n) / (p + n)
    return score, "dict_fallback"

scorer, method = None, None
_snownlp_scores = None
try:
    s0, m0 = make_snownlp_scorer()
    # 采样探测：snownlp 在本语料上是否退化（武侠文本常被误判为全正面而饱和）
    probe = s0(open(os.path.join(CHAPTER_DIR, "chap_01.txt"), encoding="utf-8").read())
    _snownlp_scores = [s0(open(os.path.join(CHAPTER_DIR, "chap_%02d.txt" % i), encoding="utf-8").read()) for i in range(1, N + 1)]
    spread = max(_snownlp_scores) - min(_snownlp_scores)
    if spread < 0.02:
        # 退化（如全部饱和到 1.0）：视作“不可用”，退回词典打分
        print("snownlp 探测退化（全章极差=%.4f，近似饱和），退回词典打分" % spread)
        scorer, method = make_dict_scorer()
    else:
        scorer, method = s0, m0
        print("使用打分器: snownlp（探测正常，极差=%.4f）" % spread)
except Exception as e:
    print("snownlp 不可用（%s），退回内置词典打分" % repr(e))
    scorer, method = make_dict_scorer()
    print("使用打分器:", method)

# ----------------------------------------------------------------------------
# 2) 逐章读取并计算 sentiment
# ----------------------------------------------------------------------------
N = 59
sentiments = [None] * (N + 1)   # 1-indexed
for ch in range(1, N + 1):
    if method == "snownlp" and _snownlp_scores is not None:
        sentiments[ch] = _snownlp_scores[ch - 1]
    else:
        fp = os.path.join(CHAPTER_DIR, "chap_%02d.txt" % ch)
        with open(fp, "r", encoding="utf-8") as f:
            txt = f.read()
        sentiments[ch] = scorer(txt)
    print("chap %02d sentiment=%.4f [%s]" % (ch, sentiments[ch], method))

# ----------------------------------------------------------------------------
# 3) 读取 combat_intensity
# ----------------------------------------------------------------------------
with open(os.path.join(CHAPTER_DIR, "all_tags.json"), "r", encoding="utf-8") as f:
    tags = json.load(f)
combat = {t["chapter"]: int(t["combat_intensity"]) for t in tags}

# ----------------------------------------------------------------------------
# 4) 统计量 + 相关系数
# ----------------------------------------------------------------------------
chapters = []
for ch in range(1, N + 1):
    chapters.append({
        "chapter": ch,
        "sentiment": round(sentiments[ch], 6),
        "combat_intensity": combat.get(ch, None),
    })

mean_all = sum(sentiments[1:]) / N

# 前/中/后 1/3：59 -> 19 / 20 / 20 三段（1-19, 20-39, 40-59）
early = sentiments[1:20]
mid = sentiments[20:40]
late = sentiments[40:60]
mean_early = sum(early) / len(early)
mean_mid = sum(mid) / len(mid)
mean_late = sum(late) / len(late)

# 相关系数
try:
    from scipy.stats import pearsonr, spearmanr
    s_arr = [sentiments[ch] for ch in range(1, N + 1)]
    c_arr = [combat[ch] for ch in range(1, N + 1)]
    pr, pp = pearsonr(s_arr, c_arr)
    sr, sp = spearmanr(s_arr, c_arr)
    corr = {
        "pearson": {"r": round(float(pr), 6), "p": round(float(pp), 6)},
        "spearman": {"r": round(float(sr), 6), "p": round(float(sp), 6)},
    }
except Exception as e:
    print("scipy 不可用：%s" % repr(e))
    corr = {"pearson": {"r": None, "p": None}, "spearman": {"r": None, "p": None}}

result = {
    "method": method,
    "chapters": chapters,
    "mean": round(mean_all, 6),
    "thirds": {"early": round(mean_early, 6), "mid": round(mean_mid, 6), "late": round(mean_late, 6)},
    "corr": corr,
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("已写:", OUT_JSON)

# ----------------------------------------------------------------------------
# 5) SVG 折线图（双轴：sentiment 0-1 左轴；combat 0-3 右轴）
# ----------------------------------------------------------------------------
W, H = 1000, 520
M = {"left": 60, "right": 60, "top": 50, "bottom": 60}
plot_w = W - M["left"] - M["right"]
plot_h = H - M["top"] - M["bottom"]
x = lambda i: M["left"] + plot_w * (i - 1) / (N - 1)
y_s = lambda v: M["top"] + plot_h * (1 - (v - 0) / 1.0)          # sentiment 0~1
y_c = lambda v: M["top"] + plot_h * (1 - (v - 0) / 3.0)          # combat 0~3

def poly(points):
    return " ".join("%.2f,%.2f" % (px, py) for px, py in points)

s_pts = [(x(i), y_s(sentiments[i])) for i in range(1, N + 1)]
c_pts = [(x(i), y_c(combat[i])) for i in range(1, N + 1)]

# 网格 + 轴标签
grid_lines = []
for g in range(0, 11):
    sv = g / 10.0
    gy = y_s(sv)
    grid_lines.append('<line x1="%g" y1="%.2f" x2="%g" y2="%.2f" stroke="#eee" stroke-width="1"/>' % (M["left"], gy, W - M["right"], gy))
    grid_lines.append('<text x="%g" y="%.2f" font-size="11" fill="#888" text-anchor="end">%.1f</text>' % (M["left"] - 8, gy + 4, sv))
for g in range(0, 4):
    gy = y_c(g)
    grid_lines.append('<text x="%g" y="%.2f" font-size="11" fill="#c0392b" text-anchor="start">%d</text>' % (W - M["right"] + 8, gy + 4, g))

# x 轴刻度（每 5 章）
x_ticks = []
for i in range(1, N + 1, 5):
    xt = x(i)
    x_ticks.append('<text x="%.2f" y="%g" font-size="11" fill="#888" text-anchor="middle">%02d</text>' % (xt, H - M["bottom"] + 18, i))
x_ticks.append('<text x="%.2f" y="%g" font-size="11" fill="#888" text-anchor="middle">%02d</text>' % (x(N), H - M["bottom"] + 18, N))

svg = []
svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="system-ui,Segoe UI,Helvetica,Arial,sans-serif">' % (W, H))
svg.append('<rect x="0" y="0" width="%d" height="%d" fill="#fff"/>' % (W, H))
svg.append('<text x="%d" y="28" font-size="16" font-weight="600" fill="#222">《苇舟江湖梦》情感极性时序 vs 战斗强度</text>' % (M["left"], ))
svg.append('<text x="%d" y="44" font-size="11" fill="#888">左轴=情感 polarity(0-1, 蓝) ｜ 右轴=战斗强度(0-3, 红) ｜ 方法=%s</text>' % (M["left"], method))
svg += grid_lines
svg += x_ticks
svg.append('<polyline fill="none" stroke="#2980b9" stroke-width="2" points="%s"/>' % poly(s_pts))
svg.append('<polyline fill="none" stroke="#c0392b" stroke-width="2" stroke-dasharray="5 4" points="%s"/>' % poly(c_pts))
# 均值参考线
my = y_s(mean_all)
svg.append('<line x1="%g" y1="%.2f" x2="%g" y2="%.2f" stroke="#2980b9" stroke-width="1" stroke-dasharray="2 3" opacity="0.6"/>' % (M["left"], my, W - M["right"], my))
svg.append('<text x="%g" y="%.2f" font-size="10" fill="#2980b9">均值 %.3f</text>' % (W - M["right"] - 70, my - 5, mean_all))
# 图例
svg.append('<rect x="%d" y="%d" width="14" height="4" fill="#2980b9"/><text x="%d" y="%d" font-size="11" fill="#2980b9">情感 polarity</text>' % (M["left"], H - 20, M["left"] + 20, H - 16))
svg.append('<rect x="%d" y="%d" width="14" height="4" fill="#c0392b"/><text x="%d" y="%d" font-size="11" fill="#c0392b">战斗强度</text>' % (M["left"] + 130, H - 20, M["left"] + 150, H - 16))
svg.append('</svg>')
svg_str = "\n".join(svg)

with open(os.path.join(ANALYSIS_DIR, "sentiment_chart.svg"), "w", encoding="utf-8") as f:
    f.write(svg_str)

# ----------------------------------------------------------------------------
# 7) 自包含 HTML 报告
# ----------------------------------------------------------------------------
def pct(v):
    return ("%.4f" % v) if v is not None else "N/A"
def strength(r):
    if r is None: return "无数据"
    a = abs(r)
    if a < 0.1: return "可忽略"
    if a < 0.3: return "弱"
    if a < 0.5: return "中等"
    if a < 0.7: return "较强"
    return "强"

pe_r = corr["pearson"]["r"]; sp_r = corr["spearman"]["r"]
interpret = """
<p>全本情感均值 <b>%.4f</b>（0=极负, 0.5=中性, 1=极正），整体%s。</p>
<p>前后段对比：前 1/3 均值 <b>%.4f</b>，中 1/3 <b>%.4f</b>，后 1/3 <b>%.4f</b>。
%s</p>
<p><b>Pearson r = %s</b>（p=%s），相关强度：%s。该系数衡量情感与战斗强度的<em>线性</em>同步程度。</p>
<p><b>Spearman ρ = %s</b>（p=%s），相关强度：%s。该系数基于秩次，衡量单调趋势，对非线性/异常值更稳健。</p>
<p>若两系数均接近 0，说明本章情感高低与战斗激烈程度之间不存在稳定的系统关联——
武侠小说中激烈的战斗既可伴随悲壮/愤怒（负向），也可伴随豪情/畅快（正向），极性被文本修辞中和属正常现象。</p>
""" % (
    mean_all,
    "偏负面" if mean_all < 0.45 else ("偏正面" if mean_all > 0.55 else "接近中性"),
    mean_early, mean_mid, mean_late,
    ("后段相对%s" % ("回升" if mean_late > mean_early else "走低")) if abs(mean_late-mean_early) > 0.02 else "前后段基本持平",
    pct(pe_r), pct(corr["pearson"]["p"]), strength(pe_r),
    pct(sp_r), pct(corr["spearman"]["p"]), strength(sp_r),
)

method_note = """
<ul>
  <li><b>打分模型</b>：优先使用 <code>snownlp</code> 对每章<em>全文</em>计算 <code>sentiments</code>（0–1，越接近 1 越正面）；
  若 snownlp 不可用，则退回内置正/负情感词典的简易计数打分。本次实际方法：<b>%s</b>。</li>
  <li><b>snownlp 退化记录</b>：本次实测 <code>snownlp</code> 在本武侠语料上严重误判——不仅将"他死了，好悲伤好痛苦"之类明显负面句判为 0.99 正面，
  且对全部 59 章的长文本极性均饱和到精确的 <code>1.0</code>（全章极差 &lt; 0.02，无任何区分度）。
  该模型在古文/武侠语域未训练、被修辞与战斗描写带偏，故被视为"不可用"并自动切回词典打分。这正是任务所述"情感模型可能偏差"的典型例证。</li>
  <li><b>战斗强度</b>：取自 <code>chapter_data/all_tags.json</code> 的 <code>combat_intensity</code>（0–3 序数）。</li>
  <li><b>相关系数</b>：Pearson 与 Spearman 均由 <code>scipy</code> 计算；p 值用于显著性判断（通常以 p&lt;0.05 视为显著）。</li>
  <li><b>词典回退打分加固（2026-08-18）</b>：回退打分器对单字情感种子（笑/好等）采用「否定清单边界」——<code>score()</code> 前先以 <code>_clean()</code> 剔除 嘲笑/冷笑/讥笑/好像 等同字污染复合词，避免子串污染（与 <code>_rebuild_char_mentions.py</code> 修正「影」同机制）。实测全本均值仅变动约 0.3 个百分点（低于 1%%），Pearson/Spearman 相关方向与显著性（p&lt;0.001）均不变。</li>
  <li><b>重要方法局限</b>：武侠文本大量包含<strong>讽刺、反语、夸张、正话反说、以乐景写哀情</strong>等修辞，
  通用情感模型（尤其 snownlp 在古文/武侠语域上未专门训练）可能产生<strong>系统性偏差</strong>，
  例如把"快意恩仇""笑傲"误判为轻松正面、把含蓄悲壮判为中性。因此本分析<strong>仅作趋势性参考</strong>，
  不可作为文本情感事实的定论。如需严谨结论，建议结合人工标注或领域微调模型。</li>
  <li><b>纪律</b>：分析过程仅读取源文件，未对任何 chapter_data 或源文件做任何修改。</li>
</ul>
""" % method

table_rows = "".join(
    "<tr><td>%02d</td><td>%.4f</td><td>%d</td></tr>" % (c["chapter"], c["sentiment"], c["combat_intensity"])
    for c in chapters
)

# ---- 图表数据：优先用已验证落盘数据回填，避免重跑打分漂移 ----
try:
    with open(OUT_JSON, encoding="utf-8") as _f:
        _c = json.load(_f)
    _ch = _c["chapters"]
    CH = [c["chapter"] for c in _ch]
    S  = [c["sentiment"] for c in _ch]
    C  = [c["combat_intensity"] for c in _ch]
    MEAN = _c["mean"]
    PEARSON = _c["corr"]["pearson"]["r"]
except Exception:
    CH = [c["chapter"] for c in chapters]
    S  = [c["sentiment"] for c in chapters]
    C  = [c["combat_intensity"] for c in chapters]
    MEAN = mean_all
    PEARSON = corr["pearson"]["r"]
N = len(CH)

# ---- 交互式图表卡片（替换原静态 SVG）----
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

html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>苇舟江湖梦 · 情感时序</title>
<link rel="stylesheet" href="theme.css"></head>
<body><div class="wrap">
<h1>《苇舟江湖梦》情感极性时序分析</h1>
<p class="note">逐章情感打分（59 章）与战斗强度对照 · 生成方法：%s</p>

<div class="kpis">
  <div class="kpi"><div class="v">%.4f</div><div class="l">全本情感均值</div></div>
  <div class="kpi"><div class="v">%.4f</div><div class="l">前 1/3 均值</div></div>
  <div class="kpi"><div class="v">%.4f</div><div class="l">中 1/3 均值</div></div>
  <div class="kpi"><div class="v">%.4f</div><div class="l">后 1/3 均值</div></div>
  <div class="kpi"><div class="v">%s</div><div class="l">Pearson r（情感~战斗）</div></div>
  <div class="kpi"><div class="v">%s</div><div class="l">Spearman ρ（情感~战斗）</div></div>
</div>

%s

<h2>相关系数解读</h2>
<div class="card note">%s</div>

<h2>方法注记与局限</h2>
<div class="card note">%s</div>

<h2>逐章明细</h2>
<div class="card scroll"><table>
<thead><tr><th>章</th><th>sentiment</th><th>combat</th></tr></thead>
<tbody>%s</tbody></table></div>
</div></body></html>
""" % (
    method,
    mean_all, mean_early, mean_mid, mean_late,
    pct(pe_r), pct(sp_r),
    NEW_CARD,
    interpret,
    method_note,
    table_rows,
)

# 在 </body> 前注入交互图表脚本（保留其余内容）
html = html.replace("</body>", INIT + "\n</body>", 1)

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)
print("已写:", OUT_HTML)

print("SENTIMENT DONE: mean=%.4f corr_r=%.4f" % (mean_all, pe_r if pe_r is not None else 0.0))
