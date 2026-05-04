# RGPUF Lab v3 Blueprint

## **Adaptive Minimum-Law Retro Physics Lab**

The next demo should be called:

```text
rgpuf_lab_v3.py
```

Subtitle:

```text
Adaptive Minimum-Law Retro Physics Lab
```

Core purpose:

```text
v2 proved that small law stacks can generate diverse retro-physics worlds.
v3 should prove that the simulator can diagnose, adapt, falsify, and improve its own law stack.
```

The existing `rgpuf_lab.py` already has the right skeleton: six modes, a law registry, metrics, CSV/JSON output, resource reservoirs, motion kernels, graph pressure diffusion, Freescape zones, Colony cells, and a static semantic mode. 

v3 should evolve it into a **self-auditing law optimizer**.

---

# 1. v3 Thesis

```text
RGPUF Lab v3 demonstrates that playable retro physics can be optimized by dynamically selecting the smallest active law stack that maximizes agency, compression, falsifiability, and critical tension while minimizing semantic entropy.
```

In simpler terms:

```text
v2 = compare law stacks
v3 = repair and optimize law stacks while running
```

---

# 2. Main New Features

v3 should add five major systems:

```text
1. Dynamic Law Activation
2. Adaptive Agent Scripts
3. Law-Weighted PR Formula
4. Failure Boundary Testing
5. GhostMesh48-HDC Semantic Optimizer
```

The big win is that the script should no longer just report:

```text
freescape PR = 0.654
colony PR = 0.312
```

It should explain:

```text
Colony PR is low because movement agency collapsed after repeated wall-block events.
Recommended patch: activate wall_following_agent, reduce wall density, increase teleport visibility.
Predicted PR improvement: +0.18
```

---

# 3. New Script Name and Modes

## Filename

```text
rgpuf_lab_v3.py
```

## CLI

```bash
python rgpuf_lab_v3.py --all --steps 240 --seed 42
python rgpuf_lab_v3.py --mode colony --adaptive --steps 240
python rgpuf_lab_v3.py --stress pressure --until-failure
python rgpuf_lab_v3.py --semantic-optimize --episodes 30
python rgpuf_lab_v3.py --all --csv telemetry.csv --json summary.json --report report.md
```

## Modes

Keep the six existing modes:

```text
lander
asteroids
pressure
freescape
colony
semantic
```

Add three meta-modes:

```text
stress
optimizer
audit
```

Final mode list:

```python
Mode = Literal[
    "lander",
    "asteroids",
    "pressure",
    "freescape",
    "colony",
    "semantic",
    "stress",
    "optimizer",
    "audit",
]
```

---

# 4. v3 Architecture

Current v2 architecture is:

```text
Mode runner → Metrics → comparison table
```

v3 architecture should become:

```text
Mode runner
  → live telemetry
  → law contribution analysis
  → adaptive controller
  → semantic optimizer
  → falsification update
  → repair suggestion
  → comparison table
```

Full flow:

```text
initialize mode
initialize active law stack
initialize agent policy
for each step:
    observe state
    compute prediction error
    activate/deactivate eligible laws
    run physics
    update resources
    update semantic metrics
    update law trust score
    update agent policy
    log telemetry
after run:
    compute per-law contribution
    compute failure envelope
    output diagnosis
```

---

# 5. Fixes Required Before New Features

These should be treated as v3 blockers.

## Fix 1 — Use Law Cost, Not Law Count

Current PR behaves like:

```python
PR = (state_density * agency) / (law_count * (1 + ambiguity))
```

v3 should use weighted law cost:

```python
law_cost = sum(LAW_REGISTRY[name].cost for name in active_laws)
PR = (state_density * agency * falsifiability) / (law_cost * (1 + ambiguity + semantic_entropy))
```

Better formula:

```text
PR_v3 = (D_state × A_player × F_law × C_compression)
        /
        (C_law × (1 + B_ambiguity + S_entropy + E_error))
```

Where:

```text
D_state        = measured state diversity
A_player       = measured agency, not hardcoded
F_law          = falsifiability score
C_compression  = normalized compression gain
C_law          = active law cost
B_ambiguity    = prediction ambiguity
S_entropy      = semantic entropy
E_error        = model prediction error
```

