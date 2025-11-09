# HYDRUS1D Python Wrapper - Comprehensive Development Plan

## Executive Summary

This document outlines a comprehensive plan to create a Python wrapper for HYDRUS1D, a Fortran-based hydrological model for simulating one-dimensional variably saturated water flow, heat transport, and solute transport. The plan includes three implementation approaches with increasing levels of Python integration, a modular architecture for exchangeable soil hydraulic models, comprehensive testing framework, and interactive visualization capabilities.

## 1. HYDRUS1D Fortran Code Analysis

### 1.1 Code Structure Overview

The HYDRUS1D model consists of approximately 11,000 lines of Fortran code distributed across 10 source files:

| File | Lines | Primary Function |
|------|-------|------------------|
| HYDRUS.FOR | 999 | Main program, initialization, file I/O setup |
| INPUT.FOR | 1,723 | Input file parsing and data structures |
| MATERIAL.FOR | 946 | Soil hydraulic property functions |
| WATFLOW.FOR | 1,127 | Water flow calculations (Richards equation) |
| SOLUTE.FOR | 2,105 | Solute transport calculations |
| TEMPER.FOR | 323 | Heat transport calculations |
| SINK.FOR | 366 | Root water uptake (sink term) |
| TIME.FOR | 1,594 | Time stepping and boundary conditions |
| OUTPUT.FOR | 1,114 | Output generation and mass balance |
| HYSTER.FOR | 756 | Hysteresis modeling |

### 1.2 Key Model Components

#### 1.2.1 Governing Equations

**Water Flow (Richards Equation)**
```
∂θ/∂t = ∂/∂z[K(h)(∂h/∂z + cos(α))] - S(h)
```
Where:
- θ: volumetric water content
- h: pressure head
- K(h): unsaturated hydraulic conductivity
- α: angle from vertical (for slope)
- S(h): sink term (root water uptake)

**Solute Transport**
- Advection-dispersion equation with sequential decay reactions
- Multiple species with interaction
- Mobile-immobile water concepts

**Heat Transport**
- Conduction and convection
- Phase change (vapor transport)
- Energy balance at surface

#### 1.2.2 Soil Hydraulic Models (MATERIAL.FOR)

The code supports multiple soil hydraulic models (iModel parameter):

1. **van Genuchten (iModel=0)** - Primary model
   - Retention: `θ(h) = θr + (θs - θr) / [1 + |αh|^n]^m`
   - Conductivity: `K(h) = Ks * Se^l * [1 - (1 - Se^(1/m))^m]^2`
   - Parameters: θr, θs, α, n, Ks, l (m = 1 - 1/n)

2. **Modified van Genuchten (iModel=1)** - Vogel and Cislerova
   - Additional parameters for separate retention and conductivity curves
   - Parameters: θr, θs, α, n, Ks, l, θm, θa, θk, Kk

3. **Brooks and Corey (iModel=2)**
   - Power-law relationships
   - Parameters: θr, θs, α (air entry), n (pore size distribution)

4. **Log-normal (iModel=4)** - Kosugi model
   - Based on log-normal pore size distribution

5. **Dual-porosity (iModel=5)** - Durner
   - Bimodal pore size distribution
   - Parameters: θr, θs, α, n, Ks, l, w2, α2, n2

6. **Tabulated (iModel=9)** - User-defined tables

### 1.3 Input/Output Structure

#### 1.3.1 Input Files

**Selector.in** (Main control file)
- Header information
- Units (length, time, mass)
- Process flags (lWat, lChem, lTemp, lSnow, lVapor, etc.)
- Material and layer counts
- Numerical parameters (MaxIt, TolTh, TolH)
- Boundary condition types (KodTop, KodBot)
- Time control parameters

**Profile.dat**
- Node coordinates (x array)
- Initial pressure heads (hNew)
- Material assignments (MatNum)
- Observation node locations
- Material properties (θr, θs, α, n, Ks, l)
- Initial conditions for solutes and temperature

**ATMOSPH.IN** (Time-variable boundary conditions)
- Time series of:
  - Precipitation
  - Evaporation
  - Atmospheric pressure head
  - Solute concentrations
  - Temperature

**Meteo.in** (Optional meteorological data)
- Solar radiation
- Temperature (max/min)
- Humidity
- Wind speed
- For evapotranspiration calculations

#### 1.3.2 Output Files

**I_CHECK.OUT** - Input verification
**RUN_INF.OUT** - Runtime information
**T_LEVEL.OUT** - Time-level information (mass balance)
**NOD_INF.OUT** - Node information at print times
**BALANCE.OUT** - Water and solute mass balance
**OBS_NODE.OUT** - Time series at observation nodes
**PROFILE.OUT** - Full profile outputs

### 1.4 Numerical Solution Approach

- **Spatial discretization**: Finite difference/finite element hybrid
- **Time discretization**: Adaptive time stepping
- **Linearization**: Picard iteration (successive substitution)
- **Matrix solution**: Gauss elimination (tridiagonal)
- **Convergence criteria**: Based on water content (TolTh) and pressure head (TolH)
- **Time step control**: Automatic adjustment based on iteration count

## 2. Python Wrapper Strategies

### 2.1 Strategy A: Fortran Engine with Python I/O (Minimal Intervention)

**Approach**: Keep Fortran computation engine, wrap with Python for I/O and pre/post-processing

**Advantages**:
- Fastest implementation (~2-4 weeks)
- Maintains proven numerical stability
- No revalidation of core physics needed
- Leverage existing Fortran optimizations

**Disadvantages**:
- Limited extensibility
- Requires Fortran compiler
- Platform-dependent binaries
- Difficult to debug across language boundary

**Implementation Tools**:
- `f2py` for automatic wrapper generation
- `subprocess` for direct executable calls
- `ctypes` for shared library interface

### 2.2 Strategy B: Hybrid Python/Fortran (Gradual Migration)

**Approach**: Convert I/O and utilities to Python, keep numerical solvers in Fortran/Cython

**Advantages**:
- Balance of performance and maintainability
- Easier testing and debugging
- Gradual migration path
- Core numerics still compiled

**Disadvantages**:
- Moderate development time (~2-3 months)
- Requires careful interface design
- Mixed-language debugging

**Implementation Tools**:
- Cython for hot loops
- NumPy for array operations
- f2py for retained Fortran components

### 2.3 Strategy C: Pure Python with Numba (Full Conversion)

**Approach**: Complete rewrite in Python with Numba JIT compilation for performance

**Advantages**:
- Full Python ecosystem integration
- Easier to extend and maintain
- No compiler dependencies for users
- Modern development practices (testing, CI/CD)
- Better documentation and readability

**Disadvantages**:
- Longest development time (~3-6 months)
- Requires complete revalidation
- Initial performance tuning needed
- Risk of introducing numerical errors

**Implementation Tools**:
- NumPy for arrays
- SciPy for linear algebra
- Numba for JIT compilation
- Xarray for data management

