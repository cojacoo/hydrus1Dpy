# HYDRUS1D Phase 3: Visualization and Data Handling

This document describes the modern data handling and visualization features in Phase 3.

## New Features

### 1. xarray Output Format

Convert simulation results to xarray Datasets for modern, labeled data handling:

```python
from hydrus1dpy import HydrusModel

# Run simulation
model = HydrusModel(...)
results = model.run(...)

# Convert to xarray
ds = model.to_xarray()

# Easy coordinate-based selection (no index calculations!)
theta_at_50cm = ds.theta.sel(depth=-50, method='nearest')
final_profile = ds.theta.isel(time=-1)

# Dimension-aware operations
time_averaged = ds.theta.mean(dim='time')
depth_averaged = ds.theta.mean(dim='depth')

# Save to standard NetCDF format
ds.to_netcdf('results.nc')
```

### 2. Spatiotemporal Visualization

The demo notebook (`demo_infiltration.ipynb`) includes advanced visualizations:

- **Heatmaps**: State variables over time and depth
- **Profile snapshots**: Vertical profiles at multiple times
- **Time series**: Evolution at specific depths
- **Mass balance**: Conservation verification

## Installation

### Minimal (for Python scripts only)

```bash
pip install numpy scipy numba pandas
```

### With xarray support

```bash
pip install numpy scipy numba pandas xarray netcdf4
```

### Full (including Jupyter notebook)

```bash
cd phase3
pip install -r requirements.txt
```

## Usage Examples

### Example 1: Quick Demo (xarray features)

```bash
cd phase3/examples
python demo_xarray.py
```

This script demonstrates:
- Converting results to xarray Dataset
- Coordinate-based selection
- Dimension-aware operations
- Saving/loading NetCDF files
- Comparison with dict-based approach

**No matplotlib required** - just tests xarray functionality.

### Example 2: Interactive Notebook (full visualization)

```bash
cd phase3
jupyter notebook demo_infiltration.ipynb
```

This notebook includes:
- Spatiotemporal heatmaps (time × depth)
- Profile plots at multiple times
- Time series at multiple depths
- Mass balance analysis
- xarray data manipulation examples

### Example 3: Python Script (without Jupyter)

You can also run the examples as Python scripts:

```python
import numpy as np
from pathlib import Path
import sys

# Add paths
phase3_path = Path('phase3').absolute()
phase2_path = Path('phase2').absolute()
sys.path.insert(0, str(phase2_path))
sys.path.insert(0, str(phase3_path))

from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten

# Setup and run
vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96)
model = HydrusModel(depth=100.0, n_nodes=101, material=vg)
model.set_top_bc('flux', flux=5.0)
model.set_bottom_bc('free_drainage')
model.set_initial_conditions('hydrostatic', h_bottom=-200)

results = model.run(t_end=1.0, dt_init=0.0005, dt_max=0.01)

# Convert to xarray
ds = model.to_xarray()

# Analyze
print(f"Final water storage: {ds.storage.values[-1]:.2f} cm")
print(f"Mass balance error: {ds.mass_balance_error.values[-1]:.4e} cm")
```

## Benefits of xarray

### 1. **Labeled Dimensions**
No more index confusion - select by coordinate value:

```python
# Old way (error-prone)
idx = np.argmin(np.abs(depths - (-50)))
theta_50 = results['theta'][:, idx]

# New way (clear and safe)
theta_50 = ds.theta.sel(depth=-50, method='nearest')
```

### 2. **Self-Documenting**
Coordinates, units, and metadata are preserved:

```python
>>> ds.theta
<xarray.DataArray 'theta' (time: 156, depth: 101)>
Coordinates:
  * time     (time) float64 0.0 0.0005 0.001 ... 0.998 0.999 1.0
  * depth    (depth) float64 0.0 -1.0 -2.0 ... -98.0 -99.0 -100.0
Attributes:
    units:        -
    long_name:    Water content
    description:  Volumetric water content
```

### 3. **Easy Slicing**
Select ranges by coordinate values:

```python
# Get data for top 30 cm
shallow = ds.sel(depth=slice(-30, 0))

# Get data for first 6 hours
early = ds.sel(time=slice(0, 0.25))

# Combine selections
shallow_early = ds.sel(depth=slice(-30, 0), time=slice(0, 0.25))
```

### 4. **Dimension-Aware Operations**
Statistical operations understand dimensions:

```python
# Time-averaged profile
ds.theta.mean(dim='time')

# Depth-averaged time series
ds.theta.mean(dim='depth')

# Overall spatial-temporal mean
ds.theta.mean()
```

### 5. **Built-in Plotting**
Quick visualization with proper labels:

```python
# Requires matplotlib
ds.theta.isel(time=-1).plot()  # Final profile
ds.theta.sel(depth=-50, method='nearest').plot()  # Time series at 50 cm
ds.theta.plot(x='time', y='depth')  # Heatmap
```

