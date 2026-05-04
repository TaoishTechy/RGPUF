#!/usr/bin/env python3
"""
RGPUF Lab v2 — Minimum-Law Retro Physics Lab
=============================================

Retro Game Physics Unified Framework — Minimum-Law Lab

A small executable science lab that proves: a small number of executable laws
can reproduce many retro-game physics families — landing, inertia, pressure,
heat, topology, procedural worlds, cell collision, teleportation, and
player-agency metrics.

Modes:
    lander    — Lunar Lander / Moonlander / MSFS landing dynamics
    asteroids — Spacewar! / Asteroids / Elite inertial motion
    pressure  — Driller pressure + MW2 heat + resource thermodynamics
    freescape — Driller / Freescape cuboid spatial logic + zone laws
    colony    — The Colony / 3-Demon cell grid + teleport + LOS
    semantic  — RGPUF analytics: compare modes scientifically

Run:
    python rgpuf_lab.py --mode asteroids --steps 240 --seed 42
    python rgpuf_lab.py --mode freescape --steps 360 --seed 7
    python rgpuf_lab.py --all --steps 240 --seed 42

Output:
    python rgpuf_lab.py --all --csv telemetry.csv --json summary.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Literal

Mode = Literal["lander", "asteroids", "pressure", "freescape", "colony", "semantic"]

TAU = math.tau

# ═══════════════════════════════════════════════════════════════════════════════
# 1. Math Primitives
# ═══════════════════════════════════════════════════════════════════════════════


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def wrap(value: float, size: float) -> float:
    """Toroidal boundary: Asteroids / 3-Demon / Elite / Colony wrap."""
    return value % size


@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, s: float) -> "Vec2":
        return Vec2(self.x * s, self.y * s)

    def dot(self, o: "Vec2") -> float:
        return self.x * o.x + self.y * o.y

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def distance_to(self, o: "Vec2") -> float:
        return (self - o).length()

    def rotate(self, rad: float) -> "Vec2":
        c, s = math.cos(rad), math.sin(rad)
        return Vec2(self.x * c - self.y * s, self.x * s + self.y * c)

    def normalized(self) -> "Vec2":
        mag = self.length()
        if mag <= 1e-9:
            return Vec2()
        return Vec2(self.x / mag, self.y / mag)


@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, s: float) -> "Vec3":
        return Vec3(self.x * s, self.y * s, self.z * s)

    def dot(self, o: "Vec3") -> float:
        return self.x * o.x + self.y * o.y + self.z * o.z

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def distance_to(self, o: "Vec3") -> float:
        return (self - o).length()

    def rotate_y(self, rad: float) -> "Vec3":
        c, s = math.cos(rad), math.sin(rad)
        return Vec3(self.x * c + self.z * s, self.y, -self.x * s + self.z * c)

    def normalized(self) -> "Vec3":
        mag = self.length()
        if mag <= 1e-9:
            return Vec3()
        return Vec3(self.x / mag, self.y / mag, self.z / mag)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Core Data Classes
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class Body:
    """Rigid body with 2D position, velocity, quantized heading, and extended state."""

    pos: Vec2 = field(default_factory=Vec2)
    vel: Vec2 = field(default_factory=Vec2)
    mass: float = 1.0
    radius: float = 1.0
    heading_byte: int = 64  # Colony / Elite 256-step pseudo-angle; 64 ≈ up
    height: float = 0.0  # for Freescape vertical axis
    mode: str = "ground"  # ground | flying | falling | maroon
    zone_id: int = 0
    state: str = "active"  # active | exploded | landed | dead

    @property
    def heading_rad(self) -> float:
        return (self.heading_byte / 256.0) * TAU

    @property
    def forward(self) -> Vec2:
        a = self.heading_rad
        return Vec2(math.cos(a), math.sin(a))

    def rotate_quantized(self, ticks: int) -> None:
        """The Colony / Elite byte-sized angular state — Eq. 5."""
        self.heading_byte = (self.heading_byte + ticks) % 256


@dataclass
class Body3:
    """3D body for Freescape / Colony spatial modes."""

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
    """
    Universal RGPUF resource law — Eq. 2:
        dR/dt = source(t) - sink(t) - leak * R + noise
    Usable for fuel, heat, pressure, oxygen, shield, power_suit, grain, agency.
    """

    value: float
    capacity: float
    leak: float = 0.0
    critical: float | None = None

    def step(self, dt: float, source: float = 0.0, sink: float = 0.0, noise: float = 0.0) -> None:
        self.value += (source - sink - self.leak * self.value + noise) * dt
        self.value = clamp(self.value, 0.0, self.capacity)

    @property
    def criticality(self) -> float:
        if self.critical is None or self.critical <= 0:
            return self.value / max(self.capacity, 1e-9)
        return self.value / self.critical


@dataclass
class Zone:
    """Per-zone physical laws — Driller / Freescape style — Eq. 4, 7."""

    id: int
    gravity: float = 1.0
    friction: float = 0.1
    light_radius: float = 999.0
    time_scale: float = 1.0
    pressure: float = 25.0
    neighbors: list[int] = field(default_factory=list)


@dataclass
class Cuboid:
    """Axis-aligned bounding box — Freespace / Driller constructive geometry."""

    mn: Vec3 = field(default_factory=Vec3)
    mx: Vec3 = field(default_factory=Vec3)
    solid: bool = True


def inside_cuboid(p: Vec3, c: Cuboid) -> bool:
    return c.mn.x <= p.x <= c.mx.x and c.mn.y <= p.y <= c.mx.y and c.mn.z <= p.z <= c.mx.z


def cuboid_collide(p: Vec3, vel: Vec3, c: Cuboid) -> tuple[bool, Vec3]:
    """Resolve body against solid cuboid. Returns (hit, new_vel)."""
    if not inside_cuboid(p, c) or not c.solid:
        return False, vel
    # Push out along axis of minimum penetration
    pen_x = min(p.x - c.mn.x, c.mx.x - p.x)
    pen_y = min(p.y - c.mn.y, c.mx.y - p.y)
    pen_z = min(p.z - c.mn.z, c.mx.z - p.z)
    if pen_x <= pen_y and pen_x <= pen_z:
        vel.x *= -0.3
        if p.x - c.mn.x < c.mx.x - p.x:
            p.x = c.mn.x - 0.01
        else:
            p.x = c.mx.x + 0.01
    elif pen_y <= pen_z:
        vel.y *= -0.3
        if p.y - c.mn.y < c.mx.y - p.y:
            p.y = c.mn.y - 0.01
        else:
            p.y = c.mx.y + 0.01
    else:
        vel.z *= -0.3
        if p.z - c.mn.z < c.mx.z - p.z:
            p.z = c.mn.z - 0.01
        else:
            p.z = c.mx.z + 0.01
    return True, vel


@dataclass
class Cell:
    """Colony / 3-Demon cell: compressed spatial law, not just a map tile."""

    walls: dict[str, bool] = field(default_factory=lambda: {"n": True, "s": True, "e": True, "w": True, "u": True, "d": True})
    object_id: int = 0
    furniture: bool = False
    teleport_to: tuple[int, int] | None = None
    energy_station: bool = False


@dataclass
class LawTerm:
    """Epistemic classification for each law — Section 13."""

    name: str
    active: bool
    cost: float
    verified: str  # "historical" | "equivalent" | "speculative"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Law Registry — Falsification Layer (Section 13)
# ═══════════════════════════════════════════════════════════════════════════════

VERIFIED_WEIGHT = {"historical": 1.0, "equivalent": 0.7, "speculative": 0.3}

LAW_REGISTRY: dict[str, LawTerm] = {
    # Motion family
    "thrust_gravity_drag":       LawTerm("thrust_gravity_drag",       True, 1.0, "equivalent"),
    "central_gravity_well":      LawTerm("central_gravity_well",      True, 1.2, "historical"),
    "quantized_rotation":        LawTerm("quantized_rotation",        True, 0.5, "historical"),
    # Topology family
    "toroidal_wrap":             LawTerm("toroidal_wrap",             True, 0.5, "historical"),
    "teleport_transform":        LawTerm("teleport_transform",        True, 1.0, "historical"),
    # Resource family
    "resource_thermodynamics":   LawTerm("resource_thermodynamics",   True, 1.0, "equivalent"),
    "graph_pressure_diffusion":  LawTerm("graph_pressure_diffusion",  True, 1.5, "equivalent"),
    "hysteresis_failure":        LawTerm("hysteresis_failure",        True, 1.5, "equivalent"),
    # Spatial family
    "cuboid_collision":          LawTerm("cuboid_collision",          True, 1.5, "historical"),
    "zone_gravity_friction":     LawTerm("zone_gravity_friction",     True, 1.0, "historical"),
    "hydraulic_height":          LawTerm("hydraulic_height",          True, 1.2, "equivalent"),
    # Colony family
    "cell_occupancy":            LawTerm("cell_occupancy",            True, 1.0, "historical"),
    "bresenham_los":             LawTerm("bresenham_los",             True, 0.8, "historical"),
    "toroidal_surface":          LawTerm("toroidal_surface",          True, 0.5, "historical"),
    "power_suit_energy":         LawTerm("power_suit_energy",         True, 1.0, "equivalent"),
    # Semantic family
    "playable_reality":          LawTerm("playable_reality",          True, 2.0, "speculative"),
    "minimum_law_efficiency":    LawTerm("minimum_law_efficiency",    True, 2.0, "speculative"),
    "compression_ratio":         LawTerm("compression_ratio",         True, 1.5, "speculative"),
    "semantic_entropy":          LawTerm("semantic_entropy",          True, 2.0, "speculative"),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Resource Laws (Eq. 2)
# ═══════════════════════════════════════════════════════════════════════════════

# Resource law is embodied in ResourceReservoir.step().  All modes share
# the same universal reservoir form: fuel, heat, pressure, oxygen, shield,
# power_suit are each a ResourceReservoir instance.


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Motion Laws (Eq. 1, 5, 6)
# ═══════════════════════════════════════════════════════════════════════════════

def arcade_motion_step(
    body: Body,
    dt: float,
    thrust: float,
    gravity: Vec2,
    drag: float,
    world_size: Vec2,
    wrap_edges: bool,
) -> None:
    """Unified arcade motion — Eq. 1:
        F = T * forward + m * g - drag * v + external
    """
    force = body.forward * thrust + gravity * body.mass - body.vel * drag
    acc = force * (1.0 / body.mass)
    body.vel = body.vel + acc * dt
    body.pos = body.pos + body.vel * dt

    if wrap_edges:
        body.pos.x = wrap(body.pos.x, world_size.x)
        body.pos.y = wrap(body.pos.y, world_size.y)
    else:
        if body.pos.x < 0 or body.pos.x > world_size.x:
            body.vel.x *= -0.85
            body.pos.x = clamp(body.pos.x, 0, world_size.x)
        if body.pos.y < 0:
            body.vel.y *= -0.30
            body.pos.y = 0
        if body.pos.y > world_size.y:
            body.vel.y *= -0.85
            body.pos.y = world_size.y


def motion_step_3d(
    body: Body3,
    dt: float,
    gravity: float,
    friction: float,
    world_size: Vec3,
    wrap_edges: bool = False,
) -> None:
    """3D motion with per-zone gravity and friction."""
    body.vel.y -= gravity * dt
    body.vel.x *= (1.0 - friction)
    body.vel.z *= (1.0 - friction)
    body.pos = body.pos + body.vel * dt
    if wrap_edges:
        body.pos.x = wrap(body.pos.x, world_size.x)
        body.pos.z = wrap(body.pos.z, world_size.z)
    else:
        body.pos.x = clamp(body.pos.x, 0, world_size.x)
        body.pos.z = clamp(body.pos.z, 0, world_size.z)
        if body.pos.y < 0:
            body.pos.y = 0
            body.vel.y *= -0.3


def central_gravity_well(body: Body, attractor: Vec2, gm: float, softening: float = 25.0) -> Vec2:
    """Spacewar!-style central force with softening."""
    delta = attractor - body.pos
    r2 = delta.x * delta.x + delta.y * delta.y + softening
    return delta.normalized() * (gm / r2)


def procedural_starfield(seed: int, count: int, world_size: Vec2) -> list[Vec2]:
    """Deterministic universe: law + seed > stored map."""
    rng = random.Random(seed)
    return [Vec2(rng.random() * world_size.x, rng.random() * world_size.y) for _ in range(count)]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Topology Laws (Eq. 6, 7)
# ═══════════════════════════════════════════════════════════════════════════════

# Toroidal wrap is already embodied in wrap().  Teleport transform — Eq. 7:

def teleport_transform(
    pos: Vec2,
    vel: Vec2,
    target: Vec2,
    delta_heading_byte: int,
) -> tuple[Vec2, Vec2, int]:
    """
    Teleport with orientation/velocity transform — Colony-style.
        p_new = target + rotate(p - door_origin, delta_angle)
        v_new = rotate(v, delta_angle)
    Simplified: we teleport to target and rotate velocity by delta angle.
    """
    delta_rad = (delta_heading_byte / 256.0) * TAU
    new_vel = vel.rotate(delta_rad)
    return target, new_vel, delta_heading_byte


def bresenham_los(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """Bresenham line-of-sight — Colony / 3-Demon family."""
    cells: list[tuple[int, int]] = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
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
    return cells


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Freescape Laws (Eq. 3, 4)
# ═══════════════════════════════════════════════════════════════════════════════

def graph_pressure_diffusion(
    zones: list[Zone],
    drill_sinks: dict[int, float],
    dt: float,
    diffusion_coeff: float = 0.08,
) -> None:
    """Eq. 3 — Driller pressure graph:
        dP_i = D * sum(P_j - P_i for j in neighbors) - drill_i
    """
    deltas = [0.0] * len(zones)
    for i, z in enumerate(zones):
        diff = sum(zones[j].pressure - z.pressure for j in z.neighbors)
        deltas[i] = (diffusion_coeff * diff - drill_sinks.get(z.id, 0.0)) * dt
    for i, z in enumerate(zones):
        z.pressure = max(0.0, z.pressure + deltas[i])


def hysteresis_failure(
    excess: float,
    pressure: float,
    critical: float,
    dt: float,
    threshold: float = 15.0,
) -> tuple[float, bool]:
    """Eq. 4 — Failure is memory, not instant threshold:
        excess += max(0, P - P_crit) * dt
        explode = excess > threshold
    """
    excess += max(0.0, pressure - critical) * dt
    return excess, excess > threshold


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Colony Laws (Eq. 5, 6, 7, cell_occupancy)
# ═══════════════════════════════════════════════════════════════════════════════

def colony_generate_grid(
    width: int, height: int, seed: int,
) -> dict[tuple[int, int], Cell]:
    """Procedural cell grid with teleport doors and energy stations."""
    rng = random.Random(seed)
    grid: dict[tuple[int, int], Cell] = {}
    for y in range(height):
        for x in range(width):
            w = {"n": True, "s": True, "e": True, "w": True, "u": False, "d": False}
            # Remove some walls procedurally
            if x < width - 1 and rng.random() < 0.35:
                w["e"] = False
            if y < height - 1 and rng.random() < 0.35:
                w["s"] = False
            tp = None
            if rng.random() < 0.03:
                tx, ty = rng.randint(0, width - 1), rng.randint(0, height - 1)
                tp = (tx, ty)
            grid[(x, y)] = Cell(
                walls=w,
                object_id=rng.randint(0, 3),
                furniture=rng.random() < 0.08,
                teleport_to=tp,
                energy_station=rng.random() < 0.04,
            )
    return grid


def colony_move(
    cx: int, cy: int, heading_byte: int,
    grid: dict[tuple[int, int], Cell],
    grid_w: int, grid_h: int,
) -> tuple[int, int, int, bool]:
    """
    Attempt Colony-style cell movement by heading. Returns (new_cx, new_cy, delta_heading, teleported).
    Uses the 256-step heading to determine direction.
    """
    # Map 256-step heading to 4 cardinal directions
    sector = (heading_byte + 32) % 256 // 64  # 0=N, 1=E, 2=S, 3=W
    dx, dy, wall_key = [(0, -1, "n"), (1, 0, "e"), (0, 1, "s"), (-1, 0, "w")][sector]
    cell = grid.get((cx, cy))
    if cell and not cell.walls.get(wall_key, True):
        nx = (cx + dx) % grid_w
        ny = (cy + dy) % grid_h
        target_cell = grid.get((nx, ny))
        if target_cell and target_cell.teleport_to is not None:
            return target_cell.teleport_to[0], target_cell.teleport_to[1], 0, True
        return nx, ny, 0, False
    # Blocked — rotate toward opening
    return cx, cy, 16, False


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Semantic Metrics (Section 7)
# ═══════════════════════════════════════════════════════════════════════════════

def playable_reality_score(
    state_density: float, agency: float, cost: float, ambiguity: float,
) -> float:
    """Eq. 8 — Headline metric:
        PR = (state_density * agency) / (cost * (1 + ambiguity))
    """
    return (state_density * agency) / max(cost * (1.0 + ambiguity), 1e-9)


def minimum_law_efficiency(perceived_world: float, active_law_count: int) -> float:
    """7.1 — How much world does each law generate?
        MLE = perceived_world / max(active_law_count, 1)
    """
    return perceived_world / max(active_law_count, 1)


def compression_ratio(generated_state_count: int, seed_bytes: int, law_bytes: int) -> float:
    """7.2 — Elite-style law-before-data score:
        CR = generated_states / max(seed_bytes + law_bytes, 1)
    """
    return generated_state_count / max(seed_bytes + law_bytes, 1)


def falsifiability_score(active_laws: list[str]) -> float:
    """7.3 — Verified / total:
        historical=1.0, equivalent=0.7, speculative=0.3
    """
    if not active_laws:
        return 0.0
    total = 0.0
    verified = 0.0
    for name in active_laws:
        lt = LAW_REGISTRY.get(name)
        if lt:
            total += 1.0
            verified += VERIFIED_WEIGHT.get(lt.verified, 0.0)
    return verified / max(total, 1e-9)


def criticality_score(heat: float, heat_crit: float, pressure: float, pressure_crit: float) -> float:
    """7.4 — When does play become failure?
        crit = max(heat/heat_crit, pressure/pressure_crit)
    """
    return max(
        heat / max(heat_crit, 1e-9),
        pressure / max(pressure_crit, 1e-9),
    )


def semantic_entropy_metric(ambiguity: float, law_count: int, agency: float) -> float:
    """7.5 — Incomprehensibility measure:
        SE = ambiguity * law_count / max(agency, 0.01)
    """
    return ambiguity * law_count / max(agency, 0.01)


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Metrics Packet (Section 7)
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
    criticality: float = 0.0
    playable_reality: float = 0.0
    law_count: int = 0
    compression_ratio: float = 0.0
    falsifiability: float = 0.0
    semantic_entropy: float = 0.0
    mle: float = 0.0
    # Extended state for display
    zone_id: int = 0
    heading_byte: int = 0
    cell_pos: str = ""

    def csv_row(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "mode": self.mode,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "z": round(self.z, 2),
            "speed": round(self.speed, 3),
            "fuel": round(self.fuel, 2),
            "heat": round(self.heat, 2),
            "pressure": round(self.pressure, 2),
            "criticality": round(self.criticality, 4),
            "playable_reality": round(self.playable_reality, 4),
            "law_count": self.law_count,
            "compression_ratio": round(self.compression_ratio, 4),
            "falsifiability": round(self.falsifiability, 4),
            "semantic_entropy": round(self.semantic_entropy, 4),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Display Utilities
# ═══════════════════════════════════════════════════════════════════════════════

def sparkline(value: float, width: int = 16, maximum: float = 1.0) -> str:
    v = clamp(value / max(maximum, 1e-9), 0.0, 1.0)
    filled = int(round(v * width))
    return "\u2588" * filled + "\u2591" * (width - filled)


def print_frame(m: Metrics, interval: int = 12) -> None:
    if m.step % interval != 0:
        return
    parts = [f"t={m.step:03d} mode={m.mode:<9}"]
    if m.mode == "colony":
        parts.append(f"cell={m.cell_pos} heading={m.heading_byte:03d}")
        parts.append(f"fuel={m.fuel:6.1f}")
    elif m.mode == "freescape":
        parts.append(f"zone={m.zone_id:02d} pos=({m.x:5.1f},{m.y:5.1f},{m.z:4.1f})")
        parts.append(f"speed={m.speed:5.2f} fuel={m.fuel:5.1f} heat={m.heat:5.1f} pressure={m.pressure:6.1f}")
    else:
        parts.append(f"pos=({m.x:6.1f},{m.y:6.1f}) speed={m.speed:6.2f}")
        parts.append(f"fuel={m.fuel:6.1f} heat={m.heat:6.1f} pressure={m.pressure:6.1f}")
    parts.append(f"crit={sparkline(m.criticality, maximum=1.25)}")
    parts.append(f"PR={m.playable_reality:7.3f} laws={m.law_count:2d} MLE={m.mle:5.2f} fals={m.falsifiability:.2f}")
    print(" ".join(parts))


def print_zone_pressure(zones: list[Zone]) -> None:
    for z in zones:
        bar = sparkline(z.pressure, width=8, maximum=150.0)
        print(f"  [{z.id:02d}] {bar} {z.pressure:6.1f}")


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Mode Initialization & Simulation Loop (Section 11)
# ═══════════════════════════════════════════════════════════════════════════════

# Each mode returns a generator of Metrics.  The shared loop architecture:
#
#   for step in range(steps + 1):
#       inputs = scripted_input(mode, step, seed)
#       active_laws = apply_mode_laws(state, inputs, mode)
#       metrics = measure(state, active_laws)
#       yield metrics


def _measure_common(
    step: int, mode: str,
    body: Body,
    fuel: ResourceReservoir, heat: ResourceReservoir, pressure: ResourceReservoir,
    active_laws: list[str],
    state_density: float, agency: float, cost: float, ambiguity: float,
    zone_id: int = 0,
) -> Metrics:
    """Compute full Metrics packet from common state."""
    n_laws = max(len(active_laws), 1)
    pr = playable_reality_score(state_density, agency, cost=n_laws, ambiguity=ambiguity)
    mle = minimum_law_efficiency(state_density, n_laws)
    cr = compression_ratio(step + 1, seed_bytes=4, law_bytes=n_laws * 8)
    fals = falsifiability_score(active_laws)
    se = semantic_entropy_metric(ambiguity, n_laws, agency)
    return Metrics(
        step=step,
        mode=mode,
        x=body.pos.x,
        y=body.pos.y,
        speed=body.vel.length(),
        fuel=fuel.value,
        heat=heat.value,
        pressure=pressure.value,
        criticality=max(heat.criticality, pressure.criticality),
        playable_reality=pr,
        law_count=n_laws,
        compression_ratio=cr,
        falsifiability=fals,
        semantic_entropy=se,
        mle=mle,
        zone_id=zone_id,
        heading_byte=body.heading_byte,
    )


def run_lander(steps: int, seed: int) -> Iterable[Metrics]:
    """Mode 1 — Tennis for Two -> Lunar Lander -> Moonlander -> MSFS."""
    rng = random.Random(seed)
    world = Vec2(160.0, 90.0)
    ship = Body(pos=Vec2(world.x * 0.5, world.y * 0.75), vel=Vec2(5.0, 0.0))
    fuel = ResourceReservoir(value=100.0, capacity=100.0)
    heat = ResourceReservoir(value=5.0, capacity=100.0, leak=0.035, critical=90.0)
    pressure = ResourceReservoir(value=25.0, capacity=150.0, critical=120.0)
    dt = 0.12
    active_laws = [
        "thrust_gravity_drag", "quantized_rotation",
        "resource_thermodynamics", "playable_reality",
    ]

    for step in range(steps + 1):
        if step % 32 == 0:
            ship.rotate_quantized(rng.choice([-8, -4, 4, 8]))
        thrust = 3.8 if fuel.value > 0 and step % 9 in (0, 1, 2, 3) else 0.0
        gravity = Vec2(0.0, -1.62)
        drag = 0.01
        fuel.step(dt, sink=0.9 if thrust else 0.0)
        heat.step(dt, source=0.35 if thrust else 0.0)
        arcade_motion_step(ship, dt, thrust, gravity, drag, world, wrap_edges=False)
        yield _measure_common(
            step, "lander", ship, fuel, heat, pressure,
            active_laws, state_density=3.0, agency=0.8, cost=1.0, ambiguity=0.15,
        )


def run_asteroids(steps: int, seed: int) -> Iterable[Metrics]:
    """Mode 2 — Spacewar! -> Computer Space -> Asteroids -> Elite."""
    rng = random.Random(seed)
    world = Vec2(160.0, 90.0)
    stars = procedural_starfield(seed, 64, world)
    ship = Body(pos=Vec2(world.x * 0.5, world.y * 0.75), vel=Vec2(5.0, 0.0))
    fuel = ResourceReservoir(value=100.0, capacity=100.0)
    heat = ResourceReservoir(value=5.0, capacity=100.0, leak=0.035, critical=90.0)
    pressure = ResourceReservoir(value=25.0, capacity=150.0, critical=120.0)
    dt = 0.12
    attractor = Vec2(world.x * 0.5, world.y * 0.5)
    active_laws = [
        "central_gravity_well", "toroidal_wrap", "quantized_rotation",
        "resource_thermodynamics", "playable_reality",
    ]

    for step in range(steps + 1):
        if step % 32 == 0:
            ship.rotate_quantized(rng.choice([-8, -4, 4, 8]))
        gravity = central_gravity_well(ship, attractor, gm=85.0)
        thrust = 2.2 if step % 11 < 4 else 0.0
        drag = 0.0
        fuel.step(dt, sink=0.35 if thrust else 0.0)
        heat.step(dt, source=0.25 if thrust else 0.0, noise=rng.uniform(-0.02, 0.02))
        arcade_motion_step(ship, dt, thrust, gravity, drag, world, wrap_edges=True)
        yield _measure_common(
            step, "asteroids", ship, fuel, heat, pressure,
            active_laws, state_density=4.5, agency=0.9, cost=1.2, ambiguity=0.25,
        )


def run_pressure(steps: int, seed: int) -> Iterable[Metrics]:
    """Mode 3 — Driller pressure + MW2 heat + resource thermodynamics."""
    rng = random.Random(seed)
    world = Vec2(160.0, 90.0)
    ship = Body(pos=Vec2(world.x * 0.3, world.y * 0.5), vel=Vec2(2.0, 0.0))
    fuel = ResourceReservoir(value=100.0, capacity=100.0)
    heat = ResourceReservoir(value=5.0, capacity=100.0, leak=0.035, critical=90.0)
    pressure = ResourceReservoir(value=25.0, capacity=150.0, critical=120.0)
    dt = 0.12

    # Build pressure zone graph — 6 zones
    zones = [
        Zone(id=0, pressure=25.0, neighbors=[1, 2]),
        Zone(id=1, pressure=40.0, neighbors=[0, 3, 4]),
        Zone(id=2, pressure=20.0, neighbors=[0, 5]),
        Zone(id=3, pressure=35.0, neighbors=[1]),
        Zone(id=4, pressure=50.0, neighbors=[1]),
        Zone(id=5, pressure=15.0, neighbors=[2]),
    ]
    excess_integral = 0.0
    active_laws = [
        "thrust_gravity_drag", "graph_pressure_diffusion",
        "hysteresis_failure", "resource_thermodynamics", "playable_reality",
    ]

    for step in range(steps + 1):
        if step % 32 == 0:
            ship.rotate_quantized(rng.choice([-8, -4, 4, 8]))
        thrust = 1.2 if fuel.value > 0 and step % 13 < 5 else 0.0
        gravity = Vec2(0.0, -0.4)
        drag = 0.08
        fuel.step(dt, sink=0.25 if thrust else 0.0)
        heat.step(dt, source=0.15 if thrust else 0.0)
        pressure.step(dt, source=1.15, noise=rng.uniform(-0.1, 0.1))

        drilling = 8.0 if step in range(70, 95) or step in range(155, 180) else 0.0
        sinks = {0: drilling, 1: drilling * 0.5, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        graph_pressure_diffusion(zones, sinks, dt)

        excess_integral, exploded = hysteresis_failure(
            excess_integral, pressure.value, pressure.critical, dt,
        )
        if exploded:
            ship.state = "exploded"

        arcade_motion_step(ship, dt, thrust, gravity, drag, world, wrap_edges=False)

        agency = 0.75 if drilling > 0 else 0.55
        m = _measure_common(
            step, "pressure", ship, fuel, heat, pressure,
            active_laws, state_density=5.0, agency=agency, cost=1.1, ambiguity=0.35,
        )
        yield m

        # Print zone pressure map every 48 steps
        if step > 0 and step % 48 == 0:
            print_zone_pressure(zones)


def run_freescape(steps: int, seed: int) -> Iterable[Metrics]:
    """Mode 4 — Driller / Freescape cuboid spatial logic + zone laws."""
    rng = random.Random(seed)
    world3 = Vec3(64.0, 32.0, 64.0)
    body = Body3(
        pos=Vec3(32.0, 16.0, 32.0),
        vel=Vec3(0.5, 0.0, 0.3),
        heading_byte=64,
        zone_id=0,
    )
    fuel = ResourceReservoir(value=100.0, capacity=100.0)
    heat = ResourceReservoir(value=5.0, capacity=100.0, leak=0.02, critical=90.0)
    pressure = ResourceReservoir(value=25.0, capacity=150.0, critical=120.0)
    shield = ResourceReservoir(value=50.0, capacity=50.0, critical=10.0)
    dt = 0.12

    # Build zone graph with varied gravity/friction
    zones = [
        Zone(id=0, gravity=1.0, friction=0.05, pressure=25.0, neighbors=[1, 3]),
        Zone(id=1, gravity=0.5, friction=0.10, pressure=40.0, neighbors=[0, 2]),
        Zone(id=2, gravity=0.1, friction=0.20, pressure=80.0, neighbors=[1]),
        Zone(id=3, gravity=2.0, friction=0.02, pressure=15.0, neighbors=[0, 4]),
        Zone(id=4, gravity=1.5, friction=0.08, pressure=60.0, neighbors=[3]),
    ]

    # Build cuboids (walls/obstacles)
    cuboids = [
        Cuboid(Vec3(20, 0, 20), Vec3(22, 20, 22)),   # wall column
        Cuboid(Vec3(40, 0, 30), Vec3(42, 18, 50)),   # long wall
        Cuboid(Vec3(10, 0, 40), Vec3(18, 12, 42)),   # low block
        Cuboid(Vec3(50, 0, 10), Vec3(52, 25, 30)),   # tower
    ]

    excess_integral = 0.0
    active_laws = [
        "cuboid_collision", "zone_gravity_friction", "hydraulic_height",
        "graph_pressure_diffusion", "hysteresis_failure",
        "resource_thermodynamics", "playable_reality",
    ]

    for step in range(steps + 1):
        if step % 24 == 0:
            body.rotate_quantized(rng.choice([-12, -6, 6, 12]))

        # Determine current zone by position
        zone_idx = body.zone_id
        if step % 60 == 0:
            zone_idx = (zone_idx + 1) % len(zones)
            body.zone_id = zone_idx
        z = zones[zone_idx]

        # Movement: script-based wandering + occasional thrust
        thrust_active = step % 7 < 3
        if thrust_active:
            rad = body.heading_rad
            body.vel.x += math.cos(rad) * 0.15 * z.time_scale
            body.vel.z += math.sin(rad) * 0.15 * z.time_scale
        fuel.step(dt, sink=0.4 if thrust_active else 0.0)
        heat.step(dt, source=0.2 if thrust_active else 0.0)

        motion_step_3d(body, dt, z.gravity, z.friction, world3)

        # Cuboid collision
        for c in cuboids:
            hit, new_vel = cuboid_collide(body.pos, body.vel, c)
            if hit:
                body.vel = new_vel

        # Pressure diffusion across zones
        graph_pressure_diffusion(zones, {zone_idx: 2.0 if thrust_active else 0.0}, dt)
        pressure.value = z.pressure  # track local zone pressure

        # Shield decay in high-pressure zones
        if z.pressure > 60:
            shield.step(dt, sink=0.5)
        else:
            shield.step(dt, source=0.1)

        # Hysteresis failure
        excess_integral, exploded = hysteresis_failure(
            excess_integral, pressure.value, pressure.critical, dt,
        )
        if exploded:
            body.state = "exploded"

        # Hydraulic height step (Driller concept)
        if body.pos.y < 2.0 and z.id == 3:
            body.vel.y = 3.0  # hydraulic lift

        # Metrics
        n_laws = len(active_laws)
        sd = 7.0  # position(3) + velocity(3) + zone_id + cuboid_hits + pressure
        agency = 0.85 if thrust_active else 0.6
        pr = playable_reality_score(sd, agency, cost=n_laws, ambiguity=0.3)
        mle = minimum_law_efficiency(sd, n_laws)
        cr = compression_ratio((step + 1) * 3, seed_bytes=4, law_bytes=n_laws * 8)
        fals = falsifiability_score(active_laws)
        se = semantic_entropy_metric(0.3, n_laws, agency)
        crit = max(heat.criticality, pressure.criticality, 1.0 - shield.criticality)

        m = Metrics(
            step=step, mode="freescape",
            x=body.pos.x, y=body.pos.y, z=body.pos.z,
            speed=body.vel.length(),
            fuel=fuel.value, heat=heat.value, pressure=pressure.value,
            criticality=crit,
            playable_reality=pr, law_count=n_laws,
            compression_ratio=cr, falsifiability=fals,
            semantic_entropy=se, mle=mle,
            zone_id=z.id,
            heading_byte=body.heading_byte,
        )
        yield m

        if step > 0 and step % 48 == 0:
            print_zone_pressure(zones)


def run_colony(steps: int, seed: int) -> Iterable[Metrics]:
    """Mode 5 — The Colony / 3-Demon hybrid cell grid."""
    rng = random.Random(seed)
    grid_w, grid_h = 24, 24
    grid = colony_generate_grid(grid_w, grid_h, seed)

    cx, cy = grid_w // 2, grid_h // 2
    heading = 64  # start facing north-ish
    fuel = ResourceReservoir(value=100.0, capacity=100.0)
    heat = ResourceReservoir(value=5.0, capacity=100.0, leak=0.01, critical=90.0)
    pressure = ResourceReservoir(value=25.0, capacity=150.0, critical=120.0)
    suit = ResourceReservoir(value=100.0, capacity=100.0, leak=0.005, critical=15.0)
    dt = 0.12
    teleported = False
    steps_since_teleport = 0

    active_laws = [
        "cell_occupancy", "quantized_rotation", "toroidal_wrap",
        "teleport_transform", "bresenham_los", "power_suit_energy",
        "resource_thermodynamics", "playable_reality",
    ]

    for step in range(steps + 1):
        # Scripted input: move every few steps, occasionally rotate
        if step % 6 == 0:
            cx, cy, dh, teleported = colony_move(cx, cy, heading, grid, grid_w, grid_h)
            heading = (heading + dh) % 256
            if teleported:
                steps_since_teleport = 0
                suit.step(dt, sink=5.0)  # teleport costs energy
            steps_since_teleport += 1
        if step % 18 == 0:
            heading = (heading + rng.choice([-16, -8, 8, 16])) % 256

        # Energy station recharge
        cell = grid.get((cx, cy))
        if cell and cell.energy_station:
            suit.step(dt, source=3.0)
        suit.step(dt)  # passive drain

        fuel.step(dt, sink=0.1)
        heat.step(dt, source=0.05)

        # LOS check (looking ahead)
        sector = (heading + 32) % 256 // 64
        dx, dy = [(0, -1), (1, 0), (0, 1), (-1, 0)][sector]
        los_cells = bresenham_los(cx, cy, cx + dx * 8, cy + dy * 8)
        los_blocked = any(
            (lx, ly) in grid and grid[(lx, ly)].furniture for lx, ly in los_cells
        )

        # Compute metrics
        n_laws = len(active_laws)
        sd = 6.0  # cell_pos, heading, LOS, energy, teleport, furniture
        agency = 0.8 if not los_blocked else 0.5
        pr = playable_reality_score(sd, agency, cost=n_laws, ambiguity=0.2)
        mle = minimum_law_efficiency(sd, n_laws)
        cr = compression_ratio(grid_w * grid_h, seed_bytes=4, law_bytes=n_laws * 8)
        fals = falsifiability_score(active_laws)
        se = semantic_entropy_metric(0.2, n_laws, agency)
        crit = max(heat.criticality, 1.0 - suit.criticality)

        m = Metrics(
            step=step, mode="colony",
            x=float(cx), y=float(cy),
            speed=1.0 if step % 6 == 0 else 0.0,
            fuel=fuel.value, heat=heat.value, pressure=pressure.value,
            criticality=crit,
            playable_reality=pr, law_count=n_laws,
            compression_ratio=cr, falsifiability=fals,
            semantic_entropy=se, mle=mle,
            heading_byte=heading,
            cell_pos=f"({cx:2d},{cy:2d})",
        )
        yield m


def run_semantic(steps: int, seed: int) -> Iterable[Metrics]:
    """Mode 6 — RGPUF analytics: compare all modes' metrics side-by-side."""
    rng = random.Random(seed)

    # Run a short burst of each mode to collect metrics
    mode_names = ["lander", "asteroids", "pressure", "freescape", "colony"]
    generators = {
        "lander": run_lander, "asteroids": run_asteroids,
        "pressure": run_pressure, "freescape": run_freescape,
        "colony": run_colony,
    }
    # Collect final metrics from each mode
    finals: dict[str, Metrics] = {}
    for name in mode_names:
        last_m = None
        for m in generators[name](steps, seed):
            last_m = m
        if last_m:
            finals[name] = last_m

    active_laws = [
        "playable_reality", "minimum_law_efficiency", "compression_ratio",
        "falsifiability_score", "semantic_entropy",
    ]
    n_laws = len(active_laws)

    for step in range(steps + 1):
        # Aggregate metrics across all modes
        if not finals:
            yield Metrics(step=step, mode="semantic", law_count=n_laws)
            continue

        avg_pr = sum(m.playable_reality for m in finals.values()) / len(finals)
        avg_mle = sum(m.mle for m in finals.values()) / len(finals)
        avg_fals = sum(m.falsifiability for m in finals.values()) / len(finals)
        avg_se = sum(m.semantic_entropy for m in finals.values()) / len(finals)
        avg_cr = sum(m.compression_ratio for m in finals.values()) / len(finals)
        avg_crit = sum(m.criticality for m in finals.values()) / len(finals)
        avg_laws = sum(m.law_count for m in finals.values()) / len(finals)

        sd = 8.0  # five modes * multiple metrics
        agency = avg_pr / max(avg_se, 0.01)
        ambiguity = avg_se / max(avg_pr, 0.01)

        pr = playable_reality_score(sd, agency, cost=n_laws, ambiguity=min(ambiguity, 2.0))

        m = Metrics(
            step=step, mode="semantic",
            x=avg_pr, y=avg_mle, z=avg_fals,
            speed=avg_cr,
            fuel=100.0, heat=avg_crit * 50.0, pressure=avg_se * 30.0,
            criticality=avg_crit,
            playable_reality=pr, law_count=n_laws,
            compression_ratio=avg_cr, falsifiability=avg_fals,
            semantic_entropy=avg_se, mle=avg_mle,
        )
        yield m


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Output / Export (Section 14)
# ═══════════════════════════════════════════════════════════════════════════════

