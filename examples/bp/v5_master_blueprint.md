# RGPUF v5 — Sovereign Novelty Forge (Updated)
## 6 Blueprint Frames + 48 Integrated Enhancements

The six frames build upward like a ladder: **truth metrics → bounded tokens → accountable laws → meaningful failure/recovery → semantic repair control → alien novelty generation.** Each frame depends on the one below it. Frame 1 establishes that the system can tell truth from noise. Frame 2 gives it an economy to act on what it learns. Frame 3 makes laws testable organisms rather than static rules. Frame 4 gives every micro-world its own failure grammar so that recovery is meaningful. Frame 5 promotes the semantic observer into a causal director that spends tokens and leases laws to repair other modes. Frame 6 goes beyond human playability entirely, inventing strange but recoverable novelty that survives across seeds.

> **The aim is not merely "better v4."** The aim is a self-auditing, self-repairing, self-evolving retro-physics forge where micro-worlds are measured, repaired, stressed, mutated, and made strange.

---

## Shared v5 Thesis

```
RGPUF Lab v5 measures not whether a micro-world moves,
but whether its smallest executable law stack produces
controllable, goal-directed, recoverable, compressible,
and eventually novel play.
```

v4 proved the architecture can hold:

```
LawStack / Goal Agency / Prediction Model / HDC Drift
/ Gödel Tokens / DLASc / Optimizer / Reports / Micro-World Recipes
```

v5 must enforce:

```
No PR without goal truth.
No tokens without harmful surprise.
No laws without measured contribution.
No semantic mode without causal repair.
No optimizer victory without cross-seed robustness.
No novelty without recoverability.
```

---

## Recommended Build Order

```
1. Metric Sovereignty
2. Token Metabolism
3. Law Ecology
4. Mode Grammar / Recoverable Failure
5. Semantic META-K Controller
6. Alien Novelty Forge
```

---

## Minimal v5 File Structure

```
examples/core_tier/v5/
  core/
    metrics_v5.py
    token_economy.py
    law_ecology.py
    mode_grammars.py
    failure_injector.py
    semantic_controller.py
    repair_planner.py
    repair_auction.py
    novelty_metrics.py
    law_forge.py
  demos/
    demo_01_metric_sovereignty.py
    demo_02_token_metabolism.py
    demo_03_law_ecology.py
    demo_04_mode_grammar.py
    demo_05_meta_k_controller.py
    demo_06_alien_novelty_forge.py
  data/
    telemetry/
    reports/
    recipes/
    law_provenance/
    born_laws/
    dashboards/
  README.md
```

---

## Frame 1 — Metric Sovereignty Demo

**Demo file:** `demo_01_metric_sovereignty.py`

**Core purpose:** Prove RGPUF can distinguish *moving* / *acting* / *achieving* / *recovering* / *inventing*. This repairs the central v4 flaw: **silent fallback from goal agency to action agency.** In v4, when goal agency was hard to compute, the system quietly fell back to measuring mere activity. v5 makes this fallback impossible — if there is no goal progress, PR is zero.

**What it demonstrates:** Run the same micro-world under four score heads:

- **PR_activity** — Did the agent do anything at all? (Trivially satisfied by any motion.)
- **PR_mixed** — Old-style diagnostic that blends activity with goal progress, masking the gap.
- **PR_strict** — Did it achieve *goal* progress? (Only this one actually measures meaningful play.)
- **PR_novel** — Did it achieve goal progress in a *novel* way?

Only PR_strict honestly ranks worlds. PR_activity and PR_mixed can be gamed; PR_strict cannot.

### Core Equations

**Agency Divergence:**

$$D_A = \frac{A_{act} - A_{goal}}{A_{act} + A_{goal} + \varepsilon}$$

High $D_A$ means the agent is "busy but failing" — lots of activity, no goal progress. This is the core diagnostic that v4 lacked.

**Strict Playable Reality:**

$$PR_{strict} = \frac{\rho_{fair} \cdot A_{goal} \cdot F \cdot C_{gain} \cdot R_{recover}}{C_{exec}(1 + S_{sem} + E_{pred} + P_{stag} + R_{risk})}$$

If $A_{goal} = 0$, then $PR_{strict} = 0$. **No fallback.** This is the central enforcement. Activity without goal truth scores nothing.

**Entropy-Normalized State Density:**

$$\rho_{fair} = \frac{H(\Sigma_{visited})}{\log(|\Sigma_{reachable}|)}$$

Normalizes state exploration by the entropy of the reachable state space, so small-world modes are not penalized for visiting fewer states.

**Stagnation Penalty:**

$$P_{stag} = \frac{1}{W} \sum_{t} \mathbb{I}[\sigma_t = \sigma_{t-1}]$$

Measures the fraction of time steps within the window $W$ where the agent visits the same state consecutively.

**Stagnation-Adjusted PR:**

$$PR_{adjusted} = \frac{PR}{1 + \lambda \cdot P_{stag}}$$

Applies a penalty proportional to stagnation frequency, ensuring that even a well-scoring world is penalized for looping.

### Demo Setup Modes

| Mode        | Primary Signal           | Agency Profile                          |
|-------------|--------------------------|-----------------------------------------|
| **Lander**  | Motion                   | May fail landing                        |
| **Pressure**| Entropy                  | Weak agency                             |
| **Colony**  | Low movement             | Meaningful exploration                  |
| **Freescape**| Spatial traversal       | Collision recovery                      |
| **Semantic**| Observer/controller      | Baseline for meta-level scoring         |

### New Telemetry Columns (Full CSV Header)

```csv
mode,seed,step,A_action,A_goal,A_outcome,A_goal_short,A_goal_long,D_A,
PR_activity,PR_mixed,PR_strict,PR_novel,PR_meta,rho_fair,P_stag,
H_outcome,formula_version,formula_hash,failure_state,terminal_state,
subterminal_state
```

### Expected Result

**Pressure mode exposes the v4 cheat:** The agent jittering in pressure space produces:

- `PR_activity` = **high** (agent is doing something)
- `PR_mixed` = **medium** (blended score masks the problem)
- `PR_strict` ≈ **0** (no actual goal progress)
- `D_A` = **high** (busy but failing)

This is the canonical demonstration that v5's strict metrics catch what v4 missed.

### Build Files

- `core/metrics_v5.py` — All metric heads, agency decomposition, formula versioning
- `demos/demo_01_metric_sovereignty.py` — Five-mode comparison runner
- `data/telemetry/metric_sovereignty_run.csv` — Per-step telemetry output
- `data/dashboards/metric_sovereignty.html` — Interactive comparison dashboard

---

### Integrated Enhancements 1–8

**1. Formula Version Hashing**

Every row of telemetry stores a SHA-256 hash of the `metrics_v5.py` source at the time the metric was computed. This ensures reproducibility and makes it possible to audit whether a score was produced by the correct formula version. The hash is computed once at import time and stored in `formula_hash`.

```python
import hashlib

def compute_formula_hash(source_path="core/metrics_v5.py"):
    with open(source_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
```

**2. Temporal Agency Decomposition**

Decompose goal agency into two time scales:

- $A_{goal,short}$ — goal agency measured over the last $W$ steps (e.g., $W=12$), capturing recent progress.
- $A_{goal,long}$ — goal agency measured over the entire run, capturing cumulative progress.

This allows detection of agents that achieved goals early and stagnated ($A_{goal,long}$ high, $A_{goal,short}$ low) versus agents that are currently improving ($A_{goal,short}$ high).

**3. Outcome Expectation Entropy**

$$H_{outcome} = -\sum_i p(o_i) \log p(o_i)$$

Where $p(o_i)$ is the empirical frequency of outcome $o_i$ (terminal state) over recent windows. High $H_{outcome}$ means the system is exploring diverse outcomes; low $H_{outcome}$ means it is converging on a single outcome repeatedly. This complements stagnation detection by measuring *outcome* diversity rather than *state* repetition.

**4. Counterfactual Agency Baseline**

Run a "ghost agent" alongside the real agent. The ghost agent applies jitter and random dropout to actions, providing a baseline for what random behavior would achieve. From this we compute:

