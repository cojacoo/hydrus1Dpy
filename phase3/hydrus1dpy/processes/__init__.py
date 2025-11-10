"""
Physical Processes for HYDRUS1D Phase 3
========================================

Boundary conditions, root water uptake, and other physical processes.
"""

from .boundary_conditions import (
    BoundaryCondition,
    ConstantHeadBC,
    ConstantFluxBC,
    FreeDrainageBC,
    AtmosphericBC
)

__all__ = [
    'BoundaryCondition',
    'ConstantHeadBC',
    'ConstantFluxBC',
    'FreeDrainageBC',
    'AtmosphericBC'
]
