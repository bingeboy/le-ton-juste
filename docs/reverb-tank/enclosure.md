# Reverb Tank — Rackmount Enclosure

> **Authoritative sources:** for the *final* build, [`parts-spec.md`](./parts-spec.md), [`parts-list.md`](./parts-list.md) and [`mouser-bom.csv`](./mouser-bom.csv) are ground truth. This doc is the mechanical/layout overview; where a number here disagrees with parts-spec, parts-spec wins. Known fixed-up points: the chassis is **aluminum Hammond 1455T2201** (steel is explicitly wrong — it interacts with the toroid), the transformer is **30VA Triad F-219X** (not 15VA), the op-amps are **OPA2134** (not NE5532), and the mains fuse is **500mA slow-blow** (not 1A). Send/Return/XLR jacks are *not* part of this build.

## Form Factor

**2U rackmount chassis** (~3.5" × 19" × variable depth). A 1U chassis is possible but very tight once a spring tank is mounted internally. 2U provides comfortable space for the tank, PCB, power supply, and ventilation.

## Chassis Options

| Manufacturer | Model | Notes |
|---|---|---|
| **Hammond** | **1455T2201** | **Specified part — aluminum, 2U, rack ears included. Aluminum is mandatory: a steel chassis interacts with the toroid's residual field (see parts-spec).** |
| Bud Industries | RM-14215 | Aluminum, 15" depth — acceptable alternative |
| Penn Elcom | Custom | Blank aluminum chassis, drill yourself |

> Avoid steel rackmount chassis (e.g. Hammond RM2U) — steel couples to the toroidal transformer field and can inject 60Hz hum into the spring tank. Use aluminum only.

## Internal Layout (Top-Down View)

```
Rear Panel ───────────────────────────────────── Front Panel
│                                                   │
│   ┌─────────────────────────┐                    │
│   │                         │                    │
│   │   Spring Tank           │                    │
│   │   (horizontal mount,    │      ┌─────────┐   │
│   │    grommet-isolated,    │      │  Audio   │   │
│   │    open side down)      │      │  PCB     │   │
│   │                         │      │          │   │
│   └─────────────────────────┘      └─────────┘   │
│                                                   │
│   ┌──────────┐                                    │
│   │ PSU PCB  │                                    │
│   │ (trans-  │                                    │
│   │ former)  │                                    │
│   └──────────┘                                    │
│                                                   │
─────────────────────────────────────────────────────
          ↑ IEC Inlet, Fuse, Power Switch ↑
```

## Tank Mounting

The Accutronics/Belton tank must be mounted:
- **Open side down** (springs hang below the transducers)
- On **rubber grommets** for mechanical isolation
- Away from the power transformer to avoid magnetic hum coupling
- With **RCA cables** connecting the tank to the PCB (keep these short and shielded)

### Grommet Selection

- Accutronics/Belton tanks come with mounting holes designed for #6 or #8 screws
- Use soft rubber grommets (not hard plastic bushings)
- Grommet inner diameter = screw size, outer diameter fits chassis hole
- Common part: Keystone 763 or equivalent

## Connectors

### Rear Panel

| Connector | Type | Notes |
|---|---|---|
| Input | 1/4" TS (Switchcraft #11) | From QuadraVerb / preamp |
| Output | 1/4" TS (Switchcraft #11) | To McIntosh MC100 |
| Send | 1/4" TS (optional) | To external tank |
| Return | 1/4" TS (optional) | From external tank |
| Balanced Out | XLR-M (Neutrik NC3MD) (optional) | For future use |
| IEC Power | Schurter 5110.1052 EMI-filtered IEC C14 inlet with fuse holder (500mA slow-blow) | Standard power cable |

### Front Panel

| Control | Type | Notes |
|---|---|---|
| Dwell | 10k linear pot, 16mm | How hard springs are driven (like Fender "Dwell") |
| Tone | 100k audio pot, 16mm | High-cut or high-shelf on wet signal |
| Mix | 100k audio pot, 16mm | Dry → Wet blend |
| Power LED | 5mm LED with bezel (blue or green) | Indicates power on |

## Grounding Scheme

- **Star ground:** All grounds (audio, power, chassis) meet at a single point near the IEC inlet
- Chassis is safety grounded (IEC ground pin connected directly to chassis)
- Audio ground is isolated from chassis except at the star ground point
- RCA/TS jack sleeves connect to audio ground, not chassis
- If hum persists, add a ground-lift switch that inserts a 10Ω resistor + 100nF cap between audio ground and chassis

## Thermal Considerations

- The OPA2134 op-amps consume only a few mA each — negligible heat
- The BD139 driver (~0.22W) and the LM7815/LM7915 regulators (~0.15–0.3W each) are the only warm parts — heatsink the regulators (mica-isolated) and clip a small heatsink on Q1; see parts-spec Heatsinks
- Power transformer generates mild heat — keep away from the spring tank and ensure some airflow
- No fan needed for this solid-state design

## Ventilation

- Prefer a vented aluminum chassis; the specified Hammond 1455T2201 can be vented by drilling/milling near the PSU area if its stock venting is insufficient
- If using a blank chassis, drill a pattern of small holes or mill slots near the PSU area
- Don't block vents when rackmounted — leave 1U of space above/below if possible
