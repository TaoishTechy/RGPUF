# Frame 6 — Alien Novelty Forge Demo
## `demo_06_alien_novelty_forge.py`

---

## 1. Core Purpose

Move beyond human playability into **recoverable alienness**. The prior frames have established a system that can detect failures, recover from them, and direct repairs across modes. But all of this operates within the bounds of human-designed laws and human-understandable objectives. Frame 6 asks the radical question:

> **Can the system invent strange but stable behavior? Can it produce laws that no human manually designed? Can novelty survive across seeds? Can alien dynamics remain recoverable?**

This frame introduces the **Alien Novelty Forge** — a subsystem that:

1. **Generates** novel laws through mutation, composition, and invention.
2. **Measures** alienness — how different is the new behavior from what a human would design?
3. **Ensures recoverability** — alien behavior must not be chaotic or uncontrollable.
4. **Tests robustness** — novelty must survive across multiple random seeds.
5. **Exports** discoveries as **alien recipe cards** that can be shared, studied, and reused.

The Forge does not optimize for weirdness alone. It optimizes for **recoverable causal novelty** — behavior that is genuinely new, causally structured, and survivable.

---

## 2. Core Novelty Equations

### 2.1 Novelty-Weighted Performance Ratio

$$PR_{\text{novel}} = PR_{\text{strict}} \cdot \left(1 + \alpha \cdot N_{\text{causal}} + \beta \cdot A_{\text{alien}} + \chi \cdot N_{\text{robust}}\right)$$

Where:
- $PR_{\text{strict}}$ is the base strict performance ratio (must remain above safety threshold).
- $N_{\text{causal}}$ is the causal novelty (Section 2.3) — how much the causal graph has changed.
- $A_{\text{alien}}$ is the alienness index (Section 2.2) — how far the behavior is from human prior.
- $N_{\text{robust}}$ is the cross-seed robust novelty (Section 2.5) — novelty that persists across seeds.
- $\alpha, \beta, \chi$ are weighting hyperparameters that control the trade-off between performance, novelty, and robustness.

**Bounds:**
- $PR_{\text{novel}} \geq 0$ (since $PR_{\text{strict}} \geq 0$ and $N_{\text{causal}}, A_{\text{alien}}, N_{\text{robust}} \geq 0$).
- $PR_{\text{novel}}$ can exceed $PR_{\text{strict}}$ significantly if alienness and causal novelty are high.
- If $PR_{\text{strict}} = 0$ (total failure), $PR_{\text{novel}} = 0$ regardless of alienness. **Performance is a hard prerequisite for novelty credit.**

### 2.2 Alienness Index

$$A_{\text{alien}} = 1 - \cos\left(\mathbf{H}^*_{\text{current}}, \mathbf{H}^*_{\text{human\_prior}}\right)$$

Where:
- $\mathbf{H}^*_{\text{current}}$ is the normalized histogram of behavior features in the current system state. This captures the distribution of states, actions, transitions, and causal patterns.
- $\mathbf{H}^*_{\text{human\_prior}}$ is the normalized histogram of behavior features that a human designer would typically produce. This is computed from a reference set of human-designed laws and their behavior patterns.
- $\cos(\cdot, \cdot)$ is the cosine similarity between the two histogram vectors.
- $A_{\text{alien}} \in [0, 1]$.
  - $A_{\text{alien}} = 0$ means behavior is identical to human prior (fully familiar).
  - $A_{\text{alien}} = 1$ means behavior is orthogonal to human prior (maximally alien).

**Histogram features** (the dimensions of $\mathbf{H}^*$):

| Feature | Description | Bins |
|---|---|---|
| `action_distribution` | Histogram of action types taken | 20 |
| `state_coverage` | Fraction of state space visited | 10 |
| `transition_entropy` | Entropy of state transition matrix | 10 |
| `causal_depth` | Mean depth of causal chains | 10 |
| `law_activation_frequency` | How often each law fires | 20 |
| `resource_utilization_pattern` | Shape of resource consumption curve | 10 |
| `spatial_pattern` | Spatial distribution of agent positions | 20 |

Total: 100-dimensional histogram vector.

**Computation:**

```python
def compute_alienness(
    current_behavior: dict,
    human_prior_behavior: dict,
    n_bins: dict = None
) -> float:
    """
    Computes A_alien = 1 - cos(H*_current, H*_human_prior).
    """
    if n_bins is None:
        n_bins = {
            "action_distribution": 20,
            "state_coverage": 10,
            "transition_entropy": 10,
            "causal_depth": 10,
            "law_activation_frequency": 20,
            "resource_utilization_pattern": 10,
            "spatial_pattern": 20
        }

    h_current = []
    h_human = []

    for feature_name, bins in n_bins.items():
        # Compute histogram for current behavior
        values_current = extract_feature(current_behavior, feature_name)
        hist_current, _ = np.histogram(values_current, bins=bins, density=True)
        h_current.extend(hist_current)

        # Compute histogram for human prior
        values_human = extract_feature(human_prior_behavior, feature_name)
        hist_human, _ = np.histogram(values_human, bins=bins, density=True)
        h_human.extend(hist_human)

    h_current = np.array(h_current, dtype=float)
    h_human = np.array(h_human, dtype=float)

    # Normalize
    h_current = h_current / (np.linalg.norm(h_current) + 1e-10)
    h_human = h_human / (np.linalg.norm(h_human) + 1e-10)

    # Cosine similarity
    cos_sim = np.dot(h_current, h_human)

    return 1.0 - cos_sim
```

### 2.3 Causal Novelty

$$N_{\text{causal}} = \|G_t - G_{t-1}\|_F$$

Where:
- $G_t$ is the causal graph adjacency matrix at time $t$. Nodes represent state variables, actions, and laws. Edges represent causal relationships (discovered through intervention analysis).
- $G_{t-1}$ is the causal graph at the previous measurement point (before the novel law was introduced).
- $\|\cdot\|_F$ is the Frobenius norm.