CSV_HEADER = [
    "step", "mode", "x", "y", "z", "speed", "fuel", "heat", "pressure",
    "criticality", "playable_reality", "law_count", "compression_ratio",
    "falsifiability", "semantic_entropy",
]


def write_csv(metrics_list: list[Metrics], path: str) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADER)
        w.writeheader()
        for m in metrics_list:
            w.writerow(m.csv_row())
    print(f"\n[CSV] wrote {len(metrics_list)} rows -> {path}")


def write_json_summary(results: dict[str, Metrics], path: str, seed: int, steps: int) -> None:
    summary: dict[str, Any] = {"seed": seed, "steps": steps, "modes": {}}
    for name, m in results.items():
        summary["modes"][name] = {
            "final_state": {
                "criticality": round(m.criticality, 4),
                "playable_reality": round(m.playable_reality, 4),
                "mle": round(m.mle, 4),
                "falsifiability": round(m.falsifiability, 4),
                "compression_ratio": round(m.compression_ratio, 4),
                "semantic_entropy": round(m.semantic_entropy, 4),
                "law_count": m.law_count,
            },
            "active_laws": {
                lt.name: lt.verified for lt in LAW_REGISTRY.values() if lt.active
            },
        }
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[JSON] wrote summary -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Simulation Runners
# ═══════════════════════════════════════════════════════════════════════════════

