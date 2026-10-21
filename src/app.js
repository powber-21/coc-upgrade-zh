const DATA = window.DATA;
window.APP_READY = true;
// 根目錄的頁面 BASE 是空字串；項目頁在子資料夾裡，BASE 是 "../"
const BASE = document.documentElement.dataset.base || "";
const PAGE_ITEM = document.documentElement.dataset.item || "";
const itemHref = id => `${BASE}${id}/`;
const $ = (s, el = document) => el.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));


const LABELS = {
  hitpoints: "生命值", dps: "每秒傷害", damagePerShot: "每擊傷害", damagePerSecond: "每秒傷害", damagePerHit: "每擊傷害",
  buildCost: "升級費用", upgradeCost: "升級費用", researchCost: "研究費用", buildTime: "升級時間", upgradeTime: "升級時間", researchTime: "研究時間",
  xpGained: "獲得經驗", townHallRequired: "需大本營", laboratoryRequired: "需實驗室", heroHallLevelRequired: "需英雄大廳",
  petHouseLevelRequired: "需戰寵小屋", blacksmithLevelRequired: "需鐵匠鋪", builderHallRequired: "需建築大師基地",
  builderHallLevelRequired: "需建築大師基地", starLabRequired: "需星空實驗室", districtHallRequired: "需區域大廳", capitalHallRequired: "需都城大廳",
  healthRecovery: "生命回復", hitpointIncrease: "生命提升", hpRecoveryIncrease: "回復提升",
  upgradeShinyOre: "閃亮礦石", upgradeGlowingOre: "發光礦石", upgradeStarryOre: "星光礦石",
  capacity: "容量", unitsPerCamp: "每營數量", damage: "傷害", productionRate: "每小時產量", deathDamage: "死亡傷害",
  damageVsWalls: "對城牆傷害", maxBuildings: "建築數上限", maxTraps: "陷阱數上限", housingSpace: "人口", spellDuration: "持續時間",
  radius: "半徑", wallRings: "城牆戒指", troopCapacity: "部隊容量", spellCapacity: "法術容量", siegeMachineCapacity: "攻城機器容量",
  spellStorageCapacity: "法術容量", abilityLevel: "技能等級", speedIncrease: "速度提升", damageIncrease: "傷害提升",
  unlockedUnit: "解鎖兵種", unlockedSpell: "解鎖法術", unlockedHero: "解鎖英雄", unlockedPet: "解鎖戰寵", unlockedSiegeMachine: "解鎖攻城機器",
  heroSlots: "英雄欄位", stat: "數值", sparkyStones: "火花石", healingPerSecond: "每秒治療", healingPerPulse: "每波治療",
  numberOfTargets: "目標數", labLevelCap: "實驗室上限", storageCapacity: "儲存容量", oreCapacity: "礦石容量", maxEquipmentLevel: "裝備等級上限",
  equipmentUnlocked: "解鎖裝備", lifetime: "存在時間", stunDuration: "暈眩時間", spawnCount: "召喚數量", supercharge: "超級充能",
  troopLevel: "部隊等級", workRate: "工作速率", xpRequired: "所需經驗", cumulativeXp: "累計經驗", perks: "福利",
  // 屬性
  movementSpeed: "移動速度", range: "攻擊範圍", attackSpeed: "攻擊間隔(秒)", damageType: "傷害類型", targetType: "攻擊目標",
  troopType: "類型", barrackLevelRequired: "需訓練營", size: "佔地", preferredTarget: "優先目標", specialAbility: "特殊技能",
  rarity: "稀有度", abilityType: "技能類型", hero: "所屬英雄", unlockRequirement: "取得方式", spellType: "類型",
  spellFactoryLevelRequired: "需法術工廠", workshopLevelRequired: "需攻城機器工坊", boostCost: "增幅費用", boostDuration: "增幅時間",
  regularLevelRequired: "需原兵種等級", attackType: "攻擊方式", searchRadius: "索敵範圍", triggerRadius: "觸發範圍",
  favoriteTarget: "優先目標", maxCapacity: "容量上限", sellingPrice: "售價", craftingPhase: "工藝階段", isCurrent: "目前可用",
  "donationCost.amount": "捐贈費用", "donationCost.resource": "捐贈資源", "donationCost.gemsOrRaidMedals": "捐贈寶石/突襲獎牌",
  "gold": "金幣", "elixir": "聖水", "darkElixir": "暗黑重油",
  dpsIncrease: "每秒傷害提升", abilityDuration: "技能持續", troopUnlocked: "解鎖兵種", builderBarracksRequired: "需建築大師訓練營",
  splashRadius: "濺射半徑", shotsPerBurst: "每輪發射數", timeBetweenBursts: "每輪間隔", damageRadius: "傷害半徑", minRange: "最小射程",
  attackSpeedIncrease: "攻速提升", spellUnlocked: "解鎖法術", requiredSpellFactory: "需法術工廠", secondaryChainDamagePerShot: "第二段連鎖傷害",
  tertiaryChainDamagePerShot: "第三段連鎖傷害", chainDamagePerShot: "連鎖傷害", incomingDamageReduction: "受到傷害減免",
  selfHealingPerSecond: "每秒自我治療", projectileDamage: "投射物傷害", triggerRange: "觸發範圍", chainRange: "連鎖範圍",
  maxChainTargets: "連鎖目標上限", availableFromLevel: "可用起始等級", spellRadius: "法術半徑", rechargeTime: "充能時間", maxDps: "最大每秒傷害",
  durationAttacks: "持續攻擊次數", movementSpeedIncrease: "移速提升", damagePerShotIncrease: "每擊傷害提升", slowDownDuration: "減速持續",
  abilityDamage: "技能傷害", numberOfAttacks: "攻擊次數", rageDuration: "狂暴持續", rageDamageIncrease: "狂暴傷害提升", rageSpeedIncrease: "狂暴速度提升",
  summonCooldown: "召喚冷卻", auraRange: "光環範圍", timeBetweenPulses: "脈衝間隔", numberOfPulses: "脈衝次數", boostTime: "加速時間",
  healingPerSecondOnHeroes: "對英雄每秒治療", healingPerPulseOnHeroes: "對英雄每波治療", poisonMaxDps: "毒素最大每秒傷害",
  buildingDamagePercent: "建築傷害%", troopDamagePercent: "部隊傷害%", damageVsHeroes: "對英雄傷害", springCapacity: "彈簧容量",
  dpsInitial: "初始每秒傷害", dpsAfter1p5s: "1.5秒後每秒傷害", infernoInitialDps: "初始每秒傷害", repairPerSecond: "每秒修復", repairPerHit: "每次修復",
  pushStrength: "擊退力道", skeletonLevel: "骷髏等級", spawnedUnits: "生成單位", duration: "持續時間", freezeTime: "冰凍時間",
  totalHealing: "總治療量", maxDamagePerSecond: "最大每秒傷害", speedDecrease: "速度下降", attackRateDecrease: "攻速下降",
  invisibilityDuration: "隱形時間", reviveDuration: "復活時間", cooldownTime: "冷卻時間", healPerHit: "每擊回復", unitName: "單位",
  guardianType: "守衛類型", instances: "數量", passiveAbility: "被動技能", wallDamageMultiplier: "城牆傷害倍率", hpDecayPerSecond: "每秒生命衰減",
  armorHitpoints: "護甲生命值", damageVsResources: "對資源傷害", heroLevelCaps: "英雄等級上限", maxEquipmentLevel: "裝備等級上限",
  common: "普通", epic: "史詩", shinyOre: "閃亮礦石", glowyOre: "發光礦石", starryOre: "星光礦石", ability: "技能", weapon: "武器", name: "名稱",
  targets: "目標", gearUp: "齒輪強化", cost: "費用", time: "時間", requiresLevel: "需等級", timeGainedMinutes: "獲得時間(分)", boostDurationMinutes: "加速時間(分)",
};
const MODES = { normal: "一般", multiTarget: "多目標", singleTarget: "單目標", ground: "對地", air: "對空", burst: "連發", sniper: "狙擊",
  gearUp: "齒輪強化", geared: "齒輪強化", gearedUpBurst: "齒輪強化連發", gearedUpFastAttack: "齒輪強化快攻", longRange: "遠程", fastAttack: "快速攻擊",
  stage1: "第一階段", stage2: "第二階段", stage3: "第三階段", rage: "狂暴", poison: "毒藥", invisibility: "隱形", earthquake: "地震",
  airAndGround: "對空與對地", builder: "建築工人", active: "啟動", depleted: "耗盡" };
