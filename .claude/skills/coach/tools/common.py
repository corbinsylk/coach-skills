"""Shared helpers for the /coach tools: the coach's profile, the output folder, and HTML -> PNG / PDF through the
browser already on the computer (Chrome, Edge, Brave or Chromium). Standard library only."""
import json, os, re, shutil, subprocess, sys, tempfile, platform, venv
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent          # .../skills/coach
ASSETS = SKILL / "assets"
TEMPLATES = SKILL / "templates"
HOME = Path.home() / "Documents" / "Coach Skills"       # every result lands here, one folder per client
PROFILE = HOME / "profile.json"


def load_profile():
    if PROFILE.exists():
        return json.loads(PROFILE.read_text())
    return {"business": "", "handle": "", "logo": "", "units": "metric"}


def save_profile(p):
    HOME.mkdir(parents=True, exist_ok=True)
    PROFILE.write_text(json.dumps(p, indent=2))


def slug(s):
    s = re.sub(r"[^\w\s-]", "", s or "").strip()
    return re.sub(r"\s+", " ", s) or "Client"


def client_dir(name):
    d = HOME / slug(name)
    d.mkdir(parents=True, exist_ok=True)
    return d


def find_browser():
    env = os.environ.get("COACH_BROWSER")
    if env and Path(env).exists():
        return env
    sysname = platform.system()
    cands = []
    if sysname == "Darwin":
        for app in ["Google Chrome", "Microsoft Edge", "Brave Browser", "Chromium", "Google Chrome Canary"]:
            cands.append(f"/Applications/{app}.app/Contents/MacOS/{app}")
            cands.append(str(Path.home() / f"Applications/{app}.app/Contents/MacOS/{app}"))
    elif sysname == "Windows":
        for base in [os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""), os.environ.get("LOCALAPPDATA", "")]:
            if not base:
                continue
            cands += [base + r"\Google\Chrome\Application\chrome.exe", base + r"\Microsoft\Edge\Application\msedge.exe",
                      base + r"\BraveSoftware\Brave-Browser\Application\brave.exe"]
    for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "brave-browser", "chrome", "msedge"]:
        p = shutil.which(name)
        if p:
            cands.append(p)
    for c in cands:
        if c and Path(c).exists():
            return c
    return None


# the coach's brand: one accent colour, one heading font (stock list or their own file), their logo. Layouts never change.
FONTS = {   # name: (file, css weight range, kind)
    "Plus Jakarta Sans": ("PlusJakartaSans.ttf", "200 800", "sans"), "Inter": ("Inter.ttf", "100 900", "sans"),
    "Montserrat": ("Montserrat.ttf", "100 900", "sans"), "DM Sans": ("DMSans.ttf", "100 1000", "sans"),
    "Poppins": ("Poppins-Bold.ttf", "700 800", "sans"),
    "Playfair Display": ("PlayfairDisplay.ttf", "400 900", "serif"), "Fraunces": ("Fraunces.ttf", "100 900", "serif"),
    "Lora": ("Lora.ttf", "400 700", "serif"), "DM Serif Display": ("DMSerifDisplay.ttf", "400 900", "serif"),
}
ACCENTS = {"green": "#16A34A", "lime": "#84CC16", "teal": "#0D9488", "blue": "#2563EB", "purple": "#7C3AED", "pink": "#DB2777",
           "red": "#DC2626", "orange": "#EA580C", "gold": "#CA8A04", "black": "#121417"}


def accent_hex(v):
    v = (v or "").strip().lower()
    if v in ACCENTS: return ACCENTS[v]
    if re.fullmatch(r"#?[0-9a-f]{6}", v): return "#" + v.lstrip("#").upper()
    return None


def brand_css(p, default_font="Plus Jakarta Sans", default_accent="#16A34A"):
    """CSS variables --accent and --head (the heading font) for the templates."""
    acc = accent_hex(p.get("accent")) or default_accent
    ff = p.get("font_file") or ""
    if ff and Path(ff).exists():
        fmt = {".otf": "opentype", ".woff2": "woff2", ".woff": "woff"}.get(Path(ff).suffix.lower(), "truetype")
        face = f"@font-face{{font-family:'BrandHead';src:url('{Path(ff).resolve().as_uri()}') format('{fmt}');font-weight:100 900;}}"
        kind = p.get("font_kind", "sans")
    else:
        name = p.get("font") if p.get("font") in FONTS else default_font
        file, wr, kind = FONTS[name]
        face = f"@font-face{{font-family:'BrandHead';src:url('{(ASSETS / 'fonts' / file).as_uri()}') format('truetype');font-weight:{wr};}}"
    # serif headings are set a touch less heavy and less tight than the sans ones
    hw, ls = ("700", "-0.02em") if kind == "serif" else ("800", "-0.04em")
    return face + f":root{{--accent:{acc};--head:'BrandHead','Jakarta',sans-serif;--head-w:{hw};--head-ls:{ls};}}"


