# -*- coding: utf-8 -*-
"""
《苇舟江湖梦》章节标注数据 —— 统计推断
文学计量分析员：对叙事假设做非参数检验（样本非正态，用 Mann-Whitney U / Spearman）。
纪律：仅读取并分析 chapter_data/all_tags.json，绝不修改任何源文件。
"""
import os
import json
import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "数据", "chapter_data", "all_tags.json")
OUT_DIR = os.path.join(ROOT, "数据", "analysis")
HTML_OUT = os.path.join(ROOT, "产物", "苇舟江湖梦_统计推断.html")

ALPHA = 0.05  # 原始显著性水平
# 多重比较：共 5 项检验 -> Bonferroni 校正阈值
N_TESTS = 5
BONFERRONI = ALPHA / N_TESTS

os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 读取数据（只读，不修改） ----------
with open(SRC, encoding="utf-8") as f:
    data = json.load(f)

N = len(data)
print(f"载入章节数: {N}")

# ---------- 工具函数 ----------
def split_by(pred):
    """按 pred(d) 把 combat_intensity 分为 出场组 / 未出场组。"""
    present = [d["combat_intensity"] for d in data if pred(d)]
    absent = [d["combat_intensity"] for d in data if not pred(d)]
    return present, absent

def cliffs_delta(a, b):
    """Cliff's delta = (P(a>b) - P(a<b))，范围 [-1,1]，对序数/非正态稳健。"""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    gt = int(((a[:, None] > b[None, :]).sum()))
    lt = int(((a[:, None] < b[None, :]).sum()))
    denom = len(a) * len(b)
    return (gt - lt) / denom if denom else float("nan")

def delta_magnitude(d):
    ad = abs(d)
    if ad < 0.147:
        return "可忽略"
    if ad < 0.33:
        return "小"
    if ad < 0.474:
        return "中"
    return "大"

def rho_magnitude(r):
    ar = abs(r)
    if ar < 0.1:
        return "可忽略"
    if ar < 0.3:
        return "小"
    if ar < 0.5:
        return "中"
    return "大"

results = []

# ---------- a. 陈奉天 出场 vs 未出场 ----------
present, absent = split_by(lambda d: "陈奉天" in d["characters_present"])
U, p = stats.mannwhitneyu(present, absent, alternative="two-sided")
cd = cliffs_delta(present, absent)
mp, ma = float(np.mean(present)), float(np.mean(absent))
if p < ALPHA:
    dir_word = "高于" if mp > ma else "低于"
    interp = (f"陈奉天出场的章节（均值 {mp:.2f}，n={len(present)}）战斗强度{dir_word}其未出场章节"
              f"（均值 {ma:.2f}，n={len(absent)}）。U={U:.0f}，p={p:.3f}，Cliff's δ={cd:+.3f}"
              f"（{delta_magnitude(cd)}效应）。差异在 α=0.05 下具有统计学意义。")
else:
    interp = (f"陈奉天出场与未出场章节的战斗强度无显著差异（均值 {mp:.2f} vs {ma:.2f}）。"
              f"U={U:.0f}，p={p:.3f}，Cliff's δ={cd:+.3f}（{delta_magnitude(cd)}效应）。"
              f"不显著，不能拒绝原假设：现有数据不足以说明陈奉天是否出场会影响战斗强度。")
results.append({
    "test": "a_陈奉天_出场vs未出场",
    "method": "Mann-Whitney U (双侧)",
    "stat": round(float(U), 3),
    "p": round(float(p), 4),
    "effect": f"Cliff's δ={cd:+.3f}",
    "significant": bool(p < ALPHA),
    "interpretation": interp,
})

