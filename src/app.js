const DATA = window.DATA;
window.APP_READY = true;
// 根目錄的頁面 BASE 是空字串；項目頁在子資料夾裡，BASE 是 "../"
const BASE = document.documentElement.dataset.base || "";
const PAGE_ITEM = document.documentElement.dataset.item || "";
const itemHref = id => `${BASE}${id}/`;
const $ = (s, el = document) => el.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));


// 中文翻譯在 zh.json（build.py 放進 data.js）
const { labels: LABELS, modes: MODES, values: VALUES } = DATA.zh;

function label(key) {
  let mode = "";
  const m = key.match(/^@([^.]+)\.(.*)$/);
  if (m) { mode = MODES[m[1]] || m[1]; key = m[2]; }
  let t = LABELS[key];
  if (!t) {
    const parts = key.split(".");
    t = parts.map(p => LABELS[p] || humanize(p)).join(" · ");
  }
  return mode ? `${t}（${mode}）` : t;
}
const NAMES = Object.fromEntries(Object.values(DATA.items).map(i => [i.en.replace(/[^A-Za-z]/g, "").toLowerCase(), i.zh]));
function humanize(k) {
  const z = NAMES[k.toLowerCase()];
  if (z) return z;
  return k.replace(/([a-z0-9])([A-Z])/g, "$1 $2").replace(/_/g, " ").replace(/^./, c => c.toUpperCase());
}
function value(v) {
  if (v === null || v === undefined || v === "") return "";
  if (typeof v === "string") return VALUES[v] ?? v;
  if (typeof v === "boolean") return VALUES[v];
  return v;
}

let discount = 0;
try { discount = +localStorage.getItem("coc-pass") || 0; } catch (e) {}
const passBar = () => `<div class="seg4" role="group" aria-label="月卡折扣">${[0, 10, 15, 20].map(d =>
  `<button type="button" data-pass="${d}" aria-pressed="${d === discount}">${d ? `-${d}%` : "無折扣"}</button>`).join("")}</div>`;

const fmtN = n => typeof n === "number" ? (Number.isInteger(n) ? n.toLocaleString("en-US") : String(+n.toFixed(3))) : n;
function fmtT(s) {
  if (!s) return "0";
  s = Math.round(s);
  const d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
  return [d && d + "天", h && h + "時", m && m + "分", x && x + "秒"].filter(Boolean).join(" ");
}
const ORE_COL = { upgradeShinyOre: "Shiny Ore", upgradeGlowingOre: "Glowy Ore", upgradeStarryOre: "Starry Ore" };
const resIcon = r => r ? r.split(" or ").map(x => DATA.res[x] ? `<img class="ri" src="${DATA.res[x]}" alt="${esc(value(x))}" title="${esc(value(x))}">` : "").join("") : "";
const off = x => discount ? x * (100 - discount) / 100 : x;
// 費用用「萬」：25,000,000 → 2,500萬
const wan = n => n >= 1e4 ? (n >= 1e7 ? Math.round(n / 1e4).toLocaleString("en-US") : String(+(n / 1e4).toFixed(2))) + "萬" : n.toLocaleString("en-US");
const resClass = r => "c-" + (r || "").split(" or ")[0].toLowerCase().replace(/ /g, "-");

// 解鎖兵種／法術／裝備這類欄位的值是項目名稱（build.py 的 is_name_key），找得到項目就連到它的頁面
const isNameCol = c => { const k = (c || "").split(".").pop(); return /^unlocked|Unlocked$/.test(k) || ["unlocksSpell", "requiredSpellFactory", "unitName", "specialAbility"].includes(k); };
function nameLinks(v, base) {
  return v.split("、").map(n => {
    const all = Object.values(DATA.items), u = all.find(i => i.zh === n && i.base === base) || all.find(i => i.zh === n);
    return u ? `<a class="nm" href="${itemHref(u.id)}">${img(u, "ni")}${esc(nameOf(u))}</a>` : esc(n);
  }).join("、");
}