- $A_{regret} = A_{goal,ghost} - A_{goal,agent}$ — if positive, the ghost outperformed the real agent.
- $A_{advantage} = A_{goal,agent} - A_{goal,ghost}$ — if positive, the real agent meaningfully outperforms random.

This prevents the system from crediting an agent for outcomes that random exploration would have produced anyway.

**5. Multi-Scale PR Grid**

Compute PR at three window scales:

- $PR_{12}$ — PR over the last 12 steps
- $PR_{48}$ — PR over the last 48 steps
- $PR_{240}$ — PR over the last 240 steps

Geometric mean across scales:

$$PR_{multi} = (PR_{12} \cdot PR_{48} \cdot PR_{240})^{1/3}$$

This ensures that an agent cannot game a single time scale. An agent that spikes briefly at scale 12 but decays at scale 48 and 240 will have a low $PR_{multi}$.

**6. Human Prior Baseline**

For each mode, define a fixed $H_{human\_prior}$ — the PR that a human-designed baseline agent would achieve. This provides an absolute reference: $PR_{strict} > H_{human\_prior}$ means the system has exceeded human design; $PR_{strict} < H_{human\_prior}$ means it has not. The prior is stored per mode and updated only when human play data is explicitly provided.

**7. Multi-Seed Batch Runner**

Run all five modes across seeds 42–51 (10 seeds per mode = 50 runs total). Each run produces a full telemetry CSV. The batch runner aggregates results into:

- Per-mode mean/std of all PR heads
- Per-seed stability analysis
- Cross-seed correlation of PR_strict with mode characteristics

```python
SEEDS = range(42, 52)
MODES = ["lander", "pressure", "colony", "freescape", "semantic"]

for mode in MODES:
    for seed in SEEDS:
        run_metric_sovereignty(mode=mode, seed=seed, steps=500)
```

**8. Metric Sovereignty Dashboard**

An HTML/Flask dashboard displaying per-run and aggregated results:

- PR_activity vs PR_mixed vs PR_strict vs PR_novel (grouped bar chart)
- $D_A$ sparkline per run (highlights busy-but-failing runs)
- $\rho_{fair}$ distribution across modes
- Terminal state frequency pie chart
- Formula hash verification badge (green = hash matches current source)
- Seed-by-seed comparison table

---

## Frame 2 — Token Metabolism + Harmful Surprise Demo

**Demo file:** `demo_02_token_metabolism.py`

**Core purpose:** Turn Gödel tokens from passive drift counters into a real adaptive economy. Tokens must be **earned, spent, decayed, wasted, staked, and converted.** v4 minted approximately one token per time step regardless of whether anything meaningful happened. v5 ties token creation exclusively to *harmful surprise* — tokens appear only when the system encounters a breakdown that actually damages agency, safety, novelty, or recoverability.

**What it demonstrates:** The system earns tokens only when surprise harms the micro-world in a measurable way. Tokens are spent on repair leases. Unused tokens decay. Misallocated tokens are wasted (spent on repairs that fail). The economy remains bounded, transparent, and accountable.

### Core Equations

**Harmful Surprise Rule:**

$$T_{earned}(t) = \mathbb{I}\left[(\delta_{drift} > \theta_t) \wedge (\Delta A_{goal} < 0 \vee \Delta Crit > 0 \vee P_{stag} > \tau \vee R_{risk} > \kappa)\right]$$

A token is earned only when: (1) drift exceeds the adaptive anomaly threshold $\theta_t$, **and** (2) the surprise actually caused harm — either goal agency decreased, criticality spiked, stagnation exceeded tolerance, or recovery risk rose above threshold. Mere surprise without harm produces no tokens.

**Token Metabolism:**

$$T_{t+1} = T_t(1 - \lambda) + T_{earned} - T_{spent} - T_{waste}$$

Where $\lambda$ is the decay rate (e.g., 0.01 per step). Tokens naturally decay over time, preventing unbounded accumulation. Earned tokens are added; spent tokens (on successful repair leases) and wasted tokens (on failed repair attempts) are subtracted.

**Token Inflation Rate:**

$$I_T = \frac{T_{earned} - T_{spent}}{N_{steps}}$$

Tracks whether the system is minting tokens faster than it spends them. A positive $I_T$ means token supply is growing; negative means it is shrinking. Healthy systems maintain $I_T$ near zero — tokens are earned and spent in rough balance.

**Token Spend Ratio:**

$$R_{spend} = \frac{T_{spent}}{\max(T_{earned}, 1)}$$

The fraction of earned tokens that were productively spent on repairs. Low $R_{spend}$ means the system is earning tokens but not using them (hoarding or wasted repairs). High $R_{spend}$ means the token economy is active and productive.

**Adaptive Anomaly Threshold (PID Controller):**

$$\theta_{t+1} = \theta_t + k_p(r_{anom} - r_{target}) + k_i \sum(r_{anom} - r_{target}) + k_d \cdot \Delta r_{anom}$$

Where:
- $r_{anom}$ = current harmful anomaly rate (fraction of steps with harmful surprise)
- $r_{target}$ = target harmful anomaly rate (5–10%)
- $k_p, k_i, k_d$ = proportional, integral, derivative gains

The PID controller dynamically adjusts the sensitivity of the surprise detector. If the anomaly rate is too high (too many tokens minted), $\theta$ rises to filter out minor surprises. If too low (system is under-reacting), $\theta$ drops to catch subtler breakdowns.

### New Telemetry Columns (CSV)

```csv
drift,theta,raw_surprise,surprise_type,harmful_surprise,tokens_earned,
tokens_spent,tokens_decayed,tokens_wasted,token_balance,
token_inflation_rate,token_spend_ratio,repair_triggered,
repair_name,repair_cost,repair_stake,repair_success
```

### Demo Mechanics

Inject controlled breakdowns into each mode and observe the token economy's response:

| Mode        | Breakdown Injected                | Expected Token Response                          |
|-------------|-----------------------------------|-------------------------------------------------|
| **Colony**  | Loop trap — agent cycles 4 cells  | Tokens earned when $A_{goal}$ drops             |
| **Pressure**| Spike / runaway pressure event    | Tokens earned when $\Delta Crit > 0$            |
| **Lander**  | Crash trajectory injection        | Tokens earned when $R_{risk} > \kappa$          |
| **Freescape**| Collision pocket / zone lock     | Tokens earned when $P_{stag} > \tau$            |

Tokens appear **only** when the breakdown measurably affects agency, criticality, stagnation, or risk. Tokens are then spent on repair leases (see Frame 5 for repair auction mechanics).

### Expected Result

- **v4 behavior:** ~1 token minted per step regardless of context. Token balance grows unboundedly. Tokens are meaningless.
- **v5 behavior:** Tokens earned only during meaningful breakdown events. Balance remains bounded (e.g., 0–20 tokens). Decay prevents hoarding. Spend ratio is healthy (tokens earned ≈ tokens spent + tokens wasted). Waste is visible and traceable to specific failed repair attempts.

### Build Files

- `core/token_economy.py` — Token metabolism, adaptive threshold, inflation tracking
- `demos/demo_02_token_metabolism.py` — Controlled breakdown injection + token response
- `data/telemetry/token_metabolism_run.csv` — Per-step token telemetry
- `data/dashboards/token_economy.html` — Token balance, inflation, spend ratio charts

---

### Integrated Enhancements 9–16

**9. Multi-Token Types**

Instead of a single generic token, v5 introduces four specialized token types:

- **repair_tokens** — earned when repairable breakdowns occur, spent on repair leases
- **explore_tokens** — earned when the system discovers new states, spent on exploration actions
- **safety_tokens** — earned when criticality spikes are detected, spent on safety interventions
- **novelty_tokens** — earned when alien novelty is generated, spent on law mutation and forge operations

Each token type has its own balance, decay rate, and spend rules. This prevents the system from spending repair tokens on exploration, or novelty tokens on safety — each economy is purpose-bound.

**10. Token Collateral for Law Leases**

To lease a law from the law ecology (Frame 3), the system must **stake** tokens as collateral:

- If $\Delta PR_{strict} > 0$ after the lease period: tokens refunded **with bonus** (interest for successful repair).
- If $\Delta PR_{strict} \leq 0$: tokens **burned** (penalty for failed repair).
- If the law causes catastrophic failure: tokens burned **and** the law is sent to **quarantine**.

