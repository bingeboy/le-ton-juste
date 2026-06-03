# Ghost Spring — Orderable Parts List

Organized by supplier. Mouser items have a ready-to-upload BOM CSV at `mouser-bom.csv` in this folder.

---

## How to Order from Mouser (BOM Tool)

1. Go to **mouser.com** and create a free account if you don't have one
2. Click **"BOM Tool"** in the top navigation (or go to mouser.com/BOMTool)
3. Click **"Create New BOM"** → give it a name (e.g. "Ghost Spring Reverb")
4. Click **"Upload BOM File"** → select `mouser-bom.csv` from this folder
5. Mouser maps manufacturer part numbers automatically — confirm each match
6. Review the cart: it shows live price, stock level, and lead time per item
7. Anything out of stock will show alternatives — accept or skip
8. Click **"Add All to Cart"** → checkout

> Prices shown in the BOM tool are live at time of ordering. Estimates below are approximate based on typical market pricing — verify in the tool before paying.

---

## Supplier 1 — Amplified Parts (amplifiedparts.com)
*Order separately — not on Mouser*

| Item | Part # | Qty | Est. Price |
|---|---|---|---|
| Accutronics 9AB3C1B reverb tank (3-spring, long decay) | 9AB3C1B | 1 | ~$35 |
| Accutronics REB3S reverb driver transformer | REB3S | 1 | ~$18 |

**Subtotal: ~$53**

---

## Supplier 2 — Mouser Electronics (upload mouser-bom.csv)

### Semiconductors

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| OPA2134PA dual audio op-amp DIP-8 | OPA2134PA | 2 pkg | **$7.64 each** = $15.28 |
| BD139 NPN transistor TO-126 | BD139 | 1 | ~$0.55 |
| LM7815CT/NOPB +15V regulator TO-220 | LM7815CT/NOPB | 1 | ~$0.75 |
| LM7915CT/NOPB −15V regulator TO-220 | LM7915CT/NOPB | 1 | ~$0.75 |
| W02G-E4/51 bridge rectifier 1A/200V | W02G-E4/51 | 1 | ~$0.45 |

### Capacitors — Signal Path (WIMA MKS2 film)

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| 1µF/63V film | MKS2C041001B00KSSD | 1 | ~$0.50 |
| 470nF/63V film | MKS2C034700K00KSSD | 1 | ~$0.35 |
| 100nF/63V film (HPF + op-amp decoupling) | MKS2C031001A00KSSD | 8 | ~$0.25 each = $2.00 |
| 47pF silver mica (bright cap) | CD15ED470JO3F | 1 | ~$0.40 |

### Capacitors — Electrolytic (Nichicon)

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| 2200µF/35V low-ESR (main PSU filter) | UKW1V222MHD | 2 | ~$1.20 each = $2.40 |
| 100µF/25V audio grade (reg output + emitter bypass) | UKW1E101MED | 3 | ~$0.35 each = $1.05 |
| 10µF/25V (bulk rail decoupling) | UKW1E100MDD | 2 | ~$0.25 each = $0.50 |

### Resistors (Yageo MFR 1% 250mW — order 5 of each)

| Value | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| 1MΩ | MFR-25FBF52-1M | 5 | ~$0.40 |
| 100kΩ | MFR-25FBF52-100K | 5 | ~$0.40 |
| 22kΩ | MFR-25FBF52-22K | 5 | ~$0.40 |
| 10kΩ | MFR-25FBF52-10K | 5 | ~$0.40 |
| 6.8kΩ | MFR-25FBF52-6K8 | 5 | ~$0.40 |
| 5.6kΩ | MFR-25FBF52-5K6 | 5 | ~$0.40 |
| 470Ω | MFR-25FBF52-470R | 5 | ~$0.40 |
| 100Ω | MFR-25FBF52-100R | 5 | ~$0.40 |
| 68Ω | MFR-25FBF52-68R | 5 | ~$0.40 |
| 1kΩ | MFR-25FBF52-1K | 5 | ~$0.40 |

### Potentiometers (Vishay/Spectrol 296 — MIL-PRF-39023)

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| 10kΩ linear (Dwell) | 296UAL103B2 | 1 | ~$10 |
| 100kΩ linear (Mix + Tone) | 296UAL104B2 | 2 | ~$10 each = $20 |

### Hardware & Connectors

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| Switchcraft 112A ¼" TS jack | 112A | 2 | ~$3.20 each = $6.40 |
| DIP-8 machine-pin IC socket | A-108-A-LPT | 2 | ~$0.50 each = $1.00 |
| Schurter IEC inlet with fuse holder | 4301.0527 | 1 | ~$8.00 |
| TE SPST rocker switch 6A/250V | 1825232-1 | 1 | ~$2.00 |
| TO-220 heatsink | V7477X | 2 | ~$1.50 each = $3.00 |
| TO-220 mica insulating pad | 4880SG | 2 | ~$0.30 each = $0.60 |
| Triad F-219X toroidal transformer 15VA dual 15VAC | F-219X | 1 | ~$28 |
| Vector T44 FR4 perfboard | T44 | 1 | ~$8.00 |
| Würth M3 nylon standoff 10mm | 971100311 | 4 | ~$0.50 each = $2.00 |
| Würth M3 stainless screw | 900151030030 | 10 | ~$0.20 each = $2.00 |
| Belden 8451 shielded wire 24AWG | 8451 | 1 roll | ~$15 |
| Kester 44 solder 63/37 0.031" | 24-6337-0027 | 1 roll | ~$18 |
| Kester 951 flux pen | 2331-ZX | 1 | ~$8.00 |

**Mouser Subtotal: ~$145–165**

---

## Supplier 3 — Hammond (via Mouser or hammfg.com)

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| 2U aluminum rackmount chassis (rack ears included) | 1455T2201 | 1 | ~$50 |

---

## Supplier 4 — Front Panel Express (frontpanelexpress.com)

Design a custom 2U aluminum panel with:
- 3× ¼" D-shaft pot holes (DWELL / MIX / TONE)
- 2× ¼" jack holes (IN / OUT)
- 1× IEC cutout (rear)
- 1× rocker switch hole (rear)
- Engraved labels

| Item | Qty | Est. Price |
|---|---|---|
| Custom 2U aluminum front panel | 1 | ~$35 |

---

## Knobs (Owner to Select)
3× ¼" D-shaft aluminum skirted knobs, 1" diameter. Source from Mouser, Smallbear Electronics, or Amazon.

---

## Total Estimated Cost

| Supplier | Est. Cost |
|---|---|
| Amplified Parts | ~$53 |
| Mouser | ~$145–165 |
| Hammond (chassis) | ~$50 |
| Front Panel Express | ~$35 |
| Knobs | ~$15 |
| **Total** | **~$298–318** |

> OPA2134PA price confirmed at $7.64 (Mouser, June 2026). All other prices are estimates — the Mouser BOM tool will show exact current prices when you upload `mouser-bom.csv`.
