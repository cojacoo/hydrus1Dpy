"""
Numerical Methods for HYDRUS1D Phase 3
======================================

Numerical algorithms for solving Richards equation.
"""

from .linear_solver import solve_tridiagonal
from .time_stepping import AdaptiveTimeStepper

__all__ = ['solve_tridiagonal', 'AdaptiveTimeStepper']
