"""追加チェック：HTML構造・ページ内リンク・タイトル・リンク先の内容の食い違い など"""
import os, re, sys, json, urllib.parse
from collections import Counter
from bs4 import BeautifulSoup
sys.path.insert(0, os.path.dirname(__file__))
import build
sys.stdout.reconfigure(encoding="utf-8")
OUT = build.OUT
pages = {}
for url, d in build.info.items():
    if "file" in d:
        pages[urllib.parse.urlparse(url).path.lstrip("/")] = d["file"]
pages["topic1.html"] = "topic1.html"; pages["topic2.html"] = "topic2.html"

def soup_of(path):
    return BeautifulSoup(open(os.path.join(OUT, path), encoding="utf-8").read(), "html.parser")

issues = []
titles = {}
for path in sorted(pages):
    s = soup_of(path)
    # 重複ID
    ids = [t["id"] for t in s.find_all(id=True)]
    d = [k for k, v in Counter(ids).items() if v > 1]
    if d: issues.append(f"{path}: 重複ID {d}")
    # aの入れ子
    for a in s.find_all("a"):
        if a.find("a"): issues.append(f"{path}: aの入れ子 {a.get('href')}")
        if not a.get_text(strip=True) and not a.find("img") and "to-top" not in (a.get("class") or []):
            issues.append(f"{path}: 中身の無いリンク {a.get('href')}")
    # ページ内リンク / 他ページのアンカー
    for a in s.find_all("a", href=True):
        h = a["href"]
        if h.startswith(("http", "mailto", "tel")) or "#" not in h: continue
        target, frag = h.split("#", 1)
        if not frag or frag == "top": continue
        tp = os.path.normpath(os.path.join(os.path.dirname(os.path.join(OUT, path)), urllib.parse.unquote(target))) if target else os.path.join(OUT, path)
        if not os.path.exists(tp): continue
        ts = BeautifulSoup(open(tp, encoding="utf-8").read(), "html.parser")
        if not ts.find(id=frag) and not ts.find(attrs={"name": frag}):
            issues.append(f"{path}: アンカー先なし {h}（{a.get_text(strip=True)[:20]}）")
    # 空の見出し
    for h in s.find_all(["h1", "h2", "h3", "h4"]):
        if not h.get_text(strip=True): issues.append(f"{path}: 空の見出し {h.name}")
    # タイトル・説明文が現行と同じか
    src = open(os.path.join(build.RAW, pages[path]), encoding="utf-8").read()
    mt = re.search(r"<title>(.*?)</title>", src, re.S)
    ot = mt.group(1).strip() if mt else ""
    nt = s.title.get_text().strip()
    if path.startswith("topic"):
        pass
    elif ot != nt: issues.append(f"{path}: title違い 現行[{ot}] デモ[{nt}]")
    h1 = s.find("h1")
    titles[path] = h1.get_text(" ", strip=True) if h1 else nt
# リンク文字とリンク先ページの見出しの食い違い（現行サイト側）
mism = []
for path, f in pages.items():
    src = open(os.path.join(build.RAW, f), encoding="utf-8").read()
    main = build.extract_main(src)
    for m in re.finditer(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', main, re.S):
        href, inner = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        inner = re.sub(r"\s+", "", inner)
        n = build.norm_internal(href)
        if not n or n.startswith(("http", "#", "mailto")) or not n.endswith(".html") and ".html#" not in n: continue
        tgt = n.split("#")[0]
        if tgt not in titles or len(inner) < 4 or inner in ("詳細はこちら", "こちら", "詳しく見る"): continue
        tt = re.sub(r"\s+", "", titles[tgt])
        key = re.sub(r"[・▶→\(\)（）\[\]［］]", "", inner)[:6]
        if key and key not in re.sub(r"[・▶→\(\)（）\[\]［］]", "", tt) :
            mism.append(f"{path}: 「{inner[:30]}」→ {tgt}（見出し：{tt[:30]}）")
print("== 構造・アンカー・タイトル", len(issues))
for i in issues: print(" ", i)
print("== リンク文字とリンク先見出しの食い違い候補", len(mism))
for i in sorted(set(mism)): print(" ", i)
