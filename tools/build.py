"""JECOM デモサイト生成スクリプト
現行サイトの本文（raw/pages/）を新デザインのテンプレートに流し込み、site/ に書き出す。
- URLは現行と同じパスを維持（SEO）
- 本文の文字情報は現行のまま（誤字の修正は FIXES に一覧化して提案書に記載）
- トップページ等の手作りページは tools/partials/ の内容を使う
"""
import os, re, json, html as H, urllib.parse
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "pages")
OUT = os.path.join(ROOT, "site")
PARTS = os.path.join(HERE, "partials")
info = json.load(open(os.path.join(ROOT, "raw", "pages.json"), encoding="utf-8"))

TEL = "048-936-5699"
FAX = "048-936-5693"
HOURS = "平日9:00〜17:15"

# ---------------------------------------------------------------- サイト構成
SECTIONS = [
    dict(key="safety", label="オフィスの安全対策", en="Office Safety", hub="office.html", hub_title="オフィスの安全対策について", children=[
        ("annzenn/riskninnchi.html", "地震発生リスク認知について"),
        ("annzenn/office.html", "巨大地震発生時、オフィス内はどうなるのか？"),
        ("dutyofcare.html", "安全配慮義務"),
        ("annzen/selfcheck.html", "室内安全対策セルフチェック"),
        ("annzenn/damper.html", "震度７相当に対応のダンパー機能付制振器具"),
        ("bousaikanritenken.html", "防災管理点検"),
    ]),
    dict(key="seishin", label="制震オフィス", en="Seismic Office", hub="office/index.html", hub_title="震度７相当に対応［制震オフィス］", children=[
        ("seisinoffice/about.html", "制震オフィスとは"),
        ("jisya_toritsuke.html", "制振器具を自社で簡単設置できる目安表"),
        ("chosa_sindan.html", "制震オフィス化診断"),
        ("chousa_sindan_ex.html", "制震オフィス化診断 実施例"),
        ("sekou_service.html", "制震オフィスソリューションサービス"),
        ("seishin/jikkendouga.html", "制振器具の実験動画"),
    ]),
    dict(key="products", label="商品紹介", en="Products", hub="eco_bus/index.html", hub_title="商品紹介", children=[
        ("shouhinn/damper.html", "社員の生命を守るダンパー機能付制振器具"),
        ("shouhinn/jecomselect-flooddamageescape.html", "水害対策用品"),
        ("shouhinn/jecomselect/sanitarygoods.html", "オフィス向け備蓄用品　衛生用品"),
        ("shouhinn/jecomselect/foods.html", "オフィス向け備蓄用品　水・食料セット"),
        ("shouhinn/all.html", "商品一覧"),
        ("ichioshi.html", "今コレ！アレルギー対応・ハラール対応食品"),
    ]),
    dict(key="qa", label="Q&A", en="Q&A", hub="qa.html", hub_title="Q＆A", children=[
        ("qa_seshin.html", "制振器具に関する質問"),
        ("qa_secchi.html", "設置作業に関する質問"),
        ("qa_bousai.html", "防災用品選定に関する質問"),
    ]),
    dict(key="gaisan", label="概算見積", en="Estimate", hub="gaisan.html", hub_title="概算見積", children=[
        ("checkpoint.html", "オフィス内チェックポイント"),
        ("gaisan/simulation.html", "概算見積シミュレーション"),
    ]),
    dict(key="company", label="会社概要", en="Company", hub="profile/index.html", hub_title="会社概要", children=[
        ("aisatsu.html", "社長あいさつ"),
        ("kigyorinen.html", "企業理念"),
        ("partner2/index.html", "ビジネスパートナー募集"),
        ("contact.html", "お問い合わせ"),
    ]),
]
INFO_SECTION = dict(key="info", label="防災情報・お知らせ", en="Information", hub="bousai-info.html", hub_title="都道府県防災情報", children=[
    ("topic1.html", "お知らせ一覧"),
    ("topic2.html", "防災情報一覧"),
    ("bousai-info.html", "都道府県防災情報"),
    ("sitemap/index.html", "サイトマップ"),
    ("about.html", "このサイトについて"),
    ("privacy.html", "個人情報保護方針"),
])
PREFS = [("hokkaido", "北海道"), ("miyagi", "宮城県"), ("tokyo", "東京都"), ("shizuoka", "静岡県"), ("aichi", "愛知県"),
         ("ishikawa", "石川県"), ("osaka", "大阪府"), ("hyogo", "兵庫県"), ("hiroshima", "広島県"), ("ehime", "愛媛県"),
         ("fukuoka", "福岡県"), ("okinawa", "沖縄県")]

# 商品ページ → 商品紹介セクション
PRODUCT_PAGES = {
    "shouhinn/kttcasterstopper.html": "shouhinn/damper.html", "ktt_003j.html": "shouhinn/damper.html", "ktt_004j.html": "shouhinn/damper.html",
    "ktt_005j.html": "shouhinn/damper.html", "ktt_006j.html": "shouhinn/damper.html", "ktt_007j.html": "shouhinn/damper.html",
    "secretroom-ktt.html": "shouhinn/damper.html",
    "shouhinn/jecomselect/sunoukun2.html": "shouhinn/jecomselect-flooddamageescape.html",
    "jecomselect/suinoukun2/1m.html": "shouhinn/jecomselect-flooddamageescape.html",
    "jecomselect/suinoukun2/5p.html": "shouhinn/jecomselect-flooddamageescape.html",
}
for p in ["sanitary", "sanitary2", "bodytowel", "wettowel"]:
    PRODUCT_PAGES[f"shouhinn/jecomselect/{p}.html"] = "shouhinn/jecomselect/sanitarygoods.html"
PRODUCT_PAGES["eco_bus/situnai_kinmu.html"] = "shouhinn/jecomselect/sanitarygoods.html"
PRODUCT_PAGES["untitled2/shouhinn/jecomselect/acrylicplate.html"] = "shouhinn/jecomselect/sanitarygoods.html"
for p in ["3daysset", "3days_foods", "5yearsrice", "7yearscookie", "7yearskomekocookie", "7yearsbread", "7yearsrice", "7yearsokazu",
          "7yearswater", "7years_set", "7years_set2", "7years_set3", "10yearswater", "10yearscookie"]:
    PRODUCT_PAGES[f"shouhinn/jecomselect/{p}.html"] = "shouhinn/jecomselect/foods.html"
PRODUCT_PAGES["jecomselect/7years_shasaiset2.html"] = "shouhinn/jecomselect/foods.html"

