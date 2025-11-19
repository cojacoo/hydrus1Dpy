# HYDRUS1DPy Installation Guide

## Quick Installation

### Step 1: Navigate to Package Directory

```bash
cd /Users/cojack/Documents/TUBAF/models/Hydrus1D/phase3
```

### Step 2: Fix NumPy Version (if needed)

If you have NumPy 2.x, Numba will not work. Check your version:

```bash
python -c "import numpy; print(numpy.__version__)"
```

If version is 2.x or higher, downgrade:

```bash
pip install "numpy<2.0"
```

### Step 3: Install Package

```bash
# Basic installation
pip install -e .

# Or with Jupyter notebook support
pip install -e ".[notebook]"

# Or with development tools
pip install -e ".[dev]"
```

### Step 4: Verify Installation

```bash
python -c "
from hydrus1dpy import HydrusModel, VanGenuchten, get_soil_parameters
print('✓ HYDRUS1DPy installed successfully!')

# Test soil database
loam = get_soil_parameters('loam')
print(f'✓ Soil database working (loam Ks={loam[\"Ks\"]} cm/day)')
"
```

## Running the Demo Notebook

```bash
# Install Jupyter if needed
pip install jupyter ipywidgets

# Launch notebook
cd examples
jupyter notebook comprehensive_demo.ipynb
```

## Troubleshooting

### Issue: "Numba needs NumPy 2.0 or less"

**Solution**: Downgrade NumPy
```bash
pip install "numpy<2.0"
```

### Issue: "No module named 'hydrus1dpy'"

**Solution**: Install in development mode
```bash
cd /Users/cojack/Documents/TUBAF/models/Hydrus1D/phase3
pip install -e .
```

### Issue: Plotly charts not showing in Jupyter

**Solution**: Install ipywidgets
```bash
pip install ipywidgets
jupyter nbextension enable --py widgetsnbextension
```

## Alternative: Virtual Environment Installation

For a clean installation, use a virtual environment:

```bash
# Create virtual environment
python -m venv hydrus_env

# Activate it
source hydrus_env/bin/activate  # On macOS/Linux
# or
hydrus_env\Scripts\activate  # On Windows

# Install package
cd /Users/cojack/Documents/TUBAF/models/Hydrus1D/phase3
pip install -e ".[notebook]"

# Verify
python -c "from hydrus1dpy import HydrusModel; print('✓ Success!')"
```

## Dependencies

The following packages will be installed:

- numpy (<2.0 for Numba compatibility)
- scipy (>=1.7.0)
- pandas (>=1.3.0)
- numba (>=0.55.0)
- plotly (>=5.0.0)

Optional (with `[notebook]`):
- jupyter
- ipywidgets

Optional (with `[dev]`):
- pytest
- pytest-cov
- black
- flake8

## Quick Test

Run a simple simulation:

```python
from hydrus1dpy import HydrusModel, VanGenuchten, get_soil_parameters

# Create soil model
loam = VanGenuchten(**get_soil_parameters('loam'))

# Create and run model
model = HydrusModel(depth=100.0, n_nodes=51, material=loam)
model.set_top_bc('flux', flux=0.5)
model.set_bottom_bc('free_drainage')
model.set_initial_conditions('uniform', h=-100)

# Run simulation
results = model.run(t_end=1.0, dt_init=0.01, verbose=True)

print(f"✓ Simulation completed!")
print(f"  Final mass balance error: {results['mass_balance']['error'][-1]:.3f}%")
```

## Getting Help

- **Documentation**: See README.md
- **Examples**: Check examples/comprehensive_demo.ipynb
- **Issues**: Report on GitHub

---

**Last Updated**: 2025-01-19
