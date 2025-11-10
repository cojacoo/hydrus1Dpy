"""
HYDRUS1D Python Wrapper - Phase 1
==================================

Python interface for HYDRUS1D Fortran hydrological model.

This package provides:
- Input file parsing and generation
- Output file parsing
- Fortran model execution
- Results visualization with Plotly

Author: HYDRUS1DPy Development Team
License: MIT
Version: 0.1.0 (Phase 1)
"""

__version__ = "0.1.0-phase1"
__author__ = "HYDRUS1DPy Development Team"

from .io.data_structures import (
    ModelDomain,
    TimeControl,
    ModelResults,
    BoundaryCondition,
    MaterialProperties
)
from .io.input_parser import InputParser
from .io.output_parser import OutputParser
from .visualization.plots import HydrusVisualizer

__all__ = [
    'ModelDomain',
    'TimeControl',
    'ModelResults',
    'BoundaryCondition',
    'MaterialProperties',
    'InputParser',
    'OutputParser',
    'HydrusVisualizer',
]