def section_of(path):
    for s in SECTIONS + [INFO_SECTION]:
        if path == s["hub"] or any(path == c for c, _ in s["children"]):
            return s
    if path in PRODUCT_PAGES:
        return SECTIONS[2]
    if path.startswith("bousai-info/") or path.startswith("bousi-info/"):
        return INFO_SECTION
    return INFO_SECTION

# 現行サイトのリンク切れ → デモでの扱い（提案書にも記載）
BROKEN = {
    "/shouhinn/jecomselect-escape.html": None,            # 初期消火・避難具（取扱停止）→ リンクを外す
    "/eco_bus/hudo_tv.html": "/ktt_007j.html",            # 旧テレビ用シート → 後継のKTT-007Jへ（要確認）
    "/eco_bus/hudo_stv.html": "/ktt_007j.html",
    "/shouhinn/jecomselect/10years_set.html": None,       # 10年保存クッキー3日分セット：ページが存在しない
    "/shouhinn/jecomselect/7years_shasaiset.html": "/jecomselect/7years_shasaiset2.html",
}
DEAD_EXTERNAL_PREFIX = ("http://bizmail.itp.ne.jp", "https://bizmail.itp.ne.jp")  # 終了したブログサービス

# 明らかな誤字の修正（ページ, 修正前, 修正後）。提案書の「誤字修正一覧」と同じ内容
FIXES = [
    ("*", "数博年オーダー", "数百年オーダー"),
    ("annzen/selfcheck.html", "出展：東京消防庁", "出典：東京消防庁"),
    ("annzen/selfcheck.html", "下記出展元", "下記出典元"),
    ("seishin/jikkendouga.html", "（出展）", "（出典）"),
    ("dutyofcare.html", "<th><strong>請求額</strong></th><th><strong>請求額</strong></th>", "<th><strong>請求額</strong></th><th><strong>結果</strong></th>"),
    ("*", "重量150lgまで", "重量150kgまで"),
    ("*", "オフレイン樹脂壁紙", "オレフィン樹脂壁紙"),
    ("ktt_003j.html", "先着剤と壁", "接着剤と壁"),
    ("*", "対策キッドカーペット用", "対策キットカーペット用"),
    ("checkpoint.html", "適切な器具を選びが重要です", "適切な器具選びが重要です"),
    ("gaisan.html", "適切な器具を選びが重要です", "適切な器具選びが重要です"),
    ("*", "参考にすることできます", "参考にすることができます"),
    ("kigyorinen.html", "少数先鋭", "少数精鋭"),
    ("topic1.html", "おお知らせ", "お知らせ"),
    ("topic1.html", "今後との変わらぬ", "今後とも変わらぬ"),
    ("topic1.html", "お願申し上げます", "お願い申し上げます"),
    ("*", "宜しくお願致します", "宜しくお願い致します"),
    ("ichioshi.html", "Completeⅾ", "Completed"),
]
# 内容が古い・欠けている等で確認が必要な箇所（黄色マーカーで表示）
TODO_MARK = [
    ("*", "※2025年12月10日発売予定"),
    ("shouhinn/damper.html", "重さ（単体）：ｇ"),
    ("contact.html", "見積シミュレーション"),
    ("*", "車両直径100ｍｍ以下"),
    ("shouhinn/jecomselect/7yearsokazu.html", "②140*160"),
]

# ---------------------------------------------------------------- 共通部品
# B案（動きのあるデザイン）は全ページを site/b/ に同じパスで出力する。画像・CSS・JS・提案書は A案のものを共用
VARIANT = "a"
SHARED = ("asset/", "img/", "css/", "js/", "proposal.html")
GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist"

def rel(target, cur):
    """サイト内パス target（先頭/なし）へ、cur ページからの相対パス"""
    frag = ""
    if "#" in target:
        target, frag = target.split("#", 1)
        frag = "#" + frag
    if target == "":
        return frag
    if VARIANT == "b":
        cur = "b/" + cur
        if not target.startswith(SHARED):
            target = "b/" + target
    cur_dir = os.path.dirname(cur)
    r = os.path.relpath(target, cur_dir or ".").replace("\\", "/")
    return r + frag

def nav_html(cur):
    sec = section_of(cur)
    out = []
    for s in SECTIONS[:5]:
        on = " on" if sec is s else ""
        drop = f'<a class="hub" href="{rel(s["hub"], cur)}">{s["hub_title"]}</a>' + "".join(
            f'<a href="{rel(c, cur)}">{t}</a>' for c, t in s["children"])
        out.append(f'<div class="item{on}"><a href="{rel(s["hub"], cur)}">{s["label"]}</a><div class="drop">{drop}</div></div>')
    c = SECTIONS[5]
    on = " on" if sec is c else ""
    drop = f'<a class="hub" href="{rel(c["hub"], cur)}">会社概要</a>' + "".join(f'<a href="{rel(p, cur)}">{t}</a>' for p, t in c["children"])
    out.append(f'<div class="item{on}"><a href="{rel(c["hub"], cur)}">会社概要</a><div class="drop">{drop}</div></div>')
    out.append(f'<div class="m-cta"><a class="btn btn-primary" href="{rel("contact.html", cur)}">お問い合わせ</a><a class="btn btn-line" href="tel:{TEL}">TEL {TEL}</a><p class="note" style="text-align:center;margin:0">FAX {FAX}　営業時間：{HOURS}</p></div>')
    return "".join(out)

def header_html(cur):
    return f'''<div class="util"><div class="container"><span>TEL <b>{TEL}</b></span><span>FAX <b>{FAX}</b></span><span>営業時間：{HOURS}</span></div></div>
<header class="site-header"><div class="container">
<a class="logo" href="{rel("index.html", cur)}"><img src="{rel("img/logo.png", cur)}" alt="JECOM ジェコム株式会社" width="214" height="90"></a>
<nav class="gnav" aria-label="メインメニュー">{nav_html(cur)}</nav>
<a class="btn btn-primary btn-s header-cta" href="{rel("contact.html", cur)}">お問い合わせ</a>
<button class="menu-btn" aria-label="メニュー" aria-expanded="false"><span></span><span></span><span></span></button>
</div></header>'''

ICON = {
    "doc": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></svg>',
    "play": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M10 9.5v5l4.5-2.5z" fill="currentColor"/></svg>',
    "hand": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 12l4-4 4 3 3-3 7 5M7 8v7l5 4 5-4"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>',
    "food": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 10h16v3a8 8 0 0 1-16 0zM8 6c0-1 1-1 1-2M12 6c0-1 1-1 1-2M16 6c0-1 1-1 1-2"/></svg>',
    "map": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>',
    "factory": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 21V10l6 3V10l6 3V6l6-3v18z"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 12l3 3 5-6"/></svg>',
}

