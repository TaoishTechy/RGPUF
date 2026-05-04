# Frame 2 — Token Metabolism + Harmful Surprise Demo
## `demo_02_token_metabolism.py`

**Version**: RGPUF v5 Blueprint — Frame 2
**Status**: Specification (pre-implementation)
**Dependencies**: `token_economy.py`, `hdc_surprise.py`, Frame 1 (`metrics_v5.py`)
**Output Artifacts**: `repair_events.csv`, `token_ledger.jsonl`, `token_dashboard.html`, `report_token_metabolism.md`

---

## 1. Core Purpose

In RGPUF v4, **Gödel tokens** served primarily as drift counters: every time the anomaly detector flagged a deviation from the predicted world state, a token was minted. The intention was to track "surprise," but the implementation was indiscriminate — tokens accumulated regardless of whether the surprise was *meaningful* or *trivial*. This led to **token inflation**: tokens became a noisy, high-volume signal that did not distinguish between "the world did something unexpected" and "the world did something unexpected that actually matters."

**Frame 2 transforms Gödel tokens from passive drift counters into an active adaptive economy.** Tokens are:

| Token Action | v4 Behavior | v5 Behavior |
|---|---|---|
| **Earned** | Every anomaly, unconditionally | Only when surprise *harms* agency, safety, novelty, or recoverability |
| **Spent** | Ad-hoc, often not tracked | Explicitly spent on repair leases, exploration actions, safety overrides |
| **Decayed** | Rarely implemented | Continuous decay at rate $\lambda$ per step (tokens are perishable) |
| **Wasted** | Not tracked | Explicitly tracked: earned tokens that expired before being spent |
| **Staked** | Not implemented | Tokens staked as collateral for law leases; refunded with bonus or burned |
| **Converted** | Not implemented | Convertible between token types (repair ↔ explore ↔ safety ↔ novelty) |

The core insight is: **not all surprise is harmful, and not all drift matters**. A sudden temperature fluctuation in the colony mode might be surprising but harmless if the agent's goal progress is unaffected. A loop detection in the same mode is surprising *and* harmful because it directly blocks goal progress. v5 tokens appear only in the second case.

---

## 2. What It Demonstrates

Frame 2 runs four micro-world modes with **controlled breakdowns injected** at predetermined steps. The demo proves:

1. **Selective minting**: Tokens are earned only during breakdowns that affect agency or risk, not during benign state changes.
2. **Purposeful spending**: Tokens are spent on repair leases that address specific failure modes.
3. **Bounded economy**: Token balance stays bounded over the full run, unlike v4's monotonically increasing token count.
4. **Waste visibility**: The difference between tokens earned and tokens spent is decomposed into decay and waste, making inefficiency visible.
5. **Adaptive thresholds**: The anomaly threshold $\theta_t$ adjusts dynamically via PID control to maintain a target harmful anomaly rate.

### 2.1 v4 vs v5 Token Behavior Comparison

| Metric | v4 Behavior | v5 Behavior |
|---|---|---|
| Tokens minted per step | ~1.0 (every anomaly) | ~0.05–0.15 (only harmful surprises) |
| Token balance over 240 steps | ~240 tokens | ~5–20 tokens (bounded) |
| Token spending | Ad-hoc, often zero | Explicit, tied to repair events |
| Token waste | Not tracked | Explicitly measured and reported |
| Threshold adaptation | Fixed $\theta$ | PID-controlled $\theta_t$ |
| Token types | Single type | Four types: repair, explore, safety, novelty |

---

## 3. Core Equations

### 3.1 Harmful Surprise Rule

$$T_{earned}(t) = \mathbb{I}\left[ (\delta_{drift}(t) > \theta_t) \wedge \left( \Delta A_{goal}(t) < 0 \;\lor\; \Delta Crit(t) > 0 \;\lor\; P_{stag}(t) > \tau \;\lor\; R_{risk}(t) > \kappa \right) \right]$$

**Term-by-term breakdown:**

| Symbol | Meaning |
|---|---|
| $\delta_{drift}(t)$ | Gödel drift magnitude at step $t$ — the distance between predicted and observed world state |
| $\theta_t$ | Adaptive anomaly threshold at step $t$ (see §3.5) |
| $\Delta A_{goal}(t)$ | Change in goal agency from step $t-1$ to step $t$ |
| $\Delta Crit(t)$ | Change in criticality (proximity to failure boundary) |
| $P_{stag}(t)$ | Stagnation penalty at step $t$ (from Frame 1, §3.4) |
| $R_{risk}(t)$ | Risk penalty at step $t$ |
| $\tau$ | Stagnation trigger threshold (default: 0.3) |
| $\kappa$ | Risk trigger threshold (default: 0.7) |
| $\mathbb{I}[\cdot]$ | Indicator function: 1 if condition is true, 0 otherwise |

