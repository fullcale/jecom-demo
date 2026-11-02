// Chrome DevTools Protocol で全ページを開き、JSエラー・読み込めない画像・横はみ出し・メニュー動作を確認する
// 使い方: node tools/cdp_check.mjs
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SITE = path.join(ROOT, "site");
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9333;

const pages = [];
(function walk(d) { for (const f of fs.readdirSync(d)) { const p = path.join(d, f); if (fs.statSync(p).isDirectory()) walk(p); else if (f.endsWith(".html")) pages.push(path.relative(SITE, p).replaceAll("\\", "/")); } })(SITE);

const prof = path.join(ROOT, "raw", "shots", "cdpprof");
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", `--remote-debugging-port=${PORT}`, `--user-data-dir=${prof}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 50; i++) { try { const r = await fetch(`http://127.0.0.1:${PORT}/json`); const j = await r.json(); target = j.find((t) => t.type === "page"); if (target) break; } catch {} await sleep(200); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map(); const events = [];
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else events.push(d); };
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
await send("Page.enable"); await send("Runtime.enable"); await send("Log.enable"); await send("Network.enable");

const evalJS = async (expr) => (await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true })).result?.result?.value;
const results = [];
for (const width of [390, 1280]) {
  await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 600 });
  for (const p of pages) {
    events.length = 0;
    const url = pathToFileURL(path.join(SITE, p)).href;
    await send("Page.navigate", { url });
    for (let i = 0; i < 60; i++) { if (events.some((e) => e.method === "Page.loadEventFired")) break; await sleep(100); }
    await sleep(150);
    const info = await evalJS(`(() => {
      const w = window.innerWidth, sw = document.documentElement.scrollWidth, over = [];
      if (sw > w + 1) document.querySelectorAll('body *').forEach(el => { const r = el.getBoundingClientRect(); if (r.right > w + 2 && r.width > 0 && !el.closest('.gallery,.table-wrap,.gnav')) over.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right)); });
      const broken = [...document.images].filter(im => im.complete && im.naturalWidth === 0 && im.loading !== 'lazy').map(im => im.getAttribute('src'));
      return { sw, w, over: over.slice(0, 6), broken };
    })()`);
    const errs = events.filter((e) => e.method === "Runtime.exceptionThrown").map((e) => e.params.exceptionDetails.exception?.description || e.params.exceptionDetails.text);
    const netfail = events.filter((e) => e.method === "Network.loadingFailed" && !/fonts\.g|youtube|google/.test(JSON.stringify(e.params))).map((e) => e.params.errorText + " " + (e.params.requestId));
    const failedReq = events.filter((e) => e.method === "Network.responseReceived" && e.params.response.status >= 400).map((e) => e.params.response.status + " " + e.params.response.url);
    results.push({ p, width, ...info, errs, netfail, failedReq });
  }
}
// メニュー動作（スマホ）
await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 900, deviceScaleFactor: 1, mobile: true });
events.length = 0;
await send("Page.navigate", { url: pathToFileURL(path.join(SITE, "ktt_003j.html")).href });
await sleep(1200);
const menu = await evalJS(`(() => { const b = document.querySelector('.menu-btn'); b.click(); const open = document.body.classList.contains('nav-open'); const nav = document.querySelector('.gnav').getBoundingClientRect(); const first = document.querySelector('.gnav>.item>a'); first.click(); const sub = getComputedStyle(document.querySelector('.gnav>.item .drop')).display; return { open, navLeft: Math.round(nav.left), sub }; })()`);
await sleep(300);
const menuTransform = await evalJS(`Math.round(document.querySelector('.gnav').getBoundingClientRect().left)`);
// お知らせのアンカーで開くか
await send("Page.navigate", { url: pathToFileURL(path.join(SITE, "topic1.html")).href + "#47" });
await sleep(1200);
const det = await evalJS(`document.getElementById('47') && document.getElementById('47').open`);
// フォームが送信されないか
await send("Page.navigate", { url: pathToFileURL(path.join(SITE, "contact.html")).href });
await sleep(1200);
const form = await evalJS(`(() => { window.alert = (m) => { window.__al = m; }; const f = document.querySelector('form.form'); f.requestSubmit(); return { alerted: window.__al || null, url: location.href.endsWith('contact.html') }; })()`);

const bad = results.filter((r) => r.over?.length || r.broken?.length || r.errs.length || r.failedReq.length || r.netfail.length || r.sw > r.w + 1);
console.log(JSON.stringify({ checked: results.length, bad, menu: { ...menu, navLeftAfter: menuTransform }, newsAnchorOpens: det, form }, null, 1));
ws.close(); chrome.kill();
process.exit(0);