This makes PR harder to game.

---

## Fix 2 — Measure State Density

Replace guessed constants like:

```python
state_density = 7.0
```

With:

```python
state_density = unique_state_bins / total_possible_bins
```

Practical implementation:

```python
def state_signature(metrics):
    return (
        round(metrics.x, 1),
        round(metrics.y, 1),
        round(metrics.z, 1),
        round(metrics.speed, 1),
        round(metrics.criticality, 2),
        metrics.zone_id,
        metrics.heading_byte // 16,
        metrics.cell_pos,
    )
```

Then:

```python
state_density = len(unique_signatures) / max(step + 1, 1)
```

This directly fixes the “state density is estimated” problem.

---

## Fix 3 — Measure Agency

Agency should not be a fixed mode scalar.

v3 agency should come from:

```text
successful actions / attempted actions
```

For example:

```python
agency = successful_transitions / max(attempted_transitions, 1)
```

Mode-specific examples:

```text
lander:
  agency = controlled_velocity_reduction / fuel_used

asteroids:
  agency = heading_change_effect_on_velocity / thrust_used

pressure:
  agency = pressure_reduction_after_drilling / drill_attempts

freescape:
  agency = successful movement + zone transitions + collision recovery

colony:
  agency = successful cell moves / attempted cell moves
```

This will immediately expose why Colony v2 underperformed.

---

## Fix 4 — Dynamic Ambiguity

Ambiguity should be prediction error:

```python
ambiguity = abs(predicted_next_state - actual_next_state)
```

Simplified:

```python
ambiguity = normalized_prediction_error
```

Per mode:

```text
lander:
  predicted altitude/speed vs actual

asteroids:
  predicted position vs actual after wrap/gravity

pressure:
  predicted pressure graph vs actual pressure graph

freescape:
  predicted zone/position/collision vs actual

colony:
  predicted next cell vs actual next cell
```

This converts ambiguity from a poetic constant into a real diagnostic.

---

## Fix 5 — CSV/JSON Completeness

CSV should include:

```text
mle
law_cost
agency
ambiguity
prediction_error
state_density
active_laws
agent_policy
failure_state
teleported
collision_count
zone_id
cell_x
cell_y
suit_energy
```

JSON should include **per-mode active law sets**, not the global registry.

---

# 6. New Core Data Classes

## `LawTermV3`

```python
@dataclass
class LawTermV3:
    name: str
    active: bool
    cost: float
    verified: str
    preconditions: list[str]
    effects: list[str]
    trust: float = 1.0
    activation_count: int = 0
    contribution_score: float = 0.0
    prediction_error: float = 0.0
```

This enables DLASc.

---

## `AgentStats`

```python
@dataclass
class AgentStats:
    attempted_actions: int = 0
    successful_actions: int = 0
    blocked_actions: int = 0
    useful_actions: int = 0
    collisions: int = 0
    teleports: int = 0
    failures: int = 0

    @property
    def agency(self) -> float:
        return self.successful_actions / max(self.attempted_actions, 1)
```

---

## `SemanticState`

```python
@dataclass
class SemanticState:
    state_density: float = 0.0
    agency: float = 0.0
    ambiguity: float = 0.0
    prediction_error: float = 0.0
    semantic_entropy: float = 0.0
    compression_ratio: float = 0.0
    falsifiability: float = 0.0
    law_cost: float = 0.0
    playable_reality: float = 0.0
```

---

## `RunDiagnosis`

```python
@dataclass
class RunDiagnosis:
    mode: str
    best_pr: float
    final_pr: float
    failure_reason: str | None
    bottlenecks: list[str]
    recommended_repairs: list[str]
    law_contributions: dict[str, float]
```

---

# 7. Dynamic Law-Actuated Semantic Compiler

This is the biggest v3 system.

Name:

```text
DLASc — Dynamic Law-Actuated Semantic Compiler
```

Purpose:

```text
Activate only the laws that improve playable reality under current conditions.
```

## Law Preconditions

Example registry:

