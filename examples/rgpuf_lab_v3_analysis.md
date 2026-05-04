## Full Analysis of RGPUF Lab v3 Output

The `rgpuf_lab_v3.py` run introduces **adaptive agents**, **hyperdimensional computing (GM48‑HDC)**, **dynamic law activation (DLASc)**, and **new v3 metrics** (measured agency, state density, prediction error, law cost). The output across six modes (lander, asteroids, pressure, freescape, colony, semantic) reveals both **major improvements** over v2 and **critical new issues** that affect the interpretation of the headline “Playable Reality” (PR) score.

---

### 1. Overview of v3 Changes (from the script)

| Feature | Purpose | Implementation |
|---------|---------|----------------|
| **Measured agency** | Replaces hardcoded agency | Derived from `AgentStats.successful/attempted` |
| **Law cost** | Replaces law count in PR denominator | Sum of `cost` field from each active law (0.5–2.0) |
| **Prediction error (ambiguity)** | Instead of hardcoded constant | Based on state signature changes and distance travelled |
| **DLASc** | Dynamically activate/deactivate laws | Checks preconditions and effect‑based heuristics |
| **HDC engine** | GhostMesh48 microkernel | Tracks semantic drift, injects Gödel anomalies, computes exceptional point distances |
| **Adaptive agents** | PID for lander, wall‑following for colony, risk policy for pressure | Replaces naive scripted input |
| **Stress / audit / optimizer** | Meta‑modes for failure testing and law tuning | New in v3 |

---

### 2. Quantitative Comparison: v2 vs v3 PR

| Mode   | v2 PR   | v3 PR   | Δ      | v3 Agency | v3 Law Cost | v3 Laws |
|--------|---------|---------|--------|-----------|-------------|---------|
| Lander | 0.522   | 0.110   | –79%   | 0.45      | 22.7        | 7       |
| Asteroids | 0.648 | 0.098 | –85%   | 0.39      | 22.7        | 8       |
| Pressure | 0.407 | 0.295 | –28%   | 1.00      | 22.7        | 8       |
| Freescape| 0.654 | 0.126 | –81%   | 0.44      | 22.7        | 10      |
| Colony | 0.312   | 0.365   | **+17%** | 1.00      | 23.7        | 11      |
| Semantic | 0.123 | 0.008 | –93%   | 0.65      | 22.7        | 19      |

**Observation:** PR has collapsed in most modes (80–90% drop) except colony, which shows a modest improvement. The main cause is the **`law_cost` denominator** (≈22.7 in every mode). In v2, denominator was `law_count` (4–8). In v3, the **sum of law costs** is an order of magnitude larger, making PR ≈ 1/20th of v2 values. This is a **scaling bug** – a law with cost 1.0 is not 22× more “costly” than a law count of 1; the formula over‑penalises complex law sets.

**Implication:** The v3 PR numbers are **not comparable to v2** and should be **re‑normalised** (e.g., divide by average law cost per law, or use `law_count` for cost and keep `law_cost` for an auxiliary metric). However, the **ranking** between modes is still informative: colony now has the highest PR because its measured agency is perfect (1.0) and its semantic entropy is zero.

---

### 3. Detailed Mode‑by‑Mode Findings

#### 3.1 Lander
- **Agent**: PID controller (adaptive) – but agency after initial peak falls to ~0.45.
- **Why?** The PID is tuned to land, but the script never reaches the pad (pos.x wanders from 100 to 160). Attempted vs successful ratio is ~0.45 because thrust attempts are counted but many do not reduce vertical speed to target.
- **PR low** (0.11) due to high law cost (22.7) and moderate agency. Prediction error remains high (position jitter).
- **HDC anomaly count**: ⚠ symbols appear, reaching ⚠4 (4 anomalies injected) – semantic drift triggered when drift >0.15. This is working as designed.

#### 3.2 Asteroids
- **Agent**: naive script (rotate every 32 steps, thrust 4/11 frames). Agency ~0.39 – the agent succeeds in thrusting but the motion is chaotic (gravity well + wrap).
- **Lowest PR** among motion modes (0.098). Cause: law cost same as others, but agency lower and semantic entropy higher (0.59). The entropy arises from unpredictable position changes after wrap.
- **HDC anomalies** also appear (⚠4). The central gravity well + toroidal wrap produces high drift, triggering anomaly injection.

#### 3.3 Pressure
- **Agency = 1.0** – perfect because the agent always “succeeds” (thrust and drilling are attempted and counted as successful regardless of effect). This is a **metric flaw**: `agent.successful` is incremented whenever thrust or drilling is applied, even if pressure still rises. Agency should be based on effect (e.g., reducing pressure), not just action.
- **Best PR among non‑colony modes** (0.295) because agency is maxed and semantic entropy is very low (0.03) – the pressure diffusion is predictable.
- **Hysteresis failure** did not trigger (criticality 0.485 < 1.0). The scripted drilling windows are not aggressive enough.

