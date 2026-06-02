# Cables — Types, Lengths & Connectors

## Cable Philosophy

In a hi-fi rig, cables matter. High-quality, low-capacitance cable preserves the treble extension that defines the Jerry/Bob clean tone. Poor cables work against everything the OBEL buffer and Thick Air are trying to achieve.

## Recommended Cable Types

### Instrument / Pedalboard

| Cable | Type | Capacitance | Notes |
|---|---|---|---|
| **Canare GS-6** | Coaxial, 18 AWG | ~49 pF/ft | Industry standard. Thick conductor, durable, excellent shielding. |
| **Mogami 2524** | Coaxial, 20 AWG | ~43 pF/ft | Slightly lower capacitance than GS-6. More flexible. |
| **Mogami 2314** | Coaxial, 25 AWG | ~67 pF/ft | Thinner, good for tight pedalboard patch cables. |
| **Belden 8412** | Twisted pair w/shield | ~58 pF/ft | Studio standard. Two conductors + shield. Can be wired unbalanced. |

### Speaker Cable

| Cable | Type | Notes |
|---|---|---|
| **Canare 4S11** | 4-conductor, 14 AWG star quad | Current standard for our rig. R+W = 1+, B+Black = 1−. |
| **Mogami 3103** | 2-conductor, 12 AWG | Excellent speaker cable. Heavier gauge than 4S11. |
| **Belden 1313A** | 2-conductor, 12 AWG | Pro audio standard for speaker runs. |

**Important:** Never use instrument cable as speaker cable. Instrument cable is coaxial and can't handle the current. Speaker cable is unshielded, low-resistance, and rated for the power.

### Rack Interconnects

Use the same GS-6 or Mogami 2524 as instrument cable for short rack-to-rack connections. If runs exceed 15ft, consider balanced cables (if the gear supports it).

## Connectors

| Connector | Brand | Model | Notes |
|---|---|---|---|
| 1/4" TS (straight) | Switchcraft | 280 | Mono. Standard for guitar/pedals. |
| 1/4" TS (right angle) | Switchcraft | 226 | For tight pedalboard spaces. |
| 1/4" TS (straight) | Neutrik/Rean | NYS224 | Good budget option. |
| RCA | Switchcraft | 3502A | For MC100 input. Gold-plated preferred. |
| Speakon NL4FC/FX | Neutrik | NL4FC / NL4FX | Locking speaker connector. 4-pole. |
| XLR (if needed) | Neutrik | NC3MX / NC3FX | For balanced connections (Alembic XLR out, etc.). |

## Current Cable Inventory

### Instrument / Line Level

| Run | Length | Cable | Connector | Notes |
|---|---|---|---|---|
| Guitar → Pedalboard | 15ft | GS-6 | SP600 both ends | Guitar to Thick Air input |
| Pedalboard patch | 6"–12" | GS-6 patch | SP600 both ends | Thick Air → Dirt |
| Pedalboard → Rack | 8ft | GS-6 | SP600 → SW280 | Dirt → Alembic FX-1 |
| Rack interconnect | ~3ft | GS-6 | 1/4" TS both ends | FX-1 → QuadraVerb → Reverb |
| Reverb → MC100 | ~3ft | GS-6 | 1/4" TS → RCA | Reverb tank out → MC100 in |

### Speaker

| Run | Length | Cable | Connector | Notes |
|---|---|---|---|---|
| MC100 → Cabinet | TBD | Canare 4S11 | Spades → NL4FC | R+W=1+, B+Black=1− |
| Internal cabinet | Short | 14 AWG stranded | — | E120 #1 parallel to E120 #2 |

## Cable Length Guidelines

- **Guitar to first buffer:** ≤15ft. Longer = more treble loss before the buffer. If the first pedal is the Thick Air (always on), 15ft is fine.
- **Patch cables between pedals:** As short as practical. 6"–12" typical.
- **Pedalboard to rack:** Up to 25ft (buffered signal from Thick Air / OBEL). Unbuffered would be ≤15ft.
- **Rack interconnects:** ≤3ft. Keep the rack tight.
- **Speaker cable:** Can be any practical length. Use heavy gauge (12–14 AWG) for runs over 20ft.
- **Reverb tank send/return (if external):** Short RCA cables. Long runs pick up hum.

## DIY Cable Assembly

Building your own cables with bulk cable and solder connectors is:
- Cheaper per cable than buying pre-made
- Customizable to exact lengths
- More durable if soldered properly (no molded strain reliefs to fail)

### Soldering 1/4" TS (Switchcraft 280)

```
Center conductor → Tip lug
Shield/braid → Sleeve lug
No connection → (nothing — this is a mono/TS connector)
```

### Soldering RCA (Switchcraft 3502A)

```
Center conductor → Center pin
Shield/braid → Outer shell tab
```

### Wiring Canare 4S11 to Speakon NL4FC

```
Red conductor → 1+ terminal
White conductor → 1+ terminal
Black conductor → 1− terminal
Blue conductor → 1− terminal

Pin 1+ = Hot (speaker +)
Pin 1− = Cold (speaker −)
Pins 2+/2− = unused
```