const VALUES = {
  single: "單體", splash: "濺射", area: "範圍", chain: "連鎖", none: "無", both: "地面與空中", ground: "地面", air: "空中",
  defenses: "防禦建築", regular: "一般", dark: "暗黑", Common: "普通", Epic: "史詩", Active: "主動", Passive: "被動",
  Gold: "金幣", Elixir: "聖水", "Dark Elixir": "暗黑重油", Gems: "寶石", "Builder Gold": "建築大師金幣", "Builder Elixir": "建築大師聖水",
  "Capital Gold": "都城金幣", "Gold or Elixir": "金幣或聖水", "Builder Gold or Builder Elixir": "建築金幣或聖水",
  Any: "任意", Resources: "資源建築", Walls: "城牆", Heroes: "英雄", Hero: "英雄", None: "無", true: "是", false: "否",
};

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
$("#pass").value = String(discount);
$("#pass").addEventListener("change", e => {
  discount = +e.target.value;
  try { localStorage.setItem("coc-pass", discount); } catch (e) {}
  render();
});

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

function cell(v, col) {
  if (v === null || v === undefined) return "";
  if (typeof v === "object" && "t" in v) return `<span class="${discount && v.t ? "disc" : ""}">${fmtT(off(v.t))}</span>`;
  if (typeof v === "object" && "c" in v) {
    const c = typeof v.c === "number" ? Math.round(off(v.c)) : v.c;
    return `<span class="${discount && v.c ? "disc" : ""}">${fmtN(c)}</span>${resIcon(v.r)}`;
  }
  if (/Ore$/.test(col) && typeof v === "number") return `${fmtN(v)}${resIcon(ORE_COL[col])}`;
  if (Array.isArray(v)) return esc(v.map(value).join("、"));
  return esc(fmtN(value(v)));
}