This creates real economic consequences for law leasing, preventing frivolous or speculative law activation.

**11. Surprise Type Classification**

Each surprise event is classified into one of seven types:

- `drift` — standard HDC drift exceeding threshold
- `prediction_error` — predicted next state diverges from actual
- `agency_drop` — measurable decrease in $A_{goal}$
- `criticality_spike` — system enters critical or dangerous state
- `loop_detected` — state cycle detected (stagnation)
- `risk_spike` — recovery risk exceeds threshold
- `novelty_breakthrough` — unexpected positive discovery

Only `drift`, `agency_drop`, `criticality_spike`, `loop_detected`, and `risk_spike` can trigger token earning. `novelty_breakthrough` is logged but does not earn repair tokens (it may earn novelty tokens instead).

**12. Second-Price Repair Auction**

When multiple repair candidates are available, a second-price auction determines which repair wins:

$$Bid(l) = \frac{\mathbb{E}[\Delta PR_{strict}]}{token\_cost_l}$$

The law with the highest expected value-per-token bid wins, but pays only the **second-highest** bid price. This incentivizes truthful bidding — candidates cannot overbid without risking paying more than necessary.

**13. Token Inflation Tax**

If $I_T > threshold$ (e.g., inflation rate exceeds 0.5 tokens per 100 steps), apply an inflation tax:

$$T_{balance} \leftarrow T_{balance} \cdot (1 - tax)$$

This prevents token accumulation from degrading the meaning of the token economy. The tax rate is proportional to the degree of inflation.

**14. Cross-Mode Token Commons**

Modes that maintain stable, healthy operation accumulate surplus tokens. These surpluses are donated to a **commons pool** that failing modes can draw from. The donation rule:

- If mode $i$ has $T_{balance,i} > T_{donate\_threshold}$ for $N_{stable}$ consecutive steps: donate excess to commons.
- If mode $j$ has $T_{balance,j} < T_{emergency\_threshold}$: draw from commons (up to $T_{max\_draw}$ per step).

This creates a cooperative token economy where stable modes subsidize struggling modes.

**15. Surprise Replay Buffer**

Maintain a buffer of the last $N$ harmful surprise events (e.g., $N=1000$). Each entry contains:

```json
{
  "timestamp": 3847,
  "mode": "colony",
  "state_before": {"position": [5, 3], "energy": 0.72, "visited_count": 12},
  "state_after": {"position": [5, 4], "energy": 0.71, "visited_count": 13},
  "drift": 0.34,
  "failure_type": "loop_detected",
  "repair_attempted": "anti_loop_bfs_agent",
  "repair_outcome": "success",
  "delta_pr_strict": 0.08
}
```

This buffer enables:
- Pattern analysis of recurring failure modes
- Training of repair impact predictors (enhancement 34)
- Replay-based counterfactual analysis (enhancement 35)

**16. Token-Backed Mutation Costs**

Mutating a law (Frame 3 / Frame 6) costs tokens:

$$Cost_{mutation}(l_{new}) = c_{base} + \eta \cdot complexity(l_{new})$$

Where $complexity(l_{new})$ measures the size/complexity of the new law (e.g., number of terms, nesting depth, runtime estimate). More complex mutations cost more tokens, creating an incentive for parsimonious law design. The cost is paid from novelty_tokens for Frame 6 mutations and repair_tokens for Frame 3 repair-driven mutations.

---

## Frame 3 — Law Ecology + Dead-Law Quarantine Demo

**Demo file:** `demo_03_law_ecology.py`

**Core purpose:** Prove that laws are **testable organisms** — not static rules, but entities with measurable utility, ablation sensitivity, pairwise synergy, quarantine status, provenance records, mutation history, and lineage tracking. Laws that do not contribute are identified, deprioritized, and eventually archived. Laws that contribute synergistically are protected even when individually weak.

**What it demonstrates:** Every $N$ steps, the system runs a full law stack evaluation: disable one law at a time, measure $\Delta PR_{strict}$, update each law's utility score, scan pairwise synergy between laws, and decide whether each law should remain active, be leased to a specific mode, be mutated for improvement, be quarantined for investigation, or be archived as a fossil.

### Core Equations

**Law Utility (Ablation Test):**

$$U(l) = PR_{strict}(\mathcal{L}) - PR_{strict}(\mathcal{L} \setminus \{l\})$$

The utility of law $l$ is the drop in PR_strict when that law is removed from the active law stack $\mathcal{L}$. High $U(l)$ means the law is essential; $U(l) \leq 0$ means removing the law does not hurt (or helps) the system — a candidate for quarantine or archival.

**Law Synergy:**

$$Syn(l_i, l_j) = PR(l_i, l_j) - PR(l_i) - PR(l_j) + PR(\emptyset)$$

Measures whether two laws are more valuable together than the sum of their individual contributions. Positive synergy means the laws amplify each other; negative synergy means they interfere. Laws with high positive synergy are protected as keystone pairs.

**Functional Law Cost:**

$$C_{exec}(\mathcal{L}) = \sum_l c_{base}(l) + \alpha \cdot runtime_l + \beta \cdot memory_l - \gamma \cdot U(l) - \delta \cdot Syn(l)$$

The effective cost of maintaining a law stack, net of its utility and synergy contributions. Laws that cost more than they contribute increase $C_{exec}$ and reduce PR.

### Law States

Each law exists in one of eight states:

| State         | Description                                                          |
|---------------|----------------------------------------------------------------------|
| **active**    | Currently running, contributing to the law stack                     |
| **leased**    | Temporarily activated for a specific mode or repair                  |
| **embryo**    | Newly born law, running in sandbox before full activation            |
| **dormant**   | Not running, stored in cryo, resurrectable if needed                 |
| **quarantined**| Suspected harmful or useless, under investigation                   |
| **archived**  | Permanently removed, fossilized with full provenance                 |
| **mutating**  | Currently undergoing mutation in a sandbox                           |
| **fossilized**| Archived law preserved as historical record                          |

### Law Metadata Example

```json
{
  "law_name": "wall_following_agent",
  "category": "agent_law",
  "source": "human",
  "parent_laws": [],
  "birth_step": 0,
  "last_mutation_step": null,
  "activation_reason": "colony_loop_detected",
  "last_utility": 0.114,
  "utility_history": [0.02, 0.07, 0.114],
  "synergy_partners": ["cell_occupancy"],
  "failure_cases": ["open_field_no_walls"],
  "quarantine_count": 0,
  "state": "active"
}
```

### Demo Mechanics

Every $N$ steps (e.g., $N=50$):

1. Run the full active law stack, compute $PR_{strict}$.
2. For each active law $l$: disable $l$, recompute $PR_{strict}$, compute $U(l)$.
3. For each pair of active laws $(l_i, l_j)$: test pairwise, compute $Syn(l_i, l_j)$.
4. Update each law's metadata (utility history, synergy partners, failure cases).
5. Decision logic:
   - If $U(l) > threshold_{active}$ and $state \neq active$: → **activate**
   - If $U(l) > 0$ but $C_{exec}$ is high: → **lease** (run only when needed)
   - If $U(l) \leq 0$ for $K$ consecutive evaluations: → **quarantine**
   - If quarantined for $M$ steps without appeal: → **archive** (fossilize)
   - If $U(l)$ is moderate and synergistic partners exist: → **protect** (keep active even if individually weak)

### Expected Result

- `playable_reality` in the law stack is replaced by `metric_head` — the metric system itself becomes a law that can be ablated and measured.
- Unused laws naturally drift to `dormant_pool` through quarantine → archive pipeline.
- Synergistic law pairs (e.g., `wall_following_agent` + `cell_occupancy`) remain protected even when individual utility is modest.
- Dead-law waste decreases measurably over time as the ecology prunes itself.

### Build Files

- `core/law_ecology.py` — Law states, utility computation, synergy scanning, quarantine pipeline
- `demos/demo_03_law_ecology.py` — Full law stack evaluation loop
- `data/law_provenance/*.json` — Per-law metadata files
- `data/telemetry/law_ecology_run.csv` — Utility and synergy telemetry

---

### Integrated Enhancements 17–24

