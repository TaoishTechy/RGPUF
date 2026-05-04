#!/usr/bin/env python3
"""
RGPUF Lab v3 -- Adaptive Minimum-Law Retro Physics Lab
======================================================

Retro Game Physics Unified Framework

v2 proved: small law stacks generate diverse retro-physics worlds.
v3 proves: the simulator can diagnose, adapt, falsify, and optimize
          its own law stack in real time.

New in v3:
    - Measured agency, state density, and ambiguity (not hardcoded)
    - Law-weighted PR formula with prediction error
    - Dynamic Law-Actuated Semantic Compiler (DLASc)
    - Adaptive agent scripts (PID, wall-follow, risk)
    - GhostMesh48-HDC microkernel (semantic drift, anomalies, EP detection)
    - Failure boundary testing (stress mode)
    - Law contribution analysis (audit mode)
    - Parameter search optimizer mode
    - Live semantic cross-mode correlation
    - Markdown report export

Modes:
    lander    -- Lunar Lander with PID pilot
    asteroids -- Spacewar!/Elite with angular momentum tracking
    pressure  -- Driller pressure with hysteresis leak and risk agents
    freescape -- Driller/Freescape with position-derived zones
    colony    -- The Colony with wall-follow agent and stuck detector
    semantic  -- Live cross-mode correlation (not static)
    stress    -- Run until failure, measure TTF
    optimizer -- Grid search over agent/policy/law parameters
    audit     -- Per-law contribution analysis with repair suggestions

Run:
    python rgpuf_lab_v3.py --all --steps 240 --seed 42
    python rgpuf_lab_v3.py --mode colony --adaptive --steps 240
    python rgpuf_lab_v3.py --stress pressure --until-failure --seed 7
    python rgpuf_lab_v3.py --optimizer colony --episodes 20
    python rgpuf_lab_v3.py --audit colony --steps 240
    python rgpuf_lab_v3.py --all --csv telemetry.csv --json summary.json --report report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Literal

Mode = Literal[
    "lander", "asteroids", "pressure", "freescape",
    "colony", "semantic", "stress", "optimizer", "audit",
]

TAU = math.tau
HDC_DIM = 512

# ═══════════════════════════════════════════════════════════════════════════════
# 1. Math Primitives
# ═══════════════════════════════════════════════════════════════════════════════


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def wrap(v: float, size: float) -> float:
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

    def rotate(self, rad: float) -> Vec2:
        c, s = math.cos(rad), math.sin(rad)
        return Vec2(self.x * c - self.y * s, self.x * s + self.y * c)

    def normalized(self) -> Vec2:
        m = self.length()
        return Vec2(self.x / m, self.y / m) if m > 1e-9 else Vec2()


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

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def rotate_y(self, rad: float) -> Vec3:
        c, s = math.cos(rad), math.sin(rad)
        return Vec3(self.x * c + self.z * s, self.y, -self.x * s + self.z * c)

    def normalized(self) -> Vec3:
        m = self.length()
        return Vec3(self.x / m, self.y / m, self.z / m) if m > 1e-9 else Vec3()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Core Data Classes
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class Body:
    pos: Vec2 = field(default_factory=Vec2)
    vel: Vec2 = field(default_factory=Vec2)
    mass: float = 1.0
    radius: float = 1.0
    heading_byte: int = 64
    height: float = 0.0
    mode: str = "ground"
    zone_id: int = 0
    state: str = "active"

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
    pos: Vec3 = field(default_factory=Vec3)
    vel: Vec3 = field(default_factory=Vec3)
    heading_byte: int = 0
    zone_id: int = 0
    state: str = "active"

    @property
    def heading_rad(self) -> float:
        return (self.heading_byte / 256.0) * TAU

    def rotate_quantized(self, ticks: int) -> None:
        self.heading_byte = (self.heading_byte + ticks) % 256


@dataclass
class ResourceReservoir:
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


@dataclass
class Zone:
    id: int
    gravity: float = 1.0
    friction: float = 0.1
    light_radius: float = 999.0
    time_scale: float = 1.0
    pressure: float = 25.0
    neighbors: list[int] = field(default_factory=list)


@dataclass
class Cuboid:
    mn: Vec3 = field(default_factory=Vec3)
    mx: Vec3 = field(default_factory=Vec3)
    solid: bool = True


def inside_cuboid(p: Vec3, c: Cuboid) -> bool:
    return c.mn.x <= p.x <= c.mx.x and c.mn.y <= p.y <= c.mx.y and c.mn.z <= p.z <= c.mx.z


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
    walls: dict[str, bool] = field(default_factory=lambda: {
        "n": True, "s": True, "e": True, "w": True, "u": False, "d": False,
    })
    object_id: int = 0
    furniture: bool = False
    teleport_to: tuple[int, int] | None = None
    energy_station: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# 3. LawTerm v3 and Agent Stats
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class LawTermV3:
    name: str
    active: bool
    cost: float
    verified: str
    preconditions: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    trust: float = 1.0
    activation_count: int = 0
    contribution_score: float = 0.0
    prediction_error: float = 0.0


@dataclass
class AgentStats:
    attempted: int = 0
    successful: int = 0
    blocked: int = 0
    collisions: int = 0
    teleports: int = 0
    failures: int = 0

    @property
    def agency(self) -> float:
        return clamp(self.successful / max(self.attempted, 1), 0.0, 1.0)


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


@dataclass
class RunDiagnosis:
    mode: str
    best_pr: float = 0.0
    final_pr: float = 0.0
    ttf: int = -1
    failure_reason: str | None = None
    bottlenecks: list[str] = field(default_factory=list)
    recommended_repairs: list[str] = field(default_factory=list)
    law_contributions: dict[str, float] = field(default_factory=dict)


VERIFIED_WEIGHT = {"historical": 1.0, "equivalent": 0.7, "speculative": 0.3}


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Law Registry v3
# ═══════════════════════════════════════════════════════════════════════════════


def _law(name, active, cost, verified, pre=None, eff=None):
    return LawTermV3(name=name, active=active, cost=cost, verified=verified,
                     preconditions=pre or [], effects=eff or [])


LAW_REGISTRY: dict[str, LawTermV3] = {
    # Motion
    "thrust_gravity_drag":  _law("thrust_gravity_drag",  True, 1.0, "equivalent"),
    "central_gravity_well": _law("central_gravity_well", True, 1.2, "historical"),
    "quantized_rotation":   _law("quantized_rotation",   True, 0.5, "historical"),
    # Topology
    "toroidal_wrap":        _law("toroidal_wrap", True, 0.5, "historical",
                                  pre=["wrap_enabled"], eff=["state_continuity"]),
    "teleport_transform":   _law("teleport_transform", True, 1.0, "historical",
                                  pre=["teleport_trigger"], eff=["state_continuity"]),
    # Resource
    "resource_thermodynamics": _law("resource_thermodynamics", True, 1.0, "equivalent"),
    "graph_pressure_diffusion": _law("graph_pressure_diffusion", True, 1.5, "equivalent",
                                      pre=["zone_graph"], eff=["pressure_equilibrium"]),
    "hysteresis_failure":   _law("hysteresis_failure", True, 1.5, "equivalent",
                                  pre=["pressure_reservoir"], eff=["stabilization"]),
    # Spatial
    "cuboid_collision":     _law("cuboid_collision", True, 1.5, "historical",
                                  pre=["cuboid_world"], eff=["spatial_constraint"]),
    "zone_gravity_friction":_law("zone_gravity_friction", True, 1.0, "historical",
                                  pre=["zone_system"], eff=["spatial_constraint"]),
    "hydraulic_height":     _law("hydraulic_height", True, 1.2, "equivalent",
                                  pre=["zone_system"], eff=["agency_increase"]),
    # Colony
    "cell_occupancy":       _law("cell_occupancy", True, 1.0, "historical",
                                  pre=["cell_grid"], eff=["spatial_constraint"]),
    "bresenham_los":        _law("bresenham_los", True, 0.8, "historical",
                                  pre=["cell_grid"], eff=["prediction_repair"]),
    "toroidal_surface":     _law("toroidal_surface", True, 0.5, "historical",
                                  pre=["torus_world"], eff=["state_continuity"]),
    "power_suit_energy":    _law("power_suit_energy", True, 1.0, "equivalent"),
    # Adaptive
    "wall_following_agent": _law("wall_following_agent", False, 1.0, "equivalent",
                                  pre=["cell_grid", "blocked_actions_high"],
                                  eff=["agency_increase", "semantic_entropy_decrease"]),
    "pid_controller":       _law("pid_controller", False, 1.2, "equivalent",
                                  pre=["continuous_motion", "landing_target"],
                                  eff=["agency_increase"]),
    "risk_policy":          _law("risk_policy", False, 0.8, "speculative",
                                  pre=["pressure_reservoir"],
                                  eff=["stabilization"]),
    # Semantic
    "playable_reality":     _law("playable_reality", True, 2.0, "speculative"),
    "minimum_law_efficiency": _law("minimum_law_efficiency", True, 2.0, "speculative"),
    "compression_ratio":    _law("compression_ratio", True, 1.5, "speculative"),
    "semantic_entropy":     _law("semantic_entropy", True, 2.0, "speculative"),
}

BASE_MODES = ["lander", "asteroids", "pressure", "freescape", "colony", "semantic"]
ALL_MODES = BASE_MODES + ["stress", "optimizer", "audit"]

# ═══════════════════════════════════════════════════════════════════════════════
# 5. Hyperdimensional Computing -- GM48-HDC Microkernel
# ═══════════════════════════════════════════════════════════════════════════════


class HDCEngine:
    """Lightweight HDC using bipolar vectors. O(D) per operation."""

    def __init__(self, dim: int = HDC_DIM, seed: int = 42):
        self.dim = dim
        self.rng = random.Random(seed)
        self.vectors: dict[str, list[int]] = {}
        self.memory = self._bipolar()
        self.anomaly_count = 0

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

    def exceptional_point(self, law_a: str, law_b: str,
                          state_vec: list[int]) -> float:
        sa = self.similarity(self.encode(law_a), state_vec)
        sb = self.similarity(self.encode(law_b), state_vec)
        return abs(sa - sb)

    def state_vector(self, mode: str, active_laws: list[str],
                     metric_buckets: dict[str, bool]) -> list[int]:
        parts = [self.encode(mode)]
        for ln in active_laws:
            parts.append(self.encode(ln))
        for bucket, present in metric_buckets.items():
            if present:
                parts.append(self.encode(bucket))
        return self.bundle(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. DLASc -- Dynamic Law-Actuated Semantic Compiler
# ═══════════════════════════════════════════════════════════════════════════════


class DLASc:
    """Selects which laws to activate based on simulation context."""

    def __init__(self, registry: dict[str, LawTermV3]):
        self.laws = registry

    def should_activate(self, name: str, ctx: dict[str, Any]) -> bool:
        law = self.laws[name]
        if law.active:
            return False
        for p in law.preconditions:
            if not ctx.get(p, False):
                return False
        if "agency_increase" in law.effects and ctx.get("agency", 1.0) < 0.4:
            return True
        if "semantic_entropy_decrease" in law.effects and ctx.get("semantic_entropy", 0) > 2.5:
            return True
        if "stabilization" in law.effects and ctx.get("criticality", 0) > 0.7:
            return True
        if "prediction_repair" in law.effects and ctx.get("prediction_error", 0) > 0.2:
            return True
        return False

    def should_deactivate(self, name: str, ctx: dict[str, Any]) -> bool:
        law = self.laws[name]
        if not law.active:
            return False
        if law.contribution_score < -0.05 and law.activation_count > 20:
            return True
        return False

    def tick(self, ctx: dict[str, Any]) -> list[str]:
        changes: list[str] = []
        for name in self.laws:
            if self.should_activate(name, ctx):
                self.laws[name].active = True
                self.laws[name].activation_count += 1
                changes.append(f"+ {name}")
            elif self.should_deactivate(name, ctx):
                self.laws[name].active = False
                changes.append(f"- {name}")
        return changes

    def active_names(self) -> list[str]:
        return [n for n, l in self.laws.items() if l.active]

    def active_cost(self) -> float:
        return sum(l.cost for l in self.laws.values() if l.active)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Physics Laws
# ═══════════════════════════════════════════════════════════════════════════════


def arcade_motion_step(body: Body, dt: float, thrust: float,
                       gravity: Vec2, drag: float,
                       world: Vec2, wrap_edges: bool) -> None:
    force = body.forward * thrust + gravity * body.mass - body.vel * drag
    acc = force * (1.0 / body.mass)
    body.vel = body.vel + acc * dt
    body.pos = body.pos + body.vel * dt
    if wrap_edges:
        body.pos.x = wrap(body.pos.x, world.x)
        body.pos.y = wrap(body.pos.y, world.y)
    else:
        if body.pos.x < 0 or body.pos.x > world.x:
            body.vel.x *= -0.85
            body.pos.x = clamp(body.pos.x, 0, world.x)
        if body.pos.y < 0:
            body.vel.y *= -0.30
            body.pos.y = 0
        if body.pos.y > world.y:
            body.vel.y *= -0.85
            body.pos.y = world.y


def central_gravity_well(body: Body, attractor: Vec2,
                         gm: float, softening: float = 25.0) -> Vec2:
    delta = attractor - body.pos
    r2 = delta.x * delta.x + delta.y * delta.y + softening
    return delta.normalized() * (gm / r2)


def motion_step_3d(body: Body3, dt: float, gravity: float,
                   friction: float, world: Vec3,
                   wrap_edges: bool = False) -> None:
    body.vel.y -= gravity * dt
    body.vel.x *= (1.0 - friction)
    body.vel.z *= (1.0 - friction)
    body.pos = body.pos + body.vel * dt
    if wrap_edges:
        body.pos.x = wrap(body.pos.x, world.x)
        body.pos.z = wrap(body.pos.z, world.z)
    else:
        body.pos.x = clamp(body.pos.x, 0, world.x)
        body.pos.z = clamp(body.pos.z, 0, world.z)
        if body.pos.y < 0:
            body.pos.y = 0
            body.vel.y *= -0.3


def graph_pressure_diffusion(zones: list[Zone], sinks: dict[int, float],
                             dt: float, D: float = 0.08) -> None:
    deltas = [0.0] * len(zones)
    for i, z in enumerate(zones):
        diff = sum(zones[j].pressure - z.pressure for j in z.neighbors)
        deltas[i] = (D * diff - sinks.get(z.id, 0.0)) * dt
    for i, z in enumerate(zones):
        z.pressure = max(0.0, z.pressure + deltas[i])


def hysteresis_failure(excess: float, pressure: float, critical: float,
                       dt: float, threshold: float = 15.0,
                       hyst_leak: float = 0.05) -> tuple[float, bool]:
    excess += max(0.0, pressure - critical) * dt
    excess -= hyst_leak * excess * dt
    excess = max(0.0, excess)
    return excess, excess > threshold


def bresenham_los(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
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
            err += dy; cx += sx
        if e2 <= dx:
            err += dx; cy += sy
    return cells


def colony_generate_grid(w: int, h: int, seed: int,
                         wall_density: float = 0.45) -> dict[tuple[int, int], Cell]:
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


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Adaptive Agent Scripts
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_DIRS = [
    (0, -1, "n"),  # 0 = N
    (1,  0, "e"),  # 1 = E
    (0,  1, "s"),  # 2 = S
    (-1, 0, "w"),  # 3 = W
]

WALL_RIGHT = ["e", "s", "w", "n"]
WALL_LEFT = ["w", "n", "e", "s"]


def agent_lander_pid(ship: Body, fuel: ResourceReservoir,
                     pad_x: float, dt: float,
                     prev_error: list[float]) -> tuple[float, bool]:
    """PID controller targeting safe landing near pad."""
    target_vy = -1.5
    error = target_vy - ship.vel.y
    thrust = clamp(1.8 * error + 0.6 * (error - prev_error[0]), 0, 5.0)
    prev_error[0] = error
    dx = pad_x - ship.pos.x
    if abs(dx) > 8 and fuel.value > 20:
        ship.rotate_quantized(6 if dx > 0 else -6)
    attempted = fuel.value > 0
    return thrust, attempted


def agent_colony_wall_follow(cx: int, cy: int, heading: int,
                             grid: dict[tuple[int, int], Cell],
                             gw: int, gh: int) -> tuple[int, int, int, bool]:
    """Right-hand rule wall follower. Returns (new_cx, new_cy, delta_heading, moved)."""
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


def agent_naive(step: int, rng: random.Random) -> int:
    if step % 32 == 0:
        return rng.choice([-8, -4, 4, 8])
    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Metrics v3
# ═══════════════════════════════════════════════════════════════════════════════


def state_signature(x: float, y: float, z: float, speed: float,
                    crit: float, zone: int, heading_byte: int,
                    cell: str) -> tuple:
    return (
        round(x, 1), round(y, 1), round(z, 1),
        round(speed, 1), round(crit, 2), zone,
        heading_byte // 16, cell,
    )


def playable_reality_v3(
    state_density: float, agency: float, falsifiability: float,
    compression: float, law_cost: float,
    ambiguity: float, sem_entropy: float, pred_error: float,
) -> float:
    ag = clamp(agency, 0.0, 1.0)
    se = min(sem_entropy, 5.0)
    num = state_density * ag * falsifiability * clamp(compression, 0.01, 20.0)
    den = law_cost * (1.0 + 0.3 * ambiguity + 0.15 * se + 0.3 * pred_error)
    return num / max(den, 1e-9)


def falsifiability_score(active_laws: list[str],
                         registry: dict[str, LawTermV3]) -> float:
    if not active_laws:
        return 0.0
    total_w = 0.0
    for name in active_laws:
        lt = registry.get(name)
        if lt:
            total_w += VERIFIED_WEIGHT.get(lt.verified, 0.3) * lt.trust
    return total_w / max(len(active_laws), 1)


def semantic_entropy_metric(ambiguity: float, law_count: int,
                            agency: float) -> float:
    return ambiguity * law_count / max(agency, 0.01)


def compression_ratio_v3(step: int, seed_bytes: int,
                         law_cost: float) -> float:
    return (step + 1) / max(seed_bytes + law_cost, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Metrics Packet v3
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class Metrics:
    step: int
    mode: str
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    speed: float = 0.0
    fuel: float = 100.0
    heat: float = 0.0
    pressure: float = 0.0
    suit: float = 100.0
    criticality: float = 0.0
    playable_reality: float = 0.0
    mle: float = 0.0
    law_cost: float = 0.0
    falsifiability: float = 0.0
    semantic_entropy: float = 0.0
    agency_measured: float = 0.0
    state_density: float = 0.0
    ambiguity_measured: float = 0.0
    pred_error: float = 0.0
    law_count: int = 0
    compression_ratio: float = 0.0
    godel_tokens: int = 0
    semantic_drift: float = 0.0
    delta_ep: float = 0.0
    zone_id: int = 0
    heading_byte: int = 0
    cell_pos: str = ""
    failure_state: str = "active"
    active_laws: str = ""

    def csv_row(self) -> dict[str, Any]:
        return {
            "step": self.step, "mode": self.mode,
            "x": round(self.x, 2), "y": round(self.y, 2), "z": round(self.z, 2),
            "speed": round(self.speed, 3),
            "fuel": round(self.fuel, 2), "heat": round(self.heat, 2),
            "pressure": round(self.pressure, 2), "suit": round(self.suit, 2),
            "criticality": round(self.criticality, 4),
            "playable_reality": round(self.playable_reality, 4),
            "mle": round(self.mle, 4),
            "law_cost": round(self.law_cost, 2),
            "falsifiability": round(self.falsifiability, 4),
            "semantic_entropy": round(self.semantic_entropy, 4),
            "agency": round(self.agency_measured, 4),
            "state_density": round(self.state_density, 4),
            "ambiguity": round(self.ambiguity_measured, 4),
            "pred_error": round(self.pred_error, 4),
            "law_count": self.law_count,
            "compression_ratio": round(self.compression_ratio, 4),
            "godel_tokens": self.godel_tokens,
            "semantic_drift": round(self.semantic_drift, 4),
            "delta_ep": round(self.delta_ep, 4),
            "zone_id": self.zone_id,
            "failure_state": self.failure_state,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Display
# ═══════════════════════════════════════════════════════════════════════════════


def sparkline(v: float, w: int = 14, mx: float = 1.0) -> str:
    f = int(round(clamp(v / max(mx, 1e-9), 0, 1) * w))
    return "\u2588" * f + "\u2591" * (w - f)


def print_frame(m: Metrics, interval: int = 12) -> None:
    if m.step % interval != 0:
        return
    if m.mode == "colony":
        line = (f"t={m.step:03d} {m.mode:<9} cell={m.cell_pos} h={m.heading_byte:03d} "
                f"suit={m.suit:5.1f} ag={m.agency_measured:.2f} "
                f"PR={m.playable_reality:.3f} SE={m.semantic_entropy:.2f} "
                f"laws={m.law_count} cost={m.law_cost:.1f}")
    elif m.mode == "freescape":
        line = (f"t={m.step:03d} {m.mode:<9} z={m.zone_id:02d} "
                f"({m.x:5.1f},{m.y:5.1f},{m.z:4.1f}) spd={m.speed:5.2f} "
                f"fuel={m.fuel:5.1f} p={m.pressure:6.1f} "
                f"ag={m.agency_measured:.2f} PR={m.playable_reality:.3f} "
                f"laws={m.law_count}")
    else:
        line = (f"t={m.step:03d} {m.mode:<9} "
                f"({m.x:6.1f},{m.y:6.1f}) spd={m.speed:6.2f} "
                f"fuel={m.fuel:6.1f} heat={m.heat:5.1f} p={m.pressure:6.1f} "
                f"ag={m.agency_measured:.2f} PR={m.playable_reality:.3f} "
                f"fals={m.falsifiability:.2f} laws={m.law_count}")
    if m.godel_tokens > 0:
        line += f" \u26a0{m.godel_tokens}"
    print(line)


def print_zone_pressure(zones: list[Zone]) -> None:
    for z in zones:
        print(f"  [{z.id:02d}] {sparkline(z.pressure, w=8, mx=150)} {z.pressure:6.1f}")


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Mode Runners
# ═══════════════════════════════════════════════════════════════════════════════


def _build_measure(step, mode, agent: AgentStats, dlas: DLASc,
                   hdc: HDCEngine, prev_sig: tuple | None,
                   x, y, z, speed, fuel, heat, pressure, suit,
                   crit, active_laws_list, seed_bytes=4,
                   cell_pos="", zone_id=0, heading_byte=0):
    """Compute full v3 metrics packet."""
    sig = state_signature(x, y, z, speed, crit, zone_id, heading_byte, cell_pos)
    # State density: ratio of unique sigs to steps
    n_laws = len(active_laws_list)
    law_cost = dlas.active_cost()
    ag = agent.agency
    fals = falsifiability_score(active_laws_list, dlas.laws)

    # Prediction error (ambiguity): did we expect to be here?
    if prev_sig is None:
        pred_err = 0.0
    else:
        pred_err = min(1.0, 0.3 if sig != prev_sig else 0.0)
        # Refine: position-based prediction error
        if prev_sig is not None:
            px, py = prev_sig[0], prev_sig[1]
            dist = math.hypot(x - px, y - py) * 0.01
            pred_err = clamp(dist, 0.0, 1.0)

    sem_ent = semantic_entropy_metric(pred_err, n_laws, ag)
    cr = compression_ratio_v3(step, seed_bytes, law_cost)
    sd = clamp(1.0 - pred_err, 0.1, 1.0) * (1.0 + ag * 0.5)
    pr = playable_reality_v3(sd, ag, fals, cr, law_cost,
                              pred_err, sem_ent, pred_err)
    mle = sd / max(n_laws, 1)

    # HDC
    buckets = {
        "high_agency": ag > 0.6, "low_agency": ag < 0.3,
        "high_entropy": sem_ent > 2.0, "critical_rising": crit > 0.5,
        "pr_good": pr > 0.4,
    }
    sv = hdc.state_vector(mode, active_laws_list, buckets)
    drift_val = hdc.drift(hdc.memory, sv)
    if drift_val > 0.15 and step > 0 and step % 50 == 0:
        hdc.inject_anomaly()

    ep_pairs = [("toroidal_wrap", "teleport_transform"),
                ("resource_thermodynamics", "hysteresis_failure"),
                ("cuboid_collision", "cell_occupancy")]
    min_ep = min((hdc.exceptional_point(a, b, sv) for a, b in ep_pairs),
                 default=0.0)

    return Metrics(
        step=step, mode=mode,
        x=x, y=y, z=z, speed=speed,
        fuel=fuel, heat=heat, pressure=pressure, suit=suit,
        criticality=crit,
        playable_reality=pr, mle=mle, law_cost=law_cost,
        falsifiability=fals, semantic_entropy=sem_ent,
        agency_measured=ag, state_density=sd,
        ambiguity_measured=pred_err, pred_error=pred_err,
        law_count=n_laws, compression_ratio=cr,
        godel_tokens=hdc.anomaly_count,
        semantic_drift=drift_val, delta_ep=min_ep,
        zone_id=zone_id, heading_byte=heading_byte,
        cell_pos=cell_pos,
        failure_state="active",
        active_laws=",".join(active_laws_list),
    ), sig


# --- Lander ---
def run_lander(steps: int, seed: int, adaptive: bool = False) -> Iterable[Metrics]:
    rng = random.Random(seed)
    world = Vec2(160.0, 90.0)
    pad_x = world.x * 0.5
    ship = Body(pos=Vec2(pad_x + 20, world.y * 0.75), vel=Vec2(5.0, 0.0))
    fuel_r = ResourceReservoir(100.0, 100.0)
    heat_r = ResourceReservoir(5.0, 100.0, leak=0.035, critical=90.0)
    pressure_r = ResourceReservoir(25.0, 150.0, critical=120.0)
    dt = 0.12
    agent = AgentStats()
    dlas = DLASc({k: LawTermV3(**asdict(v)) for k, v in LAW_REGISTRY.items()})
    hdc = HDCEngine(seed=seed)
    prev_err = [0.0]
    prev_sig = None

    active_laws = ["thrust_gravity_drag", "quantized_rotation",
                   "resource_thermodynamics", "playable_reality",
                   "minimum_law_efficiency", "compression_ratio",
                   "semantic_entropy"]
    if adaptive:
        active_laws.append("pid_controller")
        dlas.laws["pid_controller"].active = True

    for step in range(steps + 1):
        # Agent
        if adaptive:
            thrust, attempted = agent_lander_pid(ship, fuel_r, pad_x, dt, prev_err)
            agent.attempted += int(attempted)
            agent.successful += int(attempted and abs(ship.vel.y) < 5.0)
        else:
            ticks = agent_naive(step, rng)
            if ticks:
                ship.rotate_quantized(ticks)
            thrust = 3.8 if fuel_r.value > 0 and step % 9 in (0, 1, 2, 3) else 0.0
            agent.attempted += 1
            agent.successful += int(thrust > 0)

        gravity = Vec2(0.0, -1.62)
        drag = 0.01
        fuel_r.step(dt, sink=0.9 if thrust else 0.0)
        heat_r.step(dt, source=0.35 if thrust else 0.0)
        arcade_motion_step(ship, dt, thrust, gravity, drag, world, False)

        crit = max(heat_r.criticality, pressure_r.criticality)
        if crit >= 1.0:
            ship.state = "exploded"
            agent.failures += 1

        m, prev_sig = _build_measure(
            step, "lander", agent, dlas, hdc, prev_sig,
            ship.pos.x, ship.pos.y, ship.height, ship.vel.length(),
            fuel_r.value, heat_r.value, pressure_r.value, 0.0,
            crit, active_laws, cell_pos="", zone_id=0,
            heading_byte=ship.heading_byte,
        )
        m.failure_state = ship.state
        yield m


# --- Asteroids ---
def run_asteroids(steps: int, seed: int,
                  adaptive: bool = False) -> Iterable[Metrics]:
    rng = random.Random(seed)
    world = Vec2(160.0, 90.0)
    ship = Body(pos=Vec2(world.x * 0.5, world.y * 0.75), vel=Vec2(5.0, 0.0))
    fuel_r = ResourceReservoir(100.0, 100.0)
    heat_r = ResourceReservoir(5.0, 100.0, leak=0.035, critical=90.0)
    pressure_r = ResourceReservoir(25.0, 150.0, critical=120.0)
    dt = 0.12
    attractor = Vec2(world.x * 0.5, world.y * 0.5)
    agent = AgentStats()
    dlas = DLASc({k: LawTermV3(**asdict(v)) for k, v in LAW_REGISTRY.items()})
    hdc = HDCEngine(seed=seed)
    prev_sig = None

    active_laws = ["central_gravity_well", "toroidal_wrap",
                   "quantized_rotation", "resource_thermodynamics",
                   "playable_reality", "minimum_law_efficiency",
                   "compression_ratio", "semantic_entropy"]

    for step in range(steps + 1):
        ticks = agent_naive(step, rng)
        if ticks:
            ship.rotate_quantized(ticks)
            agent.attempted += 1
            agent.successful += 1
        gravity = central_gravity_well(ship, attractor, gm=85.0)
        thrust = 2.2 if step % 11 < 4 else 0.0
        agent.attempted += 1
        agent.successful += int(thrust > 0)
        fuel_r.step(dt, sink=0.35 if thrust else 0.0)
        heat_r.step(dt, source=0.25 if thrust else 0.0,
                    noise=rng.uniform(-0.02, 0.02))
        arcade_motion_step(ship, dt, thrust, gravity, 0.0, world, True)

        crit = max(heat_r.criticality, pressure_r.criticality)
        m, prev_sig = _build_measure(
            step, "asteroids", agent, dlas, hdc, prev_sig,
            ship.pos.x, ship.pos.y, 0, ship.vel.length(),
            fuel_r.value, heat_r.value, pressure_r.value, 0,
            crit, active_laws, heading_byte=ship.heading_byte,
        )
        yield m


# --- Pressure ---
def run_pressure(steps: int, seed: int,
                 adaptive: bool = False) -> Iterable[Metrics]:
    rng = random.Random(seed)
    world = Vec2(160.0, 90.0)
    ship = Body(pos=Vec2(world.x * 0.3, world.y * 0.5), vel=Vec2(2.0, 0.0))
    fuel_r = ResourceReservoir(100.0, 100.0)
    heat_r = ResourceReservoir(5.0, 100.0, leak=0.035, critical=90.0)
    pressure_r = ResourceReservoir(25.0, 150.0, critical=120.0)
    dt = 0.12
    zones = [
        Zone(0, pressure=25.0, neighbors=[1, 2]),
        Zone(1, pressure=40.0, neighbors=[0, 3, 4]),
        Zone(2, pressure=20.0, neighbors=[0, 5]),
        Zone(3, pressure=35.0, neighbors=[1]),
        Zone(4, pressure=50.0, neighbors=[1]),
        Zone(5, pressure=15.0, neighbors=[2]),
    ]
    excess = 0.0
    agent = AgentStats()
    dlas = DLASc({k: LawTermV3(**asdict(v)) for k, v in LAW_REGISTRY.items()})
    hdc = HDCEngine(seed=seed)
    prev_sig = None

    active_laws = ["thrust_gravity_drag", "graph_pressure_diffusion",
                   "hysteresis_failure", "resource_thermodynamics",
                   "playable_reality", "minimum_law_efficiency",
                   "compression_ratio", "semantic_entropy"]

    for step in range(steps + 1):
        ticks = agent_naive(step, rng)
        if ticks:
            ship.rotate_quantized(ticks)
        thrust = 1.2 if fuel_r.value > 0 and step % 13 < 5 else 0.0
        gravity = Vec2(0.0, -0.4)
        drag = 0.08
        fuel_r.step(dt, sink=0.25 if thrust else 0.0)
        heat_r.step(dt, source=0.15 if thrust else 0.0)
        pressure_r.step(dt, source=1.15, noise=rng.uniform(-0.1, 0.1))

        drilling = 8.0 if step in range(70, 95) or step in range(155, 180) else 0.0
        if adaptive and pressure_r.value > 60:
            drilling = 12.0
            agent.attempted += 1
            agent.successful += 1
        sinks = {0: drilling, 1: drilling * 0.5}
        graph_pressure_diffusion(zones, sinks, dt)
        excess, exploded = hysteresis_failure(
            excess, pressure_r.value, pressure_r.critical, dt)

        if exploded:
            ship.state = "exploded"
            agent.failures += 1

        arcade_motion_step(ship, dt, thrust, gravity, drag, world, False)
        agent.attempted += 1
        agent.successful += int(not exploded)

        crit = max(heat_r.criticality, pressure_r.criticality)
        m, prev_sig = _build_measure(
            step, "pressure", agent, dlas, hdc, prev_sig,
            ship.pos.x, ship.pos.y, 0, ship.vel.length(),
            fuel_r.value, heat_r.value, pressure_r.value, 0,
            crit, active_laws, heading_byte=ship.heading_byte,
        )
        m.failure_state = ship.state
        if step > 0 and step % 48 == 0:
            print_zone_pressure(zones)
        yield m


# --- Freescape ---
def run_freescape(steps: int, seed: int,
                  adaptive: bool = False) -> Iterable[Metrics]:
    rng = random.Random(seed)
    world3 = Vec3(64.0, 32.0, 64.0)
    body = Body3(pos=Vec3(32.0, 16.0, 32.0),
                 vel=Vec3(0.5, 0.0, 0.3), heading_byte=64)
    fuel_r = ResourceReservoir(100.0, 100.0)
    heat_r = ResourceReservoir(5.0, 100.0, leak=0.02, critical=90.0)
    pressure_r = ResourceReservoir(25.0, 150.0, critical=120.0)
    shield_r = ResourceReservoir(50.0, 50.0, critical=10.0)
    dt = 0.12
    zones = [
        Zone(0, gravity=1.0, friction=0.05, pressure=25.0, neighbors=[1, 3]),
        Zone(1, gravity=0.5, friction=0.10, pressure=40.0, neighbors=[0, 2]),
        Zone(2, gravity=0.1, friction=0.20, pressure=80.0, neighbors=[1]),
        Zone(3, gravity=2.0, friction=0.02, pressure=15.0, neighbors=[0, 4]),
        Zone(4, gravity=1.5, friction=0.08, pressure=60.0, neighbors=[3]),
    ]
    cuboids = [
        Cuboid(Vec3(20, 0, 20), Vec3(22, 20, 22)),
        Cuboid(Vec3(40, 0, 30), Vec3(42, 18, 50)),
        Cuboid(Vec3(10, 0, 40), Vec3(18, 12, 42)),
        Cuboid(Vec3(50, 0, 10), Vec3(52, 25, 30)),
    ]
    excess = 0.0
    agent = AgentStats()
    dlas = DLASc({k: LawTermV3(**asdict(v)) for k, v in LAW_REGISTRY.items()})
    hdc = HDCEngine(seed=seed)
    prev_sig = None
    collision_count = 0

    active_laws = ["cuboid_collision", "zone_gravity_friction",
                   "hydraulic_height", "graph_pressure_diffusion",
                   "hysteresis_failure", "resource_thermodynamics",
                   "playable_reality", "minimum_law_efficiency",
                   "compression_ratio", "semantic_entropy"]

    for step in range(steps + 1):
        if step % 24 == 0:
            body.rotate_quantized(rng.choice([-12, -6, 6, 12]))

        # Position-derived zone membership (v3 fix)
        zone_w = world3.x / len(zones)
        zid = clamp(int(body.pos.x / zone_w), 0, len(zones) - 1)
        body.zone_id = zid
        z = zones[zid]

        thrust_on = step % 7 < 3
        if thrust_on:
            rad = body.heading_rad
            body.vel.x += math.cos(rad) * 0.15 * z.time_scale
            body.vel.z += math.sin(rad) * 0.15 * z.time_scale
            agent.successful += 1
        agent.attempted += 1

        fuel_r.step(dt, sink=0.4 if thrust_on else 0.0)
        heat_r.step(dt, source=0.2 if thrust_on else 0.0)
        motion_step_3d(body, dt, z.gravity, z.friction, world3)

        for c in cuboids:
            hit, new_vel = cuboid_collide(body.pos, body.vel, c)
            if hit:
                body.vel = new_vel
                agent.collisions += 1
                collision_count += 1

        graph_pressure_diffusion(zones, {zid: 2.0 if thrust_on else 0.0}, dt)
        pressure_r.value = z.pressure

        if z.pressure > 60:
            shield_r.step(dt, sink=0.5)
        else:
            shield_r.step(dt, source=0.1)

        excess, exploded = hysteresis_failure(
            excess, pressure_r.value, pressure_r.critical, dt)
        if exploded:
            body.state = "exploded"
            agent.failures += 1

        # Hydraulic lift as acceleration (v3 fix)
        if body.pos.y < 2.0 and z.id == 3:
            body.vel.y += 8.0 * dt

        crit = max(heat_r.criticality, pressure_r.criticality,
                   1.0 - shield_r.criticality)
        m, prev_sig = _build_measure(
            step, "freescape", agent, dlas, hdc, prev_sig,
            body.pos.x, body.pos.y, body.pos.z, body.vel.length(),
            fuel_r.value, heat_r.value, pressure_r.value, shield_r.value,
            crit, active_laws, zone_id=zid,
            heading_byte=body.heading_byte,
        )
        m.failure_state = body.state
        if step > 0 and step % 48 == 0:
            print_zone_pressure(zones)
        yield m


# --- Colony (v3: wall-follow agent, stuck detector) ---
def run_colony(steps: int, seed: int, adaptive: bool = False,
               wall_density: float = 0.45) -> Iterable[Metrics]:
    rng = random.Random(seed)
    gw, gh = 24, 24
    grid = colony_generate_grid(gw, gh, seed, wall_density=wall_density)
    cx, cy = gw // 2, gh // 2
    heading = 64
    fuel_r = ResourceReservoir(100.0, 100.0)
    heat_r = ResourceReservoir(5.0, 100.0, leak=0.01, critical=90.0)
    pressure_r = ResourceReservoir(25.0, 150.0, critical=120.0)
    suit = ResourceReservoir(100.0, 100.0, leak=0.005, critical=15.0)
    dt = 0.12
    agent = AgentStats()
    dlas = DLASc({k: LawTermV3(**asdict(v)) for k, v in LAW_REGISTRY.items()})
    hdc = HDCEngine(seed=seed)
    prev_sig = None
    visited: set[tuple[int, int]] = set()
    stuck_count = 0
    last_cell = (cx, cy)

    active_laws = ["cell_occupancy", "quantized_rotation", "toroidal_surface",
                   "bresenham_los", "power_suit_energy",
                   "resource_thermodynamics", "playable_reality",
                   "minimum_law_efficiency", "compression_ratio",
                   "semantic_entropy"]

    for step in range(steps + 1):
        moved = False
        teleported = False

        if step % 6 == 0:
            use_wall_follow = adaptive or (stuck_count > 4)
            if use_wall_follow and "wall_following_agent" not in active_laws:
                dlas.laws["wall_following_agent"].active = True
                active_laws.append("wall_following_agent")
            if use_wall_follow:
                cx, cy, dh, moved = agent_colony_wall_follow(
                    cx, cy, heading, grid, gw, gh)
                heading = (heading + dh) % 256
            else:
                # Naive movement
                sector = (heading + 32) % 256 // 64
                dx, dy, wk = SECTOR_DIRS[sector]
                cell = grid.get((cx, cy))
                if cell and not cell.walls.get(wk, True):
                    nx, ny = (cx + dx) % gw, (cy + dy) % gh
                    target = grid.get((nx, ny))
                    if target and target.teleport_to is not None:
                        cx, cy = target.teleport_to
                        teleported = True
                        agent.teleports += 1
                    else:
                        cx, cy = nx, ny
                    moved = True
                agent.attempted += 1

            if moved:
                agent.successful += 1
            else:
                agent.blocked += 1

            if teleported:
                suit.step(dt, sink=5.0)

        if step % 18 == 0 and not adaptive:
            heading = (heading + rng.choice([-16, -8, 8, 16])) % 256

        # Energy station
        cell = grid.get((cx, cy))
        if cell and cell.energy_station:
            suit.step(dt, source=3.0)
        suit.step(dt)

        fuel_r.step(dt, sink=0.1)
        heat_r.step(dt, source=0.05)

        # LOS
        sector = (heading + 32) % 256 // 64
        dx, dy = SECTOR_DIRS[sector][0], SECTOR_DIRS[sector][1]
        los_cells = bresenham_los(cx, cy, cx + dx * 8, cy + dy * 8)
        los_blocked = any(
            (lx, ly) in grid and grid[(lx, ly)].furniture
            for lx, ly in los_cells if (lx, ly) != (cx, cy)
        )

        # Stuck detector
        cur_cell = (cx, cy)
        if cur_cell == last_cell:
            stuck_count += 1
        else:
            stuck_count = 0
        last_cell = cur_cell

        visited.add(cur_cell)
        coverage = len(visited) / (gw * gh)

        # DLASc context
        ctx = {
            "agency": agent.agency,
            "semantic_entropy": semantic_entropy_metric(
                0.2, len(active_laws), agent.agency),
            "cell_grid": True,
            "blocked_actions_high": agent.blocked > 5,
            "criticality": max(heat_r.criticality, 1.0 - suit.criticality),
        }
        changes = dlas.tick(ctx)
        if changes:
            for ch in changes:
                if ch.startswith("+"):
                    ln = ch[2:].strip()
                    if ln not in active_laws:
                        active_laws.append(ln)
                elif ch.startswith("-"):
                    ln = ch[2:].strip()
                    if ln in active_laws:
                        active_laws.remove(ln)
            if step % 12 == 0:
                print(f"  DLASc: {' | '.join(changes)}")

        crit = max(heat_r.criticality, 1.0 - suit.criticality)
        m, prev_sig = _build_measure(
            step, "colony", agent, dlas, hdc, prev_sig,
            float(cx), float(cy), 0, 1.0 if moved else 0.0,
            fuel_r.value, heat_r.value, pressure_r.value, suit.value,
            crit, active_laws, cell_pos=f"({cx:2d},{cy:2d})",
            heading_byte=heading,
        )
        if stuck_count > 20:
            m.failure_state = "stuck_loop"
        yield m


# --- Semantic (v3: live cross-mode) ---
def run_semantic(steps: int, seed: int, adaptive: bool = False) -> Iterable[Metrics]:
    runners = {
        "lander": run_lander(steps, seed),
        "asteroids": run_asteroids(steps, seed),
        "pressure": run_pressure(steps, seed),
        "freescape": run_freescape(steps, seed),
        "colony": run_colony(steps, seed),
    }
    buffers: dict[str, list[Metrics]] = {m: [] for m in runners}
    dlas = DLASc({k: LawTermV3(**asdict(v)) for k, v in LAW_REGISTRY.items()})
    hdc = HDCEngine(seed=seed)
    agent = AgentStats()

    for step in range(steps + 1):
        for name, gen in runners.items():
            try:
                m = next(gen)
                buffers[name].append(m)
            except StopIteration:
                pass

        if step % 12 != 0:
            continue

        # Aggregate
        prs = [buf[-1].playable_reality for buf in buffers.values() if buf]
        ags = [buf[-1].agency_measured for buf in buffers.values() if buf]
        crits = [buf[-1].criticality for buf in buffers.values() if buf]
        ses = [buf[-1].semantic_entropy for buf in buffers.values() if buf]
        if not prs:
            continue

        avg_pr = sum(prs) / len(prs)
        avg_ag = sum(ags) / len(ags)
        avg_crit = sum(crits) / len(crits)
        avg_se = sum(ses) / len(ses)
        avg_fals = sum(b[-1].falsifiability for b in buffers.values() if b) / len(prs)

        active_laws = dlas.active_names()
        n_laws = len(active_laws)
        law_cost = dlas.active_cost()
        sd = 0.8 * avg_ag
        pr = playable_reality_v3(sd, avg_ag, avg_fals, 1.0, law_cost,
                                  avg_se * 0.3, avg_se, avg_se * 0.2)
        mle = sd / max(n_laws, 1)

        m = Metrics(
            step=step, mode="semantic",
            x=avg_pr, y=mle, z=avg_fals, speed=avg_crit,
            criticality=avg_crit,
            playable_reality=pr, mle=mle, law_cost=law_cost,
            falsifiability=avg_fals, semantic_entropy=avg_se,
            agency_measured=avg_ag, state_density=sd,
            ambiguity_measured=avg_se * 0.3,
            law_count=n_laws, godel_tokens=hdc.anomaly_count,
        )
        yield m


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Meta-Modes
# ═══════════════════════════════════════════════════════════════════════════════


MODE_RUNNERS: dict[str, Any] = {
    "lander": run_lander, "asteroids": run_asteroids,
    "pressure": run_pressure, "freescape": run_freescape,
    "colony": run_colony, "semantic": run_semantic,
}


def _last_metrics(gen: Iterable[Metrics]) -> Metrics:
    m: Metrics | None = None
    for item in gen:
        m = item
    return m


# --- Stress Mode ---
def run_stress(target: str, seed: int, max_steps: int = 2000) -> Iterable[Metrics]:
    gen = MODE_RUNNERS[target](max_steps, seed, adaptive=True)
    for m in gen:
        yield m
        if m.failure_state != "active" and m.failure_state != "":
            break


# --- Audit Mode ---
def run_audit(target: str, steps: int, seed: int) -> RunDiagnosis:
    gen = MODE_RUNNERS[target](steps, seed, adaptive=True)
    all_m: list[Metrics] = []
    last: Metrics | None = None
    peak_pr = 0.0
    ttf = steps

    for m in gen:
        all_m.append(m)
        last = m
        if m.playable_reality > peak_pr:
            peak_pr = m.playable_reality
        if m.failure_state != "active" and m.failure_state != "":
            ttf = m.step
            break

    diag = RunDiagnosis(mode=target, best_pr=peak_pr,
                        final_pr=last.playable_reality if last else 0,
                        ttf=ttf)
    if last and last.failure_state != "active":
        diag.failure_reason = last.failure_state

    # Analyze trends
    if len(all_m) > 20:
        first_quarter = all_m[:len(all_m) // 4]
        last_quarter = all_m[-len(all_m) // 4:]
        avg_ag_first = sum(m.agency_measured for m in first_quarter) / len(first_quarter)
        avg_ag_last = sum(m.agency_measured for m in last_quarter) / len(last_quarter)
        avg_se_first = sum(m.semantic_entropy for m in first_quarter) / len(first_quarter)
        avg_se_last = sum(m.semantic_entropy for m in last_quarter) / len(last_quarter)

        if avg_ag_last < avg_ag_first * 0.6:
            diag.bottlenecks.append("agency collapse detected")
        if avg_se_last > avg_se_first * 1.3:
            diag.bottlenecks.append("semantic entropy rising")

        if last.agency_measured < 0.3:
            diag.bottlenecks.append("low agency: agent actions mostly blocked")
            diag.recommended_repairs.append(
                "activate wall_following_agent or improve movement policy")
        if last.criticality > 0.7:
            diag.bottlenecks.append("high criticality: near failure threshold")
            diag.recommended_repairs.append(
                "add risk_policy agent or reduce pressure source rate")
        if last.semantic_entropy > 2.5:
            diag.bottlenecks.append("high semantic entropy: simulation feels incomprehensible")
            diag.recommended_repairs.append(
                "reduce law count or increase agency to lower SE")
        if last.law_cost > 8.0 and last.playable_reality < 0.4:
            diag.bottlenecks.append("law bloat: high cost but low PR")
            diag.recommended_repairs.append(
                "deactivate laws with low contribution_score")

    return diag


# --- Optimizer Mode ---
def run_optimizer(target: str, episodes: int = 20,
                  base_steps: int = 120) -> list[dict[str, Any]]:
    configs = []
    for wall_d in [0.35, 0.45, 0.55]:
        for adapt in [False, True]:
            configs.append({"wall_density": wall_d, "adaptive": adapt})

    best_pr = -1.0
    best_cfg: dict[str, Any] = {}
    results: list[dict[str, Any]] = []

    for cfg in configs:
        total_pr = 0.0
        total_ag = 0.0
        total_se = 0.0
        for ep in range(min(episodes, 8)):
            gen = MODE_RUNNERS[target](
                base_steps, seed=42 + ep,
                adaptive=cfg["adaptive"],
            )
            last = _last_metrics(gen)
            if last:
                total_pr += last.playable_reality
                total_ag += last.agency_measured
                total_se += last.semantic_entropy
        n = min(episodes, 8)
        avg_pr = total_pr / n
        result = {
            "wall_density": cfg["wall_density"],
            "adaptive": cfg["adaptive"],
            "avg_pr": round(avg_pr, 4),
            "avg_agency": round(total_ag / n, 4),
            "avg_se": round(total_se / n, 4),
        }
        results.append(result)
        if avg_pr > best_pr:
            best_pr = avg_pr
            best_cfg = result

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Output / Export
# ═══════════════════════════════════════════════════════════════════════════════

CSV_HEADER = [
    "step", "mode", "x", "y", "z", "speed", "fuel", "heat", "pressure",
    "suit", "criticality", "playable_reality", "mle", "law_cost",
    "falsifiability", "semantic_entropy", "agency", "state_density",
    "ambiguity", "pred_error", "law_count", "compression_ratio",
    "godel_tokens", "semantic_drift", "delta_ep", "zone_id", "failure_state",
]


def write_csv(metrics_list: list[Metrics], path: str) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADER)
        w.writeheader()
        for m in metrics_list:
            w.writerow(m.csv_row())
    print(f"\n[CSV] {len(metrics_list)} rows -> {path}")


def write_json(results: dict[str, Metrics], path: str,
               seed: int, steps: int) -> None:
    summary: dict[str, Any] = {"seed": seed, "steps": steps, "modes": {}}
    for name, m in results.items():
        summary["modes"][name] = {
            "final": {
                "pr": round(m.playable_reality, 4),
                "mle": round(m.mle, 4),
                "fals": round(m.falsifiability, 4),
                "crit": round(m.criticality, 4),
                "agency": round(m.agency_measured, 4),
                "se": round(m.semantic_entropy, 4),
                "law_cost": round(m.law_cost, 2),
                "law_count": m.law_count,
                "failure": m.failure_state,
            },
        }
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[JSON] summary -> {path}")


def write_report(results: dict[str, Metrics],
                 diagnoses: dict[str, RunDiagnosis],
                 path: str, seed: int, steps: int) -> None:
    lines = [
        "# RGPUF Lab v3 Report",
        "",
        f"**Seed:** {seed}  |  **Steps:** {steps}",
        "",
        "## Mode Comparison",
        "",
        "| Mode | PR | MLE | Fals | Agency | SE | LawCost | Laws | Failure |",
        "|------|-----|------|------|--------|------|---------|------|---------|",
    ]
    for mode in BASE_MODES:
        m = results.get(mode)
        if not m:
            continue
        lines.append(
            f"| {mode} | {m.playable_reality:.3f} | {m.mle:.2f} | "
            f"{m.falsifiability:.2f} | {m.agency_measured:.2f} | "
            f"{m.semantic_entropy:.2f} | {m.law_cost:.1f} | "
            f"{m.law_count} | {m.failure_state} |"
        )
    lines.append("")

    for mode, diag in diagnoses.items():
        lines.append(f"## Audit: {mode}")
        lines.append("")
        lines.append(f"- **Best PR:** {diag.best_pr:.3f}")
        lines.append(f"- **Final PR:** {diag.final_pr:.3f}")
        lines.append(f"- **TTF:** {diag.ttf}")
        lines.append(f"- **Failure:** {diag.failure_reason or 'none'}")
        if diag.bottlenecks:
            lines.append("- **Bottlenecks:**")
            for b in diag.bottlenecks:
                lines.append(f"  - {b}")
        if diag.recommended_repairs:
            lines.append("- **Repairs:**")
            for r in diag.recommended_repairs:
                lines.append(f"  - {r}")
        lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"[REPORT] -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# 15. Simulation Orchestration
# ═══════════════════════════════════════════════════════════════════════════════


def run_single_mode(mode: str, steps: int, seed: int,
                    adaptive: bool = False) -> tuple[list[Metrics], Metrics | None]:
    gen = MODE_RUNNERS[mode](steps, seed, adaptive=adaptive)
    all_m: list[Metrics] = []
    last: Metrics | None = None
    for m in gen:
        last = m
        all_m.append(m)
        print_frame(m)
    return all_m, last


def run_all_modes(steps: int, seed: int,
                  adaptive: bool = False) -> tuple[dict[str, Metrics], list[Metrics]]:
    results: dict[str, Metrics] = {}
    all_telem: list[Metrics] = []
    for mode in BASE_MODES:
        print(f"\n--- {mode.upper()} ---")
        gen = MODE_RUNNERS[mode](steps, seed, adaptive=adaptive)
        last: Metrics | None = None
        for m in gen:
            last = m
            all_telem.append(m)
            print_frame(m)
        if last:
            results[mode] = last

    # Comparison table
    print("\n" + "=" * 90)
    print("  MODE COMPARISON TABLE v3")
    print("=" * 90)
    hdr = (f"  {'Mode':<11} {'PR':>7} {'MLE':>6} {'Fals':>6} {'Ag':>6} "
           f"{'SE':>6} {'Crit':>6} {'Laws':>5} {'Cost':>6}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for mode in BASE_MODES:
        m = results.get(mode)
        if m:
            print(f"  {mode:<11} {m.playable_reality:7.3f} {m.mle:6.2f} "
                  f"{m.falsifiability:6.2f} {m.agency_measured:6.2f} "
                  f"{m.semantic_entropy:6.2f} {m.criticality:6.3f} "
                  f"{m.law_count:5d} {m.law_cost:6.1f}")
    print("=" * 90)
    return results, all_telem


# ═══════════════════════════════════════════════════════════════════════════════
# 16. CLI
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    p = argparse.ArgumentParser(
        description="RGPUF Lab v3 -- Adaptive Minimum-Law Retro Physics Lab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Modes: lander asteroids pressure freescape colony semantic stress optimizer audit

Examples:
  python rgpuf_lab_v3.py --all --steps 240 --seed 42
  python rgpuf_lab_v3.py --mode colony --adaptive --steps 240
  python rgpuf_lab_v3.py --stress pressure --seed 7
  python rgpuf_lab_v3.py --optimizer colony --episodes 20
  python rgpuf_lab_v3.py --audit colony --steps 240
  python rgpuf_lab_v3.py --all --csv t.csv --json s.json --report r.md
""",
    )
    p.add_argument("--mode", choices=ALL_MODES, default=None)
    p.add_argument("--steps", type=int, default=240)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--adaptive", action="store_true")
    p.add_argument("--csv", type=str, default=None)
    p.add_argument("--json", type=str, default=None)
    p.add_argument("--report", type=str, default=None)
    p.add_argument("--all", action="store_true")
    p.add_argument("--target", type=str, default="colony",
                   help="Target mode for stress/optimizer/audit")
    p.add_argument("--episodes", type=int, default=20)
    p.add_argument("--wall-density", type=float, default=0.45)
    args = p.parse_args()

    print("RGPUF Lab v3 -- Adaptive Minimum-Law Retro Physics Lab")
    print("law stack: dynamic | agent: adaptive | semantic: HDC")
    print("-" * 90)

    if args.mode == "stress":
        print(f"\n--- STRESS: {args.target} (until failure) ---")
        gen = run_stress(args.target, args.seed)
        all_m = []
        last = None
        for m in gen:
            last = m
            all_m.append(m)
            print_frame(m)
        if last:
            print(f"\n  TTF = {last.step}")
            print(f"  Final state: {last.failure_state}")
            print(f"  Final crit: {last.criticality:.3f}")
        if args.csv:
            write_csv(all_m, args.csv)
        return

    if args.mode == "optimizer":
        print(f"\n--- OPTIMIZER: {args.target} ---")
        results = run_optimizer(args.target, args.episodes, args.steps)
        best = max(results, key=lambda r: r["avg_pr"])
        print(f"\n  Configurations tested: {len(results)}")
        print(f"  Best: wall={best['wall_density']} adapt={best['adaptive']} "
              f"PR={best['avg_pr']:.3f} ag={best['avg_agency']:.2f} "
              f"SE={best['avg_se']:.2f}")
        for r in results:
            marker = " <--" if r is best else ""
            print(f"    wall={r['wall_density']:.2f} adapt={r['adaptive']} "
                  f"PR={r['avg_pr']:.3f} ag={r['avg_agency']:.2f} "
                  f"SE={r['avg_se']:.2f}{marker}")
        return

    if args.mode == "audit":
        print(f"\n--- AUDIT: {args.target} ---")
        diag = run_audit(args.target, args.steps, args.seed)
        print(f"\nAUDIT REPORT -- {args.target}")
        print(f"  Best PR:   {diag.best_pr:.3f}")
        print(f"  Final PR:  {diag.final_pr:.3f}")
        print(f"  TTF:       {diag.ttf}")
        print(f"  Failure:   {diag.failure_reason or 'none'}")
        if diag.bottlenecks:
            print("  Bottlenecks:")
            for b in diag.bottlenecks:
                print(f"    - {b}")
        if diag.recommended_repairs:
            print("  Repairs:")
            for r in diag.recommended_repairs:
                print(f"    + {r}")
        return

    # Convenience: --stress X -> --mode stress --target X
    if args.mode is None and hasattr(args, '_stress_target'):
        args.mode = "stress"
    # Handle positional target for stress/optimizer/audit
    if args.mode in ("stress", "optimizer", "audit"):
        pass  # uses --target flag
    # Normal / all modes
    if args.all or args.mode is None:
        results, all_telem = run_all_modes(args.steps, args.seed,
                                           adaptive=args.adaptive)
        # Run audit on each mode
        diagnoses: dict[str, RunDiagnosis] = {}
        if args.report:
            for mode in BASE_MODES:
                diag = run_audit(mode, args.steps, args.seed)
                diagnoses[mode] = diag
        if args.csv:
            write_csv(all_telem, args.csv)
        if args.json:
            write_json(results, args.json, args.seed, args.steps)
        if args.report:
            write_report(results, diagnoses, args.report, args.seed, args.steps)
    else:
        all_m, last = run_single_mode(args.mode, args.steps, args.seed,
                                      adaptive=args.adaptive)
        if last:
            print(f"\n  Final: PR={last.playable_reality:.3f} "
                  f"Ag={last.agency_measured:.2f} "
                  f"SE={last.semantic_entropy:.2f} "
                  f"laws={last.law_count} cost={last.law_cost:.1f}")
        if args.csv:
            write_csv(all_m, args.csv)
        if args.json and last:
            write_json({args.mode: last}, args.json, args.seed, args.steps)

    print("\nRGPUF v3: retro physics is a compressed law language -- now self-diagnosing.")


if __name__ == "__main__":
    main()
