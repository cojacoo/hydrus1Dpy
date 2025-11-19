"""
Data structures for HYDRUS1D model
===================================

Dataclasses and structures to hold model configuration and results.
Based on HYDRUS1D version 4.08 Fortran code structure.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Union
from pathlib import Path
import numpy as np
import pandas as pd


@dataclass
class Units:
    """Unit system for the model"""
    length: str = 'cm'  # Length units: 'cm', 'mm', 'm'
    time: str = 'days'  # Time units: 'min', 'hours', 'days', 'years'
    mass: str = '-'     # Mass units (for solute transport)

    def __post_init__(self):
        """Validate units"""
        valid_length = ['cm', 'mm', 'm']
        valid_time = ['min', 'hours', 'days', 'years']

        if self.length not in valid_length:
            raise ValueError(f"Invalid length unit: {self.length}. Must be one of {valid_length}")
        if self.time not in valid_time:
            raise ValueError(f"Invalid time unit: {self.time}. Must be one of {valid_time}")

    def length_conversion_to_cm(self) -> float:
        """Get conversion factor from model units to cm"""
        conversions = {'cm': 1.0, 'mm': 0.1, 'm': 100.0}
        return conversions[self.length]

    def time_conversion_to_days(self) -> float:
        """Get conversion factor from model units to days"""
        conversions = {'min': 1.0/1440.0, 'hours': 1.0/24.0, 'days': 1.0, 'years': 365.25}
        return conversions[self.time]


@dataclass
class ProcessFlags:
    """Flags for which processes to simulate"""
    water: bool = True       # Water flow (lWat)
    solute: bool = False     # Solute transport (lChem)
    heat: bool = False       # Heat transport (lTemp)
    root: bool = False       # Root water uptake (lRoot)
    snow: bool = False       # Snow accumulation (lSnow)
    vapor: bool = False      # Water vapor transport (lVapor)
    meteo: bool = False      # Meteorological data (lMeteo)

    def __str__(self):
        active = [k for k, v in self.__dict__.items() if v]
        return f"Active processes: {', '.join(active)}"


@dataclass
class NumericalParameters:
    """Numerical solution parameters"""
    max_iter: int = 10           # Maximum iterations for Picard (MaxIt)
    tol_theta: float = 0.001     # Water content tolerance (TolTh)
    tol_h: float = 0.1           # Pressure head tolerance (TolH) [cm]
    cos_alpha: float = 1.0       # Cosine of angle from vertical (CosAlf)

    def __post_init__(self):
        """Validate parameters"""
        if self.max_iter < 1:
            raise ValueError("max_iter must be >= 1")
        if self.tol_theta <= 0:
            raise ValueError("tol_theta must be > 0")
        if self.tol_h <= 0:
            raise ValueError("tol_h must be > 0")
        if not -1.0 <= self.cos_alpha <= 1.0:
            raise ValueError("cos_alpha must be between -1 and 1")


@dataclass
class BoundaryCondition:
    """Boundary condition specification"""
    bc_type: int                 # Boundary condition code (KodTop/KodBot)
    time_variable: bool = False  # Time-variable BC (TopInF/BotInF)
    value: Optional[float] = None  # Constant value if not time-variable
    data: Optional[pd.DataFrame] = None  # Time series if time-variable

    # BC type codes from HYDRUS:
    # -1: Constant head
    # -2: Seepage face
    # -3: Time-variable head/flux
    # -4: Atmospheric BC with surface layer
    # -5: Free drainage
    # -7: Water table (GWL)

    def __post_init__(self):
        """Validate boundary condition"""
        valid_types = [-7, -5, -4, -3, -2, -1, 1, 2, 3]
        if self.bc_type not in valid_types:
            raise ValueError(f"Invalid bc_type: {self.bc_type}")

        if self.time_variable and self.data is None:
            raise ValueError("Time-variable BC requires data")
        if not self.time_variable and self.value is None and abs(self.bc_type) not in [2, 4, 5, 7]:
            raise ValueError("Constant BC requires value")

    @classmethod
    def constant_head(cls, h: float):
        """Create constant head BC"""
        return cls(bc_type=-1, value=h)

    @classmethod
    def constant_flux(cls, flux: float):
        """Create constant flux BC (positive = infiltration)"""
        return cls(bc_type=1, value=flux)

    @classmethod
    def free_drainage(cls):
        """Create free drainage BC (unit gradient)"""
        return cls(bc_type=-5)

    @classmethod
    def atmospheric(cls, data: pd.DataFrame):
        """Create atmospheric BC with time series data"""
        required_cols = ['time', 'Prec', 'rSoil', 'rRoot', 'hCritA']
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"Atmospheric BC data must contain: {required_cols}")
        return cls(bc_type=-4, time_variable=True, data=data)


@dataclass
class MaterialProperties:
    """Soil hydraulic material properties"""
    material_id: int
    model_type: int = 0          # iModel: 0=van Genuchten, 2=Brooks-Corey, etc.
    theta_r: float = 0.0         # Residual water content [-]
    theta_s: float = 0.45        # Saturated water content [-]
    alpha: float = 0.01          # Scale parameter [1/cm]
    n: float = 2.0               # Shape parameter [-]
    Ks: float = 1.0              # Saturated hydraulic conductivity [cm/day]
    l: float = 0.5               # Pore connectivity parameter [-]

    # Additional parameters for other models
    extra_params: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate material properties"""
        if not 0 <= self.theta_r < self.theta_s <= 1:
            raise ValueError(f"Must have 0 <= theta_r < theta_s <= 1")
        if self.alpha <= 0:
            raise ValueError("alpha must be > 0")
        if self.n <= 1:
            raise ValueError("n must be > 1 for van Genuchten")
        if self.Ks <= 0:
            raise ValueError("Ks must be > 0")

    @property
    def m(self) -> float:
        """Calculate m parameter (m = 1 - 1/n)"""
        return 1.0 - 1.0 / self.n

    def to_fortran_array(self) -> np.ndarray:
        """Convert to Fortran parameter array format ParD(1:11)"""
        params = np.zeros(11)
        params[0] = self.theta_r
        params[1] = self.theta_s
        params[2] = self.alpha
        params[3] = self.n
        params[4] = self.Ks
        params[5] = self.l
        # params[6:10] for model-specific parameters
        return params