**17. Law Category Separation**

Laws are categorized into six types, each with different evaluation criteria and management rules:

- **physics_laws** — govern physical simulation (e.g., gravity, pressure dynamics). Evaluated on simulation fidelity.
- **agent_laws** — govern agent behavior (e.g., wall following, BFS exploration). Evaluated on goal agency contribution.
- **metric_heads** — govern measurement and scoring (e.g., PR_strict computation). Evaluated on discriminative power.
- **report_heads** — govern output formatting and logging. Evaluated on information content.
- **semantic_controllers** — govern META-K repair logic (Frame 5). Evaluated on $V_{sem}$.
- **novelty_laws** — govern alien novelty generation (Frame 6). Evaluated on $A_{alien}$ and $R_{strange}$.

**18. Law Pedigree Tracking**

Every law carries a full provenance record:

- `parent_laws` — which laws this law was derived from (via mutation, composition, or inspiration)
- `child_laws` — which laws were derived from this law
- `birth_step` — the simulation step at which this law was first created
- `mutation_step` — the most recent step at which this law was mutated
- `source` — origin: `human`, `mutation`, `composition`, `forge`, `cross_mode_port`
- `mode_origin` — which mode this law was born in or designed for

This enables full lineage tracing: any law can be traced back to its human-designed ancestors and all mutations that produced it.

**19. Epistasis Graph**

Construct a graph where:

- **Nodes** = active laws
- **Edges** = $Syn(l_i, l_j) > threshold_{syn}$

Analyze graph centrality to identify **keystone laws** — laws with high betweenness or degree centrality that connect otherwise separate law clusters. Keystone laws are given extra protection from quarantine, as removing them could collapse multiple synergistic groups simultaneously.

```python
def compute_keystone_laws(law_graph, centrality_measure="betweenness", top_k=5):
    centrality = nx.betweenness_centrality(law_graph)
    return sorted(centrality, key=centrality.get, reverse=True)[:top_k]
```

**20. Law Mutation Sandbox**

Mutated laws are never deployed directly. Instead, they run in a **forked micro-world sandbox**:

- Fork the current simulation state.
- Run the mutated law for a short validation horizon.
- Reject the mutation if **any** of the following occur:
  - Catastrophic failure (unrecoverable state)
  - Syntax or runtime error in the law code
  - Unbounded growth (state size, memory, or runtime exceeds limits)
  - PR_strict collapse (drops below acceptable threshold)
  - Risk spike (recovery risk exceeds emergency threshold)

Only mutations that pass all checks graduate from `embryo` to `active`.

**21. Dormant Law Cryo-Storage**

Quarantined laws that are not archived are moved to **dormant cryo-storage** — a compressed, zero-import pool. Dormant laws:

- Consume no runtime or memory
- Can be resurrected if a relevant failure pattern is detected
- Maintain their full provenance and metadata
- Have a revival condition: "resurrect if mode $m$ enters failure class $f$ and this law historically contributed $U(l) > \theta_{revive}$ to that mode"

**22. Law Contribution Decay**

Utility is computed as an exponential moving average, not a raw snapshot:

$$U_t(l) = \alpha \cdot U_{t-1}(l) + (1 - \alpha) \cdot U_{current}(l)$$

Where $\alpha \in [0.8, 0.95]$. This prevents a single good or bad evaluation from drastically changing a law's status. Laws must consistently contribute (or fail to contribute) before their state changes.

**23. Law Safety Sandbox**

All laws are subject to safety bounds checking before and during execution:

- **Velocity bounds** — law cannot set velocities above maximum safe speed
- **Pressure bounds** — law cannot set pressures above critical threshold
- **Memory bounds** — law's memory footprint must stay within allocated limit
- **Runtime bounds** — law's per-step execution time must stay within budget
- **No infinite loops** — laws are instrumented with step counters and timeout guards
- **No unsafe imports** — laws are restricted to a whitelist of safe modules

Violation of any safety bound triggers immediate quarantine.

**24. Law Fossil Record**

Archived laws become **fossils** — permanent records preserved for historical analysis and potential future revival:

```json
{
  "law_name": "random_walk_explorer",
  "category": "agent_law",
  "state": "fossilized",
  "final_utility": -0.003,
  "reason_removed": "consistently_negative_utility_over_500_steps",
  "failure_contexts": ["colony.open_field_drift", "colony.edge_oscillation"],
  "parent_lineage": ["random_walk_base"],
  "revival_condition": "never — superseded by BFS-based explorers"
}
```

Fossils are never automatically resurrected but can be manually inspected for insights or revived in special sandbox experiments.

---

## Frame 4 — Mode Grammar + Recoverable Failure Demo

**Demo file:** `demo_04_mode_grammar.py`

**Core purpose:** Give every micro-world its own **success/failure grammar** — a structured vocabulary of terminal states, subterminal states, root causes, recovery paths, and risk penalties. v4's "Failure: active" was far too vague to enable meaningful recovery analysis. v5 needs the system to know *what kind* of failure occurred, *how deep* it went, *whether* it was recoverable, *what path* recovery took, and *what it cost*.

### Mode Grammars

#### Lander

**Terminal states:**
- `landed` — successfully touched down on the pad
- `hard_landed` — touched down but with excessive velocity (damaged)
- `crashed` — collided with ground or obstacle
- `missed_pad` — landed but not on the target pad
- `fuel_starved` — ran out of fuel before landing
- `hover_loop` — oscillating at altitude without descending
- `bounced` — touched pad but bounced off
- `recovering` — in the process of recovering from a failure state

**Useful actions:**
- Reduces vertical speed error
- Moves toward pad
- Preserves fuel
- Does not enter crash trajectory

#### Pressure

**Terminal states:**
- `stabilized` — pressure held within safe bounds
- `slowed_growth` — pressure growing but below runaway threshold
- `runaway` — pressure exceeding safe bounds, growing rapidly
- `critical_breach` — pressure exceeded critical threshold
- `vented` — safety vent activated, pressure released
- `contained` — pressure returned to safe bounds after venting

**Useful actions:**
- Reduces $dP/dt$ (rate of pressure change)
- Reduces critical zones (regions above safe threshold)
- Prevents runaway (keeps growth rate bounded)

#### Colony

**Terminal states:**
- `expanded` — successfully visited new region or cell
- `looped` — agent is cycling through a small set of cells
- `trapped` — agent is stuck in a single cell or dead end
- `resource_depleted` — agent has exhausted available energy or resources
- `teleport_discovered` — agent found a teleport or passage to new area
- `new_region_entered` — agent crossed a boundary into a previously unvisited region

**Useful actions:**
- Visits new reachable cell
- Reduces loop probability (visits diverse states)
- Moves toward frontier (cells adjacent to unvisited cells)
- Preserves energy (avoids wasteful backtracking)

#### Freescape

**Terminal states:**
- `zone_transitioned` — successfully moved between zones
- `height_recovered` — regained lost altitude
- `collision_recovered` — escaped from collision state
- `marooned` — stuck in inaccessible location with no recovery path
- `hydraulic_success` — hydraulic system operated correctly
- `pressure_survived` — survived a pressure hazard event

**Useful actions:**
- Changes zone (spatial progress)
- Recovers height (altitude restoration)
- Escapes collision (obstacle avoidance recovery)
- Stabilizes local hazard (environmental control)

#### Semantic

**Terminal states:**
- `metric_convergence` — metrics have stabilized to consistent values
- `self_contradiction` — semantic controller issued conflicting diagnoses
- `observer_timeout` — semantic observation exceeded time budget without conclusion
- `repair_success` — a proposed repair measurably improved the target mode
- `repair_failure` — a proposed repair failed or worsened the target mode
- `controller_overreach` — semantic controller intervened without justification

### Core Equations

**Recoverability:**

$$R_{recover} = \frac{N_{fail \rightarrow stable}}{N_{fail\_states}}$$

The fraction of failure states from which the system successfully recovered to a stable (non-failure) state. High $R_{recover}$ means the system is resilient. Low $R_{recover}$ means failures tend to be permanent or cascading.

**Recovery Efficiency:**

$$E_{recover} = \frac{A_{goal,after}}{1 + t_{recovery}}$$

