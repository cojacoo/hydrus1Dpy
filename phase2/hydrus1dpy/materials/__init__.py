"""
Soil Hydraulic Material Models
================================

Exchangeable soil hydraulic models for HYDRUS1D.

All models implement the HydraulicModel abstract base class and provide:
- Water retention curve: θ(h)
- Hydraulic conductivity function: K(h)
- Water capacity: C(h) = dθ/dh
- Inverse functions where analytical solutions exist

Available Models:
-----------------
- VanGenuchten: van Genuchten (1980) + Mualem (1976)
- ModifiedVanGenuchten: Vogel & Cislerova modification
- BrooksCorey: Brooks & Corey (1964) + Burdine or Mualem
- DualPorosity: Durner (1994) bimodal model
- LogNormal: Kosugi (1996) log-normal distribution
- CustomHydraulicModel: User-defined functions

References:
-----------
1. van Genuchten, M. Th. (1980). A closed-form equation for predicting
   the hydraulic conductivity of unsaturated soils. SSSA J. 44(5):892-898.

2. Mualem, Y. (1976). A new model for predicting the hydraulic conductivity
   of unsaturated porous media. Water Resour. Res. 12(3):513-522.

3. Brooks, R. H., & Corey, A. T. (1964). Hydraulic properties of porous media.
   Hydrology Papers, Colorado State University.

4. Durner, W. (1994). Hydraulic conductivity estimation for soils with
   heterogeneous pore structure. Water Resour. Res. 30(2):211-223.

5. Kosugi, K. (1996). Lognormal distribution model for unsaturated soil
   hydraulic properties. Water Resour. Res. 32(9):2697-2703.
"""

from .base import HydraulicModel
from .van_genuchten import VanGenuchten, ModifiedVanGenuchten
from .brooks_corey import BrooksCorey
from .dual_porosity import DualPorosity
from .log_normal import LogNormal
from .custom import CustomHydraulicModel

__all__ = [
    'HydraulicModel',
    'VanGenuchten',
    'ModifiedVanGenuchten',
    'BrooksCorey',
    'DualPorosity',
    'LogNormal',
    'CustomHydraulicModel',
]

__version__ = '0.2.0-phase2'
