"""現行サイト www.jecom.jp を全ページクロールして raw/pages/ に保存する。
メインコンテンツ部分のテキストと画像・リンク一覧を raw/extract/ に書き出す。"""
import re, os, sys, json, time, urllib.request, urllib.parse
from html.parser import HTMLParser

BASE = "https://www.jecom.jp"
ROOT = os.path.join(os.path.dirname(__file__), "..", "raw")
PAGES = os.path.join(ROOT, "pages")
EXT = os.path.join(ROOT, "extract")
os.makedirs(PAGES, exist_ok=True); os.makedirs(EXT, exist_ok=True)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()

def norm(href, cur):
    u = urllib.parse.urljoin(cur, href.strip())
    u = u.split("#")[0]
    p = urllib.parse.urlparse(u)
    if p.netloc not in ("www.jecom.jp", "jecom.jp"):
        return None
    path = p.path or "/"
    if path.endswith("/"):
        path += "index.html"
    if not path.endswith(".html"):
        return None
    return BASE + path

seen, queue, info = set(), [BASE + "/index.html"], {}
while queue:
    url = queue.pop(0)
    if url in seen:
        continue
    seen.add(url)
    try:
        st, ct, body = fetch(url)
    except Exception as e:
        info[url] = {"error": str(e)}
        print("ERR", url, e); continue
    html = body.decode("utf-8", "replace")
    name = urllib.parse.urlparse(url).path.strip("/").replace("/", "__")
    open(os.path.join(PAGES, name), "w", encoding="utf-8").write(html)
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    info[url] = {"file": name, "title": title.group(1).strip() if title else ""}
    print(st, url)
    for h in re.findall(r'href="([^"]+)"', html):
        n = norm(h, url)
        if n and n not in seen:
            queue.append(n)
    time.sleep(0.3)

json.dump(info, open(os.path.join(ROOT, "pages.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(info), "pages")
