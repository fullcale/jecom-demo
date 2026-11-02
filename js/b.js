// B案：動き（GSAP + ScrollTrigger）。メニュー・スライドショー・フォームは main.js
// main.js と同じページで読むので、全体を { } で囲んで変数名の衝突を避ける
{
const root = document.documentElement;
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const header = document.querySelector('.site-header');
const hero = document.querySelector('.hero');

// ---------- ヘッダー：下にスクロールで隠れ、上に戻すと出る ----------
let lastY = scrollY;
function onScroll() {
  const y = scrollY;
  header.classList.toggle('is-scrolled', y > 10);
  const open = document.body.classList.contains('nav-open');
  header.classList.toggle('is-hidden', !open && y > lastY && y > 400);
  lastY = y;
}
addEventListener('scroll', onScroll, { passive: true });
onScroll();

// ---------- 文字を1文字ずつ span に分ける（em などの入れ子は保つ） ----------
// 英単語は単語ごと、閉じかっこ・句読点は前の文字とくっつけて、行頭に来ないようにする
const CLOSE = '、。，．」』）】〉》？！ー…・,.!?):;';
const OPEN = '「『（【〈《(';
function splitChars(el) {
  if (el.dataset.split) return el.querySelectorAll('.ch');
  el.dataset.split = '1';
  el.setAttribute('aria-label', el.textContent.replace(/\s+/g, ' ').trim());
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach((node) => {
    const text = node.textContent;
    if (!text.trim()) return;
    const tokens = [];
    let pendingOpen = '';
    for (const c of text) {
      const last = tokens[tokens.length - 1];
      if (/\s/.test(c)) { tokens.push(' '); continue; }
      if (OPEN.includes(c)) { pendingOpen += c; continue; }
      const latin = /[A-Za-z0-9&'’\-]/.test(c);
      if (last && last !== ' ' && (CLOSE.includes(c) || (latin && /[A-Za-z0-9&'’\-]$/.test(last)))) {
        tokens[tokens.length - 1] = last + c;
      } else {
        tokens.push(pendingOpen + c);
        pendingOpen = '';
      }
    }
    if (pendingOpen) tokens.push(pendingOpen);
    const frag = document.createDocumentFragment();
    tokens.forEach((t) => {
      if (t === ' ') { frag.appendChild(document.createTextNode(' ')); return; }
      const w = document.createElement('span');
      w.className = 'w';
      w.style.cssText = 'display:inline-block;white-space:nowrap';
      w.setAttribute('aria-hidden', 'true');
      for (const c of t) {
        const s = document.createElement('span');
        s.className = 'ch';
        s.style.display = 'inline-block';
        s.textContent = c;
        w.appendChild(s);
      }
      frag.appendChild(w);
    });
    node.replaceWith(frag);
  });
  return el.querySelectorAll('.ch');
}

// ---------- 地震計の波形（揺れが始まり、ダンパーで収まって平らになる） ----------
function wavePath(w, h) {
  const mid = h / 2;
  let d = `M0 ${mid}`;
  for (let x = 0; x <= w; x += 3) {
    const t = x / w;
    let amp = 0;
    if (t > .16 && t < .2) amp = (t - .16) / .04;           // 揺れ始め
    else if (t >= .2) amp = Math.exp(-(t - .2) * 9);         // ダンパーで減衰
    const y = mid + Math.sin(x * .19) * Math.cos(x * .053) * amp * mid * .92;
    d += ` L${x} ${y.toFixed(1)}`;
  }
  return d;
}
function waveSVG(w, h) {
  return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><path d="${wavePath(w, h)}"/></svg>`;
}

// ---------- GSAP ----------
if (!window.gsap || !window.ScrollTrigger || reduce) {
  root.classList.remove('anim');
} else {
  gsap.registerPlugin(ScrollTrigger);

  // スクロール量のバー
  const bar = document.createElement('div');
  bar.className = 'b-progress';
  document.body.appendChild(bar);
  gsap.to(bar, { scaleX: 1, ease: 'none', scrollTrigger: { start: 0, end: 'max', scrub: .3 } });

  const tl = gsap.timeline();

  // オープニング（トップ・セッション中1回だけ）
  if (hero && !sessionStorage.getItem('jecom-b-opened')) {
    sessionStorage.setItem('jecom-b-opened', '1');
    const open = document.createElement('div');
    open.className = 'b-open';
    open.setAttribute('aria-hidden', 'true');
    open.innerHTML = `<img src="${document.querySelector('.logo img').src}" alt="">${waveSVG(600, 60)}`;
    document.body.appendChild(open);
    tl.to(open.querySelector('img'), { opacity: 1, y: 0, duration: .6, ease: 'power2.out' })
      .fromTo(open.querySelector('svg'), { clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)', duration: 1.1, ease: 'power2.inOut' }, '-=.25')
      .to(open, { clipPath: 'inset(0 0 100% 0)', duration: .9, ease: 'power4.inOut' }, '+=.1')
      .add(() => open.remove());
  }

  // ヒーロー：見出しがせり上がり → 写真が「揺れて、止まる」 → 震度7のバッジ
  if (hero) {
    const text = hero.querySelector('.container>div:first-child');
    const visual = hero.querySelector('.hero-visual');
    const card = visual.querySelector('.main');
    const wave = document.createElement('div');
    wave.className = 'b-wave';
    wave.innerHTML = waveSVG(1200, 70);
    hero.appendChild(wave);
    const ripples = [0, 1, 2].map(() => { const r = document.createElement('i'); r.className = 'b-ripple'; visual.appendChild(r); return r; });

    const h1chars = splitChars(text.querySelector('h1'));
    const eyeChars = splitChars(text.querySelector('.eyebrow'));
    gsap.set([text, visual], { visibility: 'visible' });
    window.__bOK = true;
    tl.from(eyeChars, { yPercent: 100, opacity: 0, duration: .8, ease: 'power3.out', stagger: .025 }, tl.duration() ? '-=.45' : 0)
      .from(h1chars, { yPercent: 110, rotate: 8, opacity: 0, duration: 1, ease: 'power4.out', stagger: .035 }, '<.1')
      .from(text.querySelectorAll('.lead, .btns'), { y: 26, opacity: 0, duration: .9, ease: 'power3.out', stagger: .12 }, '-=.7')
      .from(card, { y: 50, opacity: 0, scale: .94, duration: 1, ease: 'power3.out' }, '-=.9')
      // 揺れ（地震）→ だんだん小さくなって止まる（ダンパー）
      .to(card, { keyframes: { x: [0, -16, 14, -11, 9, -6, 4, -2, 1, 0], rotate: [0, -1.4, 1.2, -.9, .7, -.45, .3, -.15, .05, 0] }, duration: 1.5, ease: 'none' }, '-=.15')
      .fromTo(ripples, { scale: .4, opacity: .9 }, { scale: 1.9, opacity: 0, duration: 1.4, ease: 'power2.out', stagger: .22 }, '<')
      .fromTo(wave, { clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)', duration: 1.8, ease: 'power1.inOut' }, '<-.25')
      .from(visual.querySelector('.badge'), { scale: 0, rotate: -40, duration: .8, ease: 'back.out(2.2)' }, '-=.9')
      .from(visual.querySelector('.chip'), { y: -18, opacity: 0, duration: .6, ease: 'power3.out' }, '-=.55');

    // スクロールで文字と写真が少しずれて流れる
    gsap.to(text, { yPercent: -10, opacity: .3, ease: 'none', scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true } });
    gsap.to(visual, { yPercent: -6, ease: 'none', scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true } });

    // PC：背景の光がマウスについてくる
    if (matchMedia('(hover: hover)').matches) {
      hero.addEventListener('pointermove', (e) => {
        const r = hero.getBoundingClientRect();
        gsap.to(hero, { '--gx': ((e.clientX - r.left) / r.width * 100) + '%', '--gy': ((e.clientY - r.top) / r.height * 100) + '%', duration: 1.2, ease: 'power2.out' });
      });
    }
  }

  // 数字のカウントアップ（818gal・8年・3段階）
  document.querySelectorAll('.stat .v').forEach((v) => {
    const node = v.firstChild;
    if (!node || node.nodeType !== 3 || !/^\d+$/.test(node.textContent.trim())) return;
    const end = Number(node.textContent.trim());
    const obj = { n: 0 };
    gsap.to(obj, { n: end, duration: end > 100 ? 2 : 1.2, ease: 'power2.out', scrollTrigger: { trigger: v, start: 'top 90%' },
      onStart: () => { node.textContent = '0'; }, onUpdate: () => { node.textContent = Math.round(obj.n); } });
  });

  // 英字の小見出し：1文字ずつ下から
  document.querySelectorAll('.eyebrow').forEach((el) => {
    if (el.closest('.hero')) return;
    gsap.from(splitChars(el), { yPercent: 100, opacity: 0, duration: .8, ease: 'power3.out', stagger: .03, scrollTrigger: { trigger: el, start: 'top 90%' } });
  });

  // 大見出し：下から幕が上がるように
  document.querySelectorAll('.sec-head h2, .cta-band h2, .resources h2').forEach((el) => {
    gsap.fromTo(el, { clipPath: 'inset(0 0 100% 0)', y: 36 }, { clipPath: 'inset(0 0 0% 0)', y: 0, duration: 1.2, ease: 'power4.out',
      scrollTrigger: { trigger: el, start: 'top 90%' }, onComplete: () => gsap.set(el, { clearProps: 'clipPath' }) });
  });

  // ブロック・カード：順番にふわっと
  const batchIn = (sel, opts = {}) => {
    const els = gsap.utils.toArray(sel).filter((el) => !el.closest('.hero'));
    if (!els.length) return;
    gsap.set(els, { opacity: 0, y: opts.y ?? 56 });
    ScrollTrigger.batch(els, { start: 'top 92%', once: true,
      onEnter: (b) => gsap.to(b, { opacity: 1, y: 0, duration: 1, ease: 'power3.out', stagger: opts.stagger ?? .12, overwrite: true }) });
  };
  batchIn('.reveal:not(.sec-head)');
  batchIn('.stat', { y: 30 });
  batchIn('.tile', { stagger: .07 });
  batchIn('.card');
  batchIn('.side li', { y: 14, stagger: .04 });
  batchIn('.article h2, .article h3', { y: 20 });

  // 写真が窓から広がる
  document.querySelectorAll('.risk .ph, .path .ph, .case-meta img').forEach((ph) => {
    const st = { trigger: ph, start: 'top 88%' };
    gsap.fromTo(ph, { clipPath: 'inset(14% 14% 14% 14%)' }, { clipPath: 'inset(0% 0% 0% 0%)', duration: 1.4, ease: 'power4.out', scrollTrigger: st });
    const img = ph.tagName === 'IMG' ? null : ph.querySelector('img');
    if (img) gsap.from(img, { scale: 1.3, duration: 1.8, ease: 'power3.out', scrollTrigger: st });
  });

  // 番号（01〜05）が横から
  document.querySelectorAll('.pillar .no').forEach((n) => {
    gsap.from(n, { x: 40, opacity: 0, duration: 1.1, ease: 'power3.out', scrollTrigger: { trigger: n, start: 'top 90%' } });
  });

  // 設置事例：Before のあと After が横から重なる
  document.querySelectorAll('.case .after').forEach((a) => {
    gsap.fromTo(a, { clipPath: 'inset(0 0 0 100%)' }, { clipPath: 'inset(0 0 0 0%)', duration: 1.1, ease: 'power3.inOut', delay: .35,
      scrollTrigger: { trigger: a, start: 'top 88%' } });
  });

  // 下層ページ：見出しが1文字ずつ、パンくず・前置きが続く
  const pageH1 = document.querySelector('.page-hero h1');
  if (pageH1) {
    gsap.from(splitChars(pageH1), { yPercent: 70, opacity: 0, duration: .9, ease: 'power3.out', stagger: .03 });
    gsap.from('.page-hero .breadcrumb, .page-hero .kicker, .page-hero .eyebrow', { opacity: 0, y: 14, duration: .9, delay: .25, ease: 'power2.out' });
  }

  // 下層ページの本文写真：窓から広がる（小さい画像・スライドショーは除く）
  gsap.utils.toArray('.article img').slice(0, 80).forEach((img) => {
    if (img.closest('.slider, .card, a.tile') || (img.complete && img.naturalWidth && img.naturalWidth < 160)) return;
    gsap.fromTo(img, { clipPath: 'inset(10% 10% 10% 10%)', opacity: 0 }, { clipPath: 'inset(0% 0% 0% 0%)', opacity: 1, duration: 1.2, ease: 'power4.out',
      scrollTrigger: { trigger: img, start: 'top 92%' }, onComplete: () => gsap.set(img, { clearProps: 'clipPath' }) });
  });

  // 画像の読み込みで高さが変わるので、読み込み後に位置を測り直す
  addEventListener('load', () => ScrollTrigger.refresh());
}
}
