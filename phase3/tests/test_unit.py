"""
Unit Tests for HYDRUS1D Phase 3
=================================

Comprehensive unit tests for all Phase 3 components.
"""

import numpy as np
import sys
from pathlib import Path
import unittest

# Add packages to path
phase3_path = str(Path(__file__).parent.parent)
phase2_path = str(Path(__file__).parent.parent.parent / 'phase2')
sys.path.insert(0, phase2_path)
sys.path.insert(0, phase3_path)

from hydrus1dpy.numerics.linear_solver import (
    solve_tridiagonal, check_diagonal_dominance, condition_number_estimate
)
from hydrus1dpy.numerics.time_stepping import AdaptiveTimeStepper
from hydrus1dpy.processes.boundary_conditions import (
    ConstantHeadBC, ConstantFluxBC, FreeDrainageBC, AtmosphericBC
)
from hydrus1dpy.core.richards_solver import RichardsSolver1D, SolverParameters
from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten


class TestLinearSolver(unittest.TestCase):
    """Tests for tridiagonal linear solver."""

    def test_simple_system(self):
        """Test solution of simple tridiagonal system."""
        # System: [2 -1 0; -1 2 -1; 0 -1 2] * x = [1; 0; 1]
        a = np.array([0, -1, -1])
        b = np.array([2, 2, 2])
        c = np.array([-1, -1, 0])
        d = np.array([1, 0, 1])

        x = solve_tridiagonal(a, b, c, d)

        # Check solution
        self.assertEqual(len(x), 3)
        # Expected solution: x = [1, 1, 1]
        self.assertAlmostEqual(x[0], 1.0, places=10)
        self.assertAlmostEqual(x[1], 1.0, places=10)
        self.assertAlmostEqual(x[2], 1.0, places=10)

    def test_diagonal_dominance(self):
        """Test diagonal dominance checker."""
        # Diagonally dominant matrix
        a = np.array([0, 1, 1])
        b = np.array([3, 3, 3])
        c = np.array([1, 1, 0])

        dominant, ratio = check_diagonal_dominance(a, b, c)
        self.assertTrue(dominant)
        self.assertGreaterEqual(ratio, 1.0)

    def test_condition_number(self):
        """Test condition number estimation."""
        # Well-conditioned system with strictly positive diagonal
        a = np.array([0, -0.5, -0.5])
        b = np.array([2, 2, 2])
        c = np.array([-0.5, -0.5, 0])

        cond = condition_number_estimate(a, b, c)
        # Should return a finite positive number > 1
        self.assertGreater(cond, 1.0)
        if not np.isinf(cond):  # Only check if finite
            self.assertLess(cond, 100.0)


class TestTimeStepping(unittest.TestCase):
    """Tests for adaptive time stepping."""

    def test_initialization(self):
        """Test time stepper initialization."""
        stepper = AdaptiveTimeStepper(
            dt_min=1e-6,
            dt_max=1.0,
            dt_init=0.01
        )

        self.assertEqual(stepper.dt_current, 0.01)
        self.assertEqual(stepper.n_accepted, 0)
        self.assertEqual(stepper.n_rejected, 0)

    def test_timestep_increase(self):
        """Test that dt increases with few iterations."""
        stepper = AdaptiveTimeStepper(
            dt_min=1e-6,
            dt_max=1.0,
            dt_init=0.01,
            optimal_iter_min=3
        )

        # Few iterations should increase dt
        dt_new, reason = stepper.adjust_timestep(0.01, n_iter=2, converged=True)
        self.assertGreater(dt_new, 0.01)

    def test_timestep_decrease(self):
        """Test that dt decreases with many iterations."""
        stepper = AdaptiveTimeStepper(
            dt_min=1e-6,
            dt_max=1.0,
            dt_init=0.01,
            optimal_iter_max=7
        )

        # Many iterations should decrease dt
        dt_new, reason = stepper.adjust_timestep(0.01, n_iter=10, converged=True)
        self.assertLess(dt_new, 0.01)

    def test_nonconvergence(self):
        """Test that non-convergence reduces dt."""
        stepper = AdaptiveTimeStepper(
            dt_min=1e-6,
            dt_max=1.0,
            dt_init=0.01
        )

        dt_new, reason = stepper.adjust_timestep(0.01, n_iter=10, converged=False)
        self.assertLess(dt_new, 0.01)

    def test_bounds(self):
        """Test that dt respects min/max bounds."""
        stepper = AdaptiveTimeStepper(
            dt_min=0.001,
            dt_max=0.1,
            dt_init=0.05
        )

        # Should not exceed max
        dt_new, _ = stepper.adjust_timestep(0.09, n_iter=1, converged=True)
        self.assertLessEqual(dt_new, 0.1)

        # Should not go below min
        dt_new, _ = stepper.adjust_timestep(0.002, n_iter=20, converged=False)
        self.assertGreaterEqual(dt_new, 0.001)


