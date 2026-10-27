# LastCopy submission files

Use [SUBMIT_TOMORROW.md](SUBMIT_TOMORROW.md) for the form: track, description, video, GitHub link, deck and sponsor explanation.

**Video to upload: `LastCopy-demo.mp4`** (2:41, 1920×1080, 30 fps, narration and burned-in captions; `LastCopy-demo.srt` holds the same captions). Every scene is rendered in code: a GSAP timeline stepped frame by frame in headless Chromium, with real screens captured from the live site at 2× and figures taken from the live connected run (`output_examples/live_connected_fleet.json`). Narration: Kokoro TTS (open-weight, Apache-2.0). Soundtrack synthesized with NumPy. No AI-generated imagery.

| Time | Scene |
| --- | --- |
| 0:00–0:20 | Cold open: a real case from the public ODK forum (June 2024), a tablet of field data lost after an app update, quoted verbatim |
| 0:20–0:40 | The problem: "received" is not "complete" (missing photo, stuck record, spreadsheet false alarm) |
| 0:40–0:48 | LastCopy |
| 0:48–1:05 | Zetaris: four sources joined in place; the real missing-photo SQL and the 7 queries of the live run (12.1 s) |
| 1:05–1:22 | Real product screens of the live run: World Model plan (0 → 184 observations), Nemotron hypotheses, Reviewer sends 3 back |
| 1:22–1:32 | The verifier compares original bytes, record by record and photo by photo |
| 1:32–1:44 | Five tablets, five code-made decisions from the live run |
| 1:44–1:58 | Nemotron as Adversary: the five live objections, each answered by code from raw bytes |
| 1:58–2:07 | Certificate and the independent verifier output (16/16) |
| 2:07–2:23 | Blind tests: 500/500 fleets, 1,980 tablets, 0 wrongly cleared |
| 2:23–2:32 | What makes LastCopy different |
| 2:32–2:41 | Close: site, repo, built with Zetaris, Meterless and NVIDIA Nemotron |

The cold-open quote is verbatim from a public post on forum.getodk.org (thread 47711, June 2024). LastCopy's own figures all come from the live run and the blind benchmark in this repository.

Source for the film: `submission/video/` (film.html, render.cjs, mix.py, script.json).

`LastCopy-demo-narrated.mp4`, `LastCopy-submission-deck.pptx` and the files that go with them show earlier versions of the product. Keep them for history only.
