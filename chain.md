# Signal Chain

## Current State

```mermaid
flowchart TD
  G["🎸 Guitar"]

  subgraph PEDALBOARD["Pedalboard"]
    TA["IO Thick Air<br/>Dual JFET Clean Boost"]
    DIRT["IO Old Dirt<br/>Distortion"]
  end

  subgraph RACK["Rack"]
    PRE["Alembic FX-1<br/>Tube Preamp"]
    QV["Alesis QuadraVerb<br/>Delay + Modulation"]
    REV["Custom Spring Reverb<br/>w/ Low-Z Output Buffer"]
    TUNER["Sabine RT-1601<br/>Rack Tuner (silent path)"]
  end

  subgraph AMP["Power Amp"]
    MC["McIntosh MC100<br/>100W Solid State Mono<br/>Autoformer Output"]
  end

  subgraph CABINET["Speaker Cabinet"]
    SP1["JBL E120-8 #1<br/>8Ω / 150W"]
    SP2["JBL E120-8 #2<br/>8Ω / 150W"]
  end

  G -->|"GS-6 15ft"| TA
  TA -->|"GS-6 patch"| DIRT
  DIRT -->|"GS-6 8ft"| PRE
  PRE -->|"1/4 TS"| QV
  QV -->|"1/4 TS"| REV
  REV -->|"1/4 TS"| MC
  MC -->|"Canare 4S11 / 4Ω tap"| SP1
  MC -->|"Canare 4S11 / 4Ω tap"| SP2
```

## Aspirational / Future State

```mermaid
flowchart TD
  G["🎸 Guitar"]

  subgraph OBEL["OBEL Buffer (pedal form)"]
    BUF_SEND["Buffer → Send"]
    BUF_RET["Return → Volume"]
  end

  subgraph PEDALBOARD["Pedalboard (in OBEL loop)"]
    TA["IO Thick Air<br/>Dual JFET Clean Boost"]
    DIRT["IO Old Dirt<br/>Distortion"]
    MUTE["Mute Switch<br/>→ Rack Tuner"]
    WEIRD["Experimental Pedals<br/>(Rainbow Machine / POG)"]
  end

  subgraph RACK["Rack"]
    PRE["Alembic FX-1<br/>Tube Preamp"]
    LPM["Lehle Parallel M<br/>Single Parallel Loop"]
    QV["Alesis QuadraVerb<br/>Delay + Modulation (in loop)"]
    REV["Ghost Spring Reverb<br/>Transformer-Coupled (series)"]
    TUNER["Sabine RT-1601<br/>Rack Tuner (silent path)"]
  end

  subgraph AMP["Power Amp"]
    MC["McIntosh MC100<br/>100W Solid State Mono<br/>Autoformer Output"]
  end

  subgraph CABINET["Speaker Cabinet"]
    SP1["JBL E120-8 #1<br/>8Ω / 150W"]
    SP2["JBL E120-8 #2<br/>8Ω / 150W"]
  end

  G --> BUF_SEND
  BUF_SEND --> TA
  TA --> DIRT
  DIRT --> WEIRD
  WEIRD --> BUF_RET
  BUF_RET --> PRE
  PRE --> LPM
  LPM -- loop --> QV --> LPM
  LPM --> REV
  REV --> MC
  MC -->|"4Ω tap / parallel"| SP1
  MC -->|"4Ω tap / parallel"| SP2
  MUTE -.->|"split to tuner"| TUNER
```

## Signal Flow Philosophy

1. **Buffer immediately.** Place a high-quality buffer (Thick Air stage 1, or dedicated OBEL buffer) as close to the guitar as possible to combat cable capacitance and preserve high-end.
2. **Gain stages before preamp.** Thick Air → Old Dirt provide clean boost and dirt that hit the Alembic's tube front-end. The Alembic is run clean — edge of breakup at most.
3. **Time effects after preamp.** QuadraVerb runs in a parallel loop via the **Lehle Parallel M** — dry signal never touches A/D conversion. Ghost Spring stays in series after the Lehle (fully analog, Mix pot handles blend). QuadraVerb handles delay and modulation only — reverb programs retired.
4. **Reverb last before power amp.** The spring tank with low-impedance buffer is the final device before the MC100, just like Jerry's Fender Reverb Unit placement between F-2B and MC2300.
5. **Clean power, always.** The MC100 should never clip. All tone and dynamics come from preceding gain stages.
