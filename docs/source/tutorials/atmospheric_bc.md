# Enhanced Atmospheric Boundary Conditions

This document describes the enhanced atmospheric boundary condition features in HYDRUS1D Phase 3.

## Overview

The `EnhancedAtmosphericBC` class provides realistic simulation of atmospheric interactions with the soil surface:

1. **Evapotranspiration (ET)**: Penman-Monteith or simple constant ET
2. **Stage 1/2 Evaporation**: Automatic transition based on surface dryness (pF 4.5)
3. **Infiltration**: Modeled as thin water film with small positive head
4. **Surface Runoff**: Tracks excess ponding beyond maximum depth

## Key Features

### 1. Penman-Monteith ET Calculation

FAO-56 Penman-Monteith reference evapotranspiration based on weather data:

```python
from hydrus1dpy.processes.evapotranspiration import WeatherData

# Define weather conditions
def get_weather(t):
    return WeatherData(
        time=t,
        temperature=20.0,        # °C
        relative_humidity=60.0,  # %
        wind_speed=2.0,          # m/s at 2m height
        solar_radiation=15.0     # MJ/m²/day
    )

# Create BC with Penman-Monteith ET
from hydrus1dpy.processes.boundary_conditions import EnhancedAtmosphericBC

bc = EnhancedAtmosphericBC(
    'top',
    et_method='penman_monteith',
    weather_func=get_weather,
    latitude=52.0,  # degrees
    elevation=100.0 # meters
)
```

**Benefits**:
- Physically-based ET estimation
- Accounts for temperature, humidity, wind, radiation
- Standard method used worldwide (FAO-56)
- Automatic atmospheric pressure correction for elevation

### 2. Simple ET (Default Fallback)

When weather data is not available, use constant reference ET:

```python
bc = EnhancedAtmosphericBC(
    'top',
    et_method='simple',
    et_default=4.0  # mm/day
)
```

**Default**: 4 mm/day (typical temperate climate)

### 3. Stage 1/2 Evaporation

Evaporation occurs in two stages:

#### Stage 1: Potential Evaporation
- **Condition**: Surface pressure head h > h_threshold (pF < 4.5)
- **Behavior**: Full potential ET applied as flux boundary condition
- **Control**: Atmosphere-controlled (energy-limited)

#### Stage 2: Soil-Limited Evaporation
- **Condition**: Surface pressure head h < h_threshold (pF > 4.5)
- **Behavior**: Switches to head BC at h = h_threshold
- **Control**: Soil-controlled (hydraulic conductivity limits flux)
- **Effect**: Actual ET < potential ET

**pF 4.5 Threshold**:
- pF = log₁₀(|h|) where h is in cm
- pF 4.5 corresponds to h = -31,623 cm
- Approximately wilting point (plants cannot extract water)
- Surface becomes too dry for potential evaporation

```python
# Use default pF 4.5
bc = EnhancedAtmosphericBC('top', h_stage2=None)

# Or customize threshold
bc = EnhancedAtmosphericBC('top', h_stage2=-15849)  # pF 4.2 (wilting point)
```

### 4. Infiltration with Ponding

Instead of prescribing infiltration flux, water is applied as a thin film:

```python
bc = EnhancedAtmosphericBC(
    'top',
    precipitation=10.0,  # mm/day
    h_ponding=0.05       # cm (0.5 mm water film)
)
```

**How it works**:
1. When precipitation > ET, infiltration occurs
2. Surface boundary switches to head BC with h = h_ponding (slightly positive)
3. Richards equation calculates actual infiltration rate
4. If soil cannot accept water fast enough, ponding increases
5. When ponding exceeds maximum, excess becomes runoff

**Benefits**:
- Physically realistic (water ponds before infiltrating)
- Automatically accounts for infiltration capacity
- Richards equation determines flux based on soil properties
- No need to know infiltration rate in advance

**Comparison**:

| Approach | Old (Flux BC) | New (Ponding BC) |
|----------|---------------|------------------|
| **Input** | Prescribe flux | Prescribe water availability |
| **Physics** | Force water in | Let Richards eq. determine flux |
| **Capacity** | Ignored | Automatically handled |
| **Ponding** | Not represented | Realistic (small positive h) |
| **Realism** | Low | High |

