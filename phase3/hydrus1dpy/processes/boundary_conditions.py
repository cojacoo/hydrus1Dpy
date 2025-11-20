"""
Boundary Conditions for HYDRUS1D Phase 3
=========================================

Implementation of common boundary conditions for Richards equation.

Author: HYDRUS1DPy Development Team

References
----------
Simunek, J., van Genuchten, M. Th., & Sejna, M. (2008).
Development and applications of the HYDRUS and STANMOD software packages
and related codes. Vadose Zone Journal, 7(2), 587-600.
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Callable

from .evapotranspiration import ETCalculator, pf_to_head, head_to_pf


class BoundaryCondition(ABC):
    """
    Abstract base class for boundary conditions.

    All boundary conditions must implement methods to:
    1. Modify the system matrix (A) and RHS (b)
    2. Provide diagnostics (flux, head, etc.)
    """

    def __init__(self, location: str):
        """
        Parameters
        ----------
        location : str
            Either 'top' or 'bottom'
        """
        if location not in ['top', 'bottom']:
            raise ValueError("location must be 'top' or 'bottom'")
        self.location = location
        self.flux_history = []
        self.head_history = []

    @abstractmethod
    def apply(
        self,
        a: np.ndarray,
        b: np.ndarray,
        c: np.ndarray,
        d: np.ndarray,
        h: np.ndarray,
        K: np.ndarray,
        dz: float,
        t: float
    ) -> None:
        """
        Apply boundary condition to the linear system.

        Modifies the tridiagonal system [a, b, c] x = d in place.

        Parameters
        ----------
        a, b, c : ndarray
            Tridiagonal matrix diagonals (modified in place)
        d : ndarray
            Right-hand side vector (modified in place)
        h : ndarray
            Current pressure head values [cm]
        K : ndarray
            Current hydraulic conductivity [cm/day]
        dz : float
            Spatial step size [cm]
        t : float
            Current time [days]
        """
        pass

    @abstractmethod
    def get_flux(self, h: np.ndarray, K: np.ndarray, dz: float, t: float) -> float:
        """
        Calculate flux at the boundary [cm/day].

        Positive flux = water entering domain.
        """
        pass

    def record_state(self, h: np.ndarray, K: np.ndarray, dz: float, t: float):
        """Record boundary state for diagnostics."""
        flux = self.get_flux(h, K, dz, t)
        self.flux_history.append(flux)

        if self.location == 'top':
            self.head_history.append(h[0])
        else:
            self.head_history.append(h[-1])


class ConstantHeadBC(BoundaryCondition):
    """
    Constant (Dirichlet) boundary condition: h = h_bc

    Parameters
    ----------
    location : str
        'top' or 'bottom'
    head : float or callable
        Prescribed head [cm]. Can be:
        - float: constant head
        - callable: head(t) function of time

    Examples
    --------
    >>> # Constant head at surface
    >>> bc_top = ConstantHeadBC('top', head=-100.0)
    >>>
    >>> # Time-varying head at bottom
    >>> bc_bot = ConstantHeadBC('bottom', head=lambda t: -50 * (1 + 0.1*np.sin(2*np.pi*t)))
    """

    def __init__(self, location: str, head: float | Callable):
        super().__init__(location)

        if callable(head):
            self.head_func = head
        else:
            self.head_func = lambda t: float(head)

    def apply(self, a, b, c, d, h, K, dz, t):
        """Apply Dirichlet BC: directly set boundary value."""
        h_bc = self.head_func(t)

        if self.location == 'top':
            # Top node (i=0): h[0] = h_bc
            # Eliminate first equation: 1*h[0] = h_bc
            a[0] = 0.0
            b[0] = 1.0
            c[0] = 0.0
            d[0] = h_bc

        else:  # bottom
            # Bottom node (i=n-1): h[n-1] = h_bc
            n = len(d)
            a[n-1] = 0.0
            b[n-1] = 1.0
            c[n-1] = 0.0
            d[n-1] = h_bc

    def get_flux(self, h, K, dz, t):
        """
        Calculate flux from Darcy's law.

        For top BC:    q = -K[1/2] * [(h[1] - h[0])/dz + 1]
        For bottom BC: q = -K[n-3/2] * [(h[n-1] - h[n-2])/dz + 1]
        """
        if self.location == 'top':
            # Flux at top surface (positive = infiltration)
            K_interface = 0.5 * (K[0] + K[1])
            dh_dz = (h[1] - h[0]) / dz
            flux = -K_interface * (dh_dz + 1.0)  # +1 for gravity

        else:  # bottom
            # Flux at bottom (positive = upward)
            n = len(h)
            K_interface = 0.5 * (K[n-2] + K[n-1])
            dh_dz = (h[n-1] - h[n-2]) / dz
            flux = -K_interface * (dh_dz + 1.0)

        return flux


class ConstantFluxBC(BoundaryCondition):
    """
    Constant flux (Neumann) boundary condition: q = q_bc

    Parameters
    ----------
    location : str
        'top' or 'bottom'
    flux : float or callable
        Prescribed flux [cm/day]. Can be:
        - float: constant flux
        - callable: flux(t) function of time

    Sign convention:
    - Positive flux = water entering domain (infiltration at top, seepage at bottom)
    - Negative flux = water leaving domain (evaporation at top, drainage at bottom)

    Examples
    --------
    >>> # Constant infiltration at top
    >>> bc_top = ConstantFluxBC('top', flux=0.5)  # 0.5 cm/day infiltration
    >>>
    >>> # Time-varying evaporation
    >>> bc_top = ConstantFluxBC('top', flux=lambda t: -0.3 * np.sin(2*np.pi*t/365))
    """

    def __init__(self, location: str, flux: float | Callable):
        super().__init__(location)

        if callable(flux):
            self.flux_func = flux
        else:
            self.flux_func = lambda t: float(flux)

    def apply(self, a, b, c, d, h, K, dz, t):
        """
        Apply Neumann BC: set up equation for boundary node with prescribed flux.

        For flux BC, we need to discretize the boundary node equation.
        At top (i=0): C[0] * dh[0]/dt = (q_bc - q[0->1]) / dz
        At bottom (i=n-1): C[n-1] * dh[n-1]/dt = (q[n-2->n-1] - q_bc) / dz

        where q[i->i+1] = -K[i,i+1] * (dh/dz + 1)
        """
        q_bc = self.flux_func(t)

        if self.location == 'top':
            # Top node (i=0)
            # Need to set up full equation for this node
            # The equation is already being set up by Richards solver for internal nodes
            # We just need to modify it for the boundary

            # For top BC, the flux enters from above
            # Discretization: C[0]/dt * h[0] - K[0,1]/dz * (h[1] - h[0]) =
            #                 C[0]/dt * h_old[0] + q_bc/dz - K[0,1]/dz * 1

            # This equation needs matrix coefficients to be set
            # Since internal loop doesn't handle i=0, we set it here
            # Note: d[0] should already have time derivative term from solver
            # We add the flux contribution
            d[0] += q_bc / dz

        else:  # bottom
            # Bottom node (i=n-1)
            # Similar setup for bottom
            n = len(d)
            d[n-1] -= q_bc / dz

    def get_flux(self, h, K, dz, t):
        """Return prescribed flux."""
        return self.flux_func(t)


class FreeDrainageBC(BoundaryCondition):
    """
    Free drainage (unit gradient) boundary condition: dh/dz = 0

    This implies q = -K (pure gravity drainage).
    Commonly used at the bottom of soil profiles.

    Parameters
    ----------
    location : str
        Usually 'bottom', but can be 'top'

    Notes
    -----
    The free drainage condition assumes:
    - No capillary gradient (dh/dz = 0)
    - Flow driven only by gravity
    - Flux = -K(h) at boundary

    This is appropriate when:
    - Water table is deep
    - No impermeable layer below
    - Drainage to deeper layers

    Examples
    --------
    >>> bc_bot = FreeDrainageBC('bottom')
    """

    def __init__(self, location: str = 'bottom'):
        super().__init__(location)

    def apply(self, a, b, c, d, h, K, dz, t):
        """
        Apply unit gradient (free drainage): dh/dz = 0

        Uses second-order extrapolation: h[n] = h[n-1] + 0 * dz = h[n-1]
        where h[n] is a ghost node below the bottom.

        This is implemented by modifying the bottom node equation to use the
        extrapolated value, avoiding the constraint equation h[n-1] = h[n-2].
        """
        if self.location == 'top':
            # Not typically used, but included for completeness
            # Use zero flux approximation
            pass

        else:  # bottom
            # For free drainage at bottom, use second-order backward difference
            # to approximate dh/dz = 0 at the boundary
            #
            # Standard approach: use 3-point backward difference
            # dh/dz|_{n-1} ~= (3h[n-1] - 4h[n-2] + h[n-3]) / (2*dz) = 0
            # This gives: 3h[n-1] = 4h[n-2] - h[n-3]
            #
            # But this requires information about h[n-3], making the matrix
            # structure more complex. Instead, use first-order:
            # dh/dz|_{n-1} ~= (h[n-1] - h[n-2]) / dz = 0
            #
            # The numerical implementation uses a "reflective" ghost node:
            # h_ghost = h[n-1] (below bottom)
            #
            # This means the flux out of the domain is purely gravitational:
            # q_out = -K[n-1] * (dh/dz + 1) = -K[n-1] * (0 + 1) = -K[n-1]
            #
            # Replace the bottom equation entirely:
            # Set h[n-1] = h[n-2] using a well-conditioned formulation
            #
            # To avoid singularity, use a weighted average:
            # (1+eps)*h[n-1] - h[n-2] = eps*h[n-1]
            # where eps is a small number for regularization

            n = len(d)
            epsilon = 1e-10  # Regularization parameter

            a[n-1] = -1.0
            b[n-1] = 1.0 + epsilon
            c[n-1] = 0.0
            d[n-1] = epsilon * h[n-1]  # Use current value for regularization

    def get_flux(self, h, K, dz, t):
        """
        Calculate free drainage flux: q = -K

        Negative because water is leaving the domain.
        """
        if self.location == 'top':
            flux = -K[0]
        else:
            flux = -K[-1]

        return flux


class AtmosphericBC(BoundaryCondition):
    """
    Atmospheric boundary condition with surface ponding.

    Attempts to apply prescribed flux (precipitation - evaporation).
    If surface becomes too dry (h < h_min) or too wet (h > 0),
    switches to pressure head BC.

    Parameters
    ----------
    location : str
        Must be 'top'
    flux : float or callable
        Atmospheric flux [cm/day]
        Positive = infiltration (precipitation)
        Negative = evaporation
    h_min : float, optional
        Minimum allowed surface pressure head [cm] (default: -15000)
    h_surface : float, optional
        Surface ponding head when saturated [cm] (default: 0.0)

    Notes
    -----
    Algorithm:
    1. Try to apply flux BC
    2. After solving, check h[0]:
       - If h[0] < h_min: switch to h = h_min (evaporation limit)
       - If h[0] > h_surface: switch to h = h_surface (ponding)
       - Otherwise: keep flux BC

    This mimics HYDRUS-1D atmospheric boundary condition.

    Examples
    --------
    >>> # Daily precipitation/evaporation
    >>> def atm_flux(t):
    ...     # Simple sinusoidal pattern
    ...     return 0.5 * np.sin(2*np.pi*t/365)  # cm/day
    >>>
    >>> bc_top = AtmosphericBC('top', flux=atm_flux, h_min=-15000, h_surface=0.0)
    """

    def __init__(
        self,
        location: str,
        flux: float | Callable,
        h_min: float = -15000.0,
        h_surface: float = 0.0
    ):
        if location != 'top':
            raise ValueError("AtmosphericBC only valid at top boundary")

        super().__init__(location)

        if callable(flux):
            self.flux_func = flux
        else:
            self.flux_func = lambda t: float(flux)

        self.h_min = h_min
        self.h_surface = h_surface

        # Track BC state
        self.bc_type = 'flux'  # Current type: 'flux', 'h_min', or 'ponding'
        self.bc_switches = {'flux': 0, 'h_min': 0, 'ponding': 0}

    def apply(self, a, b, c, d, h, K, dz, t):
        """
        Apply atmospheric BC based on current state.

        This is evaluated AFTER the previous time step solution,
        so h[0] contains the result from attempting flux BC.
        """
        q_atm = self.flux_func(t)

        # Check if we need to switch BC type based on previous solution
        if self.bc_type == 'flux':
            # Check limits
            if h[0] < self.h_min:
                self.bc_type = 'h_min'
                self.bc_switches['h_min'] += 1
            elif h[0] > self.h_surface:
                self.bc_type = 'ponding'
                self.bc_switches['ponding'] += 1

        elif self.bc_type == 'h_min':
            # Check if we can return to flux BC
            # This requires that potential flux would increase h
            if q_atm > 0:  # Infiltration
                self.bc_type = 'flux'
                self.bc_switches['flux'] += 1

        elif self.bc_type == 'ponding':
            # Check if ponding has ended
            if q_atm < 0:  # Evaporation
                self.bc_type = 'flux'
                self.bc_switches['flux'] += 1

        # Apply the appropriate BC
        if self.bc_type == 'flux':
            # Apply flux BC
            d[0] += q_atm / dz

        elif self.bc_type == 'h_min':
            # Apply minimum head BC (dry limit)
            a[0] = 0.0
            b[0] = 1.0
            c[0] = 0.0
            d[0] = self.h_min

        elif self.bc_type == 'ponding':
            # Apply surface ponding BC
            a[0] = 0.0
            b[0] = 1.0
            c[0] = 0.0
            d[0] = self.h_surface

    def get_flux(self, h, K, dz, t):
        """
        Calculate actual flux at surface.

        If flux BC is active: return prescribed flux
        If head BC is active: calculate flux from gradient
        """
        if self.bc_type == 'flux':
            return self.flux_func(t)
        else:
            # Head BC active - calculate actual flux
            K_interface = 0.5 * (K[0] + K[1])
            dh_dz = (h[1] - h[0]) / dz
            flux = -K_interface * (dh_dz + 1.0)
            return flux

    def get_diagnostics(self) -> dict:
        """Get atmospheric BC diagnostics."""
        return {
            'current_type': self.bc_type,
            'n_switches_to_flux': self.bc_switches['flux'],
            'n_switches_to_dry': self.bc_switches['h_min'],
            'n_switches_to_ponding': self.bc_switches['ponding']
        }


class EnhancedAtmosphericBC(BoundaryCondition):
    """
    Enhanced atmospheric boundary condition with realistic ET and infiltration.

    Features:
    - Penman-Monteith or simple ET calculation
    - Stage 1/2 evaporation (switches at pF 4.5)
    - Infiltration as thin water film (small positive head)
    - Surface ponding when infiltration capacity exceeded

    Parameters
    ----------
    location : str
        Must be 'top'
    precipitation : float or callable, optional
        Precipitation rate [mm/day]. Can be:
        - float: constant precipitation
        - callable: precip(t) function of time
        - None: no precipitation (default)
    et_method : str, optional
        ET calculation method:
        - 'penman_monteith': FAO-56 Penman-Monteith (requires weather_func)
        - 'simple': Constant ET (default: 4 mm/day if no other BC defined)
        - 'none': No ET
    et_default : float, optional
        Default ET for 'simple' method [mm/day] (default: 4.0)
    weather_func : callable, optional
        Function returning WeatherData: weather_func(t) -> WeatherData
        Required for 'penman_monteith' method
    latitude : float, optional
        Site latitude [degrees] for Penman-Monteith (default: 0)
    elevation : float, optional
        Site elevation [m] for Penman-Monteith (default: 0)
    h_ponding : float, optional
        Ponding head when infiltrating [cm] (default: 0.05 cm = 0.5 mm film)
    h_stage2 : float, optional
        Surface head for stage 2 evaporation [cm] (default: pF 4.5 = -31623 cm)
    ponding_max : float, optional
        Maximum ponding depth [cm] before runoff (default: 5.0 cm)

    Notes
    -----
    Evaporation Stages:
    - Stage 1: Potential ET when h_surface > h_stage2 (surface wet enough)
                Flux = -ET_pot [mm/day]
    - Stage 2: Soil-limited ET when h_surface < h_stage2 (surface too dry)
                Switches to head BC with h = h_stage2
                Actual ET determined by soil hydraulic properties

    Infiltration:
    - Applied as small positive head (thin water film)
    - h_surface = h_ponding (typically 0.05 cm = 0.5 mm)
    - Richards equation calculates actual infiltration rate
    - More realistic than prescribed flux for capacity-limited infiltration

    Examples
    --------
    >>> # Simple ET (4 mm/day) with occasional rainfall
    >>> def precip(t):
    ...     # 10 mm rain every 7 days
    ...     if t % 7 < 0.5:
    ...         return 10.0
    ...     return 0.0
    >>> bc = EnhancedAtmosphericBC(
    ...     'top',
    ...     precipitation=precip,
    ...     et_method='simple',
    ...     et_default=4.0
    ... )

    >>> # Penman-Monteith ET with weather data
    >>> def get_weather(t):
    ...     return WeatherData(
    ...         time=t,
    ...         temperature=20 + 5*np.sin(2*np.pi*t/365),
    ...         relative_humidity=60,
    ...         wind_speed=2.0,
    ...         solar_radiation=15.0
    ...     )
    >>> bc = EnhancedAtmosphericBC(
    ...     'top',
    ...     precipitation=0.0,
    ...     et_method='penman_monteith',
    ...     weather_func=get_weather,
    ...     latitude=52.0,
    ...     elevation=100
    ... )
    """

    def __init__(
        self,
        location: str,
        precipitation: Optional[float | Callable] = None,
        et_method: str = 'simple',
        et_default: float = 4.0,
        weather_func: Optional[Callable] = None,
        latitude: float = 0.0,
        elevation: float = 0.0,
        h_ponding: float = 0.05,
        h_stage2: float = None,
        ponding_max: float = 5.0
    ):
        if location != 'top':
            raise ValueError("EnhancedAtmosphericBC only valid at top boundary")

        super().__init__(location)

        # Precipitation
        if precipitation is None:
            self.precip_func = lambda t: 0.0
        elif callable(precipitation):
            self.precip_func = precipitation
        else:
            self.precip_func = lambda t: float(precipitation)

        # ET calculator
        if et_method == 'none':
            self.et_calculator = None
        else:
            self.et_calculator = ETCalculator(
                method=et_method,
                weather_func=weather_func,
                et0_default=et_default,
                latitude=latitude,
                elevation=elevation
            )

        # Ponding/infiltration parameters
        self.h_ponding = h_ponding  # Small positive head for infiltration
        self.ponding_max = ponding_max  # Maximum ponding before runoff

        # Stage 2 evaporation threshold (pF 4.5 by default)
        if h_stage2 is None:
            self.h_stage2 = pf_to_head(4.5)  # ≈ -31623 cm
        else:
            self.h_stage2 = h_stage2

        # State tracking
        self.bc_type = 'flux'  # 'flux', 'infiltration', 'ponding', 'stage2_et'
        self.bc_switches = {
            'flux': 0,
            'infiltration': 0,
            'ponding': 0,
            'stage2_et': 0
        }
        self.et_stage = 1  # 1 or 2
        self.cumulative_runoff = 0.0

    def apply(self, a, b, c, d, h, K, dz, t):
        """
        Apply enhanced atmospheric BC.

        Implements:
        1. ET calculation (Penman-Monteith or simple)
        2. Stage 1/2 evaporation based on surface dryness
        3. Infiltration with ponding (small positive head)
        4. Surface runoff when ponding exceeds maximum
        """
        # Get precipitation and potential ET
        precip = self.precip_func(t)  # mm/day
        if self.et_calculator is not None:
            et_pot = self.et_calculator.calculate(t)  # mm/day
        else:
            et_pot = 0.0

        # Convert mm/day to cm/day
        precip_cm = precip / 10.0
        et_pot_cm = et_pot / 10.0

        # Net atmospheric demand
        atm_flux = precip_cm - et_pot_cm  # Positive = infiltration, negative = ET

        # Determine BC type based on current state and atmospheric demand
        h_surface = h[0]

        if atm_flux > 0:
            # INFILTRATION case
            # Apply as small positive head (thin water film)
            # This allows Richards equation to determine actual infiltration rate
            self.bc_type = 'infiltration'
            self.bc_switches['infiltration'] += 1

            # Check if ponding exceeds maximum
            if h_surface > self.ponding_max:
                # Excessive ponding - limit to maximum and track runoff
                excess = h_surface - self.ponding_max
                self.cumulative_runoff += excess * dz  # Approximate runoff volume
                h_ponding_actual = self.ponding_max
            else:
                h_ponding_actual = self.h_ponding

            # Apply head BC with small positive head
            a[0] = 0.0
            b[0] = 1.0
            c[0] = 0.0
            d[0] = h_ponding_actual

        elif atm_flux < 0:
            # EVAPORATION case
            # Check if surface is dry enough for stage 2 evaporation
            if h_surface < self.h_stage2:
                # Stage 2: Soil-limited evaporation
                self.et_stage = 2
                self.bc_type = 'stage2_et'
                self.bc_switches['stage2_et'] += 1

                # Apply head BC at stage 2 threshold
                # This limits evaporation based on soil hydraulic properties
                a[0] = 0.0
                b[0] = 1.0
                c[0] = 0.0
                d[0] = self.h_stage2

            else:
                # Stage 1: Potential evaporation (flux-controlled)
                self.et_stage = 1
                self.bc_type = 'flux'
                self.bc_switches['flux'] += 1

                # Apply ET as flux BC
                d[0] += atm_flux / dz

        else:
            # Zero flux (no precip, no ET)
            self.bc_type = 'flux'
            # No change to d[0] (zero flux)

    def get_flux(self, h, K, dz, t):
        """
        Calculate actual flux at surface.

        Returns
        -------
        flux : float
            Actual surface flux [cm/day]
            Positive = infiltration, negative = evaporation
        """
        if self.bc_type == 'flux':
            # Flux BC: return prescribed flux
            precip = self.precip_func(t) / 10.0  # mm/day -> cm/day
            if self.et_calculator is not None:
                et_pot = self.et_calculator.calculate(t) / 10.0
            else:
                et_pot = 0.0
            return precip - et_pot

        else:
            # Head BC active: calculate actual flux from gradient
            K_interface = 0.5 * (K[0] + K[1])
            dh_dz = (h[1] - h[0]) / dz
            flux = -K_interface * (dh_dz + 1.0)
            return flux

    def get_diagnostics(self) -> dict:
        """Get enhanced atmospheric BC diagnostics."""
        return {
            'current_type': self.bc_type,
            'et_stage': self.et_stage,
            'h_stage2_threshold': self.h_stage2,
            'pf_stage2_threshold': head_to_pf(self.h_stage2),
            'cumulative_runoff': self.cumulative_runoff,
            'n_switches_to_flux': self.bc_switches['flux'],
            'n_switches_to_infiltration': self.bc_switches['infiltration'],
            'n_switches_to_ponding': self.bc_switches['ponding'],
            'n_switches_to_stage2_et': self.bc_switches['stage2_et']
        }
