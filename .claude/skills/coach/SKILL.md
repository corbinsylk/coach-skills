---
name: coach
description: Five tools for fitness coaches. Use when the user types /coach, or asks to clean up gym audio or a noisy voice on a video, show which muscles an exercise works (an anatomy or muscle diagram), work out a client's macros or calories, build a meal plan, recipe book or grocery list that hits a client's macros, or edit a video. Commands are /coach audio, /coach anatomy, /coach macros, /coach meals and /coach edit.
argument-hint: "audio | anatomy | macros | meals | edit  [details]"
---

# /coach

Five tools for fitness coaches. The user typed `/coach` followed by a command and maybe some details, or asked in plain words
for one of these jobs. Work out which command it is, then open that command's file in the `commands/` folder next to this
file and follow it exactly.

| Command | What it does | File |
|---|---|---|
| `audio` | Cleans the voice on a gym video or voice note | `commands/audio.md` |
| `anatomy` | A body with the muscles an exercise works glowing | `commands/anatomy.md` |
| `macros` | A client's calories and macros, as a branded card | `commands/macros.md` |
| `meals` | A recipe book and grocery list that hit those macros | `commands/meals.md` |
| `edit` | The full video edit (Creator OS) | `commands/edit.md` |

If they typed only `/coach`, show this and ask which one they want:

> **/coach** gives you five tools:
> - `/coach audio` + your clip: cleans up gym audio
> - `/coach anatomy` + an exercise: shows the muscles it works
> - `/coach macros` + your client's stats: their macro card
> - `/coach meals`: a recipe book and grocery list that hit those macros
> - `/coach edit`: the full video edit
>
> Which one?

## How to talk to the coach

- They are coaches, not programmers. Never explain code, file paths inside this skill, or the commands you run. Say what
  you're doing in a few plain words ("Cleaning the audio now").
- Ask for missing details **one short question at a time**, never a form. Use what they already said; never ask twice.
- When a result is ready, the folder opens on its own. Tell them the file names and one line on what to do with them.
- Every tool is in `tools/` next to this file. Run them with `python3` from that folder (on Windows `python` if `python3` is
  missing). Everything runs on their computer. The only thing that leaves it: when a new muscle or food photo is needed, the
  drawing or dish description goes to their own Gemini account.

## First time only: Gemini

`anatomy` and `meals` need the coach's Gemini connection (it draws new muscles and food photos). Before either, run
`python3 tools/connect.py --status`. If it says NOT CONNECTED, do the connect step exactly as in the install (CLAUDE.md at the
repo root, step 4): the browser page takes the key, never the chat.

## First time only: their brand

The macro card, recipe book and grocery list are LOCKED designs: the layout never changes. Only four things are the coach's:
their logo, one accent colour, one heading font, and their name and handle. Before the first `macros` or `meals` job, run
`python3 tools/profile.py show`. If `set_up` is false, ask these, one at a time:

1. "What's your coaching business called?"
2. "Your Instagram handle?" (optional)
3. "Drag in your logo, ideally a transparent PNG. Or say skip." (without one, the business name is used)
4. "Pick an accent colour: green, lime, teal, blue, purple, pink, red, orange, gold or black. Or give me your brand's hex code."
5. "Pick a font for the headings." Offer the list from `python3 tools/profile.py fonts`. Sans: Plus Jakarta Sans, Inter, Montserrat,
   DM Sans, Poppins. Serif: Playfair Display, Fraunces, Lora, DM Serif Display. Or "drag in your own font file". Ask whether
   their own font is a serif or a sans.
6. "Kilos and centimetres, or pounds and feet?"

Then save it: `python3 tools/profile.py set --business "..." --handle "..." --logo "/path" --accent blue --font "Montserrat"
--units metric` (own font: `--font-file "/path/font.otf" --font-kind serif`). Never ask again unless they want to change
something ("change my accent to orange" → run `set` with just that).

## Where results go

Everything lands in `Documents/Coach Skills/`, one folder per client (or `Clean audio` and `Anatomy` when no client is named).
Nothing they gave you is ever changed or moved.

## If something breaks

- `NO BROWSER`: the cards are drawn by Google Chrome. Ask them to install Chrome (free, google.com/chrome), then run it again.
- `python3` not found: on a Mac, run `xcode-select --install` once (it's Apple's free installer and asks them to click Install);
  on Windows, install Python from python.org and tick "Add to PATH".
- Anything else: read the last lines of the error, fix what you can (a wrong path, a typo in a food name), and only then tell
  them in one plain sentence what's wrong.
