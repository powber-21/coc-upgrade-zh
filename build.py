"""把 clash-of-clans-data 的 JSON 轉成 App 用的精簡資料，並嵌入 template.html 產生 index.html。

用法: python build.py <clash-of-clans-data 資料夾路徑>
"""
import base64
import glob
import io
import json
import os
import sys

from PIL import Image

from zh import ZH_NAMES

SRC = sys.argv[1]
SITE_URL = "https://powber-21.github.io/coc-upgrade-zh"
HERE = os.path.dirname(os.path.abspath(__file__))

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
        if v in (None, "", []) or (k.endswith("Resource") and k[:-8] in d):
            continue
        if is_time(v):
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


def thumb(rel, size=88):
    if not rel:
        return None
    p = os.path.join(SRC, rel)
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGBA")
    im.thumbnail((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=80, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


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


def make_share_images():
    """產生 LINE / 社群分享縮圖 (og.png) 與手機主畫面圖示 (apple-touch-icon.png)。"""
    th = "images/home/town-hall/normal/level-18.png"
    og = _gradient(1200, 630, (120, 190, 90), (40, 95, 45)).convert("RGBA")
    _paste(og, "images/home/heroes/barbarian-king/icon.png", 440, 270, 660)
    _paste(og, "images/home/heroes/archer-queen/icon.png", 440, 930, 660)
    _paste(og, th, 520, 600, 610)
    og.convert("RGB").save(os.path.join(HERE, "og.png"), optimize=True)

    icon = _gradient(180, 180, (255, 214, 102), (214, 140, 20)).convert("RGBA")
    _paste(icon, th, 150, 90, 168)
    icon.convert("RGB").save(os.path.join(HERE, "apple-touch-icon.png"), optimize=True)
    icon.resize((32, 32), Image.LANCZOS).convert("RGB").save(os.path.join(HERE, "favicon-32.png"), optimize=True)


def write_seo_files():
    """產生給搜尋引擎的 robots.txt 與 sitemap.xml。"""
    import datetime
    today = datetime.date.today().isoformat()
    open(os.path.join(HERE, "robots.txt"), "w", encoding="utf8").write(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod></url>\n"
        "</urlset>\n")


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

    data = {"groups": groups, "items": items, "res": {k: thumb(v, 48) for k, v in RES_ICONS.items()}}
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf8").read()
    out = tpl.replace("/*__DATA__*/null", js).replace("__SITE__", SITE_URL)
    make_share_images()
    write_seo_files()
    open(os.path.join(HERE, "index.html"), "w", encoding="utf8").write(out)
    print(f"items={len(items)} groups={len(groups)} size={len(out.encode()) / 1e6:.2f}MB")


main()