**Key insight**: The first clause $(\delta_{drift} > \theta_t)$ checks whether anything surprising happened. The second clause (the four `∨` conditions) checks whether the surprise *matters*. Both must be true for a token to be earned. This is the **harmful surprise filter** that eliminates v4's indiscriminate minting.

**Example scenarios:**

| Scenario | $\delta_{drift} > \theta$? | Harmful? | Tokens Earned |
|---|---|---|---|
| Colony: agent enters new cell (expected) | No | N/A | 0 |
| Colony: agent caught in loop trap | Yes | Yes ($\Delta A_{goal} < 0$, $P_{stag} > \tau$) | 1 |
| Pressure: random particle fluctuation | Yes | No ($A_{goal}$ already 0, no criticality) | 0 |
| Pressure: pressure spike → system warning | Yes | Yes ($\Delta Crit > 0$) | 1 |
| Lander: normal descent | No | N/A | 0 |
| Lander: crash trajectory detected | Yes | Yes ($\Delta A_{goal} < 0$, $R_{risk} > \kappa$) | 1 |
| Freescape: normal navigation | No | N/A | 0 |
| Freescape: collision pocket / zone lock | Yes | Yes ($P_{stag} > \tau$, $\Delta A_{goal} < 0$) | 1 |

### 3.2 Token Metabolism Equation

$$T_{t+1} = T_t(1 - \lambda) + T_{earned}(t) - T_{spent}(t) - T_{waste}(t)$$

Where:
- $T_t$ is the token balance at the beginning of step $t$
- $\lambda$ is the decay rate per step (default: $\lambda = 0.01$, meaning 1% decay per step)
- $T_{earned}(t)$ is the number of tokens earned at step $t$ (from §3.1, typically 0 or 1)
- $T_{spent}(t)$ is the number of tokens spent at step $t$ (on repair leases)
- $T_{waste}(t)$ is the number of tokens that expired due to exceeding their lifetime

**Token decay mechanics**: Each token has a maximum lifetime of $L_{max}$ steps (default: $L_{max} = 120$). Tokens that are not spent within $L_{max}$ steps of being earned are automatically removed and counted as $T_{waste}$. The continuous decay factor $(1 - \lambda)$ provides a gradual erosion on top of the hard lifetime expiration.

**Economic interpretation**: The token economy is designed to be **mildly deflationary** in steady state. If the agent is performing well (few harmful surprises), tokens decay and waste away, keeping the balance low. If the agent encounters frequent breakdowns, tokens are earned rapidly but must be spent on repairs, preventing accumulation. The only way to maintain a high balance is to consistently convert harmful surprises into successful repairs — which is exactly the behavior the system should reward.

### 3.3 Token Inflation Rate

$$I_T = \frac{T_{earned}^{total} - T_{spent}^{total}}{N_{steps}}$$

Where:
- $T_{earned}^{total} = \sum_{t=0}^{N-1} T_{earned}(t)$ is the cumulative tokens earned
- $T_{spent}^{total} = \sum_{t=0}^{N-1} T_{spent}(t)$ is the cumulative tokens spent
- $N_{steps}$ is the total number of steps

**Interpretation**:
- $I_T > 0$: Economy is inflating (more tokens earned than spent). Sustained inflation indicates broken spending mechanisms.
- $I_T \approx 0$: Economy is balanced (earn ≈ spend). This is the target.
- $I_T < 0$: Economy is deflating (more tokens spent than earned). This can happen during intense repair phases and is acceptable in the short term.

**Target**: $|I_T| < 0.05$ over a 240-step run. If $I_T$ consistently exceeds 0.1, the inflation tax (Enhancement 13) is activated.

### 3.4 Token Spend Ratio

$$R_{spend} = \frac{T_{spent}^{total}}{\max(T_{earned}^{total}, 1)}$$

**Interpretation**:
- $R_{spend} \approx 1.0$: Almost all earned tokens are being spent — efficient economy, no waste
- $R_{spend} \approx 0.5$: Half of earned tokens are spent, half decay or expire — moderate efficiency
- $R_{spend} \approx 0.0$: Tokens are earned but never spent — broken spending pipeline (v4 behavior)

**Target**: $R_{spend} > 0.6$ over a 240-step run. Values below 0.3 indicate a spending problem.

### 3.5 Adaptive Anomaly Threshold (PID Controller)

$$\theta_{t+1} = \theta_t + k_p \left( r_{anom}(t) - r_{target} \right) + k_i \sum_{t'=0}^{t} \left( r_{anom}(t') - r_{target} \right) + k_d \cdot \Delta r_{anom}(t)$$

