# Build Roadmap

Priority order for remaining builds and upgrades. Each item builds on the previous.

---

## 1. Ghost Spring Reverb Tank
**Status: In progress — build pending**

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

---

## 5. Rack Compressor
**Status: Under consideration — do not add to chain yet**

A rack compressor post-Alembic FX-1 would provide the bloom/sustain character that gives notes a viola or horn-like swell. Slow attack lets the pick transient through; medium-slow release sustains the tail. Goal is musical bloom, not squash.

**Placement when added:** Alembic FX-1 → Compressor → Lehle Parallel M → Ghost Spring → MC100

### Options

| Unit | Price (used) | Character | Notes |
|---|---|---|---|
| **dbx 160A** | ~$300–400 | Warm, transparent, musical "over easy" knee | Top recommendation. 1U, industry standard for live/studio. Precise ratio/attack/release control. Fits the rack aesthetic perfectly. |
| **dbx 165A** | ~$250–350 | Same 160A lineage, adds an integrated limiter | Good if you want an automatic ceiling on peaks going into the Lehle/Ghost Spring. |
| **Summit Audio DCL-200** | ~$700–900 | Tube optical — very warm, smooth, slow-attack by nature | Higher-end option. The tube stage complements the Alembic FX-1's character. More colored than the dbx but in a musical way. |
| **UA 1176LN** (or Black Lion clone) | ~$800–1200 (orig) / ~$400 (clone) | Fast FET — more aggressive, punchier attack control | Better for bite and presence than bloom. Less ideal for the viola/horn goal but excellent if you ever want a more aggressive compressed sound. |
| **Boss CS-2** (pedal, on pedalboard) | ~$80–120 | Guitar-voiced, simple, warm | Lower-fi option but specifically voiced for guitar dynamics. Simpler to dial in. Goes before the Alembic at instrument level. |

### Decision factors
- **dbx 160A is the move** for this rig — professional grade, transparent at low ratios, 1U rack, used market is strong
- Hold off until Ghost Spring and Lehle are in place and the chain is settled
- The Alembic Parametric EQ (if added) should be dialed in first — compressor after EQ in the decision sequence
