# Discretization Guidelines for HYDRUS1D Phase 3

## Overview

The accuracy of Richards equation solutions depends critically on **spatial** and **temporal** discretization. This guide provides recommendations for different problem types.

## General Principles

### Spatial Discretization

**Key factors:**
- Gradient steepness (wetting fronts, interfaces)
- Domain depth
- Hydraulic property variations

**Rule of thumb:**
```
Δz ≤ L_characteristic / 10
```
where L_characteristic is the length scale of the steepest gradients.

### Temporal Discretization

**Key factors:**
- Rate of change in boundary conditions
- Hydraulic conductivity range
- Initial condition gradients

**Rule of thumb:**
```
Δt_max ≤ 0.1 * T_characteristic
```
where T_characteristic is the time scale of the fastest changes.

## Problem-Specific Recommendations

### 1. Infiltration into Dry Soil

**Characteristics:**
- Sharp wetting front
- Rapid changes near surface
- Large pressure head gradients

**Recommended Settings:**
```python
model = HydrusModel(
    depth=100.0,
    n_nodes=101,  # 1 cm spacing minimum
    material=soil
)

results = model.run(
    dt_init=0.0005,
    dt_min=1e-6,
    dt_max=0.01,  # ≤ 0.01 days
    ...
)
```

**Expected accuracy:** < 3% mass balance error

### 2. Drainage from Saturation

**Characteristics:**
- Moderate gradients
- Slower changes
- Uniform initial conditions

**Recommended Settings:**
```python
model = HydrusModel(
    depth=100.0,
    n_nodes=51,   # 2 cm spacing acceptable
    material=soil
)

results = model.run(
    dt_init=0.001,
    dt_min=1e-6,
    dt_max=0.05,  # Can be larger
    ...
)
```

**Expected accuracy:** < 2% mass balance error

### 3. Steady-State Problems

**Characteristics:**
- No time evolution
- Equilibrium conditions
- Smooth gradients

**Recommended Settings:**
```python
model = HydrusModel(
    depth=100.0,
    n_nodes=51,   # 2 cm spacing often sufficient
    material=soil
)

results = model.run(
    dt_init=0.01,
    dt_min=1e-6,
    dt_max=0.1,   # Large dt acceptable
    t_end=10.0,   # Run to equilibrium
    ...
)
```

**Expected accuracy:** < 1% mass balance error

### 4. Layered Soils

**Characteristics:**
- Material interfaces
- Conductivity contrasts
- Potential ponding

**Recommended Settings:**
```python
# Use fine grid at interfaces
model = HydrusModel(
    depth=100.0,
    n_nodes=201,  # 0.5 cm spacing for interfaces
    material=layered_materials
)

results = model.run(
    dt_init=0.0001,  # Start very small
    dt_min=1e-7,
    dt_max=0.005,    # Keep small
    ...
)
```

**Expected accuracy:** < 5% mass balance error (challenging!)

### 5. Atmospheric Forcing

**Characteristics:**
- Time-varying fluxes
- Potential ponding/drying
- BC switching

**Recommended Settings:**
```python
model = HydrusModel(
    depth=100.0,
    n_nodes=101,  # 1 cm spacing
    material=soil
)

model.set_top_bc('atmospheric',
                 flux=lambda t: precipitation(t) - evaporation(t),
                 h_min=-15000,
                 h_surface=0.0)

results = model.run(
    dt_init=0.001,
    dt_min=1e-6,
    dt_max=0.02,  # Match weather data resolution
    ...
)
```

**Expected accuracy:** < 5% mass balance error

## Convergence Testing

Always perform convergence tests for new problem types:

### Spatial Convergence

```python
for n_nodes in [26, 51, 101, 201]:
    model = HydrusModel(depth=100, n_nodes=n_nodes, ...)
    results = model.run(...)

    # Check mass balance error
    mb_error = results['mass_balance']['error'][-1]
    print(f"Nodes: {n_nodes}, Error: {mb_error}")
```

**Criterion:** Error should decrease monotonically. Use grid where error < 5%.

### Temporal Convergence

```python
for dt_max in [0.1, 0.05, 0.01, 0.005]:
    results = model.run(dt_max=dt_max, ...)

    # Check mass balance error
    mb_error = results['mass_balance']['error'][-1]
    print(f"dt_max: {dt_max}, Error: {mb_error}")
```

**Criterion:** Error should stabilize. Use dt_max where error < 5%.

## Mass Balance Interpretation

### Excellent (< 1%)
- Solution is highly accurate
- Grid and time step are appropriate
- Can trust quantitative results

### Good (1-5%)
- Solution is acceptable for most applications
- Qualitatively correct behavior
- Consider refinement for critical studies

### Marginal (5-10%)
- Solution may have significant errors
- Recommend refinement
- Use only for qualitative insights

### Poor (> 10%)
- Solution is unreliable
- Must refine grid and/or time step
- Check for numerical instabilities

## Common Issues

### Issue 1: Large Mass Balance Error

**Symptoms:**
- Error > 5%
- Large flux imbalances

**Solutions:**
1. Reduce dt_max by factor of 5-10
2. Increase nodes by factor of 2
3. Check BC implementation

### Issue 2: Rejected Time Steps

**Symptoms:**
- Many rejected steps
- Slow simulation

**Solutions:**
1. Reduce dt_init
2. Reduce under_relaxation factor (< 1.0)
3. Check for unrealistic BCs

### Issue 3: Non-Physical Results

**Symptoms:**
- θ outside [θr, θs]
- Oscillating solutions

**Solutions:**
1. Reduce dt_max significantly
2. Increase spatial resolution
3. Check initial conditions

## Performance vs Accuracy Trade-offs

| Priority | Spatial | Temporal | Typical Time | MB Error |
|----------|---------|----------|--------------|----------|
| **Speed** | 26-51 nodes | dt_max=0.1 | Seconds | 5-10% |
| **Balanced** | 51-101 nodes | dt_max=0.01 | ~1 minute | 2-5% |
| **Accuracy** | 101-201 nodes | dt_max=0.005 | Minutes | <2% |
| **Research** | 201+ nodes | dt_max=0.001 | 10+ minutes | <1% |

## Examples

See `phase3/examples/convergence_test.py` for complete convergence analysis of the infiltration problem.

## References

1. **Celia et al. (1990)**: Mass-conservative numerical methods
2. **Huang et al. (1996)**: Convergence criteria
3. **Miller et al. (1998)**: Numerical stability in Richards equation
4. **Lehmann & Ackerer (1998)**: Comparison of iterative methods

---

**Last updated:** 2025-01-10
**Version:** 1.0 for Phase 3
