# -*- coding: utf-8 -*-
"""Phase 2e：生成四份独立量化报告（玻璃风格 + echarts-kit 交互图）。
读取 数据/{char_traits,catchphrases,combat_actions,geo_profile}.json + text_coords.json，
产出 产物/苇舟江湖梦_{角色性格,口头禅,对打动作,地理描述}量化.html。内容为服务端烘焙（离线可读），
图表为 echarts-kit 增强；含深色切换。
"""
import os, json
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "数据")
OUT = os.path.join(ROOT, "产物")

ct = json.load(open(os.path.join(DATA, "char_traits.json"), encoding="utf-8"))
cp = json.load(open(os.path.join(DATA, "catchphrases.json"), encoding="utf-8"))
ca = json.load(open(os.path.join(DATA, "combat_actions.json"), encoding="utf-8"))
gp = json.load(open(os.path.join(DATA, "geo_profile.json"), encoding="utf-8"))
tc = json.load(open(os.path.join(DATA, "text_coords.json"), encoding="utf-8"))
pos = tc.get("pos", {})


def e(s):
    return escape(str(s))


DARK_TOGGLE = """<script>
(function(){var t=localStorage.getItem('wz-dark');if(t==='1')document.body.classList.add('dark');
var b=document.createElement('button');b.className='dm-toggle';b.textContent='🌓';
b.setAttribute('aria-label','切换深色');b.onclick=function(){var d=document.body.classList.toggle('dark');localStorage.setItem('wz-dark',d?'1':'0');};
document.body.appendChild(b);})();
</script>"""

EXTRA_CSS = """
.dm-toggle{position:fixed;right:18px;bottom:18px;z-index:50;width:42px;height:42px;border-radius:50%;
 border:1px solid var(--glass-border);background:var(--glass-bg-soft);color:var(--ink);font-size:18px;cursor:pointer;
 box-shadow:var(--shadow-card)}
.dash-block{margin-top:32px}
.dash-block h2{font-size:19px;font-weight:800;margin:0 0 6px;display:flex;align-items:center;gap:10px}
.dash-block h2::before{content:"";width:5px;height:20px;border-radius:20px;background:var(--band)}
.dash-intro{color:var(--muted);font-size:13.5px;line-height:1.72;margin:-4px 0 16px;max-width:90ch}
.q-table{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:8px}
.q-table th,.q-table td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
.q-table th{color:var(--muted);font-weight:600;position:sticky;top:0;background:var(--surface)}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:600;margin:2px 3px 2px 0;
 background:var(--primary);color:#fff}
.badge.mut{background:var(--glass-bg-soft);color:var(--ink);border:1px solid var(--glass-border)}
.q-card{background:var(--glass-bg-soft);border:1px solid var(--glass-border);border-radius:var(--radius,14px);
 padding:14px 16px;margin:10px 0;box-shadow:var(--shadow-card)}
.q-card h3{margin:0 0 6px;font-size:15px}
.q-card .meta{color:var(--muted);font-size:12px;margin-bottom:6px}
details{margin-top:6px}summary{cursor:pointer;color:var(--primary);font-size:12.5px}
.ev{padding:4px 0;font-size:12.5px;color:var(--muted);border-left:2px solid var(--line);padding-left:10px;margin:4px 0}
.wz-chart-card{background:var(--glass-bg-soft);border:1px solid var(--glass-border);border-radius:14px;padding:18px 20px;margin:10px 0}
.wz-hint{color:var(--muted);font-size:12px;margin-top:8px}
"""

