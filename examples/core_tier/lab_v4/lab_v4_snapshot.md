### Date: May 04 2026 (https://github.com/TaoishTechy/RGPUF/)

```
# RGPUF Lab v4 -- Micro-World Forge Report

core: rgpuf_core.py | demo: rgpuf_lab_v4.py


## Mode Comparison


MODE          PR_BASE PR_ADAPT   PR_OPT   DELTA  AGENCY  COVER LAW_COST

------------------------------------------------------------------------
lander          0.997    1.644    1.644  +0.648    0.00   0.00      5.7
asteroids       0.489    0.489    0.489  +0.000    0.24   0.00      5.2
pressure        0.550    0.469    0.550  +0.000    0.00   0.00      7.8
freescape       0.434    0.434    0.456  +0.022    0.00   0.00      9.7
colony          0.035    0.188    0.499  +0.464    0.56   0.01      7.8
semantic        0.065    0.065    0.065  -0.000    0.58   0.00      6.2

## Detailed Mode Analysis


### lander

- Final PR (normalized): 0.9965
- Final PR (raw): 0.2215
- Goal Agency: 0.4898
- Coverage: 0.0000
- Law Cost: 4.50
- Laws: thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality
- Gödel Tokens: 49
- Failure: active

### asteroids

- Final PR (normalized): 0.4891
- Final PR (raw): 0.0940
- Goal Agency: 0.2353
- Coverage: 0.0000
- Law Cost: 5.20
- Laws: central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality
- Gödel Tokens: 49
- Failure: active

### pressure

- Final PR (normalized): 0.5499
- Final PR (raw): 0.0786
- Goal Agency: 0.0000
- Coverage: 0.0000
- Law Cost: 7.00
- Laws: thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality
- Gödel Tokens: 49
- Failure: active

### freescape

- Final PR (normalized): 0.4336
- Final PR (raw): 0.0447
- Goal Agency: 0.0000
- Coverage: 0.0000
- Law Cost: 9.70
- Laws: cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality
- Gödel Tokens: 49
- Failure: active

### colony

- Final PR (normalized): 0.0348
- Final PR (raw): 0.0058
- Goal Agency: 0.2222
- Coverage: 0.0052
- Law Cost: 6.00
- Laws: cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality
- Gödel Tokens: 9
- Failure: active

### semantic

- Final PR (normalized): 0.0650
- Final PR (raw): 0.0650
- Goal Agency: 0.5833
- Coverage: 0.0006
- Law Cost: 6.15
- Laws: playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy
- Gödel Tokens: 0
- Failure: active

## Best Micro-World Recipes


### Lander

- Seed: 42
- Wall Density: 0.3
- Policy: wall_follow
- PR: 1.6441

### Asteroids

- Seed: 42
- Wall Density: 0.3
- Policy: naive
- PR: 0.4891

### Pressure

- Seed: 42
- Wall Density: 0.3
- Policy: naive
- PR: 0.5499

### Freescape

- Seed: 50
- Wall Density: 0.3
- Policy: naive
- PR: 0.4558

### Colony

- Seed: 47
- Wall Density: 0.3
- Policy: wall_follow
- PR: 0.4987

### Semantic

- Seed: 42
- Wall Density: 0.3
- Policy: naive
- PR: 0.065

---
---
---

>>
```

