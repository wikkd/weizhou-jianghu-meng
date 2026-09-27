# -*- coding: utf-8 -*-
"""
全量迁移：将 产物/*.html 中的 <link ... href="theme.css"> 切换为 href="glass.css"。
幂等：仅当存在 theme.css 引用时才替换，已迁移的不会重复处理。
"""
import io, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT  = os.path.join(ROOT, "产物")

LINK_PATTERNS = [
    (re.compile(r'href="theme\.css"'), 'href="glass.css"'),
    (re.compile(r"href='theme\.css'"), "href='glass.css'"),
]

def migrate_file(path):
    txt = io.open(path, encoding="utf-8").read()
    changed = 0
    for pat, repl in LINK_PATTERNS:
        new, n = pat.subn(repl, txt)
        if n:
            txt = new; changed += n
    if changed:
        io.open(path, "w", encoding="utf-8").write(txt)
    return changed

def main():
    files = sorted(glob.glob(os.path.join(OUT, "*.html")))
    # 排除组件库示范页（已自行引用 glass.css）与安全名
    total = 0
    migrated = []
    for f in files:
        if os.path.basename(f) == "苇舟江湖梦_组件库.html":
            continue
        c = migrate_file(f)
        if c:
            total += c; migrated.append(os.path.basename(f))
    print("迁移完成。替换引用 %d 处，涉及 %d 个文件：" % (total, len(migrated)))
    for m in migrated:
        print("  -", m)
    if not migrated:
        print("  （无需要迁移的文件，可能已全量切换）")

if __name__ == "__main__":
    main()