```python
LAW_REGISTRY = {
    "toroidal_wrap": LawTermV3(
        name="toroidal_wrap",
        active=False,
        cost=0.5,
        verified="historical",
        preconditions=["world_has_edges", "wrap_enabled"],
        effects=["boundary_transition", "state_continuity"],
    ),
    "wall_following_agent": LawTermV3(
        name="wall_following_agent",
        active=False,
        cost=1.0,
        verified="equivalent",
        preconditions=["cell_grid", "blocked_actions_high"],
        effects=["agency_increase", "semantic_entropy_decrease"],
    ),
}
```

## Activation Logic

```python
def should_activate_law(law, context):
    if not all(context[p] for p in law.preconditions):
        return False
    if context["agency"] < 0.4 and "agency_increase" in law.effects:
        return True
    if context["prediction_error"] > 0.25 and "prediction_repair" in law.effects:
        return True
    if context["criticality"] > 0.8 and "stabilization" in law.effects:
        return True
    return False
```

## Deactivation Logic

```python
def should_deactivate_law(law, context):
    if law.contribution_score < 0 and law.activation_count > 20:
        return True
    if context["semantic_entropy"] > 4.0 and law.cost > 2.0:
        return True
    return False
```

---

# 8. Adaptive Agent Scripts

The v2 “scripted input” is too dumb. v3 should have named agents.

## Agent Types

```text
naive
pid
wall_follow
risk_seeking
risk_averse
optimizer
```

## Lander PID Agent

Goal:

```text
reduce vertical speed near landing pad while conserving fuel
```

Pseudo:

```python
def lander_pid_agent(state):
    target_vertical_speed = -1.5
    error = target_vertical_speed - state.vel.y
    thrust = kp * error + kd * (error - prev_error)
    return clamp(thrust, 0, max_thrust)
```

This tests “player as numerical solver.”

---

## Colony Wall-Following Agent

Goal:

```text
escape the stuck-cell failure seen in v2
```

Pseudo:

```python
def colony_wall_follow_agent(cx, cy, heading, grid):
    # right-hand rule
    if can_move(right_of(heading)):
        return turn_right_then_move
    if can_move(forward):
        return move_forward
    if can_move(left_of(heading)):
        return turn_left_then_move
    return turn_around
```

Expected result:

```text
Colony PR should rise sharply.
Agency should rise.
Semantic entropy should fall.
Cell coverage should increase.
```

---

## Pressure Risk Agent

Goal:

```text
test pressure failure boundaries
```

Modes:

```text
risk_averse: drill early, avoid criticality
risk_seeking: wait until high pressure, drill late
random: baseline
```

This creates meaningful time-to-failure comparisons.

---

# 9. Failure Boundary Testing

Add:

```bash
python rgpuf_lab_v3.py --stress pressure --until-failure
python rgpuf_lab_v3.py --stress lander --until-failure
python rgpuf_lab_v3.py --stress freescape --until-failure
```

Metrics:

```text
TTF = time to failure
CTF = criticality at failure
AUC_crit = area under criticality curve
Recovery = whether agent reduced criticality after crossing warning level
```

## Failure Types

```text
lander:
  crash_velocity
  fuel_empty
  heat_shutdown

asteroids:
  heat_overload
  gravity_capture
  wrap_disorientation

pressure:
  overpressure_explosion
  hysteresis_failure

freescape:
  shield_depletion
  fall_maroon
  pressure_zone_failure

colony:
  suit_energy_depletion
  stuck_loop
  hostile_los_failure

semantic:
  entropy_collapse
  law_bloat
```

---

# 10. GhostMesh48-HDC Semantic Optimizer

This should be lightweight, not a giant matrix engine.

Name:

```text
GM48-HDC Microkernel
```

Purpose:

```text
Represent laws, states, and metrics as hyperdimensional vectors and use similarity to detect drift, anomaly, and law usefulness.
```

## Vector Size

Use:

```python
HDC_DIM = 2048
```

Not 10,000 yet. Keep it fast.

## Encoding

Each law gets a bipolar vector:

```python
law_vector[name] = random_bipolar_vector(seed=hash(name))
```

Each metric bucket gets a vector:

```text
high_agency
low_agency
high_entropy
low_entropy
critical_rising
critical_falling
pr_improving
pr_declining
```