def font_css():
    """The two fonts ship in assets/fonts (SIL Open Font Licence)."""
    f = (ASSETS / "fonts").as_uri()
    return (f"@font-face{{font-family:'Jakarta';src:url('{f}/PlusJakartaSans.ttf') format('truetype');font-weight:200 800;}}"
            f"@font-face{{font-family:'Inter';src:url('{f}/Inter.ttf') format('truetype');font-weight:100 900;}}")


def fill(template, values):
    """{{key}} placeholders in a template file."""
    html = (TEMPLATES / template).read_text()
    dfont = "Inter" if template == "macro-card.html" else "Plus Jakarta Sans"   # each locked design keeps its own type unless the coach picks one
    values = {"fonts": font_css() + brand_css(load_profile(), default_font=dfont), "assets": ASSETS.as_uri(), **values}
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(values.get(m.group(1), "")), html)


def render(html, out_png=None, out_pdf=None, size=(1080, 1350), scale=2):
    """Writes the HTML next to the outputs and has the browser draw it. Returns the files made."""
    br = find_browser()
    if not br:
        sys.exit("NO BROWSER: install Google Chrome (free), then run this again.")
    target = Path(out_png or out_pdf)
    src = target.with_suffix(".html")
    src.write_text(html)
    made = []
    prof = tempfile.mkdtemp(prefix="coach-chrome-")
    base = [br, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
            "--allow-file-access-from-files", f"--user-data-dir={prof}", "--virtual-time-budget=4000"]
    try:
        if out_png:
            subprocess.run(base + [f"--window-size={size[0]},{size[1]}", f"--force-device-scale-factor={scale}",
                                   f"--screenshot={Path(out_png).resolve()}", src.resolve().as_uri()],
                           capture_output=True, timeout=120)
            if Path(out_png).exists():
                made.append(str(out_png))
        if out_pdf:
            subprocess.run(base + ["--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={Path(out_pdf).resolve()}",
                                   src.resolve().as_uri()], capture_output=True, timeout=120)
            if Path(out_pdf).exists():
                made.append(str(out_pdf))
    finally:
        shutil.rmtree(prof, ignore_errors=True)
    if not made:
        sys.exit("RENDER FAILED: the browser made no file. Close every Chrome window and try once more.")
    return made


def open_folder(path):
    try:
        if platform.system() == "Darwin":
            subprocess.Popen(["open", str(path)])
        elif platform.system() == "Windows":
            os.startfile(str(path))  # noqa
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def handle_text(p):
    h = (p.get("handle") or "").strip()
    return ("@" + h.lstrip("@")) if h else ""


def logo_html(p, dark=False):
    """The coach's logo if they gave one, else their business name as a word mark."""
    logo = p.get("logo") or ""
    if logo and Path(logo).exists():
        return f'<img class="logo-img" src="{Path(logo).resolve().as_uri()}">'
    name = esc(p.get("business") or "Your Coaching")
    return f'<span class="logo-word">{name}</span>'


def ffmpeg_bin():
    """ffmpeg already on the computer, else a private copy installed once into this skill's folder (no admin rights)."""
    p = shutil.which("ffmpeg")
    if p: return p
    vdir = SKILL / ".venv"
    py = vdir / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")
    if not py.exists():
        print("FIRST RUN: installing a private copy of ffmpeg into the skill folder (about a minute)...", flush=True)
        venv.create(vdir, with_pip=True)
    r = subprocess.run([str(py), "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"], capture_output=True, text=True)
    if r.returncode != 0:
        subprocess.run([str(py), "-m", "pip", "install", "-q", "imageio-ffmpeg"], check=True)
        r = subprocess.run([str(py), "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"], capture_output=True, text=True, check=True)
    return r.stdout.strip()
