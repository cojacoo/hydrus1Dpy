"""
Linear Solvers for HYDRUS1D Phase 3
====================================

Efficient solvers for tridiagonal systems arising from
finite difference discretization of Richards equation.

Author: HYDRUS1DPy Development Team
"""

import numpy as np
from numba import njit


@njit
def solve_tridiagonal(a, b, c, d):
    """
    Solve tridiagonal system Ax = d using Thomas algorithm.

    The system has the form:

    | b[0]  c[0]   0     0   ...   0   |   | x[0]   |   | d[0]   |
    | a[1]  b[1]  c[1]   0   ...   0   |   | x[1]   |   | d[1]   |
    |  0    a[2]  b[2]  c[2]  ...  0   | · | x[2]   | = | d[2]   |
    | ...   ...   ...   ...  ...  ... |   | ...    |   | ...    |
    |  0     0     0    ... a[n] b[n] |   | x[n]   |   | d[n]   |

    Parameters
    ----------
    a : ndarray
        Lower diagonal (length n, a[0] is unused)
    b : ndarray
        Main diagonal (length n)
    c : ndarray
        Upper diagonal (length n, c[n-1] is unused)
    d : ndarray
        Right-hand side (length n)

    Returns
    -------
    x : ndarray
        Solution vector (length n)

    Notes
    -----
    - Algorithm: Thomas algorithm (specialized Gaussian elimination)
    - Complexity: O(n) time, O(n) space
    - Stability: Requires diagonal dominance for numerical stability
    - Reference: Press et al. (2007), Numerical Recipes, Section 2.4

    The Thomas algorithm consists of two passes:
    1. Forward elimination: Eliminate lower diagonal
    2. Back substitution: Solve for unknowns from bottom to top

    Examples
    --------
    >>> # Solve simple 3x3 system
    >>> a = np.array([0.0, 1.0, 1.0])     # Lower diagonal (a[0] unused)
    >>> b = np.array([2.0, 2.0, 2.0])     # Main diagonal
    >>> c = np.array([1.0, 1.0, 0.0])     # Upper diagonal (c[2] unused)
    >>> d = np.array([1.0, 2.0, 3.0])     # RHS
    >>> x = solve_tridiagonal(a, b, c, d)
    """
    n = len(d)

    # Create copies to avoid modifying input
    c_prime = np.zeros(n, dtype=np.float64)
    d_prime = np.zeros(n, dtype=np.float64)
    x = np.zeros(n, dtype=np.float64)

    # Forward elimination
    c_prime[0] = c[0] / b[0]
    d_prime[0] = d[0] / b[0]

    for i in range(1, n):
        denom = b[i] - a[i] * c_prime[i-1]

        # Check for singular matrix
        if abs(denom) < 1e-30:
            # Matrix is singular or nearly singular
            # This shouldn't happen with proper discretization
            raise ValueError(f"Singular matrix at row {i}: denominator = {denom}")

        c_prime[i] = c[i] / denom
        d_prime[i] = (d[i] - a[i] * d_prime[i-1]) / denom

    # Back substitution
    x[n-1] = d_prime[n-1]

    for i in range(n-2, -1, -1):
        x[i] = d_prime[i] - c_prime[i] * x[i+1]

    return x


@njit
def solve_tridiagonal_inplace(a, b, c, d):
    """
    Solve tridiagonal system in-place (modifies c and d arrays).

    More memory-efficient version that overwrites c and d.
    Use when you don't need to preserve the original system.

    Parameters
    ----------
    a : ndarray
        Lower diagonal (length n, a[0] is unused)
    b : ndarray
        Main diagonal (length n)
    c : ndarray
        Upper diagonal (length n, c[n-1] is unused) - MODIFIED
    d : ndarray
        Right-hand side (length n) - MODIFIED and returned as solution

    Returns
    -------
    d : ndarray
        Solution vector (overwrites input d)

    Notes
    -----
    This version modifies the input arrays c and d in place,
    reducing memory allocation. Useful for large systems or
    when called repeatedly in time stepping loops.
    """
    n = len(d)

    # Forward elimination
    c[0] = c[0] / b[0]
    d[0] = d[0] / b[0]

    for i in range(1, n):
        denom = b[i] - a[i] * c[i-1]

        if abs(denom) < 1e-30:
            raise ValueError(f"Singular matrix at row {i}")

        c[i] = c[i] / denom
        d[i] = (d[i] - a[i] * d[i-1]) / denom

    # Back substitution (stored in d)
    for i in range(n-2, -1, -1):
        d[i] = d[i] - c[i] * d[i+1]

    return d


def check_diagonal_dominance(a, b, c):
    """
    Check if tridiagonal matrix is diagonally dominant.

    A matrix is diagonally dominant if:
    |b[i]| >= |a[i]| + |c[i]| for all i

    This is a sufficient (but not necessary) condition for
    numerical stability of the Thomas algorithm.

    Parameters
    ----------
    a, b, c : ndarray
        Lower, main, and upper diagonals

    Returns
    -------
    dominant : bool
        True if matrix is diagonally dominant
    min_ratio : float
        Minimum diagonal dominance ratio (should be >= 1.0)
    """
    n = len(b)

    ratios = np.zeros(n)
    for i in range(n):
        off_diag = 0.0
        if i > 0:
            off_diag += abs(a[i])
        if i < n-1:
            off_diag += abs(c[i])

        if off_diag > 0:
            ratios[i] = abs(b[i]) / off_diag
        else:
            ratios[i] = np.inf

    min_ratio = np.min(ratios)
    dominant = min_ratio >= 1.0

    return dominant, min_ratio


def condition_number_estimate(a, b, c):
    """
    Estimate condition number of tridiagonal matrix.

    Uses Gershgorin circle theorem for rough estimate.
    High condition numbers (>> 1) indicate potential
    numerical instability.

    Parameters
    ----------
    a, b, c : ndarray
        Lower, main, and upper diagonals

    Returns
    -------
    cond_est : float
        Estimated condition number
    """
    n = len(b)

    # Gershgorin radii
    max_lambda = -np.inf
    min_lambda = np.inf

    for i in range(n):
        radius = 0.0
        if i > 0:
            radius += abs(a[i])
        if i < n-1:
            radius += abs(c[i])

        max_lambda = max(max_lambda, abs(b[i]) + radius)
        min_lambda = min(min_lambda, abs(b[i]) - radius)

    if min_lambda > 0:
        cond_est = max_lambda / min_lambda
    else:
        cond_est = np.inf

    return cond_est
