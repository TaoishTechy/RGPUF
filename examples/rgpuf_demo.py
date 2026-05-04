#!/usr/bin/env python3
"""
RGPUF Demo — Minimum-Law Retro Physics Simulator
================================================

A small, dependency-free Python demo for the Retro Game Physics Unified
Framework (RGPUF). It shows how many retro-game physics ideas can be expressed
as tiny executable laws:

- 1960s: ballistic motion, gravity wells, resource depletion
- 1970s: thrust/gravity/collision arcade kernel
- 1980s: quantized rotation, topology wrapping, procedural compression
- RGPUF: heat/pressure/resource thermodynamics + playable-reality metric

Run:
    python examples/rgpuf_demo.py

Optional:
    python examples/rgpuf_demo.py --mode lander
    python examples/rgpuf_demo.py --mode asteroids
    python examples/rgpuf_demo.py --mode pressure
    python examples/rgpuf_demo.py --steps 240 --seed 7
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass, field
from typing import Callable, Iterable, Literal

Mode = Literal["lander", "asteroids", "pressure"]


# -----------------------------------------------------------------------------
# Core math primitives
# -----------------------------------------------------------------------------

@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> "Vec2":
        mag = self.length()
        if mag <= 1e-9:
            return Vec2()
        return Vec2(self.x / mag, self.y / mag)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def wrap(value: float, size: float) -> float:
    """Toroidal boundary condition: Asteroids / 3-Demon / Elite-style wrap."""
    return value % size


# -----------------------------------------------------------------------------
# RGPUF laws: compact executable physics kernels
# -----------------------------------------------------------------------------

@dataclass
class Body:
    pos: Vec2
    vel: Vec2 = field(default_factory=Vec2)
    mass: float = 1.0
    radius: float = 1.0
    heading_byte: int = 64  # 256-step pseudo-angle; 64 = up-ish in this demo.

    @property
    def heading_rad(self) -> float:
        return (self.heading_byte / 256.0) * math.tau

    @property
    def forward(self) -> Vec2:
        a = self.heading_rad
        return Vec2(math.cos(a), math.sin(a))

    def rotate_quantized(self, ticks: int) -> None:
        """The Colony / Elite-style byte-sized angular state."""
        self.heading_byte = (self.heading_byte + ticks) % 256


@dataclass
class ResourceReservoir:
    """
    Universal RGPUF resource law:

        dR/dt = source(t) - sink(t) - leak*R + noise

    Interpretable as fuel, heat, pressure, grain, shield, oxygen, etc.
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


def arcade_motion_step(
    body: Body,
    dt: float,
    thrust: float,
    gravity: Vec2,
    drag: float,
    world_size: Vec2,
    wrap_edges: bool,
) -> None:
    """Unified arcade motion: thrust + gravity - drag + optional toroidal topology."""
    force = body.forward * thrust + gravity * body.mass - body.vel * drag
    acc = force * (1.0 / body.mass)
    body.vel = body.vel + acc * dt
    body.pos = body.pos + body.vel * dt

    if wrap_edges:
        body.pos.x = wrap(body.pos.x, world_size.x)
        body.pos.y = wrap(body.pos.y, world_size.y)
    else:
        # Ground / wall collision with restitution: Pong/Lander boundary law.
        if body.pos.x < 0 or body.pos.x > world_size.x:
            body.vel.x *= -0.85
            body.pos.x = clamp(body.pos.x, 0, world_size.x)
        if body.pos.y < 0:
            body.vel.y *= -0.30
            body.pos.y = 0
        if body.pos.y > world_size.y:
            body.vel.y *= -0.85
            body.pos.y = world_size.y


def central_gravity_well(body: Body, attractor: Vec2, gm: float, softening: float = 25.0) -> Vec2:
    """Spacewar!-style central force with softening to avoid singularity."""
    delta = attractor - body.pos
    r2 = delta.x * delta.x + delta.y * delta.y + softening
    return delta.normalized() * (gm / r2)


def procedural_starfield(seed: int, count: int, world_size: Vec2) -> list[Vec2]:
    """Tiny deterministic universe: law + seed > stored map."""
    rng = random.Random(seed)
    return [Vec2(rng.random() * world_size.x, rng.random() * world_size.y) for _ in range(count)]


# -----------------------------------------------------------------------------
# Telemetry and display
# -----------------------------------------------------------------------------

@dataclass
class Metrics:
    step: int
    mode: str
    x: float
    y: float
    speed: float
    fuel: float
    heat: float
    pressure: float
    criticality: float
    playable_reality: float


def playable_reality_metric(state_density: float, agency: float, cost: float, ambiguity: float) -> float:
    """
    Compact RGPUF-style score:

        PR = (state_density * agency) / (cost * (1 + ambiguity))

    Higher means more perceived world per unit executable burden.
    """
    return (state_density * agency) / max(cost * (1.0 + ambiguity), 1e-9)


def sparkline(value: float, width: int = 18, maximum: float = 1.0) -> str:
    value = clamp(value / max(maximum, 1e-9), 0.0, 1.0)
    filled = int(round(value * width))
    return "█" * filled + "░" * (width - filled)


