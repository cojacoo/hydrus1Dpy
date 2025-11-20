# Convergence Analysis Example

This example demonstrates how to analyze spatial and temporal convergence.

## Spatial Convergence

```python
import numpy as np
from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten

soil = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96)

# Test different grid resolutions
node_counts = [26, 51, 101, 201]
errors = []

for n_nodes in node_counts:
    model = HydrusModel(depth=100, n_nodes=n_nodes, material=soil)
    model.set_top_bc('flux', flux=5.0)
    model.set_bottom_bc('free_drainage')
    model.set_initial_conditions('hydrostatic', h_bottom=-200)

    results = model.run(t_end=1.0, dt_init=0.001, dt_max=0.01, verbose=False)

    mb = results['mass_balance']
    rel_error = abs(mb['error'][-1]) / abs(mb['flux_top'][-1]) * 100
    errors.append(rel_error)

    spacing = 100 / (n_nodes - 1)
    print(f"n={n_nodes:3d} (Δz={spacing:.2f} cm): error = {rel_error:.2f}%")

# Plot convergence
import matplotlib.pyplot as plt

plt.figure()
plt.plot(node_counts, errors, 'o-')
plt.xlabel('Number of nodes')
plt.ylabel('Mass balance error [%]')
plt.title('Spatial Convergence')
plt.grid(True)
plt.show()
```

## Temporal Convergence

```python
# Test different time step sizes
dt_max_values = [0.1, 0.01, 0.001]
errors = []

model = HydrusModel(depth=100, n_nodes=101, material=soil)
model.set_top_bc('flux', flux=5.0)
model.set_bottom_bc('free_drainage')
model.set_initial_conditions('hydrostatic', h_bottom=-200)

for dt_max in dt_max_values:
    results = model.run(t_end=1.0, dt_init=dt_max/10, dt_max=dt_max, verbose=False)

    mb = results['mass_balance']
    rel_error = abs(mb['error'][-1]) / abs(mb['flux_top'][-1]) * 100
    errors.append(rel_error)

    print(f"dt_max={dt_max:.3f}: error = {rel_error:.2f}%")
```

## Recommendations

Based on convergence analysis:

- **Infiltration into dry soil**:
  - Grid spacing: ≤ 1 cm
  - dt_max: ≤ 0.01 days
  - Expected error: < 3%

- **Drainage from saturation**:
  - Grid spacing: ≤ 2 cm
  - dt_max: ≤ 0.1 days
  - Expected error: < 1%

## Source

See `phase3/examples/convergence_test.py` for complete analysis.
