# Rack Parallel Mixer — Bill of Materials

## Enclosure & Hardware

| Item | Qty | Notes | Est. Cost |
|---|---|---|---|
| 1U aluminum rack chassis | 1 | Hammond or equivalent | ~$45 |
| Front panel (Front Panel Express) | 1 | Custom aluminum — 8 jacks, 3 pots, 3 switches | ~$35 |
| IEC power inlet with fuse holder | 1 | 500mA slow-blow | ~$3 |
| Power switch (rocker) | 1 | SPST, 6A/250V | ~$2 |

## Electronics — Audio Circuit

| Item | Qty | Notes | Est. Cost |
|---|---|---|---|
| OPA2134PA dual op-amp | 2 | 4 sections total — 3 used (input buffer, summing amp, phase correct/output), 1 spare | ~$14 |
| Resistors (metal film 1% 250mW) | ~20 | 100kΩ, 22kΩ, 10kΩ, 1kΩ, 100Ω — see design for exact values | ~$5 |
| WIMA MKS2 100nF/63V film caps | 8 | Op-amp supply decoupling (2 per package × 2 packages × 2 rails) | ~$8 |
| Nichicon UKW 10µF/25V electrolytic | 2 | Bulk decoupling, one per supply rail at PCB entry | ~$4 |
| Level pots 100kΩ audio (Vishay/Spectrol 296) | 3 | Return level — Loop 1, 2, 3 | ~$30 |
| Send trim pots 10kΩ cermet trimmer | 3 | Internal send level calibration per loop | ~$6 |
| DPDT toggle switches | 3 | Phase invert per loop return | ~$9 |
| Switchcraft 112A ¼" TS jacks | 8 | Input, Output, Send 1–3, Return 1–3 | ~$40 |

## Electronics — Power Supply

| Item | Qty | Notes | Est. Cost |
|---|---|---|---|
| Toroidal transformer 15VA dual 15VAC | 1 | Same spec as Ghost Spring — parts commonality | ~$25 |
| Bridge rectifier 1A/200V (Vishay W02G) | 1 | Full-wave rectification | ~$3 |
| LM7815 TO-220 | 1 | +15V regulator | ~$2 |
| LM7915 TO-220 | 1 | −15V regulator | ~$2 |
| 2200µF/35V low-ESR electrolytic (Nichicon KW) | 2 | Main filter caps | ~$6 |
| 100µF/35V electrolytic (Nichicon KW) | 2 | Regulator output caps | ~$4 |
| 100nF/63V WIMA film | 2 | HF bypass on regulator outputs | ~$2 |
| TO-220 heatsinks + insulating pads | 2 | One per regulator, insulated from chassis | ~$6 |

## Hardware & Consumables

| Item | Qty | Notes | Est. Cost |
|---|---|---|---|
| FR4 perfboard (Vector T44) | 1 | Build surface | ~$8 |
| M3 nylon standoffs 10mm | 4 | Isolate PCB from chassis | ~$3 |
| M3 stainless screws | 10 | Chassis and PCB mounting | ~$3 |
| M3 star washers | 4 | Star-ground and jack mounting points | ~$2 |
| Belden 8451 shielded wire | 1 roll | All internal signal connections | ~$12 |
| 22AWG stranded hookup wire | assorted | Power connections | ~$4 |
| DIP-8 machine-pin IC sockets | 2 | For OPA2134 packages | ~$4 |
| Kester 44 63/37 solder 0.031" | 1 roll | — | ~$12 |
| Kester 951 flux pen | 1 | — | ~$6 |
| Heat shrink tubing assorted | 1 pack | PSU wiring insulation | ~$4 |
| Cable ties 2.5mm | 1 bag | Internal wire management | ~$2 |

## Knobs (Owner to Select)
3 knobs for Level 1–3 pots. Vishay/Spectrol 296 pots have ¼" D-shaft. Match style to Ghost Spring knobs for rack consistency.

## Feet (Owner to Select)
4× self-adhesive rubber feet, 10–12mm height.

## Total Estimated Cost: ~$240–280
