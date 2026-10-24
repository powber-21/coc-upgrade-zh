"""把 clash-of-clans-data 的 JSON 轉成網站，輸出到 site/（src/ 裡是頁面外框、樣式與程式）。

用法: python build.py <clash-of-clans-data 資料夾路徑>
"""
import base64
import glob
import hashlib
import io
import json
import os
import shutil
import sys
from html import escape as esc

from PIL import Image

SRC = sys.argv[1]
SITE_URL = "https://powber-21.github.io/coc-upgrade-zh"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")

# 所有中文翻譯（名稱、欄位、攻擊模式、數值文字）都在 zh.json
ZH = json.load(open(os.path.join(HERE, "zh.json"), encoding="utf8"))
ZH_NAMES = ZH["names"]

# (base, 資料夾, 中文分類名)，順序即顯示順序
GROUPS = [
    ("home", "town-hall", "大本營"),
    ("home", "defenses", "防禦建築"),
    ("home", "crafted-defenses", "工藝防禦"),
    ("home", "traps", "陷阱"),
    ("home", "walls", "城牆"),
    ("home", "resource-buildings", "資源建築"),
    ("home", "army-buildings", "軍隊建築"),
    ("home", "troops", "兵種"),
    ("home", "super-troops", "超級兵種"),
    ("home", "spells", "法術"),
    ("home", "siege-machines", "攻城機器"),
    ("home", "heroes", "英雄"),
    ("home", "hero-equipment", "英雄裝備"),
    ("home", "pets", "戰寵"),
    ("home", "guardians", "守衛"),
    ("home", "other", "其他建築"),
    ("home", "other/helpers", "助手"),
    ("builder", "builder-hall", "建築大師基地"),
    ("builder", "defenses", "防禦建築"),
    ("builder", "traps", "陷阱"),
    ("builder", "walls", "城牆"),
    ("builder", "resource-buildings", "資源建築"),
    ("builder", "army-buildings", "軍隊建築"),
    ("builder", "troops", "兵種"),
    ("builder", "heroes", "英雄"),
    ("builder", "other", "其他建築"),
    ("clan-capital", "halls", "都城大廳"),
    ("clan-capital", "defenses", "防禦建築"),
    ("clan-capital", "traps", "陷阱"),
    ("clan-capital", "walls", "城牆"),
    ("clan-capital", "army-buildings", "軍隊建築"),
    ("clan-capital", "army-buildings/barracks", "兵營"),
    ("clan-capital", "army-buildings/spell-factories", "法術工廠"),
    ("clan-capital", "troops", "兵種"),
    ("clan-capital", "spells", "法術"),
    ("clan-capital", "other/houses", "房屋"),
    ("clan", "", "部落等級"),
]

SKIP_KEYS = {"images", "image", "badge", "level"}
# 「每一個建築」各自的費用清單（例如第 2 個軍營要多少錢），在項目頁另外列一張表
INSTANCE_LISTS = {"instances": "每個建築的建造費用", "placementCosts": "每間小屋的放置費用"}
TIME_KEYS = {"days", "hours", "minutes", "seconds"}

# 每個 base 的「需求欄位 → 對應建築 id」，用來推算各大本營等級的上限
REQS = {
    "home": {
        "laboratoryRequired": "laboratory",
        "heroHallLevelRequired": "hero-hall",
        "petHouseLevelRequired": "pet-house",
        "blacksmithLevelRequired": "blacksmith",
    },
    "builder": {"starLabRequired": "star-laboratory"},
}
HALL_FIELD = {
    "home": ("townHallRequired",),
    "builder": ("builderHallRequired", "builderHallLevelRequired"),
}


def is_time(v):
    return isinstance(v, dict) and set(v) <= TIME_KEYS and v


def has_levels(v):
    """召喚單位、技能、大本營武器這類「有自己一套等級」的子資料。"""
    return isinstance(v, dict) and isinstance(v.get("levels"), list) and bool(v["levels"])


def camel(name):
    """"Hog Rider" -> "hogRider"，當作欄位名稱的開頭，網站會把它換成項目的中文名稱。"""
    w = [x for x in "".join(c if c.isalnum() else " " for c in name).split()]
    return w[0].lower() + "".join(x.capitalize() for x in w[1:]) if w else name


def zh_name(name):
    return ZH_NAMES.get(name) or name


def secs(t):
    return t.get("days", 0) * 86400 + t.get("hours", 0) * 3600 + t.get("minutes", 0) * 60 + t.get("seconds", 0)


