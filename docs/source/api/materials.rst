Materials Module
================

The materials module contains soil hydraulic property models.

Base Class
----------

.. autoclass:: hydrus1dpy.HydraulicModel
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

van Genuchten Model
-------------------

.. autoclass:: hydrus1dpy.VanGenuchten
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Equations:**

   Water retention:

   .. math::

      \\theta(h) = \\theta_r + \\frac{\\theta_s - \\theta_r}{[1 + (\\alpha|h|)^n]^m}

   Hydraulic conductivity:

   .. math::

      K(h) = K_s S_e^l [1 - (1 - S_e^{1/m})^m]^2

   Where :math:`S_e = \\frac{\\theta - \\theta_r}{\\theta_s - \\theta_r}` and :math:`m = 1 - 1/n`

   **Example:**

   .. code-block:: python

      from hydrus1dpy import VanGenuchten

      # Loam soil (Carsel & Parrish, 1988)
      soil = VanGenuchten(
          theta_r=0.078,  # Residual water content
          theta_s=0.430,  # Saturated water content
          alpha=0.036,    # Scale parameter [1/cm]
          n=1.56,         # Shape parameter
          Ks=24.96,       # Saturated conductivity [cm/day]
          l=0.5           # Pore connectivity
      )

Modified van Genuchten
----------------------

.. autoclass:: hydrus1dpy.ModifiedVanGenuchten
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Brooks-Corey Model
------------------

.. autoclass:: hydrus1dpy.BrooksCorey
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Equations:**

   Water retention:

   .. math::

      \\theta(h) = \\begin{cases}
      \\theta_r + (\\theta_s - \\theta_r)(h_b/h)^\\lambda & h < h_b \\\\
      \\theta_s & h \\geq h_b
      \\end{cases}

   Hydraulic conductivity:

   .. math::

      K(h) = K_s S_e^{2/\\lambda + 2 + l}

Dual Porosity Model
-------------------

.. autoclass:: hydrus1dpy.DualPorosity
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Log-Normal Model
----------------

.. autoclass:: hydrus1dpy.LogNormal
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Custom Hydraulic Model
----------------------

.. autoclass:: hydrus1dpy.CustomHydraulicModel
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Example:**

   .. code-block:: python

      from hydrus1dpy import CustomHydraulicModel
      import numpy as np

      def custom_theta(h):
          # Custom water retention function
          return 0.1 + 0.3 / (1 + np.abs(h/10)**2)

      def custom_K(h):
          # Custom hydraulic conductivity
          Se = (custom_theta(h) - 0.1) / 0.3
          return 10.0 * Se**3

      def custom_C(h):
          # Specific moisture capacity (derivative)
          dh = 0.001
          return (custom_theta(h + dh) - custom_theta(h - dh)) / (2*dh)

      soil = CustomHydraulicModel(
          theta_func=custom_theta,
          K_func=custom_K,
          C_func=custom_C,
          theta_s=0.4,
          theta_r=0.1
      )