Where:
- $\theta_t$ is the anomaly threshold at step $t$ (initial: $\theta_0$ from config)
- $r_{anom}(t)$ is the observed harmful anomaly rate over the trailing window (fraction of steps with $T_{earned} = 1$)
- $r_{target}$ is the target harmful anomaly rate (default: $r_{target} = 0.075$, i.e., 7.5%)
- $k_p$ is the proportional gain (default: 0.1)
- $k_i$ is the integral gain (default: 0.01)
- $k_d$ is the derivative gain (default: 0.05)
- $\Delta r_{anom}(t) = r_{anom}(t) - r_{anom}(t-1)$ is the rate of change of anomaly rate

**Bounds**: $\theta_{t+1}$ is clamped to $[\theta_{min}, \theta_{max}]$ (default: $[0.01, 1.0]$) to prevent the threshold from becoming too sensitive or too insensitive.

**PID intuition**:
- **Proportional ($k_p$)**: If current anomaly rate is above target, increase threshold (make it harder to trigger). If below, decrease threshold (make it easier).
- **Integral ($k_i$)**: If anomaly rate has been above target for a sustained period, accumulate correction to push threshold higher more aggressively. Prevents persistent offset.
- **Derivative ($k_d$)**: If anomaly rate is changing rapidly, dampen the correction to prevent overshoot. Smooths transitions.

**Target behavior**: The PID controller maintains the harmful anomaly rate at approximately 5–10% of steps. This means:
- ~5–10% of steps produce harmful surprises (tokens earned)
- ~90–95% of steps are uneventful (no tokens earned)
- The threshold adapts to the inherent "surprisiness" of each mode

---

## 4. New Telemetry Columns

Frame 2 extends the Frame 1 telemetry with token-specific columns. The full header is:

```csv
mode,seed,step,drift,theta,raw_surprise,surprise_type,harmful_surprise,tokens_earned,tokens_spent,tokens_decayed,tokens_wasted,token_balance,token_inflation_rate,token_spend_ratio,repair_triggered,repair_name,repair_cost,repair_stake,repair_success
```

### 4.1 Column Definitions

| Column | Type | Description |
|---|---|---|
| `mode` | `str` | Micro-world mode: `lander`, `pressure`, `colony`, `freescape` |
| `seed` | `int` | Random seed for reproducibility |
| `step` | `int` | Simulation step number (0-indexed) |
| `drift` | `float` | Gödel drift magnitude $\delta_{drift}(t)$ — distance between predicted and observed state |
| `theta` | `float` | Current adaptive anomaly threshold $\theta_t$ |
| `raw_surprise` | `bool` | `true` if $\delta_{drift} > \theta_t$ (surprise detected before harmful filter) |
| `surprise_type` | `str` | Classification of surprise: `none`, `drift`, `prediction_error`, `agency_drop`, `criticality_spike`, `loop_detected`, `risk_spike`, `novelty_breakthrough` |
| `harmful_surprise` | `bool` | `true` if surprise passed the harmful filter (tokens earned) |
| `tokens_earned` | `int` | Number of tokens earned this step (0 or 1, or more with multi-token types) |
| `tokens_spent` | `int` | Number of tokens spent this step on repair leases |
| `tokens_decayed` | `float` | Tokens lost to continuous decay this step |
| `tokens_wasted` | `int` | Tokens that expired due to lifetime limit this step |
| `token_balance` | `float` | Current total token balance after all adjustments |
| `token_inflation_rate` | `float` | Running $I_T$ over the trailing window |
| `token_spend_ratio` | `float` | Running $R_{spend}$ over the trailing window |
| `repair_triggered` | `bool` | `true` if a repair was initiated this step |
| `repair_name` | `str` | Name of the repair law that was leased (if any) |
| `repair_cost` | `float` | Token cost of the repair lease |
| `repair_stake` | `float` | Tokens staked as collateral for the repair |
| `repair_success` | `bool` | `true` if the repair improved $PR_{strict}$ (evaluated after lease period) |

### 4.2 Example Rows

```csv
mode,seed,step,drift,theta,raw_surprise,surprise_type,harmful_surprise,tokens_earned,tokens_spent,tokens_decayed,tokens_wasted,token_balance,token_inflation_rate,token_spend_ratio,repair_triggered,repair_name,repair_cost,repair_stake,repair_success
colony,42,0,0.002,0.100,false,none,false,0,0,0.000,0,0.000,0.000,0.000,false,,0.0,0.0,false
colony,42,50,0.145,0.095,true,loop_detected,true,1,0,0.000,0,1.000,0.020,0.000,false,,0.0,0.0,false
colony,42,51,0.003,0.096,false,none,false,0,1,0.010,0,0.990,0.010,0.500,true,loop_breaker,1.0,0.5,true
colony,42,52,0.004,0.096,false,none,false,0,0,0.010,0,0.980,0.008,0.500,false,,0.0,0.0,false
pressure,42,0,0.231,0.100,true,drift,false,0,0,0.000,0,0.000,0.000,0.000,false,,0.0,0.0,false
pressure,42,80,0.567,0.088,true,criticality_spike,true,1,0,0.000,0,1.000,0.012,0.000,false,,0.0,0.0,false
pressure,42,81,0.489,0.089,true,risk_spike,true,1,1,0.010,0,1.990,0.024,0.500,true,pressure_relief,1.0,0.5,false
```