function cell(v, col, base) {
  if (v === null || v === undefined) return "";
  if (typeof v === "string" && base && isNameCol(col)) return nameLinks(v, base);
  if (typeof v === "object" && "t" in v) return `<span class="${discount && v.t ? "disc" : ""}">${fmtT(off(v.t))}</span>`;
  if (typeof v === "object" && "c" in v) {
    const c = typeof v.c === "number" ? Math.round(off(v.c)) : v.c;
    if (c === 0) return "—";
    return `<span class="cost ${resClass(v.r)}">${resIcon(v.r)}${typeof c === "number" ? wan(c) : esc(c)}</span>`;
  }
  if (/Ore$/.test(col) && typeof v === "number") return `<span class="cost">${resIcon(ORE_COL[col])}${fmtN(v)}</span>`;
  if (Array.isArray(v)) return esc(v.map(value).join("、"));
  return esc(fmtN(value(v)));
}

// 表格第一欄：一般等級是深色方塊；超級蓄能（{sc: 1}）加上蓄能圖示
function lvCell(l) {
  if (typeof l === "number") return `<span class="lvb">${l}</span>`;
  if (l && typeof l === "object" && "sc" in l) return `<span class="lvb sc"><img src="${DATA.res.Supercharge}" alt="超級蓄能" title="超級蓄能">${l.sc}</span>`;
  return esc(l ?? "");
}

const img = (it, cls = "") => it.img ? `<img src="${BASE}${it.img}" alt="" class="${cls}" loading="lazy">` : `<div class="noimg ${cls}">${esc((it.zh || it.en)[0])}</div>`;
const nameOf = it => it.zh || it.en;

function tile(it, extra = "", dim = false) {
  return `<a class="tile${dim ? " off" : ""}" href="${itemHref(it.id)}" title="${esc(it.en)}">${img(it)}<div class="n">${esc(nameOf(it))}</div>${extra}</a>`;
}

const attrOf = (it, k) => (it.attrs.find(a => a[0] === k) || [])[1];
const G = key => (DATA.groups.find(g => g.key === key) || { items: [] }).items.map(id => DATA.items[id]);
const sec = (title, items) => ({ title, items });
// 英雄裝備屬於哪個英雄（英雄的項目 id）
const owner = e => "home-" + attrOf(e, "hero");

function homeHeroes() {
  const heroes = G("home/heroes"), eq = G("home/hero-equipment");
  return [
    sec("英雄", heroes),
    sec("戰寵", G("home/pets")),
    ...heroes.map(h => sec(`裝備（${nameOf(h)}）`, eq.filter(e => owner(e) === h.id))),
    sec("其他裝備", eq.filter(e => !heroes.some(h => owner(e) === h.id))),
  ];
}
function homeTech() {
  const t = G("home/troops"), s = G("home/spells");
  const dark = (x, k) => attrOf(x, k) === "dark";
  return [
    sec("聖水兵", t.filter(x => !dark(x, "troopType"))),
    sec("闇黑兵", t.filter(x => dark(x, "troopType"))),
    sec("超級部隊", G("home/super-troops")),
    sec("法術", s.filter(x => !dark(x, "spellType"))),
    sec("闇黑法術", s.filter(x => dark(x, "spellType"))),
    sec("攻城機器", G("home/siege-machines")),
    sec("非戰鬥人員", G("home/other/helpers")),
  ];
}

