"""/coach macros: a client's daily calories and macros, drawn as the dark macro card (PNG + PDF).

usage: macros.py --name "Sarah M." --sex female --age 29 --height 168 --weight 82 --goal fat-loss
                 [--goal-weight 75] [--training-days 4] [--job desk|feet|physical] [--meals 3]
                 [--diet balanced|high-protein|low-carb] [--kcal 2100] [--units metric|imperial] [--notes "..."]
Height: cm, or 5'11 / 71in. Weight: kg, or 180lb. With --units imperial plain numbers are inches and pounds.
Writes <Documents>/Coach Skills/<name>/macros.json, "<name> - Macros.png" and ".pdf"."""
import argparse, datetime, json, math, re, sys
from common import load_profile, client_dir, fill, render, esc, handle_text, logo_html, open_folder

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True); ap.add_argument("--sex", required=True, choices=["male", "female"])
ap.add_argument("--age", type=int, required=True); ap.add_argument("--height", required=True); ap.add_argument("--weight", required=True)
ap.add_argument("--goal", required=True, choices=["fat-loss", "lean-bulk", "maintain", "recomp"])
ap.add_argument("--goal-weight"); ap.add_argument("--training-days", type=int, default=3)
ap.add_argument("--job", default="desk", choices=["desk", "feet", "physical"]); ap.add_argument("--meals", type=int, default=3)
ap.add_argument("--diet", default="balanced", choices=["balanced", "high-protein", "low-carb"])
ap.add_argument("--kcal", type=int); ap.add_argument("--units", choices=["metric", "imperial"]); ap.add_argument("--notes", default="")
ap.add_argument("--no-open", action="store_true")
a = ap.parse_args()
prof = load_profile()
units = a.units or prof.get("units", "metric")


def to_cm(s):
    s = str(s).strip().lower().replace(" ", "")
    m = re.match(r"^(\d+)'(\d+(?:\.\d+)?)?(?:\"|in)?$", s)
    if m: return (int(m.group(1)) * 12 + float(m.group(2) or 0)) * 2.54
    if s.endswith("cm"): return float(s[:-2])
    if s.endswith("in"): return float(s[:-2]) * 2.54
    if s.endswith("m") and float(s[:-1]) < 3: return float(s[:-1]) * 100
    v = float(s)
    return v * 2.54 if units == "imperial" else v


def to_kg(s):
    s = str(s).strip().lower().replace(" ", "")
    if s.endswith(("lb", "lbs")): return float(s.rstrip("s")[:-2]) * 0.453592
    if s.endswith("kg"): return float(s[:-2])
    v = float(s)
    return v * 0.453592 if units == "imperial" else v


h, w = to_cm(a.height), to_kg(a.weight)
gw = to_kg(a.goal_weight) if a.goal_weight else None
if not (120 < h < 230 and 30 < w < 300):
    sys.exit(f"CHECK THE NUMBERS: height {h:.0f} cm, weight {w:.1f} kg don't look right.")

# energy: Mifflin-St Jeor, then the day's activity (job + training days), then the goal
bmr = 10 * w + 6.25 * h - 5 * a.age + (5 if a.sex == "male" else -161)
mult = {"desk": 1.2, "feet": 1.35, "physical": 1.5}[a.job] + 0.045 * max(0, min(7, a.training_days))
tdee = bmr * mult
adj = {"fat-loss": -0.20, "lean-bulk": 0.10, "maintain": 0.0, "recomp": -0.08}[a.goal]
kcal = a.kcal or tdee * (1 + adj)
if a.goal == "fat-loss": kcal = max(kcal, tdee - 1000, bmr * 1.0 if a.sex == "male" else bmr * 0.95)
kcal = int(round(kcal / 10) * 10)

# protein from body weight (goal weight when far heavier than it), fat as a share, carbs the rest
ref_w = gw if (gw and w - gw > 15) else w
ppk = {"fat-loss": 2.2, "lean-bulk": 2.0, "maintain": 1.8, "recomp": 2.2}[a.goal] + (0.2 if a.diet == "high-protein" else 0)
p = round(ref_w * ppk / 5) * 5
fat_share = {"balanced": 0.27, "high-protein": 0.25, "low-carb": 0.40}[a.diet]
f = max(round(kcal * fat_share / 9 / 5) * 5, round(0.6 * w / 5) * 5)
c = max(0, round((kcal - p * 4 - f * 9) / 4 / 5) * 5)
kcal_m = p * 4 + c * 4 + f * 9   # the card's calories are exactly the macros' sum
macros = [{"n": "Protein", "g": p, "kc": p * 4}, {"n": "Carbs", "g": c, "kc": c * 4}, {"n": "Fat", "g": f, "kc": f * 9}]
for m in macros: m["pct"] = round(100 * m["kc"] / kcal_m)

