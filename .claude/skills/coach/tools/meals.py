"""/coach meals: turns a meal plan (written by Claude as JSON) into a recipe book PDF and a weekly grocery list that hit the
client's macros. The macros of every recipe are calculated from assets/foods.json, never guessed, and the portions of the
ingredients marked with a role (protein / carb / fat) are scaled until each recipe lands on its share of the day.

usage: meals.py plan.json [--no-open] [--check]
  --check  only fit and print the numbers (no files), to review before building the book

plan.json:
{ "client": "Sarah M.",                       # reads <Coach Skills>/<client>/macros.json for the targets
  "targets": {"kcal": 2100, "protein": 180, "carbs": 210, "fat": 60},   # optional, overrides macros.json
  "slots": [ {"name": "Breakfast", "share": 0.3}, {"name": "Lunch", "share": 0.35}, {"name": "Dinner", "share": 0.35} ],
  "recipes": [
    { "slot": "Breakfast", "title": "Berry protein overnight oats", "photo": "overnight-oats", "time": "5 min",
      "level": "Simple", "times_per_week": 4,
      "ingredients": [ {"food": "rolled oats", "g": 60, "role": "carb"}, {"food": "greek yoghurt, 0% fat", "g": 200, "role": "protein"},
                       {"food": "eggs", "pieces": 2}, {"food": "almonds", "g": 15, "role": "fat"},
                       {"food": "cinnamon", "to_taste": true},
                       {"food": "protein granola", "g": 30, "per100": {"kcal": 420, "p": 25, "c": 50, "f": 12}, "aisle": "Pantry"} ],
      "steps": ["...", "...", "..."] } ] }
"""
import argparse, difflib, json, math, sys
from pathlib import Path
from common import ASSETS, load_profile, client_dir, fill, render, esc, handle_text, logo_html, open_folder

ap = argparse.ArgumentParser()
ap.add_argument("plan"); ap.add_argument("--no-open", action="store_true"); ap.add_argument("--check", action="store_true")
a = ap.parse_args()
plan = json.loads(Path(a.plan).read_text())
prof = load_profile()
FOODS = json.loads((ASSETS / "foods.json").read_text())
LOWER = {k.lower(): k for k in FOODS}
from common import HOME
PHOTO_FILES = {p.stem: p for p in (ASSETS / "food").glob("*.jpg") if p.stem != "cover"}
PHOTO_FILES.update({p.stem: p for p in (HOME / "Library" / "food").glob("*.*") if p.suffix.lower() in (".jpg", ".png")})   # the coach's own, made with food_photo.py
PHOTOS = sorted(PHOTO_FILES)

d = client_dir(plan["client"])
t = plan.get("targets")
if not t:
    mj = d / "macros.json"
    if not mj.exists():
        sys.exit("NO TARGETS: run /coach macros for this client first, or put \"targets\" in the plan.")
    m = json.loads(mj.read_text()); t = {"kcal": m["kcal"], "protein": m["protein"], "carbs": m["carbs"], "fat": m["fat"]}
T = (t["protein"], t["carbs"], t["fat"])
slots = plan.get("slots") or [{"name": "Breakfast", "share": 1 / 3}, {"name": "Lunch", "share": 1 / 3}, {"name": "Dinner", "share": 1 / 3}]
tot_share = sum(s["share"] for s in slots)
SHARE = {s["name"]: s["share"] / tot_share for s in slots}


def food(ing):
    """per-100 g values for one ingredient line, and the name it matched"""
    if ing.get("per100"):
        v = ing["per100"]; return {"kcal": v["kcal"], "p": v["p"], "c": v["c"], "f": v["f"], "aisle": ing.get("aisle", "Other")}, ing["food"]
    name = ing["food"].strip().lower()
    if ing.get("to_taste") and name not in LOWER:
        return {"kcal": 0, "p": 0, "c": 0, "f": 0, "aisle": ing.get("aisle", "Herbs & spices")}, ing["food"]
    if name in LOWER: return FOODS[LOWER[name]], LOWER[name]
    close = difflib.get_close_matches(name, list(LOWER), n=1, cutoff=0.72)
    if close: return FOODS[LOWER[close[0]]], LOWER[close[0]]
    sys.exit(f"UNKNOWN FOOD: \"{ing['food']}\". Use a name from assets/foods.json, or give it \"per100\" values (from the pack) and an \"aisle\".")