## rgpuf_core.py
```
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
- DLASc dynamic law compiler
- audit/optimization primitives

This file is importable and should not run full demos by default.
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Literal

TAU = math.tau
BASE_MODES = ["lander", "asteroids", "pressure", "freescape", "colony", "semantic"]

# ═══════════════════════════════════════════════════════════════════════════════
# 1. Constants
# ═══════════════════════════════════════════════════════════════════════════════

VERIFIED_WEIGHT = {"historical": 1.0, "equivalent": 0.7, "speculative": 0.3}
SECTOR_DIRS = [(0, -1, "n"), (1, 0, "e"), (0, 1, "s"), (-1, 0, "w")]
WALL_RIGHT = ["e", "s", "w", "n"]
WALL_LEFT = ["w", "n", "e", "s"]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Math Primitives
# ═══════════════════════════════════════════════════════════════════════════════

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def wrap(v: float, size: float) -> float:
    """Toroidal boundary: Asteroids / 3-Demon / Elite / Colony wrap."""
    return v % size


@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, o: Vec2) -> Vec2:
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: Vec2) -> Vec2:
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, s: float) -> Vec2:
        return Vec2(self.x * s, self.y * s)

    def dot(self, o: Vec2) -> float:
        return self.x * o.x + self.y * o.y

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def distance_to(self, o: Vec2) -> float:
        return (self - o).length()

    def rotate(self, rad: float) -> Vec2:
        c, s = math.cos(rad), math.sin(rad)
        return Vec2(self.x * c - self.y * s, self.x * s + self.y * c)

    def normalized(self) -> Vec2:
        m = self.length()
        return Vec2(self.x / m, self.y / m) if m > 1e-9 else Vec2()

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    def quantized(self, scale: float = 1.0) -> tuple[int, int]:
        return (int(self.x / scale), int(self.y / scale))


@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o: Vec3) -> Vec3:
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o: Vec3) -> Vec3:
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, s: float) -> Vec3:
        return Vec3(self.x * s, self.y * s, self.z * s)

    def dot(self, o: Vec3) -> float:
        return self.x * o.x + self.y * o.y + self.z * o.z

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def distance_to(self, o: Vec3) -> float:
        return (self - o).length()

    def rotate_y(self, rad: float) -> Vec3:
        c, s = math.cos(rad), math.sin(rad)
        return Vec3(self.x * c + self.z * s, self.y, -self.x * s + self.z * c)

    def normalized(self) -> Vec3:
        m = self.length()
        return Vec3(self.x / m, self.y / m, self.z / m) if m > 1e-9 else Vec3()

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def quantized(self, scale: float = 1.0) -> tuple[int, int, int]:
        return (int(self.x / scale), int(self.y / scale), int(self.z / scale))


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Core Dataclasses
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class Body:
    """Rigid body with 2D position, velocity, quantized heading, and extended state."""
    pos: Vec2 = field(default_factory=Vec2)
    vel: Vec2 = field(default_factory=Vec2)
    mass: float = 1.0
    radius: float = 1.0
    heading_byte: int = 64
    height: float = 0.0
    mode: str = "ground"
    zone_id: int = 0
    state: str = "active"

    # v4: event counters for measured agency
    last_pos: Vec2 = field(default_factory=Vec2)
    collision_count: int = 0
    wrap_count: int = 0
    teleport_count: int = 0

    @property
    def heading_rad(self) -> float:
        return (self.heading_byte / 256.0) * TAU

    @property
    def forward(self) -> Vec2:
        a = self.heading_rad
        return Vec2(math.cos(a), math.sin(a))

    def rotate_quantized(self, ticks: int) -> None:
        self.heading_byte = (self.heading_byte + ticks) % 256


@dataclass
class Body3:
    """3D body for Freescape / Colony spatial modes."""
    pos: Vec3 = field(default_factory=Vec3)
    vel: Vec3 = field(default_factory=Vec3)
    heading_byte: int = 0
    zone_id: int = 0
    state: str = "active"

    last_pos: Vec3 = field(default_factory=Vec3)
    collision_count: int = 0
    wrap_count: int = 0
    teleport_count: int = 0

    @property
    def heading_rad(self) -> float:
        return (self.heading_byte / 256.0) * TAU

    def rotate_quantized(self, ticks: int) -> None:
        self.heading_byte = (self.heading_byte + ticks) % 256


@dataclass
class ResourceReservoir:
    """Universal RGPUF resource law -- Eq. 2:
        dR/dt = source(t) - sink(t) - leak * R + noise
    """
    value: float
    capacity: float
    leak: float = 0.0
    critical: float | None = None

    def step(self, dt: float, source: float = 0.0,
             sink: float = 0.0, noise: float = 0.0) -> None:
        self.value += (source - sink - self.leak * self.value + noise) * dt
        self.value = clamp(self.value, 0.0, self.capacity)

    @property
    def criticality(self) -> float:
        if self.critical is None or self.critical <= 0:
            return self.value / max(self.capacity, 1e-9)
        return self.value / self.critical

    def normalized(self) -> float:
        return self.value / max(self.capacity, 1e-9)

    def failure_margin(self) -> float:
        if self.critical is None:
            return 1.0 - self.normalized()
        return (self.value - self.critical) / max(self.critical, 1e-9)

    def is_critical(self) -> bool:
        if self.critical is None:
            return self.value < self.capacity * 0.1
        return self.value < self.critical


@dataclass
class Zone:
    """Per-zone physical laws -- Driller / Freescape style."""
    id: int
    gravity: float = 1.0
    friction: float = 0.1
    light_radius: float = 999.0
    time_scale: float = 1.0
    pressure: float = 25.0
    neighbors: list[int] = field(default_factory=list)


@dataclass
class Cuboid:
    """Axis-aligned bounding box -- Freespace / Driller constructive geometry."""
    mn: Vec3 = field(default_factory=Vec3)
    mx: Vec3 = field(default_factory=Vec3)
    solid: bool = True


def inside_cuboid(p: Vec3, c: Cuboid) -> bool:
    return (c.mn.x <= p.x <= c.mx.x and
            c.mn.y <= p.y <= c.mx.y and
            c.mn.z <= p.z <= c.mx.z)


def cuboid_collide(p: Vec3, vel: Vec3, c: Cuboid) -> tuple[bool, Vec3]:
    if not inside_cuboid(p, c) or not c.solid:
        return False, vel
    pen_x = min(p.x - c.mn.x, c.mx.x - p.x)
    pen_y = min(p.y - c.mn.y, c.mx.y - p.y)
    pen_z = min(p.z - c.mn.z, c.mx.z - p.z)
    if pen_x <= pen_y and pen_x <= pen_z:
        vel.x *= -0.3
        p.x = (c.mn.x - 0.01) if (p.x - c.mn.x) < (c.mx.x - p.x) else (c.mx.x + 0.01)
    elif pen_y <= pen_z:
        vel.y *= -0.3
        p.y = (c.mn.y - 0.01) if (p.y - c.mn.y) < (c.mx.y - p.y) else (c.mx.y + 0.01)
    else:
        vel.z *= -0.3
        p.z = (c.mn.z - 0.01) if (p.z - c.mn.z) < (c.mx.z - p.z) else (c.mx.z + 0.01)
    return True, vel


@dataclass
class Cell:
    """Colony / 3-Demon cell: compressed spatial law."""
    walls: dict[str, bool] = field(default_factory=lambda: {
        "n": True, "s": True, "e": True, "w": True, "u": False, "d": False,
    })
    object_id: int = 0
    furniture: bool = False
    teleport_to: tuple[int, int] | None = None
    energy_station: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Law Registry v4
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class LawTerm:
    """Law descriptor. No `active` flag -- LawStack handles runtime state."""
    name: str
    family: str
    cost: float
    verified: str  # "historical" | "equivalent" | "speculative"
    preconditions: tuple[str, ...] = ()
    effects: tuple[str, ...] = ()
    trust: float = 1.0
    token_cost: int = 2  # Gödel tokens needed for repair trial


@dataclass
class LawStack:
    """Runtime law stack -- the v4 keystone.
    Global registry describes *available* laws.
    LawStack describes *actually executed* laws.
    This prevents the v3 bug where global active flags inflated every mode.
    """
    names: list[str] = field(default_factory=list)

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
        total = sum(
            weights.get(registry[n].verified, 0.3) * registry[n].trust
            for n in self.names if n in registry
        )
        return total / len(self.names)

    def count(self) -> int:
        return len(self.names)


LAW_REGISTRY: dict[str, LawTerm] = {
    # Motion family
    "thrust_gravity_drag": LawTerm(
        "thrust_gravity_drag", "motion", 1.0, "equivalent",
        effects=("motion", "control")
    ),
    "central_gravity_well": LawTerm(
        "central_gravity_well", "motion", 1.2, "historical",
        effects=("orbital_motion",)
    ),
    "quantized_rotation": LawTerm(
        "quantized_rotation", "motion", 0.5, "historical",
        effects=("heading_discrete",)
    ),
    # Topology family
    "toroidal_wrap": LawTerm(
        "toroidal_wrap", "topology", 0.5, "historical",
        preconditions=("wrap_enabled",),
        effects=("boundary_continuity",)
    ),
    "teleport_transform": LawTerm(
        "teleport_transform", "topology", 1.0, "historical",
        preconditions=("teleport_trigger",),
        effects=("state_continuity",)
    ),
    # Resource family
    "resource_thermodynamics": LawTerm(
        "resource_thermodynamics", "resource", 1.0, "equivalent",
        effects=("fuel_drain", "heat_buildup")
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
    # Spatial family
    "cuboid_collision": LawTerm(
        "cuboid_collision", "spatial", 1.5, "historical",
        preconditions=("cuboid_world",),
        effects=("spatial_constraint",)
    ),
    "zone_gravity_friction": LawTerm(
        "zone_gravity_friction", "spatial", 1.0, "historical",
        preconditions=("zone_system",),
        effects=("spatial_constraint",)
    ),
    "hydraulic_height": LawTerm(
        "hydraulic_height", "spatial", 1.2, "equivalent",
        preconditions=("zone_system",),
        effects=("agency_increase",)
    ),
    # Colony family
    "cell_occupancy": LawTerm(
        "cell_occupancy", "colony", 1.0, "historical",
        preconditions=("cell_grid",),
        effects=("spatial_constraint",)
    ),
    "bresenham_los": LawTerm(
        "bresenham_los", "colony", 0.8, "historical",
        preconditions=("cell_grid",),
        effects=("prediction_repair",)
    ),
    "toroidal_surface": LawTerm(
        "toroidal_surface", "colony", 0.5, "historical",
        preconditions=("torus_world",),
        effects=("state_continuity",)
    ),
    "power_suit_energy": LawTerm(
        "power_suit_energy", "colony", 1.0, "equivalent",
        effects=("energy_drain",)
    ),
    # Adaptive agent family
    "wall_following_agent": LawTerm(
        "wall_following_agent", "agent", 1.0, "equivalent",
        preconditions=("cell_grid", "blocked_actions_high"),
        effects=("coverage_increase", "agency_increase"),
        token_cost=2
    ),
    "pid_controller": LawTerm(
        "pid_controller", "agent", 1.2, "equivalent",
        preconditions=("continuous_motion", "landing_target"),
        effects=("agency_increase",),
        token_cost=2
    ),
    "risk_policy": LawTerm(
        "risk_policy", "agent", 0.8, "speculative",
        preconditions=("pressure_reservoir",),
        effects=("stabilization",),
        token_cost=1
    ),
    # Semantic family
    "playable_reality": LawTerm(
        "playable_reality", "semantic", 2.0, "speculative",
        effects=("metric_headline",)
    ),
    "minimum_law_efficiency": LawTerm(
        "minimum_law_efficiency", "semantic", 2.0, "speculative",
        effects=("metric_mle",)
    ),
    "compression_ratio": LawTerm(
        "compression_ratio", "semantic", 1.5, "speculative",
        effects=("metric_cr",)
    ),
    "semantic_entropy": LawTerm(
        "semantic_entropy", "semantic", 2.0, "speculative",
        effects=("metric_se",)
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Agent Stats, SimConfig, SimState, Telemetry
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class AgentStats:
    """Separates action success from goal success."""
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


@dataclass
class Telemetry:
    """v4 telemetry packet -- richer than v3 Metrics."""
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
    state_density: float = 0.0
    ambiguity: float = 0.0
    compression_gain: float = 0.0

    godel_tokens: int = 0
    semantic_drift: float = 0.0
    delta_ep_min: float = 0.0

    active_laws: str = ""
    events: str = ""
    failure_state: str = "active"
    zone_id: int = 0
    heading_byte: int = 0
    cell_pos: str = ""

    def csv_row(self) -> dict[str, Any]:
        return {
            "step": self.step, "mode": self.mode, "seed": self.seed,
            "x": round(self.x, 2), "y": round(self.y, 2), "z": round(self.z, 2),
            "speed": round(self.speed, 3),
            "fuel": round(self.fuel, 2), "heat": round(self.heat, 2),
            "pressure": round(self.pressure, 2), "suit": round(self.suit, 2),
            "shield": round(self.shield, 2),
            "criticality": round(self.criticality, 4),
            "pr": round(self.pr, 4), "pr_norm": round(self.pr_norm, 4),
            "mle": round(self.mle, 4),
            "law_cost": round(self.law_cost, 2), "law_count": self.law_count,
            "falsifiability": round(self.falsifiability, 4),
            "semantic_entropy": round(self.semantic_entropy, 4),
            "prediction_error": round(self.prediction_error, 4),
            "action_agency": round(self.action_agency, 4),
            "goal_agency": round(self.goal_agency, 4),
            "coverage": round(self.coverage, 4),
            "state_density": round(self.state_density, 4),
            "ambiguity": round(self.ambiguity, 4),
            "compression_gain": round(self.compression_gain, 4),
            "godel_tokens": self.godel_tokens,
            "semantic_drift": round(self.semantic_drift, 4),
            "delta_ep_min": round(self.delta_ep_min, 4),
            "active_laws": self.active_laws,
            "failure_state": self.failure_state,
            "zone_id": self.zone_id,
            "cell_pos": self.cell_pos,
        }


@dataclass
class SimState:
    """Unified simulation state container."""
    mode: str
    seed: int
    step: int
    config: SimConfig
    law_stack: LawStack
    agent_stats: AgentStats
    hdc: HDCEngine | None
    history: list[Telemetry] = field(default_factory=list)

    body: Body | None = None
    body3: Body3 | None = None
    resources: dict[str, ResourceReservoir] = field(default_factory=dict)
    zones: list[Zone] = field(default_factory=list)
    cuboids: list[Cuboid] = field(default_factory=list)
    grid: dict[tuple[int, int], Cell] = field(default_factory=dict)
    visited_cells: set[tuple[int, int]] = field(default_factory=set)
    signatures: set[tuple] = field(default_factory=set)

    extra: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Physics Laws
# ═══════════════════════════════════════════════════════════════════════════════


def arcade_motion_step(
    body: Body, dt: float, thrust: float,
    gravity: Vec2, drag: float,
    world: Vec2, wrap_edges: bool,
) -> None:
    """Unified arcade motion -- Eq. 1:
        F = T * forward + m * g - drag * v + external
    """
    body.last_pos = Vec2(body.pos.x, body.pos.y)
    force = body.forward * thrust + gravity * body.mass - body.vel * drag
    acc = force * (1.0 / body.mass)
    body.vel = body.vel + acc * dt
    body.pos = body.pos + body.vel * dt

    if wrap_edges:
        old_x, old_y = body.pos.x, body.pos.y
        body.pos.x = wrap(body.pos.x, world.x)
        body.pos.y = wrap(body.pos.y, world.y)
        if body.pos.x != old_x or body.pos.y != old_y:
            body.wrap_count += 1
    else:
        if body.pos.x < 0 or body.pos.x > world.x:
            body.vel.x *= -0.85
            body.collision_count += 1
            body.pos.x = clamp(body.pos.x, 0, world.x)
        if body.pos.y < 0:
            body.vel.y *= -0.30
            body.collision_count += 1
            body.pos.y = 0
        if body.pos.y > world.y:
            body.vel.y *= -0.85
            body.collision_count += 1
            body.pos.y = world.y


def motion_step_3d(
    body: Body3, dt: float, gravity: float,
    friction: float, world: Vec3,
    wrap_edges: bool = False,
) -> None:
    """3D motion with per-zone gravity and friction."""
    body.last_pos = Vec3(body.pos.x, body.pos.y, body.pos.z)
    body.vel.y -= gravity * dt
    body.vel.x *= (1.0 - friction)
    body.vel.z *= (1.0 - friction)
    body.pos = body.pos + body.vel * dt
    if wrap_edges:
        old_x, old_z = body.pos.x, body.pos.z
        body.pos.x = wrap(body.pos.x, world.x)
        body.pos.z = wrap(body.pos.z, world.z)
        if body.pos.x != old_x or body.pos.z != old_z:
            body.wrap_count += 1
    else:
        body.pos.x = clamp(body.pos.x, 0, world.x)
        body.pos.z = clamp(body.pos.z, 0, world.z)
        if body.pos.y < 0:
            body.pos.y = 0
            body.vel.y *= -0.3


def central_gravity_well(
    body: Body, attractor: Vec2, gm: float, softening: float = 25.0
) -> Vec2:
    """Spacewar!-style central force with softening."""
    delta = attractor - body.pos
    r2 = delta.x * delta.x + delta.y * delta.y + softening
    return delta.normalized() * (gm / r2)


def graph_pressure_diffusion(
    zones: list[Zone], sinks: dict[int, float],
    dt: float, D: float = 0.08,
) -> None:
    """Eq. 3 -- Driller pressure graph (double-buffered)."""
    deltas = [0.0] * len(zones)
    for i, z in enumerate(zones):
        diff = sum(zones[j].pressure - z.pressure for j in z.neighbors)
        deltas[i] = (D * diff - sinks.get(z.id, 0.0)) * dt
    for i, z in enumerate(zones):
        z.pressure = max(0.0, z.pressure + deltas[i])


def hysteresis_failure(
    excess: float, pressure: float, critical: float,
    dt: float, threshold: float = 15.0,
    hyst_leak: float = 0.05,
) -> tuple[float, bool]:
    """Eq. 4 -- Failure is memory, not instant threshold. With leak for recovery."""
    excess += max(0.0, pressure - critical) * dt
    excess -= hyst_leak * excess * dt
    excess = max(0.0, excess)
    return excess, excess > threshold


def teleport_transform(
    pos: Vec2, vel: Vec2, target: Vec2, delta_heading_byte: int,
) -> tuple[Vec2, Vec2, int]:
    """Colony-style teleport with orientation transform."""
    delta_rad = (delta_heading_byte / 256.0) * TAU
    new_vel = vel.rotate(delta_rad)
    return target, new_vel, delta_heading_byte


def bresenham_los(
    x0: int, y0: int, x1: int, y1: int,
    grid: dict[tuple[int, int], Cell] | None = None,
) -> list[tuple[int, int]]:
    """Bresenham line-of-sight with optional wall-aware truncation."""
    cells: list[tuple[int, int]] = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    cx, cy = x0, y0
    while True:
        cells.append((cx, cy))
        if cx == x1 and cy == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            cx += sx
        if e2 <= dx:
            err += dx
            cy += sy
        # If grid provided, stop at furniture (LOS blocked by walls)
        if grid is not None:
            cell = grid.get((cx, cy))
            if cell and cell.furniture:
                break
    return cells


def colony_generate_grid(
    w: int, h: int, seed: int, wall_density: float = 0.45,
) -> dict[tuple[int, int], Cell]:
    """Procedural cell grid with teleport doors and energy stations."""
    rng = random.Random(seed)
    grid: dict[tuple[int, int], Cell] = {}
    for y in range(h):
        for x in range(w):
            walls = {"n": True, "s": True, "e": True, "w": True,
                     "u": False, "d": False}
            if x < w - 1 and rng.random() < (1.0 - wall_density):
                walls["e"] = False
            if y < h - 1 and rng.random() < (1.0 - wall_density):
                walls["s"] = False
            tp = None
            if rng.random() < 0.04:
                tx, ty = rng.randint(0, w - 1), rng.randint(0, h - 1)
                tp = (tx, ty)
            grid[(x, y)] = Cell(
                walls=walls,
                object_id=rng.randint(0, 3),
                furniture=rng.random() < 0.06,
                teleport_to=tp,
                energy_station=rng.random() < 0.05,
            )
    return grid


def procedural_starfield(
    seed: int, count: int, world_size: Vec2,
) -> list[Vec2]:
    """Deterministic universe: law + seed > stored map."""
    rng = random.Random(seed)
    return [Vec2(rng.random() * world_size.x, rng.random() * world_size.y)
            for _ in range(count)]


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Agent Policies
# ═══════════════════════════════════════════════════════════════════════════════


def agent_naive(step: int, rng: random.Random) -> int:
    """Random rotation ticks on a schedule."""
    if step % 32 == 0:
        return rng.choice([-8, -4, 4, 8])
    return 0


def agent_lander_pid(
    ship: Body, fuel: ResourceReservoir,
    pad_x: float, dt: float,
    prev_error: list[float],
) -> tuple[float, bool]:
    """PID controller targeting safe landing near pad."""
    target_vy = -1.5
    error = target_vy - ship.vel.y
    thrust = clamp(1.8 * error + 0.6 * (error - prev_error[0]), 0, 5.0)
    prev_error[0] = error
    dx = pad_x - ship.pos.x
    if abs(dx) > 8 and fuel.value > 20:
        ship.rotate_quantized(6 if dx > 0 else -6)
    return thrust, fuel.value > 0


def agent_colony_wall_follow(
    cx: int, cy: int, heading: int,
    grid: dict[tuple[int, int], Cell],
    gw: int, gh: int,
) -> tuple[int, int, int, bool]:
    """Right-hand rule wall follower for Colony mode."""
    sector = (heading + 32) % 256 // 64
    cell = grid.get((cx, cy))
    if cell is None:
        return cx, cy, 0, False

    # Try right
    r_wall = WALL_RIGHT[sector]
    r_sector = (sector + 1) % 4
    rdx, rdy, _ = SECTOR_DIRS[r_sector]
    if not cell.walls.get(r_wall, True):
        nx, ny = (cx + rdx) % gw, (cy + rdy) % gh
        target = grid.get((nx, ny))
        if target and not target.furniture:
            dh = 64 if r_sector > sector else -192
            return nx, ny, dh, True

    # Try forward
    fwall = SECTOR_DIRS[sector][2]
    fdx, fdy = SECTOR_DIRS[sector][0], SECTOR_DIRS[sector][1]
    if not cell.walls.get(fwall, True):
        nx, ny = (cx + fdx) % gw, (cy + fdy) % gh
        target = grid.get((nx, ny))
        if target and not target.furniture:
            return nx, ny, 0, True

    # Try left
    l_wall = WALL_LEFT[sector]
    l_sector = (sector + 3) % 4
    ldx, ldy, _ = SECTOR_DIRS[l_sector]
    if not cell.walls.get(l_wall, True):
        nx, ny = (cx + ldx) % gw, (cy + ldy) % gh
        target = grid.get((nx, ny))
        if target and not target.furniture:
            dh = -64 if l_sector < sector else 192
            return nx, ny, dh, True

    # Turn around
    return cx, cy, 128, False


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Prediction Model v4
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class SignaturePredictor:
    """Tiny transition-based predictor -- retro-simple but stateful."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# 9. HDC Engine v4
# ═══════════════════════════════════════════════════════════════════════════════


class HDCEngine:
    """Lightweight HDC using bipolar vectors.
    v4: Gödel tokens are functional -- they buy repair trials via DLASc.
    """

    def __init__(self, dim: int = 1024, seed: int = 42):
        self.dim = dim
        self.rng = random.Random(seed)
        self.vectors: dict[str, list[int]] = {}
        self.memory = self._bipolar()
        self.godel_tokens: int = 0
        self.anomaly_count: int = 0

    def _bipolar(self) -> list[int]:
        return [1 if self.rng.random() < 0.5 else -1 for _ in range(self.dim)]

    def encode(self, name: str) -> list[int]:
        if name not in self.vectors:
            self.vectors[name] = self._bipolar()
        return self.vectors[name]

    @staticmethod
    def bind(a: list[int], b: list[int]) -> list[int]:
        return [x * y for x, y in zip(a, b)]

    @staticmethod
    def bundle(vecs: list[list[int]]) -> list[int]:
        if not vecs:
            return []
        n = len(vecs[0])
        s = [0] * n
        for v in vecs:
            for i in range(n):
                s[i] += v[i]
        return [1 if x >= 0 else -1 for x in s]

    @staticmethod
    def permute(v: list[int], shift: int = 1) -> list[int]:
        shift = shift % len(v)
        return v[shift:] + v[:shift]

    @staticmethod
    def similarity(a: list[int], b: list[int]) -> float:
        n = min(len(a), len(b))
        if n == 0:
            return 0.0
        return sum(a[i] * b[i] for i in range(n)) / n

    def drift(self, predicted: list[int], actual: list[int]) -> float:
        return 1.0 - self.similarity(predicted, actual)

    def inject_anomaly(self) -> list[int]:
        self.anomaly_count += 1
        a = self._bipolar()
        self.memory = self.bundle([self.memory, a])
        return a

    def exceptional_point(
        self, law_a: str, law_b: str, state_vec: list[int],
    ) -> float:
        sa = self.similarity(self.encode(law_a), state_vec)
        sb = self.similarity(self.encode(law_b), state_vec)
        return abs(sa - sb)

    def state_vector(
        self, mode: str, active_laws: list[str],
        metric_buckets: dict[str, bool],
    ) -> list[int]:
        parts = [self.encode(mode)]
        for ln in active_laws:
            parts.append(self.encode(ln))
        for bucket, present in metric_buckets.items():
            if present:
                parts.append(self.encode(bucket))
        return self.bundle(parts)

    def earn_godel_token(self, prediction_error: float,
                         drift_val: float,
                         anomaly_threshold: float) -> bool:
        """Functional anomaly mechanism:
        Prediction failure earns a Gödel token.
        Tokens can be spent by DLASc to test repair laws.
        """
        if prediction_error > anomaly_threshold or drift_val > anomaly_threshold:
            self.godel_tokens += 1
            return True
        return False

    def spend_godel_tokens(self, cost: int) -> bool:
        """Try to spend tokens for a repair trial."""
        if self.godel_tokens >= cost:
            self.godel_tokens -= cost
            return True
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 10. DLASc v4 -- Dynamic Law-Actuated Semantic Compiler
# ═══════════════════════════════════════════════════════════════════════════════


class DLASc:
    """Operates on LawStack, not global registry flags.
    Activation triggers map conditions to law additions.
    Deactivation triggers map conditions to law removals.
    """

    ACTIVATION_RULES: list[tuple[str, callable]] = []
    DEACTIVATION_RULES: list[tuple[str, callable]] = []

    def __init__(self, registry: dict[str, LawTerm]):
        self.registry = registry
        self.contribution_scores: dict[str, float] = defaultdict(float)
        self.execution_counts: dict[str, int] = defaultdict(int)
        self.step_count: int = 0

    def propose(self, state: SimState, t: Telemetry) -> list[str]:
        """Examine state and propose law additions/removals."""
        proposals: list[str] = []
        ctx = {
            "blocked_ratio": state.agent_stats.blocked / max(state.agent_stats.attempted, 1),
            "criticality": t.criticality,
            "prediction_error": t.prediction_error,
            "coverage": t.coverage,
            "law_count": t.law_count,
            "semantic_entropy": t.semantic_entropy,
            "step": state.step,
        }

        # Activation proposals
        if (ctx["blocked_ratio"] > 0.5 and
                "cell_grid" in [LAW_REGISTRY[n].preconditions[0]
                                for n in state.law_stack.names
                                if n in LAW_REGISTRY and LAW_REGISTRY[n].preconditions]):
            if not state.law_stack.has("wall_following_agent"):
                proposals.append("+wall_following_agent")

        if (ctx["criticality"] > 0.7 and
                "pressure_reservoir" in [LAW_REGISTRY[n].preconditions[0]
                                         for n in state.law_stack.names
                                         if n in LAW_REGISTRY and LAW_REGISTRY[n].preconditions]):
            if not state.law_stack.has("risk_policy"):
                proposals.append("+risk_policy")

        if (ctx["prediction_error"] > 0.3 and
                state.mode == "colony" and
                not state.law_stack.has("bresenham_los")):
            proposals.append("+bresenham_los")

        # Deactivation proposals
        for name in list(state.law_stack.names):
            if self.execution_counts[name] == 0 and self.step_count > 40:
                proposals.append(f"-{name}")
            elif self.contribution_scores[name] < -0.05 and self.step_count > 30:
                proposals.append(f"-{name}")

        return proposals

    def apply(self, state: SimState, proposals: list[str]) -> list[str]:
        """Apply proposals to the law stack. Returns list of changes."""
        changes: list[str] = []
        for p in proposals:
            if p.startswith("+"):
                name = p[1:]
                if name in LAW_REGISTRY:
                    cost = LAW_REGISTRY[name].token_cost
                    if (state.hdc is not None and
                            state.hdc.spend_godel_tokens(cost)):
                        state.law_stack.add(name)
                        changes.append(f"+{name}")
            elif p.startswith("-"):
                name = p[1:]
                state.law_stack.remove(name)
                changes.append(f"-{name}")
        return changes

    def tick(self, state: SimState, t: Telemetry) -> list[str]:
        """Full propose+apply cycle."""
        self.step_count += 1
        proposals = self.propose(state, t)
        changes = self.apply(state, proposals)
        return changes

    def record_execution(self, name: str) -> None:
        self.execution_counts[name] += 1

    def update_contribution(
        self, law: str, baseline_pr: float, ablated_pr: float,
    ) -> None:
        contrib = baseline_pr - ablated_pr
        # Rolling average
        old = self.contribution_scores[law]
        self.contribution_scores[law] = 0.7 * old + 0.3 * contrib


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Metrics Engine v4
# ═══════════════════════════════════════════════════════════════════════════════


def state_signature(
    x: float, y: float, z: float, speed: float,
    crit: float, zone: int, heading_byte: int,
    cell: str,
) -> tuple:
    return (
        round(x, 1), round(y, 1), round(z, 1),
        round(speed, 1), round(crit, 2), zone,
        heading_byte // 16, cell,
    )


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
    """Compute (PR_raw, PR_norm).
    PR_raw for internal comparisons.
    PR_norm comparable to v2/v3 outputs.
    """
    law_cost = law_stack.cost(registry)
    law_count = max(law_stack.count(), 1)
    mean_cost = law_cost / law_count

    raw = (
        state_density
        * clamp(goal_agency, 0.0, 1.0)
        * falsifiability
        * clamp(compression_gain, 0.01, 20.0)
    ) / max(
        law_cost * (1 + 0.3 * ambiguity +
                    0.15 * min(semantic_entropy, 5.0) +
                    0.3 * prediction_error),
        1e-9,
    )

    normalized = raw * mean_cost * law_count
    return raw, normalized


def falsifiability_v4(
    law_stack: LawStack, registry: dict[str, LawTerm],
) -> float:
    return law_stack.falsifiability(registry)


def semantic_entropy_v4(
    ambiguity: float, law_count: int, agency: float,
) -> float:
    return ambiguity * law_count / max(agency, 0.01)


def compression_gain_v4(
    step: int, seed_bytes: int, law_cost: float,
) -> float:
    return (step + 1) / max(seed_bytes + law_cost, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Mode Constructors
# ═══════════════════════════════════════════════════════════════════════════════


def make_state(mode: str, seed: int, config: SimConfig) -> SimState:
    """Create a SimState for the given mode."""
    agent_stats = AgentStats()
    hdc = HDCEngine(dim=config.hdc_dim, seed=seed)
    predictor = SignaturePredictor()

    if mode == "lander":
        state = _make_lander(seed, config)
    elif mode == "asteroids":
        state = _make_asteroids(seed, config)
    elif mode == "pressure":
        state = _make_pressure(seed, config)
    elif mode == "freescape":
        state = _make_freescape(seed, config)
    elif mode == "colony":
        state = _make_colony(seed, config)
    elif mode == "semantic":
        state = _make_semantic(seed, config)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    # Keep the law_stack set by the constructor (already has mode-specific laws)
    state.agent_stats = agent_stats
    state.hdc = hdc
    state.config = config
    state.seed = seed
    state.mode = mode
    state.step = 0
    state.extra["predictor"] = predictor
    state.extra["rng"] = random.Random(seed)
    return state


def _make_lander(seed: int, config: SimConfig) -> SimState:
    world = Vec2(160.0, 90.0)
    pad_x = world.x * 0.5
    ship = Body(pos=Vec2(pad_x + 20, world.y * 0.75), vel=Vec2(5.0, 0.0))
    ship.last_pos = Vec2(ship.pos.x, ship.pos.y)
    resources = {
        "fuel": ResourceReservoir(100.0, 100.0),
        "heat": ResourceReservoir(5.0, 100.0, leak=0.035, critical=90.0),
        "pressure": ResourceReservoir(25.0, 150.0, critical=120.0),
    }
    law_stack = LawStack(names=[
        "thrust_gravity_drag", "quantized_rotation",
        "resource_thermodynamics", "playable_reality",
    ])
    if config.adaptive:
        law_stack.add("pid_controller")
    return SimState(
        mode="lander", seed=seed, step=0, config=config,
        law_stack=law_stack, agent_stats=AgentStats(), hdc=None,
        body=ship, resources=resources,
        extra={"pad_x": pad_x, "world": world, "prev_error": [0.0]},
    )


def _make_asteroids(seed: int, config: SimConfig) -> SimState:
    world = Vec2(160.0, 90.0)
    ship = Body(pos=Vec2(world.x * 0.5, world.y * 0.75), vel=Vec2(5.0, 0.0))
    ship.last_pos = Vec2(ship.pos.x, ship.pos.y)
    resources = {
        "fuel": ResourceReservoir(100.0, 100.0),
        "heat": ResourceReservoir(5.0, 100.0, leak=0.035, critical=90.0),
        "pressure": ResourceReservoir(25.0, 150.0, critical=120.0),
    }
    law_stack = LawStack(names=[
        "central_gravity_well", "toroidal_wrap",
        "quantized_rotation", "resource_thermodynamics",
        "playable_reality",
    ])
    return SimState(
        mode="asteroids", seed=seed, step=0, config=config,
        law_stack=law_stack, agent_stats=AgentStats(), hdc=None,
        body=ship, resources=resources,
        extra={
            "world": world,
            "attractor": Vec2(world.x * 0.5, world.y * 0.5),
        },
    )


def _make_pressure(seed: int, config: SimConfig) -> SimState:
    world = Vec2(160.0, 90.0)
    ship = Body(pos=Vec2(world.x * 0.3, world.y * 0.5), vel=Vec2(2.0, 0.0))
    ship.last_pos = Vec2(ship.pos.x, ship.pos.y)
    resources = {
        "fuel": ResourceReservoir(100.0, 100.0),
        "heat": ResourceReservoir(5.0, 100.0, leak=0.035, critical=90.0),
        "pressure": ResourceReservoir(25.0, 150.0, critical=120.0),
    }
    zones = [
        Zone(id=0, pressure=25.0, neighbors=[1, 2]),
        Zone(id=1, pressure=40.0, neighbors=[0, 3, 4]),
        Zone(id=2, pressure=20.0, neighbors=[0, 5]),
        Zone(id=3, pressure=35.0, neighbors=[1]),
        Zone(id=4, pressure=50.0, neighbors=[1]),
        Zone(id=5, pressure=15.0, neighbors=[2]),
    ]
    law_stack = LawStack(names=[
        "thrust_gravity_drag", "graph_pressure_diffusion",
        "hysteresis_failure", "resource_thermodynamics",
        "playable_reality",
    ])
    if config.adaptive:
        law_stack.add("risk_policy")
    return SimState(
        mode="pressure", seed=seed, step=0, config=config,
        law_stack=law_stack, agent_stats=AgentStats(), hdc=None,
        body=ship, resources=resources, zones=zones,
        extra={"world": world, "excess_integral": 0.0, "peak_pressure": 25.0},
    )


def _make_freescape(seed: int, config: SimConfig) -> SimState:
    world3 = Vec3(64.0, 32.0, 64.0)
    body = Body3(
        pos=Vec3(32.0, 16.0, 32.0),
        vel=Vec3(0.5, 0.0, 0.3),
        heading_byte=64, zone_id=0,
    )
    body.last_pos = Vec3(body.pos.x, body.pos.y, body.pos.z)
    resources = {
        "fuel": ResourceReservoir(100.0, 100.0),
        "heat": ResourceReservoir(5.0, 100.0, leak=0.02, critical=90.0),
        "pressure": ResourceReservoir(25.0, 150.0, critical=120.0),
        "shield": ResourceReservoir(50.0, 50.0, critical=10.0),
    }
    zones = [
        Zone(id=0, gravity=1.0, friction=0.05, pressure=25.0, neighbors=[1, 3]),
        Zone(id=1, gravity=0.5, friction=0.10, pressure=40.0, neighbors=[0, 2]),
        Zone(id=2, gravity=0.1, friction=0.20, pressure=80.0, neighbors=[1]),
        Zone(id=3, gravity=2.0, friction=0.02, pressure=15.0, neighbors=[0, 4]),
        Zone(id=4, gravity=1.5, friction=0.08, pressure=60.0, neighbors=[3]),
    ]
    cuboids = [
        Cuboid(Vec3(20, 0, 20), Vec3(22, 20, 22)),
        Cuboid(Vec3(40, 0, 30), Vec3(42, 18, 50)),
        Cuboid(Vec3(10, 0, 40), Vec3(18, 12, 42)),
        Cuboid(Vec3(50, 0, 10), Vec3(52, 25, 30)),
    ]
    law_stack = LawStack(names=[
        "cuboid_collision", "zone_gravity_friction", "hydraulic_height",
        "graph_pressure_diffusion", "hysteresis_failure",
        "resource_thermodynamics", "playable_reality",
    ])
    return SimState(
        mode="freescape", seed=seed, step=0, config=config,
        law_stack=law_stack, agent_stats=AgentStats(), hdc=None,
        body3=body, resources=resources, zones=zones, cuboids=cuboids,
        extra={"world3": world3, "excess_integral": 0.0},
    )


def _make_colony(seed: int, config: SimConfig) -> SimState:
    grid_w, grid_h = 24, 24
    grid = colony_generate_grid(grid_w, grid_h, seed, config.wall_density)
    resources = {
        "fuel": ResourceReservoir(100.0, 100.0),
        "heat": ResourceReservoir(5.0, 100.0, leak=0.01, critical=90.0),
        "pressure": ResourceReservoir(25.0, 150.0, critical=120.0),
        "suit": ResourceReservoir(100.0, 100.0, leak=0.005, critical=15.0),
    }
    cx, cy = grid_w // 2, grid_h // 2
    law_stack = LawStack(names=[
        "cell_occupancy", "quantized_rotation", "toroidal_surface",
        "power_suit_energy", "resource_thermodynamics",
        "playable_reality",
    ])
    if config.adaptive:
        law_stack.add("wall_following_agent")
    return SimState(
        mode="colony", seed=seed, step=0, config=config,
        law_stack=law_stack, agent_stats=AgentStats(), hdc=None,
        resources=resources, grid=grid,
        visited_cells={(cx, cy)},
        extra={
            "cx": cx, "cy": cy, "heading": 64,
            "grid_w": grid_w, "grid_h": grid_h,
        },
    )


def _make_semantic(seed: int, config: SimConfig) -> SimState:
    resources = {
        "fuel": ResourceReservoir(100.0, 100.0),
        "heat": ResourceReservoir(5.0, 100.0),
        "pressure": ResourceReservoir(25.0, 150.0),
    }
    law_stack = LawStack(names=[
        "playable_reality", "minimum_law_efficiency",
        "compression_ratio", "semantic_entropy",
    ])
    return SimState(
        mode="semantic", seed=seed, step=0, config=config,
        law_stack=law_stack, agent_stats=AgentStats(), hdc=None,
        resources=resources,
        extra={"mode_results": {}},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Per-Mode Step Functions
# ═══════════════════════════════════════════════════════════════════════════════


def _build_telemetry(state: SimState) -> Telemetry:
    """Build telemetry from current SimState."""
    rng = state.extra.get("rng", random.Random(0))
    predictor: SignaturePredictor = state.extra.get("predictor", SignaturePredictor())
    dt = state.config.dt

    # Gather position/speed data
    if state.body is not None:
        x, y, z = state.body.pos.x, state.body.pos.y, state.body.height
        speed = state.body.vel.length()
        hb = state.body.heading_byte
        failure_state = state.body.state
    elif state.body3 is not None:
        x, y, z = state.body3.pos.x, state.body3.pos.y, state.body3.pos.z
        speed = state.body3.vel.length()
        hb = state.body3.heading_byte
        failure_state = state.body3.state
    else:
        x, y, z, speed, hb = 0.0, 0.0, 0.0, 0.0, 0
        failure_state = "active"

    fuel = state.resources.get("fuel", ResourceReservoir(0, 1)).value
    heat = state.resources.get("heat", ResourceReservoir(0, 1)).value
    pressure = state.resources.get("pressure", ResourceReservoir(0, 1)).value
    suit = state.resources.get("suit", ResourceReservoir(0, 1)).value
    shield = state.resources.get("shield", ResourceReservoir(0, 1)).value

    crit = max(
        state.resources.get("heat", ResourceReservoir(0, 1)).criticality,
        state.resources.get("pressure", ResourceReservoir(0, 1)).criticality,
        1.0 - state.resources.get("shield", ResourceReservoir(100, 100)).normalized()
        if "shield" in state.resources else 0.0,
    )

    # State signature for state density
    cell_pos = ""
    if "cx" in state.extra and "cy" in state.extra:
        cell_pos = f"({state.extra['cx']},{state.extra['cy']})"
    zone_id = 0
    if state.body3 is not None:
        zone_id = state.body3.zone_id
    elif state.body is not None:
        zone_id = state.body.zone_id

    sig = state_signature(x, y, z, speed, crit, zone_id, hb, cell_pos)
    state.signatures.add(sig)
    state_density = len(state.signatures) / max(state.step + 1, 1)

    # Prediction error via SignaturePredictor
    if predictor.last is not None:
        pred_error = predictor.update(predictor.last, sig)
    else:
        pred_error = 0.0
    predictor.last = sig

    # Coverage (for colony)
    coverage = len(state.visited_cells) / max(
        state.extra.get("grid_w", 1) * state.extra.get("grid_h", 1), 1,
    ) if state.visited_cells else 0.0

    # Agency from AgentStats
    action_ag = state.agent_stats.action_agency
    goal_ag = state.agent_stats.goal_agency
    ag = goal_ag if goal_ag > 0 else action_ag

    # Ambiguity = prediction error for now
    ambiguity = pred_error

    # Metrics
    fals = falsifiability_v4(state.law_stack, LAW_REGISTRY)
    se = semantic_entropy_v4(ambiguity, state.law_stack.count(), ag)
    cg = compression_gain_v4(state.step, 4, state.law_stack.cost(LAW_REGISTRY))
    pr_raw, pr_norm = playable_reality_v4(
        state_density, ag, fals, cg,
        state.law_stack, LAW_REGISTRY,
        ambiguity, se, pred_error,
    )
    mle = state_density / max(state.law_stack.count(), 1)

    # HDC
    godel_tokens = 0
    drift_val = 0.0
    delta_ep = 0.0
    if state.hdc is not None:
        buckets = {
            "high_agency": ag > 0.6,
            "low_agency": ag < 0.3,
            "high_entropy": se > 2.0,
            "critical_rising": crit > 0.5,
            "pr_good": pr_raw > 0.4,
            "coverage_good": coverage > 0.1,
        }
        sv = state.hdc.state_vector(state.mode, state.law_stack.names, buckets)
        drift_val = state.hdc.drift(state.hdc.memory, sv)
        state.hdc.memory = sv
        state.hdc.earn_godel_token(pred_error, drift_val, state.config.anomaly_threshold)
        godel_tokens = state.hdc.godel_tokens

        ep_pairs = [
            ("toroidal_wrap", "teleport_transform"),
            ("resource_thermodynamics", "hysteresis_failure"),
            ("cuboid_collision", "cell_occupancy"),
        ]
        delta_ep = min(
            (state.hdc.exceptional_point(a, b, sv) for a, b in ep_pairs),
            default=0.0,
        )

    return Telemetry(
        step=state.step, mode=state.mode, seed=state.seed,
        x=x, y=y, z=z, speed=speed,
        fuel=fuel, heat=heat, pressure=pressure,
        suit=suit, shield=shield,
        criticality=crit, pr=pr_raw, pr_norm=pr_norm, mle=mle,
        law_cost=state.law_stack.cost(LAW_REGISTRY),
        law_count=state.law_stack.count(),
        falsifiability=fals, semantic_entropy=se,
        prediction_error=pred_error,
        action_agency=action_ag, goal_agency=goal_ag,
        coverage=coverage, state_density=state_density,
        ambiguity=ambiguity, compression_gain=cg,
        godel_tokens=godel_tokens,
        semantic_drift=drift_val, delta_ep_min=delta_ep,
        active_laws=",".join(state.law_stack.names),
        failure_state=failure_state,
        zone_id=zone_id, heading_byte=hb, cell_pos=cell_pos,
    )


def step_lander(state: SimState) -> Telemetry:
    """Step Lander mode."""
    rng: random.Random = state.extra["rng"]
    dt = state.config.dt
    ship = state.body
    world: Vec2 = state.extra["world"]
    pad_x = state.extra["pad_x"]
    prev_error: list[float] = state.extra["prev_error"]
    fuel = state.resources["fuel"]
    heat = state.resources["heat"]

    prev_vy_error = abs(ship.vel.y - (-1.5))

    if state.config.adaptive and "pid_controller" in state.law_stack.names:
        thrust, attempted = agent_lander_pid(ship, fuel, pad_x, dt, prev_error)
        state.agent_stats.attempted += int(attempted)
        useful = abs(ship.vel.y + 1.5) < prev_vy_error
        state.agent_stats.useful += int(attempted and useful)
        state.agent_stats.moved += int(thrust > 0)
    else:
        ticks = agent_naive(state.step, rng)
        if ticks:
            ship.rotate_quantized(ticks)
        thrust = 3.8 if fuel.value > 0 and state.step % 9 in (0, 1, 2, 3) else 0.0
        state.agent_stats.attempted += 1
        state.agent_stats.moved += int(thrust > 0)
        useful = abs(ship.vel.y) < 3.0
        state.agent_stats.useful += int(thrust > 0 and useful)

    gravity = Vec2(0.0, -1.62)
    drag = 0.01
    fuel.step(dt, sink=0.9 if thrust else 0.0)
    heat.step(dt, source=0.35 if thrust else 0.0)
    arcade_motion_step(ship, dt, thrust, gravity, drag, world, wrap_edges=False)

    crit = max(heat.criticality, state.resources["pressure"].criticality)
    if crit >= 1.0 and ship.state == "active":
        ship.state = "exploded"
        state.agent_stats.failures += 1

    return _build_telemetry(state)


def step_asteroids(state: SimState) -> Telemetry:
    """Step Asteroids mode."""
    rng: random.Random = state.extra["rng"]
    dt = state.config.dt
    ship = state.body
    world: Vec2 = state.extra["world"]
    attractor: Vec2 = state.extra["attractor"]
    fuel = state.resources["fuel"]
    heat = state.resources["heat"]

    ticks = agent_naive(state.step, rng)
    if ticks:
        ship.rotate_quantized(ticks)
        state.agent_stats.attempted += 1
        state.agent_stats.moved += 1
        state.agent_stats.useful += 1

    gravity = central_gravity_well(ship, attractor, gm=85.0)
    thrust = 2.2 if state.step % 11 < 4 else 0.0
    state.agent_stats.attempted += 1
    state.agent_stats.moved += int(thrust > 0)
    # Goal agency: did thrust improve orbital distance stability?
    dist_to_attractor = ship.pos.distance_to(attractor)
    useful = thrust > 0 and 30 < dist_to_attractor < 80
    state.agent_stats.useful += int(useful)

    fuel.step(dt, sink=0.35 if thrust else 0.0)
    heat.step(dt, source=0.25 if thrust else 0.0,
              noise=rng.uniform(-0.02, 0.02))
    arcade_motion_step(ship, dt, thrust, gravity, 0.0, world, wrap_edges=True)

    return _build_telemetry(state)


def step_pressure(state: SimState) -> Telemetry:
    """Step Pressure mode."""
    rng: random.Random = state.extra["rng"]
    dt = state.config.dt
    ship = state.body
    world: Vec2 = state.extra["world"]
    fuel = state.resources["fuel"]
    heat = state.resources["heat"]
    pressure = state.resources["pressure"]
    excess: float = state.extra["excess_integral"]
    peak: float = state.extra["peak_pressure"]

    ticks = agent_naive(state.step, rng)
    if ticks:
        ship.rotate_quantized(ticks)

    thrust = 1.2 if fuel.value > 0 and state.step % 13 < 5 else 0.0
    gravity = Vec2(0.0, -0.4)
    drag = 0.08
    fuel.step(dt, sink=0.25 if thrust else 0.0)
    heat.step(dt, source=0.15 if thrust else 0.0)
    pressure.step(dt, source=state.config.pressure_source,
                  noise=rng.uniform(-0.1, 0.1))

    drilling = (state.config.drill_power
                if state.step in range(70, 95) or state.step in range(155, 180)
                else 0.0)
    sinks = {0: drilling, 1: drilling * 0.5, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
    graph_pressure_diffusion(state.zones, sinks, dt)

    excess, exploded = hysteresis_failure(
        excess, pressure.value, pressure.critical, dt,
    )
    state.extra["excess_integral"] = excess
    peak = max(peak, pressure.value)
    state.extra["peak_pressure"] = peak

    if exploded and ship.state == "active":
        ship.state = "exploded"
        state.agent_stats.failures += 1

    arcade_motion_step(ship, dt, thrust, gravity, drag, world, wrap_edges=False)

    state.agent_stats.attempted += 1
    state.agent_stats.moved += int(thrust > 0 or drilling > 0)
    # Goal agency: did drilling reduce pressure?
    pressure_recovery = max(0, peak - pressure.value) / max(peak - 25.0, 1e-9)
    state.agent_stats.useful += int(drilling > 0 and pressure_recovery > 0.1)

    return _build_telemetry(state)


def step_freescape(state: SimState) -> Telemetry:
    """Step Freescape mode."""
    rng: random.Random = state.extra["rng"]
    dt = state.config.dt
    body = state.body3
    world3: Vec3 = state.extra["world3"]
    fuel = state.resources["fuel"]
    heat = state.resources["heat"]
    pressure = state.resources["pressure"]
    shield = state.resources["shield"]
    excess: float = state.extra["excess_integral"]

    if state.step % 24 == 0:
        body.rotate_quantized(rng.choice([-12, -6, 6, 12]))

    # Zone from position (v4 fix: not timer)
    zone_idx = min(int(body.pos.x / world3.x * len(state.zones)),
                   len(state.zones) - 1)
    body.zone_id = zone_idx
    z = state.zones[zone_idx]

    thrust_active = state.step % 7 < 3
    if thrust_active:
        rad = body.heading_rad
        body.vel.x += math.cos(rad) * 0.15 * z.time_scale
        body.vel.z += math.sin(rad) * 0.15 * z.time_scale

    fuel.step(dt, sink=0.4 if thrust_active else 0.0)
    heat.step(dt, source=0.2 if thrust_active else 0.0)
    motion_step_3d(body, dt, z.gravity, z.friction, world3)

    for c in state.cuboids:
        hit, new_vel = cuboid_collide(body.pos, body.vel, c)
        if hit:
            body.vel = new_vel
            body.collision_count += 1

    graph_pressure_diffusion(state.zones,
                            {zone_idx: 2.0 if thrust_active else 0.0}, dt)
    pressure.value = z.pressure

    if z.pressure > 60:
        shield.step(dt, sink=0.5)
    else:
        shield.step(dt, source=0.1)

    excess, exploded = hysteresis_failure(excess, pressure.value,
                                           pressure.critical, dt)
    state.extra["excess_integral"] = excess
    if exploded and body.state == "active":
        body.state = "exploded"
        state.agent_stats.failures += 1

    # Hydraulic height lift
    if body.pos.y < 2.0 and z.id == 3:
        body.vel.y = 3.0

    state.agent_stats.attempted += 1
    state.agent_stats.moved += int(thrust_active)
    useful = (body.pos.distance_to(body.last_pos) > 0.3
              or body.collision_count > state.extra.get("prev_collisions", 0))
    state.agent_stats.useful += int(useful)
    state.extra["prev_collisions"] = body.collision_count

    return _build_telemetry(state)


def step_colony(state: SimState) -> Telemetry:
    """Step Colony mode."""
    rng: random.Random = state.extra["rng"]
    dt = state.config.dt
    cx: int = state.extra["cx"]
    cy: int = state.extra["cy"]
    heading: int = state.extra["heading"]
    gw: int = state.extra["grid_w"]
    gh: int = state.extra["grid_h"]
    grid = state.grid
    suit = state.resources["suit"]
    fuel = state.resources["fuel"]
    heat = state.resources["heat"]

    moved = False
    if state.step % 6 == 0:
        if state.config.adaptive and "wall_following_agent" in state.law_stack.names:
            new_cx, new_cy, dh, moved = agent_colony_wall_follow(
                cx, cy, heading, grid, gw, gh,
            )
        else:
            sector = (heading + 32) % 256 // 64
            dx, dy, wall_key = SECTOR_DIRS[sector]
            cell = grid.get((cx, cy))
            if cell and not cell.walls.get(wall_key, True):
                nx, ny = (cx + dx) % gw, (cy + dy) % gh
                target = grid.get((nx, ny))
                if target and target.teleport_to is not None:
                    new_cx, new_cy, dh, moved = target.teleport_to[0], target.teleport_to[1], 0, True
                else:
                    new_cx, new_cy, dh, moved = nx, ny, 0, True
            else:
                new_cx, new_cy, dh, moved = cx, cy, 16, False

        if moved and new_cx != cx or new_cy != cy:
            state.visited_cells.add((new_cx, new_cy))
        heading = (heading + dh) % 256
        state.extra["cx"] = new_cx
        state.extra["cy"] = new_cy
        state.extra["heading"] = heading

        if moved:
            state.agent_stats.moved += 1
        else:
            state.agent_stats.blocked += 1
        state.agent_stats.attempted += 1
        # Goal agency: new cell visited
        state.agent_stats.useful += int(
            moved and (new_cx, new_cy) in state.visited_cells
        )

    if state.step % 18 == 0:
        heading = (heading + rng.choice([-16, -8, 8, 16])) % 256
        state.extra["heading"] = heading

    # Energy station
    cur_cx, cur_cy = state.extra["cx"], state.extra["cy"]
    cell = grid.get((cur_cx, cur_cy))
    if cell and cell.energy_station:
        suit.step(dt, source=3.0)
    suit.step(dt)
    fuel.step(dt, sink=0.1)
    heat.step(dt, source=0.05)

    if suit.is_critical():
        state.agent_stats.failures += 1

    return _build_telemetry(state)


def step_semantic(state: SimState) -> Telemetry:
    """Step Semantic mode -- live cross-mode analytics."""
    dt = state.config.dt
    results: dict = state.extra.get("mode_results", {})

    # Simulate a tiny version of each mode every step cycle
    mode_idx = state.step % 6
    mode_name = BASE_MODES[mode_idx]
    mini_config = SimConfig(dt=dt, max_steps=1)
    mini_state = make_state(mode_name, state.seed, mini_config)
    mini_state.hdc = None  # no nested HDC
    t = step_sim(mini_state)
    results[mode_name] = {
        "pr": t.pr_norm,
        "agency": t.goal_agency,
        "law_cost": t.law_cost,
        "coverage": t.coverage,
    }
    state.extra["mode_results"] = results

    # Semantic: aggregate stats
    avg_pr = sum(r["pr"] for r in results.values()) / max(len(results), 1)
    return Telemetry(
        step=state.step, mode="semantic", seed=state.seed,
        pr=avg_pr, pr_norm=avg_pr,
        law_cost=sum(r["law_cost"] for r in results.values()) / max(len(results), 1),
        law_count=4,
        state_density=len(results) / 6.0,
        goal_agency=sum(r["agency"] for r in results.values()) / max(len(results), 1),
        coverage=sum(r["coverage"] for r in results.values()) / max(len(results), 1),
        active_laws="playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",
        failure_state="active",
    )


def step_sim(state: SimState) -> Telemetry:
    """Dispatch to the correct step function."""
    step_fn = {
        "lander": step_lander,
        "asteroids": step_asteroids,
        "pressure": step_pressure,
        "freescape": step_freescape,
        "colony": step_colony,
        "semantic": step_semantic,
    }.get(state.mode)

    if step_fn is None:
        raise ValueError(f"No step function for mode: {state.mode}")

    t = step_fn(state)
    state.step += 1
    state.history.append(t)
    return t


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Simulation Runner
# ═══════════════════════════════════════════════════════════════════════════════


def run_sim(
    mode: str, seed: int, steps: int,
    config: SimConfig | None = None,
    dlas: DLASc | None = None,
) -> list[Telemetry]:
    """Run a full simulation and return telemetry list."""
    if config is None:
        config = SimConfig(max_steps=steps)
    state = make_state(mode, seed, config)
    out: list[Telemetry] = []

    for _ in range(steps + 1):
        t = step_sim(state)
        # DLASc adaptive tick
        if dlas is not None and config.adaptive and state.step % 10 == 0:
            changes = dlas.tick(state, t)
            if changes:
                t.events = " ".join(changes)
        out.append(t)

        # Early exit on failure (stress mode)
        if config.stress and t.failure_state != "active":
            break

    return out


def final_pr(telemetry: list[Telemetry]) -> float:
    """Get the final PR_norm from a telemetry list."""
    return telemetry[-1].pr_norm if telemetry else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 15. Audit and Optimizer Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def estimate_law_contribution(
    mode: str, seed: int, config: SimConfig,
    law: str, window: int = 80,
) -> float:
    """Cheap ablation: PR_full - PR_without_law."""
    baseline = run_sim(mode, seed, window, config)
    patched_config = SimConfig(
        dt=config.dt, adaptive=config.adaptive,
        agent_policy=config.agent_policy,
        wall_density=config.wall_density,
        hdc_dim=config.hdc_dim, max_steps=window,
    )
    # Create state and remove the law
    state = make_state(mode, seed, patched_config)
    if law in state.law_stack.names:
        state.law_stack.remove(law)
    # Run manually
    out: list[Telemetry] = []
    for _ in range(window + 1):
        t = step_sim(state)
        out.append(t)
        if t.failure_state != "active":
            break
    return final_pr(baseline) - final_pr(out)


def audit_mode(
    mode: str, seed: int, steps: int,
    config: SimConfig | None = None,
) -> dict[str, Any]:
    """Compute per-law contribution analysis for a mode."""
    if config is None:
        config = SimConfig(max_steps=steps)
    state = make_state(mode, seed, config)
    dlas = DLASc(LAW_REGISTRY)

    for _ in range(steps + 1):
        t = step_sim(state)
        if config.adaptive and state.step % 10 == 0:
            dlas.tick(state, t)
        # Track which laws executed
        for ln in state.law_stack.names:
            dlas.record_execution(ln)
        if t.failure_state != "active":
            break

    contributions: dict[str, dict[str, Any]] = {}
    for law in state.law_stack.names:
        contrib = estimate_law_contribution(mode, seed, config, law, window=min(steps, 80))
        contributions[law] = {
            "contribution": round(contrib, 4),
            "executed": dlas.execution_counts[law] > 0,
            "execution_count": dlas.execution_counts[law],
            "verdict": "keep" if contrib > 0 else "remove",
        }

    dead_laws = [
        name for name, info in contributions.items()
        if info["contribution"] <= 0 or not info["executed"]
    ]
    total_cost = state.law_stack.cost(LAW_REGISTRY)

    return {
        "mode": mode,
        "seed": seed,
        "steps": len(state.history),
        "final_pr": round(final_pr(state.history), 4),
        "final_pr_norm": round(state.history[-1].pr_norm if state.history else 0, 4),
        "law_cost": round(total_cost, 2),
        "law_count": state.law_stack.count(),
        "coverage": round(state.history[-1].coverage if state.history else 0, 4),
        "goal_agency": round(state.history[-1].goal_agency if state.history else 0, 4),
        "contributions": contributions,
        "dead_laws": dead_laws,
        "active_laws": state.law_stack.names,
    }


def optimize_mode(
    mode: str, seed: int, episodes: int,
    config: SimConfig | None = None,
) -> dict[str, Any]:
    """Grid search over wall_density and agent_policy."""
    if config is None:
        config = SimConfig()
    best_pr = -1.0
    best_params: dict[str, Any] = {}
    results: list[dict] = []

    densities = [0.30, 0.40, 0.45, 0.55, 0.65]
    policies = ["naive", "wall_follow"]

    for ep in range(episodes):
        ep_seed = seed + ep
        for wd in densities:
            for pol in policies:
                cfg = SimConfig(
                    dt=config.dt,
                    adaptive=(pol != "naive"),
                    agent_policy=pol,
                    wall_density=wd,
                    max_steps=config.max_steps,
                    hdc_dim=config.hdc_dim,
                )
                tel = run_sim(mode, ep_seed, config.max_steps, cfg)
                pr = final_pr(tel)
                ag = tel[-1].goal_agency if tel else 0
                cov = tel[-1].coverage if tel else 0
                lc = tel[-1].law_cost if tel else 0
                results.append({
                    "episode": ep, "seed": ep_seed,
                    "wall_density": wd, "policy": pol,
                    "pr": round(pr, 4), "agency": round(ag, 4),
                    "coverage": round(cov, 4), "law_cost": round(lc, 2),
                })
                if pr > best_pr:
                    best_pr = pr
                    best_params = {
                        "wall_density": wd, "policy": pol,
                        "seed": ep_seed, "pr": round(pr, 4),
                    }

    results.sort(key=lambda r: r["pr"], reverse=True)
    return {
        "mode": mode,
        "episodes": episodes,
        "best_params": best_params,
        "best_pr": round(best_pr, 4),
        "top_5": results[:5],
        "all_results": results,
    }


def stress_mode(
    mode: str, seed: int, max_steps: int,
    config: SimConfig | None = None,
) -> dict[str, Any]:
    """Run until failure or max_steps. Measure TTF."""
    if config is None:
        config = SimConfig(max_steps=max_steps, stress=True)
    else:
        config = SimConfig(
            dt=config.dt, adaptive=config.adaptive,
            agent_policy=config.agent_policy,
            wall_density=config.wall_density,
            hdc_dim=config.hdc_dim,
            max_steps=max_steps, stress=True,
        )
    tel = run_sim(mode, seed, max_steps, config)
    ttf = len(tel)
    failed = any(t.failure_state != "active" for t in tel)
    failure_step = next(
        (t.step for t in tel if t.failure_state != "active"),
        -1,
    )
    failure_reason = ""
    if failed:
        ft = next(t for t in tel if t.failure_state != "active")
        failure_reason = ft.failure_state

    return {
        "mode": mode,
        "seed": seed,
        "ttf": ttf,
        "max_steps": max_steps,
        "failed": failed,
        "failure_step": failure_step,
        "failure_reason": failure_reason,
        "final_pr": round(final_pr(tel), 4) if tel else 0,
        "final_coverage": round(tel[-1].coverage, 4) if tel else 0,
        "final_agency": round(tel[-1].goal_agency, 4) if tel else 0,
        "telemetry_count": len(tel),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 16. Campaign Runners
# ═══════════════════════════════════════════════════════════════════════════════


def run_campaign_baseline(
    seed: int, steps: int,
    config: SimConfig | None = None,
) -> dict[str, list[Telemetry]]:
    """Run all modes with minimal static stacks."""
    if config is None:
        config = SimConfig(adaptive=False, max_steps=steps)
    else:
        config = SimConfig(
            dt=config.dt, adaptive=False,
            agent_policy=config.agent_policy,
            wall_density=config.wall_density,
            hdc_dim=config.hdc_dim, max_steps=steps,
        )
    results: dict[str, list[Telemetry]] = {}
    for mode in BASE_MODES:
        results[mode] = run_sim(mode, seed, steps, config)
    return results


def run_campaign_adaptive(
    seed: int, steps: int,
    config: SimConfig | None = None,
) -> dict[str, list[Telemetry]]:
    """Run all modes with DLASc + HDC tokens enabled."""
    if config is None:
        config = SimConfig(adaptive=True, max_steps=steps)
    else:
        config = SimConfig(
            dt=config.dt, adaptive=True,
            agent_policy=config.agent_policy,
            wall_density=config.wall_density,
            hdc_dim=config.hdc_dim, max_steps=steps,
        )
    results: dict[str, list[Telemetry]] = {}
    for mode in BASE_MODES:
        dlas = DLASc(LAW_REGISTRY)
        results[mode] = run_sim(mode, seed, steps, config, dlas=dlas)
    return results


def run_campaign_stress(
    mode: str, seed: int, max_steps: int,
    config: SimConfig | None = None,
) -> dict[str, dict[str, Any]]:
    """Stress test a single mode across multiple seeds."""
    if config is None:
        config = SimConfig(adaptive=True, stress=True)
    results: dict[str, dict[str, Any]] = {}
    for s in range(seed, seed + 5):
        results[f"seed_{s}"] = stress_mode(mode, s, max_steps, config)
    return results


def run_campaign_audit(
    mode: str, seed: int, steps: int,
    config: SimConfig | None = None,
) -> dict[str, Any]:
    """Full audit of a single mode."""
    return audit_mode(mode, seed, steps, config)


def run_campaign_optimize(
    mode: str, seed: int, episodes: int,
    config: SimConfig | None = None,
) -> dict[str, Any]:
    """Optimize parameters for a single mode."""
    return optimize_mode(mode, seed, episodes, config)


def run_campaign_compare(
    seed: int, steps: int,
    config: SimConfig | None = None,
) -> dict[str, dict[str, Any]]:
    """Compare baseline vs adaptive vs optimized for all modes."""
    if config is None:
        config = SimConfig(max_steps=steps)
    baseline = run_campaign_baseline(seed, steps, config)
    adaptive = run_campaign_adaptive(seed, steps, config)

    comparison: dict[str, dict[str, Any]] = {}
    for mode in BASE_MODES:
        bl = baseline[mode]
        ad = adaptive[mode]

        # Quick optimization (fewer episodes)
        opt = optimize_mode(mode, seed, episodes=10,
                           config=SimConfig(
                               dt=config.dt, max_steps=steps,
                               wall_density=config.wall_density,
                               hdc_dim=config.hdc_dim,
                           ))

        comparison[mode] = {
            "pr_base": round(final_pr(bl), 4),
            "pr_adapt": round(final_pr(ad), 4),
            "pr_opt": round(opt["best_pr"], 4),
            "delta_opt": round(opt["best_pr"] - final_pr(bl), 4),
            "agency_base": round(bl[-1].goal_agency, 4) if bl else 0,
            "agency_adapt": round(ad[-1].goal_agency, 4) if ad else 0,
            "coverage_base": round(bl[-1].coverage, 4) if bl else 0,
            "coverage_adapt": round(ad[-1].coverage, 4) if ad else 0,
            "law_cost_base": round(bl[-1].law_cost, 2) if bl else 0,
            "law_cost_adapt": round(ad[-1].law_cost, 2) if ad else 0,
            "best_params": opt.get("best_params", {}),
            "dead_laws": opt.get("best_params", {}),
        }

    return {"baseline": baseline, "adaptive": adaptive, "comparison": comparison}


# ═══════════════════════════════════════════════════════════════════════════════
# 17. Export Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def write_csv(telemetry: list[Telemetry], path: str) -> None:
    """Write telemetry to CSV."""
    if not telemetry:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=telemetry[0].csv_row().keys())
        writer.writeheader()
        for t in telemetry:
            writer.writerow(t.csv_row())


def write_json(summary: dict[str, Any], path: str) -> None:
    """Write summary to JSON."""
    with open(path, "w") as f:
        json.dump(summary, f, indent=2, default=str)


def write_markdown_report(
    data: dict[str, Any], path: str,
) -> None:
    """Write a markdown report from campaign/compare results."""
    lines: list[str] = []
    lines.append("# RGPUF Lab v4 -- Micro-World Forge Report\n")
    lines.append("core: rgpuf_core.py | demo: rgpuf_lab_v4.py\n")

    if "comparison" in data:
        lines.append("\n## Mode Comparison\n")
        lines.append("")
        header = (
            f"{'MODE':<12} {'PR_BASE':>8} {'PR_ADAPT':>8} {'PR_OPT':>8} "
            f"{'DELTA':>7} {'AGENCY':>7} {'COVER':>6} {'LAW_COST':>8}\n"
        )
        lines.append(header)
        lines.append("-" * len(header))

        for mode, info in data["comparison"].items():
            lines.append(
                f"{mode:<12} {info['pr_base']:8.3f} {info['pr_adapt']:8.3f} "
                f"{info['pr_opt']:8.3f} {info['delta_opt']:+7.3f} "
                f"{info['agency_adapt']:7.2f} {info['coverage_adapt']:6.2f} "
                f"{info['law_cost_adapt']:8.1f}"
            )

    # Law contribution sections
    if "baseline" in data:
        lines.append("\n## Detailed Mode Analysis\n")
        for mode in BASE_MODES:
            tel = data["baseline"].get(mode, [])
            if not tel:
                continue
            last = tel[-1]
            lines.append(f"\n### {mode}\n")
            lines.append(f"- Final PR (normalized): {last.pr_norm:.4f}")
            lines.append(f"- Final PR (raw): {last.pr:.4f}")
            lines.append(f"- Goal Agency: {last.goal_agency:.4f}")
            lines.append(f"- Coverage: {last.coverage:.4f}")
            lines.append(f"- Law Cost: {last.law_cost:.2f}")
            lines.append(f"- Laws: {last.active_laws}")
            lines.append(f"- Gödel Tokens: {last.godel_tokens}")
            lines.append(f"- Failure: {last.failure_state}")

    # Best micro-world recipe
    if "comparison" in data:
        lines.append("\n## Best Micro-World Recipes\n")
        for mode, info in data["comparison"].items():
            bp = info.get("best_params", {})
            if bp:
                lines.append(f"\n### {mode.title()}\n")
                lines.append(f"- Seed: {bp.get('seed', '?')}")
                lines.append(f"- Wall Density: {bp.get('wall_density', '?')}")
                lines.append(f"- Policy: {bp.get('policy', '?')}")
                lines.append(f"- PR: {bp.get('pr', '?')}")

    with open(path, "w") as f:
        f.write("\n".join(lines))


# ═══════════════════════════════════════════════════════════════════════════════
# 18. Display Utilities
# ═══════════════════════════════════════════════════════════════════════════════


def sparkline(v: float, w: int = 14, mx: float = 1.0) -> str:
    f = int(round(clamp(v / max(mx, 1e-9), 0, 1) * w))
    return "\u2588" * f + "\u2591" * (w - f)


def print_telemetry(t: Telemetry, interval: int = 12) -> None:
    """Print a telemetry frame to terminal."""
    if t.step % interval != 0:
        return
    if t.mode == "colony":
        line = (
            f"t={t.step:03d} {t.mode:<9} cell={t.cell_pos} h={t.heading_byte:03d} "
            f"suit={t.suit:5.1f} ag_act={t.action_agency:.2f} ag_goal={t.goal_agency:.2f} "
            f"cov={t.coverage:.2f} PR={t.pr_norm:.3f} cost={t.law_cost:.1f}"
        )
    elif t.mode == "freescape":
        line = (
            f"t={t.step:03d} {t.mode:<9} z={t.zone_id:02d} "
            f"({t.x:5.1f},{t.y:5.1f},{t.z:4.1f}) spd={t.speed:5.2f} "
            f"ag={t.goal_agency:.2f} PR={t.pr_norm:.3f} laws={t.law_count}"
        )
    else:
        line = (
            f"t={t.step:03d} {t.mode:<9} "
            f"({t.x:6.1f},{t.y:6.1f}) spd={t.speed:6.2f} "
            f"ag={t.goal_agency:.2f} PR={t.pr_norm:.3f} "
            f"fals={t.falsifiability:.2f} cost={t.law_cost:.1f}"
        )
    if t.godel_tokens > 0:
        line += f" \u26a0{t.godel_tokens}"
    if t.events:
        line += f" [{t.events}]"
    print(line)
```

