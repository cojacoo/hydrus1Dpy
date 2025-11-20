"""
High-Level Model Interface for HYDRUS1D Phase 3
================================================

Simplified interface for setting up and running simulations.

Author: HYDRUS1DPy Development Team
"""

# Set up path for Phase 2 import BEFORE any other imports
import sys
from pathlib import Path
_phase2_path = str(Path(__file__).parent.parent.parent.parent / 'phase2')
if _phase2_path not in sys.path:
    sys.path.insert(0, _phase2_path)

import numpy as np
from typing import Optional, Union, Dict, List
from dataclasses import dataclass

# Import from Phase 2
from hydrus1dpy.materials import HydraulicModel

# Optional xarray support
try:
    import xarray as xr
    HAS_XARRAY = True
except ImportError:
    HAS_XARRAY = False

from .richards_solver import RichardsSolver1D, SolverParameters
from ..processes.boundary_conditions import (
    BoundaryCondition, ConstantHeadBC, ConstantFluxBC,
    FreeDrainageBC, AtmosphericBC
)
from ..numerics.time_stepping import AdaptiveTimeStepper


class HydrusModel:
    """
    High-level interface for HYDRUS1D simulations.

    This class simplifies model setup by providing helper methods
    for common tasks like domain creation, material assignment,
    and result visualization.

    Parameters
    ----------
    depth : float
        Total depth of soil profile [cm] (positive value)
    n_nodes : int
        Number of discretization nodes
    material : HydraulicModel or dict
        Either:
        - Single HydraulicModel applied to entire profile
        - Dict mapping depth ranges to materials: {(z_top, z_bot): material}

    Examples
    --------
    >>> from phase2.hydrus1dpy.materials import VanGenuchten
    >>> from phase3.hydrus1dpy import HydrusModel
    >>>
    >>> # Create soil material
    >>> vg_loam = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96)
    >>>
    >>> # Create model with 100 cm profile and 101 nodes
    >>> model = HydrusModel(depth=100, n_nodes=101, material=vg_loam)
    >>>
    >>> # Set boundary conditions
    >>> model.set_top_bc('flux', flux=0.5)  # 0.5 cm/day infiltration
    >>> model.set_bottom_bc('free_drainage')
    >>>
    >>> # Set initial conditions (hydrostatic from -50 cm)
    >>> model.set_initial_conditions('hydrostatic', h_bottom=-50)
    >>>
    >>> # Run simulation
    >>> results = model.run(t_end=10.0, dt_init=0.01)
    >>>
    >>> # Plot results
    >>> model.plot_profile(results, time_index=-1)
    """

    def __init__(
        self,
        depth: float,
        n_nodes: int,
        material: Union[HydraulicModel, Dict[tuple, HydraulicModel]]
    ):
        """Initialize HYDRUS1D model."""

        if depth <= 0:
            raise ValueError("depth must be > 0")
        if n_nodes < 3:
            raise ValueError("n_nodes must be >= 3")

        # Create domain
        self.depth = depth
        self.n_nodes = n_nodes
        self.depths = np.linspace(0, -depth, n_nodes)  # Surface to bottom

        # Assign materials
        if isinstance(material, HydraulicModel):
            # Single material for entire profile
            self.materials = {i: material for i in range(n_nodes)}
        else:
            # Layered materials
            self.materials = self._assign_layered_materials(material)

        # Boundary conditions (defaults)
        self.bc_top = None
        self.bc_bottom = None

        # Initial conditions
        self.h_init = None

        # Solver parameters
        self.solver_params = SolverParameters()

        # Results
        self.results = None
        self.solver = None

    def _assign_layered_materials(
        self,
        material_dict: Dict[tuple, HydraulicModel]
    ) -> Dict[int, HydraulicModel]:
        """
        Assign materials to nodes based on depth ranges.

        Parameters
        ----------
        material_dict : dict
            {(z_top, z_bot): material} where depths are negative
        """
        node_materials = {}

        for i, z in enumerate(self.depths):
            assigned = False
            for (z_top, z_bot), material in material_dict.items():
                if z_bot <= z <= z_top:  # Note: z values are negative
                    node_materials[i] = material
                    assigned = True
                    break

            if not assigned:
                raise ValueError(f"No material assigned for depth z={z:.2f} cm")

        return node_materials

    def set_top_bc(
        self,
        bc_type: str,
        **kwargs
    ):
        """
        Set top boundary condition.

        Parameters
        ----------
        bc_type : str
            Type of boundary condition:
            - 'constant_head': Constant pressure head
            - 'flux': Constant or time-varying flux
            - 'atmospheric': Atmospheric BC with surface ponding
        **kwargs
            Additional parameters for the BC:
            - For 'constant_head': head (float or callable)
            - For 'flux': flux (float or callable)
            - For 'atmospheric': flux, h_min, h_surface

        Examples
        --------
        >>> model.set_top_bc('constant_head', head=-100)
        >>> model.set_top_bc('flux', flux=0.5)
        >>> model.set_top_bc('atmospheric', flux=lambda t: 0.5*np.sin(t))
        """
        if bc_type == 'constant_head':
            self.bc_top = ConstantHeadBC('top', kwargs['head'])

        elif bc_type == 'flux':
            self.bc_top = ConstantFluxBC('top', kwargs['flux'])

        elif bc_type == 'atmospheric':
            self.bc_top = AtmosphericBC(
                'top',
                flux=kwargs['flux'],
                h_min=kwargs.get('h_min', -15000.0),
                h_surface=kwargs.get('h_surface', 0.0)
            )

        else:
            raise ValueError(f"Unknown BC type: {bc_type}")

    def set_bottom_bc(
        self,
        bc_type: str,
        **kwargs
    ):
        """
        Set bottom boundary condition.

        Parameters
        ----------
        bc_type : str
            Type of boundary condition:
            - 'constant_head': Constant pressure head (water table)
            - 'flux': Constant or time-varying flux
            - 'free_drainage': Unit gradient (no capillary gradient)
        **kwargs
            Additional parameters for the BC

        Examples
        --------
        >>> model.set_bottom_bc('free_drainage')
        >>> model.set_bottom_bc('constant_head', head=-200)
        >>> model.set_bottom_bc('flux', flux=-0.1)
        """
        if bc_type == 'constant_head':
            self.bc_bottom = ConstantHeadBC('bottom', kwargs['head'])

        elif bc_type == 'flux':
            self.bc_bottom = ConstantFluxBC('bottom', kwargs['flux'])

        elif bc_type == 'free_drainage':
            self.bc_bottom = FreeDrainageBC('bottom')

        else:
            raise ValueError(f"Unknown BC type: {bc_type}")

    def set_initial_conditions(
        self,
        ic_type: str,
        **kwargs
    ):
        """
        Set initial pressure head distribution.

        Parameters
        ----------
        ic_type : str
            Type of initial condition:
            - 'uniform': Uniform pressure head
            - 'hydrostatic': Hydrostatic equilibrium
            - 'linear': Linear gradient
            - 'custom': User-provided array
        **kwargs
            Additional parameters:
            - For 'uniform': h (float)
            - For 'hydrostatic': h_bottom (float)
            - For 'linear': h_top, h_bottom (float)
            - For 'custom': h (ndarray)

        Examples
        --------
        >>> model.set_initial_conditions('uniform', h=-100)
        >>> model.set_initial_conditions('hydrostatic', h_bottom=-50)
        >>> model.set_initial_conditions('linear', h_top=-10, h_bottom=-200)
        """
        if ic_type == 'uniform':
            h = kwargs['h']
            self.h_init = np.full(self.n_nodes, h)

        elif ic_type == 'hydrostatic':
            # Hydrostatic: h = z - z_ref, where h(z_ref) = h_bottom
            h_bottom = kwargs['h_bottom']
            z_bottom = self.depths[-1]
            self.h_init = self.depths - z_bottom + h_bottom

        elif ic_type == 'linear':
            h_top = kwargs['h_top']
            h_bottom = kwargs['h_bottom']
            self.h_init = np.linspace(h_top, h_bottom, self.n_nodes)

        elif ic_type == 'custom':
            self.h_init = np.asarray(kwargs['h'])
            if len(self.h_init) != self.n_nodes:
                raise ValueError(f"Custom h must have length {self.n_nodes}")

        else:
            raise ValueError(f"Unknown IC type: {ic_type}")

    def set_solver_parameters(
        self,
        max_iterations: int = 10,
        tolerance_h: float = 0.1,
        tolerance_theta: float = 0.001,
        **kwargs
    ):
        """
        Set numerical solver parameters.

        Parameters
        ----------
        max_iterations : int
            Maximum Picard iterations per time step
        tolerance_h : float
            Convergence tolerance for pressure head [cm]
        tolerance_theta : float
            Convergence tolerance for water content [-]
        """
        self.solver_params = SolverParameters(
            max_iterations=max_iterations,
            tolerance_h=tolerance_h,
            tolerance_theta=tolerance_theta,
            **kwargs
        )

    def run(
        self,
        t_end: float,
        dt_init: float,
        dt_min: float = 1e-6,
        dt_max: float = 1.0,
        output_times: Optional[np.ndarray] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Run the simulation.

        Parameters
        ----------
        t_end : float
            End time [days]
        dt_init : float
            Initial time step [days]
        dt_min : float, optional
            Minimum time step [days]
        dt_max : float, optional
            Maximum time step [days]
        output_times : ndarray, optional
            Specific times to save output
        verbose : bool, optional
            Print progress information

        Returns
        -------
        results : dict
            Simulation results containing:
            - times, h, theta, mass_balance, statistics
        """
        # Validate setup
        if self.bc_top is None:
            raise ValueError("Top boundary condition not set. Use set_top_bc()")
        if self.bc_bottom is None:
            raise ValueError("Bottom boundary condition not set. Use set_bottom_bc()")
        if self.h_init is None:
            raise ValueError("Initial conditions not set. Use set_initial_conditions()")

        # Create solver
        self.solver = RichardsSolver1D(
            depths=self.depths,
            materials=self.materials,
            bc_top=self.bc_top,
            bc_bottom=self.bc_bottom,
            solver_params=self.solver_params
        )

        # Run simulation
        if verbose:
            print("=" * 70)
            print("HYDRUS1D Phase 3 - Richards Equation Solver")
            print("=" * 70)
            print(f"Profile depth: {self.depth:.1f} cm")
            print(f"Number of nodes: {self.n_nodes}")
            print(f"Simulation time: {t_end:.2f} days")
            print(f"Time step range: [{dt_min:.2e}, {dt_max:.2e}] days")
            print("=" * 70)

        self.results = self.solver.solve(
            h_init=self.h_init,
            t_end=t_end,
            dt_init=dt_init,
            dt_min=dt_min,
            dt_max=dt_max,
            output_times=output_times,
            verbose=verbose
        )

        return self.results

    def get_profile(self, time_index: int = -1) -> Dict:
        """
        Get profile data at a specific time.

        Parameters
        ----------
        time_index : int
            Index in results (default: -1 for last time)

        Returns
        -------
        profile : dict
            {'depth': depths, 'h': h, 'theta': theta, 'time': t}
        """
        if self.results is None:
            raise ValueError("No results available. Run simulation first.")

        return {
            'depth': self.depths,
            'h': self.results['h'][time_index],
            'theta': self.results['theta'][time_index],
            'time': self.results['times'][time_index]
        }

    def get_timeseries(self, node_index: int) -> Dict:
        """
        Get time series at a specific node.

        Parameters
        ----------
        node_index : int
            Node index (0 = surface, -1 = bottom)

        Returns
        -------
        timeseries : dict
            {'time': times, 'h': h, 'theta': theta, 'depth': z}
        """
        if self.results is None:
            raise ValueError("No results available. Run simulation first.")

        return {
            'time': self.results['times'],
            'h': self.results['h'][:, node_index],
            'theta': self.results['theta'][:, node_index],
            'depth': self.depths[node_index]
        }

    def to_xarray(self) -> 'xr.Dataset':
        """
        Convert simulation results to xarray Dataset.

        Returns
        -------
        ds : xarray.Dataset
            Dataset containing:
            - Coordinates: time, depth
            - Data variables: h, theta, K, C
            - Attributes: model metadata

        Raises
        ------
        ImportError
            If xarray is not installed
        ValueError
            If no results are available

        Examples
        --------
        >>> results = model.run(t_end=1.0, dt_init=0.01)
        >>> ds = model.to_xarray()
        >>> ds.h.sel(depth=-50, method='nearest').plot()  # Plot h at 50 cm depth
        >>> ds.theta.isel(time=-1).plot()  # Plot final theta profile
        """
        if not HAS_XARRAY:
            raise ImportError(
                "xarray is required for this feature. "
                "Install with: pip install xarray"
            )

        if self.results is None:
            raise ValueError("No results available. Run simulation first.")

        # Create coordinates
        coords = {
            'time': ('time', self.results['times'], {'units': 'days', 'long_name': 'Time'}),
            'depth': ('depth', self.depths, {'units': 'cm', 'long_name': 'Depth below surface'})
        }

        # Create data variables
        data_vars = {
            'h': (
                ['time', 'depth'],
                self.results['h'],
                {
                    'units': 'cm',
                    'long_name': 'Pressure head',
                    'description': 'Soil water pressure head (matric potential)'
                }
            ),
            'theta': (
                ['time', 'depth'],
                self.results['theta'],
                {
                    'units': '-',
                    'long_name': 'Water content',
                    'description': 'Volumetric water content'
                }
            ),
        }

        # Add mass balance variables (1D time series)
        mb = self.results['mass_balance']
        data_vars.update({
            'flux_top': (
                ['time'],
                mb['flux_top'],
                {'units': 'cm', 'long_name': 'Cumulative flux at top boundary'}
            ),
            'flux_bottom': (
                ['time'],
                mb['flux_bottom'],
                {'units': 'cm', 'long_name': 'Cumulative flux at bottom boundary'}
            ),
            'storage': (
                ['time'],
                mb['storage'],
                {'units': 'cm', 'long_name': 'Water storage in profile'}
            ),
            'mass_balance_error': (
                ['time'],
                mb['error'],
                {'units': 'cm', 'long_name': 'Mass balance error'}
            ),
        })

        # Global attributes
        attrs = {
            'title': 'HYDRUS1D Phase 3 Simulation Results',
            'description': '1D Richards equation solution',
            'depth_total': self.depth,
            'n_nodes': self.n_nodes,
            'top_bc': self.bc_top.__class__.__name__,
            'bottom_bc': self.bc_bottom.__class__.__name__,
        }

        # Add statistics as attributes
        stats = self.results['statistics']
        attrs.update({
            'total_steps': stats['total_steps'],
            'rejected_steps': stats['rejected_steps'],
            'avg_iterations': stats['avg_iterations'],
        })

        # Create Dataset
        ds = xr.Dataset(data_vars=data_vars, coords=coords, attrs=attrs)

        return ds

    def __repr__(self):
        return (
            f"HydrusModel("
            f"depth={self.depth:.1f} cm, "
            f"n_nodes={self.n_nodes}, "
            f"BC: {self.bc_top.__class__.__name__ if self.bc_top else 'None'} / "
            f"{self.bc_bottom.__class__.__name__ if self.bc_bottom else 'None'})"
        )
