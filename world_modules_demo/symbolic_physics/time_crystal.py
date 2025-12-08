# TIME CRYSTAL MODULE (Upgraded Integrated Version)
# -----------------------------------------------------
# Supports:
# - Stable, Unstable, Fractal, and Harmonic Time Crystals
# - Universal .update() and .apply() signatures
# - Deterministic or noisy oscillation
# - Temporal phase output for world_clock + symbolic physics
# - Ready for world_delta, world_expansion_engine, zone_engine
# - Safe fallback behavior

import math
import random

# -----------------------------------------------------
# Base Class
# -----------------------------------------------------

class TimeCrystalBase:
    """
    Abstract temporal-stability object.
    Converts world ticks into cyclic phases,
    producing distortions applied to world values.
    """

    def __init__(self, frequency=1.0, amplitude=1.0, stability=1.0):
        self.frequency = float(frequency)
        self.amplitude = float(amplitude)
        self.stability = float(stability)
        self.phase = 0.0                # current oscillation phase
        self.raw_phase = 0.0            # pre-processed phase value

    # --------------------------------------------------
    # Phase Update
    # --------------------------------------------------
    def update(self, world_tick: int):
        """Basic harmonic update. Override for complex crystals."""
        raw = math.sin(world_tick * self.frequency)
        self.raw_phase = raw
        self.phase = raw * self.stability

    # --------------------------------------------------
    # Value Transformation
    # --------------------------------------------------
    def apply(self, value: float, *_, **__) -> float:
        """
        Applies crystal distortion to a value.
        Subclasses may add symbolic parameters.
        """
        return value * (1.0 + self.phase * self.amplitude)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    @property
    def pulse(self) -> float:
        """Public pulse output used by world_clock."""
        return float(self.phase)

    def __repr__(self):
        return (
            f"<TimeCrystal freq={self.frequency} "
            f"amp={self.amplitude} stab={self.stability}>"
        )


# -----------------------------------------------------
# Type A — Stable Time Crystal
# -----------------------------------------------------

class StableTimeCrystal(TimeCrystalBase):
    """Predictable, low-noise oscillation."""

    def update(self, world_tick: int):
        base = math.sin(world_tick * self.frequency)
        self.raw_phase = base
        self.phase = base * self.stability

    def apply(self, value: float, *_):
        return value * (1.0 + 0.15 * self.phase)


# -----------------------------------------------------
# Type B — Unstable Time Crystal
# -----------------------------------------------------

class UnstableTimeCrystal(TimeCrystalBase):
    """
    Chaotic fluctuations: Used for Slipwave distortions,
    memory drift, recursion anomalies.
    """

    def update(self, world_tick: int):
        harmonic = math.sin(world_tick * self.frequency)
        noise = (random.random() - 0.5) * (1.0 - self.stability)
        self.raw_phase = harmonic + noise
        self.phase = self.raw_phase

    def apply(self, value: float, *_):
        distortion = 1.0 + self.phase * self.amplitude
        return value * distortion


# -----------------------------------------------------
# Type C — Harmonic Time Crystal
# -----------------------------------------------------

class HarmonicTimeCrystal(TimeCrystalBase):
    """
    Couples crystal oscillation with symbolic resonance.
    """

    def apply(self, value: float, resonance: float = 1.0, *_):
        multiplier = 1.0 + self.phase * self.amplitude * resonance
        return value * multiplier


# -----------------------------------------------------
# Type D — Fractal Time Crystal
# -----------------------------------------------------

class FractalTimeCrystal(TimeCrystalBase):
    """
    Recursive time echo. Used for:
    - Slips
    - Ghost ticks
    - Nonlinear temporal recursion
    """

    def update(self, world_tick: int):
        base = math.sin(world_tick * self.frequency)
        # fractal echo layer
        echo = math.sin(base * math.pi)
        self.raw_phase = base
        self.phase = (base + echo) * 0.5

    def apply(self, value: float, *_):
        return value * (1.0 + 0.25 * self.phase + 0.1 * math.sin(value))


# -----------------------------------------------------
# Factory Utility
# -----------------------------------------------------

def get_time_crystal(kind: str = "stable") -> TimeCrystalBase:
    """
    Factory for all time-crystal types.
    """

    if not isinstance(kind, str):
        raise ValueError("Crystal type must be a string.")

    k = kind.lower().strip()

    if k == "stable":
        return StableTimeCrystal(frequency=1.0, amplitude=0.8, stability=1.0)

    if k == "unstable":
        return UnstableTimeCrystal(frequency=1.2, amplitude=1.3, stability=0.4)

    if k == "harmonic":
        return HarmonicTimeCrystal(frequency=0.7, amplitude=0.6, stability=0.9)

    if k == "fractal":
        return FractalTimeCrystal(frequency=0.9, amplitude=1.2, stability=0.7)

    raise ValueError(f"Unknown time crystal type: {kind}")
