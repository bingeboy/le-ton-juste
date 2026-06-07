#!/usr/bin/env python3
"""Single source of truth for Ghost Spring component values. Import from
generator scripts instead of hardcoding.

THE CASCADE
-----------
    circuit_params.py  <- edit values HERE (the only place)
           |
           v
    gen_stage*.py            -> stage_0*.net   (SPICE netlists)
    gen_circuit_params_md.py -> circuit-params.md  (human-readable table)
           |
           v
    validate.py  (checks netlist + circuit-params.md + test-assertions.md
                  all agree with these constants; the CI gate)
    sync.py      (regenerates every netlist + circuit-params.md, then
                  runs validate.py; one command to re-cascade)

Edit circuit_params.py, then run sync.py. Do not edit circuit-params.md by
hand -- it is generated.

This module is the single source of truth. circuit-params.md (human-readable
table) and stage_06_full.net (the SPICE netlist) are both GENERATED from it and
must agree with it. To change a value: edit it HERE, then run
`python docs/reverb-tank/sync.py`, which regenerates every netlist and
circuit-params.md and re-validates. Never hand-edit a generated netlist or
circuit-params.md.

Values are SPICE-formatted strings (e.g. "6.8k", "100n", "2200u") because the
generator scripts emit them verbatim into netlist cards. Operating-point
targets and tolerances are floats/tuples for programmatic checks.

Naming follows the netlist instance names. Where the schematic/BOM designator
differs from the netlist instance, the netlist name is used as the key and the
difference is noted in a comment (e.g. C1 == C_DRIVE, F2/F3 == RF2/RF3).
"""

# ============================================================================
# RESISTORS (Ohms, SPICE-formatted strings)
# ============================================================================
R1        = "1Meg"   # U1(+) FET DC return / 1M input Z (shunt after C_in)
R2        = "100"    # U1 output isolation
R3        = "1k"     # Dwell wiper -> Q1 base drive resistor
R3B       = "6.8k"   # upper leg of Q1 base bias divider (+15V -> base)
R4        = "1k"     # lower leg of Q1 base bias divider (base -> GND)
R5        = "68"     # Q1 emitter degeneration (sets Ic, thermal stability)
RI        = "470"    # U2 gain-set lower leg
RF        = "100k"   # U2 feedback upper leg; gain = 1 + RF/RI
R6        = "5.6k"   # wet HPF resistor (with C4)
RBIAS     = "100k"   # U2 (+) input bias / recovery input impedance
RDRY      = "10k"    # dry-path series R: u1_buf -> RV2 CCW end (mix_dry)
R7        = "100"    # U3 output isolation
RLOAD     = "47k"    # MC100 RCA input load (downstream model, not a fitted part)

# Tank lumped-model resistors (SPICE modelling, not purchased parts)
R_TANK_IN   = "8"     # tank input impedance (8 ohm side)
R_TANK_MECH = "200"   # tank mechanical-resonance series R
R_TANK_OUT  = "2550"  # tank output impedance (2550 ohm side)

# Power-supply resistors
R_BLEED1 = "10k"   # bleed across C11 (+15V bulk), 1W flameproof
R_BLEED2 = "10k"   # bleed across C12 (-15V bulk), 1W flameproof
RF2      = "0.5"   # F2 polyfuse (MF-R050) model, +15V rail
RF3      = "0.5"   # F3 polyfuse (MF-R050) model, -15V rail

# Potentiometers, modelled as two series halves (value = each half)
RV1A = "5k"   # Dwell upper half   (RV1 = 10k linear total)
RV1B = "5k"   # Dwell lower half
RV2A = "50k"  # Mix upper half     (RV2 = 100k audio total)
RV2B = "50k"  # Mix lower half
RV3A = "50k"  # Tone upper half    (RV3 = 100k audio total)
RV3B = "50k"  # Tone lower half

# ============================================================================
# CAPACITORS (SPICE-formatted strings)
# ============================================================================
C_IN     = "1u"    # input coupling at the jack (before U1)
C_DRIVE  = "1u"    # BOM ref C1: Dwell wiper -> Q1 base coupling
C2       = "100u"  # Q1 emitter bypass (across R5)
C3       = "470n"  # tank output -> U2 input DC block
C4       = "100n"  # wet HPF cap (with R6)
C_BRIGHT = "47p"   # bright cap across Mix pot
C_DRIVE_OUT = "1u"  # Stage-2-only collector->tank DC block (removed once REB3S transformer is added in Stage 3; not a final BOM part)

