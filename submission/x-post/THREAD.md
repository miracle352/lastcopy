# X thread: LastCopy launch

Attach `LastCopy-x-motion.mp4` (50 s, 4:5) to post 1. Every post is under 280 characters.

---

**1/**
Every survey round ends the same way: someone resets the tablets.

The server says everything arrived. But "received" isn't "complete". A record can arrive without its photo.

Wipe that tablet and the only copy is gone. So I built LastCopy 🧵

**2/**
ODK runs on 2M+ people's phones and tablets, 250M+ submissions a year in 194 countries, including WHO polio and cholera surveillance.

Before every reset, a coordinator has to guess which devices still hold the only copy of something. Nobody checks by hand.

**3/**
LastCopy asks one question per tablet: is this the last copy?

It answers with exactly one of:
🟢 SAFE TO WIPE
🟡 RECOVER FIRST (names the exact record or photo)
🔴 HOLD (a person must look)

Never a guess.

**4/**
How it finds out:

• Zetaris SQL joins tablet exports, the server and the spreadsheet in place
• NVIDIA Nemotron investigates, and a Reviewer pushes back on weak hypotheses
• A Meterless World Model plans every next step
• Code compares the original bytes

**5/**
The rule I cared about most: models never decide.

Agents decide where to look. Code decides what's true. The wipe gate is a fixed rule that no prompt can talk its way past.

**6/**
Then it attacks itself.

An Adversary agent tries to break every "safe to wipe" with five objections. Code has to answer each one from the raw bytes. One objection left open and the tablet is held.

**7/**
"Did you plant the answers?"

So I built blind tests: random fleets with hidden problems the agents never see. Truth revealed only after each decision.

500 / 500 fleets correct
1,980 / 1,980 tablets
0 wrongly cleared to wipe

**8/**
Every decision ships with a SHA-256 certificate anyone can re-check against the original archives, with no model and no LastCopy runtime.

Try it in 10 seconds, no keys:
`python run.py`

**9/**
Built for the Open Agent Hackathon 2026.

Site: https://lastcopy-five.vercel.app
Code: https://github.com/miracle352/lastcopy

If you run field data collection, I'd love to hear how you decide when a device is safe to wipe.

---

## Single-post version (if you'd rather not thread)

Field teams wipe tablets between survey rounds. "Received" isn't "complete": a record can arrive without its photo.

LastCopy tells you, per tablet: safe to wipe, recover first, or hold. Agents investigate, code proves it byte for byte.

500/500 blind fleets, 0 wrongly cleared.
https://lastcopy-five.vercel.app

---

## How the video was made

Made entirely in code, with no AI imagery and no stock footage. `source/film.html` is a GSAP kinetic-typography timeline. `source/render.cjs` steps it frame by frame in headless Chromium at 30 fps and pipes the frames to ffmpeg. `source/sound.py` synthesizes the soundtrack (pad, pulse and hits on the cuts) with NumPy. Fonts: Fraunces, Figtree and Geist Mono (OFL), the same as the site.