def tiles_html(cur):
    """現行サイドバナーを色分けした写真付きバナーに（現行の色分けを踏襲）"""
    T = [
        ("asset/00032/pdf/gennchousinndann-4.pdf", "t-rose", ("img", "asset/00032/seishin/sinndannkekkareport.jpg", True), "現調・診断 申込書ダウンロード", "制震オフィス化診断のお申し込みに（PDF）"),
        ("seishin/jikkendouga.html", "t-apricot", ("play", "asset/00032/office/office_photo1.jpg", False), "制振器具の実験動画", "制振器具の効果を動画でご覧いただけます"),
        ("partner2/index.html", "t-sky", ("img", "asset/00032/seishin/KTT-001J-1.jpg", False), "ビジネスパートナー募集", "販売代理店・施工代理店を募集中"),
        ("contact.html", "t-butter", ("icon", "mail", None), "お問い合わせ", "資料請求・お見積・診断のご相談"),
        ("ichioshi.html", "t-sage", ("img", "asset/00032/syouhin/Cube-Completed2_2402-2_2.jpg", True), "アレルギー対応・ハラール対応 3日分の水・食品セット", "今コレ！のおすすめ備蓄食"),
        ("bousai-info.html", "t-sand", ("icon", "map", None), "都道府県防災情報", "家具転倒防止の助成・啓発情報"),
        ("annzen/selfcheck.html", "t-mint", ("icon", "check", None), "室内安全対策セルフチェック", "オフィスの対策状況を自己診断"),
        ("http://www.fujilatex.co.jp/jp/", "t-lilac", ("img", "asset/00032/side/side-banner.jpg", True), "不二ラテックス株式会社", "外部サイトへ移動します"),
    ]
    out = []
    for href, cls, (kind, src, contain), t, sub in T:
        ext = href.startswith("http")
        h = href if ext else rel(href, cur)
        tgt = ' target="_blank" rel="noopener"' if ext or href.endswith(".pdf") else ""
        if kind == "icon":
            ph = f'<div class="ph"><span class="ic">{ICON[src]}</span></div>'
        else:
            ph = f'<div class="ph{" contain" if contain else ""}"><img src="{rel(src, cur)}" alt="" loading="lazy"></div>'
            if kind == "play":
                ph = ph[:-6] + f'<span class="play">{ICON["play"]}</span></div>'
        out.append(f'<a class="tile {cls}" href="{h}"{tgt}>{ph}<div class="bd"><b>{t}</b><small>{sub}</small><span class="go">{"開く" if ext else "見る"} →</span></div></a>')
    return f'<div class="tiles">{"".join(out)}</div>'

def resources_html(cur):
    return f'''<section class="resources"><div class="container">
<span class="eyebrow">Resources</span><h2>資料・関連情報</h2>
{tiles_html(cur)}</div></section>'''

def news_list_html(tid, cur):
    """お知らせ／防災情報を全件（現行トップと同じくスクロールで全部見られる）"""
    src = open(os.path.join(RAW, f"topic{tid}.html"), encoding="utf-8").read()
    sp = BeautifulSoup(extract_main(src), "html.parser")
    lis = []
    seen = set()
    for dt in sp.find_all("dt"):
        ds = dt.find("span", class_="date")
        date = ds.get_text(strip=True) if ds else ""
        ttl = dt.find("strong").get_text(" ", strip=True) if dt.find("strong") else ""
        did = dt.get("id", "")
        if did in seen: did += "-2"
        seen.add(did)
        ttl, _ = apply_text_fixes(H.escape(ttl), f"topic{tid}.html")
        lis.append(f'<li><a href="{rel(f"topic{tid}.html#{did}", cur)}"><span class="d">{date}</span><span class="t">{ttl}</span></a></li>')
    return f'<ul class="scroll">{"".join(lis)}</ul>'

def cta_html(cur):
    return f'''<section class="cta-band"><div class="container">
<div><span class="eyebrow">Contact</span><h2>オフィスの地震対策、<br>まずはお気軽にご相談ください。</h2>
<p>資料請求・お見積のご依頼・制震オフィス化診断や設置作業のご相談を承ります。</p></div>
<div class="tel-box"><a class="tel" href="tel:{TEL}">{TEL}</a><small>FAX {FAX}　営業時間：{HOURS}</small>
<div class="btns"><a class="btn btn-yellow" href="{rel("contact.html", cur)}">お問い合わせフォーム <span class="arr">→</span></a></div></div>
</div></section>'''

def footer_html(cur):
    cols = []
    for s in SECTIONS[:5]:
        lis = "".join(f'<li><a href="{rel(c, cur)}">{t}</a></li>' for c, t in s["children"])
        cols.append(f'<div><h3><a href="{rel(s["hub"], cur)}">{s["hub_title"]}</a></h3><ul>{lis}</ul></div>')
    c = SECTIONS[5]
    lis = "".join(f'<li><a href="{rel(p, cur)}">{t}</a></li>' for p, t in c["children"])
    lis += "".join(f'<li><a href="{rel(p, cur)}">{t}</a></li>' for p, t in INFO_SECTION["children"][:3])
    cols.append(f'<div><h3><a href="{rel(c["hub"], cur)}">会社概要</a></h3><ul>{lis}</ul></div>')
    # 6列 → 4列グリッドに収めるため Q&A と概算見積を1列にまとめる
    cols = [cols[0], cols[1], cols[2], cols[3] + cols[4] + cols[5]]
    cols = [cols[0], cols[1], cols[2], f'<div>{cols[3]}</div>']
    words = "".join(f"<span>{w}</span>" for w in ["Office Safety for Earthquakes", "JECOM", "Seismic Office", "Japan Eco Communications"] * 2)
    marquee = f'<div class="b-bigtext" aria-hidden="true"><div>{words}</div></div>' if VARIANT == "b" else ""
    return marquee + f'''<footer class="site-footer"><div class="container">
<div class="f-top"><div class="f-brand"><span class="logo-box"><img src="{rel("img/logo.png", cur)}" alt="JECOM ジェコム株式会社"></span>
<p><b>JECOM株式会社</b><br>〒340-0011　埼玉県草加市栄町2-11-3-203<br>TEL：{TEL}　FAX：{FAX}<br>営業時間：{HOURS}</p></div>
<nav class="f-nav" aria-label="サイトマップ">{"".join(cols)}</nav></div>
<div class="f-bottom"><ul><li><a href="{rel("index.html", cur)}">HOME</a></li><li><a href="{rel("sitemap/index.html", cur)}">サイトマップ</a></li><li><a href="{rel("about.html", cur)}">このサイトについて</a></li><li><a href="{rel("privacy.html", cur)}">個人情報保護方針</a></li><li><a href="{rel("contact.html", cur)}">お問い合わせ</a></li></ul>
<small>Copyright (c) 2009 JECOM All Rights Reserved.</small></div>
</div></footer><a class="to-top" href="#top" aria-label="ページの先頭へ">↑</a>'''

