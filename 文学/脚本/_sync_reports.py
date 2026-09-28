# -*- coding: utf-8 -*-
"""
_sync_reports.py —— 报告双视图统一（唯一权威视图 = 01-05 分类子目录）
====================================================================
背景：生成器（03-25 号脚本）把报告写到 产物/ 根（根平铺），而图书馆/入口
历史形成的分类视图在 01_文本语言/ ... 05_制度家族/ 子目录。两份长期漂移
（线上子目录版曾是 59 章旧数据）。

本脚本做三件事（幂等，可重复执行）：
  1. 分发：根平铺报告（生成器权威输出，数据最新）覆盖到分类子目录
  2. 重写：全产物区 html/js/json 中按"宿主所在目录"把裸文件名链接
     改写为正确的相对路径（报告→分类子目录，功能页→根）
  3. 清理：删除根平铺报告副本与重复的图书馆旧页

根平铺 = 生成器输出缓冲区；子目录 = 线上唯一报告视图。
"""
import os, re, io, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "产物")

# ---- 分类子目录报告（线上唯一视图）----
SUB_REPORTS = {
    # 文件名: 分类目录
    "苇舟江湖梦_词汇计量.html": "01_文本语言",
    "苇舟江湖梦_风格计量.html": "01_文本语言",
    "苇舟江湖梦_可视化叙事系统.html": "02_叙事情感",
    "苇舟江湖梦_情感时序.html": "02_叙事情感",
    "苇舟江湖梦_扩展叙事可视化.html": "02_叙事情感",
    "苇舟江湖梦_时间节奏量化.html": "02_叙事情感",
    "苇舟江湖梦_派生维度量化.html": "02_叙事情感",
    "苇舟江湖梦_深度叙事可视化.html": "02_叙事情感",
    "苇舟江湖梦_章节标签量化看板.html": "02_叙事情感",
    "苇舟江湖梦_章节结构量化.html": "02_叙事情感",
    "苇舟江湖梦_人物关系网络.html": "03_人物社会",
    "苇舟江湖梦_口头禅量化.html": "03_人物社会",
    "苇舟江湖梦_对打动作量化.html": "03_人物社会",
    "苇舟江湖梦_统计推断.html": "03_人物社会",
    "苇舟江湖梦_角色性格量化.html": "03_人物社会",
    "苇舟江湖梦_地理位置关系图.html": "04_空间地理",
    "苇舟江湖梦_地理描述量化.html": "04_空间地理",
    "苇舟江湖梦_空间地点分析报告.html": "04_空间地理",
    "苇舟江湖梦_官制考究.html": "05_制度家族",
    "川阴王建都推演.html": "05_制度家族",
    "黄家概况.html": "05_制度家族",
    "苇舟江湖梦_数据归档总览.html": "数据归档",
}
# ---- 根功能页（保留在根）----
ROOT_FUNC = [
    "苇舟江湖梦_分析报告.html", "苇舟江湖梦_原文阅读.html",
    "苇舟江湖梦_报告归纳整理.html", "苇舟江湖梦_关键词索引.html",
    "苇舟江湖梦_组件库.html", "美学图谱.html",
]
# ---- 确认删除的重复页 ----
DUPES = ["苇舟江湖梦_图书馆.html"]  # 与 library.html 重复

ALL_NAMES = list(SUB_REPORTS.keys()) + ROOT_FUNC
# 归一正则：把已带分类前缀的形态还原为裸名（防二次加前缀）
_norm_re = re.compile(
    "(?:0\\d_[^/\"'\\)\\s]+|数据归档)/(" + "|".join(re.escape(n) for n in ALL_NAMES) + ")"
)

SKIP_DIRS = {"fonts", "glass", "支撑资源", ".git"}


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def host_dir(rel):
    """宿主文件的目录前缀（'' = 根）"""
    d = os.path.dirname(rel)
    return "" if not d or d == "." else d + "/"


def rewrite_links(rel, text):
    """按宿主目录重写报告/功能页链接（先归一，再加正确前缀）"""
    text = _norm_re.sub(r"\1", text)
    hd = host_dir(rel)

    def sub_name(name):
        if name in SUB_REPORTS:
            target = SUB_REPORTS[name] + "/" + name
        elif name in ROOT_FUNC:
            target = name
        else:
            return name
        if hd == "":            # 宿主在根
            return target
        return "../" + target   # 宿主在子目录

    for name in ALL_NAMES:
        # 仅替换引用形态（引号内整名，避免误伤正文文字）
        for q in ("\"", "'"):
            text = text.replace(q + name + q, q + sub_name(name) + q)
            text = text.replace(q + "./" + name + q, q + sub_name(name) + q)
    return text


def main():
    # 1) 分发：根平铺 → 子目录（根平铺是生成器最新输出）
    n_copy = 0
    for name, sub in SUB_REPORTS.items():
        src = os.path.join(OUT, name)
        dst = os.path.join(OUT, sub, name)
        if os.path.exists(src):
            shutil.copyfile(src, dst)
            os.remove(src)
            n_copy += 1
        elif not os.path.exists(dst):
            print("  [WARN] 两处均缺失: " + name)
    print("[分发] 根平铺 → 子目录: %d 份" % n_copy)

    # 2) 删除确认重复页
    for name in DUPES:
        p = os.path.join(OUT, name)
        if os.path.exists(p):
            os.remove(p)
            print("[删除] 重复页: " + name)

    # 3) 全区链接重写（html/js/json）
    n_rw = 0
    for dp, dn, fn in os.walk(OUT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if not f.endswith((".html", ".js", ".json")):
                continue
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, OUT).replace("\\", "/")
            t = read(full)
            t2 = rewrite_links(rel, t)
            if t2 != t:
                write(full, t2)
                n_rw += 1
    print("[重写] 链接更新文件: %d 个" % n_rw)

    # 4) 校验：根平铺不应再有报告
    left = [n for n in list(SUB_REPORTS.keys()) if os.path.exists(os.path.join(OUT, n))]
    print("[校验] 根平铺残留报告: %s" % (left or "无"))
    print("完成。")


if __name__ == "__main__":
    main()
