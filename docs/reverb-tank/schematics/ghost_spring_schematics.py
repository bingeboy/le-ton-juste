#!/usr/bin/env python3
"""Ghost Spring spring reverb - builder schematics (schemdraw 0.23).

Generates 4 section PNGs:
  /tmp/ghost_sec1.png  Input & Buffer
  /tmp/ghost_sec2.png  Dwell Driver
  /tmp/ghost_sec3.png  Tank Model & Recovery Amp
  /tmp/ghost_sec4.png  Tone & Mix
"""

import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: F401  (Agg backend wiring)

import schemdraw
import schemdraw.elements as elm

# Single source of truth: pull every component value from circuit_params.py so a
# schematic label can never drift from the netlist constant. (Resolve the stages
# dir relative to THIS file so it works from any cwd.)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'stages'))
import circuit_params as cp  # noqa: E402


def new_drawing():
    return schemdraw.Drawing(fontsize=12, inches_per_unit=0.55)


def title(d, text, at=(0, 3.0)):
    """Place a section heading at a fixed point well clear of the circuit."""
    d.add(elm.Label().at(at).label(text, loc='center', halign='left').color('black'))


# ---------------------------------------------------------------------------
# Section 1: Input & Buffer
# ---------------------------------------------------------------------------
def section1():
    d = new_drawing()
    title(d, 'GHOST SPRING - Sec 1: Input and Buffer', at=(0, 4.5))

    # V1 sine source going upward on the left
    src = elm.SourceSin().up().label('V1\nvin', loc='left')
    d.add(src)
    d.add(elm.Ground().at(src.start))
    vin = src.end

    # TVS back-to-back zener pair down to GND, junction = tvs_mid
    d.add(elm.Dot().at(vin).label('vin', loc='left'))
    tvs_top = elm.Line().right().length(1.5).at(vin)
    d.add(tvs_top)
    tvs_node = tvs_top.end
    d.add(elm.Dot().at(tvs_node))
    z1 = elm.Zener().down().at(tvs_node).label('DTVS1a\nBZX84C15L', loc='right')
    d.add(z1)
    d.add(elm.Dot().at(z1.end).label('tvs_mid', loc='left'))
    z2 = elm.Zener().down().at(z1.end).reverse().label('DTVS1b', loc='right')
    d.add(z2)
    d.add(elm.Ground().at(z2.end))

    # Continue right: C_in coupling cap
    cin = elm.Capacitor().right().at(tvs_node).label(f'C_in\n{cp.C_IN}F', loc='top')
    d.add(cin)
    node = cin.end
    d.add(elm.Dot().at(node))

    # R1 bias to GND (at the C_in node)
    r1 = elm.Resistor().down().at(node).label(f'R1\n{cp.R1}', loc='right')
    d.add(r1)
    d.add(elm.Ground().at(r1.end))

    # spine to a clamp column, then to the opamp - keeps branches from stacking
    d.add(elm.Line().right().at(node).length(2))
    clamp = d.here
    d.add(elm.Dot().at(clamp))

    # Clamp diodes: Dclamp_p up to +15V, Dclamp_n down from -15V
    dcp = elm.Diode().up().at(clamp).length(2.2).label('Dclamp_p', loc='right')
    d.add(dcp)
    d.add(elm.Vdd().at(dcp.end).label('+15V'))
    dcn = elm.Diode().down().at(clamp).length(2.2).reverse().label('Dclamp_n', loc='right')
    d.add(dcn)
    d.add(elm.Vss().at(dcn.end).label('-15V'))

    # spine onward to the opamp non-inverting input
    d.add(elm.Line().right().at(clamp).length(1.5))
    opin = d.here

    # U1 opamp, non-inv from node, unity gain
    op = elm.Opamp(leads=True).right().at(opin).anchor('in1').label('U1', loc='center', ofst=(0, 0))
    d.add(op)
    # tie inverting input to output (unity gain)
    d.add(elm.Line().down().at(op.in2).length(1))
    fbk = d.here
    d.add(elm.Line().right().tox(op.out))
    d.add(elm.Dot().at(op.out))
    d.add(elm.Line().up().toy(op.out))

    # supply rails
    d.add(elm.Line().up().at(op.vs).length(1.5))
    d.add(elm.Vdd().label('+15V', loc='top'))
    d.add(elm.Line().down().at(op.vd).length(1.5))
    d.add(elm.Vss().label('-15V', loc='bottom'))

    # R2 100 ohm from U1 out -> u1_buf
    out_tap = elm.Line().right().at(op.out).length(0.6)
    d.add(out_tap)
    d.add(elm.Dot().at(out_tap.end))
    r2 = elm.Resistor().right().at(out_tap.end).label(f'R2\n{cp.R2}', loc='top')
    d.add(r2)
    d.add(elm.Dot(open=True).at(r2.end).label('u1_buf', loc='right'))

    d.save('/tmp/ghost_sec1.png', dpi=180)