def page_shell(cur, title, desc, body, extra_head=""):
    d = H.escape(desc or "", quote=True)
    # A案⇔B案を同じページで切り替えるリンク
    if VARIANT == "b":
        other = os.path.relpath(cur, os.path.dirname("b/" + cur) or ".").replace("\\", "/")
        variant_link = f'<b>B案（動きのあるデザイン）</b>を表示中 → <a href="{other}">A案を見る</a>／'
        b_head = f'''
<link rel="stylesheet" href="{rel("css/b.css", cur)}">
<script>if(!matchMedia('(prefers-reduced-motion: reduce)').matches){{document.documentElement.classList.add('anim');setTimeout(function(){{if(!window.__bOK)document.documentElement.classList.remove('anim')}},4000)}}</script>'''
        b_tail = f'''
<script src="{GSAP}/gsap.min.js"></script>
<script src="{GSAP}/ScrollTrigger.min.js"></script>
<script src="{rel("js/b.js", cur)}"></script>'''
    else:
        variant_link = f'<a href="{rel("b/" + cur, cur)}">B案（動きのあるデザイン）を見る</a>／'
        b_head = b_tail = ""
    return f'''<!DOCTYPE html>
<html lang="ja"{' class="b"' if VARIANT == "b" else ""}><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{H.escape(title)}</title>
<meta name="description" content="{d}">
<meta property="og:title" content="{H.escape(title, quote=True)}">
<meta property="og:type" content="website">
<meta property="og:description" content="{d}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;0,700;1,600&family=Shippori+Mincho+B1:wght@600;700&family=Noto+Sans+JP:wght@400;500;700&family=Zen+Kaku+Gothic+New:wght@500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{rel("css/style.css", cur)}">{b_head}{extra_head}
</head><body id="top">
<div class="demo-bar">これはJECOM株式会社様へのホームページリニューアル提案用のデモです（公式サイトではありません）。{variant_link}<a href="https://www.jecom.jp/" target="_blank" rel="noopener">公式サイト</a>／<a href="{rel("proposal.html", cur)}">提案書</a></div>
{header_html(cur)}
<main>
{body}
</main>
{footer_html(cur)}
<script src="{rel("js/main.js", cur)}"></script>{b_tail}
</body></html>'''

# ---------------------------------------------------------------- 本文変換
RED = re.compile(r"color:\s*(red|#f00\b|#ff0000|#cc0000|#c00\b|#e60012|#ff3300|#cc3300|#ff6600|#dc143c|#b22222|rgb\(\s*255,\s*0,\s*0\s*\)|rgb\(\s*204,\s*0,\s*0\s*\)|rgb\(\s*255,\s*51,\s*0\s*\))", re.I)
BLUE = re.compile(r"color:\s*(blue|#0000ff|#00f\b|#0066cc|#003399|#0033cc|#000080|#3366ff|rgb\(\s*0,\s*0,\s*255\s*\)|rgb\(\s*0,\s*102,\s*204\s*\))", re.I)
BOLD = re.compile(r"font-weight:\s*(bold|700|800|900)", re.I)
MARK = re.compile(r"background(-color)?:\s*(yellow|#ffff00|#ff0|#ffff99|#ffffcc|rgb\(\s*255,\s*255,\s*0\s*\))", re.I)
KEEP_ATTR = {"a": {"href", "id", "target"}, "img": {"src", "alt"}, "td": {"colspan", "rowspan"}, "th": {"colspan", "rowspan"}, "iframe": {"src"}}
DECOR_REPLACE = {
    "selecting_arrow.gif": "arrow", "detail-btn1.gif": "detail", "main_text-banner_3box-01-yellow_button.jpg": "detail",
    "pdf_download.jpg": "pdf", "default-temp_before-arter_yajirushi.jpg": "ba", "dammy-w210.gif": "drop",
}

def norm_internal(href):
    """現行サイトのURLを サイト内パス（先頭/なし）または外部URLに正規化。None=リンクを外す"""
    h = href.strip()
    if h.startswith("javascript:") or h == "":
        return ""
    m = re.match(r"https?://(www\.)?jecom\.jp(/.*)?$", h)
    if m:
        h = m.group(2) or "/"
    if h.startswith(DEAD_EXTERNAL_PREFIX):
        return None
    if h.startswith("http") or h.startswith("mailto:") or h.startswith("tel:"):
        return h
    if h.startswith("#"):
        return h
    if h.startswith("/topic"):
        q = urllib.parse.urlparse(h)
        tid = urllib.parse.parse_qs(q.query).get("id", ["1"])[0]
        return f"topic{tid}.html" + (("#" + q.fragment) if q.fragment else "")
    if h.startswith("/rss"):
        tid = urllib.parse.parse_qs(urllib.parse.urlparse(h).query).get("id", ["1"])[0]
        return f"topic{tid}.html"
    if not h.startswith("/"):
        return h  # 相対（ほぼ無い）
    path, _, frag = h.partition("#")
    if path in BROKEN:
        b = BROKEN[path]
        if b is None:
            return None
        path = b
    if path.endswith("/"):
        path += "index.html"
    path = urllib.parse.unquote(path).lstrip("/")
    return path + ("#" + frag if frag else "")

def is_blank(tag):
    if tag.find(["img", "iframe", "table", "input", "select", "textarea", "video"]):
        return False
    if tag.find(id=True) or (tag.get("id") if isinstance(tag, Tag) and tag.attrs is not None else None):
        return False
    return tag.get_text().replace("\xa0", "").replace("　", "").strip() == ""

