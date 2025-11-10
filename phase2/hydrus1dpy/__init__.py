"""
HYDRUS1D Python Wrapper - Phase 2
==================================

Exchangeable soil hydraulic models.
"""

from .materials import (
    HydraulicModel,
    VanGenuchten,
    ModifiedVanGenuchten,
    BrooksCorey,
    DualPorosity,
    LogNormal,
    CustomHydraulicModel,
)

__version__ = "0.2.0-phase2"

__all__ = [
    'HydraulicModel',
    'VanGenuchten',
    'ModifiedVanGenuchten',
    'BrooksCorey',
    'DualPorosity',
    'LogNormal',
    'CustomHydraulicModel',
]
