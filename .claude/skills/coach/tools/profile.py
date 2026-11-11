"""The coach's own details, asked once and reused on every card, book and list.
usage: profile.py show
       profile.py set [--business "Name"] [--handle yourhandle] [--logo /path/logo.png] [--units metric|imperial]"""
import argparse, json, shutil
from pathlib import Path
from common import load_profile, save_profile, HOME

ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=["show", "set"])
ap.add_argument("--business"); ap.add_argument("--handle"); ap.add_argument("--logo"); ap.add_argument("--units", choices=["metric", "imperial"])
a = ap.parse_args()
p = load_profile()
if a.cmd == "set":
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
print(json.dumps({**p, "set_up": bool(p.get("business"))}, indent=2))
