#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《苇舟江湖梦》全量信息归档：构建 SQLite 数据库 + HTML 总览索引。
整合：源文件 / 分析报告 / 数据资产(JSON) / 处理脚本 / 62章结构化标签 / 人物 / 地点。
输出：
  产物/数据归档/苇舟江湖梦_数据归档.db   （可查询关系库）
  产物/数据归档/苇舟江湖梦_数据归档总览.html （浏览版索引）
"""
import json, os, sqlite3, html, datetime
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH = os.path.join(ROOT, "产物", "数据归档")
os.makedirs(ARCH, exist_ok=True)
DB = os.path.join(ARCH, "苇舟江湖梦_数据归档.db")
HTML = os.path.join(ARCH, "苇舟江湖梦_数据归档总览.html")
GEN_DATE = "2026-08-17"

def load(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)

# —— 载入基础数据 ——
tags = load("数据/chapter_data/all_tags.json")
cidx = {x["chapter"]: x for x in load("数据/chapter_data/chapters_index.json")}
char_stats = load("数据/char_stats.json")          # list[dict]
tc = load("数据/text_coords.json")
CANON_LOC = set(tc["nodes"])                   # 19 正文规范地名
spatial = load("数据/spatial_data.json")
SPATIAL_LOC = set(spatial["nodes"].keys())    # 33 示意图地名

# 规范人物（原49表）
canon_char = {x["name"]: x for x in char_stats}

# 人物×章节出场（来自标签）
char_chaps = defaultdict(list)
for o in tags:
    for c in o["characters_present"]:
        char_chaps[c].append(o["chapter"])
all_chars = sorted(set(canon_char) | set(char_chaps))

# 地点×章节（来自 main_locations）
loc_chaps = defaultdict(list)
for o in tags:
    for l in o["main_locations"]:
        loc_chaps[l].append(o["chapter"])
all_locs = sorted(loc_chaps)

# 人物备注（仅对确有依据者标注）
ROLE_NOTE = {
    "任琅": "男主角",
    "尚樱": "女主角",
    "陈奉天": "反派 / 川阴王（王爷、反王归一）",
    "李月婵": "扩展人物：海郡酒楼女子，许达线情感锚点，第43章留白式退场",
    "福": "扩展人物：灰袍道士，授咒解毒，关联仙境'空'",
    "皇帝": "扩展人物：被提及的压迫性皇权象征",
    "影": "铁面人，重要暗线角色",
    "夏叶": "重要女性角色，与刘笑岩感情线",
    "刘笑岩": "重要角色，与夏叶感情线",
    "许达": "海郡守将（许司马），李月婵关联人物",
}

# —— 资产清单（人工编目）——
ARTIFACTS = [
    # 类别, 名称, 相对路径, 格式, 描述, 生成日期, 关键指标
    ("分析报告", "全文本量化分析报告", "产物/苇舟江湖梦_分析报告.html", "HTML",
     "237,264字/62章自动抽取：人物识别与共现网络、时间轴、空间谱系、七幕故事线与感情线。", GEN_DATE, "7张图表"),
    ("分析报告", "空间地点分析报告（示意图标定）", "产物/苇舟江湖梦_空间地点分析报告.html", "HTML",
     "结合文档内嵌参考图坐标，叠加旅行时间/地形/战术，建立相对坐标系与距离矩阵。", GEN_DATE, "33节点"),
    ("分析报告", "地理位置关系图（纯文本派生）", "产物/苇舟江湖梦_地理位置关系图.html", "HTML",
     "仅依正文方位词/里程/地形，加权最小二乘求解相对坐标；不引用文档示意图。", GEN_DATE, "19节点"),
    ("分析报告", "官制考究", "产物/苇舟江湖梦_官制考究.html", "HTML",
     "职官术语与秦—清历代比对，判定两汉郡县—将相制为体、兼采唐以来科举县制的架空仿古官制。", GEN_DATE, "朝代判定"),
    ("分析报告", "川阴王建都推演", "产物/川阴王建都推演.html", "HTML",
     "大战后川阴王建都最佳地点推演：京城为都、北盾南陪都东财枢格局。", GEN_DATE, "地缘推演"),
    ("分析报告", "章节标签量化看板", "产物/苇舟江湖梦_章节标签量化看板.html", "HTML",
     "62章受控词表标注的可视化看板：类型/时间层/感情线分布、情节演进、地点与人物热度。", GEN_DATE, "6版块8图"),
    ("分析报告", "章节结构深度量化", "产物/苇舟江湖梦_章节结构量化.html", "HTML",
     "补完既往报告未消费的标注维度：故事线/视角分布、自由标签主题词频与前后段漂移、感情线×算法情感交叉验证。", GEN_DATE, "6版块"),
    ("分析报告", "时间节奏与空间地名量化", "产物/苇舟江湖梦_时间节奏量化.html", "HTML",
     "聚合 time_loc 既往未消费信号：季节/昼夜/相对时间密度分布，命名实体地名去噪清洗与热度。", GEN_DATE, "4版块"),
    ("分析报告", "派生维度量化", "产物/苇舟江湖梦_派生维度量化.html", "HTML",
     "出场vs提及背离（幕后/符号型角色识别）与人物-地点共现矩阵（角色空间足迹）。", GEN_DATE, "2版块"),
    ("分析报告", "人物关系网络", "产物/苇舟江湖梦_人物关系网络.html", "HTML",
     "62章人物共现网络：degree/PageRank/社区划分，spring_layout 可视化，103节点/1363边/5社区。", GEN_DATE, "网络图"),
    ("分析报告", "情感时序曲线", "产物/苇舟江湖梦_情感时序.html", "HTML",
     "62章逐章情感极性（词典法，snownlp退化回退）与战斗强度对照，含相关系数。", GEN_DATE, "时序图"),
    ("分析报告", "词汇计量", "产物/苇舟江湖梦_词汇计量.html", "HTML",
     "全本词频Top50、分章TTR、前后19章用语漂移（市井→庙堂）。", GEN_DATE, "词频/TTR"),
    ("分析报告", "统计推断", "产物/苇舟江湖梦_统计推断.html", "HTML",
     "5项叙事假设非参检验（任琅/战斗类型与战斗强度显著正相关）。", GEN_DATE, "检验结果"),
    ("分析报告", "风格计量", "产物/苇舟江湖梦_风格计量.html", "HTML",
     "62章文体指纹：平均句长、标点密度、对话占比，反映叙事节奏。", GEN_DATE, "风格曲线"),
    ("数据资产", "人物统计", "数据/char_stats.json", "JSON",
     "49个规范人物：提及次数、出场章节、首末章。", GEN_DATE, "49人"),
    ("数据资产", "章节统计", "数据/chap_stats.json", "JSON", "62章字数与段落数。", GEN_DATE, "62章"),
    ("数据资产", "时间-地点序列", "数据/time_loc.json", "JSON", "时间线与地点标注序列。", GEN_DATE, "—"),
    ("数据资产", "章节序列", "数据/series.json", "JSON", "按章时间序列数据。", GEN_DATE, "—"),
    ("数据资产", "空间数据(示意图标定)", "数据/spatial_data.json", "JSON",
     "来自文档内嵌示意图的33节点坐标与距离矩阵（含像素比例尺）。", GEN_DATE, "33节点"),
    ("数据资产", "纯文本坐标", "数据/text_coords.json", "JSON",
     "纯正文派生的19节点相对坐标（1单位≈200里）。", GEN_DATE, "19节点"),
    ("数据资产", "分章索引", "数据/chapter_data/chapters_index.json", "JSON",
     "62章：章节号/文件名/字数/场景提示。", GEN_DATE, "62章"),
    ("数据资产", "章节结构化标签(核心)", "数据/chapter_data/all_tags.json", "JSON",
     "62章受控词表标注聚合（时间层/地点/人物/类型/故事线/感情线/战斗强度/视角/关键事件）。", GEN_DATE, "62章"),
    ("数据资产", "批次标注1-6", "数据/chapter_data/tags_batch1.json … tags_batch6.json", "JSON",
     "6个subagent并行标注的原始批次输出。", GEN_DATE, "6批"),
    ("数据资产", "人物共现网络", "数据/analysis/character_network.json", "JSON",
     "节点(度/PageRank/社区/出场)与边(共现权重)。", GEN_DATE, "103节点/1363边"),
    ("数据资产", "情感时序", "数据/analysis/sentiment_series.json", "JSON",
     "逐章 sentiment、thirds 分段均值、与 combat_intensity 相关系数。", GEN_DATE, "62章"),
    ("数据资产", "词汇计量", "数据/analysis/lexical_stats.json", "JSON",
     "Top词、分章TTR、平均句长、前后期漂移。", GEN_DATE, "—"),
    ("数据资产", "统计推断", "数据/analysis/stats_inference.json", "JSON",
     "每项检验的方法/统计量/p值/效应量/显著性。", GEN_DATE, "5检验"),
    ("数据资产", "风格计量", "数据/analysis/stylometry.json", "JSON",
     "逐章句长/标点密度/对话占比/段数。", GEN_DATE, "62章"),
    ("数据资产", "标注规范", "数据/chapter_data/tag_schema.md", "Markdown",
     "受控词表与归一规则（人物49/地点19/枚举类型）。", GEN_DATE, "schema"),
    ("处理脚本", "全文本报告生成", "脚本/08_generate_report.py", "Python",
     "生成全文本量化分析报告。", GEN_DATE, "—"),
    ("处理脚本", "空间报告生成", "脚本/09_generate_spatial_report.py", "Python",
     "生成空间地点分析报告（示意图标定）。", GEN_DATE, "—"),
    ("处理脚本", "纯文本地图生成", "脚本/11_generate_text_map.py", "Python",
     "加权最小二乘求解纯文本地理坐标。", GEN_DATE, "—"),
    ("处理脚本", "官制考究生成", "脚本/10_generate_guanzhi.py", "Python",
     "生成官制考究报告。", GEN_DATE, "—"),
    ("处理脚本", "标签看板生成", "脚本/12_generate_tag_dashboard.py", "Python",
     "生成章节标签量化看板。", GEN_DATE, "—"),
    ("处理脚本", "章节结构量化", "脚本/14_chapter_structure.py", "Python",
     "补完故事线/视角/自由标签量化及感情线×算法情感交叉验证。", GEN_DATE, "—"),
    ("处理脚本", "时间节奏量化", "脚本/15_time_rhythm.py", "Python",
     "聚合 time_loc 的季节/昼夜/相对时间密度与 ner_loc 地名去噪。", GEN_DATE, "—"),
    ("处理脚本", "派生维度量化", "脚本/16_derived_dims.py", "Python",
     "出场vs提及背离散射与人物-地点共现热力图。", GEN_DATE, "—"),
    ("处理脚本", "分章切分", "脚本/01_split_chapters.py", "Python",
     "将全文按章节标记切分为59个独立文本。", GEN_DATE, "—"),
    ("处理脚本", "标签聚合校验", "脚本/02_aggregate_tags.py", "Python",
     "合并6批次标签为all_tags.json并做一致性校验。", GEN_DATE, "—"),
    ("处理脚本", "情感分析", "脚本/06_run_sentiment.py", "Python",
     "逐章情感打分（snownlp退化检测+词典回退），可复现留档。", GEN_DATE, "—"),
    ("源文件", "原始文档", "源文件/苇舟江湖梦.docx", "DOCX",
     "小说原稿（作者：霜月仲明）。", "原作", "约1.1MB"),
    ("源文件", "提取纯文本", "数据/full_text.txt", "TXT",
     "从docx提取的纯文本（含自序与简易参考图注）。", GEN_DATE, "654KB"),
]

# —— 建库 ——
if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
cur = con.cursor()
cur.executescript("""
CREATE TABLE artifacts(
  id INTEGER PRIMARY KEY, category TEXT, name TEXT, path TEXT, fmt TEXT,
  description TEXT, gen_date TEXT, metrics TEXT);