## rgpuf_lab_v4.py
```
#!/usr/bin/env python3
"""
rgpuf_lab_v4.py
================

Next-level RGPUF demo using rgpuf_core.py.

RGPUF Lab v4 -- Micro-World Forge

Runs campaign experiments:
- baseline vs adaptive
- per-mode audit
- law contribution analysis
- stress/failure envelope
- optimizer search
- micro-world recipe extraction

This file should stay thin. All reusable mechanics live in rgpuf_core.py.

Run:
    python rgpuf_lab_v4.py --campaign compare --steps 240 --seed 42
    python rgpuf_lab_v4.py --campaign audit --mode colony --steps 240
    python rgpuf_lab_v4.py --campaign stress --mode pressure --max-steps 2000
    python rgpuf_lab_v4.py --campaign optimize --mode colony --episodes 30
    python rgpuf_lab_v4.py --campaign baseline --steps 240 --csv telemetry.csv
    python rgpuf_lab_v4.py --campaign compare --report report.md
"""

from __future__ import annotations

import argparse
import sys
import time

from rgpuf_core import (
    BASE_MODES,
    LAW_REGISTRY,
    SimConfig,
    Telemetry,
    audit_mode,
    optimize_mode,
    print_telemetry,
    run_campaign_adaptive,
    run_campaign_audit,
    run_campaign_baseline,
    run_campaign_compare,
    run_campaign_optimize,
    run_campaign_stress,
    run_sim,
    stress_mode,
    write_csv,
    write_json,
    write_markdown_report,
    final_pr,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Result Printers
# ═══════════════════════════════════════════════════════════════════════════════


def print_comparison_table(comparison: dict) -> None:
    """Print the v4 comparison table to terminal."""
    print()
    print("RGPUF Lab v4 -- Micro-World Forge")
    print("core: rgpuf_core.py | demo: rgpuf_lab_v4.py")
    print()
    header = (
        f"{'MODE':<12} {'PR_BASE':>8} {'PR_ADAPT':>8} {'PR_OPT':>8} "
        f"{'DELTA':>7} {'AGENCY':>7} {'COVER':>6} {'LAW_COST':>8} {'LAWS':>5}"
    )
    print(header)
    print("-" * len(header))

    for mode, info in comparison.items():
        pr_base = info.get("pr_base", 0)
        pr_adapt = info.get("pr_adapt", 0)
        pr_opt = info.get("pr_opt", 0)
        delta = info.get("delta_opt", 0)
        agency = info.get("agency_adapt", 0)
        cover = info.get("coverage_adapt", 0)
        cost = info.get("law_cost_adapt", 0)

        print(
            f"{mode:<12} {pr_base:8.3f} {pr_adapt:8.3f} {pr_opt:8.3f} "
            f"{delta:+7.3f} {agency:7.2f} {cover:6.2f} {cost:8.1f} "
            f"{'N/A':>5}"
        )


def print_audit_results(audit: dict) -> None:
    """Print audit results for a mode."""
    print()
    print(f"AUDIT -- {audit['mode']}")
    print(f"  Final PR_norm:  {audit['final_pr_norm']:.4f}")
    print(f"  Law Cost:       {audit['law_cost']:.2f}")
    print(f"  Law Count:      {audit['law_count']}")
    print(f"  Coverage:       {audit['coverage']:.4f}")
    print(f"  Goal Agency:    {audit['goal_agency']:.4f}")
    print(f"  Active Laws:    {', '.join(audit['active_laws'])}")
    print()
    print(f"  LAW CONTRIBUTION -- {audit['mode']}")
    print(f"  {'law':<30} {'contribution':>12} {'executed':>9} {'verdict':>8}")
    print(f"  {'-'*61}")

    for law, info in audit["contributions"].items():
        contrib = info["contribution"]
        executed = "yes" if info["executed"] else "no"
        verdict = info["verdict"]
        print(f"  {law:<30} {contrib:+12.4f} {executed:>9} {verdict:>8}")

    if audit["dead_laws"]:
        print(f"\n  Dead laws (recommended removal): {', '.join(audit['dead_laws'])}")
    else:
        print(f"\n  No dead laws detected.")


def print_stress_results(results: dict) -> None:
    """Print stress test results."""
    print()
    print("STRESS TEST RESULTS")
    print(f"  {'Seed':>8} {'TTF':>6} {'Failed':>7} {'Reason':>10} {'PR':>8} {'Agency':>7}")
    print(f"  {'-'*52}")

    for seed_key, info in results.items():
        print(
            f"  {seed_key:>8} {info['ttf']:6d} "
            f"{'yes' if info['failed'] else 'no':>7} "
            f"{info['failure_reason']:>10} "
            f"{info['final_pr']:8.4f} {info['final_agency']:7.4f}"
        )


def print_optimize_results(opt: dict) -> None:
    """Print optimization results."""
    print()
    print(f"OPTIMIZER -- {opt['mode']}")
    print(f"  Episodes: {opt['episodes']}")
    print(f"  Best PR: {opt['best_pr']:.4f}")
    bp = opt["best_params"]
    print(f"  Best Params:")
    print(f"    wall_density: {bp.get('wall_density', '?')}")
    print(f"    policy:       {bp.get('policy', '?')}")
    print(f"    seed:         {bp.get('seed', '?')}")
    print()
    print(f"  TOP 5 CONFIGURATIONS:")
    print(f"  {'#':>3} {'seed':>6} {'wall_d':>7} {'policy':>12} {'PR':>8} {'agency':>7} {'cover':>6}")
    print(f"  {'-'*54}")
    for i, r in enumerate(opt.get("top_5", [])):
        print(
            f"  {i+1:>3} {r['seed']:6d} {r['wall_density']:7.2f} "
            f"{r['policy']:>12} {r['pr']:8.4f} {r['agency']:7.4f} {r['coverage']:6.4f}"
        )


def print_baseline_results(results: dict) -> None:
    """Print baseline campaign results."""
    print()
    print("BASELINE CAMPAIGN RESULTS")
    print(f"  {'MODE':<12} {'PR_norm':>8} {'PR_raw':>8} {'Agency':>7} "
          f"{'Coverage':>8} {'LawCost':>8} {'Laws':>5}")
    print(f"  {'-'*60}")

    for mode in BASE_MODES:
        tel = results.get(mode, [])
        if tel:
            last = tel[-1]
            print(
                f"  {mode:<12} {last.pr_norm:8.4f} {last.pr:8.4f} "
                f"{last.goal_agency:7.4f} {last.coverage:8.4f} "
                f"{last.law_cost:8.2f} {last.law_count:5d}"
            )


def print_adaptive_results(results: dict) -> None:
    """Print adaptive campaign results."""
    print()
    print("ADAPTIVE CAMPAIGN RESULTS (DLASc + HDC)")
    print(f"  {'MODE':<12} {'PR_norm':>8} {'PR_raw':>8} {'Agency':>7} "
          f"{'Coverage':>8} {'LawCost':>8} {'Godel':>6}")
    print(f"  {'-'*60}")

    for mode in BASE_MODES:
        tel = results.get(mode, [])
        if tel:
            last = tel[-1]
            print(
                f"  {mode:<12} {last.pr_norm:8.4f} {last.pr:8.4f} "
                f"{last.goal_agency:7.4f} {last.coverage:8.4f} "
                f"{last.law_cost:8.2f} {last.godel_tokens:6d}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Micro-World Recipe Extraction
# ═══════════════════════════════════════════════════════════════════════════════


def extract_recipe(
    mode: str, seed: int, steps: int, config: SimConfig,
) -> dict:
    """Extract a micro-world recipe from an optimized run."""
    from rgpuf_core import run_sim, DLASc, make_state, step_sim

    # Run with adaptive to discover laws
    dlas = DLASc(LAW_REGISTRY)
    tel = run_sim(mode, seed, steps, config, dlas=dlas)

    last = tel[-1] if tel else None
    if not last:
        return {"mode": mode, "error": "no telemetry"}

    # Find failure boundary
    failure_step = -1
    failure_reason = "none"
    for t in tel:
        if t.failure_state != "active":
            failure_step = t.step
            failure_reason = t.failure_state
            break

    # Build recipe
    recipe = {
        "name": f"{mode.title()} Escape",
        "mode": mode,
        "seed": seed,
        "law_stack": last.active_laws.split(","),
        "agent_policy": config.agent_policy if config.adaptive else "naive",
        "goal": "maximize_coverage" if mode == "colony" else "maximize_pr",
        "failure": failure_reason if failure_step >= 0 else "none",
        "failure_step": failure_step,
        "topology": "cell_torus" if mode == "colony" else "continuous",
        "results": {
            "laws": len(last.active_laws.split(",")),
            "law_cost": round(last.law_cost, 2),
            "pr_norm": round(last.pr_norm, 4),
            "pr_raw": round(last.pr, 4),
            "coverage": round(last.coverage, 4),
            "goal_agency": round(last.goal_agency, 4),
            "godel_tokens": last.godel_tokens,
        },
    }

    # Count dead laws (from DLASc contribution tracking)
    dead = []
    for law in last.active_laws.split(","):
        if dlas.execution_counts.get(law, 0) == 0:
            dead.append(law)
        elif dlas.contribution_scores.get(law, 0) < -0.05:
            dead.append(law)
    recipe["dead_laws_removed"] = dead
    recipe["results"]["dead_count"] = len(dead)

    return recipe


def print_recipe(recipe: dict) -> None:
    """Print a micro-world recipe."""
    print()
    print("BEST MICRO-WORLD RECIPE")
    print(f"  Name:            {recipe['name']}")
    print(f"  Mode:            {recipe['mode']}")
    print(f"  Seed:            {recipe['seed']}")
    r = recipe["results"]
    print(f"  Laws:            {r['laws']}")
    print(f"  LawCost:         {r['law_cost']}")
    print(f"  PR_norm:         {r['pr_norm']}")
    print(f"  Coverage:        {r['coverage']}")
    print(f"  Failure:         {recipe['failure']} at T={recipe['failure_step']}")
    if recipe["dead_laws_removed"]:
        print(f"  Dead Laws:       {', '.join(recipe['dead_laws_removed'])}")
    print(f"  Law Stack:       {', '.join(recipe['law_stack'])}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Automatic Diagnosis
# ═══════════════════════════════════════════════════════════════════════════════


def print_diagnosis(mode: str, baseline_pr: float, adaptive_pr: float,
                    adaptive_tel: list[Telemetry]) -> None:
    """Print automatic diagnosis of mode improvements."""
    last = adaptive_tel[-1] if adaptive_tel else None
    if not last:
        return

    print()
    print(f"DIAGNOSIS -- {mode}")
    print(f"  Problem in v3:")
    print(f"    - PR was crushed by global registry law cost.")
    print(f"    - Agency was inflated by action success instead of goal success.")
    if mode == "colony":
        print(f"    - Cell movement improved but coverage remained low.")
        print(f"    - Teleport law was present but rarely executed.")
    elif mode == "pressure":
        print(f"    - Agency was false-perfect because actions counted even when pressure rose.")
        print(f"    - Hysteresis excess never decayed.")
    elif mode == "freescape":
        print(f"    - Zone changes were on timer, not position.")
    elif mode == "semantic":
        print(f"    - Metrics computed once then repeated -- no live data.")

    print(f"\n  v4 repair:")
    print(f"    - LawStack now counts only executed mode laws (cost: {last.law_cost:.1f}).")
    print(f"    - Goal agency uses mode-specific useful action criteria.")
    print(f"    - HDC anomalies buy repair trials via Gödel tokens.")
    print(f"    - State density measured from unique signatures.")
    print(f"    - Prediction error from transition-based predictor.")

    delta = adaptive_pr - baseline_pr
    print(f"\n  Result:")
    print(f"    PR_norm: {baseline_pr:.3f} -> {adaptive_pr:.3f} ({delta:+.3f})")
    print(f"    LawCost: N/A -> {last.law_cost:.1f}")
    print(f"    Coverage: N/A -> {last.coverage:.2f}")
    print(f"    Goal Agency: N/A -> {last.goal_agency:.2f}")
    print(f"    Gödel Tokens: {last.godel_tokens}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CLI
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="RGPUF Lab v4 -- Micro-World Forge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Campaigns:
  baseline   Run all modes with minimal static stacks
  adaptive   Run all modes with DLASc + HDC enabled
  stress     Run until failure or max steps
  audit      Compute law contribution and dead laws
  optimize   Grid search over parameters
  compare    Run baseline vs adaptive vs optimized

Examples:
  python rgpuf_lab_v4.py --campaign compare --steps 240 --seed 42
  python rgpuf_lab_v4.py --campaign audit --mode colony --steps 240
  python rgpuf_lab_v4.py --campaign stress --mode pressure --max-steps 2000
  python rgpuf_lab_v4.py --campaign optimize --mode colony --episodes 30
  python rgpuf_lab_v4.py --campaign baseline --steps 240 --csv telemetry.csv
  python rgpuf_lab_v4.py --campaign compare --report report.md
        """,
    )
    parser.add_argument(
        "--campaign", default="compare",
        choices=["baseline", "adaptive", "stress", "audit", "optimize", "compare"],
        help="Which campaign to run (default: compare)",
    )
    parser.add_argument(
        "--mode", default="colony",
        choices=BASE_MODES,
        help="Target mode for audit/stress/optimize (default: colony)",
    )
    parser.add_argument(
        "--steps", type=int, default=240,
        help="Number of simulation steps (default: 240)",
    )
    parser.add_argument(
        "--max-steps", type=int, default=2000,
        help="Max steps for stress testing (default: 2000)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--episodes", type=int, default=30,
        help="Number of optimization episodes (default: 30)",
    )
    parser.add_argument(
        "--csv", default=None,
        help="Output CSV file path",
    )
    parser.add_argument(
        "--json", default=None,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--report", default=None,
        help="Output Markdown report path",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress terminal output (except final results)",
    )
    args = parser.parse_args()

    config = SimConfig(
        max_steps=args.steps,
        wall_density=0.45,
        hdc_dim=1024,
    )

    t0 = time.time()

    # ---- BASELINE ----
    if args.campaign == "baseline":
        print(f"Running baseline campaign: {args.steps} steps, seed={args.seed}")
        results = run_campaign_baseline(args.seed, args.steps, config)

        # Print live telemetry (sampled)
        if not args.quiet:
            for mode in BASE_MODES:
                for t in results[mode]:
                    print_telemetry(t, interval=48)

        print_baseline_results(results)

        # Export
        all_tel = []
        for mode in BASE_MODES:
            all_tel.extend(results[mode])
        if args.csv:
            write_csv(all_tel, args.csv)
            print(f"\n  CSV written to {args.csv}")
        if args.json:
            summary = {
                mode: {
                    "pr_norm": results[mode][-1].pr_norm if results[mode] else 0,
                    "pr_raw": results[mode][-1].pr if results[mode] else 0,
                    "goal_agency": results[mode][-1].goal_agency if results[mode] else 0,
                    "coverage": results[mode][-1].coverage if results[mode] else 0,
                    "law_cost": results[mode][-1].law_cost if results[mode] else 0,
                    "active_laws": results[mode][-1].active_laws if results[mode] else "",
                }
                for mode in BASE_MODES
            }
            write_json(summary, args.json)
            print(f"  JSON written to {args.json}")

    # ---- ADAPTIVE ----
    elif args.campaign == "adaptive":
        print(f"Running adaptive campaign: {args.steps} steps, seed={args.seed}")
        results = run_campaign_adaptive(args.seed, args.steps, config)

        if not args.quiet:
            for mode in BASE_MODES:
                for t in results[mode]:
                    print_telemetry(t, interval=48)

        print_adaptive_results(results)

        all_tel = []
        for mode in BASE_MODES:
            all_tel.extend(results[mode])
        if args.csv:
            write_csv(all_tel, args.csv)
            print(f"\n  CSV written to {args.csv}")
        if args.json:
            summary = {
                mode: {
                    "pr_norm": results[mode][-1].pr_norm if results[mode] else 0,
                    "godel_tokens": results[mode][-1].godel_tokens if results[mode] else 0,
                    "active_laws": results[mode][-1].active_laws if results[mode] else "",
                }
                for mode in BASE_MODES
            }
            write_json(summary, args.json)
            print(f"  JSON written to {args.json}")

    # ---- STRESS ----
    elif args.campaign == "stress":
        print(f"Running stress test: mode={args.mode}, max_steps={args.max_steps}, seed={args.seed}")
        results = run_campaign_stress(args.mode, args.seed, args.max_steps, config)
        print_stress_results(results)

        if args.json:
            write_json(results, args.json)
            print(f"\n  JSON written to {args.json}")

    # ---- AUDIT ----
    elif args.campaign == "audit":
        print(f"Running audit: mode={args.mode}, steps={args.steps}, seed={args.seed}")
        audit = run_campaign_audit(args.mode, args.seed, args.steps, config)
        print_audit_results(audit)

        if args.json:
            write_json(audit, args.json)
            print(f"\n  JSON written to {args.json}")

    # ---- OPTIMIZE ----
    elif args.campaign == "optimize":
        print(f"Running optimizer: mode={args.mode}, episodes={args.episodes}, seed={args.seed}")
        opt = run_campaign_optimize(args.mode, args.seed, args.episodes, config)
        print_optimize_results(opt)

        # Also extract best recipe
        if opt["best_params"]:
            bp = opt["best_params"]
            best_cfg = SimConfig(
                adaptive=(bp.get("policy", "naive") != "naive"),
                agent_policy=bp.get("policy", "naive"),
                wall_density=bp.get("wall_density", 0.45),
                max_steps=args.steps,
                hdc_dim=config.hdc_dim,
            )
            recipe = extract_recipe(
                args.mode, bp.get("seed", args.seed),
                args.steps, best_cfg,
            )
            print_recipe(recipe)

        if args.json:
            write_json(opt, args.json)
            print(f"\n  JSON written to {args.json}")

    # ---- COMPARE ----
    elif args.campaign == "compare":
        print(f"Running comparison campaign: {args.steps} steps, seed={args.seed}")
        data = run_campaign_compare(args.seed, args.steps, config)

        comparison = data["comparison"]
        print_comparison_table(comparison)

        # Diagnosis for each mode
        baseline = data["baseline"]
        adaptive = data["adaptive"]
        for mode in BASE_MODES:
            bl_tel = baseline.get(mode, [])
            ad_tel = adaptive.get(mode, [])
            if bl_tel and ad_tel:
                bl_pr = final_pr(bl_tel)
                ad_pr = final_pr(ad_tel)
                if not args.quiet:
                    print_diagnosis(mode, bl_pr, ad_pr, ad_tel)

        # Best recipes
        if not args.quiet:
            print("\n" + "=" * 60)
            print("MICRO-WORLD RECIPES")
            print("=" * 60)
            for mode in BASE_MODES:
                opt = optimize_mode(mode, args.seed, episodes=5,
                                   config=SimConfig(
                                       dt=config.dt, max_steps=args.steps,
                                       wall_density=config.wall_density,
                                       hdc_dim=config.hdc_dim,
                                   ))
                bp = opt.get("best_params", {})
                if bp:
                    recipe_cfg = SimConfig(
                        adaptive=(bp.get("policy", "naive") != "naive"),
                        agent_policy=bp.get("policy", "naive"),
                        wall_density=bp.get("wall_density", 0.45),
                        max_steps=args.steps,
                        hdc_dim=config.hdc_dim,
                    )
                    recipe = extract_recipe(
                        mode, bp.get("seed", args.seed),
                        args.steps, recipe_cfg,
                    )
                    print_recipe(recipe)

        # Exports
        all_tel = []
        for mode in BASE_MODES:
            all_tel.extend(data["baseline"].get(mode, []))
            all_tel.extend(data["adaptive"].get(mode, []))

        if args.csv:
            write_csv(all_tel, args.csv)
            print(f"\n  CSV written to {args.csv}")
        if args.json:
            summary = {
                "comparison": comparison,
                "campaign": "compare",
                "steps": args.steps,
                "seed": args.seed,
            }
            write_json(summary, args.json)
            print(f"  JSON written to {args.json}")
        if args.report:
            write_markdown_report(data, args.report)
            print(f"  Report written to {args.report}")

    elapsed = time.time() - t0
    print(f"\n  Completed in {elapsed:.1f}s")


if __name__ == "__main__":
    main()

```