def grams(ing, f):
    if ing.get("to_taste"): return 0.0
    if "pieces" in ing: return ing["pieces"] * f.get("piece_g", 100)
    return float(ing.get("g", 0))


def macros_of(lines):
    p = c = fat = 0.0
    for ing, f, g in lines:
        p += f["p"] * g / 100; c += f["c"] * g / 100; fat += f["f"] * g / 100
    return p, c, fat


def solve(A, b):
    """small dense solve (Gaussian elimination with pivoting)"""
    n = len(b); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(M[r][i]))
        if abs(M[piv][i]) < 1e-9: return None
        M[i], M[piv] = M[piv], M[i]
        for r in range(n):
            if r != i:
                k = M[r][i] / M[i][i]; M[r] = [x - k * y for x, y in zip(M[r], M[i])]
    return [M[i][n] / M[i][i] for i in range(n)]


def fit(recipe):
    lines = []
    for ing in recipe["ingredients"]:
        f, matched = food(ing); ing["_matched"] = matched; lines.append([ing, f, grams(ing, f)])
    share = SHARE.get(recipe["slot"], 1 / len(slots))
    tgt = [x * share for x in T]
    W = [4, 4, 9]   # error measured in calories, so the recipe's energy lands too
    roles = [r for r in ("protein", "carb", "fat") if any(l[0].get("role") == r and l[2] > 0 for l in lines)]
    if roles:
        fixed = macros_of([l for l in lines if l[0].get("role") not in roles])
        G = [macros_of([l for l in lines if l[0].get("role") == r]) for r in roles]
        n = len(roles)
        A = [[sum(W[i] ** 2 * G[a_][i] * G[b_][i] for i in range(3)) for b_ in range(n)] for a_ in range(n)]
        b = [sum(W[i] ** 2 * G[a_][i] * (tgt[i] - fixed[i]) for i in range(3)) for a_ in range(n)]
        s = solve(A, b) or [1.0] * n
        s = [min(3.0, max(0.4, x)) for x in s]
        for l in lines:
            r = l[0].get("role")
            if r in roles:
                k = s[roles.index(r)]
                if "pieces" in l[0]:
                    l[0]["pieces"] = max(1, round(l[0]["pieces"] * k)); l[2] = grams(l[0], l[1])
                else:
                    g = l[2] * k; l[0]["g"] = max(5, round(g / 5) * 5); l[2] = l[0]["g"]
    p, c, fat = macros_of(lines)
    recipe["_lines"] = lines
    recipe["_m"] = {"kcal": round(p * 4 + c * 4 + fat * 9), "p": round(p), "c": round(c), "f": round(fat)}
    recipe["_t"] = {"kcal": round(tgt[0] * 4 + tgt[1] * 4 + tgt[2] * 9), "p": round(tgt[0]), "c": round(tgt[1]), "f": round(tgt[2])}
    return recipe


recipes = [fit(r) for r in plan["recipes"]]
report, worst = [], 0
for r in recipes:
    m, tg = r["_m"], r["_t"]
    off = max(abs(m["kcal"] - tg["kcal"]) / max(1, tg["kcal"]), abs(m["p"] - tg["p"]) / max(1, tg["p"]))
    worst = max(worst, off)
    report.append({"slot": r["slot"], "title": r["title"], "kcal": m["kcal"], "protein": m["p"], "carbs": m["c"], "fat": m["f"],
                   "target": tg, "off_pct": round(off * 100), "photo": r.get("photo"),
                   "matched": {i["food"]: i["_matched"] for i, _, _ in r["_lines"] if i["food"].lower() != i["_matched"].lower()},
                   "portions": {i["_matched"]: (f'{i["pieces"]} pcs' if "pieces" in i else ("to taste" if i.get("to_taste") else f'{i.get("g")} g')) for i, _, _ in r["_lines"]}})