## 3. Recommended Implementation Plan: Phased Approach

**Phase 1**: Strategy A (Weeks 1-4)
**Phase 2**: Strategy B (Months 2-3)
**Phase 3**: Strategy C (Months 4-6+)

This allows immediate functionality while building toward long-term sustainability.

## 4. Architecture Design

### 4.1 Package Structure

```
hydrus1dpy/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── model.py              # Main Model class
│   ├── fortran_interface.py  # Fortran wrapper (Phase 1)
│   ├── solver.py             # Python solvers (Phase 2/3)
│   └── numerics.py           # Numerical utilities
├── io/
│   ├── __init__.py
│   ├── input_parser.py       # Parse Selector.in, Profile.dat, etc.
│   ├── output_parser.py      # Parse output files
│   ├── input_writer.py       # Write Fortran-compatible inputs
│   └── data_structures.py    # Dataclasses for model data
├── materials/
│   ├── __init__.py
│   ├── base.py              # Abstract base class for hydraulic models
│   ├── van_genuchten.py     # van Genuchten implementation
│   ├── brooks_corey.py      # Brooks-Corey implementation
│   ├── dual_porosity.py     # Dual-porosity models
│   ├── custom.py            # User-defined models
│   └── parameters.py        # Parameter classes
├── boundary/
│   ├── __init__.py
│   ├── atmospheric.py       # Atmospheric boundary conditions
│   ├── constant.py          # Constant BC
│   └── variable.py          # Time-variable BC
├── processes/
│   ├── __init__.py
│   ├── water_flow.py        # Richards equation solver
│   ├── solute_transport.py  # ADE solver
│   ├── heat_transport.py    # Heat equation solver
│   └── root_uptake.py       # Sink term calculations
├── visualization/
│   ├── __init__.py
│   ├── plots.py             # Plotly plotting functions
│   ├── profiles.py          # Profile visualization
│   ├── timeseries.py        # Time series plots
│   └── interactive.py       # Interactive dashboards
├── validation/
│   ├── __init__.py
│   ├── test_cases.py        # Standard test problems
│   ├── benchmarks.py        # Benchmark solutions
│   └── comparisons.py       # Fortran vs Python comparison
└── utils/
    ├── __init__.py
    ├── units.py             # Unit conversions
    ├── interpolation.py     # Interpolation utilities
    └── mesh.py              # Mesh generation
```

### 4.2 Core Classes

#### 4.2.1 Model Class

```python
from dataclasses import dataclass
from typing import Optional, Union
import numpy as np

@dataclass
class ModelDomain:
    """Spatial domain definition"""
    nodes: int
    depths: np.ndarray  # Node depths [cm]
    materials: np.ndarray  # Material IDs per node
    observation_nodes: Optional[list] = None

@dataclass
class TimeControl:
    """Time stepping parameters"""
    t_init: float = 0.0
    t_max: float
    dt_init: float
    dt_min: float
    dt_max: float
    print_times: np.ndarray

class HYDRUS1D:
    """Main model class"""

    def __init__(self,
                 domain: ModelDomain,
                 materials: dict,  # Material ID -> HydraulicModel
                 boundary_top: BoundaryCondition,
                 boundary_bottom: BoundaryCondition,
                 time_control: TimeControl,
                 processes: dict = None):
        """
        Initialize HYDRUS1D model

        Parameters
        ----------
        domain : ModelDomain
            Spatial discretization
        materials : dict
            Mapping of material IDs to HydraulicModel objects
        boundary_top : BoundaryCondition
            Upper boundary condition
        boundary_bottom : BoundaryCondition
            Lower boundary condition
        time_control : TimeControl
            Time stepping parameters
        processes : dict, optional
            Flags for processes (water, solute, heat)
        """
        self.domain = domain
        self.materials = materials
        self.bc_top = boundary_top
        self.bc_bottom = boundary_bottom
        self.time = time_control
        self.processes = processes or {'water': True}

        # State variables
        self.h = None  # Pressure head [cm]
        self.theta = None  # Water content [-]
        self.K = None  # Hydraulic conductivity [cm/day]
        self.C = None  # Specific water capacity [1/cm]

        # Results storage
        self.results = ModelResults()

    def set_initial_conditions(self, h_init: np.ndarray):
        """Set initial pressure head distribution"""
        self.h = h_init.copy()
        self._update_hydraulic_properties()

    def run(self, engine='fortran'):
        """
        Run simulation

        Parameters
        ----------
        engine : str
            'fortran', 'python', or 'numba'
        """
        if engine == 'fortran':
            return self._run_fortran()
        elif engine == 'python':
            return self._run_python()
        elif engine == 'numba':
            return self._run_numba()
        else:
            raise ValueError(f"Unknown engine: {engine}")

    def _run_fortran(self):
        """Run using Fortran engine"""
        from .fortran_interface import FortranRunner
        runner = FortranRunner(self)
        return runner.execute()

    def _run_python(self):
        """Run using pure Python"""
        from .solver import PythonSolver
        solver = PythonSolver(self)
        return solver.solve()

    def _run_numba(self):
        """Run using Numba-accelerated Python"""
        from .solver import NumbaSolver
        solver = NumbaSolver(self)
        return solver.solve()

    def _update_hydraulic_properties(self):
        """Update K, theta, C based on current h"""
        for node in range(self.domain.nodes):
            mat_id = self.domain.materials[node]
            material = self.materials[mat_id]

            self.theta[node] = material.water_content(self.h[node])
            self.K[node] = material.conductivity(self.h[node])
            self.C[node] = material.capacity(self.h[node])
```

#### 4.2.2 Hydraulic Model Base Class

```python
from abc import ABC, abstractmethod
import numpy as np

class HydraulicModel(ABC):
    """Abstract base class for soil hydraulic models"""

    def __init__(self, theta_r: float, theta_s: float, **kwargs):
        """
        Parameters
        ----------
        theta_r : float
            Residual water content [-]
        theta_s : float
            Saturated water content [-]
        """
        self.theta_r = theta_r
        self.theta_s = theta_s
        self.params = kwargs

    @abstractmethod
    def water_content(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate water content from pressure head

        Parameters
        ----------
        h : float or array
            Pressure head [cm]

        Returns
        -------
        theta : float or array
            Volumetric water content [-]
        """
        pass

    @abstractmethod
    def conductivity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate hydraulic conductivity from pressure head

        Parameters
        ----------
        h : float or array
            Pressure head [cm]

        Returns
        -------
        K : float or array
            Hydraulic conductivity [cm/day]
        """
        pass

    @abstractmethod
    def capacity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate specific water capacity (dθ/dh)

        Parameters
        ----------
        h : float or array
            Pressure head [cm]

        Returns
        -------
        C : float or array
            Specific water capacity [1/cm]
        """
        pass

    def pressure_head(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate pressure head from water content (inverse function)

        Parameters
        ----------
        theta : float or array
            Volumetric water content [-]

        Returns
        -------
        h : float or array
            Pressure head [cm]
        """
        # Default implementation using bisection
        # Can be overridden for analytical solutions
        from scipy.optimize import brentq

        if np.isscalar(theta):
            return brentq(lambda h: self.water_content(h) - theta, -1e6, 0)
        else:
            return np.array([self.pressure_head(t) for t in theta])
```

