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
| W04G bridge rectifier 2A/400V *(upgraded from W02G)* | W04G | 1 | ~$0.55 |
| 1N4148 small-signal diode (input clamp pair + D3 collector clamp) | 1N4148 | 3 | ~$0.10 each = $0.30 |
| SMBJ15CA bidirectional TVS diode (input ESD protection) | SMBJ15CA | 1 | ~$0.50 |

### Protection Components

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| Littelfuse V275LA20AP MOV — mains surge clamp 275V | V275LA20AP | 1 | ~$0.75 |
| Ametherm MS32 5006 NTC thermistor — inrush limiter | MS32 5006 | 1 | ~$3.00 |
| Bourns MF-R050 polyfuse 500mA — +15V rail | MF-R050 | 1 | ~$0.75 |
| Bourns MF-R050 polyfuse 500mA — −15V rail | MF-R050 | 1 | ~$0.75 |

### Capacitors — Signal Path (WIMA MKS2 film)

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| 1µF/63V film (C_in input coupling + C1 driver coupling) | MKS2C041001B00KSSD | 2 | ~$0.50 each = $1.00 |
| 470nF/63V film | MKS2C034700K00KSSD | 1 | ~$0.35 |
| 100nF/63V film (HPF + op-amp decoupling) | MKS2C031001A00KSSD | 8 | ~$0.25 each = $2.00 |
| 47pF silver mica (bright cap) | CD15ED470JO3F | 1 | ~$0.40 |

### Capacitors — Electrolytic (Nichicon)

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| 2200µF/**50V** low-ESR (main PSU filter) *(upgraded from 35V)* | UKW1H222MHD | 2 | ~$1.50 each = $3.00 |
| 100µF/25V audio grade (reg output + emitter bypass) | UKW1E101MED | 3 | ~$0.35 each = $1.05 |
| 10µF/25V (bulk rail decoupling) | UKW1E100MDD | 2 | ~$0.25 each = $0.50 |

### Resistors (Yageo MFR 1% 250mW — order 5 of each)

| Value | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| 1MΩ | MFR-25FBF52-1M | 5 | ~$0.40 |
| 100kΩ | MFR-25FBF52-100K | 5 | ~$0.40 |
| 10kΩ | MFR-25FBF52-10K | 5 | ~$0.40 |
| 6.8kΩ | MFR-25FBF52-6K8 | 5 | ~$0.40 |
| 5.6kΩ | MFR-25FBF52-5K6 | 5 | ~$0.40 |
| 470Ω | MFR-25FBF52-470R | 5 | ~$0.40 |
| 100Ω | MFR-25FBF52-100R | 5 | ~$0.40 |
| 68Ω | MFR-25FBF52-68R | 5 | ~$0.40 |
| 1kΩ | MFR-25FBF52-1K | 5 | ~$0.40 |

### Resistors — High Wattage (1W — bleed + ground lift)

| Value | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| 10kΩ / 1W metal film (PSU bleed resistors — 1 per rail) | FMP100JR-52-10K | 2 | ~$0.30 each = $0.60 |
| 10Ω / 0.5W metal film (ground lift RC network) | MFR-25FBF52-10R | 2 | ~$0.10 each = $0.20 |

### Potentiometers (Vishay/Spectrol 296 — MIL-PRF-39023)

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| 10kΩ linear (Dwell) | 296UAL103B2 | 1 | ~$10 |
| 100kΩ linear (Mix + Tone) | 296UAL104B2 | 2 | ~$10 each = $20 |

### Serviceability — Molex KK Connectors
*Use these at every internal wire connection so components can be swapped without desoldering*

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| Molex KK 2-pin housing (transformer secondary × 2, tank RCA × 2, jacks × 2) | 22-01-3027 | 8 | ~$0.25 each = $2.00 |
| Molex KK 3-pin housing (front panel pots × 3) | 22-01-3037 | 3 | ~$0.25 each = $0.75 |
| Molex KK crimp terminals (bag of 50) | 08-50-0114 | 1 bag | ~$3.00 |

### Hardware & Connectors

| Item | Mfr Part # | Qty | Est. Price |
|---|---|---|---|
| Switchcraft 112A ¼" TS jack | 112A | 2 | ~$3.20 each = $6.40 |
| DIP-8 machine-pin IC socket | A-108-A-LPT | 2 | ~$0.50 each = $1.00 |
| Schurter EMI-filtered IEC inlet with fuse holder *(upgraded from 4301.0527)* | 5110.1052 | 1 | ~$15.00 |
| TE SPST rocker switch 6A/250V (mains power) | 1825232-1 | 1 | ~$2.00 |
| SPDT mini toggle switch (ground lift, rear panel) | 100SP1T1B1M1QEH | 1 | ~$3.50 |
| 5mm LED — blue or amber (power indicator) | — | 1 | ~$0.50 |
| 5mm LED panel-mount bezel | — | 1 | ~$1.00 |
| TO-220 heatsink | V7477X | 2 | ~$1.50 each = $3.00 |
| TO-220 mica insulating pad | 4880SG | 2 | ~$0.30 each = $0.60 |
| Thermal compound (Shin-Etsu X-23 or equivalent) | — | 1 small tube | ~$5.00 |
| Triad F-219X toroidal transformer 15VA dual 15VAC | F-219X | 1 | ~$28 |
| Vector T44 FR4 perfboard | T44 | 1 | ~$8.00 |
| Würth M3 nylon standoff 10mm | 971100311 | 4 | ~$0.50 each = $2.00 |
| Würth M3 stainless screw | 900151030030 | 10 | ~$0.20 each = $2.00 |
| Belden 8451 shielded wire 24AWG | 8451 | 1 roll | ~$15 |
| Colored heat-shrink assortment (red/blue/black/white/gray) | — | 1 pack | ~$5.00 |
| Kester 44 solder 63/37 0.031" | 24-6337-0027 | 1 roll | ~$18 |
| Kester 951 flux pen | 2331-ZX | 1 | ~$8.00 |
| MG Chemicals 422B conformal coating spray | 422B | 1 can | ~$15.00 |

**Mouser Subtotal: ~$190–215**

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
- 1× 5mm LED hole (power indicator)
- 1× IEC cutout (rear)
- 1× rocker switch hole (mains, rear)
- 1× mini toggle hole (ground lift, rear)
- Engraved labels

| Item | Qty | Est. Price |
|---|---|---|
| Custom 2U aluminum front panel | 1 | ~$35 |

---

## Supplier 5 — Amazon / McMaster-Carr

| Item | Qty | Est. Price |
|---|---|---|
| Sorbothane isolation grommets M3, Shore 30–40 (tank mounting) | 4 | ~$10–12 |

---

## Knobs (Owner to Select)
3× ¼" D-shaft aluminum skirted knobs, 1" diameter. Source from Mouser, Smallbear Electronics, or Amazon.

---

## Total Estimated Cost

| Supplier | Est. Cost |
|---|---|
| Amplified Parts | ~$53 |
| Mouser | ~$190–215 |
| Hammond (chassis) | ~$50 |
| Front Panel Express | ~$35 |
| Sorbothane grommets | ~$12 |
| Knobs | ~$15 |
| **Total** | **~$355–380** |

> OPA2134PA price confirmed at $7.64 (Mouser, June 2026). All other prices are estimates — verify in the Mouser BOM tool before ordering. Upgraded total reflects full reliability/protection package.