const VILLAGES = {
  home: {
    zh: "家鄉村莊", tag: "大本營、兵種、英雄與所有建築",
    tabs: [
      ["heroes", "英雄", homeHeroes],
      ["tech", "科技", homeTech],
      ["th", "大本", () => [sec("大本營", G("home/town-hall")), sec("精工防禦", G("home/crafted-defenses")), sec("守衛", G("home/guardians"))]],
      ["build", "建築", () => [
        sec("防禦建築", [...G("home/walls"), ...G("home/defenses")]), sec("陷阱", G("home/traps")),
        sec("資源建築", G("home/resource-buildings")), sec("軍隊建築", G("home/army-buildings")), sec("其他建築", G("home/other")),
      ]],
    ],
  },
  builder: {
    zh: "建築大師基地", tag: "建築大師的兵種、英雄與建築",
    tabs: [
      ["heroes", "英雄", () => [sec("英雄", G("builder/heroes"))]],
      ["tech", "科技", () => [sec("兵種", G("builder/troops"))]],
      ["build", "建築", () => [
        sec("建築大師大本營", G("builder/builder-hall")), sec("防禦建築", [...G("builder/walls"), ...G("builder/defenses")]),
        sec("陷阱", G("builder/traps")), sec("資源建築", G("builder/resource-buildings")),
        sec("軍隊建築", G("builder/army-buildings")), sec("其他建築", G("builder/other")),
      ]],
    ],
  },
  "clan-capital": {
    zh: "部落首都", tag: "首都大本營、衛城建築與兵種",
    tabs: [
      ["tech", "科技", () => [sec("兵種", G("clan-capital/troops")), sec("法術", G("clan-capital/spells"))]],
      ["build", "建築", () => [
        sec("大廳", G("clan-capital/halls")), sec("防禦建築", [...G("clan-capital/walls"), ...G("clan-capital/defenses")]),
        sec("陷阱", G("clan-capital/traps")), sec("兵營", G("clan-capital/army-buildings/barracks")),
        sec("法術工廠", G("clan-capital/army-buildings/spell-factories")), sec("軍隊建築", G("clan-capital/army-buildings")),
        sec("房屋", G("clan-capital/other/houses")),
      ]],
      ["clan", "部落", () => [sec("部落等級", G("clan/"))]],
    ],
  },
};

// 每個項目屬於哪個村莊的哪個分頁（給返回按鈕和麵包屑用）
const HOME_OF = {};
for (const [v, cfg] of Object.entries(VILLAGES))
  for (const [t, , fn] of cfg.tabs)
    for (const s of fn()) for (const it of s.items) HOME_OF[it.id] ||= { v, t, sec: s.title };

let state = { sub: {}, hall: 0, hallBase: "home", my: {} };
try { Object.assign(state, JSON.parse(localStorage.getItem("coc-state2") || "{}")); } catch (e) {}
const save = () => { try { localStorage.setItem("coc-state2", JSON.stringify(state)); } catch (e) {} };

// home：目前就在數據首頁，像「版本更新」「常見問題」一樣標示出來
function crumbs(parts, home = false) {
  $("#crumbs").innerHTML = [`<a href="${BASE}./"${home ? ' aria-current="page"' : ""}>數據首頁</a>`, ...parts.map(([t, href]) => href ? `<a href="${BASE}#${href}">${esc(t)}</a>` : `<span>${esc(t)}</span>`)]
    .join(`<span class="sep">›</span>`);
}

function landingView() {
  crumbs([], true);
  const card = (v, title, tag, big) => `<a class="vcard${big ? " big" : ""}" href="${BASE}#${v}">
    <img src="${BASE}card-${v}.webp" alt="" width="800" height="396"><div class="vt"><h2>${title}</h2><p>${tag}</p></div></a>`;
  const V = VILLAGES;
  return `<div class="intro"><h1>升級數據</h1><p>部落衝突所有建築、兵種、法術、英雄與裝備的升級費用、時間和屬性。</p></div>
    <div class="passbar"><div class="lbl">月卡折扣</div>${passBar()}</div>
    <div class="vcards">${card("home", V.home.zh, V.home.tag, true)}${card("builder", V.builder.zh, V.builder.tag, true)}
      ${card("clan-capital", V["clan-capital"].zh, V["clan-capital"].tag)}${card("hall", "依大本營等級", "每樣東西能升到幾級")}</div>
    <section><h2 class="group">英雄</h2><div class="grid heroes">${G("home/heroes").map(it => tile(it)).join("")}</div></section>`;
}

function villageView(v, tab) {
  const cfg = VILLAGES[v];
  const cur = cfg.tabs.find(t => t[0] === tab) || cfg.tabs.find(t => t[0] === state.sub[v]) || cfg.tabs.find(t => t[0] === "tech") || cfg.tabs[0];
  state.sub[v] = cur[0]; save();
  crumbs([[cfg.zh]]);
  const sections = cur[2]().filter(s => s.items.length);
  return `<nav class="subtabs band" aria-label="${cfg.zh}分類">${cfg.tabs.map(([k, t]) => `<a href="${BASE}#${v}.${k}" aria-current="${k === cur[0] ? "page" : "false"}">${t}</a>`).join("")}</nav>
    ${sections.map(s => `<section><h2 class="group">${esc(s.title)}<span>${s.items.length}</span></h2><div class="grid">${s.items.map(it => tile(it)).join("")}</div></section>`).join("")}`;
}

