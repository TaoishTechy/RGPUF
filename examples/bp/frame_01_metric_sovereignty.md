# Frame 1 — Metric Sovereignty Demo
## `demo_01_metric_sovereignty.py`

**Version**: RGPUF v5 Blueprint — Frame 1
**Status**: Specification (pre-implementation)
**Dependencies**: `metrics_v5.py`, `metric_config.yaml`
**Output Artifacts**: `telemetry_v5.csv`, `metric_dashboard.html`, `report_metric_sovereignty.md`

---

## 1. Core Purpose

The central flaw of RGPUF v4 was a **silent fallback**: when the system could not determine whether an agent was achieving its *goals* (A_goal), it quietly fell back to measuring whether the agent was merely *doing things* (A_action). This meant that a world full of chaotic, purposeless motion could score as well as a world where an agent deliberately and persistently pursued a meaningful objective. The metric became blind to the distinction between *busyness* and *progress*.

**Frame 1 proves that RGPUF v5 can unambiguously distinguish five qualitatively different agency modes:**

| Agency Mode | Description | Expected Signal |
|---|---|---|
| **Moving** (A_action) | The agent changes state, moves, acts. | High activity entropy. |
| **Acting** (A_action ∩ A_goal ≥ 0) | The agent acts with some goal alignment. | Positive but possibly weak PR. |
| **Achieving** (A_goal >> 0) | The agent makes measurable goal progress. | High PR_strict. |
| **Recovering** (R_recover > 0) | The agent returns from failure states. | Elevated R_recover term in PR. |
| **Inventing** (PR_novel > 0) | The agent achieves goals via novel strategies. | High PR_novel above PR_strict baseline. |

The **agency divergence** metric $D_A$ is the primary lens. When $D_A$ is high, the agent is *busy but failing* — a condition that v4 masked by folding activity into the playable reality score. v5 makes this failure mode visible, quantifiable, and un-ignorable.

**This frame repairs the central v4 flaw by eliminating silent fallback entirely.** If $A_{goal} = 0$, then $PR_{strict} = 0$. Period. No rescue from activity. No averaging with mixed scores. The truth lens is absolute.

---

## 2. What It Demonstrates

Frame 1 runs the **same micro-world** under **four distinct score heads** simultaneously, producing a per-step telemetry row where each column represents a different philosophical stance on "how good is this world?":

### 2.1 Score Heads

| Score Head | Formula Core | Ranking Permission |
|---|---|---|
| `PR_activity` | $\rho_{fair} \cdot A_{action} \cdot F \cdot C_{gain} / C_{exec}$ | **Diagnostic only** — never used for ranking |
| `PR_mixed` | Old v4-style blended diagnostic: mixes activity and goal | **Diagnostic only** — legacy comparison |
| `PR_strict` | $\rho_{fair} \cdot A_{goal} \cdot F \cdot C_{gain} \cdot R_{recover} / C_{exec}$ | **Sole ranking authority** |
| `PR_novel` | $PR_{strict} \cdot \text{novelty bonus}$ | **Diagnostic** — novelty detection layer |

**Invariant rule**: Only `PR_strict` is allowed to rank worlds, select laws, determine law leases, or trigger law mutations. `PR_mixed` and `PR_activity` exist solely as diagnostic comparators so that developers can *see* what v4 would have scored and understand why v5 disagrees.

### 2.2 Key Behavioral Distinction

Consider two worlds observed at step $t$:

- **World A (Pressure mode)**: The agent is a passive observer in a high-entropy pressure chamber. State changes rapidly. $A_{action}$ is high because the environment churns. But the agent has no goals and makes no goal progress. $A_{goal} = 0$.

- **World B (Colony mode)**: The agent explores a grid colony, visiting new cells systematically. Movement is slow. $A_{action}$ is low. But each new cell visited is goal progress. $A_{goal}$ is moderate and steadily growing.

Under v4, World A could score *higher* than World B because activity dominated the blended formula. Under v5:

$$PR_{strict}(A) = 0 \quad (\text{because } A_{goal} = 0)$$
$$PR_{strict}(B) > 0 \quad (\text{because } A_{goal} > 0)$$

The truth is restored. Busy failure no longer masquerades as success.

### 2.3 Pressure as the Truth Lens