MODE_RUNNERS: dict[str, Any] = {
    "lander": run_lander,
    "asteroids": run_asteroids,
    "pressure": run_pressure,
    "freescape": run_freescape,
    "colony": run_colony,
    "semantic": run_semantic,
}

ALL_MODES: list[str] = ["lander", "asteroids", "pressure", "freescape", "colony", "semantic"]


def run_mode(mode: str, steps: int, seed: int, csv_path: str | None = None, json_path: str | None = None) -> Metrics | None:
    """Run a single mode and optionally export."""
    print(f"\n--- {mode.upper()} ---")
    gen = MODE_RUNNERS[mode](steps, seed)
    last: Metrics | None = None
    all_m: list[Metrics] = []
    for m in gen:
        last = m
        all_m.append(m)
        print_frame(m)

    if last is None:
        return None

    print(f"\n  Final: PR={last.playable_reality:.3f} MLE={last.mle:.2f} "
          f"fals={last.falsifiability:.2f} crit={last.criticality:.3f} "
          f"laws={last.law_count}")

    if csv_path:
        write_csv(all_m, csv_path)
    if json_path:
        write_json_summary({mode: last}, json_path, seed, steps)
    return last


def run_all(steps: int, seed: int, csv_path: str | None = None, json_path: str | None = None) -> dict[str, Metrics]:
    """Run all modes and produce comparison table."""
    results: dict[str, Metrics] = {}
    all_metrics: list[Metrics] = []

    for mode in ALL_MODES:
        gen = MODE_RUNNERS[mode](steps, seed)
        last: Metrics | None = None
        for m in gen:
            last = m
            all_metrics.append(m)
            print_frame(m)
        if last:
            results[mode] = last

    # Comparison table
    print("\n" + "=" * 80)
    print("  MODE COMPARISON TABLE")
    print("=" * 80)
    header = f"  {'Mode':<11} {'PR':>7} {'MLE':>6} {'Fals':>6} {'Crit':>6} {'Laws':>5} {'CR':>8} {'SE':>6}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for mode in ALL_MODES:
        m = results.get(mode)
        if m:
            print(f"  {mode:<11} {m.playable_reality:7.3f} {m.mle:6.2f} "
                  f"{m.falsifiability:6.2f} {m.criticality:6.3f} "
                  f"{m.law_count:5d} {m.compression_ratio:8.2f} {m.semantic_entropy:6.2f}")
    print("=" * 80)

    if csv_path:
        write_csv(all_metrics, csv_path)
    if json_path:
        write_json_summary(results, json_path, seed, steps)

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 15. Law Trace Display
# ═══════════════════════════════════════════════════════════════════════════════