State vector:

```python
state_vec = bundle([
    vector_for_mode,
    vector_for_active_laws,
    vector_for_metric_buckets,
])
```

## HDC Operations

```python
bind(a, b)      = elementwise multiply
bundle(vectors) = sign(sum(vectors))
permute(v)      = rotate vector by one index
similarity(a,b) = cosine similarity
```

## Semantic Drift

```python
drift = 1.0 - similarity(predicted_state_vec, actual_state_vec)
```

## Gödel Anomaly Injection

When prediction error spikes:

```python
if drift > anomaly_threshold:
    anomaly_vec = random_bipolar_vector(seed=step + seed)
    semantic_memory = bundle([semantic_memory, anomaly_vec])
    godel_tokens += 1
```

This gives your “Gödel anomaly” a concrete runtime meaning:

```text
Gödel anomaly = unexpected state transition that the current law stack failed to predict.
```

No mysticism needed. It becomes a falsifiable prediction-error event.

---

# 11. Exceptional Point Approximation

In full theory, exceptional points need eigenvalues. v3 can approximate them cheaply.

Define:

```python
delta_ep = abs(similarity(law_vec_a, state_vec) - similarity(law_vec_b, state_vec))
```

If:

```python
delta_ep < epsilon
```

Then two laws are functionally overlapping or interfering.

Use this to detect:

```text
resource_thermodynamics vs hysteresis_failure
cell_occupancy vs wall_following_agent
toroidal_wrap vs teleport_transform
```

Output:

```text
EP warning: toroidal_wrap and teleport_transform are near-degenerate in colony mode.
Potential ambiguity source: boundary transition and teleport transition are indistinguishable to agent.
```

---

# 12. Dynamic Semantic Mode

v2 semantic mode is static. v3 semantic mode should run live.

Instead of:

```text
compute final metrics once → repeat every frame
```

Use:

```text
run each submode as a coroutine
step all modes together
collect metrics at each step
compute cross-mode correlations
update law weights
emit evolving semantic telemetry
```

Pseudo:

```python
def run_semantic_live(steps, seed):
    runners = init_all_mode_states(seed)

    for step in range(steps + 1):
        mode_metrics = {}
        for mode, runner in runners.items():
            mode_metrics[mode] = runner.step()

        correlations = compute_cross_mode_correlations(mode_metrics)
        optimizer_state = gm48_hdc_update(mode_metrics, correlations)
        yield semantic_metrics(step, mode_metrics, optimizer_state)
```

Now semantic mode becomes meaningful.

---

# 13. New Metrics for v3

Add these columns:

| Metric               | Meaning                                         |
| -------------------- | ----------------------------------------------- |
| `agency_measured`    | successful actions / attempted actions          |
| `ambiguity_measured` | normalized prediction error                     |
| `law_cost`           | sum of active law costs                         |
| `law_contribution`   | PR delta caused by each law                     |
| `state_coverage`     | unique states visited / total steps             |
| `ttf`                | time to failure                                 |
| `recovery_score`     | ability to return from high criticality         |
| `godel_tokens`       | number of prediction anomalies                  |
| `semantic_drift`     | HDC distance from predicted state               |
| `delta_ep_min`       | closest law-law exceptional point approximation |
| `law_bloat`          | cost of laws with low contribution              |
| `repair_gain`        | estimated PR gain from suggested patch          |

---

# 14. Per-Law Contribution Analysis

This is essential.

Method:

```text
Run baseline with all laws.
Disable one law.
Run same seed.
Measure PR delta.
```

Formula:

```text
Contribution(law_i) = PR_full - PR_without_i
```

Interpretation:

```text
positive = useful law
zero = unused law
negative = harmful law
```

Output:

```text
LAW CONTRIBUTIONS — colony
cell_occupancy          +0.180
quantized_rotation      +0.042
toroidal_wrap           +0.010
teleport_transform      +0.000  unused
bresenham_los           -0.030  harmful under current agent
wall_following_agent    +0.220  recommended
```

This directly repairs the “laws counted but not actually executed” issue.

---

# 15. Colony v3 Specific Repairs

Colony is the most important v3 repair target.

