"""/coach audio: cleans the voice on a gym video or voice note. Background noise and hum come down (a free noise-removal
model that ships with this skill), the voice is brightened and levelled, and the loudness is set for Instagram.
The picture is untouched. Also draws a before / after panel from the real sound.

usage: audio.py "/path/to/clip.mp4" [--client "Name"] [--strength light|normal|strong] [--no-open]
Writes "<clip> - clean.mp4" (or .m4a for audio files) and "<clip> - before and after.png" next to the other results."""
import argparse, array, json, os, platform, shutil, subprocess, sys, venv
from pathlib import Path
from common import SKILL, ASSETS, HOME, client_dir, fill, render, open_folder, ffmpeg_bin

ap = argparse.ArgumentParser()
ap.add_argument("clip"); ap.add_argument("--client", default="")
ap.add_argument("--strength", default="normal", choices=["light", "normal", "strong"]); ap.add_argument("--no-open", action="store_true")
a = ap.parse_args()
src = Path(a.clip).expanduser()
if not src.exists():
    sys.exit(f"NO FILE: {src}")

FF = ffmpeg_bin()
probe = subprocess.run([FF, "-hide_banner", "-i", str(src)], capture_output=True, text=True).stderr
has_video = "Video:" in probe and "attached pic" not in probe.split("Video:")[1][:80]
if "Audio:" not in probe:
    sys.exit("NO SOUND: this file has no audio track.")

out_dir = client_dir(a.client) if a.client else (HOME / "Clean audio")
out_dir.mkdir(parents=True, exist_ok=True)
stem = src.stem
out = out_dir / (f"{stem} - clean.mp4" if has_video else f"{stem} - clean.m4a")

# the chain: high-pass, the noise model (copied to a temp name without spaces: ffmpeg's filter syntax), gentle presence, level, loudness
model = Path(os.environ.get("TMPDIR", "/tmp") if platform.system() != "Windows" else os.environ.get("TEMP", ".")) / "coach_rnn_sh.rnnn"
shutil.copyfile(ASSETS / "audio" / "sh.rnnn", model)
mix = {"light": "mix=0.85", "normal": "mix=1", "strong": "mix=1"}[a.strength]   # any dry signal brings the noise straight back
mpath = str(model).replace("\\", "/").replace(":", "\\:")
nr = f"arnndn=m='{mpath}':{mix}" + (f",arnndn=m='{mpath}'" if a.strength == "strong" else "")
chain = (f"highpass=f=80,{nr},equalizer=f=300:t=q:w=1:g=-1.5,equalizer=f=4000:t=q:w=1:g=3,highshelf=f=9000:g=2,"
         "acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=2")
tmpwav = out_dir / f".{stem}-voice.wav"
r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vn", "-af", chain, "-ar", "48000", "-c:a", "pcm_s16le", str(tmpwav)],
                   capture_output=True, text=True)
model.unlink(missing_ok=True)
if r.returncode != 0:
    sys.exit("CLEAN FAILED: " + r.stderr[-600:])


def loudness(path):
    e = subprocess.run([FF, "-hide_banner", "-i", str(path), "-af", "ebur128=framelog=quiet", "-f", "null", "-"], capture_output=True, text=True).stderr
    for l in e.splitlines()[::-1]:
        if " I:" in l: return float(l.split("I:")[1].split("LUFS")[0])
    return -23.0


# loudness for Instagram (-14 LUFS) as ONE fixed gain and a peak limiter: a level-riding normaliser would lift the noise back up between words
gain = -14.0 - loudness(tmpwav)
cmd = [FF, "-hide_banner", "-loglevel", "error", "-y"] + (["-i", str(src)] if has_video else []) + ["-i", str(tmpwav),
       "-af", f"volume={gain:.2f}dB,alimiter=limit=0.84:level=false", "-ar", "48000"]
cmd += (["-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart"] if has_video
        else ["-c:a", "aac", "-b:a", "256k"])
r = subprocess.run(cmd + [str(out)], capture_output=True, text=True)
tmpwav.unlink(missing_ok=True)
if r.returncode != 0 or not out.exists():
    sys.exit("CLEAN FAILED: " + r.stderr[-600:])


# ------------------------------------------------------------------ before / after panel from the real sound
def bars(path, n=96):
    raw = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    s = array.array("h"); s.frombytes(raw[: len(raw) // 2 * 2])
    if not s: return [0] * n
    step = max(1, len(s) // n); out = []
    for i in range(n):
        seg = s[i * step:(i + 1) * step] or array.array("h", [0])
        out.append((sum(x * x for x in seg[::4]) / max(1, len(seg[::4]))) ** 0.5)
    return out


import math
b, c = bars(src, 110), bars(out, 110)
def norm(v):   # each wave against its own loud parts, so the gaps between words show how much noise sits there
    s = sorted(v); ref = s[int(len(s) * 0.95)] or 1
    return [min(1.0, x / ref) for x in v]
def floor_db(v):   # the quiet parts (10th percentile) against the loud parts (90th), in dB
    s = sorted(v); return 20 * math.log10(max(1e-6, s[int(len(s) * 0.1)]) / max(1e-6, s[int(len(s) * 0.9)]))
drop = round(floor_db(bars(src, 400)) - floor_db(bars(out, 400)))
def html_bars(v, col):
    return "".join(f'<i style="height:{max(4, 116 * x):.0f}px;background:{col}"></i>' for x in norm(v))
panel = fill("audio-panel.html", {"name": stem, "before": html_bars(b, "#BDB6AC"), "after": html_bars(c, "#C8442B"),
                                  "drop": f"Noise between words down {drop} dB" if drop >= 3 else "Background noise down"})
png = out_dir / f"{stem} - before and after.png"
render(panel, out_png=str(png), size=(1080, 640), scale=1)
png.with_suffix(".html").unlink(missing_ok=True)

lv = subprocess.run([FF, "-hide_banner", "-i", str(out), "-af", "ebur128=framelog=quiet", "-f", "null", "-"], capture_output=True, text=True).stderr
lufs = next((l.split("I:")[1].split("LUFS")[0].strip() for l in lv.splitlines()[::-1] if " I:" in l), "?")
print(json.dumps({"clean": str(out), "panel": str(png), "loudness_lufs": lufs, "noise_drop_db": drop, "video": has_video, "folder": str(out_dir)}, indent=1))
if not a.no_open: open_folder(out_dir)
