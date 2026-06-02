# Guitar & On-Board Effects Loop (OBEL)

## The OBEL Concept

The On-Board Effects Loop is a buffer + effects loop built **into the guitar** (or as a pedal) that sits between the pickups and the output jack. Jerry Garcia's custom guitars (Wolf, Tiger, Rosebud) all had OBEL circuits.

### Signal Flow

```
Pickups → Buffer (unity-gain preamp) → Effects Send → [pedalboard] → Effects Return → Master Volume → Output Jack → Amp
```

### What It Solves

1. **Cable capacitance.** A passive guitar signal loses treble over long cable runs. A buffer right at the guitar preserves high-end regardless of cable length.
2. **Consistent pickup loading.** Pedals turning on/off change the impedance the pickups see. The buffer isolates pickups from everything downstream.
3. **Master volume after effects.** The guitar's volume knob in traditional wiring changes how hard you hit your pedals. With OBEL, the volume is *after* the effects loop, so pedal gain character stays consistent — only overall level changes.

### Jerry's Usage

```
Guitar OBEL Send → Wah → Distortion → Envelope Filter → OBEL Return → Master Volume → Preamp
```

The OBEL let Jerry sweep his wah or engage the Mu-Tron without his guitar's volume knob messing with the envelope trigger threshold.

## Pedal-Form OBEL Options

Since a guitar with built-in OBEL is a future project, these pedal-form alternatives replicate the same behavior on your pedalboard:

| Product | Type | Notes |
|---|---|---|
| **Waldo OBEL Buffer** | Dedicated Jerry-style buffer + loop + master volume | Closest pedal-form replica. Built by Matt Waldo, well-regarded in the Deadhead community. |
| **IO Thick Air (stage 1)** | JFET buffer / clean boost | Already owned. At minimum gain, stage 1 is an effective buffer. Not a full OBEL (no loop, no post-loop volume). |
| **Sarno FreeLoader** | Variable-impedance buffer | Optimizes pickup loading. No effects loop. Pairs well with a separate looper pedal. |
| **BOSS LS-2** | Line selector / loop switcher | Budget option. Can create a buffered effects loop. |
| **RJM Mini Line Mixer** | Buffered loop with blend | Pro-grade routing. Overkill for simple OBEL, but flexible. |
| **DIY JFET buffer** | Custom build | A simple 2N5457 or J201 buffer with a TRS insert cable. Inexpensive and effective. |

### Recommended Approach

**Short term:** Use the IO Thick Air stage 1 as your buffer (first in chain, always on at minimum gain). This handles cable capacitance but doesn't give you the post-effects master volume.

**Medium term:** Add a Waldo OBEL Buffer or build a DIY JFET buffer with a send/return loop. Place all your pedals (Thick Air, Dirt, etc.) in its loop, use its return-level volume as your master volume.

**Long term:** When you get/mod a guitar for built-in OBEL, the pedal-form OBEL becomes redundant and can be repurposed or removed.

## Future Guitar OBEL Wiring

A built-in OBEL requires:
- A small onboard buffer preamp (JFET or op-amp based, 9V battery powered)
- A stereo (TRS) output jack: Tip = OBEL Send, Ring = OBEL Return
- A TRS insert cable to a breakout box on the pedalboard
- A separate master volume pot on the guitar

This is the "real deal" and was how Wolf/Tiger/Rosebud were wired.
