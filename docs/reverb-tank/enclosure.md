# Reverb Tank — Rackmount Enclosure

## Form Factor

**2U rackmount chassis** (~3.5" × 19" × variable depth). A 1U chassis is possible but very tight once a spring tank is mounted internally. 2U provides comfortable space for the tank, PCB, power supply, and ventilation.

## Chassis Options

| Manufacturer | Model | Notes |
|---|---|---|
| Hammond | RM2U | Steel, black, vented top/bottom |
| Bud Industries | RM-14215 | Aluminum, 15" depth |
| Penn Elcom | Custom | Blank chassis, drill yourself |
| eBay / generic | 2U rack chassis | Various depths and finishes |

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
| IEC Power | IEC C14 inlet with fuse holder (1A, slow-blow) | Standard power cable |

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

- The NE5532 op-amps consume ~8mA each — negligible heat
- If a tube driver/recovery stage is used, the tube adds ~2-5W of heat — add ventilation slots above the tube area
- Power transformer generates mild heat — keep away from the spring tank and ensure some airflow
- No fan needed for solid state design

## Ventilation

- Use a vented chassis (Hammond RM2U has perforated top/bottom)
- If using a blank chassis, drill a pattern of small holes or mill slots near the PSU area
- Don't block vents when rackmounted — leave 1U of space above/below if possible