Measures how much goal agency was restored after recovery, normalized by the time it took. Fast, complete recoveries score high. Slow, partial recoveries score low.

**Risk-Adjusted Strict PR:**

$$PR_{risk} = PR_{strict} \cdot (1 - R_{risk})$$

Penalizes PR by the recovery risk — the probability that the current state could cascade into an unrecoverable failure. Even a high-PR world is penalized if it is operating near the edge of catastrophe.

### Telemetry Columns

```csv
terminal_state,subterminal_state,failure_cause,failure_depth,recoverable,
recovery_time,recovery_path_length,mode_objective_progress,R_recover,
E_recover,R_risk,P_cascade,RTQ
```

Where `RTQ` is the Recovery Time Quotient — a composite measure of recovery speed and completeness.

### Demo Mechanics

Inject controlled failures into each mode and test the full detect → repair → recover → explain pipeline:

| Mode        | Failure Injected                  | Expected Detection                     | Expected Recovery                         |
|-------------|-----------------------------------|----------------------------------------|-------------------------------------------|
| **Lander**  | Bad velocity (overspeed)          | Crash trajectory detected              | Thrust correction → `recovering` → `landed` |
| **Pressure**| Pressure spike                    | Runaway detected                       | Vent activation → `vented` → `contained`  |
| **Colony**  | Loop trap (4-cell cycle)          | Loop detected via stagnation           | BFS escape → `new_region_entered`         |
| **Freescape**| Collision pocket (local minimum) | Collision state detected               | Height recovery → `collision_recovered`   |
| **Semantic**| Bad repair (worsening PR)         | Repair failure detected                | Rollback → `metric_convergence`           |

### Expected Result

1. **Failure entered** — system detects `failure_state` via mode grammar.
2. **Harmful surprise detected** — drift and/or agency drop triggers token earning.
3. **Token spent** — system spends token on repair lease.
4. **Repair lease activated** — appropriate law leased from ecology (Frame 3).
5. **Recovery achieved** — system transitions to `recovering` then stable state.
6. **PR_strict improved** — post-recovery PR_strict exceeds pre-failure PR_strict.
7. **Recovery path logged** — full sequence of states between failure and recovery recorded.

### Build Files

- `core/mode_grammars.py` — Terminal/subterminal state definitions, useful actions per mode
- `core/failure_injector.py` — Controlled failure injection per mode
- `demos/demo_04_mode_grammar.py` — Full detect-repair-recover pipeline
- `data/telemetry/mode_grammar_run.csv` — Failure and recovery telemetry

---

### Integrated Enhancements 25–32

**25. Mode Grammar DSL**

Define mode grammars in YAML for readability and extensibility:

```yaml
mode: lander
terminal_states:
  - name: landed
    success: true
    description: "Successfully touched down on pad"
  - name: crashed
    success: false
    description: "Collided with ground or obstacle"
    recoverable_from: [recovering]
  - name: recovering
    success: false
    description: "In process of recovering from failure"
    recoverable_from: [landed, hard_landed]
useful_actions:
  - "reduces vertical speed error"
  - "moves toward pad"
  - "preserves fuel"
  - "does not enter crash trajectory"
```

New modes can be added by writing a new YAML file, no code changes required.

**26. Hierarchical Outcome Grammar**

Terminal states are further refined with hierarchical labels using dot notation:

- `lander.crash.overspeed` — crashed due to excessive speed
- `lander.crash.missed_pad` — crashed while trying to reach pad
- `pressure.runaway.source_rate` — runaway caused by high source rate
- `pressure.runaway.vent_failure` — runaway caused by vent malfunction
- `colony.loop.local_cycle` — looping within a local region
- `colony.loop.dead_end_revisit` — repeatedly visiting a dead end

This enables fine-grained failure analysis and targeted repair candidate matching.

**27. Failure Injection Scheduler**

Three scheduling modes for injecting failures during testing:

- **Fixed schedule** — failures injected at predetermined steps (e.g., every 100 steps)
- **Poisson schedule** — failures injected according to a Poisson process with rate $\lambda$ (e.g., $\lambda = 0.02$ per step)
- **Adversarial schedule** — failures injected when the system appears most stable (maximize surprise), testing robustness under worst-case conditions

```python
class FailureScheduler:
    def fixed(self, steps: List[int]) -> Iterator[int]:
        for step in steps:
            yield step

    def poisson(self, rate: float, max_steps: int) -> Iterator[int]:
        next_failure = np.random.exponential(1 / rate)
        for step in range(max_steps):
            if step >= next_failure:
                yield step
                next_failure = step + np.random.exponential(1 / rate)
```

**28. Recovery Path Tracing**

Log every state transition between `failure_detected` and `stable_recovered`:

```json
{
  "failure_id": "f_0047",
  "mode": "colony",
  "failure_state": "looped",
  "recovery_path": [
    {"step": 1247, "state": "looped", "action": "inject_bfs_agent"},
    {"step": 1251, "state": "looped", "action": "bfs_exploring"},
    {"step": 1258, "state": "recovering", "action": "bfs_found_new_cell"},
    {"step": 1262, "state": "new_region_entered", "action": "none"}
  ],
  "recovery_time": 15,
  "recovery_path_length": 4,
  "final_state": "new_region_entered"
}
```

This trace enables retrospective analysis of what worked and what didn't in each recovery.

**29. Subterminal State Clustering**

Apply k-means clustering to subterminal states to discover **emergent failure modes** — patterns of failure that were not explicitly defined in the mode grammar but recur frequently:

```python
from sklearn.cluster import KMeans

def discover_emergent_failures(state_vectors, n_clusters=5):
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(state_vectors)
    return labels, kmeans.cluster_centers_
```

Emergent failure modes are logged and can be promoted to official grammar entries if they persist across runs.

**30. Failure Cascade Probability**

$$P_{cascade} = 1 - \exp\left(-\lambda \cdot \frac{N_{failures}}{N_{steps}}\right)$$

Estimates the probability that a failure in one subsystem will cascade to other subsystems. High $P_{cascade}$ means the system is fragile — failures tend to spread. Low $P_{cascade}$ means failures are contained. This metric feeds into $R_{risk}$ and influences the risk-adjusted PR.

**31. Recovery Darwinism**

When a failure is detected, spawn **parallel recovery policies** in separate sandboxes. Each policy attempts a different recovery strategy. The fastest successful recovery becomes the default for that failure class:

```python
def recovery_darwinism(failure_state, candidates, timeout=50):
    results = []
    for policy in candidates:
        sandbox = fork_micro_world()
        result = sandbox.run_recovery(policy, max_steps=timeout)
        results.append((policy, result))
    # Select fastest successful recovery
    successful = [(p, r) for p, r in results if r.recovered]
    if successful:
        best = min(successful, key=lambda x: x[1].recovery_time)
        return best
    return None  # All recovery attempts failed
```

**32. Failure Memory Bank**

Successful recoveries are stored as reusable **macros** — compact mappings from failure signatures to repair actions:

```json
{
  "failure_signature": "colony.loop.local_cycle.4cell",
  "repair_macro": "anti_loop_bfs_agent",
  "success_rate": 0.87,
  "avg_recovery_time": 12.3,
  "times_used": 47,
  "last_used_step": 3891
}
```

When a failure signature is detected, the memory bank is consulted first before running a full repair auction. If a high-success-rate macro exists, it is used directly, saving time and tokens.

---

## Frame 5 — Semantic META-K Controller Demo

**Demo file:** `demo_05_meta_k_controller.py`

**Core purpose:** Promote the semantic mode from a passive observer to a **causal director**. The META-K controller observes other modes, diagnoses failures, proposes repairs, spends tokens, activates law leases, measures the effect of each intervention, and decides whether to keep, quarantine, or mutate the deployed repair. The semantic controller scores itself not on its own PR (which may stay low) but on its **causal impact** on other modes.

### Core Equation

**Semantic Value:**

$$V_{sem} = \frac{\Delta PR_{strict,cross}}{\lambda \cdot C_{analysis} + \mu \cdot T_{wasted}}$$

The semantic controller's value is the improvement in other modes' PR_strict, divided by the cost of analysis and wasted tokens. A positive $V_{sem}$ means the controller is producing net benefit. A negative $V_{sem}$ means the controller's interventions are costing more than they are worth. The controller's goal is to maximize $V_{sem}$ over time.

