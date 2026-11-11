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
  missing). They need no API keys and send nothing anywhere.

## First time only: their brand

Macro cards, recipe books and grocery lists carry the coach's own brand. Before the first `macros` or `meals` job, run
`python3 tools/profile.py show`. If `set_up` is false, ask these, one at a time:

1. "What's your coaching business called?" (goes on every card)
2. "Your Instagram handle?" (optional)
3. "Got a logo? Drag the file in, or say skip." (optional)
4. "Kilos and centimetres, or pounds and feet?"

Then save it: `python3 tools/profile.py set --business "..." --handle "..." --logo "/path" --units metric|imperial`.
Never ask again unless they want to change it ("change my logo" → run `set` with just that).

## Where results go

Everything lands in `Documents/Coach Skills/`, one folder per client (or `Clean audio` and `Anatomy` when no client is named).
Nothing they gave you is ever changed or moved.

## If something breaks

- `NO BROWSER`: the cards are drawn by Google Chrome. Ask them to install Chrome (free, google.com/chrome), then run it again.
- `python3` not found: on a Mac, run `xcode-select --install` once (it's Apple's free installer and asks them to click Install);
  on Windows, install Python from python.org and tick "Add to PATH".
- Anything else: read the last lines of the error, fix what you can (a wrong path, a typo in a food name), and only then tell
  them in one plain sentence what's wrong.