---

## 5. Demo Mechanics

Frame 2 operates across four micro-world modes. Each mode has **controlled breakdowns injected** at predetermined steps to trigger token-earning events. Breakdowns are designed to be realistic failure modes that the system should detect, diagnose, and repair.

### 5.1 Mode: `colony` — Local Loop Trap

**Breakdown**: At step 50 (configurable), the colony agent enters a local loop — it begins cycling between two adjacent cells without making exploration progress. This simulates a common agent failure mode where the policy gets stuck in a local optimum.

**Failure characteristics**:
- $\delta_{drift}$ spikes because the predicted next state (continuing exploration) diverges from the observed next state (looping)
- $\Delta A_{goal} < 0$ because no new cells are being visited
- $P_{stag} > \tau$ because the agent is repeating states
- Surprise type: `loop_detected`

**Expected token flow**:
1. Step 50: Harmful surprise detected → 1 token earned
2. Step 51–52: Repair lease activated (`loop_breaker` law) → 1 token spent as stake
3. Step 53–55: Agent breaks out of loop → goal progress resumes
4. Step 56: Repair evaluated → $\Delta PR_{strict} > 0$ → stake refunded + bonus

### 5.2 Mode: `pressure` — Pressure Spike / Runaway

**Breakdown**: At step 80, a pressure spike occurs in the chamber. The pressure exceeds safe thresholds, triggering a criticality warning. If uncorrected, the pressure continues to rise (runaway) until the system enters a failure state.

**Failure characteristics**:
- $\delta_{drift}$ spikes because the predicted stable-pressure state diverges from the observed pressure-spike state
- $\Delta Crit > 0$ because the system approaches failure boundary
- $R_{risk} > \kappa$ because the risk penalty increases near the failure boundary
- Surprise type: `criticality_spike`, followed by `risk_spike`

**Expected token flow**:
1. Step 80: Criticality surprise → 1 token earned
2. Step 81: Risk spike → 1 additional token earned (danger is escalating)
3. Step 82: Repair lease activated (`pressure_relief` law) → tokens spent
4. Step 83–85: Pressure relief takes effect
5. Step 86: Repair evaluated — if pressure normalized, stake refunded; if not, tokens burned

**Note**: In v4, *every* pressure fluctuation would earn a token, including harmless ones. In v5, only the critical spike earns tokens. Benign fluctuations (steps 0–79, 87+) earn nothing.

### 5.3 Mode: `lander` — Crash Trajectory

**Breakdown**: At step 30, the lander enters a crash trajectory — its descent rate exceeds the safe landing threshold and it is not decelerating. Without intervention, it will crash within 10–15 steps.

**Failure characteristics**:
- $\delta_{drift}$ spikes because the predicted gentle-descent trajectory diverges from the observed crash trajectory
- $\Delta A_{goal} < 0$ because landing progress is reversing
- $R_{risk} > \kappa$ because crash risk is increasing
- Surprise type: `risk_spike` (may also trigger `agency_drop`)

**Expected token flow**:
1. Step 30: Risk spike detected → 1 token earned
2. Step 31: Agency drop confirmed → 1 additional token earned
3. Step 32: Repair lease activated (`emergency_brake` law) → tokens spent
4. Step 33–38: Emergency braking takes effect
5. Step 39: Trajectory corrected → recovery confirmed → stake refunded + bonus

**Recovery scenario**: If the emergency brake fails and the lander crashes (step 40–45):
- Remaining staked tokens are burned (lost)
- System enters failure state → no further token earning until recovery
- Recovery mechanism (if available) may earn additional tokens through `novelty_breakthrough` type

### 5.4 Mode: `freescape` — Collision Pocket / Zone Lock

**Breakdown**: At step 60, the agent enters a collision pocket — a region of the 3D space where obstacles are densely packed. The agent collides repeatedly and becomes locked in a small zone, unable to progress toward the goal.

**Failure characteristics**:
- $\delta_{drift}$ spikes because predicted forward-motion diverges from observed collision
- $P_{stag} > \tau$ because the agent repeats collision-escape-collision cycles
- $\Delta A_{goal} < 0$ because goal-region progress stalls
- Surprise type: `loop_detected` + `agency_drop`

**Expected token flow**:
1. Step 60: Collision detected → surprise triggered → harmful confirmed → 1 token earned
2. Step 61–63: Repeated collisions → additional tokens earned (escalating)
3. Step 64: Repair lease activated (`path_replan` law) → tokens spent
4. Step 65–70: Agent re-plans route around collision pocket
5. Step 71: Path replan successful → stake refunded + bonus

