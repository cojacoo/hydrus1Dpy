"""
Dual-Porosity Hydraulic Model
==============================

Implementation of Durner (1994) bimodal van Genuchten model.

References
----------
Durner, W. (1994). Hydraulic conductivity estimation for soils with
heterogeneous pore structure. Water Resources Research, 30(2), 211-223.
"""

from typing import Union
import numpy as np
from .base import HydraulicModel


class DualPorosity(HydraulicModel):
    """
    Durner (1994) dual-porosity model (bimodal van Genuchten)

    θ(h) = θr + (θs - θr) · [w1·Se1 + w2·Se2]

    where:
        Se1 = [1 + |α1·h|^n1]^(-m1)  (macro pores)
        Se2 = [1 + |α2·h|^n2]^(-m2)  (micro pores)
        w1 + w2 = 1

    Parameters
    ----------
    theta_r, theta_s, Ks : float
        Standard parameters
    w2 : float
        Weight for second pore system, 0 < w2 < 1
    alpha1, alpha2 : float
        Scale parameters for pore systems [1/cm]
    n1, n2 : float
        Shape parameters (n > 1)
    l : float, optional
        Pore connectivity
    """

    def __init__(self,
                 theta_r: float,
                 theta_s: float,
                 alpha1: float,
                 n1: float,
                 alpha2: float,
                 n2: float,
                 w2: float,
                 Ks: float,
                 l: float = 0.5):
        super().__init__(theta_r, theta_s, Ks)

        if not 0 < w2 < 1:
            raise ValueError(f"w2 must be in (0,1). Got w2={w2:.4f}")
        if alpha1 <= 0 or alpha2 <= 0:
            raise ValueError("Both α1 and α2 must be positive")
        if n1 <= 1 or n2 <= 1:
            raise ValueError("Both n1 and n2 must be > 1")

        self.w2 = float(w2)
        self.w1 = 1.0 - w2
        self.alpha1 = float(alpha1)
        self.alpha2 = float(alpha2)
        self.n1 = float(n1)
        self.n2 = float(n2)
        self.m1 = 1.0 - 1.0 / n1
        self.m2 = 1.0 - 1.0 / n2
        self.l = float(l)

    def water_content(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Dual-porosity water retention"""
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        theta = np.full_like(h, self.theta_s)

        mask = h < 0
        if np.any(mask):
            h_abs = np.abs(h[mask])
            Se1 = (1.0 + (self.alpha1 * h_abs) ** self.n1) ** (-self.m1)
            Se2 = (1.0 + (self.alpha2 * h_abs) ** self.n2) ** (-self.m2)
            Se_total = self.w1 * Se1 + self.w2 * Se2
            theta[mask] = self.theta_r + (self.theta_s - self.theta_r) * Se_total

        return float(theta[0]) if scalar_input else theta

    def conductivity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Dual-porosity conductivity (simplified)"""
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        K = np.full_like(h, self.Ks)

        mask = h < 0
        if np.any(mask):
            Se1 = (1.0 + (self.alpha1 * np.abs(h[mask])) ** self.n1) ** (-self.m1)
            Se2 = (1.0 + (self.alpha2 * np.abs(h[mask])) ** self.n2) ** (-self.m2)
            Se_total = self.w1 * Se1 + self.w2 * Se2

            term1 = self.w1 * self.alpha1 * (1.0 - (1.0 - Se1 ** (1/self.m1)) ** self.m1)
            term2 = self.w2 * self.alpha2 * (1.0 - (1.0 - Se2 ** (1/self.m2)) ** self.m2)
            denom = self.w1 * self.alpha1 + self.w2 * self.alpha2

            Kr = Se_total ** self.l * ((term1 + term2) / denom) ** 2
            K[mask] = self.Ks * Kr

        return float(K[0]) if scalar_input else K

    def capacity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Dual-porosity water capacity"""
        h = np.asarray(h, dtype=float)
        scalar_input = h.ndim == 0
        h = np.atleast_1d(h)

        C = np.zeros_like(h)

        mask = h < 0
        if np.any(mask):
            h_abs = np.abs(h[mask])
            C1 = self.w1 * (self.theta_s - self.theta_r) * self.m1 * self.n1 * \
                 (self.alpha1 ** self.n1) * (h_abs ** (self.n1-1)) * \
                 (1.0 + (self.alpha1 * h_abs) ** self.n1) ** (-self.m1-1)
            C2 = self.w2 * (self.theta_s - self.theta_r) * self.m2 * self.n2 * \
                 (self.alpha2 ** self.n2) * (h_abs ** (self.n2-1)) * \
                 (1.0 + (self.alpha2 * h_abs) ** self.n2) ** (-self.m2-1)
            C[mask] = C1 + C2

        return float(C[0]) if scalar_input else C

    def __repr__(self) -> str:
        return f"DualPorosity(α1={self.alpha1:.4f}, n1={self.n1:.2f}, " \
               f"α2={self.alpha2:.4f}, n2={self.n2:.2f}, w2={self.w2:.3f})"
