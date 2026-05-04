# RGPUF Lab v4 Blueprint

## **Two-Script Architecture: Reusable Core + Next-Level Demo**

The next notch up should **not** be one giant script. v3 already showed the danger: the demo, core engine, optimizer, report writer, HDC logic, mode runners, and CLI all started collapsing into one file. v4 should split the project into exactly two scripts:

```text
rgpuf_core.py       # reusable simulation engine, laws, metrics, HDC, agents
rgpuf_lab_v4.py     # demo/orchestrator: campaigns, modes, reports, visual outputs
```

The current `rgpuf_lab.py` already contains the foundations that should move into the core: six simulation families, reusable vector math, resource reservoirs, motion kernels, graph pressure diffusion, Freescape zones, Colony cells, and metric/export infrastructure.  The law registry is also already separated conceptually into motion, topology, resource, spatial, colony, and semantic families, which makes it ideal for extraction into `rgpuf_core.py`. 

The new demo script should be **thin, experimental, and dramatic**.

---

# 1. v4 Thesis

```text
v2 proved minimum-law simulation.
v3 proved self-diagnosis was possible.
v4 proves reusable law kernels can generate, audit, optimize, and compare entire retro-physics “micro-worlds” from one shared core.
```

The core should become a mini-engine.

The demo should become a research experiment.

```text
rgpuf_core.py = law engine
rgpuf_lab_v4.py = experiment runner
```

---

# 2. The Two Scripts

## Script 1 — `rgpuf_core.py`

Purpose:

```text
Reusable RGPUF kernel library.
No big CLI.
No long terminal show.
No mode-specific report prose.
Just clean primitives, laws, metrics, agents, HDC, and simulation APIs.
```

It should contain:

```text
1. Math primitives
2. Bodies and world objects
3. Resource reservoirs
4. Law registry
5. Physics laws
6. Prediction and agency metrics
7. HDC semantic engine
8. Dynamic law compiler
9. Agent policies
10. Mode state constructors
11. Step functions
12. Telemetry dataclasses
13. Export helpers
```

## Script 2 — `rgpuf_lab_v4.py`

Purpose:

```text
Research/demo runner using rgpuf_core.py.
Runs campaigns.
Compares v2/v3/v4-style scoring.
Finds weak modes.
Optimizes parameters.
Produces markdown and CSV reports.
```

It should contain:

```text
1. CLI
2. Scenario presets
3. Campaign orchestration
4. Audit runs
5. Optimizer runs
6. Stress tests
7. Comparison tables
8. Markdown report generation
9. Optional ASCII/BrailleStream terminal visual summaries
```

---

# 3. Why This Split Matters

v3’s main bug was conceptual: the **registry’s active flags and the actual mode law set diverged**. In the output you described, every mode got nearly the same law cost because the compiler summed the global active registry instead of the executed per-mode laws. v4 must enforce:

```text
global registry ≠ active runtime law stack
```

So the core must introduce a true runtime object:

```python
@dataclass
class LawStack:
    names: list[str]

    def cost(self, registry) -> float:
        return sum(registry[name].cost for name in self.names)

    def falsifiability(self, registry) -> float:
        ...
```

This alone fixes the biggest v3 metric failure.

---

# 4. v4 Design Target

v4 should answer this automatically:

```text
Given a mode, seed, and agent policy:
1. What laws actually executed?
2. Which laws helped?
3. Which laws were dead weight?
4. Which failure boundary was closest?
5. Which repair gives the highest PR gain per law-cost added?
```

Not just:

```text
PR = 0.365
```

But:

```text
Colony improved because wall-follow increased coverage from 2% to 31%.
Teleport law did not execute.
Bresenham LOS had negative contribution under this seed.
Recommended stack: cell_occupancy + quantized_rotation + wall_follow + suit_energy.
```

---

# 5. File 1 Blueprint: `rgpuf_core.py`

## 5.1 Header

```python
#!/usr/bin/env python3
"""
rgpuf_core.py
==============

Reusable core for the Retro Game Physics Unified Framework.

Contains:
- compact retro-physics laws
- resource thermodynamics
- topology and cell-world logic
- Freescape-style zone/cuboid physics
- adaptive agents
- law-stack metrics
- HDC semantic drift engine
- audit/optimization primitives

This file is importable and should not run full demos by default.
"""
```

