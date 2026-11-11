"""Adds a muscle the pack doesn't have yet (or redoes one), on one body and one view, with the coach's Gemini.
Gemini gets OUR drawing (assets/body/<body>_<view>_source.jpg) and is asked to fill only that muscle in magenta; this tool keeps only
the magenta area as a mask, checks Gemini didn't move the drawing, and saves it to the coach's library. The design never changes:
the lines, glow and tag always come from the template.

usage: new_muscle.py --body male|female --view front|back|side --muscle rhomboids --name "Rhomboids" --heading "Upper back"
                     --describe "the rhomboids, between the shoulder blades on both sides" [--upper yes|no]
Prints ADDED (with the alignment score) or a plain reason."""
import _env; _env.need("PIL", "numpy")
import argparse, io, json, sys
import numpy as np
from PIL import Image, ImageFilter
from common import ASSETS, HOME
from gemini import image

ap = argparse.ArgumentParser()
ap.add_argument("--body", required=True, choices=["male", "female"]); ap.add_argument("--view", required=True, choices=["front", "back", "side"])
ap.add_argument("--muscle", required=True); ap.add_argument("--name", required=True); ap.add_argument("--heading", required=True)
ap.add_argument("--describe", required=True); ap.add_argument("--upper", default="yes", choices=["yes", "no"])
a = ap.parse_args()
mid = a.muscle.strip().lower().replace(" ", "-")
LIB = HOME / "Library"; (LIB / "masks").mkdir(parents=True, exist_ok=True)
src = ASSETS / "body" / f"{a.body}_{a.view}_source.jpg"
W, H = 768, 1376
side = " on the near (visible) side" if a.view == "side" else ""
prompt = (f"Edit this exact image. Fill ONLY {a.describe}{side} with solid flat pure magenta colour #FF00FF, filling inside their outlines completely.\n"
          "Keep every single line, the whole figure, its position, size, pose and the white background exactly unchanged, pixel for pixel. "
          "Do not move, redraw or recolour anything else. No other colour anywhere.")

base = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)


def lines_of(rgb):
    mag = (rgb[..., 0] > 170) & (rgb[..., 2] > 170) & (rgb[..., 1] < 120)
    return (rgb.mean(2) < 150) & ~mag


L0 = Image.fromarray((lines_of(base) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
L0 = np.asarray(L0) > 0
best = None
for attempt in range(3):
    try:
        raw = image(prompt, [src], aspect="9:16", size="2K")
    except RuntimeError as e:
        sys.exit(str(e))
    e = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB").resize((base.shape[1], base.shape[0]))).astype(np.float32)
    L1 = lines_of(e)
    aligned = float((L1 & L0).sum() / max(1, L1.sum()))
    r, g, b = e[..., 0], e[..., 1], e[..., 2]
    mag = (r > 150) & (b > 150) & (g < 140) & (r - g > 60) & (b - g > 60)
    m = Image.fromarray((mag * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))   # close the fibre lines
    area = float((np.asarray(m) > 0).mean())
    if best is None or aligned > best[0]: best = (aligned, area, m)
    if aligned >= 0.97 and area > 0.0005: break
aligned, area, m = best
if area <= 0.0005:
    sys.exit("NOT ADDED: Gemini didn't mark anything. Describe the muscle more plainly (where it is on the body) and try again.")
if aligned < 0.93:
    sys.exit(f"NOT ADDED: Gemini moved the drawing (alignment {aligned:.2f}). Try again; if it keeps failing, use a neighbouring muscle.")
mk = np.asarray(m.resize((W, H), Image.BOX).filter(ImageFilter.GaussianBlur(0.8)))
out = np.zeros((H, W, 4), np.uint8); out[..., :3] = 255; out[..., 3] = mk
dst = LIB / "masks" / f"{a.body}_{a.view}_{mid}.png"
Image.fromarray(out).save(dst, optimize=True)
reg_p = LIB / "muscles.json"
reg = json.loads(reg_p.read_text()) if reg_p.exists() else {}
e = reg.setdefault(mid, {"heading": a.heading, "name": a.name, "views": [], "upper": a.upper == "yes"})
if a.view not in e["views"]: e["views"].append(a.view)
reg_p.write_text(json.dumps(reg, indent=1))
print(json.dumps({"added": mid, "body": a.body, "view": a.view, "alignment": round(aligned, 3), "area_pct": round(area * 100, 2), "file": str(dst)}))