function hallView() {
  crumbs([["依大本營等級"]]);
  const base = state.hallBase;
  const hallId = base === "home" ? "home-town-hall" : "builder-builder-hall";
  const max = DATA.items[hallId].hallMax.length;
  if (!state.hall || state.hall > max) state.hall = max;
  const h = state.hall;
  const hallName = base === "home" ? "大本營" : "建築大師大本營";
  const countAt = it => {
    if (!it.count) return null;
    let best = null;
    for (const [k, c] of Object.entries(it.count)) if (+k <= h) best = c;
    return best;
  };
  const sections = VILLAGES[base].tabs.flatMap(([, , fn]) => fn())
    .map(s => sec(s.title, s.items.filter(it => it.hallMax && it.id !== hallId))).filter(s => s.items.length);
  return `<div class="seg" role="group" aria-label="村莊">
      <button data-hb="home" aria-pressed="${base === "home"}">家鄉村莊</button><button data-hb="builder" aria-pressed="${base === "builder"}">建築大師基地</button></div>
    <div class="hallpick"><span class="lbl">${hallName}</span>${Array.from({ length: max }, (_, i) => `<button class="chip" data-h="${i + 1}" aria-pressed="${i + 1 === h}">${i + 1}</button>`).join("")}</div>
    <p class="note">每個項目在${hallName} ${h} 級時能升到的最高等級，以及可擁有數量（×）。灰色代表此等級尚未解鎖。</p>
    ${sections.map(s => `<section><h2 class="group">${esc(s.title)}</h2><div class="grid">${s.items.map(it => {
      const lv = it.hallMax[h - 1], n = countAt(it);
      return tile(it, `<div class="lv">${lv ? "Lv " + lv : "—"}${n ? ` <span style="font-size:12px">×${n}</span>` : ""}</div>`, !lv);
    }).join("")}</div></section>`).join("")}`;
}