CREATE TABLE chapters(
  chapter INTEGER PRIMARY KEY, file TEXT, word_count INTEGER, time_layer TEXT,
  story_arc TEXT, emotion_line TEXT, combat_intensity INTEGER, narrative_pov TEXT,
  main_locations TEXT, chapter_type TEXT, characters_present TEXT, key_events TEXT);
CREATE TABLE characters(
  name TEXT PRIMARY KEY, in_canonical_table INTEGER, mentions_total INTEGER,
  chapter_appearances INTEGER, first_chapter INTEGER, last_chapter INTEGER, role_note TEXT);
CREATE TABLE locations(
  name TEXT PRIMARY KEY, is_canonical INTEGER, in_spatial_map INTEGER,
  chapter_freq INTEGER);
""")

# artifacts
cur.executemany("INSERT INTO artifacts(category,name,path,fmt,description,gen_date,metrics) VALUES(?,?,?,?,?,?,?)",
                [(a[0],a[1],a[2],a[3],a[4],a[5],a[6]) for a in ARTIFACTS])

# chapters
for o in sorted(tags, key=lambda x: x["chapter"]):
    ch = o["chapter"]
    cur.execute("""INSERT INTO chapters VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (
        ch, o["file"], cidx.get(ch, {}).get("word_count", o.get("word_count")),
        o["time_layer"], o["story_arc"], o["emotion_line"], o["combat_intensity"],
        o["narrative_pov"], json.dumps(o["main_locations"], ensure_ascii=False),
        json.dumps(o["chapter_type"], ensure_ascii=False),
        json.dumps(o["characters_present"], ensure_ascii=False), o["key_events"]))