for r in recipes:
    if r.get("photo") and r["photo"] not in PHOTOS:
        close = difflib.get_close_matches(r["photo"], PHOTOS, n=1, cutoff=0.5)
        r["photo"] = close[0] if close else None
if a.check:
    print(json.dumps({"targets": t, "recipes": report, "worst_off_pct": round(worst * 100), "photos_available": PHOTOS}, indent=1)); sys.exit()

# ------------------------------------------------------------------ the recipe book
def amount(ing):
    if ing.get("to_taste"): return "to taste"
    if "pieces" in ing:
        n = ing["pieces"]; return f"{n:g}"
    g = ing.get("g", 0)
    return f"{g / 1000:.1f} kg" if g >= 1000 else f"{g:g} g"


first = plan["client"].split()[0]
photo_uri = lambda name: (PHOTO_FILES.get(name) or ASSETS / "food" / f"{name}.jpg").as_uri()
pages = []
cover = f"""<section class="pg cover"><img class="ph" src="{photo_uri('cover')}"><div class="veil"></div>
<div class="brand frost">{logo_html(prof)}</div>
<div class="ctitle"><div class="eb acc">{esc(first)}'s recipe book</div><div class="big">{len(recipes)} meals built<br>for your macros.</div></div>
<div class="cstats frost"><div class="row4">""" + "".join(
    f'<div><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in
    [(f'{t["kcal"]:,}', "kcal a day"), (f'{t["protein"]}g', "protein"), (f'{t["carbs"]}g', "carbs"), (f'{t["fat"]}g', "fat")]) + f"""</div>
<div class="rule"></div><div class="foot"><span>{len(slots)} meals a day · pick one from each</span><b>{esc(handle_text(prof))}</b></div></div></section>"""
pages.append(cover)

# how to use it: the slots and their recipes, so any day the client builds lands on target
guide = '<section class="pg guide"><div class="eb acc">How to use this book</div><div class="gt">Pick one meal from each section.<br>Every day lands on your macros.</div>'
for s in slots:
    rs = [r for r in recipes if r["slot"] == s["name"]]
    if not rs: continue
    guide += f'<div class="gslot"><div class="eb">{esc(s["name"])}</div>'
    for r in rs:
        m = r["_m"]
        guide += f'<div class="grow"><span>{esc(r["title"])}</span><span class="gm"><b>{m["kcal"]}</b> kcal · {m["p"]}P · {m["c"]}C · {m["f"]}F</span></div>'
    guide += "</div>"
guide += f'<div class="gfoot">Daily target: <b>{t["kcal"]:,} kcal</b> · {t["protein"]}g protein · {t["carbs"]}g carbs · {t["fat"]}g fat</div></section>'
pages.append(guide)

for n, r in enumerate(recipes, 1):
    m = r["_m"]
    ings = [(i["_matched"] if not i.get("per100") else i["food"], amount(i)) for i, _, _ in r["_lines"]]
    small = " small" if len(ings) > 7 or len(r.get("steps", [])) > 4 else ""
    ph = f'<img class="ph rph" src="{photo_uri(r["photo"])}">' if r.get("photo") else '<div class="ph nophoto"></div>'
    tags = [r.get("time"), r.get("level", "Simple"), "1 serving"]
    pages.append(f"""<section class="pg">{ph}<div class="panel frost{small}">
<div class="sp"><span class="eb acc">{esc(r['slot'])} · Meal {n}</span><span class="eb">p. {n}</span></div>
<div class="rt">{esc(r['title'])}</div>
<div class="tags">{''.join(f'<span>{esc(x)}</span>' for x in tags if x)}</div>
<div class="nums">{''.join(f'<div class="{"dk" if i == 0 else ""}"><div class="v">{v}</div><div class="l">{l}</div></div>' for i, (v, l) in enumerate([(m['kcal'], 'kcal'), (f"{m['p']}g", 'protein'), (f"{m['c']}g", 'carbs'), (f"{m['f']}g", 'fat')]))}</div>
<div class="cols"><div class="ing"><div class="eb">Ingredients</div>{''.join(f'<div class="il"><span>{esc(x.capitalize())}</span><b>{esc(y)}</b></div>' for x, y in ings)}</div>
<div class="meth"><div class="eb">Method</div>{''.join(f'<div class="st"><span class="n">{i}</span><span>{esc(s)}</span></div>' for i, s in enumerate(r.get('steps', []), 1))}</div></div>
</div></section>""")