# ---------------------------------------------------------------------------
# Section 2: Dwell Driver
# ---------------------------------------------------------------------------
def section2():
    d = new_drawing()
    title(d, 'GHOST SPRING - Sec 2: Dwell Driver', at=(0, 3.5))

    # RV1 Dwell pot drawn as a TRUE 3-terminal divider (NOT a 2-terminal series
    # resistor). Physical wiring: lug3(CW)->u1_buf, lug1(CCW)->GND, lug2(wiper)->
    # C_drive. The pot is a resistive element from u1_buf down to GND with the
    # wiper tapped off the middle; the wiper drives C_drive. A builder following a
    # 2-terminal drawing would mis-wire this as a series pot instead of a divider.
    start = elm.Dot(open=True).at((0, 2.5)).label('lug3 -> u1_buf', loc='left')
    d.add(start)
    # Top half: u1_buf (lug3, CW end) down to the wiper tap node.
    rv1_top = elm.Resistor().down().at(start.start).length(1.5).label(
        f'RV1\n{cp.RV1_TOTAL}', loc='left')
    d.add(rv1_top)
    wiper = rv1_top.end
    d.add(elm.Dot().at(wiper))
    # Bottom half: wiper tap node down to GND (lug1, CCW end).
    rv1_bot = elm.Resistor().down().at(wiper).length(1.5).label(
        'lug1 -> GND', loc='left')
    d.add(rv1_bot)
    d.add(elm.Ground().at(rv1_bot.end))
    # Wiper (lug2) taps off to the right and feeds C_drive.
    d.add(elm.Line().right().at(wiper).length(0.8).color('blue'))
    d.add(elm.Dot().at(d.here).label('lug2 (wiper)\n-> C_drive', loc='top'))
    cdrv = elm.Capacitor().right().at(d.here).label(
        f'C_drive\n{cp.C_DRIVE}F', loc='top')
    d.add(cdrv)

    # wire right to q1_drv
    w = elm.Line().right().at(cdrv.end).length(1)
    d.add(w)
    q1_drv = w.end
    d.add(elm.Dot().at(q1_drv).label('q1_drv', loc='top'))

    # R3 1k from q1_drv to q1_base
    r3 = elm.Resistor().right().at(q1_drv).label(f'R3\n{cp.R3}', loc='top')
    d.add(r3)
    q1_base = r3.end
    d.add(elm.Dot().at(q1_base).label('q1_base', loc='bottom'))

    # R3b 6.8k from +15V down to q1_base
    r3b = elm.Resistor().up().at(q1_base).label(f'R3b\n{cp.R3B}', loc='right')
    d.add(r3b)
    d.add(elm.Vdd().at(r3b.end).label('+15V'))

    # R4 1k from q1_base down to GND
    r4 = elm.Resistor().down().at(q1_base).label(f'R4\n{cp.R4}', loc='right')
    d.add(r4)
    d.add(elm.Ground().at(r4.end))

    # Q1 BD139 NPN, base at q1_base
    q1 = elm.BjtNpn().right().at(q1_base).anchor('base').label('Q1\nBD139', loc='right')
    d.add(q1)

    # Collector goes up -> q1_c
    cwire = elm.Line().up().at(q1.collector).length(1)
    d.add(cwire)
    q1_c = cwire.end
    d.add(elm.Dot().at(q1_c).label('q1_c', loc='right'))

    # L1 and D3 in parallel between +15V and q1_c
    # L1 100mH from +15V to collector (left branch)
    l1 = elm.Inductor().up().at(q1_c).length(2.5).label(f'L1\n{cp.L1}H', loc='left')
    d.add(l1)
    rail = l1.end
    d.add(elm.Dot().at(rail))
    d.add(elm.Vdd().at(rail).label('+15V'))
    # D3 1N4148 flyback, anode=collector, cathode=+15V (parallel branch to the right)
    d.add(elm.Line().right().at(q1_c).length(1.5))
    branch_bot = d.here
    d.add(elm.Dot().at(branch_bot))
    d3 = elm.Diode().up().at(branch_bot).length(2.5).label(f'D3\n{cp.D_1N4148}', loc='right')
    d.add(d3)
    d.add(elm.Line().left().at(d3.end).tox(rail))
    d.add(elm.Dot().at(rail))

    # Emitter goes down -> q1_e
    ewire = elm.Line().down().at(q1.emitter).length(1)
    d.add(ewire)
    q1_e = ewire.end
    d.add(elm.Dot().at(q1_e).label('q1_e', loc='right'))

    # R5 68 from emitter to node, C2 100uF node to GND
    r5 = elm.Resistor().down().at(q1_e).label(f'R5\n{cp.R5}', loc='right')
    d.add(r5)
    enode = r5.end
    d.add(elm.Dot().at(enode))
    c2 = elm.Capacitor2().down().at(enode).label(f'C2\n{cp.C2}F', loc='right')
    d.add(c2)
    d.add(elm.Ground().at(c2.end))

    d.save('/tmp/ghost_sec2.png', dpi=180)


