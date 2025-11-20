# Boundary Conditions Guide

This guide covers all boundary condition types available in HYDRUS1DPy.

## Overview

HYDRUS1DPy supports six boundary condition types:

1. **Constant Head (Dirichlet)**: Fixed pressure head
2. **Constant Flux (Neumann)**: Fixed water flux
3. **Free Drainage**: Unit gradient (gravity drainage)
4. **Atmospheric**: Flux with switching to head BC
5. **Enhanced Atmospheric**: Penman-Monteith ET with stage 1/2 evaporation

## Constant Head BC

Prescribes a fixed pressure head at the boundary.

**When to use:**
- Water table at known depth
- Constant ponding depth
- Laboratory column experiments

**Examples:**

```python
from hydrus1dpy import ConstantHeadBC

# Fixed head at bottom (water table)
bc = ConstantHeadBC('bottom', head=-50)

# Time-varying head (fluctuating water table)
bc = ConstantHeadBC('bottom', head=lambda t: -50 + 10*np.sin(2*np.pi*t/365))

# Ponding at surface
bc = ConstantHeadBC('top', head=0.0)
```

**Physics:**
- Dirichlet boundary condition
- Flux calculated from head gradient
- Can cause large fluxes if not physical

## Constant Flux BC

Prescribes a fixed water flux at the boundary.

**When to use:**
- Known infiltration/evaporation rate
- Irrigation with known application rate
- Simple rainfall without ponding

**Examples:**

```python
from hydrus1dpy import ConstantFluxBC

# Constant infiltration
bc = ConstantFluxBC('top', flux=0.5)  # 0.5 cm/day

# Constant evaporation
bc = ConstantFluxBC('top', flux=-0.3)  # -0.3 cm/day (negative = out)

# Time-varying rainfall
def rainfall(t):
    if 2 <= t <= 3:
        return 5.0  # 5 cm/day during event
    return 0.0

bc = ConstantFluxBC('top', flux=rainfall)
```

**Physics:**
- Neumann boundary condition
- Head adjusts to maintain prescribed flux
- Can lead to unrealistic heads if flux too large

**Sign convention:**
- Positive flux = water entering domain
- Negative flux = water leaving domain

## Free Drainage BC

Assumes zero pressure head gradient (unit gradient condition).

**When to use:**
- Deep water table
- Bottom of soil profile
- No impermeable layer below

**Example:**

```python
from hydrus1dpy import FreeDrainageBC

# Typical bottom boundary
bc = FreeDrainageBC('bottom')
```

**Physics:**
- Assumes dh/dz = 0 at boundary
- Flux = -K(h) (pure gravity drainage)
- Appropriate when capillary gradient negligible

**Limitations:**
- Not valid near water table
- Assumes deep drainage
- May not conserve mass if water table shallow

## Atmospheric BC

Attempts to apply prescribed flux, switches to head BC if limits exceeded.

**When to use:**
- Precipitation and evaporation
- Surface can dry or saturate
- Need automatic BC switching

**Example:**

```python
from hydrus1dpy import AtmosphericBC

# Simple atmospheric flux
def atm_flux(t):
    # Seasonal pattern
    return 0.5 * np.sin(2*np.pi*t/365)

bc = AtmosphericBC(
    'top',
    flux=atm_flux,
    h_min=-15000,    # Switch to head BC if h < -15000 cm
    h_surface=0.0    # Switch to head BC if h > 0 (ponding)
)
```

**Algorithm:**
1. Try to apply flux BC
2. If h < h_min: switch to h = h_min (too dry)
3. If h > h_surface: switch to h = h_surface (ponding)

**Limitations:**
- Requires manual flux specification
- No physical ET calculation
- Abrupt switching can cause oscillations

## Enhanced Atmospheric BC

Realistic atmospheric BC with Penman-Monteith ET and stage 1/2 evaporation.

**When to use:**
- Realistic evapotranspiration
- Weather data available
- Need physical stage transitions
- Infiltration with ponding

