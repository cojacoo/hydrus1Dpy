# HYDRUS1D Python Wrapper - Phase 1

**Status**: ✅ Complete
**Version**: 0.1.0-phase1

## Overview

Phase 1 provides a Python interface to the HYDRUS1D Fortran model with:
- ✅ Complete Python I/O for reading/writing HYDRUS1D files
- ✅ Data structures with validation
- ✅ Fortran engine wrapper
- ✅ Interactive Plotly visualizations
- ✅ Comprehensive test suite

## Features

### 1. Data Structures (`hydrus1dpy.io.data_structures`)

Scientifically validated dataclasses for all model components:

```python
from hydrus1dpy import (
    ModelDomain, MaterialProperties, BoundaryCondition,
    TimeControl, InitialConditions, ModelConfiguration
)
```

- **ModelDomain**: Spatial discretization with validation
- **MaterialProperties**: Soil hydraulic parameters (van Genuchten, Brooks-Corey, etc.)
- **BoundaryCondition**: Top/bottom boundary conditions
- **TimeControl**: Time stepping parameters
- **ModelConfiguration**: Complete model setup

### 2. Input/Output (`hydrus1dpy.io`)

**Input Parser** - Read existing HYDRUS1D files:
```python
from hydrus1dpy.io import InputParser

parser = InputParser('./my_project')
config = parser.parse_all()  # Reads Selector.in, Profile.dat, ATMOSPH.IN
```

**Input Writer** - Create new HYDRUS1D files from Python:
```python
from hydrus1dpy.io import InputWriter

writer = InputWriter(config, './output_dir')
writer.write_all()  # Writes all input files
```

**Output Parser** - Read results:
```python
from hydrus1dpy.io import OutputParser

parser = OutputParser('./project_dir')
results = parser.parse_all()  # Reads T_LEVEL.OUT, OBS_NODE.OUT, NOD_INF.OUT
```

### 3. Fortran Interface (`hydrus1dpy.utils.fortran_runner`)

Run HYDRUS1D Fortran engine from Python:

```python
from hydrus1dpy.utils import FortranRunner

runner = FortranRunner(config, hydrus_exe='./hydrus1d')
results = runner.run()
```

### 4. Visualization (`hydrus1dpy.visualization`)

Interactive Plotly visualizations:

```python
from hydrus1dpy.visualization import HydrusVisualizer

viz = HydrusVisualizer(results)

# Profile plots
fig = viz.plot_profile([0, 1, 5, 10], variable='theta')
fig.show()

# Time series
fig = viz.plot_timeseries(nodes=[25, 50, 75], variable='h')
fig.show()

# Mass balance
fig = viz.plot_mass_balance()
fig.show()

# Animated profiles
fig = viz.plot_animation(variable='theta')
fig.show()
```

### 5. Helper Functions (`hydrus1dpy.utils.helpers`)

Quick configuration creation:

```python
from hydrus1dpy.utils.helpers import (
    create_example_configuration,
    create_layered_soil,
    get_soil_parameters
)

# Simple configuration
config = create_example_configuration(
    profile_depth=100.0,
    n_nodes=101,
    simulation_time=10.0,
    soil_type='loam'
)

# Layered soil
domain, materials = create_layered_soil(
    layer_depths=[0, 30, 60, 100],
    soil_types=['loam', 'sandy_loam', 'sand']
)

# Soil parameters from Carsel & Parrish (1988)
params = get_soil_parameters('loam')
```

## Installation

### Requirements

```bash
pip install numpy pandas plotly
```

### Optional: Fortran Compiler

To run the Fortran engine, you need `gfortran`:

```bash
# Ubuntu/Debian
sudo apt-get install gfortran

# macOS
brew install gcc

# Windows
# Download MinGW-w64 from https://mingw-w64.org
```

### Install Package

```bash
cd phase1
pip install -e .
```

## Quick Start

### Example 1: Create and Write Input Files

```python
import numpy as np
from hydrus1dpy import *

# Create domain
n_nodes = 101
depths = np.linspace(0, -100, n_nodes)
domain = ModelDomain(
    n_nodes=n_nodes,
    depths=depths,
    materials=np.ones(n_nodes, dtype=int)
)

# Create materials (Loam soil)
materials = {
    1: MaterialProperties(
        material_id=1,
        theta_r=0.078,
        theta_s=0.430,
        alpha=0.036,
        n=1.56,
        Ks=24.96
    )
}

# Boundary conditions
bc_top = BoundaryCondition.constant_flux(-5.0)  # Infiltration
bc_bottom = BoundaryCondition.free_drainage()

# Time control
time_control = TimeControl(
    t_max=10.0,
    dt_init=0.01,
    dt_min=0.0001,
    dt_max=0.5,
    print_times=np.linspace(0, 10, 21)
)

# Initial conditions
initial_conditions = InitialConditions(
    h_init=depths - depths[0]
)

# Complete configuration
config = ModelConfiguration(
    project_name='my_simulation',
    units=Units(length='cm', time='days'),
    domain=domain,
    materials=materials,
    bc_top=bc_top,
    bc_bottom=bc_bottom,
    time_control=time_control,
    initial_conditions=initial_conditions
)

# Write input files
from hydrus1dpy.io import InputWriter
writer = InputWriter(config, './my_project')
writer.write_all()
```

### Example 2: Run Simulation (with Fortran)

