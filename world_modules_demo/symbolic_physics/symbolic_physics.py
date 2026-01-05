# SYMBOLIC PHYSICS MODULE (Upgraded + Integrated Version)
# -------------------------------------------------------
# Provides:
#   ✔ Symbolic fields (archetypes, mythic pressure, recursion weights)
#   ✔ Symbolic density + resonance
#   ✔ Flux vector (directional metaphysical pressure)
#   ✔ Metamorphic rules
#   ✔ Recursive temporal anchor (time crystal integration)
#   ✔ Harmonized symbolic-physics → world-physics bridge
#   ✔ Deterministic + chaotic modes

import math
import random

# ======================================================================
# Symbolic Field
# ======================================================================

class SymbolicField:
    """
    Represents a symbolic parameter in the world:
        - archetypal charge
        - recursion weight
        - mythic harmonic pressure
        - symbolic instability
    """

    def __init__(self, name, value=0.0, volatility=0.1):
        self.name = name
        self.value = float(value)
        self.volatility = float(volatility)

    def fluctuate(self):
        """Small stochastic drift used for dream or slip-like behavior."""
        delta = (random.random() - 0.5) * self.volatility
        self.value += delta
        return self.value

    def __repr__(self):
        return f"<SymbolicField {self.name}: {self.value:.3f}>"


# ======================================================================
# Symbolic Density
# ======================================================================

class SymbolicDensity:
    """
    Controls how strongly symbolic physics influences world physics.
    """

    def __init__(self, density=1.0, resonance=1.0):
        self.density = float(density)
        self.resonance = float(resonance)

    @property
    def effective_weight(self):
        """Density × (1 + resonance)."""
        return self.density * (1.0 + self.resonance)

    def elevate(self, amount):
        self.density = max(0.0, self.density + amount)

    def tune_resonance(self, factor):
        self.resonance *= factor

    def __repr__(self):
        return f"<SymbolicDensity d={self.density:.3f} r={self.resonance:.3f}>"


# ======================================================================
# Flux Vector
# ======================================================================

class FluxVector:
    """
    A metaphysical directional force driving transformation.
    """

    def __init__(self, magnitude=0.0, direction=1.0):
        self.magnitude = float(magnitude)
        self.direction = float(direction)

    @property
    def output(self):
        return self.magnitude * self.direction

    def invert(self):
        self.direction *= -1

    def amplify(self, factor):
        self.magnitude *= factor

    def __repr__(self):
        return f"<FluxVector mag={self.magnitude:.3f} dir={self.direction:+.1f}>"


# ======================================================================
# Metamorphic Rules
# ======================================================================

class MetamorphRules:
    """
    Defines how symbolic density + flux modify world values.
    """

    @staticmethod
    def transform(value, density: SymbolicDensity, flux: FluxVector):
        """
        Base symbolic → numeric transformation.
        """

        # Fundamental symbolic displacement
        out = value + flux.output * density.effective_weight * 0.05

        # Resonant echo (symbolic harmonic impact)
        if density.resonance > 1.5:
            out += math.sin(out * density.resonance) * 0.1

        return out


# ======================================================================
# Temporal Anchor (integrates Time Crystal -> Symbolic Physics)
# ======================================================================

class RecursiveTemporalAnchor:
    """
    Receives input from the world tick and produces temporal resonance.
    Supports symbolic ≈ temporal coupling.
    """

    def __init__(self, time_anchor_strength=1.0, phase_offset=0.0):
        self.time_anchor_strength = float(time_anchor_strength)
        self.phase_offset = float(phase_offset)
        self.temporal_phase = 0.0

    def update(self, world_tick):
        """Primary temporal resonance formula."""
        self.temporal_phase = math.sin(world_tick * self.time_anchor_strength + self.phase_offset)

    def apply(self, value):
        """Amplifies or dampens the value depending on temporal_phase."""
        return value * (1.0 + 0.25 * self.temporal_phase)

    def __repr__(self):
        return f"<TemporalAnchor strength={self.time_anchor_strength} phase={self.temporal_phase:.3f}>"


# ======================================================================
# Main Interface
# ======================================================================

def apply_symbolic_physics(
    world_value: float,
    density: SymbolicDensity,
    flux: FluxVector,
    time_anchor: RecursiveTemporalAnchor = None,
    world_tick: int = 0,
    pulse: float = None
):
    """
    Applies the complete metaphysical transformation pipeline:
        1. metamorphic transformation (density × flux)
        2. optional temporal modulation (recursive anchor)
        3. optional time-crystal modulation (pulse)
    """

    # 1. Base metamorphic rule
    new_val = MetamorphRules.transform(world_value, density, flux)

    # 2. Temporal anchor modulation
    if time_anchor is not None:
        time_anchor.update(world_tick)
        new_val = time_anchor.apply(new_val)

    # 3. Optional direct time-crystal pulse coupling
    #     (pulse provided by world_clock)
    if pulse is not None:
        new_val = new_val * (1.0 + 0.1 * pulse)

    return new_val
