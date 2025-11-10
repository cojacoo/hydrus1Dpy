"""
Custom Hydraulic Model
=======================

User-defined hydraulic model using callable functions.
"""

from typing import Union, Callable, Optional, Dict
import numpy as np
from .base import HydraulicModel


class CustomHydraulicModel(HydraulicModel):
    """
    Custom hydraulic model using user-defined functions

    Allows users to define their own water retention and conductivity functions.

    Parameters
    ----------
    theta_r, theta_s, Ks : float
        Standard parameters
    theta_func : callable
        Function: theta = f(h, **params)
    K_func : callable
        Function: K = f(h, **params)
    C_func : callable, optional
        Function: C = f(h, **params)
        If None, computed numerically
    **params : dict
        Additional parameters passed to functions

    Examples
    --------
    >>> def my_theta(h, a, b):
    ...     if h >= 0:
    ...         return 0.43
    ...     return 0.078 + 0.352 * np.exp(a * h ** b)
    >>>
    >>> def my_K(h, Ks, c):
    ...     return Ks * np.exp(c * h)
    >>>
    >>> model = CustomHydraulicModel(
    ...     theta_r=0.078, theta_s=0.43, Ks=24.96,
    ...     theta_func=my_theta, K_func=my_K,
    ...     a=0.01, b=0.5, c=0.05
    ... )
    """

    def __init__(self,
                 theta_r: float,
                 theta_s: float,
                 Ks: float,
                 theta_func: Callable,
                 K_func: Callable,
                 C_func: Optional[Callable] = None,
                 **params):
        super().__init__(theta_r, theta_s, Ks)

        self._theta_func = theta_func
        self._K_func = K_func
        self._C_func = C_func
        self.params = params

    def water_content(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """User-defined water content"""
        return self._theta_func(h, **self.params)

    def conductivity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """User-defined conductivity"""
        return self._K_func(h, **self.params)

    def capacity(self, h: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """User-defined or numerical capacity"""
        if self._C_func is not None:
            return self._C_func(h, **self.params)
        else:
            # Numerical derivative
            dh = 0.01
            h = np.asarray(h)
            theta_plus = self.water_content(h + dh)
            theta_minus = self.water_content(h - dh)
            return (theta_plus - theta_minus) / (2 * dh)

    def __repr__(self) -> str:
        return f"CustomHydraulicModel(params={list(self.params.keys())})"
