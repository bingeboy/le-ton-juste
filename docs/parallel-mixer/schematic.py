#!/usr/bin/env python3
"""Rack Parallel Mixer — Signal Path Schematic"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

BG   = '#FAFAF8'
BOX  = '#FFFFFF'
EDGE = '#222222'
DRY  = '#1A5276'
WET1 = '#1D8348'
WET2 = '#884EA0'
WET3 = '#B7950B'
PWRR = '#922B21'

def box(ax, x, y, w, h, title, body, color=BOX):
    r = mpatches.FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle='round,pad=0.04', lw=1.2, edgecolor=EDGE, facecolor=color, zorder=3)
    ax.add_patch(r)
    ax.text(x, y+h/2-0.12, title, ha='center', va='top',
            fontsize=7.5, fontweight='bold', zorder=4)
    ax.text(x, y-0.05, body, ha='center', va='center',
            fontsize=6.5, fontfamily='monospace', zorder=4)

def wire(ax, x1, y1, x2, y2, color=EDGE, lw=1.3, ls='-'):
    ax.plot([x1,x2],[y1,y2], color=color, lw=lw, ls=ls, zorder=2)

def dot(ax, x, y):
    ax.plot(x, y, 'o', color=EDGE, ms=4.5, zorder=5)

def lbl(ax, x, y, t, ha='center', va='center', color=EDGE, size=7):
    ax.text(x, y, t, ha=ha, va=va, fontsize=size, color=color, zorder=6)

W, H = 18, 10
BW, BH = 1.5, 0.8

fig, ax = plt.subplots(figsize=(W, H), facecolor=BG)
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect('equal')
ax.axis('off')
ax.set_facecolor(BG)

# Title
ax.text(W/2, H-0.3, 'Rack Parallel Mixer — Signal Path Schematic',
        ha='center', va='top', fontsize=13, fontweight='bold')
ax.text(W/2, H-0.65,
        '3-Channel Active Summing  •  OPA2134 Throughout  •  ±15V Linear Supply  •  1U Rackmount',
        ha='center', va='top', fontsize=8.5, color='#555')

# ── MAIN SIGNAL PATH ─────────────────────────────────────────────────────────
Y_main = 5.5   # centre line

# Input jack
ax.plot(0.7, Y_main, 's', ms=11, color='#D5D8DC', zorder=3)
lbl(ax, 0.7, Y_main+0.55, 'INPUT\nFrom Alembic FX-1', size=7.5, color=EDGE)
lbl(ax, 0.7, Y_main, 'J1', size=7)

wire(ax, 0.82, Y_main, 1.3, Y_main)

# U1: Input Buffer
box(ax, 2.1, Y_main, BW+0.1, BH,
    'U1  OPA2134', 'Input Buffer\nR_in 100kΩ  Unity gain', color='#EBF5FB')

wire(ax, 2.1+BW/2+0.05, Y_main, 2.9, Y_main)

# Splitter node
split_x = 3.1
dot(ax, split_x, Y_main)
lbl(ax, split_x, Y_main+0.28, 'SPLITTER\n(R_iso 1kΩ each)', color=EDGE, size=6.5)

# Dry path — straight through (top-most path)
Y_dry = 7.8
wire(ax, split_x, Y_main, split_x, Y_dry, color=DRY, lw=1.5)
wire(ax, split_x, Y_dry, 14.5, Y_dry, color=DRY, lw=1.5)
lbl(ax, 8.8, Y_dry+0.22, 'DRY PATH — 100% Analog, No Conversion, No Coloration', color=DRY, size=7.5)

# ── LOOP 1: QuadraVerb ────────────────────────────────────────────────────────
Y1 = 5.5
loop1_send_x = 4.5

wire(ax, split_x, Y_main, loop1_send_x-0.5, Y1)
ax.plot(loop1_send_x-0.5, Y1, 's', ms=9, color='#D8F0E8', zorder=3)
lbl(ax, loop1_send_x-0.5, Y1+0.4, 'S1', size=7, color=WET1)

box(ax, loop1_send_x+0.7, Y1, 1.6, BH,
    'QUADRAVERB', 'Loop 1\nDelay + Modulation\n100% Wet', color='#EAFAF1')

ax.plot(loop1_send_x+1.8, Y1, 's', ms=9, color='#D8F0E8', zorder=3)
lbl(ax, loop1_send_x+1.8, Y1+0.4, 'R1', size=7, color=WET1)
wire(ax, loop1_send_x+1.8+0.1, Y1, 7.5, Y1)

box(ax, 8.0, Y1, BW-0.1, BH,
    'PHASE SW 1', 'DPDT Toggle\nPhase Invert', color='#EAFAF1')
wire(ax, 8.0+BW/2-0.05, Y1, 8.8, Y1)
box(ax, 9.4, Y1, BW-0.1, BH,
    'LEVEL 1', 'Vishay 296\n100kΩ audio', color='#EAFAF1')
wire(ax, 9.4+BW/2-0.05, Y1, 10.2, Y1, color=WET1)
lbl(ax, 5.3, Y1+0.45, 'Loop 1 — QuadraVerb (Delay / Mod)', color=WET1, size=7)

# ── LOOP 2: Ghost Spring ──────────────────────────────────────────────────────
Y2 = 3.5

wire(ax, split_x, Y_main, split_x, Y2)
wire(ax, split_x, Y2, loop1_send_x-0.5, Y2)
ax.plot(loop1_send_x-0.5, Y2, 's', ms=9, color='#EDE0F5', zorder=3)
lbl(ax, loop1_send_x-0.5, Y2+0.4, 'S2', size=7, color=WET2)

box(ax, loop1_send_x+0.7, Y2, 1.6, BH,
    'GHOST SPRING', 'Loop 2\nSpring Reverb\n100% Wet', color='#F5EEF8')

ax.plot(loop1_send_x+1.8, Y2, 's', ms=9, color='#EDE0F5', zorder=3)
lbl(ax, loop1_send_x+1.8, Y2+0.4, 'R2', size=7, color=WET2)
wire(ax, loop1_send_x+1.8+0.1, Y2, 7.5, Y2)

box(ax, 8.0, Y2, BW-0.1, BH,
    'PHASE SW 2', 'DPDT Toggle\nPhase Invert', color='#F5EEF8')
wire(ax, 8.0+BW/2-0.05, Y2, 8.8, Y2)
box(ax, 9.4, Y2, BW-0.1, BH,
    'LEVEL 2', 'Vishay 296\n100kΩ audio', color='#F5EEF8')
wire(ax, 9.4+BW/2-0.05, Y2, 10.2, Y2, color=WET2)
lbl(ax, 5.3, Y2+0.45, 'Loop 2 — Ghost Spring (Reverb)', color=WET2, size=7)

# ── LOOP 3: Experimental ──────────────────────────────────────────────────────
Y3 = 1.5

wire(ax, split_x, Y_main, split_x, Y3)
wire(ax, split_x, Y3, loop1_send_x-0.5, Y3)
ax.plot(loop1_send_x-0.5, Y3, 's', ms=9, color='#FEF3CD', zorder=3)
lbl(ax, loop1_send_x-0.5, Y3+0.4, 'S3', size=7, color=WET3)

box(ax, loop1_send_x+0.7, Y3, 1.6, BH,
    'LOOP 3', 'Experimental\nRainbow Machine / POG\nMOTOR / Future', color='#FEF9E7')

ax.plot(loop1_send_x+1.8, Y3, 's', ms=9, color='#FEF3CD', zorder=3)
lbl(ax, loop1_send_x+1.8, Y3+0.4, 'R3', size=7, color=WET3)
wire(ax, loop1_send_x+1.8+0.1, Y3, 7.5, Y3)

box(ax, 8.0, Y3, BW-0.1, BH,
    'PHASE SW 3', 'DPDT Toggle\nPhase Invert', color='#FEF9E7')
wire(ax, 8.0+BW/2-0.05, Y3, 8.8, Y3)
box(ax, 9.4, Y3, BW-0.1, BH,
    'LEVEL 3', 'Vishay 296\n100kΩ audio', color='#FEF9E7')
wire(ax, 9.4+BW/2-0.05, Y3, 10.2, Y3, color=WET3)
lbl(ax, 5.3, Y3+0.45, 'Loop 3 — Experimental (open)', color=WET3, size=7)

# ── SUMMING AMP ───────────────────────────────────────────────────────────────
sum_x = 11.2
sum_y = (Y1+Y2+Y3)/3 + 0.3

# Drop wet signals to summing amp
for (Yw, col) in [(Y1, WET1), (Y2, WET2), (Y3, WET3)]:
    wire(ax, 10.2, Yw, sum_x-BW/2, sum_y, color=col, lw=1.2)

# Drop dry path to summing amp
wire(ax, 14.5, Y_dry, sum_x+BW/2+0.8, sum_y+0.3, color=DRY, lw=1.5)
wire(ax, sum_x+BW/2+0.8, sum_y+0.3, sum_x-BW/2, sum_y, color=DRY, lw=1.5)
lbl(ax, 13.0, Y_dry-0.25, 'R_dry 22kΩ', color=DRY, size=6.5)

box(ax, sum_x, sum_y, BW+0.1, BH+0.2,
    'U2  OPA2134', 'Active Summing Amp\nR_in = Rf = 22kΩ\nUnity gain per channel\n(inverted)', color='#FEF9E7')

# Feedback arc label
lbl(ax, sum_x+0.1, sum_y+BH/2+0.35, 'Rf 22kΩ', color=EDGE, size=6.5)

# ── PHASE CORRECT + OUTPUT BUFFER ────────────────────────────────────────────
pc_x = 13.5
wire(ax, sum_x+BW/2+0.05, sum_y, pc_x-BW/2, sum_y)
box(ax, pc_x, sum_y, BW+0.2, BH,
    'U3  OPA2134', 'Phase Correct\n+ Output Buffer\nR 10kΩ  R_out 100Ω', color='#EBF5FB')

# Output jack
wire(ax, pc_x+BW/2+0.1, sum_y, 16.3, sum_y)
ax.plot(16.5, sum_y, 's', ms=11, color='#D5D8DC', zorder=3)
lbl(ax, 16.5, sum_y+0.55, 'OUTPUT\n→ McIntosh MC100', size=7.5)
lbl(ax, 16.5, sum_y, 'J8', size=7)

# ── PSU INSET ─────────────────────────────────────────────────────────────────
ps_x, ps_y = 15.5, 2.2
psw, psh = 2.2, 2.6
r = mpatches.FancyBboxPatch((ps_x-psw/2, ps_y-psh/2), psw, psh,
    boxstyle='round,pad=0.05', lw=1.5, edgecolor=PWRR, facecolor='#FDEDEC', zorder=3)
ax.add_patch(r)
ax.text(ps_x, ps_y+psh/2-0.15, '±15V POWER SUPPLY',
        ha='center', va='top', fontsize=7.5, fontweight='bold', color=PWRR, zorder=4)
ax.text(ps_x, ps_y-0.1,
        'T1  Antek AN-0115\n    15VA 2×15VAC\n\nBR1 Vishay W02G\n\nU4  LM7815  +15V\nU5  LM7915  −15V\n\nSame spec as\nGhost Spring',
        ha='center', va='center', fontsize=6.5, fontfamily='monospace', zorder=4)

# ── LEGEND ────────────────────────────────────────────────────────────────────
lx, ly = 0.5, 1.5
ax.text(lx, ly+0.3, 'Signal paths:', fontsize=7.5, fontweight='bold')
wire(ax, lx, ly-0.05, lx+0.6, ly-0.05, color=DRY, lw=2)
lbl(ax, lx+1.05, ly-0.05, 'Dry — 100% analog, untouched', ha='left', color=DRY, size=7)
wire(ax, lx, ly-0.38, lx+0.6, ly-0.38, color=WET1, lw=2)
lbl(ax, lx+1.05, ly-0.38, 'Loop 1 — QuadraVerb (delay/mod)', ha='left', color=WET1, size=7)
wire(ax, lx, ly-0.71, lx+0.6, ly-0.71, color=WET2, lw=2)
lbl(ax, lx+1.05, ly-0.71, 'Loop 2 — Ghost Spring (reverb)', ha='left', color=WET2, size=7)
wire(ax, lx, ly-1.04, lx+0.6, ly-1.04, color=WET3, lw=2)
lbl(ax, lx+1.05, ly-1.04, 'Loop 3 — Experimental (open)', ha='left', color=WET3, size=7)

# Footer
lbl(ax, W/2, 0.35,
    'All effects units must be set to 100% Wet / Kill Dry  •  Use Phase switches if blending sounds thin  •  Calibrate Send trims to −6dBFS',
    size=6.5, color='#555')

plt.tight_layout(pad=0.3)
plt.savefig('docs/parallel-mixer/schematic.png', dpi=180, bbox_inches='tight', facecolor=BG)
print("Saved: docs/parallel-mixer/schematic.png")
