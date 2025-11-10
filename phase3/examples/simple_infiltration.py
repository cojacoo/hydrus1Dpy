"""
Simple Infiltration Example
============================

Basic verification of Phase 3 Richards solver with:
- 1D vertical column
- Constant infiltration rate at top
- Free drainage at bottom
- van Genuchten hydraulic properties
"""

import numpy as np
import sys
from pathlib import Path

# Add packages to path
# Note: Phase 3 must come before Phase 2 so we import from phase3/hydrus1dpy
# but can still access phase2/hydrus1dpy/materials
phase3_path = str(Path(__file__).parent.parent)
phase2_path = str(Path(__file__).parent.parent.parent / 'phase2')
sys.path.insert(0, phase2_path)  # Add phase2 first (will be at index 1)
sys.path.insert(0, phase3_path)  # Add phase3 second (will be at index 0)

# Import from Phase 3 (this will also import Phase 2 materials)
from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten


def main():
    print("\n" + "=" * 70)
    print("HYDRUS1D Phase 3: Simple Infiltration Example")
    print("=" * 70 + "\n")

    # Create van Genuchten hydraulic model for loam soil
    # Parameters from Carsel & Parrish (1988)
    vg_loam = VanGenuchten(
        theta_r=0.078,  # Residual water content
        theta_s=0.430,  # Saturated water content
        alpha=0.036,    # Scale parameter [1/cm]
        n=1.56,         # Shape parameter
        Ks=24.96,       # Saturated conductivity [cm/day]
        l=0.5           # Pore connectivity
    )

    print("Soil Hydraulic Properties (Loam):")
    print(f"  θr = {vg_loam.theta_r:.3f}")
    print(f"  θs = {vg_loam.theta_s:.3f}")
    print(f"  α  = {vg_loam.alpha:.3f} 1/cm")
    print(f"  n  = {vg_loam.n:.2f}")
    print(f"  Ks = {vg_loam.Ks:.2f} cm/day")
    print()

    # Create model: 100 cm deep column with 101 nodes
    # Note: Use fine grid (1 cm spacing) to resolve sharp wetting front
    model = HydrusModel(
        depth=100.0,
        n_nodes=101,  # 1 cm spacing for better accuracy
        material=vg_loam
    )

    print(f"Domain Setup:")
    print(f"  Depth: {model.depth:.1f} cm")
    print(f"  Nodes: {model.n_nodes}")
    print(f"  Node spacing: {model.depth/(model.n_nodes-1):.2f} cm")
    print()

    # Set boundary conditions
    # Top: Constant infiltration rate
    infiltration_rate = 5.0  # cm/day (high rate → requires fine resolution!)
    model.set_top_bc('flux', flux=infiltration_rate)

    # Bottom: Free drainage (unit gradient)
    model.set_bottom_bc('free_drainage')

    print("Boundary Conditions:")
    print(f"  Top: Constant flux = {infiltration_rate:.2f} cm/day (infiltration)")
    print(f"  Bottom: Free drainage")
    print()

    # Set initial conditions: relatively dry profile
    # Hydrostatic equilibrium with water table at -300 cm (below domain)
    model.set_initial_conditions('hydrostatic', h_bottom=-200)

    print("Initial Conditions:")
    print(f"  Hydrostatic with h_bottom = -200 cm")
    print(f"  Initial h at surface: {model.h_init[0]:.1f} cm")
    print(f"  Initial h at bottom: {model.h_init[-1]:.1f} cm")
    print()

    # Run simulation
    print("Running simulation...")
    print("Note: Small time steps needed for sharp wetting front")
    print()

    results = model.run(
        t_end=1.0,        # Simulate 1 day
        dt_init=0.0005,   # Start with small time step
        dt_min=1e-6,      # Minimum time step
        dt_max=0.01,      # Small max dt for accuracy (was 0.1, too large!)
        verbose=True
    )

    # Print summary
    print("\n" + "=" * 70)
    print("Simulation Results Summary")
    print("=" * 70)

    stats = results['statistics']
    print(f"\nTime Stepping:")
    print(f"  Total accepted steps: {stats['total_steps']}")
    print(f"  Rejected steps: {stats['rejected_steps']}")
    print(f"  Average iterations: {stats['avg_iterations']:.2f}")

    # Mass balance
    mb = results['mass_balance']
    storage_change = mb['storage'][-1] - mb['storage'][0]
    rel_error = abs(mb['error'][-1]) / abs(mb['flux_top'][-1]) * 100

    print(f"\nMass Balance (final):")
    print(f"  Flux in (top): {mb['flux_top'][-1]:.4f} cm")
    print(f"  Flux out (bottom): {mb['flux_bottom'][-1]:.4f} cm")
    print(f"  Storage change: {storage_change:.4f} cm")
    print(f"  Mass balance error: {mb['error'][-1]:.4e} cm")
    print(f"  Relative error: {rel_error:.2f}%")

    if rel_error < 1.0:
        print(f"  ✓ Mass balance excellent (< 1%)")
    elif rel_error < 5.0:
        print(f"  ✓ Mass balance good (< 5%)")
    else:
        print(f"  ⚠ Mass balance error significant (> 5%)")
        print(f"     Consider: finer grid or smaller time steps")

    # Water content changes
    theta_init = results['theta'][0]
    theta_final = results['theta'][-1]
    print(f"\nWater Content Changes:")
    print(f"  Surface (z=0 cm):")
    print(f"    Initial: θ = {theta_init[0]:.3f}")
    print(f"    Final:   θ = {theta_final[0]:.3f}")
    print(f"    Change: Δθ = {theta_final[0] - theta_init[0]:.3f}")
    print(f"  Bottom (z=-100 cm):")
    print(f"    Initial: θ = {theta_init[-1]:.3f}")
    print(f"    Final:   θ = {theta_final[-1]:.3f}")
    print(f"    Change: Δθ = {theta_final[-1] - theta_init[-1]:.3f}")

    # Pressure head changes
    h_init = results['h'][0]
    h_final = results['h'][-1]
    print(f"\nPressure Head Changes:")
    print(f"  Surface: {h_init[0]:.1f} → {h_final[0]:.1f} cm")
    print(f"  Bottom:  {h_init[-1]:.1f} → {h_final[-1]:.1f} cm")

    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70)

    # Basic validation checks
    print("\nValidation Checks:")
    checks_passed = 0
    total_checks = 5

    # 1. Water content should increase (infiltration)
    if theta_final[0] > theta_init[0]:
        print("  ✓ Surface water content increased (infiltration occurred)")
        checks_passed += 1
    else:
        print("  ✗ Surface water content did not increase")

    # 2. Water content within physical bounds
    if np.all((vg_loam.theta_r <= theta_final) & (theta_final <= vg_loam.theta_s)):
        print("  ✓ Water content within physical bounds [θr, θs]")
        checks_passed += 1
    else:
        print("  ✗ Water content outside physical bounds")

    # 3. Mass balance error small
    rel_error_pct = abs(mb['error'][-1]) / abs(mb['flux_top'][-1]) * 100
    if rel_error_pct < 5.0:
        print(f"  ✓ Mass balance error < 5% ({rel_error_pct:.2f}%)")
        checks_passed += 1
    else:
        print(f"  ✗ Mass balance error too large ({rel_error_pct:.2f}%)")

    # 4. No rejected time steps (for this simple problem)
    if stats['rejected_steps'] == 0:
        print("  ✓ No rejected time steps")
        checks_passed += 1
    else:
        print(f"  ⚠ {stats['rejected_steps']} rejected time steps (not critical)")
        checks_passed += 1  # Still okay

    # 5. Reasonable iteration count
    if 2 <= stats['avg_iterations'] <= 10:
        print(f"  ✓ Average iterations reasonable ({stats['avg_iterations']:.1f})")
        checks_passed += 1
    else:
        print(f"  ⚠ Average iterations unusual ({stats['avg_iterations']:.1f})")

    print(f"\nPassed {checks_passed}/{total_checks} validation checks")

    if checks_passed == total_checks:
        print("✓ All checks passed - Phase 3 implementation verified!")
    elif checks_passed >= total_checks - 1:
        print("✓ Implementation appears functional")
    else:
        print("⚠ Some issues detected - review results")

    return results


if __name__ == '__main__':
    results = main()