#### 4.2.3 van Genuchten Implementation

```python
import numpy as np
from typing import Union

class VanGenuchten(HydraulicModel):
    """van Genuchten (1980) soil hydraulic model"""

    def __init__(self,
                 theta_r: float,
                 theta_s: float,
                 alpha: float,
                 n: float,
                 Ks: float,
                 l: float = 0.5):
        """
        Parameters
        ----------
        theta_r : float
            Residual water content [-]
        theta_s : float
            Saturated water content [-]
        alpha : float
            Scale parameter [1/cm]
        n : float
            Shape parameter [-]
        Ks : float
            Saturated hydraulic conductivity [cm/day]
        l : float, optional
            Pore connectivity parameter [-], default 0.5
        """
        super().__init__(theta_r, theta_s)
        self.alpha = alpha
        self.n = n
        self.m = 1.0 - 1.0 / n
        self.Ks = Ks
        self.l = l

    def water_content(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """van Genuchten water retention function"""
        h = np.asarray(h)

        # For h >= 0 (saturated)
        theta = np.full_like(h, self.theta_s, dtype=float)

        # For h < 0 (unsaturated)
        mask = h < 0
        if np.any(mask):
            Se = (1.0 + np.abs(self.alpha * h[mask]) ** self.n) ** (-self.m)
            theta[mask] = self.theta_r + (self.theta_s - self.theta_r) * Se

        return float(theta) if np.isscalar(h) else theta

    def conductivity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """van Genuchten hydraulic conductivity function (Mualem, 1976)"""
        h = np.asarray(h)

        # For h >= 0 (saturated)
        K = np.full_like(h, self.Ks, dtype=float)

        # For h < 0 (unsaturated)
        mask = h < 0
        if np.any(mask):
            Se = self._effective_saturation(h[mask])
            K[mask] = self.Ks * Se ** self.l * (1.0 - (1.0 - Se ** (1.0/self.m)) ** self.m) ** 2

        return float(K) if np.isscalar(h) else K

    def capacity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Specific water capacity (dθ/dh)"""
        h = np.asarray(h)

        # For h >= 0 (saturated)
        C = np.zeros_like(h, dtype=float)

        # For h < 0 (unsaturated)
        mask = h < 0
        if np.any(mask):
            h_neg = h[mask]
            term1 = (1.0 + np.abs(self.alpha * h_neg) ** self.n) ** (-self.m - 1.0)
            term2 = (self.theta_s - self.theta_r) * self.m * self.n
            term3 = (self.alpha ** self.n) * (np.abs(h_neg) ** (self.n - 1.0))
            C[mask] = term2 * term3 * term1

        return float(C) if np.isscalar(h) else C

    def _effective_saturation(self, h: np.ndarray) -> np.ndarray:
        """Calculate effective saturation"""
        return (1.0 + np.abs(self.alpha * h) ** self.n) ** (-self.m)

    def pressure_head(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Analytical inverse function"""
        theta = np.asarray(theta)

        # Clip to valid range
        theta = np.clip(theta, self.theta_r, self.theta_s)

        # For theta = theta_s (saturated)
        h = np.zeros_like(theta, dtype=float)

        # For theta < theta_s (unsaturated)
        mask = theta < self.theta_s
        if np.any(mask):
            Se = (theta[mask] - self.theta_r) / (self.theta_s - self.theta_r)
            h[mask] = -1.0 / self.alpha * (Se ** (-1.0/self.m) - 1.0) ** (1.0/self.n)

        return float(h) if np.isscalar(theta) else h
```

#### 4.2.4 Custom Hydraulic Model Interface

```python
class CustomHydraulicModel(HydraulicModel):
    """User-defined hydraulic model using callable functions"""

    def __init__(self,
                 theta_r: float,
                 theta_s: float,
                 theta_func: callable,
                 K_func: callable,
                 C_func: callable = None):
        """
        Parameters
        ----------
        theta_r : float
            Residual water content
        theta_s : float
            Saturated water content
        theta_func : callable
            Function for water content: theta = f(h, params)
        K_func : callable
            Function for conductivity: K = f(h, params)
        C_func : callable, optional
            Function for capacity: C = f(h, params)
            If None, computed numerically
        """
        super().__init__(theta_r, theta_s)
        self._theta_func = theta_func
        self._K_func = K_func
        self._C_func = C_func

    def water_content(self, h):
        return self._theta_func(h, theta_r=self.theta_r, theta_s=self.theta_s, **self.params)

    def conductivity(self, h):
        return self._K_func(h, theta_r=self.theta_r, theta_s=self.theta_s, **self.params)

    def capacity(self, h):
        if self._C_func:
            return self._C_func(h, theta_r=self.theta_r, theta_s=self.theta_s, **self.params)
        else:
            # Numerical differentiation
            dh = 0.001
            return (self.water_content(h + dh) - self.water_content(h - dh)) / (2 * dh)
```

### 4.3 Exchangeable Soil Hydraulic Models

The architecture supports easy swapping of hydraulic models:

```python
# Example 1: Using van Genuchten
vg_model = VanGenuchten(
    theta_r=0.078,
    theta_s=0.43,
    alpha=0.036,
    n=1.56,
    Ks=24.96,
    l=0.5
)

# Example 2: Using Brooks-Corey
bc_model = BrooksCorey(
    theta_r=0.078,
    theta_s=0.43,
    h_b=27.8,  # Air entry value
    lambda_=0.5,  # Pore size distribution
    Ks=24.96
)

# Example 3: Custom model
def custom_theta(h, theta_r, theta_s, a, b):
    """Custom water retention function"""
    if h >= 0:
        return theta_s
    else:
        return theta_r + (theta_s - theta_r) * np.exp(a * h ** b)

custom_model = CustomHydraulicModel(
    theta_r=0.078,
    theta_s=0.43,
    theta_func=custom_theta,
    K_func=lambda h, **kw: 24.96 * np.exp(0.05 * h),
    a=0.01,
    b=0.8
)

# Use in model
materials = {
    1: vg_model,
    2: bc_model,
    3: custom_model
}
```

### 4.4 Input/Output Management

