"""/coach anatomy: a flat drawn body with the muscles an exercise works glowing. The best view is picked from the muscles
(front, back, or side for arm and shoulder work); the coach can override it.

usage: anatomy.py --exercise "Shoulder press" [--primary front-delts,side-delts --secondary triceps] [--body male|female]
                  [--view auto|front|back|side|both] [--colour "#E5484D"] [--client "Name"] [--no-open]
Without --primary, the exercise is looked up in assets/exercises.json.
Writes "<exercise> - anatomy.png" (a 4:5 post with the names) and "<exercise> - body.png" (the body alone, transparent, for edits)."""
import argparse, difflib, json, sys
from common import ASSETS, HOME, client_dir, fill, render, esc, open_folder

MUSCLES = {   # id: (name, views it can be drawn in)
    "chest": ("Chest", ["front"]), "front-delts": ("Front delts", ["side", "front"]), "side-delts": ("Side delts", ["side", "front", "back"]),
    "rear-delts": ("Rear delts", ["side", "back"]), "biceps": ("Biceps", ["side", "front"]), "triceps": ("Triceps", ["side", "back"]),
    "forearms": ("Forearms", ["side", "front", "back"]), "abs": ("Abs", ["front"]), "obliques": ("Obliques", ["front"]),
    "quads": ("Quads", ["front"]), "adductors": ("Adductors", ["front"]), "traps": ("Traps", ["back", "front"]), "lats": ("Lats", ["back"]),
    "lower-back": ("Lower back", ["back"]), "glutes": ("Glutes", ["back"]), "hamstrings": ("Hamstrings", ["back"]), "calves": ("Calves", ["back"]),
}
ARM = {"front-delts", "side-delts", "rear-delts", "biceps", "triceps", "forearms"}

ap = argparse.ArgumentParser()
ap.add_argument("--exercise", required=True); ap.add_argument("--primary", default=""); ap.add_argument("--secondary", default="")
ap.add_argument("--body", default="male", choices=["male", "female"]); ap.add_argument("--view", default="auto", choices=["auto", "front", "back", "side", "both"])
ap.add_argument("--colour", default="#E5484D"); ap.add_argument("--client", default=""); ap.add_argument("--no-open", action="store_true")
a = ap.parse_args()


def ids(s):
    out = []
    for x in [t.strip().lower().replace(" ", "-") for t in s.split(",") if t.strip()]:
        x = {"shoulders": "side-delts", "delts": "side-delts", "back": "lats", "legs": "quads", "core": "abs", "pecs": "chest", "bum": "glutes",
             "lower-traps": "traps", "upper-back": "traps", "rhomboids": "traps", "hip-flexors": "quads", "calf": "calves"}.get(x, x)
        if x not in MUSCLES:
            m = difflib.get_close_matches(x, list(MUSCLES), n=1, cutoff=0.6)
            if not m: sys.exit(f"UNKNOWN MUSCLE: {x}. Use: {', '.join(MUSCLES)}")
            x = m[0]
        if x not in out: out.append(x)
    return out


prim, sec = ids(a.primary), ids(a.secondary)
if not prim:
    ex = json.loads((ASSETS / "exercises.json").read_text())
    key = a.exercise.strip().lower()
    hit = key if key in ex else (difflib.get_close_matches(key, list(ex), n=1, cutoff=0.7) or [None])[0]
    if not hit:
        sys.exit(f"NOT IN THE LIST: \"{a.exercise}\". Pass --primary (and --secondary) yourself. Muscles: {', '.join(MUSCLES)}")
    prim, sec = ex[hit]["primary"], ex[hit].get("secondary", [])
sec = [m for m in sec if m not in prim]

# the view: arm and shoulder work reads best from the side; otherwise the side of the body holding most of the primary work
view = a.view
if view == "auto":
    if set(prim) <= ARM:
        view = "side"
    else:
        score = {v: sum(2 for m in prim if v in MUSCLES[m][1]) + sum(1 for m in sec if v in MUSCLES[m][1]) for v in ("front", "back")}
        fr = all("front" in MUSCLES[m][1] for m in prim); bk = all("back" in MUSCLES[m][1] for m in prim)
        view = "front" if fr and not bk else "back" if bk and not fr else ("both" if abs(score["front"] - score["back"]) <= 1 else max(score, key=score.get))
views = ["front", "back"] if view == "both" else [view]


def figure(v, h):
    lines = (ASSETS / "body" / f"{a.body}_{v}.png").as_uri()
    layers = ""
    for m, op in [(m, 0.45) for m in sec] + [(m, 1.0) for m in prim]:
        mk = ASSETS / "body" / "masks" / f"{a.body}_{v}_{m}.png"
        if not mk.exists(): continue
        u = mk.as_uri()
        layers += (f'<div class="glow" style="--m:url(\'{u}\');opacity:{0.9 * op}"></div>'
                   f'<div class="fill" style="--m:url(\'{u}\');opacity:{0.82 * op}"></div>')
    return f'<div class="fig" style="height:{h}px">{layers}<img class="lines" src="{lines}"></div>'


name = lambda ms: ", ".join(MUSCLES[m][0] for m in ms)
out_dir = client_dir(a.client) if a.client else (HOME / "Anatomy")
out_dir.mkdir(parents=True, exist_ok=True)
safe = "".join(ch for ch in a.exercise if ch.isalnum() or ch in " -").strip() or "Exercise"
h = 980 if len(views) == 1 else 900
post = fill("anatomy.html", {"colour": a.colour, "figs": "".join(figure(v, h) for v in views), "exercise": esc(a.exercise),
                             "primary": esc(name(prim)), "secondary": esc(name(sec)) if sec else "", "sec_vis": "" if sec else "display:none",
                             "bg": "#0A0B0D", "label_vis": ""})
png = out_dir / f"{safe} - anatomy.png"
render(post, out_png=str(png), size=(1080, 1350), scale=1)
body = fill("anatomy.html", {"colour": a.colour, "figs": "".join(figure(v, 1250) for v in views), "exercise": "", "primary": "", "secondary": "",
                             "sec_vis": "display:none", "bg": "transparent", "label_vis": "display:none"})
bpng = out_dir / f"{safe} - body.png"
import subprocess  # the transparent copy: same page, no background
from common import find_browser
import tempfile, shutil
src = bpng.with_suffix(".html"); src.write_text(body)
prof = tempfile.mkdtemp()
subprocess.run([find_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files", f"--user-data-dir={prof}",
                "--default-background-color=00000000", "--window-size=1080,1350", f"--screenshot={bpng}", src.as_uri()], capture_output=True, timeout=120)
shutil.rmtree(prof, ignore_errors=True)
for f in (png.with_suffix(".html"), src): f.unlink(missing_ok=True)
missing = [f"{v}:{m}" for v in views for m in prim + sec if not (ASSETS / "body" / "masks" / f"{a.body}_{v}_{m}.png").exists()]
print(json.dumps({"view": view, "primary": prim, "secondary": sec, "not_visible_in_this_view": missing,
                  "post": str(png), "body": str(bpng), "folder": str(out_dir)}, indent=1))
if not a.no_open: open_folder(out_dir)