# ---------------------------------------------------------------------------
# Section 3: Tank Model & Recovery Amp
# ---------------------------------------------------------------------------
def section3():
    d = new_drawing()
    title(d, 'GHOST SPRING - Sec 3: Tank Model and Recovery Amp', at=(0, 2.0))

    # --- Tank model (left, vertical ladder) ---
    d.add(elm.Dot(open=True).label('from L1 primary (K=0.98)', loc='left'))
    src = d.here
    # L2 secondary winding down into tank_in
    l2 = elm.Inductor().down().at(src).label(f'L2\n{cp.L2}H\n(secondary)', loc='left')
    d.add(l2)
    tank_in = l2.end
    d.add(elm.Dot().at(tank_in).label('tank_in', loc='left'))

    # R_tank_in 8 from tank_in to GND (branch to the left/down)
    rti = elm.Resistor().down().at(tank_in).label(f'R_tank_in\n{cp.R_TANK_IN}', loc='left')
    d.add(rti)
    d.add(elm.Line().down().at(rti.end).length(0.5))
    d.add(elm.Ground())

    # L_tank 15mH from tank_in to tank_mid (go right then down to keep ladder readable)
    d.add(elm.Line().right().at(tank_in).length(2))
    branch = d.here
    d.add(elm.Dot().at(branch))
    ltank = elm.Inductor().down().at(branch).label(f'L_tank\n{cp.L_TANK}H', loc='right')
    d.add(ltank)
    tank_mid = ltank.end
    d.add(elm.Dot().at(tank_mid).label('tank_mid', loc='left'))

    # Mechanical branch from tank_mid: R_tank_mech -> L_tank_mech -> C_tank_mech -> GND
    rtm = elm.Resistor().down().at(tank_mid).label(f'R_tank_mech\n{cp.R_TANK_MECH}', loc='left')
    d.add(rtm)
    tk_a = rtm.end
    d.add(elm.Dot().at(tk_a).label('tk_a', loc='left'))
    ltm = elm.Inductor().down().at(tk_a).label(f'L_tank_mech\n{cp.L_TANK_MECH}H', loc='left')
    d.add(ltm)
    tk_b = ltm.end
    d.add(elm.Dot().at(tk_b).label('tk_b', loc='left'))
    ctm = elm.Capacitor().down().at(tk_b).label(f'C_tank_mech\n{cp.C_TANK_MECH}F', loc='left')
    d.add(ctm)
    d.add(elm.Line().down().at(ctm.end).length(0.5))
    d.add(elm.Ground())

    # Output branch from tank_mid: R_tank_out -> tank_out, L_tank_out -> GND
    d.add(elm.Line().right().at(tank_mid).length(2.5))
    obranch = d.here
    d.add(elm.Dot().at(tank_mid))
    rto = elm.Resistor().right().at(tank_mid).label(f'R_tank_out\n{cp.R_TANK_OUT}', loc='top')
    d.add(rto)
    tank_out = rto.end
    d.add(elm.Dot().at(tank_out).label('tank_out', loc='top'))
    lto = elm.Inductor().down().at(tank_out).label(f'L_tank_out\n{cp.L_TANK_OUT}H', loc='left')
    d.add(lto)
    d.add(elm.Line().down().at(lto.end).length(0.5))
    d.add(elm.Ground())

    # --- Recovery amp (right) ---
    # C3 470nF from tank_out to u2_in_pos
    c3 = elm.Capacitor().right().at(tank_out).label(f'C3\n{cp.C3}F', loc='top')
    d.add(c3)
    u2_in_pos = c3.end
    d.add(elm.Dot().at(u2_in_pos).label('u2_in_pos', loc='top'))

    # Rbias 100k from u2_in_pos to GND
    rb = elm.Resistor().down().at(u2_in_pos).label(f'Rbias\n{cp.RBIAS}', loc='left')
    d.add(rb)
    d.add(elm.Line().down().at(rb.end).length(0.5))
    d.add(elm.Ground())

    # U2 opamp
    op = elm.Opamp(leads=True).right().at(u2_in_pos).anchor('in1').label('U2', loc='center')
    d.add(op)

    # Inverting input node u2_inv
    d.add(elm.Line().down().at(op.in2).length(1.2))
    u2_inv = d.here
    d.add(elm.Dot().at(u2_inv).label('u2_inv', loc='left'))
    # Ri 470 from u2_inv to GND
    ri = elm.Resistor().down().at(u2_inv).label(f'Ri\n{cp.RI}', loc='left')
    d.add(ri)
    d.add(elm.Line().down().at(ri.end).length(0.5))
    d.add(elm.Ground())

    # Output and Rf feedback
    out_tap = elm.Line().right().at(op.out).length(0.8)
    d.add(out_tap)
    d.add(elm.Dot().at(out_tap.end))
    u2_out = out_tap.end
    # Rf 100k from u2_out back to u2_inv
    d.add(elm.Line().up().at(u2_out).length(2))
    fbtop = d.here
    rf = elm.Resistor().left().at(fbtop).tox(u2_inv).label(f'Rf\n{cp.RF}', loc='top')
    d.add(rf)
    d.add(elm.Line().down().at(rf.end).toy(u2_inv))

    # supply rails
    d.add(elm.Line().up().at(op.vs).length(1.5))
    d.add(elm.Vdd().label('+15V', loc='top'))
    d.add(elm.Line().down().at(op.vd).length(1.5))
    d.add(elm.Vss().label('-15V', loc='bottom'))

    # output label + gain note
    d.add(elm.Line().right().at(u2_out).length(0.8))
    d.add(elm.Dot(open=True).label('u2_out', loc='right'))
    d.add(elm.Label().at((u2_out[0], u2_out[1] - 1.5)).label(
        f'gain = 1 + Rf/Ri = {cp.RECOV_GAIN_SIM:g}x', loc='center'))

    d.save('/tmp/ghost_sec3.png', dpi=180)


