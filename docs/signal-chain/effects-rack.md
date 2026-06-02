# Effects Rack — QuadraVerb + Reverb Tank

## Alesis QuadraVerb

The QuadraVerb is a multi-effects processor that provides digital reverb, delay, chorus, flanger, pitch shift, and EQ. In the hi-fi Jerry context, it's used for:

- **Digital reverb** (halls, plates) as an alternative to the spring tank
- **Delay** (digital, tap tempo if available)
- **Modulation** (chorus, flanger) for Bob Weir-style shimmer

### Signal Chain Position

Between the Alembic FX-1 output and the custom reverb tank input. Time-based effects after the preamp keep the preamp's tube EQ from coloring the effect tails.

### Routing Options

1. **Series:** Preamp → QuadraVerb → Reverb Tank → MC100 (simplest)
2. **Parallel/wet-dry:** Preamp splits to dry path AND QuadraVerb → mixed post-QuadraVerb (cleaner dry signal but requires a mixer)
3. **FX Loop:** If the Alembic FX-1 has an effects loop, the QuadraVerb goes in the loop (post-preamp-EQ, pre-master-output)

**Recommended starting point:** Series (option 1). It's simple, and the QuadraVerb's mix control allows blending dry/wet internally.

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