### 5.5 Breakdown Schedule Summary

| Mode | Breakdown Step | Type | Surprise Types | Tokens Expected | Repair Law |
|---|---|---|---|---|---|
| `colony` | 50 | Loop trap | `loop_detected` | 1–2 | `loop_breaker` |
| `pressure` | 80 | Pressure spike | `criticality_spike`, `risk_spike` | 2–3 | `pressure_relief` |
| `lander` | 30 | Crash trajectory | `risk_spike`, `agency_drop` | 2–3 | `emergency_brake` |
| `freescape` | 60 | Collision pocket | `loop_detected`, `agency_drop` | 2–4 | `path_replan` |

---

## 6. Expected Result

### 6.1 v4 vs v5 Token Economy Comparison

Over a 240-step run:

| Metric | v4 | v5 (Expected) |
|---|---|---|
| Total tokens earned | ~200–240 | ~8–16 |
| Total tokens spent | ~0–20 (ad-hoc) | ~6–14 (targeted repairs) |
| Token waste | Not tracked | ~1–3 (expired tokens) |
| Final token balance | ~180–240 | ~2–6 |
| Token inflation rate $I_T$ | ~0.8–1.0 | ~0.0–0.05 |
| Token spend ratio $R_{spend}$ | ~0.0–0.1 | ~0.6–0.9 |
| Meaningful events detected | ~200 (mostly noise) | ~8–16 (all harmful) |

### 6.2 Per-Mode Token Balance Trajectory

**Colony mode**: Token balance rises to 1 at step 50 (loop detected), drops to 0 at step 51 (repair spent), then remains near 0 for the rest of the run. Total tokens earned: 1. Total spent: 1. Waste: 0.

**Pressure mode**: Token balance rises to 2 at steps 80–81 (criticality + risk spike), drops to ~1 after repair at step 82. If repair succeeds, balance returns to ~1 (stake refund). If repair fails, balance drops to 0 (stake burned). Total earned: 2–3. Total spent: 1–2.

**Lander mode**: Token balance rises to 2 at steps 30–31 (risk + agency drop), drops after emergency brake. If landing succeeds: balance returns to ~1. If crash: balance goes to 0. Total earned: 2–3. Total spent: 1–2.

**Freescape mode**: Token balance rises to 2–4 at steps 60–63 (escalating collisions), drops after path replan. If replan succeeds: balance returns to ~1–2. If agent remains stuck: balance decays to 0. Total earned: 2–4. Total spent: 2–3.

### 6.3 Dashboard Confirmation

The token dashboard should show:
- **Token balance plot**: Low, spiky, bounded — not a monotonic ramp
- **Earning events**: Clustered around breakdown steps, sparse elsewhere
- **Spending events**: Follow earning events within 1–3 steps (responsive repair pipeline)
- **Waste bar**: Small but nonzero (expired tokens visible)
- **Inflation rate**: Near zero throughout the run
- **Threshold adaptation**: $\theta_t$ line adjusts smoothly via PID control

---

## 7. Build Files

```
examples/core_tier/v5_demo_02/
├── demo_02_token_metabolism.py    # Main demo runner
├── token_economy.py               # Token metabolism implementation
├── hdc_surprise.py                # Harmful drift classification
├── repair_events.csv              # Log of all repair events
├── token_ledger.jsonl             # Per-step token transactions
├── token_dashboard.html           # Interactive token economy dashboard
└── report_token_metabolism.md     # Auto-generated analysis report
```

### 7.1 File Descriptions

**`demo_02_token_metabolism.py`** — Main entry point. Accepts `--mode`, `--seed`, `--steps`, `--breakdown-step`, `--config` arguments. Runs the specified mode with controlled breakdown injection. Computes token economy metrics at each step and writes telemetry to CSV. Generates the HTML dashboard and Markdown report at completion.

**`token_economy.py`** — Pure Python module implementing the token economy:
- `earn_tokens(drift, theta, delta_ag_goal, delta_crit, p_stag, r_risk, tau, kappa)` → `int`
- `spend_tokens(balance, cost, repair_name)` → `(int, bool)`
- `decay_tokens(balance, decay_rate)` → `float`
- `expire_tokens(token_ages, max_lifetime)` → `(int, list)`
- `compute_inflation_rate(earned_total, spent_total, n_steps)` → `float`
- `compute_spend_ratio(spent_total, earned_total)` → `float`
- `update_threshold_pid(theta, r_anom, r_target, kp, ki, kd, theta_min, theta_max)` → `float`

**`hdc_surprise.py`** — Harmful Drift Classification module:
- `classify_surprise(drift, theta, delta_ag_goal, delta_crit, p_stag, r_risk, tau, kappa)` → `SurpriseClassification`
- `SurpriseClassification` dataclass with fields: `raw_surprise`, `surprise_type`, `harmful`, `drift_magnitude`
- Implements the harmful surprise rule from §3.1