### META-K Control Loop (13 Steps)

1. **Read telemetry** — ingest current state of all modes: PR heads, agency scores, token balances, active laws, failure states.
2. **Detect failure class** — identify which mode(s) are in failure state, using mode grammar (Frame 4).
3. **Identify mode grammar** — retrieve the specific grammar for the failing mode to understand valid terminal/subterminal states and recovery paths.
4. **Inspect law ecology** — query the law ecology (Frame 3) for current law states, utilities, synergies, and available dormant/embryo laws.
5. **Inspect token balance** — check available tokens across all token types to determine budget for repair operations.
6. **Choose repair candidate** — select one or more potential repairs from available laws, mutations, or cross-mode ports.
7. **Run repair auction** — execute second-price auction (enhancement 12) among repair candidates.
8. **Spend/stake tokens** — pay the auction price, stake collateral for the law lease.
9. **Lease law** — activate the winning law in the target mode for a fixed lease period.
10. **Run validation window** — observe the target mode for the lease duration, collecting PR_strict and other metrics.
11. **Compare counterfactual** — compare actual performance with predicted performance and with the no-repair counterfactual.
12. **Keep/quarantine/mutate** — decide the fate of the leased law: keep active, quarantine for investigation, or mutate for improvement.
13. **Export repair event** — log the full repair event to telemetry with all metadata for retrospective analysis.

### Repair Candidate Example

```json
{
  "mode": "colony",
  "failure": "colony.loop.local_cycle",
  "repair_candidates": ["anti_loop_bfs_agent", "unvisited_neighbor_bias", "random_escape_mutation"],
  "chosen": "anti_loop_bfs_agent",
  "lease_steps": 40,
  "expected_delta_pr": 0.12,
  "semantic_confidence": 0.78
}
```

### Telemetry Columns

```csv
semantic_diagnosis,semantic_confidence,repair_candidate_count,chosen_repair,
expected_delta_pr,actual_delta_pr,counterfactual_delta,lease_result,
semantic_value,meta_k_energy,semantic_version,repair_provenance_id
```

### Expected Result

- The semantic controller's own base PR may stay low (it is not a goal-directed agent in the traditional sense).
- But $V_{sem} > 0$ because its interventions measurably improve other modes' $PR_{strict}$.
- Token economy is active: tokens earned from failures are spent on repair leases.
- Repair provenance is fully traceable: each repair can be traced back to the failure, the auction, the law lease, and the outcome.

### Build Files

- `core/semantic_controller.py` — META-K control loop, diagnosis engine, repair selection
- `core/repair_planner.py` — Repair candidate generation and evaluation
- `core/repair_auction.py` — Second-price auction implementation
- `demos/demo_05_meta_k_controller.py` — Full META-K controller demo
- `data/telemetry/meta_k_controller_run.csv` — Repair event telemetry

---

### Integrated Enhancements 33–40

**33. META-K Policy Library**

The controller has access to a library of 10 intervention policies:

1. **prune** — deactivate a low-utility law
2. **mutate** — modify an existing law's parameters or logic
3. **lease** — temporarily activate a dormant or embryo law
4. **swap** — replace one active law with another
5. **inject_noise** — add controlled randomness to break stagnation
6. **extend_budget** — grant extra tokens to a struggling mode
7. **quarantine** — move a suspected-harmful law to quarantine
8. **revive_dormant** — resurrect a dormant law for testing
9. **port_cross_mode_law** — adapt a law from one mode for use in another
10. **escalate** — flag an unrecoverable situation for human review

The controller selects from this library based on the failure class and available resources.

**34. Repair Impact Prediction**

Train a small regressor to predict the expected $\Delta PR_{strict}$ for a repair candidate before committing tokens:

$$\hat{\Delta PR}_{strict} = f(\text{law\_features}, \text{failure\_features}, \text{mode\_features})$$

Features include: law utility history, law category, failure type, mode PR baseline, current token balance, similar past repairs' outcomes. The regressor is updated online with actual repair results from the replay buffer.

**35. Counterfactual Replay**

After a repair is deployed, compute the **causal impact** by comparing with a counterfactual where the repair was not deployed:

$$\Delta PR_{causal} = PR_{with\_repair} - PR_{without\_repair}$$

The counterfactual is estimated by running a shadow simulation (fork of the pre-repair state) without the repair for the same validation window. This separates the repair's effect from confounding factors (e.g., natural recovery, mode drift).

**36. Semantic Cross-Mode Attention**

Build a relevance matrix that maps failures in mode $i$ to potential repairs originating from mode $j$:

$$M_{ij} = \text{similarity}(\text{failure}_i, \text{repair\_history}_j)$$

When a failure occurs in one mode, the controller checks whether a repair that worked in a different mode might be applicable. This enables cross-pollination of repair strategies across the entire mode ecosystem.

**37. Multi-Objective Repair Ranking**

Rank repair candidates on a **Pareto front** over five objectives:

1. $\Delta PR_{strict}$ — goal-directed improvement
2. $token\_cost$ — economic efficiency
3. $risk\_delta$ — change in recovery risk (prefer risk reduction)
4. $novelty\_delta$ — change in novelty (prefer novelty increase)
5. $runtime\_cost$ — computational overhead (prefer low cost)

No single repair dominates all objectives; the controller selects from the Pareto front based on current priorities (e.g., prioritize risk reduction when $R_{risk}$ is high, prioritize novelty when $PR_{strict}$ is already high).

**38. Repair Sandbox**

Before committing a repair, simulate it in a **short-horizon sandbox**:

- Fork the current simulation state.
- Deploy the repair candidate.
- Run for $H$ steps (e.g., $H=20$).
- Reject the repair if **any** of:
  - $R_{risk}$ rises above threshold
  - $PR_{strict}$ drops below baseline
  - $token\_cost$ exceeds available balance
  - $P_{stag}$ increases (repair worsens stagnation)
  - Catastrophic failure occurs

Only sandbox-passed repairs are committed to the live simulation.

**39. Semantic Value Ledger**

Maintain a rolling record of $V_{sem}$ for the last 10 repairs, segmented by:

- Mode — which mode was repaired
- Repair type — which policy was used (prune, mutate, lease, swap, etc.)
- Controller version — which version of the META-K controller produced the repair

This enables the controller to learn which strategies work best for which failure classes, and to track its own improvement over time.

```python
class SemanticValueLedger:
    def __init__(self, window_size=10):
        self.recent_repairs = deque(maxlen=window_size)

    def record(self, repair_event):
        self.recent_repairs.append(repair_event)

    def rolling_v_sem(self, group_by=None):
        repairs = list(self.recent_repairs)
        if group_by:
            repairs = [r for r in repairs if r[group_by] == group_by]
        return mean([r["semantic_value"] for r in repairs]) if repairs else 0.0
```

**40. Self-Awareness Dashboard**

A real-time dashboard showing the semantic controller's current state:

- Current diagnosis (which mode is failing, what failure class)
- Repair queue (pending, in-progress, completed repairs)
- Token balances by type
- Expected vs actual $\Delta PR_{strict}$ for recent repairs
- Active law leases and their remaining durations
- Semantic confidence score
- Controller version and deployment date
- Rolling $V_{sem}$ by mode and by repair type

This dashboard makes the META-K controller's reasoning transparent and auditable.

---

## Frame 6 — Alien Novelty Forge Demo

**Demo file:** `demo_06_alien_novelty_forge.py`

**Core purpose:** Move beyond human playability into **recoverable alienness**. Can the system invent strange but stable behavior? Can it produce laws that no human designed? Can novelty survive across multiple seeds? Can alien dynamics remain recoverable (i.e., the system can recover from the strange situations the alien laws create)? This is the ultimate test of RGPUF v5 — not just measuring and repairing known physics, but inventing *new* physics that is simultaneously strange, stable, and recoverable.

### Core Novelty Equations

**Novelty-Weighted PR:**

$$PR_{novel} = PR_{strict} \cdot (1 + \alpha \cdot N_{causal} + \beta \cdot A_{alien} + \chi \cdot N_{robust})$$