def print_frame(m: Metrics) -> None:
    if m.step % 12 != 0:
        return
    print(
        f"t={m.step:03d} mode={m.mode:<9} "
        f"pos=({m.x:6.1f},{m.y:6.1f}) speed={m.speed:6.2f} "
        f"fuel={m.fuel:6.1f} heat={m.heat:6.1f} pressure={m.pressure:6.1f} "
        f"crit={sparkline(m.criticality, maximum=1.25)} "
        f"PR={m.playable_reality:7.3f}"
    )


# -----------------------------------------------------------------------------
# Demo modes
# -----------------------------------------------------------------------------

def run(mode: Mode, steps: int, seed: int) -> Iterable[Metrics]:
    rng = random.Random(seed)
    world = Vec2(160.0, 90.0)
    stars = procedural_starfield(seed, count=64, world_size=world)

    ship = Body(pos=Vec2(world.x * 0.5, world.y * 0.75), vel=Vec2(5.0, 0.0), mass=1.0, radius=1.0)
    fuel = ResourceReservoir(value=100.0, capacity=100.0, leak=0.0)
    heat = ResourceReservoir(value=5.0, capacity=100.0, leak=0.035, critical=90.0)
    pressure = ResourceReservoir(value=25.0, capacity=150.0, leak=0.0, critical=120.0)

    dt = 0.12
    attractor = Vec2(world.x * 0.5, world.y * 0.5)

    for step in range(steps + 1):
        # A deterministic input script: repeatable, minimal, demo-friendly.
        if step % 32 == 0:
            ship.rotate_quantized(rng.choice([-8, -4, 4, 8]))

        thrust = 0.0
        gravity = Vec2()
        drag = 0.0
        wrap_edges = False
        ambiguity = 0.15

        if mode == "lander":
            gravity = Vec2(0.0, -1.62)
            thrust = 3.8 if fuel.value > 0 and step % 9 in (0, 1, 2, 3) else 0.0
            drag = 0.01
            wrap_edges = False
            fuel.step(dt, sink=0.9 if thrust else 0.0)
            heat.step(dt, source=0.35 if thrust else 0.0)
            pressure.step(dt, source=0.0)
            state_density = 3.0  # position, velocity, fuel/landing state
            agency = 0.8
            cost = 1.0

        elif mode == "asteroids":
            gravity = central_gravity_well(ship, attractor, gm=85.0)
            thrust = 2.2 if step % 11 < 4 else 0.0
            drag = 0.0
            wrap_edges = True
            fuel.step(dt, sink=0.35 if thrust else 0.0)
            heat.step(dt, source=0.25 if thrust else 0.0, noise=rng.uniform(-0.02, 0.02))
            pressure.step(dt, source=0.0)
            state_density = 4.5  # orbit, wrap, heading, thrust
            agency = 0.9
            cost = 1.2
            ambiguity = 0.25

        elif mode == "pressure":
            gravity = Vec2(0.0, -0.4)
            thrust = 1.2 if fuel.value > 0 and step % 13 < 5 else 0.0
            drag = 0.08
            wrap_edges = False
            drilling = 8.0 if step in range(70, 95) or step in range(155, 180) else 0.0
            pressure.step(dt, source=1.15, sink=drilling, noise=rng.uniform(-0.1, 0.1))
            heat.step(dt, source=0.15 if thrust else 0.0)
            fuel.step(dt, sink=0.25 if thrust else 0.0)
            state_density = 5.0  # movement + pressure puzzle + timing windows
            agency = 0.75 if drilling else 0.55
            cost = 1.1
            ambiguity = 0.35

        arcade_motion_step(ship, dt, thrust, gravity, drag, world, wrap_edges)

        # Estimate executable cost as number of active law terms.
        active_terms = 1 + int(thrust > 0) + int(gravity.length() > 0) + int(drag > 0) + int(wrap_edges)
        pr = playable_reality_metric(state_density, agency, cost=active_terms, ambiguity=ambiguity)

        yield Metrics(
            step=step,
            mode=mode,
            x=ship.pos.x,
            y=ship.pos.y,
            speed=ship.vel.length(),
            fuel=fuel.value,
            heat=heat.value,
            pressure=pressure.value,
            criticality=max(heat.criticality, pressure.criticality),
            playable_reality=pr,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="RGPUF minimum-law retro physics demo")
    parser.add_argument("--mode", choices=["lander", "asteroids", "pressure"], default="asteroids")
    parser.add_argument("--steps", type=int, default=240)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("RGPUF Demo — Minimum-Law Retro Physics Simulator")
    print("law stack: thrust + gravity + drag/collision + resource thermodynamics + topology")
    print("-" * 116)

    last: Metrics | None = None
    for metrics in run(args.mode, args.steps, args.seed):
        last = metrics
        print_frame(metrics)

    if last is None:
        return

    print("-" * 116)
    print("Final diagnosis:")
    if last.criticality >= 1.0:
        print("  CRITICAL: thermal/pressure threshold crossed — retro resource law becomes failure state.")
    elif last.fuel <= 1.0:
        print("  DEPLETED: fuel reservoir exhausted — agency collapses into drift.")
    else:
        print("  STABLE: compact laws produced playable state without crossing failure thresholds.")
    print(f"  Final playable-reality score: {last.playable_reality:.3f}")


if __name__ == "__main__":
    main()