**`repair_events.csv`** — Structured log of all repair events:

```csv
mode,seed,step,trigger_type,repair_law,tokens_staked,tokens_refunded,lease_duration,outcome,pr_before,pr_after,delta_pr
colony,42,50,loop_detected,loop_breaker,1.0,1.5,3,success,0.006,0.012,0.006
pressure,42,80,criticality_spike,pressure_relief,2.0,0.0,5,failure,0.002,0.001,-0.001
```

**`token_ledger.jsonl`** — JSON Lines format, one transaction per line:

```json
{"step": 50, "type": "earn", "amount": 1, "reason": "loop_detected", "balance_after": 1.0}
{"step": 51, "type": "spend", "amount": 1, "reason": "lease:loop_breaker", "balance_after": 0.0}
{"step": 51, "type": "refund", "amount": 1.5, "reason": "lease_success:loop_breaker", "balance_after": 1.5}
```

**`token_dashboard.html`** — Self-contained HTML dashboard (no external dependencies) showing:
- Token balance over time (line chart)
- Token earning events (scatter overlay)
- Token spending events (scatter overlay)
- Token waste accumulation (area chart)
- Inflation rate and spend ratio (gauge charts)
- Anomaly threshold $\theta_t$ adaptation (line chart)
- Per-mode breakdown timeline with repair event annotations

**`report_token_metabolism.md`** — Auto-generated Markdown report summarizing:
- Total tokens earned, spent, decayed, wasted per mode
- Inflation rate and spend ratio per mode
- Repair success rate and cost-effectiveness
- Threshold adaptation statistics (initial vs final $\theta$, convergence time)
- Comparison with v4 token behavior (documented baseline)

---

## 8. Integrated Enhancements 9–16

### Enhancement 9: Multi-Token Types

**Purpose**: Different repair actions require different resources. Exploration, safety, novelty, and repair are qualitatively different activities that should not draw from a single undifferentiated token pool.

**Implementation**: Four token types, each with independent earning and spending rules:

| Token Type | Earned When | Spent On | Decay Rate |
|---|---|---|---|
| `repair_tokens` | Agency drop, loop detection, stagnation | Repair leases for agency failures | $\lambda_r = 0.01$ |
| `explore_tokens` | Novel state visited, coverage gap detected | Exploration leases, mapping actions | $\lambda_e = 0.02$ |
| `safety_tokens` | Criticality spike, risk spike | Safety override leases, emergency protocols | $\lambda_s = 0.005$ |
| `novelty_tokens` | Novelty breakthrough, strategy innovation | Mutation costs, law innovation leases | $\lambda_n = 0.015$ |

**Conversion**: Tokens can be converted between types at a 10% conversion cost:

$$T_{new} = 0.9 \cdot T_{old}$$

This allows the system to shift resources between priorities but penalizes frequent conversion, encouraging efficient token type management.

**Telemetry**: Each token type gets its own balance column: `repair_balance`, `explore_balance`, `safety_balance`, `novelty_balance`. The aggregate `token_balance` is the sum.

### Enhancement 10: Token Collateral for Law Leases

**Purpose**: Align law selection incentives with outcome quality. Laws should not be leased "for free" — the system should have skin in the game.

**Implementation**: When a law $l$ is leased for repair, the system stakes tokens as collateral:

$$\text{stake}(l) = c_{base}(l) \cdot (1 + \text{complexity}(l))$$

Where:
- $c_{base}(l)$ is the base cost of law $l$
- $\text{complexity}(l)$ is a complexity metric (e.g., number of conditions, nesting depth)

**Outcome evaluation**: After the lease period expires, the system evaluates:

| Outcome | Token Action |
|---|---|
| $\Delta PR_{strict} > 0$ (repair succeeded) | Refund stake + bonus (stake × 1.5) |
| $\Delta PR_{strict} = 0$ (no effect) | Refund stake (no bonus, no penalty) |
| $\Delta PR_{strict} < 0$ (repair worsened things) | Burn stake + quarantine law |

**Mechanism**: This creates a **selection pressure** on laws — laws that consistently improve $PR_{strict}$ generate net positive token flow for the system. Laws that fail are expensive, discouraging repeated use. Over time, the token economy naturally favors effective laws.

### Enhancement 11: Surprise Type Classification

**Purpose**: Not all surprises are the same. Different types of surprises should unlock different repair menus and earn different token types.

**Implementation**: The harmful drift classifier (in `hdc_surprise.py`) produces a structured classification:

```python
@dataclass
class SurpriseClassification:
    raw_surprise: bool          # Was anything surprising?
    drift_magnitude: float      # How surprising? (δ_drift)
    surprise_type: str          # Classification label
    harmful: bool               # Did it pass the harmful filter?
    token_type_earned: str      # Which token type to mint
    repair_menu: list[str]      # Which repair laws are eligible
```