def print_law_trace() -> None:
    """Print full law registry with verification tags."""
    print("\nLAW REGISTRY (falsification tags):")
    print("-" * 62)
    print(f"  {'Law Name':<32} {'Cost':>5} {'Verified':<12} {'Weight'}")
    print("-" * 62)
    for name, lt in LAW_REGISTRY.items():
        w = VERIFIED_WEIGHT.get(lt.verified, 0.0)
        marker = " *" if lt.active else " -"
        print(f"  {name:<32} {lt.cost:5.1f} {lt.verified:<12} {w:.1f}{marker}")
    print("-" * 62)
    total = len(LAW_REGISTRY)
    active = sum(1 for lt in LAW_REGISTRY.values() if lt.active)
    hist = sum(1 for lt in LAW_REGISTRY.values() if lt.verified == "historical" and lt.active)
    equiv = sum(1 for lt in LAW_REGISTRY.values() if lt.verified == "equivalent" and lt.active)
    spec = sum(1 for lt in LAW_REGISTRY.values() if lt.verified == "speculative" and lt.active)
    print(f"  Total: {total}  Active: {active}  "
          f"Historical: {hist}  Equivalent: {equiv}  Speculative: {spec}")
    print("  * = active in at least one mode")


# ═══════════════════════════════════════════════════════════════════════════════
# 16. CLI Main (Section 9)
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="RGPUF Lab v2 -- Minimum-Law Retro Physics Lab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Modes:
  lander    Tennis for Two -> Lunar Lander -> Moonlander -> MSFS
  asteroids Spacewar! -> Computer Space -> Asteroids -> Elite
  pressure  Driller pressure + MW2 heat + resource thermodynamics
  freescape Driller / Freescape cuboid spatial logic + zone laws
  colony    The Colony / 3-Demon cell grid + teleport + LOS
  semantic  RGPUF analytics: compare all modes scientifically