const img = (it, cls = "") => it.img ? `<img src="${BASE}${it.img}" alt="" class="${cls}" loading="lazy">` : `<div class="noimg ${cls}">${esc((it.zh || it.en)[0])}</div>`;
const nameOf = it => it.zh || it.en;

function tile(it, extra = "", dim = false) {
  return `<a class="tile${dim ? " off" : ""}" href="${itemHref(it.id)}" title="${esc(it.en)}">${img(it)}<div class="n">${esc(nameOf(it))}</div>${extra}</a>`;
}

const attrOf = (it, k) => (it.attrs.find(a => a[0] === k) || [])[1];
const G = key => (DATA.groups.find(g => g.key === key) || { items: [] }).items.map(id => DATA.items[id]);
const sec = (title, items) => ({ title, items });

function homeHeroes() {
  const heroes = G("home/heroes"), eq = G("home/hero-equipment");
  const owner = e => "home-" + attrOf(e, "hero");
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
    sec("暗黑兵", t.filter(x => dark(x, "troopType"))),
    sec("超級兵", G("home/super-troops")),
    sec("法術", s.filter(x => !dark(x, "spellType"))),
    sec("暗黑法術", s.filter(x => dark(x, "spellType"))),
    sec("攻城機器", G("home/siege-machines")),
    sec("非戰鬥人員", G("home/other/helpers")),
  ];
}