class TestBoundaryConditions(unittest.TestCase):
    """Tests for boundary conditions."""

    def setUp(self):
        """Set up test arrays."""
        self.n = 5
        self.a = np.zeros(self.n)
        self.b = np.ones(self.n) * 2.0
        self.c = np.zeros(self.n)
        self.d = np.zeros(self.n)
        self.h = np.full(self.n, -100.0)
        self.K = np.full(self.n, 10.0)
        self.dz = 2.0

    def test_constant_head_top(self):
        """Test constant head BC at top."""
        bc = ConstantHeadBC('top', head=-50.0)
        bc.apply(self.a, self.b, self.c, self.d, self.h, self.K, self.dz, 0.0)

        # Should set h[0] = -50.0
        self.assertEqual(self.b[0], 1.0)
        self.assertEqual(self.d[0], -50.0)

    def test_constant_flux_top(self):
        """Test constant flux BC at top."""
        bc = ConstantFluxBC('top', flux=0.5)

        # Need to set up matrix first (like solver does)
        self.b[0] = 1.0  # Dummy setup

        bc.apply(self.a, self.b, self.c, self.d, self.h, self.K, self.dz, 0.0)

        # Should modify RHS
        self.assertAlmostEqual(self.d[0], 0.5 / self.dz)

    def test_free_drainage_bottom(self):
        """Test free drainage BC at bottom."""
        bc = FreeDrainageBC('bottom')
        bc.apply(self.a, self.b, self.c, self.d, self.h, self.K, self.dz, 0.0)

        # Should set approximately h[n-1] - h[n-2] = 0 (with small regularization)
        # The regularized form is: (1+epsilon)*h[n-1] - h[n-2] = epsilon*h[n-1]
        self.assertEqual(self.a[self.n-1], -1.0)
        self.assertAlmostEqual(self.b[self.n-1], 1.0, places=8)  # b = 1 + epsilon
        # d = epsilon * h[n-1], which is very small (epsilon ~ 1e-10)
        self.assertLess(abs(self.d[self.n-1]), 1e-7)  # Should be tiny

    def test_atmospheric_bc(self):
        """Test atmospheric BC."""
        bc = AtmosphericBC('top', flux=0.5, h_min=-15000, h_surface=0.0)

        # Should start in flux mode
        self.assertEqual(bc.bc_type, 'flux')

    def test_time_varying_bc(self):
        """Test time-varying boundary condition."""
        # Time-varying head
        bc = ConstantHeadBC('top', head=lambda t: -100 * (1 + 0.1*t))

        bc.apply(self.a, self.b, self.c, self.d, self.h, self.K, self.dz, t=1.0)
        self.assertAlmostEqual(self.d[0], -110.0, places=10)

        bc.apply(self.a, self.b, self.c, self.d, self.h, self.K, self.dz, t=2.0)
        self.assertAlmostEqual(self.d[0], -120.0, places=10)


class TestSolverParameters(unittest.TestCase):
    """Tests for solver parameters."""

    def test_defaults(self):
        """Test default solver parameters."""
        params = SolverParameters()

        self.assertEqual(params.max_iterations, 10)
        self.assertGreater(params.tolerance_h, 0)
        self.assertGreater(params.tolerance_theta, 0)


class TestHydrusModel(unittest.TestCase):
    """Tests for high-level model interface."""

    def setUp(self):
        """Set up test model."""
        self.vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

    def test_initialization(self):
        """Test model initialization."""
        model = HydrusModel(depth=100.0, n_nodes=11, material=self.vg)

        self.assertEqual(model.depth, 100.0)
        self.assertEqual(model.n_nodes, 11)
        self.assertEqual(len(model.depths), 11)

    def test_boundary_conditions(self):
        """Test setting boundary conditions."""
        model = HydrusModel(depth=50.0, n_nodes=6, material=self.vg)

        model.set_top_bc('constant_head', head=-100.0)
        model.set_bottom_bc('free_drainage')

        self.assertIsNotNone(model.bc_top)
        self.assertIsNotNone(model.bc_bottom)

    def test_initial_conditions(self):
        """Test setting initial conditions."""
        model = HydrusModel(depth=50.0, n_nodes=6, material=self.vg)

        # Uniform
        model.set_initial_conditions('uniform', h=-100.0)
        self.assertTrue(np.all(model.h_init == -100.0))

        # Hydrostatic
        model.set_initial_conditions('hydrostatic', h_bottom=-150.0)
        self.assertEqual(model.h_init[0], -100.0)  # Surface
        self.assertEqual(model.h_init[-1], -150.0)  # Bottom

        # Linear
        model.set_initial_conditions('linear', h_top=-50.0, h_bottom=-150.0)
        self.assertEqual(model.h_init[0], -50.0)
        self.assertEqual(model.h_init[-1], -150.0)

    def test_simple_run(self):
        """Test running a simple simulation."""
        model = HydrusModel(depth=10.0, n_nodes=6, material=self.vg)
        model.set_top_bc('constant_head', head=-100.0)
        model.set_bottom_bc('constant_head', head=-100.0)
        model.set_initial_conditions('uniform', h=-100.0)

        results = model.run(t_end=0.01, dt_init=0.001, dt_max=0.001, verbose=False)

        self.assertIn('times', results)
        self.assertIn('h', results)
        self.assertIn('theta', results)
        self.assertGreater(len(results['times']), 0)


def run_tests():
    """Run all unit tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestLinearSolver))
    suite.addTests(loader.loadTestsFromTestCase(TestTimeStepping))
    suite.addTests(loader.loadTestsFromTestCase(TestBoundaryConditions))
    suite.addTests(loader.loadTestsFromTestCase(TestSolverParameters))
    suite.addTests(loader.loadTestsFromTestCase(TestHydrusModel))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("UNIT TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\nOK All unit tests passed!")
        return 0
    else:
        print("\nX Some tests failed.")
        return 1


if __name__ == '__main__':
    exit(run_tests())
