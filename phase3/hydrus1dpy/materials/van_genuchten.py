"""
van Genuchten Soil Hydraulic Models
====================================

Implementation of van Genuchten (1980) water retention curve combined with
Mualem (1976) hydraulic conductivity function.

References
----------
van Genuchten, M. Th. (1980). A closed-form equation for predicting the
hydraulic conductivity of unsaturated soils. Soil Science Society of America
Journal, 44(5), 892-898. DOI: 10.2136/sssaj1980.03615995004400050002x

Mualem, Y. (1976). A new model for predicting the hydraulic conductivity of
unsaturated porous media. Water Resources Research, 12(3), 513-522.
DOI: 10.1029/WR012i003p00513

Vogel, T., & Cislerova, M. (1988). On the reliability of unsaturated hydraulic
conductivity calculated from the moisture retention curve. Transport in Porous
Media, 3(1), 1-15.
"""

from typing import Union
import numpy as np
from .base import HydraulicModel


class VanGenuchten(HydraulicModel):
    """
    van Genuchten (1980) + Mualem (1976) hydraulic model

    Water Retention (van Genuchten, 1980):
    ---------------------------------------
    For h < 0:
        θ(h) = θr + (θs - θr) / [1 + |α·h|^n]^m

    where m = 1 - 1/n (Mualem constraint)

    Hydraulic Conductivity (Mualem, 1976):
    ---------------------------------------
    For h < 0:
        K(h) = Ks · Se^l · [1 - (1 - Se^(1/m))^m]^2

    where:
        Se = (θ - θr) / (θs - θr) : effective saturation

    Parameters
    ----------
    theta_r : float
        Residual water content [-]
    theta_s : float
        Saturated water content [-]
    alpha : float
        Scale parameter [1/cm], related to inverse of air-entry value
        Must be > 0. Typical range: 0.001 - 0.5 cm⁻¹
    n : float
        Pore size distribution parameter [-]
        Must be > 1. Typical range: 1.1 - 10
        Controls curve steepness
    Ks : float
        Saturated hydraulic conductivity [cm/day]
    l : float, optional
        Pore connectivity parameter [-]
        Default: 0.5 (Mualem, 1976)
        Typical range: -2 to 2
        Common values: 0.5 (Mualem), 2.0 (Burdine)

    Attributes
    ----------
    m : float
        Shape parameter, calculated as m = 1 - 1/n

    Notes
    -----
    The van Genuchten-Mualem (VGM) model is one of the most widely used
    models for describing soil hydraulic properties. The model parameters
    can be obtained by:
    1. Direct measurement (retention and conductivity experiments)
    2. Pedotransfer functions (e.g., Rosetta)
    3. Literature values (e.g., Carsel & Parrish, 1988)

    Physical interpretation of parameters:
    - α: Related to air-entry value (approximately -1/α)
    - n: Controls pore size distribution width
    - Higher n: More uniform pore sizes, steeper curve
    - Lower n: More heterogeneous pores, gentler curve

    Examples
    --------
    >>> # Loam soil (Carsel & Parrish, 1988)
    >>> vg = VanGenuchten(
    ...     theta_r=0.078,
    ...     theta_s=0.430,
    ...     alpha=0.036,
    ...     n=1.56,
    ...     Ks=24.96,
    ...     l=0.5
    ... )
    >>>
    >>> # Calculate water content at h = -100 cm
    >>> theta = vg.water_content(-100)
    >>> print(f"θ(-100 cm) = {theta:.3f}")
    >>>
    >>> # Calculate conductivity
    >>> K = vg.conductivity(-100)
    >>> print(f"K(-100 cm) = {K:.3e} cm/day")
    """

    def __init__(self,
                 theta_r: float,
                 theta_s: float,
                 alpha: float,
                 n: float,
                 Ks: float,
                 l: float = 0.5):
        """Initialize van Genuchten model"""
        super().__init__(theta_r, theta_s, Ks)

        # Validate van Genuchten specific parameters
        if alpha <= 0:
            raise ValueError(f"α must be positive. Got α={alpha:.4e}")
        if n <= 1:
            raise ValueError(f"n must be > 1. Got n={n:.4f}")
        if not -10 <= l <= 10:
            raise ValueError(f"l must be reasonable (-10 to 10). Got l={l:.4f}")

        self.alpha = float(alpha)
        self.n = float(n)
        self.l = float(l)

        # Calculate m parameter (Mualem constraint)
        self.m = 1.0 - 1.0 / self.n

        # Pre-calculate useful constants
        self._alpha_n = self.alpha ** self.n
        self._one_over_m = 1.0 / self.m
        self._theta_range = self.theta_s - self.theta_r

    def water_content(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        van Genuchten water retention function

        θ(h) = θr + (θs - θr) / [1 + |α·h|^n]^m

        For h >= 0: θ = θs (saturated)
        For h < 0: van Genuchten equation
        """
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        # Initialize with saturated value
        theta = np.full_like(h, self.theta_s, dtype=float)

        # Unsaturated zone (h < 0)
        mask = h < 0
        if np.any(mask):
            h_unsat = -h[mask]  # Work with positive values

            # van Genuchten equation
            # θ = θr + (θs - θr) / [1 + (α·h)^n]^m
            term = (1.0 + (self.alpha * h_unsat) ** self.n) ** (-self.m)
            theta[mask] = self.theta_r + self._theta_range * term

        return float(theta[0]) if scalar_input else theta

    def conductivity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        van Genuchten-Mualem hydraulic conductivity function

        K(h) = Ks · Se^l · [1 - (1 - Se^(1/m))^m]^2

        For h >= 0: K = Ks (saturated)
        For h < 0: van Genuchten-Mualem equation
        """
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        # Initialize with saturated value
        K = np.full_like(h, self.Ks, dtype=float)

        # Unsaturated zone (h < 0)
        mask = h < 0
        if np.any(mask):
            # Calculate effective saturation
            Se = self._effective_saturation_vectorized(h[mask])

            # Mualem conductivity model
            # K = Ks · Se^l · [1 - (1 - Se^(1/m))^m]^2
            Se_power = Se ** self._one_over_m
            term = 1.0 - (1.0 - Se_power) ** self.m
            Kr = (Se ** self.l) * (term ** 2)

            # Apply safety bounds
            Kr = np.clip(Kr, 1e-37, 1.0)
            K[mask] = self.Ks * Kr

        return float(K[0]) if scalar_input else K

    def capacity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Specific water capacity (differential water capacity)

        C(h) = dθ/dh

        Analytical derivative of van Genuchten equation:
        C(h) = (θs - θr) · m · n · α^n · |h|^(n-1) · [1 + (α·h)^n]^(-m-1)

        For h >= 0: C = 0 (saturated, no change in θ with h)
        For h < 0: Positive capacity
        """
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        # Initialize with zero (saturated)
        C = np.zeros_like(h, dtype=float)

        # Unsaturated zone (h < 0)
        mask = h < 0
        if np.any(mask):
            h_unsat = -h[mask]  # Work with positive values

            # Analytical derivative
            # C = (θs - θr) · m · n · α^n · h^(n-1) · [1 + (α·h)^n]^(-m-1)
            h_power = h_unsat ** (self.n - 1.0)
            bracket = (1.0 + (self.alpha * h_unsat) ** self.n) ** (-self.m - 1.0)

            C[mask] = (
                self._theta_range *
                self.m *
                self.n *
                self._alpha_n *
                h_power *
                bracket
            )

            # Apply safety bounds to prevent numerical instability
            # Use a very small minimum to prevent division by zero
            C[mask] = np.maximum(C[mask], 1e-30)

        return float(C[0]) if scalar_input else C

    def pressure_head(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Analytical inverse of van Genuchten equation

        h(θ) = -1/α · [Se^(-1/m) - 1]^(1/n)

        where Se = (θ - θr) / (θs - θr)

        For θ = θs: h = 0
        For θr ≤ θ < θs: h < 0 (calculated)
        """
        theta = np.asarray(theta, dtype=float)
        scalar_input = theta.ndim == 0
        theta = np.atleast_1d(theta)

        # Validate input
        if np.any(theta < self.theta_r - 1e-10) or np.any(theta > self.theta_s + 1e-10):
            raise ValueError(
                f"θ must be in [{self.theta_r:.4f}, {self.theta_s:.4f}]. "
                f"Got θ range: [{np.min(theta):.4f}, {np.max(theta):.4f}]"
            )

        # Clip to valid range
        theta = np.clip(theta, self.theta_r, self.theta_s)

        # Initialize with zero (saturated)
        h = np.zeros_like(theta, dtype=float)

        # Unsaturated zone (θ < θs)
        mask = theta < self.theta_s - 1e-10
        if np.any(mask):
            # Calculate effective saturation
            Se = (theta[mask] - self.theta_r) / self._theta_range

            # Ensure Se is in valid range
            Se = np.clip(Se, 1e-10, 0.999999)

            # Analytical inverse: h = -1/α · [Se^(-1/m) - 1]^(1/n)
            term = Se ** (-self._one_over_m) - 1.0
            h[mask] = -(1.0 / self.alpha) * (term ** (1.0 / self.n))

        return float(h[0]) if scalar_input else h

    def _effective_saturation_vectorized(self, h: np.ndarray) -> np.ndarray:
        """
        Calculate effective saturation (vectorized, for internal use)

        Se = [1 + (α·|h|)^n]^(-m)

        Parameters
        ----------
        h : ndarray
            Pressure head [cm], assumed h < 0

        Returns
        -------
        Se : ndarray
            Effective saturation [-]
        """
        h_abs = np.abs(h)
        Se = (1.0 + (self.alpha * h_abs) ** self.n) ** (-self.m)
        return Se

    def air_entry_value(self) -> float:
        """
        Estimate air-entry value

        For van Genuchten model, the air-entry value is not explicitly defined,
        but can be approximated as hae ≈ -1/α

        Returns
        -------
        hae : float
            Approximate air-entry value [cm], negative
        """
        return -1.0 / self.alpha

    def inflection_point(self) -> tuple:
        """
        Calculate inflection point of retention curve

        The inflection point occurs where d²θ/dh² = 0,
        corresponding to maximum water capacity.

        Returns
        -------
        h_inf : float
            Pressure head at inflection point [cm]
        theta_inf : float
            Water content at inflection point [-]
        C_max : float
            Maximum water capacity [1/cm]
        """
        # For van Genuchten, inflection occurs at:
        # Se = [(n-1)/(n(m+1))]^(1/m)
        Se_inf = ((self.n - 1.0) / (self.n * (self.m + 1.0))) ** self._one_over_m

        # Calculate corresponding theta
        theta_inf = self.theta_r + self._theta_range * Se_inf

        # Calculate corresponding h
        h_inf = self.pressure_head(theta_inf)

        # Calculate maximum capacity
        C_max = self.capacity(h_inf)

        return h_inf, theta_inf, C_max

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"VanGenuchten(θr={self.theta_r:.4f}, θs={self.theta_s:.4f}, "
            f"α={self.alpha:.4f} cm⁻¹, n={self.n:.2f}, m={self.m:.4f}, "
            f"Ks={self.Ks:.2f} cm/day, l={self.l:.2f})"
        )


