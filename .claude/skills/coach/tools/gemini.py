"""The coach's Gemini connection: where the key lives, a test, and one image call. Standard library only.
The key is kept in a private file on their computer and is never printed, so it never enters the chat.

Used by connect.py (saves the key), new_muscle.py and food_photo.py (make images)."""
import base64, json, os, platform, stat, time, urllib.error, urllib.request
from pathlib import Path

MODELS = ["gemini-3.1-flash-image", "gemini-nano-banana-2.1"]   # the first is the one the pack was made with; the second if Google retires it
API = "https://generativelanguage.googleapis.com/v1beta/models"


def key_path():
    base = Path(os.environ.get("APPDATA", "")) if platform.system() == "Windows" else Path.home() / ".config"
    return base / "coach-skills" / "gemini.key"


def load_key():
    if os.environ.get("GEMINI_API_KEY"): return os.environ["GEMINI_API_KEY"].strip()
    p = key_path()
    return p.read_text().strip() if p.exists() else ""


def save_key(k):
    p = key_path(); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(k.strip())
    try: os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)
    except Exception: pass


def test_key(k):
    """True if Google accepts the key. Returns (ok, message)."""
    req = urllib.request.Request(f"{API}?pageSize=5", headers={"x-goog-api-key": k.strip()})
    try:
        urllib.request.urlopen(req, timeout=30); return True, "connected"
    except urllib.error.HTTPError as e:
        return False, {400: "that key isn't valid", 401: "that key isn't valid", 403: "that key isn't allowed to use Gemini"}.get(e.code, f"Google said {e.code}")
    except Exception as e:
        return False, f"couldn't reach Google ({e.__class__.__name__})"


def image(prompt, images=(), aspect="3:4", size=""):
    """One image from Gemini: the prompt plus any reference images (paths). Returns PNG/JPEG bytes. Raises RuntimeError with a plain reason."""
    k = load_key()
    if not k: raise RuntimeError("NOT CONNECTED: run tools/connect.py first")
    parts = []
    for p in images:
        p = Path(p); mt = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        parts.append({"inlineData": {"mimeType": mt, "data": base64.b64encode(p.read_bytes()).decode()}})
    parts.append({"text": prompt})
    cfg = {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect, **({"imageSize": size} if size else {})}}
    body = json.dumps({"contents": [{"role": "user", "parts": parts}], "generationConfig": cfg}).encode()
    last = ""
    for model in MODELS:
        for attempt in range(6):
            req = urllib.request.Request(f"{API}/{model}:generateContent", data=body,
                                         headers={"x-goog-api-key": k, "Content-Type": "application/json"})
            try:
                d = json.load(urllib.request.urlopen(req, timeout=300))
            except urllib.error.HTTPError as e:
                last = e.read().decode(errors="ignore")[:300]
                if e.code == 429 or e.code >= 500:   # busy: wait and try again
                    time.sleep(8 * (attempt + 1)); continue
                if e.code == 404: break               # this model is gone: try the next one
                if e.code in (400, 403) and "billing" in last.lower():
                    raise RuntimeError("BILLING: image generation needs billing turned on in Google AI Studio (about 4 cents an image)")
                raise RuntimeError(f"GEMINI ERROR {e.code}: {last}")
            for c in d.get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    if "inlineData" in p: return base64.b64decode(p["inlineData"]["data"])
            last = "no image came back"; time.sleep(3)
    raise RuntimeError(f"GEMINI FAILED: {last}")
