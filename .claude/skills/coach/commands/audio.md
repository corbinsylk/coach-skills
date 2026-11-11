# /coach audio

Cleans the voice on a video or voice note filmed in the gym: background noise, hum and crowd come down, the voice is brightened
and levelled, and the loudness is set for Instagram. The picture isn't touched. It also makes a before/after picture.

## What you need

A video or audio file. If they haven't given one: "Drag your clip in here." Never change or move their original.

Optional, only if they say so: a client name (the result goes in that client's folder), or how hard to clean:
- "light": keeps more of the room, for a fairly quiet gym
- "normal": the default
- "strong": for loud music. It can make the voice a little thinner.

## Run it

```
python3 tools/audio.py "/path/to/their clip.mp4" [--client "Name"] [--strength light|normal|strong]
```

The first run may print `FIRST RUN: installing a private copy of ffmpeg`. Tell them it's a one-time setup (about a minute).
After that a one-minute clip takes a few seconds.

## Hand it over

It prints the clean file, the before/after picture and the loudness.
- Video in → `<clip> - clean.mp4`. Same picture, new sound. They drop it straight into their editing app or post it.
- Audio in → `<clip> - clean.m4a`.
- `<clip> - before and after.png` shows the change. It's good for a story.

Say what changed in one line, using `noise_drop_db` if it is 3 or more ("noise between words down 21 dB").
If they say it sounds thin or underwater, run it again with `--strength light`. If music is still loud, use `--strength strong`.
The free version can't remove music that's as loud as the voice. Say so plainly if that's the case.
