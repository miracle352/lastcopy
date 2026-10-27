# LastCopy submission files

Use [SUBMIT_TOMORROW.md](SUBMIT_TOMORROW.md) for the form: track, description, video, GitHub link, deck and sponsor explanation.

**Video to upload: `LastCopy-demo.mp4`** (2:31, 1920×1080, 30 fps, narrated, with captions; `LastCopy-demo.srt` holds the same captions).

**Concept: a countdown to the reset.** A live "factory reset in 2:30" clock runs through the whole film while LastCopy races it. Five tablets float in 3D and are x-rayed to show what is still only on them. The camera flies across real screenshots of the live product (captured at 2× from lastcopy-five.vercel.app/demo, live run of 27 Oct 2026) and spotlights each element as it is narrated: the World Model plan, the Reviewer's three send-backs, the seven-point evidence checks, and Nemotron's five live objections with the code's answers. The proof scene shows real `verify_certificate` output (16/16). The blind-test numbers come from `eval/blind-benchmark.json`. At 0:00, tablet-01 is reset with nothing lost and the other four are blocked.

Rendering: a GSAP timeline stepped frame by frame in headless Chromium, timed to the narration's word timestamps (Kokoro TTS, open-weight). The soundtrack (drone, countdown ticks, impacts) is synthesized with NumPy. No AI-generated imagery. Source: `submission/video/`.

`LastCopy-demo-narrated.mp4`, `LastCopy-submission-deck.pptx` and the files that go with them show earlier versions of the product. Keep them for history only.
