# /coach meals

A locked design, every time: the cover, a "how to use this book" page, then one page per recipe with a photo of the dish full
bleed behind a frosted card. It carries the coach's logo, accent colour and heading font, and nothing else changes. A recipe
book (PDF, plus each page as an image) and a weekly grocery list, built so that **any day the client builds lands on
their macros**: one recipe from each meal section. You write the recipes. The tool works out every recipe's macros from a
nutrition table and scales the portions until each one hits its share of the day. Never guess macros yourself.

## First

Do the Gemini and brand checks from SKILL.md the first time. Then you need the client's targets: if `/coach macros` was run for this
client, the tool reads them by itself. If not, ask for their calories and macros, or offer to run `/coach macros` first.

## What you need

Ask one at a time, and skip anything they already said:

1. Client's name (the same name as their macro card)
2. Meals a day (default: their macro card's number)
3. Foods they love, and foods they won't eat (allergies, dislikes, vegetarian and so on)
4. How hard the recipes can be: "quick and simple", "normal", or "I like cooking"
5. How many options per meal (default 2: enough variety, a short shopping list)

## Write the plan

Write a JSON file in their client folder (`Documents/Coach Skills/<client>/plan.json`) in exactly the format at the top of
`tools/meals.py`. The rules:

- **Slots** are the meals of the day with their share of the calories. 3 meals: Breakfast 0.3, Lunch 0.35, Dinner 0.35.
  4 meals: Breakfast 0.25, Lunch 0.3, Snack 0.15, Dinner 0.3. Change it if the coach asks (e.g. a big post-training meal).
- **Ingredients** use the exact names in `assets/foods.json` (raw weights for meat, fish, potatoes and vegetables; cooked
  weights for rice and quinoa; dry for pasta, oats and noodles). Count eggs and fruit with `"pieces"`. Herbs, spices and salt
  are `"to_taste": true`. For a branded product (a protein bar, a yoghurt brand) give `"per100"` values from the pack and an `"aisle"`.
- **Roles:** mark the one main protein `"role": "protein"`, the main carb `"role": "carb"`, and the main fat source (oil, nuts,
  avocado, cheese) `"role": "fat"`. Those are the portions the tool scales. Every recipe needs at least a protein and a carb role.
- **Photo:** every recipe page has a photo of that dish behind it.
  1. If a photo in `photos_available` (from the check) is clearly the same dish, use it: it's free and instant
     (`chicken-rice-bowl`, `overnight-oats` and so on).
  2. Otherwise make one with their Gemini (about 4 cents each):
     `python3 tools/food_photo.py --dish "<what's on the plate, in plain words>"`. It prints the name to put in `"photo"`.
     It matches the house look by itself: light, white marble, three-quarter angle.
  3. If the coach wants a different look ("dark and moody", "overhead on wood"), pass `--style "..."` on every photo in that
     book and skip the bank photos, so the whole book matches. The page layout never changes, only the photos.
  If Gemini isn't connected, do the Gemini step in SKILL.md first. If it still fails, leave `"photo"` out and that page gets a
  soft plain background. Say so.
- Steps: three or four short ones, written as a coach would say them. Respect the difficulty they chose.

## Check, then build

1. `python3 tools/meals.py "<plan.json>" --check` prints every recipe's macros against its target and the portions it chose.
2. Fix any recipe more than 10% off (`off_pct`). The usual fix is to give a fatty protein (salmon, steak, whole eggs) a lean
   partner with the protein role (egg whites, Greek yoghurt), or to cut a second fat. Also fix portions that look silly (20 g of
   oats, 400 g of chicken): change the recipe and check again. Two rounds at most.
3. `python3 tools/meals.py "<plan.json>"` builds everything.

## Hand it over

- `<client> - Recipe Book.pdf`: cover, a "how to use this book" page listing every option with its macros, then one page per recipe
- `Recipe pages/`: each page as an image for DMs
- `<client> - Grocery List.pdf` and `.png`: one week of shopping, grouped by aisle, with tick boxes

Say in one line how close it landed ("Every day lands within 3% of 1,730 kcal and 180g protein").
