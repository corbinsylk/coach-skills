# Coach skills

This repo holds one Claude Code skill, `/coach`, in `.claude/skills/coach/`. Its instructions are in that folder's `SKILL.md`.

## When the user asks to install it

(For example, "Install the coach skills from github.com/corbinsylk/coach-skills".) Do this without explaining the steps:

1. Clone the repo into a temporary folder: `git clone --depth 1 https://github.com/corbinsylk/coach-skills`. If git is
   missing, download https://github.com/corbinsylk/coach-skills/archive/refs/heads/main.zip and unzip it instead.
2. Copy its `.claude/skills/coach` folder to the user's personal skills folder, replacing any older copy:
   - Mac or Linux: `~/.claude/skills/coach`
   - Windows: `%USERPROFILE%\.claude\skills\coach`
   Keep their `Documents/Coach Skills` folder as it is: it holds their brand and their clients.
3. Check it's there (`SKILL.md` in the new folder) and check for Python 3 and Google Chrome. Tell them in plain words if
   either is missing, and how to get it (see "If something breaks" in `SKILL.md`).
4. **Connect Gemini. Never skip this step.** It draws new muscles for /coach anatomy and the food photos for /coach meals.
   Run `python3 tools/connect.py --status` from the installed folder's `tools`. If it says NOT CONNECTED, tell them:
   "Last step: connect Gemini. A page is opening in your browser. Follow its three steps and click Save." Then run
   `python3 tools/connect.py` in the background and wait for CONNECTED. Never ask them to paste the key into this chat; if they
   do, don't repeat it, and point them to the page instead.
5. Tell them: "Done. Type /coach to see the six tools. If it doesn't show, start a new chat."

An update is the same steps; the copy replaces the old one.

## When this folder itself is open

The skill already works here. If the user wants it in every folder, do the install above.
