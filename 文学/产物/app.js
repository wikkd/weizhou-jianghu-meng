/* 苇舟江湖梦 · 统一报告展示平台
 * 纯原生 JS，无构建依赖。报告通过 iframe 内联加载，保留各自的 theme.css 渲染。
 * v2：主区分类筛选 pills、iframe 骨架屏、抽屉焦点管理与 ESC、卡片键盘可达。
 */
(function () {
  "use strict";

  // ---- 分类定义（顺序即筛选条顺序）----
  const CATEGORIES = [
    { key: "overview",   label: "总体概览", icon: "◎" },
    { key: "characters", label: "人物维度", icon: "♟" },
    { key: "chapter",    label: "章节标注", icon: "❖" },
    { key: "geospace",   label: "时空地理", icon: "✷" },
    { key: "linguistics",label: "语言计量", icon: "✎" },
    { key: "research",   label: "考据专题", icon: "❍" },
    { key: "narrative",  label: "叙事可视化", icon: "✦" },
    { key: "tools",      label: "工具与入口", icon: "⌘" },
  ];

  // ---- 报告清单（src 相对 index.html 所在目录）----
  const REPORTS = [
    { id: "analysis", file: "苇舟江湖梦_分析报告.html", category: "overview",
      title: "全文本量化分析报告",
      desc: "184,624 字 / 59 章的自动抽取：人物识别与共现网络、时间轴与历史回溯、空间谱系、七幕故事线与感情线，含 7 张图表。",
      tags: ["人物", "时间", "地点", "故事线", "关系网"] },
    { id: "archive", file: "数据归档/苇舟江湖梦_数据归档总览.html", category: "overview",
      title: "数据归档总览（索引数据库）",
      desc: "统一归档全部信息：资产清单、59 章标签、106 人物、32 地点。配套 SQLite 数据库可 SQL 查询。",
      tags: ["归档", "SQLite", "全量索引"] },
    { id: "organize", file: "苇舟江湖梦_报告归纳整理.html", category: "overview",
      title: "报告归纳整理（盘点方案）",
      desc: "25 份报告 × 3 入口 × 6 重复组的只读盘点：主题分组 / 重复组分析 / L1清理-L4保持 动作清单。",
      tags: ["治理", "重复识别", "入口收敛", "归纳"] },
    { id: "network", file: "03_人物社会/苇舟江湖梦_人物关系网络.html", category: "characters",
      title: "人物关系网络",
      desc: "59 章人物共现网络：degree / PageRank / 社区划分，spring_layout 可视化。101 节点 / 1318 边 / 4 社区。",
      tags: ["共现网络", "PageRank", "社区划分"] },
    { id: "derived", file: "02_叙事情感/苇舟江湖梦_派生维度量化.html", category: "characters",
      title: "出场·提及背离与人物-地点共现",
      desc: "49 角色出场 vs 提及背离，识别「在场却不在场」的幕后人物；逐章人物-地点共现热力图，与关系网正交互补。",
      tags: ["出场-提及", "人物-地点", "热力图"] },
    { id: "tags", file: "02_叙事情感/苇舟江湖梦_章节标签量化看板.html", category: "chapter",
      title: "章节标签量化看板",
      desc: "59 章受控词表标注的结构化看板：章节类型 / 时间层 / 感情线分布、情节演进、地点与人物出场热度。",
      tags: ["受控词表", "情节演进", "热度"] },
    { id: "structure", file: "02_叙事情感/苇舟江湖梦_章节结构量化.html", category: "chapter",
      title: "章节结构深度量化",
      desc: "补完既往未消费维度：故事线 / 叙事视角分布、自由标签主题漂移、感情线 × 算法情感交叉验证。",
      tags: ["故事线", "视角", "感情线交叉"] },
    { id: "spatial", file: "04_空间地理/苇舟江湖梦_空间地点分析报告.html", category: "geospace",
      title: "空间地点分析报告",
      desc: "结合文档内嵌参考图坐标，叠加旅行时间 / 地形 / 战术，建立相对坐标系与距离矩阵、地形分类及战争阶段战术研判。",
      tags: ["地理拓扑", "距离矩阵", "战术地理"] },
    { id: "geo", file: "04_空间地理/苇舟江湖梦_地理位置关系图.html", category: "geospace",
      title: "地理位置关系图（纯文本派生）",
      desc: "仅依据正文方位词、里程 / 旅行时间、地形水文，以加权最小二乘求解相对坐标；含 SVG 地图与方位证据表。",
      tags: ["方位约束", "最小二乘", "SVG地图"] },
    { id: "timerhythm", file: "02_叙事情感/苇舟江湖梦_时间节奏量化.html", category: "geospace",
      title: "时间节奏量化",
      desc: "季节 / 昼夜 / 相对时间密度聚合 + 地名清洗。昼夜叙事占比 63%，季节分布附字形干扰 caveat。",
      tags: ["季节", "昼夜", "相对时间"] },
    { id: "style", file: "01_文本语言/苇舟江湖梦_风格计量.html", category: "linguistics",
      title: "文体指纹与节奏",
      desc: "59 章文体指纹：平均句长、标点密度、对话占比。决战章对话骤降、叙述加快；全本平均对话占比约 35.6%。",
      tags: ["句长", "对话占比", "节奏"] },
    { id: "lexical", file: "01_文本语言/苇舟江湖梦_词汇计量.html", category: "linguistics",
      title: "词汇与用词漂移",
      desc: "全本词频 Top50、分章类符 / 形符比 (TTR≈0.687)、前后段用语漂移：市井 → 庙堂迁移清晰。",
      tags: ["词频", "TTR", "语义迁移"] },
    { id: "sentiment", file: "02_叙事情感/苇舟江湖梦_情感时序.html", category: "linguistics",
      title: "情感时序曲线",
      desc: "59 章逐章情感极性与战斗强度对照；均值 0.585，与战斗强度 r≈−0.475 显著负相关。",
      tags: ["情感极性", "战斗强度", "相关"] },
    { id: "stats", file: "03_人物社会/苇舟江湖梦_统计推断.html", category: "linguistics",
      title: "叙事假设统计检验",
      desc: "5 项叙事假设非参检验：任琅出场、章节含「战斗」与战斗强度显著正相关；部分小样本已做 Bonferroni 提示。",
      tags: ["非参检验", "假设验证", "校正"] },
    { id: "official", file: "05_制度家族/苇舟江湖梦_官制考究.html", category: "research",
      title: "官制考究",
      desc: "抽取正文职官 / 建制术语，与秦—清历代官制比对：判定两汉郡县—将相制为体、兼采唐以来科举与县制的架空仿古官制。",
      tags: ["职官术语", "历代比对", "朝代判定"] },
    { id: "capital", file: "05_制度家族/川阴王建都推演.html", category: "research",
      title: "川阴王建都推演",
      desc: "大战结束后川阴王建都最佳地点推演：以京城为正式都城，南岭关·卫京郡为北盾、川阴为西南陪都、海郡为东方财枢。",
      tags: ["模拟推理", "战后建都", "地缘"] },
    { id: "traits", file: "03_人物社会/苇舟江湖梦_角色性格量化.html", category: "characters",
      title: "角色性格量化",
      desc: "六轴受控词表（性情/品性/心气/情义/智愚/胆气）自动抽取 49 角色性格档案，附原文证据片段，可人审。",
      tags: ["性格档案", "六轴", "证据"] },
    { id: "catch", file: "03_人物社会/苇舟江湖梦_口头禅量化.html", category: "linguistics",
      title: "口头禅与标志语量化",
      desc: "对话归属 + 复现识别：抽取各角色标志语与特征 n-gram（如陈奉天「本王」、尚樱「一百两」、夏叶「任哥」）。",
      tags: ["口头禅", "标志语", "n-gram"] },
    { id: "combat", file: "03_人物社会/苇舟江湖梦_对打动作量化.html", category: "chapter",
      title: "精彩对打动作量化",
      desc: "六类动作词表（兵器/身法/内力/招式/防守/伤效）抽取战斗章动作分布与招式组合序列，含兵器功法。",
      tags: ["对打动作", "招式序列", "兵器"] },
    { id: "geodesc", file: "04_空间地理/苇舟江湖梦_地理描述量化.html", category: "geospace",
      title: "地点地理描述量化",
      desc: "对 54 个地点归类地形类型、聚合 17 项地理要素、抽样描述句；叙事相对坐标地图可按地形着色并跳原文。",
      tags: ["地形归类", "地理要素", "描述抽样"] },
    { id: "huangjia", file: "05_制度家族/黄家概况.html", category: "research",
      title: "黄氏家族概况",
      desc: "黄氏家族谱系分析：家主 / 成员 / 势力地缘 / 恩怨脉络 / 命运走向 / 叙事功能，数据源 full_text + 章节标注。",
      tags: ["家族谱系", "势力", "地缘", "黄亚钊"] },
    { id: "narrative", file: "02_叙事情感/苇舟江湖梦_可视化叙事系统.html", category: "narrative",
      title: "可视化叙事系统（四维流程图）",
      desc: "剧情/情感/空间/时间 四维状态转移流程图 + 9 章 Nexus 立体交叉引用。点击节点跨图联动高亮，◎ 立体定位四图同步锚定。",
      tags: ["Mermaid", "四维", "Nexus", "立体交叉"] },
    { id: "narrativeExt", file: "02_叙事情感/苇舟江湖梦_扩展叙事可视化.html", category: "narrative",
      title: "扩展叙事可视化",
      desc: "因果事件链 / 叙事节奏谱 / 角色六维雷达+性格谱系 / 角色登场矩阵热力图，因果链回溯 full_text 原文抽取真实连词。",
      tags: ["因果链", "心电图", "雷达", "热力图"] },
    { id: "narrativeDeep", file: "02_叙事情感/苇舟江湖梦_深度叙事可视化.html", category: "narrative",
      title: "深度叙事可视化",
      desc: "伏笔—回收网络（46 推断边 + 8 例句）/ 时空动画地图（scatter+timeline 逐章迁移）/ 文风漂移流图 / 知识图谱+MOC。",
      tags: ["伏笔", "时空动画", "文风漂移", "知识图谱"] },
    { id: "library", file: "library.html", category: "tools", external: true,
      title: "数字图书馆",
      desc: "全本原文典藏外壳：侧栏目录 + 章节快检 + 报告联动查看，支持主题跟随。",
      tags: ["入口", "原文", "典藏"] },
    { id: "kwindex", file: "苇舟江湖梦_关键词索引.html", category: "tools",
      title: "关键词索引",
      desc: "关键词 → 原文章节跳转对照索引，检索定位原文利器。",
      tags: ["入口", "检索", "对照"] },
    { id: "components", file: "苇舟江湖梦_组件库.html", category: "tools",
      title: "液态玻璃组件典",
      desc: "站点设计系统组件一览：玻璃卡片 / 胶囊按钮 / 图表骨架，统一视觉语言。",
      tags: ["入口", "设计系统", "组件"] },
    { id: "aesthetics", file: "美学图谱.html", category: "tools",
      title: "美学图谱",
      desc: "小说视觉美学体系：配色 / 意象 / 版式基因的可视化图谱。",
      tags: ["入口", "美学", "视觉"] },
  ];

  // ---- 运行时状态 ----
  const state = { category: "all", query: "", current: null };

  // ---- DOM 引用 ----
  const $ = (s) => document.querySelector(s);
  const sidebarEl = $("#rc-sidebar");
  const gridEl = $("#rc-grid");
  const listEl = $("#rc-list");
  const filterEl = $("#rc-filterbar");
  const searchEl = $("#rc-search");
  const browseEl = $("#rc-browse");
  const viewerEl = $("#rc-viewer");
  const frameEl = $("#rc-frame");
  const skelEl = $("#rc-skel");
  const crumbEl = $("#rc-crumb");
  const countEl = $("#rc-count");
  const menuBtn = $("#rc-menu");
  const backdropEl = $("#rc-backdrop");
  const mainEl = $("#rc-main");

  const catLabel = (k) => (CATEGORIES.find((c) => c.key === k) || {}).label || k;
  const catCount = (k) => (k === "all" ? REPORTS.length : REPORTS.filter((r) => r.category === k).length);

  // 过滤条件（分类 + 搜索）
  function filterReports() {
    const q = state.query.trim().toLowerCase();
    return REPORTS.filter(
      (r) =>
        (state.category === "all" || r.category === state.category) &&
        (!q ||
          r.title.toLowerCase().includes(q) ||
          r.desc.toLowerCase().includes(q) ||
          r.tags.join(" ").toLowerCase().includes(q))
    );
  }

  // ---- 主区分类筛选 pills（始终可见，含移动端）----
  function renderFilter() {
    const frag = document.createDocumentFragment();
    const mk = (key, label, n) => {
      const b = document.createElement("button");
      b.className = "rc-pill" + (state.category === key ? " active" : "");
      b.dataset.cat = key;
      b.setAttribute("aria-pressed", state.category === key ? "true" : "false");
      b.innerHTML = `<span>${label}</span><span class="rc-pill-n">${n}</span>`;
      b.addEventListener("click", () => setCategory(key));
      return b;
    };
    frag.appendChild(mk("all", "全部报告", REPORTS.length));
    CATEGORIES.forEach((c) => frag.appendChild(mk(c.key, c.label, catCount(c.key))));
    filterEl.innerHTML = "";
    filterEl.appendChild(frag);
  }

  // ---- 侧栏报告列表（按分类分组跳转，受筛选影响）----
  function renderList() {
    const items = filterReports();
    const frag = document.createDocumentFragment();
    let lastCat = null;
    items.forEach((r) => {
      if (r.category !== lastCat) {
        const h = document.createElement("div");
        h.className = "rc-list-cat";
        h.textContent = catLabel(r.category);
        frag.appendChild(h);
        lastCat = r.category;
      }
      const a = document.createElement("button");
      a.className = "rc-list-item" + (state.current === r.id ? " active" : "");
      a.dataset.id = r.id;
      a.setAttribute("aria-current", state.current === r.id ? "true" : "false");
      a.innerHTML = `<span class="rc-li-dot"></span><span class="rc-li-t">${r.title}</span>`;
      a.addEventListener("click", () => openReport(r.id));
      frag.appendChild(a);
    });
    if (!items.length) {
      const e = document.createElement("div");
      e.className = "rc-list-empty";
      e.textContent = "没有匹配的报告";
      frag.appendChild(e);
    }
    listEl.innerHTML = "";
    listEl.appendChild(frag);
  }

  // ---- 总览网格（卡片可筛选）----
  function renderGrid() {
    const items = filterReports();
    const frag = document.createDocumentFragment();
    items.forEach((r, i) => {
      const card = document.createElement("article");
      card.className = "rc-card";
      card.style.animationDelay = i * 35 + "ms";
      card.tabIndex = 0;
      card.setAttribute("role", "button");
      card.setAttribute("aria-label", "查看报告：" + r.title);
      const tags = r.tags.map((t) => `<span class="rc-badge">${t}</span>`).join("");
      card.innerHTML = `
        <div class="rc-card-head">
          <span class="rc-card-cat">${catLabel(r.category)}</span>
          <span class="rc-card-open" aria-hidden="true">↗</span>
        </div>
        <h3 class="rc-card-title">${r.title}</h3>
        <p class="rc-card-desc">${r.desc}</p>
        <div class="rc-card-tags">${tags}</div>
        <button class="rc-card-btn" type="button" data-id="${r.id}">查看报告</button>`;
      const go = () => openReport(r.id);
      card.querySelector(".rc-card-btn").addEventListener("click", (e) => {
        e.stopPropagation();
        go();
      });
      card.addEventListener("click", go);
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          go();
        }
      });
      frag.appendChild(card);
    });
    if (!items.length) {
      const e = document.createElement("div");
      e.className = "rc-grid-empty";
      e.textContent = "没有匹配「" + state.query + "」的报告，试试其他关键词。";
      frag.appendChild(e);
    }
    gridEl.innerHTML = "";
    gridEl.appendChild(frag);
    countEl.textContent = `共 ${items.length} 份报告`;
  }

  // ---- 打开报告（iframe 查看器 + 骨架屏）----
  function openReport(id) {
    const r = REPORTS.find((x) => x.id === id);
    if (!r) return;
    if (r.external) { location.href = r.file; return; }  // 外壳型页面整页打开，避免 iframe 套壳
    state.current = id;
    skelEl.classList.add("show");
    frameEl.onload = () => skelEl.classList.remove("show");
    frameEl.onerror = () => skelEl.classList.remove("show");
    frameEl.src = r.file;
    crumbEl.innerHTML =
      `<a href="#" data-home="1">总览</a><span class="rc-sep">/</span>` +
      `<span>${catLabel(r.category)}</span><span class="rc-sep">/</span>` +
      `<span class="rc-crumb-cur">${r.title}</span>`;
    crumbEl.querySelector("[data-home]").addEventListener("click", (e) => {
      e.preventDefault();
      showBrowse();
    });
    $("#rc-open-new").href = r.file;
    browseEl.classList.remove("active");
    viewerEl.classList.add("active");
    mainEl.classList.add("rc-viewing");
    renderList();
    closeDrawer();
  }

  function showBrowse() {
    state.current = null;
    skelEl.classList.remove("show");
    viewerEl.classList.remove("active");
    browseEl.classList.add("active");
    mainEl.classList.remove("rc-viewing");
    renderGrid();
    renderList();
  }

  function setCategory(key) {
    state.category = key;
    renderFilter();
    renderGrid();
    renderList();
    if (viewerEl.classList.contains("active")) showBrowse();
  }

  // ---- 移动端抽屉 ----
  function openDrawer() {
    sidebarEl.classList.add("open");
    backdropEl.classList.add("show");
    menuBtn.setAttribute("aria-expanded", "true");
    const first = sidebarEl.querySelector(".rc-search");
    if (first) first.focus();
  }
  function closeDrawer() {
    if (!sidebarEl.classList.contains("open")) return;
    sidebarEl.classList.remove("open");
    backdropEl.classList.remove("show");
    menuBtn.setAttribute("aria-expanded", "false");
    menuBtn.focus();
  }

  // ---- 事件绑定 ----
  let searchTimer = null;
  searchEl.addEventListener("input", (e) => {
    state.query = e.target.value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      renderGrid();
      renderList();
    }, 120);
  });
  menuBtn.addEventListener("click", () => {
    if (sidebarEl.classList.contains("open")) closeDrawer();
    else openDrawer();
  });
  backdropEl.addEventListener("click", closeDrawer);
  $("#rc-tobrowse").addEventListener("click", showBrowse);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
  });

  // ---- 初始化 ----
  $("#rc-foot-n").textContent = REPORTS.length;
  $("#rc-foot-c").textContent = CATEGORIES.length;
  renderFilter();
  showBrowse();
})();