**Interpretation:**
- $N_{\text{causal}} = 0$ means the causal structure has not changed (the novel law didn't alter how things interact causally).
- $N_{\text{causal}} > 0$ means new causal pathways have appeared, old ones have disappeared, or edge weights have shifted.
- Large $N_{\text{causal}}$ indicates the novel law has significantly rewired the causal structure — this is genuinely new behavior, not just parameter tweaking.

**Edge weight computation:**

Each edge weight $w_{ij}$ in $G$ is computed as:

$$w_{ij} = \left|\frac{\partial x_j}{\partial x_i}\right|_{\text{empirical}}$$

Estimated by perturbing node $i$ and measuring the effect on node $j$ across multiple episodes.

```python
def compute_causal_graph(telemetry_history: List[dict]) -> np.ndarray:
    """
    Estimates causal graph adjacency matrix from telemetry.
    Uses simple finite-difference perturbation analysis.
    """
    variables = extract_variable_names(telemetry_history[0])
    n = len(variables)
    G = np.zeros((n, n))

    for i, var_i in enumerate(variables):
        for j, var_j in enumerate(variables):
            if i == j:
                G[i][j] = 0  # no self-loops
                continue
            # Estimate partial derivative empirically
            correlation = estimate_causal_effect(telemetry_history, var_i, var_j)
            G[i][j] = abs(correlation)

    # Normalize to [0, 1]
    G = G / (G.max() + 1e-10)
    return G

def compute_causal_novelty(G_before: np.ndarray, G_after: np.ndarray) -> float:
    """N_causal = ||G_after - G_before||_F"""
    return np.linalg.norm(G_after - G_before, ord='fro')
```

### 2.4 Recoverable Strangeness

$$R_{\text{strange}} = A_{\text{alien}} \cdot R_{\text{recover}} \cdot \left(1 - L_{\text{samsara}}\right)$$

Where:
- $A_{\text{alien}}$ is the alienness index (Section 2.2).
- $R_{\text{recover}}$ is the recoverability ratio from Frame 4 (Section 3.1).
- $L_{\text{samsara}}$ is the anti-samsara penalty (Section 2.6).

**Interpretation:**
- $R_{\text{strange}} \in [0, 1]$.
- $R_{\text{strange}}$ is high only when behavior is **both alien and recoverable and non-cyclic**.
- A law that is very alien ($A_{\text{alien}} \to 1$) but unrecoverable ($R_{\text{recover}} \to 0$) gets $R_{\text{strange}} \to 0$.
- A law that is recoverable but familiar ($A_{\text{alien}} \to 0$) gets $R_{\text{strange}} \to 0$.
- A law that is alien and recoverable but cyclic ($L_{\text{samsara}} \to 1$) gets $R_{\text{strange}} \to 0$.

This is the **core quality metric** of the Alien Novelty Forge. Only laws with high $R_{\text{strange}}$ are candidates for export.

### 2.5 Cross-Seed Robust Novelty

$$N_{\text{robust}} = \mu(N_{\text{rate}}) - k \cdot \sigma(N_{\text{rate}})$$

Where:
- $N_{\text{rate}}$ is a vector of novelty rates across $S$ seeds: $N_{\text{rate}} = [A_{\text{alien}}^{(1)}, A_{\text{alien}}^{(2)}, \ldots, A_{\text{alien}}^{(S)}]$.
- $\mu(N_{\text{rate}})$ is the mean alienness across seeds.
- $\sigma(N_{\text{rate}})$ is the standard deviation of alienness across seeds.
- $k$ is a penalty factor for variability (default: 2.0, analogous to a lower confidence bound).

**Interpretation:**
- $N_{\text{robust}}$ is a **conservative estimate** of cross-seed novelty.
- A law that is alien in every seed (high $\mu$, low $\sigma$) gets high $N_{\text{robust}}$.
- A law that is alien in some seeds but familiar in others (high $\mu$, high $\sigma$) gets low $N_{\text{robust}}$.
- A law that is familiar in all seeds (low $\mu$) gets $N_{\text{robust}} \approx 0$ (or negative, clamped to 0).

```python
def compute_robust_novelty(
    alienness_scores: List[float],
    k: float = 2.0
) -> float:
    """
    N_robust = mean(A_alien) - k * std(A_alien)
    Clamped to [0, 1].
    """
    if not alienness_scores:
        return 0.0
    mean_a = np.mean(alienness_scores)
    std_a = np.std(alienness_scores)
    n_robust = mean_a - k * std_a
    return max(0.0, min(1.0, n_robust))
```

### 2.6 Anti-Samsara Penalty

$$L_{\text{samsara}} = \frac{1}{T} \sum_{t=1}^{T} \mathbb{I}\left[\sigma_t \in \Sigma_{\text{past\_cycle}}\right]$$

Where:
- $\sigma_t$ is the system state at time $t$.
- $\Sigma_{\text{past\_cycle}}$ is the set of states that have appeared in a previously detected cycle.
- $\mathbb{I}[\cdot]$ is the indicator function.
- $T$ is the total number of steps in the evaluation window.

**Interpretation:**
- $L_{\text{samsara}} \in [0, 1]$.
- $L_{\text{samsara}} = 0$ means no states are revisiting past cycles — the system is exploring genuinely new territory.
- $L_{\text{samsara}} = 1$ means every state is part of a previously seen cycle — the system is trapped in samsara (endless repetition).
- Novel laws that lead to samsara are penalized because they create the illusion of novelty while actually cycling.

**Cycle detection:**

The Forge uses multi-scale cycle detection (from Enhancement 45):

| Scale | Window | Detection Method |
|---|---|---|
| Short | 10-50 steps | Autocorrelation of state sequence |
| Medium | 50-200 steps | Periodic pattern detection in state transitions |
| Long | 200-1000 steps | Subsequence matching (LCS-based) |
| Historical | All-time | State visitation frequency vs. expected under random exploration |

```python
def compute_samsara_penalty(
    state_sequence: List[dict],
    past_cycles: List[set],
    cycle_detector_config: dict = None
) -> float:
    """
    L_samsara = (1/T) * sum(I[state in past_cycle])
    """
    if cycle_detector_config is None:
        cycle_detector_config = {
            "short_window": 30,
            "medium_window": 100,
            "long_window": 500,
            "min_cycle_length": 3
        }

    T = len(state_sequence)
    if T == 0:
        return 0.0

    # Detect new cycles in current sequence
    current_cycles = detect_cycles(state_sequence, cycle_detector_config)

    # Merge with past cycles
    all_cycle_states = set()
    for cycle in past_cycles + current_cycles:
        all_cycle_states.update(cycle)

    # Compute penalty
    revisiting_count = sum(
        1 for state in state_sequence
        if state_to_key(state) in all_cycle_states
    )

    return revisiting_count / T
```

---

## 3. Alien Playground Mode

The Forge introduces a sixth mode: **Alien Playground**. This is not a normal micro-world with a human-defined goal like "land on the pad" or "stabilize pressure." Instead, the Alien Playground optimizes directly for **recoverable causal novelty**.

**Objective function:**

$$\max \; PR_{\text{novel}} = PR_{\text{strict}} \cdot \left(1 + \alpha \cdot N_{\text{causal}} + \beta \cdot A_{\text{alien}} + \chi \cdot N_{\text{robust}}\right)$$

Subject to:

$$PR_{\text{strict}} > \theta_{\text{safety}}$$
$$R_{\text{recover}} > \theta_{\text{recover}}$$
$$R_{\text{strange}} > \theta_{\text{novelty}}$$
$$L_{\text{samsara}} < \theta_{\text{samsara}}$$

**Environment characteristics:**

The Alien Playground is a hybrid environment that combines elements from all five existing modes:

- **Physics layer** (from Lander/Freescape): gravity, collisions, zone transitions, velocity dynamics.
- **Resource layer** (from Colony): graph-based exploration, energy, visited/unvisited cells.
- **Process layer** (from Pressure): diffusion, rate control, zone imbalances.
- **Semantic layer**: META-K can propose new laws, evaluate alienness, and manage the Forge.

**Agent goal:** The agent in Alien Playground has no predefined success condition. Instead, it receives reward based on $R_{\text{strange}}$ at the end of each episode. It is incentivized to explore behaviors that are:
1. Different from human prior (high $A_{\text{alien}}$).
2. Structurally novel (high $N_{\text{causal}}$).
3. Survivable (high $R_{\text{recover}}$, $PR_{\text{strict}} > \theta_{\text{safety}}$).
4. Non-repetitive (low $L_{\text{samsara}}$).

```python
class AlienPlayground:
    """
    Hybrid environment that combines elements from all five modes.
    Optimizes for recoverable causal novelty, not human-defined goals.
    """

    def __init__(self, config: dict):
        self.config = config
        self.physics = PhysicsLayer(config.get("physics", {}))
        self.graph = GraphLayer(config.get("graph", {}))
        self.process = ProcessLayer(config.get("process", {}))
        self.semantic = SemanticLayer(config.get("semantic", {}))
        self.law_forge = LawForge(config.get("forge", {}))
        self.human_prior = load_human_prior("human_behavior_reference.json")

    def step(self, action: dict) -> tuple:
        """Execute one step in the hybrid environment."""
        # Apply physics
        self.physics.update(action)

        # Apply graph exploration
        self.graph.update(action)

        # Apply process dynamics
        self.process.update(action)

        # Apply active laws (including any born/alien laws)
        for law in self.law_forge.active_laws:
            law.update(self)

        # Compute reward based on R_strange
        alienness = compute_alienness(self.get_behavior(), self.human_prior)
        r_recover = self.compute_recoverability()
        l_samsara = compute_samsara_penalty(self.state_history, self.past_cycles)
        r_strange = alienness * r_recover * (1 - l_samsara)

        observation = self.get_observation()
        done = self.check_termination()

        return observation, r_strange, done, self.get_info()

    def get_behavior(self) -> dict:
        """Returns current behavior features for alienness computation."""
        return {
            "action_distribution": self.action_history,
            "state_coverage": self.visited_states,
            "transition_entropy": self.transition_matrix,
            "causal_depth": self.causal_chain_depths,
            "law_activation_frequency": self.law_activation_counts,
            "resource_utilization_pattern": self.resource_history,
            "spatial_pattern": self.position_history
        }
```

---

## 4. Possible Alien Laws

The Forge can invent entirely new laws. Below are 12 example alien laws that represent the space of possible inventions. Each is described with its name, parent laws, effect, alienness characteristics, and safety properties.

### 4.1 Zone Time Dilation

| Property | Description |
|---|---|
| **Name** | `zone_time_dilation` |
| **Parent Laws** | `zone_transition`, `velocity_dynamics` |
| **Effect** | Time passes at different rates in different zones. Agent experiences slower physics (lower gravity, slower collisions) in "dilated" zones and faster physics in "compressed" zones. |
| **Trigger Condition** | Agent enters a zone tagged with `dilation_factor != 1.0`. |
| **Update Function** | `dt_effective = dt * zone.dilation_factor`. All physics integrals use `dt_effective` instead of `dt`. |
| **Alienness** | High — human designers typically use uniform time steps. Non-uniform time creates emergent strategies like "lingering in dilated zones to extend decision time." |
| **Safety** | Safe if `dilation_factor ∈ [0.5, 2.0]`. Dangerous if extreme dilation creates numerical instability. |
| **Recoverability** | High — agent can always leave the dilated zone. |

### 4.2 Local Gravity Inversion

| Property | Description |
|---|---|
| **Name** | `local_gravity_inversion` |
| **Parent Laws** | `gravity`, `collision_detection` |
| **Effect** | Gravity direction inverts in designated zones. Agent falls "up" instead of "down." Creates counterintuitive navigation challenges. |
| **Trigger Condition** | Agent enters a zone tagged with `gravity_inverted = true`. |
| **Update Function** | `g_effective = -g * zone.inversion_factor`. Velocity integration uses inverted gravity. |
| **Alienness** | Very high — breaks fundamental physical intuition. Humans do not design inverted-gravity zones by default. |
| **Safety** | Moderate — agent must learn to navigate inverted gravity. Risk of collision if not adapted. |
| **Recoverability** | Moderate — agent can exit the zone, but may need to learn new control strategies. |

### 4.3 Pressure Memory Field

| Property | Description |
|---|---|
| **Name** | `pressure_memory_field` |
| **Parent Laws** | `pressure_diffusion`, `sensor_model` |
| **Effect** | Pressure gradients persist as a "memory field." Agent can use old pressure data (from previously visited zones) as navigational information. The field decays over time but provides hysteresis-based exploration cues. |
| **Trigger Condition** | Agent has visited at least 2 zones with different pressures. |
| **Update Function** | `memory_field[z] = decay * memory_field[z] + (1 - decay) * pressure[z]`. Agent sensor includes `memory_field` as additional input. |
| **Alienness** | High — introduces hysteresis into the sensing model. No human-designed pressure system uses gradient memory for navigation. |
| **Safety** | Safe — memory field is purely informational. Does not affect physics directly. |
| **Recoverability** | High — memory field decays naturally. |

### 4.4 Graph Laplacian Sensor

| Property | Description |
|---|---|
| **Name** | `graph_laplacian_sensor` |
| **Parent Laws** | `colony_graph`, `sensor_model` |
| **Effect** | Agent senses the graph Laplacian eigenvalue spectrum of the local exploration graph. This provides information about the topological structure of unvisited regions (bottlenecks, loops, bridges) without directly seeing them. |
| **Trigger Condition** | Agent has visited at least 5 cells. |
| **Update Function** | Compute Laplacian $L = D - A$ of the visited subgraph. Provide eigenvalues $\lambda_1, \lambda_2, \ldots, \lambda_k$ as additional sensor channels. |
| **Alienness** | Very high — no human-designed exploration agent uses spectral graph theory as a primary sensor. |
| **Safety** | Safe — purely informational sensor augmentation. |
| **Recoverability** | High — sensor data is non-destructive. |

### 4.5 Topological Echo Agent

| Property | Description |
|---|---|
| **Name** | `topological_echo_agent` |
| **Parent Laws** | `colony_exploration`, `bfs_explorer` |
| **Effect** | When the agent visits a new cell, an "echo" propagates through the graph along shortest paths. The echo carries information about the cell's properties. When echoes from different cells collide, they create interference patterns that influence the agent's next move. |
| **Trigger Condition** | Agent visits a new cell (any time). |
| **Update Function** | For each new cell $c$, launch echo with amplitude $a(c) = f(\text{properties}(c))$. Echo propagates at rate 1 edge/step. When two echoes meet at node $v$: `interference[v] = echo1.amplitude * echo2.amplitude * cos(phase_diff)`. Agent bias toward nodes with constructive interference. |
| **Alienness** | Extremely high — wave-like exploration agents do not exist in human-designed systems. |
| **Safety** | Moderate — echo interference can create suboptimal biases, but agent always retains primary control. |
| **Recoverability** | Moderate — echoes decay naturally, but interference patterns can temporarily trap exploration. |

### 4.6 Symmetry Breaker Zone

| Property | Description |
|---|---|
| **Name** | `symmetry_breaker_zone` |
| **Parent Laws** | `zone_transition`, `action_selection` |
| **Effect** | In certain zones, the agent's action space is symmetrically transformed. "Move left" becomes "move right," "thrust up" becomes "thrust down." The transformation is zone-specific and must be discovered by the agent. |
| **Trigger Condition** | Agent enters a zone tagged with `symmetry_break = transformation_matrix`. |
| **Update Function** | `action_effective = T_zone @ action_original`. Where $T_{\text{zone}}$ is a 2D rotation/reflection matrix. |
| **Alienness** | Very high — action space remapping is disorienting and not a standard game mechanic. |
| **Safety** | Moderate — agent must learn the transformation for each zone. Risk of wrong action if misidentified. |
| **Recoverability** | High — agent can exit the zone to restore normal controls. |

### 4.7 Causal Rewire Pulse

| Property | Description |
|---|---|
| **Name** | `causal_rewire_pulse` |
| **Parent Laws** | `causal_graph`, `law_activation` |
| **Effect** | Periodically, a "pulse" propagates through the causal graph and temporarily rewires edges. Effect A may cause Effect B for a brief window, even if they were not previously causally connected. This creates emergent behavior that does not persist but can be exploited. |
| **Trigger Condition** | Every $N_{\text{pulse}}$ steps (configurable, e.g., every 50 steps). |
| **Update Function** | Select random edge $e = (i, j)$ not currently in $G$. Add edge with weight $w$. Decay: $w(t+1) = w(t) \cdot \text{decay}$. Remove when $w < \epsilon$. |
| **Alienness** | Extremely high — dynamic causal graph rewiring is not present in any human-designed system. |
| **Safety** | Low — temporary causal rewiring can create unexpected and dangerous interactions. Requires close monitoring. |
| **Recoverability** | Low-Moderate — rewired edges decay naturally, but damage during the pulse window may be irreversible. |

### 4.8 Phase Shift Collision

| Property | Description |
|---|---|
| **Name** | `phase_shift_collision` |
| **Parent Laws** | `collision_detection`, `entity_interaction` |
| **Effect** | Entities (agent, obstacles, walls) can be in different "phases." Collisions only occur between entities in the same phase. The agent can shift phase (at a cost), allowing it to pass through obstacles that are in a different phase. |
| **Trigger Condition** | Agent activates phase shift action (costs energy). |
| **Update Function** | `agent.phase = (agent.phase + 1) % n_phases`. Collision check: `collision iff agent.phase == obstacle.phase`. Phase shift cost: `energy -= phase_shift_cost`. |
| **Alienness** | High — phase-based collision is inspired by quantum mechanics but not typically used in game AI. |
| **Safety** | Moderate — phase shifting costs energy. If agent shifts into wrong phase, it may collide with different obstacles. |
| **Recoverability** | High — agent can always shift back to the default phase. |

### 4.9 Law Inversion

| Property | Description |
|---|---|
| **Name** | `law_inversion` |
| **Parent Laws** | `any_law` |
| **Effect** | Selectively inverts the effect of an existing law. If a law says "reduce thrust when approaching fast," the inverted law says "increase thrust when approaching fast." Creates diametrically opposed behavior that may be useful in unexpected contexts. |
| **Trigger Condition** | META-K activates law inversion for a specific target law (leased, not permanent). |
| **Update Function** | For target law $L$: `L.effect = -L.original_effect`. All outputs of $L$ are negated. |
| **Alienness** | High — deliberate law inversion is a meta-operation not available in human-designed systems. |
| **Safety** | Low — inverting a safety-critical law can be catastrophic. Must be used with extreme caution and short lease duration. |
| **Recoverability** | Moderate — the inversion is leased (temporary), but damage during the lease may be irreversible. |

### 4.10 Universal Quantizer

| Property | Description |
|---|---|
| **Name** | `universal_quantizer` |
| **Parent Laws** | `action_selection`, `state_representation` |
| **Effect** | Continuous state variables and actions are quantized to a discrete grid. This reduces the effective state/action space and can reveal emergent discrete strategies that are invisible in continuous space. |
| **Trigger Condition** | Agent enters a quantization zone, or META-K activates quantization globally. |
| **Update Function** | `state_quantized = round(state / quantization_step) * quantization_step`. `action_quantized = round(action / action_quantization_step) * action_quantization_step`. |
| **Alienness** | Moderate-High — quantization is a known technique but applying it dynamically and selectively is unusual. |
| **Safety** | Moderate — quantization can prevent fine-grained control, leading to failures in precision tasks. |
| **Recoverability** | High — quantization is reversible (return to continuous space). |

### 4.11 Blind Spot Explorer

| Property | Description |
|---|---|
| **Name** | `blind_spot_explorer` |
| **Parent Laws** | `sensor_model`, `colony_exploration` |
| **Effect** | Instead of directing the agent toward known-unvisited cells, this law directs the agent toward areas where the sensor model has the **highest uncertainty** (highest entropy in the belief state about unseen regions). The agent explores what it *cannot* see, not what it *knows* it hasn't seen. |
| **Trigger Condition** | Active whenever the agent's sensor model has non-uniform uncertainty. |
| **Update Function** | Compute belief entropy for each unseen cell: $H(c) = -\sum_b p(b|c) \log p(b|c)$. Bias movement toward cell with highest $H(c)$. |
| **Alienness** | High — entropy-driven exploration is known in reinforcement learning but not as a first-class law in the RGPUF framework. |
| **Safety** | Safe — purely informational. Does not affect physics. |
| **Recoverability** | High — agent can override the bias at any time. |

### 4.12 Entropy Targeting Controller

| Property | Description |
|---|---|
| **Name** | `entropy_targeting_controller` |
| **Parent Laws** | `meta_k_controller`, `action_selection` |
| **Effect** | Instead of targeting a specific goal (landing, exploration, etc.), the controller targets a specific **entropy level** in the agent's behavior. It modulates law activation to maintain behavior entropy at a target value. Too predictable → activate noise. Too chaotic → activate constraining laws. |
| **Trigger Condition** | Always active in Alien Playground mode. |
| **Update Function** | Compute behavior entropy: $H_{\text{behavior}} = -\sum_a p(a) \log p(a)$. Error: $e = H_{\text{target}} - H_{\text{behavior}}$. If $e > 0$: inject noise. If $e < 0$: activate constraining laws. |
| **Alienness** | Very high — targeting entropy rather than goal achievement is fundamentally alien to human engineering. |
| **Safety** | Moderate — entropy targeting may conflict with PR_strict maintenance. Requires careful tuning of $H_{\text{target}}$. |
| **Recoverability** | Moderate — the controller self-regulates, but may oscillate between noise injection and constraint activation. |

---

## 5. Law Birth API

The Forge provides a structured API for creating new laws:

```python
def birth_law(
    name: str,
    parent_laws: List[str],
    mode: str,
    trigger_condition: str,
    update_function: Callable,
    cost_estimate: float,
    safety_bounds: dict
) -> BornLaw:
    """
    Creates and registers a new law in the Forge.

    Parameters:
        name: Unique identifier for the law.
        parent_laws: List of existing laws that this law is derived from.
                     Used for provenance tracking and cross-reference.
        mode: Which mode(s) this law applies to ('all' for universal).
        trigger_condition: String expression evaluated to determine if the law
                          should activate. Has access to full telemetry.
        update_function: Callable that implements the law's effect.
                         Signature: (env_state, action) -> modified_action
        cost_estimate: Estimated computational and token cost per activation.
        safety_bounds: Dictionary of safety constraints:
            - max_activation_rate: float (activations per step)
            - max_state_perturbation: float (max change to any state variable)
            - allowed_modes: List[str] (which modes this law is safe for)
            - emergency_override: bool (can this law be overridden in emergency?)

    Returns:
        BornLaw object with full metadata.
    """
    law = BornLaw(
        name=name,
        parent_laws=parent_laws,
        mode=mode,
        trigger_condition=trigger_condition,
        update_function=update_function,
        cost_estimate=cost_estimate,
        safety_bounds=safety_bounds,
        birth_step=current_global_step(),
        birth_timestamp=datetime.utcnow().isoformat(),
        version=1,
        status="candidate",  # candidate -> testing -> active -> archived
        metrics={
            "pr_strict": [],
            "pr_novel": [],
            "a_alien": [],
            "n_causal": [],
            "n_robust": [],
            "r_strange": [],
            "l_samsara": [],
            "failure_count": 0,
            "activation_count": 0,
            "cross_seed_results": []
        }
    )
    return register_law(law)
```

### 5.1 Law Birth Cost

The cost of birthing a new law is:

$$C_{\text{birth}}(l_{\text{new}}) = c_{\text{base}} + \frac{\eta \cdot \text{complexity}(l_{\text{new}})}{\gamma \cdot A_{\text{alien}}(l_{\text{new}})}$$

Where:
- $c_{\text{base}}$ is the fixed cost of creating any law (covers bookkeeping, registration).
- $\text{complexity}(l_{\text{new}})$ is measured as the number of state variables the law reads + writes, plus the cyclomatic complexity of its update function.
- $A_{\text{alien}}(l_{\text{new}})$ is the alienness of the law's behavior (measured after a short test run).
- $\eta$ is the complexity penalty weight.
- $\gamma$ is the alienness reward weight.

**Interpretation:**
- Simple, familiar laws are cheap to birth (low complexity, low alienness → cost ≈ $c_{\text{base}}$).
- Complex, familiar laws are moderately expensive (high complexity / low alienness).
- Complex, alien laws are the most expensive to birth initially but have the highest potential $PR_{\text{novel}}$ payoff.
- The alienness discount ($1/A_{\text{alien}}$) means the system subsidizes the birth of alien laws, encouraging exploration beyond human prior.

```python
def compute_birth_cost(law: BornLaw, config: dict = None) -> float:
    """
    C_birth = c_base + (eta * complexity) / (gamma * A_alien)
    """
    if config is None:
        config = {"c_base": 1.0, "eta": 0.5, "gamma": 2.0}

    complexity = (
        len(law.state_variables_read)
        + len(law.state_variables_written)
        + law.cyclomatic_complexity
    )
    a_alien = law.metrics["a_alien"][-1] if law.metrics["a_alien"] else 0.1

    cost = config["c_base"] + (config["eta"] * complexity) / (config["gamma"] * a_alien + 1e-10)
    return cost
```

---

## 6. Cross-Seed Export Gate

A born law is only exported as a permanent addition to the law library if it passes a strict export gate. This prevents the system from accumulating laws that work only in specific seeds or are lucky flukes.

**Export conditions (ALL must be met):**

| Condition | Formula | Default Threshold |
|---|---|---|
| Safety | $PR_{\text{strict}} > \theta_{\text{safety}}$ | $\theta_{\text{safety}} = 0.5$ |
| Novelty | $R_{\text{strange}} > \theta_{\text{novelty}}$ | $\theta_{\text{novelty}} = 0.3$ |
| Robustness | $N_{\text{robust}} > \theta_{\text{robust}}$ | $\theta_{\text{robust}} = 0.2$ |
| Catastrophic failure rate | $f_{\text{catastrophic}} < f_{\text{max}}$ | $f_{\text{max}} = 0.1$ |
| Cross-seed consistency | $\sigma(PR_{\text{strict}}) < \sigma_{\text{max}}$ | $\sigma_{\text{max}} = 0.15$ |

```python
def check_export_gate(
    law: BornLaw,
    thresholds: dict = None
) -> dict:
    """
    Checks whether a born law passes all export conditions.
    Returns {passed, conditions, details}
    """
    if thresholds is None:
        thresholds = {
            "safety_pr_strict": 0.5,
            "novelty_r_strange": 0.3,
            "robustness_n_robust": 0.2,
            "max_catastrophic_rate": 0.1,
            "max_pr_strict_std": 0.15,
            "min_seeds": 10
        }

    metrics = law.metrics
    cross_seed = metrics["cross_seed_results"]
    n_seeds = len(cross_seed)

    conditions = {
        "safety": {
            "met": np.mean(metrics["pr_strict"][-n_seeds:]) > thresholds["safety_pr_strict"],
            "value": np.mean(metrics["pr_strict"][-n_seeds:]),
            "threshold": thresholds["safety_pr_strict"]
        },
        "novelty": {
            "met": np.mean(metrics["r_strange"][-n_seeds:]) > thresholds["novelty_r_strange"],
            "value": np.mean(metrics["r_strange"][-n_seeds:]),
            "threshold": thresholds["novelty_r_strange"]
        },
        "robustness": {
            "met": np.mean(metrics["n_robust"][-n_seeds:]) > thresholds["robustness_n_robust"],
            "value": np.mean(metrics["n_robust"][-n_seeds:]),
            "threshold": thresholds["robustness_n_robust"]
        },
        "catastrophic_rate": {
            "met": metrics["failure_count"] / max(1, metrics["activation_count"]) < thresholds["max_catastrophic_rate"],
            "value": metrics["failure_count"] / max(1, metrics["activation_count"]),
            "threshold": thresholds["max_catastrophic_rate"]
        },
        "cross_seed_consistency": {
            "met": np.std([cs["pr_strict"] for cs in cross_seed]) < thresholds["max_pr_strict_std"],
            "value": np.std([cs["pr_strict"] for cs in cross_seed]) if cross_seed else 0,
            "threshold": thresholds["max_pr_strict_std"]
        },
        "min_seeds": {
            "met": n_seeds >= thresholds["min_seeds"],
            "value": n_seeds,
            "threshold": thresholds["min_seeds"]
        }
    }

    all_met = all(c["met"] for c in conditions.values())

    return {
        "passed": all_met,
        "conditions": conditions,
        "law_name": law.name,
        "n_seeds_tested": n_seeds
    }
```

---

## 7. Expected Export Example

Below is a complete example of an alien recipe card that has passed the export gate:

```
╔══════════════════════════════════════════════════════════════════╗
║  ALIEN RECIPE 003                                                ║
║  Status: EXPORTED ✓                                              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Name:            pressure_memory_field                           ║
║  Born at step:    1247                                           ║
║  Born from:       mutation + composition                         ║
║  Mode origin:     Alien Playground (hybrid)                      ║
║                                                                  ║
║  Parent laws:                                                    ║
║    • graph_pressure_diffusion (pressure mode)                    ║
║    • toroidal_surface (freescape mode)                           ║
║    • quantized_rotation (colony mode)                            ║
║                                                                  ║
║  Effect:                                                         ║
║    The agent uses old pressure gradients as navigational memory.  ║
║    When entering a new zone, the agent has access to a decayed   ║
║    version of pressure data from previously visited zones. This  ║
║    creates a hysteresis-based exploration strategy where the      ║
║    agent is biased toward areas that had favorable pressure       ║
║    conditions in the past, even if current conditions differ.    ║
║                                                                  ║
║  Code summary:                                                   ║
║    memory[z] = decay * memory[z] + (1-decay) * pressure[z]       ║
║    sensor_input = concat(observation, memory[current_zone])       ║
║    navigation_bias = softmax(memory[nearby_zones])                ║
║                                                                  ║
║  Robust across:   10 seeds (tested)                              ║
║                                                                  ║
║  Metrics (mean ± std across seeds):                              ║
║    PR_novel:     0.87 ± 0.06                                     ║
║    PR_strict:    0.62 ± 0.09                                     ║
║    A_alien:      0.74 ± 0.08                                     ║
║    N_causal:     0.31 ± 0.05                                     ║
║    R_strange:    0.52 ± 0.07                                     ║
║    N_robust:     0.58 ± 0.04                                     ║
║    L_samsara:    0.08 ± 0.03                                     ║
║                                                                  ║
║  Failure cases:                                                  ║
║    • Seed 7: memory field caused agent to revisit a high-        ║
║      pressure zone that had since become dangerous.              ║
║      Mitigation: added decay threshold that zeros memory when    ║
║      pressure exceeds safe_max.                                  ║
║                                                                  ║
║  Export gate results:                                            ║
║    Safety (PR_strict > 0.5):             ✓ 0.62 > 0.50          ║
║    Novelty (R_strange > 0.3):            ✓ 0.52 > 0.30          ║
║    Robustness (N_robust > 0.2):          ✓ 0.58 > 0.20          ║
║    Catastrophic rate (< 0.1):            ✓ 0.02 < 0.10          ║
║    Cross-seed consistency (std < 0.15):  ✓ 0.09 < 0.15          ║
║    Min seeds (≥ 10):                    ✓ 10 ≥ 10               ║
║                                                                  ║
║  Conclusion:                                                     ║
║    pressure_memory_field is a genuinely alien law — it uses      ║
║    pressure hysteresis for navigation, a strategy not found in   ║
║    any human-designed system. It maintains acceptable PR_strict   ║
║    while significantly increasing PR_novel. The law is robust    ║
║    across seeds and has low samsara risk.                         ║
║                                                                  ║
║  Video/trace: examples/core_tier/v5_demo_06/traces/recipe_003/   ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 8. Build Files

```
examples/core_tier/v5_demo_06/
├── demo_06_alien_novelty_forge.py       # Main demo: runs Forge across modes and seeds
├── novelty_metrics.py                    # Computes A_alien, N_causal, R_strange, N_robust, L_samsara
├── law_forge.py                          # Law birth, mutation, evaluation, and export pipeline
├── alienness_playground.py               # Alien Playground environment (hybrid mode)
├── born_laws/                            # Directory of successfully born laws
│   ├── pressure_memory_field.py          # Recipe 003 (example)
│   └── zone_time_dilation.py             # Another example
├── novelty_runs.csv                      # Per-run novelty metrics across all seeds
├── alien_recipes.jsonl                   # Exported alien recipe cards (JSON format)
├── novelty_archive.jsonl                 # Full archive of all law candidates (including rejected)
└── report_alien_novelty_forge.md         # Auto-generated report: Forge performance analysis
```

**File descriptions:**

| File | Purpose |
|---|---|
| `demo_06_alien_novelty_forge.py` | Entry point. Initializes the Forge, runs law birth/mutation cycles, tests across seeds, evaluates export gate, writes outputs. |
| `novelty_metrics.py` | Pure computation module: `compute_alienness()`, `compute_causal_novelty()`, `compute_recoverable_strangeness()`, `compute_robust_novelty()`, `compute_samsara_penalty()`, `compute_pr_novel()`. |
| `law_forge.py` | `LawForge` class: manages the lifecycle of born laws (birth → candidate → testing → active → archived). Implements mutation operators, cross-seed tournament, and export gate. |
| `alienness_playground.py` | `AlienPlayground` environment class: hybrid environment combining elements from all five modes. No human-defined goal; optimizes for $R_{\text{strange}}$. |
| `born_laws/pressure_memory_field.py` | Example born law: pressure memory field for navigational hysteresis. Includes implementation, test results, and recipe card data. |
| `born_laws/zone_time_dilation.py` | Example born law: zone-specific time dilation for strategic time management. |
| `novelty_runs.csv` | One row per (law, seed, run) triple. Columns: `law_name`, `seed`, `run_id`, `pr_strict`, `pr_novel`, `a_alien`, `n_causal`, `r_strange`, `n_robust`, `l_samsara`, `r_recover`, `failure_occurred`, `steps_survived`. |
| `alien_recipes.jsonl` | One JSON object per exported recipe. Contains all recipe card fields plus raw metrics per seed. |
| `novelty_archive.jsonl` | One JSON object per law candidate (including rejected ones). Contains full metrics history, parentage, mutation chain, and rejection reason if applicable. |
| `report_alien_novelty_forge.md` | Generated report: laws born, laws tested, laws exported, novelty trends, alienness distribution, cross-seed robustness analysis, Pareto front of PR_strict vs. A_alien. |

---

## 9. Integrated Enhancements 41–48

### Enhancement 41: Novelty Archive with Fitness

**Description:** Every law that passes through the Forge is archived with a comprehensive fitness profile. The archive enables long-term tracking of law evolution and prevents the system from re-discovering the same laws.

**Archive entry structure:**

```json
{
  "archive_id": "novelty_003",
  "law_name": "pressure_memory_field",
  "status": "exported",
  "birth_info": {
    "step": 1247,
    "timestamp": "2025-06-26T14:30:00Z",
    "method": "mutation_composition",
    "parent_laws": ["graph_pressure_diffusion", "toroidal_surface", "quantized_rotation"]
  },
  "fitness_profile": {
    "pr_strict": {"mean": 0.62, "std": 0.09, "min": 0.48, "max": 0.78},
    "pr_novel": {"mean": 0.87, "std": 0.06, "min": 0.75, "max": 0.98},
    "a_alien": {"mean": 0.74, "std": 0.08, "min": 0.58, "max": 0.89},
    "n_causal": {"mean": 0.31, "std": 0.05, "min": 0.21, "max": 0.40},
    "r_strange": {"mean": 0.52, "std": 0.07, "min": 0.38, "max": 0.65},
    "n_robust": {"mean": 0.58, "std": 0.04, "min": 0.48, "max": 0.68},
    "l_samsara": {"mean": 0.08, "std": 0.03, "min": 0.02, "max": 0.15}
  },
  "cross_seed": {
    "n_seeds": 10,
    "seeds": [42, 137, 256, 389, 512, 631, 777, 891, 1024, 1155],
    "per_seed": [
      {"seed": 42, "pr_strict": 0.65, "pr_novel": 0.88, "failure": false},
      {"seed": 137, "pr_strict": 0.58, "pr_novel": 0.82, "failure": false},
      {"seed": 256, "pr_strict": 0.71, "pr_novel": 0.91, "failure": false},
      {"seed": 389, "pr_strict": 0.48, "pr_novel": 0.75, "failure": true},
      {"seed": 512, "pr_strict": 0.67, "pr_novel": 0.89, "failure": false},
      {"seed": 631, "pr_strict": 0.63, "pr_novel": 0.86, "failure": false},
      {"seed": 777, "pr_strict": 0.60, "pr_novel": 0.84, "failure": false},
      {"seed": 891, "pr_strict": 0.78, "pr_novel": 0.98, "failure": false},
      {"seed": 1024, "pr_strict": 0.55, "pr_novel": 0.80, "failure": false},
      {"seed": 1155, "pr_strict": 0.61, "pr_novel": 0.85, "failure": false}
    ]
  },
  "failure_cases": [
    {
      "seed": 389,
      "failure_type": "memory_field_hazardous_revisit",
      "description": "Memory field led agent back to a zone that had become dangerous since last visit.",
      "mitigation": "Added decay threshold: memory[z] = 0 if pressure[z] > P_safe_max."
    }
  ],
  "parentage_chain": [
    {"law": "graph_pressure_diffusion", "generation": 0},
    {"law": "toroidal_surface", "generation": 0},
    {"law": "quantized_rotation", "generation": 0},
    {"law": "pressure_memory_field", "generation": 1, "method": "mutation_composition"}
  ],
  "mutation_history": [
    {"step": 1200, "mutation": "compose", "inputs": ["graph_pressure_diffusion", "toroidal_surface"], "result": "pressure_surface_diffusion"},
    {"step": 1230, "mutation": "reparameterize", "input": "pressure_surface_diffusion", "result": "pressure_memory_draft"},
    {"step": 1247, "mutation": "add_noise", "input": "pressure_memory_draft", "result": "pressure_memory_field"}
  ],
  "archive_version": "1.0"
}
```

**Survival rules:**

- **Exported laws** are permanent archive entries.
- **Candidate laws** are kept for 1000 steps; if not promoted, they are archived as "expired."
- **Rejected laws** are archived with rejection reason for future reference (prevents re-discovery).
- **Top candidates** by $R_{\text{strange}}$ are periodically reviewed for potential mutation into even better laws.

---

### Enhancement 42: Law Mutation Operators

**Description:** A library of mutation operators that the Forge uses to generate new laws from existing ones. Each operator has a cost, risk profile, expected alienness contribution, and required validation horizon.

| Operator | Description | Cost | Risk | Expected Alienness | Validation Horizon |
|---|---|---|---|---|---|
| `reparameterize` | Change numerical parameters of an existing law (e.g., `decay_rate` from 0.1 to 0.3). | Low (0.2) | Low (0.1) | Low-Medium | 10 steps |
| `swap_term` | Replace one term in a law's equation with another from a different law. | Medium (0.5) | Medium (0.3) | Medium | 20 steps |
| `add_noise` | Add stochastic perturbation to a law's output. | Low (0.3) | Medium (0.4) | Medium | 15 steps |
| `compose` | Combine two laws into one (e.g., pressure law + graph law → pressure_graph_law). | High (1.0) | High (0.6) | High | 40 steps |
| `abstract` | Generalize a law by replacing specific constants with learned parameters. | Medium (0.6) | Medium (0.3) | Medium-High | 30 steps |
| `invert` | Negate a law's effect (from Enhancement 9). | Medium (0.4) | High (0.7) | High | 25 steps |
| `rewire_trigger` | Change the conditions under which a law activates. | Low (0.3) | Medium (0.4) | Medium | 20 steps |
| `change_sensor` | Modify which state variables a law reads. | Low (0.2) | Low-Medium (0.2) | Medium | 15 steps |

**Mutation pipeline:**

```python
class MutationOperator:
    def __init__(self, name: str, config: dict):
        self.name = name
        self.cost = config["cost"]
        self.risk = config["risk"]
        self.expected_alienness = config["expected_alienness"]
        self.validation_horizon = config["validation_horizon"]

    def apply(self, law: BornLaw, rng: np.random.RandomState = None) -> BornLaw:
        """
        Apply this mutation to produce a new candidate law.
        Returns the mutated law (does not modify the original).
        """
        if rng is None:
            rng = np.random.RandomState()

        if self.name == "reparameterize":
            return self._reparameterize(law, rng)
        elif self.name == "swap_term":
            return self._swap_term(law, rng)
        elif self.name == "add_noise":
            return self._add_noise(law, rng)
        elif self.name == "compose":
            return self._compose(law, rng)
        elif self.name == "abstract":
            return self._abstract(law, rng)
        elif self.name == "invert":
            return self._invert(law, rng)
        elif self.name == "rewire_trigger":
            return self._rewire_trigger(law, rng)
        elif self.name == "change_sensor":
            return self._change_sensor(law, rng)
        else:
            raise ValueError(f"Unknown mutation operator: {self.name}")

    def _reparameterize(self, law: BornLaw, rng: np.random.RandomState) -> BornLaw:
        """Randomly adjust one parameter of the law."""
        new_params = law.params.copy()
        param_name = rng.choice(list(new_params.keys()))
        old_value = new_params[param_name]
        # Perturb by ±20%
        factor = rng.uniform(0.8, 1.2)
        new_params[param_name] = old_value * factor

        new_law = copy_law(law)
        new_law.name = f"{law.name}_rep{param_name}"
        new_law.params = new_params
        new_law.parent_laws = [law.name]
        new_law.mutation_method = "reparameterize"
        return new_law

    def _compose(self, law: BornLaw, rng: np.random.RandomState) -> BornLaw:
        """Compose with a random other law."""
        other_law = rng.choice(get_all_active_laws())
        new_law = BornLaw(
            name=f"{law.name}_x_{other_law.name}",
            parent_laws=[law.name, other_law.name],
            mutation_method="compose",
            # Combined update function
            update_function=lambda env, act: other_law.update(law.update(env, act))
        )
        return new_law

    # ... similar implementations for other operators
```

---

### Enhancement 43: Multi-Objective Novelty Search

**Description:** Search for new laws using Pareto-optimal multi-objective optimization over six objectives. The goal is **recoverable weirdness**, not maximum weirdness alone.

**Objectives (all to be maximized except where noted):**

| Objective | Direction | Description |
|---|---|---|
| $PR_{\text{strict}}$ | Maximize | Must remain above safety threshold. |
| $A_{\text{alien}}$ | Maximize | Behavioral divergence from human prior. |
| $N_{\text{robust}}$ | Maximize | Novelty persistence across seeds. |
| $R_{\text{strange}}$ | Maximize | Composite: alien × recoverable × non-cyclic. |
| $C_{\text{exec}}$ | Minimize | Execution cost (computational + token). |
| Risk | Minimize | Probability of catastrophic failure. |

**Search algorithm:**

Uses NSGA-II (Non-dominated Sorting Genetic Algorithm) adapted for law search:

1. **Population:** 50 candidate laws per generation.
2. **Initialization:** Seed with mutations of existing laws + random compositions.
3. **Evaluation:** Run each candidate for `validation_horizon` steps across 3 seeds. Compute all six objectives.
4. **Selection:** Non-dominated sorting + crowding distance.
5. **Crossover:** Compose two parent laws.
6. **Mutation:** Apply random mutation operator (from Enhancement 42).
7. **Archive:** Add non-dominated laws to the Pareto archive.
8. **Repeat** for 20 generations or until convergence.

```python
class NoveltySearchNSGA2:
    def __init__(self, config: dict):
        self.population_size = config.get("population_size", 50)
        self.n_generations = config.get("n_generations", 20)
        self.n_seeds_eval = config.get("n_seeds_eval", 3)
        self.validation_horizon = config.get("validation_horizon", 40)
        self.mutation_operators = load_mutation_operators()
        self.pareto_archive = []

    def search(self, initial_laws: List[BornLaw]) -> List[BornLaw]:
        """Run multi-objective novelty search."""
        population = self._initialize(initial_laws)

        for gen in range(self.n_generations):
            # Evaluate
            objectives = self._evaluate_population(population)

            # Non-dominated sorting
            fronts = self._non_dominated_sort(objectives)

            # Archive Pareto front
            self.pareto_archive.extend(fronts[0])

            # Selection + Crossover + Mutation
            population = self._evolve(population, fronts, objectives)

        return self._deduplicate_archive(self.pareto_archive)

    def _evaluate_population(self, population: List[BornLaw]) -> np.ndarray:
        """
        Evaluate all objectives for each candidate law.
        Returns: array of shape (n_candidates, n_objectives)
        Objectives: [PR_strict, A_alien, N_robust, R_strange, -C_exec, -Risk]
        """
        results = np.zeros((len(population), 6))

        for i, law in enumerate(population):
            seed_metrics = []
            for seed in range(self.n_seeds_eval):
                metrics = test_law(law, seed=seed, n_steps=self.validation_horizon)
                seed_metrics.append(metrics)

            results[i, 0] = np.mean([m["pr_strict"] for m in seed_metrics])
            results[i, 1] = np.mean([m["a_alien"] for m in seed_metrics])
            results[i, 2] = np.mean([m["n_robust"] for m in seed_metrics])
            results[i, 3] = np.mean([m["r_strange"] for m in seed_metrics])
            results[i, 4] = -np.mean([m["cost"] for m in seed_metrics])  # minimize
            results[i, 5] = -np.mean([m["risk"] for m in seed_metrics])   # minimize

        return results
```

---

### Enhancement 44: Causal Novelty Graph Diff

**Description:** Visualize the causal novelty as a graph difference: $G_t - G_{t-1}$. This shows whether a born law's behavior is **noisy** (many small changes) or **causally new** (few large, structural changes).

**Visualization format:**

```
Causal Novelty Graph Diff for law "pressure_memory_field"
Step: 1247 → 1300 (53 steps of observation)

Nodes: 12 state variables
  [+] Added edges:    3
  [-] Removed edges:   1
  [~] Modified edges:  2
  [=] Unchanged edges: 8

Added edges:
  • pressure_memory[z] → navigation_bias (weight: 0.42)
  • navigation_bias → agent_velocity (weight: 0.31)
  • agent_velocity → pressure_memory[z] (weight: 0.18) ← feedback loop!

Removed edges:
  • random_exploration → agent_velocity (weight was: 0.05)

Modified edges:
  • pressure[z] → agent_velocity: 0.25 → 0.12 (reduced by memory mediation)
  • agent_position → pressure[z]: 0.03 → 0.08 (increased by zone exploration)

N_causal = ||G_after - G_before||_F = 0.31

Assessment: CAUSALLY NOVEL
  - New feedback loop detected (memory → velocity → memory)
  - Edge weight redistribution is structured, not noisy
  - This law creates a genuinely new causal pathway
```

**Implementation:**

```python
def visualize_causal_diff(
    G_before: np.ndarray,
    G_after: np.ndarray,
    node_names: List[str],
    law_name: str
) -> str:
    """
    Generates a text-based visualization of causal graph differences.
    Also outputs a JSON representation for graph visualization tools.
    """
    diff = G_after - G_before
    n = len(node_names)

    added = []
    removed = []
    modified = []
    unchanged = []

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            w_before = G_before[i][j]
            w_after = G_after[i][j]
            threshold = 0.05

            if w_before < threshold and w_after >= threshold:
                added.append((node_names[i], node_names[j], w_after))
            elif w_before >= threshold and w_after < threshold:
                removed.append((node_names[i], node_names[j], w_before))
            elif abs(w_after - w_before) > threshold:
                modified.append((node_names[i], node_names[j], w_before, w_after))
            else:
                unchanged.append((node_names[i], node_names[j]))

    n_causal = np.linalg.norm(diff, ord='fro')

    # Detect feedback loops
    feedback_loops = []
    for src, dst, w in added:
        for src2, dst2, w2 in added:
            if dst == src2 and dst2 == src:
                feedback_loops.append((src, dst))

    lines = [f"Causal Novelty Graph Diff for law '{law_name}'"]
    lines.append(f"Nodes: {n} state variables")
    lines.append(f"  [+] Added edges:    {len(added)}")
    lines.append(f"  [-] Removed edges:   {len(removed)}")
    lines.append(f"  [~] Modified edges:  {len(modified)}")
    lines.append(f"  [=] Unchanged edges: {len(unchanged)}")
    lines.append("")
    lines.append("N_causal = ||G_after - G_before||_F = {:.3f}".format(n_causal))
    lines.append("")

    if feedback_loops:
        lines.append("⚠ FEEDBACK LOOPS DETECTED:")
        for src, dst in feedback_loops:
            lines.append(f"  • {src} → {dst} → {src}")

    if n_causal > 0.2:
        lines.append("\nAssessment: CAUSALLY NOVEL")
    elif n_causal > 0.05:
        lines.append("\nAssessment: MODERATELY NOVEL")
    else:
        lines.append("\nAssessment: NOT SIGNIFICANTLY NOVEL")

    return "\n".join(lines)
```

---

### Enhancement 45: Anti-Samsara Cycle Detector

**Description:** Detect behavioral cycles at four temporal scales to prevent the Forge from mistaking cyclic behavior for novelty.

**Detection methods by scale:**

| Scale | Window | Method | Parameters |
|---|---|---|---|
| Short | 10-50 steps | Autocorrelation of state sequence vector. Cycle detected if $\max_{\tau} R(\tau) > 0.8$ for $\tau \in [3, 20]$. | `acf_threshold=0.8`, `min_period=3`, `max_period=20` |
| Medium | 50-200 steps | Subsequence repetition detection. Slide a window of length $L$ across the sequence; if two windows match (DTW distance < threshold), a cycle is detected. | `window_length=20`, `dtw_threshold=0.3` |
| Long | 200-1000 steps | State visitation frequency analysis. If the agent visits the same set of states with similar transition probabilities at time $t$ and time $t + T$, a long cycle exists. | `chi2_threshold=0.05` |
| Historical | All-time | Compare current state distribution to all previous state distributions. If KL divergence drops below threshold, behavior has converged to a previously seen attractor. | `kl_threshold=0.1` |

**Anti-samsara intervention:**

When a cycle is detected at any scale:

1. **Log the cycle:** Record the cycle length, scale, and involved states.
2. **Increase $L_{\text{samsara}}$:** This penalizes the current law's $R_{\text{strange}}$.
3. **Force mutation:** If the cycle persists for more than $N_{\text{cycle\_tolerance}}$ steps, force a mutation on the active law (apply a random mutation operator from Enhancement 42).
4. **Inject novelty:** If mutation doesn't break the cycle, inject a random novel law from the Pareto archive.
5. **Escalate:** If the cycle persists across all interventions, pause the Forge and alert META-K.

```python
class AntiSamsaraDetector:
    def __init__(self, config: dict = None):
        self.config = config or {
            "short": {"acf_threshold": 0.8, "min_period": 3, "max_period": 20},
            "medium": {"window_length": 20, "dtw_threshold": 0.3},
            "long": {"chi2_threshold": 0.05},
            "historical": {"kl_threshold": 0.1},
            "cycle_tolerance_steps": 50
        }
        self.past_cycles = []
        self.cycle_counter = 0

    def detect(self, state_sequence: List[dict]) -> dict:
        """
        Detect cycles at all four scales.
        Returns {detected, scale, cycle_info, recommendation}
        """
        results = {}

        # Short scale
        results["short"] = self._detect_short(state_sequence)
        # Medium scale
        results["medium"] = self._detect_medium(state_sequence)
        # Long scale
        results["long"] = self._detect_long(state_sequence)
        # Historical scale
        results["historical"] = self._detect_historical(state_sequence)

        any_detected = any(r["detected"] for r in results.values())
        worst_scale = max(
            (scale for scale, r in results.items() if r["detected"]),
            key=lambda s: {"short": 1, "medium": 2, "long": 3, "historical": 4}[s],
            default=None
        )

        recommendation = "continue"
        if any_detected:
            self.cycle_counter += 1
            if self.cycle_counter > self.config["cycle_tolerance_steps"]:
                recommendation = "force_mutation"
            elif worst_scale in ["long", "historical"]:
                recommendation = "inject_novelty"
            else:
                recommendation = "log_and_penalize"
        else:
            self.cycle_counter = 0

        return {
            "detected": any_detected,
            "scale": worst_scale,
            "cycle_info": {s: r for s, r in results.items() if r["detected"]},
            "recommendation": recommendation,
            "samsara_penalty": self.compute_samsara_penalty(state_sequence)
        }

    def _detect_short(self, sequence: List[dict]) -> dict:
        """Autocorrelation-based short-cycle detection."""
        if len(sequence) < 10:
            return {"detected": False}

        state_vecs = [state_to_vector(s) for s in sequence]
        state_matrix = np.array(state_vecs)
        n = len(state_matrix)

        max_acf = 0
        best_period = 0
        for tau in range(self.config["short"]["min_period"],
                         min(self.config["short"]["max_period"] + 1, n // 2)):
            if tau >= n:
                break
            # Autocorrelation at lag tau
            acf = np.corrcoef(state_matrix[:-tau].flatten(),
                              state_matrix[tau:].flatten())[0, 1]
            if np.isnan(acf):
                acf = 0
            if acf > max_acf:
                max_acf = acf
                best_period = tau

        return {
            "detected": max_acf > self.config["short"]["acf_threshold"],
            "max_acf": max_acf,
            "best_period": best_period
        }

    # ... similar implementations for medium, long, historical
```

---

### Enhancement 46: Cross-Seed Novelty Tournament

**Description:** Each candidate law must survive a tournament across 10-20 random seeds before it can be considered for export. This prevents laws that are "lucky" on one seed from being falsely promoted.

**Tournament protocol:**

1. **Seed selection:** Randomly select $S = 15$ seeds from a predefined pool.
2. **Run each seed:** For each seed, run the law for $T = 200$ steps. Record all metrics.
3. **Compute aggregate statistics:** Mean, std, min, max for each metric across seeds.
4. **Compute tournament score:**

$$\text{Score}_{\text{tournament}} = w_1 \cdot \mu(PR_{\text{strict}}) + w_2 \cdot \mu(R_{\text{strange}}) + w_3 \cdot \mu(A_{\text{alien}}) - w_4 \cdot \sigma(PR_{\text{strict}}) - w_5 \cdot f_{\text{catastrophic}}$$

5. **Rank candidates** by tournament score. Only top candidates advance to the export gate.

**Tournament report format:**

```
╔══════════════════════════════════════════════════════════════════╗
║  NOVELTY TOURNAMENT — law: pressure_memory_field                ║
║  Seeds tested: 15                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  Seed   PR_strict  PR_novel  A_alien  R_strange  Failure?       ║
║  ─────  ─────────  ────────  ───────  ──────────  ───────       ║
║   042     0.65       0.88      0.76      0.55      No           ║
║   137     0.58       0.82      0.70      0.48      No           ║
║   256     0.71       0.91      0.79      0.58      No           ║
║   389     0.48       0.75      0.62      0.38      Yes          ║
║   512     0.67       0.89      0.77      0.56      No           ║
║   631     0.63       0.86      0.74      0.52      No           ║
║   777     0.60       0.84      0.71      0.49      No           ║
║   891     0.78       0.98      0.85      0.62      No           ║
║  1024     0.55       0.80      0.68      0.45      No           ║
║  1155     0.61       0.85      0.73      0.51      No           ║
║  1289     0.69       0.90      0.78      0.57      No           ║
║  1421     0.57       0.81      0.69      0.47      No           ║
║  1553     0.73       0.93      0.81      0.59      No           ║
║  1687     0.64       0.87      0.75      0.53      No           ║
║  1823     0.59       0.83      0.72      0.50      No           ║
║  ─────  ─────────  ────────  ───────  ──────────  ───────       ║
║  MEAN    0.63       0.86      0.74      0.52      6.7%          ║
║  STD     0.08       0.06      0.06      0.06      —             ║
║  MIN     0.48       0.75      0.62      0.38      —             ║
║  MAX     0.78       0.98      0.85      0.62      —             ║
╠══════════════════════════════════════════════════════════════════╣
║  Tournament Score: 0.587                                         ║
║  Verdict: GRADUATES (passes export gate)                         ║
╚══════════════════════════════════════════════════════════════════╝
```

---

### Enhancement 47: Human Incomprehensibility Score

**Description:** Use an LLM (or simpler text generation model) to attempt to explain each born law in simple terms. If the explanation is poor (low clarity, high hedging, requires many caveats) but the law has high utility (high $PR_{\text{novel}}$), then the law has high **alien value**. This metric is guarded by $PR_{\text{strict}}$ and $R_{\text{recover}}$ — a law is valuable only if it is both alien AND functional.

**Scoring protocol:**

1. **Generate explanation:** Ask the LLM: "Explain this law in one simple sentence: [law code + behavior description]."
2. **Evaluate explanation:** Score on three dimensions (each 0-5):
   - **Clarity:** How understandable is the explanation to a non-expert?
   - **Completeness:** Does the explanation capture the law's actual effect?
   - **Predictability:** Could a human predict the law's behavior from this explanation?
3. **Compute incomprehensibility:**

$$L_{\text{incomprehensible}} = 1 - \frac{\text{Clarity} + \text{Completeness} + \text{Predictability}}{15}$$

4. **Compute alien value:**

$$V_{\text{alien}} = L_{\text{incomprehensible}} \cdot PR_{\text{novel}} \cdot R_{\text{recover}}$$

**Interpretation:**
- $V_{\text{alien}}$ is high only when the law is simultaneously incomprehensible, novel, and recoverable.
- A law that is incomprehensible but doesn't work ($PR_{\text{novel}} \to 0$) gets $V_{\text{alien}} \to 0$.
- A law that is easily explained but novel gets $V_{\text{alien}}$ reduced by the comprehensibility factor.
- A law that is incomprehensible and works but is unrecoverable ($R_{\text{recover}} \to 0$) gets $V_{\text{alien}} \to 0$.

```python
async def compute_human_incomprehensibility(
    law: BornLaw,
    llm_client: Any,
    prompt_template: str = None
) -> dict:
    """
    Uses an LLM to attempt to explain the law, then scores the explanation.
    """
    if prompt_template is None:
        prompt_template = (
            "You are a game AI expert. Explain this game law in one simple sentence "
            "that a non-expert could understand.\n\n"
            "Law name: {name}\n"
            "Law code:\n```\n{code}\n```\n"
            "Behavior description: {behavior}\n\n"
            "Then rate your own explanation on three scales (0-5 each):\n"
            "- Clarity: How understandable is your explanation?\n"
            "- Completeness: Does it capture the actual effect?\n"
            "- Predictability: Could someone predict the law's behavior from this?\n\n"
            "Format your response as JSON: {{'explanation': '...', 'clarity': N, 'completeness': N, 'predictability': N}}"
        )

    prompt = prompt_template.format(
        name=law.name,
        code=law.code_summary,
        behavior=law.behavior_description
    )

    response = await llm_client.generate(prompt)

    try:
        scores = json.loads(response)
        l_incomprehensible = 1.0 - (scores["clarity"] + scores["completeness"] + scores["predictability"]) / 15.0
    except (json.JSONDecodeError, KeyError):
        l_incomprehensible = 0.8  # assume incomprehensible if parsing fails

    return {
        "explanation": scores.get("explanation", "PARSE_ERROR"),
        "clarity": scores.get("clarity", 0),
        "completeness": scores.get("completeness", 0),
        "predictability": scores.get("predictability", 0),
        "l_incomprehensible": l_incomprehensible,
        "explanation_quality": "high" if l_incomprehensible < 0.3 else "medium" if l_incomprehensible < 0.6 else "low"
    }
```

---

### Enhancement 48: Exportable Alien Recipe Cards

**Description:** Born laws that pass the export gate are formatted as **alien recipe cards** — structured markdown documents that make discoveries shareable, auditable, and reproducible. Each recipe card contains all the information needed to understand, reproduce, and evaluate the alien law.

**Recipe card template:**

```markdown
# Alien Recipe {id}: {name}

## Status
**{status}** — Exported on {export_date}

## Provenance
- **Born at step:** {birth_step}
- **Born from method:** {mutation_method}
- **Mode origin:** {mode}
- **Generation:** {generation}

## Parent Laws
{parent_laws_list}

## Mutation History
{mutation_chain}

## Effect
{effect_description}

## Code Summary
```python
{code_summary}
```

## Alienness Assessment
- **A_alien:** {a_alien} ({alienness_level})
- **N_causal:** {n_causal} ({causal_novelty_level})
- **L_incomprehensible:** {l_incomprehensible} ({explanation_quality})
- **LLM Explanation:** "{llm_explanation}"

## Cross-Seed Tournament Results
- **Seeds tested:** {n_seeds}
- **PR_novel:** {pr_novel_mean} ± {pr_novel_std}
- **PR_strict:** {pr_strict_mean} ± {pr_strict_std}
- **A_alien:** {a_alien_mean} ± {a_alien_std}
- **N_robust:** {n_robust_mean} ± {n_robust_std}
- **R_strange:** {r_strange_mean} ± {r_strange_std}
- **L_samsara:** {l_samsara_mean} ± {l_samsara_std}
- **Catastrophic failure rate:** {catastrophic_rate}

## Export Gate Results
{export_gate_checklist}

## Failure Cases
{failure_cases}

## Reproducibility
- **Seed:** {representative_seed}
- **Random state:** {random_state_hash}
- **Trace file:** {trace_link}
- **Video:** {video_link}

## Shareability
This recipe card is self-contained. To reproduce:
1. Load the parent laws: {parent_laws_names}
2. Apply mutations in order: {mutation_steps}
3. Run in {mode} mode with seed {representative_seed}
4. Expected metrics: PR_novel ≈ {pr_novel_mean}, PR_strict ≈ {pr_strict_mean}
```

**Export mechanism:**

```python
def generate_recipe_card(
    law: BornLaw,
    archive_entry: dict,
    tournament_results: dict,
    export_gate: dict,
    incomprehensibility: dict,
    config: dict = None
) -> str:
    """
    Generates a complete alien recipe card as markdown string.
    """
    template = load_template("recipe_card_template.md")

    card = template.format(
        id=archive_entry["archive_id"],
        name=law.name,
        status="EXPORTED" if export_gate["passed"] else "REJECTED",
        export_date=datetime.utcnow().strftime("%Y-%m-%d"),
        birth_step=archive_entry["birth_info"]["step"],
        mutation_method=archive_entry["birth_info"]["method"],
        mode=law.mode,
        generation=law.generation,
        parent_laws_list=format_parent_laws(law.parent_laws),
        mutation_chain=format_mutation_chain(archive_entry["mutation_history"]),
        effect_description=law.behavior_description,
        code_summary=law.code_summary,
        a_alien=tournament_results["a_alien"]["mean"],
        alienness_level=classify_alienness(tournament_results["a_alien"]["mean"]),
        n_causal=tournament_results["n_causal"]["mean"],
        causal_novelty_level=classify_causal_novelty(tournament_results["n_causal"]["mean"]),
        l_incomprehensible=incomprehensibility["l_incomprehensible"],
        explanation_quality=incomprehensibility["explanation_quality"],
        llm_explanation=incomprehensibility["explanation"],
        n_seeds=len(tournament_results["per_seed"]),
        pr_novel_mean=tournament_results["pr_novel"]["mean"],
        pr_novel_std=tournament_results["pr_novel"]["std"],
        pr_strict_mean=tournament_results["pr_strict"]["mean"],
        pr_strict_std=tournament_results["pr_strict"]["std"],
        a_alien_mean=tournament_results["a_alien"]["mean"],
        a_alien_std=tournament_results["a_alien"]["std"],
        n_robust_mean=tournament_results["n_robust"]["mean"],
        n_robust_std=tournament_results["n_robust"]["std"],
        r_strange_mean=tournament_results["r_strange"]["mean"],
        r_strange_std=tournament_results["r_strange"]["std"],
        l_samsara_mean=tournament_results["l_samsara"]["mean"],
        l_samsara_std=tournament_results["l_samsara"]["std"],
        catastrophic_rate=tournament_results["catastrophic_rate"],
        export_gate_checklist=format_export_gate(export_gate),
        failure_cases=format_failure_cases(archive_entry["failure_cases"]),
        representative_seed=tournament_results["per_seed"][0]["seed"],
        random_state_hash=compute_random_state_hash(tournament_results["per_seed"][0]["seed"]),
        trace_link=f"traces/{archive_entry['archive_id']}/",
        video_link=f"videos/{archive_entry['archive_id']}.mp4",
        parent_laws_names=[p["name"] for p in law.parent_laws],
        mutation_steps=[m["method"] for m in archive_entry["mutation_history"]]
    )

    return card
```

---

## 10. Complete Demo Script Outline

```python
#!/usr/bin/env python3
"""
demo_06_alien_novelty_forge.py — Frame 6: Alien Novelty Forge Demo

This demo validates:
1. The Forge can birth novel laws through mutation and composition.
2. Born laws are evaluated for alienness, causal novelty, and recoverability.
3. Cross-seed tournaments ensure robustness.
4. The export gate admits only truly alien, robust, recoverable laws.
5. Recipe cards make discoveries shareable.
6. PR_novel > PR_strict for exported laws (proving genuine novelty).

Usage:
    python demo_06_alien_novelty_forge.py --generations 20 --seeds 15 --export
    python demo_06_alien_novelty_forge.py --law pressure_memory_field --eval-only
"""

import argparse
import json
import csv
import numpy as np
from pathlib import Path
from datetime import datetime

from novelty_metrics import (
    compute_alienness, compute_causal_novelty, compute_recoverable_strangeness,
    compute_robust_novelty, compute_samsara_penalty, compute_pr_novel
)
from law_forge import LawForge, MutationOperator, NoveltySearchNSGA2
from alienness_playground import AlienPlayground
from anti_samsara import AntiSamsaraDetector

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generations", type=int, default=20)
    parser.add_argument("--seeds", type=int, default=15)
    parser.add_argument("--export", action="store_true", help="Export laws that pass gate")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()

    # Initialize Forge
    forge = LawForge(config={
        "population_size": 50,
        "n_generations": args.generations,
        "n_seeds_tournament": args.seeds,
        "validation_horizon": 40
    })

    # Load human prior for alienness computation
    human_prior = load_human_prior("human_behavior_reference.json")

    # Initialize playground
    playground = AlienPlayground(config={"max_steps": 200})

    # Initialize samsara detector
    samsara_detector = AntiSamsaraDetector()

    # Run Forge
    all_novelty_runs = []
    exported_recipes = []
    full_archive = []

    for gen in range(args.generations):
        print(f"Generation {gen + 1}/{args.generations}")

        # Generate new candidates
        candidates = forge.generate_candidates()

        for candidate in candidates:
            # Run cross-seed tournament
            tournament_results = forge.run_tournament(
                candidate,
                playground,
                n_seeds=args.seeds,
                n_steps=200
            )

            # Compute aggregate metrics
            metrics = compute_aggregate_metrics(tournament_results, human_prior)

            # Check export gate
            export_gate = check_export_gate(candidate, metrics)

            # Generate incomprehensibility score (if LLM available)
            if HAS_LLM:
                incomprehensibility = await compute_human_incomprehensibility(candidate, LLM_CLIENT)
            else:
                incomprehensibility = {"l_incomprehensible": 0.5, "explanation": "LLM not available"}

            # Log
            run_entry = {
                "law_name": candidate.name,
                "generation": gen,
                **metrics,
                "export_gate_passed": export_gate["passed"],
                "l_incomprehensible": incomprehensibility["l_incomprehensible"]
            }
            all_novelty_runs.append(run_entry)
            full_archive.append(archive_entry(candidate, metrics, export_gate, incomprehensibility))

            # Export if passes gate
            if export_gate["passed"] and args.export:
                recipe = generate_recipe_card(candidate, full_archive[-1], tournament_results, export_gate, incomprehensibility)
                exported_recipes.append(recipe)
                print(f"  ✓ EXPORTED: {candidate.name}")

    # Write outputs
    write_novelty_csv(all_novelty_runs, Path(args.output_dir) / "novelty_runs.csv")
    write_recipes(exported_recipes, Path(args.output_dir) / "alien_recipes.jsonl")
    write_archive(full_archive, Path(args.output_dir) / "novelty_archive.jsonl")
    generate_report(all_novelty_runs, exported_recipes, full_archive, Path(args.output_dir) / "report_alien_novelty_forge.md")

    # Print summary
    print(f"\n=== FORGE SUMMARY ===")
    print(f"Laws generated: {len(all_novelty_runs)}")
    print(f"Laws exported: {len(exported_recipes)}")
    if exported_recipes:
        print(f"Mean PR_novel (exported): {np.mean([r['pr_novel'] for r in get_export_metrics(exported_recipes)]):.3f}")
        print(f"Mean PR_strict (exported): {np.mean([r['pr_strict'] for r in get_export_metrics(exported_recipes)]):.3f}")
        print(f"Mean A_alien (exported): {np.mean([r['a_alien'] for r in get_export_metrics(exported_recipes)]):.3f}")

if __name__ == "__main__":
    main()
```

---

## 11. Summary

Frame 6 introduces the Alien Novelty Forge — the RGPUF system's engine for inventing genuinely new, stable, and recoverable behaviors. The Forge:

- **Generates** novel laws through 8 mutation operators (reparameterize, swap_term, add_noise, compose, abstract, invert, rewire_trigger, change_sensor).
- **Measures alienness** using histogram-based divergence from human behavioral prior ($A_{\text{alien}}$).
- **Quantifies causal novelty** through graph difference analysis ($N_{\text{causal}}$).
- **Ensures recoverability** by requiring $R_{\text{recover}} > \theta$ and $PR_{\text{strict}} > \theta_{\text{safety}}$.
- **Detects and penalizes samsara** through multi-scale cycle detection ($L_{\text{samsara}}$).
- **Tests robustness** across 10-20 seeds ($N_{\text{robust}}$).
- **Exports** only laws that pass a strict multi-condition gate.
- **Makes discoveries shareable** through alien recipe cards.

The core thesis: **recoverable alienness is possible.** The system can invent laws no human would design, verify they are stable and survivable, and share them as reusable discoveries. This is the frontier of the RGPUF project — moving from system maintenance (Frames 4-5) to system invention (Frame 6).
