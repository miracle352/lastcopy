# Optional low-memory text model

SmolLM2-360M-Instruct, quantized Q4_K_M. Text only; no imagery engine.

- Original: https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct
- GGUF publisher: https://huggingface.co/bartowski/SmolLM2-360M-Instruct-GGUF
- Pinned repository revision: `7be6f65f1db715fe5dc5a4634c0d459b4eed42ec`
- File: `SmolLM2-360M-Instruct-Q4_K_M.gguf`
- SHA-256: `2fa3f013dcdd7b99f9b237717fa0b12d75bbb89984cc1274be1471a465bac9c2`
- Published bytes: 270590880. License: Apache-2.0, per publisher metadata.

Weights are optional, downloaded separately, ignored and not redistributed.
`setup_nightshift_small_text.mjs` checks exact bytes/hash and existing local
Nightshift identity before copying into its model directory. It creates only
`lastcopy-small-text`, a CPU text lane on port 11502, preserving the existing 1B
lane and runtime memory safeguards. `active_gb` is a configuration estimate,
not a measured benchmark. Starting a lane does not prove inference. Record the
actual serving identity from each response. This small model has limited general
reasoning capability; code validates all actions and computes preservation.
Neither SmolLM nor Llama qualifies the NVIDIA Nemotron award path.

After downloading and verifying the pinned file:

```powershell
$env:LOCALAPPDATA=Join-Path $env:USERPROFILE 'AppData\Local'
node scripts/setup_nightshift_small_text.mjs private/stage3/SmolLM2-360M-Instruct-Q4_K_M.gguf
```

Setup uses the observed control contract of the installed Nightshift 1.2.3 with
strict version/ownership checks, not an invented or spec-only administration API.