```python
from pathlib import Path
from dataclasses import dataclass
import pandas as pd

class InputParser:
    """Parse HYDRUS1D input files"""

    def __init__(self, project_path: Union[str, Path]):
        self.path = Path(project_path)

    def read_selector(self) -> dict:
        """Parse Selector.in file"""
        selector_file = self.path / 'Selector.in'
        # Implementation details...
        return {
            'units': {'length': 'cm', 'time': 'days'},
            'processes': {'water': True, 'solute': False, 'heat': False},
            'n_materials': 1,
            'max_iter': 10,
            'tol_theta': 0.001,
            'tol_h': 0.1,
            # ... more parameters
        }

    def read_profile(self) -> tuple:
        """Parse Profile.dat file"""
        profile_file = self.path / 'Profile.dat'
        # Returns domain, initial conditions, materials
        return domain, h_init, materials

    def read_atmosph(self) -> pd.DataFrame:
        """Parse ATMOSPH.IN file"""
        atmosph_file = self.path / 'ATMOSPH.IN'
        # Returns time series dataframe
        return pd.DataFrame({
            'time': [...],
            'Prec': [...],
            'rSoil': [...],
            'rRoot': [...],
            'hCritA': [...],
        })

class OutputParser:
    """Parse HYDRUS1D output files"""

    def __init__(self, project_path: Union[str, Path]):
        self.path = Path(project_path)

    def read_obs_node(self) -> pd.DataFrame:
        """Parse OBS_NODE.OUT"""
        obs_file = self.path / 'OBS_NODE.OUT'
        # Returns time series at observation nodes

    def read_tlevel(self) -> pd.DataFrame:
        """Parse T_LEVEL.OUT (mass balance)"""
        tlevel_file = self.path / 'T_LEVEL.OUT'
        # Returns mass balance time series

    def read_nod_inf(self, time_index: int = -1) -> pd.DataFrame:
        """Parse NOD_INF.OUT (profiles)"""
        nod_file = self.path / 'NOD_INF.OUT'
        # Returns profile data at specified time

class InputWriter:
    """Write HYDRUS1D-compatible input files"""

    def __init__(self, model: HYDRUS1D, output_path: Union[str, Path]):
        self.model = model
        self.path = Path(output_path)
        self.path.mkdir(exist_ok=True)

    def write_selector(self):
        """Write Selector.in"""
        # Implementation...

    def write_profile(self):
        """Write Profile.dat"""
        # Implementation...

    def write_atmosph(self, bc_data: pd.DataFrame):
        """Write ATMOSPH.IN"""
        # Implementation...
```

## 5. Fortran Interface (Phase 1)

### 5.1 Compilation Strategy

```bash
# Compile Fortran to shared library
gfortran -c -fPIC -O3 src/*.FOR
gfortran -shared -o libhydrus1d.so *.o

# Or use f2py
f2py -c -m hydrus1d_fortran src/*.FOR
```

### 5.2 Python Wrapper

```python
import ctypes
import numpy as np
from pathlib import Path

class FortranRunner:
    """Interface to compiled Fortran HYDRUS1D"""

    def __init__(self, model: HYDRUS1D):
        self.model = model
        self.lib = self._load_library()

    def _load_library(self):
        """Load compiled Fortran library"""
        lib_path = Path(__file__).parent / 'libhydrus1d.so'
        return ctypes.CDLL(str(lib_path))

    def execute(self):
        """Run Fortran model"""
        # Write input files
        temp_dir = Path('./temp_hydrus_run')
        temp_dir.mkdir(exist_ok=True)

        writer = InputWriter(self.model, temp_dir)
        writer.write_selector()
        writer.write_profile()
        if self.model.bc_top.is_time_variable:
            writer.write_atmosph(self.model.bc_top.data)

        # Call Fortran executable
        import subprocess
        result = subprocess.run(
            ['./hydrus1d', str(temp_dir)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Fortran execution failed: {result.stderr}")

        # Parse output files
        parser = OutputParser(temp_dir)
        results = ModelResults(
            obs_nodes=parser.read_obs_node(),
            mass_balance=parser.read_tlevel(),
            profiles=parser.read_nod_inf()
        )

        # Cleanup
        # shutil.rmtree(temp_dir)  # Optional

        return results
```

## 6. Python/Numba Solver (Phase 3)

### 6.1 Richards Equation Solver

```python
import numpy as np
from numba import jit

class RichardsSolver:
    """Solve Richards equation using mixed form"""

    def __init__(self,
                 domain: ModelDomain,
                 materials: dict,
                 bc_top: BoundaryCondition,
                 bc_bottom: BoundaryCondition,
                 time_params: TimeControl):
        self.domain = domain
        self.materials = materials
        self.bc_top = bc_top
        self.bc_bottom = bc_bottom
        self.time = time_params

    def solve(self, h_init: np.ndarray) -> ModelResults:
        """
        Main solution loop

        Parameters
        ----------
        h_init : np.ndarray
            Initial pressure head distribution

        Returns
        -------
        results : ModelResults
            Simulation results
        """
        # Initialize
        n = self.domain.nodes
        h = h_init.copy()
        h_old = h.copy()
        theta = np.zeros(n)
        theta_old = np.zeros(n)

        # Update hydraulic properties
        K, C = self._update_properties(h)

        # Time loop
        t = self.time.t_init
        dt = self.time.dt_init
        results = ModelResults()

        while t < self.time.t_max:
            # Adaptive time stepping
            converged = False
            iter_count = 0

            while not converged:
                # Picard iteration
                h_temp = h.copy()

                # Assemble matrix
                A, b = self._assemble_system(h, h_old, theta_old, K, C, dt)

                # Apply boundary conditions
                self._apply_bc(A, b, h, t)

                # Solve linear system
                h = self._solve_linear_system(A, b)

                # Update properties
                K, C = self._update_properties(h)

                # Check convergence
                converged, iter_count = self._check_convergence(
                    h, h_temp, theta, theta_old, C, iter_count
                )

                if iter_count > self.max_iter and not converged:
                    # Reduce time step and retry
                    dt = max(dt / 3.0, self.time.dt_min)
                    h = h_old.copy()
                    if dt == self.time.dt_min:
                        raise RuntimeError("Solution did not converge")
                    continue

            # Update for next time step
            h_old = h.copy()
            theta_old = theta.copy()
            t += dt

            # Store results at print times
            if self._is_print_time(t):
                results.store(t, h, theta, K)

            # Adjust time step based on iterations
            dt = self._adjust_timestep(dt, iter_count)

        return results

    @staticmethod
    @jit(nopython=True)
    def _assemble_system(h, h_old, theta_old, K, C, dt):
        """
        Assemble finite difference system (JIT compiled)

        Mixed form: C(h) * dh/dt = d/dx[K(h) * (dh/dx + 1)] - S
        """
        n = len(h)
        A = np.zeros((n, 3))  # Tridiagonal matrix (sub, diag, super)
        b = np.zeros(n)

        for i in range(1, n-1):
            # Internodal hydraulic conductivities
            K_plus = 0.5 * (K[i] + K[i+1])
            K_minus = 0.5 * (K[i] + K[i-1])

            # Grid spacing
            dx_plus = x[i+1] - x[i]
            dx_minus = x[i] - x[i-1]
            dx = 0.5 * (dx_plus + dx_minus)

            # Coefficients
            A[i, 0] = -K_minus / (dx_minus * dx)  # Sub-diagonal
            A[i, 1] = C[i] / dt + (K_plus / dx_plus + K_minus / dx_minus) / dx  # Diagonal
            A[i, 2] = -K_plus / (dx_plus * dx)  # Super-diagonal

            # Right-hand side
            b[i] = C[i] * h_old[i] / dt + (K_plus - K_minus) / dx - S[i]

        return A, b

    def _update_properties(self, h):
        """Update K, C, theta based on current h"""
        n = self.domain.nodes
        K = np.zeros(n)
        C = np.zeros(n)

        for i in range(n):
            mat_id = self.domain.materials[i]
            material = self.materials[mat_id]
            K[i] = material.conductivity(h[i])
            C[i] = material.capacity(h[i])

        return K, C

    def _check_convergence(self, h, h_temp, theta, theta_old, C, iter_count):
        """Check Picard iteration convergence"""
        iter_count += 1

        # Update theta
        for i in range(len(h)):
            mat_id = self.domain.materials[i]
            theta[i] = self.materials[mat_id].water_content(h[i])

        # Convergence criteria
        dh = np.abs(h - h_temp)
        dtheta = np.abs(theta - theta_old)

        h_converged = np.all(dh < self.tol_h)
        theta_converged = np.all(dtheta < self.tol_theta)

        return (h_converged and theta_converged), iter_count
```

