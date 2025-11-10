"""
Debug Script for Richards Solver
=================================

Identifies and fixes numerical issues in Phase 3 solver.
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

def test_minimal_setup():
    """Test with minimal, well-conditioned setup."""
    print("\n" + "="*70)
    print("DEBUG: Testing minimal setup")
    print("="*70 + "\n")

    # Very simple case: uniform properties, small domain
    vg = VanGenuchten(
        theta_r=0.078,
        theta_s=0.430,
        alpha=0.036,
        n=1.56,
        Ks=24.96,
        l=0.5
    )

    # Small domain for debugging
    model = HydrusModel(depth=10.0, n_nodes=6, material=vg)

    print(f"Domain: {model.depth} cm, {model.n_nodes} nodes")
    print(f"Node depths: {model.depths}")
    print(f"Grid spacing: {model.depths[0] - model.depths[1]} cm")

    # Simple boundary conditions
    model.set_top_bc('constant_head', head=-100.0)
    model.set_bottom_bc('constant_head', head=-100.0)

    print(f"BCs: Top = constant h=-100, Bottom = constant h=-100")

    # Uniform initial condition (should be equilibrium)
    model.set_initial_conditions('uniform', h=-100.0)

    print(f"Initial h: {model.h_init}")

    # Check initial properties
    print("\nInitial hydraulic properties:")
    for i in range(model.n_nodes):
        h = model.h_init[i]
        theta = vg.water_content(h)
        K = vg.conductivity(h)
        C = vg.capacity(h)
        print(f"  Node {i}: h={h:.1f}, θ={theta:.3f}, K={K:.2f}, C={C:.4f}")

    # Very small time step
    print("\nAttempting simulation with dt=1e-4...")

    try:
        results = model.run(
            t_end=0.001,
            dt_init=1e-4,
            dt_min=1e-6,
            dt_max=1e-4,
            verbose=True
        )
        print("\n✓ Success! Equilibrium case works.")
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_boundary_condition_assembly():
    """Test boundary condition matrix assembly directly."""
    print("\n" + "="*70)
    print("DEBUG: Testing BC assembly")
    print("="*70 + "\n")

    from hydrus1dpy.processes.boundary_conditions import ConstantHeadBC, ConstantFluxBC

    # Create simple arrays
    n = 5
    a = np.zeros(n)
    b = np.ones(n) * 2.0  # Diagonal
    c = np.zeros(n)
    d = np.zeros(n)
    h = np.full(n, -100.0)
    K = np.full(n, 10.0)
    dz = 2.0

    print(f"Initial matrix diagonal b: {b}")

    # Test constant head BC
    bc_top = ConstantHeadBC('top', head=-50.0)
    bc_top.apply(a, b, c, d, h, K, dz, 0.0)

    print(f"After top BC: a[0]={a[0]}, b[0]={b[0]}, c[0]={c[0]}, d[0]={d[0]}")

    bc_bottom = ConstantHeadBC('bottom', head=-150.0)
    bc_bottom.apply(a, b, c, d, h, K, dz, 0.0)

    print(f"After bottom BC: a[-1]={a[-1]}, b[-1]={b[-1]}, c[-1]={c[-1]}, d[-1]={d[-1]}")

    # Check for zeros in diagonal
    if np.any(b == 0):
        print("✗ ERROR: Zero found in diagonal!")
        print(f"  Diagonal b: {b}")
        return False
    else:
        print("✓ No zeros in diagonal")
        return True


def test_tridiagonal_solver():
    """Test tridiagonal solver independently."""
    print("\n" + "="*70)
    print("DEBUG: Testing tridiagonal solver")
    print("="*70 + "\n")

    from hydrus1dpy.numerics.linear_solver import solve_tridiagonal

    # Simple test problem: -u'' = 1, u(0)=0, u(1)=0
    # Solution: u(x) = 0.5*x*(1-x)
    n = 5
    dx = 1.0 / (n - 1)

    a = np.ones(n) * (-1.0 / dx**2)
    b = np.ones(n) * (2.0 / dx**2)
    c = np.ones(n) * (-1.0 / dx**2)
    d = np.ones(n)

    # Boundary conditions
    a[0] = 0.0
    b[0] = 1.0
    c[0] = 0.0
    d[0] = 0.0

    a[-1] = 0.0
    b[-1] = 1.0
    c[-1] = 0.0
    d[-1] = 0.0

    print(f"Matrix a: {a}")
    print(f"Matrix b: {b}")
    print(f"Matrix c: {c}")
    print(f"RHS d: {d}")

    try:
        u = solve_tridiagonal(a, b, c, d)
        print(f"\nSolution u: {u}")

        # Check solution
        x = np.linspace(0, 1, n)
        u_exact = 0.5 * x * (1 - x)
        error = np.max(np.abs(u - u_exact))
        print(f"Exact solution: {u_exact}")
        print(f"Max error: {error:.2e}")

        if error < 0.01:
            print("✓ Tridiagonal solver works correctly")
            return True
        else:
            print("✗ Solution error too large")
            return False

    except Exception as e:
        print(f"✗ Error in solver: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_flux_bc():
    """Test with flux boundary condition."""
    print("\n" + "="*70)
    print("DEBUG: Testing with flux BC")
    print("="*70 + "\n")

    vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

    model = HydrusModel(depth=10.0, n_nodes=6, material=vg)

    # Flux at top, constant head at bottom
    model.set_top_bc('flux', flux=0.0)  # No flux
    model.set_bottom_bc('constant_head', head=-100.0)

    model.set_initial_conditions('uniform', h=-100.0)

    print("Testing no-flux at top, constant head at bottom...")
    print("This should be stable (equilibrium)")

    try:
        results = model.run(
            t_end=0.001,
            dt_init=1e-4,
            dt_min=1e-6,
            dt_max=1e-4,
            verbose=True
        )
        print("\n✓ Flux BC works!")
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all debug tests."""
    print("\n" + "#"*70)
    print("# RICHARDS SOLVER DEBUG SUITE")
    print("#"*70)

    tests = [
        ("Tridiagonal Solver", test_tridiagonal_solver),
        ("BC Assembly", test_boundary_condition_assembly),
        ("Minimal Setup (equilibrium)", test_minimal_setup),
        ("Flux BC", test_with_flux_bc),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n\n{'='*70}")
        print(f"Running: {name}")
        print(f"{'='*70}")
        success = test_func()
        results.append((name, success))

    # Summary
    print("\n\n" + "#"*70)
    print("# DEBUG SUMMARY")
    print("#"*70 + "\n")

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed! Solver is working correctly.")
    else:
        print("\n✗ Some tests failed. Check output above for details.")


if __name__ == '__main__':
    main()
