"""
Adaptive Time Stepping for HYDRUS1D Phase 3
============================================

Automatic time step control for Richards equation solver.

Author: HYDRUS1DPy Development Team

References
----------
Huang, K., Mohanty, B. P., & van Genuchten, M. Th. (1996).
A new convergence criterion for the modified Picard iteration method
to solve the variably saturated flow equation.
Journal of Hydrology, 178(1-4), 69-91.
"""

import numpy as np
from typing import Tuple


class AdaptiveTimeStepper:
    """
    Adaptive time step controller for Richards equation.

    Adjusts time step based on:
    - Picard iteration count (more iterations → smaller dt)
    - Solution changes (large changes → smaller dt)
    - Mass balance errors (large errors → smaller dt)
    - User-specified constraints (dt_min, dt_max)

    Parameters
    ----------
    dt_min : float
        Minimum allowed time step [days]
    dt_max : float
        Maximum allowed time step [days]
    dt_init : float
        Initial time step [days]
    dt_decrease_factor : float, optional
        Factor to decrease dt on failure (default: 0.5)
    dt_increase_factor : float, optional
        Factor to increase dt on success (default: 1.3)
    optimal_iter_min : int, optional
        Target minimum iteration count (default: 3)
    optimal_iter_max : int, optional
        Target maximum iteration count (default: 7)

    Attributes
    ----------
    dt_current : float
        Current time step size
    n_accepted : int
        Number of accepted time steps
    n_rejected : int
        Number of rejected time steps

    Notes
    -----
    Time step adjustment strategy (after Huang et al., 1996):

    - If n_iter < optimal_iter_min: dt → dt * increase_factor
    - If n_iter > optimal_iter_max: dt → dt * decrease_factor
    - Otherwise: keep dt unchanged

    Additionally:
    - If Picard fails to converge: dt → dt * decrease_factor
    - Never exceed dt_max or go below dt_min
    - Gradual adjustment prevents oscillations
    """

    def __init__(
        self,
        dt_min: float,
        dt_max: float,
        dt_init: float,
        dt_decrease_factor: float = 0.5,
        dt_increase_factor: float = 1.3,
        optimal_iter_min: int = 3,
        optimal_iter_max: int = 7
    ):
        # Validate inputs
        if dt_min <= 0:
            raise ValueError("dt_min must be > 0")
        if dt_max < dt_min:
            raise ValueError("dt_max must be >= dt_min")
        if not (dt_min <= dt_init <= dt_max):
            raise ValueError("dt_init must be between dt_min and dt_max")
        if not (0 < dt_decrease_factor < 1):
            raise ValueError("dt_decrease_factor must be in (0, 1)")
        if dt_increase_factor <= 1:
            raise ValueError("dt_increase_factor must be > 1")
        if optimal_iter_min < 1:
            raise ValueError("optimal_iter_min must be >= 1")
        if optimal_iter_max <= optimal_iter_min:
            raise ValueError("optimal_iter_max must be > optimal_iter_min")

        self.dt_min = dt_min
        self.dt_max = dt_max
        self.dt_current = dt_init
        self.dt_decrease_factor = dt_decrease_factor
        self.dt_increase_factor = dt_increase_factor
        self.optimal_iter_min = optimal_iter_min
        self.optimal_iter_max = optimal_iter_max

        # Statistics
        self.n_accepted = 0
        self.n_rejected = 0
        self.iteration_history = []
        self.dt_history = []

    def adjust_timestep(
        self,
        dt: float,
        n_iter: int,
        converged: bool = True,
        max_change: float = None,
        mass_balance_error: float = None
    ) -> Tuple[float, str]:
        """
        Adjust time step based on iteration performance.

        Parameters
        ----------
        dt : float
            Current time step that was just attempted
        n_iter : int
            Number of Picard iterations used
        converged : bool, optional
            Whether Picard iteration converged (default: True)
        max_change : float, optional
            Maximum change in solution (for additional control)
        mass_balance_error : float, optional
            Relative mass balance error (for additional control)

        Returns
        -------
        dt_new : float
            Recommended time step for next attempt
        reason : str
            Explanation of adjustment decision
        """
        dt_new = dt
        reason = "unchanged"

        # Record statistics
        self.iteration_history.append(n_iter)
        self.dt_history.append(dt)

        if converged:
            self.n_accepted += 1

            # Adjust based on iteration count
            if n_iter < self.optimal_iter_min:
                # Too few iterations - can increase dt
                dt_new = min(dt * self.dt_increase_factor, self.dt_max)
                reason = f"increased (only {n_iter} iterations)"

            elif n_iter > self.optimal_iter_max:
                # Too many iterations - should decrease dt
                dt_new = max(dt * self.dt_decrease_factor, self.dt_min)
                reason = f"decreased ({n_iter} iterations)"

            else:
                # Optimal iteration count - maintain dt
                reason = f"optimal ({n_iter} iterations)"

            # Additional checks
            if max_change is not None and max_change > 100.0:  # cm
                # Very large pressure changes - be more conservative
                dt_new = max(dt_new * 0.8, self.dt_min)
                reason += f", large change ({max_change:.1f} cm)"

            if mass_balance_error is not None and abs(mass_balance_error) > 0.01:
                # Significant mass balance error
                dt_new = max(dt_new * 0.8, self.dt_min)
                reason += f", mass error ({mass_balance_error:.2e})"

        else:
            # Failed to converge - reduce dt significantly
            self.n_rejected += 1
            dt_new = max(dt * self.dt_decrease_factor, self.dt_min)
            reason = f"reduced (non-convergence after {n_iter} iterations)"

            # If at minimum dt and still failing, this is critical
            if dt_new == self.dt_min:
                reason += " [WARNING: at dt_min]"

        # Ensure bounds
        dt_new = np.clip(dt_new, self.dt_min, self.dt_max)

        self.dt_current = dt_new

        return dt_new, reason

    def suggest_initial_dt(self, h_init: np.ndarray, dz: float) -> float:
        """
        Suggest initial time step based on domain properties.

        Parameters
        ----------
        h_init : ndarray
            Initial pressure head profile [cm]
        dz : float
            Spatial discretization [cm]

        Returns
        -------
        dt_suggest : float
            Suggested initial time step [days]

        Notes
        -----
        Uses a heuristic based on the diffusion CFL condition:
        dt ~ dz^2 / (2 * K_max)

        This is conservative for the implicit solver but helps
        start with a reasonable time step.
        """
        # Estimate maximum conductivity (assuming near saturation)
        # For now, use a typical value - could be improved with
        # actual hydraulic model information
        K_typical = 100.0  # cm/day (reasonable for many soils)

        # Diffusion CFL criterion
        dt_cfl = dz**2 / (2.0 * K_typical)

        # Start with 10x the CFL limit (since we're implicit)
        dt_suggest = min(10.0 * dt_cfl, self.dt_max)
        dt_suggest = max(dt_suggest, self.dt_min)

        return dt_suggest

    def reset_statistics(self):
        """Reset acceptance/rejection counters and history."""
        self.n_accepted = 0
        self.n_rejected = 0
        self.iteration_history = []
        self.dt_history = []

    def get_statistics(self) -> dict:
        """
        Get time stepping statistics.

        Returns
        -------
        stats : dict
            Dictionary with timing statistics
        """
        total_steps = self.n_accepted + self.n_rejected

        if total_steps > 0:
            acceptance_rate = self.n_accepted / total_steps
        else:
            acceptance_rate = 0.0

        if len(self.iteration_history) > 0:
            avg_iterations = np.mean(self.iteration_history)
            max_iterations = np.max(self.iteration_history)
        else:
            avg_iterations = 0.0
            max_iterations = 0

        stats = {
            'n_accepted': self.n_accepted,
            'n_rejected': self.n_rejected,
            'acceptance_rate': acceptance_rate,
            'avg_iterations': avg_iterations,
            'max_iterations': max_iterations,
            'current_dt': self.dt_current,
            'dt_min_used': min(self.dt_history) if self.dt_history else None,
            'dt_max_used': max(self.dt_history) if self.dt_history else None
        }

        return stats

    def __repr__(self):
        return (
            f"AdaptiveTimeStepper("
            f"dt_range=[{self.dt_min:.2e}, {self.dt_max:.2e}], "
            f"current={self.dt_current:.2e}, "
            f"accepted={self.n_accepted}, "
            f"rejected={self.n_rejected})"
        )
