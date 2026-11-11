"""/coach anatomy: the locked anatomy design. A drawn muscle-atlas body (line art only, no shading) on a TRANSPARENT background, so
it overlays the coach's own video; only the worked muscles are filled, with a soft glow; the muscle tag sits top right.

usage: anatomy.py --exercise "Shoulder press" [--primary front-delts,side-delts --secondary triceps] [--body male|female]
                  [--view auto|front|back|side] [--colour red|orange|yellow|green|teal|blue|purple|pink] [--outline white|black]
                  [--client "Name"] [--no-open]
Without --primary the exercise is looked up in assets/exercises.json.
Writes "<exercise> - anatomy.png" (transparent, 1080 x 1350, to lay over a video) and "<exercise> - preview.png" (the same on a
background, to look at)."""
import argparse, difflib, json, shutil, subprocess, sys, tempfile
from common import ASSETS, HOME, client_dir, fill, esc, open_folder, find_browser, font_css

# id: (tag heading, anatomical name, views it can be drawn in, upper body?)
MUSCLES = {
    "chest": ("Chest", "Pectoralis major", ["front"], True),
    "front-delts": ("Shoulders", "Anterior deltoid", ["side", "front"], True),
    "side-delts": ("Shoulders", "Lateral deltoid", ["side", "front", "back"], True),
    "rear-delts": ("Shoulders", "Posterior deltoid", ["side", "back"], True),
    "biceps": ("Arms", "Biceps brachii", ["side", "front"], True),
    "triceps": ("Arms", "Triceps brachii", ["side", "back"], True),
    "forearms": ("Forearms", "Forearm flexors and extensors", ["side", "front", "back"], True),
    "abs": ("Core", "Rectus abdominis", ["front"], True),
    "obliques": ("Core", "Obliques", ["front"], True),
    "traps": ("Upper back", "Trapezius", ["back", "front"], True),
    "lats": ("Back", "Latissimus dorsi", ["back"], True),
    "lower-back": ("Lower back", "Erector spinae", ["back"], True),
    "glutes": ("Glutes", "Gluteus maximus and medius", ["back"], False),
    "quads": ("Legs", "Quadriceps", ["front"], False),
    "adductors": ("Legs", "Adductors", ["front"], False),
    "hamstrings": ("Legs", "Hamstrings", ["back"], False),
    "calves": ("Legs", "Gastrocnemius and soleus", ["back"], False),
}
# muscles the coach added with new_muscle.py (their library survives updates)
LIBM = HOME / "Library" / "masks"
_reg = HOME / "Library" / "muscles.json"
if _reg.exists():
    for k, v in json.loads(_reg.read_text()).items():
        MUSCLES[k] = (v["heading"], v["name"], v["views"], v.get("upper", True))
ARM = {"front-delts", "side-delts", "rear-delts", "biceps", "triceps", "forearms"}
# the stock glow colours: muted highlight pairs (deep, light), like an anatomy atlas. Red is the default and the recommended one.
COLOURS = {"red": ("#D7372A", "#FF7B5E"), "orange": ("#E2602A", "#FFA766"), "yellow": ("#D9A21C", "#FFDC6E"),
           "green": ("#2E9E58", "#86E39A"), "teal": ("#14988F", "#6BE0D3"), "blue": ("#2F69DB", "#82B3FF"),
           "purple": ("#7650D6", "#BCA2FF"), "pink": ("#D53F7C", "#FF95BE")}

ap = argparse.ArgumentParser()
ap.add_argument("--exercise", required=True); ap.add_argument("--primary", default=""); ap.add_argument("--secondary", default="")
ap.add_argument("--body", default="male", choices=["male", "female"]); ap.add_argument("--view", default="auto", choices=["auto", "front", "back", "side"])
ap.add_argument("--colour", default="red", choices=list(COLOURS)); ap.add_argument("--outline", default="white", choices=["white", "black"])
ap.add_argument("--client", default=""); ap.add_argument("--no-open", action="store_true")
a = ap.parse_args()


def ids(s):
    out = []
    for x in [t.strip().lower().replace(" ", "-") for t in s.split(",") if t.strip()]:
        if x in MUSCLES: out.append(x) if x not in out else None; continue
        x = {"shoulders": "side-delts", "delts": "side-delts", "back": "lats", "core": "abs", "pecs": "chest", "bum": "glutes",
             "upper-back": "traps", "rhomboids": "traps", "calf": "calves", "lower-traps": "traps"}.get(x, x)
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

