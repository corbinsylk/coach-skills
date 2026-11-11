"""Shared helpers for the /coach tools: the coach's profile, the output folder, and HTML -> PNG / PDF through the
browser already on the computer (Chrome, Edge, Brave or Chromium). Standard library only."""
import json, os, re, shutil, subprocess, sys, tempfile, platform
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


def font_css():
    """The two fonts ship in assets/fonts (SIL Open Font Licence)."""
    f = (ASSETS / "fonts").as_uri()
    return (f"@font-face{{font-family:'Jakarta';src:url('{f}/PlusJakartaSans.ttf') format('truetype');font-weight:200 800;}}"
            f"@font-face{{font-family:'Inter';src:url('{f}/Inter.ttf') format('truetype');font-weight:100 900;}}")


def fill(template, values):
    """{{key}} placeholders in a template file."""
    html = (TEMPLATES / template).read_text()
    values = {"fonts": font_css(), "assets": ASSETS.as_uri(), **values}
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
