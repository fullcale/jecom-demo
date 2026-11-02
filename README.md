# JECOM株式会社 HPリニューアル提案（デモサイト）

現行サイト https://www.jecom.jp/ の全ページを新デザインで作り直したデモと提案書。

## 構成
- `site/` … 公開用一式（ブラウザで `site/index.html` / `site/proposal.html` を開けば見られる）
  - URLは現行と同じパス（`office.html`, `shouhinn/damper.html` など）。お知らせ `/topic?id=1` は `topic1.html`、防災情報 `/topic?id=2` は `topic2.html`
  - `asset/` は現行サイトからダウンロードした画像・PDF（116MB）
  - 全ページ noindex
- `raw/` … 現行サイトのクロール結果（`pages/`=HTML、`extract/`=本文テキスト）、スクリーンショット、検証レポート
- `tools/`
  - `crawl.py` 現行サイトの全ページ取得 → `extract.py` 本文テキスト化
  - `build.py` 生成スクリプト。現行の本文HTMLを整形して新テンプレートに流し込む。`python tools/build.py`
    - 手作りページは `tools/partials/`（`index.html`=トップ、`eco_bus__index.html`=商品紹介）
    - `FIXES`=誤字修正（提案書の一覧と同じ）、`TODO_MARK`=要確認の黄色マーカー、`BROKEN`=現行のリンク切れの扱い
  - `verify.py` 現行とデモの照合（文字・画像・動画・デモ内リンク切れ）→ `raw/verify_report.txt`
  - `check2.py` 重複ID・ページ内リンク・title・リンク文字とリンク先の食い違い
  - `cdp_check.mjs` Chrome DevToolsで全ページを390px/1280pxで開き、JSエラー・はみ出し・画像・メニュー/フォーム動作を確認（`node tools/cdp_check.mjs`）
  - `shot.sh` / `shot_sp.sh` スクリーンショット（Chrome headless。スマホは iframe で390px）
- 依存：Python 3 + beautifulsoup4 + Pillow

## 検証結果（2026-11-02）
- 文字 3,972行中 未検出4行（いずれも意図した修正：誤字「150lg」×2、入力例の表記×2）、画像 326点すべて掲載、デモ内リンク切れ 0件
- 現行の外部リンク 373件中 158件が開けない（404=122、5xx=6、接続不可=30）。大半は都道府県防災情報の自治体ページ

- 2回目の確認（同日）：現行の商品ページにあったカテゴリ別サイドメニューが抜けていた（7年保存レトルトおかず・シートイレビズに入口が無かった）→ サイドバーに「このカテゴリの商品」として復元。ページ内アンカーの消失も修正。全ページJSエラー・はみ出し0件
- 現行側の誤り：Q&A「商品特長」「現状調査にかかる費用」のページ内リンク不良（後者は回答なし）、商品一覧「7年保存クッキー3日分セット」のリンク先がレトルト食品 → デモでは7years_set.htmlへ修正

## 意図的に外したもの
- 概算見積シミュレーションのサイドバナー（サービス終了済み。ページ自体は残している）
- ヘッダーの「購入サイト」ボタン（現行でもリンク先なし）
- iタウンページ「ビズメール」のブログへのリンク（つながらない。文字は残す）
- 現行の404リンク：初期消火・避難具、10年保存クッキー3日分セット → リンクを外す／旧テレビ用シート → KTT-007J（要確認）／7years_shasaiset → 7years_shasaiset2

## 公開（2026-11-02）
- 提案書 https://fullcale.github.io/jecom-demo/proposal.html ／ デモ https://fullcale.github.io/jecom-demo/
- リポジトリ fullcale/jecom-demo（公開）。更新手順：`python tools/build.py` → commit → `git subtree split --prefix site -b gh-pages` → `git push -f origin gh-pages`
- 全ページnoindex＋robots.txt、上部に「提案用デモ・公式サイトではありません」の帯
