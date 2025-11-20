# Installation

## Requirements

HYDRUS1DPy requires Python 3.9 or higher.

### Core Dependencies

- NumPy >= 1.20 (< 2.0 for numba compatibility)
- SciPy >= 1.7
- Numba >= 0.55
- Pandas >= 1.3

### Optional Dependencies

**Visualization:**
- matplotlib >= 3.3
- plotly >= 5.0

**Data Handling:**
- xarray >= 0.19
- netcdf4 >= 1.5

**Interactive Notebooks:**
- jupyter >= 1.0
- ipykernel >= 6.0

## Installation Methods

### Method 1: From Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/cojacoo/hydrus1Dpy.git
cd hydrus1Dpy

# Install Phase 3 (includes all features)
cd phase3
pip install -r requirements.txt
```

### Method 2: Minimal Installation

For core functionality only (no visualization):

```bash
pip install numpy scipy numba pandas
```

### Method 3: With Visualization

```bash
pip install numpy scipy numba pandas matplotlib xarray netcdf4
```

### Method 4: Full Installation

Everything including Jupyter notebooks:

```bash
cd phase3
pip install -r requirements.txt
```

## Verify Installation

```python
# Test basic import
from hydrus1dpy import HydrusModel
print("✓ HYDRUS1DPy installed successfully")

# Test xarray support
try:
    import xarray
    print("✓ xarray available")
except ImportError:
    print("⚠ xarray not available (optional)")

# Test visualization
try:
    import matplotlib
    print("✓ matplotlib available")
except ImportError:
    print("⚠ matplotlib not available (optional)")
```

## Troubleshooting

### NumPy 2.0 Compatibility

Numba currently requires NumPy < 2.0. If you have NumPy 2.x:

```bash
pip install "numpy<2.0"
```

### Numba Compilation Issues

If numba fails to compile:

```bash
# Update numba
pip install --upgrade numba

# Or create fresh environment
conda create -n hydrus python=3.9
conda activate hydrus
pip install -r requirements.txt
```

### Missing Dependencies

If you encounter import errors, install missing packages:

```bash
pip install <package-name>
```

## Development Installation

For development work:

```bash
# Clone repository
git clone https://github.com/cojacoo/hydrus1Dpy.git
cd hydrus1Dpy

# Install in editable mode
pip install -e phase3/

# Install development tools
pip install pytest pytest-cov black flake8
```

## Next Steps

- Continue to [Quick Start](quickstart.md)
- See [API Reference](../api/core.rst) for detailed documentation
- Try [Examples](../examples/simple_infiltration.md)
