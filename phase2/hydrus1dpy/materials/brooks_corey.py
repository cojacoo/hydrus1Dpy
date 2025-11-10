"""
Brooks-Corey Soil Hydraulic Model
==================================

Implementation of Brooks & Corey (1964) water retention curve.

References
----------
Brooks, R. H., & Corey, A. T. (1964). Hydraulic properties of porous media.
Hydrology Papers, Colorado State University, Fort Collins, Colorado.
"""

from typing import Union
import numpy as np
from .base import HydraulicModel


class BrooksCorey(HydraulicModel):
    """
    Brooks-Corey (1964) hydraulic model

    Water Retention:
    ----------------
    For h >= hb:  θ = θs (saturated)
    For h < hb:   Se = (h/hb)^(-λ)
                  θ = θr + (θs - θr) · Se

    Hydraulic Conductivity:
    -----------------------
    K(h) = Ks · Se^(2/λ + l + 2)  [Mualem, 1976]

    Parameters
    ----------
    theta_r : float
        Residual water content [-]
    theta_s : float
        Saturated water content [-]
    hb : float
        Air-entry (bubbling) pressure [cm], negative value
        Typical range: -30 to -2 cm
    lambda_ : float
        Pore size distribution index [-]
        Must be > 0. Typical range: 0.2 - 3.0
        Higher λ: More uniform pore sizes
    Ks : float
        Saturated hydraulic conductivity [cm/day]
    l : float, optional
        Pore connectivity (default: 2 for Mualem, 1.5 for Burdine)
    """

    def __init__(self,
                 theta_r: float,
                 theta_s: float,
                 hb: float,
                 lambda_: float,
                 Ks: float,
                 l: float = 2.0):
        super().__init__(theta_r, theta_s, Ks)

        if hb >= 0:
            raise ValueError(f"hb (air-entry) must be negative. Got hb={hb:.2f}")
        if lambda_ <= 0:
            raise ValueError(f"λ must be positive. Got λ={lambda_:.4f}")

        self.hb = float(hb)
        self.lambda_ = float(lambda_)
        self.l = float(l)
        self._K_exponent = 2.0 / self.lambda_ + self.l + 2.0

    def water_content(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Brooks-Corey water retention"""
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        theta = np.full_like(h, self.theta_s)

        # Unsaturated (h < hb)
        mask = h < self.hb
        if np.any(mask):
            Se = (h[mask] / self.hb) ** (-self.lambda_)
            theta[mask] = self.theta_r + (self.theta_s - self.theta_r) * Se

        return float(theta[0]) if scalar_input else theta

    def conductivity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Brooks-Corey-Mualem conductivity"""
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        K = np.full_like(h, self.Ks)

        mask = h < self.hb
        if np.any(mask):
            Se = (h[mask] / self.hb) ** (-self.lambda_)
            Kr = Se ** self._K_exponent
            K[mask] = self.Ks * Kr

        return float(K[0]) if scalar_input else K

    def capacity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Brooks-Corey water capacity"""
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        C = np.zeros_like(h)

        mask = h < self.hb
        if np.any(mask):
            C[mask] = -self.lambda_ * (self.theta_s - self.theta_r) * \
                      (h[mask] / self.hb) ** (-self.lambda_) / h[mask]

        return float(C[0]) if scalar_input else C

    def __repr__(self) -> str:
        return f"BrooksCorey(θr={self.theta_r:.4f}, θs={self.theta_s:.4f}, " \
               f"hb={self.hb:.2f} cm, λ={self.lambda_:.3f}, Ks={self.Ks:.2f} cm/day)"
