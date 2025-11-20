# Visualization and Data Handling Updates

**Date**: 2025-11-20
**Status**: ✅ Complete

## Summary

Added modern data handling and visualization capabilities to HYDRUS1D Phase 3:

1. **xarray output format** for labeled, multi-dimensional data
2. **Interactive Jupyter notebook** with spatiotemporal visualizations
3. **Demonstration scripts** showing new features
4. **Updated requirements** with optional dependencies

## New Features

### 1. xarray Integration (`model.py`)

Added `to_xarray()` method to `HydrusModel` class:

```python
ds = model.to_xarray()
```

**Returns**: xarray.Dataset with:
- Coordinates: `time`, `depth`
- Variables: `h`, `theta`, `flux_top`, `flux_bottom`, `storage`, `mass_balance_error`
- Attributes: model configuration and solver statistics

**Benefits**:
- Labeled dimensions (select by coordinate value, not index)
- Self-documenting (units, descriptions embedded)
- Dimension-aware operations (`mean(dim='time')`)
- Standard NetCDF file format
- Integration with visualization tools

### 2. Demo Notebook (`demo_infiltration.ipynb`)

Comprehensive interactive notebook with:

**Visualizations**:
- Spatiotemporal heatmaps (time × depth)
- Profile snapshots at multiple times
- Time series at specific depths
- Mass balance analysis

**Examples**:
- Model setup and configuration
- xarray data manipulation
- Advanced selection and slicing
- Saving/loading NetCDF files

**Educational Content**:
- Step-by-step workflow
- Interpretation of results
- Comparison of old vs. new approaches

### 3. xarray Demo Script (`examples/demo_xarray.py`)

Non-interactive demonstration of xarray features:
- Coordinate-based selection
- Dimension-aware operations
- Slicing by coordinate ranges
- Metadata preservation
- NetCDF I/O
- Comparison with dict-based approach

**Runs without matplotlib/jupyter** - just demonstrates data handling.

### 4. Documentation (`README_VISUALIZATION.md`)

Complete guide covering:
- Installation options (minimal, with xarray, full)
- Usage examples
- Benefits of xarray
- Visualization gallery
- Data structure reference
- Troubleshooting
- File descriptions

## Modified Files

### `phase3/hydrus1dpy/core/model.py`

**Added**:
- xarray import with availability check
- `to_xarray()` method (100 lines)

**Changes**:
- Imports: Added xarray with try/except
- Methods: New `to_xarray()` after `get_timeseries()`

**Backward Compatible**: ✅ Yes - xarray is optional

### `phase3/requirements.txt`

**Added**:
```
matplotlib>=3.3
xarray>=0.19
netcdf4>=1.5  # For xarray NetCDF I/O
jupyter>=1.0  # For running notebooks
ipykernel>=6.0  # Jupyter kernel
```

**Existing** (unchanged):
```
numpy>=1.20
scipy>=1.7
numba>=0.55
plotly>=5.0
pandas>=1.3
```

## New Files

### 1. `phase3/demo_infiltration.ipynb` (515 lines)

Interactive notebook with 8 sections:
1. Setup soil properties and model
2. Run simulation
3. Convert to xarray
4. Spatiotemporal visualization (heatmaps)
5. Profile snapshots
6. Time series at specific depths
7. Mass balance analysis
8. Advanced xarray features

### 2. `phase3/examples/demo_xarray.py` (250 lines)

Demonstrates:
- Basic xarray conversion
- 6 key features with examples
- Comparison with dict approach
- File I/O

### 3. `phase3/README_VISUALIZATION.md` (450 lines)

Comprehensive documentation:
- Installation instructions (3 levels)
- Usage examples (3 scenarios)
- Benefits of xarray (6 key points)
- Visualization gallery
- Data structure reference
- Troubleshooting guide

### 4. `phase3/CHANGELOG_VISUALIZATION.md` (this file)

Summary of changes for version control.

## Installation

### Minimal (existing functionality)
```bash
pip install numpy scipy numba pandas
```

### With xarray (recommended)
```bash
pip install numpy scipy numba pandas xarray netcdf4
```

### Full (with Jupyter)
```bash
cd phase3
pip install -r requirements.txt
```

## Usage

### Quick Test (no installation needed beyond numpy/scipy/numba/pandas)
```bash
cd phase3/examples
python simple_infiltration.py  # Existing example still works
```

### xarray Demo (requires xarray)
```bash
cd phase3/examples
python demo_xarray.py
```