## rgpuf_lab_v4.py
```
#!/usr/bin/env python3
"""
rgpuf_lab_v4.py
================

Next-level RGPUF demo using rgpuf_core.py.

RGPUF Lab v4 -- Micro-World Forge

Runs campaign experiments:
- baseline vs adaptive
- per-mode audit
- law contribution analysis
- stress/failure envelope
- optimizer search
- micro-world recipe extraction

This file should stay thin. All reusable mechanics live in rgpuf_core.py.

Run:
    python rgpuf_lab_v4.py --campaign compare --steps 240 --seed 42
    python rgpuf_lab_v4.py --campaign audit --mode colony --steps 240
    python rgpuf_lab_v4.py --campaign stress --mode pressure --max-steps 2000
    python rgpuf_lab_v4.py --campaign optimize --mode colony --episodes 30
    python rgpuf_lab_v4.py --campaign baseline --steps 240 --csv telemetry.csv
    python rgpuf_lab_v4.py --campaign compare --report report.md
"""

from __future__ import annotations

import argparse
import sys
import time

from rgpuf_core import (
    BASE_MODES,
    LAW_REGISTRY,
    SimConfig,
    Telemetry,
    audit_mode,
    optimize_mode,
    print_telemetry,
    run_campaign_adaptive,
    run_campaign_audit,
    run_campaign_baseline,
    run_campaign_compare,
    run_campaign_optimize,
    run_campaign_stress,
    run_sim,
    stress_mode,
    write_csv,
    write_json,
    write_markdown_report,
    final_pr,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Result Printers
# ═══════════════════════════════════════════════════════════════════════════════


def print_comparison_table(comparison: dict) -> None:
    """Print the v4 comparison table to terminal."""
    print()
    print("RGPUF Lab v4 -- Micro-World Forge")
    print("core: rgpuf_core.py | demo: rgpuf_lab_v4.py")
    print()
    header = (
        f"{'MODE':<12} {'PR_BASE':>8} {'PR_ADAPT':>8} {'PR_OPT':>8} "
        f"{'DELTA':>7} {'AGENCY':>7} {'COVER':>6} {'LAW_COST':>8} {'LAWS':>5}"
    )
    print(header)
    print("-" * len(header))

    for mode, info in comparison.items():
        pr_base = info.get("pr_base", 0)
        pr_adapt = info.get("pr_adapt", 0)
        pr_opt = info.get("pr_opt", 0)
        delta = info.get("delta_opt", 0)
        agency = info.get("agency_adapt", 0)
        cover = info.get("coverage_adapt", 0)
        cost = info.get("law_cost_adapt", 0)

        print(
            f"{mode:<12} {pr_base:8.3f} {pr_adapt:8.3f} {pr_opt:8.3f} "
            f"{delta:+7.3f} {agency:7.2f} {cover:6.2f} {cost:8.1f} "
            f"{'N/A':>5}"
        )


def print_audit_results(audit: dict) -> None:
    """Print audit results for a mode."""
    print()
    print(f"AUDIT -- {audit['mode']}")
    print(f"  Final PR_norm:  {audit['final_pr_norm']:.4f}")
    print(f"  Law Cost:       {audit['law_cost']:.2f}")
    print(f"  Law Count:      {audit['law_count']}")
    print(f"  Coverage:       {audit['coverage']:.4f}")
    print(f"  Goal Agency:    {audit['goal_agency']:.4f}")
    print(f"  Active Laws:    {', '.join(audit['active_laws'])}")
    print()
    print(f"  LAW CONTRIBUTION -- {audit['mode']}")
    print(f"  {'law':<30} {'contribution':>12} {'executed':>9} {'verdict':>8}")
    print(f"  {'-'*61}")

    for law, info in audit["contributions"].items():
        contrib = info["contribution"]
        executed = "yes" if info["executed"] else "no"
        verdict = info["verdict"]
        print(f"  {law:<30} {contrib:+12.4f} {executed:>9} {verdict:>8}")

    if audit["dead_laws"]:
        print(f"\n  Dead laws (recommended removal): {', '.join(audit['dead_laws'])}")
    else:
        print(f"\n  No dead laws detected.")


def print_stress_results(results: dict) -> None:
    """Print stress test results."""
    print()
    print("STRESS TEST RESULTS")
    print(f"  {'Seed':>8} {'TTF':>6} {'Failed':>7} {'Reason':>10} {'PR':>8} {'Agency':>7}")
    print(f"  {'-'*52}")

    for seed_key, info in results.items():
        print(
            f"  {seed_key:>8} {info['ttf']:6d} "
            f"{'yes' if info['failed'] else 'no':>7} "
            f"{info['failure_reason']:>10} "
            f"{info['final_pr']:8.4f} {info['final_agency']:7.4f}"
        )


def print_optimize_results(opt: dict) -> None:
    """Print optimization results."""
    print()
    print(f"OPTIMIZER -- {opt['mode']}")
    print(f"  Episodes: {opt['episodes']}")
    print(f"  Best PR: {opt['best_pr']:.4f}")
    bp = opt["best_params"]
    print(f"  Best Params:")
    print(f"    wall_density: {bp.get('wall_density', '?')}")
    print(f"    policy:       {bp.get('policy', '?')}")
    print(f"    seed:         {bp.get('seed', '?')}")
    print()
    print(f"  TOP 5 CONFIGURATIONS:")
    print(f"  {'#':>3} {'seed':>6} {'wall_d':>7} {'policy':>12} {'PR':>8} {'agency':>7} {'cover':>6}")
    print(f"  {'-'*54}")
    for i, r in enumerate(opt.get("top_5", [])):
        print(
            f"  {i+1:>3} {r['seed']:6d} {r['wall_density']:7.2f} "
            f"{r['policy']:>12} {r['pr']:8.4f} {r['agency']:7.4f} {r['coverage']:6.4f}"
        )


def print_baseline_results(results: dict) -> None:
    """Print baseline campaign results."""
    print()
    print("BASELINE CAMPAIGN RESULTS")
    print(f"  {'MODE':<12} {'PR_norm':>8} {'PR_raw':>8} {'Agency':>7} "
          f"{'Coverage':>8} {'LawCost':>8} {'Laws':>5}")
    print(f"  {'-'*60}")

    for mode in BASE_MODES:
        tel = results.get(mode, [])
        if tel:
            last = tel[-1]
            print(
                f"  {mode:<12} {last.pr_norm:8.4f} {last.pr:8.4f} "
                f"{last.goal_agency:7.4f} {last.coverage:8.4f} "
                f"{last.law_cost:8.2f} {last.law_count:5d}"
            )


def print_adaptive_results(results: dict) -> None:
    """Print adaptive campaign results."""
    print()
    print("ADAPTIVE CAMPAIGN RESULTS (DLASc + HDC)")
    print(f"  {'MODE':<12} {'PR_norm':>8} {'PR_raw':>8} {'Agency':>7} "
          f"{'Coverage':>8} {'LawCost':>8} {'Godel':>6}")
    print(f"  {'-'*60}")

    for mode in BASE_MODES:
        tel = results.get(mode, [])
        if tel:
            last = tel[-1]
            print(
                f"  {mode:<12} {last.pr_norm:8.4f} {last.pr:8.4f} "
                f"{last.goal_agency:7.4f} {last.coverage:8.4f} "
                f"{last.law_cost:8.2f} {last.godel_tokens:6d}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Micro-World Recipe Extraction
# ═══════════════════════════════════════════════════════════════════════════════


def extract_recipe(
    mode: str, seed: int, steps: int, config: SimConfig,
) -> dict:
    """Extract a micro-world recipe from an optimized run."""
    from rgpuf_core import run_sim, DLASc, make_state, step_sim

    # Run with adaptive to discover laws
    dlas = DLASc(LAW_REGISTRY)
    tel = run_sim(mode, seed, steps, config, dlas=dlas)

    last = tel[-1] if tel else None
    if not last:
        return {"mode": mode, "error": "no telemetry"}

    # Find failure boundary
    failure_step = -1
    failure_reason = "none"
    for t in tel:
        if t.failure_state != "active":
            failure_step = t.step
            failure_reason = t.failure_state
            break

    # Build recipe
    recipe = {
        "name": f"{mode.title()} Escape",
        "mode": mode,
        "seed": seed,
        "law_stack": last.active_laws.split(","),
        "agent_policy": config.agent_policy if config.adaptive else "naive",
        "goal": "maximize_coverage" if mode == "colony" else "maximize_pr",
        "failure": failure_reason if failure_step >= 0 else "none",
        "failure_step": failure_step,
        "topology": "cell_torus" if mode == "colony" else "continuous",
        "results": {
            "laws": len(last.active_laws.split(",")),
            "law_cost": round(last.law_cost, 2),
            "pr_norm": round(last.pr_norm, 4),
            "pr_raw": round(last.pr, 4),
            "coverage": round(last.coverage, 4),
            "goal_agency": round(last.goal_agency, 4),
            "godel_tokens": last.godel_tokens,
        },
    }

    # Count dead laws (from DLASc contribution tracking)
    dead = []
    for law in last.active_laws.split(","):
        if dlas.execution_counts.get(law, 0) == 0:
            dead.append(law)
        elif dlas.contribution_scores.get(law, 0) < -0.05:
            dead.append(law)
    recipe["dead_laws_removed"] = dead
    recipe["results"]["dead_count"] = len(dead)

    return recipe


def print_recipe(recipe: dict) -> None:
    """Print a micro-world recipe."""
    print()
    print("BEST MICRO-WORLD RECIPE")
    print(f"  Name:            {recipe['name']}")
    print(f"  Mode:            {recipe['mode']}")
    print(f"  Seed:            {recipe['seed']}")
    r = recipe["results"]
    print(f"  Laws:            {r['laws']}")
    print(f"  LawCost:         {r['law_cost']}")
    print(f"  PR_norm:         {r['pr_norm']}")
    print(f"  Coverage:        {r['coverage']}")
    print(f"  Failure:         {recipe['failure']} at T={recipe['failure_step']}")
    if recipe["dead_laws_removed"]:
        print(f"  Dead Laws:       {', '.join(recipe['dead_laws_removed'])}")
    print(f"  Law Stack:       {', '.join(recipe['law_stack'])}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Automatic Diagnosis
# ═══════════════════════════════════════════════════════════════════════════════


def print_diagnosis(mode: str, baseline_pr: float, adaptive_pr: float,
                    adaptive_tel: list[Telemetry]) -> None:
    """Print automatic diagnosis of mode improvements."""
    last = adaptive_tel[-1] if adaptive_tel else None
    if not last:
        return

    print()
    print(f"DIAGNOSIS -- {mode}")
    print(f"  Problem in v3:")
    print(f"    - PR was crushed by global registry law cost.")
    print(f"    - Agency was inflated by action success instead of goal success.")
    if mode == "colony":
        print(f"    - Cell movement improved but coverage remained low.")
        print(f"    - Teleport law was present but rarely executed.")
    elif mode == "pressure":
        print(f"    - Agency was false-perfect because actions counted even when pressure rose.")
        print(f"    - Hysteresis excess never decayed.")
    elif mode == "freescape":
        print(f"    - Zone changes were on timer, not position.")
    elif mode == "semantic":
        print(f"    - Metrics computed once then repeated -- no live data.")

    print(f"\n  v4 repair:")
    print(f"    - LawStack now counts only executed mode laws (cost: {last.law_cost:.1f}).")
    print(f"    - Goal agency uses mode-specific useful action criteria.")
    print(f"    - HDC anomalies buy repair trials via Gödel tokens.")
    print(f"    - State density measured from unique signatures.")
    print(f"    - Prediction error from transition-based predictor.")

    delta = adaptive_pr - baseline_pr
    print(f"\n  Result:")
    print(f"    PR_norm: {baseline_pr:.3f} -> {adaptive_pr:.3f} ({delta:+.3f})")
    print(f"    LawCost: N/A -> {last.law_cost:.1f}")
    print(f"    Coverage: N/A -> {last.coverage:.2f}")
    print(f"    Goal Agency: N/A -> {last.goal_agency:.2f}")
    print(f"    Gödel Tokens: {last.godel_tokens}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CLI
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="RGPUF Lab v4 -- Micro-World Forge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Campaigns:
  baseline   Run all modes with minimal static stacks
  adaptive   Run all modes with DLASc + HDC enabled
  stress     Run until failure or max steps
  audit      Compute law contribution and dead laws
  optimize   Grid search over parameters
  compare    Run baseline vs adaptive vs optimized

Examples:
  python rgpuf_lab_v4.py --campaign compare --steps 240 --seed 42
  python rgpuf_lab_v4.py --campaign audit --mode colony --steps 240
  python rgpuf_lab_v4.py --campaign stress --mode pressure --max-steps 2000
  python rgpuf_lab_v4.py --campaign optimize --mode colony --episodes 30
  python rgpuf_lab_v4.py --campaign baseline --steps 240 --csv telemetry.csv
  python rgpuf_lab_v4.py --campaign compare --report report.md
        """,
    )
    parser.add_argument(
        "--campaign", default="compare",
        choices=["baseline", "adaptive", "stress", "audit", "optimize", "compare"],
        help="Which campaign to run (default: compare)",
    )
    parser.add_argument(
        "--mode", default="colony",
        choices=BASE_MODES,
        help="Target mode for audit/stress/optimize (default: colony)",
    )
    parser.add_argument(
        "--steps", type=int, default=240,
        help="Number of simulation steps (default: 240)",
    )
    parser.add_argument(
        "--max-steps", type=int, default=2000,
        help="Max steps for stress testing (default: 2000)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--episodes", type=int, default=30,
        help="Number of optimization episodes (default: 30)",
    )
    parser.add_argument(
        "--csv", default=None,
        help="Output CSV file path",
    )
    parser.add_argument(
        "--json", default=None,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--report", default=None,
        help="Output Markdown report path",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress terminal output (except final results)",
    )
    args = parser.parse_args()

    config = SimConfig(
        max_steps=args.steps,
        wall_density=0.45,
        hdc_dim=1024,
    )

    t0 = time.time()

    # ---- BASELINE ----
    if args.campaign == "baseline":
        print(f"Running baseline campaign: {args.steps} steps, seed={args.seed}")
        results = run_campaign_baseline(args.seed, args.steps, config)

        # Print live telemetry (sampled)
        if not args.quiet:
            for mode in BASE_MODES:
                for t in results[mode]:
                    print_telemetry(t, interval=48)

        print_baseline_results(results)

        # Export
        all_tel = []
        for mode in BASE_MODES:
            all_tel.extend(results[mode])
        if args.csv:
            write_csv(all_tel, args.csv)
            print(f"\n  CSV written to {args.csv}")
        if args.json:
            summary = {
                mode: {
                    "pr_norm": results[mode][-1].pr_norm if results[mode] else 0,
                    "pr_raw": results[mode][-1].pr if results[mode] else 0,
                    "goal_agency": results[mode][-1].goal_agency if results[mode] else 0,
                    "coverage": results[mode][-1].coverage if results[mode] else 0,
                    "law_cost": results[mode][-1].law_cost if results[mode] else 0,
                    "active_laws": results[mode][-1].active_laws if results[mode] else "",
                }
                for mode in BASE_MODES
            }
            write_json(summary, args.json)
            print(f"  JSON written to {args.json}")

    # ---- ADAPTIVE ----
    elif args.campaign == "adaptive":
        print(f"Running adaptive campaign: {args.steps} steps, seed={args.seed}")
        results = run_campaign_adaptive(args.seed, args.steps, config)

        if not args.quiet:
            for mode in BASE_MODES:
                for t in results[mode]:
                    print_telemetry(t, interval=48)

        print_adaptive_results(results)

        all_tel = []
        for mode in BASE_MODES:
            all_tel.extend(results[mode])
        if args.csv:
            write_csv(all_tel, args.csv)
            print(f"\n  CSV written to {args.csv}")
        if args.json:
            summary = {
                mode: {
                    "pr_norm": results[mode][-1].pr_norm if results[mode] else 0,
                    "godel_tokens": results[mode][-1].godel_tokens if results[mode] else 0,
                    "active_laws": results[mode][-1].active_laws if results[mode] else "",
                }
                for mode in BASE_MODES
            }
            write_json(summary, args.json)
            print(f"  JSON written to {args.json}")

    # ---- STRESS ----
    elif args.campaign == "stress":
        print(f"Running stress test: mode={args.mode}, max_steps={args.max_steps}, seed={args.seed}")
        results = run_campaign_stress(args.mode, args.seed, args.max_steps, config)
        print_stress_results(results)

        if args.json:
            write_json(results, args.json)
            print(f"\n  JSON written to {args.json}")

    # ---- AUDIT ----
    elif args.campaign == "audit":
        print(f"Running audit: mode={args.mode}, steps={args.steps}, seed={args.seed}")
        audit = run_campaign_audit(args.mode, args.seed, args.steps, config)
        print_audit_results(audit)

        if args.json:
            write_json(audit, args.json)
            print(f"\n  JSON written to {args.json}")

    # ---- OPTIMIZE ----
    elif args.campaign == "optimize":
        print(f"Running optimizer: mode={args.mode}, episodes={args.episodes}, seed={args.seed}")
        opt = run_campaign_optimize(args.mode, args.seed, args.episodes, config)
        print_optimize_results(opt)

        # Also extract best recipe
        if opt["best_params"]:
            bp = opt["best_params"]
            best_cfg = SimConfig(
                adaptive=(bp.get("policy", "naive") != "naive"),
                agent_policy=bp.get("policy", "naive"),
                wall_density=bp.get("wall_density", 0.45),
                max_steps=args.steps,
                hdc_dim=config.hdc_dim,
            )
            recipe = extract_recipe(
                args.mode, bp.get("seed", args.seed),
                args.steps, best_cfg,
            )
            print_recipe(recipe)

        if args.json:
            write_json(opt, args.json)
            print(f"\n  JSON written to {args.json}")

    # ---- COMPARE ----
    elif args.campaign == "compare":
        print(f"Running comparison campaign: {args.steps} steps, seed={args.seed}")
        data = run_campaign_compare(args.seed, args.steps, config)

        comparison = data["comparison"]
        print_comparison_table(comparison)

        # Diagnosis for each mode
        baseline = data["baseline"]
        adaptive = data["adaptive"]
        for mode in BASE_MODES:
            bl_tel = baseline.get(mode, [])
            ad_tel = adaptive.get(mode, [])
            if bl_tel and ad_tel:
                bl_pr = final_pr(bl_tel)
                ad_pr = final_pr(ad_tel)
                if not args.quiet:
                    print_diagnosis(mode, bl_pr, ad_pr, ad_tel)

        # Best recipes
        if not args.quiet:
            print("\n" + "=" * 60)
            print("MICRO-WORLD RECIPES")
            print("=" * 60)
            for mode in BASE_MODES:
                opt = optimize_mode(mode, args.seed, episodes=5,
                                   config=SimConfig(
                                       dt=config.dt, max_steps=args.steps,
                                       wall_density=config.wall_density,
                                       hdc_dim=config.hdc_dim,
                                   ))
                bp = opt.get("best_params", {})
                if bp:
                    recipe_cfg = SimConfig(
                        adaptive=(bp.get("policy", "naive") != "naive"),
                        agent_policy=bp.get("policy", "naive"),
                        wall_density=bp.get("wall_density", 0.45),
                        max_steps=args.steps,
                        hdc_dim=config.hdc_dim,
                    )
                    recipe = extract_recipe(
                        mode, bp.get("seed", args.seed),
                        args.steps, recipe_cfg,
                    )
                    print_recipe(recipe)

        # Exports
        all_tel = []
        for mode in BASE_MODES:
            all_tel.extend(data["baseline"].get(mode, []))
            all_tel.extend(data["adaptive"].get(mode, []))

        if args.csv:
            write_csv(all_tel, args.csv)
            print(f"\n  CSV written to {args.csv}")
        if args.json:
            summary = {
                "comparison": comparison,
                "campaign": "compare",
                "steps": args.steps,
                "seed": args.seed,
            }
            write_json(summary, args.json)
            print(f"  JSON written to {args.json}")
        if args.report:
            write_markdown_report(data, args.report)
            print(f"  Report written to {args.report}")

    elapsed = time.time() - t0
    print(f"\n  Completed in {elapsed:.1f}s")


if __name__ == "__main__":
    main()

```

