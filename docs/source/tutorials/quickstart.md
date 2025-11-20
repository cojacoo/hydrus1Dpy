# Quick Start Guide

This guide will get you running your first HYDRUS1DPy simulation in minutes.

## Basic Workflow

1. Create soil hydraulic model
2. Setup domain and boundary conditions
3. Run simulation
4. Analyze results

## Simple Infiltration Example

```python
from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten

# Step 1: Create soil model (loam soil)
soil = VanGenuchten(
    theta_r=0.078,  # Residual water content
    theta_s=0.430,  # Saturated water content
    alpha=0.036,    # Scale parameter [1/cm]
    n=1.56,         # Shape parameter
    Ks=24.96,       # Saturated conductivity [cm/day]
    l=0.5           # Pore connectivity
)

# Step 2: Create model with 100 cm profile
model = HydrusModel(
    depth=100.0,    # cm
    n_nodes=51,     # Discretization nodes
    material=soil
)

# Step 3: Set boundary conditions
model.set_top_bc('flux', flux=0.5)  # 0.5 cm/day infiltration
model.set_bottom_bc('free_drainage')

# Step 4: Set initial conditions
model.set_initial_conditions('hydrostatic', h_bottom=-200)

# Step 5: Run simulation
results = model.run(
    t_end=10.0,     # Days
    dt_init=0.01,   # Initial time step
    dt_max=0.1      # Maximum time step
)

# Step 6: Print summary
print(f"Simulation completed:")
print(f"  Time steps: {results['statistics']['total_steps']}")
print(f"  Final storage: {results['mass_balance']['storage'][-1]:.2f} cm")
```

## Understanding the Results

The `results` dictionary contains:

```python
{
    'times': array of time points [days],
    'h': pressure head [time, nodes] [cm],
    'theta': water content [time, nodes] [-],
    'mass_balance': {
        'flux_top': cumulative top flux [cm],
        'flux_bottom': cumulative bottom flux [cm],
        'storage': water storage [cm],
        'error': mass balance error [cm]
    },
    'statistics': {
        'total_steps': number of time steps,
        'rejected_steps': failed time steps,
        'avg_iterations': average Picard iterations
    }
}
```

## Basic Visualization

### Using xarray (Recommended)

```python
# Convert to xarray Dataset
ds = model.to_xarray()

# Spatiotemporal heatmap
ds.theta.plot(x='time', y='depth', cmap='Blues')

# Profile at final time
ds.theta.isel(time=-1).plot()

# Time series at 50 cm depth
ds.theta.sel(depth=-50, method='nearest').plot()
```

### Using matplotlib

```python
import matplotlib.pyplot as plt

# Plot final water content profile
plt.figure(figsize=(6, 8))
plt.plot(results['theta'][-1], model.depths)
plt.xlabel('Water content θ [-]')
plt.ylabel('Depth [cm]')
plt.title('Final Water Content Profile')
plt.grid(True)
plt.show()

# Plot time series at surface
plt.figure(figsize=(10, 4))
plt.plot(results['times'], results['theta'][:, 0])
plt.xlabel('Time [days]')
plt.ylabel('Surface water content [-]')
plt.title('Surface Water Content Evolution')
plt.grid(True)
plt.show()
```

## Common Scenarios

### Rainfall Event

```python
# Time-varying precipitation
def rainfall(t):
    if 2 <= t <= 3:  # Rain from day 2 to 3
        return 5.0   # 5 cm/day
    return 0.0

model.set_top_bc('flux', flux=rainfall)
```

### Evapotranspiration

```python
from hydrus1dpy import EnhancedAtmosphericBC

# Simple ET with rainfall events
def precip(t):
    if t % 7 < 0.5:  # Weekly rain
        return 20.0  # mm/day
    return 0.0

bc = EnhancedAtmosphericBC(
    'top',
    precipitation=precip,
    et_method='simple',
    et_default=4.0  # mm/day
)

model.bc_top = bc
```

### Layered Soil

```python
from hydrus1dpy.materials import VanGenuchten

# Create two soil types
sand = VanGenuchten(0.045, 0.430, 0.145, 2.68, 712.8)
clay = VanGenuchten(0.068, 0.380, 0.008, 1.09, 4.8)

# Assign to layers
material_dict = {
    (0, -50): sand,    # Top 50 cm: sand
    (-50, -100): clay  # Bottom 50 cm: clay
}

model = HydrusModel(
    depth=100.0,
    n_nodes=101,
    material=material_dict
)
```

## Next Steps

- Learn about [Atmospheric Boundary Conditions](atmospheric_bc.md)
- Explore [Visualization Options](visualization.md)
- Read [Discretization Guide](../guides/discretization.md)
- See more [Examples](../examples/simple_infiltration.md)
