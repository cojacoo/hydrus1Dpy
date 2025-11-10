"""
Richards Equation Solver - Core Implementation
================================================

Mixed-form Richards equation solver using finite differences and Picard iteration.

Governing Equation (Mixed Form):
---------------------------------
C(h) ∂h/∂t = ∂/∂z[K(h)(∂h/∂z + cos(α))] - S(h)

where:
- h: pressure head [cm]
- θ(h): water content from hydraulic model
- C(h) = dθ/dh: specific water capacity [1/cm]
- K(h): hydraulic conductivity [cm/day]
- α: angle from vertical
- S(h): sink term (root uptake) [1/day]

Numerical Method:
-----------------
- Spatial: Finite differences (centered)
- Time: Implicit Euler (backward)
- Linearization: Picard iteration
- Matrix: Tridiagonal (Thomas algorithm)
- Time stepping: Adaptive based on iteration count

References:
-----------
Celia, M. A., Bouloutas, E. T., & Zarba, R. L. (1990). A general mass-conservative
numerical solution for the unsaturated flow equation. Water Resources Research,
26(7), 1483-1496. DOI: 10.1029/WR026i007p01483
"""

# Set up path for Phase 2 import BEFORE any other imports
import sys
from pathlib import Path
_phase2_path = str(Path(__file__).parent.parent.parent.parent / 'phase2')
if _phase2_path not in sys.path:
    sys.path.insert(0, _phase2_path)

from typing import Optional, Dict, List
import numpy as np
from dataclasses import dataclass
import warnings

# Import from Phase 2
from hydrus1dpy.materials import HydraulicModel

from ..numerics.linear_solver import solve_tridiagonal
from ..numerics.time_stepping import AdaptiveTimeStepper
from ..processes.boundary_conditions import BoundaryCondition


@dataclass
class SolverParameters:
    """
    Parameters controlling the numerical solution

    Attributes
    ----------
    max_iterations : int
        Maximum Picard iterations per time step (default: 10)
    tolerance_h : float
        Convergence tolerance for pressure head [cm] (default: 0.1)
    tolerance_theta : float
        Convergence tolerance for water content [-] (default: 0.001)
    max_iter_increase : int
        Maximum iterations before reducing time step (default: 7)
    min_iter_optimal : int
        Minimum iterations for optimal time step (default: 3)
    max_iter_optimal : int
        Maximum iterations for optimal time step (default: 7)
    """
    max_iterations: int = 10
    tolerance_h: float = 0.1
    tolerance_theta: float = 0.001
    max_iter_increase: int = 7
    min_iter_optimal: int = 3
    max_iter_optimal: int = 7
    under_relaxation: float = 1.0  # Under-relaxation factor (1.0 = no relaxation)