Rewards worlds that maintain goal-directed play while exhibiting causal novelty, alienness, and cross-seed robustness. The base $PR_{strict}$ ensures the world remains playable; the novelty terms reward strangeness.

**Alienness Index:**

$$A_{alien} = 1 - \cos(H^*_{current}, H^*_{human\_prior})$$

Measures the angular distance between the current law stack's behavior signature and the human-designed prior. $A_{alien} = 0$ means the system behaves exactly as a human would expect. $A_{alien} \rightarrow 1$ means the system's behavior is maximally alien (orthogonal to human expectations). The behavior signature $H^*$ captures the statistical fingerprint of the law stack's dynamics.

**Causal Novelty:**

$$N_{causal} = \|G_t - G_{t-1}\|_F$$

The Frobenius norm of the difference between the current causal graph $G_t$ and the previous causal graph $G_{t-1}$. Measures how much the causal structure of the world has changed due to new or mutated laws. Large $N_{causal}$ means the system has introduced genuinely new cause-effect relationships.

**Recoverable Strangeness:**

$$R_{strange} = A_{alien} \cdot R_{recover} \cdot (1 - L_{samsara})$$

Combines alienness with recoverability and penalizes samsara (cyclic repetition). High $R_{strange}$ means the system is simultaneously strange, recoverable, and non-repetitive — the ideal target for the forge.

**Cross-Seed Robust Novelty:**

$$N_{robust} = \mu(N_{rate}) - k \cdot \sigma(N_{rate})$$

The novelty rate (novel states discovered per step) must be high on average ($\mu$) and consistent across seeds (low $\sigma$). Novelty that appears in one seed but not others is not robust and is penalized.

**Anti-Samsara Penalty:**

$$L_{samsara} = \frac{1}{T} \sum_t \mathbb{I}[\sigma_t \in \Sigma_{past\_cycle}]$$

Penalizes the system for revisiting states it has already visited in a previous cycle. The forge must not simply oscillate between a set of known states — it must generate *genuinely new* states.

### Alien Playground Mode

A dedicated mode with **no normal human goal**. Instead, the optimization target is:

$$\max \; R_{strange} = A_{alien} \cdot R_{recover} \cdot (1 - L_{samsara})$$

The system is free to explore any dynamics, as long as they are alien, recoverable, and non-cyclic. This mode serves as the incubator for alien law birth.

### Possible Alien Laws (12 Candidates)

1. **zone_time_dilation** — time passes at different rates in different spatial zones, causing agents to experience temporal asymmetry
2. **local_gravity_inversion** — gravity direction inverts in certain regions, creating spatial paradoxes
3. **pressure_memory_field** — pressure at a point depends on the history of pressure at neighboring points, creating temporal-spatial coupling
4. **graph_laplacian_sensor** — agent senses not raw state but the graph Laplacian of the state network, detecting topological features
5. **topological_echo_agent** — agent's actions are influenced by the topology of previously visited state space, creating path-dependent behavior
6. **symmetry_breaker_zone** — certain zones spontaneously break symmetries in the physics, causing irreversible state changes
7. **causal_rewire_pulse** — periodic pulses that temporarily rewire cause-effect relationships between variables
8. **phase_shift_collision** — collisions cause phase shifts in the simulation clock, creating desynchronization effects
9. **law_inversion** — one law's effect is inverted when a trigger condition is met, creating toggle dynamics
10. **universal_quantizer** — continuous state variables are periodically quantized, creating discrete jumps in dynamics
11. **blind_spot_explorer** — agent is attracted to regions where its prediction model has highest uncertainty
12. **entropy_targeting_controller** — controller actively drives the system toward high-entropy states, seeking disorder

### Law Birth API

```python
def birth_law(
    name: str,
    parent_laws: List[str],
    mode: str,
    trigger_condition: Callable,
    update_function: Callable,
    cost_estimate: float,
    safety_bounds: Dict[str, Tuple[float, float]]
) -> Law:
    """
    Create a new law from the forge.

    Parameters:
        name: Unique identifier for the new law
        parent_laws: List of laws that inspired or were composed to create this law
        mode: The mode where this law was born or is intended for
        trigger_condition: Function that returns True when the law should activate
        update_function: Function that computes the law's effect on state
        cost_estimate: Estimated computational cost per step
        safety_bounds: Dictionary mapping variable names to (min, max) safe ranges

    Returns:
        Law object in 'embryo' state, ready for sandbox validation
    """
    law = Law(
        name=name,
        parent_laws=parent_laws,
        mode_origin=mode,
        state="embryo",
        source="forge",
        ...
    )
    return law
```

### Law Birth Cost

$$C_{birth}(l_{new}) = \frac{c_{base} + \eta \cdot complexity(l_{new})}{\gamma \cdot A_{alien}(l_{new})}$$

More complex laws cost more to birth. But highly alien laws (large $A_{alien}$) receive a cost discount — the forge actively subsidizes strangeness. This creates an economic incentive for the system to generate alien rather than conventional laws.

### Cross-Seed Export Gate

For an alien law to graduate from the forge and enter the general law ecology, it must pass **all five gates**:

1. $PR_{strict} > PR_{minimum\_safety}$ — the law does not destroy playability
2. $R_{strange} > R_{novelty\_threshold}$ — the law produces genuine recoverable strangeness
3. $N_{robust} > N_{cross\_seed\_threshold}$ — the law's novelty is consistent across seeds
4. catastrophic failure rate $< max\_failure\_rate$ — the law does not cause unacceptable failures
5. $\text{std}(PR_{strict}) < tolerance$ — the law's effect is stable, not erratic

Only laws passing all five gates are exported. The rest remain in the forge for further mutation.

### Expected Export Example

**Alien Recipe 003: Causal Echo Field**

```json
{
  "recipe_id": "alien_003",
  "name": "causal_echo_field",
  "parent_laws": ["pressure_memory_field", "graph_laplacian_sensor"],
  "born_step": 1247,
  "mode_origin": "alien_playground",
  "effect": "State transitions in one zone create delayed echoes in neighboring zones, producing emergent wave-like dynamics",
  "pr_strict": 0.34,
  "pr_novel": 0.71,
  "A_alien": 0.82,
  "R_strange": 0.63,
  "N_robust": 0.58,
  "cross_seed_stats": {
    "seeds_tested": 10,
    "mean_pr_novel": 0.68,
    "std_pr_novel": 0.09,
    "mean_pr_strict": 0.31,
    "std_pr_strict": 0.04,
    "failure_rate": 0.02
  },
  "failure_cases": ["zone_boundary_interference", "echo_amplification_overflow"],
  "export_status": "PASSED"
}
```

### Build Files

- `core/novelty_metrics.py` — All novelty equations, alienness computation, samsara detection
- `core/law_forge.py` — Law birth API, mutation operators, sandbox validation, export gate
- `demos/demo_06_alien_novelty_forge.py` — Full forge demo with cross-seed validation
- `data/born_laws/*.json` — Laws born from the forge
- `data/recipes/alien_recipe_*.json` — Exported alien recipe cards

---

### Integrated Enhancements 41–48

**41. Novelty Archive with Fitness**

Every law produced by the forge is archived with a full fitness profile:

```json
{
  "law_name": "causal_echo_field",
  "fitness": {
    "PR_strict": 0.34,
    "PR_novel": 0.71,
    "A_alien": 0.82,
    "R_strange": 0.63,
    "N_robust": 0.58
  },
  "cross_seed_stats": { ... },
  "parentage": ["pressure_memory_field", "graph_laplacian_sensor"],
  "failure_cases": ["zone_boundary_interference"]
}
```

The archive enables retrospective analysis of which forge strategies produce the best laws and supports future novelty search.

**42. Law Mutation Operators**

Eight mutation operators, each with distinct cost, risk, expected alienness, and validation horizon:

| Operator            | Cost   | Risk    | Expected Alienness | Validation Horizon |
|---------------------|--------|---------|--------------------|--------------------|
| `reparameterize`    | Low    | Low     | Low                | Short              |
| `swap_term`         | Medium | Medium  | Medium             | Medium             |
| `add_noise`         | Low    | Low     | Low-Medium         | Short              |
| `compose`           | High   | Medium  | High               | Long               |
| `abstract`          | Medium | Low     | Medium             | Medium             |
| `invert`            | Medium | High    | High               | Medium             |
| `rewire_trigger`    | High   | High    | High               | Long               |
| `change_sensor`     | Medium | Medium  | Medium-High        | Medium             |

