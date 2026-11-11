"""The coach's own details, asked once and reused on every card, book and list.
usage: profile.py show
       profile.py fonts                     (the stock fonts and accent colours to offer)
       profile.py set [--business "Name"] [--handle yourhandle] [--logo /path/logo.png] [--units metric|imperial]
                      [--accent green|#16A34A] [--font "Playfair Display"] [--font-file /path/font.ttf --font-kind serif|sans]"""
import argparse, json, shutil
from pathlib import Path
from common import load_profile, save_profile, HOME, FONTS, ACCENTS, accent_hex

ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=["show", "set", "fonts"])
ap.add_argument("--business"); ap.add_argument("--handle"); ap.add_argument("--logo"); ap.add_argument("--units", choices=["metric", "imperial"])
ap.add_argument("--accent"); ap.add_argument("--font"); ap.add_argument("--font-file"); ap.add_argument("--font-kind", choices=["serif", "sans"])
a = ap.parse_args()
p = load_profile()
if a.cmd == "fonts":
    print(json.dumps({"sans": [k for k, v in FONTS.items() if v[2] == "sans"], "serif": [k for k, v in FONTS.items() if v[2] == "serif"],
                      "accents": ACCENTS}, indent=1)); raise SystemExit
if a.cmd == "set":
    if a.accent is not None:
        h = accent_hex(a.accent)
        if not h: raise SystemExit(f"ACCENT: use a colour name ({', '.join(ACCENTS)}) or a hex code like #16A34A")
        p["accent"] = h
    if a.font is not None:
        m = {k.lower(): k for k in FONTS}.get(a.font.strip().lower())
        if not m: raise SystemExit(f"FONT: pick one of {', '.join(FONTS)}, or pass --font-file")
        p["font"], p["font_file"] = m, ""
    if a.font_file:
        src = Path(a.font_file).expanduser()
        if not src.exists(): raise SystemExit(f"NO FILE: {src}")
        HOME.mkdir(parents=True, exist_ok=True)
        dst = HOME / ("brand-font" + src.suffix.lower()); shutil.copyfile(src, dst)
        p["font_file"], p["font_kind"] = str(dst), a.font_kind or "sans"
    if a.business is not None: p["business"] = a.business.strip()
    if a.handle is not None: p["handle"] = a.handle.strip().lstrip("@")
    if a.units: p["units"] = a.units
    if a.logo is not None:
        if a.logo and Path(a.logo).exists():
            HOME.mkdir(parents=True, exist_ok=True)
            dst = HOME / ("logo" + Path(a.logo).suffix.lower())
            shutil.copyfile(a.logo, dst)
            p["logo"] = str(dst)
        else:
            p["logo"] = ""
    save_profile(p)
print(json.dumps({**p, "set_up": bool(p.get("business")) and bool(p.get("accent"))}, indent=2))
