# HYDRUS1D Python Wrapper - Phase 2

**Status**: ✅ Complete
**Version**: 0.2.0-phase2

## Overview

Phase 2 implements exchangeable soil hydraulic models with scientifically rigorous implementations based on peer-reviewed literature.

### Key Features

- ✅ Abstract base class for hydraulic models
- ✅ van Genuchten (1980) + Mualem (1976)
- ✅ Modified van Genuchten (Vogel & Cislerova, 1988)
- ✅ Brooks-Corey (1964) + Mualem/Burdine
- ✅ Dual-Porosity (Durner, 1994)
- ✅ Log-Normal (Kosugi, 1996)
- ✅ Custom user-defined models
- ✅ Comprehensive validation and testing
- ✅ Interactive comparison visualizations

## Hydraulic Models

### 1. van Genuchten (1980)

The most widely used model for soil hydraulic properties:

```python
from hydrus1dpy.materials import VanGenuchten

vg = VanGenuchten(
    theta_r=0.078,  # Residual water content
    theta_s=0.430,  # Saturated water content
    alpha=0.036,    # Scale parameter [1/cm]
    n=1.56,         # Shape parameter
    Ks=24.96,       # Saturated conductivity [cm/day]
    l=0.5           # Pore connectivity
)

# Calculate properties
theta = vg.water_content(h=-100)  # Water content at h=-100 cm
K = vg.conductivity(h=-100)        # Conductivity
C = vg.capacity(h=-100)            # Water capacity (dθ/dh)
h = vg.pressure_head(theta=0.25)   # Inverse function

# Validate model
vg.validate()  # Check physical constraints
```

**Equations**:

Water Retention:
```
θ(h) = θr + (θs - θr) / [1 + |α·h|^n]^m
where m = 1 - 1/n
```

Hydraulic Conductivity (Mualem, 1976):
```
K(h) = Ks · Se^l · [1 - (1 - Se^(1/m))^m]^2
where Se = (θ - θr) / (θs - θr)
```

### 2. Brooks-Corey (1964)

Power-law model with explicit air-entry value:

```python
from hydrus1dpy.materials import BrooksCorey

bc = BrooksCorey(
    theta_r=0.078,
    theta_s=0.430,
    hb=-20.0,      # Air-entry value [cm]
    lambda_=0.5,   # Pore size distribution index
    Ks=24.96,
    l=2.0          # Pore connectivity (2.0 for Mualem, 1.5 for Burdine)
)
```

**Equations**:
```
For h >= hb:  θ = θs
For h < hb:   Se = (h/hb)^(-λ)
              θ = θr + (θs - θr) · Se
              K = Ks · Se^(2/λ + l + 2)
```

### 3. Dual-Porosity (Durner, 1994)

Bimodal pore size distribution for structured soils:

```python
from hydrus1dpy.materials import DualPorosity

dp = DualPorosity(
    theta_r=0.05,
    theta_s=0.45,
    alpha1=0.15,   # Macro pores scale [1/cm]
    n1=2.5,        # Macro pores shape
    alpha2=0.01,   # Micro pores scale [1/cm]
    n2=1.4,        # Micro pores shape
    w2=0.7,        # Weight for micro pores (0-1)
    Ks=50.0
)
```

**Equation**:
```
θ = θr + (θs - θr) · [w1·Se1 + w2·Se2]
where:
  Se1 = [1 + |α1·h|^n1]^(-m1)  (macro pores)
  Se2 = [1 + |α2·h|^n2]^(-m2)  (micro pores)
  w1 + w2 = 1
```

### 4. Log-Normal (Kosugi, 1996)

Based on log-normal pore size distribution:

```python
from hydrus1dpy.materials import LogNormal

ln = LogNormal(
    theta_r=0.078,
    theta_s=0.430,
    hm=-10.0,      # Median pressure head [cm]
    sigma=1.5,     # Standard deviation of log(h)
    Ks=24.96
)
```

### 5. Custom Models

Define your own hydraulic functions:

```python
from hydrus1dpy.materials import CustomHydraulicModel
import numpy as np

def my_retention(h, a, b):
    """Custom retention function"""
    if isinstance(h, np.ndarray):
        theta = np.full_like(h, 0.43)
        mask = h < 0
        theta[mask] = 0.078 + 0.352 * np.exp(a * h[mask] ** b)
        return theta
    else:
        return 0.43 if h >= 0 else 0.078 + 0.352 * np.exp(a * h ** b)

def my_conductivity(h, Ks, c):
    """Custom conductivity function"""
    return Ks * np.exp(c * np.asarray(h))

custom = CustomHydraulicModel(
    theta_r=0.078,
    theta_s=0.43,
    Ks=24.96,
    theta_func=my_retention,
    K_func=my_conductivity,
    a=0.001,  # Custom parameters
    b=0.8,
    c=0.01
)
```

## Model Comparison

Compare different models interactively:

```python
from hydrus1dpy.materials import VanGenuchten, BrooksCorey, DualPorosity
import numpy as np
import plotly.graph_objects as go

# Create models
models = {
    'van Genuchten': VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96),
    'Brooks-Corey': BrooksCorey(0.078, 0.430, -20.0, 0.5, 24.96),
    'Dual-Porosity': DualPorosity(0.05, 0.45, 0.15, 2.5, 0.01, 1.4, 0.7, 50.0)
}

# Compare retention curves
h = np.logspace(0, 4, 100)  # 1 to 10000 cm
h = -h

fig = go.Figure()
for name, model in models.items():
    theta = model.water_content(h)
    fig.add_trace(go.Scatter(x=-h, y=theta, name=name))

fig.update_layout(xaxis_type='log', xaxis_title='|h| [cm]', yaxis_title='θ [-]')
fig.show()
```