# ---------- b. 任琅 出场 vs 未出场 ----------
present, absent = split_by(lambda d: "任琅" in d["characters_present"])
U, p = stats.mannwhitneyu(present, absent, alternative="two-sided")
cd = cliffs_delta(present, absent)
mp, ma = float(np.mean(present)), float(np.mean(absent))
if p < ALPHA:
    dir_word = "高于" if mp > ma else "低于"
    interp = (f"任琅出场的章节（均值 {mp:.2f}，n={len(present)}）战斗强度{dir_word}其未出场章节"
              f"（均值 {ma:.2f}，n={len(absent)}）。U={U:.0f}，p={p:.3f}，Cliff's δ={cd:+.3f}"
              f"（{delta_magnitude(cd)}效应）。差异在 α=0.05 下具有统计学意义。")
else:
    interp = (f"任琅出场与未出场章节的战斗强度无显著差异（均值 {mp:.2f} vs {ma:.2f}；未出场仅 n={len(absent)} 章）。"
              f"U={U:.0f}，p={p:.3f}，Cliff's δ={cd:+.3f}（{delta_magnitude(cd)}效应）。"
              f"不显著，不能拒绝原假设：样本未表现出任琅是否出场对战斗强度的系统性影响。"
              f"（注：未出场组仅 {len(absent)} 章，组间极不平衡，结论尤其需谨慎。）")
results.append({
    "test": "b_任琅_出场vs未出场",
    "method": "Mann-Whitney U (双侧)",
    "stat": round(float(U), 3),
    "p": round(float(p), 4),
    "effect": f"Cliff's δ={cd:+.3f}",
    "significant": bool(p < ALPHA),
    "interpretation": interp,
})

# ---------- c. chapter_type 含'战斗' vs 不含 ----------
present, absent = split_by(lambda d: any("战斗" in t for t in d["chapter_type"]))
U, p = stats.mannwhitneyu(present, absent, alternative="two-sided")
cd = cliffs_delta(present, absent)
mp, ma = float(np.mean(present)), float(np.mean(absent))
if p < ALPHA:
    dir_word = "高于" if mp > ma else "低于"
    interp = (f"标注含'战斗/武斗'类型的章节（均值 {mp:.2f}，n={len(present)}）战斗强度{dir_word}不含战斗类型的章节"
              f"（均值 {ma:.2f}，n={len(absent)}）。U={U:.0f}，p={p:.3f}，Cliff's δ={cd:+.3f}"
              f"（{delta_magnitude(cd)}效应）。差异在 α=0.05 下显著，符合'战斗章节更激烈'的直觉。")
else:
    interp = (f"含'战斗'类型与不含'战斗'类型的章节战斗强度无显著差异（均值 {mp:.2f} vs {ma:.2f}）。"
              f"U={U:.0f}，p={p:.3f}，Cliff's δ={cd:+.3f}（{delta_magnitude(cd)}效应）。"
              f"不显著，不能拒绝原假设：标签上的'战斗'类型并不必然对应更高的量化战斗强度。")
results.append({
    "test": "c_章节类型_含战斗vs不含",
    "method": "Mann-Whitney U (双侧)",
    "stat": round(float(U), 3),
    "p": round(float(p), 4),
    "effect": f"Cliff's δ={cd:+.3f}",
    "significant": bool(p < ALPHA),
    "interpretation": interp,
})

# ---------- d. emotion_line 序数 vs combat_intensity 的 Spearman ----------
# 映射（严格按指令）：平淡/日常=0, 升温/进展=1, 虐/悲情=2；其余（无显著感情戏/波折误会/分离离别）按"未明"排除。
emotion_map = {"平淡/日常": 0, "升温/进展": 1, "虐/悲情": 2}
em_ord, ci = [], []
for d in data:
    e = d["emotion_line"]
    if e in emotion_map:
        em_ord.append(emotion_map[e])
        ci.append(d["combat_intensity"])
em_ord = np.asarray(em_ord, dtype=float)
ci = np.asarray(ci, dtype=float)
rho, p = stats.spearmanr(em_ord, ci)
n_corr = len(em_ord)
if p < ALPHA:
    dir_word = "正" if rho > 0 else "负"
    interp = (f"情感线强度序数（平淡=0→虐/悲情=2）与战斗强度呈显著{dir_word}相关"
              f"（Spearman ρ={rho:+.3f}，n={n_corr}，p={p:.3f}，{rho_magnitude(rho)}效应）。"
              f"即情感张力越强的章节，战斗强度整体也越高（或反之）。")