function itemView(it) {
  const where = HOME_OF[it.id];
  const cfg = where && VILLAGES[where.v];
  const tabName = cfg ? cfg.tabs.find(t => t[0] === where.t)[1] : "";
  crumbs(cfg ? [[cfg.zh, where.v], [tabName, `${where.v}.${where.t}`], [nameOf(it)]] : [[nameOf(it)]]);
  // 捷徑連結：兵種和超級部隊互相連結，英雄頁列出自己的裝備，裝備頁連回所屬英雄
  const gear = it.group === "home/heroes" ? G("home/hero-equipment").filter(e => owner(e) === it.id) : [];
  const hero = it.group === "home/hero-equipment" ? DATA.items[owner(it)] : null;
  const rel = [...[it.super, it.from].filter(Boolean).map(id => DATA.items[id]), ...gear, ...(hero ? [hero] : [])];
  const attrHtml = it.attrs.length ? `<dl class="attrs">${it.attrs.map(([k, v]) => {
    if (Array.isArray(v) && v.length && v.every(x => x && x.u)) {
      // 防守部隊：找得到對應的兵種就顯示圖示並連到它的頁面
      const unit = x => Object.values(DATA.items).find(i => i.en === x.u && i.base === it.base) || Object.values(DATA.items).find(i => i.en === x.u);
      return `<div class="wide"><dt>${esc(label(k))}</dt><dd><div class="links">${v.map(x => {
        const u = unit(x), name = esc((u && nameOf(u)) || x.zh || x.u) + ` ×${x.n}`;
        return u ? `<a href="${itemHref(u.id)}">${img(u)}${name} ›</a>` : `<span class="unit">${name}</span>`;
      }).join("")}</div></dd></div>`;
    }
    if (Array.isArray(v)) return `<div class="wide"><dt>${esc(label(k))}</dt><dd><ul>${v.map(x => `<li>${esc(value(x))}</li>`).join("")}</ul></dd></div>`;
    let shown;
    if (v && typeof v === "object" && "t" in v) shown = fmtT(v.t);
    else if (v && typeof v === "object" && "c" in v) return `<div><dt>${esc(label(k))}</dt><dd>${cell(v)}</dd></div>`;
    else if (k === "hero") shown = nameOf(DATA.items["home-" + v] || { en: v });
    else if (typeof v === "string" && isNameCol(k)) return `<div><dt>${esc(label(k))}</dt><dd>${nameLinks(v, it.base)}</dd></div>`;
    else shown = fmtN(value(v));
    return `<div><dt>${esc(label(k))}</dt><dd>${esc(shown)}</dd></div>`;
  }).join("")}</dl>` : "";
  const used = [...new Set(it.tables.flatMap(t => t.rows.flatMap(r => r.flatMap((v, i) =>
    v && typeof v === "object" && "c" in v ? v.r.split(" or ") : (i && ORE_COL[t.cols[i - 1]] && v ? [ORE_COL[t.cols[i - 1]]] : [])))))];
  // 我的大本營：表中超過這個大本營能升的等級會變淡；超級蓄能要先升到最高等級，所以跟最高等級一起變淡
  const isHall = it.id === "home-town-hall" || it.id === "builder-builder-hall";
  const hm = !isHall && (it.base === "home" || it.base === "builder") && it.hallMax ? it.hallMax : null;
  const hallName = it.base === "builder" ? "建築大師大本營" : "大本營";
  const my = hm ? Math.min(state.my[it.base] || hm.length, hm.length) : 0;
  const myMax = hm ? hm[my - 1] || 0 : Infinity;
  // 召喚單位、武器這些附帶的表格（extra）有自己的等級，不算進「最高」，也不跟大本營比較
  const levels = it.tables.filter(t => !t.extra).flatMap(t => t.rows.map(r => r[0]).filter(x => typeof x === "number"));
  const top = levels.length ? Math.max(...levels) : 0;
  const panel = hm || used.length ? `<div class="panel">
    ${hm ? `<div class="row"><span class="lbl">我的${hallName}</span><div class="step">
      <button type="button" data-my="-1" data-b="${it.base}" data-n="${hm.length}" aria-label="${hallName}降一級"${my <= 1 ? " disabled" : ""}>−</button>
      <select class="n" data-myset data-b="${it.base}" aria-label="選擇${hallName}等級">${hm.map((_, i) => `<option value="${i + 1}"${i + 1 === my ? " selected" : ""}>${i + 1}</option>`).join("")}</select>
      <button type="button" data-my="1" data-b="${it.base}" data-n="${hm.length}" aria-label="${hallName}升一級"${my >= hm.length ? " disabled" : ""}>+</button></div></div>
      <div class="say">${hallName} <b>${my}</b> ${myMax ? `可升到 <b class="hl">Lv ${myMax}</b>，表中淡色的等級需要更高的${hallName}。` : "還不能使用。"}</div>` : ""}
    ${hm && used.length ? "<hr>" : ""}
    ${used.length ? `<div class="lbl">月卡折扣</div>${passBar()}` : ""}</div>` : "";
  const tables = it.tables.map(t => `<section class="tbl">
    <h3>${t.img ? `<img class="ti" src="${BASE}${t.img}" alt="" loading="lazy">` : ""}${esc(t.title || "升級數據")}</h3>${t.sub ? `<p class="sub">${esc(t.sub)}</p>` : ""}
    <div class="scroll"><table><thead><tr><th>${esc(t.head || "等級")}</th>${t.cols.map(c => `<th>${esc(label(c))}</th>`).join("")}</tr></thead>
    <tbody>${t.rows.map(r => `<tr${!t.extra && (typeof r[0] === "number" ? r[0] : top) > myMax ? ' class="above"' : ""}><td>${lvCell(r[0])}</td>${t.cols.map((c, i) => `<td>${cell(r[i + 1], c, it.base)}</td>`).join("")}</tr>`).join("")}</tbody></table></div></section>`).join("");
  return `<div class="hero band"><div class="pic">${img(it)}</div>
      <div class="who"><div class="crumb">${esc(cfg ? cfg.zh : "")}${where ? "・" + esc(where.sec) : ""}</div>
      <h1>${esc(nameOf(it))}</h1>${it.zh ? `<div class="en">${esc(it.en)}</div>` : ""}</div>
      ${top ? `<div class="max">最高<b>${top}</b></div>` : ""}</div>
    ${it.desc ? `<p class="desc">${esc(it.desc)}</p>` : ""}
    ${rel.length ? `<div class="links">${rel.map(r => `<a href="${itemHref(r.id)}">${img(r)}${esc(nameOf(r))} ›</a>`).join("")}</div>` : ""}
    ${attrHtml}
    ${panel}
    ${discount && used.length ? `<p class="disc" style="margin:0">已套用月卡 -${discount}%</p>` : ""}
    ${tables}`;
}

