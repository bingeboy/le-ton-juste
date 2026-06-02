# Effects Rack — QuadraVerb + Reverb Tank

## Alesis QuadraVerb

The QuadraVerb is a multi-effects processor that provides digital reverb, delay, chorus, flanger, pitch shift, and EQ. In the hi-fi Jerry context, it's used for:

- **Digital reverb** (halls, plates) as an alternative to the spring tank
- **Delay** (digital, tap tempo if available)
- **Modulation** (chorus, flanger) for Bob Weir-style shimmer

### Signal Chain Position

Between the Alembic FX-1 output and the custom reverb tank input. Time-based effects after the preamp keep the preamp's tube EQ from coloring the effect tails.

## Routing

**Series:** Preamp main output → QuadraVerb → Custom Reverb Tank → MC100.

The QuadraVerb takes the Alembic's main line-level output. It does not use the Alembic's effects loop (send/return). All time-based effects sit after the preamp's master output, keeping the chain linear and clean.

### QuadraVerb Setup for Clean Jerry Tone

- Keep reverb algorithms on "plate" or "hall" with moderate decay (1.5–2.5s)
- Delay: subtle slapback or clean digital delay mixed low
- EQ: flat or slight high-shelf boost to compensate for any top-end loss
- Avoid heavy modulation unless intentionally going for effect

---

## Custom Spring Reverb Tank (Overview)

The custom reverb tank sits **last before the McIntosh MC100**, matching Jerry Garcia's placement of the Fender Reverb Unit between his Alembic F-2B and MC2300.

### Why Post-Preamp

- The spring tank is driven by the already-EQ'd preamp signal
- Reverb tails aren't colored by subsequent gain stages
- The McIntosh amplifies the wet+dry mix linearly
- This is historically accurate to Jerry's chain

### Design Requirements

1. **Input:** Line level (~1V) from the QuadraVerb or directly from the preamp
2. **Spring tank:** Accutronics/Belton type (typically 8Ω input, 2250Ω output impedance)
3. **Driver circuit:** Converts line level to the current needed to drive the springs
4. **Recovery preamp:** Brings the transducer output back to line level
5. **Mix control:** Blends dry and wet signals
6. **Low-impedance output buffer:** Drives the MC100's ~100kΩ input with consistent impedance regardless of mix position
7. **Optional:** Dwell control (how hard the springs are driven), tone control on wet signal

### Form Factor

Rackmount (1U or 2U). Spring tank mounted internally with shock isolation. Front panel: Dwell, Mix, Tone. Rear panel: In, Out, Send (to external tank), Return (from external tank).

See [reverb-tank/design.md](../reverb-tank/design.md) for full design document.

---

## Sabine RT-1601 — Rack Tuner

### Signal Path

The Sabine RT-1601 is **not in the main signal path.** It receives signal via a passive mute switch split placed after the pedalboard, before the Alembic FX-1:

```
Pedalboard (Dirt out) → Mute Switch (normal: pass through) → Alembic FX-1 → ...
                                   ↓
                              Sabine RT-1601 (when muted)
```

When the mute switch is stomped, the signal is routed to the Sabine and the output to the Alembic is disconnected (silent). The Sabine's own buffer is never in the audio path during play.

### Why Not In-Line

The Sabine RT-1601 has a pass-through design (input and output are directly connected unless muted) with a 250kΩ input impedance. While functional, its buffer from the 1990s is not audiophile-grade. Keeping it on a passive split preserves the hi-fi signal chain.

### Rack Integration

The Sabine occupies 1U of rack space. It sits next to the Alembic FX-1 and above/below the QuadraVerb, connected to the mute switch footswitch on the pedalboard via a dedicated ¼" TS cable run.

### Sabine RT-1601 Quick Specs

| Parameter | Value |
|---|---|
| Form Factor | 1U rackmount |
| Tuning | Chromatic, auto-sensing, 7 octaves |
| Accuracy | ±1 cent |
| Inputs | 2x ¼" TS (front + rear, parallel) |
| Outputs | 2x ¼" TS (front + rear, pass-through) |
| Mute | Front panel button + external footswitch jack |
| Power | 9VDC 225mA, center-negative |
