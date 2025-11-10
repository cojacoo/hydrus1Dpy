"""
HYDRUS1D Python Solver - Phase 3
==================================

Pure Python/Numba implementation of Richards equation solver.

Components:
- Richards equation solver (mixed form)
- Picard iteration for nonlinearity
- Adaptive time stepping
- Mass-conservative numerical scheme
- Numba JIT optimization
- Full integration with Phase 1 (I/O) and Phase 2 (materials)

Author: HYDRUS1DPy Development Team
Version: 0.3.0-phase3
"""

# Import Phase 2 materials and inject into this package's namespace
import sys
from pathlib import Path
_phase2_path = str(Path(__file__).parent.parent.parent / 'phase2')
if _phase2_path not in sys.path:
    sys.path.insert(0, _phase2_path)

# Import Phase 2's materials module and make it available as hydrus1dpy.materials
import importlib.util
_materials_spec = importlib.util.spec_from_file_location(
    "hydrus1dpy.materials",
    str(Path(_phase2_path) / "hydrus1dpy" / "materials" / "__init__.py")
)
materials = importlib.util.module_from_spec(_materials_spec)
sys.modules["hydrus1dpy.materials"] = materials
_materials_spec.loader.exec_module(materials)

from .core.richards_solver import RichardsSolver1D
from .core.model import HydrusModel
from .numerics.time_stepping import AdaptiveTimeStepper
from .processes.boundary_conditions import (
    ConstantHeadBC, ConstantFluxBC, AtmosphericBC, FreeDrainageBC
)

__version__ = "0.3.0-phase3"

__all__ = [
    'RichardsSolver1D',
    'HydrusModel',
    'AdaptiveTimeStepper',
    'ConstantHeadBC',
    'ConstantFluxBC',
    'AtmosphericBC',
    'FreeDrainageBC',
]
