"""
Physical Consistency Tests for HYDRUS1D Phase 3
================================================

Tests that verify physical consistency and real-world behavior
rather than atomic technical checks.

These tests focus on:
1. Conservation laws (mass balance)
2. Physical bounds (0 <= theta <= theta_s, K >= 0, etc.)
3. Monotonicity and causality
4. Realistic scenarios
"""

import numpy as np
import sys
from pathlib import Path

# Add packages to path
phase3_path = str(Path(__file__).parent.parent)
sys.path.insert(0, phase3_path)

from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten, BrooksCorey


class PhysicalTest:
    """Base class for physical consistency tests."""
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.details = []

    def run(self):
        """Run test and return True if passed."""
        raise NotImplementedError

    def report(self):
        """Print test results."""
        status = "PASS" if self.passed else "FAIL"
        print(f"\n{status}: {self.name}")
        for detail in self.details:
            print(f"  {detail}")


class MassConservationTest(PhysicalTest):
    """Test that mass is conserved throughout simulation."""

    def __init__(self, tolerance=0.05):
        super().__init__("Mass Conservation")
        self.tolerance = tolerance  # 5% tolerance

    def run(self):
        print(f"\nRunning: {self.name}")
        print("-" * 70)

        # Test multiple scenarios
        scenarios = [
            ("Constant infiltration", {'flux': 2.0, 'h_init': -100}),
            ("Strong infiltration", {'flux': 10.0, 'h_init': -200}),
            ("Drainage", {'flux': 0.0, 'h_init': -20}),
            ("Evaporation", {'flux': -1.0, 'h_init': -50}),
        ]

        all_pass = True
        for scenario_name, params in scenarios:
            vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

            model = HydrusModel(depth=100.0, n_nodes=51, material=vg)
            model.set_top_bc('flux', flux=params['flux'])
            model.set_bottom_bc('free_drainage')
            model.set_initial_conditions('uniform', h=params['h_init'])

            results = model.run(t_end=1.0, dt_init=0.01, dt_max=0.1, verbose=False)

            # Check mass balance
            mb = results['mass_balance']
            final_error = abs(mb['error'][-1])
            infiltrated = abs(mb['flux_top'][-1])

            if infiltrated > 0.1:
                rel_error = final_error / infiltrated
            else:
                rel_error = final_error

            passed = rel_error < self.tolerance
            all_pass = all_pass and passed

            status = "OK" if passed else "X"
            self.details.append(
                f"{status} {scenario_name}: {rel_error*100:.2f}% error "
                f"(infiltrated={infiltrated:.2f} cm)"
            )

        self.passed = all_pass
        return self.passed


class WaterContentBoundsTest(PhysicalTest):
    """Test that water content stays within physical bounds."""

    def __init__(self):
        super().__init__("Water Content Physical Bounds")

    def run(self):
        print(f"\nRunning: {self.name}")
        print("-" * 70)

        # Test extreme scenarios
        scenarios = [
            ("Dry to wet", -500, 15.0),
            ("Near saturation", -10, 5.0),
            ("Drainage from wet", -20, 0.0),
        ]

        all_pass = True
        for scenario_name, h_init, flux in scenarios:
            vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

            model = HydrusModel(depth=100.0, n_nodes=51, material=vg)
            model.set_top_bc('flux', flux=flux)
            model.set_bottom_bc('free_drainage')
            model.set_initial_conditions('uniform', h=h_init)

            results = model.run(t_end=0.5, dt_init=0.001, dt_max=0.05, verbose=False)

            # Check all profiles
            for i, theta_profile in enumerate(results['theta']):
                # Check theta_r <= theta <= theta_s
                within_bounds = np.all((vg.theta_r - 1e-6 <= theta_profile) &
                                       (theta_profile <= vg.theta_s + 1e-6))

                if not within_bounds:
                    min_theta = np.min(theta_profile)
                    max_theta = np.max(theta_profile)
                    self.details.append(
                        f"X {scenario_name} at t={results['times'][i]:.3f}: "
                        f"theta in [{min_theta:.4f}, {max_theta:.4f}] "
                        f"(bounds: [{vg.theta_r:.4f}, {vg.theta_s:.4f}])"
                    )
                    all_pass = False
                    break

            if within_bounds:
                self.details.append(f"OK {scenario_name}: theta in [theta_r, theta_s] always")

        self.passed = all_pass
        return self.passed