### 6. **Standard File Format**
NetCDF is widely used in earth sciences:

```python
# Save
ds.to_netcdf('results.nc')

# Load
ds_loaded = xr.open_dataset('results.nc')

# Works with other tools: NCO, CDO, Panoply, etc.
```

## Visualization Gallery

### Spatiotemporal Heatmap

Shows wetting front propagation:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
ds.theta.plot(
    ax=ax,
    x='time',
    y='depth',
    cmap='Blues',
    cbar_kwargs={'label': 'Water content θ [-]'}
)
ax.invert_yaxis()  # Surface at top
ax.set_title('Infiltration Dynamics')
plt.show()
```

### Profile Snapshots

Compare different times:

```python
times_to_plot = [0.0, 0.25, 0.5, 0.75, 1.0]

fig, ax = plt.subplots()
for t in times_to_plot:
    ds.theta.sel(time=t, method='nearest').plot(
        y='depth',
        label=f't = {t} d',
        ax=ax
    )
ax.invert_yaxis()
ax.legend()
ax.set_title('Water Content Profiles')
plt.show()
```

### Time Series

Monitor specific depths:

```python
depths_to_plot = [0, -25, -50, -75, -100]

fig, ax = plt.subplots()
for z in depths_to_plot:
    ds.theta.sel(depth=z, method='nearest').plot(
        label=f'z = {z} cm',
        ax=ax
    )
ax.legend()
ax.set_title('Water Content Time Series')
plt.show()
```

## Data Structure

### xarray Dataset Contents

```
Dimensions:
  - time: (n_times,) Simulation time points [days]
  - depth: (n_nodes,) Depth coordinates [cm, negative downward]

Data Variables:
  - h: (time, depth) Pressure head [cm]
  - theta: (time, depth) Water content [-]
  - flux_top: (time,) Cumulative flux at top [cm]
  - flux_bottom: (time,) Cumulative flux at bottom [cm]
  - storage: (time,) Water storage in profile [cm]
  - mass_balance_error: (time,) Mass balance error [cm]

Attributes:
  - title: Description
  - depth_total: Total profile depth
  - n_nodes: Number of nodes
  - top_bc, bottom_bc: Boundary condition types
  - total_steps, rejected_steps: Solver statistics
  - avg_iterations: Average Picard iterations
```

### Comparison: Dict vs. xarray

| Feature | Dict (old) | xarray (new) |
|---------|-----------|--------------|
| **Selection** | `results['h'][:, 50]` | `ds.h.sel(depth=-50)` |
| **Coordinates** | Manual index calculation | Automatic matching |
| **Slicing** | `results['h'][10:20, 30:40]` | `ds.h.sel(time=slice(0.1,0.2), depth=slice(-30,-40))` |
| **Labels** | None | Automatic in plots |
| **Metadata** | External | Embedded |
| **File I/O** | pickle (fragile) | NetCDF (standard) |
| **Operations** | Manual axis specification | Dimension names |

## Troubleshooting

### ImportError: No module named 'xarray'

```bash
pip install xarray netcdf4
```

### Jupyter notebook won't start

```bash
pip install jupyter ipykernel
```

### numba compatibility issues

If you encounter numba version conflicts:

1. Check numba version: `pip show numba`
2. Update numba: `pip install --upgrade numba`
3. If issues persist, create a fresh environment:

```bash
conda create -n hydrus python=3.9
conda activate hydrus
cd phase3
pip install -r requirements.txt
```

### Matplotlib style warning

If you see warnings about 'seaborn-v0_8-darkgrid' style:

```python
# In notebook, replace:
plt.style.use('seaborn-v0_8-darkgrid')

# With:
plt.style.use('seaborn-v0_8-whitegrid')
# or
plt.style.use('default')
```

## Files

- `demo_infiltration.ipynb` - Interactive notebook with full visualizations
- `examples/demo_xarray.py` - Script demonstrating xarray features (no plotting)
- `examples/simple_infiltration.py` - Basic example with text output
- `examples/convergence_test.py` - Discretization analysis
- `requirements.txt` - All dependencies
- `DISCRETIZATION_GUIDE.md` - Guidelines for choosing grid and time steps

## Next Steps

1. Try the quick demo: `python examples/demo_xarray.py`
2. Explore the notebook: `jupyter notebook demo_infiltration.ipynb`
3. Adapt examples to your soil/boundary conditions
4. See `DISCRETIZATION_GUIDE.md` for accuracy guidelines

## References

- xarray documentation: https://docs.xarray.dev/
- NetCDF format: https://www.unidata.ucar.edu/software/netcdf/
- van Genuchten (1980): https://doi.org/10.2136/sssaj1980.03615995004400050002x
- Carsel & Parrish (1988): https://doi.org/10.1029/WR024i005p00755
