# Alesis QuadraVerb — Configuration & Role

## Current Role: Delay + Modulation Only

With the Ghost Spring reverb tank handling all reverb duties, the QuadraVerb's reverb programs are retired. It now serves exclusively as a delay and modulation processor. All patches should be configured with 100% wet output — the dry signal is passed through the unit unprocessed by the bypass, and wet/dry blend is handled downstream.

---

## Known Signal Chain Weakness

The QuadraVerb is currently placed **in series** in the main signal path. This means the dry guitar signal passes through the unit's 16-bit A/D and D/A converters even when the effect level is low — a compromise for a hi-fi analog rig.

**Long-term fix:** The parallel mixer (`docs/signal-chain/parallel-mixer.md`) routes the QuadraVerb in a parallel loop so the dry signal never touches digital conversion. This is the priority next build after the reverb tank is complete.

---

## Recommended Patch Types

### 1. Slapback Delay — Rhythm / Rockabilly Attack
Used subtly under chord playing. Adds body without smearing the attack.

| Parameter | Setting |
|---|---|
| Delay time | 80–120ms |
| Feedback | 0 (single repeat only) |
| Mix (wet level) | 15–25% |
| EQ | Slight high-shelf cut on wet — keeps repeats from fighting the dry signal |

### 2. Tap-Tempo Delay — Lead / Melodic Lines
Quarter-note delay locked to tempo. Classic Jerry melodic playing delay.

| Parameter | Setting |
|---|---|
| Delay time | 300–500ms (quarter note at 120–200 BPM) |
| Feedback | 1–2 repeats |
| Mix (wet level) | 20–35% |
| EQ | Flat or slight treble cut on repeats |

### 3. Chorus — Weir Shimmer / Chord Texture
Subtle stereo-width effect for rhythm guitar. Use sparingly — the Alembic FX-1 already has inherent warmth that competes with heavy modulation.

| Parameter | Setting |
|---|---|
| Rate | Slow (0.3–0.8 Hz) |
| Depth | Light (20–40%) |
| Mix | 30–50% |
| Type | Stereo chorus preferred over flanger — less phasy, more natural |

### 4. Flanger — Weir "Shimmer" Specific Effect
For intentional modulation texture, not a always-on tone. Used on specific passages.

| Parameter | Setting |
|---|---|
| Rate | Very slow (0.1–0.3 Hz) |
| Depth | Light–medium |
| Feedback | Low (under 30%) — prevents the metallic sound |
| Mix | 40–60% |

---

## General Settings Notes

- **Kill dry on all patches** — set the QuadraVerb to 100% wet. The dry signal passes through regardless; adding dry from the unit creates comb filtering against the main dry path.
- **No reverb programs** — delete or ignore all reverb patches. The Ghost Spring handles reverb exclusively.
- **Input level** — set the QuadraVerb input trim so the signal peaks at around −6dBFS on the QuadraVerb's input meter. Hot input = digital clipping in the A/D stage, which is irreversible and sounds bad.
