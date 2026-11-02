"""raw/pages/ の各ページからメインコンテンツを取り出し、テキスト化して raw/extract/*.txt に書く。
HTMLコメント内（非表示）の内容は除外する。画像は [IMG src | alt]、リンクは [text](href) で残す。"""
import re, os, json, html as H

ROOT = os.path.join(os.path.dirname(__file__), "..", "raw")
info = json.load(open(os.path.join(ROOT, "pages.json"), encoding="utf-8"))

def main_part(src):
    m = re.search(r'<div id="main-contents">(.*?)<!-- /メインコンテンツ', src, re.S)
    if m:
        return m.group(1)
    m = re.search(r'<div id="cont">(.*?)<footer', src, re.S)
    return m.group(1) if m else src

def to_text(s):
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S | re.I)
    def img(m):
        t = m.group(0)
        src = re.search(r'src="([^"]*)"', t); alt = re.search(r'alt="([^"]*)"', t)
        return f" [IMG {src.group(1) if src else ''} | {alt.group(1) if alt else ''}] "
    s = re.sub(r"<img[^>]*>", img, s, flags=re.I)
    s = re.sub(r"<iframe[^>]*src=\"([^\"]*)\"[^>]*>", r" [IFRAME \1] ", s, flags=re.I)
    s = re.sub(r"<(source|embed)[^>]*src=\"([^\"]*)\"[^>]*>", r" [MEDIA \2] ", s, flags=re.I)
    def a(m):
        href = re.search(r'href="([^"]*)"', m.group(1))
        return f"[{m.group(2)}]({href.group(1) if href else ''})"
    s = re.sub(r"<a\b([^>]*)>(.*?)</a>", a, s, flags=re.S | re.I)
    s = re.sub(r"<h([1-6])[^>]*>", lambda m: "\n\n" + "#" * int(m.group(1)) + " ", s, flags=re.I)
    s = re.sub(r"</(p|div|h[1-6]|li|tr|table)>", "\n", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<(td|th)[^>]*>", " | ", s, flags=re.I)
    s = re.sub(r"<li[^>]*>", "\n・", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = H.unescape(s).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in s.splitlines()]
    out, blank = [], 0
    for l in lines:
        if l in ("", "|", "| |", "| | |"):
            blank += 1
            if blank == 1: out.append("")
        else:
            blank = 0; out.append(l)
    return "\n".join(out).strip()

allout = []
for url, d in info.items():
    if "file" not in d: continue
    src = open(os.path.join(ROOT, "pages", d["file"]), encoding="utf-8").read()
    txt = to_text(main_part(src))
    open(os.path.join(ROOT, "extract", d["file"] + ".txt"), "w", encoding="utf-8").write(f"URL: {url}\nTITLE: {d['title']}\n\n{txt}\n")
    allout.append((url, len(txt)))
for u, n in allout: print(n, u)