```python
from hydrus1dpy.utils import FortranRunner

# Run simulation
runner = FortranRunner(config, hydrus_exe='./hydrus1d')
results = runner.run()

# Visualize results
from hydrus1dpy.visualization import HydrusVisualizer
viz = HydrusVisualizer(results)

fig = viz.plot_profile([0, 2, 5, 10], variable='theta')
fig.show()
```

### Example 3: Read Existing Project

```python
from hydrus1dpy.io import InputParser, OutputParser
from hydrus1dpy.visualization import HydrusVisualizer

# Read configuration
parser = InputParser('./existing_project')
config = parser.parse_all()

# Read results
out_parser = OutputParser('./existing_project')
results = out_parser.parse_all()

# Visualize
viz = HydrusVisualizer(results)
fig = viz.create_dashboard()
fig.show()
```

## Running Tests

```bash
cd phase1
pytest tests/ -v
```

## File Format Reference

### Input Files

**Selector.in** - Main control file
- Units (length, time, mass)
- Process flags (water, solute, heat)
- Numerical parameters (iterations, tolerances)
- Boundary condition types
- Material and layer information

**Profile.dat** - Domain and initial conditions
- Node coordinates
- Initial pressure heads
- Material assignments
- Material hydraulic properties

**ATMOSPH.IN** - Time-variable boundary conditions (optional)
- Time series of precipitation, evaporation, etc.

### Output Files

**T_LEVEL.OUT** - Time-level mass balance
**OBS_NODE.OUT** - Time series at observation nodes
**NOD_INF.OUT** - Complete profiles at print times
**BALANCE.OUT** - Detailed mass balance

## Soil Parameters

Built-in database from Carsel & Parrish (1988):

| Soil Type | θr | θs | α [1/cm] | n | Ks [cm/day] |
|-----------|----|----|----------|---|-------------|
| Sand | 0.045 | 0.430 | 0.145 | 2.68 | 712.8 |
| Loamy Sand | 0.057 | 0.410 | 0.124 | 2.28 | 350.2 |
| Sandy Loam | 0.065 | 0.410 | 0.075 | 1.89 | 106.1 |
| Loam | 0.078 | 0.430 | 0.036 | 1.56 | 24.96 |
| Silt | 0.034 | 0.460 | 0.016 | 1.37 | 6.0 |
| Silt Loam | 0.067 | 0.450 | 0.020 | 1.41 | 10.8 |
| Sandy Clay Loam | 0.100 | 0.390 | 0.059 | 1.48 | 31.44 |
| Clay Loam | 0.095 | 0.410 | 0.019 | 1.31 | 6.24 |
| Silty Clay Loam | 0.089 | 0.430 | 0.010 | 1.23 | 1.68 |
| Sandy Clay | 0.100 | 0.380 | 0.027 | 1.23 | 2.88 |
| Silty Clay | 0.070 | 0.360 | 0.005 | 1.09 | 0.48 |
| Clay | 0.068 | 0.380 | 0.008 | 1.09 | 4.8 |

## Scientific Rigor

All implementations are based on:

1. **van Genuchten (1980)** - Soil water retention function
2. **Mualem (1976)** - Hydraulic conductivity function
3. **Carsel & Parrish (1988)** - Soil hydraulic parameters
4. **HYDRUS1D v4.08** - Fortran code validation

Input/output parsers exactly match Fortran file formats:
- `INPUT.FOR` subroutines: `BasInf`, `NodInf`, `MatIn`
- `OUTPUT.FOR` subroutines: `TLInf`, `ObsNod`, `NodOut`

## Validation

Phase 1 has been validated by:
- ✅ Round-trip testing (write → read → write produces identical files)
- ✅ Unit tests for all data structures
- ✅ Comparison with existing HYDRUS1D projects
- ✅ Parameter validation against physical constraints

## Limitations

Phase 1 limitations (addressed in Phases 2-3):
- Requires compiled Fortran executable to run simulations
- No direct access to hydraulic functions from Python
- Cannot modify soil hydraulic models
- Limited to models supported by Fortran code

## Next Steps

**Phase 2** (in progress):
- Hydraulic model abstraction
- Pure Python implementation of van Genuchten, Brooks-Corey
- Custom material models
- Direct calculation without Fortran

**Phase 3** (planned):
- Complete Python/Numba Richards equation solver
- Performance optimization
- Extended validation suite

## Examples

See `examples/` directory:
- `example_basic_usage.py` - Complete workflow
- More examples coming in Phase 2/3

## References

1. van Genuchten, M. Th. (1980). A closed-form equation for predicting the hydraulic conductivity of unsaturated soils. Soil Sci. Soc. Am. J., 44(5), 892-898.

2. Mualem, Y. (1976). A new model for predicting the hydraulic conductivity of unsaturated porous media. Water Resources Research, 12(3), 513-522.

3. Carsel, R. F., & Parrish, R. S. (1988). Developing joint probability distributions of soil water retention characteristics. Water Resources Research, 24(5), 755-769.

4. Šimůnek, J., van Genuchten, M. Th., & Šejna, M. (2008). Development and applications of the HYDRUS and STANMOD software packages. Vadose Zone Journal, 7(2), 587-600.

## License

MIT License (to be confirmed with repository owner)

## Contact

For issues and questions, please use the GitHub issue tracker.