def flatten(obj, prefix="", multi=False):
    """把一個等級的資料攤平成 [(欄位路徑, 值)]。"""
    out = []
    for k, v in obj.items():
        if k in SKIP_KEYS or k == "supercharge" or k.endswith("Resource"):
            continue
        path = f"{prefix}{k}"
        if is_time(v):
            out.append((path, {"t": secs(v)}))
        elif k == "stats" and isinstance(v, dict) and all(isinstance(x, dict) for x in v.values()):
            for m, sv in v.items():
                out += flatten(sv, f"@{m}." if multi else "")
        elif k == "stats" and isinstance(v, dict):
            out += flatten(v)
        elif has_levels(v):
            continue  # 有自己等級的子資料（例如大本營武器）另外列表，見 sub_tables
        elif isinstance(v, dict):
            out += flatten(v, path + ".")
        elif isinstance(v, list):
            out.append((path, "、".join(str(x) if not isinstance(x, dict) else json.dumps(x, ensure_ascii=False) for x in v)))
        else:
            out.append((path, v))
    return out


def cost_with_resource(level, key, v):
    res = level.get(key + "Resource")
    return {"c": v, "r": res} if res else v


def table(levels, title=None):
    cols, rows = [], []
    # 只要有任何一級有多種攻擊模式，整張表都標上模式，欄位才會對齊
    multi = any(isinstance(lv.get("stats"), dict) and len(lv["stats"]) > 1
                and all(isinstance(x, dict) for x in lv["stats"].values()) for lv in levels)
    for lv in levels:
        row = {}
        for path, v in flatten(lv, multi=multi):
            if path in lv and isinstance(lv.get(path + "Resource"), str):
                v = cost_with_resource(lv, path, v)
            row[path] = v
            if path not in cols:
                cols.append(path)
        lvl = lv.get("level")
        rows.append((f"超充 {lvl}" if lv.get("supercharge") else lvl, row))
    cols = [c for c in cols if any(r.get(c) not in (None, "") for _, r in rows)]
    return {"title": title, "cols": cols, "rows": [[lvl] + [r.get(c) for c in cols] for lvl, r in rows]}


def attrs(d):
    out = []
    for k, v in d.items():
        if k in ("id", "dataId", "name", "description", "base", "category", "levels", "images", "image",
                 "superTroop", "modules", "availablePerTownHall", "availablePerBuilderHall",
                 "availablePerCapitalHall", "availablePerDistrict", "isCurrent"):
            continue
        if v in (None, "", []) or (k.endswith("Resource") and k[:-8] in d) or k in INSTANCE_LISTS:
            continue
        if has_levels(v):
            # 子資料的固定屬性放在這裡（例如「廢墟騎士 · 移動速度」），每一級的數值見 sub_tables
            out += [[f"{k}.{p}", x] for p, x in attrs(v)]
        elif isinstance(v, list) and v and all(has_levels(x) and x.get("name") for x in v):
            for u in v:
                out += [[f"{camel(u['name'])}.{p}", x] for p, x in attrs(u)]
        elif isinstance(v, list) and v and all(isinstance(x, dict) and x.get("name") for x in v):
            # 例如守衛哨站的防守部隊：[{name, count}] -> ["狂暴野蠻人 ×1", ...]
            out.append([k, [zh_name(x["name"]) + (f" ×{x['count']}" if "count" in x else "") for x in v]])
        elif is_time(v):
            out.append([k, {"t": secs(v)}])
        elif isinstance(d.get(k + "Resource"), str):
            out.append([k, {"c": v, "r": d[k + "Resource"]}])
        elif k == "modes" and isinstance(v, dict):
            for m, mv in v.items():
                for p, x in flatten(mv, "" if len(v) == 1 else f"@{m}."):
                    out.append([p, x])
        elif k in ("mode", "stats") and isinstance(v, dict):
            for p, x in flatten(v):
                out.append([p, x])
        elif isinstance(v, dict):
            for p, x in flatten(v, k + "."):
                out.append([p, x])
        elif isinstance(v, list):
            out.append([k, [x if not isinstance(x, dict) else json.dumps(x, ensure_ascii=False) for x in v]])
        else:
            out.append([k, v])
    return out


IMAGES = {}  # 縮圖檔名 -> 內容，write_site 時寫到 site/img/


