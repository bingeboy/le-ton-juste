# Alembic FX-1 Tube Preamp

## Overview

The Alembic FX-1 is a single-channel tube preamp in a 1U rack format, descended from the F-2B (which Jerry Garcia used in the early 1970s). It's essentially a Fender Showman/Dual Showman preamp circuit repackaged by Alembic (Ron Wickersham) in a hi-fi rack format.

## Lineage: F-2B → F-1X → FX-1

- **F-2B (1970s):** Jerry's preamp. 1U, dual-channel (2 independent channels), dual 12AX7, Bright switch per channel, XLR + 1/4" outputs. Fender Showman topology.
- **F-1X:** Successor to F-2B, added footswitchable channel select.
- **FX-1:** Modern version with additional features.

## Role in the Rig

The Alembic is **the amp** — all tone shaping happens here. The McIntosh MC100 is a transparent power amplifier that adds no coloration. This mirrors Jerry's approach: the F-2B provided Fender-style tube warmth and EQ, and the MC2300 just made it louder.

## Tube Selection

See [tubes.md](../tubes.md) for current tube inventory and recommendations.

Key tube: **NOS GE 5751 5 Star Gray Plate 3 Mica** — lower gain than a 12AX7 (gain factor ~70 vs 100), smoother, more articulate. The classic "baller" tube for Jerry tones.

## EQ Approach for Jerry Tone

Based on research into the F-2B/F-1X topology and the Garcia/Weir clean tone:

- **Bass:** Moderate boost. Single-coil pickups (or the Jerry tone profile) need low-end reinforcement for clean sustain. The JBL E120s add tight low end.
- **Midrange:** Slightly scooped. The Fender preamp inherits a natural mid-scoop. JBL aluminum domes add midrange back in a different frequency band.
- **Treble:** Fairly high, with the Bright switch engaged. Jerry's tone had clear, articulate sparkle — partially from the F-2B's bright cap, partially from the aluminum-dome JBLs.
- **Gain:** Always clean. The Alembic should be run at edge-of-breakup at most. Jerry never intentionally overdriven his preamp. Dirt comes from pedal gain staging, tube warmth from the preamp running clean.

## Connections

- **Input:** 1/4" instrument level (from pedalboard)
- **Output:** 1/4" line level (to QuadraVerb / effects rack)
- **Effects loop:** If available, useful for inserting the QuadraVerb post-EQ
- **Footswitch:** Channel select / bypass

## Gain Staging with the MC100

- MC100 Input Sensitivity: ~0.75V for rated output
- The Alembic's output should be set to drive this cleanly
- Never intentionally overdrive any stage
- The power amp's autoformer ensures consistent frequency response regardless of load
