# Guitar Setup Project — AGENTS.md

## Project Overview

Reference and design tool for a clean, hi-fi Jerry Garcia / Bob Weir guitar signal chain. Tracks full rack, pedalboard, speaker setup, and DIY builds.

## Conventions

### Package Management

- Use `n-get` for any npm package installations. Never use `curl`, `wget`, or direct `npm install -g` for tools that can be installed via `n-get`.
- For non-npm tools (brew, choco, etc.), use the platform-native package manager.

### Documentation

- All docs live under `docs/` organized by topic (`signal-chain/`, `reverb-tank/`, `parts/`, `research/`).
- `chain.md` in root contains the mermaid signal chain diagram.
- Keep files concise. No fluff. Reference-oriented, not tutorial.
- Use markdown tables for specs and comparisons.
- Use mermaid for diagrams.

### Git

- Commit frequently with clear, descriptive messages.
- No large binary files — PDFs in `manuals/` and `parts/` are exceptions.
- Never commit secrets, API keys, or personal info.

#### Branching (hard rules)

- **Never commit to `master` directly.** All work happens on feature branches.
- Branch naming: `feature/<short-desc>` or `fix/<short-desc>`.
- Push the branch, open a Pull Request on GitHub, merge via the GitHub UI.
- `master` has classic branch protection enabled — direct pushes are rejected.
- After merging a PR, delete the feature branch (both local and remote).
- Keep `master` clean and deployable at all times.

### Signal Chain Philosophy

- Clean headroom is everything. Power amp never clips.
- The preamp (Alembic FX-1) is the "amp" — all tone shaping happens there.
- Time-based effects after preamp. Reverb last before power amp.
- JBL E120s are the voice — aluminum dome, hi-fi response.
- OBEL (On-Board Effects Loop) is the goal — pedal form for now, built-in later.

### Key Gear

| Component | Device |
|---|---|
| Preamp | Alembic FX-1 (tube, Fender Showman topology) |
| Power Amp | McIntosh MC100 (100W solid state mono, autoformer output) |
| Speakers | 2x JBL E120-8 (parallel → 4Ω load) |
| Boost | IO Thick Air (dual JFET clean boost) |
| Distortion | IO Old Dirt |
| Multi-FX | Alesis QuadraVerb |
| Reverb | Custom spring reverb tank (in design, rackmount, low-Z buffer) |