# Op-amp supply decoupling. All four are the same HF bypass value; DECOUPLE_VAL
# names that shared value so validate.py can check the cap VALUES (not just that
# the caps are present on the right rails). A decoupling cap that is present but
# wrong-valued (e.g. 100p instead of 100n) bypasses nothing at audio HF and
# invites instability that a presence-only check never sees.
DECOUPLE_VAL = "100n"
C5 = DECOUPLE_VAL   # U1/U2 +15V
C6 = DECOUPLE_VAL   # U1/U2 -15V
C7 = DECOUPLE_VAL   # U3 +15V
C8 = DECOUPLE_VAL   # U3 -15V

# Power-supply caps
C11 = "2200u"  # +ve unregulated bulk filter (50V part)
C12 = "2200u"  # -ve unregulated bulk filter (50V part)
C13 = "100u"   # U4 (LM7815) output cap
C14 = "100u"   # U5 (LM7915) output cap
C15 = "10u"    # +15V board-entry bulk decoupling
C16 = "10u"    # -15V board-entry bulk decoupling
C17 = "100n"   # U4 output HF bypass
C18 = "100n"   # U5 output HF bypass

C_TANK_MECH = "10n"  # tank mechanical-resonance cap (lumped model)

# ============================================================================
# INDUCTORS / COUPLED MAGNETICS (lumped models, all Rser=0)
# ============================================================================
L1          = "100m"  # REB3S primary (Q1 collector -> +15V)
L2          = "5m"    # REB3S 8 ohm secondary (into tank input)
K1          = "0.98"  # REB3S coupling coefficient (L1 <-> L2)
L_TANK      = "15m"   # tank input series inductance
L_TANK_MECH = "500m"  # tank mechanical-resonance inductance
L_TANK_OUT  = "2"     # tank output inductance (2H)

# ============================================================================
# SEMICONDUCTOR MODELS (SPICE .model / subckt bodies)
# ============================================================================
BD139_MODEL     = "NPN(Is=1e-14 Bf=100 Vaf=50 Rb=1 Rc=0.1 Re=0.05 Cje=30p Cjc=15p)"
BZX84C15L_MODEL = "D(BV=15 N=1.6 Rs=2 IBV=5m Cjo=80p Iave=200m)"
DN4007_MODEL    = "D(Is=14.1n N=1.984 Rs=33.9m Ikf=94.8 Cjo=51.7p M=0.333 Vj=0.7 Bv=1000 Ibv=10u)"

# Op-amp (UniversalOpAmp2 level2) parameter strings
OPA_PARAMS = "Avol=1Meg GBW=8Meg Slew=20Meg Ilimit=25m Rail=0 Rinc=1T"
OPA_PARAMS_NET = ("level2 Avol=1Meg GBW=8Meg Slew=20Meg Ilimit=25m "
                  "Rail=0 Rinc=1T Vos=0 En=0 Enk=0 In=0 "
                  "Ink=0 Rin=500Meg")

# Behavioural linear-regulator subckts (no 78xx/79xx ships with this LTspice)
LM78XX_SUBCKT = [
    ".subckt LM78xx IN COM OUT",
    ".param Vout=15",
    "B1 OUT COM V=min(V(IN,COM)-2, {Vout})",
    ".ends LM78xx",
]
LM79XX_SUBCKT = [
    ".subckt LM79xx IN COM OUT",
    ".param Vout=15",
    "B1 OUT COM V=max(V(IN,COM)+2, -{Vout})",
    ".ends LM79xx",
]

# ============================================================================
# POWER SUPPLY (transformer / rails)
# ============================================================================
VSEC_PEAK   = "21.2"            # T1 secondary peak = 15Vrms * sqrt(2)
VSEC_SINE   = "SINE(0 21.2 60)"  # one half of the 15-0-15 secondary (0V offset, 21.2Vpk, 60Hz mains)
RAIL_POS    = 15.0            # nominal +15V regulated rail
RAIL_NEG    = -15.0           # nominal -15V regulated rail
UNREG_BUS   = 20.4           # nominal unregulated bus (avg, ~peak - 2 Vf)
VRAIL_IDEAL = "15"           # ideal +/-15V bench-rail source value (Stages 1-4, Stage 6 ac)