# ---------------------------------------------------------------------------
# Section 4: Tone & Mix
# ---------------------------------------------------------------------------
def section4():
    d = new_drawing()
    title(d, 'GHOST SPRING - Sec 4: Tone and Mix', at=(0, 3.0))

    # --- Wet path (tone control), top band ---
    d.add(elm.Dot(open=True).at((0, 0)).label('u2_out (wet)', loc='left'))
    wet_in = d.here
    # C4 100nF -> hpf_out  (HPF fc=312Hz with R6)
    c4 = elm.Capacitor().right().at(wet_in).label(f'C4\n{cp.C4}F', loc='top')
    d.add(c4)
    hpf_out = c4.end
    d.add(elm.Dot().at(hpf_out).label('hpf_out', loc='top'))

    # R6 5.6k from hpf_out to GND (sets HPF corner)
    r6 = elm.Resistor().down().at(hpf_out).label(f'R6\n{cp.R6}', loc='left')
    d.add(r6)
    d.add(elm.Line().down().at(r6.end).length(0.5))
    d.add(elm.Ground())
    d.add(elm.Label().at((hpf_out[0] - 0.2, hpf_out[1] + 1.0)).label(
        f'HPF fc(design)={cp.HPF_CORNER_DESIGN:g}Hz\nfc(loaded sim)={cp.HPF_CORNER_SIM:g}Hz',
        loc='center'))

    # RV3 tone pot 100k: hpf_out through pot to GND, wiper = rv3_wiper
    rv3 = elm.ResistorVar().right().at(hpf_out).length(3).label(f'RV3 tone\n{cp.RV3_TOTAL}', loc='top')
    d.add(rv3)
    d.add(elm.Line().right().at(rv3.end).length(0.6))
    d.add(elm.Ground())
    # wiper tap drops to a labeled stub (routes to mix_wet, drawn as a stub for clarity)
    d.add(elm.Line().down().at(rv3.center).length(1.3).color('blue'))
    d.add(elm.Dot(open=True).color('blue').label('rv3_wiper\n-> mix_wet (0R)', loc='bottom'))

    # --- Mix section (passive 3-terminal blend), lower band ---
    dry_in = (0, -5.0)
    d.add(elm.Dot(open=True).at(dry_in).label('u1_buf (dry)', loc='left'))
    # Rdry 10k from u1_buf to mix_dry
    rdry = elm.Resistor().right().at(dry_in).label(f'Rdry\n{cp.RDRY}', loc='top')
    d.add(rdry)
    mix_dry = rdry.end
    d.add(elm.Dot().at(mix_dry).label('mix_dry', loc='bottom'))

    # RV2 mix pot 100k: lug1=mix_dry, wiper=mix_node, lug3=mix_wet
    rv2 = elm.ResistorVar().right().at(mix_dry).length(3).label(f'RV2 mix\n{cp.RV2_TOTAL}', loc='top')
    d.add(rv2)
    mix_wet = rv2.end
    d.add(elm.Dot().at(mix_wet).label('mix_wet', loc='bottom'))
    # wiper = mix_node (drops down to the output buffer)
    mix_node = (rv2.center[0], rv2.center[1] - 1.2)
    d.add(elm.Line().down().at(rv2.center).length(1.2))
    d.add(elm.Dot().at(mix_node).label('mix_node', loc='left'))

    # C_bright 47pF across the pot (mix_dry to mix_wet), routed well above
    d.add(elm.Line().up().at(mix_dry).length(1.6))
    cbtop_l = d.here
    cb = elm.Capacitor().right().at(cbtop_l).tox(mix_wet).label(f'C_bright\n{cp.C_BRIGHT}F', loc='top')
    d.add(cb)
    d.add(elm.Line().down().at(cb.end).toy(mix_wet))

    # mix_wet receives the tone wiper (matching labeled stub - 0R wire to rv3_wiper)
    d.add(elm.Line().up().at(mix_wet).length(0.9).color('blue'))
    d.add(elm.Dot(open=True).color('blue').label('from rv3_wiper (0R)', loc='right'))

    # --- Output ---
    # U3 opamp non-inv = mix_node, unity gain
    op = elm.Opamp(leads=True).right().at(mix_node).anchor('in1').label('U3', loc='center')
    d.add(op)
    # unity gain: out -> in2
    d.add(elm.Line().down().at(op.in2).length(1))
    d.add(elm.Line().right().tox(op.out))
    d.add(elm.Dot().at(op.out))
    d.add(elm.Line().up().toy(op.out))

    # supply rails
    d.add(elm.Line().up().at(op.vs).length(1.5))
    d.add(elm.Vdd().label('+15V', loc='top'))
    d.add(elm.Line().down().at(op.vd).length(1.5))
    d.add(elm.Vss().label('-15V', loc='bottom'))

    # R7 100 from U3 out
    out_tap = elm.Line().right().at(op.out).length(0.6)
    d.add(out_tap)
    d.add(elm.Dot().at(out_tap.end))
    r7 = elm.Resistor().right().at(out_tap.end).label(f'R7\n{cp.R7}', loc='top')
    d.add(r7)
    vout = r7.end
    d.add(elm.Dot().at(vout))
    # Rload 47k to GND, output v_out
    rload = elm.Resistor().down().at(vout).label(f'Rload\n{cp.RLOAD}', loc='right')
    d.add(rload)
    d.add(elm.Ground().at(rload.end))
    d.add(elm.Line().right().at(vout).length(0.8))
    d.add(elm.Dot(open=True).label('v_out', loc='right'))

    d.save('/tmp/ghost_sec4.png', dpi=180)


