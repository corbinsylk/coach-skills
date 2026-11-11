# /coach anatomy

One locked design, every time. A drawn muscle-atlas body: line art only, no shading, on a **transparent background**, so it lays
over the coach's own video. Only the worked muscles are filled, with a soft glow: the main ones full strength, the helpers at half.
A tag in the top right names them (e.g. ARMS / Biceps brachii). The upper body is framed from head to hips; when legs or glutes
are involved, the whole body shows. The head is always in.

The coach chooses only:
- **Body:** male (default) or female.
- **Glow colour** from the stock list: **red (the default, and the one we recommend)**, orange, yellow, green, teal, blue,
  purple, pink. No hex codes, so it always stays the muted atlas look.
- **Outlines:** white (the default, for dark gyms) or black (for light videos).
- **View:** picked for them (see below). They can ask for another.

## The view

- **side** for arm and shoulder work (curls, raises, pushdowns): the whole arm and all three heads of the shoulder show
- **front** or **back** wherever most of the work is (bench → front, rows → back, squats → back for the glutes)

## What you need

1. **The exercise.** "Which exercise?" if they didn't say.
2. **Male or female body.** Default male. If the coach, their client or their audience is clearly female, use female. Ask only
   when it's a toss-up.
3. Colour and outlines: use red and white unless they say otherwise. The first time, mention it in one line: "Red glow, white
   outlines. Say if you want another colour or black lines."

## Run it

The muscles in the pack are: `chest, front-delts, side-delts, rear-delts, biceps, triceps, forearms, abs, obliques, quads,
adductors, traps, lats, lower-back, glutes, hamstrings, calves`.

```
python3 tools/anatomy.py --exercise "Shoulder press" [--primary front-delts,side-delts --secondary triceps] [--body female] [--colour red] [--outline white] [--view auto]
```

Leave out `--primary` and it uses its own list of about 75 common exercises. For anything else, pass `--primary` (the muscle
doing most of the work) and `--secondary` (the helpers) yourself. Keep it to what a coach would say: two or three muscles.

## A muscle the pack doesn't have

If the coach wants a muscle that isn't in the list (rhomboids, rotator cuff, brachialis, serratus, hip flexors, neck), or the
result lists it under `missing_in_this_view`, add it with their Gemini (about 4 cents and 30 seconds a muscle; it's saved for
next time):

```
python3 tools/new_muscle.py --body male --view back --muscle rhomboids --name "Rhomboids" --heading "Upper back" \
  --describe "the rhomboids, the muscles between the shoulder blades on both sides" [--upper yes|no]
```

`--describe` says plainly where the muscle sits on the body, like an anatomy atlas would. `--upper no` for legs and glutes.
Then run `anatomy.py` again with that muscle's name. If it prints NOT ADDED, it says why: reword the description once and try
again. After a second failure, offer the nearest muscle in the pack. If it prints NOT CONNECTED or BILLING, do the Gemini step
in SKILL.md.

Muscles under `not_visible_from_this_side` can't be seen from that view. Offer the other view if the coach cares about them
("Want the front view too, so the quads show?").

## Hand it over

- `<exercise> - anatomy.png`: transparent, 1080 x 1350. Drop it over the video in any editing app.
- `<exercise> - preview.png`: the same on a background, to look at or post as it is.
