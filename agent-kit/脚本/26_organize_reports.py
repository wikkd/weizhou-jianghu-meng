# -*- coding: utf-8 -*-
"""
26_organize_reports.py
======================
报告归纳整理（只读盘点 → 方案页面）：
扫描产物目录，将全部报告按主题分组，识别重复/重叠组，输出分安全等级的动作清单。
本脚本【不删除/不移动任何文件】——产出整理方案页，执行需用户确认。

产物：产物/苇舟江湖梦_报告归纳整理.html
"""
import os, re, glob, json
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "产物")

# ---------------------------------------------------------------- 报告注册表（扫描得出）
# (文件名, 短标题, 主题组, 报告中心✓, 图书馆✓, 顶层index✓, 一句话定位)
REPORTS = [
    # —— 总览/入口 ——
    ("苇舟江湖梦_分析报告.html",        "全文本量化分析报告", "总览", True, True, True,
     "早期一体化总览：概况/人物/时间轴/空间/故事线/感情线/结论，八节被后分化专业报告超越"),
    ("数据归档/苇舟江湖梦_数据归档总览.html", "数据归档总览", "总览", True, False, True,
     "归档目录 + 索引数据库入口（数据归档/）"),
    ("苇舟江湖梦_报告归纳整理.html",    "报告归纳整理（治理页）", "总览", True, True, True,
     "只读盘点：9 主题分组 / 6 重复组 / L1–L4 动作清单（本页即产出）"),
    # —— 人物 ——
    ("苇舟江湖梦_人物关系网络.html",    "人物关系网络",      "人物", True, True, True,
     "共现网络 / PageRank 中心性 / 社区划分"),
    ("苇舟江湖梦_派生维度量化.html",    "派生维度量化",      "人物", True, True, False,
     "出场vs提及背离 + 人物-地点共现矩阵（与人物网络、空间报告部分重叠）"),
    ("苇舟江湖梦_角色性格量化.html",    "角色性格量化",      "人物", True, False, False,
     "六轴性格分布 + 角色档案（Phase2 新增）"),
    # —— 章节 ——
    ("苇舟江湖梦_章节结构量化.html",    "章节结构量化",      "章节", True, True, False,
     "标注治理基线 / 故事线 / 视角 / 主题词频与漂移 / 感情线×故事线"),
    ("苇舟江湖梦_章节标签量化看板.html", "章节标签量化看板", "章节", True, True, True,
     "情节演进（时间层色带+战斗强度）+ 分布速览（类型/感情线/战斗/地点/人物）"),
    ("苇舟江湖梦_统计推断.html",        "统计推断",          "章节", True, True, True,
     "非参数检验：叙事假设的统计验证（Mann-Whitney U / Spearman）"),
    # —— 时空地理 ——
    ("苇舟江湖梦_空间地点分析报告.html", "空间地点分析报告", "时空地理", True, True, True,
     "内嵌参考图坐标版：距离矩阵 / 地形分类 / 战术地理 / 旅行时间（最权威）"),
    ("苇舟江湖梦_地理位置关系图.html",  "地理位置关系图",    "时空地理", True, True, True,
     "纯文本派生版：方位约束 / 相对坐标系 / 战术地理（不引用内嵌图）"),
    ("苇舟江湖梦_地理描述量化.html",    "地理描述量化",      "时空地理", True, False, False,
     "地形要素分布 + 地点地理档案（Phase2，语境段数排序）"),
    ("苇舟江湖梦_时间节奏量化.html",    "时间节奏量化",      "时空地理", True, True, False,
     "季节/昼夜/相对时间密度 + 第4节 ner_loc 地名热度（空间部分重复）"),
    # —— 语言计量 ——
    ("苇舟江湖梦_风格计量.html",        "风格计量",          "语言计量", True, True, True,
     "文体指纹与节奏（句长/标点/对话占比等）"),
    ("苇舟江湖梦_词汇计量.html",        "词汇计量",          "语言计量", True, True, True,
     "词频 / TTR / 前后期用词漂移"),
    ("苇舟江湖梦_口头禅量化.html",      "口头禅量化",        "语言计量", True, False, False,
     "标志短语 Top15 + 各角色标志语（词汇计量的角色侧深化）"),
    ("苇舟江湖梦_对打动作量化.html",    "对打动作量化",      "语言计量", True, False, False,
     "动作频次 / 词表 Top40 / 招式组合序列（动作词汇库）"),
    # —— 情感节奏 ——
    ("苇舟江湖梦_情感时序.html",        "情感时序",          "情感节奏", True, True, True,
     "情感极性时序 vs 战斗强度 + 相关系数"),
    # —— 研究考据 ——
    ("苇舟江湖梦_官制考究.html",        "官制考究",          "研究考据", True, True, True,
     "职官术语抽取 + 历代官制比对"),
    ("川阴王建都推演.html",             "川阴王建都推演",    "研究考据", True, True, True,
     "基于空间报告结论的战略推演（独立，不重复）"),
    ("黄家概况.html",                   "黄家概况",          "研究考据", True, True, True,
     "家族谱系分析（独立，已补注册）"),
    # —— 叙事可视化（已注册全部入口）——
    ("苇舟江湖梦_可视化叙事系统.html",  "可视化叙事系统",    "叙事可视化", True, True, True,
     "四维状态转移流程图（剧情/情感/空间/时间）+ Nexus 立体交叉引用"),
    ("苇舟江湖梦_扩展叙事可视化.html",  "扩展叙事可视化",    "叙事可视化", True, True, True,
     "因果事件链 / 叙事节奏谱 / 角色六维雷达 / 登场矩阵热力图"),
    ("苇舟江湖梦_深度叙事可视化.html",  "深度叙事可视化",    "叙事可视化", True, True, True,
     "伏笔回收网络 / 时空动画地图 / 文风漂移流图 / 知识图谱+MOC"),
    # —— 工具/阅读 ——
    ("苇舟江湖梦_关键词索引.html",      "关键词索引",        "工具阅读", False, True, False,
     "关键词→原文跨索引页（配套 keyword-index-widget.js）"),
    ("苇舟江湖梦_原文阅读.html",        "原文阅读",          "工具阅读", False, True, False,
     "59 章全文阅读器，支持 ?loc / ?kw 深链"),
]