### 6.2 Numba Optimization

```python
from numba import jit, prange

@jit(nopython=True, parallel=True)
def compute_hydraulic_properties_vectorized(h, theta_r, theta_s, alpha, n, Ks, l):
    """Vectorized hydraulic property calculation"""
    m = 1.0 - 1.0 / n
    n_nodes = len(h)

    theta = np.empty(n_nodes)
    K = np.empty(n_nodes)
    C = np.empty(n_nodes)

    for i in prange(n_nodes):
        if h[i] >= 0:
            theta[i] = theta_s
            K[i] = Ks
            C[i] = 0.0
        else:
            # van Genuchten functions (inlined for speed)
            ah_n = (alpha * abs(h[i])) ** n
            term = 1.0 + ah_n
            Se = term ** (-m)

            theta[i] = theta_r + (theta_s - theta_r) * Se

            Se_1m = Se ** (1.0 / m)
            K[i] = Ks * (Se ** l) * (1.0 - (1.0 - Se_1m) ** m) ** 2

            C[i] = (theta_s - theta_r) * m * n * (alpha ** n) * \
                   (abs(h[i]) ** (n - 1.0)) * (term ** (-m - 1.0))

    return theta, K, C
```

## 7. Testing and Validation

### 7.1 Unit Tests

```python
import pytest
import numpy as np
from hydrus1dpy.materials import VanGenuchten

class TestVanGenuchten:
    """Test van Genuchten hydraulic model"""

    def setup_method(self):
        """Setup test parameters (Loam soil)"""
        self.model = VanGenuchten(
            theta_r=0.078,
            theta_s=0.43,
            alpha=0.036,
            n=1.56,
            Ks=24.96,
            l=0.5
        )

    def test_saturated_water_content(self):
        """Test that theta(h=0) = theta_s"""
        theta = self.model.water_content(0.0)
        assert np.isclose(theta, self.model.theta_s)

    def test_saturated_conductivity(self):
        """Test that K(h=0) = Ks"""
        K = self.model.conductivity(0.0)
        assert np.isclose(K, self.model.Ks)

    def test_residual_water_content(self):
        """Test that theta -> theta_r as h -> -infinity"""
        theta = self.model.water_content(-1e6)
        assert theta > self.model.theta_r
        assert theta < self.model.theta_r + 0.001

    def test_inverse_function(self):
        """Test that h(theta(h)) = h"""
        h_test = -100.0
        theta = self.model.water_content(h_test)
        h_calc = self.model.pressure_head(theta)
        assert np.isclose(h_calc, h_test, rtol=1e-3)

    def test_vectorized_operations(self):
        """Test array input"""
        h = np.array([-1000, -100, -10, 0])
        theta = self.model.water_content(h)
        assert len(theta) == len(h)
        assert np.all(theta >= self.model.theta_r)
        assert np.all(theta <= self.model.theta_s)
```

### 7.2 Integration Tests

```python
class TestRichardsSolver:
    """Test Richards equation solver"""

    def test_steady_state_infiltration(self):
        """Test steady infiltration (Darcy's law)"""
        # Setup vertical column with constant flux at top
        domain = ModelDomain(
            nodes=101,
            depths=np.linspace(0, -100, 101)
        )

        material = VanGenuchten(
            theta_r=0.078,
            theta_s=0.43,
            alpha=0.036,
            n=1.56,
            Ks=24.96
        )

        bc_top = FluxBC(flux=-5.0)  # cm/day
        bc_bottom = PressureBC(h=-100.0)

        model = HYDRUS1D(domain, {1: material}, bc_top, bc_bottom)
        model.set_initial_conditions(np.linspace(0, -100, 101))

        results = model.run(engine='python')

        # At steady state, q = K(h) * (dh/dz + 1) = constant
        h_final = results.get_profile(-1, 'h')
        # Verify solution...

    def test_infiltration_redistribution(self):
        """Test infiltration followed by redistribution"""
        # Compare with analytical Parlange solution
        # ...
```

### 7.3 Validation Against Fortran

```python
class TestFortranComparison:
    """Compare Python implementation against Fortran"""

    @pytest.fixture
    def reference_case(self):
        """Load reference Fortran results"""
        return OutputParser('./tests/reference_runs/case1').read_obs_node()

    def test_infiltration_case(self, reference_case):
        """Test Case 1: Infiltration into dry soil"""
        # Setup Python model
        model = self._setup_case1()

        # Run Python solver
        results_py = model.run(engine='python')

        # Run Fortran solver
        results_f = model.run(engine='fortran')

        # Compare results
        for obs in [1, 2, 3]:
            h_py = results_py.obs_nodes[f'h{obs}']
            h_f = results_f.obs_nodes[f'h{obs}']
            h_ref = reference_case[f'h{obs}']

            # Check Python vs Fortran
            rmse = np.sqrt(np.mean((h_py - h_f)**2))
            assert rmse < 1.0, f"RMSE too large at obs {obs}: {rmse}"

            # Check against reference
            rmse_ref = np.sqrt(np.mean((h_py - h_ref)**2))
            assert rmse_ref < 2.0

    def test_all_benchmark_cases(self):
        """Run all benchmark test cases"""
        cases = [
            'infiltration_dry',
            'infiltration_wet',
            'evaporation',
            'drainage',
            'water_table',
        ]

        for case_name in cases:
            self._run_comparison(case_name)
```

