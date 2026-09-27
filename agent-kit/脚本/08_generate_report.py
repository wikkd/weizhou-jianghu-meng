# -*- coding: utf-8 -*-
"""生成《苇舟江湖梦》量化分析报告（自包含 HTML，内联 SVG 图表）。"""
import json, math, random, os
random.seed(42)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- 载入数据 ----------
char_stats = json.load(open(os.path.join(ROOT, "数据", "char_stats.json"), encoding="utf-8"))
chap_stats = json.load(open(os.path.join(ROOT, "数据", "chap_stats.json"), encoding="utf-8"))
series = json.load(open(os.path.join(ROOT, "数据", "series.json"), encoding="utf-8"))
N = series["N"]

# 整理人物表
char_by_name = {c["name"]: c for c in char_stats}
top10 = series["top_chars"]

# 地理（精选，人工核对）
geo = [
    ("九州", 19, "天下/世界观"),
    ("京城", 55, "帝国都城"),
    ("川阴", 97, "川阴王封国(含王号)"),
    ("川阴城", 17, "川阴王都"),
    ("楚城", 30, "楚氏势力"),
    ("梨阳", 18, "梨阳王故地"),
    ("岱胜", 26, "城池"),
    ("望岳镇", 41, "故事起点小镇"),
    ("海郡", 44, "郡城"),
    ("镜湖", 6, "山水"),
    ("华山", 10, "名山"),
    ("千佛谷", 2, "山谷"),
    ("堕凤谷", 5, "山谷"),
    ("仙境", 9, "秘境/终局"),
    ("皇宫", 8, "宫阙"),
    ("王宫", 11, "宫阙"),
    ("寺院", 3, "庙宇"),
    ("吊桥", 12, "关隘桥梁"),
    ("廊桥", 8, "关隘桥梁"),
    ("板桥", 5, "关隘桥梁"),
    ("铁索桥", 3, "关隘桥梁"),
    ("渡江", 9, "渡口"),
    ("后山", 11, "山水"),
    ("山坡", 9, "山水"),
]

# 时间回溯深度（叙事时间层）
time_layers = [
    ("现在(主线)", "故事当下"),
    ("六年前", "金刚山仙峰寺·幼童(任琅身世伏笔)"),
    ("二十余年前", "仙峰寺·'非不死，乃行尸走肉'(不死之力本源)"),
    ("三十余年前", "白猿守护'仙门之物'"),
    ("两百年前", "划界术/开国渊源"),
    ("百余年前", "前史"),
    ("十余年前", "深宫·影奉命平'梨阳王'"),
    ("二十多年前", "债务灭门/身世另一线"),
    ("十年前", "前史"),
]

# 相对时间词分布
rel_dist = [("多时",30),("片刻",21),("一瞬间",18),("须臾",13),("一瞬",13),("不久",8),
            ("几日",7),("当日下午",4),("明日启程",4),("两日",4),("三日",3),("多年",3)]