## Current problem

```text
High law count.
High falsifiability.
Low movement.
Low agency.
High semantic entropy.
```

## Add

```text
wall-following agent
cell coverage metric
teleport visibility metric
wall density tuning
LOS wall checking
suit display
stuck-loop detector
```

## Stuck Loop Detector

```python
if same_cell_count > 24:
    context["stuck_loop"] = True
    activate("wall_following_agent")
```

## Cell Coverage

```python
coverage = len(visited_cells) / (grid_w * grid_h)
```

## Better print line

```text
t=120 mode=colony cell=(14,13) heading=032 suit=92.1 coverage=0.18 agency=0.74 stuck=false PR=0.521
```

Expected v3 result:

```text
Colony PR should move from ~0.312 to ~0.50–0.60.
SE should drop from ~3.20 to ~1.50–2.10.
```

---

# 16. Pressure v3 Specific Repairs

Pressure mode should become the failure-boundary lab.

Add:

```text
pressure critical threshold test
hysteresis leak
drilling policy variants
zone pressure AUC
pressure wave speed
time-to-explosion
```

## Hysteresis with leak

Instead of:

```python
excess += max(0, pressure - critical) * dt
```

Use:

```python
excess += max(0, pressure - critical) * dt
excess -= hysteresis_leak * excess * dt
excess = max(0, excess)
```

Now recovery is possible.

## Pressure Wave Speed

Track when each zone crosses a threshold:

```python
crossing_time[zone_id] = step
```

Then:

```python
wave_speed = graph_distance / time_delta
```

This makes pressure diffusion scientifically measurable.

---

# 17. Lander v3 Specific Repairs

Add:

```text
PID pilot
suicide burn solver
landing pad target
crash/land classification
fuel-optimal score
```

## Landing condition

```python
landed = (
    abs(vx) < safe_vx and
    abs(vy) < safe_vy and
    abs(x - pad_x) < pad_width and
    y <= ground_height
)
```

## Score

```text
landing_score = landed × fuel_remaining × safety_margin
```

This makes the “player as numerical solver” claim executable.

---

# 18. Asteroids v3 Specific Repairs

Add:

```text
energy conservation test
orbital capture detector
slingshot detector
angular momentum metric
wrap event count
```

## Angular Momentum

```python
L = r.x * v.y - r.y * v.x
```

Track drift:

```python
angular_momentum_error = abs(L_t - L_0)
```

This helps validate central gravity and integration quality.

## Integrator Choice

Add:

```bash
--integrator euler
--integrator verlet
--integrator rk4
```

Then compare:

```text
Euler: high energy drift
Verlet: better orbital stability
RK4: best accuracy, highest cost
```

This directly addresses numerical issues.

---

# 19. Freescape v3 Specific Repairs

Add:

```text
position-derived zone membership
collision count
maroon state
cuboid contact normal
hydraulic acceleration not velocity assignment
zone law transition log
```

## Zone from position

Instead of changing zone every 60 steps, derive it:

```python
zone_id = int(body.pos.x / zone_width) % len(zones)
```

## Hydraulic lift

Replace:

```python
body.vel.y = 3.0
```

With:

```python
body.vel.y += hydraulic_accel * dt
```

## Maroon state

```python
if body.pos.y == 0 and no_elevator_nearby:
    body.state = "marooned"
```

This makes Driller-style falling meaningful.

---

# 20. Audit Mode

Add:

```bash
python rgpuf_lab_v3.py --mode audit --target colony
```

Output:

```text
AUDIT REPORT — colony

Detected:
- agency collapse after step 36
- 87.5% of movement attempts blocked
- teleport_transform registered but never executed
- suit energy not displayed
- semantic entropy high because law_count=8 and agency=0.31

Recommended:
1. activate wall_following_agent
2. lower procedural wall density from 0.65 to 0.45
3. count only executed laws in active_laws
4. show suit energy instead of fuel
5. add stuck_loop failure state
```

This is the most useful developer-facing feature.

---

# 21. Optimizer Mode

Add:

```bash
python rgpuf_lab_v3.py --mode optimizer --target colony --episodes 30
```

The optimizer runs multiple seeds/policies/law stacks.