# ---------------------------------------------------------------------------
# Full circuit: stitch the 4 section PNGs into a 2x2 grid + annotate
# ---------------------------------------------------------------------------
def section_full():
    """Stitch the 4 section PNGs into a 2x2 grid and annotate the signal flow.

    Layout:
        top-left  = sec1 (Input & Buffer)   top-right = sec2 (Dwell Driver)
        bot-left  = sec3 (Tank & Recovery)  bot-right = sec4 (Tone & Mix)
    """
    from PIL import Image

    sec_paths = {
        'tl': '/tmp/ghost_sec1.png',
        'tr': '/tmp/ghost_sec2.png',
        'bl': '/tmp/ghost_sec3.png',
        'br': '/tmp/ghost_sec4.png',
    }
    imgs = {k: Image.open(p).convert('RGBA') for k, p in sec_paths.items()}

    # Cell size = max width/height across all 4, with internal padding.
    pad = 60
    cell_w = max(im.width for im in imgs.values()) + 2 * pad
    cell_h = max(im.height for im in imgs.values()) + 2 * pad

    # Extra margins: top for title, bottom for the flow note.
    margin_top = 160
    margin_bottom = 120
    margin_side = 40

    grid_w = 2 * cell_w
    grid_h = 2 * cell_h
    canvas_w = grid_w + 2 * margin_side
    canvas_h = grid_h + margin_top + margin_bottom

    canvas = Image.new('RGBA', (canvas_w, canvas_h), (255, 255, 255, 255))

    # Paste each section centered within its grid cell.
    positions = {
        'tl': (0, 0), 'tr': (1, 0),
        'bl': (0, 1), 'br': (1, 1),
    }
    for k, (col, row) in positions.items():
        im = imgs[k]
        cell_x = margin_side + col * cell_w
        cell_y = margin_top + row * cell_h
        off_x = cell_x + (cell_w - im.width) // 2
        off_y = cell_y + (cell_h - im.height) // 2
        canvas.paste(im, (off_x, off_y), im)

    stitched = canvas.convert('RGB')

    # --- annotate with matplotlib on top of the stitched image ---
    import numpy as np  # noqa: F401  (only used if needed; harmless import)
    arr = stitched
    tmp_stitch = '/tmp/ghost_full_stitched.png'
    arr.save(tmp_stitch)

    img = plt.imread(tmp_stitch)
    h, w = img.shape[0], img.shape[1]

    # work in pixel coordinates (origin top-left) for annotate
    fig_w_in = 16
    fig_h_in = fig_w_in * h / w
    fig = plt.figure(figsize=(fig_w_in, fig_h_in))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img, extent=(0, w, h, 0))
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis('off')

    # Helpful pixel landmarks
    col_mid = margin_side + cell_w          # vertical seam between columns
    row_mid = margin_top + cell_h           # horizontal seam between rows
    top_band = margin_top + cell_h * 0.5    # vertical center of top row
    bot_band = margin_top + cell_h * 1.5    # vertical center of bottom row
    left_band = margin_side + cell_w * 0.5  # horizontal center of left col
    right_band = margin_side + cell_w * 1.5  # horizontal center of right col

    arrow = dict(arrowstyle='->', color='#b00020', lw=2.2,
                 shrinkA=0, shrinkB=0)
    txt = dict(color='#b00020', fontsize=15, fontweight='bold',
               ha='center', va='center')

    # Title at the very top
    ax.text(w / 2, margin_top * 0.45, 'GHOST SPRING - Full Circuit',
            color='black', fontsize=26, fontweight='bold',
            ha='center', va='center')

    # sec1 -> sec2 (top row, left to right across the column seam)
    ax.annotate('', xy=(col_mid + cell_w * 0.18, top_band),
                xytext=(col_mid - cell_w * 0.18, top_band),
                arrowprops=arrow)
    ax.text(col_mid, top_band - 28, 'u1_buf ->', **txt)

    # sec2 -> sec3 (top-right to bottom-left, diagonal)
    ax.annotate('', xy=(left_band, row_mid + cell_h * 0.16),
                xytext=(right_band, row_mid - cell_h * 0.16),
                arrowprops=dict(arrowstyle='->', color='#0050b0', lw=2.4,
                                shrinkA=0, shrinkB=0,
                                connectionstyle='arc3,rad=0.15'))
    ax.text(col_mid, row_mid, 'L1 -> L2 (K=0.98)',
            color='#0050b0', fontsize=15, fontweight='bold',
            ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#0050b0'))

    # sec3 -> sec4 (bottom row, left to right across the column seam)
    ax.annotate('', xy=(col_mid + cell_w * 0.18, bot_band),
                xytext=(col_mid - cell_w * 0.18, bot_band),
                arrowprops=arrow)
    ax.text(col_mid, bot_band - 36, 'u2_out (wet) ->', **txt)
    ax.text(col_mid, bot_band + 36, 'u1_buf (dry) ->', **txt)

    # Signal flow note along the bottom
    ax.text(w / 2, h - margin_bottom * 0.45,
            'Signal flow: Input -> Dwell Driver -> Reverb Tank -> '
            'Recovery -> Tone & Mix -> Output',
            color='black', fontsize=15, ha='center', va='center', style='italic')

    out_path = ('/Users/bubblegum/projects/le-ton-juste/docs/reverb-tank/'
                'schematics/ghost_full.png')
    fig.savefig(out_path, dpi=200, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    for name, fn in (('sec1', section1), ('sec2', section2),
                     ('sec3', section3), ('sec4', section4),
                     ('full', section_full)):
        try:
            fn()
            print(f'{name}: OK')
        except Exception as e:  # surface which section failed
            import traceback
            print(f'{name}: FAILED -> {e}')
            traceback.print_exc()
            raise
