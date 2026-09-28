/* =====================================================================
 *  Glass · JS（交互库：涟漪 / 标签 / 分段 / 手风琴 / 模态 / 抽屉 / 吐司 / 进度 / 主题）
 *  零依赖。统一动效与无障碍（focus/aria/reduced-motion 由 CSS 处理）。
 * ===================================================================== */
(function () {
  'use strict';
  var Glass = (window.Glass = window.Glass || {});
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 涟漪反馈（.btn / .icon-btn）---------- */
  function spawnRipple(el, x, y) {
    if (reduced) return;
    var rect = el.getBoundingClientRect();
    var size = Math.max(rect.width, rect.height);
    var span = document.createElement('span');
    span.className = 'ripple';
    span.style.width = span.style.height = size + 'px';
    span.style.left = (x - rect.left - size / 2) + 'px';
    span.style.top = (y - rect.top - size / 2) + 'px';
    el.appendChild(span);
    setTimeout(function () { span.remove(); }, 620);
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.btn, .icon-btn');
    if (b && !b.disabled) spawnRipple(b, e.clientX, e.clientY);
  }, true);

  /* ---------- 标签页（滑动指示）---------- */
  Glass.initTabs = function (root) {
    var tabs = (root || document).querySelectorAll('.tabs');
    Array.prototype.forEach.call(tabs, function (t) {
      var ind = t.querySelector('.tabs__indicator');
      var tabEls = t.querySelectorAll('.tabs__tab');
      var panels = t.querySelectorAll('.tabs__panel');
      function move(el) {
        if (!ind || !el) return;
        ind.style.width = el.offsetWidth + 'px';
        ind.style.transform = 'translateX(' + el.offsetLeft + 'px)';
      }
      Array.prototype.forEach.call(tabEls, function (tab, i) {
        tab.addEventListener('click', function () {
          Array.prototype.forEach.call(tabEls, function (x) {
            x.classList.remove('is-active'); x.setAttribute('aria-selected', 'false');
          });
          tab.classList.add('is-active'); tab.setAttribute('aria-selected', 'true');
          Array.prototype.forEach.call(panels, function (p) { p.classList.remove('is-active'); });
          if (panels[i]) panels[i].classList.add('is-active');
          move(tab);
        });
      });
      var active = t.querySelector('.tabs__tab.is-active') || tabEls[0];
      if (active) {
        active.classList.add('is-active');
        if (panels[0]) panels[0].classList.add('is-active');
        requestAnimationFrame(function () { move(active); });
      }
      window.addEventListener('resize', function () { move(t.querySelector('.tabs__tab.is-active')); });
    });
  };

  /* ---------- 分段控件（滑动滑块）---------- */
  Glass.initSegmented = function (root) {
    var segs = (root || document).querySelectorAll('.segmented');
    Array.prototype.forEach.call(segs, function (s) {
      var items = s.querySelectorAll('.segmented__item');
      var thumb = s.querySelector('.segmented__thumb');
      function move(el) {
        if (!thumb || !el) return;
        thumb.style.width = el.offsetWidth + 'px';
        thumb.style.transform = 'translateX(' + (el.offsetLeft - 4) + 'px)';
      }
      Array.prototype.forEach.call(items, function (it) {
        it.addEventListener('click', function () {
          Array.prototype.forEach.call(items, function (x) { x.classList.remove('is-active'); });
          it.classList.add('is-active');
          move(it);
          s.dispatchEvent(new CustomEvent('segmented:change', {
            detail: { value: it.dataset.value || it.textContent, btn: it }
          }));
        });
      });
      var active = s.querySelector('.segmented__item.is-active') || items[0];
      if (active) { active.classList.add('is-active'); requestAnimationFrame(function () { move(active); }); }
      window.addEventListener('resize', function () { move(s.querySelector('.segmented__item.is-active')); });
    });
  };

  /* ---------- 手风琴 ---------- */
  Glass.initAccordion = function (root) {
    var accs = (root || document).querySelectorAll('.accordion');
    Array.prototype.forEach.call(accs, function (a) {
      Array.prototype.forEach.call(a.querySelectorAll('.accordion__head'), function (h) {
        h.addEventListener('click', function () {
          var item = h.closest('.accordion__item');
          var body = item.querySelector('.accordion__body');
          var open = item.classList.toggle('is-open');
          body.style.maxHeight = open ? (body.scrollHeight + 'px') : '0px';
        });
      });
      Array.prototype.forEach.call(a.querySelectorAll('.accordion__item.is-open'), function (it) {
        var b = it.querySelector('.accordion__body'); b.style.maxHeight = b.scrollHeight + 'px';
      });
    });
  };

  /* ---------- 模态框 ---------- */
  Glass.openModal = function (id) {
    var m = typeof id === 'string' ? document.getElementById(id) : id;
    if (!m) return;
    m.classList.add('is-open'); m.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  };
  Glass.closeModal = function (m) {
    if (typeof m === 'string') m = document.getElementById(m);
    if (!m) return;
    m.classList.remove('is-open'); m.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  };

  /* ---------- 抽屉 ---------- */
  Glass.openDrawer = function (id) {
    var d = typeof id === 'string' ? document.getElementById(id) : id;
    if (!d) return;
    var bd = document.createElement('div');
    bd.className = 'drawer__backdrop';
    bd.addEventListener('click', function () { Glass.closeDrawer(d); });
    d.parentNode.insertBefore(bd, d);
    d.classList.add('is-open');
  };
  Glass.closeDrawer = function (d) {
    if (typeof d === 'string') d = document.getElementById(d);
    if (!d) return;
    d.classList.remove('is-open');
    var bd = d.previousElementSibling;
    if (bd && bd.classList.contains('drawer__backdrop')) bd.remove();
  };

  /* 全局点击 / 键盘委托 */
  document.addEventListener('click', function (e) {
    var op = e.target.closest && e.target.closest('[data-modal-open]');
    if (op) { Glass.openModal(op.getAttribute('data-modal-open')); return; }
    var cl = e.target.closest && e.target.closest('[data-modal-close]');
    if (cl) { Glass.closeModal(cl.closest('.modal')); return; }
    if (e.target.classList && e.target.classList.contains('modal__backdrop')) {
      Glass.closeModal(e.target.closest('.modal'));
    }
    var dop = e.target.closest && e.target.closest('[data-drawer-open]');
    if (dop) { Glass.openDrawer(dop.getAttribute('data-drawer-open')); }
    var dcl = e.target.closest && e.target.closest('[data-drawer-close]');
    if (dcl) { Glass.closeDrawer(dcl.closest('.drawer')); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      Array.prototype.forEach.call(document.querySelectorAll('.modal.is-open'), Glass.closeModal);
      Array.prototype.forEach.call(document.querySelectorAll('.drawer.is-open'), Glass.closeDrawer);
    }
  });

  /* ---------- 吐司 ---------- */
  var ICONS = { success: '✓', error: '✕', info: 'i', warn: '!' };
  Glass.toast = function (opts) {
    opts = opts || {};
    var stack = document.querySelector('.toast-stack');
    if (!stack) { stack = document.createElement('div'); stack.className = 'toast-stack'; document.body.appendChild(stack); }
    var t = document.createElement('div');
    t.className = 'toast toast--' + (opts.type || 'info');
    t.setAttribute('role', 'status');
    t.innerHTML =
      '<span class="toast__icon">' + (opts.icon || ICONS[opts.type || 'info'] || 'i') + '</span>' +
      '<div class="toast__body"><div class="toast__title"></div>' +
      (opts.msg ? '<div class="toast__msg"></div>' : '') + '</div>' +
      '<span class="toast__close" aria-label="关闭">×</span>';
    t.querySelector('.toast__title').textContent = opts.title || '';
    if (opts.msg) t.querySelector('.toast__msg').textContent = opts.msg;
    var tm;
    function dismiss() { clearTimeout(tm); t.classList.add('is-leaving'); setTimeout(function () { t.remove(); }, 300); }
    t.querySelector('.toast__close').addEventListener('click', dismiss);
    stack.appendChild(t);
    tm = setTimeout(dismiss, opts.duration || 3200);
    return t;
  };

  /* ---------- 进度 ---------- */
  Glass.setProgress = function (el, pct) {
    if (!el) return;
    pct = Math.max(0, Math.min(100, pct));
    var bar = el.querySelector('.progress__bar');
    if (bar) { bar.style.width = pct + '%'; }
    else { el.style.setProperty('--p', (pct / 100).toFixed(3)); }
  };

  /* ---------- 跨组件主题（重设主色，全局生效）---------- */
  Glass.setAccent = function (hex) {
    var root = document.documentElement.style;
    root.setProperty('--primary', hex);
    // 派生深端（向黑混合 16%）与浅端（向白混合 30%）
    root.setProperty('--primary-d', mix(hex, '#000000', 0.16));
    root.setProperty('--primary-l', mix(hex, '#ffffff', 0.35));
    root.setProperty('--band', 'linear-gradient(135deg,' + hex + ' 0%,' + mix(hex, '#5e5ce6', 0.5) + ' 100%)');
  };
  function mix(a, b, t) {
    var ca = hex2rgb(a), cb = hex2rgb(b);
    var r = Math.round(ca[0] + (cb[0] - ca[0]) * t);
    var g = Math.round(ca[1] + (cb[1] - ca[1]) * t);
    var bl = Math.round(ca[2] + (cb[2] - ca[2]) * t);
    return '#' + [r, g, bl].map(function (v) { return ('0' + v.toString(16)).slice(-2); }).join('');
  }
  function hex2rgb(h) {
    h = h.replace('#', '');
    if (h.length === 3) h = h.split('').map(function (c) { return c + c; }).join('');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }

  /* ---------- 初始化 ---------- */
  function init() {
    Glass.initTabs();
    Glass.initSegmented();
    Glass.initAccordion();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else { init(); }
})();