def convert(main_html, cur, soup_factory):
    soup = BeautifulSoup(main_html, "html.parser")
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    for t in soup.find_all(["script", "style", "noscript", "link", "meta"]):
        t.decompose()
    # nivo スライダー → 横スクロールのギャラリー
    for w in soup.select("div.slider-wrapper"):
        imgs = w.find_all("img")
        g = soup.new_tag("div", attrs={"class": "gallery"})
        for im in imgs:
            g.append(soup.new_tag("img", attrs={"src": im.get("src", ""), "alt": im.get("alt", "")}))
        w.replace_with(g)
    # 装飾画像の置換
    for im in list(soup.find_all("img")):
        src = im.get("src", "")
        base = urllib.parse.unquote(src.split("/")[-1])
        kind = DECOR_REPLACE.get(base)
        if src.startswith("/track") or "page-up" in src:
            im.decompose(); continue
        if not kind:
            continue
        a = im.find_parent("a")
        if kind == "arrow":
            im.replace_with(soup.new_tag("div", attrs={"class": "flow-arrow", "aria-hidden": "true"}))
        elif kind == "ba":
            s = soup.new_tag("span", attrs={"class": "ba-arrow", "aria-hidden": "true"}); s.string = "→"; im.replace_with(s)
        elif kind == "drop":
            im.decompose()
        elif kind in ("detail", "pdf"):
            if a is None:  # リンクの無いボタン画像（ダミー）→ 削除
                im.decompose(); continue
            s = soup.new_string("PDFをダウンロード" if kind == "pdf" else "詳しく見る")
            im.replace_with(s)
            a["class"] = ["btn", "btn-line", "btn-s"]
    # 地図などの拡大ポップアップ（onclick）
    for a in soup.find_all("a"):
        if a.get("onclick"):
            del a["onclick"]
            a["target"] = "_blank"
    # 名前付きアンカー
    for a in soup.find_all("a"):
        if not a.get("href") and (a.get("name") or a.get("id")):
            nm = a.get("name") or a.get("id")
            sp = soup.new_tag("span", attrs={"id": nm, "class": "anchor"})
            for ch in list(a.contents):
                sp.append(ch)
            a.replace_with(sp)
        elif not a.get("href"):
            a.unwrap()
    # font / span / b 等の整理
    for t in list(soup.find_all(["font", "span", "b", "u", "center", "big", "small", "o:p", "strike", "em", "i"])):
        if t.name in ("span",) and "anchor" in (t.get("class") or []):
            continue
        st = t.get("style", "") or ""
        col = t.get("color", "") or ""
        if t.name == "b":
            t.name = "strong"; t.attrs = {}; continue
        if t.name == "center":
            t.name = "div"; t.attrs = {}; continue
        if t.name in ("em", "i"):
            t.attrs = {}; continue
        cls = None
        if RED.search(st) or re.match(r"(red|#f00|#ff0000|#cc0000)$", col, re.I):
            cls = "t-red"
        elif BLUE.search(st) or re.match(r"(blue|#0000ff|#00f)$", col, re.I):
            cls = "t-blue"
        elif MARK.search(st):
            cls = "t-mark"
        if cls:
            t.name = "span"; t.attrs = {"class": cls}
        elif BOLD.search(st):
            t.name = "strong"; t.attrs = {}
        else:
            t.unwrap()
    # 入れ子の同色 span を解消
    for t in soup.find_all("span", class_=["t-red", "t-blue", "t-mark"]):
        for inner in t.find_all("span", class_=t["class"]):
            inner.unwrap()
    # YouTube
    for f in soup.find_all("iframe"):
        src = f.get("src", "")
        if src.startswith("//"):
            src = "https:" + src
        nf = soup.new_tag("iframe", attrs={"src": src, "title": "動画", "loading": "lazy", "allowfullscreen": "", "allow": "accelerometer; encrypted-media; gyroscope; picture-in-picture", "referrerpolicy": "strict-origin-when-cross-origin"})
        w = soup.new_tag("div", attrs={"class": "video"}); w.append(nf)
        f.replace_with(w)
    # 表：レイアウト用か、データ表か
    tables = soup.find_all("table")
    for tb in reversed(tables):  # 内側から
        convert_table(soup, tb)
    # 属性の整理
    for t in soup.find_all(True):
        if t.name in ("div",) and t.get("class") and any(c in ("gallery", "video", "flow-arrow", "row", "cell", "table-wrap", "media", "card-row", "action") for c in t["class"]):
            t.attrs = {k: v for k, v in t.attrs.items() if k in ("class", "aria-hidden")}
            continue
        if t.name == "span" and t.get("class"):
            t.attrs = {k: v for k, v in t.attrs.items() if k in ("class", "id", "aria-hidden")}
            continue
        if t.name == "iframe":
            continue
        if t.name == "a" and t.get("class"):
            keep = {"href", "class", "target", "id"}
        else:
            keep = KEEP_ATTR.get(t.name, {"id"}) | ({"class"} if t.name in ("table", "tr") and t.get("class") in (["data"], ["head"]) else set())
        t.attrs = {k: v for k, v in t.attrs.items() if k in keep}
    # 見出しを1段階上げる（h3→h2 …）
    for t in soup.find_all(["h3", "h4", "h5", "h6"]):
        t.name = {"h3": "h2", "h4": "h3", "h5": "h4", "h6": "h4"}[t.name]
    # 空段落の削除
    for p in soup.find_all(["p", "div", "h2", "h3", "h4"]):
        if p.decomposed or p.attrs is None:
            continue
        if p.get("class") and any(c in ("flow-arrow", "gallery", "video", "cell", "row") for c in p["class"]):
            continue
        if is_blank(p):
            p.decompose()
    # 連続 br の圧縮・段落先頭の br 削除
    for br in soup.find_all("br"):
        nxt = br.next_sibling
        while isinstance(nxt, NavigableString) and nxt.strip() == "":
            nxt = nxt.next_sibling
        if isinstance(nxt, Tag) and nxt.name == "br":
            br.decompose()
    # リンクと画像のパス
    for a in soup.find_all("a"):
        href = a.get("href")
        if href is None:
            continue
        n = norm_internal(href)
        if n is None:
            if "btn" in (a.get("class") or []):
                a.decompose()
            else:
                a.unwrap()
            continue
        if n == "":
            a.unwrap(); continue
        if n.startswith(("http", "mailto:", "tel:")):
            a["href"] = n
            if n.startswith("http"):
                a["target"] = "_blank"; a["rel"] = "noopener"
        elif n.startswith("#"):
            a["href"] = n
        else:
            a["href"] = rel(n, cur)
            if n.split("#")[0].lower().endswith((".pdf", ".jpg", ".png", ".bmp", ".gif")):
                a["target"] = "_blank"
        if a.find("img") and not a.get_text(strip=True):
            a["class"] = (a.get("class") or []) + ["img-link"]
    for im in soup.find_all("img"):
        src = im.get("src", "")
        n = norm_internal(src)
        if n and not n.startswith("http"):
            im["src"] = rel(n, cur)
        im["loading"] = "lazy"
        if im.get("alt") is None:
            im["alt"] = ""
    # 文字化けしたページ内アンカー（#____）をリンク文字と同じ見出しへ付け替え
    seen = set()
    for t in soup.find_all(id=True):
        if t["id"] in seen:
            k = 2
            while f'{t["id"]}-{k}' in seen: k += 1
            t["id"] = f'{t["id"]}-{k}'
        seen.add(t["id"])
    ids = set(seen)
    heads = soup.find_all(["h2", "h3", "h4"])
    for a in soup.find_all("a", href=re.compile(r"^#")):
        frag = a["href"][1:]
        if frag in ids:
            continue
        txt = re.sub(r"[\s▶・]", "", a.get_text())
        for i, h in enumerate(heads):
            ht = re.sub(r"[\s▶・]", "", h.get_text())
            if txt and (ht == txt or ht.startswith(txt) or txt.startswith(ht)) and ht:
                hid = h.get("id") or f"sec{i+1}"
                h["id"] = hid; a["href"] = "#" + hid; ids.add(hid)
                break
    return soup