**Features:**
- Penman-Monteith or simple ET
- Stage 1/2 evaporation (switches at pF 4.5)
- Infiltration as ponding (small positive head)
- Runoff tracking

**Example 1: Simple ET**

```python
from hydrus1dpy import EnhancedAtmosphericBC

# Rainfall events with simple ET
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
```

**Example 2: Penman-Monteith**

```python
from hydrus1dpy import EnhancedAtmosphericBC, WeatherData

def get_weather(t):
    return WeatherData(
        time=t,
        temperature=20.0,
        relative_humidity=60.0,
        wind_speed=2.0,
        solar_radiation=15.0
    )

bc = EnhancedAtmosphericBC(
    'top',
    precipitation=5.0,
    et_method='penman_monteith',
    weather_func=get_weather,
    latitude=52.0,
    elevation=100.0
)
```

**Stage 1/2 Evaporation:**
- **Stage 1**: h > pF 4.5, potential ET (flux BC)
- **Stage 2**: h < pF 4.5, soil-limited ET (head BC at pF 4.5)

**Infiltration:**
- Applied as small positive head (0.05 cm = 0.5 mm film)
- Richards equation determines actual flux
- More realistic than prescribed flux

See [Atmospheric BC Tutorial](../tutorials/atmospheric_bc.md) for details.

## Comparison Table

| BC Type | Input | Output | Switching | Complexity | Realism |
|---------|-------|--------|-----------|------------|---------|
| Constant Head | h | q calculated | No | Low | Low |
| Constant Flux | q | h adjusts | No | Low | Low |
| Free Drainage | None | q = -K | No | Low | Medium |
| Atmospheric | q | h/q | Yes | Medium | Medium |
| Enhanced Atmospheric | Weather/Simple | h/q | Yes | High | High |

## Best Practices

### Choosing BC Type

**Top Boundary:**
- Realistic: EnhancedAtmosphericBC
- Simple rain: ConstantFluxBC
- Lab experiment: ConstantHeadBC

**Bottom Boundary:**
- Deep water table: FreeDrainageBC
- Known water table: ConstantHeadBC
- Impermeable layer: ConstantFluxBC (flux=0)

### Time Stepping

BC switching requires careful time stepping:

```python
results = model.run(
    t_end=30.0,
    dt_init=0.001,    # Start small
    dt_min=1e-6,      # Allow very small
    dt_max=0.1,       # Limit maximum
    verbose=True
)
```

### Mass Balance

Always check mass balance:

```python
mb = results['mass_balance']
rel_error = abs(mb['error'][-1]) / abs(mb['flux_top'][-1]) * 100
print(f"Mass balance error: {rel_error:.2f}%")

if rel_error > 5.0:
    print("Warning: Large mass balance error")
    print("Consider: finer grid, smaller time steps")
```

## Troubleshooting

### Excessive BC Switches

**Problem**: Too many switches between BC types

**Solutions:**
```python
# Reduce max time step
dt_max=0.01

# Adjust thresholds
h_min=-10000  # Less restrictive

# Increase solver tolerance
model.set_solver_parameters(tolerance_h=0.01)
```

### Unrealistic Fluxes

**Problem**: Calculated fluxes too large

**Solutions:**
- Check head BC values are physical
- Ensure flux BC doesn't exceed Ks
- Verify initial conditions compatible with BC

### Convergence Issues

**Problem**: Solver fails to converge

**Solutions:**
```python
# Better initial guess
model.set_initial_conditions('uniform', h=-100)

# Relaxed solver parameters
model.set_solver_parameters(
    max_iterations=20,
    tolerance_h=1.0
)

# Smaller time steps
dt_max=0.01
```

## References

1. Šimůnek, J., van Genuchten, M.T., Šejna, M. (2008). HYDRUS-1D manual.
2. Allen, R.G., et al. (1998). FAO-56: Crop evapotranspiration.
3. Philip, J.R. (1957). Evaporation and moisture fields in soil.