# 重复组定义：(组名, 重叠点描述, 涉及文件, 建议动作, 建议说明)
GROUPS = [
    ("G1 空间/地理 ×4", "高度重叠", [
        "空间地点分析报告（内嵌参考图坐标：距离矩阵/地形/战术地理）",
        "地理位置关系图（纯文本派生：方位约束/相对坐标/战术地理）",
        "地理描述量化（地形要素分布 + 地点语境档案）",
        "时间节奏量化·第4节 ner_loc 地名热度（空间子集）",
    ], "保留 1 权威 + 1 量化，其余并入",
     "前两份同为「空间格局+地形+战术地理」，仅数据源不同（内嵌参考图 vs 纯文本），建议以「空间地点分析报告」为主报告，把「地理位置关系图」的方位约束并入其附录；「地理描述量化」保留（语境档案是独有产出）；ner_loc 地名热度并入主报告。「时间节奏量化」去掉第4节只留时间维度。"),

    ("G2 情感/时间/节奏 ×3", "中度重叠", [
        "情感时序（情感极性 vs 战斗强度）",
        "章节标签量化看板（情节演进：时间层色带 + 战斗强度）",
        "时间节奏量化（季节/昼夜/相对时间）",
    ], "保留 3 份但各自聚焦，标注交叉引用",
     "战斗强度时间序列同时出现在「情感时序」与「看板」，建议看板保留战斗强度、情感时序专注情感极性，两页顶部互链；时间节奏专注季节/昼夜，移除 ner_loc 后与其余两页不再重叠。"),

    ("G3 章节 ×2", "中度重叠", [
        "章节结构量化（故事线/视角/主题漂移/感情线×故事线）",
        "章节标签量化看板（分布速览：章节类型/感情线/战斗强度/地点/人物）",
    ], "保留 2 份，拆分职责",
     "「结构量化」= 数据治理与结构研究；「看板」= 速览聚合。重叠处（感情线/故事线分布）由看板保留速览图，结构量化聚焦漂移与交叉分析。"),

    ("G4 语言计量 ×4", "轻度重叠", [
        "词汇计量（词频/TTR/漂移）",
        "口头禅量化（标志短语/角色标志语）",
        "风格计量（文体指纹/节奏）",
        "对打动作量化（动作词表/招式序列）",
    ], "保留 4 份，归位归类",
     "口头禅量化是词汇计量的角色侧深化（可并入词汇计量做「角色标志语」章节，或保留独立）；对打动作量化归「章节/语言」边界——建议归档到语言计量组并在报告中心改分类。"),

    ("G5 人物 ×3", "轻度重叠", [
        "人物关系网络（共现/中心性/社区）",
        "派生维度量化（出场vs提及背离/人物-地点共现）",
        "角色性格量化（六轴性格）",
    ], "保留 3 份（维度各自独立）",
     "人物-地点共现与空间报告、人物网络有交集，但「出场vs提及背离」是独有指标，建议保留并互链。"),

    ("G6 总览 vs 专业报告", "历史遗留重叠", [
        "分析报告（八节综合：人物/时间轴/空间/故事线/感情线）",
        "人物关系网络 / 时间节奏量化 / 空间地点分析报告 / 章节结构量化 / 情感时序",
    ], "分析报告降级为「导读总览」，各节链接到专业报告",
     "分析报告的八节内容均已被后分化专业报告覆盖或超越。建议：保留其作为入门总览，每节加「详见 XX 报告」跳转，避免重复维护；或将其归档。"),
]

