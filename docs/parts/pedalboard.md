# Pedalboard Layout

## Current Pedals

| Pedal | Size | Power | Placement |
|---|---|---|---|
| IO Thick Air | Compact (approx. 4.7" × 3.7") | 9V DC, center-negative | First in chain, right side (closest to guitar input) |
| IO Old Dirt | TBD | 9V DC, center-negative | After Thick Air |

## Future Pedals

| Pedal | Size | Power | Placement |
|---|---|---|---|
| Waldo OBEL Buffer (or DIY) | Compact | 9V DC | First in chain (before everything) |
| Mute/Tuner Switch | Mini (1590A) | Passive (no power) | Last on board (splits to rack tuner) |
| Volume Pedal | Full size | Passive or active | In OBEL loop, after effects (master volume) |
| Wah Pedal | Full size | 9V DC or passive | In OBEL loop, first in effects |

## Layout (Plan)

```
                    ┌──────────────────────────────────────────┐
                    │              PEDALBOARD                   │
                    │                                           │
   Guitar In ───────┤                                           ├──── To Preamp
                    │                                           │
                    │  ┌─────────┐  ┌──────────┐  ┌─────────┐  │
                    │  │  OBEL   │  │  Thick   │  │   Old   │  │
                    │  │ Buffer  │──│   Air    │──│   Dirt  │  │
                    │  │ (future)│  │          │  │         │  │
                    │  └────┬────┘  └──────────┘  └────┬────┘  │
                    │       │                           │       │
                    │       │    ┌──────────┐          │       │
                    │       └────│   Wah    │──────────┘       │
                    │        ┌───│ (future) │───┐              │
                    │        │   └──────────┘   │              │
                    │        │                  │              │
                    │   ┌────┴────┐        ┌────┴────┐         │
                    │   │ Volume  │        │  Mute   ├── Tuner │
                    │   │ Pedal   │        │ Switch  │   Out   │
                    │   │(future) │        │         │         │
                    │   └─────────┘        └─────────┘         │
                    │                                           │
                    └──────────────────────────────────────────┘
```

## OBEL Loop Routing (Future)

When the OBEL buffer pedal is added:

```
Guitar → OBEL Buffer Input
           ↓
         OBEL Send ─→ Thick Air → Old Dirt → Wah → OBEL Return
                                                        ↓
                                                  Volume Pedal
                                                        ↓
                                                  Mute Switch
                                                        ↓
                                                     To Preamp
                                                        ↓
                                                   Rack Tuner
```

Without OBEL (current state):

```
Guitar → Thick Air → Old Dirt → Mute Switch → To Preamp
                                    ↓
                               Rack Tuner
```

## Power Supply

- All pedals currently 9V DC, center-negative (standard Boss-style)
- Waldo OBEL Buffer also 9V DC
- Recommended power supply: isolated outputs to prevent ground loops
  - **Cioks DC7** — compact, 7 isolated outputs, fits under most boards
  - **Strymon Zuma** — 9 outputs, dead quiet
  - **Truetone CS6** — 6 outputs, good value
  - **Voodoo Lab Pedal Power 2 Plus** — industry standard

## Board Platform

- **Pedaltrain** — aluminum slat design, comes with soft/hard case
  - PT-JR or PT-1 would fit this setup with room for expansion
- **Temple Audio** — perforated mounting plate, more customizable
- **DIY** — plywood + Velcro, custom size

## Cabling

All pedal interconnects: **Mogami 2314** or **Canare GS-6** with **Neutrik/Rean** or **Switchcraft** connectors. See [cables.md](cables.md) for full specs.

Keep patch cables as short as possible between pedals to minimize capacitance. Guitar-to-board cable should be 15ft max. Board-to-rack cable can be up to 25ft if buffered (which it is, via the Thick Air or OBEL buffer).