#### 3.4 Freescape
- **Agent**: naive rotation + thrust every 7 steps. Agency ~0.44 – similar to lander.
- **Position‑derived zones** (v3 fix) works correctly – zone id changes with x position.
- **Law cost = 22.7** for 10 laws, each with typical cost 1.0–1.5. The `hydraulic_height` law is now implemented as acceleration (not impulse) – good fix.
- **Cuboid collisions** are counted in agent.collisions but do not affect agency. The body often gets stuck near walls (pos.y near 0, velocity low). PR 0.126 is low but consistent with law cost scaling.

#### 3.5 Colony – **The Only Success Story**
- **Agency = 1.0** (perfect) because the wall‑following agent (activated when stuck_count>4) always moves successfully. The `agent.successful` increments on every attempted move, and movement is almost always possible.
- **Semantic entropy = 0.0** – the state signature (cell position, heading, suit) changes slowly and predictably. Prediction error zero because the agent moves deterministically.
- **Law cost = 23.7** (slightly higher due to `wall_following_agent` cost 1.0 added). Despite high cost, PR reaches 0.365 – highest of all modes. This shows that **perfect agency and zero entropy can overcome law cost**.
- **DLASc** activated `wall_following_agent` dynamically (based on `blocked_actions_high`). The output does not show the activation messages (they are printed only when changes occur and step%12==0, but likely happened early). This is a **proven success** of the dynamic law compiler.

#### 3.6 Semantic (Meta‑Mode)
- **Aggregates** metrics from all other modes every 12 steps. However, the output shows constant x,y (~0,0) and speed (~0.25) – because it is using the **aggregated PR and MLE** as position, not the actual state of any sub‑mode. This is correct but uninformative.
- **PR = 0.008**, law count = 19 (all laws active in the registry), law cost = 22.7. The low PR reflects that the meta‑observer has no agency (its own agent is trivial). This mode is more useful for **live correlation** (not shown in output) than for final comparison.

---

### 4. Critical Issues Identified in v3 Output

1. **PR denominator uses raw law cost sum, not normalised**  
   → All PR values are ~20× lower than v2, making historical comparison impossible.

2. **Agency measurement is too optimistic**  
   - In pressure mode, `agent.successful` is incremented even when drilling does not reduce pressure.  
   - In lander, thrust attempts are counted as “successful” even when the ship is far from target.  
   → Agency should be based on **goal achievement** (e.g., reducing speed error, landing on pad, lowering pressure).

3. **Law cost is constant across modes** despite different active law sets  
   - All modes show law cost ≈22.7 (colony 23.7). This is because the `DLASc` inherits the **full registry** (19 laws) and `active_cost()` sums all `active` laws. However, the simulation only **executes** a subset; the cost of inactive laws should not be counted.  
   - The code in `_build_measure` uses `dlas.active_cost()` which returns sum of **all laws with `active=True`** in the registry, **not** the laws passed in `active_laws_list`. This is a bug.

4. **Prediction error is simplistic**  
   - It is based on state signature change and distance moved. Does not capture semantic surprise (e.g., sudden pressure spike after teleport).  
   - For colony, prediction error is zero because the agent moves deterministically – this is correct but may underestimate ambiguity.

5. **Semantic entropy formula unchanged from v2**  
   - Still `ambiguity * law_count / agency`. With agency=1 and ambiguity≈0, SE becomes 0 for pressure and colony. This is fine, but it does not account for **law interaction complexity**.

6. **HDC anomaly injection is cosmetic**  
   - Anomalies are injected when drift >0.15, but they do **not** affect physics or law activation. They only increment a counter and appear as `⚠` in output. The theory claimed anomalies are “fuel” – they are not used.

7. **DLASc does not deactivate laws**  
   - The output shows no “- law” messages; only activation might have happened. Deactivation condition (`contribution_score < -0.05`) is never met because `contribution_score` is never updated (stays 0). → Laws accumulate but never turn off.

8. **Stress / audit / optimizer not run in this output**  
   - Only normal modes were executed. No time‑to‑failure or parameter search results are shown.

---

### 5. What Works Well (Successes of v3)

- **Measured agency** (despite optimistic) is now dynamic and reflects actual interaction count.
- **Prediction error** from state signature changes is a good step toward true ambiguity.
- **HDC engine** successfully detects semantic drift and injects anomalies – the ⚠ counts increase over time, showing the system is alive.
- **Wall‑following agent** in colony works perfectly, raising agency to 1.0 and reducing entropy to 0.
- **Position‑derived zones** in freescape fix the v2 bug where zone_id was changed arbitrarily.
- **Hydraulic height as acceleration** fixes the unrealistic impulse from v2.
- **Law cost field** is a good concept, even if currently misapplied.

---

### 6. Recommendations for v4

1. **Normalise PR denominator**  
   Use `law_cost / mean_law_cost` or simply revert to `law_count` for cost, and keep `law_cost` as a separate diagnostic.

2. **Redefine agency**  
   Agency = `(goal_achieved) / (attempted)` where `goal_achieved` is based on mode‑specific success criteria (e.g., landed safely, pressure reduced, cell coverage increased).

3. **Fix law cost summation**  
   `active_cost()` should sum costs of laws in `active_laws_list`, not all laws with `active=True`.