def convert_table(soup, tb):
    has_media = tb.find(["img", "iframe"]) or tb.find("div", class_=["gallery", "video", "row"]) or tb.find("table")
    rows = tb.find_all("tr", recursive=True)
    rows = [r for r in rows if r.find_parent("table") is tb]
    if has_media:
        wrap = soup.new_tag("div")
        for r in rows:
            cells = [c for c in r.find_all(["td", "th"], recursive=False)]
            cells = [c for c in cells if not is_blank(c)]
            if not cells:
                continue
            row = soup.new_tag("div", attrs={"class": "row"})
            for c in cells:
                cell = soup.new_tag("div", attrs={"class": "cell"})
                only_media = c.find(["img", "iframe"]) is not None and c.get_text(strip=True) == "" or (
                    len(c.find_all("img")) == 1 and len(c.get_text(strip=True)) < 2)
                is_action = c.find("a", class_="btn") is not None and len(c.get_text(strip=True)) <= 12
                if only_media and not c.find("div", class_="video"):
                    cell["class"] = ["cell", "media"]
                if is_action:
                    cell["class"] = ["cell", "action"]
                for ch in list(c.contents):
                    cell.append(ch)
                row.append(cell)
            if len(cells) == 1:
                for ch in list(row.contents[0].contents):
                    wrap.append(ch)
            else:
                if any("action" in (x.get("class") or []) for x in row.find_all("div", class_="cell", recursive=False)) and \
                   any("media" in (x.get("class") or []) for x in row.find_all("div", class_="cell", recursive=False)):
                    row["class"] = ["row", "card-row"]
                wrap.append(row)
        tb.replace_with(wrap)
        wrap.unwrap()
        return
    # データ表
    ncols = max((len(r.find_all(["td", "th"], recursive=False)) for r in rows), default=0)
    new = soup.new_tag("table", attrs={"class": "data"})
    for i, r in enumerate(rows):
        cells = r.find_all(["td", "th"], recursive=False)
        if not cells or all(is_blank(c) for c in cells):
            continue
        tr = soup.new_tag("tr")
        for j, c in enumerate(cells):
            tag = "td"
            if ncols == 2 and j == 0 and len(cells) == 2:
                tag = "th"
            if ncols >= 3 and i == 0:
                tag = "th"
            cell = soup.new_tag(tag)
            for k in ("colspan", "rowspan"):
                if c.get(k):
                    cell[k] = c[k]
            for ch in list(c.contents):
                cell.append(ch)
            tr.append(cell)
        new.append(tr)
    w = soup.new_tag("div", attrs={"class": "table-wrap"})
    w.append(new)
    tb.replace_with(w)

def apply_text_fixes(html, cur):
    applied = []
    for page, old, new in FIXES:
        if page in ("*", cur) and old in html:
            html = html.replace(old, new); applied.append((cur, old, new))
    for page, s in TODO_MARK:
        if page in ("*", cur) and s in html:
            html = html.replace(s, f'<span class="todo">{s}</span>'); applied.append((cur, s, "TODO"))
    return html, applied

FORM_CACHE = {}
def form_html(form):
    """現行のフォーム（tx_form）の項目をそのまま新デザインのフォームに"""
    rows = []
    for it in form.select(".form-item"):
        label = it.select_one(".label label").get_text(" ", strip=True)
        req = it.select_one(".required") is not None
        field = it.select_one(".field")
        desc = field.select_one("p.description")
        desc_t = desc.get_text(" ", strip=True) if desc else ""
        badge = '<span class="req">必須</span>' if req else '<span class="opt">任意</span>'
        fid = None
        if field.find("textarea"):
            ctl = '<textarea rows="8"></textarea>'
        elif field.find("select"):
            opts = "".join(f"<option>{H.escape(o.get_text(strip=True))}</option>" for o in field.find_all("option"))
            ctl = f"<select>{opts}</select>"
        elif field.find("input", type="radio"):
            name = field.find("input")["name"]
            ch = "".join(f'<label><input type="radio" name="{name}"> {H.escape(l.get_text(strip=True))}</label>' for l in field.find_all("label"))
            ctl = f'<div class="choices">{ch}</div>'
        else:
            inp = field.find("input")
            typ = "email" if inp.get("type") == "email" else "text"
            ph = desc_t if desc_t.startswith("(例)") else ""
            ctl = f'<input type="{typ}" placeholder="{H.escape(ph.replace("(例)", "例）"))}">'
            if ph:
                desc_t = ""
        d = f'<p class="desc">{H.escape(desc_t)}</p>' if desc_t else ""
        rows.append(f'<div class="f-row"><label class="l">{H.escape(label)} {badge}</label><div>{ctl}{d}</div></div>')
    return ('<form class="form" action="#" method="post">' + "".join(rows) +
            '<div class="submit"><button class="btn btn-primary" type="submit">送　信</button><p class="demo-note">※デモサイトのため送信はされません</p></div></form>')

def extract_main(src):
    m = re.search(r'<div id="main-contents">(.*?)<!-- /メインコンテンツ', src, re.S)
    return m.group(1) if m else ""

def page_hero(cur, title, eyebrow_text, kicker=""):
    sec = section_of(cur)
    crumbs = [f'<a href="{rel("index.html", cur)}">HOME</a>']
    if cur != sec["hub"]:
        crumbs.append(f'<a href="{rel(sec["hub"], cur)}">{sec["hub_title"]}</a>')
    if cur in PRODUCT_PAGES:
        parent = PRODUCT_PAGES[cur]
        pt = dict(sec["children"]).get(parent, "")
        crumbs.append(f'<a href="{rel(parent, cur)}">{pt}</a>')
    if cur.startswith(("bousai-info/", "bousi-info/")):
        pass
    crumbs.append(f"<span>{H.escape(title)}</span>")
    ck = '<span class="sep">/</span>'.join(crumbs)
    k = f'<p class="kicker">{H.escape(kicker)}</p>' if kicker else ""
    return f'''<section class="page-hero"><div class="container"><nav class="crumb" aria-label="パンくず">{ck}</nav>
<span class="eyebrow">{eyebrow_text}</span><h1>{H.escape(title)}</h1>{k}</div></section>'''

