"""現行サイトとデモサイトの突き合わせ
1. 文字：現行の本文テキストを行単位に分け、デモの同じページに含まれているか（誤字修正は修正後で照合）
2. 画像：現行本文の画像（装飾画像を除く）がデモの同じページにあるか
3. リンク：デモ内のサイト内リンク・画像の参照先ファイルが存在するか
4. 動画：YouTube の埋め込みが同じページにあるか
結果は raw/verify_report.txt に書く。"""
import os, re, json, sys, urllib.parse, html as H
from bs4 import BeautifulSoup, Comment
sys.path.insert(0, os.path.dirname(__file__))
import build

ROOT = build.ROOT
info = build.info
DECOR = set(build.DECOR_REPLACE) | {"page-up.jpg"}

def norm(s):
    s = H.unescape(s)
    s = re.sub(r"[\s　\xa0]+", "", s)
    return s

def orig_segments(src, path):
    main = build.extract_main(src)
    soup = BeautifulSoup(main, "html.parser")
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    for t in soup.find_all(["script", "style", "noscript"]):
        t.decompose()
    for f in soup.find_all("form"):  # フォームは項目名だけ照合
        labels = [l.get_text(" ", strip=True) for l in f.select(".label label")]
        opts = [o.get_text(strip=True) for o in f.find_all("option")] + [l.get_text(strip=True) for l in f.select(".field label")]
        descs = [d.get_text(" ", strip=True) for d in f.select("p.description")]
        f.replace_with("\n".join(labels + opts + descs))
    txt = soup.get_text("\n")
    segs = []
    for line in txt.split("\n"):
        n = norm(line)
        if len(n) >= 2 and n not in ("フォームを送信するにはJavaScriptをONにしてください。",):
            segs.append(n)
    imgs = []
    for im in soup.find_all("img"):
        s = im.get("src", "")
        base = urllib.parse.unquote(s.split("/")[-1])
        if base in DECOR or s.startswith("/track"):
            continue
        n = build.norm_internal(s)
        if n:
            imgs.append(urllib.parse.unquote(n.split("/asset/")[-1] if "asset/" in n else n))
    vids = re.findall(r"youtube\.com/embed/([\w-]+)", main) + re.findall(r"youtube\.com/watch\?v=([\w-]+)", main)
    return segs, imgs, vids

def fixed(seg):
    for page, old, new in build.FIXES:
        o = norm(re.sub(r"<[^>]+>", "", old)); n = norm(re.sub(r"<[^>]+>", "", new))
        if o and o in seg:
            seg = seg.replace(o, n)
    return seg

def new_text(path):
    p = os.path.join(build.OUT, path)
    s = open(p, encoding="utf-8").read()
    soup = BeautifulSoup(s, "html.parser")
    main = soup.find("main")
    # 入力欄の placeholder も照合対象に
    extra = " ".join(i.get("placeholder", "") for i in main.find_all("input"))
    return norm(main.get_text("") + extra), s

def main():
    out = []
    pages = {}
    for url, d in info.items():
        if "file" in d:
            pages[urllib.parse.urlparse(url).path.lstrip("/")] = d["file"]
    pages["topic1.html"] = "topic1.html"; pages["topic2.html"] = "topic2.html"
    topic_all = new_text("topic1.html")[0] + new_text("topic2.html")[0]
    total_seg = miss_seg = total_img = miss_img = 0
    for path, f in sorted(pages.items()):
        src = open(os.path.join(build.RAW, f), encoding="utf-8").read()
        segs, imgs, vids = orig_segments(src, path)
        nt, nhtml = new_text(path)
        # トップページは「お知らせ」本文がお知らせ一覧側にあれば可
        hay = nt + (topic_all if path == "index.html" else "")
        miss = []
        for sg in segs:
            total_seg += 1
            sg2 = fixed(sg)
            if sg2 in hay or sg in hay:
                continue
            # 行が長い場合、途中にタグ由来の分割がある可能性 → 前後半で照合
            if len(sg2) > 30 and sg2[:15] in hay and sg2[-15:] in hay:
                continue
            miss.append(sg)
        mimg = []
        for im in imgs:
            total_img += 1
            if im.split("/")[-1] not in urllib.parse.unquote(nhtml):
                mimg.append(im)
        mv = [v for v in vids if v not in nhtml]
        miss_seg += len(miss); miss_img += len(mimg)
        if miss or mimg or mv:
            out.append(f"■ {path}")
            for m in miss: out.append(f"  [文字] {m}")
            for m in mimg: out.append(f"  [画像] {m}")
            for m in mv: out.append(f"  [動画] {m}")
    # リンク切れ（デモ内）
    broken = []
    for dp, _, fs in os.walk(build.OUT):
        for fn in fs:
            if not fn.endswith(".html") or fn == "proposal.html":
                continue
            fp = os.path.join(dp, fn)
            s = open(fp, encoding="utf-8").read()
            for m in re.findall(r'(?:href|src)="([^"]+)"', s):
                if m.startswith(("http", "mailto:", "tel:", "#", "data:", "javascript")):
                    continue
                t = urllib.parse.unquote(m.split("#")[0])
                if not t:
                    continue
                if not os.path.exists(os.path.normpath(os.path.join(dp, t))):
                    broken.append((os.path.relpath(fp, build.OUT), m))
    out.append(f"\n== デモ内のリンク切れ: {len(broken)}件")
    for b in sorted(set(broken)): out.append(f"  {b[0]} -> {b[1]}")
    head = f"文字 {total_seg}行中 未検出 {miss_seg}行 / 画像 {total_img}点中 未検出 {miss_img}点\n"
    open(os.path.join(ROOT, "raw", "verify_report.txt"), "w", encoding="utf-8").write(head + "\n".join(out))
    print(head)

if __name__ == "__main__":
    main()
