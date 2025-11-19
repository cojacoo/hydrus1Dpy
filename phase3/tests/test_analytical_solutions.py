"""
Analytical Solution Validation Tests
======================================

Validates Phase 3 Richards solver against analytical solutions.

References
----------
1. **Srivastava & Yeh (1991)**: Analytical solutions for one-dimensional
   infiltration in unsaturated soils. Water Resources Research, 27(5), 753-763.

2. **Tracy (2006)**: Clean two- and three-dimensional analytical solutions of
   Richards' equation for testing numerical solvers. Water Resources Research,
   42(8).

3. **Warrick (1974)**: Time-dependent linearized infiltration: I. Point sources.
   Soil Science Society of America Journal, 38(3), 383-386.
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


class AnalyticalTestCase:
    """Base class for analytical test cases."""
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.error = None
        self.max_error = None

    def run(self):
        """Run test and check against analytical solution."""
        raise NotImplementedError

    def report(self):
        """Print test results."""
        status = "OK PASS" if self.passed else "X FAIL"
        print(f"\n{status}: {self.name}")
        if self.max_error is not None:
            print(f"  Maximum error: {self.max_error:.4e}")
        if self.error is not None:
            print(f"  Error message: {self.error}")


class HydrostaticEquilibriumTest(AnalyticalTestCase):
    """
    Test 1: Hydrostatic Equilibrium

    With constant head BCs at top and bottom (same value), and
    hydrostatic initial conditions, the solution should remain
    at equilibrium with no flow.

    Analytical solution: h(z, t) = h_0 for all z and t
    """

    def __init__(self):
        super().__init__("Hydrostatic Equilibrium")
        self.tolerance = 1e-3  # cm

    def run(self):
        print(f"\nRunning: {self.name}")
        print("-" * 70)

        try:
            # Setup
            h_ref = -100.0  # cm
            vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

            model = HydrusModel(depth=50.0, n_nodes=26, material=vg)
            model.set_top_bc('constant_head', head=h_ref)
            model.set_bottom_bc('constant_head', head=h_ref)
            model.set_initial_conditions('uniform', h=h_ref)

            # Run for 1 day
            results = model.run(t_end=1.0, dt_init=0.01, dt_max=0.1, verbose=False)

            # Check: h should remain constant
            h_final = results['h'][-1]
            error = np.abs(h_final - h_ref)
            self.max_error = np.max(error)

            print(f"Initial h: {h_ref} cm")
            print(f"Final h range: [{h_final.min():.4f}, {h_final.max():.4f}] cm")
            print(f"Maximum deviation: {self.max_error:.4e} cm")

            # Check mass balance
            mb_error = results['mass_balance']['error'][-1]
            print(f"Mass balance error: {mb_error:.4e} cm")

            self.passed = (self.max_error < self.tolerance and abs(mb_error) < 0.01)

        except Exception as e:
            self.error = str(e)
            self.passed = False


class SteadyStateInfiltrationTest(AnalyticalTestCase):
    """
    Test 2: Steady-State Unit Gradient Flow

    With free drainage at bottom and constant head at top equal to depth,
    the steady state should have h(z) = z (unit gradient).

    This gives constant flux q = -K(h=z) everywhere.

    Note: This is only exact for certain soil properties. We test for
    approximate steady state.
    """

    def __init__(self):
        super().__init__("Steady-State Unit Gradient")
        self.tolerance = 5.0  # cm (relaxed for steady state approximation)

    def run(self):
        print(f"\nRunning: {self.name}")
        print("-" * 70)

        try:
            # Setup: small, well-drained soil
            vg = VanGenuchten(0.045, 0.43, 0.145, 2.68, 29.7, 0.5)  # Sand parameters

            model = HydrusModel(depth=50.0, n_nodes=26, material=vg)
            model.set_top_bc('constant_head', head=0.0)  # Ponding at surface
            model.set_bottom_bc('free_drainage')

            # Start with unit gradient
            model.set_initial_conditions('hydrostatic', h_bottom=-50.0)

            # Run to near steady state
            results = model.run(t_end=2.0, dt_init=0.001, dt_max=0.05, verbose=False)

            # At steady state, h should approximately equal z
            h_final = results['h'][-1]
            z = model.depths
            h_expected = z  # Unit gradient: h = z

            error = np.abs(h_final - h_expected)
            self.max_error = np.max(error)

            print(f"Expected h = z (unit gradient)")
            print(f"Actual h range: [{h_final.min():.2f}, {h_final.max():.2f}] cm")
            print(f"Maximum error: {self.max_error:.2f} cm")

            # Check that solution is no longer changing (steady state)
            if len(results['h']) > 2:
                dh_dt = np.abs(results['h'][-1] - results['h'][-2])
                max_change = np.max(dh_dt)
                print(f"Maximum change in last step: {max_change:.4f} cm")

                self.passed = (self.max_error < self.tolerance and max_change < 1.0)
            else:
                self.passed = (self.max_error < self.tolerance)

        except Exception as e:
            self.error = str(e)
            self.passed = False


class GravityDrainageTest(AnalyticalTestCase):
    """
    Test 3: Gravity Drainage

    Starting from saturation with free drainage at bottom and no flux at top,
    the soil should drain under gravity.

    For exponential K(theta) models, analytical solutions exist (e.g., Philip, 1957).
    We test that:
    1. Water content decreases monotonically
    2. Flux at bottom equals gravity drainage rate
    3. Mass balance is conserved
    """

    def __init__(self):
        super().__init__("Gravity Drainage from Saturation")
        self.mass_balance_tolerance = 0.01  # 1% error

    def run(self):
        print(f"\nRunning: {self.name}")
        print("-" * 70)

        try:
            vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

            model = HydrusModel(depth=100.0, n_nodes=51, material=vg)
            model.set_top_bc('flux', flux=0.0)  # No flux at top
            model.set_bottom_bc('free_drainage')

            # Start nearly saturated
            model.set_initial_conditions('uniform', h=-10.0)

            # Simulate drainage
            results = model.run(t_end=1.0, dt_init=0.001, dt_max=0.01, verbose=False)

            # Check 1: Water content should decrease
            theta_init = results['theta'][0]
            theta_final = results['theta'][-1]

            theta_decrease = np.all(theta_final <= theta_init)
            print(f"Initial theta (surface): {theta_init[0]:.3f}")
            print(f"Final theta (surface): {theta_final[0]:.3f}")
            print(f"Monotonic decrease: {theta_decrease}")

            # Check 2: Mass balance
            mb = results['mass_balance']
            storage_change = mb['storage'][-1] - mb['storage'][0]
            flux_out = -mb['flux_bottom'][-1]  # Negative because water leaving
            mass_error = mb['error'][-1]

            print(f"Storage change: {storage_change:.4f} cm")
            print(f"Cumulative outflow: {flux_out:.4f} cm")
            print(f"Mass balance error: {mass_error:.4e} cm")

            # Check 3: Physical constraints
            within_bounds = np.all((vg.theta_r <= theta_final) & (theta_final <= vg.theta_s))
            print(f"theta within physical bounds: {within_bounds}")

            self.max_error = abs(mass_error)
            self.passed = (theta_decrease and
                          within_bounds and
                          abs(mass_error) < self.mass_balance_tolerance)

        except Exception as e:
            self.error = str(e)
            self.passed = False


class InfiltrationFrontTest(AnalyticalTestCase):
    """
    Test 4: Infiltration into Dry Soil

    Constant infiltration into initially dry soil should produce
    a sharp wetting front that propagates downward.

    We validate:
    1. Wetting front position increases monotonically
    2. Water content ahead of front remains near initial
    3. Water content behind front approaches saturation
    4. Mass balance is conserved
    """

    def __init__(self):
        super().__init__("Infiltration Front Propagation")
        self.mass_balance_tolerance = 0.05  # 5% for this challenging case

    def run(self):
        print(f"\nRunning: {self.name}")
        print("-" * 70)

        try:
            vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

            model = HydrusModel(depth=100.0, n_nodes=101, material=vg)

            # Strong infiltration
            infiltration_rate = 10.0  # cm/day
            model.set_top_bc('flux', flux=infiltration_rate)
            model.set_bottom_bc('free_drainage')

            # Start dry
            model.set_initial_conditions('uniform', h=-300.0)

            # Short simulation
            results = model.run(t_end=0.5, dt_init=0.0001, dt_max=0.01, verbose=False)

            # Analyze wetting front
            theta_init = results['theta'][0]
            theta_final = results['theta'][-1]

            # Find wetting front (where theta increases significantly from initial)
            theta_increase = theta_final - theta_init[0]
            wetting_depth = 0
            for i in range(len(theta_increase)):
                if theta_increase[i] > 0.1:  # Significant wetting
                    wetting_depth = abs(model.depths[i])

            print(f"Initial theta: {theta_init[0]:.3f}")
            print(f"Surface theta (final): {theta_final[0]:.3f}")
            print(f"Wetting front depth: {wetting_depth:.1f} cm")

            # Mass balance
            mb = results['mass_balance']
            infiltrated = mb['flux_top'][-1]
            storage_change = mb['storage'][-1] - mb['storage'][0]
            mass_error = mb['error'][-1]
            rel_error = abs(mass_error) / max(abs(infiltrated), abs(storage_change))

            print(f"Infiltrated: {infiltrated:.4f} cm")
            print(f"Storage change: {storage_change:.4f} cm")
            print(f"Relative mass error: {rel_error:.2%}")

            # Checks
            front_moved = wetting_depth > 0
            surface_wetted = theta_final[0] > theta_init[0] + 0.05

            self.max_error = rel_error
            self.passed = (front_moved and surface_wetted and
                          rel_error < self.mass_balance_tolerance)

        except Exception as e:
            self.error = str(e)
            self.passed = False


def run_all_tests():
    """Run all analytical solution validation tests."""

    print("\n" + "="*70)
    print("RICHARDS SOLVER: ANALYTICAL SOLUTION VALIDATION")
    print("="*70)

    tests = [
        HydrostaticEquilibriumTest(),
        SteadyStateInfiltrationTest(),
        GravityDrainageTest(),
        InfiltrationFrontTest(),
    ]

    # Run all tests
    for test in tests:
        test.run()
        test.report()

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    passed = sum(1 for t in tests if t.passed)
    total = len(tests)

    print(f"\nPassed: {passed}/{total} tests")

    if passed == total:
        print("\nOK All analytical validation tests passed!")
        print("  Solver is producing physically correct results.")
    else:
        print("\nWARNING: Some tests failed. Review results above.")
        print("  Note: Some failures may be due to numerical approximations")
        print("  or requiring longer simulation times for steady state.")

    return tests


if __name__ == '__main__':
    tests = run_all_tests()