# ---------- SVG 工具 ----------
def esc(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def hbar(data, w=640, rowh=26, maxv=None, color="#3b6ea5"):
    maxv = maxv or max(v for _,v in data)
    svg=[f'<svg viewBox="0 0 {w+150} {len(data)*rowh+10}" width="100%" style="font-size:13px">']
    for i,(name,v) in enumerate(data):
        y=i*rowh+4
        bw=max(2, v/maxv*(w-10))
        svg.append(f'<rect x="0" y="{y}" width="{bw}" height="{rowh-8}" rx="3" fill="{color}"/>')
        svg.append(f'<text x="{bw+6}" y="{y+rowh-11}" fill="#333">{v}</text>')
        svg.append(f'<text x="{-4}" y="{y+rowh-11}" text-anchor="end" fill="#222" transform="translate(0,0)"></text>')
        svg.append(f'<text x="0" y="{y+rowh-11}" fill="#111" style="font-weight:600"></text>')
    # labels on left need width; place name left of bar start -> use x=-? simpler: name above? Use separate text at x=0 with anchor end but need margin.
    svg.append('</svg>')
    return "".join(svg)

# Better horizontal bar with left labels
def hbar2(data, labelw=70, barmax=520, rowh=26, color="#3b6ea5"):
    maxv=max(v for _,v in data)
    W=labelw+barmax+50
    H=len(data)*rowh+10
    svg=[f'<svg viewBox="0 0 {W} {H}" width="100%" preserveAspectRatio="xMinYMin meet" style="font-size:13px">']
    for i,(name,v) in enumerate(data):
        y=i*rowh+4
        bw=max(2, v/maxv*barmax)
        svg.append(f'<text x="{labelw-6}" y="{y+rowh-10}" text-anchor="end" fill="#222" style="font-weight:600">{esc(name)}</text>')
        svg.append(f'<rect x="{labelw}" y="{y}" width="{bw}" height="{rowh-8}" rx="3" fill="{color}"/>')
        svg.append(f'<text x="{labelw+bw+6}" y="{y+rowh-10}" fill="#555">{v}</text>')
    svg.append('</svg>')
    return "".join(svg)

def vbar(data, color="#5a8f3c"):
    n=len(data); cw=12; gap=2; W=n*(cw+gap)+10; H=170
    maxv=max(data) or 1
    svg=[f'<svg viewBox="0 0 {W} {H}" width="100%" preserveAspectRatio="xMinYMin meet" style="font-size:10px">']
    for i,v in enumerate(data):
        bh=v/maxv*(H-30)
        x=5+i*(cw+gap); y=H-20-bh
        svg.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{bh}" fill="{color}" rx="1"/>')
        if i%5==0 or i==n-1:
            svg.append(f'<text x="{x+cw/2}" y="{H-6}" text-anchor="middle" fill="#777">{i+1}</text>')
    svg.append(f'<text x="2" y="12" fill="#555">字数</text>')
    svg.append('</svg>')
    return "".join(svg)

def linechart(data, color="#c0392b", h=160, fill=True):
    n=len(data); W=760; maxv=max(data) or 1
    pad=24
    svg=[f'<svg viewBox="0 0 {W} {h}" width="100%" preserveAspectRatio="xMinYMin meet" style="font-size:10px">']
    pts=[]
    for i,v in enumerate(data):
        x=pad+i/(max(1,n-1))*(W-2*pad)
        y=h-18-(v/maxv)*(h-40)
        pts.append((x,y))
    d="M"+(" L".join(f"{x:.1f},{y:.1f}" for x,y in pts))
    if fill:
        svg.append(f'<path d="{d} L{pts[-1][0]:.1f},{h-18} L{pts[0][0]:.1f},{h-18} Z" fill="{color}" opacity="0.12"/>')
    svg.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"/>')
    for i,(x,y) in enumerate(pts):
        if i%6==0 or i==n-1:
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{color}"/>')
            svg.append(f'<text x="{x:.1f}" y="{h-4}" text-anchor="middle" fill="#777">{i+1}</text>')
    svg.append('</svg>')
    return "".join(svg)

# 人物出场热力图（top10 × 59章）
def heatmap(names, perchap, N):
    cw=12; rh=18; labelw=56; W=labelw+N*cw+5; H=len(names)*rh+10
    svg=[f'<svg viewBox="0 0 {W} {H}" width="100%" preserveAspectRatio="xMinYMin meet" style="font-size:11px">']
    for i,nm in enumerate(names):
        y=i*rh+2
        svg.append(f'<text x="{labelw-5}" y="{y+rh-5}" text-anchor="end" fill="#222">{esc(nm)}</text>')
        for k in range(N):
            x=labelw+k*cw
            on = perchap[nm][k] if perchap[nm][k]>0 else 0
            col = "#2c5d8a" if on else "#eee"
            svg.append(f'<rect x="{x}" y="{y}" width="{cw-1}" height="{rh-2}" fill="{col}"/>')
    svg.append('</svg>')
    return "".join(svg)

# ---------- 力导向布局 ----------
nodes = [c["name"] for c in char_stats]
mentions = {c["name"]: c["mentions"] for c in char_stats}
# build adjacency from edges
adj={n:set() for n in nodes}
edge_w={}
for e in series["edges"]:
    a,b,w=e["a"],e["b"],e["w"]
    if a in adj and b in adj:
        adj[a].add(b); adj[b].add(a)
        edge_w[(a,b)]=w; edge_w[(b,a)]=w
# only keep nodes with degree>0 for layout; place isolated separately
active=[n for n in nodes if adj[n]]
pos={}
random.seed(7)
for n in active:
    pos[n]=(random.uniform(-200,200), random.uniform(-200,200))
# iterations
k=160.0
for it in range(300):
    disp={n:[0,0] for n in active}
    for i in range(len(active)):
        a=active[i]
        for j in range(i+1,len(active)):
            b=active[j]
            dx=pos[a][0]-pos[b][0]; dy=pos[a][1]-pos[b][1]
            d=math.hypot(dx,dy)+0.01
            f=k*k/d
            disp[a][0]+=dx/d*f; disp[a][1]+=dy/d*f
            disp[b][0]-=dx/d*f; disp[b][1]-=dy/d*f
    for a in active:
        for b in adj[a]:
            dx=pos[b][0]-pos[a][0]; dy=pos[b][1]-pos[a][1]
            d=math.hypot(dx,dy)+0.01
            f=d*d/k
            disp[a][0]+=dx/d*f; disp[a][1]+=dy/d*f
    for n in active:
        d=math.hypot(disp[n][0],disp[n][1])+0.01
        step=min(d, k*1.2)
        pos[n]=(pos[n][0]+disp[n][0]/d*step, pos[n][1]+disp[n][1]/d*step)
# scale to viewBox
xs=[p[0] for p in pos.values()]; ys=[p[1] for p in pos.values()]
minx,maxx=min(xs),max(xs); miny,maxy=min(ys),max(ys)
VW,VH=900,560
def sx(x): return 40+(x-minx)/(maxx-minx+1e-6)*(VW-80)
def sy(y): return 40+(y-miny)/(maxy-miny+1e-6)*(VH-80)
net_svg=[f'<svg viewBox="0 0 {VW} {VH}" width="100%" preserveAspectRatio="xMidYMid meet" style="font-size:12px">']
# edges
for e in series["edges"]:
    a,b=e["a"],e["b"]
    if a in pos and b in pos:
        w=min(6, 0.5+e["w"]/15)
        net_svg.append(f'<line x1="{sx(pos[a][0]):.1f}" y1="{sy(pos[a][1]):.1f}" x2="{sx(pos[b][0]):.1f}" y2="{sy(pos[b][1]):.1f}" stroke="#bbb" stroke-width="{w}" opacity="0.6"/>')
# nodes
for n in active:
    r=6+math.sqrt(mentions[n])*0.55
    cx,cy=sx(pos[n][0]),sy(pos[n][1])
    fill="#c0392b" if n in("任琅","尚樱") else ("#e08e0b" if n=="陈奉天" else "#3b6ea5")
    net_svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="#fff" stroke-width="1.5"/>')
    net_svg.append(f'<text x="{cx:.1f}" y="{cy-r-3:.1f}" text-anchor="middle" fill="#222" style="font-weight:600">{esc(n)}</text>')
net_svg.append('</svg>')
net_svg="".join(net_svg)

# 关系表（基于共现+叙事实证的研判）
relations = [
    ("任琅","尚樱","夫妻 / 挚爱（主线）","spar结缘→同游→成婚(婚服/中秋王室礼服)→育有一子→仙境相守"),
    ("任琅","影","神秘羁绊（赠器·不死同源）","影赠吹火筒/神之飞雪/月隐糖；尸体与影同貌；任琅持'不死斩'"),
    ("尚樱","虞环","姐妹 / 挚友","尚樱称'虞环姐姐'；虞环为川阴王妃，尚樱为长公主"),
    ("陈奉天","虞环","夫妻","川阴王与王妃，同坐王宫"),
    ("陈奉天","影","旧识 / 主从或对立","影曾奉命平'梨阳王'；后影似背离，火烧王府"),
    ("赵骁","赵翔","父子","独眼老将赵骁与子赵翔同帐"),
    ("刑布","刑泰","父子","大将军刑布战死，子刑泰继领"),
    ("苏雨","苏沐文","同族 / 疑似手足","同姓苏，政务/军务协作频繁"),
    ("叶云","夏叶/魏才思/范豪","师徒","叶云为门主，二弟子魏才思、弟子范豪、夏叶出其门下"),
    ("夏叶","刘笑岩","爱慕 / 搭档","同段107次居次；夏叶追问刘笑岩'之后想做什么'"),
    ("张潇璃","陆仲","爱慕","同段21次，爱慕关键词4次，情感线支线"),
    ("陈奉天","赵骁/王慕","君臣","川阴王与老将军、近臣"),
    ("许达","马远/黄亚钊","同袍 / 阵营","军事同僚，合力南渡、围城"),
    ("任琅","夏叶/刘笑岩","枢纽（三角/伙伴）","夏叶分别与任琅、尚樱、刘笑岩强共现，为核心连接点"),
]

# HTML —— 篇幅/章节指标动态取自切分结果，避免与正文版本脱节
_ch_idx = json.load(open(os.path.join(ROOT, "数据", "chapter_data", "chapters_index.json"), encoding="utf-8"))
total_chars = sum(c["chars"] for c in _ch_idx)
_ch_lens = {c["chapter"]: c["chars"] for c in _ch_idx}
_long = max(_ch_lens, key=_ch_lens.get)
_short = min(_ch_lens, key=_ch_lens.get)
total_cn = sum(1 for ch in open(os.path.join(ROOT, "数据", "full_text.txt"), encoding="utf-8").read() if '一' <= ch <= '鿿')

# 详见专业报告（导读降级：各节末尾追加跳转链接）
SEEALSO = {
    "一、文本概况与结构": ("苇舟江湖梦_章节结构量化.html", "章节结构量化"),
    "二、人物图谱（角色识别与关系网络）": ("苇舟江湖梦_人物关系网络.html", "人物关系网络"),
    "三、时间轴与叙事时序": ("苇舟江湖梦_时间节奏量化.html", "时间节奏量化"),
    "四、空间谱系（地理分布）": ("苇舟江湖梦_空间地点分析报告.html", "空间地点分析报告"),
    "五、任务线（目标与使命）": ("苇舟江湖梦_章节标签量化看板.html", "章节标签量化看板"),
    "六、故事线与重大事件（七幕结构）": ("苇舟江湖梦_章节标签量化看板.html", "章节标签量化看板"),
    "七、感情线（情感脉络）": ("苇舟江湖梦_情感时序.html", "情感时序"),
    "八、量化结论": ("苇舟江湖梦_统计推断.html", "统计推断"),
}

html=[]
html.append("""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>《苇舟江湖梦》量化分析报告</title>
<link rel="stylesheet" href="theme.css"></head><body><div class="wrap">""")

html.append("<h1>《苇舟江湖梦》文本量化分析报告</h1>")
html.append('<div class="sub">基于全文 {tc:,} 字（含标点）· {nc} 章 · 平均 {avg:,} 字/章 的自动抽取与结构研判</div>'.replace("{tc:,}", str(total_chars)).replace("{nc}", str(len(_ch_idx))).replace("{avg:,}", str(total_chars // len(_ch_idx))))
html.append('<div class="author">原著：霜月仲明 ｜ 分析：WorkBuddy 量化文本分析管道</div>')

# KPI
html.append('<div class="card"><div class="kpis">')
kpis=[("总字数", "{:,}".format(total_chars)),("章节数", str(len(_ch_idx))),("中文字符", "{:,}".format(total_cn)),
      ("识别人物","49"),("地理节点","24+"),("时间回溯层","9"),("共现关系对","296"),("核心枢纽","任琅·尚樱")]
for v,l in kpis:
    html.append(f'<div class="kpi"><div class="v">{v}</div><div class="l">{l}</div></div>')
html.append('</div></div>')

# 1 文本概况
html.append("<h2>一、文本概况与结构</h2>")
html.append('<div class="card"><ul class="tight">')
html.append("<li><b>体裁</b>：传统武侠 / 仙侠长篇（第一、三人称交替；含自序与'简易参考图'）。</li>")
html.append("<li><b>篇幅</b>：中文汉字 {cn:,} 字（含标点 {tc:,} 字符），共 {nc} 章，平均 {avg:,} 字/章。</li>".replace("{cn:,}", str(total_cn)).replace("{tc:,}",  str(total_chars)).replace("{nc}", str(len(_ch_idx))).replace("{avg:,}", str(total_chars // len(_ch_idx))))
html.append("<li><b>章节区间</b>：最长第 {lo} 章（{lo_n:,} 字）；最短第 {sh} 章（{sh_n:,} 字）。</li>".replace("{lo}", str(_long)).replace("{lo_n:,}", str(_ch_lens[_long])).replace("{sh}", str(_short)).replace("{sh_n:,}", str(_ch_lens[_short])))
html.append("<li><b>叙事结构</b>：以'现在'主线为轴，嵌入六层历史回溯（六年前→两百年前），构成'嵌套式时间'。</li>")
html.append("<li><b>视角</b>：任琅、尚樱双主角，辅以全知旁白与影/陈奉天等暗线。</li>")
html.append('</ul>')
html.append("<h3>各章字数分布</h3>"+vbar([c["chars"] for c in chap_stats]))
html.append('<div class="note">横轴为章序号（1–59），纵轴为章内中文字数。可见第 37 章为体量峰值。</div>')
html.append("</div>")

# 2 人物图谱
html.append("<h2>二、人物图谱（角色识别与关系网络）</h2>")
html.append('<div class="card"><h3>2.1 角色提及频次 TOP 15</h3>')
top15=[(c["name"],c["mentions"]) for c in char_stats[:15]]
html.append(hbar2(top15, color="#8a3324"))
html.append(f'<div class="note">任琅(1,438)、尚樱(1,177) 双主角断层领先；夏叶(328)、刘笑岩(288)、陈奉天(267)、影({mentions.get("影",0)}) 构成第二梯队。</div>')
html.append("</div>")

html.append('<div class="card"><h3>2.2 主要角色出场章节分布（热力图）</h3>')
html.append(heatmap(top10, series["per_chap_char"], N))
html.append('<div class="note">深蓝=该章出现。任琅(57/59章)、尚樱(53/59章)贯穿全书；影自第2章起持续渗透；陈奉天第17章登场后成为后半程核心。</div>')
html.append("</div>")

html.append('<div class="card"><h3>2.3 角色共现网络（交互强度）</h3>')
html.append(net_svg)
html.append('<div class="note">节点大小≈提及频次（红=双主角，金=陈奉天，蓝=其余）；连线粗细≈同段共现次数。任琅—尚樱(429段)为绝对核心边；夏叶为连接双主角与刘笑岩的关键枢纽。</div>')
html.append("</div>")

html.append('<div class="card"><h3>2.4 核心人物关系研判</h3>')
html.append("<table><tr><th>人物 A</th><th>人物 B</th><th>关系类型</th><th>文本证据</th></tr>")
for a,b,t,ev in relations:
    cls="r" if "夫妻" in t or "挚爱" in t else ("g" if "爱慕" in t else "")
    html.append(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td><span class='tag {cls}'>{esc(t)}</span></td><td>{esc(ev)}</td></tr>")
html.append("</table></div>")

# 3 时间轴
html.append("<h2>三、时间轴与叙事时序</h2>")
html.append('<div class="card"><h3>3.1 各章时间标记密度</h3>')
html.append(linechart(series["per_chap_time"]))
html.append('<div class="note">每章出现"相对时间词+时点/时辰词"的总数。第6章(11)为永夜城镇探索、第46章(岁末宴)等时段密集；总体时间推进模糊化（武侠常见），以事件序为主。</div>')
html.append("</div>")
html.append('<div class="card"><h3>3.2 叙事时间深度（回溯层）</h3>')
html.append("<table><tr><th>时间层</th><th>对应叙事 / 功能</th></tr>")
for t,d in time_layers:
    html.append(f"<tr><td><b>{esc(t)}</b></td><td>{esc(d)}</td></tr>")
html.append("</table>")
html.append('<div class="note">绝对纪年缺失（无具体年号/年份），时间以"几年前/季节/时辰"相对表达，并以多重回溯构建横跨数百年的"不死之力"神话谱系。</div>')
html.append("</div>")
html.append('<div class="card"><h3>3.3 高频相对时间词</h3>')
html.append(hbar2(rel_dist, color="#b8860b", labelw=70))
html.append("</div>")

# 4 地理
html.append("<h2>四、空间谱系（地理分布）</h2>")
html.append('<div class="card"><h3>4.1 主要地理节点词频</h3>')
geo_sorted=sorted(geo,key=lambda x:-x[1])
html.append(hbar2([(g[0],g[1]) for g in geo_sorted], color="#2c5d8a", labelw=70))
html.append('<div class="note">"川阴"含王号指代；京城(帝国都城)、望岳镇(起点)、海郡、楚城、梨阳为关键城池；仙境为终局秘境。</div>')
html.append("</div>")
html.append('<div class="card"><h3>4.2 地理层级</h3><ul class="tight">')
html.append("<li><b>天下/政权</b>：九州（世界观）｜川阴（川阴王封国）｜梨阳（梨阳王故地）｜楚氏（楚城）｜海郡｜岱胜｜京城（帝国都城）</li>")
html.append("<li><b>起点与城镇</b>：望岳镇（任琅出村首站）｜暮山城｜奉秋（张广义）｜梨阳城｜川陵｜邺口关｜方上城</li>")
html.append("<li><b>山水秘境</b>：华山｜镜湖｜千佛谷｜堕凤谷｜金刚山·仙峰寺｜弈剑峰｜幽山村｜后山｜仙境</li>")
html.append("<li><b>关隘桥梁</b>：廊桥｜板桥｜吊桥｜铁索桥｜梨阳大桥（南渡关键）</li>")
html.append("</ul><div class=\"note\">空间由'乡村→城镇→封国→京城→秘境'逐层升级，对应主角从江湖走向庙堂再入仙道的成长弧。</div></div>")

# 5 任务线
html.append("<h2>五、任务线（目标与使命）</h2>")
html.append('<div class="card"><ul class="tight">')
html.append("<li><b>任琅（主角）</b>：出村看世界 → 入镖局谋生 → 寻丹药(ch33) → 守护尚樱/成家 → 披甲参战(ch52) → 终局入仙境。核心道具：不死斩、吹火筒、神之飞雪、月隐糖（影所赠）。</li>")
html.append("<li><b>影（暗线）</b>：寻'年轻无畏之力'重入极死门(ch2/5)；贯穿全文的神秘执行者，亦正亦邪。</li>")
html.append("<li><b>陈奉天（ antagonist）</b>：追逐不死之力、扩张封国、最终兵临京城(ch57)夺权。</li>")
html.append("<li><b>苏雨 / 苏沐文</b>：政务文书与外交（奉川阴王命议长公主事，ch41）。</li>")
html.append("<li><b>许达 / 马远 / 黄亚钊 / 刑布</b>：军事征伐线（围奉秋、南渡、守城、粮道博弈）。</li>")
html.append("<li><b>夏叶 / 刘笑岩</b>：身份之谜与情感抉择（ch28 夏叶追问刘笑岩'之后想做什么'）。</li>")
html.append("</ul></div>")

# 6 故事线/重大事件
html.append("<h2>六、故事线与重大事件（七幕结构）</h2>")
arcs=[
 ("第一幕·启程","ch1–3","麦田比剑，任琅别尚樱出村；半年前偷鸡斗狼；入望岳镇，连环杀人案起，任琅决意当镖客。"),
 ("第二幕·初入江湖","ch4–13","影赠秘器、现'同貌尸'；永夜城镇探壁画；情花节；弈剑门六方剑(黄石)追杀；福登场。"),
 ("第三幕·身世揭秘","ch14–25,41,46","多层回溯：仙峰寺'非不死乃行尸走肉'、白猿守仙门、影平梨阳王；尚樱实为先王长公主(蓝眸)，虞环为王妃。"),
 ("第四幕·王室与羁绊","ch18–23,40–46","川阴王陈奉天下；尚樱 royal 身份坐实；婚服(ch20)、中秋王室礼服(ch42)、育子(ch43)；虞环谱曲。"),
 ("第五幕·群雄边境","ch26–39,44","叶云门下(夏叶/范豪/魏才思)；海郡黄氏商帮、许达守城；梨阳大桥南渡；任琅尚樱雾中路迷失。"),
 ("第六幕·战争","ch45–58","黄亚钊联合楚氏南渡；马远、许达、苏沐文、赵翔谋攻黄九州；刑布粮道被断、战死，刑泰继；陈奉天雪围京城。"),
 ("第七幕·终局·仙境","ch49–50,51–59","前史回溯(百余年前/十年前)；战后分配会议；皇帝问'计划需我做什么'；仙境中福以羽扇相托——开放式尾声。"),
]
html.append('<div class="arc">')
for t,ch,d in arcs:
    html.append(f'<div class="step"><b>{esc(t)}</b><br><span class="note">{esc(ch)}</span><br>{esc(d)}</div>')
html.append('</div>')
html.append('<div class="card"><h3>关键转折事件（量化锚点）</h3><ul class="tight">')
html.append("<li>ch2 望岳镇连环杀人 → 任琅卷入江湖（影首次现身，埋极死门伏笔）。</li>")
html.append("<li>ch5 与影同貌之尸 → 揭示'不死/灵体'设定，任琅身世疑云。</li>")
html.append("<li>ch17/41 尚樱=长公主 → 身份逆转，情感与政治双重升级。</li>")
html.append("<li>ch42–43 中秋成礼·育子 → 主线情感闭环。</li>")
html.append("<li>ch57 陈奉天雪围京城 → 战争顶点，旧朝倾覆。</li>")
html.append("<li>ch59 仙境托付 → 主题收束于'自由与初心'(呼应自序)。</li>")
html.append("</ul></div>")

# 7 感情线
html.append("<h2>七、感情线（情感脉络）</h2>")
html.append('<div class="card"><ul class="tight">')
html.append("<li><span class='tag r'>主线</span><b>任琅 × 尚樱</b>：麦田比剑的对手 → 同行挚友 → 婚服定情(ch20) → 中秋王室成礼(ch42) → 育有一子(ch43) → 仙境相守(ch59)。全书最强情感锚（同段429次）。</li>")
html.append("<li><span class='tag g'>支线</span><b>夏叶 × 刘笑岩</b>：第二强共现对(107段)，夏叶主动追问对方未来，疑似双向羁绊/爱慕。</li>")
html.append("<li><span class='tag g'>支线</span><b>张潇璃 × 陆仲</b>：爱慕关键词显著，独立情感副线。</li>")
html.append("<li><span class='tag'>亲情</span><b>赵骁—赵翔 / 刑布—刑泰</b>：两对父子，贯穿军事故事；陈奉天—虞环夫妻，尚樱称虞环'姐姐'。</li>")
html.append("<li><span class='tag'>命运共同体</span><b>任琅 × 影</b>：赠器、同貌、不死同源，超越普通情谊的神秘连结。</li>")
html.append("</ul><div class=\"note\">情感曲线与故事弧高度耦合：启程(懵懂)→同行(升温)→身份逆转(张力)→成婚育子(圆满)→战争离散(考验)→仙境(超越)。</div></div>")

# 8 结论
html.append("<h2>八、量化结论</h2>")
html.append('<div class="card"><ul class="tight">')
html.append("<li><b>双核驱动</b>：任琅、尚樱分别为全书提及第一、二人（1,438 / 1,177 次），断层领先其余角色；两人同段共现 429 次，为全部 296 对共现关系之首，印证'双主角'定位。</li>")
html.append("<li><b>枢纽人物</b>：夏叶（连接任琅、尚樱、刘笑岩）、影（连接任琅与极死门暗线）、陈奉天（连接王室与战争）是关键结构节点。</li>")
html.append("<li><b>时间模糊、空间升级</b>：无绝对纪年，依赖相对时间+九层回溯；空间由乡村→封国→京城→仙境逐级抬升，映射成长弧。</li>")
html.append("<li><b>战争占比高</b>：ch45–58 连续 14 章聚焦军事，是体量最重的中后段；情感闭环(ch42–43)恰置于战争前夕，形成'圆满—破碎'对照。</li>")
html.append("<li><b>主题</b>：以'自由之侠'与'初心'为核（自序明言），结局入仙境，完成由江湖到仙道的意境升华。</li>")
html.append("</ul></div>")

html.append('<div class="footer">本报告由 WorkBuddy 文本量化分析管道自动生成 · 数据基于原文全文抽取，关系研判结合共现统计与叙事实证 · 2026-08-17</div>')
html.append("</div></body></html>")

# 导读模式：在每节 h2 标题后追加「详见 XX 报告」链接 + 顶部公告
doc = "\n".join(html)
for h2_text, (href, label) in SEEALSO.items():
    needle = f"<h2>{h2_text}</h2>"
    repl = f'<h2>{h2_text}</h2>\n<div class="see-also">📖 <b>详见：</b><a href="{href}">{label} →</a></div>'
    if needle in doc:
        doc = doc.replace(needle, repl, 1)
banner = ('<div class="see-also" style="background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.4);'
          'border-radius:10px;padding:10px 14px;margin:8px 0 14px;color:#ffd9a0;font-size:13px">'
          '◆ <b>导读总览</b>：本页 8 节为快速通览，详细分析见各专业报告（每节末尾已加跳转）。</div>')
doc = doc.replace('<h1>《苇舟江湖梦》文本量化分析报告</h1>', banner + '<h1>《苇舟江湖梦》文本量化分析报告</h1>', 1)

open(os.path.join(ROOT, "产物", "苇舟江湖梦_分析报告.html"),"w",encoding="utf-8").write(doc)
print("报告已生成：苇舟江湖梦_分析报告.html ，大小", len(doc), "字符")
