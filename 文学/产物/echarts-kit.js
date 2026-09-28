/* =====================================================================
 *  echarts-kit.js — 《苇舟江湖梦》统一交互式图表工具库
 *  ---------------------------------------------------------------------
 *  职责：
 *   1. 从 CDN 惰性加载 ECharts 5；
 *   2. 自动读取 theme.css 的设计 Token（--ink/--muted/--line/--primary…）
 *      使图表随「深色模式」(body.dark) 实时换肤；
 *   3. 统一交互能力：悬停 tooltip、dataZoom 缩放、图例筛选、点击回调；
 *   4. 动态能力原语：时间轴播放器（逐帧推进）、实时数据流模拟器
 *      （外部事件触发平滑重绘）。
 *  设计原则：仅动画 transform/opacity 无关项；尊重 prefers-reduced-motion；
 *  所有颜色取自 CSS 变量，保证与现有宣纸/墨蓝/朱砂主题一致。
 * ===================================================================== */
(function (global) {
  "use strict";

  var ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js";
  var instances = [];          // 已创建的图表实例
  var byDom = {};              // domId -> 实例（供外部稳定取用）
  var readyCbs = [];           // ECharts 就绪后的回调队列
  var echartsLoaded = false;

  /* ---------- 1. 加载 ECharts ---------- */
  function loadECharts(cb) {
    if (global.echarts) { echartsLoaded = true; cb(); return; }
    var s = document.createElement("script");
    s.src = ECHARTS_CDN;
    s.onload = function () { echartsLoaded = true; cb(); };
    s.onerror = function () {
      // CDN 不可达：回退到同目录本地 echarts.min.js（离线可用）
      if (!s._fallback) {
        s._fallback = true;
        var s2 = document.createElement("script");
        s2.src = "echarts.min.js";
        s2.onload = function () { echartsLoaded = true; cb(); };
        s2.onerror = function () {
          document.querySelectorAll("[data-wz-chart]").forEach(function (el) {
            el.innerHTML = '<div style="padding:24px;color:#b00;font-size:13px">' +
              '⚠ 图表库加载失败（CDN 不可达 + 本地 echarts.min.js 缺失）。请检查产物/目录。</div>';
          });
        };
        document.head.appendChild(s2);
      }
    };
    document.head.appendChild(s);
  }

  /* ---------- 2. 读取 CSS 设计 Token ---------- */
  function cssVars() {
    var cs = getComputedStyle(document.body);
    var g = function (n, d) {
      var v = cs.getPropertyValue(n);
      return v ? v.trim() : d;
    };
    return {
      bg: g("--bg", "#f4f1ea"),
      surface: g("--surface", "#fffdf8"),
      ink: g("--ink", "#1f1c17"),
      muted: g("--muted", "#6b6353"),
      line: g("--line", "#e3ddcf"),
      lineStrong: g("--line-strong", "#d3cbb8"),
      primary: g("--primary", "#2c5d8a"),
      primaryD: g("--primary-d", "#1f3a5f"),
      accent: g("--accent", "#8a3324"),
      gold: g("--gold", "#b8860b")
    };
  }

  /* ---------- 3. 构建 ECharts 主题对象 ---------- */
  function buildTheme() {
    var v = cssVars();
    return {
      color: [v.primary, v.accent, v.gold, "#3a8f7a", "#7a5fa3"],
      backgroundColor: "transparent",
      textStyle: { color: v.ink, fontFamily: '"HarmonyOS Sans SC","HarmonyOS Sans","PingFang SC","Microsoft YaHei","Noto Sans SC",system-ui,sans-serif' },
      title: { textStyle: { color: v.ink } },
      legend: { textStyle: { color: v.muted } },
      tooltip: {
        backgroundColor: v.surface,
        borderColor: v.lineStrong,
        borderWidth: 1,
        textStyle: { color: v.ink, fontSize: 12 },
        extraCssText: "box-shadow:0 6px 20px rgba(31,28,23,.18);border-radius:8px;"
      },
      categoryAxis: {
        axisLine: { lineStyle: { color: v.lineStrong } },
        axisLabel: { color: v.muted },
        splitLine: { lineStyle: { color: v.line, type: "dashed" } }
      },
      valueAxis: {
        axisLine: { lineStyle: { color: v.lineStrong } },
        axisLabel: { color: v.muted },
        splitLine: { lineStyle: { color: v.line, type: "dashed" } }
      },
      dataZoom: [
        { textStyle: { color: v.muted } }
      ]
    };
  }

  /* ---------- 4. 创建图表（含默认交互） ---------- */
  // 默认开启：悬停 tooltip、dataZoom 缩放、图例筛选
  function defBase() {
    return {
      tooltip: { trigger: "item", confine: true, axisPointer: { type: "cross", label: { backgroundColor: "#888" } } },
      grid: { left: 56, right: 56, top: 48, bottom: 64, containLabel: true },
      dataZoom: [
        { type: "inside", throttle: 50 },
        { type: "slider", height: 18, bottom: 18 }
      ]
    };
  }
  // buildOption(vars) 返回用户 option；var 切换时仅重设 option（不 dispose），
  // 保证外部对实例的引用（时间轴/实时流/点击）始终有效。
  function chart(dom, buildOption, opts) {
    opts = opts || {};
    var inst = global.echarts.init(dom, buildTheme(), { renderer: "canvas" });
    function apply(vars) {
      var merged = deepMerge(defBase(), buildOption(vars));
      inst.setOption(merged, true);
    }
    apply(cssVars());
    inst._apply = apply;
    inst._opts = opts;
    instances.push(inst);
    byDom[dom.id || dom] = inst;

    // 点击回调
    if (typeof opts.onClick === "function") {
      inst.on("click", function (params) { opts.onClick(params, inst); });
    }
    // 响应式
    var ro = function () { try { inst.resize(); } catch (e) {} };
    if (global.ResizeObserver) { new ResizeObserver(ro).observe(dom); }
    else { global.addEventListener("resize", ro); }
    return inst;
  }

  /* ---------- 5. 主题热更新（深色模式联动，原位重绘不销毁实例） ---------- */
  function reskinAll() {
    instances.forEach(function (inst) {
      try { inst._apply(cssVars()); } catch (e) {}
    });
  }

  function watchTheme() {
    // 监听 body class 变化（本地切换按钮）
    if (global.MutationObserver) {
      var mo = new MutationObserver(function () { reskinAll(); });
      mo.observe(document.body, { attributes: true, attributeFilter: ["class"] });
    }
    // 监听外壳 postMessage（iframe 场景）
    global.addEventListener("message", function (e) {
      if (e.data && e.data.wzTheme) { setTimeout(reskinAll, 30); }
    });
  }

  /* ---------- 6. 时间轴播放器 ---------- */
  // 用法：WZ.timelinePlayer(chart, {max:n, onFrame:t=>{...}, step:200})
  // 返回控制器 { play, pause, toggle, seek, setProgress }
  function timelinePlayer(chart, cfg) {
    cfg = cfg || {};
    var max = cfg.max || 59;
    var step = cfg.step || 220;
    var onFrame = cfg.onFrame || function () {};
    var timer = null, t = 0, playing = false;
    var reduce = global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function frame() {
      onFrame(t);
      if (t >= max) { pause(); return; }
    }
    function tick() {
      t = Math.min(max, t + (cfg.stride || 1));
      frame();
      if (t >= max) pause();
    }
    function play() {
      if (playing) return;
      if (t >= max) t = 0;
      playing = true;
      if (reduce) { t = max; onFrame(t); pause(); return; }
      timer = setInterval(tick, step);
    }
    function pause() {
      playing = false;
      if (timer) { clearInterval(timer); timer = null; }
    }
    function toggle() { playing ? pause() : play(); }
    function seek(v) { t = Math.max(0, Math.min(max, v | 0)); onFrame(t); }
    function setProgress(fn) { /* 进度回调钩子，由调用方绑定 UI */ }
    return { play: play, pause: pause, toggle: toggle, seek: seek, get t() { return t; }, get max() { return max; }, isPlaying: function () { return playing; } };
  }

  /* ---------- 7. 实时数据流模拟器 ---------- */
  // 用法：WZ.liveStream({ interval:1200, onTick:()=>{ chart.setOption({...}, {lazyUpdate:true}) } })
  function liveStream(cfg) {
    cfg = cfg || {};
    var interval = cfg.interval || 1200;
    var onTick = cfg.onTick || function () {};
    var onState = cfg.onState || function () {};
    var timer = null, on = false;
    var reduce = global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function start() {
      if (on) return; on = true; onState(true);
      if (reduce) { onTick(); return; }   // 减弱动效时仅刷新一次
      timer = setInterval(function () { onTick(); }, interval);
    }
    function stop() { on = false; if (timer) { clearInterval(timer); timer = null; } onState(false); }
    function toggle() { on ? stop() : start(); }
    return { start: start, stop: stop, toggle: toggle, isOn: function () { return on; } };
  }

  /* ---------- 工具：深合并 ---------- */
  function deepMerge(a, b) {
    var out = {};
    Object.keys(a).forEach(function (k) { out[k] = a[k]; });
    Object.keys(b || {}).forEach(function (k) {
      if (b[k] && typeof b[k] === "object" && !Array.isArray(b[k]) &&
          a[k] && typeof a[k] === "object" && !Array.isArray(a[k])) {
        out[k] = deepMerge(a[k], b[k]);
      } else {
        out[k] = b[k];
      }
    });
    return out;
  }

  /* ---------- 8. 注入图表控制条样式（随主题 Token 自动换肤） ---------- */
  function injectStyles() {
    if (document.getElementById("wz-kit-style")) return;
    var css = [
      ".wz-chart-card{padding:20px 22px}",
      ".wz-controls{display:flex;flex-wrap:wrap;gap:14px;justify-content:space-between;align-items:center;margin-bottom:14px}",
      ".wz-ctrl-group{display:flex;align-items:center;gap:10px;flex-wrap:wrap}",
      ".wz-btn{font-family:inherit;font-size:12.5px;font-weight:600;padding:7px 14px;border-radius:9px;cursor:pointer;",
      "border:1px solid var(--line-strong,var(--line,#e3ddcf));background:var(--surface,#fffdf8);color:var(--primary-d,var(--primary,#1f3a5f));",
      "transition:background .16s,color .16s,border-color .16s,transform .12s;display:inline-flex;align-items:center;gap:6px}",
      ".wz-btn:hover{transform:translateY(-1px);border-color:var(--primary,#2c5d8a)}",
      ".wz-btn:active{transform:translateY(0)}",
      ".wz-btn.active{background:var(--primary,#2c5d8a);border-color:var(--primary,#2c5d8a);color:#fff}",
      ".wz-btn.active.wz-live{background:var(--accent,#8a3324);border-color:var(--accent,#8a3324)}",
      ".wz-seek{flex:1;min-width:160px;accent-color:var(--primary,#2c5d8a);cursor:pointer}",
      ".wz-frame{font-size:12.5px;color:var(--muted,#6b6353);white-space:nowrap;min-width:96px;text-align:right}",
      ".wz-detail{margin-top:14px;padding:14px 16px;border:1px solid var(--line,#e3ddcf);border-radius:10px;",
      "background:var(--surface,#fffdf8);font-size:13px;color:var(--ink,#1f1c17);line-height:1.75}",
      ".wz-detail[hidden]{display:none}",
      ".wz-detail b{color:var(--primary-d,var(--primary,#1f3a5f))}",
      ".wz-dot{width:9px;height:9px;border-radius:50%;background:var(--line-strong,#d3cbb8);transition:background .3s}",
      ".wz-dot.live{background:var(--accent,#8a3324);animation:wz-pulse 1.4s infinite}",
      "@keyframes wz-pulse{0%{box-shadow:0 0 0 0 rgba(138,51,36,.5)}70%{box-shadow:0 0 0 9px rgba(138,51,36,0)}100%{box-shadow:0 0 0 0 rgba(138,51,36,0)}}",
      ".wz-hint{font-size:11.5px;color:var(--muted,#6b6353);margin-top:8px}"
    ].join("");
    var s = document.createElement("style");
    s.id = "wz-kit-style";
    s.textContent = css;
    document.head.appendChild(s);
  }
  injectStyles();

  /* ---------- 对外暴露 ---------- */
  global.WZ = {
    ready: function (cb) {
      if (echartsLoaded) cb();
      else { readyCbs.push(cb); loadECharts(function () { readyCbs.forEach(function (f) { f(); }); }); }
    },
    cssVars: cssVars,
    buildTheme: buildTheme,
    chart: chart,
    reskinAll: reskinAll,
    timelinePlayer: timelinePlayer,
    liveStream: liveStream,
    getInstance: function (id) { return byDom[id]; }
  };

  // 装载后立即启动主题监听
  loadECharts(function () { watchTheme(); });
})(window);