### 7.4 Benchmark Problems

Standard test cases to implement:

1. **Haverkamp Infiltration** - Infiltration into dry soil, comparison with analytical solution
2. **Constant Flux** - Steady-state infiltration, verify Darcy's law
3. **Free Drainage** - Unit gradient condition at bottom
4. **Water Table** - Rising/falling water table scenarios
5. **Evaporation** - Atmospheric BC with evaporation
6. **Layered Soil** - Multiple materials, test interface conditions
7. **Root Uptake** - Transpiration with Feddes model

## 8. Visualization with Plotly

### 8.1 Profile Plots

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class HydrusVisualizer:
    """Create interactive visualizations of HYDRUS results"""

    def __init__(self, results: ModelResults):
        self.results = results

    def plot_profile(self, times: list, variable='h'):
        """
        Plot vertical profiles at multiple times

        Parameters
        ----------
        times : list
            List of times to plot
        variable : str
            'h', 'theta', 'K', or 'v'
        """
        fig = go.Figure()

        for t in times:
            profile = self.results.get_profile(t, variable)
            depths = self.results.depths

            fig.add_trace(go.Scatter(
                x=profile,
                y=depths,
                mode='lines+markers',
                name=f't = {t:.2f} days',
                hovertemplate='%{y:.1f} cm<br>%{x:.3f}<extra></extra>'
            ))

        # Formatting
        labels = {
            'h': 'Pressure Head [cm]',
            'theta': 'Water Content [-]',
            'K': 'Hydraulic Conductivity [cm/day]',
            'v': 'Water Flux [cm/day]'
        }

        fig.update_layout(
            title=f'Vertical Profile: {labels[variable]}',
            xaxis_title=labels[variable],
            yaxis_title='Depth [cm]',
            yaxis=dict(autorange='reversed'),
            hovermode='closest',
            template='plotly_white'
        )

        return fig

    def plot_timeseries(self, depths: list, variable='h'):
        """
        Plot time series at specific depths

        Parameters
        ----------
        depths : list
            Depths to plot [cm]
        variable : str
            'h', 'theta', 'K'
        """
        fig = go.Figure()

        for depth in depths:
            ts = self.results.get_timeseries(depth, variable)

            fig.add_trace(go.Scatter(
                x=ts.time,
                y=ts.values,
                mode='lines',
                name=f'z = {depth} cm',
                hovertemplate='%{x:.2f} days<br>%{y:.3f}<extra></extra>'
            ))

        labels = {
            'h': 'Pressure Head [cm]',
            'theta': 'Water Content [-]',
            'K': 'Hydraulic Conductivity [cm/day]'
        }

        fig.update_layout(
            title=f'Time Series: {labels[variable]}',
            xaxis_title='Time [days]',
            yaxis_title=labels[variable],
            hovermode='x unified',
            template='plotly_white'
        )

        return fig

    def plot_mass_balance(self):
        """Plot cumulative mass balance"""
        mb = self.results.mass_balance

        fig = go.Figure()

        # Cumulative fluxes
        fig.add_trace(go.Scatter(
            x=mb.time, y=mb.cum_infiltration,
            name='Infiltration', mode='lines', line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=mb.time, y=mb.cum_evaporation,
            name='Evaporation', mode='lines', line=dict(color='red')
        ))
        fig.add_trace(go.Scatter(
            x=mb.time, y=mb.cum_drainage,
            name='Drainage', mode='lines', line=dict(color='green')
        ))
        fig.add_trace(go.Scatter(
            x=mb.time, y=mb.cum_root_uptake,
            name='Root Uptake', mode='lines', line=dict(color='orange')
        ))

        # Storage change
        fig.add_trace(go.Scatter(
            x=mb.time, y=mb.storage_change,
            name='Storage Change', mode='lines',
            line=dict(color='black', dash='dash')
        ))

        # Mass balance error
        fig.add_trace(go.Scatter(
            x=mb.time, y=mb.error,
            name='Error', mode='lines',
            line=dict(color='gray'), yaxis='y2'
        ))

        fig.update_layout(
            title='Cumulative Mass Balance',
            xaxis_title='Time [days]',
            yaxis_title='Cumulative Water [cm]',
            yaxis2=dict(title='Error [cm]', overlaying='y', side='right'),
            hovermode='x unified',
            template='plotly_white'
        )

        return fig

    def plot_animation(self, variable='theta'):
        """Create animated profile evolution"""
        times = self.results.times
        depths = self.results.depths

        # Create frames
        frames = []
        for t in times:
            profile = self.results.get_profile(t, variable)
            frame = go.Frame(
                data=[go.Scatter(x=profile, y=depths, mode='lines+markers')],
                name=f'{t:.2f}'
            )
            frames.append(frame)

        # Initial plot
        profile_0 = self.results.get_profile(times[0], variable)

        fig = go.Figure(
            data=[go.Scatter(x=profile_0, y=depths, mode='lines+markers')],
            frames=frames
        )

        # Add play/pause buttons
        fig.update_layout(
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'buttons': [
                    {'label': 'Play', 'method': 'animate',
                     'args': [None, {'frame': {'duration': 100}}]},
                    {'label': 'Pause', 'method': 'animate',
                     'args': [[None], {'frame': {'duration': 0}, 'mode': 'immediate'}]}
                ]
            }],
            sliders=[{
                'steps': [
                    {'args': [[f.name], {'frame': {'duration': 0}, 'mode': 'immediate'}],
                     'label': f'{float(f.name):.2f}', 'method': 'animate'}
                    for f in frames
                ],
                'active': 0,
                'yanchor': 'top',
                'y': 0,
                'xanchor': 'left',
                'x': 0.1,
                'currentvalue': {'prefix': 'Time: ', 'suffix': ' days'},
                'len': 0.9
            }],
            yaxis=dict(autorange='reversed'),
            template='plotly_white'
        )

        return fig

    def create_dashboard(self):
        """Create interactive dashboard with multiple panels"""
        from jupyter_dash import JupyterDash
        from dash import dcc, html, Input, Output

        app = JupyterDash(__name__)

        app.layout = html.Div([
            html.H1('HYDRUS1D Results Dashboard'),

            dcc.Tabs([
                dcc.Tab(label='Profiles', children=[
                    dcc.Graph(id='profile-plot'),
                    dcc.Slider(
                        id='time-slider',
                        min=0,
                        max=len(self.results.times)-1,
                        value=0,
                        marks={i: f'{t:.1f}' for i, t in enumerate(self.results.times[::10])}
                    )
                ]),

                dcc.Tab(label='Time Series', children=[
                    dcc.Graph(id='timeseries-plot'),
                    dcc.Dropdown(
                        id='depth-selector',
                        options=[{'label': f'{d} cm', 'value': d} for d in self.results.depths[::10]],
                        value=[self.results.depths[i] for i in [10, 50, 90]],
                        multi=True
                    )
                ]),

                dcc.Tab(label='Mass Balance', children=[
                    dcc.Graph(id='mass-balance-plot', figure=self.plot_mass_balance())
                ])
            ])
        ])

        @app.callback(
            Output('profile-plot', 'figure'),
            Input('time-slider', 'value')
        )
        def update_profile(time_idx):
            t = self.results.times[time_idx]
            return self.plot_profile([t])

        @app.callback(
            Output('timeseries-plot', 'figure'),
            Input('depth-selector', 'value')
        )
        def update_timeseries(depths):
            return self.plot_timeseries(depths)

        return app
