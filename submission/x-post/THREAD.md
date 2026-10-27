# X thread: LastCopy launch

Attach `LastCopy-x-motion.mp4` to post 1. Every post is under 280 characters.

---

**1**

June 2024. A researcher posts on the ODK forum. A week of surveys, collected offline on four tablets. An app update logged them out before anything was uploaded.

Three tablets were rescued by hand. The fourth wasn't.

"I am sad to report that the data is in fact gone."

**2**

That's the moment I built LastCopy for.

Field teams reset their tablets between rounds. The server says everything was received. But "received" doesn't mean complete. A record can arrive without its photo, and nothing on the dashboard tells you.

**3**

LastCopy gives one answer per tablet before you wipe it: safe to wipe, recover first, or hold.

If it says recover first, it names the exact record or file that only exists on that device.

**4**

Agents decide where to look. Zetaris joins the tablet exports, the server and the spreadsheet in place. Nemotron forms hypotheses and a Reviewer sends weak ones back. A Meterless World Model plans each step.

Then code compares the original bytes. Models never decide.

**5**

Then it argues with itself. An Adversary tries to break every "safe to wipe" with five objections, and code has to answer each one from the raw bytes. If one stays open, the tablet is held.

**6**

I didn't want it to only pass its own demo, so I ran blind tests. 500 random fleets with hidden problems the agents never see.

1,980 tablets. Every one decided correctly. Zero wrongly cleared to wipe.

**7**

Every decision comes with a certificate you can re-check against the original files, without LastCopy and without a model.

Open source. Runs in 5 seconds with no keys.

lastcopy-five.vercel.app
github.com/miracle352/lastcopy

---

## Single post

Field teams wipe their tablets between survey rounds, trusting a server count. But "received" isn't complete. A record can arrive without its photo.

LastCopy tells you, tablet by tablet, whether it's safe to wipe. Agents investigate, and code proves it byte for byte.

lastcopy-five.vercel.app

---

## How the video was made

Made entirely in code, with no AI imagery and no stock footage. `source/film.html` is a GSAP kinetic-typography timeline. `source/render.cjs` steps it frame by frame in headless Chromium at 30 fps and pipes the frames to ffmpeg. `source/sound.py` synthesizes the soundtrack with NumPy. Fonts: Fraunces, Figtree and Geist Mono (OFL).
