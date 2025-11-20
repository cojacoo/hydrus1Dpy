Numerics Module
===============

The numerics module contains numerical solvers and time stepping algorithms.

Time Stepping
-------------

.. autoclass:: hydrus1dpy.AdaptiveTimeStepper
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Example:**

   .. code-block:: python

      from hydrus1dpy import AdaptiveTimeStepper

      stepper = AdaptiveTimeStepper(
          dt_init=0.01,
          dt_min=1e-6,
          dt_max=1.0,
          max_iterations=10,
          target_iterations=5
      )

Linear Solver
-------------

.. autofunction:: hydrus1dpy.solve_tridiagonal

   Solves tridiagonal system using Thomas algorithm.

   **Algorithm:**

   The Thomas algorithm solves :math:`Ax = d` where:

   .. math::

      A = \\begin{bmatrix}
      b_0 & c_0 & 0 & \\cdots & 0 \\\\
      a_1 & b_1 & c_1 & \\cdots & 0 \\\\
      0 & a_2 & b_2 & \\cdots & 0 \\\\
      \\vdots & \\vdots & \\vdots & \\ddots & \\vdots \\\\
      0 & 0 & 0 & \\cdots & b_n
      \\end{bmatrix}

   **Complexity:** :math:`O(n)` operations

   **Example:**

   .. code-block:: python

      import numpy as np
      from hydrus1dpy import solve_tridiagonal

      # Simple test system
      a = np.array([0, -1, -1])
      b = np.array([2, 2, 2])
      c = np.array([-1, -1, 0])
      d = np.array([1, 0, 1])

      x = solve_tridiagonal(a, b, c, d)
      # x = [1, 1, 1]