# 动作清单（安全等级）
ACTIONS = [
    ("L1 · 清理残留", 2, [
        ("产物/苇舟江湖梦_情感时序.html.bak", "升级图表前的旧版备份，现版已可用；98 行差异为图表升级，非独有内容", "删除或移入数据归档/"),
        ("产物/echarts-kit.js（CDN 依赖）", "14 份旧报告仍靠它从 jsdelivr 惰性加载 ECharts；离线时图表降级为提示", "改为优先加载本地 echarts.min.js（保留 kit 作回退）"),
    ]),
    ("L2 · 入口收敛", 1, [
        ("产物/index.html（旧，注册 12 份）", "与报告中心(19份)、图书馆(17项) 三个入口重叠", "统一收敛到报告中心；index.html 保留为跳转页"),
        ("可视化三页未注册任何入口", "叙事可视化体系(23/24/25) 只有页间互链，外部找不到", "注册进报告中心 + 图书馆（每类加一个分类）"),
        ("黄家概况.html 未进入口", "独立研究页，外部无法发现", "注册进报告中心「研究考据」"),
    ]),
    ("L3 · 合并重构（需构建器改动）", 3, [
        ("空间 4 份 → 1+1", "按 G1 方案：主报告吸收方位约束与地名热度；时间节奏去掉第4节", "改 09/11/20/15 生成器 + 重建"),
        ("分析报告 → 导读总览", "按 G6 方案：各节加「详见」链接或归档", "改 08 生成器 + 重建"),
        ("口头禅量化 → 并入词汇计量", "按 G4 方案（可选）", "改 05/18 生成器 + 重建"),
    ]),
    ("L4 · 保持现状", 0, [
        ("可视化叙事三页 / 原文阅读 / 关键词索引 / 组件库", "独立体系，职责清晰，不动", "—"),
        ("官制考究 / 建都推演 / 黄家概况 / 统计推断", "独立研究，不重复，不动", "—"),
    ]),
]