# characters
for name in all_chars:
    in_tab = 1 if name in canon_char else 0
    cs = canon_char.get(name, {})
    mentions = cs.get("mentions")
    chs = char_chaps.get(name, [])
    ca = len(chs)
    first = min(chs) if chs else (cs.get("first") if cs.get("first", -1) >= 0 else None)
    last = max(chs) if chs else (cs.get("last") if cs.get("last", -1) >= 0 else None)
    note = ROLE_NOTE.get(name, "—")
    cur.execute("INSERT OR REPLACE INTO characters VALUES(?,?,?,?,?,?,?)",
                (name, in_tab, mentions, ca, first, last, note))

# locations
for name in all_locs:
    is_canon = 1 if name in CANON_LOC else 0
    in_sp = 1 if name in SPATIAL_LOC else 0
    cur.execute("INSERT OR REPLACE INTO locations VALUES(?,?,?,?)",
                (name, is_canon, in_sp, len(loc_chaps[name])))

con.commit()

# —— 量化分析模块（第二批 subagent 产出）——
def loadp(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)

cur.executescript("""
CREATE TABLE IF NOT EXISTS analyses(
  module TEXT PRIMARY KEY, title TEXT, html_path TEXT, data_json TEXT,
  key_metric TEXT, summary TEXT);
CREATE TABLE IF NOT EXISTS net_nodes(
  name TEXT PRIMARY KEY, degree REAL, pagerank REAL, community INTEGER, appearances INTEGER);
CREATE TABLE IF NOT EXISTS net_edges(
  source TEXT, target TEXT, weight INTEGER);
""")

