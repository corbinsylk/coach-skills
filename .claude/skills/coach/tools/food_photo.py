"""A food photo for a recipe page, made with the coach's Gemini. By default it matches the house look: two of the pack's own photos
go to Gemini as the style reference. A coach who wants a different look passes --style, and then no references are sent, so the
photos don't drift back to the house look. Saved to the coach's library and reused by name from then on.

usage: food_photo.py --dish "chicken teriyaki rice bowl with edamame and sesame" [--name chicken-teriyaki] [--style "dark and moody, black slate"]
Prints the photo name to put in the plan's "photo" field."""
import argparse, json, re, sys
from common import ASSETS, HOME
from gemini import image

ap = argparse.ArgumentParser()
ap.add_argument("--dish", required=True); ap.add_argument("--name"); ap.add_argument("--style", default="")
a = ap.parse_args()
name = a.name or re.sub(r"[^a-z0-9]+", "-", a.dish.lower()).strip("-")[:40]
LIB = HOME / "Library" / "food"; LIB.mkdir(parents=True, exist_ok=True)
HOUSE = ("Premium editorial food photography, photorealistic, shot on a full-frame camera with a 50mm lens, soft natural window light from the left, "
         "light and airy, white marble table with a linen napkin, shallow depth of field, fresh vibrant colours, appetising, magazine cover quality.")
if a.style:
    look, refs = f"Premium food photography, photorealistic, appetising, magazine quality. Style: {a.style}.", []
else:
    look = HOUSE + " Match the light, colour, table and camera angle of the reference photos exactly; only the food changes."
    refs = [ASSETS / "food" / "chicken-rice-bowl.jpg", ASSETS / "food" / "salmon-sweet-potato.jpg"]
prompt = (f"{look} No text, no logos, no hands, no people. Close three-quarter angle of {a.dish}. "
          "The dish sits in the top half of the frame; the lower half is soft out-of-focus table.")
try:
    raw = image(prompt, refs, aspect="3:4")
except RuntimeError as e:
    sys.exit(str(e))
ext = ".png" if raw[:4] == b"\x89PNG" else ".jpg"
dst = LIB / f"{name}{ext}"
for old in LIB.glob(f"{name}.*"): old.unlink()
dst.write_bytes(raw)
print(json.dumps({"photo": name, "file": str(dst)}))