def side_html(cur):
    sec = section_of(cur)
    items = [(sec["hub"], sec["hub_title"])] + [c for c in sec["children"] if c[0] != sec["hub"]]
    if sec is INFO_SECTION and cur.startswith(("bousai-info/", "bousi-info/")):
        items = [("bousai-info.html", "都道府県防災情報")] + [((f"bousi-info/{k}.html" if k == "fukuoka" else f"bousai-info/{k}.html"), n) for k, n in PREFS]
    active = PRODUCT_PAGES.get(cur, cur)
    lis = "".join(f'<li><a href="{rel(p, cur)}"{" class=\"on\"" if p == active else ""}>{t}</a></li>' for p, t in items)
    extra = ""
    sub = [(p, t) for p, t in ORIG_SUB.get(cur, []) if p not in {x for x, _ in items}]
    if sub:
        parent = PRODUCT_PAGES.get(cur, cur)
        head = "このカテゴリの商品" if sec["key"] == "products" else "関連ページ"
        extra = f'<h2 style="margin-top:22px">{head}</h2><ul>' + "".join(
            f'<li><a href="{rel(p, cur)}"{" class=\"on\"" if p == cur else ""}>{t}</a></li>' for p, t in sub) + "</ul>"
    return f'''<aside class="side"><div class="side-inner"><h2>{sec["label"].upper() if sec["key"]=="qa" else sec["label"]}</h2><ul>{lis}</ul>{extra}
<div class="side-cta"><strong>ご相談・お見積</strong>お電話でもお気軽にどうぞ。<a class="tel" href="tel:{TEL}">{TEL}</a>営業時間：{HOURS}<a class="btn btn-primary btn-s" href="{rel("contact.html", cur)}">お問い合わせフォーム</a></div>
</div></aside>'''

def hub_cards(cur):
    sec = section_of(cur)
    if cur != sec["hub"] or cur in ("eco_bus/index.html",):
        return ""
    thumbs = THUMBS
    cards = []
    for p, t in sec["children"]:
        th = thumbs.get(p)
        img = f'<div class="thumb"><img src="{rel(th, cur)}" alt="" loading="lazy"></div>' if th else ""
        cards.append(f'<a class="card" href="{rel(p, cur)}">{img}<div class="body"><h3>{t}</h3><span class="more">詳しく見る →</span></div></a>')
    return f'<h2>{sec["hub_title"]}のページ一覧</h2><div class="cards">{"".join(cards)}</div>'

THUMBS = {
    "annzenn/riskninnchi.html": "asset/00032/office/office_graph.jpg",
    "annzenn/office.html": "asset/00032/office/office_photo1.jpg",
    "dutyofcare.html": "asset/00032/toppage/main-bcp.jpg",
    "annzen/selfcheck.html": "asset/00032/office/selfcheck-1.jpg",
    "annzenn/damper.html": "asset/00032/office/damper_zu1.jpg",
    "bousaikanritenken.html": "asset/00032/office/seishinoffice2.jpg",
    "seisinoffice/about.html": "asset/00032/office/seishinoffice3.jpg",
    "jisya_toritsuke.html": "asset/00032/seishin/cost_low_photo.jpg",
    "chosa_sindan.html": "asset/00032/seishin/sinndannkekkareport2.jpg",
    "chousa_sindan_ex.html": "asset/00032/seishin/jinnzaikennshuu_buil.jpg",
    "sekou_service.html": "asset/00032/office/seishinoffice2.jpg",
    "seishin/jikkendouga.html": "asset/00032/office/office_photo1.jpg",
    "shouhinn/damper.html": "asset/00032/syouhin/KTT003-007/KTTshuugou.jpg",
    "shouhinn/jecomselect-flooddamageescape.html": "asset/00032/syouhin/suinoukun2.jpg",
    "shouhinn/jecomselect/sanitarygoods.html": "asset/00032/syouhin/sanita.jpg",
    "shouhinn/jecomselect/foods.html": "asset/00032/syouhin/D3_3.jpg",
    "shouhinn/all.html": "asset/00032/syouhin/KTTshuugou.jpg",
    "ichioshi.html": "asset/00032/syouhin/Cube-Completed2_2402-2_2.jpg",
    "qa_seshin.html": "asset/00032/qa/qa_photo1.jpg",
    "qa_secchi.html": "asset/00032/office/seishinoffice2.jpg",
    "qa_bousai.html": "asset/00032/syouhin/D3_3.jpg",
    "checkpoint.html": "asset/00032/mitsumori/illustration_1.jpg",
    "gaisan/simulation.html": "asset/00032/toppage/main-gaisan.jpg",
    "partner2/index.html": "asset/00032/seishin/KTT-001J-1.jpg",
}

def en_label(cur):
    return section_of(cur)["en"]

# ---------------------------------------------------------------- お知らせ一覧
def topic_page(cur, src, all_applied):
    main = extract_main(src)
    soup = BeautifulSoup(main, "html.parser")
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    h3 = soup.find("h3")
    title = h3.get_text(strip=True) if h3 else "お知らせ"
    items = []
    seen_ids = set()
    for dt in soup.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        ds = dt.find("span", class_="date")
        date = ds.get_text(strip=True) if ds else ""
        ttl = dt.find("strong").get_text(" ", strip=True) if dt.find("strong") else dt.get_text(" ", strip=True).replace(date, "")
        body = convert(str(dd.decode_contents()) if dd else "", cur, None)
        for sep in body.select("div.topic-sepalator"):
            sep.decompose()
        bhtml = str(body).strip()
        did = dt.get("id", "")
        if did in seen_ids:
            did = f"{did}-2"
        seen_ids.add(did)
        items.append(f'<details class="news-item" id="{did}"><summary><span class="date">{date}</span><span class="ttl">{H.escape(ttl)}</span></summary><div class="content">{bhtml}</div></details>')
    html = f'<div class="news-list">{"".join(items)}</div>'
    hs = BeautifulSoup(html, "html.parser"); seen = set()
    for t in hs.find_all(id=True):
        if t["id"] in seen:
            if t.name == "details":
                pass
            t["id"] = t["id"] + "-b"
        seen.add(t["id"])
    html = str(hs)
    html, ap = apply_text_fixes(html, cur); all_applied += ap
    ptitle = f"{title} | 防災用品　制震オフィス　KTTシリーズ　ＪＥＣＯＭ株式会社"
    body = page_hero(cur, title, "Information") + f'<div class="container layout">{side_html(cur)}<article class="article">{html}</article></div>' + cta_html(cur) + resources_html(cur)
    return ptitle, body