---

## 5.2 Core Layout

```text
rgpuf_core.py

1. constants
2. math primitives
3. dataclasses
4. law registry
5. LawStack runtime object
6. physics laws
7. world generators
8. agent policies
9. prediction model
10. metrics engine
11. HDC engine
12. DLASc compiler
13. mode state constructors
14. per-mode step functions
15. simulation runner
16. audit and optimizer helpers
17. export helpers
```

---

# 6. `rgpuf_core.py` Required Dataclasses

## 6.1 `Vec2`, `Vec3`

Reuse from v3.

Add:

```python
def as_tuple(self) -> tuple[float, float]
def quantized(self, scale: float = 1.0) -> tuple[int, int]
```

For metrics and state signatures.

---

## 6.2 `Body`, `Body3`

Keep:

```text
position
velocity
heading_byte
zone_id
state
```

Add:

```python
last_pos: Vec2 | Vec3
collision_count: int
wrap_count: int
teleport_count: int
```

Why:

```text
Agency and ambiguity need actual event counters, not guesses.
```

---

## 6.3 `ResourceReservoir`

Keep the universal equation:

```text
dR/dt = source - sink - leak*R + noise
```

The current core already uses this kind of universal reservoir for fuel, heat, pressure, oxygen, shield, and suit-style resources. 

Add:

```python
def normalized(self) -> float
def failure_margin(self) -> float
def is_critical(self) -> bool
```

---

## 6.4 `LawTerm`

```python
@dataclass
class LawTerm:
    name: str
    family: str
    cost: float
    verified: str
    preconditions: tuple[str, ...] = ()
    effects: tuple[str, ...] = ()
    trust: float = 1.0
```

Important: remove `active` from global laws.

Global laws should describe **available laws**, not runtime active laws.

---

## 6.5 `LawStack`

This is the v4 keystone.

```python
@dataclass
class LawStack:
    names: list[str]

    def has(self, name: str) -> bool:
        return name in self.names

    def add(self, name: str) -> None:
        if name not in self.names:
            self.names.append(name)

    def remove(self, name: str) -> None:
        if name in self.names:
            self.names.remove(name)

    def cost(self, registry: dict[str, LawTerm]) -> float:
        return sum(registry[n].cost for n in self.names if n in registry)

    def falsifiability(self, registry: dict[str, LawTerm]) -> float:
        if not self.names:
            return 0.0
        weights = {"historical": 1.0, "equivalent": 0.7, "speculative": 0.3}
        return sum(weights.get(registry[n].verified, 0.3) * registry[n].trust
                   for n in self.names if n in registry) / len(self.names)
```

This directly prevents the v3 bug where the whole registry inflated every mode’s law cost.

---

## 6.6 `AgentStats`

Separate **action success** from **goal success**.

```python
@dataclass
class AgentStats:
    attempted: int = 0
    moved: int = 0
    useful: int = 0
    blocked: int = 0
    collisions: int = 0
    teleports: int = 0
    failures: int = 0

    @property
    def action_agency(self) -> float:
        return self.moved / max(self.attempted, 1)

    @property
    def goal_agency(self) -> float:
        return self.useful / max(self.attempted, 1)
```

v3’s pressure mode got false agency because actions were counted as successful even if pressure kept rising. v4 fixes this by distinguishing:

```text
action_agency = did the action execute?
goal_agency   = did the action improve the objective?
```

---

## 6.7 `Telemetry`

```python
@dataclass
class Telemetry:
    step: int
    mode: str
    seed: int
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    speed: float = 0.0

    fuel: float = 0.0
    heat: float = 0.0
    pressure: float = 0.0
    suit: float = 0.0
    shield: float = 0.0

    criticality: float = 0.0
    pr: float = 0.0
    pr_norm: float = 0.0
    mle: float = 0.0
    law_cost: float = 0.0
    law_count: int = 0
    falsifiability: float = 0.0
    semantic_entropy: float = 0.0
    prediction_error: float = 0.0
    action_agency: float = 0.0
    goal_agency: float = 0.0
    coverage: float = 0.0

    godel_tokens: int = 0
    semantic_drift: float = 0.0
    delta_ep_min: float = 0.0

    active_laws: str = ""
    events: str = ""
    failure_state: str = "active"
```