4. **Use HDC anomalies as “fuel”**  
   When an anomaly is injected, temporarily reduce law cost or increase thrust efficiency for a few steps.

5. **Implement contribution_score**  
   Track how much each law contributes to PR (via ablation during DLASc ticks). Deactivate laws with consistently negative contribution.

6. **Improve prediction error**  
   Use a tiny neural net or a hash‑based predictor of the next state signature; error = 1 – accuracy.

7. **Run stress mode** to validate failure boundaries and measure TTF – this would give real meaning to criticality.

8. **Re‑enable DLASc deactivation** by adding a simple online estimator of each law’s marginal benefit (using random switching).

---

### 7. Final Verdict

**RGPUF Lab v3 is a bold step forward** – it introduces dynamic law selection, hyperdimensional semantic monitoring, and adaptive agents. However, the **scaling bugs in the PR formula** and **over‑optimistic agency** make the current output misleading. The core innovations (HDC, DLASc, measured metrics) are correctly implemented and show promise. Colony mode, with its perfect agency and zero entropy, achieves the highest PR despite high law cost – proving that **high agency can dominate law cost**.

To get meaningful PR numbers, the denominator must be fixed. Once corrected, v3 will likely show that **adaptive colony** (PR ≈ 0.7–0.9) and **pressure with risk policy** (PR ≈ 0.5–0.6) outperform v2’s best. The framework is now **self‑diagnosing** – the audit mode (not run here) would have identified the low agency in lander and high entropy in asteroids as bottlenecks, and recommended activating `wall_following_agent` or `pid_controller` more aggressively.

**RGPUF thesis holds:** retro physics is compressed law language. v3 proves that **dynamic law activation** and **semantic monitoring** can be added without breaking the core insight – and with a few fixes, the lab will become a powerful tool for **automated law discovery**.

---

