# /coach macros

A client's daily calories, protein, carbs and fat, drawn as a branded macro card (PNG + PDF) to send them. The maths is
Mifflin-St Jeor for the base, the job plus training days for activity, and the goal for the deficit or surplus. Protein comes
from body weight, fat is a share, and carbs are the rest.

## First

Do the brand check from SKILL.md the first time.

## What you need

Use anything they already said (e.g. "182cm, 84kg, lean bulk"). Ask only for what's missing, **one at a time**, in this order:

1. Client's name
2. Male or female
3. Age
4. Height
5. Weight
6. Goal: fat loss, lean bulk, maintain, or recomp
7. Goal weight (optional: "Got a goal weight? Or skip.")
8. Training days a week
9. Their job: desk, on their feet, or physical work
10. Meals a day (default 3)

If they gave enough to work it out and seem in a hurry, use the defaults for 7-10 (no goal weight, 3 days, desk, 3 meals) and
say which defaults you used.

## Run it

```
python3 tools/macros.py --name "Sarah M." --sex female --age 29 --height 168 --weight 82 --goal fat-loss \
  --goal-weight 75 --training-days 4 --job desk --meals 3 [--diet balanced|high-protein|low-carb] [--notes "..."]
```

Height can be `168`, `168cm`, `5'6` or `66in`. Weight can be `82`, `82kg` or `180lb`. Plain numbers follow their units setting.
If the coach wants their own number ("make it 2,000"), pass `--kcal 2000` and the macros follow it.
`--notes` puts a line in the card's Coach notes box (e.g. "Hit protein first, carbs around training").

## Hand it over

`<client> - Macros.png` (for a DM) and `<client> - Macros.pdf` (to print or attach). Say the numbers in one line:
"1,730 kcal: 180g protein, 140g carbs, 50g fat."
Then offer the next step: "Want a recipe book that hits these? Say /coach meals."
