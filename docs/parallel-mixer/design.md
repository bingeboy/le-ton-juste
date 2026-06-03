# Parallel Loop — Lehle Parallel M

## Decision
The parallel mixer for this rig is the **Lehle Parallel M** — a commercial single-loop unit. A DIY 3-channel summing mixer was originally specced but was correctly identified as over-engineered. The only signal path that genuinely benefits from parallel treatment is the QuadraVerb (digital A/D conversion). The Ghost Spring is fully analog with its own Mix pot and stays in series.

**Buy used: ~$180 on Reverb.com or Music Go Round.**

---

## Why the Lehle Parallel M

- Single parallel loop — exactly what's needed for the QuadraVerb
- Phase correction built in (DPDT switch, no guessing)
- Transformer-isolated loop return — prevents ground loops between the QuadraVerb and the main signal path
- ±15V internal supply, extremely transparent
- No build required — plug in and it works

---

## Signal Chain Placement

```
Alembic FX-1 → Lehle Parallel M → Ghost Spring → McIntosh MC100
                      ↕
               [QuadraVerb loop]
```

The Lehle sits between the Alembic output and the Ghost Spring input. The Ghost Spring stays in series after the Lehle — reverb is always the last thing added before the power amp, same as Jerry's Fender Reverb Unit placement.

---

## Setup

1. **Connect:** Alembic FX-1 output → Lehle input. Lehle output → Ghost Spring input.
2. **Loop:** Lehle Send → QuadraVerb input. QuadraVerb output → Lehle Return.
3. **QuadraVerb:** Set to **100% Wet / Kill Dry**. If the QuadraVerb outputs any dry signal, it will phase-combine with the Lehle's own dry path and cause comb filtering (hollow, scooped sound).
4. **Phase switch:** Blend the QuadraVerb in with the Level knob. If the tone sounds thin or loses low end, flip the Phase switch. The correct position is the one that sounds fuller.
5. **Level knob:** Sets how much of the QuadraVerb wet signal blends into the dry path. Start at ~30% and adjust to taste.

---

## Adding Experimental Pedals

If a Rainbow Machine, POG, or similar experimental pedal is ever used post-preamp, route it in series within the Lehle loop:

```
Lehle Send → [A/B switch] → QuadraVerb OR Rainbow Machine → Lehle Return
```

An A/B switcher (e.g. Radial BigShot ABY or similar passive unit) before the Lehle Send selects which effect is active. Since these are never used simultaneously, one shared loop is sufficient.
