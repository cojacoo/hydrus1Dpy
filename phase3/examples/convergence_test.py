"""
Convergence Test for Simple Infiltration
=========================================

Tests spatial and temporal convergence to identify optimal discretization.
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


def test_spatial_convergence():
    """Test different spatial discretizations."""
    print("\n" + "="*70)
    print("SPATIAL CONVERGENCE TEST")
    print("="*70)

    vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)
    infiltration_rate = 5.0  # cm/day

    # Test different node counts
    node_counts = [26, 51, 101, 201]

    print(f"\n{'Nodes':>6s} {'Spacing':>10s} {'MB Error':>12s} {'Steps':>8s} {'Time':>10s}")
    print("-"*70)

    for n_nodes in node_counts:
        depth = 100.0
        spacing = depth / (n_nodes - 1)

        model = HydrusModel(depth=depth, n_nodes=n_nodes, material=vg)
        model.set_top_bc('flux', flux=infiltration_rate)
        model.set_bottom_bc('free_drainage')
        model.set_initial_conditions('hydrostatic', h_bottom=-200)

        # Use small time steps for accuracy
        results = model.run(
            t_end=1.0,
            dt_init=0.001,
            dt_min=1e-5,
            dt_max=0.01,  # Smaller max dt
            verbose=False
        )

        mb_error = results['mass_balance']['error'][-1]
        rel_error = abs(mb_error) / abs(results['mass_balance']['flux_top'][-1])

        import time
        stats = results['statistics']

        print(f"{n_nodes:6d} {spacing:10.2f} {rel_error:12.4%} {stats['total_steps']:8d}")


def test_temporal_convergence():
    """Test different time step sizes."""
    print("\n" + "="*70)
    print("TEMPORAL CONVERGENCE TEST")
    print("="*70)

    vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)
    infiltration_rate = 5.0

    # Fixed spatial discretization
    n_nodes = 101

    # Test different max time steps
    dt_max_values = [0.1, 0.05, 0.01, 0.005, 0.001]

    print(f"\n{'dt_max':>10s} {'MB Error':>12s} {'Steps':>8s} {'Avg Iter':>10s}")
    print("-"*70)

    for dt_max in dt_max_values:
        model = HydrusModel(depth=100.0, n_nodes=n_nodes, material=vg)
        model.set_top_bc('flux', flux=infiltration_rate)
        model.set_bottom_bc('free_drainage')
        model.set_initial_conditions('hydrostatic', h_bottom=-200)

        results = model.run(
            t_end=1.0,
            dt_init=min(0.001, dt_max/10),
            dt_min=1e-6,
            dt_max=dt_max,
            verbose=False
        )

        mb_error = results['mass_balance']['error'][-1]
        rel_error = abs(mb_error) / abs(results['mass_balance']['flux_top'][-1])
        stats = results['statistics']

        print(f"{dt_max:10.4f} {rel_error:12.4%} {stats['total_steps']:8d} "
              f"{stats['avg_iterations']:10.2f}")


def test_recommended_settings():
    """Test with recommended settings for this problem."""
    print("\n" + "="*70)
    print("RECOMMENDED SETTINGS TEST")
    print("="*70)

    vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

    print("\nProblem: High infiltration (5 cm/day) into dry soil")
    print("Recommended: Fine grid + small time steps")
    print()

    # Recommended settings
    model = HydrusModel(
        depth=100.0,
        n_nodes=101,  # 1 cm spacing
        material=vg
    )

    model.set_top_bc('flux', flux=5.0)
    model.set_bottom_bc('free_drainage')
    model.set_initial_conditions('hydrostatic', h_bottom=-200)

    print("Running with:")
    print("  - 101 nodes (1 cm spacing)")
    print("  - dt_max = 0.01 days")
    print("  - dt_min = 1e-6 days")
    print()

    results = model.run(
        t_end=1.0,
        dt_init=0.0005,
        dt_min=1e-6,
        dt_max=0.01,
        verbose=True
    )

    # Detailed mass balance
    mb = results['mass_balance']
    print("\nMass Balance Analysis:")
    print(f"  Infiltrated:     {mb['flux_top'][-1]:10.4f} cm")
    print(f"  Drained:         {mb['flux_bottom'][-1]:10.4f} cm")
    print(f"  Storage change:  {mb['storage'][-1] - mb['storage'][0]:10.4f} cm")
    print(f"  Error:           {mb['error'][-1]:10.6f} cm")

    rel_error = abs(mb['error'][-1]) / abs(mb['flux_top'][-1])
    print(f"  Relative error:  {rel_error:10.4%}")

    if rel_error < 0.01:
        print("\n✓ Excellent mass balance (< 1% error)")
    elif rel_error < 0.05:
        print("\n✓ Good mass balance (< 5% error)")
    else:
        print("\n⚠ Mass balance error significant (> 5%)")
        print("  Consider: finer grid or smaller time steps")


if __name__ == '__main__':
    print("\nInvestigating mass balance errors in infiltration problem...")

    test_spatial_convergence()
    test_temporal_convergence()
    test_recommended_settings()

    print("\n" + "="*70)
    print("CONCLUSIONS")
    print("="*70)
    print("""
For high infiltration into dry soil:

1. SPATIAL: Use at least 1 cm grid spacing (100+ nodes for 100 cm)
   - Coarser grids miss sharp wetting front
   - Error decreases with finer grids

2. TEMPORAL: Use dt_max ≤ 0.01 days
   - Larger time steps miss rapid changes
   - Adaptive stepping handles this automatically

3. RECOMMENDED for this problem:
   - nodes ≥ 101 (1 cm spacing)
   - dt_max = 0.01 days
   - dt_min = 1e-6 days
   - Should achieve < 1% mass balance error
""")