function searchView(q) {
  crumbs([["搜尋：" + q.trim()]]);
  const s = q.trim().toLowerCase();
  const hits = Object.values(DATA.items).filter(it => it.en.toLowerCase().includes(s) || (it.zh || "").includes(q.trim()));
  if (!hits.length) return `<div class="empty">找不到「${esc(q)}」。試試看英文名稱，或換個關鍵字。</div>`;
  const by = {};
  for (const it of hits) { const v = (HOME_OF[it.id] || {}).v || "other"; (by[v] ||= []).push(it); }
  return Object.entries(by).map(([v, list]) => `<section><h2 class="group">${VILLAGES[v] ? VILLAGES[v].zh : "其他"}<span>${list.length}</span></h2><div class="grid">${list.map(it => tile(it)).join("")}</div></section>`).join("");
}

function faqView() {
  crumbs([]);  // 路徑只顯示「數據首頁」，目前這頁由右上角亮起來的連結表示
  const qa = [
    ["這個網站是做什麼的？", "查詢部落衝突（Clash of Clans）所有兵種、建築、法術、英雄、裝備與戰寵的升級費用、升級時間和屬性。"],
    ["資料從哪裡來？", `數據來自開源專案 <a href="https://github.com/chiefpansancolt/clash-of-clans-data" target="_blank" rel="noopener">clash-of-clans-data</a>（MIT 授權，© 2026 Christopher Pezza）。本站只負責整理成中文和方便查詢，數字和原始資料一致。遊戲剛改版時，資料可能要過幾天才會更新。`],
    ["多久更新一次？", "每天自動檢查一次，資料來源一更新，本站隔天就會跟著更新。"],
    ["中文名稱為什麼跟遊戲裡不一樣？", "中文名稱是對照翻譯，大部分和遊戲一致，少數可能略有不同。新推出的兵種或建築，會先顯示英文名稱。"],
    ["「我的大本營」和「月卡折扣」怎麼用？", "在兵種或建築頁按「−」「+」調成你的大本營等級，表中升不到的等級會變淡；選擇月卡折扣後，所有費用和時間會自動打折。"],
    ["可以像 App 一樣使用嗎？", "可以。iPhone 用 Safari 打開本站，按「分享」→「加入主畫面」，之後從主畫面打開就是全螢幕，跟 App 一樣。Android 用 Chrome 打開，按右上角選單 →「加到主畫面」。"],
    ["需要付費或登入嗎？", "不用。完全免費，不需要帳號。"],
    ["這是官方網站嗎？", "不是。本站為非官方粉絲內容，未經 Supercell 認可。This material is unofficial and is not endorsed by Supercell. For more information see Supercell's Fan Content Policy: <a href=\"https://www.supercell.com/fan-content-policy\" target=\"_blank\" rel=\"noopener\">www.supercell.com/fan-content-policy</a>."],
    ["網站是怎麼做的？", `程式碼公開在 GitHub：<a href="https://github.com/powber-21/coc-upgrade-zh" target="_blank" rel="noopener">github.com/powber-21/coc-upgrade-zh</a>`],
  ];
  return `<div class="intro"><h1>常見問題</h1></div>
    <div class="faq">${qa.map(([q, a]) => `<section><h2>${q}</h2><p>${a}</p></section>`).join("")}</div>`;
}