# 人物共现网络
net = loadp("数据/analysis/character_network.json")
for n in net["nodes"]:
    cur.execute("INSERT OR REPLACE INTO net_nodes VALUES(?,?,?,?,?)",
                (n["name"], n.get("degree"), n.get("pagerank"), n.get("community"), n.get("appearances")))
for e in net["edges"]:
    cur.execute("INSERT INTO net_edges VALUES(?,?,?)", (e["source"], e["target"], e["weight"]))
n_comm = len(set(n.get("community") for n in net["nodes"]))
net_metric = f"{len(net['nodes'])}节点 / {len(net['edges'])}边 / {n_comm}社区"
net_sum = "共现=62章逐章两两去重；社区0陈奉天权力群/1任琅主线群/2许达-苏雨江湖群/3刘媛灵乡土小群/4陆氏小群。"

# 情感时序
sent = loadp("数据/analysis/sentiment_series.json")
sent_metric = f"均值{sent['mean']:.3f}，与战斗强度 r={sent['corr']['pearson']['r']:.3f}(p={sent['corr']['pearson']['p']:.4f})"
sent_sum = "snownlp武侠语料退化饱和，自动回退情感词典打分；战斗强度越高负向词占比越高，中等负相关且显著。"

# 词汇计量
lex = loadp("数据/analysis/lexical_stats.json")
ttr_vals = [t["ttr"] for t in lex.get("ttr", [])]
ttr_mean = sum(ttr_vals) / len(ttr_vals) if ttr_vals else 0
lex_metric = f"TTR均{ttr_mean:.3f}，前/后19章语义漂移显著"
lex_sum = "实词47035/类符11853；前19章江湖宗教意象，后19章朝堂军国意象，市井→庙堂迁移清晰。"

# 统计推断
stats = loadp("数据/analysis/stats_inference.json")
n_sig = sum(1 for s in stats if s.get("significant"))
stats_metric = f"{len(stats)}项检验中 {n_sig} 项原始显著"
stats_sum = "任琅出场、章节含'战斗'与战斗强度显著正相关；陈奉天出场/京城/情感线序数不显著（小样本）。"