class MonotonicityTest(PhysicalTest):
    """Test causality and monotonicity properties."""

    def __init__(self):
        super().__init__("Monotonicity and Causality")

    def run(self):
        print(f"\nRunning: {self.name}")
        print("-" * 70)

        vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

        # Test 1: Infiltration should increase water content
        model = HydrusModel(depth=100.0, n_nodes=51, material=vg)
        model.set_top_bc('flux', flux=5.0)
        model.set_bottom_bc('free_drainage')
        model.set_initial_conditions('uniform', h=-100.0)

        results = model.run(t_end=1.0, dt_init=0.01, dt_max=0.1, verbose=False)

        # Surface should get wetter over time
        theta_surface = [theta_prof[0] for theta_prof in results['theta']]
        increasing = all(theta_surface[i] <= theta_surface[i+1] + 1e-6
                        for i in range(len(theta_surface)-1))

        if increasing:
            self.details.append(
                f"OK Infiltration causes monotonic increase in surface theta: "
                f"{theta_surface[0]:.4f} -> {theta_surface[-1]:.4f}"
            )
        else:
            self.details.append("X Infiltration did not monotonically increase theta")

        # Test 2: Drainage should decrease water content
        model2 = HydrusModel(depth=100.0, n_nodes=51, material=vg)
        model2.set_top_bc('flux', flux=0.0)
        model2.set_bottom_bc('free_drainage')
        model2.set_initial_conditions('uniform', h=-20.0)

        results2 = model2.run(t_end=1.0, dt_init=0.01, dt_max=0.1, verbose=False)

        # Average theta should decrease
        theta_avg_initial = np.mean(results2['theta'][0])
        theta_avg_final = np.mean(results2['theta'][-1])
        decreasing = theta_avg_final <= theta_avg_initial

        if decreasing:
            self.details.append(
                f"OK Drainage causes decrease in average theta: "
                f"{theta_avg_initial:.4f} -> {theta_avg_final:.4f}"
            )
        else:
            self.details.append("X Drainage did not decrease average theta")

        self.passed = increasing and decreasing
        return self.passed


class ConductivityConsistencyTest(PhysicalTest):
    """Test hydraulic conductivity consistency."""

    def __init__(self):
        super().__init__("Hydraulic Conductivity Consistency")

    def run(self):
        print(f"\nRunning: {self.name}")
        print("-" * 70)

        # Test that K is always positive and bounded
        materials = [
            ("van Genuchten (Loam)", VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)),
            ("Brooks-Corey (Sand)", BrooksCorey(0.045, 0.43, -6.9, 2.0, 29.7, 0.5)),  # hb must be negative (air-entry)
        ]

        all_pass = True
        for mat_name, material in materials:
            # Test K at various h values
            h_values = np.linspace(-1000, 0, 100)
            K_values = np.array([material.conductivity(h) for h in h_values])

            # Check K > 0
            positive = np.all(K_values > 0)

            # Check K <= Ks
            bounded = np.all(K_values <= material.Ks * 1.001)  # Small tolerance

            # Check K increases with h (wetter = more conductive)
            monotonic = np.all(np.diff(K_values) >= -1e-10)  # Allow tiny numerical errors

            if positive and bounded and monotonic:
                self.details.append(
                    f"OK {mat_name}: K in (0, Ks], monotonic increasing with h"
                )
            else:
                issues = []
                if not positive: issues.append("not always positive")
                if not bounded: issues.append(f"exceeds Ks ({np.max(K_values):.2f} > {material.Ks:.2f})")
                if not monotonic: issues.append("not monotonic")
                self.details.append(f"X {mat_name}: {', '.join(issues)}")
                all_pass = False

        self.passed = all_pass
        return self.passed


