# Build Roadmap

Priority order for remaining builds and upgrades. Each item builds on the previous.

---

## 1. Ghost Spring Reverb Tank
**Status: In progress — being built by Dan Jams LLC**

Transformer-coupled single spring reverb unit. Full design, parts spec, and schematic complete. See `docs/reverb-tank/`.

---

## 2. Rack Parallel Mixer
**Status: Designed, not yet built**

3-channel active summing mixer (OPA2134) that moves the QuadraVerb and Ghost Spring into parallel loops, keeping the dry signal fully analog and untouched through the entire rack. This is the single biggest remaining upgrade to the hi-fi signal path.

**Why it matters:** Currently both the QuadraVerb and Ghost Spring are in series — the dry signal passes through digital converters (QuadraVerb) and the spring tank mix pot (Ghost Spring). The parallel mixer eliminates both compromises.

**Result:** The dry guitar sits completely isolated and transparent. Reverb and delay bloom independently around it — the separation between the note and the space that defines the early 80s Dead live sound.

See `docs/signal-chain/parallel-mixer.md` for the design and commercial alternatives.

---

## 3. OBEL Buffer
**Status: Planned**

On-Board Effects Loop buffer — either a Waldo OBEL Buffer pedal or DIY JFET build. Moves the volume pot downstream of the pedalboard effects so turning down doesn't kill reverb and delay tails. Also keeps the guitar's high-impedance pickup output isolated from pedal loading.

Complements the rack parallel mixer — OBEL protects the guitar-to-preamp path, rack mixer protects the preamp-to-amp path. Jerry ran both.

---

## 4. Mute Switch + Tuner Routing
**Status: Planned — depends on OBEL**

Passive mute switch on the pedalboard that splits signal to the Sabine RT-1601 rack tuner silently. Most cleanly implemented as part of the OBEL loop. Wiring design is straightforward once the OBEL buffer is in place.
