"""
Core Components for HYDRUS1D Phase 3
=====================================

Richards equation solver and related components.
"""

from .richards_solver import RichardsSolver1D, SolverParameters
from .model import HydrusModel

__all__ = ['RichardsSolver1D', 'SolverParameters', 'HydrusModel']
