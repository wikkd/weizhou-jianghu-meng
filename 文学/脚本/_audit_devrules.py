# -*- coding: utf-8 -*-
"""DEV_RULES 合规审计：产物/ 全部页面逐条扫铁律与红线（只读，不改）。"""
import io, os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "产物")

pages = sorted(glob.glob(os.path.join(BASE, "*.html"))) + \
        sorted(glob.glob(os.path.join(BASE, "*", "*.html")))
CSS = [os.path.join(BASE, "theme.css"), os.path.join(BASE, "glass.css")]

def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()

issues = {}
def add(cat, item):
    issues.setdefault(cat, []).append(item)

CDN_RE = re.compile(r'(?:src|href)\s*=\s*["\'](https?:)?//[^"\']+', re.I)
CDN_RE2 = re.compile(r'(?:src|href)\s*=\s*["\']https?://[^"\']+', re.I)
ALL_TRANS = re.compile(r"transition\s*:[^;]*\ball\b", re.I)
INF_ANIM = re.compile(r"animation\s*:[^;]*(infinite|alternate\s+infinite)", re.I)
STORE_KEYS = re.compile(r"localStorage\.(?:getItem|setItem|removeItem)\(\s*['\"]([^'\"]+)['\"]", re.I)

for p in pages:
    rel = os.path.relpath(p, BASE)
    html = read(p)
    # 1. 外链（src/href 绝对 URL）
    ext = [m.group(0) for m in CDN_RE2.finditer(html)]
    # 过滤 data URI 之类误报不存在的；另外查 CSS 内 @import url(http
    if ext:
        add("外链CDN", f"{rel}: {ext[:3]}")
    for cssf in CSS:
        c = read(cssf)
        for m in re.finditer(r"@import\s+url\(\s*['\"]?https?", c):
            add("外链CDN", f"{os.path.basename(cssf)}: @import 外部")
            break
    # 2. transition:all
    if ALL_TRANS.search(html):
        add("transition:all", f"{rel}")
    for cssf in CSS:
        if rel.endswith("theme.css") is False and cssf.endswith(("theme.css", "glass.css")):
            pass
    # 3. 循环动画（页面内联）——白名单：功能性加载反馈（状态反馈四件套）
    LOADING_OK = ("glass-shimmer", "glass-spin")   # 骨架屏流光 / 加载圈，非装饰
    for m in INF_ANIM.finditer(html):
        name = re.search(r"animation\s*:\s*([\w-]+)", m.group(0))
        nm = name.group(1) if name else ""
        if nm not in LOADING_OK:
            add("循环动画", f"{rel}: {nm or m.group(0)[:40]}")
    # 4. localStorage 键
    for m in STORE_KEYS.finditer(html):
        k = m.group(1)
        if not k.startswith("wzjm_"):
            add("存储键前缀", f"{rel}: '{k}'")
    # 5. 返回入口（来路/逃生口）：页内是否有指向 index/总览 的链接
    has_back = bool(re.search(r'href="[^"]*index\.html|href="\.\./|返回|回到|报告中心|总览', html))
    if not has_back:
        add("缺返回入口", rel)

# CSS 单独查
for cssf in CSS:
    c = read(cssf)
    n = os.path.basename(cssf)
    for m in ALL_TRANS.finditer(c):
        add("transition:all", f"{n}(CSS)")
        break
    for m in INF_ANIM.finditer(c):
        name = re.search(r"animation\s*:\s*([\w-]+)", m.group(0))
        nm = name.group(1) if name else ""
        if nm not in ("glass-shimmer", "glass-spin"):  # 白名单：骨架屏/加载圈（状态反馈）
            add("循环动画", f"{n}(CSS): {nm}")

print("=" * 60)
for cat in sorted(issues):
    items = issues[cat]
    uniq = sorted(set(items))
    print(f"[{cat}] {len(uniq)} 项")
    for it in uniq[:12]:
        print("   -", it)
    if len(uniq) > 12:
        print(f"   ... 其余 {len(uniq)-12} 项")
if not issues:
    print("全部通过")