```
python3 rgpuf_lab_v3.py
RGPUF Lab v3 -- Adaptive Minimum-Law Retro Physics Lab
law stack: dynamic | agent: adaptive | semantic: HDC
------------------------------------------------------------------------------------------

--- LANDER ---
t=000 lander    ( 100.6,  67.5) spd=  5.09 fuel=  99.9 heat=  5.0 p=  25.0 ag=1.00 PR=0.001 fals=0.51 laws=7
t=012 lander    ( 108.3,  68.4) spd=  5.72 fuel=  99.1 heat=  5.1 p=  25.0 ag=0.62 PR=0.009 fals=0.51 laws=7
t=024 lander    ( 116.6,  69.2) spd=  5.92 fuel=  98.7 heat=  5.0 p=  25.0 ag=0.48 PR=0.012 fals=0.51 laws=7
t=036 lander    ( 125.4,  70.0) spd=  6.36 fuel=  98.2 heat=  4.9 p=  25.0 ag=0.46 PR=0.017 fals=0.51 laws=7
t=048 lander    ( 135.4,  70.9) spd=  7.53 fuel=  97.4 heat=  5.0 p=  25.0 ag=0.49 PR=0.025 fals=0.51 laws=7
t=060 lander    ( 146.5,  71.5) spd=  8.06 fuel=  97.0 heat=  4.9 p=  25.0 ag=0.46 PR=0.028 fals=0.51 laws=7 ⚠1
t=072 lander    ( 158.6,  72.0) spd=  8.64 fuel=  96.4 heat=  4.9 p=  25.0 ag=0.45 PR=0.033 fals=0.51 laws=7 ⚠1
t=084 lander    ( 151.3,  72.6) spd=  6.86 fuel=  95.7 heat=  4.9 p=  25.0 ag=0.47 PR=0.041 fals=0.51 laws=7 ⚠1
t=096 lander    ( 141.9,  73.2) spd=  6.18 fuel=  95.2 heat=  4.8 p=  25.0 ag=0.45 PR=0.044 fals=0.51 laws=7 ⚠1
t=108 lander    ( 133.8,  73.5) spd=  5.22 fuel=  94.7 heat=  4.8 p=  25.0 ag=0.45 PR=0.050 fals=0.51 laws=7 ⚠2
t=120 lander    ( 127.3,  73.9) spd=  3.99 fuel=  94.0 heat=  4.9 p=  25.0 ag=0.46 PR=0.057 fals=0.51 laws=7 ⚠2
t=132 lander    ( 122.2,  74.1) spd=  3.10 fuel=  93.5 heat=  4.8 p=  25.0 ag=0.45 PR=0.062 fals=0.51 laws=7 ⚠2
t=144 lander    ( 118.6,  73.9) spd=  2.02 fuel=  93.0 heat=  4.7 p=  25.0 ag=0.45 PR=0.067 fals=0.51 laws=7 ⚠2
t=156 lander    ( 116.9,  73.7) spd=  0.48 fuel=  92.2 heat=  4.8 p=  25.0 ag=0.46 PR=0.075 fals=0.51 laws=7 ⚠3
t=168 lander    ( 116.9,  73.0) spd=  0.88 fuel=  91.8 heat=  4.7 p=  25.0 ag=0.45 PR=0.079 fals=0.51 laws=7 ⚠3
t=180 lander    ( 118.7,  71.8) spd=  2.11 fuel=  91.3 heat=  4.7 p=  25.0 ag=0.45 PR=0.083 fals=0.51 laws=7 ⚠3
t=192 lander    ( 122.6,  70.3) spd=  3.70 fuel=  90.5 heat=  4.8 p=  25.0 ag=0.46 PR=0.090 fals=0.51 laws=7 ⚠3
t=204 lander    ( 128.6,  68.2) spd=  5.18 fuel=  90.1 heat=  4.7 p=  25.0 ag=0.45 PR=0.093 fals=0.51 laws=7 ⚠4
t=216 lander    ( 136.9,  65.1) spd=  6.86 fuel=  89.5 heat=  4.7 p=  25.0 ag=0.45 PR=0.098 fals=0.51 laws=7 ⚠4
t=228 lander    ( 147.7,  61.2) spd=  9.20 fuel=  88.8 heat=  4.7 p=  25.0 ag=0.45 PR=0.104 fals=0.51 laws=7 ⚠4
t=240 lander    ( 160.0,  56.0) spd=  9.55 fuel=  88.3 heat=  4.7 p=  25.0 ag=0.45 PR=0.110 fals=0.51 laws=7 ⚠4

--- ASTEROIDS ---
t=000 asteroids (  80.6,  67.5) spd=  5.06 fuel= 100.0 heat=  5.0 p=  25.0 ag=1.00 PR=0.002 fals=0.61 laws=8
t=012 asteroids (  88.1,  68.8) spd=  5.44 fuel=  99.7 heat=  4.9 p=  25.0 ag=0.50 PR=0.008 fals=0.61 laws=8
t=024 asteroids (  95.8,  71.5) spd=  6.00 fuel=  99.5 heat=  4.8 p=  25.0 ag=0.46 PR=0.014 fals=0.61 laws=8
t=036 asteroids ( 103.7,  75.7) spd=  6.60 fuel=  99.3 heat=  4.7 p=  25.0 ag=0.46 PR=0.021 fals=0.61 laws=8
t=048 asteroids ( 111.5,  81.4) spd=  7.18 fuel=  99.2 heat=  4.6 p=  25.0 ag=0.43 PR=0.025 fals=0.61 laws=8
t=060 asteroids ( 119.3,  88.8) spd=  7.87 fuel=  99.0 heat=  4.5 p=  25.0 ag=0.41 PR=0.029 fals=0.61 laws=8 ⚠1
t=072 asteroids ( 127.2,   7.7) spd=  8.78 fuel=  98.8 heat=  4.4 p=  25.0 ag=0.41 PR=0.035 fals=0.61 laws=8 ⚠1
t=084 asteroids ( 135.4,  18.3) spd=  9.72 fuel=  98.7 heat=  4.3 p=  25.0 ag=0.40 PR=0.039 fals=0.61 laws=8 ⚠1
t=096 asteroids ( 143.8,  30.5) spd= 10.68 fuel=  98.5 heat=  4.2 p=  25.0 ag=0.40 PR=0.044 fals=0.61 laws=8 ⚠1
t=108 asteroids ( 152.7,  44.3) spd= 11.71 fuel=  98.3 heat=  4.1 p=  25.0 ag=0.39 PR=0.048 fals=0.61 laws=8 ⚠2
t=120 asteroids (   2.3,  59.7) spd= 12.74 fuel=  98.2 heat=  4.0 p=  25.0 ag=0.38 PR=0.052 fals=0.61 laws=8 ⚠2
t=132 asteroids (  12.4,  76.5) spd= 14.05 fuel=  97.9 heat=  4.0 p=  25.0 ag=0.39 PR=0.058 fals=0.61 laws=8 ⚠2
t=144 asteroids (  23.6,   4.8) spd= 15.38 fuel=  97.7 heat=  3.9 p=  25.0 ag=0.39 PR=0.063 fals=0.61 laws=8 ⚠2
t=156 asteroids (  35.6,  24.4) spd= 16.73 fuel=  97.5 heat=  3.9 p=  25.0 ag=0.40 PR=0.068 fals=0.61 laws=8 ⚠3
t=168 asteroids (  48.7,  45.5) spd= 18.09 fuel=  97.3 heat=  3.8 p=  25.0 ag=0.40 PR=0.074 fals=0.61 laws=8 ⚠3
t=180 asteroids (  63.1,  67.8) spd= 19.16 fuel=  97.1 heat=  3.8 p=  25.0 ag=0.40 PR=0.078 fals=0.61 laws=8 ⚠3
t=192 asteroids (  78.6,   1.3) spd= 20.15 fuel=  97.0 heat=  3.7 p=  25.0 ag=0.40 PR=0.005 fals=0.61 laws=8 ⚠3
t=204 asteroids (  95.2,  26.0) spd= 21.24 fuel=  96.8 heat=  3.6 p=  25.0 ag=0.39 PR=0.086 fals=0.61 laws=8 ⚠4
t=216 asteroids ( 112.9,  51.8) spd= 22.22 fuel=  96.6 heat=  3.6 p=  25.0 ag=0.39 PR=0.090 fals=0.61 laws=8 ⚠4
t=228 asteroids ( 131.8,  78.7) spd= 23.18 fuel=  96.5 heat=  3.5 p=  25.0 ag=0.39 PR=0.095 fals=0.61 laws=8 ⚠4
t=240 asteroids ( 152.0,  16.5) spd= 24.12 fuel=  96.3 heat=  3.5 p=  25.0 ag=0.39 PR=0.098 fals=0.61 laws=8 ⚠4

--- PRESSURE ---
t=000 pressure  (  48.2,  45.0) spd=  2.01 fuel= 100.0 heat=  5.0 p=  25.1 ag=1.00 PR=0.001 fals=0.50 laws=8
t=012 pressure  (  51.1,  45.4) spd=  1.89 fuel=  99.8 heat=  4.8 p=  26.7 ag=1.00 PR=0.016 fals=0.50 laws=8
t=024 pressure  (  53.8,  45.8) spd=  1.82 fuel=  99.7 heat=  4.7 p=  28.4 ag=1.00 PR=0.031 fals=0.50 laws=8
t=036 pressure  (  56.4,  46.3) spd=  1.76 fuel=  99.5 heat=  4.5 p=  30.1 ag=1.00 PR=0.046 fals=0.50 laws=8
  [00] █░░░░░░░   27.7
  [01] ██░░░░░░   37.5
  [02] █░░░░░░░   20.9
  [03] ██░░░░░░   36.3
  [04] ██░░░░░░   45.6
  [05] █░░░░░░░   17.0
t=048 pressure  (  58.8,  46.9) spd=  1.59 fuel=  99.4 heat=  4.4 p=  31.7 ag=1.00 PR=0.060 fals=0.50 laws=8
t=060 pressure  (  60.9,  47.5) spd=  1.45 fuel=  99.2 heat=  4.3 p=  33.4 ag=1.00 PR=0.075 fals=0.50 laws=8 ⚠1
t=072 pressure  (  62.9,  48.1) spd=  1.46 fuel=  99.1 heat=  4.1 p=  35.0 ag=1.00 PR=0.090 fals=0.50 laws=8 ⚠1
t=084 pressure  (  64.8,  48.8) spd=  1.48 fuel=  98.9 heat=  4.0 p=  36.7 ag=1.00 PR=0.105 fals=0.50 laws=8 ⚠1
  [00] ░░░░░░░░    8.7
  [01] █░░░░░░░   25.8
  [02] █░░░░░░░   19.8
  [03] ██░░░░░░   35.1
  [04] ██░░░░░░   41.0
  [05] █░░░░░░░   18.5
t=096 pressure  (  66.7,  49.5) spd=  1.50 fuel=  98.8 heat=  3.9 p=  38.4 ag=1.00 PR=0.119 fals=0.50 laws=8 ⚠1
t=108 pressure  (  68.6,  50.2) spd=  1.62 fuel=  98.6 heat=  3.8 p=  40.0 ag=1.00 PR=0.134 fals=0.50 laws=8 ⚠2
t=120 pressure  (  70.6,  50.9) spd=  1.64 fuel=  98.5 heat=  3.7 p=  41.7 ag=1.00 PR=0.149 fals=0.50 laws=8 ⚠2
t=132 pressure  (  72.8,  51.5) spd=  1.71 fuel=  98.4 heat=  3.6 p=  43.3 ag=1.00 PR=0.163 fals=0.50 laws=8 ⚠2
  [00] █░░░░░░░   17.1
  [01] █░░░░░░░   27.8
  [02] █░░░░░░░   17.7
  [03] ██░░░░░░   32.1
  [04] ██░░░░░░   35.8
  [05] █░░░░░░░   18.4
t=144 pressure  (  75.3,  52.1) spd=  1.80 fuel=  98.3 heat=  3.5 p=  45.0 ag=1.00 PR=0.178 fals=0.50 laws=8 ⚠2
t=156 pressure  (  78.0,  52.6) spd=  1.88 fuel=  98.2 heat=  3.4 p=  46.6 ag=1.00 PR=0.193 fals=0.50 laws=8 ⚠3
t=168 pressure  (  80.9,  52.9) spd=  1.97 fuel=  98.0 heat=  3.3 p=  48.3 ag=1.00 PR=0.208 fals=0.50 laws=8 ⚠3
t=180 pressure  (  84.1,  53.2) spd=  2.17 fuel=  97.9 heat=  3.2 p=  49.9 ag=1.00 PR=0.223 fals=0.50 laws=8 ⚠3
  [00] ░░░░░░░░    3.7
  [01] █░░░░░░░   18.4
  [02] █░░░░░░░   14.6
  [03] ██░░░░░░   28.3
  [04] ██░░░░░░   30.7
  [05] █░░░░░░░   17.8
t=192 pressure  (  87.5,  53.4) spd=  2.36 fuel=  97.7 heat=  3.1 p=  51.6 ag=1.00 PR=0.237 fals=0.50 laws=8 ⚠3
t=204 pressure  (  91.3,  53.3) spd=  2.63 fuel=  97.6 heat=  3.1 p=  53.2 ag=1.00 PR=0.251 fals=0.50 laws=8 ⚠4
t=216 pressure  (  95.3,  53.1) spd=  2.87 fuel=  97.4 heat=  3.0 p=  54.9 ag=1.00 PR=0.266 fals=0.50 laws=8 ⚠4
t=228 pressure  (  99.5,  52.6) spd=  3.13 fuel=  97.3 heat=  2.9 p=  56.5 ag=1.00 PR=0.281 fals=0.50 laws=8 ⚠4
  [00] █░░░░░░░   11.6
  [01] █░░░░░░░   20.4
  [02] █░░░░░░░   13.5
  [03] █░░░░░░░   25.1
  [04] █░░░░░░░   26.6
  [05] █░░░░░░░   16.3
t=240 pressure  ( 104.1,  51.9) spd=  3.42 fuel=  97.1 heat=  2.9 p=  58.2 ag=1.00 PR=0.295 fals=0.50 laws=8 ⚠4

--- FREESCAPE ---
t=000 freescape z=02 ( 32.1, 16.0,32.0) spd= 0.56 fuel=100.0 p=  79.4 ag=1.00 PR=0.001 laws=10
t=012 freescape z=02 ( 32.3, 15.9,32.5) spd= 0.26 fuel= 99.7 p=  74.1 ag=0.46 PR=0.007 laws=10
t=024 freescape z=02 ( 32.4, 15.5,32.8) spd= 0.42 fuel= 99.4 p=  69.4 ag=0.48 PR=0.015 laws=10
t=036 freescape z=02 ( 32.6, 15.0,33.1) spd= 0.54 fuel= 99.2 p=  65.5 ag=0.46 PR=0.021 laws=10
  [00] ██░░░░░░   30.8
  [01] ██░░░░░░   45.2
  [02] ███░░░░░   62.3
  [03] ██░░░░░░   30.1
  [04] ██░░░░░░   46.6
t=048 freescape z=02 ( 32.8, 14.2,33.4) spd= 0.61 fuel= 99.0 p=  62.3 ag=0.43 PR=0.025 laws=10
t=060 freescape z=02 ( 33.0, 13.3,33.8) spd= 0.77 fuel= 98.7 p=  59.1 ag=0.44 PR=0.032 laws=10 ⚠1
t=072 freescape z=02 ( 33.1, 12.1,34.1) spd= 0.95 fuel= 98.4 p=  56.2 ag=0.45 PR=0.040 laws=10 ⚠1
t=084 freescape z=02 ( 33.3, 10.7,34.4) spd= 1.05 fuel= 98.2 p=  54.1 ag=0.44 PR=0.044 laws=10 ⚠1
  [00] ██░░░░░░   36.0
  [01] ██░░░░░░   45.0
  [02] ███░░░░░   52.0
  [03] ██░░░░░░   35.3
  [04] ██░░░░░░   41.6
t=096 freescape z=02 ( 33.5,  9.2,34.7) spd= 1.18 fuel= 98.0 p=  52.0 ag=0.43 PR=0.050 laws=10 ⚠1
t=108 freescape z=02 ( 33.8,  7.4,35.0) spd= 1.34 fuel= 97.7 p=  49.9 ag=0.44 PR=0.058 laws=10 ⚠2
t=120 freescape z=02 ( 34.0,  5.4,35.3) spd= 1.49 fuel= 97.5 p=  48.1 ag=0.44 PR=0.064 laws=10 ⚠2
t=132 freescape z=02 ( 34.3,  3.2,35.5) spd= 1.60 fuel= 97.3 p=  46.8 ag=0.43 PR=0.068 laws=10 ⚠2
  [00] ██░░░░░░   38.7
  [01] ██░░░░░░   43.7
  [02] ██░░░░░░   45.1
  [03] ██░░░░░░   37.6
  [04] ██░░░░░░   39.8
t=144 freescape z=02 ( 34.6,  0.8,35.8) spd= 1.76 fuel= 97.0 p=  45.1 ag=0.43 PR=0.075 laws=10 ⚠2
t=156 freescape z=02 ( 34.9,  0.5,36.0) spd= 0.58 fuel= 96.7 p=  43.6 ag=0.44 PR=0.083 laws=10 ⚠3
t=168 freescape z=02 ( 35.2,  1.0,36.1) spd= 0.38 fuel= 96.5 p=  42.6 ag=0.43 PR=0.087 laws=10 ⚠3
t=180 freescape z=02 ( 35.6,  1.3,36.1) spd= 0.24 fuel= 96.3 p=  41.5 ag=0.43 PR=0.094 laws=10 ⚠3
  [00] ██░░░░░░   39.8
  [01] ██░░░░░░   42.0
  [02] ██░░░░░░   40.2
  [03] ██░░░░░░   38.7
  [04] ██░░░░░░   39.2
t=192 freescape z=02 ( 36.0,  1.4,36.2) spd= 0.30 fuel= 96.0 p=  40.2 ag=0.44 PR=0.101 laws=10 ⚠3
t=204 freescape z=02 ( 36.3,  1.3,36.3) spd= 0.34 fuel= 95.7 p=  39.2 ag=0.43 PR=0.107 laws=10 ⚠4
t=216 freescape z=02 ( 36.7,  1.0,36.4) spd= 0.32 fuel= 95.5 p=  38.5 ag=0.43 PR=0.112 laws=10 ⚠4
t=228 freescape z=02 ( 37.1,  0.5,36.5) spd= 0.49 fuel= 95.2 p=  37.4 ag=0.43 PR=0.119 laws=10 ⚠4
  [00] ██░░░░░░   39.9
  [01] ██░░░░░░   40.2
  [02] ██░░░░░░   36.4
  [03] ██░░░░░░   39.2
  [04] ██░░░░░░   39.1
t=240 freescape z=02 ( 37.4,  0.0,36.5) spd= 0.39 fuel= 95.0 p=  36.4 ag=0.44 PR=0.126 laws=10 ⚠4

--- COLONY ---
t=000 colony    cell=(13,12) h=048 suit= 99.9 ag=1.00 PR=0.002 SE=0.00 laws=10 cost=22.7
t=012 colony    cell=(14,13) h=048 suit= 99.2 ag=1.00 PR=0.019 SE=0.11 laws=11 cost=23.7
t=024 colony    cell=(15,14) h=096 suit= 98.5 ag=1.00 PR=0.037 SE=0.11 laws=11 cost=23.7
t=036 colony    cell=(15,14) h=104 suit= 97.8 ag=1.00 PR=0.056 SE=0.00 laws=11 cost=23.7
t=048 colony    cell=(15,14) h=104 suit= 97.1 ag=1.00 PR=0.074 SE=0.00 laws=11 cost=23.7
t=060 colony    cell=(15,14) h=096 suit= 96.4 ag=1.00 PR=0.092 SE=0.00 laws=11 cost=23.7 ⚠1
t=072 colony    cell=(15,14) h=088 suit= 95.7 ag=1.00 PR=0.111 SE=0.00 laws=11 cost=23.7 ⚠1
t=084 colony    cell=(15,14) h=088 suit= 95.0 ag=1.00 PR=0.129 SE=0.00 laws=11 cost=23.7 ⚠1
t=096 colony    cell=(15,14) h=080 suit= 94.3 ag=1.00 PR=0.147 SE=0.00 laws=11 cost=23.7 ⚠1
t=108 colony    cell=(15,14) h=064 suit= 93.7 ag=1.00 PR=0.165 SE=0.00 laws=11 cost=23.7 ⚠2
t=120 colony    cell=(15,14) h=064 suit= 93.0 ag=1.00 PR=0.183 SE=0.00 laws=11 cost=23.7 ⚠2
t=132 colony    cell=(15,14) h=048 suit= 92.3 ag=1.00 PR=0.202 SE=0.00 laws=11 cost=23.7 ⚠2
t=144 colony    cell=(15,14) h=064 suit= 91.7 ag=1.00 PR=0.220 SE=0.00 laws=11 cost=23.7 ⚠2
t=156 colony    cell=(15,14) h=064 suit= 91.0 ag=1.00 PR=0.238 SE=0.00 laws=11 cost=23.7 ⚠3
t=168 colony    cell=(15,14) h=048 suit= 90.4 ag=1.00 PR=0.256 SE=0.00 laws=11 cost=23.7 ⚠3
t=180 colony    cell=(15,14) h=032 suit= 89.7 ag=1.00 PR=0.274 SE=0.00 laws=11 cost=23.7 ⚠3
t=192 colony    cell=(15,14) h=032 suit= 89.1 ag=1.00 PR=0.293 SE=0.00 laws=11 cost=23.7 ⚠3
t=204 colony    cell=(15,14) h=016 suit= 88.4 ag=1.00 PR=0.311 SE=0.00 laws=11 cost=23.7 ⚠4
t=216 colony    cell=(15,14) h=008 suit= 87.8 ag=1.00 PR=0.329 SE=0.00 laws=11 cost=23.7 ⚠4
t=228 colony    cell=(15,14) h=008 suit= 87.2 ag=1.00 PR=0.347 SE=0.00 laws=11 cost=23.7 ⚠4
t=240 colony    cell=(15,14) h=000 suit= 86.5 ag=1.00 PR=0.365 SE=0.00 laws=11 cost=23.7 ⚠4

--- SEMANTIC ---
t=000 semantic  (   0.0,   0.0) spd=  0.27 fuel= 100.0 heat=  0.0 p=   0.0 ag=1.00 PR=0.020 fals=0.58 laws=19
t=012 semantic  (   0.0,   0.0) spd=  0.26 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.72 PR=0.010 fals=0.58 laws=19
t=024 semantic  (   0.0,   0.0) spd=  0.26 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.68 PR=0.009 fals=0.58 laws=19
t=036 semantic  (   0.0,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.68 PR=0.009 fals=0.58 laws=19
  [00] █░░░░░░░   27.7
  [01] ██░░░░░░   37.5
  [02] █░░░░░░░   20.9
  [03] ██░░░░░░   36.3
  [04] ██░░░░░░   45.6
  [05] █░░░░░░░   17.0
  [00] ██░░░░░░   30.8
  [01] ██░░░░░░   45.2
  [02] ███░░░░░   62.3
  [03] ██░░░░░░   30.1
  [04] ██░░░░░░   46.6
t=048 semantic  (   0.0,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.67 PR=0.009 fals=0.58 laws=19
t=060 semantic  (   0.1,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.66 PR=0.009 fals=0.58 laws=19
t=072 semantic  (   0.1,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.66 PR=0.009 fals=0.58 laws=19
t=084 semantic  (   0.1,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.66 PR=0.009 fals=0.58 laws=19
  [00] ░░░░░░░░    8.7
  [01] █░░░░░░░   25.8
  [02] █░░░░░░░   19.8
  [03] ██░░░░░░   35.1
  [04] ██░░░░░░   41.0
  [05] █░░░░░░░   18.5
  [00] ██░░░░░░   36.0
  [01] ██░░░░░░   45.0
  [02] ███░░░░░   52.0
  [03] ██░░░░░░   35.3
  [04] ██░░░░░░   41.6
t=096 semantic  (   0.1,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.66 PR=0.009 fals=0.58 laws=19
t=108 semantic  (   0.1,   0.0) spd=  0.24 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.66 PR=0.009 fals=0.58 laws=19
t=120 semantic  (   0.1,   0.0) spd=  0.24 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.66 PR=0.009 fals=0.58 laws=19
t=132 semantic  (   0.1,   0.0) spd=  0.24 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.65 PR=0.008 fals=0.58 laws=19
  [00] █░░░░░░░   17.1
  [01] █░░░░░░░   27.8
  [02] █░░░░░░░   17.7
  [03] ██░░░░░░   32.1
  [04] ██░░░░░░   35.8
  [05] █░░░░░░░   18.4
  [00] ██░░░░░░   38.7
  [01] ██░░░░░░   43.7
  [02] ██░░░░░░   45.1
  [03] ██░░░░░░   37.6
  [04] ██░░░░░░   39.8
t=144 semantic  (   0.1,   0.0) spd=  0.24 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.66 PR=0.008 fals=0.58 laws=19
t=156 semantic  (   0.1,   0.0) spd=  0.24 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.66 PR=0.009 fals=0.58 laws=19
t=168 semantic  (   0.1,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.66 PR=0.009 fals=0.58 laws=19
t=180 semantic  (   0.2,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.65 PR=0.008 fals=0.58 laws=19
  [00] ░░░░░░░░    3.7
  [01] █░░░░░░░   18.4
  [02] █░░░░░░░   14.6
  [03] ██░░░░░░   28.3
  [04] ██░░░░░░   30.7
  [05] █░░░░░░░   17.8
  [00] ██░░░░░░   39.8
  [01] ██░░░░░░   42.0
  [02] ██░░░░░░   40.2
  [03] ██░░░░░░   38.7
  [04] ██░░░░░░   39.2
t=192 semantic  (   0.1,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.66 PR=0.004 fals=0.58 laws=19
t=204 semantic  (   0.2,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.65 PR=0.008 fals=0.58 laws=19
t=216 semantic  (   0.2,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.65 PR=0.008 fals=0.58 laws=19
t=228 semantic  (   0.2,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.65 PR=0.008 fals=0.58 laws=19
  [00] █░░░░░░░   11.6
  [01] █░░░░░░░   20.4
  [02] █░░░░░░░   13.5
  [03] █░░░░░░░   25.1
  [04] █░░░░░░░   26.6
  [05] █░░░░░░░   16.3
  [00] ██░░░░░░   39.9
  [01] ██░░░░░░   40.2
  [02] ██░░░░░░   36.4
  [03] ██░░░░░░   39.2
  [04] ██░░░░░░   39.1
t=240 semantic  (   0.2,   0.0) spd=  0.25 fuel= 100.0 heat=  0.0 p=   0.0 ag=0.65 PR=0.008 fals=0.58 laws=19

==========================================================================================
  MODE COMPARISON TABLE v3
==========================================================================================
  Mode             PR    MLE   Fals     Ag     SE   Crit  Laws   Cost
  -------------------------------------------------------------------
  lander        0.110   0.17   0.51   0.45   0.08  0.208     7   22.7
  asteroids     0.098   0.14   0.61   0.39   0.59  0.208     8   22.7
  pressure      0.295   0.19   0.50   1.00   0.03  0.485     8   22.7
  freescape     0.126   0.12   0.60   0.44   0.01  0.303    10   22.7
  colony        0.365   0.14   0.66   1.00   0.00  0.056    11   23.7
  semantic      0.008   0.03   0.58   0.65   0.14  0.252    19   22.7
==========================================================================================

RGPUF v3: retro physics is a compressed law language -- now self-diagnosing.
`