# ---------------------------------------------------------------- HTML
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def main():
    files = [r[0] for r in REPORTS]
    n_missing = [f for f in files if not os.path.exists(os.path.join(OUT, f))]

    # 入口覆盖统计
    rc = sum(1 for r in REPORTS if r[3]); lib = sum(1 for r in REPORTS if r[4]); top = sum(1 for r in REPORTS if r[5])
    unreg = [r[1] for r in REPORTS if not (r[3] or r[4] or r[5])]

    # 分组渲染
    groups_order = ["总览", "人物", "章节", "时空地理", "语言计量", "情感节奏", "研究考据", "叙事可视化", "工具阅读"]
    group_rows = ""
    for g in groups_order:
        rows = [r for r in REPORTS if r[2] == g]
        if not rows:
            continue
        rows_html = ""
        for (f, t, _, rcl, libl, topl, desc) in rows:
            badge = []
            badge.append('<span class="b b-rc">报告中心</span>' if rcl else '<span class="b b-off">—</span>')
            badge.append('<span class="b b-lib">图书馆</span>' if libl else '<span class="b b-off">—</span>')
            badge.append('<span class="b b-top">顶层索引</span>' if topl else '<span class="b b-off">—</span>')
            rows_html += (f'<tr><td class="f">{esc(f)}</td><td>{esc(t)}</td>'
                          f'<td class="desc">{esc(desc)}</td><td class="bdg">{" ".join(badge)}</td></tr>')
        group_rows += f'<div class="grp"><h3>{g} <small>{len(rows)} 份</small></h3>'
        group_rows += ('<table><thead><tr><th>文件</th><th>标题</th><th>定位/差异</th><th>入口覆盖</th></tr></thead>'
                       f'<tbody>{rows_html}</tbody></table></div>')

    # 重复组渲染
    groups_html = ""
    for (name, level, items, action, note) in GROUPS:
        lvl = {"高度重叠": "hi", "中度重叠": "mid", "轻度重叠": "lo", "历史遗留重叠": "hi"}[level]
        items_html = "".join(f'<li>{esc(i)}</li>' for i in items)
        groups_html += (f'<div class="dup"><div class="dup-h"><span class="lv lv-{lvl}">{esc(level)}</span>'
                        f'<h3>{esc(name)}</h3></div>'
                        f'<ul>{items_html}</ul>'
                        f'<p class="act"><b>建议：</b>{esc(action)}</p>'
                        f'<p class="note">{esc(note)}</p></div>')

    # 动作清单渲染
    actions_html = ""
    for (title, sev, items, ) in ACTIONS:
        rows_html = "".join(f'<tr><td class="f">{esc(fp)}</td><td>{esc(why)}</td><td class="how">{esc(how)}</td></tr>'
                            for (fp, why, how) in items)
        cls = "sev1" if "L1" in title else ("sev2" if "L2" in title else ("sev3" if "L3" in title else "sev4"))
        actions_html += (f'<div class="act-block {cls}"><h3>{esc(title)} <small>{sev} 项</small></h3>'
                         f'<table><thead><tr><th>文件/对象</th><th>理由</th><th>建议动作</th></tr></thead>'
                         f'<tbody>{rows_html}</tbody></table></div>')

    html = TEMPLATE
    html = html.replace("/*GROUP*/", group_rows).replace("/*DUP*/", groups_html).replace("/*ACT*/", actions_html)
    html = html.replace("/*STATS*/", json.dumps({
        "total": len(REPORTS), "rc": rc, "lib": lib, "top": top,
        "unreg": unreg, "missing": n_missing, "dup_groups": len(GROUPS),
    }, ensure_ascii=False))
    out = os.path.join(OUT, "苇舟江湖梦_报告归纳整理.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("reports:", len(REPORTS), "| rc:", rc, "lib:", lib, "top:", top)
    print("unregistered:", unreg)
    print("missing files:", n_missing or "无")
    print("written:", out)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>苇舟江湖梦 · 报告归纳整理</title>
<style>
:root{--bg:#0a0f1c;--panel:rgba(20,32,54,.62);--brd:rgba(90,150,230,.22);--txt:#e8eefc;--muted:#9fb2d4;
  --blue:#3b82f6;--cyan:#22d3ee;--violet:#a78bfa;--amber:#f59e0b;--red:#ef4444;--green:#34d399;}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 700px at 80% -10%,rgba(167,139,250,.16),transparent 60%),
  radial-gradient(900px 600px at 0% 110%,rgba(34,211,238,.12),transparent 55%),var(--bg);
  color:var(--txt);font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",system-ui,sans-serif;line-height:1.65}
.wrap{max-width:1180px;margin:0 auto;padding:28px 22px 80px}
header h1{margin:0;font-size:27px;letter-spacing:2px;background:linear-gradient(90deg,var(--violet),var(--cyan),var(--blue));
  -webkit-background-clip:text;background-clip:text;color:transparent}
header p{margin:6px 0 0;color:var(--muted);font-size:14px}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:18px 0 4px}
@media(max-width:760px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:var(--panel);border:1px solid var(--brd);border-radius:12px;padding:12px 14px}
.kpi b{font-size:22px;display:block}.kpi span{color:var(--muted);font-size:12px}
section{background:var(--panel);border:1px solid var(--brd);border-radius:16px;padding:18px;margin-top:20px;
  backdrop-filter:blur(14px);box-shadow:0 10px 40px rgba(0,0,0,.35)}
section>h2{margin:0 0 12px;font-size:20px;display:flex;align-items:center;gap:8px}
section>h2 .dot{width:12px;height:12px;border-radius:3px}
.grp{margin-bottom:16px}
.grp h3{margin:14px 0 6px;font-size:16px;color:var(--cyan)}
.grp h3 small{color:var(--muted);font-size:12px}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;color:var(--muted);font-weight:600;border-bottom:1px solid var(--brd);padding:6px 8px}
td{padding:6px 8px;border-bottom:1px solid rgba(90,150,230,.08);vertical-align:top}
td.f{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#c9d8f5;white-space:nowrap}
td.desc{color:var(--muted)}
.b{display:inline-block;font-size:10.5px;border-radius:6px;padding:1px 6px;margin:1px 2px;white-space:nowrap}
.b-rc{background:rgba(59,130,246,.18);color:#8ab6ff;border:1px solid rgba(59,130,246,.4)}
.b-lib{background:rgba(34,211,238,.14);color:#7fe6f2;border:1px solid rgba(34,211,238,.35)}
.b-top{background:rgba(167,139,250,.16);color:#c3abff;border:1px solid rgba(167,139,250,.4)}
.b-off{background:rgba(120,140,180,.08);color:#5c6a86;border:1px solid transparent}
.dup{background:rgba(6,11,22,.4);border:1px solid rgba(90,150,230,.14);border-radius:12px;padding:12px 14px;margin-bottom:14px}
.dup-h{display:flex;align-items:center;gap:10px}
.dup-h h3{margin:0;font-size:16px}
.lv{font-size:11px;font-weight:700;border-radius:8px;padding:2px 8px;white-space:nowrap}
.lv-hi{background:rgba(239,68,68,.16);color:#ff9d9d;border:1px solid rgba(239,68,68,.45)}
.lv-mid{background:rgba(245,158,11,.15);color:#ffd18a;border:1px solid rgba(245,158,11,.4)}
.lv-lo{background:rgba(52,211,153,.13);color:#8ff0c6;border:1px solid rgba(52,211,153,.35)}
.dup ul{margin:8px 0 6px;padding-left:20px;color:#d7e2f7}
.dup ul li{margin:2px 0}
.dup .act{color:#ffd9a0;margin:6px 0 2px}
.dup .note{color:var(--muted);font-size:12.5px;margin:4px 0 0}
.act-block{border-radius:12px;padding:12px 14px;margin-bottom:14px;border:1px solid}
.act-block h3{margin:0 0 8px;font-size:16px}
.act-block h3 small{font-size:12px;color:var(--muted)}
td.how{color:#8ff0c6}
.sev1{background:rgba(239,68,68,.07);border-color:rgba(239,68,68,.35)}
.sev2{background:rgba(245,158,11,.06);border-color:rgba(245,158,11,.32)}
.sev3{background:rgba(59,130,246,.06);border-color:rgba(59,130,246,.3)}
.sev4{background:rgba(52,211,153,.05);border-color:rgba(52,211,153,.28)}
.notice{background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.35);border-radius:12px;
  padding:10px 14px;color:#ffd9a0;font-size:13px;margin-top:14px}
.hint{color:var(--muted);font-size:12px;margin-top:8px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>苇舟江湖梦 · 报告归纳整理</h1>
  <p>只读盘点：全部报告按主题分组、识别重复/重叠、输出分安全等级的动作清单。<b style="color:#ffd9a0">本页不删除/移动任何文件，执行需确认。</b></p>
  <div class="kpis" id="kpis"></div>
</header>

<section>
  <h2><span class="dot" style="background:var(--cyan)"></span>① 报告全景地图（按主题分组）</h2>
  /*GROUP*/
  <div class="hint">入口覆盖：报告中心(19) / 图书馆(17项) / 顶层 index.html(12) —— 三个入口本身即存在重叠，见 ③。</div>
</section>

<section>
  <h2><span class="dot" style="background:var(--amber)"></span>② 重复/重叠组分析</h2>
  /*DUP*/
  <div class="hint">重叠级别依据「主题 + 图表/数据源 + 结论」三重判断；文学量化报告互相有交集属正常，此处只收敛真正冗余的。</div>
</section>

<section>
  <h2><span class="dot" style="background:var(--red)"></span>③ 建议动作清单（按安全等级）</h2>
  /*ACT*/
  <div class="notice">⚠ 执行前需确认：L1/L2 为低风险（清理残留/入口收敛），L3 涉及生成器改动与重建（会覆盖对应 HTML 产物），
  每项执行前会再次列出具体文件清单。L4 不动。</div>
</section>

</div>

<script>
const S=/*STATS*/;
document.getElementById('kpis').innerHTML=[
  ['报告总数',S.total],['报告中心',S.rc],['图书馆',S.lib],['顶层索引',S.top],['重复组',S.dup_groups]
].map(([k,v])=>'<div class="kpi"><b>'+v+'</b><span>'+k+'</span></div>').join('');
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
