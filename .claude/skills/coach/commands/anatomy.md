# /coach anatomy

A flat, drawn body (white line art on black) with the muscles an exercise works glowing: the main ones bright, the helpers
dimmer. It picks the clearest view by itself:
- **side** for arm and shoulder work (curls, raises, pushdowns), where the whole arm and all three heads of the shoulder show
- **front** or **back** wherever most of the work is (bench → front, rows → back)
- **both** side by side when it's split evenly (squats, deadlifts)

## What you need

1. **The exercise.** "Which exercise?" if they didn't say.
2. **Male or female body.** Default male. If the coach, their client or their audience is clearly female, use female. Ask
   only when it's a toss-up: "Male or female body?"

Optional, only if they ask: a view (front, back, side, both), a colour (any hex code; turn a colour name into one and tell them),
a client name.

## Run it

Look the exercise up yourself first. The muscles you can light up are:
`chest, front-delts, side-delts, rear-delts, biceps, triceps, forearms, abs, obliques, quads, adductors, traps, lats,
lower-back, glutes, hamstrings, calves`.

```
python3 tools/anatomy.py --exercise "Shoulder press" [--primary front-delts,side-delts --secondary triceps] [--body female] [--view auto] [--colour "#E5484D"]
```

Leave out `--primary` and it uses its own list of about 75 common exercises. For anything not on it (a machine name, a variation),
pass `--primary` and `--secondary` yourself: primary is the muscle doing most of the work, secondary are the helpers. Keep it to
what a coach would say. Two or three muscles, not every stabiliser.

## Hand it over

- `<exercise> - anatomy.png`: a 4:5 post with the exercise name and the muscles, ready for a carousel or story.
- `<exercise> - body.png`: just the body, with no background, to drop over their own video.

If `not_visible_in_this_view` lists a muscle the coach cares about, offer the other view ("Want the back view too, so the
triceps show?").