// 版本更新：build.py 比對資料來源每次更新，列出新增的項目和改變的數值
const lvName = l => l && typeof l === "object" ? `超級蓄能 ${l.sc}` : `${l} 級`;
function logVal(v) {
  if (v === null || v === undefined || v === "") return "無";
  if (Array.isArray(v)) return v.map(x => x && x.u ? `${x.zh || x.u} ×${x.n}` : value(x)).join("、");
  if (typeof v === "object" && "t" in v) return fmtT(v.t);
  if (typeof v === "object" && "c" in v) return fmtN(v.c) + resIcon(v.r);
  return esc(fmtN(value(v)));
}
function logLines(ch) {
  const lines = [], by = new Map();
  for (const c of ch) {
    const pre = c.tbl ? esc(c.tbl) + " · " : "";
    if (c.add) lines.push(`新增「${esc(c.tbl)}」`);
    else if (c.lvAdd) lines.push(`${c.tbl ? esc(c.tbl) + "：" : ""}新增 ${c.lvAdd.map(lvName).join("、")}`);
    else if (!("lv" in c)) lines.push(`${pre}${esc(label(c.k))}：${logVal(c.o)} → ${logVal(c.n)}`);
    else {
      // 同一個欄位改了好幾級，合成一行
      const k = (c.tbl || "") + "|" + c.k;
      if (!by.has(k)) { by.set(k, { pre, k: c.k, v: [] }); lines.push(by.get(k)); }
      by.get(k).v.push(`${lvName(c.lv)}：${logVal(c.o)} → ${logVal(c.n)}`);
    }
  }
  return lines.map(l => typeof l === "string" ? l : `${l.pre}${esc(label(l.k))}${l.v.map(x => `<span class="lvl">${x}</span>`).join("")}`);
}
const fmtDay = d => { const [y, m, dd] = d.split("-"); return `${y} 年 ${+m} 月 ${+dd} 日`; };
function updatesView() {
  crumbs([]);  // 路徑只顯示「數據首頁」，目前這頁由右上角亮起來的連結表示
  const log = DATA.log || [];
  return `<div class="intro"><h1>版本更新</h1><p>資料來源每次更新時，自動比對出新增的項目和改變的數值。數值依照目前的中文名稱顯示。</p></div>
    <div class="log">${log.map(day => {
      const add = day.items.filter(e => e.new).map(e => DATA.items[e.id]);
      const chg = day.items.filter(e => e.ch);
      // 日期預設收起來，點日期才展開；展開後每個項目直接列出改了什麼
      return `<details class="day"><summary><h2>${fmtDay(day.date)}</h2><span>${day.items.length} 個項目</span></summary>
        ${add.length ? `<h3>新增項目</h3><div class="links">${add.map(it => `<a href="${itemHref(it.id)}">${img(it)}${esc(nameOf(it))} ›</a>`).join("")}</div>` : ""}
        ${chg.length ? `<h3>數值調整</h3>${chg.map(e => {
          const it = DATA.items[e.id];
          return `<div class="item"><a class="name" href="${itemHref(it.id)}">${img(it)}<b>${esc(nameOf(it))}</b> ›</a>
            <ul>${logLines(e.ch).map(l => `<li>${l}</li>`).join("")}</ul></div>`;
        }).join("")}` : ""}
        <button type="button" class="fold" data-fold>▴ 收合 ${fmtDay(day.date)}</button></details>`;
    }).join("") || `<p class="note">目前還沒有版本更新紀錄。</p>`}</div>`;
}
// 最近一次資料更新在 3 天內、而且使用者還沒看過，「版本更新」連結旁顯示紅點
const logRecent = () => DATA.log && DATA.log.length && Date.now() - new Date(DATA.log[0].date + "T00:00:00+08:00") < 3 * 86400e3;

function footer() {
  return `<footer><p><b>資料最後更新：${esc(DATA.updated || "")}</b></p>
    <p>資料來源：<a href="https://github.com/chiefpansancolt/clash-of-clans-data" target="_blank" rel="noopener">clash-of-clans-data</a>，© 2026 Christopher Pezza，依 MIT 授權使用（<a href="https://github.com/powber-21/coc-upgrade-zh/blob/main/THIRD_PARTY_LICENSES.md" target="_blank" rel="noopener">授權條文</a>）。中文名稱為對照翻譯，可能與遊戲內略有不同。</p>
    <p><a href="${BASE}updates/">版本更新</a>　<a href="${BASE}faq/">常見問題</a></p>
    <p>本網站為非官方粉絲內容，未經 Supercell 認可。This material is unofficial and is not endorsed by Supercell. For more information see Supercell's Fan Content Policy: <a href="https://www.supercell.com/fan-content-policy" target="_blank" rel="noopener">www.supercell.com/fan-content-policy</a>.</p></footer>`;
}

