"""/coach transform: a client's before and after progress photos -> a premium before/after reveal, the physique untouched.
Both bodies are cut out and matched (transform_match.swift: one uniform scale on torso length, exposure and skin colour only, light
denoise and the same sharpen on both; no warp, no AI on the body), then set on one dark studio: a scan line sweeps head to thighs,
the after replacing the before, and four callouts draw in. Chrome draws every frame; ffmpeg makes the MP4. Mac only (the cut-out is
Apple's subject lift).

usage: transform.py --before "/path/before.jpg" --after "/path/after.jpg" [--client "Name"]
                    [--callouts "Shoulders:broader,Chest:fuller,Abs:visible,Waist:tighter"] [--label "12 weeks"] [--no-video] [--no-open]
Writes "<name> - transform.mp4" (1080 x 1920, 30 fps), "<name> - transform.png" (the last frame, with the callouts) and
"<name> - transform cover.png" (mid-scan: half before, half after)."""
import argparse, base64, fcntl, json, os, platform, shutil, subprocess, sys, tempfile
from pathlib import Path
from common import SKILL, HOME, client_dir, slug, fill, open_folder, find_browser, esc, load_profile, accent_hex, handle_text, logo_html, ffmpeg_bin

ap = argparse.ArgumentParser()
ap.add_argument("--before", required=True); ap.add_argument("--after", required=True); ap.add_argument("--client", default="")
ap.add_argument("--callouts", default="Shoulders:broader,Chest:fuller,Abs:visible,Waist:tighter")
ap.add_argument("--label", default=""); ap.add_argument("--no-video", action="store_true"); ap.add_argument("--no-open", action="store_true")
a = ap.parse_args()

if platform.system() != "Darwin":
    sys.exit("MAC ONLY: /coach transform cuts the body out with Apple's subject lift, which only runs on a Mac (macOS 14 or newer).")
src = {n: Path(p).expanduser() for n, p in (("before", a.before), ("after", a.after))}
for n, p in src.items():
    if not p.exists(): sys.exit(f"NO FILE: the {n} photo ({p})")