**Surprise types and their properties**:

| Surprise Type | Trigger Condition | Token Type | Eligible Repairs |
|---|---|---|---|
| `drift` | State divergence with no specific pattern | `repair_tokens` | General drift correction laws |
| `prediction_error` | World model prediction failed | `repair_tokens` | Model update laws |
| `agency_drop` | $\Delta A_{goal} < 0$ during drift | `repair_tokens` | Agency restoration laws |
| `criticality_spike` | $\Delta Crit > 0$ | `safety_tokens` | Emergency safety laws |
| `loop_detected` | $P_{stag} > \tau$ | `repair_tokens` | Loop-breaking laws |
| `risk_spike` | $R_{risk} > \kappa$ | `safety_tokens` | Risk mitigation laws |
| `novelty_breakthrough` | New strategy discovered | `novelty_tokens` | Innovation laws |

**Repair menu restriction**: When a surprise of type `criticality_spike` occurs, only safety-related repair laws are eligible for lease. The system cannot spend safety tokens on exploration repairs. This enforces resource allocation discipline.

### Enhancement 12: Second-Price Repair Auction

**Purpose**: When multiple repair laws are eligible for a given surprise type, select the most cost-effective one using a mechanism-design approach (Vickrey auction) that incentivizes truthful bidding.

**Implementation**: Each eligible law $l$ submits a bid:

$$\text{Bid}(l) = \frac{\mathbb{E}[\Delta PR_{strict} \mid l]}{\text{token\_cost}(l)}$$

The law with the highest bid wins the lease, but pays the **second-highest bid price** (Vickrey mechanism):

$$\text{Price}_{paid} = \text{Bid}_{second\_highest}$$

**Why second-price?** In a first-price auction, laws would have an incentive to underbid (claim lower cost than actual) to win cheaply. In a second-price auction, the dominant strategy is to bid truthfully — the winning law pays less than or equal to its bid, and losing laws have no incentive to misrepresent. This produces efficient, honest law selection.

**Tie-breaking**: If two laws have equal bids, prefer the law with lower historical variance in $\Delta PR_{strict}$ (more reliable repair).

**Telemetry**: Each auction is logged with bids from all eligible laws, the winner, and the price paid.

### Enhancement 13: Token Inflation Tax

**Purpose**: Prevent runaway token accumulation in edge cases where the harmful surprise rate is consistently above the spending rate. Without a tax, token balances could grow unboundedly during extended breakdown periods.

**Implementation**: If the inflation rate exceeds a threshold, a progressive tax is applied:

$$\text{If } I_T > I_{threshold}: \quad T_{balance} \leftarrow T_{balance} \cdot (1 - \text{tax\_rate})$$

Where:
- $I_{threshold} = 0.1$ (10% inflation per step)
- $\text{tax\_rate} = \min(0.5, \max(0.01, I_T - I_{threshold}))$

The tax is progressive: mild inflation (0.10–0.15) incurs a 1–5% tax, while severe inflation (0.5+) incurs a 50% cap tax. This prevents token balances from growing more than ~2× per 10 steps during high-inflation periods.

**Trigger conditions**: The tax is evaluated at every step. If the trailing-window inflation rate exceeds $I_{threshold}$, the tax is applied before any other token operations (earn, spend, decay). The tax event is logged in the token ledger.

### Enhancement 14: Cross-Mode Token Commons

**Purpose**: In a multi-mode system, some modes are naturally stable (e.g., colony with well-tuned exploration) while others are naturally volatile (e.g., pressure with frequent spikes). Cross-mode token commons allow stable modes to donate surplus repair capacity to struggling modes.

**Implementation**: A shared "commons pool" of tokens is maintained:

$$C_{commons}(t) = C_{commons}(t-1) + \sum_{m \in \text{donors}} D_m(t) - \sum_{m \in \text{recipients}} R_m(t)$$

Where:
- $D_m(t)$ is the donation from mode $m$ at step $t$
- $R_m(t)$ is the receipt by mode $m$ at step $t$

**Donation rules**: A mode donates if:
1. Its token balance exceeds a surplus threshold (e.g., $T_m > 3$)
2. Its $PR_{strict}$ is above its mode average (the mode is doing well)
3. Another mode has $PR_{strict}$ below its mode average and zero token balance

**Donation amount**: $D_m = \min(T_m - T_{surplus}, T_{deficit\_of\_recipient})$, where $T_{surplus}$ is the surplus threshold and $T_{deficit\_of\_recipient}$ is how many tokens the recipient needs.

**Expected flows**:
- `pressure → colony`: Pressure mode may earn safety tokens during spikes that colony does not need, but colony needs repair tokens during loop traps
- `semantic → lander`: Semantic mode may accumulate explore tokens that lander can use for path exploration
- `freescape → pressure`: Freescape's safety surplus can help pressure during criticality spikes

