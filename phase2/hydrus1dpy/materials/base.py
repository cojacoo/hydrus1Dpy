"""
Abstract Base Class for Hydraulic Models
==========================================

Defines the interface that all soil hydraulic models must implement.
"""

from abc import ABC, abstractmethod
from typing import Union
import numpy as np


class HydraulicModel(ABC):
    """
    Abstract base class for soil hydraulic property models

    All hydraulic models must provide functions for:
    1. Water retention: θ(h)
    2. Hydraulic conductivity: K(h)
    3. Water capacity: C(h) = dθ/dh
    4. Inverse function: h(θ) [if analytical solution exists]

    Parameters
    ----------
    theta_r : float
        Residual water content [-], must satisfy: 0 ≤ θr < θs ≤ 1
    theta_s : float
        Saturated water content [-], must satisfy: 0 ≤ θr < θs ≤ 1
    Ks : float
        Saturated hydraulic conductivity [cm/day], must be > 0

    Notes
    -----
    - All pressure heads h are in [cm], negative for unsaturated conditions
    - Water contents θ are volumetric [-], dimensionless
    - Hydraulic conductivity K is in [cm/day]
    - Methods support both scalar and array inputs (vectorized)
    """

    def __init__(self, theta_r: float, theta_s: float, Ks: float):
        """
        Initialize base hydraulic model

        Parameters
        ----------
        theta_r : float
            Residual water content [-]
        theta_s : float
            Saturated water content [-]
        Ks : float
            Saturated hydraulic conductivity [cm/day]

        Raises
        ------
        ValueError
            If parameters violate physical constraints
        """
        # Validate parameters
        if not 0 <= theta_r < theta_s <= 1:
            raise ValueError(
                f"Must satisfy 0 ≤ θr < θs ≤ 1. "
                f"Got θr={theta_r:.4f}, θs={theta_s:.4f}"
            )
        if Ks <= 0:
            raise ValueError(f"Ks must be positive. Got Ks={Ks:.4e}")

        self.theta_r = float(theta_r)
        self.theta_s = float(theta_s)
        self.Ks = float(Ks)

    @abstractmethod
    def water_content(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate volumetric water content from pressure head

        Implements the water retention curve: θ = θ(h)

        Parameters
        ----------
        h : float or ndarray
            Pressure head [cm]
            - h >= 0: saturated conditions
            - h < 0: unsaturated conditions

        Returns
        -------
        theta : float or ndarray
            Volumetric water content [-]
            Same shape as input h

        Notes
        -----
        For h >= 0 (saturated): θ = θs
        For h < 0 (unsaturated): θ depends on model

        Physical constraints:
        - θr ≤ θ ≤ θs for all h
        - θ → θs as h → 0⁻
        - θ → θr as h → -∞
        - dθ/dh > 0 (monotonically increasing)
        """
        pass

    @abstractmethod
    def conductivity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate hydraulic conductivity from pressure head

        Implements the conductivity function: K = K(h)

        Parameters
        ----------
        h : float or ndarray
            Pressure head [cm]

        Returns
        -------
        K : float or ndarray
            Hydraulic conductivity [cm/day]
            Same shape as input h

        Notes
        -----
        For h >= 0 (saturated): K = Ks
        For h < 0 (unsaturated): K < Ks, depends on model

        Physical constraints:
        - 0 < K ≤ Ks for all h
        - K → Ks as h → 0⁻
        - K → 0 as h → -∞
        - dK/dh > 0 (monotonically increasing)
        """
        pass

    @abstractmethod
    def capacity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate specific water capacity (differential water capacity)

        C(h) = dθ/dh [1/cm]

        Parameters
        ----------
        h : float or ndarray
            Pressure head [cm]

        Returns
        -------
        C : float or ndarray
            Specific water capacity [1/cm]
            Same shape as input h

        Notes
        -----
        For h >= 0 (saturated): C = 0
        For h < 0 (unsaturated): C > 0

        Physical constraints:
        - C ≥ 0 for all h
        - C = 0 for h >= 0
        - C has maximum at some h < 0 (inflection point)
        - C → 0 as h → -∞

        Implementation:
        Can be computed analytically (preferred) or numerically:
        C(h) ≈ [θ(h+Δh) - θ(h-Δh)] / (2Δh)
        """
        pass

    def pressure_head(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate pressure head from water content (inverse function)

        Implements: h = θ⁻¹(θ)

        Parameters
        ----------
        theta : float or ndarray
            Volumetric water content [-]

        Returns
        -------
        h : float or ndarray
            Pressure head [cm]

        Notes
        -----
        Default implementation uses numerical root finding (bisection).
        Subclasses should override with analytical solution if available.

        For θ = θs: h = 0
        For θr ≤ θ < θs: h < 0

        Raises
        ------
        ValueError
            If θ < θr or θ > θs
        """
        from scipy.optimize import brentq

        def objective(h_trial):
            return self.water_content(h_trial) - theta

        # Vectorize if needed
        if np.isscalar(theta):
            theta_val = float(theta)

            # Validate input
            if theta_val < self.theta_r or theta_val > self.theta_s:
                raise ValueError(
                    f"θ must be in [{self.theta_r:.4f}, {self.theta_s:.4f}]. "
                    f"Got θ={theta_val:.4f}"
                )

            # Special case: saturated
            if np.isclose(theta_val, self.theta_s, rtol=1e-10):
                return 0.0

            # Numerical solution
            try:
                h_solution = brentq(objective, -1e6, 0.0, xtol=1e-8)
                return h_solution
            except ValueError:
                # Fallback to wider bracket
                h_solution = brentq(objective, -1e8, 1.0, xtol=1e-8)
                return h_solution

        else:
            # Vectorized version
            theta_array = np.asarray(theta)
            h_result = np.zeros_like(theta_array, dtype=float)

            for i, theta_val in enumerate(theta_array.flat):
                h_result.flat[i] = self.pressure_head(theta_val)

            return h_result

    def effective_saturation(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate effective saturation

        Se = (θ - θr) / (θs - θr)

        Parameters
        ----------
        h : float or ndarray
            Pressure head [cm]

        Returns
        -------
        Se : float or ndarray
            Effective saturation [-], 0 ≤ Se ≤ 1

        Notes
        -----
        Effective saturation normalizes water content:
        - Se = 0 at θ = θr (residual)
        - Se = 1 at θ = θs (saturated)
        """
        theta = self.water_content(h)
        Se = (theta - self.theta_r) / (self.theta_s - self.theta_r)
        return np.clip(Se, 0.0, 1.0)

    def relative_conductivity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate relative hydraulic conductivity

        Kr = K(h) / Ks

        Parameters
        ----------
        h : float or ndarray
            Pressure head [cm]

        Returns
        -------
        Kr : float or ndarray
            Relative conductivity [-], 0 < Kr ≤ 1
        """
        K = self.conductivity(h)
        return K / self.Ks

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"{self.__class__.__name__}("
            f"θr={self.theta_r:.4f}, θs={self.theta_s:.4f}, Ks={self.Ks:.2f})"
        )

    def validate(self) -> bool:
        """
        Validate hydraulic model properties

        Checks that the model satisfies physical constraints:
        - Water content increases with pressure head
        - Conductivity increases with pressure head
        - Proper behavior at boundaries

        Returns
        -------
        valid : bool
            True if model passes all checks

        Raises
        ------
        AssertionError
            If any validation check fails (with descriptive message)
        """
        # Test points
        h_test = np.array([-10000, -1000, -100, -10, -1, -0.1, 0.0])

        # Check 1: Water content
        theta = self.water_content(h_test)
        assert np.all(theta >= self.theta_r), "θ < θr detected"
        assert np.all(theta <= self.theta_s), "θ > θs detected"
        assert np.isclose(theta[-1], self.theta_s), "θ(h=0) should equal θs"

        # Check 2: Monotonicity of water content
        dtheta = np.diff(theta)
        assert np.all(dtheta >= 0), "θ(h) is not monotonically increasing"

        # Check 3: Conductivity
        K = self.conductivity(h_test)
        assert np.all(K > 0), "K ≤ 0 detected"
        assert np.all(K <= self.Ks), "K > Ks detected"
        assert np.isclose(K[-1], self.Ks), "K(h=0) should equal Ks"

        # Check 4: Monotonicity of conductivity
        dK = np.diff(K)
        assert np.all(dK >= -1e-10), "K(h) is not monotonically increasing"

        # Check 5: Capacity
        C = self.capacity(h_test[:-1])  # Skip h=0
        assert np.all(C >= 0), "C < 0 detected"
        assert np.isclose(self.capacity(0.0), 0.0), "C(h=0) should equal 0"

        # Check 6: Inverse function (if theta < theta_s)
        for theta_test in np.linspace(self.theta_r + 0.01, self.theta_s - 0.01, 5):
            h_calc = self.pressure_head(theta_test)
            theta_back = self.water_content(h_calc)
            assert np.isclose(theta_test, theta_back, rtol=1e-3), \
                f"Inverse function failed: θ={theta_test:.4f} → h={h_calc:.2f} → θ={theta_back:.4f}"

        return True