# ============================================================================
# SIGNAL SOURCE / STIMULI (SPICE source strings)
# ============================================================================
V1_SINE_NORMAL   = "SINE(0 100m 1k)"  # normal 100mVpk 1kHz test stimulus
V1_SINE_OVERLOAD = "SINE(0 10 1k)"    # 20Vpp clamp-window overload (Stage 4)
V1_SINE_KILLED   = "SINE(0 0 1k)"     # signal killed -> pure DC bias (op variant)
V1_AC_TOKEN      = "AC 1"             # small-signal AC drive token on V1

# ============================================================================
# DIODE MODEL NAMES (the small-signal/clamp parts come from standard.dio)
# ============================================================================
D_1N4148 = "1N4148"  # flyback (D3) + input clamp pair (Dclamp_p/Dclamp_n)

# ============================================================================
# OPERATING-POINT TARGETS + TOLERANCES (verified by stage_06_full sim)
# ============================================================================
# Q1 (BD139) bias
Q1_VE_SIM        = 1.092          # verified sim V(q1_e)
Q1_VE_FIRSTORDER = 1.22           # first-order estimate
Q1_VE_WINDOW     = (1.0, 1.4)     # pass band, volts
Q1_IC_SIM        = 16e-3          # verified sim Ic, amps
Q1_IC_FIRSTORDER = 18e-3          # first-order estimate
Q1_IC_WINDOW     = (10e-3, 26e-3)  # pass band, amps
Q1_IC_ERR_MAX    = 0.10           # max |q1_ic_calc - q1_ic|/q1_ic (10% cross-check tol)
# Q1 must stay in the FORWARD-ACTIVE region (not saturated): for an NPN the
# collector must sit ABOVE the base by at least a margin. Vce = V(q1_c) - V(q1_e)
# must stay well above Vce(sat) (~0.2V), and Vcb = V(q1_c) - V(q1_base) must be
# >= 0 (collector at/above base). If Q1 saturates the transformer drive distorts
# badly (flat-topped collector swing). q1_vc is read at the same 190-200ms tail.
Q1_VC_SIM        = 14.6            # verified sim V(q1_c) (collector near +15V rail)
Q1_VC_WINDOW     = (3.0, 15.2)    # pass band, volts: comfortably above Vce(sat)+Ve
                                  #   (~1.3V) yet not above the +15V rail (+headroom)
Q1_VCE_MIN       = 1.0            # min Vce = V(q1_c)-V(q1_e); >> Vce(sat) 0.2V = active
Q1_VCB_MIN       = 0.0            # min Vcb = V(q1_c)-V(q1_base); >=0 keeps CBJ reverse-
                                  #   biased (the saturation guard)

# Op-amp output DC offsets (all share the same window)
OFFSET_WINDOW    = (-10e-3, 10e-3)  # +/-10 mV
OFF_U1_SIM       = 0.0            # ~0 V (+0.8 fV)
OFF_U2_SIM       = 0.47e-3        # +0.47 mV (settles from ~72mV @20ms)
OFF_U3_SIM       = -0.35e-6       # -0.35 uV

# U2 non-inverting input DC bias. The recovery + input (u2_in_pos) is held to 0V
# by Rbias (100k to GND); C3 (470n) blocks any tank/rail DC from leaking in. If
# Rbias opened or a rail leaked through, this node would float to a DC offset that
# the 214x stage multiplies into U2 clipping. Same +/-10 mV window as the op-amp
# outputs (measured AVG over the 190-200ms tail in the op netlist).
U2_INPOS_BIAS_WINDOW = (-10e-3, 10e-3)  # +/-10 mV DC at u2_in_pos
U2_INPOS_BIAS_SIM    = 0.0              # ~0 V (Rbias holds it; C3 blocks DC)

# Rails
RAIL_POS_WINDOW  = (14.85, 15.15)   # volts
RAIL_NEG_WINDOW  = (-15.15, -14.85)  # volts
RIPPLE_MAX_PP    = 10e-3           # < 10 mVpp on each rail

# Unregulated-bus headroom. The 78xx/79xx need their input >= Vout + ~2V dropout
# to stay IN regulation. The bulk caps hold pos_rect / neg_rect near the rectified
# peak (~19V); if the bus sagged below ~17V the regulator would drop out and the
# rail would follow the ripple. The PSU netlists measure unreg_pos/unreg_neg but
# nothing gated them -> a silent dropout. |V(bus)| must clear this floor.
UNREG_HEADROOM_MIN = 17.0          # V; |unreg bus| floor = Vout(15) + dropout(2)

