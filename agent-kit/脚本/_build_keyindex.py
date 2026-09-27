# -*- coding: utf-8 -*-
"""
生成《苇舟江湖梦》「关键词 → 原文」索引数据（产物/关键词索引.json）。

关键词来源（即「报告内讨论的关键词」，由分析管线自动提取）：
  - 人物：数据/char_stats.json 中的角色名
  - 地点：数据/spatial_data.json 中的节点名（nodes 字典的 key）

对全书原文（数据/full_text.txt）做全量扫描，计算每个关键词：
  - total        ：在原文中出现的总次数（与阅读页高亮口径一致，按子串计数）
  - chapters     ：实际出现的章数（含序，序记作 ch=0）
  - first        ：首次出现位置 {ch, para}（para 为该章/序内的段落序号，从 0 起）
  - first_label  ：首次出现位置的可读标签（如「序」「第一回」）

仅保留在原文中实际出现（total>=1）的关键词，避免索引出现死链。
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "数据", "full_text.txt")
CHAR = os.path.join(ROOT, "数据", "char_stats.json")
SPAT = os.path.join(ROOT, "数据", "spatial_data.json")
IDX = os.path.join(ROOT, "数据", "chapter_data", "chapters_index.json")
OUT = os.path.join(ROOT, "产物", "关键词索引.json")

CHAP_RE = re.compile(r"^[一二三四五六七八九十百]+、$")
CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
          "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九",
          "二十", "二十一", "二十二", "二十三", "二十四", "二十五", "二十六",
          "二十七", "二十八", "二十九", "三十", "三十一", "三十二", "三十三",
          "三十四", "三十五", "三十六", "三十七", "三十八", "三十九", "四十",
          "四十一", "四十二", "四十三", "四十四", "四十五", "四十六", "四十七",
          "四十八", "四十九", "五十", "五十一", "五十二", "五十三", "五十四",
          "五十五", "五十六", "五十七", "五十八", "五十九"]


def parse_paragraphs(text):
    """源文件以「每物理行 = 一个段落」组织。返回段落纯文本列表（已折叠空白）。"""
    out = []
    for ln in text.split("\n"):
        b = ln.strip()
        if not b:
            continue
        out.append(re.sub(r"\s+", " ", b))
    return out


def load_text():
    text = io.open(SRC, encoding="utf-8").read()
    lines = text.split("\n")
    first = None
    for i, ln in enumerate(lines):
        if CHAP_RE.match(ln.strip()):
            first = i
            break
    if first is None:
        raise RuntimeError("未在 full_text.txt 中找到任何章首标记")
    fore_lines = lines[:first]
    body_lines = lines[first:]
    chapters = []
    marker = None
    buf = []
    for ln in body_lines:
        s = ln.strip()
        if CHAP_RE.match(s):
            if marker is not None:
                chapters.append(buf)
            marker = s
            buf = []
        else:
            buf.append(ln)
    if marker is not None:
        chapters.append(buf)
    return parse_paragraphs("\n".join(fore_lines)), [parse_paragraphs("\n".join(c)) for c in chapters]


def load_entities():
    chars = json.load(io.open(CHAR, encoding="utf-8"))
    spat = json.load(io.open(SPAT, encoding="utf-8"))
    ents = []
    for c in chars:
        n = (c.get("name") or "").strip()
        if n:
            ents.append((n, "人物"))
    for n in spat.get("nodes", {}).keys():
        n = (n or "").strip()
        if n:
            ents.append((n, "地点"))
    # 去重（人物/地点同名时保留先出现的类型，并以集合去重词面）
    seen = {}
    for name, typ in ents:
        if name not in seen:
            seen[name] = typ
    return [(k, v) for k, v in seen.items()]


def ch_label(ch):
    if ch == 0:
        return "序"
    idx = ch - 1
    if 0 <= idx < len(CN_NUM):
        return "第" + CN_NUM[idx] + "回"
    return "第%d回" % ch


def main():
    fore, chapters = load_text()
    total_paras = len(fore) + sum(len(c) for c in chapters)
    entities = load_entities()

    # 预先把全部段落拼成 (ch, para, text) 序列，便于扫描
    seq = []
    for pi, t in enumerate(fore):
        seq.append((0, pi, t))
    for ci, chap in enumerate(chapters):
        ch = ci + 1
        for pi, t in enumerate(chap):
            seq.append((ch, pi, t))

    keywords = []
    for name, typ in entities:
        total = 0
        ch_set = set()
        first = None
        for ch, pi, t in seq:
            c = t.count(name)
            if c:
                total += c
                ch_set.add(ch)
                if first is None:
                    first = {"ch": ch, "para": pi}
        if total == 0:
            continue
        keywords.append({
            "name": name,
            "type": typ,
            "total": total,
            "chapters": len(ch_set),
            "first": first,
            "first_label": ch_label(first["ch"]) if first else "序",
        })

    # 排序：人物在前、地点在后；同类按 total 降序
    type_rank = {"人物": 0, "地点": 1}
    keywords.sort(key=lambda k: (type_rank.get(k["type"], 9), -k["total"]))

    data = {
        "generated": "",
        "source": "char_stats.json + spatial_data.json + full_text.txt",
        "total_paragraphs": total_paras,
        "count": len(keywords),
        "keywords": keywords,
    }
    io.open(OUT, "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=2)
    )
    print("已生成:", OUT)
    print("关键词数:", len(keywords))
    persons = sum(1 for k in keywords if k["type"] == "人物")
    places = sum(1 for k in keywords if k["type"] == "地点")
    print("  人物 %d · 地点 %d" % (persons, places))
    print("扫描段落数:", total_paras)
    emit_widget(data)


WIDGET_JS = r"""
(function(){
  var DATA = __KEYINDEX_DATA__;
  var STYLE_ID='wz-kwindex-style';
  if(!document.getElementById(STYLE_ID)){
    var css=[
      '.wz-kwindex{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:22px 24px;margin:18px 0;box-shadow:var(--shadow-card);}',
      '.wz-kw-title{margin:0 0 6px;font-size:20px;color:var(--primary-d);letter-spacing:2px;}',
      '.wz-kw-sub{margin:0 0 16px;font-size:13px;color:var(--muted);line-height:1.6;}',
      '.wz-kw-tools{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;margin-bottom:14px;}',
      '.wz-kw-search{flex:1 1 200px;min-width:160px;padding:9px 12px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--ink);font:inherit;font-size:14px;}',
      '.wz-kw-search:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px rgba(31,58,95,.12);}',
      '.wz-kw-tabs{display:flex;gap:8px;}',
      '.wz-kw-tabs button{padding:7px 14px;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);border-radius:20px;cursor:pointer;font:inherit;font-size:13px;transition:all .2s;}',
      '.wz-kw-tabs button.active{background:var(--primary);color:#fff;border-color:var(--primary);}',
      '.wz-kw-list{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;}',
      '.wz-kw-item{display:flex;flex-direction:column;gap:4px;padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:var(--surface-2);cursor:pointer;transition:transform .15s,border-color .2s,box-shadow .2s;}',
      '.wz-kw-item:hover{transform:translateY(-2px);border-color:var(--primary);box-shadow:0 6px 16px rgba(31,28,23,.12);}',
      '.wz-kw-item:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px rgba(31,58,95,.15);}',
      '.wz-kw-name{font-size:16px;font-weight:700;color:var(--primary-d);letter-spacing:1px;}',
      '.wz-kw-badge{display:inline-block;align-self:flex-start;font-size:11px;padding:2px 9px;border-radius:10px;margin-top:2px;}',
      '.wz-kw-badge.b-人物{background:rgba(31,58,95,.12);color:var(--primary-d);}',
      '.wz-kw-badge.b-地点{background:rgba(214,160,60,.20);color:#9a6b12;}',
      '.wz-kw-meta{font-size:12px;color:var(--muted);margin-top:2px;}',
      '.wz-kw-none,.wz-kw-empty{padding:18px;text-align:center;color:var(--muted);font-size:14px;grid-column:1/-1;}',
      '@media(max-width:560px){.wz-kw-list{grid-template-columns:1fr;}}'
    ].join('\n');
    var st=document.createElement('style'); st.id=STYLE_ID; st.textContent=css;
    document.head.appendChild(st);
  }
  function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function go(name){
    var url='苇舟江湖梦_原文阅读.html?kw='+encodeURIComponent(name);
    window.open(url,'_blank','noopener');
  }
  function render(root){
    if(!root)return;
    if(!DATA||!DATA.keywords){root.innerHTML='<p class="wz-kw-empty">索引数据未能加载。</p>';return;}
    var kws=DATA.keywords;
    var state={q:'',type:'全部'};
    root.innerHTML=
      '<div class="wz-kwindex">'+
        '<div class="wz-kw-head">'+
          '<h2 class="wz-kw-title">关键词原文索引</h2>'+
          '<p class="wz-kw-sub">点击关键词，跳转至《原文阅读》页并高亮该词在全书中的全部出现位置（共 '+kws.length+' 个关键词）。</p>'+
          '<div class="wz-kw-tools">'+
            '<input class="wz-kw-search" type="search" placeholder="搜索关键词…" aria-label="搜索关键词">'+
            '<div class="wz-kw-tabs">'+
              '<button type="button" data-t="全部" class="active">全部</button>'+
              '<button type="button" data-t="人物">人物</button>'+
              '<button type="button" data-t="地点">地点</button>'+
            '</div>'+
          '</div>'+
        '</div>'+
        '<ul class="wz-kw-list" role="listbox" aria-label="关键词列表"></ul>'+
      '</div>';
    var ul=root.querySelector('.wz-kw-list');
    var search=root.querySelector('.wz-kw-search');
    var tabs=root.querySelectorAll('.wz-kw-tabs button');
    function paint(){
      var q=state.q.trim();
      var list=kws.filter(function(c){
        if(state.type!=='全部'&&c.type!==state.type)return false;
        if(q&&c.name.indexOf(q)===-1)return false;
        return true;
      });
      if(!list.length){ul.innerHTML='<li class="wz-kw-none">未找到匹配的关键词。</li>';return;}
      ul.innerHTML=list.map(function(c){
        return '<li class="wz-kw-item" role="option" tabindex="0" data-name="'+esc(c.name)+'">'+
          '<span class="wz-kw-name">'+esc(c.name)+'</span>'+
          '<span class="wz-kw-badge b-'+esc(c.type)+'">'+esc(c.type)+'</span>'+
          '<span class="wz-kw-meta">命中 '+c.total+' 处 · 涉及 '+c.chapters+' 回 · 首现 '+esc(c.first_label)+'</span>'+
        '</li>';
      }).join('');
    }
    ul.addEventListener('click',function(e){
      var li=e.target.closest('.wz-kw-item'); if(li) go(li.getAttribute('data-name'));
    });
    ul.addEventListener('keydown',function(e){
      if(e.key==='Enter'||e.key===' '){var li=e.target.closest('.wz-kw-item'); if(li){e.preventDefault();go(li.getAttribute('data-name'));}}
    });
    search.addEventListener('input',function(){state.q=search.value;paint();});
    tabs.forEach(function(b){b.addEventListener('click',function(){
      tabs.forEach(function(x){x.classList.remove('active');});
      b.classList.add('active'); state.type=b.getAttribute('data-t'); paint();
    });});
    paint();
  }
  function init(){render(document.getElementById('wz-kwindex'));}
  if(document.readyState!=='loading')init();else document.addEventListener('DOMContentLoaded',init);
})();
"""


def emit_widget(data):
    """生成自包含挂件 产物/keyword-index-widget.js（内嵌索引数据，避免 file:// 下 fetch 受限）。"""
    WIDGET_OUT = os.path.join(ROOT, "产物", "keyword-index-widget.js")
    safe = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    js = WIDGET_JS.replace("__KEYINDEX_DATA__", safe)
    io.open(WIDGET_OUT, "w", encoding="utf-8").write(js)
    print("已生成:", WIDGET_OUT)


if __name__ == "__main__":
    main()