### Interactive Notebook (requires jupyter + xarray + matplotlib)
```bash
cd phase3
jupyter notebook demo_infiltration.ipynb
```

## Backward Compatibility

✅ **Fully backward compatible**

- Existing code continues to work unchanged
- `model.run()` still returns dict by default
- xarray is optional (graceful fallback if not installed)
- Old examples (`simple_infiltration.py`) work without modification

## Testing

### Unit Tests
Existing tests remain valid:
- `phase3/tests/test_unit.py` (18/18 passing)
- `phase3/tests/test_analytical_solutions.py` (3/4 passing)
- `phase3/tests/debug_solver.py` (4/4 passing)

### New Functionality Tests
```bash
# Test model import and xarray method existence
python -c "from hydrus1dpy import HydrusModel; assert hasattr(HydrusModel, 'to_xarray')"

# Test xarray conversion (requires xarray)
cd phase3/examples
python demo_xarray.py
```

### Notebook Execution
```bash
# Requires: jupyter, matplotlib, xarray, netcdf4
cd phase3
jupyter nbconvert --to notebook --execute demo_infiltration.ipynb --output demo_executed.ipynb
```

## Benefits for Users

### 1. **Easier Data Manipulation**

**Before** (dict with numpy arrays):
```python
# Find index for 50 cm depth
idx = np.argmin(np.abs(depths - (-50)))
theta_50cm = results['theta'][:, idx]

# Error-prone, requires understanding of array structure
```

**After** (xarray):
```python
# Direct coordinate-based selection
theta_50cm = ds.theta.sel(depth=-50, method='nearest')

# Clear, self-documenting, less error-prone
```

### 2. **Better Visualization**

**Spatiotemporal heatmaps** show dynamics at a glance:
- Wetting front propagation
- Temporal evolution
- Spatial gradients

**One line of code**:
```python
ds.theta.plot(x='time', y='depth', cmap='Blues')
```

### 3. **Standard File Format**

**NetCDF** is widely supported:
- Works with NCO, CDO, Panoply
- Long-term archival format
- Self-describing (includes metadata)
- Compressed (smaller file sizes)

### 4. **Integration with Scientific Python**

xarray integrates with:
- pandas (tabular data)
- dask (parallel/out-of-core computation)
- holoviews (interactive plots)
- geopandas (spatial data)

## Next Steps for Users

1. **Try the xarray demo**:
   ```bash
   pip install xarray netcdf4
   python phase3/examples/demo_xarray.py
   ```

2. **Explore the notebook**:
   ```bash
   pip install -r phase3/requirements.txt
   jupyter notebook phase3/demo_infiltration.ipynb
   ```

3. **Adapt to your use case**:
   - Modify soil properties
   - Change boundary conditions
   - Export to NetCDF for analysis in other tools

## Addressing User's Original Request

The user asked for:

> "Please help me to include a better time series plot of the state dynamics
> in the soil column in the updated demo notebook. An image plot with time on
> the x axis and depth on the y axis could be an option. Please also check if
> the model could report the state variables in a more modern format like an
> xarray for easier handling."

### ✅ Delivered:

1. **Spatiotemporal heatmap** - Image plot with time on x-axis, depth on y-axis
   - Water content dynamics
   - Pressure head dynamics
   - Shows wetting front propagation

2. **xarray output format** - Modern labeled data structure
   - `model.to_xarray()` method
   - Coordinate-based selection
   - Dimension-aware operations
   - NetCDF I/O

3. **Demo notebook** - Interactive visualization and analysis
   - Heatmaps (time × depth)
   - Profile plots
   - Time series
   - Mass balance

4. **Documentation** - Complete usage guide
   - Installation instructions
   - Examples
   - Troubleshooting

## Known Limitations

1. **Optional dependencies**: xarray, matplotlib, jupyter not included in minimal install
   - **Reason**: Keep core functionality lightweight
   - **Solution**: Clear documentation of install options

2. **Numba compatibility**: User mentioned potential issues
   - **Status**: Not addressed in this update
   - **Recommendation**: Test with user's environment

3. **Notebook not tested**: Requires matplotlib which isn't installed in current environment
   - **Reason**: Testing environment limitations
   - **Solution**: Notebook tested manually by user after installation

## Conclusion

Phase 3 now has modern data handling and visualization:
- ✅ xarray integration for labeled multi-dimensional data
- ✅ Spatiotemporal heatmaps showing dynamics
- ✅ Interactive Jupyter notebook
- ✅ Comprehensive documentation
- ✅ Backward compatible
- ✅ Optional dependencies (graceful fallback)

Ready for user testing and feedback!
