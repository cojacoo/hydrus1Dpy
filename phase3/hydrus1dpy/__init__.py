"""
HYDRUS1DPy - Comprehensive Python Package for HYDRUS1D
=======================================================

A scientifically rigorous Python implementation of the HYDRUS1D hydrological model
for simulating one-dimensional variably saturated water flow in soils.

Main Components:
---------------
- **materials**: Soil hydraulic models (van Genuchten, Brooks-Corey, etc.)
- **io**: Input/output handling for HYDRUS1D files
- **core**: Richards equation solver with Picard iteration
- **processes**: Boundary conditions and root water uptake
- **numerics**: Numerical solvers and time stepping
- **visualization**: Interactive Plotly visualizations
- **utils**: Helper functions and configuration builders

Quick Start:
-----------
>>> from hydrus1dpy import HydrusModel
>>> from hydrus1dpy.materials import VanGenuchten
>>>
>>> # Create soil model
>>> soil = VanGenuchten(theta_r=0.078, theta_s=0.430, alpha=0.036, n=1.56, Ks=24.96)
>>>
>>> # Create and run simulation
>>> model = HydrusModel(depth=100.0, n_nodes=51, material=soil)
>>> model.set_top_bc('flux', flux=0.5)
>>> model.set_bottom_bc('free_drainage')
>>> results = model.run(t_end=10.0, dt_init=0.01)

Author: HYDRUS1DPy Development Team
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"

# Core solver and model
from .core.richards_solver import RichardsSolver1D
from .core.model import HydrusModel

# Numerical components
from .numerics.time_stepping import AdaptiveTimeStepper
from .numerics.linear_solver import solve_tridiagonal

# Boundary conditions
from .processes.boundary_conditions import (
    BoundaryCondition,
    ConstantHeadBC,
    ConstantFluxBC,
    AtmosphericBC,
    FreeDrainageBC,
    EnhancedAtmosphericBC
)

# Evapotranspiration
from .processes.evapotranspiration import (
    WeatherData,
    PenmanMonteith,
    SimpleET,
    ETCalculator,
    pf_to_head,
    head_to_pf
)

# Materials (soil hydraulic models)
from .materials import (
    HydraulicModel,
    VanGenuchten,
    ModifiedVanGenuchten,
    BrooksCorey,
    DualPorosity,
    LogNormal,
    CustomHydraulicModel
)

# I/O components
from .io.data_structures import (
    Units,
    ProcessFlags,
    NumericalParameters,
    BoundaryCondition as BoundaryConditionData,
    MaterialProperties,
    ModelDomain,
    TimeControl,
    InitialConditions,
    ModelConfiguration,
    ModelResults
)
from .io.input_parser import InputParser
from .io.output_parser import OutputParser
from .io.input_writer import InputWriter

# Visualization
from .visualization.plots import HydrusVisualizer

# Utilities
from .utils.helpers import (
    create_example_configuration,
    create_infiltration_scenario,
    create_layered_soil,
    get_soil_parameters
)
from .utils.fortran_runner import FortranRunner

__all__ = [
    # Core
    'HydrusModel',
    'RichardsSolver1D',

    # Numerics
    'AdaptiveTimeStepper',
    'solve_tridiagonal',

    # Boundary conditions
    'BoundaryCondition',
    'ConstantHeadBC',
    'ConstantFluxBC',
    'AtmosphericBC',
    'FreeDrainageBC',
    'EnhancedAtmosphericBC',

    # Evapotranspiration
    'WeatherData',
    'PenmanMonteith',
    'SimpleET',
    'ETCalculator',
    'pf_to_head',
    'head_to_pf',

    # Materials
    'HydraulicModel',
    'VanGenuchten',
    'ModifiedVanGenuchten',
    'BrooksCorey',
    'DualPorosity',
    'LogNormal',
    'CustomHydraulicModel',

    # I/O
    'Units',
    'ProcessFlags',
    'NumericalParameters',
    'BoundaryConditionData',
    'MaterialProperties',
    'ModelDomain',
    'TimeControl',
    'InitialConditions',
    'ModelConfiguration',
    'ModelResults',
    'InputParser',
    'OutputParser',
    'InputWriter',

    # Visualization
    'HydrusVisualizer',

    # Utils
    'create_example_configuration',
    'create_infiltration_scenario',
    'create_layered_soil',
    'get_soil_parameters',
    'FortranRunner',
]