### 5. Surface Runoff

When ponding depth exceeds maximum, excess water becomes runoff:

```python
bc = EnhancedAtmosphericBC(
    'top',
    precipitation=50.0,   # Heavy rain
    ponding_max=5.0       # Max 5 cm ponding before runoff
)

# After simulation
diagnostics = bc.get_diagnostics()
print(f"Cumulative runoff: {diagnostics['cumulative_runoff']:.2f} cm")
```

## Complete Examples

### Example 1: Simple ET with Rainfall Events

```python
from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten
from hydrus1dpy.processes.boundary_conditions import EnhancedAtmosphericBC

# Soil properties
vg_loam = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96)

# Model setup
model = HydrusModel(depth=100.0, n_nodes=51, material=vg_loam)

# Precipitation events: 20 mm/day for 0.5 days, every 7 days
def precipitation(t):
    if t % 7 < 0.5:
        return 20.0  # mm/day
    return 0.0

# Atmospheric BC
bc = EnhancedAtmosphericBC(
    'top',
    precipitation=precipitation,
    et_method='simple',
    et_default=4.0  # mm/day
)

model.bc_top = bc
model.set_bottom_bc('free_drainage')
model.set_initial_conditions('hydrostatic', h_bottom=-200)

# Run simulation
results = model.run(t_end=30.0, dt_init=0.001, dt_max=0.1)

# Check diagnostics
diag = bc.get_diagnostics()
print(f"ET stage: {diag['et_stage']}")
print(f"Runoff: {diag['cumulative_runoff']:.2f} cm")
print(f"Stage 2 switches: {diag['n_switches_to_stage2_et']}")
```

### Example 2: Penman-Monteith ET

```python
from hydrus1dpy.processes.evapotranspiration import WeatherData
import numpy as np

# Weather generator (seasonal variation)
def get_weather(t):
    day_of_year = t % 365
    temp = 15.0 + 10.0 * np.sin(2*np.pi*day_of_year/365)
    rh = 60.0 + 20.0 * np.sin(2*np.pi*day_of_year/365 + np.pi/2)
    wind = 2.0 + 1.0 * np.sin(2*np.pi*day_of_year/365)
    solar = 15.0 + 10.0 * np.sin(2*np.pi*day_of_year/365)

    return WeatherData(
        time=t,
        temperature=temp,
        relative_humidity=rh,
        wind_speed=wind,
        solar_radiation=solar
    )

# Atmospheric BC with Penman-Monteith
bc = EnhancedAtmosphericBC(
    'top',
    precipitation=0.0,
    et_method='penman_monteith',
    weather_func=get_weather,
    latitude=52.0,
    elevation=100.0
)

model.bc_top = bc
# ... rest of setup and run
```

### Example 3: Heavy Rainfall with Runoff

```python
# Extreme event: 50 mm/day rainfall
bc = EnhancedAtmosphericBC(
    'top',
    precipitation=50.0,  # mm/day
    et_method='simple',
    et_default=3.0,
    h_ponding=0.1,       # 1 mm water film
    ponding_max=2.0      # Max 2 cm ponding
)

model.bc_top = bc
results = model.run(t_end=1.0, dt_init=0.0001, dt_max=0.01)

# Analyze runoff
diag = bc.get_diagnostics()
total_precip = 50.0 / 10.0  # Convert mm to cm
runoff_fraction = diag['cumulative_runoff'] / total_precip * 100
print(f"Runoff: {runoff_fraction:.1f}% of precipitation")
```

## Comparison with Basic Boundary Conditions

| Feature | ConstantFluxBC | AtmosphericBC | EnhancedAtmosphericBC |
|---------|----------------|---------------|----------------------|
| **ET Calculation** | Manual | Manual | Penman-Monteith or simple |
| **Stage 1/2 ET** | No | No | Yes (pF 4.5) |
| **Infiltration** | Prescribed flux | Prescribed flux | Ponding (small +h) |
| **Runoff** | No | No | Yes (tracks excess) |
| **Weather Data** | No | No | Yes (optional) |
| **Realism** | Low | Medium | High |
| **Complexity** | Simple | Medium | Advanced |

