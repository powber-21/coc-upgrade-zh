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
SITE_URL = "https://cocdata.app"
SITE_NAME = "部落衝突數據"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")

# 所有中文翻譯（名稱、欄位、攻擊模式、數值文字）都在 zh.json
ZH = json.load(open(os.path.join(HERE, "zh.json"), encoding="utf8"))
ZH_NAMES = ZH["names"]

# (base, 資料夾, 中文分類名)，順序即顯示順序
GROUPS = [
    ("home", "town-hall", "大本營"),
    ("home", "defenses", "防禦建築"),
    ("home", "crafted-defenses", "精工防禦"),
    ("home", "traps", "陷阱"),
    ("home", "walls", "城牆"),
    ("home", "resource-buildings", "資源建築"),
    ("home", "army-buildings", "軍隊建築"),
    ("home", "troops", "兵種"),
    ("home", "super-troops", "超級部隊"),
    ("home", "spells", "法術"),
    ("home", "siege-machines", "攻城機器"),
    ("home", "heroes", "英雄"),
    ("home", "hero-equipment", "英雄裝備"),
    ("home", "pets", "戰寵"),
    ("home", "guardians", "守衛"),
    ("home", "other", "其他建築"),
    ("home", "other/helpers", "助手"),
    ("builder", "builder-hall", "建築大師大本營"),
    ("builder", "defenses", "防禦建築"),
    ("builder", "traps", "陷阱"),
    ("builder", "walls", "城牆"),
    ("builder", "resource-buildings", "資源建築"),
    ("builder", "army-buildings", "軍隊建築"),
    ("builder", "troops", "兵種"),
    ("builder", "heroes", "英雄"),
    ("builder", "other", "其他建築"),
    ("clan-capital", "halls", "首都大本營"),
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


# 這些欄位的值是兵種、法術、裝備等的英文名稱（例如法術工廠的「解鎖法術」），要換成中文名稱
NAME_KEYS = ("unlocksSpell", "requiredSpellFactory", "unitName", "specialAbility")


def is_name_key(k):
    return k.startswith("unlocked") or k.endswith("Unlocked") or k in NAME_KEYS


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
            if is_name_key(k):
                v = [zh_name(x) if isinstance(x, str) else x for x in v]
            out.append((path, "、".join(str(x) if not isinstance(x, dict) else json.dumps(x, ensure_ascii=False) for x in v)))
        elif is_name_key(k) and isinstance(v, str):
            out.append((path, zh_name(v)))
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
        # 超級蓄能的等級寫成 {"sc": 1}，網站會顯示成蓄能圖示加等級
        rows.append(({"sc": lvl} if lv.get("supercharge") else lvl, row))
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
            if all("count" in x for x in v):
                # 例如守衛哨站的防守部隊：網站用英文名稱找到兵種，顯示圖示並連到它的頁面
                out.append([k, [{"u": x["name"], "zh": zh_name(x["name"]), "n": x["count"]} for x in v]])
            else:
                out.append([k, [zh_name(x["name"]) for x in v]])
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
        elif is_name_key(k) and isinstance(v, str):
            out.append([k, zh_name(v)])
        else:
            out.append([k, v])
    return out


IMAGES = {}  # 縮圖檔名 -> 內容，write_site 時寫到 site/img/
NO_THUMB = []  # 比對舊版資料時不需要圖片，放進任何東西就略過縮圖


def thumb(rel, size=88, inline=False):
    """縮小成 webp。項目圖存成獨立檔案（img/<內容雜湊>.webp，看到才下載）；inline=True 時直接內嵌（資源小圖示）。"""
    if not rel or NO_THUMB:
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
    "Supercharge": "images/other/supercharge.png",
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
        t = table(levels, title or (zh_name(name) if name else None))
        img = thumb(pick_image(u))  # 召喚單位、武器有自己的圖示，放在表格標題旁
        if img:
            t["img"] = img
        add(t, en=name)

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
                t_title = f"{zh_name(name) if name else k}（{zh_name(d['name'])}{lv.get('level')}級）"
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


# 版本更新從這天開始；更早是資料來源剛建立時的整理，不算遊戲更新
LOG_SINCE = "2026-09-01"


def git_src(*args):
    import subprocess
    return subprocess.run(["git", "-C", SRC, *args], capture_output=True, encoding="utf8", check=True).stdout


def items_at(rev, path):
    """某個版本的一個資料檔，轉成網站項目（兵種檔會多帶出它的超級部隊）。"""
    import subprocess
    try:
        d = json.loads(git_src("show", f"{rev}:{path}"))
    except (subprocess.CalledProcessError, ValueError):
        return {}
    if not isinstance(d, dict) or not d.get("id") or not (d.get("levels") or d.get("modules")):
        return {}
    base = path.split("/")[1]
    out = {f"{base}-{d['id']}": make_item(d, base, "", "")}
    if d.get("superTroop"):
        out["home-" + d["superTroop"]["id"]] = make_item(dict(d["superTroop"], base="home"), "home", "", "")
    return out


def diff_item(old, new):
    """比對同一個項目的新舊版本，列出新增的等級和改變的數值。"""
    same = lambda a, b: (a in (None, "")) and (b in (None, "")) or a == b
    ch = []
    key = lambda t: t.get("en") or t.get("title") or ""
    olds = {key(t): t for t in old["tables"]}
    # 整個新增的召喚單位只寫「新增」，不再逐項列出它的屬性
    fresh = tuple(camel(t["en"]) + "." for t in new["tables"] if t.get("en") and key(t) not in olds)
    oa = {k: v for k, v in old["attrs"]}
    for k, v in new["attrs"]:
        if not same(oa.get(k), v) and not (k not in oa and fresh and k.startswith(fresh)):
            ch.append({"k": k, "o": oa.get(k), "n": v})
    for i, t in enumerate(new["tables"]):
        tbl = t.get("title") if i else None
        ot = olds.get(key(t))
        if not ot:
            ch.append({"tbl": tbl or "", "add": 1})
            continue
        orows = {json.dumps(r[0]): dict(zip(ot["cols"], r[1:])) for r in ot["rows"]}
        added = []
        for r in t["rows"]:
            o = orows.get(json.dumps(r[0]))
            if o is None:
                added.append(r[0])
                continue
            for c, v in zip(t["cols"], r[1:]):
                if not same(o.get(c), v):
                    ch.append({"tbl": tbl, "lv": r[0], "k": c, "o": o.get(c), "n": v})
        if added:
            ch.append({"tbl": tbl, "lvAdd": added})
    return ch


def changelog(ids):
    """用資料來源的 Git 歷史，比對每一天的更新新增了哪些項目、改了哪些數值。
    ids 是網站現有項目的順序；找不到歷史（例如只下載最新版）時回傳空清單。"""
    import subprocess
    try:
        commits = git_src("log", "--first-parent", f"--since={LOG_SINCE}", "--format=%H %cs", "--", "data").split()
    except (OSError, subprocess.CalledProcessError):
        return []
    days = {}
    for sha, day in zip(commits[::2], commits[1::2]):
        days.setdefault(day, []).append(sha)  # 新的在前
    order = {i: n for n, i in enumerate(ids)}
    log = []
    NO_THUMB.append(1)
    try:
        for day, shas in days.items():
            old_rev, new_rev = shas[-1] + "^", shas[0]
            try:
                files = git_src("diff", "--no-renames", "--name-only", old_rev, new_rev, "--", "data").split()
            except subprocess.CalledProcessError:
                break  # 再往前的歷史沒有下載
            entries = {}
            for f in files:
                if not f.endswith(".json"):
                    continue
                old, new = items_at(old_rev, f), items_at(new_rev, f)
                for uid, it in new.items():
                    if uid not in order:
                        continue
                    if uid not in old:
                        entries[uid] = {"id": uid, "new": 1}
                    else:
                        ch = diff_item(old[uid], it)
                        if ch:
                            entries[uid] = {"id": uid, "ch": ch}
            if entries:
                log.append({"date": day, "items": sorted(entries.values(), key=lambda e: order[e["id"]])})
    finally:
        NO_THUMB.clear()
    return log


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
    # 分享縮圖用首頁「家鄉村莊」卡片的插圖，縮到 630 高、左右置中裁成 1200 寬
    og = Image.open(os.path.join(HERE, "art", "home.jpg")).convert("RGB")
    og = og.resize((round(og.width * 630 / og.height), 630), Image.LANCZOS)
    x = (og.width - 1200) // 2
    og.crop((x, 0, x + 1200, 630)).save(os.path.join(OUT, "og.png"), optimize=True)

    icon = _gradient(180, 180, (255, 214, 102), (214, 140, 20)).convert("RGBA")
    _paste(icon, th, 150, 90, 168)
    icon.convert("RGB").save(os.path.join(OUT, "apple-touch-icon.png"), optimize=True)
    icon.resize((32, 32), Image.LANCZOS).convert("RGB").save(os.path.join(OUT, "favicon-32.png"), optimize=True)
    # Google 搜尋結果的網站圖示要 48px 的倍數
    icon.resize((192, 192), Image.LANCZOS).convert("RGB").save(os.path.join(OUT, "favicon-192.png"), optimize=True)


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


def license_text():
    """從 THIRD_PARTY_LICENSES.md 取出 ``` 框起來的 MIT 授權全文，給授權條文頁使用。
    原文每 80 字硬換行，在手機上會斷得很亂，所以段落內的換行改成空格，只保留段落之間的空行。"""
    md = open(os.path.join(HERE, "THIRD_PARTY_LICENSES.md"), encoding="utf8").read()
    paras = md.split("```")[1].strip().split("\n\n")
    return "\n\n".join(" ".join(line.strip() for line in p.splitlines()) for p in paras)


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
                # 有些超級部隊的資料沒寫大本營需求；它們的等級跟原兵種相同，
                # 就借用原兵種同等級的需求，「依大本營等級」才找得到它們
                reg = {lv["level"]: lv for lv in d["levels"]}
                levels = [lv if lv.get("townHallRequired") is not None or lv["level"] not in reg else
                          {**lv, **{k: reg[lv["level"]][k] for k in ("townHallRequired", "laboratoryRequired")
                                    if k in reg[lv["level"]]}}
                          for lv in st["levels"]]
                st = dict(st, base="home", levels=levels)
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

    # 各大本營 / 建築大師大本營等級的最高等級
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
            # 遊戲裡超級部隊要 11 本才能開啟
            if "from" in it:
                it["hallMax"] = [lv if h >= 11 else 0 for h, lv in enumerate(it["hallMax"], 1)]
        items[hall_id]["hallMax"] = list(range(1, max_hall + 1))

    for it in items.values():
        it.pop("_levels", None)

    data = {"groups": groups, "items": items, "res": {k: thumb(v, 48, inline=True) for k, v in RES_ICONS.items()},
            "updated": data_date(), "log": changelog([i for g in groups for i in g["items"]]),
            "zh": {k: ZH[k] for k in ("labels", "modes", "values")}, "license": license_text()}
    write_site(data)


PRERENDER_JS = """<script type="application/json" id="out"></script>
<script>
const out = {};
if (BASE) {
  for (const id in DATA.items) out[id] = { view: itemView(DATA.items[id]) + footer(), crumbs: $("#crumbs").innerHTML };
  out.faq = { view: faqView() + footer(), crumbs: $("#crumbs").innerHTML };
  out.updates = { view: updatesView() + footer(), crumbs: $("#crumbs").innerHTML };
  out.licenses = { view: licensesView() + footer(), crumbs: $("#crumbs").innerHTML };
  for (const base of ["home", "builder"])
    for (let h = 1; h <= hallMaxOf(base); h++)
      out[hallPage(base, h)] = { view: hallView(base, h) + footer(), crumbs: $("#crumbs").innerHTML, title: hallTitle(base, h) };
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
    base_zh = {"home": "家鄉村莊", "builder": "建築大師基地", "clan-capital": "部落首都", "clan": "部落"}

    pre = prerender()
    loading = '<div class="loading" role="status">載入中<i></i><i></i><i></i></div>'

    def page(path, base, item, title, desc, static, ld=""):
        # 有預先產生的畫面就直接放進去；沒有的話先顯示「載入中」，原本的文字清單藏起來給搜尋引擎看
        p = pre.get(item)
        view = p["view"] if p else loading
        if static:
            view += f'<div class="seo">{static}</div>'
        html = shell
        for k, v in (("__TITLE__", esc(title)), ("__DESC__", esc(desc)), ("__URL__", f"{SITE_URL}/{path}"),
                     ("__BASE__", base), ("__ITEM__", item), ("__VER__", ver), ("__SITE__", SITE_URL),
                     ("__CRUMBS__", p["crumbs"] if p else ""), ("__LDJSON__", ld), ("__STATIC__", view)):
            html = html.replace(k, v)
        os.makedirs(os.path.join(OUT, path), exist_ok=True)
        open(os.path.join(OUT, path, "index.html"), "w", encoding="utf8").write(html)

    # 首頁：靜態內容列出所有項目的連結，讓搜尋引擎找得到每一頁（瀏覽器載入後會被 app.js 取代）
    lists = "".join(
        f"<h2>{esc(base_zh.get(g['base'], ''))} · {esc(g['zh'])}</h2><ul>"
        + "".join(f'<li><a href="{i}/">{esc(items[i]["zh"] or items[i]["en"])}</a></li>' for i in g["items"])
        + "</ul>" for g in groups if g["items"])
    # 標題結尾統一用網站名稱 SITE_NAME，Google 比較容易認出網站叫什麼
    page("", "", "", f"部落衝突升級數據｜COC兵種、建築、英雄升級時間與費用｜{SITE_NAME}",
         "部落衝突（Clash of Clans, COC）繁體中文升級數據：所有兵種、建築、法術、英雄、裝備與戰寵的升級時間、升級費用和屬性，可依大本營等級查詢上限，每天自動更新。",
         "<h2>部落衝突升級數據</h2>" + lists)  # 畫面上已經有 <h1>，藏起來的清單不再放第二個 <h1>

    for uid, it in items.items():
        name = it["zh"] or it["en"]
        en = f"（{it['en']}）" if it["zh"] else ""
        kind = group_zh.get(it["group"], "")
        rows = it["tables"][0]["rows"] if it["tables"] else []
        summary = f"共{len(rows)}個等級" if rows else ""
        title = f"{name}升級數據｜{it['en']}｜COC｜{SITE_NAME}" if it["zh"] else f"{name}升級數據｜COC｜{SITE_NAME}"
        desc = (f"部落衝突{base_zh.get(it['base'], '')}{kind}「{name}」{en}各等級的升級費用、升級時間、生命值與傷害"
                f"{'，' + summary if summary else ''}。COC繁體中文升級數據，每天自動更新。")
        static = (f"<h1>{esc(name)}</h1><p>{esc(it['en'])}</p><p>{esc(desc)}</p>"
                  + (f"<p>{esc(it['desc'])}</p>" if it.get("desc") else "") + '<p><a href="../">回到部落衝突升級數據首頁</a></p>')
        # 麵包屑結構化資料：搜尋結果顯示「部落衝突數據 › 弓箭手」
        crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE_NAME, "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": name}]}
        ld = '<script type="application/ld+json">' + json.dumps(crumbs, ensure_ascii=False).replace("<", "\\u003c") + "</script>"
        page(f"{uid}/", "../", uid, title, desc, "" if uid in pre else static, ld)

    page("faq/", "../", "faq", "常見問題｜部落衝突數據",
         "部落衝突數據網站的常見問題：資料來源、更新頻率、中文名稱、怎麼加入手機主畫面。", "")

    page("updates/", "../", "updates", "版本更新｜部落衝突數據",
         "部落衝突（COC）版本更新：每次更新新增的兵種、建築、裝備，以及調整過的升級費用、時間和數值。", "")

    page("licenses/", "../", "licenses", "授權條文｜部落衝突數據",
         "部落衝突數據網站使用的資料來源與授權條文。", "")

    # 依大本營等級：每個等級一頁（th1/…、bh1/…），標題由 app.js 的 hallTitle() 產生
    halls = []
    for base, hall_id, prefix, zh in (("home", "home-town-hall", "th", "大本營"),
                                      ("builder", "builder-builder-hall", "bh", "建築大師大本營")):
        for h in range(1, len(items[hall_id]["hallMax"]) + 1):
            hid = f"{prefix}{h}"
            halls.append(hid)
            title = pre[hid]["title"] if hid in pre else f"{zh}{h}級升級數據｜{SITE_NAME}"
            desc = (f"部落衝突（COC）{zh}{h}級（{h}本）時，所有建築、兵種、法術、英雄與裝備能升到的最高等級"
                    f"和可擁有數量，一頁查完。")
            page(f"{hid}/", "../", hid, title, desc, "")

    make_share_images()
    make_card_art()
    write_seo_files(list(items) + ["faq", "updates"] + halls)
    print(f"items={len(items)} groups={len(groups)} data.js={len(data_js.encode()) / 1e6:.2f}MB pages={len(items) + 1}")


main()
