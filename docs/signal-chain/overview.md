# Signal Chain Overview

## Full Chain (Current)

```
Guitar → IO Thick Air → IO Old Dirt → Alembic FX-1 → Alesis QuadraVerb → Custom Reverb Tank → McIntosh MC100 → 2x JBL E120-8 (parallel, 4Ω)
```

## Gain Staging Philosophy

This rig follows the "Wall of Sound" hi-fi approach: **every stage before the power amp shapes tone; the power amp adds only volume.** The McIntosh MC100 should never clip — all dynamics and dirt come from pedals and the Alembic's tube front-end.

### Stage-by-Stage Intent

| Stage | Device | Role | Input Level | Output Level |
|---|---|---|---|---|
| Buffer/Boost | IO Thick Air | Tone enhancer, always-on presence boost, optional solo lift | Instrument | Instrument/Low-Z |
| Dirt | IO Old Dirt | Overdrive/distortion when needed | Instrument | Instrument |
| Preamp | Alembic FX-1 | Tube EQ, Fender-style coloration, channel switching | Instrument | Line |
| Multi-FX | Alesis QuadraVerb | Reverbs, delays, modulation (post-preamp) | Line | Line |
| Reverb | Custom Spring Reverb | Analog spring reverb with low-Z buffer | Line | Line (low-Z) |
| Tuner | Sabine RT-1601 | Rack tuner on passive mute-switch split (not in signal path) | Split from pedalboard out | — |
| Power Amp | McIntosh MC100 | Clean, transparent amplification | Line (~0.75V) | Speaker (100W @ 8Ω) |
| Speakers | JBL E120-8 x2 | Extended hi-fi response, aluminum dome | Speaker | — |

### Why This Order

1. **Thick Air first** — Its JFET buffer combats cable capacitance. Even at minimum gain, it preserves treble and adds presence. Stage 2 acts as a lead boost.
2. **Dirt before preamp** — Overdrive hitting the Alembic's tube input gives the most natural, dynamic grit. The tube stage smooths the clipping.
3. **Time effects after preamp** — The QuadraVerb and reverb tank sit post-EQ so the preamp doesn't color the reverb tails. This mirrors Jerry's placement of the Fender Reverb Unit between his F-2B and MC2300.
4. **Reverb last before power amp** — The custom spring reverb tank with low-impedance output buffer is the final device before the MC100. This ensures the reverb mix drives the power amp with consistent impedance regardless of wet/dry blend.
5. **Clean power** — The MC100 amplifies everything linearly. No power amp saturation. All tone is upstream.