@dataclass
class ModelDomain:
    """Spatial domain definition"""
    n_nodes: int                           # Number of nodes (NumNP)
    depths: np.ndarray                     # Node depths [cm] (x array)
    materials: np.ndarray                  # Material ID at each node (MatNum)
    n_materials: int = 1                   # Number of different materials (NMat)
    n_layers: int = 1                      # Number of layers (NLay)
    observation_nodes: Optional[List[int]] = None  # Observation node indices (Node)
    layer_numbers: Optional[np.ndarray] = None  # Layer number at each node (LayNum)

    def __post_init__(self):
        """Validate domain"""
        if len(self.depths) != self.n_nodes:
            raise ValueError(f"depths array length ({len(self.depths)}) must equal n_nodes ({self.n_nodes})")
        if len(self.materials) != self.n_nodes:
            raise ValueError(f"materials array length must equal n_nodes")

        # Check depths are monotonically decreasing (surface at top)
        if not np.all(np.diff(self.depths) < 0):
            raise ValueError("depths must be monotonically decreasing (surface = max, bottom = min)")

        # Validate material IDs
        if np.any(self.materials < 1) or np.any(self.materials > self.n_materials):
            raise ValueError(f"Material IDs must be between 1 and {self.n_materials}")

        if self.observation_nodes:
            if any(n < 1 or n > self.n_nodes for n in self.observation_nodes):
                raise ValueError(f"Observation nodes must be between 1 and {self.n_nodes}")

    @property
    def depth_surface(self) -> float:
        """Depth at surface (maximum depth value)"""
        return self.depths[-1]

    @property
    def depth_bottom(self) -> float:
        """Depth at bottom (minimum depth value)"""
        return self.depths[0]

    @property
    def profile_length(self) -> float:
        """Total profile length [cm]"""
        return abs(self.depth_surface - self.depth_bottom)

    def get_node_index(self, depth: float) -> int:
        """Find nearest node index for a given depth"""
        return np.argmin(np.abs(self.depths - depth))


@dataclass
class TimeControl:
    """Time stepping and output control"""
    t_max: float                 # Maximum simulation time (tMax)
    dt_init: float               # Initial time step (dt)
    dt_min: float                # Minimum time step (dtMin)
    dt_max: float                # Maximum time step (dtMax)
    t_init: float = 0.0          # Initial time (tInit)
    dt_multiplier: float = 1.3   # Time step multiplier (dMul)
    dt_multiplier2: float = 0.7  # Time step reduction factor (dMul2)
    print_interval: Optional[float] = None  # Print interval
    print_times: Optional[np.ndarray] = None  # Specific print times (TPrint)

    def __post_init__(self):
        """Validate time control"""
        if self.t_max <= self.t_init:
            raise ValueError("t_max must be > t_init")
        if not self.dt_min <= self.dt_init <= self.dt_max:
            raise ValueError("Must have dt_min <= dt_init <= dt_max")
        if self.dt_multiplier <= 1.0:
            raise ValueError("dt_multiplier must be > 1")
        if not 0 < self.dt_multiplier2 < 1:
            raise ValueError("dt_multiplier2 must be between 0 and 1")

        if self.print_times is None and self.print_interval is None:
            # Default: print every 10% of simulation
            self.print_times = np.linspace(self.t_init, self.t_max, 11)
        elif self.print_times is None:
            # Generate from interval
            self.print_times = np.arange(self.t_init, self.t_max + self.print_interval,
                                         self.print_interval)