## telemetry_v4.json
```
{
  "lander": {
    "pr_norm": 0.9965397923875433,
    "pr_raw": 0.22145328719723184,
    "goal_agency": 0.4897959183673469,
    "coverage": 0.0,
    "law_cost": 4.5,
    "active_laws": "thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality"
  },
  "asteroids": {
    "pr_norm": 0.4890524608570893,
    "pr_raw": 0.09404855016482487,
    "goal_agency": 0.23529411764705882,
    "coverage": 0.0,
    "law_cost": 5.2,
    "active_laws": "central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality"
  },
  "pressure": {
    "pr_norm": 0.5498891352549888,
    "pr_raw": 0.0785555907507127,
    "goal_agency": 0.0,
    "coverage": 0.0,
    "law_cost": 7.0,
    "active_laws": "thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality"
  },
  "freescape": {
    "pr_norm": 0.43359626207613183,
    "pr_raw": 0.04470064557485895,
    "goal_agency": 0.0,
    "coverage": 0.0,
    "law_cost": 9.7,
    "active_laws": "cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality"
  },
  "colony": {
    "pr_norm": 0.03481481481481481,
    "pr_raw": 0.005802469135802468,
    "goal_agency": 0.2222222222222222,
    "coverage": 0.005208333333333333,
    "law_cost": 6.0,
    "active_laws": "cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality"
  },
  "semantic": {
    "pr_norm": 0.06502985937073155,
    "pr_raw": 0.06502985937073155,
    "goal_agency": 0.5833333333333334,
    "coverage": 0.0005787037037037037,
    "law_cost": 6.1499999999999995,
    "active_laws": "playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy"
  }
}
```

