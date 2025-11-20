# Soil Hydraulic Models Guide

This guide covers the hydraulic models available for describing soil water retention and conductivity.

## Overview

HYDRUS1DPy supports multiple hydraulic models:

1. **van Genuchten (1980)**: Most widely used
2. **Modified van Genuchten**: Alternative K(h) formulation
3. **Brooks-Corey (1964)**: Power-law model
4. **Dual Porosity**: Structured soils
5. **Log-Normal**: Pore size distribution
6. **Custom**: User-defined functions

## van Genuchten Model

The most commonly used model for soil hydraulic properties.

### Equations

**Water retention:**

$$\theta(h) = \theta_r + \frac{\theta_s - \theta_r}{[1 + (\alpha|h|)^n]^m}$$

**Hydraulic conductivity:**

$$K(h) = K_s S_e^l [1 - (1 - S_e^{1/m})^m]^2$$

Where:
- $S_e = \frac{\theta - \theta_r}{\theta_s - \theta_r}$ (effective saturation)
- $m = 1 - 1/n$ (constraint for prediction)

### Parameters

- **θr**: Residual water content [-]
- **θs**: Saturated water content [-]
- **α**: Scale parameter [1/cm]
- **n**: Shape parameter [-]
- **Ks**: Saturated hydraulic conductivity [cm/day]
- **l**: Pore connectivity [-] (typically 0.5)

### Usage

```python
from hydrus1dpy import VanGenuchten

# Loam soil (Carsel & Parrish, 1988)
loam = VanGenuchten(
    theta_r=0.078,
    theta_s=0.430,
    alpha=0.036,
    n=1.56,
    Ks=24.96,
    l=0.5
)

# Use in model
model = HydrusModel(depth=100, n_nodes=51, material=loam)
```

### Typical Parameter Values

| Texture | θr | θs | α [1/cm] | n | Ks [cm/day] |
|---------|-----|-----|----------|---|-------------|
| Sand | 0.045 | 0.430 | 0.145 | 2.68 | 712.8 |
| Loamy Sand | 0.057 | 0.410 | 0.124 | 2.28 | 350.2 |
| Sandy Loam | 0.065 | 0.410 | 0.075 | 1.89 | 106.1 |
| Loam | 0.078 | 0.430 | 0.036 | 1.56 | 24.96 |
| Silt Loam | 0.067 | 0.450 | 0.020 | 1.41 | 10.8 |
| Sandy Clay Loam | 0.100 | 0.390 | 0.059 | 1.48 | 31.44 |
| Clay Loam | 0.095 | 0.410 | 0.019 | 1.31 | 6.24 |
| Silty Clay Loam | 0.089 | 0.430 | 0.010 | 1.23 | 1.68 |
| Sandy Clay | 0.100 | 0.380 | 0.027 | 1.23 | 2.88 |
| Silty Clay | 0.070 | 0.360 | 0.005 | 1.09 | 0.48 |
| Clay | 0.068 | 0.380 | 0.008 | 1.09 | 4.80 |

*From Carsel & Parrish (1988)*

## Brooks-Corey Model

Power-law model, simpler than van Genuchten.

### Equations

**Water retention:**

$$\theta(h) = \begin{cases}
\theta_r + (\theta_s - \theta_r)(h_b/h)^\lambda & h < h_b \\
\theta_s & h \geq h_b
\end{cases}$$

**Hydraulic conductivity:**

$$K(h) = K_s S_e^{2/\lambda + 2 + l}$$

### Parameters

- **θr, θs**: Residual and saturated water content
- **hb**: Air entry pressure head [cm]
- **λ**: Pore size distribution index [-]
- **Ks**: Saturated hydraulic conductivity [cm/day]
- **l**: Pore connectivity [-]

### Usage

```python
from hydrus1dpy import BrooksCorey

soil = BrooksCorey(
    theta_r=0.08,
    theta_s=0.40,
    h_b=-20.0,  # Air entry pressure
    lambda_=0.5,
    Ks=50.0,
    l=0.5
)
```

## Dual Porosity Model

For structured soils with macropores.

### Concept

Soil has two pore systems:
- **Matrix**: Small pores, high retention
- **Macropores**: Large pores, high conductivity

### Usage

```python
from hydrus1dpy import DualPorosity

soil = DualPorosity(
    theta_r=0.05,
    theta_s=0.45,
    theta_m=0.40,   # Matrix saturation
    alpha=0.03,
    n=1.5,
    alpha_m=0.01,   # Macropore α
    n_m=2.0,        # Macropore n
    w=0.1,          # Macropore fraction
    Ks=100.0
)
```

## Custom Hydraulic Model

Define your own functions for θ(h) and K(h).

### Usage