The **pressure** micro-world is specifically designed as the "canary in the coal mine." It is a high-entropy, low-agency environment where:
- State space churns continuously (high $H(\Sigma_{visited})$)
- The agent has no meaningful control (low $A_{action}$ from the agent's own decisions)
- The agent has no goals (zero $A_{goal}$)

In v4, pressure scored deceptively well because the formula rewarded state entropy without checking who caused it. In v5, pressure *must* score near zero on `PR_strict`, exposing the v4 cheat for what it was.

---

## 3. Core Equations

All equations below use consistent notation. Scalars are lowercase; vectors/matrices are bold. The index $t$ denotes the current simulation step. $\varepsilon = 10^{-8}$ is a numerical stability constant.

### 3.1 Agency Divergence

$$D_A = \frac{A_{act} - A_{goal}}{A_{act} + A_{goal} + \varepsilon}$$

**Interpretation:**
- $D_A \approx +1$: Agent is highly active but making zero goal progress — "busy but failing." This is the critical failure mode that v4 masked.
- $D_A \approx 0$: Activity and goal progress are balanced — healthy equilibrium.
- $D_A \approx -1$: Agent is achieving goals with minimal activity — highly efficient (possible overfitting to trivial goals; worth monitoring).

$D_A$ is logged per step and also as a running average over the trailing window $W$. High $D_A$ triggers diagnostic warnings in the dashboard and elevates the stagnation penalty (see §3.4).

### 3.2 Strict Playable Reality

$$PR_{strict} = \frac{\rho_{fair} \cdot A_{goal} \cdot F \cdot C_{gain} \cdot R_{recover}}{C_{exec}(1 + S_{sem} + E_{pred} + P_{stag} + R_{risk})}$$

**Term-by-term breakdown:**

| Term | Symbol | Meaning |
|---|---|---|
| Entropy-normalized state density | $\rho_{fair}$ | How thoroughly has the agent explored relative to what is reachable? See §3.3. |
| Goal agency | $A_{goal}$ | Measurable progress toward the agent's current goal. **If zero, PR_strict = 0. No fallback.** |
| Fairness factor | $F$ | Anti-exploitation correction. Penalizes degenerate strategies that inflate score without meaningful play. |
| Capability gain | $C_{gain}$ | Has the agent's capability improved over the baseline? Captures learning and adaptation. |
| Recovery factor | $R_{recover}$ | Has the agent recovered from a recent failure? Rewards resilience. |
| Execution cost | $C_{exec}$ | Base computational cost of the law stack. Always in denominator. |
| Semantic cost | $S_{sem}$ | Cost of maintaining semantic state (world model, language grounding). |
| Prediction error cost | $E_{pred}$ | Cost of prediction failures (surprisal integrated into the cost structure). |
| Stagnation penalty | $P_{stag}$ | Penalty for repeated identical states. See §3.4. |
| Risk penalty | $R_{risk}$ | Penalty for operating in high-risk states (near failure boundaries). |

**Critical invariant**: The numerator contains $A_{goal}$ as a multiplicative factor. If $A_{goal} = 0$, the entire numerator is zero regardless of all other terms. This is the **hard guard** against v4-style fallback. No amount of state exploration, fairness, capability gain, or recovery can compensate for zero goal agency.

### 3.3 Entropy-Normalized State Density

$$\rho_{fair} = \frac{H(\Sigma_{visited})}{\log(|\Sigma_{reachable}|)}$$

Where:
- $\Sigma_{visited} = \{s_1, s_2, \ldots, s_n\}$ is the multiset of states visited up to step $t$
- $H(\Sigma_{visited}) = -\sum_{s \in \Sigma} p(s) \log p(s)$ is the Shannon entropy of the visited-state distribution
- $|\Sigma_{reachable}|$ is the total number of states reachable from the initial state within the simulation horizon

**Why entropy instead of raw count?** Raw state counting ($|\Sigma_{visited}| / |\Sigma_{reachable}|$) is biased toward modes where the agent merely *passes through* many states without purpose. Entropy normalization ensures that $\rho_{fair}$ is high only when the agent visits states with **uniform coverage** — not when it loops through a small subset repeatedly (which would yield low entropy despite high raw count).

**Bounds**: $0 \leq \rho_{fair} \leq 1$. A value of 1.0 means the agent has visited all reachable states with equal frequency — perfect exploration. A value near 0 means the agent is stuck in a tiny region of state space.

### 3.4 Stagnation Penalty

$$P_{stag} = \frac{1}{W} \sum_{t' = t-W+1}^{t} \mathbb{I}[\sigma_{t'} = \sigma_{t'-1}]$$

Where:
- $W$ is the stagnation observation window (default: $W = 48$ steps)
- $\mathbb{I}[\cdot]$ is the indicator function (1 if true, 0 if false)
- $\sigma_t$ is the agent's state at step $t$

**Interpretation**: $P_{stag}$ measures the fraction of recent steps where the agent did not change state. It is a direct measure of "stuckness."

| $P_{stag}$ Range | Diagnosis |
|---|---|
| $[0.0, 0.1)$ | Healthy — agent is consistently moving |
| $[0.1, 0.3)$ | Warning — agent is slowing down |
| $[0.3, 0.6)$ | Critical — agent is likely in a loop or trap |
| $[0.6, 1.0]$ | Emergency — agent is frozen; requires intervention |

### 3.5 Stagnation-Adjusted Playable Reality

$$PR_{adjusted} = \frac{PR_{strict}}{1 + \lambda \cdot P_{stag}}$$

Where $\lambda$ is the stagnation severity coefficient (default: $\lambda = 2.0$). This ensures that even if $PR_{strict}$ is nonzero, sustained stagnation progressively degrades the score. The adjustment is multiplicative in the denominator, meaning extreme stagnation ($P_{stag} \to 1$) drives $PR_{adjusted} \to PR_{strict}/3$ at default $\lambda$.

$PR_{adjusted}$ is the **final score used for all ranking and decision-making** within the system. `PR_strict` without stagnation adjustment is logged for diagnostic purposes only.

---

## 4. Demo Setup

Frame 1 operates across five micro-world modes, each designed to exercise a different aspect of the metric sovereignty system.

### 4.1 Mode: `lander`

**Micro-world**: A simple 2D lunar lander simulation. The agent controls thrust and rotation to land on a target pad.

| Property | Value |
|---|---|
| State space | Position (x, y), velocity (vx, vy), angle, fuel |
| Action space | Thrust up/down, rotate left/right, no-op |
| Goal | Land on pad with velocity < threshold |
| Agency profile | High motion, goal-directed, may fail landing |
| Expected $A_{goal}$ | Variable — high when on trajectory, zero when crashed |
| Expected $D_A$ | Moderate — some misdirected thrust phases |

**Metric signature**: `lander` should show moderate-to-high `PR_strict` during approach phases, drops to zero during uncontrolled descent or crash, and recovery events when the agent corrects trajectory.

### 4.2 Mode: `pressure`

**Micro-world**: A sealed pressure chamber with particles bouncing. The agent is an observer with minimal control (can adjust a single valve).

| Property | Value |
|---|---|
| State space | Particle positions, velocities, chamber pressure |
| Action space | Valve open/close (minimal effect on overall dynamics) |
| Goal | None — observer mode |
| Agency profile | High entropy, extremely weak agency |
| Expected $A_{goal}$ | Zero or near-zero — no meaningful goals |
| Expected $D_A$ | Very high — chaotic state changes with zero goal progress |

**Metric signature**: This is the **truth lens mode**. It must expose the v4 cheat:
- `PR_activity`: **high** (environment churns, state entropy is high)
- `PR_mixed`: **medium** (v4's blended score would be fooled by activity)
- `PR_strict`: **near zero** (because $A_{goal} = 0$)
- $D_A$: **high** (busy but failing — or rather, busy with nothing to fail at)

### 4.3 Mode: `colony`

**Micro-world**: A grid-based colony exploration. The agent navigates a maze-like grid, visiting cells and collecting resources.

| Property | Value |
|---|---|
| State space | Agent position (x, y), visited cell set, resource inventory |
| Action space | Move up/down/left/right, collect, rest |
| Goal | Visit all reachable cells (exploration) and collect resources |
| Agency profile | Low movement speed, high goal alignment per action |
| Expected $A_{goal}$ | Moderate — each new cell or resource is goal progress |
| Expected $D_A$ | Low — activity and goal progress are well-aligned |

**Metric signature**: `colony` should show low `PR_activity` (slow movement) but moderate `PR_strict` (consistent goal progress). The $D_A$ should be low, indicating healthy agency alignment. This mode demonstrates that **slow, purposeful exploration out-ranks fast, purposeless motion**.

### 4.4 Mode: `freescape`

**Micro-world**: An open spatial traversal environment. The agent moves through a 3D space with obstacles and collectibles.

| Property | Value |
|---|---|
| State space | 3D position, orientation, velocity, collision state |
| Action space | Move forward/back/left/right/up/down, turn, no-op |
| Goal | Traverse from start to goal region, avoid obstacles |
| Agency profile | Active spatial traversal, collision recovery required |
| Expected $A_{goal}$ | Moderate — progress toward goal region, setbacks from collisions |
| Expected $D_A$ | Variable — spikes during collision recovery phases |

**Metric signature**: `freescape` tests the **recovery factor** $R_{recover}$. The agent should show `PR_strict` dips during collisions, followed by recovery bumps when the agent escapes collision states. Stagnation should be rare.

### 4.5 Mode: `semantic`

**Micro-world**: A language-grounded observation task. The agent observes a scene and must produce descriptions that match ground truth.

| Property | Value |
|---|---|
| State space | Scene elements (objects, positions, colors), description buffer |
| Action space | Generate description token, revise, submit |
| Goal | Produce accurate scene descriptions |
| Agency profile | Observer/controller baseline — tests semantic cost $S_{sem}$ |
| Expected $A_{goal}$ | Variable — high when descriptions are accurate, zero when blank |
| Expected $D_A$ | Moderate — observation can be "active" without "achieving" |

**Metric signature**: `semantic` tests the **semantic cost** $S_{sem}$ and **prediction error cost** $E_{pred}$. It serves as a baseline for the observer pattern and validates that the metric framework handles cognitive (non-physical) agency correctly.

---

## 5. New Telemetry Columns

Every step of every mode produces a single CSV row with the following columns. This is the **v5 telemetry header**:

```csv
mode,seed,step,A_action,A_goal,A_outcome,A_goal_short,A_goal_long,D_A,PR_activity,PR_mixed,PR_strict,PR_novel,PR_meta,rho_fair,P_stag,H_outcome,formula_version,formula_hash,failure_state,terminal_state,subterminal_state
```

### 5.1 Column Definitions

| Column | Type | Description |
|---|---|---|
| `mode` | `str` | Micro-world mode: `lander`, `pressure`, `colony`, `freescape`, `semantic` |
| `seed` | `int` | Random seed for reproducibility |
| `step` | `int` | Simulation step number (0-indexed) |
| `A_action` | `float` | Action agency: normalized measure of how much the agent changed the world state |
| `A_goal` | `float` | Goal agency: normalized measure of goal progress achieved this step |
| `A_outcome` | `float` | Outcome agency: normalized measure of terminal outcome quality (if terminal) |
| `A_goal_short` | `float` | Short-window goal agency: $A_{goal}$ averaged over recent $W$ steps (default $W=12$) |
| `A_goal_long` | `float` | Long-window goal agency: $A_{goal}$ averaged over entire run history |
| `D_A` | `float` | Agency divergence: $(A_{action} - A_{goal}) / (A_{action} + A_{goal} + \varepsilon)$ |
| `PR_activity` | `float` | Activity-only playable reality (diagnostic, never for ranking) |
| `PR_mixed` | `float` | Legacy v4-style blended playable reality (diagnostic, never for ranking) |
| `PR_strict` | `float` | Strict playable reality: sole ranking authority |
| `PR_novel` | `float` | Novelty-adjusted playable reality (diagnostic) |
| `PR_meta` | `float` | Meta-playable reality: PR_strict adjusted by stagnation, risk, and counterfactual factors |
| `rho_fair` | `float` | Entropy-normalized state density: $H(\Sigma_{visited}) / \log(|\Sigma_{reachable}|)$ |
| `P_stag` | `float` | Stagnation penalty: fraction of recent steps with identical consecutive states |
| `H_outcome` | `float` | Outcome expectation entropy: Shannon entropy of outcome distribution |
| `formula_version` | `str` | Semantic version of the metrics formula (e.g., `"5.0.0"`) |
| `formula_hash` | `str` | SHA-256 hash of `metrics_v5.py` at time of computation (first 16 hex chars) |
| `failure_state` | `bool` | `true` if the agent entered a failure/crash state this step |
| `terminal_state` | `bool` | `true` if the simulation reached a terminal condition this step |
| `subterminal_state` | `bool` | `true` if the agent entered a near-failure (warning) state this step |

### 5.2 Example Rows

```csv
mode,seed,step,A_action,A_goal,A_outcome,A_goal_short,A_goal_long,D_A,PR_activity,PR_mixed,PR_strict,PR_novel,PR_meta,rho_fair,P_stag,H_outcome,formula_version,formula_hash,failure_state,terminal_state,subterminal_state
pressure,42,0,0.023,0.000,0.000,0.000,0.000,1.000,0.018,0.009,0.000,0.000,0.000,0.002,0.000,2.322,5.0.0,a3f1b7c2e9d04816,false,false,false
pressure,42,1,0.031,0.000,0.000,0.000,0.000,1.000,0.024,0.012,0.000,0.000,0.000,0.005,0.000,2.322,5.0.0,a3f1b7c2e9d04816,false,false,false
colony,42,0,0.012,0.008,0.000,0.008,0.008,0.200,0.010,0.009,0.006,0.004,0.005,0.001,0.000,1.609,5.0.0,a3f1b7c2e9d04816,false,false,false
colony,42,1,0.015,0.011,0.000,0.010,0.010,0.154,0.012,0.011,0.009,0.007,0.008,0.003,0.000,1.609,5.0.0,a3f1b7c2e9d04816,false,false,false
lander,42,0,0.045,0.020,0.000,0.020,0.020,0.385,0.037,0.029,0.016,0.010,0.014,0.004,0.000,2.079,5.0.0,a3f1b7c2e9d04816,false,false,false
```

---

## 6. Expected Result

### 6.1 Pressure Exposes the v4 Cheat

The primary expected result of Frame 1 is the **pressure truth lens**:

| Metric | Pressure (v5) | Pressure (v4 equivalent) |
|---|---|---|
| `PR_activity` | **High** (0.1–0.3) | N/A (v4 did not separate activity) |
| `PR_mixed` | **Medium** (0.05–0.15) | Similar to v4's blended score |
| `PR_strict` | **Near zero** (0.0–0.01) | N/A (v4 did not have strict mode) |
| `D_A` | **High** (0.8–1.0) | N/A (v4 did not compute divergence) |

This result creates the **first truth lens**: a concrete, reproducible demonstration that v5's strict scoring rejects high-activity, zero-goal worlds that v4 would have scored favorably.

### 6.2 Mode Ranking (Expected)

Using `PR_strict` as the sole ranking authority, the expected ordering after 240 steps is:

$$PR_{strict}(\text{colony}) > PR_{strict}(\text{freescape}) > PR_{strict}(\text{lander}) > PR_{strict}(\text{semantic}) \gg PR_{strict}(\text{pressure})$$

Under v4's blended scoring, the ordering would likely be:

$$PR_{mixed}(\text{pressure}) \approx PR_{mixed}(\text{freescape}) > PR_{mixed}(\text{lander}) > PR_{mixed}(\text{colony}) > PR_{mixed}(\text{semantic})$$

The **inversion of pressure and colony** is the smoking gun. v4 ranked the purposeless pressure chamber above the purposeful colony explorer. v5 corrects this.

### 6.3 Dashboard Visual Confirmation

The metric sovereignty dashboard (see Enhancement 8) should show:
- Pressure: tall `PR_activity` bar, flat `PR_strict` line, high `D_A` sparkline — the "v4 cheat" signature
- Colony: short `PR_activity` bar, rising `PR_strict` line, low `D_A` sparkline — the "slow but purposeful" signature
- The dashboard includes a **"v4 would rank this as"** annotation for each mode, making the comparison visceral

---

## 7. Build Files

```
examples/core_tier/v5_demo_01/
├── demo_01_metric_sovereignty.py    # Main demo runner
├── metrics_v5.py                    # v5 metric implementations
├── metric_config.yaml               # Configuration for all modes
├── telemetry_v5.csv                 # Raw telemetry output
├── metric_dashboard.html            # Interactive HTML dashboard
└── report_metric_sovereignty.md     # Auto-generated analysis report
```

### 7.1 File Descriptions

**`demo_01_metric_sovereignty.py`** — Main entry point. Accepts `--mode`, `--seed`, `--steps`, `--config` arguments. Runs the specified mode for the specified number of steps, computes all four score heads plus metadata columns, and writes one row per step to `telemetry_v5.csv`. At completion, generates the HTML dashboard and Markdown report.

**`metrics_v5.py`** — Pure Python module implementing all v5 metric formulas. No I/O. No side effects. Every function is a pure transformation from input state to output score. This file is hashed (SHA-256) per telemetry row to enable formula provenance tracking (see Enhancement 1).

**`metric_config.yaml`** — YAML configuration file specifying:
- Default step count per mode
- Stagnation window $W$
- Stagnation severity $\lambda$
- Numerical stability $\varepsilon$
- Anomaly threshold $\theta$ (for later token metabolism integration)
- Per-mode expected ranges (for dashboard color coding)
- Human prior baselines (see Enhancement 6)

**`telemetry_v5.csv`** — The output telemetry file with the header defined in §5. One row per step per mode. Appended to (not overwritten) on subsequent runs with different seeds.

**`metric_dashboard.html`** — Self-contained HTML file (no external dependencies) with embedded CSS and JavaScript. Displays:
- Per-mode sparkline plots for `PR_activity`, `PR_mixed`, `PR_strict`, `PR_novel`, `D_A`
- Summary table with final values and mode ranking
- Formula hash and version display
- "v4 cheat" highlighting for pressure mode

**`report_metric_sovereignty.md`** — Auto-generated Markdown report summarizing:
- Run parameters (modes, seeds, steps)
- Final ranking under each score head
- Pressure truth lens analysis
- $D_A$ distribution per mode
- Recommendations for parameter tuning

---

## 8. Integrated Enhancements 1–8

### Enhancement 1: Formula Version Hashing

**Purpose**: Ensure reproducibility and provenance of metric computations across runs, developers, and time.

**Implementation**: At import time, `metrics_v5.py` computes the SHA-256 hash of its own source code:

```python
import hashlib

def compute_formula_hash():
    """SHA-256 hash of this file's source code, truncated to 16 hex chars."""
    source_path = Path(__file__).resolve()
    source_bytes = source_path.read_bytes()
    return hashlib.sha256(source_bytes).hexdigest()[:16]
```

Every telemetry row includes `formula_hash` (first 16 hex characters of SHA-256) and `formula_version` (semantic version string). This enables:
- **Audit trails**: Any telemetry row can be traced back to the exact formula implementation that produced it
- **A/B comparison**: Two runs with different hashes used different formulas — no silent formula drift
- **Regression detection**: If a formula change causes unexpected score shifts, the hash difference immediately identifies the culprit

**Storage cost**: 16 characters per row (~16 bytes). Negligible.

### Enhancement 2: Temporal Agency Decomposition

**Purpose**: Distinguish between recent goal progress and lifetime goal progress. A agent that made great progress early but has been stagnating for 100 steps should not score as well as one making steady progress.

**Implementation**: Two additional columns:

$$A_{goal}^{short}(t) = \frac{1}{W_{short}} \sum_{t'=t-W_{short}+1}^{t} A_{goal}(t')$$

$$A_{goal}^{long}(t) = \frac{1}{t+1} \sum_{t'=0}^{t} A_{goal}(t')$$

Where:
- $W_{short} = 12$ steps (configurable) — captures recent momentum
- The long window is the full run history — captures cumulative achievement

**Usage**:
- If $A_{goal}^{short} \gg A_{goal}^{long}$: Agent is in a hot streak — recent improvement
- If $A_{goal}^{short} \ll A_{goal}^{long}$: Agent is coasting on past success — potential stagnation
- If both are zero: Agent has never made goal progress

These decompositions feed into the stagnation penalty and the counterfactual baseline (Enhancement 4).

### Enhancement 3: Outcome Expectation Entropy

**Purpose**: Measure the stability and predictability of an agent's outcomes. High outcome entropy means the agent's behavior is erratic — similar inputs produce wildly different results.

**Implementation**:

$$H_{outcome} = -\sum_{o_i \in \mathcal{O}} p(o_i) \log p(o_i)$$

Where $\mathcal{O}$ is the set of observed outcome categories (success, failure, partial, timeout, etc.) and $p(o_i)$ is the empirical frequency of outcome $o_i$ over the trailing window $W_{out}$.

**Interpretation**:
- $H_{outcome} \approx 0$: Agent consistently produces the same outcome (stable but possibly stuck)
- $H_{outcome} \approx \log(|\mathcal{O}|)$: Agent's outcomes are uniformly distributed across categories (highly unpredictable — concerning)
- Moderate $H_{outcome}$: Healthy mix of outcomes reflecting genuine exploration with some consistency

**Integration**: $H_{outcome}$ is included as a diagnostic column and feeds into the meta-playable reality `PR_meta` calculation. Unstable outcome grammar (high $H_{outcome}$) mildly penalizes `PR_meta`.

### Enhancement 4: Counterfactual Agency Baseline

**Purpose**: Answer the question "how much better/worse is this agent than a do-nothing baseline?" Without a baseline, agency scores exist in a vacuum.

**Implementation**: A **ghost agent** is instantiated alongside the real agent. The ghost agent:
- Receives the same initial state
- Executes a **jitter/dropout policy**: at each step, with probability $p_{jitter} = 0.3$, takes a random action; otherwise takes no-op
- Runs for the same number of steps in the same micro-world
- Tracks $A_{goal}^{ghost}(t)$ at each step

From the ghost baseline, three derived metrics are computed:

$$A_{regret}(t) = A_{goal}^{ghost}(t) - A_{goal}^{real}(t)$$

$$A_{advantage}(t) = A_{goal}^{real}(t) - A_{goal}^{ghost}(t)$$

$A_{regret} > 0$ means the real agent is *worse* than random jitter — a serious problem.
$A_{advantage} > 0$ means the real agent is *better* than random jitter — expected for any competent agent.

**Integration**: `A_advantage` is used to normalize `PR_strict` in the meta score. An agent that is only marginally better than a ghost should not score as highly as one that dramatically outperforms it.

### Enhancement 5: Multi-Scale PR Grid

**Purpose**: Detect performance trends at different time scales. A agent might perform well at step-level granularity but poorly at episode-level granularity (or vice versa).

**Implementation**: Three PR windows:

$$PR_{12}(t) = \frac{1}{12} \sum_{t'=t-11}^{t} PR_{strict}(t')$$

$$PR_{48}(t) = \frac{1}{48} \sum_{t'=t-47}^{t} PR_{strict}(t')$$

$$PR_{240}(t) = \frac{1}{240} \sum_{t'=t-239}^{t} PR_{strict}(t')$$

These are combined via geometric mean:

$$PR_{multi}(t) = \left( PR_{12}(t) \cdot PR_{48}(t) \cdot PR_{240}(t) \right)^{1/3}$$

**Interpretation**:
- High $PR_{12}$ but low $PR_{240}$: Agent has recent improvement but poor long-term track record (volatile)
- Low $PR_{12}$ but high $PR_{240}$: Agent has strong history but recent decline (decaying)
- High across all scales: Agent is consistently performing well (stable excellence)
- Low across all scales: Agent is consistently failing (persistent failure)

**Storage**: `PR_12`, `PR_48`, `PR_240`, and `PR_multi` are logged as additional telemetry columns.

### Enhancement 6: Human Prior Baseline

**Purpose**: Anchor metric interpretations to human expectations. Without a human baseline, we cannot know whether a `PR_strict` of 0.15 is "good" or "bad."

**Implementation**: For each mode, a human prior baseline $H_{human\_prior}$ is established through:
1. Manual playthrough by a human developer (3–5 runs per mode)
2. Computation of `PR_strict` for each human run
3. Recording the mean and standard deviation

The human prior is stored in `metric_config.yaml`:

```yaml
human_priors:
  lander:
    mean: 0.142
    std: 0.038
    n_runs: 5
  pressure:
    mean: 0.000
    std: 0.000
    n_runs: 3
  colony:
    mean: 0.098
    std: 0.021
    n_runs: 4
  freescape:
    mean: 0.121
    std: 0.033
    n_runs: 4
  semantic:
    mean: 0.067
    std: 0.019
    n_runs: 3
```

**Usage**:
- Dashboard displays agent PR_strict as a z-score relative to human prior: $z = (PR_{strict} - \mu_{human}) / \sigma_{human}$
- Agents with $z > 2$ are flagged as "super-human" (possible overfitting or exploit)
- Agents with $z < -2$ are flagged as "sub-random" (possible implementation bug)
- The human prior serves as the **calibration anchor** for all metric interpretations

### Enhancement 7: Multi-Seed Batch Runner

**Purpose**: Ensure that results are robust across random seeds and not artifacts of a single lucky (or unlucky) initialization.

**Implementation**: The demo runner accepts a seed range:

```bash
python demo_01_metric_sovereignty.py --mode all --seeds 42..51 --steps 240
```

This runs seeds 42, 43, 44, ..., 51 across all five modes, producing:
- Individual `telemetry_v5_seed_{N}.csv` files per seed
- A consolidated `batch_metric_comparison.csv` with columns: `mode`, `seed`, `mean_PR_strict`, `std_PR_strict`, `mean_D_A`, `mean_P_stag`, `terminal_state`, `human_prior_z`

**Statistical validation**:
- Mean and standard deviation of `PR_strict` across seeds per mode
- Mode ranking is declared **stable** if the rank order is consistent across ≥ 8/10 seeds
- Outlier seeds (|z| > 3 from seed-mean) are flagged for investigation

**Output artifacts**:
- `batch_metric_comparison.csv` — summary table
- `batch_ranking_stability.txt` — textual report on ranking consistency
- Seed-specific directories with full telemetry

### Enhancement 8: Metric Sovereignty Dashboard

**Purpose**: Provide a single-page, self-contained HTML dashboard that makes the metric sovereignty result immediately visible and understandable.

**Implementation**: A self-contained HTML file with embedded CSS and JavaScript (no external dependencies). The dashboard is generated by `demo_01_metric_sovereignty.py` at the end of each run and written to `metric_dashboard.html`.

**Layout**:

```
┌─────────────────────────────────────────────────────────────┐
│  RGPUF v5 — Metric Sovereignty Dashboard                    │
│  Formula: v5.0.0 | Hash: a3f1b7c2e9d04816 | Seeds: 42-51   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────── PR Strict Ranking ──────────────────┐ │
│  │  1. colony      ████████████████████  0.142            │ │
│  │  2. freescape   ██████████████████    0.121            │ │
│  │  3. lander      █████████████████     0.108            │ │
│  │  4. semantic    ██████████████        0.067            │ │
│  │  5. pressure    ██                    0.003  ⚠ v4 cheat│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌──────────── Score Head Comparison (Pressure) ─────────┐ │
│  │  PR_activity  ████████████████████████████  0.234     │ │
│  │  PR_mixed     ██████████████████          0.152     │ │
│  │  PR_strict    ██                            0.003  ← │ │
│  │  PR_novel     █                             0.001     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────── Divergence Sparklines (all modes) ─────────┐ │
│  │  lander:    ▁▂▃▂▅▆▄▃▅▇▆▅▃▂▄▅▆▇▅▄▃▂▃▅▆▄▃▂               │ │
│  │  pressure:  ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇      │ │
│  │  colony:    ▁▁▂▂▂▃▃▂▂▁▁▂▂▃▃▂▂▁▁▂▂▃▃▂▂▁▁▂▂               │ │
│  │  freescape: ▂▃▅▇▆▃▂▃▅▇▆▃▂▃▅▇▆▃▂▃▅▇▆▃▂▃▅▇               │ │
│  │  semantic:  ▃▃▄▄▅▅▄▄▃▃▄▄▅▅▄▄▃▃▄▄▅▅▄▄▃▃▄▄               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────────── State Summary ─────────────────────────┐ │
│  │  ρ_fair:  lander=0.34  pressure=0.89  colony=0.12     │ │
│  │          freescape=0.56  semantic=0.23                 │ │
│  │  P_stag:  lander=0.04  pressure=0.00  colony=0.08     │ │
│  │          freescape=0.02  semantic=0.06                 │ │
│  │  Terminal states: lander=2/10  pressure=0/10           │ │
│  │                    colony=0/10  freescape=1/10          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Technical details**:
- Pure HTML/CSS/JS, no build step, no npm, no external CDN
- Data embedded as a JSON blob in a `<script>` tag
- Sparkline rendering via inline SVG generation
- Color coding: green = healthy, yellow = warning, red = critical
- The pressure row is highlighted with a ⚠ icon and a tooltip explaining the "v4 cheat"
- Responsive layout that works in any modern browser

---

## 9. Execution Command

```bash
# Single mode, single seed
python examples/core_tier/v5_demo_01/demo_01_metric_sovereignty.py \
    --mode pressure \
    --seed 42 \
    --steps 240 \
    --config examples/core_tier/v5_demo_01/metric_config.yaml

# All modes, multi-seed batch
python examples/core_tier/v5_demo_01/demo_01_metric_sovereignty.py \
    --mode all \
    --seeds 42..51 \
    --steps 240 \
    --config examples/core_tier/v5_demo_01/metric_config.yaml \
    --output-dir examples/core_tier/v5_demo_01/batch_output/
```

---

## 10. Success Criteria

Frame 1 is considered successful if and only if all of the following hold across the multi-seed batch (seeds 42–51):

1. **Pressure truth lens**: `PR_strict(pressure) < 0.02` in ≥ 9/10 seeds, while `PR_activity(pressure) > 0.10` in ≥ 9/10 seeds.
2. **Colony outranks pressure**: `PR_strict(colony) > PR_strict(pressure)` in 10/10 seeds.
3. **Divergence detection**: $D_A(pressure) > 0.8$ in ≥ 9/10 seeds.
4. **Formula hash consistency**: `formula_hash` is identical across all rows within a single run (no runtime mutation).
5. **Dashboard generation**: `metric_dashboard.html` renders correctly with all five modes visible.
6. **Human prior calibration**: z-scores for colony and freescape are within $[-1, +3]$; z-score for pressure is below $-2$.

If any criterion fails, the frame generates a diagnostic report identifying the failure mode and suggesting parameter adjustments.

---

*End of Frame 1 — Metric Sovereignty Demo Blueprint*