const VILLAGES = {
  home: {
    zh: "家鄉", tag: "大本營、兵種、英雄與所有建築",
    tabs: [
      ["heroes", "英雄", homeHeroes],
      ["tech", "科技", homeTech],
      ["th", "大本", () => [sec("大本營", G("home/town-hall")), sec("工藝防禦", G("home/crafted-defenses")), sec("守衛", G("home/guardians"))]],
      ["build", "建築", () => [
        sec("防禦建築", [...G("home/walls"), ...G("home/defenses")]), sec("陷阱", G("home/traps")),
        sec("資源建築", G("home/resource-buildings")), sec("軍隊建築", G("home/army-buildings")), sec("其他建築", G("home/other")),
      ]],
    ],
  },
  builder: {
    zh: "夜世界", tag: "建築大師的兵種、英雄與建築",
    tabs: [
      ["heroes", "英雄", () => [sec("英雄", G("builder/heroes"))]],
      ["tech", "科技", () => [sec("兵種", G("builder/troops"))]],
      ["build", "建築", () => [
        sec("建築大師基地", G("builder/builder-hall")), sec("防禦建築", [...G("builder/walls"), ...G("builder/defenses")]),
        sec("陷阱", G("builder/traps")), sec("資源建築", G("builder/resource-buildings")),
        sec("軍隊建築", G("builder/army-buildings")), sec("其他建築", G("builder/other")),
      ]],
    ],
  },
  "clan-capital": {
    zh: "部落都城", tag: "都城大廳、區域建築與兵種",
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

let state = { sub: {}, hall: 0, hallBase: "home" };
try { Object.assign(state, JSON.parse(localStorage.getItem("coc-state2") || "{}")); } catch (e) {}
const save = () => { try { localStorage.setItem("coc-state2", JSON.stringify(state)); } catch (e) {} };

function crumbs(parts) {
  $("#crumbs").innerHTML = [`<a href="${BASE}./">升級數據</a>`, ...parts.map(([t, href]) => href ? `<a href="${BASE}#${href}">${esc(t)}</a>` : `<span>${esc(t)}</span>`)]
    .join(`<span class="sep">›</span>`);
}

function landingView() {
  crumbs([]);
  const art = name => `<img src="${BASE}card-${name}.webp" alt="" width="800" height="396">`;
  const cards = Object.entries(VILLAGES).map(([v, c]) =>
    `<a class="vcard v-${v}" href="${BASE}#${v}"><div class="vt"><h2>${c.zh}</h2><p>${c.tag}</p></div><div class="art">${art(v)}</div></a>`);
  cards.push(`<a class="vcard v-hall" href="${BASE}#hall"><div class="vt"><h2>依大本營等級</h2><p>選等級，查每樣東西能升到幾級</p></div>
    <div class="art">${art("hall")}</div></a>`);
  return `<div class="intro"><h1>升級數據</h1><p>部落衝突所有建築、兵種、法術、英雄與裝備的升級費用、時間和屬性。右上角可以套用月卡折扣。</p></div>
    <div class="vcards">${cards.join("")}</div>`;
}

function villageView(v, tab) {
  const cfg = VILLAGES[v];
  const cur = cfg.tabs.find(t => t[0] === tab) || cfg.tabs.find(t => t[0] === state.sub[v]) || cfg.tabs.find(t => t[0] === "tech") || cfg.tabs[0];
  state.sub[v] = cur[0]; save();
  crumbs([[cfg.zh]]);
  const sections = cur[2]().filter(s => s.items.length);
  return `<nav class="subtabs" aria-label="${cfg.zh}分類">${cfg.tabs.map(([k, t]) => `<a href="${BASE}#${v}.${k}" aria-current="${k === cur[0] ? "page" : "false"}">${t}</a>`).join("")}</nav>
    ${sections.map(s => `<section><h2 class="group">${esc(s.title)}<span>${s.items.length}</span></h2><div class="grid">${s.items.map(it => tile(it)).join("")}</div></section>`).join("")}`;
}

function hallView() {
  crumbs([["依大本營等級"]]);
  const base = state.hallBase;
  const hallId = base === "home" ? "home-town-hall" : "builder-builder-hall";
  const max = DATA.items[hallId].hallMax.length;
  if (!state.hall || state.hall > max) state.hall = max;
  const h = state.hall;
  const hallName = base === "home" ? "大本營" : "建築大師基地";
  const countAt = it => {
    if (!it.count) return null;
    let best = null;
    for (const [k, c] of Object.entries(it.count)) if (+k <= h) best = c;
    return best;
  };
  const sections = VILLAGES[base].tabs.flatMap(([, , fn]) => fn())
    .map(s => sec(s.title, s.items.filter(it => it.hallMax && it.id !== hallId))).filter(s => s.items.length);
  return `<div class="seg" role="group" aria-label="村莊">
      <button data-hb="home" aria-pressed="${base === "home"}">家鄉</button><button data-hb="builder" aria-pressed="${base === "builder"}">夜世界</button></div>
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
  const rel = [it.super, it.from].filter(Boolean).map(id => DATA.items[id]);
  const attrHtml = it.attrs.length ? `<dl class="attrs">${it.attrs.map(([k, v]) => {
    if (Array.isArray(v)) return `<div class="wide"><dt>${esc(label(k))}</dt><dd><ul>${v.map(x => `<li>${esc(value(x))}</li>`).join("")}</ul></dd></div>`;
    let shown;
    if (v && typeof v === "object" && "t" in v) shown = fmtT(v.t);
    else if (v && typeof v === "object" && "c" in v) return `<div><dt>${esc(label(k))}</dt><dd>${cell(v)}</dd></div>`;
    else if (k === "hero") shown = nameOf(DATA.items["home-" + v] || { en: v });
    else shown = fmtN(value(v));
    return `<div><dt>${esc(label(k))}</dt><dd>${esc(shown)}</dd></div>`;
  }).join("")}</dl>` : "";
  const used = [...new Set(it.tables.flatMap(t => t.rows.flatMap(r => r.flatMap((v, i) =>
    v && typeof v === "object" && "c" in v ? v.r.split(" or ") : (i && ORE_COL[t.cols[i - 1]] && v ? [ORE_COL[t.cols[i - 1]]] : [])))))];
  const tables = it.tables.map(t => `<section class="tbl">
    <h3>${esc(t.title || "升級數據")}</h3>${t.sub ? `<p class="sub">${esc(t.sub)}</p>` : ""}
    <div class="scroll"><table><thead><tr><th>等級</th>${t.cols.map(c => `<th>${esc(label(c))}</th>`).join("")}</tr></thead>
    <tbody>${t.rows.map(r => `<tr><td>${r[0] ?? ""}</td>${t.cols.map((c, i) => `<td>${cell(r[i + 1], c)}</td>`).join("")}</tr>`).join("")}</tbody></table></div></section>`).join("");
  return `${cfg ? `<a class="back" href="${BASE}#${where.v}.${where.t}">‹ 返回${esc(cfg.zh)} · ${esc(tabName)}</a>` : ""}
    <div class="hero">${img(it)}<div><div class="crumb">${esc(cfg ? cfg.zh : "")} · ${esc(where ? where.sec : "")}</div>
      <h1>${esc(nameOf(it))}</h1>${it.zh ? `<div class="en">${esc(it.en)}</div>` : ""}</div></div>
    ${it.desc ? `<p class="desc">${esc(it.desc)}</p>` : ""}
    ${rel.length ? `<div class="links">${rel.map(r => `<a href="${itemHref(r.id)}">${img(r)}${esc(nameOf(r))}</a>`).join("")}</div>` : ""}
    ${attrHtml}
    ${used.length ? `<div class="legend">${used.map(r => `<span>${resIcon(r)}${esc(value(r))}</span>`).join("")}${discount ? `<span class="disc">已套用月卡 -${discount}%</span>` : ""}</div>` : ""}
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

function footer() {
  return `<footer><p>資料來源：<a href="https://github.com/chiefpansancolt/clash-of-clans-data" target="_blank" rel="noopener">clash-of-clans-data</a>，© 2026 Christopher Pezza，依 MIT 授權使用（<a href="https://github.com/powber-21/coc-upgrade-zh/blob/main/THIRD_PARTY_LICENSES.md" target="_blank" rel="noopener">授權條文</a>）。中文名稱為對照翻譯，可能與遊戲內略有不同。</p>
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
window.addEventListener("hashchange", () => { $("#q").value = ""; render(); window.scrollTo(0, 0); });
$("#q").addEventListener("input", render);
render();
