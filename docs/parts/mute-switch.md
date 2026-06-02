# Mute Switch — Tuner Routing

## Purpose

A footswitch that mutes the signal path to the amp while routing to a rack tuner. Allows silent tuning between songs or during sets.

## Requirements

- One stomp: mute signal to amp, route to tuner
- Second stomp: unmute (return to normal signal path)
- Passive or active? Passive is simpler (no power needed). Active ensures no signal degradation.
- LED indicator for mute status (if powered)

## Placement in Signal Chain

The mute switch should be placed **before the amp** but **after the preamp and effects rack** so you can tune with effects on if desired. Alternatively, place it **right after the pedalboard** so the tuner sees a clean, unaffected signal.

### Option A: Post-Pedalboard (Recommended for Tuner Accuracy)

```
Pedalboard → Mute Switch → Preamp/Rack
                    ↓
                Rack Tuner
```

- Tuner sees clean guitar signal (most accurate)
- Muting here kills everything downstream (silent to amp)
- Place mute switch last on pedalboard or first in rack chain

### Option B: Post-Rack (For Tuning with Effects Reference)

```
Rack Output → Mute Switch → Power Amp
                    ↓
                Rack Tuner
```

- You hear effects when tuning (can be distracting)
- Simpler wiring

**Recommendation: Option A.** The tuner gets the cleanest signal from post-pedalboard.

## Circuit Design

### Passive A/B/Y Mute

A simple DPDT footswitch (or 3PDT for LED):

```
                            DPDT Switch
Input ────┬──────────────────────┐
          │                      │
          │  Normal position:    │  Mute position:
          │  In → Out            │  In → Tuner
          │  Tuner = disconnected│  Out = disconnected (muted)
          │                      │
          ├── COM1               ├── COM2
          │   NO1 → Output        │   NO2 → Tuner Out
          │   NC1 → (unused)      │   NC2 → (unused)

Need a way to mute the output when in tuner mode.
Better approach: DPDT

COM1: Input tip
NO1: Output tip (normal mode)
NC1: Tuner tip (mute mode)

COM2: (tied to ground)
NO2: Output sleeve (connected in normal mode)
NC2: (disconnected in mute mode → mutes output)

This grounds the output in tuner mode = silent amp.
```

### Active Mute with LED (3PDT)

For an LED indicator, use a 3PDT switch or a relay-based mute circuit:

```
                         3PDT Switch
Input ──────┬──────────────┬──────────────┐
            │              │              │
            │  Pole 1:     │  Pole 2:     │  Pole 3:
            │  Signal      │  Ground      │  LED
            │              │              │
            ├── COM1       ├── COM2       ├── COM3
            │   NO1 → Out  │   NO2 → GND  │   NO3 → LED+ 9V
            │   NC1 → Tun  │   NC2 → Out  │   NC3 → (no connect)
            │              │   sleeve     │
```

When switched to Mute:
- Pole 1: Input routes to Tuner (not Output)
- Pole 2: Output sleeve is disconnected from ground → mutes
- Pole 3: LED connects to 9V → lights up

When switched to Normal:
- Pole 1: Input routes to Output
- Pole 2: Output sleeve is grounded
- Pole 3: LED disconnected → off

### Passive Option (No LED, No Power)

A simple DPDT stomp switch in a small enclosure (1590A or 1590B):

```
Input Tip ───── COM1 ┬─ NO1 → Output Tip (normal)
                     └─ NC1 → Tuner Input (mute)

Input Sleeve ─── directly connected to Output Sleeve and Tuner Sleeve (common ground)
Output Tip in mute position: disconnected = silent
```

This is the simplest possible implementation — one switch, three jacks, a small enclosure. No power, no LED. Works perfectly for tuning.

## Parts List (Passive)

| Item | Qty | Notes |
|---|---|---|
| Enclosure (1590A or 1590B) | 1 | Small aluminum box |
| DPDT footswitch (Carling, Alpha) | 1 | Heavy-duty stomp switch |
| 1/4" TS jacks (Switchcraft #11) | 3 | In, Out, Tuner |
| Hookup wire | — | Short lengths |
| Rubber feet (optional) | 4 | For standalone use |

## Wiring Diagram

```
                    ┌──────────────────────┐
                    │     DPDT Switch       │
                    │                       │
    Input Jack ─────┤ COM1    COM2 ├────────── Tuner Jack
                    │  │        │  │
    Output Jack ────┤ NO1      NC2 ├───── (unconnected)
                    │                       │
                    │  NC1 = (no connect)   │
                    │  NO2 = GND (from Input│
                    │        sleeve)        │
                    │                       │
                    │  All sleeves tied     │
                    │  together (common GND)│
                    └──────────────────────┘
```
