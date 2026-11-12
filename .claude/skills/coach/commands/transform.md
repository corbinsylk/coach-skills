# /coach transform

A client's before and after progress photos become a premium before/after reveal: both bodies cut out on one dark studio under a
soft rim light, a scan line sweeps head to thighs and the after replaces the before as it passes, then four callouts draw in on what
changed. One locked design. **Mac only** (the cut-out uses Apple's subject lift, macOS 14 Sonoma or newer). On Windows or Linux say
so plainly in one line and stop.

## The physique is never changed

This is the whole point: the result has to be genuine. The tool changes only:
- **the scale**: one uniform scale, so both torsos (neck to hips) are the same length. The bones match and the real change shows.
- **the lighting**: the before's exposure moves to the after's. Its contrast stays its own (raising it draws shadows that weren't there).
- **the skin colour**: the before's white balance and skin tone move to the after's.
- **the clarity**: a light denoise on the before, the same gentle sharpen on both.

No warping, no slimming, no AI on either photo. Never offer to "enhance" a body, and refuse if asked: say it would make the
transformation fake, and that the tool only matches the lighting and size.

## What you need

1. **The before photo** and **the after photo**: "Drag in the before photo." then "Now the after." Never change or move their files.
   Best results: front-on, similar distance, shirt off or fitted, the whole torso in view. Phone screenshots are fine (the black bars are cut).
2. **The client's name** (for the folder). Optional: if they don't give one, it goes in `Transformations`.
3. Optional, only if they say: a line over the header like the time it took ("12 weeks"), and their own callout words.

## The callouts

Four words-only callouts, top to bottom. The default is **Shoulders broader · Chest fuller · Abs visible · Waist tighter**.
Before you run it, **look at both photos yourself** and keep only claims the photos plainly show. Swap any that aren't true
(e.g. "Arms bigger", "Core tighter", "Waist slimmer"). The parts it can point at: shoulders, chest, abs/core/stomach, waist/hips,
arms. Numbers only when the coach gives the client's real numbers ("Waist:-9 cm", "Weight:-8 kg"); never guess one.

## Run it

```
python3 tools/transform.py --before "/path/before.jpg" --after "/path/after.jpg" --client "Sarah" \
  [--label "12 weeks"] [--callouts "Shoulders:broader,Chest:fuller,Abs:visible,Waist:tighter"] [--no-video]
```

The first run prints `FIRST RUN: building the photo matcher`: a one-time setup, about 20 seconds. If it says `NO SWIFT`, they need
Apple's free command line tools: run `xcode-select --install` and have them click Install. A full run takes about a minute.

## Check it before handing over

Open `<name> - transform.png` and look. The two bodies should stand torso on torso and the callout dots should sit on the body.
- `NO PERSON FOUND` / `BODY NOT FOUND`: the photo needs the person clear of the background and the shoulders and hips in view. Ask
  for another photo.
- A dot off the body, or the bodies badly out of line (very different poses or distances): say so in one line and ask for a closer
  matching pair. Never fix it by moving or reshaping a body.

## Hand it over

- `<name> - transform.mp4`: the 4.5-second reveal, 1080 x 1920. Post it as a reel or story, or drop it into an edit.
- `<name> - transform.png`: the after with the callouts, for a carousel or a story.
- `<name> - transform cover.png`: the mid-scan frame (half before, half after), a strong reel cover.

Their brand colour from the profile is the rim light and accents (a near-black one falls back to the warm default), and their logo or
handle sits under the body. Get the client's permission before posting their photos.