## Search space

```text
agent_policy:
  naive
  wall_follow
  random_walk
  right_hand_rule

wall_density:
  0.25–0.70

teleport_probability:
  0.01–0.10

law_stack:
  static
  dynamic
  minimal
  full
```

## Output

```text
BEST CONFIG — colony
policy=wall_follow
wall_density=0.42
teleport_probability=0.06
dynamic_laws=true

PR: 0.312 → 0.587
Agency: 0.31 → 0.78
SE: 3.20 → 1.64
Coverage: 0.02 → 0.31
```

This turns v3 into a working research tool.

---

# 22. Markdown Report Export

Add:

```bash
--report rgpuf_v3_report.md
```

Report structure:

```text
# RGPUF Lab v3 Report

## Run Config
## Mode Comparison
## Per-Mode Diagnosis
## Failure Boundary Results
## Law Contribution Table
## Semantic Drift Events
## Gödel Anomalies
## Exceptional Point Warnings
## Recommended Repairs
## Final Verdict
```

This will make the demo usable for GitHub documentation immediately.

---

# 23. v3 Output Example

Target output should look like:

```text
RGPUF Lab v3 — Adaptive Minimum-Law Retro Physics Lab
law stack: dynamic | agent: adaptive | semantic: HDC

t=000 colony cell=(13,12) suit=100.0 agency=1.00 PR=0.412 SE=1.88 laws=7
t=036 colony cell=(14,13) suit= 99.6 agency=0.42 PR=0.301 SE=3.05 laws=8
  ! stuck_loop detected
  + activating wall_following_agent
  - deactivating teleport_transform: unused
t=060 colony cell=(15,13) suit= 99.1 agency=0.61 PR=0.438 SE=2.22 laws=8
t=120 colony cell=(18,16) suit= 97.8 agency=0.76 PR=0.552 SE=1.68 laws=8
```

Comparison:

```text
MODE COMPARISON v3

Mode        PR_v2   PR_v3   ΔPR    Agency  SE     Laws  LawCost  Diagnosis
lander      0.522   0.701  +0.179  0.88    0.62   5     4.8      PID improved landing
asteroids   0.648   0.682  +0.034  0.91    1.21   5     4.7      stable
pressure    0.407   0.531  +0.124  0.67    2.40   6     6.1      recovery enabled
freescape   0.654   0.690  +0.036  0.82    2.10   7     7.2      zone membership fixed
colony      0.312   0.587  +0.275  0.78    1.64   8     7.4      wall-follow repair
semantic    0.123   0.441  +0.318  0.62    1.92   6     6.5      live optimizer
```

---

# 24. Development Phases

## Phase 1 — Repair Metrics

Implement:

```text
measured agency
measured state density
dynamic ambiguity
law cost
CSV/JSON completion
per-mode active laws
```

## Phase 2 — Fix Weak Modes

Implement:

```text
Colony wall-following
semantic live mode
pressure hysteresis leak
freescape position-derived zones
lander PID
asteroids angular momentum
```

## Phase 3 — Add DLASc

Implement:

```text
law preconditions
law activation/deactivation
law contribution scoring
stuck-loop law activation
criticality law activation
```

## Phase 4 — Add GM48-HDC

Implement:

```text
hyperdimensional vectors
semantic drift
Gödel tokens
exceptional point approximation
semantic memory
```

## Phase 5 — Add Research Exports

Implement:

```text
audit mode
optimizer mode
stress mode
markdown report
comparison against v2 baseline
```

---

# 25. Final v3 Target

The next script should answer four questions automatically:

```text
1. Which mode generates the most playable reality?
2. Which law contributes the most?
3. Which law is dead weight?
4. What repair increases PR the most without bloating the law stack?
```

That is the leap from v2 to v3.

```text
v2 proves the RGPUF thesis.
v3 makes RGPUF self-diagnosing.
v4 can make it self-generating.
```

Final design name:

```text
RGPUF Lab v3 — Adaptive Minimum-Law Retro Physics Lab
```

Core one-line purpose:

```text
A self-auditing retro physics lab that dynamically discovers the smallest law stack capable of producing the richest playable world.
```