```

### 8.2 Comparison Plots

```python
class ComparisonVisualizer:
    """Visualize comparisons between runs"""

    def compare_scenarios(self, results_dict: dict, variable='h', time=-1):
        """
        Compare multiple scenarios

        Parameters
        ----------
        results_dict : dict
            Dictionary of {scenario_name: ModelResults}
        variable : str
            Variable to compare
        time : float or int
            Time to compare (or index if int)
        """
        fig = go.Figure()

        for name, results in results_dict.items():
            profile = results.get_profile(time, variable)
            depths = results.depths

            fig.add_trace(go.Scatter(
                x=profile,
                y=depths,
                mode='lines+markers',
                name=name
            ))

        fig.update_layout(
            title=f'Scenario Comparison: {variable} at t={time}',
            xaxis_title=variable,
            yaxis_title='Depth [cm]',
            yaxis=dict(autorange='reversed'),
            template='plotly_white'
        )

        return fig

    def compare_materials(self, materials_dict: dict):
        """
        Compare hydraulic property curves for different materials

        Parameters
        ----------
        materials_dict : dict
            Dictionary of {material_name: HydraulicModel}
        """
        h_range = np.logspace(-4, 3, 1000)  # -10000 to 0
        h_range = -h_range

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Water Retention', 'Hydraulic Conductivity')
        )

        for name, material in materials_dict.items():
            theta = material.water_content(h_range)
            K = material.conductivity(h_range)

            # Retention curve
            fig.add_trace(
                go.Scatter(x=-h_range, y=theta, name=name, legendgroup=name),
                row=1, col=1
            )

            # Conductivity function
            fig.add_trace(
                go.Scatter(x=-h_range, y=K, name=name,
                          legendgroup=name, showlegend=False),
                row=1, col=2
            )

        fig.update_xaxes(type='log', title_text='|h| [cm]', row=1, col=1)
        fig.update_xaxes(type='log', title_text='|h| [cm]', row=1, col=2)
        fig.update_yaxes(title_text='θ [-]', row=1, col=1)
        fig.update_yaxes(type='log', title_text='K [cm/day]', row=1, col=2)

        fig.update_layout(
            title='Soil Hydraulic Functions Comparison',
            template='plotly_white',
            height=500
        )

        return fig
```

## 9. Implementation Timeline

### Phase 1: Fortran Wrapper (Weeks 1-4)

**Week 1-2: Core Infrastructure**
- Set up project structure
- Implement input/output parsers
- Create basic data structures
- Write unit tests for I/O

**Week 3: Fortran Interface**
- Compile Fortran to shared library
- Create Python wrapper for Fortran execution
- Test with example cases

**Week 4: Basic Visualization**
- Implement profile plotting
- Implement time series plotting
- Create example notebooks
- Documentation

**Deliverable**: Working Python package that runs Fortran HYDRUS1D with Python I/O

### Phase 2: Hydraulic Model Abstraction (Weeks 5-8)

**Week 5: Base Architecture**
- Design HydraulicModel abstract class
- Implement van Genuchten model
- Implement Brooks-Corey model
- Unit tests for material models

**Week 6: Extended Models**
- Implement dual-porosity models
- Implement custom model interface
- Comparison visualization tools
- Integration with main model class

**Week 7-8: Integration & Testing**
- Connect to Fortran wrapper
- Validation against Fortran results
- Performance benchmarking
- Extended documentation

**Deliverable**: Modular hydraulic model system with exchangeable components

### Phase 3: Python Solver (Months 3-6)

**Month 3: Core Numerics**
- Implement Richards equation solver (basic)
- Tridiagonal matrix solver
- Time stepping algorithm
- Boundary condition handling

**Month 4: Optimization & Features**
- Numba optimization of hot loops
- Vectorization improvements
- Root water uptake implementation
- Advanced boundary conditions

**Month 5: Validation**
- Comprehensive testing against Fortran
- Benchmark problem suite
- Performance optimization
- Bug fixes

**Month 6: Polish & Release**
- Complete documentation
- Tutorial notebooks
- API refinement
- Package for PyPI

**Deliverable**: Production-ready pure Python HYDRUS1D implementation

### Phase 4: Advanced Features (Months 7+)

**Optional Extensions**:
- Solute transport module
- Heat transport module
- Parameter estimation tools
- GUI development
- Cloud deployment options
- Parallel execution for multiple scenarios

## 10. Testing Strategy

### 10.1 Test Categories

1. **Unit Tests** (pytest)
   - Individual functions
   - Hydraulic models
   - Boundary conditions
   - Numerical methods

2. **Integration Tests**
   - Full model runs
   - I/O workflows
   - Multi-component interactions

3. **Validation Tests**
   - Comparison with Fortran
   - Analytical solutions
   - Published benchmarks

4. **Performance Tests**
   - Execution time
   - Memory usage
   - Scaling behavior

### 10.2 Continuous Integration

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.8, 3.9, '3.10', 3.11]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -e .[dev]

    - name: Run unit tests
      run: |
        pytest tests/unit -v --cov=hydrus1dpy

    - name: Run integration tests
      run: |
        pytest tests/integration -v

    - name: Run validation tests
      run: |
        pytest tests/validation -v
```

### 10.3 Test Coverage Goals

- Unit tests: >90% coverage
- Integration tests: All major workflows
- Validation tests: 5-10 benchmark cases
- Performance tests: Baseline established

## 11. Documentation Plan

### 11.1 Documentation Structure

```
docs/
├── index.md
├── getting_started/
│   ├── installation.md
│   ├── quickstart.md
│   └── first_simulation.md
├── user_guide/
│   ├── model_setup.md
│   ├── hydraulic_models.md
│   ├── boundary_conditions.md
│   ├── running_simulations.md
│   └── visualization.md
├── examples/
│   ├── infiltration.ipynb
│   ├── evaporation.ipynb
│   ├── layered_soil.ipynb
│   └── parameter_sensitivity.ipynb
├── api_reference/
│   ├── core.md
│   ├── materials.md
│   ├── io.md
│   └── visualization.md
├── developer_guide/
│   ├── architecture.md
│   ├── contributing.md
│   └── custom_models.md
└── validation/
    ├── test_cases.md
    └── benchmarks.md
```

### 11.2 Documentation Tools