function render() {
  let h = decodeURIComponent(location.hash.slice(1));
  // 舊的 #home-archer 連結轉到新的項目頁；項目頁上的其他 # 連結回首頁處理
  if (!PAGE_ITEM && DATA.items[h]) { location.replace(itemHref(h)); return; }
  if (PAGE_ITEM) {
    if (h && !DATA.items[h]) { location.replace(BASE + "#" + h); return; }
    h = PAGE_ITEM;
  }
  const q = $("#q").value;
  const v = $("#view");
  if (q.trim()) { v.innerHTML = searchView(q) + footer(); return; }
  if (PAGE_ITEM === "faq") { v.innerHTML = faqView() + footer(); return; }
  if (PAGE_ITEM === "updates") { v.innerHTML = updatesView() + footer(); return; }
  const it = DATA.items[h];
  const [village, tab] = h.split(".");
  if (it) {
    v.innerHTML = itemView(it) + footer();
  } else if (VILLAGES[village]) {
    v.innerHTML = villageView(village, tab) + footer();
  } else if (h === "hall") {
    v.innerHTML = hallView() + footer();
    v.querySelectorAll("[data-h]").forEach(b => b.onclick = () => { state.hall = +b.dataset.h; save(); render(); });
    v.querySelectorAll("[data-hb]").forEach(b => b.onclick = () => { state.hallBase = b.dataset.hb; state.hall = 0; save(); render(); });
  } else {
    v.innerHTML = landingView() + footer();
  }
}
// 月卡折扣和「我的大本營」按鈕
$("#view").addEventListener("click", e => {
  const p = e.target.closest("[data-pass]");
  if (p) { discount = +p.dataset.pass; try { localStorage.setItem("coc-pass", discount); } catch (err) {} render(); return; }
  const m = e.target.closest("[data-my]");
  if (m) {
    const b = m.dataset.b, n = +m.dataset.n;
    state.my[b] = Math.max(1, Math.min(n, (state.my[b] || n) + +m.dataset.my)); save(); render();
  }
});
// 版本更新頁：滑到一天的最下面，按按鈕收起來並回到那個日期
$("#view").addEventListener("click", e => {
  const b = e.target.closest("[data-fold]");
  if (!b) return;
  const day = b.closest("details");
  day.open = false;
  if (day.getBoundingClientRect().top < 0) day.scrollIntoView({ block: "start" });
});
$("#view").addEventListener("change", e => {
  const s = e.target.closest("[data-myset]");
  if (s) { state.my[s.dataset.b] = +s.value; save(); render(); }
});
window.addEventListener("hashchange", () => { $("#q").value = ""; render(); window.scrollTo(0, 0); });
$("#q").addEventListener("input", render);
// 版本更新、常見問題頁：右上角對應的連結亮起來，讓使用者知道自己在哪一頁
document.querySelectorAll(".toplinks a").forEach(a => { if (PAGE_ITEM && a.getAttribute("href").endsWith(PAGE_ITEM + "/")) a.setAttribute("aria-current", "page"); });
// 看過版本更新頁就記下最新的日期，紅點不再出現，直到下一次資料更新
function logDot() {
  const link = $("#loglink");
  if (!link || !DATA.log || !DATA.log.length) return;
  let seen = "";
  try {
    if (PAGE_ITEM === "updates") localStorage.setItem("coc-log-seen", DATA.log[0].date);
    seen = localStorage.getItem("coc-log-seen") || "";
  } catch (e) {}
  const dot = $(".dot", link), show = logRecent() && seen !== DATA.log[0].date;
  if (show && !dot) link.insertAdjacentHTML("afterbegin", `<i class="dot" title="最近有資料更新"></i>`);
  if (!show && dot) dot.remove();
}
logDot();
// 用返回鍵回到之前的頁面時，瀏覽器會直接顯示舊畫面，要再檢查一次
window.addEventListener("pageshow", logDot);
window.addEventListener("storage", logDot);
// 頁首的高度會隨螢幕寬度改變（例如導覽列換行），分類列要貼在它下面
const head = $("header");
new ResizeObserver(() => document.documentElement.style.setProperty("--head-h", head.offsetHeight + "px")).observe(head);
render();