class LayeredSoilTest(PhysicalTest):
    """Test realistic layered soil scenario."""

    def __init__(self):
        super().__init__("Layered Soil Profile")

    def run(self):
        print(f"\nRunning: {self.name}")
        print("-" * 70)

        # Create 3-layer soil: Sand over Loam over Clay
        sand = VanGenuchten(0.045, 0.43, 0.145, 2.68, 29.7, 0.5)
        loam = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)
        clay = VanGenuchten(0.068, 0.38, 0.008, 1.09, 4.8, 0.5)

        # 100 cm profile: 0-30 sand, 30-70 loam, 70-100 clay
        depths = np.linspace(0, -100, 101)
        materials = {}
        for i, z in enumerate(depths):
            if z >= -30:
                materials[i] = sand
            elif z >= -70:
                materials[i] = loam
            else:
                materials[i] = clay

        from hydrus1dpy import RichardsSolver1D, ConstantFluxBC, FreeDrainageBC

        bc_top = ConstantFluxBC('top', flux=5.0)  # Infiltration
        bc_bottom = FreeDrainageBC('bottom')

        solver = RichardsSolver1D(depths, materials, bc_top, bc_bottom)

        # Start with hydrostatic equilibrium
        h_init = np.array([z - 50 for z in depths])  # Water table at -50 cm

        try:
            results = solver.solve(
                h_init=h_init,
                t_end=1.0,
                dt_init=0.001,
                dt_max=0.05,
                verbose=False
            )

            # Check for wetting front propagation through layers
            theta_initial = results['theta'][0]
            theta_final = results['theta'][-1]

            # Sand layer (top) should wet up significantly
            sand_wetted = np.mean(theta_final[:30]) > np.mean(theta_initial[:30]) + 0.01

            # Check mass balance
            mb_error = abs(results['mass_balance']['error'][-1])
            mb_good = mb_error < 5.0  # cm

            if sand_wetted and mb_good:
                self.details.append("OK Wetting front propagates through layered profile")
                self.details.append(f"OK Mass balance error: {mb_error:.4f} cm")
                self.passed = True
            else:
                if not sand_wetted:
                    self.details.append("X No significant wetting in sand layer")
                if not mb_good:
                    self.details.append(f"X Poor mass balance: {mb_error:.2f} cm error")
                self.passed = False

        except Exception as e:
            self.details.append(f"X Simulation failed: {str(e)[:60]}")
            self.passed = False

        return self.passed


class PondingTest(PhysicalTest):
    """Test realistic ponding/infiltration scenario."""

    def __init__(self):
        super().__init__("Surface Ponding During Intense Rain")

    def run(self):
        print(f"\nRunning: {self.name}")
        print("-" * 70)

        # Clay loam with low conductivity
        clay_loam = VanGenuchten(0.095, 0.410, 0.019, 1.31, 6.24, 0.5)

        # Intense rainfall: 50 mm/hr = 120 cm/day
        # Soil can't infiltrate this fast, should reach ponding

        model = HydrusModel(depth=50.0, n_nodes=51, material=clay_loam)
        model.set_top_bc('flux', flux=120.0)  # Very high flux
        model.set_bottom_bc('free_drainage')
        model.set_initial_conditions('uniform', h=-100.0)

        results = model.run(t_end=0.1, dt_init=0.0001, dt_max=0.01, verbose=False)

        # Surface should approach saturation (ponding)
        h_surface_final = results['h'][-1][0]
        theta_surface_final = results['theta'][-1][0]

        # Should be very wet (near saturation)
        near_saturation = theta_surface_final > clay_loam.theta_s * 0.95

        # Or actually ponding (h > 0)
        ponding = h_surface_final > -1.0

        if near_saturation or ponding:
            self.details.append(
                f"OK Surface approaches saturation: theta={theta_surface_final:.4f} "
                f"(theta_s={clay_loam.theta_s:.4f}), h={h_surface_final:.1f} cm"
            )
            self.passed = True
        else:
            self.details.append(
                f"X Surface not saturated: theta={theta_surface_final:.4f}, "
                f"h={h_surface_final:.1f} cm"
            )
            self.passed = False

        return self.passed


def run_all_tests():
    """Run all physical consistency tests."""

    print("\n" + "="*70)
    print("PHYSICAL CONSISTENCY TESTS - Real-World Functionality")
    print("="*70)
    print("\nFocus: Physical behavior, conservation laws, realistic scenarios")
    print("(Not atomic technical checks)")

    tests = [
        MassConservationTest(),
        WaterContentBoundsTest(),
        MonotonicityTest(),
        ConductivityConsistencyTest(),
        LayeredSoilTest(),
        PondingTest(),
    ]

    # Run all tests
    for test in tests:
        test.run()
        test.report()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for t in tests if t.passed)
    total = len(tests)

    print(f"\nPassed: {passed}/{total} tests")

    if passed == total:
        print("\nOKOKOK All physical consistency tests passed! OKOKOK")
        print("The solver produces physically realistic results.")
    else:
        print("\nWARNING: Some tests failed. Review details above.")

    return tests


if __name__ == '__main__':
    tests = run_all_tests()