def thumb(rel, size=88, inline=False):
    """縮小成 webp。項目圖存成獨立檔案（img/<內容雜湊>.webp，看到才下載）；inline=True 時直接內嵌（資源小圖示）。"""
    if not rel:
        return None
    p = os.path.join(SRC, rel)
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGBA")
    im.thumbnail((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=80, method=6)
    if inline:
        return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    name = f"img/{hashlib.sha1(buf.getvalue()).hexdigest()[:10]}.webp"
    IMAGES[name] = buf.getvalue()
    return name


# 資源圖示（遊戲內圖案），鍵是資料裡的資源名稱
RES_ICONS = {
    "Gold": "images/other/gold.png",
    "Elixir": "images/other/elixir.png",
    "Dark Elixir": "images/other/dark-elixir.png",
    "Builder Gold": "images/other/gold-b.png",
    "Builder Elixir": "images/other/elixir-b.png",
    "Capital Gold": "images/other/gold-c.png",
    "Gems": "images/other/gem.png",
    "Shiny Ore": "images/other/ore/shiny-ore.png",
    "Glowy Ore": "images/other/ore/glowy-ore.png",
    "Starry Ore": "images/other/ore/starry-ore.png",
}


def pick_image(d):
    imgs = d.get("images")
    if isinstance(imgs, dict) and (imgs.get("icon") or imgs.get("normal")):
        return imgs.get("icon") or imgs["normal"]
    if isinstance(imgs, list) and imgs:
        return imgs[-1].get("normal")
    for lv in reversed(d.get("levels") or []):
        li = lv.get("images")
        if isinstance(li, dict) and li:
            return li.get("normal") or next(iter(li.values()))
    return d.get("image") if isinstance(d.get("image"), str) else None


def available(d):
    for key, hall in (("availablePerTownHall", "townHallLevel"), ("availablePerBuilderHall", "builderHallLevel")):
        if d.get(key):
            return {str(x.get(hall)): x.get("count") for x in d[key]}
    return None


def sub_tables(d):
    """子資料的表格：召喚單位、技能、大本營武器（每個大本營等級一張），以及每個建築各自的費用。
    標上 extra，網站就不會拿它們的等級去算「最高等級」或跟大本營等級比較。"""
    out = []

    def add(t, en=None, head=None):
        t["extra"] = True
        if en:
            t["en"] = en  # 英文原名（中文名稱還沒翻譯時可以對照）
        if head:
            t["head"] = head
        out.append(t)

    def unit_table(u, title=None):
        # 技能的等級欄位叫 abilityLevel，統一當成等級
        levels = [{**{k: v for k, v in lv.items() if k != "abilityLevel"}, "level": lv.get("level", lv.get("abilityLevel"))}
                  for lv in u["levels"]]
        name = u.get("name")
        add(table(levels, title or (zh_name(name) if name else None)), en=name)

    for k, v in d.items():
        if k in ("superTroop", "levels", "modules"):
            continue
        if k in INSTANCE_LISTS and isinstance(v, list):
            rows = [{**{a: b for a, b in x.items() if a != "instance"}, "level": x.get("instance")} for x in v]
            add(table(rows, INSTANCE_LISTS[k]), head="第幾個")
        elif has_levels(v):
            unit_table(v)
        elif isinstance(v, list) and v and all(has_levels(x) for x in v):
            for u in v:
                unit_table(u)
    # 大本營武器：每個大本營等級的武器各有一套等級
    for lv in d.get("levels") or []:
        for k, v in lv.items():
            if has_levels(v):
                name = v.get("name")
                t_title = f"{zh_name(name) if name else k}（{zh_name(d['name'])} {lv.get('level')} 級）"
                unit_table(v, t_title)
    return out


def make_item(d, base, gkey, uid):
    item = {
        "id": uid,
        "en": d["name"],
        "zh": ZH_NAMES.get(f"{base}/{d['name']}") or ZH_NAMES.get(d["name"]),
        "base": base,
        "group": gkey,
        "desc": d.get("description"),
        "attrs": attrs(d),
        "tables": [],
        "img": thumb(pick_image(d)),
    }
    if d.get("levels"):
        item["tables"].append(table(d["levels"]))
        item["_levels"] = d["levels"]
    item["tables"] += sub_tables(d)
    for m in d.get("modules") or []:
        t = table(m["upgrades"], m.get("name"))
        t["sub"] = m.get("controls")
        item["tables"].append(t)
    if d.get("isCurrent") is not None:
        item["attrs"].append(["isCurrent", d["isCurrent"]])
    av = available(d)
    if av:
        item["count"] = av
    return item


def _gradient(w, h, top, bottom):
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / (h - 1)
        g.putpixel((0, y), tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return g.resize((w, h))


def _paste(canvas, rel, height, center_x, bottom_y):
    im = Image.open(os.path.join(SRC, rel)).convert("RGBA")
    im = im.resize((round(im.width * height / im.height), height), Image.LANCZOS)
    canvas.alpha_composite(im, (round(center_x - im.width / 2), bottom_y - im.height))


def make_card_art():
    """首頁四張卡片的插圖：art/ 裡的 AI 繪圖原檔，縮小轉成 card-<名稱>.webp。"""
    for path in glob.glob(os.path.join(HERE, "art", "*.jpg")):
        im = Image.open(path).convert("RGB")
        im = im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS)
        im.save(os.path.join(OUT, f"card-{os.path.splitext(os.path.basename(path))[0]}.webp"), quality=82)


def make_share_images():
    """產生 LINE / 社群分享縮圖 (og.png) 與手機主畫面圖示 (apple-touch-icon.png)。"""
    th = "images/home/town-hall/normal/level-18.png"
    # 分享縮圖用首頁「家鄉」卡片的插圖，縮到 630 高、左右置中裁成 1200 寬
    og = Image.open(os.path.join(HERE, "art", "home.jpg")).convert("RGB")
    og = og.resize((round(og.width * 630 / og.height), 630), Image.LANCZOS)
    x = (og.width - 1200) // 2
    og.crop((x, 0, x + 1200, 630)).save(os.path.join(OUT, "og.png"), optimize=True)

    icon = _gradient(180, 180, (255, 214, 102), (214, 140, 20)).convert("RGBA")
    _paste(icon, th, 150, 90, 168)
    icon.convert("RGB").save(os.path.join(OUT, "apple-touch-icon.png"), optimize=True)
    icon.resize((32, 32), Image.LANCZOS).convert("RGB").save(os.path.join(OUT, "favicon-32.png"), optimize=True)


def data_date():
    """資料最後更新的日期：資料來源 CHANGELOG 裡最新一版的發布日期（找不到就用最後一次提交的日期）。"""
    import datetime, re, subprocess
    try:
        m = re.search(r"^## \[[^\]]+\] [-—] (\d{4}-\d{2}-\d{2})", open(os.path.join(SRC, "CHANGELOG.md"), encoding="utf8").read(), re.M)
        if m:
            return m.group(1)
    except OSError:
        pass
    try:
        return subprocess.run(["git", "-C", SRC, "log", "-1", "--format=%cs"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return datetime.date.today().isoformat()


def write_seo_files(ids):
    """產生給搜尋引擎的 robots.txt 與 sitemap.xml（首頁加上每個項目頁）。"""
    # 用資料最後更新的日期，而不是每次產生網頁的日期，避免假裝每天都有新內容
    today = data_date()
    open(os.path.join(OUT, "robots.txt"), "w", encoding="utf8").write(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/{i}/" for i in ids]
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
        + "</urlset>\n")


def main():
    items, groups, order = {}, [], {}
    for base, folder, zh in GROUPS:
        gkey = f"{base}/{folder}"
        ids = []
        if folder == "super-troops":
            for f in sorted(glob.glob(os.path.join(SRC, "data/home/troops/*.json"))):
                d = json.load(open(f, encoding="utf8"))
                st = d.get("superTroop")
                if not st:
                    continue
                st = dict(st, base="home")
                uid = "home-" + st["id"]
                it = make_item(st, "home", gkey, uid)
                it["from"] = "home-" + d["id"]
                items[uid] = it
                ids.append(uid)
                items["home-" + d["id"]]["super"] = uid
            ids.sort(key=lambda i: order[items[i]["from"]])
            groups.append({"key": gkey, "base": "home", "zh": zh, "items": ids})
            continue
        for f in sorted(glob.glob(os.path.join(SRC, "data", base, folder, "*.json"))):
            d = json.load(open(f, encoding="utf8"))
            if not isinstance(d, dict) or not (d.get("levels") or d.get("modules")):
                continue
            uid = f"{base}-{d['id']}"
            items[uid] = make_item(d, base, gkey, uid)
            ids.append(uid)
            order[uid] = d.get("dataId") or 10**10
        # dataId 依遊戲內解鎖順序遞增，用它排序才會跟遊戲一樣
        ids.sort(key=lambda i: order[i])
        groups.append({"key": gkey, "base": base, "zh": zh, "items": ids})

    # 各大本營 / 建築大師基地等級的最高等級
    for base, fields in HALL_FIELD.items():
        hall_id = f"{base}-town-hall" if base == "home" else f"{base}-builder-hall"
        max_hall = len(items[hall_id]["_levels"])
        memo = {}

        def max_level(uid, hall, stack=()):
            key = (uid, hall)
            if key in memo:
                return memo[key]
            it = items.get(uid)
            best = 0
            if it and "_levels" in it and uid not in stack:
                for lv in it["_levels"]:
                    ok = True
                    hr = next((lv[f] for f in fields if lv.get(f) is not None), None)
                    if hr is not None and hr > hall:
                        ok = False
                    for rf, bid in REQS.get(base, {}).items():
                        if ok and lv.get(rf):
                            if lv[rf] > max_level(f"{base}-{bid}", hall, stack + (uid,)):
                                ok = False
                    if ok:
                        best = max(best, lv["level"])
                    else:
                        break
            memo[key] = best
            return best

        for uid, it in items.items():
            if it["base"] != base or "_levels" not in it:
                continue
            lv0 = it["_levels"]
            has_req = any(any(lv.get(f) is not None for f in fields) or any(lv.get(r) for r in REQS.get(base, {})) for lv in lv0)
            if not has_req:
                continue
            it["hallMax"] = [max_level(uid, h) for h in range(1, max_hall + 1)]
        items[hall_id]["hallMax"] = list(range(1, max_hall + 1))

    for it in items.values():
        it.pop("_levels", None)

    data = {"groups": groups, "items": items, "res": {k: thumb(v, 48, inline=True) for k, v in RES_ICONS.items()},
            "updated": data_date(), "zh": {k: ZH[k] for k in ("labels", "modes", "values")}}
    write_site(data)


PRERENDER_JS = """<script type="application/json" id="out"></script>
<script>
const out = {};
if (BASE) {
  for (const id in DATA.items) out[id] = { view: itemView(DATA.items[id]) + footer(), crumbs: $("#crumbs").innerHTML };
  out.faq = { view: faqView() + footer(), crumbs: $("#crumbs").innerHTML };
}
else out[""] = { view: landingView() + footer(), crumbs: $("#crumbs").innerHTML };
document.getElementById("out").textContent = JSON.stringify(out).replace(/</g, "\\\\u003c");
</script>"""


def find_browser():
    for name in ("google-chrome", "chromium", "chromium-browser", "msedge"):
        if shutil.which(name):
            return shutil.which(name)
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        if os.path.exists(p):
            return p
    return None


def prerender():
    """用無頭瀏覽器執行 app.js，把首頁和每個項目頁畫好的畫面存下來，直接寫進網頁。
    找不到瀏覽器時回傳 {}，網頁會改成顯示「載入中」再由瀏覽器畫出來。"""
    import subprocess, tempfile
    browser = find_browser()
    if not browser:
        if os.environ.get("CI"):
            sys.exit("找不到 Chrome，無法預先產生網頁")
        print("找不到瀏覽器，略過預先產生")
        return {}
    result = {}
    with tempfile.TemporaryDirectory() as profile:
        for path, base in (("_pre_root.html", ""), ("_pre/index.html", "../")):
            full = os.path.join(OUT, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            open(full, "w", encoding="utf8").write(
                f'<!doctype html><html data-base="{base}"><meta charset="utf-8"><body>'
                '<input id="q"><select id="pass"></select><nav id="crumbs"></nav><div id="view"></div>'
                f'<script src="{base}data.js"></script><script src="{base}app.js"></script>{PRERENDER_JS}</body></html>')
            dom = subprocess.run(
                [browser, "--headless=new", "--disable-gpu", "--no-sandbox", f"--user-data-dir={profile}",
                 "--allow-file-access-from-files", "--virtual-time-budget=20000", "--dump-dom",
                 "file:///" + os.path.abspath(full).replace(os.sep, "/")],
                capture_output=True, timeout=300).stdout.decode("utf8")
            start = dom.index('id="out">') + len('id="out">')
            result.update(json.loads(dom[start:dom.index("</script>", start)]))
        os.remove(os.path.join(OUT, "_pre_root.html"))
        shutil.rmtree(os.path.join(OUT, "_pre"))
    return result


def write_site(data):
    """輸出整個網站到 site/：共用的 data.js / app.js / styles.css，首頁，以及每個項目一頁。"""
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):
        p = os.path.join(OUT, name)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    data_js = "window.DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"
    app_js = open(os.path.join(HERE, "src/app.js"), encoding="utf8").read()
    css = open(os.path.join(HERE, "src/styles.css"), encoding="utf8").read()
    ver = hashlib.sha1((data_js + app_js + css).encode()).hexdigest()[:8]
    for name, text in (("data.js", data_js), ("app.js", app_js), ("styles.css", css)):
        open(os.path.join(OUT, name), "w", encoding="utf8").write(text)
    os.makedirs(os.path.join(OUT, "img"))
    for name, content in IMAGES.items():
        open(os.path.join(OUT, name), "wb").write(content)
    shell = open(os.path.join(HERE, "src/shell.html"), encoding="utf8").read()
    items, groups = data["items"], data["groups"]
    group_zh = {g["key"]: g["zh"] for g in groups}
    base_zh = {"home": "家鄉", "builder": "夜世界", "clan-capital": "部落都城", "clan": "部落"}

    pre = prerender()
    loading = '<div class="loading" role="status">載入中<i></i><i></i><i></i></div>'

    def page(path, base, item, title, desc, static):
        # 有預先產生的畫面就直接放進去；沒有的話先顯示「載入中」，原本的文字清單藏起來給搜尋引擎看
        p = pre.get(item)
        view = p["view"] if p else loading
        if static:
            view += f'<div class="seo">{static}</div>'
        html = shell
        for k, v in (("__TITLE__", esc(title)), ("__DESC__", esc(desc)), ("__URL__", f"{SITE_URL}/{path}"),
                     ("__BASE__", base), ("__ITEM__", item), ("__VER__", ver), ("__SITE__", SITE_URL),
                     ("__CRUMBS__", p["crumbs"] if p else ""), ("__STATIC__", view)):
            html = html.replace(k, v)
        os.makedirs(os.path.join(OUT, path), exist_ok=True)
        open(os.path.join(OUT, path, "index.html"), "w", encoding="utf8").write(html)

    # 首頁：靜態內容列出所有項目的連結，讓搜尋引擎找得到每一頁（瀏覽器載入後會被 app.js 取代）
    lists = "".join(
        f"<h2>{esc(base_zh.get(g['base'], ''))} · {esc(g['zh'])}</h2><ul>"
        + "".join(f'<li><a href="{i}/">{esc(items[i]["zh"] or items[i]["en"])}</a></li>' for i in g["items"])
        + "</ul>" for g in groups if g["items"])
    page("", "", "", "部落衝突升級數據｜COC 兵種、建築、英雄升級時間與費用",
         "部落衝突（Clash of Clans, COC）繁體中文升級數據：所有兵種、建築、法術、英雄、裝備與戰寵的升級時間、升級費用和屬性，可依大本營等級查詢上限，每天自動更新。",
         "<h1>部落衝突升級數據</h1>" + lists)

    for uid, it in items.items():
        name = it["zh"] or it["en"]
        en = f"（{it['en']}）" if it["zh"] else ""
        kind = group_zh.get(it["group"], "")
        rows = it["tables"][0]["rows"] if it["tables"] else []
        summary = f"共 {len(rows)} 個等級" if rows else ""
        title = f"{name}升級數據｜{it['en']}｜部落衝突 COC" if it["zh"] else f"{name} 升級數據｜部落衝突 COC"
        desc = (f"部落衝突{base_zh.get(it['base'], '')}{kind}「{name}」{en}各等級的升級費用、升級時間、生命值與傷害"
                f"{'，' + summary if summary else ''}。COC 繁體中文升級數據，每天自動更新。")
        static = (f"<h1>{esc(name)}</h1><p>{esc(it['en'])}</p><p>{esc(desc)}</p>"
                  + (f"<p>{esc(it['desc'])}</p>" if it.get("desc") else "") + '<p><a href="../">回到部落衝突升級數據首頁</a></p>')
        page(f"{uid}/", "../", uid, title, desc, "" if uid in pre else static)

    page("faq/", "../", "faq", "常見問題｜部落衝突數據",
         "部落衝突數據網站的常見問題：資料來源、更新頻率、中文名稱、怎麼加入手機主畫面。", "")

    make_share_images()
    make_card_art()
    write_seo_files(list(items) + ["faq"])
    print(f"items={len(items)} groups={len(groups)} data.js={len(data_js.encode()) / 1e6:.2f}MB pages={len(items) + 1}")


main()