Examples:
  python rgpuf_lab.py --mode asteroids --steps 240 --seed 42
  python rgpuf_lab.py --mode freescape --steps 360 --seed 7
  python rgpuf_lab.py --all --steps 240 --seed 42
  python rgpuf_lab.py --all --csv telemetry.csv --json summary.json
""",
    )
    parser.add_argument("--mode", choices=ALL_MODES, default=None,
                        help="Simulation mode (default: run --all)")
    parser.add_argument("--steps", type=int, default=240, help="Simulation steps (default: 240)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")
    parser.add_argument("--csv", type=str, default=None, help="Output CSV path")
    parser.add_argument("--json", type=str, default=None, help="Output JSON summary path")
    parser.add_argument("--trace-laws", action="store_true", help="Print full law registry")
    parser.add_argument("--all", action="store_true", help="Run all modes and show comparison")
    args = parser.parse_args()

    print("RGPUF Lab v2 -- Minimum-Law Retro Physics Lab")
    print("Retro Game Physics Unified Framework")
    print("law stack: motion + resources + topology + spatial + cell + semantic")
    print("-" * 80)

    if args.trace_laws:
        print_law_trace()

    if args.all or args.mode is None:
        run_all(args.steps, args.seed, csv_path=args.csv, json_path=args.json)
    else:
        run_mode(args.mode, args.steps, args.seed, csv_path=args.csv, json_path=args.json)

    # Final thesis statement
    print()
    print("RGPUF thesis: Retro physics is not a pile of old tricks;")
    print("it is a compressed law language where motion, resources, topology,")
    print("collision, pressure, and agency can all be expressed as tiny")
    print("executable primitives.")


if __name__ == "__main__":
    main()
