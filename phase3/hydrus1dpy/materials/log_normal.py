"""
Log-Normal Hydraulic Model
===========================

Implementation of Kosugi (1996) log-normal pore-size distribution model.

References
----------
Kosugi, K. (1996). Lognormal distribution model for unsaturated soil
hydraulic properties. Water Resources Research, 32(9), 2697-2703.
"""

from typing import Union
import numpy as np
from scipy.special import erfc
from .base import HydraulicModel


class LogNormal(HydraulicModel):
    """
    Kosugi (1996) log-normal model

    Based on log-normal pore-size distribution

    Parameters
    ----------
    theta_r, theta_s, Ks : float
        Standard parameters
    hm : float
        Median pressure head [cm], negative
    sigma : float
        Standard deviation of log(h), > 0
    l : float, optional
        Pore connectivity
    """

    def __init__(self,
                 theta_r: float,
                 theta_s: float,
                 hm: float,
                 sigma: float,
                 Ks: float,
                 l: float = 0.5):
        super().__init__(theta_r, theta_s, Ks)

        if hm >= 0:
            raise ValueError("hm must be negative")
        if sigma <= 0:
            raise ValueError("σ must be positive")

        self.hm = float(hm)
        self.sigma = float(sigma)
        self.l = float(l)

    def water_content(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Log-normal water retention"""
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        theta = np.full_like(h, self.theta_s)

        mask = h < 0
        if np.any(mask):
            x = np.log(np.abs(h[mask]) / np.abs(self.hm)) / self.sigma
            Se = 0.5 * erfc(x / np.sqrt(2))
            theta[mask] = self.theta_r + (self.theta_s - self.theta_r) * Se

        return float(theta[0]) if scalar_input else theta

    def conductivity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Log-normal conductivity"""
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        K = np.full_like(h, self.Ks)

        mask = h < 0
        if np.any(mask):
            x1 = np.log(np.abs(h[mask]) / np.abs(self.hm)) / self.sigma
            x2 = x1 + self.sigma
            Se = 0.5 * erfc(x1 / np.sqrt(2))
            T = 0.5 * erfc(x2 / np.sqrt(2))
            Kr = Se ** self.l * T ** 2
            K[mask] = self.Ks * Kr

        return float(K[0]) if scalar_input else K

    def capacity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Log-normal water capacity (numerical)"""
        return super().capacity(h)  # Use numerical derivative from base class

    def __repr__(self) -> str:
        return f"LogNormal(hm={self.hm:.2f} cm, σ={self.sigma:.3f}, " \
               f"Ks={self.Ks:.2f} cm/day)"