## Scientific Validation

All models include:

### Physical Constraint Validation
```python
model = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96)
model.validate()  # Checks:
# ✓ θr ≤ θ(h) ≤ θs for all h
# ✓ θ(h) monotonically increasing
# ✓ 0 < K(h) ≤ Ks
# ✓ K(h) monotonically increasing
# ✓ C(h) ≥ 0
# ✓ Inverse function accuracy
```

### Analytical Solutions

Where available, models use analytical solutions for:
- Water content: θ(h)
- Conductivity: K(h)
- Capacity: C(h) = dθ/dh
- Inverse: h(θ)

### Vectorization

All functions support both scalar and array inputs:
```python
# Scalar
theta = model.water_content(-100.0)

# Array
h = np.array([-1000, -100, -10, 0])
theta = model.water_content(h)  # Vectorized computation
```

## References

### Primary Literature

1. **van Genuchten (1980)**
   - van Genuchten, M. Th. (1980). A closed-form equation for predicting the hydraulic conductivity of unsaturated soils. Soil Science Society of America Journal, 44(5), 892-898.
   - DOI: 10.2136/sssaj1980.03615995004400050002x

2. **Mualem (1976)**
   - Mualem, Y. (1976). A new model for predicting the hydraulic conductivity of unsaturated porous media. Water Resources Research, 12(3), 513-522.
   - DOI: 10.1029/WR012i003p00513

3. **Brooks & Corey (1964)**
   - Brooks, R. H., & Corey, A. T. (1964). Hydraulic properties of porous media. Hydrology Papers, Colorado State University.

4. **Durner (1994)**
   - Durner, W. (1994). Hydraulic conductivity estimation for soils with heterogeneous pore structure. Water Resources Research, 30(2), 211-223.
   - DOI: 10.1029/93WR02676

5. **Kosugi (1996)**
   - Kosugi, K. (1996). Lognormal distribution model for unsaturated soil hydraulic properties. Water Resources Research, 32(9), 2697-2703.
   - DOI: 10.1029/96WR01776

6. **Vogel & Cislerova (1988)**
   - Vogel, T., & Cislerova, M. (1988). On the reliability of unsaturated hydraulic conductivity calculated from the moisture retention curve. Transport in Porous Media, 3(1), 1-15.

### Parameter Databases

7. **Carsel & Parrish (1988)**
   - Carsel, R. F., & Parrish, R. S. (1988). Developing joint probability distributions of soil water retention characteristics. Water Resources Research, 24(5), 755-769.
   - Standard parameters for 12 USDA soil texture classes

## Installation

```bash
cd phase2
pip install -e .
```

Requirements:
- numpy >= 1.20
- scipy >= 1.7
- plotly >= 5.0

## Running Tests

```bash
cd phase2
pytest tests/ -v

# Run specific test
pytest tests/test_hydraulic_models.py::TestVanGenuchten -v

# With coverage
pytest tests/ --cov=hydrus1dpy --cov-report=html
```

## Examples

See `examples/` directory:
- `example_material_comparison.py` - Compare different models

Run examples:
```bash
cd examples
python example_material_comparison.py
```

## API Reference

### Base Class

```python
class HydraulicModel(ABC):
    """Abstract base class for all hydraulic models"""

    @abstractmethod
    def water_content(self, h) -> float | ndarray:
        """θ(h) - Water retention curve"""

    @abstractmethod
    def conductivity(self, h) -> float | ndarray:
        """K(h) - Hydraulic conductivity function"""

    @abstractmethod
    def capacity(self, h) -> float | ndarray:
        """C(h) = dθ/dh - Water capacity"""

    def pressure_head(self, theta) -> float | ndarray:
        """h(θ) - Inverse function (numerical or analytical)"""

    def effective_saturation(self, h) -> float | ndarray:
        """Se = (θ - θr) / (θs - θr)"""

    def relative_conductivity(self, h) -> float | ndarray:
        """Kr = K(h) / Ks"""

    def validate(self) -> bool:
        """Validate physical constraints"""
```

## Integration with Phase 1

Phase 2 materials are compatible with Phase 1 I/O:

```python
from phase1.hydrus1dpy import ModelConfiguration, MaterialProperties
from phase2.hydrus1dpy.materials import VanGenuchten

# Create hydraulic model
vg_model = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96)

# Convert to Phase 1 MaterialProperties for file I/O
mat_props = MaterialProperties(
    material_id=1,
    model_type=0,  # van Genuchten
    theta_r=vg_model.theta_r,
    theta_s=vg_model.theta_s,
    alpha=vg_model.alpha,
    n=vg_model.n,
    Ks=vg_model.Ks,
    l=vg_model.l
)
```

## Advantages over Phase 1

1. **Direct Python calculations** - No Fortran needed for hydraulic functions
2. **Extensible** - Easy to add new models
3. **Custom models** - Define your own functions
4. **Validated** - Comprehensive physical constraint checking
5. **Interactive** - Immediate feedback and visualization
6. **Documented** - Complete equations and references

## Next Steps: Phase 3

Phase 3 will implement:
- Richards equation solver in Python/Numba
- Full water flow simulation without Fortran
- Performance optimization
- Validation against Fortran results

## License

MIT License (subject to repository owner approval)

## Contributing

For issues and contributions, please use the GitHub repository.