else:
    interp = (f"情感线强度序数与战斗强度无显著相关（Spearman ρ={rho:+.3f}，n={n_corr}，p={p:.3f}，"
              f"{rho_magnitude(rho)}效应）。不显著，不能拒绝原假设：现有样本未呈现情感强度与战斗强度之间的系统性关联。"
              f"（已按指令排除 9 章'无显著感情戏'、2 章'波折/误会'、1 章'分离/离别'等'未明'类别。）")
results.append({
    "test": "d_情感线序数_vs_战斗强度",
    "method": "Spearman 秩相关",
    "stat": round(float(rho), 3),
    "p": round(float(p), 4),
    "effect": f"ρ={rho:+.3f}",
    "significant": bool(p < ALPHA),
    "interpretation": interp,
})

# ---------- e. 主地点含'京城' vs 其他 ----------
present, absent = split_by(lambda d: any("京城" in l for l in d["main_locations"]))
U, p = stats.mannwhitneyu(present, absent, alternative="two-sided")
cd = cliffs_delta(present, absent)
mp, ma = float(np.mean(present)), float(np.mean(absent))
if p < ALPHA:
    dir_word = "高于" if mp > ma else "低于"
    interp = (f"主地点含'京城'的章节（均值 {mp:.2f}，n={len(present)}）战斗强度{dir_word}其他地点的章节"
              f"（均值 {ma:.2f}，n={len(absent)}）。U={U:.0f}，p={p:.3f}，Cliff's δ={cd:+.3f}"
              f"（{delta_magnitude(cd)}效应）。差异在 α=0.05 下具有统计学意义。")
else:
    interp = (f"主地点含'京城'与其他地点的章节战斗强度无显著差异（均值 {mp:.2f} vs {ma:.2f}）。"
              f"U={U:.0f}，p={p:.3f}，Cliff's δ={cd:+.3f}（{delta_magnitude(cd)}效应）。"
              f"不显著，不能拒绝原假设：现有数据不足以说明京城场景对应更高或更低的战斗强度。")
results.append({
    "test": "e_主地点_京城vs其他",
    "method": "Mann-Whitney U (双侧)",
    "stat": round(float(U), 3),
    "p": round(float(p), 4),
    "effect": f"Cliff's δ={cd:+.3f}",
    "significant": bool(p < ALPHA),
    "interpretation": interp,
})

