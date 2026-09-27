#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《苇舟江湖梦》全文本词汇计量分析。
步骤：
 1. 建 analysis/ 目录
 2. 读取 full_text.txt，按中文数字章节标记切分 59 章，jieba 分词，
    内置停用词表 + 词性过滤(仅保留 n/v/a 开头的实词)
 3. 计算：全本 Top50；逐章 TTR；全本平均句长(按 。！？ 切分)
 4. 用词漂移：前 19 章 vs 后 19 章高频词差异
 5. 生成 SVG 图表(59 章 TTR 折线图、Top20 水平条形图)
 6. 写 analysis/lexical_stats.json
 7. 写 产物/苇舟江湖梦_词汇计量.html
纪律：只读取与分析，绝不修改任何源文件。
"""
import os
import re
import json

import jieba
from jieba import posseg as pseg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "数据", "full_text.txt")
ANALYSIS_DIR = os.path.join(ROOT, "数据", "analysis")
OUT_DIR = os.path.join(ROOT, "产物")

# 0. 人物专有名词保护：从规范人名表注入 jieba，避免三字/生僻人名被拆成子词
#    例：「陈奉天」默认切成「陈 / 奉天」，而「奉天」恰是现实历史地名，
#    导致人名在词频与地名 NER 维度被误拆。注入整名（高词频 + 名词标记）后优先匹配，
#    并以专有名词身份进入实词统计。
def protect_char_names():
    try:
        cs = json.load(open(os.path.join(ROOT, "数据", "char_stats.json"), encoding="utf-8"))
        names = [c["name"] for c in cs if c.get("name")]
    except Exception:
        names = []
    n = 0
    for name in names:
        if len(name) >= 2:
            jieba.add_word(name, freq=100000, tag="n")
            n += 1
    return n

PROTECTED_NAMES = protect_char_names()

# 1. 建目录
os.makedirs(ANALYSIS_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# 2. 内置中文停用词表（标点、虚词、常见功能词、高频对话动词等）
STOPWORDS = set("""
的 了 是 在 我 你 他 她 它 这 那 就 也 都 和 与 及 其 之 而 以 于 把 被 让 给
等 又 再 还 很 太 最 更 不 没 别 莫 但 却 然 因 为 由于 所以 如果 虽然 但是 而且
并且 或者 于是 然后 然而 不过 只是 这样 那样 怎么 什么 谁 哪 多少 一些 一样
自己 我们 你们 他们 大家 人家 这个 那个 这些 那些 一种 没有 不是 就是 还是
已经 正在 将要 可以 应该 能够 会 要 得 着 过 啊 呀 吗 呢 吧 哦 嗯 哎 咦 嘛 啦
喽 呗 罢 哩 些 个 们 来 去 说 道 看 见 知 道 想 道 道 叫 道 道 道
道 曰 云 谓 言 道 道 道 道 道 道 道 道 道 道 道 道 道 道 道 道 道 道 道 道 道
虽 虽 然 而 乃 则 且 若 倘 倘 若 苟 缘 顾 岂 焉 奚 胡 盍 恶 安 何 曷 几 盍
喏 咄 嘻 噫 嗟 唉 呜 呼 嗟 乎 哉 矣 耳 焉 耶 与 欤 夫 盖 窃 谨 伏 敬 敢 辱
所谓 所谓 所有 有所 无所 得以 加以 予以 据 据 按 按 依 照 替 向 朝 从 自 由
对 对于 关于 至于 除了 将 把 使 令 教 让 叫 任 随 跟 同 与 跟 给 替 为 被 叫 让
一 二 三 四 五 六 七 八 九 十 百 千 万 几 两 半 诸 众 各 每 某 另 旁 上 下 中
前 后 左 右 内 外 东 西 南 北 里 间 旁 边 面 头 底 顶 上 下 内 外
现在 正在 刚才 从前 将来 然后 后来 同时 顿时 渐渐 忽然 突然 依然 仍旧 依旧
大概 也许 或许 究竟 毕竟 索性 简直 甚至 乃至 反而 反倒 幸而 幸好 可惜 难怪
起来 出来 过来 过去 上去 下去 进来 进去 出来 开来 开来 出来 出来
的话 罢了 而已 似的 一般 一样 等等 之类 所谓 如此 这么 那么 怎样 如何 何等
的话 罢了 而已 似的 一般 一样 等等 之类 所谓 如此 这么 那么 怎样 如何 何等
""".split())

# 补充：高频通用动词 / 体貌复合词（无显著语义指向，污染关键词）
STOPWORDS |= set("""
有 到 走 带 看 听 问 知 道 时 起 来 出 进 回 过 想 见 叫 让 使 做 干 用 拿 给
笑 点 摇 望 盯 跟 跑 飞 落 开 关 站 坐 躺 吃 喝 睡 替 帮 等 赶 送 接 找 抓 杀
好 多 少 大 小 新 旧 长 短 高 低 远 近 快 慢 早 晚 真 假 全 整 同 异
看着 听着 想着 知道 起来 出来 过来 回去 进来 出去 走到 看到 听到 问到 笑着
点头 回头 转身 开口 伸手 抬头 低头 起身 站起 坐下 离开 进去 出来 上去 下去
看看 还有 不知 可 能 倒 直接 二人 说完 准备 事 人 话 眼 手 脸 心 身 头
便是 只见 说话 待 却 微 忽 顿 又 仍 皆 俱
""".split())

# 补充：标点与空白（词性过滤本就会排除，这里再显式兜底）
PUNCT = set("，。！？；：、（）《》〈〉“”‘’「」『』【】—…·.,;:!?()[]{}<>\"'　 \n\tabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789%℃°")


def is_content_token(word: str, flag: str) -> bool:
    """仅保留名词/动词/形容词（词性标记以 n/v/a 开头）且非停用词、含汉字。"""
    if not re.search(r"[一-鿿]", word):
        return False
    if word in STOPWORDS:
        return False
    if word in PUNCT:
        return False
    if len(word.strip()) == 0:
        return False
    return flag.startswith(("n", "v", "a"))


# 章节切分：行首为「中文/阿拉伯数字 + 、 ． .」且整行仅此内容
CN_DIGIT = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4,
            "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
CN_UNIT = {"十": 10, "百": 100}


def cn_to_int(s: str) -> int:
    if s.isdigit():
        return int(s)
    total, cur, has = 0, 0, False
    for ch in s:
        if ch in CN_DIGIT:
            cur = CN_DIGIT[ch]
            has = True
        elif ch in CN_UNIT:
            unit = CN_UNIT[ch]
            if not has:
                cur = 1
            total += cur * unit
            cur, has = 0, False
    total += cur
    return total


MARKER = re.compile(r"^([一二三四五六七八九十百零〇\d]+)[、．.]\s*$")


def split_chapters(text: str):
    lines = text.split("\n")
    markers = []
    for i, ln in enumerate(lines):
        m = MARKER.match(ln)
        if m:
            markers.append((i, cn_to_int(m.group(1))))
    markers.sort(key=lambda x: x[1])
    chapters = []
    for idx, (li, val) in enumerate(markers):
        start = li + 1
        end = markers[idx + 1][0] if idx + 1 < len(markers) else len(lines)
        body = lines[start:end]
        while body and body[0].strip() == "":
            body.pop(0)
        while body and body[-1].strip() == "":
            body.pop()
        chapters.append((val, "\n".join(body)))
    return chapters


def read_full_text():
    with open(SRC, encoding="utf-8") as f:
        return f.read()


def tokenize(text: str):
    """返回过滤后的实词列表。"""
    toks = []
    for word, flag in pseg.cut(text):
        w = word.strip()
        if is_content_token(w, flag):
            toks.append(w)
    return toks


# ---- 主流程 ----
print(f"已注入 {PROTECTED_NAMES} 个规范人名保护 jieba 词典")
print("读取全文...")
full_text = read_full_text()
chapters = split_chapters(full_text)
print(f"切分得到 {len(chapters)} 章")

# 全本分词
print("全本分词(jieba + 词性/停用词过滤)...")
all_tokens = tokenize(full_text)
from collections import Counter
freq = Counter(all_tokens)
total_tokens = len(all_tokens)
unique_tokens = len(freq)
top50 = [{"word": w, "freq": c} for w, c in freq.most_common(50)]

# 逐章 TTR
print("计算逐章 TTR...")
ttr_list = []
for val, body in chapters:
    ctoks = tokenize(body)
    if ctoks:
        ttr = len(set(ctoks)) / len(ctoks)
    else:
        ttr = 0.0
    ttr_list.append({"chapter": val, "ttr": round(ttr, 4)})
ttr_mean = sum(x["ttr"] for x in ttr_list) / len(ttr_list)

# 全本平均句长（按 。！？ 切分，统计每句汉字数）
print("计算平均句长...")
sentences = re.split(r"[。！？]", full_text)
sent_chars = [len(re.findall(r"[一-鿿]", s)) for s in sentences if re.search(r"[一-鿿]", s)]
avg_sent_len = sum(sent_chars) / len(sent_chars) if sent_chars else 0.0

# 用词漂移：前 19 章 vs 后 19 章
print("计算前后期用词漂移...")
N_HALF = 19
early_chaps = [b for v, b in chapters if v <= N_HALF]
late_chaps = [b for v, b in chapters if v > len(chapters) - N_HALF]
early_tokens = []
for b in early_chaps:
    early_tokens.extend(tokenize(b))
late_tokens = []
for b in late_chaps:
    late_tokens.extend(tokenize(b))

early_freq = Counter(early_tokens)
late_freq = Counter(late_tokens)
early_total = len(early_tokens)
late_total = len(late_tokens)


def rate(counter, total):
    return {w: c / total * 1000.0 for w, c in counter.items()} if total else {}


early_rate = rate(early_freq, early_total)
late_rate = rate(late_freq, late_total)

early_top = [{"word": w, "freq": c} for w, c in early_freq.most_common(30)]
late_top = [{"word": w, "freq": c} for w, c in late_freq.most_common(30)]

# 差异词：仅在一半显著出现 / 频次差显著
vocab = set(early_freq) | set(late_freq)
diff_rows = []
for w in vocab:
    e = early_freq.get(w, 0)
    l = late_freq.get(w, 0)
    er = early_rate.get(w, 0.0)
    lr = late_rate.get(w, 0.0)
    delta = lr - er  # 正：后期更显著
    diff_rows.append({"word": w, "early": e, "late": l,
                      "early_rate": round(er, 3), "late_rate": round(lr, 3),
                      "delta": round(delta, 3)})

# 仅在某一半显著出现（在另一半未出现或极少）
only_early = sorted([d for d in diff_rows if d["late"] == 0 and d["early"] >= 5],
                    key=lambda x: -x["early"])
only_late = sorted([d for d in diff_rows if d["early"] == 0 and d["late"] >= 5],
                   key=lambda x: -x["late"])
# 频次差显著（按 delta 绝对值）
big_diff = sorted(diff_rows, key=lambda x: -abs(x["delta"]))[:40]

drift = {
    "early_top": early_top,
    "late_top": late_top,
    "diff": big_diff,
    "only_early": [{"word": d["word"], "early": d["early"]} for d in only_early[:20]],
    "only_late": [{"word": d["word"], "late": d["late"]} for d in only_late[:20]],
    "early_token_total": early_total,
    "late_token_total": late_total,
}

# ---- SVG 图表 ----
def svg_ttr_line(ttr_list):
    """59 章 TTR 折线图。"""
    W, H = 900, 380
    ml, mr, mt, mb = 60, 30, 30, 50
    plot_w = W - ml - mr
    plot_h = H - mt - mb
    n = len(ttr_list)
    ymax = 1.0
    ymin = 0.0
    x = lambda i: ml + (plot_w * i / (n - 1)) if n > 1 else ml
    y = lambda v: mt + plot_h * (1 - (v - ymin) / (ymax - ymin))

    # 网格 + Y 轴刻度
    grid = ""
    for k in range(0, 11):
        val = ymin + (ymax - ymin) * k / 10
        yy = y(val)
        grid += f'<line x1="{ml}" y1="{yy:.1f}" x2="{W-mr}" y2="{yy:.1f}" stroke="#e3e8ef" stroke-width="1"/>'
        grid += f'<text x="{ml-8}" y="{yy+4:.1f}" font-size="11" fill="#7a8699" text-anchor="end">{val:.1f}</text>'

    # X 轴刻度（每 5 章）
    xticks = ""
    for i in range(0, n, 5):
        xx = x(i)
        xticks += f'<text x="{xx:.1f}" y="{H-mb+18}" font-size="11" fill="#7a8699" text-anchor="middle">{ttr_list[i]["chapter"]}</text>'

    pts = " ".join(f"{x(i):.1f},{y(d['ttr']):.1f}" for i, d in enumerate(ttr_list))
    area = f"{ml},{y(ymin):.1f} " + pts + f" {x(n-1):.1f},{y(ymin):.1f}"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Inter, sans-serif">
<rect width="{W}" height="{H}" fill="#ffffff"/>
<text x="{W/2:.0f}" y="20" font-size="15" font-weight="600" fill="#1f2a37" text-anchor="middle">59 章 类符/形符比 (TTR) 折线图</text>
{grid}
<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{H-mb}" stroke="#9aa7b8" stroke-width="1.2"/>
<line x1="{ml}" y1="{H-mb}" x2="{W-mr}" y2="{H-mb}" stroke="#9aa7b8" stroke-width="1.2"/>
<text x="{ml-8}" y="{mt-10}" font-size="11" fill="#7a8699" text-anchor="end">TTR</text>
<text x="{W/2:.0f}" y="{H-12}" font-size="11" fill="#7a8699" text-anchor="middle">章节序号</text>
{poly_area(area)}
<polyline points="{pts}" fill="none" stroke="#2f6df0" stroke-width="2"/>
{xticks}
<text x="{W-mr}" y="{mt+4}" font-size="11" fill="#2f6df0" text-anchor="end">均值 {ttr_mean:.3f}</text>
</svg>'''
    return svg


def poly_area(area):
    return f'<polygon points="{area}" fill="#2f6df0" fill-opacity="0.08"/>'


def svg_top20_bar(top20):
    """Top20 词水平条形图。"""
    items = top20[:20]
    W, H = 900, 560
    ml, mr, mt, mb = 110, 70, 30, 30
    plot_w = W - ml - mr
    plot_h = H - mt - mb
    maxf = max(x["freq"] for x in items) if items else 1
    row_h = plot_h / len(items)
    bar_max = plot_w

    bars = ""
    for i, it in enumerate(items):
        yy = mt + i * row_h + row_h * 0.15
        bh = row_h * 0.7
        bw = bar_max * (it["freq"] / maxf)
        bars += f'<text x="{ml-10}" y="{yy+bh/2+4:.1f}" font-size="13" fill="#1f2a37" text-anchor="end">{it["word"]}</text>'
        bars += f'<rect x="{ml}" y="{yy:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="#2f6df0"/>'
        bars += f'<text x="{ml+bw+6:.1f}" y="{yy+bh/2+4:.1f}" font-size="12" fill="#55607a">{it["freq"]}</text>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Inter, sans-serif">
<rect width="{W}" height="{H}" fill="#ffffff"/>
<text x="{W/2:.0f}" y="20" font-size="15" font-weight="600" fill="#1f2a37" text-anchor="middle">全本 Top20 关键词（实词词频）</text>
{bars}
<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{H-mb}" stroke="#9aa7b8" stroke-width="1.2"/>
</svg>'''
    return svg


ttr_svg = svg_ttr_line(ttr_list)
top20_svg = svg_top20_bar(top50)

# ---- 6. 写 JSON ----
stats = {
    "top_words": top50,
    "ttr": ttr_list,
    "avg_sent_len": round(avg_sent_len, 3),
    "drift": {
        "early_top": drift["early_top"],
        "late_top": drift["late_top"],
        "diff": drift["diff"],
        "only_early": drift["only_early"],
        "only_late": drift["only_late"],
        "early_token_total": drift["early_token_total"],
        "late_token_total": drift["late_token_total"],
    },
    "meta": {
        "total_tokens": total_tokens,
        "unique_tokens": unique_tokens,
        "ttr_mean": round(ttr_mean, 4),
        "n_chapters": len(chapters),
    },
}
json_path = os.path.join(ANALYSIS_DIR, "lexical_stats.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)
print("写入", json_path)

# 漂移解读文本
late_words = "、".join(d["word"] for d in drift["only_late"][:12]) or "（无显著独占词）"
early_words = "、".join(d["word"] for d in drift["only_early"][:12]) or "（无显著独占词）"
rise_words = "、".join(d["word"] for d in drift["diff"][:10] if d["delta"] > 0) or "—"
fall_words = "、".join(d["word"] for d in drift["diff"][:10] if d["delta"] < 0) or "—"

drift_html = f"""
<p>将全本 59 章以前 19 章（市井江湖）与后 19 章（庙堂朝局）对半切分，分别统计实词频次并折算为「每千词出现率」以消除篇幅差异，比较如下：</p>
<ul>
<li><b>仅前期显著出现</b>（后 19 章基本消失）的实词：{early_words}</li>
<li><b>仅后期显著出现</b>（前 19 章基本缺席）的实词：{late_words}</li>
<li><b>后期相对升势最强</b>（每千词率差最大为正）的实词：{rise_words}</li>
<li><b>前期相对降势最强</b>的实词：{fall_words}</li>
</ul>
<p>前期语料以江湖草莽、市井行旅、个人恩怨相关名词为主，体现「苇舟」「少年」「剑」「客」式的漂泊与侠气；后期语料中朝堂、权谋、军国、制度类名词比重上升，呈现出由「市井江湖」向「庙堂朝局」的语义迁移。需注意：差异同时受情节推进与人物线转移影响，此处仅作计量层面的显著漂移刻画，不替代细读。</p>
"""

method_html = f"""
<ul>
<li><b>分词</b>：jieba 精确模式 + 词性标注；仅保留词性标记以 <code>n / v / a</code> 开头的名词、动词、形容词（实词），并剔除内置停用词表（含标点、虚词、高频对话动词如「说/道」等）。</li>
<li><b>Top 关键词</b>：全本实词按出现频次降序取前 50。</li>
<li><b>逐章 TTR</b>：类符/形符比 = 该章不重复实词数 ÷ 该章实词总数。</li>
<li><b>平均句长</b>：以「。！？」切分全本，统计每句汉字数取均值，得 <b>{avg_sent_len:.2f}</b> 字/句。</li>
<li><b>用词漂移</b>：前 19 章 vs 后 19 章，各取每千词出现率，比较独占词与率差。</li>
<li><b>方法注记（重要）</b>：TTR 受章节长度显著影响——短章的可复用实词少，TTR 天然偏高；长章因重复用词多，TTR 天然偏低。本折线图已观察到短章 TTR 普遍偏高，属正常计量现象，解读章节间 TTR 差异时须结合章节实词总量，不宜直接据此判定「词汇丰富度」。</li>
</ul>
"""

# ---- 7. 写 HTML ----
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>苇舟江湖梦 · 词汇计量</title>
<link rel="stylesheet" href="theme.css">
</head>
<body>
<div class="wrap">
  <h1>《苇舟江湖梦》词汇计量报告</h1>
  <div class="sub">文学计量分析 · 词频 / TTR / 前后期用词漂移 · 全本 {len(chapters)} 章</div>

  <div class="card">
    <div class="kpis">
      <div class="kpi"><div class="v">{total_tokens:,}</div><div class="l">全本实词总量</div></div>
      <div class="kpi"><div class="v">{unique_tokens:,}</div><div class="l">不重复实词(类符)</div></div>
      <div class="kpi"><div class="v">{ttr_mean:.3f}</div><div class="l">平均 TTR</div></div>
      <div class="kpi"><div class="v">{avg_sent_len:.1f}</div><div class="l">平均句长(字)</div></div>
    </div>
  </div>

  <div class="card">
    <h2>59 章 TTR 折线图</h2>
    {ttr_svg}
  </div>

  <div class="card">
    <h2>全本 Top20 关键词</h2>
    {top20_svg}
  </div>

  <div class="card">
    <h2>前后期用词漂移（市井 → 庙堂）</h2>
    <div class="note">{drift_html}</div>
  </div>

  <div class="card">
    <h2>方法注记</h2>
    <div class="note">{method_html}</div>
  </div>

  <div class="card">
    <h2>全本 Top50 关键词表</h2>
    <table>
      <tr><th>#</th><th>词</th><th>频次</th><th>#</th><th>词</th><th>频次</th></tr>
      {''.join(
        f'<tr><td>{i*2+1}</td><td>{top50[i*2]["word"]}</td><td>{top50[i*2]["freq"]}</td>'
        f'<td>{i*2+2 if i*2+1<len(top50) else ""}</td>'
        f'<td>{top50[i*2+1]["word"] if i*2+1<len(top50) else ""}</td>'
        f'<td>{top50[i*2+1]["freq"] if i*2+1<len(top50) else ""}</td></tr>'
        for i in range((len(top50)+1)//2))
      }
    </table>
  </div>
</div>
</body>
</html>
"""

html_path = os.path.join(OUT_DIR, "苇舟江湖梦_词汇计量.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("写入", html_path)

# 确认两文件写入成功
assert os.path.exists(json_path) and os.path.getsize(json_path) > 0, "JSON 写入失败"
assert os.path.exists(html_path) and os.path.getsize(html_path) > 0, "HTML 写入失败"

# 8. 打印结果行
top_word = top50[0]["word"]
print(f"LEXICAL DONE: top_word={top_word} ttr_mean={ttr_mean:.4f}")