@dataclass
class InitialConditions:
    """Initial conditions for the simulation"""
    h_init: np.ndarray           # Initial pressure head [cm] (hNew, hOld)
    theta_init: Optional[np.ndarray] = None  # Initial water content (optional)
    temp_init: Optional[np.ndarray] = None   # Initial temperature (TempN, TempO)
    conc_init: Optional[Dict[int, np.ndarray]] = None  # Initial concentrations by species

    def __post_init__(self):
        """Validate initial conditions"""
        n_nodes = len(self.h_init)

        if self.theta_init is not None and len(self.theta_init) != n_nodes:
            raise ValueError("theta_init length must match h_init")
        if self.temp_init is not None and len(self.temp_init) != n_nodes:
            raise ValueError("temp_init length must match h_init")
        if self.conc_init is not None:
            for species_id, conc in self.conc_init.items():
                if len(conc) != n_nodes:
                    raise ValueError(f"conc_init for species {species_id} length must match h_init")


@dataclass
class ModelConfiguration:
    """Complete model configuration"""
    project_name: str
    units: Units
    domain: ModelDomain
    materials: Dict[int, MaterialProperties]
    bc_top: BoundaryCondition
    bc_bottom: BoundaryCondition
    time_control: TimeControl
    initial_conditions: InitialConditions
    processes: ProcessFlags = field(default_factory=ProcessFlags)
    numerical: NumericalParameters = field(default_factory=NumericalParameters)

    def __post_init__(self):
        """Validate complete configuration"""
        # Check all materials referenced in domain exist
        material_ids = set(self.domain.materials)
        defined_materials = set(self.materials.keys())
        if not material_ids.issubset(defined_materials):
            missing = material_ids - defined_materials
            raise ValueError(f"Materials {missing} referenced but not defined")

        # Check initial conditions match domain
        if len(self.initial_conditions.h_init) != self.domain.n_nodes:
            raise ValueError("Initial conditions must match domain size")


@dataclass
class ModelResults:
    """Container for model results"""
    project_name: str
    success: bool = True
    message: str = ""

    # Time series at observation nodes
    obs_node_data: Optional[pd.DataFrame] = None

    # Mass balance time series
    mass_balance: Optional[pd.DataFrame] = None

    # Profile data at print times
    profiles: Optional[Dict[float, pd.DataFrame]] = None

    # Run information
    run_info: Optional[Dict[str, any]] = None

    def __post_init__(self):
        """Initialize containers"""
        if self.profiles is None:
            self.profiles = {}
        if self.run_info is None:
            self.run_info = {}

    def add_profile(self, time: float, profile_data: pd.DataFrame):
        """Add profile data at a specific time"""
        self.profiles[time] = profile_data

    def get_profile(self, time: float, variable: str = 'h') -> pd.Series:
        """Get profile of variable at specified time"""
        if time not in self.profiles:
            # Find nearest time
            times = np.array(list(self.profiles.keys()))
            nearest_time = times[np.argmin(np.abs(times - time))]
            return self.profiles[nearest_time][variable]
        return self.profiles[time][variable]

    def get_timeseries(self, node: int, variable: str = 'h') -> pd.Series:
        """Get time series of variable at specified node"""
        if self.obs_node_data is None:
            raise ValueError("No observation node data available")

        col_name = f'{variable}{node}'
        if col_name not in self.obs_node_data.columns:
            raise ValueError(f"Variable {col_name} not found in observation data")

        return self.obs_node_data[col_name]

    @property
    def times(self) -> np.ndarray:
        """Get all times with profile data"""
        return np.array(sorted(self.profiles.keys()))

    def summary(self) -> str:
        """Generate summary of results"""
        lines = [
            f"HYDRUS1D Results: {self.project_name}",
            f"Status: {'Success' if self.success else 'Failed'}",
        ]

        if self.message:
            lines.append(f"Message: {self.message}")

        if self.profiles:
            lines.append(f"Profile times: {len(self.profiles)} snapshots")

        if self.obs_node_data is not None:
            lines.append(f"Observation nodes: {len(self.obs_node_data)} time steps")

        if self.mass_balance is not None:
            lines.append(f"Mass balance: {len(self.mass_balance)} time steps")

        return "\n".join(lines)