class ModifiedVanGenuchten(VanGenuchten):
    """
    Modified van Genuchten model (Vogel & Cislerova, 1988)

    Allows separate parameters for retention and conductivity curves,
    removing the constraint m = 1 - 1/n between them.

    Parameters
    ----------
    theta_r : float
        Residual water content (retention) [-]
    theta_s : float
        Saturated water content (retention) [-]
    alpha : float
        Scale parameter (retention) [1/cm]
    n : float
        Shape parameter (retention) [-]
    Ks : float
        Saturated hydraulic conductivity [cm/day]
    l : float, optional
        Pore connectivity parameter [-]
    theta_m : float, optional
        Saturated water content for conductivity [-]
        If None, uses theta_s
    theta_a : float, optional
        Residual water content for conductivity [-]
        If None, uses theta_r
    theta_k : float, optional
        Water content at K = Ks for conductivity [-]
        If None, uses theta_s
    Kk : float, optional
        Conductivity at theta_k [cm/day]
        If None, uses Ks

    Notes
    -----
    This model provides more flexibility by using different effective
    saturation for conductivity:
        Se_K = (θ - θa) / (θm - θa)

    This can better fit experimental data where retention and conductivity
    measurements don't align perfectly with the standard VG model.

    References
    ----------
    Vogel, T., & Cislerova, M. (1988). On the reliability of unsaturated
    hydraulic conductivity calculated from the moisture retention curve.
    Transport in Porous Media, 3(1), 1-15.
    """

    def __init__(self,
                 theta_r: float,
                 theta_s: float,
                 alpha: float,
                 n: float,
                 Ks: float,
                 l: float = 0.5,
                 theta_m: float = None,
                 theta_a: float = None,
                 theta_k: float = None,
                 Kk: float = None):
        """Initialize modified van Genuchten model"""
        super().__init__(theta_r, theta_s, alpha, n, Ks, l)

        # Conductivity parameters (default to retention parameters)
        self.theta_m = theta_m if theta_m is not None else theta_s
        self.theta_a = theta_a if theta_a is not None else theta_r
        self.theta_k = theta_k if theta_k is not None else theta_s
        self.Kk = Kk if Kk is not None else Ks

        # Validate conductivity parameters
        if not theta_r <= self.theta_a < self.theta_m <= theta_s:
            raise ValueError("Must have θr ≤ θa < θm ≤ θs")
        if not theta_r <= self.theta_k <= theta_s:
            raise ValueError("θk must be between θr and θs")
        if not 0 < self.Kk <= Ks:
            raise ValueError("Kk must be positive and ≤ Ks")

        self._theta_range_K = self.theta_m - self.theta_a

    def conductivity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Modified van Genuchten-Mualem conductivity

        Uses separate effective saturation for conductivity:
        Se_K = (θ - θa) / (θm - θa)

        K(h) = Kk · (Se_K)^l · [1 - (1 - (Se_K)^(1/m))^m]^2
        """
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        # Initialize with saturated value
        K = np.full_like(h, self.Ks, dtype=float)

        # Unsaturated zone (h < 0)
        mask = h < 0
        if np.any(mask):
            # Get water content
            theta = self.water_content(h[mask])

            # Calculate effective saturation for conductivity
            Se_K = (theta - self.theta_a) / self._theta_range_K
            Se_K = np.clip(Se_K, 0.0, 1.0)

            # Mualem model with modified Se
            Se_K_power = Se_K ** self._one_over_m
            term = 1.0 - (1.0 - Se_K_power) ** self.m
            Kr = (Se_K ** self.l) * (term ** 2)

            K[mask] = self.Kk * Kr

        return float(K[0]) if scalar_input else K

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"ModifiedVanGenuchten(θr={self.theta_r:.4f}, θs={self.theta_s:.4f}, "
            f"α={self.alpha:.4f} cm⁻¹, n={self.n:.2f}, "
            f"θm={self.theta_m:.4f}, θa={self.theta_a:.4f}, "
            f"Ks={self.Ks:.2f} cm/day, l={self.l:.2f})"
        )