# ---------- 写出 JSON ----------
json_path = os.path.join(OUT_DIR, "stats_inference.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"已写入 {json_path}")

# ---------- 生成 HTML ----------
n_sig = sum(1 for r in results if r["significant"])
sig_tests = [r["test"] for r in results if r["significant"]]

def cls_sig(r):
    return "sig" if r["significant"] else "nsig"

rows = ""
for r in results:
    star = "✅ 显著" if r["significant"] else "— 不显著"
    pclass = "p-sig" if r["significant"] else "p-nsig"
    bonf = "通过" if (r["significant"] and r["p"] < BONFERRONI) else ("未达" if r["significant"] else "—")
    rows += f"""      <tr class="{cls_sig(r)}">
        <td>{r['test']}</td>
        <td>{r['method']}</td>
        <td>{r['stat']}</td>
        <td class="{pclass}">{r['p']}</td>
        <td>{r['effect']}</td>
        <td>{star}</td>
        <td>{bonf}</td>
      </tr>
"""

n_total = len(results)
bonf_text = f"{BONFERRONI:.3f}"

# 通俗解读段落
interpret_blocks = "\n".join(
    f"<li><b>{r['test']}</b>（{r['method']}）：{r['interpretation']}</li>" for r in results
)

# 显著结论摘要
if n_sig == 0:
    summary = "本次 5 项检验中，<b>没有任何一项</b>在 α=0.05 下达到统计显著。按照纪律要求，对 p≥0.05 的结果一律写作「不显著，不能拒绝原假设」，不夸大、不编造显著。"
else:
    summary = (f"本次 {n_total} 项检验中，共 <b>{n_sig}</b> 项在原始 α=0.05 下显著："
               f"<b>{'、'.join(sig_tests)}</b>。"
               f"经 Bonferroni 校正（阈值 {bonf_text}），需进一步核对上述显著项是否仍能通过校正阈值。")

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>苇舟江湖梦 · 章节标注统计推断</title>
<link rel="stylesheet" href="theme.css">
</head>
<body>
<div class="wrap">
  <h1>《苇舟江湖梦》章节标注 · 统计推断报告</h1>
  <div class="sub">文学计量分析 · 非参数检验（Mann-Whitney U / Spearman）· 样本量 N={N} 章 · 生成于分析脚本</div>

  <div class="card">
    <h2>一、结果速览</h2>
    <p>{summary}</p>
    <p class="note">原始显著性水平 α=0.05；共 {n_total} 项检验，Bonferroni 校正阈值 = 0.05 / {n_total} = <b>{bonf_text}</b>。
    下表 <span class="p-sig">红色 p 值</span> 为该检验在原始 α 下显著。</p>
    <table>
      <thead>
        <tr>
          <th>检验</th><th>方法</th><th>统计量</th><th>p 值</th>
          <th>效应量</th><th>原始 α 结论</th><th>Bonferroni</th>
        </tr>
      </thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>二、通俗解读</h2>
    <ul>
{interpret_blocks}
    </ul>
  </div>

  <div class="card">
    <h2>三、方法注记（小样本 / 多重比较需谨慎）</h2>
    <ul>
      <li><span class="tag">数据</span>来源 <code>chapter_data/all_tags.json</code>，仅做读取分析，未修改任何源文件。战斗强度 <code>combat_intensity</code> 为 0–3 的序数变量，分布非正态，故优先采用非参数方法。</li>
      <li><span class="tag">检验选择</span>组间比较用 <b>Mann-Whitney U</b>（不假设正态与方差齐性）；相关性用 <b>Spearman 秩相关</b>（对单调关系稳健）。</li>
      <li><span class="tag">效应量</span>组间比较报告 <b>Cliff's δ</b>（P&gt;Q 之差，∈[-1,1]）：|δ|&lt;0.147 可忽略、0.147–0.33 小、0.33–0.474 中、≥0.474 大。相关报告 <b>Spearman ρ</b> 本身。</li>
      <li><span class="tag">情感线编码</span>按指令映射：平淡/日常=0、升温/进展=1、虐/悲情=2；其余"无显著感情戏"(9)、"波折/误会"(2)、"分离/离别"(1) 共 12 章视为"未明"排除，相关分析实际 n={n_corr}。</li>
      <li><span class="tag">多重比较</span>共 {n_total} 项检验，若把全部检验当作同一家族，Bonferroni 校正后阈值收紧至 <b>{bonf_text}</b>。任一"显著"项若其 p 仍 ≥ {bonf_text}，应视为在更严格标准下不再显著，需谨慎表述。</li>
      <li><span class="tag">小样本风险</span>任琅未出场仅 {len(data)-54} 章、京城组仅 15 章、情感极端类别样本少，统计功效低；即便某检验不显著，也<b>不能证明"无效应"</b>，只能说"现有证据不足"。</li>
      <li><span class="tag">纪律</span>对所有 p≥0.05 的结果一律写作"不显著，不能拒绝原假设"，不夸大、不编造显著性。</li>
    </ul>
    <div class="warn">⚠️ 本推断基于人工标注的章节级聚合数据，结论仅描述"标注层面的统计关联"，不等同于作者创作意图或文本细读的因果判断。小样本下请结合叙事语境谨慎解读。</div>
  </div>
</div>
</body>
</html>"""

with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"已写入 {HTML_OUT}")

# ---------- 完成打印 ----------
print(f"STATS DONE: tests={len(results)} significant={n_sig}")