# ---------------------------------------------------------------- メイン
ORIG_SUB = {}
def load_orig_sub():
    for url, d in info.items():
        if "file" not in d:
            continue
        path = urllib.parse.urlparse(url).path.lstrip("/")
        src = open(os.path.join(RAW, d["file"]), encoding="utf-8").read()
        m = re.search(r'<div id="sub-menu">(.*?)</div>\s*<!-- /サブメニュー', src, re.S)
        if not m:
            continue
        items = []
        for h, t in re.findall(r'<a href="([^"]+)"[^>]*>\s*<span>(.*?)</span>', m.group(1), re.S):
            n = norm_internal(h)
            if n and not n.startswith("http"):
                items.append((n.split("#")[0], re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", t))).strip()))
        ORIG_SUB[path] = items

def build():
    load_orig_sub()
    all_applied = []
    pages = {}
    for url, d in info.items():
        if "file" not in d:
            continue
        path = urllib.parse.urlparse(url).path.lstrip("/")
        pages[path] = d["file"]
    pages["topic1.html"] = "topic1.html"
    pages["topic2.html"] = "topic2.html"
    written = []
    for path, fname in pages.items():
        src = open(os.path.join(RAW, fname), encoding="utf-8").read()
        mt = re.search(r"<title>(.*?)</title>", src, re.S)
        ptitle = mt.group(1).strip() if mt else "ＪＥＣＯＭ株式会社"
        md = re.search(r'<meta name="description" content="(.*?)"', src, re.S)
        desc = re.sub(r"\s+", "", md.group(1)) if md else ""
        partial = os.path.join(PARTS, path.replace("/", "__"))
        if os.path.exists(partial):
            body = open(partial, encoding="utf-8").read()
            body = render_partial(body, path)
            body, ap = apply_text_fixes(body, path); all_applied += ap
        elif path.startswith("topic"):
            ptitle, body = topic_page(path, src, all_applied)
        else:
            main = extract_main(src)
            # 現行のリンク先の誤り：商品一覧「7年保存クッキー3日分セット」→ レトルト食品のページになっている
            if path == "shouhinn/all.html":
                i = main.find("S3_2.jpg"); j = main.find("/shouhinn/jecomselect/7yearsrice.html", i)
                assert i > 0 and j > 0
                main = main[:j] + "/shouhinn/jecomselect/7years_set.html" + main[j + len("/shouhinn/jecomselect/7yearsrice.html"):]
            # フォームは変換前に新デザインのHTMLを作っておき、目印に置き換える
            pre = BeautifulSoup(main, "html.parser")
            forms = []
            for f in pre.find_all("form"):
                forms.append(form_html(f))
                f.replace_with(BeautifulSoup(f"<p>@@FORM{len(forms)-1}@@</p>", "html.parser"))
            soup = convert(str(pre), path, None)
            for el in soup.find_all(string=re.compile("フォームを送信するにはJavaScriptをONにしてください")):
                el.extract()
            # ページタイトル（最初の h2 = 元の h3）と、その前の短い前置き（キッカー）
            first = soup.find("h2")
            title = first.get_text(" ", strip=True) if first else ptitle.split("|")[0].strip()
            kicker = ""
            if first:
                prev = []
                for el in list(first.find_all_previous(string=True)):
                    if el.find_parent("h2") is first:
                        continue
                    prev.append(el)
                txt = "".join(reversed([p.strip() for p in prev])).strip()
                parent_links = first.find_all_previous("a")
                if txt and len(txt) <= 40 and not parent_links:
                    kicker = txt
                    pars = [getattr(p, "parent", None) for p in prev]
                    for p in prev:
                        p.extract()
                    for par in pars:
                        while par is not None and not par.decomposed and par.name not in (None, "[document]") and is_blank(par):
                            up = par.parent; par.decompose(); par = up
                for anc in first.find_all(id=True):
                    sp = soup.new_tag("span", attrs={"id": anc["id"], "class": "anchor"})
                    first.insert_before(sp)
                first.decompose()
            if not title:
                title = ptitle.split("|")[0].strip()
            html = str(soup)
            html, ap = apply_text_fixes(html, path); all_applied += ap
            for i, fh in enumerate(forms):
                assert f"@@FORM{i}@@" in html, path
                html = html.replace(f"<p>@@FORM{i}@@</p>", fh).replace(f"@@FORM{i}@@", fh)
            html += hub_cards(path)
            body = page_hero(path, title, en_label(path), kicker) + \
                f'<div class="container layout">{side_html(path)}<article class="article">{html}</article></div>' + \
                cta_html(path) + resources_html(path)
        out = os.path.join(OUT, "b" if VARIANT == "b" else "", path)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(page_shell(path, ptitle, desc, body))
        written.append(path)
    json.dump(all_applied, open(os.path.join(ROOT, "raw", "applied_fixes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    used = {(o) for _, o, _ in all_applied}
    for page, old, new in FIXES:
        if old not in used:
            print("!! FIX not applied:", page, old)
    for page, s in TODO_MARK:
        if s not in used:
            print("!! TODO not applied:", page, s)
    print(len(written), "pages written", "(B案 site/b/)" if VARIANT == "b" else "")

def render_partial(body, cur):
    """partials 内の {{rel:path}} {{cta}} {{resources}} {{hero:...}} を展開"""
    body = re.sub(r"\{\{rel:([^}]+)\}\}", lambda m: rel(m.group(1), cur), body)
    body = body.replace("{{cta}}", cta_html(cur)).replace("{{resources}}", resources_html(cur)).replace("{{tiles}}", tiles_html(cur))
    body = re.sub(r"\{\{news:(\d)\}\}", lambda m: news_list_html(m.group(1), cur), body)
    body = body.replace("{{side}}", side_html(cur)).replace("{{hubcards}}", hub_cards(cur))
    body = re.sub(r"\{\{hero:([^|}]*)\|([^|}]*)\|?([^}]*)\}\}", lambda m: page_hero(cur, m.group(1), m.group(2), m.group(3)), body)
    return body

if __name__ == "__main__":
    build()
    VARIANT = "b"
    build()
