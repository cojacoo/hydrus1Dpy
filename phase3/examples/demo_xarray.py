"""
Demo: xarray Integration with HYDRUS1D
========================================

Demonstrates the modern xarray output format for easy data handling
and visualization.

This script can be run even without matplotlib or jupyter installed
to test the xarray functionality.
"""

import numpy as np
import sys
from pathlib import Path

# Add packages to path
phase3_path = str(Path(__file__).parent.parent)
phase2_path = str(Path(__file__).parent.parent.parent / 'phase2')
sys.path.insert(0, phase2_path)
sys.path.insert(0, phase3_path)

from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten

# Check xarray availability
try:
    import xarray as xr
    HAS_XARRAY = True
except ImportError:
    print("ERROR: xarray is not installed")
    print("Install with: pip install xarray netcdf4")
    sys.exit(1)


def main():
    print("\n" + "=" * 70)
    print("HYDRUS1D Phase 3: xarray Integration Demo")
    print("=" * 70 + "\n")

    # Create soil material
    vg_loam = VanGenuchten(
        theta_r=0.078,
        theta_s=0.430,
        alpha=0.036,
        n=1.56,
        Ks=24.96,
        l=0.5
    )

    print("Setting up model...")
    model = HydrusModel(
        depth=100.0,
        n_nodes=51,  # Smaller for quick demo
        material=vg_loam
    )

    model.set_top_bc('flux', flux=5.0)
    model.set_bottom_bc('free_drainage')
    model.set_initial_conditions('hydrostatic', h_bottom=-200)

    print("Running simulation...")
    results = model.run(
        t_end=0.5,  # Shorter for quick demo
        dt_init=0.0005,
        dt_min=1e-6,
        dt_max=0.01,
        verbose=False
    )

    print("\n" + "=" * 70)
    print("Converting to xarray Dataset...")
    print("=" * 70 + "\n")

    # Convert to xarray
    ds = model.to_xarray()

    # Display dataset info
    print("Dataset structure:")
    print(ds)

    print("\n" + "=" * 70)
    print("xarray Features Demo")
    print("=" * 70 + "\n")

    # 1. Easy coordinate-based selection
    print("1. SELECT BY COORDINATE VALUE (not array index!):")
    print("   ds.theta.sel(depth=-50, method='nearest')")
    theta_50cm = ds.theta.sel(depth=-50, method='nearest')
    print(f"   → Found {len(theta_50cm)} time points at z ≈ -50 cm")
    print(f"   → Initial θ = {theta_50cm.values[0]:.3f}")
    print(f"   → Final θ   = {theta_50cm.values[-1]:.3f}\n")

    # 2. Dimension-aware operations
    print("2. DIMENSION-AWARE OPERATIONS:")
    print("   ds.theta.mean(dim='time')  # Time-averaged profile")
    theta_tavg = ds.theta.mean(dim='time')
    print(f"   → Shape: {theta_tavg.shape}")
    print(f"   → Surface time-avg θ = {theta_tavg.values[0]:.3f}")
    print(f"   → Bottom time-avg θ  = {theta_tavg.values[-1]:.3f}\n")

    print("   ds.theta.mean(dim='depth')  # Depth-averaged time series")
    theta_zavg = ds.theta.mean(dim='depth')
    print(f"   → Shape: {theta_zavg.shape}")
    print(f"   → Initial profile-avg θ = {theta_zavg.values[0]:.3f}")
    print(f"   → Final profile-avg θ   = {theta_zavg.values[-1]:.3f}\n")

    # 3. Slicing with coordinate ranges
    print("3. SLICE BY COORDINATE RANGES:")
    print("   ds.sel(depth=slice(-30, -70))  # Select 30-70 cm depth range")
    ds_layer = ds.sel(depth=slice(-30, -70))
    print(f"   → Selected {len(ds_layer.depth)} nodes in this range")
    print(f"   → Depth range: {ds_layer.depth.values[0]:.1f} to {ds_layer.depth.values[-1]:.1f} cm\n")

    # 4. Metadata preservation
    print("4. METADATA AND ATTRIBUTES:")
    print("   Dataset global attributes:")
    for key, value in ds.attrs.items():
        print(f"     {key}: {value}")
    print("\n   Variable attributes:")
    print(f"     theta.units = {ds.theta.units}")
    print(f"     theta.long_name = {ds.theta.long_name}\n")

    # 5. Save and load
    print("5. SAVE TO NETCDF (standard format):")
    output_file = Path(__file__).parent / 'xarray_demo.nc'
    ds.to_netcdf(output_file)
    file_size_kb = output_file.stat().st_size / 1024
    print(f"   Saved to: {output_file.name}")
    print(f"   File size: {file_size_kb:.1f} KB")

    # Reload to demonstrate
    print("\n   Reloading from file...")
    ds_loaded = xr.open_dataset(output_file)
    print(f"   ✓ Successfully loaded {len(ds_loaded.data_vars)} variables")
    ds_loaded.close()

    # Clean up
    output_file.unlink()
    print(f"   Cleaned up demo file\n")

    # 6. Comparison with dict results
    print("6. COMPARISON: xarray vs. dict")
    print("\n   OLD WAY (dict with numpy arrays):")
    print("   ----------------------------------")
    print("   # Get theta at 50 cm depth")
    print("   idx = np.argmin(np.abs(depths - (-50)))  # Find nearest index")
    print("   theta_50 = results['theta'][:, idx]      # Extract column")
    print("   → Requires manual index calculation")
    print("   → No coordinate labels in output")
    print("   → Easy to make indexing errors\n")

    print("   NEW WAY (xarray):")
    print("   -----------------")
    print("   # Get theta at 50 cm depth")
    print("   theta_50 = ds.theta.sel(depth=-50, method='nearest')")
    print("   → Automatic coordinate matching")
    print("   → Result includes coordinate labels")
    print("   → Self-documenting code\n")

    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("\nxarray provides:")
    print("  ✓ Labeled arrays with coordinates (no more index confusion!)")
    print("  ✓ Dimension-aware operations (mean, std, etc.)")
    print("  ✓ Rich metadata (units, descriptions)")
    print("  ✓ Standard file format (NetCDF)")
    print("  ✓ Integration with visualization tools")
    print("  ✓ Intuitive slicing and selection")
    print("\nFor plotting, see: demo_infiltration.ipynb")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