# the matcher is compiled once on this Mac (Apple's own compiler, part of the free command line tools)
TOOLS = Path(__file__).resolve().parent
BIN = SKILL / ".bin" / "transform_match"
SWIFT = TOOLS / "transform_match.swift"
if not BIN.exists() or BIN.stat().st_mtime < SWIFT.stat().st_mtime:
    if not shutil.which("swiftc"):
        sys.exit("NO SWIFT: run `xcode-select --install` once (Apple's free installer; click Install), then run this again.")
    print("FIRST RUN: building the photo matcher (about 20 seconds)...", flush=True)
    BIN.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["swiftc", "-O", str(SWIFT), "-o", str(BIN)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("BUILD FAILED: " + (r.stderr.strip().splitlines() or ["swiftc gave no reason"])[-1])

out_dir = client_dir(a.client) if a.client else HOME / "Transformations"
out_dir.mkdir(parents=True, exist_ok=True)
base = f"{slug(a.client)} - transform" if a.client else "Transform"
name, n = base, 2
while (out_dir / f"{name}.png").exists() or (out_dir / f"{name}.mp4").exists():
    name, n = f"{base} {n}", n + 1
work = out_dir / f".{name}"            # the matched cut-outs and the page; hidden, kept for a re-run
work.mkdir(parents=True, exist_ok=True)

r = subprocess.run([str(BIN), str(src["before"]), str(src["after"]), str(work)], capture_output=True, text=True)
if r.returncode != 0:
    shutil.rmtree(work, ignore_errors=True)
    sys.exit((r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "MATCH FAILED")
match = json.loads((work / "match.json").read_text())
A = match["anchors"]

# the arm point: halfway down the image-right upper arm
sh = sorted([A["left_shoulder_1_joint"], A["right_shoulder_1_joint"]])[1]
fa = [A[k] for k in ("left_forearm_joint", "right_forearm_joint") if k in A]
if fa:
    f = min(fa, key=lambda p: abs(p[0] - sh[0]) + abs(p[1] - sh[1]))
    A["arm"] = [round((sh[0] + f[0]) / 2 + 18, 1), round((sh[1] + f[1]) / 2, 1)]
else:
    A["arm"] = [sh[0] - 10, sh[1] + 90]

# the callouts: words only, each one a claim about what is visible. A title naming a body part lands on that part.
PART = {"shoulder": "shoulder", "delt": "shoulder", "chest": "chest", "pec": "chest", "ab": "abs", "core": "abs", "stomach": "abs",
        "belly": "abs", "waist": "waist", "hip": "waist", "love": "waist", "arm": "arm", "bicep": "arm", "tricep": "arm"}
SIDE = {"shoulder": "l", "chest": "r", "abs": "l", "waist": "r", "arm": "r"}
calls, used = [], []
for item in [c for c in a.callouts.split(",") if c.strip()][:4]:
    title, _, sub = item.partition(":")
    title, sub = title.strip(), sub.strip()
    part = next((v for k, v in PART.items() if title.lower().startswith(k)), None)
    if part in used or part is None:
        part = next(p for p in ("shoulder", "chest", "abs", "waist", "arm") if p not in used)
    used.append(part)
    calls.append({"part": part, "title": title, "sub": sub, "side": SIDE[part], "anchor": A[part]})
calls.sort(key=lambda c: c["anchor"][1])
last = {"l": -1e9, "r": -1e9}
for i, c in enumerate(calls):           # labels sit a little above their point, never closer than 150 px on one side
    ly = max(c["anchor"][1] - 100, last[c["side"]] + 150, 430)
    ly = min(ly, 1560); last[c["side"]] = ly
    c["label"] = [330 if c["side"] == "l" else 770, round(ly)]
    c["at"] = round(1.6 + 0.18 * i, 2)

prof = load_profile()
acc = accent_hex(prof.get("accent")) or "#D97757"
rgb = [int(acc[i:i + 2], 16) for i in (1, 3, 5)]
if 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2] < 70:      # a near-black accent would vanish on the dark studio
    acc, rgb = "#D97757", [217, 119, 87]
brand = logo_html(prof) if prof.get("logo") else esc(handle_text(prof))
DUR = 4.5
html = fill("transform.html", {"before": (work / "before.png").as_uri(), "after": (work / "after.png").as_uri(), "anchors": json.dumps(A),
                               "calls": json.dumps(calls), "duration": DUR, "accent": acc, "rgb": ",".join(map(str, rgb)),
                               "label": esc(a.label.upper()), "brand": brand})
page = work / "transform.html"
page.write_text(html)


class Chrome:
    """Chrome without a window, driven over its DevTools pipe (fd 3 in, fd 4 out): one browser draws every frame."""

    def __init__(self, browser):
        self.prof = tempfile.mkdtemp(prefix="coach-chrome-")
        to_child, self.w = os.pipe()
        self.r, from_child = os.pipe()
        hi_in, hi_out = fcntl.fcntl(to_child, fcntl.F_DUPFD, 20), fcntl.fcntl(from_child, fcntl.F_DUPFD, 20)

        def pre():
            os.dup2(hi_in, 3); os.dup2(hi_out, 4)

        self.p = subprocess.Popen([browser, "--headless=new", "--remote-debugging-pipe", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                                   "--no-default-browser-check", "--allow-file-access-from-files", f"--user-data-dir={self.prof}",
                                   "--window-size=1080,1920", "about:blank"], preexec_fn=pre, pass_fds=(3, 4),
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for fd in (to_child, from_child, hi_in, hi_out): os.close(fd)
        self.buf, self.n, self.events = b"", 0, []
        tid = self.call("Target.createTarget", {"url": "about:blank"})["targetId"]
        self.sid = self.call("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
        self.call("Emulation.setDeviceMetricsOverride", {"width": 1080, "height": 1920, "deviceScaleFactor": 1, "mobile": False}, self.sid)
        self.call("Page.enable", {}, self.sid)

    def call(self, method, params, sid=None):
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params}
        if sid: msg["sessionId"] = sid
        os.write(self.w, json.dumps(msg).encode() + b"\0")
        while True:
            while b"\0" not in self.buf:
                chunk = os.read(self.r, 1 << 20)
                if not chunk: raise RuntimeError("the browser closed")
                self.buf += chunk
            raw, self.buf = self.buf.split(b"\0", 1)
            m = json.loads(raw)
            if m.get("id") == self.n:
                if "error" in m: raise RuntimeError(m["error"].get("message", "browser error"))
                return m.get("result", {})
            self.events.append(m.get("method"))

    def run(self, js):
        r = self.call("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True}, self.sid)
        if "exceptionDetails" in r: raise RuntimeError("page error: " + r["exceptionDetails"].get("text", ""))
        return r.get("result", {}).get("value")

    def shot(self, path):
        Path(path).write_bytes(base64.b64decode(self.call("Page.captureScreenshot", {"format": "png"}, self.sid)["data"]))

    def close(self):
        try: self.call("Browser.close", {})
        except Exception: pass
        try: self.p.wait(timeout=10)
        except Exception: self.p.kill()
        for fd in (self.w, self.r):
            try: os.close(fd)
            except OSError: pass
        shutil.rmtree(self.prof, ignore_errors=True)


br = find_browser()
if not br: sys.exit("NO BROWSER: install Google Chrome (free), then run this again.")
made = []
frames = Path(tempfile.mkdtemp(prefix="coach-transform-"))
c = Chrome(br)
try:
    c.call("Page.navigate", {"url": page.as_uri() + "?capture=1"}, c.sid)
    c.run("new Promise(r => { const w = () => window.ready ? window.ready.then(r) : setTimeout(w, 50); w(); })")
    for t, still in ((0.9, out_dir / f"{name} cover.png"), (DUR, out_dir / f"{name}.png")):
        c.run(f"draw({t})"); c.shot(still); made.append(str(still))
    if not a.no_video:
        print("Drawing the video...", flush=True)
        total = int(DUR * 30)
        for i in range(total):
            c.run(f"draw({i / 30})"); c.shot(frames / f"{i:04d}.png")
finally:
    c.close()

if not a.no_video:
    mp4 = out_dir / f"{name}.mp4"
    ff = ffmpeg_bin()
    r = subprocess.run([ff, "-v", "error", "-y", "-framerate", "30", "-i", str(frames / "%04d.png"), "-c:v", "libx264", "-preset", "slow",
                        "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)], capture_output=True, text=True)
    if r.returncode != 0 or not mp4.exists():
        sys.exit("VIDEO FAILED: " + (r.stderr.strip().splitlines() or ["ffmpeg gave no reason"])[-1])
    made.insert(0, str(mp4))
shutil.rmtree(frames, ignore_errors=True)

print(json.dumps({"files": made, "folder": str(out_dir), "callouts": [f"{c_['title']} {c_['sub']}" for c_ in calls],
                  "before_scale": round(match["before"]["scale"], 3), "after_scale": round(match["after"]["scale"], 3),
                  "exposure_shift": round(match["skin_lab"]["exposure_shift_L"], 1)}, indent=1))
if not a.no_open: open_folder(out_dir)
