# Simple Infiltration Example

This example demonstrates basic infiltration simulation.

## Overview

Simulates constant infiltration into an initially dry soil profile with:
- Loam soil (van Genuchten parameters)
- Constant 5 cm/day infiltration rate
- Free drainage at bottom
- 100 cm soil column

## Full Code

```python
import numpy as np
from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten

# Create van Genuchten loam soil
vg_loam = VanGenuchten(
    theta_r=0.078,
    theta_s=0.430,
    alpha=0.036,
    n=1.56,
    Ks=24.96,
    l=0.5
)

# Create model
model = HydrusModel(
    depth=100.0,
    n_nodes=101,  # 1 cm spacing
    material=vg_loam
)

# Set boundary conditions
model.set_top_bc('flux', flux=5.0)  # High infiltration rate
model.set_bottom_bc('free_drainage')

# Initial conditions: relatively dry
model.set_initial_conditions('hydrostatic', h_bottom=-200)

# Run simulation
results = model.run(
    t_end=1.0,
    dt_init=0.0005,
    dt_min=1e-6,
    dt_max=0.01,
    verbose=True
)

# Print summary
mb = results['mass_balance']
rel_error = abs(mb['error'][-1]) / abs(mb['flux_top'][-1]) * 100

print(f"\nResults:")
print(f"  Mass balance error: {rel_error:.2f}%")
print(f"  Water infiltrated: {mb['flux_top'][-1]:.2f} cm")
print(f"  Water drained: {-mb['flux_bottom'][-1]:.2f} cm")
print(f"  Storage change: {mb['storage'][-1] - mb['storage'][0]:.2f} cm")
```

## Visualization

```python
# Convert to xarray
ds = model.to_xarray()

# Spatiotemporal heatmap
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Water content
ds.theta.plot(ax=axes[0], x='time', y='depth', cmap='Blues')
axes[0].invert_yaxis()
axes[0].set_title('Water Content Dynamics')

# Pressure head
ds.h.plot(ax=axes[1], x='time', y='depth', cmap='RdBu_r')
axes[1].invert_yaxis()
axes[1].set_title('Pressure Head Dynamics')

plt.tight_layout()
plt.show()
```

## Results

The simulation shows:
- Wetting front propagating downward
- Surface approaching saturation
- Bottom boundary draining
- Mass balance error < 3%

## Source

See `phase3/examples/simple_infiltration.py` for the complete script.