# the view: arm and shoulder work from the side; otherwise where most of the primary work is
view = a.view
if view == "auto":
    if set(prim) <= ARM:
        view = "side"
    else:
        sc = {v: sum(2 for m in prim if v in MUSCLES[m][2]) + sum(1 for m in sec if v in MUSCLES[m][2]) for v in ("front", "back")}
        view = max(sc, key=sc.get)
# the framing: head to hips for upper-body work, the whole body when legs or glutes are involved. The head is always in.
upper = all(MUSCLES[m][3] for m in prim + sec)
base, light = COLOURS[a.colour]
B = ASSETS / "body"
lines = B / (f"{a.body}_{view}.png" if a.outline == "white" else f"{a.body}_{view}_black.png")
if not lines.exists(): lines = B / f"{a.body}_{view}.png"

layers, missing, hidden = "", [], []
for m, op in [(m, 0.5) for m in sec] + [(m, 1.0) for m in prim]:
    if view not in MUSCLES[m][2]:
        hidden.append(m); continue
    mk = B / "masks" / f"{a.body}_{view}_{m}.png"
    if not mk.exists(): mk = LIBM / f"{a.body}_{view}_{m}.png"
    if not mk.exists():
        missing.append(m); continue
    u = mk.as_uri()
    layers += (f'<div class="glow" style="--m:url(\'{u}\');opacity:{0.75 * op}"></div>'
               f'<div class="fill" style="--m:url(\'{u}\');opacity:{op}"></div>')

shown = [m for m in prim if m not in missing and m not in hidden] or prim
heads = []
for m in shown:
    if MUSCLES[m][0] not in heads: heads.append(MUSCLES[m][0])
names = [MUSCLES[m][1] for m in shown]
if len({MUSCLES[m][0] for m in shown}) == 1 and MUSCLES[shown[0]][0] == "Shoulders" and len(shown) > 1:
    names = ["Deltoids (" + ", ".join(MUSCLES[m][1].split()[0].lower() for m in shown) + ")"]
also = [MUSCLES[m][1] for m in sec if m not in missing and m not in hidden]

FIG_H = 2420 if upper else 1300          # upper: the figure is drawn big and the frame stops at the hips
vals = {"base": base, "light": light, "layers": layers, "lines": lines.as_uri(), "fig_h": FIG_H, "fig_w": round(FIG_H * 1536 / 2752),
        "fig_top": 40 if upper else 30, "heading": esc(" + ".join(heads).upper()), "names": "<br>".join(esc(n) for n in names),
        "also": esc("Also: " + ", ".join(also)) if also else "", "also_vis": "" if also else "display:none",
        "ink": "#121417" if a.outline == "black" else "#FFFFFF", "fonts": font_css()}

out_dir = client_dir(a.client) if a.client else (HOME / "Anatomy")
out_dir.mkdir(parents=True, exist_ok=True)
safe = "".join(ch for ch in a.exercise if ch.isalnum() or ch in " -").strip() or "Exercise"
br = find_browser()
if not br: sys.exit("NO BROWSER: install Google Chrome (free), then run this again.")
made = []
for kind, bg in [("anatomy", "transparent"), ("preview", "#0B0C0E" if a.outline == "white" else "#EEF0F2")]:
    html = fill("anatomy.html", {**vals, "bg": bg})
    src = out_dir / f".{safe}-{kind}.html"; src.write_text(html)
    png = out_dir / f"{safe} - {kind}.png"
    prof = tempfile.mkdtemp()
    subprocess.run([br, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files", f"--user-data-dir={prof}",
                    "--default-background-color=00000000", "--window-size=1080,1350", "--virtual-time-budget=3000", f"--screenshot={png}", src.as_uri()],
                   capture_output=True, timeout=120)
    shutil.rmtree(prof, ignore_errors=True); src.unlink(missing_ok=True)
    if png.exists(): made.append(str(png))
print(json.dumps({"view": view, "frame": "head to hips" if upper else "full body", "primary": prim, "secondary": sec,
                  "not_visible_from_this_side": hidden, "missing_in_this_view": missing, "fix_missing": "run new_muscle.py for each missing one, then run this again" if missing else "", "files": made, "folder": str(out_dir)}, indent=1))
if not a.no_open: open_folder(out_dir)