PAGE_HEAD = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><link rel="stylesheet" href="glass.css">
<style>{extra_css}</style></head>
<body>
<script data-wz-embed>try{{if(location.search.indexOf("embed")>=0){{document.body.classList.add("embed");document.addEventListener("message",function(ev){{if(!ev.data)return;if(ev.data.wzTheme){{document.body.classList.toggle("dark",ev.data.wzTheme==="dark");}}if(ev.data.wzAccent){{document.documentElement.style.setProperty("--primary",ev.data.wzAccent);}}}});}}}}catch(e){{}}</script>
<header><h1>{title}</h1><p>{subtitle}</p></header>
<div class="wrap">
"""

PAGE_TAIL = """
</div>
{dark_toggle}
<script src="echarts-kit.js"></script>
<script>{chart_js}</script>
</body></html>"""


def kpi_cards(items):
    return '<div class="cards">' + "".join(
        '<div class="card"><div class="kpi-v">%s</div><div class="kpi-l">%s</div></div>' % (e(v), e(l))
        for v, l in items) + '</div>'


# ---------- 报告 1：角色性格 ----------
def rep_traits():
    axes_keys = ["性情", "品性", "心气", "情义", "智愚", "胆气"]
    # 每轴两极计数
    pole_counts = {ax: {} for ax in axes_keys}
    for v in ct.values():
        for ax in axes_keys:
            pol = v["trait_axes"].get(ax)
            if pol:
                pole_counts[ax][pol] = pole_counts[ax].get(pol, 0) + 1
    n_with = sum(1 for v in ct.values() if v["dominant_traits"])
    conf_avg = round(sum(v["confidence"] for v in ct.values()) / len(ct), 2)

    # 构造分组柱数据
    pole_a = []; pole_b = []
    for ax in axes_keys:
        keys = list(pole_counts[ax].keys())
        a = keys[0] if keys else "—"; b = keys[1] if len(keys) > 1 else "—"
        pole_a.append(pole_counts[ax].get(a, 0)); pole_b.append(pole_counts[ax].get(b, 0))
    chart_js = """
    var AX=%s, PA=%s, PB=%s;
    WZ.ready(function(){
      WZ.chart(document.getElementById('ch_axes'), function(vars){
        return {title:{text:'六性格轴 · 两极角色数分布',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},
          tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
          legend:{bottom:6,textStyle:{color:vars.muted}},
          grid:{left:54,right:24,top:48,bottom:64,containLabel:true},
          xAxis:{type:'category',data:AX,axisLabel:{color:vars.muted}},
          yAxis:{type:'value',name:'角色数',axisLabel:{color:vars.muted}},
          series:[
            {name:'极A',type:'bar',data:PA,itemStyle:{color:vars.palette[0],borderRadius:[4,4,0,0]},label:{show:true,position:'top',color:vars.muted}},
            {name:'极B',type:'bar',data:PB,itemStyle:{color:vars.palette[1],borderRadius:[4,4,0,0]},label:{show:true,position:'top',color:vars.muted}}
          ]};
      }, {});
    });
    """ % (json.dumps(axes_keys), json.dumps(pole_a), json.dumps(pole_b))

    # 表格
    rows = []
    for nm, v in sorted(ct.items(), key=lambda kv: -kv[1]["paragraphs"]):
        badges = "".join('<span class="badge">%s</span>' % e(t) for t in v["dominant_traits"])
        ax = " ".join("<span class='badge mut'>%s:%s</span>" % (e(a), e(p)) for a, p in v["trait_axes"].items() if p)
        ev = ""
        for sig in v["signals"]:
            for x in sig["evidence"][:1]:
                ev += "<div class='ev'>第%s章 · %s：「%s」</div>" % (e(x["chapter"]), e(sig["pole"]), e(x["snippet"]))
        rows.append("<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            e(nm), badges or "<span class='badge mut'>—</span>", ax, e(v["paragraphs"]), e(v["confidence"])))
    table = ("<table class='q-table'><thead><tr><th>角色</th><th>主导性格</th><th>各轴</th><th>语境段</th><th>置信度</th></tr></thead>"
             "<tbody>" + "".join(rows) + "</tbody></table>")

    body = kpi_cards([(49, "角色档案"), (n_with, "有主导性格"), (conf_avg, "平均置信度"),
                      (len(axes_keys), "性格维度轴")])
    body += "<section class='dash-block'><h2>一、六轴性格分布</h2><p class='dash-intro'>按 6 个性格维度轴统计被判定为各极的角色数量（自动词表抽取，证据见下表）。</p>"
    body += "<div class='wz-chart-card'><div id='ch_axes' data-wz-chart style='width:100%%;height:380px'></div><p class='wz-hint'>悬停查看角色数。</p></div></section>"
    body += "<section class='dash-block'><h2>二、角色性格档案（按语境段数排序）</h2><p class='dash-intro'>主导性格徽章 + 各轴判定 + 抽样证据（原文片段）。单字名角色（影/空/福）已启用否定清单防泛指污染。</p>" + table + "</section>"

    html = (PAGE_HEAD.format(title="《苇舟江湖梦》角色性格量化", subtitle="六轴受控词表自动抽取 · 49 角色性格档案与证据", extra_css=EXTRA_CSS)
            + body + PAGE_TAIL.format(dark_toggle=DARK_TOGGLE, chart_js=chart_js))
    return html


# ---------- 报告 2：口头禅 ----------
def rep_catch():
    rec = cp["recurring_utterances"]
    sig = cp["signature_ngrams"]
    n_char = cp["stats"]["characters_with_catchphrase"]
    top = sig[:15]
    chart_js = """
    var D=%s;
    WZ.ready(function(){
      WZ.chart(document.getElementById('ch_sig'), function(vars){
        var names=D.map(function(d){return d.phrase;}).reverse();
        var vals=D.map(function(d){return d.freq;}).reverse();
        var cols=D.map(function(d){return d.character;}).reverse();
        return {title:{text:'标志短语 Top15（按频次）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},
          tooltip:{trigger:'axis',axisPointer:{type:'shadow'},formatter:function(p){var i=p[0].dataIndex;return cols[i]+'：「'+names[i]+'」 '+vals[i]+'次';}},
          grid:{left:90,right:40,top:48,bottom:40,containLabel:true},
          xAxis:{type:'value',name:'频次'},
          yAxis:{type:'category',data:names,axisLabel:{color:vars.muted,fontSize:11}},
          series:[{type:'bar',data:vals,itemStyle:{color:vars.palette[0],borderRadius:[0,4,4,0]},label:{show:true,position:'right',color:vars.muted}}]};
      }, {});
    });
    """ % json.dumps([{"phrase": s["phrase"], "freq": s["freq"], "character": s["character"]} for s in top])

    # 按角色分组卡片
    byc = {}
    for s in sig:
        byc.setdefault(s["character"], []).append(s)
    for r in rec:
        byc.setdefault(r["character"], [])
    cards = []
    for nm in sorted(byc, key=lambda n: -len(byc[n])):
        items = byc[nm]
        lis = "".join("<div class='ev'>「%s」 ×%s（第%s章起，share %s）</div>" % (
            e(s["phrase"]), e(s["freq"]), e(s.get("first_chapter")), e(s.get("share", "-"))) for s in items[:8])
        cards.append("<div class='q-card'><h3>%s</h3><div class='meta'>标志语 %s 条</div>%s</div>" % (e(nm), e(len(items)), lis))

    body = kpi_cards([(n_char, "有口头禅角色"), (len(rec), "复现整句"), (len(sig), "标志短语"), (cp["stats"]["recurring_count"], "复现计数")])
    body += "<section class='dash-block'><h2>一、标志短语 Top15</h2><p class='dash-intro'>对话归属（最近前置角色名）后，按频次 ≥5 且 ≥70%% 归属于单一角色的 n-gram 筛选出的特征短语。</p>"
    body += "<div class='wz-chart-card'><div id='ch_sig' data-wz-chart style='width:100%%;height:420px'></div><p class='wz-hint'>悬停查看归属角色与频次。</p></div></section>"
    body += "<section class='dash-block'><h2>二、各角色标志语</h2><p class='dash-intro'>按角色归并的标志短语（含复现整句与特征 n-gram），可下钻至章节。</p>" + "".join(cards) + "</section>"

    html = (PAGE_HEAD.format(title="《苇舟江湖梦》口头禅量化", subtitle="对话归属 + 复现识别 · 角色标志语与特征短语", extra_css=EXTRA_CSS)
            + body + PAGE_TAIL.format(dark_toggle=DARK_TOGGLE, chart_js=chart_js))
    return html


# ---------- 报告 3：对打动作 ----------
def rep_combat():
    vocab = ca["vocab"]
    cats = ca["stats"]["categories"]
    top = vocab[:20]
    cat_items = [{"name": k, "value": v} for k, v in cats.items() if v]
    chart_js = """
    var TOP=%s, CAT=%s;
    WZ.ready(function(){
      WZ.chart(document.getElementById('ch_act'), function(vars){
        var names=TOP.map(function(d){return d.action;}).reverse();
        var vals=TOP.map(function(d){return d.freq;}).reverse();
        var cols=TOP.map(function(d){return d.category;}).reverse();
        var palette=vars.palette;
        var catColor={ '兵器':palette[0],'身法':palette[1],'内力':palette[2],'招式':palette[3],'防守':palette[4],'伤效':palette[5] };
        return {title:{text:'对打动作 Top20（按频次，按类着色）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},
          tooltip:{trigger:'axis',axisPointer:{type:'shadow'},formatter:function(p){var i=p[0].dataIndex;return cols[i]+' ·「'+names[i]+'」 '+vals[i]+'次';}},
          grid:{left:54,right:40,top:48,bottom:40,containLabel:true},
          xAxis:{type:'value',name:'频次'},
          yAxis:{type:'category',data:names,axisLabel:{color:vars.muted,fontSize:11}},
          series:[{type:'bar',data:vals.map(function(v,i){return {value:v,itemStyle:{color:catColor[cols[i]]||palette[0],borderRadius:[0,4,4,0]}};}),label:{show:true,position:'right',color:vars.muted}}]};
      }, {});
      WZ.chart(document.getElementById('ch_cat'), function(vars){
        return {title:{text:'动作类别分布',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},
          tooltip:{trigger:'item'},legend:{bottom:4,textStyle:{color:vars.muted}},
          series:[{type:'pie',radius:['38%%','66%%'],data:CAT,label:{color:vars.ink}}]};
      }, {});
    });
    """ % (json.dumps([{"action": v["action"], "freq": v["freq"], "category": v["category"]} for v in top]),
           json.dumps(cat_items))

    rows = []
    for v in vocab[:40]:
        ctx = e(v["sample_context"][:60]) if v["sample_context"] else "—"
        rows.append("<tr><td><b>%s</b></td><td><span class='badge mut'>%s</span></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            e(v["action"]), e(v["category"]), e(v["freq"]), e(len(v["characters"])), e(len(v["chapters"])), ctx))
    table = ("<table class='q-table'><thead><tr><th>动作</th><th>类</th><th>频次</th><th>涉及角色</th><th>涉及章</th><th>证据片段</th></tr></thead><tbody>"
             + "".join(rows) + "</tbody></table>")
    seq = "".join("<div class='ev'>%s ×%s</div>" % (e(s["bigram"]), e(s["freq"])) for s in ca["sequences"][:20])

    body = kpi_cards([(ca["stats"]["combat_chapters"], "战斗章"), (ca["stats"]["distinct_actions"], "动作种类"),
                      (ca["stats"]["total_action_hits"], "动作命中"), (len(ca["sequences"]), "招式序列")])
    body += "<section class='dash-block'><h2>一、动作频次与类别</h2><p class='dash-intro'>在 combat_intensity≥2 的 %s 个战斗章中，按 6 类动作词表抽取（兵器/身法涵盖 D5 兵器功法）。</p>" % ca["stats"]["combat_chapters"]
    body += "<div class='wz-chart-card'><div id='ch_act' data-wz-chart style='width:100%%;height:440px'></div><p class='wz-hint'>悬停查看类别与频次。</p></div>"
    body += "<div class='wz-chart-card'><div id='ch_cat' data-wz-chart style='width:100%%;height:340px'></div></div></section>"
    body += "<section class='dash-block'><h2>二、动作词表（Top40）</h2><p class='dash-intro'>动作词、类别、频次、涉及角色/章节数与证据片段。归属为同段出场角色共现，作参考。</p>" + table + "</section>"
    body += "<section class='dash-block'><h2>三、招式组合序列 Top20</h2><p class='dash-intro'>段落内相邻动作 bigram（频次≥2），反映攻防连贯节奏。</p>" + seq + "</section>"

    html = (PAGE_HEAD.format(title="《苇舟江湖梦》对打动作量化", subtitle="六类动作词表抽取 · 战斗章动作分布与招式序列（含兵器功法）", extra_css=EXTRA_CSS)
            + body + PAGE_TAIL.format(dark_toggle=DARK_TOGGLE, chart_js=chart_js))
    return html


# ---------- 报告 4：地理描述 ----------
def rep_geo():
    terr = {}
    for v in gp.values():
        terr[v["terrain_type"]] = terr.get(v["terrain_type"], 0) + 1
    feat_types = {}
    for v in gp.values():
        for f in v["features"]:
            feat_types[f["type"]] = feat_types.get(f["type"], 0) + 1
    terr_items = [{"name": k, "value": v} for k, v in terr.items()]
    feat_items = [{"name": k, "value": v} for k, v in feat_types.items()]
    # 地图点：pos + terrain 颜色
    pts = []
    terr_color = {"山岳型": "#7a8c5a", "水滨型": "#3a7ca5", "城郭型": "#b07a3a", "关隘型": "#9a5a5a", "平原型": "#9a9a5a", "未明": "#888"}
    for loc, xy in pos.items():
        t = gp.get(loc, {}).get("terrain_type", "未明")
        pts.append({"name": loc, "value": [xy[0], xy[1]], "terrain": t, "color": terr_color.get(t, "#888")})
    n_feat = sum(1 for v in gp.values() if v["features"])
    n_exc = sum(1 for v in gp.values() if v["excerpts"])

    chart_js = """
    var TERR=%s, FEAT=%s, PTS=%s;
    WZ.ready(function(){
      WZ.chart(document.getElementById('ch_terr'), function(vars){
        return {title:{text:'地形类型分布',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},
          tooltip:{trigger:'item'},legend:{bottom:4,textStyle:{color:vars.muted}},
          series:[{type:'pie',radius:['38%%','66%%'],data:TERR,label:{color:vars.ink}}]};
      }, {});
      WZ.chart(document.getElementById('ch_feat'), function(vars){
        return {title:{text:'地理要素类型',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},
          tooltip:{trigger:'item'},legend:{bottom:4,textStyle:{color:vars.muted}},
          series:[{type:'pie',radius:['38%%','66%%'],data:FEAT,label:{color:vars.ink}}]};
      }, {});
      WZ.chart(document.getElementById('ch_map'), function(vars){
        return {title:{text:'地点分布图（按地形着色，点击查看档案）',left:'center',top:6,textStyle:{color:vars.ink,fontSize:15}},
          tooltip:{trigger:'item',formatter:function(p){return p.data.name+' · '+p.data.terrain;}},
          grid:{left:40,right:20,top:48,bottom:30,containLabel:true},
          xAxis:{type:'value',min:-1,max:1,name:'相对经度',axisLabel:{color:vars.muted},splitLine:{lineStyle:{color:vars.line}}},
          yAxis:{type:'value',min:-1,max:1,name:'相对纬度',axisLabel:{color:vars.muted},splitLine:{lineStyle:{color:vars.line}}},
          series:[{type:'scatter',symbolSize:14,data:PTS,itemStyle:{color:function(p){return p.data.color;},borderColor:'#fff',borderWidth:1},
            label:{show:true,formatter:function(p){return p.data.name;},color:vars.ink,fontSize:10,position:'right'}}]};
      }, {onClick:function(p){ if(p&&p.data&&p.data.name){ window.open('苇舟江湖梦_原文阅读.html?kw='+encodeURIComponent(p.data.name),'_blank','noopener'); } }});
    });
    """ % (json.dumps(terr_items), json.dumps(feat_items), json.dumps(pts))

    # 地点档案卡片（按段落数排序）
    cards = []
    for loc, v in sorted(gp.items(), key=lambda kv: -kv[1]["paragraphs"])[:40]:
        feats = "".join("<span class='badge mut'>%s·%s</span>" % (e(f["type"]), e(f["name"])) for f in v["features"])
        exc = "".join("<div class='ev'>第%s章：%s</div>" % (e(x["chapter"]), e(x["text"][:50])) for x in v["excerpts"][:3])
        cards.append("<div class='q-card'><h3>%s</h3><div class='meta'>地形：%s ｜ 段落 %s ｜ 气候 %s</div>%s%s</div>" % (
            e(loc), e(v["terrain_type"]), e(v["paragraphs"]), e("、".join(v["climate_hints"]) or "—"),
            feats or "", exc))

    body = kpi_cards([(len(gp), "地点档案"), (n_feat, "含要素"), (n_exc, "含描述"), (len(terr), "地形类型")])
    body += "<section class='dash-block'><h2>一、地形与要素分布</h2><p class='dash-intro'>对 %s 个地点（spatial 节点 ∪ 叙事 main_locations）归类地形并聚合 geo_features 的 17 项要素。</p>" % len(gp)
    body += "<div class='wz-chart-card'><div id='ch_terr' data-wz-chart style='width:100%%;height:320px'></div></div>"
    body += "<div class='wz-chart-card'><div id='ch_feat' data-wz-chart style='width:100%%;height:320px'></div></div></section>"
    body += "<section class='dash-block'><h2>二、地点分布图</h2><p class='dash-intro'>叙事相对坐标系；按地形着色，点击地点跳原文高亮。</p>"
    body += "<div class='wz-chart-card'><div id='ch_map' data-wz-chart style='width:100%%;height:460px'></div><p class='wz-hint'>点击散点跳转原文。</p></div></section>"
    body += "<section class='dash-block'><h2>三、地点地理档案（按语境段数排序）</h2><p class='dash-intro'>地形类型、气候提示、地理要素与描述句抽样。</p>" + "".join(cards) + "</section>"

    html = (PAGE_HEAD.format(title="《苇舟江湖梦》地理描述量化", subtitle="地点地形归类 + 地理要素聚合 + 描述句抽样（覆盖全文地点）", extra_css=EXTRA_CSS)
            + body + PAGE_TAIL.format(dark_toggle=DARK_TOGGLE, chart_js=chart_js))
    return html


if __name__ == "__main__":
    files = {
        "苇舟江湖梦_角色性格量化.html": rep_traits(),
        "苇舟江湖梦_口头禅量化.html": rep_catch(),
        "苇舟江湖梦_对打动作量化.html": rep_combat(),
        "苇舟江湖梦_地理描述量化.html": rep_geo(),
    }
    for fn, html in files.items():
        open(os.path.join(OUT, fn), "w", encoding="utf-8").write(html)
        print("written", fn, len(html), "bytes")
