#!/usr/bin/env python3
"""Ghost Spring Reverb — Chassis Layout Blueprint"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Palette (vintage spec-sheet, aged paper) ─────────────────────────────────
BG   = '#F4EFE4'
INK  = '#1C1008'
DIM  = '#8B2200'
FILL = '#EDE8DC'
PCB  = '#C8D4A4'
TANK = '#D8D0E8'
PSU  = '#F0D8D0'
COMP = '#D8D0C0'
TOROID = '#E8D8B8'

fig, ax = plt.subplots(figsize=(17, 12), facecolor=BG)
ax.set_xlim(0, 17)
ax.set_ylim(0, 12)
ax.set_aspect('equal')
ax.axis('off')
ax.set_facecolor(BG)


def rect(ax, x, y, w, h, fc=FILL, ec=INK, lw=1.5, zorder=2):
    p = mpatches.Rectangle((x, y), w, h, linewidth=lw, edgecolor=ec,
                            facecolor=fc, zorder=zorder)
    ax.add_patch(p)


def circ(ax, cx, cy, r, fc=COMP, ec=INK, lw=1.2, zorder=3):
    c = plt.Circle((cx, cy), r, linewidth=lw, edgecolor=ec, facecolor=fc,
                   zorder=zorder)
    ax.add_patch(c)


def txt(ax, x, y, s, size=7, color=INK, ha='center', va='center',
        bold=False, mono=False, zorder=6):
    kw = dict(fontsize=size, color=color, ha=ha, va=va, zorder=zorder)
    if bold:
        kw['fontweight'] = 'bold'
    if mono:
        kw['fontfamily'] = 'monospace'
    ax.text(x, y, s, **kw)


def dim_h(ax, x1, x2, y, label):
    """Horizontal dimension line."""
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='<->', color=DIM, lw=0.8))
    txt(ax, (x1 + x2) / 2, y + 0.17, label, size=5.5, color=DIM, mono=True)


def dim_v(ax, x, y1, y2, label):
    """Vertical dimension line."""
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='<->', color=DIM, lw=0.8))
    txt(ax, x + 0.18, (y1 + y2) / 2, label, size=5.5, color=DIM,
        mono=True, ha='left')


# ══════════════════════════════════════════════════════════════════════════════
# TITLE BLOCK (top-right)
# ══════════════════════════════════════════════════════════════════════════════
TB_X, TB_Y, TB_W, TB_H = 12.3, 10.25, 4.5, 1.6
rect(ax, TB_X, TB_Y, TB_W, TB_H, fc='#EDE7D8', ec=INK, lw=1.8)
ax.plot([TB_X, TB_X + TB_W], [TB_Y + 1.1, TB_Y + 1.1], color=INK, lw=0.8)
ax.plot([TB_X, TB_X + TB_W], [TB_Y + 0.55, TB_Y + 0.55], color=INK, lw=0.8)
ax.plot([TB_X + 2.25, TB_X + 2.25], [TB_Y, TB_Y + 1.1], color=INK, lw=0.8)

txt(ax, TB_X + TB_W / 2, TB_Y + 1.45, 'Ghost Spring Reverb Tank',
    size=9.5, bold=True)
txt(ax, TB_X + TB_W / 2, TB_Y + 1.18,
    'Chassis Layout — Internal Top-Down + Panel Elevations', size=6.8)

txt(ax, TB_X + 1.12, TB_Y + 0.82, 'Scale', size=5.5, bold=True)
txt(ax, TB_X + 1.12, TB_Y + 0.60, '1:30  (1 div = 10mm)', size=5.5, mono=True)
txt(ax, TB_X + 3.37, TB_Y + 0.82, 'Rev', size=5.5, bold=True)
txt(ax, TB_X + 3.37, TB_Y + 0.60, 'A  2026-06', size=5.5, mono=True)
txt(ax, TB_X + 1.12, TB_Y + 0.32, 'Chassis', size=5.5, bold=True)
txt(ax, TB_X + 3.37, TB_Y + 0.32, 'Hammond 1455T2201', size=5.5, mono=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION HEADING — TOP VIEW
# ══════════════════════════════════════════════════════════════════════════════
txt(ax, 0.4, 11.75, 'TOP VIEW — Internal Layout (looking down, lid removed)',
    size=9, bold=True, ha='left')
txt(ax, 0.4, 11.48,
    'Hammond 1455T2201  •  483 × 204 × 88mm (2U rack)  •  '
    'Internal clearance ≈ 450 × 170mm  •  Scale 1:30',
    size=6.5, color='#554433', ha='left')

# ══════════════════════════════════════════════════════════════════════════════
# CHASSIS TOP-DOWN VIEW
# Scale: 1 fig-unit = 30mm
# Internal 450mm wide → 15.0 fig-units, 170mm deep → 5.67 fig-units
# Origin: chassis inner bottom-left at (1.0, 5.35)
# ══════════════════════════════════════════════════════════════════════════════
CX0, CY0 = 1.0, 5.35
CW,  CH  = 15.0, 5.67   # 450mm × 170mm at 1:30

WALL = 0.17

# Outer shell (chassis walls)
rect(ax, CX0 - WALL, CY0 - WALL, CW + 2 * WALL, CH + 2 * WALL,
     fc='#B8B0A0', ec=INK, lw=2.8, zorder=1)
# Interior floor
rect(ax, CX0, CY0, CW, CH, fc='#EDE8DC', ec=INK, lw=1.5, zorder=2)

# Cardinal labels
txt(ax, CX0 + CW / 2, CY0 + CH + 0.32, '← REAR PANEL →',
    size=7, bold=True)
txt(ax, CX0 + CW / 2, CY0 - 0.38, '← FRONT PANEL →',
    size=7, bold=True)
txt(ax, CX0 - 0.55, CY0 + CH / 2, 'LEFT', size=6, va='center')
txt(ax, CX0 + CW + 0.45, CY0 + CH / 2, 'RIGHT', size=6, va='center')

# Subtle grid (30mm divisions)
for xi in range(1, 15):
    ax.plot([CX0 + xi, CX0 + xi], [CY0, CY0 + CH],
            color='#C0B8A8', lw=0.28, ls=':', zorder=1)
for yi in range(1, 6):
    ax.plot([CX0, CX0 + CW], [CY0 + yi, CY0 + yi],
            color='#C0B8A8', lw=0.28, ls=':', zorder=1)

# ── SPRING TANK (9AB3C1B) ─────────────────────────────────────────────────────
# 228mm × 61mm → 7.60 × 2.03 fig-units. Rear-left, 10mm clearance each side.
TK_X = CX0 + 0.33
TK_W = 7.60
TK_H = 2.03
TK_Y = CY0 + CH - 0.33 - TK_H   # 10mm from rear wall

rect(ax, TK_X, TK_Y, TK_W, TK_H, fc=TANK, ec='#5030A0', lw=2.0, zorder=3)

txt(ax, TK_X + TK_W / 2, TK_Y + TK_H / 2 + 0.25,
    'SPRING TANK', size=8, bold=True, color='#4020A0')
txt(ax, TK_X + TK_W / 2, TK_Y + TK_H / 2 - 0.02,
    'Accutronics 9AB3C1B', size=6.5, color=INK, mono=True)
txt(ax, TK_X + TK_W / 2, TK_Y + TK_H / 2 - 0.30,
    '3-spring  •  Long decay  •  8Ω input / 2550Ω output',
    size=5.8, color=INK, mono=True)
txt(ax, TK_X + TK_W / 2, TK_Y + 0.12,
    '▼  OPEN SIDE DOWN (faces chassis floor)',
    size=5.5, color=DIM, mono=True)

# Tank RCA connector positions
txt(ax, TK_X + 0.55, TK_Y + TK_H + 0.15, 'IN', size=6, color=DIM, bold=True)
txt(ax, TK_X + 0.55, TK_Y + TK_H + 0.33, 'RCA', size=5.2, color=DIM, mono=True)
txt(ax, TK_X + TK_W - 0.55, TK_Y + TK_H + 0.15, 'OUT', size=6, color=DIM, bold=True)
txt(ax, TK_X + TK_W - 0.55, TK_Y + TK_H + 0.33, 'RCA', size=5.2, color=DIM, mono=True)

# Sorbothane grommet mounting holes (4 corners)
for gx in [TK_X + 0.35, TK_X + TK_W - 0.35]:
    for gy in [TK_Y + 0.22, TK_Y + TK_H - 0.22]:
        circ(ax, gx, gy, 0.10, fc='#907868', ec=INK, lw=0.9, zorder=4)

# ── DRIVER TRANSFORMER (T2 REB3S) ────────────────────────────────────────────
# Small laminated core, ~50×50mm → 1.67×1.67 units. Near tank input end.
DT_X = TK_X + TK_W + 0.4
DT_Y = TK_Y + 0.15
DT_S = 1.0
rect(ax, DT_X, DT_Y, DT_S, DT_S, fc='#F0E8B8', ec='#7A5010', lw=1.6, zorder=3)
txt(ax, DT_X + DT_S / 2, DT_Y + DT_S / 2 + 0.12,
    'T2', size=7, bold=True, color='#7A5010')
txt(ax, DT_X + DT_S / 2, DT_Y + DT_S / 2 - 0.12,
    'REB3S', size=5.8, color=INK, mono=True)

# ── AUDIO PCB (Vector T44, 114 × 89mm → 3.80 × 2.97 fig-units) ──────────────
APCB_X = CX0 + 0.33
APCB_Y = CY0 + 0.40
APCB_W = 3.80
APCB_H = 2.97
rect(ax, APCB_X, APCB_Y, APCB_W, APCB_H, fc=PCB, ec='#2A5010', lw=1.8, zorder=3)

txt(ax, APCB_X + APCB_W / 2, APCB_Y + APCB_H / 2 + 0.38,
    'AUDIO PCB', size=8, bold=True, color='#1A4008')
txt(ax, APCB_X + APCB_W / 2, APCB_Y + APCB_H / 2 + 0.12,
    'Vector T44  FR4 perfboard', size=6, color=INK, mono=True)
txt(ax, APCB_X + APCB_W / 2, APCB_Y + APCB_H / 2 - 0.14,
    '114 × 89mm', size=5.8, color=INK, mono=True)
txt(ax, APCB_X + APCB_W / 2, APCB_Y + APCB_H / 2 - 0.38,
    'U1/U2/U3 OPA2134  •  Q1 BD139', size=5.5, color=INK, mono=True)
txt(ax, APCB_X + APCB_W / 2, APCB_Y + APCB_H / 2 - 0.60,
    'U4 LM7815  •  U5 LM7915  •  BR1 W04G', size=5.5, color=INK, mono=True)

# PCB standoff holes (M3 nylon, 4 corners)
for sx in [APCB_X + 0.22, APCB_X + APCB_W - 0.22]:
    for sy in [APCB_Y + 0.22, APCB_Y + APCB_H - 0.22]:
        circ(ax, sx, sy, 0.11, fc='#A0A890', ec=INK, lw=0.8, zorder=4)

# Molex KK connectors along top edge (facing rear/tank)
for mk in range(3):
    rect(ax, APCB_X + 0.25 + mk * 1.1, APCB_Y + APCB_H - 0.18,
         0.55, 0.18, fc='#F8F4D0', ec='#808040', lw=0.9, zorder=4)
txt(ax, APCB_X + APCB_W / 2, APCB_Y + APCB_H + 0.18,
    'Molex KK connectors (power + signal)', size=5.2, color='#808040', mono=True)

# ── PSU TOROIDAL TRANSFORMER (T1, Triad F-219X, Ø~75mm → 2.5 units dia) ──────
# Rear-right, well separated from spring tank.
T1_CX = CX0 + CW - 1.8
T1_CY = CY0 + CH - 1.55
T1_R  = 1.25
# Clearance zone (dashed circle showing minimum keep-out from tank)
circ(ax, T1_CX, T1_CY, T1_R + 0.35, fc='none',
     ec='#B08040', lw=0.6, zorder=2)
circ(ax, T1_CX, T1_CY, T1_R, fc=TOROID, ec='#604020', lw=2.0, zorder=3)
circ(ax, T1_CX, T1_CY, 0.38, fc='#A09080', ec='#604020', lw=1.2, zorder=4)
txt(ax, T1_CX, T1_CY + 0.22, 'T1', size=7.5, bold=True, color='#604020')
txt(ax, T1_CX, T1_CY - 0.08, 'Triad F-219X', size=6, color=INK, mono=True)
txt(ax, T1_CX, T1_CY - 0.33, '30VA toroidal', size=5.8, color=INK, mono=True)
txt(ax, T1_CX, T1_CY - T1_R - 0.25, 'Ø75mm', size=5.5, color=DIM)

# Regulator heatsinks on right chassis wall
rect(ax, CX0 + CW - 0.17, T1_CY - 1.8, 0.17, 0.75,
     fc='#C0A890', ec=INK, lw=1.0, zorder=4)
txt(ax, CX0 + CW + 0.22, T1_CY - 1.43, 'HS\nU4\nU5', size=5, color=DIM,
    ha='left', mono=True)

# ── STAR GROUND POINT ────────────────────────────────────────────────────────
SG_X = CX0 + 6.0
SG_Y = CY0 + 2.0
circ(ax, SG_X, SG_Y, 0.15, fc='#F0D030', ec='#806820', lw=1.8, zorder=5)
ax.plot(SG_X, SG_Y, '+', ms=9, color='#806820', zorder=6, mew=1.8)
txt(ax, SG_X, SG_Y + 0.32, 'STAR GND', size=5.8, color='#806820', bold=True)
txt(ax, SG_X, SG_Y - 0.30, 'M3 chassis bolt', size=5, color=INK, mono=True)

# Ground leads (dashed) from PCBs to star ground
ax.plot([APCB_X + APCB_W / 2, SG_X], [APCB_Y, SG_Y],
        color='#806820', lw=0.7, ls='--', zorder=2)
ax.plot([T1_CX, SG_X], [T1_CY - T1_R, SG_Y],
        color='#806820', lw=0.7, ls='--', zorder=2)
txt(ax, (APCB_X + APCB_W / 2 + SG_X) / 2 + 0.3,
    (APCB_Y + SG_Y) / 2 + 0.1, 'chassis\nground', size=5, color='#806820', mono=True)

# ── SIGNAL WIRES ─────────────────────────────────────────────────────────────
# Drive path: Audio PCB right edge → T2 REB3S → Tank input (Belden 8451)
ax.annotate('', xy=(DT_X, DT_Y + DT_S / 2),
            xytext=(APCB_X + APCB_W, APCB_Y + APCB_H * 0.75),
            arrowprops=dict(arrowstyle='->', color='#1A5276', lw=1.1,
                            connectionstyle='arc3,rad=0.25'))
txt(ax, APCB_X + APCB_W + 1.05, APCB_Y + APCB_H * 0.75 + 0.22,
    'DRIVE (Belden 8451\nshielded)', size=5.5, color='#1A5276', mono=True)

# T2 → Tank input
ax.annotate('', xy=(TK_X + 0.55, TK_Y),
            xytext=(DT_X + DT_S / 2, DT_Y + DT_S),
            arrowprops=dict(arrowstyle='->', color='#1A5276', lw=1.1,
                            connectionstyle='arc3,rad=-0.2'))

# Recovery path: Tank output → Audio PCB (critical — shielded, short)
ax.annotate('', xy=(APCB_X + APCB_W, APCB_Y + APCB_H * 0.30),
            xytext=(TK_X + TK_W - 0.55, TK_Y),
            arrowprops=dict(arrowstyle='->', color='#1D8348', lw=1.3,
                            connectionstyle='arc3,rad=0.3',
                            linestyle='dashed'))
txt(ax, TK_X + TK_W - 0.55 + 1.6, TK_Y - 0.85,
    'RECOVERY — shielded\n(shield to GND at PCB end only)',
    size=5.5, color='#1D8348', mono=True)

# Power wire: T1 → Audio PCB (rough path)
ax.plot([T1_CX - T1_R, APCB_X + APCB_W + 0.5,
         APCB_X + APCB_W, APCB_X + APCB_W],
        [T1_CY, T1_CY - 2.0, APCB_Y + APCB_H * 0.5, APCB_Y + APCB_H * 0.5],
        color='#922B21', lw=0.9, ls='dotted', zorder=2)
txt(ax, APCB_X + APCB_W + 1.1, APCB_Y + APCB_H * 0.5 - 0.2,
    '±15V (Molex KK)', size=5.5, color='#922B21', mono=True)

# ── CLEARANCE NOTE: tank–toroid minimum ──────────────────────────────────────
# Measure gap between tank right edge and toroid left edge
gap_x1 = TK_X + TK_W + 0.1
gap_x2 = T1_CX - T1_R - 0.1
gap_y  = CY0 + CH - 0.3
ax.plot([gap_x1, gap_x2], [gap_y, gap_y], color=DIM, lw=0.8, ls=':', zorder=4)
txt(ax, (gap_x1 + gap_x2) / 2, gap_y + 0.20,
    '⚠  ≥80mm clearance required', size=6, color=DIM, bold=True)
txt(ax, (gap_x1 + gap_x2) / 2, gap_y - 0.15,
    '(60Hz coupling into springs)', size=5.5, color=DIM, mono=True)

# ── DIMENSION LINES ──────────────────────────────────────────────────────────
dim_h(ax, CX0, CX0 + CW, CY0 - 0.55, '450mm (usable internal width)')
dim_v(ax, CX0 - 0.65, CY0, CY0 + CH, '170mm usable depth')
dim_h(ax, TK_X, TK_X + TK_W, TK_Y - 0.42, '228mm')
dim_h(ax, APCB_X, APCB_X + APCB_W, CY0 + 0.10, '114mm')

# ══════════════════════════════════════════════════════════════════════════════
# FRONT PANEL ELEVATION
# 483mm wide × 88mm tall (2U). Scale: FPW/483 fig-units per mm.
# Position: x=0.4–8.4, y=2.7–4.16
# ══════════════════════════════════════════════════════════════════════════════
txt(ax, 0.4, 4.7, 'FRONT PANEL ELEVATION — 483 × 88mm (2U)',
    size=8, bold=True, ha='left')

FP_X, FP_Y = 0.4, 2.82
FP_W, FP_H = 8.0, 1.46
FP_S = FP_W / 483          # fig-units per mm
FP_CY = FP_Y + FP_H / 2   # panel centre line

rect(ax, FP_X, FP_Y, FP_W, FP_H, fc='#D4D0C4', ec=INK, lw=2.2)

# Rack ears
for ex in [FP_X + 0.30, FP_X + FP_W - 0.30]:
    for ey in [FP_Y + 0.26, FP_Y + FP_H - 0.26]:
        circ(ax, ex, ey, 0.09, fc='#A09080', ec=INK, lw=0.8)

# Component positions (mm from left edge)
fp_items = [
    (50,  'IN',    '¼" TS', 'jack', '#C8E8F4', 0.155),
    (140, 'DWELL', '10kΩ',  'pot',  '#ECD8B0', 0.220),
    (242, 'MIX',   '100kΩ', 'pot',  '#ECD8B0', 0.220),
    (344, 'TONE',  '100kΩ', 'pot',  '#ECD8B0', 0.220),
    (433, 'OUT',   '¼" TS', 'jack', '#C8E8F4', 0.155),
    (465, '●',     'power', 'LED',  '#F0F880', 0.085),
]

for mm, name, val, kind, fc, r in fp_items:
    fx = FP_X + mm * FP_S
    circ(ax, fx, FP_CY, r, fc=fc, ec=INK, lw=1.2, zorder=4)
    txt(ax, fx, FP_Y + FP_H + 0.18, name, size=6.5, bold=True)
    txt(ax, fx, FP_Y + FP_H + 0.36, val, size=5.2, color='#554433', mono=True)
    txt(ax, fx, FP_Y - 0.18, kind, size=5.2, color='#554433', mono=True)
    ax.plot([fx, fx], [FP_Y, FP_Y - 0.08], color=DIM, lw=0.5)
    txt(ax, fx, FP_Y - 0.35, f'{mm}mm', size=4.8, color=DIM, mono=True)

# Overall dimension
dim_h(ax, FP_X, FP_X + FP_W, FP_Y - 0.60, '483mm')

# ══════════════════════════════════════════════════════════════════════════════
# REAR PANEL ELEVATION — same scale, same height
# Position: x=8.7–16.7, y=2.7–4.16
# ══════════════════════════════════════════════════════════════════════════════
txt(ax, 8.7, 4.7, 'REAR PANEL ELEVATION — 483 × 88mm (2U)',
    size=8, bold=True, ha='left')

RP_X, RP_Y = 8.7, 2.82
RP_W, RP_H = 8.0, 1.46
RP_S = RP_W / 483
RP_CY = RP_Y + RP_H / 2

rect(ax, RP_X, RP_Y, RP_W, RP_H, fc='#D4D0C4', ec=INK, lw=2.2)

# Rack ears
for ex in [RP_X + 0.30, RP_X + RP_W - 0.30]:
    for ey in [RP_Y + 0.26, RP_Y + RP_H - 0.26]:
        circ(ax, ex, ey, 0.09, fc='#A09080', ec=INK, lw=0.8)

# IEC C14 inlet (rectangular cutout)
IEC_mm = 65
IEC_X  = RP_X + IEC_mm * RP_S
IEC_W, IEC_H = 0.65, 1.02
rect(ax, IEC_X - IEC_W / 2, RP_CY - IEC_H / 2, IEC_W, IEC_H,
     fc='#A8A098', ec=INK, lw=1.3, zorder=4)
txt(ax, IEC_X, RP_CY + 0.06, 'Schurter', size=5.2, color='#F0ECE0', mono=True)
txt(ax, IEC_X, RP_CY - 0.18, '5110.1052', size=5.0, color='#F0ECE0', mono=True)
txt(ax, IEC_X, RP_Y + RP_H + 0.18, 'IEC INLET', size=6.5, bold=True)
txt(ax, IEC_X, RP_Y + RP_H + 0.36, 'EMI filtered + fuse', size=5.2, color='#554433', mono=True)
txt(ax, IEC_X, RP_Y - 0.35, f'{IEC_mm}mm', size=4.8, color=DIM, mono=True)

# Power rocker switch
PWR_mm = 185
PWR_X  = RP_X + PWR_mm * RP_S
PWR_W, PWR_H = 0.40, 0.52
rect(ax, PWR_X - PWR_W / 2, RP_CY - PWR_H / 2, PWR_W, PWR_H,
     fc='#E0D8C8', ec=INK, lw=1.2, zorder=4)
txt(ax, PWR_X, RP_CY + 0.06, '○ / I', size=6.5, color=INK)
txt(ax, PWR_X, RP_CY - 0.15, '6A/250V', size=4.8, color=INK, mono=True)
txt(ax, PWR_X, RP_Y + RP_H + 0.18, 'POWER', size=6.5, bold=True)
txt(ax, PWR_X, RP_Y + RP_H + 0.36, 'rocker switch', size=5.2, color='#554433', mono=True)
txt(ax, PWR_X, RP_Y - 0.35, f'{PWR_mm}mm', size=4.8, color=DIM, mono=True)

# Ground lift toggle
GL_mm = 260
GL_X  = RP_X + GL_mm * RP_S
circ(ax, GL_X, RP_CY, 0.13, fc='#E8D8C0', ec=INK, lw=1.2, zorder=4)
ax.plot([GL_X, GL_X], [RP_CY + 0.13, RP_CY + 0.40],
        color=INK, lw=1.8, zorder=5)
txt(ax, GL_X, RP_Y + RP_H + 0.18, 'GND LIFT', size=6.5, bold=True)
txt(ax, GL_X, RP_Y + RP_H + 0.36, 'SPDT mini toggle', size=5.2, color='#554433', mono=True)
txt(ax, GL_X, RP_Y - 0.18, 'LIFT / GND', size=5.2, color='#554433', mono=True)
txt(ax, GL_X, RP_Y - 0.35, f'{GL_mm}mm', size=4.8, color=DIM, mono=True)

dim_h(ax, RP_X, RP_X + RP_W, RP_Y - 0.60, '483mm')

# ══════════════════════════════════════════════════════════════════════════════
# BUILD NOTES (bottom strip)
# ══════════════════════════════════════════════════════════════════════════════
notes = [
    ('①', 'Spring tank open side faces chassis FLOOR.  '
          'Mount via 4× Sorbothane Shore-30 grommets on M3 standoffs.'),
    ('②', 'Toroidal T1 minimum 80mm from tank.  '
          'Orient core gap away from tank to minimise 60Hz hum coupling.'),
    ('③', 'Recovery wire (tank out → U2 pin 2) must be Belden 8451 shielded.  '
          'Ground shield at PCB end only — floating at tank end.'),
    ('④', 'Star ground: single M3 chassis bolt.  '
          'All PCB grounds, shield drains, and safety earth bond to this one point.'),
    ('⑤', 'Phase check on first power-up: if reverb sounds hollow, '
          'swap the two RCA wires at the tank OUTPUT Molex connector.'),
]

txt(ax, 0.4, 2.10, 'BUILD NOTES', size=7.5, bold=True, ha='left', color=INK)
for i, (num, note) in enumerate(notes):
    y = 1.82 - i * 0.29
    txt(ax, 0.4, y, num, size=6.5, bold=True, color=DIM, ha='left', va='top')
    txt(ax, 0.72, y, note, size=5.8, color='#2A1A08', ha='left', va='top', mono=True)

# ──────────────────────────────────────────────────────────────────────────────
# LEGEND
# ──────────────────────────────────────────────────────────────────────────────
LG_X, LG_Y = 9.2, 2.10
txt(ax, LG_X, LG_Y, 'WIRING', size=7, bold=True, ha='left')
ax.plot([LG_X, LG_X + 0.7], [LG_Y - 0.25, LG_Y - 0.25],
        color='#1A5276', lw=1.5)
txt(ax, LG_X + 0.82, LG_Y - 0.25, 'Drive path (shielded)',
    size=6, color='#1A5276', ha='left', va='center')
ax.plot([LG_X, LG_X + 0.7], [LG_Y - 0.50, LG_Y - 0.50],
        color='#1D8348', lw=1.5, ls='dashed')
txt(ax, LG_X + 0.82, LG_Y - 0.50, 'Recovery path (shielded, critical)',
    size=6, color='#1D8348', ha='left', va='center')
ax.plot([LG_X, LG_X + 0.7], [LG_Y - 0.75, LG_Y - 0.75],
        color='#922B21', lw=1.5, ls='dotted')
txt(ax, LG_X + 0.82, LG_Y - 0.75, 'Power distribution (±15V)',
    size=6, color='#922B21', ha='left', va='center')
ax.plot([LG_X, LG_X + 0.7], [LG_Y - 1.00, LG_Y - 1.00],
        color='#806820', lw=1.2, ls='dashed')
txt(ax, LG_X + 0.82, LG_Y - 1.00, 'Chassis ground bonds',
    size=6, color='#806820', ha='left', va='center')

# ──────────────────────────────────────────────────────────────────────────────
# OUTER BORDER
# ──────────────────────────────────────────────────────────────────────────────
border = mpatches.Rectangle(
    (0.10, 0.08), 16.80, 11.84,
    linewidth=2.2, edgecolor='#7A6548', facecolor='none', zorder=10)
ax.add_patch(border)
# Inner border line
inner = mpatches.Rectangle(
    (0.18, 0.16), 16.64, 11.68,
    linewidth=0.8, edgecolor='#9A8568', facecolor='none', zorder=10)
ax.add_patch(inner)

plt.tight_layout(pad=0.15)
plt.savefig('docs/reverb-tank/layout.png', dpi=180, bbox_inches='tight',
            facecolor=BG)
print("Saved: docs/reverb-tank/layout.png")