---

# 7. Law Registry v4

Use families.

```python
LAW_REGISTRY = {
    "thrust_gravity_drag": LawTerm(
        "thrust_gravity_drag", "motion", 1.0, "equivalent",
        effects=("motion", "control")
    ),
    "central_gravity_well": LawTerm(
        "central_gravity_well", "motion", 1.2, "historical",
        effects=("orbital_motion",)
    ),
    "toroidal_wrap": LawTerm(
        "toroidal_wrap", "topology", 0.5, "historical",
        preconditions=("wrap_enabled",),
        effects=("boundary_continuity",)
    ),
    "graph_pressure_diffusion": LawTerm(
        "graph_pressure_diffusion", "resource", 1.5, "equivalent",
        preconditions=("zone_graph",),
        effects=("pressure_equilibrium",)
    ),
    "hysteresis_failure": LawTerm(
        "hysteresis_failure", "failure", 1.5, "equivalent",
        preconditions=("critical_resource",),
        effects=("failure_memory",)
    ),
    "wall_following_agent": LawTerm(
        "wall_following_agent", "agent", 1.0, "equivalent",
        preconditions=("cell_grid", "blocked_actions_high"),
        effects=("coverage_increase", "agency_increase")
    ),
}
```

Do **not** mark them active here.

Mode constructors create runtime stacks.

---

# 8. Mode Constructors in Core

Each mode gets:

```python
def make_lander(seed: int, config: SimConfig) -> SimState
def make_asteroids(seed: int, config: SimConfig) -> SimState
def make_pressure(seed: int, config: SimConfig) -> SimState
def make_freescape(seed: int, config: SimConfig) -> SimState
def make_colony(seed: int, config: SimConfig) -> SimState
def make_semantic(seed: int, config: SimConfig) -> SimState
```

## `SimState`

```python
@dataclass
class SimState:
    mode: str
    seed: int
    step: int
    config: SimConfig
    law_stack: LawStack
    agent_stats: AgentStats
    hdc: HDCEngine
    history: list[Telemetry]

    body: Body | None = None
    body3: Body3 | None = None
    resources: dict[str, ResourceReservoir] = field(default_factory=dict)
    zones: list[Zone] = field(default_factory=list)
    cuboids: list[Cuboid] = field(default_factory=list)
    grid: dict[tuple[int, int], Cell] = field(default_factory=dict)
    visited_cells: set[tuple[int, int]] = field(default_factory=set)

    extra: dict[str, Any] = field(default_factory=dict)
```

This is what allows `rgpuf_lab_v4.py` to run a mode step-by-step without rewriting mode logic.

---

# 9. Step API in Core

```python
def step_sim(state: SimState) -> Telemetry:
    if state.mode == "lander":
        return step_lander(state)
    if state.mode == "asteroids":
        return step_asteroids(state)
    ...
```

Also expose:

```python
def run_sim(mode: str, seed: int, steps: int, config: SimConfig) -> list[Telemetry]:
    state = make_state(mode, seed, config)
    out = []
    for _ in range(steps + 1):
        out.append(step_sim(state))
    return out
```

This makes the demo script tiny.

---

# 10. SimConfig

```python
@dataclass
class SimConfig:
    dt: float = 0.12
    adaptive: bool = False
    agent_policy: str = "naive"
    integrator: str = "euler"
    wall_density: float = 0.45
    teleport_probability: float = 0.04
    pressure_source: float = 1.15
    drill_power: float = 8.0
    hdc_dim: int = 1024
    anomaly_threshold: float = 0.25
    law_cost_scale: str = "normalized"
    stress: bool = False
    max_steps: int = 240
```

---

# 11. PR Formula v4

v4 should compute both:

```text
raw PR
normalized PR
```

## Raw PR