# ============================================================================
# KEY AC PARAMETERS (verified by stage_06_full sim)
# ============================================================================
# U1 input buffer is a unity-gain follower: V(u1_buf) must track V(vin) (~1.0x).
# Measured in the ac netlist as mag(V(u1_buf)/V(vin)) AT=1k. R2 (100Ω) into the
# Dwell pot / Rdry load drops a hair, so the window allows a small loss. A dead or
# wrongly-wired U1 (e.g. gain stage, or out-of-loop) would land far outside this.
U1_BUF_GAIN_SIM    = 1.0           # V/V @1kHz (unity follower through R2)
U1_BUF_GAIN_WINDOW = (0.90, 1.05)  # V/V pass band for the U1 buffer

RECOV_GAIN_SIM     = 213.8         # V/V @1kHz (= 1 + RF/RI = 1 + 100000/470 = 213.766..., nearest tenth)
RECOV_GAIN_DB_SIM  = 46.59         # dB
RECOV_GAIN_WINDOW  = (205.0, 225.0)  # V/V pass band (1% Rf/Ri worst-case ~208-219, +meas error)
# recov_gain_db (Stage 6 ac): the recovery stage gain measured END-TO-END across
# U2 in dB, i.e. 20*log10(V(u2_out)/V(u2_in_pos)). This is the SAME quantity as
# RECOV_GAIN_DB_SIM above, just the pass target + window used by the .meas
# recov_gain_db directive. It is NOT the full vin->v_out chain gain (that is only
# ~15-21 dB: the dry path attenuates and the wet path is tank/HPF-shaped), so the
# .meas measures U2 directly. Window is +/-2 dB about the 46.59 dB sim result.
CHAIN_GAIN_DB_SIM    = 46.59       # dB, recovery stage gain end-to-end (= recov_gain 213.8x)
CHAIN_GAIN_DB_WINDOW = (44.6, 48.6)  # +/-2dB about CHAIN_GAIN_DB_SIM
HPF_CORNER_SIM     = 312.0         # Hz (measured R6/C4 transfer)
HPF_CORNER_DESIGN  = 284.0         # Hz = 1/(2*pi*R6*C4)
HPF_CORNER_WINDOW  = (250.0, 320.0)  # Hz pass band
TANK_PEAK_WINDOW   = (1e3, 5e3)    # Hz "drip" resonance band (~2-3kHz)
VOUT_PK_SIM        = 1.16          # V, 100mVpk in
VOUT_PK_MAX        = 14.0          # V clipping limit
OSC_RATIO_SIM      = 0.9998        # RMS_late / RMS_early
OSC_RATIO_MAX      = 1.05

# Input-clamp pass criteria
CLAMP_IDLE_MAX     = 1e-6          # < 1 uA at idle
CLAMP_VOLTAGE      = 15.7          # ~ clamp threshold at U1(+), volts
U1POS_CLAMP_WINDOW = (-16.0, 16.0)  # V under 20Vpp overload
# Under the 20Vpp overload (Stage 4 'overload' tran), the clamp diodes MUST
# conduct on the peaks (proving the clamp engages). Dclamp_p carries forward
# (positive) current on the +peak; Dclamp_n forward current shows as a NEGATIVE
# I(Dclamp_n) (it is wired -15V->u1_pos, so conduction is the -direction). The
# guard is only that they conduct AT ALL (> 0 / < 0), not a magnitude.
CLAMP_OVERLOAD_P_MIN = 0.0        # I(Dclamp_p) peak MUST be > 0 under overload
CLAMP_OVERLOAD_N_MAX = 0.0        # I(Dclamp_n) peak MUST be < 0 under overload
# At idle the negative clamp (Dclamp_n, wired -15V->u1_pos) is reverse-biased,
# so its current floor is just below 0 (same |I| < 1uA reasoning as clamp_p_i,
# but the sign convention makes it a NEGATIVE-side floor).
CLAMP_N_IDLE_MIN = -1e-6          # I(Dclamp_n) > -1 uA at idle (reverse-biased)
# The TVS pair (DTVS1a/DTVS1b) is non-conducting at idle (vin ~0V << 15V knee),
# so each zener's idle current sits in a tight window around 0.
TVS_IDLE_WINDOW = (-1e-6, 1e-6)   # I(DTVS1a)/I(DTVS1b) at idle: ~0, +/-1 uA
# At the DC operating point the AC source V1 sits at 0V, so the jack node vin is
# at 0V DC (no DC path charges it). Same +/-10mV window as the op-amp offsets.
VIN_IDLE_WINDOW = (-10e-3, 10e-3)  # V(vin) at idle DC: 0V, +/-10 mV