# 风格计量
sty = loadp("数据/analysis/stylometry.json")
sm = sty.get("summary", {})
sty_metric = f"均句长{sm.get('mean_sent_len',0):.2f}字，对话占比{sm.get('mean_dialogue_ratio',0):.1%}"
sty_sum = "决战章对话占比骤降、叙述加快；日常章对话密集；全本平均对话占比约35.6%。"

ANALYSIS_ROWS = [
    ("人物共现网络", "人物关系网络", "产物/苇舟江湖梦_人物关系网络.html", "数据/analysis/character_network.json", net_metric, net_sum),
    ("情感时序", "情感时序曲线", "产物/苇舟江湖梦_情感时序.html", "数据/analysis/sentiment_series.json", sent_metric, sent_sum),
    ("词汇计量", "词汇与用词漂移", "产物/苇舟江湖梦_词汇计量.html", "数据/analysis/lexical_stats.json", lex_metric, lex_sum),
    ("统计推断", "叙事假设统计检验", "产物/苇舟江湖梦_统计推断.html", "数据/analysis/stats_inference.json", stats_metric, stats_sum),
    ("风格计量", "文体指纹与节奏", "产物/苇舟江湖梦_风格计量.html", "数据/analysis/stylometry.json", sty_metric, sty_sum),
]
for r in ANALYSIS_ROWS:
    cur.execute("INSERT OR REPLACE INTO analyses VALUES(?,?,?,?,?,?)", r)

con.commit()

# —— 统计用于总览 ——
def q(sql): return cur.execute(sql).fetchall()
n_art = q("SELECT COUNT(*) FROM artifacts")[0][0]
n_rep = q("SELECT COUNT(*) FROM artifacts WHERE category='分析报告'")[0][0]
n_ch = q("SELECT COUNT(*) FROM chapters")[0][0]
n_char = q("SELECT COUNT(*) FROM characters")[0][0]
n_char_ext = q("SELECT COUNT(*) FROM characters WHERE in_canonical_table=0")[0][0]
n_loc = q("SELECT COUNT(*) FROM locations")[0][0]
n_loc_ext = q("SELECT COUNT(*) FROM locations WHERE is_canonical=0")[0][0]
total_words = q("SELECT SUM(word_count) FROM chapters")[0][0] or 0

# —— 生成 HTML 总览 ——
def esc(s): return html.escape(str(s))

art_rows = ""
for a in ARTIFACTS:
    art_rows += f"<tr><td>{esc(a[0])}</td><td>{esc(a[1])}</td><td><code>{esc(a[2])}</code></td><td>{esc(a[3])}</td><td>{esc(a[4])}</td><td>{esc(a[5])}</td><td>{esc(a[6])}</td></tr>"

ch_rows = ""
for o in sorted(tags, key=lambda x: x["chapter"]):
    ch_rows += (f"<tr><td>{o['chapter']}</td><td>{esc(o['file'])}</td><td>{cidx.get(o['chapter'],{}).get('word_count','')}</td>"
                f"<td>{esc(o['time_layer'])}</td><td>{esc(o['story_arc'])}</td><td>{esc(o['emotion_line'])}</td>"
                f"<td>{o['combat_intensity']}</td><td>{esc('、'.join(o['main_locations']))}</td>"
                f"<td>{esc('、'.join(o['chapter_type']))}</td></tr>")

char_rows = ""
for r in q("SELECT name,in_canonical_table,mentions_total,chapter_appearances,first_chapter,last_chapter,role_note FROM characters ORDER BY chapter_appearances DESC, name"):
    tag = "规范" if r[1] else "<span class='ext'>扩展</span>"
    mt = r[2] if r[2] is not None else "—"
    char_rows += f"<tr><td>{esc(r[0])}</td><td>{tag}</td><td>{mt}</td><td>{r[3]}</td><td>{r[4] or '—'}</td><td>{r[5] or '—'}</td><td>{esc(r[6])}</td></tr>"

loc_rows = ""
for r in q("SELECT name,is_canonical,in_spatial_map,chapter_freq FROM locations ORDER BY chapter_freq DESC, name"):
    tag = "规范" if r[1] else "<span class='ext'>扩展</span>"
    sp = "✓" if r[2] else "—"
    loc_rows += f"<tr><td>{esc(r[0])}</td><td>{tag}</td><td>{sp}</td><td>{r[3]}</td></tr>"

an_rows = ""
for r in q("SELECT module,title,html_path,key_metric,summary FROM analyses ORDER BY module"):
    link = "../" + os.path.basename(r[2])
    an_rows += (f"<tr><td>{esc(r[0])}</td><td><a href='{esc(link)}'>{esc(r[1])}</a></td>"
                f"<td>{esc(r[3])}</td><td>{esc(r[4])}</td></tr>")

