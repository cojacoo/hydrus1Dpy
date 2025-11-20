# xarray Usage Example

This example shows how to use xarray for modern data handling and visualization.

## Basic Conversion

```python
from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten

# Run simulation
soil = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96)
model = HydrusModel(depth=100, n_nodes=51, material=soil)
model.set_top_bc('flux', flux=0.5)
model.set_bottom_bc('free_drainage')
model.set_initial_conditions('hydrostatic', h_bottom=-200)

results = model.run(t_end=10, dt_init=0.01, dt_max=0.1)

# Convert to xarray
ds = model.to_xarray()
print(ds)
```

## Data Selection

```python
# Select by coordinate value
theta_50cm = ds.theta.sel(depth=-50, method='nearest')

# Slice by range
shallow = ds.sel(depth=slice(-30, 0))

# Time slicing
early = ds.sel(time=slice(0, 5.0))
```

## Dimension-Aware Operations

```python
# Time-averaged profile
theta_tavg = ds.theta.mean(dim='time')

# Depth-averaged time series
theta_zavg = ds.theta.mean(dim='depth')

# Overall statistics
print(f"Mean θ: {ds.theta.mean().values:.3f}")
print(f"Std θ: {ds.theta.std().values:.3f}")
```

## Visualization

```python
import matplotlib.pyplot as plt

# Heatmap
ds.theta.plot(x='time', y='depth', cmap='Blues')
plt.gca().invert_yaxis()
plt.show()

# Profile
ds.theta.isel(time=-1).plot()

# Time series
ds.theta.sel(depth=-50, method='nearest').plot()
```

## Save/Load

```python
# Save to NetCDF
ds.to_netcdf('results.nc')

# Load
import xarray as xr
ds_loaded = xr.open_dataset('results.nc')
```

## Source

See `phase3/examples/demo_xarray.py` for complete demonstration.
