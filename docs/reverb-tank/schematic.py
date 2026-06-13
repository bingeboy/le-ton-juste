#!/usr/bin/env python3
"""Ghost Spring Reverb — Signal Path Schematic"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np

# ── Colour palette ───────────────────────────────────────────────────────────
BG   = '#FAFAF8'
BOX  = '#FFFFFF'
EDGE = '#222222'
DRY  = '#1A5276'   # blue  — dry signal path
WET  = '#1D8348'   # green — wet signal path
PWRR = '#922B21'   # red   — power / supply references

def box(ax, x, y, w, h, title, body, color=BOX, title_bg='#D5D8DC'):
    """Draw a labelled box at (x,y) centre."""
    rect = mpatches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle='round,pad=0.04', linewidth=1.2,
        edgecolor=EDGE, facecolor=color, zorder=3)
    ax.add_patch(rect)
    ax.text(x, y + h/2 - 0.13, title,
            ha='center', va='top', fontsize=7.5, fontweight='bold', zorder=4)
    ax.text(x, y - 0.05, body,
            ha='center', va='center', fontsize=6.8,
            fontfamily='monospace', zorder=4)

def wire(ax, x1, y1, x2, y2, color=EDGE, lw=1.3, style='-'):
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw, ls=style, zorder=2)

def junction(ax, x, y):
    ax.plot(x, y, 'o', color=EDGE, ms=4, zorder=5)

def label(ax, x, y, text, ha='center', va='center', color=EDGE, size=7):
    ax.text(x, y, text, ha=ha, va=va, fontsize=size, color=color, zorder=6)

def arrow(ax, x1, y1, x2, y2, color=EDGE):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.2), zorder=4)


# ── Layout constants ─────────────────────────────────────────────────────────
W, H = 17, 9           # figure size (inches)
BW   = 1.45            # box width
BH   = 0.80            # box height
Y1   = 6.5             # top row y
Y2   = 2.8             # bottom row y
Y3   = 1.1             # ground rail y

fig, ax = plt.subplots(figsize=(W, H), facecolor=BG)
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect('equal')
ax.axis('off')
ax.set_facecolor(BG)

# ── Title ────────────────────────────────────────────────────────────────────
ax.text(W/2, H - 0.35, 'Ghost Spring Reverb — Signal Path Schematic',
        ha='center', va='top', fontsize=13, fontweight='bold', color=EDGE)
ax.text(W/2, H - 0.72,
        'Transformer-Coupled 3-Spring Tank  •  OPA2134 Solid-State  •  ±15V Linear Supply',
        ha='center', va='top', fontsize=8.5, color='#555555')

# ═════════════════════════════════════════════════════════════════════════════
# TOP ROW  (Y1)  —  Input → Buffer → Driver → Transformer → Tank
# ═════════════════════════════════════════════════════════════════════════════
xs = [1.2, 3.0, 4.9, 6.8, 9.1, 11.4]   # x-centres of top-row boxes
labels_top = [
    ('LINE IN\n¼" TS', ''),
    ('U1  OPA2134\nInput Buffer', 'R1  1MΩ input\nR2  100Ω output\nUnity gain'),
    ('RV1  DWELL\n+ Driver Stage', 'C1  1µF coupling\nRV1 10kΩ lin\nR3  1kΩ base\nR3b 6.8kΩ / R4 1kΩ bias\nR5  68Ω emitter\nC2  100µF bypass\nQ1  BD139 NPN'),
    ('T2  REB3S\nDriver Xfmr', '8Ω secondary\n→ tank input\n+15V on primary'),
    ('SPRING TANK\nAccutronics\n9AB3C1B', '3-spring  Long\n8Ω input\n2550Ω output\nLong decay'),
    ('', ''),   # placeholder — tank has no right box
]

# ── Input terminal ────────────────────────────────────────────────────────────
ax.plot(xs[0], Y1, 's', ms=10, color='#D5D8DC', zorder=3)
ax.text(xs[0], Y1 + 0.55, 'LINE IN\n¼" TS Jack', ha='center', va='bottom',
        fontsize=7.5, fontweight='bold')
label(ax, xs[0], Y1, 'J1', size=7)

# ── U1: Input Buffer ──────────────────────────────────────────────────────────
box(ax, xs[1], Y1, BW, BH,
    'U1  OPA2134',
    'Input Buffer\nUnity gain\nR1 = 1MΩ  R2 = 100Ω',
    color='#EBF5FB')

# ── Driver Stage (Dwell + BD139) ──────────────────────────────────────────────
box(ax, xs[2], Y1, BW + 0.1, BH + 0.3,
    'DRIVER STAGE',
    'C1  1µF coupling\nRV1 10kΩ Dwell pot\nR3  1kΩ  R3b 6.8kΩ  R4 1kΩ\nR5  68Ω  C2  100µF\nQ1  BD139 NPN',
    color='#EAFAF1')

# ── T2: REB3S Transformer ────────────────────────────────────────────────────
box(ax, xs[3], Y1, BW - 0.05, BH,
    'T2  Accutronics REB3S',
    'Driver Transformer\nPri: Q1 collector\nSec: 8Ω → tank',
    color='#FEF9E7')

# ── Spring Tank ───────────────────────────────────────────────────────────────
tank_x, tank_w, tank_h = xs[4], 2.0, BH + 0.1
rect = mpatches.FancyBboxPatch(
    (tank_x - tank_w/2, Y1 - tank_h/2), tank_w, tank_h,
    boxstyle='round,pad=0.05', lw=2.0,
    edgecolor='#884EA0', facecolor='#F5EEF8', zorder=3)
ax.add_patch(rect)
ax.text(tank_x, Y1 + tank_h/2 - 0.12, 'ACCUTRONICS  9AB3C1B',
        ha='center', va='top', fontsize=8, fontweight='bold', color='#884EA0', zorder=4)
ax.text(tank_x, Y1 - 0.05, '3-spring  •  Long decay\n8Ω input  /  2550Ω output',
        ha='center', va='center', fontsize=7.2, zorder=4)

# ── Top row wires ─────────────────────────────────────────────────────────────
for i in range(len(xs) - 2):
    x_start = xs[i] + (0.12 if i == 0 else BW/2)
    x_end   = xs[i+1] - BW/2
    wire(ax, x_start, Y1, x_end, Y1, color=DRY)

# Input → Buffer impedance label
label(ax, (xs[0] + xs[1])/2, Y1 + 0.18, 'R1  1MΩ', color=DRY, size=6.5)

# Buffer → Driver
label(ax, (xs[1] + xs[2])/2, Y1 + 0.18, 'C1  1µF', color=DRY, size=6.5)

# Transformer → Tank
wire(ax, xs[3] + BW/2 - 0.05, Y1, tank_x - tank_w/2, Y1, color=WET)
label(ax, (xs[3] + tank_x)/2, Y1 + 0.18, '8Ω', color=WET, size=6.5)

# Dry tap point (after U1 output resistor)
dry_x = xs[1] + BW/2 + 0.25
junction(ax, dry_x, Y1)
label(ax, dry_x + 0.05, Y1 + 0.22, 'DRY TAP', color=DRY, size=6)

# +15V supply to driver & transformer
label(ax, xs[2] + 0.1, Y1 + BH/2 + 0.18, '+15V', color=PWRR, size=6.5)
ax.plot(xs[2] + 0.1, Y1 + BH/2 + 0.08, '^', ms=6, color=PWRR, zorder=5)
label(ax, xs[3] + 0.1, Y1 + BH/2 + 0.18, '+15V', color=PWRR, size=6.5)
ax.plot(xs[3] + 0.1, Y1 + BH/2 + 0.08, '^', ms=6, color=PWRR, zorder=5)

# D3: flyback clamp diode — anode at Q1 collector junction, cathode to +15V
# Drawn between driver stage and transformer
d3_x = (xs[2] + xs[3]) / 2 + 0.1
d3_y = Y1 - BH/2 - 0.28
ax.plot([d3_x - 0.18, d3_x + 0.18], [d3_y, d3_y], color=PWRR, lw=1.0, zorder=4)
ax.plot([d3_x, d3_x], [d3_y, d3_y + 0.18], color=PWRR, lw=0.8, ls='--', zorder=4)
ax.plot(d3_x, d3_y + 0.18, '^', ms=5, color=PWRR, zorder=5)
label(ax, d3_x, d3_y - 0.18, 'D3  1N4148\nflyback clamp\nanode→collector  cathode→+15V',
      color=PWRR, size=5.8)

# ═════════════════════════════════════════════════════════════════════════════
# BOTTOM ROW  (Y2)  —  Tank out → Recovery → HPF → Tone → Mix → Output
# ═════════════════════════════════════════════════════════════════════════════
xs2 = [11.4, 9.4, 7.5, 5.7, 4.0, 2.2]  # x-centres, right to left (mirrors top)

# Tank output drop line → recovery
wire(ax, tank_x + tank_w/2 - 0.1, Y1 - tank_h/2,
         tank_x + tank_w/2 - 0.1, Y2 + BH/2, color=WET, lw=1.4)
label(ax, tank_x + tank_w/2 + 0.35, (Y1 + Y2)/2, '2550Ω\nout', color=WET, size=6.5)

# ── U2: Recovery Preamp ───────────────────────────────────────────────────────
box(ax, xs2[1], Y2, BW + 0.1, BH + 0.2,
    'U2  OPA2134',
    'Recovery Preamp  (non-inverting)\nGain = 1+Rf/Ri = 214×  (~46 dB)\nRi 470Ω   Rf 100kΩ\nC3 470nF  Rbias 100kΩ',
    color='#EAFAF1')
wire(ax, tank_x + tank_w/2 - 0.1, Y2, xs2[1] + BW/2 + 0.05, Y2, color=WET)
label(ax, (tank_x + tank_w/2 + xs2[1])/2 + 0.1, Y2 + 0.22,
      'C3  470nF', color=WET, size=6.5)

# ── HPF (300 Hz wet-only) ─────────────────────────────────────────────────────
box(ax, xs2[2], Y2, BW - 0.1, BH,
    '300 Hz HPF',
    '(wet signal only)\nC4  100nF film\nR6  5.6kΩ to GND',
    color='#EAFAF1')
wire(ax, xs2[1] - BW/2 - 0.05, Y2, xs2[2] + (BW - 0.1)/2, Y2, color=WET)
# HPF ground
wire(ax, xs2[2], Y2 - BH/2, xs2[2], Y3 + 0.15, color=EDGE, lw=0.9, style='--')
label(ax, xs2[2] + 0.25, Y3 + 0.25, 'GND', size=6.5)

# ── RV3: Tone ────────────────────────────────────────────────────────────────
box(ax, xs2[3], Y2, BW - 0.1, BH,
    'RV3  TONE',
    'High-shelf\n(wet only)\n100kΩ audio',
    color='#EAFAF1')
wire(ax, xs2[2] - (BW - 0.1)/2, Y2, xs2[3] + (BW - 0.1)/2, Y2, color=WET)

# ── Mix node + RV2 ────────────────────────────────────────────────────────────
mix_x = xs2[4]
box(ax, mix_x, Y2, BW - 0.05, BH,
    'RV2  MIX',
    'Dry + Wet blend\n100kΩ audio\n+ 47pF bright cap',
    color='#FEF9E7')
wire(ax, xs2[3] - (BW - 0.1)/2, Y2, mix_x + (BW - 0.05)/2, Y2, color=WET)
junction(ax, mix_x + (BW - 0.05)/2, Y2)

# ── U3: Output Buffer ─────────────────────────────────────────────────────────
box(ax, xs2[5], Y2, BW - 0.1, BH,
    'U3  OPA2134',
    'Output Buffer\nUnity gain\nR7 = 100Ω output',
    color='#EBF5FB')
wire(ax, mix_x - (BW - 0.05)/2, Y2, xs2[5] + (BW - 0.1)/2, Y2, color=EDGE)

# ── Output terminal ──────────────────────────────────────────────────────────
out_x = xs2[5] - (BW - 0.1)/2 - 0.5
wire(ax, xs2[5] - (BW - 0.1)/2, Y2, out_x + 0.1, Y2, color=EDGE)
ax.plot(out_x, Y2, 's', ms=10, color='#D5D8DC', zorder=3)
ax.text(out_x, Y2 + 0.55, 'LINE OUT\n¼" TS → MC100', ha='center', va='bottom',
        fontsize=7.5, fontweight='bold')
label(ax, out_x, Y2, 'J2', size=7)

# ═════════════════════════════════════════════════════════════════════════════
# DRY PATH:  dry_x  →  drops down  →  arrives at mix node
# ═════════════════════════════════════════════════════════════════════════════
dry_drop_y = (Y1 + Y2) / 2
mix_arrive_x = mix_x + (BW - 0.05)/2 + 0.05

wire(ax, dry_x, Y1, dry_x, dry_drop_y, color=DRY)
wire(ax, dry_x, dry_drop_y, mix_arrive_x, dry_drop_y, color=DRY)
wire(ax, mix_arrive_x, dry_drop_y, mix_arrive_x, Y2, color=DRY)
label(ax, (dry_x + mix_arrive_x)/2, dry_drop_y + 0.18, 'Rdry  10kΩ', color=DRY, size=6.5)
# Rdry resistor visual
label(ax, (dry_x + mix_arrive_x)/2, dry_drop_y - 0.18,
      '────[10kΩ]────', color=DRY, size=6.5, ha='center')

# ═════════════════════════════════════════════════════════════════════════════
# POWER SUPPLY INSET (bottom-right)
# ═════════════════════════════════════════════════════════════════════════════
ps_x, ps_y = 13.8, 2.0
psu_w, psu_h = 2.8, 2.8
rect_psu = mpatches.FancyBboxPatch(
    (ps_x - psu_w/2, ps_y - psu_h/2), psu_w, psu_h,
    boxstyle='round,pad=0.06', lw=1.5,
    edgecolor=PWRR, facecolor='#FDEDEC', zorder=3)
ax.add_patch(rect_psu)
ax.text(ps_x, ps_y + psu_h/2 - 0.15, '±15V POWER SUPPLY',
        ha='center', va='top', fontsize=8, fontweight='bold', color=PWRR, zorder=4)
psu_body = (
    'T1  Toroidal 30VA\n'
    '    2 × 15VAC output\n\n'
    'BR1  Bridge rectifier 2A\n\n'
    'U4   LM7815  →  +15V\n'
    'U5   LM7915  →  −15V\n\n'
    'C11–C12  1000µF / 50V\n'
    'C13/C14 reg · C15/C16 bulk'
)
ax.text(ps_x, ps_y - 0.05, psu_body,
        ha='center', va='center', fontsize=6.8,
        fontfamily='monospace', zorder=4)

# ═════════════════════════════════════════════════════════════════════════════
# LEGEND
# ═════════════════════════════════════════════════════════════════════════════
leg_x, leg_y = 1.0, 1.8
ax.text(leg_x, leg_y + 0.25, 'Signal path:', fontsize=7.5, fontweight='bold')
wire(ax, leg_x, leg_y - 0.05, leg_x + 0.7, leg_y - 0.05, color=DRY, lw=2)
label(ax, leg_x + 1.1, leg_y - 0.05, 'Dry (analog, unprocessed)', ha='left', color=DRY, size=7)
wire(ax, leg_x, leg_y - 0.38, leg_x + 0.7, leg_y - 0.38, color=WET, lw=2)
label(ax, leg_x + 1.1, leg_y - 0.38, 'Wet (through spring tank)', ha='left', color=WET, size=7)

# ── Op-amp supply annotation ──────────────────────────────────────────────────
label(ax, 6.0, 0.6,
      'All op-amps (U1–U3): 100nF film decoupling on each supply pin  •  '
      'Power: ±15V from onboard linear supply',
      size=6.5, color='#555555')

plt.tight_layout(pad=0.3)
import os as _os
_out = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'schematic.png')
plt.savefig(_out, dpi=180, bbox_inches='tight', facecolor=BG)
print(f"Saved: {_out}")