html_doc = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>《苇舟江湖梦》数据归档总览</title>
<link rel="stylesheet" href="../theme.css"></head><body>
<header><h1>《苇舟江湖梦》数据归档总览</h1>
<p>统一索引 · 源文件 / 分析报告 / 数据资产 / 处理脚本 / 62章标签 / 人物 / 地点 ｜ 生成日期 {GEN_DATE} ｜ 配套数据库：苇舟江湖梦_数据归档.db（SQLite，可SQL查询）</p></header>
<div class="wrap">
<div class="cards">
<div class="card"><div class="kv">{n_art}</div><div class="kl">归档资产</div></div>
<div class="card"><div class="kv">{n_rep}</div><div class="kl">分析报告</div></div>
<div class="card"><div class="kv">{n_ch}</div><div class="kl">标注章节</div></div>
<div class="card"><div class="kv">{total_words:,}</div><div class="kl">章节总字数</div></div>
<div class="card"><div class="kv">{n_char}</div><div class="kl">人物({n_char_ext}扩展)</div></div>
<div class="card"><div class="kv">{n_loc}</div><div class="kl">地点({n_loc_ext}扩展)</div></div>
<div class="card"><div class="kv">7</div><div class="kl">脚本</div></div>
</div>

<section><h2>一、资产清单（{n_art} 项）</h2>
<p class="note">类别：源文件 / 分析报告 / 数据资产 / 处理脚本。路径相对工作区根目录。</p>
<table><thead><tr><th>类别</th><th>名称</th><th>路径</th><th>格式</th><th>描述</th><th>生成</th><th>指标</th></tr></thead>
<tbody>{art_rows}</tbody></table></section>

<section><h2>二、章节标签索引（{n_ch} 章）</h2>
<p class="note">取自 chapter_data/all_tags.json；地点/类型经受控词表归一。</p>
<table><thead><tr><th>章</th><th>文件</th><th>字数</th><th>时间层</th><th>故事线</th><th>感情线</th><th>战斗</th><th>主地点</th><th>章节类型</th></tr></thead>
<tbody>{ch_rows}</tbody></table></section>

<section><h2>三、人物总览（{n_char} 人，含 {n_char_ext} 扩展）</h2>
<p class="note">规范=原49人表；扩展=subagent标注发现、未入规范表。mentions为全文提及数（仅规范人物有），chapter_appearances为被列为出场人物的章节数。</p>
<table><thead><tr><th>人物</th><th>类别</th><th>提及</th><th>出场章数</th><th>首章</th><th>末章</th><th>备注</th></tr></thead>
<tbody>{char_rows}</tbody></table></section>

<section><h2>四、地点总览（{n_loc} 处，含 {n_loc_ext} 扩展）</h2>
<p class="note">规范=纯文本19节点；扩展=确指且重要但未入规范表的真实地名。章节频次=作为主地点的章节数；示意图=是否见于文档内嵌示意图坐标。</p>
<table><thead><tr><th>地点</th><th>类别</th><th>示意图</th><th>章节频次</th></tr></thead>
<tbody>{loc_rows}</tbody></table></section>

<section><h2>五、量化分析模块（第二批 · 5 subagent 并行）</h2>
<p class="note">人物共现网络 / 情感时序 / 词汇计量 / 统计推断 / 风格计量。数据见各模块HTML与配套JSON，亦可在数据库中以 analyses / net_nodes / net_edges 表检索。</p>
<table><thead><tr><th>模块</th><th>报告</th><th>关键指标</th><th>摘要</th></tr></thead>
<tbody>{an_rows}</tbody></table></section>

<div class="foot">《苇舟江湖梦》文本量化分析 · 数据归档 · SQLite + HTML 双形态 · {GEN_DATE}</div>
</div></body></html>"""

with open(HTML, "w", encoding="utf-8") as f:
    f.write(html_doc)

con.close()
print(f"数据库: {DB}  ({os.path.getsize(DB):,} 字节)")
print(f"总览页: {HTML}  ({os.path.getsize(HTML):,} 字节)")
print(f"资产{n_art} 报告{n_rep} 章节{n_ch} 人物{n_char}(扩展{n_char_ext}) 地点{n_loc}(扩展{n_loc_ext})")