Useful for internal comparisons:

```text
PR_raw = (state_density × goal_agency × falsifiability × compression_gain)
         / (law_cost × (1 + ambiguity + semantic_entropy + prediction_error))
```

## Normalized PR

Comparable to v2/v3 outputs:

```text
PR_norm = PR_raw × law_count_mean_cost × PR_SCALE
```

Practical:

```python
def playable_reality_v4(
    state_density: float,
    goal_agency: float,
    falsifiability: float,
    compression_gain: float,
    law_stack: LawStack,
    registry: dict[str, LawTerm],
    ambiguity: float,
    semantic_entropy: float,
    prediction_error: float,
) -> tuple[float, float]:
    law_cost = law_stack.cost(registry)
    law_count = max(len(law_stack.names), 1)
    mean_cost = law_cost / law_count

    raw = (
        state_density
        * goal_agency
        * falsifiability
        * compression_gain
    ) / max(law_cost * (1 + ambiguity + semantic_entropy + prediction_error), 1e-9)

    normalized = raw * mean_cost * law_count
    return raw, normalized
```

This keeps law cost meaningful without crushing every PR value.

---

# 12. Agency v4: Mode-Specific Goal Agency

## Lander

```text
useful = vertical_speed_error decreased OR distance_to_pad decreased
```

```python
goal_agency = useful_actions / attempted_actions
```

## Asteroids

```text
useful = thrust increased orbital control OR avoided gravity capture OR improved target alignment
```

Add:

```python
angular_momentum_error
energy_drift
wrap_count
```

## Pressure

```text
useful = drilling reduced pressure slope
```

This fixes v3’s false perfect agency.

## Freescape

```text
useful = position changed meaningfully OR zone advanced OR collision recovered
```

## Colony

```text
useful = new cell visited OR stuck counter decreased OR teleporter discovered
```

Not merely “movement happened.”

---

# 13. Prediction Model v4

v4 should have a tiny predictor object.

```python
@dataclass
class SignaturePredictor:
    last: tuple | None = None
    transition_counts: Counter[tuple[tuple, tuple]] = field(default_factory=Counter)

    def predict(self, current: tuple) -> tuple | None:
        candidates = {
            nxt: count
            for (cur, nxt), count in self.transition_counts.items()
            if cur == current
        }
        if not candidates:
            return None
        return max(candidates, key=candidates.get)

    def update(self, current: tuple, actual_next: tuple) -> float:
        pred = self.predict(current)
        self.transition_counts[(current, actual_next)] += 1
        if pred is None:
            return 0.5
        return 0.0 if pred == actual_next else 1.0
```

This is still retro-simple but much better than distance-only prediction error.

---

# 14. HDC v4: Make Anomalies Functional

In v3, anomalies were cosmetic.

v4:

```text
Gödel token = prediction failure credit.
Tokens can be spent by DLASc to test a candidate repair law.
```

Example:

```python
if prediction_error > threshold:
    hdc.godel_tokens += 1

if hdc.godel_tokens >= 2 and context["stuck_loop"]:
    law_stack.add("wall_following_agent")
    hdc.godel_tokens -= 2
```

Now anomalies do something.

```text
Anomaly → token → repair test → law contribution measured
```

That is the clean mechanism.

---

# 15. DLASc v4

DLASc must operate on `LawStack`, not global registry flags.

```python
class DLASc:
    def __init__(self, registry):
        self.registry = registry

    def propose(self, state: SimState, telemetry: Telemetry) -> list[str]:
        ...

    def apply(self, state: SimState, proposals: list[str]) -> list[str]:
        for law in proposals:
            state.law_stack.add(law)
```

## Activation triggers

```text
blocked_actions_high → wall_following_agent
criticality_high → risk_policy
landing_error_high → pid_controller
energy_drift_high → verlet_integrator
dead_law_detected → remove law
prediction_error_high → predictor_repair
```

## Deactivation triggers

```text
law never executed
law contribution < 0
law duplicates another law under EP check
law increases entropy without increasing agency
```

---

# 16. Law Contribution v4

Run cheap ablation on short windows.

