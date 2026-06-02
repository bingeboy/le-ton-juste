# Guitar Setup — Hi-Fi Jerry Garcia / Bob Weir Tone Rig

Reference and design tool for a clean, hi-fi guitar signal chain inspired by Jerry Garcia and Bob Weir's early-70s tone. Tracks the full rack, pedalboard, speaker setup, and DIY builds (reverb tank, A/B switches, mute/tuner routing).

**Goal:** Recreate the glassy, articulate, distortion-free tone Garcia achieved with the Alembic + McIntosh + JBL rig, using modern and period-correct gear.

## Current Gear

| Component | Device | Role |
|---|---|---|
| Preamp | Alembic FX-1 | Tube preamp (Fender-derived topology) |
| Power Amp | McIntosh MC100 | 100W solid-state mono, autoformer output |
| Speakers | 2x JBL E120-8 (parallel) | 8Ω each → 4Ω load on MC100 4Ω tap |
| Boost | IO Thick Air | Dual JFET clean boost / tone enhancer |
| Distortion | IO Old Dirt | Distortion pedal |
| Multi-FX | Alesis QuadraVerb | Rack reverb/delay/modulation |
| Reverb | Custom spring reverb tank | In design — rackmount, low-Z output buffer |
| Tuner | Sabine RT-1601 | 1U rackmount chromatic tuner, passive mute-switch split |

## Documentation Structure

```
chain.md                   # Mermaid signal chain diagram + explanation
docs/
  signal-chain/            # Deep dives into each link in the chain
    overview.md            # Full chain philosophy & gain staging
    guitar-and-obel.md     # OBEL concept, pedal-form options, future guitar wiring
    pedals.md              # IO Thick Air, Old Dirt
    preamp.md              # Alembic FX-1 tube preamp
    effects-rack.md        # QuadraVerb + reverb tank integration
    power-amp.md           # McIntosh MC100 specs & operation
    speakers.md            # JBL E120-8 wiring & impedance
  reverb-tank/             # Custom spring reverb tank design
    design.md              # Architecture & design choices
    parts-list.md          # Bill of materials
    buffer-circuit.md      # Low-impedance output buffer circuit
    enclosure.md           # Rackmount enclosure specs
  parts/                   # DIY builds
    mute-switch.md         # Mute/tuner routing switch
    pedalboard.md          # Pedalboard layout & power
    cables.md              # Cable types, lengths, connectors
  research/                # Historical tone research
    jerry-tone.md          # Jerry Garcia's 1970s signal chain
    bob-weir-tone.md       # Bob Weir's approach & differences
    obel.md                # On-Board Effects Loop explained
  tubes.md                 # Tube selection for Alembic FX-1
  references.md            # External links & resources
manuals/                   # Equipment manuals (PDFs)
parts/                     # Parts spec sheets (PDFs)
```

## Tone Philosophy

- **Clean headroom is everything.** The power amp should never clip — all tone shaping happens at the preamp and pedals, inspired by the "Wall of Sound" hi-fi approach.
- **The preamp is the amp.** The Alembic FX-1 provides the Fender-style tube warmth. The McIntosh MC100 is a transparent, high-headroom amplifier — it should add nothing but volume.
- **Time-based effects come after the preamp.** Reverb and delay sit between preamp and power amp (or in the preamp's effects loop), preserving transient clarity.
- **JBLs are the voice.** The aluminum-dome E120s provide extended high-frequency response and speaker breakup characteristics essential to the Jerry/Bob sound.