class RichardsSolver1D:
    """
    One-dimensional Richards equation solver

    Implements mixed-form Richards equation with:
    - Picard iteration for nonlinearity
    - Adaptive time stepping
    - Mass conservation
    - Flexible boundary conditions
    - Integration with Phase 2 hydraulic models

    Parameters
    ----------
    depths : ndarray
        Node depths [cm], decreasing from surface (e.g., 0, -10, -20, ...)
    materials : dict
        Mapping of node indices to HydraulicModel objects
    bc_top : BoundaryCondition
        Top boundary condition
    bc_bottom : BoundaryCondition
        Bottom boundary condition
    solver_params : SolverParameters, optional
        Numerical solution parameters
    cos_alpha : float, optional
        Cosine of angle from vertical (default: 1.0 for vertical)
    sink : ndarray, optional
        Sink term at each node [1/day] (e.g., root uptake)

    Examples
    --------
    >>> from phase2.hydrus1dpy.materials import VanGenuchten
    >>> from phase3.hydrus1dpy import RichardsSolver1D, ConstantFluxBC, FreeDrainageBC
    >>>
    >>> # Create domain
    >>> depths = np.linspace(0, -100, 101)
    >>>
    >>> # Create hydraulic model
    >>> vg = VanGenuchten(theta_r=0.078, theta_s=0.430,
    ...                   alpha=0.036, n=1.56, Ks=24.96)
    >>>
    >>> # Assign material to all nodes
    >>> materials = {i: vg for i in range(101)}
    >>>
    >>> # Create boundary conditions
    >>> bc_top = ConstantFluxBC(flux=-5.0)  # 5 cm/day infiltration
    >>> bc_bottom = FreeDrainageBC()
    >>>
    >>> # Create solver
    >>> solver = RichardsSolver1D(depths, materials, bc_top, bc_bottom)
    >>>
    >>> # Set initial conditions
    >>> h_init = depths.copy()  # Hydrostatic
    >>>
    >>> # Solve
    >>> results = solver.solve(h_init, t_end=10.0, dt_init=0.01)
    """

    def __init__(self,
                 depths: np.ndarray,
                 materials: Dict[int, HydraulicModel],
                 bc_top: BoundaryCondition,
                 bc_bottom: BoundaryCondition,
                 solver_params: Optional[SolverParameters] = None,
                 cos_alpha: float = 1.0,
                 sink: Optional[np.ndarray] = None):
        """Initialize Richards equation solver"""

        # Domain
        self.depths = np.asarray(depths, dtype=float)
        self.n_nodes = len(depths)
        self.materials = materials

        # Validate depths (should be decreasing: 0, -10, -20, ...)
        if not np.all(np.diff(self.depths) < 0):
            raise ValueError("Depths must be decreasing (surface to bottom)")

        # Boundary conditions
        self.bc_top = bc_top
        self.bc_bottom = bc_bottom

        # Solver parameters
        self.params = solver_params if solver_params is not None else SolverParameters()

        # Geometry
        self.cos_alpha = cos_alpha

        # Calculate grid spacing
        self.dz = np.zeros(self.n_nodes - 1)
        for i in range(self.n_nodes - 1):
            self.dz[i] = abs(self.depths[i+1] - self.depths[i])

        # Sink term (root uptake)
        self.sink = sink if sink is not None else np.zeros(self.n_nodes)

        # State variables (will be set during solve)
        self.h = None  # Pressure head [cm]
        self.theta = None  # Water content [-]
        self.K = None  # Hydraulic conductivity [cm/day]
        self.C = None  # Water capacity [1/cm]

        # Statistics
        self.total_iterations = 0
        self.total_time_steps = 0
        self.rejected_steps = 0

    def solve(self,
              h_init: np.ndarray,
              t_end: float,
              dt_init: float,
              dt_min: float = 1e-6,
              dt_max: float = 1.0,
              output_times: Optional[np.ndarray] = None,
              verbose: bool = False) -> Dict:
        """
        Solve Richards equation from t=0 to t=t_end

        Parameters
        ----------
        h_init : ndarray
            Initial pressure head distribution [cm]
        t_end : float
            End time [days]
        dt_init : float
            Initial time step [days]
        dt_min : float, optional
            Minimum time step [days]
        dt_max : float, optional
            Maximum time step [days]
        output_times : ndarray, optional
            Specific times to save output (if None, saves all steps)
        verbose : bool, optional
            Print progress information

        Returns
        -------
        results : dict
            Dictionary containing:
            - 'times': Array of output times
            - 'h': Pressure head profiles at output times
            - 'theta': Water content profiles at output times
            - 'mass_balance': Mass balance information
            - 'statistics': Solver statistics
        """

        # Initialize
        self.h = h_init.copy()
        self.theta = np.zeros(self.n_nodes)
        self.K = np.zeros(self.n_nodes)
        self.C = np.zeros(self.n_nodes)

        # Update hydraulic properties
        self._update_properties(self.h)

        # Initialize time stepper
        time_stepper = AdaptiveTimeStepper(
            dt_min=dt_min,
            dt_max=dt_max,
            dt_init=dt_init,
            dt_increase_factor=1.3,
            dt_decrease_factor=0.5,
            optimal_iter_min=self.params.min_iter_optimal,
            optimal_iter_max=self.params.max_iter_optimal
        )

        # Storage for results
        if output_times is None:
            # Save every step
            save_every_step = True
            output_times_set = None
        else:
            save_every_step = False
            output_times_set = set(output_times)

        results_times = []
        results_h = []
        results_theta = []

        # Mass balance tracking
        mass_balance = {
            'time': [],
            'storage': [],
            'flux_top': [],
            'flux_bottom': [],
            'sink_total': [],
            'error': []
        }

        # Initial storage
        storage_init = self._calculate_storage()
        cumulative_flux_top = 0.0
        cumulative_flux_bottom = 0.0
        cumulative_sink = 0.0

        # Save initial state
        results_times.append(0.0)
        results_h.append(self.h.copy())
        results_theta.append(self.theta.copy())

        # Time stepping loop
        t = 0.0
        dt = dt_init
        step = 0

        if verbose:
            print(f"{'Step':>6s} {'Time':>10s} {'dt':>10s} {'Iter':>6s} {'Max Δh':>10s} {'Status':>10s}")
            print("-" * 70)

        while t < t_end:
            # Don't overshoot end time
            if t + dt > t_end:
                dt = t_end - t

            # Store old solution
            h_old = self.h.copy()
            theta_old = self.theta.copy()

            # Try time step
            converged, n_iter, max_dh = self._time_step(dt)

            if converged:
                # Accept time step
                t += dt
                step += 1
                self.total_time_steps += 1

                # Calculate fluxes
                flux_top = self._calculate_top_flux(dt)
                flux_bottom = self._calculate_bottom_flux(dt)
                sink_step = np.sum(self.sink * self.theta) * dt  # Simplified

                cumulative_flux_top += flux_top
                cumulative_flux_bottom += flux_bottom
                cumulative_sink += sink_step

                # Mass balance
                storage_current = self._calculate_storage()
                storage_change = storage_current - storage_init
                mass_error = (cumulative_flux_top - cumulative_flux_bottom -
                             cumulative_sink - storage_change)

                # Save if needed
                if save_every_step or (output_times_set and t in output_times_set):
                    results_times.append(t)
                    results_h.append(self.h.copy())
                    results_theta.append(self.theta.copy())

                    mass_balance['time'].append(t)
                    mass_balance['storage'].append(storage_current)
                    mass_balance['flux_top'].append(cumulative_flux_top)
                    mass_balance['flux_bottom'].append(cumulative_flux_bottom)
                    mass_balance['sink_total'].append(cumulative_sink)
                    mass_balance['error'].append(mass_error)

                # Print progress
                if verbose and step % max(1, int(0.1 / dt_init)) == 0:
                    print(f"{step:6d} {t:10.4f} {dt:10.4e} {n_iter:6d} {max_dh:10.4f} {'accepted':>10s}")

                # Adjust time step based on iterations
                dt, reason = time_stepper.adjust_timestep(dt, n_iter, converged=True)

            else:
                # Reject time step
                self.h = h_old
                self.theta = theta_old
                self._update_properties(self.h)
                self.rejected_steps += 1

                # Reduce time step
                dt, reason = time_stepper.adjust_timestep(dt, n_iter, converged=False)
                dt = max(dt, dt_min)

                if verbose:
                    print(f"{step:6d} {t:10.4f} {dt:10.4e} {n_iter:6d} {max_dh:10.4f} {'rejected':>10s}")

                if dt <= dt_min:
                    warnings.warn(f"Minimum time step reached at t={t:.4f}. Solution may be inaccurate.")
                    break

        # Compile results
        results = {
            'times': np.array(results_times),
            'h': np.array(results_h),
            'theta': np.array(results_theta),
            'mass_balance': {k: np.array(v) for k, v in mass_balance.items()},
            'statistics': {
                'total_steps': self.total_time_steps,
                'rejected_steps': self.rejected_steps,
                'total_iterations': self.total_iterations,
                'avg_iterations': self.total_iterations / max(self.total_time_steps, 1)
            }
        }

        if verbose:
            print("-" * 70)
            print(f"Simulation completed: t={t:.4f} days")
            print(f"Total steps: {self.total_time_steps}")
            print(f"Rejected steps: {self.rejected_steps}")
            print(f"Average iterations: {results['statistics']['avg_iterations']:.2f}")

        return results

    def _time_step(self, dt: float) -> tuple:
        """
        Perform one time step using Picard iteration

        Returns
        -------
        converged : bool
            Whether iteration converged
        n_iter : int
            Number of iterations performed
        max_dh : float
            Maximum change in h during last iteration
        """
        h_old = self.h.copy()
        theta_old = self.theta.copy()

        converged = False
        n_iter = 0
        max_dh = np.inf

        for iteration in range(self.params.max_iterations):
            n_iter += 1
            self.total_iterations += 1

            # Store previous iteration
            h_prev = self.h.copy()

            # Assemble and solve linear system
            self._picard_iteration(h_old, theta_old, dt)

            # Under-relaxation if needed
            if self.params.under_relaxation < 1.0:
                self.h = (self.params.under_relaxation * self.h +
                         (1.0 - self.params.under_relaxation) * h_prev)

            # Update properties
            self._update_properties(self.h)

            # Check convergence
            dh = np.abs(self.h - h_prev)
            max_dh = np.max(dh)

            # Water content change
            dtheta = np.abs(self.theta - theta_old)
            max_dtheta = np.max(dtheta)

            # Convergence criteria
            h_converged = max_dh < self.params.tolerance_h
            theta_converged = max_dtheta < self.params.tolerance_theta

            if h_converged or theta_converged:
                converged = True
                break

            # Check for divergence
            if np.any(~np.isfinite(self.h)) or max_dh > 1e6:
                converged = False
                break

        return converged, n_iter, max_dh

    def _picard_iteration(self, h_old: np.ndarray, theta_old: np.ndarray, dt: float):
        """
        One Picard iteration: assemble system and solve

        Mixed form: C(h) dh/dt = d/dz[K(h)(dh/dz + cos(α))] - S

        Discretized implicitly:
        C(h^k) (h^(k+1) - h^n) / dt = [K](dh^(k+1)/dz + cos(α)) - S
        """
        n = self.n_nodes

        # Tridiagonal matrix coefficients
        # Note: solve_tridiagonal expects a[i] for i=0..n-1, where a[0] is unused
        a = np.zeros(n)  # Lower diagonal
        b = np.zeros(n)  # Main diagonal
        c = np.zeros(n)  # Upper diagonal
        d = np.zeros(n)  # Right-hand side

        # Internal nodes
        for i in range(1, n-1):
            # Grid spacing
            dz_minus = self.dz[i-1]  # Distance to node i-1
            dz_plus = self.dz[i]      # Distance to node i+1
            dz_avg = 0.5 * (dz_minus + dz_plus)

            # Internodal conductivities (arithmetic mean)
            K_minus = 0.5 * (self.K[i-1] + self.K[i])
            K_plus = 0.5 * (self.K[i] + self.K[i+1])

            # Coefficients for dh/dz terms
            a_minus = K_minus / (dz_minus * dz_avg)
            a_plus = K_plus / (dz_plus * dz_avg)

            # Matrix coefficients
            a[i] = -a_minus       # Lower diagonal
            b[i] = self.C[i] / dt + a_minus + a_plus  # Main diagonal
            c[i] = -a_plus        # Upper diagonal

            # Right-hand side
            gravity_term = (K_plus - K_minus) / dz_avg * self.cos_alpha
            d[i] = self.C[i] * h_old[i] / dt + gravity_term - self.sink[i]

        # Boundary conditions
        # Note: For our coordinate system, node 0 is at the top (surface)
        # and node n-1 is at the bottom

        # Top boundary (i=0, surface)
        if self.bc_top.location != 'top':
            raise ValueError("Top BC must have location='top'")
        dz_surface = self.dz[0]
        self.bc_top.apply(a, b, c, d, self.h, self.K, dz_surface, 0.0)

        # Bottom boundary (i=n-1)
        if self.bc_bottom.location != 'bottom':
            raise ValueError("Bottom BC must have location='bottom'")
        dz_bottom = self.dz[-1]
        self.bc_bottom.apply(a, b, c, d, self.h, self.K, dz_bottom, 0.0)

        # Solve tridiagonal system
        self.h = solve_tridiagonal(a, b, c, d)

    def _update_properties(self, h: np.ndarray):
        """Update hydraulic properties from pressure head"""
        for i in range(self.n_nodes):
            material = self.materials[i]
            self.theta[i] = material.water_content(h[i])
            self.K[i] = material.conductivity(h[i])
            self.C[i] = material.capacity(h[i])

    def _calculate_storage(self) -> float:
        """Calculate total water storage in profile [cm]"""
        storage = 0.0
        for i in range(self.n_nodes - 1):
            dz = self.dz[i]
            theta_avg = 0.5 * (self.theta[i] + self.theta[i+1])
            storage += theta_avg * dz
        return storage

    def _calculate_top_flux(self, dt: float) -> float:
        """Calculate flux at top boundary [cm]"""
        # Get flux and integrate over time step
        dz = self.dz[0]
        flux_rate = self.bc_top.get_flux(self.h, self.K, dz, 0.0)  # [cm/day]
        return flux_rate * dt  # [cm]

    def _calculate_bottom_flux(self, dt: float) -> float:
        """Calculate flux at bottom boundary [cm]"""
        dz = self.dz[-1]
        flux_rate = self.bc_bottom.get_flux(self.h, self.K, dz, 0.0)  # [cm/day]
        return flux_rate * dt  # [cm]