# ============================================================================
# STAGE 2 DRIVER DYNAMIC (transient) PASS CRITERIA
# ============================================================================
# The stage_02 .op netlist only checks DC bias; the dynamic driver behaviour
# (flyback diode idle, no driver clip) needs a transient. These gate the
# stage_02_driver_tran variant (1kHz 100mVpk, .tran 0 10m 0 5u):
#   d3_pk   : the D3 flyback diode must NOT conduct during normal drive. Under
#             normal operation the collector never flies above +15V (the tank is
#             a soft load and L1 returns to the rail), so D3 stays reverse-biased.
D3_IDLE_PEAK_MAX = 1e-3            # < 1 mA peak through D3 in normal drive
#   drv_pk  : peak |I(L1)| (the driver/primary current). Quiescent Ic ~16mA flows
#             through L1; a healthy driver's AC swing keeps the peak well under
#             this ceiling. A driver CLIPPING/over-driving the transformer would
#             flat-top and push |I(L1)| past it. Ceiling = quiescent Ic high
#             (Q1_IC_WINDOW = 26mA) + generous AC headroom, still far below the
#             BD139 1.5A rating, so it reads as a clip/over-drive detector.
DRV_PEAK_MAX  = 0.1               # < 100 mA peak |I(L1)| (no driver clip)
#   drv_rms : RMS I(L1). DC-dominated (~Ic), so it sits near the quiescent
#             current and must stay under the same ceiling (RMS <= peak always).
DRV_RMS_MAX   = 0.1               # < 100 mA RMS I(L1)

# ============================================================================
# Q1 BASE BIAS (divider operating point)
# ============================================================================
# Q1 base DC, set by the R3b (6.8k, +15V->base) / R4 (1k, base->GND) divider.
# Unloaded (no base current) the divider sits at 15 * R4/(R3b+R4). Loaded by the
# base current it pulls down a little, so the bench window is wider/lower.
Q1_VB_UNLOADED = round(15 * 1000 / (6800 + 1000), 4)   # 1.923V (15*R4/(R3b+R4))
Q1_VB_WINDOW   = (1.65, 2.05)     # loaded V(q1_base), with base current

# Bench noise floor (Stage 7)
NOISE_FLOOR_MAX_VRMS = 1e-3        # < 1 mVrms at J2

# ============================================================================
# POT POSITION SWEEP (Stage 7 — pot-extreme coverage, GitHub issue #43)
# ============================================================================
# All baseline sims hardcode every pot at 50% (equal halves). These constants
# drive the pot-extreme variants of gen_stage6_full.py, which sweep one pot to a
# rail while holding the others at noon, exercising the real failure modes at
# the travel extremes (zero drive, hard clip, dry/wet bleed, tone cut/peak).

# Pot positions (fraction of full travel: 0.0 = CCW/min, 0.5 = noon, 1.0 = CW/max)
POT_MIN  = 0.0
POT_MID  = 0.5
POT_MAX  = 1.0

# Pot total values (each = sum of the two modelled halves, confirms the netlist:
# RV1a+RV1b = 5k+5k = 10k; RV2a+RV2b = 50k+50k = 100k; RV3a+RV3b = 50k+50k = 100k)
RV1_TOTAL = "10k"   # Dwell — linear
RV2_TOTAL = "100k"  # Mix — audio taper (modelled as linear in SPICE)
RV3_TOTAL = "100k"  # Tone — audio taper (modelled as linear in SPICE)

# Minimum non-zero pot half (a SPICE-singularity guard: a true 0 Ω half can make
# the wiper node float/short, so the CCW/CW rail uses 0.001 instead of 0).
POT_MIN_OHMS = "0.001"