## Physical Basis

### Evaporation Stages

**Theory** (Philip, 1957; Gardner, 1959):

- **Stage 1**: Evaporation controlled by atmospheric demand
  - Surface remains wet enough for vapor transport
  - Actual ET ≈ Potential ET
  - Flux boundary condition appropriate

- **Stage 2**: Evaporation controlled by soil hydraulic properties
  - Surface becomes dry, restricts vapor diffusion
  - Hydraulic conductivity limits water supply to surface
  - Actual ET << Potential ET
  - Head boundary condition more appropriate

**Transition**: Occurs when surface dries to critical water content/pressure:
- Original theory: ~pF 3.5 - 4.0
- HYDRUS1D default: pF 4.5 (more conservative)
- Customizable based on soil and climate

### Infiltration Process

**Traditional Approach** (Flux BC):
```
q_infiltration = min(precipitation, Ks)
```
- Problem: Ignores actual pressure head and saturation state
- Problem: Arbitrary capacity limit (usually Ks)
- Problem: Doesn't represent ponding

**Enhanced Approach** (Ponding BC):
```
h_surface = h_ponding (small positive value)
q_infiltration = Richards equation determines flux
```
- Benefit: Physically realistic (water ponds before infiltrating)
- Benefit: Flux determined by soil state (saturation, conductivity)
- Benefit: Ponding naturally represented
- Benefit: Runoff occurs when capacity exceeded

### Penman-Monteith Equation

FAO-56 version:

```
         0.408 Δ(Rn - G) + γ(900/(T+273))u₂(es - ea)
ET₀ = ───────────────────────────────────────────────
                  Δ + γ(1 + 0.34u₂)
```

Where:
- Δ = slope of saturation vapor pressure curve [kPa/°C]
- Rn = net radiation [MJ/m²/day]
- G = soil heat flux [MJ/m²/day]
- γ = psychrometric constant [kPa/°C]
- T = air temperature [°C]
- u₂ = wind speed at 2m [m/s]
- es = saturation vapor pressure [kPa]
- ea = actual vapor pressure [kPa]

**Advantages**:
- Physically-based
- International standard (FAO)
- Accounts for all energy balance components
- Validated worldwide

## Diagnostics

Get detailed boundary condition statistics:

```python
diag = bc.get_diagnostics()

print(f"Current BC type: {diag['current_type']}")
# 'flux', 'infiltration', 'ponding', or 'stage2_et'

print(f"ET stage: {diag['et_stage']}")
# 1 (potential) or 2 (soil-limited)

print(f"Stage 2 threshold: pF {diag['pf_stage2_threshold']:.1f}")
# pF value for stage 2 transition

print(f"Cumulative runoff: {diag['cumulative_runoff']:.2f} cm")
# Total runoff during simulation

print(f"Switches to stage 2: {diag['n_switches_to_stage2_et']}")
# Number of times stage 2 evaporation activated

print(f"Switches to infiltration: {diag['n_switches_to_infiltration']}")
# Number of times infiltration/ponding occurred
```

## Best Practices

### 1. Choosing ET Method

**Use Penman-Monteith when**:
- Weather data available
- Accuracy is important
- Simulating specific conditions
- Validating against measurements

**Use Simple ET when**:
- No weather data
- Rough estimate sufficient
- Scenario analysis
- Typical conditions assumed

### 2. Setting Stage 2 Threshold

**Default (pF 4.5)**:
- Conservative
- Suitable for most soils
- Corresponds to very dry surface

**Custom thresholds**:
- pF 4.2: Wilting point (h = -15,849 cm)
- pF 3.5: Moderately dry (h = -3,162 cm)
- pF 3.0: Field capacity range (h = -1,000 cm)

```python
from hydrus1dpy.processes.evapotranspiration import pf_to_head

bc = EnhancedAtmosphericBC(
    'top',
    h_stage2=pf_to_head(4.2)  # Use wilting point
)
```

