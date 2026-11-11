"""Makes sure Pillow and numpy are available, installing them once into a private folder inside the skill (no admin rights),
then re-runs the calling script with that Python. Import this first: `import _env; _env.need("PIL", "numpy")`."""
import os, platform, subprocess, sys, venv
from pathlib import Path

PKG = {"PIL": "pillow", "numpy": "numpy"}


def need(*mods):
    try:
        for m in mods: __import__(m)
        return
    except ImportError:
        pass
    vdir = Path(__file__).resolve().parent.parent / ".venv"
    py = vdir / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")
    if Path(sys.executable).resolve() == py.resolve():
        sys.exit("SETUP FAILED: couldn't load " + ", ".join(mods))
    if not py.exists():
        print("FIRST RUN: setting up the image tools in the skill folder (about a minute)...", flush=True)
        venv.create(vdir, with_pip=True)
    chk = subprocess.run([str(py), "-c", "; ".join(f"import {m}" for m in mods)], capture_output=True)
    if chk.returncode != 0:
        subprocess.run([str(py), "-m", "pip", "install", "-q"] + [PKG.get(m, m) for m in mods], check=True)
    os.execv(str(py), [str(py)] + sys.argv) if platform.system() != "Windows" else sys.exit(subprocess.call([str(py)] + sys.argv))