# --- Pot sweep pass windows -------------------------------------------------
# Grounded in the actual circuit and verified against the LTspice 26 sim of the
# pot-extreme variants (200ms tran, 100mVpk 1kHz stimulus). The "level" windows
# are measured as MAX abs() over a settled tail (a sine's raw AVG is ~0, so the
# .meas directives that gate a SIGNAL LEVEL use MAX abs(); AVG is reserved for
# the DC-bias reads q1_e, where the bypassed emitter has no AC content).
#
# Dry-path level: u1_buf carries the 100mVpk input through the unity U1 buffer
# (+R2 100Ω). At Mix noon the dry signal is divided by the pot/Rdry network
# before mix_node, so the dry contribution observed at v_out lands near ~0.1V pk.
# Window is generous (0.05–0.15) to pass a correct circuit and catch a dead path.
DWELL_MIN_DRY_WINDOW   = (0.05, 0.15)   # ~0.1V pk dry still passes at min Dwell
DWELL_MAX_WIPER_PK_WINDOW = (0.03, 0.15)  # at max drive the wiper sees most of u1_buf
                                        # (~100mVpk) through near-zero series R; C_drive
                                        # loading brings it to ~40-100mVpk depending on
                                        # drive; window catches a dead path (< 0.03) or
                                        # weird amplification (> 0.15)
DWELL_MAX_U2_PK_MAX    = 13.5           # U2 output must not rail beyond the +/-15V supply
MIX_CCW_VOUT_WINDOW    = (0.05, 0.15)   # dry signal present at full-CCW (wet muted)
MIX_CCW_WET_BLEED_WINDOW = (0.90, 1.05)  # mix_node/dry_lvl ratio; at full-CCW wiper ≈ mix_dry so ratio ≈ 1
MIX_CW_VOUT_PK_MIN  = 0.01              # V pk; wet path must deliver some signal at full-CW
MIX_CW_DRY_ATTN_MAX = 0.50             # dry_lvl/mix_node ratio; dry should be < 50% of wiper at full-CW
WORST_CASE_SETTLE_MAX  = 0.5            # DC at U2 out settles back to ~0 after any clip

# ============================================================================
# STAGE 8 — REALISTIC HARDWARE STRESS VARIANTS
# ============================================================================
# Idealized sims use Vos=0, nominal mains, and nominal BD139 beta. Real hardware
# deviates; these constants drive the stress variants that model the most likely
# real-world deviations and confirm the design still passes the same windows.

# --- 3a. Low mains voltage (PSU headroom) -----------------------------------
# ANSI C84.1 allows 114-126V for 120V nominal; older homes sag to ~108V under
# load. The PSU low-mains variant scales the T1 secondary AC source by this
# factor (108/120 = 0.90, 10% low) and re-runs the SAME rail/ripple checks: the
# regulators must still hit +/-15V and ripple must stay < 10mVpp on the sagged
# bus. Same RAIL_*_WINDOW / RIPPLE_MAX_PP windows apply.
PSU_LOW_MAINS_VFACTOR = 0.90       # AC secondary scale at 108V (10% low mains)

# --- 3b. U2 input offset injection (Vos stress) -----------------------------
# Real OPA2134 Vos is up to 500uV (typ 50uV). A 500uV DC source in series with
# U2's non-inverting input is multiplied by the 213.8x gain to ~107mV DC at
# u2_out. C4 blocks this from v_out, but it stresses U2 headroom. The op-variant
# Vos stress reads u2_out_dc_vos and confirms it stays within the bench-documented
# 20-150mV typical offset band (so the 214x * 500uV stays blocked by C4 and never
# rails U2). Window straddles 0 so either Vos polarity passes.
U2_VOS_INJECT     = "500u"         # DC source in series with U2(+) input
U2_VOS_OUT_WINDOW = (-0.15, 0.15)  # V DC at u2_out under 500uV Vos (214x*500uV ~107mV)

# --- 3c. BD139 low-beta corner ----------------------------------------------
# BD139 datasheet hFE min=40 (at Ic=500mA), typ ~100-150. Emitter degeneration
# (R5=68) + stiff base bias make the Q1 bias point largely beta-independent. The
# low-beta variant overrides BF to 40 (BD139_LO_BETA model = BD139_MODEL params
# with BF=40) and re-runs the SAME q1_ve / q1_ic bias windows: if they fail at
# BF=40 the bias design is not beta-independent. Same Q1_VE_WINDOW / Q1_IC_WINDOW.
BD139_LO_BETA_BF    = 40           # forced forward beta (datasheet hFE min)
# Derived from BD139_MODEL (single source of truth) with Bf overridden to the
# low-beta corner, so a change to the base BD139 params flows here automatically.
BD139_LO_BETA_MODEL = BD139_MODEL.replace("Bf=100", "Bf=%d" % BD139_LO_BETA_BF)