d = client_dir(a.name)
data = {"name": a.name, "date": datetime.date.today().isoformat(), "sex": a.sex, "age": a.age, "height_cm": round(h, 1), "weight_kg": round(w, 1),
        "goal": a.goal, "goal_weight_kg": round(gw, 1) if gw else None, "training_days": a.training_days, "job": a.job, "diet": a.diet,
        "meals": a.meals, "bmr": round(bmr), "tdee": round(tdee), "kcal": kcal_m, "protein": p, "carbs": c, "fat": f, "units": units}
(d / "macros.json").write_text(json.dumps(data, indent=2))

# ------------------------------------------------------------------ the card
def wt(kg): return (f"{kg / 0.453592:.0f}", "lb") if units == "imperial" else (f"{kg:.0f}" if kg >= 100 else f"{kg:.1f}".rstrip("0").rstrip("."), "kg")
RING = [("#1FBF4F", "#A6FF4D"), ("#0A6CFF", "#5EE7FF"), ("#FF7A00", "#FFD60A")]
size, sw, gap = 280, 26, 4
rings = ""
for i, (ca, cb) in enumerate(RING):
    r = size / 2 - sw / 2 - i * (sw + gap); C = 2 * math.pi * r
    L = C   # full rings, as on the approved card: each macro is a target to close
    arc = f'<circle cx="{size/2}" cy="{size/2}" r="{r:.2f}" fill="none" stroke="url(#rg{i})" stroke-width="{sw}" stroke-linecap="round" stroke-dasharray="{L:.1f} {C:.1f}" transform="rotate(-90 {size/2} {size/2})"'
    rings += (f'<circle cx="{size/2}" cy="{size/2}" r="{r:.2f}" fill="none" stroke="{ca}" stroke-opacity="0.18" stroke-width="{sw}"/>'
              f'{arc} filter="url(#rglow)" opacity="0.55"/>{arc}/>')
defs = "".join(f'<linearGradient id="rg{i}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{ca}"/><stop offset="1" stop-color="{cb}"/></linearGradient>' for i, (ca, cb) in enumerate(RING))
rows = "".join(f'<div class="mrow"><div><div class="lab" style="color:{RING[i][1]};font-size:12px">{m["n"]}</div>'
               f'<div class="mg">{m["g"]}<span>g</span></div></div><div class="mside">{m["kc"]} kcal<br>{m["pct"]}% of total</div></div>' for i, m in enumerate(macros))
nw, nu = wt(w)
tiles = [("Daily calories", f"{kcal_m:,}", "kcal", "")]
tiles.append(("Current weight", nw, nu, ""))
if gw:
    gv, gu = wt(gw); diff = abs(w - gw); dv, du = wt(diff)
    tiles.append(("Goal weight", gv, gu, f"{dv} {du} to {'lose' if gw < w else 'gain'}" if diff >= 0.5 else "hold"))
else:
    tiles.append(("Goal", {"fat-loss": "Lose", "lean-bulk": "Build", "maintain": "Hold", "recomp": "Recomp"}[a.goal], "", ""))
tiles_html = "".join(f'<div class="glass tile"><div class="trow"><span class="lab">{l}</span>{f"<span class=tag>{esc(t)}</span>" if t else ""}</div>'
                     f'<div class="tv"><span>{v}</span><small>{u}</small></div></div>' for l, v, u, t in tiles)
per = [("Calories", kcal_m / a.meals, "kcal", "#F5F5F7")] + [(m["n"], m["g"] / a.meals, "g", RING[i][1]) for i, m in enumerate(macros)]
per_html = "".join(f'<div class="pm"><span class="bar" style="background:{col};box-shadow:0 0 10px {col}"></span><span class="lab">{l}</span>'
                   f'<span class="pv">{v:,.0f}<small>{u}</small></span></div>' for l, v, u, col in per)
goal_word = {"fat-loss": "Fat loss", "lean-bulk": "Lean bulk", "maintain": "Maintenance", "recomp": "Recomposition"}[a.goal]
notes = esc(a.notes) if a.notes else ""
html = fill("macro-card.html", {
    "logo": logo_html(prof, dark=True), "name": esc(a.name), "date": datetime.date.today().strftime("%-d %b %Y") if sys.platform != "win32" else datetime.date.today().strftime("%d %b %Y"),
    "phase": goal_word, "defs": defs, "rings": rings, "kcal": f"{kcal_m:,}", "rows": rows, "tiles": tiles_html, "meals": a.meals, "per": per_html,
    "notes": notes, "business": esc(prof.get("business") or ""), "handle": esc(handle_text(prof)), "handle_vis": "" if handle_text(prof) else "display:none",
})
base = d / f"{a.name} - Macros"
made = render(html, out_png=str(base) + ".png", out_pdf=str(base) + ".pdf", size=(794, 1123), scale=2)
print(json.dumps({"kcal": kcal_m, "protein": p, "carbs": c, "fat": f, "tdee": round(tdee), "files": made, "folder": str(d)}, indent=2))
if not a.no_open: open_folder(d)