```python
def estimate_law_contribution(mode, seed, config, law, window=80):
    baseline = run_sim(mode, seed, window, config)
    patched_config = config.with_disabled_law(law)
    ablated = run_sim(mode, seed, window, patched_config)
    return final_pr(baseline) - final_pr(ablated)
```

Store:

```python
law_contribution[law] = rolling_average(...)
```

Then DLASc can actually deactivate laws.

---

# 17. File 2 Blueprint: `rgpuf_lab_v4.py`

## 17.1 Header

```python
#!/usr/bin/env python3
"""
rgpuf_lab_v4.py
================

Next-level RGPUF demo using rgpuf_core.py.

Runs campaign experiments:
- baseline vs adaptive
- per-mode audit
- law contribution analysis
- stress/failure envelope
- optimizer search
- semantic campaign report

This file should stay thin. All reusable mechanics live in rgpuf_core.py.
"""
```

---

## 17.2 Imports

```python
from rgpuf_core import (
    SimConfig,
    run_sim,
    make_state,
    step_sim,
    audit_mode,
    optimize_mode,
    stress_mode,
    write_csv,
    write_json,
    write_markdown_report,
    BASE_MODES,
)
```

---

# 18. v4 Demo Modes

The demo script should support:

```bash
python rgpuf_lab_v4.py --campaign baseline
python rgpuf_lab_v4.py --campaign adaptive
python rgpuf_lab_v4.py --campaign stress
python rgpuf_lab_v4.py --campaign audit
python rgpuf_lab_v4.py --campaign optimize
python rgpuf_lab_v4.py --campaign compare
```

## Campaign 1 — `baseline`

Runs all modes with minimal static stacks.

Purpose:

```text
Reference behavior.
```

## Campaign 2 — `adaptive`

Runs all modes with DLASc + HDC tokens enabled.

Purpose:

```text
Show self-repair.
```

## Campaign 3 — `stress`

Runs until failure or max steps.

Purpose:

```text
Measure TTF and failure envelope.
```

## Campaign 4 — `audit`

Computes law contribution and dead laws.

Purpose:

```text
Identify bloat.
```

## Campaign 5 — `optimize`

Grid search over parameters.

Purpose:

```text
Find best PR_norm per law cost.
```

## Campaign 6 — `compare`

Runs:

```text
baseline vs adaptive vs optimized
```

Purpose:

```text
Prove v4 improved over v3.
```

---

# 19. v4 New Demo Concept: “Micro-World Forge”

This is the “take it up a notch” layer.

Instead of just running modes, v4 should generate a **micro-world recipe**.

```text
MicroWorld = mode + law_stack + agent_policy + failure_goal + topology
```

Example:

```json
{
  "name": "Colony Escape",
  "mode": "colony",
  "law_stack": [
    "cell_occupancy",
    "quantized_rotation",
    "power_suit_energy",
    "wall_following_agent",
    "semantic_entropy",
    "playable_reality"
  ],
  "agent_policy": "wall_follow",
  "goal": "maximize_coverage",
  "failure": "suit_depletion",
  "topology": "cell_torus"
}
```

The demo should produce these recipes automatically.

Output:

```text
BEST MICRO-WORLD RECIPE
Name: Colony Escape
Seed: 42
Laws: 6
LawCost: 7.2
PR_norm: 0.741
Coverage: 0.34
Failure Boundary: suit_depletion at T=812
Dead Laws Removed: teleport_transform, bresenham_los
```

---

# 20. v4 CLI

```bash
# baseline all modes
python rgpuf_lab_v4.py --campaign baseline --steps 240 --seed 42

# adaptive comparison
python rgpuf_lab_v4.py --campaign compare --steps 240 --seed 42

# audit colony
python rgpuf_lab_v4.py --campaign audit --mode colony --steps 240

# stress pressure
python rgpuf_lab_v4.py --campaign stress --mode pressure --max-steps 2000

# optimize Colony parameters
python rgpuf_lab_v4.py --campaign optimize --mode colony --episodes 50

# generate markdown report
python rgpuf_lab_v4.py --campaign compare --csv telemetry.csv --json summary.json --report report.md
```