```python
from hydrus1dpy import CustomHydraulicModel
import numpy as np

def my_theta(h):
    """Custom water retention."""
    return 0.1 + 0.3 / (1 + np.abs(h/10)**2)

def my_K(h):
    """Custom hydraulic conductivity."""
    Se = (my_theta(h) - 0.1) / 0.3
    return 10.0 * Se**3

def my_C(h):
    """Specific moisture capacity (dθ/dh)."""
    dh = 0.001
    return (my_theta(h + dh) - my_theta(h - dh)) / (2*dh)

soil = CustomHydraulicModel(
    theta_func=my_theta,
    K_func=my_K,
    C_func=my_C,
    theta_s=0.4,
    theta_r=0.1
)
```

## Layered Soils

Different materials at different depths.

### Usage

```python
from hydrus1dpy import VanGenuchten

# Define materials
sand = VanGenuchten(0.045, 0.430, 0.145, 2.68, 712.8)
clay = VanGenuchten(0.068, 0.380, 0.008, 1.09, 4.8)

# Assign to layers (depths are negative!)
material_dict = {
    (0, -50): sand,    # Top 50 cm: sand
    (-50, -100): clay  # Bottom 50 cm: clay
}

model = HydrusModel(
    depth=100,
    n_nodes=101,  # Need finer grid for layers
    material=material_dict
)
```

## Parameter Estimation

### From Texture

Use pedotransfer functions:

```python
from hydrus1dpy import get_soil_parameters

# Get parameters by texture class
params = get_soil_parameters('loam')
soil = VanGenuchten(**params)
```

### From Measured Data

Fit van Genuchten parameters to retention/conductivity data:

```python
import numpy as np
from scipy.optimize import curve_fit

# Measured data
h_measured = np.array([-10, -30, -100, -300, -1000])  # cm
theta_measured = np.array([0.38, 0.32, 0.25, 0.18, 0.12])

# van Genuchten function
def vg_theta(h, theta_r, theta_s, alpha, n):
    m = 1 - 1/n
    return theta_r + (theta_s - theta_r) / (1 + (alpha * np.abs(h))**n)**m

# Fit parameters
p0 = [0.05, 0.40, 0.03, 1.5]  # Initial guess
params, cov = curve_fit(vg_theta, h_measured, theta_measured, p0=p0)

theta_r, theta_s, alpha, n = params
print(f"Fitted: θr={theta_r:.3f}, θs={theta_s:.3f}, α={alpha:.3f}, n={n:.2f}")

# Create soil model
soil = VanGenuchten(
    theta_r=theta_r,
    theta_s=theta_s,
    alpha=alpha,
    n=n,
    Ks=10.0,  # From separate measurement
    l=0.5
)
```

## Best Practices

### Choosing a Model

**van Genuchten:**
- Most versatile
- Well-validated
- Standard choice

**Brooks-Corey:**
- Simpler
- Good for sandy soils
- Has air-entry pressure

**Dual Porosity:**
- Structured soils
- Macropore flow
- Preferential flow

### Parameter Constraints

**Physical constraints:**
```python
assert 0 <= theta_r < theta_s <= 1
assert alpha > 0
assert n > 1
assert Ks > 0
assert 0 <= l <= 1
```

**Typical ranges:**
- θr: 0.0 - 0.1
- θs: 0.3 - 0.5
- α: 0.001 - 0.2 [1/cm]
- n: 1.1 - 3.0
- Ks: 0.1 - 1000 [cm/day]

### Sensitivity Analysis

Parameters ranked by influence on flow:

1. **Ks**: Most sensitive (orders of magnitude)
2. **α**: Very sensitive (wetting front)
3. **n**: Sensitive (shape of retention curve)
4. **θs**: Moderately sensitive (storage)
5. **θr**: Less sensitive (dry end)
6. **l**: Least sensitive (conductivity only)

## Troubleshooting

### Unrealistic Water Contents

**Problem**: θ > θs or θ < θr

**Causes:**
- Numerical errors
- Grid too coarse
- Time step too large

**Solutions:**
```python
# Finer grid
n_nodes=201

# Smaller time steps
dt_max=0.01

# Check parameter values
assert theta_r < theta_s
```

### Convergence Issues

**Problem**: Solver fails to converge

**Causes:**
- Ks too high or too low
- α and n extreme
- Discontinuous K(h)

**Solutions:**
```python
# Realistic parameters
assert 0.1 < Ks < 1000
assert 0.01 < alpha < 0.2
assert 1.1 < n < 3.0

# Smoother initial conditions
model.set_initial_conditions('hydrostatic', h_bottom=-100)
```

## References

1. van Genuchten, M.Th. (1980). A closed-form equation for predicting the hydraulic conductivity of unsaturated soils. SSSAJ 44:892-898.

2. Brooks, R.H., Corey, A.T. (1964). Hydraulic properties of porous media. Hydrology Paper 3, Colorado State University.

3. Carsel, R.F., Parrish, R.S. (1988). Developing joint probability distributions of soil water retention characteristics. Water Resources Research 24:755-769.

4. Mualem, Y. (1976). A new model for predicting the hydraulic conductivity of unsaturated porous media. Water Resources Research 12:513-522.