The forge selects mutation operators based on the current target: low-risk refinement uses `reparameterize` and `add_noise`; high-alienness exploration uses `compose`, `invert`, and `rewire_trigger`.

**43. Multi-Objective Novelty Search**

The forge optimizes over **six objectives** simultaneously:

1. $PR_{strict}$ — maintain playability
2. $A_{alien}$ — maximize alienness
3. $N_{robust}$ — ensure cross-seed consistency
4. $R_{strange}$ — maximize recoverable strangeness
5. $C_{exec}$ — minimize computational cost
6. $risk$ — minimize failure risk

Novelty search proceeds via Pareto-based selection: laws that are not dominated on any objective by any other law are preserved on the Pareto front. The forge samples new candidates from the Pareto front and mutates them.

**44. Causal Novelty Graph Diff**

Visualize the change in causal structure as the forge introduces new laws:

$$\Delta G = G_t - G_{t-1}$$

Rendered as an **animated graph** where:
- Added edges (new causal relationships) are highlighted in green
- Removed edges (broken causal relationships) are highlighted in red
- Changed edge weights (modified causal strengths) are highlighted in yellow

This provides an intuitive visualization of how the forge is reshaping the causal landscape of the micro-world.

**45. Anti-Samsara Cycle Detector**

Detect cyclic repetition at four temporal scales:

- **Short scale** — cycles within the last 20 steps (immediate looping)
- **Medium scale** — cycles within the last 200 steps (medium-term repetition)
- **Long scale** — cycles within the last 2000 steps (long-term return to old states)
- **Historical scale** — cycles compared to the entire run history (global repetition)

When samsara is detected at any scale, the forge **forces mutation or novelty injection** — either mutate an existing law, inject a new random law, or activate a dormant alien law from the archive.

```python
def detect_samsara(state_history, scales=[20, 200, 2000, None]):
    detections = {}
    for scale in scales:
        window = state_history[-scale:] if scale else state_history
        cycle_length = find_shortest_cycle(window)
        if cycle_length is not None:
            detections[scale] = cycle_length
    return detections
```

**46. Cross-Seed Novelty Tournament**

To determine whether a law's novelty is robust, run a **tournament** across 10–20 seeds:

1. Deploy the candidate law in each seed.
2. Run for a fixed evaluation horizon.
3. Collect $PR_{novel}$ and $PR_{strict}$ per seed.
4. Compute $\mu$ and $\sigma$ of both metrics.
5. Compute failure rate across seeds.
6. **Graduation criteria:** mean $PR_{novel} > threshold$, std $PR_{novel} < tolerance$, mean $PR_{strict} > safety\_floor$, failure rate $< max\_rate$.

Only laws that pass the tournament graduate to the general law ecology.

**47. Human Incomprehensibility Score**

To measure how alien a law truly is, use an LLM to attempt to **explain the law in simple terms**:

```
Prompt: "Explain this law in one simple sentence a child could understand:
{law_code}"
```

- If the LLM produces a clear, simple explanation: low alien value (the law is comprehensible).
- If the LLM struggles, produces vague explanations, or fails: high alien value (the law is genuinely difficult to understand).

$$L_{incomprehensible} = 1 - \text{explainability\_score}$$

High $L_{incomprehensible}$ combined with high utility ($U(l) > 0$) signals high alien value. However, all alien laws are still guarded by $PR_{strict}$ and $R_{recover}$ — strangeness without playability or recoverability is rejected.

**48. Exportable Alien Recipe Cards**

When a law graduates from the forge, generate a **markdown recipe card** documenting everything:

```markdown
# Alien Recipe 003: Causal Echo Field

## Parent Laws
- pressure_memory_field
- graph_laplacian_sensor

## Born
- Step: 1247
- Mode: alien_playground

## Effect
State transitions in one zone create delayed echoes in neighboring zones,
producing emergent wave-like dynamics that no human-designed law produces.

## Code Summary
Computes graph Laplacian of zone connectivity, applies temporal convolution
with learnable delay parameter, modulates transition probabilities.

## Metrics
- PR_strict: 0.34
- PR_novel: 0.71
- A_alien: 0.82
- R_strange: 0.63
- N_robust: 0.58

## Cross-Seed Stats
- Seeds tested: 10
- Mean PR_novel: 0.68 (std: 0.09)
- Mean PR_strict: 0.31 (std: 0.04)
- Failure rate: 2%

## Failure Cases
- zone_boundary_interference
- echo_amplification_overflow

## Trace
[Link to video/trace of law in action]
```

Recipe cards are the final output of the forge — portable, documented, reproducible records of alien novelty.

---

## Final Cross-Demo Evaluator

**Master script:** `run_v5_forge_suite.py`

Runs all six demos in sequence, collects all telemetry, and generates a comprehensive `Novelty_Forge_Health_Report.md`.

### Health Report Checks

The health report evaluates **nine critical checks**:

1. **PR_strict nonzero where goals achievable** — Verify that $PR_{strict} > 0$ in modes where goals are achievable (lander, colony). If $PR_{strict} = 0$ everywhere, the goal agency system is broken.
2. **D_A does not stay high forever** — Verify that agency divergence decreases over time in modes with recovery mechanisms. If $D_A$ stays high indefinitely, recovery is failing.
3. **token_inflation_rate bounded** — Verify that $I_T$ remains within acceptable bounds (e.g., $[-0.1, 0.1]$ tokens per step). Unbounded inflation means the token economy is broken.
4. **token_spend_ratio healthy** — Verify that $R_{spend}$ is in a productive range (e.g., $[0.3, 0.8]$). Too low means tokens are hoarded; too high means the system is overspending.
5. **dead-law waste decreases** — Verify that the fraction of laws in `quarantined` or `archived` state decreases (or stabilizes at a low level) over time. Growing dead-law waste means the ecology is not pruning effectively.
6. **R_recover improves after repair** — Verify that the recoverability metric increases after repair events. If repairs do not improve recoverability, the repair system is failing.
7. **V_sem positive over rolling window** — Verify that the semantic controller's value is positive over the last 10 repairs. If $V_{sem} < 0$, the controller is doing more harm than good.
8. **N_robust passes cross-seed gate** — Verify that novelty produced by the forge is consistent across seeds. If $N_{robust}$ is low, the forge is producing seed-specific noise, not genuine novelty.
9. **alien laws do not cause catastrophic failure** — Verify that exported alien laws have a catastrophic failure rate below the maximum threshold. If alien laws cause frequent catastrophes, the export gate is too permissive.

### Health Report Output

For each check, the report assigns one of three statuses:

- **PASS** — check criteria met, no action needed
- **WARN** — check criteria borderline, monitor and investigate
- **FAIL** — check criteria not met, immediate attention required

Additionally, the report includes:

- **Recommended patches** — specific code or parameter changes to address failures
- **Suspicious laws** — laws with unexpected behavior patterns (e.g., high utility but also high risk)
- **High-risk modes** — modes with elevated failure rates or low recoverability
- **Best recipes** — top-performing alien recipes by $PR_{novel}$, $A_{alien}$, and $R_{strange}$
- **Best alien laws** — laws with highest combined novelty and robustness scores
- **Token economy status** — summary of inflation, spend ratio, and commons pool health
- **Semantic controller ROI** — rolling $V_{sem}$, repair success rate, token efficiency

> This closes the loop: the demo suite audits itself.

---

## Final Vision

The six frames merged with 48 enhancements create a ladder from truth to strangeness:

```
Frame 1: The system tells truth from activity.
Frame 2: The system metabolizes harmful surprise.
Frame 3: The system tests, mutates, and prunes laws.
Frame 4: The system understands failure and recovery.
Frame 5: The system directs repairs through META-K.
Frame 6: The system invents recoverable alien novelty.
```

> **RGPUF v5 — Sovereign Novelty Forge**
> A self-auditing retro-physics engine where playable reality is not merely simulated, but tested, repaired, evolved, and made strange.