---

# 21. v4 Output Target

## Comparison table

```text
RGPUF Lab v4 — Micro-World Forge
core: rgpuf_core.py | demo: rgpuf_lab_v4.py

MODE        PR_BASE  PR_ADAPT  PR_OPT  ΔOPT   AGENCY  COVER  LAW_COST  DEAD  TTF
lander      0.522    0.641     0.702  +0.180  0.81    0.42   5.2       1     390
asteroids   0.648    0.665     0.688  +0.040  0.57    0.88   5.0       0     ∞
pressure    0.407    0.532     0.601  +0.194  0.68    0.51   6.1       1     744
freescape   0.654    0.681     0.718  +0.064  0.64    0.38   7.0       2     880
colony      0.312    0.588     0.742  +0.430  0.79    0.34   7.2       3     812
semantic    0.123    0.392     0.501  +0.378  0.62    0.00   6.4       4     ∞
```

## Law contribution table

```text
LAW CONTRIBUTION — colony optimized

law                     contribution   executed   verdict
cell_occupancy          +0.210         yes        keep
wall_following_agent    +0.286         yes        keep
power_suit_energy       +0.074         yes        keep
quantized_rotation      +0.041         yes        keep
teleport_transform      +0.000         no         remove
bresenham_los           -0.028         yes        remove unless hostile AI active
semantic_entropy        +0.019         yes        keep
```

## Automatic diagnosis

```text
DIAGNOSIS — colony

Problem in v3:
- PR was crushed by global registry law cost.
- Agency was inflated by action success instead of goal success.
- Cell movement improved but coverage remained low.
- Teleport law was present but rarely executed.

v4 repair:
- LawStack now counts only executed mode laws.
- Goal agency uses new-cell coverage.
- HDC anomalies buy repair trials.
- DLASc removed dead laws after contribution test.

Result:
PR_norm: 0.312 → 0.742
LawCost: 23.7 → 7.2
Coverage: 0.02 → 0.34
Dead laws removed: 3
```

---

# 22. Core Equations for v4

## 1. Runtime law cost

```text
C_L = Σ cost(l), for l ∈ LawStack_runtime
```

## 2. Goal agency

```text
A_goal = useful_actions / attempted_actions
```

## 3. State coverage

```text
Ω = unique_state_signatures / total_steps
```

## 4. PR normalized

```text
PR_norm = [(Ω × A_goal × F × C_comp) / (C_L × (1 + E_pred + S_ent))] × C_L_mean × N_laws
```

## 5. Law contribution

```text
ΔPR_l = PR_full - PR_without_l
```

## 6. Dead law score

```text
D_l = I(executed_l = 0) + I(ΔPR_l ≤ 0) + I(EP_l < ε)
```

## 7. HDC anomaly token

```text
G_t = G_{t-1} + I(E_pred > θ_pred or drift > θ_drift)
```

## 8. Repair trial condition

```text
Try(l) iff G_t ≥ token_cost(l) and preconditions(l)
```

## 9. Pressure recovery score

```text
R_pressure = max(0, P_peak - P_final) / max(P_peak - P_initial, ε)
```

## 10. Lander solver score

```text
S_land = I(landed) × fuel_remaining × exp(-|v_y| - |x - x_pad| / pad_width)
```

---

# 23. What to Reuse from Existing Core

From current `rgpuf_lab.py`, move these into `rgpuf_core.py`:

```text
Vec2 / Vec3
Body / Body3
ResourceReservoir
Zone / Cuboid / Cell
LawTerm concept
LAW_REGISTRY
arcade_motion_step
motion_step_3d
central_gravity_well
teleport_transform
bresenham_los
graph_pressure_diffusion
hysteresis_failure
playable_reality_score family
minimum_law_efficiency
compression_ratio
falsifiability_score
semantic_entropy_metric
Metrics/Telemetry structure
CSV/JSON helpers
```

These parts are already established in the v2 lab: motion and topology are represented through `arcade_motion_step`, toroidal wrap, quantized rotation, and central gravity; pressure mode uses a graph of zones and resource reservoirs; Colony mode uses cells, suit energy, LOS, and cell movement; Freescape mode uses cuboids, hydraulic height, pressure, and zones.   

