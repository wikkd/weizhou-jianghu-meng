#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成诗图对照画廊 poem_gallery.html（零依赖，引用同目录 PNG）。"""
import json, os, shutil

OUTDIR = os.path.dirname(os.path.abspath(__file__))
POEMDIR = os.path.join(OUTDIR, "poems")

POEMS = [
 {"id":1,"file":"poem01_shangying_rongmao.png","char":"尚樱","chapter":"十八、",
  "type":"夏叶打油诗·赠嫂子","note":"夏叶初见尚樱所作的容貌赞",
  "text":"声若弦簧唇赤丹，目似平波颜带欢，\n溟池未竟心澄澈，一肌一态极尽妍。"},
 {"id":2,"file":"poem02_qinghua_fuzhi.png","char":"任琅 · 尚樱","chapter":"十一、",
  "type":"情花节·福纸愿","note":"二人各自写在祈福红纸上的心愿",
  "text":"尚樱：如果可以，希望任琅能永遠和尚樱一起\n任琅：祝尚樱平平安安、好運連連"},
 {"id":3,"file":"poem03_renlang_huzi.png","char":"任琅（疑）","chapter":"四十二、",
  "type":"题画诗","note":"画中“护子”者，疑似任琅父辈，待考",
  "text":"张灯成宴度佳节，高墙月明照影孑，\n以身护子不求报，乡土家父实豪杰。"},
 {"id":4,"file":"poem04_liuyuanling_libie.png","char":"刘媛灵","chapter":"一、",
  "type":"临别口占","note":"被迫回屋、对离别少年的怅惘",
  "text":"此去一别经世年，心中遗憾再难填。\n他日相逢各为主，未相识来不相看。"},
 {"id":5,"file":"poem05_xiaye_yeyu.png","char":"夏叶","chapter":"三十五、",
  "type":"词（题草纸）","note":"夏叶所作，尚樱于王芣房中读出",
  "text":"窗外小楼隔夜雨，暗问庭树默不语。\n愁思满芳膺，点点至天明。\n身闲心久病，无需镜妆定，\n望残花伶仃，雨蒙远山亭。"},
 {"id":6,"file":"poem06_chenfengtian_yaodao.png","char":"陈奉天 / 梨阳王一脉","chapter":"二十八、",
  "type":"神像飘字条·五言","note":"咏梨阳王→川阴王一脉与妖刀",
  "text":"梨阳川阴替，长生迷心计，\n纷乱三十载，妖刀终伤己。"},
 {"id":7,"file":"poem07_shangying_lianlisong.png","char":"尚樱身世（疑）","chapter":"二十八、",
  "type":"题画诗","note":"画中绝美女子与尚樱一模一样",
  "text":"朝观婴孩木边戏，夕思己小不与同，\n天道有常善相报，幸得相成连理松。"},
 {"id":8,"file":"poem08_qinglou_beiju.png","char":"青楼/琴笛女子（待考，疑苏雨）","chapter":"二十五、",
  "type":"题画·七言律","note":"范豪所展画卷上的盛装美女判词",
  "text":"柔情皎身离青楼，事态相违只得愁，\n应执花烛伴暑木，却得尸骨喂野鸥，\n文闺怎奈刀剑寒，抚琴终难存笑颜，\n三尺白绫东拗树，燕舞画笛难再演。"},
 {"id":9,"file":"poem09_nvzhai_qingdeng.png","char":"女斋主/守青灯者（待考）","chapter":"四十九、",
  "type":"题画·七言律","note":"古观素袍女子独守青灯、念救身恩",
  "text":"曾时林间猎弓惊，幸而遇得帝同情，\n虽从恶人心犹善，山石与命不同行，\n朗月撒辉星辰稀，殿外桃花正得形，\n久念昔日救身恩，独守青灯使长明。"},
]

# write poems.json
with open(os.path.join(OUTDIR, "poems.json"), "w", encoding="utf-8") as f:
    json.dump(POEMS, f, ensure_ascii=False, indent=2)

cards = []
for p in POEMS:
    cards.append(f"""
    <div class="card">
      <div class="img"><img src="{p['file']}" alt="{p['char']}" loading="lazy"></div>
      <div class="meta">
        <div class="ch">{p['char']} <span class="tag">{p['chapter']}</span> <span class="tag">{p['type']}</span></div>
        <div class="poem">{p['text']}</div>
        <div class="note">注：{p['note']}</div>
      </div>
    </div>""")

HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>苇舟江湖梦 · 角色诗图对照</title>
<style>
:root{--bg:#f5f8fc;--panel:#fff;--ink:#1f2a37;--muted:#6b7a90;--line:#e2e9f3;--blue:#2f6fed;--blue2:#e8f0fe;--accent:#0f9d8b}
*{box-sizing:border-box}
body{margin:0;font-family:"Noto Sans CJK SC","Microsoft YaHei",system-ui,sans-serif;background:var(--bg);color:var(--ink)}
header{background:linear-gradient(120deg,#2f6fed,#0f9d8b);color:#fff;padding:18px 24px}
header h1{margin:0;font-size:20px}header .sub{opacity:.9;font-size:12px;margin-top:2px}
.wrap{max-width:1180px;margin:0 auto;padding:18px 20px 60px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}
@media(max-width:760px){.grid{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(31,42,55,.08),0 6px 20px rgba(31,42,55,.06)}
.img{background:#0c1320;display:flex;justify-content:center}
.img img{width:100%;max-height:520px;object-fit:contain;display:block}
.meta{padding:14px 16px}
.ch{font-weight:800;font-size:15px;margin-bottom:8px}
.tag{display:inline-block;padding:1px 8px;border-radius:6px;font-size:11px;background:var(--blue2);color:var(--blue);margin-left:4px;font-weight:600}
.poem{white-space:pre-line;line-height:1.9;font-size:14px;color:var(--ink);font-family:"Noto Serif CJK SC","Songti SC",serif}
.note{margin-top:8px;font-size:12px;color:var(--muted)}
a.back{display:inline-block;margin:6px 0 14px;color:var(--blue);text-decoration:none;font-weight:600}
</style></head><body>
<header><h1>苇舟江湖梦 · 角色诗图对照</h1>
<div class="sub">9 首题画诗/口占/福纸愿 × Qwen-Image-2.1 生图 ｜ 含 4 处待考归属</div></header>
<div class="wrap">
<a class="back" href="../index.html">← 返回主页</a>
<div class="grid">__CARDS__</div>
</div></body></html>"""

html = HTML.replace("__CARDS__", "\n".join(cards))
with open(os.path.join(POEMDIR, "poem_gallery.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("gallery + poems.json written; poems:", len(POEMS))