**Anti-gaming**: A mode cannot both donate and receive in the same step. Donation is limited to once per 24 steps to prevent oscillation.

### Enhancement 15: Surprise Replay Buffer

**Purpose**: Maintain a structured memory of past harmful surprises for diagnostic analysis, law testing, and training data generation. Without a replay buffer, each breakdown is an isolated event with no organizational memory.

**Implementation**: A bounded buffer (default: $N = 500$ entries) stores the last $N$ harmful surprises:

```python
@dataclass
class SurpriseReplayEntry:
    step: int
    mode: str
    surprise_type: str
    drift_magnitude: float
    state_before: dict          # World state before surprise
    state_after: dict           # World state after surprise
    failure_type: str           # What kind of failure occurred
    repair_attempted: str       # Name of repair law leased (if any)
    repair_outcome: str         # "success", "failure", "no_repair"
    delta_pr_strict: float      # Change in PR_strict from repair
    tokens_earned: int
    tokens_spent: int
    net_token_flow: float       # earned - spent (negative = net cost)
```

**Usage**:
1. **Diagnostic analysis**: Aggregate statistics on which surprise types are most common, which repairs are most effective, which modes have the highest harmful surprise rate
2. **Law testing**: Replay a surprise entry in a forked micro-world, test a candidate law, compare outcomes without risking the live system
3. **Training data**: Export replay buffer as a dataset for training predictive models that can anticipate harmful surprises before they occur

**Eviction policy**: When the buffer is full, the oldest entry is evicted (FIFO). Critical entries (those that led to law quarantine or system failure) are protected from eviction and promoted to a permanent "critical lessons" buffer.

### Enhancement 16: Token-Backed Mutation Costs

**Purpose**: Law mutation is powerful but risky. Radical mutations should require a resource commitment to prevent frivolous or excessive mutation.

**Implementation**: The cost of mutating law $l$ into variant $l'$ is:

$$C_{mutation}(l \to l') = c_{base} + \eta \cdot \text{complexity}(l')$$

Where:
- $c_{base}$ is a fixed base cost (default: $c_{base} = 2$ tokens)
- $\eta$ is the complexity scaling factor (default: $\eta = 0.5$)
- $\text{complexity}(l')$ is the complexity of the mutated law (number of conditions, nesting depth, etc.)

**Token type requirement**:
- Conservative mutations (parameter tuning, threshold adjustment): `repair_tokens`
- Moderate mutations (condition changes, new branches): `repair_tokens` + `explore_tokens`
- Radical mutations (structural changes, new laws from scratch): `novelty_tokens` (mandatory)

This creates a **mutation hierarchy**: the more radical the change, the more expensive and specific the token requirement. The system cannot attempt a radical mutation unless it has accumulated sufficient novelty tokens through genuine innovation events.

**Failure penalty**: If a mutation fails (see Frame 3, Enhancement 20), the mutation cost is forfeit (tokens burned). This creates selection pressure for well-considered mutations over random experimentation.

---

## 9. Execution Command

```bash
# Single mode with controlled breakdown
python examples/core_tier/v5_demo_02/demo_02_token_metabolism.py \
    --mode colony \
    --seed 42 \
    --steps 240 \
    --breakdown-step 50 \
    --config examples/core_tier/v5_demo_02/token_config.yaml

# All modes with multi-seed batch
python examples/core_tier/v5_demo_02/demo_02_token_metabolism.py \
    --mode all \
    --seeds 42..51 \
    --steps 240 \
    --config examples/core_tier/v5_demo_02/token_config.yaml \
    --output-dir examples/core_tier/v5_demo_02/batch_output/
```

---

## 10. Success Criteria

Frame 2 is considered successful if and only if all of the following hold across the multi-seed batch (seeds 42–51):

1. **Selective minting**: Total tokens earned per 240-step run is < 20 in all modes (vs. v4's ~200+).
2. **Harmful filter**: ≥ 90% of earned tokens correspond to steps where $\Delta A_{goal} < 0$ or $\Delta Crit > 0$ or $P_{stag} > \tau$ or $R_{risk} > \kappa$.
3. **Bounded balance**: Final token balance is < 10 in all modes at step 240.
4. **Spend ratio**: $R_{spend} > 0.5$ in all modes.
5. **Inflation control**: $|I_T| < 0.1$ over the full run.
6. **PID convergence**: $\theta_t$ stabilizes within ±20% of initial value by step 120.
7. **Dashboard generation**: `token_dashboard.html` renders correctly with token balance, earning events, spending events, and threshold adaptation visible.
8. **Token ledger integrity**: `token_ledger.jsonl` balances match telemetry CSV balances for every step.

---

*End of Frame 2 — Token Metabolism + Harmful Surprise Demo Blueprint*
