# On-Board Effects Loop (OBEL) — Technical Deep Dive

## What It Is

The OBEL is an active buffer + effects loop built directly into the guitar, developed by Alembic (Ron Wickersham) and installed in Jerry Garcia's custom Doug Irwin guitars (Wolf, Tiger, Rosebud).

## Signal Flow

```
Pickups (high-Z, passive)
    ↓
Onboard Buffer (unity-gain, high-Z in → low-Z out)
    ↓
OBEL Send (Tip of TRS jack)
    ↓
    →→→ Pedalboard Effects (wah, distortion, Mu-Tron, etc.) →→→
    ↓
OBEL Return (Ring of TRS jack)
    ↓
Master Volume Pot
    ↓
Output to Amp (low-Z, consistent regardless of volume knob position)
```

## Why It Was Revolutionary

### 1. Solves Cable Capacitance

A passive guitar pickup is high-impedance (~5k–15kΩ). Long cables create a low-pass filter with the pickup's inductance, rolling off treble. The longer the cable, the duller the tone. An OBEL buffer presents a high-impedance load to the pickups (preserving treble) and outputs a low-impedance signal to the cable (immune to capacitance).

### 2. Consistent Pickup Loading

True bypass pedals change the impedance the pickups see when engaged vs. bypassed. This causes subtle (or not-so-subtle) tone changes depending on which pedals are on. The OBEL buffer isolates the pickups — they always see the buffer's consistent input impedance.

### 3. Post-Effects Master Volume

In a standard guitar, the volume knob changes the signal level going INTO your effects. This means:
- Lower volume = less drive hitting your distortion pedal
- Envelope filter (Mu-Tron) trigger threshold changes
- Wah sweep character changes

With OBEL, volume is AFTER the effects loop. You can roll off for clean rhythm and crank for leads without changing how your pedals respond.

### 4. Effects Loop Bypass

The OBEL effects loop is bypassable — a switch on the guitar can route pickups directly to output, bypassing the entire effects loop and its buffer. This gives a direct-to-amp option for when you want maximum signal purity.

## Garcia's Implementation

Jerry's Wolf guitar had:
- Alembic Strat-o-blaster → refined buffer circuit (actually an Alembic preamp, not just a buffer)
- TRS output jack (Tip = OBEL Send, Ring = OBEL Return)
- Separate master volume knob
- 5-way pickup selector
- OBEL bypass switch

The real secret: It wasn't just a unity-gain buffer. It was an active preamp that shaped the tone before the signal ever left the guitar.

## Modern Pedal-Form Alternatives

Since a built-in OBEL requires guitar modification (routing, battery cavity, preamp PCB, stereo jack), pedal-form alternatives are practical:

### Waldo OBEL Buffer
- Dedicated Jerry-style buffer + loop + master volume pedal
- Most faithful pedal-form replica
- Built to order by Matt Waldo

### Sarno FreeLoader
- Variable-impedance buffer (33k–1MΩ)
- Optimizes pickup loading — you can "tune" the loading to find the pickup's sweet spot
- No effects loop, no master volume — just the buffer
- Often paired with a looper pedal (BOSS LS-2, Lehle, etc.)

### DIY JFET Buffer + TRS Insert
- Simple JFET buffer (2N5457, J201, or MPF102) in a small enclosure
- TRS insert jack creates the send/return
- Add a volume pot after the return
- Can replicate the full OBEL functionality for ~$30 in parts

## Recommended Path for This Rig

1. **Now:** IO Thick Air stage 1 as buffer (first in chain, min gain). Handles cable capacitance.
2. **Soon:** Waldo OBEL Buffer or DIY JFET OBEL pedal. Full loop + post-effects master volume.
3. **Later:** Guitar with built-in OBEL. The pedal OBEL becomes a backup or is repurposed.

The pedal-form approach gets you 90% of the OBEL benefit without modifying your guitar.
