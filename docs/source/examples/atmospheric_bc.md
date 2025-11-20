# Atmospheric Boundary Condition Example

This example demonstrates the enhanced atmospheric boundary condition with Penman-Monteith ET.

## Scenario 1: Simple ET with Rainfall

```python
from hydrus1dpy import HydrusModel, EnhancedAtmosphericBC
from hydrus1dpy.materials import VanGenuchten

# Setup model
soil = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96)
model = HydrusModel(depth=100, n_nodes=51, material=soil)

# Rainfall events
def precip(t):
    if t % 7 < 0.5:  # Weekly rain
        return 20.0  # mm/day
    return 0.0

# Enhanced atmospheric BC
bc = EnhancedAtmosphericBC(
    'top',
    precipitation=precip,
    et_method='simple',
    et_default=4.0  # mm/day
)

model.bc_top = bc
model.set_bottom_bc('free_drainage')
model.set_initial_conditions('hydrostatic', h_bottom=-200)

# Run
results = model.run(t_end=30, dt_init=0.001, dt_max=0.1)

# Check diagnostics
diag = bc.get_diagnostics()
print(f"ET stage: {diag['et_stage']}")
print(f"Runoff: {diag['cumulative_runoff']:.2f} cm")
```

## Scenario 2: Penman-Monteith ET

```python
from hydrus1dpy import WeatherData
import numpy as np

def get_weather(t):
    day = t % 365
    return WeatherData(
        time=t,
        temperature=15 + 10*np.sin(2*np.pi*day/365),
        relative_humidity=60,
        wind_speed=2.0,
        solar_radiation=15 + 10*np.sin(2*np.pi*day/365)
    )

bc = EnhancedAtmosphericBC(
    'top',
    precipitation=0.0,
    et_method='penman_monteith',
    weather_func=get_weather,
    latitude=52.0,
    elevation=100.0
)

model.bc_top = bc
results = model.run(t_end=60, dt_init=0.001, dt_max=0.1)
```

## Source

See `phase3/examples/demo_atmospheric_bc.py` for complete demonstration.