## telemetry_v4.scv
```
step,mode,seed,x,y,z,speed,fuel,heat,pressure,suit,shield,criticality,pr,pr_norm,mle,law_cost,law_count,falsifiability,semantic_entropy,prediction_error,action_agency,goal_agency,coverage,state_density,ambiguity,compression_gain,godel_tokens,semantic_drift,delta_ep_min,active_laws,failure_state,zone_id,cell_pos
0,lander,42,100.61,67.53,0.0,5.089,99.89,5.02,25.0,0,0,0.2083,0.0176,0.0794,0.25,4.5,4,0.675,0.0,0.0,1.0,1.0,0.0,1.0,0.0,0.1176,1,0.9941,0.0625,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
1,lander,42,101.23,67.59,0.0,5.19,99.78,5.04,25.0,0,0,0.2083,0.0221,0.0993,0.25,4.5,4,0.675,2.0,0.5,1.0,1.0,0.0,1.0,0.5,0.2353,2,0.0,0.0625,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
2,lander,42,101.86,67.68,0.0,5.303,99.68,5.06,25.0,0,0,0.2083,0.0331,0.1489,0.25,4.5,4,0.675,2.0,0.5,1.0,1.0,0.0,1.0,0.5,0.3529,3,0.0,0.0625,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
3,lander,42,102.5,67.8,0.0,5.426,99.57,5.08,25.0,0,0,0.2083,0.0441,0.1985,0.25,4.5,4,0.675,2.0,0.5,1.0,1.0,0.0,1.0,0.5,0.4706,4,0.0,0.0625,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
4,lander,42,103.14,67.9,0.0,5.387,99.57,5.06,25.0,0,0,0.2083,0.0421,0.1896,0.25,4.5,4,0.675,2.5,0.5,0.8,0.8,0.0,1.0,0.5,0.5882,5,0.3242,0.0078,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
5,lander,42,103.78,67.97,0.0,5.354,99.57,5.04,25.0,0,0,0.2083,0.0403,0.1815,0.25,4.5,4,0.675,3.0,0.5,0.6667,0.6667,0.0,1.0,0.5,0.7059,6,0.0,0.0078,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
6,lander,42,104.41,68.03,0.0,5.329,99.57,5.02,25.0,0,0,0.2083,0.0387,0.1741,0.25,4.5,4,0.675,3.5,0.5,0.5714,0.5714,0.0,1.0,0.5,0.8235,7,0.3145,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
7,lander,42,105.05,68.05,0.0,5.311,99.57,5.0,25.0,0,0,0.2083,0.0372,0.1672,0.25,4.5,4,0.675,4.0,0.5,0.5,0.5,0.0,1.0,0.5,0.9412,8,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
8,lander,42,105.69,68.06,0.0,5.299,99.57,4.98,25.0,0,0,0.2083,0.0357,0.1608,0.25,4.5,4,0.675,4.5,0.5,0.4444,0.4444,0.0,1.0,0.5,1.0588,9,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
9,lander,42,106.33,68.09,0.0,5.39,99.46,5.0,25.0,0,0,0.2083,0.0464,0.209,0.25,4.5,4,0.675,4.0,0.5,0.5,0.5,0.0,1.0,0.5,1.1765,10,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
10,lander,42,106.99,68.16,0.0,5.491,99.35,5.02,25.0,0,0,0.2083,0.0572,0.2576,0.25,4.5,4,0.675,3.6667,0.5,0.5455,0.5455,0.0,1.0,0.5,1.2941,11,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
11,lander,42,107.65,68.25,0.0,5.603,99.24,5.04,25.0,0,0,0.2083,0.0681,0.3064,0.25,4.5,4,0.675,3.4286,0.5,0.5833,0.5833,0.0,1.0,0.5,1.4118,12,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
12,lander,42,108.33,68.38,0.0,5.725,99.14,5.06,25.0,0,0,0.2083,0.079,0.3554,0.25,4.5,4,0.675,3.25,0.5,0.6154,0.6154,0.0,1.0,0.5,1.5294,13,0.3145,0.0078,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
13,lander,42,109.0,68.48,0.0,5.686,99.14,5.04,25.0,0,0,0.2083,0.0774,0.3481,0.25,4.5,4,0.675,3.5,0.5,0.5714,0.5714,0.0,1.0,0.5,1.6471,14,0.3145,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
14,lander,42,109.68,68.56,0.0,5.653,99.14,5.02,25.0,0,0,0.2083,0.0758,0.3411,0.25,4.5,4,0.675,3.75,0.5,0.5333,0.5333,0.0,1.0,0.5,1.7647,15,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
15,lander,42,110.35,68.61,0.0,5.627,99.14,5.0,25.0,0,0,0.2083,0.0743,0.3344,0.25,4.5,4,0.675,4.0,0.5,0.5,0.5,0.0,1.0,0.5,1.8824,16,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
16,lander,42,111.02,68.64,0.0,5.608,99.14,4.98,25.0,0,0,0.2083,0.0729,0.3279,0.25,4.5,4,0.675,4.25,0.5,0.4706,0.4706,0.0,1.0,0.5,2.0,17,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
17,lander,42,111.69,68.65,0.0,5.596,99.14,4.96,25.0,0,0,0.2083,0.0715,0.3217,0.25,4.5,4,0.675,4.5,0.5,0.4444,0.4444,0.0,1.0,0.5,2.1176,18,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
18,lander,42,112.38,68.69,0.0,5.687,99.03,4.98,25.0,0,0,0.2083,0.0822,0.3697,0.25,4.5,4,0.675,4.2222,0.5,0.4737,0.4737,0.0,1.0,0.5,2.2353,19,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
19,lander,42,113.07,68.76,0.0,5.788,98.92,5.0,25.0,0,0,0.2083,0.0929,0.418,0.25,4.5,4,0.675,4.0,0.5,0.5,0.5,0.0,1.0,0.5,2.3529,20,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
20,lander,42,113.77,68.86,0.0,5.9,98.81,5.02,25.0,0,0,0.2083,0.1037,0.4664,0.25,4.5,4,0.675,3.8182,0.5,0.5238,0.5238,0.0,1.0,0.5,2.4706,21,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
21,lander,42,114.48,68.99,0.0,6.021,98.7,5.04,25.0,0,0,0.2083,0.1145,0.5151,0.25,4.5,4,0.675,3.6667,0.5,0.5455,0.5455,0.0,1.0,0.5,2.5882,22,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
22,lander,42,115.19,69.09,0.0,5.982,98.7,5.02,25.0,0,0,0.2083,0.1129,0.5082,0.25,4.5,4,0.675,3.8333,0.5,0.5217,0.5217,0.0,1.0,0.5,2.7059,23,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
23,lander,42,115.9,69.17,0.0,5.949,98.7,5.0,25.0,0,0,0.2083,0.1115,0.5015,0.25,4.5,4,0.675,4.0,0.5,0.5,0.5,0.0,1.0,0.5,2.8235,24,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
24,lander,42,116.61,69.23,0.0,5.923,98.7,4.98,25.0,0,0,0.2083,0.11,0.495,0.25,4.5,4,0.675,4.1667,0.5,0.48,0.48,0.0,1.0,0.5,2.9412,25,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
25,lander,42,117.31,69.27,0.0,5.903,98.7,4.96,25.0,0,0,0.2083,0.1086,0.4887,0.25,4.5,4,0.675,4.3333,0.5,0.4615,0.4615,0.0,1.0,0.5,3.0588,26,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
26,lander,42,118.02,69.28,0.0,5.889,98.7,4.94,25.0,0,0,0.2083,0.1072,0.4825,0.25,4.5,4,0.675,4.5,0.5,0.4444,0.4444,0.0,1.0,0.5,3.1765,27,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
27,lander,42,118.74,69.32,0.0,5.981,98.6,4.96,25.0,0,0,0.2083,0.1179,0.5305,0.25,4.5,4,0.675,4.3077,0.5,0.4643,0.4643,0.0,1.0,0.5,3.2941,28,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
28,lander,42,119.46,69.4,0.0,6.082,98.49,4.98,25.0,0,0,0.2083,0.1286,0.5786,0.25,4.5,4,0.675,4.1429,0.5,0.4828,0.4828,0.0,1.0,0.5,3.4118,29,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
29,lander,42,120.2,69.5,0.0,6.193,98.38,5.0,25.0,0,0,0.2083,0.1393,0.6269,0.25,4.5,4,0.675,4.0,0.5,0.5,0.5,0.0,1.0,0.5,3.5294,30,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
30,lander,42,120.95,69.63,0.0,6.314,98.27,5.02,25.0,0,0,0.2083,0.1501,0.6754,0.25,4.5,4,0.675,3.875,0.5,0.5161,0.5161,0.0,1.0,0.5,3.6471,31,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
31,lander,42,121.69,69.74,0.0,6.275,98.27,5.0,25.0,0,0,0.2083,0.1486,0.6687,0.25,4.5,4,0.675,4.0,0.5,0.5,0.5,0.0,1.0,0.5,3.7647,32,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
32,lander,42,122.43,69.83,0.0,6.242,98.27,4.98,25.0,0,0,0.2083,0.1472,0.6622,0.25,4.5,4,0.675,4.125,0.5,0.4848,0.4848,0.0,1.0,0.5,3.8824,33,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
33,lander,42,123.18,69.89,0.0,6.215,98.27,4.96,25.0,0,0,0.2083,0.1457,0.6558,0.25,4.5,4,0.675,4.25,0.5,0.4706,0.4706,0.0,1.0,0.5,4.0,34,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
34,lander,42,123.92,69.93,0.0,6.194,98.27,4.94,25.0,0,0,0.2083,0.1443,0.6495,0.25,4.5,4,0.675,4.375,0.5,0.4571,0.4571,0.0,1.0,0.5,4.1176,35,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
35,lander,42,124.66,69.95,0.0,6.18,98.27,4.92,25.0,0,0,0.2083,0.143,0.6433,0.25,4.5,4,0.675,4.5,0.5,0.4444,0.4444,0.0,1.0,0.5,4.2353,36,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
36,lander,42,125.42,69.99,0.0,6.355,98.16,4.94,25.0,0,0,0.2083,0.1536,0.6913,0.25,4.5,4,0.675,4.3529,0.5,0.4595,0.4595,0.0,1.0,0.5,4.3529,37,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
37,lander,42,126.2,70.06,0.0,6.539,98.06,4.96,25.0,0,0,0.2083,0.1643,0.7394,0.25,4.5,4,0.675,4.2222,0.5,0.4737,0.4737,0.0,1.0,0.5,4.4706,38,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
38,lander,42,127.01,70.16,0.0,6.728,97.95,4.98,25.0,0,0,0.2083,0.175,0.7876,0.25,4.5,4,0.675,4.1053,0.5,0.4872,0.4872,0.0,1.0,0.5,4.5882,39,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
39,lander,42,127.83,70.28,0.0,6.924,97.84,5.0,25.0,0,0,0.2083,0.1858,0.8359,0.25,4.5,4,0.675,4.0,0.5,0.5,0.5,0.0,1.0,0.5,4.7059,40,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
40,lander,42,128.65,70.38,0.0,6.889,97.84,4.98,25.0,0,0,0.2083,0.1843,0.8294,0.25,4.5,4,0.675,4.1,0.5,0.4878,0.4878,0.0,1.0,0.5,4.8235,41,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
41,lander,42,129.47,70.46,0.0,6.86,97.84,4.96,25.0,0,0,0.2083,0.1829,0.8229,0.25,4.5,4,0.675,4.2,0.5,0.4762,0.4762,0.0,1.0,0.5,4.9412,42,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
42,lander,42,130.29,70.51,0.0,6.836,97.84,4.94,25.0,0,0,0.2083,0.1815,0.8166,0.25,4.5,4,0.675,4.3,0.5,0.4651,0.4651,0.0,1.0,0.5,5.0588,43,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
43,lander,42,131.1,70.54,0.0,6.817,97.84,4.92,25.0,0,0,0.2083,0.1801,0.8103,0.25,4.5,4,0.675,4.4,0.5,0.4545,0.4545,0.0,1.0,0.5,5.1765,44,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
44,lander,42,131.92,70.55,0.0,6.805,97.84,4.9,25.0,0,0,0.2083,0.1787,0.8042,0.25,4.5,4,0.675,4.5,0.5,0.4444,0.4444,0.0,1.0,0.5,5.2941,45,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
45,lander,42,132.76,70.59,0.0,6.977,97.73,4.92,25.0,0,0,0.2083,0.1894,0.8521,0.25,4.5,4,0.675,4.381,0.5,0.4565,0.4565,0.0,1.0,0.5,5.4118,46,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
46,lander,42,133.61,70.65,0.0,7.155,97.62,4.94,25.0,0,0,0.2083,0.2,0.9001,0.25,4.5,4,0.675,4.2727,0.5,0.4681,0.4681,0.0,1.0,0.5,5.5294,47,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
47,lander,42,134.49,70.74,0.0,7.34,97.52,4.96,25.0,0,0,0.2083,0.2107,0.9483,0.25,4.5,4,0.675,4.1739,0.5,0.4792,0.4792,0.0,1.0,0.5,5.6471,48,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
48,lander,42,135.38,70.85,0.0,7.531,97.41,4.98,25.0,0,0,0.2083,0.2215,0.9965,0.25,4.5,4,0.675,4.0833,0.5,0.4898,0.4898,0.0,1.0,0.5,5.7647,49,0.0,0.0234,"thrust_gravity_drag,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
0,asteroids,42,80.61,67.53,0.0,5.057,99.96,5.01,25.0,0,0,0.2083,0.0084,0.0435,0.2,5.2,5,0.8,0.0,0.0,1.0,0.5,0.0,1.0,0.0,0.1087,1,0.9941,0.0332,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
1,asteroids,42,81.22,67.59,0.0,5.125,99.92,5.01,25.0,0,0,0.2083,0.0054,0.0283,0.2,5.2,5,0.8,7.5,0.5,1.0,0.3333,0.0,1.0,0.5,0.2174,2,0.3555,0.0762,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
2,asteroids,42,81.84,67.67,0.0,5.203,99.87,5.02,25.0,0,0,0.2083,0.0061,0.0318,0.2,5.2,5,0.8,10.0,0.5,1.0,0.25,0.0,1.0,0.5,0.3261,3,0.2832,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
3,asteroids,42,82.46,67.79,0.0,5.291,99.83,5.03,25.0,0,0,0.2083,0.0065,0.0339,0.2,5.2,5,0.8,12.5,0.5,1.0,0.2,0.0,1.0,0.5,0.4348,4,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
4,asteroids,42,83.09,67.9,0.0,5.285,99.83,5.01,25.0,0,0,0.2083,0.0068,0.0353,0.2,5.2,5,0.8,15.0,0.5,0.8333,0.1667,0.0,1.0,0.5,0.5435,5,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
5,asteroids,42,83.71,68.01,0.0,5.28,99.83,4.99,25.0,0,0,0.2083,0.007,0.0364,0.2,5.2,5,0.8,17.5,0.5,0.7143,0.1429,0.0,1.0,0.5,0.6522,6,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
6,asteroids,42,84.33,68.12,0.0,5.274,99.83,4.97,25.0,0,0,0.2083,0.0071,0.0371,0.2,5.2,5,0.8,20.0,0.5,0.625,0.125,0.0,1.0,0.5,0.7609,7,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
7,asteroids,42,84.96,68.23,0.0,5.268,99.83,4.95,25.0,0,0,0.2083,0.0073,0.0377,0.2,5.2,5,0.8,22.5,0.5,0.5556,0.1111,0.0,1.0,0.5,0.8696,8,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
8,asteroids,42,85.58,68.33,0.0,5.261,99.83,4.93,25.0,0,0,0.2083,0.0073,0.0382,0.2,5.2,5,0.8,25.0,0.5,0.5,0.1,0.0,1.0,0.5,0.9783,9,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
9,asteroids,42,86.2,68.43,0.0,5.255,99.83,4.9,25.0,0,0,0.2083,0.0074,0.0386,0.2,5.2,5,0.8,27.5,0.5,0.4545,0.0909,0.0,1.0,0.5,1.087,10,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
10,asteroids,42,86.82,68.53,0.0,5.248,99.83,4.88,25.0,0,0,0.2083,0.0075,0.0389,0.2,5.2,5,0.8,30.0,0.5,0.4167,0.0833,0.0,1.0,0.5,1.1957,11,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
11,asteroids,42,87.45,68.66,0.0,5.338,99.79,4.89,25.0,0,0,0.2083,0.0075,0.0392,0.2,5.2,5,0.8,32.5,0.5,0.4615,0.0769,0.0,1.0,0.5,1.3043,12,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
12,asteroids,42,88.08,68.82,0.0,5.438,99.75,4.9,25.0,0,0,0.2083,0.0076,0.0394,0.2,5.2,5,0.8,35.0,0.5,0.5,0.0714,0.0,1.0,0.5,1.413,13,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
13,asteroids,42,88.72,69.01,0.0,5.548,99.71,4.91,25.0,0,0,0.2083,0.0076,0.0396,0.2,5.2,5,0.8,37.5,0.5,0.5333,0.0667,0.0,1.0,0.5,1.5217,14,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
14,asteroids,42,89.36,69.23,0.0,5.666,99.66,4.92,25.0,0,0,0.2083,0.0076,0.0398,0.2,5.2,5,0.8,40.0,0.5,0.5625,0.0625,0.0,1.0,0.5,1.6304,15,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
15,asteroids,42,90.01,69.45,0.0,5.656,99.66,4.9,25.0,0,0,0.2083,0.0077,0.0399,0.2,5.2,5,0.8,42.5,0.5,0.5294,0.0588,0.0,1.0,0.5,1.7391,16,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
16,asteroids,42,90.65,69.66,0.0,5.647,99.66,4.88,25.0,0,0,0.2083,0.0077,0.0401,0.2,5.2,5,0.8,45.0,0.5,0.5,0.0556,0.0,1.0,0.5,1.8478,17,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
17,asteroids,42,91.29,69.87,0.0,5.638,99.66,4.86,25.0,0,0,0.2083,0.0077,0.0402,0.2,5.2,5,0.8,47.5,0.5,0.4737,0.0526,0.0,1.0,0.5,1.9565,18,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
18,asteroids,42,91.93,70.08,0.0,5.629,99.66,4.83,25.0,0,0,0.2083,0.0077,0.0403,0.2,5.2,5,0.8,50.0,0.5,0.45,0.05,0.0,1.0,0.5,2.0652,19,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
19,asteroids,42,92.58,70.29,0.0,5.62,99.66,4.82,25.0,0,0,0.2083,0.0078,0.0404,0.2,5.2,5,0.8,52.5,0.5,0.4286,0.0476,0.0,1.0,0.5,2.1739,20,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
20,asteroids,42,93.22,70.5,0.0,5.611,99.66,4.8,25.0,0,0,0.2083,0.0078,0.0405,0.2,5.2,5,0.8,55.0,0.5,0.4091,0.0455,0.0,1.0,0.5,2.2826,21,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
21,asteroids,42,93.86,70.71,0.0,5.603,99.66,4.78,25.0,0,0,0.2083,0.0078,0.0406,0.2,5.2,5,0.8,57.5,0.5,0.3913,0.0435,0.0,1.0,0.5,2.3913,22,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
22,asteroids,42,94.5,70.95,0.0,5.728,99.62,4.78,25.0,0,0,0.2083,0.0078,0.0407,0.2,5.2,5,0.8,60.0,0.5,0.4167,0.0417,0.0,1.0,0.5,2.5,23,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
23,asteroids,42,95.15,71.22,0.0,5.861,99.58,4.8,25.0,0,0,0.2083,0.0078,0.0407,0.2,5.2,5,0.8,62.5,0.5,0.44,0.04,0.0,1.0,0.5,2.6087,24,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
24,asteroids,42,95.81,71.51,0.0,6.002,99.54,4.8,25.0,0,0,0.2083,0.0157,0.0816,0.2,5.2,5,0.8,32.5,0.5,0.4615,0.0769,0.0,1.0,0.5,2.7174,25,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
25,asteroids,42,96.47,71.84,0.0,6.151,99.5,4.81,25.0,0,0,0.2083,0.0236,0.1225,0.2,5.2,5,0.8,22.5,0.5,0.4815,0.1111,0.0,1.0,0.5,2.8261,26,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
26,asteroids,42,97.13,72.17,0.0,6.143,99.5,4.79,25.0,0,0,0.2083,0.0236,0.1227,0.2,5.2,5,0.8,23.3333,0.5,0.4643,0.1071,0.0,1.0,0.5,2.9348,27,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
27,asteroids,42,97.79,72.49,0.0,6.134,99.5,4.77,25.0,0,0,0.2083,0.0236,0.1229,0.2,5.2,5,0.8,24.1667,0.5,0.4483,0.1034,0.0,1.0,0.5,3.0435,28,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
28,asteroids,42,98.45,72.82,0.0,6.126,99.5,4.75,25.0,0,0,0.2083,0.0237,0.123,0.2,5.2,5,0.8,25.0,0.5,0.4333,0.1,0.0,1.0,0.5,3.1522,29,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
29,asteroids,42,99.11,73.14,0.0,6.119,99.5,4.73,25.0,0,0,0.2083,0.0237,0.1231,0.2,5.2,5,0.8,25.8333,0.5,0.4194,0.0968,0.0,1.0,0.5,3.2609,30,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
30,asteroids,42,99.77,73.46,0.0,6.111,99.5,4.71,25.0,0,0,0.2083,0.0237,0.1233,0.2,5.2,5,0.8,26.6667,0.5,0.4062,0.0938,0.0,1.0,0.5,3.3696,31,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
31,asteroids,42,100.43,73.78,0.0,6.104,99.5,4.7,25.0,0,0,0.2083,0.0237,0.1234,0.2,5.2,5,0.8,27.5,0.5,0.3939,0.0909,0.0,1.0,0.5,3.4783,32,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
32,asteroids,42,101.08,74.11,0.0,6.097,99.5,4.67,25.0,0,0,0.2083,0.0308,0.16,0.2,5.2,5,0.8,21.875,0.5,0.4,0.1143,0.0,1.0,0.5,3.587,33,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
33,asteroids,42,101.74,74.46,0.0,6.21,99.45,4.68,25.0,0,0,0.2083,0.0385,0.2003,0.2,5.2,5,0.8,18.0,0.5,0.4167,0.1389,0.0,1.0,0.5,3.6957,34,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
34,asteroids,42,102.4,74.84,0.0,6.332,99.41,4.69,25.0,0,0,0.2083,0.0463,0.2407,0.2,5.2,5,0.8,15.4167,0.5,0.4324,0.1622,0.0,1.0,0.5,3.8043,35,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
35,asteroids,42,103.05,75.25,0.0,6.463,99.37,4.71,25.0,0,0,0.2083,0.0541,0.2813,0.2,5.2,5,0.8,13.5714,0.5,0.4474,0.1842,0.0,1.0,0.5,3.913,36,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
36,asteroids,42,103.71,75.7,0.0,6.601,99.33,4.72,25.0,0,0,0.2083,0.0619,0.3219,0.2,5.2,5,0.8,12.1875,0.5,0.4615,0.2051,0.0,1.0,0.5,4.0217,37,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
37,asteroids,42,104.36,76.14,0.0,6.594,99.33,4.69,25.0,0,0,0.2083,0.062,0.3224,0.2,5.2,5,0.8,12.5,0.5,0.45,0.2,0.0,1.0,0.5,4.1304,38,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
38,asteroids,42,105.02,76.59,0.0,6.588,99.33,4.67,25.0,0,0,0.2083,0.0621,0.3228,0.2,5.2,5,0.8,12.8125,0.5,0.439,0.1951,0.0,1.0,0.5,4.2391,39,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
39,asteroids,42,105.67,77.03,0.0,6.582,99.33,4.65,25.0,0,0,0.2083,0.0622,0.3232,0.2,5.2,5,0.8,13.125,0.5,0.4286,0.1905,0.0,1.0,0.5,4.3478,40,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
40,asteroids,42,106.32,77.47,0.0,6.577,99.33,4.64,25.0,0,0,0.2083,0.0622,0.3236,0.2,5.2,5,0.8,13.4375,0.5,0.4186,0.186,0.0,1.0,0.5,4.4565,41,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
41,asteroids,42,106.98,77.91,0.0,6.571,99.33,4.62,25.0,0,0,0.2083,0.0623,0.3239,0.2,5.2,5,0.8,13.75,0.5,0.4091,0.1818,0.0,1.0,0.5,4.5652,42,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
42,asteroids,42,107.63,78.36,0.0,6.566,99.33,4.6,25.0,0,0,0.2083,0.0624,0.3243,0.2,5.2,5,0.8,14.0625,0.5,0.4,0.1778,0.0,1.0,0.5,4.6739,43,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
43,asteroids,42,108.28,78.8,0.0,6.561,99.33,4.58,25.0,0,0,0.2083,0.0624,0.3246,0.2,5.2,5,0.8,14.375,0.5,0.3913,0.1739,0.0,1.0,0.5,4.7826,44,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
44,asteroids,42,108.93,79.27,0.0,6.707,99.29,4.59,25.0,0,0,0.2083,0.0703,0.3655,0.2,5.2,5,0.8,13.0556,0.5,0.4043,0.1915,0.0,1.0,0.5,4.8913,45,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
45,asteroids,42,109.59,79.77,0.0,6.86,99.24,4.6,25.0,0,0,0.2083,0.0782,0.4065,0.2,5.2,5,0.8,12.0,0.5,0.4167,0.2083,0.0,1.0,0.5,5.0,46,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
46,asteroids,42,110.24,80.31,0.0,7.02,99.2,4.62,25.0,0,0,0.2083,0.0861,0.4476,0.2,5.2,5,0.8,11.1364,0.5,0.4286,0.2245,0.0,1.0,0.5,5.1087,47,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
47,asteroids,42,110.89,80.87,0.0,7.186,99.16,4.63,25.0,0,0,0.2083,0.094,0.4887,0.2,5.2,5,0.8,10.4167,0.5,0.44,0.24,0.0,1.0,0.5,5.2174,48,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
48,asteroids,42,111.54,81.44,0.0,7.182,99.16,4.6,25.0,0,0,0.2083,0.094,0.4891,0.2,5.2,5,0.8,10.625,0.5,0.4314,0.2353,0.0,1.0,0.5,5.3261,49,0.0,0.0527,"central_gravity_well,toroidal_wrap,quantized_rotation,resource_thermodynamics,playable_reality",active,0,
0,pressure,42,48.24,45.01,0.0,2.011,99.97,5.0,25.13,0,0,0.2094,0.0081,0.0564,0.2,7.0,5,0.62,0.0,0.0,1.0,0.0,0.0,1.0,0.0,0.0909,1,0.9785,0.0176,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
1,pressure,42,48.48,45.03,0.0,2.026,99.94,4.99,25.26,0,0,0.2105,0.0096,0.0673,0.2,7.0,5,0.62,2.5,0.5,1.0,0.0,0.0,1.0,0.5,0.1818,2,0.2461,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
2,pressure,42,48.73,45.07,0.0,2.045,99.91,4.99,25.39,0,0,0.2116,0.0144,0.1009,0.2,7.0,5,0.62,2.5,0.5,1.0,0.0,0.0,1.0,0.5,0.2727,3,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
3,pressure,42,48.97,45.11,0.0,2.068,99.88,4.99,25.53,0,0,0.2128,0.0192,0.1346,0.2,7.0,5,0.62,2.5,0.5,1.0,0.0,0.0,1.0,0.5,0.3636,4,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
4,pressure,42,49.22,45.17,0.0,2.094,99.85,4.99,25.68,0,0,0.214,0.024,0.1682,0.2,7.0,5,0.62,2.5,0.5,1.0,0.0,0.0,1.0,0.5,0.4545,5,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
5,pressure,42,49.46,45.21,0.0,2.064,99.85,4.96,25.82,0,0,0.2152,0.023,0.161,0.2,7.0,5,0.62,3.0,0.5,0.8333,0.0,0.0,1.0,0.5,0.5455,6,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
6,pressure,42,49.7,45.26,0.0,2.035,99.85,4.94,25.95,0,0,0.2163,0.0221,0.1544,0.2,7.0,5,0.62,3.5,0.5,0.7143,0.0,0.0,1.0,0.5,0.6364,7,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
7,pressure,42,49.94,45.29,0.0,2.008,99.85,4.92,26.09,0,0,0.2174,0.0212,0.1483,0.2,7.0,5,0.62,4.0,0.5,0.625,0.0,0.0,1.0,0.5,0.7273,8,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
8,pressure,42,50.17,45.32,0.0,1.982,99.85,4.9,26.21,0,0,0.2185,0.0204,0.1427,0.2,7.0,5,0.62,4.5,0.5,0.5556,0.0,0.0,1.0,0.5,0.8182,9,0.2539,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
9,pressure,42,50.41,45.35,0.0,1.958,99.85,4.88,26.35,0,0,0.2196,0.0196,0.1375,0.2,7.0,5,0.62,5.0,0.5,0.5,0.0,0.0,1.0,0.5,0.9091,10,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
10,pressure,42,50.64,45.37,0.0,1.935,99.85,4.86,26.48,0,0,0.2207,0.0196,0.1375,0.2,7.0,5,0.62,5.5,0.5,0.4545,0.0,0.0,1.0,0.5,1.0,11,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
11,pressure,42,50.87,45.38,0.0,1.913,99.85,4.84,26.61,0,0,0.2218,0.0196,0.1375,0.2,7.0,5,0.62,6.0,0.5,0.4167,0.0,0.0,1.0,0.5,1.0909,12,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
12,pressure,42,51.09,45.38,0.0,1.893,99.85,4.82,26.74,0,0,0.2228,0.0196,0.1375,0.2,7.0,5,0.62,6.5,0.5,0.3846,0.0,0.0,1.0,0.5,1.1818,13,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
13,pressure,42,51.32,45.4,0.0,1.907,99.82,4.82,26.88,0,0,0.224,0.0236,0.165,0.2,7.0,5,0.62,5.8333,0.5,0.4286,0.0,0.0,1.0,0.5,1.2727,14,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
14,pressure,42,51.55,45.43,0.0,1.926,99.79,4.82,27.02,0,0,0.2252,0.0275,0.1925,0.2,7.0,5,0.62,5.3571,0.5,0.4667,0.0,0.0,1.0,0.5,1.3636,15,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
15,pressure,42,51.78,45.47,0.0,1.949,99.76,4.81,27.15,0,0,0.2263,0.0314,0.22,0.2,7.0,5,0.62,5.0,0.5,0.5,0.0,0.0,1.0,0.5,1.4545,16,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
16,pressure,42,52.01,45.52,0.0,1.976,99.73,4.81,27.29,0,0,0.2274,0.0361,0.2526,0.2,7.0,5,0.62,4.7222,0.5,0.5294,0.0,0.0,1.0,0.5,1.5455,17,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
17,pressure,42,52.25,45.58,0.0,2.006,99.7,4.81,27.44,0,0,0.2287,0.0408,0.2854,0.2,7.0,5,0.62,4.5,0.5,0.5556,0.0,0.0,1.0,0.5,1.6364,18,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
18,pressure,42,52.48,45.63,0.0,1.975,99.7,4.79,27.57,0,0,0.2297,0.04,0.2801,0.2,7.0,5,0.62,4.75,0.5,0.5263,0.0,0.0,1.0,0.5,1.7273,19,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
19,pressure,42,52.71,45.68,0.0,1.945,99.7,4.77,27.71,0,0,0.2309,0.0393,0.2749,0.2,7.0,5,0.62,5.0,0.5,0.5,0.0,0.0,1.0,0.5,1.8182,20,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
20,pressure,42,52.93,45.72,0.0,1.917,99.7,4.75,27.85,0,0,0.2321,0.0393,0.2749,0.2,7.0,5,0.62,5.25,0.5,0.4762,0.0,0.0,1.0,0.5,1.9091,21,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
21,pressure,42,53.16,45.76,0.0,1.891,99.7,4.73,27.99,0,0,0.2332,0.0393,0.2749,0.2,7.0,5,0.62,5.5,0.5,0.4545,0.0,0.0,1.0,0.5,2.0,22,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
22,pressure,42,53.38,45.79,0.0,1.866,99.7,4.71,28.12,0,0,0.2343,0.0393,0.2749,0.2,7.0,5,0.62,5.75,0.5,0.4348,0.0,0.0,1.0,0.5,2.0909,23,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
23,pressure,42,53.6,45.81,0.0,1.842,99.7,4.69,28.27,0,0,0.2356,0.0393,0.2749,0.2,7.0,5,0.62,6.0,0.5,0.4167,0.0,0.0,1.0,0.5,2.1818,24,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
24,pressure,42,53.82,45.83,0.0,1.82,99.7,4.67,28.4,0,0,0.2367,0.0393,0.2749,0.2,7.0,5,0.62,6.25,0.5,0.4,0.0,0.0,1.0,0.5,2.2727,25,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
25,pressure,42,54.03,45.84,0.0,1.799,99.7,4.65,28.53,0,0,0.2377,0.0393,0.2749,0.2,7.0,5,0.62,6.5,0.5,0.3846,0.0,0.0,1.0,0.5,2.3636,26,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
26,pressure,42,54.25,45.87,0.0,1.817,99.67,4.65,28.66,0,0,0.2388,0.0432,0.3024,0.2,7.0,5,0.62,6.1364,0.5,0.4074,0.0,0.0,1.0,0.5,2.4545,27,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
27,pressure,42,54.47,45.9,0.0,1.84,99.64,4.65,28.8,0,0,0.24,0.0471,0.3299,0.2,7.0,5,0.62,5.8333,0.5,0.4286,0.0,0.0,1.0,0.5,2.5455,28,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
28,pressure,42,54.69,45.94,0.0,1.866,99.61,4.65,28.94,0,0,0.2412,0.0511,0.3574,0.2,7.0,5,0.62,5.5769,0.5,0.4483,0.0,0.0,1.0,0.5,2.6364,29,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
29,pressure,42,54.91,46.0,0.0,1.896,99.58,4.64,29.09,0,0,0.2424,0.055,0.3849,0.2,7.0,5,0.62,5.3571,0.5,0.4667,0.0,0.0,1.0,0.5,2.7273,30,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
30,pressure,42,55.13,46.07,0.0,1.93,99.55,4.64,29.23,0,0,0.2436,0.0589,0.4124,0.2,7.0,5,0.62,5.1667,0.5,0.4839,0.0,0.0,1.0,0.5,2.8182,31,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
31,pressure,42,55.35,46.13,0.0,1.898,99.55,4.62,29.37,0,0,0.2448,0.0589,0.4124,0.2,7.0,5,0.62,5.3333,0.5,0.4688,0.0,0.0,1.0,0.5,2.9091,32,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
32,pressure,42,55.57,46.18,0.0,1.868,99.55,4.6,29.5,0,0,0.2458,0.0589,0.4124,0.2,7.0,5,0.62,5.5,0.5,0.4545,0.0,0.0,1.0,0.5,3.0,33,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
33,pressure,42,55.78,46.23,0.0,1.839,99.55,4.58,29.63,0,0,0.2469,0.0589,0.4124,0.2,7.0,5,0.62,5.6667,0.5,0.4412,0.0,0.0,1.0,0.5,3.0909,34,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
34,pressure,42,56.0,46.27,0.0,1.812,99.55,4.56,29.77,0,0,0.2481,0.0589,0.4124,0.2,7.0,5,0.62,5.8333,0.5,0.4286,0.0,0.0,1.0,0.5,3.1818,35,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
35,pressure,42,56.21,46.3,0.0,1.786,99.55,4.55,29.92,0,0,0.2493,0.0589,0.4124,0.2,7.0,5,0.62,6.0,0.5,0.4167,0.0,0.0,1.0,0.5,3.2727,36,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
36,pressure,42,56.42,46.33,0.0,1.762,99.55,4.53,30.06,0,0,0.2505,0.0589,0.4124,0.2,7.0,5,0.62,6.1667,0.5,0.4054,0.0,0.0,1.0,0.5,3.3636,37,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
37,pressure,42,56.62,46.35,0.0,1.739,99.55,4.51,30.19,0,0,0.2516,0.0589,0.4124,0.2,7.0,5,0.62,6.3333,0.5,0.3947,0.0,0.0,1.0,0.5,3.4545,38,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
38,pressure,42,56.83,46.37,0.0,1.718,99.55,4.49,30.31,0,0,0.2526,0.0589,0.4124,0.2,7.0,5,0.62,6.5,0.5,0.3846,0.0,0.0,1.0,0.5,3.5455,39,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
39,pressure,42,57.03,46.4,0.0,1.712,99.52,4.49,30.46,0,0,0.2538,0.0628,0.4399,0.2,7.0,5,0.62,6.25,0.5,0.4,0.0,0.0,1.0,0.5,3.6364,40,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
40,pressure,42,57.23,46.44,0.0,1.711,99.49,4.49,30.6,0,0,0.255,0.0668,0.4674,0.2,7.0,5,0.62,6.0294,0.5,0.4146,0.0,0.0,1.0,0.5,3.7273,41,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
41,pressure,42,57.43,46.49,0.0,1.716,99.46,4.49,30.75,0,0,0.2562,0.0707,0.4949,0.2,7.0,5,0.62,5.8333,0.5,0.4286,0.0,0.0,1.0,0.5,3.8182,42,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
42,pressure,42,57.63,46.55,0.0,1.725,99.43,4.49,30.9,0,0,0.2575,0.0746,0.5224,0.2,7.0,5,0.62,5.6579,0.5,0.4419,0.0,0.0,1.0,0.5,3.9091,43,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
43,pressure,42,57.83,46.62,0.0,1.739,99.4,4.48,31.04,0,0,0.2587,0.0786,0.5499,0.2,7.0,5,0.62,5.5,0.5,0.4545,0.0,0.0,1.0,0.5,4.0,44,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
44,pressure,42,58.02,46.69,0.0,1.707,99.4,4.47,31.18,0,0,0.2598,0.0786,0.5499,0.2,7.0,5,0.62,5.625,0.5,0.4444,0.0,0.0,1.0,0.5,4.0909,45,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
45,pressure,42,58.21,46.75,0.0,1.675,99.4,4.45,31.32,0,0,0.261,0.0786,0.5499,0.2,7.0,5,0.62,5.75,0.5,0.4348,0.0,0.0,1.0,0.5,4.1818,46,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
46,pressure,42,58.4,46.8,0.0,1.646,99.4,4.43,31.46,0,0,0.2622,0.0786,0.5499,0.2,7.0,5,0.62,5.875,0.5,0.4255,0.0,0.0,1.0,0.5,4.2727,47,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
47,pressure,42,58.59,46.85,0.0,1.618,99.4,4.41,31.59,0,0,0.2633,0.0786,0.5499,0.2,7.0,5,0.62,6.0,0.5,0.4167,0.0,0.0,1.0,0.5,4.3636,48,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
48,pressure,42,58.78,46.89,0.0,1.591,99.4,4.39,31.73,0,0,0.2644,0.0786,0.5499,0.2,7.0,5,0.62,6.125,0.5,0.4082,0.0,0.0,1.0,0.5,4.4545,49,0.0,0.0078,"thrust_gravity_drag,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,0,
0,freescape,42,32.05,16.0,32.04,0.561,99.95,5.01,79.38,0,49.94,0.6615,0.0055,0.0532,0.1429,9.7,7,0.7286,0.0,0.0,1.0,0.0,0.0,1.0,0.0,0.073,1,0.9766,0.0156,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
1,freescape,42,32.1,16.0,32.09,0.553,99.9,5.02,78.76,0,49.88,0.6563,0.006,0.0583,0.1429,9.7,7,0.7286,3.5,0.5,1.0,0.0,0.0,1.0,0.5,0.146,2,0.2734,0.0117,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
2,freescape,42,32.14,15.99,32.14,0.553,99.86,5.04,78.15,0,49.82,0.6513,0.009,0.0874,0.1429,9.7,7,0.7286,3.5,0.5,1.0,0.0,0.0,1.0,0.5,0.219,3,0.0,0.0117,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
3,freescape,42,32.17,15.99,32.18,0.444,99.86,5.02,77.79,0,49.76,0.6483,0.0082,0.0798,0.1429,9.7,7,0.7286,4.6667,0.5,0.75,0.0,0.0,1.0,0.5,0.292,4,0.0,0.0117,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
4,freescape,42,32.2,15.98,32.22,0.358,99.86,5.01,77.44,0,49.7,0.6453,0.0064,0.0623,0.1143,9.7,7,0.7286,5.8333,0.5,0.6,0.0,0.0,0.8,0.5,0.365,5,0.2207,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
5,freescape,42,32.22,15.97,32.24,0.292,99.86,5.0,77.09,0,49.64,0.6424,0.0058,0.0566,0.119,9.7,7,0.7286,14.0,1.0,0.5,0.0,0.0,0.8333,1.0,0.438,6,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
6,freescape,42,32.24,15.96,32.27,0.241,99.86,4.99,76.75,0,49.58,0.6396,0.0069,0.0667,0.1224,9.7,7,0.7286,8.1667,0.5,0.4286,0.0,0.0,0.8571,0.5,0.5109,7,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
7,freescape,42,32.25,15.95,32.3,0.311,99.81,5.0,76.17,0,49.52,0.6347,0.0094,0.0908,0.125,9.7,7,0.7286,7.0,0.5,0.5,0.0,0.0,0.875,0.5,0.5839,8,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
8,freescape,42,32.27,15.94,32.33,0.371,99.76,5.01,75.6,0,49.46,0.63,0.0119,0.1153,0.127,9.7,7,0.7286,6.3,0.5,0.5556,0.0,0.0,0.8889,0.5,0.6569,9,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
9,freescape,42,32.29,15.92,32.38,0.42,99.71,5.02,75.03,0,49.4,0.6253,0.0144,0.1401,0.1286,9.7,7,0.7286,5.8333,0.5,0.6,0.0,0.0,0.9,0.5,0.7299,10,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
10,freescape,42,32.31,15.9,32.41,0.348,99.71,5.01,74.72,0,49.34,0.6226,0.0146,0.1415,0.1299,9.7,7,0.7286,6.4167,0.5,0.5455,0.0,0.0,0.9091,0.5,0.8029,11,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
11,freescape,42,32.32,15.89,32.44,0.295,99.71,5.0,74.4,0,49.28,0.62,0.0134,0.1297,0.119,9.7,7,0.7286,7.0,0.5,0.5,0.0,0.0,0.8333,0.5,0.8759,12,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
12,freescape,42,32.33,15.87,32.47,0.259,99.71,4.99,74.1,0,49.22,0.6175,0.0118,0.1149,0.1209,9.7,7,0.7286,15.1667,1.0,0.4615,0.0,0.0,0.8462,1.0,0.9489,13,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
13,freescape,42,32.33,15.85,32.48,0.235,99.71,4.98,73.79,0,49.16,0.6149,0.0138,0.1334,0.1224,9.7,7,0.7286,8.1667,0.5,0.4286,0.0,0.0,0.8571,0.5,1.0219,14,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
14,freescape,42,32.34,15.83,32.51,0.309,99.66,4.99,73.25,0,49.1,0.6104,0.0162,0.1574,0.1238,9.7,7,0.7286,7.5,0.5,0.4667,0.0,0.0,0.8667,0.5,1.0949,15,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
15,freescape,42,32.36,15.8,32.55,0.374,99.62,5.0,72.72,0,49.04,0.606,0.0187,0.1816,0.125,9.7,7,0.7286,7.0,0.5,0.5,0.0,0.0,0.875,0.5,1.1679,16,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
16,freescape,42,32.37,15.78,32.59,0.429,99.57,5.01,72.19,0,48.98,0.6016,0.0212,0.206,0.1261,9.7,7,0.7286,6.6111,0.5,0.5294,0.0,0.0,0.8824,0.5,1.2409,17,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
17,freescape,42,32.38,15.75,32.63,0.371,99.57,5.0,71.91,0,48.92,0.5993,0.0201,0.1946,0.119,9.7,7,0.7286,7.0,0.5,0.5,0.0,0.0,0.8333,0.5,1.3139,18,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
18,freescape,42,32.39,15.73,32.65,0.332,99.57,4.99,71.64,0,48.86,0.597,0.0177,0.1715,0.1203,9.7,7,0.7286,14.7778,1.0,0.4737,0.0,0.0,0.8421,1.0,1.3869,19,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
19,freescape,42,32.4,15.7,32.68,0.308,99.57,4.98,71.37,0,48.8,0.5947,0.0205,0.1985,0.1214,9.7,7,0.7286,7.7778,0.5,0.45,0.0,0.0,0.85,0.5,1.4599,20,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
20,freescape,42,32.4,15.67,32.69,0.296,99.57,4.96,71.1,0,48.74,0.5925,0.0195,0.189,0.1156,9.7,7,0.7286,8.1667,0.5,0.4286,0.0,0.0,0.8095,0.5,1.5328,21,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
21,freescape,42,32.41,15.64,32.72,0.359,99.52,4.98,70.59,0,48.68,0.5883,0.0191,0.1852,0.1169,9.7,7,0.7286,15.4,1.0,0.4545,0.0,0.0,0.8182,1.0,1.6058,22,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
22,freescape,42,32.42,15.6,32.76,0.419,99.47,4.99,70.09,0,48.62,0.5841,0.0243,0.2357,0.118,9.7,7,0.7286,7.3182,0.5,0.4783,0.0,0.0,0.8261,0.5,1.6788,23,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
23,freescape,42,32.44,15.57,32.8,0.47,99.42,5.0,69.6,0,48.56,0.58,0.0267,0.2594,0.119,9.7,7,0.7286,7.0,0.5,0.5,0.0,0.0,0.8333,0.5,1.7518,24,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
24,freescape,42,32.45,15.53,32.83,0.422,99.42,4.99,69.35,0,48.5,0.5779,0.027,0.2615,0.12,9.7,7,0.7286,7.2917,0.5,0.48,0.0,0.0,0.84,0.5,1.8248,25,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
25,freescape,42,32.46,15.49,32.86,0.392,99.42,4.98,69.11,0,48.44,0.5759,0.0272,0.2634,0.1209,9.7,7,0.7286,7.5833,0.5,0.4615,0.0,0.0,0.8462,0.5,1.8978,26,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
26,freescape,42,32.46,15.46,32.88,0.376,99.42,4.96,68.87,0,48.38,0.5739,0.0273,0.2652,0.1217,9.7,7,0.7286,7.875,0.5,0.4444,0.0,0.0,0.8519,0.5,1.9708,27,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
27,freescape,42,32.47,15.42,32.9,0.369,99.42,4.95,68.63,0,48.32,0.5719,0.0275,0.2668,0.1224,9.7,7,0.7286,8.1667,0.5,0.4286,0.0,0.0,0.8571,0.5,2.0438,28,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
28,freescape,42,32.48,15.37,32.93,0.422,99.38,4.96,68.15,0,48.26,0.5679,0.0288,0.2791,0.1182,9.7,7,0.7286,7.8077,0.5,0.4483,0.0,0.0,0.8276,0.5,2.1168,29,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
29,freescape,42,32.5,15.33,32.96,0.476,99.33,4.98,67.68,0,48.2,0.564,0.0272,0.264,0.119,9.7,7,0.7286,15.0,1.0,0.4667,0.0,0.0,0.8333,1.0,2.1898,30,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
30,freescape,42,32.52,15.29,33.0,0.523,99.28,4.99,67.22,0,48.14,0.5602,0.0324,0.3138,0.1152,9.7,7,0.7286,7.2333,0.5,0.4839,0.0,0.0,0.8065,0.5,2.2628,31,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
31,freescape,42,32.54,15.24,33.03,0.484,99.28,4.98,67.0,0,48.08,0.5583,0.0284,0.2758,0.1161,9.7,7,0.7286,14.9333,1.0,0.4688,0.0,0.0,0.8125,1.0,2.3358,32,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
32,freescape,42,32.55,15.19,33.05,0.461,99.28,4.96,66.78,0,48.02,0.5565,0.0328,0.3184,0.1169,9.7,7,0.7286,7.7,0.5,0.4545,0.0,0.0,0.8182,0.5,2.4088,33,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
33,freescape,42,32.57,15.14,33.07,0.449,99.28,4.95,66.57,0,47.96,0.5547,0.033,0.3205,0.1176,9.7,7,0.7286,7.9333,0.5,0.4412,0.0,0.0,0.8235,0.5,2.4818,34,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
34,freescape,42,32.57,15.09,33.09,0.446,99.28,4.94,66.36,0,47.9,0.553,0.0321,0.3113,0.1143,9.7,7,0.7286,8.1667,0.5,0.4286,0.0,0.0,0.8,0.5,2.5547,35,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
35,freescape,42,32.59,15.04,33.11,0.494,99.23,4.95,65.91,0,47.84,0.5492,0.0301,0.2917,0.1151,9.7,7,0.7286,15.75,1.0,0.4444,0.0,0.0,0.8056,1.0,2.6277,36,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
36,freescape,42,32.61,14.99,33.14,0.543,99.18,4.96,65.47,0,47.78,0.5455,0.0356,0.3457,0.112,9.7,7,0.7286,7.6176,0.5,0.4595,0.0,0.0,0.7838,0.5,2.7007,37,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
37,freescape,42,32.63,14.93,33.18,0.587,99.14,4.98,65.03,0,47.72,0.5419,0.0332,0.3216,0.1128,9.7,7,0.7286,14.7778,1.0,0.4737,0.0,0.0,0.7895,1.0,2.7737,38,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
38,freescape,42,32.65,14.88,33.21,0.554,99.14,4.97,64.83,0,47.66,0.5403,0.0383,0.3712,0.1136,9.7,7,0.7286,7.5833,0.5,0.4615,0.0,0.0,0.7949,0.5,2.8467,39,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
39,freescape,42,32.67,14.82,33.23,0.535,99.14,4.95,64.64,0,47.6,0.5387,0.0385,0.3736,0.1143,9.7,7,0.7286,7.7778,0.5,0.45,0.0,0.0,0.8,0.5,2.9197,40,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
40,freescape,42,32.68,14.76,33.25,0.527,99.14,4.94,64.45,0,47.54,0.5371,0.0387,0.3758,0.115,9.7,7,0.7286,7.9722,0.5,0.439,0.0,0.0,0.8049,0.5,2.9927,41,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
41,freescape,42,32.69,14.7,33.27,0.526,99.14,4.93,64.26,0,47.48,0.5355,0.039,0.378,0.1156,9.7,7,0.7286,8.1667,0.5,0.4286,0.0,0.0,0.8095,0.5,3.0657,42,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
42,freescape,42,32.71,14.64,33.29,0.57,99.09,4.94,63.84,0,47.42,0.532,0.0414,0.4012,0.1163,9.7,7,0.7286,7.9211,0.5,0.4419,0.0,0.0,0.814,0.5,3.1387,43,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
43,freescape,42,32.73,14.57,33.32,0.614,99.04,4.95,63.42,0,47.36,0.5285,0.0425,0.4127,0.1136,9.7,7,0.7286,7.7,0.5,0.4545,0.0,0.0,0.7955,0.5,3.2117,44,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
44,freescape,42,32.75,14.51,33.36,0.655,98.99,4.97,63.0,0,47.3,0.525,0.0392,0.3802,0.1143,9.7,7,0.7286,15.0,1.0,0.4667,0.0,0.0,0.8,1.0,3.2847,45,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
45,freescape,42,32.77,14.44,33.39,0.626,98.99,4.95,62.83,0,47.24,0.5236,0.0452,0.4382,0.1149,9.7,7,0.7286,7.6667,0.5,0.4565,0.0,0.0,0.8043,0.5,3.3577,46,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
46,freescape,42,32.79,14.38,33.41,0.612,98.99,4.94,62.66,0,47.18,0.5221,0.0442,0.4289,0.1125,9.7,7,0.7286,7.8333,0.5,0.4468,0.0,0.0,0.7872,0.5,3.4307,47,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
47,freescape,42,32.8,14.31,33.43,0.606,98.99,4.93,62.49,0,47.12,0.5207,0.0388,0.3762,0.1131,9.7,7,0.7286,16.0,1.0,0.4375,0.0,0.0,0.7917,1.0,3.5036,48,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
48,freescape,42,32.81,14.24,33.45,0.607,98.99,4.92,62.32,0,47.06,0.5193,0.0447,0.4336,0.1137,9.7,7,0.7286,8.1667,0.5,0.4286,0.0,0.0,0.7959,0.5,3.5766,49,0.0,0.0234,"cuboid_collision,zone_gravity_friction,hydraulic_height,graph_pressure_diffusion,hysteresis_failure,resource_thermodynamics,playable_reality",active,2,
0,colony,42,0.0,0.0,0.0,0.0,99.99,5.0,25.0,99.94,0,0.2083,0.0131,0.0783,0.1667,6.0,6,0.7833,0.0,0.0,1.0,1.0,0.0035,1.0,0.0,0.1,1,0.9551,0.0566,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
1,colony,42,0.0,0.0,0.0,0.0,99.98,5.0,25.0,99.88,0,0.2083,0.0075,0.0448,0.0833,6.0,6,0.7833,3.0,0.5,1.0,1.0,0.0035,0.5,0.5,0.2,2,0.2891,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
2,colony,42,0.0,0.0,0.0,0.0,99.96,5.0,25.0,99.82,0,0.2083,0.0131,0.0783,0.0556,6.0,6,0.7833,0.0,0.0,1.0,1.0,0.0035,0.3333,0.0,0.3,3,0.2891,0.0566,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
3,colony,42,0.0,0.0,0.0,0.0,99.95,5.0,25.0,99.76,0,0.2083,0.0131,0.0783,0.0417,6.0,6,0.7833,0.0,0.0,1.0,1.0,0.0035,0.25,0.0,0.4,3,0.0,0.0566,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
4,colony,42,0.0,0.0,0.0,0.0,99.94,5.0,25.0,99.7,0,0.2083,0.0131,0.0783,0.0333,6.0,6,0.7833,0.0,0.0,1.0,1.0,0.0035,0.2,0.0,0.5,3,0.0,0.0566,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
5,colony,42,0.0,0.0,0.0,0.0,99.93,5.0,25.0,99.64,0,0.2083,0.0131,0.0783,0.0278,6.0,6,0.7833,0.0,0.0,1.0,1.0,0.0035,0.1667,0.0,0.6,3,0.0,0.0566,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
6,colony,42,0.0,0.0,0.0,0.0,99.92,5.0,25.0,99.58,0,0.2083,0.0065,0.0392,0.0238,6.0,6,0.7833,0.0,0.0,0.5,0.5,0.0035,0.1429,0.0,0.7,4,0.2578,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
7,colony,42,0.0,0.0,0.0,0.0,99.9,5.0,25.0,99.52,0,0.2083,0.0065,0.0392,0.0208,6.0,6,0.7833,0.0,0.0,0.5,0.5,0.0035,0.125,0.0,0.8,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
8,colony,42,0.0,0.0,0.0,0.0,99.89,5.0,25.0,99.46,0,0.2083,0.0065,0.0392,0.0185,6.0,6,0.7833,0.0,0.0,0.5,0.5,0.0035,0.1111,0.0,0.9,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
9,colony,42,0.0,0.0,0.0,0.0,99.88,5.0,25.0,99.4,0,0.2083,0.0065,0.0392,0.0167,6.0,6,0.7833,0.0,0.0,0.5,0.5,0.0035,0.1,0.0,1.0,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
10,colony,42,0.0,0.0,0.0,0.0,99.87,5.0,25.0,99.34,0,0.2083,0.0065,0.0392,0.0152,6.0,6,0.7833,0.0,0.0,0.5,0.5,0.0035,0.0909,0.0,1.1,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
11,colony,42,0.0,0.0,0.0,0.0,99.86,5.0,25.0,99.28,0,0.2083,0.0065,0.0392,0.0139,6.0,6,0.7833,0.0,0.0,0.5,0.5,0.0035,0.0833,0.0,1.2,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
12,colony,42,0.0,0.0,0.0,0.0,99.84,5.0,25.0,99.22,0,0.2083,0.0044,0.0261,0.0128,6.0,6,0.7833,0.0,0.0,0.3333,0.3333,0.0035,0.0769,0.0,1.3,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
13,colony,42,0.0,0.0,0.0,0.0,99.83,5.0,25.0,99.16,0,0.2083,0.0044,0.0261,0.0119,6.0,6,0.7833,0.0,0.0,0.3333,0.3333,0.0035,0.0714,0.0,1.4,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
14,colony,42,0.0,0.0,0.0,0.0,99.82,5.0,25.0,99.1,0,0.2083,0.0044,0.0261,0.0111,6.0,6,0.7833,0.0,0.0,0.3333,0.3333,0.0035,0.0667,0.0,1.5,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
15,colony,42,0.0,0.0,0.0,0.0,99.81,5.0,25.0,99.04,0,0.2083,0.0044,0.0261,0.0104,6.0,6,0.7833,0.0,0.0,0.3333,0.3333,0.0035,0.0625,0.0,1.6,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
16,colony,42,0.0,0.0,0.0,0.0,99.8,5.0,25.0,98.98,0,0.2083,0.0044,0.0261,0.0098,6.0,6,0.7833,0.0,0.0,0.3333,0.3333,0.0035,0.0588,0.0,1.7,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
17,colony,42,0.0,0.0,0.0,0.0,99.78,5.0,25.0,98.93,0,0.2083,0.0044,0.0261,0.0093,6.0,6,0.7833,0.0,0.0,0.3333,0.3333,0.0035,0.0556,0.0,1.8,4,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
18,colony,42,0.0,0.0,0.0,0.0,99.77,5.0,25.0,98.87,0,0.2083,0.0033,0.0196,0.0088,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0035,0.0526,0.0,1.9,5,0.2539,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
19,colony,42,0.0,0.0,0.0,0.0,99.76,5.0,25.0,98.81,0,0.2083,0.0033,0.0196,0.0083,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0035,0.05,0.0,2.0,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
20,colony,42,0.0,0.0,0.0,0.0,99.75,5.0,25.0,98.75,0,0.2083,0.0033,0.0196,0.0079,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0035,0.0476,0.0,2.1,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
21,colony,42,0.0,0.0,0.0,0.0,99.74,5.0,25.0,98.69,0,0.2083,0.0033,0.0196,0.0076,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0035,0.0455,0.0,2.2,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
22,colony,42,0.0,0.0,0.0,0.0,99.72,5.0,25.0,98.63,0,0.2083,0.0033,0.0196,0.0072,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0035,0.0435,0.0,2.3,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
23,colony,42,0.0,0.0,0.0,0.0,99.71,5.0,25.0,98.57,0,0.2083,0.0033,0.0196,0.0069,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0035,0.0417,0.0,2.4,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
24,colony,42,0.0,0.0,0.0,0.0,99.7,5.0,25.0,98.51,0,0.2083,0.0026,0.0157,0.0067,6.0,6,0.7833,0.0,0.0,0.2,0.2,0.0035,0.04,0.0,2.5,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
25,colony,42,0.0,0.0,0.0,0.0,99.69,5.0,25.0,98.45,0,0.2083,0.0026,0.0157,0.0064,6.0,6,0.7833,0.0,0.0,0.2,0.2,0.0035,0.0385,0.0,2.6,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
26,colony,42,0.0,0.0,0.0,0.0,99.68,5.0,25.0,98.39,0,0.2083,0.0026,0.0157,0.0062,6.0,6,0.7833,0.0,0.0,0.2,0.2,0.0035,0.037,0.0,2.7,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
27,colony,42,0.0,0.0,0.0,0.0,99.66,5.0,25.0,98.33,0,0.2083,0.0026,0.0157,0.006,6.0,6,0.7833,0.0,0.0,0.2,0.2,0.0035,0.0357,0.0,2.8,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
28,colony,42,0.0,0.0,0.0,0.0,99.65,5.0,25.0,98.27,0,0.2083,0.0026,0.0157,0.0057,6.0,6,0.7833,0.0,0.0,0.2,0.2,0.0035,0.0345,0.0,2.9,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
29,colony,42,0.0,0.0,0.0,0.0,99.64,5.0,25.0,98.22,0,0.2083,0.0026,0.0157,0.0056,6.0,6,0.7833,0.0,0.0,0.2,0.2,0.0035,0.0333,0.0,3.0,5,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,12)"
30,colony,42,0.0,0.0,0.0,0.0,99.63,5.0,25.0,98.16,0,0.2083,0.0037,0.0222,0.0108,6.0,6,0.7833,18.0,1.0,0.3333,0.3333,0.0052,0.0645,1.0,3.1,6,0.2637,0.0137,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
31,colony,42,0.0,0.0,0.0,0.0,99.62,5.0,25.0,98.1,0,0.2083,0.0042,0.0255,0.0104,6.0,6,0.7833,9.0,0.5,0.3333,0.3333,0.0052,0.0625,0.5,3.2,7,0.0,0.0137,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
32,colony,42,0.0,0.0,0.0,0.0,99.6,5.0,25.0,98.04,0,0.2083,0.0087,0.0522,0.0101,6.0,6,0.7833,0.0,0.0,0.3333,0.3333,0.0052,0.0606,0.0,3.3,8,0.2598,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
33,colony,42,0.0,0.0,0.0,0.0,99.59,5.0,25.0,97.98,0,0.2083,0.0087,0.0522,0.0098,6.0,6,0.7833,0.0,0.0,0.3333,0.3333,0.0052,0.0588,0.0,3.4,8,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
34,colony,42,0.0,0.0,0.0,0.0,99.58,5.0,25.0,97.92,0,0.2083,0.0087,0.0522,0.0095,6.0,6,0.7833,0.0,0.0,0.3333,0.3333,0.0052,0.0571,0.0,3.5,8,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
35,colony,42,0.0,0.0,0.0,0.0,99.57,5.0,25.0,97.86,0,0.2083,0.0087,0.0522,0.0093,6.0,6,0.7833,0.0,0.0,0.3333,0.3333,0.0052,0.0556,0.0,3.6,8,0.0,0.0449,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
36,colony,42,0.0,0.0,0.0,0.0,99.56,5.0,25.0,97.8,0,0.2083,0.0075,0.0448,0.009,6.0,6,0.7833,0.0,0.0,0.2857,0.2857,0.0052,0.0541,0.0,3.7,9,0.2539,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
37,colony,42,0.0,0.0,0.0,0.0,99.54,5.0,25.0,97.75,0,0.2083,0.0075,0.0448,0.0088,6.0,6,0.7833,0.0,0.0,0.2857,0.2857,0.0052,0.0526,0.0,3.8,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
38,colony,42,0.0,0.0,0.0,0.0,99.53,5.0,25.0,97.69,0,0.2083,0.0075,0.0448,0.0085,6.0,6,0.7833,0.0,0.0,0.2857,0.2857,0.0052,0.0513,0.0,3.9,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
39,colony,42,0.0,0.0,0.0,0.0,99.52,5.0,25.0,97.63,0,0.2083,0.0075,0.0448,0.0083,6.0,6,0.7833,0.0,0.0,0.2857,0.2857,0.0052,0.05,0.0,4.0,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
40,colony,42,0.0,0.0,0.0,0.0,99.51,5.0,25.0,97.57,0,0.2083,0.0075,0.0448,0.0081,6.0,6,0.7833,0.0,0.0,0.2857,0.2857,0.0052,0.0488,0.0,4.1,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
41,colony,42,0.0,0.0,0.0,0.0,99.5,5.0,25.0,97.51,0,0.2083,0.0075,0.0448,0.0079,6.0,6,0.7833,0.0,0.0,0.2857,0.2857,0.0052,0.0476,0.0,4.2,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
42,colony,42,0.0,0.0,0.0,0.0,99.48,5.0,25.0,97.45,0,0.2083,0.0065,0.0392,0.0078,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0052,0.0465,0.0,4.3,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
43,colony,42,0.0,0.0,0.0,0.0,99.47,5.0,25.0,97.39,0,0.2083,0.0065,0.0392,0.0076,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0052,0.0455,0.0,4.4,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
44,colony,42,0.0,0.0,0.0,0.0,99.46,5.0,25.0,97.34,0,0.2083,0.0065,0.0392,0.0074,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0052,0.0444,0.0,4.5,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
45,colony,42,0.0,0.0,0.0,0.0,99.45,5.0,25.0,97.28,0,0.2083,0.0065,0.0392,0.0072,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0052,0.0435,0.0,4.6,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
46,colony,42,0.0,0.0,0.0,0.0,99.44,5.0,25.0,97.22,0,0.2083,0.0065,0.0392,0.0071,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0052,0.0426,0.0,4.7,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
47,colony,42,0.0,0.0,0.0,0.0,99.42,5.0,25.0,97.16,0,0.2083,0.0065,0.0392,0.0069,6.0,6,0.7833,0.0,0.0,0.25,0.25,0.0052,0.0417,0.0,4.8,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
48,colony,42,0.0,0.0,0.0,0.0,99.41,5.0,25.0,97.1,0,0.2083,0.0058,0.0348,0.0068,6.0,6,0.7833,0.0,0.0,0.2222,0.2222,0.0052,0.0408,0.0,4.9,9,0.0,0.041,"cell_occupancy,quantized_rotation,toroidal_surface,power_suit_energy,resource_thermodynamics,playable_reality",active,0,"(13,13)"
0,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0794,0.0794,0.0,4.5,4,0.0,0.0,0.0,0.0,1.0,0.0,0.1667,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
1,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0614,0.0614,0.0,4.85,4,0.0,0.0,0.0,0.0,0.75,0.0,0.3333,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
2,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0598,0.0598,0.0,5.57,4,0.0,0.0,0.0,0.0,0.5,0.0,0.5,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
3,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0581,0.0581,0.0,6.6,4,0.0,0.0,0.0,0.0,0.375,0.0,0.6667,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
4,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0622,0.0622,0.0,6.48,4,0.0,0.0,0.0,0.0,0.5,0.0007,0.8333,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
5,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
6,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
7,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
8,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
9,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
10,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
11,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
12,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
13,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
14,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
15,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
16,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
17,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
18,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
19,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
20,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
21,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
22,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
23,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
24,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
25,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
26,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
27,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
28,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
29,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
30,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
31,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
32,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
33,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
34,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
35,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
36,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
37,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
38,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
39,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
40,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
41,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
42,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
43,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
44,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
45,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
46,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
47,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
48,semantic,42,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.065,0.065,0.0,6.15,4,0.0,0.0,0.0,0.0,0.5833,0.0006,1.0,0.0,0.0,0,0.0,0.0,"playable_reality,minimum_law_efficiency,compression_ratio,semantic_entropy",active,0,
```