- **Sphinx** for API documentation
- **Jupyter Book** for tutorials
- **MkDocs** for user guide
- **Docstrings** following NumPy style

## 12. Performance Considerations

### 12.1 Optimization Strategies

1. **Numba JIT Compilation**
   - Compile hot loops
   - Use `@jit(nopython=True)`
   - Parallel execution with `prange`

2. **Vectorization**
   - NumPy operations instead of loops
   - Avoid Python-level iteration
   - Use broadcasting

3. **Memory Management**
   - Preallocate arrays
   - Avoid unnecessary copies
   - Use views instead of copies

4. **Caching**
   - Memoize expensive functions
   - Cache hydraulic property calculations
   - Reuse factorized matrices

### 12.2 Expected Performance

**Fortran Engine**: ~same as original (baseline)
**Python + Numba**: ~2-5x slower than Fortran
**Pure Python**: ~10-50x slower than Fortran

For typical problems (100 nodes, 1 year simulation):
- Fortran: ~1 second
- Python+Numba: ~2-5 seconds
- Pure Python: ~10-30 seconds

## 13. Deployment & Distribution

### 13.1 Package Distribution

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name='hydrus1dpy',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.20',
        'scipy>=1.7',
        'pandas>=1.3',
        'plotly>=5.0',
        'numba>=0.55',
        'xarray>=0.19',
    ],
    extras_require={
        'dev': ['pytest', 'pytest-cov', 'black', 'flake8', 'mypy'],
        'docs': ['sphinx', 'sphinx-rtd-theme', 'nbsphinx'],
        'fortran': ['numpy.f2py'],
    },
    entry_points={
        'console_scripts': [
            'hydrus1d=hydrus1dpy.cli:main',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='Python wrapper for HYDRUS1D hydrological model',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/hydrus1dpy',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
```

### 13.2 Installation Methods

```bash
# From PyPI (future)
pip install hydrus1dpy

# From source
git clone https://github.com/yourusername/hydrus1dpy
cd hydrus1dpy
pip install -e .

# With Fortran support
pip install hydrus1dpy[fortran]

# For development
pip install -e .[dev]
```

## 14. Example Usage

### 14.1 Quick Start Example

```python
import numpy as np
from hydrus1dpy import HYDRUS1D, ModelDomain, TimeControl
from hydrus1dpy.materials import VanGenuchten
from hydrus1dpy.boundary import FluxBC, PressureBC
from hydrus1dpy.visualization import HydrusVisualizer

# Define domain
domain = ModelDomain(
    nodes=101,
    depths=np.linspace(0, -100, 101),
    materials=np.ones(101, dtype=int)
)

# Define soil hydraulic properties
loam = VanGenuchten(
    theta_r=0.078,
    theta_s=0.43,
    alpha=0.036,
    n=1.56,
    Ks=24.96,
    l=0.5
)

# Boundary conditions
bc_top = FluxBC(flux=-5.0)  # 5 cm/day infiltration
bc_bottom = PressureBC(h=-100.0)  # Constant head

# Time control
time = TimeControl(
    t_max=10.0,  # 10 days
    dt_init=0.01,
    dt_min=0.0001,
    dt_max=1.0,
    print_times=np.linspace(0, 10, 21)
)

# Create and run model
model = HYDRUS1D(domain, {1: loam}, bc_top, bc_bottom, time)
model.set_initial_conditions(np.linspace(0, -100, 101))

results = model.run(engine='python')

# Visualize
viz = HydrusVisualizer(results)
fig = viz.plot_profile([0, 1, 5, 10], variable='theta')
fig.show()
```

### 14.2 Custom Hydraulic Model Example

```python
from hydrus1dpy.materials import CustomHydraulicModel

# Define custom functions
def custom_theta(h, theta_r, theta_s, a, b):
    if h >= 0:
        return theta_s
    else:
        return theta_r + (theta_s - theta_r) * np.exp(a * h**b)

def custom_K(h, Ks, c):
    return Ks * np.exp(c * h)

# Create custom model
my_model = CustomHydraulicModel(
    theta_r=0.05,
    theta_s=0.40,
    theta_func=custom_theta,
    K_func=custom_K,
    a=0.01,
    b=0.5,
    Ks=10.0,
    c=0.02
)

# Use in simulation
model = HYDRUS1D(domain, {1: my_model}, bc_top, bc_bottom, time)
```

## 15. Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Numerical instability in Python solver | Medium | High | Extensive testing, validation against Fortran |
| Performance issues | Medium | Medium | Numba optimization, profiling, benchmarking |
| Fortran compilation issues | High | Low | Provide pre-compiled binaries, fallback to subprocess |
| API design limitations | Low | High | Iterative design, user feedback, versioning |
| Scope creep | High | Medium | Phased approach, clear milestones |
| Maintenance burden | Medium | Medium | Good documentation, test coverage, community |

## 16. Success Criteria

1. **Functionality**:
   - Successfully run all Fortran test cases
   - Match Fortran results within acceptable tolerance
   - Support all major hydraulic models

2. **Performance**:
   - Python+Numba within 5x of Fortran speed
   - Handle problems with 1000+ nodes
   - Run typical simulations in <10 seconds

3. **Usability**:
   - Installation in <5 minutes
   - Run first simulation with <10 lines of code
   - Clear documentation and examples

4. **Quality**:
   - >90% test coverage
   - Pass all validation benchmarks
   - No major bugs in release

5. **Community**:
   - 10+ users within 6 months
   - 5+ GitHub stars
   - Active issue/PR engagement

## 17. Conclusion

This plan provides a comprehensive roadmap for developing a Python wrapper for HYDRUS1D with three implementation strategies:

1. **Short-term** (1 month): Fortran engine with Python I/O - immediate functionality
2. **Medium-term** (3 months): Hybrid approach with exchangeable hydraulic models
3. **Long-term** (6 months): Pure Python/Numba implementation

The modular architecture ensures that soil hydraulic models are easily exchangeable, supporting van Genuchten, Brooks-Corey, dual-porosity, and custom user-defined models. Comprehensive testing against the Fortran version and interactive Plotly visualizations ensure quality and usability.

The phased approach balances rapid delivery with long-term maintainability, allowing users to benefit from Python integration while maintaining the proven numerical stability of the original Fortran code.

## 18. Next Steps

1. **Immediate** (Week 1):
   - Set up Git repository
   - Create project structure
   - Begin input parser implementation

2. **Short-term** (Month 1):
   - Complete Phase 1 (Fortran wrapper)
   - Release v0.1.0 alpha
   - Gather user feedback

3. **Medium-term** (Months 2-3):
   - Implement hydraulic model abstraction
   - Validation and testing
   - Release v0.2.0 beta

4. **Long-term** (Months 4-6):
   - Python solver implementation
   - Performance optimization
   - Release v1.0.0

---

**Document Version**: 1.0
**Date**: 2025-11-09
**Author**: Claude (Anthropic)