book = fill("recipe-book.html", {"pages": "".join(pages)})
base = d / f"{plan['client']} - Recipe Book"
made = render(book, out_pdf=str(base) + ".pdf")
# the cover and each recipe page as an image too (for DMs and stories)
pdir = d / "Recipe pages"; pdir.mkdir(exist_ok=True)
for i, pg in enumerate(pages):
    made += render(fill("recipe-book.html", {"pages": pg}), out_png=str(pdir / f"{i:02d}.png"), size=(900, 1200), scale=1.5)
    (pdir / f"{i:02d}.html").unlink(missing_ok=True)

# ------------------------------------------------------------------ the grocery list (one week)
week = {}
for s in slots:
    rs = [r for r in recipes if r["slot"] == s["name"]]
    if not rs: continue
    given = [r.get("times_per_week") for r in rs]
    default = math.ceil(7 / len(rs))
    for r in rs:
        k = r.get("times_per_week") or default
        for ing, f, g in r["_lines"]:
            name = ing["_matched"] if not ing.get("per100") else ing["food"]
            e = week.setdefault(name, {"g": 0.0, "pcs": 0, "aisle": f.get("aisle", "Other"), "taste": False, "piece": "pieces" in ing})
            if ing.get("to_taste"): e["taste"] = True
            elif "pieces" in ing: e["pcs"] += ing["pieces"] * k
            else: e["g"] += g * k
ORDER = ["Meat & fish", "Dairy & eggs", "Fridge", "Fruit & veg", "Frozen", "Bakery", "Pantry", "Herbs & spices", "Supplements", "Other"]
groups = {}
for name, e in week.items():
    if e["piece"]: q = f'{e["pcs"]:g}'
    elif e["g"] > 0: q = f'{e["g"] / 1000:.1f} kg' if e["g"] >= 1000 else f'{math.ceil(e["g"] / 10) * 10:g} g'
    else: q = "a little"
    groups.setdefault(e["aisle"], []).append((name, q))
gl = ""
for aisle in sorted(groups, key=lambda x: ORDER.index(x) if x in ORDER else 99):
    gl += f'<div class="aisle"><div class="eb acc">{esc(aisle)}</div>' + "".join(
        f'<div class="gi"><span class="box"></span><span class="nm">{esc(n.capitalize())}</span><b>{esc(q)}</b></div>' for n, q in sorted(groups[aisle])) + "</div>"
glist = fill("grocery-list.html", {"logo": logo_html(prof), "name": esc(plan["client"]), "items": gl, "handle": esc(handle_text(prof)),
                                    "business": esc(prof.get("business") or ""), "count": len(week)})
gbase = d / f"{plan['client']} - Grocery List"
made += render(glist, out_png=str(gbase) + ".png", out_pdf=str(gbase) + ".pdf", size=(794, 1123), scale=2)
(d / "meal-plan.json").write_text(json.dumps({**plan, "fitted": report}, indent=1, default=str))
print(json.dumps({"recipes": report, "worst_off_pct": round(worst * 100), "files": made, "folder": str(d)}, indent=1))
if not a.no_open: open_folder(d)