---

# 24. v4 Development Phases

## Phase 1 — Extract Core

Create:

```text
rgpuf_core.py
rgpuf_lab_v4.py
```

Move all reusable classes and laws into core.

`rgpuf_lab_v4.py` should be less than 400 lines if possible.

---

## Phase 2 — Fix Runtime Law Cost

Implement:

```text
LawStack
mode-specific stack
executed-law tracking
law cost based on runtime stack only
```

This is the most important v4 fix.

---

## Phase 3 — Fix Agency

Implement:

```text
action_agency
goal_agency
mode-specific useful action criteria
coverage metric
pressure recovery metric
lander target metric
```

---

## Phase 4 — Make HDC Functional

Implement:

```text
prediction error → Gödel token
Gödel token → repair trial
repair trial → contribution score
contribution score → keep/remove
```

---

## Phase 5 — Add Campaign System

In `rgpuf_lab_v4.py`, implement:

```text
baseline
adaptive
stress
audit
optimize
compare
```

---

## Phase 6 — Micro-World Forge

Implement:

```text
recipe extraction
best law stack
best agent policy
best failure boundary
export as JSON
```

Output:

```text
recipes/best_colony_escape.json
recipes/best_pressure_recovery.json
```

---

# 25. Minimal File Skeletons

## `rgpuf_core.py`

```python
#!/usr/bin/env python3
from __future__ import annotations

import csv, json, math, random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Literal

TAU = math.tau

# constants
# Vec2 / Vec3
# Body / Body3
# ResourceReservoir
# Zone / Cuboid / Cell
# LawTerm / LawStack
# AgentStats / SimConfig / SimState / Telemetry
# LAW_REGISTRY
# physics laws
# world generators
# agent policies
# predictor
# HDC
# DLASc
# mode constructors
# step functions
# run_sim
# audit helpers
# optimize helpers
# export helpers
```

## `rgpuf_lab_v4.py`

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse

from rgpuf_core import (
    BASE_MODES,
    SimConfig,
    run_sim,
    run_campaign_baseline,
    run_campaign_adaptive,
    run_campaign_compare,
    run_campaign_stress,
    run_campaign_audit,
    run_campaign_optimize,
    write_csv,
    write_json,
    write_markdown_report,
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", default="compare",
        choices=["baseline", "adaptive", "stress", "audit", "optimize", "compare"])
    parser.add_argument("--mode", default="colony")
    parser.add_argument("--steps", type=int, default=240)
    parser.add_argument("--max-steps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--csv")
    parser.add_argument("--json")
    parser.add_argument("--report")
    args = parser.parse_args()

    config = SimConfig(max_steps=args.steps)

    if args.campaign == "baseline":
        results = run_campaign_baseline(args.seed, args.steps, config)
    elif args.campaign == "adaptive":
        results = run_campaign_adaptive(args.seed, args.steps, config)
    elif args.campaign == "stress":
        results = run_campaign_stress(args.mode, args.seed, args.max_steps, config)
    elif args.campaign == "audit":
        results = run_campaign_audit(args.mode, args.seed, args.steps, config)
    elif args.campaign == "optimize":
        results = run_campaign_optimize(args.mode, args.seed, args.episodes, config)
    else:
        results = run_campaign_compare(args.seed, args.steps, config)

    print_results(results)

    if args.csv:
        write_csv(results.telemetry, args.csv)
    if args.json:
        write_json(results.summary, args.json)
    if args.report:
        write_markdown_report(results, args.report)

if __name__ == "__main__":
    main()
```

---

# 26. Final v4 Target

The v4 demo should prove:

```text
The engine is no longer just measuring law stacks.
It is forging law stacks.
```

Final names:

```text
rgpuf_core.py
rgpuf_lab_v4.py
```

Final project title:

```text
RGPUF Lab v4 — Micro-World Forge
```

Final one-line purpose:

```text
A reusable retro-physics core plus a campaign runner that discovers the smallest law stack capable of producing the richest, most stable playable micro-world.
```
