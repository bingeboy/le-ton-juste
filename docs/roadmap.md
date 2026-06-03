# Build Roadmap

Priority order for remaining builds and upgrades. Each item builds on the previous.

---

## 1. Ghost Spring Reverb Tank
**Status: In progress — being built by Dan Jams LLC**

Transformer-coupled single spring reverb unit. Full design, parts spec, and schematic complete. See `docs/reverb-tank/`.

---

## 2. Lehle Parallel M
**Status: Ready to purchase (~$180 used)**

Single parallel loop unit that puts the QuadraVerb in a parallel loop, keeping the dry signal completely off the QuadraVerb's A/D converters. The Ghost Spring stays in series after the Lehle — it's fully analog with its own Mix pot, no parallel treatment needed.

**Chain:** Alembic FX-1 → Lehle Parallel M (QuadraVerb in loop) → Ghost Spring → MC100

Buy used on Reverb.com or Music Go Round. See `docs/parallel-mixer/design.md` for setup instructions.

---

## 3. OBEL Buffer
**Status: Planned**

On-Board Effects Loop buffer — either a Waldo OBEL Buffer pedal or DIY JFET build. Moves the volume pot downstream of the pedalboard effects so turning down doesn't kill reverb and delay tails. Also keeps the guitar's high-impedance pickup output isolated from pedal loading.

Complements the rack parallel mixer — OBEL protects the guitar-to-preamp path, rack mixer protects the preamp-to-amp path. Jerry ran both.

---

## 4. Mute Switch + Tuner Routing
**Status: Planned — depends on OBEL**

Passive mute switch on the pedalboard that splits signal to the Sabine RT-1601 rack tuner silently. Most cleanly implemented as part of the OBEL loop. Wiring design is straightforward once the OBEL buffer is in place.