### 3. Ponding Parameters

**h_ponding** (typical: 0.05 - 0.5 cm):
- Smaller values: More realistic (thin film)
- Larger values: Numerically more stable
- Recommended: 0.05 cm (0.5 mm)

**ponding_max** (typical: 1 - 10 cm):
- Depends on surface micro-topography
- Flat surface: 0.5 - 2 cm
- Rough surface: 2 - 10 cm
- Depression storage: up to 20 cm

### 4. Time Stepping

Enhanced BC requires careful time stepping:

```python
results = model.run(
    t_end=30.0,
    dt_init=0.001,    # Start small
    dt_min=1e-6,      # Allow very small steps
    dt_max=0.1,       # Limit max step
    verbose=True
)
```

**Why**:
- BC switching events require small time steps
- Infiltration events create sharp gradients
- Stage transitions need to be captured

### 5. Spatial Discretization

Fine grid near surface recommended:

```python
# For uniform grid
model = HydrusModel(
    depth=100.0,
    n_nodes=101,  # 1 cm spacing
    material=soil
)

# Top 10 cm most critical for atmospheric BC
```

## Troubleshooting

### Problem: Too many BC switches

**Symptoms**: Many switches between flux and head BC

**Causes**:
- Time step too large
- Threshold too close to actual conditions
- Numerical noise

**Solutions**:
```python
# Reduce max time step
dt_max=0.01  # Instead of 0.1

# Adjust stage 2 threshold
h_stage2=pf_to_head(4.2)  # Instead of 4.5

# Increase solver tolerance
model.set_solver_parameters(tolerance_h=0.01)
```

### Problem: Excessive runoff

**Symptoms**: Unrealistic runoff amounts

**Causes**:
- ponding_max too small
- Infiltration rate underestimated (soil Ks too low)
- Time step issues

**Solutions**:
```python
# Increase ponding maximum
ponding_max=5.0  # Instead of 2.0

# Check soil Ks value
print(f"Ks = {soil.Ks} cm/day")

# Verify with convergence test
```

### Problem: Mass balance errors

**Symptoms**: Large mass balance errors

**Causes**:
- BC switches not captured properly
- Grid too coarse
- Time step too large

**Solutions**:
```python
# Finer grid
n_nodes=201  # 0.5 cm spacing

# Smaller time steps
dt_max=0.01

# Check discretization guide
# See DISCRETIZATION_GUIDE.md
```

## Files and Modules

- `hydrus1dpy/processes/evapotranspiration.py` - ET calculation classes
- `hydrus1dpy/processes/boundary_conditions.py` - BC classes including EnhancedAtmosphericBC
- `examples/demo_atmospheric_bc.py` - Complete demonstration
- `README_ATMOSPHERIC_BC.md` - This documentation

## References

1. **Penman-Monteith ET**:
   - Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). Crop evapotranspiration - Guidelines for computing crop water requirements. FAO Irrigation and drainage paper 56.

2. **Evaporation Stages**:
   - Philip, J.R. (1957). Evaporation, and moisture and heat fields in the soil. Journal of Meteorology, 14(4), 354-366.
   - Gardner, W.R. (1959). Solutions of the flow equation for the drying of soils and other porous media. Soil Science Society of America Journal, 23(3), 183-187.

3. **Infiltration**:
   - Horton, R.E. (1940). An approach toward a physical interpretation of infiltration-capacity. Soil Science Society of America Proceedings, 5, 399-417.
   - Green, W.H., Ampt, G.A. (1911). Studies on soil physics. The Journal of Agricultural Science, 4(1), 1-24.

4. **HYDRUS**:
   - Šimůnek, J., van Genuchten, M.T., Šejna, M. (2008). Development and applications of the HYDRUS and STANMOD software packages and related codes. Vadose Zone Journal, 7(2), 587-600.

## Next Steps

- Try `examples/demo_atmospheric_bc.py`
- Adapt to your climate/soil conditions
- Experiment with different ET methods
- Compare with simple flux BC
- Validate against field data (if available)
